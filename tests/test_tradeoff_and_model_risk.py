from __future__ import annotations

import json
from pathlib import Path

from src.tradeoff_and_model_risk import (
    MODEL_RISK_SCHEMA,
    TRADEOFF_SCHEMA,
    build_model_risk_diagnostics,
    build_tradeoff_explanation,
    write_tradeoff_and_model_risk_outputs,
)
from src.config_schema import validate_config


def _metrics(**overrides) -> dict:
    base = {
        "cagr": 0.08,
        "vol_annual": 0.12,
        "max_drawdown": -0.22,
        "sharpe": 0.5,
    }
    base.update(overrides)
    return {"10y": base}


def _cand(
    cid: str,
    *,
    status: str = "available",
    role: str = "benchmark",
    metrics: dict | None = None,
    mandate_valid: bool = True,
    stress_overall: str = "DIAG_PASS",
    artifact_root: str = "alt",
) -> dict:
    return {
        "candidate_id": cid,
        "display_name": cid.title(),
        "role": role,
        "status": status,
        "artifact_root": artifact_root,
        "metrics": metrics or _metrics(),
        "drawdown": {"max_drawdown": (metrics or _metrics())["10y"]["max_drawdown"]},
        "mandate": {"portfolio_valid": mandate_valid},
        "stress": {
            "overall": stress_overall,
            "scenarios": [{"scenario_id": "s1", "portfolio_pnl_pct": -0.15}],
        },
        "warnings": [],
        "missing_fields": [],
        "weight_concentration": {"top1_weight_pct": 0.2},
        "diversification": {"top1_rc_pct": 0.3},
    }


def _comparison_with_current(tmp_path: Path) -> dict:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    current = tmp_path / "current portfolio"
    current.mkdir()
    for folder, weights in (
        (main, {"VOO": 0.6, "BND": 0.4}),
        (current, {"VOO": 0.5, "BND": 0.5}),
    ):
        snap = {
            "metrics": _metrics()["10y"],
            "final_weights_total": weights,
        }
        with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as f:
            json.dump(snap, f)

    return {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": "2025-12-31",
        "primary_window": "10y",
        "output_dir_final": "Main portfolio",
        "warnings": [],
        "candidates": [
            _cand(
                "policy",
                role="policy",
                metrics=_metrics(cagr=0.09, vol_annual=0.11, max_drawdown=-0.18),
                artifact_root="Main portfolio",
            ),
            _cand(
                "current",
                role="user_current",
                metrics=_metrics(cagr=0.07, vol_annual=0.13, max_drawdown=-0.24),
                artifact_root="current portfolio",
            ),
        ],
    }


def _selection(favored: str = "policy") -> dict:
    return {
        "schema_version": "selection_decision_v1",
        "decision_status": "selected_candidate",
        "favored_candidate_id": favored,
        "favored_display_name": "Policy",
        "composite_ranking": [
            {"candidate_id": "policy", "composite_score": 80},
            {"candidate_id": "current", "composite_score": 70},
        ],
        "no_trade": {"evaluated": False},
        "warnings": [],
    }


def _portfolio_first_selection(favored: str = "equal_weight") -> dict:
    doc = _selection(favored)
    doc["baseline_candidate_id"] = "analysis_subject"
    doc["favored_display_name"] = "Equal Weight"
    doc["composite_ranking"] = [
        {"candidate_id": "equal_weight", "composite_score": 80},
        {"candidate_id": "policy", "composite_score": 70},
    ]
    doc["no_trade"] = {
        "evaluated": True,
        "baseline_candidate_id": "analysis_subject",
    }
    return doc


def test_tradeoff_primary_pair_complete(tmp_path: Path) -> None:
    comparison = _comparison_with_current(tmp_path)
    selection = _selection("policy")
    doc = build_tradeoff_explanation(
        comparison,
        selection,
        project_root=tmp_path,
    )
    assert doc["schema_version"] == TRADEOFF_SCHEMA
    assert doc["tradeoff_status"] == "complete"
    assert "return_cagr" in doc["improves"]
    primary = next(p for p in doc["pairs"] if p["pair_id"] == "baseline_to_favored")
    assert primary["turnover_half_sum_pct"] == 10.0
    assert doc["cost_of_change"]["turnover_half_sum_pct"] == 10.0


def test_tradeoff_uses_analysis_subject_as_primary_baseline(tmp_path: Path) -> None:
    subject = tmp_path / "analysis_subject"
    equal = tmp_path / "equal-weight portfolio"
    subject.mkdir()
    equal.mkdir()
    for folder, weights in (
        (subject, {"VOO": 0.4, "BND": 0.6}),
        (equal, {"VOO": 0.7, "BND": 0.3}),
    ):
        with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as f:
            json.dump({"final_weights_total": weights}, f)

    comparison = {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": "2025-12-31",
        "primary_window": "10y",
        "comparison_baseline_candidate_id": "analysis_subject",
        "candidates": [
            _cand(
                "analysis_subject",
                role="analysis_subject",
                metrics=_metrics(cagr=0.06, vol_annual=0.13, max_drawdown=-0.25),
                artifact_root="analysis_subject",
            ),
            _cand(
                "current",
                role="user_current",
                metrics=_metrics(cagr=0.05, vol_annual=0.14, max_drawdown=-0.30),
            ),
            _cand(
                "equal_weight",
                role="benchmark",
                metrics=_metrics(cagr=0.08, vol_annual=0.11, max_drawdown=-0.18),
                artifact_root="equal-weight portfolio",
            ),
        ],
    }

    doc = build_tradeoff_explanation(
        comparison,
        _portfolio_first_selection(),
        project_root=tmp_path,
    )

    assert doc["tradeoff_status"] == "complete"
    assert doc["baseline_candidate_id"] == "analysis_subject"
    primary = next(p for p in doc["pairs"] if p["pair_id"] == "baseline_to_favored")
    assert primary["baseline_candidate_id"] == "analysis_subject"
    assert primary["target_candidate_id"] == "equal_weight"
    assert doc["cost_of_change"]["no_trade_context"]["baseline_candidate_id"] == "analysis_subject"


def test_tradeoff_baseline_unavailable() -> None:
    comparison = {
        "analysis_end": "2025-12-31",
        "primary_window": "10y",
        "candidates": [
            _cand("policy", role="policy"),
            _cand("current", status="unavailable", role="user_current"),
        ],
    }
    doc = build_tradeoff_explanation(
        comparison,
        _selection("policy"),
        project_root=Path("."),
    )
    assert doc["tradeoff_status"] == "baseline_unavailable"
    assert not any(p["pair_id"] == "baseline_to_favored" for p in doc["pairs"])


def test_model_risk_dedup_and_mandate(tmp_path: Path) -> None:
    comparison = _comparison_with_current(tmp_path)
    comparison["candidates"][0]["mandate"]["portfolio_valid"] = False
    comparison["candidates"][0]["stress"]["overall"] = "FAIL_STRESS"
    doc = build_model_risk_diagnostics(
        comparison,
        _selection("policy"),
        project_root=tmp_path,
    )
    assert doc["schema_version"] == MODEL_RISK_SCHEMA
    ids = [w["warning_id"] for w in doc["warnings"]]
    assert "mandate_portfolio_invalid" in ids
    assert "stress_fail_on_favored" in ids
    assert doc["overall_severity"] == "high"


def test_write_outputs_integration(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "metrics": _metrics(cagr=0.09)["10y"],
                "final_weights_total": {"VOO": 0.6, "BND": 0.4},
            },
            f,
        )
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump({"metrics": _metrics()["10y"]}, f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    from src.candidate_comparison import write_candidate_comparison_outputs

    paths = write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    assert paths.get("tradeoff_explanation_json", Path()).is_file()
    assert paths.get("model_risk_diagnostics_json", Path()).is_file()
    with open(paths["tradeoff_explanation_json"], encoding="utf-8") as f:
        tradeoff = json.load(f)
    assert tradeoff["schema_version"] == TRADEOFF_SCHEMA
