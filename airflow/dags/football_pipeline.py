"""Full pipeline DAG: ingest -> flatten -> dbt build.

Uses dynamic task mapping to process each league/season target in parallel.
Config is loaded at task runtime (not DAG parse time) to avoid stale state.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.operators.bash import BashOperator

# Ensure the project root is importable inside the Airflow container.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default DAG parameters (overridable from the Airflow UI "Trigger w/ config")
# ---------------------------------------------------------------------------
DAG_PARAMS = {
    "run_date": Param(default="", type="string", description="YYYY-MM-DD (empty = today)"),
    "config_path": Param(
        default="pipeline_config.json",
        type="string",
        description="Path to pipeline_config.json relative to project root",
    ),
    "baseline_only": Param(default=False, type="boolean"),
    "force_league_snapshot_refresh": Param(default=False, type="boolean"),
    "dev_limit": Param(default=0, type="integer", description="0 = disabled"),
    "enable_gold": Param(default=False, type="boolean"),
    "enable_platinum": Param(default=False, type="boolean"),
}


def _resolve_run_date(raw: str) -> date:
    if raw:
        return date.fromisoformat(raw)
    return date.today()


@dag(
    dag_id="football_pipeline",
    description="End-to-end football data pipeline: ingest -> flatten -> dbt build",
    schedule=None,  # manual trigger only
    start_date=date(2025, 1, 1),
    catchup=False,
    default_args={
        "owner": "data-eng",
        "retries": 0,
        "retry_delay": timedelta(minutes=5),
    },
    params=DAG_PARAMS,
    tags=["football", "pipeline"],
    max_active_runs=1,
)
def football_pipeline():

    @task()
    def load_configs(**context) -> list[dict]:
        """Read pipeline_config.json and return a list of serialisable targets."""
        from src.pipeline.config import load_configs_from_file

        params = context["params"]
        config_path = params.get("config_path") or None
        if config_path:
            config_path = str(PROJECT_ROOT / config_path)

        configs = load_configs_from_file(config_path)
        # Serialise to dicts for XCom (dataclasses aren't JSON-safe by default).
        from dataclasses import asdict

        return [asdict(c) for c in configs]

    @task(retries=2, retry_delay=timedelta(minutes=2), execution_timeout=timedelta(hours=3))
    def ingest_league(config_dict: dict, **context) -> dict:
        """Run ingestion for a single league/season target."""
        from src.pipeline.config import PipelineConfig, resolve_run_date, with_overrides
        from src.pipeline.ingest import run_ingestion

        params = context["params"]
        run_date = _resolve_run_date(params.get("run_date", ""))
        dev_limit = params.get("dev_limit") or None

        config = PipelineConfig(**config_dict)
        if dev_limit:
            config = with_overrides(config, dev_limit=dev_limit)

        logger.info("Ingesting league_id=%s season=%s", config.league_id, config.season)
        start = perf_counter()
        summary = run_ingestion(
            config,
            run_date,
            force_league_snapshot_refresh=params.get("force_league_snapshot_refresh", False),
            baseline_only=params.get("baseline_only", False),
            dev_limit=dev_limit,
        )
        logger.info(
            "Ingestion complete league_id=%s in %.2fs: %s",
            config.league_id,
            perf_counter() - start,
            summary,
        )
        return summary

    @task(execution_timeout=timedelta(hours=1))
    def flatten_league(config_dict: dict, **context) -> dict:
        """Flatten raw JSON to Parquet for a single league/season target."""
        from src.pipeline.config import PipelineConfig, resolve_run_date, with_overrides
        from src.pipeline.flatten import normalize_warehouse_uri, run_flatten
        from src.pipeline.storage import create_writer, generate_run_id

        params = context["params"]
        run_date = _resolve_run_date(params.get("run_date", ""))
        dev_limit = params.get("dev_limit") or None

        config = PipelineConfig(**config_dict)
        if dev_limit:
            config = with_overrides(config, dev_limit=dev_limit)

        writer = create_writer(
            config.storage_backend,
            local_root=config.local_root,
            s3_bucket=config.s3_bucket,
            aws_region=config.aws_region,
            gcs_bucket=config.gcs_bucket,
            gcs_project=config.gcs_project,
        )

        # Resolve warehouse URI (mirrors run_pipeline.py logic)
        uri = config.warehouse_uri_test if dev_limit else config.warehouse_uri
        base_database = os.getenv("SNOWFLAKE_DATABASE", "").strip()
        if dev_limit:
            default_database = os.getenv("SNOWFLAKE_DATABASE_TEST", "").strip()
            if not default_database and base_database:
                default_database = f"{base_database}_TEST"
        else:
            default_database = base_database
        default_schema = os.getenv("SNOWFLAKE_SCHEMA", "").strip() or "STAGING"
        uri = normalize_warehouse_uri(
            uri,
            default_database=default_database or None,
            default_schema=default_schema,
        )

        flatten_run_id = generate_run_id()
        logger.info("Flattening league_id=%s season=%s", config.league_id, config.season)
        start = perf_counter()
        summary = run_flatten(
            writer,
            config.league_id,
            config.season,
            run_date,
            flatten_run_id,
            warehouse_backend=config.warehouse_backend,
            warehouse_uri=uri,
        )
        logger.info(
            "Flatten complete league_id=%s in %.2fs: %s",
            config.league_id,
            perf_counter() - start,
            summary,
        )
        return summary

    # -- Build the dbt command string ------------------------------------------
    # We build the command at render time using Jinja so DAG params flow through.
    dbt_project_dir = str(PROJECT_ROOT / "leagues_data_dbt")
    dbt_profiles_dir = dbt_project_dir

    dbt_cmd = (
        "set -e; "
        "dbt build"
        f" --project-dir {dbt_project_dir}"
        f" --profiles-dir {dbt_profiles_dir}"
        " --fail-fast"
        " --select staging silver gold platinum"
        '{% set dev = params.dev_limit | int %}'
        '{% if dev %} --target test{% endif %}'
        '{% set vars = {} %}'
        '{% if params.enable_gold or params.enable_platinum %}'
        '{% set _ = vars.update({"enable_gold_layer": true}) %}'
        '{% endif %}'
        '{% if params.enable_platinum %}'
        '{% set _ = vars.update({"enable_platinum_layer": true}) %}'
        '{% endif %}'
        '{% if vars %} --vars \'{{ vars | tojson }}\'{% endif %}'
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=dbt_cmd,
        retries=0,
        execution_timeout=timedelta(hours=2),
    )

    # -- Wire the DAG ----------------------------------------------------------
    configs = load_configs()
    ingested = ingest_league.expand(config_dict=configs)
    flattened = flatten_league.expand(config_dict=configs)

    ingested >> flattened >> dbt_build


football_pipeline()
