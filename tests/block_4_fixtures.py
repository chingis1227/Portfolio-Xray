"""Shared Block 4 v2 test fixtures and ten portfolio archetypes (Session 11)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.current_portfolio_stress_scorecard_block import build_current_portfolio_stress_scorecard_v1
from src.stress_results_block import build_stress_results_v1

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GOLDEN_XRAY = FIXTURES / "portfolio_xray_golden_v2.json"
ARCHETYPE_MANIFEST = FIXTURES / "block_4" / "archetype_manifest.json"


def load_golden_xray() -> dict[str, Any]:
    return json.loads(GOLDEN_XRAY.read_text(encoding="utf-8"))


def load_archetype_manifest() -> dict[str, Any]:
    return json.loads(ARCHETYPE_MANIFEST.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Block4ArchetypeCase:
    archetype_id: str
    portfolio_xray: dict[str, Any]
    stress_report: dict[str, Any]
    expected_primary_ids: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    launchpad_may_proceed: bool
    label_en: str = ""


def hedge_gap_stress(**overrides: object) -> dict[str, Any]:
    base: dict[str, Any] = {
        "loss_gate_mode": "diagnostic",
        "stress_scorecard_v1": {"overall_status": "DIAG_PASS", "overall_confidence": "medium"},
        "stress_conclusions": {"overall_confidence": "medium", "hedge_gap_status": "not_applicable"},
        "hedge_gap_analysis_v1": {
            "version": "hedge_gap_analysis_v1",
            "block_status": "ok",
            "ruleset_version": "hedge_gap_rules_v1_2",
            "summary": {
                "protection_profile": "mostly_weak_protection",
                "main_hedge_gap": {
                    "risk_type": "equity_crash_protection",
                    "linked_scenario_id": "equity_shock",
                    "protection_status": "no_protection",
                    "offset_coverage_ratio": 0.0,
                    "portfolio_loss_pct": -0.12,
                    "confidence": "high",
                },
                "diagnosis_summary_en": "Main gap equity crash with no internal offset.",
            },
            "by_risk_type": [
                {
                    "risk_type": "equity_crash_protection",
                    "linked_scenario_id": "equity_shock",
                    "protection_status": "no_protection",
                    "offset_coverage_ratio": 0.0,
                    "portfolio_loss_pct": -0.12,
                    "confidence": "high",
                },
            ],
        },
        "scenario_results": [{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.12}],
        "historical_results": [],
        "data_trust_summary": {},
    }
    base.update(overrides)  # type: ignore[arg-type]
    base["stress_results_v1"] = build_stress_results_v1(
        scenario_results=base["scenario_results"],
        historical_results=base["historical_results"],
        historical_episode_paths=[],
        stress_conclusions=base.get("stress_conclusions") or {},
        loss_gate_mode="diagnostic",
    )
    if "current_portfolio_stress_scorecard_v1" not in base:
        base["current_portfolio_stress_scorecard_v1"] = build_current_portfolio_stress_scorecard_v1(base)
    return base


def _benign_hedge_gap() -> dict[str, Any]:
    return {
        "version": "hedge_gap_analysis_v1",
        "block_status": "ok",
        "ruleset_version": "hedge_gap_rules_v1_2",
        "summary": {
            "protection_profile": "mostly_strong_protection",
            "main_hedge_gap": {
                "risk_type": "equity_crash_protection",
                "linked_scenario_id": "equity_shock",
                "protection_status": "strong_protection",
                "offset_coverage_ratio": 0.72,
                "portfolio_loss_pct": -0.03,
                "confidence": "high",
            },
            "diagnosis_summary_en": "Internal offsets absorb most of the equity shock.",
        },
        "by_risk_type": [
            {
                "risk_type": "equity_crash_protection",
                "linked_scenario_id": "equity_shock",
                "protection_status": "strong_protection",
                "offset_coverage_ratio": 0.72,
                "portfolio_loss_pct": -0.03,
                "confidence": "high",
            },
        ],
    }


def benign_stress(
    *,
    scenario_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    scenarios = scenario_results or [{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.03}]
    return hedge_gap_stress(
        hedge_gap_analysis_v1=_benign_hedge_gap(),
        scenario_results=scenarios,
    )


def _ok_block_2_1(
    *,
    top1_ticker: str,
    top1_pct: float,
    top3_pct: float,
    concentration_flags: list[dict[str, Any]] | None = None,
    duplicate_flags: list[dict[str, Any]] | None = None,
    by_asset_class: list[dict[str, Any]] | None = None,
    by_main_risk_factor: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    block: dict[str, Any] = {
        "status": "ok",
        "portfolio_composition_snapshot": {
            "top1_holding": {"ticker": top1_ticker, "weight_pct": top1_pct},
            "top3_weight_pct": top3_pct,
        },
        "concentration_flags": concentration_flags or [],
        "duplicate_exposure_flags": duplicate_flags or [],
    }
    breakdown: dict[str, Any] = {}
    if by_asset_class:
        breakdown["by_asset_class"] = by_asset_class
    if by_main_risk_factor:
        breakdown["by_main_risk_factor"] = by_main_risk_factor
    if breakdown:
        block["capital_allocation_breakdown"] = breakdown
    return block


def _ok_block_2_2(
    *,
    vol: float,
    sharpe: float | None = None,
    sortino: float | None = None,
    max_dd: float = -0.08,
    es_95: float = -0.012,
    beta: float = 0.5,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {"vol_annual": vol}
    if sharpe is not None:
        metrics["sharpe"] = sharpe
    if sortino is not None:
        metrics["sortino"] = sortino
    return {
        "status": "ok",
        "return_risk_metrics": metrics,
        "drawdown_diagnostics": {"max_drawdown": max_dd, "recovered": True},
        "tail_risk_diagnostics": {"es_95": es_95},
        "benchmark_dependence": {"beta_portfolio": beta},
    }


def _ok_block_2_3(
    *,
    beta_eq: float,
    beta_rr: float = 0.1,
    beta_credit: float = 0.05,
) -> dict[str, Any]:
    return {
        "status": "ok",
        "factor_betas_5y": {
            "betas": {
                "beta_eq": beta_eq,
                "beta_rr": beta_rr,
                "beta_credit": beta_credit,
            }
        },
    }


def _block_2_4_alerts(**alerts: dict[str, Any]) -> dict[str, Any]:
    return {"status": "ok", "alerts": alerts}


def _block_2_6_risk(
    risk_type: str,
    *,
    severity: str = "high",
    score: int = 72,
    short_diagnosis: str | None = None,
) -> dict[str, Any]:
    return {
        "risk_types": [
            {
                "risk_type": risk_type,
                "severity": severity,
                "score_0_100": score,
                "short_diagnosis": short_diagnosis or f"{risk_type} weakness is elevated on the weakness map.",
            }
        ]
    }


def archetype_concentrated_equity() -> Block4ArchetypeCase:
    return Block4ArchetypeCase(
        archetype_id="concentrated_equity",
        label_en="Concentrated equity growth book",
        portfolio_xray={
            "block_2_1_asset_allocation": _ok_block_2_1(
                top1_ticker="SPY",
                top1_pct=58.0,
                top3_pct=88.0,
                concentration_flags=[{"severity": "high", "flag": "top1_holding_above_threshold"}],
            ),
            "block_2_2_portfolio_metrics": _ok_block_2_2(vol=0.16, beta=0.95),
            "block_2_3_factor_exposure": _ok_block_2_3(beta_eq=0.92),
        },
        stress_report=hedge_gap_stress(
            hedge_gap_analysis_v1={
                "version": "hedge_gap_analysis_v1",
                "block_status": "ok",
                "summary": {
                    "main_hedge_gap": {
                        "protection_status": "partial_protection",
                        "offset_coverage_ratio": 0.25,
                        "portfolio_loss_pct": -0.08,
                    }
                },
                "by_risk_type": [],
            },
            scenario_results=[{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.08}],
        ),
        expected_primary_ids=("high_concentration",),
        expected_outcomes=("proceed_to_launchpad",),
        launchpad_may_proceed=True,
    )


def archetype_balanced_60_40() -> Block4ArchetypeCase:
    return Block4ArchetypeCase(
        archetype_id="balanced_60_40",
        label_en="Balanced 60/40-style portfolio",
        portfolio_xray={
            "block_2_1_asset_allocation": _ok_block_2_1(
                top1_ticker="SPY",
                top1_pct=14.0,
                top3_pct=38.0,
                by_asset_class=[
                    {"name": "equity", "weight_pct": 58.0},
                    {"name": "fixed_income", "weight_pct": 38.0},
                ],
            ),
            "block_2_2_portfolio_metrics": _ok_block_2_2(
                vol=0.10,
                sharpe=0.78,
                sortino=0.92,
                max_dd=-0.07,
                es_95=-0.011,
                beta=0.52,
            ),
            "block_2_3_factor_exposure": _ok_block_2_3(beta_eq=0.48, beta_rr=0.12),
        },
        stress_report=benign_stress(),
        expected_primary_ids=("current_portfolio_acceptable",),
        expected_outcomes=("monitor", "proceed_to_launchpad"),
        launchpad_may_proceed=False,
    )


def archetype_duration_heavy_bonds() -> Block4ArchetypeCase:
    return Block4ArchetypeCase(
        archetype_id="duration_heavy_bonds",
        label_en="Duration-heavy bond portfolio",
        portfolio_xray={
            "block_2_1_asset_allocation": _ok_block_2_1(
                top1_ticker="TLT",
                top1_pct=22.0,
                top3_pct=48.0,
                by_asset_class=[{"name": "fixed_income", "weight_pct": 62.0}],
            ),
            "block_2_2_portfolio_metrics": _ok_block_2_2(vol=0.09, beta=0.22, max_dd=-0.06),
            "block_2_3_factor_exposure": _ok_block_2_3(beta_eq=0.18, beta_rr=0.62),
            "block_2_4_hidden_exposure": _block_2_4_alerts(
                duration_concentration={
                    "status": "High",
                    "summary": "Duration risk is concentrated in long Treasuries.",
                    "confidence": "high",
                }
            ),
            "block_2_6_portfolio_weakness_map": _block_2_6_risk(
                "rates_shock",
                short_diagnosis="Rates-up shock would pressure the bond sleeve.",
            ),
        },
        stress_report=benign_stress(
            scenario_results=[
                {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.02},
                {"scenario_id": "rates_shock", "portfolio_pnl_pct": -0.11},
            ],
        ),
        expected_primary_ids=("duration_rates_vulnerability", "poor_rates_up_behavior"),
        expected_outcomes=("proceed_to_launchpad",),
        launchpad_may_proceed=True,
    )


def archetype_high_credit_carry() -> Block4ArchetypeCase:
    return Block4ArchetypeCase(
        archetype_id="high_credit_carry",
        label_en="High credit carry book",
        portfolio_xray={
            "block_2_1_asset_allocation": _ok_block_2_1(
                top1_ticker="HYG",
                top1_pct=22.0,
                top3_pct=48.0,
                by_main_risk_factor=[{"name": "credit", "weight_pct": 42.0}],
            ),
            "block_2_2_portfolio_metrics": _ok_block_2_2(vol=0.12, beta=0.35, es_95=-0.018),
            "block_2_3_factor_exposure": _ok_block_2_3(beta_eq=0.3, beta_credit=0.45),
            "block_2_4_hidden_exposure": _block_2_4_alerts(
                credit_liquidity_risk={
                    "status": "High",
                    "summary": "Credit and liquidity fragility is elevated.",
                    "confidence": "medium",
                }
            ),
            "block_2_6_portfolio_weakness_map": _block_2_6_risk(
                "credit_shock",
                short_diagnosis="Credit spread shock would hurt carry positions.",
            ),
        },
        stress_report=benign_stress(
            scenario_results=[
                {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.03},
                {"scenario_id": "credit_shock", "portfolio_pnl_pct": -0.11},
            ],
        ),
        expected_primary_ids=("credit_liquidity_fragility", "weak_crisis_resilience"),
        expected_outcomes=("proceed_to_launchpad",),
        launchpad_may_proceed=True,
    )


def archetype_pseudo_diversified_equity_etfs() -> Block4ArchetypeCase:
    return Block4ArchetypeCase(
        archetype_id="pseudo_diversified_equity_etfs",
        label_en="Pseudo-diversified equity ETF sleeve",
        portfolio_xray={
            "block_2_1_asset_allocation": _ok_block_2_1(
                top1_ticker="QQQ",
                top1_pct=12.0,
                top3_pct=34.0,
                duplicate_flags=[
                    {"ticker": "SPY", "duplicate_of": "VOO", "severity": "medium"},
                    {"ticker": "IVV", "duplicate_of": "VOO", "severity": "medium"},
                ],
            ),
            "block_2_2_portfolio_metrics": _ok_block_2_2(vol=0.16, beta=0.9),
            "block_2_3_factor_exposure": _ok_block_2_3(beta_eq=0.86),
            "block_2_4_hidden_exposure": _block_2_4_alerts(
                correlation_concentration={
                    "status": "High",
                    "summary": "Holdings look diversified but share a common equity factor.",
                    "confidence": "high",
                }
            ),
            "block_2_5_risk_budget_view": {
                "status": "ok",
                "top1_rc_asset": {"ticker": "QQQ", "rc_pct": 38.0},
            },
        },
        stress_report=benign_stress(
            scenario_results=[{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.06}],
        ),
        expected_primary_ids=("poor_diversification", "high_equity_beta"),
        expected_outcomes=("proceed_to_launchpad",),
        launchpad_may_proceed=True,
    )


def archetype_cash_heavy_conservative() -> Block4ArchetypeCase:
    return Block4ArchetypeCase(
        archetype_id="cash_heavy_conservative",
        label_en="Cash-heavy conservative book",
        portfolio_xray={
            "block_2_1_asset_allocation": _ok_block_2_1(
                top1_ticker="BIL",
                top1_pct=11.0,
                top3_pct=30.0,
                by_asset_class=[
                    {"name": "cash", "weight_pct": 44.0},
                    {"name": "fixed_income", "weight_pct": 30.0},
                    {"name": "equity", "weight_pct": 20.0},
                ],
            ),
            "block_2_2_portfolio_metrics": _ok_block_2_2(
                vol=0.04,
                sharpe=0.55,
                max_dd=-0.02,
                es_95=-0.005,
                beta=0.12,
            ),
            "block_2_3_factor_exposure": _ok_block_2_3(beta_eq=0.12, beta_rr=0.04),
        },
        stress_report=benign_stress(
            scenario_results=[{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.01}],
        ),
        expected_primary_ids=("current_portfolio_acceptable",),
        expected_outcomes=("monitor", "proceed_to_launchpad"),
        launchpad_may_proceed=False,
    )


def archetype_weak_hedge() -> Block4ArchetypeCase:
    return Block4ArchetypeCase(
        archetype_id="weak_hedge",
        label_en="Weak crisis hedge / stress gap",
        portfolio_xray=load_golden_xray(),
        stress_report=hedge_gap_stress(),
        expected_primary_ids=("weak_crisis_resilience", "weak_hedge_behavior"),
        expected_outcomes=("proceed_to_launchpad",),
        launchpad_may_proceed=True,
    )


def archetype_insufficient_data() -> Block4ArchetypeCase:
    return Block4ArchetypeCase(
        archetype_id="insufficient_data",
        label_en="Partial upstream sections / data quality",
        portfolio_xray={"sections": {f"section_{i}": {"status": "partial"} for i in range(4)}},
        stress_report={},
        expected_primary_ids=("evidence_insufficient_data_quality",),
        expected_outcomes=("do_not_act_yet",),
        launchpad_may_proceed=False,
    )


def archetype_conflicting_signals() -> Block4ArchetypeCase:
    return Block4ArchetypeCase(
        archetype_id="conflicting_signals",
        label_en="High vol vs mild stress tension",
        portfolio_xray={
            "block_2_2_portfolio_metrics": _ok_block_2_2(vol=0.22, beta=0.7),
        },
        stress_report=hedge_gap_stress(
            scenario_results=[{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.03}],
            hedge_gap_analysis_v1={
                "version": "hedge_gap_analysis_v1",
                "block_status": "ok",
                "summary": {
                    "main_hedge_gap": {
                        "protection_status": "partial_protection",
                        "offset_coverage_ratio": 0.4,
                        "portfolio_loss_pct": -0.03,
                    }
                },
                "by_risk_type": [],
            },
        ),
        expected_primary_ids=("evidence_insufficient_conflicting_signals",),
        expected_outcomes=("do_not_act_yet",),
        launchpad_may_proceed=False,
    )


def archetype_acceptable_no_action() -> Block4ArchetypeCase:
    return Block4ArchetypeCase(
        archetype_id="acceptable_no_action",
        label_en="Broad low-risk acceptable book",
        portfolio_xray={
            "block_2_1_asset_allocation": _ok_block_2_1(
                top1_ticker="VTI",
                top1_pct=11.0,
                top3_pct=28.0,
            ),
            "block_2_2_portfolio_metrics": _ok_block_2_2(
                vol=0.09,
                sharpe=0.88,
                sortino=1.05,
                max_dd=-0.05,
                es_95=-0.008,
                beta=0.42,
            ),
            "block_2_3_factor_exposure": _ok_block_2_3(beta_eq=0.42),
        },
        stress_report=benign_stress(
            scenario_results=[{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.02}],
        ),
        expected_primary_ids=("current_portfolio_acceptable",),
        expected_outcomes=("monitor",),
        launchpad_may_proceed=False,
    )


def all_block_4_archetypes() -> tuple[Block4ArchetypeCase, ...]:
    return (
        archetype_concentrated_equity(),
        archetype_balanced_60_40(),
        archetype_duration_heavy_bonds(),
        archetype_high_credit_carry(),
        archetype_pseudo_diversified_equity_etfs(),
        archetype_cash_heavy_conservative(),
        archetype_weak_hedge(),
        archetype_insufficient_data(),
        archetype_conflicting_signals(),
        archetype_acceptable_no_action(),
    )


def archetype_by_id(archetype_id: str) -> Block4ArchetypeCase:
    for case in all_block_4_archetypes():
        if case.archetype_id == archetype_id:
            return case
    raise KeyError(archetype_id)
