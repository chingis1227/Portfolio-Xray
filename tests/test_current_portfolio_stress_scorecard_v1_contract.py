"""Contract tests for Block 3.4 current_portfolio_stress_scorecard_v1."""

from __future__ import annotations

import pandas as pd
import pytest

from src.current_portfolio_stress_scorecard_block import (
    BLOCK_3_4_VERSION,
    RULESET_VERSION,
    SCORECARD_SCOPE,
    build_current_portfolio_stress_scorecard_v1,
    collect_forbidden_english_phrases,
    empty_current_portfolio_stress_scorecard_v1,
)
from src.block_2_4_hidden_exposure import build_block_2_4_hidden_exposure
from src.block_2_6_portfolio_weakness_map import build_block_2_6_portfolio_weakness_map
from src.hedge_gap_analysis_block import (
    apply_hidden_exposure_confirmation_bridge,
    apply_weakness_map_confirmation_bridge,
    attach_hedge_gap_analysis_v1,
    build_hedge_gap_analysis_v1,
    empty_hedge_gap_analysis_v1,
)
from test_block_2_4_hidden_exposure import _block_2_1, _block_2_2, _block_2_3, _taxonomy
from test_block_2_6_portfolio_weakness_map import _block_2_4, _block_2_5
from src.scenario_library import HISTORICAL_SCENARIO_IDS, SYNTHETIC_SCENARIO_IDS
from src.stress import run_stress
from src.stress_results_block import build_stress_results_v1, empty_stress_results_v1


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
        loss_gate_mode="diagnostic",
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_block_exists_and_has_required_keys() -> None:
    out = _minimal_run()
    block = out.get(BLOCK_3_4_VERSION)
    assert isinstance(block, dict)
    assert block["version"] == BLOCK_3_4_VERSION
    assert block["block"] == "3.4"
    assert block["loss_gate_mode"] in {"diagnostic", "mandate"}
    for key in (
        "ruleset_version",
        "block_status",
        "scorecard_scope",
        "source_blocks_used",
        "stress_coverage",
        "legacy_fallback_used",
        "limitations",
        "scenario_library",
        "worst_synthetic_scenario",
        "worst_historical_scenario",
        "portfolio_loss_summary",
        "historical_drawdown_summary",
        "top_loss_contributors",
        "loss_contribution_summary",
        "top_risk_contributors",
        "risk_contribution_summary",
        "factor_stress_attribution_summary",
        "assets_helped_hurt_summary",
        "offset_coverage_summary",
        "main_hedge_gap",
        "hedge_gap_summary",
        "relatively_resilient_scenarios",
        "less_damaging_scenarios",
        "stress_diagnosis",
        "problem_classification_signals",
        "candidate_comparison_targets",
        "ai_commentary_context",
        "next_decision_uses",
        "pre_stress_confirmation_summary",
        "data_quality_warnings",
        "diagnosis_summary_en",
    ):
        assert key in block, f"Missing key: {key}"


def test_ruleset_version_and_scorecard_scope() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    assert block["ruleset_version"] == RULESET_VERSION
    assert block["scorecard_scope"] == SCORECARD_SCOPE == "current_portfolio_diagnostic"


def test_block_status_on_minimal_run() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    assert block["block_status"] in {"ok", "partial"}


def test_block_status_unavailable_when_stress_results_missing() -> None:
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": empty_stress_results_v1("fixture"),
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    assert block["block_status"] == "unavailable"
    assert block["ruleset_version"] == RULESET_VERSION
    assert block["legacy_fallback_used"] is False


def test_empty_block_has_product_metadata() -> None:
    block = empty_current_portfolio_stress_scorecard_v1("fixture")
    assert block["block_status"] == "unavailable"
    assert block["ruleset_version"] == RULESET_VERSION
    assert block["scorecard_scope"] == SCORECARD_SCOPE
    assert block["source_blocks_used"] == []
    assert block["legacy_fallback_used"] is False
    assert isinstance(block["limitations"], list)
    cov = block["stress_coverage"]
    assert cov["n_synthetic_available"] == 0
    assert cov["fraction_synthetic_available"] is None


def test_source_blocks_used_lists_evidence_blocks() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    used = block["source_blocks_used"]
    assert isinstance(used, list)
    assert "stress_results_v1" in used
    assert "hedge_gap_analysis_v1" in used
    assert "stress_conclusions" in used
    assert "data_trust_summary" in used


def test_legacy_fallback_used_is_explicit_boolean() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    assert block["legacy_fallback_used"] is False
    assert isinstance(block["legacy_fallback_used"], bool)


def test_linkage_to_block_3_2_and_3_3() -> None:
    out = _minimal_run()
    assert out["stress_results_v1"]["version"] == "stress_results_v1"
    assert out["hedge_gap_analysis_v1"]["version"] == "hedge_gap_analysis_v1"
    block = out[BLOCK_3_4_VERSION]
    assert isinstance(block.get("scenario_library"), dict)
    assert block["scenario_library"]["version"] == out["stress_results_v1"]["scenario_library"]["version"]


def test_worst_selectors_use_required_rules() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    ws = block["worst_synthetic_scenario"]
    assert ws["availability"] == "available"
    worst_id = ws["scenario_id"]
    # required: min portfolio_pnl_pct (same as Block 3.2 envelope.worst_synthetic)
    assert worst_id == out["stress_results_v1"]["envelope"]["worst_synthetic"]["scenario_id"]
    assert ws["selection_metric"] == "portfolio_pnl_pct"
    assert ws["selection_source"] == "stress_results_v1.envelope"
    assert ws["portfolio_loss_pct"] == out["stress_results_v1"]["envelope"]["worst_synthetic"]["portfolio_loss_pct"]

    wh = block["worst_historical_scenario"]
    assert wh["availability"] == "available"
    # required: min max_dd (same as Block 3.2 envelope.worst_historical)
    assert wh["episode"] == out["stress_results_v1"]["envelope"]["worst_historical"]["episode"]
    assert wh["selection_metric"] == "max_dd"
    assert wh["selection_source"] == "stress_results_v1.envelope"
    assert wh["drawdown_pct"] == out["stress_results_v1"]["envelope"]["worst_historical"]["drawdown_pct"]


def test_stress_coverage_present_and_matches_rows() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    cov = block["stress_coverage"]
    sr = out["stress_results_v1"]
    syn_rows = sr.get("synthetic_scenarios") or []
    hist_rows = sr.get("historical_episodes") or []
    assert cov["n_synthetic_total"] == len(syn_rows)
    assert cov["n_historical_total"] == len(hist_rows)
    assert cov["n_synthetic_available"] == sum(
        1 for r in syn_rows if isinstance(r, dict) and r.get("availability") == "available"
    )
    assert cov["n_historical_available"] == sum(
        1
        for r in hist_rows
        if isinstance(r, dict)
        and r.get("availability") == "available"
        and isinstance(r.get("drawdown_pct"), (int, float))
    )
    if cov["n_synthetic_total"] > 0:
        assert cov["fraction_synthetic_available"] == cov["n_synthetic_available"] / cov["n_synthetic_total"]
    if cov["n_historical_total"] > 0:
        assert cov["fraction_historical_available"] == cov["n_historical_available"] / cov["n_historical_total"]


def test_worst_historical_uses_drawdown_not_worst_pnl_episode() -> None:
    """Envelope worst historical must follow min max_dd, not min episode PnL."""
    scenario_results = [
        {"scenario_id": sid, "portfolio_pnl_pct": -0.01} for sid in SYNTHETIC_SCENARIO_IDS
    ]
    historical_results = [
        {"episode": "dotcom", "pnl_real_episode": -0.05, "max_dd": -0.50},
        {"episode": "2008", "pnl_real_episode": -0.60, "max_dd": -0.25},
        {"episode": "2020", "pnl_real_episode": -0.10, "max_dd": -0.15},
        {"episode": "2022", "pnl_real_episode": -0.08, "max_dd": -0.12},
        {"episode": "banking_2023", "pnl_real_episode": -0.04, "max_dd": -0.08},
    ]
    paths = [
        {"episode": eid, "asset_pnl_contrib_episode": {"AAA": -0.01}, "top_loss_assets_episode": ["AAA"]}
        for eid in HISTORICAL_SCENARIO_IDS
    ]
    stress_results = build_stress_results_v1(
        scenario_results=scenario_results,
        historical_results=historical_results,
        historical_episode_paths=paths,
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    wh = block["worst_historical_scenario"]
    assert wh["availability"] == "available"
    assert wh["episode"] == "dotcom"
    assert wh["episode"] != "2008"


def test_worst_synthetic_unavailable_when_envelope_loss_non_numeric() -> None:
    stress_results = empty_stress_results_v1("fixture")
    stress_results["envelope"]["worst_synthetic"] = {
        "scenario_id": "equity_shock",
        "portfolio_loss_pct": None,
        "top3_loss_assets": [],
        "top_factor_drivers": [],
        "helped_assets": [],
    }
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    ws = block["worst_synthetic_scenario"]
    assert ws["availability"] == "unavailable"
    assert ws["reason_en"] == "worst_synthetic_loss_non_numeric"


def test_stress_coverage_uses_scenario_library_when_row_lists_empty() -> None:
    stress_results = empty_stress_results_v1("fixture")
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    cov = block["stress_coverage"]
    lib = stress_results["scenario_library"]
    assert cov["n_synthetic_total"] == len(lib["synthetic_ids"])
    assert cov["n_historical_total"] == len(lib["historical_ids"])
    assert cov["n_synthetic_available"] == 0
    assert cov["fraction_synthetic_available"] == 0.0


def test_worst_selector_consistency_limitation_on_envelope_drift() -> None:
    stress_results = empty_stress_results_v1("fixture")
    syn_id = stress_results["scenario_library"]["synthetic_ids"][0]
    stress_results["envelope"]["worst_synthetic"] = {
        "scenario_id": syn_id,
        "portfolio_loss_pct": -0.99,
        "top3_loss_assets": [],
        "top_factor_drivers": [],
        "helped_assets": [],
    }
    stress_results["synthetic_scenarios"] = [
        {
            "scenario_id": sid,
            "portfolio_pnl_pct": -0.01 * (i + 1),
            "availability": "available",
        }
        for i, sid in enumerate(stress_results["scenario_library"]["synthetic_ids"][:3])
    ]
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    assert "worst_synthetic_envelope_id_not_min_pnl" in block["limitations"]


def test_loss_contribution_summary_aliases_top_loss_contributors() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    top = block["top_loss_contributors"]
    summary = block["loss_contribution_summary"]
    assert summary["availability"] == top["availability"]
    for branch in ("synthetic", "historical"):
        top_branch = top.get(branch)
        sum_branch = summary.get(branch)
        assert isinstance(top_branch, dict)
        assert isinstance(sum_branch, dict)
        for key in ("scenario_id", "episode", "top3_loss_assets", "availability", "reason_en"):
            if key in top_branch:
                assert sum_branch.get(key) == top_branch.get(key)


def test_loss_concentration_top3_share_computed_from_pnl_by_asset() -> None:
    scenario_results = [
        {
            "scenario_id": "equity_shock",
            "portfolio_pnl_pct": -0.20,
            "pnl_by_asset_pct": {"AAA": -0.12, "BBB": -0.06, "CCC": -0.02},
            "top3_loss_assets": [
                {"ticker": "AAA", "pnl_pct": -0.12},
                {"ticker": "BBB", "pnl_pct": -0.06},
                {"ticker": "CCC", "pnl_pct": -0.02},
            ],
            "top1_rc_asset": "AAA",
            "top1_rc_pct": 0.5,
            "top3_rc_assets": ["AAA"],
            "top3_rc_sum_pct": 0.5,
        }
    ]
    stress_results = build_stress_results_v1(
        scenario_results=scenario_results,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    syn = block["loss_contribution_summary"]["synthetic"]
    assert syn["loss_concentration_top3_share"] == pytest.approx(1.0)


def test_risk_contribution_summary_aliases_top_risk_contributors() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    top = block["top_risk_contributors"]
    summary = block["risk_contribution_summary"]
    for key in ("availability", "scenario_id", "top1_rc_asset", "top1_rc_pct", "top3_rc_assets", "top3_rc_sum_pct", "reason_en"):
        if key in top:
            assert summary.get(key) == top.get(key)


def test_rc_overlap_with_loss_contributors_flag() -> None:
    scenario_results = [
        {
            "scenario_id": "equity_shock",
            "portfolio_pnl_pct": -0.20,
            "pnl_by_asset_pct": {"AAA": -0.12, "BBB": -0.08},
            "top3_loss_assets": [
                {"ticker": "AAA", "pnl_pct": -0.12},
                {"ticker": "BBB", "pnl_pct": -0.08},
            ],
            "top1_rc_asset": "AAA",
            "top1_rc_pct": 0.6,
            "top3_rc_assets": ["AAA", "CCC"],
            "top3_rc_sum_pct": 0.8,
        }
    ]
    stress_results = build_stress_results_v1(
        scenario_results=scenario_results,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    summary = block["risk_contribution_summary"]
    assert summary["availability"] == "available"
    assert summary["rc_overlap_with_loss_contributors"] is True


def test_rc_overlap_omitted_when_rc_unavailable() -> None:
    stress_results = empty_stress_results_v1("fixture")
    syn_id = stress_results["scenario_library"]["synthetic_ids"][0]
    stress_results["envelope"]["worst_synthetic"] = {
        "scenario_id": syn_id,
        "portfolio_loss_pct": -0.10,
        "top3_loss_assets": [{"ticker": "AAA", "pnl_pct": -0.10}],
        "top_factor_drivers": [],
        "helped_assets": [],
    }
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    summary = block["risk_contribution_summary"]
    assert summary["availability"] == "unavailable"
    assert "rc_overlap_with_loss_contributors" not in summary


def test_hedge_gap_summary_links_to_block_3_3_main_gap() -> None:
    scenario_rows = [
        {
            "scenario_id": "inflation_stagflation",
            "portfolio_pnl_pct": -0.10,
            "pnl_by_asset_pct": {"EQ1": -0.07, "EQ2": -0.05, "BOND": 0.025},
            "pnl_by_factor_pct": {"eq": -0.08, "inf": -0.02},
            "top1_rc_asset": "EQ1",
            "top1_rc_pct": 0.6,
            "top3_rc_assets": ["EQ1"],
            "top3_rc_sum_pct": 0.6,
        }
    ]
    stress_results = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    hedge_gap = build_hedge_gap_analysis_v1(
        stress_results_v1=stress_results,
        scenario_results=scenario_rows,
        loss_gate_mode="diagnostic",
    )
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": hedge_gap,
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    hg_summary = block["hedge_gap_summary"]
    hg_block_summary = hedge_gap["summary"]
    main = hg_block_summary["main_hedge_gap"]
    assert hg_summary["availability"] == "available"
    assert hg_summary["main_hedge_gap_scenario_id"] == main["linked_scenario_id"]
    assert hg_summary["main_hedge_gap_scenario_id"] == hg_block_summary["main_hedge_gap_scenario_id"]
    assert hg_summary["main_hedge_gap_risk_type"] == main["risk_type"]
    assert hg_summary["offset_coverage_ratio"] == main["offset_coverage_ratio"]
    assert hg_summary["hedge_gap_block_status"] == hedge_gap["block_status"]
    assert hg_summary["hedge_gap_ruleset_version"] == hedge_gap["ruleset_version"]
    assert hg_summary["protection_profile"] == hg_block_summary["protection_profile"]


def test_hedge_gap_summary_unavailable_when_block_3_3_missing() -> None:
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": empty_stress_results_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    hg_summary = block["hedge_gap_summary"]
    assert hg_summary["availability"] == "unavailable"
    assert hg_summary["reason_en"] == "hedge_gap_analysis_v1_unavailable"


def test_hedge_gap_summary_unavailable_when_main_gap_missing() -> None:
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": empty_stress_results_v1("fixture"),
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    hg_summary = block["hedge_gap_summary"]
    assert hg_summary["availability"] == "unavailable"
    assert hg_summary["reason_en"] == "main_hedge_gap_unavailable"
    assert hg_summary["hedge_gap_block_status"] == "unavailable"


def test_factor_stress_attribution_matches_worst_synthetic() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    factor = block["factor_stress_attribution_summary"]
    worst = block["worst_synthetic_scenario"]
    assert factor["availability"] == "available"
    assert factor["scenario_id"] == worst["scenario_id"]
    assert isinstance(factor["top_factor_drivers"], list)


def test_factor_stress_attribution_falls_back_to_synthetic_row() -> None:
    scenario_results = [
        {
            "scenario_id": "equity_shock",
            "portfolio_pnl_pct": -0.20,
            "pnl_by_asset_pct": {"AAA": -0.12, "BBB": -0.08},
            "pnl_by_factor_pct": {"eq": -0.15, "credit": -0.05},
            "top1_rc_asset": "AAA",
            "top1_rc_pct": 0.6,
            "top3_rc_assets": ["AAA"],
            "top3_rc_sum_pct": 0.6,
        }
    ]
    stress_results = build_stress_results_v1(
        scenario_results=scenario_results,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    env = stress_results["envelope"]["worst_synthetic"]
    env["top_factor_drivers"] = []
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    factor = block["factor_stress_attribution_summary"]
    assert factor["availability"] == "available"
    assert len(factor["top_factor_drivers"]) >= 1


def test_stress_diagnosis_present_on_minimal_run() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    diag = block["stress_diagnosis"]
    assert isinstance(diag, dict)
    for key in (
        "headline",
        "diagnosis_summary_en",
        "diagnosis_confidence",
        "confidence_reason",
        "confidence_reason_en",
        "key_findings",
    ):
        assert key in diag
    assert block["block_status"] in {"ok", "partial"}
    assert isinstance(diag["headline"], str) and diag["headline"].strip()
    assert diag["diagnosis_confidence"] in {"high", "medium", "low", "unavailable"}
    assert isinstance(diag["key_findings"], list)
    assert block["diagnosis_summary_en"] == diag["diagnosis_summary_en"]


def test_next_decision_uses_when_block_available() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    uses = block["next_decision_uses"]
    assert block["block_status"] in {"ok", "partial"}
    assert uses == [
        "problem_classification",
        "candidate_comparison",
        "ai_commentary",
        "monitoring",
    ]


def test_next_decision_uses_empty_when_unavailable() -> None:
    block = empty_current_portfolio_stress_scorecard_v1("fixture")
    assert block["next_decision_uses"] == []
    assert block["stress_diagnosis"]["diagnosis_confidence"] == "unavailable"


def test_problem_classification_signals_on_minimal_run() -> None:
    out = _minimal_run()
    signals = out[BLOCK_3_4_VERSION]["problem_classification_signals"]
    assert signals["availability"] == "available"
    assert signals["stress_severity"] in {"high", "moderate", "low", "unknown"}
    assert signals["diagnosis_confidence"] in {"high", "medium", "low", "unavailable"}
    assert signals.get("worst_synthetic_id") is not None


def test_problem_classification_signals_unavailable_when_block_unavailable() -> None:
    block = empty_current_portfolio_stress_scorecard_v1("fixture")
    signals = block["problem_classification_signals"]
    assert signals["availability"] == "unavailable"
    assert signals["diagnosis_confidence"] == "unavailable"
    assert signals["stress_severity"] is None


def test_candidate_comparison_targets_on_minimal_run() -> None:
    out = _minimal_run()
    targets = out[BLOCK_3_4_VERSION]["candidate_comparison_targets"]
    assert targets["availability"] == "available"
    assert targets.get("worst_synthetic_scenario_id") is not None
    assert isinstance(targets.get("compare_offset_coverage"), bool)


def test_candidate_comparison_targets_unavailable_when_block_unavailable() -> None:
    block = empty_current_portfolio_stress_scorecard_v1("fixture")
    targets = block["candidate_comparison_targets"]
    assert targets["availability"] == "unavailable"
    assert targets["compare_offset_coverage"] is False


def test_ai_commentary_context_on_minimal_run() -> None:
    out = _minimal_run()
    ctx = out[BLOCK_3_4_VERSION]["ai_commentary_context"]
    assert ctx["availability"] == "available"
    assert ctx["stress_scorecard_source"] == BLOCK_3_4_VERSION
    assert ctx["diagnosis_confidence"] in {"high", "medium", "low"}
    assert isinstance(ctx.get("headline"), str) and ctx["headline"]
    assert "stress_scorecard_v1.overall_status" in ctx["forbidden_legacy_field_paths"]
    assert "overall_status" not in ctx


def test_ai_commentary_context_unavailable_when_block_unavailable() -> None:
    block = empty_current_portfolio_stress_scorecard_v1("fixture")
    ctx = block["ai_commentary_context"]
    assert ctx["availability"] == "unavailable"
    assert ctx["diagnosis_confidence"] == "unavailable"
    assert ctx["headline"] is None


def test_relatively_resilient_and_less_damaging_scenarios() -> None:
    scenario_results = [
        {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.20},
        {"scenario_id": "rates_shock", "portfolio_pnl_pct": -0.05},
        {"scenario_id": "usd_shock", "portfolio_pnl_pct": 0.02},
        {"scenario_id": "inflation_stagflation", "portfolio_pnl_pct": 0.01},
        {"scenario_id": "credit_shock", "portfolio_pnl_pct": -0.12},
    ]
    stress_results = build_stress_results_v1(
        scenario_results=scenario_results,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    resilient = block["relatively_resilient_scenarios"]
    less = block["less_damaging_scenarios"]
    resilient_ids = {row["scenario_id"] for row in resilient}
    assert resilient_ids == {"usd_shock", "inflation_stagflation"}
    assert all(row["portfolio_pnl_pct"] >= 0 for row in resilient)
    assert all(row["scenario_id"] not in resilient_ids for row in less)
    assert all(row["portfolio_pnl_pct"] > -0.20 for row in less)
    assert len(less) <= 3


def test_diagnosis_confidence_high_when_evidence_clean() -> None:
    scenario_rows = [
        {
            "scenario_id": "inflation_stagflation",
            "portfolio_pnl_pct": -0.10,
            "pnl_by_asset_pct": {"EQ1": -0.07, "EQ2": -0.05, "BOND": 0.025},
            "pnl_by_factor_pct": {"eq": -0.08, "inf": -0.02},
            "top1_rc_asset": "EQ1",
            "top1_rc_pct": 0.6,
            "top3_rc_assets": ["EQ1"],
            "top3_rc_sum_pct": 0.6,
        }
    ]
    stress_results = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    hedge_gap = build_hedge_gap_analysis_v1(
        stress_results_v1=stress_results,
        scenario_results=scenario_rows,
        loss_gate_mode="diagnostic",
    )
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": hedge_gap,
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    block = build_current_portfolio_stress_scorecard_v1(report)
    if block["block_status"] == "ok" and hedge_gap["block_status"] == "ok":
        assert block["stress_diagnosis"]["diagnosis_confidence"] in {"high", "medium"}


def test_pre_stress_confirmation_not_applicable_without_bridges() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    pre = block["pre_stress_confirmation_summary"]
    assert pre["hidden_exposure"]["status"] == "not_applicable"
    assert pre["hidden_exposure"]["reason_en"] == "block_2_4_not_attached"
    assert pre["weakness_map"]["status"] == "not_applicable"
    assert pre["weakness_map"]["reason_en"] == "block_2_6_not_attached"
    assert pre["aggregate_confirmation"]["status"] == "unavailable"


def test_pre_stress_confirmation_copies_hedge_gap_bridges() -> None:
    scenario_rows = [
        {
            "scenario_id": "equity_shock",
            "portfolio_pnl_pct": -0.10,
            "pnl_by_asset_pct": {"SPY": -0.08, "BND": -0.02},
        },
        {
            "scenario_id": "inflation_stagflation",
            "portfolio_pnl_pct": -0.08,
            "pnl_by_asset_pct": {"SPY": -0.05, "BND": 0.01},
        },
    ]
    stress_results = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "scenario_results": scenario_rows,
        "stress_results_v1": stress_results,
        "loss_gate_mode": "diagnostic",
        "stress_conclusions": {},
        "data_trust_summary": {},
    }
    attach_hedge_gap_analysis_v1(report)
    block_2_4 = build_block_2_4_hidden_exposure(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        taxonomy_rows=_taxonomy(),
    )
    block_2_6 = build_block_2_6_portfolio_weakness_map(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        _block_2_4(),
        _block_2_5(),
    )
    assert apply_hidden_exposure_confirmation_bridge(report, block_2_4) is True
    assert apply_weakness_map_confirmation_bridge(report, block_2_6) is True
    portfolio_xray = {
        "block_2_4_hidden_exposure": block_2_4,
        "block_2_6_portfolio_weakness_map": block_2_6,
    }
    block = build_current_portfolio_stress_scorecard_v1(report, portfolio_xray=portfolio_xray)
    pre = block["pre_stress_confirmation_summary"]
    hidden = pre["hidden_exposure"]
    weakness = pre["weakness_map"]
    assert hidden["status"] != "not_applicable"
    assert weakness["status"] != "not_applicable"
    assert len(hidden["confirmation_rows"]) == 6
    assert len(weakness["confirmation_rows"]) == 8
    assert pre["aggregate_confirmation"]["status"] != "unavailable"
    assert "portfolio_xray" in block["source_blocks_used"]


def test_block_status_independent_of_pre_stress_bridges() -> None:
    out = _minimal_run()
    scenario_rows = [
        {
            "scenario_id": "equity_shock",
            "portfolio_pnl_pct": -0.10,
            "pnl_by_asset_pct": {"SPY": -0.08, "BND": -0.02},
        },
    ]
    stress_results = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": stress_results,
        "hedge_gap_analysis_v1": empty_hedge_gap_analysis_v1("fixture"),
        "stress_conclusions": out.get("stress_conclusions") or {},
        "data_trust_summary": out.get("data_trust_summary") or {},
    }
    without = build_current_portfolio_stress_scorecard_v1(report)
    portfolio_xray = {
        "block_2_4_hidden_exposure": build_block_2_4_hidden_exposure(
            _block_2_1(),
            _block_2_2(),
            _block_2_3(),
            taxonomy_rows=_taxonomy(),
        ),
        "block_2_6_portfolio_weakness_map": build_block_2_6_portfolio_weakness_map(
            _block_2_1(),
            _block_2_2(),
            _block_2_3(),
            _block_2_4(),
            _block_2_5(),
        ),
    }
    with_bridges = build_current_portfolio_stress_scorecard_v1(report, portfolio_xray=portfolio_xray)
    assert without["block_status"] == with_bridges["block_status"]


def test_no_forbidden_english_phrases_inside_block() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    found = collect_forbidden_english_phrases(block)
    assert not found, f"Forbidden phrases found: {found}"


def test_no_mandate_pass_fail_language_inside_block() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]

    forbidden_keys = {
        "pass",
        "loss_ok",
        "max_dd_limit",
        "diagnostic_codes",
        "primary_diagnostic_code",
        "fail_reason_code",
        "failed_scenario",
        "failed_test",
        "overall_status",
    }

    def _walk(obj: object) -> list[str]:
        found: list[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in forbidden_keys:
                    found.append(k)
                found.extend(_walk(v))
        elif isinstance(obj, list):
            for item in obj:
                found.extend(_walk(item))
        return found

    found = set(_walk(block))
    assert not found, f"Forbidden mandate keys found in Block 3.4: {sorted(found)}"

