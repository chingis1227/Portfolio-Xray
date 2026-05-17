"""
Rebalance: current positions → target weights → list of trades.

Input: current weights (ticker → weight), target weights (ticker → weight), optional NAV.
Optional: threshold_pct — skip trades when max absolute per-ticker weight change (max |Δw_i|,
          in percent points) is below this value; turnover is not used for this gate.
          min_trade_pct — do not emit trades smaller than this percent of portfolio.
Output: list of trades (ticker, direction, delta_weight, optional delta_amount).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Trade:
    """Single rebalance trade."""
    ticker: str
    direction: str  # "buy" | "sell"
    delta_weight: float
    delta_pct: float  # delta_weight * 100
    delta_amount: float | None = None  # if NAV provided


def compute_trades(
    current_weights: dict[str, float],
    target_weights: dict[str, float],
    nav: float | None = None,
    threshold_pct: float | None = None,
    min_trade_pct: float | None = None,
) -> tuple[list[Trade], bool]:
    """
    Compute rebalance trades from current to target weights.

    Weights are shares of portfolio (sum = 1). All tickers from both dicts are considered;
    missing ticker is treated as 0.

    Returns (list of Trade, rebalance_needed).
    If threshold_pct is set and max absolute per-ticker weight deviation (percent points) is below
    threshold_pct, returns ([], False). Portfolio turnover is not used for this gate.
    Trades with |delta_pct| < min_trade_pct are excluded if min_trade_pct is set.
    """
    all_tickers = set(current_weights) | set(target_weights)
    current_weights = {t: current_weights.get(t, 0.0) for t in all_tickers}
    target_weights = {t: target_weights.get(t, 0.0) for t in all_tickers}

    deltas = {t: target_weights[t] - current_weights[t] for t in all_tickers}
    max_abs_delta_pct = max((abs(d) for d in deltas.values()), default=0.0) * 100.0

    if threshold_pct is not None and threshold_pct > 0:
        if max_abs_delta_pct < threshold_pct:
            return [], False

    trades: list[Trade] = []
    for t in sorted(deltas.keys()):
        dw = deltas[t]
        if abs(dw) < 1e-9:
            continue
        dpct = dw * 100.0
        if min_trade_pct is not None and min_trade_pct > 0 and abs(dpct) < min_trade_pct:
            continue
        direction = "buy" if dw > 0 else "sell"
        amount = (nav * dw) if nav is not None and nav > 0 else None
        trades.append(Trade(ticker=t, direction=direction, delta_weight=dw, delta_pct=dpct, delta_amount=amount))

    return trades, True


def rebalance_needed(
    current_weights: dict[str, float],
    target_weights: dict[str, float],
    threshold_pct: float,
) -> bool:
    """
    Return True if rebalance is needed: max absolute per-ticker weight deviation (percent points)
    is at or above threshold_pct. Portfolio turnover is not evaluated.
    """
    _, needed = compute_trades(current_weights, target_weights, threshold_pct=threshold_pct)
    return needed
