from src.site_explanation_bundle import build_site_explanation_bundle


def test_site_explanation_populates_block_4_diagnosis_hierarchy() -> None:
    doc = build_site_explanation_bundle(
        problem_classification={
            "schema_version": "problem_classification_v3",
            "primary_diagnosis": {
                "label_en": "Duration / rates vulnerability",
                "confidence": "medium",
                "materiality": "high",
                "why_this_matters": "Structural duration exposure dominates risk.",
                "key_evidence": [
                    {
                        "source_artifact": "portfolio_xray.json",
                        "interpretation_en": "Fixed-income sleeve is 62.5% of capital.",
                    },
                    {
                        "source_artifact": "stress_report.json",
                        "interpretation_en": "Offset coverage ratio is 0.00 in the main hedge-gap scenario.",
                    },
                ],
            },
            "next_diagnostic_step": {
                "label": "Test lower duration sensitivity",
                "reason": "Rates stress is the main diagnostic pressure point.",
            },
        }
    )

    diagnosis = doc["screens"]["diagnosis"]

    assert any(
        item["id"] == "diagnosis.executive.primary_problem"
        and "Duration / rates vulnerability" in item["text"]
        for item in diagnosis["executive"]
    )
    assert {
        item["id"] for item in diagnosis["evidence"]
    } >= {
        "diagnosis.evidence.why_this_matters",
        "diagnosis.evidence.key_evidence_1",
        "diagnosis.evidence.key_evidence_2",
    }
    assert any(
        item["id"] == "diagnosis.technical.next_diagnostic_step"
        for item in diagnosis["technical"]
    )
    for level in diagnosis.values():
        for item in level:
            if item["claim_type"] == "material_claim":
                assert item["source_refs"]


def test_site_explanation_populates_xray_diagnosis_when_block_4_absent() -> None:
    doc = build_site_explanation_bundle(
        portfolio_xray={
            "version": "portfolio_xray_v2",
            "block_2_6_portfolio_weakness_map": {
                "summary": "Portfolio weakness map shows elevated pressure in two test areas.",
                "risk_types": [
                    {
                        "risk_type": "rates_shock",
                        "score_0_100": 48,
                        "severity": "Medium",
                        "short_diagnosis": "Rates shock / duration risk is Medium.",
                    },
                    {
                        "risk_type": "equity_shock",
                        "score_0_100": 72,
                        "severity": "High",
                        "short_diagnosis": "Equity shock risk is High.",
                    },
                ],
            },
        }
    )

    diagnosis = doc["screens"]["diagnosis"]

    assert any(
        item["id"] == "diagnosis.executive.weakness_map_summary"
        for item in diagnosis["executive"]
    )
    first_weakness = next(
        item for item in diagnosis["evidence"] if item["id"] == "diagnosis.evidence.weakness_1"
    )
    assert "Equity shock risk is High" in first_weakness["text"]
    assert first_weakness["source_refs"] == [
        {
            "artifact": "portfolio_xray.json",
            "field_path": "block_2_6_portfolio_weakness_map.risk_types[1]",
        }
    ]


def test_site_explanation_populates_stress_hierarchy_on_evidence_screen() -> None:
    doc = build_site_explanation_bundle(
        stress_report={
            "stress_conclusions": {
                "overall_confidence": "low",
                "worst_synthetic_scenario": {
                    "scenario_id": "equity_shock",
                    "portfolio_pnl_pct": -0.1883,
                    "loss_severity": "moderate",
                },
                "worst_historical_episode": {
                    "episode": "2022",
                    "max_dd": -0.1903,
                    "loss_severity": "moderate",
                    "data_quality": "reliable",
                },
                "top_loss_assets_worst_scenario": ["QQQ", "SPY", "SLV"],
            },
            "stress_scorecard_v1": {
                "n_synthetic_scenarios": 8,
                "n_historical_episodes": 5,
                "overall_confidence": "low",
            },
            "hedge_gap_analysis_v1": {
                "summary": {
                    "main_hedge_gap": {
                        "risk_type": "equity_shock_protection",
                        "offset_coverage_ratio": 0.25,
                    }
                }
            },
        }
    )

    evidence = doc["screens"]["evidence"]

    assert any(
        item["id"] == "evidence.executive.worst_synthetic_stress"
        and "-18.8%" in item["text"]
        and "equity_shock" in item["text"]
        for item in evidence["executive"]
    )
    assert {
        item["id"] for item in evidence["evidence"]
    } >= {
        "evidence.evidence.worst_historical_stress",
        "evidence.evidence.top_loss_assets",
        "evidence.evidence.main_hedge_gap",
    }
    assert any(
        item["id"] == "evidence.technical.stress_coverage"
        and "8 synthetic scenarios" in item["text"]
        for item in evidence["technical"]
    )
