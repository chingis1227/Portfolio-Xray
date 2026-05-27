"""Block 3.3 Hedge Gap Analysis builder — hedge_gap_analysis_v1.

Builds the product-facing Block 3.3 layer from stress evidence already on
``stress_report.json`` (Block 3.1 ``scenario_results[]``, Block 3.2
``stress_results_v1``). No second stress engine and no taxonomy hedge labels.

This module must not import ``src.stress`` (mirror Block 3.2 isolation).

Session 02 (scaffold): registry, eight unavailable placeholder rows, attach stub.
Session 03: per-risk hurt/helped extraction and offset_coverage_ratio.
Session 04: summary + diagnosis_summary_en templates (implemented).
Session 05: attach_hedge_gap_analysis_v1 wired from run_stress, _empty_report, run_report, run_optimization.
"""
from __future__ import annotations

from typing import Any

from src.scenario_library import SCENARIO_LIBRARY_VERSION, SYNTHETIC_SCENARIO_IDS

BLOCK_3_3_VERSION = "hedge_gap_analysis_v1"
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
    summary = _build_summary(by_risk_type)
    return {
        "version": BLOCK_3_3_VERSION,
        "loss_gate_mode": gate_mode,
        "diagnosis_method": _DIAGNOSIS_METHOD,
        "scenario_library": {
            "version": SCENARIO_LIBRARY_VERSION,
            "synthetic_ids": list(SYNTHETIC_SCENARIO_IDS),
        },
        "by_risk_type": by_risk_type,
        "summary": summary,
        "n_risk_types": len(by_risk_type),
    }


def attach_hedge_gap_analysis_v1(stress_report: dict[str, Any]) -> None:
    """Rebuild ``hedge_gap_analysis_v1`` on *stress_report* from current evidence (in-place)."""
    stress_results_v1 = stress_report.get("stress_results_v1")
    if not isinstance(stress_results_v1, dict):
        stress_results_v1 = {}
    stress_report["hedge_gap_analysis_v1"] = build_hedge_gap_analysis_v1(
        stress_results_v1=stress_results_v1,
        scenario_results=list(stress_report.get("scenario_results") or []),
        loss_gate_mode=str(stress_report.get("loss_gate_mode") or _LOSS_GATE_MODE_MANDATE),
    )


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


def _compact_main_hedge_gap_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_type": row["risk_type"],
        "linked_scenario_id": row["linked_scenario_id"],
        "offset_coverage_ratio": row["offset_coverage_ratio"],
        "portfolio_loss_pct": row.get("portfolio_loss_pct"),
    }


def _build_summary(by_risk_type: list[dict[str, Any]]) -> dict[str, Any]:
    rows_with_ratio = _rows_with_offset_ratio(by_risk_type)
    main_row: dict[str, Any] | None = None
    if rows_with_ratio:
        main_row = min(
            rows_with_ratio,
            key=lambda row: (
                float(row["offset_coverage_ratio"]),
                _portfolio_loss_sort_key(row.get("portfolio_loss_pct")),
            ),
        )

    strongest_area: str | None = None
    if len(rows_with_ratio) >= 2:
        strongest_row = max(
            rows_with_ratio,
            key=lambda row: float(row["offset_coverage_ratio"]),
        )
        strongest_area = str(strongest_row["risk_type"])

    main_hedge_gap = _compact_main_hedge_gap_row(main_row) if main_row is not None else None
    summary: dict[str, Any] = {
        "main_hedge_gap": main_hedge_gap,
        "weakest_protection_area": main_row["risk_type"] if main_row is not None else None,
        "strongest_protection_area": strongest_area,
        "diagnosis_summary_en": None,
        "data_quality_warnings": _collect_data_quality_warnings(by_risk_type, rows_with_ratio),
    }
    summary["diagnosis_summary_en"] = _format_portfolio_diagnosis_summary_en(
        summary=summary,
        by_risk_type=by_risk_type,
    )
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
    if not isinstance(raw, dict) or not raw:
        return None
    out: dict[str, float] = {}
    for ticker, pnl in raw.items():
        if isinstance(pnl, (int, float)):
            out[str(ticker)] = float(pnl)
    return out if out else None


def _split_hurt_helped(
    pnl_by_asset: dict[str, float],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    hurt_pairs = sorted(
        ((ticker, pnl) for ticker, pnl in pnl_by_asset.items() if pnl < 0),
        key=lambda item: (item[1], item[0]),
    )
    helped_pairs = sorted(
        ((ticker, pnl) for ticker, pnl in pnl_by_asset.items() if pnl > 0),
        key=lambda item: (-item[1], item[0]),
    )
    assets_hurt = [{"ticker": t, "pnl_pct": v} for t, v in hurt_pairs]
    assets_helped = [{"ticker": t, "pnl_pct": v} for t, v in helped_pairs]
    return assets_hurt, assets_helped


def _compute_loss_concentration(
    assets_hurt: list[dict[str, Any]],
    gross_loss: float,
) -> dict[str, float | None]:
    if gross_loss <= 0:
        return {"top3_share_of_gross_loss": None}
    top3_abs = sum(abs(float(a["pnl_pct"])) for a in assets_hurt[:3])
    return {"top3_share_of_gross_loss": top3_abs / gross_loss}


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
        return {
            "risk_type": risk_type,
            "linked_scenario_id": linked_scenario_id,
            "linked_episode": None,
            "scenario_type": "synthetic",
            "portfolio_loss_pct": portfolio_loss_pct,
            "assets_hurt": [],
            "assets_helped": assets_helped,
            "gross_loss_from_assets_hurt": None,
            "positive_contribution_from_assets_helped": (
                sum(float(a["pnl_pct"]) for a in assets_helped) if assets_helped else 0.0
            ),
            "offset_coverage_ratio": None,
            "loss_concentration": {"top3_share_of_gross_loss": None},
            "data_availability": "insufficient_data",
            "data_availability_reason": "no_assets_hurt",
            "diagnosis_summary_en": None,
        }

    gross_loss = sum(abs(float(a["pnl_pct"])) for a in assets_hurt)
    positive_contribution = sum(float(a["pnl_pct"]) for a in assets_helped)

    if gross_loss <= 0:
        return {
            "risk_type": risk_type,
            "linked_scenario_id": linked_scenario_id,
            "linked_episode": None,
            "scenario_type": "synthetic",
            "portfolio_loss_pct": portfolio_loss_pct,
            "assets_hurt": assets_hurt,
            "assets_helped": assets_helped,
            "gross_loss_from_assets_hurt": gross_loss,
            "positive_contribution_from_assets_helped": positive_contribution,
            "offset_coverage_ratio": None,
            "loss_concentration": {"top3_share_of_gross_loss": None},
            "data_availability": "insufficient_data",
            "data_availability_reason": "zero_gross_loss",
            "diagnosis_summary_en": None,
        }

    offset_coverage_ratio = positive_contribution / gross_loss
    return {
        "risk_type": risk_type,
        "linked_scenario_id": linked_scenario_id,
        "linked_episode": None,
        "scenario_type": "synthetic",
        "portfolio_loss_pct": portfolio_loss_pct,
        "assets_hurt": assets_hurt,
        "assets_helped": assets_helped,
        "gross_loss_from_assets_hurt": gross_loss,
        "positive_contribution_from_assets_helped": positive_contribution,
        "offset_coverage_ratio": offset_coverage_ratio,
        "loss_concentration": _compute_loss_concentration(assets_hurt, gross_loss),
        "data_availability": "available",
        "data_availability_reason": None,
        "diagnosis_summary_en": None,
    }


def _unavailable_risk_row(
    risk_type: str,
    linked_scenario_id: str,
    *,
    reason: str = "scenario_row_missing",
    portfolio_loss_pct: float | None = None,
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
        "data_availability_reason": reason,
        "diagnosis_summary_en": None,
    }
