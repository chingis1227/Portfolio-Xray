"""
Tests for Maximum-Diversification baseline construction (portfolio_variants).
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
    build_maximum_diversification_constrained,
    build_maximum_diversification_unconstrained,
    maximum_diversification_baseline_metadata_export,
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
        minimum_variance_turnover_lambda=0.0,
        young_etf_optimization_policy={"enabled": False},
    )


def _diversification_ratio(w: np.ndarray, cov_np: np.ndarray) -> float:
    sig = np.sqrt(np.maximum(np.diag(np.asarray(cov_np, dtype=float)), 0.0))
    v = float(w @ cov_np @ w)
    d = np.sqrt(max(v, 1e-30))
    return float(sig @ w) / d


def test_build_maximum_diversification_three_assets_bounds_sum() -> None:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2015-01-31", periods=120, freq="ME")
    n = len(dates)
    r_high = rng.normal(0.003, 0.04, n)
    r_mid = rng.normal(0.003, 0.02, n)
    r_low = rng.normal(0.003, 0.01, n)
    returns = pd.DataFrame({"H": r_high, "M": r_mid, "L": r_low}, index=dates)
    cfg = _minimal_portfolio_config(["H", "M", "L"])
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_maximum_diversification_constrained(cfg, returns, end, 120)
    assert res.status in ("OK", "APPROXIMATE")
    assert abs(sum(res.weights.values()) - 1.0) < 1e-4
    for t in ("H", "M", "L"):
        assert res.weights[t] >= 0.0
        assert 0.01 - 1e-6 <= res.weights[t] <= 0.40 + 1e-3
    diag = res.diagnostics
    assert diag.get("optimizer_name") == "maximum_diversification_constrained"
    assert diag.get("solver") == "SLSQP"
    assert diag.get("covariance_method") == "sample_monthly_ddof1"
    assert diag.get("shrinkage_used") is False
    assert diag.get("diversification_ratio") is not None
    assert float(diag.get("diversification_ratio", 0.0)) >= 1.0 - 1e-6
    meta = maximum_diversification_baseline_metadata_export(diag)
    orm = meta["optimizer_run_metadata"]
    assert orm["schema_version"] == "candidate_optimizer_run_metadata_v1"
    assert orm["method_id"] == "maximum_diversification_constrained"
    assert orm["input_window"]["analysis_end"] == end
    assert orm["input_window"]["window_months"] == 120
    assert orm["input_window"]["returns_panel_end"] == end
    assert len(orm["input_fingerprints"]["returns_panel_fingerprint"]) == 64
    assert len(orm["input_fingerprints"]["config_fingerprint"]) == 64
    assert len(orm["input_fingerprints"]["universe_fingerprint"]) == 64
    assert orm["constraints"]["bounds_used"]["H"]["min"] == 0.01
    assert orm["solver"]["name"] == "SLSQP"


def test_maximum_diversification_dr_ge_equal_weight_same_covariance() -> None:
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
    md = build_maximum_diversification_constrained(cfg, returns, end, len(dates))
    eq = build_equal_weight_baseline(cfg, returns, end, len(dates))
    assert md.status in ("OK", "APPROXIMATE")
    cols = ["A", "B", "C"]
    cov_df = cov_matrix_monthly(returns[cols], ddof=1, use_shrinkage=False)
    cov_np, _ = repair_covariance_psd(cov_df.values)
    w_md = np.array([md.weights[t] for t in cols], dtype=float)
    w_eq = np.array([eq.weights[t] for t in cols], dtype=float)
    dr_md = _diversification_ratio(w_md, cov_np)
    dr_eq = _diversification_ratio(w_eq, cov_np)
    assert dr_md >= dr_eq - 1e-5


def test_maximum_diversification_infeasible_bounds() -> None:
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
    res = build_maximum_diversification_constrained(cfg, returns, end, 60)
    assert res.status == "FAIL_INFEASIBLE_BOUNDS"
    assert sum(res.weights.values()) == 0.0


def test_maximum_diversification_import_run_script() -> None:
    import run_maximum_diversification as rmd

    assert callable(rmd.main)


def test_build_maximum_diversification_unconstrained_three_assets() -> None:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2015-01-31", periods=120, freq="ME")
    n = len(dates)
    r_high = rng.normal(0.003, 0.04, n)
    r_mid = rng.normal(0.003, 0.02, n)
    r_low = rng.normal(0.003, 0.01, n)
    returns = pd.DataFrame({"H": r_high, "M": r_mid, "L": r_low}, index=dates)
    cfg = _minimal_portfolio_config(["H", "M", "L"])
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_maximum_diversification_unconstrained(cfg, returns, end, 120)
    assert res.status in ("OK", "APPROXIMATE")
    assert abs(sum(res.weights.values()) - 1.0) < 1e-4
    for t in ("H", "M", "L"):
        assert res.weights[t] >= -1e-9
    diag = res.diagnostics
    assert diag.get("optimizer_name") == "maximum_diversification_unconstrained"
    assert diag.get("active_constraints") == [
        "equality: sum(weights) = 1",
        "long-only: weights >= 0",
    ]
    assert diag.get("diversification_ratio") is not None
    assert float(diag.get("diversification_ratio", 0.0)) >= 1.0 - 1e-6


def test_maximum_diversification_unconstrained_succeeds_when_constrained_infeasible() -> None:
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
    c_res = build_maximum_diversification_constrained(cfg, returns, end, 60)
    u_res = build_maximum_diversification_unconstrained(cfg, returns, end, 60)
    assert c_res.status == "FAIL_INFEASIBLE_BOUNDS"
    assert u_res.status in ("OK", "APPROXIMATE")
    assert abs(sum(u_res.weights.values()) - 1.0) < 1e-4


def test_unconstrained_diversification_ratio_greater_or_equal_constrained() -> None:
    rng = np.random.default_rng(123)
    dates = pd.date_range("2015-01-31", periods=100, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.12, n),
            "B": rng.normal(0.0, 0.04, n),
            "C": rng.normal(0.0, 0.04, n),
            "D": rng.normal(0.0, 0.04, n),
            "E": rng.normal(0.0, 0.04, n),
        },
        index=dates,
    )
    tickers = ["A", "B", "C", "D", "E"]
    # Need sum of upper bounds >= 1 for a fully-invested box (5 * 0.15 < 1 is infeasible).
    cfg = _minimal_portfolio_config(tickers, max_w=0.22, min_w=0.01)
    end = dates[-1].strftime("%Y-%m-%d")
    wnd = len(dates)
    u_res = build_maximum_diversification_unconstrained(cfg, returns, end, wnd)
    c_res = build_maximum_diversification_constrained(cfg, returns, end, wnd)
    assert u_res.status in ("OK", "APPROXIMATE")
    assert c_res.status in ("OK", "APPROXIMATE")
    dr_u = float(u_res.diagnostics["diversification_ratio"])
    dr_c = float(c_res.diagnostics["diversification_ratio"])
    assert dr_u >= dr_c - 1e-5


def test_unconstrained_weight_can_exceed_project_config_max() -> None:
    """Unconstrained MaxDiv uses [0,1] bounds only; config max_single should not cap the optimizer."""
    n = 200
    dates = pd.date_range("2015-01-31", periods=n, freq="ME")
    rng = np.random.default_rng(0)
    # Nearly independent columns: one much higher vol — MD concentrates on the high-vol name.
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.35, n),
            "B": rng.normal(0.0, 0.025, n),
            "C": rng.normal(0.0, 0.025, n),
        },
        index=dates,
    )
    cfg = _minimal_portfolio_config(["A", "B", "C"], max_w=0.15, min_w=0.01)
    end = dates[-1].strftime("%Y-%m-%d")
    u_res = build_maximum_diversification_unconstrained(cfg, returns, end, n)
    assert u_res.status in ("OK", "APPROXIMATE")
    mx = max(u_res.weights[t] for t in ("A", "B", "C"))
    assert mx > 0.15 + 1e-4


def test_maximum_diversification_unconstrained_import_run_script() -> None:
    import run_maximum_diversification_unconstrained as rmd_u

    assert callable(rmd_u.main)
