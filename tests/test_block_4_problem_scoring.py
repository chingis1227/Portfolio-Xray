"""Tests for Block 4 v2 evidence-to-problem scoring (Session 04)."""

from __future__ import annotations

from src.block_4.evidence_extraction import extract_evidence_signals
from src.block_4.problem_scoring import (
    ACTIVATION_RAW_THRESHOLD,
    score_problems,
)
from block_4_fixtures import hedge_gap_stress as _hedge_gap_stress
from block_4_fixtures import load_golden_xray as _load_golden_xray

def test_golden_fixture_activates_stress_and_concentration_problems() -> None:
    evidence = extract_evidence_signals(_load_golden_xray(), _hedge_gap_stress())
    result = score_problems(evidence)

    assert result.problems_evaluated == 15
    assert "weak_crisis_resilience" in result.actionable_activated_ids
    assert "weak_hedge_behavior" in result.actionable_activated_ids
    assert "high_concentration" in result.actionable_activated_ids

    crisis = result.get_row("weak_crisis_resilience")
    assert crisis is not None
    assert crisis.activated
    assert crisis.required_met
    assert crisis.scoring.stress_confirmation == "confirmed"
    assert crisis.scoring.materiality in {"high", "medium"}
    assert crisis.scoring.raw_score >= ACTIVATION_RAW_THRESHOLD
    assert crisis.evidence_refs
    assert all("normalized_score" in ref for ref in crisis.evidence_refs)


def test_low_risk_portfolio_triggers_acceptable_outcome() -> None:
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
    evidence = extract_evidence_signals(xray, stress)
    result = score_problems(evidence)

    assert result.no_material_problem
    acceptable = result.get_row("current_portfolio_acceptable")
    assert acceptable is not None
    assert acceptable.activated
    assert "current_portfolio_acceptable" in result.activated_problem_ids


def test_data_trust_failure_activates_evidence_quality_problem() -> None:
    xray = {"sections": {f"section_{i}": {"status": "partial"} for i in range(4)}}
    evidence = extract_evidence_signals(xray, {})
    result = score_problems(evidence)

    dq = result.get_row("evidence_insufficient_data_quality")
    assert dq is not None
    assert dq.activated
    assert result.activated_problem_ids == ("evidence_insufficient_data_quality",)


def test_conflicting_signals_activate_conflict_problem() -> None:
    xray = {
        "block_2_2_portfolio_metrics": {
            "status": "ok",
            "return_risk_metrics": {"vol_annual": 0.22},
        },
    }
    stress = _hedge_gap_stress()
    evidence = extract_evidence_signals(xray, stress)
    assert evidence.has_signal("worst_synthetic_scenario")

    # Inject contradictory derived signal via manual bucket extension is not needed;
    # low_stress_loss_with_high_vol is emitted when vol high and synthetic loss mild.
    stress_mild = _hedge_gap_stress(
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
    evidence2 = extract_evidence_signals(xray, stress_mild)
    assert evidence2.has_signal("low_stress_loss_with_high_vol")
    result = score_problems(evidence2)

    assert result.conflicting_signal_bundle
    conflict = result.get_row("evidence_insufficient_conflicting_signals")
    assert conflict is not None
    assert conflict.activated


def test_negative_evidence_may_block_equity_beta_when_present() -> None:
    xray = _load_golden_xray()
    stress = _hedge_gap_stress()
    evidence = extract_evidence_signals(xray, stress)
    result = score_problems(evidence)

    beta_row = result.get_row("high_equity_beta")
    assert beta_row is not None
    if beta_row.negative_evidence_refs:
        assert all(ref["signal"] for ref in beta_row.negative_evidence_refs)


def test_inactive_problem_gets_reject_reason_below_threshold() -> None:
    xray = {
        "block_2_2_portfolio_metrics": {
            "status": "ok",
            "return_risk_metrics": {"vol_annual": 0.11},
        },
    }
    evidence = extract_evidence_signals(xray, {})
    result = score_problems(evidence)

    vol_row = result.get_row("high_volatility")
    assert vol_row is not None
    assert not vol_row.activated
    assert vol_row.reject_reason_code in {
        "below_activation_threshold",
        "required_evidence_incomplete",
    }
