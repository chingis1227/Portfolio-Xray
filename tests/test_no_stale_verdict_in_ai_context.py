from __future__ import annotations

from src.ai_commentary_context import build_ai_commentary_context


def _product_run(run_id: str) -> dict:
    return {"run_id": run_id, "active": True, "artifact_role": "test", "workflow_state": "blocks_5_9_vertical"}


def test_ai_commentary_does_not_use_verdict_from_different_product_run() -> None:
    current_vs_candidate = {
        "schema_version": "current_vs_candidate_v1",
        "view_mode": "one_candidate",
        "selected_candidate_ids": ["equal_weight"],
        "comparisons": [{"candidate_id": "equal_weight"}],
        "product_run": _product_run("run-current"),
    }
    stale_verdict = {
        "schema_version": "decision_verdict_v1",
        "verdict_id": "rebalance_to_selected_candidate",
        "reviewed_candidate_id": "equal_weight",
        "product_run": _product_run("run-old"),
    }
    candidate_generation = {
        "schema_version": "candidate_generation_v1",
        "generation_status": "generated",
        "candidate": {"candidate_id": "equal_weight"},
        "product_run": _product_run("run-current"),
    }

    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=current_vs_candidate,
        selection=None,
        decision_verdict=stale_verdict,
        candidate_generation=candidate_generation,
    )

    assert "artifact_lineage_mismatch:decision_verdict.json" in doc["warnings"]
    assert doc["source_artifacts"]["decision_verdict"] is None
    assert not any(
        ref["artifact"] == "decision_verdict.json"
        for ref in doc["evidence_references"]
    )
    assert doc["grounding_phase"] == "diagnosis_only"


def test_ai_commentary_uses_verdict_from_same_product_run() -> None:
    current_vs_candidate = {
        "schema_version": "current_vs_candidate_v1",
        "view_mode": "one_candidate",
        "selected_candidate_ids": ["equal_weight"],
        "comparisons": [{"candidate_id": "equal_weight"}],
        "product_run": _product_run("run-1"),
    }
    verdict = {
        "schema_version": "decision_verdict_v1",
        "verdict_id": "no_material_rebalance_recommended",
        "reviewed_candidate_id": "equal_weight",
        "product_run": _product_run("run-1"),
    }
    candidate_generation = {
        "schema_version": "candidate_generation_v1",
        "generation_status": "generated",
        "candidate": {"candidate_id": "equal_weight"},
        "product_run": _product_run("run-1"),
    }

    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=current_vs_candidate,
        selection=None,
        decision_verdict=verdict,
        candidate_generation=candidate_generation,
    )

    assert "artifact_lineage_mismatch:decision_verdict.json" not in doc["warnings"]
    assert doc["source_artifacts"]["decision_verdict"] == "decision_verdict.json"
    assert any(ref["artifact"] == "decision_verdict.json" for ref in doc["evidence_references"])
    assert doc["grounding_phase"] == "post_compare"
