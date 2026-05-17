from __future__ import annotations

import json
from pathlib import Path

from src.action_engine import (
    SCHEMA_VERSION,
    TRANSACTION_COST_BPS,
    build_action_plan,
    write_action_plan_outputs,
)
from src.config_schema import validate_config
from src.selection_engine import build_selection_decision


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


def _selection_from_comparison(
    comp: dict,
    *,
    project_root: Path,
    output_dir: str = "Main portfolio",
) -> dict:
    return build_selection_decision(
        comp,
        health=_health_fixture(("policy", 72, 1), ("current", 68, 2)),
        robustness=_robust_fixture(("policy", 70, 1), ("current", 69, 2)),
        project_root=project_root,
    )


def test_schema_and_always_writes(tmp_path: Path) -> None:
    out = "Main portfolio"
    comp = _comparison_policy_current(output_dir=out)
    root = tmp_path
    policy_dir = root / out
    current_dir = root / "current portfolio"
    current_dir.mkdir(parents=True)
    comp["candidates"][0]["artifact_root"] = out
    comp["candidates"][1]["artifact_root"] = "current portfolio"
    _write_weights(policy_dir / "snapshot_10y.json", {"AAA": 0.4, "BBB": 0.35, "CCC": 0.25})
    _write_weights(current_dir / "snapshot_10y.json", {"AAA": 0.5, "BBB": 0.5})

    sel = _selection_from_comparison(comp, project_root=root, output_dir=out)
    assert sel is not None
    plan = build_action_plan(comp, sel, project_root=root)
    assert plan["schema_version"] == SCHEMA_VERSION
    assert plan["non_executing"] is True
    assert plan["transaction_cost_bps"] == TRANSACTION_COST_BPS
    assert "action_status" in plan
    assert "no_trades_reason" in plan
    assert plan["input_artifacts"]["selection_decision"] == "selection_decision.json"


def test_no_material_rebalance_empty_trades_with_weights(tmp_path: Path) -> None:
    out = "Main portfolio"
    comp = _comparison_policy_current(output_dir=out)
    root = tmp_path
    comp["candidates"][0]["artifact_root"] = "policy_dir"
    comp["candidates"][1]["artifact_root"] = "current_dir"
    (root / "policy_dir").mkdir()
    (root / "current_dir").mkdir()
    _write_weights(
        root / "policy_dir" / "snapshot_10y.json",
        {"VOO": 0.9, "BND": 0.1},
    )
    _write_weights(
        root / "current_dir" / "snapshot_10y.json",
        {"VOO": 0.2, "BND": 0.3, "GLD": 0.5},
    )

    health = _health_fixture(
        ("policy", 69, 1), ("current", 68, 2), ("equal_weight", 50, 3)
    )
    robust = _robust_fixture(
        ("policy", 69, 1), ("current", 68, 2), ("equal_weight", 50, 3)
    )
    sel = build_selection_decision(
        comp, health=health, robustness=robust, project_root=root
    )
    assert sel is not None
    assert sel["decision_status"] == "no_material_rebalance"

    plan = build_action_plan(comp, sel, project_root=root)
    assert plan["action_status"] == "no_trades_no_material_rebalance"
    assert plan["trades"] == []
    assert plan["current_weights"] is not None
    assert plan["target_weights"] is not None
    assert "No material rebalance" in plan["no_trades_reason"]


def test_selected_candidate_has_trades(tmp_path: Path) -> None:
    out = "Main portfolio"
    comp = _comparison_policy_current(output_dir=out)
    root = tmp_path
    policy_dir = root / out
    current_dir = root / "current portfolio"
    current_dir.mkdir(parents=True)
    comp["candidates"][0]["artifact_root"] = out
    comp["candidates"][1]["artifact_root"] = "current portfolio"
    _write_weights(policy_dir / "snapshot_10y.json", {"AAA": 0.2, "BBB": 0.3, "CCC": 0.5})
    _write_weights(current_dir / "snapshot_10y.json", {"AAA": 0.5, "BBB": 0.5})

    health = _health_fixture(("policy", 80, 1), ("current", 60, 2))
    robust = _robust_fixture(("policy", 78, 1), ("current", 58, 2))
    sel = build_selection_decision(
        comp, health=health, robustness=robust, project_root=root
    )
    assert sel is not None
    assert sel["decision_status"] == "selected_candidate"

    plan = build_action_plan(comp, sel, project_root=root)
    assert plan["action_status"] == "trades_for_review"
    assert len(plan["trades"]) > 0
    assert plan["turnover_half_sum_pct"] is not None
    assert plan["estimated_transaction_cost_pct"] == round(
        plan["turnover_half_sum_pct"] * TRANSACTION_COST_BPS / 10000.0,
        4,
    )
    assert len(plan["priority_trades"]) <= 5
    directions = {t["direction"] for t in plan["trades"]}
    assert directions <= {"buy", "sell"}


def test_transaction_cost_and_risk_per_turnover(tmp_path: Path) -> None:
    out = "Main portfolio"
    comp = _comparison_policy_current(output_dir=out)
    root = tmp_path
    policy_dir = root / out
    current_dir = root / "current portfolio"
    current_dir.mkdir(parents=True)
    comp["candidates"][0]["artifact_root"] = out
    comp["candidates"][1]["artifact_root"] = "current portfolio"
    _write_weights(policy_dir / "snapshot_10y.json", {"AAA": 0.1, "BBB": 0.9})
    _write_weights(current_dir / "snapshot_10y.json", {"AAA": 0.9, "BBB": 0.1})

    health = _health_fixture(("policy", 85, 1), ("current", 55, 2))
    robust = _robust_fixture(("policy", 82, 1), ("current", 52, 2))
    sel = build_selection_decision(
        comp, health=health, robustness=robust, project_root=root
    )
    plan = build_action_plan(comp, sel, project_root=root)
    turnover = plan["turnover_half_sum_pct"]
    assert turnover is not None and turnover > 0
    rc = plan["risk_context"]
    assert rc.get("risk_improvement_per_one_pct_turnover") is not None


def test_mandate_risk_reduction_no_trades(tmp_path: Path) -> None:
    comp = _comparison_policy_current(current_valid=False)
    comp["candidates"][1]["stress"]["fail_reason_code"] = "FAIL_MANDATE_MAXDD"
    root = tmp_path
    sel = build_selection_decision(
        comp,
        health=_health_fixture(
            ("policy", 70, 1), ("current", 65, 2), ("equal_weight", 50, 3)
        ),
        robustness=_robust_fixture(
            ("policy", 68, 1), ("current", 60, 2), ("equal_weight", 48, 3)
        ),
        project_root=root,
    )
    assert sel is not None
    assert sel["decision_status"] == "mandate_risk_reduction"
    plan = build_action_plan(comp, sel, project_root=root)
    assert plan["action_status"] == "no_trades_other"
    assert plan["trades"] == []


def test_write_outputs_integration(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = "Main portfolio"
    (tmp_path / out).mkdir(parents=True)
    comp = _comparison_policy_current(output_dir=out)
    policy_dir = tmp_path / out
    current_dir = tmp_path / "current portfolio"
    current_dir.mkdir(parents=True)
    comp["candidates"][0]["artifact_root"] = out
    comp["candidates"][1]["artifact_root"] = "current portfolio"
    _write_weights(policy_dir / "snapshot_10y.json", {"AAA": 0.5, "BBB": 0.5})
    _write_weights(current_dir / "snapshot_10y.json", {"AAA": 0.5, "BBB": 0.5})

    sel = _selection_from_comparison(comp, project_root=tmp_path, output_dir=out)
    with open(tmp_path / out / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comp, f)
    with open(tmp_path / out / "selection_decision.json", "w", encoding="utf-8") as f:
        json.dump(sel, f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": out,
            "tickers": ["VOO"],
        }
    )
    paths = write_action_plan_outputs(cfg, project_root=tmp_path)
    assert paths["action_plan_json"].is_file()
    assert paths["action_plan_txt"].is_file()
    with open(paths["action_plan_json"], encoding="utf-8") as f:
        plan = json.load(f)
    assert plan["schema_version"] == SCHEMA_VERSION
