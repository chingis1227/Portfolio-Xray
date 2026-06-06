from __future__ import annotations

from pathlib import Path
from typing import Any

from src.portfolio_alternatives_builder import (
    PortfolioAlternativeRequest,
    build_builder_prefill_from_launchpad_card,
    build_portfolio_alternative_plan,
)


DECISION_BOUNDARY = (
    "This is not a rebalance recommendation. Actual rebalance decision is made "
    "only after Current vs Candidate Comparison and Decision Verdict."
)


def _launchpad_card(
    *,
    diagnosis_id: str,
    goal: str,
    methods: list[dict[str, Any]],
    card_type: str = "targeted_hypothesis_test",
    launch_status: str = "hypothesis_test",
    **overrides: Any,
) -> dict[str, Any]:
    card: dict[str, Any] = {
        "card_id": f"launchpad_01_{diagnosis_id}",
        "goal": goal,
        "source_diagnosis_id": diagnosis_id,
        "source_problem_id": diagnosis_id,
        "hypothesis_to_test": f"Test whether the Builder setup addresses {diagnosis_id}.",
        "card_type": card_type,
        "launch_status": launch_status,
        "suggested_methods": methods,
        "success_criteria": ["Improve the diagnosed risk without hiding tradeoffs."],
        "tradeoff_to_watch": "Risk improvement vs turnover and opportunity cost.",
        "when_to_skip": "Skip when the diagnosis no longer applies.",
        "is_rebalance_recommendation": False,
        "decision_boundary": DECISION_BOUNDARY,
    }
    if methods:
        card["default_method"] = methods[0]["candidate_method_id"]
    card.update(overrides)
    return card


def _method(method_id: str, role: str = "targeted_hypothesis") -> dict[str, str]:
    return {"candidate_method_id": method_id, "method_role": role}


def test_weak_crisis_resilience_opens_targeted_crisis_resilience_setup() -> None:
    prefill = build_builder_prefill_from_launchpad_card(
        _launchpad_card(
            diagnosis_id="weak_crisis_resilience",
            goal="Improve crisis resilience",
            methods=[
                _method("minimum_cvar"),
                _method("maximum_diversification"),
                _method("minimum_variance"),
            ],
        )
    )

    assert prefill["builder_mode"] == "guided_from_diagnosis"
    assert prefill["source_diagnosis_id"] == "weak_crisis_resilience"
    assert prefill["suggested_method"] == "minimum_cvar"
    assert set(prefill["alternative_methods"]) == {
        "maximum_diversification",
        "minimum_variance",
    }
    assert prefill["method_role"] == "targeted_candidate_method"
    assert prefill["candidate_generation_allowed"] is True
    assert prefill["is_rebalance_recommendation"] is False
    assert "Decision Verdict" in prefill["decision_boundary"]


def test_poor_diversification_opens_diversification_setup() -> None:
    prefill = build_builder_prefill_from_launchpad_card(
        _launchpad_card(
            diagnosis_id="poor_diversification",
            goal="Improve diversification",
            methods=[
                _method("risk_parity"),
                _method("maximum_diversification"),
                _method("risk_parity"),
            ],
        )
    )

    candidate_methods = {prefill["suggested_method"], *prefill["alternative_methods"]}
    assert prefill["source_diagnosis_id"] == "poor_diversification"
    assert prefill["builder_mode"] == "guided_from_diagnosis"
    assert candidate_methods & {"risk_parity", "risk_parity"}
    assert prefill["method_role"] == "targeted_candidate_method"
    assert prefill["candidate_generation_allowed"] is True


def test_high_concentration_exposes_concentration_constraints() -> None:
    prefill = build_builder_prefill_from_launchpad_card(
        _launchpad_card(
            diagnosis_id="high_concentration",
            goal="Reduce concentration",
            methods=[
                _method("equal_weight"),
                _method("risk_parity"),
                _method("maximum_diversification"),
            ],
            constraint_preset="concentration_cap",
            max_asset_weight=0.15,
        )
    )

    assert prefill["source_diagnosis_id"] == "high_concentration"
    assert prefill["suggested_method"] == "equal_weight"
    assert prefill["constraint_preset"] == "concentration_cap"
    assert prefill["max_asset_weight"] == 0.15
    assert prefill["candidate_generation_allowed"] is True


def test_mixed_evidence_no_action_opens_reference_comparison() -> None:
    prefill = build_builder_prefill_from_launchpad_card(
        _launchpad_card(
            diagnosis_id="mixed_evidence_no_action",
            goal="Compare against simple references",
            methods=[
                _method("equal_weight", role="reference_benchmark"),
                _method("risk_parity", role="reference_benchmark"),
            ],
            card_type="reference_benchmark_test",
            launch_status="reference_test",
        )
    )

    assert prefill["source_diagnosis_id"] == "mixed_evidence_no_action"
    assert prefill["suggested_method"] == "equal_weight"
    assert prefill["alternative_methods"] == ["risk_parity"]
    assert prefill["method_role"] == "reference_benchmark"
    assert prefill["candidate_generation_allowed"] is True
    assert prefill["is_rebalance_recommendation"] is False


def test_current_portfolio_acceptable_keeps_monitoring_visible() -> None:
    prefill = build_builder_prefill_from_launchpad_card(
        _launchpad_card(
            diagnosis_id="current_portfolio_acceptable",
            goal="Keep current portfolio and monitor",
            methods=[],
            card_type="monitor_or_data_step",
            launch_status="monitor_or_resolve_data",
            success_criteria=["Monitor diagnostics and re-open tests only if evidence changes."],
        )
    )

    assert prefill["source_diagnosis_id"] == "current_portfolio_acceptable"
    assert prefill["builder_mode"] == "monitor_only"
    assert prefill["suggested_method"] is None
    assert prefill["alternative_methods"] == []
    assert prefill["success_criteria"] == [
        "Monitor diagnostics and re-open tests only if evidence changes."
    ]
    assert prefill["candidate_generation_allowed"] is False
    assert "monitor" in prefill["launch_status"]


def test_evidence_insufficient_data_quality_blocks_candidate_generation() -> None:
    prefill = build_builder_prefill_from_launchpad_card(
        _launchpad_card(
            diagnosis_id="evidence_insufficient_data_quality",
            goal="Review data quality",
            methods=[],
            card_type="monitor_or_data_step",
            launch_status="monitor_or_resolve_data",
            hypothesis_to_test="Resolve data quality before testing candidates.",
        )
    )

    assert prefill["source_diagnosis_id"] == "evidence_insufficient_data_quality"
    assert prefill["builder_mode"] == "blocked_data_quality"
    assert prefill["suggested_method"] is None
    assert prefill["method_role"] is None
    assert prefill["candidate_generation_allowed"] is False
    assert prefill["is_rebalance_recommendation"] is False


def test_manual_custom_builder_request_still_works_without_launchpad_card(
    tmp_path: Path,
) -> None:
    plan = build_portfolio_alternative_plan(
        PortfolioAlternativeRequest(
            candidate_method_id="risk_parity",
            goal="Manual diversification reference",
            max_asset_weight=0.2,
        ),
        project_root=tmp_path,
        python_executable="python-test",
    )

    assert plan.candidate_method_id == "risk_parity"
    assert plan.candidate_id == "risk_parity"
    assert plan.command[:4] == (
        "python-test",
        str(tmp_path / "run_candidate_factory.py"),
        "--candidates",
        "risk_parity",
    )
    assert plan.provenance["source"] == "portfolio_alternatives_builder_v1"
    assert plan.warnings == ("request_parameters_recorded_not_applied_v1",)
