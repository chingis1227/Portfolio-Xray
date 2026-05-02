"""
Tests for Risk-Parity baseline construction (portfolio_variants / run_risk_parity pipeline inputs).
"""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import numpy as np
import pandas as pd

from src.config_schema import PortfolioConfig
from src.portfolio_variants import _risk_parity_solver, build_risk_parity_baseline


def _minimal_portfolio_config(tickers: list[str]) -> PortfolioConfig:
    n = len(tickers)
    eq = 1.0 / n if n else 0.0
    return PortfolioConfig(
        investor_currency="USD",
        initial_investable_amount=100_000.0,
        liquidity_need=0.0,
        liquidity_need_months=6.0,
        monthly_expenses=0.0,
        portfolio_value=100_000.0,
        cash_policy="allowed_for_scaling",
        tickers=list(tickers),
        weights={t: eq for t in tickers},
        benchmark_base_ticker="VOO",
        rf_source="FRED:DTB3",
        cash_proxy_ticker="BIL",
        local_benchmark_map=None,
        allow_leverage=False,
        allow_short_selling=False,
        min_acceptable_return=None,
        target_nominal_return_annual=None,
        target_vol_annual=None,
        target_max_drawdown_pct=None,
        horizon_years=None,
        client_profile=None,
        max_single_security_weight_pct=None,
        min_single_security_weight_pct=None,
        N_rc=5,
        donor_shift_mode="proportional",
        windows_months=[36, 60, 120],
        coverage_threshold=0.90,
        output_dir="results_csv",
        output_dir_final="Main portfolio",
    )


def test_risk_parity_solver_equal_weights_diagonal_cov() -> None:
    """Equal variances and no correlations → ~equal weights and low RC dispersion."""
    cols = ["a", "b", "c"]
    cov = pd.DataFrame(np.eye(3) * 0.01, index=cols, columns=cols)
    weights, diag = _risk_parity_solver(cov, cols)
    assert abs(sum(weights.values()) - 1.0) < 1e-6
    for t in cols:
        assert abs(weights[t] - 1.0 / 3.0) < 0.02
    assert float(diag.get("max_rc_error", 1.0)) < 0.02


def test_build_risk_parity_infeasible_single_ticker() -> None:
    """Need at least two eligible assets."""
    dates = pd.date_range("2015-01-31", periods=60, freq="M")
    returns = pd.DataFrame({"VOO": np.random.default_rng(1).normal(0.005, 0.02, len(dates))}, index=dates)
    cfg = _minimal_portfolio_config(["VOO"])
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_risk_parity_baseline(cfg, returns, end, 60)
    assert res.status == "FAIL_INFEASIBLE_UNIVERSE"
    assert "Fewer than 2 eligible" in str(res.diagnostics.get("reason", ""))


def test_build_risk_parity_three_assets_weights_valid() -> None:
    """Full baseline: long-only, sum to 1, solver diagnostics present."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2015-01-31", periods=120, freq="M")
    n = len(dates)
    r_high = rng.normal(0.003, 0.04, n)
    r_mid = rng.normal(0.003, 0.02, n)
    r_low = rng.normal(0.003, 0.01, n)
    returns = pd.DataFrame({"H": r_high, "M": r_mid, "L": r_low}, index=dates)
    cfg = _minimal_portfolio_config(["H", "M", "L"])
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_risk_parity_baseline(cfg, returns, end, 120)
    assert res.status in ("OK", "APPROXIMATE")
    assert res.diagnostics.get("max_rc_error") is not None
    s = sum(res.weights.values())
    assert abs(s - 1.0) < 1e-5
    positive = [t for t, w in res.weights.items() if w > 1e-8]
    assert set(positive) == {"H", "M", "L"}
    # Higher realized vol name: typically lower RP weight than low-vol name
    assert res.weights["H"] < res.weights["L"]
