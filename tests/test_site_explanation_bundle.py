import json
from pathlib import Path

from src.site_explanation_bundle import (
    HIERARCHY_LEVELS,
    SCREEN_KEYS,
    SITE_EXPLANATION_BUNDLE_FILENAME,
    SITE_EXPLANATION_BUNDLE_VERSION,
    build_site_explanation_bundle,
    write_site_explanation_bundle_outputs,
)


def test_site_explanation_bundle_skeleton_shape() -> None:
    doc = build_site_explanation_bundle(review_id="review-1")

    assert doc["schema_version"] == SITE_EXPLANATION_BUNDLE_VERSION
    assert doc["review_id"] == "review-1"
    assert set(doc["screens"]) == set(SCREEN_KEYS)
    for screen in SCREEN_KEYS:
        assert set(doc["screens"][screen]) == set(HIERARCHY_LEVELS)
    assert doc["guardrails"]["does_not_call_llm"] is True
    assert doc["guardrails"]["does_not_create_new_metrics"] is True
    assert doc["guardrails"]["does_not_issue_trade_instruction"] is True
    assert doc["guardrails"]["candidate_is_not_recommendation"] is True


def test_site_explanation_bundle_missing_sources_emit_empty_states() -> None:
    doc = build_site_explanation_bundle()

    assert "missing_source:portfolio_xray.json" in doc["warnings"]
    diagnosis_copy = doc["screens"]["diagnosis"]["executive"]
    assert diagnosis_copy
    assert diagnosis_copy[0]["claim_type"] == "empty_state"
    assert diagnosis_copy[0]["evidence_status"] == "missing"
    assert diagnosis_copy[0]["source_refs"] == []


def test_site_explanation_bundle_available_sources_are_technical_and_sourced() -> None:
    doc = build_site_explanation_bundle(
        portfolio_xray={"schema_version": "portfolio_xray_v2"},
        stress_report={"status": "ok"},
    )

    technical = doc["screens"]["diagnosis"]["technical"]
    assert technical
    assert technical[0]["claim_type"] == "material_claim"
    assert {
        (ref["artifact"], ref["field_path"]) for ref in technical[0]["source_refs"]
    } == {
        ("portfolio_xray.json", "$"),
        ("stress_report.json", "$"),
    }


def test_write_site_explanation_bundle_outputs(tmp_path: Path) -> None:
    paths = write_site_explanation_bundle_outputs(
        output_dir=tmp_path,
        review_id="review-2",
        current_vs_candidate={"view_mode": "one_candidate"},
        decision_verdict={"verdict_id": "evidence_insufficient"},
    )

    path = paths["site_explanation_bundle_json"]
    assert path == tmp_path / SITE_EXPLANATION_BUNDLE_FILENAME
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == SITE_EXPLANATION_BUNDLE_VERSION
    assert doc["review_id"] == "review-2"
