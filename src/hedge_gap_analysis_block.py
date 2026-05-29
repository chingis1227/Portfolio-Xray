"""Block 3.3 Hedge Gap Analysis builder — hedge_gap_analysis_v1.

Builds the product-facing Block 3.3 layer from stress evidence already on
``stress_report.json`` (Block 3.1 ``scenario_results[]``, Block 3.2
``stress_results_v1``). No second stress engine and no taxonomy hedge labels.

This module must not import ``src.stress`` (mirror Block 3.2 isolation).

Session 02 (scaffold): registry, eight unavailable placeholder rows, attach stub.
Session 03: per-risk hurt/helped extraction and offset_coverage_ratio.
Session 04: summary + diagnosis_summary_en templates (implemented).
Session 05: attach_hedge_gap_analysis_v1 wired from run_stress, _empty_report, run_report, run_optimization.
Institutional upgrade Session 02: product contract v1.1 (aliases, protection_status, block_status).
Session 03: calculation hardening (finite PnL filter, safe ratio, deterministic splits).
Session 04: main hedge gap selection v2 (weighted main_gap_score, selection reason fields).
Session 05: Block 2.4 bridge (hidden_exposure_confirmation, weak_hedge enrichment).
Session 06: Block 2.6 bridge (weakness_map_confirmation; optional attach input).
"""
from __future__ import annotations

import math
from typing import Any

from src.scenario_library import SCENARIO_LIBRARY_VERSION, SYNTHETIC_SCENARIO_IDS

BLOCK_3_3_VERSION = "hedge_gap_analysis_v1"
RULESET_VERSION = "hedge_gap_rules_v1_2"

# Main-gap scoring (Session 04): higher score = worse material hedge gap.
_MAIN_GAP_CONCENTRATION_BOOST = 0.25

# Block 2.4 / 2.6 bridges: align pre-stress hypotheses with stress offset evidence.
_OFFSET_COVERAGE_WEAK_THRESHOLD = 0.25
_ALERT_MATERIAL_SCORE = 40
_WEAKNESS_MATERIAL_SCORE = 40

BLOCK_2_4_ALERT_RISK_TYPES: dict[str, tuple[str, ...]] = {
    "hidden_equity_beta": ("equity_crash_protection", "recession_severe_protection"),
    "duration_concentration": (
        "rates_up_shock_protection",
        "stagflation_protection",
        "commodity_inflation_shock_protection",
    ),
    "credit_liquidity_risk": ("credit_shock_protection", "liquidity_shock_protection"),
    "correlation_concentration": (),
    "weak_hedge_behavior": (),
    "tail_risk": (
        "recession_severe_protection",
        "equity_crash_protection",
        "liquidity_shock_protection",
    ),
}

_ROW_CONFIRMATION_PRIORITY: dict[str, int] = {
    "confirmed": 4,
    "partially_confirmed": 3,
    "not_confirmed": 2,
    "preliminary": 1,
    "not_applicable": 0,
    "unavailable": -1,
}
_DIAGNOSIS_METHOD = "contribution_based_offset_coverage_v1"

_LOSS_GATE_MODE_DIAGNOSTIC = "diagnostic"
_LOSS_GATE_MODE_MANDATE = "mandate"

# Frozen v1 product map — eight protection areas (seven fixed synthetics + recession_severe).
BLOCK_3_3_RISK_SCENARIO_MAP: dict[str, str] = {
    "equity_crash_protection": "equity_shock",
    "rates_up_shock_protection": "rates_shock",
    "stagflation_protection": "inflation_stagflation",
    "liquidity_shock_protection": "liquidity_shock",
    "usd_spike_protection": "usd_shock",
    "credit_shock_protection": "credit_shock",
    "commodity_inflation_shock_protection": "commodity_shock",
    "recession_severe_protection": "recession_severe",
}

_SCENARIO_ID_TO_PROTECTION_RISK: dict[str, str] = {
    scenario_id: risk_type for risk_type, scenario_id in BLOCK_3_3_RISK_SCENARIO_MAP.items()
}

_RISK_TYPE_LABEL_EN: dict[str, str] = {
    "equity_crash_protection": "equity crash",
    "rates_up_shock_protection": "rates-up shock",
    "stagflation_protection": "stagflation",
    "liquidity_shock_protection": "liquidity shock",
    "usd_spike_protection": "USD spike",
    "credit_shock_protection": "credit shock",
    "commodity_inflation_shock_protection": "commodity inflation shock",
    "recession_severe_protection": "severe recession",
}

_SCENARIO_LABEL_EN: dict[str, str] = {
    "equity_shock": "equity shock",
    "rates_shock": "rates shock",
    "inflation_stagflation": "inflation/stagflation",
    "liquidity_shock": "liquidity shock",
    "usd_shock": "USD shock",
    "credit_shock": "credit shock",
    "commodity_shock": "commodity shock",
    "recession_severe": "severe recession",
}


def build_hedge_gap_analysis_v1(
    *,
    stress_results_v1: dict[str, Any],
    scenario_results: list[dict[str, Any]],
    loss_gate_mode: str,
) -> dict[str, Any]:
    """Build the Block 3.3 product layer from Block 3.1/3.2 evidence dicts."""
    gate_mode = _normalize_gate_mode(loss_gate_mode)
    scenario_by_id = _index_scenario_results(scenario_results)
    synthetic_by_id = _index_stress_results_v1_synthetics(stress_results_v1)

    by_risk_type = [
        _build_risk_row(
            risk_type=risk_type,
            linked_scenario_id=linked_scenario_id,
            scenario_evidence=scenario_by_id.get(linked_scenario_id),
            stress_row=synthetic_by_id.get(linked_scenario_id),
        )
        for risk_type, linked_scenario_id in BLOCK_3_3_RISK_SCENARIO_MAP.items()
    ]
    for row in by_risk_type:
        row["diagnosis_summary_en"] = _format_risk_diagnosis_summary_en(row)
        _apply_product_contract_fields(row)
    summary = _build_summary(by_risk_type)
    block_status = _derive_block_status(by_risk_type)
    return {
        "version": BLOCK_3_3_VERSION,
        "ruleset_version": RULESET_VERSION,
        "block_status": block_status,
        "loss_gate_mode": gate_mode,
        "diagnosis_method": _DIAGNOSIS_METHOD,
        "scenario_library": {
            "version": SCENARIO_LIBRARY_VERSION,
            "synthetic_ids": list(SYNTHETIC_SCENARIO_IDS),
        },
        "scenario_coverage": _scenario_coverage(by_risk_type),
        "by_risk_type": by_risk_type,
        "summary": summary,
        "n_risk_types": len(by_risk_type),
    }


def attach_hedge_gap_analysis_v1(
    stress_report: dict[str, Any],
    *,
    block_2_4_hidden_exposure: dict[str, Any] | None = None,
    block_2_6_portfolio_weakness_map: dict[str, Any] | None = None,
) -> None:
    """Rebuild ``hedge_gap_analysis_v1`` on *stress_report* from current evidence (in-place).

    When *block_2_4_hidden_exposure* and/or *block_2_6_portfolio_weakness_map* are provided
    (after Portfolio X-Ray), apply confirmation bridges without importing Block 2.4/2.6 modules.
    """
    stress_results_v1 = stress_report.get("stress_results_v1")
    if not isinstance(stress_results_v1, dict):
        stress_results_v1 = {}
    stress_report["hedge_gap_analysis_v1"] = build_hedge_gap_analysis_v1(
        stress_results_v1=stress_results_v1,
        scenario_results=list(stress_report.get("scenario_results") or []),
        loss_gate_mode=str(stress_report.get("loss_gate_mode") or _LOSS_GATE_MODE_MANDATE),
    )
    if isinstance(block_2_4_hidden_exposure, dict):
        apply_hidden_exposure_confirmation_bridge(
            stress_report,
            block_2_4_hidden_exposure,
        )
    if isinstance(block_2_6_portfolio_weakness_map, dict):
        apply_weakness_map_confirmation_bridge(
            stress_report,
            block_2_6_portfolio_weakness_map,
        )


def apply_hidden_exposure_confirmation_bridge(
    stress_report: dict[str, Any],
    block_2_4_hidden_exposure: dict[str, Any],
) -> bool:
    """Attach ``hidden_exposure_confirmation`` to hedge_gap v1 and update row statuses."""
    hedge_gap = stress_report.get("hedge_gap_analysis_v1")
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != BLOCK_3_3_VERSION:
        return False
    alerts = block_2_4_hidden_exposure.get("alerts")
    if not isinstance(alerts, dict):
        return False

    by_risk = hedge_gap.get("by_risk_type")
    if not isinstance(by_risk, list):
        return False
    rows_by_type = {
        str(row.get("risk_type")): row
        for row in by_risk
        if isinstance(row, dict) and row.get("risk_type")
    }
    summary = hedge_gap.get("summary") if isinstance(hedge_gap.get("summary"), dict) else {}
    main_gap = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else None

    confirmations: list[dict[str, Any]] = []
    row_status_accum: dict[str, list[str]] = {key: [] for key in rows_by_type}

    for alert_id, linked_types in BLOCK_2_4_ALERT_RISK_TYPES.items():
        alert = alerts.get(alert_id)
        if not isinstance(alert, dict):
            continue
        risk_types = _linked_risk_types_for_alert(
            alert_id=alert_id,
            linked_types=linked_types,
            rows_by_type=rows_by_type,
            main_gap=main_gap,
        )
        risk_confirmations: list[dict[str, Any]] = []
        for risk_type in risk_types:
            row = rows_by_type.get(risk_type)
            if not isinstance(row, dict):
                continue
            status, reason_code = _confirm_row_against_block_2_4_alert(row, alert)
            risk_confirmations.append(
                {
                    "risk_type": risk_type,
                    "linked_scenario_id": row.get("linked_scenario_id"),
                    "confirmation_status": status,
                    "confirmation_reason_code": reason_code,
                    "protection_status": row.get("protection_status"),
                    "offset_coverage_ratio": row.get("offset_coverage_ratio"),
                    "portfolio_loss_pct": row.get("portfolio_loss_pct"),
                }
            )
            row_status_accum.setdefault(risk_type, []).append(status)

        alert_confirmation = _aggregate_bridge_confirmation(
            [str(item["confirmation_status"]) for item in risk_confirmations]
        )
        confirmations.append(
            {
                "alert_id": alert_id,
                "alert_status": alert.get("status"),
                "alert_score": alert.get("score"),
                "confirmation_status": alert_confirmation,
                "confirmation_reason_code": _bridge_alert_reason_code(
                    alert_id=alert_id,
                    alert=alert,
                    alert_confirmation=alert_confirmation,
                ),
                "confirmation_reason_en": _format_bridge_confirmation_reason_en(
                    alert_id=alert_id,
                    alert=alert,
                    alert_confirmation=alert_confirmation,
                    risk_confirmations=risk_confirmations,
                ),
                "linked_risk_types": risk_types,
                "linked_scenario_ids": [
                    str(item["linked_scenario_id"])
                    for item in risk_confirmations
                    if item.get("linked_scenario_id")
                ],
                "risk_type_confirmations": risk_confirmations,
            }
        )

    hedge_gap["hidden_exposure_confirmation"] = confirmations
    hedge_gap["bridge_meta"] = {
        "block_2_4_hidden_exposure": True,
        "ruleset": RULESET_VERSION,
        "n_alerts_linked": len(confirmations),
    }
    _apply_row_confirmation_statuses(rows_by_type, row_status_accum)
    _refresh_summary_after_bridge(hedge_gap=hedge_gap, by_risk_type=by_risk)
    enrich_block_2_4_weak_hedge_from_hedge_gap(block_2_4_hidden_exposure, hedge_gap)
    return True


def apply_weakness_map_confirmation_bridge(
    stress_report: dict[str, Any],
    block_2_6_portfolio_weakness_map: dict[str, Any],
) -> bool:
    """Attach ``weakness_map_confirmation`` to hedge_gap v1 (read-only on Block 2.6)."""
    hedge_gap = stress_report.get("hedge_gap_analysis_v1")
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != BLOCK_3_3_VERSION:
        return False
    weakness_rows = block_2_6_portfolio_weakness_map.get("risk_types")
    if not isinstance(weakness_rows, list):
        return False

    by_risk = hedge_gap.get("by_risk_type")
    if not isinstance(by_risk, list):
        return False
    rows_by_type = {
        str(row.get("risk_type")): row
        for row in by_risk
        if isinstance(row, dict) and row.get("risk_type")
    }

    confirmations: list[dict[str, Any]] = []
    row_status_accum: dict[str, list[str]] = {}
    for protection_type, row in rows_by_type.items():
        existing = row.get("confirmation_status")
        if isinstance(existing, str) and existing:
            row_status_accum.setdefault(protection_type, []).append(existing)

    for weakness in weakness_rows:
        if not isinstance(weakness, dict):
            continue
        scenario_id = str(weakness.get("risk_type") or "")
        protection_type = _SCENARIO_ID_TO_PROTECTION_RISK.get(scenario_id)
        if not protection_type:
            continue
        hedge_row = rows_by_type.get(protection_type)
        status, _ = _confirm_row_against_block_2_6_weakness(
            hedge_row if isinstance(hedge_row, dict) else {},
            weakness,
        )
        confirmations.append(
            {
                "risk_type": scenario_id,
                "linked_protection_type": protection_type,
                "linked_scenario_id": scenario_id,
                "weakness_severity": weakness.get("severity"),
                "weakness_score_0_100": weakness.get("score_0_100"),
                "weakness_confidence": weakness.get("confidence"),
                "confirmation_status": status,
                "confirmation_reason_code": _weakness_bridge_reason_code(
                    scenario_id=scenario_id,
                    weakness=weakness,
                    confirmation_status=status,
                ),
                "confirmation_reason_en": _format_weakness_bridge_reason_en(
                    scenario_id=scenario_id,
                    weakness=weakness,
                    confirmation_status=status,
                    hedge_row=hedge_row if isinstance(hedge_row, dict) else None,
                ),
                "protection_status": (
                    hedge_row.get("protection_status") if isinstance(hedge_row, dict) else None
                ),
                "offset_coverage_ratio": (
                    hedge_row.get("offset_coverage_ratio") if isinstance(hedge_row, dict) else None
                ),
                "portfolio_loss_pct": (
                    hedge_row.get("portfolio_loss_pct") if isinstance(hedge_row, dict) else None
                ),
            }
        )
        if status != "not_applicable":
            row_status_accum.setdefault(protection_type, []).append(status)

    hedge_gap["weakness_map_confirmation"] = confirmations
    bridge_meta = hedge_gap.get("bridge_meta")
    if not isinstance(bridge_meta, dict):
        bridge_meta = {}
    bridge_meta["block_2_6_portfolio_weakness_map"] = True
    bridge_meta["n_weakness_rows_linked"] = len(confirmations)
    bridge_meta.setdefault("ruleset", RULESET_VERSION)
    hedge_gap["bridge_meta"] = bridge_meta
    _apply_row_confirmation_statuses(rows_by_type, row_status_accum)
    _refresh_summary_after_bridge(hedge_gap=hedge_gap, by_risk_type=by_risk)
    return True


def enrich_block_2_4_weak_hedge_from_hedge_gap(
    block_2_4_hidden_exposure: dict[str, Any],
    hedge_gap_v1: dict[str, Any],
) -> None:
    """Patch ``weak_hedge_behavior`` with hedge-gap bridge context (no Block 2.4 import)."""
    alerts = block_2_4_hidden_exposure.get("alerts")
    if not isinstance(alerts, dict):
        return
    weak = alerts.get("weak_hedge_behavior")
    if not isinstance(weak, dict):
        return

    bridge_row = next(
        (
            row
            for row in hedge_gap_v1.get("hidden_exposure_confirmation") or []
            if isinstance(row, dict) and row.get("alert_id") == "weak_hedge_behavior"
        ),
        None,
    )
    summary = hedge_gap_v1.get("summary") if isinstance(hedge_gap_v1.get("summary"), dict) else {}
    main_gap = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else None

    if not isinstance(bridge_row, dict):
        return

    bridge_status = str(bridge_row.get("confirmation_status") or "")
    weak["hedge_gap_bridge"] = {
        "confirmation_status": bridge_status,
        "main_hedge_gap_risk_type": main_gap.get("risk_type") if isinstance(main_gap, dict) else None,
        "main_hedge_gap_scenario_id": (
            main_gap.get("linked_scenario_id") if isinstance(main_gap, dict) else None
        ),
        "main_gap_score": summary.get("main_gap_score"),
        "n_risk_types_confirmed": sum(
            1
            for item in bridge_row.get("risk_type_confirmations") or []
            if isinstance(item, dict) and item.get("confirmation_status") == "confirmed"
        ),
    }

    if bridge_status in {"confirmed", "partially_confirmed", "not_confirmed"}:
        weak["confirmation_status"] = bridge_status
        notes = list(weak.get("calculation_notes") or [])
        note = (
            "weak_hedge_behavior confirmation refined by Block 3.3 hidden_exposure_confirmation "
            f"bridge ({bridge_status})."
        )
        if note not in notes:
            notes.append(note)
        weak["calculation_notes"] = notes

    if bridge_status == "partially_confirmed":
        limitations = list(weak.get("limitations") or [])
        extra = (
            "Stress offset coverage is mixed across protection areas relative to the weak-hedge "
            "pre-stress hypothesis."
        )
        if extra not in limitations:
            limitations.append(extra)
        weak["limitations"] = limitations
    elif bridge_status == "not_confirmed":
        limitations = list(weak.get("limitations") or [])
        extra = (
            "Pre-stress weak-hedge alert is not fully supported by Block 3.3 offset coverage "
            "in linked stress scenarios."
        )
        if extra not in limitations:
            limitations.append(extra)
        weak["limitations"] = limitations

    meta = block_2_4_hidden_exposure.get("diagnostics_meta")
    if isinstance(meta, dict):
        meta["hedge_gap_bridge_wire_time"] = True
        meta["hedge_gap_bridge_ruleset"] = hedge_gap_v1.get("ruleset_version")


def empty_hedge_gap_analysis_v1(
    reason: str = "no_data",
    *,
    loss_gate_mode: str = _LOSS_GATE_MODE_DIAGNOSTIC,
) -> dict[str, Any]:
    """Return a valid but empty hedge_gap_analysis_v1 block."""
    block = build_hedge_gap_analysis_v1(
        stress_results_v1={},
        scenario_results=[],
        loss_gate_mode=loss_gate_mode,
    )
    block["error"] = reason
    return block


def _alert_is_material_for_bridge(alert: dict[str, Any]) -> bool:
    status = str(alert.get("status") or "")
    if status in {"Medium", "High"}:
        return True
    score = alert.get("score")
    return isinstance(score, (int, float)) and float(score) >= _ALERT_MATERIAL_SCORE


def _linked_risk_types_for_alert(
    *,
    alert_id: str,
    linked_types: tuple[str, ...],
    rows_by_type: dict[str, dict[str, Any]],
    main_gap: dict[str, Any] | None,
) -> list[str]:
    if linked_types:
        return [risk_type for risk_type in linked_types if risk_type in rows_by_type]
    if alert_id == "weak_hedge_behavior":
        return [
            risk_type
            for risk_type, row in rows_by_type.items()
            if row.get("data_availability") == "available"
        ]
    if alert_id == "correlation_concentration" and isinstance(main_gap, dict):
        risk_type = main_gap.get("risk_type")
        if isinstance(risk_type, str) and risk_type in rows_by_type:
            return [risk_type]
    return []


def _weakness_is_material_for_bridge(weakness: dict[str, Any]) -> bool:
    severity = str(weakness.get("severity") or "")
    if severity in {"Medium", "High"}:
        return True
    score = weakness.get("score_0_100")
    return isinstance(score, (int, float)) and float(score) >= _WEAKNESS_MATERIAL_SCORE


def _confirm_row_against_block_2_6_weakness(
    row: dict[str, Any],
    weakness: dict[str, Any],
) -> tuple[str, str]:
    if not _weakness_is_material_for_bridge(weakness):
        return "not_applicable", "block_2_6_weakness_below_material_threshold"
    if not row:
        return "preliminary", "hedge_gap_row_missing_for_scenario"
    availability = row.get("data_availability")
    if availability != "available":
        return "preliminary", str(row.get("data_availability_reason") or "stress_row_not_available")
    protection = str(row.get("protection_status") or "")
    ratio = row.get("offset_coverage_ratio")
    if protection in {"weak_protection", "no_protection"}:
        return "confirmed", "material_weakness_aligns_with_weak_offset"
    if protection == "partial_protection":
        return "partially_confirmed", "material_weakness_with_partial_internal_offset"
    if protection in {"strong_protection", "not_needed_or_no_loss"}:
        return "not_confirmed", "material_weakness_not_supported_by_stress_offset"
    if isinstance(ratio, (int, float)) and float(ratio) < _OFFSET_COVERAGE_WEAK_THRESHOLD:
        return "confirmed", "offset_below_weak_threshold"
    return "preliminary", "protection_status_unresolved"


def _format_weakness_bridge_reason_en(
    *,
    scenario_id: str,
    weakness: dict[str, Any],
    confirmation_status: str,
    hedge_row: dict[str, Any] | None,
) -> str:
    severity = weakness.get("severity")
    score = weakness.get("score_0_100")
    score_text = f" (score {int(score)})" if isinstance(score, (int, float)) else ""
    if not _weakness_is_material_for_bridge(weakness):
        return (
            f"Block 2.6 weakness hypothesis for {scenario_id} is below the material threshold; "
            f"stress confirmation is not_applicable."
        )
    if not isinstance(hedge_row, dict):
        return (
            f"Block 2.6 {scenario_id}{score_text} severity {severity} has no linked hedge-gap row "
            f"for stress confirmation."
        )
    ratio = hedge_row.get("offset_coverage_ratio")
    ratio_text = (
        f"{float(ratio) * 100:.1f}% offset coverage"
        if isinstance(ratio, (int, float))
        else "offset coverage unavailable"
    )
    return (
        f"Block 2.6 {scenario_id}{score_text} ({severity}) is {confirmation_status} against "
        f"Block 3.3 stress evidence ({ratio_text}, protection "
        f"{hedge_row.get('protection_status') or 'unknown'})."
    )


def _weakness_bridge_reason_code(
    *,
    scenario_id: str,
    weakness: dict[str, Any],
    confirmation_status: str,
) -> str:
    if not _weakness_is_material_for_bridge(weakness):
        return "weakness_below_material_threshold"
    if confirmation_status == "confirmed":
        return f"{scenario_id}_stress_offset_confirms_weakness_hypothesis"
    if confirmation_status == "not_confirmed":
        return f"{scenario_id}_stress_offset_contradicts_weakness_hypothesis"
    if confirmation_status == "partially_confirmed":
        return f"{scenario_id}_mixed_stress_offset_evidence"
    if confirmation_status == "preliminary":
        return f"{scenario_id}_stress_evidence_incomplete"
    return f"{scenario_id}_no_hedge_gap_row"


def _confirm_row_against_block_2_4_alert(
    row: dict[str, Any],
    alert: dict[str, Any],
) -> tuple[str, str]:
    if not _alert_is_material_for_bridge(alert):
        return "not_applicable", "block_2_4_alert_below_material_threshold"
    availability = row.get("data_availability")
    if availability != "available":
        return "preliminary", str(row.get("data_availability_reason") or "stress_row_not_available")
    protection = str(row.get("protection_status") or "")
    ratio = row.get("offset_coverage_ratio")
    if protection in {"weak_protection", "no_protection"}:
        return "confirmed", "adverse_alert_aligns_with_weak_offset"
    if protection == "partial_protection":
        return "partially_confirmed", "adverse_alert_with_partial_internal_offset"
    if protection in {"strong_protection", "not_needed_or_no_loss"}:
        return "not_confirmed", "adverse_alert_not_supported_by_stress_offset"
    if isinstance(ratio, (int, float)) and float(ratio) < _OFFSET_COVERAGE_WEAK_THRESHOLD:
        return "confirmed", "offset_below_weak_threshold"
    return "preliminary", "protection_status_unresolved"


def _aggregate_bridge_confirmation(statuses: list[str]) -> str:
    if not statuses:
        return "not_applicable"
    if all(status == "not_applicable" for status in statuses):
        return "not_applicable"
    material = [status for status in statuses if status != "not_applicable"]
    if not material:
        return "not_applicable"
    if all(status == "confirmed" for status in material):
        return "confirmed"
    if all(status == "not_confirmed" for status in material):
        return "not_confirmed"
    if any(status == "confirmed" for status in material) and any(
        status == "not_confirmed" for status in material
    ):
        return "partially_confirmed"
    if any(status == "confirmed" for status in material):
        return "partially_confirmed"
    if any(status == "preliminary" for status in material):
        return "preliminary"
    return "partially_confirmed"


def _bridge_alert_reason_code(
    *,
    alert_id: str,
    alert: dict[str, Any],
    alert_confirmation: str,
) -> str:
    if not _alert_is_material_for_bridge(alert):
        return "alert_below_material_threshold"
    if alert_confirmation == "confirmed":
        return f"{alert_id}_stress_offset_confirms_hypothesis"
    if alert_confirmation == "not_confirmed":
        return f"{alert_id}_stress_offset_contradicts_hypothesis"
    if alert_confirmation == "partially_confirmed":
        return f"{alert_id}_mixed_stress_offset_evidence"
    if alert_confirmation == "preliminary":
        return f"{alert_id}_stress_evidence_incomplete"
    return f"{alert_id}_no_linked_risk_rows"


def _format_bridge_confirmation_reason_en(
    *,
    alert_id: str,
    alert: dict[str, Any],
    alert_confirmation: str,
    risk_confirmations: list[dict[str, Any]],
) -> str:
    alert_status = alert.get("status")
    alert_score = alert.get("score")
    score_text = (
        f" (score {float(alert_score):.0f})" if isinstance(alert_score, (int, float)) else ""
    )
    if not _alert_is_material_for_bridge(alert):
        return (
            f"Block 2.4 alert {alert_id} is below the material threshold; stress confirmation "
            f"is not_applicable."
        )
    if not risk_confirmations:
        return (
            f"Block 2.4 alert {alert_id}{score_text} has no linked hedge-gap risk rows for "
            f"stress confirmation."
        )
    n_confirmed = sum(1 for item in risk_confirmations if item.get("confirmation_status") == "confirmed")
    n_rows = len(risk_confirmations)
    return (
        f"Block 2.4 alert {alert_id}{score_text} is {alert_confirmation} against Block 3.3 offset "
        f"coverage ({n_confirmed} of {n_rows} linked scenario(s) show weak or no internal offset "
        f"where expected)."
    )


def _apply_row_confirmation_statuses(
    rows_by_type: dict[str, dict[str, Any]],
    row_status_accum: dict[str, list[str]],
) -> None:
    for risk_type, statuses in row_status_accum.items():
        row = rows_by_type.get(risk_type)
        if not isinstance(row, dict) or not statuses:
            continue
        best = max(
            statuses,
            key=lambda status: _ROW_CONFIRMATION_PRIORITY.get(str(status), -1),
        )
        row["confirmation_status"] = best


def _refresh_summary_after_bridge(
    *,
    hedge_gap: dict[str, Any],
    by_risk_type: list[dict[str, Any]],
) -> None:
    summary = hedge_gap.get("summary")
    if not isinstance(summary, dict):
        return
    bridge_meta = hedge_gap.get("bridge_meta")
    if not isinstance(bridge_meta, dict):
        bridge_meta = {}
    summary["limitations"] = _summary_limitations(
        data_quality_warnings=list(summary.get("data_quality_warnings") or []),
        by_risk_type=by_risk_type,
        block_2_4_bridge_applied=bool(bridge_meta.get("block_2_4_hidden_exposure")),
        block_2_6_bridge_applied=bool(bridge_meta.get("block_2_6_portfolio_weakness_map")),
    )


def _normalize_gate_mode(loss_gate_mode: str) -> str:
    mode = str(loss_gate_mode or "").strip().lower()
    if mode == _LOSS_GATE_MODE_DIAGNOSTIC:
        return _LOSS_GATE_MODE_DIAGNOSTIC
    return _LOSS_GATE_MODE_MANDATE


def _empty_summary() -> dict[str, Any]:
    return _build_summary([])


def _rows_with_offset_ratio(by_risk_type: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in by_risk_type
        if isinstance(row.get("offset_coverage_ratio"), (int, float))
    ]


def _portfolio_loss_sort_key(portfolio_loss_pct: Any) -> float:
    if isinstance(portfolio_loss_pct, (int, float)):
        return float(portfolio_loss_pct)
    return 0.0


def _compact_main_hedge_gap_row(row: dict[str, Any], *, main_gap_score: float | None) -> dict[str, Any]:
    compact: dict[str, Any] = {
        "risk_type": row["risk_type"],
        "protection_type": row["risk_type"],
        "linked_scenario_id": row["linked_scenario_id"],
        "scenario_id": row["linked_scenario_id"],
        "offset_coverage_ratio": row["offset_coverage_ratio"],
        "portfolio_loss_pct": row.get("portfolio_loss_pct"),
        "protection_status": row.get("protection_status"),
    }
    if main_gap_score is not None:
        compact["main_gap_score"] = round(main_gap_score, 3)
    return compact


def _row_has_portfolio_loss(row: dict[str, Any]) -> bool:
    loss = row.get("portfolio_loss_pct")
    return isinstance(loss, (int, float)) and float(loss) < 0.0


def _eligible_main_gap_candidate_rows(rows_with_ratio: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prefer loss scenarios; fall back to all ratio rows when none are losing."""
    loss_rows = [row for row in rows_with_ratio if _row_has_portfolio_loss(row)]
    return loss_rows if loss_rows else list(rows_with_ratio)


def _compute_main_gap_score(row: dict[str, Any]) -> float | None:
    """Weighted severity: offset deficit x portfolio loss x concentration boost."""
    ratio = row.get("offset_coverage_ratio")
    loss = row.get("portfolio_loss_pct")
    if not isinstance(ratio, (int, float)) or not isinstance(loss, (int, float)):
        return None
    if float(loss) >= 0.0:
        return None
    ratio_f = float(ratio)
    if not math.isfinite(ratio_f):
        return None
    loss_severity = abs(float(loss))
    if loss_severity <= 0.0 or not math.isfinite(loss_severity):
        return None
    offset_deficit = 1.0 - min(max(ratio_f, 0.0), 1.0)
    concentration = row.get("loss_concentration")
    conc_share: float = 0.0
    if isinstance(concentration, dict):
        top3 = concentration.get("top3_share_of_gross_loss")
        if isinstance(top3, (int, float)) and math.isfinite(float(top3)):
            conc_share = min(max(float(top3), 0.0), 1.0)
    conc_multiplier = 1.0 + _MAIN_GAP_CONCENTRATION_BOOST * conc_share
    score = offset_deficit * loss_severity * conc_multiplier
    if not math.isfinite(score):
        return None
    return float(score)


def _main_gap_selection_sort_key(row: dict[str, Any]) -> tuple[float, float, float, str]:
    score = _compute_main_gap_score(row)
    loss = row.get("portfolio_loss_pct")
    abs_loss = abs(float(loss)) if isinstance(loss, (int, float)) else 0.0
    ratio = float(row["offset_coverage_ratio"]) if isinstance(row.get("offset_coverage_ratio"), (int, float)) else 0.0
    return (
        score if score is not None else -1.0,
        abs_loss,
        -ratio,
        str(row.get("risk_type") or ""),
    )


def _select_main_hedge_gap_row(
    rows_with_ratio: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str, float | None]:
    if not rows_with_ratio:
        return None, "no_ratio_rows", None
    candidates = _eligible_main_gap_candidate_rows(rows_with_ratio)
    scored: list[tuple[dict[str, Any], float]] = []
    for row in candidates:
        score = _compute_main_gap_score(row)
        if score is not None:
            scored.append((row, score))
    if scored:
        main_row, score = max(scored, key=lambda item: _main_gap_selection_sort_key(item[0]))
        reason_code = (
            "weighted_gap_score_v2_loss_scenarios"
            if any(_row_has_portfolio_loss(row) for row in candidates)
            else "weighted_gap_score_v2_no_loss_fallback"
        )
        return main_row, reason_code, score
    main_row = min(
        candidates,
        key=lambda row: (
            float(row["offset_coverage_ratio"]),
            _portfolio_loss_sort_key(row.get("portfolio_loss_pct")),
            str(row.get("risk_type") or ""),
        ),
    )
    return main_row, "fallback_min_offset_ratio", None


def _format_main_gap_selection_reason_en(
    *,
    main_row: dict[str, Any],
    selection_reason_code: str,
    main_gap_score: float | None,
    candidate_count: int,
) -> str:
    risk_label = _risk_type_label_en(str(main_row.get("risk_type") or ""))
    scenario_label = _scenario_label_en(main_row.get("linked_scenario_id"))
    ratio_text = _format_ratio_pct_for_text(main_row.get("offset_coverage_ratio"))
    loss_text = _format_pct_for_text(main_row.get("portfolio_loss_pct"))
    if selection_reason_code.startswith("weighted_gap_score_v2"):
        score_text = f"{main_gap_score:.3f}" if isinstance(main_gap_score, (int, float)) else "n/a"
        parts = [
            (
                f"Selected {risk_label} protection ({scenario_label}) as the main hedge gap among "
                f"{candidate_count} scored scenario(s) using weighted gap score {score_text} "
                f"(offset deficit x portfolio loss severity, with up to "
                f"{int(_MAIN_GAP_CONCENTRATION_BOOST * 100)}% concentration boost)."
            ),
        ]
        if ratio_text:
            parts.append(f"Offset coverage is about {ratio_text}.")
        if loss_text:
            parts.append(f"Portfolio loss in that scenario is about {loss_text}.")
        return " ".join(parts)
    parts = [
        (
            f"Selected {risk_label} protection ({scenario_label}) by minimum offset coverage "
            f"among {candidate_count} candidate row(s) (legacy tie-break; weighted score unavailable)."
        ),
    ]
    if ratio_text:
        parts.append(f"Offset coverage is about {ratio_text}.")
    return " ".join(parts)


def _build_summary(by_risk_type: list[dict[str, Any]]) -> dict[str, Any]:
    rows_with_ratio = _rows_with_offset_ratio(by_risk_type)
    main_row, selection_reason_code, main_gap_score = _select_main_hedge_gap_row(rows_with_ratio)

    strongest_area: str | None = None
    if len(rows_with_ratio) >= 2:
        strongest_row = max(
            rows_with_ratio,
            key=lambda row: float(row["offset_coverage_ratio"]),
        )
        strongest_area = str(strongest_row["risk_type"])

    main_hedge_gap = (
        _compact_main_hedge_gap_row(main_row, main_gap_score=main_gap_score)
        if main_row is not None
        else None
    )
    summary: dict[str, Any] = {
        "main_hedge_gap": main_hedge_gap,
        "weakest_protection_area": main_row["risk_type"] if main_row is not None else None,
        "strongest_protection_area": strongest_area,
        "main_gap_score": round(main_gap_score, 3) if isinstance(main_gap_score, (int, float)) else None,
        "selection_reason_code": selection_reason_code if main_row is not None else None,
        "selection_reason_en": None,
        "diagnosis_summary_en": None,
        "data_quality_warnings": _collect_data_quality_warnings(by_risk_type, rows_with_ratio),
    }
    if main_row is not None:
        summary["selection_reason_en"] = _format_main_gap_selection_reason_en(
            main_row=main_row,
            selection_reason_code=selection_reason_code,
            main_gap_score=main_gap_score,
            candidate_count=len(_eligible_main_gap_candidate_rows(rows_with_ratio)),
        )
    summary["diagnosis_summary_en"] = _format_portfolio_diagnosis_summary_en(
        summary=summary,
        by_risk_type=by_risk_type,
    )
    _apply_summary_product_contract_fields(summary=summary, by_risk_type=by_risk_type, main_row=main_row)
    return summary


def _collect_data_quality_warnings(
    by_risk_type: list[dict[str, Any]],
    rows_with_ratio: list[dict[str, Any]],
) -> list[str]:
    warnings: list[str] = []
    reason_counts: dict[str, int] = {}
    for row in by_risk_type:
        availability = row.get("data_availability")
        if availability == "available":
            continue
        reason = str(row.get("data_availability_reason") or availability or "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    for reason, count in sorted(reason_counts.items()):
        warnings.append(f"{count}_risk_type_rows_{reason}")

    if by_risk_type and not rows_with_ratio:
        if any(row.get("data_availability") != "unavailable" for row in by_risk_type):
            warnings.append("no_offset_coverage_ratios_computed")
        elif len(by_risk_type) == len(
            [r for r in by_risk_type if r.get("data_availability") == "unavailable"]
        ):
            warnings.append("all_risk_type_rows_unavailable")

    return warnings


def _scenario_coverage(by_risk_type: list[dict[str, Any]]) -> dict[str, Any]:
    available = sum(1 for row in by_risk_type if row.get("data_availability") == "available")
    total = len(by_risk_type)
    return {
        "n_available": available,
        "n_total": total,
        "fraction_available": (available / total) if total else None,
    }


def _derive_block_status(by_risk_type: list[dict[str, Any]]) -> str:
    if not by_risk_type:
        return "unavailable"
    available = sum(1 for row in by_risk_type if row.get("data_availability") == "available")
    if available == 0:
        return "unavailable"
    if available == len(by_risk_type):
        return "ok"
    return "partial"


def _top3_asset_entries(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"ticker": a.get("ticker"), "pnl_pct": a.get("pnl_pct")} for a in (assets or [])[:3]]


def _derive_protection_status(row: dict[str, Any]) -> str:
    availability = row.get("data_availability")
    if availability == "unavailable":
        return "unavailable"
    loss = row.get("portfolio_loss_pct")
    if isinstance(loss, (int, float)) and float(loss) >= 0:
        return "not_needed_or_no_loss"
    if availability != "available":
        return "unavailable"
    ratio = row.get("offset_coverage_ratio")
    if not isinstance(ratio, (int, float)):
        return "unavailable"
    ratio_f = float(ratio)
    if ratio_f >= 0.60:
        return "strong_protection"
    if ratio_f >= 0.25:
        return "partial_protection"
    if ratio_f > 0:
        return "weak_protection"
    return "no_protection"


def _derive_confidence(row: dict[str, Any]) -> tuple[str, str]:
    availability = row.get("data_availability")
    if availability == "unavailable":
        return "unavailable", "scenario_or_contribution_data_missing"
    if availability == "insufficient_data":
        reason = str(row.get("data_availability_reason") or "insufficient_contributions")
        return "low", reason
    if row.get("portfolio_loss_pct") is None:
        return "medium", "portfolio_loss_missing"
    if not row.get("assets_hurt"):
        return "medium", "no_hurt_assets_in_scenario"
    return "high", "full_contribution_split_available"


def _row_limitations(row: dict[str, Any]) -> list[str]:
    limitations: list[str] = []
    if row.get("data_availability") != "available":
        reason = row.get("data_availability_reason")
        if reason:
            limitations.append(f"row_{reason}")
        return limitations
    loss = row.get("portfolio_loss_pct")
    if not isinstance(loss, (int, float)):
        limitations.append("portfolio_loss_unavailable")
    ratio = row.get("offset_coverage_ratio")
    if isinstance(ratio, (int, float)) and float(ratio) == 0.0 and isinstance(loss, (int, float)) and float(loss) < 0:
        limitations.append("zero_internal_offset_in_loss_scenario")
    return limitations


def _derive_next_decision_use(row: dict[str, Any]) -> str:
    status = row.get("protection_status")
    if status in {"weak_protection", "no_protection"}:
        return "candidate_hedge_gap_compare"
    if status in {"strong_protection", "partial_protection"}:
        return "monitor_protection_profile"
    if status == "not_needed_or_no_loss":
        return "no_hedge_gap_action_needed"
    return "review_data_before_decision"


def _format_client_risk_diagnosis_en(row: dict[str, Any]) -> str | None:
    if row.get("data_availability") != "available":
        return None
    loss_text = _format_pct_for_text(row.get("portfolio_loss_pct"))
    ratio_text = _format_ratio_pct_for_text(row.get("offset_coverage_ratio"))
    if loss_text is None or ratio_text is None:
        return None
    risk_label = _risk_type_label_en(str(row.get("risk_type") or ""))
    scenario_label = _scenario_label_en(row.get("linked_scenario_id"))
    status = row.get("protection_status")
    status_phrase = {
        "strong_protection": "strong internal offset",
        "partial_protection": "partial internal offset",
        "weak_protection": "weak internal offset",
        "no_protection": "no meaningful internal offset",
        "not_needed_or_no_loss": "no portfolio loss in this scenario",
    }.get(str(status or ""), "offset coverage")
    return (
        f"In the {scenario_label} scenario ({risk_label} protection, portfolio loss {loss_text}), "
        f"assets that helped offset about {ratio_text} of losses from assets that hurt — {status_phrase}."
    )


def _apply_product_contract_fields(row: dict[str, Any]) -> None:
    risk_type = str(row.get("risk_type") or "")
    linked_scenario_id = row.get("linked_scenario_id")
    row["protection_type"] = risk_type
    row["scenario_id"] = linked_scenario_id
    row["top3_loss_assets"] = _top3_asset_entries(list(row.get("assets_hurt") or []))
    row["top3_helped_assets"] = _top3_asset_entries(list(row.get("assets_helped") or []))
    row["protection_status"] = _derive_protection_status(row)
    row["confirmation_status"] = "not_applicable"
    confidence, confidence_reason = _derive_confidence(row)
    row["confidence"] = confidence
    row["confidence_reason"] = confidence_reason
    row["limitations"] = _row_limitations(row)
    row["client_diagnosis_en"] = _format_client_risk_diagnosis_en(row)
    row["next_decision_use"] = _derive_next_decision_use(row)


def _derive_protection_profile(by_risk_type: list[dict[str, Any]]) -> str:
    statuses = [str(row.get("protection_status") or "") for row in by_risk_type]
    weakish = sum(1 for s in statuses if s in {"weak_protection", "no_protection"})
    strongish = sum(1 for s in statuses if s in {"strong_protection", "partial_protection"})
    if weakish >= 3:
        return "mostly_weak_protection"
    if strongish >= 3 and weakish == 0:
        return "mostly_adequate_protection"
    if all(s == "unavailable" for s in statuses):
        return "unavailable"
    return "mixed_protection"


def _format_client_portfolio_summary_en(
    *,
    summary: dict[str, Any],
    by_risk_type: list[dict[str, Any]],
) -> str | None:
    main = summary.get("main_hedge_gap")
    if not isinstance(main, dict):
        return None
    weakest_label = _risk_type_label_en(str(main.get("risk_type") or ""))
    ratio_text = _format_ratio_pct_for_text(main.get("offset_coverage_ratio"))
    loss_text = _format_pct_for_text(main.get("portfolio_loss_pct"))
    if ratio_text is None:
        return None
    parts = [
        (
            f"The main hedge gap is {weakest_label} protection: in the stressed scenario, "
            f"helped assets covered only about {ratio_text} of losses from hurt assets."
        ),
    ]
    if loss_text:
        parts.append(f"Portfolio loss in that scenario was about {loss_text}.")
    profile = summary.get("protection_profile")
    if profile == "mostly_weak_protection":
        parts.append("Several protection areas show weak internal offset across scenarios.")
    return " ".join(parts)


def _summary_limitations(
    *,
    data_quality_warnings: list[str],
    by_risk_type: list[dict[str, Any]],
    block_2_4_bridge_applied: bool = False,
    block_2_6_bridge_applied: bool = False,
) -> list[str]:
    limitations = list(data_quality_warnings)
    if block_2_4_bridge_applied and block_2_6_bridge_applied:
        return limitations
    if not block_2_4_bridge_applied and not block_2_6_bridge_applied and any(
        row.get("confirmation_status") == "not_applicable" for row in by_risk_type
    ):
        limitations.append("pre_stress_confirmation_pending_block_2_4_2_6")
    if block_2_4_bridge_applied and not block_2_6_bridge_applied:
        limitations.append("block_2_6_weakness_map_confirmation_pending")
    if block_2_6_bridge_applied and not block_2_4_bridge_applied:
        limitations.append("block_2_4_hidden_exposure_confirmation_pending")
    return limitations


def _apply_summary_product_contract_fields(
    *,
    summary: dict[str, Any],
    by_risk_type: list[dict[str, Any]],
    main_row: dict[str, Any] | None,
) -> None:
    rows_with_ratio = _rows_with_offset_ratio(by_risk_type)
    ratios = [float(row["offset_coverage_ratio"]) for row in rows_with_ratio]
    summary["average_offset_coverage_ratio"] = (sum(ratios) / len(ratios)) if ratios else None
    summary["protection_profile"] = _derive_protection_profile(by_risk_type)
    summary["limitations"] = _summary_limitations(
        data_quality_warnings=list(summary.get("data_quality_warnings") or []),
        by_risk_type=by_risk_type,
    )
    summary["client_summary_en"] = _format_client_portfolio_summary_en(
        summary=summary,
        by_risk_type=by_risk_type,
    )
    main = summary.get("main_hedge_gap")
    if isinstance(main, dict):
        summary["main_hedge_gap_scenario_id"] = main.get("linked_scenario_id") or main.get("scenario_id")
        summary["main_hedge_gap_offset_coverage_ratio"] = main.get("offset_coverage_ratio")
        summary["main_hedge_gap_portfolio_loss_pct"] = main.get("portfolio_loss_pct")
    else:
        summary["main_hedge_gap_scenario_id"] = None
        summary["main_hedge_gap_offset_coverage_ratio"] = None
        summary["main_hedge_gap_portfolio_loss_pct"] = None
    if isinstance(main_row, dict):
        summary["main_assets_hurt"] = list(main_row.get("assets_hurt") or [])
        summary["main_assets_helped"] = list(main_row.get("assets_helped") or [])
    else:
        summary["main_assets_hurt"] = []
        summary["main_assets_helped"] = []


def _format_pct_for_text(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return f"{float(value) * 100:.1f}%"


def _format_ratio_pct_for_text(ratio: Any) -> str | None:
    if not isinstance(ratio, (int, float)):
        return None
    return f"{float(ratio) * 100:.1f}%"


def _risk_type_label_en(risk_type: str) -> str:
    return _RISK_TYPE_LABEL_EN.get(risk_type, risk_type.replace("_", " "))


def _scenario_label_en(scenario_id: str | None) -> str:
    if not scenario_id:
        return "mapped stress"
    return _SCENARIO_LABEL_EN.get(scenario_id, str(scenario_id).replace("_", " "))


def _format_risk_diagnosis_summary_en(row: dict[str, Any]) -> str | None:
    if row.get("data_availability") != "available":
        return None

    loss_text = _format_pct_for_text(row.get("portfolio_loss_pct"))
    if loss_text is None:
        return None

    risk_label = _risk_type_label_en(str(row.get("risk_type") or ""))
    scenario_label = _scenario_label_en(row.get("linked_scenario_id"))
    ratio_text = _format_ratio_pct_for_text(row.get("offset_coverage_ratio"))
    if ratio_text is None:
        return None

    parts = [
        (
            f"For {risk_label} protection ({scenario_label} scenario, portfolio loss {loss_text}), "
            f"helped assets offset about {ratio_text} of gross losses from hurt assets."
        ),
    ]

    assets_hurt = row.get("assets_hurt") or []
    assets_helped = row.get("assets_helped") or []
    if assets_hurt:
        top_hurt = str(assets_hurt[0].get("ticker") or "")
        if top_hurt:
            parts.append(f"Largest hurt contribution: {top_hurt}.")
    if assets_helped:
        top_helped = str(assets_helped[0].get("ticker") or "")
        if top_helped:
            parts.append(f"Largest offsetting contribution: {top_helped}.")
    elif float(row.get("offset_coverage_ratio") or 0) == 0.0:
        parts.append("No assets had positive contributions in this scenario.")

    loss_concentration = row.get("loss_concentration") or {}
    top3_share = loss_concentration.get("top3_share_of_gross_loss")
    if isinstance(top3_share, (int, float)) and float(top3_share) >= 0.5:
        parts.append(
            f"Losses are concentrated: top three hurt assets account for "
            f"{_format_ratio_pct_for_text(top3_share)} of gross hurt."
        )

    return " ".join(parts)


def _format_portfolio_diagnosis_summary_en(
    *,
    summary: dict[str, Any],
    by_risk_type: list[dict[str, Any]],
) -> str | None:
    main = summary.get("main_hedge_gap")
    if not isinstance(main, dict):
        return None

    weakest_label = _risk_type_label_en(str(main.get("risk_type") or ""))
    weakest_ratio_text = _format_ratio_pct_for_text(main.get("offset_coverage_ratio"))
    if weakest_ratio_text is None:
        return None

    parts = [f"The main hedge gap is {weakest_label} protection (offset coverage {weakest_ratio_text})."]
    selection_reason = summary.get("selection_reason_en")
    if isinstance(selection_reason, str) and selection_reason.strip():
        parts.append(selection_reason.strip())

    strongest_area = summary.get("strongest_protection_area")
    weakest_area = summary.get("weakest_protection_area")
    if (
        isinstance(strongest_area, str)
        and isinstance(weakest_area, str)
        and strongest_area != weakest_area
    ):
        strong_row = next(
            (row for row in by_risk_type if row.get("risk_type") == strongest_area),
            None,
        )
        if isinstance(strong_row, dict):
            strong_ratio_text = _format_ratio_pct_for_text(strong_row.get("offset_coverage_ratio"))
            strong_label = _risk_type_label_en(strongest_area)
            if strong_ratio_text:
                parts.append(
                    f"Offset coverage is relatively stronger for {strong_label} "
                    f"({strong_ratio_text}) than for {weakest_label} ({weakest_ratio_text})."
                )

    scenario_label = _scenario_label_en(main.get("linked_scenario_id"))
    loss_text = _format_pct_for_text(main.get("portfolio_loss_pct"))
    if loss_text:
        parts.append(
            f"In the {scenario_label} scenario (portfolio loss {loss_text}), "
            f"positive contributions from helped assets offset only about {weakest_ratio_text} "
            f"of gross losses from hurt assets."
        )

    return " ".join(parts)


def _index_scenario_results(
    scenario_results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("scenario_id")): row
        for row in scenario_results
        if row.get("scenario_id") is not None
    }


def _index_stress_results_v1_synthetics(
    stress_results_v1: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    synthetics = stress_results_v1.get("synthetic_scenarios")
    if not isinstance(synthetics, list):
        return {}
    return {
        str(row.get("scenario_id")): row
        for row in synthetics
        if isinstance(row, dict) and row.get("scenario_id") is not None
    }


def _resolve_portfolio_loss_pct(
    *,
    scenario_evidence: dict[str, Any] | None,
    stress_row: dict[str, Any] | None,
) -> float | None:
    if isinstance(stress_row, dict):
        loss = stress_row.get("portfolio_loss_pct")
        if isinstance(loss, (int, float)):
            return float(loss)
    if isinstance(scenario_evidence, dict):
        pnl = scenario_evidence.get("portfolio_pnl_pct")
        if isinstance(pnl, (int, float)):
            return float(pnl)
    return None


def _resolve_pnl_by_asset_pct(
    *,
    scenario_evidence: dict[str, Any] | None,
    stress_row: dict[str, Any] | None,
) -> dict[str, float] | None:
    if isinstance(stress_row, dict):
        loss_contrib = stress_row.get("loss_contribution")
        if isinstance(loss_contrib, dict):
            pnl_map = loss_contrib.get("pnl_by_asset_pct")
            parsed = _parse_pnl_by_asset_map(pnl_map)
            if parsed is not None:
                return parsed
    if isinstance(scenario_evidence, dict):
        parsed = _parse_pnl_by_asset_map(scenario_evidence.get("pnl_by_asset_pct"))
        if parsed is not None:
            return parsed
    return None


def _parse_pnl_by_asset_map(raw: Any) -> dict[str, float] | None:
    """Parse asset PnL map; drop non-finite values and blank tickers."""
    if not isinstance(raw, dict) or not raw:
        return None
    out: dict[str, float] = {}
    for ticker, pnl in raw.items():
        if not isinstance(pnl, (int, float)):
            continue
        value = float(pnl)
        if not math.isfinite(value):
            continue
        tick = str(ticker).strip()
        if not tick:
            continue
        out[tick] = value
    return out if out else None


def _split_hurt_helped(
    pnl_by_asset: dict[str, float],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Classify by sign only: hurt if pnl < 0, helped if pnl > 0; zeros excluded."""
    hurt_pairs = sorted(
        ((ticker, pnl) for ticker, pnl in pnl_by_asset.items() if pnl < 0.0),
        key=lambda item: (item[1], item[0]),
    )
    helped_pairs = sorted(
        ((ticker, pnl) for ticker, pnl in pnl_by_asset.items() if pnl > 0.0),
        key=lambda item: (-item[1], item[0]),
    )
    assets_hurt = [{"ticker": t, "pnl_pct": v} for t, v in hurt_pairs]
    assets_helped = [{"ticker": t, "pnl_pct": v} for t, v in helped_pairs]
    return assets_hurt, assets_helped


def _sum_gross_loss_from_hurt(assets_hurt: list[dict[str, Any]]) -> float:
    return sum(abs(float(a["pnl_pct"])) for a in assets_hurt)


def _sum_positive_contribution_from_helped(assets_helped: list[dict[str, Any]]) -> float:
    return sum(float(a["pnl_pct"]) for a in assets_helped)


def _compute_offset_coverage_ratio(
    gross_loss: float,
    positive_contribution: float,
) -> float | None:
    """Safe ratio; returns 0.0 when offset is zero and gross loss is positive."""
    if not math.isfinite(gross_loss) or not math.isfinite(positive_contribution):
        return None
    if gross_loss <= 0.0:
        return None
    return float(positive_contribution) / float(gross_loss)


def _compute_loss_concentration(
    assets_hurt: list[dict[str, Any]],
    gross_loss: float,
) -> dict[str, float | None]:
    if gross_loss <= 0.0 or not math.isfinite(gross_loss):
        return {"top3_share_of_gross_loss": None}
    top3_abs = _sum_gross_loss_from_hurt(assets_hurt[:3])
    share = top3_abs / gross_loss
    if not math.isfinite(share):
        return {"top3_share_of_gross_loss": None}
    return {"top3_share_of_gross_loss": share}


def _scaffold_risk_row(
    *,
    risk_type: str,
    linked_scenario_id: str,
    portfolio_loss_pct: float | None,
) -> dict[str, Any]:
    return {
        "risk_type": risk_type,
        "linked_scenario_id": linked_scenario_id,
        "linked_episode": None,
        "scenario_type": "synthetic",
        "portfolio_loss_pct": portfolio_loss_pct,
        "assets_hurt": [],
        "assets_helped": [],
        "gross_loss_from_assets_hurt": None,
        "positive_contribution_from_assets_helped": None,
        "offset_coverage_ratio": None,
        "loss_concentration": {"top3_share_of_gross_loss": None},
        "data_availability": "unavailable",
        "data_availability_reason": None,
        "diagnosis_summary_en": None,
    }


def _row_insufficient_data(
    *,
    risk_type: str,
    linked_scenario_id: str,
    portfolio_loss_pct: float | None,
    reason: str,
    assets_hurt: list[dict[str, Any]] | None = None,
    assets_helped: list[dict[str, Any]] | None = None,
    gross_loss: float | None = None,
    positive_contribution: float | None = None,
) -> dict[str, Any]:
    row = _scaffold_risk_row(
        risk_type=risk_type,
        linked_scenario_id=linked_scenario_id,
        portfolio_loss_pct=portfolio_loss_pct,
    )
    row["assets_hurt"] = assets_hurt or []
    row["assets_helped"] = assets_helped or []
    row["gross_loss_from_assets_hurt"] = gross_loss
    row["positive_contribution_from_assets_helped"] = positive_contribution
    row["data_availability"] = "insufficient_data"
    row["data_availability_reason"] = reason
    return row


def _row_available_contributions(
    *,
    risk_type: str,
    linked_scenario_id: str,
    portfolio_loss_pct: float | None,
    assets_hurt: list[dict[str, Any]],
    assets_helped: list[dict[str, Any]],
    gross_loss: float,
    positive_contribution: float,
) -> dict[str, Any]:
    ratio = _compute_offset_coverage_ratio(gross_loss, positive_contribution)
    assert ratio is not None
    row = _scaffold_risk_row(
        risk_type=risk_type,
        linked_scenario_id=linked_scenario_id,
        portfolio_loss_pct=portfolio_loss_pct,
    )
    row["assets_hurt"] = assets_hurt
    row["assets_helped"] = assets_helped
    row["gross_loss_from_assets_hurt"] = gross_loss
    row["positive_contribution_from_assets_helped"] = positive_contribution
    row["offset_coverage_ratio"] = ratio
    row["loss_concentration"] = _compute_loss_concentration(assets_hurt, gross_loss)
    row["data_availability"] = "available"
    row["data_availability_reason"] = None
    return row


def _build_risk_row(
    *,
    risk_type: str,
    linked_scenario_id: str,
    scenario_evidence: dict[str, Any] | None,
    stress_row: dict[str, Any] | None,
) -> dict[str, Any]:
    if scenario_evidence is None and stress_row is None:
        return _unavailable_risk_row(risk_type, linked_scenario_id, reason="scenario_row_missing")

    portfolio_loss_pct = _resolve_portfolio_loss_pct(
        scenario_evidence=scenario_evidence,
        stress_row=stress_row,
    )
    pnl_by_asset = _resolve_pnl_by_asset_pct(
        scenario_evidence=scenario_evidence,
        stress_row=stress_row,
    )
    if pnl_by_asset is None:
        return _unavailable_risk_row(
            risk_type,
            linked_scenario_id,
            reason="pnl_by_asset_unavailable",
            portfolio_loss_pct=portfolio_loss_pct,
        )

    assets_hurt, assets_helped = _split_hurt_helped(pnl_by_asset)
    if not assets_hurt:
        positive = _sum_positive_contribution_from_helped(assets_helped)
        return _row_insufficient_data(
            risk_type=risk_type,
            linked_scenario_id=linked_scenario_id,
            portfolio_loss_pct=portfolio_loss_pct,
            reason="no_assets_hurt",
            assets_helped=assets_helped,
            positive_contribution=positive,
        )

    gross_loss = _sum_gross_loss_from_hurt(assets_hurt)
    positive_contribution = _sum_positive_contribution_from_helped(assets_helped)
    ratio = _compute_offset_coverage_ratio(gross_loss, positive_contribution)
    if ratio is None:
        return _row_insufficient_data(
            risk_type=risk_type,
            linked_scenario_id=linked_scenario_id,
            portfolio_loss_pct=portfolio_loss_pct,
            reason="zero_gross_loss",
            assets_hurt=assets_hurt,
            assets_helped=assets_helped,
            gross_loss=gross_loss,
            positive_contribution=positive_contribution,
        )

    return _row_available_contributions(
        risk_type=risk_type,
        linked_scenario_id=linked_scenario_id,
        portfolio_loss_pct=portfolio_loss_pct,
        assets_hurt=assets_hurt,
        assets_helped=assets_helped,
        gross_loss=gross_loss,
        positive_contribution=positive_contribution,
    )


def _unavailable_risk_row(
    risk_type: str,
    linked_scenario_id: str,
    *,
    reason: str = "scenario_row_missing",
    portfolio_loss_pct: float | None = None,
) -> dict[str, Any]:
    row = _scaffold_risk_row(
        risk_type=risk_type,
        linked_scenario_id=linked_scenario_id,
        portfolio_loss_pct=portfolio_loss_pct,
    )
    row["data_availability"] = "unavailable"
    row["data_availability_reason"] = reason
    return row
