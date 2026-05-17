from __future__ import annotations

import json
from pathlib import Path

from src.decision_package_reporting import (
    REPORT_TXT_MARKER,
    SCHEMA_VERSION,
    build_decision_package_report,
    build_decision_package_report_md,
    write_decision_package_reporting_outputs,
)
from src.selection_engine import rationale_text_is_client_safe


def _comparison() -> dict:
    return {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": "2025-12-31",
        "investor_currency": "USD",
        "output_dir_final": "Main portfolio",
        "candidates": [
            {
                "candidate_id": "policy",
                "display_name": "Policy (Optimized)",
                "role": "policy",
                "status": "available",
                "metrics": {
                    "10y": {
                        "cagr": 0.08,
                        "vol_annual": 0.12,
                        "max_drawdown": -0.2,
                    }
                },
                "stress": {"overall": "DIAG_PASS"},
                "mandate": {"portfolio_valid": True},
            },
            {
                "candidate_id": "current",
                "display_name": "Current Portfolio",
                "role": "user_current",
                "status": "available",
                "metrics": {
                    "10y": {
                        "cagr": 0.07,
                        "vol_annual": 0.14,
                        "max_drawdown": -0.24,
                    }
                },
                "stress": {"overall": "DIAG_PASS"},
                "mandate": {"portfolio_valid": True},
            },
        ],
    }


def _health_robust() -> tuple[dict, dict]:
    rows = [
        {
            "candidate_id": "policy",
            "total_score": 72,
            "score_status": "scored",
            "health_rank": 1,
            "robustness_rank": 1,
        },
        {
            "candidate_id": "current",
            "total_score": 65,
            "score_status": "scored",
            "health_rank": 2,
            "robustness_rank": 2,
        },
    ]
    health = {
        "schema_version": "portfolio_health_score_v1",
        "candidates": [
            {k: v for k, v in r.items() if k != "robustness_rank"} for r in rows
        ],
    }
    robust = {
        "schema_version": "robustness_scorecard_v1",
        "candidates": [
            {k: v for k, v in r.items() if k != "health_rank"} for r in rows
        ],
    }
    return health, robust


def _selection() -> dict:
    return {
        "schema_version": "selection_decision_v1",
        "decision_status": "no_material_rebalance",
        "favored_candidate_id": "policy",
        "favored_display_name": "Policy (Optimized)",
        "rationale": {
            "summary": "Policy profile is favored; move from current is below review thresholds."
        },
        "no_trade": {
            "evaluated": True,
            "summary": "Health and robustness deltas are below thresholds.",
        },
        "warnings": [],
    }


def _action() -> dict:
    return {
        "schema_version": "action_plan_v1",
        "action_status": "no_trades_no_material_rebalance",
        "no_trades_reason": "No trades: no material rebalance versus current weights.",
        "turnover_half_sum_pct": 2.5,
        "trades": [],
    }


def _monitoring() -> dict:
    return {
        "schema_version": "monitoring_diff_v1",
        "diff_status": "no_prior_snapshot",
        "summary_plain_en": "First analysis snapshot stored for future comparison.",
    }


def _journal() -> dict:
    return {
        "schema_version": "decision_journal_v1",
        "analysis_end": "2025-12-31",
    }


def test_build_decision_package_report_sections() -> None:
    health, robust = _health_robust()
    doc = build_decision_package_report(
        comparison=_comparison(),
        health=health,
        robustness=robust,
        selection=_selection(),
        action=_action(),
        monitoring_diff=_monitoring(),
        decision_journal=_journal(),
    )
    assert doc["schema_version"] == SCHEMA_VERSION
    assert doc["sections"]["comparison"]["availability"] == "available"
    text = doc["summary_plain_en"]
    assert "Policy (Optimized)" in text
    assert "No material rebalance" in text
    assert "First analysis snapshot" in text
    assert rationale_text_is_client_safe(text)


def test_missing_artifacts_marked_not_available() -> None:
    doc = build_decision_package_report(
        comparison=None,
        health=None,
        robustness=None,
        selection=None,
        action=None,
        monitoring_diff=None,
        decision_journal=None,
    )
    assert all(
        s["availability"] == "not_available" for s in doc["sections"].values()
    )
    assert "Not available" in doc["summary_plain_en"]


def test_write_outputs_and_append_report_txt(tmp_path: Path) -> None:
    from src.config_schema import validate_config

    out = tmp_path / "Main portfolio"
    out.mkdir()
    (out / "report.txt").write_text("Existing report body\n", encoding="utf-8")

    health, robust = _health_robust()
    comp = _comparison()
    for name, data in (
        ("candidate_comparison.json", comp),
        ("portfolio_health_score.json", health),
        ("robustness_scorecard.json", robust),
        ("selection_decision.json", _selection()),
        ("action_plan.json", _action()),
        ("monitoring_diff.json", _monitoring()),
        ("decision_journal.json", _journal()),
    ):
        (out / name).write_text(json.dumps(data), encoding="utf-8")

    cfg = validate_config(
        {
            "output_dir_final": out.name,
            "investor_currency": "USD",
            "tickers": ["VOO"],
        }
    )
    paths = write_decision_package_reporting_outputs(
        cfg, project_root=tmp_path, comparison=comp
    )
    assert paths["decision_package_summary_txt"].is_file()
    assert paths["decision_package_summary_json"].is_file()
    report = (out / "report.txt").read_text(encoding="utf-8")
    assert REPORT_TXT_MARKER in report
    assert "Decision package summary" in report

    md = build_decision_package_report_md(
        paths["decision_package_summary_txt"].read_text(encoding="utf-8"),
        analysis_end="2025-12-31",
    )
    assert "# Decision Package Summary" in md
