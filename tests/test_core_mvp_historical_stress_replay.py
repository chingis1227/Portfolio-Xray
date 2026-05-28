"""Session 2 — Core MVP historical replay engine (direct history only)."""
from __future__ import annotations

import pandas as pd

from src.core_mvp_historical_stress_replay import (
    REPLAY_STATUS_FULL,
    REPLAY_STATUS_PARTIAL,
    REPLAY_STATUS_UNAVAILABLE,
    USER_NOTE_FULL_REPLAY_EN,
    USER_NOTE_PARTIAL_REPLAY_EN,
    USER_NOTE_UNAVAILABLE_EN,
    build_episode_replay,
    build_historical_stress_replay_v1,
)


def _monthly_panel(columns: dict[str, list[float | None]], start: str = "2000-03-31") -> pd.DataFrame:
    n = max(len(v) for v in columns.values())
    idx = pd.date_range(start, periods=n, freq="ME")
    return pd.DataFrame(columns, index=idx)


def _dense_returns(ticker: str, n: int, r: float = 0.01, start: str = "2000-03-31") -> pd.DataFrame:
    return pd.DataFrame({ticker: [r] * n}, index=pd.date_range(start, periods=n, freq="ME"))


# Case A — full direct history
def test_case_a_full_direct_replay() -> None:
    monthly = _dense_returns("SPY", 8, start="2000-03-31")
    monthly["BND"] = [0.002] * 8
    weights = {"SPY": 0.6, "BND": 0.4}
    row = build_episode_replay("dotcom", weights, monthly)
    assert row["replay_status"] == REPLAY_STATUS_FULL
    assert row["portfolio_level_result_available"] is True
    assert row["unavailable_weight_pct"] == 0.0
    assert row["direct_coverage_weight_pct"] == 100.0
    assert row["portfolio_loss_pct"] is not None
    assert row["drawdown_pct"] is not None
    assert row["limitation_summary"] is None
    assert row["available_history_assets"]["partial_replay_caveat_en"] is None
    assert "used_proxies" not in row
    assert "proxy_coverage_weight_pct" not in row


# Case B — individual stock missing (no proxy)
def test_case_b_stock_missing_no_proxy() -> None:
    monthly = _dense_returns("SPY", 8, start="2000-03-31")
    weights = {"SPY": 0.7, "META": 0.3}
    row = build_episode_replay("dotcom", weights, monthly)
    assert row["replay_status"] == REPLAY_STATUS_PARTIAL
    assert row["portfolio_level_result_available"] is False
    assert row["portfolio_loss_pct"] is None
    assert row["drawdown_pct"] is None
    tickers = {p["ticker"] for p in row["unavailable_positions"]}
    assert "META" in tickers
    assert row["unavailable_weight_pct"] == 30.0
    assert len(row["available_history_assets"]["positions"]) == 1
    assert row["available_history_assets"]["positions"][0]["ticker"] == "SPY"


# Case C — mixed: direct + unavailable ETF column missing
def test_case_c_mixed_partial_unavailable() -> None:
    monthly = _dense_returns("SPY", 8, start="2000-03-31")
    weights = {"SPY": 0.5, "VOO": 0.5}
    row = build_episode_replay("dotcom", weights, monthly)
    assert row["replay_status"] == REPLAY_STATUS_PARTIAL
    assert row["unavailable_weight_pct"] > 0.0
    assert row["direct_coverage_weight_pct"] > 0.0
    assert row["portfolio_level_result_available"] is False
    assert row["available_history_assets"]["partial_replay_caveat_en"]
    assert row["user_note"]


# Case D — ETF with no direct history (not replaced by proxy)
def test_case_d_etf_no_history_unavailable_not_proxied() -> None:
    monthly = _dense_returns("SPY", 8, start="2020-02-29")
    weights = {"VOO": 1.0}
    row = build_episode_replay("dotcom", weights, monthly)
    assert row["replay_status"] == REPLAY_STATUS_UNAVAILABLE
    assert row["portfolio_level_result_available"] is False
    assert row["unavailable_positions"]
    assert row["unavailable_positions"][0]["ticker"] == "VOO"
    assert "proxy" not in row["unavailable_positions"][0]["reason_en"].lower()
    assert row["portfolio_loss_pct"] is None


def test_build_historical_stress_replay_v1_all_episodes() -> None:
    monthly = _dense_returns("SPY", 12, start="2000-03-31")
    block = build_historical_stress_replay_v1({"SPY": 1.0}, monthly)
    assert block["version"] == "core_mvp_historical_stress_replay_v1"
    assert block["policy"] == "direct_history_only"
    assert len(block["episodes"]) == 5
    for ep in block["episodes"]:
        assert "replay_status" in ep
        assert "used_proxies" not in ep


def test_cash_proxy_excluded_from_risk_weight() -> None:
    monthly = _dense_returns("SPY", 8, start="2000-03-31")
    weights = {"SPY": 0.9, "BIL": 0.1}
    row = build_episode_replay("dotcom", weights, monthly, cash_proxy_ticker="BIL")
    assert row["replay_status"] == REPLAY_STATUS_FULL
    assert row["direct_coverage_weight_pct"] == 100.0


def test_user_note_full_replay_matches_spec() -> None:
    monthly = _dense_returns("SPY", 8, start="2000-03-31")
    row = build_episode_replay("dotcom", {"SPY": 1.0}, monthly)
    assert row["user_note"] == USER_NOTE_FULL_REPLAY_EN


def test_user_note_partial_matches_spec() -> None:
    monthly = _dense_returns("SPY", 8, start="2000-03-31")
    row = build_episode_replay("dotcom", {"SPY": 0.7, "META": 0.3}, monthly)
    assert row["user_note"] == USER_NOTE_PARTIAL_REPLAY_EN


def test_diagnosis_summary_en_full_includes_metrics() -> None:
    monthly = _dense_returns("SPY", 8, start="2000-03-31")
    monthly["BND"] = [0.002] * 8
    row = build_episode_replay("dotcom", {"SPY": 0.6, "BND": 0.4}, monthly)
    summary = row["diagnosis_summary_en"]
    assert summary
    assert "dot-com bust" in summary.lower()
    assert "100%" in summary
    assert "return was" in summary.lower()
    assert "drawdown" in summary.lower()
    assert "proxy" not in summary.lower()


def test_diagnosis_summary_en_partial_mentions_coverage_and_tickers() -> None:
    monthly = _dense_returns("SPY", 8, start="2000-03-31")
    row = build_episode_replay("dotcom", {"SPY": 0.7, "META": 0.3}, monthly)
    summary = row["diagnosis_summary_en"]
    assert summary
    assert "70.0%" in summary
    assert "30.0%" in summary
    assert USER_NOTE_PARTIAL_REPLAY_EN in summary
    assert "META" in summary
    assert "SPY" in summary
    assert "not a full replay" in summary.lower()


def test_diagnosis_summary_en_unavailable_no_proxy_language() -> None:
    monthly = _dense_returns("SPY", 8, start="2020-02-29")
    row = build_episode_replay("dotcom", {"VOO": 1.0}, monthly)
    summary = row["diagnosis_summary_en"]
    assert summary
    assert USER_NOTE_UNAVAILABLE_EN in summary
    assert "VOO" in summary
    assert "proxy" not in summary.lower()
