"""Smoke tests for auto-generated commentary.txt."""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from src.portfolio_commentary import write_portfolio_commentary, write_stress_commentary


def _test_output_dir(name: str) -> Path:
    root = Path.cwd() / "output" / "codex_test_artifacts" / name
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_write_portfolio_commentary_creates_file() -> None:
    root = _test_output_dir("commentary")
    try:
        final = root / "risk parity portfolio"
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
            "primary_diagnostic_code": "DIAG_LOSS_EQUITY_SHOCK",
            "diagnostic_codes": ["DIAG_LOSS_EQUITY_SHOCK"],
            "fail_reason_code": "DIAG_LOSS_EQUITY_SHOCK",
            "failed_scenario": "equity_shock",
            "failed_test": "Loss",
            "worst_scenario_loss_pct": -0.2,
            "scenario_results": [
                {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True, "loss_ok": True},
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
        assert "DIAG_ATTENTION" in text or "диагност" in text.lower()
        assert "equity_shock" in text
        assert "Risk-Parity baseline" in text or "Risk-Parity" in text
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_write_stress_commentary_from_stress_report() -> None:
    root = _test_output_dir("stress_commentary")
    try:
        final = root / "Main portfolio"
        final.mkdir(parents=True)
        stress = {
            "status": "DIAG_ATTENTION",
            "primary_diagnostic_code": "DIAG_LOSS_EQUITY_SHOCK",
            "diagnostic_codes": ["DIAG_LOSS_EQUITY_SHOCK"],
            "fail_reason_code": "DIAG_LOSS_EQUITY_SHOCK",
            "warning_code": None,
            "worst_scenario_loss_pct": -0.31,
            "failed_scenario": "equity_shock",
            "failed_test": "Loss",
            "max_dd_limit": 0.35,
            "scenario_results": [
                {
                    "scenario_id": "equity_shock",
                    "portfolio_pnl_pct": -0.31,
                    "pass": False,
                    "loss_ok": False,
                    "top1_rc_asset": "URA",
                    "top1_rc_pct": 0.18,
                    "top3_rc_sum_pct": 0.55,
                    "diagnostic_codes": ["DIAG_LOSS_EQUITY_SHOCK"],
                },
            ],
            "historical_results": [
                {
                    "episode": "2020",
                    "max_dd": -0.1,
                    "pnl_real_episode": -0.08,
                    "pass": True,
                    "vol_annualized_episode": 0.4,
                    "diagnostic_code": None,
                    "factor_model_pnl_pct": -0.072,
                    "factor_model_error_pct": 0.008,
                    "historical_factor_attribution": {
                        "method": "model_based_beta_times_realized_factor_shock",
                        "caveat": "Model-based attribution: beta times realized factor shock. This is not a pure realized causal decomposition.",
                        "beta_source": "5y",
                    },
                    "top_factor_drivers": [
                        {"beta_key": "beta_eq", "factor": "Equity", "pnl_pct": -0.05, "abs_pnl_pct": 0.05, "direction": "loss", "rank": 1},
                        {"beta_key": "beta_credit", "factor": "Credit (HY)", "pnl_pct": -0.02, "abs_pnl_pct": 0.02, "direction": "loss", "rank": 2},
                    ],
                    "largest_negative_factor": {"beta_key": "beta_eq", "factor": "Equity", "pnl_pct": -0.05, "abs_pnl_pct": 0.05, "direction": "loss"},
                },
            ],
            "factor_betas_5y": {"beta_eq": 0.77, "beta_vix": -0.12, "beta_us_growth": 0.08},
            "factor_betas_10y": {"beta_eq": 0.81, "beta_oil": 0.11},
        }
        out = write_stress_commentary(final, stress_report=stress, analysis_end="2026-02-28")
        assert out is not None and out.name == "stress_commentary.txt"
        text = out.read_text(encoding="utf-8")
        assert "Executive Summary" in text
        assert "DIAG_ATTENTION" in text
        assert "equity_shock" in text
        assert "stress_report.json" in text
        assert "диагност" in text.lower()
        assert "URA" in text
        assert "Historical factor attribution caveat" in text
        assert "not a pure realized causal decomposition" in text
        assert "top drivers: Equity" in text
        assert "Structural historical factor vulnerability" in text

        stress2 = {
            **stress,
            "factor_regression_5y": {
                "n_obs": 100,
                "r2": 0.9,
                "idiosyncratic_risk": 0.1,
                "adj_r2": 0.89,
                "intercept": 0.001,
                "se_type": "classic_ols",
                "alpha": 0.05,
                "ci_level": 0.95,
                "betas": {"beta_eq": 0.5, "beta_vix": -0.2, "beta_us_growth": 0.15, "beta_oil": 0.05},
                "t": {"beta_eq": 2.0, "beta_vix": -1.8, "beta_us_growth": 1.2, "beta_oil": 0.7},
                "p": {"beta_eq": 0.01, "beta_vix": 0.08, "beta_us_growth": 0.24, "beta_oil": 0.49},
                "ci_low": {"beta_eq": 0.1, "beta_vix": -0.4, "beta_us_growth": -0.1, "beta_oil": -0.08},
                "ci_high": {"beta_eq": 0.9, "beta_vix": 0.0, "beta_us_growth": 0.4, "beta_oil": 0.18},
                "heteroskedasticity_diagnostics": {
                    "method": "breusch_pagan_lm",
                    "h0": "homoskedastic_ols_residuals",
                    "breusch_pagan": {
                        "lm_statistic": 1.2,
                        "df_chi2": 2,
                        "p_value": 0.55,
                        "n_aux_observations": 100,
                        "aux_r_squared": 0.012,
                        "f_statistic": 0.59,
                        "f_df_num": 2,
                        "f_df_den": 97,
                        "f_p_value": 0.56,
                    },
                },
                "serial_correlation_diagnostics": {
                    "method": "durbin_watson_breusch_godfrey_lm",
                    "durbin_watson": 2.01,
                    "breusch_godfrey": [
                        {"lags": 1, "lm_statistic": 0.5, "df_chi2": 1, "p_value": 0.5, "n_aux_observations": 99, "aux_r_squared": 0.01},
                    ],
                },
                "factor_multicollinearity": {
                    "severity": "low",
                    "cond_correlation_matrix": 5.0,
                    "max_vif": 2.1,
                    "max_vif_factor": "equity",
                    "max_vif_is_infinite": False,
                    "strongest_pair": {"factor_i": "equity", "factor_j": "credit", "rho": -0.71},
                    "assessment_ru": "Мягкая: тест.",
                    "pairwise_correlations": [
                        {"factor_i": "equity", "factor_j": "credit", "rho": -0.71},
                    ],
                    "vif_by_factor": {"equity": 2.1, "credit": 1.5, "vix": 1.4},
                    "method": "pearson_sample_corr_vif_raw_regressors",
                    "n_obs_factors": 100,
                },
            },
            "factor_betas_rolling_windows_weeks": {"3y": 156},
            "factor_betas_rolling_summary": {
                "3y": {
                    "beta_eq": {"n_points": 10, "mean": 0.5, "median": 0.5, "p10": 0.4, "p90": 0.6},
                    "beta_vix": {"n_points": 10, "mean": -0.2, "median": -0.2, "p10": -0.3, "p90": -0.1},
                    "beta_us_growth": {"n_points": 10, "mean": 0.1, "median": 0.1, "p10": 0.0, "p90": 0.2},
                    "beta_oil": {"n_points": 10, "mean": 0.05, "median": 0.05, "p10": -0.02, "p90": 0.1},
                }
            },
            "factor_betas_rolling_artifacts": {"plot_png_by_window": {"3y": "rolling_factor_betas_3y.png"}},
            "factor_betas_stability": {
                "overall_severity": "high",
                "severity_distribution": {
                    "shares": {"low": 0.1, "moderate": 0.1, "high": 0.8, "unknown": 0.0},
                    "counts": {"low": 1, "moderate": 1, "high": 8, "unknown": 0},
                    "n": 10,
                },
                "severity_distribution_warning": "thresholds_may_be_too_strict_consider_relaxing_magnitude_to_1_5_2_5",
                "by_beta": {
                    "beta_eq": {
                        "combined_severity": "high",
                        "sign_stability": {
                            "severity": "low",
                            "dominant_sign": "positive",
                            "dominant_sign_share": 0.95,
                            "sign_change_count": 0,
                        },
                        "magnitude_stability": {
                            "severity": "moderate",
                            "p90_minus_p10": 0.25,
                            "relative_band": 1.2,
                        },
                        "specification_sensitivity": {
                            "severity": "low",
                            "relative_median_span": 0.2,
                            "sign_disagreement": False,
                        },
                        "oos_stability": {
                            "severity": "high",
                            "n_tests": 12,
                            "sign_match_share": 0.5,
                            "relative_magnitude_degradation": 2.1,
                        },
                    }
                },
            },
            "factor_covariance": {
                "factor_order": ["equity", "credit"],
                "exposure_vector": {
                    "zero_filled_beta_keys": ["beta_rr"],
                },
                "portfolio_factor_risk": {
                    "base": {
                        "classification": "data_driven",
                        "portfolio_factor_vol": 0.04,
                        "portfolio_factor_variance": 0.0016,
                    },
                    "stress_empirical": {
                        "classification": "data_driven",
                        "portfolio_factor_vol": 0.06,
                        "portfolio_factor_variance": 0.0036,
                    },
                    "stress_overlay": {
                        "classification": "hypothetical",
                        "portfolio_factor_vol": 0.08,
                        "portfolio_factor_variance": 0.0064,
                    },
                },
                "comparison": {
                    "empirical_change": [
                        {"factor_i": "equity", "factor_j": "credit", "corr_delta": 0.25, "abs_corr_delta": 0.25},
                    ],
                    "overlay_amplification": [
                        {"factor_i": "equity", "factor_j": "credit", "corr_delta": 0.15, "abs_corr_delta": 0.15},
                    ],
                },
                "RC_stability_flag": {
                    "threshold_pct": 30.0,
                    "overall_flag": True,
                    "by_factor": [
                        {"factor": "equity", "RC_stability_flag": True},
                        {"factor": "credit", "RC_stability_flag": False},
                    ],
                },
                "beta_sensitivity": {
                    "base": {"classification": "data_driven", "vol_min": 0.03, "vol_max": 0.05},
                    "stress_empirical": {"classification": "data_driven", "vol_min": 0.05, "vol_max": 0.07},
                    "stress_overlay": {"classification": "hypothetical", "vol_min": 0.07, "vol_max": 0.09},
                },
                "covariance_stability_check": {
                    "threshold_pct": 35.0,
                    "overall_flag": True,
                },
            },
        }
        out2 = write_stress_commentary(final, stress_report=stress2, analysis_end="2026-02-28")
        text2 = out2.read_text(encoding="utf-8")
        assert "5Y" in text2
        assert "R" in text2
        assert "idiosyncratic risk" in text2
        assert "0.1000" in text2
        assert "rolling_factor_betas_3y.png" in text2
        assert "beta_vix" in text2
        assert "beta_us_growth" in text2
        assert "beta_oil" in text2
        assert "Durbin" in text2
        assert "Breusch" in text2
        assert "VIF" in text2
        assert "-0.7100" in text2
        assert "Factor beta stability diagnostics" in text2
        assert "Severity distribution warning" in text2
        assert "OOS=high" in text2
        assert "Factor covariance matrix" in text2
        assert "data_driven" in text2
        assert "hypothetical" in text2
        assert "Empirical change" in text2
        assert "Overlay amplification" in text2
        assert "RC_stability_flag" in text2
        assert "Covariance stability check" in text2
    finally:
        shutil.rmtree(root, ignore_errors=True)
