from __future__ import annotations

from src.current_vs_candidate import build_current_vs_candidate


def _row(cid: str, *, stress: float, drawdown: float, vol: float = 0.10) -> dict:
    return {
        "candidate_id": cid,
        "display_name": cid,
        "role": "analysis_subject" if cid == "analysis_subject" else "benchmark",
        "status": "available",
        "artifact_root": cid,
        "metrics": {
            "10y": {
                "cagr": 0.06,
                "vol_annual": vol,
                "max_drawdown": drawdown,
                "sharpe": 0.60,
            }
        },
        "drawdown": {"max_drawdown": drawdown},
        "stress": {"scenarios": [{"scenario_id": "shock", "portfolio_pnl_pct": stress}]},
        "missing_fields": [],
        "warnings": [],
        "source_files": ["snapshot_10y.json"],
    }


def _generation(candidate_id: str, success_criteria: list[str]) -> dict:
    return {
        "generation_status": "generated",
        "candidate": {
            "candidate_id": candidate_id,
            "status": "generated",
            "success_criteria": success_criteria,
            "weights": {"VOO": 0.5, "BND": 0.5},
        },
        "handoff_to_comparison": {"can_compare": True, "reason": "valid_generated_candidate"},
    }


def test_success_criteria_are_not_faked_when_mapped_metric_worsens() -> None:
    comparison = {
        "comparison_baseline_candidate_id": "analysis_subject",
        "analysis_end": "2026-04-30",
        "primary_window": "10y",
        "candidates": [
            _row("analysis_subject", stress=-0.10, drawdown=-0.20),
            _row("minimum_cvar_constrained", stress=-0.14, drawdown=-0.16),
        ],
    }
    generation = _generation("minimum_cvar_constrained", ["Lower severe-stress loss."])

    doc = build_current_vs_candidate(
        comparison,
        candidate_ids=["minimum_cvar_constrained"],
        candidate_generation=generation,
    )

    result = doc["comparisons"][0]["success_criteria_result"]
    assert result["overall_status"] == "not_met"
    assert result["criteria"][0]["status"] == "not_met"
    assert result["criteria"][0]["metric_field"] == "worst_stress_loss"
    assert doc["comparisons"][0]["materiality_for_decision_review"]["reason"] == (
        "success_criteria_not_met"
    )


def test_success_criteria_are_marked_unavailable_when_metric_is_missing() -> None:
    comparison = {
        "comparison_baseline_candidate_id": "analysis_subject",
        "analysis_end": "2026-04-30",
        "primary_window": "10y",
        "candidates": [
            _row("analysis_subject", stress=-0.10, drawdown=-0.20),
            {
                **_row("equal_weight", stress=-0.08, drawdown=-0.18),
                "stress": {},
            },
        ],
    }
    generation = _generation("equal_weight", ["Lower severe-stress loss."])

    doc = build_current_vs_candidate(
        comparison,
        candidate_ids=["equal_weight"],
        candidate_generation=generation,
    )

    result = doc["comparisons"][0]["success_criteria_result"]
    assert result["overall_status"] == "unavailable"
    assert result["criteria"][0] == {
        "criterion": "Lower severe-stress loss.",
        "status": "unavailable",
        "reason": "mapped_metric_unavailable",
        "metric_field": "worst_stress_loss",
    }


def test_unmapped_success_criteria_are_not_evaluated() -> None:
    comparison = {
        "comparison_baseline_candidate_id": "analysis_subject",
        "analysis_end": "2026-04-30",
        "primary_window": "10y",
        "candidates": [
            _row("analysis_subject", stress=-0.10, drawdown=-0.20),
            _row("equal_weight", stress=-0.08, drawdown=-0.18),
        ],
    }
    generation = _generation("equal_weight", ["Create a transparent reference point."])

    doc = build_current_vs_candidate(
        comparison,
        candidate_ids=["equal_weight"],
        candidate_generation=generation,
    )

    result = doc["comparisons"][0]["success_criteria_result"]
    assert result["overall_status"] == "not_evaluated"
    assert result["criteria"][0]["reason"] == "criterion_not_mapped_to_available_metric"
