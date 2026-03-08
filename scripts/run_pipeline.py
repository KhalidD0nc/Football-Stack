from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
from datetime import date
from pathlib import Path
from time import perf_counter

from src.pipeline.config import load_configs_from_file, resolve_run_date, with_overrides
from src.pipeline.ingest import run_ingestion


logger = logging.getLogger(__name__)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_raw_sync_macro_args(
    run_date: date | None,
    raw_database: str | None,
    raw_schema: str,
    stage_name: str,
) -> dict[str, str]:
    macro_args: dict[str, str] = {
        "raw_schema": raw_schema,
        "stage_name": stage_name,
    }
    if run_date is not None:
        macro_args["run_date"] = run_date.isoformat()
    if raw_database:
        macro_args["raw_database"] = raw_database
    return macro_args


def build_dbt_raw_sync_cmd(
    project_dir: Path,
    profiles_dir: Path,
    macro_args: dict[str, str],
) -> list[str]:
    return [
        "dbt",
        "run-operation",
        "sync_raw_from_s3",
        "--project-dir",
        str(project_dir),
        "--profiles-dir",
        str(profiles_dir),
        "--args",
        json.dumps(macro_args),
    ]


def build_dbt_build_cmd(
    project_dir: Path,
    profiles_dir: Path,
    selectors: list[str],
) -> list[str]:
    return [
        "dbt",
        "build",
        "--project-dir",
        str(project_dir),
        "--profiles-dir",
        str(profiles_dir),
        "--fail-fast",
        "--select",
        *selectors,
    ]


def _run_command(command: list[str], dry_run: bool, step_name: str) -> None:
    start = perf_counter()
    logger.info("Step start: %s", step_name)
    logger.info("Running command: %s", " ".join(command))
    if dry_run:
        logger.info("Step complete (dry-run): %s in %.2fs", step_name, perf_counter() - start)
        return
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        logger.exception("Step failed: %s after %.2fs", step_name, perf_counter() - start)
        raise
    logger.info("Step complete: %s in %.2fs", step_name, perf_counter() - start)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run end-to-end data pipeline (ingestion -> RAW -> dbt)."
    )
    parser.add_argument("--date", dest="run_date", help="Run date in YYYY-MM-DD format.", default=None)
    parser.add_argument(
        "--config",
        dest="config_path",
        help="Path to pipeline_config.json containing targets.",
        default=None,
    )
    parser.add_argument(
        "--league-id",
        dest="league_id",
        type=_positive_int,
        default=None,
        help="Override env LEAGUE_ID for this run (single-league execution).",
    )
    parser.add_argument(
        "--league-ids",
        dest="league_ids",
        type=_positive_int,
        nargs="+",
        default=None,
        help="Run ingestion for multiple leagues sequentially, then dbt once (e.g. --league-ids 307 39 140 135).",
    )
    parser.add_argument("--project-dir", default="leagues_data_dbt", help="dbt project directory.")
    parser.add_argument("--profiles-dir", default="leagues_data_dbt", help="dbt profiles directory.")
    parser.add_argument(
        "--raw-database",
        default=None,
        help="Snowflake database for RAW tables (defaults to dbt target database).",
    )
    parser.add_argument("--raw-schema", default="RAW", help="Snowflake schema for RAW tables.")
    parser.add_argument("--stage-name", default="LEAGUES_STAGE", help="Snowflake stage name for S3 raw files.")
    parser.add_argument(
        "--select",
        nargs="+",
        default=["staging", "silver", "gold"],
        help="dbt selectors to build after RAW sync.",
    )
    parser.add_argument("--skip-ingestion", action="store_true", help="Skip API -> S3 ingestion step.")
    parser.add_argument(
        "--force-league-snapshot-refresh",
        action="store_true",
        help="Force refresh of league snapshots (fixtures, teams, standings, rounds, top lists) even if same-date markers exist.",
    )
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Ingestion mode: only refresh league-level baseline endpoints (minimal API calls).",
    )
    parser.add_argument("--skip-raw-sync", action="store_true", help="Skip Snowflake RAW COPY INTO step.")
    parser.add_argument("--skip-dbt-build", action="store_true", help="Skip dbt build step.")
    parser.add_argument(
        "--raw-sync-all-dates",
        action="store_true",
        help="Load RAW files without filtering on run date.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing dbt commands.")
    return parser.parse_args()


def main() -> None:
    pipeline_start = perf_counter()
    args = parse_args()
    run_date = resolve_run_date(args.run_date)
    project_dir = Path(args.project_dir).resolve()
    profiles_dir = Path(args.profiles_dir).resolve()
    logger.info(
        "Pipeline start run_date=%s league_id_override=%s skip_ingestion=%s skip_raw_sync=%s skip_dbt_build=%s dry_run=%s",
        run_date.isoformat(),
        args.league_id,
        args.skip_ingestion,
        args.skip_raw_sync,
        args.skip_dbt_build,
        args.dry_run,
    )

    if not args.skip_ingestion:
        base_configs = load_configs_from_file(args.config_path)
        configs_to_run = []
        league_ids_override = args.league_ids or ([args.league_id] if args.league_id else [])
        if league_ids_override:
            for bc in base_configs:
                for target_lid in league_ids_override:
                    configs_to_run.append(with_overrides(bc, league_id=target_lid))
        else:
            configs_to_run = base_configs

        for config in configs_to_run:
            step_start = perf_counter()
            logger.info(
                "Step start: ingestion (league_id=%s season=%s baseline_only=%s force_snapshot_refresh=%s)",
                config.league_id,
                config.season,
                args.baseline_only,
                args.force_league_snapshot_refresh,
            )
            summary = run_ingestion(
                config,
                run_date,
                force_league_snapshot_refresh=args.force_league_snapshot_refresh,
                baseline_only=args.baseline_only,
            )
            logger.info("Step complete: ingestion league_id=%s in %.2fs", config.league_id, perf_counter() - step_start)
            logger.info("Ingestion complete league_id=%s for %s: %s", config.league_id, run_date.isoformat(), summary)
    else:
        logger.info("Skipping ingestion step")

    should_run_dbt = not (args.skip_raw_sync and args.skip_dbt_build)
    if should_run_dbt and not args.dry_run and shutil.which("dbt") is None:
        raise RuntimeError("dbt CLI is not installed. Install dbt before running RAW sync/build steps.")

    if not args.skip_raw_sync:
        raw_sync_date = None if args.raw_sync_all_dates else run_date
        macro_args = build_raw_sync_macro_args(
            run_date=raw_sync_date,
            raw_database=args.raw_database,
            raw_schema=args.raw_schema,
            stage_name=args.stage_name,
        )
        raw_sync_cmd = build_dbt_raw_sync_cmd(
            project_dir=project_dir,
            profiles_dir=profiles_dir,
            macro_args=macro_args,
        )
        _run_command(raw_sync_cmd, dry_run=args.dry_run, step_name="raw_sync")
    else:
        logger.info("Skipping RAW sync step")

    if not args.skip_dbt_build:
        dbt_build_cmd = build_dbt_build_cmd(
            project_dir=project_dir,
            profiles_dir=profiles_dir,
            selectors=args.select,
        )
        _run_command(dbt_build_cmd, dry_run=args.dry_run, step_name="dbt_build")
    else:
        logger.info("Skipping dbt build step")

    logger.info(
        "Pipeline run finished for %s in %.2fs",
        run_date.isoformat(),
        perf_counter() - pipeline_start,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    main()
