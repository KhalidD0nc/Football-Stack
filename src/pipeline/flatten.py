"""Post-ingest JSON flattening layer.

Reads raw JSON from storage, flattens nested API responses into typed rows,
deduplicates, and writes Parquet to the curated/ prefix. Replaces Snowflake
LATERAL FLATTEN logic with portable Python, producing warehouse-agnostic output.

Usage:
    python -m src.pipeline.flatten --date 2026-03-10 --config pipeline_config.json
"""

from __future__ import annotations

import argparse
import io
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import partial
from time import perf_counter
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from .schemas import SCHEMAS
from .storage import StorageWriter, generate_run_id, normalize_endpoint

logger = logging.getLogger(__name__)


# ── Context & utilities ──────────────────────────────────────────────────────


class WarehouseSyncError(RuntimeError):
    """Raised when direct warehouse publication fails for a curated table."""


@dataclass(frozen=True)
class FlattenContext:
    league_id: int
    season: int
    dt: str
    run_id: str
    loaded_at: str


def _int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _str(val: Any) -> str | None:
    if val is None:
        return None
    return str(val)


def _bool(val: Any) -> bool | None:
    if val is None:
        return None
    return bool(val)


def parse_pct(val: Any) -> float | None:
    """Convert '45%' → 45.0, None → None."""
    if val is None:
        return None
    try:
        return float(str(val).replace("%", ""))
    except (ValueError, TypeError):
        return None


def _safe_float(val: Any) -> float | None:
    """try_to_double equivalent: parse string or number to float, None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> int | None:
    """try_to_number equivalent: parse string or number to int, None on failure."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _meta(ctx: FlattenContext) -> dict[str, Any]:
    return {
        "league_id": ctx.league_id,
        "season": ctx.season,
        "dt": ctx.dt,
        "run_id": ctx.run_id,
        "_loaded_at": ctx.loaded_at,
    }


def _get(d: Any, *keys: str, default: Any = None) -> Any:
    """Safely navigate nested dicts: _get(d, 'a', 'b', 'c') == d['a']['b']['c']."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


# ── Flattener functions ──────────────────────────────────────────────────────


def flatten_teams(raw: dict, ctx: FlattenContext) -> list[dict]:
    rows = []
    for item in raw.get("payload", {}).get("response", []):
        team = item.get("team", {}) or {}
        venue = item.get("venue", {}) or {}
        row = {
            "team_id": _int(team.get("id")),
            "team_name": _str(team.get("name")),
            "team_code": _str(team.get("code")),
            "country": _str(team.get("country")),
            "founded": _int(team.get("founded")),
            "is_national_team": _bool(team.get("national")),
            "team_logo_url": _str(team.get("logo")),
            "venue_id": _int(venue.get("id")),
            "venue_name": _str(venue.get("name")),
            "venue_address": _str(venue.get("address")),
            "venue_city": _str(venue.get("city")),
            "venue_capacity": _int(venue.get("capacity")),
            "venue_surface": _str(venue.get("surface")),
            "venue_image_url": _str(venue.get("image")),
            **_meta(ctx),
        }
        rows.append(row)
    return rows


def flatten_fixtures(raw: dict, ctx: FlattenContext) -> list[dict]:
    rows = []
    for item in raw.get("payload", {}).get("response", []):
        fix = item.get("fixture", {}) or {}
        league = item.get("league", {}) or {}
        teams = item.get("teams", {}) or {}
        goals = item.get("goals", {}) or {}
        score = item.get("score", {}) or {}
        home = teams.get("home", {}) or {}
        away = teams.get("away", {}) or {}
        status = fix.get("status", {}) or {}
        periods = fix.get("periods", {}) or {}
        venue = fix.get("venue", {}) or {}
        ht = score.get("halftime", {}) or {}
        ft = score.get("fulltime", {}) or {}
        et = score.get("extratime", {}) or {}
        pen = score.get("penalty", {}) or {}

        row = {
            "fixture_id": _int(fix.get("id")),
            "referee": _str(fix.get("referee")),
            "fixture_timezone": _str(fix.get("timezone")),
            "fixture_date": _str(fix.get("date")),
            "fixture_timestamp": _int(fix.get("timestamp")),
            "period_first": _int(periods.get("first")),
            "period_second": _int(periods.get("second")),
            "venue_id": _int(venue.get("id")),
            "venue_name": _str(venue.get("name")),
            "venue_city": _str(venue.get("city")),
            "status_long": _str(status.get("long")),
            "status_short": _str(status.get("short")),
            "status_elapsed": _int(status.get("elapsed")),
            "fixture_league_id": _int(league.get("id")),
            "fixture_league_name": _str(league.get("name")),
            "fixture_league_country": _str(league.get("country")),
            "fixture_league_logo": _str(league.get("logo")),
            "fixture_league_flag": _str(league.get("flag")),
            "fixture_league_season": _int(league.get("season")),
            "round_name": _str(league.get("round")),
            "home_team_id": _int(home.get("id")),
            "home_team_name": _str(home.get("name")),
            "home_team_logo": _str(home.get("logo")),
            "home_team_winner": _bool(home.get("winner")),
            "away_team_id": _int(away.get("id")),
            "away_team_name": _str(away.get("name")),
            "away_team_logo": _str(away.get("logo")),
            "away_team_winner": _bool(away.get("winner")),
            "home_goals": _int(goals.get("home")),
            "away_goals": _int(goals.get("away")),
            "halftime_home_goals": _int(ht.get("home")),
            "halftime_away_goals": _int(ht.get("away")),
            "fulltime_home_goals": _int(ft.get("home")),
            "fulltime_away_goals": _int(ft.get("away")),
            "extratime_home_goals": _int(et.get("home")),
            "extratime_away_goals": _int(et.get("away")),
            "penalty_home_goals": _int(pen.get("home")),
            "penalty_away_goals": _int(pen.get("away")),
            **_meta(ctx),
        }
        rows.append(row)
    return rows


def flatten_rounds(raw: dict, ctx: FlattenContext) -> list[dict]:
    rows = []
    for round_name in raw.get("payload", {}).get("response", []):
        name = _str(round_name)
        match = re.search(r"[0-9]+", name) if name else None
        row = {
            "round_name": name,
            "round_number": int(match.group()) if match else None,
            **_meta(ctx),
        }
        rows.append(row)
    return rows


def flatten_match_events(raw: dict, ctx: FlattenContext) -> list[dict]:
    fixture_id = _int(_get(raw, "params", "fixture"))
    rows = []
    for idx, event in enumerate(raw.get("payload", {}).get("response", [])):
        time_obj = event.get("time", {}) or {}
        team = event.get("team", {}) or {}
        player = event.get("player", {}) or {}
        assist = event.get("assist", {}) or {}
        row = {
            "fixture_id": fixture_id,
            "event_sequence": idx,
            "event_minute": _int(time_obj.get("elapsed")),
            "event_extra_minute": _int(time_obj.get("extra")),
            "team_id": _int(team.get("id")),
            "team_name": _str(team.get("name")),
            "player_id": _int(player.get("id")),
            "player_name": _str(player.get("name")),
            "assist_player_id": _int(assist.get("id")),
            "assist_player_name": _str(assist.get("name")),
            "event_type": _str(event.get("type")),
            "event_detail": _str(event.get("detail")),
            "event_comments": _str(event.get("comments")),
            **_meta(ctx),
        }
        rows.append(row)
    return rows


def flatten_match_team_stats(raw: dict, ctx: FlattenContext) -> list[dict]:
    """Double FLATTEN + PIVOT: team stats from long → wide row."""
    fixture_id = _int(_get(raw, "params", "fixture"))
    rows = []
    for team_entry in raw.get("payload", {}).get("response", []):
        team = team_entry.get("team", {}) or {}
        stats_list = team_entry.get("statistics", []) or []

        stat_map: dict[str, str | None] = {}
        for stat in stats_list:
            stat_type = stat.get("type")
            stat_value = stat.get("value")
            if stat_type is not None:
                stat_map[stat_type] = _str(stat_value) if stat_value is not None else None

        row = {
            "fixture_id": fixture_id,
            "team_id": _int(team.get("id")),
            "team_name": _str(team.get("name")),
            "ball_possession_pct": parse_pct(stat_map.get("Ball Possession")),
            "passes_pct": parse_pct(stat_map.get("Passes %")),
            "expected_goals": _safe_float(stat_map.get("expected_goals")),
            "goals_prevented": _safe_float(stat_map.get("goals_prevented")),
            "total_shots": _safe_int(stat_map.get("Total Shots")),
            "shots_on_goal": _safe_int(stat_map.get("Shots on Goal")),
            "shots_off_goal": _safe_int(stat_map.get("Shots off Goal")),
            "blocked_shots": _safe_int(stat_map.get("Blocked Shots")),
            "shots_inside_box": _safe_int(stat_map.get("Shots insidebox")),
            "shots_outside_box": _safe_int(stat_map.get("Shots outsidebox")),
            "corner_kicks": _safe_int(stat_map.get("Corner Kicks")),
            "offsides": _safe_int(stat_map.get("Offsides")),
            "fouls": _safe_int(stat_map.get("Fouls")),
            "yellow_cards": _safe_int(stat_map.get("Yellow Cards")),
            "red_cards": _safe_int(stat_map.get("Red Cards")),
            "goalkeeper_saves": _safe_int(stat_map.get("Goalkeeper Saves")),
            "passes_accurate": _safe_int(stat_map.get("Passes accurate")),
            "total_passes": _safe_int(stat_map.get("Total passes")),
            **_meta(ctx),
        }
        rows.append(row)
    return rows


def flatten_match_player_stats(raw: dict, ctx: FlattenContext) -> list[dict]:
    """Double FLATTEN: teams → players array."""
    fixture_id = _int(_get(raw, "params", "fixture"))
    rows = []
    for team_entry in raw.get("payload", {}).get("response", []):
        team = team_entry.get("team", {}) or {}
        for p_entry in team_entry.get("players", []) or []:
            player = p_entry.get("player", {}) or {}
            s = (p_entry.get("statistics") or [{}])[0] if p_entry.get("statistics") else {}
            games = s.get("games", {}) or {}
            shots = s.get("shots", {}) or {}
            goals_obj = s.get("goals", {}) or {}
            passes = s.get("passes", {}) or {}
            tackles = s.get("tackles", {}) or {}
            duels = s.get("duels", {}) or {}
            dribbles = s.get("dribbles", {}) or {}
            fouls_obj = s.get("fouls", {}) or {}
            cards = s.get("cards", {}) or {}
            penalty = s.get("penalty", {}) or {}

            row = {
                "fixture_id": fixture_id,
                "team_id": _int(team.get("id")),
                "team_name": _str(team.get("name")),
                "team_logo": _str(team.get("logo")),
                "player_id": _int(player.get("id")),
                "player_name": _str(player.get("name")),
                "player_photo": _str(player.get("photo")),
                "shirt_number": _int(games.get("number")),
                "position": _str(games.get("position")),
                "rating": _float(games.get("rating")),
                "minutes_played": _int(games.get("minutes")),
                "is_captain": _bool(games.get("captain")),
                "is_substitute": _bool(games.get("substitute")),
                "offsides": _int(s.get("offsides")),
                "shots_total": _int(shots.get("total")),
                "shots_on_target": _int(shots.get("on")),
                "goals_total": _int(goals_obj.get("total")),
                "goals_conceded": _int(goals_obj.get("conceded")),
                "assists": _int(goals_obj.get("assists")),
                "saves": _int(goals_obj.get("saves")),
                "passes_total": _int(passes.get("total")),
                "key_passes": _int(passes.get("key")),
                "passes_accuracy": _int(passes.get("accuracy")),
                "tackles_total": _int(tackles.get("total")),
                "blocks": _int(tackles.get("blocks")),
                "interceptions": _int(tackles.get("interceptions")),
                "duels_total": _int(duels.get("total")),
                "duels_won": _int(duels.get("won")),
                "dribbles_attempted": _int(dribbles.get("attempts")),
                "dribbles_success": _int(dribbles.get("success")),
                "dribbled_past": _int(dribbles.get("past")),
                "fouls_drawn": _int(fouls_obj.get("drawn")),
                "fouls_committed": _int(fouls_obj.get("committed")),
                "yellow_cards": _int(cards.get("yellow")),
                "red_cards": _int(cards.get("red")),
                "penalties_won": _int(penalty.get("won")),
                "penalties_committed": _int(penalty.get("commited")),
                "penalties_scored": _int(penalty.get("scored")),
                "penalties_missed": _int(penalty.get("missed")),
                "penalties_saved": _int(penalty.get("saved")),
                **_meta(ctx),
            }
            rows.append(row)
    return rows


def flatten_lineup_players(raw: dict, ctx: FlattenContext) -> list[dict]:
    """Double FLATTEN + UNION ALL: startXI and substitutes."""
    fixture_id = _int(_get(raw, "params", "fixture"))
    rows = []
    for lineup in raw.get("payload", {}).get("response", []):
        team = lineup.get("team", {}) or {}
        colors = _get(team, "colors", "player") or {}
        coach = lineup.get("coach", {}) or {}
        base = {
            "fixture_id": fixture_id,
            "team_id": _int(team.get("id")),
            "team_name": _str(team.get("name")),
            "team_colors_player_primary": _str(colors.get("primary")),
            "team_colors_player_number": _str(colors.get("number")),
            "team_colors_player_border": _str(colors.get("border")),
            "formation": _str(lineup.get("formation")),
            "coach_id": _int(coach.get("id")),
            "coach_name": _str(coach.get("name")),
            "coach_photo": _str(coach.get("photo")),
        }

        for bucket, key in [("start_xi", "startXI"), ("substitutes", "substitutes")]:
            for p_entry in lineup.get(key, []) or []:
                player = p_entry.get("player", {}) or {}
                row = {
                    **base,
                    "lineup_bucket": bucket,
                    "player_id": _int(player.get("id")),
                    "player_name": _str(player.get("name")),
                    "player_number": _int(player.get("number")),
                    "player_pos": _str(player.get("pos")),
                    "grid": _str(player.get("grid")),
                    **_meta(ctx),
                }
                rows.append(row)
    return rows


def flatten_predictions(raw: dict, ctx: FlattenContext) -> list[dict]:
    fixture_id = _int(_get(raw, "params", "fixture"))
    rows = []
    for p in raw.get("payload", {}).get("response", []):
        preds = p.get("predictions", {}) or {}
        winner = preds.get("winner", {}) or {}
        pct = preds.get("percent", {}) or {}
        teams = p.get("teams", {}) or {}
        home = teams.get("home", {}) or {}
        away = teams.get("away", {}) or {}
        comp = p.get("comparison", {}) or {}

        h_pct = _str(pct.get("home"))
        d_pct = _str(pct.get("draw"))
        a_pct = _str(pct.get("away"))

        row = {
            "fixture_id": fixture_id,
            "predicted_winner_team_id": _int(winner.get("id")),
            "predicted_winner_team_name": _str(winner.get("name")),
            "predicted_winner_comment": _str(winner.get("comment")),
            "betting_advice": _str(preds.get("advice")),
            "home_win_percent": h_pct,
            "draw_percent": d_pct,
            "away_win_percent": a_pct,
            "home_win_percent_value": parse_pct(h_pct),
            "draw_percent_value": parse_pct(d_pct),
            "away_win_percent_value": parse_pct(a_pct),
            "home_team_id": _int(home.get("id")),
            "home_team_name": _str(home.get("name")),
            "away_team_id": _int(away.get("id")),
            "away_team_name": _str(away.get("name")),
            "comparison_form_home": _str(_get(comp, "form", "home")),
            "comparison_form_away": _str(_get(comp, "form", "away")),
            "comparison_attack_home": _str(_get(comp, "att", "home")),
            "comparison_attack_away": _str(_get(comp, "att", "away")),
            "comparison_defense_home": _str(_get(comp, "def", "home")),
            "comparison_defense_away": _str(_get(comp, "def", "away")),
            "comparison_poisson_home": _str(_get(comp, "poisson_distribution", "home")),
            "comparison_poisson_away": _str(_get(comp, "poisson_distribution", "away")),
            "comparison_h2h_home": _str(_get(comp, "h2h", "home")),
            "comparison_h2h_away": _str(_get(comp, "h2h", "away")),
            "comparison_goals_home": _str(_get(comp, "goals", "home")),
            "comparison_goals_away": _str(_get(comp, "goals", "away")),
            "comparison_total_home": _str(_get(comp, "total", "home")),
            "comparison_total_away": _str(_get(comp, "total", "away")),
            **_meta(ctx),
        }
        rows.append(row)
    return rows


def flatten_player_season_stats(raw: dict, ctx: FlattenContext) -> list[dict]:
    """Double FLATTEN: players → statistics array."""
    rows = []
    for p_entry in raw.get("payload", {}).get("response", []):
        player = p_entry.get("player", {}) or {}
        for s in p_entry.get("statistics", []) or []:
            team = s.get("team", {}) or {}
            league = s.get("league", {}) or {}
            games = s.get("games", {}) or {}
            subs = s.get("substitutes", {}) or {}
            shots = s.get("shots", {}) or {}
            goals_obj = s.get("goals", {}) or {}
            passes = s.get("passes", {}) or {}
            tackles = s.get("tackles", {}) or {}
            duels = s.get("duels", {}) or {}
            dribbles = s.get("dribbles", {}) or {}
            fouls_obj = s.get("fouls", {}) or {}
            cards = s.get("cards", {}) or {}
            penalty = s.get("penalty", {}) or {}

            row = {
                "player_id": _int(player.get("id")),
                "player_name": _str(player.get("name")),
                "player_first_name": _str(player.get("firstname")),
                "player_last_name": _str(player.get("lastname")),
                "player_age": _int(player.get("age")),
                "player_birthday": _str(player.get("birthday")),
                "player_nationality": _str(player.get("nationality")),
                "player_height": _str(player.get("height")),
                "player_weight": _str(player.get("weight")),
                "is_injured": _bool(player.get("injured")),
                "player_photo": _str(player.get("photo")),
                "team_id": _int(team.get("id")),
                "team_name": _str(team.get("name")),
                "team_logo": _str(team.get("logo")),
                "stats_league_id": _int(league.get("id")),
                "stats_league_name": _str(league.get("name")),
                "stats_league_country": _str(league.get("country")),
                "stats_league_logo": _str(league.get("logo")),
                "stats_league_flag": _str(league.get("flag")),
                "stats_season": _int(league.get("season")),
                "appearances": _int(games.get("appearences")),
                "lineups": _int(games.get("lineups")),
                "minutes_played": _int(games.get("minutes")),
                "shirt_number": _int(games.get("number")),
                "position": _str(games.get("position")),
                "rating": _float(games.get("rating")),
                "is_captain": _bool(games.get("captain")),
                "sub_in": _int(subs.get("in")),
                "sub_out": _int(subs.get("out")),
                "sub_bench": _int(subs.get("bench")),
                "shots_total": _int(shots.get("total")),
                "shots_on": _int(shots.get("on")),
                "goals_total": _int(goals_obj.get("total")),
                "goals_conceded": _int(goals_obj.get("conceded")),
                "assists_total": _int(goals_obj.get("assists")),
                "saves": _int(goals_obj.get("saves")),
                "passes_total": _int(passes.get("total")),
                "key_passes": _int(passes.get("key")),
                "passes_accuracy": _int(passes.get("accuracy")),
                "tackles_total": _int(tackles.get("total")),
                "tackles_blocks": _int(tackles.get("blocks")),
                "interceptions": _int(tackles.get("interceptions")),
                "duels_total": _int(duels.get("total")),
                "duels_won": _int(duels.get("won")),
                "dribbles_attempts": _int(dribbles.get("attempts")),
                "dribbles_success": _int(dribbles.get("success")),
                "dribbles_past": _int(dribbles.get("past")),
                "fouls_drawn": _int(fouls_obj.get("drawn")),
                "fouls_committed": _int(fouls_obj.get("committed")),
                "yellow_cards": _int(cards.get("yellow")),
                "yellow_red_cards": _int(cards.get("yellowred")),
                "red_cards": _int(cards.get("red")),
                "penalties_won": _int(penalty.get("won")),
                "penalties_committed": _int(penalty.get("commited")),
                "penalties_scored": _int(penalty.get("scored")),
                "penalties_missed": _int(penalty.get("missed")),
                "penalties_saved": _int(penalty.get("saved")),
                **_meta(ctx),
            }
            rows.append(row)
    return rows


def flatten_player_leaderboards(
    raw: dict, ctx: FlattenContext, *, ranking_type: str
) -> list[dict]:
    """Single FLATTEN with index-based ranking, shared across 4 raw endpoints."""
    rows = []
    for idx, entry in enumerate(raw.get("payload", {}).get("response", [])):
        player = entry.get("player", {}) or {}
        stats = (entry.get("statistics") or [{}])[0] if entry.get("statistics") else {}
        team = stats.get("team", {}) or {}
        league = stats.get("league", {}) or {}
        games = stats.get("games", {}) or {}
        goals_obj = stats.get("goals", {}) or {}
        cards = stats.get("cards", {}) or {}

        row = {
            "ranking_type": ranking_type,
            "player_id": _int(player.get("id")),
            "player_name": _str(player.get("name")),
            "player_first_name": _str(player.get("firstname")),
            "player_last_name": _str(player.get("lastname")),
            "player_age": _int(player.get("age")),
            "player_nationality": _str(player.get("nationality")),
            "player_photo_url": _str(player.get("photo")),
            "team_id": _int(team.get("id")),
            "team_name": _str(team.get("name")),
            "stats_league_id": _int(league.get("id")),
            "stats_season": _int(league.get("season")),
            "appearances": _int(games.get("appearences")),
            "minutes_played": _int(games.get("minutes")),
            "position": _str(games.get("position")),
            "rating": _float(games.get("rating")),
            "goals_total": _int(goals_obj.get("total")),
            "assists_total": _int(goals_obj.get("assists")),
            "yellow_cards": _int(cards.get("yellow")),
            "red_cards": _int(cards.get("red")),
            "rank": idx + 1,
            **_meta(ctx),
        }
        rows.append(row)
    return rows


def flatten_squad_players(raw: dict, ctx: FlattenContext) -> list[dict]:
    """Double FLATTEN: squads → players."""
    rows = []
    for squad_entry in raw.get("payload", {}).get("response", []):
        team = squad_entry.get("team", {}) or {}
        for p in squad_entry.get("players", []) or []:
            row = {
                "team_id": _int(team.get("id")),
                "team_name": _str(team.get("name")),
                "team_logo": _str(team.get("logo")),
                "player_id": _int(p.get("id")),
                "player_name": _str(p.get("name")),
                "player_age": _int(p.get("age")),
                "shirt_number": _int(p.get("number")),
                "position": _str(p.get("position")),
                "player_photo": _str(p.get("photo")),
                **_meta(ctx),
            }
            rows.append(row)
    return rows


def flatten_team_standings(raw: dict, ctx: FlattenContext) -> list[dict]:
    """Indexed path: response[0].league.standings[0]."""
    rows = []
    response = raw.get("payload", {}).get("response", [])
    if not response:
        return rows
    standings_arr = _get(response[0], "league", "standings")
    if not standings_arr or not isinstance(standings_arr, list) or not standings_arr[0]:
        return rows
    for s in standings_arr[0]:
        team = s.get("team", {}) or {}
        all_rec = s.get("all", {}) or {}
        home_rec = s.get("home", {}) or {}
        away_rec = s.get("away", {}) or {}
        row = {
            "standing_rank": _int(s.get("rank")),
            "team_id": _int(team.get("id")),
            "team_name": _str(team.get("name")),
            "team_logo": _str(team.get("logo")),
            "standing_group": _str(s.get("group")),
            "recent_form": _str(s.get("form")),
            "standing_status": _str(s.get("status")),
            "standing_description": _str(s.get("description")),
            "all_played": _int(all_rec.get("played")),
            "all_win": _int(all_rec.get("win")),
            "all_draw": _int(all_rec.get("draw")),
            "all_lose": _int(all_rec.get("lose")),
            "all_goals_for": _int(_get(all_rec, "goals", "for")),
            "all_goals_against": _int(_get(all_rec, "goals", "against")),
            "home_played": _int(home_rec.get("played")),
            "home_win": _int(home_rec.get("win")),
            "home_draw": _int(home_rec.get("draw")),
            "home_lose": _int(home_rec.get("lose")),
            "home_goals_for": _int(_get(home_rec, "goals", "for")),
            "home_goals_against": _int(_get(home_rec, "goals", "against")),
            "away_played": _int(away_rec.get("played")),
            "away_win": _int(away_rec.get("win")),
            "away_draw": _int(away_rec.get("draw")),
            "away_lose": _int(away_rec.get("lose")),
            "away_goals_for": _int(_get(away_rec, "goals", "for")),
            "away_goals_against": _int(_get(away_rec, "goals", "against")),
            "goals_diff": _int(s.get("goalsDiff")),
            "points": _int(s.get("points")),
            **_meta(ctx),
        }
        rows.append(row)
    return rows


def flatten_team_statistics(raw: dict, ctx: FlattenContext) -> list[dict]:
    """Direct extraction: 1:1 field extraction from response object (not array)."""
    resp = raw.get("payload", {}).get("response", {})
    if not resp or isinstance(resp, list):
        return []
    team = resp.get("team", {}) or {}
    league = resp.get("league", {}) or {}
    fixtures = resp.get("fixtures", {}) or {}
    goals = resp.get("goals", {}) or {}
    biggest = resp.get("biggest", {}) or {}

    played = fixtures.get("played", {}) or {}
    wins = fixtures.get("wins", {}) or {}
    draws = fixtures.get("draws", {}) or {}
    loses = fixtures.get("loses", {}) or {}
    gf_total = _get(goals, "for", "total") or {}
    gf_avg = _get(goals, "for", "average") or {}
    ga_total = _get(goals, "against", "total") or {}
    ga_avg = _get(goals, "against", "average") or {}
    cs = resp.get("clean_sheet", {}) or {}
    fts = resp.get("failed_to_score", {}) or {}
    streak = biggest.get("streak", {}) or {}
    b_wins = biggest.get("wins", {}) or {}
    b_loses = biggest.get("loses", {}) or {}
    b_gf = _get(biggest, "goals", "for") or {}
    b_ga = _get(biggest, "goals", "against") or {}

    row = {
        "team_id": _int(team.get("id")),
        "team_name": _str(team.get("name")),
        "team_logo": _str(team.get("logo")),
        "stats_league_id": _int(league.get("id")),
        "stats_league_name": _str(league.get("name")),
        "stats_season": _int(league.get("season")),
        "recent_form": _str(resp.get("form")),
        "fixtures_played_home": _int(played.get("home")),
        "fixtures_played_away": _int(played.get("away")),
        "fixtures_played_total": _int(played.get("total")),
        "fixtures_wins_home": _int(wins.get("home")),
        "fixtures_wins_away": _int(wins.get("away")),
        "fixtures_wins_total": _int(wins.get("total")),
        "fixtures_draws_home": _int(draws.get("home")),
        "fixtures_draws_away": _int(draws.get("away")),
        "fixtures_draws_total": _int(draws.get("total")),
        "fixtures_loses_home": _int(loses.get("home")),
        "fixtures_loses_away": _int(loses.get("away")),
        "fixtures_loses_total": _int(loses.get("total")),
        "goals_for_home": _int(gf_total.get("home")),
        "goals_for_away": _int(gf_total.get("away")),
        "goals_for_total": _int(gf_total.get("total")),
        "goals_for_avg_home": _safe_float(gf_avg.get("home")),
        "goals_for_avg_away": _safe_float(gf_avg.get("away")),
        "goals_for_avg_total": _safe_float(gf_avg.get("total")),
        "goals_against_home": _int(ga_total.get("home")),
        "goals_against_away": _int(ga_total.get("away")),
        "goals_against_total": _int(ga_total.get("total")),
        "goals_against_avg_home": _safe_float(ga_avg.get("home")),
        "goals_against_avg_away": _safe_float(ga_avg.get("away")),
        "goals_against_avg_total": _safe_float(ga_avg.get("total")),
        "clean_sheets_home": _int(cs.get("home")),
        "clean_sheets_away": _int(cs.get("away")),
        "clean_sheets_total": _int(cs.get("total")),
        "failed_to_score_home": _int(fts.get("home")),
        "failed_to_score_away": _int(fts.get("away")),
        "failed_to_score_total": _int(fts.get("total")),
        "biggest_streak_wins": _int(streak.get("wins")),
        "biggest_streak_draws": _int(streak.get("draws")),
        "biggest_streak_loses": _int(streak.get("loses")),
        "biggest_win_home": _str(b_wins.get("home")),
        "biggest_win_away": _str(b_wins.get("away")),
        "biggest_loss_home": _str(b_loses.get("home")),
        "biggest_loss_away": _str(b_loses.get("away")),
        "biggest_goals_for_home": _int(b_gf.get("home")),
        "biggest_goals_for_away": _int(b_gf.get("away")),
        "biggest_goals_against_home": _int(b_ga.get("home")),
        "biggest_goals_against_away": _int(b_ga.get("away")),
        **_meta(ctx),
    }
    return [row]


def flatten_transfers(raw: dict, ctx: FlattenContext) -> list[dict]:
    """Double FLATTEN: players → transfers array."""
    rows = []
    for p_entry in raw.get("payload", {}).get("response", []):
        player = p_entry.get("player", {}) or {}
        for t in p_entry.get("transfers", []) or []:
            teams = t.get("teams", {}) or {}
            to_team = teams.get("in", {}) or {}
            from_team = teams.get("out", {}) or {}
            row = {
                "player_id": _int(player.get("id")),
                "player_name": _str(player.get("name")),
                "transfer_date": _str(t.get("date")),
                "transfer_type": _str(t.get("type")),
                "to_team_id": _int(to_team.get("id")),
                "to_team_name": _str(to_team.get("name")),
                "to_team_logo": _str(to_team.get("logo")),
                "from_team_id": _int(from_team.get("id")),
                "from_team_name": _str(from_team.get("name")),
                "from_team_logo": _str(from_team.get("logo")),
                **_meta(ctx),
            }
            rows.append(row)
    return rows


def flatten_injuries(raw: dict, ctx: FlattenContext) -> list[dict]:
    rows = []
    for item in raw.get("payload", {}).get("response", []):
        player = item.get("player", {}) or {}
        team = item.get("team", {}) or {}
        fix = item.get("fixture", {}) or {}
        league = item.get("league", {}) or {}
        row = {
            "player_id": _int(player.get("id")),
            "player_name": _str(player.get("name")),
            "player_photo": _str(player.get("photo")),
            "team_id": _int(team.get("id")),
            "team_name": _str(team.get("name")),
            "team_logo": _str(team.get("logo")),
            "fixture_id": _int(fix.get("id")),
            "fixture_timezone": _str(fix.get("timezone")),
            "fixture_date": _str(fix.get("date")),
            "fixture_timestamp": _int(fix.get("timestamp")),
            "injury_league_id": _int(league.get("id")),
            "injury_league_name": _str(league.get("name")),
            "injury_league_country": _str(league.get("country")),
            "injury_league_logo": _str(league.get("logo")),
            "injury_league_flag": _str(league.get("flag")),
            "injury_league_season": _int(league.get("season")),
            "injury_type": _str(item.get("type")),
            "injury_reason": _str(item.get("reason")),
            **_meta(ctx),
        }
        rows.append(row)
    return rows


# ── Endpoint registry ────────────────────────────────────────────────────────

# Maps raw endpoint name → (output_table, flattener_fn)
# The 4 leaderboard endpoints share an output table via partial application.

Flattener = Callable[[dict, FlattenContext], list[dict]]

ENDPOINT_REGISTRY: dict[str, tuple[str, Flattener]] = {
    "fixtures": ("fixtures", flatten_fixtures),
    "teams": ("teams", flatten_teams),
    "standings": ("team_standings", flatten_team_standings),
    "fixtures_rounds": ("rounds", flatten_rounds),
    "players": ("player_season_stats", flatten_player_season_stats),
    "players_topscorers": (
        "player_leaderboards",
        partial(flatten_player_leaderboards, ranking_type="top_scorers"),
    ),
    "players_topassists": (
        "player_leaderboards",
        partial(flatten_player_leaderboards, ranking_type="top_assists"),
    ),
    "players_topyellowcards": (
        "player_leaderboards",
        partial(flatten_player_leaderboards, ranking_type="top_yellow_cards"),
    ),
    "players_topredcards": (
        "player_leaderboards",
        partial(flatten_player_leaderboards, ranking_type="top_red_cards"),
    ),
    "teams_statistics": ("team_statistics", flatten_team_statistics),
    "injuries": ("injuries", flatten_injuries),
    "transfers": ("transfers", flatten_transfers),
    "players_squads": ("squad_players", flatten_squad_players),
    "fixtures_statistics": ("match_team_stats", flatten_match_team_stats),
    "fixtures_events": ("match_events", flatten_match_events),
    "fixtures_lineups": ("lineup_players", flatten_lineup_players),
    "fixtures_players": ("match_player_stats", flatten_match_player_stats),
    "predictions": ("predictions", flatten_predictions),
}

# ── Entity-level dedup configs ───────────────────────────────────────────────

# (partition_by_cols, order_by_cols_desc, coalesce_defaults)
ENTITY_DEDUP: dict[str, tuple[list[str], list[str], dict[str, Any]]] = {
    "player_season_stats": (
        ["player_id", "team_id", "stats_season", "stats_league_id", "league_id", "season"],
        ["_loaded_at"],
        {},
    ),
    "transfers": (
        ["league_id", "season", "player_id", "transfer_date", "from_team_id", "to_team_id", "transfer_type"],
        ["_loaded_at"],
        {"from_team_id": -1, "to_team_id": -1, "transfer_type": "na"},
    ),
    "match_player_stats": (
        ["league_id", "season", "fixture_id", "team_id", "player_id"],
        ["minutes_played", "rating", "_loaded_at"],
        {},
    ),
}


# ── Dedup engine ─────────────────────────────────────────────────────────────


def _source_dedup(raw_docs: list[dict]) -> list[dict]:
    """Keep latest raw document per entity_key (by fetched_at)."""
    by_key: dict[str, dict] = {}
    for doc in raw_docs:
        ek = doc.get("entity_key", "")
        existing = by_key.get(ek)
        if existing is None or doc.get("fetched_at", "") > existing.get("fetched_at", ""):
            by_key[ek] = doc
    return list(by_key.values())


def _entity_dedup(
    df: pl.DataFrame,
    partition_cols: list[str],
    order_cols_desc: list[str],
    coalesce_defaults: dict[str, Any],
) -> pl.DataFrame:
    """Polars-based row_number() dedup matching the SQL QUALIFY pattern."""
    if df.is_empty():
        return df

    # Apply coalesce (fill_null) for partition columns that need it
    exprs = []
    for col in partition_cols:
        if col in coalesce_defaults:
            exprs.append(pl.col(col).fill_null(coalesce_defaults[col]).alias(f"_dedup_{col}"))

    if exprs:
        df = df.with_columns(exprs)
        actual_partition = [
            f"_dedup_{c}" if c in coalesce_defaults else c for c in partition_cols
        ]
    else:
        actual_partition = partition_cols

    # Build sort expressions (all descending, nulls last)
    sort_exprs = []
    for col in order_cols_desc:
        sort_exprs.append(pl.col(col).fill_null(pl.lit(-1 if df.schema.get(col) in (pl.Int32, pl.Int64, pl.Float64) else "")))

    df = df.with_columns(
        pl.struct(actual_partition)
        .alias("_partition_key")
    )

    # Sort and deduplicate
    df = df.sort(sort_exprs, descending=True, nulls_last=True)
    df = df.unique(subset=actual_partition, keep="first")

    # Drop helper columns
    drop_cols = ["_partition_key"] + [c for c in df.columns if c.startswith("_dedup_")]
    df = df.drop([c for c in drop_cols if c in df.columns])

    return df


# ── Parquet writing ──────────────────────────────────────────────────────────


def _rows_to_parquet(rows: list[dict], schema: pa.Schema) -> bytes:
    """Convert flattened row dicts to Parquet bytes using the given schema."""
    if not rows:
        # Write empty Parquet with correct schema
        table = pa.table({f.name: pa.array([], type=f.type) for f in schema}, schema=schema)
    else:
        arrays = {}
        for field in schema:
            values = [row.get(field.name) for row in rows]
            arrays[field.name] = pa.array(values, type=field.type)
        table = pa.table(arrays, schema=schema)

    buf = io.BytesIO()
    pq.write_table(table, buf, compression="snappy")
    return buf.getvalue()


def _empty_dataframe_from_schema(schema: pa.Schema) -> pl.DataFrame:
    """Build an empty Polars frame that preserves the declared output schema."""
    table = pa.table({field.name: pa.array([], type=field.type) for field in schema}, schema=schema)
    return pl.from_arrow(table)


def normalize_warehouse_uri(
    uri: str | None,
    *,
    default_database: str | None = None,
    default_schema: str | None = None,
) -> str | None:
    """Ensure Snowflake URIs include database/schema context for unqualified writes."""
    if not uri:
        return uri

    parts = urlsplit(uri)
    if parts.scheme != "snowflake":
        return uri

    path_parts = [part for part in parts.path.split("/") if part]
    if len(path_parts) >= 2:
        return uri

    database = path_parts[0] if path_parts else (default_database or "")
    schema = default_schema or ""
    if not database or not schema:
        return uri

    return urlunsplit((parts.scheme, parts.netloc, f"/{database}/{schema}", parts.query, parts.fragment))


def warehouse_target_parts(warehouse_uri: str | None) -> tuple[str | None, str | None]:
    """Return (database, schema) for Snowflake URIs when present."""
    if not warehouse_uri:
        return None, None

    parts = urlsplit(warehouse_uri)
    if parts.scheme != "snowflake":
        return None, None

    path_parts = [part for part in parts.path.split("/") if part]
    database = path_parts[0] if len(path_parts) >= 1 else None
    schema = path_parts[1] if len(path_parts) >= 2 else None
    return database, schema


def warehouse_identifier(table_name: str, warehouse_uri: str | None = None) -> str:
    """Return a fully qualified warehouse identifier when context is available."""
    database, schema = warehouse_target_parts(warehouse_uri)
    parts = [part for part in (database, schema, table_name) if part]
    return ".".join(parts) if parts else table_name


def warehouse_table_name(output_table: str) -> str:
    """Physical Snowflake table name for flattened curated outputs."""
    return output_table.upper()


def warehouse_table_identifier(output_table: str, warehouse_uri: str | None = None) -> str:
    """Return a fully qualified warehouse identifier when context is available."""
    return warehouse_identifier(warehouse_table_name(output_table), warehouse_uri)


def _quote_sql_identifier(identifier: str) -> str:
    return ".".join(f'"{part.replace("\"", "\"\"")}"' for part in identifier.split("."))


def _replace_snowflake_slice(
    df: pl.DataFrame,
    output_table: str,
    warehouse_uri: str,
    *,
    league_id: int,
    season: int,
    dt: date,
    run_id: str,
) -> None:
    """Replace a league/season/day slice atomically via a temporary table."""
    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise RuntimeError(
            "Snowflake direct loads now require sqlalchemy and snowflake-sqlalchemy "
            "to replace warehouse slices idempotently."
        ) from exc

    target_identifier = warehouse_table_identifier(output_table, warehouse_uri)
    temp_suffix = re.sub(r"[^A-Za-z0-9_]", "_", run_id)[:48]
    temp_table_name = f"__tmp_{warehouse_table_name(output_table)}_{temp_suffix}".upper()
    temp_identifier = warehouse_identifier(temp_table_name, warehouse_uri)
    quoted_target = _quote_sql_identifier(target_identifier)
    quoted_temp = _quote_sql_identifier(temp_identifier)
    params = {"league_id": league_id, "season": season, "dt": dt.isoformat()}
    engine = create_engine(warehouse_uri)

    try:
        df.write_database(
            table_name=temp_table_name,
            connection=warehouse_uri,
            if_table_exists="replace",
        )

        with engine.begin() as conn:
            conn.execute(text(f"CREATE TABLE IF NOT EXISTS {quoted_target} LIKE {quoted_temp}"))
            conn.execute(
                text(
                    f"""
                    DELETE FROM {quoted_target}
                    WHERE league_id = :league_id
                      AND season = :season
                      AND dt = :dt
                    """
                ),
                params,
            )
            conn.execute(text(f"INSERT INTO {quoted_target} SELECT * FROM {quoted_temp}"))
    finally:
        try:
            with engine.begin() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {quoted_temp}"))
        finally:
            engine.dispose()


def resolve_warehouse_backend(warehouse_backend: str | None, warehouse_uri: str | None) -> str:
    """Normalize direct warehouse backend selection for runtime calls."""
    explicit = (warehouse_backend or "").strip().lower()
    if explicit == "none":
        return "none"

    if explicit == "":
        if not warehouse_uri:
            return "none"
        inferred = urlsplit(warehouse_uri).scheme
        if inferred == "snowflake":
            return "snowflake"
        raise ValueError(
            f"Unsupported direct warehouse backend inferred from warehouse URI scheme '{inferred}'. "
            "Set DATA_WAREHOUSE=none to disable direct loads."
        )

    if explicit != "snowflake":
        raise ValueError(
            f"Unsupported warehouse backend '{explicit}'. Supported values are 'snowflake' and 'none'."
        )

    if not warehouse_uri:
        raise ValueError("warehouse_backend='snowflake' requires a warehouse URI.")

    if urlsplit(warehouse_uri).scheme != "snowflake":
        raise ValueError("warehouse_backend='snowflake' requires a snowflake:// warehouse URI.")

    return "snowflake"


# ── Main orchestration ───────────────────────────────────────────────────────


def run_flatten(
    writer: StorageWriter,
    league_id: int,
    season: int,
    dt: date,
    run_id: str | None = None,
    warehouse_backend: str | None = None,
    warehouse_uri: str | None = None,
) -> dict[str, int]:
    """Read raw JSON, flatten to Parquet, write to curated/.

    Returns a summary dict with row counts per output table.
    """
    if run_id is None:
        run_id = generate_run_id()
    warehouse_backend = resolve_warehouse_backend(warehouse_backend, warehouse_uri)

    loaded_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    ctx = FlattenContext(
        league_id=league_id,
        season=season,
        dt=dt.isoformat(),
        run_id=run_id,
        loaded_at=loaded_at,
    )

    # Group registry entries by output table
    output_groups: dict[str, list[tuple[str, Flattener]]] = defaultdict(list)
    for raw_ep, (output_table, flatten_fn) in ENDPOINT_REGISTRY.items():
        output_groups[output_table].append((raw_ep, flatten_fn))

    summary: dict[str, int] = {}

    for output_table, sources in output_groups.items():
        all_rows: list[dict] = []
        had_raw_input = False

        for raw_ep, flatten_fn in sources:
            ep_normalized = normalize_endpoint(raw_ep)
            raw_keys = writer.list_raw(league_id, season, ep_normalized, dt)
            if not raw_keys:
                logger.debug("No raw files for endpoint=%s", raw_ep)
                continue
            had_raw_input = True

            # Read all raw docs for this endpoint
            raw_docs = []
            for key in raw_keys:
                try:
                    doc = writer.get_raw(key)
                    raw_docs.append(doc)
                except Exception:
                    logger.warning("Failed to read raw file: %s", key, exc_info=True)

            # Source-level dedup: keep latest per entity_key
            deduped_docs = _source_dedup(raw_docs)
            logger.debug(
                "endpoint=%s raw_files=%d after_source_dedup=%d",
                raw_ep, len(raw_docs), len(deduped_docs),
            )

            # Flatten each document
            for doc in deduped_docs:
                try:
                    rows = flatten_fn(doc, ctx)
                    all_rows.extend(rows)
                except Exception:
                    logger.warning("Failed to flatten doc entity_key=%s", doc.get("entity_key"), exc_info=True)

        schema = SCHEMAS[output_table]

        # Entity-level dedup if configured
        if output_table in ENTITY_DEDUP and all_rows:
            partition_cols, order_cols, coalesce_defaults = ENTITY_DEDUP[output_table]
            df = pl.DataFrame(all_rows)
            df = _entity_dedup(df, partition_cols, order_cols, coalesce_defaults)
            all_rows = df.to_dicts()
        elif all_rows:
            df = pl.DataFrame(all_rows)
        else:
            df = _empty_dataframe_from_schema(schema)

        # Write Parquet
        parquet_bytes = _rows_to_parquet(all_rows, schema)
        out_key = writer.put_curated(league_id, season, output_table, dt, run_id, parquet_bytes)
        summary[output_table] = len(all_rows)
        logger.info("Wrote %d rows to %s", len(all_rows), out_key)

        # Push to Warehouse if URI is provided
        if warehouse_backend != "none" and warehouse_uri:
            full_name = warehouse_table_identifier(output_table, warehouse_uri)
            if not had_raw_input:
                logger.info(
                    "Skipping warehouse push for %s; no raw input found for league_id=%s season=%s dt=%s",
                    full_name,
                    league_id,
                    season,
                    dt.isoformat(),
                )
                continue

            logger.info("Syncing %d rows to warehouse table %s", len(df), full_name)
            try:
                if warehouse_backend == "snowflake":
                    _replace_snowflake_slice(
                        df,
                        output_table,
                        warehouse_uri,
                        league_id=league_id,
                        season=season,
                        dt=dt,
                        run_id=run_id,
                    )
                else:
                    raise RuntimeError(
                        f"Direct warehouse sync is not implemented for backend '{warehouse_backend}'. "
                        "Set DATA_WAREHOUSE=none to disable direct loads."
                    )
            except Exception as e:
                logger.error("Failed to push %s to warehouse: %s", full_name, e)
                raise WarehouseSyncError(
                    f"Warehouse sync failed for curated table {full_name}"
                ) from e

    return summary


# ── CLI entry point ──────────────────────────────────────────────────────────


def _cli_main() -> None:
    parser = argparse.ArgumentParser(description="Flatten raw JSON to curated Parquet.")
    parser.add_argument("--date", required=True, help="Run date YYYY-MM-DD.")
    parser.add_argument("--league-id", type=int, default=None, help="Override league ID.")
    parser.add_argument("--season", type=int, default=None, help="Override season.")
    parser.add_argument("--warehouse-backend", default=None, help="Direct warehouse backend (for example: snowflake or none).")
    parser.add_argument("--warehouse-uri", default=None, help="Warehouse connection string for direct load.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

    from .config import load_configs_from_file
    from .storage import create_writer

    run_date = date.fromisoformat(args.date)
    configs = load_configs_from_file(args.config)
    run_id = generate_run_id()

    for config in configs:
        lid = args.league_id or config.league_id
        szn = args.season or config.season
        writer = create_writer(
            config.storage_backend,
            local_root=config.local_root,
            s3_bucket=config.s3_bucket,
            aws_region=config.aws_region,
            gcs_bucket=config.gcs_bucket,
            gcs_project=config.gcs_project,
        )
        start = perf_counter()
        logger.info("Flattening league_id=%d season=%d dt=%s", lid, szn, run_date)
        
        uri = args.warehouse_uri or config.warehouse_uri
        warehouse_backend = args.warehouse_backend or config.warehouse_backend
        summary = run_flatten(
            writer,
            lid,
            szn,
            run_date,
            run_id,
            warehouse_backend=warehouse_backend,
            warehouse_uri=uri,
        )
        logger.info(
            "Flatten complete league_id=%d in %.2fs: %s",
            lid, perf_counter() - start, summary,
        )


if __name__ == "__main__":
    _cli_main()
