"""Explicit real-cash holdings (e.g. Cash USD): zero return, no market price series."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
import pandas as pd

# Flat level for synthetic price panel (return = 0 each period).
REAL_CASH_LEVEL: float = 1.0


def is_real_cash_ticker(ticker: str) -> bool:
    """
    True for user-entered bank cash labels (not ETF cash proxies like BIL).

    Accepts ``CASH``, ``CASH USD``, ``Cash USD``, ``Cash EUR``, etc.
    """
    token = str(ticker or "").strip()
    if not token:
        return False
    upper = token.upper()
    if upper == "CASH":
        return True
    if upper.startswith("CASH "):
        return True
    lower = token.lower()
    return lower.startswith("cash ") and len(token.split()) >= 2


def collect_real_cash_tickers(
    *,
    tickers: Iterable[str] | None = None,
    weights: Mapping[str, float] | None = None,
) -> list[str]:
    """Ordered unique real-cash tickers from ticker lists and positive-weight keys."""
    seen: set[str] = set()
    out: list[str] = []

    def _add(raw: str) -> None:
        label = str(raw or "").strip()
        if not label or not is_real_cash_ticker(label):
            return
        key = label.upper()
        if key in seen:
            return
        seen.add(key)
        out.append(label)

    for raw in tickers or []:
        _add(str(raw))
    for raw, value in (weights or {}).items():
        try:
            positive = float(value) > 0
        except (TypeError, ValueError):
            positive = False
        if positive:
            _add(str(raw))
    return out


def partition_market_data_tickers(tickers: list[str]) -> tuple[list[str], list[str]]:
    """Split into (download_tickers, real_cash_tickers) preserving order."""
    download: list[str] = []
    real_cash: list[str] = []
    for t in tickers:
        label = str(t).strip()
        if not label:
            continue
        if is_real_cash_ticker(label):
            if label not in real_cash:
                real_cash.append(label)
        else:
            download.append(label)
    return download, real_cash


def inject_real_cash_return_panels(
    prices: pd.DataFrame,
    simple_returns: pd.DataFrame,
    log_returns: pd.DataFrame,
    real_cash_tickers: list[str],
    *,
    level: float = REAL_CASH_LEVEL,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Append flat level and zero simple/log returns on the panel index."""
    if not real_cash_tickers:
        return prices, simple_returns, log_returns

    if simple_returns is not None and not simple_returns.empty:
        index = simple_returns.index
    elif prices is not None and not prices.empty:
        index = prices.index
    else:
        return prices, simple_returns, log_returns

    prices_out = prices.copy() if prices is not None else pd.DataFrame()
    simple_out = simple_returns.copy() if simple_returns is not None else pd.DataFrame(index=index)
    log_out = log_returns.copy() if log_returns is not None else pd.DataFrame(index=index)

    for label in real_cash_tickers:
        token = str(label).strip()
        if not token:
            continue
        prices_out[token] = float(level)
        simple_out[token] = 0.0
        log_out[token] = 0.0

    return prices_out.sort_index(), simple_out.sort_index(), log_out.sort_index()


def real_cash_holdings_from_weights(weights: Mapping[str, float]) -> list[dict[str, Any]]:
    """Structured holdings for ``analysis_setup.cash_handling``."""
    rows: list[dict[str, Any]] = []
    for ticker in collect_real_cash_tickers(weights=weights):
        try:
            w = float(weights.get(ticker, 0.0))
        except (TypeError, ValueError):
            w = 0.0
        if w > 0:
            rows.append({"ticker": ticker, "weight": round(w, 3)})
    return rows


def enrich_cash_handling(
    cash_handling: dict[str, Any],
    *,
    resolved_weights: Mapping[str, float],
    cash_proxy_ticker: str | None,
) -> dict[str, Any]:
    """Extend ``cash_handling`` with real-cash disclosure (does not alter cash proxy)."""
    holdings = real_cash_holdings_from_weights(resolved_weights)
    total = float(sum(float(row["weight"]) for row in holdings))
    proxy = str(cash_proxy_ticker or "").strip()
    proxy_upper = proxy.upper()
    distinct = bool(
        holdings
        and all(str(row["ticker"]).strip().upper() != proxy_upper for row in holdings)
    )
    out = dict(cash_handling)
    out["real_cash_holdings"] = holdings
    out["real_cash_weight_total"] = round(total, 3) if holdings else 0.0
    out["real_cash_distinct_from_cash_proxy"] = distinct
    if holdings:
        out["real_cash_return_assumption"] = "zero_return_zero_volatility_no_price_download"
    return out


__all__ = [
    "REAL_CASH_LEVEL",
    "collect_real_cash_tickers",
    "enrich_cash_handling",
    "inject_real_cash_return_panels",
    "is_real_cash_ticker",
    "partition_market_data_tickers",
    "real_cash_holdings_from_weights",
]
