import json

from src.block_4.diagnosis_builder import build_block_4_diagnosis
from src.block_4.evidence_extraction import extract_evidence_signals
from src.block_4.problem_prioritization import prioritize_problems
from src.block_4.problem_scoring import score_problems
from src.client_fit import (
    CLIENT_FIT_CHECK_FILENAME,
    build_client_fit_check,
    write_client_fit_check_outputs,
)
from block_4_fixtures import archetype_concentrated_equity


def _xray(*, cagr=0.06, vol=0.09, max_drawdown=-0.16):
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


def _stress(*, worst_loss=-0.18):
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


def _client_fit(**overrides):
    base = {
        "preset_id": "balanced",
        "source": "questionnaire",
        "source_quality": "medium",
        "source_quality_reason": "test profile",
        "horizon_years": 7,
        "target_return_range": {"min": 0.05, "max": 0.07},
        "target_vol_range": {"min": 0.07, "max": 0.10},
        "target_max_drawdown_pct": -0.20,
    }
    base.update(overrides)
    return base


def test_client_fit_check_not_provided_is_backend_compatible():
    doc = build_client_fit_check(client_fit=None, portfolio_xray=_xray(), stress_report=_stress())

    assert doc["schema_version"] == "client_fit_check_v1"
    assert doc["client_fit_status"] == "not_provided"
    assert doc["profile"]["source_quality"] == "missing"
    assert doc["recommendation_boundary"]


def test_client_fit_check_fit_and_written_artifact(tmp_path):
    doc = write_client_fit_check_outputs(
        output_dir=tmp_path,
        client_fit=_client_fit(),
        portfolio_xray=_xray(),
        stress_report=_stress(),
        analysis_end="2026-06-12",
    )

    assert doc["client_fit_status"] == "fit"
    assert {row["dimension"] for row in doc["checks"]} >= {
        "volatility_vs_target",
        "historical_max_drawdown_vs_limit",
        "worst_stress_loss_vs_limit",
        "return_target_gap",
        "horizon_risk_mismatch",
        "goal_risk_conflict",
    }
    loaded = json.loads((tmp_path / CLIENT_FIT_CHECK_FILENAME).read_text(encoding="utf-8"))
    assert loaded["analysis_end"] == "2026-06-12"


def test_client_fit_check_detects_breach_and_goal_risk_conflict():
    doc = build_client_fit_check(
        client_fit=_client_fit(
            preset_id="aggressive",
            horizon_years=2,
            target_return_range={"min": 0.10, "max": 0.12},
            target_vol_range={"min": 0.08, "max": 0.12},
            target_max_drawdown_pct=-0.12,
        ),
        portfolio_xray=_xray(cagr=0.06, vol=0.16, max_drawdown=-0.18),
        stress_report=_stress(worst_loss=-0.25),
    )

    assert doc["client_fit_status"] == "conflict"
    assert doc["goal_risk_conflict"]["status"] == "conflict"
    assert any(row["status"] == "breach" for row in doc["checks"])


def test_block_4_evidence_extraction_preserves_client_fit_context():
    fit = build_client_fit_check(
        client_fit=_client_fit(target_max_drawdown_pct=-0.12),
        portfolio_xray=_xray(max_drawdown=-0.18),
        stress_report=_stress(worst_loss=-0.22),
    )

    evidence = extract_evidence_signals(_xray(max_drawdown=-0.18), _stress(worst_loss=-0.22), fit)

    assert evidence.has_signal("client_fit_status")
    assert evidence.get_signals("client_fit_status")[0].source_artifact == "client_fit_check.json"
    assert evidence.has_signal("client_fit_historical_max_drawdown_vs_limit")


def test_block_4_diagnosis_lists_client_fit_source_artifact():
    fit = build_client_fit_check(
        client_fit=_client_fit(target_max_drawdown_pct=-0.12),
        portfolio_xray=_xray(max_drawdown=-0.18),
        stress_report=_stress(worst_loss=-0.22),
    )

    diagnosis = build_block_4_diagnosis(
        portfolio_xray=_xray(max_drawdown=-0.18),
        stress_report=_stress(worst_loss=-0.22),
        client_fit_check=fit,
        analysis_end="2026-06-12",
    )

    assert diagnosis.problem_classification["source_artifacts"]["client_fit_check"] == "client_fit_check.json"
    assert diagnosis.problem_classification["diagnostics_meta"]["evidence_signal_count"] >= 1


def test_client_fit_breach_supports_existing_diagnosis_without_universal_primary():
    fit = build_client_fit_check(
        client_fit=_client_fit(target_vol_range={"min": 0.04, "max": 0.10}),
        portfolio_xray=_xray(vol=0.18, max_drawdown=-0.07),
        stress_report=_stress(worst_loss=-0.04),
    )
    evidence = extract_evidence_signals(_xray(vol=0.18, max_drawdown=-0.07), _stress(worst_loss=-0.04), fit)
    scoring = score_problems(evidence)
    prioritization = prioritize_problems(scoring, evidence)

    volatility = scoring.get_row("high_volatility")
    assert volatility is not None
    assert any(ref["signal"] == "client_fit_volatility_vs_target" for ref in volatility.evidence_refs)
    assert prioritization.primary_problem_id != "goal_risk_conflict"


def test_client_fit_fit_is_contrary_context_not_structural_suppression():
    fit = build_client_fit_check(
        client_fit=_client_fit(target_vol_range={"min": 0.04, "max": 0.22}, target_max_drawdown_pct=-0.30),
        portfolio_xray=_xray(vol=0.18, max_drawdown=-0.07),
        stress_report=_stress(worst_loss=-0.04),
    )
    evidence = extract_evidence_signals(_xray(vol=0.18, max_drawdown=-0.07), _stress(worst_loss=-0.04), fit)
    scoring = score_problems(evidence)

    assert evidence.has_signal("client_fit_within_profile")
    volatility = scoring.get_row("high_volatility")
    assert volatility is not None
    assert any(ref["signal"] == "client_fit_within_profile" for ref in volatility.negative_evidence_refs)


def test_client_fit_breach_alone_does_not_replace_portfolio_diagnosis():
    fit = build_client_fit_check(
        client_fit=_client_fit(
            target_return_range={"min": 0.02, "max": 0.04},
            target_vol_range={"min": 0.01, "max": 0.03},
            target_max_drawdown_pct=-0.01,
        ),
        portfolio_xray=_xray(cagr=0.03, vol=0.08, max_drawdown=-0.05),
        stress_report=_stress(worst_loss=-0.02),
    )

    diagnosis = build_block_4_diagnosis(
        portfolio_xray=_xray(cagr=0.03, vol=0.08, max_drawdown=-0.05),
        stress_report=_stress(worst_loss=-0.02),
        client_fit_check=fit,
        analysis_end="2026-06-12",
    )
    pc = diagnosis.problem_classification

    assert fit["client_fit_status"] == "breach"
    assert pc["client_fit_status"] == "breach"
    assert pc["diagnostic_quality_status"] == "clean"
    assert pc["primary_problem"]["problem_id"] == "current_portfolio_acceptable"
    assert pc["interpretation_chain"]["selected_diagnosis_id"] == "current_portfolio_acceptable"


def test_goal_risk_conflict_is_the_only_client_fit_primary_exception():
    fit = build_client_fit_check(
        client_fit=_client_fit(
            preset_id="aggressive",
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

    assert pc["primary_problem"]["problem_id"] == "goal_risk_conflict"
    assert pc["next_diagnostic_step"]["type"] == "client_objective_review"
    assert pc["diagnostic_quality_status"] == "clean"
    assert pc["client_fit_context"]["goal_risk_conflict_status"] == "conflict"


def test_client_fit_status_and_diagnostic_quality_status_remain_separate_with_material_issue():
    case = archetype_concentrated_equity()
    xray = dict(case.portfolio_xray)
    metrics_block = dict(xray["block_2_2_portfolio_metrics"])
    return_risk = dict(metrics_block["return_risk_metrics"])
    return_risk["portfolio_cagr"] = 0.06
    metrics_block["return_risk_metrics"] = return_risk
    xray["block_2_2_portfolio_metrics"] = metrics_block
    fit = build_client_fit_check(
        client_fit=_client_fit(target_vol_range={"min": 0.05, "max": 0.20}, target_max_drawdown_pct=-0.30),
        portfolio_xray=xray,
        stress_report=case.stress_report,
    )

    diagnosis = build_block_4_diagnosis(
        portfolio_xray=xray,
        stress_report=case.stress_report,
        client_fit_check=fit,
        analysis_end="2026-06-12",
    )
    pc = diagnosis.problem_classification
    chain = pc["interpretation_chain"]

    assert pc["client_fit_status"] == "fit"
    assert pc["diagnostic_quality_status"] in {"issue", "material_issue"}
    assert pc["primary_problem"]["problem_id"] == "high_concentration"
    assert chain["client_fit_status"] == pc["client_fit_status"]
    assert chain["diagnostic_quality_status"] == pc["diagnostic_quality_status"]
    assert chain["client_fit_context"]["selected_diagnosis_id"] == "high_concentration"
