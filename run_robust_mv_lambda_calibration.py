from __future__ import annotations

"""
Robust Mean–Variance λ calibration: scan an internal λ grid, evaluate each candidate against
config IPS targets (vol, MaxDD mandate, weight cap, optional synthetic loss / RC limits via YAML),
then pick the lowest λ that satisfies the mandate (including borderline class), tie-break by highest
10Y CAGR. Writes CSV + JSON summary + ``selected_portfolio/`` full report when a mandate-eligible λ exists.
When none qualifies, the summary JSON includes ``no_feasible_lambda_diagnostic`` (tested range,
fallback λ, breached limits, generic causes, suggested actions) and logs a warning.

Does **not** modify the policy optimizer, mandate gate implementation in ``run_report``, or ``run_stress``.
"""

import argparse
import csv
import json
import shutil
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pandas as pd

from run_report import run_portfolio_report_for_weights

from src.config import (
    load_validated_config,
    load_assets_metadata,
    resolve_cash_and_rf,
    resolve_local_benchmarks,
)
from src.config_schema import ConfigValidationError
from src.data_loader import load_monthly_data_shared
from src.metrics_asset import mandate_max_drawdown_full_history_check
from src.portfolio_variants import (
    BASELINE_ROBUST_MV_CONSTRAINED_LABEL,
    build_robust_mean_variance_constrained,
    export_baseline_weights_txt,
    robust_mean_variance_baseline_metadata_export,
)
from src.robust_mv_calibration import (
    build_no_feasible_lambda_diagnostic,
    classify_robust_mv_mandate,
    infer_binding_constraints,
    load_optional_robust_mv_calibration_block,
    max_top1_rc_synthetic,
    max_top3_rc_sum_synthetic,
    pick_least_bad_lambda,
    read_es95_from_var_es_csv,
    synthetic_mandatory_loss_detail,
)
from src.risk_contrib import rc_vol_window
from src.utils import logger, setup_logging
from src.windows import slice_window

DEFAULT_LAMBDA_GRID = (0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0)


def _lam_slug(lam: float) -> str:
    return f"{lam:g}".replace(".", "p")


def _json_safe(x):
    if isinstance(x, float) and x != x:
        return None
    return x


def _finite_float(x) -> float | None:
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def _pick_winner_rows(rows: list[dict[str, object]]) -> dict[str, object] | None:
    eligible = [
        r
        for r in rows
        if r.get("build_status") in ("OK", "APPROXIMATE")
        and r.get("mandate_classification") in ("pass", "borderline")
    ]
    if eligible:
        eligible.sort(
            key=lambda r: (float(r.get("robust_mv_lambda", 1e9)), -float(r.get("cagr_10y") or -1e9))
        )
        return eligible[0]
    return pick_least_bad_lambda(rows)  # type: ignore[arg-type]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Calibrate robust_mv_lambda vs IPS mandate (Robust MV constrained).")
    p.add_argument("--config", type=str, default=None, help="Path to config.yml (default: project root).")
    p.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output folder (default: ./analysis_robust_mv_lambda_calibration).",
    )
    p.add_argument(
        "--lambda-grid",
        type=str,
        default=None,
        help="Comma-separated λ grid (default: built-in grid). Example: 0.1,0.2,0.5",
    )
    p.add_argument(
        "--keep-scratch",
        action="store_true",
        help="Keep per-λ scratch folders under output-dir/_scratch.",
    )
    return p.parse_args()


def main() -> None:
    setup_logging()
    args = parse_args()
    config_path = Path(args.config).resolve() if args.config else Path(__file__).resolve().parent / "config.yml"

    try:
        base_cfg = load_validated_config(config_path)
    except ConfigValidationError as e:
        logger.error("Configuration validation failed: %s", e)
        raise SystemExit(1)

    calibration_limits = load_optional_robust_mv_calibration_block(config_path)

    if args.lambda_grid:
        try:
            lam_grid = tuple(float(x.strip()) for x in args.lambda_grid.split(",") if x.strip())
        except ValueError:
            logger.error("Invalid --lambda-grid")
            raise SystemExit(2)
    else:
        lam_grid = DEFAULT_LAMBDA_GRID

    root = Path(args.output_dir).resolve() if args.output_dir else Path(__file__).resolve().parent / "analysis_robust_mv_lambda_calibration"
    root.mkdir(parents=True, exist_ok=True)
    scratch_root = root / "_scratch"
    if scratch_root.is_dir() and not args.keep_scratch:
        shutil.rmtree(scratch_root, ignore_errors=True)
    scratch_root.mkdir(parents=True, exist_ok=True)

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

    enforce_syn = base_cfg.target_max_drawdown_pct is not None

    rows_out: list[dict[str, object]] = []
    run_started = datetime.now().isoformat()

    for lam in lam_grid:
        slug = _lam_slug(lam)
        cfg_lam = replace(base_cfg, robust_mv_lambda=float(lam))
        res = build_robust_mean_variance_constrained(
            cfg_lam,
            monthly_returns,
            analysis_end_str,
            primary_window,
        )

        base_row: dict[str, object] = {
            "robust_mv_lambda": float(lam),
            "build_status": res.status,
            "covariance_method": (res.diagnostics or {}).get("covariance_method"),
            "mu_shrinkage_method": (res.diagnostics or {}).get("mu_shrinkage_method"),
            "solver_success": (res.diagnostics or {}).get("solver_success"),
            "mandate_classification": None,
            "mandate_failures": None,
            "portfolio_valid": None,
            "cagr_10y": None,
            "vol_annual_10y": None,
            "max_drawdown_10y": None,
            "sharpe_10y": None,
            "es_95_hist_10y": None,
            "worst_scenario_loss_pct": None,
            "failed_synthetic_scenarios": None,
            "max_weight": None,
            "hhi": None,
            "effective_n": None,
            "max_top1_rc_pct_synthetic": None,
            "max_top3_rc_sum_pct_synthetic": None,
            "slack_target_vol": None,
            "slack_mandate_max_dd_hist": None,
            "slack_max_single_weight": None,
            "weights_compact": None,
        }

        if res.status not in ("OK", "APPROXIMATE"):
            rows_out.append(base_row)
            continue

        scratch_final = scratch_root / f"lambda_{slug}"
        scratch_csv = scratch_final / "results_csv"
        scratch_csv.mkdir(parents=True, exist_ok=True)

        run_ts = datetime.now().isoformat()
        pm_summary, meta = run_portfolio_report_for_weights(
            cfg_lam,
            res.weights,
            run_timestamp=run_ts,
            output_dir_csv=scratch_csv,
            output_dir_final=scratch_final,
            backtest_mode_override=getattr(cfg_lam, "backtest_mode", "dynamic_nan_safe"),
            no_cache=False,
        )
        stress = meta.get("stress_report") or {}
        mandate_chk = mandate_max_drawdown_full_history_check(
            monthly_returns,
            res.weights,
            abs(cfg_lam.target_max_drawdown_pct) if cfg_lam.target_max_drawdown_pct is not None else None,
        )

        cm = (res.diagnostics or {}).get("concentration_metrics") or {}
        mx_w = float(res.diagnostics.get("max_weight") or 0.0)

        eval_blob = classify_robust_mv_mandate(
            portfolio_valid=meta.get("portfolio_valid"),
            target_vol_annual=cfg_lam.target_vol_annual,
            vol_annual_10y=_finite_float(pm_summary.get("vol_annual")) if pm_summary else None,
            target_max_drawdown_pct=cfg_lam.target_max_drawdown_pct,
            mandate_max_drawdown_realized=(
                float(mandate_chk["max_drawdown_realized"])
                if mandate_chk.get("max_drawdown_realized") is not None
                else None
            ),
            max_single_security_weight_pct=cfg_lam.max_single_security_weight_pct,
            weights=res.weights,
            stress_report=stress,
            calibration_limits=calibration_limits,
            enforce_synthetic_vs_mandate_dd=enforce_syn,
        )

        es95 = read_es95_from_var_es_csv(scratch_csv / "var_es_10y.csv")

        mx1 = max_top1_rc_synthetic(stress)
        mx3 = max_top3_rc_sum_synthetic(stress)
        _, syn_failed_list = synthetic_mandatory_loss_detail(stress)

        base_row.update(
            {
                "mandate_classification": eval_blob["mandate_classification"],
                "mandate_failures": ";".join(eval_blob["mandate_failures"]),
                "portfolio_valid": meta.get("portfolio_valid"),
                "cagr_10y": _json_safe(pm_summary.get("cagr") if pm_summary else None),
                "vol_annual_10y": _json_safe(pm_summary.get("vol_annual") if pm_summary else None),
                "max_drawdown_10y": _json_safe(pm_summary.get("max_drawdown") if pm_summary else None),
                "sharpe_10y": _json_safe(pm_summary.get("sharpe") if pm_summary else None),
                "es_95_hist_10y": es95,
                "worst_scenario_loss_pct": _json_safe(stress.get("worst_scenario_loss_pct")),
                "failed_synthetic_scenarios": ";".join(syn_failed_list),
                "max_weight": mx_w,
                "hhi": _json_safe(cm.get("hhi")),
                "effective_n": _json_safe(cm.get("effective_n")),
                "max_top1_rc_pct_synthetic": mx1,
                "max_top3_rc_sum_pct_synthetic": mx3,
                "slack_target_vol": eval_blob["slack"].get("target_vol"),
                "slack_mandate_max_dd_hist": eval_blob["slack"].get("mandate_max_dd_hist"),
                "slack_max_single_weight": eval_blob["slack"].get("max_single_asset_weight"),
                "weights_compact": json.dumps(
                    {k: round(float(v), 6) for k, v in sorted(res.weights.items()) if float(v) > 1e-12}
                ),
            }
        )
        rows_out.append(base_row)

    winner = _pick_winner_rows(rows_out)
    feasible = bool(
        winner is not None and winner.get("mandate_classification") in ("pass", "borderline")
    )

    summary = {
        "generated_at": run_started,
        "analysis_end": analysis_end_str,
        "primary_window_months": primary_window,
        "lambda_grid": list(lam_grid),
        "mandate_targets": {
            "target_vol_annual": base_cfg.target_vol_annual,
            "target_max_drawdown_pct": base_cfg.target_max_drawdown_pct,
            "max_single_security_weight_pct": base_cfg.max_single_security_weight_pct,
            "min_single_security_weight_pct": base_cfg.min_single_security_weight_pct,
        },
        "robust_mv_calibration_yaml": calibration_limits or {},
        "enforce_synthetic_loss_vs_mandate_dd": enforce_syn,
        "feasible_lambda_found": feasible,
        "selected_lambda": winner.get("robust_mv_lambda") if winner else None,
        "selected_mandate_classification": winner.get("mandate_classification") if winner else None,
        "rows": rows_out,
    }

    if feasible:
        summary["selection_note"] = (
            "Lowest λ among mandate-eligible (pass or borderline), tie-break highest 10Y CAGR."
        )
    else:
        diag = build_no_feasible_lambda_diagnostic(lambda_grid=list(lam_grid), winner=winner)
        summary["no_feasible_lambda_diagnostic"] = diag
        summary["selection_note"] = diag["narrative"]
        logger.warning("Robust MV λ calibration: %s", diag["narrative"])

    if winner and winner.get("build_status") in ("OK", "APPROXIMATE"):
        lam_sel = float(winner["robust_mv_lambda"])
        cfg_win = replace(base_cfg, robust_mv_lambda=lam_sel)
        win_build = build_robust_mean_variance_constrained(
            cfg_win,
            monthly_returns,
            analysis_end_str,
            primary_window,
        )
        bind_eval = None
        if win_build.status not in ("OK", "APPROXIMATE"):
            logger.warning(
                "Robust MV rebuild at selected λ=%s failed (%s); skipping selected_portfolio report bundle.",
                lam_sel,
                win_build.status,
            )
        if win_build.status in ("OK", "APPROXIMATE"):
            mandate_chk_w = mandate_max_drawdown_full_history_check(
                monthly_returns,
                win_build.weights,
                abs(cfg_win.target_max_drawdown_pct) if cfg_win.target_max_drawdown_pct is not None else None,
            )
            pm_w, meta_w = run_portfolio_report_for_weights(
                cfg_win,
                win_build.weights,
                run_timestamp=datetime.now().isoformat(),
                output_dir_csv=root / "selected_portfolio" / "results_csv",
                output_dir_final=root / "selected_portfolio",
                backtest_mode_override=getattr(cfg_win, "backtest_mode", "dynamic_nan_safe"),
                no_cache=False,
            )
            stress_w = meta_w.get("stress_report") or {}
            bind_eval = classify_robust_mv_mandate(
                portfolio_valid=meta_w.get("portfolio_valid"),
                target_vol_annual=cfg_win.target_vol_annual,
                vol_annual_10y=_finite_float(pm_w.get("vol_annual")) if pm_w else None,
                target_max_drawdown_pct=cfg_win.target_max_drawdown_pct,
                mandate_max_drawdown_realized=(
                    float(mandate_chk_w["max_drawdown_realized"])
                    if mandate_chk_w.get("max_drawdown_realized") is not None
                    else None
                ),
                max_single_security_weight_pct=cfg_win.max_single_security_weight_pct,
                weights=win_build.weights,
                stress_report=stress_w,
                calibration_limits=calibration_limits,
                enforce_synthetic_vs_mandate_dd=enforce_syn,
            )
            summary["selected_binding_constraints"] = infer_binding_constraints(bind_eval)
            summary["selected_portfolio_metrics_10y"] = {k: _json_safe(pm_w.get(k)) for k in ("cagr", "vol_annual", "max_drawdown", "sharpe")}

            meta_export = robust_mean_variance_baseline_metadata_export(win_build.diagnostics)
            sel_dir = root / "selected_portfolio"
            sel_dir.mkdir(parents=True, exist_ok=True)
            with open(sel_dir / "weights.json", "w", encoding="utf-8") as f:
                json.dump(win_build.weights, f, indent=2, ensure_ascii=False)
            with open(sel_dir / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
                json.dump(meta_export, f, indent=2, ensure_ascii=False)

            rc_series = None
            try:
                cols = [t for t in cfg_win.tickers if t in monthly_returns.columns]
                ret_slice = slice_window(monthly_returns[cols], analysis_end_str, primary_window).dropna(how="all")
                if len(ret_slice) >= 2:
                    w_dict = {t: float(win_build.weights.get(t, 0.0)) for t in cols}
                    weights_df = pd.DataFrame(
                        index=ret_slice.index, data={t: w_dict.get(t, 0.0) for t in cols}
                    )
                    rc_series = rc_vol_window(ret_slice, weights_df, ddof=1)
            except Exception as e:
                logger.warning("RC_vol for selected portfolio weights.txt skipped: %s", e)

            export_baseline_weights_txt(
                win_build.weights,
                rc_series=rc_series,
                label=BASELINE_ROBUST_MV_CONSTRAINED_LABEL,
                output_dir=sel_dir,
            )

        with open(root / "selected_weights.json", "w", encoding="utf-8") as f:
            json.dump(win_build.weights if win_build.status in ("OK", "APPROXIMATE") else {}, f, indent=2)
        with open(root / "selected_lambda.txt", "w", encoding="utf-8") as f:
            f.write(str(winner.get("robust_mv_lambda")))
    else:
        with open(root / "selected_weights.json", "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        Path(root / "selected_lambda.txt").write_text("", encoding="utf-8")

    csv_path = root / "robust_mv_lambda_calibration.csv"
    if rows_out:
        fields = list(rows_out[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in rows_out:
                w.writerow(r)

    json_path = root / "robust_mv_lambda_calibration_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    if not args.keep_scratch:
        shutil.rmtree(scratch_root, ignore_errors=True)

    logger.info("Wrote %s, %s, selected_* under %s", csv_path, json_path, root)

    try:
        from src.pdf_reports import try_rebuild_pdfs_after_variant

        try_rebuild_pdfs_after_variant(logger=logger)
    except Exception as e:
        logger.warning("PDF suite rebuild skipped: %s", e)


if __name__ == "__main__":
    main()
