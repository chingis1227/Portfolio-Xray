from __future__ import annotations
"""
Build **minimum_variance_advanced_controls** portfolio and run full metrics / stress pipeline.

**Not the primary lowest-volatility-under-constraints baseline** — that is **constrained** MinVar
(`run_minimum_variance.py` / ``minimum_variance_constrained``). Advanced adds Ledoit--Wolf monthly Σ,
optional **maximum** vol cap from ``target_vol_annual``, and optional **L1 vs current weights** when
``minimum_variance_turnover_lambda > 0`` (rebalance-aware / turnover-controlled; equal-weight is
never the reference).

**Default** ``minimum_variance_turnover_lambda: 0`` — pure minimum variance on this advanced path
(no L1). When λ>0 and a valid current-weight reference exists on the eligible universe, metadata
``l1_penalty_used`` is true and outputs are labeled as turnover-controlled, not pure lowest-vol.
Otherwise ``l1_disabled_reason`` explains why L1 is off.

Same long-only box bounds as constrained MV. Optional **maximum** vol cap from ``target_vol_annual``:
``w'Σw ≤ σ²/12`` on monthly Σ (annualized vol ≤ σ).
"""
from legacy.runners._paths import REPO_ROOT

from pathlib import Path
import json
from datetime import datetime

from src.config import (
    load_validated_config,
    load_assets_metadata,
    resolve_cash_and_rf,
    resolve_local_benchmarks,
)
from src.config_schema import ConfigValidationError
from src.data_loader import load_monthly_data_shared
from src.portfolio_variants import (
    BASELINE_MV_ADVANCED_LABEL,
    advanced_minimum_variance_weights_txt_label,
    build_minimum_variance_advanced_controls,
    export_baseline_weights_txt,
    minimum_variance_advanced_metadata_export,
)
from src.utils import setup_logging, logger
from src.risk_contrib import rc_vol_window
from src.windows import slice_window
from run_report import run_portfolio_report_for_weights


def main() -> None:
    setup_logging()
    try:
        cfg = load_validated_config()
    except ConfigValidationError as e:
        logger.error("Configuration validation failed: %s", e)
        raise SystemExit(1)

    assets_meta = load_assets_metadata()
    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    local_benchmark_map = resolve_local_benchmarks(
        cfg.tickers, cfg.local_benchmark_map or {}, base_benchmark=cfg.benchmark_base_ticker
    )
    data = load_monthly_data_shared(
        tickers=cfg.tickers,
        benchmark_base_ticker=cfg.benchmark_base_ticker,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        investor_currency=cfg.investor_currency,
        windows_months=cfg.windows_months,
        assets_meta=assets_meta,
        no_cache=False,
        local_benchmark_map=local_benchmark_map,
        returns_frequency=getattr(cfg, "returns_frequency", None),
    )
    monthly_returns = data.monthly_returns
    analysis_end_str = data.analysis_end_str

    primary_window = cfg.windows_months[-1] if cfg.windows_months else 120
    mv_result = build_minimum_variance_advanced_controls(
        cfg,
        monthly_returns,
        analysis_end_str,
        primary_window,
    )

    out_dir = REPO_ROOT / "minimum variance advanced portfolio"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_export = minimum_variance_advanced_metadata_export(mv_result.diagnostics)

    with open(out_dir / "weights.json", "w", encoding="utf-8") as f:
        json.dump(mv_result.weights, f, indent=2, ensure_ascii=False)

    with open(out_dir / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta_export, f, indent=2, ensure_ascii=False)

    rc_series = None
    try:
        cols = [t for t in cfg.tickers if t in monthly_returns.columns]
        ret_slice = slice_window(monthly_returns[cols], analysis_end_str, primary_window).dropna(
            how="all"
        )
        if len(ret_slice) >= 2:
            w_dict = {t: float(mv_result.weights.get(t, 0.0)) for t in cols}
            import pandas as pd

            weights_df = pd.DataFrame(
                index=ret_slice.index, data={t: w_dict.get(t, 0.0) for t in cols}
            )
            rc_series = rc_vol_window(ret_slice, weights_df, ddof=1)
    except Exception as e:
        logger.warning("Could not compute RC_vol for advanced Minimum-Variance: %s", e)
        rc_series = None

    export_baseline_weights_txt(
        mv_result.weights,
        rc_series=rc_series,
        label=advanced_minimum_variance_weights_txt_label(mv_result.diagnostics),
        output_dir=out_dir,
    )

    if mv_result.status not in ("OK", "APPROXIMATE"):
        summary = {
            "portfolio_type": BASELINE_MV_ADVANCED_LABEL,
            "status": mv_result.status,
            "reason": mv_result.diagnostics.get("reason"),
            "minimum_variance_metadata": meta_export,
        }
        with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"{BASELINE_MV_ADVANCED_LABEL} — infeasible or failed baseline\n")
            f.write(f"Status: {mv_result.status}\n")
            if summary.get("reason"):
                f.write(f"Reason: {summary['reason']}\n")
        print("Minimum-Variance (advanced) baseline failed or infeasible; summary written.")
        return

    output_dir_csv = out_dir / "results_csv"
    output_dir_csv.mkdir(parents=True, exist_ok=True)

    run_timestamp = datetime.now().isoformat()
    pm_summary, meta = run_portfolio_report_for_weights(
        cfg,
        mv_result.weights,
        run_timestamp=run_timestamp,
        output_dir_csv=output_dir_csv,
        output_dir_final=out_dir,
        backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
        no_cache=False,
    )

    stress_report = meta.get("stress_report") or {}
    summary = {
        "portfolio_type": BASELINE_MV_ADVANCED_LABEL,
        "status": mv_result.status,
        "minimum_variance_metadata": meta_export,
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason"),
        "portfolio_valid": meta.get("portfolio_valid"),
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"{BASELINE_MV_ADVANCED_LABEL}\n")
        f.write("=" * 50 + "\n\n")
        interpret = (meta_export or {}).get("minimum_variance_interpretation")
        role = (meta_export or {}).get("minimum_variance_baseline_role")
        if isinstance(interpret, str) and interpret.strip():
            f.write(f"Role ({role}): {interpret.strip()}\n\n")
        if (meta_export or {}).get("l1_penalty_used"):
            f.write(
                "Reporting label: rebalance-aware / turnover-controlled minimum variance "
                "(L1 vs current portfolio weights).\n\n"
            )
        if pm_summary:
            f.write(
                "CAGR: {cagr:.3%}, Vol: {vol:.3%}, MaxDD: {mdd:.3%}, Sharpe: {sharpe:.3f}, Sortino: {sortino:.3f}, "
                "Beta: {beta:.3f}, Corr_base: {corr:.3f}\n".format(
                    cagr=pm_summary.get("cagr") or 0.0,
                    vol=pm_summary.get("vol_annual") or 0.0,
                    mdd=pm_summary.get("max_drawdown") or 0.0,
                    sharpe=pm_summary.get("sharpe") or 0.0,
                    sortino=pm_summary.get("sortino") or 0.0,
                    beta=pm_summary.get("beta_portfolio") or 0.0,
                    corr=pm_summary.get("corr_base") or 0.0,
                )
            )
        meta_diag = meta_export or {}
        f.write(
            f"\nOptimizer: {meta_diag.get('optimizer_name', 'minimum_variance_advanced_controls')} "
            f"(solver={meta_diag.get('solver', 'SLSQP')}, success={meta_diag.get('solver_success', '—')})\n"
        )
        f.write(
            f"L1: l1_penalty_used={meta_diag.get('l1_penalty_used', False)} "
            f"(lambda_config={meta_diag.get('lambda_turnover')}, "
            f"lambda_effective={meta_diag.get('lambda_turnover_effective', 0.0)})\n"
        )
        if meta_diag.get("l1_disabled_reason"):
            f.write(f"L1 disabled reason: {meta_diag.get('l1_disabled_reason')}\n")
        if meta_diag.get("l1_reference_source"):
            f.write(
                f"L1 reference: {meta_diag.get('l1_reference_source')} "
                f"(current_weights_available={meta_diag.get('current_portfolio_weights_available')})\n"
            )
        if meta_diag.get("volatility_target_used"):
            f.write(
                f"Vol target: {meta_diag.get('target_volatility')!r}, "
                f"binding={meta_diag.get('volatility_constraint_binding')}\n"
            )
        if meta_diag.get("l1_penalty_used"):
            f.write(
                f"L1 vs current: lambda={meta_diag.get('lambda_turnover')}, "
                f"L1_distance={meta_diag.get('l1_distance_to_current_portfolio')}\n"
            )
        pv = meta_diag.get("portfolio_variance")
        av = meta_diag.get("annualized_volatility")
        if pv is not None and av is not None:
            f.write(
                f"Window portfolio variance (monthly): {float(pv):.6g}; annualized vol: {float(av):.3%}\n"
            )
        f.write(
            f"\nStress: {stress_report.get('status', 'N/A')} "
            f"({stress_report.get('fail_reason_code') or stress_report.get('skip_reason') or '—'})\n"
        )
        f.write(f"Client-fit (MaxDD gate): {'PASS' if meta.get('portfolio_valid') else 'FAIL'}\n")
        if mv_result.status == "APPROXIMATE":
            f.write(
                "\nNOTE: Minimum-variance (advanced) solution is approximate (solver tolerances or fallback).\n"
            )

    print(f"Minimum-Variance (advanced) report written to {out_dir}")

    from src.variant_builder_runtime import maybe_rebuild_pdfs_after_variant

    maybe_rebuild_pdfs_after_variant(logger=logger)


if __name__ == "__main__":
    main()
