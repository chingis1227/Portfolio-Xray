from src.site_explanation_bundle import build_site_explanation_bundle


def _block_7_8_9_fixture() -> tuple[dict, dict, dict]:
    candidate_generation = {
        "schema_version": "candidate_generation_v1",
        "generation_status": "generated",
        "candidate": {
            "candidate_id": "equal_weight",
            "candidate_name": "Equal Weight",
            "goal": "Test whether diversification reduces concentration risk.",
            "hypothesis_to_test": "Equal weighting should reduce single-name concentration.",
            "method": "equal_weight",
            "method_variant": "equal_weight",
            "status": "generated",
            "success_criteria": ["Reduce max drawdown without adding high turnover"],
            "tradeoff_to_watch": "May reduce expected return.",
            "decision_boundary": "No action if turnover is too high.",
            "is_rebalance_recommendation": False,
        },
        "handoff_to_comparison": {
            "can_compare": True,
            "candidate_id": "equal_weight",
            "blocked_reason": None,
        },
    }
    current_vs_candidate = {
        "schema_version": "current_vs_candidate_v1",
        "view_mode": "one_candidate",
        "selected_candidate_ids": ["equal_weight"],
        "comparisons": [
            {
                "candidate_id": "equal_weight",
                "status": "available",
                "what_improved": [{"metric": "max_drawdown", "direction": "improved"}],
                "what_worsened": [{"metric": "cagr", "direction": "worsened"}],
                "risk_reduced": [{"metric": "concentration", "direction": "reduced"}],
                "risk_added": [{"metric": "return", "direction": "lower"}],
                "practicality": {
                    "turnover_required": {
                        "status": "available",
                        "turnover_half_sum_pct": 0.18,
                    },
                    "estimated_transaction_cost_pct": 0.001,
                },
                "success_criteria_result": {"overall_status": "met"},
                "materiality_for_decision_review": {
                    "status": "review_candidate",
                    "is_material_enough": True,
                },
            }
        ],
    }
    decision_verdict = {
        "schema_version": "decision_verdict_v1",
        "verdict_id": "no_material_rebalance_recommended",
        "selection_decision_status": "no_material_rebalance",
        "verdict_reason_id": "risk_improved_but_turnover_too_high",
        "confidence": "medium",
        "no_trade": {"evaluated": True, "applies": True},
        "rationale_summary": "Risk evidence improved, but practicality evidence blocks a rebalance verdict.",
        "confidence_limitations": [],
    }
    return candidate_generation, current_vs_candidate, decision_verdict


def test_site_explanation_populates_candidate_hierarchy_without_recommendation_language() -> None:
    candidate_generation, _, _ = _block_7_8_9_fixture()
    candidate_generation["candidate"]["success_criteria"] = [
        "Create a transparent reference point, not an action recommendation."
    ]
    candidate_generation["candidate"][
        "decision_boundary"
    ] = "This is not a rebalance recommendation. Actual rebalance decision is made only after comparison."

    doc = build_site_explanation_bundle(candidate_generation=candidate_generation)

    candidate = doc["screens"]["candidate"]
    assert any(
        item["id"] == "candidate.executive.diagnostic_candidate"
        and "diagnostic candidate" in item["text"]
        and "Equal weighting should reduce single-name concentration" in item["text"]
        for item in candidate["executive"]
    )
    assert {
        item["id"] for item in candidate["evidence"]
    } >= {
        "candidate.evidence.success_criteria",
        "candidate.evidence.tradeoff_to_watch",
        "candidate.evidence.decision_boundary",
    }
    assert any(item["id"] == "candidate.technical.method_handoff" for item in candidate["technical"])
    for level in candidate.values():
        for item in level:
            assert "recommend" not in item["text"].lower()
            if item["claim_type"] == "material_claim":
                assert item["source_refs"]


def test_site_explanation_populates_comparison_hierarchy_from_current_vs_candidate() -> None:
    _, current_vs_candidate, _ = _block_7_8_9_fixture()

    doc = build_site_explanation_bundle(current_vs_candidate=current_vs_candidate)

    comparison = doc["screens"]["comparison"]
    assert any(
        item["id"] == "comparison.executive.active_candidate"
        and "equal_weight" in item["text"]
        for item in comparison["executive"]
    )
    assert {
        item["id"] for item in comparison["evidence"]
    } >= {
        "comparison.evidence.what_improved",
        "comparison.evidence.what_worsened",
        "comparison.evidence.risk_reduced",
        "comparison.evidence.risk_added",
        "comparison.evidence.success_criteria",
        "comparison.evidence.practicality",
    }
    assert any(
        item["id"] == "comparison.technical.materiality_gate"
        and "review candidate" in item["text"]
        for item in comparison["technical"]
    )


def test_site_explanation_populates_verdict_only_with_comparison_evidence() -> None:
    _, current_vs_candidate, decision_verdict = _block_7_8_9_fixture()

    blocked_doc = build_site_explanation_bundle(decision_verdict=decision_verdict)
    assert not any(
        item["id"] == "verdict.executive.decision_support_outcome"
        for item in blocked_doc["screens"]["verdict"]["executive"]
    )
    assert any(
        item["id"] == "verdict.executive.blocked_until_comparison"
        for item in blocked_doc["screens"]["verdict"]["executive"]
    )

    doc = build_site_explanation_bundle(
        current_vs_candidate=current_vs_candidate,
        decision_verdict=decision_verdict,
    )

    verdict = doc["screens"]["verdict"]
    assert any(
        item["id"] == "verdict.executive.decision_support_outcome"
        and "keeping the current portfolio" in item["text"]
        for item in verdict["executive"]
    )
    assert {
        item["id"] for item in verdict["evidence"]
    } >= {
        "verdict.evidence.rationale_summary",
        "verdict.evidence.no_trade",
    }
    assert any(item["id"] == "verdict.technical.reason_and_limits" for item in verdict["technical"])
    for level in verdict.values():
        for item in level:
            if item["claim_type"] == "material_claim":
                assert item["source_refs"]
