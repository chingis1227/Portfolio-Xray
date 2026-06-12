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


def test_ai_commentary_context_grounds_direct_block7_8_vertical_loop() -> None:
    candidate_generation = {
        "schema_version": "candidate_generation_v1",
        "generation_status": "generated",
        "candidate": {
            "candidate_id": "equal_weight",
            "candidate_name": "Equal Weight",
            "source_card_id": "card_1",
            "source_diagnosis_id": "concentration_risk",
            "source_launchpad_card_type": "targeted_hypothesis",
            "goal": "Test whether diversification reduces concentration risk.",
            "hypothesis_to_test": "Equal weighting should reduce single-name concentration.",
            "method": "equal_weight",
            "method_variant": "equal_weight",
            "capped": True,
            "uncapped": False,
            "min_asset_weight": 0.0,
            "max_asset_weight": 0.2,
            "constraint_preset": "balanced",
            "status": "generated",
            "success_criteria": ["Reduce max drawdown without adding high turnover"],
            "tradeoff_to_watch": "May reduce expected return.",
            "decision_boundary": "No action if turnover is too high.",
            "is_rebalance_recommendation": False,
        },
        "source_builder_setup": {
            "candidate_setup_id": "setup_1",
            "builder_prefill_id": "prefill_1",
            "source_card_id": "card_1",
            "source_diagnosis_id": "concentration_risk",
            "validation_status": "valid",
            "can_generate_candidate": True,
        },
        "method_availability": {
            "method": "equal_weight",
            "method_variant": "equal_weight",
            "mode": "capped",
            "available": True,
            "availability_status": "available",
        },
        "handoff_to_comparison": {
            "can_compare": True,
            "blocked_reason": None,
            "candidate_id": "equal_weight",
        },
        "warnings": ["diagnostic_candidate_not_recommendation"],
    }
    current_vs_candidate = {
        "view_mode": "one_candidate",
        "selected_candidate_ids": ["equal_weight"],
        "comparisons": [
            {
                "candidate_id": "equal_weight",
                "status": "available",
                "dimensions": [{"status": "available"}],
                "what_improved": [{"metric": "max_drawdown", "direction": "improved"}],
                "what_worsened": [{"metric": "cagr", "direction": "worsened"}],
                "what_stayed_similar": [],
                "risk_reduced": [{"metric": "concentration", "direction": "reduced"}],
                "risk_added": [{"metric": "return", "direction": "lower"}],
                "practicality": {
                    "turnover_required": {
                        "status": "available",
                        "turnover_half_sum_pct": 0.18,
                    },
                    "transaction_cost_bps": 10,
                    "transaction_cost_source": "action_engine_default",
                    "estimated_transaction_cost_pct": 0.018,
                },
                "success_criteria_result": {"overall_status": "met"},
                "materiality_for_decision_review": {
                    "status": "review_candidate",
                    "is_material_enough": True,
                },
                "tradeoff_summary": "Improves concentration but may lower return.",
            }
        ],
        "warnings": [],
    }
    decision_verdict = {
        "verdict_id": "no_material_rebalance_recommended",
        "selection_decision_status": "no_material_rebalance",
        "verdict_reason_id": "risk_improved_but_turnover_too_high",
        "reviewed_candidate_id": "equal_weight",
        "selected_candidate_id": None,
        "confidence": "medium",
        "no_trade": {
            "evaluated": True,
            "applies": True,
            "source": {"reason_id": "risk_improved_but_turnover_too_high"},
        },
        "rationale_summary": "Risk improved, but practicality blocks a rebalance verdict.",
        "confidence_limitations": [],
    }

    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=current_vs_candidate,
        selection=None,
        decision_verdict=decision_verdict,
        candidate_generation=candidate_generation,
    )

    assert "candidate_generation.json" in doc["allowed_source_artifacts"]
    assert doc["source_artifacts"]["candidate_generation"] == "candidate_generation.json"
    assert doc["source_artifacts"]["portfolio_alternatives_builder"] is None
    assert doc["source_artifacts"]["selection_decision"] is None
    assert doc["grounding_phase"] == "post_compare"
    assert doc["purpose"] == PURPOSE_GROUNDED_DECISION_CONTEXT
    assert doc["client_explanation_draft"]["does_not_call_llm"] is True
    assert len(doc["client_explanation_draft"]["sentences"]) == 11
    assert doc["light_decision_journal"]["decision_verdict"] == "no_material_rebalance_recommended"
    assert "candidate_generation.json:diagnostic_candidate_not_recommendation" in doc["warnings"]
    assert not any("selection_decision.json" in warning for warning in doc["warnings"])
    assert not any("candidate_comparison.json" in warning for warning in doc["warnings"])

    paths = {(ref["artifact"], ref["field_path"]) for ref in doc["evidence_references"]}
    assert ("candidate_generation.json", "generation_status") in paths
    assert ("candidate_generation.json", "candidate.hypothesis_to_test") in paths
    assert ("candidate_generation.json", "candidate.success_criteria") in paths
    assert ("current_vs_candidate.json", "comparisons[0].what_improved") in paths
    assert ("current_vs_candidate.json", "comparisons[0].what_worsened") in paths
    assert ("current_vs_candidate.json", "comparisons[0].practicality") in paths
    assert ("current_vs_candidate.json", "comparisons[0].success_criteria_result") in paths
    assert ("decision_verdict.json", "verdict_reason_id") in paths
    assert ("decision_verdict.json", "no_trade") in paths
    for topic in (
        "diagnosis",
        "hypothesis_tested",
        "candidate_generated",
        "improvements",
        "deteriorations",
        "turnover_cost",
        "success_criteria_result",
        "decision_verdict",
        "no_trade_rationale",
        "monitoring_trigger",
        "light_decision_journal",
    ):
        assert topic in doc["commentary_topics"]


def test_ai_commentary_context_supports_blocked_builder_client_explanation() -> None:
    builder = {
        "status": "blocked",
        "reason": "data_quality_blocker",
        "can_generate_candidate": False,
        "selected_card_id": "launchpad_01_keep_current_portfolio_and_monitor",
        "validation": {
            "validation_status": "blocked_by_data_quality",
            "can_generate_candidate": False,
            "validation_errors": ["data_quality_blocker"],
        },
        "builder_prefill": {
            "source_card_id": "launchpad_01_keep_current_portfolio_and_monitor",
            "source_diagnosis_id": "weak_crisis_resilience",
            "goal": "Keep current portfolio and monitor",
            "hypothesis_to_test": "Do not generate a candidate yet; monitor stress evidence.",
            "success_criteria": ["No material deterioration in monitored risks."],
            "when_to_skip": "Skip if worst stress loss is no longer material.",
        },
    }
    doc = build_ai_commentary_context(
        comparison=None,
        current_vs_candidate=None,
        selection=None,
        decision_verdict=None,
        problem_classification={
            "primary_diagnosis": {
                "diagnosis_id": "weak_crisis_resilience",
                "thesis_en": "Weak crisis resilience: worst synthetic stress loss is material.",
            }
        },
        candidate_launchpad={
            "cards": [
                {
                    "card_id": "launchpad_01_keep_current_portfolio_and_monitor",
                    "goal": "Keep current portfolio and monitor",
                    "launch_status": "monitor_or_resolve_data",
                    "success_criteria": ["No material deterioration in monitored risks."],
                }
            ]
        },
        portfolio_alternatives_builder=builder,
        stress_report={"status": "ok", "loss_gate_mode": "diagnostic", "worst_scenario_loss_pct": -0.4},
    )

    assert doc["grounding_phase"] == "diagnosis_only"
    assert doc["source_artifacts"]["portfolio_alternatives_builder"] == "portfolio_alternatives_builder.json"
    paths = {(ref["artifact"], ref["field_path"]) for ref in doc["evidence_references"]}
    assert ("portfolio_alternatives_builder.json", "status") in paths
    assert ("portfolio_alternatives_builder.json", "builder_prefill") in paths

    draft = doc["client_explanation_draft"]
    assert draft["does_not_call_llm"] is True
    assert len(draft["sentences"]) == 11
    candidate_logic = next(row for row in draft["sentences"] if row["topic"] == "selected_candidate_logic")
    assert candidate_logic["evidence_status"] == "blocked"
    assert "data_quality_blocker" in candidate_logic["text"]
    journal = doc["light_decision_journal"]
    assert journal["selected_candidate"]["builder_status"] == "blocked"
    assert journal["selected_candidate"]["can_generate_candidate"] is False


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
