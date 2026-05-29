from __future__ import annotations

import json
from pathlib import Path

from src.ai_commentary_context import (
    AI_COMMENTARY_CONTEXT_VERSION,
    HEDGE_GAP_CONTEXT_VERSION,
    HEDGE_GAP_SOURCE_LEGACY,
    HEDGE_GAP_SOURCE_V1,
    PURPOSE_DIAGNOSIS_GROUNDING_ONLY,
    PURPOSE_GROUNDED_DECISION_CONTEXT,
    SCORECARD_V1_BLOCK,
    STRESS_SCORECARD_CONTEXT_VERSION,
    STRESS_SCORECARD_SOURCE_LEGACY,
    STRESS_SCORECARD_SOURCE_V1,
    build_ai_commentary_context,
    write_ai_commentary_context_outputs,
)
from src.stress import run_stress


def _hedge_gap_v1_stress(
    *,
    protection_profile: str = "mostly_weak_protection",
    main_protection_status: str = "no_protection",
    hedge_gap_status: str = "not_applicable",
) -> dict:
    return {
        "loss_gate_mode": "diagnostic",
        "stress_conclusions": {"hedge_gap_status": hedge_gap_status},
        "hedge_gap_analysis_v1": {
            "version": "hedge_gap_analysis_v1",
            "block_status": "ok",
            "ruleset_version": "hedge_gap_rules_v1_2",
            "summary": {
                "protection_profile": protection_profile,
                "weakest_protection_area": "equity_crash_protection",
                "main_hedge_gap": {
                    "risk_type": "equity_crash_protection",
                    "linked_scenario_id": "equity_shock",
                    "protection_status": main_protection_status,
                    "offset_coverage_ratio": 0.0,
                    "portfolio_loss_pct": -0.12,
                },
                "main_hedge_gap_scenario_id": "equity_shock",
                "main_hedge_gap_offset_coverage_ratio": 0.0,
                "diagnosis_summary_en": "Main gap equity crash with no internal offset.",
            },
            "by_risk_type": [
                {
                    "risk_type": "equity_crash_protection",
                    "protection_status": main_protection_status,
                }
            ],
            "bridge_meta": {
                "block_2_4_hidden_exposure": True,
                "block_2_6_portfolio_weakness_map": False,
            },
        },
    }


def test_ai_commentary_context_lists_sources_and_guardrails() -> None:
    doc = build_ai_commentary_context(
        comparison={
            "comparison_baseline_candidate_id": "analysis_subject",
            "candidate_menu": {"factory_evidence_status": "fresh"},
        },
        current_vs_candidate={
            "view_mode": "one_candidate",
            "comparisons": [{"candidate_id": "equal_weight", "status": "available", "dimensions": [{}, {}]}],
            "warnings": [],
        },
        selection={
            "decision_status": "selected_candidate",
            "favored_candidate_id": "equal_weight",
            "warnings": [],
        },
        decision_verdict={
            "verdict_id": "rebalance_to_selected_candidate",
            "confidence": "medium",
            "confidence_limitations": [],
        },
        action={"action_status": "trades_for_review"},
    )

    assert doc["schema_version"] == AI_COMMENTARY_CONTEXT_VERSION
    assert doc["guardrails"]["does_not_call_llm"] is True
    assert doc["guardrails"]["does_not_calculate_metrics"] is True
    assert "new_metric_calculation" in doc["forbidden_claim_categories"]
    assert "unsupported_verdict" in doc["forbidden_claim_categories"]
    assert doc["source_artifacts"]["candidate_comparison"] == "candidate_comparison.json"
    assert doc["source_artifacts"]["decision_verdict"] == "decision_verdict.json"
    assert doc["warnings"] == []
    assert doc["purpose"] == PURPOSE_GROUNDED_DECISION_CONTEXT
    assert doc["grounding_phase"] == "post_compare"


def test_ai_commentary_context_includes_xray_and_stress_summary_refs() -> None:
    doc = build_ai_commentary_context(
        comparison={"comparison_baseline_candidate_id": "analysis_subject"},
        current_vs_candidate={"view_mode": "one_candidate", "comparisons": []},
        selection={"decision_status": "selected_candidate", "warnings": []},
        decision_verdict={"verdict_id": "rebalance_to_selected_candidate", "confidence": "medium"},
        portfolio_xray={
            "version": "portfolio_xray_v2",
            "diagnostic_only": True,
            "block_2_6_portfolio_weakness_map": {
                "status": "ok",
                "summary": "Weakness map completed.",
                "metadata": {"rule_version": "heuristic_v2"},
                "risk_types": [
                    {
                        "risk_type": "equity_shock",
                        "severity": "High",
                        "score_0_100": 72,
                        "short_diagnosis": "Equity shock risk is High.",
                        "why_status": "Severity is High because equity exposure is elevated.",
                        "next_tests": ["equity_shock"],
                    },
                    {
                        "risk_type": "rates_shock",
                        "severity": "Low",
                        "score_0_100": 20,
                        "short_diagnosis": "Rates shock risk is Low.",
                    },
                ],
            },
        },
        stress_report={
            "status": "ok",
            "loss_gate_mode": "diagnostic",
            "worst_scenario_loss_pct": -0.12,
            "stress_scorecard_v1": {"overall_status": "ok"},
        },
    )
    paths = {(ref["artifact"], ref["field_path"]) for ref in doc["evidence_references"]}
    assert ("portfolio_xray.json", "version") in paths
    assert ("portfolio_xray.json", "block_2_6_portfolio_weakness_map.status") in paths
    assert ("portfolio_xray.json", "block_2_6_portfolio_weakness_map.risk_types") in paths
    assert (
        "portfolio_xray.json",
        "block_2_6_portfolio_weakness_map.risk_types[0].short_diagnosis",
    ) in paths
    assert ("stress_report.json", "status") in paths
    assert ("stress_report.json", "loss_gate_mode") in paths
    assert ("stress_report.json", "worst_scenario_loss_pct") in paths
    assert ("stress_report.json", "stress_scorecard_v1.overall_status") in paths
    ctx = doc.get("current_portfolio_stress_scorecard_context")
    assert isinstance(ctx, dict)
    assert ctx["stress_scorecard_source"] == STRESS_SCORECARD_SOURCE_LEGACY
    assert doc["source_artifacts"]["portfolio_xray"] == "portfolio_xray.json"
    assert doc["source_artifacts"]["stress_report"] == "stress_report.json"


def test_ai_commentary_context_diagnosis_only_without_compare_warnings() -> None:
    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=None,
        selection=None,
        decision_verdict=None,
        problem_classification={
            "problems": [
                {
                    "problem_id": "concentration",
                    "severity": "moderate",
                    "status": "open",
                }
            ]
        },
        portfolio_xray={"version": "portfolio_xray_v2", "diagnostic_only": True},
        stress_report={"status": "ok", "loss_gate_mode": "diagnostic"},
    )
    assert doc["purpose"] == PURPOSE_DIAGNOSIS_GROUNDING_ONLY
    assert doc["grounding_phase"] == "diagnosis_only"
    assert not any(w.startswith("missing_required_source:") for w in doc["warnings"])
    paths = {ref["artifact"] for ref in doc["evidence_references"]}
    assert "portfolio_xray.json" in paths
    assert "stress_report.json" in paths
    assert "candidate_comparison.json" not in paths


def test_ai_commentary_context_includes_verdict_and_no_trade_evidence() -> None:
    doc = build_ai_commentary_context(
        comparison={"comparison_baseline_candidate_id": "analysis_subject"},
        current_vs_candidate={"view_mode": "one_candidate", "comparisons": []},
        selection={
            "decision_status": "no_material_rebalance",
            "favored_candidate_id": "risk_parity",
            "no_trade": {
                "evaluated": True,
                "baseline_candidate_id": "analysis_subject",
                "target_candidate_id": "risk_parity",
            },
        },
        decision_verdict={
            "verdict_id": "no_material_rebalance_recommended",
            "confidence": "medium",
        },
    )

    paths = {(ref["artifact"], ref["field_path"]) for ref in doc["evidence_references"]}
    assert ("selection_decision.json", "decision_status") in paths
    assert ("selection_decision.json", "no_trade") in paths
    assert ("decision_verdict.json", "verdict_id") in paths
    assert doc["commentary_topics"]["no_trade"]


def test_ai_commentary_context_warns_on_missing_required_sources() -> None:
    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=None,
        selection={"decision_status": "data_review_required", "warnings": ["missing_score_artifacts"]},
        decision_verdict={"verdict_id": "evidence_insufficient", "confidence_limitations": ["missing_score_artifacts"]},
    )

    assert doc["grounding_phase"] == "diagnosis_only"
    assert not any(w.startswith("missing_required_source:") for w in doc["warnings"])


def test_ai_commentary_context_warns_when_post_compare_bundle_incomplete() -> None:
    doc = build_ai_commentary_context(
        comparison={"comparison_baseline_candidate_id": "analysis_subject"},
        current_vs_candidate={"view_mode": "one_candidate", "comparisons": []},
        selection=None,
        decision_verdict=None,
    )
    assert doc["grounding_phase"] == "diagnosis_only"
    assert "missing_required_source:selection_decision.json" not in doc["warnings"]

    doc_full = build_ai_commentary_context(
        comparison={"comparison_baseline_candidate_id": "analysis_subject"},
        current_vs_candidate={"view_mode": "one_candidate", "comparisons": []},
        selection={"decision_status": "data_review_required", "warnings": ["missing_score_artifacts"]},
        decision_verdict={"verdict_id": "evidence_insufficient", "confidence_limitations": ["missing_score_artifacts"]},
    )
    assert doc_full["grounding_phase"] == "post_compare"
    assert "missing_required_source:candidate_comparison.json" not in doc_full["warnings"]
    assert "selection_decision.json:missing_score_artifacts" in doc_full["warnings"]
    assert (
        "decision_verdict.json:confidence_limit:missing_score_artifacts"
        in doc_full["warnings"]
    )


def test_ai_commentary_context_hedge_gap_v1_primary() -> None:
    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=None,
        selection=None,
        decision_verdict=None,
        stress_report=_hedge_gap_v1_stress(),
    )
    ctx = doc.get("hedge_gap_context")
    assert isinstance(ctx, dict)
    assert ctx["version"] == HEDGE_GAP_CONTEXT_VERSION
    assert ctx["hedge_gap_source"] == HEDGE_GAP_SOURCE_V1
    assert ctx["legacy_fallback_used"] is False
    assert ctx["main_hedge_gap_protection_status"] == "no_protection"
    assert ctx["bridges_applied"]["block_2_4_hidden_exposure"] is True

    paths = {(ref["artifact"], ref["field_path"]) for ref in doc["evidence_references"]}
    assert ("stress_report.json", "hedge_gap_analysis_v1.summary.main_hedge_gap") in paths
    assert "hedge_gap" in doc["commentary_topics"]


def test_ai_commentary_context_hedge_gap_legacy_fallback_without_v1() -> None:
    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=None,
        selection=None,
        decision_verdict=None,
        stress_report={
            "stress_conclusions": {"hedge_gap_status": "attention"},
        },
    )
    ctx = doc.get("hedge_gap_context")
    assert ctx["hedge_gap_source"] == HEDGE_GAP_SOURCE_LEGACY
    assert ctx["legacy_fallback_used"] is True
    paths = {(ref["artifact"], ref["field_path"]) for ref in doc["evidence_references"]}
    assert ("stress_report.json", "stress_conclusions.hedge_gap_status") in paths


def test_ai_commentary_context_includes_hedge_gap_comparison_post_compare() -> None:
    doc = build_ai_commentary_context(
        comparison={
            "comparison_baseline_candidate_id": "analysis_subject",
            "hedge_gap_comparison": {
                "version": "hedge_gap_comparison_v1",
                "status": "ok",
                "baseline_candidate_id": "analysis_subject",
                "hedge_gap_source": "hedge_gap_analysis_v1",
                "comparison_candidate_ids": ["equal_weight"],
                "pairwise": [
                    {
                        "candidate_id": "equal_weight",
                        "offset_coverage_ratio_delta": 0.15,
                        "main_gap_score_delta": -0.2,
                        "comparison_summary_en": "Equal weight improves offset coverage.",
                    }
                ],
            },
        },
        current_vs_candidate={"view_mode": "one_candidate", "comparisons": []},
        selection={"decision_status": "selected_candidate", "warnings": []},
        decision_verdict={"verdict_id": "rebalance_to_selected_candidate", "confidence": "medium"},
        stress_report=_hedge_gap_v1_stress(),
    )
    ctx = doc["hedge_gap_context"]
    assert ctx["comparison"]["status"] == "ok"
    assert ctx["comparison"]["pairwise"][0]["candidate_id"] == "equal_weight"
    paths = {(ref["artifact"], ref["field_path"]) for ref in doc["evidence_references"]}
    assert ("candidate_comparison.json", "hedge_gap_comparison.status") in paths
    assert ("candidate_comparison.json", "hedge_gap_comparison.pairwise") in paths


def _minimal_scorecard_v1_stress_report() -> dict:
    import pandas as pd

    idx = pd.date_range("2015-01-31", periods=120, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)}, index=idx)
    return run_stress(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.8, "BBB": 0.2},
        monthly_returns=monthly_returns,
        asset_betas=pd.DataFrame(
            columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]
        ),
        portfolio_betas={k: 0.0 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")},
        target_max_drawdown_pct=0.2,
        cash_proxy_ticker="",
        hedge_assets=["AAA"],
        loss_gate_mode="diagnostic",
    )


def test_ai_commentary_context_scorecard_v1_primary() -> None:
    stress = _minimal_scorecard_v1_stress_report()
    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=None,
        selection=None,
        decision_verdict=None,
        stress_report=stress,
    )
    ctx = doc["current_portfolio_stress_scorecard_context"]
    assert ctx["version"] == STRESS_SCORECARD_CONTEXT_VERSION
    assert ctx["stress_scorecard_source"] == STRESS_SCORECARD_SOURCE_V1
    assert ctx["legacy_fallback_used"] is False
    assert ctx.get("headline")
    paths = {(ref["artifact"], ref["field_path"]) for ref in doc["evidence_references"]}
    assert ("stress_report.json", f"{SCORECARD_V1_BLOCK}.stress_diagnosis.headline") in paths
    assert ("stress_report.json", "stress_scorecard_v1.overall_status") not in paths
    assert "stress_scorecard" in doc["commentary_topics"]
    assert not any(w.startswith("missing_stress_scorecard:") for w in doc["warnings"])


def test_ai_commentary_context_scorecard_legacy_fallback_without_v1() -> None:
    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=None,
        selection=None,
        decision_verdict=None,
        stress_report={
            "status": "ok",
            "loss_gate_mode": "diagnostic",
            "stress_scorecard_v1": {"overall_status": "DIAG_PASS", "overall_confidence": "medium"},
        },
    )
    ctx = doc["current_portfolio_stress_scorecard_context"]
    assert ctx["stress_scorecard_source"] == STRESS_SCORECARD_SOURCE_LEGACY
    assert ctx["legacy_fallback_used"] is True
    paths = {(ref["artifact"], ref["field_path"]) for ref in doc["evidence_references"]}
    assert ("stress_report.json", "stress_scorecard_v1.overall_status") in paths


def test_write_ai_commentary_context_outputs(tmp_path: Path) -> None:
    paths = write_ai_commentary_context_outputs(
        output_dir=tmp_path,
        comparison={"comparison_baseline_candidate_id": "analysis_subject"},
        current_vs_candidate={"view_mode": "diagnosis_only", "comparisons": []},
        selection={"decision_status": "inconclusive"},
        decision_verdict={"verdict_id": "test_another_candidate_or_review_evidence"},
    )

    path = paths["ai_commentary_context_json"]
    assert path == tmp_path / "ai_commentary_context.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == AI_COMMENTARY_CONTEXT_VERSION
