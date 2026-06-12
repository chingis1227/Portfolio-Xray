from __future__ import annotations

from typing import Any

from scripts.core_mvp_validation_contract import (
    builder_prefill_product_contract_violations,
)
from src.portfolio_alternatives_builder import (
    BUILDER_PREFILL_PROHIBITED_FIELDS,
    builder_prefill_contract_violations,
    launchpad_card_to_builder_prefill,
)


DECISION_BOUNDARY = (
    "This is not a rebalance recommendation. Actual rebalance decision is made "
    "only after Current vs Candidate Comparison and Decision Verdict."
)


def _method(
    method_id: str,
    *,
    role: str = "targeted_hypothesis",
    rationale: str = "Diagnosis-linked method rationale.",
) -> dict[str, str]:
    return {
        "candidate_method_id": method_id,
        "method_role": role,
        "rationale": rationale,
    }


def _launchpad_card(**overrides: Any) -> dict[str, Any]:
    card: dict[str, Any] = {
        "card_id": "launchpad_01_improve_crisis_resilience",
        "goal": "Improve crisis resilience",
        "source_problem_id": "weak_crisis_resilience",
        "source_diagnosis_id": "weak_crisis_resilience",
        "hypothesis_to_test": "Test whether stress loss improves without hiding tradeoffs.",
        "default_method": "minimum_cvar",
        "suggested_methods": [
            _method("minimum_cvar"),
            _method("maximum_diversification", rationale="Robustness cross-check."),
        ],
        "success_criteria": [
            "Lower severe-stress loss.",
            "Do not create an unexplained concentration increase.",
        ],
        "tradeoff_to_watch": "Stress protection versus expected return and turnover.",
        "when_to_skip": "Skip if the crisis-resilience diagnosis no longer applies.",
        "card_type": "targeted_hypothesis_test",
        "launch_status": "hypothesis_test",
        "is_rebalance_recommendation": False,
        "decision_boundary": DECISION_BOUNDARY,
        "constraint_preset": "balanced",
        "max_asset_weight": 0.25,
        "min_asset_weight": 0.0,
        "volatility_target": 0.12,
        "rebalancing_frequency": "quarterly",
        "transaction_cost_bps": 10,
    }
    card.update(overrides)
    return card


def test_launchpad_card_to_builder_prefill_preserves_session_02_handoff_fields() -> None:
    next_step = {
        "type": "candidate_hypothesis_test",
        "label": "Open Builder and test a crisis-resilience candidate.",
        "decision_boundary": DECISION_BOUNDARY,
    }

    prefill = launchpad_card_to_builder_prefill(
        _launchpad_card(),
        next_diagnostic_step=next_step,
    )

    assert prefill["source_diagnosis_id"] == "weak_crisis_resilience"
    assert prefill["source_problem_id"] == "weak_crisis_resilience"
    assert prefill["source_card_id"] == "launchpad_01_improve_crisis_resilience"
    assert prefill["hypothesis_to_test"] == (
        "Test whether stress loss improves without hiding tradeoffs."
    )
    assert prefill["goal"] == "Improve crisis resilience"
    assert prefill["suggested_method"] == "minimum_cvar"
    assert prefill["alternative_methods"] == ["maximum_diversification"]
    assert prefill["suggested_methods"] == _launchpad_card()["suggested_methods"]
    assert prefill["success_criteria"] == [
        "Lower severe-stress loss.",
        "Do not create an unexplained concentration increase.",
    ]
    assert prefill["tradeoff_to_watch"] == "Stress protection versus expected return and turnover."
    assert prefill["when_to_skip"] == "Skip if the crisis-resilience diagnosis no longer applies."
    assert prefill["decision_boundary"] == DECISION_BOUNDARY
    assert prefill["card_type"] == "targeted_hypothesis_test"
    assert prefill["launch_status"] == "hypothesis_test"
    assert prefill["method_role"] == "targeted_candidate_method"
    assert prefill["is_rebalance_recommendation"] is False
    assert prefill["next_diagnostic_step"] == next_step

    assert BUILDER_PREFILL_PROHIBITED_FIELDS.isdisjoint(prefill)
    assert not builder_prefill_contract_violations(prefill)
    assert not builder_prefill_product_contract_violations(prefill)


def test_launchpad_card_to_builder_prefill_preserves_reference_benchmark_boundary() -> None:
    prefill = launchpad_card_to_builder_prefill(
        _launchpad_card(
            card_id="launchpad_01_compare_against_simple_benchmark",
            goal="Compare against simple benchmark",
            source_problem_id="mixed_evidence_no_action",
            source_diagnosis_id="mixed_evidence_no_action",
            hypothesis_to_test="Test whether simple references clarify materiality.",
            default_method="equal_weight",
            suggested_methods=[
                _method("equal_weight", role="reference_benchmark"),
                _method("risk_parity", role="reference_benchmark"),
            ],
            success_criteria=["Create a transparent reference point."],
            card_type="reference_benchmark_test",
            launch_status="reference_test",
        )
    )

    assert prefill["suggested_method"] == "equal_weight"
    assert prefill["alternative_methods"] == ["risk_parity"]
    assert prefill["method_role"] == "reference_benchmark"
    assert prefill["candidate_generation_allowed"] is True
    assert prefill["is_rebalance_recommendation"] is False
    assert "Decision Verdict" in prefill["decision_boundary"]
    assert BUILDER_PREFILL_PROHIBITED_FIELDS.isdisjoint(prefill)
    assert not builder_prefill_product_contract_violations(prefill)


def test_launchpad_card_to_builder_prefill_blocks_data_quality_without_candidate_outputs() -> None:
    prefill = launchpad_card_to_builder_prefill(
        _launchpad_card(
            card_id="launchpad_01_evidence_insufficient_do_not_act_yet",
            goal="Review data quality",
            source_problem_id="evidence_insufficient_data_quality",
            source_diagnosis_id="evidence_insufficient_data_quality",
            hypothesis_to_test="Resolve data quality before testing candidates.",
            default_method=None,
            suggested_methods=[],
            success_criteria=["Resolve data-quality blockers."],
            card_type="monitor_or_data_step",
            launch_status="monitor_or_resolve_data",
        )
    )

    assert prefill["builder_mode"] == "blocked_data_quality"
    assert prefill["status"] == "blocked"
    assert prefill["suggested_method"] is None
    assert prefill["alternative_methods"] == []
    assert prefill["method_role"] is None
    assert prefill["candidate_generation_allowed"] is False
    assert prefill["is_rebalance_recommendation"] is False
    assert BUILDER_PREFILL_PROHIBITED_FIELDS.isdisjoint(prefill)
    assert not builder_prefill_contract_violations(prefill)
    assert not builder_prefill_product_contract_violations(prefill)


def test_client_fit_targets_are_builder_success_criteria_not_optimizer_mandates() -> None:
    client_fit_check = {
        "schema_version": "client_fit_check_v1",
        "client_fit_status": "watch",
        "profile": {
            "preset_id": "balanced",
            "source_quality": "high",
            "horizon_years": 7,
            "target_return_range": {"min": 0.05, "max": 0.07},
            "target_vol_range": {"min": 0.07, "max": 0.10},
            "target_max_drawdown_pct": -0.20,
        },
    }

    prefill = launchpad_card_to_builder_prefill(
        _launchpad_card(),
        client_fit_check=client_fit_check,
    )

    assert "Compare return against the stated Client Fit target range." in prefill["success_criteria"]
    assert "Compare volatility against the stated Client Fit comfort range." in prefill["success_criteria"]
    assert prefill["client_fit_test_criteria"]["client_fit_status"] == "watch"
    assert {
        row["usage"] for row in prefill["client_fit_test_criteria"]["target_rows"]
    } <= {"display_test_criterion", "display_context_only"}
    assert "client_fit" not in prefill["parameters"] if "parameters" in prefill else True
    assert "optimizer objectives" in prefill["client_fit_optimizer_boundary"]
    assert not builder_prefill_product_contract_violations(prefill)
