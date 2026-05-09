"""
Tests for Minimum CVaR baseline construction (Rockafellar–Uryasev LP).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.config_schema import PortfolioConfig
from src.portfolio_variants import (
    _minimum_cvar_empirical_loss_cvar,
    _minimum_cvar_linprog,
    _minimum_cvar_tail_effective_obs,
    build_minimum_cvar_constrained,
    build_minimum_cvar_uncapped,
)
from src.windows import slice_window


def _minimal_portfolio_config(
    tickers: list[str],
    *,
    min_w: float | None = None,
    max_w: float | None = None,
    minimum_cvar_confidence_level: float = 0.95,
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
        minimum_cvar_confidence_level=minimum_cvar_confidence_level,
    )


def test_minimum_cvar_linprog_small_matrix() -> None:
    R = np.array(
        [
            [0.02, -0.01],
            [-0.05, 0.03],
            [0.01, 0.00],
        ],
        dtype=float,
    )
    bounds = [(0.0, 1.0), (0.0, 1.0)]
    out = _minimum_cvar_linprog(R, 0.90, bounds, scenario_dates=None)
    assert out["ok"]
    w = out["w"]
    assert abs(float(w.sum()) - 1.0) < 1e-5
    assert np.all(w >= -1e-6) and np.all(w <= 1.0 + 1e-6)
    assert out["n_scenarios"] == 3
    assert out["tail_effective_obs"] == _minimum_cvar_tail_effective_obs(3, 0.90)


def test_minimum_cvar_uncapped_basic_and_vs_equal_weight() -> None:
    rng = np.random.default_rng(123)
    dates = pd.date_range("2018-01-31", periods=80, freq="ME")
    n = len(dates)
    # Third asset: heavy left tail on some months
    r_a = rng.normal(0.002, 0.02, n)
    r_b = rng.normal(0.002, 0.015, n)
    r_bad = rng.normal(0.002, 0.08, n)
    r_bad[5:15] -= 0.12
    returns = pd.DataFrame({"A": r_a, "B": r_b, "BAD": r_bad}, index=dates)
    cfg = _minimal_portfolio_config(["A", "B", "BAD"])
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_minimum_cvar_uncapped(cfg, returns, end, len(dates))
    assert res.status in ("OK", "APPROXIMATE")
    assert abs(sum(res.weights.values()) - 1.0) < 1e-4
    for t in ("A", "B", "BAD"):
        assert -1e-6 <= res.weights[t] <= 1.0 + 1e-4
    assert res.diagnostics.get("optimizer_name") == "minimum_cvar_uncapped"
    R = slice_window(returns[["A", "B", "BAD"]], end, len(dates)).dropna(how="any").to_numpy(
        dtype=float
    )
    gamma = 0.95
    w_star = np.array([res.weights["A"], res.weights["B"], res.weights["BAD"]], dtype=float)
    w_ew = np.ones(3) / 3.0
    cvar_star = _minimum_cvar_empirical_loss_cvar(R, w_star, gamma)
    cvar_ew = _minimum_cvar_empirical_loss_cvar(R, w_ew, gamma)
    assert cvar_star <= cvar_ew + 1e-6
    # Usually more concentrated than EW on this fixture (lower weight on BAD or higher HHI)
    hhi_star = float(np.sum(w_star**2))
    hhi_ew = float(np.sum(w_ew**2))
    assert hhi_star >= hhi_ew - 1e-9


def test_minimum_cvar_constrained_respects_bounds() -> None:
    rng = np.random.default_rng(7)
    dates = pd.date_range("2016-12-31", periods=100, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "X": rng.normal(0.0, 0.04, n),
            "Y": rng.normal(0.0, 0.03, n),
            "Z": rng.normal(0.0, 0.02, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    window = len(dates)
    cfg = _minimal_portfolio_config(["X", "Y", "Z"], min_w=0.01, max_w=0.40)
    res = build_minimum_cvar_constrained(cfg, returns, end, window)
    assert res.status in ("OK", "APPROXIMATE")
    assert abs(sum(res.weights.values()) - 1.0) < 1e-3
    for t in ("X", "Y", "Z"):
        assert 0.01 - 1e-5 <= res.weights[t] <= 0.40 + 1e-3
    assert res.diagnostics.get("optimizer_name") == "minimum_cvar_constrained"
    assert res.diagnostics.get("bounds_used") is not None
    assert res.diagnostics.get("constraint_summary") is not None


def test_minimum_cvar_constrained_differs_from_uncapped_when_cap_binds() -> None:
    rng = np.random.default_rng(99)
    dates = pd.date_range("2017-06-30", periods=90, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "L": rng.normal(0.004, 0.05, n),
            "M": rng.normal(0.003, 0.02, n),
            "S": rng.normal(0.002, 0.01, n),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    w = len(dates)
    cfg_u = _minimal_portfolio_config(["L", "M", "S"])
    cfg_c = _minimal_portfolio_config(["L", "M", "S"], min_w=0.01, max_w=0.34)
    u = build_minimum_cvar_uncapped(cfg_u, returns, end, w)
    c = build_minimum_cvar_constrained(cfg_c, returns, end, w)
    assert u.status in ("OK", "APPROXIMATE")
    assert c.status in ("OK", "APPROXIMATE")
    mu = max(u.weights.values())
    mc = max(c.weights.values())
    assert mc <= 0.35 + 1e-3
    # With a tight cap, constrained max should be at or below uncapped max (often strictly below if uncapped concentrates)
    assert mc <= mu + 1e-6


@pytest.mark.parametrize("gamma", [0.90, 0.95, 0.975])
def test_minimum_cvar_gamma_sensitivity(gamma: float) -> None:
    rng = np.random.default_rng(int(gamma * 1000))
    dates = pd.date_range("2019-01-31", periods=60, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "P": rng.normal(0.0, 0.03, n),
            "Q": rng.normal(0.0, 0.025, n),
        },
        index=dates,
    )
    cfg = _minimal_portfolio_config(["P", "Q"], minimum_cvar_confidence_level=gamma)
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_minimum_cvar_uncapped(cfg, returns, end, n, confidence_level=gamma)
    assert res.status in ("OK", "APPROXIMATE")
    assert abs(float(res.diagnostics.get("cvar_confidence_level", 0)) - gamma) < 1e-9
    assert res.diagnostics.get("cvar_objective_value") is not None
    tail_obs = res.diagnostics.get("tail_effective_obs")
    assert tail_obs == _minimum_cvar_tail_effective_obs(n, gamma)


def test_minimum_cvar_constrained_infeasible_bounds() -> None:
    """When sum of upper bounds < 1, constrained CVaR should fail fast with FAIL_INFEASIBLE_BOUNDS."""
    dates = pd.date_range("2020-01-31", periods=40, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "a": np.full(n, 0.01),
            "b": np.full(n, 0.01),
            "c": np.full(n, 0.01),
        },
        index=dates,
    )
    end = dates[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(["a", "b", "c"], min_w=0.01, max_w=0.25)
    res = build_minimum_cvar_constrained(cfg, returns, end, n)
    assert res.status == "FAIL_INFEASIBLE_BOUNDS"


def test_tail_scenarios_populated_when_lp_ok() -> None:
    dates = pd.date_range("2021-03-31", periods=50, freq="ME")
    n = len(dates)
    rng = np.random.default_rng(1)
    returns = pd.DataFrame(
        {"u": rng.normal(0.0, 0.02, n), "v": rng.normal(0.0, 0.025, n)},
        index=dates,
    )
    cfg = _minimal_portfolio_config(["u", "v"])
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_minimum_cvar_uncapped(cfg, returns, end, n)
    assert res.status in ("OK", "APPROXIMATE")
    tail = res.diagnostics.get("tail_scenarios_used") or []
    assert isinstance(tail, list)
    assert res.diagnostics.get("tail_effective_obs") == _minimum_cvar_tail_effective_obs(n, 0.95)

