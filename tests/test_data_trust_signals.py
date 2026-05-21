"""Data-quality and young-ETF trust signal disclosure (RM-1016)."""
from __future__ import annotations

import pandas as pd

from src.data_trust_signals import (
    INPUT_DATA_TRUST_SIGNALS_VERSION,
    STRESS_DATA_TRUST_SUMMARY_VERSION,
    build_input_data_trust_signals,
    build_stress_data_trust_summary,
    build_xray_data_trust_signals,
)
from src.input_assumptions import build_input_assumptions_from_analysis_setup
from src.stress import run_stress


def _minimal_run(**kwargs: object) -> dict:
    idx = pd.date_range("2015-01-31", periods=120, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.005] * len(idx)}, index=idx)
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.6, "BBB": 0.4}
    asset_betas = pd.DataFrame(
        index=tickers,
        columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"],
        dtype=float,
    ).fillna(0.0)
    portfolio_betas = {k: 0.0 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")}
    defaults = dict(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.2,
        cash_proxy_ticker="",
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_stress_report_includes_data_trust_summary() -> None:
    out = _minimal_run()
    trust = out.get("data_trust_summary")
    assert isinstance(trust, dict)
    assert trust.get("version") == STRESS_DATA_TRUST_SUMMARY_VERSION
    assert trust.get("user_summary_lines")
    assert "historical_episode_quality_counts" in trust
    conclusions = out.get("stress_conclusions") or {}
    assert conclusions.get("data_quality_warnings")


def test_short_history_episodes_surface_in_trust_summary() -> None:
    idx = pd.date_range("2023-01-31", periods=24, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.005] * len(idx)}, index=idx)
    out = _minimal_run(monthly_returns=monthly_returns)
    trust = out["data_trust_summary"]
    assert int(trust.get("n_historical_episodes_flagged") or 0) >= 1
    assert trust.get("overall_trust") in {"low", "medium", "high"}
    flagged = [
        row
        for row in trust.get("episode_flags") or []
        if row.get("data_quality") not in {"reliable", "usable_with_gaps"}
    ]
    assert flagged
    assert any("insufficient" in str(row.get("plain_english") or "").lower() for row in flagged)


def test_input_assumptions_exports_data_trust_signals() -> None:
    setup = {
        "version": "analysis_setup_v1",
        "portfolio_input": {"tickers": ["VOO"], "investor_currency": "USD"},
        "analysis_subject": {"type": "current_portfolio", "tickers": ["VOO"]},
        "analysis_portfolio": {"weight_status": {"status": "fully_invested"}},
        "resolved_assumptions": {
            "young_etf_optimization_policy": {"enabled": True, "min_history_months": 36},
        },
        "validation_result": {
            "status": "valid",
            "action_required_warnings": [],
            "legacy_current_repo_conflicts": [{"code": "UNKNOWN_TICKER_POLICY"}],
        },
    }
    exported = build_input_assumptions_from_analysis_setup(setup)
    trust = exported.get("data_trust_signals")
    assert trust.get("version") == INPUT_DATA_TRUST_SIGNALS_VERSION
    assert trust.get("young_etf_policy_enabled") is True
    assert any("Young ETF" in line for line in trust.get("user_summary_lines") or [])
    assert any(
        "taxonomy" in str(sig.get("category") or "").lower()
        for sig in trust.get("signals") or []
    )


def test_xray_data_trust_signals_merge_section_and_stress_warnings() -> None:
    xray = {
        "version": "portfolio_xray_v2",
        "sections": {
            "asset_allocation": {
                "warnings": ["12.0% of portfolio weight has unknown taxonomy"],
            },
            "weakness_map": {"warnings": ["stress scenario rows are missing"]},
        },
    }
    stress_trust = build_stress_data_trust_summary(
        historical_results=[
            {
                "episode": "2008",
                "data_quality": "insufficient_data",
                "n_obs": 0,
                "coverage_ratio": 0.0,
            }
        ],
        stress_conclusions={
            "data_quality_warnings": ["2008: insufficient_data (return_method=realized_portfolio_monthly)"],
            "overall_confidence": "low",
        },
    )
    trust = build_xray_data_trust_signals(xray, stress_data_trust_summary=stress_trust)
    lines = trust.get("user_summary_lines") or []
    assert any("taxonomy" in line.lower() for line in lines)
    assert any("Stress data trust" in line for line in lines)
    assert trust.get("overall_trust") == "low"
