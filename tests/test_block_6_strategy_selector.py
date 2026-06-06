from __future__ import annotations

import pytest

from scripts.core_mvp_validation_contract import (
    builder_prefill_product_contract_violations,
)
from src.portfolio_alternatives_builder import (
    BUILDER_PREFILL_PROHIBITED_FIELDS,
    launchpad_card_to_builder_prefill,
    select_builder_strategy,
)


DECISION_BOUNDARY = (
    "This is not a rebalance recommendation. Actual rebalance decision is made "
    "only after Current vs Candidate Comparison and Decision Verdict."
)


@pytest.mark.parametrize(
    ("goal", "expected_goal_id", "expected_method"),
    [
        ("improve_crisis_resilience", "improve_crisis_resilience", "minimum_cvar"),
        ("Improve crisis resilience", "improve_crisis_resilience", "minimum_cvar"),
        ("improve_diversification", "improve_diversification", "risk_parity"),
        ("Reduce concentration", "reduce_concentration", "equal_weight"),
        ("reduce_volatility", "reduce_volatility", "minimum_variance"),
        ("compare_simple_benchmark", "compare_simple_benchmark", "equal_weight"),
        ("Compare against simple benchmark", "compare_simple_benchmark", "equal_weight"),
    ],
)
def test_strategy_selector_maps_goal_to_guided_method(
    goal: str,
    expected_goal_id: str,
    expected_method: str,
) -> None:
    strategy = select_builder_strategy(goal)

    assert strategy["goal_id"] == expected_goal_id
    assert strategy["original_suggested_method"] == expected_method
    assert strategy["selected_method"] == expected_method
    assert strategy["method_changed_by_user"] is False
    assert expected_method in strategy["guided_methods"]
    assert strategy["shows_raw_optimizer_menu"] is False
    assert strategy["is_rebalance_recommendation"] is False


def test_strategy_selector_adds_concentration_max_weight_hint() -> None:
    strategy = select_builder_strategy("reduce_concentration")

    assert strategy["selected_method"] == "equal_weight"
    assert strategy["constraint_preset"] == "custom"
    assert strategy["max_asset_weight"] == 0.15
    assert strategy["min_asset_weight"] == 0.0


def test_strategy_selector_preserves_user_changed_method() -> None:
    strategy = select_builder_strategy(
        "reduce_volatility",
        selected_method="risk_parity",
    )

    assert strategy["original_suggested_method"] == "minimum_variance"
    assert strategy["selected_method"] == "risk_parity"
    assert strategy["method_changed_by_user"] is True
    assert "minimum_variance" in strategy["alternative_methods"]
    assert "selected_method_outside_guided_goal_methods" not in strategy["warnings"]


def test_strategy_selector_preserves_out_of_guided_menu_user_method_without_validation() -> None:
    strategy = select_builder_strategy(
        "reduce_volatility",
        selected_method="maximum_diversification",
    )

    assert strategy["original_suggested_method"] == "minimum_variance"
    assert strategy["selected_method"] == "maximum_diversification"
    assert strategy["method_changed_by_user"] is True
    assert "selected_method_outside_guided_goal_methods" in strategy["warnings"]


def test_strategy_selector_preserves_reference_benchmark_boundary() -> None:
    strategy = select_builder_strategy(
        "Compare against simple references",
        card_type="reference_benchmark_test",
        method_role="reference_benchmark",
    )

    assert strategy["goal_id"] == "compare_simple_benchmark"
    assert strategy["selected_method"] == "equal_weight"
    assert strategy["guided_methods"] == ["equal_weight", "risk_parity"]
    assert strategy["method_role"] == "reference_benchmark"
    assert strategy["constraint_preset"] == "basic_reference"
    assert strategy["is_rebalance_recommendation"] is False


def test_strategy_selector_unknown_goal_does_not_show_raw_optimizer_menu() -> None:
    strategy = select_builder_strategy("Review data quality")

    assert strategy["goal_id"] is None
    assert strategy["original_suggested_method"] is None
    assert strategy["selected_method"] is None
    assert strategy["guided_methods"] == []
    assert strategy["shows_raw_optimizer_menu"] is False
    assert strategy["warnings"] == ["unknown_goal_no_guided_method"]


def test_launchpad_prefill_uses_strategy_selector_without_candidate_outputs() -> None:
    prefill = launchpad_card_to_builder_prefill(
        {
            "card_id": "launchpad_01_improve_diversification",
            "goal": "Improve diversification",
            "source_problem_id": "poor_diversification",
            "source_diagnosis_id": "poor_diversification",
            "hypothesis_to_test": "Test whether risk-balanced diversification improves.",
            "default_method": "risk_parity",
            "suggested_methods": [
                {
                    "candidate_method_id": "risk_parity",
                    "method_role": "targeted_hypothesis",
                },
                {
                    "candidate_method_id": "risk_parity",
                    "method_role": "targeted_hypothesis",
                },
                {
                    "candidate_method_id": "maximum_diversification",
                    "method_role": "targeted_hypothesis",
                },
            ],
            "success_criteria": ["Lower top-3 risk contribution share."],
            "tradeoff_to_watch": "Risk balance versus turnover.",
            "when_to_skip": "Skip if diversification diagnosis no longer applies.",
            "card_type": "targeted_hypothesis_test",
            "launch_status": "hypothesis_test",
            "is_rebalance_recommendation": False,
            "decision_boundary": DECISION_BOUNDARY,
        }
    )

    assert prefill["suggested_method"] == "risk_parity"
    assert prefill["original_suggested_method"] == "risk_parity"
    assert prefill["selected_method"] == "risk_parity"
    assert prefill["method_changed_by_user"] is False
    assert prefill["strategy_selector"]["shows_raw_optimizer_menu"] is False
    assert BUILDER_PREFILL_PROHIBITED_FIELDS.isdisjoint(prefill)
    assert not builder_prefill_product_contract_violations(prefill)
