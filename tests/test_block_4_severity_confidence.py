"""Tests for Block 4 v3 severity/confidence classifiers and thresholds (Session 05)."""

from __future__ import annotations

import json
from pathlib import Path

from src.block_4.evidence_extraction import extract_evidence_signals
from src.block_4.problem_scoring import score_problems
from src.block_4.severity_confidence import classify_confidence, classify_severity
from src.block_4.thresholds import (
    DEFAULT_THRESHOLDS_PATH,
    THRESHOLDS_VERSION,
    load_block_4_thresholds,
    parse_block_4_thresholds,
)
from block_4_fixtures import hedge_gap_stress as _hedge_gap_stress
from block_4_fixtures import load_golden_xray as _load_golden_xray


def test_load_block_4_thresholds_from_repo_config() -> None:
    cfg = load_block_4_thresholds(DEFAULT_THRESHOLDS_PATH)
    assert cfg.version == THRESHOLDS_VERSION
    assert cfg.ruleset_version == "block_4_v3_2026_06"
    assert cfg.activation.raw_score_min == 0.35
    assert cfg.severity.high_decision_score_min == 0.60
    assert cfg.stress_confirmation_multipliers["confirmed"] == 1.12


def test_parse_block_4_thresholds_merges_overrides() -> None:
    cfg = parse_block_4_thresholds(
        {
            "activation": {"raw_score_min": 0.40},
            "signal_strength": {"vol_baseline": 0.12},
        }
    )
    assert cfg.activation.raw_score_min == 0.40
    assert cfg.activation.min_required_signal_strength == 0.12
    assert cfg.signal_strength.vol_baseline == 0.12


def test_golden_fixture_assigns_severity_and_confidence() -> None:
    evidence = extract_evidence_signals(_load_golden_xray(), _hedge_gap_stress())
    result = score_problems(evidence)

    crisis = result.get_row("weak_crisis_resilience")
    assert crisis is not None
    assert crisis.activated
    assert crisis.severity in {"high", "medium", "low"}
    assert crisis.confidence in {"high", "medium", "low"}

    hedge = result.get_row("weak_hedge_behavior")
    assert hedge is not None
    assert hedge.activated
    assert hedge.scoring.stress_confirmation == "confirmed"
    assert hedge.confidence == "low"
    assert hedge.scoring.materiality == "high"


def test_data_quality_problem_gets_high_severity_low_confidence() -> None:
    xray = {"sections": {f"section_{i}": {"status": "partial"} for i in range(4)}}
    evidence = extract_evidence_signals(xray, {})
    result = score_problems(evidence)
    row = result.get_row("evidence_insufficient_data_quality")
    assert row is not None
    assert row.severity == "high"
    assert row.confidence == "low"


def test_acceptable_portfolio_gets_monitor_severity() -> None:
    xray = {
        "block_2_1_asset_allocation": {
            "status": "ok",
            "portfolio_composition_snapshot": {
                "top1_holding": {"ticker": "A", "weight_pct": 10.0},
                "top3_weight_pct": 28.0,
            },
            "concentration_flags": [],
            "duplicate_exposure_flags": [],
        },
        "block_2_2_portfolio_metrics": {
            "status": "ok",
            "return_risk_metrics": {"vol_annual": 0.08, "sharpe": 0.9, "sortino": 1.1},
            "drawdown_diagnostics": {"max_drawdown": -0.05, "recovered": True},
            "tail_risk_diagnostics": {"es_95": -0.008},
            "benchmark_dependence": {"beta_portfolio": 0.4},
        },
        "block_2_3_factor_exposure": {
            "status": "ok",
            "factor_betas_5y": {"betas": {"beta_eq": 0.4, "beta_rr": 0.1, "beta_credit": 0.05}},
        },
    }
    stress = _hedge_gap_stress(
        hedge_gap_analysis_v1={
            "version": "hedge_gap_analysis_v1",
            "block_status": "ok",
            "summary": {
                "main_hedge_gap": {
                    "protection_status": "strong_protection",
                    "offset_coverage_ratio": 0.75,
                    "portfolio_loss_pct": -0.02,
                }
            },
            "by_risk_type": [],
        },
        scenario_results=[{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.02}],
    )
    evidence = extract_evidence_signals(xray, stress)
    result = score_problems(evidence)
    row = result.get_row("current_portfolio_acceptable")
    assert row is not None
    assert row.severity == "low"
    assert row.confidence == "medium"


def test_inactive_problem_severity_unavailable() -> None:
    cfg = load_block_4_thresholds()
    xray = {
        "block_2_2_portfolio_metrics": {
            "status": "ok",
            "return_risk_metrics": {"vol_annual": 0.11},
        },
    }
    evidence = extract_evidence_signals(xray, {})
    result = score_problems(evidence, thresholds=cfg)
    row = result.get_row("high_volatility")
    assert row is not None
    assert not row.activated
    assert classify_severity(row, cfg) == "unavailable"
    assert classify_confidence(row, evidence, cfg) == "low"
