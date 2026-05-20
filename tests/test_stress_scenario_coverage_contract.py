"""Contract tests for canonical stress scenario coverage (Stress Lab Session 05)."""
from __future__ import annotations

import pandas as pd

from src.scenario_library import (
    HISTORICAL_SCENARIO_IDS,
    SCENARIO_LIBRARY_VERSION,
    SYNTHETIC_SCENARIO_IDS,
    build_scenario_library,
)
from src.stress import HISTORICAL_EPISODES, run_stress
from src.stress_covariance_taxonomy import LAMBDA_BLEND, key_rho_overrides_used_for_scenario


def _long_history_run(**kwargs: object) -> dict:
    idx = pd.date_range("1995-01-31", periods=360, freq="ME")
    monthly_returns = pd.DataFrame(
        {"AAA": [0.008] * len(idx), "BBB": [0.006] * len(idx)},
        index=idx,
    )
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.7, "BBB": 0.3}
    asset_betas = pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"])
    portfolio_betas = {k: 0.05 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")}
    defaults = dict(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.25,
        cash_proxy_ticker="",
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_canonical_synthetic_and_historical_ids_in_stress_report() -> None:
    out = _long_history_run()
    syn_ids = {r["scenario_id"] for r in out["scenario_results"]}
    hist_ids = {r["episode"] for r in out["historical_results"]}
    assert syn_ids == set(SYNTHETIC_SCENARIO_IDS)
    assert hist_ids == set(HISTORICAL_SCENARIO_IDS)
    assert "usd_shock" in syn_ids
    assert "commodity_shock" in syn_ids
    assert "banking_2023" in hist_ids


def test_usd_and_commodity_shock_use_dedicated_taxonomy_calibration() -> None:
    out = _long_history_run()
    by_id = {r["scenario_id"]: r for r in out["scenario_results"]}
    for sid in ("usd_shock", "commodity_shock"):
        row = by_id[sid]
        assert row["stress_cov_method"] == "taxonomy_blend_v1"
        assert row["stress_cov_lambda"] == LAMBDA_BLEND[sid]
        assert row["stress_cov_calibration_version"] is not None
        assert row["vol_mult_by_block"] is not None
        assert key_rho_overrides_used_for_scenario(sid)
    eq_vol = (by_id["equity_shock"].get("vol_mult_by_block") or {}).get("CO")
    usd_vol = (by_id["usd_shock"].get("vol_mult_by_block") or {}).get("CO")
    cmd_vol = (by_id["commodity_shock"].get("vol_mult_by_block") or {}).get("CO")
    assert usd_vol != eq_vol
    assert cmd_vol != eq_vol


def test_banking_2023_historical_path_and_scorecard() -> None:
    out = _long_history_run()
    hist_rows = {r["episode"]: r for r in out["historical_results"]}
    assert "banking_2023" in hist_rows
    banking = hist_rows["banking_2023"]
    assert banking.get("episode_start") == "2023-02-01"
    assert banking.get("episode_end") == "2023-05-31"
    assert "data_quality" in banking
    assert "coverage_ratio" in banking

    paths = {p.get("episode"): p for p in out.get("historical_episode_paths") or []}
    assert "banking_2023" in paths

    scorecard = out["stress_scorecard_v1"]
    sc_syn = {r["scenario_id"] for r in scorecard["synthetic_scenarios"]}
    sc_hist = {r["episode"] for r in scorecard["historical_episodes"]}
    assert sc_syn == set(SYNTHETIC_SCENARIO_IDS)
    assert sc_hist == set(HISTORICAL_SCENARIO_IDS)


def test_scenario_library_includes_expanded_coverage(tmp_path) -> None:
    out = _long_history_run()
    idx = pd.date_range("1995-01-31", periods=360, freq="ME")
    monthly_returns = pd.DataFrame(
        {"AAA": [0.008] * len(idx), "BBB": [0.006] * len(idx)},
        index=idx,
    )
    sl = build_scenario_library(
        out,
        weights={"AAA": 0.7, "BBB": 0.3},
        tickers=["AAA", "BBB"],
        monthly_returns=monthly_returns,
        returns_frequency="monthly",
        output_dir_final=tmp_path,
        output_dir_csv=tmp_path,
    )
    assert sl["version"] == SCENARIO_LIBRARY_VERSION
    lib_ids = {s["scenario_id"] for s in sl["scenarios"]}
    for sid in SYNTHETIC_SCENARIO_IDS:
        assert sid in lib_ids, f"missing synthetic scenario {sid} in scenario_library"
    for ep in HISTORICAL_SCENARIO_IDS:
        assert ep in lib_ids, f"missing historical episode {ep} in scenario_library"


def test_historical_episodes_registry_matches_canonical_ids() -> None:
    registry_ids = {t[0] for t in HISTORICAL_EPISODES}
    assert registry_ids == set(HISTORICAL_SCENARIO_IDS)
    assert "banking_2023" in registry_ids
