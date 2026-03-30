"""
Run portfolio optimization (risk budget + ProLiquidity) and output weights.
Uses config.yml; client_profile (e.g. Growth) supplies rc_block_targets.

**Primary RiskPortfolio (default):** two-stage optimization — see docs/two_stage_optimization.md
(stage1: risk_skeleton + RB search; stage2: max_return from skeleton + soft IPS).
Use ``--single-stage`` for the legacy single-pass optimizer.

Run from project root: python run_optimization.py [--no-cache] [--write-config] [--single-stage]

Output: final weights are written to portfolio_weights.yml. Use --write-config to also write them into config.yml (legacy).
"""
from __future__ import annotations

import argparse
import json
import re
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
from policy_math.feasibility import DEFAULT_RC_CAP_RB_K_MULTIPLIER, RC_CAP_MODE_GLOBAL
from src.optimization import (
    DEFAULT_RISK_SKELETON_CONCENTRATION_LAMBDA,
    OBJECTIVE_MODE_MAX_RETURN,
    OBJECTIVE_MODE_RISK_SKELETON,
    get_risk_portfolio_tickers,
    ticker_to_block_map,
    run_risk_budget_optimization,
    enforce_rc_caps_postprocess,
    proliquidity,
    portfolio_vol_annual,
    rc_by_block_from_weights,
    rc_by_asset_from_weights,
    check_rb_corridor,
    check_rb_achievement,
    RB_CORRIDOR_PP,
)
from src.risk_contrib import build_rc_cap_per_ticker, cov_matrix_monthly, resolve_rc_asset_cap
from src.metrics_asset import mandate_max_drawdown_full_history_check
from src.young_etfs_dual_cov import build_dual_covariance_and_mu, per_ticker_young_weight_caps
from src.robustness import compute_robustness_diagnostics
from src.snapshot import build_snapshot, print_snapshot, save_snapshot
from src.stress import run_stress
from src.utils import setup_logging, logger, tickers_meeting_coverage
from src.block_selection import apply_block_selection


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portfolio optimization — risk budget + ProLiquidity")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cache, download fresh data")
    parser.add_argument("--write-config", action="store_true", help="Write optimized weights to config.yml")
    parser.add_argument("--profile", type=str, default=None, help="Override client_profile (e.g. Growth, conservative)")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config YAML (default: config.yml in project root)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip run_report.py and PDF rebuild after optimization (scenario / isolated runs)",
    )
    parser.add_argument(
        "--single-stage",
        action="store_true",
        help="Legacy: one-pass RiskPortfolio (RB search + default max_return). Default is two-stage (see docs/two_stage_optimization.md).",
    )
    return parser.parse_args()


# Production workflow: status and violation codes
STATUS_APPROVED = "APPROVED"
STATUS_CANDIDATE_RB_BREACH = "CANDIDATE_RB_BREACH"
STATUS_OK_FALLBACK = "OK_FALLBACK"
STATUS_FAIL_DATA = "FAIL_DATA"
STATUS_FAIL_MAX_DD = "FAIL_MAX_DD"  # legacy alias; new runs use FAIL_MANDATE for historical MaxDD gate
STATUS_FAIL_MANDATE = "FAIL_MANDATE"
STATUS_FAIL_STRESS = "FAIL_STRESS"  # legacy; no longer blocks release
STATUS_FAIL_RC = "FAIL_RC"
STATUS_FAIL_FEASIBILITY = "FAIL_FEASIBILITY"

VIOL_RB_BREACH = "RB_BREACH"
VIOL_MAX_DD_GATE = "MAX_DD_GATE"
VIOL_RC_VIOLATION = "RC_VIOLATION"
VIOL_RC_ASSET_CAP = "VIOL_RC_ASSET_CAP"
VIOL_FAIL_STRESS = "FAIL_STRESS"  # legacy violation label; stress is diagnostic-only
VIOL_FAIL_MANDATE = "FAIL_MANDATE"
VIOL_MAX_DD_BREACH = "MAX_DD_BREACH"
WARN_MODEL_RISK_YOUNG_WEIGHT = "WARN_MODEL_RISK_YOUNG_WEIGHT"

# Stage-2 warm start: tracking penalty vs skeleton weights (same order of magnitude as research script)
_TWO_STAGE_SKEL_TRACK_LAMBDA = 10.0


def _parse_rb_target_used(status: str) -> dict[str, float] | None:
    """Parse RB_TARGET_USED: g/d/i from optimization status (after RB search)."""
    m = re.search(r"RB_TARGET_USED:\s*([\d.]+)/([\d.]+)/([\d.]+)", status)
    if not m:
        return None
    g, d, i = float(m.group(1)), float(m.group(2)), float(m.group(3))
    s = g + d + i
    if s <= 1e-12:
        return None
    return {"Growth": g / s, "Duration": d / s, "Inflation": i / s}


def _apply_tail_overlay(
    final_weights: dict[str, float],
    cfg,
    blocks: dict[str, list[str]],
) -> None:
    """
    After ProLiquidity: reserve tail_target_weight_pct for Tail-block tickers (e.g. VIXY);
    scale all other weights proportionally so weights sum to 1.
    """
    tw = getattr(cfg, "tail_target_weight_pct", None)
    if tw is None or float(tw) <= 0:
        return
    tail_tickers = [t for t in (blocks.get("Tail") or []) if t in cfg.tickers]
    if not tail_tickers:
        return
    tw = float(min(max(float(tw), 0.0), 0.25))
    others_sum = sum(w for t, w in final_weights.items() if t not in tail_tickers)
    if others_sum <= 1e-15:
        return
    scale = (1.0 - tw) / others_sum
    for t in list(final_weights.keys()):
        if t not in tail_tickers:
            final_weights[t] = final_weights.get(t, 0.0) * scale
    share = tw / len(tail_tickers)
    for t in tail_tickers:
        final_weights[t] = share
    logger.info(
        "Tail overlay: target=%.2f%% split across %s",
        tw * 100.0,
        tail_tickers,
    )


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
            "Stress diagnostic (DIAG_*): review liquidity, duration, growth/HY — informational only."
        )
    if VIOL_FAIL_MANDATE in codes:
        actions.append(
            "Mandate: historical max drawdown exceeds client limit on full overlapping sample; reduce risk or adjust mandate."
        )
    if VIOL_MAX_DD_BREACH in codes:
        actions.append(
            "Realized max drawdown exceeds mandate; consider reducing risk (target_vol, growth share) or liquidity."
        )
    if VIOL_MAX_DD_GATE in codes:
        actions.append(
            "MaxDD / mandate gate: historical drawdown exceeded limit; weights not written. "
            "Adjust target_max_drawdown_pct, risk budget, or universe and re-run."
        )
    if VIOL_RC_VIOLATION in codes:
        actions.append(
            "RC post-processing could not satisfy RC caps (strict mode: weights not written; permissive: violation flagged). "
            "Relax rc_asset_cap_pct, add assets, or set rc_policy_mode: permissive to write weights with violation."
        )
    if WARN_MODEL_RISK_YOUNG_WEIGHT in codes:
        actions.append(
            "Суммарный вес candidate/new активов превышает порог young_etf_optimization_policy.aggregate_candidate_new_warn_pct: "
            "повышенная неопределённость оценки риска; рассмотреть снижение доли молодых ETF или отключение dual-cov."
        )
    return actions


def _extract_rb_target_selection(status_text: str) -> dict | None:
    """
    Parse optimization status text and extract RB target selection metadata.
    Expected markers in status: "RB_TARGET_SOURCE: <stage>" and
    "RB_TARGET_USED: <growth>/<duration>/<inflation>".
    """
    if not status_text:
        return None
    source_match = re.search(r"RB_TARGET_SOURCE:\s*([A-Za-z_]+)", status_text)
    used_match = re.search(
        r"RB_TARGET_USED:\s*([0-9]*\.?[0-9]+)\/([0-9]*\.?[0-9]+)\/([0-9]*\.?[0-9]+)",
        status_text,
    )
    if not source_match and not used_match:
        return None
    out: dict[str, object] = {}
    if source_match:
        out["stage"] = source_match.group(1).strip().lower()
    if used_match:
        out["target"] = {
            "Growth": round(float(used_match.group(1)), 4),
            "Duration": round(float(used_match.group(2)), 4),
            "Inflation": round(float(used_match.group(3)), 4),
        }
    return out or None


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
        cfg_path = Path(args.config).resolve() if args.config else None
        cfg = load_validated_config(cfg_path)
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
        logger.warning(
            "Block selection FAIL_FEASIBILITY: %s — продолжаем с блоками как есть (без internal weights).",
            block_result.get("reason", ""),
        )
    blocks_for_optimization = block_result.get("blocks", cfg.blocks)
    duration_internal_weights = block_result.get("duration_internal_weights") if block_result.get("status") == "OK" else None
    inflation_internal_weights = block_result.get("inflation_internal_weights") if block_result.get("status") == "OK" else None
    if duration_internal_weights:
        logger.info("Duration block selection: internal_weights=%s", duration_internal_weights)
    if inflation_internal_weights:
        logger.info("Inflation block selection: internal_weights=%s", inflation_internal_weights)

    # Feasibility check before optimization: if RB is structurally unachievable, do not run optimizer or write weights
    risk_tickers_opt = get_risk_portfolio_tickers(blocks_for_optimization)
    n_total = len(risk_tickers_opt)
    rb_growth = (cfg.rc_block_targets or {}).get("Growth", 1.0 / 3.0)
    rb_norm = sum((cfg.rc_block_targets or {}).get(b, 0.0) for b in ("Growth", "Duration", "Inflation")) or 1.0
    if rb_norm > 0:
        rb_growth = (cfg.rc_block_targets or {}).get("Growth", 1.0 / 3.0) / rb_norm
    rc_cap_feas = resolve_rc_asset_cap(cfg.rc_asset_cap_pct, max(n_total, 1), rb_growth)
    feas_ok, feas_err = check_rb_achievement(
        blocks_for_optimization,
        cfg.rc_block_targets or {},
        rc_cap_feas,
        cfg.growth_core_candidates,
        n_total,
        rb_growth,
        rc_cap_mode=getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
        rc_cap_rb_k_multiplier=float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
    )
    if not feas_ok:
        out_final = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
        out_final.mkdir(parents=True, exist_ok=True)
        fail_result = {
            "weights": {},
            "status": STATUS_FAIL_FEASIBILITY,
            "violations": [{"code": "FEASIBILITY", "details": feas_err}],
            "rb_deltas_pp": {},
            "rc_breaches": [],
            "stress_summary": {},
            "next_actions": [
                "Add instruments to the offending block(s) or relax risk budget (rc_block_targets).",
                "Check docs/docs/feasibility_constraints_spec.md for RB achievability rules.",
            ],
        }
        if hasattr(cfg, "get_resolved_config"):
            fail_result["resolved_config"] = cfg.get_resolved_config()
        run_result_path = out_final / "run_result.json"
        with open(run_result_path, "w", encoding="utf-8") as f:
            json.dump(fail_result, f, indent=2, default=str)
        logger.error("Feasibility check failed: %s. Weights not written.", feas_err)
        print("")
        print("--- Feasibility gate: веса НЕ записаны ---")
        print("  %s" % feas_err)
        print("  См. %s (status=%s)." % (run_result_path, STATUS_FAIL_FEASIBILITY))
        raise SystemExit(1)

    # Primary window: dual covariance (young ETFs) or legacy full inner join
    cols_primary = [t for t in risk_tickers_opt if t in monthly_returns.columns]
    if not cols_primary:
        logger.error("FAIL_DATA: no risk tickers with returns in primary window")
        raise SystemExit(1)
    use_shrinkage = getattr(cfg, "covariance_shrinkage", False)
    young_pol = getattr(cfg, "young_etf_optimization_policy", None) or {}
    dual_enabled = bool(young_pol.get("enabled", True))
    young_diagnostics: dict | None = None
    per_ticker_young_caps: dict[str, float] | None = None
    mu_series_primary: pd.Series | None = None
    ret_primary: pd.DataFrame

    if dual_enabled:
        ticker_to_rb = ticker_to_block_map(blocks_for_optimization)
        cov_df, mu_series_primary, young_diagnostics = build_dual_covariance_and_mu(
            monthly_returns,
            cols_primary,
            ticker_to_rb,
            window_months,
            young_pol,
            use_shrinkage_on_core=use_shrinkage,
        )
        cols_primary = list(cov_df.columns)
        per_ticker_young_caps = per_ticker_young_weight_caps(
            young_diagnostics["tickers"],
            float(young_pol.get("max_weight_candidate_or_new_pct", 0.02)),
        )
        if not per_ticker_young_caps:
            per_ticker_young_caps = None
        ret_primary = monthly_returns[cols_primary].iloc[-window_months:]
        logger.info(
            "Young-ETF optimization: mode=%s, eligible=%s",
            young_diagnostics.get("mode"),
            young_diagnostics.get("eligible_tickers"),
        )
    else:
        MIN_FULL_JOIN_MONTHS = 11
        ret_primary = monthly_returns[cols_primary].iloc[-window_months:].dropna(axis=1, how="all").dropna(how="any")
        if len(ret_primary) < MIN_FULL_JOIN_MONTHS:
            lookback = min(monthly_returns.shape[0], max(window_months * 2, 120))
            ret_primary = monthly_returns[cols_primary].iloc[-lookback:].dropna(axis=1, how="all").dropna(how="any")
            if len(ret_primary) >= MIN_FULL_JOIN_MONTHS:
                ret_primary = ret_primary.iloc[-min(window_months, len(ret_primary)):]
        cols_primary = list(ret_primary.columns)
        if not cols_primary:
            logger.error("FAIL_DATA: no risk tickers with returns in primary window")
            raise SystemExit(1)
        cov_df = cov_matrix_monthly(ret_primary, ddof=1, use_shrinkage=use_shrinkage)

    # --- A) Primary optimization (10Y by default): this is the final portfolio ---
    rc_pen_lam = float(getattr(cfg, "rc_cap_penalty_lambda", 25.0))
    skel_conc = float(getattr(cfg, "risk_skeleton_concentration_lambda", DEFAULT_RISK_SKELETON_CONCENTRATION_LAMBDA))
    if skel_conc < 0:
        skel_conc = 0.0

    if not args.single_stage:
        logger.info("Primary optimization: TWO-STAGE (risk_skeleton -> max_return + soft IPS)")
        w_sk, st_sk = run_risk_budget_optimization(
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
            returns_window=None if dual_enabled else ret_primary,
            use_shrinkage=use_shrinkage,
            rb_target_ranges=getattr(cfg, "rc_block_target_ranges", None),
            cov_precomputed=cov_df if dual_enabled else None,
            mu_precomputed=mu_series_primary if dual_enabled else None,
            per_ticker_max_weight=per_ticker_young_caps,
            rc_cap_mode=getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
            rc_cap_rb_k_multiplier=float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
            rc_cap_penalty_lambda=rc_pen_lam,
            objective_mode=OBJECTIVE_MODE_RISK_SKELETON,
            risk_skeleton_concentration_lambda=skel_conc,
        )
        if not w_sk:
            logger.error("Two-stage stage1 (skeleton) failed: %s", st_sk)
            raise SystemExit(1)
        logger.info("Two-stage stage1: %s", st_sk)
        rb_eff = _parse_rb_target_used(st_sk) or (cfg.rc_block_targets or {})
        vol_lam = float(getattr(cfg, "optimization_soft_vol_penalty_lambda", 0.0) or 0.0)
        ret_lam = float(getattr(cfg, "optimization_soft_return_penalty_lambda", 0.0) or 0.0)
        if vol_lam <= 0:
            vol_lam = 12.0
        if ret_lam <= 0:
            ret_lam = 8.0
        tv = getattr(cfg, "target_vol_annual", None)
        tr = getattr(cfg, "target_nominal_return_annual", None)
        weights_risk, status = run_risk_budget_optimization(
            monthly_returns,
            blocks_for_optimization,
            rb_eff,
            cfg.growth_core_candidates,
            rc_asset_cap_pct=cfg.rc_asset_cap_pct,
            min_single_security_weight_pct=cfg.min_single_security_weight_pct,
            max_single_security_weight_pct=cfg.max_single_security_weight_pct,
            window_months=window_months,
            duration_internal_weights=duration_internal_weights,
            inflation_internal_weights=inflation_internal_weights,
            returns_window=None if dual_enabled else ret_primary,
            use_shrinkage=use_shrinkage,
            rb_target_ranges=None,
            rb_search_enabled=False,
            cov_precomputed=cov_df if dual_enabled else None,
            mu_precomputed=mu_series_primary if dual_enabled else None,
            per_ticker_max_weight=per_ticker_young_caps,
            rc_cap_mode=getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
            rc_cap_rb_k_multiplier=float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
            rc_cap_penalty_lambda=rc_pen_lam,
            objective_mode=OBJECTIVE_MODE_MAX_RETURN,
            warm_start_weights=w_sk,
            skeleton_tracking_lambda=_TWO_STAGE_SKEL_TRACK_LAMBDA,
            soft_target_vol_annual=float(tv) if tv is not None else None,
            soft_vol_penalty_lambda=vol_lam,
            soft_target_return_annual=float(tr) if tr is not None else None,
            soft_return_penalty_lambda=ret_lam,
            risk_skeleton_concentration_lambda=skel_conc,
        )
        if not weights_risk:
            logger.error("Two-stage stage2 failed: %s", status)
            raise SystemExit(1)
        logger.info("Two-stage stage2: %s", status)
    else:
        logger.info("Primary optimization: SINGLE-STAGE (legacy: RB search + max_return)")
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
            returns_window=None if dual_enabled else ret_primary,
            use_shrinkage=use_shrinkage,
            rb_target_ranges=getattr(cfg, "rc_block_target_ranges", None),
            cov_precomputed=cov_df if dual_enabled else None,
            mu_precomputed=mu_series_primary if dual_enabled else None,
            per_ticker_max_weight=per_ticker_young_caps,
            rc_cap_mode=getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
            rc_cap_rb_k_multiplier=float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
            rc_cap_penalty_lambda=rc_pen_lam,
        )

    if not weights_risk:
        logger.error(f"Оптимизация не удалась: {status}")
        raise SystemExit(1)

    logger.info(f"RiskPortfolio (primary %d мес.): {status}", window_months)

    # Primary window already built above (ret_primary, cov_df)
    if dual_enabled and young_diagnostics:
        effective_months_10y = int(young_diagnostics.get("core_effective_months", len(ret_primary)))
    else:
        effective_months_10y = len(ret_primary)
    if effective_months_10y < min_effective_months:
        logger.warning(
            "Primary window: effective months in risk core = %d (< %d). Robustness may flag FLAG_SHORT_SAMPLE.",
            effective_months_10y,
            min_effective_months,
        )
    # --- RC post-processing (Option B): enforce RC caps iteratively; strict = no write if unresolved ---
    risk_tickers_opt = get_risk_portfolio_tickers(blocks_for_optimization)
    n_risk = len(cols_primary)
    rb_growth = (cfg.rc_block_targets or {}).get("Growth", 1.0 / 3.0)
    rc_cap_resolved = resolve_rc_asset_cap(cfg.rc_asset_cap_pct, max(n_risk, 1), rb_growth)
    cap_by_ticker = build_rc_cap_per_ticker(
        blocks_for_optimization,
        cfg.rc_block_targets,
        cfg.rc_asset_cap_pct,
        getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
        float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
        max(n_risk, 1),
    )
    min_weight_rc = (
        float(cfg.min_single_security_weight_pct)
        if (cfg.min_single_security_weight_pct is not None and cfg.min_single_security_weight_pct > 0)
        else 0.01
    )
    adjusted_risk, rc_postprocess_ok, rc_postprocess_diag = enforce_rc_caps_postprocess(
        weights_risk,
        cov_df,
        blocks_for_optimization,
        cfg.growth_core_candidates,
        rc_cap_resolved,
        min_weight_rc,
        cfg.max_single_security_weight_pct,
        rb_growth,
        risk_tickers_opt,
        per_ticker_max_weight=per_ticker_young_caps,
        rc_cap_by_ticker=cap_by_ticker,
    )
    rc_policy_mode = getattr(cfg, "rc_policy_mode", "strict")
    if not rc_postprocess_ok and rc_policy_mode == "strict":
        out_final = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
        out_final.mkdir(parents=True, exist_ok=True)
        fail_violations = [{"code": VIOL_RC_VIOLATION, "details": rc_postprocess_diag}]
        fail_result = {
            "weights": {},
            "status": STATUS_FAIL_RC,
            "violations": fail_violations,
            "rb_deltas_pp": {},
            "rc_breaches": [],
            "stress_summary": {},
            "next_actions": _build_next_actions(fail_violations, {}, None),
        }
        try:
            fail_result["resolved_config"] = cfg.get_resolved_config()
        except Exception:
            fail_result["resolved_config"] = None
        run_result_path = out_final / "run_result.json"
        with open(run_result_path, "w", encoding="utf-8") as f:
            json.dump(fail_result, f, indent=2, default=str)
        logger.error(
            "RC post-processing could not satisfy RC caps (rc_policy_mode=strict). Weights not written. Diagnostics: %s",
            rc_postprocess_diag,
        )
        print("")
        print("--- RC gate (strict): веса НЕ записаны ---")
        print("  RC caps не достигнуты после итеративного перераспределения.")
        print("  См. %s (status=%s)." % (run_result_path, STATUS_FAIL_RC))
        raise SystemExit(1)
    weights_risk = adjusted_risk
    rc_violation_after_postprocess = not rc_postprocess_ok
    if rc_postprocess_ok:
        logger.info(
            "RC post-processing: все активы в пределах RC cap (mode=%s)",
            getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
        )
    elif rc_policy_mode == "permissive":
        logger.warning(
            "RC post-processing: нарушение RC cap сохранено (permissive). Диагностика: %s",
            rc_postprocess_diag,
        )

    mu_10y = mu_series_primary if dual_enabled and mu_series_primary is not None else ret_primary.mean()
    actual_rc_block = rc_by_block_from_weights(weights_risk, cov_df, blocks_for_optimization)
    if actual_rc_block and cfg.rc_block_targets:
        logger.info(
            "RC по блокам на основном окне (%d мес.): %s",
            window_months,
            actual_rc_block,
        )
    current_vol = portfolio_vol_annual(weights_risk, cov_df)

    young_agg_warn_details: dict | None = None
    if dual_enabled and young_diagnostics and weights_risk:
        warn_pct_y = float(young_pol.get("aggregate_candidate_new_warn_pct", 0.10))
        young_set = {
            t for t, m in young_diagnostics["tickers"].items()
            if m.get("bucket") in ("candidate", "new")
        }
        young_w_sum = sum(float(weights_risk.get(t, 0.0)) for t in young_set)
        if young_w_sum > warn_pct_y + 1e-12:
            young_agg_warn_details = {
                "aggregate_weight": round(young_w_sum, 4),
                "threshold": round(warn_pct_y, 4),
                "tickers": sorted(young_set),
            }

    # --- B) Secondary optimization (5Y) and robustness diagnostics ---
    robustness_report = None
    cov_5y_pre: pd.DataFrame | None = None
    mu_5y_pre: pd.Series | None = None
    diag_5y: dict | None = None
    if dual_enabled:
        ticker_to_rb_5 = ticker_to_block_map(blocks_for_optimization)
        cov_5y_pre, mu_5y_pre, diag_5y = build_dual_covariance_and_mu(
            monthly_returns,
            cols_primary,
            ticker_to_rb_5,
            secondary_window_months,
            young_pol,
            use_shrinkage_on_core=use_shrinkage,
        )
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
            use_shrinkage=use_shrinkage,
            rb_target_ranges=getattr(cfg, "rc_block_target_ranges", None),
            cov_precomputed=cov_5y_pre if dual_enabled else None,
            mu_precomputed=mu_5y_pre if dual_enabled else None,
            per_ticker_max_weight=per_ticker_young_caps,
            rc_cap_mode=getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
            rc_cap_rb_k_multiplier=float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
            rc_cap_penalty_lambda=float(getattr(cfg, "rc_cap_penalty_lambda", 25.0)),
        )
        cols_5y = [t for t in (weights_5y_risk or weights_risk) if t in monthly_returns.columns]
        ret_5y = monthly_returns[cols_5y].iloc[-secondary_window_months:].dropna(how="any")
        effective_months_5y = len(ret_5y)
        if not dual_enabled and effective_months_5y < min_effective_months:
            logger.warning(
                "Secondary window: effective months after inner join = %d (< %d).",
                effective_months_5y,
                min_effective_months,
            )
        if dual_enabled and diag_5y is not None:
            effective_months_5y = int(diag_5y.get("core_effective_months", 0))
        cov_5y: pd.DataFrame | None = None
        mu_5y: pd.Series | None = None
        if weights_5y_risk and dual_enabled and cov_5y_pre is not None:
            cov_5y = cov_5y_pre
            mu_5y = mu_5y_pre
        elif weights_5y_risk and len(ret_5y) >= 2:
            cov_5y = cov_matrix_monthly(ret_5y, ddof=1, use_shrinkage=use_shrinkage)
            mu_5y = ret_5y.mean()
        if weights_5y_risk and cov_5y is not None and mu_5y is not None and len(mu_5y):
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
                "final_portfolio_is_10y": True,
            }
            logger.info("Dual-horizon: 10Y vs 5Y comparison written to robustness_report.json")
            # Persist for report (ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ)
            out_final = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
            out_final.mkdir(parents=True, exist_ok=True)
            with open(out_final / "robustness_report.json", "w", encoding="utf-8") as f:
                json.dump(robustness_report, f, indent=2)
        elif weights_5y_risk:
            logger.warning("Secondary optimization succeeded but 5Y robustness inputs missing; robustness report skipped.")

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

    _apply_tail_overlay(final_weights, cfg, blocks_for_optimization)

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

    # Mandate: full-history MaxDD (blocking). Stress suite: diagnostic only (DIAG_*).
    max_dd_limit = abs(cfg.target_max_drawdown_pct) if cfg.target_max_drawdown_pct is not None else None
    mandate_check = mandate_max_drawdown_full_history_check(monthly_returns, final_weights, max_dd_limit)
    max_dd_ok = mandate_check.get("pass")
    stress_status = None
    stress_fail_reason = None

    asset_betas_df = pd.DataFrame()
    portfolio_betas_dict = {}
    portfolio_betas_5y_dict = {}
    portfolio_betas_10y_dict = {}
    try:
        from src.stress_factors import (
            FACTOR_WEEKS_10Y,
            FACTOR_WEEKS_5Y,
            compute_asset_factor_betas_weekly,
            portfolio_factor_regression_weekly,
            portfolio_factor_betas,
        )

        beta_tickers = [t for t in cfg.tickers if final_weights.get(t, 0) > 0]
        if not beta_tickers:
            beta_tickers = list(cfg.tickers)

        def _portfolio_betas_weekly(window_weeks: int) -> tuple[pd.DataFrame, dict]:
            asset_betas_win = compute_asset_factor_betas_weekly(
                beta_tickers,
                analysis_end_str,
                window_weeks,
            )
            return asset_betas_win, portfolio_factor_betas(final_weights, asset_betas_win)

        # Factor betas: weekly regression, ~5Y and ~10Y windows (see stress_factors.FACTOR_WEEKS_*).
        asset_betas_5y_df, portfolio_betas_5y_dict = _portfolio_betas_weekly(FACTOR_WEEKS_5Y)
        _asset_betas_10y_df, portfolio_betas_10y_dict = _portfolio_betas_weekly(FACTOR_WEEKS_10Y)

        # Keep run_stress input/backward compatibility on factor_betas using 5Y.
        asset_betas_df = asset_betas_5y_df
        portfolio_betas_dict = portfolio_betas_5y_dict
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
        rc_cap_mode=getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
        rc_cap_rb_k_multiplier=float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
        rc_block_targets=cfg.rc_block_targets,
    )
    # Expose requested horizons explicitly in stress report.
    stress_report["factor_betas_5y"] = {k: round(v, 4) for k, v in (portfolio_betas_5y_dict or {}).items()}
    stress_report["factor_betas_10y"] = {k: round(v, 4) for k, v in (portfolio_betas_10y_dict or {}).items()}
    # Keep legacy field aligned with 5Y window.
    stress_report["factor_betas"] = dict(stress_report["factor_betas_5y"])
    # Portfolio factor regression diagnostics (5Y/10Y): t/p/CI/R^2 on weekly data, same factor matrix definition.
    stress_report["factor_regression_5y"] = {}
    stress_report["factor_regression_10y"] = {}
    try:
        stress_report["factor_regression_5y"] = portfolio_factor_regression_weekly(
            weights=final_weights,
            tickers=cfg.tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_5Y,
        )
    except Exception as e:
        stress_report["factor_regression_5y_error"] = str(e)
        logger.warning(f"Factor regression diagnostics (5Y) failed: {e}")
    try:
        stress_report["factor_regression_10y"] = portfolio_factor_regression_weekly(
            weights=final_weights,
            tickers=cfg.tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=FACTOR_WEEKS_10Y,
        )
    except Exception as e:
        stress_report["factor_regression_10y_error"] = str(e)
        logger.warning(f"Factor regression diagnostics (10Y) failed: {e}")
    stress_status = stress_report.get("status")
    stress_fail_reason = stress_report.get("fail_reason_code") or stress_report.get("skip_reason")

    print("")
    print("--- Guardrails (мандат: MaxDD по полной истории; стресс: только диагностика) ---")
    if max_dd_limit is not None:
        if max_dd_ok is True:
            print(
                "  Мандат MaxDD: PASS (полная пересекающаяся история: %s мес., %s .. %s)"
                % (
                    mandate_check.get("months_used", 0),
                    mandate_check.get("history_start") or "—",
                    mandate_check.get("history_end") or "—",
                )
            )
        elif max_dd_ok is False:
            mddr = mandate_check.get("max_drawdown_realized")
            print(
                "  Мандат MaxDD: FAIL (реализованная просадка %.2f%% vs лимит %.1f%%) — веса не будут записаны"
                % ((mddr or 0) * 100, max_dd_limit * 100)
            )
        else:
            print("  Мандат MaxDD: не проверен (недостаточно пересекающихся данных)")
    else:
        print("  Мандат MaxDD: не задан (target_max_drawdown_pct отсутствует)")
    if stress_status is not None:
        if stress_status in ("DIAG_PASS", "PASS"):
            print("  Стресс (диагностика): %s" % stress_status)
        else:
            print(
                "  Стресс (диагностика, не блокирует выпуск): %s (%s)"
                % (stress_status, stress_fail_reason or stress_report.get("primary_diagnostic_code") or "—")
            )
    else:
        print("  Стресс (диагностика): не выполнен (нет данных/факторов)")
    if young_agg_warn_details:
        print(
            "  Young ETF (модельный риск): суммарный вес candidate/new %.2f%% > порога %.2f%% — см. run_result.json (%s)"
            % (
                young_agg_warn_details["aggregate_weight"] * 100,
                young_agg_warn_details["threshold"] * 100,
                WARN_MODEL_RISK_YOUNG_WEIGHT,
            )
        )
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
    rc_by_asset = rc_by_asset_from_weights(weights_risk, cov_df)
    for t, rc_share in (rc_by_asset or {}).items():
        cap_t = float(cap_by_ticker.get(t, rc_cap_resolved))
        if rc_share > cap_t + 1e-9:
            rc_breaches.append({
                "ticker": t,
                "rc_pct": round(float(rc_share) * 100.0, 2),
                "cap_pct": round(cap_t * 100.0, 2),
            })

    # Status: APPROVED | CANDIDATE_RB_BREACH | OK_FALLBACK (FAIL_DATA/FAIL_RC already exited)
    if not rb_ok:
        production_status = STATUS_CANDIDATE_RB_BREACH
    elif "OK_FALLBACK" in status or rc_breaches or rc_violation_after_postprocess:
        production_status = STATUS_OK_FALLBACK
    else:
        production_status = STATUS_APPROVED

    violations = []
    if rc_violation_after_postprocess:
        violations.append({
            "code": VIOL_RC_VIOLATION,
            "details": rc_postprocess_diag,
        })
    if not rb_ok:
        violations.append({"code": VIOL_RB_BREACH, "details": rb_deltas_pp})
    if rc_breaches:
        violations.append({"code": VIOL_RC_ASSET_CAP, "details": rc_breaches})
    if young_agg_warn_details:
        violations.append({
            "code": WARN_MODEL_RISK_YOUNG_WEIGHT,
            "details": young_agg_warn_details,
        })
    if stress_status == "DIAG_ATTENTION":
        violations.append({
            "code": VIOL_FAIL_STRESS,
            "details": {
                "note": "diagnostic_only",
                "diagnostic_codes": stress_report.get("diagnostic_codes", []),
                "primary_diagnostic_code": stress_report.get("primary_diagnostic_code"),
                "worst_scenario_loss_pct": stress_report.get("worst_scenario_loss_pct"),
                "failed_scenario": stress_report.get("failed_scenario"),
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
                    "target_max_drawdown_pct": cfg.target_max_drawdown_pct,
                    "reason": "insufficient_overlapping_history",
                    "months_used": mandate_check.get("months_used", 0),
                },
            })

    stress_worst_pct = stress_report.get("worst_scenario_loss_pct")
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
        "worst_scenario_loss_pct": stress_worst_pct,
        "failed_scenario": stress_report.get("failed_scenario"),
    }
    next_actions = _build_next_actions(violations, rb_deltas_pp, stress_report)

    if not mandate_gate_passed:
        production_status = STATUS_FAIL_MANDATE

    strict_stress_gate = getattr(cfg, "strict_stress_gate", False)
    if strict_stress_gate:
        logger.warning(
            "strict_stress_gate is deprecated: stress is diagnostic-only (DIAG_*) and never blocks release."
        )

    write_weights_gate = mandate_gate_passed
    run_result = {
        "weights": rounded if write_weights_gate else {},
        "status": production_status,
        "mandate_check": mandate_check,
        "rb_target_selection": _extract_rb_target_selection(status),
        "violations": violations,
        "rb_deltas_pp": rb_deltas_pp,
        "rc_breaches": rc_breaches,
        "stress_summary": stress_summary,
        "stress_diagnostic_report": stress_report,
        "next_actions": next_actions,
        "actual_rc_block": {k: round(v, 4) for k, v in (actual_rc_block or {}).items()},
        "rc_block_targets": cfg.rc_block_targets,
        "young_etf_dual_cov_enabled": dual_enabled,
        "young_etf_diagnostics": young_diagnostics,
        "young_etf_aggregate_weight_warn": young_agg_warn_details,
    }
    try:
        run_result["resolved_config"] = cfg.get_resolved_config()
    except Exception:
        run_result["resolved_config"] = None

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
            use_shrinkage=use_shrinkage,
            rb_target_ranges=getattr(cfg, "rc_block_target_ranges", None),
            rc_cap_mode=getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
            rc_cap_rb_k_multiplier=float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
            rc_cap_penalty_lambda=float(getattr(cfg, "rc_cap_penalty_lambda", 25.0)),
        )
        if weights_baseline:
            cols_b = [t for t in weights_baseline if t in monthly_returns.columns]
            ret_b = monthly_returns[cols_b].iloc[-window_months:].dropna(how="any")
            if len(ret_b) >= 2:
                cov_b = cov_matrix_monthly(ret_b, ddof=1, use_shrinkage=use_shrinkage)
                vol_b = portfolio_vol_annual(weights_baseline, cov_b)
                print("  Baseline: волатильность %.2f%% (для сравнения с Full: %.2f%%)" % (vol_b * 100, current_vol * 100))
        print("  Baseline используется только как диагностика; веса для покупки — только Full (выше).")
    elif not_in_baseline:
        print("  Baseline не рассчитан (нет достаточного числа тикеров с coverage >= %.0f%%)." % (coverage_threshold * 100))
    print("")

    out_final = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
    out_final.mkdir(parents=True, exist_ok=True)
    run_result_path = out_final / "run_result.json"
    with open(run_result_path, "w", encoding="utf-8") as f:
        json.dump(run_result, f, indent=2, default=str)
    print("Результат прогона: %s (status=%s)" % (run_result_path, production_status))

    from src.io_export import generate_ips_summary
    generate_ips_summary(cfg, run_result, out_final / "ips_summary.txt")

    if not mandate_gate_passed:
        logger.error(
            "Mandate gate: historical max drawdown check failed or inconclusive. Weights not written. mandate_check=%s",
            mandate_check,
        )
        print("")
        print("--- Мандат MaxDD: веса НЕ записаны (FAIL_MANDATE) ---")
        print("  Целевая просадка: %.1f%%" % ((max_dd_limit or 0) * 100))
        if mandate_check.get("max_drawdown_realized") is not None:
            print("  Реализованная MaxDD на полной истории: %.2f%%" % (mandate_check["max_drawdown_realized"] * 100))
        if mandate_check.get("history_start"):
            print("  Период: %s .. %s (%s мес.)" % (
                mandate_check.get("history_start"),
                mandate_check.get("history_end"),
                mandate_check.get("months_used"),
            ))
        print("  См. %s (status=%s)." % (run_result_path, STATUS_FAIL_MANDATE))
        raise SystemExit(1)

    # Write weights and snapshot (only when mandate MaxDD gate passed)
    weights_path = out_final / WEIGHTS_FILENAME
    with open(weights_path, "w", encoding="utf-8") as f:
        yaml.dump(rounded, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print("Веса записаны в %s." % weights_path)

    # Final snapshot (one object, same print and save)
    cash_proxy = cfg.cash_proxy_ticker or "BIL"
    try:
        _resolved_config = cfg.get_resolved_config()
    except Exception:
        _resolved_config = None
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
        resolved_config=_resolved_config,
    )
    print_snapshot(snapshot)
    save_snapshot(snapshot, out_final)
    print("Snapshot сохранён в %s" % (out_final / "snapshot.json"))

    # Full report (CSV and snapshots). Weights and run_result are already written; report must not block.
    project_root = Path(__file__).resolve().parent
    if not args.no_report:
        report_cmd = [sys.executable, "run_report.py"]
        if args.no_cache:
            report_cmd.append("--no-cache")
        try:
            subprocess.run(report_cmd, cwd=project_root, check=True)
        except subprocess.CalledProcessError as e:
            logger.warning("Report failed (exit %s). Weights and run_result were saved. %s", e.returncode, e)
            print("")
            print("Report failed, weights saved. See log for details.")
            try:
                from src.pdf_reports import try_rebuild_pdfs_after_main_report

                try_rebuild_pdfs_after_main_report(logger=logger)
            except Exception as ex:
                logger.warning("PDF suite rebuild skipped: %s", ex)
    else:
        logger.info("Skipping run_report.py (--no-report).")

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
