"""Lightweight daily ingestion DAG — mirrors scripts/run_daily.py.

Runs a single-league daily ingest using environment-variable config
(LEAGUE_ID / SEASON). No flatten or dbt steps.
"""

from __future__ import annotations

import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter

from airflow.decorators import dag, task
from airflow.models.param import Param

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


@dag(
    dag_id="football_daily_ingest",
    description="Daily thin-slice ingestion for a single league",
    schedule="@daily",
    start_date=date(2025, 1, 1),
    catchup=False,
    default_args={
        "owner": "data-eng",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    params={
        "run_date": Param(default="", type="string", description="YYYY-MM-DD (empty = today)"),
        "baseline_only": Param(default=False, type="boolean"),
        "force_league_snapshot_refresh": Param(default=False, type="boolean"),
    },
    tags=["football", "daily"],
    max_active_runs=1,
)
def football_daily_ingest():

    @task(retries=2, retry_delay=timedelta(minutes=2), execution_timeout=timedelta(hours=3))
    def ingest(**context) -> dict:
        from src.pipeline.config import load_config
        from src.pipeline.ingest import run_ingestion

        params = context["params"]
        raw_date = params.get("run_date", "")
        run_date = date.fromisoformat(raw_date) if raw_date else date.today()

        config = load_config()
        logger.info(
            "Daily ingestion start league_id=%s season=%s run_date=%s",
            config.league_id,
            config.season,
            run_date.isoformat(),
        )
        start = perf_counter()
        summary = run_ingestion(
            config,
            run_date,
            force_league_snapshot_refresh=params.get("force_league_snapshot_refresh", False),
            baseline_only=params.get("baseline_only", False),
        )
        logger.info(
            "Daily ingestion complete league_id=%s in %.2fs: %s",
            config.league_id,
            perf_counter() - start,
            summary,
        )
        return summary

    ingest()


football_daily_ingest()
