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
    L1_REFERENCE_CURRENT_PORTFOLIO,
    MV_BASELINE_ROLE_ADVANCED_CONTROLS_PURE_PATH,
    MV_BASELINE_ROLE_PRIMARY_LOWEST_VOL_UNDER_CONSTRAINTS,
    MV_BASELINE_ROLE_REBALANCE_AWARE_TURNOVER_CONTROLLED,
    build_equal_weight_baseline,
    build_minimum_variance_advanced_controls,
    build_minimum_variance_baseline,
    build_minimum_variance_constrained,
    build_minimum_variance_uncapped_long_only,
    minimum_variance_baseline_metadata_export,
)
from src.risk_contrib import cov_matrix_monthly
from src.risk_parity_spinu import repair_covariance_psd


def _minimal_portfolio_config(
    tickers: list[str],
    *,
    min_w: float | None = None,
    max_w: float | None = None,
    target_vol_annual: float | None = None,
    minimum_variance_turnover_lambda: float = 0.0,
    minimum_variance_l1_experimental: bool = False,
    covariance_shrinkage: bool = False,
    weights: dict[str, float] | None = None,
) -> PortfolioConfig:
    n = len(tickers)
    eq = 1.0 / n if n else 0.0
    wdict = weights if weights is not None else {t: eq for t in tickers}
    return PortfolioConfig(
        investor_currency="USD",
        initial_investable_amount=100_000.0,
        liquidity_need=0.0,
        liquidity_need_months=6.0,
        monthly_expenses=0.0,
        portfolio_value=100_000.0,
        cash_policy="allowed_for_scaling",
        tickers=list(tickers),
        weights=wdict,
        benchmark_base_ticker="VOO",
        rf_source="FRED:DTB3",
        cash_proxy_ticker="BIL",
        local_benchmark_map=None,
        allow_leverage=False,
        allow_short_selling=False,
        min_acceptable_return=None,
        target_nominal_return_annual=None,
        target_vol_annual=target_vol_annual,
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
        covariance_shrinkage=covariance_shrinkage,
        minimum_variance_turnover_lambda=minimum_variance_turnover_lambda,
        minimum_variance_l1_experimental=minimum_variance_l1_experimental,
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
    res = build_minimum_variance_constrained(cfg, returns, end, 120)
    assert res.status in ("OK", "APPROXIMATE")
    s = sum(res.weights.values())
    assert abs(s - 1.0) < 1e-4
    for t in ("H", "M", "L"):
        assert res.weights[t] >= 0.0
        assert 0.01 - 1e-6 <= res.weights[t] <= 0.40 + 1e-3  # feasibility cap for N=3
    diag = res.diagnostics
    assert diag.get("optimizer_name") == "minimum_variance_constrained"
    assert diag.get("minimum_variance_baseline_role") == MV_BASELINE_ROLE_PRIMARY_LOWEST_VOL_UNDER_CONSTRAINTS
    assert "primary" in str(diag.get("minimum_variance_interpretation") or "").lower()
    assert diag.get("solver") == "SLSQP"
    assert diag.get("covariance_method") == "sample_monthly_ddof1"
    assert diag.get("shrinkage_used") is False
    assert diag.get("portfolio_variance") is not None
    assert diag.get("annualized_volatility") is not None
    assert "solver_success" in diag
    meta = minimum_variance_baseline_metadata_export(diag)
    orm = meta["optimizer_run_metadata"]
    assert orm["schema_version"] == "candidate_optimizer_run_metadata_v1"
    assert orm["optimizer_role"] == "candidate_only"
    assert orm["method_id"] == "minimum_variance_constrained"
    assert orm["input_window"]["analysis_end"] == end
    assert orm["input_window"]["window_months"] == 120
    assert orm["input_window"]["return_frequency"] == "monthly_simple"
    assert orm["input_window"]["returns_panel_end"] == end
    assert orm["input_window"]["returns_panel_rows"] == 120
    assert len(orm["input_fingerprints"]["returns_panel_fingerprint"]) == 64
    assert len(orm["input_fingerprints"]["config_fingerprint"]) == 64
    assert len(orm["input_fingerprints"]["universe_fingerprint"]) == 64
    assert orm["covariance"]["analysis_end"] == end
    assert orm["covariance"]["returns_panel_fingerprint"] == (
        orm["input_fingerprints"]["returns_panel_fingerprint"]
    )
    assert orm["covariance"]["methodology"]["schema_version"] == "optimizer_covariance_methodology_v1"
    assert orm["covariance"]["methodology"]["join_policy"] == "inner_join_complete_cases"
    assert orm["young_etf_methodology"]["enabled"] is False
    assert "Covariance method=sample_monthly_ddof1" in orm["covariance"]["methodology_summary"]
    assert orm["expected_return"]["uses_expected_returns"] is False
    assert orm["constraints"]["bounds_used"]["H"]["min"] == 0.01
    assert orm["solver"]["optimization_quality_status"] in {
        "clean_solve",
        "approximate_fallback",
    }


def test_minimum_variance_baseline_alias_matches_constrained() -> None:
    rng = np.random.default_rng(99)
    dates = pd.date_range("2016-01-31", periods=60, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.02, n),
            "B": rng.normal(0.0, 0.03, n),
            "C": rng.normal(0.0, 0.04, n),
        },
        index=dates,
    )
    cfg = _minimal_portfolio_config(["A", "B", "C"], max_w=0.35)
    end = dates[-1].strftime("%Y-%m-%d")
    w1 = build_minimum_variance_baseline(cfg, returns, end, 60)
    w2 = build_minimum_variance_constrained(cfg, returns, end, 60)
    assert w1.status == w2.status
    assert abs(w1.weights["A"] - w2.weights["A"]) < 1e-9


def test_minimum_variance_uncapped_can_exceed_config_max_weight() -> None:
    """Uncapped variant ignores project max_single_security_weight_pct."""
    rng = np.random.default_rng(5)
    dates = pd.date_range("2014-06-30", periods=100, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "H": rng.normal(0.002, 0.06, n),
            "M": rng.normal(0.002, 0.03, n),
            "L": rng.normal(0.002, 0.008, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    # Feasible intersection with default min weight (0.01): need sum(max) >= 1.
    cfg_tight = _minimal_portfolio_config(["H", "M", "L"], max_w=0.40)
    c = build_minimum_variance_constrained(cfg_tight, returns, end, len(dates))
    u = build_minimum_variance_uncapped_long_only(cfg_tight, returns, end, len(dates))
    assert c.status in ("OK", "APPROXIMATE")
    assert u.status in ("OK", "APPROXIMATE")
    assert max(c.weights.values()) <= 0.40 + 1e-3
    assert max(u.weights.values()) > 0.40 + 1e-3
    assert u.diagnostics.get("optimizer_name") == "minimum_variance_uncapped_long_only"
    cu = u.diagnostics.get("constraints_used") or []
    assert "long_only" in cu
    s = sum(u.weights.values())
    assert abs(s - 1.0) < 1e-3
    for w in u.weights.values():
        assert w >= -1e-9


def test_minimum_variance_advanced_reference_and_l1_moves_weights() -> None:
    rng = np.random.default_rng(11)
    dates = pd.date_range("2013-01-31", periods=120, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.05, n),
            "B": rng.normal(0.0, 0.03, n),
            "C": rng.normal(0.0, 0.04, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    w0 = {"A": 0.5, "B": 0.35, "C": 0.15}
    cfg = _minimal_portfolio_config(
        ["A", "B", "C"],
        max_w=0.45,
        target_vol_annual=None,
        minimum_variance_turnover_lambda=0.25,
        covariance_shrinkage=True,
        weights=w0,
    )
    base = build_minimum_variance_constrained(cfg, returns, end, 120)
    adv = build_minimum_variance_advanced_controls(cfg, returns, end, 120)
    assert base.status in ("OK", "APPROXIMATE")
    assert adv.status in ("OK", "APPROXIMATE")
    assert adv.diagnostics.get("l1_reference_source") == L1_REFERENCE_CURRENT_PORTFOLIO
    assert adv.diagnostics.get("reference_allocation_source") is None
    assert adv.diagnostics.get("current_portfolio_weights_available") is True
    assert adv.diagnostics.get("l1_penalty_used") is True
    assert adv.diagnostics.get("minimum_variance_baseline_role") == (
        MV_BASELINE_ROLE_REBALANCE_AWARE_TURNOVER_CONTROLLED
    )
    assert "rebalance-aware" in str(
        adv.diagnostics.get("minimum_variance_interpretation") or ""
    ).lower()
    assert float(adv.diagnostics.get("lambda_turnover_effective") or 0.0) > 0.0
    assert adv.diagnostics.get("shrinkage_used") is True
    w_cols = ["A", "B", "C"]
    diff = sum(abs(adv.weights[t] - base.weights[t]) for t in w_cols)
    assert diff > 0.005
    w_cur = np.array([w0[t] for t in w_cols], dtype=float)
    turn = float(np.sum(np.abs(np.array([adv.weights[t] for t in w_cols]) - w_cur)))
    assert abs(float(adv.diagnostics.get("l1_distance_to_current_portfolio") or -1.0) - turn) < 1e-5
    assert adv.diagnostics.get("l1_disabled_reason") is None
    assert "equal_weight" not in str(adv.diagnostics).lower()


def test_minimum_variance_advanced_l1_active_without_legacy_experimental_flag() -> None:
    rng = np.random.default_rng(101)
    dates = pd.date_range("2012-01-31", periods=100, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.04, n),
            "B": rng.normal(0.0, 0.035, n),
            "C": rng.normal(0.0, 0.03, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(
        ["A", "B", "C"],
        max_w=0.45,
        minimum_variance_turnover_lambda=0.1,
        minimum_variance_l1_experimental=False,
        covariance_shrinkage=True,
        weights={"A": 0.55, "B": 0.30, "C": 0.15},
    )
    adv = build_minimum_variance_advanced_controls(cfg, returns, end, len(dates))
    assert adv.status in ("OK", "APPROXIMATE")
    assert adv.diagnostics.get("l1_penalty_used") is True
    assert adv.diagnostics.get("minimum_variance_baseline_role") == (
        MV_BASELINE_ROLE_REBALANCE_AWARE_TURNOVER_CONTROLLED
    )
    assert adv.diagnostics.get("l1_reference_source") == L1_REFERENCE_CURRENT_PORTFOLIO
    assert adv.diagnostics.get("lambda_turnover_effective") == 0.1


def test_minimum_variance_advanced_matches_constrained_without_vol_cap_or_l1() -> None:
    rng = np.random.default_rng(31)
    dates = pd.date_range("2012-06-30", periods=90, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.04, n),
            "B": rng.normal(0.0, 0.03, n),
            "C": rng.normal(0.0, 0.035, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(
        ["A", "B", "C"],
        max_w=0.40,
        target_vol_annual=None,
        minimum_variance_turnover_lambda=0.0,
        covariance_shrinkage=True,
    )
    base = build_minimum_variance_constrained(cfg, returns, end, len(dates))
    adv = build_minimum_variance_advanced_controls(cfg, returns, end, len(dates))
    assert base.status in ("OK", "APPROXIMATE")
    assert adv.status in ("OK", "APPROXIMATE")
    assert base.diagnostics.get("minimum_variance_baseline_role") == (
        MV_BASELINE_ROLE_PRIMARY_LOWEST_VOL_UNDER_CONSTRAINTS
    )
    assert adv.diagnostics.get("minimum_variance_baseline_role") == (
        MV_BASELINE_ROLE_ADVANCED_CONTROLS_PURE_PATH
    )
    assert adv.diagnostics.get("l1_penalty_used") is False
    assert adv.diagnostics.get("lambda_turnover_effective") == 0.0
    assert adv.diagnostics.get("l1_reference_source") is None
    dr = str(adv.diagnostics.get("l1_disabled_reason") or "")
    assert "lambda" in dr.lower()
    assert adv.diagnostics.get("shrinkage_used") is True
    for t in ("A", "B", "C"):
        assert abs(base.weights[t] - adv.weights[t]) < 1e-8


def test_minimum_variance_advanced_default_lambda_zero_is_pure_min_var_no_l1() -> None:
    """Schema default λ=0: no L1 term; same as constrained when Σ path aligned (LW + same bounds)."""
    rng = np.random.default_rng(77)
    dates = pd.date_range("2015-03-31", periods=80, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.04, n),
            "B": rng.normal(0.0, 0.03, n),
            "C": rng.normal(0.0, 0.035, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(
        ["A", "B", "C"],
        max_w=0.42,
        covariance_shrinkage=True,
    )
    assert cfg.minimum_variance_turnover_lambda == 0.0
    adv = build_minimum_variance_advanced_controls(cfg, returns, end, len(dates))
    assert adv.status in ("OK", "APPROXIMATE")
    assert adv.diagnostics.get("lambda_turnover") == 0.0
    assert adv.diagnostics.get("lambda_turnover_effective") == 0.0
    assert adv.diagnostics.get("l1_penalty_used") is False
    assert adv.diagnostics.get("minimum_variance_baseline_role") == (
        MV_BASELINE_ROLE_ADVANCED_CONTROLS_PURE_PATH
    )
    assert adv.diagnostics.get("l1_reference_source") is None
    dr = str(adv.diagnostics.get("l1_disabled_reason") or "")
    assert "lambda" in dr.lower()


def test_minimum_variance_advanced_infeasible_vol_target() -> None:
    rng = np.random.default_rng(3)
    dates = pd.date_range("2015-01-31", periods=96, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.01, 0.08, n),
            "B": rng.normal(0.008, 0.07, n),
            "C": rng.normal(0.009, 0.075, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(
        ["A", "B", "C"],
        max_w=None,
        min_w=None,
        target_vol_annual=0.01,
    )
    res = build_minimum_variance_advanced_controls(cfg, returns, end, len(dates))
    assert res.status == "FAIL_INFEASIBLE_VOL_TARGET"
    assert res.diagnostics.get("volatility_constraint_feasible") is False
    assert "Infeasible volatility target" in str(res.diagnostics.get("reason", ""))


def test_minimum_variance_advanced_vol_feasible_respected() -> None:
    rng = np.random.default_rng(2)
    dates = pd.date_range("2014-01-31", periods=100, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.02, n),
            "B": rng.normal(0.0, 0.02, n),
            "C": rng.normal(0.0, 0.02, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(["A", "B", "C"], target_vol_annual=0.50)
    res = build_minimum_variance_advanced_controls(cfg, returns, end, len(dates))
    assert res.status in ("OK", "APPROXIMATE")
    assert res.diagnostics.get("volatility_target_used") is True
    var_m = float(res.diagnostics.get("portfolio_variance") or 0.0)
    v_cap = (0.50 / np.sqrt(12.0)) ** 2
    assert var_m <= v_cap + 1e-7


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


def test_minimum_variance_advanced_disables_l1_when_no_positive_current_weights() -> None:
    rng = np.random.default_rng(22)
    dates = pd.date_range("2013-01-31", periods=60, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.03, n),
            "B": rng.normal(0.0, 0.03, n),
            "C": rng.normal(0.0, 0.03, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(
        ["A", "B", "C"],
        minimum_variance_turnover_lambda=0.5,
        weights={"A": 0.0, "B": 0.0, "C": 0.0},
        covariance_shrinkage=True,
    )
    adv = build_minimum_variance_advanced_controls(cfg, returns, end, 60)
    assert adv.status in ("OK", "APPROXIMATE")
    assert adv.diagnostics.get("l1_penalty_used") is False
    assert adv.diagnostics.get("lambda_turnover_effective") == 0.0
    assert adv.diagnostics.get("l1_reference_source") is None
    assert adv.diagnostics.get("l1_disabled_reason")


def test_minimum_variance_advanced_forces_ledoit_even_if_config_shrinkage_false() -> None:
    rng = np.random.default_rng(44)
    dates = pd.date_range("2014-01-31", periods=72, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0, 0.04, n),
            "B": rng.normal(0.0, 0.035, n),
            "C": rng.normal(0.0, 0.03, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(["A", "B", "C"], covariance_shrinkage=False)
    adv = build_minimum_variance_advanced_controls(cfg, returns, end, len(dates))
    assert adv.status in ("OK", "APPROXIMATE")
    assert adv.diagnostics.get("shrinkage_used") is True


def test_minimum_variance_import_run_scripts() -> None:
    import run_minimum_variance as rmv
    import run_minimum_variance_advanced as rmd
    import run_minimum_variance_uncapped as rmu

    assert callable(rmv.main)
    assert callable(rmu.main)
    assert callable(rmd.main)
