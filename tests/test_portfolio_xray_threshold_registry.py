"""Portfolio X-Ray threshold registry drift tests (RM-942 / post-audit Session 02).

Canonical numeric values are owned by docs/specs/portfolio_xray_diagnostics_spec.md §8.
Runtime source: src/portfolio_xray.py::XRAY_THRESHOLDS.
"""
from __future__ import annotations

from src.portfolio_xray import XRAY_THRESHOLDS, build_portfolio_xray_v2

# Locked to portfolio_xray_diagnostics_spec.md §8 — update spec and this dict together.
CANONICAL_XRAY_THRESHOLDS: dict[str, float] = {
    "equity_beta_moderate_abs": 0.35,
    "equity_beta_high_abs": 0.65,
    "factor_beta_moderate_abs": 0.25,
    "factor_beta_high_abs": 0.50,
    "top1_rc_moderate": 0.25,
    "top1_rc_high": 0.35,
    "top3_rc_high": 0.60,
    "pca_pc1_moderate": 0.40,
    "pca_pc1_high": 0.60,
    "stress_top1_rc_moderate": 0.25,
    "stress_top1_rc_high": 0.35,
    "factor_residual_moderate": 0.50,
    "factor_residual_high": 0.65,
    "duration_weight_high": 0.30,
    "credit_weight_high": 0.25,
    "liquidity_risk_weight_high": 0.20,
    "weak_hedge_oos_mae_moderate": 0.05,
    "weak_hedge_oos_mae_high": 0.10,
    "macro_dominant_variance_share_moderate": 0.35,
    "macro_dominant_variance_share_high": 0.50,
    "archetype_equity_weight_high": 0.55,
    "archetype_fixed_income_weight_high": 0.45,
    "archetype_balanced_equity_min": 0.30,
    "archetype_balanced_equity_max": 0.70,
    "archetype_balanced_fixed_income_min": 0.20,
    "archetype_cash_weight_high": 0.35,
    "archetype_defensive_equity_max": 0.30,
    "archetype_concentrated_rc_min": 0.35,
    "stress_loss_moderate": -0.06,
    "stress_loss_high": -0.12,
    "max_drawdown_moderate": -0.10,
    "max_drawdown_high": -0.20,
    "es_95_moderate": -0.015,
    "es_95_high": -0.025,
}


def test_xray_threshold_registry_matches_canonical_values() -> None:
    assert XRAY_THRESHOLDS == CANONICAL_XRAY_THRESHOLDS


def test_xray_threshold_registry_key_set_is_stable() -> None:
    assert set(XRAY_THRESHOLDS) == set(CANONICAL_XRAY_THRESHOLDS)


def test_xray_threshold_registry_values_are_finite_floats() -> None:
    for key, value in XRAY_THRESHOLDS.items():
        assert isinstance(value, float), key
        assert value == value, key  # not NaN


def test_portfolio_xray_json_exports_full_threshold_registry() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup={"analysis_portfolio": {"portfolio_role": "test"}},
        weights={"SPY": 1.0},
        rc_asset=[],
        stress_report={},
        portfolio_valid=True,
    )
    assert xray["thresholds"] == CANONICAL_XRAY_THRESHOLDS
