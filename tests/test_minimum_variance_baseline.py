"""
Tests for Minimum-Variance baseline construction (portfolio_variants).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.config_schema import PortfolioConfig
from src.portfolio_variants import (
    build_equal_weight_baseline,
    build_minimum_variance_baseline,
)
from src.risk_contrib import cov_matrix_monthly
from src.risk_parity_spinu import repair_covariance_psd


def _minimal_portfolio_config(
    tickers: list[str],
    *,
    min_w: float | None = None,
    max_w: float | None = None,
) -> PortfolioConfig:
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
        max_single_security_weight_pct=max_w,
        min_single_security_weight_pct=min_w,
        N_rc=5,
        donor_shift_mode="proportional",
        windows_months=[36, 60, 120],
        coverage_threshold=0.90,
        output_dir="results_csv",
        output_dir_final="Main portfolio",
        covariance_shrinkage=False,
        young_etf_optimization_policy={"enabled": False},
    )


def test_build_minimum_variance_three_assets_bounds_and_sum() -> None:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2015-01-31", periods=120, freq="ME")
    n = len(dates)
    r_high = rng.normal(0.003, 0.04, n)
    r_mid = rng.normal(0.003, 0.02, n)
    r_low = rng.normal(0.003, 0.01, n)
    returns = pd.DataFrame({"H": r_high, "M": r_mid, "L": r_low}, index=dates)
    cfg = _minimal_portfolio_config(["H", "M", "L"])
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_minimum_variance_baseline(cfg, returns, end, 120)
    assert res.status in ("OK", "APPROXIMATE")
    s = sum(res.weights.values())
    assert abs(s - 1.0) < 1e-4
    for t in ("H", "M", "L"):
        assert res.weights[t] >= 0.0
        assert 0.01 - 1e-6 <= res.weights[t] <= 0.40 + 1e-3  # feasibility cap for N=3
    diag = res.diagnostics
    assert diag.get("optimizer_name") == "minimum_variance"
    assert diag.get("solver") == "SLSQP"
    assert diag.get("covariance_method") == "sample_monthly_ddof1"
    assert diag.get("shrinkage_used") is False
    assert diag.get("portfolio_variance") is not None
    assert diag.get("annualized_volatility") is not None
    assert "solver_success" in diag


def test_minimum_variance_variance_vs_equal_weight_same_covariance() -> None:
    rng = np.random.default_rng(7)
    dates = pd.date_range("2014-12-31", periods=80, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.05, n),
            "B": rng.normal(0.0, 0.03, n),
            "C": rng.normal(0.0, 0.02, n),
        },
        index=dates,
    )
    cfg = _minimal_portfolio_config(["A", "B", "C"])
    end = dates[-1].strftime("%Y-%m-%d")
    mv = build_minimum_variance_baseline(cfg, returns, end, len(dates))
    eq = build_equal_weight_baseline(cfg, returns, end, len(dates))
    assert mv.status in ("OK", "APPROXIMATE")
    cols = ["A", "B", "C"]
    cov_df = cov_matrix_monthly(returns[cols], ddof=1, use_shrinkage=False)
    cov_np, _ = repair_covariance_psd(cov_df.values)
    w_mv = np.array([mv.weights[t] for t in cols], dtype=float)
    w_eq = np.array([eq.weights[t] for t in cols], dtype=float)
    var_mv = float(w_mv @ cov_np @ w_mv)
    var_eq = float(w_eq @ cov_np @ w_eq)
    assert var_mv <= var_eq + 1e-8


def test_minimum_variance_infeasible_bounds() -> None:
    dates = pd.date_range("2015-01-31", periods=60, freq="ME")
    n = len(dates)
    rng = np.random.default_rng(1)
    returns = pd.DataFrame(
        {
            "X": rng.normal(0.005, 0.02, n),
            "Y": rng.normal(0.005, 0.02, n),
            "Z": rng.normal(0.005, 0.02, n),
        },
        index=dates,
    )
    cfg = _minimal_portfolio_config(["X", "Y", "Z"], min_w=0.40)
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_minimum_variance_baseline(cfg, returns, end, 60)
    assert res.status == "FAIL_INFEASIBLE_BOUNDS"
    assert sum(res.weights.values()) == 0.0


def test_minimum_variance_import_run_script() -> None:
    import run_minimum_variance as rmv

    assert callable(rmv.main)
