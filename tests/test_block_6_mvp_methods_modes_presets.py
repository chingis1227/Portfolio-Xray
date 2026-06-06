from __future__ import annotations

from src.portfolio_alternatives_builder import (
    CONSTRAINT_PRESETS,
    GUIDED_METHODS,
    HIDDEN_METHOD_CLASSIFICATIONS,
    UNCAPPED_MODE_CONCENTRATION_WARNING,
    build_simple_builder_parameters,
    candidate_id_for_builder_method,
    launchpad_card_to_builder_prefill,
    supported_candidate_methods,
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
        "hypothesis_to_test": "Test whether stress loss improves.",
        "default_method": "minimum_cvar",
        "suggested_methods": [
            {"candidate_method_id": "minimum_cvar", "method_role": "targeted_hypothesis"},
            {"candidate_method_id": "maximum_diversification", "method_role": "targeted_hypothesis"},
            {"candidate_method_id": "minimum_variance", "method_role": "targeted_hypothesis"},
        ],
        "success_criteria": ["Lower severe-stress loss."],
        "tradeoff_to_watch": "Stress protection versus turnover.",
        "when_to_skip": "Skip if diagnosis no longer applies.",
        "card_type": "targeted_hypothesis_test",
        "launch_status": "hypothesis_test",
        "is_rebalance_recommendation": False,
        "decision_boundary": DECISION_BOUNDARY,
    }
    card.update(overrides)
    return card


def test_guided_method_allowlist_matches_block_6_mvp_scope() -> None:
    assert set(supported_candidate_methods()) == {
        "equal_weight",
        "risk_parity",
        "hierarchical_risk_parity",
        "minimum_variance",
        "minimum_cvar",
        "maximum_diversification",
    }
    assert set(GUIDED_METHODS) == set(supported_candidate_methods())


def test_hidden_advanced_and_legacy_methods_are_not_guided() -> None:
    hidden = {
        "equal_weight_by_asset_class",
        "risk_budget_by_asset",
        "risk_budget_by_asset_class",
        "minimum_variance_advanced",
        "robust_mv_constrained",
        "robust_mv_uncapped",
        "robust_scenario",
        "legacy_policy_optimizer",
    }

    assert hidden <= set(HIDDEN_METHOD_CLASSIFICATIONS)
    assert hidden.isdisjoint(supported_candidate_methods())


def test_constraint_presets_match_session_01_contract() -> None:
    assert CONSTRAINT_PRESETS["conservative"] == {
        "min_asset_weight": 0.0,
        "max_asset_weight": 0.15,
        "mode": "capped",
        "capped": True,
    }
    assert CONSTRAINT_PRESETS["balanced"]["max_asset_weight"] == 0.20
    assert CONSTRAINT_PRESETS["aggressive"]["max_asset_weight"] == 0.30
    assert CONSTRAINT_PRESETS["uncapped"] == {
        "min_asset_weight": 0.0,
        "max_asset_weight": None,
        "mode": "uncapped",
        "capped": False,
    }


def test_capped_and_uncapped_modes_map_to_current_backend_engines() -> None:
    assert candidate_id_for_builder_method("minimum_variance", mode="capped") == "minimum_variance"
    assert (
        candidate_id_for_builder_method("minimum_variance", mode="uncapped")
        == "minimum_variance_uncapped"
    )
    assert (
        candidate_id_for_builder_method("minimum_cvar", mode="capped")
        == "minimum_cvar_constrained"
    )
    assert (
        candidate_id_for_builder_method("minimum_cvar", mode="uncapped")
        == "minimum_cvar_uncapped"
    )
    assert (
        candidate_id_for_builder_method("maximum_diversification", mode="capped")
        == "maximum_diversification"
    )
    assert (
        candidate_id_for_builder_method("maximum_diversification", mode="uncapped")
        == "maximum_diversification_uncapped"
    )


def test_uncapped_mode_carries_concentration_warning_and_null_cap() -> None:
    prefill = launchpad_card_to_builder_prefill(_launchpad_card())

    setup = build_simple_builder_parameters(
        prefill,
        overrides={"constraint_preset": "uncapped"},
    )
    validation = validate_builder_setup(setup)

    assert setup["mode"] == "uncapped"
    assert setup["capped"] is False
    assert setup["uncapped"] is True
    assert setup["min_asset_weight"] == 0.0
    assert setup["max_asset_weight"] is None
    assert UNCAPPED_MODE_CONCENTRATION_WARNING in setup["warnings"]
    assert UNCAPPED_MODE_CONCENTRATION_WARNING in validation["validation_warnings"]
