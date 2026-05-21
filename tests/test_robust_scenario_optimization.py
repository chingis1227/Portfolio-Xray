"""Tests for scenario-based robust optimization v1."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.stress import PRODUCTION_FACTOR_BETA_KEYS

from src.robust_scenario_optimization import (
    OBJECTIVE_LOWER_HALF_MEAN,
    _asset_betas_df_from_stress,
    build_robust_optimization_inputs,
    export_robust_optimization_outputs,
    lower_half_mean,
    run_robust_scenario_optimization,
)
from src.optimization import MIN_WEIGHT_DEFAULT, _build_bounds


def test_lower_half_mean_even_and_odd_n() -> None:
    lh, k, _ = lower_half_mean(np.array([-0.10, -0.05, 0.01, 0.02]))
    assert k == 2
    assert abs(lh - (-0.075)) < 1e-9
    lh5, k5, _ = lower_half_mean(np.array([-0.10, -0.08, -0.05, 0.01, 0.02]))
    assert k5 == 3


def _minimal_asset_factor_betas(tickers: list[str]) -> dict:
    row = {k: 0.01 for k in PRODUCTION_FACTOR_BETA_KEYS}
    row["beta_eq"] = 1.0
    return {t: {"betas": dict(row)} for t in tickers}


def test_asset_betas_df_from_stress_has_beta_columns() -> None:
    tickers = ["AAA", "BBB"]
    sr = {"asset_factor_betas": _minimal_asset_factor_betas(tickers)}
    df, warns = _asset_betas_df_from_stress(sr, tickers)
    assert list(df.columns) == list(PRODUCTION_FACTOR_BETA_KEYS)
    assert df.loc["AAA", "beta_eq"] == 1.0
    assert not any("fallback_portfolio" in w for w in warns)


def test_asset_betas_fallback_portfolio_warns() -> None:
    tickers = ["AAA", "BBB"]
    sr = {"factor_betas_5y": {k: (0.5 if k == "beta_eq" else 0.0) for k in PRODUCTION_FACTOR_BETA_KEYS}}
    df, warns = _asset_betas_df_from_stress(sr, tickers)
    assert any("fallback_portfolio_factor_betas_5y" in w for w in warns)
    assert df.loc["AAA", "beta_eq"] == 0.5


def test_synthetic_row_nonzero_with_asset_betas() -> None:
    cov = {"AAA": {"AAA": 0.0004, "BBB": 0.0001}, "BBB": {"AAA": 0.0001, "BBB": 0.0009}}
    tickers = ["AAA", "BBB"]
    normalized = {
        "version": "scenario_library_normalized_v1",
        "scenarios": [
            {
                "scenario_id": "base_historical",
                "scenario_type": "base",
                "optimization_role": "objective_input",
                "confidence_weight": 1.0,
                "expected_returns_by_asset": {"AAA": 0.01, "BBB": 0.012},
                "asset_covariance_monthly_equivalent": cov,
            },
            {
                "scenario_id": "equity_shock",
                "scenario_type": "synthetic_stress",
                "optimization_role": "soft_constraint",
                "confidence_weight": 1.0,
                "scenario_factor_move": {"shock_eq": -0.10},
            },
        ],
    }
    stress = {"asset_factor_betas": _minimal_asset_factor_betas(tickers)}
    inputs = build_robust_optimization_inputs(
        scenario_library_normalized=normalized,
        stress_report=stress,
        risk_tickers=tickers,
        lambdas={"vol": 0.0, "stress_penalty": 0.0, "hhi": 0.0},
    )
    eq_idx = inputs.scenario_ids.index("equity_shock")
    assert float(inputs.C[eq_idx].sum()) < -0.15


def test_build_inputs_and_optimize_round_trip(tmp_path: Path) -> None:
    cov = {"AAA": {"AAA": 0.0004, "BBB": 0.0001}, "BBB": {"AAA": 0.0001, "BBB": 0.0009}}
    normalized = {
        "version": "scenario_library_normalized_v1",
        "scenarios": [
            {
                "scenario_id": "base_historical",
                "scenario_type": "base",
                "optimization_role": "objective_input",
                "confidence_weight": 1.0,
                "expected_returns_by_asset": {"AAA": 0.01, "BBB": 0.012},
                "asset_covariance_monthly_equivalent": cov,
                "factor_betas_used": {"5y": {"beta_eq": 1.0}},
            },
            {
                "scenario_id": "equity_shock",
                "scenario_type": "synthetic_stress",
                "optimization_role": "hard_stress_constraint",
                "confidence_weight": 1.0,
                "scenario_factor_move": {"shock_eq": -0.20},
                "factor_betas_used": {"5y": {"beta_eq": 1.0}},
            },
            {
                "scenario_id": "2020",
                "scenario_type": "historical_stress",
                "optimization_role": "soft_constraint",
                "confidence_weight": 0.5,
                "scenario_asset_return": {"AAA": -0.05, "BBB": -0.08},
                "factor_betas_used": {"5y": {"beta_eq": 1.0}},
            },
        ],
    }
    stress = {"asset_factor_betas": _minimal_asset_factor_betas(["AAA", "BBB"])}
    inputs = build_robust_optimization_inputs(
        scenario_library_normalized=normalized,
        stress_report=stress,
        risk_tickers=["AAA", "BBB"],
        objective_mode=OBJECTIVE_LOWER_HALF_MEAN,
        lambdas={"vol": 0.0, "stress_penalty": 0.0, "hhi": 0.0},
    )
    assert inputs.C.shape == (3, 2)
    bounds = _build_bounds(inputs.ticker_order, 2, MIN_WEIGHT_DEFAULT, None, None)
    res = run_robust_scenario_optimization(inputs, bounds=bounds, warm_starts=[np.array([0.5, 0.5])])
    assert res["weights_vec"].sum() > 0.99
    assert res["solver"]["name"] == "SLSQP"
    assert res["solver"]["status"] == ("OK" if res["solver"]["success"] else "APPROXIMATE")
    assert res["solver"]["fallback_used"] is False
    assert res["solver"]["optimization_quality_status"] == (
        "clean_solve" if res["solver"]["success"] else "approximate_solver"
    )
    paths = export_robust_optimization_outputs(res, inputs, output_dir=tmp_path)
    assert (tmp_path / "robust_optimization_v1_summary.json").is_file()
    summary = json.loads((tmp_path / "robust_optimization_v1_summary.json").read_text(encoding="utf-8"))
    assert "lower_half_mean" in summary
    assert summary["solver"]["name"] == "SLSQP"
    assert summary["solver_status"] == summary["solver"]["status"]
    assert summary["fallback_used"] is False
    assert summary["optimization_quality_status"] == summary["solver"]["optimization_quality_status"]
