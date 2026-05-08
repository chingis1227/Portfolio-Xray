"""
Spinu's cyclical coordinate descent for equal risk-budget (risk parity).

Minimizes the convex Spinu objective::

    0.5 * x' Σ x - sum_i b_i log(x_i)

with x_i > 0 and budgets b_i > 0 (default b_i = 1/N). Portfolio weights are
w = x / sum(x) (long-only, fully invested).

References: Spinu (2013), risk budgeting / risk parity via CCD.

RC_vol alignment: at optimum, x_i (Σ x)_i = b_i; equal b_i implies equal
percentage contributions to variance after normalization.
"""
from __future__ import annotations

from typing import Any

import numpy as np


def repair_covariance_psd(S: np.ndarray, min_eigenvalue: float = 1e-12) -> tuple[np.ndarray, bool]:
    """
    Symmetrize and clip negative eigenvalues (nearest PSD in Frobenius sense).

    Returns (repaired_matrix, was_modified).
    """
    M = np.asarray(S, dtype=float)
    M = 0.5 * (M + M.T)
    evals, evecs = np.linalg.eigh(M)
    modified = bool(np.any(evals < -1e-10))
    evals_clipped = np.maximum(evals, float(min_eigenvalue))
    out = (evecs * evals_clipped) @ evecs.T
    out = 0.5 * (out + out.T)
    return out, modified


def spinu_objective(x: np.ndarray, cov: np.ndarray, b: np.ndarray) -> float:
    """0.5 x'Σx - sum b_i log(x_i)."""
    x = np.asarray(x, dtype=float)
    return float(0.5 * (x @ cov @ x) - float(np.sum(b * np.log(np.maximum(x, 1e-300)))))


def _percentage_contributions_variance(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    var_p = float(w @ cov @ w)
    if var_p <= 1e-16:
        return np.full_like(w, 1.0 / len(w))
    m = cov @ w
    return (w * m) / var_p


def spinu_ccd_equal_budget(
    cov: np.ndarray,
    *,
    n_assets: int | None = None,
    budget: np.ndarray | None = None,
    eps_floor: float = 1e-12,
    max_iter: int = 50_000,
    tol: float = 1e-10,
    init: str = "inv_vol",
) -> tuple[np.ndarray, dict[str, Any]]:
    """
    Cyclical coordinate descent on Spinu's objective.

    Returns:
        w: weights with sum(w)=1, w_i > 0.
        diagnostics: converged, iterations, max_coord_delta, objective_value, etc.
    """
    S = np.asarray(cov, dtype=float)
    n = int(S.shape[0])
    if n_assets is not None and n_assets != n:
        raise ValueError("n_assets must match covariance shape")
    if budget is None:
        b = np.full(n, 1.0 / float(n), dtype=float)
    else:
        b = np.asarray(budget, dtype=float).reshape(-1)
        if len(b) != n:
            raise ValueError("budget length must match n")
        if np.any(b <= 0):
            raise ValueError("budget entries must be positive")

    if init == "uniform":
        x = np.full(n, 1.0 / float(n), dtype=float)
    elif init == "inv_vol":
        diag = np.maximum(np.diag(S), eps_floor)
        inv_vol = 1.0 / np.sqrt(diag)
        x = inv_vol / float(np.sum(inv_vol))
    else:
        raise ValueError("init must be 'uniform' or 'inv_vol'")

    x = np.maximum(x, eps_floor)

    converged = False
    max_coord_delta_last = 0.0
    iterations_used = 0

    for it in range(int(max_iter)):
        max_delta = 0.0
        for i in range(n):
            old = float(x[i])
            c_i = float(np.dot(S[i, :], x) - S[i, i] * x[i])
            sii = float(S[i, i])
            if sii <= 1e-14:
                xi_new = max(old, eps_floor)
            else:
                disc = c_i * c_i + 4.0 * sii * b[i]
                disc = max(float(disc), 0.0)
                xi_new = (-c_i + np.sqrt(disc)) / (2.0 * sii)
                xi_new = max(float(xi_new), eps_floor)
            x[i] = xi_new
            max_delta = max(max_delta, abs(xi_new - old))
        iterations_used = it + 1
        max_coord_delta_last = max_delta
        if max_delta < tol:
            converged = True
            break

    s = float(np.sum(x))
    if s <= 1e-15 or not np.all(np.isfinite(x)):
        w = np.full(n, 1.0 / float(n))
        return w, {
            "converged": False,
            "iterations": iterations_used,
            "max_coord_delta": max_coord_delta_last,
            "failure": "invalid_x_sum",
            "objective": spinu_objective(x, S, b) if np.all(np.isfinite(x)) else float("nan"),
        }

    w = x / s
    target_rc = 1.0 / float(n)
    pc = _percentage_contributions_variance(w, S)
    max_rc_error = float(np.max(np.abs(pc - target_rc)))

    return w, {
        "converged": converged,
        "iterations": iterations_used,
        "max_coord_delta": max_coord_delta_last,
        "max_rc_error": max_rc_error,
        "objective": spinu_objective(x, S, b),
        "rc_by_asset": pc.tolist(),
    }
