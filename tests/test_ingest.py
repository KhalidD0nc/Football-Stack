"""Unit tests for the three production-readiness fixes in the ingestion pipeline.

Issue 1 (High):  Idempotency check happens BEFORE API fetch.
Issue 2 (Medium): api_attempts tracks real HTTP attempts including retries.
Issue 3 (Low):  detail_calls renamed to detail_writes.
"""

from __future__ import annotations

from datetime import date
from itertools import count
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.fetch import (
    _build_marker_key,
    _call_api,
    _safe_fetch_and_upload,
)
from src.pipeline.steps import (
    _ingest_paginated_league_players,
    _ingest_team_deep_fixture_details,
    DETAIL_ENDPOINTS,
)
from src.pipeline.config import PipelineConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DUMMY_CONFIG = PipelineConfig(
    api_football_key="test-key",
    api_base_url="https://example.com",
    league_id=307,
    team_id=2932,
    season=2025,
    timezone="UTC",
    players_max_pages=3,
    aws_region="us-east-1",
    s3_bucket="test-bucket",
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


def _mock_s3(marker_exists: bool = False) -> MagicMock:
    s3 = MagicMock()
    s3.marker_exists.return_value = marker_exists
    s3.idempotency_key_from_parts.return_value = "idem-hash"
    s3.marker_key.return_value = "state/marker.json"
    s3.marker_key_without_date.return_value = "state/marker-no-date.json"
    return s3


# ===========================================================================
# Issue 1: Idempotency check BEFORE API fetch
# ===========================================================================


class TestIdempotencyBeforeFetch:
    """When the marker already exists the API must NOT be called."""

    def test_safe_fetch_skips_api_on_existing_marker(self) -> None:
        client = _mock_client()
        s3 = _mock_s3(marker_exists=True)
        summary = _fresh_summary()

        _safe_fetch_and_upload(
            client=client,
            s3=s3,
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
        s3.put_raw.assert_not_called()
        s3.put_marker.assert_not_called()

    def test_safe_fetch_proceeds_on_missing_marker(self) -> None:
        client = _mock_client()
        s3 = _mock_s3(marker_exists=False)
        summary = _fresh_summary()

        _safe_fetch_and_upload(
            client=client,
            s3=s3,
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
        s3.put_raw.assert_called_once()
        s3.put_marker.assert_called_once()

    def test_safe_fetch_force_refresh_ignores_existing_marker(self) -> None:
        client = _mock_client()
        s3 = _mock_s3(marker_exists=True)
        summary = _fresh_summary()

        _safe_fetch_and_upload(
            client=client,
            s3=s3,
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
        s3.put_raw.assert_called_once()
        s3.put_marker.assert_called_once()

    def test_paginated_players_skips_api_on_existing_marker(self) -> None:
        client = _mock_client()
        s3 = _mock_s3(marker_exists=True)
        summary = _fresh_summary()

        _ingest_paginated_league_players(
            client=client,
            s3=s3,
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
        s3 = _mock_s3(marker_exists=True)
        summary = _fresh_summary()
        fixture_ids = [101, 102]

        _ingest_team_deep_fixture_details(
            client=client,
            s3=s3,
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
        s3 = _mock_s3(marker_exists=False)
        summary = _fresh_summary()
        fixture_ids = [101]

        _ingest_team_deep_fixture_details(
            client=client,
            s3=s3,
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
        s3 = _mock_s3(marker_exists=False)
        summary = _fresh_summary()
        fixture_ids = [101]

        _ingest_team_deep_fixture_details(
            client=client,
            s3=s3,
            summary=summary,
            part_counter=count(1),
            config=DUMMY_CONFIG,
            run_date=RUN_DATE,
            run_id=RUN_ID,
            fixture_ids=fixture_ids,
        )

        assert summary["detail_writes"] == len(DETAIL_ENDPOINTS)
