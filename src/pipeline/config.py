from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

from dotenv import load_dotenv


@dataclass(frozen=True)
class PipelineConfig:
    api_football_key: str
    api_base_url: str
    league_id: int
    team_id: int
    season: int
    timezone: str
    players_max_pages: int
    aws_region: str
    s3_bucket: str


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_config() -> PipelineConfig:
    load_dotenv()

    return PipelineConfig(
        api_football_key=_require("API_FOOTBALL_KEY"),
        api_base_url=os.getenv("API_BASE_URL", "https://v3.football.api-sports.io").rstrip("/"),
        league_id=int(os.getenv("LEAGUE_ID", "307")),
        team_id=int(os.getenv("TEAM_ID", "2932")),
        season=int(_require("SEASON")),
        timezone=os.getenv("TIMEZONE", "Asia/Riyadh"),
        players_max_pages=int(os.getenv("PLAYERS_MAX_PAGES", "200")),
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        s3_bucket=_require("S3_BUCKET"),
    )


def resolve_run_date(run_date: str | None = None) -> date:
    if run_date:
        return date.fromisoformat(run_date)
    return date.today()
