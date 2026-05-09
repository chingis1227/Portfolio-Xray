from __future__ import annotations

"""
Hierarchical Risk Parity (HRP) — long-only weights from correlation distance,
hierarchical clustering, quasi-diagonalization, and recursive bisection.

No matrix inversion. No optimizer projection. Intended as an unconstrained
diversification baseline (same role as canonical Risk Parity in this project).
"""

from typing import Any, Dict, Tuple

import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform


def correlation_from_covariance(cov: np.ndarray) -> np.ndarray:
    """Pearson correlation from covariance; diagonal forced to 1 after clipping."""
    cov = np.asarray(cov, dtype=float)
    d = np.sqrt(np.maximum(np.diag(cov), 1e-18))
    with np.errstate(divide="ignore", invalid="ignore"):
        rho = cov / (d[:, None] * d[None, :])
    rho = np.nan_to_num(rho, nan=0.0, posinf=0.0, neginf=0.0)
    rho = np.clip(rho, -1.0, 1.0)
    np.fill_diagonal(rho, 1.0)
    return rho


def correlation_distance_matrix(rho: np.ndarray) -> np.ndarray:
    """Correlation distance d_ij = sqrt(0.5 * (1 - rho_ij)), symmetric, zero diagonal."""
    rho = np.asarray(rho, dtype=float)
    d = np.sqrt(np.maximum(0.0, 0.5 * (1.0 - rho)))
    np.fill_diagonal(d, 0.0)
    d = np.maximum(d, d.T)
    return d


def _cluster_variance_inverse_variance(cov: np.ndarray, ix: list[int]) -> float:
    """Variance of the inverse-variance-weighted portfolio on the sub-covariance slice."""
    sub = cov[np.ix_(ix, ix)]
    d = np.diag(sub)
    iv = 1.0 / np.maximum(np.asarray(d, dtype=float), 1e-18)
    s = float(iv.sum())
    if s <= 0.0:
        return float(np.trace(sub)) / max(len(ix), 1)
    w = iv / s
    return float(w @ sub @ w)


def _recursive_bisection_sorted(cov_sorted: np.ndarray) -> np.ndarray:
    """
    Recursive bisection along quasi-diagonal order (contiguous blocks are hierarchical).

    Weights start at 1 for each asset; at each split between two child index sets,
    multiply the left branch by alpha = v_right / (v_left + v_right) and the right
    by (1 - alpha).
    """
    cov_sorted = np.asarray(cov_sorted, dtype=float)
    n = int(cov_sorted.shape[0])
    if n <= 0:
        return np.array([])
    if n == 1:
        return np.ones(1, dtype=float)

    w = np.ones(n, dtype=float)
    clusters: list[list[int]] = [list(range(n))]
    while clusters:
        items = clusters.pop(0)
        if len(items) < 2:
            continue
        split = len(items) // 2
        ix_l = items[:split]
        ix_r = items[split:]
        v_l = _cluster_variance_inverse_variance(cov_sorted, ix_l)
        v_r = _cluster_variance_inverse_variance(cov_sorted, ix_r)
        denom = v_l + v_r
        if denom <= 1e-20:
            alpha = 0.5
        else:
            alpha = float(v_r / denom)
        for i in ix_l:
            w[i] *= alpha
        for i in ix_r:
            w[i] *= 1.0 - alpha
        clusters.insert(0, ix_r)
        clusters.insert(0, ix_l)

    s = float(w.sum())
    if s <= 1e-20 or not np.all(np.isfinite(w)):
        return np.ones(n, dtype=float) / float(n)
    return w / s


def _linkage_from_condensed(
    condensed: np.ndarray, *, prefer_ward: bool
) -> Tuple[np.ndarray, str, bool]:
    """
    Build SciPy linkage from condensed distance matrix.

    Ward on a generic precomputed distance can be invalid; try Ward first when
    requested, then fall back to average linkage.
    """
    condensed = np.asarray(condensed, dtype=float)
    if prefer_ward:
        try:
            z = linkage(condensed, method="ward")
            if np.all(np.isfinite(z)):
                return z, "ward", False
        except Exception:
            pass
        z = linkage(condensed, method="average")
        if not np.all(np.isfinite(z)):
            raise ValueError("HRP linkage produced non-finite values")
        return z, "average", True
    z = linkage(condensed, method="average")
    if not np.all(np.isfinite(z)):
        raise ValueError("HRP linkage produced non-finite values")
    return z, "average", False


def hrp_long_only_weights(
    cov: np.ndarray,
    *,
    prefer_ward: bool = True,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Compute HRP portfolio weights (long-only, sum to 1) from a square covariance matrix.

    Parameters
    ----------
    cov :
        (n, n) covariance aligned to asset order; symmetrized internally.
    prefer_ward :
        If True, try ``method='ward'`` first on condensed correlation-distance, then fall back
        to ``average`` if Ward fails or yields non-finite values.

    Returns
    -------
    weights :
        Length-n array aligned to rows/columns of ``cov``.
    diagnostics :
        Metadata for exports (linkage method, seriation, etc.).
    """
    cov = np.asarray(cov, dtype=float)
    cov = 0.5 * (cov + cov.T)
    n = int(cov.shape[0])
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError("cov must be square")
    if n == 0:
        return np.array([]), {"status": "empty", "n_assets": 0}
    if n == 1:
        return np.ones(1), {
            "status": "ok_single_asset",
            "n_assets": 1,
            "linkage_method": None,
            "linkage_fallback_from_ward": False,
            "seriation_indices": [0],
        }

    rho = correlation_from_covariance(cov)
    dist = correlation_distance_matrix(rho)
    condensed = squareform(dist, checks=False)
    z, method_used, fallback = _linkage_from_condensed(condensed, prefer_ward=prefer_ward)
    order = [int(x) for x in leaves_list(z)]
    if len(order) != n:
        raise ValueError("leaves_list length mismatch")
    cov_sorted = cov[np.ix_(order, order)]
    w_sorted = _recursive_bisection_sorted(cov_sorted)
    w = np.zeros(n, dtype=float)
    for i, j in enumerate(order):
        w[j] = float(w_sorted[i])

    s = float(w.sum())
    if s > 1e-18:
        w = w / s
    else:
        w = np.ones(n, dtype=float) / float(n)

    w = np.clip(w, 0.0, None)
    s2 = float(w.sum())
    if s2 > 1e-18:
        w = w / s2

    diag: Dict[str, Any] = {
        "status": "ok",
        "n_assets": n,
        "linkage_method": method_used,
        "linkage_fallback_from_ward": bool(fallback),
        "seriation_indices": list(order),
        "distance": "sqrt(0.5*(1-rho))",
        "weights_sum": float(np.sum(w)),
    }
    return w, diag
