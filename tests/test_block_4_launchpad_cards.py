"""Tests for Block 4 v3 Candidate Launchpad card generation (Session 08)."""

from __future__ import annotations

from scripts.core_mvp_validation_contract import (
    BLOCK_4_V3_RULESET_VERSION,
    CANDIDATE_LAUNCHPAD_V3_VERSION,
    PROBLEM_CLASSIFICATION_V3_VERSION,
    block_4_v3_diagnosis_handoff_violations,
    candidate_launchpad_v3_product_contract_violations,
    check_candidate_launchpad_v3,
)
from src.block_4.action_path_mapping import map_action_paths
from src.block_4.evidence_extraction import extract_evidence_signals
from src.block_4.launchpad_cards import (
    LAUNCHPAD_BUILD_RULESET_VERSION,
    MAX_LAUNCHPAD_CARDS,
    build_candidate_launchpad_v3_document,
    build_launchpad_cards,
)
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


def _minimal_pc_from_mapping(mapping, *, launchpad_outcome: str = "proceed_to_launchpad") -> dict:
    return {
        "schema_version": PROBLEM_CLASSIFICATION_V3_VERSION,
        "diagnostic_only": True,
        "diagnosis_mode": "current_portfolio_problem_classification",
        "ruleset_version": BLOCK_4_V3_RULESET_VERSION,
        "status": "ok",
        "generated_at": "2026-05-29T12:00:00Z",
        "analysis_end": "2026-04-30",
        "source_artifacts": {
            "portfolio_xray": "portfolio_xray.json",
            "stress_report": "stress_report.json",
        },
        "primary_problem": mapping.primary_problem,
        "secondary_problems": list(mapping.secondary_problems),
        "rejected_problems": [],
        "suggested_actions": [row.to_dict() for row in mapping.suggested_actions],
        "no_trade_or_monitoring_view": {
            "outcome": launchpad_outcome,
            "headline_en": "Diagnostic headline.",
            "reasons": [],
            "recommended_next_step": "select_launchpad_card",
            "launchpad_suppressed": False,
        },
        "data_quality_warnings": [],
        "diagnostics_meta": {
            "evidence_signal_count": 12,
            "problems_evaluated": 15,
            "problems_activated": 3,
        },
        "problems": list(mapping.problem_rows),
        "summary": {
            "primary_problem_id": mapping.primary_problem["problem_id"],
            "n_secondary": len(mapping.secondary_problems),
            "n_rejected": 0,
            "n_problems": len(mapping.problem_rows),
            "current_portfolio_acceptable": False,
            "no_trade_outcome": launchpad_outcome,
        },
        "warnings": [],
    }


def test_golden_fixture_builds_contract_valid_launchpad() -> None:
    xray = _load_golden_xray()
    stress = _hedge_gap_stress()
    evidence = extract_evidence_signals(xray, stress)
    scoring = score_problems(evidence)
    _, _, _, mapping = _pipeline(xray, stress)
    launchpad = build_candidate_launchpad_v3_document(
        mapping,
        scoring=scoring,
        evidence=evidence,
        analysis_end="2026-04-30",
        generated_at="2026-05-29T12:00:00Z",
    )

    assert launchpad["schema_version"] == CANDIDATE_LAUNCHPAD_V3_VERSION
    assert launchpad["launchpad_outcome"] == "proceed_to_launchpad"
    assert launchpad["cards"]
    assert len(launchpad["cards"]) <= MAX_LAUNCHPAD_CARDS
    assert launchpad["cards"][0]["source_problem_id"] == "weak_crisis_resilience"
    assert launchpad["cards"][0]["suggested_methods"]
    assert launchpad["cards"][0]["default_method"]
    assert launchpad["cards"][0]["generates_portfolio"] is False
    assert launchpad["summary"]["primary_card_id"] == launchpad["cards"][0]["card_id"]

    assert not candidate_launchpad_v3_product_contract_violations(launchpad)
    checks = check_candidate_launchpad_v3(launchpad)
    assert checks["product_contract_ok"] is True


def test_golden_fixture_handoff_with_problem_classification_stub() -> None:
    xray = _load_golden_xray()
    stress = _hedge_gap_stress()
    evidence = extract_evidence_signals(xray, stress)
    scoring = score_problems(evidence)
    _, _, _, mapping = _pipeline(xray, stress)
    launchpad = build_candidate_launchpad_v3_document(
        mapping,
        scoring=scoring,
        evidence=evidence,
        analysis_end="2026-04-30",
        generated_at="2026-05-29T12:00:00Z",
    )
    pc = _minimal_pc_from_mapping(mapping, launchpad_outcome=launchpad["launchpad_outcome"])
    assert not block_4_v3_diagnosis_handoff_violations(pc, launchpad)


def test_acceptable_portfolio_suppresses_builder_methods() -> None:
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
    result = build_launchpad_cards(mapping)

    assert result.launchpad_outcome == "monitor"
    assert result.launchpad_suppressed is True
    assert len(result.cards) <= 2
    reference_cards = [card for card in result.cards if card["card_type"] == "reference_benchmark_test"]
    assert reference_cards
    reference_card = reference_cards[0]
    assert reference_card["launch_status"] == "reference_test"
    assert reference_card["is_rebalance_recommendation"] is False
    assert "Current vs Candidate Comparison and Decision Verdict" in reference_card["decision_boundary"]
    method_ids = [row["candidate_method_id"] for row in reference_card["suggested_methods"]]
    assert method_ids == ["equal_weight", "risk_parity"]
    assert {row["method_role"] for row in reference_card["suggested_methods"]} == {
        "reference_benchmark"
    }
    assert "Equal Weight" in reference_card["why_this_test"]
    assert "Risk Parity" in reference_card["why_this_test"]


def test_data_quality_primary_emits_do_not_act_outcome() -> None:
    xray = {"sections": {f"section_{i}": {"status": "partial"} for i in range(4)}}
    _, _, _, mapping = _pipeline(xray, {})
    launchpad = build_candidate_launchpad_v3_document(mapping, analysis_end="2026-04-30")

    assert launchpad["launchpad_outcome"] == "do_not_act_yet"
    assert launchpad["cards"]
    assert all(not card["suggested_methods"] for card in launchpad["cards"])
    assert all(card["card_type"] != "reference_benchmark_test" for card in launchpad["cards"])
    assert not candidate_launchpad_v3_product_contract_violations(launchpad)


def test_actionable_problem_keeps_targeted_card_before_reference_tests() -> None:
    xray = _load_golden_xray()
    stress = _hedge_gap_stress()
    evidence, scoring, _, mapping = _pipeline(xray, stress)
    launchpad = build_candidate_launchpad_v3_document(
        mapping,
        scoring=scoring,
        evidence=evidence,
        analysis_end="2026-04-30",
        generated_at="2026-05-29T12:00:00Z",
    )

    first = launchpad["cards"][0]
    assert first["source_problem_id"] == "weak_crisis_resilience"
    assert first["card_type"] == "targeted_hypothesis_test"
    assert first["launch_status"] == "hypothesis_test"
    assert first["default_method"] != "equal_weight"
    assert first["default_method"] != "risk_parity"


def test_cards_include_v2_narrative_fields() -> None:
    _, _, _, mapping = _pipeline(_load_golden_xray(), _hedge_gap_stress())
    result = build_launchpad_cards(mapping)
    card = result.cards[0]

    for key in (
        "why_this_path_en",
        "what_this_tests_en",
        "expected_tradeoff_to_check_en",
        "when_to_skip_this_test_en",
        "not_a_recommendation_disclaimer_en",
        "priority_rank",
        "simple_constraints",
    ):
        assert key in card
    assert card["not_a_recommendation_disclaimer_en"].startswith(
        "This card suggests a hypothesis to test, not a buy or sell instruction."
    )


def test_launchpad_build_ruleset_version_constant() -> None:
    assert LAUNCHPAD_BUILD_RULESET_VERSION.startswith("block_4_v3_")
