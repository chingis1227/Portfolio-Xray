"""Read-only Interactive Brokers market data smoke command."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date

from src.data_provider import download_all_prices
from src.data_ibkr import (
    DEFAULT_IBKR_HOST,
    DEFAULT_IBKR_PAPER_PORT,
    IBKRConnectionConfig,
    fetch_historical_daily,
    fetch_latest_quotes,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch read-only quotes from a running TWS / IB Gateway session.")
    parser.add_argument("--symbols", default="VOO", help="Comma-separated symbols, e.g. VOO,SPY,QQQ.")
    parser.add_argument("--host", default=DEFAULT_IBKR_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_IBKR_PAPER_PORT)
    parser.add_argument("--client-id", type=int, default=21)
    parser.add_argument("--exchange", default="SMART")
    parser.add_argument("--currency", default="USD")
    parser.add_argument(
        "--market-data-type",
        type=int,
        default=3,
        choices=[1, 2, 3, 4],
        help="IBKR market data type: 1 live, 2 frozen, 3 delayed, 4 delayed-frozen.",
    )
    parser.add_argument("--snapshot-seconds", type=float, default=3.0)
    parser.add_argument("--history-symbol", help="Also fetch daily historical bars for one symbol.")
    parser.add_argument("--history-duration", default="1 M")
    parser.add_argument("--history-all", action="store_true", help="Fetch daily historical bars for all --symbols.")
    parser.add_argument("--start", default="2026-05-01", help="Start date for --history-all.")
    parser.add_argument("--end", default=date.today().isoformat(), help="End date for --history-all.")
    parser.add_argument(
        "--provider",
        default="ibkr_yfinance_fallback",
        help="Provider for --history-all: yfinance, ibkr, or ibkr_yfinance_fallback.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config = IBKRConnectionConfig(
        host=args.host,
        port=args.port,
        client_id=args.client_id,
        readonly=True,
    )
    symbols = [symbol.strip().upper() for symbol in args.symbols.split(",") if symbol.strip()]
    quotes = fetch_latest_quotes(
        symbols,
        config=config,
        exchange=args.exchange,
        currency=args.currency,
        market_data_type=args.market_data_type,
        snapshot_seconds=args.snapshot_seconds,
    )
    payload: dict[str, object] = {"quotes": [asdict(quote) for quote in quotes]}
    if args.history_symbol:
        history = fetch_historical_daily(
            args.history_symbol,
            config=config,
            exchange=args.exchange,
            currency=args.currency,
            duration=args.history_duration,
        )
        payload["history"] = {
            "symbol": args.history_symbol.upper(),
            "rows": int(len(history)),
            "first_date": None if history.empty else history.index.min().strftime("%Y-%m-%d"),
            "last_date": None if history.empty else history.index.max().strftime("%Y-%m-%d"),
            "last_close": None if history.empty else float(history["Close"].iloc[-1]),
        }
    if args.history_all:
        history_all = download_all_prices(
            symbols,
            args.start,
            args.end,
            {symbol: args.currency for symbol in symbols},
            provider=args.provider,
        )
        payload["history_all"] = {
            "start": args.start,
            "end": args.end,
            "provider_by_ticker": history_all.provider_by_ticker,
            "rows": {symbol: int(len(df)) for symbol, df in history_all.prices.items()},
            "last_close": {
                symbol: None if df.empty else float(df["Close"].iloc[-1])
                for symbol, df in history_all.prices.items()
            },
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
