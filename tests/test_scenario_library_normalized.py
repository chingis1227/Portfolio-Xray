"""Tests for Scenario Library Normalized View v1."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.scenario_library_normalized import (
    SCENARIO_LIBRARY_NORMALIZED_VERSION,
    WEEKLY_TO_MONTHLY_VARIANCE_FACTOR,
    build_scenario_library_normalized,
    summarize_normalized_roles,
)


def _sample_cov() -> dict[str, dict[str, float]]:
    return {
        "AAA": {"AAA": 0.04, "BBB": 0.01},
        "BBB": {"AAA": 0.01, "BBB": 0.09},
    }


def test_normalized_view_return_types_and_paths(tmp_path: Path) -> None:
    scenario_library = {
        "version": "scenario_library_v1",
        "scenarios": [
            {
                "scenario_id": "base_historical",
                "scenario_type": "base",
                "frequency": "monthly",
                "classification": "usable_with_caution",
                "quality_status": "usable",
                "scenario_portfolio_return": None,
                "asset_covariance": {
                    "native_frequency": "monthly",
                    "normalized_frequency": "monthly",
                    "matrix": _sample_cov(),
                },
                "factor_covariance": {
                    "native_frequency": "weekly",
                    "normalized_frequency": "monthly_equivalent",
                    "matrix": _sample_cov(),
                },
                "factor_betas": {"beta_eq": 0.7},
                "warnings": [],
            },
            {
                "scenario_id": "2020",
                "scenario_type": "historical_stress",
                "frequency": "episode",
                "classification": "usable_with_caution",
                "quality_status": "usable",
                "scenario_portfolio_return": -0.18,
                "asset_covariance": {
                    "native_frequency": "monthly",
                    "normalized_frequency": "monthly",
                    "matrix": _sample_cov(),
                },
                "factor_covariance": {
                    "native_frequency": "weekly",
                    "normalized_frequency": "monthly_equivalent",
                    "matrix": _sample_cov(),
                },
                "factor_betas": {"5y": {"beta_eq": 1.0}},
                "warnings": [],
            },
            {
                "scenario_id": "equity_shock",
                "scenario_type": "synthetic_stress",
                "frequency": "monthly",
                "classification": "ready_for_optimization",
                "quality_status": "reliable",
                "scenario_portfolio_return": -0.15,
                "asset_covariance": {
                    "native_frequency": "monthly",
                    "normalized_frequency": "monthly",
                    "matrix": _sample_cov(),
                },
                "factor_covariance": {
                    "native_frequency": "weekly",
                    "normalized_frequency": "monthly_equivalent",
                    "matrix": _sample_cov(),
                },
                "factor_betas": {"5y": {"beta_eq": 1.0}},
                "warnings": [],
            },
        ],
    }

    out = build_scenario_library_normalized(
        scenario_library,
        output_dir_final=tmp_path,
        output_dir_csv=tmp_path,
    )
    assert out["version"] == SCENARIO_LIBRARY_NORMALIZED_VERSION
    assert out["n_scenarios"] == 3
    assert (tmp_path / "scenario_library_normalized.json").exists()
    assert (tmp_path / "scenario_library_normalized_summary.csv").exists()
    assert (tmp_path / "scenario_library_normalized_missing_inputs.csv").exists()
    assert (tmp_path / "scenario_library_normalized_warnings.csv").exists()
    assert (tmp_path / "scenario_library_normalized_classification.csv").exists()

    raw = json.loads((tmp_path / "scenario_library_normalized.json").read_text(encoding="utf-8"))
    by_id = {row["scenario_id"]: row for row in raw["scenarios"]}

    assert by_id["2020"]["scenario_return_type"] == "historical_episode_loss"
    assert by_id["2020"]["scenario_return_monthly_equivalent"] is None
    assert by_id["equity_shock"]["scenario_return_type"] == "synthetic_one_time_shock"
    assert by_id["equity_shock"]["scenario_return_monthly_equivalent"] is None
    assert by_id["base_historical"]["scenario_return_type"] == "unavailable"


def test_base_monthly_mu_and_normalized_ready(tmp_path: Path) -> None:
    mr = pd.DataFrame(
        {"AAA": [0.01] * 24, "BBB": [0.02] * 24},
        index=pd.date_range("2020-01-31", periods=24, freq="ME"),
    )
    scenario_library = {
        "version": "scenario_library_v1",
        "returns_frequency": "weekly",
        "scenarios": [
            {
                "scenario_id": "base_historical",
                "scenario_type": "base",
                "frequency": "monthly",
                "classification": "diagnostic_only",
                "quality_status": "usable",
                "scenario_portfolio_return": None,
                "asset_covariance": {
                    "native_frequency": "monthly",
                    "normalized_frequency": "monthly",
                    "matrix": _sample_cov(),
                    "quality_status": "usable",
                },
                "factor_covariance": {
                    "native_frequency": "weekly",
                    "normalized_frequency": "monthly_equivalent",
                    "matrix": _sample_cov(),
                    "quality_status": "usable",
                },
                "factor_betas": {"beta_eq": 0.7},
                "warnings": ["returns_frequency=weekly_mixed_cadence_with_weekly_factor_pipeline"],
            },
        ],
    }
    out = build_scenario_library_normalized(
        scenario_library,
        output_dir_final=tmp_path,
        output_dir_csv=tmp_path,
        monthly_returns=mr,
        weights={"AAA": 0.5, "BBB": 0.5},
        tickers=["AAA", "BBB"],
        returns_frequency_pipeline="weekly",
    )
    base = {row["scenario_id"]: row for row in out["scenarios"]}["base_historical"]
    assert base["scenario_return_type"] == "monthly_expected_return"
    assert base["expected_return_method"] == "historical_monthly_mean"
    assert base["optimization_frequency"] == "monthly"
    assert base["classification"] == "ready_for_optimization"
    assert base["usable_for_optimization"] is True
    roles = summarize_normalized_roles(out["scenarios"])
    assert "base_historical" in roles["objective_input"]


def test_synthetic_upstream_insufficient_overridden_when_structural_ok(tmp_path: Path) -> None:
    scenario_library = {
        "version": "scenario_library_v1",
        "scenarios": [
            {
                "scenario_id": "equity_shock",
                "scenario_type": "synthetic_stress",
                "frequency": "monthly",
                "classification": "insufficient_data",
                "quality_status": "insufficient_data",
                "scenario_portfolio_return": -0.15,
                "asset_covariance": {
                    "native_frequency": "monthly",
                    "normalized_frequency": "monthly",
                    "matrix": _sample_cov(),
                    "quality_status": "usable",
                },
                "factor_covariance": {
                    "native_frequency": "weekly",
                    "normalized_frequency": "monthly_equivalent",
                    "matrix": _sample_cov(),
                    "quality_status": "usable",
                },
                "factor_betas": {"5y": {"beta_eq": 1.0}},
                "warnings": [],
            },
        ],
    }
    out = build_scenario_library_normalized(scenario_library, output_dir_final=tmp_path, output_dir_csv=tmp_path)
    row = out["scenarios"][0]
    assert row["upstream_classification"] == "insufficient_data"
    assert row["classification"] == "ready_for_optimization"
    assert row["optimization_role"] == "hard_stress_constraint"


def test_normalized_view_scaling_and_role_mapping() -> None:
    scenario_library = {
        "version": "scenario_library_v1",
        "scenarios": [
            {
                "scenario_id": "S1",
                "scenario_type": "synthetic_stress",
                "frequency": "monthly",
                "classification": "ready_for_optimization",
                "quality_status": "reliable",
                "scenario_portfolio_return": -0.1,
                "asset_covariance": {
                    "native_frequency": "weekly",
                    "normalized_frequency": "monthly_equivalent",
                    "matrix": _sample_cov(),
                },
                "factor_covariance": {
                    "native_frequency": "weekly",
                    "normalized_frequency": "monthly_equivalent",
                    "matrix": _sample_cov(),
                },
                "factor_betas": {"5y": {"beta_eq": 1.0}},
                "warnings": [],
            },
            {
                "scenario_id": "R1",
                "scenario_type": "macro_regime",
                "frequency": "daily",
                "classification": "diagnostic_only",
                "quality_status": "low_confidence",
                "scenario_portfolio_return": None,
                "asset_covariance": {
                    "native_frequency": "daily",
                    "normalized_frequency": "annualized_daily",
                    "matrix": _sample_cov(),
                },
                "factor_covariance": {
                    "native_frequency": "daily",
                    "normalized_frequency": "annualized_daily",
                    "matrix": _sample_cov(),
                },
                "factor_betas": {},
                "warnings": ["frequency_conflict"],
            },
        ],
    }
    out = build_scenario_library_normalized(scenario_library)
    by_id = {row["scenario_id"]: row for row in out["scenarios"]}

    s1 = by_id["S1"]
    assert s1["optimization_role"] == "hard_stress_constraint"
    scaled = s1["asset_covariance_monthly_equivalent"]
    assert scaled["AAA"]["AAA"] == _sample_cov()["AAA"]["AAA"] * WEEKLY_TO_MONTHLY_VARIANCE_FACTOR

    r1 = by_id["R1"]
    assert r1["optimization_role"] == "diagnostic_only"
    assert r1["confidence_weight"] == 0.0
    assert r1["usable_for_optimization"] is False

