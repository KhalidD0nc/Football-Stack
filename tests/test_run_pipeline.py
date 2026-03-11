from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from scripts.run_pipeline import (
    _resolve_warehouse_uri,
    build_dbt_build_cmd,
    parse_args,
)


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


def test_build_dbt_build_cmd_without_vars() -> None:
    cmd = build_dbt_build_cmd(
        project_dir=Path("/tmp/project"),
        profiles_dir=Path("/tmp/profiles"),
        selectors=["staging"],
    )
    assert "--vars" not in cmd


def test_parse_args_accepts_league_id() -> None:
    with patch.object(sys, "argv", ["run_pipeline", "--league-id", "39"]):
        args = parse_args()
    assert args.league_id == 39


def test_parse_args_defaults_to_post_staging_layers() -> None:
    with patch.object(sys, "argv", ["run_pipeline"]):
        args = parse_args()

    assert args.select == ["staging", "silver", "gold", "platinum"]


def test_parse_args_rejects_non_positive_league_id() -> None:
    with patch.object(sys, "argv", ["run_pipeline", "--league-id", "0"]):
        with pytest.raises(SystemExit):
            parse_args()


def test_resolve_warehouse_uri_adds_missing_test_schema() -> None:
    with patch.dict(
        os.environ,
        {
            "SNOWFLAKE_DATABASE": "LEAGUES_DATA",
            "SNOWFLAKE_SCHEMA": "STAGING",
        },
        clear=False,
    ):
        uri = _resolve_warehouse_uri("snowflake://user:pass@example.snowflakecomputing.com/LEAGUES_DATA_TEST", is_test=True)

    assert uri == "snowflake://user:pass@example.snowflakecomputing.com/LEAGUES_DATA_TEST/STAGING"
