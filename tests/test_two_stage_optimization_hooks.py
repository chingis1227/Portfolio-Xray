from __future__ import annotations

import numpy as np
import pandas as pd

from src.optimization import (
    OBJECTIVE_MODE_MAX_RETURN,
    OBJECTIVE_MODE_RISK_PARITY,
    OBJECTIVE_MODE_RISK_SKELETON,
    rc_by_asset_from_weights,
    run_risk_budget_optimization,
)
from src.risk_contrib import cov_matrix_monthly


def _tiny_universe_returns() -> pd.DataFrame:
    dates = pd.date_range("2020-01-31", periods=24, freq="ME")
    rng = np.random.default_rng(42)
    data = {
        "VOO": rng.normal(0.01, 0.04, len(dates)),
        "BND": rng.normal(0.003, 0.01, len(dates)),
        "GLD": rng.normal(0.005, 0.03, len(dates)),
    }
    return pd.DataFrame(data, index=dates)


def _blocks():
    return {
        "Growth": ["VOO"],
        "Duration": ["BND"],
        "Inflation": ["GLD"],
        "Growth_HY": [],
        "Growth_EM_debt": [],
        "Liquidity": [],
        "Tail": [],
    }


def _equal_rc_dev_sq(wdict: dict, cov_df: pd.DataFrame, tickers: list[str]) -> float:
    """Sum_i (RC_i - 1/n)^2 for RC_vol on tickers."""
    rc = rc_by_asset_from_weights(wdict, cov_df)
    n = len(tickers)
    target = 1.0 / n
    return float(sum((rc.get(t, 0.0) - target) ** 2 for t in tickers))


def _hhi_rc_vol(wdict: dict, cov_df: pd.DataFrame, tickers: list[str]) -> float:
    """Herfindahl of RC_vol shares: sum RC_i^2."""
    rc = rc_by_asset_from_weights(wdict, cov_df)
    return float(sum(float(rc.get(t, 0.0)) ** 2 for t in tickers))


def test_invalid_objective_mode_falls_back_and_status_tagged():
    returns_df = _tiny_universe_returns()
    blocks = _blocks()
    rc = {"Growth": 0.55, "Duration": 0.30, "Inflation": 0.15}
    _, status = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc,
        growth_core_candidates=["VOO"],
        window_months=24,
        rb_search_enabled=False,
        objective_mode="not_a_mode",
    )
    assert "OBJECTIVE_MODE_INVALID" in status
    assert "OBJECTIVE_MODE=max_return" in status


def test_risk_parity_mode_runs_and_reports_mode():
    returns_df = _tiny_universe_returns()
    blocks = _blocks()
    rc = {"Growth": 0.55, "Duration": 0.30, "Inflation": 0.15}
    w, status = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc,
        growth_core_candidates=["VOO"],
        window_months=24,
        rb_search_enabled=False,
        objective_mode=OBJECTIVE_MODE_RISK_PARITY,
    )
    assert w
    assert abs(sum(w.values()) - 1.0) < 1e-5
    assert "OBJECTIVE_MODE=risk_parity" in status


def test_risk_skeleton_mode_runs_and_skel_hhi_tagged():
    returns_df = _tiny_universe_returns()
    blocks = _blocks()
    rc = {"Growth": 0.55, "Duration": 0.30, "Inflation": 0.15}
    _, status = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc,
        growth_core_candidates=["VOO"],
        window_months=24,
        rb_search_enabled=False,
        objective_mode=OBJECTIVE_MODE_RISK_SKELETON,
        risk_skeleton_concentration_lambda=10.0,
    )
    assert "OBJECTIVE_MODE=risk_skeleton" in status
    assert "SKEL_HHI_LAMBDA=" in status


def test_risk_skeleton_lower_or_equal_hhi_rc_than_max_return():
    """Skeleton minimizes HHI(RC) among feasible; should be <= max-return solution on same toy."""
    returns_df = _tiny_universe_returns()
    blocks = _blocks()
    rc = {"Growth": 0.55, "Duration": 0.30, "Inflation": 0.15}
    ret_w = returns_df[["VOO", "BND", "GLD"]].dropna(how="any")
    cov_df = cov_matrix_monthly(ret_w, ddof=1, use_shrinkage=False)
    tickers = ["VOO", "BND", "GLD"]

    w_sk, _ = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc,
        growth_core_candidates=["VOO"],
        window_months=24,
        rb_search_enabled=False,
        objective_mode=OBJECTIVE_MODE_RISK_SKELETON,
        risk_skeleton_concentration_lambda=15.0,
    )
    w_mr, _ = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc,
        growth_core_candidates=["VOO"],
        window_months=24,
        rb_search_enabled=False,
        objective_mode=OBJECTIVE_MODE_MAX_RETURN,
    )
    h_sk = _hhi_rc_vol(w_sk, cov_df, tickers)
    h_mr = _hhi_rc_vol(w_mr, cov_df, tickers)
    assert h_sk <= h_mr + 1e-6


def test_risk_parity_lower_equal_rc_deviation_than_max_return():
    returns_df = _tiny_universe_returns()
    blocks = _blocks()
    rc = {"Growth": 0.55, "Duration": 0.30, "Inflation": 0.15}
    ret_w = returns_df[["VOO", "BND", "GLD"]].dropna(how="any")
    cov_df = cov_matrix_monthly(ret_w, ddof=1, use_shrinkage=False)
    tickers = ["VOO", "BND", "GLD"]

    w_rp, _ = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc,
        growth_core_candidates=["VOO"],
        window_months=24,
        rb_search_enabled=False,
        objective_mode=OBJECTIVE_MODE_RISK_PARITY,
    )
    w_mr, _ = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc,
        growth_core_candidates=["VOO"],
        window_months=24,
        rb_search_enabled=False,
        objective_mode=OBJECTIVE_MODE_MAX_RETURN,
    )
    d_rp = _equal_rc_dev_sq(w_rp, cov_df, tickers)
    d_mr = _equal_rc_dev_sq(w_mr, cov_df, tickers)
    assert d_rp <= d_mr + 1e-8


def test_soft_profile_penalties_in_status_when_enabled():
    returns_df = _tiny_universe_returns()
    blocks = _blocks()
    rc = {"Growth": 0.55, "Duration": 0.30, "Inflation": 0.15}
    _, status = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc,
        growth_core_candidates=["VOO"],
        window_months=24,
        rb_search_enabled=False,
        objective_mode=OBJECTIVE_MODE_MAX_RETURN,
        soft_target_vol_annual=0.10,
        soft_vol_penalty_lambda=5.0,
        soft_target_return_annual=0.07,
        soft_return_penalty_lambda=3.0,
    )
    assert "SOFT_VOL_TARGET=" in status
    assert "SOFT_RET_TARGET=" in status


def test_warm_start_with_high_tracking_stays_near_skeleton():
    returns_df = _tiny_universe_returns()
    blocks = _blocks()
    rc = {"Growth": 0.55, "Duration": 0.30, "Inflation": 0.15}
    w1, _ = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc,
        growth_core_candidates=["VOO"],
        window_months=24,
        rb_search_enabled=False,
        objective_mode=OBJECTIVE_MODE_RISK_SKELETON,
        risk_skeleton_concentration_lambda=10.0,
    )
    w2, st2 = run_risk_budget_optimization(
        returns_df=returns_df,
        blocks=blocks,
        rc_block_targets=rc,
        growth_core_candidates=["VOO"],
        window_months=24,
        rb_search_enabled=False,
        objective_mode=OBJECTIVE_MODE_MAX_RETURN,
        warm_start_weights=w1,
        skeleton_tracking_lambda=2000.0,
    )
    tickers = ["VOO", "BND", "GLD"]
    diffs = [abs(float(w2.get(t, 0.0) - w1.get(t, 0.0))) for t in tickers]
    assert max(diffs) < 0.08
    assert "WARM_START=on" in st2
    assert "SKEL_TRACK_LAMBDA" in st2
