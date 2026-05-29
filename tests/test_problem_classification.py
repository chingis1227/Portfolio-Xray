from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.problem_classification import (
    BLOCK_2_6_RISK_TYPE_TO_PROBLEM_IDS,
    HEDGE_GAP_SOURCE_LEGACY,
    HEDGE_GAP_SOURCE_V1,
    PROBLEM_CLASSIFICATION_VERSION,
    SCORECARD_V1_BLOCK,
    STRESS_SCORECARD_SOURCE_LEGACY,
    STRESS_SCORECARD_SOURCE_V1,
    WEAKNESS_MAP_SOURCE_BLOCK,
    build_problem_classification,
    write_problem_classification_outputs,
)
from src.stress import run_stress


def _hedge_gap_v1_stress(
    *,
    protection_profile: str = "mostly_weak_protection",
    main_protection_status: str = "no_protection",
    hedge_gap_status: str = "not_applicable",
) -> dict:
    return {
        "loss_gate_mode": "diagnostic",
        "stress_scorecard_v1": {"overall_status": "DIAG_PASS", "overall_confidence": "medium"},
        "stress_conclusions": {
            "overall_confidence": "medium",
            "hedge_gap_status": hedge_gap_status,
        },
        "hedge_gap_analysis_v1": {
            "version": "hedge_gap_analysis_v1",
            "block_status": "ok",
            "ruleset_version": "hedge_gap_rules_v1_2",
            "summary": {
                "protection_profile": protection_profile,
                "main_hedge_gap": {
                    "risk_type": "equity_crash_protection",
                    "linked_scenario_id": "equity_shock",
                    "protection_status": main_protection_status,
                    "offset_coverage_ratio": 0.0,
                    "portfolio_loss_pct": -0.12,
                    "confidence": "high",
                },
                "main_hedge_gap_scenario_id": "equity_shock",
                "main_hedge_gap_offset_coverage_ratio": 0.0,
                "main_hedge_gap_portfolio_loss_pct": -0.12,
                "diagnosis_summary_en": "Main gap equity crash with no internal offset.",
            },
            "by_risk_type": [
                {
                    "risk_type": "equity_crash_protection",
                    "linked_scenario_id": "equity_shock",
                    "protection_status": main_protection_status,
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
    }


def _block_2_6_xray(*, risk_types: list[dict]) -> dict:
    return {
        "version": "portfolio_xray_v2",
        "block_2_6_portfolio_weakness_map": {
            "block": "2.6_portfolio_weakness_map",
            "status": "ok",
            "summary": "Weakness map completed.",
            "metadata": {"rule_version": "heuristic_v2"},
            "risk_types": risk_types,
        },
        "sections": {
            "weakness_map": {
                "status": "available",
                "legacy": True,
                "product_surface": False,
                "items": [
                    {
                        "type": "weakness",
                        "risk": "volatility_spike",
                        "severity": "high",
                        "confidence": "high",
                        "summary": "Legacy-only row must not drive classification.",
                    }
                ],
            },
            "risk_diagnostics": {
                "status": "available",
                "items": [
                    {
                        "type": "metrics",
                        "vol_annual": 0.22,
                        "max_drawdown": -0.31,
                    }
                ],
            },
        },
    }


def _minimal_stress_report(**kwargs: object) -> dict:
    idx = pd.date_range("2015-01-31", periods=120, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)}, index=idx)
    defaults = dict(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.8, "BBB": 0.2},
        monthly_returns=monthly_returns,
        asset_betas=pd.DataFrame(
            columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]
        ),
        portfolio_betas={k: 0.0 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")},
        target_max_drawdown_pct=0.2,
        cash_proxy_ticker="",
        hedge_assets=["AAA"],
        loss_gate_mode="diagnostic",
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_problem_classification_detects_xray_and_stress_problems() -> None:
    xray = _block_2_6_xray(
        risk_types=[
            {
                "risk_type": "equity_shock",
                "severity": "High",
                "score_0_100": 78,
                "confidence": "high",
                "short_diagnosis": "Equity shock risk is High (score 78/100).",
                "why_status": "Severity is High because equity_weight is above threshold.",
                "next_tests": ["equity_shock", "recession_severe"],
            },
            {
                "risk_type": "liquidity_shock",
                "severity": "Medium",
                "score_0_100": 55,
                "confidence": "medium",
                "short_diagnosis": "Liquidity shock risk is Medium.",
                "why_status": "Severity is Medium based on credit and correlation signals.",
                "next_tests": ["liquidity_shock"],
            },
        ]
    )
    stress = {
        "stress_scorecard_v1": {
            "overall_status": "DIAG_ATTENTION",
            "overall_confidence": "medium",
        },
        "stress_conclusions": {
            "overall_confidence": "medium",
            "worst_synthetic_scenario": {
                "scenario_id": "recession",
                "loss_severity": "high",
            },
            "hedge_gap_status": "attention",
        },
    }

    doc = build_problem_classification(
        portfolio_xray=xray,
        stress_report=stress,
        analysis_end="2026-04-30",
    )

    assert doc["schema_version"] == PROBLEM_CLASSIFICATION_VERSION
    assert doc["diagnostic_only"] is True
    assert doc["analysis_end"] == "2026-04-30"
    assert doc["weakness_map_source"] == WEAKNESS_MAP_SOURCE_BLOCK
    assert doc["hedge_gap_source"] == HEDGE_GAP_SOURCE_LEGACY
    assert doc["stress_scorecard_source"] == STRESS_SCORECARD_SOURCE_LEGACY
    problem_ids = {row["problem_id"] for row in doc["problems"]}
    assert len(doc["problems"]) <= 3
    assert "weak_crisis_resilience" in problem_ids
    assert "high_equity_beta" in problem_ids
    assert "high_drawdown_risk" in problem_ids
    assert doc["summary"]["current_portfolio_acceptable"] is False
    for row in doc["problems"]:
        assert row["evidence"]
        assert row["reasonable_paths_to_test"]
    weakness_evidence = [
        ev
        for row in doc["problems"]
        for ev in row["evidence"]
        if ev.get("source_section") == WEAKNESS_MAP_SOURCE_BLOCK
    ]
    assert weakness_evidence
    assert all(ev.get("risk_type") in BLOCK_2_6_RISK_TYPE_TO_PROBLEM_IDS for ev in weakness_evidence)
    assert not any(ev.get("risk") == "volatility_spike" for ev in weakness_evidence)


def test_problem_classification_ignores_legacy_weakness_map_section() -> None:
    xray = _block_2_6_xray(
        risk_types=[
            {
                "risk_type": "commodity_shock",
                "severity": "Low",
                "score_0_100": 25,
                "confidence": "medium",
                "short_diagnosis": "Low commodity vulnerability.",
                "why_status": "Severity is Low.",
                "next_tests": ["commodity_shock"],
            }
        ]
    )
    doc = build_problem_classification(
        portfolio_xray=xray,
        stress_report={"stress_scorecard_v1": {"overall_status": "DIAG_PASS"}},
    )
    weakness_evidence = [
        ev
        for row in doc["problems"]
        for ev in row["evidence"]
        if ev.get("source_section") == WEAKNESS_MAP_SOURCE_BLOCK
    ]
    assert weakness_evidence == []


def test_problem_classification_accepts_current_when_no_problem_detected() -> None:
    doc = build_problem_classification(
        portfolio_xray={
            "block_2_6_portfolio_weakness_map": {
                "status": "ok",
                "risk_types": [],
            },
            "sections": {"weakness_map": {"status": "available", "items": []}},
        },
        stress_report={"stress_scorecard_v1": {"overall_status": "DIAG_PASS"}},
    )

    assert doc["problems"][0]["problem_id"] == "current_portfolio_acceptable"
    assert doc["summary"]["current_portfolio_acceptable"] is True


def test_problem_classification_warns_on_missing_sources() -> None:
    doc = build_problem_classification(portfolio_xray=None, stress_report=None)

    assert "missing_portfolio_xray" in doc["warnings"]
    assert "missing_stress_report" in doc["warnings"]


def test_problem_classification_uses_hedge_gap_v1_when_legacy_not_applicable() -> None:
    doc = build_problem_classification(
        portfolio_xray={"sections": {}},
        stress_report=_hedge_gap_v1_stress(
            hedge_gap_status="not_applicable",
            main_protection_status="no_protection",
        ),
    )
    assert doc["hedge_gap_source"] == HEDGE_GAP_SOURCE_V1
    problem_ids = {row["problem_id"] for row in doc["problems"]}
    assert "weak_hedge_behavior" in problem_ids
    hedge_evidence = [
        ev
        for row in doc["problems"]
        if row["problem_id"] == "weak_hedge_behavior"
        for ev in row["evidence"]
        if ev.get("source_section") == HEDGE_GAP_SOURCE_V1
    ]
    assert hedge_evidence
    assert hedge_evidence[0].get("main_hedge_gap_protection_status") == "no_protection"
    assert "protection_profile_mostly_weak" in (hedge_evidence[0].get("reason_codes") or [])


def test_problem_classification_v1_supersedes_legacy_attention_when_adequate() -> None:
    doc = build_problem_classification(
        portfolio_xray={"sections": {}},
        stress_report=_hedge_gap_v1_stress(
            protection_profile="mostly_adequate_protection",
            main_protection_status="strong_protection",
            hedge_gap_status="attention",
        ),
    )
    assert doc["hedge_gap_source"] == HEDGE_GAP_SOURCE_V1
    assert "weak_hedge_behavior" not in {row["problem_id"] for row in doc["problems"]}


def test_problem_classification_legacy_hedge_gap_fallback_without_v1() -> None:
    doc = build_problem_classification(
        portfolio_xray={"sections": {}},
        stress_report={
            "stress_conclusions": {"hedge_gap_status": "attention", "overall_confidence": "medium"},
        },
    )
    assert doc["hedge_gap_source"] == HEDGE_GAP_SOURCE_LEGACY
    assert "weak_hedge_behavior" in {row["problem_id"] for row in doc["problems"]}
    legacy_evidence = [
        ev
        for row in doc["problems"]
        if row["problem_id"] == "weak_hedge_behavior"
        for ev in row["evidence"]
        if ev.get("evidence_path") == "legacy_fallback"
    ]
    assert legacy_evidence


def test_problem_classification_prefers_scorecard_v1_when_present() -> None:
    stress = _minimal_stress_report()
    scorecard = stress.get(SCORECARD_V1_BLOCK)
    assert isinstance(scorecard, dict)
    assert scorecard.get("block_status") in {"ok", "partial"}
    signals = scorecard.get("problem_classification_signals") or {}
    assert signals.get("availability") == "available"
    assert signals.get("diagnosis_confidence") in {"high", "medium", "low"}

    doc = build_problem_classification(
        portfolio_xray={"sections": {}},
        stress_report=stress,
    )
    assert doc["stress_scorecard_source"] == STRESS_SCORECARD_SOURCE_V1
    v1_evidence = [
        ev
        for row in doc["problems"]
        for ev in row["evidence"]
        if ev.get("source_section") == SCORECARD_V1_BLOCK
    ]
    assert v1_evidence
    assert not any(ev.get("evidence_path") == "legacy_fallback" for ev in v1_evidence)


def test_problem_classification_scorecard_v1_ignores_legacy_worst_conclusions() -> None:
    stress = _minimal_stress_report()
    stress["stress_conclusions"] = {
        **(stress.get("stress_conclusions") or {}),
        "worst_synthetic_scenario": {
            "scenario_id": "legacy_only_scenario",
            "loss_severity": "high",
        },
        "worst_historical_episode": {
            "episode": "legacy_episode",
            "loss_severity": "high",
        },
    }
    doc = build_problem_classification(
        portfolio_xray={"sections": {}},
        stress_report=stress,
    )
    assert doc["stress_scorecard_source"] == STRESS_SCORECARD_SOURCE_V1
    scenario_ids = {
        ev.get("scenario_id")
        for row in doc["problems"]
        for ev in row["evidence"]
        if ev.get("source_section") == SCORECARD_V1_BLOCK
    }
    assert "legacy_only_scenario" not in scenario_ids
    assert "legacy_episode" not in scenario_ids


def test_write_problem_classification_outputs(tmp_path: Path) -> None:
    path = write_problem_classification_outputs(
        output_dir=tmp_path,
        portfolio_xray={"sections": {}},
        stress_report={},
        analysis_end="2026-04-30",
    )

    assert path == tmp_path / "problem_classification.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == PROBLEM_CLASSIFICATION_VERSION
