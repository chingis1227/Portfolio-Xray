from __future__ import annotations

import json
from pathlib import Path

from src.candidate_launchpad import (
    CANDIDATE_LAUNCHPAD_VERSION,
    build_candidate_launchpad,
    write_candidate_launchpad_outputs,
)


def _problem_doc() -> dict:
    return {
        "schema_version": "problem_classification_v1",
        "analysis_end": "2026-04-30",
        "problems": [
            {
                "problem_id": "high_volatility",
                "label": "High volatility",
                "severity": "high",
                "confidence": "medium",
                "evidence": [{"source_artifact": "portfolio_xray.json"}],
                "reasonable_paths_to_test": [
                    "Reduce volatility",
                    "Compare against simple benchmark",
                ],
            },
            {
                "problem_id": "weak_crisis_resilience",
                "label": "Weak crisis resilience",
                "severity": "moderate",
                "confidence": "medium",
                "evidence": [{"source_artifact": "stress_report.json"}],
                "reasonable_paths_to_test": [
                    "Improve crisis resilience",
                    "Reduce volatility",
                ],
            },
        ],
        "warnings": [],
    }


def test_candidate_launchpad_builds_unique_cards_from_problems() -> None:
    doc = build_candidate_launchpad(problem_classification=_problem_doc())

    assert doc["schema_version"] == CANDIDATE_LAUNCHPAD_VERSION
    assert doc["diagnostic_only"] is True
    assert doc["analysis_end"] == "2026-04-30"
    goals = [card["goal"] for card in doc["cards"]]
    assert goals == [
        "Reduce volatility",
        "Compare against simple benchmark",
        "Improve crisis resilience",
    ]
    assert doc["summary"]["n_cards"] == 3
    assert doc["summary"]["has_portfolio_generating_options"] is True
    for card in doc["cards"]:
        assert card["generates_portfolio"] is False
        assert "weights" not in card
        assert card["rationale"]["evidence"]


def test_candidate_launchpad_current_acceptable_includes_monitor_card() -> None:
    doc = build_candidate_launchpad(
        problem_classification={
            "analysis_end": "2026-04-30",
            "problems": [
                {
                    "problem_id": "current_portfolio_acceptable",
                    "label": "Current portfolio already acceptable",
                    "severity": "low",
                    "confidence": "medium",
                    "evidence": [],
                    "reasonable_paths_to_test": ["Keep current portfolio and monitor"],
                }
            ],
        }
    )

    goals = [card["goal"] for card in doc["cards"]]
    assert "Keep current portfolio and monitor" in goals
    assert doc["summary"]["has_keep_current_option"] is True


def test_candidate_launchpad_missing_problem_classification_fallback() -> None:
    doc = build_candidate_launchpad(problem_classification=None)

    assert doc["warnings"] == ["missing_problem_classification"]
    assert doc["cards"][0]["goal"] == "Keep current portfolio and monitor"
    assert doc["cards"][0]["requires_user_action"] is False


def test_write_candidate_launchpad_outputs(tmp_path: Path) -> None:
    path = write_candidate_launchpad_outputs(
        output_dir=tmp_path,
        problem_classification=_problem_doc(),
    )

    assert path == tmp_path / "candidate_launchpad.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == CANDIDATE_LAUNCHPAD_VERSION
