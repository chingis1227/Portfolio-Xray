"""
Tests for Robust Mean–Variance baselines (James–Stein mu, LW/OAS Sigma, SLSQP).
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
    build_robust_mean_variance_constrained,
    build_robust_mean_variance_uncapped,
)
from src.robust_mv import (
    james_stein_shrink_means,
    shrunk_covariance_monthly,
    solve_robust_mean_variance,
)


def _minimal_cfg(
    tickers: list[str],
    *,
    min_w: float | None = None,
    max_w: float | None = None,
    lam: float | None = 0.0,
    cov_method: str = "ledoit_wolf",
    young_enabled: bool = False,
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
        young_etf_optimization_policy={"enabled": young_enabled},
        robust_mv_lambda=(None if lam is None else float(lam)),
        robust_mv_covariance_method=cov_method,
        robust_mv_mu_shrinkage_method="james_stein",
    )


def test_james_stein_shrinks_toward_grand_mean() -> None:
    rng = np.random.default_rng(0)
    dates = pd.date_range("2018-01-31", periods=60, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.02, 0.05, n),
            "B": rng.normal(0.001, 0.04, n),
            "C": rng.normal(-0.005, 0.03, n),
        },
        index=dates,
    ).dropna(how="any")
    out = james_stein_shrink_means(returns)
    raw = out["raw_mu"]
    shrunk = out["shrunk_mu"]
    gm = float(raw.mean())
    assert 0.0 <= float(out["shrinkage_intensity"]) <= 1.0
    dist_raw = float(np.sum((raw.values - gm) ** 2))
    dist_shr = float(np.sum((shrunk.values - gm) ** 2))
    assert dist_shr <= dist_raw + 1e-10


def test_james_stein_single_asset_no_crash() -> None:
    dates = pd.date_range("2020-01-31", periods=24, freq="ME")
    returns = pd.DataFrame({"X": np.linspace(-0.02, 0.02, len(dates))}, index=dates)
    out = james_stein_shrink_means(returns)
    assert out["shrinkage_intensity"] == 0.0
    np.testing.assert_allclose(out["raw_mu"].values, out["shrunk_mu"].values, rtol=1e-9)


def test_shrunk_covariance_ledoit_oas_psd_after_repair() -> None:
    rng = np.random.default_rng(3)
    dates = pd.date_range("2019-01-31", periods=80, freq="ME")
    n = len(dates)
    r = pd.DataFrame(
        {"a": rng.normal(0, 0.02, n), "b": rng.normal(0, 0.02, n)},
        index=dates,
    )
    for method in ("ledoit_wolf", "oas"):
        cov_df, meta = shrunk_covariance_monthly(r, method)
        assert meta["covariance_method"] in ("ledoit_wolf", "oas")
        assert np.all(np.isfinite(cov_df.values))
        evals = np.linalg.eigvalsh(cov_df.values)
        assert float(np.min(evals)) > -1e-8


def test_uncapped_weights_sum_one_long_only_lambda_zero_max_mu() -> None:
    dates = pd.date_range("2017-01-31", periods=100, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "LOW": np.full(n, -0.001),
            "MID": np.full(n, 0.0005),
            "HIGH": np.full(n, 0.004),
        },
        index=dates,
    )
    cfg = _minimal_cfg(["LOW", "MID", "HIGH"], lam=0.0)
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_robust_mean_variance_uncapped(cfg, returns, end, 100)
    assert res.status in ("OK", "APPROXIMATE")
    assert abs(sum(res.weights.values()) - 1.0) < 1e-4
    for t in cfg.tickers:
        assert 0.0 <= res.weights[t] <= 1.0 + 1e-6
    diag = res.diagnostics
    assert diag.get("optimizer_name") == "robust_mean_variance_uncapped"
    assert float(diag.get("robust_mv_lambda", -1)) == 0.0
    assert diag.get("raw_mu") and diag.get("shrunk_mu")
    assert diag.get("objective_value") is not None
    assert diag.get("psd_status") in ("psd", "repaired")
    # Highest shrunk mean should capture most weight when λ=0
    sm = diag["shrunk_mu"]
    best = max(sm, key=lambda k: sm[k])
    assert res.weights[best] >= 0.5


def test_uncapped_fails_config_when_robust_mv_lambda_unset() -> None:
    dates = pd.date_range("2017-01-31", periods=100, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "LOW": np.full(n, -0.001),
            "MID": np.full(n, 0.0005),
            "HIGH": np.full(n, 0.004),
        },
        index=dates,
    )
    cfg = _minimal_cfg(["LOW", "MID", "HIGH"], lam=None)
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_robust_mean_variance_uncapped(cfg, returns, end, 100)
    assert res.status == "FAIL_CONFIG"
    assert res.diagnostics.get("reason") and "robust_mv_lambda" in str(res.diagnostics["reason"])


def test_lambda_increases_variance_penalty_reduces_or_equal_variance() -> None:
    mu = np.array([0.01, 0.008, 0.006], dtype=float)
    cov = np.array(
        [[0.0010, 0.0003, 0.0002], [0.0003, 0.0009, 0.00025], [0.0002, 0.00025, 0.0008]],
        dtype=float,
    )
    cov = 0.5 * (cov + cov.T)
    bounds = [(0.0, 1.0)] * 3
    w0, _, _ = solve_robust_mean_variance(mu, cov, bounds, 0.05)
    w1, _, _ = solve_robust_mean_variance(mu, cov, bounds, 2.0)
    v0 = float(w0 @ cov @ w0)
    v1 = float(w1 @ cov @ w1)
    assert v1 <= v0 + 1e-6


def test_constrained_respects_max_weight_cap() -> None:
    rng = np.random.default_rng(11)
    dates = pd.date_range("2016-01-31", periods=120, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.004, 0.03, n),
            "B": rng.normal(0.003, 0.025, n),
            "C": rng.normal(0.0025, 0.02, n),
            "D": rng.normal(0.002, 0.018, n),
        },
        index=dates,
    )
    cap = 0.28
    cfg = _minimal_cfg(["A", "B", "C", "D"], max_w=cap, lam=0.15)
    end = dates[-1].strftime("%Y-%m-%d")
    unc = build_robust_mean_variance_uncapped(cfg, returns, end, 120)
    con = build_robust_mean_variance_constrained(cfg, returns, end, 120)
    assert unc.status in ("OK", "APPROXIMATE")
    assert con.status in ("OK", "APPROXIMATE")
    assert max(con.weights.values()) <= cap + 1e-3
    wu = np.array([unc.weights[t] for t in ["A", "B", "C", "D"]])
    wc = np.array([con.weights[t] for t in ["A", "B", "C", "D"]])
    wdiff = float(np.sum(np.abs(wu - wc)))
    mu_unc_max = max(unc.weights.values())
    if mu_unc_max > cap + 0.02:
        assert wdiff > 1e-5


def test_metadata_covariance_method_recorded() -> None:
    rng = np.random.default_rng(21)
    dates = pd.date_range("2015-06-30", periods=90, freq="ME")
    n = len(dates)
    returns = pd.DataFrame(
        {"U": rng.normal(0.002, 0.04, n), "V": rng.normal(0.001, 0.035, n)},
        index=dates,
    )
    cfg = _minimal_cfg(["U", "V"], lam=0.2, cov_method="oas")
    end = dates[-1].strftime("%Y-%m-%d")
    res = build_robust_mean_variance_uncapped(cfg, returns, end, 90)
    assert res.diagnostics.get("covariance_method") == "oas"
