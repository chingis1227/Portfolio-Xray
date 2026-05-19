from __future__ import annotations

import json
from pathlib import Path

from src.monitoring import (
    DIFF_SCHEMA_VERSION,
    SNAPSHOT_SCHEMA_VERSION,
    build_analysis_snapshot,
    build_monitoring_diff,
    persist_analysis_snapshot,
    write_monitoring_outputs,
)


def _cand(cid: str, *, role: str, status: str = "available", vol: float = 0.12) -> dict:
    return {
        "candidate_id": cid,
        "display_name": cid.title(),
        "role": role,
        "status": status,
        "metrics": {
            "10y": {
                "vol_annual": vol,
                "beta_portfolio": 0.9,
                "max_drawdown": -0.22,
                "cagr": 0.07,
            }
        },
        "stress": {
            "overall": "DIAG_PASS",
            "scenarios": [
                {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.15},
                {"scenario_id": "rates_shock", "portfolio_pnl_pct": -0.08},
            ],
        },
        "diversification": {"top1_rc_asset": "VOO", "top1_rc_pct": 0.35},
        "factor_regime": {"macro_regime": {"label": "late_cycle"}},
        "mandate": {"portfolio_valid": True},
    }


def _comparison(*, analysis_end: str = "2025-12-31") -> dict:
    return {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": analysis_end,
        "investor_currency": "USD",
        "output_dir_final": "Main portfolio",
        "candidates": [
            _cand("policy", role="policy"),
            _cand("current", role="user_current", vol=0.14),
        ],
    }


def _comparison_with_subject(*, analysis_end: str = "2025-12-31") -> dict:
    comp = _comparison(analysis_end=analysis_end)
    comp["candidates"].insert(0, _cand("analysis_subject", role="analysis_subject", vol=0.13))
    return comp


def _health_robust() -> tuple[dict, dict]:
    rows = [
        {"candidate_id": "policy", "total_score": 72, "score_status": "scored"},
        {"candidate_id": "current", "total_score": 65, "score_status": "scored"},
    ]
    return (
        {"schema_version": "portfolio_health_score_v1", "candidates": rows},
        {"schema_version": "robustness_scorecard_v1", "candidates": rows},
    )


def _selection(*, status: str = "no_material_rebalance") -> dict:
    return {
        "schema_version": "selection_decision_v1",
        "decision_status": status,
        "favored_candidate_id": "policy",
        "favored_display_name": "Policy",
    }


def _action(*, status: str = "no_trades_no_material_rebalance") -> dict:
    return {
        "schema_version": "action_plan_v1",
        "action_status": status,
        "selection_decision_status": "no_material_rebalance",
    }


def test_snapshot_schema_and_profiles():
    health, robust = _health_robust()
    snap = build_analysis_snapshot(
        _comparison(),
        health=health,
        robustness=robust,
        selection=_selection(),
        action=_action(),
    )
    assert snap["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert "current" in snap["profiles"]
    assert "policy" in snap["profiles"]
    assert snap["profiles"]["current"]["health_score"] == 65
    assert snap["profiles"]["current"]["worst_scenario_id"] == "equity_shock"
    assert snap["profiles"]["current"]["macro_regime_label"] == "late_cycle"


def test_monitoring_primary_profile_prefers_analysis_subject():
    health, robust = _health_robust()
    health["candidates"].append(
        {"candidate_id": "analysis_subject", "total_score": 66, "score_status": "scored"}
    )
    robust["candidates"].append(
        {"candidate_id": "analysis_subject", "total_score": 67, "score_status": "scored"}
    )
    snap = build_analysis_snapshot(_comparison_with_subject(), health=health, robustness=robust)
    diff = build_monitoring_diff(snap, None)
    assert "analysis_subject" in snap["profiles"]
    assert diff["primary_profile_id"] == "analysis_subject"


def test_diff_no_prior_snapshot():
    snap = build_analysis_snapshot(_comparison(), health=_health_robust()[0])
    diff = build_monitoring_diff(snap, None)
    assert diff["schema_version"] == DIFF_SCHEMA_VERSION
    assert diff["diff_status"] == "no_prior_snapshot"
    assert "first stored monitoring snapshot" in diff["summary_plain_en"]
    assert diff["profile_changes"] == {}
    assert diff["prior_analysis_end"] is None
    assert diff["decision_changes"]["decision_status_changed"] is False
    assert diff["decision_changes"]["prior_decision_status"] is None
    assert diff["input_artifacts"]["prior_snapshot"] is None


def test_diff_available_with_deltas():
    health, robust = _health_robust()
    prior = build_analysis_snapshot(
        _comparison(analysis_end="2025-11-30"),
        health=health,
        robustness=robust,
    )
    prior["profiles"]["current"]["health_score"] = 60
    prior["profiles"]["current"]["metrics_10y"]["vol_annual"] = 0.11
    prior["profiles"]["current"]["worst_scenario_id"] = "rates_shock"
    prior["profiles"]["current"]["macro_regime_label"] = "expansion"

    current = build_analysis_snapshot(
        _comparison(analysis_end="2025-12-31"),
        health=health,
        robustness=robust,
        selection=_selection(status="selected_candidate"),
        action=_action(status="trades_for_review"),
    )
    diff = build_monitoring_diff(current, prior)
    assert diff["diff_status"] == "diff_available"
    pc = diff["profile_changes"]["current"]
    assert pc["available"] is True
    assert pc["health_score_delta"] == 5.0
    assert pc["worst_scenario_changed"] is True
    assert pc["macro_regime_changed"] is True
    assert diff["rebalance_trigger"] is True


def test_diff_same_analysis_end_ignored():
    health, robust = _health_robust()
    prior = build_analysis_snapshot(_comparison(), health=health, robustness=robust)
    prior["profiles"]["current"]["health_score"] = 50
    current = build_analysis_snapshot(_comparison(), health=health, robustness=robust)
    diff = build_monitoring_diff(current, prior)
    assert diff["diff_status"] == "no_prior_snapshot"
    assert "prior_same_analysis_end_ignored" in diff["warnings"]
    assert diff["profile_changes"] == {}
    assert diff["prior_analysis_end"] is None
    assert diff["input_artifacts"]["prior_snapshot"] is None
    pc = diff["profile_changes"].get("current")
    assert pc is None


def test_persist_history_and_write_outputs(tmp_path: Path):
    out = tmp_path / "Main portfolio"
    out.mkdir()
    comp = _comparison()
    health, robust = _health_robust()
    sel = _selection()
    act = _action()

    with open(out / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comp, f)
    with open(out / "portfolio_health_score.json", "w", encoding="utf-8") as f:
        json.dump(health, f)
    with open(out / "robustness_scorecard.json", "w", encoding="utf-8") as f:
        json.dump(robust, f)
    with open(out / "selection_decision.json", "w", encoding="utf-8") as f:
        json.dump(sel, f)
    with open(out / "action_plan.json", "w", encoding="utf-8") as f:
        json.dump(act, f)

    class _Cfg:
        output_dir_final = "Main portfolio"

    paths1 = write_monitoring_outputs(_Cfg(), project_root=tmp_path, write_txt=True)
    assert paths1["monitoring_diff_json"].is_file()
    assert paths1["analysis_snapshot_latest"].is_file()
    assert paths1["analysis_snapshot_history"].is_file()

    d1 = json.loads(paths1["monitoring_diff_json"].read_text(encoding="utf-8"))
    assert d1["diff_status"] == "no_prior_snapshot"

    comp2 = _comparison(analysis_end="2026-01-31")
    comp2["candidates"][1]["metrics"]["10y"]["vol_annual"] = 0.16
    with open(out / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comp2, f)

    paths2 = write_monitoring_outputs(
        _Cfg(),
        project_root=tmp_path,
        comparison=comp2,
        health=health,
        robustness=robust,
        selection=sel,
        action=act,
    )
    d2 = json.loads(paths2["monitoring_diff_json"].read_text(encoding="utf-8"))
    assert d2["diff_status"] == "diff_available"
    assert d2["profile_changes"]["current"]["vol_annual_delta"] is not None
