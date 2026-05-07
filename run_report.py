"""
Portfolio Metrics Standard вЂ” single entry script.
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
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.cache import cleanup_old_cache, clear_all_cache
from src.config import (
    load_validated_config,
    load_assets_metadata,
    resolve_cash_and_rf,
    resolve_local_benchmarks,
    get_mar_from_config,
    portfolio_total_tickers,
)
from src.config_schema import ConfigValidationError, PortfolioConfig
from src.data_loader import load_monthly_data_shared, MonthlyDataResult
from src.etf_universe import UniverseValidationError, write_universe_diagnostics
from src.io_export import (
    ensure_output_dir,
    export_asset_metrics_csv,
    export_portfolio_metrics_csv,
    export_rc_vol_csv,
    export_run_metadata,
    export_correlation_matrix_csv,
    export_stress_report,
    export_data_policy,
    save_inputs,
)
from src.snapshot import (
    build_snapshot,
    build_snapshot_assets,
    build_snapshot_for_window,
    print_snapshot,
    save_snapshot,
    write_report_html,
    write_report_txt,
)
from src.metrics_asset import asset_metrics_one_window, mandate_max_drawdown_full_history_check
from src.metrics_portfolio import portfolio_metrics_one_window
from src.portfolio_analytics import (
    drawdown_structure,
    effective_equity_exposure,
    es_historical,
    rolling_sharpe,
    rolling_sortino,
    rolling_summary,
    rolling_vol_annual,
    var_historical,
)
from src.optimization import get_risk_portfolio_tickers
from src.portfolio_dynamic import portfolio_returns_nan_safe
from src.risk_contrib import cov_matrix_monthly, rc_vol_window
from src.stress import run_stress
from src.stress_factors import (
    FACTOR_COLUMN_ORDER,
    FACTOR_WEEKS_10Y,
    FACTOR_WEEKS_3Y,
    FACTOR_WEEKS_5Y,
    FACTOR_MONTHS_10Y,
    FACTOR_MONTHS_3Y,
    FACTOR_MONTHS_5Y,
    compute_portfolio_rolling_factor_betas_weekly,
    compute_portfolio_rolling_factor_betas_monthly,
    compute_portfolio_factor_beta_oos_weekly,
    compute_portfolio_factor_beta_oos_monthly,
    compute_asset_factor_betas_weekly,
    build_factor_matrix,
    attach_kalman_factor_betas_to_stress_report,
    build_diagnostic_oil_beta,
    build_factor_beta_diagnostic_overlay,
    enrich_historical_results_with_factor_attribution,
    factor_covariance_analytics,
    factor_variance_decomposition_weekly,
    macro_regime_csv_frames,
    macro_regime_diagnostics,
    portfolio_pca_diagnostics,
    factor_beta_oos_stability_diagnostics,
    factor_beta_stability_diagnostics,
    factor_beta_stability_rows,
    factor_oos_beta_shock_explainability,
    portfolio_factor_regression_weekly,
    portfolio_factor_betas,
    rolling_beta_summary,
    write_rolling_betas_plot_html,
    write_rolling_betas_plot_pngs,
)
from src.utils import setup_logging, warn_skipped_asset, info_data_summary, logger, coverage_ratio
from src.windows import slice_window
from src.portfolio_commentary import write_portfolio_commentary, write_stress_commentary


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Portfolio Metrics Standard вЂ” calculate and export portfolio metrics"
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
    parser.add_argument(
        "--backtest-mode",
        type=str,
        choices=("dynamic_nan_safe", "simple"),
        default="dynamic_nan_safe",
        help="Backtest mode: dynamic_nan_safe (default, policy-compliant NaN/young ETF handling) or simple (opt-in)",
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


def run_portfolio_report_for_weights(
    cfg: PortfolioConfig,
    weights: dict[str, float],
    *,
    run_timestamp: str,
    output_dir_csv: Path,
    output_dir_final: Path,
    backtest_mode_override: str | None = None,
    no_cache: bool = False,
) -> tuple[dict | None, dict]:
    """
    Core metrics/stress/report pipeline, parameterized by explicit weights and output dirs.

    Р’Р°Р¶РЅРѕ: СЌС‚Р° С„СѓРЅРєС†РёСЏ РЅРµ РїСЂРёРјРµРЅСЏРµС‚ РЅРёРєР°РєРѕР№ policy-Р»РѕРіРёРєРё Рє РІС…РѕРґРЅС‹Рј РІРµСЃР°Рј.
    Р”Р»СЏ Equal-Weight Рё Risk-Parity РІРµСЃР° РґРѕР»Р¶РЅС‹ Р±С‹С‚СЊ РїРѕСЃС‚СЂРѕРµРЅС‹ РєР°Рє baseline-РїРѕСЂС‚С„РµР»Рё
    Р±РµР· RC caps / weight caps / discretionary overlays
    Рё СЃРєСЂС‹С‚С‹С… policy-С„РёР»СЊС‚СЂРѕРІ.
    """
    investor_currency = cfg.investor_currency
    benchmark_base_ticker = cfg.benchmark_base_ticker
    windows_months = cfg.windows_months

    assets_meta = load_assets_metadata()

    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    tickers = portfolio_total_tickers(cfg.tickers, weights, cash_proxy_ticker)

    mar_annual = get_mar_from_config(cfg)
    mar_monthly = mar_annual / 12 if mar_annual is not None else None

    config_local_override = cfg.local_benchmark_map or {}
    local_benchmark_map = resolve_local_benchmarks(
        tickers, config_local_override, base_benchmark=benchmark_base_ticker
    )

    logger.info(f"Р’Р°Р»СЋС‚Р° РёРЅРІРµСЃС‚РѕСЂР°: {investor_currency}")
    logger.info(f"Р‘Р°Р·РѕРІС‹Р№ Р±РµРЅС‡РјР°СЂРє: {benchmark_base_ticker}")
    logger.info(f"Cash proxy: {cash_proxy_ticker}")
    logger.info(f"Risk-free source: {rf_source}")
    logger.info(f"Р›РѕРєР°Р»СЊРЅС‹Рµ Р±РµРЅС‡РјР°СЂРєРё: {local_benchmark_map}")

    if cfg.target_nominal_return_annual is not None:
        logger.info(f"Р¦РµР»РµРІР°СЏ РґРѕС…РѕРґРЅРѕСЃС‚СЊ: {cfg.target_nominal_return_annual:.2%}")

    data = load_monthly_data_shared(
        tickers=tickers,
        benchmark_base_ticker=benchmark_base_ticker,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        investor_currency=investor_currency,
        windows_months=windows_months,
        assets_meta=assets_meta,
        no_cache=no_cache,
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
    # STEP 4: Compute portfolio returns (NaN-safe dynamic; production vs research mode)
    # =========================================================================

    # Ensure cash_returns is aligned to monthly index so common_idx is non-empty (avoid empty portfolio returns)
    if cash_returns.empty or len(cash_returns.index) == 0:
        logger.warning(
            f"РќРµС‚ РґР°РЅРЅС‹С… РїРѕ cash proxy ({cash_proxy_ticker}); РґР»СЏ СЂР°СЃС‡С‘С‚Р° РїРѕСЂС‚С„РµР»СЏ РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РЅСѓР»РµРІР°СЏ РґРѕС…РѕРґРЅРѕСЃС‚СЊ РєСЌС€Р°."
        )
        cash_returns = pd.Series(0.0, index=monthly_returns.index)
    else:
        cash_returns = cash_returns.reindex(monthly_returns.index).fillna(0.0)

    asset_returns_df = monthly_returns[[t for t in tickers if t in monthly_returns.columns]].copy()
    target_weights = {t: weights.get(t, 0.0) for t in tickers}

    backtest_mode = backtest_mode_override or getattr(cfg, "backtest_mode", "dynamic_nan_safe")
    backtest_mode = backtest_mode or "dynamic_nan_safe"
    if backtest_mode not in ("dynamic_nan_safe", "simple"):
        backtest_mode = "dynamic_nan_safe"

    backtest_diagnostics: dict | None = None
    inner_join_months_used: int | None = None  # inner-join sample length (dynamic mode diagnostics)
    if backtest_mode == "dynamic_nan_safe":
        # Policy-compliant: global redistribution among risk tickers when returns are missing
        if asset_returns_df.shape[0] >= 2:
            ret_inner = asset_returns_df.dropna(how="any").iloc[-720:]  # inner join, up to 60y
            inner_join_months_used = len(ret_inner)
            if inner_join_months_used is not None and inner_join_months_used < 36 and inner_join_months_used >= 2:
                logger.warning(
                    "Inner-join sample for covariance context is %d months (< 36). Risk estimates may be noisy.",
                    inner_join_months_used,
                )
        risk_rt = get_risk_portfolio_tickers(cfg.tickers, cfg.cash_proxy_ticker)
        result = portfolio_returns_nan_safe(
            asset_returns_df,
            target_weights,
            cash_returns,
            risk_tickers=risk_rt,
            return_diagnostics=True,
        )
        portfolio_returns, weights_used, backtest_diagnostics = result
        logger.info(
            "Backtest mode: dynamic_nan_safe (NaN-safe with global redistribution)."
        )
    else:
        # Simple (opt-in): direct portfolio return path, no RC-gating.
        portfolio_returns, weights_used = portfolio_returns_nan_safe(
            asset_returns_df,
            target_weights,
            cash_returns,
        )
        backtest_diagnostics = None
        logger.info("Backtest mode: simple.")

    # Data policy section: first available month per ticker (young ETF inclusion)
    first_available_month: dict[str, str] = {}
    for t in tickers:
        if t not in asset_returns_df.columns:
            continue
        s = asset_returns_df[t].dropna()
        if not s.empty:
            first_available_month[t] = s.index.min().strftime("%Y-%m")

    # =========================================================================
    # STEP 5: Persist inputs (for reproducibility)
    # =========================================================================

    save_inputs(
        output_dir_csv,
        monthly_prices,
        monthly_returns,
        rf_monthly,
        benchmark_returns,
        cash_returns,
        fx_series_used,
    )

    export_data_policy(
        output_dir_final,
        backtest_mode=backtest_mode,
        first_available_month=first_available_month,
        inner_join_months_used=inner_join_months_used,
        n_months_redistributed=backtest_diagnostics.get("n_months_redistributed") if backtest_diagnostics else None,
        n_months_cash_fallback=backtest_diagnostics.get("n_months_cash_fallback") if backtest_diagnostics else None,
    )

    # Log data availability summary
    logger.info("=" * 50)
    logger.info("РЎРІРѕРґРєР° РїРѕ РґРѕСЃС‚СѓРїРЅС‹Рј РґР°РЅРЅС‹Рј:")
    for ticker in tickers:
        r = monthly_returns.get(ticker)
        if r is None or r.dropna().empty:
            warn_skipped_asset(ticker, "РЅРµС‚ РґР°РЅРЅС‹С… Рѕ РґРѕС…РѕРґРЅРѕСЃС‚СЏС…")
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
                warn_skipped_asset(ticker, "РЅРµС‚ РґР°РЅРЅС‹С… Рѕ РґРѕС…РѕРґРЅРѕСЃС‚СЏС…")
                continue
            if coverage_ratio(r_simple, analysis_end_ts, wm) < coverage_threshold:
                warn_skipped_asset(
                    ticker,
                    "coverage РІ РѕРєРЅРµ %d РјРµСЃ. < %.0f%%" % (wm, coverage_threshold * 100),
                )
                continue

            # Get local benchmark returns for Beta_local
            local_bench_ticker = local_benchmark_map.get(ticker)
            local_bench_returns = None
            if local_bench_ticker and local_bench_ticker != benchmark_base_ticker:
                local_bench_returns = monthly_returns.get(local_bench_ticker)
                if local_bench_returns is None:
                    logger.warning(
                        f"Р›РѕРєР°Р»СЊРЅС‹Р№ Р±РµРЅС‡РјР°СЂРє {local_bench_ticker} РґР»СЏ {ticker} РЅРµ РЅР°Р№РґРµРЅ, "
                        f"РёСЃРїРѕР»СЊР·СѓРµРј Р±Р°Р·РѕРІС‹Р№ Р±РµРЅС‡РјР°СЂРє {benchmark_base_ticker}"
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
        export_asset_metrics_csv(rows, wm, output_dir_csv)

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
    export_portfolio_metrics_csv(portfolio_metrics_list, output_dir_csv)

    # Map window_months to human-readable keys for snapshot (3y/5y/10y)
    portfolio_windows: dict[str, dict] = {}
    for pm in portfolio_metrics_list:
        wm = pm.get("window_months", 0)
        if wm == 36:
            key = "3y"
        elif wm == 60:
            key = "5y"
        elif wm == 120:
            key = "10y"
        else:
            key = f"{int(wm)}m" if isinstance(wm, (int, float)) else "unknown"
        portfolio_windows[key] = pm

    # Get longest window portfolio metrics for target comparison
    portfolio_metrics_summary = None
    if portfolio_metrics_list:
        longest_window_metrics = max(portfolio_metrics_list, key=lambda x: x.get("window_months", 0))
        portfolio_metrics_summary = longest_window_metrics

    # =========================================================================
    # STEP 8: Compute RC_vol and correlation matrix per window
    # =========================================================================

    asset_cols = [t for t in tickers if t in monthly_returns.columns]
    rc_for_snapshot = None
    rc_by_window: dict[str, pd.Series] = {}
    rc_csv_by_window: dict[str, str] = {}
    corr_csv_by_window: dict[str, str] = {}
    for wm in windows_months:
        if not asset_cols:
            logger.warning(f"RC_vol: РЅРµС‚ Р°РєС‚РёРІРѕРІ РґР»СЏ СЂР°СЃС‡С‘С‚Р°")
            continue
        returns_slice = slice_window(monthly_returns[asset_cols], analysis_end, wm)
        weights_slice = slice_window(weights_used.reindex(columns=asset_cols).fillna(0), analysis_end, wm)
        returns_slice = returns_slice.dropna(how="all")
        if returns_slice.empty or len(returns_slice) < 2:
            window_label = f"{wm // 12}Y" if wm >= 12 else f"{wm}M"
            logger.warning(f"RC_vol ({window_label}): РЅРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РґР°РЅРЅС‹С… (РґРѕСЃС‚СѓРїРЅРѕ {len(returns_slice)} РјРµСЃ.)")
            continue

        # RC_vol
        rc = rc_vol_window(returns_slice, weights_slice, ddof=1)
        if wm == 60:
            rc_for_snapshot = rc
        suffix = "3y" if wm == 36 else "5y" if wm == 60 else "10y"
        rc_filename = f"rc_vol_{suffix}.csv"
        export_rc_vol_csv(rc, output_dir_csv / rc_filename)
        # Store per-window RC for snapshot windows section
        if wm in (36, 60, 120):
            key = "3y" if wm == 36 else "5y" if wm == 60 else "10y"
            rc_by_window[key] = rc
            rc_csv_by_window[key] = rc_filename

        # Correlation matrix
        corr_matrix = returns_slice.corr()
        export_correlation_matrix_csv(corr_matrix, wm, output_dir_csv)
        if wm in (36, 60, 120):
            key = "3y" if wm == 36 else "5y" if wm == 60 else "10y"
            corr_csv_by_window[key] = f"correlation_matrix_{suffix}.csv"

    # =========================================================================
    # STEP 9: Stress testing (per docs/docs/stress_testing_spec.md)
    # =========================================================================

    portfolio_betas_5y_dict: dict[str, float] = {}
    portfolio_betas_10y_dict: dict[str, float] = {}
    diagnostic_betas_5y_extended: dict[str, float] = {}
    diagnostic_betas_10y_extended: dict[str, float] = {}
    recession_factor_returns = pd.DataFrame()
    try:
        beta_tickers = [t for t in tickers if weights.get(t, 0) > 0]
        if not beta_tickers:
            beta_tickers = list(tickers)

        def _portfolio_betas_weekly(window_weeks: int) -> tuple[pd.DataFrame, dict[str, float]]:
            asset_betas_win = compute_asset_factor_betas_weekly(
                beta_tickers,
                analysis_end_str,
                window_weeks,
            )
            return asset_betas_win, portfolio_factor_betas(weights, asset_betas_win)

        asset_betas_5y_df, portfolio_betas_5y_dict = _portfolio_betas_weekly(FACTOR_WEEKS_5Y)
        _asset_betas_10y_df, portfolio_betas_10y_dict = _portfolio_betas_weekly(FACTOR_WEEKS_10Y)
        diagnostic_betas_5y_extended = portfolio_factor_betas(
            weights,
            compute_asset_factor_betas_weekly(beta_tickers, analysis_end_str, FACTOR_WEEKS_5Y, factor_columns=FACTOR_COLUMN_ORDER),
        )
        diagnostic_betas_10y_extended = portfolio_factor_betas(
            weights,
            compute_asset_factor_betas_weekly(beta_tickers, analysis_end_str, FACTOR_WEEKS_10Y, factor_columns=FACTOR_COLUMN_ORDER),
        )
        # Keep stress engine input/backward compatibility aligned to 5Y betas.
        asset_betas_df = asset_betas_5y_df
        portfolio_betas_dict = portfolio_betas_5y_dict
        try:
            recession_factor_returns = build_factor_matrix("2007-01-01", analysis_end_str)
        except Exception as e:
            logger.warning(f"Recession factor calibration setup failed: {e}; recession severe will use fallback.")
    except Exception as e:
        logger.warning(f"Stress factor/beta setup failed: {e}; stress report may use fallback only.")
        asset_betas_df = pd.DataFrame()
        portfolio_betas_dict = {}

    stress_report = run_stress(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas_df,
        portfolio_betas=portfolio_betas_dict,
        target_max_drawdown_pct=cfg.target_max_drawdown_pct,
        cash_proxy_ticker=cash_proxy_ticker,
        factor_returns=recession_factor_returns,
    )
    stress_report["factor_betas_5y"] = {k: round(v, 4) for k, v in (portfolio_betas_5y_dict or {}).items()}
    stress_report["factor_betas_10y"] = {k: round(v, 4) for k, v in (portfolio_betas_10y_dict or {}).items()}
    stress_report["factor_betas"] = dict(stress_report["factor_betas_5y"])
    # Portfolio factor regression diagnostics (5Y/10Y): t/p/CI/R^2 on weekly data, same factor matrix definition.
    stress_report["factor_regression_5y"] = {}
    stress_report["factor_regression_10y"] = {}
    factor_regression_5y_extended: dict[str, Any] = {}
    factor_regression_10y_extended: dict[str, Any] = {}
    try:
        stress_report["factor_regression_5y"] = portfolio_factor_regression_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_5Y,
        )
    except Exception as e:
        stress_report["factor_regression_5y_error"] = str(e)
        logger.warning(f"Factor regression diagnostics (5Y) failed: {e}")
    try:
        stress_report["factor_regression_10y"] = portfolio_factor_regression_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_10Y,
        )
    except Exception as e:
        stress_report["factor_regression_10y_error"] = str(e)
        logger.warning(f"Factor regression diagnostics (10Y) failed: {e}")
    try:
        factor_regression_5y_extended = portfolio_factor_regression_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_5Y,
            factor_columns=FACTOR_COLUMN_ORDER,
        )
        factor_regression_10y_extended = portfolio_factor_regression_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_10Y,
            factor_columns=FACTOR_COLUMN_ORDER,
        )
    except Exception as e:
        stress_report["diagnostic_oil_beta_regression_error"] = str(e)
        logger.warning(f"Extended Oil diagnostic regression failed: {e}")

    # Rolling beta stability (diagnostic): 3Y/5Y/10Y weekly + monthly betas, OOS checks, and severity.
    rb: dict[str, pd.DataFrame] = {}
    try:
        rolling_windows = {"3y": FACTOR_WEEKS_3Y, "5y": FACTOR_WEEKS_5Y, "10y": FACTOR_WEEKS_10Y}
        rolling_windows_months = {"3y": FACTOR_MONTHS_3Y, "5y": FACTOR_MONTHS_5Y, "10y": FACTOR_MONTHS_10Y}
        rb = compute_portfolio_rolling_factor_betas_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            rolling_windows_weeks=rolling_windows,
        )
        rb_monthly = compute_portfolio_rolling_factor_betas_monthly(
            monthly_returns=monthly_returns,
            weights=weights,
            analysis_end_str=analysis_end_str,
            rolling_windows_months=rolling_windows_months,
        )
        # Save rolling beta time series CSV files
        csv_paths: dict[str, str] = {}
        for lbl, df_rb in rb.items():
            if df_rb is None or df_rb.empty:
                continue
            p = output_dir_csv / f"rolling_factor_betas_{lbl}.csv"
            df_rb.round(4).to_csv(p, index=True)
            csv_paths[lbl] = p.name

        monthly_csv_paths: dict[str, str] = {}
        for lbl, df_rb in rb_monthly.items():
            if df_rb is None or df_rb.empty:
                continue
            p = output_dir_csv / f"rolling_factor_betas_monthly_{lbl}.csv"
            df_rb.round(4).to_csv(p, index=True)
            monthly_csv_paths[lbl] = p.name

        summary_df = rolling_beta_summary(rb)
        summary_csv_name = ""
        summary_struct: dict[str, dict[str, dict[str, float | int]]] = {}
        if not summary_df.empty:
            summary_csv = output_dir_csv / "rolling_factor_betas_summary.csv"
            summary_df.round(4).to_csv(summary_csv, index=False)
            summary_csv_name = summary_csv.name
            for _, row in summary_df.iterrows():
                w = str(row["window"])
                b = str(row["beta"])
                summary_struct.setdefault(w, {})[b] = {
                    "n_points": int(row["n_points"]),
                    "mean": float(row["mean"]),
                    "median": float(row["median"]),
                    "p10": float(row["p10"]),
                    "p90": float(row["p90"]),
                }

        monthly_summary_df = rolling_beta_summary(rb_monthly)
        monthly_summary_csv_name = ""
        monthly_summary_struct: dict[str, dict[str, dict[str, float | int]]] = {}
        if not monthly_summary_df.empty:
            monthly_summary_csv = output_dir_csv / "rolling_factor_betas_monthly_summary.csv"
            monthly_summary_df.round(4).to_csv(monthly_summary_csv, index=False)
            monthly_summary_csv_name = monthly_summary_csv.name
            for _, row in monthly_summary_df.iterrows():
                w = str(row["window"])
                b = str(row["beta"])
                monthly_summary_struct.setdefault(w, {})[b] = {
                    "n_points": int(row["n_points"]),
                    "mean": float(row["mean"]),
                    "median": float(row["median"]),
                    "p10": float(row["p10"]),
                    "p90": float(row["p90"]),
                }

        oos_weekly = compute_portfolio_factor_beta_oos_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            rolling_windows_weeks=rolling_windows,
        )
        oos_monthly = compute_portfolio_factor_beta_oos_monthly(
            monthly_returns=monthly_returns,
            weights=weights,
            analysis_end_str=analysis_end_str,
            rolling_windows_months=rolling_windows_months,
        )
        oos_stability = factor_beta_oos_stability_diagnostics({
            "weekly": oos_weekly,
            "monthly": oos_monthly,
        })
        stability = factor_beta_stability_diagnostics(
            {
                "weekly": rb,
                "monthly": rb_monthly,
            },
            oos_stability=oos_stability,
        )
        stability_csv_name = ""
        stability_df = factor_beta_stability_rows(stability)
        if not stability_df.empty:
            stability_csv = output_dir_csv / "factor_beta_stability.csv"
            stability_df.round(4).to_csv(stability_csv, index=False)
            stability_csv_name = stability_csv.name

        plot_name = ""
        plot_png_by_window: dict[str, str] = {}
        if rb:
            plot_path = output_dir_final / "rolling_factor_betas.html"
            write_rolling_betas_plot_html(rb, plot_path)
            plot_name = plot_path.name
            plot_png_by_window = write_rolling_betas_plot_pngs(rb, output_dir_final)

        stress_report["factor_betas_rolling_windows_weeks"] = rolling_windows
        stress_report["factor_betas_rolling_windows_months"] = rolling_windows_months
        stress_report["factor_betas_rolling_summary"] = summary_struct
        stress_report["factor_betas_rolling_monthly_summary"] = monthly_summary_struct
        stress_report["factor_betas_stability"] = stability
        stress_report["factor_betas_rolling_artifacts"] = {
            "csv_by_window": csv_paths,
            "monthly_csv_by_window": monthly_csv_paths,
            "summary_csv": summary_csv_name,
            "monthly_summary_csv": monthly_summary_csv_name,
            "stability_csv": stability_csv_name,
            "plot_html": plot_name,
            "plot_png_by_window": plot_png_by_window,
        }
    except Exception as e:
        stress_report["factor_betas_rolling_error"] = str(e)
        logger.warning(f"Rolling factor betas diagnostics failed: {e}")

    # Kalman factor betas: diagnostic-only current regime estimate, does not replace raw 5Y/10Y OLS betas.
    try:
        attach_kalman_factor_betas_to_stress_report(
            stress_report,
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            output_dir_csv=output_dir_csv,
            window_weeks=FACTOR_WEEKS_10Y,
        )
    except Exception as e:
        stress_report["factor_betas_kalman_error"] = str(e)
        logger.warning(f"Kalman factor betas diagnostics failed: {e}")

    # Factor covariance analytics: explicit base / stress_empirical / stress_overlay regimes.
    try:
        factor_cov = factor_covariance_analytics(
            analysis_end_str=analysis_end_str,
            portfolio_betas=stress_report.get("factor_betas_5y") or stress_report.get("factor_betas") or {},
            rolling_betas_weekly=rb,
            factor_returns=recession_factor_returns if not recession_factor_returns.empty else None,
        )
        stress_report["factor_covariance"] = factor_cov

        def _matrix_df(regime: str, field: str) -> pd.DataFrame:
            payload = (factor_cov.get(regime) or {}).get(field)
            if not isinstance(payload, dict):
                return pd.DataFrame()
            order = factor_cov.get("factor_order") or []
            df = pd.DataFrame(payload).T
            if order:
                df = df.reindex(index=order, columns=order)
            return df

        for regime, fname in {
            "base": "factor_covariance_base_5y_weekly.csv",
            "stress_empirical": "factor_covariance_stress_empirical_weekly.csv",
            "stress_overlay": "factor_covariance_stress_overlay_weekly.csv",
        }.items():
            df = _matrix_df(regime, "matrix")
            if not df.empty:
                df.round(6).to_csv(output_dir_csv / fname)

        for regime, fname in {
            "base": "factor_correlation_base_5y_weekly.csv",
            "stress_empirical": "factor_correlation_stress_empirical_weekly.csv",
            "stress_overlay": "factor_correlation_stress_overlay_weekly.csv",
        }.items():
            df = _matrix_df(regime, "correlations")
            if not df.empty:
                df.round(6).to_csv(output_dir_csv / fname)

        for regime, fname in {
            "base": "portfolio_factor_rc_base.csv",
            "stress_empirical": "portfolio_factor_rc_stress_empirical.csv",
            "stress_overlay": "portfolio_factor_rc_stress_overlay.csv",
        }.items():
            rows = ((factor_cov.get("portfolio_factor_rc") or {}).get(regime) or [])
            if rows:
                pd.DataFrame(rows).round(6).to_csv(output_dir_csv / fname, index=False)

        overlay_deltas = ((factor_cov.get("stress_overlay") or {}).get("overlay_deltas") or [])
        if overlay_deltas:
            pd.DataFrame(overlay_deltas).round(6).to_csv(output_dir_csv / "factor_covariance_overlay_deltas.csv", index=False)

        stability = factor_cov.get("covariance_stability_check") or {}
        stability_rows = []
        for row in stability.get("by_pair") or []:
            stability_rows.append({"type": "pair", **row})
        for row in stability.get("by_factor_variance") or []:
            stability_rows.append({"type": "factor_variance", **row})
        if stability_rows:
            pd.DataFrame(stability_rows).round(6).to_csv(output_dir_csv / "factor_covariance_stability_check.csv", index=False)

        forecast_quality = factor_cov.get("forecast_quality") or {}
        forecast_rows = forecast_quality.get("rows") if isinstance(forecast_quality, dict) else []
        if forecast_rows:
            flat_rows = []
            for row in forecast_rows:
                if not isinstance(row, dict):
                    continue
                flat_rows.append({k: v for k, v in row.items() if k != "worst_corr_error_pair"})
            if flat_rows:
                pd.DataFrame(flat_rows).round(6).to_csv(output_dir_csv / "factor_covariance_forecast_quality.csv", index=False)
    except Exception as e:
        stress_report["factor_covariance_error"] = str(e)
        logger.warning(f"Factor covariance analytics failed: {e}")

    try:
        macro_regimes = macro_regime_diagnostics(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            factor_returns=recession_factor_returns if not recession_factor_returns.empty else None,
        )
        stress_report["macro_regime_diagnostics"] = macro_regimes
        for fname, df in macro_regime_csv_frames(macro_regimes).items():
            if not df.empty:
                df.round(6).to_csv(output_dir_csv / fname, index=False)
        quality_summary = (macro_regimes or {}).get("regime_label_quality_check")
        if isinstance(quality_summary, dict) and quality_summary:
            (output_dir_final / "regime_label_quality_summary.json").write_text(
                json.dumps(quality_summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    except Exception as e:
        stress_report["macro_regime_diagnostics_error"] = str(e)
        logger.warning(f"Macro regime diagnostics failed: {e}")

    try:
        stress_report["diagnostic_oil_beta"] = build_diagnostic_oil_beta(
            factor_betas_5y_extended=diagnostic_betas_5y_extended,
            factor_betas_10y_extended=diagnostic_betas_10y_extended,
            factor_regression_5y_extended=factor_regression_5y_extended,
            factor_regression_10y_extended=factor_regression_10y_extended,
            factor_covariance=stress_report.get("factor_covariance") or {},
            kalman_report=stress_report.get("factor_betas_kalman") or {},
        )
    except Exception as e:
        stress_report["diagnostic_oil_beta_error"] = str(e)
        logger.warning(f"Diagnostic Oil beta block failed: {e}")

    # Factor variance decomposition: 5Y weekly factor shares plus residual risk.
    try:
        factor_decomp = factor_variance_decomposition_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_5Y,
        )
        stress_report["factor_variance_decomposition"] = factor_decomp
        for warning in factor_decomp.get("warnings") or []:
            logger.warning(f"Factor variance decomposition warning: {warning}")
        rows = factor_decomp.get("rows") or []
        if rows:
            export_rows = []
            cross = factor_decomp.get("cross_check") or {}
            for row in rows:
                export_rows.append(
                    {
                        "method": factor_decomp.get("method"),
                        "window": factor_decomp.get("window"),
                        "variance_scale": factor_decomp.get("variance_scale"),
                        "status": factor_decomp.get("status"),
                        "r2": factor_decomp.get("r2"),
                        "residual_share": factor_decomp.get("residual_share"),
                        "residual_severity": factor_decomp.get("residual_severity"),
                        "cross_check_status": cross.get("status"),
                        "cross_check_warning_code": cross.get("warning_code"),
                        "stability_severity": (factor_decomp.get("stability") or {}).get("overall_severity"),
                        **row,
                    }
                )
            pd.DataFrame(export_rows).round(8).to_csv(
                output_dir_csv / "factor_variance_decomposition_5y.csv",
                index=False,
            )
    except Exception as e:
        stress_report["factor_variance_decomposition_error"] = str(e)
        logger.warning(f"Factor variance decomposition failed: {e}")

    # Portfolio PCA diagnostics: hidden statistical risk concentration, diagnostic only.
    try:
        pca = portfolio_pca_diagnostics(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_5Y,
            factor_returns=recession_factor_returns if not recession_factor_returns.empty else None,
        )
        stress_report["portfolio_pca"] = pca

        summary_rows = []
        component_rows = []
        rolling_rows = []
        corr_rows = []
        for layer_name in ("raw", "residual"):
            layer = pca.get(layer_name) if isinstance(pca, dict) else None
            if not isinstance(layer, dict) or layer.get("status") != "available":
                continue
            for pca_key in ("covariance_pca", "correlation_pca"):
                block = layer.get(pca_key)
                if not isinstance(block, dict) or block.get("status") != "available":
                    continue
                rolling = block.get("rolling_pc1") or {}
                rolling_pc1_summary = rolling.get("summary") if isinstance(rolling, dict) else {}
                summary_rows.append(
                    {
                        "layer": layer_name,
                        "pca_type": pca_key,
                        "interpretation": block.get("interpretation"),
                        "n_obs": block.get("n_obs"),
                        "n_assets": block.get("n_assets"),
                        "pc1_explained_variance_ratio": block.get("pc1_explained_variance_ratio"),
                        "pc1_concentration_ratio": block.get("pc1_concentration_ratio"),
                        "pc1_severity": block.get("pc1_severity"),
                        "effective_number_of_bets": block.get("effective_number_of_bets"),
                        "effective_number_of_bets_ratio": block.get("effective_number_of_bets_ratio"),
                        "enb_severity": block.get("enb_severity"),
                        "rolling_stability_severity": (rolling_pc1_summary or {}).get("stability_severity") if isinstance(rolling_pc1_summary, dict) else None,
                        "rolling_trend_slope_per_year": (rolling_pc1_summary or {}).get("trend_slope_per_year") if isinstance(rolling_pc1_summary, dict) else None,
                        "rolling_latest_minus_mean": (rolling_pc1_summary or {}).get("latest_minus_mean") if isinstance(rolling_pc1_summary, dict) else None,
                    }
                )
                for comp in block.get("components") or []:
                    if not isinstance(comp, dict):
                        continue
                    loadings = comp.get("loadings") or {}
                    if not isinstance(loadings, dict):
                        continue
                    for asset, loading in loadings.items():
                        component_rows.append(
                            {
                                "layer": layer_name,
                                "pca_type": pca_key,
                                "interpretation": block.get("interpretation"),
                                "component": comp.get("component"),
                                "asset": asset,
                                "loading": loading,
                                "eigenvalue": comp.get("eigenvalue"),
                                "explained_variance_ratio": comp.get("explained_variance_ratio"),
                                "cumulative_explained_variance_ratio": comp.get("cumulative_explained_variance_ratio"),
                            }
                        )
                if isinstance(rolling, dict):
                    for row in rolling.get("rows") or []:
                        if isinstance(row, dict):
                            rolling_rows.append({"layer": layer_name, "pca_type": pca_key, **row})
                fc = block.get("pc1_factor_correlations") or {}
                correlations = fc.get("correlations") if isinstance(fc, dict) else {}
                if isinstance(correlations, dict):
                    for factor, corr in correlations.items():
                        corr_rows.append(
                            {
                                "layer": layer_name,
                                "pca_type": pca_key,
                                "factor": factor,
                                "correlation": corr,
                                "abs_correlation": abs(float(corr)) if corr is not None else None,
                            }
                        )

        if summary_rows:
            pd.DataFrame(summary_rows).round(8).to_csv(output_dir_csv / "portfolio_pca_summary_5y.csv", index=False)
        if component_rows:
            pd.DataFrame(component_rows).round(8).to_csv(output_dir_csv / "portfolio_pca_components_5y.csv", index=False)
        if rolling_rows:
            pd.DataFrame(rolling_rows).round(8).to_csv(output_dir_csv / "portfolio_pca_rolling_pc1.csv", index=False)
        if corr_rows:
            pd.DataFrame(corr_rows).round(8).to_csv(output_dir_csv / "portfolio_pca_pc1_factor_correlations.csv", index=False)
    except Exception as e:
        stress_report["portfolio_pca_error"] = str(e)
        logger.warning(f"Portfolio PCA diagnostics failed: {e}")

    # Out-of-sample explainability in historical episodes: beta Г— realized factor shocks.
    try:
        stress_report["factor_beta_shock_oos"] = factor_oos_beta_shock_explainability(
            weights=weights,
            tickers=tickers,
            historical_results=stress_report.get("historical_results") or [],
            factor_betas_5y=stress_report.get("factor_betas_5y") or {},
            factor_betas_10y=stress_report.get("factor_betas_10y") or {},
            rolling_window_weeks=FACTOR_WEEKS_3Y,
        )
        stress_report["historical_results"] = enrich_historical_results_with_factor_attribution(
            stress_report.get("historical_results") or [],
            stress_report.get("factor_beta_shock_oos"),
            beta_source="5y",
        )
    except Exception as e:
        stress_report["factor_beta_shock_oos_error"] = str(e)
        logger.warning(f"Factor betaГ—shock OOS diagnostics failed: {e}")
    try:
        overlay = build_factor_beta_diagnostic_overlay(
            weights=weights,
            tickers=tickers,
            scenario_results=stress_report.get("scenario_results") or [],
            historical_results=stress_report.get("historical_results") or [],
            factor_betas_5y=stress_report.get("factor_betas_5y") or {},
            factor_betas_10y=stress_report.get("factor_betas_10y") or {},
            factor_betas_stability=stress_report.get("factor_betas_stability") or {},
            factor_beta_shock_oos_raw=stress_report.get("factor_beta_shock_oos"),
            rolling_window_weeks=FACTOR_WEEKS_3Y,
        )
        stress_report["factor_betas_adjusted"] = overlay.get("factor_betas_adjusted") or {}
        stress_report["synthetic_factor_pnl_adjusted"] = overlay.get("synthetic_factor_pnl_adjusted") or {}
        stress_report["factor_beta_shock_oos_adjusted"] = overlay.get("factor_beta_shock_oos_adjusted") or {}
        stress_report["historical_results"] = overlay.get("historical_results_adjusted") or stress_report.get("historical_results") or []
        stress_report["raw_vs_adjusted_pnl_signal"] = overlay.get("raw_vs_adjusted_pnl_signal") or {}
        material_signal = stress_report["raw_vs_adjusted_pnl_signal"]
        if isinstance(material_signal, dict) and material_signal.get("material_difference_any"):
            logger.info(
                "Factor beta adjusted overlay found material raw-vs-adjusted PnL differences: synthetic=%s historical=%s",
                ", ".join(material_signal.get("material_scenarios") or []) or "none",
                ", ".join(material_signal.get("material_historical_episodes") or []) or "none",
            )
    except Exception as e:
        stress_report["factor_beta_adjusted_overlay_error"] = str(e)
        logger.warning(f"Factor beta adjusted overlay failed: {e}")
    export_stress_report(stress_report, output_dir_final)
    logger.info(f"Stress status: {stress_report.get('status', 'N/A')}")

    # =========================================================================
    # STEP 9b: Portfolio analytics per window (rolling Sharpe/Sortino, drawdown, VaR/ES, EEE)
    # =========================================================================
    analytics_by_window: dict[str, dict] = {}
    for wm in windows_months:
        suffix = "3y" if wm == 36 else "5y" if wm == 60 else "10y"
        ret_slice = slice_window(portfolio_returns, analysis_end, wm).dropna()
        rf_slice = slice_window(rf_monthly, analysis_end, wm).reindex(ret_slice.index).fillna(0)
        bench_slice = slice_window(benchmark_returns, analysis_end, wm).reindex(ret_slice.index).dropna()
        if len(ret_slice) < 24:
            continue
        # Rolling 36m and 12m
        rs36 = rolling_sharpe(ret_slice, rf_slice, 36)
        rs12 = rolling_sharpe(ret_slice, rf_slice, 12)
        rsort36 = rolling_sortino(ret_slice, rf_slice, 36, mar=mar_monthly)
        rsort12 = rolling_sortino(ret_slice, rf_slice, 12, mar=mar_monthly)
        rvol = rolling_vol_annual(ret_slice, 12)
        # Export rolling series to CSV
        rs36.round(3).to_csv(output_dir_csv / f"rolling_sharpe_36m_{suffix}.csv", header=True)
        rs12.round(3).to_csv(output_dir_csv / f"rolling_sharpe_12m_{suffix}.csv", header=True)
        rsort36.round(3).to_csv(output_dir_csv / f"rolling_sortino_36m_{suffix}.csv", header=True)
        rsort12.round(3).to_csv(output_dir_csv / f"rolling_sortino_12m_{suffix}.csv", header=True)
        rvol.round(3).to_csv(output_dir_csv / f"rolling_vol_12m_{suffix}.csv", header=True)
        # Drawdown structure (JSON -> final)
        dd_struct = drawdown_structure(ret_slice)
        import json as _json
        with open(output_dir_final / f"drawdown_structure_{suffix}.json", "w", encoding="utf-8") as _f:
            _json.dump(dd_struct, _f, indent=2, default=str)
        # VaR / ES 95% and 99% (CSV)
        var_95 = var_historical(ret_slice, 0.95)
        var_99 = var_historical(ret_slice, 0.99)
        es_95 = es_historical(ret_slice, 0.95)
        es_99 = es_historical(ret_slice, 0.99)
        pd.DataFrame([{"var_95": var_95, "var_99": var_99, "es_95": es_95, "es_99": es_99}]).round(3).to_csv(
            output_dir_csv / f"var_es_{suffix}.csv", index=False
        )
        # EEE (crisis beta * 100%) (CSV)
        eee = effective_equity_exposure(ret_slice, bench_slice, 0.10) if len(bench_slice.dropna()) >= 12 else None
        pd.DataFrame([{"eee_10pct": eee}]).round(3).to_csv(output_dir_csv / f"eee_{suffix}.csv", index=False)
        # Vol-of-vol
        vol_of_vol = float(rvol.std()) if len(rvol.dropna()) >= 2 else None
        rel_vol_of_vol = float(rvol.std() / rvol.mean()) if len(rvol.dropna()) >= 2 and rvol.mean() and rvol.mean() != 0 else None
        analytics_by_window[suffix] = {
            "rolling_sharpe_36m": rolling_summary(rs36),
            "rolling_sharpe_12m": rolling_summary(rs12),
            "rolling_sortino_36m": rolling_summary(rsort36),
            "rolling_sortino_12m": rolling_summary(rsort12),
            "rolling_vol_12m": rolling_summary(rvol),
            "vol_of_vol": round(vol_of_vol, 3) if vol_of_vol is not None else None,
            "rel_vol_of_vol": round(rel_vol_of_vol, 3) if rel_vol_of_vol is not None else None,
            "drawdown_structure": dd_struct,
            "var_95": round(var_95, 3),
            "var_99": round(var_99, 3),
            "es_95": round(es_95, 3),
            "es_99": round(es_99, 3),
            "eee_10pct": eee,
        }

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

    # Gatekeepers: portfolio_valid = False С‚РѕР»СЊРєРѕ РµСЃР»Рё MaxDD РЅР° РїРѕР»РЅРѕР№ РїРµСЂРµСЃРµРєР°СЋС‰РµР№СЃСЏ РёСЃС‚РѕСЂРёРё РЅР°СЂСѓС€Р°РµС‚ РјР°РЅРґР°С‚.
    # РЎС†РµРЅР°СЂРЅС‹Р№ СЃС‚СЂРµСЃСЃ (DIAG_*) РЅРµ РґРµР»Р°РµС‚ РїРѕСЂС‚С„РµР»СЊ invalid.
    portfolio_valid = True
    mandate_chk = mandate_max_drawdown_full_history_check(
        monthly_returns,
        weights,
        abs(cfg.target_max_drawdown_pct) if cfg.target_max_drawdown_pct is not None else None,
    )
    if cfg.target_max_drawdown_pct is not None:
        if mandate_chk.get("pass") is False or mandate_chk.get("pass") is None:
            portfolio_valid = False

    export_run_metadata(
        output_dir_final,
        cfg,
        derived_assumptions,
        analysis_end_str,
        run_timestamp,
        portfolio_metrics_summary,
        stress_report=stress_report,
        portfolio_valid=portfolio_valid,
    )

    # Snapshots: one for assets, three by window (3y / 5y / 10y)
    snapshot_window = 60 if 60 in windows_months else (windows_months[0] if windows_months else 60)
    max_dd_ok = mandate_chk.get("pass") if cfg.target_max_drawdown_pct is not None else None
    snapshot = build_snapshot(
        final_weights_total=weights,
        cash_proxy_ticker=cash_proxy_ticker,
        analysis_end=analysis_end_str,
        stress_report=stress_report,
        final_weights_risk_portfolio=None,
        rc_series=rc_for_snapshot,
        monthly_returns=monthly_returns,
        window_months=snapshot_window,
        target_vol_annual=cfg.target_vol_annual,
        current_vol_annual=portfolio_metrics_summary.get("vol_annual") if portfolio_metrics_summary else None,
        max_dd_ok=max_dd_ok,
        rc_caps_ok=None,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
        portfolio_metrics_summary=portfolio_metrics_summary,
        run_timestamp=run_timestamp,
        portfolio_windows=portfolio_windows,
        rc_by_window=rc_by_window,
        rc_csv_by_window=rc_csv_by_window,
        corr_csv_by_window=corr_csv_by_window,
    )
    print_snapshot(snapshot)
    constraints_status = snapshot.get("constraints_status", {})

    # 1) Snapshot for assets only (per-asset metrics by window, not in portfolio)
    asset_metrics_by_window: dict[str, list] = {}
    for i, wm in enumerate(windows_months):
        key = "3y" if wm == 36 else "5y" if wm == 60 else "10y"
        if i < len(asset_metrics_all):
            asset_metrics_by_window[key] = asset_metrics_all[i]
    snapshot_assets = build_snapshot_assets(asset_metrics_by_window, run_timestamp)
    save_snapshot(snapshot_assets, output_dir_final / "snapshot_assets.json")
    logger.info("Snapshot Р°РєС‚РёРІРѕРІ: %s", output_dir_final / "snapshot_assets.json")

    # 2) Three snapshots by window (3y, 5y, 10y)
    for label in ("3y", "5y", "10y"):
        if label not in portfolio_windows:
            continue
        pm = portfolio_windows[label]
        rc_series_w = rc_by_window.get(label)
        rc_csv_w = rc_csv_by_window.get(label)
        corr_csv_w = corr_csv_by_window.get(label)
        stress_params = {
            "cagr": round(pm.get("cagr"), 3) if pm.get("cagr") is not None else None,
            "vol_annual": round(pm.get("vol_annual"), 3) if pm.get("vol_annual") is not None else None,
            "max_drawdown": round(pm.get("max_drawdown"), 3) if pm.get("max_drawdown") is not None else None,
            "sharpe": round(pm.get("sharpe"), 3) if pm.get("sharpe") is not None else None,
            "beta_base": round(pm.get("beta_portfolio"), 3) if pm.get("beta_portfolio") is not None else None,
        }
        snap_w = build_snapshot_for_window(
            window_label=label,
            window_months=pm.get("window_months", 36 if label == "3y" else 60 if label == "5y" else 120),
            final_weights_total=weights,
            cash_proxy_ticker=cash_proxy_ticker,
            analysis_end=analysis_end_str,
            stress_report=stress_report,
            final_weights_risk_portfolio=None,
            rc_series=rc_series_w,
            portfolio_metrics=pm,
            rc_vol_csv=rc_csv_w,
            correlation_matrix_csv=corr_csv_w,
            constraints_status=constraints_status,
            run_timestamp=run_timestamp,
            stress_portfolio_params=stress_params,
            analytics=analytics_by_window.get(label),
        )
        save_snapshot(snap_w, output_dir_final / f"snapshot_{label}.json")
        logger.info("Snapshot %s: %s", label, output_dir_final / f"snapshot_{label}.json")

    # Index of snapshot files
    save_snapshot(
        {
            "timestamp": run_timestamp,
            "snapshots": {
                "assets": "snapshot_assets.json",
                "3y": "snapshot_3y.json",
                "5y": "snapshot_5y.json",
                "10y": "snapshot_10y.json",
            },
        },
        output_dir_final / "snapshot_index.json",
    )

    # Text and HTML reports aggregating all snapshots (read from output_dir_final)
    write_report_txt(str(output_dir_final))
    html_path = write_report_html(str(output_dir_final))
    logger.info("HTML report: %s", html_path)

    # commentary.txt: always align with this run (summary/stress/CSV)
    try:
        cpath = write_portfolio_commentary(
            output_dir_final,
            output_dir_csv=output_dir_csv,
            portfolio_metrics_10y=portfolio_metrics_summary,
            stress_report=stress_report,
            portfolio_valid=portfolio_valid,
            analysis_end=analysis_end_str,
        )
        if cpath:
            logger.info("commentary.txt: %s", cpath)
    except Exception as e:
        logger.warning("commentary.txt generation failed: %s", e)

    try:
        spath = write_stress_commentary(
            output_dir_final,
            stress_report=stress_report,
            analysis_end=analysis_end_str,
        )
        if spath:
            logger.info("stress_commentary.txt: %s", spath)
    except Exception as e:
        logger.warning("stress_commentary.txt generation failed: %s", e)

    meta = {
        "stress_report": stress_report,
        "portfolio_valid": portfolio_valid,
        "daily_cache_key": daily_cache_key,
        "monthly_cache_key": monthly_cache_key,
    }
    return portfolio_metrics_summary, meta


def main() -> None:
    args = parse_args()
    setup_logging()
    run_timestamp = datetime.now().isoformat()

    if args.clear_cache:
        clear_all_cache()

    try:
        cfg = load_validated_config()
    except ConfigValidationError as e:
        logger.error(f"РћС€РёР±РєР° РІР°Р»РёРґР°С†РёРё РєРѕРЅС„РёРіСѓСЂР°С†РёРё: {e}")
        raise SystemExit(1)

    if cfg.pending_fields:
        logger.info(f"РџРѕР»СЏ РєРѕРЅС„РёРіСѓСЂР°С†РёРё, РѕР¶РёРґР°СЋС‰РёРµ РІРІРѕРґР° РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ: {cfg.pending_fields}")

    if not cfg.weights:
        logger.error(
            "Portfolio weights are not set. Weights are produced by optimization (constraints + client metrics). "
            "Run the optimization step first: python run_optimization.py (writes portfolio_weights.yml)."
        )
        raise SystemExit(1)

    output_dir_csv = ensure_output_dir(Path(cfg.output_dir))
    output_dir_final = ensure_output_dir(Path(getattr(cfg, "output_dir_final", "Main portfolio")))

    try:
        diag_path = write_universe_diagnostics(output_dir_final, cfg.tickers)
        if diag_path:
            logger.info("ETF universe diagnostics: %s", diag_path)
    except UniverseValidationError as e:
        logger.error("%s", e)
        raise SystemExit(1)

    portfolio_metrics_summary, meta = run_portfolio_report_for_weights(
        cfg,
        cfg.weights,
        run_timestamp=run_timestamp,
        output_dir_csv=output_dir_csv,
        output_dir_final=output_dir_final,
        backtest_mode_override=args.backtest_mode,
        no_cache=args.no_cache,
    )

    cleanup_old_cache(keep_versions=3)

    print("\nDone.")
    print(
        "  CSV РІ %s: asset_metrics, portfolio_metrics, rc_vol, correlation_matrix, rolling_*, var_es, eee, inputs/"
        % output_dir_csv
    )
    print(
        "  Р¤РёРЅР°Р»СЊРЅС‹Рµ СЂРµР·СѓР»СЊС‚Р°С‚С‹ РІ %s: portfolio_weights.yml, РІСЃРµ JSON (snapshot_*, stress_report, run_metadata, data_policy, drawdown_structure), report.txt, report.html, commentary.txt"
        % output_dir_final
    )

    if cfg.pending_fields:
        print(f"\nРџРѕР»СЏ, РѕР¶РёРґР°СЋС‰РёРµ РІРІРѕРґР° РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ: {cfg.pending_fields}")

    if cfg.target_nominal_return_annual is not None and portfolio_metrics_summary:
        realized = portfolio_metrics_summary.get("cagr")
        target = cfg.target_nominal_return_annual
        if realized is not None:
            diff = realized - target
            status = "[OK] РґРѕСЃС‚РёРіРЅСѓС‚Р°" if diff >= 0 else "[X] РЅРµ РґРѕСЃС‚РёРіРЅСѓС‚Р°"
            print(f"\nР¦РµР»РµРІР°СЏ РґРѕС…РѕРґРЅРѕСЃС‚СЊ: {target:.2%}, СЂРµР°Р»РёР·РѕРІР°РЅРЅР°СЏ: {realized:.2%} ({status})")

    stress_report = meta["stress_report"]
    if portfolio_metrics_summary and cfg.target_max_drawdown_pct is not None:
        max_dd_limit = abs(cfg.target_max_drawdown_pct)
        realized_mdd = portfolio_metrics_summary.get("max_drawdown")
        if realized_mdd is not None and not (realized_mdd != realized_mdd):
            mdd_ok = realized_mdd >= -max_dd_limit
            print(
                f"\nMax DD: {'PASS' if mdd_ok else 'FAIL'} (С†РµР»СЊ: -{max_dd_limit:.1%}, СЂРµР°Р»РёР·РѕРІР°РЅРѕ: {realized_mdd:.1%})"
            )
    if stress_report:
        st = stress_report.get("status", "N/A")
        reason = stress_report.get("fail_reason_code") or stress_report.get("skip_reason") or ""
        print(f"Stress Judge: {st}" + (f" ({reason})" if reason else ""))

    print(
        f"\nРљРµС€ СЃРѕС…СЂР°РЅС‘РЅ РІ cache/ (РґРЅРµРІРЅРѕР№: {meta['daily_cache_key']}, РјРµСЃСЏС‡РЅС‹Р№: {meta['monthly_cache_key']})"
    )

    if not meta["portfolio_valid"]:
        logger.warning(
            "Portfolio valid = False (e.g. MaxDD exceeds mandate). Report and files written; no exit (production workflow)."
        )

    try:
        from src.pdf_reports import try_rebuild_pdfs_after_main_report

        try_rebuild_pdfs_after_main_report(logger=logger)
    except Exception as e:
        logger.warning("PDF suite rebuild skipped: %s", e)


if __name__ == "__main__":
    main()
