"""
Shared data loading and caching: daily → FX → month-end → returns, rf, benchmark, cash.
Used by run_report.py and run_optimization.py to avoid duplicated logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from src.cache import (
    compute_daily_cache_key,
    compute_monthly_cache_key,
    get_daily_cache_path,
    get_monthly_cache_path,
    cache_exists,
    save_cache_meta,
    save_daily_prices,
    save_monthly_data,
    load_daily_prices,
    load_monthly_data,
    get_last_completed_month,
    get_current_date,
)
from src.config import get_asset_currency, resolve_cash_and_rf
from src.data_ecb import fetch_estr
from src.data_fred import (
    fetch_fred_series,
    annual_percent_to_monthly_effective,
    resample_rf_to_month_end,
)
from src.data_yf import download_all, infer_currency_from_ticker
from src.fx import convert_prices_to_investor_currency
from src.resample import to_month_end
from src.returns import simple_returns_df, log_returns_df
from src.utils import logger
from src.windows import get_analysis_end


@dataclass
class MonthlyDataResult:
    """Result of loading or building monthly data."""

    monthly_prices: pd.DataFrame
    monthly_returns: pd.DataFrame
    monthly_log_returns: pd.DataFrame
    rf_monthly: pd.Series
    benchmark_returns: pd.Series
    cash_returns: pd.Series
    fx_series_used: dict[str, pd.Series]
    analysis_end: pd.Timestamp
    analysis_end_str: str
    daily_cache_key: str
    monthly_cache_key: str


def load_monthly_data_shared(
    tickers: list[str],
    benchmark_base_ticker: str,
    cash_proxy_ticker: str,
    rf_source: str,
    investor_currency: str,
    windows_months: list[int],
    assets_meta: dict[str, dict[str, Any]],
    no_cache: bool = False,
    local_benchmark_map: dict[str, str] | None = None,
) -> MonthlyDataResult:
    """
    Load or build monthly prices/returns, rf, benchmark, cash. Uses daily and monthly cache.
    If local_benchmark_map is provided, its values are included in downloaded and converted
    tickers so that Beta_local can use local benchmark returns.
    """
    local_bench_tickers = list(local_benchmark_map.values()) if local_benchmark_map else []
    all_tickers = list(set(tickers + [benchmark_base_ticker, cash_proxy_ticker] + local_bench_tickers))

    currency_by_ticker = {}
    for t in all_tickers:
        currency_by_ticker[t] = get_asset_currency(t, assets_meta, infer_currency_from_ticker(t))

    max_window = max(windows_months)
    end_date = datetime.now()
    start_date = datetime(end_date.year - (max_window // 12) - 2, end_date.month, 1)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    current_date = get_current_date()
    data_month = get_last_completed_month()
    daily_cache_key = compute_daily_cache_key(
        tickers=all_tickers,
        start_date=start_str,
        end_date=end_str,
        data_date=current_date,
    )
    daily_cache_path = get_daily_cache_path(daily_cache_key)
    monthly_cache_key = compute_monthly_cache_key(
        tickers=tickers,
        investor_currency=investor_currency,
        benchmark=benchmark_base_ticker,
        cash_proxy=cash_proxy_ticker,
        rf_source=rf_source,
        windows_months=windows_months,
        data_month=data_month,
        extra_tickers=local_bench_tickers if local_bench_tickers else None,
    )
    monthly_cache_path = get_monthly_cache_path(monthly_cache_key)

    monthly_data = None
    if not no_cache and cache_exists(monthly_cache_path):
        logger.info("Найден месячный кеш, загружаю...")
        monthly_data = load_monthly_data(monthly_cache_path)

    if monthly_data is not None:
        monthly_prices = monthly_data["monthly_prices"]
        monthly_returns = monthly_data["monthly_returns"]
        monthly_log_returns = monthly_data["monthly_log_returns"]
        rf_monthly = monthly_data["rf_monthly"]
        benchmark_returns = monthly_data["benchmark_returns"]
        cash_returns = monthly_data["cash_returns"]
        fx_series_used = monthly_data["fx_series"] or {}
    else:
        daily = None
        if not no_cache and cache_exists(daily_cache_path):
            logger.info("Найден дневной кеш, загружаю...")
            daily = load_daily_prices(daily_cache_path)

        if daily is None:
            logger.info("Загружаю данные из Yahoo Finance...")
            daily_raw = download_all(all_tickers, start_str, end_str, currency_by_ticker)
            daily = {t: df for t, df in daily_raw.items() if not df.empty and "Close" in df.columns}
            save_cache_meta(daily_cache_path, {
                "tickers": all_tickers,
                "start": start_str,
                "end": end_str,
                "data_date": current_date,
            })
            save_daily_prices(daily_cache_path, daily)

        prices_daily = {t: df["Close"] for t, df in daily.items()}
        prices_daily_sub = {t: prices_daily[t] for t in all_tickers if t in prices_daily}
        fx_cache: dict[str, pd.Series | None] = {}
        prices_inv = convert_prices_to_investor_currency(
            prices_daily_sub,
            currency_by_ticker,
            investor_currency,
            start_str,
            end_str,
            fx_cache=fx_cache,
            ffill_fx=True,
        )
        fx_series_used = {k: v for k, v in fx_cache.items() if v is not None}

        monthly_prices = pd.DataFrame({t: to_month_end(s) for t, s in prices_inv.items()})
        monthly_prices = monthly_prices.dropna(how="all")
        monthly_returns = simple_returns_df(monthly_prices)
        monthly_log_returns = log_returns_df(monthly_prices)

        logger.info(f"Загружаю risk-free rate из {rf_source}...")
        if rf_source.startswith("FRED:"):
            series_id = rf_source.split(":", 1)[1]
            rf_annual = fetch_fred_series(series_id, start_str, end_str)
            rf_monthly = annual_percent_to_monthly_effective(rf_annual)
            rf_monthly = resample_rf_to_month_end(rf_monthly)
        elif rf_source.startswith("ECB:") and "€STR" in rf_source:
            rf_annual = fetch_estr(start_str, end_str)
            rf_monthly = annual_percent_to_monthly_effective(rf_annual)
            rf_monthly = resample_rf_to_month_end(rf_monthly)
        else:
            raise ValueError(f"Unsupported rf_source: {rf_source!r}. Use FRED:DTB3 or ECB:€STR.")

        benchmark_returns = monthly_returns.get(benchmark_base_ticker)
        if benchmark_returns is None:
            benchmark_returns = pd.Series(dtype=float)
        else:
            benchmark_returns = benchmark_returns.dropna()
        cash_returns = monthly_returns.get(cash_proxy_ticker)
        if cash_returns is None:
            cash_returns = pd.Series(dtype=float)
        else:
            cash_returns = cash_returns.dropna()

        save_cache_meta(monthly_cache_path, {
            "tickers": tickers,
            "investor_currency": investor_currency,
            "benchmark": benchmark_base_ticker,
            "cash_proxy": cash_proxy_ticker,
            "rf_source": rf_source,
            "windows_months": windows_months,
            "data_month": data_month,
        })
        save_monthly_data(
            monthly_cache_path,
            monthly_prices,
            monthly_returns,
            monthly_log_returns,
            rf_monthly,
            benchmark_returns,
            cash_returns,
            fx_series_used,
        )

    today_ts = pd.Timestamp(datetime.now().date())
    analysis_end = get_analysis_end(monthly_prices.index, today_ts)
    analysis_end_str = analysis_end.strftime("%Y-%m-%d")

    return MonthlyDataResult(
        monthly_prices=monthly_prices,
        monthly_returns=monthly_returns,
        monthly_log_returns=monthly_log_returns,
        rf_monthly=rf_monthly,
        benchmark_returns=benchmark_returns,
        cash_returns=cash_returns,
        fx_series_used=fx_series_used,
        analysis_end=analysis_end,
        analysis_end_str=analysis_end_str,
        daily_cache_key=daily_cache_key,
        monthly_cache_key=monthly_cache_key,
    )
