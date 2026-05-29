"""Block 4 v2 contract shape tests (Session 01 — spec-only, no builder yet)."""

from __future__ import annotations

from scripts.core_mvp_validation_contract import (
    BLOCK_4_V2_RULESET_VERSION,
    CANDIDATE_LAUNCHPAD_V2_VERSION,
    PROBLEM_CLASSIFICATION_V2_VERSION,
    block_4_v2_diagnosis_handoff_violations,
    candidate_launchpad_v2_product_contract_violations,
    check_block_4_v2_diagnosis_handoff,
    check_candidate_launchpad_v2,
    check_problem_classification_v2,
    problem_classification_v2_product_contract_violations,
)


def _evidence_ref(**overrides: object) -> dict:
    base = {
        "evidence_id": "ev_test_01",
        "source_block": "block_3_3_hedge_gap_analysis",
        "source_artifact": "stress_report.json",
        "signal": "offset_coverage_ratio",
        "value": 0.21,
        "interpretation_en": "Only 21% of losses were offset by helping assets.",
        "why_relevant_to_problem_en": "Supports weak hedge behavior.",
        "evidence_path": "primary",
    }
    base.update(overrides)
    return base


def _problem_row(*, problem_id: str = "weak_crisis_resilience") -> dict:
    return {
        "problem_id": problem_id,
        "label_en": "Weak crisis resilience",
        "severity": "high",
        "confidence": "high",
        "short_diagnosis_en": "Large stress losses with limited internal offset.",
        "why_it_matters_en": "Severe scenarios dominate portfolio downside.",
        "evidence_refs": [_evidence_ref()],
        "negative_evidence_refs": [],
        "suggested_action_path_id": "improve_crisis_resilience",
        "secondary_action_path_ids": ["reduce_drawdown_risk"],
        "candidate_method_suggestions": [
            {
                "candidate_method_id": "minimum_cvar_constrained",
                "rationale_en": "Tests tail-loss reduction.",
            }
        ],
        "reasonable_paths_to_test": ["Improve crisis resilience", "Reduce drawdown"],
        "scoring": {
            "raw_score": 0.78,
            "decision_score": 0.85,
            "stress_confirmation": "confirmed",
            "materiality": "high",
        },
    }


def _minimal_problem_classification_v2() -> dict:
    primary = _problem_row()
    return {
        "schema_version": PROBLEM_CLASSIFICATION_V2_VERSION,
        "diagnostic_only": True,
        "diagnosis_mode": "current_portfolio_problem_classification",
        "ruleset_version": BLOCK_4_V2_RULESET_VERSION,
        "status": "ok",
        "generated_at": "2026-05-29T12:00:00Z",
        "analysis_end": "2026-04-30",
        "source_artifacts": {
            "portfolio_xray": "portfolio_xray.json",
            "stress_report": "stress_report.json",
        },
        "primary_problem": primary,
        "secondary_problems": [],
        "rejected_problems": [],
        "suggested_actions": [
            {
                "action_path_id": "improve_crisis_resilience",
                "label_en": "Improve crisis resilience",
                "source_problem_ids": ["weak_crisis_resilience"],
                "priority": 1,
            }
        ],
        "no_trade_or_monitoring_view": {
            "outcome": "proceed_to_launchpad",
            "headline_en": "Stress-confirmed weakness warrants testing a defensive hypothesis.",
            "reasons": ["Primary confidence is high"],
            "recommended_next_step": "select_launchpad_card",
            "launchpad_suppressed": False,
        },
        "data_quality_warnings": [],
        "diagnostics_meta": {
            "evidence_signal_count": 12,
            "problems_evaluated": 15,
            "problems_activated": 2,
        },
        "problems": [primary],
        "summary": {
            "primary_problem_id": "weak_crisis_resilience",
            "n_secondary": 0,
            "n_rejected": 0,
            "n_problems": 1,
            "current_portfolio_acceptable": False,
            "no_trade_outcome": "proceed_to_launchpad",
        },
        "warnings": [],
    }


def _minimal_launchpad_v2(*, source_problem_id: str = "weak_crisis_resilience") -> dict:
    return {
        "schema_version": CANDIDATE_LAUNCHPAD_V2_VERSION,
        "diagnostic_only": True,
        "ruleset_version": BLOCK_4_V2_RULESET_VERSION,
        "generated_at": "2026-05-29T12:00:00Z",
        "analysis_end": "2026-04-30",
        "source_artifacts": {"problem_classification": "problem_classification.json"},
        "launchpad_outcome": "proceed_to_launchpad",
        "cards": [
            {
                "card_id": "launchpad_01_improve_crisis_resilience",
                "title": "Improve Crisis Resilience",
                "goal": "Improve crisis resilience",
                "description": "Test whether stress-aware candidates reduce tail losses.",
                "source_problem_id": source_problem_id,
                "source_problem_label": "Weak crisis resilience",
                "rationale": {
                    "severity": "high",
                    "confidence": "high",
                    "evidence": [_evidence_ref()],
                },
                "suggested_methods": [{"candidate_method_id": "minimum_cvar_constrained"}],
                "generates_portfolio": False,
                "requires_user_action": True,
                "why_this_path_en": "Stress losses are material and hedge offset is weak.",
                "what_this_tests_en": "Whether tail losses can be reduced in severe scenarios.",
                "default_method": "minimum_cvar_constrained",
                "simple_constraints": [],
                "expected_tradeoff_to_check_en": "Lower tail loss vs lower expected return.",
                "not_a_recommendation_disclaimer_en": (
                    "This card suggests a hypothesis to test, not a buy or sell instruction."
                ),
                "when_to_skip_this_test_en": "Skip if stress losses are not material.",
                "priority_rank": 1,
            }
        ],
        "summary": {
            "n_cards": 1,
            "primary_card_id": "launchpad_01_improve_crisis_resilience",
            "has_portfolio_generating_options": True,
            "has_keep_current_option": False,
            "launchpad_outcome": "proceed_to_launchpad",
        },
        "warnings": [],
    }


def test_problem_classification_v2_contract_accepts_minimal_doc() -> None:
    doc = _minimal_problem_classification_v2()
    assert not problem_classification_v2_product_contract_violations(doc)
    checks = check_problem_classification_v2(doc)
    assert checks["product_contract_ok"] is True
    assert checks["primary_problem_id"] == "weak_crisis_resilience"


def test_problem_classification_v2_rejects_missing_evidence_refs() -> None:
    doc = _minimal_problem_classification_v2()
    doc["primary_problem"]["evidence_refs"] = []
    violations = problem_classification_v2_product_contract_violations(doc)
    assert any("evidence_refs" in row for row in violations)


def test_problem_classification_v2_rejects_too_many_secondary() -> None:
    doc = _minimal_problem_classification_v2()
    doc["secondary_problems"] = [_problem_row(problem_id="high_volatility") for _ in range(3)]
    violations = problem_classification_v2_product_contract_violations(doc)
    assert any("at most 2 secondary" in row for row in violations)


def test_launchpad_v2_contract_accepts_minimal_doc() -> None:
    doc = _minimal_launchpad_v2()
    assert not candidate_launchpad_v2_product_contract_violations(doc)
    checks = check_candidate_launchpad_v2(doc)
    assert checks["product_contract_ok"] is True
    assert checks["n_cards"] == 1


def test_launchpad_v2_rejects_missing_disclaimer() -> None:
    doc = _minimal_launchpad_v2()
    doc["cards"][0]["not_a_recommendation_disclaimer_en"] = "Buy this ETF."
    violations = candidate_launchpad_v2_product_contract_violations(doc)
    assert any("not_a_recommendation_disclaimer_en" in row for row in violations)


def test_block_4_v2_handoff_accepts_linked_artifacts() -> None:
    pc = _minimal_problem_classification_v2()
    lp = _minimal_launchpad_v2()
    assert not block_4_v2_diagnosis_handoff_violations(pc, lp)
    handoff = check_block_4_v2_diagnosis_handoff(pc, lp)
    assert handoff["handoff_ok"] is True


def test_block_4_v2_handoff_rejects_unknown_source_problem() -> None:
    pc = _minimal_problem_classification_v2()
    lp = _minimal_launchpad_v2(source_problem_id="high_volatility")
    violations = block_4_v2_diagnosis_handoff_violations(pc, lp)
    assert any("source_problem_id" in row for row in violations)
