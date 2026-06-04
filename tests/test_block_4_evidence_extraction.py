"""Tests for Block 4 v3 evidence extraction layer (Session 03)."""

from __future__ import annotations

import json
from pathlib import Path

from src.block_4.evidence_extraction import extract_evidence_signals
from src.current_portfolio_stress_scorecard_block import build_current_portfolio_stress_scorecard_v1
from src.hedge_gap_analysis_block import empty_hedge_gap_analysis_v1
from src.stress_results_block import build_stress_results_v1

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GOLDEN_XRAY = FIXTURES / "portfolio_xray_golden_v2.json"


def _load_golden_xray() -> dict:
    return json.loads(GOLDEN_XRAY.read_text(encoding="utf-8"))


def _hedge_gap_stress(**overrides: object) -> dict:
    base = {
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
                {
                    "risk_type": "rates_up_shock_protection",
                    "linked_scenario_id": "rates_shock",
                    "protection_status": "strong_protection",
                    "offset_coverage_ratio": 0.8,
                    "portfolio_loss_pct": -0.02,
                    "confidence": "high",
                },
            ],
        },
        "scenario_results": [
            {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.12},
            {"scenario_id": "rates_shock", "portfolio_pnl_pct": -0.02},
        ],
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


def test_golden_xray_extracts_canonical_block_signals() -> None:
    xray = _load_golden_xray()
    stress = _hedge_gap_stress()
    result = extract_evidence_signals(xray, stress)

    assert result.signal_count > 0
    assert result.has_signal("vol_annual")
    assert result.has_signal("max_drawdown")
    assert result.has_signal("beta_eq")
    assert result.has_signal("top1_weight_pct")
    assert result.has_signal("concentration_flags")
    assert result.has_signal("rc_top1_share")
    assert result.has_signal("hidden_equity_beta")
    assert result.has_signal("offset_coverage_ratio")
    assert result.has_signal("worst_synthetic_scenario")

    vol = result.get_signals("vol_annual")[0]
    assert vol.source_block == "block_2_2_portfolio_metrics"
    assert vol.evidence_path == "primary"
    assert vol.source_artifact == "portfolio_xray.json"
    assert vol.interpretation_en


def test_block_2_6_signals_use_taxonomy_names() -> None:
    xray = _load_golden_xray()
    stress = _hedge_gap_stress()
    result = extract_evidence_signals(xray, stress)

    equity = result.get_signals("block_2_6_equity_shock")
    assert equity, "expected equity_shock weakness row from golden fixture"
    assert equity[0].source_block == "block_2_6_portfolio_weakness_map"
    assert equity[0].severity in {"medium", "high"}


def test_legacy_sections_fallback_when_block_2_2_unavailable() -> None:
    xray = {
        "sections": {
            "risk_diagnostics": {
                "status": "available",
                "items": [
                    {
                        "type": "metrics",
                        "vol_annual": 0.22,
                        "max_drawdown": -0.18,
                    }
                ],
            }
        },
        "block_2_2_portfolio_metrics": {"status": "unavailable"},
    }
    result = extract_evidence_signals(xray, _hedge_gap_stress())

    assert result.legacy_sections_fallback_used is True
    vol = result.get_signals("vol_annual")[0]
    assert vol.evidence_path == "legacy_fallback"
    assert vol.limitation_en


def test_data_trust_when_many_sections_partial() -> None:
    xray = {
        "sections": {
            f"section_{i}": {"status": "partial"} for i in range(4)
        },
    }
    result = extract_evidence_signals(xray, {})

    assert result.has_signal("partial_sections")
    assert result.has_signal("data_trust_failure")
    assert result.has_signal("stress_block_unavailable")


def test_derived_signals_when_conditions_met() -> None:
    xray = {
        "block_2_1_asset_allocation": {
            "status": "ok",
            "portfolio_composition_snapshot": {"top1_holding": {"ticker": "A", "weight_pct": 8.0}, "top3_weight_pct": 24.0},
            "concentration_flags": [],
            "duplicate_exposure_flags": [{"flag_id": "overlap"}],
            "capital_allocation_breakdown": {
                "by_asset_class": [{"name": "fixed_income", "weight_pct": 10.0}],
                "by_main_risk_factor": [{"name": "credit", "weight_pct": 3.0}],
            },
        },
        "block_2_2_portfolio_metrics": {
            "status": "ok",
            "return_risk_metrics": {"vol_annual": 0.2, "sharpe": 0.2, "sortino": 0.2, "portfolio_cagr": 0.04},
            "drawdown_diagnostics": {"max_drawdown": -0.1, "recovered": True, "recovery_months": 2},
            "correlation_breakdown": {"avg_pairwise_correlation": 0.25},
        },
        "block_2_4_hidden_exposure": {
            "status": "ok",
            "alerts": {
                "correlation_concentration": {
                    "status": "High",
                    "score": 80,
                    "summary": "Correlation cluster detected.",
                }
            },
        },
        "block_2_6_portfolio_weakness_map": {
            "risk_types": [
                {
                    "risk_type": "recession_severe",
                    "severity": "High",
                    "confidence": "high",
                    "score_0_100": 72,
                    "short_diagnosis": "Recession stress hypothesis elevated.",
                }
            ]
        },
    }
    stress = _hedge_gap_stress()
    result = extract_evidence_signals(xray, stress)

    assert result.has_signal("duplicate_exposure")
    assert result.has_signal("broad_equal_weights")
    assert result.has_signal("short_duration_book")
    assert result.has_signal("minimal_credit_weight")
    assert result.has_signal("avg_pairwise_correlation")
    assert result.has_signal("low_correlation_breadth")
    assert result.has_signal("correlation_concentration")
    assert result.has_signal("block_2_6_recession_severe")
    assert result.has_signal("drawdown_recovered_quickly")
    assert result.has_signal("offset_coverage_ratio")


def test_signal_to_dict_roundtrip_fields() -> None:
    xray = _load_golden_xray()
    result = extract_evidence_signals(xray, _hedge_gap_stress())
    sample = next(iter(next(iter(result.signals.values()))))
    d = sample.to_dict()
    for key in ("signal", "value", "source_block", "source_artifact", "evidence_path", "interpretation_en"):
        assert key in d
