from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from scripts.run_pipeline import (
    _resolve_warehouse_uri,
    build_dbt_build_cmd,
    main,
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


def test_main_skips_dbt_when_flatten_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config = SimpleNamespace(
        league_id=307,
        season=2024,
        storage_backend="local",
        local_root=str(tmp_path),
        s3_bucket=None,
        aws_region=None,
        gcs_bucket=None,
        gcs_project=None,
        warehouse_backend="snowflake",
        warehouse_uri="snowflake://user:pass@example.snowflakecomputing.com/LEAGUES_DATA/STAGING",
        warehouse_uri_test=None,
    )

    monkeypatch.setattr(
        "scripts.run_pipeline.parse_args",
        lambda: SimpleNamespace(
            run_date="2025-01-15",
            config_path=None,
            league_id=None,
            league_ids=None,
            project_dir="leagues_data_dbt",
            profiles_dir="leagues_data_dbt",
            select=["staging"],
            skip_ingestion=True,
            force_league_snapshot_refresh=False,
            baseline_only=False,
            dev_limit=None,
            skip_flatten=False,
            skip_dbt_build=False,
            dry_run=False,
        ),
    )
    monkeypatch.setattr("scripts.run_pipeline.load_configs_from_file", lambda _path: [config])
    monkeypatch.setattr("scripts.run_pipeline.with_overrides", lambda cfg, league_id=None, dev_limit=None: cfg)
    monkeypatch.setattr("scripts.run_pipeline.create_writer", lambda *args, **kwargs: object())
    monkeypatch.setattr("scripts.run_pipeline.generate_run_id", lambda: "run-1")
    monkeypatch.setattr("scripts.run_pipeline.shutil.which", lambda name: "/usr/bin/dbt")

    run_command_called = False

    def fake_run_command(command: list[str], dry_run: bool, step_name: str) -> None:
        nonlocal run_command_called
        run_command_called = True

    monkeypatch.setattr("scripts.run_pipeline._run_command", fake_run_command)

    def fake_run_flatten(*args, **kwargs):
        raise RuntimeError("warehouse sync failed")

    monkeypatch.setattr("scripts.run_pipeline.run_flatten", fake_run_flatten)

    with pytest.raises(RuntimeError, match="warehouse sync failed"):
        main()

    assert run_command_called is False
