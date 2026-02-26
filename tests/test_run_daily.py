from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from scripts.run_daily import parse_args


def test_parse_args_accepts_league_id() -> None:
    with patch.object(sys, "argv", ["run_daily", "--league-id", "39"]):
        args = parse_args()
    assert args.league_id == 39


def test_parse_args_rejects_invalid_league_id() -> None:
    with patch.object(sys, "argv", ["run_daily", "--league-id", "-1"]):
        with pytest.raises(SystemExit):
            parse_args()
