from __future__ import annotations

import numpy as np
import pytest

from src.risk_budgeting import (
    normalize_budget_map,
    pc_from_w,
    resolve_class_risk_targets,
    risk_budget_bucket_from_row,
    solve_asset_risk_budget_spinu,
    solve_class_risk_budget_slsqp,
)
from src.risk_budgeting_presets import RISK_BUDGET_PRESETS, RISK_BUDGET_BUCKET_KEYS


def test_all_presets_sum_to_one() -> None:
    for name, table in RISK_BUDGET_PRESETS.items():
        s = sum(table.values())
        assert abs(s - 1.0) < 1e-9, name
        for k in RISK_BUDGET_BUCKET_KEYS:
            assert k in table


def test_manual_override_replaces_preset() -> None:
    targets, preset, manual, _ = resolve_class_risk_targets(
        {
            "preset": "defensive",
            "targets": {"equity": 0.5, "fixed_income": 0.5},
        }
    )
    assert manual is True
    assert targets["equity"] == 0.5
    assert preset == "defensive"


def test_slsqp_class_long_only_sums_to_one() -> None:
    rng = np.random.default_rng(42)
    n = 4
    x = rng.standard_normal((n, n))
    cov = x @ x.T / n + np.eye(n) * 0.1
    # 2 assets bucket 0, 2 assets bucket 1
    bi = np.array([0, 0, 1, 1], dtype=int)
    b = np.array([0.6, 0.4], dtype=float)
    w, diag = solve_class_risk_budget_slsqp(cov, bi, b)
    assert w.shape == (n,)
    assert np.all(w >= -1e-8)
    assert abs(w.sum() - 1.0) < 1e-6
    assert diag.get("solver_status") in ("OK", "APPROXIMATE")


def test_class_realized_near_target_diagonal() -> None:
    """Perfect decoupling: one asset per bucket on diagonal cov -> exact PC match equal weights scaled."""
    cov = np.diag([0.04, 0.09, 0.01])
    n = 3
    bi = np.array([0, 1, 2], dtype=int)
    b = np.array([1 / 3, 1 / 3, 1 / 3], dtype=float)
    w, diag = solve_class_risk_budget_slsqp(cov, bi, b, tol=1e-12)
    pc = pc_from_w(w, cov)
    assert abs(pc.sum() - 1.0) < 1e-5
    r = np.array(
        [float(pc[bi == k].sum()) for k in range(3)],
        dtype=float,
    )
    assert np.max(np.abs(r - b)) < 0.05


def test_spinu_non_equal_budget() -> None:
    n = 3
    cov = np.eye(n) * 0.01
    b = np.array([0.5, 0.3, 0.2], dtype=float)
    w, diag = solve_asset_risk_budget_spinu(cov, b, spinu_max_iter=20_000)
    assert abs(w.sum() - 1.0) < 1e-5
    assert np.all(w > 0)
    pc = pc_from_w(w, cov)
    assert float(np.max(np.abs(pc - b))) < 0.05


def test_bucket_mapping_tips_and_equity() -> None:
    assert risk_budget_bucket_from_row({"asset_class": "equity", "subtype": "broad_market"}) == "equity"
    assert (
        risk_budget_bucket_from_row({"asset_class": "fixed_income", "subtype": "tips"})
        == "inflation_linked"
    )
    assert risk_budget_bucket_from_row({"asset_class": "alternative", "subtype": "reit"}) == "real_assets"
    assert risk_budget_bucket_from_row(None) == "unknown"


def test_normalize_budget_map_rejects_negative() -> None:
    with pytest.raises(ValueError):
        normalize_budget_map({"a": 0.5, "b": -0.5})


def test_unused_bucket_detection_path() -> None:
    """SLSQP is defined when K matches b; degenerate grouping still runs."""
    n = 4
    cov = np.eye(n) * 0.01
    bi = np.zeros(n, dtype=int)
    b = np.array([1.0], dtype=float)
    w, diag = solve_class_risk_budget_slsqp(cov, bi, b)
    assert abs(w.sum() - 1.0) < 1e-5


def test_build_asset_class_baseline_fails_without_two_assets() -> None:
    from src.portfolio_variants import build_risk_budget_by_asset_class_baseline
    from src.config_schema import PortfolioConfig

    cfg = PortfolioConfig(
        investor_currency="USD",
        initial_investable_amount=1000,
        liquidity_need=0,
        liquidity_need_months=0,
        monthly_expenses=0,
        portfolio_value=None,
        cash_policy="allowed_for_scaling",
        tickers=["A"],
        weights={},
        benchmark_base_ticker="SPY",
        rf_source=None,
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
        N_rc=3,
        donor_shift_mode="proportional",
        windows_months=[120],
        coverage_threshold=0.9,
        output_dir="results_csv",
        output_dir_final="Main portfolio",
        risk_budgeting={"preset": "balanced"},
    )
    import pandas as pd

    ret = pd.DataFrame({"A": [0.01, -0.02, 0.03]}, index=pd.date_range("2020-01-31", periods=3, freq="ME"))
    res = build_risk_budget_by_asset_class_baseline(cfg, ret, "2020-03-31", 120)
    assert res.status == "FAIL_INFEASIBLE_UNIVERSE"


def test_build_asset_baseline_requires_asset_targets() -> None:
    from src.portfolio_variants import build_risk_budget_by_asset_baseline
    from src.config_schema import PortfolioConfig

    cfg = PortfolioConfig(
        investor_currency="USD",
        initial_investable_amount=1000,
        liquidity_need=0,
        liquidity_need_months=0,
        monthly_expenses=0,
        portfolio_value=None,
        cash_policy="allowed_for_scaling",
        tickers=["A", "B"],
        weights={},
        benchmark_base_ticker="SPY",
        rf_source=None,
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
        N_rc=3,
        donor_shift_mode="proportional",
        windows_months=[120],
        coverage_threshold=0.0,
        output_dir="results_csv",
        output_dir_final="Main portfolio",
        risk_budgeting={"preset": "balanced", "asset_targets": {}},
    )
    import pandas as pd

    ret = pd.DataFrame(
        {"A": [0.01] * 50, "B": [0.02] * 50},
        index=pd.date_range("2016-01-31", periods=50, freq="ME"),
    )
    res = build_risk_budget_by_asset_baseline(cfg, ret, "2019-12-31", 120)
    assert res.status == "FAIL_CONFIG"
