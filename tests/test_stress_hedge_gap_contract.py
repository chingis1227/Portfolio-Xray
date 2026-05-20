"""Contract tests for hedge_gap_analysis (Stress Lab hedge gap v2)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.portfolio_commentary import write_stress_commentary
from src.stress import (
    HEDGE_GAP_RISK_TYPE_ORDER,
    HEDGE_GAP_SCENARIO_BY_RISK,
    HEDGE_GAP_SCENARIOS_BY_RISK,
    HEDGE_LABEL_RISK_ROLES,
    _build_hedge_gap_analysis,
    _build_hedge_gap_by_risk_type,
    run_stress,
)


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
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_hedge_gap_contract_required_fields() -> None:
    out = _minimal_run(hedge_assets=["AAA"])
    hg = out["hedge_gap_analysis"]
    for key in (
        "method",
        "scenario_mapping",
        "hedge_label_risk_roles",
        "hedge_assets_considered",
        "n_hedge_assets_considered",
        "worst_scenario_id",
        "worst_scenario_portfolio_pnl_pct",
        "hedge_assets_negative_in_worst_scenario",
        "gap_detected",
        "status",
        "status_reason",
        "status_reason_en",
        "by_risk_type",
        "n_risk_types_evaluated",
        "any_risk_type_gap_detected",
    ):
        assert key in hg
    assert hg["method"] == "stress_scenario_hedge_evidence_v2"
    assert hg["scenario_mapping"] == "HEDGE_GAP_SCENARIO_BY_RISK"
    assert isinstance(hg["by_risk_type"], list)
    assert hg["n_risk_types_evaluated"] == len(hg["by_risk_type"])
    assert hg["hedge_label_risk_roles"] == list(HEDGE_LABEL_RISK_ROLES)
    assert hg["status"] in {
        "gap_detected",
        "no_gap_detected",
        "insufficient_data",
        "not_applicable",
    }
    assert isinstance(hg["gap_detected"], bool)
    assert isinstance(hg["status_reason_en"], str) and hg["status_reason_en"]
    assert out["stress_conclusions"]["hedge_gap_status"] == hg["status"]


def test_hedge_gap_not_applicable_without_hedge_labels() -> None:
    out = _minimal_run(hedge_assets=[])
    hg = out["hedge_gap_analysis"]
    assert hg["status"] == "not_applicable"
    assert hg["status_reason"] == "no_hedge_labels"
    assert "risk_role" in hg["status_reason_en"].lower() or "taxonomy" in hg["status_reason_en"].lower()
    assert hg["gap_detected"] is False
    assert hg["n_hedge_assets_considered"] == 0
    assert hg["by_risk_type"] == []
    assert hg["any_risk_type_gap_detected"] is False


def test_hedge_gap_not_applicable_empty_report() -> None:
    out = _minimal_run(monthly_returns=pd.DataFrame())
    hg = out["hedge_gap_analysis"]
    assert hg["status"] == "not_applicable"
    assert hg["status_reason"] == "no_hedge_labels"
    assert hg["worst_scenario_portfolio_pnl_pct"] is None
    assert out["stress_conclusions"]["hedge_gap_status"] == "not_applicable"


def test_build_hedge_gap_insufficient_data_no_synthetic_scenarios() -> None:
    hg = _build_hedge_gap_analysis(worst_scenario_row=None, hedge_assets=["AAA"])
    assert hg["status"] == "insufficient_data"
    assert hg["status_reason"] == "no_synthetic_scenarios"
    assert hg["n_hedge_assets_considered"] == 1


def test_build_hedge_gap_insufficient_data_portfolio_pnl_unavailable() -> None:
    worst = {"scenario_id": "equity_shock", "portfolio_pnl_pct": None, "pnl_by_asset_pct": {}}
    hg = _build_hedge_gap_analysis(worst_scenario_row=worst, hedge_assets=["AAA"])
    assert hg["status"] == "insufficient_data"
    assert hg["status_reason"] == "portfolio_pnl_unavailable"
    assert hg["worst_scenario_id"] == "equity_shock"


def test_build_hedge_gap_detected_when_portfolio_loss_and_hedge_non_positive() -> None:
    worst = {
        "scenario_id": "equity_shock",
        "portfolio_pnl_pct": -0.12,
        "pnl_by_asset_pct": {"AAA": -0.05, "BBB": 0.01},
    }
    hg = _build_hedge_gap_analysis(worst_scenario_row=worst, hedge_assets=["AAA"])
    assert hg["status"] == "gap_detected"
    assert hg["status_reason"] == "gap_evidence"
    assert hg["gap_detected"] is True
    assert hg["worst_scenario_portfolio_pnl_pct"] == -0.12
    assert hg["hedge_assets_negative_in_worst_scenario"] == [{"ticker": "AAA", "pnl_pct": -0.05}]


def test_build_hedge_gap_no_gap_when_portfolio_not_losing() -> None:
    worst = {
        "scenario_id": "equity_shock",
        "portfolio_pnl_pct": 0.02,
        "pnl_by_asset_pct": {"AAA": -0.01, "BBB": 0.03},
    }
    hg = _build_hedge_gap_analysis(worst_scenario_row=worst, hedge_assets=["AAA"])
    assert hg["status"] == "no_gap_detected"
    assert hg["status_reason"] == "no_gap_evidence_global"
    assert hg["gap_detected"] is False
    assert hg["hedge_assets_negative_in_worst_scenario"] == []


def test_build_hedge_gap_no_gap_when_hedge_positive_in_loss_scenario() -> None:
    worst = {
        "scenario_id": "recession_severe",
        "portfolio_pnl_pct": -0.2,
        "pnl_by_asset_pct": {"AAA": 0.03, "BBB": -0.25},
    }
    hg = _build_hedge_gap_analysis(worst_scenario_row=worst, hedge_assets=["AAA"])
    assert hg["status"] == "no_gap_detected"
    assert hg["status_reason"] == "no_gap_evidence_global"
    assert hg["gap_detected"] is False


def test_hedge_gap_scenario_map_aligned_with_portfolio_xray() -> None:
    from src.portfolio_xray import WEAKNESS_SCENARIO_MAP

    assert HEDGE_GAP_SCENARIO_BY_RISK == WEAKNESS_SCENARIO_MAP


def test_by_risk_type_covers_mapped_risk_types_when_scenarios_present() -> None:
    scenario_results = [
        {
            "scenario_id": sid,
            "portfolio_pnl_pct": -0.05,
            "pnl_by_asset_pct": {"AAA": 0.01},
        }
        for sid in HEDGE_GAP_SCENARIO_BY_RISK
    ]
    rows = _build_hedge_gap_by_risk_type(scenario_results=scenario_results, hedge_assets=["AAA"])
    assert [r["risk_type"] for r in rows] == list(HEDGE_GAP_RISK_TYPE_ORDER)
    for row in rows:
        assert row["mapped_scenario_ids"] == HEDGE_GAP_SCENARIOS_BY_RISK[row["risk_type"]]
        assert row["evaluation_scenario_id"] in row["mapped_scenario_ids"]
        assert row["scenario_mapping"] == "HEDGE_GAP_SCENARIO_BY_RISK"


def test_by_risk_type_gap_detected_on_mapped_scenario_not_global_worst() -> None:
    """Global worst is inflation; recession mapped scenario still flags hedge gap."""
    scenario_results = [
        {
            "scenario_id": "inflation_stagflation",
            "portfolio_pnl_pct": -0.30,
            "pnl_by_asset_pct": {"AAA": 0.04, "BBB": -0.35},
        },
        {
            "scenario_id": "recession_severe",
            "portfolio_pnl_pct": -0.12,
            "pnl_by_asset_pct": {"AAA": -0.04, "BBB": -0.10},
        },
        {
            "scenario_id": "equity_shock",
            "portfolio_pnl_pct": -0.08,
            "pnl_by_asset_pct": {"AAA": 0.02, "BBB": -0.12},
        },
    ]
    worst = min(scenario_results, key=lambda x: float(x["portfolio_pnl_pct"]))
    hg = _build_hedge_gap_analysis(
        worst_scenario_row=worst,
        hedge_assets=["AAA"],
        scenario_results=scenario_results,
    )
    assert hg["worst_scenario_id"] == "inflation_stagflation"
    assert hg["status"] == "no_gap_detected"
    assert hg["any_risk_type_gap_detected"] is True
    recession_row = next(r for r in hg["by_risk_type"] if r["risk_type"] == "recession")
    assert recession_row["evaluation_scenario_id"] == "recession_severe"
    assert recession_row["gap_detected"] is True
    assert recession_row["hedge_assets_negative"] == [{"ticker": "AAA", "pnl_pct": -0.04}]
    inflation_row = next(r for r in hg["by_risk_type"] if r["risk_type"] == "inflation")
    assert inflation_row["gap_detected"] is False


def test_by_risk_type_scenario_not_available_when_mapped_missing() -> None:
    scenario_results = [
        {
            "scenario_id": "equity_shock",
            "portfolio_pnl_pct": -0.10,
            "pnl_by_asset_pct": {"AAA": -0.02},
        },
    ]
    rows = _build_hedge_gap_by_risk_type(scenario_results=scenario_results, hedge_assets=["AAA"])
    recession_row = next(r for r in rows if r["risk_type"] == "recession")
    assert recession_row["status"] == "insufficient_data"
    assert recession_row["status_reason"] == "scenario_not_available"
    assert recession_row["evaluation_scenario_id"] is None
    equity_row = next(r for r in rows if r["risk_type"] == "equity_crash")
    assert equity_row["evaluation_scenario_id"] == "equity_shock"
    assert equity_row["gap_detected"] is True


def test_run_stress_gap_detected_with_equity_beta_and_hedge_label() -> None:
    idx = pd.date_range("2015-01-31", periods=60, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)}, index=idx)
    portfolio_betas = {
        "beta_eq": 1.0,
        "beta_rr": 0.0,
        "beta_inf": 0.0,
        "beta_credit": 0.0,
        "beta_usd": 0.0,
        "beta_cmd": 0.0,
    }
    out = run_stress(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.5, "BBB": 0.5},
        monthly_returns=monthly_returns,
        asset_betas=pd.DataFrame(columns=list(portfolio_betas.keys())),
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.5,
        cash_proxy_ticker="",
        hedge_assets=["AAA"],
    )
    hg = out["hedge_gap_analysis"]
    assert hg["n_hedge_assets_considered"] == 1
    assert hg["worst_scenario_portfolio_pnl_pct"] is not None
    assert float(hg["worst_scenario_portfolio_pnl_pct"]) < 0
    assert hg["status"] == "gap_detected"
    assert hg["gap_detected"] is True
    assert hg["hedge_assets_negative_in_worst_scenario"]


def test_stress_commentary_states_hedge_gap_not_applicable(tmp_path: Path) -> None:
    out_dir = tmp_path / "subject"
    out_dir.mkdir()
    stress = {
        "hedge_gap_analysis": {
            "status": "not_applicable",
            "status_reason": "no_hedge_labels",
            "status_reason_en": "No portfolio holdings carry hedge risk_role labels in ETF/stock taxonomy.",
        },
    }
    path = write_stress_commentary(out_dir, stress_report=stress, analysis_end="2026-02-28")
    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert "Hedge gap: not applicable" in text
    assert "no_hedge_labels" not in text
    assert "risk_role" in text.lower() or "taxonomy" in text.lower()
