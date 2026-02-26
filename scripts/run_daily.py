from __future__ import annotations

import argparse
import logging
from time import perf_counter

from src.pipeline.config import load_config, resolve_run_date, with_overrides
from src.pipeline.ingest import run_ingestion


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run thin-slice daily ingestion")
    parser.add_argument("--date", dest="run_date", help="Run date in YYYY-MM-DD", default=None)
    parser.add_argument(
        "--league-id",
        dest="league_id",
        type=_positive_int,
        default=None,
        help="Override env LEAGUE_ID for this run (single-league execution).",
    )
    parser.add_argument(
        "--force-league-snapshot-refresh",
        action="store_true",
        help="Force refresh of league snapshots even if same-date markers exist.",
    )
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Only ingest league baseline endpoints (minimal API calls).",
    )
    return parser.parse_args()


def main() -> None:
    run_start = perf_counter()
    args = parse_args()
    config = with_overrides(load_config(), league_id=args.league_id)
    run_date = resolve_run_date(args.run_date)
    logging.info(
        "Daily ingestion start run_date=%s league_id=%s season=%s baseline_only=%s force_snapshot_refresh=%s",
        run_date.isoformat(),
        config.league_id,
        config.season,
        args.baseline_only,
        args.force_league_snapshot_refresh,
    )
    ingestion_start = perf_counter()
    summary = run_ingestion(
        config,
        run_date,
        force_league_snapshot_refresh=args.force_league_snapshot_refresh,
        baseline_only=args.baseline_only,
    )
    logging.info("Ingestion step complete in %.2fs", perf_counter() - ingestion_start)
    logging.info("Completed run for %s: %s", run_date.isoformat(), summary)
    logging.info("Daily ingestion finished in %.2fs", perf_counter() - run_start)


if __name__ == "__main__":
    main()
