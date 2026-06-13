"""
FX conversion to investor currency. Explicit rules per metrics_specification.md and RULES.md:
- EURUSD=X means 1 EUR in USD.
- P_USD = P_EUR * FX(EURUSD=X); P_EUR = P_USD / FX(EURUSD=X).
- If investor != USD: convert via USD: P_USD = P_asset * FX(asset_ccyUSD), P_investor = P_USD / FX(investor_ccyUSD).
FX daily may be forward-filled; asset returns are never interpolated.
"""
from __future__ import annotations

import pandas as pd

from src.data_yf import fetch_daily

# Yahoo FX tickers: (ticker, needs_inversion)
# XXXUSD=X = 1 XXX in USD (no inversion needed)
# USDXXX=X or XXX=X = 1 USD in XXX (needs inversion to get USD per 1 XXX)
FX_TICKER_CONFIG: dict[str, tuple[str, bool]] = {
    "EUR": ("EURUSD=X", False),   # 1 EUR = ... USD
    "GBP": ("GBPUSD=X", False),   # 1 GBP = ... USD
    "JPY": ("JPY=X", True),       # USD/JPY: 1 USD = ... JPY → invert
    "CHF": ("USDCHF=X", True),    # USD/CHF: 1 USD = ... CHF → invert
    "HKD": ("USDHKD=X", True),    # USD/HKD: 1 USD = ... HKD → invert
    "CAD": ("USDCAD=X", True),    # USD/CAD: 1 USD = ... CAD → invert
    "AUD": ("AUDUSD=X", False),   # 1 AUD = ... USD
}


def get_fx_series_usd_per_unit(currency: str, start: str, end: str) -> pd.Series | None:
    """
    Return daily FX series: units of USD per 1 unit of currency.
    So price_USD = price_ccy * this_series.
    If FX ticker not available in required orientation, uses inverse pair and inverts.
    """
    c = currency.upper()
    if c == "USD":
        return None
    config = FX_TICKER_CONFIG.get(c)
    if not config:
        return None
    ticker, needs_inversion = config
    df = fetch_daily(ticker, start, end, currency_override=None)
    if df.empty or "Close" not in df.columns:
        return None
    s = df["Close"]
    if needs_inversion:
        s = 1.0 / s
    return s.rename("FX")


def convert_prices_to_investor_currency(
    prices_by_ticker: dict[str, pd.Series],
    currency_by_ticker: dict[str, str],
    investor_currency: str,
    start: str,
    end: str,
    fx_cache: dict[str, pd.Series | None] | None = None,
    ffill_fx: bool = True,
) -> dict[str, pd.Series]:
    """
    Convert each price series to investor_currency using explicit rules.
    - Asset EUR, investor USD: P_USD = P_EUR * FX(EURUSD=X).
    - Asset USD, investor EUR: P_EUR = P_USD / FX(EURUSD=X).
    - If investor != USD: P_USD = P_asset * FX(asset_ccyUSD); P_investor = P_USD / FX(investor_ccyUSD).
    FX is aligned by date and optionally forward-filled; asset prices are not interpolated.
    """
    inv = investor_currency.upper()
    cache = fx_cache if fx_cache is not None else {}
    out: dict[str, pd.Series] = {}

    def get_fx(ccy: str) -> pd.Series | None:
        if ccy == "USD":
            return None
        if ccy not in cache:
            cache[ccy] = get_fx_series_usd_per_unit(ccy, start, end)
        return cache[ccy]

    for ticker, prices in prices_by_ticker.items():
        asset_ccy = (currency_by_ticker.get(ticker) or "USD").upper()
        if asset_ccy == inv:
            out[ticker] = prices.copy()
            continue
        # Step 1: to USD. P_USD = P_asset * FX(asset_ccy) with FX = USD per 1 unit asset_ccy
        if asset_ccy == "USD":
            p_usd = prices.copy()
        else:
            fx_asset = get_fx(asset_ccy)
            if fx_asset is None:
                raise ValueError(
                    f"No FX available for {asset_ccy}. Cannot convert {ticker} to investor currency."
                )
            fx_aligned = fx_asset.reindex(prices.index).ffill() if ffill_fx else fx_asset.reindex(prices.index)
            p_usd = (prices * fx_aligned).dropna()
        if inv == "USD":
            out[ticker] = p_usd
            continue
        # Step 2: USD to investor. P_investor = P_USD / FX(inv_ccy); FX = USD per 1 inv_ccy
        fx_inv = get_fx(inv)
        if fx_inv is None:
            raise ValueError(
                f"No FX available for investor currency {inv}. Fail fast."
            )
        fx_inv_aligned = fx_inv.reindex(p_usd.index).ffill() if ffill_fx else fx_inv.reindex(p_usd.index)
        p_inv = (p_usd / fx_inv_aligned).dropna()
        out[ticker] = p_inv
    return out
