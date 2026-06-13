"""
View After Optimization — run tilt and write view_execution_report.json.

Per docs/docs/view_after_optimization_spec.md. Baseline weights from portfolio_weights.yml
(or config); optional baseline_rb/baseline_stress from run_result.json.

Usage:
  python run_view_after_optimization.py --asset VOO --delta 2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from legacy.runners._paths import REPO_ROOT

from src.config import (
    load_validated_config,
    load_weights_file,
    load_assets_metadata,
    resolve_cash_and_rf,
)
from src.config_schema import ConfigValidationError
from src.data_loader import load_monthly_data_shared
from src.view_after_optimization import run_view_after_optimization, write_view_execution_report
from src.utils import setup_logging, logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="View After Optimization — apply tilt and report")
    parser.add_argument("--asset", required=True, help="Ticker to increase (e.g. VOO, GLD)")
    parser.add_argument("--delta", type=float, default=5, choices=[1, 2, 5], help="Requested tilt size: 1, 2, or 5 pct")
    parser.add_argument("--weights-file", default=None, help="Path to baseline weights YAML (default: portfolio_weights.yml)")
    parser.add_argument("--run-result-file", default=None, help="Path to run_result.json for baseline RB/stress")
    parser.add_argument("--output", default=None, help="Output path for view_execution_report.json")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cache for data load")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging()

    try:
        cfg = load_validated_config()
    except ConfigValidationError as e:
        logger.error("Configuration error: %s", e)
        return 1

    # Baseline weights
    if args.weights_file:
        baseline_weights = load_weights_file(weights_path=args.weights_file)
    else:
        baseline_weights = load_weights_file(config_path=Path(cfg.config_path) if getattr(cfg, "config_path", None) else None)
    if not baseline_weights:
        # Fallback: config may have weights
        baseline_weights = getattr(cfg, "weights", None) or {}
    if not baseline_weights:
        logger.error("No base weights: provide --weights-file or run optimization (portfolio_weights.yml)")
        return 1

    if args.asset not in cfg.tickers and args.asset not in baseline_weights:
        logger.warning("Ticker %s is not in config/weights; tilt will still be applied to weights", args.asset)

    baseline_stress = None
    if args.run_result_file:
        p = Path(args.run_result_file)
        if p.is_file():
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            baseline_stress = data.get("stress_summary")

    # Load monthly returns
    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    assets_meta = load_assets_metadata()
    data = load_monthly_data_shared(
        tickers=cfg.tickers,
        benchmark_base_ticker=cfg.benchmark_base_ticker,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        investor_currency=cfg.investor_currency,
        windows_months=cfg.windows_months,
        assets_meta=assets_meta,
        no_cache=args.no_cache,
        local_benchmark_map=None,
        returns_frequency=getattr(cfg, "returns_frequency", None),
    )
    monthly_returns = data.monthly_returns
    if monthly_returns is None or monthly_returns.empty:
        logger.error("No monthly returns")
        return 1

    report = run_view_after_optimization(
        baseline_weights=baseline_weights,
        asset=args.asset,
        delta_choice_pct=float(args.delta),
        monthly_returns=monthly_returns,
        cash_proxy_ticker=cash_proxy_ticker,
        baseline_stress=baseline_stress,
        target_vol_annual=getattr(cfg, "target_vol_annual", None),
        target_max_drawdown_pct=getattr(cfg, "target_max_drawdown_pct", None),
        min_single_security_weight_pct=getattr(cfg, "min_single_security_weight_pct", 1.0) or 1.0,
        max_single_security_weight_pct=getattr(cfg, "max_single_security_weight_pct", None),
    )

    out_path = args.output
    if not out_path:
        out_path = Path.cwd() / "view_execution_report.json"
    write_view_execution_report(report, out_path)
    logger.info("Report written: %s", out_path)

    status = report.get("outcome_status", "TILT_REJECTED")
    print("\nView After Optimization: %s" % status)
    if report.get("stress_failure_code"):
        print("  Stress: %s" % report.get("stress_failure_code"))
    if report.get("broken_gate"):
        print("  Broken gate: %s" % report.get("broken_gate"))
    return 0 if status == "TILT_ACCEPTED" else 1


if __name__ == "__main__":
    sys.exit(main())
