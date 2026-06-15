"""
Download daily Adj Close via yfinance for assets, benchmarks, FX, and cash proxy.
Returns DataFrames with Date index and Close column; optional currency in attrs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

_YFINANCE_CACHE_CONFIGURED = False
_FETCH_DAILY_MEMORY_CACHE: dict[tuple[str, str, str, str | None], pd.DataFrame] = {}


def clear_fetch_daily_memory_cache() -> None:
    """Clear process-local yfinance result cache; primarily useful for tests."""

    _FETCH_DAILY_MEMORY_CACHE.clear()


def _copy_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    copied = df.copy(deep=True)
    copied.attrs = dict(getattr(df, "attrs", {}) or {})
    return copied


def _configure_yfinance_cache() -> None:
    """Keep yfinance's SQLite caches in the workspace to avoid OS cache path failures."""

    global _YFINANCE_CACHE_CONFIGURED
    if _YFINANCE_CACHE_CONFIGURED:
        return
    cache_dir = Path("cache") / "yfinance"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(yf, "set_tz_cache_location"):
            yf.set_tz_cache_location(str(cache_dir))
        yf_cache = getattr(yf, "cache", None)
        if yf_cache is not None and hasattr(yf_cache, "set_cache_location"):
            yf_cache.set_cache_location(str(cache_dir))
    except Exception:
        # yfinance can still download without its optional persistent caches.
        pass
    _YFINANCE_CACHE_CONFIGURED = True


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
    _configure_yfinance_cache()
    cache_key = (str(ticker), str(start), str(end), currency_override)
    cached = _FETCH_DAILY_MEMORY_CACHE.get(cache_key)
    if cached is not None:
        return _copy_price_frame(cached)
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
    # yfinance can return duplicate level-0 names; keep a single price column.
    if getattr(df.columns, "duplicated", None) is not None and df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()].copy()
    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
    if price_col not in df.columns:
        return pd.DataFrame(columns=["Close"]).rename_axis("Date")
    price_series = df[price_col]
    if isinstance(price_series, pd.DataFrame):
        price_series = price_series.iloc[:, 0]
    df = pd.DataFrame({"Close": pd.to_numeric(price_series, errors="coerce")})
    df = df.dropna(subset=["Close"])
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.rename_axis("Date")
    if currency_override is not None:
        df.attrs["currency"] = currency_override
    _FETCH_DAILY_MEMORY_CACHE[cache_key] = _copy_price_frame(df)
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
