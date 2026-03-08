from __future__ import annotations

import logging
from datetime import date
from typing import Any

from .api_client import ApiFootballClient
from .config import PipelineConfig
from .fetch import _build_marker_key, _call_api, _safe_fetch_and_upload, _upload_payload
from .storage import StorageWriter

logger = logging.getLogger(__name__)

DETAIL_ENDPOINTS = [
    "/fixtures/statistics",
    "/fixtures/events",
    "/fixtures/lineups",
    "/fixtures/players",
    "/predictions",
]

FINISHED_STATUSES = {"FT", "AET", "PEN"}


# ── Payload parsers ──────────────────────────────────────────────────────────


def _is_finished_fixture(fixture_row: dict[str, Any]) -> bool:
    fixture = fixture_row.get("fixture", {})
    status = fixture.get("status", {})
    return status.get("short") in FINISHED_STATUSES


def _fixture_id(fixture_row: dict[str, Any]) -> int:
    fixture = fixture_row.get("fixture", {})
    value = fixture.get("id")
    if value is None:
        raise ValueError("Fixture id missing in payload")
    return int(value)


def _fixtures_rows(fixtures_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = fixtures_payload.get("response", [])
    if not isinstance(rows, list):
        raise RuntimeError("Unexpected fixtures payload shape: response must be a list")
    return rows


def select_finished_fixture_ids(fixtures_payload: dict[str, Any]) -> list[int]:
    fixtures = _fixtures_rows(fixtures_payload)
    finished = [row for row in fixtures if _is_finished_fixture(row)]
    fixture_ids = [_fixture_id(row) for row in finished]
    return sorted(set(fixture_ids))


def _team_ids_from_teams_payload(payload: dict[str, Any]) -> list[int]:
    rows = payload.get("response", [])
    if not isinstance(rows, list):
        raise RuntimeError("Unexpected teams payload shape: response must be a list")
    team_ids: list[int] = []
    for row in rows:
        team_id = row.get("team", {}).get("id")
        if team_id is None:
            continue
        team_ids.append(int(team_id))
    return sorted(set(team_ids))


# ── Step 1: Fixtures baseline ────────────────────────────────────────────────


def _ingest_fixtures_baseline(
    client: ApiFootballClient,
    writer: StorageWriter,
    summary: dict[str, int],
    part_counter: Any,
    config: PipelineConfig,
    run_date: date,
    run_id: str,
    force_refresh: bool = False,
) -> tuple[dict[str, Any], list[int]]:
    """Fetch the full fixture list for the league season.

    Always calls the API — fixture IDs are needed for downstream steps.
    Only writes when the marker is absent or force_refresh is set.

    Returns (fixtures_payload, finished_fixture_ids).
    """
    _idem, mk = _build_marker_key(config, run_date, "/fixtures", "league_snapshot")
    params = {"league": config.league_id, "season": config.season, "timezone": config.timezone}
    marker_exists = writer.marker_exists(mk)

    fixtures_payload = _call_api(client, summary, "/fixtures", params)

    if not marker_exists or force_refresh:
        _upload_payload(
            writer=writer,
            summary=summary,
            config=config,
            run_date=run_date,
            run_id=run_id,
            endpoint="/fixtures",
            entity_key="league_snapshot",
            marker_key=mk,
            part=next(part_counter),
            params=params,
            payload=fixtures_payload,
        )
    else:
        summary["skipped_idempotent"] += 1

    rows = _fixtures_rows(fixtures_payload)
    summary["fixtures_total"] = len(rows)

    finished_ids = select_finished_fixture_ids(fixtures_payload)
    summary["fixtures_finished"] = len(finished_ids)

    return fixtures_payload, finished_ids


# ── Step 2: Teams baseline ───────────────────────────────────────────────────


def _ingest_teams_baseline(
    client: ApiFootballClient,
    writer: StorageWriter,
    summary: dict[str, int],
    part_counter: Any,
    config: PipelineConfig,
    run_date: date,
    run_id: str,
    force_refresh: bool = False,
) -> list[int]:
    """Fetch the full team list for the league season.

    Always calls the API — team IDs are needed for downstream steps.
    Only writes when the marker is absent or force_refresh is set.

    Returns sorted list of team IDs.
    """
    _idem, mk = _build_marker_key(config, run_date, "/teams", "league_snapshot")
    params = {"league": config.league_id, "season": config.season}
    marker_exists = writer.marker_exists(mk)

    teams_payload = _call_api(client, summary, "/teams", params)

    if not marker_exists or force_refresh:
        _upload_payload(
            writer=writer,
            summary=summary,
            config=config,
            run_date=run_date,
            run_id=run_id,
            endpoint="/teams",
            entity_key="league_snapshot",
            marker_key=mk,
            part=next(part_counter),
            params=params,
            payload=teams_payload,
        )
    else:
        summary["skipped_idempotent"] += 1

    team_ids = _team_ids_from_teams_payload(teams_payload)
    summary["teams_total"] = len(team_ids)

    return team_ids


# ── Step 3: League-level endpoints ───────────────────────────────────────────


def _ingest_league_endpoints(
    client: ApiFootballClient,
    writer: StorageWriter,
    summary: dict[str, int],
    part_counter: Any,
    config: PipelineConfig,
    run_date: date,
    run_id: str,
    force_refresh: bool = False,
) -> None:
    """Fetch standings, rounds, and player leaderboards for the league season."""
    league_calls = [
        "/standings",
        "/fixtures/rounds",
        "/players/topscorers",
        "/players/topassists",
        "/players/topyellowcards",
        "/players/topredcards",
    ]
    for endpoint in league_calls:
        _safe_fetch_and_upload(
            client=client,
            writer=writer,
            summary=summary,
            part_counter=part_counter,
            config=config,
            run_date=run_date,
            run_id=run_id,
            endpoint=endpoint,
            entity_key="league_snapshot",
            params={"league": config.league_id, "season": config.season},
            force_refresh=force_refresh,
        )


# ── Step 4: Paginated league players ─────────────────────────────────────────


def _ingest_paginated_league_players(
    client: ApiFootballClient,
    writer: StorageWriter,
    summary: dict[str, int],
    part_counter: Any,
    config: PipelineConfig,
    run_date: date,
    run_id: str,
) -> None:
    """Fetch all pages of player season stats for the league."""
    for page in range(1, config.players_max_pages + 1):
        entity_key = f"league_page={page}"
        _idem, mk = _build_marker_key(config, run_date, "/players", entity_key)
        if writer.marker_exists(mk):
            summary["skipped_idempotent"] += 1
            continue

        params = {"league": config.league_id, "season": config.season, "page": page}
        try:
            payload = _call_api(client, summary, "/players", params)
        except Exception:
            summary["endpoint_failures"] += 1
            logger.exception("Failed paginated players fetch page=%s", page)
            break

        summary["players_pages_fetched"] += 1
        _upload_payload(
            writer=writer,
            summary=summary,
            config=config,
            run_date=run_date,
            run_id=run_id,
            endpoint="/players",
            entity_key=entity_key,
            marker_key=mk,
            part=next(part_counter),
            params=params,
            payload=payload,
        )

        paging = payload.get("paging", {})
        current = int(paging.get("current", page) or page)
        total = int(paging.get("total", page) or page)
        if current >= total:
            break


# ── Step 5: Team-level endpoints ─────────────────────────────────────────────


def _ingest_team_endpoints(
    client: ApiFootballClient,
    writer: StorageWriter,
    summary: dict[str, int],
    part_counter: Any,
    config: PipelineConfig,
    run_date: date,
    run_id: str,
    team_ids: list[int],
) -> None:
    """Fetch statistics, injuries, transfers, and squad rosters for every team."""
    for team_id in team_ids:
        team_calls = [
            ("/teams/statistics", {"league": config.league_id, "season": config.season, "team": team_id}),
            ("/injuries",         {"team": team_id, "season": config.season}),
            ("/transfers",        {"team": team_id}),
            ("/players/squads",   {"team": team_id}),
        ]
        for endpoint, params in team_calls:
            _safe_fetch_and_upload(
                client=client,
                writer=writer,
                summary=summary,
                part_counter=part_counter,
                config=config,
                run_date=run_date,
                run_id=run_id,
                endpoint=endpoint,
                entity_key=f"team={team_id}",
                params=params,
            )


# ── Step 6: Deep fixture details ─────────────────────────────────────────────


def _ingest_team_deep_fixture_details(
    client: ApiFootballClient,
    writer: StorageWriter,
    summary: dict[str, int],
    part_counter: Any,
    config: PipelineConfig,
    run_date: date,
    run_id: str,
    fixture_ids: list[int],
) -> None:
    """Fetch per-fixture detail endpoints for all finished fixtures."""
    summary["detail_candidates"] = len(fixture_ids) * len(DETAIL_ENDPOINTS)

    for fixture_id in fixture_ids:
        for endpoint in DETAIL_ENDPOINTS:
            entity_key = f"fixture={fixture_id}"
            _idem, mk = _build_marker_key(
                config, run_date, endpoint, entity_key, include_run_date=False,
            )
            if writer.marker_exists(mk):
                summary["skipped_idempotent"] += 1
                continue

            params = {"fixture": fixture_id}
            try:
                payload = _call_api(client, summary, endpoint, params)
            except Exception:
                summary["detail_failures"] += 1
                summary["endpoint_failures"] += 1
                logger.exception("Failed detail fetch fixture_id=%s endpoint=%s", fixture_id, endpoint)
                continue

            _upload_payload(
                writer=writer,
                summary=summary,
                config=config,
                run_date=run_date,
                run_id=run_id,
                endpoint=endpoint,
                entity_key=entity_key,
                marker_key=mk,
                part=next(part_counter),
                params=params,
                payload=payload,
            )
            summary["detail_writes"] += 1
