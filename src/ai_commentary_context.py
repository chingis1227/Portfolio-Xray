"""Grounding context for product-facing AI Commentary.

This module builds a deterministic evidence bundle that an AI commentary layer
may consume later. It does not call an LLM, calculate metrics, set decisions,
or change any existing decision/selection contract.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AI_COMMENTARY_CONTEXT_VERSION = "ai_commentary_context_v1"
AI_COMMENTARY_CONTEXT_FILENAME = "ai_commentary_context.json"
PURPOSE_GROUNDED_DECISION_CONTEXT = "grounded_ai_commentary_context"
PURPOSE_DIAGNOSIS_GROUNDING_ONLY = "diagnosis_grounding_only"

HEDGE_GAP_CONTEXT_VERSION = "hedge_gap_context_v1"
HEDGE_GAP_V1_BLOCK = "hedge_gap_analysis_v1"
HEDGE_GAP_V1_VERSION = "hedge_gap_analysis_v1"
HEDGE_GAP_SOURCE_V1 = HEDGE_GAP_V1_BLOCK
HEDGE_GAP_SOURCE_LEGACY = "stress_conclusions.hedge_gap_status"
HEDGE_GAP_COMPARISON_VERSION = "hedge_gap_comparison_v1"
STRESS_SCORECARD_CONTEXT_VERSION = "current_portfolio_stress_scorecard_context_v1"
SCORECARD_V1_BLOCK = "current_portfolio_stress_scorecard_v1"
SCORECARD_V1_VERSION = "current_portfolio_stress_scorecard_v1"
STRESS_SCORECARD_SOURCE_V1 = SCORECARD_V1_BLOCK
STRESS_SCORECARD_SOURCE_LEGACY = "stress_scorecard_v1"
_WEAK_PROTECTION_STATUSES = frozenset({"weak_protection", "no_protection"})

ALLOWED_SOURCE_ARTIFACTS: tuple[str, ...] = (
    "portfolio_xray.json",
    "stress_report.json",
    "problem_classification.json",
    "candidate_launchpad.json",
    "candidate_comparison.json",
    "current_vs_candidate.json",
    "selection_decision.json",
    "decision_verdict.json",
    "action_plan.json",
    "monitoring_diff.json",
)

FORBIDDEN_CLAIM_CATEGORIES: tuple[str, ...] = (
    "new_metric_calculation",
    "unsupported_verdict",
    "trade_execution_instruction",
    "schema_rename",
    "data_quality_status_creation",
    "performance_guarantee",
    "optimizer_formula_change",
    "unstated_tax_advice",
)

REQUIRED_GROUNDING_RULES: tuple[str, ...] = (
    "Use only values and statuses present in allowed source artifacts.",
    "Every material claim must cite an artifact and field path.",
    "Do not compute new metrics, thresholds, rankings, or optimizer results.",
    "Do not rename or reinterpret Selection Engine statuses.",
    "Do not issue trade execution instructions or binding investment advice.",
    "State evidence gaps and confidence limitations when source artifacts warn or are missing.",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _source_name(name: str, doc: dict[str, Any] | None) -> str | None:
    return name if isinstance(doc, dict) else None


def _append_reference(
    refs: list[dict[str, Any]],
    *,
    artifact: str,
    field_path: str,
    value: Any = None,
    summary: str | None = None,
) -> None:
    ref: dict[str, Any] = {"artifact": artifact, "field_path": field_path}
    if value is not None:
        ref["value"] = value
    if summary:
        ref["summary"] = summary
    refs.append(ref)


def _problem_refs(problem_classification: dict[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(problem_classification, dict):
        return refs
    problems = problem_classification.get("problems")
    if isinstance(problems, list):
        for idx, problem in enumerate(problems[:5]):
            if not isinstance(problem, dict):
                continue
            _append_reference(
                refs,
                artifact="problem_classification.json",
                field_path=f"problems[{idx}]",
                value={
                    "problem_id": problem.get("problem_id"),
                    "severity": problem.get("severity"),
                    "status": problem.get("status"),
                },
            )
    return refs


def _launchpad_refs(candidate_launchpad: dict[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(candidate_launchpad, dict):
        return refs
    cards = candidate_launchpad.get("cards")
    if isinstance(cards, list):
        for idx, card in enumerate(cards[:5]):
            if not isinstance(card, dict):
                continue
            _append_reference(
                refs,
                artifact="candidate_launchpad.json",
                field_path=f"cards[{idx}]",
                value={
                    "card_id": card.get("card_id"),
                    "goal": card.get("goal"),
                    "method_id": card.get("method_id"),
                },
            )
    return refs


def _comparison_refs(
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(comparison, dict):
        _append_reference(
            refs,
            artifact="candidate_comparison.json",
            field_path="comparison_baseline_candidate_id",
            value=comparison.get("comparison_baseline_candidate_id"),
        )
        _append_reference(
            refs,
            artifact="candidate_comparison.json",
            field_path="candidate_menu.factory_evidence_status",
            value=(comparison.get("candidate_menu") or {}).get("factory_evidence_status")
            if isinstance(comparison.get("candidate_menu"), dict)
            else None,
        )
    if isinstance(current_vs_candidate, dict):
        _append_reference(
            refs,
            artifact="current_vs_candidate.json",
            field_path="view_mode",
            value=current_vs_candidate.get("view_mode"),
        )
        for idx, row in enumerate(current_vs_candidate.get("comparisons") or []):
            if not isinstance(row, dict):
                continue
            _append_reference(
                refs,
                artifact="current_vs_candidate.json",
                field_path=f"comparisons[{idx}]",
                value={
                    "candidate_id": row.get("candidate_id"),
                    "status": row.get("status"),
                    "dimension_count": len(row.get("dimensions") or []),
                },
            )
    return refs


def _decision_refs(
    selection: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
    action: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(selection, dict):
        _append_reference(
            refs,
            artifact="selection_decision.json",
            field_path="decision_status",
            value=selection.get("decision_status"),
        )
        _append_reference(
            refs,
            artifact="selection_decision.json",
            field_path="favored_candidate_id",
            value=selection.get("favored_candidate_id"),
        )
        no_trade = selection.get("no_trade")
        if isinstance(no_trade, dict):
            _append_reference(
                refs,
                artifact="selection_decision.json",
                field_path="no_trade",
                value={
                    "evaluated": no_trade.get("evaluated"),
                    "baseline_candidate_id": no_trade.get("baseline_candidate_id"),
                    "target_candidate_id": no_trade.get("target_candidate_id"),
                },
            )
    if isinstance(decision_verdict, dict):
        _append_reference(
            refs,
            artifact="decision_verdict.json",
            field_path="verdict_id",
            value=decision_verdict.get("verdict_id"),
        )
        _append_reference(
            refs,
            artifact="decision_verdict.json",
            field_path="confidence",
            value=decision_verdict.get("confidence"),
        )
    if isinstance(action, dict):
        _append_reference(
            refs,
            artifact="action_plan.json",
            field_path="action_status",
            value=action.get("action_status"),
        )
    return refs


def _xray_refs(portfolio_xray: dict[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(portfolio_xray, dict):
        return refs
    _append_reference(
        refs,
        artifact="portfolio_xray.json",
        field_path="version",
        value=portfolio_xray.get("version"),
    )
    _append_reference(
        refs,
        artifact="portfolio_xray.json",
        field_path="diagnostic_only",
        value=portfolio_xray.get("diagnostic_only"),
    )
    block_2_6 = portfolio_xray.get("block_2_6_portfolio_weakness_map")
    if isinstance(block_2_6, dict):
        _append_reference(
            refs,
            artifact="portfolio_xray.json",
            field_path="block_2_6_portfolio_weakness_map.status",
            value=block_2_6.get("status"),
            summary=str(block_2_6.get("summary") or "")[:240] or None,
        )
        rule_version = (block_2_6.get("metadata") or {}).get("rule_version")
        if rule_version:
            _append_reference(
                refs,
                artifact="portfolio_xray.json",
                field_path="block_2_6_portfolio_weakness_map.metadata.rule_version",
                value=rule_version,
            )
        elevated: list[dict[str, Any]] = []
        for idx, risk in enumerate(block_2_6.get("risk_types") or []):
            if not isinstance(risk, dict):
                continue
            severity = str(risk.get("severity") or "")
            if severity not in {"High", "Medium"}:
                continue
            elevated.append(
                {
                    "index": idx,
                    "risk_type": risk.get("risk_type"),
                    "severity": severity,
                    "score_0_100": risk.get("score_0_100"),
                    "short_diagnosis": risk.get("short_diagnosis"),
                    "why_status": risk.get("why_status"),
                    "next_tests": risk.get("next_tests"),
                }
            )
        if elevated:
            _append_reference(
                refs,
                artifact="portfolio_xray.json",
                field_path="block_2_6_portfolio_weakness_map.risk_types",
                value=elevated[:5],
                summary="Elevated pre-stress vulnerability hypotheses from Block 2.6.",
            )
            for row in elevated[:3]:
                idx = row["index"]
                _append_reference(
                    refs,
                    artifact="portfolio_xray.json",
                    field_path=f"block_2_6_portfolio_weakness_map.risk_types[{idx}].short_diagnosis",
                    value=row.get("short_diagnosis"),
                    summary=str(row.get("why_status") or "")[:240] or None,
                )
    legacy = portfolio_xray.get("legacy_summary")
    if isinstance(legacy, dict):
        scope = legacy.get("_scope")
        if isinstance(scope, dict) and scope.get("product_surface") is not None:
            _append_reference(
                refs,
                artifact="portfolio_xray.json",
                field_path="legacy_summary._scope.product_surface",
                value=scope.get("product_surface"),
            )
    return refs


def _scorecard_v1_block(stress_report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(stress_report, dict):
        return None
    block = stress_report.get(SCORECARD_V1_BLOCK)
    if isinstance(block, dict) and block.get("version") == SCORECARD_V1_VERSION:
        return block
    return None


def _build_current_portfolio_stress_scorecard_context(
    stress_report: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Compact Block 3.4 stress scorecard grounding (v1-primary; legacy fallback only)."""
    v1 = _scorecard_v1_block(stress_report)
    if v1 is None or str(v1.get("block_status") or "") == "unavailable":
        legacy = (
            stress_report.get(STRESS_SCORECARD_SOURCE_LEGACY)
            if isinstance(stress_report, dict)
            else None
        )
        if isinstance(legacy, dict) and legacy.get("overall_status") is not None:
            return {
                "version": STRESS_SCORECARD_CONTEXT_VERSION,
                "stress_scorecard_source": STRESS_SCORECARD_SOURCE_LEGACY,
                "legacy_fallback_used": True,
                "block_status": None,
                "headline": None,
                "diagnosis_confidence": legacy.get("overall_confidence"),
                "legacy_overall_status": legacy.get("overall_status"),
                "forbidden_legacy_field_paths": [],
            }
        return None

    nested = v1.get("ai_commentary_context")
    nested = nested if isinstance(nested, dict) else {}
    stress_diagnosis = v1.get("stress_diagnosis")
    stress_diagnosis = stress_diagnosis if isinstance(stress_diagnosis, dict) else {}

    ctx: dict[str, Any] = {
        "version": STRESS_SCORECARD_CONTEXT_VERSION,
        "stress_scorecard_source": STRESS_SCORECARD_SOURCE_V1,
        "legacy_fallback_used": bool(v1.get("legacy_fallback_used")),
        "block_status": v1.get("block_status"),
        "ruleset_version": v1.get("ruleset_version"),
        "headline": nested.get("headline") or stress_diagnosis.get("headline"),
        "diagnosis_confidence": nested.get("diagnosis_confidence")
        or stress_diagnosis.get("diagnosis_confidence"),
        "worst_synthetic_scenario_id": nested.get("worst_synthetic_scenario_id"),
        "worst_historical_episode": nested.get("worst_historical_episode"),
        "main_hedge_gap_scenario_id": nested.get("main_hedge_gap_scenario_id"),
        "main_hedge_gap_risk_type": nested.get("main_hedge_gap_risk_type"),
        "protection_profile": nested.get("protection_profile") or v1.get("protection_profile"),
        "forbidden_legacy_field_paths": nested.get("forbidden_legacy_field_paths")
        or [],
    }
    if nested.get("availability") == "available":
        ctx["availability"] = "available"
    elif str(v1.get("block_status") or "") in {"ok", "partial"}:
        ctx["availability"] = "available"
    else:
        ctx["availability"] = "unavailable"
    return ctx


def _hedge_gap_v1_block(stress_report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(stress_report, dict):
        return None
    block = stress_report.get(HEDGE_GAP_V1_BLOCK)
    if isinstance(block, dict) and block.get("version") == HEDGE_GAP_V1_VERSION:
        return block
    return None


def _hedge_gap_comparison_slice(comparison: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(comparison, dict):
        return None
    hg = comparison.get("hedge_gap_comparison")
    if not isinstance(hg, dict) or hg.get("version") != HEDGE_GAP_COMPARISON_VERSION:
        return None
    compact: dict[str, Any] = {
        "version": hg.get("version"),
        "status": hg.get("status"),
        "baseline_candidate_id": hg.get("baseline_candidate_id"),
        "hedge_gap_source": hg.get("hedge_gap_source"),
        "comparison_candidate_ids": hg.get("comparison_candidate_ids"),
        "reason_code": hg.get("reason_code"),
    }
    pairwise = hg.get("pairwise")
    if isinstance(pairwise, list) and pairwise:
        compact["pairwise"] = [
            {
                "candidate_id": row.get("candidate_id"),
                "offset_coverage_ratio_delta": row.get("offset_coverage_ratio_delta"),
                "main_gap_score_delta": row.get("main_gap_score_delta"),
                "comparison_summary_en": row.get("comparison_summary_en"),
            }
            for row in pairwise[:5]
            if isinstance(row, dict)
        ]
    return compact


def _build_hedge_gap_context(
    stress_report: dict[str, Any] | None,
    comparison: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Compact Block 3.3 hedge-gap grounding (v1-primary; legacy status fallback only)."""
    v1 = _hedge_gap_v1_block(stress_report)
    comparison_slice = _hedge_gap_comparison_slice(comparison)
    ctx: dict[str, Any] = {
        "version": HEDGE_GAP_CONTEXT_VERSION,
        "hedge_gap_source": None,
        "legacy_fallback_used": False,
        "comparison": comparison_slice,
    }

    if v1 is not None and str(v1.get("block_status") or "") != "unavailable":
        summary = v1.get("summary") if isinstance(v1.get("summary"), dict) else {}
        main = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else {}
        by_risk = [row for row in (v1.get("by_risk_type") or []) if isinstance(row, dict)]
        weak_count = sum(
            1
            for row in by_risk
            if str(row.get("protection_status") or "") in _WEAK_PROTECTION_STATUSES
        )
        ctx.update(
            {
                "hedge_gap_source": HEDGE_GAP_SOURCE_V1,
                "block_status": v1.get("block_status"),
                "ruleset_version": v1.get("ruleset_version"),
                "protection_profile": summary.get("protection_profile"),
                "weakest_protection_area": summary.get("weakest_protection_area"),
                "strongest_protection_area": summary.get("strongest_protection_area"),
                "main_hedge_gap_risk_type": main.get("risk_type"),
                "main_hedge_gap_scenario_id": summary.get("main_hedge_gap_scenario_id")
                or main.get("linked_scenario_id"),
                "main_hedge_gap_offset_coverage_ratio": summary.get(
                    "main_hedge_gap_offset_coverage_ratio"
                )
                if summary.get("main_hedge_gap_offset_coverage_ratio") is not None
                else main.get("offset_coverage_ratio"),
                "main_hedge_gap_portfolio_loss_pct": summary.get("main_hedge_gap_portfolio_loss_pct")
                if summary.get("main_hedge_gap_portfolio_loss_pct") is not None
                else main.get("portfolio_loss_pct"),
                "main_hedge_gap_protection_status": main.get("protection_status"),
                "main_gap_score": summary.get("main_gap_score"),
                "selection_reason_en": summary.get("selection_reason_en"),
                "n_weak_protection_rows": weak_count if by_risk else None,
                "diagnosis_summary_en": summary.get("diagnosis_summary_en"),
            }
        )
        bridge_meta = v1.get("bridge_meta")
        if isinstance(bridge_meta, dict):
            ctx["bridges_applied"] = {
                key: bool(bridge_meta.get(key))
                for key in ("block_2_4_hidden_exposure", "block_2_6_portfolio_weakness_map")
                if key in bridge_meta
            }
        return ctx

    conclusions = (
        stress_report.get("stress_conclusions") if isinstance(stress_report, dict) else None
    )
    legacy_status = (
        str(conclusions.get("hedge_gap_status") or "")
        if isinstance(conclusions, dict)
        else ""
    )
    if legacy_status:
        ctx.update(
            {
                "hedge_gap_source": HEDGE_GAP_SOURCE_LEGACY,
                "legacy_fallback_used": True,
                "legacy_hedge_gap_status": legacy_status,
            }
        )
        return ctx

    if comparison_slice is not None:
        ctx["hedge_gap_source"] = comparison_slice.get("hedge_gap_source")
        return ctx

    return None


def _hedge_gap_refs(
    stress_report: dict[str, Any] | None,
    hedge_gap_context: dict[str, Any] | None,
    comparison: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(hedge_gap_context, dict):
        return refs

    source = hedge_gap_context.get("hedge_gap_source")
    if source == HEDGE_GAP_SOURCE_V1:
        v1 = _hedge_gap_v1_block(stress_report)
        if v1 is not None:
            _append_reference(
                refs,
                artifact="stress_report.json",
                field_path=f"{HEDGE_GAP_V1_BLOCK}.block_status",
                value=v1.get("block_status"),
            )
            _append_reference(
                refs,
                artifact="stress_report.json",
                field_path=f"{HEDGE_GAP_V1_BLOCK}.summary.protection_profile",
                value=hedge_gap_context.get("protection_profile"),
            )
            _append_reference(
                refs,
                artifact="stress_report.json",
                field_path=f"{HEDGE_GAP_V1_BLOCK}.summary.main_hedge_gap",
                value={
                    "risk_type": hedge_gap_context.get("main_hedge_gap_risk_type"),
                    "linked_scenario_id": hedge_gap_context.get("main_hedge_gap_scenario_id"),
                    "protection_status": hedge_gap_context.get("main_hedge_gap_protection_status"),
                    "offset_coverage_ratio": hedge_gap_context.get(
                        "main_hedge_gap_offset_coverage_ratio"
                    ),
                },
            )
            diag = hedge_gap_context.get("diagnosis_summary_en")
            if isinstance(diag, str) and diag.strip():
                _append_reference(
                    refs,
                    artifact="stress_report.json",
                    field_path=f"{HEDGE_GAP_V1_BLOCK}.summary.diagnosis_summary_en",
                    value=diag.strip()[:240],
                    summary=diag.strip()[:240],
                )
    elif source == HEDGE_GAP_SOURCE_LEGACY:
        _append_reference(
            refs,
            artifact="stress_report.json",
            field_path="stress_conclusions.hedge_gap_status",
            value=hedge_gap_context.get("legacy_hedge_gap_status"),
            summary="Legacy hedge-gap status used because v1 block is missing or unavailable.",
        )

    comparison_slice = hedge_gap_context.get("comparison")
    if isinstance(comparison_slice, dict) and comparison_slice.get("status"):
        _append_reference(
            refs,
            artifact="candidate_comparison.json",
            field_path="hedge_gap_comparison.status",
            value=comparison_slice.get("status"),
        )
        pairwise = comparison_slice.get("pairwise")
        if isinstance(pairwise, list) and pairwise:
            _append_reference(
                refs,
                artifact="candidate_comparison.json",
                field_path="hedge_gap_comparison.pairwise",
                value=pairwise[:3],
                summary="Peer hedge-gap deltas vs baseline (Block 3.3 Session 08).",
            )
    elif isinstance(comparison, dict) and comparison.get("hedge_gap_comparison") is None:
        if hedge_gap_context.get("hedge_gap_source") == HEDGE_GAP_SOURCE_V1:
            refs.append(
                {
                    "artifact": "candidate_comparison.json",
                    "field_path": "hedge_gap_comparison",
                    "summary": "Hedge-gap peer comparison absent; cite stress_report hedge_gap_analysis_v1 only.",
                }
            )

    return refs


def _stress_scorecard_refs(
    stress_report: dict[str, Any] | None,
    scorecard_context: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(stress_report, dict):
        return refs

    source = (
        scorecard_context.get("stress_scorecard_source")
        if isinstance(scorecard_context, dict)
        else None
    )
    if source == STRESS_SCORECARD_SOURCE_V1:
        v1 = _scorecard_v1_block(stress_report)
        if v1 is not None:
            _append_reference(
                refs,
                artifact="stress_report.json",
                field_path=f"{SCORECARD_V1_BLOCK}.block_status",
                value=v1.get("block_status"),
            )
            _append_reference(
                refs,
                artifact="stress_report.json",
                field_path=f"{SCORECARD_V1_BLOCK}.stress_diagnosis.headline",
                value=scorecard_context.get("headline") if scorecard_context else None,
            )
            _append_reference(
                refs,
                artifact="stress_report.json",
                field_path=f"{SCORECARD_V1_BLOCK}.stress_diagnosis.diagnosis_confidence",
                value=scorecard_context.get("diagnosis_confidence") if scorecard_context else None,
            )
            worst_syn_id = (
                scorecard_context.get("worst_synthetic_scenario_id")
                if scorecard_context
                else None
            )
            if worst_syn_id:
                _append_reference(
                    refs,
                    artifact="stress_report.json",
                    field_path=f"{SCORECARD_V1_BLOCK}.worst_synthetic_scenario.scenario_id",
                    value=worst_syn_id,
                )
            worst_hist = (
                scorecard_context.get("worst_historical_episode") if scorecard_context else None
            )
            if worst_hist:
                _append_reference(
                    refs,
                    artifact="stress_report.json",
                    field_path=f"{SCORECARD_V1_BLOCK}.worst_historical_scenario.episode",
                    value=worst_hist,
                )
            diag = v1.get("stress_diagnosis")
            if isinstance(diag, dict):
                summary = diag.get("diagnosis_summary_en")
                if isinstance(summary, str) and summary.strip():
                    _append_reference(
                        refs,
                        artifact="stress_report.json",
                        field_path=f"{SCORECARD_V1_BLOCK}.stress_diagnosis.diagnosis_summary_en",
                        value=summary.strip()[:240],
                        summary=summary.strip()[:240],
                    )
        return refs

    if source == STRESS_SCORECARD_SOURCE_LEGACY and isinstance(scorecard_context, dict):
        _append_reference(
            refs,
            artifact="stress_report.json",
            field_path="stress_scorecard_v1.overall_status",
            value=scorecard_context.get("legacy_overall_status"),
            summary="Legacy stress scorecard used because Block 3.4 is missing or unavailable.",
        )
    return refs


def _stress_refs(
    stress_report: dict[str, Any] | None,
    scorecard_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(stress_report, dict):
        return refs
    _append_reference(
        refs,
        artifact="stress_report.json",
        field_path="status",
        value=stress_report.get("status"),
    )
    _append_reference(
        refs,
        artifact="stress_report.json",
        field_path="loss_gate_mode",
        value=stress_report.get("loss_gate_mode"),
    )
    primary = (
        stress_report.get("primary_diagnostic_code")
        or stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason")
    )
    if primary is not None:
        _append_reference(
            refs,
            artifact="stress_report.json",
            field_path="primary_diagnostic_code",
            value=primary,
        )
    worst = stress_report.get("worst_scenario_loss_pct")
    if worst is not None:
        _append_reference(
            refs,
            artifact="stress_report.json",
            field_path="worst_scenario_loss_pct",
            value=worst,
        )
    refs.extend(_stress_scorecard_refs(stress_report, scorecard_context))
    return refs


def _is_post_compare_context(
    *,
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
    selection: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
) -> bool:
    return all(
        isinstance(doc, dict)
        for doc in (comparison, current_vs_candidate, selection, decision_verdict)
    )


def _monitoring_refs(monitoring_diff: dict[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(monitoring_diff, dict):
        return refs
    _append_reference(
        refs,
        artifact="monitoring_diff.json",
        field_path="change_status",
        value=monitoring_diff.get("change_status"),
    )
    return refs


def _warnings(
    *,
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
    selection: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
    portfolio_xray: dict[str, Any] | None = None,
    stress_report: dict[str, Any] | None = None,
    scorecard_context: dict[str, Any] | None = None,
    diagnosis_only: bool = False,
) -> list[str]:
    warnings: list[str] = []
    if diagnosis_only:
        if not isinstance(portfolio_xray, dict):
            warnings.append("missing_diagnosis_source:portfolio_xray.json")
        if not isinstance(stress_report, dict):
            warnings.append("missing_diagnosis_source:stress_report.json")
        if isinstance(stress_report, dict) and scorecard_context is None:
            if isinstance(stress_report.get(STRESS_SCORECARD_SOURCE_LEGACY), dict):
                warnings.append("stress_scorecard_legacy_only:stress_scorecard_v1")
            else:
                warnings.append("missing_stress_scorecard:current_portfolio_stress_scorecard_v1")
        elif isinstance(scorecard_context, dict) and scorecard_context.get("legacy_fallback_used"):
            warnings.append("stress_scorecard_legacy_fallback:stress_scorecard_v1")
        return warnings
    required = {
        "candidate_comparison.json": comparison,
        "current_vs_candidate.json": current_vs_candidate,
        "selection_decision.json": selection,
        "decision_verdict.json": decision_verdict,
    }
    for name, doc in required.items():
        if not isinstance(doc, dict):
            warnings.append(f"missing_required_source:{name}")
    for source_name, doc in (
        ("current_vs_candidate.json", current_vs_candidate),
        ("selection_decision.json", selection),
        ("decision_verdict.json", decision_verdict),
    ):
        source_warnings = doc.get("warnings") if isinstance(doc, dict) else None
        if isinstance(source_warnings, list):
            warnings.extend(f"{source_name}:{warning}" for warning in source_warnings)
        limits = doc.get("confidence_limitations") if isinstance(doc, dict) else None
        if isinstance(limits, list):
            warnings.extend(f"{source_name}:confidence_limit:{limit}" for limit in limits)
    return warnings


def build_ai_commentary_context(
    *,
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
    selection: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
    action: dict[str, Any] | None = None,
    problem_classification: dict[str, Any] | None = None,
    candidate_launchpad: dict[str, Any] | None = None,
    monitoring_diff: dict[str, Any] | None = None,
    portfolio_xray: dict[str, Any] | None = None,
    stress_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the deterministic evidence contract for future AI Commentary."""

    post_compare = _is_post_compare_context(
        comparison=comparison,
        current_vs_candidate=current_vs_candidate,
        selection=selection,
        decision_verdict=decision_verdict,
    )
    diagnosis_only = not post_compare

    hedge_gap_context = _build_hedge_gap_context(stress_report, comparison)
    scorecard_context = _build_current_portfolio_stress_scorecard_context(stress_report)

    evidence_references: list[dict[str, Any]] = []
    evidence_references.extend(_xray_refs(portfolio_xray))
    evidence_references.extend(_stress_refs(stress_report, scorecard_context))
    evidence_references.extend(_hedge_gap_refs(stress_report, hedge_gap_context, comparison))
    evidence_references.extend(_problem_refs(problem_classification))
    evidence_references.extend(_launchpad_refs(candidate_launchpad))
    if post_compare:
        evidence_references.extend(_comparison_refs(comparison, current_vs_candidate))
        evidence_references.extend(_decision_refs(selection, decision_verdict, action))
    evidence_references.extend(_monitoring_refs(monitoring_diff))

    purpose = (
        PURPOSE_DIAGNOSIS_GROUNDING_ONLY
        if diagnosis_only
        else PURPOSE_GROUNDED_DECISION_CONTEXT
    )

    return {
        "schema_version": AI_COMMENTARY_CONTEXT_VERSION,
        "diagnostic_only": True,
        "generated_at": _utc_now_iso(),
        "purpose": purpose,
        "grounding_phase": "diagnosis_only" if diagnosis_only else "post_compare",
        "allowed_source_artifacts": list(ALLOWED_SOURCE_ARTIFACTS),
        "forbidden_claim_categories": list(FORBIDDEN_CLAIM_CATEGORIES),
        "required_grounding_rules": list(REQUIRED_GROUNDING_RULES),
        "commentary_topics": {
            "portfolio_diagnosis": (
                "Use Portfolio X-Ray product blocks 2.1–2.6 (especially block_2_6_portfolio_weakness_map "
                "narrative fields), Stress Test Lab, and Problem Classification when available."
            ),
            "hedge_gap": (
                "Use hedge_gap_context and stress_report.json hedge_gap_analysis_v1 (contribution-based "
                "offset coverage). Legacy stress_conclusions.hedge_gap_status and taxonomy hedge_gap_analysis "
                "only when v1 is missing or block_status is unavailable. For candidates, cite "
                "candidate_comparison.json hedge_gap_comparison when present."
            ),
            "stress_scorecard": (
                "Use current_portfolio_stress_scorecard_context and stress_report.json "
                "current_portfolio_stress_scorecard_v1 (Block 3.4 executive stress diagnosis). "
                "Do not cite stress_scorecard_v1.overall_status or other mandate-style legacy fields "
                "when Block 3.4 is available; use stress_diagnosis.headline and diagnosis_confidence instead."
            ),
            "candidate_logic": "Use Candidate Launchpad and current-vs-candidate evidence; do not invent weights.",
            "current_vs_candidate": "Explain only projected dimensions present in current_vs_candidate.json.",
            "decision_verdict": "Use decision_verdict.json as product language and selection_decision.json as technical source.",
            "no_trade": "If no-trade applies, cite selection_decision.json.no_trade and decision_verdict.json.",
            "monitoring_next": "Use monitoring_diff.json only when available; otherwise state that monitoring context is absent.",
        },
        "evidence_references": evidence_references,
        "hedge_gap_context": hedge_gap_context,
        "current_portfolio_stress_scorecard_context": scorecard_context,
        "source_artifacts": {
            "portfolio_xray": _source_name("portfolio_xray.json", portfolio_xray),
            "stress_report": _source_name("stress_report.json", stress_report),
            "problem_classification": _source_name("problem_classification.json", problem_classification),
            "candidate_launchpad": _source_name("candidate_launchpad.json", candidate_launchpad),
            "candidate_comparison": _source_name("candidate_comparison.json", comparison),
            "current_vs_candidate": _source_name("current_vs_candidate.json", current_vs_candidate),
            "selection_decision": _source_name("selection_decision.json", selection),
            "decision_verdict": _source_name("decision_verdict.json", decision_verdict),
            "action_plan": _source_name("action_plan.json", action),
            "monitoring_diff": _source_name("monitoring_diff.json", monitoring_diff),
        },
        "guardrails": {
            "does_not_call_llm": True,
            "does_not_calculate_metrics": True,
            "does_not_change_selection_or_verdict": True,
            "does_not_execute_trades": True,
        },
        "warnings": _warnings(
            comparison=comparison,
            current_vs_candidate=current_vs_candidate,
            selection=selection,
            decision_verdict=decision_verdict,
            portfolio_xray=portfolio_xray,
            stress_report=stress_report,
            scorecard_context=scorecard_context,
            diagnosis_only=diagnosis_only,
        ),
    }


def write_ai_commentary_context_outputs(
    *,
    output_dir: str | Path,
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
    selection: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
    action: dict[str, Any] | None = None,
    problem_classification: dict[str, Any] | None = None,
    candidate_launchpad: dict[str, Any] | None = None,
    monitoring_diff: dict[str, Any] | None = None,
    portfolio_xray: dict[str, Any] | None = None,
    stress_report: dict[str, Any] | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = build_ai_commentary_context(
        comparison=comparison,
        current_vs_candidate=current_vs_candidate,
        selection=selection,
        decision_verdict=decision_verdict,
        action=action,
        problem_classification=problem_classification,
        candidate_launchpad=candidate_launchpad,
        monitoring_diff=monitoring_diff,
        portfolio_xray=portfolio_xray,
        stress_report=stress_report,
    )
    path = out / AI_COMMENTARY_CONTEXT_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
    return {"ai_commentary_context_json": path}
