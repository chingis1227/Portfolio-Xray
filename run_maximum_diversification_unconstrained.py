from __future__ import annotations

"""
Build Maximum-Diversification (unconstrained long-only) baseline and run full metrics / stress pipeline.

Policy note:
- This variant uses only long-only ``w_i >= 0`` and ``sum(w) = 1`` as optimization constraints.
- No project box bounds: no ``min_single_security_weight_pct``, no ``max_single_security_weight_pct``,
  no feasibility per-name caps, no Young / per-ticker caps as optimizer bounds.
- No RC caps, no ProLiquidity, no discretionary overlays.

Same eligible-universe filter, monthly **Σ** path, and PSD repair as constrained Maximum Diversification.
This script is **maximum_diversification_unconstrained** only. Outputs live under
``maximum diversification unconstrained portfolio/``.
"""

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
    BASELINE_MD_UNCONSTRAINED_LABEL,
    build_maximum_diversification_unconstrained,
    export_baseline_weights_txt,
    maximum_diversification_baseline_metadata_export,
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
    md_result = build_maximum_diversification_unconstrained(
        cfg,
        monthly_returns,
        analysis_end_str,
        primary_window,
    )

    out_dir = Path(__file__).resolve().parent / "maximum diversification unconstrained portfolio"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_export = maximum_diversification_baseline_metadata_export(md_result.diagnostics)

    with open(out_dir / "weights.json", "w", encoding="utf-8") as f:
        json.dump(md_result.weights, f, indent=2, ensure_ascii=False)

    with open(out_dir / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta_export, f, indent=2, ensure_ascii=False)

    rc_series = None
    try:
        cols = [t for t in cfg.tickers if t in monthly_returns.columns]
        ret_slice = slice_window(monthly_returns[cols], analysis_end_str, primary_window).dropna(
            how="all"
        )
        if len(ret_slice) >= 2:
            w_dict = {t: float(md_result.weights.get(t, 0.0)) for t in cols}
            import pandas as pd

            weights_df = pd.DataFrame(
                index=ret_slice.index, data={t: w_dict.get(t, 0.0) for t in cols}
            )
            rc_series = rc_vol_window(ret_slice, weights_df, ddof=1)
    except Exception as e:
        logger.warning(
            "Could not compute RC_vol for Maximum-Diversification (unconstrained) baseline: %s", e
        )
        rc_series = None

    export_baseline_weights_txt(
        md_result.weights,
        rc_series=rc_series,
        label=BASELINE_MD_UNCONSTRAINED_LABEL,
        output_dir=out_dir,
    )

    if md_result.status not in ("OK", "APPROXIMATE"):
        summary = {
            "portfolio_type": BASELINE_MD_UNCONSTRAINED_LABEL,
            "status": md_result.status,
            "reason": md_result.diagnostics.get("reason"),
            "maximum_diversification_metadata": meta_export,
        }
        with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"{BASELINE_MD_UNCONSTRAINED_LABEL} — infeasible or failed baseline\n")
            f.write(f"Status: {md_result.status}\n")
            if summary.get("reason"):
                f.write(f"Reason: {summary['reason']}\n")
        print("Maximum-Diversification (unconstrained) baseline failed or infeasible; summary written.")
        return

    output_dir_csv = out_dir / "results_csv"
    output_dir_csv.mkdir(parents=True, exist_ok=True)

    run_timestamp = datetime.now().isoformat()
    pm_summary, meta = run_portfolio_report_for_weights(
        cfg,
        md_result.weights,
        run_timestamp=run_timestamp,
        output_dir_csv=output_dir_csv,
        output_dir_final=out_dir,
        backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
        no_cache=False,
    )

    stress_report = meta.get("stress_report") or {}
    summary = {
        "portfolio_type": BASELINE_MD_UNCONSTRAINED_LABEL,
        "status": md_result.status,
        "maximum_diversification_metadata": meta_export,
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason"),
        "portfolio_valid": meta.get("portfolio_valid"),
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"{BASELINE_MD_UNCONSTRAINED_LABEL}\n")
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
        meta_diag = meta_export or {}
        f.write(
            f"\nOptimizer: {meta_diag.get('optimizer_name', 'maximum_diversification_unconstrained')} "
            f"(solver={meta_diag.get('solver', 'SLSQP')}, success={meta_diag.get('solver_success', '—')})\n"
        )
        pv = meta_diag.get("portfolio_variance")
        av = meta_diag.get("annualized_volatility")
        dr = meta_diag.get("diversification_ratio")
        if pv is not None and av is not None:
            f.write(
                f"Window portfolio variance (monthly): {float(pv):.6g}; annualized vol: {float(av):.3%}\n"
            )
        if dr is not None:
            f.write(f"Diversification ratio (dimensionless): {float(dr):.6f}\n")
        f.write(
            f"\nStress: {stress_report.get('status', 'N/A')} "
            f"({stress_report.get('fail_reason_code') or stress_report.get('skip_reason') or '—'})\n"
        )
        f.write(f"Client-fit (MaxDD gate): {'PASS' if meta.get('portfolio_valid') else 'FAIL'}\n")
        if md_result.status == "APPROXIMATE":
            f.write(
                "\nNOTE: Maximum-diversification solution is approximate (solver tolerances or fallback).\n"
            )

    print(f"Maximum-Diversification (unconstrained) baseline report written to {out_dir}")

    from src.variant_builder_runtime import maybe_rebuild_pdfs_after_variant

    maybe_rebuild_pdfs_after_variant(logger=logger)


if __name__ == "__main__":
    main()
