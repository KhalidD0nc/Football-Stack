"""Unit tests for the flatten module.

Covers:
- 15 flattener functions (one per output table)
- 4 dedup scenarios (source-level + entity-level)
- Schema conformance
- Parquet round-trip integrity
- End-to-end integration with LocalFileWriter
"""

from __future__ import annotations

import io
import json
from datetime import date
from typing import Any

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.pipeline.flatten import (
    ENDPOINT_REGISTRY,
    ENTITY_DEDUP,
    FlattenContext,
    _empty_dataframe_from_schema,
    _entity_dedup,
    _rows_to_parquet,
    _source_dedup,
    flatten_fixtures,
    flatten_injuries,
    flatten_lineup_players,
    flatten_match_events,
    flatten_match_player_stats,
    flatten_match_team_stats,
    flatten_player_leaderboards,
    flatten_player_season_stats,
    flatten_predictions,
    flatten_rounds,
    flatten_squad_players,
    flatten_team_standings,
    flatten_team_statistics,
    flatten_teams,
    flatten_transfers,
    parse_pct,
    run_flatten,
    warehouse_table_identifier,
)
from src.pipeline.schemas import SCHEMAS
from src.pipeline.storage import LocalFileWriter
from tests.fixtures.sample_raw import (
    FIXTURES_RAW,
    INJURIES_RAW,
    LINEUP_PLAYERS_RAW,
    MATCH_EVENTS_RAW,
    MATCH_PLAYER_STATS_RAW,
    MATCH_TEAM_STATS_RAW,
    PLAYER_LEADERBOARDS_RAW_TOPSCORERS,
    PLAYER_SEASON_STATS_RAW,
    PREDICTIONS_RAW,
    ROUNDS_RAW,
    SQUAD_PLAYERS_RAW,
    TEAM_STANDINGS_RAW,
    TEAM_STATISTICS_RAW,
    TEAMS_RAW,
    TRANSFERS_RAW,
)

CTX = FlattenContext(
    league_id=307,
    season=2024,
    dt="2025-01-15",
    run_id="20250115T120000Z",
    loaded_at="2025-01-15T12:00:00Z",
)


# ===========================================================================
# Helper
# ===========================================================================


def _assert_meta(row: dict) -> None:
    """Assert all metadata fields are present and correct."""
    assert row["league_id"] == 307
    assert row["season"] == 2024
    assert row["dt"] == "2025-01-15"
    assert row["run_id"] == "20250115T120000Z"
    assert row["_loaded_at"] == "2025-01-15T12:00:00Z"


# ===========================================================================
# Utility tests
# ===========================================================================


class TestParsePct:
    def test_normal(self) -> None:
        assert parse_pct("55%") == 55.0

    def test_none(self) -> None:
        assert parse_pct(None) is None

    def test_no_pct_sign(self) -> None:
        assert parse_pct("75") == 75.0


class TestWarehouseHelpers:
    def test_warehouse_table_identifier_qualifies_snowflake_tables(self) -> None:
        identifier = warehouse_table_identifier(
            "injuries",
            "snowflake://user:pass@example.snowflakecomputing.com/LEAGUES_DATA_TEST/STAGING",
        )

        assert identifier == "STAGING.injuries"

    def test_empty_dataframe_preserves_schema(self) -> None:
        df = _empty_dataframe_from_schema(SCHEMAS["injuries"])

        assert df.is_empty()
        assert df.columns == SCHEMAS["injuries"].names

    def test_run_flatten_uses_typed_empty_dataframe_for_warehouse_writes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Any,
    ) -> None:
        writer = LocalFileWriter(root=tmp_path)
        league_id = 307
        season = 2024
        dt = date(2025, 1, 15)
        run_id = "20250115T120000Z"
        captured: dict[str, list[str]] = {}

        writer.put_raw(
            league_id=league_id,
            season=season,
            endpoint="injuries",
            dt=dt,
            run_id=run_id,
            part=1,
            body={"payload": {"response": []}},
        )

        def fake_write_database(
            self: pl.DataFrame,
            *,
            table_name: str,
            connection: str,
            if_table_exists: str,
        ) -> None:
            captured[table_name] = self.columns

        monkeypatch.setattr(pl.DataFrame, "write_database", fake_write_database)

        summary = run_flatten(
            writer,
            league_id,
            season,
            dt,
            run_id=run_id,
            warehouse_uri="snowflake://user:pass@example.snowflakecomputing.com/LEAGUES_DATA_TEST/STAGING",
        )

        assert summary["injuries"] == 0
        assert captured["STAGING.injuries"] == SCHEMAS["injuries"].names


# ===========================================================================
# Flattener unit tests (15)
# ===========================================================================


class TestFlattenTeams:
    def test_row_count(self) -> None:
        rows = flatten_teams(TEAMS_RAW, CTX)
        assert len(rows) == 2

    def test_values(self) -> None:
        rows = flatten_teams(TEAMS_RAW, CTX)
        r = rows[0]
        assert r["team_id"] == 2932
        assert r["team_name"] == "Al Hilal"
        assert r["team_code"] == "HIL"
        assert r["venue_capacity"] == 67000
        assert r["is_national_team"] is False
        _assert_meta(r)


class TestFlattenFixtures:
    def test_row_count(self) -> None:
        rows = flatten_fixtures(FIXTURES_RAW, CTX)
        assert len(rows) == 1

    def test_values(self) -> None:
        rows = flatten_fixtures(FIXTURES_RAW, CTX)
        r = rows[0]
        assert r["fixture_id"] == 1001
        assert r["home_team_id"] == 2932
        assert r["away_team_id"] == 2934
        assert r["home_goals"] == 2
        assert r["away_goals"] == 1
        assert r["halftime_home_goals"] == 1
        assert r["status_short"] == "FT"
        assert r["round_name"] == "Regular Season - 15"
        assert r["home_team_winner"] is True
        _assert_meta(r)


class TestFlattenRounds:
    def test_row_count(self) -> None:
        rows = flatten_rounds(ROUNDS_RAW, CTX)
        assert len(rows) == 3

    def test_round_number_extraction(self) -> None:
        rows = flatten_rounds(ROUNDS_RAW, CTX)
        assert rows[0]["round_number"] == 1
        assert rows[1]["round_number"] == 2
        assert rows[2]["round_number"] == 1  # "Playoffs - Round 1"


class TestFlattenMatchEvents:
    def test_row_count(self) -> None:
        rows = flatten_match_events(MATCH_EVENTS_RAW, CTX)
        assert len(rows) == 2

    def test_values(self) -> None:
        rows = flatten_match_events(MATCH_EVENTS_RAW, CTX)
        r = rows[0]
        assert r["fixture_id"] == 1001
        assert r["event_sequence"] == 0
        assert r["event_minute"] == 23
        assert r["event_type"] == "Goal"
        assert r["assist_player_id"] == 502
        _assert_meta(r)

    def test_extra_minute(self) -> None:
        rows = flatten_match_events(MATCH_EVENTS_RAW, CTX)
        assert rows[1]["event_extra_minute"] == 2


class TestFlattenMatchTeamStats:
    def test_row_count(self) -> None:
        rows = flatten_match_team_stats(MATCH_TEAM_STATS_RAW, CTX)
        assert len(rows) == 1

    def test_pivot_values(self) -> None:
        rows = flatten_match_team_stats(MATCH_TEAM_STATS_RAW, CTX)
        r = rows[0]
        assert r["fixture_id"] == 1001
        assert r["ball_possession_pct"] == 55.0
        assert r["total_shots"] == 12
        assert r["passes_pct"] == 84.0
        assert r["expected_goals"] == 1.75
        assert r["goals_prevented"] == 0.5
        assert r["total_passes"] == 450
        _assert_meta(r)


class TestFlattenMatchPlayerStats:
    def test_row_count(self) -> None:
        rows = flatten_match_player_stats(MATCH_PLAYER_STATS_RAW, CTX)
        assert len(rows) == 1

    def test_values(self) -> None:
        rows = flatten_match_player_stats(MATCH_PLAYER_STATS_RAW, CTX)
        r = rows[0]
        assert r["fixture_id"] == 1001
        assert r["player_id"] == 501
        assert r["rating"] == 7.8
        assert r["minutes_played"] == 90
        assert r["goals_total"] == 1
        assert r["passes_total"] == 45
        _assert_meta(r)


class TestFlattenLineupPlayers:
    def test_row_count(self) -> None:
        rows = flatten_lineup_players(LINEUP_PLAYERS_RAW, CTX)
        assert len(rows) == 2  # 1 startXI + 1 sub

    def test_buckets(self) -> None:
        rows = flatten_lineup_players(LINEUP_PLAYERS_RAW, CTX)
        buckets = [r["lineup_bucket"] for r in rows]
        assert "start_xi" in buckets
        assert "substitutes" in buckets

    def test_values(self) -> None:
        rows = flatten_lineup_players(LINEUP_PLAYERS_RAW, CTX)
        starter = [r for r in rows if r["lineup_bucket"] == "start_xi"][0]
        assert starter["player_id"] == 501
        assert starter["formation"] == "4-3-3"
        assert starter["team_colors_player_primary"] == "#0000FF"
        _assert_meta(starter)


class TestFlattenPredictions:
    def test_row_count(self) -> None:
        rows = flatten_predictions(PREDICTIONS_RAW, CTX)
        assert len(rows) == 1

    def test_values(self) -> None:
        rows = flatten_predictions(PREDICTIONS_RAW, CTX)
        r = rows[0]
        assert r["fixture_id"] == 1001
        assert r["predicted_winner_team_id"] == 2932
        assert r["home_win_percent"] == "55%"
        assert r["home_win_percent_value"] == 55.0
        assert r["comparison_form_home"] == "70%"
        _assert_meta(r)


class TestFlattenPlayerSeasonStats:
    def test_row_count(self) -> None:
        rows = flatten_player_season_stats(PLAYER_SEASON_STATS_RAW, CTX)
        assert len(rows) == 1

    def test_values(self) -> None:
        rows = flatten_player_season_stats(PLAYER_SEASON_STATS_RAW, CTX)
        r = rows[0]
        assert r["player_id"] == 501
        assert r["player_name"] == "Player A"
        assert r["appearances"] == 15
        assert r["goals_total"] == 8
        assert r["assists_total"] == 5
        assert r["rating"] == 7.5
        assert r["yellow_cards"] == 3
        assert r["stats_league_id"] == 307
        _assert_meta(r)


class TestFlattenPlayerLeaderboards:
    def test_row_count(self) -> None:
        rows = flatten_player_leaderboards(PLAYER_LEADERBOARDS_RAW_TOPSCORERS, CTX, ranking_type="top_scorers")
        assert len(rows) == 2

    def test_ranking(self) -> None:
        rows = flatten_player_leaderboards(PLAYER_LEADERBOARDS_RAW_TOPSCORERS, CTX, ranking_type="top_scorers")
        assert rows[0]["rank"] == 1
        assert rows[1]["rank"] == 2

    def test_values(self) -> None:
        rows = flatten_player_leaderboards(PLAYER_LEADERBOARDS_RAW_TOPSCORERS, CTX, ranking_type="top_scorers")
        r = rows[0]
        assert r["ranking_type"] == "top_scorers"
        assert r["player_id"] == 501
        assert r["goals_total"] == 12
        _assert_meta(r)


class TestFlattenSquadPlayers:
    def test_row_count(self) -> None:
        rows = flatten_squad_players(SQUAD_PLAYERS_RAW, CTX)
        assert len(rows) == 2

    def test_values(self) -> None:
        rows = flatten_squad_players(SQUAD_PLAYERS_RAW, CTX)
        r = rows[0]
        assert r["team_id"] == 2932
        assert r["player_id"] == 501
        assert r["position"] == "Midfielder"
        _assert_meta(r)


class TestFlattenTeamStandings:
    def test_row_count(self) -> None:
        rows = flatten_team_standings(TEAM_STANDINGS_RAW, CTX)
        assert len(rows) == 1

    def test_values(self) -> None:
        rows = flatten_team_standings(TEAM_STANDINGS_RAW, CTX)
        r = rows[0]
        assert r["standing_rank"] == 1
        assert r["team_id"] == 2932
        assert r["points"] == 38
        assert r["all_goals_for"] == 35
        assert r["goals_diff"] == 25
        _assert_meta(r)


class TestFlattenTeamStatistics:
    def test_row_count(self) -> None:
        rows = flatten_team_statistics(TEAM_STATISTICS_RAW, CTX)
        assert len(rows) == 1

    def test_values(self) -> None:
        rows = flatten_team_statistics(TEAM_STATISTICS_RAW, CTX)
        r = rows[0]
        assert r["team_id"] == 2932
        assert r["fixtures_played_total"] == 15
        assert r["goals_for_total"] == 35
        assert r["goals_for_avg_home"] == 2.5
        assert r["clean_sheets_total"] == 8
        assert r["biggest_streak_wins"] == 8
        assert r["biggest_win_home"] == "5-0"
        _assert_meta(r)


class TestFlattenTransfers:
    def test_row_count(self) -> None:
        rows = flatten_transfers(TRANSFERS_RAW, CTX)
        assert len(rows) == 2

    def test_values(self) -> None:
        rows = flatten_transfers(TRANSFERS_RAW, CTX)
        r = rows[0]
        assert r["player_id"] == 501
        assert r["transfer_type"] == "Free"
        assert r["to_team_id"] == 2932
        assert r["from_team_id"] == 100
        _assert_meta(r)


class TestFlattenInjuries:
    def test_row_count(self) -> None:
        rows = flatten_injuries(INJURIES_RAW, CTX)
        assert len(rows) == 1

    def test_values(self) -> None:
        rows = flatten_injuries(INJURIES_RAW, CTX)
        r = rows[0]
        assert r["player_id"] == 502
        assert r["injury_type"] == "Muscle Injury"
        assert r["injury_reason"] == "Hamstring"
        assert r["fixture_id"] == 1001
        _assert_meta(r)


# ===========================================================================
# Dedup tests (4)
# ===========================================================================


class TestSourceDedup:
    def test_keeps_latest_by_fetched_at(self) -> None:
        docs = [
            {"entity_key": "ek1", "fetched_at": "2025-01-15T10:00:00Z", "payload": {"response": []}},
            {"entity_key": "ek1", "fetched_at": "2025-01-15T12:00:00Z", "payload": {"response": [{"id": 1}]}},
            {"entity_key": "ek2", "fetched_at": "2025-01-15T09:00:00Z", "payload": {"response": []}},
        ]
        result = _source_dedup(docs)
        assert len(result) == 2
        ek1_doc = [d for d in result if d["entity_key"] == "ek1"][0]
        assert ek1_doc["fetched_at"] == "2025-01-15T12:00:00Z"


class TestEntityDedupPlayerSeasonStats:
    def test_dedup_by_player_team_season(self) -> None:
        import polars as pl

        rows = [
            {"player_id": 1, "team_id": 10, "stats_season": 2024, "stats_league_id": 307,
             "league_id": 307, "season": 2024, "_loaded_at": "2025-01-15T10:00:00Z", "goals_total": 5},
            {"player_id": 1, "team_id": 10, "stats_season": 2024, "stats_league_id": 307,
             "league_id": 307, "season": 2024, "_loaded_at": "2025-01-15T12:00:00Z", "goals_total": 8},
        ]
        df = pl.DataFrame(rows)
        partition_cols, order_cols, defaults = ENTITY_DEDUP["player_season_stats"]
        result = _entity_dedup(df, partition_cols, order_cols, defaults)
        assert len(result) == 1
        assert result["goals_total"][0] == 8  # latest _loaded_at wins


class TestEntityDedupTransfers:
    def test_dedup_with_coalesce(self) -> None:
        import polars as pl

        rows = [
            {"league_id": 307, "season": 2024, "player_id": 1, "transfer_date": "2024-07-01",
             "from_team_id": None, "to_team_id": 10, "transfer_type": "Free",
             "_loaded_at": "2025-01-15T10:00:00Z"},
            {"league_id": 307, "season": 2024, "player_id": 1, "transfer_date": "2024-07-01",
             "from_team_id": None, "to_team_id": 10, "transfer_type": "Free",
             "_loaded_at": "2025-01-15T12:00:00Z"},
        ]
        df = pl.DataFrame(rows)
        partition_cols, order_cols, defaults = ENTITY_DEDUP["transfers"]
        result = _entity_dedup(df, partition_cols, order_cols, defaults)
        assert len(result) == 1


class TestEntityDedupMatchPlayerStats:
    def test_dedup_by_minutes_rating(self) -> None:
        import polars as pl

        rows = [
            {"league_id": 307, "season": 2024, "fixture_id": 1001, "team_id": 10, "player_id": 501,
             "minutes_played": 45, "rating": 6.5, "_loaded_at": "2025-01-15T10:00:00Z"},
            {"league_id": 307, "season": 2024, "fixture_id": 1001, "team_id": 10, "player_id": 501,
             "minutes_played": 90, "rating": 7.8, "_loaded_at": "2025-01-15T10:00:00Z"},
        ]
        df = pl.DataFrame(rows)
        partition_cols, order_cols, defaults = ENTITY_DEDUP["match_player_stats"]
        result = _entity_dedup(df, partition_cols, order_cols, defaults)
        assert len(result) == 1
        assert result["minutes_played"][0] == 90


# ===========================================================================
# Schema conformance tests
# ===========================================================================


class TestSchemaConformance:
    """Verify flattener output matches the PyArrow schema column names."""

    _FLATTENER_FIXTURES: list[tuple[str, Callable, dict]] = [
        ("teams", flatten_teams, TEAMS_RAW),
        ("fixtures", flatten_fixtures, FIXTURES_RAW),
        ("rounds", flatten_rounds, ROUNDS_RAW),
        ("match_events", flatten_match_events, MATCH_EVENTS_RAW),
        ("match_team_stats", flatten_match_team_stats, MATCH_TEAM_STATS_RAW),
        ("match_player_stats", flatten_match_player_stats, MATCH_PLAYER_STATS_RAW),
        ("lineup_players", flatten_lineup_players, LINEUP_PLAYERS_RAW),
        ("predictions", flatten_predictions, PREDICTIONS_RAW),
        ("player_season_stats", flatten_player_season_stats, PLAYER_SEASON_STATS_RAW),
        ("squad_players", flatten_squad_players, SQUAD_PLAYERS_RAW),
        ("team_standings", flatten_team_standings, TEAM_STANDINGS_RAW),
        ("team_statistics", flatten_team_statistics, TEAM_STATISTICS_RAW),
        ("transfers", flatten_transfers, TRANSFERS_RAW),
        ("injuries", flatten_injuries, INJURIES_RAW),
    ]

    @pytest.mark.parametrize("table_name,flatten_fn,raw_data", _FLATTENER_FIXTURES, ids=[t[0] for t in _FLATTENER_FIXTURES])
    def test_column_names_match_schema(self, table_name: str, flatten_fn: Any, raw_data: dict) -> None:
        rows = flatten_fn(raw_data, CTX)
        assert len(rows) > 0, f"No rows returned for {table_name}"
        row_keys = set(rows[0].keys())
        schema_names = set(SCHEMAS[table_name].names)
        assert row_keys == schema_names, f"Column mismatch for {table_name}: extra={row_keys - schema_names}, missing={schema_names - row_keys}"

    def test_leaderboards_column_names(self) -> None:
        rows = flatten_player_leaderboards(PLAYER_LEADERBOARDS_RAW_TOPSCORERS, CTX, ranking_type="top_scorers")
        row_keys = set(rows[0].keys())
        schema_names = set(SCHEMAS["player_leaderboards"].names)
        assert row_keys == schema_names


# ===========================================================================
# Parquet round-trip test
# ===========================================================================


class TestParquetRoundTrip:
    @pytest.mark.parametrize("table_name", list(SCHEMAS.keys()))
    def test_write_read_roundtrip(self, table_name: str) -> None:
        """Write rows to Parquet bytes, read back, verify schema and data."""
        # Get sample rows
        flattener_map: dict[str, tuple[Any, dict]] = {
            "teams": (flatten_teams, TEAMS_RAW),
            "fixtures": (flatten_fixtures, FIXTURES_RAW),
            "rounds": (flatten_rounds, ROUNDS_RAW),
            "match_events": (flatten_match_events, MATCH_EVENTS_RAW),
            "match_team_stats": (flatten_match_team_stats, MATCH_TEAM_STATS_RAW),
            "match_player_stats": (flatten_match_player_stats, MATCH_PLAYER_STATS_RAW),
            "lineup_players": (flatten_lineup_players, LINEUP_PLAYERS_RAW),
            "predictions": (flatten_predictions, PREDICTIONS_RAW),
            "player_season_stats": (flatten_player_season_stats, PLAYER_SEASON_STATS_RAW),
            "player_leaderboards": (
                lambda raw, ctx: flatten_player_leaderboards(raw, ctx, ranking_type="top_scorers"),
                PLAYER_LEADERBOARDS_RAW_TOPSCORERS,
            ),
            "squad_players": (flatten_squad_players, SQUAD_PLAYERS_RAW),
            "team_standings": (flatten_team_standings, TEAM_STANDINGS_RAW),
            "team_statistics": (flatten_team_statistics, TEAM_STATISTICS_RAW),
            "transfers": (flatten_transfers, TRANSFERS_RAW),
            "injuries": (flatten_injuries, INJURIES_RAW),
        }

        flatten_fn, raw_data = flattener_map[table_name]
        rows = flatten_fn(raw_data, CTX)
        schema = SCHEMAS[table_name]

        parquet_bytes = _rows_to_parquet(rows, schema)
        table = pq.read_table(io.BytesIO(parquet_bytes))

        assert table.num_rows == len(rows)
        assert set(table.schema.names) == set(schema.names)


# ===========================================================================
# Integration test: end-to-end with LocalFileWriter
# ===========================================================================


class TestEndToEndLocalFileWriter:
    def test_full_flatten_pipeline(self, tmp_path: Any) -> None:
        """Write raw JSON → run flatten → verify Parquet output exists."""
        writer = LocalFileWriter(root=tmp_path)
        league_id = 307
        season = 2024
        dt = date(2025, 1, 15)
        run_id = "20250115T120000Z"

        # Write sample raw files
        raw_fixtures_to_write = [
            ("fixtures", FIXTURES_RAW),
            ("teams", TEAMS_RAW),
            ("standings", TEAM_STANDINGS_RAW),
            ("fixtures_rounds", ROUNDS_RAW),
            ("fixtures_events", MATCH_EVENTS_RAW),
            ("fixtures_statistics", MATCH_TEAM_STATS_RAW),
            ("fixtures_players", MATCH_PLAYER_STATS_RAW),
            ("fixtures_lineups", LINEUP_PLAYERS_RAW),
            ("predictions", PREDICTIONS_RAW),
            ("players", PLAYER_SEASON_STATS_RAW),
            ("players_topscorers", PLAYER_LEADERBOARDS_RAW_TOPSCORERS),
            ("players_squads", SQUAD_PLAYERS_RAW),
            ("teams_statistics", TEAM_STATISTICS_RAW),
            ("transfers", TRANSFERS_RAW),
            ("injuries", INJURIES_RAW),
        ]
        for endpoint, raw_data in raw_fixtures_to_write:
            writer.put_raw(
                league_id=league_id,
                season=season,
                endpoint=endpoint,
                dt=dt,
                run_id=run_id,
                part=1,
                body=raw_data,
            )

        # Run flatten
        summary = run_flatten(writer, league_id, season, dt)

        # Verify Parquet files exist
        curated_dir = tmp_path / "curated"
        assert curated_dir.exists()
        parquet_files = list(curated_dir.rglob("*.parquet"))
        # Should have files for all output tables that had data
        assert len(parquet_files) > 0

        # Verify row counts from summary
        assert summary["teams"] == 2
        assert summary["fixtures"] == 1
        assert summary["rounds"] == 3
        assert summary["match_events"] == 2
        assert summary["match_team_stats"] == 1
        assert summary["match_player_stats"] == 1
        assert summary["lineup_players"] == 2
        assert summary["predictions"] == 1
        assert summary["player_season_stats"] == 1
        assert summary["squad_players"] == 2
        assert summary["team_standings"] == 1
        assert summary["team_statistics"] == 1
        assert summary["transfers"] == 2
        assert summary["injuries"] == 1

        # Verify a Parquet file can be read and has correct data
        teams_parquet = [p for p in parquet_files if "endpoint=teams/" in str(p)]
        assert len(teams_parquet) == 1
        table = pq.read_table(io.BytesIO(teams_parquet[0].read_bytes()))
        assert table.num_rows == 2
        assert "team_id" in table.schema.names


# ===========================================================================
# Registry completeness test
# ===========================================================================


class TestRegistryCompleteness:
    def test_all_18_endpoints_registered(self) -> None:
        expected = {
            "fixtures", "teams", "standings", "fixtures_rounds",
            "players", "players_topscorers", "players_topassists",
            "players_topyellowcards", "players_topredcards",
            "teams_statistics", "injuries", "transfers", "players_squads",
            "fixtures_statistics", "fixtures_events", "fixtures_lineups",
            "fixtures_players", "predictions",
        }
        assert set(ENDPOINT_REGISTRY.keys()) == expected

    def test_all_15_output_tables_have_schemas(self) -> None:
        output_tables = {v[0] for v in ENDPOINT_REGISTRY.values()}
        assert len(output_tables) == 15
        for table in output_tables:
            assert table in SCHEMAS, f"Missing schema for {table}"
