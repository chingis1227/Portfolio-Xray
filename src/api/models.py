"""Pydantic contracts for the Portfolio MRI local FastAPI API.

These models define the public HTTP envelope and the planned MVP endpoint
surface. They are intentionally small display contracts over existing
portfolio-first artifacts; they do not run analytics or expose raw generated
artifact trees.
"""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator


API_VERSION = "v1"

ApiStage = Literal["health", "diagnosis", "recovery", "builder", "candidate", "comparison", "verdict", "report"]
ApiStatus = Literal["ok", "partial", "blocked", "failed"]
StagedReviewMode = Literal["demo_qa", "live"]
StagedReviewStatus = Literal["pending", "running", "completed", "partial", "blocked", "failed"]
StagedStageName = Literal[
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
StagedStageStatus = Literal["pending", "running", "completed", "partial", "blocked", "failed", "skipped"]
DataQuality = Literal["ok", "partial", "blocked", "unknown"]
Confidence = Literal["high", "medium", "low", "unknown"]
ClientFitTone = Literal["green", "amber", "red"]
StagedSafeErrorCode = Literal[
    "DATA_PROVIDER_FAILED",
    "INVALID_TICKER",
    "PYTHON_STAGE_FAILED",
    "TIMEOUT",
    "ARTIFACT_MISSING",
    "LINEAGE_MISMATCH",
]
StagedUserAction = Literal["fix_input", "retry", "return_to_portfolio_input", "contact_operator", "none"]
SafeErrorCode = Literal[
    "invalid_portfolio_input",
    "review_forbidden",
    "review_not_found",
    "lineage_mismatch",
    "stage_not_ready",
    "backend_failed",
    "artifact_missing",
    "artifact_stale",
    "data_quality_blocker",
    "candidate_generation_blocked",
    "comparison_unavailable",
    "verdict_unavailable",
    "report_unavailable",
    "unknown_error",
]
UserAction = Literal[
    "fix_input",
    "retry",
    "return_to_hypothesis",
    "rerun_comparison",
    "rerun_verdict",
    "contact_operator",
    "none",
]
NextAction = Literal[
    "prepare_builder",
    "recover_review",
    "resolve_data_quality",
    "generate_candidate",
    "select_another_card",
    "monitor",
    "run_comparison",
    "generate_verdict",
    "generate_report",
    "test_another_hypothesis",
    "rerun_comparison",
    "rerun_verdict",
]


class StrictModel(BaseModel):
    """Base class for public API contracts."""

    model_config = ConfigDict(extra="forbid")


class ApiLineage(StrictModel):
    """Lineage keys that keep the product chain same-review and same-candidate."""

    review_id: str | None = None
    selected_card_id: str | None = None
    builder_setup_id: str | None = None
    candidate_id: str | None = None
    comparison_id: str | None = None
    verdict_id: str | None = None
    product_run_id: str | None = None


class ArtifactRef(StrictModel):
    """Safe artifact reference without local absolute paths."""

    kind: str = Field(description="Product artifact role, for example portfolio_xray or decision_verdict.")
    ref: str = Field(description="Run-local or logical artifact reference safe for UI display.")
    scope: Literal["run_local", "analysis_subject", "logical"] = "run_local"
    raw_path_exposed: Literal[False] = False


class ApiEvidence(StrictModel):
    """Evidence quality summary for a response envelope."""

    source_artifacts: list[ArtifactRef] = Field(default_factory=list)
    data_quality: DataQuality = "unknown"
    confidence: Confidence = "unknown"


class SafeError(StrictModel):
    """Public, bounded error shape safe for the frontend."""

    code: SafeErrorCode
    message: str
    user_action: UserAction
    retryable: bool
    details: list[str] = Field(default_factory=list)


class StagedSafeError(StrictModel):
    """Public staged-review error safe for polling UI display."""

    code: StagedSafeErrorCode
    message: str
    user_action: StagedUserAction
    retryable: bool
    stage: StagedStageName | None = None


class StagedProviderStatus(StrictModel):
    """Compact provider/freshness disclosure for staged review status."""

    source: str
    freshness: str
    message: str


class StagedStageState(StrictModel):
    """Run-local state for one staged review step."""

    status: StagedStageStatus = "pending"
    started_at: str | None = None
    completed_at: str | None = None
    artifact_refs: list[str] = Field(default_factory=list)


class StagedReviewStartedResponse(StrictModel):
    """Immediate response from starting a staged web review."""

    api_version: Literal["v1"] = API_VERSION
    schema_version: Literal["review_started_v1"] = "review_started_v1"
    review_id: str
    stage: Literal["diagnosis"] = "diagnosis"
    status: StagedReviewStatus
    current_stage: StagedStageName
    mode: StagedReviewMode
    warnings: list[str] = Field(default_factory=list)
    safe_error: StagedSafeError | None = None


class StagedReviewStatusResponse(StrictModel):
    """Public safe view of run-local review_state_v1."""

    api_version: Literal["v1"] = API_VERSION
    schema_version: Literal["review_state_v1"] = "review_state_v1"
    review_id: str
    stage: Literal["diagnosis"] = "diagnosis"
    status: StagedReviewStatus
    current_stage: StagedStageName
    mode: StagedReviewMode
    created_at: str | None = None
    updated_at: str | None = None
    stages: dict[str, StagedStageState] = Field(default_factory=dict)
    artifacts: dict[str, str] = Field(default_factory=dict)
    provider_status: StagedProviderStatus
    warnings: list[str] = Field(default_factory=list)
    safe_error: StagedSafeError | None = None


DataT = TypeVar("DataT", bound=BaseModel)


class ApiEnvelope(StrictModel, Generic[DataT]):
    """Common v1 response envelope."""

    api_version: Literal["v1"] = API_VERSION
    schema_version: str
    review_id: str | None = None
    stage: ApiStage
    status: ApiStatus
    lineage: ApiLineage = Field(default_factory=ApiLineage)
    data: DataT
    warnings: list[str] = Field(default_factory=list)
    safe_error: SafeError | None = None
    evidence: ApiEvidence = Field(default_factory=ApiEvidence)


class HealthData(StrictModel):
    service: Literal["portfolio-mri-api"] = "portfolio-mri-api"
    status: Literal["ok"] = "ok"
    api_version: Literal["v1"] = API_VERSION
    openapi_available: bool = False


class HoldingInput(StrictModel):
    type: Literal["instrument", "cash"] = "instrument"
    ticker: str | None = Field(default=None, min_length=1, max_length=32, examples=["VOO"])
    currency: Literal["USD", "EUR"] | None = None
    weight_pct: float = Field(gt=0, le=100, examples=[40.0])

    @model_validator(mode="after")
    def validate_holding_identity(self) -> "HoldingInput":
        if self.type == "instrument":
            if not self.ticker or not self.ticker.strip():
                raise ValueError("instrument holding requires ticker")
            if self.currency is not None:
                raise ValueError("instrument holding must not include currency")
        if self.type == "cash":
            if not self.currency:
                raise ValueError("cash holding requires currency")
            if self.ticker is not None:
                raise ValueError("cash holding must not include ticker")
        return self


class PortfolioInput(StrictModel):
    investor_currency: Literal["USD", "EUR"] = "USD"
    holdings: list[HoldingInput] = Field(min_length=1, max_length=50)


class ClientFitRangeInput(StrictModel):
    min: float = Field(ge=0, le=1, examples=[0.05])
    max: float = Field(ge=0, le=1, examples=[0.07])

    @model_validator(mode="after")
    def validate_range_order(self) -> "ClientFitRangeInput":
        if self.min >= self.max:
            raise ValueError("range min must be below max")
        return self


class ClientFitInput(StrictModel):
    """Client Fit V1 request object.

    This is an input contract only. It records the user's stated profile for
    future Client Fit checks; it does not approve suitability or change
    diagnosis behavior by itself.
    """

    preset_id: (
        Literal["ultra_conservative", "conservative", "balanced", "growth", "aggressive"] | None
    ) = None
    source: Literal["questionnaire", "preset_override", "manual_override", "imported", "missing"]
    source_quality: Literal["high", "medium", "low", "missing"]
    source_quality_reason: str | None = Field(default=None, max_length=240)
    horizon_years: float | None = Field(default=None, gt=0, examples=[7.0])
    target_return_range: ClientFitRangeInput | None = None
    target_vol_range: ClientFitRangeInput | None = None
    target_max_drawdown_pct: float | None = Field(default=None, ge=-1, le=0, examples=[-0.2])

    @model_validator(mode="after")
    def validate_missing_profile_boundary(self) -> "ClientFitInput":
        if self.source == "missing" or self.source_quality == "missing":
            if self.source != "missing" or self.source_quality != "missing":
                raise ValueError(
                    "missing Client Fit profile requires source='missing' and source_quality='missing'"
                )
            if any(
                value is not None
                for value in (
                    self.preset_id,
                    self.horizon_years,
                    self.target_return_range,
                    self.target_vol_range,
                    self.target_max_drawdown_pct,
                )
            ):
                raise ValueError("missing Client Fit profile must not include target fields")
            return self
        if not self.preset_id and not (
            self.horizon_years
            and self.target_return_range
            and self.target_vol_range
            and self.target_max_drawdown_pct is not None
        ):
            raise ValueError("Client Fit profile requires a preset_id or complete manual targets")
        return self


class CreateReviewOptions(StrictModel):
    mode: Literal["diagnosis_only"] = "diagnosis_only"
    output_profile: Literal["site_api"] = "site_api"
    sample_mode: bool = False


class CreateReviewRequest(StrictModel):
    portfolio: PortfolioInput
    client_fit: ClientFitInput | None = None
    options: CreateReviewOptions = Field(default_factory=CreateReviewOptions)


class ReviewSummary(StrictModel):
    review_id: str | None = None
    investor_currency: Literal["USD", "EUR"] | None = None
    analysis_window: str | None = None
    data_quality: DataQuality = "unknown"
    input_weight_total_pct: float | None = None


class DiagnosisSummary(StrictModel):
    primary_diagnosis: str | None = None
    headline: str | None = None
    confidence: Confidence = "unknown"
    evidence_chain: list[str] = Field(default_factory=list)
    next_diagnostic_step: str | None = None
    selected_diagnosis_role: str | None = None
    source_artifacts: list[str] = Field(default_factory=list)
    diagnosis_evidence_items: list["DiagnosisEvidenceItem"] = Field(default_factory=list)
    root_cause_narrative: "DiagnosisRootCauseNarrative | None" = None
    metric_to_diagnosis_trace: list["DiagnosisMetricTrace"] = Field(default_factory=list)
    rejected_alternatives: list["DiagnosisRejectedAlternative"] = Field(default_factory=list)
    professional_rationale_refs: list["DiagnosisRationaleRef"] = Field(default_factory=list)
    recommendation_boundary: str | None = None


class ClientFitTargetDisplayRow(StrictModel):
    dimension_label: str
    portfolio_value_label: str | None = None
    target_or_limit_label: str | None = None
    status_label: str
    status_tone: ClientFitTone
    explanation: str | None = None


class ClientFitDisplaySummary(StrictModel):
    status_label: str = "Client Fit not provided"
    status_tone: ClientFitTone = "amber"
    profile_label: str | None = None
    source_quality_label: str | None = None
    target_rows: list[ClientFitTargetDisplayRow] = Field(default_factory=list)
    main_explanation: str | None = None
    decision_boundary: str = (
        "Client Fit is non-binding decision support. It does not approve suitability, "
        "execute trades, or clear unresolved diagnostics by itself."
    )
    next_best_test: str | None = None


class DiagnosisEvidenceItem(StrictModel):
    evidence_item_id: str | None = None
    linked_problem_id: str | None = None
    evidence_role: str | None = None
    signal: str | None = None
    source_artifact: str | None = None
    source_block: str | None = None
    source_field_path: str | None = None
    observed_value: Any = None
    interpretation: str | None = None
    why_relevant: str | None = None
    severity: str | None = None
    confidence: Confidence = "unknown"
    limitation: str | None = None


class DiagnosisRootCauseNarrative(StrictModel):
    diagnosis_id: str | None = None
    label: str | None = None
    diagnosis_role: str | None = None
    statement: str | None = None
    root_cause_over_symptom: str | None = None
    portfolio_manager_interpretation: str | None = None
    confidence_context: str | None = None
    supporting_evidence_count: int | None = None
    rejected_alternative_count: int | None = None
    source_refs: list[str] = Field(default_factory=list)


class DiagnosisMetricTrace(StrictModel):
    trace_id: str | None = None
    source_artifact: str | None = None
    source_block: str | None = None
    source_field_path: str | None = None
    metric_or_signal: str | None = None
    evidence_item_id: str | None = None
    linked_problem_id: str | None = None
    contributes_to_selected_diagnosis_id: str | None = None
    contribution: str | None = None
    interpretation: str | None = None


class DiagnosisRejectedAlternative(StrictModel):
    problem_id: str | None = None
    label: str | None = None
    reason_code: str | None = None
    reason: str | None = None
    top_evidence_item_ids: list[str] = Field(default_factory=list)


class DiagnosisRationaleRef(StrictModel):
    ref_id: str | None = None
    source: str | None = None
    problem_id: str | None = None
    reason: str | None = None
    rationale: str | None = None


class LaunchpadCardSummary(StrictModel):
    card_id: str
    title: str
    method_id: str | None = None
    generation_allowed: bool = False
    is_rebalance_recommendation: Literal[False] = False


class ReviewCreatedData(StrictModel):
    review_summary: ReviewSummary = Field(default_factory=ReviewSummary)
    diagnosis: DiagnosisSummary = Field(default_factory=DiagnosisSummary)
    client_fit: ClientFitDisplaySummary = Field(default_factory=ClientFitDisplaySummary)
    launchpad: list[LaunchpadCardSummary] = Field(default_factory=list)
    next_allowed_actions: list[NextAction] = Field(default_factory=list)
    artifact_refs: list[ArtifactRef] = Field(default_factory=list)


class ReviewRecoveryData(ReviewCreatedData):
    downstream_artifacts_restored_as_active: bool = False
    restored_active_stages: list[Literal["diagnosis", "evidence", "hypothesis_setup"]] = Field(default_factory=list)


class BuilderOverrides(StrictModel):
    method_id: (
        Literal[
            "equal_weight",
            "risk_parity",
            "hierarchical_risk_parity",
            "minimum_variance",
            "minimum_cvar",
            "maximum_diversification",
        ]
        | None
    ) = None
    mode: Literal["capped", "uncapped"] | None = None
    min_asset_weight: float | None = Field(default=None, ge=0, le=1)
    max_asset_weight: float | None = Field(default=None, ge=0, le=1)


class BuilderRequest(StrictModel):
    selected_card_id: str = Field(min_length=1)
    overrides: BuilderOverrides = Field(default_factory=BuilderOverrides)


class BuilderSetupSummary(StrictModel):
    builder_setup_id: str | None = None
    selected_card_id: str | None = None
    method_id: str | None = None
    mode: str | None = None
    success_criteria: list[str] = Field(default_factory=list)
    tradeoff_to_watch: str | None = None
    decision_boundary: str | None = None
    generation_readiness: Literal["ready", "blocked", "unknown"] = "unknown"


class BuilderData(StrictModel):
    builder_setup: BuilderSetupSummary = Field(default_factory=BuilderSetupSummary)
    candidate_generation_allowed: bool = False
    next_allowed_actions: list[NextAction] = Field(default_factory=list)


class BuilderSetupIdRequest(StrictModel):
    builder_setup_id: str = Field(min_length=1)


class CandidateSummary(StrictModel):
    candidate_id: str | None = None
    method_label: str | None = None
    generation_status: Literal["generated", "blocked", "failed", "unknown"] = "unknown"
    weight_summary: dict[str, float] | None = None
    infeasible_reason: str | None = None


class HypothesisSummary(StrictModel):
    diagnosis_id: str | None = None
    hypothesis: str | None = None
    success_criteria: list[str] = Field(default_factory=list)
    tradeoff_to_watch: str | None = None
    decision_boundary: str | None = None


class CandidateData(StrictModel):
    candidate: CandidateSummary = Field(default_factory=CandidateSummary)
    hypothesis: HypothesisSummary = Field(default_factory=HypothesisSummary)
    is_rebalance_recommendation: Literal[False] = False
    next_allowed_actions: list[NextAction] = Field(default_factory=list)


class CandidateIdRequest(StrictModel):
    candidate_id: str = Field(min_length=1)




class DownstreamEvidenceChainContext(StrictModel):
    selected_diagnosis_id: str | None = None
    selected_diagnosis_label: str | None = None
    selected_diagnosis_role: str | None = None
    diagnosis_statement: str | None = None
    tested_hypothesis: str | None = None
    success_criteria: list[str] = Field(default_factory=list)
    tradeoff_to_watch: str | None = None
    candidate_boundary: str | None = None
    recommendation_boundary: str | None = None
    source_artifacts: list[str] = Field(default_factory=list)

class ComparisonSummary(StrictModel):
    comparison_id: str | None = None
    current_label: str = "Current portfolio"
    candidate_label: str | None = None
    success_criteria_result: Literal["passed", "partial", "failed", "unavailable", "unknown"] = "unknown"
    what_improved: list[str] = Field(default_factory=list)
    what_worsened: list[str] = Field(default_factory=list)
    what_stayed_similar: list[str] = Field(default_factory=list)
    unavailable_metrics: list[str] = Field(default_factory=list)
    materiality: Literal["material", "immaterial", "unknown"] = "unknown"


class ComparisonData(StrictModel):
    comparison: ComparisonSummary = Field(default_factory=ComparisonSummary)
    evidence_chain_context: DownstreamEvidenceChainContext = Field(default_factory=DownstreamEvidenceChainContext)
    client_fit: ClientFitDisplaySummary = Field(default_factory=ClientFitDisplaySummary)
    next_allowed_actions: list[NextAction] = Field(default_factory=list)


class ComparisonIdRequest(StrictModel):
    comparison_id: str = Field(min_length=1)


class VerdictSummary(StrictModel):
    verdict_id: str | None = None
    verdict: Literal[
        "keep_current",
        "no_material_rebalance",
        "rebalance_review",
        "test_another_candidate",
        "candidate_failed_or_infeasible",
        "evidence_insufficient",
        "unknown",
    ] = "unknown"
    rationale: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    what_would_change_verdict: list[str] = Field(default_factory=list)
    confidence: Confidence = "unknown"
    limitations: list[str] = Field(default_factory=list)
    decision_support_only: Literal[True] = True


class VerdictData(StrictModel):
    verdict: VerdictSummary = Field(default_factory=VerdictSummary)
    evidence_chain_context: DownstreamEvidenceChainContext = Field(default_factory=DownstreamEvidenceChainContext)
    client_fit: ClientFitDisplaySummary = Field(default_factory=ClientFitDisplaySummary)
    next_allowed_actions: list[NextAction] = Field(default_factory=list)


class VerdictIdRequest(StrictModel):
    verdict_id: str = Field(min_length=1)


class ReportPreview(StrictModel):
    executive_summary: str | None = None
    current_portfolio_diagnosis: str | None = None
    stress_evidence: list[str] = Field(default_factory=list)
    tested_hypothesis: str | None = None
    candidate_boundary: str | None = None
    comparison_tradeoffs: list[str] = Field(default_factory=list)
    verdict_explanation: str | None = None
    evidence_limitations: list[str] = Field(default_factory=list)
    monitoring_note: str | None = None


class ReportGrounding(StrictModel):
    source_refs: list[ArtifactRef] = Field(default_factory=list)
    unavailable_sections: list[str] = Field(default_factory=list)


class ReportData(StrictModel):
    report_preview: ReportPreview = Field(default_factory=ReportPreview)
    grounding: ReportGrounding = Field(default_factory=ReportGrounding)
    evidence_chain_context: DownstreamEvidenceChainContext = Field(default_factory=DownstreamEvidenceChainContext)
    client_fit: ClientFitDisplaySummary = Field(default_factory=ClientFitDisplaySummary)
    llm_generated: Literal[False] = False


class HealthResponse(ApiEnvelope[HealthData]):
    pass


class CreateReviewResponse(ApiEnvelope[ReviewCreatedData]):
    pass


class ReviewRecoveryResponse(ApiEnvelope[ReviewRecoveryData]):
    pass


class BuilderResponse(ApiEnvelope[BuilderData]):
    pass


class CandidateResponse(ApiEnvelope[CandidateData]):
    pass


class ComparisonResponse(ApiEnvelope[ComparisonData]):
    pass


class VerdictResponse(ApiEnvelope[VerdictData]):
    pass


class ReportResponse(ApiEnvelope[ReportData]):
    pass
