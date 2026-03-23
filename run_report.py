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
import sys
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
from src.metrics_asset import asset_metrics_one_window
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
from src.portfolio_dynamic import portfolio_returns_nan_safe
from src.risk_contrib import cov_matrix_monthly, rc_vol_window
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

    Важно: эта функция не применяет никакой policy-логики к входным весам.
    Для Equal-Weight и Risk-Parity веса должны быть построены как baseline-портфели
    без block logic / risk budgets / RC caps / weight caps / discretionary overlays
    и скрытых policy-фильтров.
    """
    investor_currency = cfg.investor_currency
    tickers = cfg.tickers
    benchmark_base_ticker = cfg.benchmark_base_ticker
    windows_months = cfg.windows_months

    assets_meta = load_assets_metadata()

    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)

    mar_annual = get_mar_from_config(cfg)
    mar_monthly = mar_annual / 12 if mar_annual is not None else None

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
            f"Нет данных по cash proxy ({cash_proxy_ticker}); для расчёта портфеля используется нулевая доходность кэша."
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
    inner_join_months_used: int | None = None  # for risk Σ/RC (used in dynamic mode for gating)
    if backtest_mode == "dynamic_nan_safe":
        # Policy-compliant: within-block redistribution, RC/RB gating to cash, young ETFs do not truncate history
        cov_df_nan_safe = None
        if cfg.blocks and cfg.rc_block_targets and asset_returns_df.shape[0] >= 2:
            ret_inner = asset_returns_df.dropna(how="any").iloc[-720:]  # inner join, up to 60y for cov
            inner_join_months_used = len(ret_inner)
            if inner_join_months_used >= 2:
                cov_df_nan_safe = cov_matrix_monthly(ret_inner, ddof=1)
            if inner_join_months_used is not None and inner_join_months_used < 36 and inner_join_months_used >= 2:
                logger.warning(
                    "Inner-join sample for Σ/RC used in backtest gating is %d months (< 36). Risk estimates may be noisy.",
                    inner_join_months_used,
                )
        result = portfolio_returns_nan_safe(
            asset_returns_df,
            target_weights,
            cash_returns,
            blocks=cfg.blocks,
            rc_block_targets=cfg.rc_block_targets,
            rc_asset_cap_pct=cfg.rc_asset_cap_pct,
            cov_df=cov_df_nan_safe,
            return_diagnostics=True,
        )
        portfolio_returns, weights_used, backtest_diagnostics = result
        logger.info(
            "Backtest mode: dynamic_nan_safe (NaN-safe with within-block redistribution and RC-gating)."
        )
    else:
        # Simple (opt-in): no within-block redistribution, no RC-gating
        portfolio_returns, weights_used = portfolio_returns_nan_safe(
            asset_returns_df,
            target_weights,
            cash_returns,
        )
        backtest_diagnostics = None
        logger.info("Backtest mode: simple (no within-block redistribution / RC-gating).")

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
    
    # Gatekeepers: portfolio_valid = False, только если исторический MaxDD нарушает мандат.
    # Stress FAIL_STRESS теперь диагностический и не делает портфель "invalid".
    portfolio_valid = True
    if portfolio_metrics_summary and cfg.target_max_drawdown_pct is not None:
        realized_mdd = portfolio_metrics_summary.get("max_drawdown")
        if realized_mdd is not None and not (realized_mdd != realized_mdd):
            if realized_mdd < -abs(cfg.target_max_drawdown_pct):
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
    max_dd_ok = None
    if portfolio_metrics_summary and cfg.target_max_drawdown_pct is not None:
        realized_mdd = portfolio_metrics_summary.get("max_drawdown")
        if realized_mdd is not None and not (realized_mdd != realized_mdd):
            max_dd_ok = realized_mdd >= -abs(cfg.target_max_drawdown_pct)
    snapshot = build_snapshot(
        final_weights_total=weights,
        blocks=cfg.blocks,
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
        rc_block_targets=cfg.rc_block_targets,
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
    logger.info("Snapshot активов: %s", output_dir_final / "snapshot_assets.json")

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
            blocks=cfg.blocks,
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
        logger.error(f"Ошибка валидации конфигурации: {e}")
        raise SystemExit(1)

    if cfg.pending_fields:
        logger.info(f"Поля конфигурации, ожидающие ввода пользователя: {cfg.pending_fields}")

    if not cfg.weights:
        logger.error(
            "Portfolio weights are not set. Weights are produced by optimization (constraints + client metrics). "
            "Run the optimization step first: python run_optimization.py (writes portfolio_weights.yml)."
        )
        raise SystemExit(1)

    output_dir_csv = ensure_output_dir(Path(cfg.output_dir))
    output_dir_final = ensure_output_dir(Path(getattr(cfg, "output_dir_final", "ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ")))

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
        "  CSV в %s: asset_metrics, portfolio_metrics, rc_vol, correlation_matrix, rolling_*, var_es, eee, inputs/"
        % output_dir_csv
    )
    print(
        "  Финальные результаты в %s: portfolio_weights.yml, все JSON (snapshot_*, stress_report, run_metadata, data_policy, drawdown_structure), report.txt, report.html"
        % output_dir_final
    )

    if cfg.pending_fields:
        print(f"\nПоля, ожидающие ввода пользователя: {cfg.pending_fields}")

    if cfg.target_nominal_return_annual is not None and portfolio_metrics_summary:
        realized = portfolio_metrics_summary.get("cagr")
        target = cfg.target_nominal_return_annual
        if realized is not None:
            diff = realized - target
            status = "[OK] достигнута" if diff >= 0 else "[X] не достигнута"
            print(f"\nЦелевая доходность: {target:.2%}, реализованная: {realized:.2%} ({status})")

    stress_report = meta["stress_report"]
    if portfolio_metrics_summary and cfg.target_max_drawdown_pct is not None:
        max_dd_limit = abs(cfg.target_max_drawdown_pct)
        realized_mdd = portfolio_metrics_summary.get("max_drawdown")
        if realized_mdd is not None and not (realized_mdd != realized_mdd):
            mdd_ok = realized_mdd >= -max_dd_limit
            print(
                f"\nMax DD: {'PASS' if mdd_ok else 'FAIL'} (цель: -{max_dd_limit:.1%}, реализовано: {realized_mdd:.1%})"
            )
    if stress_report:
        st = stress_report.get("status", "N/A")
        reason = stress_report.get("fail_reason_code") or stress_report.get("skip_reason") or ""
        print(f"Stress Judge: {st}" + (f" ({reason})" if reason else ""))

    print(
        f"\nКеш сохранён в cache/ (дневной: {meta['daily_cache_key']}, месячный: {meta['monthly_cache_key']})"
    )

    if not meta["portfolio_valid"]:
        logger.warning(
            "Portfolio valid = False (e.g. MaxDD exceeds mandate). Report and files written; no exit (production workflow)."
        )


if __name__ == "__main__":
    main()
