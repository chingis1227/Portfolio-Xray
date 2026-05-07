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
        assert "DIAG_ATTENTION" in text or "diagnostic" in text.lower()
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
            "factor_betas_10y": {"beta_eq": 0.81},
            "factor_betas_adjusted": {
                "raw": {"beta_eq": 0.77, "beta_vix": -0.12, "beta_us_growth": 0.08},
                "adjusted": {"beta_eq": 0.74, "beta_vix": -0.08, "beta_us_growth": 0.08},
                "severity_by_beta": {"beta_eq": "high", "beta_vix": "moderate", "beta_us_growth": "low"},
                "adjustment_reason_by_beta": {
                    "beta_eq": "high_severity_shrink_toward_10y_anchor",
                    "beta_vix": "moderate_severity_shrink_toward_10y_anchor",
                    "beta_us_growth": "low_severity_keep_5y_raw",
                },
                "beta_5y_vs_10y_divergence": {
                    "strong_divergence_any": True,
                    "strong_divergence_betas": ["beta_vix"],
                },
            },
            "raw_vs_adjusted_pnl_signal": {
                "material_difference_any": True,
                "material_scenarios": ["equity_shock"],
                "material_historical_episodes": ["2020"],
                "synthetic": [
                    {
                        "scenario_id": "equity_shock",
                        "pnl_raw": -0.31,
                        "pnl_adjusted": -0.24,
                        "pnl_delta": 0.07,
                        "pnl_relative_delta": 0.2258,
                        "material_difference": True,
                    }
                ],
                "historical": [
                    {
                        "episode": "2020",
                        "pnl_raw": -0.072,
                        "pnl_adjusted": -0.051,
                        "pnl_delta": 0.021,
                        "pnl_relative_delta": 0.2917,
                        "material_difference": True,
                    }
                ],
            },
        }
        out = write_stress_commentary(final, stress_report=stress, analysis_end="2026-02-28")
        assert out is not None and out.name == "stress_commentary.txt"
        text = out.read_text(encoding="utf-8")
        assert "Executive Summary" in text
        assert "DIAG_ATTENTION" in text
        assert "equity_shock" in text
        assert "stress_report.json" in text
        assert "diagnostic" in text.lower()
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
                "betas": {"beta_eq": 0.5, "beta_vix": -0.2, "beta_us_growth": 0.15},
                "t": {"beta_eq": 2.0, "beta_vix": -1.8, "beta_us_growth": 1.2},
                "p": {"beta_eq": 0.01, "beta_vix": 0.08, "beta_us_growth": 0.24},
                "ci_low": {"beta_eq": 0.1, "beta_vix": -0.4, "beta_us_growth": -0.1},
                "ci_high": {"beta_eq": 0.9, "beta_vix": 0.0, "beta_us_growth": 0.4},
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
                    "zero_filled_beta_keys": ["beta_rr", "beta_oil"],
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
                "forecast_quality": {
                    "status": "available",
                    "method": "rolling_5y_covariance_vs_next_1y_realized_factor_risk",
                    "train_weeks": 260,
                    "holdout_weeks": 52,
                    "step_weeks": 52,
                    "summary": {
                        "n_forecasts": 4,
                        "median_abs_vol_error_pct": 0.18,
                        "hit_rate_abs_vol_error_le_10pct": 0.25,
                        "hit_rate_abs_vol_error_le_20pct": 0.75,
                        "hit_rate_abs_vol_error_le_30pct": 1.0,
                        "median_corr_rmse": 0.12,
                        "overall_severity": "moderate",
                    },
                    "rows": [],
                },
            },
            "factor_betas_kalman": {
                "status": "available",
                "latest": {"beta_eq": 0.52, "beta_oil": 0.06},
                "latest_raw": {"beta_eq": 0.52, "beta_oil": 0.06},
                "latest_date": "2026-02-27",
                "n_observations": 260,
                "beta_cap_abs": 3.0,
                "cap_diagnostics": {},
                "uncertainty_by_beta": {"beta_eq": "low", "beta_oil": "moderate"},
                "divergence_vs_5y": {"divergent_betas": [], "by_beta": {}},
            },
            "diagnostic_oil_beta": {
                "role": "diagnostic_warning_only",
                "production_status": "deprecated_removed_from_production_beta_outputs",
                "factor": "oil",
                "beta_key": "beta_oil",
                "commodity_factor": "commodity",
                "commodity_beta_key": "beta_cmd",
                "beta_oil_5y": 0.05,
                "beta_oil_10y": 0.07,
                "beta_commodity_5y": 0.2,
                "beta_commodity_10y": 0.25,
                "oil_commodity_correlation": {
                    "factor_regression_5y": 0.86,
                    "factor_regression_10y": 0.81,
                    "factor_covariance_base": 0.84,
                },
                "oil_commodity_vif": {"oil_5y": 4.8, "commodity_5y": 4.7},
                "collinearity_signal": {"severity": "moderate"},
                "kalman_oil": {"latest": 0.06, "latest_raw": 0.06, "uncertainty_class": "moderate", "latest_date": "2026-02-27"},
            },
            "macro_regime_diagnostics": {
                "axis_model": {
                    "version": "macro_two_axis_v1",
                    "frequency": "monthly",
                    "neutral_band_abs": 0.25,
                    "look_ahead_protection": "lag_1m",
                    "look_ahead_caveat": (
                        "Look-ahead protection is a 1-month publication lag only. "
                        "Release-date accurate vintage handling is out of scope for v1."
                    ),
                },
                "method_disclaimer": (
                    "macro_two_axis_v1 is a diagnostic-only macro regime classifier. "
                    "It does not affect optimizer weights, mandate gates, stress pass/fail, "
                    "or weight release."
                ),
                "current_regime": "stagflation",
                "axis_scores_latest": {
                    "growth_score": -0.42,
                    "inflation_score": 0.81,
                    "growth_blocks": {"growth_labor": -0.5, "growth_credit": -0.3},
                    "inflation_blocks": {"core_inflation": 0.8, "wages": 0.6},
                },
                "regime_confidence": "medium",
                "confidence_level": "medium",
                "regime_transition_warning": False,
                "score_lag_months": 1,
                "score_start_date": "2003-12-31",
                "regime_label_start_date": "2004-01-31",
                "available_blocks": [
                    "growth_labor",
                    "growth_consumer",
                    "growth_credit",
                    "core_inflation",
                    "headline_inflation",
                    "wages",
                    "inflation_expectations",
                ],
                "missing_blocks": ["growth_business_activity", "growth_nowcast", "business_price_pressure"],
                "optional_blocks_missing": ["growth_nowcast"],
                "planned_not_loaded": [],
                "coverage_ratio": 0.7,
                "coverage_tier": "reduced",
                "data_sources_used": {"eci": "fred", "ahe": "fred"},
                "available_regimes_count": 2,
                "available_regimes_by_quality": {"usable": 1, "reliable": 1},
                "stability_summary": {
                    "warning": "Stability threshold is a global heuristic, not factor-specific calibration.",
                    "policy_signal_counts": {
                        "green/general_signal": 2,
                        "yellow/regime_only": 1,
                        "red/do_not_use_as_single_signal": 1,
                    },
                    "top_unstable_betas": [
                        {
                            "beta_key": "beta_eq",
                            "policy_signal": "red/do_not_use_as_single_signal",
                            "max_abs_regime_beta_gap": 0.72,
                        }
                    ],
                },
                "regime_label_quality_check": {
                    "status": "available",
                    "by_regime": {
                        "goldilocks": {"n_obs": 8, "quality_status": "insufficient_data"},
                        "reflation": {"n_obs": 14, "quality_status": "low_confidence"},
                        "stagflation": {"n_obs": 32, "quality_status": "usable"},
                        "recession_disinflation": {"n_obs": 68, "quality_status": "reliable"},
                        "neutral_transition": {"n_obs": 6, "quality_status": "insufficient_data"},
                    },
                    "stability_summary": {
                        "n_switches": 18,
                        "avg_months_between_switches": 2.1,
                        "share_one_month_regimes": 0.31,
                        "share_regimes_lt_3m": 0.58,
                    },
                    "overall_assessment": {
                        "history_usable": False,
                        "classifier_noise_warning": True,
                        "warnings": [
                            "at least one regime has fewer than 24 observations; treat regime-specific betas/covariance/RC cautiously",
                            "regime switching appears noisy; classifier may be too unstable for strong regime-specific inference",
                        ],
                    },
                },
            },
            "factor_variance_decomposition": {
                "status": "available",
                "method": "r2_scaled_factor_rc_plus_residual",
                "variance_scale": "weekly",
                "r2": 0.75,
                "residual_share": 0.25,
                "residual_severity": "low",
                "residual_recommendation": "Factor decomposition is suitable as a diagnostic risk-management signal.",
                "cross_check": {
                    "status": "warning",
                    "variance_based_explained_share": 0.73,
                    "absolute_difference": 0.02,
                    "warning_code": "WARN_FACTOR_VARIANCE_DECOMP_MISMATCH",
                },
                "warnings": ["WARN_FACTOR_VARIANCE_DECOMP_MISMATCH"],
                "risk_adders": [{"factor": "equity", "net_total_variance_share": 0.4}],
                "hedgers": [{"factor": "usd", "net_total_variance_share": -0.1}],
                "neutral_factors": [{"factor": "credit", "net_total_variance_share": 0.0}],
                "gross_top_contributors_abs": [{"factor": "equity", "gross_total_variance_share": 0.5}],
                "stability": {
                    "status": "available",
                    "overall_severity": "moderate",
                    "r2": {"p10": 0.42, "p90": 0.8, "severity": "low"},
                },
            },
            "portfolio_pca": {
                "status": "available",
                "method": "portfolio_asset_pca_weekly",
                "window_weeks": 260,
                "n_obs": 260,
                "n_assets": 3,
                "included_assets": ["A", "B", "C"],
                "raw": {
                    "status": "available",
                    "covariance_pca": {
                        "status": "available",
                        "interpretation": "risk_dominance",
                        "pc1_explained_variance_ratio": 0.72,
                        "pc1_concentration_ratio": 2.16,
                        "pc1_severity": "high",
                        "effective_number_of_bets": 1.7,
                        "effective_number_of_bets_ratio": 0.57,
                        "enb_severity": "low",
                        "rolling_pc1": {"summary": {"stability_severity": "high", "trend_slope_per_year": 0.12}},
                        "components": [
                            {
                                "component": "PC1",
                                "top_positive_loadings": [{"asset": "A", "loading": 0.7}, {"asset": "B", "loading": 0.6}],
                                "top_negative_loadings": [{"asset": "C", "loading": -0.3}],
                            }
                        ],
                        "pc1_factor_correlations": {
                            "status": "available",
                            "top_abs_correlations": [{"factor": "equity", "correlation": 0.81, "abs_correlation": 0.81}],
                        },
                    },
                    "correlation_pca": {
                        "status": "available",
                        "interpretation": "structure",
                        "pc1_explained_variance_ratio": 0.61,
                        "pc1_concentration_ratio": 1.83,
                        "pc1_severity": "high",
                        "effective_number_of_bets": 2.0,
                        "effective_number_of_bets_ratio": 0.67,
                        "enb_severity": "low",
                        "rolling_pc1": {"summary": {"stability_severity": "moderate"}},
                        "components": [{"component": "PC1", "top_positive_loadings": [{"asset": "A", "loading": 0.58}], "top_negative_loadings": []}],
                    },
                },
                "residual": {
                    "status": "available",
                    "covariance_pca": {
                        "status": "available",
                        "interpretation": "risk_dominance",
                        "pc1_explained_variance_ratio": 0.66,
                        "pc1_concentration_ratio": 1.98,
                        "pc1_severity": "high",
                        "effective_number_of_bets": 1.9,
                        "effective_number_of_bets_ratio": 0.63,
                        "enb_severity": "low",
                        "rolling_pc1": {"summary": {"stability_severity": "high"}},
                        "components": [{"component": "PC1", "top_positive_loadings": [], "top_negative_loadings": []}],
                    },
                    "correlation_pca": {
                        "status": "available",
                        "interpretation": "structure",
                        "pc1_explained_variance_ratio": 0.52,
                        "pc1_concentration_ratio": 1.56,
                        "pc1_severity": "moderate",
                        "effective_number_of_bets": 2.2,
                        "effective_number_of_bets_ratio": 0.73,
                        "enb_severity": "low",
                        "rolling_pc1": {"summary": {"stability_severity": "low"}},
                        "components": [{"component": "PC1", "top_positive_loadings": [], "top_negative_loadings": []}],
                    },
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
        assert "Oil diagnostic/stress warning" in text2
        assert "role=diagnostic_warning_only" in text2
        assert "beta_oil is deprecated in production beta outputs" in text2
        assert "beta_oil" not in text2.split("Oil diagnostic/stress warning", 1)[0]
        assert "Durbin" in text2
        assert "Breusch" in text2
        assert "VIF" in text2
        assert "-0.7100" in text2
        assert "Factor beta stability diagnostics" in text2
        assert "Severity distribution warning" in text2
        assert "OOS=high" in text2
        assert "Stability-adjusted factor beta overlay" in text2
        assert "Strong 5Y vs 10Y divergence" in text2
        assert "Material raw vs adjusted synthetic PnL differences" in text2
        assert "Factor covariance matrix" in text2
        assert "data_driven" in text2
        assert "hypothetical" in text2
        assert "Empirical change" in text2
        assert "Overlay amplification" in text2
        assert "RC_stability_flag" in text2
        assert "Covariance stability check" in text2
        assert "Forecast quality" in text2
        assert "median_abs_vol_error=18.0%" in text2
        assert "hit20=75.0%" in text2
        assert "severity=moderate" in text2
        assert "Macro regime diagnostics" in text2
        assert "Method=macro_two_axis_v1" in text2
        assert "Current regime: stagflation" in text2
        assert "inflation_score=0.810" in text2
        assert "confidence=medium" in text2
        assert "transition_warning=False" in text2
        assert "Coverage tier: reduced" in text2
        assert "Optional blocks missing" in text2
        assert "ECI is quarterly" in text2
        assert "Top unstable regime betas" in text2
        assert "Look-ahead protection is a 1-month publication lag only" in text2
        assert "macro_two_axis_v1 is a diagnostic-only macro regime classifier" in text2
        assert "Regime Label Quality Check" in text2
        assert "weak regimes (<24 obs)" in text2
        assert "betas/covariance/RC cautiously" in text2
        assert "classifier may be too noisy" in text2
        assert "Factor variance decomposition" in text2
        assert "variance_scale=weekly" in text2
        assert "Risk adders" in text2
        assert "Hedgers" in text2
        assert "Neutral factors" in text2
        assert "Gross concentration" in text2
        assert "WARN_FACTOR_VARIANCE_DECOMP_MISMATCH" in text2
        assert "Portfolio PCA diagnostics" in text2
        assert "risk dominance" in text2
        assert "structure" in text2
        assert "Raw covariance PCA" in text2
        assert "Raw correlation PCA" in text2
        assert "High residual PC1" in text2
    finally:
        shutil.rmtree(root, ignore_errors=True)
