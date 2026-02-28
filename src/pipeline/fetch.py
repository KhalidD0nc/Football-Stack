from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

from .api_client import ApiFootballClient
from .config import PipelineConfig
from .storage import S3Writer

logger = logging.getLogger(__name__)


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
