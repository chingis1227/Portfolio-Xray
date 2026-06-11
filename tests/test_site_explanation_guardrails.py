import pytest

from src.site_explanation_bundle import (
    build_site_explanation_bundle,
    _text_item,
)


def _all_text_items(doc: dict) -> list[dict]:
    items: list[dict] = []
    for screen in doc["screens"].values():
        for level_items in screen.values():
            items.extend(level_items)
    return items


@pytest.mark.parametrize(
    "phrase",
    [
        "buy",
        "sell",
        "must rebalance",
        "best portfolio",
        "guaranteed",
    ],
)
def test_site_explanation_text_item_blocks_forbidden_phrases(phrase: str) -> None:
    with pytest.raises(ValueError, match="forbidden copy phrase"):
        _text_item(
            item_id="diagnosis.executive.test",
            level="executive",
            text=f"This screen should {phrase} now.",
            evidence_status="available",
            claim_type="boundary_note",
            source_refs=[],
        )


def test_site_explanation_candidate_copy_cannot_be_recommendation() -> None:
    with pytest.raises(ValueError, match="candidate copy must not describe"):
        _text_item(
            item_id="candidate.executive.test",
            level="executive",
            text="This candidate is the recommended portfolio test.",
            evidence_status="available",
            claim_type="boundary_note",
            source_refs=[],
        )


def test_site_explanation_optimal_portfolio_only_allowed_in_technical_method_context() -> None:
    with pytest.raises(ValueError, match="technical method context"):
        _text_item(
            item_id="comparison.executive.test",
            level="executive",
            text="This is the optimal portfolio for the active review.",
            evidence_status="available",
            claim_type="boundary_note",
            source_refs=[],
        )

    item = _text_item(
        item_id="comparison.technical.optimizer_disclosure",
        level="technical",
        text="The phrase optimal portfolio appears only in optimizer methodology disclosure.",
        evidence_status="available",
        claim_type="boundary_note",
        source_refs=[],
    )

    assert item["level"] == "technical"


def test_site_explanation_generated_skeleton_copy_has_no_forbidden_language() -> None:
    doc = build_site_explanation_bundle(
        portfolio_xray={"schema_version": "portfolio_xray_v2"},
        candidate_generation={"schema_version": "candidate_generation_v1"},
        current_vs_candidate={"schema_version": "current_vs_candidate_v1"},
        decision_verdict={"schema_version": "decision_verdict_v1"},
    )

    forbidden_fragments = (
        "buy",
        "sell",
        "must rebalance",
        "best portfolio",
        "guaranteed",
        "optimal portfolio",
    )
    for item in _all_text_items(doc):
        text = item["text"].lower()
        assert not any(fragment in text for fragment in forbidden_fragments)
        if item["id"].startswith("candidate."):
            assert "recommend" not in text
