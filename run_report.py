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

from src.cache import cleanup_old_cache, clear_all_cache
from src.config import (
    load_validated_config,
    load_assets_metadata,
    resolve_cash_and_rf,
    resolve_local_benchmarks,
    get_mar_from_config,
)
from src.config_schema import ConfigValidationError, PortfolioConfig
from src.data_loader import load_monthly_data_shared, MonthlyDataResult
from src.io_export import (
    ensure_output_dir,
    export_asset_metrics_csv,
    export_portfolio_metrics_csv,
    export_rc_vol_csv,
    export_run_metadata,
    export_correlation_matrix_csv,
    export_stress_report,
    save_inputs,
)
from src.metrics_asset import asset_metrics_one_window
from src.metrics_portfolio import portfolio_metrics_one_window
from src.portfolio_dynamic import portfolio_returns_nan_safe
from src.risk_contrib import rc_vol_window
from src.stress import run_stress
from src.stress_factors import (
    build_factor_matrix_monthly,
    estimate_betas_monthly,
    portfolio_factor_betas,
)
from src.utils import setup_logging, warn_skipped_asset, info_data_summary, logger, coverage_ratio
from src.windows import slice_window


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
    # Liquidity life floor amount = liquidity_need_months * monthly_expenses (single source of truth)
    liquidity_need_amount = cfg.liquidity_need_months * (cfg.monthly_expenses or 0)

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
        "liquidity_need": liquidity_need_amount,
        "liquidity_life_floor_amount": liquidity_need_amount,
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
    
    # Weights are produced by optimization; loaded from portfolio_weights.yml when not in config
    if not cfg.weights:
        logger.error(
            "Portfolio weights are not set. Weights are produced by optimization (constraints + client metrics). "
            "Run the optimization step first: python run_optimization.py (writes portfolio_weights.yml)."
        )
        raise SystemExit(1)
    
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
    # STEP 3: Download data (with caching) — shared loader
    # =========================================================================
    data = load_monthly_data_shared(
        tickers=tickers,
        benchmark_base_ticker=benchmark_base_ticker,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        investor_currency=investor_currency,
        windows_months=windows_months,
        assets_meta=assets_meta,
        no_cache=args.no_cache,
        local_benchmark_map=local_benchmark_map,
    )
    monthly_prices = data.monthly_prices
    monthly_returns = data.monthly_returns
    monthly_log_returns = data.monthly_log_returns
    rf_monthly = data.rf_monthly
    benchmark_returns = data.benchmark_returns
    cash_returns = data.cash_returns
    fx_series_used = data.fx_series_used
    analysis_end = data.analysis_end
    analysis_end_str = data.analysis_end_str
    daily_cache_key = data.daily_cache_key
    monthly_cache_key = data.monthly_cache_key

    # =========================================================================
    # STEP 4: Compute portfolio returns (NaN-safe dynamic)
    # =========================================================================
    
    # Ensure cash_returns is aligned to monthly index so common_idx is non-empty (avoid empty portfolio returns)
    if cash_returns.empty or len(cash_returns.index) == 0:
        logger.warning(
            f"Нет данных по cash proxy ({cash_proxy_ticker}); для расчёта портфеля используется нулевая доходность кэша."
        )
        cash_returns = pd.Series(0.0, index=monthly_returns.index)
    else:
        cash_returns = cash_returns.reindex(monthly_returns.index).fillna(0.0)
    
    asset_returns_df = monthly_returns[[t for t in tickers if t in monthly_returns.columns]].copy()
    target_weights = {t: weights.get(t, 0.0) for t in tickers}
    portfolio_returns, weights_used = portfolio_returns_nan_safe(
        asset_returns_df, target_weights, cash_returns
    )

    # =========================================================================
    # STEP 5: Persist inputs (for reproducibility)
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
    # STEP 6: Compute asset metrics per window
    # =========================================================================
    
    coverage_threshold = getattr(cfg, "coverage_threshold", 0.90) or 0.90
    analysis_end_ts = pd.Timestamp(analysis_end_str)

    asset_metrics_all: list[list[dict]] = []
    for wm in windows_months:
        rows = []
        for ticker in tickers:
            r_simple = monthly_returns.get(ticker)
            r_log = monthly_log_returns.get(ticker)
            if r_simple is None or r_log is None:
                warn_skipped_asset(ticker, "нет данных о доходностях")
                continue
            if coverage_ratio(r_simple, analysis_end_ts, wm) < coverage_threshold:
                warn_skipped_asset(
                    ticker,
                    "coverage в окне %d мес. < %.0f%%" % (wm, coverage_threshold * 100),
                )
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
    # STEP 7: Compute portfolio metrics per window
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
    # STEP 8: Compute RC_vol and correlation matrix per window
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
    # STEP 9: Stress testing (per docs/docs/stress_testing_spec.md)
    # =========================================================================
    
    beta_window_months = 36
    analysis_end_ts = pd.Timestamp(analysis_end_str)
    beta_start = (analysis_end_ts - pd.DateOffset(months=beta_window_months)).strftime("%Y-%m-%d")
    try:
        factor_monthly = build_factor_matrix_monthly(beta_start, analysis_end_str)
        asset_returns_for_beta = monthly_returns[[t for t in tickers if t in monthly_returns.columns]].copy()
        asset_betas_df = estimate_betas_monthly(
            asset_returns_for_beta,
            factor_monthly,
            min_observations=24,
        )
        portfolio_betas_dict = portfolio_factor_betas(weights, asset_betas_df)
    except Exception as e:
        logger.warning(f"Stress factor/beta setup failed: {e}; stress report may use block fallback only.")
        asset_betas_df = pd.DataFrame()
        portfolio_betas_dict = {}

    stress_top3_cap = getattr(cfg, "stress_top3_rc_sum_cap_pct", 0.70) or 0.70
    stress_report = run_stress(
        tickers=tickers,
        weights=weights,
        blocks=cfg.blocks,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas_df,
        portfolio_betas=portfolio_betas_dict,
        target_max_drawdown_pct=cfg.target_max_drawdown_pct,
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
        stress_top3_rc_sum_cap_pct=stress_top3_cap,
    )
    export_stress_report(stress_report, output_dir)
    logger.info(f"Stress status: {stress_report.get('status', 'N/A')}")

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
        stress_report=stress_report,
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
    print("  stress_report.json")
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

    # Guardrails: Max DD and Stress Judge
    if portfolio_metrics_summary and cfg.target_max_drawdown_pct is not None:
        max_dd_limit = abs(cfg.target_max_drawdown_pct)
        realized_mdd = portfolio_metrics_summary.get("max_drawdown")
        if realized_mdd is not None and not (realized_mdd != realized_mdd):
            mdd_ok = realized_mdd >= -max_dd_limit
            print(f"\nMax DD: {'PASS' if mdd_ok else 'FAIL'} (цель: -{max_dd_limit:.1%}, реализовано: {realized_mdd:.1%})")
    if stress_report:
        st = stress_report.get("status", "N/A")
        reason = stress_report.get("fail_reason_code") or stress_report.get("skip_reason") or ""
        print(f"Stress Judge: {st}" + (f" ({reason})" if reason else ""))

    print(f"\nКеш сохранён в cache/ (дневной: {daily_cache_key}, месячный: {monthly_cache_key})")


if __name__ == "__main__":
    main()
