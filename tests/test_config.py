from __future__ import annotations

import pytest

from src.pipeline.config import PipelineConfig, with_overrides


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
