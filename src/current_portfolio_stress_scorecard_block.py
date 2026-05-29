"""Block 3.4 Current Portfolio Stress Scorecard — current_portfolio_stress_scorecard_v1.

This is a diagnostic-only, product-facing summary layer that **reuses** existing Stress Lab
outputs on ``stress_report.json``:

- Block 3.1 evidence: ``scenario_results[]`` + ``historical_results[]``
- Block 3.2 product adapter: ``stress_results_v1``
- Block 3.3 product adapter: ``hedge_gap_analysis_v1``

It must not introduce mandate pass/fail, suitability logic, or DIAG_* language.
It must not create a new stress engine and must not add scenarios.
"""

from __future__ import annotations

import math
from typing import Any

BLOCK_3_4_VERSION = "current_portfolio_stress_scorecard_v1"
RULESET_VERSION = "current_portfolio_stress_scorecard_rules_v1_1"
SCORECARD_SCOPE = "current_portfolio_diagnostic"
_LOSS_GATE_MODE_DIAGNOSTIC = "diagnostic"
_LOSS_GATE_MODE_MANDATE = "mandate"
_BLOCK_3_2_VERSION = "stress_results_v1"
_BLOCK_3_3_VERSION = "hedge_gap_analysis_v1"
_WORST_SYNTHETIC_SELECTION_METRIC = "portfolio_pnl_pct"
_WORST_HISTORICAL_SELECTION_METRIC = "max_dd"
_ENVELOPE_SELECTION_SOURCE = "stress_results_v1.envelope"
_NEXT_DECISION_USE_TOKENS = (
    "problem_classification",
    "candidate_comparison",
    "ai_commentary",
    "monitoring",
)
_FORBIDDEN_ENGLISH_PHRASES = (
    "passes normally",
    "passed stress",
    "failed stress",
)
AI_COMMENTARY_FORBIDDEN_LEGACY_FIELD_PATHS: tuple[str, ...] = (
    "stress_scorecard_v1.overall_status",
    "stress_scorecard_v1.overall_reason",
    "stress_scorecard_v1.overall_confidence",
)


def attach_current_portfolio_stress_scorecard_v1(
    stress_report: dict[str, Any],
    *,
    portfolio_xray: dict[str, Any] | None = None,
    block_2_4_hidden_exposure: dict[str, Any] | None = None,
    block_2_6_portfolio_weakness_map: dict[str, Any] | None = None,
) -> None:
    """Rebuild ``current_portfolio_stress_scorecard_v1`` on *stress_report* (in-place)."""
    stress_report[BLOCK_3_4_VERSION] = build_current_portfolio_stress_scorecard_v1(
        stress_report,
        portfolio_xray=portfolio_xray,
        block_2_4_hidden_exposure=block_2_4_hidden_exposure,
        block_2_6_portfolio_weakness_map=block_2_6_portfolio_weakness_map,
    )


def empty_current_portfolio_stress_scorecard_v1(
    reason: str = "no_data",
    *,
    loss_gate_mode: str = _LOSS_GATE_MODE_DIAGNOSTIC,
) -> dict[str, Any]:
    gate_mode = _normalize_gate_mode(loss_gate_mode)
    return {
        "version": BLOCK_3_4_VERSION,
        "block": "3.4",
        "ruleset_version": RULESET_VERSION,
        "block_status": "unavailable",
        "scorecard_scope": SCORECARD_SCOPE,
        "source_blocks_used": [],
        "stress_coverage": _empty_stress_coverage(),
        "legacy_fallback_used": False,
        "limitations": [reason],
        "scenario_library": None,
        "loss_gate_mode": gate_mode,
        "worst_synthetic_scenario": {"availability": "unavailable", "reason_en": reason},
        "worst_historical_scenario": {"availability": "unavailable", "reason_en": reason},
        "portfolio_loss_summary": {"availability": "unavailable", "reason_en": reason},
        "historical_drawdown_summary": {"availability": "unavailable", "reason_en": reason},
        "top_loss_contributors": {"availability": "unavailable", "reason_en": reason},
        "loss_contribution_summary": {"availability": "unavailable", "reason_en": reason},
        "top_risk_contributors": {"availability": "unavailable", "reason_en": reason},
        "risk_contribution_summary": {"availability": "unavailable", "reason_en": reason},
        "factor_stress_attribution_summary": {"availability": "unavailable", "reason_en": reason},
        "assets_helped_hurt_summary": {"availability": "unavailable", "reason_en": reason},
        "offset_coverage_summary": {"availability": "unavailable", "reason_en": reason},
        "main_hedge_gap": {"availability": "unavailable", "reason_en": reason},
        "hedge_gap_summary": {"availability": "unavailable", "reason_en": reason},
        "relatively_resilient_scenarios": [],
        "less_damaging_scenarios": [],
        "stress_diagnosis": _empty_stress_diagnosis(reason),
        "problem_classification_signals": _empty_problem_classification_signals(reason),
        "candidate_comparison_targets": _empty_candidate_comparison_targets(reason),
        "ai_commentary_context": _empty_ai_commentary_context(reason),
        "next_decision_uses": [],
        "pre_stress_confirmation_summary": _empty_pre_stress_confirmation_summary(reason),
        "data_quality_warnings": [reason],
        "diagnosis_summary_en": None,
    }


def build_current_portfolio_stress_scorecard_v1(
    stress_report: dict[str, Any],
    *,
    portfolio_xray: dict[str, Any] | None = None,
    block_2_4_hidden_exposure: dict[str, Any] | None = None,
    block_2_6_portfolio_weakness_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build Block 3.4 summary from existing Stress Lab outputs on *stress_report*."""
    gate_mode = _normalize_gate_mode(str(stress_report.get("loss_gate_mode") or _LOSS_GATE_MODE_DIAGNOSTIC))

    block_2_4 = _resolve_block_2_4(
        block_2_4_hidden_exposure=block_2_4_hidden_exposure,
        portfolio_xray=portfolio_xray,
    )
    block_2_6 = _resolve_block_2_6(
        block_2_6_portfolio_weakness_map=block_2_6_portfolio_weakness_map,
        portfolio_xray=portfolio_xray,
    )

    stress_results = stress_report.get("stress_results_v1")
    stress_results = stress_results if isinstance(stress_results, dict) else {}

    hedge_gap = stress_report.get("hedge_gap_analysis_v1")
    hedge_gap = hedge_gap if isinstance(hedge_gap, dict) else {}

    conclusions = stress_report.get("stress_conclusions")
    conclusions = conclusions if isinstance(conclusions, dict) else {}

    trust = stress_report.get("data_trust_summary")
    trust = trust if isinstance(trust, dict) else {}

    scenario_library = stress_results.get("scenario_library")
    if not isinstance(scenario_library, dict):
        scenario_library = hedge_gap.get("scenario_library") if isinstance(hedge_gap.get("scenario_library"), dict) else None

    env = stress_results.get("envelope") if isinstance(stress_results.get("envelope"), dict) else {}
    worst_syn = env.get("worst_synthetic") if isinstance(env.get("worst_synthetic"), dict) else None
    worst_hist = env.get("worst_historical") if isinstance(env.get("worst_historical"), dict) else None

    synthetic_rows = stress_results.get("synthetic_scenarios") if isinstance(stress_results.get("synthetic_scenarios"), list) else []
    historical_rows = stress_results.get("historical_episodes") if isinstance(stress_results.get("historical_episodes"), list) else []

    worst_synthetic_scenario = _build_worst_synthetic_block(worst_syn)
    worst_historical_scenario = _build_worst_historical_block(worst_hist)

    top_loss_contributors = _build_top_loss_contributors(
        worst_syn=worst_syn,
        worst_hist=worst_hist,
    )
    loss_contribution_summary = _build_loss_contribution_summary(
        top_loss_contributors=top_loss_contributors,
        synthetic_rows=synthetic_rows,
        historical_rows=historical_rows,
    )
    top_risk_contributors = _build_top_risk_contributors(
        synthetic_rows=synthetic_rows,
        worst_synthetic_id=worst_syn.get("scenario_id") if isinstance(worst_syn, dict) else None,
    )
    risk_contribution_summary = _build_risk_contribution_summary(
        top_risk_contributors=top_risk_contributors,
        top_loss_contributors=top_loss_contributors,
    )
    factor_attr = _build_factor_stress_attribution_summary(
        worst_syn=worst_syn,
        conclusions=conclusions,
        synthetic_rows=synthetic_rows,
    )
    assets_helped_hurt = _build_assets_helped_hurt_summary(
        worst_syn=worst_syn,
        hedge_gap=hedge_gap,
    )
    offset_coverage, main_hedge_gap = _build_offset_and_main_gap(hedge_gap)
    hedge_gap_summary = _build_hedge_gap_summary(hedge_gap)

    portfolio_loss_summary = _build_portfolio_loss_summary(worst_syn=worst_syn, worst_hist=worst_hist)
    historical_drawdown_summary = _build_historical_drawdown_summary(worst_hist=worst_hist)

    warnings = _collect_data_quality_warnings(
        historical_rows=historical_rows,
        hedge_gap=hedge_gap,
        trust=trust,
        conclusions=conclusions,
    )

    diagnosis_summary_en = _format_diagnosis_summary_en(
        worst_synthetic=worst_synthetic_scenario,
        worst_historical=worst_historical_scenario,
        main_hedge_gap=main_hedge_gap,
        warnings=warnings,
    )

    hedge_gap_meta: dict[str, Any] = {}
    if isinstance(hedge_gap, dict) and hedge_gap.get("version") == _BLOCK_3_3_VERSION:
        hg_summary = hedge_gap.get("summary") if isinstance(hedge_gap.get("summary"), dict) else {}
        hedge_gap_meta = {
            "hedge_gap_ruleset_version": hedge_gap.get("ruleset_version"),
            "hedge_gap_block_status": hedge_gap.get("block_status"),
            "protection_profile": hg_summary.get("protection_profile"),
        }

    source_blocks_used = _derive_source_blocks_used(
        stress_results=stress_results,
        hedge_gap=hedge_gap,
        conclusions=conclusions,
        trust=trust,
        portfolio_xray_attached=_is_block_2_4_attached(block_2_4) or _is_block_2_6_attached(block_2_6),
    )
    legacy_fallback_used = _derive_legacy_fallback_used(stress_report)
    stress_coverage = _derive_stress_coverage(
        synthetic_rows=synthetic_rows,
        historical_rows=historical_rows,
        scenario_library=scenario_library if isinstance(scenario_library, dict) else None,
    )
    limitations = _derive_limitations(
        historical_rows=historical_rows,
        top_risk_contributors=top_risk_contributors,
        hedge_gap=hedge_gap,
        main_hedge_gap=main_hedge_gap,
    )
    limitations.extend(
        _worst_selector_consistency_limitations(
            worst_syn=worst_syn,
            worst_hist=worst_hist,
            synthetic_rows=synthetic_rows,
            historical_rows=historical_rows,
        )
    )
    block_status = _derive_block_status(
        stress_results=stress_results,
        worst_synthetic_scenario=worst_synthetic_scenario,
        worst_historical_scenario=worst_historical_scenario,
        historical_rows=historical_rows,
        top_risk_contributors=top_risk_contributors,
        hedge_gap=hedge_gap,
        warnings=warnings,
        trust=trust,
    )

    relatively_resilient_scenarios = _build_relatively_resilient_scenarios(synthetic_rows)
    resilient_ids = {
        str(row["scenario_id"])
        for row in relatively_resilient_scenarios
        if isinstance(row, dict) and row.get("scenario_id")
    }
    worst_syn_loss = (
        worst_synthetic_scenario.get("portfolio_loss_pct")
        if worst_synthetic_scenario.get("availability") == "available"
        else None
    )
    less_damaging_scenarios = _build_less_damaging_scenarios(
        synthetic_rows=synthetic_rows,
        worst_synthetic_loss_pct=worst_syn_loss,
        exclude_scenario_ids=resilient_ids,
    )
    stress_diagnosis = _build_stress_diagnosis(
        block_status=block_status,
        worst_synthetic=worst_synthetic_scenario,
        worst_historical=worst_historical_scenario,
        main_hedge_gap=main_hedge_gap,
        hedge_gap=hedge_gap,
        hedge_gap_summary=hedge_gap_summary,
        factor_attr=factor_attr,
        top_risk_contributors=top_risk_contributors,
        stress_coverage=stress_coverage,
        warnings=warnings,
        diagnosis_summary_en=diagnosis_summary_en,
    )
    next_decision_uses = _derive_next_decision_uses(block_status)
    problem_classification_signals = _build_problem_classification_signals(
        block_status=block_status,
        worst_synthetic=worst_synthetic_scenario,
        worst_historical=worst_historical_scenario,
        hedge_gap_summary=hedge_gap_summary,
        stress_diagnosis=stress_diagnosis,
        loss_gate_mode=gate_mode,
    )
    candidate_comparison_targets = _build_candidate_comparison_targets(
        block_status=block_status,
        worst_synthetic=worst_synthetic_scenario,
        hedge_gap_summary=hedge_gap_summary,
    )
    ai_commentary_context = _build_ai_commentary_context(
        block_status=block_status,
        stress_diagnosis=stress_diagnosis,
        worst_synthetic=worst_synthetic_scenario,
        worst_historical=worst_historical_scenario,
        hedge_gap_summary=hedge_gap_summary,
        legacy_fallback_used=legacy_fallback_used,
        protection_profile=hedge_gap_meta.get("protection_profile"),
    )
    pre_stress_confirmation_summary = _build_pre_stress_confirmation_summary(
        hedge_gap=hedge_gap,
        block_2_4=block_2_4,
        block_2_6=block_2_6,
    )

    return {
        "version": BLOCK_3_4_VERSION,
        "block": "3.4",
        "ruleset_version": RULESET_VERSION,
        "block_status": block_status,
        "scorecard_scope": SCORECARD_SCOPE,
        "source_blocks_used": source_blocks_used,
        "stress_coverage": stress_coverage,
        "legacy_fallback_used": legacy_fallback_used,
        "limitations": limitations,
        **hedge_gap_meta,
        "scenario_library": scenario_library,
        "loss_gate_mode": gate_mode,
        "worst_synthetic_scenario": worst_synthetic_scenario,
        "worst_historical_scenario": worst_historical_scenario,
        "portfolio_loss_summary": portfolio_loss_summary,
        "historical_drawdown_summary": historical_drawdown_summary,
        "top_loss_contributors": top_loss_contributors,
        "loss_contribution_summary": loss_contribution_summary,
        "top_risk_contributors": top_risk_contributors,
        "risk_contribution_summary": risk_contribution_summary,
        "factor_stress_attribution_summary": factor_attr,
        "assets_helped_hurt_summary": assets_helped_hurt,
        "offset_coverage_summary": offset_coverage,
        "main_hedge_gap": main_hedge_gap,
        "hedge_gap_summary": hedge_gap_summary,
        "relatively_resilient_scenarios": relatively_resilient_scenarios,
        "less_damaging_scenarios": less_damaging_scenarios,
        "stress_diagnosis": stress_diagnosis,
        "problem_classification_signals": problem_classification_signals,
        "candidate_comparison_targets": candidate_comparison_targets,
        "ai_commentary_context": ai_commentary_context,
        "next_decision_uses": next_decision_uses,
        "pre_stress_confirmation_summary": pre_stress_confirmation_summary,
        "data_quality_warnings": warnings,
        "diagnosis_summary_en": stress_diagnosis.get("diagnosis_summary_en"),
    }


def _normalize_gate_mode(loss_gate_mode: str) -> str:
    mode = str(loss_gate_mode or "").strip().lower()
    if mode == _LOSS_GATE_MODE_DIAGNOSTIC:
        return _LOSS_GATE_MODE_DIAGNOSTIC
    return _LOSS_GATE_MODE_MANDATE


def _derive_source_blocks_used(
    *,
    stress_results: dict[str, Any],
    hedge_gap: dict[str, Any],
    conclusions: dict[str, Any],
    trust: dict[str, Any],
    portfolio_xray_attached: bool = False,
) -> list[str]:
    used: list[str] = []
    if isinstance(stress_results, dict) and stress_results.get("version") == _BLOCK_3_2_VERSION:
        used.append("stress_results_v1")
    if isinstance(hedge_gap, dict) and hedge_gap.get("version") == _BLOCK_3_3_VERSION:
        used.append("hedge_gap_analysis_v1")
    if isinstance(conclusions, dict) and conclusions:
        used.append("stress_conclusions")
    if isinstance(trust, dict) and trust:
        used.append("data_trust_summary")
    if portfolio_xray_attached:
        used.append("portfolio_xray")
    return used


def _resolve_block_2_4(
    *,
    block_2_4_hidden_exposure: dict[str, Any] | None,
    portfolio_xray: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if isinstance(block_2_4_hidden_exposure, dict):
        return block_2_4_hidden_exposure
    if isinstance(portfolio_xray, dict):
        block = portfolio_xray.get("block_2_4_hidden_exposure")
        if isinstance(block, dict):
            return block
    return None


def _resolve_block_2_6(
    *,
    block_2_6_portfolio_weakness_map: dict[str, Any] | None,
    portfolio_xray: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if isinstance(block_2_6_portfolio_weakness_map, dict):
        return block_2_6_portfolio_weakness_map
    if isinstance(portfolio_xray, dict):
        block = portfolio_xray.get("block_2_6_portfolio_weakness_map")
        if isinstance(block, dict):
            return block
    return None


def _is_block_2_4_attached(block_2_4: dict[str, Any] | None) -> bool:
    return isinstance(block_2_4, dict) and isinstance(block_2_4.get("alerts"), dict)


def _is_block_2_6_attached(block_2_6: dict[str, Any] | None) -> bool:
    return isinstance(block_2_6, dict) and isinstance(block_2_6.get("risk_types"), list)


def _empty_pre_stress_confirmation_summary(reason: str) -> dict[str, Any]:
    return {
        "hidden_exposure": {
            "status": "not_applicable",
            "reason_en": "block_2_4_not_attached",
        },
        "weakness_map": {
            "status": "not_applicable",
            "reason_en": "block_2_6_not_attached",
        },
        "aggregate_confirmation": {
            "status": "unavailable",
            "reason_en": reason,
        },
    }


def _aggregate_confirmation_statuses(statuses: list[str]) -> str:
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


def _build_pre_stress_confirmation_summary(
    *,
    hedge_gap: dict[str, Any],
    block_2_4: dict[str, Any] | None,
    block_2_6: dict[str, Any] | None,
) -> dict[str, Any]:
    hidden = _build_hidden_exposure_confirmation_subblock(hedge_gap=hedge_gap, block_2_4=block_2_4)
    weakness = _build_weakness_map_confirmation_subblock(hedge_gap=hedge_gap, block_2_6=block_2_6)
    aggregate = _build_aggregate_pre_stress_confirmation(hidden=hidden, weakness=weakness)
    return {
        "hidden_exposure": hidden,
        "weakness_map": weakness,
        "aggregate_confirmation": aggregate,
    }


def _build_hidden_exposure_confirmation_subblock(
    *,
    hedge_gap: dict[str, Any],
    block_2_4: dict[str, Any] | None,
) -> dict[str, Any]:
    if not _is_block_2_4_attached(block_2_4):
        return {"status": "not_applicable", "reason_en": "block_2_4_not_attached"}

    confirmations = _hedge_gap_hidden_exposure_confirmations(hedge_gap)
    if confirmations:
        statuses = [
            str(row.get("confirmation_status") or "unavailable")
            for row in confirmations
            if isinstance(row, dict)
        ]
        return {
            "status": _aggregate_confirmation_statuses(statuses),
            "reason_en": (
                f"Block 2.4 pre-stress confirmation copied from hedge_gap hidden_exposure_confirmation "
                f"({len(confirmations)} alert links)."
            ),
            "confirmation_rows": confirmations,
        }

    return {
        "status": "preliminary",
        "reason_en": "Block 2.4 attached but hedge_gap hidden_exposure_confirmation is not populated yet.",
    }


def _build_weakness_map_confirmation_subblock(
    *,
    hedge_gap: dict[str, Any],
    block_2_6: dict[str, Any] | None,
) -> dict[str, Any]:
    if not _is_block_2_6_attached(block_2_6):
        return {"status": "not_applicable", "reason_en": "block_2_6_not_attached"}

    confirmations = _hedge_gap_weakness_map_confirmations(hedge_gap)
    if confirmations:
        statuses = [
            str(row.get("confirmation_status") or "unavailable")
            for row in confirmations
            if isinstance(row, dict)
        ]
        return {
            "status": _aggregate_confirmation_statuses(statuses),
            "reason_en": (
                f"Block 2.6 pre-stress confirmation copied from hedge_gap weakness_map_confirmation "
                f"({len(confirmations)} risk-type links)."
            ),
            "confirmation_rows": confirmations,
        }

    return {
        "status": "preliminary",
        "reason_en": "Block 2.6 attached but hedge_gap weakness_map_confirmation is not populated yet.",
    }


def _hedge_gap_hidden_exposure_confirmations(hedge_gap: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != _BLOCK_3_3_VERSION:
        return []
    raw = hedge_gap.get("hidden_exposure_confirmation")
    if not isinstance(raw, list):
        return []
    return [row for row in raw if isinstance(row, dict)]


def _hedge_gap_weakness_map_confirmations(hedge_gap: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != _BLOCK_3_3_VERSION:
        return []
    raw = hedge_gap.get("weakness_map_confirmation")
    if not isinstance(raw, list):
        return []
    return [row for row in raw if isinstance(row, dict)]


def _build_aggregate_pre_stress_confirmation(
    *,
    hidden: dict[str, Any],
    weakness: dict[str, Any],
) -> dict[str, Any]:
    hidden_status = str(hidden.get("status") or "unavailable")
    weakness_status = str(weakness.get("status") or "unavailable")
    if hidden_status == "not_applicable" and weakness_status == "not_applicable":
        return {
            "status": "unavailable",
            "reason_en": "Neither Block 2.4 nor Block 2.6 pre-stress bridges were attached.",
        }

    statuses = [
        status
        for status in (hidden_status, weakness_status)
        if status != "not_applicable"
    ]
    return {
        "status": _aggregate_confirmation_statuses(statuses),
        "reason_en": "Aggregate pre-stress confirmation from attached Block 2.4 / 2.6 bridges.",
    }


def _derive_legacy_fallback_used(stress_report: dict[str, Any]) -> bool:
    """True only when Core MVP fields were satisfied from legacy ``stress_scorecard_v1``."""
    del stress_report
    return False


def _derive_limitations(
    *,
    historical_rows: list[Any],
    top_risk_contributors: dict[str, Any],
    hedge_gap: dict[str, Any],
    main_hedge_gap: dict[str, Any],
) -> list[str]:
    limitations: list[str] = []
    if top_risk_contributors.get("availability") != "available":
        reason = top_risk_contributors.get("reason_en")
        limitations.append(f"risk_contribution_unavailable:{reason or 'unknown'}")
    if _has_partial_historical_coverage(historical_rows):
        limitations.append("partial_historical_episode_coverage")
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != _BLOCK_3_3_VERSION:
        limitations.append("hedge_gap_analysis_v1_unavailable")
    elif main_hedge_gap.get("availability") != "available":
        limitations.append("main_hedge_gap_unavailable")
    elif hedge_gap.get("block_status") == "unavailable":
        limitations.append("hedge_gap_block_unavailable")
    return limitations


def _has_partial_historical_coverage(historical_rows: list[Any]) -> bool:
    if not historical_rows:
        return False
    unavailable = 0
    for row in historical_rows:
        if not isinstance(row, dict):
            continue
        if row.get("availability") in {"unavailable", "insufficient_data"}:
            unavailable += 1
    return 0 < unavailable < len(historical_rows)


def _derive_block_status(
    *,
    stress_results: dict[str, Any],
    worst_synthetic_scenario: dict[str, Any],
    worst_historical_scenario: dict[str, Any],
    historical_rows: list[Any],
    top_risk_contributors: dict[str, Any],
    hedge_gap: dict[str, Any],
    warnings: list[str],
    trust: dict[str, Any],
) -> str:
    env = stress_results.get("envelope") if isinstance(stress_results.get("envelope"), dict) else None
    if not isinstance(stress_results, dict) or stress_results.get("version") != _BLOCK_3_2_VERSION or not env:
        return "unavailable"
    if _has_fatal_trust_block(trust):
        return "unavailable"

    worst_syn_ok = worst_synthetic_scenario.get("availability") == "available"
    worst_hist_ok = worst_historical_scenario.get("availability") == "available"
    if not worst_syn_ok and not worst_hist_ok:
        return "unavailable"

    partial_triggers = (
        not worst_syn_ok
        or not worst_hist_ok
        or not _hedge_gap_usable(hedge_gap)
        or _has_partial_historical_coverage(historical_rows)
        or top_risk_contributors.get("availability") != "available"
        or bool(warnings)
    )
    if partial_triggers:
        return "partial"

    hg_status = hedge_gap.get("block_status") if isinstance(hedge_gap, dict) else None
    if hg_status not in {"ok", "partial"}:
        return "partial"
    return "ok"


def _has_fatal_trust_block(trust: dict[str, Any]) -> bool:
    if not isinstance(trust, dict) or not trust:
        return False
    if trust.get("fatal") is True:
        return True
    status = str(trust.get("status") or "").strip().lower()
    return status in {"fatal", "blocked", "unavailable"}


def _hedge_gap_usable(hedge_gap: dict[str, Any]) -> bool:
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != _BLOCK_3_3_VERSION:
        return False
    return hedge_gap.get("block_status") in {"ok", "partial"}


def _empty_stress_coverage() -> dict[str, Any]:
    return {
        "n_synthetic_available": 0,
        "n_synthetic_total": 0,
        "n_historical_available": 0,
        "n_historical_total": 0,
        "fraction_synthetic_available": None,
        "fraction_historical_available": None,
    }


def _derive_stress_coverage(
    *,
    synthetic_rows: list[Any],
    historical_rows: list[Any],
    scenario_library: dict[str, Any] | None,
) -> dict[str, Any]:
    n_synthetic_available = sum(
        1
        for row in synthetic_rows
        if isinstance(row, dict) and row.get("availability") == "available"
    )
    if synthetic_rows:
        n_synthetic_total = len(synthetic_rows)
    elif isinstance(scenario_library, dict):
        syn_ids = scenario_library.get("synthetic_ids")
        n_synthetic_total = len(syn_ids) if isinstance(syn_ids, list) else 0
    else:
        n_synthetic_total = 0

    n_historical_available = sum(
        1 for row in historical_rows if isinstance(row, dict) and _historical_row_has_usable_max_dd(row)
    )
    if historical_rows:
        n_historical_total = len(historical_rows)
    elif isinstance(scenario_library, dict):
        hist_ids = scenario_library.get("historical_ids")
        n_historical_total = len(hist_ids) if isinstance(hist_ids, list) else 0
    else:
        n_historical_total = 0

    return {
        "n_synthetic_available": n_synthetic_available,
        "n_synthetic_total": n_synthetic_total,
        "n_historical_available": n_historical_available,
        "n_historical_total": n_historical_total,
        "fraction_synthetic_available": (
            n_synthetic_available / n_synthetic_total if n_synthetic_total > 0 else None
        ),
        "fraction_historical_available": (
            n_historical_available / n_historical_total if n_historical_total > 0 else None
        ),
    }


def _historical_row_has_usable_max_dd(row: dict[str, Any]) -> bool:
    if row.get("availability") != "available":
        return False
    dd = row.get("drawdown_pct")
    return isinstance(dd, (int, float))


def _worst_selector_consistency_limitations(
    *,
    worst_syn: dict[str, Any] | None,
    worst_hist: dict[str, Any] | None,
    synthetic_rows: list[Any],
    historical_rows: list[Any],
) -> list[str]:
    """Detect envelope vs row-list drift; Block 3.4 still copies envelope (no recompute)."""
    out: list[str] = []
    if isinstance(worst_syn, dict) and worst_syn.get("scenario_id") is not None:
        syn_id = worst_syn.get("scenario_id")
        env_loss = worst_syn.get("portfolio_loss_pct")
        available_syn = [
            r
            for r in synthetic_rows
            if isinstance(r, dict)
            and r.get("availability") == "available"
            and isinstance(r.get("portfolio_pnl_pct"), (int, float))
        ]
        if available_syn:
            row_by_id = next((r for r in available_syn if r.get("scenario_id") == syn_id), None)
            if row_by_id is not None and env_loss != row_by_id.get("portfolio_pnl_pct"):
                out.append("worst_synthetic_envelope_loss_mismatch")
            min_row = min(available_syn, key=lambda r: float(r["portfolio_pnl_pct"]))
            if min_row.get("scenario_id") != syn_id:
                out.append("worst_synthetic_envelope_id_not_min_pnl")

    if isinstance(worst_hist, dict) and worst_hist.get("episode") is not None:
        ep = worst_hist.get("episode")
        env_dd = worst_hist.get("drawdown_pct")
        available_hist = [
            r
            for r in historical_rows
            if isinstance(r, dict) and _historical_row_has_usable_max_dd(r)
        ]
        if available_hist:
            row_by_ep = next((r for r in available_hist if r.get("episode") == ep), None)
            if row_by_ep is not None and env_dd != row_by_ep.get("drawdown_pct"):
                out.append("worst_historical_envelope_drawdown_mismatch")
            min_row = min(available_hist, key=lambda r: float(r["drawdown_pct"]))
            if min_row.get("episode") != ep:
                out.append("worst_historical_envelope_episode_not_min_max_dd")
    return out


def _build_worst_synthetic_block(worst_syn: dict[str, Any] | None) -> dict[str, Any]:
    base = {
        "selection_metric": _WORST_SYNTHETIC_SELECTION_METRIC,
        "selection_source": _ENVELOPE_SELECTION_SOURCE,
    }
    if not isinstance(worst_syn, dict) or worst_syn.get("scenario_id") is None:
        return {
            **base,
            "availability": "unavailable",
            "reason_en": "worst_synthetic_unavailable",
        }
    loss = worst_syn.get("portfolio_loss_pct")
    if not isinstance(loss, (int, float)):
        return {
            **base,
            "availability": "unavailable",
            "reason_en": "worst_synthetic_loss_non_numeric",
            "scenario_id": worst_syn.get("scenario_id"),
        }
    return {
        **base,
        "availability": "available",
        "scenario_id": worst_syn.get("scenario_id"),
        "portfolio_loss_pct": loss,
    }


def _build_worst_historical_block(worst_hist: dict[str, Any] | None) -> dict[str, Any]:
    base = {
        "selection_metric": _WORST_HISTORICAL_SELECTION_METRIC,
        "selection_source": _ENVELOPE_SELECTION_SOURCE,
    }
    if not isinstance(worst_hist, dict) or worst_hist.get("episode") is None:
        return {
            **base,
            "availability": "unavailable",
            "reason_en": "worst_historical_unavailable",
        }
    drawdown = worst_hist.get("drawdown_pct")
    if not isinstance(drawdown, (int, float)):
        return {
            **base,
            "availability": "unavailable",
            "reason_en": "worst_historical_drawdown_non_numeric",
            "episode": worst_hist.get("episode"),
        }
    return {
        **base,
        "availability": "available",
        "episode": worst_hist.get("episode"),
        "portfolio_loss_pct": worst_hist.get("portfolio_loss_pct"),
        "drawdown_pct": drawdown,
    }


def _build_portfolio_loss_summary(
    *,
    worst_syn: dict[str, Any] | None,
    worst_hist: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(worst_syn, dict) and not isinstance(worst_hist, dict):
        return {"availability": "unavailable", "reason_en": "loss_summary_unavailable"}
    return {
        "availability": "available",
        "synthetic": (
            {
                "scenario_id": worst_syn.get("scenario_id"),
                "portfolio_pnl_pct": worst_syn.get("portfolio_loss_pct"),
            }
            if isinstance(worst_syn, dict)
            else {"availability": "unavailable", "reason_en": "worst_synthetic_unavailable"}
        ),
        "historical": (
            {
                "episode": worst_hist.get("episode"),
                "pnl_real_episode": worst_hist.get("portfolio_loss_pct"),
            }
            if isinstance(worst_hist, dict)
            else {"availability": "unavailable", "reason_en": "worst_historical_unavailable"}
        ),
    }


def _build_historical_drawdown_summary(*, worst_hist: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(worst_hist, dict):
        return {"availability": "unavailable", "reason_en": "worst_historical_unavailable"}
    return {
        "availability": "available",
        "episode": worst_hist.get("episode"),
        "max_dd": worst_hist.get("drawdown_pct"),
    }


def _build_loss_contribution_summary(
    *,
    top_loss_contributors: dict[str, Any],
    synthetic_rows: list[Any],
    historical_rows: list[Any],
) -> dict[str, Any]:
    """v1.1 alias of ``top_loss_contributors`` plus ``loss_concentration_top3_share`` when computable."""
    out: dict[str, Any] = {
        "availability": top_loss_contributors.get("availability"),
    }
    if top_loss_contributors.get("availability") != "available":
        out["reason_en"] = top_loss_contributors.get("reason_en")
        return out

    syn_block = top_loss_contributors.get("synthetic")
    if isinstance(syn_block, dict) and syn_block.get("availability") != "unavailable":
        syn_summary = dict(syn_block)
        syn_id = syn_block.get("scenario_id")
        pnl_by_asset = _loss_contribution_pnl_by_asset(
            synthetic_rows,
            match_key="scenario_id",
            match_value=syn_id,
        )
        share = _compute_loss_concentration_top3_share(
            list(syn_block.get("top3_loss_assets") or []),
            pnl_by_asset,
        )
        if share is not None:
            syn_summary["loss_concentration_top3_share"] = share
        out["synthetic"] = syn_summary
    else:
        out["synthetic"] = syn_block

    hist_block = top_loss_contributors.get("historical")
    if isinstance(hist_block, dict) and hist_block.get("availability") != "unavailable":
        hist_summary = dict(hist_block)
        episode = hist_block.get("episode")
        pnl_by_asset = _loss_contribution_pnl_by_asset(
            historical_rows,
            match_key="episode",
            match_value=episode,
        )
        share = _compute_loss_concentration_top3_share(
            list(hist_block.get("top3_loss_assets") or []),
            pnl_by_asset,
        )
        if share is not None:
            hist_summary["loss_concentration_top3_share"] = share
        out["historical"] = hist_summary
    else:
        out["historical"] = hist_block

    return out


def _loss_contribution_pnl_by_asset(
    rows: list[Any],
    *,
    match_key: str,
    match_value: object,
) -> dict[str, float] | None:
    if match_value is None:
        return None
    for row in rows:
        if not isinstance(row, dict) or row.get(match_key) != match_value:
            continue
        lc = row.get("loss_contribution")
        if not isinstance(lc, dict) or lc.get("availability") != "available":
            continue
        pnl_by_asset = lc.get("pnl_by_asset_pct")
        if not isinstance(pnl_by_asset, dict) or not pnl_by_asset:
            continue
        out: dict[str, float] = {}
        for ticker, pnl in pnl_by_asset.items():
            if isinstance(pnl, (int, float)) and math.isfinite(float(pnl)):
                out[str(ticker)] = float(pnl)
        return out or None
    return None


def _gross_loss_from_pnl_by_asset(pnl_by_asset: dict[str, float]) -> float | None:
    negatives = [abs(pnl) for pnl in pnl_by_asset.values() if pnl < 0]
    if not negatives:
        return None
    gross = sum(negatives)
    if gross <= 0.0 or not math.isfinite(gross):
        return None
    return gross


def _sum_abs_pnl_from_hurt(top3_loss_assets: list[dict[str, Any]]) -> float | None:
    total = 0.0
    found = False
    for row in top3_loss_assets[:3]:
        if not isinstance(row, dict):
            continue
        pnl = row.get("pnl_pct")
        if isinstance(pnl, (int, float)) and math.isfinite(float(pnl)):
            total += abs(float(pnl))
            found = True
    if not found:
        return None
    return total


def _compute_loss_concentration_top3_share(
    top3_loss_assets: list[dict[str, Any]],
    pnl_by_asset: dict[str, float] | None,
) -> float | None:
    if not top3_loss_assets:
        return None
    gross_loss = _gross_loss_from_pnl_by_asset(pnl_by_asset) if pnl_by_asset else None
    if gross_loss is None:
        return None
    top3_abs = _sum_abs_pnl_from_hurt(top3_loss_assets)
    if top3_abs is None:
        return None
    share = top3_abs / gross_loss
    if not math.isfinite(share):
        return None
    return share


def _build_risk_contribution_summary(
    *,
    top_risk_contributors: dict[str, Any],
    top_loss_contributors: dict[str, Any],
) -> dict[str, Any]:
    """v1.1 alias of ``top_risk_contributors`` plus ``rc_overlap_with_loss_contributors``."""
    out = dict(top_risk_contributors)
    if out.get("availability") != "available":
        return out

    loss_syn = top_loss_contributors.get("synthetic")
    top3_loss = (
        list(loss_syn.get("top3_loss_assets") or [])
        if isinstance(loss_syn, dict) and loss_syn.get("availability") != "unavailable"
        else []
    )
    loss_tickers = _extract_loss_contributor_tickers(top3_loss)
    rc_tickers = _extract_rc_contributor_tickers(out.get("top3_rc_assets"))
    if loss_tickers and rc_tickers:
        out["rc_overlap_with_loss_contributors"] = bool(loss_tickers & rc_tickers)
    return out


def _extract_loss_contributor_tickers(top3_loss_assets: list[Any]) -> set[str]:
    tickers: set[str] = set()
    for row in top3_loss_assets:
        if isinstance(row, dict) and row.get("ticker"):
            tickers.add(str(row["ticker"]))
        elif isinstance(row, str) and row.strip():
            tickers.add(row.strip())
    return tickers


def _extract_rc_contributor_tickers(top3_rc_assets: Any) -> set[str]:
    if not isinstance(top3_rc_assets, list):
        return set()
    tickers: set[str] = set()
    for item in top3_rc_assets:
        if isinstance(item, str) and item.strip():
            tickers.add(item.strip())
        elif isinstance(item, dict) and item.get("ticker"):
            tickers.add(str(item["ticker"]))
    return tickers


def _build_top_loss_contributors(
    *,
    worst_syn: dict[str, Any] | None,
    worst_hist: dict[str, Any] | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"availability": "available", "synthetic": None, "historical": None}
    if isinstance(worst_syn, dict):
        out["synthetic"] = {
            "scenario_id": worst_syn.get("scenario_id"),
            "top3_loss_assets": list(worst_syn.get("top3_loss_assets") or []),
        }
    else:
        out["synthetic"] = {"availability": "unavailable", "reason_en": "worst_synthetic_unavailable"}
    if isinstance(worst_hist, dict):
        out["historical"] = {
            "episode": worst_hist.get("episode"),
            "top3_loss_assets": list(worst_hist.get("top3_loss_assets") or []),
        }
    else:
        out["historical"] = {"availability": "unavailable", "reason_en": "worst_historical_unavailable"}
    if not isinstance(worst_syn, dict) and not isinstance(worst_hist, dict):
        out["availability"] = "unavailable"
        out["reason_en"] = "top_loss_contributors_unavailable"
    return out


def _build_top_risk_contributors(
    *,
    synthetic_rows: list[Any],
    worst_synthetic_id: str | None,
) -> dict[str, Any]:
    if not synthetic_rows or not worst_synthetic_id:
        return {"availability": "unavailable", "reason_en": "risk_contribution_unavailable"}
    worst_row: dict[str, Any] | None = None
    for row in synthetic_rows:
        if isinstance(row, dict) and row.get("scenario_id") == worst_synthetic_id:
            worst_row = row
            break
    if worst_row is None:
        return {"availability": "unavailable", "reason_en": "worst_synthetic_row_missing"}
    rc = worst_row.get("risk_contribution")
    if not isinstance(rc, dict) or rc.get("availability") != "available":
        reason = rc.get("reason_en") if isinstance(rc, dict) else "risk_contribution_unavailable"
        return {"availability": "unavailable", "reason_en": reason}
    return {
        "availability": "available",
        "scenario_id": worst_synthetic_id,
        "top1_rc_asset": rc.get("top1_rc_asset"),
        "top1_rc_pct": rc.get("top1_rc_pct"),
        "top3_rc_assets": list(rc.get("top3_rc_assets") or []),
        "top3_rc_sum_pct": rc.get("top3_rc_sum_pct"),
    }


def _build_hedge_gap_summary(hedge_gap: dict[str, Any]) -> dict[str, Any]:
    """Compact Block 3.3 read-only summary for downstream consumers (v1.1 Session 05)."""
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != _BLOCK_3_3_VERSION:
        return {"availability": "unavailable", "reason_en": "hedge_gap_analysis_v1_unavailable"}

    summary = hedge_gap.get("summary") if isinstance(hedge_gap.get("summary"), dict) else {}
    main = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else None
    meta = {
        "hedge_gap_block_status": hedge_gap.get("block_status"),
        "hedge_gap_ruleset_version": hedge_gap.get("ruleset_version"),
        "protection_profile": summary.get("protection_profile"),
    }

    if not isinstance(main, dict):
        return {
            "availability": "unavailable",
            "reason_en": "main_hedge_gap_unavailable",
            **meta,
        }

    scenario_id = (
        summary.get("main_hedge_gap_scenario_id")
        or main.get("linked_scenario_id")
        or main.get("scenario_id")
    )
    return {
        "availability": "available",
        "main_hedge_gap_scenario_id": scenario_id,
        "main_hedge_gap_risk_type": main.get("risk_type"),
        "offset_coverage_ratio": main.get("offset_coverage_ratio"),
        **meta,
    }


def _build_factor_stress_attribution_summary(
    *,
    worst_syn: dict[str, Any] | None,
    conclusions: dict[str, Any],
    synthetic_rows: list[Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(worst_syn, dict):
        return {"availability": "unavailable", "reason_en": "worst_synthetic_unavailable"}
    drivers = list(worst_syn.get("top_factor_drivers") or [])
    if not drivers and synthetic_rows:
        syn_id = worst_syn.get("scenario_id")
        for row in synthetic_rows:
            if not isinstance(row, dict) or row.get("scenario_id") != syn_id:
                continue
            factor_attr = row.get("factor_attribution")
            if isinstance(factor_attr, dict) and factor_attr.get("availability") == "available":
                drivers = list(factor_attr.get("top_factor_drivers") or [])
            break
    helped_factors = conclusions.get("helped_factors_worst_scenario")
    helped_factors_list = list(helped_factors) if isinstance(helped_factors, list) else []
    return {
        "availability": "available",
        "scenario_id": worst_syn.get("scenario_id"),
        "top_factor_drivers": drivers,
        "helped_factors": helped_factors_list,
    }


def _build_assets_helped_hurt_summary(
    *,
    worst_syn: dict[str, Any] | None,
    hedge_gap: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(worst_syn, dict):
        return {"availability": "unavailable", "reason_en": "worst_synthetic_unavailable"}
    helped = list(worst_syn.get("helped_assets") or [])
    hurt_top3 = list(worst_syn.get("top3_loss_assets") or [])

    # Hedge gap: contribution-based helped/hurt for the main hedge gap risk type (when available).
    main_assets: dict[str, Any] | None = None
    main_row = _resolve_main_hedge_gap_row(hedge_gap)
    if main_row is not None:
        main_assets = {
            "risk_type": main_row.get("risk_type"),
            "linked_scenario_id": main_row.get("linked_scenario_id"),
            "assets_hurt": list(main_row.get("assets_hurt") or []),
            "assets_helped": list(main_row.get("assets_helped") or []),
        }

    return {
        "availability": "available",
        "worst_synthetic": {
            "scenario_id": worst_syn.get("scenario_id"),
            "assets_helped": helped,
            "assets_hurt_top3": hurt_top3,
        },
        "hedge_gap_main_area": main_assets,
    }


def _resolve_main_hedge_gap_row(hedge_gap: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != _BLOCK_3_3_VERSION:
        return None
    summary = hedge_gap.get("summary") if isinstance(hedge_gap.get("summary"), dict) else {}
    main = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else None
    if not isinstance(main, dict):
        return None
    risk_type = main.get("risk_type")
    linked_scenario_id = main.get("linked_scenario_id")
    if not risk_type or not linked_scenario_id:
        return None
    by_risk = hedge_gap.get("by_risk_type")
    if not isinstance(by_risk, list):
        return None
    for row in by_risk:
        if not isinstance(row, dict):
            continue
        if row.get("risk_type") == risk_type and row.get("linked_scenario_id") == linked_scenario_id:
            return row
    return None


def _build_offset_and_main_gap(hedge_gap: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != _BLOCK_3_3_VERSION:
        unavailable = {"availability": "unavailable", "reason_en": "hedge_gap_analysis_v1_unavailable"}
        return unavailable, unavailable

    summary = hedge_gap.get("summary") if isinstance(hedge_gap.get("summary"), dict) else {}
    main = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else None
    if not isinstance(main, dict):
        unavailable = {"availability": "unavailable", "reason_en": "main_hedge_gap_unavailable"}
        return unavailable, unavailable

    main_row = _resolve_main_hedge_gap_row(hedge_gap)
    offset = {
        "availability": "available",
        "risk_type": main.get("risk_type"),
        "linked_scenario_id": main.get("linked_scenario_id"),
        "offset_coverage_ratio": main.get("offset_coverage_ratio"),
        "gross_loss_from_assets_hurt": main_row.get("gross_loss_from_assets_hurt") if isinstance(main_row, dict) else None,
        "positive_contribution_from_assets_helped": (
            main_row.get("positive_contribution_from_assets_helped") if isinstance(main_row, dict) else None
        ),
    }
    main_gap = {
        "availability": "available",
        "weakest_protection_area": summary.get("weakest_protection_area"),
        "strongest_protection_area": summary.get("strongest_protection_area"),
        "main_hedge_gap": dict(main),
        "diagnosis_summary_en": summary.get("diagnosis_summary_en"),
    }
    return offset, main_gap


def _collect_data_quality_warnings(
    *,
    historical_rows: list[Any],
    hedge_gap: dict[str, Any],
    trust: dict[str, Any],
    conclusions: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []

    # Prefer explicit, user-facing trust summary lines if present.
    trust_lines = trust.get("user_summary_lines")
    if isinstance(trust_lines, list):
        for line in trust_lines:
            if isinstance(line, str) and line.strip():
                warnings.append(line.strip())

    # Block 3.3 warnings.
    if isinstance(hedge_gap, dict) and hedge_gap.get("version") == _BLOCK_3_3_VERSION:
        summary = hedge_gap.get("summary") if isinstance(hedge_gap.get("summary"), dict) else {}
        hg_warn = summary.get("data_quality_warnings")
        if isinstance(hg_warn, list):
            for w in hg_warn:
                if isinstance(w, str) and w.strip():
                    warnings.append(w.strip())

    # Block 3.2 conclusions warnings (historical methodology boundary + per-episode flags).
    conc_warn = conclusions.get("data_quality_warnings")
    if isinstance(conc_warn, list):
        for w in conc_warn:
            if isinstance(w, str) and w.strip():
                warnings.append(w.strip())

    # If historical episodes exist, but some are unavailable, add a compact warning.
    if historical_rows:
        unavailable_count = 0
        for row in historical_rows:
            if not isinstance(row, dict):
                continue
            avail = row.get("availability")
            if avail in {"unavailable", "insufficient_data"}:
                unavailable_count += 1
        if unavailable_count:
            warnings.append(f"historical_episodes_with_limited_data={unavailable_count}")

    # De-duplicate while preserving order.
    out: list[str] = []
    seen: set[str] = set()
    for w in warnings:
        if w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out


def _format_diagnosis_summary_en(
    *,
    worst_synthetic: dict[str, Any],
    worst_historical: dict[str, Any],
    main_hedge_gap: dict[str, Any],
    warnings: list[str],
) -> str | None:
    if worst_synthetic.get("availability") != "available" and worst_historical.get("availability") != "available":
        return None

    parts: list[str] = []
    if worst_synthetic.get("availability") == "available":
        sid = worst_synthetic.get("scenario_id")
        loss = worst_synthetic.get("portfolio_loss_pct")
        if sid is not None and isinstance(loss, (int, float)):
            parts.append(f"Worst synthetic scenario is {sid} with portfolio loss {float(loss) * 100:.1f}%.")
    if worst_historical.get("availability") == "available":
        ep = worst_historical.get("episode")
        dd = worst_historical.get("drawdown_pct")
        if ep is not None and isinstance(dd, (int, float)):
            parts.append(f"Worst historical episode is {ep} with max drawdown {float(dd) * 100:.1f}%.")

    if main_hedge_gap.get("availability") == "available":
        mhg = main_hedge_gap.get("main_hedge_gap")
        if isinstance(mhg, dict):
            risk_type = mhg.get("risk_type")
            ratio = mhg.get("offset_coverage_ratio")
            if risk_type and isinstance(ratio, (int, float)):
                parts.append(
                    f"Main hedge gap is {risk_type}: helped assets offset about {float(ratio) * 100:.1f}% of gross losses in the mapped stress."
                )

    if warnings:
        parts.append("Data quality warnings are present; interpret historical episodes and attributions with caution where flagged.")

    return " ".join(parts) if parts else None


def _empty_stress_diagnosis(reason: str) -> dict[str, Any]:
    return {
        "headline": None,
        "diagnosis_summary_en": None,
        "diagnosis_confidence": "unavailable",
        "confidence_reason": reason,
        "confidence_reason_en": f"Stress scorecard unavailable: {reason}.",
        "key_findings": [],
    }


def _empty_problem_classification_signals(reason: str) -> dict[str, Any]:
    return {
        "availability": "unavailable",
        "reason_en": reason,
        "stress_severity": None,
        "main_gap_risk_type": None,
        "worst_synthetic_id": None,
        "worst_historical_episode": None,
        "diagnosis_confidence": "unavailable",
    }


def _loss_severity_absolute(pnl_pct: float | None) -> str:
    """Magnitude-only severity (diagnostic mode); mirrors stress.py."""
    if pnl_pct is None or not isinstance(pnl_pct, (int, float)) or not math.isfinite(float(pnl_pct)):
        return "unknown"
    p = float(pnl_pct)
    if p <= -0.25:
        return "high"
    if p <= -0.10:
        return "moderate"
    return "low"


_LOSS_SEVERITY_RANK = {"high": 3, "moderate": 2, "low": 1, "unknown": 0}


def _max_loss_severity(*severities: str | None) -> str:
    best = "unknown"
    score = -1
    for raw in severities:
        if not raw:
            continue
        label = str(raw).lower()
        rank = _LOSS_SEVERITY_RANK.get(label, 0)
        if rank > score:
            score = rank
            best = label if label in _LOSS_SEVERITY_RANK else "unknown"
    return best


def _build_problem_classification_signals(
    *,
    block_status: str,
    worst_synthetic: dict[str, Any],
    worst_historical: dict[str, Any],
    hedge_gap_summary: dict[str, Any],
    stress_diagnosis: dict[str, Any],
    loss_gate_mode: str,
) -> dict[str, Any]:
    """Compact machine hints for Problem Classification (v1.1 Session 08)."""
    diagnosis_confidence = str(stress_diagnosis.get("diagnosis_confidence") or "unavailable")
    if block_status == "unavailable":
        return _empty_problem_classification_signals("block_unavailable")

    severities: list[str] = []
    worst_synthetic_id: str | None = None
    worst_historical_episode: str | None = None

    if worst_synthetic.get("availability") == "available":
        worst_synthetic_id = (
            str(worst_synthetic["scenario_id"])
            if worst_synthetic.get("scenario_id") is not None
            else None
        )
        syn_loss = worst_synthetic.get("portfolio_loss_pct")
        severities.append(
            _loss_severity_absolute(
                float(syn_loss) if isinstance(syn_loss, (int, float)) else None
            )
        )

    if worst_historical.get("availability") == "available":
        ep = worst_historical.get("episode")
        worst_historical_episode = str(ep) if ep is not None else None
        hist_vals = (
            worst_historical.get("drawdown_pct"),
            worst_historical.get("portfolio_loss_pct"),
        )
        hist_sev = "unknown"
        for value in hist_vals:
            if isinstance(value, (int, float)) and math.isfinite(float(value)):
                hist_sev = _loss_severity_absolute(float(value))
                if hist_sev in {"moderate", "high"}:
                    break
        severities.append(hist_sev)

    main_gap_risk_type: str | None = None
    if hedge_gap_summary.get("availability") == "available":
        rt = hedge_gap_summary.get("main_hedge_gap_risk_type")
        main_gap_risk_type = str(rt) if rt is not None else None

    return {
        "availability": "available",
        "stress_severity": _max_loss_severity(*severities),
        "main_gap_risk_type": main_gap_risk_type,
        "worst_synthetic_id": worst_synthetic_id,
        "worst_historical_episode": worst_historical_episode,
        "diagnosis_confidence": diagnosis_confidence,
    }


def _empty_candidate_comparison_targets(reason: str) -> dict[str, Any]:
    return {
        "availability": "unavailable",
        "reason_en": reason,
        "worst_synthetic_scenario_id": None,
        "main_hedge_gap_scenario_id": None,
        "compare_offset_coverage": False,
    }


def _build_candidate_comparison_targets(
    *,
    block_status: str,
    worst_synthetic: dict[str, Any],
    hedge_gap_summary: dict[str, Any],
) -> dict[str, Any]:
    """Stress slice ids and comparison flags for Candidate Comparison (v1.1 Session 09)."""
    if block_status == "unavailable":
        return _empty_candidate_comparison_targets("block_unavailable")

    worst_synthetic_scenario_id: str | None = None
    if worst_synthetic.get("availability") == "available":
        sid = worst_synthetic.get("scenario_id")
        worst_synthetic_scenario_id = str(sid) if sid is not None else None

    main_hedge_gap_scenario_id: str | None = None
    compare_offset_coverage = False
    if hedge_gap_summary.get("availability") == "available":
        gap_sid = hedge_gap_summary.get("main_hedge_gap_scenario_id")
        main_hedge_gap_scenario_id = str(gap_sid) if gap_sid is not None else None
        ratio = hedge_gap_summary.get("offset_coverage_ratio")
        compare_offset_coverage = isinstance(ratio, (int, float)) and math.isfinite(float(ratio))

    return {
        "availability": "available",
        "worst_synthetic_scenario_id": worst_synthetic_scenario_id,
        "main_hedge_gap_scenario_id": main_hedge_gap_scenario_id,
        "compare_offset_coverage": compare_offset_coverage,
    }


def _empty_ai_commentary_context(reason: str) -> dict[str, Any]:
    return {
        "availability": "unavailable",
        "reason_en": reason,
        "headline": None,
        "diagnosis_confidence": "unavailable",
        "worst_synthetic_scenario_id": None,
        "worst_historical_episode": None,
        "main_hedge_gap_scenario_id": None,
        "main_hedge_gap_risk_type": None,
        "protection_profile": None,
        "stress_scorecard_source": BLOCK_3_4_VERSION,
        "legacy_fallback_used": False,
        "forbidden_legacy_field_paths": list(AI_COMMENTARY_FORBIDDEN_LEGACY_FIELD_PATHS),
    }


def _build_ai_commentary_context(
    *,
    block_status: str,
    stress_diagnosis: dict[str, Any],
    worst_synthetic: dict[str, Any],
    worst_historical: dict[str, Any],
    hedge_gap_summary: dict[str, Any],
    legacy_fallback_used: bool,
    protection_profile: Any,
) -> dict[str, Any]:
    """Compact AI Commentary grounding slice (v1.1 Session 10)."""
    if block_status == "unavailable":
        return _empty_ai_commentary_context("block_unavailable")

    worst_synthetic_scenario_id: str | None = None
    if worst_synthetic.get("availability") == "available":
        sid = worst_synthetic.get("scenario_id")
        worst_synthetic_scenario_id = str(sid) if sid is not None else None

    worst_historical_episode: str | None = None
    if worst_historical.get("availability") == "available":
        ep = worst_historical.get("episode")
        worst_historical_episode = str(ep) if ep is not None else None

    main_hedge_gap_scenario_id: str | None = None
    main_hedge_gap_risk_type: str | None = None
    profile = protection_profile
    if hedge_gap_summary.get("availability") == "available":
        gap_sid = hedge_gap_summary.get("main_hedge_gap_scenario_id")
        main_hedge_gap_scenario_id = str(gap_sid) if gap_sid is not None else None
        rt = hedge_gap_summary.get("main_hedge_gap_risk_type")
        main_hedge_gap_risk_type = str(rt) if rt is not None else None
        if profile is None:
            profile = hedge_gap_summary.get("protection_profile")

    headline = stress_diagnosis.get("headline")
    headline_out = headline.strip() if isinstance(headline, str) and headline.strip() else None

    return {
        "availability": "available",
        "headline": headline_out,
        "diagnosis_confidence": str(stress_diagnosis.get("diagnosis_confidence") or "unavailable"),
        "worst_synthetic_scenario_id": worst_synthetic_scenario_id,
        "worst_historical_episode": worst_historical_episode,
        "main_hedge_gap_scenario_id": main_hedge_gap_scenario_id,
        "main_hedge_gap_risk_type": main_hedge_gap_risk_type,
        "protection_profile": profile,
        "stress_scorecard_source": BLOCK_3_4_VERSION,
        "legacy_fallback_used": bool(legacy_fallback_used),
        "forbidden_legacy_field_paths": list(AI_COMMENTARY_FORBIDDEN_LEGACY_FIELD_PATHS),
    }


def _derive_next_decision_uses(block_status: str) -> list[str]:
    if block_status in {"ok", "partial"}:
        return list(_NEXT_DECISION_USE_TOKENS)
    return []


def _build_relatively_resilient_scenarios(
    synthetic_rows: list[Any],
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for row in synthetic_rows:
        if not isinstance(row, dict) or row.get("availability") != "available":
            continue
        pnl = row.get("portfolio_loss_pct")
        scenario_id = row.get("scenario_id")
        if scenario_id is None or not isinstance(pnl, (int, float)):
            continue
        if float(pnl) >= 0.0:
            candidates.append(row)
    candidates.sort(
        key=lambda r: (-float(r["portfolio_loss_pct"]), str(r.get("scenario_id") or "")),
    )
    out: list[dict[str, Any]] = []
    for row in candidates[:limit]:
        out.append(
            {
                "scenario_id": row.get("scenario_id"),
                "portfolio_pnl_pct": row.get("portfolio_loss_pct"),
                "availability": "available",
            }
        )
    return out


def _build_less_damaging_scenarios(
    *,
    synthetic_rows: list[Any],
    worst_synthetic_loss_pct: float | None,
    exclude_scenario_ids: set[str],
    limit: int = 3,
) -> list[dict[str, Any]]:
    if not isinstance(worst_synthetic_loss_pct, (int, float)):
        return []
    worst_loss = float(worst_synthetic_loss_pct)
    candidates: list[dict[str, Any]] = []
    for row in synthetic_rows:
        if not isinstance(row, dict) or row.get("availability") != "available":
            continue
        pnl = row.get("portfolio_loss_pct")
        scenario_id = row.get("scenario_id")
        if scenario_id is None or not isinstance(pnl, (int, float)):
            continue
        sid = str(scenario_id)
        if sid in exclude_scenario_ids:
            continue
        if float(pnl) > worst_loss:
            candidates.append(row)
    candidates.sort(
        key=lambda r: (-float(r["portfolio_loss_pct"]), str(r.get("scenario_id") or "")),
    )
    return [
        {
            "scenario_id": row.get("scenario_id"),
            "portfolio_pnl_pct": row.get("portfolio_loss_pct"),
            "availability": "available",
        }
        for row in candidates[:limit]
    ]


def _derive_diagnosis_confidence(
    *,
    block_status: str,
    worst_synthetic: dict[str, Any],
    worst_historical: dict[str, Any],
    hedge_gap: dict[str, Any],
    hedge_gap_summary: dict[str, Any],
    top_risk_contributors: dict[str, Any],
    stress_coverage: dict[str, Any],
    warnings: list[str],
) -> tuple[str, str, str]:
    worst_syn_ok = worst_synthetic.get("availability") == "available"
    worst_hist_ok = worst_historical.get("availability") == "available"
    if block_status == "unavailable" or (not worst_syn_ok and not worst_hist_ok):
        return (
            "unavailable",
            "block_unavailable",
            "Stress scorecard is unavailable or worst-scenario selectors are missing.",
        )

    n_warnings = len(warnings)
    frac_syn = stress_coverage.get("fraction_synthetic_available")
    frac_hist = stress_coverage.get("fraction_historical_available")
    hg_status = hedge_gap.get("block_status") if isinstance(hedge_gap, dict) else None
    rc_ok = top_risk_contributors.get("availability") == "available"
    hg_summary_ok = hedge_gap_summary.get("availability") == "available"

    low_reasons: list[tuple[str, str]] = []
    if block_status == "partial":
        if not rc_ok:
            low_reasons.append(
                ("risk_contribution_unavailable", "Risk contribution is unavailable on the worst synthetic row.")
            )
        if not _hedge_gap_usable(hedge_gap) or not hg_summary_ok:
            low_reasons.append(
                ("hedge_gap_partial_or_unavailable", "Hedge gap evidence is partial or unavailable.")
            )
    if n_warnings > 4:
        low_reasons.append(
            ("many_data_quality_warnings", "More than four data-quality warnings reduce diagnosis confidence.")
        )
    if low_reasons:
        code, en = low_reasons[0]
        return "low", code, en

    if (
        block_status == "ok"
        and hg_status == "ok"
        and isinstance(frac_syn, (int, float))
        and float(frac_syn) >= 0.75
        and n_warnings <= 1
    ):
        return (
            "high",
            "stress_evidence_strong",
            "Worst scenarios, hedge gap, and synthetic coverage support a confident stress read.",
        )

    medium_bits: list[str] = []
    if block_status == "partial":
        medium_bits.append("scorecard status is partial")
    if isinstance(frac_hist, (int, float)) and float(frac_hist) < 0.75:
        medium_bits.append("historical episode coverage is incomplete")
    if 2 <= n_warnings <= 4:
        medium_bits.append("multiple data-quality warnings are present")
    if worst_syn_ok and worst_hist_ok and not medium_bits:
        medium_bits.append("stress evidence is usable but not fully clean")
    detail = "; ".join(medium_bits) if medium_bits else "stress evidence is usable with caveats"
    return "medium", "partial_stress_evidence", f"Diagnosis confidence is medium because {detail}."

def _build_stress_diagnosis_headline(
    *,
    block_status: str,
    worst_synthetic: dict[str, Any],
    worst_historical: dict[str, Any],
    hedge_gap_summary: dict[str, Any],
) -> str | None:
    if block_status not in {"ok", "partial"}:
        return None
    parts: list[str] = []
    if worst_synthetic.get("availability") == "available":
        sid = worst_synthetic.get("scenario_id")
        loss = worst_synthetic.get("portfolio_loss_pct")
        if sid is not None and isinstance(loss, (int, float)):
            parts.append(f"Worst synthetic stress is {sid} at {float(loss) * 100:.1f}% portfolio loss")
    if worst_historical.get("availability") == "available":
        ep = worst_historical.get("episode")
        dd = worst_historical.get("drawdown_pct")
        if ep is not None and isinstance(dd, (int, float)):
            parts.append(f"worst historical drawdown is {ep} at {float(dd) * 100:.1f}%")
    if hedge_gap_summary.get("availability") == "available":
        risk_type = hedge_gap_summary.get("main_hedge_gap_risk_type")
        if risk_type:
            parts.append(f"main hedge gap sits in {risk_type}")
    return "; ".join(parts) if parts else None


def _build_stress_diagnosis_key_findings(
    *,
    worst_synthetic: dict[str, Any],
    worst_historical: dict[str, Any],
    main_hedge_gap: dict[str, Any],
    factor_attr: dict[str, Any],
    warnings: list[str],
    limit: int = 5,
) -> list[str]:
    findings: list[str] = []
    if worst_synthetic.get("availability") == "available":
        sid = worst_synthetic.get("scenario_id")
        loss = worst_synthetic.get("portfolio_loss_pct")
        if sid is not None and isinstance(loss, (int, float)):
            findings.append(f"Worst synthetic scenario: {sid} ({float(loss) * 100:.1f}% loss).")
    if worst_historical.get("availability") == "available":
        ep = worst_historical.get("episode")
        dd = worst_historical.get("drawdown_pct")
        if ep is not None and isinstance(dd, (int, float)):
            findings.append(f"Worst historical episode: {ep} ({float(dd) * 100:.1f}% max drawdown).")
    if main_hedge_gap.get("availability") == "available":
        mhg = main_hedge_gap.get("main_hedge_gap")
        if isinstance(mhg, dict):
            risk_type = mhg.get("risk_type")
            ratio = mhg.get("offset_coverage_ratio")
            if risk_type and isinstance(ratio, (int, float)):
                findings.append(
                    f"Main hedge gap: {risk_type} with offset coverage about {float(ratio) * 100:.1f}%."
                )
    if factor_attr.get("availability") == "available":
        drivers = factor_attr.get("top_factor_drivers") or []
        if isinstance(drivers, list) and drivers:
            top = drivers[0]
            if isinstance(top, dict):
                label = top.get("factor") or top.get("factor_short") or top.get("beta_key")
                if label:
                    findings.append(f"Top factor driver on worst synthetic: {label}.")
    if warnings:
        findings.append("Data-quality warnings are present; interpret attributions with caution.")
    return findings[:limit]


def _build_stress_diagnosis(
    *,
    block_status: str,
    worst_synthetic: dict[str, Any],
    worst_historical: dict[str, Any],
    main_hedge_gap: dict[str, Any],
    hedge_gap: dict[str, Any],
    hedge_gap_summary: dict[str, Any],
    factor_attr: dict[str, Any],
    top_risk_contributors: dict[str, Any],
    stress_coverage: dict[str, Any],
    warnings: list[str],
    diagnosis_summary_en: str | None,
) -> dict[str, Any]:
    confidence, reason_code, reason_en = _derive_diagnosis_confidence(
        block_status=block_status,
        worst_synthetic=worst_synthetic,
        worst_historical=worst_historical,
        hedge_gap=hedge_gap,
        hedge_gap_summary=hedge_gap_summary,
        top_risk_contributors=top_risk_contributors,
        stress_coverage=stress_coverage,
        warnings=warnings,
    )
    headline = _build_stress_diagnosis_headline(
        block_status=block_status,
        worst_synthetic=worst_synthetic,
        worst_historical=worst_historical,
        hedge_gap_summary=hedge_gap_summary,
    )
    return {
        "headline": headline,
        "diagnosis_summary_en": diagnosis_summary_en,
        "diagnosis_confidence": confidence,
        "confidence_reason": reason_code,
        "confidence_reason_en": reason_en,
        "key_findings": _build_stress_diagnosis_key_findings(
            worst_synthetic=worst_synthetic,
            worst_historical=worst_historical,
            main_hedge_gap=main_hedge_gap,
            factor_attr=factor_attr,
            warnings=warnings,
        ),
    }


def collect_forbidden_english_phrases(block: dict[str, Any]) -> list[str]:
    """Return forbidden mandate-adjacent phrases found in string leaves (contract tests)."""
    found: list[str] = []

    def _walk(obj: object) -> None:
        if isinstance(obj, dict):
            for value in obj.values():
                _walk(value)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
        elif isinstance(obj, str):
            lower = obj.lower()
            for phrase in _FORBIDDEN_ENGLISH_PHRASES:
                if phrase in lower and phrase not in found:
                    found.append(phrase)

    _walk(block)
    return found

