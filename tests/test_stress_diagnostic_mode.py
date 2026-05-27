"""Core MVP stress: diagnostic loss_gate_mode without client mandate pass/fail."""
from __future__ import annotations

import pandas as pd

from src.scenario_library import HISTORICAL_SCENARIO_IDS, SYNTHETIC_SCENARIO_IDS
from src.stress import LOSS_GATE_MODE_DIAGNOSTIC, LOSS_GATE_MODE_MANDATE, run_stress

_MANDATE_PRODUCT_KEYS = frozenset({"pass", "loss_ok", "diagnostic_codes", "diagnostic_code"})


def _long_history_run(**kwargs: object) -> dict:
    idx = pd.date_range("1995-01-31", periods=360, freq="ME")
    monthly_returns = pd.DataFrame(
        {"AAA": [0.008] * len(idx), "BBB": [0.006] * len(idx)},
        index=idx,
    )
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.99, "BBB": 0.01}
    asset_betas = pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"])
    portfolio_betas = {k: 0.05 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")}
    defaults = dict(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.05,
        cash_proxy_ticker="",
        loss_gate_mode=LOSS_GATE_MODE_DIAGNOSTIC,
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_diagnostic_mode_skips_mandate_pass_fail() -> None:
    out = _long_history_run()
    assert out["loss_gate_mode"] == LOSS_GATE_MODE_DIAGNOSTIC
    assert out["max_dd_limit"] is None
    assert out["status"] in {"ok", "warning", "insufficient_data"}
    assert out["status"] not in {"DIAG_PASS", "DIAG_ATTENTION", "DIAG_PASS_WITH_WARNING"}
    assert not out.get("fail_reason_code")
    for row in out["scenario_results"]:
        assert row.get("pass") is None
        assert row.get("loss_ok") is None
        assert not row.get("diagnostic_codes")


def test_diagnostic_mode_includes_hedge_gap_analysis_v1_without_mandate_fields() -> None:
    out = _long_history_run()
    block = out.get("hedge_gap_analysis_v1")
    assert isinstance(block, dict)
    assert block.get("version") == "hedge_gap_analysis_v1"
    assert block.get("loss_gate_mode") == LOSS_GATE_MODE_DIAGNOSTIC
    for row in block.get("by_risk_type") or []:
        assert _MANDATE_PRODUCT_KEYS.isdisjoint(row.keys())


def test_mandate_mode_still_applies_loss_gate() -> None:
    idx = pd.date_range("1995-01-31", periods=360, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.008] * len(idx), "BBB": [0.006] * len(idx)}, index=idx)
    out = run_stress(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.99, "BBB": 0.01},
        monthly_returns=monthly_returns,
        asset_betas=pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]),
        portfolio_betas={k: 0.05 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")},
        target_max_drawdown_pct=0.05,
        cash_proxy_ticker="",
        loss_gate_mode=LOSS_GATE_MODE_MANDATE,
    )
    assert out["loss_gate_mode"] == LOSS_GATE_MODE_MANDATE
    assert out["max_dd_limit"] == 0.05
    assert out["status"] in {"DIAG_PASS", "DIAG_PASS_WITH_WARNING", "DIAG_ATTENTION"}
    assert any(row.get("loss_ok") is not None for row in out["scenario_results"])
    block = out.get("hedge_gap_analysis_v1")
    assert isinstance(block, dict)
    assert block.get("version") == "hedge_gap_analysis_v1"
    assert block.get("loss_gate_mode") == LOSS_GATE_MODE_MANDATE
    for row in block.get("by_risk_type") or []:
        assert _MANDATE_PRODUCT_KEYS.isdisjoint(row.keys())


def test_diagnostic_mode_includes_stress_results_v1() -> None:
    out = _long_history_run()
    block = out.get("stress_results_v1")
    assert isinstance(block, dict)
    assert block.get("version") == "stress_results_v1"
    assert block.get("loss_gate_mode") == LOSS_GATE_MODE_DIAGNOSTIC


def test_diagnostic_stress_results_v1_covers_canonical_scenarios() -> None:
    out = _long_history_run()
    block = out["stress_results_v1"]
    syn_ids = [row["scenario_id"] for row in block["synthetic_scenarios"]]
    hist_ids = [row["episode"] for row in block["historical_episodes"]]
    assert syn_ids == list(SYNTHETIC_SCENARIO_IDS)
    assert hist_ids == list(HISTORICAL_SCENARIO_IDS)


def test_diagnostic_stress_results_v1_omits_mandate_fields_on_product_rows() -> None:
    out = _long_history_run()
    block = out["stress_results_v1"]
    for row in block["synthetic_scenarios"] + block["historical_episodes"]:
        assert _MANDATE_PRODUCT_KEYS.isdisjoint(row.keys())
        for sub in ("loss_contribution", "factor_attribution", "risk_contribution"):
            nested = row.get(sub)
            if isinstance(nested, dict):
                assert _MANDATE_PRODUCT_KEYS.isdisjoint(nested.keys())


def test_diagnostic_stress_results_v1_worst_ids_match_stress_conclusions() -> None:
    out = _long_history_run()
    conclusions = out.get("stress_conclusions") or {}
    block = out["stress_results_v1"]
    env = block.get("envelope") or {}
    worst_syn = conclusions.get("worst_synthetic_scenario") or {}
    worst_hist = conclusions.get("worst_historical_episode") or {}
    assert env.get("worst_synthetic", {}).get("scenario_id") == worst_syn.get("scenario_id")
    assert env.get("worst_historical", {}).get("episode") == worst_hist.get("episode")
