from __future__ import annotations

import json
from pathlib import Path

from src.config_schema import validate_config
from src.selection_engine import (
    SCHEMA_VERSION,
    build_selection_decision,
    rationale_text_is_client_safe,
    write_selection_decision_outputs,
)


def _base_metrics() -> dict:
    return {
        "cagr": 0.08,
        "vol_annual": 0.12,
        "max_drawdown": -0.22,
        "sharpe": 0.5,
    }


def _cand(
    cid: str,
    *,
    display: str | None = None,
    status: str = "available",
    role: str = "benchmark",
    mandate_valid: bool = True,
    max_dd: float = -0.22,
    artifact_root: str = "alt portfolio",
) -> dict:
    return {
        "candidate_id": cid,
        "display_name": display or cid.title(),
        "role": role,
        "status": status,
        "artifact_root": artifact_root,
        "metrics": {"10y": {**_base_metrics(), "max_drawdown": max_dd}},
        "drawdown": {"max_drawdown": max_dd},
        "mandate": {"portfolio_valid": mandate_valid, "client_fit": mandate_valid},
        "stress": {"overall": "DIAG_PASS"},
        "warnings": [],
    }


def _comparison_policy_current(
    *,
    policy_valid: bool = True,
    current_valid: bool = True,
    output_dir: str = "Main portfolio",
) -> dict:
    return {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": "2025-12-31",
        "investor_currency": "USD",
        "output_dir_final": output_dir,
        "candidates": [
            _cand(
                "policy",
                display="Policy (Optimized)",
                role="policy",
                mandate_valid=policy_valid,
                max_dd=-0.20,
                artifact_root=output_dir,
            ),
            _cand(
                "current",
                display="Current Portfolio",
                role="user_current",
                mandate_valid=current_valid,
                max_dd=-0.24,
                artifact_root=output_dir,
            ),
            _cand("equal_weight", display="Equal-Weight", role="benchmark"),
        ],
    }


def _health_fixture(*rows: tuple[str, int, int]) -> dict:
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


def _robust_fixture(*rows: tuple[str, int, int]) -> dict:
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


def _write_weights(path: Path, weights: dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"final_weights_total": weights}, f)


def test_schema_and_formal_flags() -> None:
    comp = _comparison_policy_current()
    doc = build_selection_decision(
        comp,
        health=_health_fixture(
            ("policy", 72, 1), ("current", 68, 2), ("equal_weight", 60, 3)
        ),
        robustness=_robust_fixture(
            ("policy", 70, 1), ("current", 67, 2), ("equal_weight", 55, 3)
        ),
    )
    assert doc is not None
    assert doc["schema_version"] == SCHEMA_VERSION
    assert doc["formal_decision"] is True
    assert doc["non_executing"] is True
    for key in (
        "decision_status",
        "composite_ranking",
        "rationale",
        "input_artifacts",
        "selection_weights_profile",
        "no_trade_thresholds_profile",
    ):
        assert key in doc


def test_policy_favored_when_mandate_clean() -> None:
    doc = build_selection_decision(
        _comparison_policy_current(),
        health=_health_fixture(
            ("policy", 50, 3), ("current", 90, 1), ("equal_weight", 40, 4)
        ),
        robustness=_robust_fixture(
            ("policy", 50, 3), ("current", 90, 1), ("equal_weight", 40, 4)
        ),
    )
    assert doc["decision_status"] == "selected_candidate"
    assert doc["favored_candidate_id"] == "policy"


def test_composite_winner_when_policy_unavailable() -> None:
    comp = _comparison_policy_current()
    comp["candidates"][0]["status"] = "unavailable"
    comp["candidates"][0]["unavailable_reason"] = "missing_snapshot"
    doc = build_selection_decision(
        comp,
        health=_health_fixture(("equal_weight", 80, 1), ("current", 60, 2)),
        robustness=_robust_fixture(("equal_weight", 75, 1), ("current", 55, 2)),
    )
    assert doc["favored_candidate_id"] == "equal_weight"
    assert doc["decision_status"] == "selected_candidate"


def test_no_material_rebalance(tmp_path: Path) -> None:
    out = "Main portfolio"
    comp = _comparison_policy_current(output_dir=out)
    policy_weights = {"VOO": 0.9, "BND": 0.1}
    current_weights = {"VOO": 0.2, "BND": 0.3, "GLD": 0.5}
    comp["candidates"][0]["artifact_root"] = "policy_dir"
    comp["candidates"][1]["artifact_root"] = "current_dir"
    (tmp_path / "policy_dir").mkdir()
    (tmp_path / "current_dir").mkdir()
    _write_weights(tmp_path / "policy_dir" / "snapshot_10y.json", policy_weights)
    _write_weights(tmp_path / "current_dir" / "snapshot_10y.json", current_weights)

    doc = build_selection_decision(
        comp,
        health=_health_fixture(
            ("policy", 69, 1), ("current", 68, 2), ("equal_weight", 50, 3)
        ),
        robustness=_robust_fixture(
            ("policy", 68, 1), ("current", 67, 2), ("equal_weight", 45, 3)
        ),
        project_root=tmp_path,
    )
    assert doc["decision_status"] == "no_material_rebalance"
    assert doc["no_trade"] is not None
    assert doc["no_trade"]["materiality_pass"] is False
    assert doc["favored_candidate_id"] == "policy"


def test_selected_candidate_material_move(tmp_path: Path) -> None:
    comp = _comparison_policy_current(output_dir="Main")
    (tmp_path / "policy_dir").mkdir()
    (tmp_path / "current_dir").mkdir()
    comp["candidates"][0]["artifact_root"] = "policy_dir"
    comp["candidates"][1]["artifact_root"] = "current_dir"
    _write_weights(
        tmp_path / "policy_dir" / "snapshot_10y.json",
        {"VOO": 0.55, "BND": 0.45},
    )
    _write_weights(
        tmp_path / "current_dir" / "snapshot_10y.json",
        {"VOO": 0.50, "BND": 0.50},
    )
    doc = build_selection_decision(
        comp,
        health=_health_fixture(
            ("policy", 85, 1), ("current", 60, 2), ("equal_weight", 50, 3)
        ),
        robustness=_robust_fixture(
            ("policy", 82, 1), ("current", 58, 2), ("equal_weight", 48, 3)
        ),
        project_root=tmp_path,
    )
    assert doc["decision_status"] == "selected_candidate"
    assert doc["favored_candidate_id"] == "policy"


def test_inconclusive_no_scored() -> None:
    comp = _comparison_policy_current()
    comp["candidates"][0]["status"] = "unavailable"
    doc = build_selection_decision(
        comp,
        health=_health_fixture(("current", 60, 1)),
        robustness=_robust_fixture(("current", 55, 1)),
    )
    assert doc["decision_status"] == "inconclusive"
    assert doc["favored_candidate_id"] is None


def test_data_review_required_missing_scores() -> None:
    doc = build_selection_decision(_comparison_policy_current(), health=None, robustness=None)
    assert doc["decision_status"] == "data_review_required"
    assert "missing_score_artifacts" in doc["warnings"]


def test_mandate_risk_reduction_current_breach() -> None:
    comp = _comparison_policy_current(current_valid=False)
    comp["candidates"][1]["stress"]["fail_reason_code"] = "FAIL_MANDATE_MAXDD"
    doc = build_selection_decision(
        comp,
        health=_health_fixture(
            ("policy", 70, 1), ("current", 65, 2), ("equal_weight", 50, 3)
        ),
        robustness=_robust_fixture(
            ("policy", 68, 1), ("current", 60, 2), ("equal_weight", 48, 3)
        ),
    )
    assert doc["decision_status"] == "mandate_risk_reduction"
    assert doc["favored_candidate_id"] is None


def test_missing_current_skips_no_trade() -> None:
    comp = _comparison_policy_current()
    comp["candidates"][1]["status"] = "unavailable"
    doc = build_selection_decision(
        comp,
        health=_health_fixture(("policy", 70, 1), ("equal_weight", 55, 2)),
        robustness=_robust_fixture(("policy", 68, 1), ("equal_weight", 50, 2)),
    )
    assert doc["decision_status"] == "selected_candidate"
    assert doc.get("no_trade") is None


def test_partial_score_warning() -> None:
    doc = build_selection_decision(
        _comparison_policy_current(),
        health=_health_fixture(("policy", 70, 1), ("current", 65, 2)),
        robustness=None,
    )
    assert "partial_score_inputs" in doc["warnings"]
    assert doc["decision_status"] == "selected_candidate"


def test_tie_break_robustness_rank() -> None:
    comp = _comparison_policy_current()
    comp["candidates"][0]["status"] = "unavailable"
    comp["candidates"].append(
        _cand("risk_parity", display="Risk Parity", role="benchmark", artifact_root="rp")
    )
    doc = build_selection_decision(
        comp,
        health=_health_fixture(
            ("equal_weight", 70, 2),
            ("risk_parity", 70, 1),
            ("current", 60, 3),
        ),
        robustness=_robust_fixture(
            ("equal_weight", 70, 3),
            ("risk_parity", 70, 1),
            ("current", 55, 2),
        ),
    )
    assert doc["favored_candidate_id"] == "risk_parity"


def test_rationale_no_forbidden_patterns() -> None:
    doc = build_selection_decision(
        _comparison_policy_current(),
        health=_health_fixture(
            ("policy", 72, 1), ("current", 68, 2), ("equal_weight", 60, 3)
        ),
        robustness=_robust_fixture(
            ("policy", 70, 1), ("current", 67, 2), ("equal_weight", 55, 3)
        ),
    )
    summary = doc["rationale"]["summary"]
    assert rationale_text_is_client_safe(summary)
    for bullet in doc["rationale"].get("selection_bullets", []):
        assert rationale_text_is_client_safe(bullet)


def test_write_outputs(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    out = tmp_path / "Main portfolio"
    out.mkdir()
    comparison = _comparison_policy_current()
    with open(out / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f)

    paths = write_selection_decision_outputs(
        cfg,
        project_root=tmp_path,
        comparison=comparison,
        health=_health_fixture(
            ("policy", 72, 1), ("current", 68, 2), ("equal_weight", 60, 3)
        ),
        robustness=_robust_fixture(
            ("policy", 70, 1), ("current", 67, 2), ("equal_weight", 55, 3)
        ),
    )
    assert paths["selection_decision_json"].is_file()
    assert paths["selection_decision_txt"].is_file()
    with open(paths["selection_decision_json"], encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["schema_version"] == SCHEMA_VERSION
