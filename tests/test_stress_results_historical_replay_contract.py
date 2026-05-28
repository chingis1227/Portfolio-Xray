"""Session 3 — stress_results_v1 merges Core MVP historical_stress_replay_v1."""
from __future__ import annotations

import pandas as pd

from src.core_mvp_historical_stress_replay import build_historical_stress_replay_v1
from src.stress_results_block import attach_stress_results_v1, build_stress_results_v1

_REPLAY_FIELD_KEYS = (
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
    "limitation_summary",
)


def _dense_monthly(ticker: str, n: int, r: float = 0.01, start: str = "2000-03-31") -> pd.DataFrame:
    return pd.DataFrame({ticker: [r] * n}, index=pd.date_range(start, periods=n, freq="ME"))


def _minimal_historical_evidence(episode: str) -> dict:
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


def test_stress_results_v1_merges_replay_fields_on_dotcom() -> None:
    monthly = _dense_monthly("SPY", 8)
    monthly["VOO"] = [0.01] * 8
    weights = {"SPY": 0.5, "VOO": 0.5}
    replay = build_historical_stress_replay_v1(weights, monthly)
    historical_results = [
        _minimal_historical_evidence(ep)
        for ep in ("dotcom", "2008", "2020", "2022", "banking_2023")
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
    for key in _REPLAY_FIELD_KEYS:
        assert key in dotcom, f"missing {key}"
    assert "used_proxies" not in dotcom
    assert dotcom["replay_status"] == "full_replay"
    assert dotcom["portfolio_level_result_available"] is True
    assert dotcom["portfolio_loss_pct"] is not None
    assert dotcom["drawdown_pct"] is not None


def test_attach_stress_results_v1_uses_replay_block_on_report() -> None:
    monthly = _dense_monthly("SPY", 8)
    weights = {"SPY": 1.0}
    report = {
        "scenario_results": [],
        "historical_results": [_minimal_historical_evidence("dotcom")],
        "historical_episode_paths": [],
        "stress_conclusions": {},
        "loss_gate_mode": "diagnostic",
        "historical_stress_replay_v1": build_historical_stress_replay_v1(weights, monthly),
    }
    attach_stress_results_v1(report)
    dotcom = report["stress_results_v1"]["historical_episodes"][0]
    assert dotcom["replay_status"] == "full_replay"
    assert dotcom["user_note"]


def test_partial_replay_clears_portfolio_metrics() -> None:
    monthly = _dense_monthly("SPY", 8)
    weights = {"SPY": 0.7, "META": 0.3}
    replay = build_historical_stress_replay_v1(weights, monthly)
    out = build_stress_results_v1(
        scenario_results=[],
        historical_results=[_minimal_historical_evidence("dotcom")],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
        historical_stress_replay_v1=replay,
    )
    dotcom = out["historical_episodes"][0]
    assert dotcom["replay_status"] == "partial_unavailable"
    assert dotcom["portfolio_level_result_available"] is False
    assert dotcom["portfolio_loss_pct"] is None
    assert dotcom["drawdown_pct"] is None
    assert dotcom["diagnosis_summary_en"]
    assert "70.0%" in dotcom["diagnosis_summary_en"]
    assert "not a full replay" in dotcom["diagnosis_summary_en"].lower()


def test_full_replay_diagnosis_prefers_block_attribution_when_present() -> None:
    monthly = _dense_monthly("SPY", 8)
    monthly["VOO"] = [0.01] * 8
    weights = {"SPY": 0.5, "VOO": 0.5}
    replay = build_historical_stress_replay_v1(weights, monthly)
    historical_results = [
        {
            "episode": "dotcom",
            "pnl_real_episode": -0.12,
            "max_dd": -0.15,
            "data_quality": "ok",
            "coverage_ratio": 1.0,
            "n_obs": 8,
            "return_method": "realized_portfolio_monthly",
            "proxy_used": False,
            "pnl_by_factor_pct": {"beta_equity": -0.08},
        },
        *[_minimal_historical_evidence(ep) for ep in ("2008", "2020", "2022", "banking_2023")],
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
    summary = dotcom["diagnosis_summary_en"]
    assert summary
    assert "dot-com" in summary.lower()
    assert "Model factor attribution" in summary
