"""Interactive Brokers market data helpers.

This module is intentionally read-only: it requests contract details, market
data, and historical bars through an already running TWS / IB Gateway session.
It does not place, modify, or cancel orders.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from math import isfinite
from typing import Any, Callable, Iterable

import pandas as pd


DEFAULT_IBKR_HOST = "127.0.0.1"
DEFAULT_IBKR_PAPER_PORT = 7497
DEFAULT_IBKR_LIVE_PORT = 7496


class IBKRDependencyError(RuntimeError):
    """Raised when the optional IBKR client dependency is unavailable."""


class IBKRConnectionError(RuntimeError):
    """Raised when TWS / IB Gateway cannot be reached."""


@dataclass(frozen=True)
class IBKRConnectionConfig:
    host: str = DEFAULT_IBKR_HOST
    port: int = DEFAULT_IBKR_PAPER_PORT
    client_id: int = 21
    timeout: float = 8.0
    readonly: bool = True


@dataclass(frozen=True)
class IBKRQuote:
    symbol: str
    exchange: str
    currency: str
    price: float | None
    price_source: str | None
    bid: float | None
    ask: float | None
    last: float | None
    close: float | None
    delayed: bool


def _load_ib_insync() -> tuple[type[Any], Callable[..., Any]]:
    try:
        from ib_insync import IB, Stock
    except ImportError as exc:
        raise IBKRDependencyError(
            "ib_insync is required for IBKR market data. Install it with: pip install ib_insync"
        ) from exc
    return IB, Stock


def _finite_float(value: Any) -> float | None:
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return None
    return value_float if isfinite(value_float) else None


def _midpoint(bid: float | None, ask: float | None) -> float | None:
    if bid is None or ask is None:
        return None
    if bid <= 0 or ask <= 0 or ask < bid:
        return None
    return (bid + ask) / 2.0


def _select_price(ticker: Any) -> tuple[float | None, str | None]:
    bid = _finite_float(getattr(ticker, "bid", None))
    ask = _finite_float(getattr(ticker, "ask", None))
    midpoint = _midpoint(bid, ask)
    if midpoint is not None:
        return midpoint, "mid"

    for attr in ("marketPrice", "last", "close"):
        value = getattr(ticker, attr, None)
        if callable(value):
            value = value()
        price = _finite_float(value)
        if price is not None and price > 0:
            return price, attr
    return None, None


def _connect(config: IBKRConnectionConfig, ib_factory: Callable[[], Any] | None = None) -> Any:
    if ib_factory is not None:
        ib = ib_factory()
    else:
        IB, _ = _load_ib_insync()
        ib = IB()
    try:
        ib.connect(
            config.host,
            config.port,
            clientId=config.client_id,
            timeout=config.timeout,
            readonly=config.readonly,
        )
    except TypeError:
        ib.connect(config.host, config.port, clientId=config.client_id, timeout=config.timeout)
    except Exception as exc:
        raise IBKRConnectionError(
            f"Could not connect to IBKR at {config.host}:{config.port}. "
            "Open and log in to TWS / IB Gateway first."
        ) from exc
    return ib


def _stock_contract(symbol: str, exchange: str, currency: str, stock_factory: Callable[..., Any] | None) -> Any:
    if stock_factory is not None:
        factory = stock_factory
    else:
        _, factory = _load_ib_insync()
    return factory(symbol, exchange, currency)


def fetch_latest_quotes(
    symbols: Iterable[str],
    *,
    config: IBKRConnectionConfig | None = None,
    exchange: str = "SMART",
    currency: str = "USD",
    market_data_type: int = 3,
    snapshot_seconds: float = 3.0,
    ib_factory: Callable[[], Any] | None = None,
    stock_factory: Callable[..., Any] | None = None,
) -> list[IBKRQuote]:
    """Fetch latest quotes from TWS / IB Gateway.

    ``market_data_type`` follows IBKR values: 1 live, 2 frozen, 3 delayed,
    4 delayed-frozen. Delayed quotes are the safer default for first setup.
    """
    config = config or IBKRConnectionConfig()
    ib = _connect(config, ib_factory=ib_factory)
    quotes: list[IBKRQuote] = []
    try:
        if hasattr(ib, "reqMarketDataType"):
            ib.reqMarketDataType(market_data_type)
        for raw_symbol in symbols:
            symbol = raw_symbol.strip().upper()
            if not symbol:
                continue
            contract = _stock_contract(symbol, exchange, currency, stock_factory)
            qualified = ib.qualifyContracts(contract)
            contract = qualified[0] if qualified else contract
            ticker = ib.reqMktData(contract, "", False, False)
            ib.sleep(snapshot_seconds)
            price, price_source = _select_price(ticker)
            quotes.append(
                IBKRQuote(
                    symbol=symbol,
                    exchange=exchange,
                    currency=currency,
                    price=price,
                    price_source=price_source,
                    bid=_finite_float(getattr(ticker, "bid", None)),
                    ask=_finite_float(getattr(ticker, "ask", None)),
                    last=_finite_float(getattr(ticker, "last", None)),
                    close=_finite_float(getattr(ticker, "close", None)),
                    delayed=market_data_type in {3, 4},
                )
            )
            if hasattr(ib, "cancelMktData"):
                ib.cancelMktData(contract)
    finally:
        ib.disconnect()
    return quotes


def fetch_historical_daily(
    symbol: str,
    *,
    config: IBKRConnectionConfig | None = None,
    exchange: str = "SMART",
    currency: str = "USD",
    duration: str = "1 M",
    end: str | None = None,
    what_to_show: str = "TRADES",
    use_rth: bool = True,
    ib_factory: Callable[[], Any] | None = None,
    stock_factory: Callable[..., Any] | None = None,
) -> pd.DataFrame:
    """Fetch daily historical bars as a Date-indexed ``Close`` DataFrame."""
    config = config or IBKRConnectionConfig()
    ib = _connect(config, ib_factory=ib_factory)
    try:
        contract = _stock_contract(symbol.strip().upper(), exchange, currency, stock_factory)
        qualified = ib.qualifyContracts(contract)
        contract = qualified[0] if qualified else contract
        bars = ib.reqHistoricalData(
            contract,
            endDateTime=_ibkr_end_datetime(end),
            durationStr=duration,
            barSizeSetting="1 day",
            whatToShow=what_to_show,
            useRTH=use_rth,
            formatDate=1,
        )
    finally:
        ib.disconnect()

    rows: list[dict[str, Any]] = []
    for bar in bars:
        bar_date = getattr(bar, "date", None)
        if isinstance(bar_date, datetime):
            bar_date = bar_date.date()
        if not isinstance(bar_date, date):
            bar_date = pd.to_datetime(bar_date).date()
        rows.append({"Date": pd.Timestamp(bar_date), "Close": _finite_float(getattr(bar, "close", None))})

    if not rows:
        return pd.DataFrame(columns=["Close"]).rename_axis("Date")
    df = pd.DataFrame(rows).dropna(subset=["Close"])
    df = df.set_index("Date").sort_index()
    return df.rename_axis("Date")


def _ibkr_end_datetime(end: str | None) -> str:
    if not end:
        return ""
    ts = pd.Timestamp(end)
    return ts.strftime("%Y%m%d 23:59:59")


def _duration_for_range(start: str, end: str) -> str:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    days = max(1, int((end_ts - start_ts).days) + 5)
    if days <= 365:
        return f"{days} D"
    years = int(days / 365) + 1
    return f"{years} Y"


def download_all(
    tickers: list[str],
    start: str,
    end: str,
    currency_by_ticker: dict[str, str] | None = None,
    *,
    config: IBKRConnectionConfig | None = None,
    exchange: str = "SMART",
    what_to_show: str = "ADJUSTED_LAST",
) -> dict[str, pd.DataFrame]:
    """Download daily historical prices for many tickers through IBKR."""
    currency_by_ticker = currency_by_ticker or {}
    duration = _duration_for_range(start, end)
    out: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        currency = currency_by_ticker.get(ticker) or "USD"
        try:
            df = fetch_historical_daily(
                ticker,
                config=config,
                exchange=exchange,
                currency=currency,
                duration=duration,
                end=None if what_to_show == "ADJUSTED_LAST" else end,
                what_to_show=what_to_show,
            )
            if not df.empty:
                start_ts = pd.Timestamp(start)
                end_ts = pd.Timestamp(end)
                df = df[(df.index >= start_ts) & (df.index <= end_ts)]
                df.attrs["currency"] = currency
            out[ticker] = df
        except Exception:
            out[ticker] = pd.DataFrame(columns=["Close"]).rename_axis("Date")
    return out
