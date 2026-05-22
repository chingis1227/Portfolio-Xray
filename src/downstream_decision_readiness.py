"""Downstream eligibility guards for Blocks 6–7 (backtest evidence, candidate stress).

Read-only helpers consumed by health score, robustness scorecard, and related modules.
Does not change comparison ranking, optimizer weights, or selection favoring rules
(see optimization_readiness.candidate_eligible_for_favoring).
"""

from __future__ import annotations

from typing import Any

from src.optimization_readiness import (
    fair_comparison_ready_from_candidate,
    is_optimizer_backed_for_favoring,
)

SCHEMA_VERSION = "downstream_decision_readiness_v1"

BACKTEST_DIAGNOSTIC_STATUSES = frozenset({"available", "degraded"})
STRESS_DIAGNOSTIC_STATUSES = frozenset({"available", "degraded"})


def candidate_eligible_for_diagnostic_backtest(cand: dict[str, Any]) -> bool:
    """Whether Block 6 may surface snapshot/comparison metrics for diagnostic display."""
    return cand.get("status") in BACKTEST_DIAGNOSTIC_STATUSES


def candidate_eligible_for_fair_backtest_compare(cand: dict[str, Any]) -> bool:
    """Whether backtest/metrics evidence may be used in fair cross-candidate comparison."""
    if cand.get("status") != "available":
        return False
    if is_optimizer_backed_for_favoring(cand):
        return fair_comparison_ready_from_candidate(cand)
    return True


def may_load_candidate_stress_report(cand: dict[str, Any]) -> bool:
    """Whether Block 7 may open ``artifact_root/stress_report.json`` beyond comparison embed."""
    status = cand.get("status")
    if status == "unavailable":
        return False
    if status == "degraded" and is_optimizer_backed_for_favoring(cand):
        return False
    return status in STRESS_DIAGNOSTIC_STATUSES


def backtest_ineligibility_reason(cand: dict[str, Any], *, fair_compare: bool = False) -> str | None:
    """Machine reason when backtest evidence must not be used; None when allowed."""
    if fair_compare:
        if candidate_eligible_for_fair_backtest_compare(cand):
            return None
        status = cand.get("status")
        if status == "unavailable":
            return "unavailable_no_backtest_evidence"
        if status == "degraded":
            return "degraded_backtest_diagnostic_only"
        if is_optimizer_backed_for_favoring(cand):
            return "optimizer_not_fair_comparison_ready"
        return "status_not_available"
    if candidate_eligible_for_diagnostic_backtest(cand):
        return None
    return "unavailable_no_backtest_evidence"


def stress_report_ineligibility_reason(cand: dict[str, Any]) -> str | None:
    """Machine reason when stress_report.json must not be loaded; None when allowed."""
    if may_load_candidate_stress_report(cand):
        return None
    status = cand.get("status")
    if status == "unavailable":
        return "unavailable_no_stress_artifact"
    if status == "degraded" and is_optimizer_backed_for_favoring(cand):
        return "degraded_optimizer_stress_comparison_embed_only"
    return "stress_artifact_blocked"


def build_downstream_readiness(cand: dict[str, Any]) -> dict[str, Any]:
    """Per-row downstream readiness block for comparison or diagnostics."""
    fair_backtest = candidate_eligible_for_fair_backtest_compare(cand)
    diag_backtest = candidate_eligible_for_diagnostic_backtest(cand)
    stress_load = may_load_candidate_stress_report(cand)
    return {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_backtest_allowed": diag_backtest,
        "fair_backtest_compare_allowed": fair_backtest,
        "stress_report_load_allowed": stress_load,
        "backtest_fair_ineligibility": backtest_ineligibility_reason(cand, fair_compare=True),
        "backtest_diagnostic_ineligibility": backtest_ineligibility_reason(cand, fair_compare=False),
        "stress_report_ineligibility": stress_report_ineligibility_reason(cand),
    }
