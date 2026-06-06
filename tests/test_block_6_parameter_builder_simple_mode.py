from __future__ import annotations

import pytest

from src.portfolio_alternatives_builder import (
    SIMPLE_BUILDER_ALLOWED_PRESETS,
    SIMPLE_BUILDER_EDITABLE_FIELDS,
    PortfolioAlternativesBuilderError,
    build_simple_builder_parameters,
    launchpad_card_to_builder_prefill,
)


DECISION_BOUNDARY = (
    "This is not a rebalance recommendation. Actual rebalance decision is made "
    "only after Current vs Candidate Comparison and Decision Verdict."
)


def _launchpad_card(**overrides: object) -> dict[str, object]:
    card: dict[str, object] = {
        "card_id": "launchpad_01_reduce_concentration",
        "goal": "Reduce concentration",
        "source_problem_id": "high_single_asset_concentration",
        "source_diagnosis_id": "high_single_asset_concentration",
        "hypothesis_to_test": "Test whether a capped benchmark reduces concentration.",
        "default_method": "risk_parity",
        "suggested_methods": [
            {
                "candidate_method_id": "risk_parity",
                "method_role": "targeted_hypothesis",
            },
            {
                "candidate_method_id": "equal_weight",
                "method_role": "targeted_hypothesis",
            },
            {
                "candidate_method_id": "maximum_diversification",
                "method_role": "targeted_hypothesis",
            },
        ],
        "success_criteria": ["Lower largest holding weight."],
        "tradeoff_to_watch": "Concentration reduction versus turnover.",
        "when_to_skip": "Skip if concentration is no longer material.",
        "card_type": "targeted_hypothesis_test",
        "launch_status": "hypothesis_test",
        "is_rebalance_recommendation": False,
        "decision_boundary": DECISION_BOUNDARY,
    }
    card.update(overrides)
    return card


def test_simple_mode_exposes_only_session_04_editable_fields() -> None:
    prefill = launchpad_card_to_builder_prefill(_launchpad_card())

    setup = build_simple_builder_parameters(prefill)

    assert setup["simple_mode"] is True
    assert setup["editable_fields"] == list(SIMPLE_BUILDER_EDITABLE_FIELDS)
    assert set(setup["parameters"]) == set(SIMPLE_BUILDER_EDITABLE_FIELDS)
    assert setup["goal"] == "Reduce concentration"
    assert setup["method"] == "equal_weight"
    assert setup["selected_method"] == "equal_weight"
    assert setup["constraint_preset"] == "custom"
    assert setup["max_asset_weight"] == 0.15
    assert setup["min_asset_weight"] == 0.0
    assert setup["advanced_settings_exposed"] is False
    assert setup["prohibited_advanced_fields"] == []
    assert "candidate_id" not in setup
    assert "weights" not in setup
    assert "comparison" not in setup
    assert "verdict" not in setup


def test_simple_mode_allows_user_overrides_and_preserves_method_change_state() -> None:
    prefill = launchpad_card_to_builder_prefill(_launchpad_card())

    setup = build_simple_builder_parameters(
        prefill,
        overrides={
            "method": "maximum_diversification",
            "constraint_preset": "balanced",
            "max_asset_weight": 0.2,
            "min_asset_weight": 0.01,
        },
    )

    assert setup["method"] == "maximum_diversification"
    assert setup["original_suggested_method"] == "equal_weight"
    assert setup["method_changed_by_user"] is True
    assert setup["constraint_preset"] == "balanced"
    assert setup["max_asset_weight"] == 0.2
    assert setup["min_asset_weight"] == 0.01
    assert "volatility_target" not in setup["parameters"]
    assert "rebalancing_frequency" not in setup["parameters"]
    assert "transaction_cost_bps" not in setup["parameters"]


def test_simple_mode_preserves_reference_preset_boundary() -> None:
    prefill = launchpad_card_to_builder_prefill(
        _launchpad_card(
            card_id="launchpad_01_compare_against_simple_benchmark",
            goal="Compare against simple benchmark",
            source_problem_id="mixed_evidence_no_action",
            source_diagnosis_id="mixed_evidence_no_action",
            hypothesis_to_test="Test whether simple references clarify materiality.",
            default_method="equal_weight",
            suggested_methods=[
                {"candidate_method_id": "equal_weight", "method_role": "reference_benchmark"},
                {"candidate_method_id": "risk_parity", "method_role": "reference_benchmark"},
            ],
            success_criteria=["Create a transparent reference point."],
            card_type="reference_benchmark_test",
            launch_status="reference_test",
        )
    )

    setup = build_simple_builder_parameters(prefill)

    assert setup["method_role"] == "reference_benchmark"
    assert setup["constraint_preset"] == "basic_reference"
    assert setup["constraint_preset"] in SIMPLE_BUILDER_ALLOWED_PRESETS
    assert setup["is_rebalance_recommendation"] is False
    assert "Decision Verdict" in setup["decision_boundary"]


def test_simple_mode_rejects_advanced_optimizer_settings() -> None:
    prefill = launchpad_card_to_builder_prefill(_launchpad_card())

    with pytest.raises(
        PortfolioAlternativesBuilderError,
        match="advanced_simple_mode_fields_not_supported",
    ):
        build_simple_builder_parameters(
            prefill,
            overrides={"tax_aware_optimization": True},
        )


def test_simple_mode_rejects_non_mvp_optimization_fields() -> None:
    prefill = launchpad_card_to_builder_prefill(_launchpad_card())

    with pytest.raises(
        PortfolioAlternativesBuilderError,
        match="advanced_simple_mode_fields_not_supported",
    ):
        build_simple_builder_parameters(
            prefill,
            overrides={"volatility_target": 0.1},
        )
