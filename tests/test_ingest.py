"""Unit tests for the ingestion pipeline.

Covers:
- Idempotency check happens BEFORE API fetch
- api_attempts tracks real HTTP attempts including retries
- detail_writes key in summary
- LocalFileWriter round-trip
- create_writer factory
"""

from __future__ import annotations

import json
from datetime import date
from itertools import count
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.pipeline.fetch import (
    _call_api,
    _safe_fetch_and_upload,
)
from src.pipeline.steps import (
    _ingest_paginated_league_players,
    _ingest_team_deep_fixture_details,
    DETAIL_ENDPOINTS,
)
from src.pipeline.config import PipelineConfig
from src.pipeline.storage import (
    LocalFileWriter,
    create_writer,
    idempotency_key_from_parts,
    marker_key_without_date,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DUMMY_CONFIG = PipelineConfig(
    api_football_key="test-key",
    api_base_url="https://example.com",
    league_id=307,
    season=2025,
    timezone="UTC",
    players_max_pages=3,
    storage_backend="local",
    local_root="data_lake",
)

RUN_DATE = date(2025, 6, 1)
RUN_ID = "20250601T000000Z"

DUMMY_PAYLOAD: dict[str, Any] = {"response": [], "paging": {"current": 1, "total": 1}}


def _fresh_summary() -> dict[str, int]:
    return {
        "fixtures_total": 0,
        "fixtures_finished": 0,
        "teams_total": 0,
        "players_pages_fetched": 0,
        "detail_candidates": 0,
        "detail_writes": 0,
        "detail_failures": 0,
        "api_calls": 0,
        "api_attempts": 0,
        "api_failures": 0,
        "endpoint_failures": 0,
        "raw_files": 0,
        "skipped_idempotent": 0,
    }


def _mock_client(total_attempts_delta: int = 1) -> MagicMock:
    """Return a mock ApiFootballClient whose total_attempts increments by *delta* per call."""
    client = MagicMock()
    client.total_attempts = 0

    def _simulated_get(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        client.total_attempts += total_attempts_delta
        return dict(DUMMY_PAYLOAD)

    client.get.side_effect = _simulated_get
    return client


def _mock_writer(marker_exists: bool = False) -> MagicMock:
    writer = MagicMock()
    writer.marker_exists.return_value = marker_exists
    return writer


# ===========================================================================
# Issue 1: Idempotency check BEFORE API fetch
# ===========================================================================


class TestIdempotencyBeforeFetch:
    """When the marker already exists the API must NOT be called."""

    def test_safe_fetch_skips_api_on_existing_marker(self) -> None:
        client = _mock_client()
        writer = _mock_writer(marker_exists=True)
        summary = _fresh_summary()

        _safe_fetch_and_upload(
            client=client,
            writer=writer,
            summary=summary,
            part_counter=count(1),
            config=DUMMY_CONFIG,
            run_date=RUN_DATE,
            run_id=RUN_ID,
            endpoint="/standings",
            entity_key="league_snapshot",
            params={"league": 307, "season": 2025},
        )

        client.get.assert_not_called()
        assert summary["skipped_idempotent"] == 1
        assert summary["api_calls"] == 0
        writer.put_raw.assert_not_called()
        writer.put_marker.assert_not_called()

    def test_safe_fetch_proceeds_on_missing_marker(self) -> None:
        client = _mock_client()
        writer = _mock_writer(marker_exists=False)
        summary = _fresh_summary()

        _safe_fetch_and_upload(
            client=client,
            writer=writer,
            summary=summary,
            part_counter=count(1),
            config=DUMMY_CONFIG,
            run_date=RUN_DATE,
            run_id=RUN_ID,
            endpoint="/standings",
            entity_key="league_snapshot",
            params={"league": 307, "season": 2025},
        )

        client.get.assert_called_once()
        assert summary["api_calls"] == 1
        assert summary["skipped_idempotent"] == 0
        writer.put_raw.assert_called_once()
        writer.put_marker.assert_called_once()

    def test_safe_fetch_force_refresh_ignores_existing_marker(self) -> None:
        client = _mock_client()
        writer = _mock_writer(marker_exists=True)
        summary = _fresh_summary()

        _safe_fetch_and_upload(
            client=client,
            writer=writer,
            summary=summary,
            part_counter=count(1),
            config=DUMMY_CONFIG,
            run_date=RUN_DATE,
            run_id=RUN_ID,
            endpoint="/standings",
            entity_key="league_snapshot",
            params={"league": 307, "season": 2025},
            force_refresh=True,
        )

        client.get.assert_called_once()
        assert summary["api_calls"] == 1
        assert summary["skipped_idempotent"] == 0
        writer.put_raw.assert_called_once()
        writer.put_marker.assert_called_once()

    def test_paginated_players_skips_api_on_existing_marker(self) -> None:
        client = _mock_client()
        writer = _mock_writer(marker_exists=True)
        summary = _fresh_summary()

        _ingest_paginated_league_players(
            client=client,
            writer=writer,
            summary=summary,
            part_counter=count(1),
            config=DUMMY_CONFIG,
            run_date=RUN_DATE,
            run_id=RUN_ID,
        )

        client.get.assert_not_called()
        # 3 pages max × 1 marker check each = 3 skips
        assert summary["skipped_idempotent"] == DUMMY_CONFIG.players_max_pages
        assert summary["api_calls"] == 0

    def test_deep_details_skips_api_on_existing_marker(self) -> None:
        client = _mock_client()
        writer = _mock_writer(marker_exists=True)
        summary = _fresh_summary()
        fixture_ids = [101, 102]

        _ingest_team_deep_fixture_details(
            client=client,
            writer=writer,
            summary=summary,
            part_counter=count(1),
            config=DUMMY_CONFIG,
            run_date=RUN_DATE,
            run_id=RUN_ID,
            fixture_ids=fixture_ids,
        )

        client.get.assert_not_called()
        expected_skips = len(fixture_ids) * len(DETAIL_ENDPOINTS)
        assert summary["skipped_idempotent"] == expected_skips
        assert summary["api_calls"] == 0

    def test_deep_details_fetches_on_missing_marker(self) -> None:
        client = _mock_client()
        writer = _mock_writer(marker_exists=False)
        summary = _fresh_summary()
        fixture_ids = [101]

        _ingest_team_deep_fixture_details(
            client=client,
            writer=writer,
            summary=summary,
            part_counter=count(1),
            config=DUMMY_CONFIG,
            run_date=RUN_DATE,
            run_id=RUN_ID,
            fixture_ids=fixture_ids,
        )

        assert client.get.call_count == len(DETAIL_ENDPOINTS)
        assert summary["api_calls"] == len(DETAIL_ENDPOINTS)
        assert summary["detail_writes"] == len(DETAIL_ENDPOINTS)


# ===========================================================================
# Issue 2: api_attempts tracks raw HTTP attempts (including retries)
# ===========================================================================


class TestApiAttemptsTracking:
    """summary['api_attempts'] must reflect the real HTTP attempt count."""

    def test_single_attempt_per_call(self) -> None:
        client = _mock_client(total_attempts_delta=1)
        summary = _fresh_summary()

        _call_api(client, summary, "/fixtures", {"league": 307})

        assert summary["api_calls"] == 1
        assert summary["api_attempts"] == 1

    def test_multiple_retries_counted(self) -> None:
        """Simulate a call that needed 3 HTTP attempts before succeeding."""
        client = _mock_client(total_attempts_delta=3)
        summary = _fresh_summary()

        _call_api(client, summary, "/fixtures", {"league": 307})

        assert summary["api_calls"] == 1
        assert summary["api_attempts"] == 3

    def test_attempts_tracked_on_failure(self) -> None:
        """Even if the call ultimately fails, attempts must be recorded."""
        client = MagicMock()
        client.total_attempts = 0

        def _failing_get(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
            client.total_attempts += 5  # 5 retries before giving up
            raise RuntimeError("API exhausted retries")

        client.get.side_effect = _failing_get
        summary = _fresh_summary()

        with pytest.raises(RuntimeError, match="API exhausted retries"):
            _call_api(client, summary, "/fixtures", {"league": 307})

        assert summary["api_calls"] == 1
        assert summary["api_attempts"] == 5
        assert summary["api_failures"] == 1


# ===========================================================================
# Issue 3: detail_calls renamed to detail_writes
# ===========================================================================


class TestDetailWritesRename:
    """The summary must contain 'detail_writes', not 'detail_calls'."""

    def test_summary_uses_detail_writes_key(self) -> None:
        summary = _fresh_summary()
        assert "detail_writes" in summary
        assert "detail_calls" not in summary

    def test_detail_writes_incremented_on_write(self) -> None:
        client = _mock_client()
        writer = _mock_writer(marker_exists=False)
        summary = _fresh_summary()
        fixture_ids = [101]

        _ingest_team_deep_fixture_details(
            client=client,
            writer=writer,
            summary=summary,
            part_counter=count(1),
            config=DUMMY_CONFIG,
            run_date=RUN_DATE,
            run_id=RUN_ID,
            fixture_ids=fixture_ids,
        )

        assert summary["detail_writes"] == len(DETAIL_ENDPOINTS)


# ===========================================================================
# LocalFileWriter tests
# ===========================================================================


class TestLocalFileWriter:
    def test_put_marker_and_marker_exists(self, tmp_path: Any) -> None:
        writer = LocalFileWriter(root=tmp_path)
        key = "state/test/marker.json"
        body = {"status": "ok"}

        assert not writer.marker_exists(key)
        writer.put_marker(key, body)
        assert writer.marker_exists(key)

        content = json.loads((tmp_path / key).read_text())
        assert content == body

    def test_put_raw_creates_correct_path(self, tmp_path: Any) -> None:
        writer = LocalFileWriter(root=tmp_path)
        body = {"endpoint": "/fixtures", "payload": []}

        key = writer.put_raw(
            league_id=39,
            season=2024,
            endpoint="/fixtures",
            dt=date(2025, 1, 15),
            run_id="20250115T120000Z",
            part=1,
            body=body,
        )

        assert "league=39" in key
        assert "season=2024" in key
        assert "endpoint=fixtures" in key
        assert "part-00001.json" in key
        assert (tmp_path / key).exists()

        content = json.loads((tmp_path / key).read_text())
        assert content == body

    def test_marker_round_trip_nested_endpoint(self, tmp_path: Any) -> None:
        writer = LocalFileWriter(root=tmp_path)
        idem = idempotency_key_from_parts("/fixtures/statistics", "fixture=101", 2024)
        key = marker_key_without_date(39, 2024, "/fixtures/statistics", idem)

        writer.put_marker(key, {"fixture_id": 101})
        assert writer.marker_exists(key)


# ===========================================================================
# create_writer factory tests
# ===========================================================================


class TestCreateWriter:
    def test_local_default(self) -> None:
        writer = create_writer("local")
        assert isinstance(writer, LocalFileWriter)

    def test_local_custom_root(self, tmp_path: Any) -> None:
        writer = create_writer("local", local_root=str(tmp_path / "custom"))
        assert isinstance(writer, LocalFileWriter)
        assert writer.root == tmp_path / "custom"

    def test_s3_missing_bucket_raises(self) -> None:
        with pytest.raises(ValueError, match="s3_bucket"):
            create_writer("s3", aws_region="us-east-1")

    def test_s3_missing_region_raises(self) -> None:
        with pytest.raises(ValueError, match="aws_region"):
            create_writer("s3", s3_bucket="my-bucket")

    def test_gcs_missing_bucket_raises(self) -> None:
        with pytest.raises(ValueError, match="gcs_bucket"):
            create_writer("gcs")

    def test_unknown_backend_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown storage backend"):
            create_writer("azure")
