from __future__ import annotations

import json
from pathlib import Path

from src.assumption_sensitivity import (
    SCHEMA_VERSION,
    build_assumption_sensitivity,
    write_assumption_sensitivity_outputs,
)
from src.config_schema import validate_config
from src.selection_engine import build_selection_decision


def _metrics(**overrides) -> dict:
    base = {
        "cagr": 0.08,
        "vol_annual": 0.12,
        "max_drawdown": -0.22,
        "sharpe": 0.5,
    }
    base.update(overrides)
    return {"3y": dict(base), "5y": dict(base), "10y": dict(base)}


def _cand(
    cid: str,
    *,
    status: str = "available",
    role: str = "benchmark",
    sharpe_10y: float = 0.5,
    stress_pnl: float = -0.15,
    mandate_valid: bool = True,
) -> dict:
    metrics = _metrics(sharpe=sharpe_10y)
    return {
        "candidate_id": cid,
        "display_name": cid.replace("_", " ").title(),
        "role": role,
        "status": status,
        "metrics": metrics,
        "mandate": {"portfolio_valid": mandate_valid},
        "stress": {
            "overall": "DIAG_PASS",
            "scenarios": [{"scenario_id": "s1", "portfolio_pnl_pct": stress_pnl}],
        },
    }


def _health(*rows: tuple[str, float, int]) -> dict:
    return {
        "schema_version": "portfolio_health_score_v1",
        "candidates": [
            {
                "candidate_id": cid,
                "total_score": score,
                "score_status": "scored",
                "health_rank": rank,
            }
            for cid, score, rank in rows
        ],
    }


def _robust(*rows: tuple[str, float, int]) -> dict:
    return {
        "schema_version": "robustness_scorecard_v1",
        "candidates": [
            {
                "candidate_id": cid,
                "total_score": score,
                "score_status": "scored",
                "robustness_rank": rank,
            }
            for cid, score, rank in rows
        ],
    }


def _comparison_three_way() -> dict:
    return {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": "2025-12-31",
        "candidates": [
            _cand("policy", role="policy", sharpe_10y=0.55),
            _cand("risk_parity", role="benchmark", sharpe_10y=0.48),
            _cand("equal_weight", role="benchmark", sharpe_10y=0.52),
            _cand("current", role="user_current", sharpe_10y=0.4),
        ],
    }


def test_baseline_selection_matches_selection_decision() -> None:
    comparison = _comparison_three_way()
    health = _health(("policy", 70.0, 2), ("risk_parity", 75.0, 1), ("equal_weight", 72.0, 3))
    robust = _robust(("policy", 75.0, 1), ("risk_parity", 70.0, 2), ("equal_weight", 72.0, 3))
    selection = build_selection_decision(comparison, health=health, robustness=robust)
    assert selection is not None
    doc = build_assumption_sensitivity(
        comparison,
        selection=selection,
        health=health,
        robustness=robust,
    )
    assert doc["schema_version"] == SCHEMA_VERSION
    baseline_row = next(
        r for r in doc["tier_a_variants"] if r["variant_id"] == "baseline_selection"
    )
    assert baseline_row["status"] == "evaluated"
    assert baseline_row["effective_favored_id"] == selection["favored_candidate_id"]
    assert baseline_row["matches_baseline_favored"] is True


def test_health_dominant_vs_robust_dominant_can_flip() -> None:
    comparison = {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": "2025-12-31",
        "candidates": [
            _cand("risk_parity", role="benchmark"),
            _cand("equal_weight", role="benchmark"),
        ],
    }
    health = _health(("risk_parity", 90.0, 1), ("equal_weight", 75.0, 2))
    robust = _robust(("risk_parity", 55.0, 2), ("equal_weight", 70.0, 1))
    selection = {
        "favored_candidate_id": "equal_weight",
        "favored_display_name": "Equal Weight",
        "decision_status": "selected_candidate",
    }
    doc = build_assumption_sensitivity(
        comparison,
        selection=selection,
        health=health,
        robustness=robust,
    )
    health_dom = next(r for r in doc["tier_a_variants"] if r["variant_id"] == "health_dominant")
    robust_dom = next(r for r in doc["tier_a_variants"] if r["variant_id"] == "robust_dominant")
    assert health_dom["effective_favored_id"] == "risk_parity"
    assert robust_dom["effective_favored_id"] == "equal_weight"
    assert health_dom["effective_favored_id"] != robust_dom["effective_favored_id"]


def test_composite_no_policy_default_can_differ_from_baseline() -> None:
    comparison = _comparison_three_way()
    health = _health(("policy", 72.0, 2), ("risk_parity", 78.0, 1), ("equal_weight", 70.0, 3))
    robust = _robust(("policy", 74.0, 2), ("risk_parity", 76.0, 1), ("equal_weight", 71.0, 3))
    selection = build_selection_decision(comparison, health=health, robustness=robust)
    assert selection["favored_candidate_id"] == "policy"
    doc = build_assumption_sensitivity(
        comparison,
        selection=selection,
        health=health,
        robustness=robust,
    )
    no_policy = next(
        r
        for r in doc["tier_a_variants"]
        if r["variant_id"] == "composite_only_no_policy_default"
    )
    assert no_policy["effective_favored_id"] == "risk_parity"
    assert doc["policy_default_sensitive"] is True


def test_tier_b_skipped_when_sharpe_missing() -> None:
    comparison = {
        "analysis_end": "2025-12-31",
        "candidates": [
            {
                "candidate_id": "policy",
                "display_name": "Policy",
                "role": "policy",
                "status": "available",
                "metrics": {"10y": {"cagr": 0.08}},
                "mandate": {"portfolio_valid": True},
                "stress": {"scenarios": []},
            }
        ],
    }
    selection = {"favored_candidate_id": "policy", "decision_status": "selected_candidate"}
    doc = build_assumption_sensitivity(comparison, selection=selection)
    sharpe_10y = next(r for r in doc["tier_b_variants"] if r["variant_id"] == "sharpe_rank_10y")
    assert sharpe_10y["status"] == "skipped"


def test_missing_selection_selection_unavailable() -> None:
    comparison = _comparison_three_way()
    doc = build_assumption_sensitivity(comparison, selection=None)
    assert doc["sensitivity_status"] == "selection_unavailable"
    assert "selection_unavailable" in doc["warnings"]


def test_pipeline_emits_after_tradeoff(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    rp = tmp_path / "risk parity portfolio"
    rp.mkdir()
    for folder, weights in (
        (main, {"VOO": 0.6, "BND": 0.4}),
        (eq, {"VOO": 0.5, "BND": 0.5}),
        (rp, {"VOO": 0.55, "BND": 0.45}),
    ):
        with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metrics": _metrics()["10y"],
                    "final_weights_total": weights,
                },
                f,
            )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    from src.candidate_comparison import write_candidate_comparison_outputs

    paths = write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    assert paths.get("assumption_sensitivity_json", Path()).is_file()
    with open(paths["assumption_sensitivity_json"], encoding="utf-8") as f:
        doc = json.load(f)
    assert doc["schema_version"] == SCHEMA_VERSION


def test_write_outputs_standalone(tmp_path: Path) -> None:
    out = tmp_path / "Main portfolio"
    out.mkdir()
    comparison = _comparison_three_way()
    health = _health(("policy", 70.0, 2), ("risk_parity", 75.0, 1))
    robust = _robust(("policy", 75.0, 1), ("risk_parity", 70.0, 2))
    selection = build_selection_decision(comparison, health=health, robustness=robust)
    with open(out / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f)
    cfg = validate_config(
        {"investor_currency": "USD", "output_dir_final": "Main portfolio", "tickers": ["VOO"]}
    )
    paths = write_assumption_sensitivity_outputs(
        cfg,
        project_root=tmp_path,
        comparison=comparison,
        selection=selection,
        health=health,
        robustness=robust,
    )
    assert paths["assumption_sensitivity_txt"].is_file()
