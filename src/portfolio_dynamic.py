"""
NaN-safe dynamic portfolio: at each month t, w_avail = target weights for assets with non-NaN return;
w_miss = 1 - sum(w_avail); R_p,t = sum(w_avail_i * R_i,t) + w_miss * R_cash,t. No renormalization.
"""
from __future__ import annotations

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


def portfolio_returns_nan_safe(
    returns_df: pd.DataFrame,
    target_weights: dict[str, float],
    cash_returns: pd.Series,
) -> tuple[pd.Series, pd.DataFrame]:
    """
    R_p,t = sum(w_avail_i * R_i,t) + w_miss * R_cash,t. No renormalization.
    Returns (portfolio_returns, weights_used DataFrame).
    """
    w_df = dynamic_weights_matrix(returns_df, target_weights)
    common_idx = returns_df.index.intersection(cash_returns.index).intersection(w_df.index).sort_values()
    r_p = pd.Series(index=common_idx, dtype=float)
    for t in common_idx:
        row = returns_df.loc[t] if t in returns_df.index else pd.Series(dtype=float)
        w_row = w_df.loc[t]
        w_avail_sum = w_row.sum()
        w_miss = 1.0 - w_avail_sum
        r_p_t = 0.0
        for ticker in w_row.index:
            if ticker in row and pd.notna(row[ticker]):
                r_p_t += w_row[ticker] * row[ticker]
        if t in cash_returns.index and pd.notna(cash_returns.loc[t]):
            r_p_t += w_miss * cash_returns.loc[t]
        r_p.loc[t] = r_p_t
    return r_p.dropna(), w_df
