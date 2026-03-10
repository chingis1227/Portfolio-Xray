from __future__ import annotations

"""
Basic tests for run_risk_budget_optimization fallback behavior.

Goal: under tight RC/weight settings and a tiny universe, the optimizer must
still return a valid weight vector (sum ~= 1, 0 <= w_i <= 1), even if it has
to fall back from the full constrained solution.
"""

import numpy as np
import pandas as pd

from src.optimization import run_risk_budget_optimization, get_risk_portfolio_tickers


def _synthetic_returns() -> pd.DataFrame:
    """Build a small synthetic monthly returns DataFrame for tests."""
    dates = pd.date_range("2020-01-31", periods=24, freq="M")
    data = {
        "VOO": np.linspace(0.01, 0.02, len(dates)),
        "BND": np.linspace(0.005, 0.007, len(dates)),
        "GLD": np.linspace(0.0, 0.015, len(dates)),
    }
    return pd.DataFrame(data, index=dates)


def test_run_risk_budget_optimization_returns_weights_under_tight_caps():
    """
    With very tight RC/weight caps and a tiny universe, optimizer should still
    return a non-empty weight dict whose weights are valid probabilities.
    """
    returns_df = _synthetic_returns()
    blocks = {
        "Growth": ["VOO"],
        "Duration": ["BND"],
        "Inflation": ["GLD"],
        "Growth_HY": [],
        "Growth_EM_debt": [],
        "Liquidity": [],
        "Tail": [],
    }
    rc_block_targets = {"Growth": 0.6, "Duration": 0.3, "Inflation": 0.1}

    weights, status = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc_block_targets,
        growth_core_candidates=["VOO"],
        rc_asset_cap_pct=0.15,  # deliberately tight
        min_single_security_weight_pct=0.01,
        max_single_security_weight_pct=0.6,
        window_months=24,
    )

    assert weights, f"Expected non-empty weights, got empty (status={status})"

    s = sum(weights.values())
    assert abs(s - 1.0) < 1e-6, f"Sum of weights must be ~1, got {s}"

    for t, w in weights.items():
        assert 0.0 <= w <= 1.0 + 1e-8, f"Weight for {t} must be in [0, 1], got {w}"

