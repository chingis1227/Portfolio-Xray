"""Contract tests for synthetic fallback/proxy assumption exposure (Stress Lab Session 06)."""
from __future__ import annotations

import pandas as pd

from src.scenario_library import build_scenario_library
from src.scenario_library_normalized import build_scenario_library_normalized
from src.snapshot import _stress_suite_results_for_snapshot
from src.stress import run_stress


def _run_with_missing_asset_betas() -> tuple[dict, pd.DataFrame]:
    idx = pd.date_range("1995-01-31", periods=360, freq="ME")
    monthly_returns = pd.DataFrame(
        {"AAA": [0.01] * len(idx), "BBB": [0.005] * len(idx)},
        index=idx,
    )
    out = run_stress(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.7, "BBB": 0.3},
        monthly_returns=monthly_returns,
        # Empty betas force synthetic fallback/proxy assumptions for all tickers.
        asset_betas=pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]),
        portfolio_betas={
            "beta_eq": 0.1,
            "beta_rr": 0.0,
            "beta_inf": 0.0,
            "beta_credit": 0.0,
            "beta_usd": 0.0,
            "beta_cmd": 0.0,
        },
        target_max_drawdown_pct=0.25,
        cash_proxy_ticker="",
    )
    return out, monthly_returns


def test_synthetic_rows_expose_assumption_block() -> None:
    out, _ = _run_with_missing_asset_betas()
    rows = out.get("scenario_results") or []
    assert rows
    row = rows[0]
    assumptions = row.get("synthetic_assumptions")
    assert isinstance(assumptions, dict)
    for key in (
        "version",
        "beta_source",
        "beta_coverage_ratio",
        "beta_confidence",
        "fallback_used",
        "fallback_asset_count",
        "beta_fallback_assets",
        "proxy_method_for_missing_betas",
        "proxy_applied_to_assets",
    ):
        assert key in assumptions
    assert assumptions["version"] == "synthetic_assumptions_v1"
    assert assumptions["fallback_used"] is True
    assert set(assumptions["beta_fallback_assets"]) == {"AAA", "BBB"}
    assert assumptions["proxy_method_for_missing_betas"] == "equity_shock_proxy"


def test_scenario_library_and_normalized_keep_assumptions(tmp_path) -> None:
    out, monthly_returns = _run_with_missing_asset_betas()
    sl = build_scenario_library(
        out,
        weights={"AAA": 0.7, "BBB": 0.3},
        tickers=["AAA", "BBB"],
        monthly_returns=monthly_returns,
        returns_frequency="monthly",
        output_dir_final=tmp_path,
        output_dir_csv=tmp_path,
    )
    syn = next(s for s in sl["scenarios"] if s.get("scenario_type") == "synthetic_stress")
    assert "synthetic_assumptions" in syn
    assert syn["synthetic_assumptions"]["version"] == "synthetic_assumptions_v1"

    sln = build_scenario_library_normalized(
        sl,
        output_dir_final=tmp_path,
        output_dir_csv=tmp_path,
        monthly_returns=monthly_returns,
        weights={"AAA": 0.7, "BBB": 0.3},
        tickers=["AAA", "BBB"],
        returns_frequency_pipeline="monthly",
        stress_report=out,
    )
    syn_n = next(s for s in sln["scenarios"] if s.get("scenario_type") == "synthetic_stress")
    assert "synthetic_assumptions" in syn_n
    assert syn_n["synthetic_assumptions"]["version"] == "synthetic_assumptions_v1"


def test_snapshot_stress_suite_includes_synthetic_assumptions() -> None:
    out, _ = _run_with_missing_asset_betas()
    section = _stress_suite_results_for_snapshot(out, portfolio_params={})
    scenarios = section.get("scenarios") or []
    assert scenarios
    first = scenarios[0]
    assert "synthetic_assumptions" in first
    assert first["synthetic_assumptions"].get("version") == "synthetic_assumptions_v1"
    assert "historical_methodology" in section
    assert "crisis_replay_summary" in section
    assert "hedge_gap_analysis" in section
