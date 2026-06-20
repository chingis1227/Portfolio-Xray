from __future__ import annotations

import pytest

from src.review_case import ReviewCase, ReviewCaseValidationError


def test_initial_review_case_matches_public_staged_state_contract() -> None:
    case = ReviewCase.initial(
        "frontend_review_20260619_abcd",
        mode="demo_qa",
        owner_id="user-123",
        now="2026-06-19T10:00:00Z",
        provider_status={
            "source": "frozen_fixture",
            "freshness": "fixed_demo_dataset",
            "message": "Demo / QA mode uses deterministic fixture data.",
        },
    )

    state = case.to_staged_state_dict(schema_version="review_state_v1")

    assert state["schema_version"] == "review_state_v1"
    assert state["review_id"] == "frontend_review_20260619_abcd"
    assert state["status"] == "running"
    assert state["current_stage"] == "input"
    assert state["mode"] == "demo_qa"
    assert state["owner_id"] == "user-123"
    assert list(state["stages"]) == [
        "input",
        "data_load",
        "xray",
        "stress",
        "client_fit",
        "problem_classification",
        "launchpad_builder",
        "candidate",
        "comparison",
        "verdict",
        "report",
    ]
    assert state["stages"]["input"] == {
        "status": "running",
        "started_at": "2026-06-19T10:00:00Z",
        "completed_at": None,
        "artifact_refs": ["payload.json"],
    }
    assert state["stages"]["stress"] == {
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "artifact_refs": [],
    }
    assert state["artifacts"] == {}
    assert state["provider_status"]["source"] == "frozen_fixture"
    assert state["warnings"] == []
    assert state["safe_error"] is None


def test_review_case_round_trips_existing_staged_state_without_renaming_public_fields() -> None:
    raw_state = ReviewCase.initial(
        "frontend_review_roundtrip",
        mode="live",
        owner_id="local-dev-user",
        now="2026-06-19T11:00:00Z",
        provider_status={
            "source": "live_provider",
            "freshness": "pending",
            "message": "Live mode uses the normal market-data provider path.",
        },
    ).to_staged_state_dict(schema_version="review_state_v1")
    raw_state["artifacts"] = {"portfolio_xray": "analysis_subject/portfolio_xray.json"}
    raw_state["stages"]["xray"] = {
        "status": "completed",
        "started_at": "2026-06-19T11:01:00Z",
        "completed_at": "2026-06-19T11:02:00Z",
        "artifact_refs": ["analysis_subject/portfolio_xray.json"],
    }
    raw_state["current_stage"] = "stress"

    case = ReviewCase.from_staged_state_dict(raw_state, expected_schema_version="review_state_v1")

    assert case.to_staged_state_dict(schema_version="review_state_v1") == raw_state


@pytest.mark.parametrize(
    "bad_ref",
    [
        "C:/Users/example/secret.json",
        "C:\\Users\\example\\secret.json",
        "/home/example/secret.json",
        "../outside.json",
    ],
)
def test_review_case_rejects_unsafe_artifact_refs(bad_ref: str) -> None:
    with pytest.raises(ReviewCaseValidationError):
        ReviewCase.initial(
            "frontend_review_bad_ref",
            mode="live",
            owner_id="local-dev-user",
            now="2026-06-19T12:00:00Z",
            provider_status={
                "source": "live_provider",
                "freshness": "pending",
                "message": "Live mode uses the normal market-data provider path.",
            },
            artifacts={"portfolio_xray": bad_ref},
        )
