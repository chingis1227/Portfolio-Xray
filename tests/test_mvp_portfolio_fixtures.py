"""Validation tests for Core MVP portfolio YAML fixtures (Session 04)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.config import resolve_cash_and_rf
from src.config_schema import validate_config
from src.real_cash import collect_real_cash_tickers

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "mvp_portfolios"


def _load_fixture(name: str) -> dict:
    path = _FIXTURE_DIR / name
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    assert isinstance(raw, dict), name
    return raw


@pytest.mark.parametrize(
    "fixture_name",
    ["minimal_usd_no_cash.yml", "minimal_usd_with_cash.yml"],
)
def test_mvp_fixture_validates(fixture_name: str) -> None:
    cfg = validate_config(_load_fixture(fixture_name))

    assert cfg.investor_currency == "USD"
    assert cfg.analysis_mode == "analyze_current_weights"
    assert cfg.analysis_subject["type"] == "current_portfolio"
    assert cfg.weights_source == "config.analysis_subject.weights"
    assert sum(cfg.weights.values()) == pytest.approx(1.0, abs=1e-6)


def test_minimal_usd_no_cash_has_no_real_cash() -> None:
    cfg = validate_config(_load_fixture("minimal_usd_no_cash.yml"))

    assert collect_real_cash_tickers(tickers=cfg.tickers, weights=cfg.weights) == []
    cash_proxy, _ = resolve_cash_and_rf(cfg)
    assert cash_proxy == "BIL"


def test_minimal_usd_with_cash_keeps_cash_usd_not_bil() -> None:
    cfg = validate_config(_load_fixture("minimal_usd_with_cash.yml"))

    assert "Cash USD" in cfg.weights
    assert cfg.weights["Cash USD"] == pytest.approx(0.10)
    assert cfg.weights.get("BIL") is None
    assert collect_real_cash_tickers(tickers=cfg.tickers, weights=cfg.weights) == ["Cash USD"]
    cash_proxy, _ = resolve_cash_and_rf(cfg)
    assert cash_proxy == "BIL"
