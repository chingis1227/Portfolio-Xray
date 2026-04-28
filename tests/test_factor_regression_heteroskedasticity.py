"""Breusch-Pagan heteroskedasticity diagnostics for factor OLS (no network)."""
from __future__ import annotations

import numpy as np

from src.stress_factors import factor_regression_heteroskedasticity_diagnostics


def test_breusch_pagan_detects_factor_linked_heteroskedasticity() -> None:
    rng = np.random.default_rng(123)
    n = 500
    x1 = np.linspace(0.0, 1.0, n)
    x2 = rng.normal(size=n)
    X = np.column_stack([x1, x2])
    beta = np.array([0.04, -0.02])
    noise_scale = 0.05 + 1.0 * x1
    y = X @ beta + noise_scale * rng.normal(size=n)

    out = factor_regression_heteroskedasticity_diagnostics(y, X)
    bp = out["breusch_pagan"]

    assert out.get("error") is None
    assert bp["df_chi2"] == 2
    assert bp["n_aux_observations"] == n
    assert bp["lm_statistic"] > 20.0
    assert bp["p_value"] < 0.001


def test_breusch_pagan_does_not_flag_fixed_seed_homoskedastic_noise() -> None:
    rng = np.random.default_rng(42)
    n = 500
    X = rng.normal(size=(n, 3))
    beta = np.array([0.01, 0.02, -0.01])
    y = X @ beta + rng.normal(scale=0.5, size=n)

    out = factor_regression_heteroskedasticity_diagnostics(y, X)
    bp = out["breusch_pagan"]

    assert out.get("error") is None
    assert bp["df_chi2"] == 3
    assert bp["p_value"] > 0.01

