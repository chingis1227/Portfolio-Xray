"""
Portfolio Metrics Standard - single entry script.
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

import numpy as np
import pandas as pd

from src.analysis_setup import build_analysis_setup, resolve_analysis_subject
from src.cache import cleanup_old_cache, clear_all_cache
from src.config import (
    load_validated_config,
    load_assets_metadata,
    resolve_cash_and_rf,
    resolve_local_benchmarks,
    get_mar_from_config,
    portfolio_total_tickers,
)
from src.candidate_run_context import (
    CandidateRunContext,
    ReviewRunContext,
    asset_betas_for_candidate_weights,
    coerce_factory_run_context,
    prepare_review_run_context,
    daily_panel_for_candidate_report,
    extended_diagnostic_betas_for_candidate,
    invariant_metrics_usable_for_report,
    slice_asset_metrics_for_tickers,
    weekly_factor_frames_for_candidate,
)
from src.config_schema import ConfigValidationError, PortfolioConfig
from src.data_loader import (
    load_daily_asset_returns_shared,
    load_monthly_data_shared,
    MonthlyDataResult,
)
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
    compute_candidate_config_fingerprint,
    print_snapshot,
    resolve_xray_snapshot_inputs,
    save_snapshot,
    _xray_summary_from_output_dir,
    write_report_html,
    write_report_txt,
)
from src.metrics_asset import asset_metrics_one_window, mandate_max_drawdown_full_history_check
from src.metrics_portfolio import portfolio_metrics_one_window
from src.portfolio_analytics import (
    compute_tail_risk_historical,
    drawdown_structure,
    effective_equity_exposure,
    rolling_beta,
    rolling_beta_correlation_block,
    rolling_correlation,
    rolling_sharpe,
    rolling_sortino,
    rolling_summary,
    rolling_vol_annual,
    tail_risk_flat_fields,
)
from src.portfolio_xray import build_portfolio_xray_v2
from src.optimization import get_risk_portfolio_tickers
from src.portfolio_dynamic import portfolio_returns_nan_safe
from src.risk_contrib import cov_matrix_monthly, rc_vol_window
from src.stress import (
    LOSS_GATE_MODE_DIAGNOSTIC,
    LOSS_GATE_MODE_MANDATE,
    prepared_synthetic_stress_usable,
    run_stress,
)
from src.hedge_gap_analysis_block import attach_hedge_gap_analysis_v1
from src.current_portfolio_stress_scorecard_block import (
    attach_current_portfolio_stress_scorecard_v1,
)
from src.core_mvp_historical_stress_replay import attach_core_mvp_historical_stress_replay_v1
from src.stress_results_block import attach_stress_results_v1
from src.stress_factors import (
    FACTOR_COLUMN_ORDER,
    FACTOR_TRADING_DAYS_10Y,
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
    compute_asset_factor_betas_from_daily_returns,
    build_factor_matrix,
    build_factor_matrix_daily,
    build_factor_matrix_monthly,
    attach_kalman_factor_betas_to_stress_report,
    build_diagnostic_oil_beta,
    build_factor_beta_diagnostic_overlay,
    enrich_historical_results_with_factor_attribution,
    factor_covariance_analytics,
    factor_variance_decomposition_weekly,
    macro_regime_csv_frames,
    macro_regime_diagnostics,
    macro_regime_diagnostics_with_panel,
    portfolio_pca_diagnostics,
    portfolio_pca_diagnostics_with_weekly_frames,
    weekly_factor_frames_cover_tickers,
    factor_beta_oos_stability_diagnostics,
    factor_beta_stability_diagnostics,
    factor_beta_stability_rows,
    factor_oos_beta_shock_explainability,
    portfolio_factor_regression_weekly,
    portfolio_factor_betas,
    asset_factor_betas_dict_from_df,
    rolling_beta_summary,
    write_rolling_betas_plot_html,
    write_rolling_betas_plot_pngs,
    asset_weekly_returns_from_daily,
    asset_daily_returns_from_daily,
)
from src.utils import setup_logging, warn_skipped_asset, info_data_summary, logger, coverage_ratio
from src.report_timing import ReportTimingCollector
from src.report_profile import (
    REPORT_PROFILE_FULL,
    REPORT_PROFILE_LIGHTWEIGHT,
    is_lightweight_comparison,
    normalize_report_profile,
)
from src.output_policy import (
    OUTPUT_PROFILE_VALUES,
    output_policy_for_profile,
    profile_from_legacy_report_profile,
    write_output_manifest,
)
from src.windows import slice_window, truncate_to_analysis_end
from src.returns_frequency import (
    MACRO_REGIME_FREQUENCY_DEFAULT,
    FACTOR_STRESS_FREQUENCY_DEFAULT,
    analysis_end_rule_description,
    calendar_window_to_n_periods,
    frequency_disclosure_from_resolution,
    normalize_returns_frequency,
    per_period_eff_from_annual_simple,
    periods_per_year as periods_per_year_for,
    resolve_returns_frequencies,
)
from src.portfolio_commentary import write_portfolio_commentary, write_stress_commentary
from src.candidate_launchpad import write_candidate_launchpad_outputs
from src.problem_classification import write_problem_classification_outputs
from src.product_bundle_scope import (
    DEFAULT_PRODUCT_BUNDLE_SCOPE,
    is_core_blocks_1_3_only,
    normalize_product_bundle_scope,
)
from src.regime_factor_analytics import (
    regime_factor_analytics,
    regime_factor_analytics_csv_frames,
    regime_factor_analytics_for_stress_report,
    regime_factor_analytics_summary,
)
from src.regime_portfolio_metrics import (
    build_regime_portfolio_metrics,
    expand_rf_monthly_to_daily,
    regime_portfolio_metrics_csv_frames,
    regime_portfolio_metrics_for_stress_report,
    regime_portfolio_metrics_summary,
)
from src.stress_scenario_analytics import build_stress_scenario_analytics
from src.scenario_library import build_scenario_library, summarize_scenario_classifications
from src.scenario_library_normalized import (
    build_scenario_library_normalized,
    summarize_normalized_classifications,
)
from src.data_yf import download_all


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Portfolio Metrics Standard - calculate and export portfolio metrics"
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
    parser.add_argument(
        "--materialize-current",
        action="store_true",
        help=(
            "Materialize current_weights into output_dir_final/current_portfolio/ sidecar "
            "(combined current-vs-policy workflow; does not overwrite policy Main artifacts)"
        ),
    )
    parser.add_argument(
        "--materialize-analysis-subject",
        action="store_true",
        help=(
            "Materialize the resolved analysis_subject into output_dir_final/analysis_subject/ "
            "before candidate generation."
        ),
    )
    parser.add_argument(
        "--output-profile",
        type=str,
        default=None,
        choices=sorted(OUTPUT_PROFILE_VALUES),
        help=(
            "Output profile (default: site_api). site_api/core_json write JSON/cache only; "
            "full_report enables CSV/TXT/HTML/PNG exports; legacy_export also allows PDF sidecars."
        ),
    )
    parser.add_argument(
        "--review-mode",
        type=str,
        choices=("core", "full"),
        default=None,
        help=(
            "Portfolio review mode for --materialize-analysis-subject: core uses "
            "lightweight_comparison + shared ReviewRunContext; full uses full report profile."
        ),
    )
    parser.add_argument(
        "--use-review-run-context",
        action="store_true",
        help=(
            "Preload ReviewRunContext (shared monthly/macro/PCA) before analysis_subject report. "
            "Default when --review-mode core."
        ),
    )
    parser.add_argument(
        "--no-review-run-context",
        action="store_true",
        help="Disable shared ReviewRunContext even when --review-mode core.",
    )
    parser.add_argument(
        "--core-diagnostics-only",
        action="store_true",
        help=(
            "Blocks 1-3 only: write input/X-Ray/stress JSON; skip Problem Classification, "
            "Candidate Launchpad, and AI Commentary product adapters."
        ),
    )
    return parser.parse_args()


def build_derived_assumptions(
    cfg: PortfolioConfig,
    cash_proxy_ticker: str,
    rf_source: str,
    local_benchmark_map: dict[str, str],
    analysis_end: str,
    windows_months: list[int],
    *,
    returns_frequency: str | None = None,
    periods_per_year: int = 12,
) -> dict:
    """
    Build dictionary of derived assumptions used in the run.
    These are values computed from config (not directly specified).
    """
    freq_res = resolve_returns_frequencies(returns_frequency)
    rf_mode = freq_res.main_metrics
    # Liquidity life floor amount = liquidity_need_months * monthly_expenses (single source of truth)
    liquidity_need_amount = cfg.liquidity_need_months * (cfg.monthly_expenses or 0)

    derived = {
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
        "returns_frequency": rf_mode,
        "configured_returns_frequency": freq_res.configured,
        "main_metrics_returns_frequency_forced": freq_res.forced_to_monthly,
        "periods_per_year": periods_per_year,
        "analysis_end_rule": analysis_end_rule_description(rf_mode),
    }
    return derived


def regime_mar_daily_from_annual(mar_annual: float | None) -> float | None:
    """Return daily MAR override for regime metrics; None keeps daily risk-free as MAR."""

    if mar_annual is None:
        return None
    return per_period_eff_from_annual_simple(float(mar_annual), "daily")


def run_portfolio_report_for_weights(
    cfg: PortfolioConfig,
    weights: dict[str, float],
    *,
    run_timestamp: str,
    output_dir_csv: Path,
    output_dir_final: Path,
    backtest_mode_override: str | None = None,
    no_cache: bool = False,
    weights_source: str | None = None,
    portfolio_role_override: str | None = None,
    report_profile: str | None = None,
    output_profile: str | None = None,
    product_bundle_scope: str | None = None,
    run_context: CandidateRunContext | ReviewRunContext | None = None,
    enable_report_timing: bool | None = None,
) -> tuple[dict | None, dict]:
    """
    Core metrics/stress/report pipeline, parameterized by explicit weights and output dirs.

    Important: this function does not apply policy logic to input weights.
    Equal-Weight and Risk-Parity weights must be built as baseline portfolios
    without RC caps / weight caps / discretionary overlays
    or hidden policy filters.

    ``output_profile``:
    - ``site_api`` / ``core_json`` (default): JSON contracts and cache only.
    - ``lightweight_comparison``: comparison-ready JSON snapshots/stress only.
    - ``full_report``: CSV/TXT/HTML/PNG export surfaces.
    - ``legacy_export``: full legacy export profile; PDF rebuild is still an explicit caller action.

    ``report_profile`` is the older calculation/export selector and is still accepted for
    compatibility. When ``output_profile`` is omitted, ``report_profile=full`` maps to
    ``full_report`` and ``report_profile=lightweight_comparison`` maps to JSON-only
    lightweight comparison.

    ``run_context``: optional factory or review shared context (one monthly load + factor/scenario cache).

    ``enable_report_timing``: when ``True``, record per-block seconds in ``meta["report_timing"]``
    (also enabled by env ``PORTFOLIO_REPORT_TIMING=1``). Default off for non-factory runs.
    """
    review_run_context = run_context if isinstance(run_context, ReviewRunContext) else None
    run_context = coerce_factory_run_context(run_context)
    bundle_scope = normalize_product_bundle_scope(product_bundle_scope)
    core_blocks_only = is_core_blocks_1_3_only(bundle_scope)
    report_timing = ReportTimingCollector.for_run(enable_report_timing=enable_report_timing)
    resolved_output_profile = output_profile or profile_from_legacy_report_profile(report_profile)
    output_policy = output_policy_for_profile(resolved_output_profile)
    output_dir_final.mkdir(parents=True, exist_ok=True)
    if output_policy.write_csv:
        output_dir_csv.mkdir(parents=True, exist_ok=True)
    effective_report_profile = (
        report_profile
        if report_profile is not None
        else (
            REPORT_PROFILE_LIGHTWEIGHT
            if output_policy.lightweight_calculation_path
            else REPORT_PROFILE_FULL
        )
    )
    profile = normalize_report_profile(effective_report_profile)
    lightweight = is_lightweight_comparison(profile)
    csv_export_dir = output_dir_csv if output_policy.write_csv else None
    factory_factor = (
        run_context.factor_stress
        if run_context is not None and run_context.factor_stress is not None
        else None
    )
    investor_currency = cfg.investor_currency
    benchmark_base_ticker = cfg.benchmark_base_ticker
    windows_months = cfg.windows_months

    freq_res = resolve_returns_frequencies(getattr(cfg, "returns_frequency", None))

    assets_meta = load_assets_metadata()

    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    tickers = portfolio_total_tickers(cfg.tickers, weights, cash_proxy_ticker)

    mar_annual = get_mar_from_config(cfg)

    config_local_override = cfg.local_benchmark_map or {}
    local_benchmark_map = resolve_local_benchmarks(
        tickers, config_local_override, base_benchmark=benchmark_base_ticker
    )

    logger.info(f"Investor currency: {investor_currency}")
    logger.info(f"Base benchmark: {benchmark_base_ticker}")
    logger.info(f"Cash proxy: {cash_proxy_ticker}")
    logger.info(f"Risk-free source: {rf_source}")
    logger.info(f"Local benchmarks: {local_benchmark_map}")

    if cfg.target_nominal_return_annual is not None:
        logger.info(f"Target return: {cfg.target_nominal_return_annual:.2%}")

    if run_context is not None:
        data = run_context.monthly_data
        no_cache = run_context.no_cache
    else:
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
            returns_frequency=freq_res.configured,
            data_provider=getattr(cfg, "market_data_provider", None),
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
    monthly_returns_raw = monthly_returns
    monthly_prices = truncate_to_analysis_end(monthly_prices, analysis_end)
    monthly_returns = truncate_to_analysis_end(monthly_returns, analysis_end)
    monthly_log_returns = truncate_to_analysis_end(monthly_log_returns, analysis_end)
    rf_monthly = truncate_to_analysis_end(rf_monthly, analysis_end)
    benchmark_returns = truncate_to_analysis_end(benchmark_returns, analysis_end)
    cash_returns = truncate_to_analysis_end(cash_returns, analysis_end)
    daily_cache_key = data.daily_cache_key
    monthly_cache_key = data.monthly_cache_key
    returns_frequency = normalize_returns_frequency(data.returns_frequency)
    configured_returns_frequency = normalize_returns_frequency(data.configured_returns_frequency)
    freq_res = resolve_returns_frequencies(configured_returns_frequency)
    ppy = periods_per_year_for(returns_frequency)
    mar_period = (
        per_period_eff_from_annual_simple(float(mar_annual), returns_frequency)
        if mar_annual is not None
        else None
    )
    regime_mar_daily = regime_mar_daily_from_annual(mar_annual)

    # =========================================================================
    # STEP 4: Compute portfolio returns (NaN-safe dynamic; production vs research mode)
    # =========================================================================

    # Ensure cash_returns is aligned to monthly index so common_idx is non-empty (avoid empty portfolio returns)
    if cash_returns.empty or len(cash_returns.index) == 0:
        logger.warning(
            f"No data for cash proxy ({cash_proxy_ticker}); portfolio calculation uses zero cash return."
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
            inner_cap = max(2, int(round(720.0 * float(ppy) / 12.0)))
            ret_inner = asset_returns_df.dropna(how="any").iloc[-inner_cap:]
            inner_join_months_used = len(ret_inner)
            min_cov_obs = calendar_window_to_n_periods(36, returns_frequency)
            if (
                inner_join_months_used is not None
                and inner_join_months_used < min_cov_obs
                and inner_join_months_used >= 2
            ):
                logger.warning(
                    "Inner-join sample for covariance context is %d observations (< ~3 calendar years at %s cadence); "
                    "risk estimates may be noisy.",
                    inner_join_months_used,
                    returns_frequency,
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

    with report_timing.block("save_inputs"):
        if output_policy.write_csv:
            save_inputs(
                output_dir_csv,
                monthly_prices,
                monthly_returns,
                rf_monthly,
                benchmark_returns,
                cash_returns,
                fx_series_used,
                monthly_returns_raw=monthly_returns_raw,
                analysis_end=analysis_end_str,
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
        logger.info("Data availability summary:")
        for ticker in tickers:
            r = monthly_returns.get(ticker)
            if r is None or r.dropna().empty:
                warn_skipped_asset(ticker, "no return data")
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
    use_invariant_metrics = (
        run_context is not None
        and invariant_metrics_usable_for_report(
            run_context.invariant_metrics,
            tickers=tickers,
            windows_months=windows_months,
        )
    )
    with report_timing.block("asset_metrics"):
        if use_invariant_metrics and run_context is not None:
            inv = run_context.invariant_metrics
            assert inv is not None
            asset_metrics_all = slice_asset_metrics_for_tickers(
                inv.asset_metrics_all,
                tickers,
            )
            for wm, rows in zip(windows_months, asset_metrics_all):
                if output_policy.write_csv:
                    export_asset_metrics_csv(rows, wm, output_dir_csv)
        else:
            for wm in windows_months:
                rows = []
                for ticker in tickers:
                    r_simple = monthly_returns.get(ticker)
                    r_log = monthly_log_returns.get(ticker)
                    if r_simple is None or r_log is None:
                        warn_skipped_asset(ticker, "no return data")
                        continue
                    if coverage_ratio(r_simple, analysis_end_ts, wm) < coverage_threshold:
                        warn_skipped_asset(
                            ticker,
                            "coverage in %d-month window < %.0f%%" % (wm, coverage_threshold * 100),
                        )
                        continue

                    # Get local benchmark returns for Beta_local
                    local_bench_ticker = local_benchmark_map.get(ticker)
                    local_bench_returns = None
                    if local_bench_ticker and local_bench_ticker != benchmark_base_ticker:
                        local_bench_returns = monthly_returns.get(local_bench_ticker)
                        if local_bench_returns is None:
                            logger.warning(
                                f"Local benchmark {local_bench_ticker} for {ticker} not found, "
                                f"using base benchmark {benchmark_base_ticker}"
                            )

                    row = asset_metrics_one_window(
                        ticker,
                        r_simple,
                        r_log,
                        rf_monthly,
                        benchmark_returns,
                        analysis_end,
                        wm,
                        mar=mar_period,
                        local_benchmark_returns=local_bench_returns,
                        periods_per_year=ppy,
                    )
                    rows.append(row)
                asset_metrics_all.append(rows)
                if output_policy.write_csv:
                    export_asset_metrics_csv(rows, wm, output_dir_csv)

    # =========================================================================
    # STEP 7: Compute portfolio metrics per window
    # =========================================================================

    portfolio_metrics_list = []
    with report_timing.block("portfolio_metrics"):
        for wm in windows_months:
            pm = portfolio_metrics_one_window(
                portfolio_returns,
                rf_monthly,
                analysis_end,
                wm,
                benchmark_returns=benchmark_returns,
                mar=mar_period,
                periods_per_year=ppy,
                benchmark_ticker=benchmark_base_ticker,
                risk_free_source=rf_source,
                returns_frequency=returns_frequency,
            )
            portfolio_metrics_list.append(pm)
        if output_policy.write_csv:
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
            longest_window_metrics = max(
                portfolio_metrics_list, key=lambda x: x.get("window_months", 0)
            )
            portfolio_metrics_summary = longest_window_metrics

    # =========================================================================
    # STEP 8: Compute RC_vol and correlation matrix per window
    # =========================================================================

    asset_cols = [t for t in tickers if t in monthly_returns.columns]
    rc_for_snapshot = None
    rc_by_window: dict[str, pd.Series] = {}
    rc_csv_by_window: dict[str, str] = {}
    corr_csv_by_window: dict[str, str] = {}
    corr_by_window: dict[str, pd.DataFrame] = {}
    use_invariant_corr = use_invariant_metrics
    with report_timing.block("rc_corr"):
        for wm in windows_months:
            if not asset_cols:
                logger.warning(f"RC_vol: no assets available for calculation")
                continue
            returns_slice = slice_window(monthly_returns[asset_cols], analysis_end, wm)
            weights_slice = slice_window(
                weights_used.reindex(columns=asset_cols).fillna(0), analysis_end, wm
            )
            returns_slice = returns_slice.dropna(how="all")
            if returns_slice.empty or len(returns_slice) < 2:
                window_label = f"{wm // 12}Y" if wm >= 12 else f"{wm}M"
                logger.warning(
                    f"RC_vol ({window_label}): insufficient data ( {len(returns_slice)} months available)"
                )
                continue

            # RC_vol
            rc = rc_vol_window(returns_slice, weights_slice, ddof=1)
            if wm == 60:
                rc_for_snapshot = rc
            suffix = "3y" if wm == 36 else "5y" if wm == 60 else "10y"
            rc_filename = f"rc_vol_{suffix}.csv"
            if output_policy.write_csv:
                export_rc_vol_csv(rc, output_dir_csv / rc_filename)
            # Store per-window RC for snapshot windows section
            if wm in (36, 60, 120):
                key = "3y" if wm == 36 else "5y" if wm == 60 else "10y"
                rc_by_window[key] = rc
                rc_csv_by_window[key] = rc_filename

            # Correlation matrix (invariant across candidates when factory context provides it)
            corr_matrix: pd.DataFrame | None = None
            if use_invariant_corr and run_context is not None:
                inv = run_context.invariant_metrics
                if inv is not None and wm in inv.correlation_by_window:
                    cached = inv.correlation_by_window[wm]
                    try:
                        corr_matrix = cached.loc[asset_cols, asset_cols]
                    except KeyError:
                        corr_matrix = None
            if corr_matrix is None:
                corr_matrix = returns_slice.corr()
            if output_policy.write_csv:
                export_correlation_matrix_csv(corr_matrix, wm, output_dir_csv)
            if wm in (36, 60, 120):
                key = "3y" if wm == 36 else "5y" if wm == 60 else "10y"
                corr_by_window[key] = corr_matrix
                corr_csv_by_window[key] = f"correlation_matrix_{suffix}.csv"

    # =========================================================================
    # STEP 9: Stress testing (per docs/docs/stress_testing_spec.md)
    # =========================================================================

    portfolio_betas_3y_dict: dict[str, float] = {}
    portfolio_betas_5y_dict: dict[str, float] = {}
    portfolio_betas_10y_dict: dict[str, float] = {}
    diagnostic_betas_5y_extended: dict[str, float] = {}
    diagnostic_betas_10y_extended: dict[str, float] = {}
    recession_factor_returns = pd.DataFrame()
    # Long history for historical episode factor sums (dotcom, etc.); recession calibration stays 2007+.
    scenario_episode_factor_returns = pd.DataFrame()
    asset_betas_df = pd.DataFrame()
    portfolio_betas_dict: dict[str, float] = {}
    factor_diagnostics_meta: dict[str, Any] = {
        "status": "unavailable",
        "source": None,
        "unavailable_reason": "factor_beta_setup_not_run",
        "asset_beta_coverage_count": 0,
        "factor_beta_keys": [],
        "factor_attribution_scope": "unavailable",
        "available_factors": [],
        "missing_factors": [],
        "factor_missing_reasons": {},
        "factor_columns_used": [],
        "aligned_weekly_observations": None,
        "factor_load_diagnostics": None,
        "requested_tickers": [],
        "covered_tickers": [],
        "analysis_end": analysis_end_str,
    }
    report_timing.start_block("factor_betas")
    try:
        beta_tickers = [t for t in tickers if weights.get(t, 0) > 0]
        if not beta_tickers:
            beta_tickers = list(tickers)
        factor_diagnostics_meta["requested_tickers"] = list(beta_tickers)

        def _factor_meta(
            *,
            status: str,
            source: str | None,
            reason: str | None,
            betas_df: pd.DataFrame | None,
        ) -> dict[str, Any]:
            covered = []
            if betas_df is not None and not betas_df.empty:
                covered = [str(x) for x in betas_df.index]
            beta_keys = []
            if betas_df is not None and not betas_df.empty:
                beta_keys = [str(c) for c in betas_df.columns]
            factor_load_diagnostics = (
                getattr(betas_df, "attrs", {}).get("factor_load_diagnostics")
                if betas_df is not None
                else None
            )
            factor_columns_used = (
                list(getattr(betas_df, "attrs", {}).get("factor_columns_used") or [])
                if betas_df is not None
                else []
            )
            available_factors = []
            missing_factors = []
            factor_missing_reasons: dict[str, str] = {}
            if isinstance(factor_load_diagnostics, dict):
                available_factors = [
                    str(x) for x in factor_load_diagnostics.get("available_factors") or []
                ]
                missing_factors = [
                    str(x) for x in factor_load_diagnostics.get("missing_factors") or []
                ]
                by_factor = factor_load_diagnostics.get("by_factor") or {}
                if isinstance(by_factor, dict):
                    for factor_name in missing_factors:
                        row = by_factor.get(factor_name) or {}
                        factor_missing_reasons[factor_name] = str(
                            row.get("reason") or "not_available"
                        )
            if beta_keys and set(beta_keys) == {"beta_eq"}:
                attribution_scope = "equity_only"
            elif beta_keys:
                attribution_scope = "multi_factor"
            else:
                attribution_scope = "unavailable"
            return {
                "status": status,
                "source": source,
                "unavailable_reason": reason,
                "asset_beta_coverage_count": int(len(covered)),
                "factor_beta_keys": beta_keys,
                "factor_attribution_scope": attribution_scope,
                "available_factors": available_factors,
                "missing_factors": missing_factors,
                "factor_missing_reasons": factor_missing_reasons,
                "factor_columns_used": factor_columns_used,
                "aligned_weekly_observations": (
                    int(getattr(betas_df, "attrs", {}).get("aligned_weekly_observations"))
                    if betas_df is not None
                    and getattr(betas_df, "attrs", {}).get("aligned_weekly_observations") is not None
                    else None
                ),
                "factor_load_diagnostics": factor_load_diagnostics,
                "requested_tickers": list(beta_tickers),
                "covered_tickers": covered,
                "analysis_end": analysis_end_str,
            }

        def _portfolio_betas_weekly(window_weeks: int) -> tuple[pd.DataFrame, dict[str, float]]:
            asset_betas_win = compute_asset_factor_betas_weekly(
                beta_tickers,
                analysis_end_str,
                window_weeks,
            )
            return asset_betas_win, portfolio_factor_betas(weights, asset_betas_win)

        beta_setup_reasons: list[str] = []
        beta_source: str | None = None
        asset_betas_3y_df = pd.DataFrame()
        asset_betas_5y_df = pd.DataFrame()
        asset_betas_10y_df = pd.DataFrame()
        if factory_factor is not None:
            beta_setup_reasons.extend(list(factory_factor.beta_setup_reasons))
            recession_factor_returns = factory_factor.recession_factor_returns
            scenario_episode_factor_returns = factory_factor.scenario_episode_factor_returns
            asset_betas_5y_df, asset_betas_10y_df, beta_source = asset_betas_for_candidate_weights(
                factory_factor,
                beta_tickers=beta_tickers,
                benchmark_base_ticker=benchmark_base_ticker,
                analysis_end_str=analysis_end_str,
            )
            daily_asset_returns_for_betas = factory_factor.daily_asset_returns_for_betas
            if not daily_asset_returns_for_betas.empty:
                diagnostic_betas_5y_extended, diagnostic_betas_10y_extended = (
                    extended_diagnostic_betas_for_candidate(
                        factory_factor,
                        weights=weights,
                        beta_tickers=beta_tickers,
                        benchmark_base_ticker=benchmark_base_ticker,
                        analysis_end_str=analysis_end_str,
                    )
                )
        else:
            try:
                beta_daily_tickers = list(
                    dict.fromkeys(list(beta_tickers) + [benchmark_base_ticker])
                )
                daily_asset_returns_for_betas, _cash_returns_for_betas = (
                    load_daily_asset_returns_shared(
                        tickers=beta_daily_tickers,
                        benchmark_base_ticker=benchmark_base_ticker,
                        cash_proxy_ticker=cash_proxy_ticker,
                        investor_currency=investor_currency,
                        windows_months=windows_months,
                        assets_meta=assets_meta,
                        daily_cache_key=daily_cache_key,
                        analysis_end=analysis_end,
                        no_cache=no_cache,
                        local_benchmark_map=local_benchmark_map,
                        data_provider=getattr(cfg, "market_data_provider", None),
                    )
                )
                if daily_asset_returns_for_betas.empty:
                    beta_setup_reasons.append("cached_daily_returns_empty")
                else:
                    asset_betas_5y_df = compute_asset_factor_betas_from_daily_returns(
                        daily_asset_returns_for_betas,
                        analysis_end_str,
                        FACTOR_WEEKS_5Y,
                        asset_tickers=beta_tickers,
                        equity_factor_ticker=benchmark_base_ticker,
                    )
                    asset_betas_10y_df = compute_asset_factor_betas_from_daily_returns(
                        daily_asset_returns_for_betas,
                        analysis_end_str,
                        FACTOR_WEEKS_10Y,
                        asset_tickers=beta_tickers,
                        equity_factor_ticker=benchmark_base_ticker,
                    )
                    asset_betas_3y_df = compute_asset_factor_betas_from_daily_returns(
                        daily_asset_returns_for_betas,
                        analysis_end_str,
                        FACTOR_WEEKS_3Y,
                        asset_tickers=beta_tickers,
                        equity_factor_ticker=benchmark_base_ticker,
                    )
                    diagnostic_betas_5y_extended = portfolio_factor_betas(
                        weights,
                        compute_asset_factor_betas_from_daily_returns(
                            daily_asset_returns_for_betas,
                            analysis_end_str,
                            FACTOR_WEEKS_5Y,
                            factor_columns=FACTOR_COLUMN_ORDER,
                            asset_tickers=beta_tickers,
                            equity_factor_ticker=benchmark_base_ticker,
                        ),
                    )
                    diagnostic_betas_10y_extended = portfolio_factor_betas(
                        weights,
                        compute_asset_factor_betas_from_daily_returns(
                            daily_asset_returns_for_betas,
                            analysis_end_str,
                            FACTOR_WEEKS_10Y,
                            factor_columns=FACTOR_COLUMN_ORDER,
                            asset_tickers=beta_tickers,
                            equity_factor_ticker=benchmark_base_ticker,
                        ),
                    )
                    if not asset_betas_5y_df.empty:
                        beta_source = "cached_daily_returns_weekly_ols"
                    else:
                        beta_setup_reasons.append(
                            "cached_daily_returns_weekly_ols_no_aligned_betas"
                        )
            except Exception as e_cached:
                beta_setup_reasons.append(f"cached_daily_returns_weekly_ols_error:{e_cached}")

        if asset_betas_5y_df.empty:
            try:
                asset_betas_5y_df, portfolio_betas_5y_dict = _portfolio_betas_weekly(FACTOR_WEEKS_5Y)
                asset_betas_10y_df, portfolio_betas_10y_dict = _portfolio_betas_weekly(FACTOR_WEEKS_10Y)
                asset_betas_3y_df, portfolio_betas_3y_dict = _portfolio_betas_weekly(FACTOR_WEEKS_3Y)
                diagnostic_betas_5y_extended = portfolio_factor_betas(
                    weights,
                    compute_asset_factor_betas_weekly(
                        beta_tickers,
                        analysis_end_str,
                        FACTOR_WEEKS_5Y,
                        factor_columns=FACTOR_COLUMN_ORDER,
                    ),
                )
                diagnostic_betas_10y_extended = portfolio_factor_betas(
                    weights,
                    compute_asset_factor_betas_weekly(
                        beta_tickers,
                        analysis_end_str,
                        FACTOR_WEEKS_10Y,
                        factor_columns=FACTOR_COLUMN_ORDER,
                    ),
                )
                if not asset_betas_5y_df.empty:
                    beta_source = "direct_yfinance_weekly_ols"
                else:
                    beta_setup_reasons.append("direct_yfinance_weekly_ols_no_aligned_betas")
            except Exception as e_direct:
                beta_setup_reasons.append(f"direct_yfinance_weekly_ols_error:{e_direct}")
        else:
            portfolio_betas_5y_dict = portfolio_factor_betas(weights, asset_betas_5y_df)
            portfolio_betas_10y_dict = portfolio_factor_betas(weights, asset_betas_10y_df)
            if not asset_betas_3y_df.empty:
                portfolio_betas_3y_dict = portfolio_factor_betas(weights, asset_betas_3y_df)
        if not portfolio_betas_3y_dict:
            try:
                _, portfolio_betas_3y_dict = _portfolio_betas_weekly(FACTOR_WEEKS_3Y)
            except Exception as e_3y:
                beta_setup_reasons.append(f"factor_betas_3y_weekly_ols_error:{e_3y}")

        # Keep stress engine input/backward compatibility aligned to 5Y betas.
        asset_betas_df = asset_betas_5y_df
        portfolio_betas_dict = portfolio_betas_5y_dict
        if not asset_betas_df.empty:
            factor_diagnostics_meta = _factor_meta(
                status="available",
                source=beta_source or "unknown_weekly_ols",
                reason=None,
                betas_df=asset_betas_df,
            )
        else:
            reason = "; ".join(beta_setup_reasons) if beta_setup_reasons else "no_asset_factor_betas_computed"
            factor_diagnostics_meta = _factor_meta(
                status="unavailable",
                source=None,
                reason=reason,
                betas_df=asset_betas_df,
            )
        if factory_factor is None:
            try:
                recession_factor_returns = build_factor_matrix("2007-01-01", analysis_end_str)
            except Exception as e:
                logger.warning(
                    f"Recession factor calibration setup failed: {e}; "
                    "recession severe will use fallback."
                )
            try:
                scenario_episode_factor_returns = build_factor_matrix(
                    "1990-01-01",
                    analysis_end_str,
                    require_complete_rows=False,
                )
            except Exception as e_long:
                logger.warning(
                    "Long-window factor matrix (1990+) for historical episode fallback failed: %s",
                    e_long,
                )
                scenario_episode_factor_returns = pd.DataFrame()
    except Exception as e:
        logger.warning(f"Stress factor/beta setup failed: {e}; stress report may use fallback only.")
        asset_betas_df = pd.DataFrame()
        portfolio_betas_dict = {}
        factor_diagnostics_meta = {
            "status": "unavailable",
            "source": None,
            "unavailable_reason": str(e),
            "asset_beta_coverage_count": 0,
            "factor_beta_keys": [],
            "factor_attribution_scope": "unavailable",
            "available_factors": [],
            "missing_factors": list(FACTOR_COLUMN_ORDER),
            "factor_missing_reasons": {
                str(factor): str(e) for factor in FACTOR_COLUMN_ORDER
            },
            "factor_columns_used": [],
            "aligned_weekly_observations": None,
            "factor_load_diagnostics": None,
            "requested_tickers": [t for t in tickers if weights.get(t, 0) > 0] or list(tickers),
            "covered_tickers": [],
            "analysis_end": analysis_end_str,
        }
    finally:
        report_timing.end_block("factor_betas")

    report_timing.start_block("run_stress")
    hedge_assets = []
    for ticker in tickers:
        meta = assets_meta.get(ticker) if isinstance(assets_meta, dict) else None
        if not isinstance(meta, dict):
            continue
        roles = [str(x).lower() for x in (meta.get("risk_role") or [])]
        if any(r in {"crisis_hedge", "defensive", "inflation_hedge", "tail_hedge"} for r in roles):
            hedge_assets.append(str(ticker))

    stress_cov_base: pd.DataFrame | None = None
    if use_invariant_metrics and run_context is not None:
        inv = run_context.invariant_metrics
        if inv is not None and not inv.stress_cov_base.empty:
            stress_cov_base = inv.stress_cov_base

    stress_cov_method = str(getattr(cfg, "stress_cov_method", None) or "taxonomy_blend_v1")
    prepared_synthetic = None
    if use_invariant_metrics and run_context is not None:
        prepared = run_context.prepared_synthetic_stress
        asset_cols_for_stress = [t for t in tickers if t in monthly_returns.columns]
        if prepared_synthetic_stress_usable(
            prepared,
            asset_cols=asset_cols_for_stress,
            stress_cov_method=stress_cov_method,
        ):
            prepared_synthetic = prepared

    loss_gate_mode = (
        LOSS_GATE_MODE_DIAGNOSTIC
        if getattr(cfg, "analysis_mode", "") == "analyze_current_weights"
        else LOSS_GATE_MODE_MANDATE
    )
    stress_report = run_stress(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas_df,
        portfolio_betas=portfolio_betas_dict,
        target_max_drawdown_pct=cfg.target_max_drawdown_pct
        if loss_gate_mode == LOSS_GATE_MODE_MANDATE
        else None,
        cash_proxy_ticker=cash_proxy_ticker,
        factor_returns=recession_factor_returns,
        scenario_overrides=getattr(cfg, "stress_scenario_overrides", None),
        hedge_assets=hedge_assets,
        beta_data_source=factor_diagnostics_meta.get("source"),
        cov_base=stress_cov_base,
        stress_cov_method=stress_cov_method,
        prepared_synthetic=prepared_synthetic,
        loss_gate_mode=loss_gate_mode,
    )
    stress_report["generated_at"] = run_timestamp
    stress_report["analysis_end"] = analysis_end_str
    stress_report["factor_betas_3y"] = {k: round(v, 4) for k, v in (portfolio_betas_3y_dict or {}).items()}
    stress_report["factor_betas_5y"] = {k: round(v, 4) for k, v in (portfolio_betas_5y_dict or {}).items()}
    stress_report["factor_betas_10y"] = {k: round(v, 4) for k, v in (portfolio_betas_10y_dict or {}).items()}
    stress_report["factor_betas"] = dict(stress_report["factor_betas_5y"])
    stress_report["asset_factor_betas"] = asset_factor_betas_dict_from_df(asset_betas_df)
    stress_report["asset_factor_betas_meta"] = {
        "source": factor_diagnostics_meta.get("source") or "unavailable",
        "window_weeks": int(FACTOR_WEEKS_5Y),
        "n_assets": int(len(asset_betas_df.index)) if asset_betas_df is not None and not asset_betas_df.empty else 0,
    }
    stress_report["factor_diagnostics_meta"] = factor_diagnostics_meta
    if factor_diagnostics_meta.get("status") != "available":
        trust = stress_report.setdefault("data_trust_summary", {})
        lines = list(trust.get("user_summary_lines") or [])
        reason = factor_diagnostics_meta.get("unavailable_reason") or "factor diagnostics were not produced"
        lines.append(f"Factor diagnostics unavailable: {reason}. Synthetic stress used disclosed fallback assumptions.")
        trust["user_summary_lines"] = lines
    else:
        scope = factor_diagnostics_meta.get("factor_attribution_scope")
        trust = stress_report.setdefault("data_trust_summary", {})
        lines = list(trust.get("user_summary_lines") or [])
        if scope == "equity_only":
            missing = factor_diagnostics_meta.get("missing_factors") or []
            reasons = factor_diagnostics_meta.get("factor_missing_reasons") or {}
            reason_bits = [
                f"{factor}: {reasons.get(factor, 'not_available')}"
                for factor in list(missing)[:6]
            ]
            suffix = f" Missing factor reasons: {'; '.join(reason_bits)}." if reason_bits else ""
            lines.append(
                "Factor attribution is equity-only because non-equity factor proxies were not available."
                + suffix
            )
        elif scope == "multi_factor":
            keys = ", ".join(str(k) for k in factor_diagnostics_meta.get("factor_beta_keys") or [])
            lines.append(f"Factor attribution uses multi-factor betas: {keys}.")
        trust["user_summary_lines"] = lines
    report_timing.end_block("run_stress")
    # Portfolio factor regression diagnostics (5Y/10Y): t/p/CI/R^2 on weekly data, same factor matrix definition.
    report_timing.start_block("factor_regression")
    shared_weekly_frames = (
        weekly_factor_frames_for_candidate(factory_factor, tickers=tickers)
        if factory_factor is not None
        else None
    )
    stress_report["factor_regression_3y"] = {}
    stress_report["factor_regression_5y"] = {}
    stress_report["factor_regression_10y"] = {}
    factor_regression_5y_extended: dict[str, Any] = {}
    factor_regression_10y_extended: dict[str, Any] = {}

    def _factor_regression_unavailable_reason(window_label: str) -> str:
        scope = factor_diagnostics_meta.get("factor_attribution_scope") or "unknown"
        available = factor_diagnostics_meta.get("available_factors") or []
        missing = factor_diagnostics_meta.get("missing_factors") or []
        return (
            f"{window_label} factor regression unavailable: no aligned multi-factor weekly "
            f"regression panel; factor_attribution_scope={scope}; "
            f"available_factors={','.join(str(x) for x in available) if available else 'none'}; "
            f"missing_factors={','.join(str(x) for x in missing) if missing else 'none'}"
        )

    try:
        regression_3y = portfolio_factor_regression_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_3Y,
            shared_frames=shared_weekly_frames,
        )
        stress_report["factor_regression_3y"] = regression_3y
        if not regression_3y:
            stress_report["factor_regression_3y_error"] = _factor_regression_unavailable_reason("3Y")
    except Exception as e:
        stress_report["factor_regression_3y_error"] = str(e)
        logger.warning(f"Factor regression diagnostics (3Y) failed: {e}")
    try:
        regression_5y = portfolio_factor_regression_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_5Y,
            shared_frames=shared_weekly_frames,
        )
        stress_report["factor_regression_5y"] = regression_5y
        if not regression_5y:
            stress_report["factor_regression_5y_error"] = _factor_regression_unavailable_reason("5Y")
    except Exception as e:
        stress_report["factor_regression_5y_error"] = str(e)
        logger.warning(f"Factor regression diagnostics (5Y) failed: {e}")
    try:
        regression_10y = portfolio_factor_regression_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_10Y,
            shared_frames=shared_weekly_frames,
        )
        stress_report["factor_regression_10y"] = regression_10y
        if not regression_10y:
            stress_report["factor_regression_10y_error"] = _factor_regression_unavailable_reason("10Y")
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
            shared_frames=shared_weekly_frames,
        )
        factor_regression_10y_extended = portfolio_factor_regression_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_10Y,
            factor_columns=FACTOR_COLUMN_ORDER,
            shared_frames=shared_weekly_frames,
        )
    except Exception as e:
        stress_report["diagnostic_oil_beta_regression_error"] = str(e)
        logger.warning(f"Extended Oil diagnostic regression failed: {e}")
    report_timing.end_block("factor_regression")

    # Rolling beta stability (diagnostic): 3Y/5Y/10Y weekly + monthly betas, OOS checks, and severity.
    rb: dict[str, pd.DataFrame] = {}
    if lightweight:
        stress_report["factor_betas_rolling_skip_reason"] = "lightweight_comparison_profile"
    try:
        if lightweight:
            raise RuntimeError("skip_rolling_betas_lightweight_profile")
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
        csv_paths: dict[str, str] = {}
        if output_policy.write_csv:
            for lbl, df_rb in rb.items():
                if df_rb is None or df_rb.empty:
                    continue
                p = output_dir_csv / f"rolling_factor_betas_{lbl}.csv"
                df_rb.round(4).to_csv(p, index=True)
                csv_paths[lbl] = p.name

        monthly_csv_paths: dict[str, str] = {}
        if output_policy.write_csv:
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
            if output_policy.write_csv:
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
            if output_policy.write_csv:
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
        if not stability_df.empty and output_policy.write_csv:
            stability_csv = output_dir_csv / "factor_beta_stability.csv"
            stability_df.round(4).to_csv(stability_csv, index=False)
            stability_csv_name = stability_csv.name

        plot_name = ""
        plot_png_by_window: dict[str, str] = {}
        if rb and output_policy.write_html:
            plot_path = output_dir_final / "rolling_factor_betas.html"
            write_rolling_betas_plot_html(rb, plot_path)
            plot_name = plot_path.name
        if rb and output_policy.write_png:
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
        if not lightweight or str(e) != "skip_rolling_betas_lightweight_profile":
            stress_report["factor_betas_rolling_error"] = str(e)
            logger.warning(f"Rolling factor betas diagnostics failed: {e}")

    # Kalman factor betas: diagnostic-only current regime estimate, does not replace raw 5Y/10Y OLS betas.
    # Candidate lightweight reports skip Kalman for runtime, but the product-facing
    # analysis_subject bundle keeps it because Block 2.3 is the canonical current-portfolio
    # factor-exposure surface.
    skip_kalman_for_lightweight = should_skip_kalman_for_lightweight_run(
        lightweight=lightweight,
        portfolio_role_override=portfolio_role_override,
        output_profile=output_policy.profile,
    )
    if skip_kalman_for_lightweight:
        stress_report["factor_betas_kalman_skip_reason"] = "lightweight_comparison_profile"
    try:
        if skip_kalman_for_lightweight:
            raise RuntimeError("skip_kalman_lightweight_profile")
        attach_kalman_factor_betas_to_stress_report(
            stress_report,
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            output_dir_csv=csv_export_dir,
            window_weeks=FACTOR_WEEKS_10Y,
        )
    except Exception as e:
        if not lightweight or str(e) != "skip_kalman_lightweight_profile":
            stress_report["factor_betas_kalman_error"] = str(e)
            logger.warning(f"Kalman factor betas diagnostics failed: {e}")

    # Factor covariance analytics: explicit base / stress_empirical / stress_overlay regimes.
    report_timing.start_block("factor_covariance")
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
            if output_policy.write_csv and not df.empty:
                df.round(6).to_csv(output_dir_csv / fname)

        for regime, fname in {
            "base": "factor_correlation_base_5y_weekly.csv",
            "stress_empirical": "factor_correlation_stress_empirical_weekly.csv",
            "stress_overlay": "factor_correlation_stress_overlay_weekly.csv",
        }.items():
            df = _matrix_df(regime, "correlations")
            if output_policy.write_csv and not df.empty:
                df.round(6).to_csv(output_dir_csv / fname)

        for regime, fname in {
            "base": "portfolio_factor_rc_base.csv",
            "stress_empirical": "portfolio_factor_rc_stress_empirical.csv",
            "stress_overlay": "portfolio_factor_rc_stress_overlay.csv",
        }.items():
            rows = ((factor_cov.get("portfolio_factor_rc") or {}).get(regime) or [])
            if output_policy.write_csv and rows:
                pd.DataFrame(rows).round(6).to_csv(output_dir_csv / fname, index=False)

        if output_policy.write_csv:
            overlay_deltas = ((factor_cov.get("stress_overlay") or {}).get("overlay_deltas") or [])
            if overlay_deltas:
                pd.DataFrame(overlay_deltas).round(6).to_csv(
                    output_dir_csv / "factor_covariance_overlay_deltas.csv", index=False
                )

            stability = factor_cov.get("covariance_stability_check") or {}
            stability_rows = []
            for row in stability.get("by_pair") or []:
                stability_rows.append({"type": "pair", **row})
            for row in stability.get("by_factor_variance") or []:
                stability_rows.append({"type": "factor_variance", **row})
            if stability_rows:
                pd.DataFrame(stability_rows).round(6).to_csv(
                    output_dir_csv / "factor_covariance_stability_check.csv", index=False
                )

            forecast_quality = factor_cov.get("forecast_quality") or {}
            forecast_rows = (
                forecast_quality.get("rows") if isinstance(forecast_quality, dict) else []
            )
            if forecast_rows:
                flat_rows = []
                for row in forecast_rows:
                    if not isinstance(row, dict):
                        continue
                    flat_rows.append(
                        {k: v for k, v in row.items() if k != "worst_corr_error_pair"}
                    )
                if flat_rows:
                    pd.DataFrame(flat_rows).round(6).to_csv(
                        output_dir_csv / "factor_covariance_forecast_quality.csv", index=False
                    )
    except Exception as e:
        stress_report["factor_covariance_error"] = str(e)
        stress_report["factor_covariance"] = {
            "status": "unavailable",
            "error": "factor_covariance_analytics_exception",
            "unavailable_reason": str(e),
        }
        logger.warning(f"Factor covariance analytics failed: {e}")
    report_timing.end_block("factor_covariance")

    report_timing.start_block("macro_regime")
    try:
        cached_macro_panel = (
            review_run_context.macro_panel
            if review_run_context is not None
            and review_run_context.macro_panel is not None
            and not review_run_context.macro_panel.empty
            else None
        )
        if cached_macro_panel is not None:
            macro_regimes = macro_regime_diagnostics_with_panel(
                weights=weights,
                tickers=tickers,
                analysis_end_str=analysis_end_str,
                indicator_panel=cached_macro_panel,
                indicator_meta=review_run_context.macro_panel_meta or {},
                factor_returns=recession_factor_returns if not recession_factor_returns.empty else None,
            )
        else:
            macro_regimes = macro_regime_diagnostics(
                weights=weights,
                tickers=tickers,
                analysis_end_str=analysis_end_str,
                factor_returns=recession_factor_returns if not recession_factor_returns.empty else None,
            )
        stress_report["macro_regime_diagnostics"] = macro_regimes
        if not lightweight:
            for fname, df in macro_regime_csv_frames(macro_regimes).items():
                if output_policy.write_csv and not df.empty:
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
    report_timing.end_block("macro_regime")

    regime_factor_analytics_full = None
    if lightweight:
        stress_report["regime_factor_analytics_skip_reason"] = "lightweight_comparison_profile"
    try:
        if lightweight:
            raise RuntimeError("skip_regime_factor_analytics_lightweight_profile")
        mr = stress_report.get("macro_regime_diagnostics") or {}
        lm = mr.get("labels_monthly") or []
        if not isinstance(mr, dict) or mr.get("error") or not lm:
            stress_report["regime_factor_analytics_skip_reason"] = (
                "macro_regime_diagnostics unavailable or empty labels_monthly"
            )
        else:
            idx = pd.to_datetime([row["date"] for row in lm])
            regime_ser = pd.Series([str(row.get("regime", "")) for row in lm], index=idx)
            trans_ser = pd.Series([bool(row.get("transition_flag", False)) for row in lm], index=idx)
            regime_label_history_span = {
                "start": idx.min().strftime("%Y-%m-%d"),
                "end": idx.max().strftime("%Y-%m-%d"),
                "n_months": int(len(idx)),
            }
            portfolio_regime_analytics_window = {
                "label": "10Y",
                "target_months": int(FACTOR_MONTHS_10Y),
                "target_weeks": int(FACTOR_WEEKS_10Y),
                "target_trading_days": int(FACTOR_TRADING_DAYS_10Y),
                "analysis_end": str(analysis_end_str),
                "disclaimer": (
                    "regime_label_history_span may be longer than the portfolio analytics slice; "
                    "portfolio_regime_analytics_window is fixed to 10Y (~2520 trading days for daily "
                    "regime_factor_analytics, or ~520 weeks / 120 months in legacy modes) ending at "
                    "analysis_end."
                ),
            }
            asset_cols = [t for t in tickers if t in monthly_returns.columns]
            monthly_asset = monthly_returns[asset_cols].copy()
            monthly_asset.index = (
                pd.to_datetime(monthly_asset.index).tz_localize(None).normalize()
            )
            start_m = monthly_asset.index.min().strftime("%Y-%m-%d")
            end_ts = pd.Timestamp(analysis_end_str).normalize()
            end_dl = (end_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

            extra_lb: list[str] = []
            for t in asset_cols:
                p = local_benchmark_map.get(t)
                if p and p not in asset_cols and p != benchmark_base_ticker:
                    extra_lb.append(p)
            dl_tickers = list(dict.fromkeys(list(asset_cols) + [benchmark_base_ticker] + extra_lb))
            daily = download_all(dl_tickers, start_m, end_dl)
            daily_prices: dict[str, pd.Series] = {}
            for ticker in asset_cols:
                df = daily.get(ticker)
                if df is None or df.empty or "Close" not in df.columns:
                    continue
                daily_prices[ticker] = df["Close"].copy()

            daily_asset = asset_daily_returns_from_daily(daily_prices, start_m, end_dl)
            daily_factors = build_factor_matrix_daily(start_m, analysis_end_str)
            use_daily = (
                daily_asset is not None
                and not daily_asset.empty
                and daily_factors is not None
                and not daily_factors.empty
            )
            if use_daily:
                daily_asset = daily_asset.copy()
                daily_asset.index = (
                    pd.to_datetime(daily_asset.index).tz_localize(None).normalize()
                )
                daily_factors = daily_factors.copy()
                daily_factors.index = (
                    pd.to_datetime(daily_factors.index).tz_localize(None).normalize()
                )
                common_d = daily_asset.index.intersection(daily_factors.index).sort_values()
                common_d = common_d[common_d <= end_ts]
                if len(common_d) > FACTOR_TRADING_DAYS_10Y:
                    common_d = common_d[-FACTOR_TRADING_DAYS_10Y:]
                daily_asset = daily_asset.loc[common_d]
                daily_factors = daily_factors.loc[common_d]
                rfa_payload = regime_factor_analytics(
                    monthly_returns=daily_asset,
                    monthly_factor_returns=daily_factors,
                    regime_labels=regime_ser,
                    transition_flag=trans_ser,
                    confidence_level=None,
                    weights=weights,
                    enable_transition_split=False,
                    enable_confidence_split=False,
                    frequency="daily",
                    daily_label_alignment="daily_returns_inherit_latest_monthly_regime",
                    regime_label_history_span=regime_label_history_span,
                    portfolio_regime_analytics_window=portfolio_regime_analytics_window,
                )
                regime_factor_analytics_full = rfa_payload
                stress_report["regime_factor_analytics"] = regime_factor_analytics_for_stress_report(
                    rfa_payload
                )
                rfa_summary = regime_factor_analytics_summary(rfa_payload)
                (output_dir_final / "regime_factor_analytics_summary.json").write_text(
                    json.dumps(rfa_summary, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                for fname, df in regime_factor_analytics_csv_frames(rfa_payload).items():
                    if output_policy.write_csv and df is not None and not df.empty:
                        num_cols = df.select_dtypes(include=[np.number]).columns
                        if len(num_cols):
                            df = df.copy()
                            df[num_cols] = df[num_cols].round(6)
                        df.to_csv(output_dir_csv / fname, index=False)
                try:
                    labels_ff = (
                        pd.Series(
                            regime_ser.values,
                            index=pd.to_datetime(regime_ser.index).tz_localize(None).normalize(),
                            name="regime",
                        )
                        .dropna()
                        .astype(str)
                        .sort_index()
                        .reindex(common_d, method="ffill")
                    )
                    rf_d = expand_rf_monthly_to_daily(rf_monthly, common_d)
                    bench_d = pd.Series(dtype=float, index=common_d)
                    bdf_b = daily.get(benchmark_base_ticker)
                    if bdf_b is not None and not bdf_b.empty and "Close" in bdf_b.columns:
                        br = bdf_b["Close"].pct_change()
                        br.index = pd.to_datetime(br.index).tz_localize(None).normalize()
                        bench_d = br.reindex(common_d)

                    local_bench_daily: dict[str, pd.Series] = {}
                    for tcol in asset_cols:
                        prox = local_benchmark_map.get(tcol)
                        if not prox:
                            continue
                        bdf_lb = daily.get(prox)
                        if bdf_lb is None or bdf_lb.empty or "Close" not in bdf_lb.columns:
                            continue
                        lr_lb = bdf_lb["Close"].pct_change()
                        lr_lb.index = pd.to_datetime(lr_lb.index).tz_localize(None).normalize()
                        local_bench_daily[str(tcol)] = lr_lb.reindex(common_d)

                    rpm_full = build_regime_portfolio_metrics(
                        daily_asset_returns=daily_asset,
                        daily_regime_labels_ffill=labels_ff,
                        weights=weights,
                        rf_daily=rf_d,
                        benchmark_daily_returns=bench_d,
                        mar_daily=regime_mar_daily,
                        local_benchmark_daily_by_ticker=local_bench_daily,
                        regime_factor_analytics_payload=rfa_payload,
                    )
                    stress_report["regime_portfolio_metrics"] = regime_portfolio_metrics_for_stress_report(
                        rpm_full
                    )
                    rpm_sum = regime_portfolio_metrics_summary(rpm_full)
                    (output_dir_final / "regime_portfolio_metrics_summary.json").write_text(
                        json.dumps(rpm_sum, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    for fname, df in regime_portfolio_metrics_csv_frames(rpm_full).items():
                        if output_policy.write_csv and df is not None and not df.empty:
                            num_cols = df.select_dtypes(include=[np.number]).columns
                            if len(num_cols):
                                df = df.copy()
                                df[num_cols] = df[num_cols].round(6)
                            df.to_csv(output_dir_csv / fname, index=False)
                except Exception as exc:
                    stress_report["regime_portfolio_metrics_error"] = str(exc)
                    logger.warning(f"Regime portfolio metrics failed: {exc}")
            else:
                logger.warning(
                    "Regime factor analytics: daily asset/factor history unavailable; skipping block."
                )
                stress_report["regime_factor_analytics_skip_reason"] = (
                    "regime_factor_analytics_daily_series_unavailable"
                )
    except Exception as e:
        if not lightweight or str(e) != "skip_regime_factor_analytics_lightweight_profile":
            stress_report["regime_factor_analytics_error"] = str(e)
            logger.warning(f"Regime factor analytics failed: {e}")

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
    report_timing.start_block("factor_decomposition")
    try:
        factor_decomp = factor_variance_decomposition_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_5Y,
            shared_frames=shared_weekly_frames,
        )
        stress_report["factor_variance_decomposition"] = factor_decomp
        for warning in factor_decomp.get("warnings") or []:
            logger.warning(f"Factor variance decomposition warning: {warning}")
        rows = factor_decomp.get("rows") or []
        if output_policy.write_csv and rows:
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
    report_timing.end_block("factor_decomposition")

    # Portfolio PCA diagnostics: hidden statistical risk concentration, diagnostic only.
    report_timing.start_block("portfolio_pca")
    try:
        pca_use_tickers = [
            str(t).strip()
            for t in tickers
            if str(t).strip() and float(weights.get(t, 0.0)) > 0.0
        ]
        if len(pca_use_tickers) < 2:
            pca_use_tickers = [str(t).strip() for t in tickers if str(t).strip()]
        if (
            shared_weekly_frames is not None
            and weekly_factor_frames_cover_tickers(shared_weekly_frames, pca_use_tickers)
        ):
            pca = portfolio_pca_diagnostics_with_weekly_frames(
                weights=weights,
                tickers=tickers,
                shared_frames=shared_weekly_frames,
                window_weeks=FACTOR_WEEKS_5Y,
                factor_returns=recession_factor_returns if not recession_factor_returns.empty else None,
            )
        else:
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

        if output_policy.write_csv and summary_rows:
            pd.DataFrame(summary_rows).round(8).to_csv(output_dir_csv / "portfolio_pca_summary_5y.csv", index=False)
        if output_policy.write_csv and component_rows:
            pd.DataFrame(component_rows).round(8).to_csv(output_dir_csv / "portfolio_pca_components_5y.csv", index=False)
        if output_policy.write_csv and rolling_rows:
            pd.DataFrame(rolling_rows).round(8).to_csv(output_dir_csv / "portfolio_pca_rolling_pc1.csv", index=False)
        if output_policy.write_csv and corr_rows:
            pd.DataFrame(corr_rows).round(8).to_csv(output_dir_csv / "portfolio_pca_pc1_factor_correlations.csv", index=False)
    except Exception as e:
        stress_report["portfolio_pca_error"] = str(e)
        logger.warning(f"Portfolio PCA diagnostics failed: {e}")
    report_timing.end_block("portfolio_pca")

    # Out-of-sample explainability in historical episodes: beta * realized factor shocks.
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
        logger.warning(f"Factor beta*shock OOS diagnostics failed: {e}")
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

    if loss_gate_mode == LOSS_GATE_MODE_DIAGNOSTIC:
        try:
            attach_core_mvp_historical_stress_replay_v1(
                stress_report,
                weights=weights,
                monthly_returns=monthly_returns,
                cash_proxy_ticker=cash_proxy_ticker,
            )
            trust = stress_report.setdefault("data_trust_summary", {})
            trust_lines = list(trust.get("user_summary_lines") or [])
            replay_block = stress_report.get("historical_stress_replay_v1") or {}
            for ep in replay_block.get("episodes") or []:
                if not isinstance(ep, dict):
                    continue
                if ep.get("replay_status") in {"partial_unavailable", "unavailable"}:
                    sid = ep.get("scenario_id") or ep.get("scenario_name") or "historical"
                    summary = (
                        ep.get("diagnosis_summary_en")
                        or ep.get("limitation_summary")
                        or ep.get("user_note")
                    )
                    if summary:
                        trust_lines.append(f"Historical replay ({sid}): {summary}")
            trust["user_summary_lines"] = trust_lines
        except Exception as e:
            stress_report["historical_stress_replay_v1_error"] = str(e)
            logger.warning("Core MVP historical stress replay failed: %s", e)

    attach_stress_results_v1(stress_report)
    attach_hedge_gap_analysis_v1(stress_report)
    attach_current_portfolio_stress_scorecard_v1(stress_report)

    try:
        historical_paths = stress_report.get("historical_episode_paths") or []
        for item in (historical_paths if output_policy.write_csv else []):
            if not isinstance(item, dict):
                continue
            episode = str(item.get("episode") or "").strip()
            rows = item.get("rows")
            if not episode or not isinstance(rows, list) or not rows:
                continue
            df_path = pd.DataFrame(rows)
            if df_path.empty:
                continue
            df_path.to_csv(output_dir_csv / f"crisis_replay_{episode}.csv", index=False)
            asset_contrib = item.get("asset_pnl_contrib_episode")
            if isinstance(asset_contrib, dict) and asset_contrib:
                contrib_rows = [
                    {
                        "ticker": ticker,
                        "episode_pnl_contrib": value,
                    }
                    for ticker, value in sorted(asset_contrib.items())
                ]
                pd.DataFrame(contrib_rows).to_csv(
                    output_dir_csv / f"crisis_replay_{episode}_asset_contrib.csv",
                    index=False,
                )
    except Exception as e:
        logger.warning(f"Historical episode path export failed: {e}")
    try:
        ssa = build_stress_scenario_analytics(
            stress_report=stress_report,
            weights=weights,
            tickers=tickers,
            monthly_returns=monthly_returns,
            factor_returns_weekly=recession_factor_returns
            if recession_factor_returns is not None and not recession_factor_returns.empty
            else None,
            cash_proxy_ticker=cash_proxy_ticker,
            analysis_end_str=analysis_end_str,
            output_dir_csv=csv_export_dir,
        )
        stress_report["stress_scenario_analytics"] = {k: v for k, v in ssa.items() if k != "csv_export"}
    except Exception as e:
        stress_report["stress_scenario_analytics_error"] = str(e)
        logger.warning(f"Stress scenario analytics failed: {e}")

    _scenario_lib_factor_weekly = (
        recession_factor_returns
        if recession_factor_returns is not None and not recession_factor_returns.empty
        else None
    )
    report_timing.start_block("scenario_library")
    try:
        sl = build_scenario_library(
            stress_report,
            weights=weights,
            tickers=tickers,
            monthly_returns=monthly_returns,
            returns_frequency=str(returns_frequency),
            analysis_end_str=analysis_end_str,
            regime_factor_analytics_full=regime_factor_analytics_full,
            factor_returns_weekly=_scenario_lib_factor_weekly,
            cash_proxy_ticker=cash_proxy_ticker,
            output_dir_final=output_dir_final,
            output_dir_csv=csv_export_dir,
        )
        stress_report["scenario_library_meta"] = {
            "version": sl.get("version"),
            "n_scenarios": sl.get("n_scenarios"),
            "output_paths": sl.get("output_paths"),
            "warnings_global": sl.get("warnings_global"),
            "classifications": summarize_scenario_classifications(sl.get("scenarios") or []),
        }
        try:
            sln = build_scenario_library_normalized(
                sl,
                output_dir_final=output_dir_final,
                output_dir_csv=csv_export_dir,
                monthly_returns=monthly_returns,
                weights=weights,
                tickers=tickers,
                returns_frequency_pipeline=str(returns_frequency),
                optimizer_mu_by_ticker=None,
                stress_report=stress_report,
                factor_returns_weekly=_scenario_lib_factor_weekly
                if _scenario_lib_factor_weekly is not None and not _scenario_lib_factor_weekly.empty
                else None,
                factor_returns_weekly_episode_loose=scenario_episode_factor_returns
                if scenario_episode_factor_returns is not None and not scenario_episode_factor_returns.empty
                else None,
                cash_proxy_ticker=cash_proxy_ticker,
                historical_stress_proxy_config=None,
                enable_historical_stress_fallback=True,
            )
            stress_report["scenario_library_normalized_meta"] = {
                "version": sln.get("version"),
                "n_scenarios": sln.get("n_scenarios"),
                **summarize_normalized_classifications(sln.get("scenarios") or []),
                "readiness_roles": sln.get("readiness_roles"),
                "monte_carlo_feasibility_note": sln.get("monte_carlo_feasibility_note"),
                "robust_optimization_note": sln.get("robust_optimization_note"),
                "output_paths": sln.get("output_paths"),
                "global_warnings": sln.get("global_warnings"),
            }
        except Exception as e:
            stress_report["scenario_library_normalized_error"] = str(e)
            logger.warning(f"Scenario library normalized v1 failed: {e}")
    except Exception as e:
        stress_report["scenario_library_error"] = str(e)
        logger.warning(f"Scenario library v1 failed: {e}")
    report_timing.end_block("scenario_library")
    stress_report["frequency_disclosure"] = frequency_disclosure_from_resolution(
        freq_res,
        factor_stress_frequency=FACTOR_STRESS_FREQUENCY_DEFAULT,
        macro_regime_frequency=MACRO_REGIME_FREQUENCY_DEFAULT,
    )
    stress_report["periods_per_year"] = ppy

    with report_timing.block("export_stress"):
        export_stress_report(stress_report, output_dir_final)
    logger.info(f"Stress status: {stress_report.get('status', 'N/A')}")

    # =========================================================================
    # STEP 9b: Portfolio analytics per window (rolling Sharpe/Sortino, drawdown, VaR/ES, EEE)
    # =========================================================================
    report_timing.start_block("daily_tail_risk")
    portfolio_returns_daily: pd.Series | None = None
    try:
        daily_asset_returns: pd.DataFrame | None = None
        cash_returns_daily: pd.Series | None = None
        if factory_factor is not None:
            shared_daily = daily_panel_for_candidate_report(
                factory_factor,
                tickers=tickers,
                cash_proxy_ticker=cash_proxy_ticker,
            )
            if shared_daily is not None:
                daily_asset_returns, cash_returns_daily = shared_daily
        if daily_asset_returns is None:
            daily_asset_returns, cash_returns_daily = load_daily_asset_returns_shared(
                tickers=tickers,
                benchmark_base_ticker=benchmark_base_ticker,
                cash_proxy_ticker=cash_proxy_ticker,
                investor_currency=investor_currency,
                windows_months=windows_months,
                assets_meta=assets_meta,
                daily_cache_key=daily_cache_key,
                analysis_end=analysis_end,
                no_cache=no_cache,
                local_benchmark_map=local_benchmark_map,
                data_provider=getattr(cfg, "market_data_provider", None),
            )
        if cash_returns_daily.empty or len(cash_returns_daily.index) == 0:
            cash_returns_daily = pd.Series(0.0, index=daily_asset_returns.index)
        else:
            cash_returns_daily = cash_returns_daily.reindex(daily_asset_returns.index).fillna(0.0)
        target_weights_daily = {t: weights.get(t, 0.0) for t in tickers}
        if backtest_mode == "dynamic_nan_safe":
            risk_rt_daily = get_risk_portfolio_tickers(cfg.tickers, cfg.cash_proxy_ticker)
            portfolio_returns_daily, _ = portfolio_returns_nan_safe(
                daily_asset_returns,
                target_weights_daily,
                cash_returns_daily,
                risk_tickers=risk_rt_daily,
            )
        else:
            portfolio_returns_daily, _ = portfolio_returns_nan_safe(
                daily_asset_returns,
                target_weights_daily,
                cash_returns_daily,
            )
        portfolio_returns_daily = truncate_to_analysis_end(portfolio_returns_daily, analysis_end)
    except Exception as e:
        logger.warning("Daily portfolio returns for tail risk unavailable: %s", e)
        portfolio_returns_daily = None

    analytics_by_window: dict[str, dict] = {}
    for wm in windows_months:
        suffix = "3y" if wm == 36 else "5y" if wm == 60 else "10y"
        if lightweight and suffix != "10y":
            continue
        ret_slice = slice_window(portfolio_returns, analysis_end, wm).dropna()
        rf_slice = slice_window(rf_monthly, analysis_end, wm).reindex(ret_slice.index).fillna(0)
        bench_slice = slice_window(benchmark_returns, analysis_end, wm).reindex(ret_slice.index).dropna()
        min_obs_analytics = calendar_window_to_n_periods(24, returns_frequency)
        if len(ret_slice) < min_obs_analytics:
            continue
        # Rolling 36m and 12m (calendar mapping)
        rs36 = rolling_sharpe(ret_slice, rf_slice, 36, returns_frequency=returns_frequency)
        rs12 = rolling_sharpe(ret_slice, rf_slice, 12, returns_frequency=returns_frequency)
        rsort36 = rolling_sortino(
            ret_slice, rf_slice, 36, mar=mar_period, returns_frequency=returns_frequency
        )
        rsort12 = rolling_sortino(
            ret_slice, rf_slice, 12, mar=mar_period, returns_frequency=returns_frequency
        )
        rvol = rolling_vol_annual(ret_slice, 12, returns_frequency=returns_frequency)
        if output_policy.write_csv:
            rs36.round(3).to_csv(output_dir_csv / f"rolling_sharpe_36m_{suffix}.csv", header=True)
            rs12.round(3).to_csv(output_dir_csv / f"rolling_sharpe_12m_{suffix}.csv", header=True)
            rsort36.round(3).to_csv(output_dir_csv / f"rolling_sortino_36m_{suffix}.csv", header=True)
            rsort12.round(3).to_csv(output_dir_csv / f"rolling_sortino_12m_{suffix}.csv", header=True)
            rvol.round(3).to_csv(output_dir_csv / f"rolling_vol_12m_{suffix}.csv", header=True)
        beta_corr_block: dict[str, dict] = {}
        if len(bench_slice.dropna()) >= 12:
            rb36 = rolling_beta(
                ret_slice, bench_slice, 36, returns_frequency=returns_frequency
            )
            rb12 = rolling_beta(
                ret_slice, bench_slice, 12, returns_frequency=returns_frequency
            )
            rc36 = rolling_correlation(
                ret_slice, bench_slice, 36, returns_frequency=returns_frequency
            )
            rc12 = rolling_correlation(
                ret_slice, bench_slice, 12, returns_frequency=returns_frequency
            )
            if output_policy.write_csv:
                rb36.round(3).to_csv(output_dir_csv / f"rolling_beta_36m_{suffix}.csv", header=True)
                rb12.round(3).to_csv(output_dir_csv / f"rolling_beta_12m_{suffix}.csv", header=True)
                rc36.round(3).to_csv(output_dir_csv / f"rolling_correlation_36m_{suffix}.csv", header=True)
                rc12.round(3).to_csv(output_dir_csv / f"rolling_correlation_12m_{suffix}.csv", header=True)
            beta_corr_block = rolling_beta_correlation_block(
                ret_slice, bench_slice, returns_frequency=returns_frequency
            )
        dd_struct = drawdown_structure(ret_slice)
        if not lightweight:
            import json as _json
            with open(output_dir_final / f"drawdown_structure_{suffix}.json", "w", encoding="utf-8") as _f:
                _json.dump(dd_struct, _f, indent=2, default=str)
        # VaR / ES 95% and 99% on daily simple returns (metrics_spec historical tail risk)
        tail_risk = {"metric_available": False, "unavailable_reason": "daily_portfolio_returns_unavailable"}
        if portfolio_returns_daily is not None and len(portfolio_returns_daily.dropna()) >= 2:
            tail_risk = compute_tail_risk_historical(
                portfolio_returns_daily,
                window_months=wm,
                window_label=suffix,
                analysis_end=analysis_end,
            )
        flat_tail = tail_risk_flat_fields(tail_risk)
        var_95 = flat_tail.get("var_95")
        var_99 = flat_tail.get("var_99")
        es_95 = flat_tail.get("es_95")
        es_99 = flat_tail.get("es_99")
        if output_policy.write_csv:
            pd.DataFrame(
                [
                    {
                        "method": tail_risk.get("method"),
                        "frequency": tail_risk.get("frequency"),
                        "window_months": tail_risk.get("window_months", wm),
                        "window_label": suffix,
                        "n_obs": tail_risk.get("n_obs"),
                        "var_95": var_95,
                        "var_99": var_99,
                        "es_95": es_95,
                        "es_99": es_99,
                        "metric_available": tail_risk.get("metric_available"),
                    }
                ]
            ).round(3).to_csv(output_dir_csv / f"var_es_{suffix}.csv", index=False)
        eee = effective_equity_exposure(ret_slice, bench_slice, 0.10) if len(bench_slice.dropna()) >= 12 else None
        if output_policy.write_csv:
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
            **beta_corr_block,
            "vol_of_vol": round(vol_of_vol, 3) if vol_of_vol is not None else None,
            "rel_vol_of_vol": round(rel_vol_of_vol, 3) if rel_vol_of_vol is not None else None,
            "drawdown_structure": dd_struct,
            "tail_risk": tail_risk,
            "var_95": var_95,
            "var_99": var_99,
            "es_95": es_95,
            "es_99": es_99,
            "eee_10pct": eee,
        }
    report_timing.end_block("daily_tail_risk")

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
        returns_frequency=returns_frequency,
        periods_per_year=ppy,
    )
    resolved_weights_source = weights_source or getattr(cfg, "weights_source", None)
    analysis_setup = build_analysis_setup(
        cfg,
        portfolio_weights=weights,
        weights_source=resolved_weights_source,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        local_benchmark_map=local_benchmark_map,
        analysis_end=analysis_end_str,
        windows_months=windows_months,
        returns_frequency=returns_frequency,
        periods_per_year=ppy,
        run_context="report",
        portfolio_role_override=portfolio_role_override,
    )

    # Gatekeepers: portfolio_valid = False only when MaxDD on the full overlapping history breaches the mandate.
    # Scenario stress (DIAG_*) does not make the portfolio invalid.
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
        portfolio_weights=weights,
        weights_source=resolved_weights_source,
        analysis_setup=analysis_setup,
    )

    # Snapshots: one for assets, three by window (3y / 5y / 10y)
    report_timing.start_block("snapshots")
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
    if not lightweight:
        snapshot_assets = build_snapshot_assets(asset_metrics_by_window, run_timestamp)
        save_snapshot(snapshot_assets, output_dir_final / "snapshot_assets.json")
        logger.info("Asset snapshot: %s", output_dir_final / "snapshot_assets.json")

    config_fingerprint = compute_candidate_config_fingerprint(cfg)

    snapshots_by_window: dict[str, dict[str, Any]] = {}

    # 2) Snapshots by window (3y, 5y, 10y); lightweight_comparison writes 10y only
    for label in ("3y", "5y", "10y"):
        if lightweight and label != "10y":
            continue
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
            candidate_config_fingerprint=config_fingerprint,
        )
        save_snapshot(snap_w, output_dir_final / f"snapshot_{label}.json")
        snapshots_by_window[label] = snap_w
        logger.info("Snapshot %s: %s", label, output_dir_final / f"snapshot_{label}.json")

    if lightweight:
        snapshot_index_entries: dict[str, str] = {"10y": "snapshot_10y.json"}
    else:
        snapshot_index_entries = {
            "assets": "snapshot_assets.json",
            "3y": "snapshot_3y.json",
            "5y": "snapshot_5y.json",
            "10y": "snapshot_10y.json",
        }
    save_snapshot(
        {"timestamp": run_timestamp, "snapshots": snapshot_index_entries},
        output_dir_final / "snapshot_index.json",
    )
    primary_corr_matrix = None
    primary_corr_ref = None
    for _corr_window in ("10y", "5y", "3y"):
        _corr_frame = corr_by_window.get(_corr_window)
        if _corr_frame is not None and not _corr_frame.empty:
            primary_corr_matrix = _corr_frame
            primary_corr_ref = corr_csv_by_window.get(_corr_window) or f"runtime:correlation_matrix_{_corr_window}"
            break
    xray_inputs = resolve_xray_snapshot_inputs(
        snapshots_by_window,
        fallback_snapshot=snapshot if isinstance(snapshot, dict) else None,
    )
    xray_summary = build_portfolio_xray_v2(
        analysis_setup=analysis_setup,
        weights=weights,
        rc_asset=xray_inputs.get("rc_asset"),
        stress_report=stress_report,
        portfolio_valid=portfolio_valid,
        portfolio_metrics=xray_inputs.get("portfolio_metrics"),
        portfolio_windows=portfolio_windows or None,
        portfolio_analytics=xray_inputs.get("portfolio_analytics"),
        drawdown_structure=xray_inputs.get("drawdown_structure"),
        correlation_matrix=primary_corr_matrix,
        correlation_matrix_ref=primary_corr_ref,
        output_dir_final=output_dir_final,
        output_dir_csv=csv_export_dir,
    )
    with report_timing.block("export_stress_hedge_gap_bridge"):
        attach_current_portfolio_stress_scorecard_v1(
            stress_report,
            portfolio_xray=xray_summary,
        )
        export_stress_report(stress_report, output_dir_final)
    try:
        with open(output_dir_final / "portfolio_xray.json", "w", encoding="utf-8") as f:
            json.dump(xray_summary, f, indent=2, ensure_ascii=False, default=str)
    except Exception:
        xray_summary = _xray_summary_from_output_dir(output_dir_final)
    problem_classification_doc = None
    candidate_launchpad_doc = None
    if not core_blocks_only:
        try:
            problem_classification_path = write_problem_classification_outputs(
                output_dir=output_dir_final,
                portfolio_xray=xray_summary,
                stress_report=stress_report,
                analysis_end=analysis_end_str,
            )
            try:
                with open(problem_classification_path, encoding="utf-8") as f:
                    problem_classification_doc = json.load(f)
            except Exception:
                problem_classification_doc = None
        except Exception as e:
            logger.warning("problem_classification.json generation failed: %s", e)
        try:
            launchpad_path = write_candidate_launchpad_outputs(
                output_dir=output_dir_final,
                problem_classification=problem_classification_doc,
                analysis_end=analysis_end_str,
            )
            try:
                with open(launchpad_path, encoding="utf-8") as f:
                    candidate_launchpad_doc = json.load(f)
            except Exception:
                candidate_launchpad_doc = None
        except Exception as e:
            logger.warning("candidate_launchpad.json generation failed: %s", e)
        try:
            from src.ai_commentary_context import write_ai_commentary_context_outputs

            ai_paths = write_ai_commentary_context_outputs(
                output_dir=output_dir_final,
                comparison=None,
                current_vs_candidate=None,
                selection=None,
                decision_verdict=None,
                problem_classification=problem_classification_doc,
                candidate_launchpad=candidate_launchpad_doc,
                portfolio_xray=xray_summary,
                stress_report=stress_report,
            )
            logger.info(
                "ai_commentary_context.json (diagnosis grounding): %s",
                ai_paths.get("ai_commentary_context_json"),
            )
        except Exception as e:
            logger.warning("ai_commentary_context.json generation failed: %s", e)
    else:
        logger.info(
            "Skipping product adapters (problem_classification, candidate_launchpad, "
            "ai_commentary_context); product_bundle_scope=%s",
            bundle_scope,
        )
    report_timing.end_block("snapshots")

    if output_policy.write_txt or output_policy.write_html:
        if output_policy.write_txt:
            write_report_txt(str(output_dir_final))
        if output_policy.write_html:
            html_path = write_report_html(str(output_dir_final))
            logger.info("HTML report: %s", html_path)

    if output_policy.write_txt:
        try:
            cpath = write_portfolio_commentary(
                output_dir_final,
                output_dir_csv=output_dir_csv,
                portfolio_metrics_10y=portfolio_metrics_summary,
                stress_report=stress_report,
                portfolio_valid=portfolio_valid,
                analysis_end=analysis_end_str,
                frequency_disclosure=stress_report.get("frequency_disclosure"),
                analysis_setup=analysis_setup,
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
        "report_profile": profile,
        "output_profile": output_policy.profile,
        "product_bundle_scope": bundle_scope,
        "output_policy_disabled_artifact_classes": output_policy.disabled_artifact_classes,
    }
    from src.product_bundle_paths import (
        build_output_manifest_discovery_extra,
        build_product_first_generated_paths,
    )

    report_manifest_paths = build_product_first_generated_paths(
        output_dir_final,
        {
            "run_metadata": output_dir_final / "run_metadata.json",
            "data_policy": output_dir_final / "data_policy.json",
            "portfolio_xray": output_dir_final / "portfolio_xray.json",
            "stress_report": output_dir_final / "stress_report.json",
            "snapshot_10y": output_dir_final / "snapshot_10y.json",
            "snapshot_index": output_dir_final / "snapshot_index.json",
        },
    )
    # Core MVP Blocks 1-3 diagnosis-only manifest surface:
    # keep subject diagnostics only; do not publish candidate/comparison/decision keys
    # as active product-facing paths in analysis_subject site_api/core_json outputs.
    if str(portfolio_role_override or "") == "analysis_subject" and output_policy.profile in {
        "site_api",
        "core_json",
        "lightweight_comparison",
    }:
        blocked_manifest_keys = (
            "candidate_launchpad_json",
            "candidate_comparison_json",
            "current_vs_candidate_json",
            "decision_verdict_json",
            "selection_decision_json",
            "what_changed_summary_json",
            "candidate_factory_run_json",
            "candidate_factory_manifest_json",
        )
        if core_blocks_only:
            blocked_manifest_keys = (
                *blocked_manifest_keys,
                "problem_classification_json",
                "ai_commentary_context_json",
            )
        for blocked_key in blocked_manifest_keys:
            report_manifest_paths.pop(blocked_key, None)

    manifest_path = write_output_manifest(
        output_dir_final,
        policy=output_policy,
        run_kind=str(portfolio_role_override or "portfolio_report"),
        generated_paths=report_manifest_paths,
        cache_keys={"daily": daily_cache_key, "monthly": monthly_cache_key},
        extra=build_output_manifest_discovery_extra(report_manifest_paths),
    )
    meta["output_manifest"] = manifest_path
    timing_payload = report_timing.to_dict()
    if timing_payload:
        meta["report_timing"] = timing_payload
    return portfolio_metrics_summary, meta


def run_materialize_current_report(
    cfg: PortfolioConfig,
    *,
    run_timestamp: str,
    backtest_mode: str,
    no_cache: bool,
    output_profile: str | None = None,
) -> None:
    """Write current portfolio diagnostics to output_dir_final/current_portfolio/ sidecar."""
    from src.candidate_comparison import CURRENT_SIDECAR_SUBDIR, positive_current_weights

    if getattr(cfg, "analysis_mode", "optimize_from_universe") != "optimize_from_universe":
        logger.error(
            "materialize-current requires analysis_mode=optimize_from_universe "
            "(use a combined workflow; see docs/specs/current_vs_policy_workflow_spec.md)."
        )
        raise SystemExit(1)

    current_weights = dict(getattr(cfg, "current_weights", {}) or {})
    if not positive_current_weights(cfg):
        logger.error(
            "materialize-current requires non-empty current_weights in config.yml."
        )
        raise SystemExit(1)

    output_dir_final = ensure_output_dir(Path(getattr(cfg, "output_dir_final", "Main portfolio")))
    sidecar_final = ensure_output_dir(output_dir_final / CURRENT_SIDECAR_SUBDIR)
    sidecar_csv = sidecar_final / "results_csv"

    logger.info(
        "Materializing current portfolio to %s (policy artifacts on Main root are not modified).",
        sidecar_final,
    )

    run_portfolio_report_for_weights(
        cfg,
        current_weights,
        run_timestamp=run_timestamp,
        output_dir_csv=sidecar_csv,
        output_dir_final=sidecar_final,
        backtest_mode_override=backtest_mode,
        no_cache=no_cache,
        weights_source="config.current_weights",
        portfolio_role_override="user_current_portfolio",
        output_profile=output_profile,
    )


def resolve_analysis_subject_materialization(cfg: PortfolioConfig) -> dict[str, Any]:
    """Return the resolved analysis_subject weights and metadata for sidecar materialization."""
    subject = resolve_analysis_subject(
        cfg,
        portfolio_weights=dict(getattr(cfg, "weights", {}) or {}),
        weights_source=getattr(cfg, "weights_source", None),
    )
    if subject.get("resolution_status") != "resolved":
        return {
            "status": "blocked",
            "subject": subject,
            "weights": {},
            "weights_source": subject.get("weight_source"),
            "blocking_errors": list(subject.get("blocking_errors") or []),
        }

    weights = {
        str(ticker): float(weight)
        for ticker, weight in (subject.get("weights") or {}).items()
        if float(weight) > 0
    }
    if not weights:
        return {
            "status": "blocked",
            "subject": subject,
            "weights": {},
            "weights_source": subject.get("weight_source"),
            "blocking_errors": [
                {
                    "code": "ANALYSIS_SUBJECT_WEIGHTS_EMPTY",
                    "message": "Resolved analysis_subject has no positive diagnostic weights.",
                }
            ],
        }

    return {
        "status": "resolved",
        "subject": subject,
        "weights": weights,
        "weights_source": subject.get("weight_source"),
        "blocking_errors": [],
    }


def resolve_analysis_subject_report_profile(
    *,
    review_mode: str | None = None,
    report_profile: str | None = None,
) -> str:
    """Map portfolio review mode to analysis_subject report_profile (orchestration only)."""
    if report_profile is not None:
        return normalize_report_profile(report_profile)
    mode = (review_mode or "core").strip().lower()
    if mode == "full":
        return REPORT_PROFILE_FULL
    return REPORT_PROFILE_LIGHTWEIGHT


def should_use_review_run_context_for_subject(
    *,
    review_mode: str | None = None,
    use_review_run_context: bool | None = None,
) -> bool:
    if use_review_run_context is not None:
        return use_review_run_context
    mode = (review_mode or "core").strip().lower()
    return mode == "core"


def should_skip_kalman_for_lightweight_run(
    *,
    lightweight: bool,
    portfolio_role_override: str | None = None,
    output_profile: str | None = None,
) -> bool:
    """Skip Kalman for candidate lightweight reports, but keep it for analysis_subject JSON bundles."""
    analysis_subject_json_bundle = (
        str(portfolio_role_override or "") == "analysis_subject"
        and str(output_profile or "") in {"site_api", "core_json", "lightweight_comparison"}
    )
    return bool(lightweight and not analysis_subject_json_bundle)


def run_materialize_analysis_subject_report(
    cfg: PortfolioConfig,
    *,
    run_timestamp: str,
    backtest_mode: str,
    no_cache: bool,
    output_profile: str | None = None,
    review_run_context: ReviewRunContext | None = None,
    report_profile: str | None = None,
    review_mode: str | None = None,
    project_root: Path | None = None,
    use_review_run_context: bool | None = None,
    core_diagnostics_only: bool = False,
) -> ReviewRunContext | None:
    """Write resolved analysis_subject diagnostics to output_dir_final/analysis_subject/."""
    materialization = resolve_analysis_subject_materialization(cfg)
    if materialization["status"] != "resolved":
        errors = materialization.get("blocking_errors") or []
        msg = "; ".join(str(err.get("message") or err) for err in errors) or "unknown blocker"
        logger.error("materialize-analysis-subject failed: %s", msg)
        raise SystemExit(1)

    output_dir_final = ensure_output_dir(Path(getattr(cfg, "output_dir_final", "Main portfolio")))
    subject_final = ensure_output_dir(output_dir_final / "analysis_subject")
    subject_csv = subject_final / "results_csv"
    subject = materialization["subject"]

    resolved_profile = resolve_analysis_subject_report_profile(
        review_mode=review_mode,
        report_profile=report_profile,
    )
    want_shared_context = should_use_review_run_context_for_subject(
        review_mode=review_mode,
        use_review_run_context=use_review_run_context,
    )
    shared_context = review_run_context
    if want_shared_context and shared_context is None:
        root = project_root or Path(__file__).resolve().parent
        logger.info("Preparing ReviewRunContext for analysis_subject materialization.")
        shared_context = prepare_review_run_context(
            cfg,
            project_root=root,
            no_cache=no_cache,
        )

    logger.info(
        "Materializing analysis_subject (%s, role=%s) to %s (report_profile=%s, shared_context=%s).",
        subject.get("type"),
        subject.get("portfolio_role"),
        subject_final,
        resolved_profile,
        want_shared_context,
    )

    from src.product_bundle_scope import PRODUCT_BUNDLE_SCOPE_CORE_BLOCKS_1_3

    bundle_scope = (
        PRODUCT_BUNDLE_SCOPE_CORE_BLOCKS_1_3
        if core_diagnostics_only
        else DEFAULT_PRODUCT_BUNDLE_SCOPE
    )
    run_portfolio_report_for_weights(
        cfg,
        materialization["weights"],
        run_timestamp=run_timestamp,
        output_dir_csv=subject_csv,
        output_dir_final=subject_final,
        backtest_mode_override=backtest_mode,
        no_cache=no_cache,
        weights_source=str(materialization["weights_source"] or "analysis_subject"),
        portfolio_role_override="analysis_subject",
        output_profile=output_profile,
        report_profile=resolved_profile,
        product_bundle_scope=bundle_scope,
        run_context=shared_context if want_shared_context else None,
        enable_report_timing=want_shared_context,
    )
    if core_diagnostics_only:
        from src.product_bundle_hygiene import apply_core_blocks_product_bundle_hygiene

        prune = apply_core_blocks_product_bundle_hygiene(
            output_dir_final,
            subject_dir=subject_final,
        )
        logger.info(
            "Core Blocks 1–3 product bundle hygiene (removed subject=%d, root=%d stale files).",
            len(prune.get("removed_subject_block4") or []),
            len(prune.get("removed_root_post_compare") or []),
        )
    else:
        analysis_end_str: str | None = None
        try:
            with open(subject_final / "run_metadata.json", encoding="utf-8") as f:
                run_meta = json.load(f)
            if isinstance(run_meta, dict):
                analysis_end_str = run_meta.get("analysis_end") or (
                    (run_meta.get("analysis_setup") or {}).get("analysis_end")
                    if isinstance(run_meta.get("analysis_setup"), dict)
                    else None
                )
        except Exception:
            analysis_end_str = None
        from src.product_bundle_hygiene import apply_diagnosis_only_product_bundle_hygiene

        hygiene = apply_diagnosis_only_product_bundle_hygiene(
            output_dir_final,
            analysis_end=analysis_end_str,
            investor_currency=str(getattr(cfg, "investor_currency", "USD")),
        )
        logger.info(
            "Diagnosis-only product bundle hygiene (tombstone=%s, removed=%d stale files).",
            hygiene.get("tombstone"),
            len(hygiene.get("removed_stale") or []),
        )
    return shared_context if want_shared_context else None


def main() -> None:
    args = parse_args()
    setup_logging()
    run_timestamp = datetime.now().isoformat()

    if args.clear_cache:
        clear_all_cache()

    try:
        cfg = load_validated_config()
    except ConfigValidationError as e:
        logger.error(f"Configuration validation error: {e}")
        raise SystemExit(1)

    if cfg.pending_fields:
        logger.info(f"Configuration fields awaiting user input: {cfg.pending_fields}")

    if args.materialize_current and args.materialize_analysis_subject:
        logger.error("Use only one materialization mode at a time.")
        raise SystemExit(1)

    if args.materialize_analysis_subject:
        if args.use_review_run_context and args.no_review_run_context:
            logger.error("Use only one of --use-review-run-context / --no-review-run-context.")
            raise SystemExit(1)
        subject_use_context: bool | None = None
        if args.no_review_run_context:
            subject_use_context = False
        elif args.use_review_run_context:
            subject_use_context = True
        run_materialize_analysis_subject_report(
            cfg,
            run_timestamp=run_timestamp,
            backtest_mode=args.backtest_mode,
            no_cache=args.no_cache,
            output_profile=args.output_profile,
            review_mode=args.review_mode,
            project_root=Path(__file__).resolve().parent,
            use_review_run_context=subject_use_context,
            core_diagnostics_only=args.core_diagnostics_only,
        )
        cleanup_old_cache(keep_versions=3)
        sidecar = Path(getattr(cfg, "output_dir_final", "Main portfolio")) / "analysis_subject"
        if args.core_diagnostics_only:
            print("\nDone (core diagnostics Blocks 1-3).")
            print(f"  Core diagnostic artifacts: {sidecar}")
            print("  Next: python run_portfolio_review.py for full product workflow.")
        else:
            print("\nDone (analysis_subject materialization).")
            print(f"  Analysis subject artifacts: {sidecar}")
            print("  Next: generate or compare candidate portfolios after subject diagnostics exist.")
        return

    if args.materialize_current:
        run_materialize_current_report(
            cfg,
            run_timestamp=run_timestamp,
            backtest_mode=args.backtest_mode,
            no_cache=args.no_cache,
            output_profile=args.output_profile,
        )
        cleanup_old_cache(keep_versions=3)
        sidecar = Path(getattr(cfg, "output_dir_final", "Main portfolio")) / "current_portfolio"
        print("\nDone (current materialization).")
        print(f"  Current portfolio artifacts: {sidecar}")
        print("  Next: python run_compare_variants.py")
        return

    if not cfg.weights:
        logger.error(
            "Portfolio weights are not set. Use analysis_mode=analyze_current_weights with current_weights "
            "for an existing portfolio, run `python run_report.py --materialize-analysis-subject` "
            "for the portfolio-first subject sidecar, or run legacy policy optimization with "
            "`python run_optimization.py` to write portfolio_weights.yml."
        )
        raise SystemExit(1)

    output_policy = output_policy_for_profile(args.output_profile)
    output_dir_csv = Path(cfg.output_dir)
    if output_policy.write_csv:
        output_dir_csv = ensure_output_dir(output_dir_csv)
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
        output_profile=args.output_profile,
    )

    cleanup_old_cache(keep_versions=3)

    print("\nDone.")
    if output_policy.write_csv:
        print(
            "  CSV in %s: asset_metrics, portfolio_metrics, rc_vol, correlation_matrix, rolling_*, var_es, eee, inputs/"
            % output_dir_csv
        )
    print(
        "  Final results in %s: JSON contracts (snapshot_*, stress_report, run_metadata, data_policy, portfolio_xray, output_manifest)"
        % output_dir_final
    )

    if cfg.pending_fields:
        print(f"\nFields awaiting user input: {cfg.pending_fields}")

    if cfg.target_nominal_return_annual is not None and portfolio_metrics_summary:
        realized = portfolio_metrics_summary.get("cagr")
        target = cfg.target_nominal_return_annual
        if realized is not None:
            diff = realized - target
            status = "[OK] met" if diff >= 0 else "[X] not met"
            print(f"\nTarget return: {target:.2%}, realized: {realized:.2%} ({status})")

    stress_report = meta["stress_report"]
    if portfolio_metrics_summary and cfg.target_max_drawdown_pct is not None:
        max_dd_limit = abs(cfg.target_max_drawdown_pct)
        realized_mdd = portfolio_metrics_summary.get("max_drawdown")
        if realized_mdd is not None and not (realized_mdd != realized_mdd):
            mdd_ok = realized_mdd >= -max_dd_limit
            print(
                f"\nMax DD: {'PASS' if mdd_ok else 'FAIL'} (target: -{max_dd_limit:.1%}, realized: {realized_mdd:.1%})"
            )
    if stress_report:
        st = stress_report.get("status", "N/A")
        reason = stress_report.get("fail_reason_code") or stress_report.get("skip_reason") or ""
        print(f"Stress Judge: {st}" + (f" ({reason})" if reason else ""))

    print(
        f"\nCache saved under cache/ (daily: {meta['daily_cache_key']}, monthly: {meta['monthly_cache_key']})"
    )

    if not meta["portfolio_valid"]:
        logger.warning(
            "Portfolio valid = False (e.g. MaxDD exceeds mandate). Report and files written; no exit (production workflow)."
        )

    if output_policy.write_pdf:
        from src.pdf_reports import try_rebuild_pdfs_after_main_report

        try:
            try_rebuild_pdfs_after_main_report(logger=logger)
        except Exception as e:
            logger.warning("PDF suite rebuild skipped: %s", e)


if __name__ == "__main__":
    main()
