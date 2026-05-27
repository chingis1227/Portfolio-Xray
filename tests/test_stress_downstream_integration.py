"""Downstream integration: snapshot, candidate comparison, commentary (Session 10)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.candidate_comparison import _stress_from_artifacts
from src.portfolio_commentary import write_stress_commentary
from src.snapshot import _stress_suite_results_for_snapshot
from src.stress import crisis_replay_summary_from_paths, run_stress


def _minimal_run(**kwargs: object) -> dict:
    idx = pd.date_range("2015-01-31", periods=120, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)}, index=idx)
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.8, "BBB": 0.2}
    asset_betas = pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"])
    portfolio_betas = {k: 0.0 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")}
    defaults = dict(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.2,
        cash_proxy_ticker="",
        hedge_assets=["AAA"],
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_crisis_replay_summary_omits_daily_rows() -> None:
    paths = [
        {
            "replay_version": "crisis_replay_v2",
            "episode": "2020",
            "episode_start": "2020-02-01",
            "episode_end": "2020-06-30",
            "time_to_recovery_months": 4.0,
            "recovered": True,
            "top_loss_assets_episode": ["URA", "XLE"],
            "rows": [{"date": "2020-03-31", "portfolio_return": -0.1}],
        }
    ]
    summary = crisis_replay_summary_from_paths(paths)
    assert len(summary) == 1
    assert summary[0]["episode"] == "2020"
    assert summary[0]["top_loss_assets_episode"] == ["URA", "XLE"]
    assert "rows" not in summary[0]


def test_snapshot_stress_suite_includes_governance_fields() -> None:
    out = _minimal_run()
    section = _stress_suite_results_for_snapshot(out, portfolio_params={})
    assert section.get("failed_scenario") == out.get("failed_scenario")
    hm = section.get("historical_methodology") or {}
    assert hm.get("version") == "historical_methodology_v1"
    assert hm.get("proxy_used_in_primary_stress") is False
    crs = section.get("crisis_replay_summary") or []
    assert isinstance(crs, list)
    paths = out.get("historical_episode_paths") or []
    if paths:
        assert len(crs) == len(paths)
        assert "rows" not in (crs[0] if crs else {})
    conclusions = section.get("conclusions") or {}
    assert "top_factor_drivers_worst_scenario" in conclusions
    hg = section.get("hedge_gap_analysis") or {}
    assert "by_risk_type" in hg
    stress_results = section.get("stress_results") or {}
    assert stress_results.get("version") == "stress_results_v1"
    assert isinstance(stress_results.get("envelope"), dict)
    assert "worst_synthetic" in (stress_results.get("envelope") or {})


def test_candidate_comparison_stress_merges_snapshot_and_report(tmp_path: Path) -> None:
    out = _minimal_run()
    folder = tmp_path / "candidate"
    folder.mkdir()
    suite = _stress_suite_results_for_snapshot(out, portfolio_params={})
    snap = {"stress_suite_results": suite}
    with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(snap, f)
    with open(folder / "stress_report.json", "w", encoding="utf-8") as f:
        json.dump(out, f)

    stress = _stress_from_artifacts(folder, snap)
    assert stress.get("overall") == out.get("status")
    assert stress.get("historical_methodology", {}).get("version") == "historical_methodology_v1"
    assert isinstance(stress.get("crisis_replay_summary"), list)
    assert stress.get("conclusions", {}).get("version") == "stress_conclusions_v1"
    assert "by_risk_type" in (stress.get("hedge_gap_analysis") or {})
    assert stress.get("stress_results", {}).get("version") == "stress_results_v1"


def test_stress_commentary_includes_methodology_and_crisis_replay(tmp_path: Path) -> None:
    out = _minimal_run()
    final = tmp_path / "Main portfolio"
    final.mkdir(parents=True)
    path = write_stress_commentary(final, stress_report=out, analysis_end="2026-02-28")
    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert "Historical stress methodology" in text
    assert "realized_portfolio_monthly" in text or "primary_path=realized_only" in text
    if out.get("historical_episode_paths"):
        assert "Crisis replay (path-level, crisis_replay_v2)" in text
    assert "Block 3.2 stress results (stress_results_v1" in text
    assert "Block 3.2 worst synthetic:" in text
    assert "Block 3.2 worst historical:" in text
