from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.config import load_validated_config
from src.config_schema import ConfigValidationError


def _write_yaml(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _base_config(tickers: list[str]) -> dict:
    return {
        "investor_currency": "USD",
        "tickers": tickers,
        "output_dir_final": "Main portfolio",
    }


def test_load_validated_config_loads_weights_when_tickers_match(tmp_path: Path) -> None:
    tickers = ["VOO", "BND"]
    config_path = tmp_path / "config.yml"
    weights_dir = tmp_path / "Main portfolio"
    weights_dir.mkdir(parents=True, exist_ok=True)
    weights_path = weights_dir / "portfolio_weights.yml"

    _write_yaml(config_path, _base_config(tickers))
    _write_yaml(weights_path, {"VOO": 0.6, "BND": 0.4})

    cfg = load_validated_config(config_path=config_path)
    assert cfg.weights == {"VOO": 0.6, "BND": 0.4}


def test_load_validated_config_raises_on_stale_weights_tickers_mismatch(tmp_path: Path) -> None:
    tickers = ["VOO", "BND"]
    config_path = tmp_path / "config.yml"
    weights_dir = tmp_path / "Main portfolio"
    weights_dir.mkdir(parents=True, exist_ok=True)
    weights_path = weights_dir / "portfolio_weights.yml"

    _write_yaml(config_path, _base_config(tickers))
    _write_yaml(weights_path, {"VOO": 0.6, "ARMY.PA": 0.4})

    with pytest.raises(ConfigValidationError, match="portfolio_weights.yml не соответствует текущему config.yml"):
        load_validated_config(config_path=config_path)
