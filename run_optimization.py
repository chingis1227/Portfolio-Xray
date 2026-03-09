"""
Run portfolio optimization (risk budget + ProLiquidity) and output weights.
Uses config.yml; client_profile (e.g. Growth) supplies rc_block_targets.
Run from project root: python run_optimization.py [--no-cache] [--write-config]

Output: final weights are written to portfolio_weights.yml. Use --write-config to also write them into config.yml (legacy).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

from src.config import load_validated_config, load_assets_metadata, resolve_cash_and_rf, WEIGHTS_FILENAME
from src.client_profiles import get_profile_defaults
from src.config_schema import ConfigValidationError
from src.data_loader import load_monthly_data_shared
from src.optimization import (
    get_risk_portfolio_tickers,
    run_risk_budget_optimization,
    proliquidity,
    portfolio_vol_annual,
)
from src.risk_contrib import cov_matrix_monthly
from src.snapshot import build_snapshot, print_snapshot, save_snapshot
from src.stress import run_stress
from src.utils import setup_logging, logger, tickers_meeting_coverage


def get_client_profile_from_config_file() -> str | None:
    """Read client_profile directly from config.yml so we always use the latest value from disk."""
    config_path = Path(__file__).resolve().parent / "config.yml"
    if not config_path.is_file():
        return None
    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        profile = data.get("client_profile")
        return profile.strip() if isinstance(profile, str) and profile else None
    except Exception:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portfolio optimization — risk budget + ProLiquidity")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cache, download fresh data")
    parser.add_argument("--write-config", action="store_true", help="Write optimized weights to config.yml")
    parser.add_argument("--profile", type=str, default=None, help="Override client_profile (e.g. Growth, conservative)")
    return parser.parse_args()


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

    # Apply profile: from --profile CLI, or from config.yml on disk (so we always see latest client_profile)
    # If config.yml has explicit rc_block_targets (manual override), keep them; else use profile.
    config_path = Path(__file__).resolve().parent / "config.yml"
    raw_rc_from_file = None
    if config_path.is_file():
        try:
            with open(config_path, encoding="utf-8") as f:
                raw_data = yaml.safe_load(f) or {}
            rbt = raw_data.get("rc_block_targets")
            if rbt and isinstance(rbt, dict) and len(rbt) >= 3:
                raw_rc_from_file = {k: float(v) for k, v in rbt.items() if isinstance(v, (int, float))}
                if raw_rc_from_file and abs(sum(raw_rc_from_file.values()) - 1.0) < 0.01:
                    cfg.rc_block_targets = raw_rc_from_file
        except Exception:
            pass
    profile_source = (get_client_profile_from_config_file() or cfg.client_profile or args.profile or "").strip()
    profile_display = profile_source or "—"
    if profile_source and raw_rc_from_file is None:
        defaults = get_profile_defaults(profile_source)
        if defaults:
            if defaults.get("target_vol_annual") is not None:
                cfg.target_vol_annual = defaults["target_vol_annual"]
            if defaults.get("rc_block_targets") is not None:
                cfg.rc_block_targets = dict(defaults["rc_block_targets"])
    if profile_source or cfg.rc_block_targets:
        logger.info("Профиль %s: target_vol=%.2f%%, rc_block_targets=%s", profile_display, (cfg.target_vol_annual or 0) * 100, cfg.rc_block_targets)

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
    window_months = cfg.windows_months[0] if cfg.windows_months else 60
    coverage_threshold = getattr(cfg, "coverage_threshold", 0.90) or 0.90

    # --- Full (policy_portfolio_full): all tickers, NaN-safe inner join in window; this is what we allocate ---
    weights_risk, status = run_risk_budget_optimization(
        monthly_returns,
        cfg.blocks,
        cfg.rc_block_targets,
        cfg.growth_core_candidates,
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
        window_months=window_months,
    )

    if not weights_risk:
        logger.error(f"Оптимизация не удалась: {status}")
        raise SystemExit(1)

    logger.info(f"RiskPortfolio: {status}")

    # Covariance for vol (same window, inner join as in Full optimization)
    cols = [t for t in weights_risk if t in monthly_returns.columns]
    ret_slice = monthly_returns[cols].iloc[-window_months:].dropna(how="any")
    cov_df = cov_matrix_monthly(ret_slice, ddof=1)
    current_vol = portfolio_vol_annual(weights_risk, cov_df)

    # ProLiquidity (with Alpha Shift when cash prohibited and vol > target)
    # Liquidity life floor amount = liquidity_need_months * monthly_expenses (single source of truth)
    pv = cfg.portfolio_value if cfg.portfolio_value is not None and cfg.portfolio_value > 0 else cfg.initial_investable_amount
    liquidity_amount = cfg.liquidity_need_months * (cfg.monthly_expenses or 0)
    liquidity_floor_pct = max(0.0, min(1.0, liquidity_amount / pv)) if pv > 0 else 0.0

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
        blocks=cfg.blocks,
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

    # Guardrails: Max DD and Stress Judge (per portfolio_construction_policy)
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
    print("--- Guardrails (mandate) ---")
    if max_dd_limit is not None:
        if max_dd_ok is True:
            print("  Max DD: PASS (портфель в пределах целевой просадки)")
        elif max_dd_ok is False:
            print("  Max DD: FAIL (реализованная просадка хуже целевой %.1f%%)" % (max_dd_limit * 100))
        else:
            print("  Max DD: не проверен (недостаточно данных)")
    else:
        print("  Max DD: не задан (target_max_drawdown_pct отсутствует)")
    if stress_status is not None:
        if stress_status == "PASS":
            print("  Stress Judge: PASS")
        else:
            print("  Stress Judge: %s (%s)" % (stress_status, stress_fail_reason or "—"))
    else:
        print("  Stress Judge: не выполнен (нет данных/факторов)")
    print("")

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

    # Always write weights to portfolio_weights.yml (used by run_report when config has no weights)
    weights_path = Path(__file__).resolve().parent / WEIGHTS_FILENAME
    with open(weights_path, "w", encoding="utf-8") as f:
        yaml.dump(rounded, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print("Веса записаны в %s." % weights_path.name)

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
        rc_caps_ok=True,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
    )
    print_snapshot(snapshot)
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    save_snapshot(snapshot, out_dir)
    print("Snapshot сохранён в %s" % (out_dir / "snapshot.json"))

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
