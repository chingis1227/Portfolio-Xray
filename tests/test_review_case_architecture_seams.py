from __future__ import annotations

import src.review_case as review_case


EXPECTED_REVIEW_CASE_SEAMS = {
    "ReviewCase",
    "RunLocalReviewCaseRepository",
    "ReviewCaseStageMachine",
    "ReviewCaseArtifactManifest",
    "ReviewCaseEvidenceGraph",
    "ReviewCaseScreenReadModel",
    "ReviewCaseMarketDataSnapshot",
    "InProcessReviewCaseExecutionQueue",
    "RqRedisReviewCaseExecutionQueue",
    "RunLocalReviewCaseArtifactStorage",
    "ReviewCaseStageReadiness",
    "review_case_stage_readiness_from_state",
    "ReviewCaseCandidateLineage",
    "ReviewCaseComparisonLineage",
    "ReviewCaseVerdictLineage",
    "review_case_candidate_lineage",
    "review_case_comparison_lineage",
    "review_case_verdict_lineage",
    "ReviewCaseDownstreamEvidenceChainContext",
    "review_case_downstream_evidence_chain_context",
}


def test_review_case_package_exports_migrated_internal_seams() -> None:
    exported_names = set(review_case.__all__)

    assert EXPECTED_REVIEW_CASE_SEAMS <= exported_names
    for seam_name in EXPECTED_REVIEW_CASE_SEAMS:
        assert getattr(review_case, seam_name) is not None
