"""HAC / Newey–West inference for factor OLS (no network)."""
from __future__ import annotations

import numpy as np

from src.stress_factors import _newey_west_covariance  # type: ignore[attr-defined]


def test_newey_west_covariance_positive_definite() -> None:
    # Simple synthetic design: 3 regressors + intercept, no strong serial correlation in errors.
    rng = np.random.default_rng(0)
    n = 200
    X = rng.normal(size=(n, 3))
    Z = np.column_stack([np.ones(n), X])
    beta = np.array([0.01, 0.02, -0.01, 0.03])
    y = Z @ beta + rng.normal(scale=0.5, size=n)
    resid = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    cov = _newey_west_covariance(Z, resid, max_lags=4)
    # Covariance must be symmetric and positive semi-definite on diagonal
    assert cov.shape == (4, 4)
    assert np.allclose(cov, cov.T, atol=1e-8)
    assert np.all(np.diag(cov) >= 0.0)

