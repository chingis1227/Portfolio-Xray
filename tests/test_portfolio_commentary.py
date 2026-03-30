"""Smoke tests for auto-generated commentary.txt."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.portfolio_commentary import write_portfolio_commentary, write_stress_commentary


def test_write_portfolio_commentary_creates_file(tmp_path: Path) -> None:
    final = tmp_path / "risk parity portfolio"
    csv_dir = final / "results_csv"
    csv_dir.mkdir(parents=True)
    pd.DataFrame(
        [{"window_months": 120, "cagr": 0.08, "vol_annual": 0.07, "sharpe": 0.9, "sortino": 1.2,
          "beta_portfolio": 0.5, "max_drawdown": -0.1, "corr_base": 0.3, "treynor": 0.1}]
    ).to_csv(csv_dir / "portfolio_metrics_10y.csv", index=False)
    s = pd.Series({"A": 0.2, "B": 0.2, "C": 0.2, "D": 0.2, "E": 0.2})
    s.round(3).to_csv(csv_dir / "rc_vol_10y.csv", header=True)

    stress = {
        "status": "DIAG_ATTENTION",
        "primary_diagnostic_code": "DIAG_RC_TOP1_EQUITY_SHOCK",
        "diagnostic_codes": ["DIAG_RC_TOP1_EQUITY_SHOCK"],
        "fail_reason_code": "FAIL_X",
        "failed_scenario": "credit_shock",
        "failed_test": "Loss",
        "worst_scenario_loss_pct": -0.2,
        "scenario_results": [
            {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True},
        ],
    }
    pm = {
        "cagr": 0.08,
        "vol_annual": 0.07,
        "max_drawdown": -0.1,
        "sharpe": 0.9,
        "sortino": 1.2,
        "beta_portfolio": 0.5,
        "corr_base": 0.3,
        "treynor": 0.1,
    }
    out = write_portfolio_commentary(
        final,
        output_dir_csv=csv_dir,
        portfolio_metrics_10y=pm,
        stress_report=stress,
        portfolio_valid=True,
        analysis_end="2026-02-28",
    )
    assert out is not None
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "Executive Summary" in text
    assert "DIAG_ATTENTION" in text or "диагностик" in text.lower()
    assert "credit_shock" in text
    assert "Risk-Parity baseline" in text or "Risk-Parity" in text


def test_write_stress_commentary_from_stress_report(tmp_path: Path) -> None:
    final = tmp_path / "Main portfolio"
    final.mkdir(parents=True)
    stress = {
        "status": "DIAG_ATTENTION",
        "primary_diagnostic_code": "DIAG_RC_TOP1_EQUITY_SHOCK",
        "diagnostic_codes": ["DIAG_RC_TOP1_EQUITY_SHOCK"],
        "fail_reason_code": "DIAG_RC_TOP1_EQUITY_SHOCK",
        "warning_code": "WARN_ROLE_EQUITY_DEFENSIVE_WEAK",
        "worst_scenario_loss_pct": -0.31,
        "failed_scenario": "equity_shock",
        "failed_test": "RC_Top1",
        "rc_asset_cap_used": 0.1,
        "stress_top3_rc_sum_cap": 0.7,
        "max_dd_limit": 0.35,
        "scenario_results": [
            {
                "scenario_id": "equity_shock",
                "portfolio_pnl_pct": -0.31,
                "pass": False,
                "loss_ok": True,
                "role_ok": True,
                "rc1_ok": False,
                "rc3_ok": True,
                "top1_rc_asset": "URA",
                "top1_rc_pct": 0.18,
                "diagnostic_codes": ["DIAG_RC_TOP1_EQUITY_SHOCK"],
            },
        ],
        "historical_results": [
            {"episode": "2020", "max_dd": -0.1, "pass": True, "vol_annualized_episode": 0.4, "diagnostic_code": None},
        ],
        "factor_betas_5y": {"beta_eq": 0.77},
        "factor_betas_10y": {"beta_eq": 0.81},
    }
    out = write_stress_commentary(final, stress_report=stress, analysis_end="2026-02-28")
    assert out is not None and out.name == "stress_commentary.txt"
    text = out.read_text(encoding="utf-8")
    assert "Executive Summary" in text
    assert "DIAG_ATTENTION" in text
    assert "equity_shock" in text
    assert "нестрессирующая" in text or "диагностик" in text.lower()
    assert "URA" in text

    # Regression + rolling blocks when present in stress_report
    stress2 = {
        **stress,
        "factor_regression_5y": {
            "n_obs": 100,
            "r2": 0.9,
            "adj_r2": 0.89,
            "intercept": 0.001,
            "se_type": "classic_ols",
            "alpha": 0.05,
            "ci_level": 0.95,
            "betas": {"beta_eq": 0.5},
            "t": {"beta_eq": 2.0},
            "p": {"beta_eq": 0.01},
            "ci_low": {"beta_eq": 0.1},
            "ci_high": {"beta_eq": 0.9},
            "factor_multicollinearity": {
                "severity": "low",
                "cond_correlation_matrix": 5.0,
                "max_vif": 2.1,
                "max_vif_factor": "equity",
                "max_vif_is_infinite": False,
                "strongest_pair": {"factor_i": "equity", "factor_j": "credit", "rho": -0.71},
                "assessment_ru": "Низкая: тест.",
                "pairwise_correlations": [
                    {"factor_i": "equity", "factor_j": "credit", "rho": -0.71},
                ],
                "vif_by_factor": {"equity": 2.1, "credit": 1.5},
                "method": "pearson_sample_corr_vif_raw_regressors",
                "n_obs_factors": 100,
            },
        },
        "factor_betas_rolling_windows_weeks": {"3y": 156},
        "factor_betas_rolling_summary": {
            "3y": {
                "beta_eq": {"n_points": 10, "mean": 0.5, "median": 0.5, "p10": 0.4, "p90": 0.6},
            }
        },
        "factor_betas_rolling_artifacts": {"plot_png_by_window": {"3y": "rolling_factor_betas_3y.png"}},
    }
    out2 = write_stress_commentary(final, stress_report=stress2, analysis_end="2026-02-28")
    text2 = out2.read_text(encoding="utf-8")
    assert "Портфельная факторная регрессия (5Y)" in text2
    assert "R²=" in text2 or "R" in text2
    assert "Скользящие окна" in text2
    assert "rolling_factor_betas_3y.png" in text2
    assert "Мультиколлинеарность факторов" in text2
    assert "VIF по факторам:" in text2
    assert "-0.7100" in text2
