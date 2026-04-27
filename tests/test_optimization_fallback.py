from __future__ import annotations

"""
Basic tests for run_risk_budget_optimization fallback behavior.
"""

import numpy as np
import pandas as pd

from src.optimization import run_risk_budget_optimization


def _synthetic_returns() -> pd.DataFrame:
    dates = pd.date_range("2020-01-31", periods=24, freq="M")
    data = {
        "VOO": np.linspace(0.01, 0.02, len(dates)),
        "BND": np.linspace(0.005, 0.007, len(dates)),
        "GLD": np.linspace(0.0, 0.015, len(dates)),
    }
    return pd.DataFrame(data, index=dates)


def test_run_risk_budget_optimization_returns_weights_under_tight_caps():
    returns_df = _synthetic_returns()
    risk_tickers = ["VOO", "BND", "GLD"]

    weights, status = run_risk_budget_optimization(
        returns_df=returns_df,
        risk_tickers=risk_tickers,
        growth_core_candidates=["VOO"],
        rc_asset_cap_pct=0.15,
        min_single_security_weight_pct=0.01,
        max_single_security_weight_pct=0.6,
        window_months=24,
    )

    assert weights, f"Expected non-empty weights, got empty (status={status})"

    s = sum(weights.values())
    assert abs(s - 1.0) < 1e-6, f"Sum of weights must be ~1, got {s}"

    for t, w in weights.items():
        assert 0.0 <= w <= 1.0 + 1e-8, f"Weight for {t} must be in [0, 1], got {w}"
