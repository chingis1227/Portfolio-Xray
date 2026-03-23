"""
RC_vol: percentage contribution to portfolio variance. Per metrics_specification:
- Σ_window from monthly simple returns in window (ddof=1).
- For each month t: σ²_t = w_t' Σ w_t, m_t = Σ w_t, PC_{i,t} = (w_{i,t} * m_{i,t}) / σ²_t. PC sums to 1.
- RC_window_i = mean_t(PC_{i,t}). Do not use contribution to volatility or correlations.

Also: resolve_rc_asset_cap() — shared per-asset RC cap from docs/docs/feasibility_constraints_spec.md.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from policy_math.feasibility import resolve_rc_asset_cap as _policy_resolve_rc_asset_cap

DDOF = 1


def resolve_rc_asset_cap(
    rc_asset_cap_pct: float | None,
    n_assets: int,
    rb_growth: float | None = None,
) -> float:
    """
    Backwards-compatible wrapper around policy_math.feasibility.resolve_rc_asset_cap.

    - If rc_asset_cap_pct is set and > 0, it overrides the formula.
    - Else the formula from feasibility_constraints_spec is used via the centralized policy module.
    - Equity-Only mode (rb_growth >= 0.90) is signalled via equity_only=True.
    """
    if rc_asset_cap_pct is not None and rc_asset_cap_pct > 0:
        return float(rc_asset_cap_pct)
    equity_only = bool(rb_growth is not None and rb_growth >= 0.90)
    return _policy_resolve_rc_asset_cap(n_assets=n_assets, equity_only=equity_only)


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
