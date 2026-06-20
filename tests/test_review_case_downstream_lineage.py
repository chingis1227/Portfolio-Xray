from __future__ import annotations

import pytest

from src.review_case import (
    ReviewCaseDownstreamLineageError,
    review_case_candidate_lineage,
    review_case_comparison_has_displayable_evidence,
    review_case_comparison_id_for_candidate,
    review_case_comparison_lineage,
    review_case_verdict_lineage,
)


def _candidate_generation(candidate_id: str = "equal_weight") -> dict[str, object]:
    return {
        "selected_card_id": "launchpad_card_reduce_concentration",
        "candidate": {
            "candidate_id": candidate_id,
            "source_card_id": "launchpad_card_reduce_concentration",
        },
    }


def _current_vs_candidate(candidate_id: str = "equal_weight") -> dict[str, object]:
    return {
        "selected_candidate_ids": [candidate_id],
        "comparisons": [
            {
                "candidate_id": candidate_id,
                "dimensions": [
                    {
                        "status": "available",
                        "baseline_value": 0.42,
                        "candidate_value": 0.25,
                        "delta": -0.17,
                    }
                ],
            }
        ],
    }


def _verdict(candidate_id: str = "equal_weight") -> dict[str, object]:
    return {
        "verdict_id": "evidence_insufficient",
        "reviewed_candidate_id": candidate_id,
    }


def test_candidate_lineage_validates_active_candidate() -> None:
    lineage = review_case_candidate_lineage(_candidate_generation(), "equal_weight")

    assert lineage.selected_card_id == "launchpad_card_reduce_concentration"
    assert lineage.candidate_id == "equal_weight"


def test_candidate_lineage_rejects_stale_candidate_id() -> None:
    with pytest.raises(ReviewCaseDownstreamLineageError) as exc:
        review_case_candidate_lineage(_candidate_generation(), "stale_candidate")

    assert str(exc.value) == "Requested candidate_id does not match the active run-local candidate."


def test_comparison_lineage_accepts_public_and_legacy_comparison_ids() -> None:
    for comparison_id in (
        "equal_weight",
        "current_vs_candidate:equal_weight",
        "comparison:equal_weight",
        "comparison_equal_weight",
    ):
        lineage = review_case_comparison_lineage(
            candidate_generation=_candidate_generation(),
            current_vs_candidate=_current_vs_candidate(),
            requested_comparison_id=comparison_id,
        )

        assert lineage.selected_card_id == "launchpad_card_reduce_concentration"
        assert lineage.candidate_id == "equal_weight"
        assert lineage.comparison_id == "current_vs_candidate:equal_weight"


def test_comparison_lineage_rejects_missing_displayable_evidence() -> None:
    current_vs_candidate = {
        "selected_candidate_ids": ["equal_weight"],
        "comparisons": [
            {
                "candidate_id": "equal_weight",
                "dimensions": [{"status": "unavailable", "direction": "unknown"}],
            }
        ],
    }

    with pytest.raises(ReviewCaseDownstreamLineageError) as exc:
        review_case_comparison_lineage(
            candidate_generation=_candidate_generation(),
            current_vs_candidate=current_vs_candidate,
            requested_comparison_id="current_vs_candidate:equal_weight",
        )

    assert "displayable evidence" in str(exc.value)
    assert review_case_comparison_has_displayable_evidence(current_vs_candidate, "equal_weight") is False


def test_comparison_lineage_rejects_selected_candidate_without_matching_row() -> None:
    current_vs_candidate = _current_vs_candidate()
    current_vs_candidate["comparisons"][0]["candidate_id"] = "stale_candidate"  # type: ignore[index]

    with pytest.raises(ReviewCaseDownstreamLineageError) as exc:
        review_case_comparison_lineage(
            candidate_generation=_candidate_generation(),
            current_vs_candidate=current_vs_candidate,
            requested_comparison_id="current_vs_candidate:equal_weight",
        )

    assert "displayable evidence" in str(exc.value)
    assert review_case_comparison_has_displayable_evidence(current_vs_candidate, "equal_weight") is False


def test_verdict_lineage_validates_candidate_comparison_and_verdict_chain() -> None:
    lineage = review_case_verdict_lineage(
        candidate_generation=_candidate_generation(),
        current_vs_candidate=_current_vs_candidate(),
        verdict=_verdict(),
        requested_verdict_id="evidence_insufficient",
    )

    assert lineage.selected_card_id == "launchpad_card_reduce_concentration"
    assert lineage.candidate_id == "equal_weight"
    assert lineage.comparison_id == "current_vs_candidate:equal_weight"
    assert lineage.verdict_id == "evidence_insufficient"


def test_verdict_lineage_rejects_stale_verdict_id() -> None:
    with pytest.raises(ReviewCaseDownstreamLineageError) as exc:
        review_case_verdict_lineage(
            candidate_generation=_candidate_generation(),
            current_vs_candidate=_current_vs_candidate(),
            verdict=_verdict(),
            requested_verdict_id="stale_verdict",
        )

    assert str(exc.value) == "Requested verdict_id does not match the active run-local Decision Verdict."


def test_review_case_comparison_id_for_candidate_preserves_public_id_shape() -> None:
    assert review_case_comparison_id_for_candidate("equal_weight") == "current_vs_candidate:equal_weight"
    assert review_case_comparison_id_for_candidate(None) is None
