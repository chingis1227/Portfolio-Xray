from __future__ import annotations

from src.portfolio_alternatives_builder import (
    BUILDER_VALIDATION_STATUSES,
    build_simple_builder_parameters,
    launchpad_card_to_builder_prefill,
    validate_builder_setup,
)


DECISION_BOUNDARY = (
    "This is not a rebalance recommendation. Actual rebalance decision is made "
    "only after Current vs Candidate Comparison and Decision Verdict."
)


def _launchpad_card(**overrides: object) -> dict[str, object]:
    card: dict[str, object] = {
        "card_id": "launchpad_01_improve_crisis_resilience",
        "goal": "Improve crisis resilience",
        "source_problem_id": "weak_crisis_resilience",
        "source_diagnosis_id": "weak_crisis_resilience",
        "hypothesis_to_test": "Test whether stress loss improves without hiding tradeoffs.",
        "default_method": "minimum_cvar",
        "suggested_methods": [
            {
                "candidate_method_id": "minimum_cvar",
                "method_role": "targeted_hypothesis",
            },
            {
                "candidate_method_id": "maximum_diversification",
                "method_role": "targeted_hypothesis",
            },
        ],
        "success_criteria": ["Lower severe-stress loss."],
        "tradeoff_to_watch": "Stress protection versus expected return and turnover.",
        "when_to_skip": "Skip if the crisis-resilience diagnosis no longer applies.",
        "card_type": "targeted_hypothesis_test",
        "launch_status": "hypothesis_test",
        "is_rebalance_recommendation": False,
        "decision_boundary": DECISION_BOUNDARY,
    }
    card.update(overrides)
    return card


def _valid_setup(**overrides: object) -> dict[str, object]:
    prefill = launchpad_card_to_builder_prefill(_launchpad_card())
    setup = build_simple_builder_parameters(prefill)
    setup.update(overrides)
    return setup


def test_builder_validation_status_allowlist_is_explicit() -> None:
    assert BUILDER_VALIDATION_STATUSES == {
        "valid",
        "blocked_by_data_quality",
        "invalid_method",
        "missing_goal",
        "missing_method",
        "invalid_constraints",
        "infeasible_constraints_risk",
        "reference_benchmark_boundary_violation",
    }


def test_builder_validation_accepts_valid_targeted_setup() -> None:
    setup = _valid_setup()

    validation = validate_builder_setup(setup)

    assert validation == {
        "validation_status": "valid",
        "can_generate_candidate": True,
        "validation_errors": [],
        "validation_warnings": [],
    }


def test_builder_validation_blocks_data_quality_setup_before_method_checks() -> None:
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
    setup = build_simple_builder_parameters(prefill)

    validation = validate_builder_setup(setup)

    assert validation["validation_status"] == "blocked_by_data_quality"
    assert validation["can_generate_candidate"] is False
    assert validation["validation_errors"] == ["data_quality_blocker"]


def test_builder_validation_rejects_missing_goal_and_method() -> None:
    missing_goal = validate_builder_setup(_valid_setup(goal=None))
    missing_method = validate_builder_setup(_valid_setup(method=None, selected_method=None))

    assert missing_goal["validation_status"] == "missing_goal"
    assert missing_goal["can_generate_candidate"] is False
    assert missing_method["validation_status"] == "missing_method"
    assert missing_method["can_generate_candidate"] is False


def test_builder_validation_rejects_unsupported_method() -> None:
    validation = validate_builder_setup(_valid_setup(method="unsupported_method"))

    assert validation["validation_status"] == "invalid_method"
    assert validation["can_generate_candidate"] is False
    assert validation["validation_errors"] == ["unsupported_method:unsupported_method"]


def test_builder_validation_rejects_invalid_constraint_sanity() -> None:
    bad_range = validate_builder_setup(_valid_setup(min_asset_weight=0.2, max_asset_weight=0.1))
    bad_negative_min = validate_builder_setup(_valid_setup(min_asset_weight=-0.01))
    bad_nonpositive_max = validate_builder_setup(_valid_setup(max_asset_weight=0.0))

    assert bad_range["validation_status"] == "invalid_constraints"
    assert "max_asset_weight_below_min_asset_weight" in bad_range["validation_errors"]
    assert bad_negative_min["validation_status"] == "invalid_constraints"
    assert "min_asset_weight_must_be_non_negative" in bad_negative_min["validation_errors"]
    assert bad_nonpositive_max["validation_status"] == "invalid_constraints"
    assert "max_asset_weight_must_be_positive" in bad_nonpositive_max["validation_errors"]


def test_builder_validation_flags_obvious_feasibility_risk() -> None:
    validation = validate_builder_setup(_valid_setup(max_asset_weight=0.1, asset_count=9))

    assert validation["validation_status"] == "infeasible_constraints_risk"
    assert validation["can_generate_candidate"] is False
    assert validation["validation_errors"] == ["max_asset_weight_too_low_for_asset_count"]


def test_builder_validation_preserves_reference_benchmark_boundary() -> None:
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

    validation = validate_builder_setup(setup)

    assert validation["validation_status"] == "valid"
    assert validation["can_generate_candidate"] is True
    assert setup["method_role"] == "reference_benchmark"
    assert setup["is_rebalance_recommendation"] is False
    assert "Decision Verdict" in setup["decision_boundary"]


def test_builder_validation_rejects_reference_boundary_violation() -> None:
    prefill = launchpad_card_to_builder_prefill(
        _launchpad_card(
            card_id="launchpad_01_compare_against_simple_benchmark",
            goal="Compare against simple benchmark",
            source_problem_id="mixed_evidence_no_action",
            source_diagnosis_id="mixed_evidence_no_action",
            default_method="equal_weight",
            suggested_methods=[
                {"candidate_method_id": "equal_weight", "method_role": "reference_benchmark"},
                {"candidate_method_id": "risk_parity", "method_role": "reference_benchmark"},
            ],
            card_type="reference_benchmark_test",
            launch_status="reference_test",
        )
    )
    setup = build_simple_builder_parameters(prefill)
    setup["method_role"] = "targeted_candidate_method"

    validation = validate_builder_setup(setup)

    assert validation["validation_status"] == "reference_benchmark_boundary_violation"
    assert validation["can_generate_candidate"] is False
    assert "reference_benchmark_method_role_required" in validation["validation_errors"]


def test_builder_validation_requires_targeted_hypothesis_success_and_tradeoff() -> None:
    setup = _valid_setup(
        hypothesis_to_test=None,
        success_criteria=[],
        tradeoff_to_watch=None,
    )

    validation = validate_builder_setup(setup)

    assert validation["validation_status"] == "invalid_constraints"
    assert "targeted_setup_missing_hypothesis_to_test" in validation["validation_errors"]
    assert "targeted_setup_missing_success_criteria" in validation["validation_errors"]
    assert "targeted_setup_missing_tradeoff_to_watch" in validation["validation_errors"]
