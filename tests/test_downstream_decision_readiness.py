"""Unit tests for downstream_decision_readiness guards (Phase 17 RM-1027)."""

from __future__ import annotations

from src.downstream_decision_readiness import (
    SCHEMA_VERSION,
    build_downstream_readiness,
    candidate_eligible_for_diagnostic_backtest,
    candidate_eligible_for_fair_backtest_compare,
    may_load_candidate_stress_report,
    stress_report_ineligibility_reason,
)


def _cand(
    *,
    status: str = "available",
    role: str = "benchmark_candidate",
    fair_ready: bool = True,
) -> dict:
    out: dict = {"candidate_id": "x", "status": status, "role": role}
    if role in ("optimizer_candidate", "robust_candidate"):
        out["construction_disclosure"] = {
            "optimization_readiness": {"fair_comparison_ready": fair_ready},
        }
    return out


def test_fair_backtest_requires_available_fair_ready_optimizer() -> None:
    assert candidate_eligible_for_fair_backtest_compare(_cand(role="benchmark_candidate")) is True
    assert (
        candidate_eligible_for_fair_backtest_compare(
            _cand(role="optimizer_candidate", fair_ready=True)
        )
        is True
    )
    assert (
        candidate_eligible_for_fair_backtest_compare(
            _cand(role="optimizer_candidate", fair_ready=False)
        )
        is False
    )
    assert (
        candidate_eligible_for_fair_backtest_compare(
            _cand(status="degraded", role="optimizer_candidate", fair_ready=False)
        )
        is False
    )


def test_diagnostic_backtest_allows_degraded() -> None:
    assert candidate_eligible_for_diagnostic_backtest(_cand(status="degraded")) is True
    assert candidate_eligible_for_diagnostic_backtest(_cand(status="unavailable")) is False


def test_stress_report_blocked_for_degraded_optimizer() -> None:
    degraded_opt = _cand(status="degraded", role="optimizer_candidate", fair_ready=False)
    assert may_load_candidate_stress_report(degraded_opt) is False
    assert (
        stress_report_ineligibility_reason(degraded_opt)
        == "degraded_optimizer_stress_comparison_embed_only"
    )
    assert may_load_candidate_stress_report(_cand(status="degraded", role="benchmark_candidate"))


def test_build_downstream_readiness_block() -> None:
    block = build_downstream_readiness(
        _cand(status="degraded", role="optimizer_candidate", fair_ready=False)
    )
    assert block["schema_version"] == SCHEMA_VERSION
    assert block["diagnostic_backtest_allowed"] is True
    assert block["fair_backtest_compare_allowed"] is False
    assert block["stress_report_load_allowed"] is False
