from __future__ import annotations

import copy

import pytest

from block_4_fixtures import archetype_concentrated_equity
from src.block_4.diagnosis_builder import build_block_4_diagnosis
from src.client_fit import build_client_fit_check
from src.decision_verdict import build_decision_verdict_from_block7_8


def _xray(*, cagr: float = 0.06, vol: float = 0.09, max_drawdown: float = -0.18) -> dict:
    return {
        "block_2_2_portfolio_metrics": {
            "status": "ok",
            "return_risk_metrics": {
                "portfolio_cagr": cagr,
                "vol_annual": vol,
                "sharpe": 0.6,
                "sortino": 0.8,
            },
            "drawdown_diagnostics": {"max_drawdown": max_drawdown, "recovered": True},
        }
    }


def _stress(*, worst_loss: float = -0.18) -> dict:
    return {
        "current_portfolio_stress_scorecard_v1": {
            "version": "current_portfolio_stress_scorecard_v1",
            "availability": "available",
            "worst_synthetic_scenario": {
                "availability": "available",
                "scenario_id": "recession_severe",
                "portfolio_loss_pct": worst_loss,
            },
        }
    }


def _profile(preset_id: str, **overrides) -> dict:
    base = {
        "preset_id": preset_id,
        "source": "questionnaire",
        "source_quality": "medium",
        "source_quality_reason": "matrix fixture",
        "horizon_years": 7,
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ("preset_id", "expected_status"),
    [
        ("conservative", "breach"),
        ("balanced", "fit"),
        ("aggressive", "watch"),
    ],
)
def test_same_portfolio_changes_client_fit_interpretation_without_changing_objective_evidence(preset_id: str, expected_status: str) -> None:
    xray = _xray(cagr=0.06, vol=0.09, max_drawdown=-0.18)
    stress = _stress(worst_loss=-0.18)
    xray_before = copy.deepcopy(xray)
    stress_before = copy.deepcopy(stress)

    doc = build_client_fit_check(client_fit=_profile(preset_id), portfolio_xray=xray, stress_report=stress)

    assert doc["client_fit_status"] == expected_status
    assert xray == xray_before
    assert stress == stress_before
    assert doc["checks"][0]["portfolio_value"] == 0.06
    assert doc["checks"][1]["portfolio_value"] == 0.09


def test_goal_risk_conflict_blocks_objective_review_without_optimizer_promise() -> None:
    fit = build_client_fit_check(
        client_fit=_profile(
            "aggressive",
            horizon_years=2,
            target_return_range={"min": 0.10, "max": 0.12},
            target_vol_range={"min": 0.08, "max": 0.12},
            target_max_drawdown_pct=-0.12,
        ),
        portfolio_xray=_xray(cagr=0.09, vol=0.09, max_drawdown=-0.05),
        stress_report=_stress(worst_loss=-0.04),
    )
    diagnosis = build_block_4_diagnosis(
        portfolio_xray=_xray(cagr=0.09, vol=0.09, max_drawdown=-0.05),
        stress_report=_stress(worst_loss=-0.04),
        client_fit_check=fit,
        analysis_end="2026-06-12",
    )

    pc = diagnosis.problem_classification
    assert fit["client_fit_status"] == "conflict"
    assert pc["primary_problem"]["problem_id"] == "goal_risk_conflict"
    assert pc["next_diagnostic_step"]["type"] == "client_objective_review"


def test_fit_pass_with_concentration_issue_stays_structural_diagnosis_and_not_no_action() -> None:
    case = archetype_concentrated_equity()
    xray = copy.deepcopy(case.portfolio_xray)
    metrics = dict(xray["block_2_2_portfolio_metrics"])
    return_risk = dict(metrics["return_risk_metrics"])
    return_risk["portfolio_cagr"] = 0.06
    metrics["return_risk_metrics"] = return_risk
    xray["block_2_2_portfolio_metrics"] = metrics
    fit = build_client_fit_check(
        client_fit=_profile(
            "balanced",
            target_return_range={"min": 0.05, "max": 0.07},
            target_vol_range={"min": 0.05, "max": 0.20},
            target_max_drawdown_pct=-0.30,
        ),
        portfolio_xray=xray,
        stress_report=case.stress_report,
    )

    diagnosis = build_block_4_diagnosis(
        portfolio_xray=xray,
        stress_report=case.stress_report,
        client_fit_check=fit,
        analysis_end="2026-06-12",
    )
    verdict = build_decision_verdict_from_block7_8(
        candidate_generation=_generation(),
        current_vs_candidate=_comparison(material=False, success="not_met"),
        client_fit_check=fit,
        problem_classification=diagnosis.problem_classification,
    )

    assert fit["client_fit_status"] == "fit"
    assert diagnosis.problem_classification["primary_problem"]["problem_id"] == "high_concentration"
    assert diagnosis.problem_classification["diagnostic_quality_status"] in {"issue", "material_issue"}
    assert verdict["decision_action"] == "test_another_candidate"
    assert verdict["verdict_reason_id"] == "client_fit_pass_does_not_clear_material_diagnosis"


def test_missing_client_fit_backend_compatibility_keeps_diagnosis_running() -> None:
    fit = build_client_fit_check(client_fit=None, portfolio_xray=_xray(), stress_report=_stress())
    diagnosis = build_block_4_diagnosis(
        portfolio_xray=_xray(),
        stress_report=_stress(),
        client_fit_check=fit,
        analysis_end="2026-06-12",
    )

    pc = diagnosis.problem_classification
    assert fit["client_fit_status"] == "not_provided"
    assert pc["client_fit_status"] == "not_provided"
    assert pc["primary_problem"]["problem_id"] != "goal_risk_conflict"
    assert pc["source_artifacts"]["client_fit_check"] == "client_fit_check.json"


def test_partial_client_fit_evidence_is_insufficient_not_breach_or_fit() -> None:
    doc = build_client_fit_check(
        client_fit=_profile("balanced"),
        portfolio_xray=_xray(cagr=0.06, vol=0.09, max_drawdown=-0.18),
        stress_report=None,
    )

    assert doc["client_fit_status"] == "evidence_insufficient"
    assert any(
        row["dimension"] == "worst_stress_loss_vs_limit" and row["status"] == "evidence_insufficient"
        for row in doc["checks"]
    )
    assert doc["source_artifacts"]["stress_report"] is None


def _generation() -> dict:
    return {
        "generation_status": "generated",
        "candidate": {"candidate_id": "equal_weight", "status": "generated"},
        "method_availability": {"available": True, "availability_status": "available"},
        "warnings": [],
        "handoff_to_comparison": {"can_compare": True},
    }


def _comparison(*, material: bool = False, success: str = "not_met") -> dict:
    return {
        "baseline": {"candidate_id": "analysis_subject"},
        "selected_candidate_ids": ["equal_weight"],
        "comparisons": [
            {
                "candidate_id": "equal_weight",
                "status": "available",
                "dimensions": [{"field": "vol_annual", "status": "available"}],
                "risk_reduced": [{"field": "vol_annual", "is_material": material}],
                "risk_added": [],
                "what_improved": [{"field": "vol_annual", "is_material": material}],
                "what_worsened": [],
                "practicality": {
                    "turnover_required": {"status": "available", "turnover_half_sum_pct": 0.10},
                    "estimated_transaction_cost_pct": 0.0001,
                },
                "success_criteria_result": {"overall_status": success, "criteria": []},
                "materiality_for_decision_review": {
                    "status": "review_candidate" if material else "not_material",
                    "is_material_enough": material,
                    "reason": "review_candidate" if material else "no_material_improvement_detected",
                },
                "data_quality": {
                    "missing_fields": [],
                    "warnings": [],
                    "construction_disclosure_status": "available",
                },
            }
        ],
        "warnings": [],
    }
