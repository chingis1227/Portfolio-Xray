"""Session 5 — Core MVP historical replay contract (cases A–D + Block 3.2 merge)."""
from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from src.core_mvp_historical_stress_replay import (
    CORE_MVP_HISTORICAL_SCENARIO_IDS,
    CORE_MVP_HISTORICAL_STRESS_REPLAY_VERSION,
    REPLAY_STATUS_FULL,
    REPLAY_STATUS_PARTIAL,
    REPLAY_STATUS_UNAVAILABLE,
    USER_NOTE_FULL_REPLAY_EN,
    USER_NOTE_PARTIAL_REPLAY_EN,
    USER_NOTE_UNAVAILABLE_EN,
    attach_core_mvp_historical_stress_replay_v1,
    build_episode_replay,
    build_historical_stress_replay_v1,
)
from src.scenario_library import HISTORICAL_SCENARIO_IDS
from src.stress_results_block import attach_stress_results_v1, build_stress_results_v1

_REPLAY_EPISODE_REQUIRED_KEYS = (
    "scenario_id",
    "scenario_name",
    "episode_start",
    "episode_end",
    "replay_status",
    "direct_coverage_weight_pct",
    "unavailable_weight_pct",
    "unavailable_positions",
    "available_history_assets",
    "portfolio_level_result_available",
    "user_note",
    "diagnosis_summary_en",
    "limitation_summary",
    "portfolio_loss_pct",
    "drawdown_pct",
)

_REPLAY_MERGE_KEYS = _REPLAY_EPISODE_REQUIRED_KEYS

_FORBIDDEN_REPLAY_KEYS = (
    "used_proxies",
    "proxy_coverage_weight_pct",
    "proxy_assisted_replay",
    "approved_etf_proxies",
)


def _dense_monthly(
    columns: dict[str, list[float]],
    *,
    start: str = "2000-03-31",
) -> pd.DataFrame:
    n = max(len(v) for v in columns.values())
    idx = pd.date_range(start, periods=n, freq="ME")
    return pd.DataFrame(columns, index=idx)


def _minimal_historical_evidence(episode: str) -> dict[str, Any]:
    return {
        "episode": episode,
        "pnl_real_episode": None,
        "max_dd": None,
        "data_quality": "insufficient_data",
        "coverage_ratio": 0.1,
        "n_obs": 0,
        "return_method": "realized_portfolio_monthly",
        "proxy_used": False,
    }


def _assert_no_forbidden_proxy_keys(row: dict[str, Any]) -> None:
    for key in _FORBIDDEN_REPLAY_KEYS:
        assert key not in row, f"forbidden key present: {key}"
    for pos in row.get("unavailable_positions") or []:
        if isinstance(pos, dict) and pos.get("reason_en"):
            assert "proxy" not in str(pos["reason_en"]).lower()
    summary = row.get("diagnosis_summary_en")
    if isinstance(summary, str):
        assert "proxy" not in summary.lower()


def _assert_episode_replay_contract(row: dict[str, Any]) -> None:
    for key in _REPLAY_EPISODE_REQUIRED_KEYS:
        assert key in row, f"missing replay field: {key}"
    _assert_no_forbidden_proxy_keys(row)
    assert row["scenario_id"] in CORE_MVP_HISTORICAL_SCENARIO_IDS
    assert row["replay_status"] in {
        REPLAY_STATUS_FULL,
        REPLAY_STATUS_PARTIAL,
        REPLAY_STATUS_UNAVAILABLE,
    }
    direct = float(row["direct_coverage_weight_pct"])
    unavail = float(row["unavailable_weight_pct"])
    assert abs(direct + unavail - 100.0) < 0.05, "coverage weights must sum to 100%"
    assert isinstance(row["user_note"], str) and row["user_note"].strip()
    assert isinstance(row["diagnosis_summary_en"], str) and row["diagnosis_summary_en"].strip()
    avail = row["available_history_assets"]
    assert isinstance(avail, dict)
    assert "positions" in avail
    if row["portfolio_level_result_available"]:
        assert row["replay_status"] == REPLAY_STATUS_FULL
        assert row["unavailable_weight_pct"] == 0.0
        assert row["portfolio_loss_pct"] is not None
        assert row["drawdown_pct"] is not None
        assert row["limitation_summary"] is None
        assert row["user_note"] == USER_NOTE_FULL_REPLAY_EN
    else:
        assert row["portfolio_loss_pct"] is None
        assert row["drawdown_pct"] is None
        if row["replay_status"] == REPLAY_STATUS_PARTIAL:
            assert 0.0 < unavail < 100.0
            assert direct > 0.0
            assert row["user_note"] == USER_NOTE_PARTIAL_REPLAY_EN
            assert row["limitation_summary"]
            assert avail.get("partial_replay_caveat_en")
        elif row["replay_status"] == REPLAY_STATUS_UNAVAILABLE:
            assert row["user_note"] == USER_NOTE_UNAVAILABLE_EN
            assert row["limitation_summary"]


def _case_fixtures() -> list[dict[str, Any]]:
    """Cases A–D from core_mvp_historical_stress_replay_spec acceptance."""
    dotcom_dense = _dense_monthly({"SPY": [0.01] * 8})
    return [
        {
            "case_id": "A",
            "weights": {"SPY": 0.6, "BND": 0.4},
            "monthly": _dense_monthly({"SPY": [0.01] * 8, "BND": [0.002] * 8}),
            "expected_status": REPLAY_STATUS_FULL,
            "episode": "dotcom",
        },
        {
            "case_id": "B",
            "weights": {"SPY": 0.7, "META": 0.3},
            "monthly": dotcom_dense,
            "expected_status": REPLAY_STATUS_PARTIAL,
            "episode": "dotcom",
            "unavailable_tickers": {"META"},
            "available_tickers": {"SPY"},
        },
        {
            "case_id": "C",
            "weights": {"SPY": 0.5, "VOO": 0.5},
            "monthly": dotcom_dense,
            "expected_status": REPLAY_STATUS_PARTIAL,
            "episode": "dotcom",
            "unavailable_tickers": {"VOO"},
            "available_tickers": {"SPY"},
        },
        {
            "case_id": "D",
            "weights": {"VOO": 1.0},
            "monthly": _dense_monthly({"SPY": [0.01] * 8}, start="2020-02-29"),
            "expected_status": REPLAY_STATUS_UNAVAILABLE,
            "episode": "dotcom",
            "unavailable_tickers": {"VOO"},
            "available_tickers": set(),
        },
    ]


@pytest.mark.parametrize("fixture", _case_fixtures(), ids=lambda f: f["case_id"])
def test_case_replay_contract(fixture: dict[str, Any]) -> None:
    row = build_episode_replay(
        fixture["episode"],
        fixture["weights"],
        fixture["monthly"],
    )
    assert row["replay_status"] == fixture["expected_status"]
    _assert_episode_replay_contract(row)
    if fixture.get("unavailable_tickers"):
        unavail = {p["ticker"] for p in row["unavailable_positions"]}
        assert fixture["unavailable_tickers"] <= unavail
    if fixture.get("available_tickers") is not None:
        avail = {p["ticker"] for p in row["available_history_assets"]["positions"]}
        assert avail == fixture["available_tickers"]


def test_historical_stress_replay_v1_top_level_contract() -> None:
    monthly = _dense_monthly({"SPY": [0.01] * 12})
    block = build_historical_stress_replay_v1({"SPY": 1.0}, monthly)
    assert block["version"] == CORE_MVP_HISTORICAL_STRESS_REPLAY_VERSION
    assert block["policy"] == "direct_history_only"
    episodes = block["episodes"]
    assert len(episodes) == len(CORE_MVP_HISTORICAL_SCENARIO_IDS)
    assert [ep["scenario_id"] for ep in episodes] == list(CORE_MVP_HISTORICAL_SCENARIO_IDS)
    for ep in episodes:
        _assert_episode_replay_contract(ep)


@pytest.mark.parametrize("fixture", _case_fixtures(), ids=lambda f: f["case_id"])
def test_block_32_merges_replay_contract(fixture: dict[str, Any]) -> None:
    replay = build_historical_stress_replay_v1(fixture["weights"], fixture["monthly"])
    historical_results = [_minimal_historical_evidence(ep) for ep in HISTORICAL_SCENARIO_IDS]
    out = build_stress_results_v1(
        scenario_results=[],
        historical_results=historical_results,
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
        historical_stress_replay_v1=replay,
    )
    assert [r["episode"] for r in out["historical_episodes"]] == list(HISTORICAL_SCENARIO_IDS)
    row = next(r for r in out["historical_episodes"] if r["episode"] == fixture["episode"])
    assert row["replay_status"] == fixture["expected_status"]
    for key in _REPLAY_MERGE_KEYS:
        assert key in row, f"Block 3.2 missing replay field: {key}"
    _assert_no_forbidden_proxy_keys(row)
    replay_ep = next(
        ep for ep in replay["episodes"] if ep["scenario_id"] == fixture["episode"]
    )
    assert row["direct_coverage_weight_pct"] == replay_ep["direct_coverage_weight_pct"]
    assert row["user_note"] == replay_ep["user_note"]
    if fixture["expected_status"] == REPLAY_STATUS_FULL:
        assert row["availability"] == "available"
        assert row["portfolio_loss_pct"] is not None
        assert isinstance(row["diagnosis_summary_en"], str) and row["diagnosis_summary_en"].strip()
    else:
        assert row["portfolio_loss_pct"] is None
        assert row["drawdown_pct"] is None
        assert row["availability"] == "unavailable"
        assert row["diagnosis_summary_en"] == replay_ep["diagnosis_summary_en"]


def test_attach_core_mvp_then_stress_results_v1() -> None:
    monthly = _dense_monthly({"SPY": [0.01] * 8, "BND": [0.002] * 8})
    weights = {"SPY": 0.6, "BND": 0.4}
    report: dict[str, Any] = {
        "scenario_results": [],
        "historical_results": [_minimal_historical_evidence(ep) for ep in HISTORICAL_SCENARIO_IDS],
        "historical_episode_paths": [],
        "stress_conclusions": {},
        "loss_gate_mode": "diagnostic",
    }
    attach_core_mvp_historical_stress_replay_v1(
        report,
        weights=weights,
        monthly_returns=monthly,
    )
    block = report["historical_stress_replay_v1"]
    assert block["policy"] == "direct_history_only"
    attach_stress_results_v1(report)
    dotcom = next(
        r for r in report["stress_results_v1"]["historical_episodes"] if r["episode"] == "dotcom"
    )
    assert dotcom["replay_status"] == REPLAY_STATUS_FULL
    _assert_episode_replay_contract(
        next(ep for ep in block["episodes"] if ep["scenario_id"] == "dotcom")
    )


def test_partial_case_b_legacy_evidence_does_not_restore_portfolio_metrics() -> None:
    fixture = next(f for f in _case_fixtures() if f["case_id"] == "B")
    replay = build_historical_stress_replay_v1(fixture["weights"], fixture["monthly"])
    historical_results = [
        {
            "episode": "dotcom",
            "pnl_real_episode": -0.25,
            "max_dd": -0.30,
            "data_quality": "ok",
            "coverage_ratio": 1.0,
            "n_obs": 8,
            "return_method": "realized_portfolio_monthly",
            "proxy_used": False,
        },
        *[_minimal_historical_evidence(ep) for ep in HISTORICAL_SCENARIO_IDS[1:]],
    ]
    out = build_stress_results_v1(
        scenario_results=[],
        historical_results=historical_results,
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
        historical_stress_replay_v1=replay,
    )
    dotcom = next(r for r in out["historical_episodes"] if r["episode"] == "dotcom")
    assert dotcom["replay_status"] == REPLAY_STATUS_PARTIAL
    assert dotcom["portfolio_loss_pct"] is None
    assert dotcom["drawdown_pct"] is None
    assert "70.0%" in dotcom["diagnosis_summary_en"]


def test_build_stress_results_v1_without_replay_omits_replay_fields() -> None:
    out = build_stress_results_v1(
        scenario_results=[],
        historical_results=[_minimal_historical_evidence("dotcom")],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
        historical_stress_replay_v1=None,
    )
    row = out["historical_episodes"][0]
    assert "replay_status" not in row
    assert "user_note" not in row
