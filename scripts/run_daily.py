from __future__ import annotations

import argparse
import logging

from src.pipeline.config import load_config, resolve_run_date
from src.pipeline.ingest import run_ingestion


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SPL thin-slice daily ingestion")
    parser.add_argument("--date", dest="run_date", help="Run date in YYYY-MM-DD", default=None)
    args = parser.parse_args()

    config = load_config()
    run_date = resolve_run_date(args.run_date)
    summary = run_ingestion(config, run_date)
    logging.info("Completed run for %s: %s", run_date.isoformat(), summary)


if __name__ == "__main__":
    main()
