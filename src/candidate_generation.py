"""Block 7 Candidate Generation contract.

This module turns one validated Block 6 ``CandidateSetup`` into one
product-facing candidate-generation attempt.  It is deliberately narrow: it
does not pick among many candidates, does not create a rebalance
recommendation, and does not compare or decide anything.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.portfolio_alternatives_builder import (
    UNCAPPED_MODE_CONCENTRATION_WARNING,
    candidate_id_for_builder_method,
)

CANDIDATE_GENERATION_SCHEMA_VERSION = "candidate_generation_v1"
CANDIDATE_GENERATION_FILENAME = "candidate_generation.json"
CANDIDATE_GENERATION_SOURCE = "block_6_builder_setup"

SUCCESS_STATUSES = frozenset({"generated", "available"})
TERMINAL_FAILURE_STATUSES = frozenset({"failed", "infeasible"})
ALLOWED_GENERATION_STATUSES = SUCCESS_STATUSES | TERMINAL_FAILURE_STATUSES | frozenset(
    {"attempt_created"}
)


class CandidateGenerationError(ValueError):
    """Raised when Block 7 cannot create a valid candidate attempt."""


def build_candidate_generation_document(
    candidate_setup: Mapping[str, Any],
    *,
    weights: Mapping[str, Any] | None = None,
    status: str | None = None,
    failure_reason: str | None = None,
    infeasibility_reason: str | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build one ``candidate_generation_v1`` artifact from a CandidateSetup.

    ``weights`` are optional at this contract layer so tests and later runtime
    callers can preserve generated weights without making Session 02 execute
    optimizer plumbing.  When weights are absent, the attempt is explicit and
    not comparable yet.
    """

    _assert_valid_candidate_setup(candidate_setup)

    parameters = _mapping(candidate_setup.get("parameters"))
    constraints = _mapping(candidate_setup.get("constraints"))
    method = _string(
        candidate_setup.get("selected_method")
        or parameters.get("method")
        or constraints.get("method")
    )
    mode = _normalized_mode(parameters.get("mode") or constraints.get("mode"))
    method_variant = candidate_id_for_builder_method(method, mode=mode)
    if method_variant is None:
        raise CandidateGenerationError(f"unsupported_candidate_method:{method}")

    candidate_weights = dict(weights) if isinstance(weights, Mapping) else None
    generation_status = _generation_status(
        status=status,
        weights=candidate_weights,
        failure_reason=failure_reason,
        infeasibility_reason=infeasibility_reason,
    )
    candidate_status = generation_status
    capped = _bool_from_setup(
        constraints.get("capped"),
        default=mode != "uncapped",
    )
    uncapped = _bool_from_setup(
        constraints.get("uncapped"),
        default=mode == "uncapped",
    )
    min_asset_weight = _first_present(
        constraints.get("min_asset_weight"),
        parameters.get("min_asset_weight"),
    )
    max_asset_weight = _first_present(
        constraints.get("max_asset_weight"),
        parameters.get("max_asset_weight"),
    )
    constraint_preset = _first_present(
        constraints.get("constraint_preset"),
        parameters.get("constraint_preset"),
    )

    artifact_warnings = list(warnings or [])
    artifact_warnings.extend(str(row) for row in candidate_setup.get("validation_warnings") or [])
    if uncapped and UNCAPPED_MODE_CONCENTRATION_WARNING not in artifact_warnings:
        artifact_warnings.append(UNCAPPED_MODE_CONCENTRATION_WARNING)

    candidate = {
        "candidate_id": method_variant,
        "candidate_name": _candidate_name(method, method_variant),
        "source_card_id": candidate_setup.get("source_card_id"),
        "source_diagnosis_id": candidate_setup.get("source_diagnosis_id"),
        "source_launchpad_card_type": candidate_setup.get("source_launchpad_card_type")
        or candidate_setup.get("card_type"),
        "source_builder_setup_id": candidate_setup.get("builder_prefill_id"),
        "candidate_setup_id": candidate_setup.get("candidate_setup_id"),
        "goal": candidate_setup.get("goal"),
        "hypothesis_to_test": candidate_setup.get("hypothesis_to_test"),
        "method": method,
        "method_variant": method_variant,
        "capped": capped,
        "uncapped": uncapped,
        "min_asset_weight": min_asset_weight,
        "max_asset_weight": max_asset_weight,
        "constraint_preset": constraint_preset,
        "parameters": parameters,
        "constraints": constraints,
        "weights": candidate_weights,
        "status": candidate_status,
        "failure_reason": failure_reason,
        "infeasibility_reason": infeasibility_reason,
        "success_criteria": list(candidate_setup.get("success_criteria") or []),
        "tradeoff_to_watch": candidate_setup.get("tradeoff_to_watch"),
        "decision_boundary": candidate_setup.get("decision_boundary"),
        "is_rebalance_recommendation": False,
        "generation_source": CANDIDATE_GENERATION_SOURCE,
    }
    can_compare = generation_status in SUCCESS_STATUSES and bool(candidate_weights)
    document = {
        "schema_version": CANDIDATE_GENERATION_SCHEMA_VERSION,
        "diagnostic_only": True,
        "generated_at": _utc_now_iso(),
        "candidate": candidate,
        "generation_status": generation_status,
        "source_builder_setup": {
            "candidate_setup_id": candidate_setup.get("candidate_setup_id"),
            "builder_prefill_id": candidate_setup.get("builder_prefill_id"),
            "source_card_id": candidate_setup.get("source_card_id"),
            "source_diagnosis_id": candidate_setup.get("source_diagnosis_id"),
            "validation_status": candidate_setup.get("validation_status"),
            "can_generate_candidate": candidate_setup.get("can_generate_candidate"),
            "artifact": "portfolio_alternatives_builder.json",
        },
        "method_availability": {
            "method": method,
            "method_variant": method_variant,
            "mode": mode,
            "available": True,
            "availability_status": "available",
            "backend_candidate_id": method_variant,
        },
        "warnings": artifact_warnings,
        "handoff_to_comparison": {
            "can_compare": can_compare,
            "next_artifact": "current_vs_candidate.json" if can_compare else None,
            "reason": "valid_generated_candidate" if can_compare else _comparison_blocked_reason(generation_status),
            "blocked_reason": None if can_compare else _comparison_blocked_reason(generation_status),
            "candidate_id": method_variant,
            "requires_current_vs_candidate": True,
            "does_not_create_verdict": True,
        },
        "guardrails": {
            "creates_exactly_one_candidate_attempt": True,
            "is_rebalance_recommendation": False,
            "does_not_compare_candidates": True,
            "does_not_create_decision_verdict": True,
            "does_not_execute_trades": True,
        },
    }
    violations = candidate_generation_contract_violations(document)
    if violations:
        raise CandidateGenerationError(
            "candidate_generation_contract_violation:" + "; ".join(violations)
        )
    return document


def write_candidate_generation_outputs(
    output_dir: str | Path,
    *,
    candidate_setup: Mapping[str, Any],
    weights: Mapping[str, Any] | None = None,
    status: str | None = None,
    failure_reason: str | None = None,
    infeasibility_reason: str | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Path]:
    """Write ``candidate_generation.json`` under ``output_dir``."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    document = build_candidate_generation_document(
        candidate_setup,
        weights=weights,
        status=status,
        failure_reason=failure_reason,
        infeasibility_reason=infeasibility_reason,
        warnings=warnings,
    )
    path = out / CANDIDATE_GENERATION_FILENAME
    with path.open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False, default=str)
    return {"candidate_generation_json": path}


def candidate_setup_from_builder_document(
    builder_document: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Extract the validated CandidateSetup from a Block 6 Builder artifact."""

    if not isinstance(builder_document, Mapping):
        raise CandidateGenerationError("builder_document_missing_or_invalid")
    if builder_document.get("can_generate_candidate") is not True:
        raise CandidateGenerationError("builder_document_cannot_generate_candidate")
    candidate_setup = builder_document.get("candidate_setup")
    if not isinstance(candidate_setup, Mapping):
        raise CandidateGenerationError("candidate_setup_missing_or_invalid")
    return candidate_setup


def candidate_generation_contract_violations(document: Mapping[str, Any] | None) -> list[str]:
    """Return contract violations for a ``candidate_generation_v1`` document."""

    if not isinstance(document, Mapping):
        return ["candidate_generation: document is missing or not an object"]

    violations: list[str] = []
    required_top_level = (
        "candidate",
        "generation_status",
        "source_builder_setup",
        "method_availability",
        "warnings",
        "handoff_to_comparison",
    )
    missing = [field for field in required_top_level if field not in document]
    if missing:
        violations.append(f"candidate_generation: missing fields: {', '.join(missing)}")

    candidate = document.get("candidate")
    if not isinstance(candidate, Mapping):
        violations.append("candidate_generation: candidate must be an object")
        return violations

    required_candidate_fields = (
        "candidate_id",
        "candidate_name",
        "source_card_id",
        "source_diagnosis_id",
        "source_launchpad_card_type",
        "source_builder_setup_id",
        "candidate_setup_id",
        "goal",
        "hypothesis_to_test",
        "method",
        "method_variant",
        "capped",
        "uncapped",
        "min_asset_weight",
        "max_asset_weight",
        "constraint_preset",
        "parameters",
        "constraints",
        "weights",
        "status",
        "failure_reason",
        "infeasibility_reason",
        "success_criteria",
        "tradeoff_to_watch",
        "decision_boundary",
        "is_rebalance_recommendation",
        "generation_source",
    )
    missing_candidate = [field for field in required_candidate_fields if field not in candidate]
    if missing_candidate:
        violations.append(
            f"candidate_generation.candidate: missing fields: {', '.join(missing_candidate)}"
        )
    if candidate.get("is_rebalance_recommendation") is not False:
        violations.append("candidate_generation.candidate: is_rebalance_recommendation must be false")
    if candidate.get("generation_source") != CANDIDATE_GENERATION_SOURCE:
        violations.append("candidate_generation.candidate: generation_source must be block_6_builder_setup")
    if document.get("generation_status") not in ALLOWED_GENERATION_STATUSES:
        violations.append(
            f"candidate_generation: invalid generation_status {document.get('generation_status')!r}"
        )
    if candidate.get("status") != document.get("generation_status"):
        violations.append("candidate_generation.candidate: status must match generation_status")
    weights = candidate.get("weights")
    has_weights = isinstance(weights, Mapping) and bool(weights)
    handoff = document.get("handoff_to_comparison")
    can_compare = handoff.get("can_compare") if isinstance(handoff, Mapping) else None
    status = str(document.get("generation_status") or "")
    if status == "generated":
        if not has_weights:
            violations.append("candidate_generation.generated: weights must be non-empty")
        if can_compare is not True:
            violations.append("candidate_generation.generated: handoff_to_comparison.can_compare must be true")
    if status in TERMINAL_FAILURE_STATUSES:
        if has_weights:
            violations.append("candidate_generation.failed_or_infeasible: weights must be null or empty")
        if can_compare is not False:
            violations.append("candidate_generation.failed_or_infeasible: handoff_to_comparison.can_compare must be false")
    if "verdict" in candidate or "recommended_action" in candidate:
        violations.append("candidate_generation.candidate: verdict/action fields are prohibited")
    return violations


def _assert_valid_candidate_setup(candidate_setup: Mapping[str, Any]) -> None:
    if not isinstance(candidate_setup, Mapping):
        raise CandidateGenerationError("candidate_setup_missing_or_invalid")
    if candidate_setup.get("validation_status") != "valid":
        raise CandidateGenerationError(
            f"candidate_setup_not_valid:{candidate_setup.get('validation_status')}"
        )
    if candidate_setup.get("can_generate_candidate") is not True:
        raise CandidateGenerationError("candidate_setup_cannot_generate_candidate")
    if candidate_setup.get("is_rebalance_recommendation") is not False:
        raise CandidateGenerationError("candidate_setup_must_not_be_rebalance_recommendation")


def _generation_status(
    *,
    status: str | None,
    weights: Mapping[str, Any] | None,
    failure_reason: str | None,
    infeasibility_reason: str | None,
) -> str:
    if status is not None:
        normalized = str(status).strip()
        if normalized not in ALLOWED_GENERATION_STATUSES:
            raise CandidateGenerationError(f"unsupported_generation_status:{normalized}")
        return normalized
    if infeasibility_reason:
        return "infeasible"
    if failure_reason:
        return "failed"
    if weights:
        return "generated"
    return "attempt_created"


def _comparison_blocked_reason(generation_status: str) -> str:
    if generation_status == "attempt_created":
        return "candidate_weights_not_available"
    if generation_status in TERMINAL_FAILURE_STATUSES:
        return f"candidate_generation_{generation_status}"
    return "candidate_not_comparable"


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise CandidateGenerationError("candidate_method_missing")
    return text


def _normalized_mode(value: Any) -> str:
    text = str(value or "capped").strip().lower().replace("-", "_")
    return "uncapped" if text == "uncapped" else "capped"


def _bool_from_setup(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _candidate_name(method: str, method_variant: str) -> str:
    label = method.replace("_", " ").title()
    if method_variant != method:
        return f"{label} ({method_variant})"
    return label


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
