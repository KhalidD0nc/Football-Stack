from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from scripts.run_pipeline import (
    build_dbt_build_cmd,
    build_dbt_raw_sync_cmd,
    build_raw_sync_macro_args,
    parse_args,
)


def test_build_raw_sync_macro_args_with_explicit_database() -> None:
    args = build_raw_sync_macro_args(
        run_date=date(2026, 2, 25),
        raw_database="LEAGUES_DATA",
        raw_schema="RAW",
        stage_name="LEAGUES_STAGE",
    )

    assert args == {
        "run_date": "2026-02-25",
        "raw_database": "LEAGUES_DATA",
        "raw_schema": "RAW",
        "stage_name": "LEAGUES_STAGE",
    }


def test_build_raw_sync_macro_args_without_database() -> None:
    args = build_raw_sync_macro_args(
        run_date=date(2026, 2, 25),
        raw_database=None,
        raw_schema="RAW",
        stage_name="LEAGUES_STAGE",
    )

    assert "raw_database" not in args
    assert args["run_date"] == "2026-02-25"
    assert args["raw_schema"] == "RAW"
    assert args["stage_name"] == "LEAGUES_STAGE"


def test_build_raw_sync_macro_args_without_date_filter() -> None:
    args = build_raw_sync_macro_args(
        run_date=None,
        raw_database=None,
        raw_schema="RAW",
        stage_name="LEAGUES_STAGE",
    )

    assert "run_date" not in args
    assert args["raw_schema"] == "RAW"
    assert args["stage_name"] == "LEAGUES_STAGE"


def test_build_dbt_raw_sync_cmd_contains_serialized_macro_args() -> None:
    macro_args = {
        "run_date": "2026-02-25",
        "raw_database": "LEAGUES_DATA",
        "raw_schema": "RAW",
        "stage_name": "LEAGUES_STAGE",
    }
    cmd = build_dbt_raw_sync_cmd(
        project_dir=Path("/tmp/project"),
        profiles_dir=Path("/tmp/profiles"),
        macro_args=macro_args,
    )

    assert cmd[:8] == [
        "dbt",
        "run-operation",
        "sync_raw_from_s3",
        "--project-dir",
        str(Path("/tmp/project")),
        "--profiles-dir",
        str(Path("/tmp/profiles")),
        "--args",
    ]
    args_index = cmd.index("--args") + 1
    assert json.loads(cmd[args_index]) == macro_args


def test_build_dbt_build_cmd_uses_selectors() -> None:
    cmd = build_dbt_build_cmd(
        project_dir=Path("/tmp/project"),
        profiles_dir=Path("/tmp/profiles"),
        selectors=["staging", "silver", "gold"],
    )

    assert cmd == [
        "dbt",
        "build",
        "--project-dir",
        "/tmp/project",
        "--profiles-dir",
        "/tmp/profiles",
        "--fail-fast",
        "--select",
        "staging",
        "silver",
        "gold",
    ]


def test_parse_args_accepts_league_id() -> None:
    with patch.object(sys, "argv", ["run_pipeline", "--league-id", "39"]):
        args = parse_args()
    assert args.league_id == 39


def test_parse_args_rejects_non_positive_league_id() -> None:
    with patch.object(sys, "argv", ["run_pipeline", "--league-id", "0"]):
        with pytest.raises(SystemExit):
            parse_args()
