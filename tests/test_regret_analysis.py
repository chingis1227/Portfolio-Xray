from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from src.config_schema import validate_config
from src.regret_analysis import (
    SCHEMA_VERSION,
    build_regret_analysis,
    write_regret_analysis_outputs,
)


def _metrics(*, cagr: float = 0.08) -> dict:
    block = {
        "cagr": cagr,
        "vol_annual": 0.12,
        "max_drawdown": -0.22,
        "sharpe": 0.5,
    }
    return {"3y": dict(block), "5y": dict(block), "10y": dict(block)}


def _cand(
    cid: str,
    *,
    status: str = "available",
    role: str = "benchmark",
    stress_pnl: float = -0.15,
    scenarios: list[dict] | None = None,
    cagr: float = 0.08,
) -> dict:
    stress_scenarios = scenarios
    if stress_scenarios is None:
        stress_scenarios = [{"scenario_id": "gfc", "portfolio_pnl_pct": stress_pnl}]
    return {
        "candidate_id": cid,
        "display_name": cid.replace("_", " ").title(),
        "role": role,
        "status": status,
        "metrics": _metrics(cagr=cagr),
        "stress": {"overall": "DIAG_PASS", "scenarios": stress_scenarios},
    }


def _comparison(*candidates: dict) -> dict:
    return {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": "2025-12-31",
        "primary_window": "10y",
        "candidates": list(candidates),
    }


def test_middle_profile_positive_regret_best_zero() -> None:
    best = _cand("best", stress_pnl=-0.08, cagr=0.10, role="policy")
    mid = _cand("mid", stress_pnl=-0.15, cagr=0.08, role="benchmark")
    low = _cand("low", stress_pnl=-0.20, cagr=0.06, role="benchmark")
    selection = {
        "schema_version": "selection_decision_v1",
        "favored_candidate_id": "mid",
    }
    doc = build_regret_analysis(_comparison(best, mid, low), selection=selection)
    scenario = doc["scenario_regret"][0]
    assert scenario["best_candidate_id"] == "best"
    favored = scenario["by_reference"]["favored"]
    assert favored["regret"] == 0.07
    assert favored["pnl"] == -0.15


def test_tied_best_zero_regret_stable_tiebreak() -> None:
    a = _cand("b_candidate", stress_pnl=-0.10, role="policy")
    z = _cand("a_candidate", stress_pnl=-0.10, role="benchmark")
    selection = {"favored_candidate_id": "b_candidate"}
    doc = build_regret_analysis(_comparison(a, z), selection=selection)
    scenario = doc["scenario_regret"][0]
    assert scenario["best_candidate_id"] == "a_candidate"
    assert scenario["by_reference"]["favored"]["regret"] == 0
    assert scenario["by_reference"]["benchmark"]["regret"] == 0


def test_missing_favored_current_still_computed() -> None:
    strong = _cand("strong", stress_pnl=-0.08, role="benchmark")
    current = _cand("current", stress_pnl=-0.12, role="user_current")
    doc = build_regret_analysis(_comparison(strong, current), selection=None)
    favored = next(r for r in doc["reference_profiles"] if r["reference_id"] == "favored")
    current_ref = next(r for r in doc["reference_profiles"] if r["reference_id"] == "current")
    assert favored["reference_status"] == "not_available"
    assert current_ref["reference_status"] == "complete"
    assert current_ref["worst_regret"] is not None


def test_no_scenario_pnl_cagr_tier_b() -> None:
    a = _cand("a", scenarios=[], cagr=0.09)
    b = _cand("b", scenarios=[], cagr=0.07)
    a["stress"] = {"overall": "DIAG_PASS", "scenarios": []}
    b["stress"] = {"overall": "DIAG_PASS", "scenarios": []}
    doc = build_regret_analysis(_comparison(a, b))
    assert doc["regret_status"] == "no_scenario_pnl"
    assert doc["metric_regret"]["status"] == "complete"
    assert doc["metric_regret"]["cagr_best_candidate_id"] == "a"


def test_negative_regret_surfaces_warning() -> None:
    broken = _cand("broken", stress_pnl=-0.05, role="policy")
    peer = _cand("peer", stress_pnl=-0.10, role="benchmark")
    selection = {"favored_candidate_id": "broken"}
    with patch(
        "src.regret_analysis._best_for_scenario",
        return_value=("peer", -0.10, {"broken": -0.05, "peer": -0.10}),
    ):
        doc = build_regret_analysis(_comparison(broken, peer), selection=selection)
    assert any("regret_negative_data_bug" in w for w in doc["warnings"])


def test_pipeline_emits_after_pareto_dominance(tmp_path: Path) -> None:
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
    assert paths.get("regret_analysis_json", Path()).is_file()
    pareto_mtime = paths["pareto_dominance_json"].stat().st_mtime
    regret_mtime = paths["regret_analysis_json"].stat().st_mtime
    assert regret_mtime >= pareto_mtime
    with open(paths["regret_analysis_json"], encoding="utf-8") as f:
        doc = json.load(f)
    assert doc["schema_version"] == SCHEMA_VERSION
    assert doc["diagnostic_only"] is True


def test_write_outputs_roundtrip(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    main = tmp_path / "Main portfolio"
    main.mkdir()
    comparison = _comparison(
        _cand("a", stress_pnl=-0.10, role="policy"),
        _cand("b", stress_pnl=-0.14, role="benchmark"),
    )
    with open(main / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f)
    paths = write_regret_analysis_outputs(cfg, project_root=tmp_path, comparison=comparison)
    assert paths["regret_analysis_json"].is_file()
    assert paths["regret_analysis_txt"].is_file()
