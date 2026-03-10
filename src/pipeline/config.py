from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class PipelineConfig:
    api_football_key: str
    api_base_url: str
    league_id: int
    season: int
    timezone: str
    players_max_pages: int
    team_id: int = 0
    storage_backend: str = "local"
    local_root: str = "data_lake"
    aws_region: str | None = None
    s3_bucket: str | None = None
    gcs_bucket: str | None = None
    gcs_project: str | None = None


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _infer_backend() -> str:
    """Infer storage backend from env vars for backward compat."""
    explicit = os.getenv("STORAGE_BACKEND", "").strip().lower()
    if explicit:
        return explicit
    if os.getenv("GCS_BUCKET", os.getenv("GCP_BUCKET_TEST", "")).strip():
        return "gcs"
    if os.getenv("S3_BUCKET", os.getenv("S3_BUCKET_TEST", "")).strip():
        return "s3"
    return "local"


def load_config() -> PipelineConfig:
    load_dotenv()

    backend = _infer_backend()

    return PipelineConfig(
        api_football_key=_require("API_FOOTBALL_KEY"),
        api_base_url=os.getenv("API_BASE_URL", "https://v3.football.api-sports.io").rstrip("/"),
        league_id=int(_require("LEAGUE_ID")),
        team_id=int(os.getenv("TEAM_ID", "0")),
        season=int(_require("SEASON")),
        timezone=os.getenv("TIMEZONE", "Asia/Riyadh"),
        players_max_pages=int(os.getenv("PLAYERS_MAX_PAGES", "200")),
        storage_backend=backend,
        local_root=os.getenv("LOCAL_ROOT", "data_lake"),
        aws_region=os.getenv("AWS_REGION", "us-east-1") if backend == "s3" else os.getenv("AWS_REGION"),
        s3_bucket=os.getenv("S3_BUCKET") if backend == "s3" else os.getenv("S3_BUCKET"),
        gcs_bucket=os.getenv("GCS_BUCKET", os.getenv("GCP_BUCKET_TEST")),
        gcs_project=os.getenv("GCS_PROJECT"),
    )


def load_configs_from_file(config_path: str | Path | None) -> list[PipelineConfig]:
    """Parse JSON configuration file to return multi-league, multi-season configs."""
    if not config_path:
        return [load_config()]

    load_dotenv()
    api_key = _require("API_FOOTBALL_KEY")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    settings = data.get("settings", {})
    targets = data.get("targets", [])

    base_url = settings.get("api_base_url", os.getenv("API_BASE_URL", "https://v3.football.api-sports.io")).rstrip("/")
    timezone = settings.get("timezone", os.getenv("TIMEZONE", "Asia/Riyadh"))
    pages = int(settings.get("players_max_pages", os.getenv("PLAYERS_MAX_PAGES", "200")))

    # Storage config — check settings.storage sub-object first, fall back to top-level
    storage_cfg = settings.get("storage", {})
    backend_raw = storage_cfg.get("backend", os.getenv("STORAGE_BACKEND", "")).strip().lower()

    # Backward compat: top-level s3_bucket / aws_region
    s3_bucket = storage_cfg.get("s3_bucket", settings.get("s3_bucket", os.getenv("S3_BUCKET", ""))).strip() or None
    aws_region = storage_cfg.get("aws_region", settings.get("aws_region", os.getenv("AWS_REGION", ""))).strip() or None
    local_root = storage_cfg.get("local_root", os.getenv("LOCAL_ROOT", "data_lake"))
    gcs_bucket = storage_cfg.get("gcs_bucket", settings.get("gcs_bucket", os.getenv("GCS_BUCKET", os.getenv("GCP_BUCKET_TEST", "")))).strip() or None
    gcs_project = storage_cfg.get("gcs_project", os.getenv("GCS_PROJECT")) or None

    # Infer backend if not explicit
    if backend_raw:
        backend = backend_raw
    elif gcs_bucket:
        backend = "gcs"
    elif s3_bucket:
        backend = "s3"
    else:
        backend = "local"

    if backend == "s3" and not s3_bucket:
        raise ValueError("s3_bucket is required when storage backend is 's3'. Set it in config file or S3_BUCKET env var.")

    configs = []
    for target in targets:
        league_id = int(target["league_id"])
        team_id = int(target.get("team_id", os.getenv("TEAM_ID", "0")))
        for season in target.get("seasons", []):
            configs.append(PipelineConfig(
                api_football_key=api_key,
                api_base_url=base_url,
                league_id=league_id,
                team_id=team_id,
                season=int(season),
                timezone=timezone,
                players_max_pages=pages,
                storage_backend=backend,
                local_root=local_root,
                aws_region=aws_region,
                s3_bucket=s3_bucket,
                gcs_bucket=gcs_bucket,
                gcs_project=gcs_project,
            ))

    if not configs:
         raise ValueError(f"No targets found in config file {config_path}")

    return configs


def resolve_run_date(run_date: str | None = None) -> date:
    if run_date:
        return date.fromisoformat(run_date)
    return date.today()


def with_overrides(config: PipelineConfig, league_id: int | None = None) -> PipelineConfig:
    """Return a runtime-adjusted config without mutating env-derived defaults."""
    if league_id is None:
        return config
    if league_id <= 0:
        raise ValueError("league_id override must be a positive integer")
    return replace(config, league_id=league_id)
