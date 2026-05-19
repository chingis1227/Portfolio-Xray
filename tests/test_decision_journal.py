from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.decision_journal import (
    SCHEMA_VERSION,
    build_decision_journal,
    persist_decision_journal,
    rationale_text_is_client_safe,
    write_decision_journal_outputs,
)


def _cand(cid: str, *, role: str, status: str = "available") -> dict:
    return {
        "candidate_id": cid,
        "display_name": cid.title(),
        "role": role,
        "status": status,
        "construction_method": "policy_optimizer" if cid == "policy" else "user_supplied_weights",
        "metrics": {"10y": {"max_drawdown": -0.22}},
        "stress": {
            "overall": "DIAG_PASS",
            "scenarios": [
                {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.15},
            ],
        },
        "diversification": {"top1_rc_asset": "VOO", "top1_rc_pct": 0.35},
        "factor_regime": {"macro_regime": {"label": "late_cycle"}},
        "mandate": {"portfolio_valid": True},
    }


def _comparison(*, with_current: bool = True, analysis_end: str = "2025-12-31") -> dict:
    cands = [_cand("policy", role="policy")]
    if with_current:
        cands.append(_cand("current", role="user_current"))
    return {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": analysis_end,
        "investor_currency": "USD",
        "output_dir_final": "Main portfolio",
        "analysis_setup_summary": {"source_analysis_mode": "optimize_from_universe"},
        "candidates": cands,
        "warnings": [],
    }


def _comparison_with_subject(*, analysis_end: str = "2025-12-31") -> dict:
    comp = _comparison(analysis_end=analysis_end)
    comp["candidates"].insert(0, _cand("analysis_subject", role="analysis_subject"))
    comp["analysis_setup_summary"] = {
        "source_analysis_mode": "optimize_from_universe",
        "analysis_subject_id": "analysis_subject",
        "analysis_subject_type": "model_portfolio",
        "analysis_subject_display_name": "Starting Portfolio",
    }
    return comp


def _selection(
    *,
    status: str = "no_material_rebalance",
    favored_id: str = "policy",
    baseline_id: str = "current",
) -> dict:
    return {
        "schema_version": "selection_decision_v1",
        "formal_decision": True,
        "decision_status": status,
        "baseline_candidate_id": baseline_id,
        "baseline_display_name": "Starting Portfolio" if baseline_id == "analysis_subject" else "Current Portfolio",
        "favored_candidate_id": favored_id,
        "favored_display_name": "Policy",
        "selection_weights_profile": "default_weights_reviewable",
        "no_trade_thresholds_profile": "default_no_trade_thresholds_reviewable",
        "composite_ranking": [
            {
                "candidate_id": "policy",
                "selection_score": 72.5,
                "rank": 1,
            }
        ],
        "rejected_candidates": [
            {
                "candidate_id": "equal_weight",
                "display_name": "Equal-Weight",
                "reason_code": "lower_composite_score",
            }
        ],
        "rationale": {
            "summary": "Composite scores favor policy, but turnover versus current is high.",
            "selection_bullets": ["Policy leads on composite score."],
            "no_trade_bullets": ["Turnover exceeds materiality threshold."],
            "tradeoff_bullets": [],
            "data_quality_notes": [],
        },
        "no_trade": {
            "evaluated": True,
            "health_score_delta": 7.0,
            "robustness_score_delta": 5.0,
            "turnover_half_sum_abs_delta_pct": 18.0,
        },
        "warnings": [],
    }


def _action(*, status: str = "no_trades_no_material_rebalance") -> dict:
    return {
        "schema_version": "action_plan_v1",
        "action_status": status,
        "target_candidate_id": "policy",
        "turnover_half_sum_pct": 18.0,
        "estimated_transaction_cost_pct": 0.018,
        "no_trades_reason": "No material rebalance per selection.",
        "trades": [],
        "risk_context": {
            "health_score_delta": 7.0,
            "robustness_score_delta": 5.0,
            "drawdown_improvement_pp": 2.0,
        },
        "priority_trades": [],
    }


def _monitoring_diff() -> dict:
    return {
        "schema_version": "monitoring_diff_v1",
        "diff_status": "no_prior_snapshot",
        "summary_plain_en": "First stored monitoring snapshot for this output folder.",
        "rebalance_trigger": False,
        "prior_analysis_end": None,
    }


def _health_robust() -> tuple[dict, dict]:
    rows = [
        {"candidate_id": "policy", "total_score": 72},
        {"candidate_id": "current", "total_score": 65},
    ]
    return (
        {"schema_version": "portfolio_health_score_v1", "candidates": rows},
        {"schema_version": "robustness_scorecard_v1", "candidates": rows},
    )


def test_schema_and_required_keys():
    comp = _comparison()
    sel = _selection()
    act = _action()
    diff = _monitoring_diff()
    journal = build_decision_journal(comp, sel, action=act, monitoring_diff=diff)
    assert journal["schema_version"] == SCHEMA_VERSION
    assert journal["generated_only"] is True
    assert journal["non_executing"] is True
    for key in (
        "decision_record",
        "selected_portfolio",
        "rejected_alternatives",
        "assumptions",
        "expected_improvement",
        "accepted_risks",
        "macro_context",
        "rationale",
        "no_trade_status",
        "artifact_refs",
        "warnings",
    ):
        assert key in journal
    assert journal["process_review"] == {"status": "not_implemented"}
    assert journal["follow_up_review_date"] is None


@pytest.mark.parametrize(
    "status",
    [
        "selected_candidate",
        "no_material_rebalance",
        "inconclusive",
        "data_review_required",
    ],
)
def test_journal_for_decision_statuses(status: str):
    sel = _selection(status=status)
    journal = build_decision_journal(_comparison(), sel, action=_action())
    assert journal["decision_record"]["decision_status"] == status


def test_skip_without_selection(tmp_path: Path):
    out = tmp_path / "Main portfolio"
    out.mkdir()
    comp = _comparison()
    with open(out / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comp, f)

    class _Cfg:
        output_dir_final = "Main portfolio"

    paths = write_decision_journal_outputs(
        _Cfg(),
        project_root=tmp_path,
        comparison=comp,
        selection=None,
    )
    assert paths == {}


def test_expected_improvement_not_applicable_without_current():
    comp = _comparison(with_current=False)
    journal = build_decision_journal(comp, _selection())
    assert journal["expected_improvement"]["status"] == "not_applicable"


def test_journal_identifies_analysis_subject_baseline():
    comp = _comparison_with_subject()
    sel = _selection(
        status="selected_candidate",
        favored_id="policy",
        baseline_id="analysis_subject",
    )
    journal = build_decision_journal(comp, sel, action=_action(status="trades_for_review"))
    assert journal["decision_record"]["baseline_candidate_id"] == "analysis_subject"
    assert journal["diagnosed_subject"]["candidate_id"] == "analysis_subject"
    assert journal["expected_improvement"]["baseline_candidate_id"] == "analysis_subject"
    assert journal["assumptions"]["analysis_subject_type"] == "model_portfolio"


def test_artifact_refs_and_rationale_lint():
    comp = _comparison()
    journal = build_decision_journal(
        comp,
        _selection(),
        action=_action(),
        monitoring_diff=_monitoring_diff(),
    )
    refs = journal["artifact_refs"]
    assert "candidate_comparison" in refs
    assert refs["candidate_comparison"].endswith("candidate_comparison.json")
    assert refs["selection_decision"].endswith("selection_decision.json")
    summary = journal["rationale"]["summary"]
    assert rationale_text_is_client_safe(summary)


def test_persist_latest_matches_root(tmp_path: Path):
    out = tmp_path / "Main portfolio"
    out.mkdir()
    journal = build_decision_journal(_comparison(), _selection())
    paths = persist_decision_journal(out, journal)
    root = json.loads(paths["decision_journal_json"].read_text(encoding="utf-8"))
    latest = json.loads(paths["decision_journal_latest"].read_text(encoding="utf-8"))
    assert root == latest
    assert paths["decision_journal_history"].is_file()
    assert "decision_journal_2025-12-31.json" in paths["decision_journal_history"].name


def test_write_outputs_integration(tmp_path: Path):
    out = tmp_path / "Main portfolio"
    out.mkdir()
    comp = _comparison()
    sel = _selection(status="selected_candidate")
    act = _action(status="trades_for_review")
    act["trades"] = [{"ticker": "VOO", "delta_pct": 2.0}]
    act["priority_trades"] = [{"ticker": "VOO", "delta_pct": 2.0}]
    health, robust = _health_robust()

    with open(out / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comp, f)
    with open(out / "selection_decision.json", "w", encoding="utf-8") as f:
        json.dump(sel, f)

    class _Cfg:
        output_dir_final = "Main portfolio"

    paths = write_decision_journal_outputs(
        _Cfg(),
        project_root=tmp_path,
        comparison=comp,
        selection=sel,
        action=act,
        monitoring_diff=_monitoring_diff(),
        health=health,
        robustness=robust,
    )
    assert paths["decision_journal_json"].is_file()
    assert paths["decision_journal_txt"].is_file()
    doc = json.loads(paths["decision_journal_json"].read_text(encoding="utf-8"))
    assert doc["implementation_plan"]["trade_count"] == 1
    assert doc["what_changed"]["diff_status"] == "no_prior_snapshot"
    assert "journal_no_monitoring_diff" not in doc["warnings"]
