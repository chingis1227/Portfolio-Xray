"""
Run the full metrics / stress / reporting pipeline for the latest robust scenario
optimization weights as a separate portfolio variant (does not touch policy weights).

Reads ``Main portfolio/robust_optimization_weights.json`` and writes all artifacts under
``robust scenario portfolio/``, same contract as Equal-Weight / Risk-Parity baselines.
"""
from legacy.runners._paths import REPO_ROOT

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import yaml

from run_report import run_portfolio_report_for_weights
from src.config import load_validated_config
from src.config_schema import ConfigValidationError
from src.utils import logger, setup_logging

VARIANT_LABEL = "Robust Scenario Portfolio (scenario optimization v1)"
DEFAULT_WEIGHTS_REL = Path("Main portfolio") / "robust_optimization_weights.json"
OUT_DIR_NAME = "robust scenario portfolio"


def _load_robust_optimization_summary(weights_path: Path) -> dict:
    summary_path = weights_path.parent / "robust_optimization_v1_summary.json"
    if not summary_path.is_file():
        return {}
    with summary_path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return raw if isinstance(raw, dict) else {}


def _robust_scenario_optimizer_run_metadata(
    *,
    weights_path: Path,
    weights: dict[str, float],
    summary: dict,
) -> dict:
    solver = summary.get("solver") if isinstance(summary.get("solver"), dict) else {}
    sorted_returns = summary.get("sorted_scenario_returns_at_optimum")
    scenario_count = len(sorted_returns) if isinstance(sorted_returns, list) else None
    return {
        "schema_version": "robust_scenario_optimizer_run_metadata_v1",
        "optimizer_role": "candidate_only",
        "candidate_only": True,
        "method_id": "robust_scenario_optimization_v1",
        "entrypoint": "run_robust_scenario_optimization.py",
        "objective": {
            "objective_mode": summary.get("objective_mode"),
            "expected_returns_used": True,
            "scenario_returns_used": True,
        },
        "input_window": {
            "analysis_end": summary.get("analysis_end"),
            "scenario_count": scenario_count,
            "scenario_source": str(
                (weights_path.parent / "scenario_library_normalized.json").resolve()
            ),
            "stress_source": str((weights_path.parent / "stress_report.json").resolve()),
        },
        "expected_return": {
            "used": True,
            "method": "base_historical.expected_returns_by_asset plus scenario coefficient matrix",
        },
        "covariance": {
            "method": "base_historical.asset_covariance_monthly_equivalent",
        },
        "eligible_universe": sorted(weights.keys()),
        "constraints": {
            "active_constraints": ["long_only", "fully_invested", "box_bounds"],
            "long_only": True,
            "fully_invested": True,
            "box_bounds": True,
        },
        "parameters": {
            "lambdas": summary.get("lambdas") or {},
        },
        "solver": {
            "name": solver.get("name"),
            "success": solver.get("success"),
            "status": solver.get("status"),
            "raw_status": solver.get("raw_status"),
            "message": solver.get("message") or summary.get("optimizer_message"),
            "iterations": solver.get("iterations"),
            "multi_start_count": solver.get("multi_start_count"),
            "fallback_used": bool(solver.get("fallback_used", False)),
            "fallback_reason": solver.get("fallback_reason"),
            "optimization_quality_status": solver.get("optimization_quality_status")
            or summary.get("optimization_quality_status"),
        },
        "output_summary": {
            "weights_source": str(weights_path.resolve()),
            "lower_half_mean": summary.get("lower_half_mean"),
            "lower_half_k": summary.get("lower_half_k"),
            "base_expected_return_monthly": summary.get("base_expected_return_monthly"),
            "base_vol_monthly": summary.get("base_vol_monthly"),
            "percentile_diagnostics_only": summary.get("percentile_diagnostics_only"),
        },
    }


def _load_weights(path: Path) -> dict[str, float]:
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("Weights file must be a JSON object of ticker -> float")
    out: dict[str, float] = {}
    for k, v in raw.items():
        if k is None:
            continue
        out[str(k)] = float(v)
    return out


def _validate_weights(w: dict[str, float]) -> None:
    for t, x in w.items():
        if x < -1e-12:
            raise ValueError(f"Short weight not allowed: {t}={x}")
        if x > 1.0 + 1e-6:
            raise ValueError(f"Weight > 1: {t}={x}")
    s = sum(w.values())
    if abs(s - 1.0) > 1e-5:
        raise ValueError(f"Weights must sum to 1.0, got {s}")


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description=VARIANT_LABEL)
    parser.add_argument(
        "--weights",
        type=Path,
        default=None,
        help="Path to robust weights JSON (default: Main portfolio/robust_optimization_weights.json)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Pass through to the report pipeline data loader",
    )
    args = parser.parse_args()

    project_root = REPO_ROOT
    weights_path = args.weights or (project_root / DEFAULT_WEIGHTS_REL)
    if not weights_path.is_file():
        logger.error("Weights file not found: %s", weights_path)
        raise SystemExit(1)

    try:
        cfg = load_validated_config()
    except ConfigValidationError as e:
        logger.error("Configuration validation failed: %s", e)
        raise SystemExit(1)

    weights = _load_weights(weights_path)
    _validate_weights(weights)
    robust_summary = _load_robust_optimization_summary(weights_path)

    out_dir = project_root / OUT_DIR_NAME
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "robust_scenario_weights.json", "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, ensure_ascii=False)

    with open(out_dir / "portfolio_weights.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(weights, f, sort_keys=True, allow_unicode=True)

    meta_pre = {
        "variant": "robust_scenario_portfolio_v1",
        "label": VARIANT_LABEL,
        "weights_source": str(weights_path.resolve()),
        "total_weight_sum": round(sum(weights.values()), 10),
        "long_only": True,
    }
    if robust_summary:
        meta_pre["optimizer_run_metadata"] = _robust_scenario_optimizer_run_metadata(
            weights_path=weights_path,
            weights=weights,
            summary=robust_summary,
        )
    with open(out_dir / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta_pre, f, indent=2, ensure_ascii=False)

    logger.info("%s — sum(weights)=%s, output %s", VARIANT_LABEL, sum(weights.values()), out_dir)

    output_dir_csv = out_dir / "results_csv"
    output_dir_csv.mkdir(parents=True, exist_ok=True)

    run_timestamp = datetime.now().isoformat()
    pm_summary, meta = run_portfolio_report_for_weights(
        cfg,
        weights,
        run_timestamp=run_timestamp,
        output_dir_csv=output_dir_csv,
        output_dir_final=out_dir,
        backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
        no_cache=bool(args.no_cache),
    )

    stress_report = meta.get("stress_report") or {}
    summary = {
        "portfolio_type": VARIANT_LABEL,
        "status": "OK",
        "robust_scenario_metadata": meta_pre,
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code"),
        "portfolio_valid": meta.get("portfolio_valid"),
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    lines = [
        VARIANT_LABEL,
        "=" * 70,
        f"Weights source: {weights_path}",
        f"Stress status: {stress_report.get('status', 'N/A')}",
        "",
    ]
    if pm_summary:
        lines.append(
            f"CAGR (10y window in summary): {pm_summary.get('cagr')}  "
            f"Vol: {pm_summary.get('vol_annual')}  MaxDD: {pm_summary.get('max_drawdown')}"
        )
    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    try:
        import subprocess
        import sys

        cv = project_root / "run_compare_variants.py"
        if cv.is_file():
            subprocess.run([sys.executable, str(cv)], cwd=str(project_root), check=False)
    except Exception as e:
        logger.warning("Comparison refresh skipped or failed: %s", e)

    from src.variant_builder_runtime import maybe_rebuild_pdfs_only

    maybe_rebuild_pdfs_only(logger=logger)

    print(f"Robust scenario portfolio report written under {out_dir}")


if __name__ == "__main__":
    main()
