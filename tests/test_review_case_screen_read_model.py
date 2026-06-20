from __future__ import annotations

import pytest

from src.review_case import (
    SCREEN_READ_MODEL_SCHEMA_VERSION,
    ReviewCase,
    ReviewCaseArtifactManifest,
    ReviewCaseEvidenceGraph,
    ReviewCaseEvidenceLink,
    ReviewCaseScreenReadModel,
    ReviewCaseScreenReadModelError,
)


def _review_case_with_completed_xray() -> ReviewCase:
    raw_state = ReviewCase.initial(
        "frontend_review_screen_read_model",
        mode="live",
        owner_id="local-dev-user",
        now="2026-06-19T12:00:00Z",
        provider_status={
            "source": "live_provider",
            "freshness": "pending",
            "message": "Live mode uses the normal market-data provider path.",
        },
        artifacts={
            "portfolio_xray": "analysis_subject/portfolio_xray.json",
            "stress_report": "analysis_subject/stress_report.json",
        },
    ).to_staged_state_dict(schema_version="review_state_v1")
    raw_state["current_stage"] = "stress"
    raw_state["stages"]["xray"] = {
        "status": "completed",
        "started_at": "2026-06-19T12:01:00Z",
        "completed_at": "2026-06-19T12:02:00Z",
        "artifact_refs": ["analysis_subject/portfolio_xray.json"],
    }
    return ReviewCase.from_staged_state_dict(raw_state, expected_schema_version="review_state_v1")


def test_screen_read_model_projects_progress_artifacts_and_evidence_links() -> None:
    review_case = _review_case_with_completed_xray()
    evidence_graph = ReviewCaseEvidenceGraph.from_review_case(
        review_case,
        sources={
            "portfolio_input": "payload.json",
            "market_data_snapshot": "logical://market-data/yahoo",
        },
        links=(
            ReviewCaseEvidenceLink.stage_uses_source("input", "portfolio_input"),
            ReviewCaseEvidenceLink.stage_outputs_artifact("xray", "portfolio_xray"),
            ReviewCaseEvidenceLink.artifact_uses_source(
                "portfolio_xray",
                "market_data_snapshot",
            ),
        ),
    )

    model = ReviewCaseScreenReadModel.from_review_case(
        review_case,
        evidence_graph=evidence_graph,
    )
    serialized = model.to_dict()

    assert serialized["schema_version"] == SCREEN_READ_MODEL_SCHEMA_VERSION
    assert serialized["review_id"] == "frontend_review_screen_read_model"
    assert serialized["current_stage"] == "stress"
    assert serialized["progress"] == {
        "total_stage_count": 11,
        "terminal_stage_count": 1,
        "active_stage": "stress",
    }
    assert serialized["stages"][0]["stage"] == "input"
    assert serialized["stages"][2] == {
        "stage": "xray",
        "status": "completed",
        "started_at": "2026-06-19T12:01:00Z",
        "completed_at": "2026-06-19T12:02:00Z",
        "is_started": True,
        "is_terminal": True,
        "has_artifacts": True,
        "artifact_refs": ["analysis_subject/portfolio_xray.json"],
    }
    assert {
        "key": "portfolio_xray",
        "ref": "analysis_subject/portfolio_xray.json",
        "available": True,
        "producing_stages": ["xray"],
        "evidence_source_ids": ["market_data_snapshot"],
    } in serialized["artifacts"]
    assert serialized["artifact_availability"] == {
        "available_artifact_count": 2,
        "artifact_count": 2,
    }
    assert serialized["evidence"]["sources"] == {
        "market_data_snapshot": "logical://market-data/yahoo",
        "portfolio_input": "payload.json",
    }
    assert {
        "from": "stage:xray",
        "to": "artifact:portfolio_xray",
        "relationship": "stage_outputs_artifact",
    } in serialized["evidence"]["links"]


def test_screen_read_model_keeps_artifacts_when_evidence_graph_is_absent() -> None:
    model = ReviewCaseScreenReadModel.from_review_case(_review_case_with_completed_xray())
    serialized = model.to_dict()

    assert serialized["artifacts"] == [
        {
            "key": "portfolio_xray",
            "ref": "analysis_subject/portfolio_xray.json",
            "available": True,
            "producing_stages": [],
            "evidence_source_ids": [],
        },
        {
            "key": "stress_report",
            "ref": "analysis_subject/stress_report.json",
            "available": True,
            "producing_stages": [],
            "evidence_source_ids": [],
        },
    ]
    assert serialized["evidence"] == {"sources": {}, "links": []}


def test_screen_read_model_rejects_graph_that_does_not_match_review_case_artifacts() -> None:
    mismatched_graph = ReviewCaseEvidenceGraph(
        artifact_manifest=ReviewCaseArtifactManifest(
            {"portfolio_xray": "analysis_subject/different_portfolio_xray.json"}
        )
    )

    with pytest.raises(ReviewCaseScreenReadModelError):
        ReviewCaseScreenReadModel.from_review_case(
            _review_case_with_completed_xray(),
            evidence_graph=mismatched_graph,
        )
