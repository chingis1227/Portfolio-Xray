"""
NaN-safe dynamic portfolio.

At each month t, w_avail = target weights for assets with non-NaN return;
w_miss = 1 - sum(w_avail); R_p,t = sum(w_avail_i * R_i,t) + w_miss * R_cash,t. No renormalization.

Optional global redistribution among ``risk_tickers``: if a risk asset has NaN, its weight is
redistributed equally among other risk assets with valid returns that month. If per-asset RC
would exceed cap after redistribution (and cov_df + caps provided), fall back to simple w_miss-to-cash.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def dynamic_weights_matrix(
    returns_df: pd.DataFrame,
    target_weights: dict[str, float],
) -> pd.DataFrame:
    """
    At each date t, for each asset: weight = target_weights[asset] if return at t is non-NaN else 0.
    Returns DataFrame index=dates, columns=assets, values=weights used that month (not renormalized).
    """
    tickers = list(target_weights.keys())
    w = pd.DataFrame(index=returns_df.index, columns=tickers, dtype=float)
    for t in returns_df.index:
        for ticker in tickers:
            if ticker not in returns_df.columns:
                w.loc[t, ticker] = 0.0
            elif pd.notna(returns_df.loc[t, ticker]):
                w.loc[t, ticker] = target_weights.get(ticker, 0.0)
            else:
                w.loc[t, ticker] = 0.0
    return w.fillna(0)


def _weights_at_t_global_redist(
    row: pd.Series,
    target_weights: dict[str, float],
    risk_tickers: list[str],
) -> dict[str, float]:
    """Equal redistribution of missing weight among available risk tickers for this period."""
    out = dict(target_weights)
    valid = [t for t in risk_tickers if t in row.index and pd.notna(row[t]) and target_weights.get(t, 0) != 0]
    missing = [t for t in risk_tickers if t not in valid or target_weights.get(t, 0) == 0]
    w_miss_b = sum(target_weights.get(t, 0) for t in missing)
    if not valid or w_miss_b <= 0:
        for t in risk_tickers:
            out[t] = target_weights.get(t, 0) if t in valid else 0.0
        return out
    k = len(valid)
    delta = w_miss_b / k
    for t in risk_tickers:
        if t in valid:
            out[t] = target_weights.get(t, 0) + delta
        else:
            out[t] = 0.0
    return out


def _rc_check_asset_caps_only(
    w_risk: dict[str, float],
    cov_df: pd.DataFrame,
    rc_asset_cap_pct: float | None,
    rc_cap_by_ticker: dict[str, float] | None = None,
) -> bool:
    cols = [t for t in w_risk if t in cov_df.columns and t in cov_df.index and w_risk.get(t, 0) > 0]
    if not cols:
        return True
    w = np.array([w_risk[t] for t in cols])
    cov = cov_df.reindex(index=cols, columns=cols).fillna(0).values
    var_p = float(np.dot(w, np.dot(cov, w)))
    if var_p <= 1e-16:
        return True
    pc = (w * (cov @ w)) / var_p
    total = float(np.sum(pc))
    if total <= 1e-16:
        return True
    rc_pct = pc / total
    if rc_cap_by_ticker is not None:
        for i, t in enumerate(cols):
            cap_t = float(rc_cap_by_ticker.get(t, 1.0))
            if rc_pct[i] > cap_t + 1e-9:
                return False
    elif rc_asset_cap_pct is not None and rc_asset_cap_pct > 0:
        cap = float(rc_asset_cap_pct)
        for i in range(len(cols)):
            if rc_pct[i] > cap + 1e-9:
                return False
    return True


def portfolio_returns_nan_safe(
    returns_df: pd.DataFrame,
    target_weights: dict[str, float],
    cash_returns: pd.Series,
    *,
    risk_tickers: list[str] | None = None,
    rc_asset_cap_pct: float | None = None,
    cov_df: pd.DataFrame | None = None,
    return_diagnostics: bool = False,
    rc_cap_by_ticker: dict[str, float] | None = None,
    **_: Any,
) -> tuple[pd.Series, pd.DataFrame] | tuple[pd.Series, pd.DataFrame, dict[str, Any]]:
    """
    NaN-safe portfolio returns.

    Default (risk_tickers=None): R_p,t = sum(w_avail_i * R_i,t) + w_miss * R_cash,t.

    When risk_tickers is set: global equal redistribution among those tickers first; then if
    cov_df and RC caps are provided and violated, fall back to w_miss-to-cash for that month.
    """
    rt = list(risk_tickers) if risk_tickers else []
    do_rc_check = bool(rt and cov_df is not None and (rc_cap_by_ticker is not None or (rc_asset_cap_pct is not None and rc_asset_cap_pct > 0)))

    n_months_redistributed = 0
    n_months_cash_fallback = 0

    w_df = pd.DataFrame(index=returns_df.index, columns=list(target_weights.keys()), dtype=float)
    common_idx = returns_df.index.intersection(cash_returns.index).sort_values()
    r_p = pd.Series(index=common_idx, dtype=float)

    for t in common_idx:
        row = returns_df.loc[t] if t in returns_df.index else pd.Series(dtype=float)
        used_redist = False
        used_fallback = False
        if rt:
            w_row = _weights_at_t_global_redist(row, target_weights, rt)
            for ticker in rt:
                if target_weights.get(ticker, 0) and (ticker not in row.index or pd.isna(row.get(ticker))):
                    others = [x for x in rt if x in row.index and pd.notna(row.get(x)) and target_weights.get(x, 0) != 0]
                    if others:
                        used_redist = True
                        break
            if do_rc_check and cov_df is not None:
                w_risk = {k: v for k, v in w_row.items() if k in rt and v > 0}
                if not _rc_check_asset_caps_only(w_risk, cov_df, rc_asset_cap_pct, rc_cap_by_ticker):
                    used_fallback = True
                    w_row = {}
                    for ticker in target_weights:
                        if ticker not in returns_df.columns:
                            w_row[ticker] = 0.0
                        elif pd.notna(row.get(ticker)):
                            w_row[ticker] = target_weights.get(ticker, 0.0)
                        else:
                            w_row[ticker] = 0.0
        else:
            w_row = {}
            for ticker in target_weights:
                if ticker not in returns_df.columns:
                    w_row[ticker] = 0.0
                elif pd.notna(row.get(ticker)):
                    w_row[ticker] = target_weights.get(ticker, 0.0)
                else:
                    w_row[ticker] = 0.0
        if used_redist:
            n_months_redistributed += 1
        if used_fallback:
            n_months_cash_fallback += 1
        for k in w_row:
            w_df.loc[t, k] = w_row[k]
        w_miss = 1.0 - sum(w_row.values())
        r_p_t = 0.0
        for ticker in w_row:
            if ticker in row and pd.notna(row.get(ticker)):
                r_p_t += w_row[ticker] * row[ticker]
        if t in cash_returns.index and pd.notna(cash_returns.loc[t]):
            r_p_t += w_miss * cash_returns.loc[t]
        r_p.loc[t] = r_p_t

    w_df = w_df.fillna(0)
    if return_diagnostics:
        diagnostics: dict[str, Any] = {
            "n_months_redistributed": n_months_redistributed,
            "n_months_cash_fallback": n_months_cash_fallback,
        }
        return r_p.dropna(), w_df, diagnostics
    return r_p.dropna(), w_df
