"""
Run portfolio optimization (risk budget + ProLiquidity) and output weights.
Uses config.yml; client_profile (e.g. Growth) supplies rc_block_targets.
Run from project root: python run_optimization.py [--no-cache] [--write-config]

Output: final weights are written to portfolio_weights.yml. Use --write-config to also write them into config.yml (legacy).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

from src.config import (
    load_validated_config,
    load_assets_metadata,
    resolve_cash_and_rf,
    WEIGHTS_FILENAME,
    apply_profile_override,
)
from src.config_schema import ConfigValidationError
from src.data_loader import load_monthly_data_shared
from src.optimization import (
    get_risk_portfolio_tickers,
    run_risk_budget_optimization,
    proliquidity,
    portfolio_vol_annual,
    rc_by_block_from_weights,
    rc_by_asset_from_weights,
    check_rb_corridor,
    RB_CORRIDOR_PP,
)
from src.risk_contrib import cov_matrix_monthly, resolve_rc_asset_cap
from src.robustness import (
    compute_robustness_diagnostics,
    compute_robustness_flags,
    FLAG_WEIGHT_INSTABILITY,
    FLAG_RB_INSTABILITY,
    FLAG_RC_INSTABILITY,
    FLAG_SHORT_SAMPLE,
)
from src.snapshot import build_snapshot, print_snapshot, save_snapshot
from src.stress import run_stress
from src.utils import setup_logging, logger, tickers_meeting_coverage
from src.block_selection import apply_block_selection


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portfolio optimization — risk budget + ProLiquidity")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cache, download fresh data")
    parser.add_argument("--write-config", action="store_true", help="Write optimized weights to config.yml")
    parser.add_argument("--profile", type=str, default=None, help="Override client_profile (e.g. Growth, conservative)")
    return parser.parse_args()


# Production workflow: status and violation codes
STATUS_APPROVED = "APPROVED"
STATUS_CANDIDATE_RB_BREACH = "CANDIDATE_RB_BREACH"
STATUS_OK_FALLBACK = "OK_FALLBACK"
STATUS_FAIL_DATA = "FAIL_DATA"

VIOL_RB_BREACH = "RB_BREACH"
VIOL_RC_ASSET_CAP = "VIOL_RC_ASSET_CAP"
VIOL_FAIL_STRESS = "FAIL_STRESS"
VIOL_MAX_DD_BREACH = "MAX_DD_BREACH"


def _rb_deltas_pp(actual_rc_block: dict, rc_block_targets: dict) -> dict[str, float]:
    """Return per-block delta in percentage points: (actual - target) * 100."""
    out = {}
    for b in ("Growth", "Duration", "Inflation"):
        t = rc_block_targets.get(b)
        a = actual_rc_block.get(b)
        if t is not None and a is not None:
            out[b] = round((a - t) * 100.0, 2)
    return out


def _build_next_actions(
    violations: list,
    rb_deltas_pp: dict,
    stress_report: dict | None,
) -> list[str]:
    """Deterministic recommendations when violations occur."""
    actions = []
    codes = {v["code"] for v in violations}
    if VIOL_RB_BREACH in codes:
        actions.append(
            "Re-run with wider corridor (e.g., 7pp) OR relax secondary caps (weight caps) minimally."
        )
        actions.append(
            "If still RB_BREACH: increase k_block (add instruments) in the offending block(s)."
        )
        if rb_deltas_pp.get("Growth"):
            actions.append(
                "If Growth capacity constraints prevent W_growth: add satellites or relax max_weight_sat/core caps."
            )
    if VIOL_RC_ASSET_CAP in codes:
        actions.append(
            "Consider adding assets to dilute RC or relax rc_asset_cap; review breached tickers."
        )
    if VIOL_FAIL_STRESS in codes and stress_report:
        actions.append(
            "Consider: increase liquidity, shorten duration, reduce high growth/HY exposure."
        )
    if VIOL_MAX_DD_BREACH in codes:
        actions.append(
            "Realized max drawdown exceeds mandate; consider reducing risk (target_vol, growth share) or liquidity."
        )
    return actions


def load_monthly_returns(cfg, args) -> tuple[pd.DataFrame, str, pd.Timestamp]:
    """Load or build monthly returns via shared data loader; return (monthly_returns_df, analysis_end_str, analysis_end)."""
    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    assets_meta = load_assets_metadata()
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
    )
    return data.monthly_returns, data.analysis_end_str, data.analysis_end


def main() -> None:
    args = parse_args()
    setup_logging()

    try:
        cfg = load_validated_config()
    except ConfigValidationError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        raise SystemExit(1)

    # Single source of truth for profile: config is already applied in load_validated_config.
    # CLI --profile overrides once (no second read of config file).
    if args.profile:
        apply_profile_override(cfg, args.profile.strip())
    profile_display = (cfg.client_profile or args.profile or "—").strip() or "—"
    if cfg.rc_block_targets:
        logger.info(
            "Профиль %s: target_vol=%.2f%%, rc_block_targets=%s",
            profile_display,
            (cfg.target_vol_annual or 0) * 100,
            cfg.rc_block_targets,
        )

    if not cfg.rc_block_targets:
        logger.error(
            "rc_block_targets не заданы. Укажите client_profile (например Growth) в config.yml "
            "или задайте rc_block_targets вручную (Growth, Duration, Inflation; сумма = 1)."
        )
        raise SystemExit(1)

    risk_tickers = get_risk_portfolio_tickers(cfg.blocks)
    if not risk_tickers:
        logger.error("В конфиге нет тикеров в блоках Growth, Duration или Inflation.")
        raise SystemExit(1)

    logger.info("Загрузка данных...")
    monthly_returns, analysis_end_str, analysis_end = load_monthly_returns(cfg, args)
    # Primary optimization window (default 10Y = 120 months). Final portfolio = weights from this window.
    window_months = getattr(cfg, "primary_window_months", 120) or 120
    primary_window_months = getattr(cfg, "primary_window_months", 120) or 120
    secondary_window_months = getattr(cfg, "secondary_window_months", 60) or 60
    robustness_policy = getattr(cfg, "robustness_policy", None) or {}
    robustness_enabled = robustness_policy.get("enabled", True)
    min_effective_months = robustness_policy.get("min_effective_months", 36)
    coverage_threshold = getattr(cfg, "coverage_threshold", 0.90) or 0.90

    if primary_window_months < min_effective_months:
        logger.warning(
            "primary_window_months (%d) < min_effective_months (%d); sample length after join may trigger FLAG_SHORT_SAMPLE.",
            primary_window_months,
            min_effective_months,
        )

    # Block selection: Duration/Inflation candidate selection (per optimization_duration_spec, optimization_inflation_spec)
    block_result = apply_block_selection(
        cfg.blocks,
        config=cfg,
        monthly_returns=monthly_returns,
        window_months=window_months,
        rc_block_targets=cfg.rc_block_targets,
    )
    if block_result.get("status") == "FAIL_DATA":
        logger.error("Block selection FAIL_DATA: %s", block_result.get("reason", ""))
        raise SystemExit(1)
    if block_result.get("status") == "FAIL_FEASIBILITY":
        logger.error("Block selection FAIL_FEASIBILITY: %s", block_result.get("reason", ""))
        raise SystemExit(1)
    blocks_for_optimization = block_result.get("blocks", cfg.blocks)
    duration_internal_weights = block_result.get("duration_internal_weights")
    inflation_internal_weights = block_result.get("inflation_internal_weights")
    if duration_internal_weights:
        logger.info("Duration block selection: internal_weights=%s", duration_internal_weights)
    if inflation_internal_weights:
        logger.info("Inflation block selection: internal_weights=%s", inflation_internal_weights)

    # --- A) Primary optimization (10Y by default): this is the final portfolio ---
    weights_risk, status = run_risk_budget_optimization(
        monthly_returns,
        blocks_for_optimization,
        cfg.rc_block_targets,
        cfg.growth_core_candidates,
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
        window_months=window_months,
        duration_internal_weights=duration_internal_weights,
        inflation_internal_weights=inflation_internal_weights,
    )

    if not weights_risk:
        logger.error(f"Оптимизация не удалась: {status}")
        raise SystemExit(1)

    logger.info(f"RiskPortfolio (primary %d мес.): {status}", window_months)

    # Covariance and effective sample length for primary window (inner join)
    cols_primary = [t for t in weights_risk if t in monthly_returns.columns]
    ret_slice = monthly_returns[cols_primary].iloc[-window_months:].dropna(how="any")
    effective_months_10y = len(ret_slice)
    if effective_months_10y < min_effective_months:
        logger.warning(
            "Primary window: effective months after inner join = %d (< %d). Robustness may flag FLAG_SHORT_SAMPLE.",
            effective_months_10y,
            min_effective_months,
        )
    cov_df = cov_matrix_monthly(ret_slice, ddof=1)
    mu_10y = ret_slice.mean()
    actual_rc_block = rc_by_block_from_weights(weights_risk, cov_df, blocks_for_optimization)
    if actual_rc_block and cfg.rc_block_targets:
        logger.info(
            "RC по блокам на основном окне (%d мес.): %s",
            window_months,
            actual_rc_block,
        )
    current_vol = portfolio_vol_annual(weights_risk, cov_df)

    # --- B) Secondary optimization (5Y) and robustness diagnostics ---
    robustness_report = None
    if robustness_enabled and secondary_window_months < primary_window_months:
        weights_5y_risk, status_5y = run_risk_budget_optimization(
            monthly_returns,
            blocks_for_optimization,
            cfg.rc_block_targets,
            cfg.growth_core_candidates,
            rc_asset_cap_pct=cfg.rc_asset_cap_pct,
            min_single_security_weight_pct=cfg.min_single_security_weight_pct,
            max_single_security_weight_pct=cfg.max_single_security_weight_pct,
            window_months=secondary_window_months,
            duration_internal_weights=duration_internal_weights,
            inflation_internal_weights=inflation_internal_weights,
        )
        cols_5y = [t for t in (weights_5y_risk or weights_risk) if t in monthly_returns.columns]
        ret_5y = monthly_returns[cols_5y].iloc[-secondary_window_months:].dropna(how="any")
        effective_months_5y = len(ret_5y)
        if effective_months_5y < min_effective_months:
            logger.warning(
                "Secondary window: effective months after inner join = %d (< %d).",
                effective_months_5y,
                min_effective_months,
            )
        if weights_5y_risk and len(ret_5y) >= 2:
            cov_5y = cov_matrix_monthly(ret_5y, ddof=1)
            mu_5y = ret_5y.mean()
            diagnostics = compute_robustness_diagnostics(
                weights_10y=weights_risk,
                weights_5y=weights_5y_risk,
                cov_10y=cov_df,
                cov_5y=cov_5y,
                mu_10y=mu_10y,
                mu_5y=mu_5y,
                blocks=blocks_for_optimization,
                rc_block_targets=cfg.rc_block_targets,
                effective_months_10y=effective_months_10y,
                effective_months_5y=effective_months_5y,
            )
            flags = compute_robustness_flags(diagnostics, robustness_policy)
            robustness_report = {
                "effective_months_10y": effective_months_10y,
                "effective_months_5y": effective_months_5y,
                "max_delta_w": round(diagnostics["max_delta_w"], 3),
                "top5_delta_w": [(t, round(d, 3)) for t, d in diagnostics["top5_delta_w"]],
                "rc_by_block_10y": {k: round(v, 3) for k, v in (diagnostics.get("rc_by_block_10y") or {}).items()},
                "rc_by_block_5y": {k: round(v, 3) for k, v in (diagnostics.get("rc_by_block_5y") or {}).items()},
                "rc_block_targets": diagnostics.get("rc_block_targets"),
                "vol_10y_under_sigma10y": round(diagnostics.get("vol_10y_under_sigma10y", 0) * 100, 3),
                "vol_10y_under_sigma5y": round(diagnostics.get("vol_10y_under_sigma5y", 0) * 100, 3),
                "exp_ret_10y_mu10y_annual_pct": round(diagnostics.get("exp_ret_10y_under_mu10y_annual", 0) * 100, 3),
                "exp_ret_10y_mu5y_annual_pct": round(diagnostics.get("exp_ret_10y_under_mu5y_annual", 0) * 100, 3),
                "flags": flags,
                "stabilization_actions": [],
                "final_portfolio_is_10y": True,
                "robust_vs_5y": len(flags) == 0,
            }
            if flags:
                logger.warning(
                    "Dual-horizon robustness flags: %s. Final portfolio remains 10Y; see report for details.",
                    ", ".join(flags),
                )
            else:
                logger.info("Dual-horizon robustness: 10Y solution is consistent with 5Y (no flags).")
            # Persist for report (ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ)
            out_final = Path(getattr(cfg, "output_dir_final", "ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ"))
            out_final.mkdir(parents=True, exist_ok=True)
            with open(out_final / "robustness_report.json", "w", encoding="utf-8") as f:
                json.dump(robustness_report, f, indent=2)
        elif weights_5y_risk:
            logger.warning("Secondary optimization succeeded but effective 5Y sample < 2 months; robustness report skipped.")

    # ProLiquidity (with Alpha Shift when cash prohibited and vol > target)
    # Liquidity floor: from profile/config (liquidity_floor_pct) when set, else derived from liquidity_need_months * monthly_expenses / portfolio_value
    pv = cfg.portfolio_value if cfg.portfolio_value is not None and cfg.portfolio_value > 0 else cfg.initial_investable_amount
    liquidity_amount = cfg.liquidity_need_months * (cfg.monthly_expenses or 0)
    liquidity_floor_pct = getattr(cfg, "liquidity_floor_pct", None)
    if liquidity_floor_pct is None:
        liquidity_floor_pct = max(0.0, min(1.0, liquidity_amount / pv)) if pv > 0 else 0.0
    else:
        liquidity_floor_pct = max(0.0, min(1.0, float(liquidity_floor_pct)))

    target_vol = cfg.target_vol_annual if cfg.target_vol_annual is not None and cfg.target_vol_annual > 0 else 0.12
    cash_proxy = cfg.cash_proxy_ticker or "BIL"
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
        blocks=blocks_for_optimization,
        growth_core_candidates=cfg.growth_core_candidates,
    )
    if proliquidity_error:
        logger.error("ProLiquidity: %s", proliquidity_error)
        raise SystemExit(1)

    # Ensure all config tickers appear (zero if not in optimization)
    for t in cfg.tickers:
        if t not in final_weights:
            final_weights[t] = 0.0

    # Round for display
    rounded = {t: round(w, 3) for t, w in final_weights.items() if w > 0}
    print("\n" + "=" * 60)
    print("ВЕСА ПОСЛЕ ОПТИМИЗАЦИИ (профиль: %s)" % profile_display)
    print("=" * 60)
    for t in sorted(rounded.keys(), key=lambda x: (-rounded[x], x)):
        print(f"  {t}: {rounded[t]:.3f}")
    print("=" * 60)
    print("Сумма весов: %.3f" % sum(final_weights.values()))
    print("Целевая волатильность: %.2f%%" % (target_vol * 100))
    print("Волатильность RiskPortfolio (оценка): %.2f%%" % (current_vol * 100))

    # Guardrails: Max DD (исторический) — жёсткий; Stress Judge — диагностический
    max_dd_limit = abs(cfg.target_max_drawdown_pct) if cfg.target_max_drawdown_pct is not None else None
    max_dd_ok = None
    stress_status = None
    stress_fail_reason = None

    cols_port = [t for t in final_weights if t in monthly_returns.columns and final_weights.get(t, 0) > 0]
    if cols_port and max_dd_limit is not None:
        from src.metrics_asset import max_drawdown

        ret_slice = monthly_returns[cols_port].iloc[-window_months:]
        w_vec = [final_weights[t] for t in cols_port]
        port_ret = ret_slice.dot(w_vec).dropna()
        if len(port_ret) >= 2:
            mdd, _ = max_drawdown(port_ret)
            max_dd_ok = mdd >= -max_dd_limit if mdd is not None and not (mdd != mdd) else None

    asset_betas_df = pd.DataFrame()
    portfolio_betas_dict = {}
    try:
        from src.stress_factors import (
            build_factor_matrix_monthly,
            estimate_betas_monthly,
            portfolio_factor_betas,
        )

        beta_start = (analysis_end - pd.DateOffset(months=36)).strftime("%Y-%m-%d")
        factor_monthly = build_factor_matrix_monthly(beta_start, analysis_end_str)
        asset_returns_beta = monthly_returns[[t for t in cfg.tickers if t in monthly_returns.columns]].copy()
        asset_betas_df = estimate_betas_monthly(asset_returns_beta, factor_monthly, min_observations=24)
        portfolio_betas_dict = portfolio_factor_betas(final_weights, asset_betas_df)
    except Exception as e:
        logger.warning("Не удалось построить факторы для Stress Judge: %s", e)

    stress_top3_cap = getattr(cfg, "stress_top3_rc_sum_cap_pct", 0.70) or 0.70
    stress_report = run_stress(
        tickers=cfg.tickers,
        weights=final_weights,
        blocks=cfg.blocks,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas_df,
        portfolio_betas=portfolio_betas_dict,
        target_max_drawdown_pct=cfg.target_max_drawdown_pct,
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
        stress_top3_rc_sum_cap_pct=stress_top3_cap,
    )
    stress_status = stress_report.get("status")
    stress_fail_reason = stress_report.get("fail_reason_code") or stress_report.get("skip_reason")

    print("")
    print("--- Guardrails (production: warning-only, weights always saved) ---")
    if max_dd_limit is not None:
        if max_dd_ok is True:
            print("  Max DD: PASS (портфель в пределах целевой просадки)")
        elif max_dd_ok is False:
            print("  Max DD: FAIL (реализованная просадка хуже целевой %.1f%%) — флаг нарушения" % (max_dd_limit * 100))
        else:
            print("  Max DD: не проверен (недостаточно данных)")
    else:
        print("  Max DD: не задан (target_max_drawdown_pct отсутствует)")
    if stress_status is not None:
        if stress_status == "PASS":
            print("  Stress Judge: PASS")
        else:
            print("  Stress Judge: %s (%s) — предупреждение" % (stress_status, stress_fail_reason or "—"))
    else:
        print("  Stress Judge: не выполнен (нет данных/факторов)")
    print("")

    # --- Production workflow: RB corridor (quality gate), RC breaches, stress (warning-only). Only FAIL_DATA stops. ---
    rb_corridor_pp = getattr(cfg, "rb_corridor_pp", None)
    if rb_corridor_pp is None:
        rb_corridor_pp = RB_CORRIDOR_PP
    rb_ok, rb_violations_msgs = check_rb_corridor(
        actual_rc_block or {},
        cfg.rc_block_targets or {},
        corridor_pp=float(rb_corridor_pp),
    )
    rb_deltas_pp = _rb_deltas_pp(actual_rc_block or {}, cfg.rc_block_targets or {})

    # RC breaches: per-asset RC vs cap (from RiskPortfolio weights and cov)
    rc_breaches = []
    n_risk = len([t for t in weights_risk if weights_risk.get(t, 0) > 0 and t in cov_df.columns and t in cov_df.index])
    rb_growth = (cfg.rc_block_targets or {}).get("Growth", 1.0 / 3.0)
    rc_cap = resolve_rc_asset_cap(cfg.rc_asset_cap_pct, max(n_risk, 1), rb_growth)
    rc_by_asset = rc_by_asset_from_weights(weights_risk, cov_df)
    for t, rc_share in (rc_by_asset or {}).items():
        if rc_share > rc_cap + 1e-9:
            rc_breaches.append({
                "ticker": t,
                "rc_pct": round(float(rc_share) * 100.0, 2),
                "cap_pct": round(float(rc_cap) * 100.0, 2),
            })

    # Status: APPROVED | CANDIDATE_RB_BREACH | OK_FALLBACK (FAIL_DATA already exited)
    if not rb_ok:
        production_status = STATUS_CANDIDATE_RB_BREACH
    elif "OK_FALLBACK" in status or rc_breaches:
        production_status = STATUS_OK_FALLBACK
    else:
        production_status = STATUS_APPROVED

    violations = []
    if not rb_ok:
        violations.append({"code": VIOL_RB_BREACH, "details": rb_deltas_pp})
    if rc_breaches:
        violations.append({"code": VIOL_RC_ASSET_CAP, "details": rc_breaches})
    if stress_status == "FAIL_STRESS":
        violations.append({
            "code": VIOL_FAIL_STRESS,
            "details": {
                "fail_reason_code": stress_fail_reason,
                "worst_scenario_loss_pct": stress_report.get("worst_scenario_loss_pct"),
                "failed_scenario": stress_report.get("failed_scenario"),
            },
        })
    if max_dd_ok is False:
        violations.append({
            "code": VIOL_MAX_DD_BREACH,
            "details": {"target_max_drawdown_pct": cfg.target_max_drawdown_pct, "realized_exceeds_limit": True},
        })

    stress_summary = {
        "status": stress_status,
        "fail_reason_code": stress_fail_reason,
        "worst_scenario_loss_pct": stress_report.get("worst_scenario_loss_pct"),
        "failed_scenario": stress_report.get("failed_scenario"),
    }
    next_actions = _build_next_actions(violations, rb_deltas_pp, stress_report)

    run_result = {
        "weights": rounded,
        "status": production_status,
        "violations": violations,
        "rb_deltas_pp": rb_deltas_pp,
        "rc_breaches": rc_breaches,
        "stress_summary": stress_summary,
        "next_actions": next_actions,
    }

    # --- Baseline (sanity_check_baseline): diagnostic only, never used for allocation ---
    baseline_tickers = set(
        tickers_meeting_coverage(monthly_returns, analysis_end, window_months, coverage_threshold)
    )
    not_in_baseline = [t for t in risk_tickers if t not in baseline_tickers]
    if not_in_baseline:
        print("--- Baseline (sanity check, не для аллокации) ---")
        print(
            "  Тикеры не входят в baseline (coverage < %.0f%% в окне %d мес.): %s"
            % (coverage_threshold * 100, window_months, sorted(not_in_baseline))
        )
    baseline_blocks = {
        b: [t for t in tickers if t in baseline_tickers]
        for b, tickers in cfg.blocks.items()
    }
    risk_baseline = get_risk_portfolio_tickers(baseline_blocks)
    if risk_baseline:
        weights_baseline, status_baseline = run_risk_budget_optimization(
            monthly_returns,
            baseline_blocks,
            cfg.rc_block_targets,
            cfg.growth_core_candidates,
            rc_asset_cap_pct=cfg.rc_asset_cap_pct,
            min_single_security_weight_pct=cfg.min_single_security_weight_pct,
            max_single_security_weight_pct=cfg.max_single_security_weight_pct,
            window_months=window_months,
        )
        if weights_baseline:
            cols_b = [t for t in weights_baseline if t in monthly_returns.columns]
            ret_b = monthly_returns[cols_b].iloc[-window_months:].dropna(how="any")
            if len(ret_b) >= 2:
                cov_b = cov_matrix_monthly(ret_b, ddof=1)
                vol_b = portfolio_vol_annual(weights_baseline, cov_b)
                print("  Baseline: волатильность %.2f%% (для сравнения с Full: %.2f%%)" % (vol_b * 100, current_vol * 100))
        print("  Baseline используется только как диагностика; веса для покупки — только Full (выше).")
    elif not_in_baseline:
        print("  Baseline не рассчитан (нет достаточного числа тикеров с coverage >= %.0f%%)." % (coverage_threshold * 100))
    print("")

    # Write weights and snapshot to output_dir_final (ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ) — always (production: only FAIL_DATA stops)
    out_final = Path(getattr(cfg, "output_dir_final", "ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ"))
    out_final.mkdir(parents=True, exist_ok=True)
    weights_path = out_final / WEIGHTS_FILENAME
    with open(weights_path, "w", encoding="utf-8") as f:
        yaml.dump(rounded, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print("Веса записаны в %s." % weights_path)

    # Persist production run result (status, violations, next_actions)
    run_result_path = out_final / "run_result.json"
    with open(run_result_path, "w", encoding="utf-8") as f:
        json.dump(run_result, f, indent=2, default=str)
    print("Результат прогона: %s (status=%s)" % (run_result_path, production_status))

    # Final snapshot (one object, same print and save)
    cash_proxy = cfg.cash_proxy_ticker or "BIL"
    snapshot = build_snapshot(
        final_weights_total=final_weights,
        blocks=cfg.blocks,
        cash_proxy_ticker=cash_proxy,
        analysis_end=analysis_end_str,
        stress_report=stress_report,
        final_weights_risk_portfolio=weights_risk,
        monthly_returns=monthly_returns,
        window_months=window_months,
        target_vol_annual=target_vol,
        current_vol_annual=current_vol,
        max_dd_ok=max_dd_ok,
        rc_block_targets=cfg.rc_block_targets,
        rc_caps_ok=len(rc_breaches) == 0,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
    )
    print_snapshot(snapshot)
    save_snapshot(snapshot, out_final)
    print("Snapshot сохранён в %s" % (out_final / "snapshot.json"))

    # Полный отчёт (все CSV и четыре snapshot: assets, 3y, 5y, 10y) — run_report подхватит веса из portfolio_weights.yml
    report_cmd = [sys.executable, "run_report.py"]
    if args.no_cache:
        report_cmd.append("--no-cache")
    project_root = Path(__file__).resolve().parent
    subprocess.run(report_cmd, cwd=project_root, check=True)

    if args.write_config:
        config_path = Path(__file__).resolve().parent / "config.yml"
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        data["weights"] = rounded
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print("Веса также записаны в config.yml (weights).")


if __name__ == "__main__":
    main()
