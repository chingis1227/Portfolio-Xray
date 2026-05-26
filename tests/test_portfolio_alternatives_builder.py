from __future__ import annotations

from pathlib import Path

import pytest

from src.portfolio_alternatives_builder import (
    PortfolioAlternativeRequest,
    PortfolioAlternativesBuilderError,
    build_portfolio_alternative_plan,
    request_from_launchpad_card,
    run_portfolio_alternative_plan,
    supported_candidate_methods,
)


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
