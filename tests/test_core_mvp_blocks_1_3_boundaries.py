from __future__ import annotations

from typing import Any

import pandas as pd

import portfolio_xray_golden_inputs as golden_inputs
from scripts.core_mvp_validation_contract import assert_block_2_4_product_contract
from src.analysis_setup import build_analysis_setup
from src.config import resolve_cash_and_rf
from src.config_schema import validate_config
from src.current_portfolio_stress_scorecard_block import BLOCK_3_4_VERSION
from src.input_assumptions import build_input_assumptions_from_analysis_setup
from src.real_cash import collect_real_cash_tickers, partition_market_data_tickers
from src.stress import LOSS_GATE_MODE_DIAGNOSTIC, LOSS_GATE_MODE_MANDATE, run_stress


CORE_MVP_INPUT_GROUPS = ["tickers", "allocation", "investor_currency"]

BLOCK_2_PRODUCT_KEYS = [
    "block_2_1_asset_allocation",
    "block_2_2_portfolio_metrics",
    "block_2_3_factor_exposure",
    "block_2_4_hidden_exposure",
    "block_2_5_risk_budget_view",
    "block_2_6_portfolio_weakness_map",
]

CORE_MVP_FORBIDDEN_KEYS = {
    "client_profile",
    "target_nominal_return_annual",
    "target_return",
    "target_vol_annual",
    "target_volatility",
    "target_max_drawdown_pct",
    "max_dd_limit",
    "liquidity_need",
    "liquidity_need_months",
    "monthly_expenses",
    "portfolio_value",
    "horizon_years",
    "mandate",
    "mandate_gate",
    "suitability",
    "pass",
    "loss_ok",
    "diagnostic_code",
    "diagnostic_codes",
    "fail_reason_code",
    "failed_scenario",
    "failed_test",
}


def _find_forbidden_keys(obj: Any, forbidden: set[str] = CORE_MVP_FORBIDDEN_KEYS) -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key) in forbidden:
                found.append(str(key))
            found.extend(_find_forbidden_keys(value, forbidden))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_find_forbidden_keys(item, forbidden))
    return found


def _diagnostic_stress_run() -> dict[str, Any]:
    idx = pd.date_range("2015-01-31", periods=120, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)}, index=idx)
    factor_cols = ["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]
    return run_stress(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.8, "BBB": 0.2},
        monthly_returns=monthly_returns,
        asset_betas=pd.DataFrame(columns=factor_cols),
        portfolio_betas={key: 0.0 for key in factor_cols},
        target_max_drawdown_pct=0.05,
        cash_proxy_ticker="",
        hedge_assets=["AAA"],
        loss_gate_mode=LOSS_GATE_MODE_DIAGNOSTIC,
    )


def test_block_1_core_mvp_contract_is_minimal_and_real_cash_safe() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND", "Cash USD"],
            "current_weights": {"VOO": 0.45, "BND": 0.45, "Cash USD": 0.10},
        }
    )
    cash_proxy, rf_source = resolve_cash_and_rf(cfg)
    setup = build_analysis_setup(cfg, cash_proxy_ticker=cash_proxy, rf_source=rf_source)
    assumptions = build_input_assumptions_from_analysis_setup(setup)

    assert setup["core_mvp_input_surface"]["required_user_input_groups"] == CORE_MVP_INPUT_GROUPS
    assert setup["core_mvp_input_surface"]["core_mvp_requirements_met"] is True
    assert set(setup["core_mvp_input_surface"]["fields"]) == {
        "tickers",
        "allocation",
        "investor_currency",
    }
    assert assumptions["core_mvp_input_contract"]["required_user_input_groups"] == CORE_MVP_INPUT_GROUPS
    assert assumptions["core_mvp_input_contract"]["product_surface"] is True
    assert assumptions["mandate_and_constraints"]["_scope"]["product_surface"] is False
    assert collect_real_cash_tickers(tickers=cfg.tickers, weights=cfg.weights) == ["Cash USD"]
    download, real_cash = partition_market_data_tickers(list(cfg.tickers))
    assert "Cash USD" in real_cash
    assert "Cash USD" not in download


def test_block_2_product_blocks_are_clean_consumer_surface() -> None:
    xray = golden_inputs.build_golden_document()

    assert set(BLOCK_2_PRODUCT_KEYS) <= set(xray)
    for key in BLOCK_2_PRODUCT_KEYS:
        found = sorted(set(_find_forbidden_keys(xray[key])))
        assert not found, f"{key} contains forbidden Core MVP contamination keys: {found}"

    assert_block_2_4_product_contract(xray["block_2_4_hidden_exposure"])

    legacy = xray.get("legacy_summary") or {}
    assert legacy.get("_scope", {}).get("product_surface") is False
    assert "mandate_gate" not in (legacy.get("portfolio_diagnostic_verdict") or {})


def test_block_3_diagnostic_mode_has_clean_raw_and_product_outputs() -> None:
    stress = _diagnostic_stress_run()
    assert stress["loss_gate_mode"] == LOSS_GATE_MODE_DIAGNOSTIC
    assert stress["max_dd_limit"] is None

    for row in (stress.get("scenario_results") or []) + (stress.get("historical_results") or []):
        found = sorted(set(_find_forbidden_keys(row)))
        assert not found, f"Diagnostic raw stress row contains forbidden keys: {found}"

    for key in ("stress_results_v1", "hedge_gap_analysis_v1", BLOCK_3_4_VERSION):
        block = stress[key]
        found = sorted(set(_find_forbidden_keys(block)))
        assert not found, f"{key} contains forbidden Core MVP contamination keys: {found}"


def test_legacy_mandate_stress_mode_remains_explicitly_gated() -> None:
    stress = _diagnostic_stress_run()
    mandate = run_stress(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.8, "BBB": 0.2},
        monthly_returns=pd.DataFrame(
            {"AAA": [0.01] * 120, "BBB": [0.01] * 120},
            index=pd.date_range("2015-01-31", periods=120, freq="ME"),
        ),
        asset_betas=pd.DataFrame(
            columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]
        ),
        portfolio_betas={key: 0.0 for key in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")},
        target_max_drawdown_pct=0.05,
        cash_proxy_ticker="",
        hedge_assets=["AAA"],
        loss_gate_mode=LOSS_GATE_MODE_MANDATE,
    )

    assert stress["loss_gate_mode"] == LOSS_GATE_MODE_DIAGNOSTIC
    assert mandate["loss_gate_mode"] == LOSS_GATE_MODE_MANDATE
    assert any("loss_ok" in row and "pass" in row for row in mandate["scenario_results"])
    assert all("loss_ok" not in row and "pass" not in row for row in stress["scenario_results"])
