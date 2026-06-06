from __future__ import annotations

from src.current_vs_candidate import build_current_vs_candidate


def _candidate(
    cid: str,
    *,
    cagr: float,
    vol: float,
    dd: float,
    stress: float,
    beta: float,
    weights: dict[str, float] | None = None,
    top1_weight: float | None = None,
    top3_weight: float | None = None,
    weight_hhi: float | None = None,
    top1_rc: float | None = None,
    top3_rc: float | None = None,
    rc_hhi: float | None = None,
) -> dict:
    return {
        "candidate_id": cid,
        "display_name": cid.replace("_", " ").title(),
        "role": "analysis_subject" if cid == "analysis_subject" else "benchmark",
        "status": "available",
        "artifact_root": cid,
        "metrics": {
            "10y": {
                "cagr": cagr,
                "vol_annual": vol,
                "max_drawdown": dd,
                "sharpe": cagr / vol,
                "beta_portfolio": beta,
            }
        },
        "drawdown": {"max_drawdown": dd},
        "stress": {"scenarios": [{"scenario_id": "shock", "portfolio_pnl_pct": stress}]},
        "weight_concentration": {
            "top1_weight_pct": top1_weight,
            "top3_weight_sum_pct": top3_weight,
            "weight_hhi": weight_hhi,
        },
        "diversification": {
            "top1_rc_pct": top1_rc,
            "top3_rc_sum_pct": top3_rc,
            "rc_hhi": rc_hhi,
        },
        "weights": weights or {},
        "construction_disclosure": {"disclosure_status": "available"},
        "missing_fields": [],
        "warnings": [],
        "source_files": ["snapshot_10y.json"],
    }


def test_current_vs_candidate_answers_block8_tradeoff_questions() -> None:
    comparison = {
        "schema_version": "candidate_comparison_v1",
        "comparison_baseline_candidate_id": "analysis_subject",
        "analysis_end": "2026-04-30",
        "primary_window": "10y",
        "candidates": [
            _candidate(
                "analysis_subject",
                cagr=0.07,
                vol=0.12,
                dd=-0.25,
                stress=-0.18,
                beta=0.85,
                weights={"VOO": 0.70, "BND": 0.30},
                top1_weight=0.70,
                top3_weight=1.00,
                weight_hhi=0.58,
                top1_rc=0.75,
                top3_rc=0.95,
                rc_hhi=0.62,
            ),
            _candidate(
                "equal_weight",
                cagr=0.065,
                vol=0.10,
                dd=-0.18,
                stress=-0.12,
                beta=0.65,
                weights={"VOO": 0.50, "BND": 0.50},
                top1_weight=0.50,
                top3_weight=1.00,
                weight_hhi=0.50,
                top1_rc=0.55,
                top3_rc=0.90,
                rc_hhi=0.52,
            ),
        ],
    }
    candidate_generation = {
        "schema_version": "candidate_generation_v1",
        "generation_status": "generated",
        "candidate": {
            "candidate_id": "equal_weight",
            "status": "generated",
            "success_criteria": ["Lower severe-stress loss.", "Lower largest holding weight."],
            "parameters": {"transaction_cost_bps": 15},
            "weights": {"VOO": 0.50, "BND": 0.50},
        },
        "handoff_to_comparison": {"can_compare": True, "reason": "valid_generated_candidate"},
    }

    doc = build_current_vs_candidate(
        comparison,
        candidate_ids=["equal_weight"],
        candidate_generation=candidate_generation,
    )

    row = doc["comparisons"][0]
    fields = {dim["field"]: dim for dim in row["dimensions"]}
    assert {"risk_return", "stress", "concentration", "factor_behavior"} <= {
        dim["category"] for dim in row["dimensions"]
    }
    assert fields["worst_stress_loss"]["direction"] == "improved"
    assert fields["weight_top1_weight_pct"]["direction"] == "improved"
    assert fields["beta_portfolio"]["direction"] == "improved"
    assert fields["cagr"]["direction"] == "worse"
    assert [item["field"] for item in row["risk_reduced"]] == [
        "vol_annual",
        "max_drawdown",
        "worst_stress_loss",
        "weight_top1_weight_pct",
        "weight_hhi",
        "rc_top1_rc_pct",
        "rc_top3_rc_sum_pct",
        "rc_hhi",
        "beta_portfolio",
    ]
    assert row["practicality"]["turnover_required"]["status"] == "available"
    assert row["practicality"]["turnover_required"]["turnover_half_sum_pct"] == 0.2
    assert row["practicality"]["transaction_cost_assumption"]["transaction_cost_bps"] == 15
    assert row["practicality"]["estimated_transaction_cost_pct"] == 0.0003
    assert row["success_criteria_result"]["overall_status"] == "met"
    assert row["materiality_for_decision_review"]["status"] == "review_candidate"
    assert row["materiality_for_decision_review"]["is_material_enough"] is True
    assert doc["source_artifacts"]["candidate_generation"] == "candidate_generation.json"
    assert "turnover_required" in doc["comparison_questions_answered"]
