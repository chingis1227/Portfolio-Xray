"""Tests for historical stress fallback v1."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.historical_stress_fallback import (
    build_historical_episode_asset_returns,
    dominant_historical_stress_method,
    merge_proxy_config,
)


def test_merge_proxy_config_overrides_defaults() -> None:
    base = merge_proxy_config(None, {"min_coverage_ratio": 0.9})
    assert float(base["min_coverage_ratio"]) == 0.9


def test_direct_etf_history_used_when_coverage_ok() -> None:
    idx = pd.date_range("2000-01-31", periods=40, freq="ME")
    mr = pd.DataFrame({"AAA": np.linspace(0.001, -0.02, len(idx))}, index=idx)
    rd, meta = build_historical_episode_asset_returns(
        scenario_id="dotcom",
        episode_start="2000-03-01",
        episode_end="2002-10-31",
        risk_tickers=["AAA"],
        monthly_returns=mr,
        stress_report=None,
        proxy_config={"min_coverage_ratio": 0.3},
        factor_returns_weekly=None,
    )
    assert "AAA" in rd
    assert meta["historical_stress_method_per_asset"]["AAA"] == "direct_etf_history"
    assert meta["assets_with_direct_history"] == ["AAA"]


def test_ticker_proxy_when_primary_missing() -> None:
    idx = pd.date_range("2007-10-31", periods=30, freq="ME")
    mr = pd.DataFrame(
        {
            "VOO": [np.nan] * 30,
            "SPY": [-0.02] * 30,
        },
        index=idx,
    )
    cfg = {"ticker_proxies": {"VOO": "SPY"}, "min_coverage_ratio": 0.45}
    rd, meta = build_historical_episode_asset_returns(
        scenario_id="2008",
        episode_start="2007-10-01",
        episode_end="2009-03-31",
        risk_tickers=["VOO"],
        monthly_returns=mr,
        stress_report=None,
        proxy_config=cfg,
        factor_returns_weekly=None,
    )
    assert "VOO" in rd
    assert meta["historical_stress_method_per_asset"]["VOO"] == "ticker_proxy"


def test_partition_disjoint() -> None:
    pa = {"A": "direct_etf_history", "B": "ticker_proxy"}
    assert dominant_historical_stress_method(pa) == "ticker_proxy"


def test_factor_replay_when_monthly_panel_has_no_dotcom_window() -> None:
    """Episode before monthly panel: factor sums + asset betas still recover per-asset returns."""
    idx = pd.date_range("2014-01-31", periods=24, freq="ME")
    mr = pd.DataFrame({"AAA": np.full(len(idx), 0.001)}, index=idx)
    fr_idx = pd.date_range("2000-03-03", periods=20, freq="W-FRI")
    fr = pd.DataFrame({"equity": np.full(len(fr_idx), -0.01)}, index=fr_idx)
    stress = {
        "asset_factor_betas": {
            "AAA": {"betas": {"beta_eq": 1.0, "beta_rr": 0.0, "beta_inf": 0.0, "beta_credit": 0.0, "beta_usd": 0.0, "beta_cmd": 0.0, "beta_vix": 0.0, "beta_us_growth": 0.0}},
        }
    }
    rd, meta = build_historical_episode_asset_returns(
        scenario_id="dotcom",
        episode_start="2000-03-01",
        episode_end="2000-06-30",
        risk_tickers=["AAA"],
        monthly_returns=mr,
        stress_report=stress,
        proxy_config={"min_coverage_ratio": 0.45},
        factor_returns_weekly=fr,
    )
    assert "AAA" in rd
    assert meta["historical_stress_method_per_asset"]["AAA"] == "factor_replay"
    assert meta["historical_stress_method"] == "factor_replay"
