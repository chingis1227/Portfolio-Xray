"""Tests for Block 4 v2 problem prioritization (Session 06)."""

from __future__ import annotations

from src.block_4.evidence_extraction import extract_evidence_signals
from src.block_4.problem_prioritization import (
    MAX_SECONDARY_PROBLEMS,
    prioritize_problems,
)
from src.block_4.problem_scoring import score_problems
from block_4_fixtures import hedge_gap_stress as _hedge_gap_stress
from block_4_fixtures import load_golden_xray as _load_golden_xray


def test_golden_fixture_elevates_crisis_resilience_over_hedge_behavior() -> None:
    evidence = extract_evidence_signals(_load_golden_xray(), _hedge_gap_stress())
    scoring = score_problems(evidence)
    result = prioritize_problems(scoring, evidence)

    assert result.primary_problem_id == "weak_crisis_resilience"
    assert result.primary_row is not None
    assert result.primary_row.activated
    assert "hedge_gap_over_labeled_hedge" in result.elevation_rules_applied
    assert "weak_hedge_behavior" not in result.secondary_problem_ids

    rejected_ids = {row.problem_id for row in result.rejected_problems}
    assert "weak_hedge_behavior" in rejected_ids
    hedge_reject = next(r for r in result.rejected_problems if r.problem_id == "weak_hedge_behavior")
    assert hedge_reject.reject_reason_code == "superseded_by_root_cause_diagnosis"
    assert hedge_reject.top_evidence_refs


def test_golden_fixture_allows_up_to_two_secondaries() -> None:
    evidence = extract_evidence_signals(_load_golden_xray(), _hedge_gap_stress())
    scoring = score_problems(evidence)
    result = prioritize_problems(scoring, evidence)

    assert len(result.secondary_problem_ids) <= MAX_SECONDARY_PROBLEMS
    assert result.secondary_problem_ids
    assert result.primary_problem_id not in result.secondary_problem_ids
    assert len(result.selected_problem_ids()) <= 1 + MAX_SECONDARY_PROBLEMS


def test_data_quality_problem_is_sole_primary() -> None:
    xray = {"sections": {f"section_{i}": {"status": "partial"} for i in range(4)}}
    evidence = extract_evidence_signals(xray, {})
    scoring = score_problems(evidence)
    result = prioritize_problems(scoring, evidence)

    assert result.primary_problem_id == "evidence_insufficient_data_quality"
    assert result.secondary_problem_ids == ()
    assert result.problems_activated == 1


def test_acceptable_portfolio_is_primary_when_no_actionable_problems() -> None:
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
    scoring = score_problems(evidence)
    result = prioritize_problems(scoring, evidence)

    assert result.primary_problem_id == "current_portfolio_acceptable"
    assert result.secondary_problem_ids == ()


def test_concentration_elevated_over_poor_diversification() -> None:
    xray = {
        "block_2_1_asset_allocation": {
            "status": "ok",
            "portfolio_composition_snapshot": {
                "top1_holding": {"ticker": "VOO", "weight_pct": 42.0},
                "top3_weight_pct": 68.0,
            },
            "concentration_flags": [{"flag": "top1_above_threshold", "status": "high"}],
            "duplicate_exposure_flags": [
                {"status": "high", "overlap_type": "equity_proxy_cluster"},
            ],
        },
        "block_2_2_portfolio_metrics": {
            "status": "ok",
            "return_risk_metrics": {"vol_annual": 0.14},
            "drawdown_diagnostics": {"max_drawdown": -0.12, "recovered": True},
        },
        "block_2_5_risk_budget_view": {
            "status": "ok",
            "rc_top_contributors": {"top1_share_pct": 38.0},
        },
    }
    stress = _hedge_gap_stress(
        scenario_results=[{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.06}],
        hedge_gap_analysis_v1={
            "version": "hedge_gap_analysis_v1",
            "block_status": "ok",
            "summary": {
                "main_hedge_gap": {
                    "protection_status": "partial_protection",
                    "offset_coverage_ratio": 0.35,
                    "portfolio_loss_pct": -0.06,
                }
            },
            "by_risk_type": [],
        },
    )
    evidence = extract_evidence_signals(xray, stress)
    scoring = score_problems(evidence)
    result = prioritize_problems(scoring, evidence)

    assert "high_concentration" in scoring.actionable_activated_ids
    assert "poor_diversification" in scoring.actionable_activated_ids
    assert result.primary_problem_id == "high_concentration"
    assert "concentration_over_diversification" in result.elevation_rules_applied
    if "poor_diversification" not in result.secondary_problem_ids:
        rejected_ids = {row.problem_id for row in result.rejected_problems}
        assert "poor_diversification" in rejected_ids


def test_inactive_volatility_gets_reject_reason() -> None:
    xray = {
        "block_2_2_portfolio_metrics": {
            "status": "ok",
            "return_risk_metrics": {"vol_annual": 0.11},
        },
    }
    evidence = extract_evidence_signals(xray, {})
    scoring = score_problems(evidence)
    result = prioritize_problems(scoring, evidence)

    vol_reject = next(
        (row for row in result.rejected_problems if row.problem_id == "high_volatility"),
        None,
    )
    assert vol_reject is not None
    assert vol_reject.reject_reason_code in {
        "below_activation_threshold",
        "required_evidence_incomplete",
        "stress_not_confirmed_below_materiality",
    }


def test_conflicting_signals_primary_blocks_secondaries() -> None:
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
    evidence = extract_evidence_signals(xray, stress)
    scoring = score_problems(evidence)
    assert scoring.conflicting_signal_bundle
    result = prioritize_problems(scoring, evidence)

    assert result.primary_problem_id == "evidence_insufficient_conflicting_signals"
    assert result.secondary_problem_ids == ()
