"""Historical stress fields, data quality, methodology disclosure, and crisis replay paths."""
from __future__ import annotations

import pandas as pd

from src.stress import (
    CRISIS_REPLAY_VERSION,
    HISTORICAL_EPISODES,
    HISTORICAL_METHODOLOGY_VERSION,
    HISTORICAL_PRIMARY_RETURN_METHOD,
    run_stress,
)
from src.metrics_asset import time_to_recovery

_PATH_ROW_KEYS = {"date", "portfolio_return", "equity", "drawdown"}


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


def test_historical_results_include_episode_bounds_and_pnl() -> None:
    out = _minimal_run()
    hist = out.get("historical_results") or []
    assert hist, "historical_results should not be empty"
    assert len(hist) == len(HISTORICAL_EPISODES)
    for h in hist:
        assert "episode_start" in h
        assert "episode_end" in h
        assert "pnl_real_episode" in h
        assert "n_obs" in h
        assert "n_expected_obs" in h
        assert "coverage_ratio" in h
        assert "data_quality" in h
        assert h["return_method"] == HISTORICAL_PRIMARY_RETURN_METHOD
        assert h["proxy_used"] is False

    methodology = out.get("historical_methodology") or {}
    assert methodology["version"] == HISTORICAL_METHODOLOGY_VERSION
    assert methodology["primary_stress_path"] == "realized_only"
    assert methodology["return_method"] == HISTORICAL_PRIMARY_RETURN_METHOD
    assert methodology["proxy_used_in_primary_stress"] is False
    assert methodology["proxy_location"] == "scenario_library_normalized"

    paths = out.get("historical_episode_paths") or []
    assert isinstance(paths, list)


def test_stress_data_trust_summary_promotes_episode_quality() -> None:
    idx = pd.date_range("2023-01-31", periods=24, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.005] * len(idx)}, index=idx)
    out = _minimal_run(monthly_returns=monthly_returns)
    trust = out.get("data_trust_summary") or {}
    assert trust.get("version") == "stress_data_trust_summary_v1"
    assert trust.get("user_summary_lines")
    promoted = trust.get("promoted_warnings") or []
    assert any(row.get("kind") == "methodology_boundary" for row in promoted)


def test_historical_methodology_warnings_in_conclusions() -> None:
    out = _minimal_run()
    warnings = out["stress_conclusions"]["data_quality_warnings"]
    assert warnings
    assert any("realized_portfolio_monthly" in w for w in warnings)
    assert any("scenario_library_normalized" in w for w in warnings)

    idx = pd.date_range("2023-01-31", periods=24, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.005] * len(idx)}, index=idx)
    short = _minimal_run(monthly_returns=monthly_returns)
    short_warnings = short["stress_conclusions"]["data_quality_warnings"]
    episode_lines = [w for w in short_warnings if not w.startswith("primary_historical_stress:")]
    assert episode_lines
    assert all("return_method=" in w for w in episode_lines)


def test_historical_episode_paths_max_dd_matches_aggregate() -> None:
    idx = pd.date_range("2018-01-31", "2024-12-31", freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.005] * len(idx)}, index=idx)
    for dt in idx:
        ts = pd.Timestamp(dt)
        if pd.Timestamp("2020-02-01") <= ts <= pd.Timestamp("2020-04-30"):
            monthly_returns.loc[dt, "AAA"] = -0.08
            monthly_returns.loc[dt, "BBB"] = -0.06

    out = _minimal_run(monthly_returns=monthly_returns)
    hist_by = {str(h["episode"]): h for h in out["historical_results"]}
    paths_by = {str(p["episode"]): p for p in out["historical_episode_paths"]}

    assert "2020" in paths_by, "2020 episode should emit a replay path when data is sufficient"
    path = paths_by["2020"]
    hist = hist_by["2020"]
    assert hist["max_dd"] is not None
    path_min_dd = min(float(row["drawdown"]) for row in path["rows"])
    assert abs(path_min_dd - float(hist["max_dd"])) <= 1e-4


def test_historical_episode_paths_row_count_and_structure() -> None:
    out = _minimal_run()
    hist_by = {str(h["episode"]): h for h in out["historical_results"]}

    for path in out["historical_episode_paths"]:
        ep = str(path["episode"])
        hist = hist_by[ep]
        rows = path["rows"]
        assert len(rows) == path["n_obs"] == hist["n_obs"]
        assert path["n_expected_obs"] == hist["n_expected_obs"]
        assert path["coverage_ratio"] == hist["coverage_ratio"]
        assert path["data_quality"] == hist["data_quality"]
        assert path["episode_start"] == hist["episode_start"]
        assert path["episode_end"] == hist["episode_end"]
        for row in rows:
            assert set(row) == _PATH_ROW_KEYS
            assert isinstance(row["date"], str)
            assert row["date"]


def test_insufficient_episodes_emit_quality_without_replay_path() -> None:
    idx = pd.date_range("2023-01-31", periods=24, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.005] * len(idx)}, index=idx)
    out = _minimal_run(monthly_returns=monthly_returns)

    hist_by = {str(h["episode"]): h for h in out["historical_results"]}
    paths_by = {str(p["episode"]): p for p in out["historical_episode_paths"]}

    for ep_id, _, _ in HISTORICAL_EPISODES:
        hist = hist_by[ep_id]
        assert hist["data_quality"] in {
            "insufficient_data",
            "low_confidence",
            "usable_with_gaps",
            "reliable",
        }
        if hist["n_obs"] < 2 or hist["max_dd"] is None:
            assert ep_id not in paths_by
        else:
            assert ep_id in paths_by


def test_historical_episode_paths_v2_recovery_and_asset_contrib() -> None:
    idx = pd.date_range("2018-01-31", "2024-12-31", freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.005] * len(idx)}, index=idx)
    for dt in idx:
        ts = pd.Timestamp(dt)
        if pd.Timestamp("2020-02-01") <= ts <= pd.Timestamp("2020-04-30"):
            monthly_returns.loc[dt, "AAA"] = -0.08
            monthly_returns.loc[dt, "BBB"] = -0.06

    out = _minimal_run(monthly_returns=monthly_returns)
    path = next(p for p in out["historical_episode_paths"] if p["episode"] == "2020")
    assert path["replay_version"] == CRISIS_REPLAY_VERSION
    assert "time_to_recovery_months" in path
    assert "recovered" in path
    assert isinstance(path["recovered"], bool)

    port_ret = pd.Series(
        [row["portfolio_return"] for row in path["rows"]],
        index=pd.to_datetime([row["date"] for row in path["rows"]]),
    )
    ttr, recovered = time_to_recovery(port_ret)
    assert path["recovered"] == recovered
    if ttr is None:
        assert path["time_to_recovery_months"] is None
    else:
        assert path["time_to_recovery_months"] == round(float(ttr), 3)

    contrib = path["asset_pnl_contrib_episode"]
    assert set(contrib) == {"AAA", "BBB"}
    row_sum = sum(float(r["portfolio_return"]) for r in path["rows"])
    assert abs(sum(contrib.values()) - row_sum) <= 1e-4
    assert path["top_loss_assets_episode"][0] == "AAA"


def test_crisis_replay_csv_rows_mirror_path_block(tmp_path) -> None:
    out = _minimal_run()
    export_dir = tmp_path / "results_csv"
    export_dir.mkdir()

    for item in out["historical_episode_paths"]:
        episode = str(item["episode"])
        rows = item["rows"]
        pd.DataFrame(rows).to_csv(export_dir / f"crisis_replay_{episode}.csv", index=False)

    for item in out["historical_episode_paths"]:
        episode = str(item["episode"])
        csv_path = export_dir / f"crisis_replay_{episode}.csv"
        assert csv_path.exists()
        df = pd.read_csv(csv_path)
        assert len(df) == item["n_obs"]
        assert set(df.columns) == _PATH_ROW_KEYS


def test_crisis_replay_asset_contrib_csv_export(tmp_path) -> None:
    out = _minimal_run()
    export_dir = tmp_path / "results_csv"
    export_dir.mkdir()

    for item in out["historical_episode_paths"]:
        episode = str(item["episode"])
        contrib = item.get("asset_pnl_contrib_episode") or {}
        if not contrib:
            continue
        rows = [
            {"ticker": ticker, "episode_pnl_contrib": value}
            for ticker, value in sorted(contrib.items())
        ]
        pd.DataFrame(rows).to_csv(export_dir / f"crisis_replay_{episode}_asset_contrib.csv", index=False)

    for item in out["historical_episode_paths"]:
        episode = str(item["episode"])
        csv_path = export_dir / f"crisis_replay_{episode}_asset_contrib.csv"
        assert csv_path.exists()
        df = pd.read_csv(csv_path)
        assert set(df.columns) == {"ticker", "episode_pnl_contrib"}
        assert len(df) == len(item["asset_pnl_contrib_episode"])
