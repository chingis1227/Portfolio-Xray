"""FastAPI application for the Portfolio MRI local API.

Session 07 runs the one-candidate MVP backend chain through FastAPI and the
normal Next.js portfolio API route handlers proxy to this API instead of
launching the old script bridge.
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

import src.api.reviews as review_service
from src.api.auth import InternalAuthContext, require_internal_auth
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
    StagedReviewStartedResponse,
    StagedReviewStatusResponse,
    VerdictIdRequest,
    VerdictResponse,
)


HEALTH_SCHEMA_VERSION = "health_v1"
CREATE_REVIEW_SCHEMA_VERSION = review_service.CREATE_REVIEW_SCHEMA_VERSION
RECOVERY_SCHEMA_VERSION = review_service.RECOVERY_SCHEMA_VERSION
STAGED_REVIEW_STARTED_SCHEMA_VERSION = review_service.STAGED_REVIEW_STARTED_SCHEMA_VERSION
STAGED_REVIEW_STATE_SCHEMA_VERSION = review_service.STAGED_REVIEW_STATE_SCHEMA_VERSION
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


def _max_request_body_bytes() -> int:
    raw = os.getenv("PMRI_FASTAPI_MAX_BODY_BYTES")
    if raw is None:
        return 128 * 1024
    try:
        return max(1024, int(raw))
    except ValueError:
        return 128 * 1024


def _fastapi_docs_enabled() -> bool:
    return os.getenv("PMRI_FASTAPI_ENABLE_DOCS", "").strip().lower() in {"1", "true", "yes"}


def create_app() -> FastAPI:
    """Create the local Portfolio MRI FastAPI application."""

    docs_enabled = _fastapi_docs_enabled()
    app = FastAPI(
        title="Portfolio MRI Local API",
        version="0.1.0",
        description=(
            "Contract-first local API foundation for Portfolio MRI. "
            "Session 07 runs the full one-candidate MVP backend chain through FastAPI while "
            "Next.js portfolio route handlers act only as compatibility proxies."
        ),
        openapi_url="/openapi.json" if docs_enabled else None,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
    )

    @app.middleware("http")
    async def reject_oversized_review_bodies(request: Request, call_next):
        if request.url.path.startswith("/api/v1/reviews") and request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > _max_request_body_bytes():
                        return JSONResponse({"detail": "Review request body is too large."}, status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                except ValueError:
                    return JSONResponse({"detail": "Invalid Content-Length header."}, status_code=status.HTTP_400_BAD_REQUEST)
        return await call_next(request)

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
            data=HealthData(openapi_available=docs_enabled),
        )

    @app.post(
        "/api/v1/reviews",
        tags=["reviews"],
        summary="Create a portfolio-first diagnosis review",
        operation_id="createReview",
        response_model=CreateReviewResponse,
    )
    def create_review(request: CreateReviewRequest, response: Response, auth: InternalAuthContext = Depends(require_internal_auth)) -> CreateReviewResponse:
        """Run diagnosis-only portfolio review creation through FastAPI."""

        http_status, envelope = review_service.create_review_diagnosis(request, owner_id=auth.user_id)
        response.status_code = http_status
        return envelope

    @app.post(
        "/api/v1/reviews/staged",
        tags=["reviews"],
        summary="Start a staged portfolio-first diagnosis review",
        operation_id="startStagedReview",
        response_model=StagedReviewStartedResponse,
    )
    def start_staged_review(
        request: CreateReviewRequest, response: Response, auth: InternalAuthContext = Depends(require_internal_auth)
    ) -> StagedReviewStartedResponse:
        """Create a run-local review state and start background diagnosis execution."""

        http_status, envelope = review_service.create_staged_review(request, owner_id=auth.user_id)
        response.status_code = http_status
        return envelope

    @app.get(
        "/api/v1/reviews/{review_id}",
        tags=["reviews"],
        summary="Recover a review by id",
        operation_id="recoverReview",
        response_model=ReviewRecoveryResponse,
    )
    def recover_review(review_id: str, response: Response, auth: InternalAuthContext = Depends(require_internal_auth)) -> ReviewRecoveryResponse:
        """Recover run-local diagnosis/evidence/hypothesis state through FastAPI."""

        http_status, envelope = review_service.recover_review_diagnosis(review_id, owner_id=auth.user_id)
        response.status_code = http_status
        return envelope

    @app.get(
        "/api/v1/reviews/{review_id}/status",
        tags=["reviews"],
        summary="Read staged review progress state",
        operation_id="getStagedReviewStatus",
        response_model=StagedReviewStatusResponse,
    )
    def staged_review_status(
        review_id: str, response: Response, auth: InternalAuthContext = Depends(require_internal_auth)
    ) -> StagedReviewStatusResponse:
        """Return the public safe view of run-local review_state.json."""

        http_status, envelope = review_service.get_staged_review_status(review_id, owner_id=auth.user_id)
        response.status_code = http_status
        return envelope

    @app.post(
        "/api/v1/reviews/{review_id}/builder",
        tags=["builder"],
        summary="Prepare Builder setup from a selected Launchpad card",
        operation_id="prepareBuilder",
        response_model=BuilderResponse,
    )
    def prepare_builder(review_id: str, request: BuilderRequest, response: Response, auth: InternalAuthContext = Depends(require_internal_auth)) -> BuilderResponse:
        """Prepare Builder setup through FastAPI without generating a candidate."""

        http_status, envelope = review_service.prepare_builder_setup(review_id, request, owner_id=auth.user_id)
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
        review_id: str, request: BuilderSetupIdRequest, response: Response, auth: InternalAuthContext = Depends(require_internal_auth)
    ) -> CandidateResponse:
        """Generate one diagnostic candidate through FastAPI."""

        http_status, envelope = review_service.generate_candidate_from_builder(review_id, request, owner_id=auth.user_id)
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
        review_id: str, request: CandidateIdRequest, response: Response, auth: InternalAuthContext = Depends(require_internal_auth)
    ) -> ComparisonResponse:
        """Run Current-vs-Candidate Comparison through FastAPI."""

        http_status, envelope = review_service.run_current_vs_candidate(review_id, request, owner_id=auth.user_id)
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
        review_id: str, request: ComparisonIdRequest, response: Response, auth: InternalAuthContext = Depends(require_internal_auth)
    ) -> VerdictResponse:
        """Generate non-binding Decision Verdict through FastAPI."""

        http_status, envelope = review_service.generate_decision_verdict(review_id, request, owner_id=auth.user_id)
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
        review_id: str, request: VerdictIdRequest, response: Response, auth: InternalAuthContext = Depends(require_internal_auth)
    ) -> ReportResponse:
        """Generate grounded report preview/context through FastAPI."""

        http_status, envelope = review_service.generate_report_grounding(review_id, request, owner_id=auth.user_id)
        response.status_code = http_status
        return envelope

    return app


app = create_app()
