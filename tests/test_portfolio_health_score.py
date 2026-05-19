from __future__ import annotations

import json
from pathlib import Path

from src.config_schema import validate_config
from src.portfolio_health_score import (
    SCHEMA_VERSION,
    build_portfolio_health_score,
    write_portfolio_health_score_outputs,
)


def _comparison_three_candidates() -> dict:
    base_metrics = {
        "cagr": 0.08,
        "vol_annual": 0.12,
        "max_drawdown": -0.2,
        "sharpe": 0.5,
        "sortino": 0.6,
    }
    weights = {
        "top1_weight_asset": "VOO",
        "top1_weight_pct": 0.22,
        "top3_weight_assets": ["VOO", "BND", "GLD"],
        "top3_weight_sum_pct": 0.55,
        "source": "snapshot_10y.final_weights_total",
    }
    return {
        "schema_version": "candidate_comparison_v1",
        "primary_window": "10y",
        "candidates": [
            {
                "candidate_id": "alpha",
                "display_name": "Alpha",
                "status": "available",
                "metrics": {"10y": {**base_metrics, "cagr": 0.10, "sharpe": 0.7}},
                "stress": {
                    "overall": "DIAG_PASS",
                    "scenarios": [
                        {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.04, "pass": True},
                        {"scenario_id": "credit_shock", "portfolio_pnl_pct": -0.02, "pass": True},
                    ],
                },
                "drawdown": {"max_drawdown": -0.15, "recovered": True, "time_to_recovery_months": 6},
                "diversification": {
                    "top1_rc_asset": "VOO",
                    "top1_rc_pct": 0.25,
                    "top3_rc_assets": ["VOO", "BND", "GLD"],
                    "top3_rc_sum_pct": 0.55,
                    "source_window": "10y",
                },
                "weight_concentration": {**weights, "top1_weight_pct": 0.20},
                "mandate": {"portfolio_valid": True, "client_fit": True},
                "factor_regime": {
                    "factor_regression_10y": {
                        "adj_r_squared": 0.8,
                        "betas": {"eq": 0.5, "credit": 0.1},
                    }
                },
                "warnings": [],
            },
            {
                "candidate_id": "bravo",
                "display_name": "Bravo",
                "status": "available",
                "metrics": {"10y": {**base_metrics, "cagr": 0.06, "sharpe": 0.4}},
                "stress": {
                    "overall": "DIAG_ATTENTION",
                    "scenarios": [
                        {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.12, "pass": False},
                    ],
                },
                "drawdown": {"max_drawdown": -0.28, "recovered": False},
                "diversification": {
                    "top1_rc_asset": "QQQ",
                    "top1_rc_pct": 0.40,
                    "top3_rc_assets": ["QQQ", "VOO", "BND"],
                    "top3_rc_sum_pct": 0.80,
                    "source_window": "10y",
                },
                "weight_concentration": {**weights, "top1_weight_pct": 0.35},
                "mandate": {"portfolio_valid": True, "client_fit": True},
                "factor_regime": {},
                "warnings": [],
            },
            {
                "candidate_id": "charlie",
                "display_name": "Charlie",
                "status": "available",
                "metrics": {"10y": {**base_metrics, "cagr": 0.09, "sharpe": 0.55}},
                "stress": {"overall": "DIAG_PASS_WITH_WARNING", "scenarios": []},
                "drawdown": {"max_drawdown": -0.18},
                "diversification": {
                    "top1_rc_asset": "BND",
                    "top1_rc_pct": 0.30,
                    "top3_rc_sum_pct": 0.65,
                    "top3_rc_assets": ["BND", "VOO", "GLD"],
                    "source_window": "10y",
                },
                "weight_concentration": weights,
                "mandate": {"portfolio_valid": False, "client_fit": False},
                "factor_regime": {},
                "warnings": [],
            },
        ],
    }


def _robustness_fixture() -> dict:
    return {
        "schema_version": "robustness_scorecard_v1",
        "candidates": [
            {"candidate_id": "alpha", "total_score": 75, "score_status": "scored"},
            {"candidate_id": "bravo", "total_score": 40, "score_status": "scored"},
            {"candidate_id": "charlie", "total_score": 50, "score_status": "scored"},
        ],
    }


def test_schema_required_keys() -> None:
    doc = build_portfolio_health_score(
        _comparison_three_candidates(),
        robustness_scorecard=_robustness_fixture(),
    )
    assert doc["schema_version"] == SCHEMA_VERSION
    assert doc["diagnostic_only"] is True
    for key in (
        "generated_at",
        "weights_profile",
        "weights",
        "primary_window",
        "input_artifacts",
        "display_priority",
        "candidates",
        "comparison_summary",
        "warnings",
    ):
        assert key in doc
    assert doc["display_priority"] == ["current", "policy"]


def test_display_priority_starts_with_analysis_subject_when_available() -> None:
    comp = _comparison_three_candidates()
    subject = dict(comp["candidates"][0])
    subject["candidate_id"] = "analysis_subject"
    subject["display_name"] = "Starting portfolio"
    subject["role"] = "analysis_subject"
    comp["candidates"].append(subject)

    doc = build_portfolio_health_score(
        comp,
        robustness_scorecard=_robustness_fixture(),
    )

    assert doc["display_priority"] == ["analysis_subject"]


def test_relative_ranking_three_candidates() -> None:
    doc = build_portfolio_health_score(
        _comparison_three_candidates(),
        robustness_scorecard=_robustness_fixture(),
    )
    by_id = {c["candidate_id"]: c for c in doc["candidates"]}
    assert by_id["alpha"]["total_score"] > by_id["bravo"]["total_score"]
    assert by_id["alpha"]["health_rank"] == 1
    assert doc["comparison_summary"]["highest_health_candidate_id"] == "alpha"


def test_unavailable_not_scored() -> None:
    comp = _comparison_three_candidates()
    comp["candidates"].append(
        {
            "candidate_id": "missing",
            "display_name": "Missing",
            "status": "unavailable",
            "unavailable_reason": "missing_artifact_folder",
        }
    )
    doc = build_portfolio_health_score(comp, robustness_scorecard=_robustness_fixture())
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "missing")
    assert row["score_status"] == "not_scored"
    assert row["total_score"] is None


def test_mandate_invalid_caps_component() -> None:
    doc = build_portfolio_health_score(
        _comparison_three_candidates(),
        robustness_scorecard=_robustness_fixture(),
    )
    charlie = next(c for c in doc["candidates"] if c["candidate_id"] == "charlie")
    mandate = charlie["components"]["mandate_and_model_risk"]
    assert mandate["score"] <= 20
    assert "mandate_portfolio_invalid" in charlie["warnings"]


def test_missing_weight_concentration_reweights() -> None:
    comp = _comparison_three_candidates()
    comp["candidates"][1]["weight_concentration"] = {}
    doc = build_portfolio_health_score(comp, robustness_scorecard=_robustness_fixture())
    bravo = next(c for c in doc["candidates"] if c["candidate_id"] == "bravo")
    assert bravo["components"]["weight_concentration"]["status"] == "not_computed"
    assert bravo["total_score"] is not None
    assert "weight_concentration_inputs_missing" in doc["warnings"]


def test_missing_robustness_scorecard() -> None:
    doc = build_portfolio_health_score(_comparison_three_candidates(), robustness_scorecard=None)
    assert "robustness_scorecard_missing" in doc["warnings"]
    alpha = next(c for c in doc["candidates"] if c["candidate_id"] == "alpha")
    assert alpha["components"]["resilience_reference"]["status"] == "not_computed"
    assert alpha["total_score"] is not None


def test_single_candidate_warning() -> None:
    comp = _comparison_three_candidates()
    comp["candidates"] = [comp["candidates"][0]]
    doc = build_portfolio_health_score(comp, robustness_scorecard=_robustness_fixture())
    assert "single_candidate_comparison" in doc["warnings"]
    assert doc["candidates"][0]["total_score"] is not None


def test_display_priority_summary_fields() -> None:
    comp = _comparison_three_candidates()
    comp["candidates"].extend(
        [
            {
                "candidate_id": "policy",
                "display_name": "Policy",
                "status": "available",
                "metrics": comp["candidates"][0]["metrics"],
                "stress": comp["candidates"][0]["stress"],
                "drawdown": comp["candidates"][0]["drawdown"],
                "diversification": comp["candidates"][0]["diversification"],
                "weight_concentration": comp["candidates"][0]["weight_concentration"],
                "mandate": comp["candidates"][0]["mandate"],
                "factor_regime": comp["candidates"][0]["factor_regime"],
                "warnings": [],
            },
            {
                "candidate_id": "current",
                "display_name": "Current",
                "status": "available",
                "metrics": comp["candidates"][1]["metrics"],
                "stress": comp["candidates"][1]["stress"],
                "drawdown": comp["candidates"][1]["drawdown"],
                "diversification": comp["candidates"][1]["diversification"],
                "weight_concentration": comp["candidates"][1]["weight_concentration"],
                "mandate": comp["candidates"][1]["mandate"],
                "factor_regime": {},
                "warnings": [],
            },
        ]
    )
    rob = _robustness_fixture()
    rob["candidates"].extend(
        [
            {"candidate_id": "policy", "total_score": 70, "score_status": "scored"},
            {"candidate_id": "current", "total_score": 45, "score_status": "scored"},
        ]
    )
    doc = build_portfolio_health_score(comp, robustness_scorecard=rob)
    summary = doc["comparison_summary"]
    assert summary["policy_total_score"] is not None
    assert summary["current_total_score"] is not None


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
    comparison = _comparison_three_candidates()
    with open(out / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f)

    paths = write_portfolio_health_score_outputs(
        cfg,
        project_root=tmp_path,
        comparison=comparison,
        robustness_scorecard=_robustness_fixture(),
    )
    assert paths["portfolio_health_score_json"].is_file()
    assert paths["portfolio_health_score_txt"].is_file()
    with open(paths["portfolio_health_score_json"], encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["schema_version"] == SCHEMA_VERSION
