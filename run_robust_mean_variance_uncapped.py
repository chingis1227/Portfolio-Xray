from __future__ import annotations

"""
Build Robust Mean–Variance (uncapped long-only) baseline and run full metrics / stress pipeline.

Policy note:
- James–Stein shrunk expected returns; Ledoit–Wolf or OAS shrunk monthly covariance.
- Objective: maximize mu' w - lambda * w' Sigma w (SLSQP minimizes lambda * w' Sigma w - mu' w).
- Bounds: only long-only [0,1] per asset and sum(w)=1; no project caps or Young caps.

Outputs under ``robust mean variance uncapped portfolio/``.
"""

from pathlib import Path
import argparse
import json
from dataclasses import replace
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
    BASELINE_ROBUST_MV_UNCAPPED_LABEL,
    build_robust_mean_variance_uncapped,
    export_baseline_weights_txt,
    robust_mean_variance_baseline_metadata_export,
)
from src.robust_mv_lambda_resolve import resolve_robust_mv_lambda_for_baseline
from src.utils import setup_logging, logger
from src.risk_contrib import rc_vol_window
from src.windows import slice_window
from run_report import run_portfolio_report_for_weights

_SCRIPT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Robust Mean–Variance uncapped long-only baseline.")
    p.add_argument("--config", type=str, default=None, help="Path to config.yml (default: project root).")
    p.add_argument(
        "--robust-mv-lambda",
        type=float,
        default=None,
        dest="robust_mv_lambda",
        help="Override λ (default: read analysis_robust_mv_lambda_calibration/selected_lambda.txt).",
    )
    return p.parse_args()


def main() -> None:
    setup_logging()
    args = parse_args()
    config_path = Path(args.config).resolve() if args.config else _SCRIPT_ROOT / "config.yml"

    try:
        base_cfg = load_validated_config(config_path)
    except ConfigValidationError as e:
        logger.error("Configuration validation failed: %s", e)
        raise SystemExit(1)

    lam_resolved, lam_src = resolve_robust_mv_lambda_for_baseline(
        project_root=_SCRIPT_ROOT,
        cli_lambda=args.robust_mv_lambda,
    )
    if lam_resolved is None:
        logger.error(
            "Robust MV λ not resolved: run `python run_robust_mv_lambda_calibration.py` "
            "or pass `--robust-mv-lambda`."
        )
        raise SystemExit(2)
    cfg = replace(base_cfg, robust_mv_lambda=float(lam_resolved))
    logger.info("Robust MV λ=%s (resolution=%s)", lam_resolved, lam_src)

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
    result = build_robust_mean_variance_uncapped(
        cfg,
        monthly_returns,
        analysis_end_str,
        primary_window,
    )

    out_dir = Path(__file__).resolve().parent / "robust mean variance uncapped portfolio"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_export = robust_mean_variance_baseline_metadata_export(result.diagnostics)

    with open(out_dir / "weights.json", "w", encoding="utf-8") as f:
        json.dump(result.weights, f, indent=2, ensure_ascii=False)

    with open(out_dir / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta_export, f, indent=2, ensure_ascii=False)

    rc_series = None
    try:
        cols = [t for t in cfg.tickers if t in monthly_returns.columns]
        ret_slice = slice_window(monthly_returns[cols], analysis_end_str, primary_window).dropna(
            how="all"
        )
        if len(ret_slice) >= 2:
            w_dict = {t: float(result.weights.get(t, 0.0)) for t in cols}
            import pandas as pd

            weights_df = pd.DataFrame(
                index=ret_slice.index, data={t: w_dict.get(t, 0.0) for t in cols}
            )
            rc_series = rc_vol_window(ret_slice, weights_df, ddof=1)
    except Exception as e:
        logger.warning("Could not compute RC_vol for Robust MV uncapped baseline: %s", e)
        rc_series = None

    export_baseline_weights_txt(
        result.weights,
        rc_series=rc_series,
        label=BASELINE_ROBUST_MV_UNCAPPED_LABEL,
        output_dir=out_dir,
    )

    if result.status not in ("OK", "APPROXIMATE"):
        summary = {
            "portfolio_type": BASELINE_ROBUST_MV_UNCAPPED_LABEL,
            "status": result.status,
            "reason": result.diagnostics.get("reason"),
            "robust_mv_metadata": meta_export,
            "robust_mv_lambda_resolution": lam_src,
        }
        with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"{BASELINE_ROBUST_MV_UNCAPPED_LABEL} — infeasible or failed baseline\n")
            f.write(f"Status: {result.status}\n")
            if summary.get("reason"):
                f.write(f"Reason: {summary['reason']}\n")
        print("Robust Mean–Variance (uncapped) baseline failed or infeasible; summary written.")
        return

    output_dir_csv = out_dir / "results_csv"
    output_dir_csv.mkdir(parents=True, exist_ok=True)

    run_timestamp = datetime.now().isoformat()
    pm_summary, meta = run_portfolio_report_for_weights(
        cfg,
        result.weights,
        run_timestamp=run_timestamp,
        output_dir_csv=output_dir_csv,
        output_dir_final=out_dir,
        backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
        no_cache=False,
    )

    stress_report = meta.get("stress_report") or {}
    summary = {
        "portfolio_type": BASELINE_ROBUST_MV_UNCAPPED_LABEL,
        "status": result.status,
        "robust_mv_metadata": meta_export,
        "robust_mv_lambda_resolution": lam_src,
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason"),
        "portfolio_valid": meta.get("portfolio_valid"),
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"{BASELINE_ROBUST_MV_UNCAPPED_LABEL}\n")
        f.write("=" * 50 + "\n\n")
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
        md = meta_export or {}
        f.write(
            f"\nOptimizer: {md.get('optimizer_name', 'robust_mean_variance_uncapped')} "
            f"(solver={md.get('solver', 'SLSQP')}, success={md.get('solver_success', '—')})\n"
        )
        f.write(f"robust_mv_lambda: {md.get('robust_mv_lambda', '—')}\n")
        f.write(f"Covariance: {md.get('covariance_method', '—')} (shrinkage={md.get('shrinkage_applied', '—')})\n")
        if md.get("objective_value") is not None:
            f.write(f"Objective value (min lambda*w'Sig*w - mu'w): {float(md['objective_value']):.8g}\n")
        cm = md.get("concentration_metrics") or {}
        if cm:
            f.write(
                f"Concentration: HHI={float(cm.get('hhi', 0)):.4f}, "
                f"effective_n={float(cm.get('effective_n', 0)):.3f}, "
                f"top1={float(cm.get('top1_share', 0)):.3%}\n"
            )
        f.write(
            f"\nStress: {stress_report.get('status', 'N/A')} "
            f"({stress_report.get('fail_reason_code') or stress_report.get('skip_reason') or '—'})\n"
        )
        f.write(f"Client-fit (MaxDD gate): {'PASS' if meta.get('portfolio_valid') else 'FAIL'}\n")

    print(f"Robust Mean–Variance (uncapped) baseline report written to {out_dir}")

    try:
        from src.pdf_reports import try_rebuild_pdfs_after_variant

        try_rebuild_pdfs_after_variant(logger=logger)
    except Exception as e:
        logger.warning("PDF suite rebuild skipped: %s", e)


if __name__ == "__main__":
    main()
