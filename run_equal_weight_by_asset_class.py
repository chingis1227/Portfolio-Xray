from __future__ import annotations

"""
Build Equal-Weight by Asset-Class baseline and run full metrics / stress pipeline.

Same policy separation as ``run_equal_weight.py`` (no caps, overlays, RC policy).
Weights: equal budget per non-empty ``asset_class`` among taxonomy-classified eligible
tickers; equal split within each class. See ``build_equal_weight_by_asset_class_baseline``.
"""

from datetime import datetime
from pathlib import Path
import json

from src.config import load_assets_metadata, resolve_cash_and_rf, resolve_local_benchmarks
from src.config import load_validated_config
from src.config_schema import ConfigValidationError
from src.data_loader import load_monthly_data_shared
from src.portfolio_variants import (
    BASELINE_EQ_BY_CLASS_LABEL,
    build_equal_weight_by_asset_class_baseline,
    equal_weight_baseline_metadata_export,
    export_baseline_weights_txt,
)
from src.utils import setup_logging, logger
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
        cfg.tickers,
        cfg.local_benchmark_map or {},
        base_benchmark=cfg.benchmark_base_ticker,
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

    eq_ac_result = build_equal_weight_by_asset_class_baseline(
        cfg,
        monthly_returns,
        analysis_end_str,
        primary_window,
    )

    out_dir = Path(__file__).resolve().parent / "equal-weight by asset-class portfolio"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "weights.json", "w", encoding="utf-8") as f:
        json.dump(eq_ac_result.weights, f, indent=2, ensure_ascii=False)

    meta_export = equal_weight_baseline_metadata_export(eq_ac_result.diagnostics)
    with open(out_dir / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta_export, f, indent=2, ensure_ascii=False)

    export_baseline_weights_txt(
        eq_ac_result.weights,
        rc_series=None,
        label=BASELINE_EQ_BY_CLASS_LABEL,
        output_dir=out_dir,
    )

    if eq_ac_result.status != "OK":
        summary = {
            "portfolio_type": BASELINE_EQ_BY_CLASS_LABEL,
            "status": eq_ac_result.status,
            "reason": eq_ac_result.diagnostics.get("reason"),
            "equal_weight_baseline_metadata": meta_export,
        }
        with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"{BASELINE_EQ_BY_CLASS_LABEL} — infeasible baseline\n")
            f.write(f"Status: {eq_ac_result.status}\n")
            if summary.get("reason"):
                f.write(f"Reason: {summary['reason']}\n")
        print("Equal-Weight by Asset-Class baseline infeasible, summary written.")
        return

    output_dir_csv = out_dir / "results_csv"
    output_dir_csv.mkdir(parents=True, exist_ok=True)

    run_timestamp = datetime.now().isoformat()
    pm_summary, meta = run_portfolio_report_for_weights(
        cfg,
        eq_ac_result.weights,
        run_timestamp=run_timestamp,
        output_dir_csv=output_dir_csv,
        output_dir_final=out_dir,
        backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
        no_cache=False,
    )

    stress_report = meta.get("stress_report") or {}
    summary = {
        "portfolio_type": BASELINE_EQ_BY_CLASS_LABEL,
        "status": eq_ac_result.status,
        "equal_weight_baseline_metadata": meta_export,
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason"),
        "portfolio_valid": meta.get("portfolio_valid"),
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"{BASELINE_EQ_BY_CLASS_LABEL}\n")
        f.write("=" * 50 + "\n\n")
        cw = meta_export.get("class_weights") or {}
        if cw:
            f.write("Class weights:\n")
            for cl in sorted(cw.keys()):
                f.write(f"  {cl}: {cw[cl]:.3%}\n")
            f.write("\n")
        if pm_summary:
            f.write(
                "CAGR: {cagr:.3%}, Vol: {vol:.3%}, MaxDD: {mdd:.3%}, Sharpe: {sharpe:.3f}, "
                "Sortino: {sortino:.3f}, Beta: {beta:.3f}, Corr_base: {corr:.3f}\n".format(
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

    print(f"Equal-Weight by Asset-Class baseline report written to {out_dir}")

    try:
        from src.pdf_reports import try_rebuild_pdfs_after_variant

        try_rebuild_pdfs_after_variant(logger=logger)
    except Exception as e:
        logger.warning("PDF suite rebuild skipped: %s", e)


if __name__ == "__main__":
    main()
