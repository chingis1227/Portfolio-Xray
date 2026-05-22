"""Synthetic workspace fixtures for offline MVP pipeline smoke tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.analysis_setup import build_analysis_setup
from src.config_schema import validate_config
from src.input_assumptions import build_input_assumptions_from_analysis_setup
from src.portfolio_xray import PORTFOLIO_XRAY_VERSION, XRAY_SECTION_KEYS
from src.snapshot import compute_candidate_config_fingerprint

DEFAULT_ANALYSIS_END = "2026-04-30"
FIVE_TICKER_MVP_TICKERS = ["VOO", "BND", "GLD", "QQQ", "VNQ"]
FIVE_TICKER_MVP_WEIGHTS = {
    "VOO": "35%",
    "BND": "25%",
    "GLD": "15%",
    "QQQ": "15%",
    "VNQ": "10%",
}


def snapshot_10y(
    metrics: dict[str, Any],
    *,
    rc_asset: list[dict[str, Any]] | None = None,
    final_weights_total: dict[str, float] | None = None,
    stress_overall: str = "PASS",
    candidate_config_fingerprint: str | None = None,
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
    if candidate_config_fingerprint is not None:
        snap["candidate_config_fingerprint"] = candidate_config_fingerprint
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
    final_weights_total: dict[str, float] | None = None,
) -> Path:
    folder = root / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    weights = final_weights_total or {"VOO": 0.5, "BND": 0.5}
    write_json(
        folder / "snapshot_10y.json",
        snapshot_10y(
            metrics,
            rc_asset=_rc_rows(weights),
            final_weights_total=weights,
        ),
    )
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


def five_ticker_mvp_config_dict(*, output_dir_final: str = "Main portfolio") -> dict[str, Any]:
    return {
        "investor_currency": "USD",
        "analysis_mode": "optimize_from_universe",
        "output_dir_final": output_dir_final,
        "tickers": list(FIVE_TICKER_MVP_TICKERS),
        "analysis_subject": {
            "type": "current_portfolio",
            "display_name": "Five ticker current portfolio",
            "weights": dict(FIVE_TICKER_MVP_WEIGHTS),
        },
    }


def minimal_blocks_1_5_stress_report() -> dict[str, Any]:
    return {
        "schema_version": "stress_report_v1",
        "analysis_end": DEFAULT_ANALYSIS_END,
        "stress_scorecard_v1": {
            "overall_status": "PASS",
            "score": 82,
            "worst_scenario_id": "equity_shock",
        },
        "stress_conclusions": [
            {
                "severity": "info",
                "message": "Offline smoke fixture stress diagnostics are present.",
            }
        ],
        "historical_methodology": {
            "schema_version": "historical_methodology_v1",
            "method": "offline_fixture",
            "episodes_evaluated": 1,
        },
        "hedge_gap_analysis": {
            "status": "available",
            "aggregate": {"hedge_gap_score": 0.18},
            "by_risk_type": [],
        },
        "scenario_results": [
            {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True}
        ],
        "historical_episodes": [
            {"episode_id": "global_financial_crisis", "portfolio_pnl_pct": -0.12}
        ],
    }


def minimal_blocks_1_5_portfolio_xray() -> dict[str, Any]:
    return {
        "version": PORTFOLIO_XRAY_VERSION,
        "diagnostic_only": True,
        "sections": {
            key: {"status": "available", "data_sources_used": ["offline_smoke_fixture"]}
            for key in XRAY_SECTION_KEYS
        },
    }


def _rc_rows(weights: dict[str, float]) -> list[dict[str, Any]]:
    return [{"ticker": ticker, "rc_pct": weight} for ticker, weight in weights.items()]


def _decimal_five_ticker_weights() -> dict[str, float]:
    cfg = validate_config(five_ticker_mvp_config_dict())
    return {str(k): float(v) for k, v in (cfg.weights or {}).items()}


def _seed_candidate_snapshot(
    root: Path,
    folder_name: str,
    *,
    metrics: dict[str, Any],
    weights: dict[str, float],
    config_fingerprint: str,
) -> None:
    folder = root / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    write_json(
        folder / "snapshot_10y.json",
        snapshot_10y(
            metrics,
            rc_asset=_rc_rows(weights),
            final_weights_total=weights,
            candidate_config_fingerprint=config_fingerprint,
        ),
    )


def seed_blocks_1_5_mvp_smoke_workspace(root: Path, cfg: Any) -> dict[str, Any]:
    """Seed an offline five-ticker Blocks 1-5 workspace with current factory evidence."""
    from src.candidate_factory import CORE_V1_CANDIDATE_ORDER, registry_row

    output_dir_final = str(getattr(cfg, "output_dir_final", "Main portfolio"))
    main = root / output_dir_final
    subject = main / "analysis_subject"
    weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    config_fingerprint = compute_candidate_config_fingerprint(cfg)
    setup = build_analysis_setup(
        cfg,
        portfolio_weights=weights,
        weights_source=cfg.weights_source,
        portfolio_role_override="analysis_subject",
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        analysis_end=DEFAULT_ANALYSIS_END,
        windows_months=[36, 60, 120],
        returns_frequency="monthly",
        periods_per_year=12,
        run_context="report",
    )

    write_json(
        subject / "run_metadata.json",
        {
            "run_info": {"analysis_end_date": DEFAULT_ANALYSIS_END},
            "portfolio_valid": True,
            "analysis_setup": setup,
            "input_assumptions": build_input_assumptions_from_analysis_setup(setup),
        },
    )
    write_json(
        subject / "snapshot_10y.json",
        snapshot_10y(
            {"cagr": 0.062, "vol_annual": 0.128, "max_drawdown": -0.22, "sharpe": 0.39},
            rc_asset=_rc_rows(weights),
            final_weights_total=weights,
            candidate_config_fingerprint=config_fingerprint,
        ),
    )
    write_json(subject / "stress_report.json", minimal_blocks_1_5_stress_report())
    write_json(subject / "portfolio_xray.json", minimal_blocks_1_5_portfolio_xray())

    candidate_weights = _decimal_five_ticker_weights()
    candidate_metrics = {
        "equal_weight": {"cagr": 0.071, "vol_annual": 0.116, "max_drawdown": -0.18, "sharpe": 0.48},
        "risk_parity": {"cagr": 0.069, "vol_annual": 0.101, "max_drawdown": -0.15, "sharpe": 0.55},
        "equal_weight_by_asset_class": {"cagr": 0.068, "vol_annual": 0.112, "max_drawdown": -0.17, "sharpe": 0.47},
        "risk_budget_by_asset": {"cagr": 0.073, "vol_annual": 0.109, "max_drawdown": -0.16, "sharpe": 0.57},
        "risk_budget_by_asset_class": {"cagr": 0.072, "vol_annual": 0.107, "max_drawdown": -0.155, "sharpe": 0.56},
        "hierarchical_risk_parity": {"cagr": 0.07, "vol_annual": 0.104, "max_drawdown": -0.152, "sharpe": 0.54},
    }
    steps: list[dict[str, Any]] = []
    for candidate_id in CORE_V1_CANDIDATE_ORDER:
        row = registry_row(candidate_id) or {}
        artifact_root = str(row.get("artifact_root") or candidate_id)
        _seed_candidate_snapshot(
            root,
            artifact_root,
            metrics=candidate_metrics[candidate_id],
            weights=candidate_weights,
            config_fingerprint=config_fingerprint,
        )
        steps.append(
            {
                "candidate_id": candidate_id,
                "display_name": row.get("display_name"),
                "role": row.get("role"),
                "artifact_root": artifact_root,
                "status": "succeeded",
                "entry_commands": [f"python {candidate_id}.py"],
                "exit_code": 0,
                "duration_seconds": 0.01,
                "reason_code": None,
                "message": None,
                "expected_analysis_end": DEFAULT_ANALYSIS_END,
                "snapshot_analysis_end": DEFAULT_ANALYSIS_END,
                "expected_config_fingerprint": config_fingerprint,
                "snapshot_config_fingerprint": config_fingerprint,
                "freshness_status": "fresh",
            }
        )

    write_json(
        main / "candidate_factory_run.json",
        {
            "schema_version": "candidate_factory_run_v1",
            "diagnostic_only": True,
            "generated_at": "2026-05-21T12:00:00+00:00",
            "factory_profile_id": "core_v1",
            "project_root": ".",
            "output_dir_final": output_dir_final,
            "config_path": "config.yml",
            "analysis_end": DEFAULT_ANALYSIS_END,
            "config_fingerprint": config_fingerprint,
            "options": {
                "skip_existing": True,
                "force": False,
                "fail_fast": False,
                "resume": False,
                "then_compare": True,
            },
            "steps": steps,
            "summary": {
                "total": len(steps),
                "succeeded": len(steps),
                "failed": 0,
                "skipped_existing": 0,
                "skipped_dependency": 0,
            },
            "warnings": [],
            "next_recommended_command": "python run_compare_variants.py",
        },
    )
    return {
        "main_dir": main,
        "analysis_subject_dir": subject,
        "analysis_setup": setup,
        "config_fingerprint": config_fingerprint,
        "core_candidate_ids": list(CORE_V1_CANDIDATE_ORDER),
    }


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
