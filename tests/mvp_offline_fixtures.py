"""Synthetic workspace fixtures for offline MVP pipeline smoke tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.config_schema import validate_config

DEFAULT_ANALYSIS_END = "2026-04-30"


def snapshot_10y(
    metrics: dict[str, Any],
    *,
    rc_asset: list[dict[str, Any]] | None = None,
    final_weights_total: dict[str, float] | None = None,
    stress_overall: str = "PASS",
) -> dict[str, Any]:
    snap: dict[str, Any] = {
        "analysis_end": DEFAULT_ANALYSIS_END,
        "window_label": "10y",
        "metrics": metrics,
        "stress_suite_results": {
            "overall": stress_overall,
            "fail_reason_code": None,
            "failed_scenario": None,
            "scenarios": [
                {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True}
            ],
        },
        "constraints_status": {"target_vol": "PASS", "max_dd": "PASS"},
    }
    if rc_asset is not None:
        snap["RC_asset"] = rc_asset
    if final_weights_total is not None:
        snap["final_weights_total"] = final_weights_total
    return snap


def run_metadata(portfolio_role: str = "generated_policy_portfolio") -> dict[str, Any]:
    return {
        "run_info": {"analysis_end_date": DEFAULT_ANALYSIS_END},
        "portfolio_valid": True,
        "analysis_setup": {
            "portfolio_input": {"source_analysis_mode": "optimize_from_universe"},
            "analysis_portfolio": {
                "portfolio_role": portfolio_role,
                "weight_source": "optimization_result_released",
                "recommendation_status": "generated_policy_output_released",
            },
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def seed_variant_snapshot(
    root: Path,
    folder_name: str,
    metrics: dict[str, Any],
    *,
    with_run_metadata: bool = False,
    portfolio_role: str = "generated_policy_portfolio",
) -> Path:
    folder = root / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    write_json(folder / "snapshot_10y.json", snapshot_10y(metrics))
    if with_run_metadata:
        write_json(folder / "run_metadata.json", run_metadata(portfolio_role))
    return folder


def seed_minimal_mvp_workspace(root: Path) -> Path:
    """Seed policy + legacy comparison variants with synthetic 10y snapshots only."""
    main = seed_variant_snapshot(
        root,
        "Main portfolio",
        {"cagr": 0.09, "vol_annual": 0.11, "max_drawdown": -0.15, "sharpe": 0.6},
        with_run_metadata=True,
    )
    seed_variant_snapshot(
        root,
        "equal-weight portfolio",
        {"cagr": 0.08, "vol_annual": 0.12, "max_drawdown": -0.2, "sharpe": 0.5},
    )
    seed_variant_snapshot(
        root,
        "risk parity portfolio",
        {"cagr": 0.075, "vol_annual": 0.105, "max_drawdown": -0.18, "sharpe": 0.55},
    )
    return main


def minimal_mvp_config_dict(*, output_dir_final: str = "Main portfolio") -> dict[str, Any]:
    return {
        "investor_currency": "USD",
        "analysis_mode": "optimize_from_universe",
        "output_dir_final": output_dir_final,
        "tickers": ["VOO", "BND"],
    }


def write_minimal_config_yaml(root: Path, name: str = "config_mvp_offline.yml") -> Path:
    path = root / name
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(minimal_mvp_config_dict(), f, allow_unicode=True, sort_keys=False)
    return path


def load_mvp_config(root: Path) -> Any:
    return validate_config(minimal_mvp_config_dict())


# (filename, expected schema_version)
MVP_DECISION_PACKAGE_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("candidate_comparison.json", "candidate_comparison_v1"),
    ("portfolio_health_score.json", "portfolio_health_score_v1"),
    ("robustness_scorecard.json", "robustness_scorecard_v1"),
    ("selection_decision.json", "selection_decision_v1"),
    ("current_vs_policy_status.json", "current_vs_policy_status_v1"),
    ("action_plan.json", "action_plan_v1"),
    ("monitoring_diff.json", "monitoring_diff_v1"),
    ("decision_journal.json", "decision_journal_v1"),
    ("decision_package_summary.json", "decision_package_report_v1"),
    ("tradeoff_explanation.json", "tradeoff_explanation_v1"),
    ("model_risk_diagnostics.json", "model_risk_diagnostics_v1"),
    ("assumption_sensitivity.json", "assumption_sensitivity_v1"),
    ("pareto_dominance.json", "pareto_dominance_v1"),
    ("regret_analysis.json", "regret_analysis_v1"),
)
