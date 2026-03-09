from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.pipeline.config import PipelineConfig, load_configs_from_file, with_overrides


def _base_config() -> PipelineConfig:
    return PipelineConfig(
        api_football_key="test-key",
        api_base_url="https://example.com",
        league_id=307,
        season=2025,
        timezone="UTC",
        players_max_pages=200,
        team_id=2932,
        storage_backend="s3",
        local_root="data_lake",
        aws_region="us-east-1",
        s3_bucket="bucket",
        gcs_bucket=None,
        gcs_project=None,
    )


def test_with_overrides_applies_league_id() -> None:
    cfg = _base_config()
    updated = with_overrides(cfg, league_id=39)
    assert updated.league_id == 39
    assert updated.season == cfg.season
    assert updated.team_id == cfg.team_id


def test_with_overrides_none_keeps_original_values() -> None:
    cfg = _base_config()
    updated = with_overrides(cfg, league_id=None)
    assert updated == cfg


def test_with_overrides_rejects_non_positive_league_id() -> None:
    cfg = _base_config()
    with pytest.raises(ValueError, match="positive integer"):
        with_overrides(cfg, league_id=0)


def test_load_configs_multi_target(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "settings": {
            "timezone": "Europe/London",
            "storage": {"backend": "local"}
        },
        "targets": [
            {"league_id": 39, "seasons": [2023, 2024]},
            {"league_id": 140, "seasons": [2023]}
        ]
    }))
    
    with patch("src.pipeline.config.load_dotenv"), patch.dict("os.environ", {"API_FOOTBALL_KEY": "dummy"}, clear=True):
        configs = load_configs_from_file(config_file)
        
    assert len(configs) == 3
    assert configs[0].league_id == 39
    assert configs[0].season == 2023
    assert configs[0].timezone == "Europe/London"
    assert configs[1].league_id == 39
    assert configs[1].season == 2024
    assert configs[2].league_id == 140
    assert configs[2].season == 2023
    assert configs[0].storage_backend == "local"


def test_load_configs_backend_inference(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "settings": {
            "storage": {"s3_bucket": "my-bucket", "aws_region": "eu-west-1"}
        },
        "targets": [
            {"league_id": 39, "seasons": [2023]}
        ]
    }))
    
    with patch("src.pipeline.config.load_dotenv"), patch.dict("os.environ", {"API_FOOTBALL_KEY": "dummy"}, clear=True):
        configs = load_configs_from_file(config_file)
        
    assert len(configs) == 1
    assert configs[0].storage_backend == "s3"
    assert configs[0].s3_bucket == "my-bucket"
    assert configs[0].aws_region == "eu-west-1"


def test_load_configs_missing_targets(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "settings": {},
        "targets": []
    }))
    
    with patch("src.pipeline.config.load_dotenv"), patch.dict("os.environ", {"API_FOOTBALL_KEY": "dummy"}, clear=True):
        with pytest.raises(ValueError, match="No targets found in config file"):
            load_configs_from_file(config_file)


def test_load_configs_missing_seasons(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "settings": {},
        "targets": [{"league_id": 39}]
    }))
    
    with patch("src.pipeline.config.load_dotenv"), patch.dict("os.environ", {"API_FOOTBALL_KEY": "dummy"}, clear=True):
        with pytest.raises(ValueError, match="No targets found in config file"):
            load_configs_from_file(config_file)


def test_load_configs_s3_missing_bucket(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "settings": {
            "storage": {"backend": "s3"}
        },
        "targets": [{"league_id": 39, "seasons": [2023]}]
    }))
    
    with patch("src.pipeline.config.load_dotenv"), patch.dict("os.environ", {"API_FOOTBALL_KEY": "dummy"}, clear=True):
        with pytest.raises(ValueError, match="s3_bucket is required when storage backend is 's3'"):
            load_configs_from_file(config_file)


def test_load_configs_gcs_properties(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "settings": {
            "storage": {
                "backend": "gcs",
                "gcs_bucket": "my-gcs-bucket",
                "gcs_project": "my-gcs-project"
            }
        },
        "targets": [{"league_id": 39, "seasons": [2023]}]
    }))
    
    with patch("src.pipeline.config.load_dotenv"), patch.dict("os.environ", {"API_FOOTBALL_KEY": "dummy"}, clear=True):
        configs = load_configs_from_file(config_file)
        
    assert len(configs) == 1
    assert configs[0].storage_backend == "gcs"
    assert configs[0].gcs_bucket == "my-gcs-bucket"
    assert configs[0].gcs_project == "my-gcs-project"


def test_load_configs_gcs_env_fallback(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "settings": {
            "storage": {"backend": "gcs"}
        },
        "targets": [{"league_id": 39, "seasons": [2023]}]
    }))
    
    env_vars = {
        "API_FOOTBALL_KEY": "dummy",
        "GCS_BUCKET": "env-gcs-bucket",
        "GCS_PROJECT": "env-gcs-project",
    }
    with patch("src.pipeline.config.load_dotenv"), patch.dict("os.environ", env_vars, clear=True):
        configs = load_configs_from_file(config_file)
        
    assert len(configs) == 1
    assert configs[0].storage_backend == "gcs"
    assert configs[0].gcs_bucket == "env-gcs-bucket"
    assert configs[0].gcs_project == "env-gcs-project"
