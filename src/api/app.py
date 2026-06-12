"""FastAPI application for the Portfolio MRI local API.

Session 07 runs the one-candidate MVP backend chain through FastAPI and the
normal Next.js portfolio API route handlers proxy to this API instead of
launching the old script bridge.
"""

from __future__ import annotations

from fastapi import FastAPI, Response

import src.api.reviews as review_service
from src.api.models import (
    API_VERSION,
    ApiEvidence,
    ApiLineage,
    BuilderRequest,
    BuilderResponse,
    BuilderSetupIdRequest,
    CandidateIdRequest,
    CandidateResponse,
    ComparisonIdRequest,
    ComparisonResponse,
    CreateReviewRequest,
    CreateReviewResponse,
    HealthData,
    HealthResponse,
    ReportResponse,
    ReviewRecoveryResponse,
    VerdictIdRequest,
    VerdictResponse,
)


HEALTH_SCHEMA_VERSION = "health_v1"
CREATE_REVIEW_SCHEMA_VERSION = review_service.CREATE_REVIEW_SCHEMA_VERSION
RECOVERY_SCHEMA_VERSION = review_service.RECOVERY_SCHEMA_VERSION
BUILDER_SCHEMA_VERSION = "builder_setup_v1"
CANDIDATE_SCHEMA_VERSION = "candidate_generation_v1"
COMPARISON_SCHEMA_VERSION = "current_vs_candidate_v1"
VERDICT_SCHEMA_VERSION = "decision_verdict_v1"
REPORT_SCHEMA_VERSION = "report_grounding_v1"


def _success_envelope(*, schema_version: str, data: HealthData) -> HealthResponse:
    """Return the public v1 health envelope."""

    return HealthResponse(
        api_version=API_VERSION,
        schema_version=schema_version,
        review_id=None,
        stage="health",
        status="ok",
        lineage=ApiLineage(),
        data=data,
        warnings=[],
        safe_error=None,
        evidence=ApiEvidence(data_quality="ok", confidence="high"),
    )


def create_app() -> FastAPI:
    """Create the local Portfolio MRI FastAPI application."""

    app = FastAPI(
        title="Portfolio MRI Local API",
        version="0.1.0",
        description=(
            "Contract-first local API foundation for Portfolio MRI. "
            "Session 07 runs the full one-candidate MVP backend chain through FastAPI while "
            "Next.js portfolio route handlers act only as compatibility proxies."
        ),
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.get(
        "/api/v1/health",
        tags=["health"],
        summary="Check local API readiness",
        operation_id="getHealth",
        response_model=HealthResponse,
    )
    def health() -> HealthResponse:
        """Return API readiness without reading artifacts or running diagnostics."""

        return _success_envelope(
            schema_version=HEALTH_SCHEMA_VERSION,
            data=HealthData(),
        )

    @app.post(
        "/api/v1/reviews",
        tags=["reviews"],
        summary="Create a portfolio-first diagnosis review",
        operation_id="createReview",
        response_model=CreateReviewResponse,
    )
    def create_review(request: CreateReviewRequest, response: Response) -> CreateReviewResponse:
        """Run diagnosis-only portfolio review creation through FastAPI."""

        http_status, envelope = review_service.create_review_diagnosis(request)
        response.status_code = http_status
        return envelope

    @app.get(
        "/api/v1/reviews/{review_id}",
        tags=["reviews"],
        summary="Recover a review by id",
        operation_id="recoverReview",
        response_model=ReviewRecoveryResponse,
    )
    def recover_review(review_id: str, response: Response) -> ReviewRecoveryResponse:
        """Recover run-local diagnosis/evidence/hypothesis state through FastAPI."""

        http_status, envelope = review_service.recover_review_diagnosis(review_id)
        response.status_code = http_status
        return envelope

    @app.post(
        "/api/v1/reviews/{review_id}/builder",
        tags=["builder"],
        summary="Prepare Builder setup from a selected Launchpad card",
        operation_id="prepareBuilder",
        response_model=BuilderResponse,
    )
    def prepare_builder(review_id: str, request: BuilderRequest, response: Response) -> BuilderResponse:
        """Prepare Builder setup through FastAPI without generating a candidate."""

        http_status, envelope = review_service.prepare_builder_setup(review_id, request)
        response.status_code = http_status
        return envelope

    @app.post(
        "/api/v1/reviews/{review_id}/candidate",
        tags=["candidate"],
        summary="Generate one diagnostic candidate from Builder setup",
        operation_id="generateCandidate",
        response_model=CandidateResponse,
    )
    def generate_candidate(
        review_id: str, request: BuilderSetupIdRequest, response: Response
    ) -> CandidateResponse:
        """Generate one diagnostic candidate through FastAPI."""

        http_status, envelope = review_service.generate_candidate_from_builder(review_id, request)
        response.status_code = http_status
        return envelope

    @app.post(
        "/api/v1/reviews/{review_id}/comparison",
        tags=["comparison"],
        summary="Compare current portfolio with the generated candidate",
        operation_id="runComparison",
        response_model=ComparisonResponse,
    )
    def run_comparison(
        review_id: str, request: CandidateIdRequest, response: Response
    ) -> ComparisonResponse:
        """Run Current-vs-Candidate Comparison through FastAPI."""

        http_status, envelope = review_service.run_current_vs_candidate(review_id, request)
        response.status_code = http_status
        return envelope

    @app.post(
        "/api/v1/reviews/{review_id}/verdict",
        tags=["verdict"],
        summary="Generate non-binding Decision Verdict from comparison evidence",
        operation_id="generateVerdict",
        response_model=VerdictResponse,
    )
    def generate_verdict(
        review_id: str, request: ComparisonIdRequest, response: Response
    ) -> VerdictResponse:
        """Generate non-binding Decision Verdict through FastAPI."""

        http_status, envelope = review_service.generate_decision_verdict(review_id, request)
        response.status_code = http_status
        return envelope

    @app.post(
        "/api/v1/reviews/{review_id}/report",
        tags=["report"],
        summary="Return grounded report preview from verdict evidence",
        operation_id="generateReport",
        response_model=ReportResponse,
    )
    def generate_report(
        review_id: str, request: VerdictIdRequest, response: Response
    ) -> ReportResponse:
        """Generate grounded report preview/context through FastAPI."""

        http_status, envelope = review_service.generate_report_grounding(review_id, request)
        response.status_code = http_status
        return envelope

    return app


app = create_app()
