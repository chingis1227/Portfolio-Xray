"""
Robust optimization (maximin) по box-неопределённости μ — тест на синтетике.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.optimization import run_max_return_optimization
from src.risk_contrib import cov_matrix_monthly


def _synthetic_returns_robust(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = 48
    dates = pd.date_range("2019-01-31", periods=n, freq="ME")
    return pd.DataFrame(
        {
            "VOO": rng.normal(0.011, 0.035, n),
            "QQQ": rng.normal(0.009, 0.042, n),
            "BND": rng.normal(0.0025, 0.015, n),
            "GLD": rng.normal(0.005, 0.025, n),
        },
        index=dates,
    )


def _risk_tickers() -> list[str]:
    return ["VOO", "QQQ", "BND", "GLD"]


def test_robust_box_mu_shifts_weights_relative_to_nominal():
    ret = _synthetic_returns_robust()
    # Three names: with N=3 the uniform max-weight cap is 0.40 each (3×0.4>1), so the feasible set is not a single point.
    risk = ["VOO", "QQQ", "BND"]
    ret = ret[risk].dropna(how="any")
    assert len(ret) >= 11

    cov_df = cov_matrix_monthly(ret, ddof=1, use_shrinkage=False)
    mu_hat = ret.mean()
    mu_robust = pd.Series(
        {"VOO": 0.001, "QQQ": 0.001, "BND": 0.02},
        dtype=float,
    ).reindex(risk).fillna(0.0)

    common = dict(
        returns_df=ret,
        risk_tickers=risk,
        rc_asset_cap_pct=0.99,
        min_single_security_weight_pct=0.01,
        max_single_security_weight_pct=0.99,
        window_months=len(ret),
        returns_window=None,
        use_shrinkage=False,
        cov_precomputed=cov_df,
    )

    w_nom, st_nom = run_max_return_optimization(**common, mu_precomputed=mu_hat)
    w_rob, st_rob = run_max_return_optimization(**common, mu_precomputed=mu_robust)

    assert w_nom, f"nominal empty: {st_nom}"
    assert w_rob, f"robust empty: {st_rob}"

    for name, w in [("nominal", w_nom), ("robust", w_rob)]:
        assert abs(sum(w.values()) - 1.0) < 1e-5, name
        for t, x in w.items():
            assert -1e-9 <= x <= 1.0 + 1e-9, (name, t, x)

    tickers = sorted(set(w_nom) | set(w_rob))
    l1 = sum(abs(w_nom.get(t, 0.0) - w_rob.get(t, 0.0)) for t in tickers)
    assert l1 > 1e-4, f"weights should differ (L1={l1}); status nominal={st_nom!r} robust={st_rob!r}"


def test_robust_worst_case_mu_matches_lower_bound_objective():
    ret = _synthetic_returns_robust(seed=11)
    risk = _risk_tickers()
    ret = ret[risk].dropna(how="any")
    cov_df = cov_matrix_monthly(ret, ddof=1, use_shrinkage=False)
    mu_hat = ret.mean()
    zero_eps = pd.Series(0.0, index=mu_hat.index)
    mu_same = mu_hat - zero_eps

    common = dict(
        returns_df=ret,
        risk_tickers=risk,
        rc_asset_cap_pct=0.99,
        min_single_security_weight_pct=0.02,
        max_single_security_weight_pct=0.99,
        window_months=len(ret),
        returns_window=None,
        use_shrinkage=False,
        cov_precomputed=cov_df,
    )

    w1, _ = run_max_return_optimization(**common, mu_precomputed=mu_hat)
    w2, _ = run_max_return_optimization(**common, mu_precomputed=mu_same)

    assert w1 and w2
    l1 = sum(abs(w1.get(t, 0) - w2.get(t, 0)) for t in set(w1) | set(w2))
    assert l1 < 1e-5
