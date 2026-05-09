from __future__ import annotations

from src.robust_mv_calibration import (
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
