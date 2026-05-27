"""Block 3.2 Stress Results — builder contract tests (Sessions 02–07).

Structure, synthetic/historical rows, run_stress wiring, and stress_conclusions alignment.
"""
from __future__ import annotations

import pytest

from src.scenario_library import (
    HISTORICAL_SCENARIO_IDS,
    SCENARIO_LIBRARY_VERSION,
    SYNTHETIC_SCENARIO_IDS,
)
from src.stress import run_stress
from src.stress_results_block import (
    BLOCK_3_2_VERSION,
    attach_stress_results_v1,
    build_stress_results_v1,
    empty_stress_results_v1,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_SYNTHETIC_IDS = list(SYNTHETIC_SCENARIO_IDS)
_HISTORICAL_IDS = list(HISTORICAL_SCENARIO_IDS)


def _fake_scenario_results() -> list[dict]:
    """Minimal synthetic scenario rows matching stress.py field names."""
    rows = []
    for i, sid in enumerate(_SYNTHETIC_IDS):
        rows.append(
            {
                "scenario_id": sid,
                "portfolio_pnl_pct": -0.05 * (i + 1),
                "pnl_by_asset_pct": {"AAA": -0.03, "BBB": -0.02},
                "top3_loss_assets": [{"ticker": "AAA", "pnl_pct": -0.03}],
                "pnl_by_factor_pct": {"eq": -0.04},
                "top1_rc_asset": "AAA",
                "top1_rc_pct": 0.7,
                "top3_rc_assets": ["AAA"],
                "top3_rc_sum_pct": 0.7,
            }
        )
    return rows


def _fake_historical_results() -> list[dict]:
    drawdowns = {"dotcom": -0.35, "2008": -0.50, "2020": -0.25, "2022": -0.18, "banking_2023": -0.12}
    rows = []
    for eid in _HISTORICAL_IDS:
        rows.append(
            {
                "episode": eid,
                "pnl_real_episode": drawdowns[eid] * 0.6,
                "max_dd": drawdowns[eid],
                "data_quality": "good",
                "coverage_ratio": 1.0,
                "n_obs": 12,
            }
        )
    return rows


def _fake_historical_episode_paths() -> list[dict]:
    contrib_by_episode = {
        "dotcom": {"AAA": -0.12, "BBB": -0.08, "TLT": 0.02},
        "2008": {"AAA": -0.20, "BBB": -0.15, "TLT": 0.04},
        "2020": {"AAA": -0.06, "BBB": -0.04},
        "2022": {"AAA": -0.05, "HYG": 0.01},
        "banking_2023": {"AAA": -0.03},
    }
    paths = []
    for eid in _HISTORICAL_IDS:
        contrib = contrib_by_episode.get(eid, {})
        top_loss = sorted(contrib.items(), key=lambda kv: kv[1])[:3]
        paths.append(
            {
                "episode": eid,
                "asset_pnl_contrib_episode": contrib,
                "top_loss_assets_episode": [t for t, _ in top_loss],
            }
        )
    return paths


def _fake_stress_conclusions(scenario_results: list[dict], historical_results: list[dict]) -> dict:
    worst_syn = min(scenario_results, key=lambda r: r["portfolio_pnl_pct"])
    worst_his = min(historical_results, key=lambda r: r["max_dd"])
    return {
        "version": "stress_conclusions_v1",
        "overall_confidence": "medium",
        "worst_synthetic_scenario": {
            "scenario_id": worst_syn["scenario_id"],
            "portfolio_pnl_pct": worst_syn["portfolio_pnl_pct"],
            "loss_severity": "severe",
            "pass": None,
        },
        "worst_historical_episode": {
            "episode": worst_his["episode"],
            "pnl_real_episode": worst_his["pnl_real_episode"],
            "max_dd": worst_his["max_dd"],
            "loss_severity": "severe",
        },
    }


def _build(**kwargs) -> dict:
    syn = _fake_scenario_results()
    his = _fake_historical_results()
    paths = _fake_historical_episode_paths()
    conc = _fake_stress_conclusions(syn, his)
    defaults = dict(
        scenario_results=syn,
        historical_results=his,
        historical_episode_paths=paths,
        stress_conclusions=conc,
        loss_gate_mode="diagnostic",
        helped_assets_worst_synthetic=[],
    )
    defaults.update(kwargs)
    return build_stress_results_v1(**defaults)


# ---------------------------------------------------------------------------
# Top-level structure tests
# ---------------------------------------------------------------------------


def test_version_field() -> None:
    out = _build()
    assert out["version"] == BLOCK_3_2_VERSION == "stress_results_v1"


def test_required_top_level_keys() -> None:
    out = _build()
    for key in (
        "version",
        "loss_gate_mode",
        "diagnosis_method",
        "scenario_library",
        "envelope",
        "synthetic_scenarios",
        "historical_episodes",
    ):
        assert key in out, f"Missing top-level key: {key}"


def test_loss_gate_mode_diagnostic() -> None:
    out = _build(loss_gate_mode="diagnostic")
    assert out["loss_gate_mode"] == "diagnostic"


def test_loss_gate_mode_mandate() -> None:
    out = _build(loss_gate_mode="mandate")
    assert out["loss_gate_mode"] == "mandate"


def test_loss_gate_mode_unknown_falls_back_to_mandate() -> None:
    out = _build(loss_gate_mode="unknown_value")
    assert out["loss_gate_mode"] == "mandate"


# ---------------------------------------------------------------------------
# scenario_library sub-block
# ---------------------------------------------------------------------------


def test_scenario_library_version() -> None:
    out = _build()
    assert out["scenario_library"]["version"] == SCENARIO_LIBRARY_VERSION


def test_scenario_library_synthetic_ids_match_canonical() -> None:
    out = _build()
    assert out["scenario_library"]["synthetic_ids"] == _SYNTHETIC_IDS
    assert len(out["scenario_library"]["synthetic_ids"]) == 8


def test_scenario_library_historical_ids_match_canonical() -> None:
    out = _build()
    assert out["scenario_library"]["historical_ids"] == _HISTORICAL_IDS
    assert len(out["scenario_library"]["historical_ids"]) == 5


# ---------------------------------------------------------------------------
# Envelope sub-block
# ---------------------------------------------------------------------------


def test_envelope_has_required_keys() -> None:
    out = _build()
    env = out["envelope"]
    assert "worst_synthetic" in env
    assert "worst_historical" in env


def test_envelope_worst_synthetic_fields() -> None:
    out = _build()
    ws = out["envelope"]["worst_synthetic"]
    for key in ("scenario_id", "portfolio_loss_pct", "top3_loss_assets", "top_factor_drivers", "helped_assets"):
        assert key in ws, f"worst_synthetic missing: {key}"


def test_envelope_worst_historical_fields() -> None:
    out = _build()
    wh = out["envelope"]["worst_historical"]
    for key in ("episode", "portfolio_loss_pct", "drawdown_pct", "top3_loss_assets"):
        assert key in wh, f"worst_historical missing: {key}"


def test_envelope_worst_synthetic_scenario_id_is_lowest_pnl() -> None:
    """Worst synthetic must be the scenario with the minimum portfolio_pnl_pct."""
    out = _build()
    # _fake_scenario_results gives last ID (recession_severe) the lowest pnl
    assert out["envelope"]["worst_synthetic"]["scenario_id"] == _SYNTHETIC_IDS[-1]


def test_envelope_worst_historical_is_lowest_max_dd() -> None:
    """Worst historical must be the episode with the minimum max_dd (most negative)."""
    out = _build()
    assert out["envelope"]["worst_historical"]["episode"] == "2008"


def test_envelope_worst_synthetic_loss_is_numeric() -> None:
    out = _build()
    loss = out["envelope"]["worst_synthetic"]["portfolio_loss_pct"]
    assert loss is not None and isinstance(loss, float)


def test_envelope_worst_historical_drawdown_is_numeric() -> None:
    out = _build()
    dd = out["envelope"]["worst_historical"]["drawdown_pct"]
    assert dd is not None and isinstance(dd, float)


def test_envelope_helped_assets_passed_through() -> None:
    helped = [{"ticker": "TLT", "pnl_pct": 0.03}]
    out = _build(helped_assets_worst_synthetic=helped)
    assert out["envelope"]["worst_synthetic"]["helped_assets"] == helped


def test_envelope_helped_assets_defaults_to_empty_list() -> None:
    out = _build(helped_assets_worst_synthetic=None)
    assert out["envelope"]["worst_synthetic"]["helped_assets"] == []


# ---------------------------------------------------------------------------
# Synthetic per-scenario rows (Session 03)
# ---------------------------------------------------------------------------


def test_synthetic_scenarios_is_list() -> None:
    out = _build()
    assert isinstance(out["synthetic_scenarios"], list)


def test_synthetic_scenarios_count_and_order() -> None:
    out = _build()
    ids = [row["scenario_id"] for row in out["synthetic_scenarios"]]
    assert ids == _SYNTHETIC_IDS
    assert len(ids) == 8


def test_synthetic_row_required_keys() -> None:
    out = _build()
    row = out["synthetic_scenarios"][0]
    for key in (
        "scenario_id",
        "portfolio_loss_pct",
        "drawdown_pct",
        "availability",
        "loss_contribution",
        "factor_attribution",
        "risk_contribution",
        "assets_helped",
        "diagnosis_summary_en",
    ):
        assert key in row, f"synthetic row missing: {key}"


def test_synthetic_row_maps_portfolio_loss_from_evidence() -> None:
    syn = _fake_scenario_results()
    out = _build(scenario_results=syn)
    first = out["synthetic_scenarios"][0]
    assert first["portfolio_loss_pct"] == syn[0]["portfolio_pnl_pct"]
    assert first["drawdown_pct"] is None


def test_synthetic_diagnosis_summary_en_is_english_sentence() -> None:
    out = _build()
    summary = out["synthetic_scenarios"][0]["diagnosis_summary_en"]
    assert isinstance(summary, str)
    assert "scenario" in summary.lower()
    assert "%" in summary


def test_synthetic_rows_omit_mandate_fields() -> None:
    syn = _fake_scenario_results()
    for row in syn:
        row["pass"] = False
        row["loss_ok"] = False
        row["diagnostic_codes"] = ["DIAG_LOSS_FAIL"]
    out = _build(scenario_results=syn, loss_gate_mode="diagnostic")
    for product_row in out["synthetic_scenarios"]:
        assert "pass" not in product_row
        assert "loss_ok" not in product_row
        assert "diagnostic_codes" not in product_row


def test_worst_synthetic_row_only_has_assets_helped() -> None:
    helped = [{"ticker": "TLT", "pnl_pct": 0.03}]
    out = _build(helped_assets_worst_synthetic=helped)
    worst_id = out["envelope"]["worst_synthetic"]["scenario_id"]
    for row in out["synthetic_scenarios"]:
        if row["scenario_id"] == worst_id:
            assert row["assets_helped"] == helped
        else:
            assert row["assets_helped"] == []


def test_envelope_top_factor_drivers_populated_from_synthetic_rows() -> None:
    out = _build()
    ws = out["envelope"]["worst_synthetic"]
    assert len(ws["top_factor_drivers"]) >= 1
    assert ws["top_factor_drivers"][0]["factor_short"] == "eq"
    assert len(ws["top3_loss_assets"]) >= 1


def test_synthetic_factor_attribution_top_drivers_sorted() -> None:
    syn = _fake_scenario_results()
    syn[0]["pnl_by_factor_pct"] = {"eq": -0.08, "credit": -0.02, "usd": 0.01}
    out = _build(scenario_results=syn)
    drivers = out["synthetic_scenarios"][0]["factor_attribution"]["top_factor_drivers"]
    assert len(drivers) == 2
    assert drivers[0]["pnl_pct"] <= drivers[1]["pnl_pct"]


def test_missing_synthetic_evidence_row_marked_unavailable() -> None:
    syn = _fake_scenario_results()[:1]
    out = _build(scenario_results=syn)
    assert out["synthetic_scenarios"][0]["availability"] == "available"
    assert out["synthetic_scenarios"][1]["availability"] == "unavailable"
    assert out["synthetic_scenarios"][1]["diagnosis_summary_en"] is None


def test_historical_episodes_is_list() -> None:
    out = _build()
    assert isinstance(out["historical_episodes"], list)


# ---------------------------------------------------------------------------
# Historical per-episode rows (Session 04)
# ---------------------------------------------------------------------------


def test_historical_episodes_count_and_order() -> None:
    out = _build()
    ids = [row["episode"] for row in out["historical_episodes"]]
    assert ids == _HISTORICAL_IDS
    assert len(ids) == 5


def test_historical_row_required_keys() -> None:
    out = _build()
    row = out["historical_episodes"][0]
    for key in (
        "episode",
        "portfolio_loss_pct",
        "drawdown_pct",
        "availability",
        "data_quality",
        "coverage_ratio",
        "n_obs",
        "return_method",
        "proxy_used",
        "loss_contribution",
        "factor_attribution",
        "risk_contribution",
        "assets_helped",
        "diagnosis_summary_en",
    ):
        assert key in row, f"historical row missing: {key}"


def test_historical_row_maps_loss_and_drawdown_from_evidence() -> None:
    his = _fake_historical_results()
    out = _build(historical_results=his)
    first = out["historical_episodes"][0]
    assert first["portfolio_loss_pct"] == his[0]["pnl_real_episode"]
    assert first["drawdown_pct"] == his[0]["max_dd"]


def test_historical_loss_contribution_from_paths() -> None:
    out = _build()
    row_2008 = next(r for r in out["historical_episodes"] if r["episode"] == "2008")
    lc = row_2008["loss_contribution"]
    assert lc["availability"] == "available"
    assert lc["pnl_by_asset_pct"]["AAA"] == -0.20
    assert len(lc["top3_loss_assets"]) >= 1
    assert lc["top3_loss_assets"][0]["ticker"] == "AAA"


def test_historical_risk_contribution_not_applicable() -> None:
    out = _build()
    rc = out["historical_episodes"][0]["risk_contribution"]
    assert rc["availability"] == "not_applicable"


def test_historical_factor_attribution_unavailable_without_enrichment() -> None:
    out = _build()
    fa = out["historical_episodes"][0]["factor_attribution"]
    assert fa["availability"] == "unavailable"
    assert fa["reason_en"] == "factor_attribution_requires_report_enrichment"


def test_historical_factor_attribution_available_when_enriched() -> None:
    his = _fake_historical_results()
    his[0]["pnl_by_factor_pct"] = {"beta_eq": -0.10, "beta_credit": -0.03, "beta_rr": 0.02}
    out = _build(historical_results=his)
    fa = out["historical_episodes"][0]["factor_attribution"]
    assert fa["availability"] == "available"
    assert len(fa["top_factor_drivers"]) == 2


def test_historical_diagnosis_summary_en_is_english_sentence() -> None:
    out = _build()
    summary = out["historical_episodes"][1]["diagnosis_summary_en"]
    assert isinstance(summary, str)
    assert "episode" in summary.lower()
    assert "%" in summary


def test_historical_assets_helped_from_positive_contrib() -> None:
    out = _build()
    row_2008 = next(r for r in out["historical_episodes"] if r["episode"] == "2008")
    helped = row_2008["assets_helped"]
    assert any(item["ticker"] == "TLT" for item in helped)


def test_historical_rows_omit_mandate_fields() -> None:
    his = _fake_historical_results()
    for row in his:
        row["pass"] = False
        row["diagnostic_code"] = "DIAG_HIST_FAIL"
    out = _build(historical_results=his, loss_gate_mode="diagnostic")
    for product_row in out["historical_episodes"]:
        assert "pass" not in product_row
        assert "diagnostic_code" not in product_row


def test_historical_loss_contribution_unavailable_when_n_obs_low() -> None:
    his = _fake_historical_results()
    his[0]["n_obs"] = 1
    out = _build(historical_results=his)
    lc = out["historical_episodes"][0]["loss_contribution"]
    assert lc["availability"] == "unavailable"
    assert lc["reason_en"] == "insufficient_episode_data"


def test_historical_loss_contribution_unavailable_when_path_missing() -> None:
    his = _fake_historical_results()
    paths = _fake_historical_episode_paths()[1:]
    out = _build(historical_results=his, historical_episode_paths=paths)
    lc = out["historical_episodes"][0]["loss_contribution"]
    assert lc["availability"] == "unavailable"
    assert lc["reason_en"] == "insufficient_episode_data"


def test_envelope_worst_historical_top3_from_built_rows() -> None:
    out = _build()
    wh = out["envelope"]["worst_historical"]
    assert wh["episode"] == "2008"
    assert len(wh["top3_loss_assets"]) >= 1
    assert wh["top3_loss_assets"][0]["ticker"] == "AAA"


def test_missing_historical_evidence_row_marked_unavailable() -> None:
    his = _fake_historical_results()[:1]
    paths = _fake_historical_episode_paths()[:1]
    out = _build(historical_results=his, historical_episode_paths=paths)
    assert out["historical_episodes"][0]["availability"] == "available"
    assert out["historical_episodes"][1]["availability"] == "unavailable"
    assert out["historical_episodes"][1]["diagnosis_summary_en"] is None


# ---------------------------------------------------------------------------
# Empty fallback
# ---------------------------------------------------------------------------


def test_empty_stress_results_v1_top_level_keys() -> None:
    out = empty_stress_results_v1("test_reason")
    for key in ("version", "loss_gate_mode", "scenario_library", "envelope", "synthetic_scenarios", "historical_episodes", "error"):
        assert key in out, f"Empty fallback missing: {key}"


def test_empty_stress_results_v1_version() -> None:
    out = empty_stress_results_v1()
    assert out["version"] == BLOCK_3_2_VERSION


def test_empty_stress_results_v1_error_field() -> None:
    out = empty_stress_results_v1("my_reason")
    assert out["error"] == "my_reason"


def test_empty_stress_results_v1_gate_mode() -> None:
    out_diag = empty_stress_results_v1(loss_gate_mode="diagnostic")
    assert out_diag["loss_gate_mode"] == "diagnostic"
    out_man = empty_stress_results_v1(loss_gate_mode="mandate")
    assert out_man["loss_gate_mode"] == "mandate"


def test_empty_stress_results_v1_scenario_ids_still_populated() -> None:
    """Even empty fallback must carry canonical IDs so consumers can iterate."""
    out = empty_stress_results_v1()
    assert out["scenario_library"]["synthetic_ids"] == _SYNTHETIC_IDS
    assert out["scenario_library"]["historical_ids"] == _HISTORICAL_IDS


def test_empty_stress_results_v1_envelope_all_none() -> None:
    out = empty_stress_results_v1()
    ws = out["envelope"]["worst_synthetic"]
    wh = out["envelope"]["worst_historical"]
    assert ws["scenario_id"] is None
    assert ws["portfolio_loss_pct"] is None
    assert wh["episode"] is None
    assert wh["drawdown_pct"] is None


# ---------------------------------------------------------------------------
# run_stress wiring (Session 05)
# ---------------------------------------------------------------------------


def _minimal_run_stress(**kwargs: object) -> dict:
    import pandas as pd

    idx = pd.date_range("1995-01-31", periods=360, freq="ME")
    monthly_returns = pd.DataFrame(
        {"AAA": [0.008] * len(idx), "BBB": [0.006] * len(idx)},
        index=idx,
    )
    defaults = dict(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.99, "BBB": 0.01},
        monthly_returns=monthly_returns,
        asset_betas=pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]),
        portfolio_betas={k: 0.05 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")},
        target_max_drawdown_pct=0.05,
        cash_proxy_ticker="",
        loss_gate_mode="diagnostic",
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_run_stress_includes_stress_results_v1() -> None:
    out = _minimal_run_stress()
    block = out.get("stress_results_v1")
    assert isinstance(block, dict)
    assert block.get("version") == BLOCK_3_2_VERSION
    assert block.get("loss_gate_mode") == "diagnostic"
    assert len(block.get("synthetic_scenarios") or []) == 8
    assert len(block.get("historical_episodes") or []) == 5


def test_run_stress_worst_synthetic_matches_conclusions() -> None:
    out = _minimal_run_stress()
    conclusions = out.get("stress_conclusions") or {}
    block = out.get("stress_results_v1") or {}
    worst_id = (conclusions.get("worst_synthetic_scenario") or {}).get("scenario_id")
    assert block.get("envelope", {}).get("worst_synthetic", {}).get("scenario_id") == worst_id


def test_run_stress_worst_historical_matches_conclusions_by_max_dd() -> None:
    out = _minimal_run_stress()
    conclusions = out.get("stress_conclusions") or {}
    block = out.get("stress_results_v1") or {}
    worst_ep = (conclusions.get("worst_historical_episode") or {}).get("episode")
    env = block.get("envelope", {}).get("worst_historical") or {}
    assert env.get("episode") == worst_ep
    assert env.get("drawdown_pct") == (conclusions.get("worst_historical_episode") or {}).get("max_dd")


def test_run_stress_available_synthetic_rows_have_english_diagnosis() -> None:
    out = _minimal_run_stress()
    for row in out["stress_results_v1"]["synthetic_scenarios"]:
        if row.get("availability") != "available":
            continue
        summary = row.get("diagnosis_summary_en")
        assert isinstance(summary, str) and summary.strip()
        assert "%" in summary


def test_run_stress_available_historical_rows_have_english_diagnosis() -> None:
    out = _minimal_run_stress()
    for row in out["stress_results_v1"]["historical_episodes"]:
        if row.get("availability") != "available":
            continue
        summary = row.get("diagnosis_summary_en")
        assert isinstance(summary, str) and summary.strip()
        assert "%" in summary


def test_build_worst_synthetic_loss_matches_envelope_and_conclusions() -> None:
    out = _build()
    conc = _fake_stress_conclusions(_fake_scenario_results(), _fake_historical_results())
    env_loss = out["envelope"]["worst_synthetic"]["portfolio_loss_pct"]
    conc_loss = conc["worst_synthetic_scenario"]["portfolio_pnl_pct"]
    assert env_loss == conc_loss
    worst_row = next(
        r for r in out["synthetic_scenarios"] if r["scenario_id"] == out["envelope"]["worst_synthetic"]["scenario_id"]
    )
    assert worst_row["portfolio_loss_pct"] == env_loss


def test_run_stress_empty_report_includes_stress_results_v1() -> None:
    import pandas as pd

    idx = pd.date_range("2024-01-31", periods=1, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01]}, index=idx)
    out = run_stress(
        tickers=["AAA"],
        weights={"AAA": 1.0},
        monthly_returns=monthly_returns,
        asset_betas=pd.DataFrame(columns=["beta_eq"]),
        portfolio_betas={"beta_eq": 0.1},
        target_max_drawdown_pct=0.05,
        cash_proxy_ticker="",
        loss_gate_mode="diagnostic",
    )
    block = out.get("stress_results_v1")
    assert isinstance(block, dict)
    assert block.get("version") == BLOCK_3_2_VERSION
    assert block.get("error") == "Insufficient return history"
    assert block.get("synthetic_scenarios") == []


def test_attach_stress_results_v1_refreshes_historical_factor_attribution() -> None:
    his = _fake_historical_results()
    paths = _fake_historical_episode_paths()
    syn = _fake_scenario_results()
    conc = _fake_stress_conclusions(syn, his)
    report = {
        "scenario_results": syn,
        "historical_results": his,
        "historical_episode_paths": paths,
        "stress_conclusions": conc,
        "loss_gate_mode": "diagnostic",
    }
    attach_stress_results_v1(report)
    fa_before = report["stress_results_v1"]["historical_episodes"][0]["factor_attribution"]
    assert fa_before["availability"] == "unavailable"

    report["historical_results"][0]["pnl_by_factor_pct"] = {"beta_eq": -0.10, "beta_credit": 0.02}
    attach_stress_results_v1(report)
    fa_after = report["stress_results_v1"]["historical_episodes"][0]["factor_attribution"]
    assert fa_after["availability"] == "available"
    assert len(fa_after["top_factor_drivers"]) >= 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_scenario_results_produces_none_envelope() -> None:
    out = build_stress_results_v1(
        scenario_results=[],
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    assert out["envelope"]["worst_synthetic"]["scenario_id"] is None
    assert out["envelope"]["worst_historical"]["episode"] is None


def test_conclusions_worst_id_takes_priority_over_scan() -> None:
    """If stress_conclusions names a specific worst ID, use that row (not min-scan)."""
    syn = _fake_scenario_results()
    his = _fake_historical_results()
    paths = _fake_historical_episode_paths()
    # Override conclusions to point at first scenario regardless of pnl
    conclusions = {
        "worst_synthetic_scenario": {"scenario_id": _SYNTHETIC_IDS[0]},
        "worst_historical_episode": {"episode": _HISTORICAL_IDS[0]},
    }
    out = build_stress_results_v1(
        scenario_results=syn,
        historical_results=his,
        historical_episode_paths=paths,
        stress_conclusions=conclusions,
        loss_gate_mode="diagnostic",
    )
    assert out["envelope"]["worst_synthetic"]["scenario_id"] == _SYNTHETIC_IDS[0]
    assert out["envelope"]["worst_historical"]["episode"] == _HISTORICAL_IDS[0]


def test_conclusions_bad_id_falls_back_to_scan() -> None:
    """If stress_conclusions has an ID not in results, fall back to min-scan."""
    syn = _fake_scenario_results()
    his = _fake_historical_results()
    paths = _fake_historical_episode_paths()
    conclusions = {
        "worst_synthetic_scenario": {"scenario_id": "nonexistent_id"},
        "worst_historical_episode": {"episode": "nonexistent_episode"},
    }
    out = build_stress_results_v1(
        scenario_results=syn,
        historical_results=his,
        historical_episode_paths=paths,
        stress_conclusions=conclusions,
        loss_gate_mode="diagnostic",
    )
    # Fallback: min-scan gives recession_severe (last, lowest pnl) and 2008 (lowest max_dd)
    assert out["envelope"]["worst_synthetic"]["scenario_id"] == _SYNTHETIC_IDS[-1]
    assert out["envelope"]["worst_historical"]["episode"] == "2008"
