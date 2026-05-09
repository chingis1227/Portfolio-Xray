"""Unit tests for Spinu CCD risk parity solver."""
from __future__ import annotations

import numpy as np

from src.portfolio_variants import _risk_parity_solver
from src.risk_parity_spinu import repair_covariance_psd, spinu_ccd_equal_budget
import pandas as pd


def test_spinu_diagonal_cov_converges_equal_rc() -> None:
    n = 4
    cov = np.eye(n, dtype=float) * 0.04
    w, diag = spinu_ccd_equal_budget(cov, tol=1e-12, max_iter=20_000)
    assert diag["converged"] is True
    assert abs(float(np.sum(w)) - 1.0) < 1e-10
    assert float(diag["max_rc_error"]) < 1e-10


def test_psd_repair_clips_negative_eigenvalue() -> None:
    # Artificial indefinite matrix
    S = np.array([[1.0, 1.2], [1.2, 1.0]], dtype=float)
    repaired, modified = repair_covariance_psd(S, min_eigenvalue=1e-12)
    assert modified or repaired.shape == (2, 2)
    ew = np.linalg.eigvalsh(repaired)
    assert np.all(ew >= -1e-11)


def test_risk_parity_solver_prefers_spinu_metadata() -> None:
    cols = ["a", "b", "c"]
    cov_df = pd.DataFrame(np.eye(3) * 0.01, index=cols, columns=cols)
    weights, meta = _risk_parity_solver(cov_df, cols)
    assert meta.get("risk_parity_solver") == "spinu_ccd"
    assert meta.get("fallback_used") is False
    assert meta.get("spinu_converged") is True
    assert abs(sum(weights.values()) - 1.0) < 1e-8
