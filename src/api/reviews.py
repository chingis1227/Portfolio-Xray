"""Runtime adapters for FastAPI portfolio-review stages.

This module bridges the typed FastAPI contract to the existing deterministic
portfolio-first review runner and one-candidate vertical-loop helpers. It
deliberately reuses current analytics and artifact writers instead of changing
portfolio formulas, generated artifact schemas, root ``config.yml``, or
frontend routing behavior.
"""

from __future__ import annotations

import gc
import json
import logging
import os
import re
import threading
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
    SITE_EXPLANATION_BUNDLE_FILENAME,
    VerdictBridgeError,
    build_success_result,
    compare_selected_candidate,
    create_run_dir,
    expected_output_paths,
    generate_selected_candidate,
    normalize_payload,
    prepare_selected_builder_setup,
    read_outputs,
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
    StagedProviderStatus,
    StagedReviewMode,
    StagedReviewStartedResponse,
    StagedReviewStatusResponse,
    StagedSafeError,
    StagedStageName,
    VerdictData,
    VerdictIdRequest,
    VerdictResponse,
    VerdictSummary,
)
from src.api.staged_review_state import (
    ReviewAccessError,
    StagedReviewStateStore,
    read_json_file,
    review_case_status_projection_from_state,
    safe_staged_ref,
    staged_safe_error,
    staged_status_not_found,
    utc_now_iso,
)
from src.review_case import (
    REVIEW_CASE_STAGE_NAMES,
    ReviewCase,
    ReviewCaseDownstreamLineageError,
    ReviewCaseStageMachine,
    ReviewCaseStageReadinessError,
    ReviewCaseExecutionJob,
    RunLocalReviewCaseRepository,
    StageTransition,
    enqueue_with_optional_rq,
    review_case_candidate_lineage,
    review_case_comparison_has_displayable_evidence,
    review_case_comparison_id_for_candidate,
    review_case_comparison_lineage,
    review_case_downstream_evidence_chain_context,
    review_case_stage_readiness_from_state,
    review_case_verdict_lineage,
    run_local_review_case_artifact_storage,
)


LOGGER = logging.getLogger(__name__)

CREATE_REVIEW_SCHEMA_VERSION = "review_create_v1"
RECOVERY_SCHEMA_VERSION = "review_recovery_v1"
BUILDER_SCHEMA_VERSION = "builder_setup_v1"
CANDIDATE_SCHEMA_VERSION = "candidate_generation_v1"
COMPARISON_SCHEMA_VERSION = "current_vs_candidate_v1"
VERDICT_SCHEMA_VERSION = "decision_verdict_v1"
REPORT_SCHEMA_VERSION = "report_grounding_v1"
PAYLOAD_DIR = PROJECT_ROOT / "runs" / "fastapi_review_payloads"
SAFE_REF_RE = re.compile(r"^[A-Za-z]:[\\/]|^/(...:Users|home|var|tmp|mnt)/")
STAGED_REVIEW_STARTED_SCHEMA_VERSION = "review_started_v1"
STAGED_REVIEW_STATE_SCHEMA_VERSION = "review_state_v1"
STAGED_STATE_STORE = StagedReviewStateStore(schema_version=STAGED_REVIEW_STATE_SCHEMA_VERSION)
STAGED_STAGE_NAMES: tuple[StagedStageName, ...] = REVIEW_CASE_STAGE_NAMES  # type: ignore[assignment]
STAGED_INITIAL_PROVIDER_STATUS = {
    "live": StagedProviderStatus(
        source="live_provider",
        freshness="pending",
        message="Live mode uses the normal market-data provider path.",
    ),
    "demo_qa": StagedProviderStatus(
        source="frozen_fixture",
        freshness="fixed_demo_dataset",
        message="Demo / QA mode uses deterministic fixture data and skips external market-data providers.",
    ),
}
STAGED_ARTIFACT_REFS: dict[str, str] = {
    "portfolio_xray": "analysis_subject/portfolio_xray.json",
    "stress_report": "analysis_subject/stress_report.json",
    "client_fit_check": "analysis_subject/client_fit_check.json",
    "problem_classification": "analysis_subject/problem_classification.json",
    "candidate_launchpad": "analysis_subject/candidate_launchpad.json",
    "portfolio_alternatives_builder": "analysis_subject/portfolio_alternatives_builder.json",
    "candidate_generation": "candidate_generation.json",
    "candidate_factory_run": "candidate_factory_run.json",
    "candidate_comparison": "candidate_comparison.json",
    "current_vs_candidate": "current_vs_candidate.json",
    "decision_verdict": "decision_verdict.json",
    "ai_commentary_context": "ai_commentary_context.json",
    "site_explanation_bundle": SITE_EXPLANATION_BUNDLE_FILENAME,
}
STAGED_DIAGNOSIS_STAGE_ARTIFACTS: dict[
    StagedStageName,
    dict[str, list[str]],
] = {
    "input": {
        "required": ["payload.json"],
        "optional": ["input.yml"],
    },
    "data_load": {
        "required": ["analysis_subject/run_metadata.json"],
        "optional": [],
    },
    "xray": {
        "required": ["analysis_subject/portfolio_xray.json"],
        "optional": [],
    },
    "stress": {
        "required": ["analysis_subject/stress_report.json"],
        "optional": [],
    },
    "client_fit": {
        "required": [],
        "optional": ["analysis_subject/client_fit_check.json"],
    },
    "problem_classification": {
        "required": ["analysis_subject/problem_classification.json"],
        "optional": [],
    },
    "launchpad_builder": {
        "required": [
            "analysis_subject/candidate_launchpad.json",
            "analysis_subject/portfolio_alternatives_builder.json",
        ],
        "optional": [],
    },
}
STAGED_DOWNSTREAM_STAGE_ARTIFACTS: dict[StagedStageName, dict[str, list[str]]] = {
    "candidate": {
        "required": ["candidate_generation.json"],
        "optional": ["candidate_factory_run.json"],
    },
    "comparison": {
        "required": ["current_vs_candidate.json"],
        "optional": ["candidate_comparison.json", SITE_EXPLANATION_BUNDLE_FILENAME],
    },
    "verdict": {
        "required": ["decision_verdict.json"],
        "optional": [SITE_EXPLANATION_BUNDLE_FILENAME],
    },
    "report": {
        "required": ["ai_commentary_context.json"],
        "optional": [SITE_EXPLANATION_BUNDLE_FILENAME],
    },
}
STAGED_NEXT_STAGE: dict[StagedStageName, StagedStageName] = {
    "candidate": "comparison",
    "comparison": "verdict",
    "verdict": "report",
    "report": "report",
}
DEFAULT_MAX_STAGED_WORKERS = 1
DEFAULT_MAX_STAGED_QUEUED = 3
_staged_worker_lock = threading.Lock()
_staged_worker_condition = threading.Condition(_staged_worker_lock)
_staged_worker_active = 0
_staged_worker_queued = 0


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


def _float(*values: Any) -> float | None:
    for value in values:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
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
    return read_json_file(path)


def _utc_now_iso() -> str:
    return utc_now_iso()


def _staged_state_path(run_dir: Path) -> Path:
    return STAGED_STATE_STORE.path(run_dir)


def _safe_staged_ref(value: Any, *, fallback: str) -> str:
    return safe_staged_ref(value, fallback=fallback)


def _review_case_repository(run_dir: Path) -> RunLocalReviewCaseRepository:
    return RunLocalReviewCaseRepository(run_dir, schema_version=STAGED_REVIEW_STATE_SCHEMA_VERSION)


def _initial_review_case(
    review_id: str,
    *,
    mode: StagedReviewMode,
    owner_id: str | None = None,
) -> ReviewCase:
    now = _utc_now_iso()
    return ReviewCase.initial(
        review_id,
        mode=mode,
        owner_id=owner_id,
        now=now,
        provider_status=STAGED_INITIAL_PROVIDER_STATUS[mode].model_dump(mode="json"),
    )


def _initial_staged_state(
    review_id: str,
    *,
    mode: StagedReviewMode,
    owner_id: str | None = None,
) -> dict[str, Any]:
    return _initial_review_case(
        review_id,
        mode=mode,
        owner_id=owner_id,
    ).to_staged_state_dict(schema_version=STAGED_REVIEW_STATE_SCHEMA_VERSION)


def _write_staged_state(run_dir: Path, state: dict[str, Any]) -> None:
    STAGED_STATE_STORE.write(run_dir, state)


def _read_staged_state(run_dir: Path) -> dict[str, Any]:
    return STAGED_STATE_STORE.read(run_dir)


def _read_optional_staged_state(run_dir: Path) -> dict[str, Any] | None:
    return STAGED_STATE_STORE.read_optional(run_dir)


def _assert_review_owner(state: dict[str, Any] | None, owner_id: str | None) -> None:
    STAGED_STATE_STORE.assert_owner(state, owner_id)


def _read_authorized_staged_state(review_id: str, owner_id: str | None) -> tuple[Path, dict[str, Any]]:
    run_dir = safe_review_run_dir(review_id)
    state = STAGED_STATE_STORE.read(run_dir)
    STAGED_STATE_STORE.assert_owner(state, owner_id)
    return run_dir, state


def _authorize_review_owner(review_id: str, owner_id: str | None) -> None:
    run_dir = safe_review_run_dir(review_id)
    state = STAGED_STATE_STORE.read_optional(run_dir)
    STAGED_STATE_STORE.assert_owner(state, owner_id)


def _is_stage_completed(state: dict[str, Any], stage: StagedStageName) -> bool:
    return review_case_stage_readiness_from_state(state).is_stage_completed(stage)


def _assert_downstream_stage_ready(
    state: dict[str, Any],
    stage: StagedStageName,
    *,
    required_previous: StagedStageName | None = None,
) -> None:
    try:
        review_case_stage_readiness_from_state(state).assert_downstream_stage_ready(
            stage,
            required_previous=required_previous,
        )
    except ReviewCaseStageReadinessError as exc:
        raise ReviewAccessError(
            409,
            exc.issue.code,
            exc.issue.message,
        ) from exc


def _worker_limit(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def _release_memory_pressure() -> None:
    """Best-effort cleanup after memory-heavy review stages.

    FastAPI keeps the Python interpreter alive between requests. Diagnosis and
    candidate stages load pandas/numpy/yfinance data and may launch a candidate
    factory child process; on small Render instances, retaining freed arenas can
    push the service over its memory limit on the next stage. This helper does
    not change calculations or outputs; it only asks Python and, on glibc Linux,
    the allocator to return free memory sooner.
    """

    gc.collect()
    if os.name != "posix":
        return
    try:
        import ctypes

        libc = ctypes.CDLL("libc.so.6")
        trim = getattr(libc, "malloc_trim", None)
        if trim is not None:
            trim(0)
    except Exception:
        return


def _try_reserve_staged_worker_slot() -> bool:
    global _staged_worker_active, _staged_worker_queued
    with _staged_worker_lock:
        limit = _worker_limit("PMRI_STAGED_REVIEW_MAX_WORKERS", DEFAULT_MAX_STAGED_WORKERS)
        queued_limit = _worker_limit("PMRI_STAGED_REVIEW_MAX_QUEUED", DEFAULT_MAX_STAGED_QUEUED)
        if limit <= 0:
            return False
        if _staged_worker_active + _staged_worker_queued >= limit + queued_limit:
            return False
        _staged_worker_queued += 1
        return True


def _mark_staged_worker_started() -> None:
    global _staged_worker_active, _staged_worker_queued
    with _staged_worker_condition:
        while _staged_worker_active >= max(
            1,
            _worker_limit("PMRI_STAGED_REVIEW_MAX_WORKERS", DEFAULT_MAX_STAGED_WORKERS),
        ):
            _staged_worker_condition.wait(timeout=1.0)
        _staged_worker_queued = max(0, _staged_worker_queued - 1)
        _staged_worker_active += 1


def _release_staged_worker_slot() -> None:
    global _staged_worker_active
    with _staged_worker_condition:
        _staged_worker_active = max(0, _staged_worker_active - 1)
        _staged_worker_condition.notify()


def _set_stage_status(
    state: dict[str, Any],
    stage: StagedStageName,
    status: str,
    *,
    artifact_refs: list[str] | None = None,
) -> None:
    ReviewCaseStageMachine(
        clock=_utc_now_iso,
        artifact_ref_sanitizer=lambda ref, stage_name: _safe_staged_ref(
            ref,
            fallback=f"logical://{stage_name}",
        ),
    ).apply_to_staged_state(
        state,
        StageTransition(
            stage=stage,
            status=status,  # type: ignore[arg-type]
            artifact_refs=artifact_refs,
        ),
    )


def _staged_safe_error(
    *,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
    stage: StagedStageName | None,
) -> StagedSafeError:
    return staged_safe_error(
        code=code,
        message=message,
        user_action=user_action,
        retryable=retryable,
        stage=stage,
    )


STAGED_PROVIDER_FAILURE_TERMS = (
    "fred",
    "yahoo",
    "market data",
    "market-data",
    "price",
    "quote",
    "http error",
    "download failed",
    "provider",
)


def _staged_failure_public_message(code: str, fallback: str) -> str:
    if code == "DATA_PROVIDER_FAILED":
        return (
            "Market data provider failed during data loading. "
            "Retry the diagnosis; if it repeats, check provider availability or switch to Demo / QA mode."
        )
    if code == "TIMEOUT":
        return (
            "Portfolio diagnosis timed out while loading or processing data. "
            "Retry the diagnosis; if it repeats, use a smaller portfolio or check provider/network status."
        )
    if code == "INVALID_TICKER":
        return "Portfolio input could not be validated. Check tickers, cash rows, and weights, then run diagnosis again."
    if code == "PYTHON_STAGE_FAILED" and fallback.strip().lower() == "backend run failed.":
        return (
            "Portfolio diagnosis failed during backend execution. "
            "Retry after restarting the backend/frontend; if it repeats, inspect the run state for the failed stage."
        )
    return fallback


def _safe_failure_text_for_classification(review_result: dict[str, Any]) -> str:
    parts = [
        review_result.get("error"),
        review_result.get("details"),
        review_result.get("stdout_tail"),
        review_result.get("stderr_tail"),
    ]
    return " ".join(
        str(part)
        for part in parts
        if part is not None and str(part).strip()
    ).lower()


def _classify_staged_failure(review_result: dict[str, Any], code: int) -> tuple[str, str, str, bool, StagedStageName]:
    details = str(review_result.get("details") or "").lower()
    message = _text(review_result.get("error"), "Portfolio diagnosis failed.") or "Portfolio diagnosis failed."
    lowered = _safe_failure_text_for_classification(review_result)
    if code == 124 or "timeout" in lowered:
        return "TIMEOUT", _staged_failure_public_message("TIMEOUT", message), "retry", True, "data_load"
    if "input_validation_error" in details:
        return "INVALID_TICKER", _staged_failure_public_message("INVALID_TICKER", message), "fix_input", False, "input"
    if any(term in lowered for term in STAGED_PROVIDER_FAILURE_TERMS):
        return "DATA_PROVIDER_FAILED", _staged_failure_public_message("DATA_PROVIDER_FAILED", message), "retry", True, "data_load"
    return "PYTHON_STAGE_FAILED", _staged_failure_public_message("PYTHON_STAGE_FAILED", message), "retry", True, "data_load"


def _existing_stage_refs(run_dir: Path, refs: list[str]) -> list[str]:
    return [_safe_staged_ref(ref, fallback="logical://artifact") for ref in refs if (run_dir / ref).exists()]


def _missing_stage_refs(run_dir: Path, refs: list[str]) -> list[str]:
    return [_safe_staged_ref(ref, fallback="logical://artifact") for ref in refs if not (run_dir / ref).exists()]


def _refresh_staged_artifact_map(state: dict[str, Any], run_dir: Path) -> None:
    state["artifacts"] = run_local_review_case_artifact_storage().manifest_from_existing_refs(
        run_dir,
        STAGED_ARTIFACT_REFS,
    ).to_public_artifacts_map()


def _sync_diagnosis_stage_artifacts(
    state: dict[str, Any],
    run_dir: Path,
    *,
    mark_missing_as_failed: bool,
) -> tuple[StagedStageName | None, list[str], list[str]]:
    """Update diagnosis-stage rows from run-local artifacts.

    The underlying Python runner is still mostly monolithic, so this helper is
    the staged wrapper: it records each canonical stage independently once the
    adapter returns, preserves earlier completed stages, marks optional Client
    Fit context as partial when absent, and reports the first missing required
    artifact without exposing absolute paths.
    """

    warnings: list[str] = []
    for stage, ref_groups in STAGED_DIAGNOSIS_STAGE_ARTIFACTS.items():
        required_refs = ref_groups.get("required", [])
        optional_refs = ref_groups.get("optional", [])
        present_refs = _existing_stage_refs(run_dir, required_refs + optional_refs)
        missing_required_refs = _missing_stage_refs(run_dir, required_refs)

        if missing_required_refs:
            status = "failed" if mark_missing_as_failed else "running"
            _set_stage_status(state, stage, status, artifact_refs=present_refs)
            _refresh_staged_artifact_map(state, run_dir)
            return stage, missing_required_refs, warnings

        if not required_refs and optional_refs and not present_refs:
            _set_stage_status(state, stage, "partial", artifact_refs=[])
            warnings.append(
                "Client Fit context was not produced; use the not_provided compatibility state."
            )
            continue

        _set_stage_status(state, stage, "completed", artifact_refs=present_refs)

    _refresh_staged_artifact_map(state, run_dir)
    return None, [], warnings


def _try_update_staged_downstream_success(review_id: str, stage: StagedStageName) -> None:
    """Best-effort synchronization of explicit downstream FastAPI stage calls.

    Staged diagnosis can complete before candidate, comparison, verdict, and
    report are requested. Those later endpoints remain explicit user actions,
    but once they succeed the run-local ``review_state.json`` should reflect the
    same active lineage so refresh/recovery and route gates do not depend only
    on browser memory.
    """

    if stage not in STAGED_DOWNSTREAM_STAGE_ARTIFACTS:
        return
    try:
        run_dir = safe_review_run_dir(review_id)
        if not _staged_state_path(run_dir).is_file():
            return
        state = _read_staged_state(run_dir)
        refs = STAGED_DOWNSTREAM_STAGE_ARTIFACTS[stage]
        artifact_refs = _existing_stage_refs(run_dir, refs.get("required", []) + refs.get("optional", []))
        _set_stage_status(state, stage, "completed", artifact_refs=artifact_refs)
        _refresh_staged_artifact_map(state, run_dir)
        state["status"] = "completed" if stage == "report" else "partial"
        state["current_stage"] = STAGED_NEXT_STAGE.get(stage, stage)
        state["safe_error"] = None
        _write_staged_state(run_dir, state)
    except Exception:
        return


def _try_update_staged_downstream_problem(
    review_id: str,
    stage: StagedStageName,
    *,
    blocked: bool,
    message: str,
    retryable: bool,
) -> None:
    """Best-effort downstream failure/blocker state without invalidating diagnosis."""

    if stage not in STAGED_DOWNSTREAM_STAGE_ARTIFACTS:
        return
    try:
        run_dir = safe_review_run_dir(review_id)
        if not _staged_state_path(run_dir).is_file():
            return
        state = _read_staged_state(run_dir)
        refs = STAGED_DOWNSTREAM_STAGE_ARTIFACTS[stage]
        artifact_refs = _existing_stage_refs(run_dir, refs.get("required", []) + refs.get("optional", []))
        _set_stage_status(state, stage, "blocked" if blocked else "failed", artifact_refs=artifact_refs)
        _refresh_staged_artifact_map(state, run_dir)
        state["status"] = "partial"
        state["current_stage"] = stage
        state["safe_error"] = _staged_safe_error(
            code="PYTHON_STAGE_FAILED",
            message=message,
            user_action="retry" if retryable else "none",
            retryable=retryable,
            stage=stage,
        ).model_dump(mode="json")
        _write_staged_state(run_dir, state)
    except Exception:
        return


def _demo_qa_client_fit_check(normalized: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic Client Fit fixture evidence from bounded input context."""

    client_fit = _record(normalized.get("client_fit"))
    if not client_fit or client_fit.get("source") == "missing":
        return {
            "schema_version": "client_fit_check_v1",
            "client_fit_status": "not_provided",
            "profile": {"source": "missing", "source_quality": "missing"},
            "checks": [],
            "recommendation_boundary": (
                "Client Fit is non-binding decision support and was not provided for this demo run."
            ),
        }

    profile = {
        key: value
        for key, value in client_fit.items()
        if key
        in {
            "preset_id",
            "source",
            "source_quality",
            "horizon_years",
            "target_return_range",
            "target_vol_range",
            "target_max_drawdown_pct",
        }
    }
    return {
        "schema_version": "client_fit_check_v1",
        "client_fit_status": "watch",
        "profile": profile,
        "checks": [
            {
                "dimension": "volatility_vs_target",
                "portfolio_value": 0.115,
                "client_range": profile.get("target_vol_range") or {"min": 0.07, "max": 0.10},
                "status": "watch",
                "interpretation": (
                    "Demo fixture evidence keeps Client Fit as context only; it does not approve "
                    "suitability or clear objective portfolio issues."
                ),
            }
        ],
        "recommendation_boundary": (
            "Client Fit is non-binding decision support. It does not approve suitability, execute "
            "trades, or hide material portfolio issues."
        ),
    }


def _demo_qa_fixture_outputs(review_id: str, normalized: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return frozen diagnosis artifacts for staged Demo / QA mode.

    The fixture is intentionally compact. It gives the staged UI predictable
    Portfolio X-Ray, Stress, Client Fit, Problem Classification, Launchpad, and
    Builder evidence without calling live market-data providers or changing
    portfolio formulas.
    """

    tickers = [str(item) for item in _list(normalized.get("tickers"))]
    weights = _record(normalized.get("current_weights"))
    top_holding = max(weights.items(), key=lambda item: float(item[1]))[0] if weights else None
    top_weight = float(weights.get(top_holding, 0.0)) if top_holding else None
    client_fit_check = _demo_qa_client_fit_check(normalized)
    analysis_end = "2026-05-31"
    provider = STAGED_INITIAL_PROVIDER_STATUS["demo_qa"].model_dump(mode="json")

    portfolio_xray = {
        "schema_version": "portfolio_xray_v2",
        "mode": "demo_qa",
        "analysis_end": analysis_end,
        "data_source": "frozen_fixture",
        "summary": {
            "headline": "Demo fixture highlights concentration risk in the current portfolio.",
            "top_holding": top_holding,
            "top_holding_weight": top_weight,
        },
        "block_2_1_asset_allocation": {
            "status": "ok",
            "holdings_count": len(tickers),
            "current_weights": weights,
        },
        "warnings": [
            "Demo / QA mode uses frozen fixture evidence and is not live market data."
        ],
    }
    stress_report = {
        "schema_version": "stress_report_v1",
        "mode": "demo_qa",
        "analysis_end": analysis_end,
        "data_source": "frozen_fixture",
        "stress_results_v1": {
            "block_status": "ok",
            "worst_scenario": {
                "scenario_id": "demo_equity_shock",
                "portfolio_loss_pct": -0.18,
                "interpretation": "The frozen demo stress row shows a material drawdown under an equity shock.",
            },
        },
        "current_portfolio_stress_scorecard_v1": {
            "block_status": "ok",
            "stress_diagnosis": {
                "headline": "Stress losses are concentrated in the largest risk exposures.",
                "diagnosis_confidence": "medium",
            },
        },
        "warnings": [
            "Stress evidence is deterministic fixture data for QA and demo reliability."
        ],
    }
    problem_classification = {
        "schema_version": "problem_classification_v3",
        "analysis_end": analysis_end,
        "mode": "demo_qa",
        "primary_diagnosis": {
            "diagnosis_id": "high_concentration",
            "label_en": "High concentration",
            "thesis_en": "The current portfolio is too dependent on its largest exposures.",
            "confidence": "medium",
            "key_evidence": [
                {
                    "interpretation_en": "The frozen demo X-Ray shows the largest holding as the leading capital exposure.",
                    "source_artifact": "portfolio_xray.json",
                }
            ],
        },
        "next_diagnostic_step": {
            "step_type": "targeted_hypothesis_test",
            "label": "Test a diversification candidate.",
            "decision_boundary": "Decision Verdict decides after comparison; this is not a recommendation.",
        },
        "interpretation_chain": {
            "schema_version": "diagnosis_interpretation_chain_v1",
            "diagnostic_only": True,
            "selected_diagnosis_id": "high_concentration",
            "selected_diagnosis_role": "root_cause",
            "source_artifacts": ["portfolio_xray.json", "stress_report.json"],
            "root_cause_narrative": {
                "diagnosis_id": "high_concentration",
                "label_en": "High concentration",
                "diagnosis_role": "root_cause",
                "statement_en": "High concentration is the demo root-cause diagnosis.",
                "root_cause_over_symptom_en": (
                    "Concentration is treated as the root cause because the largest exposures drive "
                    "the stress pattern in the fixture."
                ),
                "portfolio_manager_interpretation_en": (
                    "The portfolio depends too much on a small set of positions."
                ),
                "confidence_context_en": "Confidence is medium because this is frozen QA evidence.",
                "n_supporting_evidence_items": 2,
                "n_rejected_alternatives": 1,
                "source_refs": ["docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md#demo--qa-mode-and-live-mode"],
            },
            "diagnosis_evidence_items": [
                {
                    "evidence_item_id": "demo_ev_top_holding",
                    "linked_problem_id": "high_concentration",
                    "evidence_role": "supports_selected_diagnosis",
                    "signal": "top_holding_weight",
                    "source_artifact": "portfolio_xray.json",
                    "source_block": "block_2_1_asset_allocation",
                    "source_field_path": "summary.top_holding_weight",
                    "observed_value": top_weight,
                    "interpretation_en": "The largest holding dominates the frozen demo portfolio.",
                    "why_relevant_to_diagnosis_en": "High top-holding weight supports concentration risk.",
                    "severity": "medium",
                    "confidence": "medium",
                }
            ],
            "metric_to_diagnosis_trace": [
                {
                    "trace_id": "demo_trace_top_holding_weight",
                    "source_artifact": "portfolio_xray.json",
                    "source_block": "block_2_1_asset_allocation",
                    "source_field_path": "summary.top_holding_weight",
                    "metric_or_signal": "top_holding_weight",
                    "evidence_item_id": "demo_ev_top_holding",
                    "linked_problem_id": "high_concentration",
                    "contributes_to_selected_diagnosis_id": "high_concentration",
                    "contribution": "supports_selected_diagnosis",
                    "interpretation_en": "The top holding is the leading capital exposure in the demo fixture.",
                }
            ],
            "rejected_alternatives": [
                {
                    "problem_id": "data_quality_blocker",
                    "label_en": "Data quality blocker",
                    "reason_code": "demo_fixture_available",
                    "reason_en": "Demo / QA mode uses a complete frozen fixture instead of live provider data.",
                    "top_evidence_item_ids": ["demo_ev_top_holding"],
                }
            ],
            "professional_rationale_refs": [
                {
                    "ref_id": "staged_demo_qa_contract",
                    "source": "docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md",
                    "reason_en": "Defines deterministic Demo / QA execution and live-mode separation.",
                }
            ],
            "next_step_link": {
                "step_type": "targeted_hypothesis_test",
                "label": "Test a diversification candidate.",
                "decision_boundary": "Decision Verdict decides after comparison.",
            },
            "recommendation_boundary_en": "This diagnosis is decision support only and not trade advice.",
        },
        "warnings": [
            "Problem Classification is based on frozen Demo / QA fixture evidence."
        ],
    }
    candidate_launchpad = {
        "schema_version": "candidate_launchpad_v3",
        "mode": "demo_qa",
        "diagnostic_only": True,
        "cards": [
            {
                "card_id": "launchpad_demo_reduce_concentration",
                "title": "Test diversification",
                "goal": "reduce_concentration",
                "source_diagnosis_id": "high_concentration",
                "source_problem_id": "high_concentration",
                "hypothesis_to_test": "Test whether an Equal Weight candidate reduces concentration.",
                "success_criteria": ["Reduce reliance on the largest exposure."],
                "tradeoff_to_watch": "Potential return drag versus the current allocation.",
                "when_to_skip": "Skip if the user only wants to monitor without testing alternatives.",
                "decision_boundary": "Candidate Generation is a diagnostic test; Decision Verdict owns action language.",
                "default_method": "equal_weight",
                "suggested_methods": [{"candidate_method_id": "equal_weight", "method_role": "targeted_hypothesis"}],
                "card_type": "targeted_hypothesis_test",
                "launch_status": "ready",
                "is_rebalance_recommendation": False,
            }
        ],
        "warnings": [
            "Launchpad cards in Demo / QA mode are fixture-backed diagnostic tests, not recommendations."
        ],
    }
    builder = {
        "schema_version": "portfolio_alternatives_builder_v1",
        "diagnostic_only": True,
        "mode": "demo_qa",
        "status": "ok",
        "reason": None,
        "can_generate_candidate": True,
        "selected_card_id": "launchpad_demo_reduce_concentration",
        "candidate_setup": {
            "candidate_setup_id": "candidate_setup_launchpad_demo_reduce_concentration",
            "source_card_id": "launchpad_demo_reduce_concentration",
            "method_id": "equal_weight",
            "is_rebalance_recommendation": False,
        },
        "guardrails": {
            "does_not_generate_candidate": True,
            "does_not_write_weights": True,
            "does_not_write_comparison_or_verdict": True,
            "is_rebalance_recommendation": False,
        },
    }
    run_metadata = {
        "schema_version": "run_metadata_v1",
        "review_id": review_id,
        "mode": "demo_qa",
        "analysis_end": analysis_end,
        "analysis_setup": {
            "input_mode": "current_portfolio",
            "investor_currency": normalized.get("investor_currency"),
            "analysis_window": analysis_end,
            "market_data_provider": "frozen_fixture",
            "provider_status": provider,
        },
        "input_assumptions": {
            "analysis_window": analysis_end,
            "current_weights": weights,
        },
    }
    output_manifest = {
        "schema_version": "output_manifest_v1",
        "mode": "demo_qa",
        "output_profile": "site_api",
        "required_json": sorted(STAGED_ARTIFACT_REFS.values()),
        "provider_status": provider,
    }
    site_explanation_bundle = {
        "schema_version": "site_explanation_bundle_v1",
        "mode": "demo_qa",
        "summary": "Demo / QA mode uses deterministic fixture evidence for staged progress.",
        "provider_status": provider,
    }
    ai_commentary_context = {
        "schema_version": "ai_commentary_context_v1",
        "mode": "demo_qa",
        "grounding_phase": "diagnosis",
        "source_artifacts": {
            "portfolio_xray": "portfolio_xray.json",
            "stress_report": "stress_report.json",
            "problem_classification": "problem_classification.json",
        },
        "warnings": ["This is deterministic fixture context and not LLM-generated commentary."],
    }
    return {
        "run_metadata": run_metadata,
        "portfolio_xray": portfolio_xray,
        "stress_report": stress_report,
        "client_fit_check": client_fit_check,
        "problem_classification": problem_classification,
        "candidate_launchpad": candidate_launchpad,
        "portfolio_alternatives_builder": builder,
        "output_manifest": output_manifest,
        "site_explanation_bundle": site_explanation_bundle,
        "ai_commentary_context": ai_commentary_context,
    }


def _materialize_demo_qa_review(
    review_id: str,
    payload_path: Path,
    run_dir: Path,
) -> tuple[int, Path]:
    """Write deterministic staged Demo / QA artifacts without external providers."""

    payload = _read_json_file(payload_path)
    normalized = normalize_payload(payload)
    analysis_subject = run_dir / "analysis_subject"
    analysis_subject.mkdir(parents=True, exist_ok=True)
    (run_dir / "input.yml").write_text(
        "\n".join(
            [
                "mode: demo_qa",
                "market_data_provider: frozen_fixture",
                f"investor_currency: {normalized.get('investor_currency')}",
                "tickers:",
                *[f"  - {ticker}" for ticker in _list(normalized.get("tickers"))],
                "",
            ]
        ),
        encoding="utf-8",
    )

    outputs = _demo_qa_fixture_outputs(review_id, normalized)
    for key, document in outputs.items():
        filename = f"{key}.json"
        if key == "site_explanation_bundle":
            filename = SITE_EXPLANATION_BUNDLE_FILENAME
        write_json(analysis_subject / filename, document)

    paths = expected_output_paths(run_dir, mode=MODE_DIAGNOSIS_PLUS_PROBLEM)
    read_outputs_data = read_outputs(paths, mode=MODE_DIAGNOSIS_PLUS_PROBLEM)
    result = build_success_result(
        review_id=review_id,
        mode="demo_qa",
        normalized=normalized,
        paths=paths,
        outputs=read_outputs_data,
    )
    result["provider_status"] = STAGED_INITIAL_PROVIDER_STATUS["demo_qa"].model_dump(mode="json")
    result_path = run_dir / "review_result.json"
    write_json(result_path, result)
    return 0, result_path


def _is_demo_qa_staged_review(review_id: str) -> bool:
    try:
        state = _read_staged_state(safe_review_run_dir(review_id))
    except Exception:
        return False
    return state.get("mode") == "demo_qa"


def _demo_qa_candidate_generation_doc(selected_card_id: str) -> dict[str, Any]:
    candidate_id = "equal_weight"
    return {
        "schema_version": "candidate_generation_v1",
        "mode": "demo_qa",
        "selected_card_id": selected_card_id,
        "generation_status": "generated",
        "candidate": {
            "candidate_id": candidate_id,
            "candidate_name": "Equal Weight diagnostic candidate",
            "method": "equal_weight",
            "method_label": "Equal Weight",
            "source_card_id": selected_card_id,
            "source_diagnosis_id": "high_concentration",
            "hypothesis_to_test": "Test whether an Equal Weight candidate reduces concentration.",
            "success_criteria": ["Reduce reliance on the largest exposure."],
            "tradeoff_to_watch": "Potential return drag versus the current allocation.",
            "decision_boundary": "This candidate is a diagnostic test, not a recommendation.",
            "weights": {"fixture_equal_weight": 1.0},
            "weight_summary": {"fixture_equal_weight": 1.0},
        },
        "handoff_to_comparison": {
            "can_compare": True,
            "candidate_id": candidate_id,
            "next_stage": "current_vs_candidate",
            "blocked_reason": None,
        },
        "source_artifacts": [
            "analysis_subject/portfolio_alternatives_builder.json",
            "analysis_subject/candidate_launchpad.json",
        ],
        "warnings": [
            "Demo / QA candidate uses deterministic fixture evidence and is not a live optimized portfolio."
        ],
    }


def _write_demo_qa_candidate(review_id: str, selected_card_id: str) -> dict[str, Any]:
    run_dir = safe_review_run_dir(review_id)
    candidate_generation = _demo_qa_candidate_generation_doc(selected_card_id)
    candidate_id = _text(_record(candidate_generation.get("candidate")).get("candidate_id"))
    factory_run = {
        "schema_version": "candidate_factory_run_v1",
        "mode": "demo_qa",
        "factory_profile_id": "demo_qa_fixture",
        "review_id": review_id,
        "steps": [
            {
                "candidate_id": candidate_id,
                "method": "equal_weight",
                "status": "generated",
                "source": "frozen_fixture",
            }
        ],
        "warnings": [
            "Demo / QA factory run is a deterministic fixture for local browser QA."
        ],
    }
    write_json(run_dir / "candidate_generation.json", candidate_generation)
    write_json(run_dir / "candidate_factory_run.json", factory_run)
    return {
        "review_id": review_id,
        "status": "completed",
        "stage": "candidate_generation",
        "selected_card_id": selected_card_id,
        "candidate_id": candidate_id,
        "generation_status": "generated",
        "can_compare": True,
        "path": f"runs/{review_id}/candidate_generation.json",
        "candidate_generation": candidate_generation,
    }


def _demo_qa_current_vs_candidate_doc(candidate_generation: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    candidate = _record(candidate_generation.get("candidate"))
    return {
        "schema_version": "current_vs_candidate_v1",
        "mode": "demo_qa",
        "comparison_status": "available",
        "view_mode": "one_candidate",
        "baseline": {"display_name": "Current portfolio"},
        "selected_candidate_ids": [candidate_id],
        "comparisons": [
            {
                "candidate_id": candidate_id,
                "display_name": _text(candidate.get("candidate_name"), "Equal Weight diagnostic candidate"),
                "candidate_boundary": _text(
                    candidate.get("decision_boundary"),
                    "This candidate is a diagnostic test, not a recommendation.",
                ),
                "what_improved": [{"label": "Largest-position concentration is lower in the fixture comparison."}],
                "what_worsened": [{"label": "Turnover and tracking difference require review."}],
                "what_stayed_similar": [{"label": "The candidate still keeps broad market exposure."}],
                "dimensions": [
                    {
                        "field": "weight_top1_weight_pct",
                        "label": "Largest holding weight",
                        "category": "concentration",
                        "impact_area": "concentration_risk",
                        "baseline_value": 0.45,
                        "candidate_value": 0.25,
                        "delta": -0.2,
                        "lower_is_better": True,
                        "direction": "improved",
                        "status": "available",
                        "comparison_basis": "candidate_minus_baseline",
                        "materiality": {
                            "is_material": True,
                            "threshold": 0.05,
                            "status": "assessed",
                        },
                    }
                ],
                "unavailable_metrics": [{"field": "live price refresh"}],
                "success_criteria_result": {"overall_status": "met"},
                "materiality_for_decision_review": {"status": "review_candidate"},
                "tradeoff_to_watch": _text(candidate.get("tradeoff_to_watch")),
            }
        ],
        "warnings": [
            "Demo / QA comparison uses deterministic fixture evidence and is not live market data."
        ],
    }


def _write_demo_qa_comparison(review_id: str, candidate_id: str) -> dict[str, Any]:
    run_dir = safe_review_run_dir(review_id)
    candidate_generation = _read_run_local_json(review_id, "candidate_generation.json")
    selected_card_id, actual_candidate_id = _candidate_lineage(review_id, candidate_id)
    current_vs_candidate = _demo_qa_current_vs_candidate_doc(candidate_generation, actual_candidate_id)
    candidate_comparison = {
        "schema_version": "candidate_comparison_v1",
        "mode": "demo_qa",
        "candidate_menu": {
            "review_mode": "demo_qa",
            "is_partial_menu": True,
            "intended_menu_size": 1,
        },
        "candidates": current_vs_candidate["comparisons"],
        "warnings": current_vs_candidate["warnings"],
    }
    write_json(run_dir / "current_vs_candidate.json", current_vs_candidate)
    write_json(run_dir / "candidate_comparison.json", candidate_comparison)
    return {
        "review_id": review_id,
        "status": "completed",
        "stage": "current_vs_candidate",
        "selected_card_id": selected_card_id,
        "candidate_id": actual_candidate_id,
        "paths": {
            "candidate_comparison": f"runs/{review_id}/candidate_comparison.json",
            "current_vs_candidate": f"runs/{review_id}/current_vs_candidate.json",
            "site_explanation_bundle": f"runs/{review_id}/{SITE_EXPLANATION_BUNDLE_FILENAME}",
        },
        "current_vs_candidate": current_vs_candidate,
    }


def _demo_qa_decision_verdict_doc(candidate_id: str) -> dict[str, Any]:
    return {
        "schema_version": "decision_verdict_v1",
        "mode": "demo_qa",
        "verdict_id": "evidence_insufficient",
        "verdict_reason_id": "demo_fixture_decision_support_only",
        "reviewed_candidate_id": candidate_id,
        "confidence": "medium",
        "rationale_summary": (
            "The deterministic demo comparison shows concentration improvement, but it is fixture "
            "evidence and must not be treated as a trade instruction."
        ),
        "recommended_action": "Use the candidate only as a diagnostic comparison in this demo.",
        "confidence_limitations": ["Demo / QA mode does not use live market data."],
        "evidence_summary": {
            "improvements": [{"label": "Concentration improved in the fixture comparison."}],
            "deteriorations": [{"label": "Turnover and tracking difference require review."}],
            "client_fit_decision_context": {
                "client_fit_status": "watch",
                "diagnostic_quality_status": "issue",
                "decision_action": "evidence_insufficient",
                "status_label": "Client Fit watch",
                "status_tone": "amber",
                "boundary_en": "Client Fit remains non-binding display context only.",
                "next_best_test_en": "Review live evidence before making any decision.",
            },
        },
        "what_would_change_verdict": ["Run live mode with current market data."],
        "guardrails": {"does_not_execute_trades": True},
        "warnings": ["Demo / QA verdict is fixture-backed decision support only."],
    }


def _write_demo_qa_verdict(review_id: str, comparison_id: str) -> dict[str, Any]:
    selected_card_id, candidate_id, normalized_comparison_id = _active_comparison_lineage(
        review_id,
        comparison_id,
    )
    verdict = _demo_qa_decision_verdict_doc(candidate_id)
    run_dir = safe_review_run_dir(review_id)
    write_json(run_dir / "decision_verdict.json", verdict)
    return {
        "review_id": review_id,
        "status": "completed",
        "stage": "decision_verdict",
        "selected_card_id": selected_card_id,
        "candidate_id": candidate_id,
        "comparison_id": normalized_comparison_id,
        "path": f"runs/{review_id}/decision_verdict.json",
        "decision_verdict": verdict,
        "site_explanation_bundle_path": f"runs/{review_id}/{SITE_EXPLANATION_BUNDLE_FILENAME}",
    }


def _demo_qa_ai_commentary_context(verdict_id: str) -> dict[str, Any]:
    return {
        "schema_version": "ai_commentary_context_v1",
        "mode": "demo_qa",
        "grounding_phase": "post_compare",
        "client_explanation_draft": {
            "sentences": [
                {"topic": "diagnosis", "text": "The demo diagnosis highlights concentration risk."},
                {
                    "topic": "current_vs_candidate_comparison",
                    "text": "The demo candidate lowers concentration but adds implementation tradeoffs.",
                },
                {
                    "topic": "decision_verdict",
                    "text": "The demo verdict is evidence-insufficient for action because it uses fixture data.",
                },
            ]
        },
        "light_decision_journal": {
            "decision_verdict": verdict_id,
            "key_assumptions_and_limits": ["Demo / QA mode uses frozen fixture evidence."],
            "next_review_trigger": "Run live mode before treating any result as current evidence.",
        },
        "evidence_references": [
            {"artifact": "decision_verdict.json", "field_path": "verdict_id"},
            {"artifact": "current_vs_candidate.json", "field_path": "comparisons[0]"},
        ],
        "source_artifacts": {
            "decision_verdict": "decision_verdict.json",
            "current_vs_candidate": "current_vs_candidate.json",
        },
        "warnings": ["Grounded demo report context is fixture-backed and non-binding."],
    }


def _write_demo_qa_report_context(review_id: str, verdict_id: str) -> dict[str, Any]:
    selected_card_id, candidate_id, comparison_id, actual_verdict_id = _active_verdict_lineage(
        review_id,
        verdict_id,
    )
    ai_context = _demo_qa_ai_commentary_context(actual_verdict_id)
    run_dir = safe_review_run_dir(review_id)
    write_json(run_dir / "ai_commentary_context.json", ai_context)
    return {
        "review_id": review_id,
        "status": "completed",
        "stage": "report_commentary",
        "selected_card_id": selected_card_id,
        "candidate_id": candidate_id,
        "comparison_id": comparison_id,
        "path": f"runs/{review_id}/ai_commentary_context.json",
        "ai_commentary_context": ai_context,
        "site_explanation_bundle_path": f"runs/{review_id}/{SITE_EXPLANATION_BUNDLE_FILENAME}",
    }


def _public_staged_status_from_state(state: dict[str, Any]) -> StagedReviewStatusResponse:
    return review_case_status_projection_from_state(
        state,
        schema_version=STAGED_REVIEW_STATE_SCHEMA_VERSION,
        initial_provider_status=STAGED_INITIAL_PROVIDER_STATUS,
    ).public_status


def _staged_status_not_found(review_id: str, message: str) -> StagedReviewStatusResponse:
    return staged_status_not_found(
        review_id,
        message,
        schema_version=STAGED_REVIEW_STATE_SCHEMA_VERSION,
        initial_provider_status=STAGED_INITIAL_PROVIDER_STATUS["live"],
    )


def _run_staged_review_background(
    review_id: str,
    payload_path: Path,
    *,
    mode: StagedReviewMode,
) -> None:
    """Run the diagnosis adapter and keep run-local staged state synchronized."""

    _mark_staged_worker_started()
    run_dir = safe_review_run_dir(review_id)
    try:
        state = _read_staged_state(run_dir)
    except Exception:
        state = _initial_staged_state(review_id, mode=mode)

    try:
        _set_stage_status(state, "input", "completed", artifact_refs=["payload.json"])
        _set_stage_status(state, "data_load", "running")
        _write_staged_state(run_dir, state)

        if mode == "demo_qa":
            code, result_path = _materialize_demo_qa_review(review_id, payload_path, run_dir)
            state["provider_status"] = STAGED_INITIAL_PROVIDER_STATUS["demo_qa"].model_dump(mode="json")
        else:
            code, result_path = run_from_payload(
                payload_path,
                mode=MODE_DIAGNOSIS_PLUS_PROBLEM,
                timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
                review_id=review_id,
                run_dir=run_dir,
            )
        review_result = _read_json_file(result_path)
        if code != 0 or review_result.get("status") != "completed":
            error_code, message, user_action, retryable, failed_stage = _classify_staged_failure(review_result, code)
            LOGGER.warning(
                "staged review failed review_id=%s code=%s classified_code=%s stage=%s reason=%s",
                review_id,
                code,
                error_code,
                failed_stage,
                scrub_failure_text(_safe_failure_text_for_classification(review_result))[:1200],
            )
            artifact_failed_stage, missing_refs, warnings = _sync_diagnosis_stage_artifacts(
                state,
                run_dir,
                mark_missing_as_failed=False,
            )
            if error_code == "PYTHON_STAGE_FAILED" and artifact_failed_stage is not None:
                failed_stage = artifact_failed_stage
            elif artifact_failed_stage is not None and failed_stage == "data_load":
                failed_stage = artifact_failed_stage
            _set_stage_status(state, failed_stage, "failed")
            state["status"] = "failed"
            state["safe_error"] = _staged_safe_error(
                code=error_code,
                message=message,
                user_action=user_action,
                retryable=retryable,
                stage=failed_stage,
            ).model_dump(mode="json")
            if missing_refs:
                warnings.append(f"Missing expected staged artifact(s): {', '.join(missing_refs)}.")
            state["warnings"] = warnings
            _write_staged_state(run_dir, state)
            return

        missing_stage, missing_refs, warnings = _sync_diagnosis_stage_artifacts(
            state,
            run_dir,
            mark_missing_as_failed=True,
        )
        if missing_stage is not None:
            state["status"] = "failed"
            state["safe_error"] = _staged_safe_error(
                code="ARTIFACT_MISSING",
                message="Portfolio diagnosis completed but a required staged artifact was not found.",
                user_action="retry",
                retryable=True,
                stage=missing_stage,
            ).model_dump(mode="json")
            warnings.append(f"Missing expected staged artifact(s): {', '.join(missing_refs)}.")
            state["warnings"] = warnings
            _write_staged_state(run_dir, state)
            return

        state["status"] = "partial"
        state["current_stage"] = "candidate"
        state["warnings"] = warnings
        state["safe_error"] = None
        _write_staged_state(run_dir, state)
    except Exception as exc:
        LOGGER.exception("staged review crashed review_id=%s stage=data_load", review_id)
        _set_stage_status(state, "data_load", "failed")
        state["status"] = "failed"
        state["safe_error"] = _staged_safe_error(
            code="PYTHON_STAGE_FAILED",
            message="Portfolio diagnosis failed during staged execution.",
            user_action="retry",
            retryable=True,
            stage="data_load",
        ).model_dump(mode="json")
        state["warnings"] = [scrub_failure_text(str(exc))]
        _write_staged_state(run_dir, state)
    finally:
        _release_memory_pressure()
        _release_staged_worker_slot()

def _start_staged_background_worker(
    review_id: str,
    payload_path: Path,
    *,
    mode: StagedReviewMode,
) -> bool:
    result = enqueue_with_optional_rq(
        ReviewCaseExecutionJob(
            review_id=review_id,
            payload_path=payload_path,
            mode=mode,
        ),
        runner=_run_staged_review_background,
        reserve_slot=_try_reserve_staged_worker_slot,
    )
    if result.fallback_from is not None:
        LOGGER.warning(
            "staged review queue backend fallback review_id=%s requested_backend=%s fallback_backend=%s reason=%s metadata=%s",
            review_id,
            result.fallback_from,
            result.backend,
            result.reason,
            result.metadata,
        )
    elif result.backend == "rq_redis":
        LOGGER.info(
            "staged review enqueued review_id=%s backend=%s job_id=%s metadata=%s",
            review_id,
            result.backend,
            result.job_id,
            result.metadata,
        )
    return result.accepted


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


def _failed_envelope_contract_fields(
    *,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
    details: list[str] | None = None,
) -> dict[str, Any]:
    """Return common public failure fields shared by stage response envelopes."""

    return {
        "warnings": [],
        "safe_error": _safe_error(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
        "evidence": ApiEvidence(source_artifacts=[], data_quality="unknown", confidence="unknown"),
    }


def _error_code_for_stage_exception(exc: BaseException, *, stage: str) -> tuple[int, str, str, bool]:
    """Map internal bridge exceptions to bounded public API errors."""

    message = str(exc)
    lowered = message.lower()
    if "not found" in lowered or "was not found" in lowered:
        return 404, "review_not_found" if "review run" in lowered else "artifact_missing", "none", False
    if "does not match" in lowered or "mismatch" in lowered or "different review" in lowered:
        return 409, "lineage_mismatch", "return_to_hypothesis", False
    if "displayable evidence" in lowered or "active current-vs-candidate comparison" in lowered:
        return 409, "comparison_unavailable", "rerun_comparison", False
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
        **_failed_envelope_contract_fields(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
    )


def create_staged_review(request: CreateReviewRequest, *, owner_id: str | None = None) -> tuple[int, StagedReviewStartedResponse]:
    """Create a staged web review and return before diagnosis execution completes."""

    mode: StagedReviewMode = "demo_qa" if request.options.sample_mode else "live"
    review_id, run_dir = create_run_dir()
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = _request_to_bridge_payload(request)
    payload_path = run_dir / "payload.json"
    write_json(payload_path, payload)
    review_case = _initial_review_case(review_id, mode=mode, owner_id=owner_id)
    _review_case_repository(run_dir).save(review_case)
    state = review_case.to_staged_state_dict(schema_version=STAGED_REVIEW_STATE_SCHEMA_VERSION)
    if _start_staged_background_worker(review_id, payload_path, mode=mode) is False:
        state["status"] = "failed"
        state["warnings"] = ["Staged review worker queue is full; retry shortly."]
        state["safe_error"] = _staged_safe_error(
            code="PYTHON_STAGE_FAILED",
            message="Staged review worker queue is full; retry shortly.",
            user_action="retry",
            retryable=True,
            stage="input",
        ).model_dump(mode="json")
        _write_staged_state(run_dir, state)
        return 429, StagedReviewStartedResponse(
            api_version=API_VERSION,
            schema_version=STAGED_REVIEW_STARTED_SCHEMA_VERSION,
            review_id=review_id,
            stage="diagnosis",
            status="failed",
            current_stage="input",
            mode=mode,
            warnings=state["warnings"],
            safe_error=_staged_safe_error(
                code="PYTHON_STAGE_FAILED",
                message="Staged review worker queue is full; retry shortly.",
                user_action="retry",
                retryable=True,
                stage="input",
            ),
        )
    return 200, StagedReviewStartedResponse(
        api_version=API_VERSION,
        schema_version=STAGED_REVIEW_STARTED_SCHEMA_VERSION,
        review_id=review_id,
        stage="diagnosis",
        status="running",
        current_stage="input",
        mode=mode,
        warnings=[],
        safe_error=None,
    )


def get_staged_review_status(review_id: str, *, owner_id: str | None = None) -> tuple[int, StagedReviewStatusResponse]:
    """Return the public safe staged-review status for one run-local review."""

    try:
        _run_dir, state = _read_authorized_staged_state(review_id, owner_id)
    except ReviewAccessError as exc:
        return exc.status_code, _staged_status_not_found(review_id, exc.message)
    except FileNotFoundError:
        return 404, _staged_status_not_found(review_id, "Staged review state was not found.")
    except (PayloadValidationError, ValueError):
        return 404, _staged_status_not_found(review_id, "Staged review state was not found.")
    return 200, _public_staged_status_from_state(state)


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
        **_failed_envelope_contract_fields(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
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
        **_failed_envelope_contract_fields(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
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
        **_failed_envelope_contract_fields(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
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
        **_failed_envelope_contract_fields(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
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
        **_failed_envelope_contract_fields(
            code=code,
            message=message,
            user_action=user_action,
            retryable=retryable,
            details=details,
        ),
    )


def create_review_diagnosis(request: CreateReviewRequest, *, owner_id: str | None = None) -> tuple[int, CreateReviewResponse]:
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
    parameters = _record(candidate_setup.get("parameters"))
    constraints = _record(candidate_setup.get("constraints"))
    success_criteria = [
        str(item)
        for item in _list(candidate_setup.get("success_criteria") or prefill.get("success_criteria"))
        if str(item).strip()
    ]
    client_fit_context = _record(candidate_setup.get("client_fit_context") or prefill.get("client_fit_context"))
    client_fit_test_criteria = _record(
        candidate_setup.get("client_fit_test_criteria") or prefill.get("client_fit_test_criteria")
    )
    builder_setup = BuilderSetupSummary(
        builder_setup_id=_text(candidate_setup.get("candidate_setup_id"), prefill.get("builder_prefill_id")),
        selected_card_id=_text(builder_doc.get("selected_card_id"), candidate_setup.get("source_card_id")),
        method_id=_text(candidate_setup.get("selected_method"), prefill.get("suggested_method")),
        mode=mode,
        constraint_preset=_text(
            candidate_setup.get("constraint_preset"),
            constraints.get("constraint_preset"),
            parameters.get("constraint_preset"),
        ),
        min_asset_weight=_float(
            candidate_setup.get("min_asset_weight"),
            constraints.get("min_asset_weight"),
            parameters.get("min_asset_weight"),
        ),
        max_asset_weight=_float(
            candidate_setup.get("max_asset_weight"),
            constraints.get("max_asset_weight"),
            parameters.get("max_asset_weight"),
        ),
        success_criteria=success_criteria,
        tradeoff_to_watch=_text(candidate_setup.get("tradeoff_to_watch"), prefill.get("tradeoff_to_watch")),
        decision_boundary=_text(candidate_setup.get("decision_boundary"), prefill.get("decision_boundary")),
        client_fit_context=client_fit_context or None,
        client_fit_test_criteria=client_fit_test_criteria or None,
        client_fit_optimizer_boundary=_text(
            candidate_setup.get("client_fit_optimizer_boundary"),
            prefill.get("client_fit_optimizer_boundary"),
        ),
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


def prepare_builder_setup(review_id: str, request: BuilderRequest, *, owner_id: str | None = None) -> tuple[int, BuilderResponse]:
    """Prepare Block 6 Builder setup through FastAPI without generating a candidate."""

    try:
        _run_dir, state = _read_authorized_staged_state(review_id, owner_id)
        _assert_downstream_stage_ready(state, "candidate")
        result = prepare_selected_builder_setup(
            review_id=review_id,
            selected_card_id=request.selected_card_id,
            method=request.overrides.method_id,
            constraint_preset=request.overrides.constraint_preset,
            mode=request.overrides.mode,
            min_asset_weight=request.overrides.min_asset_weight,
            max_asset_weight=request.overrides.max_asset_weight,
        )
    except ReviewAccessError as exc:
        return exc.status_code, _failed_builder_envelope(
            review_id=review_id,
            selected_card_id=request.selected_card_id,
            code=exc.code,
            message=exc.message,
            user_action="return_to_hypothesis" if exc.status_code == 409 else "none",
            retryable=False,
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
            infeasible_reason=None if status == "generated" and can_compare else failure_reason,
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
    review_id: str,
    request: BuilderSetupIdRequest,
    *,
    owner_id: str | None = None,
) -> tuple[int, CandidateResponse]:
    """Generate one Block 7 diagnostic candidate through FastAPI."""

    selected_card_id: str | None = None
    try:
        _run_dir, state = _read_authorized_staged_state(review_id, owner_id)
        _assert_downstream_stage_ready(state, "candidate")
        _builder_doc, selected_card_id = _builder_doc_for_setup(review_id, request.builder_setup_id)
        if _is_demo_qa_staged_review(review_id):
            result = _write_demo_qa_candidate(review_id, selected_card_id)
        else:
            result = generate_selected_candidate(
                review_id=review_id,
                selected_card_id=selected_card_id,
                force=True,
                factory_execution_mode="fast",
            )
    except ReviewAccessError as exc:
        return exc.status_code, _failed_candidate_envelope(
            review_id=review_id,
            builder_setup_id=request.builder_setup_id,
            selected_card_id=selected_card_id,
            code=exc.code,
            message=exc.message,
            user_action="return_to_hypothesis" if exc.status_code == 409 else "none",
            retryable=False,
        )
    except (BuilderSelectionError, CandidateBridgeError, ValueError, FileNotFoundError) as exc:
        status_code, code, user_action, retryable = _error_code_for_stage_exception(exc, stage="candidate")
        _try_update_staged_downstream_problem(
            review_id,
            "candidate",
            blocked=True,
            message=str(exc),
            retryable=retryable,
        )
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
        _try_update_staged_downstream_problem(
            review_id,
            "candidate",
            blocked=False,
            message="Candidate generation failed.",
            retryable=True,
        )
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
    finally:
        _release_memory_pressure()

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
        _try_update_staged_downstream_problem(
            review_id,
            "candidate",
            blocked=True,
            message=safe_error.message,
            retryable=False,
        )
    else:
        _try_update_staged_downstream_success(review_id, "candidate")
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
    try:
        lineage = review_case_candidate_lineage(candidate_generation, candidate_id)
    except ReviewCaseDownstreamLineageError as exc:
        raise CandidateBridgeError(str(exc)) from exc
    return lineage.selected_card_id, lineage.candidate_id


def _comparison_id_for_candidate(candidate_id: str | None) -> str | None:
    return review_case_comparison_id_for_candidate(candidate_id)


def _active_comparison_lineage(review_id: str, comparison_id: str) -> tuple[str, str, str]:
    current_vs_candidate = _read_run_local_json(review_id, "current_vs_candidate.json")
    candidate_generation = _read_run_local_json(review_id, "candidate_generation.json")
    try:
        lineage = review_case_comparison_lineage(
            candidate_generation=candidate_generation,
            current_vs_candidate=current_vs_candidate,
            requested_comparison_id=comparison_id,
        )
    except ReviewCaseDownstreamLineageError as exc:
        raise ComparisonBridgeError(str(exc)) from exc
    return lineage.selected_card_id, lineage.candidate_id, lineage.comparison_id


def _active_verdict_lineage(review_id: str, verdict_id: str) -> tuple[str, str, str, str]:
    verdict = _read_run_local_json(review_id, "decision_verdict.json")
    candidate_generation = _read_run_local_json(review_id, "candidate_generation.json")
    current_vs_candidate = _read_run_local_json(review_id, "current_vs_candidate.json")
    try:
        lineage = review_case_verdict_lineage(
            candidate_generation=candidate_generation,
            current_vs_candidate=current_vs_candidate,
            verdict=verdict,
            requested_verdict_id=verdict_id,
        )
    except ReviewCaseDownstreamLineageError as exc:
        raise VerdictBridgeError(str(exc)) from exc
    return lineage.selected_card_id, lineage.candidate_id, lineage.comparison_id, lineage.verdict_id


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

    context = review_case_downstream_evidence_chain_context(
        _record(candidate_generation),
        comparison_row=_record(comparison_row),
        verdict=_record(verdict),
        ai_context=_record(ai_context),
    )
    return DownstreamEvidenceChainContext(**context.to_public_dict())


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
        current_vs_candidate=current_vs_candidate,
        evidence_chain_context=evidence_chain_context,
        client_fit=_client_fit_display_summary(client_fit_check),
        next_allowed_actions=["generate_verdict"] if has_row else ["test_another_hypothesis"],  # type: ignore[list-item]
    )


def _comparison_has_displayable_evidence(current_vs_candidate: dict[str, Any], candidate_id: str | None) -> bool:
    return review_case_comparison_has_displayable_evidence(current_vs_candidate, candidate_id)


def run_current_vs_candidate(
    review_id: str,
    request: CandidateIdRequest,
    *,
    owner_id: str | None = None,
) -> tuple[int, ComparisonResponse]:
    """Run Block 8 current-vs-candidate comparison through FastAPI."""

    selected_card_id: str | None = None
    try:
        _run_dir, state = _read_authorized_staged_state(review_id, owner_id)
        _assert_downstream_stage_ready(state, "comparison", required_previous="candidate")
        selected_card_id, _candidate_id = _candidate_lineage(review_id, request.candidate_id)
        if _is_demo_qa_staged_review(review_id):
            result = _write_demo_qa_comparison(review_id, request.candidate_id)
        else:
            result = compare_selected_candidate(
                review_id=review_id,
                selected_card_id=selected_card_id,
            )
    except ReviewAccessError as exc:
        return exc.status_code, _failed_comparison_envelope(
            review_id=review_id,
            candidate_id=request.candidate_id,
            selected_card_id=selected_card_id,
            code=exc.code,
            message=exc.message,
            user_action="return_to_hypothesis" if exc.status_code == 409 else "none",
            retryable=False,
        )
    except (CandidateBridgeError, ComparisonBridgeError, FileNotFoundError, ValueError) as exc:
        status_code, code, user_action, retryable = _error_code_for_stage_exception(exc, stage="comparison")
        if code == "backend_failed":
            code = "comparison_unavailable"
            user_action = "return_to_hypothesis"
            retryable = False
        _try_update_staged_downstream_problem(
            review_id,
            "comparison",
            blocked=True,
            message=str(exc),
            retryable=retryable,
        )
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
        _try_update_staged_downstream_problem(
            review_id,
            "comparison",
            blocked=False,
            message="Current-vs-candidate comparison failed.",
            retryable=True,
        )
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
    has_displayable_evidence = _comparison_has_displayable_evidence(current_vs_candidate, candidate_id)
    if not has_displayable_evidence:
        data.next_allowed_actions = ["test_another_hypothesis"]  # type: ignore[list-item]
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
    safe_error = None
    if has_displayable_evidence:
        _try_update_staged_downstream_success(review_id, "comparison")
    else:
        safe_error = _safe_error(
            code="comparison_unavailable",
            message="Current-vs-candidate comparison did not produce displayable evidence for the selected candidate.",
            user_action="return_to_hypothesis",
            retryable=False,
        )
        _try_update_staged_downstream_problem(
            review_id,
            "comparison",
            blocked=True,
            message=safe_error.message,
            retryable=False,
        )
    return 200, ComparisonResponse(
        api_version=API_VERSION,
        schema_version=COMPARISON_SCHEMA_VERSION,
        review_id=review_id,
        stage="comparison",
        status="ok" if has_displayable_evidence else "blocked",
        lineage=ApiLineage(
            review_id=review_id,
            selected_card_id=selected_card_id,
            candidate_id=candidate_id,
            comparison_id=comparison_id,
        ),
        data=data,
        warnings=warnings,
        safe_error=safe_error,
        evidence=ApiEvidence(
            source_artifacts=refs,
            data_quality="ok" if has_displayable_evidence else "partial",
            confidence="medium" if has_displayable_evidence else "low",
        ),
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
    review_id: str,
    request: ComparisonIdRequest,
    *,
    owner_id: str | None = None,
) -> tuple[int, VerdictResponse]:
    """Run Block 9 non-binding Decision Verdict through FastAPI."""

    selected_card_id: str | None = None
    candidate_id: str | None = None
    comparison_id = request.comparison_id
    try:
        _run_dir, state = _read_authorized_staged_state(review_id, owner_id)
        _assert_downstream_stage_ready(state, "verdict", required_previous="comparison")
        selected_card_id, candidate_id, comparison_id = _active_comparison_lineage(
            review_id,
            request.comparison_id,
        )
        if _is_demo_qa_staged_review(review_id):
            result = _write_demo_qa_verdict(review_id, request.comparison_id)
        else:
            result = write_selected_candidate_verdict(
                review_id=review_id,
                selected_card_id=selected_card_id,
            )
    except ReviewAccessError as exc:
        return exc.status_code, _failed_verdict_envelope(
            review_id=review_id,
            comparison_id=comparison_id,
            candidate_id=candidate_id,
            selected_card_id=selected_card_id,
            code=exc.code,
            message=exc.message,
            user_action="rerun_comparison" if exc.status_code == 409 else "none",
            retryable=False,
        )
    except (CandidateBridgeError, ComparisonBridgeError, VerdictBridgeError, FileNotFoundError, ValueError) as exc:
        status_code, code, user_action, retryable = _error_code_for_stage_exception(exc, stage="verdict")
        if code == "backend_failed":
            status_code = 409
            code = "verdict_unavailable"
            user_action = "rerun_comparison"
            retryable = False
        _try_update_staged_downstream_problem(
            review_id,
            "verdict",
            blocked=True,
            message=str(exc),
            retryable=retryable,
        )
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
        _try_update_staged_downstream_problem(
            review_id,
            "verdict",
            blocked=False,
            message="Decision Verdict generation failed.",
            retryable=True,
        )
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
    _try_update_staged_downstream_success(review_id, "verdict")
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
    review_id: str,
    request: VerdictIdRequest,
    *,
    owner_id: str | None = None,
) -> tuple[int, ReportResponse]:
    """Run grounded report/AI Commentary context through FastAPI."""

    selected_card_id: str | None = None
    candidate_id: str | None = None
    comparison_id: str | None = None
    verdict_id = request.verdict_id
    try:
        _run_dir, state = _read_authorized_staged_state(review_id, owner_id)
        _assert_downstream_stage_ready(state, "report", required_previous="verdict")
        selected_card_id, candidate_id, comparison_id, verdict_id = _active_verdict_lineage(
            review_id,
            request.verdict_id,
        )
        if _is_demo_qa_staged_review(review_id):
            result = _write_demo_qa_report_context(review_id, request.verdict_id)
        else:
            result = write_selected_report_context(
                review_id=review_id,
                selected_card_id=selected_card_id,
            )
    except ReviewAccessError as exc:
        return exc.status_code, _failed_report_envelope(
            review_id=review_id,
            verdict_id=verdict_id,
            candidate_id=candidate_id,
            selected_card_id=selected_card_id,
            comparison_id=comparison_id,
            code=exc.code,
            message=exc.message,
            user_action="rerun_verdict" if exc.status_code == 409 else "none",
            retryable=False,
        )
    except (CandidateBridgeError, ComparisonBridgeError, VerdictBridgeError, ReportBridgeError, FileNotFoundError, ValueError) as exc:
        status_code, code, user_action, retryable = _error_code_for_stage_exception(exc, stage="report")
        if code == "backend_failed":
            code = "report_unavailable"
            user_action = "rerun_verdict"
            retryable = False
        _try_update_staged_downstream_problem(
            review_id,
            "report",
            blocked=True,
            message=str(exc),
            retryable=retryable,
        )
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
        _try_update_staged_downstream_problem(
            review_id,
            "report",
            blocked=False,
            message="Grounded report context generation failed.",
            retryable=True,
        )
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
    _try_update_staged_downstream_success(review_id, "report")
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


RECOVERABLE_DIAGNOSIS_OUTPUT_KEYS = (
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
)


def _recoverable_artifact_payloads(review_result: dict[str, Any]) -> dict[str, Any]:
    """Return bounded run-local diagnosis payloads needed to rebuild frontend state.

    Recovery intentionally does not restore candidate/comparison/verdict/report
    stages as active state, but the diagnosis and evidence screens need the same
    current-portfolio artifacts that were available immediately after a fresh
    run. Keep this allowlist narrow and screen-owned.
    """

    outputs = _record(review_result.get("outputs"))
    return {
        key: value
        for key, value in outputs.items()
        if key in RECOVERABLE_DIAGNOSIS_OUTPUT_KEYS and isinstance(value, (dict, list))
    }


def recover_review_diagnosis(review_id: str, *, owner_id: str | None = None) -> tuple[int, ReviewRecoveryResponse]:
    """Recover diagnosis, evidence, and hypothesis setup state for a run-local review."""

    try:
        _authorize_review_owner(review_id, owner_id)
        review_result = _read_recoverable_review(review_id)
    except ReviewAccessError as exc:
        return exc.status_code, _failed_recovery_envelope(
            review_id=review_id,
            code=exc.code,
            message=exc.message,
            user_action="none",
            retryable=False,
        )
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
        artifact_payloads=_recoverable_artifact_payloads(review_result),
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
