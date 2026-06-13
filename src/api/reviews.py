"""Runtime adapters for FastAPI portfolio-review stages.

This module bridges the typed FastAPI contract to the existing deterministic
portfolio-first review runner and one-candidate vertical-loop helpers. It
deliberately reuses current analytics and artifact writers instead of changing
portfolio formulas, generated artifact schemas, root ``config.yml``, or
frontend routing behavior.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from scripts.run_review_from_payload import (
    DEFAULT_TIMEOUT_SECONDS,
    BuilderSelectionError,
    CandidateBridgeError,
    ComparisonBridgeError,
    MODE_DIAGNOSIS_PLUS_PROBLEM,
    PROJECT_ROOT,
    PayloadValidationError,
    ReportBridgeError,
    VerdictBridgeError,
    compare_selected_candidate,
    generate_selected_candidate,
    prepare_selected_builder_setup,
    run_from_payload,
    safe_review_run_dir,
    scrub_failure_text,
    write_selected_candidate_verdict,
    write_selected_report_context,
    write_json,
)
from src.api.models import (
    API_VERSION,
    ApiEvidence,
    ApiLineage,
    ArtifactRef,
    BuilderData,
    BuilderRequest,
    BuilderResponse,
    BuilderSetupIdRequest,
    BuilderSetupSummary,
    CandidateData,
    CandidateIdRequest,
    CandidateResponse,
    CandidateSummary,
    ClientFitDisplaySummary,
    ClientFitTargetDisplayRow,
    ComparisonData,
    ComparisonIdRequest,
    ComparisonResponse,
    ComparisonSummary,
    Confidence,
    CreateReviewRequest,
    CreateReviewResponse,
    DiagnosisEvidenceItem,
    DiagnosisMetricTrace,
    DiagnosisRationaleRef,
    DiagnosisRejectedAlternative,
    DiagnosisRootCauseNarrative,
    DiagnosisSummary,
    DownstreamEvidenceChainContext,
    HypothesisSummary,
    LaunchpadCardSummary,
    ReportData,
    ReportGrounding,
    ReportPreview,
    ReportResponse,
    ReviewCreatedData,
    ReviewRecoveryData,
    ReviewRecoveryResponse,
    ReviewSummary,
    SafeError,
    VerdictData,
    VerdictIdRequest,
    VerdictResponse,
    VerdictSummary,
)


CREATE_REVIEW_SCHEMA_VERSION = "review_create_v1"
RECOVERY_SCHEMA_VERSION = "review_recovery_v1"
BUILDER_SCHEMA_VERSION = "builder_setup_v1"
CANDIDATE_SCHEMA_VERSION = "candidate_generation_v1"
COMPARISON_SCHEMA_VERSION = "current_vs_candidate_v1"
VERDICT_SCHEMA_VERSION = "decision_verdict_v1"
REPORT_SCHEMA_VERSION = "report_grounding_v1"
PAYLOAD_DIR = PROJECT_ROOT / "runs" / "fastapi_review_payloads"
SAFE_REF_RE = re.compile(r"^[A-Za-z]:[\\/]|^/(...:Users|home|var|tmp|mnt)/")


def _record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _number_map(value: Any) -> dict[str, float] | None:
    if not isinstance(value, dict):
        return None
    result: dict[str, float] = {}
    for key, raw in value.items():
        if isinstance(key, str) and isinstance(raw, (int, float)) and not isinstance(raw, bool):
            result[key] = float(raw)
    return result or None


def _text(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _confidence(value: Any) -> Confidence:
    normalized = str(value or "").strip().lower()
    if normalized in {"high", "medium", "low"}:
        return normalized  # type: ignore[return-value]
    return "unknown"


def _string_list(value: Any) -> list[str]:
    return [str(item).strip() for item in _list(value) if item is not None and str(item).strip()]


def _format_api_percent(value: Any) -> str | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return f"{float(value) * 100:.1f}%"


def _client_fit_tone(status: Any) -> str:
    normalized = str(status or "").strip().lower()
    if normalized == "fit":
        return "green"
    if normalized in {"breach", "conflict"}:
        return "red"
    return "amber"


def _client_fit_status_label(status: Any) -> str:
    normalized = str(status or "").strip().lower()
    labels = {
        "fit": "Within stated Client Fit profile",
        "watch": "Client Fit watch",
        "breach": "Outside stated Client Fit limits",
        "conflict": "Goal-risk conflict",
        "evidence_insufficient": "Client Fit evidence insufficient",
        "not_provided": "Client Fit not provided",
    }
    return labels.get(normalized, "Client Fit not provided")


def _client_fit_dimension_label(dimension: Any) -> str:
    key = str(dimension or "").strip()
    labels = {
        "return_target_gap": "Return target",
        "volatility_vs_target": "Volatility comfort range",
        "historical_max_drawdown_vs_limit": "Historical drawdown limit",
        "worst_stress_loss_vs_limit": "Worst stress loss limit",
        "horizon_risk_mismatch": "Investment horizon",
        "goal_risk_conflict": "Goal-risk consistency",
    }
    return labels.get(key, key.replace("_", " ").title() if key else "Client Fit check")


def _client_fit_target_label(row: dict[str, Any]) -> str | None:
    client_range = _record(row.get("client_range"))
    if client_range:
        lo = _format_api_percent(client_range.get("min"))
        hi = _format_api_percent(client_range.get("max"))
        if lo and hi:
            return f"{lo} to {hi}"
    limit = _format_api_percent(row.get("client_limit"))
    if limit:
        return f"Limit: {limit}"
    if row.get("client_limit") is None and row.get("dimension") == "horizon_risk_mismatch":
        horizon = row.get("portfolio_value")
        if isinstance(horizon, (int, float)) and not isinstance(horizon, bool):
            return f"{float(horizon):.0f} years"
    return None


def _client_fit_rows_for_api(client_fit_check: dict[str, Any]) -> list[ClientFitTargetDisplayRow]:
    rows: list[ClientFitTargetDisplayRow] = []
    for raw_row in _list(client_fit_check.get("checks")):
        row = _record(raw_row)
        if not row:
            continue
        rows.append(
            ClientFitTargetDisplayRow(
                dimension_label=_client_fit_dimension_label(row.get("dimension")),
                portfolio_value_label=_format_api_percent(row.get("portfolio_value"))
                or (str(row.get("portfolio_value")) if row.get("portfolio_value") is not None else None),
                target_or_limit_label=_client_fit_target_label(row),
                status_label=_client_fit_status_label(row.get("status")),
                status_tone=_client_fit_tone(row.get("status")),  # type: ignore[arg-type]
                explanation=_text(row.get("interpretation")),
            )
        )
    return rows[:6]


def _client_fit_display_summary(
    client_fit_check: dict[str, Any] | None = None,
    *,
    decision_context: dict[str, Any] | None = None,
) -> ClientFitDisplaySummary:
    context = _record(decision_context)
    check = _record(client_fit_check)
    status = _text(context.get("client_fit_status"), check.get("client_fit_status"), "not_provided")
    profile = _record(check.get("profile"))
    checks = [_record(item) for item in _list(check.get("checks"))]
    first_non_fit = next(
        (
            row
            for row in checks
            if _text(row.get("status")) not in {None, "", "fit"}
        ),
        {},
    )
    return ClientFitDisplaySummary(
        status_label=_text(context.get("status_label")) or _client_fit_status_label(status),
        status_tone=_text(context.get("status_tone")) or _client_fit_tone(status),  # type: ignore[arg-type]
        profile_label=_text(context.get("profile_label"), profile.get("preset_id")),
        source_quality_label=_text(context.get("source_quality_label"), profile.get("source_quality")),
        target_rows=_client_fit_rows_for_api(check),
        main_explanation=_text(
            context.get("next_best_test_en"),
            first_non_fit.get("interpretation"),
            check.get("recommendation_boundary"),
        ),
        decision_boundary=_text(context.get("boundary_en"), check.get("recommendation_boundary"))
        or ClientFitDisplaySummary().decision_boundary,
        next_best_test=_text(context.get("next_best_test_en")),
    )


def _safe_ref(value: Any, *, fallback: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return fallback
    ref = value.strip().replace("\\", "/")
    if SAFE_REF_RE.search(ref):
        return fallback
    return ref


def _artifact_refs(paths: dict[str, Any]) -> list[ArtifactRef]:
    allowed = {
        "portfolio_xray",
        "stress_report",
        "run_metadata",
        "output_manifest",
        "problem_classification",
        "candidate_launchpad",
        "portfolio_alternatives_builder",
        "client_fit_check",
        "ai_commentary_context",
        "site_explanation_bundle",
    }
    refs: list[ArtifactRef] = []
    for key in sorted(allowed):
        if key in paths:
            refs.append(
                ArtifactRef(
                    kind=key,
                    ref=_safe_ref(paths.get(key), fallback=f"logical://{key}"),
                    scope="analysis_subject" if key != "run_dir" else "run_local",
                )
            )
    return refs


def _stage_artifact_ref(kind: str, ref: str, scope: str = "run_local") -> ArtifactRef:
    return ArtifactRef(
        kind=kind,
        ref=_safe_ref(ref, fallback=f"logical://{kind}"),
        scope=scope,  # type: ignore[arg-type]
    )


def _read_json_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} is not a JSON object.")
    return data


def _request_to_bridge_payload(request: CreateReviewRequest) -> dict[str, Any]:
    """Convert the public FastAPI input model to the existing runner payload.

    Session 07 keeps parity with the frontend input contract: instrument rows
    pass through as tickers, and real-cash rows pass through as cash holdings so
    the normal FastAPI path preserves the existing ``Cash USD`` / ``Cash EUR``
    portfolio behavior.
    """

    holdings: list[dict[str, Any]] = []
    for holding in request.portfolio.holdings:
        if holding.type == "cash":
            holdings.append(
                {
                    "type": "cash",
                    "currency": str(holding.currency).strip().upper(),
                    "weight": holding.weight_pct,
                }
            )
            continue
        holdings.append(
            {
                "type": "instrument",
                "ticker": str(holding.ticker).strip().upper(),
                "weight": holding.weight_pct,
            }
        )

    payload: dict[str, Any] = {
        "investor_currency": request.portfolio.investor_currency,
        "holdings": holdings,
    }
    if request.client_fit is not None:
        payload["client_fit"] = request.client_fit.model_dump(mode="json", exclude_none=True)
    return payload


def _review_summary(review_result: dict[str, Any], outputs: dict[str, Any]) -> ReviewSummary:
    portfolio_input = _record(review_result.get("portfolio_input"))
    run_metadata = _record(outputs.get("run_metadata"))
    analysis_setup = _record(run_metadata.get("analysis_setup"))
    input_assumptions = _record(run_metadata.get("input_assumptions"))
    analysis_window = _text(
        analysis_setup.get("analysis_window"),
        input_assumptions.get("analysis_window"),
        run_metadata.get("analysis_end"),
        _record(outputs.get("problem_classification")).get("analysis_end"),
    )
    return ReviewSummary(
        review_id=_text(review_result.get("review_id")),
        investor_currency=_text(portfolio_input.get("investor_currency")),  # type: ignore[arg-type]
        analysis_window=analysis_window,
        data_quality="ok",
        input_weight_total_pct=(
            float(portfolio_input["total_weight"])
            if isinstance(portfolio_input.get("total_weight"), (int, float))
            else None
        ),
    )


def _diagnosis_summary(outputs: dict[str, Any]) -> DiagnosisSummary:
    problem = _record(outputs.get("problem_classification"))
    primary = _record(problem.get("primary_diagnosis"))
    chain = _record(problem.get("interpretation_chain"))
    root_cause = _record(primary.get("root_cause") or problem.get("root_cause"))
    root_narrative = _record(
        problem.get("root_cause_narrative") or chain.get("root_cause_narrative")
    )
    next_step = _record(problem.get("next_diagnostic_step"))
    chain_evidence_rows = _list(
        problem.get("diagnosis_evidence_items") or chain.get("diagnosis_evidence_items")
    )
    evidence_rows = (chain_evidence_rows or _list(primary.get("key_evidence") or problem.get("key_evidence")))[:5]
    evidence_chain = [
        text
        for row in evidence_rows
        if isinstance(row, dict)
        for text in [_text(row.get("interpretation_en"), row.get("interpretation"), row.get("signal"))]
        if text
    ]
    next_step_link = _record(chain.get("next_step_link"))

    return DiagnosisSummary(
        primary_diagnosis=_text(
            chain.get("selected_diagnosis_id"),
            primary.get("diagnosis_id"),
            root_narrative.get("diagnosis_id"),
            root_cause.get("problem_id"),
            _record(problem.get("summary")).get("primary_problem_id"),
        ),
        headline=_text(
            root_narrative.get("statement_en"),
            root_narrative.get("statement"),
            primary.get("thesis_en"),
            primary.get("label_en"),
            root_cause.get("label_en"),
            problem.get("why_this_matters"),
        ),
        confidence=_confidence(primary.get("confidence") or problem.get("confidence")),
        evidence_chain=evidence_chain,
        next_diagnostic_step=_text(
            next_step_link.get("label"),
            next_step.get("label"),
            next_step.get("reason"),
            _record(primary.get("actionability")).get("headline_en"),
        ),
        selected_diagnosis_role=_text(chain.get("selected_diagnosis_role"), root_narrative.get("diagnosis_role")),
        source_artifacts=_string_list(chain.get("source_artifacts")),
        diagnosis_evidence_items=_diagnosis_evidence_items_for_api(chain_evidence_rows),
        root_cause_narrative=_root_cause_narrative_for_api(root_narrative),
        metric_to_diagnosis_trace=_diagnosis_metric_trace_for_api(
            problem.get("metric_to_diagnosis_trace") or chain.get("metric_to_diagnosis_trace")
        ),
        rejected_alternatives=_diagnosis_rejected_alternatives_for_api(chain.get("rejected_alternatives")),
        professional_rationale_refs=_diagnosis_rationale_refs_for_api(
            problem.get("professional_rationale_refs") or chain.get("professional_rationale_refs")
        ),
        recommendation_boundary=_text(
            chain.get("recommendation_boundary_en"),
            next_step_link.get("decision_boundary"),
            next_step.get("decision_boundary"),
        ),
    )


def _diagnosis_evidence_items_for_api(rows: Any) -> list[DiagnosisEvidenceItem]:
    items: list[DiagnosisEvidenceItem] = []
    for raw_row in _list(rows)[:10]:
        row = _record(raw_row)
        if not row:
            continue
        items.append(
            DiagnosisEvidenceItem(
                evidence_item_id=_text(row.get("evidence_item_id"), row.get("evidence_id")),
                linked_problem_id=_text(row.get("linked_problem_id"), row.get("problem_id")),
                evidence_role=_text(row.get("evidence_role")),
                signal=_text(row.get("signal")),
                source_artifact=_text(row.get("source_artifact")),
                source_block=_text(row.get("source_block")),
                source_field_path=_text(row.get("source_field_path"), row.get("evidence_path")),
                observed_value=row.get("observed_value"),
                interpretation=_text(row.get("interpretation_en"), row.get("interpretation")),
                why_relevant=_text(row.get("why_relevant_to_diagnosis_en"), row.get("why_relevant")),
                severity=_text(row.get("severity")),
                confidence=_confidence(row.get("confidence")),
                limitation=_text(row.get("limitation_en"), row.get("limitation")),
            )
        )
    return items


def _root_cause_narrative_for_api(row: dict[str, Any]) -> DiagnosisRootCauseNarrative | None:
    if not row:
        return None
    return DiagnosisRootCauseNarrative(
        diagnosis_id=_text(row.get("diagnosis_id")),
        label=_text(row.get("label_en"), row.get("label")),
        diagnosis_role=_text(row.get("diagnosis_role")),
        statement=_text(row.get("statement_en"), row.get("statement")),
        root_cause_over_symptom=_text(row.get("root_cause_over_symptom_en"), row.get("root_cause_over_symptom")),
        portfolio_manager_interpretation=_text(
            row.get("portfolio_manager_interpretation_en"),
            row.get("portfolio_manager_interpretation"),
        ),
        confidence_context=_text(row.get("confidence_context_en"), row.get("confidence_context")),
        supporting_evidence_count=(
            int(row["n_supporting_evidence_items"])
            if isinstance(row.get("n_supporting_evidence_items"), int)
            else None
        ),
        rejected_alternative_count=(
            int(row["n_rejected_alternatives"])
            if isinstance(row.get("n_rejected_alternatives"), int)
            else None
        ),
        source_refs=_string_list(row.get("source_refs")),
    )


def _diagnosis_metric_trace_for_api(rows: Any) -> list[DiagnosisMetricTrace]:
    trace: list[DiagnosisMetricTrace] = []
    for raw_row in _list(rows)[:10]:
        row = _record(raw_row)
        if not row:
            continue
        trace.append(
            DiagnosisMetricTrace(
                trace_id=_text(row.get("trace_id")),
                source_artifact=_text(row.get("source_artifact")),
                source_block=_text(row.get("source_block")),
                source_field_path=_text(row.get("source_field_path")),
                metric_or_signal=_text(row.get("metric_or_signal"), row.get("signal")),
                evidence_item_id=_text(row.get("evidence_item_id")),
                linked_problem_id=_text(row.get("linked_problem_id")),
                contributes_to_selected_diagnosis_id=_text(row.get("contributes_to_selected_diagnosis_id")),
                contribution=_text(row.get("contribution")),
                interpretation=_text(row.get("interpretation_en"), row.get("interpretation")),
            )
        )
    return trace


def _diagnosis_rejected_alternatives_for_api(rows: Any) -> list[DiagnosisRejectedAlternative]:
    alternatives: list[DiagnosisRejectedAlternative] = []
    for raw_row in _list(rows)[:5]:
        row = _record(raw_row)
        if not row:
            continue
        alternatives.append(
            DiagnosisRejectedAlternative(
                problem_id=_text(row.get("problem_id")),
                label=_text(row.get("label_en"), row.get("label")),
                reason_code=_text(row.get("reason_code")),
                reason=_text(row.get("reason_en"), row.get("reason")),
                top_evidence_item_ids=_string_list(row.get("top_evidence_item_ids")),
            )
        )
    return alternatives


def _diagnosis_rationale_refs_for_api(rows: Any) -> list[DiagnosisRationaleRef]:
    refs: list[DiagnosisRationaleRef] = []
    for raw_row in _list(rows)[:8]:
        row = _record(raw_row)
        if not row:
            continue
        refs.append(
            DiagnosisRationaleRef(
                ref_id=_text(row.get("ref_id")),
                source=_text(row.get("source")),
                problem_id=_text(row.get("problem_id")),
                reason=_text(row.get("reason_en"), row.get("reason")),
                rationale=_text(row.get("rationale_en"), row.get("rationale")),
            )
        )
    return refs


def _launchpad_summary(outputs: dict[str, Any]) -> list[LaunchpadCardSummary]:
    launchpad = _record(outputs.get("candidate_launchpad"))
    cards: list[LaunchpadCardSummary] = []
    for raw_card in _list(launchpad.get("cards")):
        card = _record(raw_card)
        card_id = _text(card.get("card_id"))
        if not card_id:
            continue
        methods = [_record(item) for item in _list(card.get("suggested_methods"))]
        first_method = next(
            (
                _text(method.get("candidate_method_id"), method.get("method_id"))
                for method in methods
                if _text(method.get("candidate_method_id"), method.get("method_id"))
            ),
            None,
        )
        generation_allowed = bool(first_method) and str(card.get("card_type")) != "monitor_or_data_step"
        cards.append(
            LaunchpadCardSummary(
                card_id=card_id,
                title=_text(card.get("title"), card.get("goal"), card_id) or card_id,
                method_id=_text(card.get("default_method"), first_method),
                generation_allowed=generation_allowed,
                is_rebalance_recommendation=False,
            )
        )
    return cards


def _warnings_from_outputs(outputs: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for key in ("problem_classification", "candidate_launchpad", "portfolio_xray", "stress_report"):
        artifact = _record(outputs.get(key))
        for item in _list(artifact.get("warnings")):
            if isinstance(item, str) and item.strip():
                warnings.append(item.strip())
    return warnings


def _created_data(review_result: dict[str, Any]) -> ReviewCreatedData:
    outputs = _record(review_result.get("outputs"))
    paths = _record(review_result.get("paths"))
    review_id = _text(review_result.get("review_id"))
    client_fit_check = _record(outputs.get("client_fit_check"))
    if not client_fit_check and review_id:
        client_fit_check = _read_run_local_json_or_empty(review_id, "analysis_subject/client_fit_check.json")
        if client_fit_check and "client_fit_check" not in paths:
            paths = {**paths, "client_fit_check": f"runs/{review_id}/analysis_subject/client_fit_check.json"}
    launchpad = _launchpad_summary(outputs)
    has_generatable_card = any(card.generation_allowed for card in launchpad)
    next_allowed = ["prepare_builder" if has_generatable_card else "resolve_data_quality", "recover_review"]
    return ReviewCreatedData(
        review_summary=_review_summary(review_result, outputs),
        diagnosis=_diagnosis_summary(outputs),
        client_fit=_client_fit_display_summary(client_fit_check),
        launchpad=launchpad,
        next_allowed_actions=next_allowed,  # type: ignore[arg-type]
        artifact_refs=_artifact_refs(paths),
    )


def _evidence_from_data(data: ReviewCreatedData) -> ApiEvidence:
    confidence = data.diagnosis.confidence if data.diagnosis.confidence != "unknown" else "medium"
    return ApiEvidence(
        source_artifacts=data.artifact_refs,
        data_quality=data.review_summary.data_quality,
        confidence=confidence,
    )


def _safe_error(
    *,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
    details: list[str] | None = None,
) -> SafeError:
    return SafeError(
        code=code,  # type: ignore[arg-type]
        message=scrub_failure_text(message),
        user_action=user_action,  # type: ignore[arg-type]
        retryable=retryable,
        details=[scrub_failure_text(item) for item in (details or []) if item],
    )


def _error_code_for_stage_exception(exc: BaseException, *, stage: str) -> tuple[int, str, str, bool]:
    """Map internal bridge exceptions to bounded public API errors."""

    message = str(exc)
    lowered = message.lower()
    if "not found" in lowered or "was not found" in lowered:
        return 404, "review_not_found" if "review run" in lowered else "artifact_missing", "none", False
    if "does not match" in lowered or "mismatch" in lowered or "different review" in lowered:
        return 409, "lineage_mismatch", "return_to_hypothesis", False
    if "cannot generate" in lowered or "not generatable" in lowered or "data_quality" in lowered:
        return (
            409,
            "candidate_generation_blocked" if stage == "candidate" else "data_quality_blocker",
            "return_to_hypothesis",
            False,
        )
    return 500, "backend_failed", "retry", True


def _failed_create_envelope(
    *,
    review_id: str | None,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
    details: list[str] | None = None,
) -> CreateReviewResponse:
    return CreateReviewResponse(
        api_version=API_VERSION,
        schema_version=CREATE_REVIEW_SCHEMA_VERSION,
        review_id=review_id,
        stage="diagnosis",
        status="failed",
        lineage=ApiLineage(review_id=review_id),
        data=ReviewCreatedData(next_allowed_actions=[]),
        warnings=[],
        safe_error=_safe_error(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
        evidence=ApiEvidence(source_artifacts=[], data_quality="unknown", confidence="unknown"),
    )


def _failed_builder_envelope(
    *,
    review_id: str,
    selected_card_id: str | None,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
    details: list[str] | None = None,
) -> BuilderResponse:
    return BuilderResponse(
        api_version=API_VERSION,
        schema_version=BUILDER_SCHEMA_VERSION,
        review_id=review_id,
        stage="builder",
        status="failed",
        lineage=ApiLineage(review_id=review_id, selected_card_id=selected_card_id),
        data=BuilderData(next_allowed_actions=["select_another_card"] if selected_card_id else []),
        warnings=[],
        safe_error=_safe_error(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
        evidence=ApiEvidence(source_artifacts=[], data_quality="unknown", confidence="unknown"),
    )


def _failed_candidate_envelope(
    *,
    review_id: str,
    builder_setup_id: str | None,
    selected_card_id: str | None = None,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
    details: list[str] | None = None,
) -> CandidateResponse:
    return CandidateResponse(
        api_version=API_VERSION,
        schema_version=CANDIDATE_SCHEMA_VERSION,
        review_id=review_id,
        stage="candidate",
        status="failed",
        lineage=ApiLineage(
            review_id=review_id,
            selected_card_id=selected_card_id,
            builder_setup_id=builder_setup_id,
        ),
        data=CandidateData(next_allowed_actions=["select_another_card"]),
        warnings=[],
        safe_error=_safe_error(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
        evidence=ApiEvidence(source_artifacts=[], data_quality="unknown", confidence="unknown"),
    )


def _failed_comparison_envelope(
    *,
    review_id: str,
    candidate_id: str | None,
    selected_card_id: str | None = None,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
    details: list[str] | None = None,
) -> ComparisonResponse:
    return ComparisonResponse(
        api_version=API_VERSION,
        schema_version=COMPARISON_SCHEMA_VERSION,
        review_id=review_id,
        stage="comparison",
        status="failed",
        lineage=ApiLineage(
            review_id=review_id,
            selected_card_id=selected_card_id,
            candidate_id=candidate_id,
        ),
        data=ComparisonData(next_allowed_actions=["test_another_hypothesis"]),
        warnings=[],
        safe_error=_safe_error(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
        evidence=ApiEvidence(source_artifacts=[], data_quality="unknown", confidence="unknown"),
    )


def _failed_verdict_envelope(
    *,
    review_id: str,
    comparison_id: str | None,
    candidate_id: str | None = None,
    selected_card_id: str | None = None,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
    details: list[str] | None = None,
) -> VerdictResponse:
    return VerdictResponse(
        api_version=API_VERSION,
        schema_version=VERDICT_SCHEMA_VERSION,
        review_id=review_id,
        stage="verdict",
        status="failed",
        lineage=ApiLineage(
            review_id=review_id,
            selected_card_id=selected_card_id,
            candidate_id=candidate_id,
            comparison_id=comparison_id,
        ),
        data=VerdictData(next_allowed_actions=["rerun_comparison"]),
        warnings=[],
        safe_error=_safe_error(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
        evidence=ApiEvidence(source_artifacts=[], data_quality="unknown", confidence="unknown"),
    )


def _failed_report_envelope(
    *,
    review_id: str,
    verdict_id: str | None,
    candidate_id: str | None = None,
    selected_card_id: str | None = None,
    comparison_id: str | None = None,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
    details: list[str] | None = None,
) -> ReportResponse:
    return ReportResponse(
        api_version=API_VERSION,
        schema_version=REPORT_SCHEMA_VERSION,
        review_id=review_id,
        stage="report",
        status="failed",
        lineage=ApiLineage(
            review_id=review_id,
            selected_card_id=selected_card_id,
            candidate_id=candidate_id,
            comparison_id=comparison_id,
            verdict_id=verdict_id,
        ),
        data=ReportData(),
        warnings=[],
        safe_error=_safe_error(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
        evidence=ApiEvidence(source_artifacts=[], data_quality="unknown", confidence="unknown"),
    )


def create_review_diagnosis(request: CreateReviewRequest) -> tuple[int, CreateReviewResponse]:
    """Create a diagnosis review and return an HTTP status plus public envelope."""

    payload = _request_to_bridge_payload(request)
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)
    payload_path = PAYLOAD_DIR / f"fastapi_payload_{uuid.uuid4().hex}.json"
    write_json(payload_path, payload)

    code, result_path = run_from_payload(
        payload_path,
        mode=MODE_DIAGNOSIS_PLUS_PROBLEM,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    try:
        review_result = json.loads(result_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return 500, _failed_create_envelope(
            review_id=None,
            code="backend_failed",
            message="Portfolio diagnosis finished but the review result could not be read.",
            user_action="retry",
            retryable=True,
            details=[str(exc)],
        )
    if not isinstance(review_result, dict):
        return 500, _failed_create_envelope(
            review_id=None,
            code="backend_failed",
            message="Portfolio diagnosis returned an invalid review result.",
            user_action="retry",
            retryable=True,
        )

    review_id = _text(review_result.get("review_id"))
    if code != 0 or review_result.get("status") != "completed":
        details_code = str(review_result.get("details") or "")
        error_code = "invalid_portfolio_input" if details_code == "input_validation_error" else "backend_failed"
        http_status = 400 if error_code == "invalid_portfolio_input" else 500
        return http_status, _failed_create_envelope(
            review_id=review_id,
            code=error_code,
            message=_text(review_result.get("error"), "Portfolio diagnosis failed.") or "Portfolio diagnosis failed.",
            user_action="fix_input" if error_code == "invalid_portfolio_input" else "retry",
            retryable=error_code != "invalid_portfolio_input",
            details=[details_code],
        )

    data = _created_data(review_result)
    return 200, CreateReviewResponse(
        api_version=API_VERSION,
        schema_version=CREATE_REVIEW_SCHEMA_VERSION,
        review_id=review_id,
        stage="diagnosis",
        status="ok",
        lineage=ApiLineage(review_id=review_id),
        data=data,
        warnings=_warnings_from_outputs(_record(review_result.get("outputs"))),
        safe_error=None,
        evidence=_evidence_from_data(data),
    )


def _builder_data(builder_doc: dict[str, Any]) -> BuilderData:
    prefill = _record(builder_doc.get("builder_prefill"))
    candidate_setup = _record(builder_doc.get("candidate_setup"))
    validation = _record(builder_doc.get("validation"))
    can_generate = bool(builder_doc.get("can_generate_candidate")) and bool(candidate_setup)
    readiness = "ready" if can_generate else "blocked"
    mode = _text(
        _record(candidate_setup.get("parameters")).get("mode"),
        _record(candidate_setup.get("constraints")).get("mode"),
        prefill.get("builder_mode"),
    )
    success_criteria = [
        str(item)
        for item in _list(candidate_setup.get("success_criteria") or prefill.get("success_criteria"))
        if str(item).strip()
    ]
    builder_setup = BuilderSetupSummary(
        builder_setup_id=_text(candidate_setup.get("candidate_setup_id"), prefill.get("builder_prefill_id")),
        selected_card_id=_text(builder_doc.get("selected_card_id"), candidate_setup.get("source_card_id")),
        method_id=_text(candidate_setup.get("selected_method"), prefill.get("suggested_method")),
        mode=mode,
        success_criteria=success_criteria,
        tradeoff_to_watch=_text(candidate_setup.get("tradeoff_to_watch"), prefill.get("tradeoff_to_watch")),
        decision_boundary=_text(candidate_setup.get("decision_boundary"), prefill.get("decision_boundary")),
        generation_readiness=readiness,  # type: ignore[arg-type]
    )
    next_allowed = ["generate_candidate"] if can_generate else ["select_another_card"]
    if validation.get("validation_status") == "blocked_by_data_quality":
        next_allowed = ["resolve_data_quality", "select_another_card"]
    return BuilderData(
        builder_setup=builder_setup,
        candidate_generation_allowed=can_generate,
        next_allowed_actions=next_allowed,  # type: ignore[arg-type]
    )


def prepare_builder_setup(review_id: str, request: BuilderRequest) -> tuple[int, BuilderResponse]:
    """Prepare Block 6 Builder setup through FastAPI without generating a candidate."""

    try:
        result = prepare_selected_builder_setup(
            review_id=review_id,
            selected_card_id=request.selected_card_id,
            method=request.overrides.method_id,
            mode=request.overrides.mode,
            min_asset_weight=request.overrides.min_asset_weight,
            max_asset_weight=request.overrides.max_asset_weight,
        )
    except BuilderSelectionError as exc:
        status_code, code, user_action, retryable = _error_code_for_stage_exception(exc, stage="builder")
        return status_code, _failed_builder_envelope(
            review_id=review_id,
            selected_card_id=request.selected_card_id,
            code=code,
            message=str(exc),
            user_action=user_action,
            retryable=retryable,
        )
    except Exception as exc:
        return 500, _failed_builder_envelope(
            review_id=review_id,
            selected_card_id=request.selected_card_id,
            code="backend_failed",
            message="Builder setup prepare failed.",
            user_action="retry",
            retryable=True,
            details=[str(exc)],
        )

    builder_doc = _record(result.get("portfolio_alternatives_builder"))
    data = _builder_data(builder_doc)
    selected_card_id = data.builder_setup.selected_card_id or request.selected_card_id
    refs = [
        _stage_artifact_ref(
            "portfolio_alternatives_builder",
            _text(result.get("path")) or f"runs/{review_id}/analysis_subject/portfolio_alternatives_builder.json",
            scope="analysis_subject",
        )
    ]
    warnings = [
        str(item)
        for item in _list(builder_doc.get("warnings"))
        + _list(_record(builder_doc.get("validation")).get("validation_warnings"))
        if str(item).strip()
    ]
    return 200, BuilderResponse(
        api_version=API_VERSION,
        schema_version=BUILDER_SCHEMA_VERSION,
        review_id=review_id,
        stage="builder",
        status="ok" if data.candidate_generation_allowed else "blocked",
        lineage=ApiLineage(
            review_id=review_id,
            selected_card_id=selected_card_id,
            builder_setup_id=data.builder_setup.builder_setup_id,
        ),
        data=data,
        warnings=warnings,
        safe_error=None,
        evidence=ApiEvidence(source_artifacts=refs, data_quality="ok", confidence="medium"),
    )


def _builder_doc_for_setup(review_id: str, builder_setup_id: str) -> tuple[dict[str, Any], str]:
    run_dir = safe_review_run_dir(review_id)
    builder_path = run_dir / "analysis_subject" / "portfolio_alternatives_builder.json"
    if not builder_path.is_file():
        raise CandidateBridgeError("portfolio_alternatives_builder.json was not found for this review.")
    builder_doc = _read_json_file(builder_path)
    candidate_setup = _record(builder_doc.get("candidate_setup"))
    actual_setup_id = _text(candidate_setup.get("candidate_setup_id"))
    if not actual_setup_id:
        raise CandidateBridgeError("portfolio_alternatives_builder.json does not contain a valid CandidateSetup.")
    if actual_setup_id != builder_setup_id:
        raise CandidateBridgeError(
            "Requested builder_setup_id does not match the active run-local Builder setup."
        )
    selected_card_id = _text(candidate_setup.get("source_card_id"), builder_doc.get("selected_card_id"))
    if not selected_card_id:
        raise CandidateBridgeError("Active Builder setup does not contain a selected Launchpad card id.")
    return builder_doc, selected_card_id


def _candidate_generation_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"generated", "available"}:
        return "generated"
    if normalized == "failed":
        return "failed"
    if normalized in {"infeasible", "attempt_created", "blocked"}:
        return "blocked"
    return "unknown"


def _candidate_data(candidate_generation: dict[str, Any]) -> CandidateData:
    candidate = _record(candidate_generation.get("candidate"))
    handoff = _record(candidate_generation.get("handoff_to_comparison"))
    status = _candidate_generation_status(candidate_generation.get("generation_status"))
    can_compare = bool(handoff.get("can_compare")) and status == "generated"
    next_allowed = ["run_comparison"] if can_compare else ["select_another_card"]
    failure_reason = _text(
        candidate.get("infeasibility_reason"),
        candidate.get("failure_reason"),
        handoff.get("blocked_reason"),
        handoff.get("reason"),
    )
    return CandidateData(
        candidate=CandidateSummary(
            candidate_id=_text(candidate.get("candidate_id")),
            method_label=_text(candidate.get("candidate_name"), candidate.get("method")),
            generation_status=status,  # type: ignore[arg-type]
            weight_summary=_number_map(candidate.get("weights")),
            infeasible_reason=None if status == "generated" else failure_reason,
        ),
        hypothesis=HypothesisSummary(
            diagnosis_id=_text(candidate.get("source_diagnosis_id")),
            hypothesis=_text(candidate.get("hypothesis_to_test")),
            success_criteria=[
                str(item) for item in _list(candidate.get("success_criteria")) if str(item).strip()
            ],
            tradeoff_to_watch=_text(candidate.get("tradeoff_to_watch")),
            decision_boundary=_text(candidate.get("decision_boundary")),
        ),
        is_rebalance_recommendation=False,
        next_allowed_actions=next_allowed,  # type: ignore[arg-type]
    )


def generate_candidate_from_builder(
    review_id: str, request: BuilderSetupIdRequest
) -> tuple[int, CandidateResponse]:
    """Generate one Block 7 diagnostic candidate through FastAPI."""

    selected_card_id: str | None = None
    try:
        _builder_doc, selected_card_id = _builder_doc_for_setup(review_id, request.builder_setup_id)
        result = generate_selected_candidate(
            review_id=review_id,
            selected_card_id=selected_card_id,
            force=False,
            factory_execution_mode="fast",
        )
    except (BuilderSelectionError, CandidateBridgeError, ValueError, FileNotFoundError) as exc:
        status_code, code, user_action, retryable = _error_code_for_stage_exception(exc, stage="candidate")
        return status_code, _failed_candidate_envelope(
            review_id=review_id,
            builder_setup_id=request.builder_setup_id,
            selected_card_id=selected_card_id,
            code=code,
            message=str(exc),
            user_action=user_action,
            retryable=retryable,
        )
    except Exception as exc:
        return 500, _failed_candidate_envelope(
            review_id=review_id,
            builder_setup_id=request.builder_setup_id,
            selected_card_id=selected_card_id,
            code="backend_failed",
            message="Candidate generation failed.",
            user_action="retry",
            retryable=True,
            details=[str(exc)],
        )

    candidate_generation = _record(result.get("candidate_generation"))
    data = _candidate_data(candidate_generation)
    can_compare = bool(result.get("can_compare")) and data.candidate.generation_status == "generated"
    refs = [
        _stage_artifact_ref(
            "portfolio_alternatives_builder",
            f"runs/{review_id}/analysis_subject/portfolio_alternatives_builder.json",
            scope="analysis_subject",
        ),
        _stage_artifact_ref(
            "candidate_generation",
            _text(result.get("path")) or f"runs/{review_id}/candidate_generation.json",
            scope="run_local",
        ),
        _stage_artifact_ref(
            "candidate_factory_run",
            f"runs/{review_id}/candidate_factory_run.json",
            scope="run_local",
        ),
    ]
    status_value = "ok" if can_compare else "blocked"
    safe_error = None
    if not can_compare:
        safe_error = _safe_error(
            code="candidate_generation_blocked",
            message=data.candidate.infeasible_reason or "Candidate generation did not produce compare-ready weights.",
            user_action="return_to_hypothesis",
            retryable=False,
        )
    return 200, CandidateResponse(
        api_version=API_VERSION,
        schema_version=CANDIDATE_SCHEMA_VERSION,
        review_id=review_id,
        stage="candidate",
        status=status_value,  # type: ignore[arg-type]
        lineage=ApiLineage(
            review_id=review_id,
            selected_card_id=selected_card_id,
            builder_setup_id=request.builder_setup_id,
            candidate_id=data.candidate.candidate_id,
        ),
        data=data,
        warnings=[
            str(item)
            for item in _list(candidate_generation.get("warnings"))
            if str(item).strip()
        ],
        safe_error=safe_error,
        evidence=ApiEvidence(
            source_artifacts=refs,
            data_quality="ok" if can_compare else "partial",
            confidence="medium",
        ),
    )


def _read_run_local_json(review_id: str, artifact_name: str) -> dict[str, Any]:
    run_dir = safe_review_run_dir(review_id)
    path = run_dir / artifact_name
    if not path.is_file():
        raise FileNotFoundError(f"{artifact_name} was not found for this review.")
    return _read_json_file(path)


def _read_run_local_json_or_empty(review_id: str, artifact_name: str) -> dict[str, Any]:
    try:
        return _read_run_local_json(review_id, artifact_name)
    except (FileNotFoundError, ValueError):
        return {}


def _candidate_lineage(review_id: str, candidate_id: str) -> tuple[str, str]:
    candidate_generation = _read_run_local_json(review_id, "candidate_generation.json")
    candidate = _record(candidate_generation.get("candidate"))
    actual_candidate_id = _text(candidate.get("candidate_id"))
    if not actual_candidate_id:
        raise CandidateBridgeError("candidate_generation.candidate.candidate_id is required.")
    if actual_candidate_id != candidate_id:
        raise CandidateBridgeError("Requested candidate_id does not match the active run-local candidate.")
    selected_card_id = _text(candidate.get("source_card_id"), candidate_generation.get("selected_card_id"))
    if not selected_card_id:
        raise CandidateBridgeError("Active candidate does not contain a selected Launchpad card id.")
    return selected_card_id, actual_candidate_id


def _comparison_id_for_candidate(candidate_id: str | None) -> str | None:
    return f"current_vs_candidate:{candidate_id}" if candidate_id else None


def _active_comparison_lineage(review_id: str, comparison_id: str) -> tuple[str, str, str]:
    current_vs_candidate = _read_run_local_json(review_id, "current_vs_candidate.json")
    selected_ids = [
        str(item).strip()
        for item in _list(current_vs_candidate.get("selected_candidate_ids"))
        if str(item).strip()
    ]
    rows = [_record(item) for item in _list(current_vs_candidate.get("comparisons"))]
    row_ids = [
        str(row.get("candidate_id") or "").strip()
        for row in rows
        if str(row.get("candidate_id") or "").strip()
    ]
    candidate_id = (selected_ids or row_ids or [""])[0]
    if not candidate_id:
        raise ComparisonBridgeError("current_vs_candidate.json does not contain an active selected candidate.")
    valid_comparison_ids = {
        candidate_id,
        _comparison_id_for_candidate(candidate_id),
        f"comparison:{candidate_id}",
        f"comparison_{candidate_id}",
    }
    if comparison_id not in valid_comparison_ids:
        raise ComparisonBridgeError("Requested comparison_id does not match the active run-local comparison.")
    selected_card_id, actual_candidate_id = _candidate_lineage(review_id, candidate_id)
    return selected_card_id, actual_candidate_id, _comparison_id_for_candidate(actual_candidate_id) or comparison_id


def _active_verdict_lineage(review_id: str, verdict_id: str) -> tuple[str, str, str, str]:
    verdict = _read_run_local_json(review_id, "decision_verdict.json")
    actual_verdict_id = _text(verdict.get("verdict_id"))
    if not actual_verdict_id:
        raise VerdictBridgeError("decision_verdict.json does not contain a verdict_id.")
    if actual_verdict_id != verdict_id:
        raise VerdictBridgeError("Requested verdict_id does not match the active run-local Decision Verdict.")
    candidate_id = _text(verdict.get("reviewed_candidate_id"), verdict.get("selected_candidate_id"))
    if not candidate_id:
        raise VerdictBridgeError("decision_verdict.json does not contain a reviewed candidate id.")
    selected_card_id, actual_candidate_id = _candidate_lineage(review_id, candidate_id)
    comparison_id = _comparison_id_for_candidate(actual_candidate_id) or actual_candidate_id
    return selected_card_id, actual_candidate_id, comparison_id, actual_verdict_id


def _as_text_list(items: Any, *, fallback_field: str = "label") -> list[str]:
    result: list[str] = []
    for item in _list(items):
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        elif isinstance(item, dict):
            text = _text(
                item.get(fallback_field),
                item.get("summary"),
                item.get("field"),
                item.get("criterion"),
                item.get("reason"),
            )
            if text:
                result.append(text)
    return result


def _dedupe_text(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _first_comparison_row(current_vs_candidate: dict[str, Any], candidate_id: str | None) -> dict[str, Any]:
    rows = [_record(item) for item in _list(current_vs_candidate.get("comparisons"))]
    if candidate_id:
        for row in rows:
            if _text(row.get("candidate_id")) == candidate_id:
                return row
    return rows[0] if rows else {}


def _candidate_evidence_chain_context(
    candidate_generation: dict[str, Any],
    *,
    comparison_row: dict[str, Any] | None = None,
    verdict: dict[str, Any] | None = None,
    ai_context: dict[str, Any] | None = None,
) -> DownstreamEvidenceChainContext:
    """Build a bounded display context linking downstream stages to diagnosis evidence."""

    candidate = _record(candidate_generation.get("candidate"))
    row = _record(comparison_row)
    verdict_row = _record(verdict)
    ai_row = _record(ai_context)
    source_artifacts = _dedupe_text(
        _string_list(candidate_generation.get("source_artifacts"))
        + _string_list(row.get("source_artifacts"))
        + list(_record(ai_row.get("source_artifacts")).keys())
    )
    if not source_artifacts:
        source_artifacts = [
            "problem_classification.json",
            "candidate_generation.json",
            "current_vs_candidate.json",
        ]
        if verdict_row:
            source_artifacts.append("decision_verdict.json")
        if ai_row:
            source_artifacts.append("ai_commentary_context.json")

    return DownstreamEvidenceChainContext(
        selected_diagnosis_id=_text(
            candidate.get("source_diagnosis_id"),
            row.get("source_diagnosis_id"),
            row.get("diagnosis_id"),
            verdict_row.get("source_diagnosis_id"),
        ),
        selected_diagnosis_label=_text(
            candidate.get("source_diagnosis_label"),
            row.get("source_diagnosis_label"),
            row.get("diagnosis_label"),
        ),
        selected_diagnosis_role=_text(
            candidate.get("source_diagnosis_role"),
            row.get("source_diagnosis_role"),
        ),
        diagnosis_statement=_text(
            candidate.get("source_diagnosis_statement"),
            row.get("diagnosis_statement"),
            verdict_row.get("diagnosis_statement"),
        ),
        tested_hypothesis=_text(
            candidate.get("hypothesis_to_test"),
            row.get("hypothesis_to_test"),
            verdict_row.get("hypothesis_tested"),
        ),
        success_criteria=_dedupe_text(
            _string_list(candidate.get("success_criteria"))
            + _as_text_list(row.get("success_criteria"), fallback_field="criterion")
            + _as_text_list(row.get("success_criteria_result"), fallback_field="criterion")
        )[:8],
        tradeoff_to_watch=_text(candidate.get("tradeoff_to_watch"), row.get("tradeoff_to_watch")),
        candidate_boundary=_text(
            candidate.get("decision_boundary"),
            candidate.get("candidate_boundary"),
            row.get("candidate_boundary"),
        ),
        recommendation_boundary=_text(
            candidate.get("decision_boundary"),
            verdict_row.get("recommendation_boundary"),
            verdict_row.get("decision_boundary"),
        )
        or "Decision Verdict is non-binding decision support and does not execute trades.",
        source_artifacts=source_artifacts[:10],
    )


def _success_result(value: Any) -> str:
    status = str(_record(value).get("overall_status") or value or "").strip().lower()
    if status == "met":
        return "passed"
    if status in {"partially_met", "mixed", "similar"}:
        return "partial"
    if status == "not_met":
        return "failed"
    if status in {"unavailable", "not_evaluated", "not_provided"}:
        return "unavailable"
    return "unknown"


def _materiality(value: Any) -> str:
    status = str(_record(value).get("status") or "").strip().lower()
    if status == "review_candidate":
        return "material"
    if status == "not_material":
        return "immaterial"
    return "unknown"


def _comparison_data(
    current_vs_candidate: dict[str, Any],
    candidate_id: str | None,
    candidate_generation: dict[str, Any] | None = None,
    client_fit_check: dict[str, Any] | None = None,
) -> ComparisonData:
    row = _first_comparison_row(current_vs_candidate, candidate_id)
    comparison_id = _comparison_id_for_candidate(_text(row.get("candidate_id"), candidate_id))
    has_row = bool(row)
    evidence_chain_context = _candidate_evidence_chain_context(
        _record(candidate_generation),
        comparison_row=row,
    )
    return ComparisonData(
        comparison=ComparisonSummary(
            comparison_id=comparison_id,
            current_label=_text(_record(current_vs_candidate.get("baseline")).get("display_name")) or "Current portfolio",
            candidate_label=_text(row.get("display_name"), row.get("candidate_label"), row.get("candidate_id")),
            success_criteria_result=_success_result(row.get("success_criteria_result")),  # type: ignore[arg-type]
            what_improved=_as_text_list(row.get("what_improved")),
            what_worsened=_as_text_list(row.get("what_worsened")),
            what_stayed_similar=_as_text_list(row.get("what_stayed_similar")),
            unavailable_metrics=_as_text_list(row.get("unavailable_metrics"), fallback_field="field"),
            materiality=_materiality(row.get("materiality_for_decision_review")),  # type: ignore[arg-type]
        ),
        evidence_chain_context=evidence_chain_context,
        client_fit=_client_fit_display_summary(client_fit_check),
        next_allowed_actions=["generate_verdict"] if has_row else ["test_another_hypothesis"],  # type: ignore[list-item]
    )


def run_current_vs_candidate(
    review_id: str, request: CandidateIdRequest
) -> tuple[int, ComparisonResponse]:
    """Run Block 8 current-vs-candidate comparison through FastAPI."""

    selected_card_id: str | None = None
    try:
        selected_card_id, _candidate_id = _candidate_lineage(review_id, request.candidate_id)
        result = compare_selected_candidate(
            review_id=review_id,
            selected_card_id=selected_card_id,
        )
    except (CandidateBridgeError, ComparisonBridgeError, FileNotFoundError, ValueError) as exc:
        status_code, code, user_action, retryable = _error_code_for_stage_exception(exc, stage="comparison")
        if code == "backend_failed":
            code = "comparison_unavailable"
            user_action = "return_to_hypothesis"
            retryable = False
        return status_code, _failed_comparison_envelope(
            review_id=review_id,
            candidate_id=request.candidate_id,
            selected_card_id=selected_card_id,
            code=code,
            message=str(exc),
            user_action=user_action,
            retryable=retryable,
        )
    except Exception as exc:
        return 500, _failed_comparison_envelope(
            review_id=review_id,
            candidate_id=request.candidate_id,
            selected_card_id=selected_card_id,
            code="backend_failed",
            message="Current-vs-candidate comparison failed.",
            user_action="retry",
            retryable=True,
            details=[str(exc)],
        )

    current_vs_candidate = _record(result.get("current_vs_candidate"))
    candidate_generation = _read_run_local_json_or_empty(review_id, "candidate_generation.json")
    client_fit_check = _read_run_local_json_or_empty(review_id, "analysis_subject/client_fit_check.json")
    data = _comparison_data(
        current_vs_candidate,
        _text(result.get("candidate_id"), request.candidate_id),
        candidate_generation,
        client_fit_check,
    )
    candidate_id = _text(result.get("candidate_id"), request.candidate_id)
    comparison_id = data.comparison.comparison_id
    refs = [
        _stage_artifact_ref(
            "candidate_generation",
            f"runs/{review_id}/candidate_generation.json",
            scope="run_local",
        ),
        _stage_artifact_ref(
            "candidate_comparison",
            _safe_ref(_record(result.get("paths")).get("candidate_comparison"), fallback=f"runs/{review_id}/candidate_comparison.json"),
            scope="run_local",
        ),
        _stage_artifact_ref(
            "current_vs_candidate",
            _safe_ref(_record(result.get("paths")).get("current_vs_candidate"), fallback=f"runs/{review_id}/current_vs_candidate.json"),
            scope="run_local",
        ),
        _stage_artifact_ref(
            "site_explanation_bundle",
            _safe_ref(_record(result.get("paths")).get("site_explanation_bundle"), fallback=f"runs/{review_id}/site_explanation_bundle.json"),
            scope="run_local",
        ),
    ]
    warnings = [str(item) for item in _list(current_vs_candidate.get("warnings")) if str(item).strip()]
    return 200, ComparisonResponse(
        api_version=API_VERSION,
        schema_version=COMPARISON_SCHEMA_VERSION,
        review_id=review_id,
        stage="comparison",
        status="ok" if data.comparison.candidate_label else "partial",
        lineage=ApiLineage(
            review_id=review_id,
            selected_card_id=selected_card_id,
            candidate_id=candidate_id,
            comparison_id=comparison_id,
        ),
        data=data,
        warnings=warnings,
        safe_error=None,
        evidence=ApiEvidence(source_artifacts=refs, data_quality="ok", confidence="medium"),
    )


def _verdict_label(value: Any, reason_id: str | None = None) -> str:
    verdict_id = str(value or "").strip()
    if verdict_id == "rebalance_to_selected_candidate":
        return "rebalance_review"
    if verdict_id == "no_material_rebalance_recommended":
        return "no_material_rebalance"
    if verdict_id == "test_another_candidate_or_review_evidence":
        return "test_another_candidate"
    if verdict_id == "evidence_insufficient":
        if reason_id in {"candidate_generation_failed", "candidate_generation_infeasible"}:
            return "candidate_failed_or_infeasible"
        return "evidence_insufficient"
    if verdict_id == "risk_reduction_required":
        return "rebalance_review"
    return "unknown"


def _verdict_data(
    verdict: dict[str, Any],
    candidate_generation: dict[str, Any] | None = None,
    current_vs_candidate: dict[str, Any] | None = None,
    candidate_id: str | None = None,
    client_fit_check: dict[str, Any] | None = None,
) -> VerdictData:
    verdict_id = _text(verdict.get("verdict_id"))
    comparison_row = _first_comparison_row(_record(current_vs_candidate), candidate_id)
    evidence_summary = _record(verdict.get("evidence_summary"))
    limitations = [
        str(item)
        for item in _list(verdict.get("confidence_limitations"))
        if str(item).strip()
    ]
    rationale = [
        item
        for item in [
            _text(verdict.get("rationale_summary")),
            _text(verdict.get("recommended_action")),
            _text(_record(verdict.get("no_trade")).get("reason")),
        ]
        if item
    ]
    evidence_used = _dedupe_text(
        _as_text_list(evidence_summary.get("improvements"))
        + _as_text_list(evidence_summary.get("deteriorations"))
        + _as_text_list(comparison_row.get("what_improved"))
        + _as_text_list(comparison_row.get("what_worsened"))
        + _as_text_list(comparison_row.get("unavailable_metrics"), fallback_field="field")
    )[:10]
    what_would_change = _dedupe_text(
        _as_text_list(verdict.get("what_would_change_verdict"))
        + _as_text_list(verdict.get("next_review_triggers"))
        + _as_text_list(_record(verdict.get("no_trade")).get("what_would_change"))
    )[:8]
    evidence_chain_context = _candidate_evidence_chain_context(
        _record(candidate_generation),
        comparison_row=comparison_row,
        verdict=verdict,
    )
    client_fit_context = _record(evidence_summary.get("client_fit_decision_context"))
    next_allowed: list[str] = ["generate_report"]
    if verdict_id in {"test_another_candidate_or_review_evidence", "evidence_insufficient"}:
        next_allowed.append("test_another_hypothesis")
    return VerdictData(
        verdict=VerdictSummary(
            verdict_id=verdict_id,
            verdict=_verdict_label(verdict_id, _text(verdict.get("verdict_reason_id"))),  # type: ignore[arg-type]
            rationale=rationale,
            evidence_used=evidence_used,
            what_would_change_verdict=what_would_change,
            confidence=_confidence(verdict.get("confidence")),
            limitations=limitations,
            decision_support_only=True,
        ),
        evidence_chain_context=evidence_chain_context,
        client_fit=_client_fit_display_summary(client_fit_check, decision_context=client_fit_context),
        next_allowed_actions=next_allowed,  # type: ignore[arg-type]
    )


def generate_decision_verdict(
    review_id: str, request: ComparisonIdRequest
) -> tuple[int, VerdictResponse]:
    """Run Block 9 non-binding Decision Verdict through FastAPI."""

    selected_card_id: str | None = None
    candidate_id: str | None = None
    comparison_id = request.comparison_id
    try:
        selected_card_id, candidate_id, comparison_id = _active_comparison_lineage(
            review_id,
            request.comparison_id,
        )
        result = write_selected_candidate_verdict(
            review_id=review_id,
            selected_card_id=selected_card_id,
        )
    except (CandidateBridgeError, ComparisonBridgeError, VerdictBridgeError, FileNotFoundError, ValueError) as exc:
        status_code, code, user_action, retryable = _error_code_for_stage_exception(exc, stage="verdict")
        if code == "backend_failed":
            code = "verdict_unavailable"
            user_action = "rerun_comparison"
            retryable = False
        return status_code, _failed_verdict_envelope(
            review_id=review_id,
            comparison_id=comparison_id,
            candidate_id=candidate_id,
            selected_card_id=selected_card_id,
            code=code,
            message=str(exc),
            user_action=user_action,
            retryable=retryable,
        )
    except Exception as exc:
        return 500, _failed_verdict_envelope(
            review_id=review_id,
            comparison_id=comparison_id,
            candidate_id=candidate_id,
            selected_card_id=selected_card_id,
            code="backend_failed",
            message="Decision Verdict generation failed.",
            user_action="retry",
            retryable=True,
            details=[str(exc)],
        )

    verdict = _record(result.get("decision_verdict"))
    candidate_generation = _read_run_local_json_or_empty(review_id, "candidate_generation.json")
    current_vs_candidate = _read_run_local_json_or_empty(review_id, "current_vs_candidate.json")
    client_fit_check = _read_run_local_json_or_empty(review_id, "analysis_subject/client_fit_check.json")
    data = _verdict_data(verdict, candidate_generation, current_vs_candidate, candidate_id, client_fit_check)
    verdict_id = data.verdict.verdict_id
    refs = [
        _stage_artifact_ref("candidate_generation", f"runs/{review_id}/candidate_generation.json"),
        _stage_artifact_ref("current_vs_candidate", f"runs/{review_id}/current_vs_candidate.json"),
        _stage_artifact_ref(
            "decision_verdict",
            _text(result.get("path")) or f"runs/{review_id}/decision_verdict.json",
        ),
        _stage_artifact_ref(
            "site_explanation_bundle",
            _text(result.get("site_explanation_bundle_path")) or f"runs/{review_id}/site_explanation_bundle.json",
        ),
    ]
    warnings = [str(item) for item in _list(verdict.get("warnings")) if str(item).strip()]
    return 200, VerdictResponse(
        api_version=API_VERSION,
        schema_version=VERDICT_SCHEMA_VERSION,
        review_id=review_id,
        stage="verdict",
        status="ok",
        lineage=ApiLineage(
            review_id=review_id,
            selected_card_id=selected_card_id,
            candidate_id=_text(result.get("candidate_id"), candidate_id),
            comparison_id=comparison_id,
            verdict_id=verdict_id,
        ),
        data=data,
        warnings=warnings,
        safe_error=None,
        evidence=ApiEvidence(source_artifacts=refs, data_quality="ok", confidence=data.verdict.confidence),
    )


def _artifact_kind(ref: Any) -> str:
    artifact = _text(_record(ref).get("artifact"), ref) or "source_artifact"
    return artifact.removesuffix(".json")


def _report_data(
    ai_context: dict[str, Any],
    candidate_generation: dict[str, Any] | None = None,
    current_vs_candidate: dict[str, Any] | None = None,
    verdict: dict[str, Any] | None = None,
    candidate_id: str | None = None,
    client_fit_check: dict[str, Any] | None = None,
) -> ReportData:
    draft = _record(ai_context.get("client_explanation_draft"))
    sentences = [_record(item) for item in _list(draft.get("sentences"))]
    by_topic: dict[str, list[str]] = {}
    for row in sentences:
        topic = _text(row.get("topic")) or "summary"
        text = _text(row.get("text"))
        if text:
            by_topic.setdefault(topic, []).append(text)

    all_text = [text for rows in by_topic.values() for text in rows]
    journal = _record(ai_context.get("light_decision_journal"))
    source_refs = [
        ArtifactRef(
            kind=_artifact_kind(ref),
            ref=_text(_record(ref).get("artifact")) or "logical://source_artifact",
            scope="logical",
        )
        for ref in _list(ai_context.get("evidence_references"))[:20]
    ]
    source_map = _record(ai_context.get("source_artifacts"))
    unavailable_sections = [
        str(key)
        for key, value in source_map.items()
        if value is None
    ]
    warnings = [str(item) for item in _list(ai_context.get("warnings")) if str(item).strip()]
    limitations = warnings + [
        str(item)
        for item in _list(journal.get("key_assumptions_and_limits"))
        if str(item).strip()
    ]
    comparison_row = _first_comparison_row(_record(current_vs_candidate), candidate_id)
    evidence_chain_context = _candidate_evidence_chain_context(
        _record(candidate_generation),
        comparison_row=comparison_row,
        verdict=_record(verdict),
        ai_context=ai_context,
    )
    client_fit_context = _record(_record(_record(verdict).get("evidence_summary")).get("client_fit_decision_context"))
    return ReportData(
        report_preview=ReportPreview(
            executive_summary=all_text[0] if all_text else None,
            current_portfolio_diagnosis=_text(
                *(by_topic.get("diagnosis") or []),
                *(by_topic.get("key_problems") or []),
            ),
            stress_evidence=(by_topic.get("stress_evidence") or by_topic.get("stress_scorecard") or [])[:5],
            tested_hypothesis=_text(
                *(by_topic.get("hypothesis_tested") or []),
                *(by_topic.get("candidate_generated") or []),
            ),
            candidate_boundary=_text(
                *(by_topic.get("candidate_generated") or []),
                *(by_topic.get("builder_status") or []),
            ),
            comparison_tradeoffs=(
                by_topic.get("current_vs_candidate_comparison")
                or by_topic.get("improvements")
                or by_topic.get("deteriorations")
                or []
            )[:5],
            verdict_explanation=_text(
                *(by_topic.get("decision_verdict") or []),
                *(by_topic.get("no_trade_rationale") or []),
                journal.get("decision_verdict"),
            ),
            evidence_limitations=limitations[:8],
            monitoring_note=_text(journal.get("next_review_trigger")),
        ),
        grounding=ReportGrounding(
            source_refs=source_refs,
            unavailable_sections=unavailable_sections,
        ),
        evidence_chain_context=evidence_chain_context,
        client_fit=_client_fit_display_summary(client_fit_check, decision_context=client_fit_context),
        llm_generated=False,
    )


def generate_report_grounding(
    review_id: str, request: VerdictIdRequest
) -> tuple[int, ReportResponse]:
    """Run grounded report/AI Commentary context through FastAPI."""

    selected_card_id: str | None = None
    candidate_id: str | None = None
    comparison_id: str | None = None
    verdict_id = request.verdict_id
    try:
        selected_card_id, candidate_id, comparison_id, verdict_id = _active_verdict_lineage(
            review_id,
            request.verdict_id,
        )
        result = write_selected_report_context(
            review_id=review_id,
            selected_card_id=selected_card_id,
        )
    except (CandidateBridgeError, ComparisonBridgeError, VerdictBridgeError, ReportBridgeError, FileNotFoundError, ValueError) as exc:
        status_code, code, user_action, retryable = _error_code_for_stage_exception(exc, stage="report")
        if code == "backend_failed":
            code = "report_unavailable"
            user_action = "rerun_verdict"
            retryable = False
        return status_code, _failed_report_envelope(
            review_id=review_id,
            verdict_id=verdict_id,
            candidate_id=candidate_id,
            selected_card_id=selected_card_id,
            comparison_id=comparison_id,
            code=code,
            message=str(exc),
            user_action=user_action,
            retryable=retryable,
        )
    except Exception as exc:
        return 500, _failed_report_envelope(
            review_id=review_id,
            verdict_id=verdict_id,
            candidate_id=candidate_id,
            selected_card_id=selected_card_id,
            comparison_id=comparison_id,
            code="backend_failed",
            message="Grounded report context generation failed.",
            user_action="retry",
            retryable=True,
            details=[str(exc)],
        )

    ai_context = _record(result.get("ai_commentary_context"))
    candidate_generation = _read_run_local_json_or_empty(review_id, "candidate_generation.json")
    current_vs_candidate = _read_run_local_json_or_empty(review_id, "current_vs_candidate.json")
    verdict = _read_run_local_json_or_empty(review_id, "decision_verdict.json")
    client_fit_check = _read_run_local_json_or_empty(review_id, "analysis_subject/client_fit_check.json")
    data = _report_data(ai_context, candidate_generation, current_vs_candidate, verdict, candidate_id, client_fit_check)
    refs = [
        _stage_artifact_ref("candidate_generation", f"runs/{review_id}/candidate_generation.json"),
        _stage_artifact_ref("current_vs_candidate", f"runs/{review_id}/current_vs_candidate.json"),
        _stage_artifact_ref("decision_verdict", f"runs/{review_id}/decision_verdict.json"),
        _stage_artifact_ref(
            "ai_commentary_context",
            _text(result.get("path")) or f"runs/{review_id}/ai_commentary_context.json",
        ),
        _stage_artifact_ref(
            "site_explanation_bundle",
            _text(result.get("site_explanation_bundle_path")) or f"runs/{review_id}/site_explanation_bundle.json",
        ),
    ]
    warnings = [str(item) for item in _list(ai_context.get("warnings")) if str(item).strip()]
    return 200, ReportResponse(
        api_version=API_VERSION,
        schema_version=REPORT_SCHEMA_VERSION,
        review_id=review_id,
        stage="report",
        status="ok",
        lineage=ApiLineage(
            review_id=review_id,
            selected_card_id=selected_card_id,
            candidate_id=_text(result.get("candidate_id"), candidate_id),
            comparison_id=comparison_id,
            verdict_id=verdict_id,
        ),
        data=data,
        warnings=warnings,
        safe_error=None,
        evidence=ApiEvidence(source_artifacts=refs, data_quality="ok", confidence="medium"),
    )


def _read_recoverable_review(review_id: str) -> dict[str, Any]:
    run_dir = safe_review_run_dir(review_id)
    result_path = run_dir / "review_result.json"
    try:
        review_result = json.loads(result_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError("No recoverable run-local review_result.json was found.") from exc
    if not isinstance(review_result, dict):
        raise ValueError("Run-local review_result.json is not a JSON object.")
    if review_result.get("review_id") != review_id or review_result.get("status") != "completed":
        raise ValueError("Run-local review_result.json is not a completed matching review.")
    return review_result


def recover_review_diagnosis(review_id: str) -> tuple[int, ReviewRecoveryResponse]:
    """Recover diagnosis, evidence, and hypothesis setup state for a run-local review."""

    try:
        review_result = _read_recoverable_review(review_id)
    except FileNotFoundError as exc:
        return 404, _failed_recovery_envelope(
            review_id=review_id,
            code="review_not_found",
            message=str(exc),
            user_action="none",
            retryable=False,
        )
    except (PayloadValidationError, ValueError) as exc:
        return 409, _failed_recovery_envelope(
            review_id=review_id,
            code="review_not_found",
            message=str(exc),
            user_action="none",
            retryable=False,
        )

    created = _created_data(review_result)
    data = ReviewRecoveryData(
        **created.model_dump(),
        downstream_artifacts_restored_as_active=False,
        restored_active_stages=["diagnosis", "evidence", "hypothesis_setup"],
    )
    return 200, ReviewRecoveryResponse(
        api_version=API_VERSION,
        schema_version=RECOVERY_SCHEMA_VERSION,
        review_id=review_id,
        stage="recovery",
        status="ok",
        lineage=ApiLineage(review_id=review_id),
        data=data,
        warnings=[
            "Candidate, comparison, verdict, and report artifacts are not restored as active state during recovery."
        ]
        + _warnings_from_outputs(_record(review_result.get("outputs"))),
        safe_error=None,
        evidence=_evidence_from_data(data),
    )


def _failed_recovery_envelope(
    *,
    review_id: str,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
) -> ReviewRecoveryResponse:
    return ReviewRecoveryResponse(
        api_version=API_VERSION,
        schema_version=RECOVERY_SCHEMA_VERSION,
        review_id=review_id,
        stage="recovery",
        status="failed",
        lineage=ApiLineage(review_id=review_id),
        data=ReviewRecoveryData(
            next_allowed_actions=[],
            downstream_artifacts_restored_as_active=False,
            restored_active_stages=[],
        ),
        warnings=[],
        safe_error=_safe_error(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
        ),
        evidence=ApiEvidence(source_artifacts=[], data_quality="unknown", confidence="unknown"),
    )
