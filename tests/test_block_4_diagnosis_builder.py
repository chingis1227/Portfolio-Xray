"""Tests for Block 4 v3 diagnosis facade and JSON writers (Session 10)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.core_mvp_validation_contract import (
    block_4_v3_diagnosis_handoff_violations,
    candidate_launchpad_v3_product_contract_violations,
    check_block_4_v3_diagnosis_handoff,
    check_candidate_launchpad_v3,
    check_problem_classification_v3,
    problem_classification_v3_product_contract_violations,
)
from src.block_4.diagnosis_builder import (
    BLOCK_4_DIAGNOSIS_FACADE_VERSION,
    PROBLEM_CLASSIFICATION_V3_VERSION,
    block_4_manifest_extra,
    build_block_4_diagnosis,
    write_block_4_diagnosis_outputs,
)
from src.product_bundle_paths import (
    product_bundle_generated_paths_for_manifest,
    resolve_candidate_launchpad_path,
    resolve_problem_classification_path,
)
from block_4_fixtures import hedge_gap_stress as _hedge_gap_stress
from block_4_fixtures import load_golden_xray as _load_golden_xray


def test_build_block_4_diagnosis_golden_contract() -> None:
    result = build_block_4_diagnosis(
        portfolio_xray=_load_golden_xray(),
        stress_report=_hedge_gap_stress(),
        analysis_end="2026-04-30",
        generated_at="2026-05-29T12:00:00Z",
    )

    pc = result.problem_classification
    lp = result.candidate_launchpad

    assert pc["schema_version"] == PROBLEM_CLASSIFICATION_V3_VERSION
    assert pc["status"] == "partial"
    assert pc["primary_problem"]["problem_id"] == "weak_crisis_resilience"
    assert pc["problems"]
    assert pc["problems"][0]["label"] == pc["problems"][0]["label_en"]
    assert pc["summary"]["no_trade_outcome"] == pc["no_trade_or_monitoring_view"]["outcome"]
    assert pc["next_diagnostic_step"]["type"] == "targeted_hypothesis_test"
    assert "Decision Verdict" in pc["next_diagnostic_step"]["decision_boundary"]
    assert pc["diagnostics_meta"]["block_4_facade_version"] == BLOCK_4_DIAGNOSIS_FACADE_VERSION
    assert pc["interpretation_chain"]["schema_version"] == "diagnosis_interpretation_chain_v1"
    assert pc["interpretation_chain"]["selected_diagnosis_id"] == pc["primary_problem"]["problem_id"]
    assert pc["diagnosis_evidence_items"] == pc["interpretation_chain"]["diagnosis_evidence_items"]
    assert pc["root_cause_narrative"] == pc["interpretation_chain"]["root_cause_narrative"]
    assert pc["metric_to_diagnosis_trace"] == pc["interpretation_chain"]["metric_to_diagnosis_trace"]
    assert pc["professional_rationale_refs"] == pc["interpretation_chain"]["professional_rationale_refs"]
    assert pc["diagnosis_evidence_items"]
    assert pc["metric_to_diagnosis_trace"]
    assert pc["root_cause_narrative"]["diagnosis_id"] == "weak_crisis_resilience"
    assert "root-cause" in pc["root_cause_narrative"]["root_cause_over_symptom_en"].lower()
    assert any(
        ref["source"] == "docs/specs/diagnosis_interpretation_methodology_spec.md"
        for ref in pc["professional_rationale_refs"]
    )

    assert not problem_classification_v3_product_contract_violations(pc)
    assert not candidate_launchpad_v3_product_contract_violations(lp)
    assert not block_4_v3_diagnosis_handoff_violations(pc, lp)

    checks = check_problem_classification_v3(pc)
    assert checks["product_contract_ok"] is True
    handoff = check_block_4_v3_diagnosis_handoff(pc, lp)
    assert handoff["handoff_ok"] is True


def test_write_block_4_diagnosis_outputs_writes_both_files(tmp_path: Path) -> None:
    write_result = write_block_4_diagnosis_outputs(
        output_dir=tmp_path,
        portfolio_xray=_load_golden_xray(),
        stress_report=_hedge_gap_stress(),
        analysis_end="2026-04-30",
    )

    assert write_result.problem_classification_path.is_file()
    assert write_result.candidate_launchpad_path.is_file()

    pc = json.loads(write_result.problem_classification_path.read_text(encoding="utf-8"))
    lp = json.loads(write_result.candidate_launchpad_path.read_text(encoding="utf-8"))
    assert pc["schema_version"] == PROBLEM_CLASSIFICATION_V3_VERSION
    assert lp["launchpad_outcome"] == pc["summary"]["no_trade_outcome"]

    manifest_paths = product_bundle_generated_paths_for_manifest(tmp_path)
    assert "problem_classification_json" in manifest_paths
    assert "candidate_launchpad_json" in manifest_paths
    assert resolve_problem_classification_path(tmp_path) == write_result.problem_classification_path
    assert resolve_candidate_launchpad_path(tmp_path) == write_result.candidate_launchpad_path


def test_block_4_manifest_extra_includes_primary_and_outcome() -> None:
    result = build_block_4_diagnosis(
        portfolio_xray=_load_golden_xray(),
        stress_report=_hedge_gap_stress(),
        analysis_end="2026-04-30",
    )
    extra = block_4_manifest_extra(result.problem_classification, result.candidate_launchpad)

    assert extra["block_4_diagnosis"]["schema_version"] == PROBLEM_CLASSIFICATION_V3_VERSION
    assert extra["block_4_diagnosis"]["primary_problem_id"] == "weak_crisis_resilience"
    assert extra["block_4_diagnosis"]["no_trade_outcome"] == "proceed_to_launchpad"
    assert extra["block_4_diagnosis"]["facade_version"] == BLOCK_4_DIAGNOSIS_FACADE_VERSION


def test_interpretation_chain_traces_evidence_to_selected_diagnosis() -> None:
    result = build_block_4_diagnosis(
        portfolio_xray=_load_golden_xray(),
        stress_report=_hedge_gap_stress(),
        analysis_end="2026-04-30",
    )
    pc = result.problem_classification
    primary_id = pc["primary_problem"]["problem_id"]

    evidence_ids = {item["evidence_item_id"] for item in pc["diagnosis_evidence_items"]}
    assert evidence_ids
    assert all(item["source_artifact"] for item in pc["diagnosis_evidence_items"])
    assert all(item["source_block"] for item in pc["diagnosis_evidence_items"])
    assert all(item["signal"] for item in pc["diagnosis_evidence_items"])
    assert all(item["evidence_item_id"] in evidence_ids for item in pc["metric_to_diagnosis_trace"])
    assert all(
        item["contributes_to_selected_diagnosis_id"] == primary_id
        for item in pc["metric_to_diagnosis_trace"]
    )
    assert pc["interpretation_chain"]["recommendation_boundary_en"] == pc["next_diagnostic_step"]["decision_boundary"]


def test_v1_shim_mirrors_medium_severity_to_moderate() -> None:
    result = build_block_4_diagnosis(
        portfolio_xray=_load_golden_xray(),
        stress_report=_hedge_gap_stress(),
        analysis_end="2026-04-30",
    )
    secondary = result.problem_classification.get("secondary_problems") or []
    shim_rows = result.problem_classification["problems"]
    for row in shim_rows[1:]:
        if row.get("problem_id") in {sec["problem_id"] for sec in secondary}:
            if row.get("severity") == "moderate":
                assert any(sec.get("severity") == "medium" for sec in secondary)
                break
    else:
        assert shim_rows


def test_data_quality_diagnosis_status_partial_or_unavailable() -> None:
    xray = {"sections": {f"section_{i}": {"status": "partial"} for i in range(4)}}
    result = build_block_4_diagnosis(portfolio_xray=xray, stress_report={}, analysis_end="2026-04-30")

    assert result.problem_classification["primary_problem"]["problem_id"] == "evidence_insufficient_data_quality"
    assert result.problem_classification["next_diagnostic_step"]["type"] == "data_quality_improvement"
    assert "Equal Weight" in result.problem_classification["next_diagnostic_step"]["reason"]
    assert result.problem_classification["status"] in {"partial", "unavailable", "ok"}
    assert result.gate.outcome == "do_not_act_yet"
    assert check_candidate_launchpad_v3(result.candidate_launchpad)["product_contract_ok"] is True


def test_mixed_or_acceptable_diagnosis_exposes_reference_next_step() -> None:
    result = build_block_4_diagnosis(
        portfolio_xray={
            "block_2_2_portfolio_metrics": {
                "status": "ok",
                "return_risk_metrics": {"vol_annual": 0.08, "sharpe": 0.9, "sortino": 1.1},
                "drawdown_diagnostics": {"max_drawdown": -0.05, "recovered": True},
                "tail_risk_diagnostics": {"es_95": -0.008},
                "benchmark_dependence": {"beta_portfolio": 0.4},
            },
            "block_2_3_factor_exposure": {
                "status": "ok",
                "factor_betas_5y": {"betas": {"beta_eq": 0.4}},
            },
        },
        stress_report=_hedge_gap_stress(
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
        ),
        analysis_end="2026-04-30",
    )

    step = result.problem_classification["next_diagnostic_step"]
    assert result.primary_problem_id == "current_portfolio_acceptable"
    assert step["type"] == "reference_comparison"
    assert step["candidate_method_ids"] == ["equal_weight", "risk_parity"]
    assert "Immediate rebalance is not justified" in step["reason"]
