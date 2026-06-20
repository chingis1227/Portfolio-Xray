from __future__ import annotations

import pytest

from src.review_case import (
    EVIDENCE_GRAPH_SCHEMA_VERSION,
    ReviewCase,
    ReviewCaseEvidenceGraph,
    ReviewCaseEvidenceGraphError,
    ReviewCaseEvidenceLink,
    review_case_evidence_node_ref,
)


def _review_case_with_artifact() -> ReviewCase:
    return ReviewCase.initial(
        "frontend_review_evidence_graph",
        mode="live",
        owner_id="local-dev-user",
        now="2026-06-19T12:00:00Z",
        provider_status={
            "source": "live_provider",
            "freshness": "pending",
            "message": "Live mode uses the normal market-data provider path.",
        },
        artifacts={"portfolio_xray": "analysis_subject/portfolio_xray.json"},
    )


def test_evidence_graph_relates_stages_artifacts_and_sources() -> None:
    graph = ReviewCaseEvidenceGraph.from_review_case(
        _review_case_with_artifact(),
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

    serialized = graph.to_dict()

    assert serialized["schema_version"] == EVIDENCE_GRAPH_SCHEMA_VERSION
    assert serialized["nodes"][0] == {
        "id": "stage:input",
        "kind": "stage",
        "key": "input",
    }
    assert {
        "id": "artifact:portfolio_xray",
        "kind": "artifact",
        "key": "portfolio_xray",
        "ref": "analysis_subject/portfolio_xray.json",
    } in serialized["nodes"]
    assert {
        "id": "source:market_data_snapshot",
        "kind": "source",
        "key": "market_data_snapshot",
        "ref": "logical://market-data/yahoo",
    } in serialized["nodes"]
    assert serialized["links"] == [
        {
            "from": "stage:input",
            "to": "source:portfolio_input",
            "relationship": "stage_uses_source",
        },
        {
            "from": "stage:xray",
            "to": "artifact:portfolio_xray",
            "relationship": "stage_outputs_artifact",
        },
        {
            "from": "artifact:portfolio_xray",
            "to": "source:market_data_snapshot",
            "relationship": "artifact_uses_source",
        },
    ]


def test_evidence_graph_rejects_links_to_undeclared_artifacts() -> None:
    with pytest.raises(ReviewCaseEvidenceGraphError):
        ReviewCaseEvidenceGraph.from_review_case(
            ReviewCase.initial(
                "frontend_review_no_artifact",
                mode="demo_qa",
                owner_id="local-dev-user",
                now="2026-06-19T12:00:00Z",
                provider_status={
                    "source": "frozen_fixture",
                    "freshness": "fixed_demo_dataset",
                    "message": "Demo / QA mode uses deterministic fixture data.",
                },
            ),
            links=(ReviewCaseEvidenceLink.stage_outputs_artifact("xray", "portfolio_xray"),),
        )


@pytest.mark.parametrize(
    "bad_ref",
    [
        "C:/Users/example/secret.json",
        "C:\\Users\\example\\secret.json",
        "/home/example/secret.json",
        "../outside.json",
        "analysis_subject/../outside.json",
    ],
)
def test_evidence_graph_rejects_unsafe_source_refs(bad_ref: str) -> None:
    with pytest.raises(ReviewCaseEvidenceGraphError):
        ReviewCaseEvidenceGraph(sources={"unsafe_source": bad_ref})


def test_evidence_graph_node_ref_rejects_unknown_stage() -> None:
    with pytest.raises(ReviewCaseEvidenceGraphError):
        review_case_evidence_node_ref("stage", "unknown")
