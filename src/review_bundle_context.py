"""Review bundle disclosure: single fingerprint and mode/subject consistency (RM-1026)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

REVIEW_BUNDLE_CONTEXT_VERSION = "review_bundle_context_v1"

_EXPECTED_ROLE_BY_SUBJECT_TYPE: dict[str, frozenset[str]] = {
    "current_portfolio": frozenset({"user_current_portfolio"}),
    "model_portfolio": frozenset({"model_portfolio"}),
    "universe_baseline": frozenset(
        {"equal_weight_initial_baseline", "model_portfolio", "user_current_portfolio"}
    ),
}


def assess_mode_subject_consistency(
    *,
    source_analysis_mode: str | None,
    analysis_subject_type: str | None,
    product_input_case: str | None = None,
    portfolio_role: str | None = None,
) -> dict[str, Any]:
    """
    Detect confusing legacy analysis_mode labels vs resolved analysis_subject.

    Portfolio-first runs often keep config analysis_mode=optimize_from_universe while
    diagnosing an explicit current_portfolio subject; that is disclosed, not blocked.
    """
    mode = str(source_analysis_mode or "optimize_from_universe").strip().lower()
    subject_type = str(analysis_subject_type or "").strip().lower() or None
    role = str(portfolio_role or "").strip() or None
    product_case = str(product_input_case or "").strip() or None

    mismatch_codes: list[str] = []
    notices: list[str] = []

    if subject_type == "current_portfolio" and mode == "optimize_from_universe":
        notices.append(
            "Config analysis_mode remains optimize_from_universe (legacy default); "
            "this review diagnoses the explicit current_portfolio analysis_subject, "
            "not a policy optimizer release."
        )
    if mode == "analyze_current_weights" and subject_type == "model_portfolio":
        mismatch_codes.append("MODE_SUBJECT_ANALYZE_CURRENT_VS_MODEL")
    if mode == "analyze_current_weights" and subject_type == "universe_baseline":
        mismatch_codes.append("MODE_SUBJECT_ANALYZE_CURRENT_VS_BASELINE")
    if mode == "optimize_from_universe" and subject_type == "universe_baseline":
        if product_case not in (None, "", "universe_only", "legacy_or_unknown"):
            mismatch_codes.append("MODE_SUBJECT_OPTIMIZE_UNIVERSE_VS_PRODUCT_CASE")
    if subject_type and role:
        expected = _EXPECTED_ROLE_BY_SUBJECT_TYPE.get(subject_type)
        if expected is not None and role not in expected:
            mismatch_codes.append("ROLE_SUBJECT_TYPE_MISMATCH")

    is_consistent = len(mismatch_codes) == 0
    interpretation_parts: list[str] = []
    if subject_type:
        interpretation_parts.append(f"analysis_subject.type={subject_type}")
    if mode:
        interpretation_parts.append(f"config analysis_mode={mode}")
    if role:
        interpretation_parts.append(f"analysis_portfolio.portfolio_role={role}")
    if notices:
        interpretation_parts.append(notices[0])
    if mismatch_codes:
        interpretation_parts.append(
            "Mode/subject labels disagree; interpret comparison baseline from analysis_subject, "
            "not from analysis_mode alone."
        )

    return {
        "source_analysis_mode": mode,
        "analysis_subject_type": subject_type,
        "product_input_case": product_case,
        "portfolio_role": role,
        "is_consistent": is_consistent,
        "mismatch_codes": mismatch_codes,
        "informational_notices": notices,
        "interpretation_en": " ".join(interpretation_parts).strip(),
    }


def _canonical_fingerprint_payload(parts: dict[str, Any]) -> dict[str, Any]:
    """Stable keys for review_bundle_fingerprint (diagnostic correlation only)."""
    return {
        "analysis_end": parts.get("analysis_end"),
        "comparison_config_fingerprint": parts.get("comparison_config_fingerprint"),
        "analysis_subject_id": parts.get("analysis_subject_id"),
        "analysis_subject_type": parts.get("analysis_subject_type"),
        "subject_snapshot_fingerprint": parts.get("subject_snapshot_fingerprint"),
        "factory_profile_id": parts.get("factory_profile_id"),
        "factory_config_fingerprint": parts.get("factory_config_fingerprint"),
        "review_mode": parts.get("review_mode"),
    }


def compute_review_bundle_fingerprint(parts: dict[str, Any]) -> str:
    payload = _canonical_fingerprint_payload(parts)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def build_review_bundle_user_summary_lines(
    bundle: dict[str, Any],
    *,
    mode_subject: dict[str, Any] | None = None,
) -> list[str]:
    lines: list[str] = []
    fp = bundle.get("review_bundle_fingerprint")
    if fp:
        lines.append(
            f"Review bundle fingerprint {str(fp)[:16]}... links subject, factory, and comparison "
            "artifacts for this run (see review_bundle_context in candidate_comparison.json)."
        )
    alignment = bundle.get("fingerprint_alignment") or {}
    if alignment.get("all_aligned") is False:
        mismatches = alignment.get("mismatch_reasons") or []
        if mismatches:
            lines.append(
                "Review bundle alignment: "
                + "; ".join(str(m) for m in mismatches[:3])
                + "."
            )
    ms = mode_subject or bundle.get("mode_subject_consistency") or {}
    for notice in ms.get("informational_notices") or []:
        if notice:
            lines.append(str(notice))
    for code in ms.get("mismatch_codes") or []:
        if code == "MODE_SUBJECT_ANALYZE_CURRENT_VS_MODEL":
            lines.append(
                "Input mismatch: analysis_mode is analyze_current_weights but "
                "analysis_subject is model_portfolio; confirm which portfolio this run diagnoses."
            )
        elif code == "ROLE_SUBJECT_TYPE_MISMATCH":
            lines.append(
                "Input mismatch: analysis_portfolio.portfolio_role does not match "
                "analysis_subject.type; use analysis_subject as the comparison baseline label."
            )
        else:
            lines.append(f"Input consistency flag: {code}.")
    return [line for line in lines if line][:6]


def build_review_bundle_context_v1(
    *,
    analysis_end: str | None,
    comparison_config_fingerprint: str | None,
    comparison_generated_at: str | None,
    comparison_rebuild_source: str | None,
    setup_summary: dict[str, Any],
    candidate_menu: dict[str, Any] | None,
    subject_artifacts: dict[str, Any] | None,
    factory_run: dict[str, Any] | None,
    factory_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """Assemble review_bundle_context_v1 for candidate_comparison.json."""
    menu = candidate_menu or {}
    factory_ctx = factory_context or {}
    subject = subject_artifacts or {}

    mode_subject = assess_mode_subject_consistency(
        source_analysis_mode=setup_summary.get("source_analysis_mode"),
        analysis_subject_type=setup_summary.get("analysis_subject_type"),
        product_input_case=setup_summary.get("product_input_case"),
        portfolio_role=setup_summary.get("portfolio_role"),
    )

    comparison_fp = comparison_config_fingerprint
    subject_snap_fp = subject.get("snapshot_config_fingerprint")
    factory_fp = (factory_run or {}).get("config_fingerprint")
    factory_profile = (factory_run or {}).get("factory_profile_id") or menu.get(
        "intended_menu_profile_id"
    )

    fingerprint_parts = {
        "analysis_end": analysis_end,
        "comparison_config_fingerprint": comparison_fp,
        "analysis_subject_id": setup_summary.get("analysis_subject_id"),
        "analysis_subject_type": setup_summary.get("analysis_subject_type"),
        "subject_snapshot_fingerprint": subject_snap_fp,
        "factory_profile_id": factory_profile,
        "factory_config_fingerprint": factory_fp if factory_ctx.get("steps_used") else None,
        "review_mode": menu.get("review_mode"),
    }
    review_bundle_fingerprint = compute_review_bundle_fingerprint(fingerprint_parts)

    mismatch_reasons: list[str] = []
    subject_vs_comparison = "unknown"
    if subject_snap_fp and comparison_fp:
        subject_vs_comparison = (
            "match" if str(subject_snap_fp) == str(comparison_fp) else "mismatch"
        )
        if subject_vs_comparison == "mismatch":
            mismatch_reasons.append(
                "subject snapshot candidate_config_fingerprint differs from comparison config_fingerprint"
            )

    factory_vs_comparison = "missing_factory"
    if factory_run and factory_fp and comparison_fp:
        if factory_ctx.get("steps_used"):
            factory_vs_comparison = (
                "match" if str(factory_fp) == str(comparison_fp) else "mismatch"
            )
            if factory_vs_comparison == "mismatch":
                mismatch_reasons.append("factory config_fingerprint differs from comparison")
        else:
            factory_vs_comparison = "not_authoritative"

    all_aligned = (
        subject_vs_comparison in ("match", "unknown")
        and factory_vs_comparison in ("match", "missing_factory", "not_authoritative")
        and mode_subject.get("is_consistent", True)
    )

    bundle: dict[str, Any] = {
        "version": REVIEW_BUNDLE_CONTEXT_VERSION,
        "review_bundle_fingerprint": review_bundle_fingerprint,
        "bundle_parts": {
            "analysis_subject": {
                "materialized": bool(subject.get("sidecar_present")),
                "artifact_root": subject.get("artifact_root"),
                "run_metadata_present": bool(subject.get("run_metadata_present")),
                "snapshot_config_fingerprint": subject_snap_fp,
                "analysis_subject_id": setup_summary.get("analysis_subject_id"),
                "analysis_subject_type": setup_summary.get("analysis_subject_type"),
            },
            "factory_run": {
                "present": bool(factory_run),
                "generated_at": (factory_run or {}).get("generated_at"),
                "factory_profile_id": factory_profile,
                "config_fingerprint": factory_fp,
                "factory_evidence_status": menu.get("factory_evidence_status"),
            },
            "comparison": {
                "generated_at": comparison_generated_at,
                "config_fingerprint": comparison_fp,
                "comparison_rebuild_source": comparison_rebuild_source,
                "review_mode": menu.get("review_mode"),
                "comparison_baseline_candidate_id": "analysis_subject",
            },
        },
        "fingerprint_alignment": {
            "subject_vs_comparison_config": subject_vs_comparison,
            "factory_vs_comparison_config": factory_vs_comparison,
            "all_aligned": all_aligned,
            "mismatch_reasons": mismatch_reasons,
        },
        "mode_subject_consistency": mode_subject,
    }
    bundle["user_summary_lines"] = build_review_bundle_user_summary_lines(
        bundle, mode_subject=mode_subject
    )
    return bundle


def mode_subject_summary_from_analysis_setup(
    analysis_setup: dict[str, Any],
) -> dict[str, Any]:
    """Project mode/subject consistency from a resolved analysis_setup document."""
    pi = analysis_setup.get("portfolio_input") or {}
    subject = analysis_setup.get("analysis_subject") or {}
    ap = analysis_setup.get("analysis_portfolio") or {}
    return assess_mode_subject_consistency(
        source_analysis_mode=pi.get("source_analysis_mode"),
        analysis_subject_type=subject.get("type"),
        product_input_case=pi.get("product_input_case"),
        portfolio_role=ap.get("portfolio_role"),
    )


def input_assumptions_review_summary_lines(
    analysis_setup: dict[str, Any],
) -> list[str]:
    """Short trust lines for input_assumptions.data_trust_signals (no filesystem)."""
    ms = mode_subject_summary_from_analysis_setup(analysis_setup)
    lines: list[str] = []
    for notice in ms.get("informational_notices") or []:
        lines.append(str(notice))
    for code in ms.get("mismatch_codes") or []:
        if code == "MODE_SUBJECT_ANALYZE_CURRENT_VS_MODEL":
            lines.append(
                "analysis_mode=analyze_current_weights conflicts with model_portfolio "
                "analysis_subject; verify the diagnosed portfolio."
            )
        elif code == "ROLE_SUBJECT_TYPE_MISMATCH":
            lines.append(
                "portfolio_role does not match analysis_subject.type; "
                "trust analysis_subject for portfolio-first interpretation."
            )
        else:
            lines.append(f"Input consistency: {code}.")
    return [line for line in lines if line][:4]


def merge_review_bundle_into_input_trust_lines(
    existing_lines: list[str],
    review_lines: list[str] | None,
    *,
    max_lines: int = 6,
) -> list[str]:
    merged = list(existing_lines or [])
    for line in review_lines or []:
        if line and line not in merged:
            merged.append(str(line))
    return [line for line in merged if line][:max_lines]


__all__ = [
    "REVIEW_BUNDLE_CONTEXT_VERSION",
    "assess_mode_subject_consistency",
    "build_review_bundle_context_v1",
    "build_review_bundle_user_summary_lines",
    "compute_review_bundle_fingerprint",
    "input_assumptions_review_summary_lines",
    "merge_review_bundle_into_input_trust_lines",
    "mode_subject_summary_from_analysis_setup",
]
