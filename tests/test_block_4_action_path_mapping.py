"""Tests for Block 4 v3 suggested action path mapping (Session 07)."""

from __future__ import annotations

from src.block_4.action_path_mapping import (
    ACTION_PATH_MAPPING_RULESET_VERSION,
    build_suggested_actions,
    map_action_paths,
)
from src.block_4.evidence_extraction import extract_evidence_signals
from src.block_4.problem_prioritization import prioritize_problems
from src.block_4.problem_scoring import score_problems
from block_4_fixtures import hedge_gap_stress as _hedge_gap_stress
from block_4_fixtures import load_golden_xray as _load_golden_xray


def _pipeline(xray: dict, stress: dict):
    evidence = extract_evidence_signals(xray, stress)
    scoring = score_problems(evidence)
    prioritization = prioritize_problems(scoring, evidence)
    mapping = map_action_paths(prioritization, scoring)
    return evidence, scoring, prioritization, mapping


def test_golden_fixture_maps_crisis_primary_action_paths() -> None:
    _, _, prioritization, mapping = _pipeline(_load_golden_xray(), _hedge_gap_stress())

    assert prioritization.primary_problem_id == "weak_crisis_resilience"
    assert mapping.primary_problem["problem_id"] == "weak_crisis_resilience"
    assert mapping.primary_problem["suggested_action_path_id"] == "improve_crisis_resilience"
    assert mapping.primary_problem["reasonable_paths_to_test"]
    assert mapping.primary_problem["candidate_method_suggestions"]
    assert mapping.primary_problem["short_diagnosis_en"]
    assert mapping.primary_problem["why_it_matters_en"]
    assert "Weak hedge behavior" in mapping.primary_problem["do_not_overreact_reason_en"]
    assert "secondary" in mapping.primary_problem["do_not_overreact_reason_en"].lower()

    assert mapping.suggested_actions
    assert mapping.suggested_actions[0].action_path_id == "improve_crisis_resilience"
    assert mapping.suggested_actions[0].priority == 1
    assert "weak_crisis_resilience" in mapping.suggested_actions[0].source_problem_ids


def test_suggested_actions_dedupe_shared_secondary_paths() -> None:
    primary = {
        "problem_id": "weak_crisis_resilience",
        "suggested_action_path_id": "improve_crisis_resilience",
        "secondary_action_path_ids": ["reduce_drawdown_risk"],
    }
    secondary = {
        "problem_id": "high_drawdown",
        "suggested_action_path_id": "reduce_drawdown_risk",
        "secondary_action_path_ids": ["improve_crisis_resilience"],
    }

    actions = build_suggested_actions(primary, [secondary])

    action_ids = [row.action_path_id for row in actions]
    assert action_ids[0] == "improve_crisis_resilience"
    assert action_ids.count("reduce_drawdown_risk") == 1
    assert actions[0].priority == 1

    drawdown_action = next(row for row in actions if row.action_path_id == "reduce_drawdown_risk")
    assert set(drawdown_action.source_problem_ids) == {"weak_crisis_resilience", "high_drawdown"}


def test_acceptable_portfolio_suppresses_candidate_methods() -> None:
    xray = {
        "block_2_1_asset_allocation": {
            "status": "ok",
            "portfolio_composition_snapshot": {
                "top1_holding": {"ticker": "A", "weight_pct": 10.0},
                "top3_weight_pct": 28.0,
            },
            "concentration_flags": [],
            "duplicate_exposure_flags": [],
        },
        "block_2_2_portfolio_metrics": {
            "status": "ok",
            "return_risk_metrics": {"vol_annual": 0.08, "sharpe": 0.9, "sortino": 1.1},
            "drawdown_diagnostics": {"max_drawdown": -0.05, "recovered": True},
            "tail_risk_diagnostics": {"es_95": -0.008},
            "benchmark_dependence": {"beta_portfolio": 0.4},
        },
        "block_2_3_factor_exposure": {
            "status": "ok",
            "factor_betas_5y": {"betas": {"beta_eq": 0.4, "beta_rr": 0.1, "beta_credit": 0.05}},
        },
    }
    stress = _hedge_gap_stress(
        hedge_gap_analysis_v1={
            "version": "hedge_gap_analysis_v1",
            "block_status": "ok",
            "summary": {
                "main_hedge_gap": {
                    "protection_status": "strong_protection",
                    "offset_coverage_ratio": 0.75,
                    "portfolio_loss_pct": -0.02,
                }
            },
            "by_risk_type": [],
        },
        scenario_results=[{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.02}],
    )
    _, _, _, mapping = _pipeline(xray, stress)

    assert mapping.primary_problem["problem_id"] == "current_portfolio_acceptable"
    assert mapping.primary_problem["suggested_action_path_id"] == "compare_against_simple_benchmark"
    assert mapping.primary_problem["candidate_method_suggestions"] == []
    assert mapping.suggested_actions[0].action_path_id == "compare_against_simple_benchmark"


def test_data_quality_problem_maps_do_not_act_path() -> None:
    xray = {"sections": {f"section_{i}": {"status": "partial"} for i in range(4)}}
    _, _, _, mapping = _pipeline(xray, {})

    assert mapping.primary_problem["problem_id"] == "evidence_insufficient_data_quality"
    assert mapping.primary_problem["suggested_action_path_id"] == "evidence_insufficient_do_not_act_yet"
    assert mapping.primary_problem["candidate_method_suggestions"] == []
    assert mapping.suggested_actions[0].action_path_id == "evidence_insufficient_do_not_act_yet"


def test_secondary_problem_action_paths_follow_primary_in_priority() -> None:
    _, _, prioritization, mapping = _pipeline(_load_golden_xray(), _hedge_gap_stress())

    assert mapping.secondary_problems
    assert len(mapping.problem_rows) == 1 + len(mapping.secondary_problems)
    assert mapping.suggested_actions[0].priority == 1
    if len(mapping.suggested_actions) > 1:
        assert mapping.suggested_actions[1].priority == 2
        secondary_ids = set(prioritization.secondary_problem_ids)
        assert secondary_ids & set(mapping.suggested_actions[1].source_problem_ids)


def test_action_path_mapping_ruleset_version_constant() -> None:
    assert ACTION_PATH_MAPPING_RULESET_VERSION.startswith("block_4_v3_")
