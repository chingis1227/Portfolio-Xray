from __future__ import annotations

import json
from pathlib import Path

from src.ai_commentary_context import (
    AI_COMMENTARY_CONTEXT_VERSION,
    build_ai_commentary_context,
    write_ai_commentary_context_outputs,
)


def test_ai_commentary_context_lists_sources_and_guardrails() -> None:
    doc = build_ai_commentary_context(
        comparison={
            "comparison_baseline_candidate_id": "analysis_subject",
            "candidate_menu": {"factory_evidence_status": "fresh"},
        },
        current_vs_candidate={
            "view_mode": "one_candidate",
            "comparisons": [{"candidate_id": "equal_weight", "status": "available", "dimensions": [{}, {}]}],
            "warnings": [],
        },
        selection={
            "decision_status": "selected_candidate",
            "favored_candidate_id": "equal_weight",
            "warnings": [],
        },
        decision_verdict={
            "verdict_id": "rebalance_to_selected_candidate",
            "confidence": "medium",
            "confidence_limitations": [],
        },
        action={"action_status": "trades_for_review"},
    )

    assert doc["schema_version"] == AI_COMMENTARY_CONTEXT_VERSION
    assert doc["guardrails"]["does_not_call_llm"] is True
    assert doc["guardrails"]["does_not_calculate_metrics"] is True
    assert "new_metric_calculation" in doc["forbidden_claim_categories"]
    assert "unsupported_verdict" in doc["forbidden_claim_categories"]
    assert doc["source_artifacts"]["candidate_comparison"] == "candidate_comparison.json"
    assert doc["source_artifacts"]["decision_verdict"] == "decision_verdict.json"
    assert doc["warnings"] == []


def test_ai_commentary_context_includes_verdict_and_no_trade_evidence() -> None:
    doc = build_ai_commentary_context(
        comparison={"comparison_baseline_candidate_id": "analysis_subject"},
        current_vs_candidate={"view_mode": "one_candidate", "comparisons": []},
        selection={
            "decision_status": "no_material_rebalance",
            "favored_candidate_id": "risk_parity",
            "no_trade": {
                "evaluated": True,
                "baseline_candidate_id": "analysis_subject",
                "target_candidate_id": "risk_parity",
            },
        },
        decision_verdict={
            "verdict_id": "no_material_rebalance_recommended",
            "confidence": "medium",
        },
    )

    paths = {(ref["artifact"], ref["field_path"]) for ref in doc["evidence_references"]}
    assert ("selection_decision.json", "decision_status") in paths
    assert ("selection_decision.json", "no_trade") in paths
    assert ("decision_verdict.json", "verdict_id") in paths
    assert doc["commentary_topics"]["no_trade"]


def test_ai_commentary_context_warns_on_missing_required_sources() -> None:
    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=None,
        selection={"decision_status": "data_review_required", "warnings": ["missing_score_artifacts"]},
        decision_verdict={"verdict_id": "evidence_insufficient", "confidence_limitations": ["missing_score_artifacts"]},
    )

    assert "missing_required_source:candidate_comparison.json" in doc["warnings"]
    assert "missing_required_source:current_vs_candidate.json" in doc["warnings"]
    assert "selection_decision.json:missing_score_artifacts" in doc["warnings"]
    assert (
        "decision_verdict.json:confidence_limit:missing_score_artifacts"
        in doc["warnings"]
    )


def test_write_ai_commentary_context_outputs(tmp_path: Path) -> None:
    paths = write_ai_commentary_context_outputs(
        output_dir=tmp_path,
        comparison={"comparison_baseline_candidate_id": "analysis_subject"},
        current_vs_candidate={"view_mode": "diagnosis_only", "comparisons": []},
        selection={"decision_status": "inconclusive"},
        decision_verdict={"verdict_id": "test_another_candidate_or_review_evidence"},
    )

    path = paths["ai_commentary_context_json"]
    assert path == tmp_path / "ai_commentary_context.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == AI_COMMENTARY_CONTEXT_VERSION
