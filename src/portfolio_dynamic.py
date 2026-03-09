"""
NaN-safe dynamic portfolio.

Default: at each month t, w_avail = target weights for assets with non-NaN return;
w_miss = 1 - sum(w_avail); R_p,t = sum(w_avail_i * R_i,t) + w_miss * R_cash,t. No renormalization.

Extended (when blocks and optionally RC params provided):
  - Within-block equal redistribution: if an asset in a block has NaN, its weight is
    redistributed equally among available assets in the same block (data_policy_nan_young_etfs.md).
  - RC-gated fallback: after redistribution, if RC_asset_cap or RB corridor would be violated,
    use simple w_miss-to-cash for that month instead.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

# Block names for risk budget (must match optimization.RISK_BUDGET_BLOCKS)
RISK_BUDGET_BLOCKS = ("Growth", "Duration", "Inflation")
RB_CORRIDOR_PP = 0.05


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


def _ticker_to_block_map(blocks: dict[str, list[str]]) -> dict[str, str]:
    """Map each ticker to its block name (Growth, Duration, Inflation)."""
    m: dict[str, str] = {}
    for b in RISK_BUDGET_BLOCKS:
        for t in blocks.get(b, []):
            m[t] = b
    return m


def _weights_at_t_within_block_redist(
    row: pd.Series,
    target_weights: dict[str, float],
    blocks: dict[str, list[str]],
) -> dict[str, float]:
    """
    For one period: within-block equal redistribution of missing weight.
    Missing weight in block X = sum of target_weights for assets in X with NaN.
    Each available asset in X gets increment w_miss_block / K (K = count of available in X).
    Cash and any ticker not in blocks keep target weight; missing risk weight (whole block NaN) stays as shortfall for cash.
    """
    ticker_to_block = _ticker_to_block_map(blocks)
    risk_tickers = [t for t in target_weights if ticker_to_block.get(t) in RISK_BUDGET_BLOCKS]
    out = dict(target_weights)
    for block_name in RISK_BUDGET_BLOCKS:
        tickers_b = blocks.get(block_name, [])
        if not tickers_b:
            continue
        valid = [t for t in tickers_b if t in row.index and pd.notna(row[t]) and target_weights.get(t, 0) != 0]
        missing = [t for t in tickers_b if t not in valid or target_weights.get(t, 0) == 0]
        w_miss_b = sum(target_weights.get(t, 0) for t in missing)
        if not valid or w_miss_b <= 0:
            for t in tickers_b:
                out[t] = target_weights.get(t, 0) if t in valid else 0.0
            continue
        K = len(valid)
        delta = w_miss_b / K
        for t in tickers_b:
            if t in valid:
                out[t] = target_weights.get(t, 0) + delta
            else:
                out[t] = 0.0
    return out


def _rc_check_after_redist(
    w_risk: dict[str, float],
    cov_df: pd.DataFrame,
    ticker_to_block: dict[str, str],
    rc_block_targets: dict[str, float],
    rc_asset_cap_pct: float | None,
) -> bool:
    """
    True if after redistribution: RC by block is within target ± RB_CORRIDOR_PP and no asset exceeds rc_asset_cap.
    Uses sample cov (ddof=1 style); PC sum = 1.
    """
    cols = [t for t in w_risk if t in cov_df.columns and t in cov_df.index and w_risk.get(t, 0) > 0]
    if not cols:
        return True
    w = np.array([w_risk[t] for t in cols])
    cov = cov_df.reindex(index=cols, columns=cols).fillna(0).values
    var_p = float(np.dot(w, np.dot(cov, w)))
    if var_p <= 1e-16:
        return True
    pc = (w * (cov @ w)) / var_p
    # RC by block (share of variance)
    rc_block: dict[str, float] = {}
    for b in RISK_BUDGET_BLOCKS:
        rc_block[b] = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == b)
    total_rc = sum(rc_block.values())
    if total_rc <= 0:
        return True
    for b in RISK_BUDGET_BLOCKS:
        target = rc_block_targets.get(b)
        if target is None:
            continue
        actual = rc_block[b] / total_rc
        if actual < target - RB_CORRIDOR_PP - 1e-9 or actual > target + RB_CORRIDOR_PP + 1e-9:
            return False
    if rc_asset_cap_pct is not None and rc_asset_cap_pct > 0:
        for i, t in enumerate(cols):
            if pc[i] / total_rc > rc_asset_cap_pct + 1e-9:
                return False
    return True


def portfolio_returns_nan_safe(
    returns_df: pd.DataFrame,
    target_weights: dict[str, float],
    cash_returns: pd.Series,
    *,
    blocks: dict[str, list[str]] | None = None,
    rc_block_targets: dict[str, float] | None = None,
    rc_asset_cap_pct: float | None = None,
    cov_df: pd.DataFrame | None = None,
) -> tuple[pd.Series, pd.DataFrame]:
    """
    NaN-safe portfolio returns.

    Default (blocks=None): R_p,t = sum(w_avail_i * R_i,t) + w_miss * R_cash,t. No renormalization.

    When blocks is provided: within-block equal redistribution first; then if rc_block_targets/cov_df
    (and optionally rc_asset_cap_pct) are provided, RC-gated check: if violated, fall back to
    w_miss-to-cash for that month.

    Returns (portfolio_returns, weights_used DataFrame).
    """
    ticker_to_block = _ticker_to_block_map(blocks) if blocks else {}
    do_rc_check = bool(
        blocks and rc_block_targets and cov_df is not None
        and all(rc_block_targets.get(b) is not None for b in RISK_BUDGET_BLOCKS)
    )
    risk_tickers = [t for b in RISK_BUDGET_BLOCKS for t in blocks.get(b, [])] if blocks else []

    w_df = pd.DataFrame(index=returns_df.index, columns=list(target_weights.keys()), dtype=float)
    common_idx = returns_df.index.intersection(cash_returns.index).sort_values()
    r_p = pd.Series(index=common_idx, dtype=float)

    for t in common_idx:
        row = returns_df.loc[t] if t in returns_df.index else pd.Series(dtype=float)
        if blocks and risk_tickers:
            w_row = _weights_at_t_within_block_redist(row, target_weights, blocks)
            if do_rc_check and cov_df is not None and rc_block_targets:
                w_risk = {k: v for k, v in w_row.items() if k in risk_tickers and v > 0}
                if not _rc_check_after_redist(
                    w_risk, cov_df, ticker_to_block, rc_block_targets, rc_asset_cap_pct
                ):
                    # Fallback: no redistribution, w_miss to cash
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
    return r_p.dropna(), w_df
