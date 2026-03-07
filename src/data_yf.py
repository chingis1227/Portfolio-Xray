"""
Download daily Adj Close via yfinance for assets, benchmarks, FX, and cash proxy.
Returns DataFrames with Date index and Close column; optional currency in attrs.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf


def fetch_daily(
    ticker: str,
    start: str,
    end: str,
    currency_override: str | None = None,
) -> pd.DataFrame:
    """
    Download daily data for one ticker.

    Args:
        ticker: Yahoo ticker (e.g. VOO, VWCE.DE, EURUSD=X).
        start: Start date ISO (YYYY-MM-DD).
        end: End date ISO (YYYY-MM-DD).
        currency_override: Optional currency for metadata.

    Returns:
        DataFrame with DatetimeIndex and 'Close' (from Adj Close when available).
        .attrs may contain 'currency'.
    """
    df = yf.download(
        ticker,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if df.empty:
        return pd.DataFrame(columns=["Close"]).rename_axis("Date")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
    df = df[[price_col]].copy()
    df.columns = ["Close"]
    df = df.dropna(subset=["Close"])
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.rename_axis("Date")
    if currency_override is not None:
        df.attrs["currency"] = currency_override
    return df


def infer_currency_from_ticker(ticker: str) -> str:
    """
    Heuristic: .DE -> EUR, .HK -> HKD, .L -> GBP, etc. Otherwise USD.
    """
    t = ticker.upper()
    if t.endswith(".DE") or t.endswith(".PA") or t.endswith(".MC"):
        return "EUR"
    if t.endswith(".HK"):
        return "HKD"
    if t.endswith(".L"):
        return "GBP"
    if t.endswith(".T") or t.endswith(".TWO"):
        return "TWD"
    if "=X" in t or "USD" in t or "EUR" in t:
        return "USD"  # FX ticker, treat as USD for display
    return "USD"


def download_all(
    tickers: list[str],
    start: str,
    end: str,
    currency_by_ticker: dict[str, str] | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Download daily Adj Close for all tickers. currency_by_ticker overrides inferred currency.
    """
    currency_by_ticker = currency_by_ticker or {}
    out: dict[str, pd.DataFrame] = {}
    for t in tickers:
        cur = currency_by_ticker.get(t) or infer_currency_from_ticker(t)
        out[t] = fetch_daily(t, start, end, currency_override=cur)
    return out
