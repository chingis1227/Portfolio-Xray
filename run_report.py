"""
Portfolio Metrics Standard — single entry script.
Produces CSV outputs and persists all input series. Run from project root: python run_report.py

All portfolio assumptions and constraints are controlled from config.yml (single configuration layer).
When the user changes variables in config.yml, re-running this script recalculates all portfolio
calculations, reports, and exported files consistently without manual code edits.

Caching:
  - Daily cache: raw prices, invalidated daily
  - Monthly cache: prices/returns/rf, invalidated when month changes or config changes
  
CLI options:
  --no-cache     Ignore cache, download fresh data
  --clear-cache  Clear all cached data before running
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.cache import (
    compute_daily_cache_key,
    compute_monthly_cache_key,
    get_daily_cache_path,
    get_monthly_cache_path,
    cache_exists,
    save_cache_meta,
    save_daily_prices,
    load_daily_prices,
    save_monthly_data,
    load_monthly_data,
    get_last_completed_month,
    get_current_date,
    cleanup_old_cache,
    clear_all_cache,
)
from src.config import (
    load_validated_config,
    load_assets_metadata,
    get_asset_currency,
    resolve_cash_and_rf,
    resolve_local_benchmarks,
    get_mar_from_config,
)
from src.config_schema import ConfigValidationError, PortfolioConfig
from src.data_ecb import fetch_estr
from src.data_fred import (
    fetch_fred_series,
    annual_percent_to_monthly_effective,
    resample_rf_to_month_end,
)
from src.data_yf import download_all, infer_currency_from_ticker
from src.fx import convert_prices_to_investor_currency, get_fx_series_usd_per_unit
from src.io_export import (
    ensure_output_dir,
    export_asset_metrics_csv,
    export_portfolio_metrics_csv,
    export_rc_vol_csv,
    export_run_metadata,
    export_correlation_matrix_csv,
    save_inputs,
)
from src.metrics_asset import asset_metrics_one_window
from src.metrics_portfolio import portfolio_metrics_one_window
from src.portfolio_dynamic import portfolio_returns_nan_safe, dynamic_weights_matrix
from src.resample import to_month_end
from src.returns import simple_returns, log_returns, simple_returns_df, log_returns_df
from src.risk_contrib import rc_vol_window, cov_matrix_monthly
from src.utils import setup_logging, warn_skipped_asset, info_data_summary, logger
from src.windows import get_analysis_end, slice_window


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Portfolio Metrics Standard — calculate and export portfolio metrics"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore cache, download fresh data from sources",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear all cached data before running",
    )
    return parser.parse_args()


def build_derived_assumptions(
    cfg: PortfolioConfig,
    cash_proxy_ticker: str,
    rf_source: str,
    local_benchmark_map: dict[str, str],
    analysis_end: str,
    windows_months: list[int],
) -> dict:
    """
    Build dictionary of derived assumptions used in the run.
    These are values computed from config (not directly specified).
    """
    return {
        "resolved_cash_proxy_ticker": cash_proxy_ticker,
        "resolved_rf_source": rf_source,
        "resolved_local_benchmark_map": local_benchmark_map,
        "analysis_end_date": analysis_end,
        "windows_months": windows_months,
        "total_weight_sum": sum(cfg.weights.values()),
        "weight_to_cash": max(0, 1.0 - sum(cfg.weights.values())),
        "mar_source": "rf_monthly" if cfg.min_acceptable_return is None else "config",
        "mar_annual_value": cfg.min_acceptable_return,
    }


def main() -> None:
    args = parse_args()
    setup_logging()
    run_timestamp = datetime.now().isoformat()
    
    if args.clear_cache:
        clear_all_cache()
    
    # =========================================================================
    # STEP 1: Load and validate configuration
    # =========================================================================
    try:
        cfg = load_validated_config()
    except ConfigValidationError as e:
        logger.error(f"Ошибка валидации конфигурации: {e}")
        raise SystemExit(1)
    
    # Log pending config items
    if cfg.pending_fields:
        logger.info(f"Поля конфигурации, ожидающие ввода пользователя: {cfg.pending_fields}")
    
    assets_meta = load_assets_metadata()
    
    # =========================================================================
    # STEP 2: Extract config values (all from centralized config)
    # =========================================================================
    investor_currency = cfg.investor_currency
    tickers = cfg.tickers
    weights = cfg.weights
    benchmark_base_ticker = cfg.benchmark_base_ticker
    windows_months = cfg.windows_months
    output_dir = ensure_output_dir(Path(cfg.output_dir))
    
    # Resolve defaults based on investor currency
    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    
    # Get MAR from config (None => use rf_monthly in calculations)
    mar_annual = get_mar_from_config(cfg)
    mar_monthly = mar_annual / 12 if mar_annual is not None else None
    
    # Resolve local benchmarks: built-in defaults + config overrides
    config_local_override = cfg.local_benchmark_map or {}
    local_benchmark_map = resolve_local_benchmarks(
        tickers, config_local_override, base_benchmark=benchmark_base_ticker
    )
    
    logger.info(f"Валюта инвестора: {investor_currency}")
    logger.info(f"Базовый бенчмарк: {benchmark_base_ticker}")
    logger.info(f"Cash proxy: {cash_proxy_ticker}")
    logger.info(f"Risk-free source: {rf_source}")
    logger.info(f"Локальные бенчмарки: {local_benchmark_map}")
    
    if cfg.target_nominal_return_annual is not None:
        logger.info(f"Целевая доходность: {cfg.target_nominal_return_annual:.2%}")

    # =========================================================================
    # STEP 3: Download data (with caching)
    # =========================================================================
    
    # All tickers to download: assets + benchmark + cash + all local benchmark proxies
    all_tickers = list(set(
        tickers + [benchmark_base_ticker, cash_proxy_ticker] + list(local_benchmark_map.values())
    ))
    currency_by_ticker = {}
    for t in all_tickers:
        currency_by_ticker[t] = get_asset_currency(t, assets_meta, infer_currency_from_ticker(t))

    # Date range: enough for longest window (e.g. 120 months + 24 buffer)
    max_window = max(windows_months)
    end_date = datetime.now()
    start_date = datetime(end_date.year - (max_window // 12) - 2, end_date.month, 1)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # --- Cache keys ---
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
    )
    monthly_cache_path = get_monthly_cache_path(monthly_cache_key)
    
    logger.info(f"Ключ дневного кеша: {daily_cache_key}")
    logger.info(f"Ключ месячного кеша: {monthly_cache_key} (месяц данных: {data_month})")

    # --- Try to load monthly cache (fastest path) ---
    monthly_data = None
    if not args.no_cache and cache_exists(monthly_cache_path):
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
        # --- Try to load daily cache ---
        daily = None
        if not args.no_cache and cache_exists(daily_cache_path):
            logger.info("Найден дневной кеш, загружаю...")
            daily = load_daily_prices(daily_cache_path)
        
        if daily is None:
            logger.info("Загружаю данные из Yahoo Finance...")
            daily_raw = download_all(all_tickers, start_str, end_str, currency_by_ticker)
            daily = {t: df for t, df in daily_raw.items() if not df.empty and "Close" in df.columns}
            
            # Save daily cache
            save_cache_meta(daily_cache_path, {
                "tickers": all_tickers,
                "start": start_str,
                "end": end_str,
                "data_date": current_date,
            })
            save_daily_prices(daily_cache_path, daily)
        
        # Prices as dict of Series (Close)
        prices_daily = {t: df["Close"] for t, df in daily.items()}

        # Convert to investor currency (only asset + benchmark + cash we use)
        used_tickers = list(set(tickers + [benchmark_base_ticker, cash_proxy_ticker]))
        prices_daily_sub = {t: prices_daily[t] for t in used_tickers if t in prices_daily}
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

        # Resample to month-end
        monthly_prices = pd.DataFrame({t: to_month_end(s) for t, s in prices_inv.items()})
        monthly_prices = monthly_prices.dropna(how="all")

        # Monthly returns (simple and log)
        monthly_returns = simple_returns_df(monthly_prices)
        monthly_log_returns = log_returns_df(monthly_prices)

        # Risk-free: FRED (USD) or ECB €STR (EUR) -> monthly effective at month-end
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

        # Save monthly cache
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

    # =========================================================================
    # STEP 4: Compute analysis period
    # =========================================================================
    
    # analysis_end = last month-end strictly before today
    today_ts = pd.Timestamp(datetime.now().date())
    analysis_end = get_analysis_end(monthly_prices.index, today_ts)
    analysis_end_str = analysis_end.strftime("%Y-%m-%d")

    # =========================================================================
    # STEP 5: Compute portfolio returns (NaN-safe dynamic)
    # =========================================================================
    
    asset_returns_df = monthly_returns[[t for t in tickers if t in monthly_returns.columns]].copy()
    target_weights = {t: weights.get(t, 0.0) for t in tickers}
    portfolio_returns, weights_used = portfolio_returns_nan_safe(
        asset_returns_df, target_weights, cash_returns
    )

    # =========================================================================
    # STEP 6: Persist inputs (for reproducibility)
    # =========================================================================
    
    save_inputs(
        output_dir,
        monthly_prices,
        monthly_returns,
        rf_monthly,
        benchmark_returns,
        cash_returns,
        fx_series_used,
    )

    # Log data availability summary
    logger.info("=" * 50)
    logger.info("Сводка по доступным данным:")
    for ticker in tickers:
        r = monthly_returns.get(ticker)
        if r is None or r.dropna().empty:
            warn_skipped_asset(ticker, "нет данных о доходностях")
        else:
            r_clean = r.dropna()
            info_data_summary(
                ticker,
                len(r_clean),
                r_clean.index.min().strftime("%Y-%m"),
                r_clean.index.max().strftime("%Y-%m"),
            )
    logger.info("=" * 50)

    # =========================================================================
    # STEP 7: Compute asset metrics per window
    # =========================================================================
    
    asset_metrics_all: list[list[dict]] = []
    for wm in windows_months:
        rows = []
        for ticker in tickers:
            r_simple = monthly_returns.get(ticker)
            r_log = monthly_log_returns.get(ticker)
            if r_simple is None or r_log is None:
                warn_skipped_asset(ticker, "нет данных о доходностях")
                continue
            
            # Get local benchmark returns for Beta_local
            local_bench_ticker = local_benchmark_map.get(ticker)
            local_bench_returns = None
            if local_bench_ticker and local_bench_ticker != benchmark_base_ticker:
                local_bench_returns = monthly_returns.get(local_bench_ticker)
                if local_bench_returns is None:
                    logger.warning(
                        f"Локальный бенчмарк {local_bench_ticker} для {ticker} не найден, "
                        f"используем базовый бенчмарк {benchmark_base_ticker}"
                    )
            
            row = asset_metrics_one_window(
                ticker,
                r_simple,
                r_log,
                rf_monthly,
                benchmark_returns,
                analysis_end,
                wm,
                mar=mar_monthly,
                local_benchmark_returns=local_bench_returns,
            )
            rows.append(row)
        asset_metrics_all.append(rows)
        export_asset_metrics_csv(rows, wm, output_dir)

    # =========================================================================
    # STEP 8: Compute portfolio metrics per window
    # =========================================================================
    
    portfolio_metrics_list = []
    for wm in windows_months:
        pm = portfolio_metrics_one_window(
            portfolio_returns,
            rf_monthly,
            analysis_end,
            wm,
            benchmark_returns=benchmark_returns,
            mar=mar_monthly,
        )
        portfolio_metrics_list.append(pm)
    export_portfolio_metrics_csv(portfolio_metrics_list, output_dir)
    
    # Get longest window portfolio metrics for target comparison
    portfolio_metrics_summary = None
    if portfolio_metrics_list:
        longest_window_metrics = max(portfolio_metrics_list, key=lambda x: x.get("window_months", 0))
        portfolio_metrics_summary = longest_window_metrics

    # =========================================================================
    # STEP 9: Compute RC_vol and correlation matrix per window
    # =========================================================================
    
    asset_cols = [t for t in tickers if t in monthly_returns.columns]
    for wm in windows_months:
        if not asset_cols:
            logger.warning(f"RC_vol: нет активов для расчёта")
            continue
        returns_slice = slice_window(monthly_returns[asset_cols], analysis_end, wm)
        weights_slice = slice_window(weights_used.reindex(columns=asset_cols).fillna(0), analysis_end, wm)
        returns_slice = returns_slice.dropna(how="all")
        if returns_slice.empty or len(returns_slice) < 2:
            window_label = f"{wm // 12}Y" if wm >= 12 else f"{wm}M"
            logger.warning(f"RC_vol ({window_label}): недостаточно данных (доступно {len(returns_slice)} мес.)")
            continue
        
        # RC_vol
        rc = rc_vol_window(returns_slice, weights_slice, ddof=1)
        suffix = "3y" if wm == 36 else "5y" if wm == 60 else "10y"
        export_rc_vol_csv(rc, output_dir / f"rc_vol_{suffix}.csv")
        
        # Correlation matrix
        corr_matrix = returns_slice.corr()
        export_correlation_matrix_csv(corr_matrix, wm, output_dir)

    # =========================================================================
    # STEP 10: Export run metadata
    # =========================================================================
    
    derived_assumptions = build_derived_assumptions(
        cfg,
        cash_proxy_ticker,
        rf_source,
        local_benchmark_map,
        analysis_end_str,
        windows_months,
    )
    
    export_run_metadata(
        output_dir,
        cfg,
        derived_assumptions,
        analysis_end_str,
        run_timestamp,
        portfolio_metrics_summary,
    )

    # Cleanup old cache versions (keep last 3)
    cleanup_old_cache(keep_versions=3)

    # =========================================================================
    # STEP 11: Print summary
    # =========================================================================
    
    print("\nDone. Outputs in", output_dir)
    print("  asset_metrics_3y.csv, _5y.csv, _10y.csv")
    print("  portfolio_metrics_3y.csv, _5y.csv, _10y.csv")
    print("  rc_vol_3y.csv, _5y.csv, _10y.csv")
    print("  correlation_matrix_3y.csv, _5y.csv, _10y.csv")
    print("  run_metadata.json")
    print("  inputs/ (monthly_prices, monthly_returns, rf, benchmark, cash, fx)")
    
    if cfg.pending_fields:
        print(f"\nПоля, ожидающие ввода пользователя: {cfg.pending_fields}")
    
    if cfg.target_nominal_return_annual is not None and portfolio_metrics_summary:
        realized = portfolio_metrics_summary.get("cagr")
        target = cfg.target_nominal_return_annual
        if realized is not None:
            diff = realized - target
            status = "[OK] достигнута" if diff >= 0 else "[X] не достигнута"
            print(f"\nЦелевая доходность: {target:.2%}, реализованная: {realized:.2%} ({status})")
    
    print(f"\nКеш сохранён в cache/ (дневной: {daily_cache_key}, месячный: {monthly_cache_key})")


if __name__ == "__main__":
    main()
