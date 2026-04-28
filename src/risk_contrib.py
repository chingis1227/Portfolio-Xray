"""
RC_vol: percentage contribution to portfolio variance. Per metrics_specification:
- Σ_window from monthly simple returns in window (ddof=1).
- For each month t: σ²_t = w_t' Σ w_t, m_t = Σ w_t, PC_{i,t} = (w_{i,t} * m_{i,t}) / σ²_t. PC sums to 1.
- RC_window_i = mean_t(PC_{i,t}). Do not use contribution to volatility or correlations.

RC_vol is used for reporting and stress diagnostics only; it is not a portfolio construction cap.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DDOF = 1


def cov_matrix_monthly(
    returns_df: pd.DataFrame,
    ddof: int = DDOF,
    use_shrinkage: bool = False,
) -> pd.DataFrame:
    """
    Covariance matrix of monthly returns (columns = assets).
    When use_shrinkage=True, applies Ledoit-Wolf shrinkage to stabilize estimates.
    """
    if use_shrinkage:
        try:
            from sklearn.covariance import LedoitWolf

            lw = LedoitWolf().fit(returns_df.values)
            cov = pd.DataFrame(
                lw.covariance_,
                index=returns_df.columns,
                columns=returns_df.columns,
            )
            return cov
        except Exception:
            return returns_df.cov(ddof=ddof)
    return returns_df.cov(ddof=ddof)


def cov_matrix_monthly_robust(
    returns_df: pd.DataFrame,
    ddof: int = DDOF,
) -> pd.DataFrame:
    """
    Robust covariance via sklearn Minimum Covariance Determinant (MCD).

    Intended for experiments / diagnostics; not the default policy pipeline.
    Falls back to sample ``returns_df.cov(ddof=ddof)`` if MCD does not fit
    (e.g. too few rows vs columns) or raises.
    """
    if returns_df.shape[1] == 0 or len(returns_df) < 2:
        return returns_df.cov(ddof=ddof)
    n, p = returns_df.shape
    if n < p + 1:
        return returns_df.cov(ddof=ddof)
    try:
        from sklearn.covariance import MinCovDet

        mcd = MinCovDet(random_state=0).fit(returns_df.values.astype(float))
        return pd.DataFrame(
            mcd.covariance_,
            index=returns_df.columns,
            columns=returns_df.columns,
        )
    except Exception:
        return returns_df.cov(ddof=ddof)


def variance_p(w: np.ndarray, cov: np.ndarray) -> float:
    """Portfolio variance σ² = w' Σ w."""
    return float(w @ cov @ w)


def marginal_contributions_variance(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """m_t = Σ w_t (vector (Σ_window w_t))."""
    return cov @ w


def percentage_contributions_variance(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """
    Percentage contribution to portfolio variance: PC_{i,t} = (w_{i,t} * (Σw)_i) / σ²_t. Sum(PC)=1.
    """
    m = marginal_contributions_variance(w, cov)
    var_p = variance_p(w, cov)
    if var_p <= 0:
        return np.full_like(w, np.nan)
    pc = (w * m) / var_p
    return pc


def rc_vol_window(
    returns_df: pd.DataFrame,
    weights_df: pd.DataFrame,
    ddof: int = DDOF,
) -> pd.Series:
    """
    For the window: Σ_window = cov(returns_df, ddof=1). For each month t, w_t from weights_df,
    compute PC_t. Return RC_window = mean_t(PC_t) as a Series (index = asset names).
    """
    cov = cov_matrix_monthly(returns_df, ddof=ddof)
    cov_np = cov.values
    asset_order = list(cov.columns)
    pc_list = []
    for d in returns_df.index:
        if d not in weights_df.index:
            continue
        w = weights_df.loc[d].reindex(asset_order).fillna(0).values
        if w.shape[0] != len(asset_order):
            continue
        pc = percentage_contributions_variance(w, cov_np)
        pc_list.append(pd.Series(pc, index=asset_order))
    if not pc_list:
        return pd.Series(index=asset_order, dtype=float)
    pc_df = pd.concat(pc_list, axis=1).T
    return pc_df.mean(axis=0)
