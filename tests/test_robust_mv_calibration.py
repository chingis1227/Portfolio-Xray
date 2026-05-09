from __future__ import annotations

from src.robust_mv_calibration import (
    build_no_feasible_lambda_diagnostic,
    classify_robust_mv_mandate,
    pick_least_bad_lambda,
    synthetic_mandatory_loss_detail,
)


def _stress_rows_all_pass() -> dict:
    scenarios = [
        "equity_shock",
        "credit_shock",
        "rates_shock",
        "inflation_stagflation",
        "liquidity_shock",
        "recession_severe",
    ]
    return {
        "scenario_results": [
            {
                "scenario_id": sid,
                "pass": True,
                "top1_rc_pct": 0.2,
                "top3_rc_sum_pct": 0.55,
            }
            for sid in scenarios
        ]
    }


def test_synthetic_mandatory_loss_detail_all_pass():
    ok, fails = synthetic_mandatory_loss_detail(_stress_rows_all_pass())
    assert ok and fails == []


def test_synthetic_mandatory_loss_detail_detects_missing_rows():
    stress = {"scenario_results": [{"scenario_id": "equity_shock", "pass": True}]}
    ok, fails = synthetic_mandatory_loss_detail(stress)
    assert ok is False
    assert len(fails) >= 1


def test_classify_mandate_pass_and_borderline_vol():
    stress = _stress_rows_all_pass()
    ev = classify_robust_mv_mandate(
        portfolio_valid=True,
        target_vol_annual=0.15,
        vol_annual_10y=0.13,
        target_max_drawdown_pct=-0.30,
        mandate_max_drawdown_realized=-0.10,
        max_single_security_weight_pct=0.30,
        weights={"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25},
        stress_report=stress,
        calibration_limits={},
        enforce_synthetic_vs_mandate_dd=True,
    )
    assert ev["mandate_classification"] == "pass"

    ev2 = classify_robust_mv_mandate(
        portfolio_valid=True,
        target_vol_annual=0.15,
        vol_annual_10y=0.145,  # >= 92% of 0.15 → borderline
        target_max_drawdown_pct=-0.30,
        mandate_max_drawdown_realized=-0.10,
        max_single_security_weight_pct=0.30,
        weights={"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25},
        stress_report=stress,
        calibration_limits={},
        enforce_synthetic_vs_mandate_dd=True,
    )
    assert ev2["mandate_classification"] == "borderline"


def test_pick_least_bad_prefers_fewer_failures():
    rows = [
        {"build_status": "OK", "mandate_failures": "a;b", "slack_target_vol": -0.01, "cagr_10y": 0.05},
        {"build_status": "OK", "mandate_failures": "a", "slack_target_vol": -0.05, "cagr_10y": 0.02},
    ]
    best = pick_least_bad_lambda(rows)
    assert best["mandate_failures"] == "a"


def test_factor_rc_limits_enforced_when_yaml_limits_present():
    stress = _stress_rows_all_pass()
    stress["scenario_results"][0]["top1_rc_pct"] = 0.99
    ev = classify_robust_mv_mandate(
        portfolio_valid=True,
        target_vol_annual=None,
        vol_annual_10y=None,
        target_max_drawdown_pct=None,
        mandate_max_drawdown_realized=None,
        max_single_security_weight_pct=None,
        weights={"A": 1.0},
        stress_report=stress,
        calibration_limits={"max_top1_rc_pct": 0.5},
        enforce_synthetic_vs_mandate_dd=False,
    )
    assert ev["mandate_classification"] == "fail"
    assert "max_top1_rc_pct" in ev["mandate_failures"]


def test_no_feasible_lambda_diagnostic_covers_grid_failures_and_guidance():
    winner = {
        "robust_mv_lambda": 2.0,
        "build_status": "OK",
        "mandate_classification": "fail",
        "mandate_failures": "target_vol_annual;mandate_max_drawdown_full_history",
    }
    d = build_no_feasible_lambda_diagnostic(lambda_grid=(0.1, 1.0, 2.0), winner=winner)
    assert d["lambda_range_tested"]["min"] == 0.1
    assert d["lambda_range_tested"]["max"] == 2.0
    assert d["lambda_range_tested"]["n_grid_points"] == 3
    assert d["best_available_lambda"] == 2.0
    assert "target_vol_annual" in d["mandate_constraints_failed_codes"]
    assert "mandate_max_drawdown_full_history" in d["mandate_constraints_failed_codes"]
    assert len(d["possible_causes"]) == 4
    assert len(d["suggested_next_actions"]) == 4
    assert "No λ in the tested grid" in d["narrative"]
    assert "Target volatility limit" in d["narrative"]


def test_no_feasible_lambda_diagnostic_when_build_not_ok():
    winner = {"robust_mv_lambda": 1.0, "build_status": "FAIL_CONFIG", "mandate_failures": None}
    d = build_no_feasible_lambda_diagnostic(lambda_grid=(1.0,), winner=winner)
    assert d["mandate_constraints_failed_codes"] == []
    assert "FAIL_CONFIG" in d["narrative"]


def test_no_feasible_lambda_diagnostic_when_no_winner_row():
    d = build_no_feasible_lambda_diagnostic(lambda_grid=(0.5, 1.5), winner=None)
    assert d["best_available_lambda"] is None
    assert d["lambda_range_tested"]["min"] == 0.5
