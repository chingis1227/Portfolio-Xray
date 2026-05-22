"""Offline integration: Blocks 8–10 package truthfulness (RM-1028)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.action_engine import build_action_plan
from src.decision_package_reporting import build_decision_package_report
from src.selection_engine import build_selection_decision
from mvp_offline_fixtures import MVP_DECISION_PACKAGE_ARTIFACTS, load_mvp_config, seed_minimal_mvp_workspace
from src.candidate_comparison import write_candidate_comparison_outputs


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args, **_kwargs):
        raise AssertionError("Blocks 8-10 integration test must not use live network data")

    import src.data_fred as data_fred
    import src.data_yf as data_yf

    monkeypatch.setattr(data_yf, "download_all", _boom)
    monkeypatch.setattr(data_fred, "fetch_fred_series", _boom, raising=False)


def _health_fixture(*rows: tuple[str, float, int]) -> dict:
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


def _robust_fixture(*rows: tuple[str, float, int]) -> dict:
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


def _optimizer_cand(
    cid: str,
    *,
    status: str = "degraded",
    fair_ready: bool = False,
) -> dict:
    return {
        "candidate_id": cid,
        "display_name": cid.replace("_", " ").title(),
        "role": "optimizer_candidate",
        "status": status,
        "metrics": {"10y": {"cagr": 0.08, "vol_annual": 0.11, "max_drawdown": -0.2}},
        "stress": {"overall": "DIAG_PASS"},
        "mandate": {"portfolio_valid": True},
        "construction_disclosure": {
            "optimization_readiness": {"fair_comparison_ready": fair_ready},
        },
    }


def test_selection_and_package_exclude_degraded_optimizer_from_favoring() -> None:
    """Block 8: degraded optimizer may rank high but cannot be favored; package says so."""
    comparison = {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": "2026-04-30",
        "investor_currency": "USD",
        "comparison_baseline_candidate_id": "analysis_subject",
        "candidate_menu": {
            "review_mode": "core",
            "is_partial_menu": True,
            "partial_menu_reason": "reduced_vs_product_menu",
            "intended_menu_profile_id": "core_v1",
            "product_menu_profile_id": "default_v1",
            "intended_menu_scored_count": 4,
            "product_menu_size": 16,
        },
        "candidates": [
            {
                "candidate_id": "analysis_subject",
                "display_name": "Subject",
                "role": "analysis_subject",
                "status": "available",
                "metrics": {"10y": {"cagr": 0.06, "vol_annual": 0.12, "max_drawdown": -0.22}},
                "stress": {"overall": "DIAG_PASS"},
                "mandate": {"portfolio_valid": True},
            },
            _optimizer_cand("degraded_opt", status="degraded", fair_ready=False),
            _optimizer_cand("fair_opt", status="available", fair_ready=True),
            {
                "candidate_id": "equal_weight",
                "display_name": "Equal-Weight",
                "role": "benchmark_candidate",
                "status": "available",
                "metrics": {"10y": {"cagr": 0.07, "vol_annual": 0.1, "max_drawdown": -0.18}},
                "stress": {"overall": "DIAG_PASS"},
                "mandate": {"portfolio_valid": True},
            },
        ],
    }
    health = _health_fixture(
        ("degraded_opt", 95, 1),
        ("fair_opt", 72, 2),
        ("equal_weight", 68, 3),
        ("analysis_subject", 60, 4),
    )
    robust = _robust_fixture(
        ("degraded_opt", 94, 1),
        ("fair_opt", 70, 2),
        ("equal_weight", 65, 3),
        ("analysis_subject", 58, 4),
    )

    selection = build_selection_decision(comparison, health=health, robustness=robust)
    assert selection["favored_candidate_id"] == "fair_opt"
    assert "partial_candidate_menu" in selection["warnings"]

    action = build_action_plan(comparison, selection, project_root=Path.cwd())
    assert "partial_candidate_menu_action_context" in action["warnings"]

    package = build_decision_package_report(
        comparison=comparison,
        health=health,
        robustness=robust,
        selection=selection,
        action=action,
        monitoring_diff=None,
        decision_journal=None,
    )
    text = package["summary_plain_en"]
    assert "Review scope (read first)" in text
    assert "Partial menu" in text
    assert "Degraded optimizer" in text
    assert "not eligible for favoring" in text
    assert package["package_truthfulness"]["degraded_optimizer_count"] == 1
    assert package["package_truthfulness"]["implies_full_product_menu_shootout"] is False
    assert selection["favored_display_name"] in text


def test_mvp_pipeline_decision_package_includes_truthfulness_block(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """End-to-end offline: write_candidate_comparison_outputs → package_truthfulness JSON."""
    _block_network(monkeypatch)
    seed_minimal_mvp_workspace(tmp_path)
    cfg = load_mvp_config(tmp_path)
    write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    out_dir = tmp_path / "Main portfolio"

    for filename, schema_version in MVP_DECISION_PACKAGE_ARTIFACTS:
        with open(out_dir / filename, encoding="utf-8") as f:
            doc = json.load(f)
        assert doc.get("schema_version") == schema_version, filename

    with open(out_dir / "decision_package_summary.json", encoding="utf-8") as f:
        package = json.load(f)
    assert package.get("package_truthfulness") is not None
    assert "schema_version" in package["package_truthfulness"]

    with open(out_dir / "selection_decision.json", encoding="utf-8") as f:
        selection = json.load(f)
    favored = selection.get("favored_candidate_id")
    if favored:
        with open(out_dir / "candidate_comparison.json", encoding="utf-8") as f:
            comparison = json.load(f)
        by_id = {c["candidate_id"]: c for c in comparison.get("candidates", [])}
        row = by_id.get(favored, {})
        assert row.get("status") != "degraded"
