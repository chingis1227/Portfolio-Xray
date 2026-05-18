"""
NaN-safe dynamic portfolio.

At each month t, w_avail = target weights for assets with non-NaN return;
w_miss = 1 - sum(w_avail); R_p,t = sum(w_avail_i * R_i,t) + w_miss * R_cash,t. No renormalization.

Optional global redistribution among ``risk_tickers``: if a risk asset has NaN, its weight is
redistributed equally among other risk assets with valid returns that month. RC_vol is not used
as a gating constraint on this path.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

CASH_FALLBACK_EPS = 1e-12


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
    valid = [
        t
        for t in risk_tickers
        if t in row.index and pd.notna(row[t]) and target_weights.get(t, 0) != 0
    ]
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


def _positive_missing_weight(
    row: pd.Series,
    target_weights: dict[str, float],
    tickers: list[str],
) -> float:
    """Return positive target weight for tickers without an observed return in this period."""
    missing_weight = 0.0
    for ticker in tickers:
        try:
            weight = float(target_weights.get(ticker, 0.0) or 0.0)
        except (TypeError, ValueError):
            continue
        if weight <= CASH_FALLBACK_EPS:
            continue
        if ticker not in row.index or pd.isna(row.get(ticker)):
            missing_weight += weight
    return missing_weight


def portfolio_returns_nan_safe(
    returns_df: pd.DataFrame,
    target_weights: dict[str, float],
    cash_returns: pd.Series,
    *,
    risk_tickers: list[str] | None = None,
    return_diagnostics: bool = False,
    **_: Any,
) -> tuple[pd.Series, pd.DataFrame] | tuple[pd.Series, pd.DataFrame, dict[str, Any]]:
    """
    NaN-safe portfolio returns.

    Default (risk_tickers=None): R_p,t = sum(w_avail_i * R_i,t) + w_miss * R_cash,t.

    When risk_tickers is set: global equal redistribution among those tickers first for missing returns.
    """
    rt = list(risk_tickers) if risk_tickers else []

    n_months_redistributed = 0
    n_months_cash_fallback = 0

    w_df = pd.DataFrame(index=returns_df.index, columns=list(target_weights.keys()), dtype=float)
    common_idx = returns_df.index.intersection(cash_returns.index).sort_values()
    r_p = pd.Series(index=common_idx, dtype=float)

    for t in common_idx:
        row = returns_df.loc[t] if t in returns_df.index else pd.Series(dtype=float)
        used_redist = False
        fallback_candidates = rt if rt else list(target_weights.keys())
        positive_missing_weight = _positive_missing_weight(row, target_weights, fallback_candidates)
        if rt:
            w_row = _weights_at_t_global_redist(row, target_weights, rt)
            for ticker in rt:
                if target_weights.get(ticker, 0) and (
                    ticker not in row.index or pd.isna(row.get(ticker))
                ):
                    others = [
                        x
                        for x in rt
                        if x in row.index and pd.notna(row.get(x)) and target_weights.get(x, 0) != 0
                    ]
                    if others:
                        used_redist = True
                        break
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
        for k in w_row:
            w_df.loc[t, k] = w_row[k]
        w_miss = 1.0 - sum(w_row.values())
        cash_available = t in cash_returns.index and pd.notna(cash_returns.loc[t])
        if (
            w_miss > CASH_FALLBACK_EPS
            and positive_missing_weight > CASH_FALLBACK_EPS
            and cash_available
        ):
            n_months_cash_fallback += 1
        r_p_t = 0.0
        for ticker in w_row:
            if ticker in row and pd.notna(row.get(ticker)):
                r_p_t += w_row[ticker] * row[ticker]
        if cash_available:
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
