from __future__ import annotations

import numpy as np
import pytest

from src.hrp_weights import (
    correlation_from_covariance,
    hrp_long_only_weights,
)


def test_hrp_weights_sum_to_one_and_nonnegative() -> None:
    rng = np.random.default_rng(42)
    n = 8
    a = rng.standard_normal((n, 100))
    cov = np.cov(a)
    cov = 0.5 * (cov + cov.T)
    w, diag = hrp_long_only_weights(cov, prefer_ward=True)
    assert w.shape == (n,)
    assert np.all(w >= -1e-12)
    assert abs(float(w.sum()) - 1.0) < 1e-10
    assert diag.get("linkage_method") in ("ward", "average", None)


def test_hrp_single_asset() -> None:
    cov = np.array([[0.0004]])
    w, diag = hrp_long_only_weights(cov)
    assert w.shape == (1,)
    assert w[0] == pytest.approx(1.0)
    assert diag.get("status") == "ok_single_asset"


def test_correlation_from_covariance_diag_one() -> None:
    cov = np.array([[0.01, 0.005], [0.005, 0.04]], dtype=float)
    rho = correlation_from_covariance(cov)
    assert rho[0, 0] == pytest.approx(1.0)
    assert rho[1, 1] == pytest.approx(1.0)
    assert -1.0 <= float(rho[0, 1]) <= 1.0


def test_hrp_two_assets_positive() -> None:
    cov = np.array([[0.01, 0.0], [0.0, 0.04]], dtype=float)
    w, _diag = hrp_long_only_weights(cov)
    assert w.shape == (2,)
    assert np.all(w > 0.0)
    assert abs(float(w.sum()) - 1.0) < 1e-10
