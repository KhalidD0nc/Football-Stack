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


def _is_finished_fixture_for_date(fixture_row: dict[str, Any], dt: date) -> bool:
    fixture = fixture_row.get("fixture", {})
    status = fixture.get("status", {})
    fixture_date = str(fixture.get("date", ""))[:10]
    return status.get("short") in FINISHED_STATUSES and fixture_date == dt.isoformat()


def _is_fixture_for_team(fixture_row: dict[str, Any], team_id: int) -> bool:
    teams = fixture_row.get("teams", {})
    home_id = teams.get("home", {}).get("id")
    away_id = teams.get("away", {}).get("id")
    return home_id == team_id or away_id == team_id


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


def select_finished_fixture_ids_for_team(
    fixtures_payload: dict[str, Any], run_date: date, team_id: int
) -> list[int]:
    fixtures = _fixtures_rows(fixtures_payload)
    finished = [
        row
        for row in fixtures
        if _is_finished_fixture_for_date(row, run_date) and _is_fixture_for_team(row, team_id)
    ]
    fixture_ids = [_fixture_id(row) for row in finished]
    return sorted(set(fixture_ids))


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _call_api(
    client: ApiFootballClient,
    summary: dict[str, int],
    endpoint: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    summary["api_calls"] += 1
    try:
        return client.get(endpoint, params)
    except Exception:
        summary["api_failures"] += 1
        raise


def _upload_payload(
    s3: S3Writer,
    summary: dict[str, int],
    config: PipelineConfig,
    run_date: date,
    run_id: str,
    endpoint: str,
    entity_key: str,
    part: int,
    params: dict[str, Any],
    payload: dict[str, Any],
) -> bool:
    idem = s3.idempotency_key_from_parts(endpoint, entity_key, config.season, run_date.isoformat())
    marker_key = s3.marker_key(config.league_id, config.season, endpoint, run_date, idem)

    if s3.marker_exists(marker_key):
        summary["skipped_idempotent"] += 1
        return False

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
    return True


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
) -> None:
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
            entity_key=f"league_page={page}",
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
            params = {"fixture": fixture_id}
            try:
                payload = _call_api(client, summary, endpoint, params)
            except Exception:
                summary["detail_failures"] += 1
                summary["endpoint_failures"] += 1
                logger.exception("Failed detail fetch fixture_id=%s endpoint=%s", fixture_id, endpoint)
                continue

            wrote = _upload_payload(
                s3=s3,
                summary=summary,
                config=config,
                run_date=run_date,
                run_id=run_id,
                endpoint=endpoint,
                entity_key=f"fixture={fixture_id}",
                part=next(part_counter),
                params=params,
                payload=payload,
            )
            if wrote:
                summary["detail_calls"] += 1


def run_ingestion(config: PipelineConfig, run_date: date) -> dict[str, int]:
    client = ApiFootballClient(config.api_base_url, config.api_football_key)
    s3 = S3Writer(config.s3_bucket, config.aws_region)
    run_id = generate_run_id()
    part_counter = count(1)

    summary = {
        "fixtures_total": 0,
        "fixtures_finished": 0,
        "teams_total": 0,
        "players_pages_fetched": 0,
        "detail_candidates": 0,
        "detail_calls": 0,
        "detail_failures": 0,
        "api_calls": 0,
        "api_failures": 0,
        "endpoint_failures": 0,
        "raw_files": 0,
        "skipped_idempotent": 0,
    }

    # 1) League fixtures baseline snapshot (required)
    fixtures_params = {"league": config.league_id, "season": config.season, "timezone": config.timezone}
    fixtures_payload = _call_api(client, summary, "/fixtures", fixtures_params)
    _upload_payload(
        s3=s3,
        summary=summary,
        config=config,
        run_date=run_date,
        run_id=run_id,
        endpoint="/fixtures",
        entity_key="league_snapshot",
        part=next(part_counter),
        params=fixtures_params,
        payload=fixtures_payload,
    )
    fixture_rows = _fixtures_rows(fixtures_payload)
    summary["fixtures_total"] = len(fixture_rows)

    team_finished_fixture_ids = select_finished_fixture_ids_for_team(
        fixtures_payload, run_date, config.team_id
    )
    summary["fixtures_finished"] = len(team_finished_fixture_ids)

    # 2) Teams baseline snapshot (required)
    teams_params = {"league": config.league_id, "season": config.season}
    teams_payload = _call_api(client, summary, "/teams", teams_params)
    _upload_payload(
        s3=s3,
        summary=summary,
        config=config,
        run_date=run_date,
        run_id=run_id,
        endpoint="/teams",
        entity_key="league_snapshot",
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
        )

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

    # 6) Deep details for configured club on run date (Al Hilal by default)
    _ingest_team_deep_fixture_details(
        client=client,
        s3=s3,
        summary=summary,
        part_counter=part_counter,
        config=config,
        run_date=run_date,
        run_id=run_id,
        fixture_ids=team_finished_fixture_ids,
    )

    logger.info("Ingestion summary: %s", summary)
    return summary
