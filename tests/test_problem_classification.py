from __future__ import annotations

import json
from pathlib import Path

from src.problem_classification import (
    PROBLEM_CLASSIFICATION_VERSION,
    build_problem_classification,
    write_problem_classification_outputs,
)


def test_problem_classification_detects_xray_and_stress_problems() -> None:
    xray = {
        "sections": {
            "weakness_map": {
                "status": "available",
                "items": [
                    {
                        "type": "weakness",
                        "risk": "volatility_spike",
                        "severity": "high",
                        "confidence": "high",
                        "summary": "Large volatility sensitivity.",
                    },
                    {
                        "type": "weakness",
                        "risk": "hedge_gap",
                        "severity": "moderate",
                        "summary": "Weak hedge evidence.",
                    },
                ],
            },
            "risk_diagnostics": {
                "status": "available",
                "items": [
                    {
                        "type": "metrics",
                        "vol_annual": 0.22,
                        "max_drawdown": -0.31,
                    }
                ],
            },
        }
    }
    stress = {
        "stress_scorecard_v1": {
            "overall_status": "DIAG_ATTENTION",
            "overall_confidence": "medium",
        },
        "stress_conclusions": {
            "overall_confidence": "medium",
            "worst_synthetic_scenario": {
                "scenario_id": "recession",
                "loss_severity": "high",
            },
            "hedge_gap_status": "attention",
        },
    }

    doc = build_problem_classification(
        portfolio_xray=xray,
        stress_report=stress,
        analysis_end="2026-04-30",
    )

    assert doc["schema_version"] == PROBLEM_CLASSIFICATION_VERSION
    assert doc["diagnostic_only"] is True
    assert doc["analysis_end"] == "2026-04-30"
    problem_ids = {row["problem_id"] for row in doc["problems"]}
    assert "high_volatility" in problem_ids
    assert "weak_crisis_resilience" in problem_ids
    assert doc["summary"]["current_portfolio_acceptable"] is False
    for row in doc["problems"]:
        assert row["evidence"]
        assert row["reasonable_paths_to_test"]


def test_problem_classification_accepts_current_when_no_problem_detected() -> None:
    doc = build_problem_classification(
        portfolio_xray={"sections": {"weakness_map": {"status": "available", "items": []}}},
        stress_report={"stress_scorecard_v1": {"overall_status": "DIAG_PASS"}},
    )

    assert doc["problems"][0]["problem_id"] == "current_portfolio_acceptable"
    assert doc["summary"]["current_portfolio_acceptable"] is True


def test_problem_classification_warns_on_missing_sources() -> None:
    doc = build_problem_classification(portfolio_xray=None, stress_report=None)

    assert "missing_portfolio_xray" in doc["warnings"]
    assert "missing_stress_report" in doc["warnings"]


def test_write_problem_classification_outputs(tmp_path: Path) -> None:
    path = write_problem_classification_outputs(
        output_dir=tmp_path,
        portfolio_xray={"sections": {}},
        stress_report={},
        analysis_end="2026-04-30",
    )

    assert path == tmp_path / "problem_classification.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == PROBLEM_CLASSIFICATION_VERSION
