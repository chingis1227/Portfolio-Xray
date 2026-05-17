from __future__ import annotations

import json
from pathlib import Path

from src.candidate_comparison import (
    CURRENT_SIDECAR_SUBDIR,
    build_candidate_comparison,
    current_sidecar_dir,
    resolve_current_artifact_folder,
    sidecar_meets_minimum,
)
from src.config_schema import validate_config
from src.current_vs_policy import (
    SCHEMA_VERSION,
    build_current_vs_policy_status,
    write_current_vs_policy_status_outputs,
)
from src.decision_package_reporting import build_decision_package_summary_lines
from src.selection_engine import build_selection_decision


def _snapshot_10y(
    metrics: dict,
    *,
    final_weights_total: dict | None = None,
) -> dict:
    snap = {
        "analysis_end": "2026-04-30",
        "window_label": "10y",
        "metrics": metrics,
        "stress_suite_results": {
            "overall": "PASS",
            "fail_reason_code": None,
            "failed_scenario": None,
            "scenarios": [{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True}],
        },
        "constraints_status": {"target_vol": "PASS", "max_dd": "PASS"},
    }
    if final_weights_total is not None:
        snap["final_weights_total"] = final_weights_total
    return snap


def _run_metadata(portfolio_role: str) -> dict:
    return {
        "run_info": {"analysis_end_date": "2026-04-30"},
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


def _write_policy_main(main: Path, *, policy_weights: dict[str, float]) -> None:
    main.mkdir(parents=True, exist_ok=True)
    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.09, "vol_annual": 0.11, "max_drawdown": -0.15, "sharpe": 0.6},
                final_weights_total=policy_weights,
            ),
            f,
        )
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("generated_policy_portfolio"), f)


def _write_current_sidecar(sidecar: Path, *, current_weights: dict[str, float]) -> None:
    sidecar.mkdir(parents=True, exist_ok=True)
    with open(sidecar / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.065, "vol_annual": 0.09, "max_drawdown": -0.18, "sharpe": 0.5},
                final_weights_total=current_weights,
            ),
            f,
        )
    with open(sidecar / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("user_current_portfolio"), f)


def test_sidecar_meets_minimum_requires_role() -> None:
    sidecar = Path("/tmp/x")  # not used for is_file when empty
    assert sidecar_meets_minimum(sidecar) is False


def test_combined_context_both_available(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    policy_weights = {"VOO": 0.5, "BND": 0.5}
    current_weights = {"VOO": 0.6, "BND": 0.4}
    _write_policy_main(main, policy_weights=policy_weights)
    _write_current_sidecar(main / CURRENT_SIDECAR_SUBDIR, current_weights=current_weights)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "current_weights": current_weights,
            "tickers": ["VOO", "BND"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    pol = next(c for c in doc["candidates"] if c["candidate_id"] == "policy")
    cur = next(c for c in doc["candidates"] if c["candidate_id"] == "current")
    assert pol["status"] in ("available", "degraded")
    assert cur["status"] in ("available", "degraded")
    assert cur["artifact_root"].endswith("current_portfolio")
    assert doc["analysis_setup_summary"].get("current_materialization_root") == (
        "Main portfolio/current_portfolio"
    )

    status = build_current_vs_policy_status(doc, cfg, project_root=tmp_path)
    assert status["schema_version"] == SCHEMA_VERSION
    assert status["workflow_profile"] == "combined_current_vs_policy"
    assert status["combined_context_complete"] is True
    assert status["no_trade_actionable"] is True
    assert status["skip_reason"] is None


def test_current_weights_without_sidecar(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    _write_policy_main(main, policy_weights={"VOO": 0.5, "BND": 0.5})

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "current_weights": {"VOO": 0.6, "BND": 0.4},
            "tickers": ["VOO", "BND"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    cur = next(c for c in doc["candidates"] if c["candidate_id"] == "current")
    assert cur["status"] == "unavailable"
    assert cur["unavailable_reason"] == "missing_current_report"

    status = build_current_vs_policy_status(doc, cfg, project_root=tmp_path)
    assert status["no_trade_actionable"] is False
    assert status["skip_reason"] == "current_not_materialized"
    assert "materialize" in status["user_message_en"].lower()


def test_policy_only_no_current_weights(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    _write_policy_main(main, policy_weights={"VOO": 1.0})

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    status = build_current_vs_policy_status(doc, cfg, project_root=tmp_path)
    assert status["workflow_profile"] == "policy_only"
    assert status["no_trade_actionable"] is False
    assert status["skip_reason"] == "current_not_configured"


def test_main_policy_snapshot_unchanged_when_sidecar_added(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    policy_weights = {"VOO": 0.7, "BND": 0.3}
    _write_policy_main(main, policy_weights=policy_weights)
    before = json.loads((main / "snapshot_10y.json").read_text(encoding="utf-8"))

    _write_current_sidecar(main / CURRENT_SIDECAR_SUBDIR, current_weights={"VOO": 0.2, "BND": 0.8})

    after = json.loads((main / "snapshot_10y.json").read_text(encoding="utf-8"))
    assert after["final_weights_total"] == before["final_weights_total"] == policy_weights


def test_resolve_current_artifact_folder_prefers_sidecar(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    _write_policy_main(main, policy_weights={"VOO": 0.5, "BND": 0.5})
    _write_current_sidecar(main / CURRENT_SIDECAR_SUBDIR, current_weights={"VOO": 0.6, "BND": 0.4})
    folder, root = resolve_current_artifact_folder(
        output_dir_final=main,
        output_dir_final_rel="Main portfolio",
        analysis_mode="optimize_from_universe",
    )
    assert folder == current_sidecar_dir(main)
    assert root == "Main portfolio/current_portfolio"


def test_selection_warns_no_trade_not_actionable() -> None:
    comp = {
        "analysis_end": "2026-04-30",
        "candidates": [
            {
                "candidate_id": "policy",
                "display_name": "Policy Portfolio",
                "status": "available",
                "artifact_root": "Main portfolio",
                "metrics": {"10y": {"max_drawdown": -0.1}},
            },
            {
                "candidate_id": "current",
                "display_name": "Current Portfolio",
                "status": "unavailable",
                "unavailable_reason": "missing_current_report",
                "artifact_root": "Main portfolio/current_portfolio",
            },
            {
                "candidate_id": "equal_weight",
                "display_name": "Equal-Weight",
                "status": "available",
                "artifact_root": "equal-weight portfolio",
                "metrics": {"10y": {"max_drawdown": -0.12}},
            },
        ],
    }
    health = {
        "candidates": [
            {"candidate_id": "policy", "total_score": 70, "health_rank": 1, "score_status": "scored"},
            {"candidate_id": "equal_weight", "total_score": 55, "health_rank": 2, "score_status": "scored"},
        ]
    }
    robust = {
        "candidates": [
            {"candidate_id": "policy", "total_score": 68, "robustness_rank": 1, "score_status": "scored"},
            {"candidate_id": "equal_weight", "total_score": 50, "robustness_rank": 2, "score_status": "scored"},
        ]
    }
    doc = build_selection_decision(comp, health=health, robustness=robust)
    assert doc.get("no_trade") is None
    assert "no_trade_not_actionable" in doc.get("warnings", [])


def test_decision_package_skips_false_no_trade_headline() -> None:
    lines = build_decision_package_summary_lines(
        comparison=None,
        health=None,
        robustness=None,
        selection={
            "decision_status": "selected_candidate",
            "favored_candidate_id": "policy",
            "favored_display_name": "Policy Portfolio",
            "rationale": {"summary": "Favored profile: Policy Portfolio for this comparison."},
            "no_trade": None,
        },
        action=None,
        monitoring_diff=None,
        decision_journal=None,
        workflow_status={
            "no_trade_actionable": False,
            "user_message_en": "Current weights are configured but not materialized.",
        },
    )
    text = "\n".join(lines)
    assert "No material rebalance suggested versus current weights" not in text
    assert "not materialized" in text.lower()


def test_write_status_outputs(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    _write_policy_main(main, policy_weights={"VOO": 0.5, "BND": 0.5})
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    paths = write_current_vs_policy_status_outputs(cfg, doc, project_root=tmp_path)
    assert paths["current_vs_policy_status_json"].is_file()
    with open(paths["current_vs_policy_status_json"], encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["schema_version"] == SCHEMA_VERSION
