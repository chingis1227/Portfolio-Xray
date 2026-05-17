"""
Run portfolio optimization (max expected return + ProLiquidity) and output weights.

RC_vol is computed in reports/stress for diagnostics only, not as an optimization constraint.

Uses config.yml; client_profile fills target_vol / max_drawdown / return / liquidity when set.

Run from project root: python run_optimization.py [--no-cache] [--write-config] [--config PATH] [--profile NAME] [--no-report]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.config import (
    WEIGHTS_FILENAME,
    apply_profile_override,
    load_assets_metadata,
    load_validated_config,
    portfolio_total_tickers,
    resolve_cash_and_rf,
)
from src.config_schema import ConfigValidationError
from src.etf_universe import UniverseValidationError, write_universe_diagnostics
from src.analysis_setup import build_analysis_setup
from src.input_assumptions import build_input_assumptions_from_analysis_setup
from src.metrics_asset import mandate_max_drawdown_full_history_check
from src.optimization import (
    get_risk_portfolio_tickers,
    portfolio_vol_annual,
    proliquidity,
    run_max_return_optimization,
)
from src.risk_contrib import cov_matrix_monthly, cov_matrix_returns
from src.robustness import compute_robustness_diagnostics, compute_robustness_flags
from src.snapshot import build_snapshot, print_snapshot, save_snapshot
from src.stress import run_stress
from src.utils import logger, setup_logging, tickers_meeting_coverage
from src.windows import slice_calendar_window
from src.returns_frequency import (
    MACRO_REGIME_FREQUENCY_DEFAULT,
    FACTOR_STRESS_FREQUENCY_DEFAULT,
    calendar_window_to_n_periods,
    compute_frequency_disclosure,
    normalize_returns_frequency,
    periods_per_year as periods_per_year_for,
)
from src.young_etfs_dual_cov import build_dual_covariance_and_mu, per_ticker_young_weight_caps

STATUS_APPROVED = "APPROVED"
STATUS_OK_FALLBACK = "OK_FALLBACK"
STATUS_FAIL_DATA = "FAIL_DATA"
STATUS_FAIL_MANDATE = "FAIL_MANDATE"

VIOL_FAIL_STRESS = "VIOL_FAIL_STRESS"
VIOL_FAIL_MANDATE = "VIOL_FAIL_MANDATE"
WARN_MODEL_RISK_YOUNG_WEIGHT = "WARN_MODEL_RISK_YOUNG_WEIGHT"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portfolio optimization - single-stage max return + liquidity")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cache, download fresh data")
    parser.add_argument("--write-config", action="store_true", help="Write optimized weights to config.yml")
    parser.add_argument("--profile", type=str, default=None, help="Override client_profile")
    parser.add_argument("--config", type=str, default=None, help="Path to config YAML (default: config.yml)")
    parser.add_argument("--no-report", action="store_true", help="Skip run_report.py after optimization")
    return parser.parse_args()


def _build_next_actions(violations: list, stress_report: dict | None) -> list[str]:
    actions: list[str] = []
    codes = {v["code"] for v in violations}
    if VIOL_FAIL_STRESS in codes and stress_report:
        actions.append("Stress diagnostic (DIAG_*): informational only; review scenario loss and RC concentration.")
    if VIOL_FAIL_MANDATE in codes:
        actions.append(
            "Mandate: historical max drawdown exceeds client limit; reduce risk or adjust target_max_drawdown_pct."
        )
    if WARN_MODEL_RISK_YOUNG_WEIGHT in codes:
        actions.append(
            "Young ETF aggregate weight above warn threshold - consider lower share of candidate/new names or dual-cov settings."
        )
    return actions


def load_monthly_returns(cfg, args) -> tuple[pd.DataFrame, str, pd.Timestamp, str]:
    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    assets_meta = load_assets_metadata()
    from src.data_loader import load_monthly_data_shared

    data = load_monthly_data_shared(
        tickers=cfg.tickers,
        benchmark_base_ticker=cfg.benchmark_base_ticker,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        investor_currency=cfg.investor_currency,
        windows_months=cfg.windows_months,
        assets_meta=assets_meta,
        no_cache=args.no_cache,
        local_benchmark_map=None,
        returns_frequency=getattr(cfg, "returns_frequency", None),
    )
    return data.monthly_returns, data.analysis_end_str, data.analysis_end, data.returns_frequency


def main() -> None:
    args = parse_args()
    setup_logging()

    try:
        cfg_path = Path(args.config).resolve() if args.config else None
        cfg = load_validated_config(cfg_path)
    except ConfigValidationError as e:
        logger.error("Configuration error: %s", e)
        raise SystemExit(1)

    if args.profile:
        apply_profile_override(cfg, args.profile.strip())
    if getattr(cfg, "analysis_mode", "optimize_from_universe") == "analyze_current_weights":
        logger.error(
            "analysis_mode=analyze_current_weights is a fixed-weight report mode. "
            "Use run_report.py for existing-portfolio diagnostics, or set "
            "analysis_mode=optimize_from_universe before running optimization."
        )
        raise SystemExit(1)
    profile_display = (cfg.client_profile or args.profile or "-").strip() or "-"

    out_final = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
    try:
        diag_path = write_universe_diagnostics(out_final, cfg.tickers)
        if diag_path:
            logger.info("ETF universe diagnostics: %s", diag_path)
    except UniverseValidationError as e:
        logger.error("%s", e)
        raise SystemExit(1)

    cash_proxy = cfg.cash_proxy_ticker or "BIL"
    risk_tickers_all = get_risk_portfolio_tickers(cfg.tickers, cfg.cash_proxy_ticker)
    if not risk_tickers_all:
        logger.error("No tickers for RiskPortfolio after excluding cash proxy.")
        raise SystemExit(1)

    logger.info("Loading data...")
    monthly_returns, analysis_end_str, analysis_end, returns_frequency = load_monthly_returns(cfg, args)
    ppy = int(periods_per_year_for(returns_frequency))

    window_months = int(getattr(cfg, "primary_window_months", 120) or 120)
    secondary_window_months = int(getattr(cfg, "secondary_window_months", 60) or 60)
    robustness_policy = getattr(cfg, "robustness_policy", None) or {}
    robustness_enabled = bool(robustness_policy.get("enabled", True))
    min_effective_months = int(robustness_policy.get("min_effective_months", 36))
    coverage_threshold = float(getattr(cfg, "coverage_threshold", 0.90) or 0.90)

    cols_primary = [t for t in risk_tickers_all if t in monthly_returns.columns]
    if not cols_primary:
        logger.error("FAIL_DATA: no risk tickers with returns")
        raise SystemExit(1)

    use_shrinkage = bool(getattr(cfg, "covariance_shrinkage", False))
    young_pol = getattr(cfg, "young_etf_optimization_policy", None) or {}
    dual_enabled = bool(young_pol.get("enabled", True))
    young_diagnostics: dict | None = None
    per_ticker_young_caps: dict[str, float] | None = None
    mu_series_primary: pd.Series | None = None
    ret_primary: pd.DataFrame
    cov_df: pd.DataFrame

    if dual_enabled:
        cov_df, mu_series_primary, young_diagnostics = build_dual_covariance_and_mu(
            monthly_returns,
            cols_primary,
            window_months,
            young_pol,
            use_shrinkage_on_core=use_shrinkage,
            analysis_end=analysis_end,
        )
        cols_primary = list(cov_df.columns)
        per_ticker_young_caps = per_ticker_young_weight_caps(
            young_diagnostics["tickers"],
            float(young_pol.get("max_weight_candidate_or_new_pct", 0.02)),
        )
        if not per_ticker_young_caps:
            per_ticker_young_caps = None
        ret_primary = (
            slice_calendar_window(monthly_returns[cols_primary], analysis_end, window_months)
            .dropna(axis=1, how="all")
            .dropna(how="any")
        )
        logger.info("Young-ETF optimization: mode=%s", young_diagnostics.get("mode"))
    else:
        MIN_FULL_JOIN = max(2, calendar_window_to_n_periods(11, returns_frequency))
        ret_primary = (
            slice_calendar_window(monthly_returns[cols_primary], analysis_end, window_months)
            .dropna(axis=1, how="all")
            .dropna(how="any")
        )
        if len(ret_primary) < MIN_FULL_JOIN:
            span = max(window_months * 4, 48)
            tail = monthly_returns[cols_primary].iloc[-span:]
            ae2 = pd.Timestamp(tail.index.max()).normalize()
            ret_primary = (
                slice_calendar_window(tail, ae2, window_months).dropna(axis=1, how="all").dropna(how="any")
            )
        cols_primary = list(ret_primary.columns)
        if not cols_primary:
            logger.error("FAIL_DATA: no assets with returns in window")
            raise SystemExit(1)
        cov_df = cov_matrix_returns(ret_primary, ddof=1, use_shrinkage=use_shrinkage)

    vol_lam = float(getattr(cfg, "optimization_soft_vol_penalty_lambda", 0.0) or 0.0)
    ret_lam = float(getattr(cfg, "optimization_soft_return_penalty_lambda", 0.0) or 0.0)
    if vol_lam <= 0:
        vol_lam = 12.0
    if ret_lam <= 0:
        ret_lam = 8.0
    tv = getattr(cfg, "target_vol_annual", None)
    tr = getattr(cfg, "target_nominal_return_annual", None)

    weights_risk, status = run_max_return_optimization(
        monthly_returns,
        cols_primary,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
        window_months=window_months,
        cash_proxy_ticker=cash_proxy,
        returns_window=None if dual_enabled else ret_primary,
        use_shrinkage=use_shrinkage,
        cov_precomputed=cov_df if dual_enabled else None,
        mu_precomputed=mu_series_primary if dual_enabled else None,
        per_ticker_max_weight=per_ticker_young_caps,
        soft_target_vol_annual=float(tv) if tv is not None else None,
        soft_vol_penalty_lambda=vol_lam,
        soft_target_return_annual=float(tr) if tr is not None else None,
        soft_return_penalty_lambda=ret_lam,
        periods_per_year=ppy,
        returns_frequency=returns_frequency,
    )

    if not weights_risk:
        logger.error("Optimization failed: %s", status)
        raise SystemExit(1)
    logger.info("RiskPortfolio (%d months): %s", window_months, status)

    if dual_enabled and young_diagnostics:
        effective_months_10y = int(young_diagnostics.get("core_effective_months", len(ret_primary)))
    else:
        effective_months_10y = len(ret_primary)
    if effective_months_10y < min_effective_months:
        logger.warning(
            "Primary window: effective months = %d (< %d).",
            effective_months_10y,
            min_effective_months,
        )

    mu_10y = mu_series_primary if dual_enabled and mu_series_primary is not None else ret_primary.mean()
    current_vol = portfolio_vol_annual(weights_risk, cov_df, periods_per_year=ppy)

    young_agg_warn_details: dict | None = None
    if dual_enabled and young_diagnostics and weights_risk:
        warn_pct_y = float(young_pol.get("aggregate_candidate_new_warn_pct", 0.10))
        young_set = {t for t, m in young_diagnostics["tickers"].items() if m.get("bucket") in ("candidate", "new")}
        young_w_sum = sum(float(weights_risk.get(t, 0.0)) for t in young_set)
        if young_w_sum > warn_pct_y + 1e-12:
            young_agg_warn_details = {
                "aggregate_weight": round(young_w_sum, 4),
                "threshold": round(warn_pct_y, 4),
                "tickers": sorted(young_set),
            }

    robustness_report = None
    cov_5y_pre: pd.DataFrame | None = None
    mu_5y_pre: pd.Series | None = None
    diag_5y: dict | None = None
    if dual_enabled:
        cov_5y_pre, mu_5y_pre, diag_5y = build_dual_covariance_and_mu(
            monthly_returns,
            cols_primary,
            secondary_window_months,
            young_pol,
            use_shrinkage_on_core=use_shrinkage,
            analysis_end=analysis_end,
        )
    if robustness_enabled and secondary_window_months < window_months:
        weights_5y_risk, status_5y = run_max_return_optimization(
            monthly_returns,
            cols_primary,
            min_single_security_weight_pct=cfg.min_single_security_weight_pct,
            max_single_security_weight_pct=cfg.max_single_security_weight_pct,
            window_months=secondary_window_months,
            cash_proxy_ticker=cash_proxy,
            use_shrinkage=use_shrinkage,
            cov_precomputed=cov_5y_pre if dual_enabled else None,
            mu_precomputed=mu_5y_pre if dual_enabled else None,
            per_ticker_max_weight=per_ticker_young_caps,
            periods_per_year=ppy,
            returns_frequency=returns_frequency,
        )
        cols_5y = [t for t in (weights_5y_risk or weights_risk) if t in monthly_returns.columns]
        ret_5y = slice_calendar_window(monthly_returns[cols_5y], analysis_end, secondary_window_months).dropna(
            how="any"
        )
        effective_months_5y = len(ret_5y)
        if dual_enabled and diag_5y is not None:
            effective_months_5y = int(diag_5y.get("core_effective_months", 0))
        cov_5y: pd.DataFrame | None = None
        mu_5y: pd.Series | None = None
        if weights_5y_risk and dual_enabled and cov_5y_pre is not None:
            cov_5y = cov_5y_pre
            mu_5y = mu_5y_pre
        elif weights_5y_risk and len(ret_5y) >= 2:
            cov_5y = cov_matrix_returns(ret_5y, ddof=1, use_shrinkage=use_shrinkage)
            mu_5y = ret_5y.mean()
        if weights_5y_risk and cov_5y is not None and mu_5y is not None and len(mu_5y):
            diagnostics = compute_robustness_diagnostics(
                weights_10y=weights_risk,
                weights_5y=weights_5y_risk,
                cov_10y=cov_df,
                cov_5y=cov_5y,
                mu_10y=mu_10y,
                mu_5y=mu_5y,
                effective_months_10y=effective_months_10y,
                effective_months_5y=effective_months_5y,
            )
            robustness_flags = compute_robustness_flags(diagnostics, dict(robustness_policy or {}))
            robustness_report = {
                "effective_months_10y": effective_months_10y,
                "effective_months_5y": effective_months_5y,
                "max_delta_w": round(diagnostics["max_delta_w"], 3),
                "top5_delta_w": [(t, round(d, 3)) for t, d in diagnostics["top5_delta_w"]],
                "rc_by_asset_10y": {k: round(v, 3) for k, v in (diagnostics.get("rc_by_asset_10y") or {}).items()},
                "rc_by_asset_5y": {k: round(v, 3) for k, v in (diagnostics.get("rc_by_asset_5y") or {}).items()},
                "max_rc_asset_delta": round(float(diagnostics.get("max_rc_asset_delta") or 0.0), 4),
                "rc_asset_deltas": {
                    k: round(float(v), 4) for k, v in (diagnostics.get("rc_asset_deltas") or {}).items()
                },
                "vol_10y_under_sigma10y": round(diagnostics.get("vol_10y_under_sigma10y", 0) * 100, 3),
                "vol_10y_under_sigma5y": round(diagnostics.get("vol_10y_under_sigma5y", 0) * 100, 3),
                "exp_ret_10y_mu10y_annual_pct": round(diagnostics.get("exp_ret_10y_under_mu10y_annual", 0) * 100, 3),
                "exp_ret_10y_mu5y_annual_pct": round(diagnostics.get("exp_ret_10y_under_mu5y_annual", 0) * 100, 3),
                "final_portfolio_is_10y": True,
                "flags": robustness_flags,
                "robust_vs_5y": len(robustness_flags) == 0,
            }
            out_final_rb = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
            out_final_rb.mkdir(parents=True, exist_ok=True)
            with open(out_final_rb / "robustness_report.json", "w", encoding="utf-8") as f:
                json.dump(robustness_report, f, indent=2)

    pv = cfg.portfolio_value if cfg.portfolio_value is not None and cfg.portfolio_value > 0 else cfg.initial_investable_amount
    liquidity_amount = cfg.liquidity_need_months * (cfg.monthly_expenses or 0)
    liquidity_floor_pct = getattr(cfg, "liquidity_floor_pct", None)
    if liquidity_floor_pct is None:
        liquidity_floor_pct = max(0.0, min(1.0, liquidity_amount / pv)) if pv > 0 else 0.0
    else:
        liquidity_floor_pct = max(0.0, min(1.0, float(liquidity_floor_pct)))

    target_vol = cfg.target_vol_annual if cfg.target_vol_annual is not None and cfg.target_vol_annual > 0 else 0.12
    final_weights, proliquidity_error = proliquidity(
        weights_risk,
        cash_proxy,
        current_vol,
        target_vol,
        liquidity_floor_pct,
        cfg.cash_policy,
        cov_df=cov_df,
        n_rc=cfg.N_rc,
        donor_shift_mode=cfg.donor_shift_mode,
        periods_per_year=ppy,
    )
    if proliquidity_error:
        logger.error("ProLiquidity: %s", proliquidity_error)
        raise SystemExit(1)

    for t in cfg.tickers:
        if t not in final_weights:
            final_weights[t] = 0.0

    rounded = {t: round(w, 3) for t, w in final_weights.items() if w > 0}
    print("\n" + "=" * 60)
    print("WEIGHTS AFTER OPTIMIZATION (profile: %s)" % profile_display)
    print("=" * 60)
    for t in sorted(rounded.keys(), key=lambda x: (-rounded[x], x)):
        print(f"  {t}: {rounded[t]:.3f}")
    print("=" * 60)
    print("Total weight: %.3f" % sum(final_weights.values()))
    print("Target volatility: %.2f%%" % (target_vol * 100))
    print("RiskPortfolio volatility estimate: %.2f%%" % (current_vol * 100))

    max_dd_limit = abs(cfg.target_max_drawdown_pct) if cfg.target_max_drawdown_pct is not None else None
    mandate_check = mandate_max_drawdown_full_history_check(monthly_returns, final_weights, max_dd_limit)
    max_dd_ok = mandate_check.get("pass")
    stress_tickers = portfolio_total_tickers(cfg.tickers, final_weights, cash_proxy)

    asset_betas_df = pd.DataFrame()
    portfolio_betas_dict: dict = {}
    portfolio_betas_5y_dict: dict = {}
    portfolio_betas_10y_dict: dict = {}
    recession_factor_returns = pd.DataFrame()
    try:
        from src.stress_factors import (
            FACTOR_COLUMN_ORDER,
            FACTOR_WEEKS_10Y,
            FACTOR_WEEKS_3Y,
            FACTOR_WEEKS_5Y,
            build_factor_matrix,
            compute_asset_factor_betas_weekly,
            portfolio_factor_betas,
        )

        beta_tickers = [t for t in stress_tickers if final_weights.get(t, 0) > 0] or list(stress_tickers)

        def _portfolio_betas_weekly(window_weeks: int) -> tuple[pd.DataFrame, dict]:
            asset_betas_win = compute_asset_factor_betas_weekly(beta_tickers, analysis_end_str, window_weeks)
            return asset_betas_win, portfolio_factor_betas(final_weights, asset_betas_win)

        asset_betas_5y_df, portfolio_betas_5y_dict = _portfolio_betas_weekly(FACTOR_WEEKS_5Y)
        _asset_betas_10y_df, portfolio_betas_10y_dict = _portfolio_betas_weekly(FACTOR_WEEKS_10Y)
        diagnostic_betas_5y_extended = portfolio_factor_betas(
            final_weights,
            compute_asset_factor_betas_weekly(beta_tickers, analysis_end_str, FACTOR_WEEKS_5Y, factor_columns=FACTOR_COLUMN_ORDER),
        )
        diagnostic_betas_10y_extended = portfolio_factor_betas(
            final_weights,
            compute_asset_factor_betas_weekly(beta_tickers, analysis_end_str, FACTOR_WEEKS_10Y, factor_columns=FACTOR_COLUMN_ORDER),
        )
        asset_betas_df = asset_betas_5y_df
        portfolio_betas_dict = portfolio_betas_5y_dict
        try:
            recession_factor_returns = build_factor_matrix("2007-01-01", analysis_end_str)
        except Exception as e:
            logger.warning("Recession factor calibration setup failed: %s; recession severe will use fallback.", e)
    except Exception as e:
        logger.warning("Could not build stress factors: %s", e)

    stress_report = run_stress(
        tickers=stress_tickers,
        weights=final_weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas_df,
        portfolio_betas=portfolio_betas_dict,
        target_max_drawdown_pct=cfg.target_max_drawdown_pct,
        cash_proxy_ticker=cash_proxy,
        factor_returns=recession_factor_returns,
    )

    if portfolio_betas_5y_dict:
        stress_report["factor_betas_5y"] = {k: round(v, 4) for k, v in portfolio_betas_5y_dict.items()}
        stress_report["factor_betas_10y"] = {k: round(v, 4) for k, v in portfolio_betas_10y_dict.items()}
        stress_report["factor_betas"] = dict(stress_report["factor_betas_5y"])

    try:
        from src.stress_factors import FACTOR_WEEKS_5Y, asset_factor_betas_dict_from_df

        stress_report["asset_factor_betas"] = asset_factor_betas_dict_from_df(asset_betas_df)
        stress_report["asset_factor_betas_meta"] = {
            "source": "compute_asset_factor_betas_weekly",
            "window_weeks": int(FACTOR_WEEKS_5Y),
            "n_assets": int(len(asset_betas_df.index)) if asset_betas_df is not None and not asset_betas_df.empty else 0,
        }
    except Exception as _e_afb:
        logger.warning("asset_factor_betas serialization skipped: %s", _e_afb)

    try:
        from src.stress_factors import (
            FACTOR_MONTHS_10Y,
            FACTOR_MONTHS_3Y,
            FACTOR_MONTHS_5Y,
            FACTOR_COLUMN_ORDER,
            FACTOR_WEEKS_10Y,
            FACTOR_WEEKS_3Y,
            FACTOR_WEEKS_5Y,
            compute_portfolio_factor_beta_oos_monthly,
            compute_portfolio_factor_beta_oos_weekly,
            compute_portfolio_rolling_factor_betas_monthly,
            compute_portfolio_rolling_factor_betas_weekly,
            attach_kalman_factor_betas_to_stress_report,
            build_diagnostic_oil_beta,
            build_factor_beta_diagnostic_overlay,
            enrich_historical_results_with_factor_attribution,
            factor_beta_oos_stability_diagnostics,
            factor_beta_stability_diagnostics,
            factor_beta_stability_rows,
            factor_covariance_analytics,
            factor_oos_beta_shock_explainability,
            factor_variance_decomposition_weekly,
            macro_regime_csv_frames,
            macro_regime_diagnostics,
            portfolio_pca_diagnostics,
            portfolio_factor_regression_weekly,
            rolling_beta_summary,
            write_rolling_betas_plot_html,
            write_rolling_betas_plot_pngs,
        )

        stress_report["factor_regression_5y"] = {}
        stress_report["factor_regression_10y"] = {}
        factor_regression_5y_extended: dict[str, Any] = {}
        factor_regression_10y_extended: dict[str, Any] = {}
        try:
            stress_report["factor_regression_5y"] = portfolio_factor_regression_weekly(
                weights=final_weights,
                tickers=stress_tickers,
                analysis_end_str=analysis_end_str,
                window_weeks=FACTOR_WEEKS_5Y,
            )
        except Exception as e:
            stress_report["factor_regression_5y_error"] = str(e)
        try:
            stress_report["factor_regression_10y"] = portfolio_factor_regression_weekly(
                weights=final_weights,
                tickers=stress_tickers,
                analysis_end_str=analysis_end_str,
                window_weeks=FACTOR_WEEKS_10Y,
            )
        except Exception as e:
            stress_report["factor_regression_10y_error"] = str(e)
        try:
            factor_regression_5y_extended = portfolio_factor_regression_weekly(
                weights=final_weights,
                tickers=stress_tickers,
                analysis_end_str=analysis_end_str,
                window_weeks=FACTOR_WEEKS_5Y,
                factor_columns=FACTOR_COLUMN_ORDER,
            )
            factor_regression_10y_extended = portfolio_factor_regression_weekly(
                weights=final_weights,
                tickers=stress_tickers,
                analysis_end_str=analysis_end_str,
                window_weeks=FACTOR_WEEKS_10Y,
                factor_columns=FACTOR_COLUMN_ORDER,
            )
        except Exception as e:
            stress_report["diagnostic_oil_beta_regression_error"] = str(e)

        rolling_windows = {"3y": FACTOR_WEEKS_3Y, "5y": FACTOR_WEEKS_5Y, "10y": FACTOR_WEEKS_10Y}
        rolling_windows_months = {"3y": FACTOR_MONTHS_3Y, "5y": FACTOR_MONTHS_5Y, "10y": FACTOR_MONTHS_10Y}
        rb = compute_portfolio_rolling_factor_betas_weekly(
            weights=final_weights,
            tickers=stress_tickers,
            analysis_end_str=analysis_end_str,
            rolling_windows_weeks=rolling_windows,
        )
        rb_monthly = compute_portfolio_rolling_factor_betas_monthly(
            monthly_returns=monthly_returns,
            weights=final_weights,
            analysis_end_str=analysis_end_str,
            rolling_windows_months=rolling_windows_months,
        )
        out_final_tmp = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
        out_final_tmp.mkdir(parents=True, exist_ok=True)
        out_csv_tmp = Path(getattr(cfg, "output_dir_csv", "results_csv"))
        out_csv_tmp.mkdir(parents=True, exist_ok=True)
        csv_paths: dict[str, str] = {}
        for lbl, df_rb in rb.items():
            if df_rb is None or df_rb.empty:
                continue
            p = out_csv_tmp / f"rolling_factor_betas_{lbl}.csv"
            df_rb.round(4).to_csv(p, index=True)
            csv_paths[lbl] = p.name
        monthly_csv_paths: dict[str, str] = {}
        for lbl, df_rb in rb_monthly.items():
            if df_rb is None or df_rb.empty:
                continue
            p = out_csv_tmp / f"rolling_factor_betas_monthly_{lbl}.csv"
            df_rb.round(4).to_csv(p, index=True)
            monthly_csv_paths[lbl] = p.name
        summary_df = rolling_beta_summary(rb)
        summary_struct: dict[str, dict[str, dict[str, float | int]]] = {}
        summary_csv_name = ""
        if not summary_df.empty:
            summary_csv = out_csv_tmp / "rolling_factor_betas_summary.csv"
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
        monthly_summary_struct: dict[str, dict[str, dict[str, float | int]]] = {}
        monthly_summary_csv_name = ""
        if not monthly_summary_df.empty:
            monthly_summary_csv = out_csv_tmp / "rolling_factor_betas_monthly_summary.csv"
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
            weights=final_weights,
            tickers=stress_tickers,
            analysis_end_str=analysis_end_str,
            rolling_windows_weeks=rolling_windows,
        )
        oos_monthly = compute_portfolio_factor_beta_oos_monthly(
            monthly_returns=monthly_returns,
            weights=final_weights,
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
            stability_csv = out_csv_tmp / "factor_beta_stability.csv"
            stability_df.round(4).to_csv(stability_csv, index=False)
            stability_csv_name = stability_csv.name
        plot_name = ""
        plot_png_by_window: dict[str, str] = {}
        if rb:
            plot_path = out_final_tmp / "rolling_factor_betas.html"
            write_rolling_betas_plot_html(rb, plot_path)
            plot_name = plot_path.name
            plot_png_by_window = write_rolling_betas_plot_pngs(rb, out_final_tmp)
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
        try:
            stress_report["factor_beta_shock_oos"] = factor_oos_beta_shock_explainability(
                weights=final_weights,
                tickers=stress_tickers,
                historical_results=stress_report.get("historical_results") or [],
                factor_betas_5y=stress_report.get("factor_betas_5y") or {},
                factor_betas_10y=stress_report.get("factor_betas_10y") or {},
                rolling_window_weeks=FACTOR_WEEKS_3Y,
            )
        except Exception as e:
            stress_report["factor_beta_shock_oos_error"] = str(e)
        try:
            stress_report["historical_results"] = enrich_historical_results_with_factor_attribution(
                stress_report.get("historical_results") or [],
                stress_report.get("factor_beta_shock_oos"),
                beta_source="5y",
            )
        except Exception as e:
            stress_report["factor_beta_shock_oos_error"] = str(e)
        try:
            overlay = build_factor_beta_diagnostic_overlay(
                weights=final_weights,
                tickers=stress_tickers,
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

        try:
            attach_kalman_factor_betas_to_stress_report(
                stress_report,
                weights=final_weights,
                tickers=stress_tickers,
                analysis_end_str=analysis_end_str,
                output_dir_csv=out_csv_tmp,
                window_weeks=FACTOR_WEEKS_10Y,
            )
        except Exception as e:
            stress_report["factor_betas_kalman_error"] = str(e)

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
                    df.round(6).to_csv(out_csv_tmp / fname)

            for regime, fname in {
                "base": "factor_correlation_base_5y_weekly.csv",
                "stress_empirical": "factor_correlation_stress_empirical_weekly.csv",
                "stress_overlay": "factor_correlation_stress_overlay_weekly.csv",
            }.items():
                df = _matrix_df(regime, "correlations")
                if not df.empty:
                    df.round(6).to_csv(out_csv_tmp / fname)

            for regime, fname in {
                "base": "portfolio_factor_rc_base.csv",
                "stress_empirical": "portfolio_factor_rc_stress_empirical.csv",
                "stress_overlay": "portfolio_factor_rc_stress_overlay.csv",
            }.items():
                rows = ((factor_cov.get("portfolio_factor_rc") or {}).get(regime) or [])
                if rows:
                    pd.DataFrame(rows).round(6).to_csv(out_csv_tmp / fname, index=False)

            overlay_deltas = ((factor_cov.get("stress_overlay") or {}).get("overlay_deltas") or [])
            if overlay_deltas:
                pd.DataFrame(overlay_deltas).round(6).to_csv(out_csv_tmp / "factor_covariance_overlay_deltas.csv", index=False)

            covariance_stability = factor_cov.get("covariance_stability_check") or {}
            stability_rows = []
            for row in covariance_stability.get("by_pair") or []:
                stability_rows.append({"type": "pair", **row})
            for row in covariance_stability.get("by_factor_variance") or []:
                stability_rows.append({"type": "factor_variance", **row})
            if stability_rows:
                pd.DataFrame(stability_rows).round(6).to_csv(out_csv_tmp / "factor_covariance_stability_check.csv", index=False)

            forecast_quality = factor_cov.get("forecast_quality") or {}
            forecast_rows = forecast_quality.get("rows") if isinstance(forecast_quality, dict) else []
            if forecast_rows:
                flat_rows = []
                for row in forecast_rows:
                    if not isinstance(row, dict):
                        continue
                    flat_rows.append({k: v for k, v in row.items() if k != "worst_corr_error_pair"})
                if flat_rows:
                    pd.DataFrame(flat_rows).round(6).to_csv(out_csv_tmp / "factor_covariance_forecast_quality.csv", index=False)
        except Exception as e:
            stress_report["factor_covariance_error"] = str(e)
            logger.warning("Factor covariance analytics failed: %s", e)

        try:
            macro_regimes = macro_regime_diagnostics(
                weights=final_weights,
                tickers=stress_tickers,
                analysis_end_str=analysis_end_str,
                factor_returns=recession_factor_returns if not recession_factor_returns.empty else None,
            )
            stress_report["macro_regime_diagnostics"] = macro_regimes
            for fname, df in macro_regime_csv_frames(macro_regimes).items():
                if not df.empty:
                    df.round(6).to_csv(out_csv_tmp / fname, index=False)
            quality_summary = (macro_regimes or {}).get("regime_label_quality_check")
            if isinstance(quality_summary, dict) and quality_summary:
                (out_final_tmp / "regime_label_quality_summary.json").write_text(
                    json.dumps(quality_summary, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
        except Exception as e:
            stress_report["macro_regime_diagnostics_error"] = str(e)
            logger.warning("Macro regime diagnostics failed: %s", e)

        try:
            stress_report["diagnostic_oil_beta"] = build_diagnostic_oil_beta(
                factor_betas_5y_extended=locals().get("diagnostic_betas_5y_extended", {}),
                factor_betas_10y_extended=locals().get("diagnostic_betas_10y_extended", {}),
                factor_regression_5y_extended=factor_regression_5y_extended,
                factor_regression_10y_extended=factor_regression_10y_extended,
                factor_covariance=stress_report.get("factor_covariance") or {},
                kalman_report=stress_report.get("factor_betas_kalman") or {},
            )
        except Exception as e:
            stress_report["diagnostic_oil_beta_error"] = str(e)
            logger.warning("Diagnostic Oil beta block failed: %s", e)

        try:
            factor_decomp = factor_variance_decomposition_weekly(
                weights=final_weights,
                tickers=stress_tickers,
                analysis_end_str=analysis_end_str,
                window_weeks=FACTOR_WEEKS_5Y,
            )
            stress_report["factor_variance_decomposition"] = factor_decomp
            for warning in factor_decomp.get("warnings") or []:
                logger.warning("Factor variance decomposition warning: %s", warning)
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
                pd.DataFrame(export_rows).round(8).to_csv(out_csv_tmp / "factor_variance_decomposition_5y.csv", index=False)
        except Exception as e:
            stress_report["factor_variance_decomposition_error"] = str(e)
            logger.warning("Factor variance decomposition failed: %s", e)

        try:
            pca = portfolio_pca_diagnostics(
                weights=final_weights,
                tickers=stress_tickers,
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
                    rolling_summary = rolling.get("summary") if isinstance(rolling, dict) else {}
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
                            "rolling_stability_severity": (rolling_summary or {}).get("stability_severity") if isinstance(rolling_summary, dict) else None,
                            "rolling_trend_slope_per_year": (rolling_summary or {}).get("trend_slope_per_year") if isinstance(rolling_summary, dict) else None,
                            "rolling_latest_minus_mean": (rolling_summary or {}).get("latest_minus_mean") if isinstance(rolling_summary, dict) else None,
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
                pd.DataFrame(summary_rows).round(8).to_csv(out_csv_tmp / "portfolio_pca_summary_5y.csv", index=False)
            if component_rows:
                pd.DataFrame(component_rows).round(8).to_csv(out_csv_tmp / "portfolio_pca_components_5y.csv", index=False)
            if rolling_rows:
                pd.DataFrame(rolling_rows).round(8).to_csv(out_csv_tmp / "portfolio_pca_rolling_pc1.csv", index=False)
            if corr_rows:
                pd.DataFrame(corr_rows).round(8).to_csv(out_csv_tmp / "portfolio_pca_pc1_factor_correlations.csv", index=False)
        except Exception as e:
            stress_report["portfolio_pca_error"] = str(e)
            logger.warning("Portfolio PCA diagnostics failed: %s", e)
    except Exception as e:
        stress_report["factor_betas_rolling_error"] = str(e)

    _stress_out = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
    _stress_out.mkdir(parents=True, exist_ok=True)
    try:
        from src.io_export import export_stress_report

        rf_norm = normalize_returns_frequency(returns_frequency)
        macro_notes = ""
        if rf_norm != "monthly":
            macro_notes = (
                f"Portfolio metrics and covariance use returns_frequency={rf_norm}; factor betas/regression/stress shocks "
                f"stay {FACTOR_STRESS_FREQUENCY_DEFAULT}; macro regime classifier labels remain {MACRO_REGIME_FREQUENCY_DEFAULT}; "
                "regime_factor_analytics may use daily returns when daily data loads (see regime_factor_analytics.summary)."
            )
        stress_report["frequency_disclosure"] = compute_frequency_disclosure(
            returns_frequency=rf_norm,
            optimization_frequency=rf_norm,
            factor_stress_frequency=FACTOR_STRESS_FREQUENCY_DEFAULT,
            macro_regime_frequency=MACRO_REGIME_FREQUENCY_DEFAULT,
            macro_regime_frequency_notes=(macro_notes or None),
        )
        stress_report["periods_per_year"] = int(periods_per_year_for(rf_norm))

        export_stress_report(stress_report, _stress_out)
    except Exception as e:
        logger.warning("export_stress_report failed: %s", e)
    try:
        from src.portfolio_commentary import write_stress_commentary

        write_stress_commentary(_stress_out, stress_report=stress_report, analysis_end=analysis_end_str)
    except Exception as e:
        logger.warning("write_stress_commentary failed: %s", e)

    stress_status = stress_report.get("status")
    stress_fail_reason = stress_report.get("fail_reason_code") or stress_report.get("skip_reason")

    rc_breaches: list[dict] = []

    if "OK_FALLBACK" in status:
        production_status = STATUS_OK_FALLBACK
    else:
        production_status = STATUS_APPROVED

    violations: list[dict] = []
    if young_agg_warn_details:
        violations.append({"code": WARN_MODEL_RISK_YOUNG_WEIGHT, "details": young_agg_warn_details})
    if stress_status == "DIAG_ATTENTION":
        violations.append({
            "code": VIOL_FAIL_STRESS,
            "details": {
                "note": "diagnostic_only",
                "diagnostic_codes": stress_report.get("diagnostic_codes", []),
                "primary_diagnostic_code": stress_report.get("primary_diagnostic_code"),
            },
        })

    mandate_gate_passed = True
    if max_dd_limit is not None:
        if max_dd_ok is False:
            mandate_gate_passed = False
            violations.append({
                "code": VIOL_FAIL_MANDATE,
                "details": {
                    "target_max_drawdown_pct": cfg.target_max_drawdown_pct,
                    "max_drawdown_realized": mandate_check.get("max_drawdown_realized"),
                    "history_start": mandate_check.get("history_start"),
                    "history_end": mandate_check.get("history_end"),
                    "months_used": mandate_check.get("months_used"),
                    "reason": "exceeds_limit",
                },
            })
        elif max_dd_ok is None:
            mandate_gate_passed = False
            violations.append({
                "code": VIOL_FAIL_MANDATE,
                "details": {
                    "reason": "insufficient_overlapping_history",
                    "months_used": mandate_check.get("months_used", 0),
                },
            })

    stress_summary = {
        "mandate_historical_max_dd_pass": mandate_check.get("pass"),
        "mandate_max_drawdown_realized": mandate_check.get("max_drawdown_realized"),
        "mandate_history_start": mandate_check.get("history_start"),
        "mandate_history_end": mandate_check.get("history_end"),
        "mandate_months_used": mandate_check.get("months_used"),
        "diagnostic_status": stress_status,
        "diagnostic_codes": stress_report.get("diagnostic_codes", []),
        "primary_diagnostic_code": stress_report.get("primary_diagnostic_code"),
        "status": stress_status,
        "fail_reason_code": stress_fail_reason,
        "worst_scenario_loss_pct": stress_report.get("worst_scenario_loss_pct"),
        "failed_scenario": stress_report.get("failed_scenario"),
    }
    next_actions = _build_next_actions(violations, stress_report)

    if not mandate_gate_passed:
        production_status = STATUS_FAIL_MANDATE

    write_weights_gate = mandate_gate_passed
    try:
        resolved_cash_proxy, resolved_rf_source = resolve_cash_and_rf(cfg)
    except ConfigValidationError:
        resolved_cash_proxy, resolved_rf_source = cash_proxy, None
    analysis_setup = build_analysis_setup(
        cfg,
        portfolio_weights=final_weights,
        weights_source="optimization_result_released" if write_weights_gate else "optimization_result_blocked",
        cash_proxy_ticker=resolved_cash_proxy,
        rf_source=resolved_rf_source,
        analysis_end=analysis_end_str,
        windows_months=list(getattr(cfg, "windows_months", []) or []),
        returns_frequency=returns_frequency,
        periods_per_year=ppy,
        run_context="optimization",
    )
    input_assumptions = build_input_assumptions_from_analysis_setup(analysis_setup)
    run_result: dict = {
        "weights": rounded if write_weights_gate else {},
        "status": production_status,
        "analysis_setup": analysis_setup,
        "input_assumptions": input_assumptions,
        "mandate_check": mandate_check,
        "violations": violations,
        "rc_breaches": rc_breaches,
        "stress_summary": stress_summary,
        "stress_diagnostic_report": stress_report,
        "next_actions": next_actions,
        "optimization_status": status,
        "young_etf_dual_cov_enabled": dual_enabled,
        "young_etf_diagnostics": young_diagnostics,
        "young_etf_aggregate_weight_warn": young_agg_warn_details,
    }
    try:
        run_result["resolved_config"] = cfg.get_resolved_config()
    except Exception:
        run_result["resolved_config"] = None

    baseline_tickers = set(
        tickers_meeting_coverage(monthly_returns, analysis_end, window_months, coverage_threshold)
    )
    risk_baseline = get_risk_portfolio_tickers([t for t in cfg.tickers if t in baseline_tickers], cfg.cash_proxy_ticker)
    if risk_baseline:
        weights_baseline, status_baseline = run_max_return_optimization(
            monthly_returns,
            risk_baseline,
            min_single_security_weight_pct=cfg.min_single_security_weight_pct,
            max_single_security_weight_pct=cfg.max_single_security_weight_pct,
            window_months=window_months,
            cash_proxy_ticker=cash_proxy,
            use_shrinkage=use_shrinkage,
            periods_per_year=ppy,
            returns_frequency=returns_frequency,
        )
        if weights_baseline:
            cols_b = [t for t in weights_baseline if t in monthly_returns.columns]
            ret_b = slice_calendar_window(monthly_returns[cols_b], analysis_end, window_months).dropna(how="any")
            if len(ret_b) >= 2:
                cov_b = cov_matrix_returns(ret_b, ddof=1, use_shrinkage=use_shrinkage)
                vol_b = portfolio_vol_annual(weights_baseline, cov_b, periods_per_year=ppy)
                print("  Baseline: volatility %.2f%% (vs Full: %.2f%%)" % (vol_b * 100, current_vol * 100))

    out_final = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
    out_final.mkdir(parents=True, exist_ok=True)
    run_result_path = out_final / "run_result.json"
    with open(run_result_path, "w", encoding="utf-8") as f:
        json.dump(run_result, f, indent=2, default=str)
    print("Run result: %s (status=%s)" % (run_result_path, production_status))

    from src.io_export import generate_ips_summary

    generate_ips_summary(cfg, run_result, out_final / "ips_summary.txt")

    if not mandate_gate_passed:
        logger.error("Mandate gate failed. Weights not written. %s", mandate_check)
        print("")
        print("--- MaxDD mandate: weights NOT written (FAIL_MANDATE) ---")
        raise SystemExit(1)

    weights_path = out_final / WEIGHTS_FILENAME
    with open(weights_path, "w", encoding="utf-8") as f:
        yaml.dump(rounded, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print("Weights written to %s." % weights_path)

    try:
        _resolved = cfg.get_resolved_config()
    except Exception:
        _resolved = None
    snapshot = build_snapshot(
        final_weights_total=final_weights,
        cash_proxy_ticker=cash_proxy,
        analysis_end=analysis_end_str,
        stress_report=stress_report,
        final_weights_risk_portfolio=weights_risk,
        monthly_returns=monthly_returns,
        window_months=window_months,
        target_vol_annual=target_vol,
        current_vol_annual=current_vol,
        max_dd_ok=max_dd_ok,
        rc_caps_ok=None,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
        resolved_config=_resolved,
    )
    print_snapshot(snapshot)
    save_snapshot(snapshot, out_final)
    print("Snapshot saved to %s" % (out_final / "snapshot.json"))

    project_root = Path(__file__).resolve().parent
    if not args.no_report:
        report_cmd = [sys.executable, "run_report.py"]
        if args.no_cache:
            report_cmd.append("--no-cache")
        try:
            subprocess.run(report_cmd, cwd=project_root, check=True)
        except subprocess.CalledProcessError as e:
            logger.warning("Report failed (exit %s). Weights saved. %s", e.returncode, e)
        try:
            from src.pdf_reports import try_rebuild_pdfs_after_main_report

            try_rebuild_pdfs_after_main_report(logger=logger)
        except Exception as ex:
            logger.warning("PDF rebuild: %s", ex)
    else:
        logger.info("Skipping run_report.py (--no-report).")
        try:
            from src.pdf_reports import try_rebuild_pdfs_after_main_report

            try_rebuild_pdfs_after_main_report(logger=logger)
        except Exception as ex:
            logger.warning("PDF rebuild: %s", ex)

    if args.write_config:
        config_path = Path(__file__).resolve().parent / "config.yml"
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        data["weights"] = rounded
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print("Weights also written to config.yml (weights).")


if __name__ == "__main__":
    main()
