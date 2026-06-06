from __future__ import annotations

import json
from pathlib import Path

from src.current_vs_candidate import (
    CURRENT_VS_CANDIDATE_VERSION,
    build_current_vs_candidate,
    write_current_vs_candidate_outputs,
)


def _candidate(cid: str, *, cagr: float, vol: float, dd: float, stress: float, status: str = "available") -> dict:
    return {
        "candidate_id": cid,
        "display_name": cid.replace("_", " ").title(),
        "role": "analysis_subject" if cid == "analysis_subject" else "benchmark",
        "status": status,
        "artifact_root": cid,
        "metrics": {"10y": {"cagr": cagr, "vol_annual": vol, "max_drawdown": dd, "sharpe": cagr / vol}},
        "drawdown": {"max_drawdown": dd},
        "stress": {"scenarios": [{"scenario_id": "shock", "portfolio_pnl_pct": stress}]},
        "construction_disclosure": {"disclosure_status": "available"},
        "missing_fields": [],
        "warnings": [],
        "source_files": ["snapshot_10y.json"],
    }


def _comparison() -> dict:
    return {
        "schema_version": "candidate_comparison_v1",
        "comparison_baseline_candidate_id": "analysis_subject",
        "analysis_end": "2026-04-30",
        "primary_window": "10y",
        "candidates": [
            _candidate("analysis_subject", cagr=0.07, vol=0.12, dd=-0.25, stress=-0.18),
            _candidate("equal_weight", cagr=0.065, vol=0.10, dd=-0.18, stress=-0.12),
            _candidate("risk_parity", cagr=0.06, vol=0.09, dd=-0.16, stress=-0.10),
        ],
    }


def test_build_current_vs_candidate_uses_selection_favored_candidate() -> None:
    doc = build_current_vs_candidate(
        _comparison(),
        selection={"favored_candidate_id": "equal_weight"},
    )

    assert doc["schema_version"] == CURRENT_VS_CANDIDATE_VERSION
    assert doc["view_mode"] == "one_candidate"
    assert doc["baseline"]["candidate_id"] == "analysis_subject"
    assert doc["selected_candidate_ids"] == ["equal_weight"]
    row = doc["comparisons"][0]
    assert row["candidate_id"] == "equal_weight"
    dimensions = {dim["field"]: dim for dim in row["dimensions"]}
    assert dimensions["vol_annual"]["direction"] == "improved"
    assert dimensions["max_drawdown"]["direction"] == "improved"
    assert dimensions["worst_stress_loss"]["direction"] == "improved"
    assert dimensions["cagr"]["direction"] == "worse"


def test_build_current_vs_candidate_explicit_ids_override_selection_favored_candidate() -> None:
    doc = build_current_vs_candidate(
        _comparison(),
        selection={"favored_candidate_id": "risk_parity"},
        candidate_ids=["equal_weight"],
    )

    assert doc["view_mode"] == "one_candidate"
    assert doc["selected_candidate_ids"] == ["equal_weight"]
    assert doc["comparisons"][0]["candidate_id"] == "equal_weight"


def test_build_current_vs_candidate_supports_shortlist() -> None:
    doc = build_current_vs_candidate(
        _comparison(),
        candidate_ids=["equal_weight", "risk_parity"],
    )

    assert doc["view_mode"] == "shortlist"
    assert [row["candidate_id"] for row in doc["comparisons"]] == ["equal_weight", "risk_parity"]


def test_build_current_vs_candidate_warns_for_missing_candidate() -> None:
    doc = build_current_vs_candidate(_comparison(), candidate_ids=["missing"])

    assert doc["view_mode"] == "diagnosis_only"
    assert doc["requested_candidate_ids"] == ["missing"]
    assert doc["selected_candidate_ids"] == []
    assert "candidate_unavailable:missing" in doc["warnings"]


def test_build_current_vs_candidate_blocks_when_candidate_generation_failed() -> None:
    doc = build_current_vs_candidate(
        _comparison(),
        candidate_ids=["equal_weight"],
        candidate_generation={
            "generation_status": "failed",
            "candidate": {"candidate_id": "equal_weight", "status": "failed", "weights": None},
            "handoff_to_comparison": {"can_compare": False, "blocked_reason": "candidate_generation_failed"},
        },
    )

    assert doc["comparison_status"] == "blocked_by_candidate_generation"
    assert doc["reason"] == "candidate_generation_failed"
    assert doc["selected_candidate_ids"] == []
    assert doc["comparisons"] == []


def test_write_current_vs_candidate_outputs(tmp_path: Path) -> None:
    paths = write_current_vs_candidate_outputs(
        output_dir=tmp_path,
        comparison=_comparison(),
        selection={"favored_candidate_id": "risk_parity"},
    )

    path = paths["current_vs_candidate_json"]
    assert path == tmp_path / "current_vs_candidate.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["selected_candidate_ids"] == ["risk_parity"]
