"""
Package-level trust disclosure for Blocks 8–10 (comparison → selection → package).

Phase 17 Session 09 (RM-1028): surfaces partial menus and degraded optimizer rows so
decision_package summaries cannot be read as a full product-menu optimizer shootout.
"""

from __future__ import annotations

from typing import Any

from src.optimization_readiness import (
    FAVORING_OPTIMIZER_ROLES,
    fair_comparison_ready_from_candidate,
    is_optimizer_backed_for_favoring,
)

SCHEMA_VERSION = "package_truthfulness_v1"


def _candidate_rows(comparison: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not comparison:
        return []
    rows = comparison.get("candidates")
    return rows if isinstance(rows, list) else []


def summarize_package_truthfulness(comparison: dict[str, Any] | None) -> dict[str, Any]:
    """Machine-readable trust context for decision_package_summary.json."""
    menu = (comparison or {}).get("candidate_menu") or {}
    rows = _candidate_rows(comparison)

    degraded_optimizers = [
        c
        for c in rows
        if c.get("status") == "degraded" and is_optimizer_backed_for_favoring(c)
    ]
    fair_ready_optimizers = [
        c
        for c in rows
        if is_optimizer_backed_for_favoring(c) and fair_comparison_ready_from_candidate(c)
    ]
    not_fair_optimizers = [
        c
        for c in rows
        if is_optimizer_backed_for_favoring(c) and not fair_comparison_ready_from_candidate(c)
    ]

    is_partial = bool(menu.get("is_partial_menu"))
    review_mode = menu.get("review_mode") or menu.get("intended_menu_profile_id")
    product_profile = menu.get("product_menu_profile_id")
    intended_profile = menu.get("intended_menu_profile_id")
    intended_scored = menu.get("intended_menu_scored_count")
    product_size = menu.get("product_menu_size")

    implies_full_shootout = not is_partial and product_profile == "default_v1"
    if is_partial or (review_mode == "core" and product_profile == "default_v1"):
        implies_full_shootout = False

    user_lines: list[str] = []
    if is_partial:
        user_lines.append(
            "This run used a reduced candidate menu; rankings are not a full product-menu "
            "optimizer comparison."
        )
    if degraded_optimizers:
        user_lines.append(
            f"{len(degraded_optimizers)} optimizer row(s) are degraded and appear for "
            "diagnostics only — they cannot become the favored profile."
        )
    if is_partial and product_size and intended_scored is not None:
        user_lines.append(
            f"Intended menu scored {intended_scored} of {product_size} product-reference candidates."
        )
    execution = menu.get("factory_execution_summary") or {}
    if isinstance(execution, dict):
        reused = int(
            execution.get("reused_existing")
            if execution.get("reused_existing") is not None
            else execution.get("reused_existing_snapshot")
            or 0
        )
        resumed = int(execution.get("resumed_from_manifest") or 0)
        invoked = int(execution.get("builder_invoked") or 0)
        build_steps = int(execution.get("build_steps_executed") or invoked)
        in_process = int(execution.get("in_process_build_steps") or 0)
        if reused or resumed:
            user_lines.append(
                f"Factory evidence: {build_steps} build step(s) executed "
                f"({invoked} builder(s) invoked, {in_process} in-process), "
                f"{reused} existing artifact step(s) reused, and {resumed} step(s) "
                "resumed from manifest."
            )
        elif execution.get("no_skip_existing_requested"):
            user_lines.append(
                f"Factory evidence: --no-skip-existing requested and {build_steps} "
                f"build step(s) executed ({invoked} builder(s) invoked, "
                f"{in_process} in-process)."
            )

    degraded_detail = [
        {
            "candidate_id": c.get("candidate_id"),
            "display_name": c.get("display_name") or c.get("candidate_id"),
            "role": c.get("role"),
        }
        for c in degraded_optimizers
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "review_mode": review_mode,
        "intended_menu_profile_id": intended_profile,
        "product_menu_profile_id": product_profile,
        "is_partial_menu": is_partial,
        "partial_menu_reason": menu.get("partial_menu_reason"),
        "implies_full_product_menu_shootout": implies_full_shootout,
        "degraded_optimizer_count": len(degraded_optimizers),
        "degraded_optimizers": degraded_detail,
        "fair_ready_optimizer_count": len(fair_ready_optimizers),
        "optimizer_not_fair_ready_count": len(not_fair_optimizers),
        "user_summary_lines": user_lines,
    }


def build_review_scope_banner_lines(
    comparison: dict[str, Any] | None,
    *,
    truth: dict[str, Any] | None = None,
) -> list[str]:
    """Plain-English banner placed at the top of decision_package_summary (read first)."""
    truth = truth or summarize_package_truthfulness(comparison)
    if not comparison:
        return []

    lines: list[str] = ["Review scope (read first)", "-" * 40]
    review_mode = truth.get("review_mode")
    if review_mode:
        lines.append(f"  Review mode: {review_mode}.")

    if truth.get("is_partial_menu"):
        reason = truth.get("partial_menu_reason") or "incomplete intended menu"
        intended = truth.get("intended_menu_profile_id") or "—"
        product = truth.get("product_menu_profile_id") or "—"
        lines.append(
            f"  Partial menu ({reason}): intended profile {intended} "
            f"vs product reference {product}."
        )
        lines.append(
            "  Rankings and selection apply only to scored candidates in the intended menu, "
            "not a complete product optimizer shootout."
        )
    elif truth.get("implies_full_product_menu_shootout") is False:
        lines.append(
            "  This package does not represent a complete default_v1 optimizer shootout."
        )

    degraded = truth.get("degraded_optimizers") or []
    if degraded:
        names = ", ".join(
            str(d.get("display_name") or d.get("candidate_id") or "—") for d in degraded
        )
        lines.append(
            f"  Degraded optimizer rows ({len(degraded)}): {names} — "
            "diagnostic rankings only; not eligible for favoring."
        )

    fair_n = truth.get("fair_ready_optimizer_count")
    if fair_n is not None and fair_n == 0 and any(
        c.get("role") in FAVORING_OPTIMIZER_ROLES for c in _candidate_rows(comparison)
    ):
        lines.append(
            "  No optimizer row is fair-comparison-ready; do not treat optimizer rankings "
            "as a clean shootout winner."
        )

    for note in truth.get("user_summary_lines") or []:
        if note not in lines:
            lines.append(f"  {note}")

    if len(lines) <= 2:
        return []
    return lines


def degraded_optimizer_detail_lines(comparison: dict[str, Any] | None) -> list[str]:
    """Optional lines under Comparison highlights for degraded optimizer rows."""
    truth = summarize_package_truthfulness(comparison)
    degraded = truth.get("degraded_optimizers") or []
    if not degraded:
        return []
    out = ["  Degraded optimizer rows (diagnostic only, not favored):"]
    for row in degraded:
        out.append(f"    {row.get('display_name') or row.get('candidate_id')}")
    return out


__all__ = [
    "SCHEMA_VERSION",
    "build_review_scope_banner_lines",
    "degraded_optimizer_detail_lines",
    "summarize_package_truthfulness",
]
