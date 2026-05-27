from __future__ import annotations

import json
from pathlib import Path

from src.decision_verdict import (
    DECISION_VERDICT_VERSION,
    build_decision_verdict,
    write_decision_verdict_outputs,
)


def test_decision_verdict_maps_selected_candidate() -> None:
    doc = build_decision_verdict(
        selection={
            "schema_version": "selection_decision_v1",
            "decision_status": "selected_candidate",
            "baseline_candidate_id": "analysis_subject",
            "favored_candidate_id": "equal_weight",
            "favored_display_name": "Equal Weight",
            "rationale": {"summary": "Equal Weight is favored in this comparison."},
            "warnings": [],
        },
        current_vs_candidate={"warnings": []},
        action={"action_status": "trades_for_review"},
    )

    assert doc["schema_version"] == DECISION_VERDICT_VERSION
    assert doc["verdict_id"] == "rebalance_to_selected_candidate"
    assert doc["selected_candidate_id"] == "equal_weight"
    assert doc["baseline_candidate_id"] == "analysis_subject"
    assert doc["confidence"] == "medium"
    assert doc["guardrails"]["does_not_rename_selection_engine_contract"] is True
    assert "selection_decision.json" == doc["source_artifacts"]["selection_decision"]


def test_decision_verdict_maps_no_trade() -> None:
    doc = build_decision_verdict(
        selection={
            "decision_status": "no_material_rebalance",
            "favored_candidate_id": "risk_parity",
            "no_trade": {
                "evaluated": True,
                "baseline_candidate_id": "analysis_subject",
                "target_candidate_id": "risk_parity",
            },
            "warnings": [],
        }
    )

    assert doc["verdict_id"] == "no_material_rebalance_recommended"
    assert doc["no_trade"]["evaluated"] is True
    assert doc["no_trade"]["applies"] is True
    assert "Keep current portfolio" in doc["recommended_action"]


def test_decision_verdict_data_review_is_low_confidence() -> None:
    doc = build_decision_verdict(
        selection={
            "decision_status": "data_review_required",
            "warnings": ["missing_score_artifacts"],
        },
        current_vs_candidate={"warnings": ["baseline_unavailable"]},
    )

    assert doc["verdict_id"] == "evidence_insufficient"
    assert doc["confidence"] == "low"
    assert "missing_score_artifacts" in doc["confidence_limitations"]
    assert "current_vs_candidate:baseline_unavailable" in doc["confidence_limitations"]


def test_write_decision_verdict_outputs(tmp_path: Path) -> None:
    paths = write_decision_verdict_outputs(
        output_dir=tmp_path,
        selection={"decision_status": "inconclusive", "warnings": []},
    )

    path = paths["decision_verdict_json"]
    assert path == tmp_path / "decision_verdict.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["verdict_id"] == "test_another_candidate_or_review_evidence"
    assert doc["verdict_family"] == "core_compare"


def test_decision_verdict_mandate_maps_policy_family() -> None:
    doc = build_decision_verdict(
        selection={
            "decision_status": "mandate_risk_reduction",
            "warnings": ["mandate_risk_reduction"],
            "rationale": {
                "summary": "Mandate constraints require risk reduction.",
                "risk_reduction_notes": ["Policy profile fails mandate validation."],
            },
        }
    )

    assert doc["verdict_id"] == "risk_reduction_required"
    assert doc["verdict_family"] == "policy_mandate"
    assert doc["selection_decision_status"] == "mandate_risk_reduction"
    assert "mandate" in doc["recommended_action"].lower()
