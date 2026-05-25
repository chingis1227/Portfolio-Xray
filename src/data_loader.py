"""
Shared data loading and caching: daily → FX → resampled levels → returns, rf, benchmark, cash.

``monthly_prices`` / ``monthly_returns`` / ``rf_monthly`` names are historical: when
``returns_frequency`` is weekly or daily, these panels use that index cadence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from src.cache import (
    compute_asset_metadata_fingerprint,
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
from src.data_fred import fetch_fred_series
from src.data_provider import download_all_prices, normalize_market_data_provider
from src.data_yf import infer_currency_from_ticker
from src.fx import convert_prices_to_investor_currency
from src.returns_frequency import (
    ReturnsFrequency,
    build_levels_and_returns_from_daily_prices,
    main_metrics_frequency_override_note,
    resolve_returns_frequencies,
    rf_series_annual_pct_to_returns_frequency,
)
from src.utils import logger
from src.windows import get_analysis_end, truncate_to_analysis_end


@dataclass
class MonthlyDataResult:
    """Loaded return panel. Field names are legacy; index follows ``returns_frequency``."""

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
    returns_frequency: ReturnsFrequency = "monthly"
    configured_returns_frequency: ReturnsFrequency = "monthly"


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
    returns_frequency: str | None = None,
    data_provider: str | None = None,
) -> MonthlyDataResult:
    """
    Load or build prices/returns, rf, benchmark, cash at the main-metrics cadence (monthly).

    ``returns_frequency`` in config may be weekly/daily for disclosure only; the returned
    panel always follows ``MAIN_METRICS_RETURNS_FREQUENCY``.

    Uses daily and panel cache. If local_benchmark_map is provided, its values are included
    in downloaded and converted tickers so Beta_local can use local benchmark returns.
    """
    freq_res = resolve_returns_frequencies(returns_frequency)
    rf_mode = freq_res.main_metrics
    resolved_data_provider = normalize_market_data_provider(data_provider)
    if freq_res.forced_to_monthly:
        logger.warning(main_metrics_frequency_override_note(freq_res))
    local_bench_tickers = list(local_benchmark_map.values()) if local_benchmark_map else []
    all_tickers = list(set(tickers + [benchmark_base_ticker, cash_proxy_ticker] + local_bench_tickers))

    currency_by_ticker = {}
    for t in all_tickers:
        currency_by_ticker[t] = get_asset_currency(t, assets_meta, infer_currency_from_ticker(t))
    asset_metadata_fingerprint = compute_asset_metadata_fingerprint(currency_by_ticker)

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
        data_provider=resolved_data_provider,
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
        asset_metadata_fingerprint=asset_metadata_fingerprint,
        extra_tickers=local_bench_tickers if local_bench_tickers else None,
        returns_frequency=rf_mode,
        data_provider=resolved_data_provider,
    )
    monthly_cache_path = get_monthly_cache_path(monthly_cache_key)

    monthly_data = None
    if not no_cache and cache_exists(monthly_cache_path):
        meta = None
        try:
            from src.cache import load_cache_meta

            meta = load_cache_meta(monthly_cache_path)
        except Exception:
            meta = None
        cfg_meta = (meta or {}).get("config") or {}
        cached_freq = str(cfg_meta.get("returns_frequency", "monthly")).strip().lower()
        if cached_freq == rf_mode:
            logger.info("Return panel cache found; loading...")
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
            logger.info("Daily cache found; loading...")
            daily = load_daily_prices(daily_cache_path)

        if daily is None:
            logger.info("Loading data via market data provider: %s", resolved_data_provider)
            provider_result = download_all_prices(
                all_tickers,
                start_str,
                end_str,
                currency_by_ticker,
                provider=resolved_data_provider,
            )
            daily_raw = provider_result.prices
            daily = {t: df for t, df in daily_raw.items() if not df.empty and "Close" in df.columns}
            save_cache_meta(
                daily_cache_path,
                {
                    "tickers": all_tickers,
                    "start": start_str,
                    "end": end_str,
                    "data_date": current_date,
                    "data_provider": resolved_data_provider,
                    "provider_by_ticker": provider_result.provider_by_ticker,
                },
            )
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

        monthly_prices, monthly_returns, monthly_log_returns = build_levels_and_returns_from_daily_prices(
            prices_inv,
            freq=rf_mode,
            tickers=all_tickers,
        )

        logger.info(f"Loading risk-free rate from {rf_source}...")
        if rf_source.startswith("FRED:"):
            series_id = rf_source.split(":", 1)[1]
            rf_annual = fetch_fred_series(series_id, start_str, end_str)
            rf_monthly = rf_series_annual_pct_to_returns_frequency(rf_annual, freq=rf_mode)
        elif rf_source.startswith("ECB:") and "€STR" in rf_source:
            rf_annual = fetch_estr(start_str, end_str)
            rf_monthly = rf_series_annual_pct_to_returns_frequency(rf_annual, freq=rf_mode)
        else:
            raise ValueError(f"Unsupported rf_source: {rf_source!r}. Use FRED:DTB3 or ECB:€STR.")

        # Align rf to returns index intersection (forward-fill stale RF stamps)
        if not monthly_returns.empty:
            full_idx = monthly_returns.sort_index().index
            rf_monthly = rf_monthly.reindex(full_idx).ffill()

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

        save_cache_meta(
            monthly_cache_path,
            {
                "tickers": tickers,
                "investor_currency": investor_currency,
                "benchmark": benchmark_base_ticker,
                "cash_proxy": cash_proxy_ticker,
                "rf_source": rf_source,
                "windows_months": windows_months,
                "data_month": data_month,
                "asset_metadata_fingerprint": asset_metadata_fingerprint,
                "asset_currency_by_ticker": currency_by_ticker,
                "returns_frequency": rf_mode,
                "data_provider": resolved_data_provider,
            },
        )
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
        returns_frequency=rf_mode,
        configured_returns_frequency=freq_res.configured,
    )


def load_daily_asset_returns_shared(
    *,
    tickers: list[str],
    benchmark_base_ticker: str,
    cash_proxy_ticker: str,
    investor_currency: str,
    windows_months: list[int],
    assets_meta: dict[str, dict[str, Any]],
    daily_cache_key: str,
    analysis_end: pd.Timestamp,
    no_cache: bool = False,
    local_benchmark_map: dict[str, str] | None = None,
    data_provider: str | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Daily simple returns in investor currency for portfolio tickers and cash proxy.

    Uses the same daily price cache as ``load_monthly_data_shared``. Rows are truncated to
    ``analysis_end`` for analysis-effective tail-risk panels.
    """
    local_bench_tickers = list(local_benchmark_map.values()) if local_benchmark_map else []
    resolved_data_provider = normalize_market_data_provider(data_provider)
    all_tickers = list(
        dict.fromkeys(list(tickers) + [benchmark_base_ticker, cash_proxy_ticker] + local_bench_tickers)
    )
    currency_by_ticker = {}
    for t in all_tickers:
        currency_by_ticker[t] = get_asset_currency(t, assets_meta, infer_currency_from_ticker(t))

    max_window = max(windows_months)
    end_date = datetime.now()
    start_date = datetime(end_date.year - (max_window // 12) - 2, end_date.month, 1)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    daily_cache_path = get_daily_cache_path(daily_cache_key)
    daily = None
    if not no_cache and cache_exists(daily_cache_path):
        logger.info("Daily cache found for tail-risk panel; loading...")
        daily = load_daily_prices(daily_cache_path)

    if daily is None:
        logger.info("Loading daily prices for tail-risk panel via market data provider: %s", resolved_data_provider)
        provider_result = download_all_prices(
            all_tickers,
            start_str,
            end_str,
            currency_by_ticker,
            provider=resolved_data_provider,
        )
        daily_raw = provider_result.prices
        daily = {t: df for t, df in daily_raw.items() if not df.empty and "Close" in df.columns}
        save_cache_meta(
            daily_cache_path,
            {
                "tickers": all_tickers,
                "start": start_str,
                "end": end_str,
                "data_date": get_current_date(),
                "data_provider": resolved_data_provider,
                "provider_by_ticker": provider_result.provider_by_ticker,
            },
        )
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
    _, daily_returns, _ = build_levels_and_returns_from_daily_prices(
        prices_inv,
        freq="daily",
        tickers=all_tickers,
    )
    daily_returns = truncate_to_analysis_end(daily_returns, analysis_end)
    cash_col = cash_proxy_ticker if cash_proxy_ticker in daily_returns.columns else None
    if cash_col is not None:
        cash_returns_daily = daily_returns[cash_col].dropna()
    else:
        cash_returns_daily = pd.Series(0.0, index=daily_returns.index)
    asset_cols = [t for t in tickers if t in daily_returns.columns]
    return daily_returns[asset_cols].copy(), cash_returns_daily
