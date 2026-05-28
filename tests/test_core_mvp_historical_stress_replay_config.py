"""Session 1 — Core MVP historical replay config and direct coverage rules (no proxies)."""
from __future__ import annotations

import pandas as pd

from src.core_mvp_historical_stress_replay import (
    CORE_MVP_HISTORICAL_SCENARIO_IDS,
    DEFAULT_MIN_COVERAGE_RATIO,
    CoreMvpHistoricalReplayConfig,
    default_core_mvp_replay_config,
    direct_history_coverage_ratio,
    episode_window_for_scenario,
    historical_episode_windows,
    position_has_usable_direct_history,
    replay_status_from_weight_pcts,
)
from src.stress import HISTORICAL_EPISODES


def test_episode_windows_match_stress_registry() -> None:
    windows = historical_episode_windows()
    assert len(windows) == len(HISTORICAL_EPISODES)
    for row, (ep_id, start, end) in zip(windows, HISTORICAL_EPISODES):
        assert row["scenario_id"] == ep_id
        assert row["episode_start"] == start
        assert row["episode_end"] == end
        assert row["scenario_name"]
    assert CORE_MVP_HISTORICAL_SCENARIO_IDS == tuple(ep[0] for ep in HISTORICAL_EPISODES)


def test_default_config_direct_only_no_proxy_fields() -> None:
    cfg = default_core_mvp_replay_config()
    assert cfg.min_coverage_ratio == DEFAULT_MIN_COVERAGE_RATIO
    assert DEFAULT_MIN_COVERAGE_RATIO == 0.45
    fields = set(CoreMvpHistoricalReplayConfig.__dataclass_fields__)
    assert "min_coverage_ratio" in fields
    assert "ticker_proxies" not in fields
    assert "asset_class_proxies" not in fields


def test_position_direct_history_requires_coverage() -> None:
    idx = pd.date_range("2000-03-31", periods=8, freq="ME")
    # 6 of 8 months valid -> 0.75 coverage
    vals = [0.01, 0.02, None, 0.01, 0.01, 0.01, None, 0.01]
    monthly = pd.DataFrame({"SPY": vals}, index=idx)
    assert position_has_usable_direct_history(
        monthly,
        "SPY",
        "2000-03-01",
        "2002-10-31",
    )
    sparse = pd.DataFrame({"SPY": [0.01, None, None, None, None, None, None, None]}, index=idx)
    assert not position_has_usable_direct_history(
        sparse,
        "SPY",
        "2000-03-01",
        "2002-10-31",
    )


def test_missing_column_is_not_usable() -> None:
    monthly = pd.DataFrame({"SPY": [0.01, 0.02]}, index=pd.date_range("2020-02-29", periods=2, freq="ME"))
    assert not position_has_usable_direct_history(monthly, "VOO", "2020-02-01", "2020-04-30")


def test_replay_status_from_weights() -> None:
    assert replay_status_from_weight_pcts(100.0, 0.0) == "full_replay"
    assert replay_status_from_weight_pcts(60.0, 40.0) == "partial_unavailable"
    assert replay_status_from_weight_pcts(0.0, 100.0) == "unavailable"


def test_episode_window_for_scenario() -> None:
    win = episode_window_for_scenario("dotcom")
    assert win == ("2000-03-01", "2002-10-31")
    assert episode_window_for_scenario("not_an_episode") is None


def test_direct_history_coverage_ratio() -> None:
    idx = pd.date_range("2000-03-31", periods=4, freq="ME")
    monthly = pd.DataFrame({"SPY": [0.01, 0.02, None, 0.01]}, index=idx)
    ratio = direct_history_coverage_ratio(monthly, "SPY", "2000-03-01", "2002-10-31")
    assert ratio == 0.75


def test_core_mvp_module_does_not_import_proxy_fallback() -> None:
    import src.core_mvp_historical_stress_replay as mod

    assert "historical_stress_fallback" not in getattr(mod, "__all__", [])
    assert not hasattr(mod, "default_historical_stress_proxy_config")
    assert not hasattr(mod, "build_historical_episode_asset_returns")
