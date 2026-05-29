"""Tests for Block 4 v2 no-trade / monitor gate (Session 09)."""

from __future__ import annotations

from scripts.core_mvp_validation_contract import (
    PROBLEM_CLASSIFICATION_V2_VERSION,
    problem_classification_v2_product_contract_violations,
)
from src.block_4.action_path_mapping import map_action_paths
from src.block_4.evidence_extraction import extract_evidence_signals
from src.block_4.launchpad_cards import build_candidate_launchpad_v2_document
from src.block_4.no_trade_gate import (
    NO_TRADE_GATE_RULESET_VERSION,
    OUTCOME_DO_NOT_ACT,
    OUTCOME_MONITOR,
    OUTCOME_PROCEED,
    STEP_MONITOR,
    STEP_RESOLVE_DATA,
    STEP_RERUN,
    STEP_SELECT_LAUNCHPAD,
    NoTradeGateResult,
    build_diagnosis_summary,
    evaluate_no_trade_gate,
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
    gate = evaluate_no_trade_gate(mapping, scoring, evidence, prioritization=prioritization)
    return evidence, scoring, prioritization, mapping, gate


def test_golden_fixture_proceeds_to_launchpad() -> None:
    _, _, prioritization, mapping, gate = _pipeline(_load_golden_xray(), _hedge_gap_stress())

    assert gate.outcome == OUTCOME_PROCEED
    assert gate.recommended_next_step == STEP_SELECT_LAUNCHPAD
    assert gate.launchpad_suppressed is False
    assert gate.headline_en
    assert "Primary confidence is high" in gate.reasons
    assert "Stress evidence confirms the primary diagnosis" in gate.reasons

    launchpad = build_candidate_launchpad_v2_document(
        mapping,
        scoring=score_problems(extract_evidence_signals(_load_golden_xray(), _hedge_gap_stress())),
        evidence=extract_evidence_signals(_load_golden_xray(), _hedge_gap_stress()),
        analysis_end="2026-04-30",
    )
    assert launchpad["launchpad_outcome"] == OUTCOME_PROCEED


def test_acceptable_portfolio_monitors() -> None:
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
    _, _, _, mapping, gate = _pipeline(xray, stress)

    assert gate.outcome == OUTCOME_MONITOR
    assert gate.recommended_next_step == STEP_MONITOR
    assert gate.launchpad_suppressed is True

    summary = build_diagnosis_summary(mapping, gate)
    assert summary["current_portfolio_acceptable"] is True
    assert summary["no_trade_outcome"] == OUTCOME_MONITOR


def test_data_quality_blocks_action() -> None:
    xray = {"sections": {f"section_{i}": {"status": "partial"} for i in range(4)}}
    _, _, _, mapping, gate = _pipeline(xray, {})

    assert gate.outcome == OUTCOME_DO_NOT_ACT
    assert gate.recommended_next_step == STEP_RESOLVE_DATA
    assert gate.launchpad_suppressed is True
    assert gate.reasons


def test_conflicting_signals_block_action() -> None:
    xray = {
        "block_2_2_portfolio_metrics": {
            "status": "ok",
            "return_risk_metrics": {"vol_annual": 0.22},
        },
    }
    stress = _hedge_gap_stress(
        scenario_results=[{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.03}],
        hedge_gap_analysis_v1={
            "version": "hedge_gap_analysis_v1",
            "block_status": "ok",
            "summary": {
                "main_hedge_gap": {
                    "protection_status": "partial_protection",
                    "offset_coverage_ratio": 0.4,
                    "portfolio_loss_pct": -0.03,
                }
            },
            "by_risk_type": [],
        },
    )
    _, _, _, _, gate = _pipeline(xray, stress)

    assert gate.outcome == OUTCOME_DO_NOT_ACT
    assert gate.recommended_next_step == STEP_RERUN
    assert "Conflicting" in gate.headline_en


def test_no_trade_view_passes_problem_classification_contract_stub() -> None:
    _, _, prioritization, mapping, gate = _pipeline(_load_golden_xray(), _hedge_gap_stress())
    summary = build_diagnosis_summary(
        mapping,
        gate,
        n_rejected=len(prioritization.rejected_problems),
    )
    doc = {
        "schema_version": PROBLEM_CLASSIFICATION_V2_VERSION,
        "diagnostic_only": True,
        "diagnosis_mode": "current_portfolio_problem_classification",
        "ruleset_version": "block_4_v2_2026_06",
        "status": "ok",
        "generated_at": "2026-05-29T12:00:00Z",
        "analysis_end": "2026-04-30",
        "source_artifacts": {
            "portfolio_xray": "portfolio_xray.json",
            "stress_report": "stress_report.json",
        },
        "primary_problem": mapping.primary_problem,
        "secondary_problems": list(mapping.secondary_problems),
        "rejected_problems": [row.to_dict() for row in prioritization.rejected_problems],
        "suggested_actions": [row.to_dict() for row in mapping.suggested_actions],
        "no_trade_or_monitoring_view": gate.to_dict(),
        "data_quality_warnings": [],
        "diagnostics_meta": {
            "evidence_signal_count": 12,
            "problems_evaluated": 15,
            "problems_activated": prioritization.problems_activated,
        },
        "problems": list(mapping.problem_rows),
        "summary": summary,
        "warnings": [],
    }
    violations = problem_classification_v2_product_contract_violations(doc)
    assert not violations
    assert summary["no_trade_outcome"] == gate.outcome


def test_low_confidence_pre_stress_actionable_primary_monitors_or_blocks() -> None:
    primary = {
        "problem_id": "high_volatility",
        "label_en": "High volatility",
        "confidence": "low",
        "severity": "medium",
        "short_diagnosis_en": "Volatility is elevated.",
        "scoring": {
            "stress_confirmation": "pre_stress_only",
            "materiality": "medium",
        },
        "evidence_refs": [{"evidence_id": "ev1", "interpretation_en": "Vol elevated."}],
    }
    from src.block_4.action_path_mapping import ActionPathMappingResult

    mapping = ActionPathMappingResult(primary_problem=primary, problem_rows=(primary,))
    evidence = extract_evidence_signals(
        {"block_2_2_portfolio_metrics": {"status": "ok", "return_risk_metrics": {"vol_annual": 0.11}}},
        {},
    )
    scoring = score_problems(evidence)
    gate = evaluate_no_trade_gate(mapping, scoring, evidence)

    assert gate.outcome in {OUTCOME_DO_NOT_ACT, OUTCOME_MONITOR}
    assert gate.launchpad_suppressed is True


def test_no_trade_gate_ruleset_version_constant() -> None:
    assert NO_TRADE_GATE_RULESET_VERSION.startswith("block_4_v2_")
    assert NoTradeGateResult(
        outcome=OUTCOME_PROCEED,
        headline_en="Headline.",
        reasons=(),
        recommended_next_step=STEP_SELECT_LAUNCHPAD,
        launchpad_suppressed=False,
    ).to_dict()["outcome"] == OUTCOME_PROCEED
