from __future__ import annotations

"""
Build Hierarchical Risk Parity (HRP) baseline and run full metrics / stress pipeline.

Policy note (canonical baseline):
- No policy box bounds, no per-name min/max caps, no Young caps as construction constraints.
- No SLSQP or other optimizer projection onto a feasible set.
- Pure baseline comparable to canonical Risk Parity: long-only weights summing to one on the eligible
  universe; evaluated by the same metrics, stress tests, and client-fit checks as other baselines.
"""

import json
from datetime import datetime
from pathlib import Path

from src.config import (
    load_assets_metadata,
    load_validated_config,
    resolve_cash_and_rf,
    resolve_local_benchmarks,
)
from src.config_schema import ConfigValidationError
from src.data_loader import load_monthly_data_shared
from src.portfolio_variants import (
    BASELINE_HRP_LABEL,
    build_hierarchical_risk_parity_baseline,
    export_baseline_weights_txt,
    hierarchical_risk_parity_baseline_metadata_export,
)
from src.risk_contrib import rc_vol_window
from src.utils import logger, setup_logging
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
    hrp_result = build_hierarchical_risk_parity_baseline(
        cfg,
        monthly_returns,
        analysis_end_str,
        primary_window,
    )

    out_dir = Path(__file__).resolve().parent / "hierarchical risk parity portfolio"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_export = hierarchical_risk_parity_baseline_metadata_export(hrp_result.diagnostics)

    with open(out_dir / "weights.json", "w", encoding="utf-8") as f:
        json.dump(hrp_result.weights, f, indent=2, ensure_ascii=False)

    with open(out_dir / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta_export, f, indent=2, ensure_ascii=False)

    rc_series = None
    try:
        cols = [t for t in cfg.tickers if t in monthly_returns.columns]
        ret_slice = slice_window(monthly_returns[cols], analysis_end_str, primary_window).dropna(
            how="all"
        )
        if len(ret_slice) >= 2:
            w_dict = {t: float(hrp_result.weights.get(t, 0.0)) for t in cols}
            import pandas as pd

            weights_df = pd.DataFrame(
                index=ret_slice.index, data={t: w_dict.get(t, 0.0) for t in cols}
            )
            rc_series = rc_vol_window(ret_slice, weights_df, ddof=1)
    except Exception as e:
        logger.warning("Could not compute RC_vol for HRP baseline: %s", e)
        rc_series = None

    export_baseline_weights_txt(
        hrp_result.weights, rc_series=rc_series, label=BASELINE_HRP_LABEL, output_dir=out_dir
    )

    if hrp_result.status not in ("OK", "APPROXIMATE"):
        summary = {
            "portfolio_type": BASELINE_HRP_LABEL,
            "status": hrp_result.status,
            "reason": hrp_result.diagnostics.get("reason"),
            "hrp_metadata": meta_export,
        }
        with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"{BASELINE_HRP_LABEL} — infeasible or failed baseline\n")
            f.write(f"Status: {hrp_result.status}\n")
            if summary.get("reason"):
                f.write(f"Reason: {summary['reason']}\n")
        print("Hierarchical Risk Parity baseline failed or infeasible; summary written.")
        return

    output_dir_csv = out_dir / "results_csv"
    output_dir_csv.mkdir(parents=True, exist_ok=True)

    run_timestamp = datetime.now().isoformat()
    pm_summary, meta = run_portfolio_report_for_weights(
        cfg,
        hrp_result.weights,
        run_timestamp=run_timestamp,
        output_dir_csv=output_dir_csv,
        output_dir_final=out_dir,
        backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
        no_cache=False,
    )

    stress_report = meta.get("stress_report") or {}
    summary = {
        "portfolio_type": BASELINE_HRP_LABEL,
        "status": hrp_result.status,
        "hrp_linkage_method": hrp_result.diagnostics.get("hrp_linkage_method"),
        "hrp_linkage_fallback_from_ward": hrp_result.diagnostics.get(
            "hrp_linkage_fallback_from_ward"
        ),
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason"),
        "portfolio_valid": meta.get("portfolio_valid"),
        "hrp_metadata": meta_export,
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"{BASELINE_HRP_LABEL}\n")
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
        f.write(
            f"\nStress: {stress_report.get('status', 'N/A')} "
            f"({stress_report.get('fail_reason_code') or stress_report.get('skip_reason') or '—'})\n"
        )
        f.write(f"Client-fit (MaxDD gate): {'PASS' if meta.get('portfolio_valid') else 'FAIL'}\n")
        f.write(
            f"HRP linkage: {hrp_result.diagnostics.get('hrp_linkage_method', 'N/A')} "
            f"(ward_fallback={hrp_result.diagnostics.get('hrp_linkage_fallback_from_ward', False)})\n"
        )

    print(f"Hierarchical Risk Parity baseline report written to {out_dir}")

    try:
        from src.pdf_reports import try_rebuild_pdfs_after_variant

        try_rebuild_pdfs_after_variant(logger=logger)
    except Exception as e:
        logger.warning("PDF suite rebuild skipped: %s", e)


if __name__ == "__main__":
    main()
