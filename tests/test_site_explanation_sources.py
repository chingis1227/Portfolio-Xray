import pytest

from src.site_explanation_bundle import (
    ALLOWED_SOURCE_ARTIFACTS,
    build_site_explanation_bundle,
    _text_item,
)


def _all_text_items(doc: dict) -> list[dict]:
    items: list[dict] = []
    for screen in doc["screens"].values():
        for level_items in screen.values():
            items.extend(level_items)
    return items


def test_material_claim_text_item_requires_source_refs() -> None:
    with pytest.raises(ValueError, match="must include source_refs"):
        _text_item(
            item_id="diagnosis.evidence.unsourced_claim",
            level="evidence",
            text="The portfolio has a material sourced-sounding conclusion.",
            evidence_status="available",
            claim_type="material_claim",
            source_refs=[],
        )


@pytest.mark.parametrize(
    "bad_ref,match",
    [
        ({}, "must include artifact"),
        ({"artifact": "portfolio_xray.json"}, "must include field_path"),
        (
            {"artifact": "not_a_source.json", "field_path": "$.summary"},
            "unsupported artifact",
        ),
    ],
)
def test_source_refs_must_name_supported_artifact_and_field_path(
    bad_ref: dict, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        _text_item(
            item_id="diagnosis.evidence.bad_source_ref",
            level="evidence",
            text="The portfolio has a material sourced-sounding conclusion.",
            evidence_status="available",
            claim_type="material_claim",
            source_refs=[bad_ref],
        )


def test_generated_bundle_material_claims_are_sourced_with_supported_refs() -> None:
    doc = build_site_explanation_bundle(
        portfolio_xray={"schema_version": "portfolio_xray_v2"},
        stress_report={"schema_version": "stress_report_v1"},
        problem_classification={"schema_version": "problem_classification_v1"},
        candidate_generation={"schema_version": "candidate_generation_v1"},
        current_vs_candidate={"schema_version": "current_vs_candidate_v1"},
        decision_verdict={"schema_version": "decision_verdict_v1"},
        ai_commentary_context={"schema_version": "ai_commentary_context_v1"},
    )

    material_claims = [
        item for item in _all_text_items(doc) if item["claim_type"] == "material_claim"
    ]

    assert material_claims
    for item in material_claims:
        assert item["source_refs"]
        for ref in item["source_refs"]:
            assert set(ref) == {"artifact", "field_path"}
            assert ref["artifact"] in ALLOWED_SOURCE_ARTIFACTS
            assert ref["field_path"]
