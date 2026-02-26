from __future__ import annotations

from datetime import UTC
from datetime import datetime
import logging
from datetime import date
from itertools import count
from typing import Any

from .api_client import ApiFootballClient
from .config import PipelineConfig
from .storage import S3Writer, generate_run_id

logger = logging.getLogger(__name__)


DETAIL_ENDPOINTS = [
    "/fixtures/statistics",
    "/fixtures/events",
    "/fixtures/lineups",
    "/fixtures/players",
    "/predictions",
]

FINISHED_STATUSES = {"FT", "AET", "PEN"}


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


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _build_marker_key(
    s3: S3Writer,
    config: PipelineConfig,
    run_date: date,
    endpoint: str,
    entity_key: str,
    include_run_date: bool = True,
) -> tuple[str, str]:
    """Return (idempotency_hash, full_marker_key) for an endpoint+entity."""
    if include_run_date:
        idem = s3.idempotency_key_from_parts(endpoint, entity_key, config.season, run_date.isoformat())
        marker = s3.marker_key(config.league_id, config.season, endpoint, run_date, idem)
    else:
        idem = s3.idempotency_key_from_parts(endpoint, entity_key, config.season)
        marker = s3.marker_key_without_date(config.league_id, config.season, endpoint, idem)
    return idem, marker


def _call_api(
    client: ApiFootballClient,
    summary: dict[str, int],
    endpoint: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    summary["api_calls"] += 1
    attempts_before = client.total_attempts
    try:
        result = client.get(endpoint, params)
    except Exception:
        summary["api_failures"] += 1
        raise
    finally:
        summary["api_attempts"] += client.total_attempts - attempts_before
    return result


def _upload_payload(
    s3: S3Writer,
    summary: dict[str, int],
    config: PipelineConfig,
    run_date: date,
    run_id: str,
    endpoint: str,
    entity_key: str,
    marker_key: str,
    part: int,
    params: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    """Persist *payload* to S3 and write its idempotency marker.

    Callers MUST check ``s3.marker_exists`` **before** fetching data
    and skip the entire fetch+upload if the marker already exists.
    This function always writes — it does not check markers itself.
    """
    raw_body = {
        "endpoint": endpoint,
        "entity_key": entity_key,
        "params": params,
        "fetched_at": _utc_now_iso(),
        "payload": payload,
    }
    s3.put_raw(
        league_id=config.league_id,
        season=config.season,
        endpoint=endpoint,
        dt=run_date,
        run_id=run_id,
        part=part,
        body=raw_body,
    )
    summary["raw_files"] += 1

    s3.put_marker(
        marker_key,
        {
            "entity_key": entity_key,
            "endpoint": endpoint,
            "run_date": run_date.isoformat(),
            "run_id": run_id,
            "params": params,
        },
    )


def _safe_fetch_and_upload(
    client: ApiFootballClient,
    s3: S3Writer,
    summary: dict[str, int],
    part_counter: Any,
    config: PipelineConfig,
    run_date: date,
    run_id: str,
    endpoint: str,
    entity_key: str,
    params: dict[str, Any],
    force_refresh: bool = False,
) -> None:
    _idem, marker = _build_marker_key(s3, config, run_date, endpoint, entity_key)
    if s3.marker_exists(marker) and not force_refresh:
        summary["skipped_idempotent"] += 1
        return

    try:
        payload = _call_api(client, summary, endpoint, params)
    except Exception:
        summary["endpoint_failures"] += 1
        logger.exception("Failed fetch endpoint=%s entity_key=%s params=%s", endpoint, entity_key, params)
        return

    _upload_payload(
        s3=s3,
        summary=summary,
        config=config,
        run_date=run_date,
        run_id=run_id,
        endpoint=endpoint,
        entity_key=entity_key,
        marker_key=marker,
        part=next(part_counter),
        params=params,
        payload=payload,
    )


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


def _ingest_paginated_league_players(
    client: ApiFootballClient,
    s3: S3Writer,
    summary: dict[str, int],
    part_counter: Any,
    config: PipelineConfig,
    run_date: date,
    run_id: str,
) -> None:
    for page in range(1, config.players_max_pages + 1):
        entity_key = f"league_page={page}"
        _idem, marker = _build_marker_key(s3, config, run_date, "/players", entity_key)
        if s3.marker_exists(marker):
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
            s3=s3,
            summary=summary,
            config=config,
            run_date=run_date,
            run_id=run_id,
            endpoint="/players",
            entity_key=entity_key,
            marker_key=marker,
            part=next(part_counter),
            params=params,
            payload=payload,
        )

        paging = payload.get("paging", {})
        current = int(paging.get("current", page) or page)
        total = int(paging.get("total", page) or page)
        if current >= total:
            break


def _ingest_team_deep_fixture_details(
    client: ApiFootballClient,
    s3: S3Writer,
    summary: dict[str, int],
    part_counter: Any,
    config: PipelineConfig,
    run_date: date,
    run_id: str,
    fixture_ids: list[int],
) -> None:
    summary["detail_candidates"] = len(fixture_ids) * len(DETAIL_ENDPOINTS)

    for fixture_id in fixture_ids:
        for endpoint in DETAIL_ENDPOINTS:
            entity_key = f"fixture={fixture_id}"
            _idem, marker = _build_marker_key(
                s3,
                config,
                run_date,
                endpoint,
                entity_key,
                include_run_date=False,
            )
            if s3.marker_exists(marker):
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
                s3=s3,
                summary=summary,
                config=config,
                run_date=run_date,
                run_id=run_id,
                endpoint=endpoint,
                entity_key=entity_key,
                marker_key=marker,
                part=next(part_counter),
                params=params,
                payload=payload,
            )
            summary["detail_writes"] += 1


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

    # 1) League fixtures baseline snapshot (required)
    _idem, fixtures_marker = _build_marker_key(s3, config, run_date, "/fixtures", "league_snapshot")
    fixtures_params = {"league": config.league_id, "season": config.season, "timezone": config.timezone}
    fixtures_marker_exists = s3.marker_exists(fixtures_marker)
    if fixtures_marker_exists and not force_league_snapshot_refresh:
        summary["skipped_idempotent"] += 1
        # Still need fixture ids for downstream steps — re-fetch is unavoidable here
        fixtures_payload = _call_api(client, summary, "/fixtures", fixtures_params)
    else:
        fixtures_payload = _call_api(client, summary, "/fixtures", fixtures_params)
        _upload_payload(
            s3=s3,
            summary=summary,
            config=config,
            run_date=run_date,
            run_id=run_id,
            endpoint="/fixtures",
            entity_key="league_snapshot",
            marker_key=fixtures_marker,
            part=next(part_counter),
            params=fixtures_params,
            payload=fixtures_payload,
        )
    fixture_rows = _fixtures_rows(fixtures_payload)
    summary["fixtures_total"] = len(fixture_rows)

    league_finished_fixture_ids = select_finished_fixture_ids(fixtures_payload)
    summary["fixtures_finished"] = len(league_finished_fixture_ids)

    # 2) Teams baseline snapshot (required)
    _idem, teams_marker = _build_marker_key(s3, config, run_date, "/teams", "league_snapshot")
    teams_params = {"league": config.league_id, "season": config.season}
    teams_marker_exists = s3.marker_exists(teams_marker)
    if teams_marker_exists and not force_league_snapshot_refresh:
        summary["skipped_idempotent"] += 1
        # Still need team ids for downstream steps — re-fetch is unavoidable here
        teams_payload = _call_api(client, summary, "/teams", teams_params)
    else:
        teams_payload = _call_api(client, summary, "/teams", teams_params)
        _upload_payload(
            s3=s3,
            summary=summary,
            config=config,
            run_date=run_date,
            run_id=run_id,
            endpoint="/teams",
            entity_key="league_snapshot",
            marker_key=teams_marker,
            part=next(part_counter),
            params=teams_params,
            payload=teams_payload,
        )
    team_ids = _team_ids_from_teams_payload(teams_payload)
    summary["teams_total"] = len(team_ids)

    # 3) League-level baseline endpoints
    league_baseline_calls = [
        ("/standings", {"league": config.league_id, "season": config.season}, "league_snapshot"),
        ("/fixtures/rounds", {"league": config.league_id, "season": config.season}, "league_snapshot"),
        ("/players/topscorers", {"league": config.league_id, "season": config.season}, "league_snapshot"),
        ("/players/topassists", {"league": config.league_id, "season": config.season}, "league_snapshot"),
        ("/players/topyellowcards", {"league": config.league_id, "season": config.season}, "league_snapshot"),
        ("/players/topredcards", {"league": config.league_id, "season": config.season}, "league_snapshot"),
    ]
    for endpoint, params, entity_key in league_baseline_calls:
        _safe_fetch_and_upload(
            client=client,
            s3=s3,
            summary=summary,
            part_counter=part_counter,
            config=config,
            run_date=run_date,
            run_id=run_id,
            endpoint=endpoint,
            entity_key=entity_key,
            params=params,
            force_refresh=force_league_snapshot_refresh,
        )

    if baseline_only:
        logger.info("Baseline-only ingestion enabled; skipping players pages, team-level endpoints, and deep fixture details.")
        logger.info("Ingestion summary: %s", summary)
        return summary

    # 4) Paginated league players snapshot
    _ingest_paginated_league_players(
        client=client,
        s3=s3,
        summary=summary,
        part_counter=part_counter,
        config=config,
        run_date=run_date,
        run_id=run_id,
    )

    # 5) Team-level baseline endpoints for all SPL clubs
    for team_id in team_ids:
        team_entity = f"team={team_id}"
        team_calls = [
            ("/teams/statistics", {"league": config.league_id, "season": config.season, "team": team_id}),
            ("/injuries", {"team": team_id, "season": config.season}),
            ("/transfers", {"team": team_id}),
            ("/players/squads", {"team": team_id}),
        ]
        for endpoint, params in team_calls:
            _safe_fetch_and_upload(
                client=client,
                s3=s3,
                summary=summary,
                part_counter=part_counter,
                config=config,
                run_date=run_date,
                run_id=run_id,
                endpoint=endpoint,
                entity_key=team_entity,
                params=params,
            )

    # 6) Deep details for all finished league fixtures in season
    _ingest_team_deep_fixture_details(
        client=client,
        s3=s3,
        summary=summary,
        part_counter=part_counter,
        config=config,
        run_date=run_date,
        run_id=run_id,
        fixture_ids=league_finished_fixture_ids,
    )

    logger.info("Ingestion summary: %s", summary)
    return summary
