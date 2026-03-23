from __future__ import annotations

"""
Build Equal-Weight baseline portfolio and run full metrics / stress pipeline.

Important policy note:
- This script MUST NOT apply any policy construction logic:
  - do not apply block logic
  - do not apply risk budgets
  - do not apply RC caps
  - do not apply weight caps or max weight limits
  - do not apply discretionary overlays
  - do not apply hidden policy filters.

Equal-Weight is a pure baseline: same eligible universe, equal weights across assets.
It is evaluated by the same metrics, stress-tests and client-fit checks as the Policy portfolio.
"""

from pathlib import Path
import json

from src.config import load_validated_config
from src.config_schema import ConfigValidationError
from src.portfolio_variants import (
    build_equal_weight_baseline,
    BASELINE_EQ_LABEL,
    export_baseline_weights_txt,
)
from src.portfolio_dynamic import portfolio_returns_nan_safe
from src.risk_contrib import cov_matrix_monthly, rc_vol_window
from src.utils import setup_logging, logger
from run_report import run_portfolio_report_for_weights


def main() -> None:
    setup_logging()
    try:
        cfg = load_validated_config()
    except ConfigValidationError as e:
        logger.error(f"Ошибка валидации конфигурации: {e}")
        raise SystemExit(1)

    # We reuse data loader from run_report via run_portfolio_report_for_weights.
    # First, build equal-weight weights using same universe and coverage rules.
    # For this we need returns; easiest is to let run_portfolio_report_for_weights
    # handle data IO, so here we call portfolio_variants only after retrieving data
    # indirectly would be complex. Instead, we re-use config and then call loader
    # again inside portfolio_variants via run_report helper.

    # To avoid duplicating loader logic, we will:
    # 1) Run a tiny helper: load monthly data once here.
    from src.config import load_assets_metadata, resolve_cash_and_rf, resolve_local_benchmarks
    from src.data_loader import load_monthly_data_shared
    from datetime import datetime

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
    )

    monthly_returns = data.monthly_returns
    analysis_end_str = data.analysis_end_str

    primary_window = cfg.windows_months[-1] if cfg.windows_months else 120
    eq_result = build_equal_weight_baseline(
        cfg,
        monthly_returns,
        analysis_end_str,
        primary_window,
    )

    out_root = Path(getattr(cfg, "output_dir_final", "ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ"))
    out_dir = out_root / "equal-weight portfolio"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Persist raw weights.json for the baseline.
    weights_json_path = out_dir / "weights.json"
    with open(weights_json_path, "w", encoding="utf-8") as f:
        json.dump(eq_result.weights, f, indent=2, ensure_ascii=False)

    # For Equal-Weight we don't need RC in weights.txt; pass rc_series=None.
    export_baseline_weights_txt(eq_result.weights, rc_series=None, label=BASELINE_EQ_LABEL, output_dir=out_dir)

    # If infeasible, still write minimal summary and stop.
    if eq_result.status != "OK":
        summary = {
            "portfolio_type": BASELINE_EQ_LABEL,
            "status": eq_result.status,
            "reason": eq_result.diagnostics.get("reason"),
        }
        with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
            f.write(f"{BASELINE_EQ_LABEL} — infeasible baseline\n")
            f.write(f"Status: {eq_result.status}\n")
            if summary.get("reason"):
                f.write(f"Reason: {summary['reason']}\n")
        print("Equal-Weight baseline infeasible, summary written.")
        return

    # Run full metrics/stress pipeline for Equal-Weight, using dedicated subfolders.
    output_dir_csv = out_dir / "results_csv"
    output_dir_csv.mkdir(parents=True, exist_ok=True)

    run_timestamp = datetime.now().isoformat()
    pm_summary, meta = run_portfolio_report_for_weights(
        cfg,
        eq_result.weights,
        run_timestamp=run_timestamp,
        output_dir_csv=output_dir_csv,
        output_dir_final=out_dir,
        backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
        no_cache=False,
    )

    # Build lightweight comparison-friendly summary.txt
    stress_report = meta.get("stress_report") or {}
    summary = {
        "portfolio_type": BASELINE_EQ_LABEL,
        "status": eq_result.status,
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason"),
        "portfolio_valid": meta.get("portfolio_valid"),
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"{BASELINE_EQ_LABEL}\n")
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

    print(f"Equal-Weight baseline report written to {out_dir}")


if __name__ == "__main__":
    main()

