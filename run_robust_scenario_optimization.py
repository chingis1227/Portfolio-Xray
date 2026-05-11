#!/usr/bin/env python3
"""
Scenario-Based Robust Optimization v1 CLI.

Requires ``scenario_library_normalized.json`` (from ``run_report.py``) under ``output_dir_final``.
Does not run mandate gates or overwrite ``portfolio_weights.yml``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.config import load_validated_config, load_weights_file, resolve_cash_and_rf
from src.config_schema import ConfigValidationError
from src.optimization import MIN_WEIGHT_DEFAULT, _build_bounds, get_risk_portfolio_tickers
from src.robust_scenario_optimization import (
    OBJECTIVE_HYBRID_LEGACY,
    OBJECTIVE_LOWER_HALF_MEAN,
    OBJECTIVE_MAXIMIN,
    build_robust_optimization_inputs,
    export_robust_optimization_outputs,
    lower_half_mean,
    run_robust_scenario_optimization,
)
from src.utils import logger, setup_logging


def _comparison_metrics(weights_vec: np.ndarray, ticker_order: list[str], mu: np.ndarray, sigma: np.ndarray) -> dict[str, float]:
    w = np.asarray(weights_vec, dtype=float)
    return {
        "expected_return_monthly": round(float(mu @ w), 6),
        "vol_monthly": round(float(np.sqrt(max(w @ sigma @ w, 0.0))), 6),
    }


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser(description="Scenario-Based Robust Optimization v1")
    ap.add_argument("--config", type=str, default="config.yml", help="Path to config.yml")
    ap.add_argument(
        "--objective-mode",
        type=str,
        default=OBJECTIVE_LOWER_HALF_MEAN,
        choices=[OBJECTIVE_LOWER_HALF_MEAN, OBJECTIVE_MAXIMIN, OBJECTIVE_HYBRID_LEGACY],
    )
    ap.add_argument("--normalized-json", type=str, default=None, help="Override path to scenario_library_normalized.json")
    ap.add_argument("--output-dir", type=str, default=None, help="Directory for robust_optimization_* artifacts")
    args = ap.parse_args()

    try:
        cfg = load_validated_config(args.config)
    except ConfigValidationError as e:
        logger.error("Configuration validation failed: %s", e)
        raise SystemExit(1)

    rob = getattr(cfg, "robust_scenario_optimization", None) or {}
    final_dir = Path(args.output_dir or rob.get("output_dir") or cfg.output_dir_final)
    norm_path = Path(args.normalized_json or rob.get("normalized_json_path") or (final_dir / "scenario_library_normalized.json"))
    if not norm_path.is_file():
        logger.error("Missing %s — run run_report.py first.", norm_path)
        raise SystemExit(2)

    stress_path = final_dir / "stress_report.json"
    stress_report = None
    if stress_path.is_file():
        stress_report = json.loads(stress_path.read_text(encoding="utf-8"))

    normalized = json.loads(norm_path.read_text(encoding="utf-8"))

    cash_proxy, _rf = resolve_cash_and_rf(cfg)
    risk_tickers = get_risk_portfolio_tickers(list(cfg.tickers), cash_proxy)

    lam = dict(rob.get("lambdas") or {})
    try:
        inputs = build_robust_optimization_inputs(
            scenario_library_normalized=normalized,
            stress_report=stress_report,
            risk_tickers=risk_tickers,
            objective_mode=args.objective_mode,
            lambdas=lam,
        )
    except Exception as e:
        logger.error("Failed to build robust optimization inputs: %s", e)
        raise SystemExit(3)

    min_w = (
        float(cfg.min_single_security_weight_pct)
        if cfg.min_single_security_weight_pct is not None and cfg.min_single_security_weight_pct > 0
        else MIN_WEIGHT_DEFAULT
    )
    bounds = _build_bounds(
        inputs.ticker_order,
        len(inputs.ticker_order),
        min_w,
        cfg.max_single_security_weight_pct,
        None,
    )

    warm: list[np.ndarray] = []
    wpol = load_weights_file(config_path=args.config)
    if wpol:
        v = np.array([float(wpol.get(t, 0.0)) for t in inputs.ticker_order], dtype=float)
        s = float(v.sum())
        if s > 1e-12:
            warm.append(v / s)
    warm.append(np.ones(len(inputs.ticker_order)) / len(inputs.ticker_order))

    result = run_robust_scenario_optimization(inputs, bounds=bounds, warm_starts=warm)

    comparisons: dict[str, dict[str, float]] = {
        "robust_optimum": _comparison_metrics(result["weights_vec"], inputs.ticker_order, inputs.mu_base, inputs.Sigma_base),
    }
    if wpol:
        vw = np.array([float(wpol.get(t, 0.0)) for t in inputs.ticker_order], dtype=float)
        sw = float(vw.sum())
        if sw > 1e-12:
            vw = vw / sw
            comparisons["policy_weights_file"] = _comparison_metrics(vw, inputs.ticker_order, inputs.mu_base, inputs.Sigma_base)
            r_pol = inputs.C @ vw
            lh_pol, _, _ = lower_half_mean(r_pol)
            comparisons["policy_weights_file"]["lower_half_mean"] = round(float(lh_pol), 6)

    paths = export_robust_optimization_outputs(
        result,
        inputs,
        output_dir=final_dir,
        comparisons=comparisons,
    )
    logger.info("Robust scenario optimization v1 wrote: %s", paths)


if __name__ == "__main__":
    main()
