"""Tests for dual covariance / young-ETF optimization helpers."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.young_etfs_dual_cov import (
    build_dual_covariance_and_mu,
    maturity_bucket,
    shrinkage_alpha_for_history,
    per_ticker_young_weight_caps,
)


def _monthly_index(n: int) -> pd.DatetimeIndex:
    return pd.date_range("2015-01-31", periods=n, freq="ME")


def test_maturity_bucket_and_alpha():
    pol = {
        "eligible_months": 48,
        "candidate_months_min": 12,
        "new_shrinkage_alpha": 0.1,
        "candidate_alpha_min": 0.1,
        "candidate_alpha_at_eligible": 1.0,
    }
    assert maturity_bucket(50, 12, 48) == "eligible"
    assert maturity_bucket(24, 12, 48) == "candidate"
    assert maturity_bucket(6, 12, 48) == "new"
    assert shrinkage_alpha_for_history(6, pol) == 0.1
    assert abs(shrinkage_alpha_for_history(30, pol) - (0.1 + 0.5 * 0.9)) < 1e-9
    assert shrinkage_alpha_for_history(48, pol) == 1.0


def test_build_dual_covariance_symmetric_psd():
    dates = _monthly_index(80)
    rng = np.random.default_rng(42)
    base_voo = rng.normal(0.008, 0.04, len(dates))
    returns = pd.DataFrame(
        {
            "VOO": base_voo,
            "BND": rng.normal(0.002, 0.01, len(dates)),
            "GLD": rng.normal(0.004, 0.02, len(dates)),
            # Young: only last 10 months
            "NEW1": np.concatenate([np.full(len(dates) - 10, np.nan), rng.normal(0.01, 0.05, 10)]),
        },
        index=dates,
    )
    blocks = {"Growth": ["VOO", "NEW1"], "Duration": ["BND"], "Inflation": ["GLD"]}
    ticker_to_block = {"VOO": "Growth", "NEW1": "Growth", "BND": "Duration", "GLD": "Inflation"}
    policy = {
        "eligible_months": 48,
        "candidate_months_min": 12,
        "new_shrinkage_alpha": 0.1,
        "candidate_alpha_min": 0.1,
        "candidate_alpha_at_eligible": 1.0,
        "max_weight_candidate_or_new_pct": 0.02,
        "aggregate_candidate_new_warn_pct": 0.10,
    }
    cov, mu, diag = build_dual_covariance_and_mu(
        returns, ["VOO", "BND", "GLD", "NEW1"], ticker_to_block, window_months=60, policy=policy
    )
    assert cov.shape == (4, 4)
    assert np.allclose(cov.values, cov.values.T, atol=1e-8)
    eig = np.linalg.eigvalsh(cov.values)
    assert eig.min() > -1e-7
    assert "NEW1" in diag["tickers"]
    assert diag["tickers"]["NEW1"]["bucket"] == "new"
    caps = per_ticker_young_weight_caps(diag["tickers"], 0.02)
    assert caps.get("NEW1") == 0.02
    assert "VOO" not in caps
    assert len(mu) == 4
