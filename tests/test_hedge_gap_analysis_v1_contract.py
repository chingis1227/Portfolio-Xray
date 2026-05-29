"""Block 3.3 Hedge Gap Analysis — builder contract tests (Session 02+).

Structure, risk-type registry, attach stub, empty fallback, Session 03
per-risk hurt/helped + offset_coverage_ratio, Session 04 summary narratives,
and Session 05 run_stress wiring.
"""
from __future__ import annotations

import inspect

import pytest

from src.stress import run_stress
from src.scenario_library import SCENARIO_LIBRARY_VERSION, SYNTHETIC_SCENARIO_IDS
import copy

from src.block_2_4_hidden_exposure import build_block_2_4_hidden_exposure
from src.block_2_6_portfolio_weakness_map import build_block_2_6_portfolio_weakness_map
from src.hedge_gap_analysis_block import (
    BLOCK_3_3_RISK_SCENARIO_MAP,
    BLOCK_3_3_VERSION,
    RULESET_VERSION,
    _compute_main_gap_score,
    _compute_offset_coverage_ratio,
    _parse_pnl_by_asset_map,
    apply_hidden_exposure_confirmation_bridge,
    apply_weakness_map_confirmation_bridge,
    attach_hedge_gap_analysis_v1,
    build_hedge_gap_analysis_v1,
    empty_hedge_gap_analysis_v1,
)
from test_block_2_4_hidden_exposure import _block_2_1, _block_2_2, _block_2_3, _taxonomy
from test_block_2_6_portfolio_weakness_map import _block_2_4, _block_2_5
from src.stress_results_block import build_stress_results_v1

_EXPECTED_RISK_TYPES = list(BLOCK_3_3_RISK_SCENARIO_MAP.keys())
_EXPECTED_LINKED_SCENARIOS = list(BLOCK_3_3_RISK_SCENARIO_MAP.values())


def _build(**kwargs: object) -> dict:
    defaults: dict = dict(
        stress_results_v1={},
        scenario_results=[],
        loss_gate_mode="diagnostic",
    )
    defaults.update(kwargs)
    return build_hedge_gap_analysis_v1(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Top-level structure (Session 02)
# ---------------------------------------------------------------------------


def test_version_field() -> None:
    out = _build()
    assert out["version"] == BLOCK_3_3_VERSION == "hedge_gap_analysis_v1"


def test_required_top_level_keys() -> None:
    out = _build()
    for key in (
        "version",
        "ruleset_version",
        "block_status",
        "loss_gate_mode",
        "diagnosis_method",
        "scenario_library",
        "scenario_coverage",
        "by_risk_type",
        "summary",
        "n_risk_types",
    ):
        assert key in out, f"Missing top-level key: {key}"


def test_ruleset_version_and_block_status() -> None:
    out = _build()
    assert out["ruleset_version"] == RULESET_VERSION
    assert out["block_status"] == "unavailable"
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.05,
            pnl_by_asset_pct={"A": -0.04, "H": 0.01},
        ),
    ]
    out_partial = _build_with_scenarios(rows)
    assert out_partial["block_status"] == "partial"
    assert out_partial["ruleset_version"] == RULESET_VERSION


def test_diagnosis_method() -> None:
    out = _build()
    assert out["diagnosis_method"] == "contribution_based_offset_coverage_v1"


def test_loss_gate_mode_diagnostic() -> None:
    out = _build(loss_gate_mode="diagnostic")
    assert out["loss_gate_mode"] == "diagnostic"


def test_loss_gate_mode_mandate_fallback() -> None:
    out = _build(loss_gate_mode="mandate")
    assert out["loss_gate_mode"] == "mandate"
    out_unknown = _build(loss_gate_mode="")
    assert out_unknown["loss_gate_mode"] == "mandate"


def test_scenario_library_linkage() -> None:
    out = _build()
    lib = out["scenario_library"]
    assert lib["version"] == SCENARIO_LIBRARY_VERSION
    assert lib["synthetic_ids"] == list(SYNTHETIC_SCENARIO_IDS)


def test_n_risk_types_matches_by_risk_type_length() -> None:
    out = _build()
    assert out["n_risk_types"] == 8
    assert out["n_risk_types"] == len(out["by_risk_type"])


def test_block_3_3_risk_scenario_map_eight_entries() -> None:
    assert len(BLOCK_3_3_RISK_SCENARIO_MAP) == 8
    assert set(BLOCK_3_3_RISK_SCENARIO_MAP.values()).issubset(set(SYNTHETIC_SCENARIO_IDS))
    assert BLOCK_3_3_RISK_SCENARIO_MAP["recession_severe_protection"] == "recession_severe"


def test_by_risk_type_stable_order_and_ids() -> None:
    out = _build()
    rows = out["by_risk_type"]
    assert [r["risk_type"] for r in rows] == _EXPECTED_RISK_TYPES
    assert [r["linked_scenario_id"] for r in rows] == _EXPECTED_LINKED_SCENARIOS


def test_by_risk_type_row_required_keys() -> None:
    out = _build()
    required = (
        "risk_type",
        "protection_type",
        "linked_scenario_id",
        "scenario_id",
        "linked_episode",
        "scenario_type",
        "portfolio_loss_pct",
        "assets_hurt",
        "assets_helped",
        "top3_loss_assets",
        "top3_helped_assets",
        "gross_loss_from_assets_hurt",
        "positive_contribution_from_assets_helped",
        "offset_coverage_ratio",
        "loss_concentration",
        "data_availability",
        "data_availability_reason",
        "protection_status",
        "confirmation_status",
        "confidence",
        "confidence_reason",
        "limitations",
        "diagnosis_summary_en",
        "client_diagnosis_en",
        "next_decision_use",
    )
    for row in out["by_risk_type"]:
        for key in required:
            assert key in row, f"Missing row key {key!r} on {row.get('risk_type')}"


def test_product_aliases_mirror_canonical_keys() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.05,
            pnl_by_asset_pct={"A": -0.04, "H": 0.01},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    assert row["protection_type"] == row["risk_type"]
    assert row["scenario_id"] == row["linked_scenario_id"]


def test_protection_status_taxonomy_on_available_row() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.10,
            pnl_by_asset_pct={"A": -0.08, "H": 0.015},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    assert row["protection_status"] == "weak_protection"
    assert row["confirmation_status"] == "not_applicable"
    assert row["confidence"] in {"high", "medium", "low", "unavailable"}
    assert isinstance(row["limitations"], list)
    assert isinstance(row["client_diagnosis_en"], str)


def test_protection_status_no_protection_when_zero_offset() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.10,
            pnl_by_asset_pct={"A": -0.10},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    assert row["offset_coverage_ratio"] == 0.0
    assert row["protection_status"] == "no_protection"
    assert row["next_decision_use"] == "candidate_hedge_gap_compare"


def test_protection_status_strong_when_high_offset() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.10,
            pnl_by_asset_pct={"A": -0.04, "H": 0.03},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    assert row["offset_coverage_ratio"] == pytest.approx(0.75)
    assert row["protection_status"] == "strong_protection"


def test_summary_product_contract_fields() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.08,
            pnl_by_asset_pct={"A": -0.06, "H": 0.03},
        ),
        _scenario_row(
            "inflation_stagflation",
            portfolio_pnl_pct=-0.12,
            pnl_by_asset_pct={"A": -0.10, "H": 0.01},
        ),
    ]
    out = _build_with_scenarios(rows)
    summary = out["summary"]
    for key in (
        "average_offset_coverage_ratio",
        "protection_profile",
        "client_summary_en",
        "limitations",
        "main_gap_score",
        "selection_reason_code",
        "selection_reason_en",
        "main_hedge_gap_scenario_id",
        "main_hedge_gap_offset_coverage_ratio",
        "main_hedge_gap_portfolio_loss_pct",
        "main_assets_hurt",
        "main_assets_helped",
    ):
        assert key in summary, f"Missing summary key {key!r}"
    assert isinstance(summary["client_summary_en"], str)
    assert summary["main_hedge_gap_scenario_id"] == "inflation_stagflation"
    assert summary["selection_reason_code"] == "weighted_gap_score_v2_loss_scenarios"
    assert isinstance(summary["selection_reason_en"], str)
    assert isinstance(summary["main_gap_score"], (int, float))
    assert summary["main_hedge_gap"]["main_gap_score"] == summary["main_gap_score"]


def test_no_evidence_rows_unavailable() -> None:
    out = _build()
    for row in out["by_risk_type"]:
        assert row["linked_episode"] is None
        assert row["scenario_type"] == "synthetic"
        assert row["data_availability"] == "unavailable"
        assert row["data_availability_reason"] == "scenario_row_missing"
        assert row["offset_coverage_ratio"] is None
        assert row["assets_hurt"] == []
        assert row["assets_helped"] == []


def test_summary_scaffold_keys() -> None:
    out = _build()
    summary = out["summary"]
    for key in (
        "main_hedge_gap",
        "weakest_protection_area",
        "strongest_protection_area",
        "diagnosis_summary_en",
        "data_quality_warnings",
        "average_offset_coverage_ratio",
        "protection_profile",
        "client_summary_en",
        "limitations",
        "main_hedge_gap_scenario_id",
        "main_hedge_gap_offset_coverage_ratio",
        "main_hedge_gap_portfolio_loss_pct",
        "main_assets_hurt",
        "main_assets_helped",
        "main_gap_score",
        "selection_reason_code",
        "selection_reason_en",
    ):
        assert key in summary
    assert summary["main_hedge_gap"] is None
    assert summary["main_gap_score"] is None
    assert summary["selection_reason_code"] is None
    assert summary["selection_reason_en"] is None
    assert summary["diagnosis_summary_en"] is None
    assert isinstance(summary["data_quality_warnings"], list)
    assert len(summary["data_quality_warnings"]) >= 1


def test_rows_exclude_forbidden_mandate_keys() -> None:
    forbidden = {"pass", "loss_ok", "gap_detected", "status", "max_dd_limit"}
    out = _build()
    for row in out["by_risk_type"]:
        assert forbidden.isdisjoint(row.keys())


def test_module_does_not_import_stress() -> None:
    """Block 3.3 builder must stay isolated from src.stress (no circular imports)."""
    from src import hedge_gap_analysis_block as mod

    source = inspect.getsource(mod)
    assert "from src.stress" not in source
    assert "import src.stress" not in source


# ---------------------------------------------------------------------------
# attach stub (Session 02)
# ---------------------------------------------------------------------------


def test_attach_hedge_gap_analysis_v1_writes_block() -> None:
    report: dict = {
        "loss_gate_mode": "diagnostic",
        "scenario_results": [],
        "stress_results_v1": {"version": "stress_results_v1"},
    }
    attach_hedge_gap_analysis_v1(report)
    block = report.get("hedge_gap_analysis_v1")
    assert isinstance(block, dict)
    assert block["version"] == BLOCK_3_3_VERSION
    assert block["n_risk_types"] == 8


# ---------------------------------------------------------------------------
# Empty fallback (Session 02)
# ---------------------------------------------------------------------------


def test_empty_hedge_gap_analysis_v1_top_level_keys() -> None:
    out = empty_hedge_gap_analysis_v1("test_reason")
    for key in (
        "version",
        "ruleset_version",
        "block_status",
        "loss_gate_mode",
        "scenario_library",
        "scenario_coverage",
        "by_risk_type",
        "summary",
        "n_risk_types",
        "error",
    ):
        assert key in out, f"Empty fallback missing: {key}"


def test_empty_hedge_gap_analysis_v1_version() -> None:
    out = empty_hedge_gap_analysis_v1()
    assert out["version"] == BLOCK_3_3_VERSION


def test_empty_hedge_gap_analysis_v1_error_field() -> None:
    out = empty_hedge_gap_analysis_v1("my_reason")
    assert out["error"] == "my_reason"


def test_empty_hedge_gap_analysis_v1_gate_mode() -> None:
    out_diag = empty_hedge_gap_analysis_v1(loss_gate_mode="diagnostic")
    assert out_diag["loss_gate_mode"] == "diagnostic"
    out_man = empty_hedge_gap_analysis_v1(loss_gate_mode="mandate")
    assert out_man["loss_gate_mode"] == "mandate"


def test_empty_hedge_gap_analysis_v1_still_has_eight_rows() -> None:
    out = empty_hedge_gap_analysis_v1()
    assert out["n_risk_types"] == 8
    assert len(out["by_risk_type"]) == 8
    assert out["scenario_library"]["synthetic_ids"] == list(SYNTHETIC_SCENARIO_IDS)


# ---------------------------------------------------------------------------
# Session 03 — per-risk hurt/helped + offset_coverage_ratio
# ---------------------------------------------------------------------------


def _scenario_row(
    scenario_id: str,
    *,
    portfolio_pnl_pct: float,
    pnl_by_asset_pct: dict[str, float],
) -> dict:
    return {
        "scenario_id": scenario_id,
        "portfolio_pnl_pct": portfolio_pnl_pct,
        "pnl_by_asset_pct": pnl_by_asset_pct,
    }


def _build_with_scenarios(scenario_rows: list[dict]) -> dict:
    stress_results_v1 = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    return _build(
        stress_results_v1=stress_results_v1,
        scenario_results=scenario_rows,
    )


def _row_by_risk(out: dict, risk_type: str) -> dict:
    for row in out["by_risk_type"]:
        if row["risk_type"] == risk_type:
            return row
    raise AssertionError(f"Missing risk_type {risk_type!r}")


def test_offset_coverage_ratio_example_from_spec() -> None:
    """hurt gross 12%, helped +2.5% -> ratio ~0.208."""
    rows = [
        _scenario_row(
            "inflation_stagflation",
            portfolio_pnl_pct=-0.10,
            pnl_by_asset_pct={
                "EQ1": -0.07,
                "EQ2": -0.05,
                "BOND": 0.025,
            },
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "stagflation_protection")
    assert row["data_availability"] == "available"
    assert row["gross_loss_from_assets_hurt"] == pytest.approx(0.12)
    assert row["positive_contribution_from_assets_helped"] == pytest.approx(0.025)
    assert row["offset_coverage_ratio"] == pytest.approx(0.025 / 0.12, rel=1e-9)


def test_assets_hurt_sorted_most_negative_first() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.08,
            pnl_by_asset_pct={"A": -0.01, "B": -0.05, "C": -0.03, "H": 0.02},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    assert [a["ticker"] for a in row["assets_hurt"]] == ["B", "C", "A"]
    assert [a["ticker"] for a in row["assets_helped"]] == ["H"]


def test_loss_concentration_top3_share() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.10,
            pnl_by_asset_pct={
                "A": -0.04,
                "B": -0.03,
                "C": -0.02,
                "D": -0.01,
                "H": 0.01,
            },
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    gross = 0.04 + 0.03 + 0.02 + 0.01
    top3 = 0.04 + 0.03 + 0.02
    assert row["loss_concentration"]["top3_share_of_gross_loss"] == pytest.approx(
        top3 / gross, rel=1e-9
    )


def test_no_helped_assets_ratio_zero() -> None:
    rows = [
        _scenario_row(
            "credit_shock",
            portfolio_pnl_pct=-0.06,
            pnl_by_asset_pct={"X": -0.04, "Y": -0.02},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "credit_shock_protection")
    assert row["assets_helped"] == []
    assert row["positive_contribution_from_assets_helped"] == 0.0
    assert row["offset_coverage_ratio"] == 0.0


def test_no_assets_hurt_insufficient_data() -> None:
    rows = [
        _scenario_row(
            "usd_shock",
            portfolio_pnl_pct=0.02,
            pnl_by_asset_pct={"GOLD": 0.02, "CASH": 0.01},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "usd_spike_protection")
    assert row["data_availability"] == "insufficient_data"
    assert row["data_availability_reason"] == "no_assets_hurt"
    assert row["offset_coverage_ratio"] is None


def test_pnl_map_missing_unavailable() -> None:
    rows = [
        {
            "scenario_id": "rates_shock",
            "portfolio_pnl_pct": -0.05,
        },
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "rates_up_shock_protection")
    assert row["data_availability"] == "unavailable"
    assert row["data_availability_reason"] == "pnl_by_asset_unavailable"


def test_prefers_stress_results_v1_pnl_over_scenario_results() -> None:
    scenario_rows = [
        _scenario_row(
            "liquidity_shock",
            portfolio_pnl_pct=-0.05,
            pnl_by_asset_pct={"OLD": -0.05},
        ),
    ]
    stress_results_v1 = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    for syn in stress_results_v1["synthetic_scenarios"]:
        if syn["scenario_id"] == "liquidity_shock":
            syn["loss_contribution"]["pnl_by_asset_pct"] = {
                "NEW_NEG": -0.03,
                "NEW_POS": 0.01,
            }
    out = _build(stress_results_v1=stress_results_v1, scenario_results=scenario_rows)
    row = _row_by_risk(out, "liquidity_shock_protection")
    assert row["data_availability"] == "available"
    assert [a["ticker"] for a in row["assets_hurt"]] == ["NEW_NEG"]
    assert [a["ticker"] for a in row["assets_helped"]] == ["NEW_POS"]


def test_all_eight_mapped_scenarios_available_when_evidence_complete() -> None:
    scenario_rows = [
        _scenario_row(
            sid,
            portfolio_pnl_pct=-0.03,
            pnl_by_asset_pct={"L": -0.02, "H": 0.005},
        )
        for sid in _EXPECTED_LINKED_SCENARIOS
    ]
    out = _build_with_scenarios(scenario_rows)
    for risk_type, linked_id in BLOCK_3_3_RISK_SCENARIO_MAP.items():
        row = _row_by_risk(out, risk_type)
        assert row["linked_scenario_id"] == linked_id
        assert row["data_availability"] == "available"
        assert row["offset_coverage_ratio"] is not None


# ---------------------------------------------------------------------------
# Session 04 — summary + diagnosis_summary_en
# ---------------------------------------------------------------------------


def test_recession_severe_protection_row_when_evidence_present() -> None:
    rows = [
        _scenario_row(
            "recession_severe",
            portfolio_pnl_pct=-0.22,
            pnl_by_asset_pct={"QQQ": -0.12, "TLT": 0.04, "BND": 0.02},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "recession_severe_protection")
    assert row["linked_scenario_id"] == "recession_severe"
    assert row["data_availability"] == "available"
    assert row["offset_coverage_ratio"] == pytest.approx((0.04 + 0.02) / 0.12)
    assert [a["ticker"] for a in row["assets_hurt"]] == ["QQQ"]
    assert {a["ticker"] for a in row["assets_helped"]} == {"TLT", "BND"}


def test_main_hedge_gap_can_select_recession_severe_when_weakest_offset() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.08,
            pnl_by_asset_pct={"A": -0.06, "H": 0.03},
        ),
        _scenario_row(
            "recession_severe",
            portfolio_pnl_pct=-0.22,
            pnl_by_asset_pct={"A": -0.20, "H": 0.01},
        ),
    ]
    out = _build_with_scenarios(rows)
    main = out["summary"]["main_hedge_gap"]
    assert main is not None
    assert main["risk_type"] == "recession_severe_protection"
    assert main["linked_scenario_id"] == "recession_severe"
    assert out["summary"]["weakest_protection_area"] == "recession_severe_protection"


def test_main_hedge_gap_selects_minimum_offset_ratio() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.08,
            pnl_by_asset_pct={"A": -0.06, "H": 0.03},
        ),
        _scenario_row(
            "inflation_stagflation",
            portfolio_pnl_pct=-0.12,
            pnl_by_asset_pct={"A": -0.10, "H": 0.01},
        ),
    ]
    out = _build_with_scenarios(rows)
    main = out["summary"]["main_hedge_gap"]
    assert main is not None
    assert main["risk_type"] == "stagflation_protection"
    assert main["linked_scenario_id"] == "inflation_stagflation"
    assert main["offset_coverage_ratio"] == pytest.approx(0.01 / 0.10)
    assert out["summary"]["weakest_protection_area"] == "stagflation_protection"


def test_main_hedge_gap_tie_break_more_negative_portfolio_loss() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.05,
            pnl_by_asset_pct={"A": -0.04, "H": 0.01},
        ),
        _scenario_row(
            "credit_shock",
            portfolio_pnl_pct=-0.15,
            pnl_by_asset_pct={"B": -0.12, "H": 0.03},
        ),
    ]
    out = _build_with_scenarios(rows)
    assert out["summary"]["weakest_protection_area"] == "credit_shock_protection"


def test_main_gap_score_material_loss_beats_tiny_zero_offset() -> None:
    """Weighted score must not pick a negligible-loss zero-offset over a material weak offset."""
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.002,
            pnl_by_asset_pct={"A": -0.002},
        ),
        _scenario_row(
            "credit_shock",
            portfolio_pnl_pct=-0.15,
            pnl_by_asset_pct={"B": -0.12, "H": 0.03},
        ),
    ]
    out = _build_with_scenarios(rows)
    summary = out["summary"]
    assert summary["weakest_protection_area"] == "credit_shock_protection"
    assert summary["selection_reason_code"] == "weighted_gap_score_v2_loss_scenarios"
    main = summary["main_hedge_gap"]
    assert main is not None
    assert main["risk_type"] == "credit_shock_protection"
    assert summary["main_gap_score"] > 0.01


def test_compute_main_gap_score_formula() -> None:
    row = {
        "offset_coverage_ratio": 0.10,
        "portfolio_loss_pct": -0.12,
        "loss_concentration": {"top3_share_of_gross_loss": 1.0},
    }
    score = _compute_main_gap_score(row)
    assert score == pytest.approx(0.9 * 0.12 * 1.25, rel=1e-9)


def test_hidden_exposure_confirmation_bridge_updates_rows_and_weak_hedge() -> None:
    scenario_rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.10,
            pnl_by_asset_pct={"SPY": -0.08, "BND": -0.02},
        ),
        _scenario_row(
            "inflation_stagflation",
            portfolio_pnl_pct=-0.08,
            pnl_by_asset_pct={"SPY": -0.05, "BND": 0.01},
        ),
    ]
    stress_results_v1 = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "scenario_results": scenario_rows,
        "stress_results_v1": stress_results_v1,
        "loss_gate_mode": "diagnostic",
    }
    attach_hedge_gap_analysis_v1(report)
    block_2_4 = build_block_2_4_hidden_exposure(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        taxonomy_rows=_taxonomy(),
    )
    assert apply_hidden_exposure_confirmation_bridge(report, block_2_4) is True
    hedge_gap = report["hedge_gap_analysis_v1"]
    confirmations = hedge_gap.get("hidden_exposure_confirmation")
    assert isinstance(confirmations, list)
    assert len(confirmations) == 6
    weak_bridge = next(row for row in confirmations if row["alert_id"] == "weak_hedge_behavior")
    assert weak_bridge["confirmation_status"] in {
        "confirmed",
        "partially_confirmed",
        "preliminary",
        "not_applicable",
    }
    equity_row = _row_by_risk(hedge_gap, "equity_crash_protection")
    assert equity_row["confirmation_status"] in {
        "confirmed",
        "partially_confirmed",
        "not_confirmed",
        "preliminary",
        "not_applicable",
    }
    assert equity_row["confirmation_status"] != "not_applicable"
    weak_alert = block_2_4["alerts"]["weak_hedge_behavior"]
    assert "hedge_gap_bridge" in weak_alert
    assert weak_alert["confirmation_status"] == weak_bridge["confirmation_status"]
    assert block_2_4["diagnostics_meta"]["hedge_gap_bridge_wire_time"] is True
    limitations = hedge_gap["summary"].get("limitations") or []
    assert "pre_stress_confirmation_pending_block_2_4_2_6" not in limitations
    assert "block_2_6_weakness_map_confirmation_pending" in limitations


def _block_2_6_high_equity() -> dict:
    b21 = _block_2_1()
    b21["capital_allocation_breakdown"]["by_asset_class"] = [{"name": "equity", "weight_pct": 85.0}]
    b22 = _block_2_2()
    b22["benchmark_dependence"] = {"downside_beta": 1.35, "beta_portfolio": 1.25}
    return build_block_2_6_portfolio_weakness_map(b21, b22, _block_2_3(), _block_2_4(), _block_2_5())


def test_weakness_map_confirmation_bridge_updates_rows() -> None:
    scenario_rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.10,
            pnl_by_asset_pct={"SPY": -0.08, "BND": -0.01},
        ),
    ]
    stress_results_v1 = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "scenario_results": scenario_rows,
        "stress_results_v1": stress_results_v1,
        "loss_gate_mode": "diagnostic",
    }
    attach_hedge_gap_analysis_v1(report)
    block_2_6 = _block_2_6_high_equity()
    before_2_6 = copy.deepcopy(block_2_6)
    assert apply_weakness_map_confirmation_bridge(report, block_2_6) is True
    assert block_2_6 == before_2_6

    hedge_gap = report["hedge_gap_analysis_v1"]
    confirmations = hedge_gap.get("weakness_map_confirmation")
    assert isinstance(confirmations, list)
    assert len(confirmations) == 8
    equity_conf = next(row for row in confirmations if row["risk_type"] == "equity_shock")
    assert equity_conf["linked_protection_type"] == "equity_crash_protection"
    assert equity_conf["weakness_severity"] == "High"
    assert equity_conf["confirmation_status"] in {
        "confirmed",
        "partially_confirmed",
        "preliminary",
        "not_confirmed",
    }
    equity_row = _row_by_risk(hedge_gap, "equity_crash_protection")
    assert equity_row["confirmation_status"] != "not_applicable"
    meta = hedge_gap.get("bridge_meta") or {}
    assert meta.get("block_2_6_portfolio_weakness_map") is True
    limitations = hedge_gap["summary"].get("limitations") or []
    assert "block_2_6_weakness_map_confirmation_pending" not in limitations
    assert "block_2_4_hidden_exposure_confirmation_pending" in limitations


def test_attach_with_both_bridges_clears_pre_stress_limitations() -> None:
    scenario_rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.10,
            pnl_by_asset_pct={"SPY": -0.08, "BND": -0.01},
        ),
    ]
    stress_results_v1 = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "scenario_results": scenario_rows,
        "stress_results_v1": stress_results_v1,
        "loss_gate_mode": "diagnostic",
    }
    block_2_4 = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())
    block_2_6 = _block_2_6_high_equity()
    attach_hedge_gap_analysis_v1(
        report,
        block_2_4_hidden_exposure=block_2_4,
        block_2_6_portfolio_weakness_map=block_2_6,
    )
    hedge_gap = report["hedge_gap_analysis_v1"]
    assert isinstance(hedge_gap.get("hidden_exposure_confirmation"), list)
    assert isinstance(hedge_gap.get("weakness_map_confirmation"), list)
    limitations = hedge_gap["summary"].get("limitations") or []
    assert "pre_stress_confirmation_pending_block_2_4_2_6" not in limitations
    assert "block_2_6_weakness_map_confirmation_pending" not in limitations
    assert "block_2_4_hidden_exposure_confirmation_pending" not in limitations


def test_attach_with_block_2_4_applies_bridge() -> None:
    scenario_rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.08,
            pnl_by_asset_pct={"A": -0.06, "H": 0.01},
        ),
    ]
    stress_results_v1 = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "scenario_results": scenario_rows,
        "stress_results_v1": stress_results_v1,
        "loss_gate_mode": "diagnostic",
    }
    block_2_4 = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())
    attach_hedge_gap_analysis_v1(report, block_2_4_hidden_exposure=block_2_4)
    assert isinstance(report["hedge_gap_analysis_v1"].get("hidden_exposure_confirmation"), list)


def test_main_gap_selection_reason_fields_present() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.08,
            pnl_by_asset_pct={"A": -0.06, "H": 0.03},
        ),
    ]
    out = _build_with_scenarios(rows)
    summary = out["summary"]
    assert summary["selection_reason_code"] == "weighted_gap_score_v2_loss_scenarios"
    reason = summary["selection_reason_en"]
    assert isinstance(reason, str)
    assert "weighted gap score" in reason.lower()
    assert "equity crash" in reason.lower()
    diag = summary["diagnosis_summary_en"]
    assert isinstance(diag, str)
    assert reason in diag


def test_strongest_protection_area_requires_two_ratios() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.08,
            pnl_by_asset_pct={"A": -0.06, "H": 0.02},
        ),
    ]
    out_one = _build_with_scenarios(rows)
    assert out_one["summary"]["strongest_protection_area"] is None

    rows.append(
        _scenario_row(
            "rates_shock",
            portfolio_pnl_pct=-0.06,
            pnl_by_asset_pct={"B": -0.04, "H": 0.03},
        ),
    )
    out_two = _build_with_scenarios(rows)
    assert out_two["summary"]["strongest_protection_area"] == "rates_up_shock_protection"


def test_per_risk_diagnosis_summary_en_when_available() -> None:
    rows = [
        _scenario_row(
            "inflation_stagflation",
            portfolio_pnl_pct=-0.10,
            pnl_by_asset_pct={"EQ1": -0.07, "EQ2": -0.05, "BOND": 0.025},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "stagflation_protection")
    summary = row["diagnosis_summary_en"]
    assert isinstance(summary, str)
    assert "stagflation" in summary.lower()
    assert "20.8%" in summary or "20.7%" in summary
    assert "BOND" in summary


def test_portfolio_diagnosis_summary_en_when_main_gap_exists() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.08,
            pnl_by_asset_pct={"A": -0.06, "H": 0.03},
        ),
        _scenario_row(
            "inflation_stagflation",
            portfolio_pnl_pct=-0.12,
            pnl_by_asset_pct={"A": -0.10, "H": 0.01},
        ),
    ]
    out = _build_with_scenarios(rows)
    summary = out["summary"]["diagnosis_summary_en"]
    assert isinstance(summary, str)
    assert "main hedge gap" in summary.lower()
    assert "stagflation" in summary.lower()


def test_data_quality_warnings_when_rows_unavailable() -> None:
    out = _build()
    warnings = out["summary"]["data_quality_warnings"]
    assert "8_risk_type_rows_scenario_row_missing" in warnings
    assert "all_risk_type_rows_unavailable" in warnings


def test_data_quality_warnings_partial_evidence() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.05,
            pnl_by_asset_pct={"A": -0.04, "H": 0.01},
        ),
    ]
    out = _build_with_scenarios(rows)
    warnings = out["summary"]["data_quality_warnings"]
    assert any(
        token in w
        for w in warnings
        for token in ("scenario_row_missing", "pnl_by_asset_unavailable")
    )
    assert "no_offset_coverage_ratios_computed" not in warnings


# ---------------------------------------------------------------------------
# Session 05 — run_stress wiring
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


def test_run_stress_includes_hedge_gap_analysis_v1() -> None:
    out = _minimal_run_stress()
    block = out.get("hedge_gap_analysis_v1")
    assert isinstance(block, dict)
    assert block.get("version") == BLOCK_3_3_VERSION
    assert block.get("loss_gate_mode") == "diagnostic"
    assert block.get("n_risk_types") == 8
    assert len(block.get("by_risk_type") or []) == 8


def test_run_stress_hedge_gap_reads_stress_results_v1_evidence() -> None:
    out = _minimal_run_stress()
    block = out.get("hedge_gap_analysis_v1") or {}
    stress_v1 = out.get("stress_results_v1") or {}
    available_rows = [
        row for row in block.get("by_risk_type") or [] if row.get("data_availability") == "available"
    ]
    assert available_rows, "Expected at least one available hedge-gap row from synthetic stress"
    for row in available_rows:
        scenario_id = row.get("linked_scenario_id")
        syn = next(
            (s for s in stress_v1.get("synthetic_scenarios") or [] if s.get("scenario_id") == scenario_id),
            None,
        )
        assert isinstance(syn, dict)
        assert row.get("portfolio_loss_pct") == syn.get("portfolio_loss_pct")


def test_run_stress_hedge_gap_legacy_block_still_present() -> None:
    out = _minimal_run_stress()
    assert isinstance(out.get("hedge_gap_analysis"), dict)
    assert isinstance(out.get("hedge_gap_analysis_v1"), dict)


def test_run_stress_empty_report_includes_hedge_gap_analysis_v1() -> None:
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
    block = out.get("hedge_gap_analysis_v1")
    assert isinstance(block, dict)
    assert block.get("version") == BLOCK_3_3_VERSION
    assert block.get("n_risk_types") == 8
    assert block["scenario_library"]["synthetic_ids"] == list(SYNTHETIC_SCENARIO_IDS)
    assert block["scenario_library"]["version"] == SCENARIO_LIBRARY_VERSION


# ---------------------------------------------------------------------------
# Session 03 — calculation hardening
# ---------------------------------------------------------------------------


def test_compute_offset_coverage_ratio_safe_math() -> None:
    assert _compute_offset_coverage_ratio(0.12, 0.025) == pytest.approx(0.025 / 0.12)
    assert _compute_offset_coverage_ratio(0.12, 0.0) == 0.0
    assert _compute_offset_coverage_ratio(0.0, 0.05) is None
    assert _compute_offset_coverage_ratio(-0.01, 0.05) is None
    assert _compute_offset_coverage_ratio(0.12, float("nan")) is None
    assert _compute_offset_coverage_ratio(float("inf"), 0.05) is None


def test_parse_pnl_by_asset_map_drops_non_finite_and_blank_tickers() -> None:
    assert _parse_pnl_by_asset_map(None) is None
    assert _parse_pnl_by_asset_map({}) is None
    parsed = _parse_pnl_by_asset_map(
        {
            "  AAA  ": -0.02,
            "BBB": float("nan"),
            "CCC": float("inf"),
            "": 0.01,
            "DDD": "bad",
        }
    )
    assert parsed == {"AAA": -0.02}


def test_zero_pnl_tickers_excluded_from_hurt_and_helped() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.05,
            pnl_by_asset_pct={"HURT": -0.04, "FLAT": 0.0, "HELP": 0.01},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    assert [a["ticker"] for a in row["assets_hurt"]] == ["HURT"]
    assert [a["ticker"] for a in row["assets_helped"]] == ["HELP"]
    assert row["gross_loss_from_assets_hurt"] == pytest.approx(0.04)


def test_hurt_sort_tie_breaks_by_ticker_ascending() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.06,
            pnl_by_asset_pct={"Z": -0.02, "A": -0.02, "M": -0.02, "H": 0.01},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    assert [a["ticker"] for a in row["assets_hurt"]] == ["A", "M", "Z"]


def test_gross_loss_equals_sum_abs_hurt_contributions() -> None:
    rows = [
        _scenario_row(
            "credit_shock",
            portfolio_pnl_pct=-0.08,
            pnl_by_asset_pct={"X": -0.05, "Y": -0.02, "Z": -0.01, "H": 0.03},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "credit_shock_protection")
    expected_gross = sum(abs(a["pnl_pct"]) for a in row["assets_hurt"])
    assert row["gross_loss_from_assets_hurt"] == pytest.approx(expected_gross)
    assert row["positive_contribution_from_assets_helped"] == pytest.approx(0.03)


def test_positive_portfolio_loss_not_needed_or_no_loss() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=0.03,
            pnl_by_asset_pct={"A": 0.02, "B": 0.01},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    assert row["data_availability"] == "insufficient_data"
    assert row["protection_status"] == "not_needed_or_no_loss"


def test_only_zero_pnl_map_is_insufficient_no_hurt() -> None:
    rows = [
        _scenario_row(
            "rates_shock",
            portfolio_pnl_pct=-0.01,
            pnl_by_asset_pct={"A": 0.0, "B": 0.0},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "rates_up_shock_protection")
    assert row["data_availability_reason"] == "no_assets_hurt"
    assert row["offset_coverage_ratio"] is None


def test_offset_ratio_can_exceed_one_when_helped_exceeds_gross_hurt() -> None:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=-0.02,
            pnl_by_asset_pct={"A": -0.01, "H1": 0.02, "H2": 0.02},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    assert row["offset_coverage_ratio"] == pytest.approx(4.0)
    assert row["protection_status"] == "strong_protection"


def test_pnl_map_all_invalid_values_unavailable() -> None:
    rows = [
        _scenario_row(
            "liquidity_shock",
            portfolio_pnl_pct=-0.05,
            pnl_by_asset_pct={"A": float("nan"), "B": float("inf")},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "liquidity_shock_protection")
    assert row["data_availability"] == "unavailable"
    assert row["data_availability_reason"] == "pnl_by_asset_unavailable"


@pytest.mark.parametrize(
    ("ratio", "loss", "expected_status"),
    [
        (0.65, -0.10, "strong_protection"),
        (0.40, -0.10, "partial_protection"),
        (0.10, -0.10, "weak_protection"),
        (0.0, -0.10, "no_protection"),
    ],
)
def test_protection_status_thresholds(
    ratio: float,
    loss: float,
    expected_status: str,
) -> None:
    gross = 0.10
    helped = ratio * gross
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=loss,
            pnl_by_asset_pct={"A": -gross, "H": helped},
        ),
    ]
    out = _build_with_scenarios(rows)
    row = _row_by_risk(out, "equity_crash_protection")
    assert row["protection_status"] == expected_status
