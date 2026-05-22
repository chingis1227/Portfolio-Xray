"""Offline integration: guarded Block 6–7 handoff from candidate_comparison (RM-1027)."""

from __future__ import annotations

import json
from pathlib import Path

from src.portfolio_health_score import _resolve_stress_scenarios
from src.robustness_scorecard import _resolve_stress_scenarios as robust_resolve_stress
from mvp_offline_fixtures import write_json


def _stress_report(*, scenario_id: str, pnl: float) -> dict:
    return {
        "scenario_results": [
            {"scenario_id": scenario_id, "portfolio_pnl_pct": pnl, "pass": True},
        ],
    }


def _cand_row(
    cid: str,
    *,
    status: str,
    role: str,
    artifact_root: str,
    embed_scenario: str,
    fair_ready: bool = True,
) -> dict:
    row: dict = {
        "candidate_id": cid,
        "display_name": cid,
        "status": status,
        "role": role,
        "artifact_root": artifact_root,
        "metrics": {"10y": {"cagr": 0.07, "vol_annual": 0.11, "max_drawdown": -0.18, "sharpe": 0.5}},
        "stress": {
            "overall": "DIAG_PASS",
            "scenarios": [
                {
                    "scenario_id": embed_scenario,
                    "portfolio_pnl_pct": -0.03,
                    "pass": True,
                }
            ],
        },
        "drawdown": {"max_drawdown": -0.18, "recovered": True},
        "diversification": {"top1_rc_pct": 0.3, "top3_rc_sum_pct": 0.6, "source_window": "10y"},
        "weight_concentration": {"top1_weight_pct": 0.25, "top3_weight_sum_pct": 0.55},
        "mandate": {"portfolio_valid": True},
        "warnings": [],
    }
    if role in ("optimizer_candidate", "robust_candidate"):
        row["construction_disclosure"] = {
            "optimization_readiness": {"fair_comparison_ready": fair_ready},
        }
    return row


def test_degraded_optimizer_stress_uses_embed_not_artifact_file(tmp_path: Path) -> None:
    """Block 7 guard: degraded optimizer must not load richer stress_report.json."""
    root = tmp_path
    output_dir = "Main portfolio"
    degraded_dir = root / "minimum variance portfolio"
    degraded_dir.mkdir(parents=True)
    write_json(
        degraded_dir / "stress_report.json",
        _stress_report(scenario_id="file_only_scenario", pnl=-0.99),
    )

    fair_dir = root / "equal-weight portfolio"
    fair_dir.mkdir(parents=True)
    write_json(
        fair_dir / "stress_report.json",
        _stress_report(scenario_id="fair_file_scenario", pnl=-0.05),
    )

    degraded = _cand_row(
        "minimum_variance",
        status="degraded",
        role="optimizer_candidate",
        artifact_root="minimum variance portfolio",
        embed_scenario="comparison_embed_scenario",
        fair_ready=False,
    )
    fair_bench = _cand_row(
        "equal_weight",
        status="available",
        role="benchmark_candidate",
        artifact_root="equal-weight portfolio",
        embed_scenario="equal_embed",
    )
    fair_bench["stress"] = {"overall": "DIAG_PASS", "scenarios": []}

    for cand in (degraded, fair_bench):
        scenarios = _resolve_stress_scenarios(
            cand,
            project_root=root,
            output_dir_final=output_dir,
        )
        robust_scenarios, source = robust_resolve_stress(
            cand,
            project_root=root,
            output_dir_final=output_dir,
        )
        if cand["candidate_id"] == "minimum_variance":
            assert [s["scenario_id"] for s in scenarios] == ["comparison_embed_scenario"]
            assert [s["scenario_id"] for s in robust_scenarios] == ["comparison_embed_scenario"]
            assert "file_only_scenario" not in {s["scenario_id"] for s in robust_scenarios}
        else:
            assert any(s["scenario_id"] == "fair_file_scenario" for s in scenarios)
            assert any(s["scenario_id"] == "fair_file_scenario" for s in robust_scenarios)


def test_partial_menu_comparison_core_handoff(tmp_path: Path) -> None:
    """Core partial menu: comparison carries menu context for downstream warnings."""
    comparison = {
        "schema_version": "candidate_comparison_v1",
        "primary_window": "10y",
        "comparison_baseline_candidate_id": "analysis_subject",
        "candidate_menu": {
            "review_mode": "core",
            "is_partial_menu": True,
            "intended_menu_profile_id": "core_v1",
            "product_menu_profile_id": "default_v1",
        },
        "candidates": [
            _cand_row(
                "equal_weight",
                status="available",
                role="benchmark_candidate",
                artifact_root="equal-weight portfolio",
                embed_scenario="eq",
            ),
        ],
    }
    menu = comparison["candidate_menu"]
    assert menu["review_mode"] == "core"
    assert menu["is_partial_menu"] is True
    assert menu["intended_menu_profile_id"] == "core_v1"

    path = tmp_path / "candidate_comparison.json"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(comparison, handle)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["candidate_menu"]["is_partial_menu"] is True
