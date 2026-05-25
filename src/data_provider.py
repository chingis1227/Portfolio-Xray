"""Market data provider facade for daily price panels."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from src.utils import logger


MarketDataProvider = Literal["yfinance", "ibkr", "ibkr_yfinance_fallback"]

DEFAULT_MARKET_DATA_PROVIDER: MarketDataProvider = "yfinance"
MARKET_DATA_PROVIDERS = {"yfinance", "ibkr", "ibkr_yfinance_fallback"}


@dataclass(frozen=True)
class ProviderDownloadResult:
    prices: dict[str, pd.DataFrame]
    provider_by_ticker: dict[str, str]


def _download_all_yfinance(
    tickers: list[str],
    start: str,
    end: str,
    currency_by_ticker: dict[str, str] | None = None,
) -> dict[str, pd.DataFrame]:
    from src.data_yf import download_all as download_all_yfinance

    return download_all_yfinance(tickers, start, end, currency_by_ticker)


def normalize_market_data_provider(value: str | None) -> MarketDataProvider:
    raw = str(value or os.getenv("PORTFOLIO_MARKET_DATA_PROVIDER") or DEFAULT_MARKET_DATA_PROVIDER)
    provider = raw.strip().lower().replace("-", "_")
    if provider in {"yf", "yahoo", "yahoo_finance"}:
        provider = "yfinance"
    if provider in {"ib", "ibkr_fallback", "interactive_brokers"}:
        provider = "ibkr_yfinance_fallback"
    if provider not in MARKET_DATA_PROVIDERS:
        raise ValueError(
            "market_data_provider must be one of "
            f"{sorted(MARKET_DATA_PROVIDERS)}, got {value!r}"
        )
    return provider  # type: ignore[return-value]


def download_all_prices(
    tickers: list[str],
    start: str,
    end: str,
    currency_by_ticker: dict[str, str] | None = None,
    *,
    provider: str | None = None,
) -> ProviderDownloadResult:
    resolved = normalize_market_data_provider(provider)
    currency_by_ticker = currency_by_ticker or {}

    if resolved == "yfinance":
        prices = _download_all_yfinance(tickers, start, end, currency_by_ticker)
        return ProviderDownloadResult(prices=prices, provider_by_ticker={t: "yfinance" for t in prices})

    try:
        from src.data_ibkr import download_all as download_all_ibkr
    except Exception as exc:
        if resolved == "ibkr":
            raise
        logger.warning("IBKR provider unavailable; falling back to yfinance: %s", exc)
        prices = _download_all_yfinance(tickers, start, end, currency_by_ticker)
        return ProviderDownloadResult(prices=prices, provider_by_ticker={t: "yfinance" for t in prices})

    ibkr_prices = download_all_ibkr(tickers, start, end, currency_by_ticker)
    prices = {t: df for t, df in ibkr_prices.items() if not df.empty and "Close" in df.columns}
    provider_by_ticker = {t: "ibkr" for t in prices}
    missing = [t for t in tickers if t not in prices]

    if missing and resolved == "ibkr":
        logger.warning("IBKR returned no usable daily prices for tickers: %s", missing)
        return ProviderDownloadResult(prices=prices, provider_by_ticker=provider_by_ticker)

    if missing:
        logger.warning("IBKR missing %d tickers; falling back to yfinance for: %s", len(missing), missing)
        yf_prices = _download_all_yfinance(missing, start, end, currency_by_ticker)
        for ticker, df in yf_prices.items():
            if not df.empty and "Close" in df.columns:
                prices[ticker] = df
                provider_by_ticker[ticker] = "yfinance_fallback"

    return ProviderDownloadResult(prices=prices, provider_by_ticker=provider_by_ticker)
