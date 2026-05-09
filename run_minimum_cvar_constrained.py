from __future__ import annotations

"""
Build Minimum CVaR (constrained) baseline: same LP as uncapped but box bounds from
``_build_bounds`` (config min/max and Young caps when active).

Outputs under ``minimum cvar constrained portfolio/``.
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
    BASELINE_MCVAR_CONSTRAINED_LABEL,
    build_minimum_cvar_constrained,
    export_baseline_weights_txt,
    minimum_cvar_baseline_metadata_export,
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
    result = build_minimum_cvar_constrained(
        cfg,
        monthly_returns,
        analysis_end_str,
        primary_window,
    )

    out_dir = Path(__file__).resolve().parent / "minimum cvar constrained portfolio"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_export = minimum_cvar_baseline_metadata_export(result.diagnostics)

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
        logger.warning("Could not compute RC_vol for Minimum CVaR constrained baseline: %s", e)
        rc_series = None

    export_baseline_weights_txt(
        result.weights, rc_series=rc_series, label=BASELINE_MCVAR_CONSTRAINED_LABEL, output_dir=out_dir
    )

    if result.status not in ("OK", "APPROXIMATE"):
        summary = {
            "portfolio_type": BASELINE_MCVAR_CONSTRAINED_LABEL,
            "status": result.status,
            "reason": result.diagnostics.get("reason"),
            "minimum_cvar_metadata": meta_export,
        }
        with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"{BASELINE_MCVAR_CONSTRAINED_LABEL} — infeasible or failed baseline\n")
            f.write(f"Status: {result.status}\n")
            if summary.get("reason"):
                f.write(f"Reason: {summary['reason']}\n")
        print("Minimum CVaR (constrained) baseline failed or infeasible; summary written.")
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
        "portfolio_type": BASELINE_MCVAR_CONSTRAINED_LABEL,
        "status": result.status,
        "minimum_cvar_metadata": meta_export,
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason"),
        "portfolio_valid": meta.get("portfolio_valid"),
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"{BASELINE_MCVAR_CONSTRAINED_LABEL}\n")
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
            f"\nOptimizer: {md.get('optimizer_name', 'minimum_cvar_constrained')} "
            f"(solver={md.get('solver', 'HiGHS')}, linprog_success={md.get('linprog_success', '—')})\n"
        )
        if md.get("cvar_objective_value") is not None:
            f.write(f"CVaR LP objective (alpha + lambda*sum z): {float(md['cvar_objective_value']):.6g}\n")
        if md.get("empirical_cvar_loss") is not None:
            f.write(f"Empirical sample CVaR (loss): {float(md['empirical_cvar_loss']):.6g}\n")
        f.write(
            f"\nStress: {stress_report.get('status', 'N/A')} "
            f"({stress_report.get('fail_reason_code') or stress_report.get('skip_reason') or '—'})\n"
        )
        f.write(f"Client-fit (MaxDD gate): {'PASS' if meta.get('portfolio_valid') else 'FAIL'}\n")

    print(f"Minimum CVaR (constrained) baseline report written to {out_dir}")

    try:
        from src.pdf_reports import try_rebuild_pdfs_after_variant

        try_rebuild_pdfs_after_variant(logger=logger)
    except Exception as e:
        logger.warning("PDF suite rebuild skipped: %s", e)


if __name__ == "__main__":
    main()
