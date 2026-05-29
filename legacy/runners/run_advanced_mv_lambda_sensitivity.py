from __future__ import annotations
"""
Grid search on ``minimum_variance_turnover_lambda`` for Advanced Minimum Variance (**not** the primary
lowest-volatility-under-constrained-box baseline; that is ``minimum_variance_constrained`` / ``run_minimum_variance.py``).

Uses the active ``config.yml``, Ledoit--Wolf Σ (forced inside advanced MinVar), optional L1 vs **current**
portfolio weights when λ > 0 (**rebalance-aware / turnover-controlled**; equal-weight is never the reference),
existing bounds and vol cap. For **pure** Advanced MinVar on this path in normal configs, keep
``minimum_variance_turnover_lambda: 0``; this script replaces λ per row.

Writes ``minimum variance advanced portfolio/lambda_sensitivity.csv`` and a short JSON summary.
"""
from legacy.runners._paths import REPO_ROOT

import csv
import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from run_report import run_portfolio_report_for_weights
from src.config import (
    load_validated_config,
    load_assets_metadata,
    resolve_cash_and_rf,
    resolve_local_benchmarks,
)
from src.config_schema import ConfigValidationError
from src.data_loader import load_monthly_data_shared
from src.portfolio_variants import (
    build_minimum_variance_advanced_controls,
    minimum_variance_advanced_metadata_export,
)
from src.utils import logger, setup_logging

LAMBDA_GRID = (0.0, 0.0001, 0.0005, 0.001, 0.0025, 0.005, 0.01)


def _hhi(weights: dict[str, float]) -> float:
    return float(sum(w * w for w in weights.values() if w and w == w))


def _json_safe(x):
    if x != x:  # NaN
        return None
    if isinstance(x, (float, int)):
        return float(x) if isinstance(x, float) else x
    return x


def _stress_fields(stress_report: dict) -> tuple[float | None, str | None, str | None]:
    worst = stress_report.get("worst_scenario_loss_pct")
    worst = float(worst) if worst is not None else None
    top_asset = None
    top_factor = None
    for row in stress_report.get("scenario_results") or []:
        if top_asset is None:
            top_asset = row.get("top1_rc_asset")
        pf = row.get("pnl_by_factor_pct") or {}
        if pf:
            fac, val = max(pf.items(), key=lambda x: abs(float(x[1])))
            top_factor = f"{fac} ({float(val):.4f})"
            break
    return worst, top_asset, top_factor


def main() -> None:
    setup_logging()
    try:
        base_cfg = load_validated_config()
    except ConfigValidationError as e:
        logger.error("Configuration validation failed: %s", e)
        raise SystemExit(1)

    assets_meta = load_assets_metadata()
    cash_proxy_ticker, rf_source = resolve_cash_and_rf(base_cfg)
    local_benchmark_map = resolve_local_benchmarks(
        base_cfg.tickers,
        base_cfg.local_benchmark_map or {},
        base_benchmark=base_cfg.benchmark_base_ticker,
    )
    data = load_monthly_data_shared(
        tickers=base_cfg.tickers,
        benchmark_base_ticker=base_cfg.benchmark_base_ticker,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        investor_currency=base_cfg.investor_currency,
        windows_months=base_cfg.windows_months,
        assets_meta=assets_meta,
        no_cache=False,
        local_benchmark_map=local_benchmark_map,
        returns_frequency=getattr(base_cfg, "returns_frequency", None),
    )
    monthly_returns = data.monthly_returns
    analysis_end_str = data.analysis_end_str
    primary_window = base_cfg.windows_months[-1] if base_cfg.windows_months else 120

    out_dir = REPO_ROOT / "minimum variance advanced portfolio"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "lambda_sensitivity.csv"
    rows: list[dict[str, object]] = []
    l1_dist_baseline: float | None = None

    for lam in LAMBDA_GRID:
        cfg = replace(base_cfg, minimum_variance_turnover_lambda=float(lam))
        mv = build_minimum_variance_advanced_controls(
            cfg, monthly_returns, analysis_end_str, primary_window
        )
        meta = minimum_variance_advanced_metadata_export(mv.diagnostics)
        l1_dist = mv.diagnostics.get("l1_distance_to_current_portfolio")
        l1_f = float(l1_dist) if l1_dist is not None else None

        if lam == 0.0 and l1_f is not None:
            l1_dist_baseline = l1_f

        turn_reduct = None
        if l1_dist_baseline is not None and l1_f is not None:
            turn_reduct = float(l1_dist_baseline) - float(l1_f)

        row_base = {
            "lambda_config": float(lam),
            "lambda_turnover_effective": meta.get("lambda_turnover_effective"),
            "l1_penalty_used": meta.get("l1_penalty_used"),
            "l1_reference_source": meta.get("l1_reference_source"),
            "l1_disabled_reason": meta.get("l1_disabled_reason"),
            "l1_distance": l1_f,
            "turnover_reduction_vs_lambda0": turn_reduct,
            "vol_cap_binding": meta.get("volatility_constraint_binding"),
            "annualized_vol_window": meta.get("annualized_volatility"),
            "hhi": _hhi(mv.weights),
            "weights_compact": json.dumps(
                {k: round(v, 6) for k, v in sorted(mv.weights.items()) if v and abs(v) > 1e-12}
            ),
            "mv_status": mv.status,
            "portfolio_valid": None,
            "vol_annual_10y": None,
            "max_drawdown_10y": None,
            "sharpe_10y": None,
            "worst_stress_loss": None,
            "top_rc_asset": None,
            "top_factor_pnl_scenario": None,
        }

        if mv.status not in ("OK", "APPROXIMATE"):
            rows.append(row_base)
            continue

        run_ts = datetime.now().isoformat()
        output_dir_csv = out_dir / "results_csv" / f"lambda_{lam:g}".replace(".", "p")
        output_dir_csv.mkdir(parents=True, exist_ok=True)
        pm_summary, rep_meta = run_portfolio_report_for_weights(
            cfg,
            mv.weights,
            run_timestamp=run_ts,
            output_dir_csv=output_dir_csv,
            output_dir_final=out_dir,
            backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
            no_cache=False,
        )
        sr = rep_meta.get("stress_report") or {}
        worst, top_a, top_f = _stress_fields(sr)

        row_base["portfolio_valid"] = rep_meta.get("portfolio_valid")
        row_base["vol_annual_10y"] = _json_safe(pm_summary.get("vol_annual") if pm_summary else None)
        row_base["max_drawdown_10y"] = _json_safe(
            pm_summary.get("max_drawdown") if pm_summary else None
        )
        row_base["sharpe_10y"] = _json_safe(pm_summary.get("sharpe") if pm_summary else None)
        row_base["worst_stress_loss"] = worst
        row_base["top_rc_asset"] = top_a
        row_base["top_factor_pnl_scenario"] = top_f
        rows.append(row_base)

    fieldnames = list(rows[0].keys()) if rows else []
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    summary_path = out_dir / "lambda_sensitivity_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now().isoformat(),
                "analysis_end": analysis_end_str,
                "window_months": primary_window,
                "lambda_grid": list(LAMBDA_GRID),
                "rows": rows,
            },
            f,
            indent=2,
            default=str,
        )

    logger.info("Wrote %s and %s", csv_path, summary_path)
    print(f"Lambda sensitivity table: {csv_path}")


if __name__ == "__main__":
    main()
