"""Tests for stability-adjusted factor beta overlay diagnostics."""
from __future__ import annotations

from src import stress_factors as sf


def test_build_factor_beta_adjustment_overlay_shrinks_and_flags_divergence() -> None:
    out = sf.build_factor_beta_adjustment_overlay(
        factor_betas_5y={
            "beta_eq": 1.0,
            "beta_credit": 0.10,
            "beta_usd": 0.10,
            "beta_oil": 0.77,
        },
        factor_betas_10y={
            "beta_eq": 0.20,
            "beta_credit": 0.25,
            "beta_usd": -0.10,
            "beta_oil": -0.77,
        },
        factor_betas_stability={
            "by_beta": {
                "beta_eq": {"combined_severity": "high"},
                "beta_credit": {"combined_severity": "low"},
                "beta_usd": {"combined_severity": "moderate"},
                "beta_oil": {"combined_severity": "high"},
            }
        },
    )
    assert "beta_oil" not in out["raw"]
    assert "beta_oil" not in out["adjusted"]
    assert "beta_oil" not in out["confidence_by_beta"]
    assert out["adjusted"]["beta_eq"] == 0.6
    assert out["adjusted"]["beta_credit"] == 0.1
    assert abs(out["adjusted"]["beta_usd"] - 0.05) < 1e-12
    assert out["confidence_by_beta"]["beta_eq"] == 0.5
    assert out["confidence_by_beta"]["beta_usd"] == 0.75
    div = out["beta_5y_vs_10y_divergence"]
    assert div["by_beta"]["beta_credit"]["strong_divergence"] is True
    assert div["by_beta"]["beta_usd"]["strong_divergence"] is True
    assert div["strong_divergence_any"] is True
    assert "beta_credit" in div["strong_divergence_betas"]
    assert "beta_usd" in div["strong_divergence_betas"]


def test_build_raw_vs_adjusted_pnl_signal_marks_material_differences() -> None:
    out = sf.build_raw_vs_adjusted_pnl_signal(
        synthetic_overlay={
            "scenarios": [
                {
                    "scenario_id": "equity_shock",
                    "pnl_model_raw": -0.04,
                    "pnl_model_adjusted": -0.02,
                },
                {
                    "scenario_id": "rates_shock",
                    "pnl_model_raw": 0.005,
                    "pnl_model_adjusted": 0.0055,
                },
            ]
        },
        factor_beta_shock_oos_raw={
            "episodes": [
                {"episode": "2020", "pnl_model_5y": -0.03},
            ]
        },
        factor_beta_shock_oos_adjusted={
            "episodes": [
                {"episode": "2020", "pnl_model_adjusted": -0.015},
            ]
        },
    )
    assert out["material_difference_any"] is True
    assert "equity_shock" in out["material_scenarios"]
    assert out["synthetic"][0]["material_difference"] is True
    assert out["synthetic"][1]["material_difference"] is False
    assert out["historical"][0]["material_difference"] is True
