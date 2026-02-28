from __future__ import annotations

import logging
from datetime import date
from itertools import count

from .api_client import ApiFootballClient
from .config import PipelineConfig
from .steps import (
    _ingest_fixtures_baseline,
    _ingest_teams_baseline,
    _ingest_league_endpoints,
    _ingest_paginated_league_players,
    _ingest_team_endpoints,
    _ingest_team_deep_fixture_details,
)
from .storage import S3Writer, generate_run_id

logger = logging.getLogger(__name__)


def run_ingestion(
    config: PipelineConfig,
    run_date: date,
    force_league_snapshot_refresh: bool = False,
    baseline_only: bool = False,
) -> dict[str, int]:
    client = ApiFootballClient(config.api_base_url, config.api_football_key)
    s3 = S3Writer(config.s3_bucket, config.aws_region)
    run_id = generate_run_id()
    part_counter = count(1)

    summary: dict[str, int] = {
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

    # Step 1: Fetch all fixtures — IDs needed as input to step 6
    _fixtures_payload, finished_fixture_ids = _ingest_fixtures_baseline(
        client=client, s3=s3, summary=summary, part_counter=part_counter,
        config=config, run_date=run_date, run_id=run_id,
        force_refresh=force_league_snapshot_refresh,
    )

    # Step 2: Fetch all teams — IDs needed as input to step 5
    team_ids = _ingest_teams_baseline(
        client=client, s3=s3, summary=summary, part_counter=part_counter,
        config=config, run_date=run_date, run_id=run_id,
        force_refresh=force_league_snapshot_refresh,
    )

    # Step 3: League-level snapshots (standings, rounds, leaderboards)
    _ingest_league_endpoints(
        client=client, s3=s3, summary=summary, part_counter=part_counter,
        config=config, run_date=run_date, run_id=run_id,
        force_refresh=force_league_snapshot_refresh,
    )

    if baseline_only:
        logger.info("Baseline-only mode; skipping players, team endpoints, and fixture details.")
        logger.info("Ingestion summary: %s", summary)
        return summary

    # Step 4: All player season stats (paginated)
    _ingest_paginated_league_players(
        client=client, s3=s3, summary=summary, part_counter=part_counter,
        config=config, run_date=run_date, run_id=run_id,
    )

    # Step 5: Per-team endpoints (stats, injuries, transfers, squads)
    _ingest_team_endpoints(
        client=client, s3=s3, summary=summary, part_counter=part_counter,
        config=config, run_date=run_date, run_id=run_id,
        team_ids=team_ids,
    )

    # Step 6: Per-fixture details for all finished fixtures
    _ingest_team_deep_fixture_details(
        client=client, s3=s3, summary=summary, part_counter=part_counter,
        config=config, run_date=run_date, run_id=run_id,
        fixture_ids=finished_fixture_ids,
    )

    logger.info("Ingestion summary: %s", summary)
    return summary
