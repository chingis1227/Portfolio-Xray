from __future__ import annotations
"""
Build Risk-Parity baseline portfolio and run full metrics / stress pipeline.

Important policy note:
- This script MUST NOT apply any policy construction logic:
  - do not apply RC caps
  - do not apply weight caps or max weight limits
  - do not apply discretionary overlays
  - do not apply hidden policy filters.

Risk-Parity here is a pure asset-level baseline: same eligible universe, weights chosen
to equalize RC_vol across assets (as close as numerically feasible), long-only, fully invested.
It is evaluated by the same metrics, stress-tests and client-fit checks as the Policy portfolio.
"""
from legacy.runners._paths import REPO_ROOT

from pathlib import Path
import json
from datetime import datetime

from src.config import load_validated_config, load_assets_metadata, resolve_cash_and_rf, resolve_local_benchmarks
from src.config_schema import ConfigValidationError
from src.data_loader import load_monthly_data_shared
from src.portfolio_variants import (
    build_risk_parity_baseline,
    BASELINE_RP_LABEL,
    export_baseline_weights_txt,
)
from src.utils import setup_logging, logger
from src.risk_contrib import cov_matrix_monthly, rc_vol_window
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
    rp_result = build_risk_parity_baseline(
        cfg,
        monthly_returns,
        analysis_end_str,
        primary_window,
    )

    # Baseline outputs are stored separately from main optimization results.
    out_dir = REPO_ROOT / "risk parity portfolio"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save raw weights
    with open(out_dir / "weights.json", "w", encoding="utf-8") as f:
        json.dump(rp_result.weights, f, indent=2, ensure_ascii=False)

    # RC shown in weights.txt should match RP optimization target.
    # First preference: solver RC diagnostics (same covariance/setup as optimization).
    # Fallback: recompute RC on window if diagnostics are unavailable.
    rc_series = None
    try:
        rc_diag = (rp_result.diagnostics or {}).get("rc_by_asset")
        if rc_diag:
            import pandas as pd

            rc_series = pd.Series({str(k): float(v) for k, v in rc_diag.items()})
        else:
            cols = [t for t in cfg.tickers if t in monthly_returns.columns]
            ret_slice = slice_window(monthly_returns[cols], analysis_end_str, primary_window).dropna(how="all")
            if len(ret_slice) >= 2:
                w_df = (
                    json.loads(json.dumps(rp_result.weights))  # shallow copy; keeps floats JSON-serializable
                )
                import pandas as pd

                weights_df = pd.DataFrame(index=ret_slice.index, data={t: w_df.get(t, 0.0) for t in cols})
                rc_series = rc_vol_window(ret_slice, weights_df, ddof=1)
    except Exception as e:
        logger.warning(f"Не удалось посчитать RC_vol для Risk-Parity baseline: {e}")
        rc_series = None

    export_baseline_weights_txt(rp_result.weights, rc_series=rc_series, label=BASELINE_RP_LABEL, output_dir=out_dir)

    if rp_result.status not in ("OK", "APPROXIMATE"):
        summary = {
            "portfolio_type": BASELINE_RP_LABEL,
            "status": rp_result.status,
            "reason": rp_result.diagnostics.get("reason"),
        }
        with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"{BASELINE_RP_LABEL} — infeasible baseline\n")
            f.write(f"Status: {rp_result.status}\n")
            if summary.get("reason"):
                f.write(f"Reason: {summary['reason']}\n")
        print("Risk-Parity baseline infeasible, summary written.")
        return

    # Full metrics / stress pipeline
    output_dir_csv = out_dir / "results_csv"
    output_dir_csv.mkdir(parents=True, exist_ok=True)

    run_timestamp = datetime.now().isoformat()
    pm_summary, meta = run_portfolio_report_for_weights(
        cfg,
        rp_result.weights,
        run_timestamp=run_timestamp,
        output_dir_csv=output_dir_csv,
        output_dir_final=out_dir,
        backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
        no_cache=False,
    )

    stress_report = meta.get("stress_report") or {}
    summary = {
        "portfolio_type": BASELINE_RP_LABEL,
        "status": rp_result.status,
        "solver_status": rp_result.diagnostics.get("status"),
        "max_rc_error": rp_result.diagnostics.get("max_rc_error"),
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason"),
        "portfolio_valid": meta.get("portfolio_valid"),
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"{BASELINE_RP_LABEL}\n")
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
        if rp_result.diagnostics.get("status") == "APPROXIMATE":
            f.write("\nNOTE: Risk parity solution is approximate (numerical tolerances not fully met).\n")

    print(f"Risk-Parity baseline report written to {out_dir}")

    from src.variant_builder_runtime import maybe_rebuild_pdfs_after_variant

    maybe_rebuild_pdfs_after_variant(logger=logger)


if __name__ == "__main__":
    main()
