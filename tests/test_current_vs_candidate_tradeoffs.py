from __future__ import annotations

from src.current_vs_candidate import build_current_vs_candidate


def _candidate(
    cid: str,
    *,
    cagr: float,
    vol: float,
    dd: float,
    stress: float,
    weights: dict[str, float] | None = None,
) -> dict:
    return {
        "candidate_id": cid,
        "display_name": cid,
        "role": "analysis_subject" if cid == "analysis_subject" else "benchmark",
        "status": "available",
        "artifact_root": cid,
        "metrics": {
            "10y": {
                "cagr": cagr,
                "vol_annual": vol,
                "max_drawdown": dd,
                "sharpe": cagr / vol,
            }
        },
        "drawdown": {"max_drawdown": dd},
        "stress": {"scenarios": [{"scenario_id": "shock", "portfolio_pnl_pct": stress}]},
        "weights": weights or {},
        "missing_fields": [],
        "warnings": [],
        "source_files": ["snapshot_10y.json"],
    }


def test_tradeoff_summary_marks_small_improvements_not_material() -> None:
    comparison = {
        "comparison_baseline_candidate_id": "analysis_subject",
        "analysis_end": "2026-04-30",
        "primary_window": "10y",
        "candidates": [
            _candidate("analysis_subject", cagr=0.060, vol=0.100, dd=-0.200, stress=-0.100),
            _candidate("equal_weight", cagr=0.059, vol=0.098, dd=-0.195, stress=-0.095),
        ],
    }

    doc = build_current_vs_candidate(comparison, candidate_ids=["equal_weight"])

    row = doc["comparisons"][0]
    assert row["materiality_for_decision_review"] == {
        "status": "not_material",
        "is_material_enough": False,
        "reason": "no_material_improvement_detected",
        "supporting_improvements": [],
        "limiting_tradeoffs": [],
    }
    assert {item["field"] for item in row["what_improved"]} >= {
        "vol_annual",
        "max_drawdown",
        "worst_stress_loss",
    }
    assert row["tradeoff_summary"]["unavailable_metrics"]


def test_practicality_keeps_turnover_unavailable_without_weights() -> None:
    comparison = {
        "comparison_baseline_candidate_id": "analysis_subject",
        "analysis_end": "2026-04-30",
        "primary_window": "10y",
        "candidates": [
            _candidate("analysis_subject", cagr=0.060, vol=0.100, dd=-0.200, stress=-0.100),
            _candidate("equal_weight", cagr=0.060, vol=0.085, dd=-0.170, stress=-0.070),
        ],
    }

    doc = build_current_vs_candidate(comparison, candidate_ids=["equal_weight"])

    practicality = doc["comparisons"][0]["practicality"]
    assert practicality["turnover_required"]["status"] == "unavailable"
    assert practicality["turnover_required"]["unavailable_reason"] == (
        "baseline_or_candidate_weights_missing"
    )
    assert practicality["transaction_cost_assumption"] == {
        "status": "available",
        "transaction_cost_bps": 10.0,
        "transaction_cost_model": "bps_on_turnover_half_sum",
        "source": "action_engine_default",
    }
    assert practicality["estimated_transaction_cost_pct"] is None
