"""Optimization comparison readiness checklist (Block 5 Session 10).

Read-only aggregation of artifact presence for optimizer-backed comparison rows.
Does not rerun optimizers, recompute weights, or change comparison ranking.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.optimization_status import optimization_quality_family

SCHEMA_VERSION = "optimizer_comparison_readiness_v1"
OPTIMIZER_COMPARISON_ROLES = frozenset(
    {"optimizer_candidate", "robust_candidate", "policy"}
)

_READINESS_STALE_WARNING_PREFIXES = (
    "stale_snapshot_analysis_end:",
    "stale_config_fingerprint:",
)


def _artifact_check(
    *,
    present: bool,
    required_for_fair_comparison: bool = True,
    source: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "present": bool(present),
        "required_for_fair_comparison": bool(required_for_fair_comparison),
    }
    if source:
        out["source"] = source
    if detail:
        out["detail"] = detail
    return out


def _weights_check(
    folder: Path,
    *,
    baseline_metadata: dict[str, Any],
    snap_10y: dict[str, Any] | None,
) -> dict[str, Any]:
    sources: list[str] = []
    if (folder / "weights.json").is_file():
        sources.append("weights.json")
    weights_raw = (snap_10y or {}).get("final_weights_total")
    if isinstance(weights_raw, dict) and weights_raw:
        sources.append("snapshot_10y.final_weights_total")
    meta_weights = baseline_metadata.get("final_weights") or baseline_metadata.get("weights")
    if isinstance(meta_weights, dict) and meta_weights:
        sources.append("baseline_weights_metadata.weights")
    present = bool(sources)
    return _artifact_check(
        present=present,
        source=sources[0] if len(sources) == 1 else None,
        detail=", ".join(sources) if sources else "missing",
    )


def _freshness_check(
    *,
    factory_step: dict[str, Any],
    warnings: list[str],
    snap_10y: dict[str, Any] | None,
    expected_analysis_end: str | None,
) -> dict[str, Any]:
    stale = any(
        str(w).startswith(_READINESS_STALE_WARNING_PREFIXES) for w in warnings
    )
    freshness_status = factory_step.get("freshness_status")
    snapshot_end = (snap_10y or {}).get("analysis_end")
    detail_parts: list[str] = []
    if freshness_status:
        detail_parts.append(f"factory_freshness_status={freshness_status}")
    if snapshot_end is not None:
        detail_parts.append(f"snapshot_analysis_end={snapshot_end}")
    if expected_analysis_end:
        detail_parts.append(f"expected_analysis_end={expected_analysis_end}")

    if stale:
        present = False
        detail = "stale_snapshot_or_config"
    elif freshness_status == "fresh":
        present = True
        detail = "factory_step_fresh"
    elif expected_analysis_end and snapshot_end is not None:
        present = str(snapshot_end) == str(expected_analysis_end)
        detail = "snapshot_analysis_end_matches_review" if present else "analysis_end_mismatch"
    elif snapshot_end is not None:
        present = True
        detail = "snapshot_present_freshness_unchecked"
    else:
        present = False
        detail = "freshness_unknown"

    if detail_parts and detail not in detail_parts:
        detail = f"{detail}; " + "; ".join(detail_parts)

    return _artifact_check(
        present=present,
        source=str(freshness_status) if freshness_status else None,
        detail=detail,
    )


def _overall_readiness_status(
    *,
    comparison_status: str,
    quality_family: str,
    checks: dict[str, dict[str, Any]],
    gaps: list[str],
    fair_comparison_ready: bool,
) -> str:
    if comparison_status == "unavailable" or quality_family == "failed":
        return "failed"
    if quality_family == "approximate":
        return "degraded_quality"
    if quality_family == "unknown":
        return "partial"
    if not checks["weights"]["present"] or not checks["snapshot_10y"]["present"]:
        return "not_ready"
    if fair_comparison_ready and comparison_status == "available":
        return "ready"
    if gaps:
        return "partial"
    if comparison_status == "degraded":
        return "partial"
    return "ready"


def build_optimization_readiness(
    folder: Path,
    *,
    role: str,
    construction_disclosure: dict[str, Any],
    comparison_status: str,
    unavailable_reason: str | None,
    warnings: list[str],
    expected_analysis_end: str | None = None,
    primary_snapshot_name: str = "snapshot_10y.json",
) -> dict[str, Any] | None:
    """
    Build optimizer comparison readiness for roles that use the Optimization Engine.

    Returns None for non-optimizer comparison roles (benchmarks, subject, current).
    """
    if role not in OPTIMIZER_COMPARISON_ROLES:
        return None

    baseline_metadata = construction_disclosure.get("baseline_metadata")
    if not isinstance(baseline_metadata, dict):
        baseline_metadata = {}

    snap_path = folder / primary_snapshot_name
    snap_10y = None
    if snap_path.is_file():
        try:
            with open(snap_path, encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                snap_10y = loaded
        except (OSError, json.JSONDecodeError):
            snap_10y = None

    factory_step = construction_disclosure.get("factory_step")
    if not isinstance(factory_step, dict):
        factory_step = {}

    methodology = construction_disclosure.get("optimizer_methodology")
    has_methodology = isinstance(methodology, dict) and bool(methodology)
    quality = construction_disclosure.get("optimizer_quality")
    if not isinstance(quality, dict):
        quality = {}
    quality_status = quality.get("optimization_quality_status") or "unknown"
    quality_family = quality.get("optimization_quality_family") or optimization_quality_family(
        quality_status,
        fallback_used=quality.get("fallback_used", False),
    )

    disclosure_status = str(
        construction_disclosure.get("disclosure_status") or "missing"
    )
    stress_present = (folder / "stress_report.json").is_file()
    if not stress_present and isinstance(snap_10y, dict):
        suite = snap_10y.get("stress_suite_results") or {}
        stress_present = bool((suite.get("overall") if isinstance(suite, dict) else None))

    checks: dict[str, dict[str, Any]] = {
        "weights": _weights_check(
            folder,
            baseline_metadata=baseline_metadata,
            snap_10y=snap_10y,
        ),
        "snapshot_10y": _artifact_check(
            present=snap_path.is_file(),
            source=primary_snapshot_name if snap_path.is_file() else None,
        ),
        "stress_summary": _artifact_check(
            present=stress_present,
            source="stress_report.json"
            if (folder / "stress_report.json").is_file()
            else "snapshot_10y.stress_suite_results"
            if stress_present
            else None,
        ),
        "construction_disclosure": _artifact_check(
            present=disclosure_status in {"available", "partial"},
            source=f"disclosure_status={disclosure_status}",
            detail=disclosure_status,
        ),
        "optimizer_methodology": _artifact_check(
            present=has_methodology,
            required_for_fair_comparison=role in {"optimizer_candidate", "robust_candidate"},
            source=(
                str(methodology.get("source"))
                if has_methodology and isinstance(methodology, dict)
                else None
            ),
        ),
        "optimizer_quality": _artifact_check(
            present=bool(quality),
            source=str(quality.get("source")) if quality.get("source") else None,
            detail=str(quality_status),
        ),
        "freshness": _freshness_check(
            factory_step=factory_step,
            warnings=warnings,
            snap_10y=snap_10y,
            expected_analysis_end=expected_analysis_end,
        ),
    }

    optional_checks = {
        "portfolio_xray": _artifact_check(
            present=(folder / "portfolio_xray.json").is_file(),
            required_for_fair_comparison=False,
            source="portfolio_xray.json"
            if (folder / "portfolio_xray.json").is_file()
            else None,
        ),
    }

    gaps: list[str] = []
    for key, check in checks.items():
        if check.get("required_for_fair_comparison", True) and not check.get("present"):
            gaps.append(key)
    if role in {"optimizer_candidate", "robust_candidate"} and not has_methodology:
        if "optimizer_methodology" not in gaps:
            gaps.append("optimizer_methodology")
    if quality_family == "unknown" and "optimizer_quality" not in gaps:
        gaps.append("optimizer_quality")

    fair_comparison_ready = (
        comparison_status == "available"
        and quality_family == "clean"
        and checks["weights"]["present"]
        and checks["snapshot_10y"]["present"]
        and checks["stress_summary"]["present"]
        and checks["construction_disclosure"]["present"]
        and checks["freshness"]["present"]
        and disclosure_status == "available"
        and has_methodology
    )

    overall = _overall_readiness_status(
        comparison_status=comparison_status,
        quality_family=quality_family,
        checks=checks,
        gaps=gaps,
        fair_comparison_ready=fair_comparison_ready,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "role": role,
        "overall_status": overall,
        "comparison_row_status": comparison_status,
        "unavailable_reason": unavailable_reason,
        "fair_comparison_ready": fair_comparison_ready,
        "required_checks": checks,
        "optional_checks": optional_checks,
        "gaps": gaps,
        "optimization_quality_status": quality_status,
        "optimization_quality_family": quality_family,
    }


FAVORING_OPTIMIZER_ROLES = frozenset({"optimizer_candidate", "robust_candidate"})


def is_optimizer_backed_for_favoring(cand: dict[str, Any]) -> bool:
    """True when selection must enforce fair-comparison readiness before favoring."""
    return cand.get("role") in FAVORING_OPTIMIZER_ROLES


def fair_comparison_ready_from_candidate(cand: dict[str, Any]) -> bool:
    disclosure = cand.get("construction_disclosure") or {}
    readiness = disclosure.get("optimization_readiness") or {}
    return readiness.get("fair_comparison_ready") is True


def candidate_eligible_for_favoring(cand: dict[str, Any]) -> bool:
    """Whether a row may become the favored selection target (Phase 17 RM-1022)."""
    if cand.get("status") != "available":
        return False
    if is_optimizer_backed_for_favoring(cand):
        return fair_comparison_ready_from_candidate(cand)
    return True


def favoring_ineligibility_reason(cand: dict[str, Any]) -> str | None:
    """Machine reason when candidate_eligible_for_favoring is false; None when eligible."""
    status = cand.get("status")
    if status == "unavailable":
        return "unavailable"
    if status == "degraded":
        return "degraded_excluded_from_favoring"
    if status != "available":
        return "status_not_available"
    if is_optimizer_backed_for_favoring(cand) and not fair_comparison_ready_from_candidate(cand):
        return "optimizer_not_fair_comparison_ready"
    return None
