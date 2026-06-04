from __future__ import annotations

from pathlib import Path

import pytest

from scripts.core_mvp_validation_contract import (
    builder_prefill_product_contract_violations,
    candidate_launchpad_v3_product_contract_violations,
)
from src.portfolio_alternatives_builder import (
    PortfolioAlternativeRequest,
    PortfolioAlternativesBuilderError,
    build_builder_prefill_from_launchpad_card,
    build_portfolio_alternative_plan,
    request_from_launchpad_card,
    run_portfolio_alternative_plan,
    supported_candidate_methods,
)


def _contract_valid_launchpad_card(**overrides: object) -> dict[str, object]:
    card: dict[str, object] = {
        "card_id": "launchpad_01_improve_crisis_resilience",
        "title": "Improve crisis resilience",
        "goal": "Improve crisis resilience",
        "description": "Test whether crisis resilience can improve.",
        "why_this_path_en": "Stress evidence points to weak resilience.",
        "what_this_tests_en": "A CVaR constrained candidate.",
        "expected_tradeoff_to_check_en": "Stress protection versus return trade-off.",
        "when_to_skip_this_test_en": "Skip if data quality is unresolved.",
        "not_a_recommendation_disclaimer_en": (
            "This card suggests a hypothesis to test, not a buy or sell instruction."
        ),
        "priority_rank": 1,
        "source_problem_id": "weak_crisis_resilience",
        "source_diagnosis_id": "weak_crisis_resilience",
        "hypothesis_to_test": "Test whether stress loss improves.",
        "suggested_methods": [
            {
                "candidate_method_id": "minimum_cvar_constrained",
                "method_role": "targeted_hypothesis",
            }
        ],
        "default_method": "minimum_cvar_constrained",
        "simple_constraints": [],
        "generates_portfolio": False,
        "requires_user_action": True,
        "success_criteria": ["Lower stress loss."],
        "card_type": "targeted_hypothesis_test",
        "launch_status": "hypothesis_test",
        "why_this_test": "Stress evidence should be tested explicitly.",
        "tradeoff_to_watch": "Stress protection versus expected return.",
        "when_to_skip": "Skip if the diagnosis no longer applies.",
        "is_rebalance_recommendation": False,
        "decision_boundary": "This is not a rebalance recommendation.",
    }
    card.update(overrides)
    return card


def _contract_valid_launchpad_doc(card: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "candidate_launchpad_v3",
        "diagnostic_only": True,
        "ruleset_version": "block_4_v3_2026_06",
        "launchpad_outcome": "proceed_to_launchpad",
        "cards": [card],
        "summary": {
            "n_cards": 1,
            "primary_card_id": card["card_id"],
            "has_portfolio_generating_options": True,
            "has_keep_current_option": False,
            "launchpad_outcome": "proceed_to_launchpad",
        },
    }


def test_supported_candidate_methods_include_launchpad_methods() -> None:
    methods = supported_candidate_methods()

    assert "equal_weight" in methods
    assert "risk_parity" in methods
    assert "minimum_variance" in methods
    assert "minimum_cvar_constrained" in methods
    assert "robust_mv_constrained" in methods


def test_request_from_launchpad_card_selects_method() -> None:
    request = request_from_launchpad_card(
        {
            "card_id": "launchpad_01_reduce_volatility",
            "goal": "Reduce volatility",
            "suggested_methods": [
                {"candidate_method_id": "minimum_variance"},
                {"candidate_method_id": "risk_parity"},
            ],
        },
        method_index=1,
    )

    assert request.candidate_method_id == "risk_parity"
    assert request.goal == "Reduce volatility"
    assert request.source_card_id == "launchpad_01_reduce_volatility"


def test_request_from_launchpad_card_rejects_monitor_only_card() -> None:
    with pytest.raises(PortfolioAlternativesBuilderError, match="launchpad_card_has_no_suggested_methods"):
        request_from_launchpad_card(
            {
                "card_id": "launchpad_01_keep_current",
                "goal": "Keep current portfolio and monitor",
                "suggested_methods": [],
            }
        )


def test_build_builder_prefill_from_targeted_launchpad_card_preserves_handoff_fields() -> None:
    next_step = {"step_id": "test_crisis_candidate", "label": "Test crisis-resilience candidate"}

    prefill = build_builder_prefill_from_launchpad_card(
        {
            "card_id": "launchpad_01_improve_crisis_resilience",
            "goal": "Improve crisis resilience",
            "source_diagnosis_id": "weak_crisis_resilience",
            "hypothesis_to_test": "Test whether crisis resilience improves.",
            "default_method": "minimum_cvar_constrained",
            "suggested_methods": [
                {
                    "candidate_method_id": "minimum_cvar_constrained",
                    "method_role": "targeted_hypothesis",
                },
                {
                    "candidate_method_id": "robust_mv_constrained",
                    "method_role": "targeted_hypothesis",
                },
            ],
            "success_criteria": ["Lower stress loss."],
            "tradeoff_to_watch": "Risk improvement vs turnover.",
            "when_to_skip": "Skip when the diagnosis no longer applies.",
            "card_type": "targeted_hypothesis_test",
            "launch_status": "hypothesis_test",
            "is_rebalance_recommendation": False,
            "decision_boundary": "This is not a rebalance recommendation.",
        },
        next_diagnostic_step=next_step,
    )

    assert prefill["builder_mode"] == "guided_from_diagnosis"
    assert prefill["source"] == "candidate_launchpad_v3"
    assert prefill["source_diagnosis_id"] == "weak_crisis_resilience"
    assert prefill["source_card_id"] == "launchpad_01_improve_crisis_resilience"
    assert prefill["goal"] == "Improve crisis resilience"
    assert prefill["hypothesis_to_test"] == "Test whether crisis resilience improves."
    assert prefill["next_diagnostic_step"] == next_step
    assert prefill["suggested_method"] == "minimum_cvar_constrained"
    assert prefill["alternative_methods"] == ["robust_mv_constrained"]
    assert prefill["method_role"] == "targeted_candidate_method"
    assert prefill["success_criteria"] == ["Lower stress loss."]
    assert prefill["tradeoff_to_watch"] == "Risk improvement vs turnover."
    assert prefill["when_to_skip"] == "Skip when the diagnosis no longer applies."
    assert prefill["card_type"] == "targeted_hypothesis_test"
    assert prefill["launch_status"] == "hypothesis_test"
    assert prefill["is_rebalance_recommendation"] is False
    assert prefill["decision_boundary"] == "This is not a rebalance recommendation."
    assert prefill["candidate_generation_allowed"] is True


def test_build_builder_prefill_from_reference_card_keeps_benchmark_role() -> None:
    prefill = build_builder_prefill_from_launchpad_card(
        {
            "card_id": "launchpad_01_compare_against_simple_benchmark",
            "goal": "Compare against simple benchmark",
            "source_diagnosis_id": "mixed_evidence_no_action",
            "hypothesis_to_test": "Test whether simple references clarify materiality.",
            "suggested_methods": [
                {"candidate_method_id": "equal_weight", "method_role": "reference_benchmark"},
                {"candidate_method_id": "risk_parity", "method_role": "reference_benchmark"},
            ],
            "success_criteria": ["Create a transparent reference point."],
            "card_type": "reference_benchmark_test",
            "launch_status": "reference_test",
            "is_rebalance_recommendation": False,
            "decision_boundary": "This is not a rebalance recommendation.",
        }
    )

    assert prefill["builder_mode"] == "guided_from_diagnosis"
    assert prefill["suggested_method"] == "equal_weight"
    assert prefill["alternative_methods"] == ["risk_parity"]
    assert prefill["method_role"] == "reference_benchmark"
    assert prefill["candidate_generation_allowed"] is True
    assert prefill["is_rebalance_recommendation"] is False


def test_build_builder_prefill_from_data_quality_card_blocks_candidate_generation() -> None:
    prefill = build_builder_prefill_from_launchpad_card(
        {
            "card_id": "launchpad_01_evidence_insufficient_do_not_act_yet",
            "goal": "Review data quality",
            "source_diagnosis_id": "evidence_insufficient_data_quality",
            "hypothesis_to_test": "Resolve data quality before testing candidates.",
            "suggested_methods": [],
            "success_criteria": ["Resolve data-quality blockers."],
            "card_type": "monitor_or_data_step",
            "launch_status": "monitor_or_resolve_data",
            "is_rebalance_recommendation": False,
            "decision_boundary": "This is not a rebalance recommendation.",
        }
    )

    assert prefill["builder_mode"] == "blocked_data_quality"
    assert prefill["suggested_method"] is None
    assert prefill["alternative_methods"] == []
    assert prefill["method_role"] is None
    assert prefill["candidate_generation_allowed"] is False


def test_builder_prefill_contract_accepts_valid_targeted_prefill() -> None:
    prefill = build_builder_prefill_from_launchpad_card(_contract_valid_launchpad_card())

    assert not builder_prefill_product_contract_violations(prefill)


def test_builder_prefill_contract_rejects_missing_decision_boundary() -> None:
    prefill = build_builder_prefill_from_launchpad_card(_contract_valid_launchpad_card())
    prefill["decision_boundary"] = None

    violations = builder_prefill_product_contract_violations(prefill)

    assert any("missing decision_boundary" in row for row in violations)


def test_launchpad_contract_rejects_reference_ew_rp_without_reference_role() -> None:
    card = _contract_valid_launchpad_card(
        card_id="launchpad_01_compare_against_simple_benchmark",
        goal="Compare against simple benchmark",
        source_problem_id="mixed_evidence_no_action",
        source_diagnosis_id="mixed_evidence_no_action",
        card_type="reference_benchmark_test",
        launch_status="reference_test",
        suggested_methods=[
            {"candidate_method_id": "equal_weight", "method_role": "targeted_hypothesis"},
            {"candidate_method_id": "risk_parity", "method_role": "reference_benchmark"},
        ],
        default_method="equal_weight",
    )
    doc = _contract_valid_launchpad_doc(card)

    violations = candidate_launchpad_v3_product_contract_violations(doc)

    assert any("EW/RP reference methods must use method_role reference_benchmark" in row for row in violations)


def test_launchpad_contract_rejects_data_quality_candidate_methods() -> None:
    card = _contract_valid_launchpad_card(
        card_id="launchpad_01_evidence_insufficient_do_not_act_yet",
        goal="Review data quality",
        source_problem_id="evidence_insufficient_data_quality",
        source_diagnosis_id="evidence_insufficient_data_quality",
        card_type="reference_benchmark_test",
        launch_status="monitor_or_resolve_data",
        suggested_methods=[
            {"candidate_method_id": "equal_weight", "method_role": "reference_benchmark"},
            {"candidate_method_id": "risk_parity", "method_role": "reference_benchmark"},
        ],
        default_method="equal_weight",
        candidate_generation_allowed=True,
    )
    doc = _contract_valid_launchpad_doc(card)
    doc["launchpad_outcome"] = "do_not_act_yet"
    doc["summary"]["launchpad_outcome"] = "do_not_act_yet"  # type: ignore[index]

    violations = candidate_launchpad_v3_product_contract_violations(doc)

    assert any("candidate_generation_allowed must not be true" in row for row in violations)
    assert any("data-quality cards must not provide candidate methods" in row for row in violations)
    assert any("data-quality cards must not provide EW/RP comparisons" in row for row in violations)


def test_builder_prefill_contract_rejects_data_quality_candidate_generation() -> None:
    prefill = build_builder_prefill_from_launchpad_card(
        {
            **_contract_valid_launchpad_card(
                card_id="launchpad_01_evidence_insufficient_do_not_act_yet",
                goal="Review data quality",
                source_problem_id="evidence_insufficient_data_quality",
                source_diagnosis_id="evidence_insufficient_data_quality",
                card_type="monitor_or_data_step",
                launch_status="monitor_or_resolve_data",
            ),
            "suggested_methods": [],
            "default_method": None,
        }
    )
    prefill["candidate_generation_allowed"] = True

    violations = builder_prefill_product_contract_violations(prefill)

    assert any("data-quality prefill must not allow candidate generation" in row for row in violations)


def test_build_portfolio_alternative_plan_delegates_to_single_candidate_factory(
    tmp_path: Path,
) -> None:
    plan = build_portfolio_alternative_plan(
        PortfolioAlternativeRequest(
            candidate_method_id="minimum_variance",
            goal="Reduce volatility",
            source_card_id="launchpad_01_reduce_volatility",
        ),
        project_root=tmp_path,
        python_executable="python-test",
    )

    assert plan.candidate_method_id == "minimum_variance"
    assert plan.candidate_id == "minimum_variance"
    assert plan.command == (
        "python-test",
        str(tmp_path / "run_candidate_factory.py"),
        "--candidates",
        "minimum_variance",
        "--execution-mode",
        "standard",
        "--output-profile",
        "site_api",
        "--then-compare",
    )
    assert plan.provenance["delegates_to"] == "run_candidate_factory.py"
    assert plan.provenance["does_not_change_formulas"] is True


def test_build_portfolio_alternative_plan_can_skip_compare(tmp_path: Path) -> None:
    plan = build_portfolio_alternative_plan(
        PortfolioAlternativeRequest(candidate_method_id="risk_parity"),
        project_root=tmp_path,
        python_executable="python-test",
        then_compare=False,
    )

    assert "--then-compare" not in plan.command
    assert plan.artifact_contract["candidate_comparison"] is None


def test_build_portfolio_alternative_plan_records_unapplied_v1_parameters(tmp_path: Path) -> None:
    plan = build_portfolio_alternative_plan(
        PortfolioAlternativeRequest(
            candidate_method_id="equal_weight",
            max_asset_weight=0.1,
        ),
        project_root=tmp_path,
        python_executable="python-test",
    )

    assert plan.warnings == ("request_parameters_recorded_not_applied_v1",)


def test_build_portfolio_alternative_plan_rejects_unknown_method(tmp_path: Path) -> None:
    with pytest.raises(PortfolioAlternativesBuilderError, match="unsupported_candidate_method:unknown"):
        build_portfolio_alternative_plan(
            PortfolioAlternativeRequest(candidate_method_id="unknown"),
            project_root=tmp_path,
        )


def test_run_portfolio_alternative_plan_dry_run_does_not_execute(tmp_path: Path) -> None:
    plan = build_portfolio_alternative_plan(
        PortfolioAlternativeRequest(candidate_method_id="equal_weight"),
        project_root=tmp_path,
        python_executable="python-test",
    )

    def _boom(*_args, **_kwargs):
        raise AssertionError("runner must not be called in dry-run mode")

    assert run_portfolio_alternative_plan(plan, project_root=tmp_path, runner=_boom) is None


def test_equal_weight_launchpad_method_maps_to_documented_product_commands(
    tmp_path: Path,
) -> None:
    """Session 05: equal_weight from Launchpad → factory plan and review --candidates only.

    Documented in docs/product_flow_operator_guide.md; no new run_portfolio_review flags.
    """
    request = request_from_launchpad_card(
        {
            "card_id": "launchpad_demo_equal_weight",
            "goal": "Simple diversification baseline",
            "suggested_methods": [{"candidate_method_id": "equal_weight"}],
        },
    )
    plan = build_portfolio_alternative_plan(
        request,
        project_root=tmp_path,
        python_executable="python",
    )

    assert plan.candidate_method_id == "equal_weight"
    assert plan.candidate_id == "equal_weight"
    assert Path(plan.command[1]).name == "run_candidate_factory.py"
    assert plan.command[2:6] == ("--candidates", "equal_weight", "--execution-mode", "standard")
    assert "--then-compare" in plan.command
    assert "--output-profile" in plan.command
    assert "site_api" in plan.command

    factory_argv = list(plan.command[2:])
    assert factory_argv.index("--candidates") == 0
    assert factory_argv[factory_argv.index("--candidates") + 1] == "equal_weight"
    assert factory_argv.index("--execution-mode") >= 0
    assert factory_argv[factory_argv.index("--execution-mode") + 1] == "standard"
    assert "--then-compare" in factory_argv
