from __future__ import annotations

import json
from pathlib import Path

from src.config_schema import validate_config
from src.pareto_dominance import (
    SCHEMA_VERSION,
    build_pareto_dominance,
    write_pareto_dominance_outputs,
)


def _metrics(
    *,
    cagr: float = 0.08,
    vol: float = 0.12,
    mdd: float = -0.22,
    es_95: float | None = None,
) -> dict:
    block: dict = {
        "cagr": cagr,
        "vol_annual": vol,
        "max_drawdown": mdd,
        "sharpe": 0.5,
    }
    if es_95 is not None:
        block["es_95"] = es_95
    return {"3y": dict(block), "5y": dict(block), "10y": dict(block)}


def _cand(
    cid: str,
    *,
    status: str = "available",
    cagr: float = 0.08,
    vol: float = 0.12,
    mdd: float = -0.22,
    stress_pnl: float = -0.15,
    scenarios: list[dict] | None = None,
) -> dict:
    stress_scenarios = scenarios
    if stress_scenarios is None:
        stress_scenarios = [{"scenario_id": "s1", "portfolio_pnl_pct": stress_pnl}]
    return {
        "candidate_id": cid,
        "display_name": cid.replace("_", " ").title(),
        "role": "benchmark",
        "status": status,
        "metrics": _metrics(cagr=cagr, vol=vol, mdd=mdd),
        "stress": {
            "overall": "DIAG_PASS",
            "scenarios": stress_scenarios,
        },
    }


def _comparison(*candidates: dict) -> dict:
    return {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": "2025-12-31",
        "primary_window": "10y",
        "candidates": list(candidates),
    }


def test_middle_candidate_dominated_in_chain() -> None:
    top = _cand("top", cagr=0.10, vol=0.10, mdd=-0.15, stress_pnl=-0.10)
    mid = _cand("mid", cagr=0.08, vol=0.12, mdd=-0.20, stress_pnl=-0.15)
    low = _cand("low", cagr=0.06, vol=0.14, mdd=-0.25, stress_pnl=-0.20)
    doc = build_pareto_dominance(_comparison(top, mid, low))
    by_id = {c["candidate_id"]: c for c in doc["candidates"]}
    assert by_id["top"]["pareto_status"] == "non_dominated"
    assert by_id["mid"]["pareto_status"] == "dominated"
    assert by_id["low"]["pareto_status"] == "dominated"
    assert any(p["dominator_id"] == "top" and p["dominated_id"] == "mid" for p in doc["pairwise_dominance"])


def test_missing_vol_makes_row_partial() -> None:
    complete = _cand("complete", cagr=0.09, vol=0.11, mdd=-0.18)
    partial = _cand("partial", cagr=0.07, vol=0.13, mdd=-0.21)
    partial["metrics"]["10y"].pop("vol_annual")
    doc = build_pareto_dominance(_comparison(complete, partial))
    by_id = {c["candidate_id"]: c for c in doc["candidates"]}
    assert by_id["partial"]["evaluation_status"] == "partial_objectives"
    assert by_id["partial"]["pareto_status"] == "not_evaluated"
    assert doc["dominance_status"] == "insufficient_candidates"


def test_stress_skipped_when_no_scenarios_anywhere() -> None:
    a = _cand("a", cagr=0.09, vol=0.11, mdd=-0.18, scenarios=[])
    b = _cand("b", cagr=0.07, vol=0.13, mdd=-0.21, scenarios=[])
    a["stress"] = {"overall": "DIAG_PASS", "scenarios": []}
    b["stress"] = {"overall": "DIAG_PASS", "scenarios": []}
    doc = build_pareto_dominance(_comparison(a, b))
    assert "stress_worst_loss" not in doc["objectives_evaluated"]
    assert doc["dominance_status"] == "complete"


def test_favored_dominated_flag_without_selection_mutation() -> None:
    strong = _cand("strong", cagr=0.11, vol=0.09, mdd=-0.12, stress_pnl=-0.08)
    weak = _cand("weak", cagr=0.05, vol=0.15, mdd=-0.30, stress_pnl=-0.25)
    selection = {
        "schema_version": "selection_decision_v1",
        "favored_candidate_id": "weak",
        "favored_display_name": "Weak",
    }
    doc = build_pareto_dominance(_comparison(strong, weak), selection=selection)
    assert doc["favored_is_dominated"] is True
    assert selection["favored_candidate_id"] == "weak"


def test_insufficient_candidates() -> None:
    only = _cand("only")
    doc = build_pareto_dominance(_comparison(only))
    assert doc["dominance_status"] == "insufficient_candidates"
    assert doc["evaluable_candidate_count"] == 1


def test_pipeline_emits_after_assumption_sensitivity(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    snap = {
        "analysis_end": "2025-12-31",
        "metrics": {"cagr": 0.08, "vol_annual": 0.12, "max_drawdown": -0.22, "sharpe": 0.5},
        "final_weights_total": {"VOO": 1.0},
        "stress_suite_results": {
            "overall": "DIAG_PASS",
            "scenarios": [{"scenario_id": "s1", "portfolio_pnl_pct": -0.15}],
        },
    }
    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump({**snap, "metrics": {"cagr": 0.09, "vol_annual": 0.11, "max_drawdown": -0.20}}, f)
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "analysis_setup": {
                    "analysis_portfolio": {"portfolio_role": "generated_policy_portfolio"}
                }
            },
            f,
        )
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(snap, f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    from src.candidate_comparison import write_candidate_comparison_outputs

    paths = write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    assert paths.get("pareto_dominance_json", Path()).is_file()
    with open(paths["pareto_dominance_json"], encoding="utf-8") as f:
        doc = json.load(f)
    assert doc["schema_version"] == SCHEMA_VERSION
    assert doc["diagnostic_only"] is True
