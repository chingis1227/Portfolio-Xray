"""Tests for Scenario Library v1 input layer."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.scenario_library import (
    SCENARIO_LIBRARY_VERSION,
    build_scenario_library,
    summarize_scenario_classifications,
)


def _minimal_factors_nested():
    """3x3 PSD-ish factor covariance for tests."""
    factors = ["equity", "real_rates", "inflation"]
    m = {
        "equity": {"equity": 0.0004, "real_rates": 0.0001, "inflation": 0.0},
        "real_rates": {"equity": 0.0001, "real_rates": 0.0001, "inflation": 0.0},
        "inflation": {"equity": 0.0, "real_rates": 0.0, "inflation": 0.0001},
    }
    for f in factors:
        m.setdefault(f, {})
    return m


def test_build_scenario_library_smoke(tmp_path: Path):
    idx = pd.date_range("2015-01-01", periods=80, freq="ME")
    monthly_returns = pd.DataFrame(
        {
            "AAA": np.random.default_rng(1).normal(0.005, 0.02, len(idx)),
            "BBB": np.random.default_rng(2).normal(0.004, 0.03, len(idx)),
        },
        index=idx,
    )
    weights = {"AAA": 0.6, "BBB": 0.4}
    tickers = ["AAA", "BBB"]

    stress_report: dict = {
        "factor_covariance": {
            "base": {
                "matrix": _minimal_factors_nested(),
                "n_obs": 260,
                "window": {"analysis_end": "2024-12-31"},
            },
            "portfolio_factor_rc": {
                "base": [{"factor": "equity", "rc_share": 0.5}],
            },
        },
        "factor_betas_5y": {"beta_eq": 0.9, "beta_rr": -0.1},
        "factor_betas_10y": {"beta_eq": 0.85, "beta_rr": -0.08},
        "scenario_results": [
            {
                "scenario_id": "equity_shock",
                "portfolio_pnl_pct": -0.15,
                "shock_vector": {"shock_eq": -0.40},
            },
        ],
        "historical_results": [
            {
                "episode": "2020",
                "episode_start": "2020-02-01",
                "episode_end": "2020-05-31",
                "pnl_real_episode": -0.12,
            }
        ],
        "stress_scenario_analytics": {
            "scenarios": {
                "equity_shock": {
                    "suitable_robust_optimization_input": False,
                    "warnings": [],
                    "asset_covariance": {"n_obs": 80, "quality_status": "usable"},
                },
                "2020": {
                    "data_start": "2020-02-01",
                    "data_end": "2020-05-31",
                    "suitable_robust_optimization_input": False,
                    "warnings": [],
                    "top_asset_risk_contributors": {},
                },
            }
        },
    }

    widx = pd.date_range("2019-01-01", periods=120, freq="W-FRI")
    factor_returns_weekly = pd.DataFrame(
        {
            "equity": np.random.default_rng(3).normal(0.0, 0.02, len(widx)),
            "real_rates": np.random.default_rng(4).normal(0.0, 0.01, len(widx)),
            "inflation": np.random.default_rng(5).normal(0.0, 0.005, len(widx)),
        },
        index=widx,
    )
    for c in [
        "credit",
        "usd",
        "commodity",
        "vix",
        "us_growth",
        "oil",
    ]:
        if c not in factor_returns_weekly.columns:
            factor_returns_weekly[c] = 0.0

    out = build_scenario_library(
        stress_report,
        weights=weights,
        tickers=tickers,
        monthly_returns=monthly_returns,
        returns_frequency="monthly",
        regime_factor_analytics_full=None,
        factor_returns_weekly=factor_returns_weekly,
        cash_proxy_ticker=None,
        output_dir_final=tmp_path,
        output_dir_csv=tmp_path,
    )

    assert out["version"] == SCENARIO_LIBRARY_VERSION
    assert out["n_scenarios"] >= 1
    sl_path = tmp_path / "scenario_library.json"
    assert sl_path.exists()
    raw = json.loads(sl_path.read_text(encoding="utf-8"))
    assert raw["n_scenarios"] == out["n_scenarios"]
    counts = summarize_scenario_classifications(raw["scenarios"])
    assert sum(counts.values()) == raw["n_scenarios"]


def test_summarize_scenario_classifications():
    rows = [
        {"classification": "ready_for_optimization"},
        {"classification": "usable_with_caution"},
        {"classification": "diagnostic_only"},
        {"classification": "insufficient_data"},
    ]
    c = summarize_scenario_classifications(rows)
    assert c["ready_for_optimization"] == 1
    assert c["usable_with_caution"] == 1
    assert c["diagnostic_only"] == 1
    assert c["insufficient_data"] == 1
