"""
Robust Mean–Variance helpers: James–Stein shrinkage of expected returns,
Ledoit–Wolf / OAS covariance shrinkage, and SLSQP solve for

    maximize  mu' w - lambda * w' Sigma w
    <=> minimize  lambda * w' Sigma w - mu' w

Monthly simple returns; Sigma and mu are on the same synchronous panel.
"""
from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.risk_contrib import DDOF
from src.risk_parity_spinu import repair_covariance_psd

CovMethod = Literal["ledoit_wolf", "oas"]


def james_stein_shrink_means(returns_df: pd.DataFrame) -> dict[str, Any]:
    """
    James–Stein shrinkage of per-column sample means toward the cross-sectional grand mean.

    Uses the standard positive-part shrinkage (toward the mean of the estimated means):

        mu_hat_i = mean over time of asset i
        mu_bar   = (1/p) * sum_i mu_hat_i
        SS       = sum_i (mu_hat_i - mu_bar)^2
        psi      = (1/p) * sum_i Var_col_i / n   (homoskedastic-ish noise of sample means)

    For p >= 3:
        c = max(0, 1 - (p - 2) * psi / SS)
        mu_JS_i = mu_bar + c * (mu_hat_i - mu_bar)

    For p < 3: no shrinkage (c = 1), identical to raw means.

    shrinkage_intensity is (1 - c): 0 means no shrink toward grand mean, 1 means full shrink.

    Parameters
    ----------
    returns_df
        Monthly simple returns, identical row index for all columns (caller drops NA rows).
    """
    if returns_df.shape[1] == 0:
        raise ValueError("james_stein_shrink_means: empty columns")
    n = int(len(returns_df))
    if n < 2:
        raw = returns_df.mean()
        gm = float(raw.mean())
        return {
            "raw_mu": raw.astype(float),
            "shrunk_mu": raw.astype(float),
            "shrinkage_target": gm,
            "shrinkage_intensity": 0.0,
            "shrinkage_multiplier_c": 1.0,
            "n_obs": n,
            "n_assets": int(returns_df.shape[1]),
            "note": "insufficient_rows_no_shrinkage",
        }

    raw = returns_df.mean(axis=0).astype(float)
    p = int(raw.shape[0])
    grand_mean = float(raw.mean())
    deviations = raw.values.astype(float) - grand_mean
    ss = float(np.sum(deviations**2))

    col_vars = returns_df.var(axis=0, ddof=DDOF).astype(float)
    psi = float(np.mean(col_vars.values) / float(n))

    if p < 3 or ss <= 1e-30:
        c = 1.0
        intensity = 0.0
        note = "p_lt_3_or_zero_ss_no_shrinkage"
    else:
        factor = (p - 2) * psi / ss
        c = float(max(0.0, 1.0 - factor))
        intensity = float(1.0 - c)
        note = "james_stein_positive_part"

    shrunk_vals = grand_mean + c * deviations
    shrunk = pd.Series(shrunk_vals, index=raw.index, dtype=float)

    return {
        "raw_mu": raw,
        "shrunk_mu": shrunk,
        "shrinkage_target": grand_mean,
        "shrinkage_intensity": intensity,
        "shrinkage_multiplier_c": c,
        "n_obs": n,
        "n_assets": p,
        "psi_mean_variance_of_mean": psi,
        "ss_deviations_from_grand_mean": ss,
        "note": note,
        "mu_shrinkage_method": "james_stein",
    }


def shrunk_covariance_monthly(
    returns_df: pd.DataFrame,
    method: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Ledoit–Wolf or OAS shrinkage covariance on the given return panel.

    Returns symmetric DataFrame and metadata including sklearn shrinkage where exposed.
    """
    m = str(method).strip().lower().replace("-", "_")
    if m in ("lw", "ledoit", "ledoit_wolf"):
        key = "ledoit_wolf"
        from sklearn.covariance import LedoitWolf

        est = LedoitWolf().fit(returns_df.values.astype(float))
        cov_arr = np.asarray(est.covariance_, dtype=float)
        shrink_meta = float(est.shrinkage_) if hasattr(est, "shrinkage_") else float("nan")
    elif m == "oas":
        key = "oas"
        from sklearn.covariance import OAS

        est = OAS().fit(returns_df.values.astype(float))
        cov_arr = np.asarray(est.covariance_, dtype=float)
        shrink_meta = float(est.shrinkage_) if hasattr(est, "shrinkage_") else float("nan")
    else:
        raise ValueError(f"shrunk_covariance_monthly: unsupported method {method!r}")

    cols = list(returns_df.columns)
    cov_df = pd.DataFrame(cov_arr, index=cols, columns=cols)
    meta = {
        "covariance_method": key,
        "shrinkage_applied": shrink_meta,
        "n_obs": int(len(returns_df)),
        "n_assets": int(len(cols)),
    }
    return cov_df, meta


def psd_status_after_repair(cov_np: np.ndarray, repaired: bool, finite: bool) -> str:
    if not finite:
        return "not_psd"
    evals = np.linalg.eigvalsh(0.5 * (cov_np + cov_np.T))
    min_ev = float(np.min(evals))
    if min_ev >= -1e-9:
        return "repaired" if repaired else "psd"
    return "not_psd"


def solve_robust_mean_variance(
    mu: np.ndarray,
    cov: np.ndarray,
    bounds: list[tuple[float, float]],
    lam: float,
    *,
    x0: np.ndarray | None = None,
    maxiter: int = 2000,
) -> tuple[np.ndarray, Any, float]:
    """
    Minimize f(w) = lam * w' Sigma w - mu' w subject to sum(w)=1 and box bounds.

    lam == 0 gives linear objective -mu' w (maximum expected shrunk return on feasible set).

    Returns (w_opt, scipy result, objective_value_at_opt).
    """
    mu_v = np.asarray(mu, dtype=float).reshape(-1)
    sigma = np.asarray(cov, dtype=float)
    n = sigma.shape[0]
    if mu_v.shape[0] != n:
        raise ValueError("mu and cov dimension mismatch")
    lam_f = float(lam)
    if lam_f < 0:
        raise ValueError("lambda must be non-negative")

    lo = np.array([float(b[0]) for b in bounds], dtype=float)
    hi = np.array([float(b[1]) for b in bounds], dtype=float)

    if x0 is None:
        x0 = np.ones(n, dtype=float) / float(n)
    x0 = np.clip(x0, lo, hi)
    if float(x0.sum()) > 1e-12:
        x0 = x0 / float(x0.sum())
    else:
        x0 = np.ones(n, dtype=float) / float(n)
        x0 = np.clip(x0, lo, hi)
        x0 = x0 / float(x0.sum())

    def fun(w: np.ndarray) -> float:
        w = np.asarray(w, dtype=float)
        quad = float(w @ sigma @ w)
        lin = float(mu_v @ w)
        return lam_f * quad - lin

    def jac(w: np.ndarray) -> np.ndarray:
        w = np.asarray(w, dtype=float)
        return 2.0 * lam_f * (sigma @ w) - mu_v

    cons = {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)}

    res = minimize(
        fun,
        x0,
        method="SLSQP",
        jac=jac,
        bounds=list(zip(lo, hi)),
        constraints=cons,
        options={"maxiter": maxiter, "ftol": 1e-9},
    )

    w_out = np.asarray(res.x, dtype=float)
    if not getattr(res, "success", False) or not np.all(np.isfinite(w_out)):
        res2 = minimize(
            fun,
            x0,
            method="SLSQP",
            jac=jac,
            bounds=list(zip(lo, hi)),
            constraints=cons,
            options={"maxiter": maxiter, "ftol": 1e-11},
        )
        w_out = np.asarray(res2.x, dtype=float)
        res = res2

    w_out = np.clip(w_out, lo, hi)
    ssum = float(w_out.sum())
    if ssum > 1e-12:
        w_out = w_out / ssum
    else:
        w_out = np.clip(np.ones(n) / n, lo, hi)
        w_out = w_out / float(w_out.sum())

    obj_val = float(fun(w_out))
    return w_out, res, obj_val


def concentration_metrics(weights: dict[str, float]) -> dict[str, float]:
    """HHI, effective N, top1/top3 weight shares on strictly positive weights."""
    w = np.array([float(v) for v in weights.values() if float(v) > 1e-15], dtype=float)
    if w.size == 0:
        return {"hhi": 0.0, "effective_n": 0.0, "top1_share": 0.0, "top3_share": 0.0}
    w = w / float(np.sum(w))
    w_sorted = np.sort(w)[::-1]
    hhi = float(np.sum(w_sorted**2))
    eff_n = float(1.0 / hhi) if hhi > 1e-30 else float(len(w_sorted))
    top1 = float(w_sorted[0])
    top3 = float(np.sum(w_sorted[: min(3, len(w_sorted))]))
    return {"hhi": hhi, "effective_n": eff_n, "top1_share": top1, "top3_share": top3}


def normalize_robust_mv_covariance_method(raw: str | None) -> CovMethod:
    """Normalize config string to ledoit_wolf | oas."""
    if raw is None:
        return "ledoit_wolf"
    m = str(raw).strip().lower().replace("-", "_")
    if m in ("lw", "ledoit", "ledoit_wolf"):
        return "ledoit_wolf"
    if m == "oas":
        return "oas"
    raise ValueError(f"robust_mv_covariance_method must be ledoit_wolf or oas, got {raw!r}")
