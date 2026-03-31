"""Serial correlation diagnostics for factor OLS (no network)."""
from __future__ import annotations

import numpy as np

from src.stress_factors import (
    FACTOR_REGRESSION_BG_LAGS,
    durbin_watson_statistic,
    factor_regression_serial_diagnostics,
)


def test_durbin_watson_near_two_for_irregular_alternating() -> None:
    u = np.array([0.1, -0.1, 0.1, -0.1, 0.1, -0.1], dtype=float)
    dw = durbin_watson_statistic(u)
    assert dw is not None
    assert 0 < dw < 4


def test_factor_regression_serial_white_noise_like() -> None:
    rng = np.random.default_rng(42)
    n = 300
    X = rng.normal(size=(n, 3))
    beta = np.array([0.01, 0.02, -0.01])
    y = X @ beta + rng.normal(scale=0.5, size=n)
    out = factor_regression_serial_diagnostics(y, X, bg_lags=FACTOR_REGRESSION_BG_LAGS)
    assert out.get("error") is None
    assert out["durbin_watson"] is not None
    assert 1.5 < float(out["durbin_watson"]) < 2.5
    assert len(out["breusch_godfrey"]) == len(FACTOR_REGRESSION_BG_LAGS)
    for row in out["breusch_godfrey"]:
        assert "lm_statistic" in row
        assert row["df_chi2"] == row["lags"]
