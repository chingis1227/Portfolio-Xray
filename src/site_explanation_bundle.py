"""Deterministic site-facing explanation hierarchy bundle.

This module builds the additive ``site_explanation_bundle.json`` artifact.  It
does not call an LLM, calculate new portfolio metrics, change candidate
selection, or turn a diagnostic candidate into a recommendation.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SITE_EXPLANATION_BUNDLE_VERSION = "site_explanation_bundle_v1"
SITE_EXPLANATION_BUNDLE_FILENAME = "site_explanation_bundle.json"

SCREEN_KEYS: tuple[str, ...] = (
    "diagnosis",
    "evidence",
    "client_fit",
    "hypothesis",
    "candidate",
    "comparison",
    "verdict",
    "report",
    "monitoring",
)

HIERARCHY_LEVELS: tuple[str, ...] = ("executive", "evidence", "technical")

ALLOWED_SOURCE_ARTIFACTS: tuple[str, ...] = (
    "portfolio_xray.json",
    "stress_report.json",
    "client_fit_check.json",
    "problem_classification.json",
    "candidate_launchpad.json",
    "portfolio_alternatives_builder.json",
    "candidate_generation.json",
    "candidate_comparison.json",
    "current_vs_candidate.json",
    "selection_decision.json",
    "decision_verdict.json",
    "ai_commentary_context.json",
    "what_changed_summary.json",
    "monitoring_diff.json",
)

REQUIRED_GUARDRAILS: dict[str, bool] = {
    "does_not_call_llm": True,
    "does_not_create_new_metrics": True,
    "does_not_issue_trade_instruction": True,
    "candidate_is_not_recommendation": True,
    "client_fit_is_not_suitability_approval": True,
}

FORBIDDEN_COPY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("suitable", re.compile(r"\bsuitable\b", re.IGNORECASE)),
    ("suitability approved", re.compile(r"\bsuitability\s+approved\b", re.IGNORECASE)),
    ("approved", re.compile(r"\bapproved\b", re.IGNORECASE)),
    ("buy", re.compile(r"\bbuy\b", re.IGNORECASE)),
    ("sell", re.compile(r"\bsell\b", re.IGNORECASE)),
    ("must rebalance", re.compile(r"\bmust\s+rebalance\b", re.IGNORECASE)),
    ("best portfolio", re.compile(r"\bbest\s+portfolio\b", re.IGNORECASE)),
    ("guaranteed", re.compile(r"\bguaranteed\b", re.IGNORECASE)),
)

_OPTIMAL_PORTFOLIO_PATTERN = re.compile(r"\boptimal\s+portfolio\b", re.IGNORECASE)
_TECHNICAL_METHOD_CONTEXT_PATTERN = re.compile(
    r"\b(method|methodology|optimizer|optimization|technical|disclosure)\b",
    re.IGNORECASE,
)
_RECOMMENDATION_PATTERN = re.compile(r"\brecommend(?:ation|ed|s|ing)?\b", re.IGNORECASE)
_CANDIDATE_RECOMMENDATION_WORDING = re.compile(
    r"\brecommend(?:ation|ed|s|ing)?\b",
    re.IGNORECASE,
)

_SEVERITY_TONE: dict[str, str] = {
    "high": "risk",
    "medium": "caution",
    "moderate": "caution",
    "low": "neutral",
    "unknown": "caution",
    "unavailable": "caution",
}

_ARTIFACT_PARAM_NAMES: dict[str, str] = {
    "portfolio_xray": "portfolio_xray.json",
    "stress_report": "stress_report.json",
    "client_fit_check": "client_fit_check.json",
    "problem_classification": "problem_classification.json",
    "candidate_launchpad": "candidate_launchpad.json",
    "portfolio_alternatives_builder": "portfolio_alternatives_builder.json",
    "candidate_generation": "candidate_generation.json",
    "candidate_comparison": "candidate_comparison.json",
    "current_vs_candidate": "current_vs_candidate.json",
    "selection_decision": "selection_decision.json",
    "decision_verdict": "decision_verdict.json",
    "ai_commentary_context": "ai_commentary_context.json",
    "what_changed_summary": "what_changed_summary.json",
    "monitoring_diff": "monitoring_diff.json",
}

_SCREEN_SOURCE_GROUPS: dict[str, tuple[str, ...]] = {
    "diagnosis": (
        "portfolio_xray.json",
        "stress_report.json",
        "problem_classification.json",
    ),
    "evidence": (
        "portfolio_xray.json",
        "stress_report.json",
        "ai_commentary_context.json",
    ),
    "client_fit": (
        "client_fit_check.json",
        "problem_classification.json",
    ),
    "hypothesis": (
        "candidate_launchpad.json",
        "portfolio_alternatives_builder.json",
    ),
    "candidate": ("candidate_generation.json",),
    "comparison": ("candidate_comparison.json", "current_vs_candidate.json"),
    "verdict": (
        "candidate_comparison.json",
        "current_vs_candidate.json",
        "decision_verdict.json",
    ),
    "report": ("ai_commentary_context.json",),
    "monitoring": ("what_changed_summary.json", "monitoring_diff.json"),
}

_PRIMARY_MISSING_SOURCE_BY_SCREEN: dict[str, str] = {
    "diagnosis": "portfolio_xray.json",
    "evidence": "portfolio_xray.json",
    "client_fit": "client_fit_check.json",
    "hypothesis": "candidate_launchpad.json",
    "candidate": "candidate_generation.json",
    "comparison": "current_vs_candidate.json",
    "verdict": "decision_verdict.json",
    "report": "ai_commentary_context.json",
    "monitoring": "what_changed_summary.json",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_artifact_available(value: Any) -> bool:
    return isinstance(value, Mapping)


def _source_artifacts(artifacts_by_param: Mapping[str, Any]) -> dict[str, str | None]:
    return {
        key: artifact if _is_artifact_available(artifacts_by_param.get(key)) else None
        for key, artifact in _ARTIFACT_PARAM_NAMES.items()
    }


def _empty_screens() -> dict[str, dict[str, list[dict[str, Any]]]]:
    return {screen: {level: [] for level in HIERARCHY_LEVELS} for screen in SCREEN_KEYS}


def _source_refs_for_available(
    source_artifacts: Mapping[str, str | None],
    candidate_sources: tuple[str, ...],
) -> list[dict[str, str]]:
    available = {
        artifact for artifact in source_artifacts.values() if isinstance(artifact, str)
    }
    return [
        {"artifact": artifact, "field_path": "$"}
        for artifact in candidate_sources
        if artifact in available
    ]


def _source_ref(artifact: str, field_path: str) -> list[dict[str, str]]:
    return [{"artifact": artifact, "field_path": field_path}]


def _first_supported_source_ref(
    value: Mapping[str, Any],
    *,
    fallback_field_path: str,
) -> list[dict[str, str]]:
    artifact = _clean_text(value.get("source_artifact"))
    field_path = _clean_text(value.get("source_field_path")) or _clean_text(
        value.get("evidence_path")
    )
    if artifact in ALLOWED_SOURCE_ARTIFACTS and field_path:
        return _source_ref(artifact, field_path)
    return _source_ref("problem_classification.json", fallback_field_path)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    return text or None


def _label_from_mapping(value: Mapping[str, Any]) -> str | None:
    for key in ("label_en", "label", "risk_title", "name"):
        text = _clean_text(value.get(key))
        if text:
            return text
    return None


def _severity_to_tone(severity: Any, default: str = "neutral") -> str:
    key = str(severity or "").strip().lower()
    return _SEVERITY_TONE.get(key, default)


def _format_pct(value: Any, *, decimal_input: bool | None = None) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    pct = float(value) * 100.0 if decimal_input is not False and abs(float(value)) <= 1 else float(value)
    return f"{pct:.1f}%"


def _format_status(value: Any) -> str | None:
    text = _clean_text(value)
    return text.replace("_", " ") if text else None


def _client_fit_status_tone(status: str | None) -> str:
    if status == "fit":
        return "positive"
    if status in {"breach", "conflict"}:
        return "risk"
    return "caution"


def _comparison_row(current_vs_candidate: Mapping[str, Any]) -> tuple[int, Mapping[str, Any]] | None:
    rows = _as_list(current_vs_candidate.get("comparisons"))
    for index, row in enumerate(rows):
        if isinstance(row, Mapping):
            return index, row
    return None


def _comparison_item_label(value: Any) -> str | None:
    item = _as_mapping(value)
    for key in ("label", "metric", "risk_type", "dimension", "name"):
        text = _clean_text(item.get(key))
        if text:
            direction = _format_status(item.get("direction"))
            return f"{text} ({direction})" if direction else text
    text = _clean_text(value)
    return text


def _joined_comparison_labels(values: Any, *, limit: int = 3) -> str | None:
    labels = [
        label
        for label in (_comparison_item_label(item) for item in _as_list(values)[:limit])
        if label
    ]
    if not labels:
        return None
    return ", ".join(labels)


def _candidate_display_name(candidate: Mapping[str, Any]) -> str:
    return (
        _clean_text(candidate.get("candidate_name"))
        or _clean_text(candidate.get("candidate_id"))
        or "the diagnostic candidate"
    )


def _candidate_safe_text(text: str) -> str:
    """Keep candidate copy away from recommendation wording, even in negated source text."""

    return _CANDIDATE_RECOMMENDATION_WORDING.sub("action instruction", text)


def _verdict_executive_text(verdict_id: str | None) -> str:
    if verdict_id == "rebalance_to_selected_candidate":
        return "The candidate is flagged for decision review, not automatic implementation."
    if verdict_id == "no_material_rebalance_recommended":
        return "The current evidence supports keeping the current portfolio under the review thresholds."
    if verdict_id == "test_another_candidate_or_review_evidence":
        return "The evidence is mixed; another candidate or evidence review is the supported next diagnostic path."
    if verdict_id == "risk_reduction_required":
        return "Mandate risk review is required before candidate allocation changes."
    if verdict_id == "candidate_failed_or_infeasible":
        return "Candidate generation failed or was infeasible, so no comparison-based action verdict is supported."
    return "The verdict is evidence-insufficient."


def _append_diagnosis_copy_rules(
    screens: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    portfolio_xray: Mapping[str, Any],
    problem_classification: Mapping[str, Any],
) -> None:
    """Populate diagnosis-screen copy from Block 4 and Portfolio X-Ray evidence."""

    primary = _as_mapping(problem_classification.get("primary_diagnosis"))
    if primary:
        chain = _as_mapping(problem_classification.get("interpretation_chain"))
        top_level_root_narrative = _as_mapping(
            problem_classification.get("root_cause_narrative")
        )
        root_narrative = top_level_root_narrative or _as_mapping(
            chain.get("root_cause_narrative")
        )
        root_narrative_path = (
            "root_cause_narrative"
            if top_level_root_narrative
            else "interpretation_chain.root_cause_narrative"
        )
        top_level_evidence_items = _as_list(
            problem_classification.get("diagnosis_evidence_items")
        )
        chain_evidence_items = top_level_evidence_items or _as_list(
            chain.get("diagnosis_evidence_items")
        )
        evidence_items_path = (
            "diagnosis_evidence_items"
            if top_level_evidence_items
            else "interpretation_chain.diagnosis_evidence_items"
        )
        top_level_metric_trace = _as_list(
            problem_classification.get("metric_to_diagnosis_trace")
        )
        metric_trace = top_level_metric_trace or _as_list(
            chain.get("metric_to_diagnosis_trace")
        )
        metric_trace_path = (
            "metric_to_diagnosis_trace"
            if top_level_metric_trace
            else "interpretation_chain.metric_to_diagnosis_trace"
        )
        chain_next_step = _as_mapping(chain.get("next_step_link"))
        label = _label_from_mapping(primary) or _label_from_mapping(
            _as_mapping(primary.get("root_cause"))
        ) or _clean_text(root_narrative.get("label_en"))
        confidence = _clean_text(primary.get("confidence"))
        materiality = _clean_text(primary.get("materiality"))
        if label:
            qualifiers = []
            if materiality:
                qualifiers.append(f"{materiality} materiality")
            if confidence:
                qualifiers.append(f"{confidence} confidence")
            qualifier_text = f" ({', '.join(qualifiers)})" if qualifiers else ""
            narrative_statement = _clean_text(root_narrative.get("statement_en"))
            executive_text = (
                f"{narrative_statement}{qualifier_text}"
                if narrative_statement
                else f"The current portfolio diagnosis is {label}{qualifier_text}."
            )
            screens["diagnosis"]["executive"].append(
                _text_item(
                    item_id="diagnosis.executive.primary_problem",
                    level="executive",
                    text=executive_text,
                    tone=_severity_to_tone(materiality, "caution"),
                    evidence_status="available",
                    claim_type="material_claim",
                    source_refs=_source_ref(
                        "problem_classification.json",
                        f"{root_narrative_path}.statement_en"
                        if narrative_statement
                        else "primary_diagnosis",
                    ),
                )
            )

        why_this_matters = _clean_text(
            root_narrative.get("portfolio_manager_interpretation_en")
        ) or _clean_text(primary.get("why_this_matters"))
        if why_this_matters:
            screens["diagnosis"]["evidence"].append(
                _text_item(
                    item_id="diagnosis.evidence.why_this_matters",
                    level="evidence",
                    text=why_this_matters,
                    tone="caution",
                    evidence_status="available",
                    claim_type="material_claim",
                    source_refs=_source_ref(
                        "problem_classification.json",
                        f"{root_narrative_path}.portfolio_manager_interpretation_en"
                        if root_narrative.get("portfolio_manager_interpretation_en")
                        else "primary_diagnosis.why_this_matters",
                    ),
                )
            )

        evidence_source = (
            chain_evidence_items
            if chain_evidence_items
            else _as_list(primary.get("key_evidence"))
        )
        for index, evidence in enumerate(evidence_source[:3], start=1):
            evidence_map = _as_mapping(evidence)
            text = _clean_text(evidence_map.get("interpretation_en"))
            if not text:
                continue
            item_id = (
                f"diagnosis.evidence.interpretation_chain_evidence_{index}"
                if chain_evidence_items
                else f"diagnosis.evidence.key_evidence_{index}"
            )
            source_refs = (
                _first_supported_source_ref(
                    evidence_map,
                    fallback_field_path=f"{evidence_items_path}[{index - 1}]",
                )
                if chain_evidence_items
                else _source_ref(
                    "problem_classification.json",
                    f"primary_diagnosis.key_evidence[{index - 1}]",
                )
            )
            screens["diagnosis"]["evidence"].append(
                _text_item(
                    item_id=item_id,
                    level="evidence",
                    text=text,
                    tone="neutral",
                    evidence_status="available",
                    claim_type="material_claim",
                    source_refs=source_refs,
                )
            )

        root_cause_boundary = _clean_text(root_narrative.get("root_cause_over_symptom_en"))
        if root_cause_boundary:
            screens["diagnosis"]["technical"].append(
                _text_item(
                    item_id="diagnosis.technical.root_cause_boundary",
                    level="technical",
                    text=root_cause_boundary,
                    tone="neutral",
                    evidence_status="available",
                    claim_type="material_claim",
                    source_refs=_source_ref(
                        "problem_classification.json",
                        f"{root_narrative_path}.root_cause_over_symptom_en",
                    ),
                )
            )

        if metric_trace:
            screens["diagnosis"]["technical"].append(
                _text_item(
                    item_id="diagnosis.technical.metric_trace",
                    level="technical",
                    text=f"Metric-to-diagnosis trace contains {len(metric_trace)} sourced signal(s) for this diagnosis.",
                    tone="neutral",
                    evidence_status="available",
                    claim_type="material_claim",
                    source_refs=_source_ref(
                        "problem_classification.json",
                        metric_trace_path,
                    ),
                )
            )

        next_step = _as_mapping(problem_classification.get("next_diagnostic_step"))
        step_label = _clean_text(chain_next_step.get("label")) or _clean_text(
            next_step.get("label")
        )
        step_reason = _clean_text(next_step.get("reason"))
        step_boundary = _clean_text(chain_next_step.get("decision_boundary"))
        if step_label or step_reason:
            step_text = step_label or step_reason or ""
            if step_reason and step_label:
                step_text = f"Next diagnostic step: {step_label}. {step_reason}"
            else:
                step_text = f"Next diagnostic step: {step_text}"
            if step_boundary:
                step_text = f"{step_text} Boundary: {step_boundary}"
            screens["diagnosis"]["technical"].append(
                _text_item(
                    item_id="diagnosis.technical.next_diagnostic_step",
                    level="technical",
                    text=step_text,
                    tone="neutral",
                    evidence_status="available",
                    claim_type="material_claim",
                    source_refs=_source_ref(
                        "problem_classification.json",
                        "interpretation_chain.next_step_link"
                        if chain_next_step
                        else "next_diagnostic_step",
                    ),
                )
            )
        return

    weakness_map = _as_mapping(portfolio_xray.get("block_2_6_portfolio_weakness_map"))
    summary = _clean_text(weakness_map.get("summary"))
    if summary:
        screens["diagnosis"]["executive"].append(
            _text_item(
                item_id="diagnosis.executive.weakness_map_summary",
                level="executive",
                text=summary,
                tone="caution",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref(
                    "portfolio_xray.json", "block_2_6_portfolio_weakness_map.summary"
                ),
            )
        )

    risk_types = [
        _as_mapping(row)
        for row in _as_list(weakness_map.get("risk_types"))
        if isinstance(row, Mapping)
    ]
    ranked = sorted(
        enumerate(risk_types),
        key=lambda row: (
            row[1].get("score_0_100") is not None,
            float(row[1].get("score_0_100") or -1),
        ),
        reverse=True,
    )
    for display_index, (source_index, risk) in enumerate(ranked[:3], start=1):
        text = _clean_text(risk.get("short_diagnosis")) or _clean_text(risk.get("why_status"))
        if not text:
            continue
        screens["diagnosis"]["evidence"].append(
            _text_item(
                item_id=f"diagnosis.evidence.weakness_{display_index}",
                level="evidence",
                text=text,
                tone=_severity_to_tone(risk.get("severity"), "caution"),
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref(
                    "portfolio_xray.json",
                    f"block_2_6_portfolio_weakness_map.risk_types[{source_index}]",
                ),
            )
        )


def _append_stress_copy_rules(
    screens: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    stress_report: Mapping[str, Any],
) -> None:
    """Populate Stress Test Lab copy under the evidence screen."""

    stress_results = _as_mapping(stress_report.get("stress_results_v1"))
    conclusions = _as_mapping(stress_report.get("stress_conclusions"))
    scorecard = _as_mapping(stress_report.get("stress_scorecard_v1"))
    hedge_gap = _as_mapping(stress_report.get("hedge_gap_analysis_v1"))

    worst_synthetic_source_path = "stress_results_v1.worst_synthetic"
    worst_synthetic = _as_mapping(stress_results.get("worst_synthetic"))
    if not worst_synthetic:
        worst_synthetic_source_path = "stress_conclusions.worst_synthetic_scenario"
        worst_synthetic = _as_mapping(conclusions.get("worst_synthetic_scenario"))
    scenario_id = _clean_text(worst_synthetic.get("scenario_id"))
    loss_pct = _format_pct(
        worst_synthetic.get("portfolio_loss_pct", worst_synthetic.get("portfolio_pnl_pct")),
        decimal_input=True,
    )
    severity = _clean_text(worst_synthetic.get("loss_severity"))
    if scenario_id and loss_pct:
        suffix = f" and {severity} severity" if severity else ""
        screens["evidence"]["executive"].append(
            _text_item(
                item_id="evidence.executive.worst_synthetic_stress",
                level="executive",
                text=f"The weakest synthetic stress result is {loss_pct} in {scenario_id}{suffix}.",
                tone=_severity_to_tone(severity, "risk"),
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref(
                    "stress_report.json",
                    worst_synthetic_source_path,
                ),
            )
        )

    worst_historical_source_path = "stress_results_v1.worst_historical"
    worst_historical = _as_mapping(stress_results.get("worst_historical"))
    if not worst_historical:
        worst_historical_source_path = "stress_conclusions.worst_historical_episode"
        worst_historical = _as_mapping(conclusions.get("worst_historical_episode"))
    episode = _clean_text(worst_historical.get("episode"))
    drawdown_pct = _format_pct(
        worst_historical.get("drawdown_pct", worst_historical.get("max_dd")),
        decimal_input=True,
    )
    if episode and drawdown_pct:
        screens["evidence"]["evidence"].append(
            _text_item(
                item_id="evidence.evidence.worst_historical_stress",
                level="evidence",
                text=f"The weakest historical replay is {episode}, with drawdown of {drawdown_pct}.",
                tone="caution",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref(
                    "stress_report.json",
                    worst_historical_source_path,
                ),
            )
        )

    top_loss_assets = _as_list(conclusions.get("top_loss_assets_worst_scenario"))
    if top_loss_assets:
        asset_text = ", ".join(str(asset) for asset in top_loss_assets[:3])
        screens["evidence"]["evidence"].append(
            _text_item(
                item_id="evidence.evidence.top_loss_assets",
                level="evidence",
                text=f"Main loss contributors in the worst synthetic scenario: {asset_text}.",
                tone="neutral",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref(
                    "stress_report.json",
                    "stress_conclusions.top_loss_assets_worst_scenario",
                ),
            )
        )

    main_hedge_gap = _as_mapping(_as_mapping(hedge_gap.get("summary")).get("main_hedge_gap"))
    offset = _format_pct(main_hedge_gap.get("offset_coverage_ratio"), decimal_input=True)
    risk_type = _clean_text(main_hedge_gap.get("risk_type"))
    if offset and risk_type:
        screens["evidence"]["evidence"].append(
            _text_item(
                item_id="evidence.evidence.main_hedge_gap",
                level="evidence",
                text=f"Offset coverage is {offset} in the main hedge-gap area, {risk_type}.",
                tone="caution",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref(
                    "stress_report.json", "hedge_gap_analysis_v1.summary.main_hedge_gap"
                ),
            )
        )

    n_synthetic = scorecard.get("n_synthetic_scenarios")
    n_historical = scorecard.get("n_historical_episodes")
    confidence = _clean_text(
        conclusions.get("overall_confidence") or scorecard.get("overall_confidence")
    )
    if n_synthetic is not None or n_historical is not None or confidence:
        parts = []
        if n_synthetic is not None:
            parts.append(f"{n_synthetic} synthetic scenarios")
        if n_historical is not None:
            parts.append(f"{n_historical} historical episodes")
        if confidence:
            parts.append(f"{confidence} overall confidence")
        screens["evidence"]["technical"].append(
            _text_item(
                item_id="evidence.technical.stress_coverage",
                level="technical",
                text="Stress coverage: " + ", ".join(parts) + ".",
                tone="neutral",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("stress_report.json", "stress_scorecard_v1"),
            )
        )


def _append_client_fit_copy_rules(
    screens: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    client_fit_check: Mapping[str, Any],
    problem_classification: Mapping[str, Any],
) -> None:
    """Populate Client Fit and report hierarchy copy from bounded display fields."""

    status = _format_status(
        client_fit_check.get("client_fit_status")
        or problem_classification.get("client_fit_status")
    )
    diagnostic_quality = _format_status(problem_classification.get("diagnostic_quality_status"))
    profile = _as_mapping(client_fit_check.get("profile"))
    source_quality = _format_status(profile.get("source_quality"))
    source_refs = []
    if client_fit_check:
        source_refs.append({"artifact": "client_fit_check.json", "field_path": "client_fit_status"})
    elif problem_classification.get("client_fit_status") is not None:
        source_refs.append({"artifact": "problem_classification.json", "field_path": "client_fit_status"})
    if diagnostic_quality:
        source_refs.append(
            {"artifact": "problem_classification.json", "field_path": "diagnostic_quality_status"}
        )

    if status:
        parts = [f"Client Fit status is {status}"]
        if diagnostic_quality:
            parts.append(f"diagnostic quality status is {diagnostic_quality}")
        if source_quality:
            parts.append(f"profile source quality is {source_quality}")
        text = (
            "; ".join(parts)
            + ". These rows are provided-profile context and stay separate from the portfolio diagnosis."
        )
        screens["client_fit"]["executive"].append(
            _text_item(
                item_id="client_fit.executive.status_boundary",
                level="executive",
                text=text,
                tone=_client_fit_status_tone(str(client_fit_check.get("client_fit_status") or "")),
                evidence_status="available",
                claim_type="material_claim",
                source_refs=source_refs or _source_ref("client_fit_check.json", "client_fit_status"),
            )
        )

    for index, check in enumerate(_as_list(client_fit_check.get("checks"))[:4], start=1):
        row = _as_mapping(check)
        dimension = _format_status(row.get("dimension"))
        row_status = _format_status(row.get("status"))
        interpretation = _clean_text(row.get("interpretation"))
        if not (dimension and row_status):
            continue
        text = f"{dimension}: portfolio evidence is {row_status} against the stated target or limit."
        if interpretation:
            text = f"{text} {interpretation}"
        screens["client_fit"]["evidence"].append(
            _text_item(
                item_id=f"client_fit.evidence.portfolio_vs_limits_{index}",
                level="evidence",
                text=text,
                tone=_client_fit_status_tone(str(row.get("status") or "")),
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("client_fit_check.json", f"checks[{index - 1}]"),
            )
        )

    boundary = _clean_text(
        _as_mapping(problem_classification.get("client_fit_context")).get(
            "diagnosis_selection_boundary_en"
        )
    )
    if boundary:
        screens["client_fit"]["technical"].append(
            _text_item(
                item_id="client_fit.technical.diagnosis_boundary",
                level="technical",
                text=boundary,
                tone="neutral",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("problem_classification.json", "client_fit_context"),
            )
        )

    if status:
        report_text = (
            f"Report hierarchy includes Client Fit status {status}"
            + (f" next to diagnostic quality status {diagnostic_quality}" if diagnostic_quality else "")
            + "; it does not turn either field into a final action."
        )
        screens["report"]["evidence"].append(
            _text_item(
                item_id="report.evidence.client_fit_hierarchy",
                level="evidence",
                text=report_text,
                tone=_client_fit_status_tone(str(client_fit_check.get("client_fit_status") or "")),
                evidence_status="available",
                claim_type="material_claim",
                source_refs=source_refs or _source_ref("client_fit_check.json", "client_fit_status"),
            )
        )


def _append_candidate_copy_rules(
    screens: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    candidate_generation: Mapping[str, Any],
) -> None:
    """Populate candidate-screen copy from the Block 7 candidate artifact."""

    candidate = _as_mapping(candidate_generation.get("candidate"))
    if not candidate:
        return

    display_name = _candidate_display_name(candidate)
    hypothesis = _clean_text(candidate.get("hypothesis_to_test"))
    goal = _clean_text(candidate.get("goal"))
    status = _format_status(candidate_generation.get("generation_status") or candidate.get("status"))

    if hypothesis:
        text = f"{display_name} is a diagnostic candidate that tests: {hypothesis}"
        path = "candidate.hypothesis_to_test"
    elif goal:
        text = f"{display_name} is a diagnostic candidate for this goal: {goal}"
        path = "candidate.goal"
    else:
        text = f"{display_name} is a diagnostic candidate created for comparison testing."
        path = "candidate"
    if status:
        text = f"{text} Generation status is {status}."
    screens["candidate"]["executive"].append(
        _text_item(
            item_id="candidate.executive.diagnostic_candidate",
            level="executive",
            text=text,
            tone="neutral" if status in {"generated", "available"} else "caution",
            evidence_status="available",
            claim_type="material_claim",
            source_refs=_source_ref("candidate_generation.json", path),
        )
    )

    criteria = _as_list(candidate.get("success_criteria"))
    if criteria:
        criteria_text = _candidate_safe_text("; ".join(str(item) for item in criteria[:3]))
        screens["candidate"]["evidence"].append(
            _text_item(
                item_id="candidate.evidence.success_criteria",
                level="evidence",
                text=f"Success criteria preserved for this candidate test: {criteria_text}.",
                tone="neutral",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("candidate_generation.json", "candidate.success_criteria"),
            )
        )

    tradeoff = _clean_text(candidate.get("tradeoff_to_watch"))
    if tradeoff:
        tradeoff = _candidate_safe_text(tradeoff)
        screens["candidate"]["evidence"].append(
            _text_item(
                item_id="candidate.evidence.tradeoff_to_watch",
                level="evidence",
                text=f"Trade-off to watch: {tradeoff}",
                tone="caution",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("candidate_generation.json", "candidate.tradeoff_to_watch"),
            )
        )

    decision_boundary = _clean_text(candidate.get("decision_boundary"))
    if decision_boundary:
        decision_boundary = _candidate_safe_text(decision_boundary)
        screens["candidate"]["evidence"].append(
            _text_item(
                item_id="candidate.evidence.decision_boundary",
                level="evidence",
                text=f"Decision boundary recorded for review: {decision_boundary}",
                tone="neutral",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("candidate_generation.json", "candidate.decision_boundary"),
            )
        )

    handoff = _as_mapping(candidate_generation.get("handoff_to_comparison"))
    can_compare = handoff.get("can_compare")
    blocked_reason = _format_status(handoff.get("blocked_reason") or handoff.get("reason"))
    method = _clean_text(candidate.get("method")) or _clean_text(candidate.get("method_variant"))
    technical_parts = []
    if method:
        technical_parts.append(f"method {method}")
    if can_compare is not None:
        technical_parts.append(f"can compare: {bool(can_compare)}")
    if blocked_reason and can_compare is False:
        technical_parts.append(f"blocked reason: {blocked_reason}")
    if technical_parts:
        screens["candidate"]["technical"].append(
            _text_item(
                item_id="candidate.technical.method_handoff",
                level="technical",
                text="Candidate method and handoff: " + ", ".join(technical_parts) + ".",
                tone="neutral" if can_compare is not False else "caution",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("candidate_generation.json", "handoff_to_comparison"),
            )
        )


def _append_comparison_copy_rules(
    screens: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    candidate_comparison: Mapping[str, Any],
    current_vs_candidate: Mapping[str, Any],
) -> None:
    """Populate comparison-screen copy from Current-vs-Candidate evidence."""

    row_entry = _comparison_row(current_vs_candidate)
    if row_entry is None:
        if candidate_comparison:
            screens["comparison"]["technical"].append(
                _text_item(
                    item_id="comparison.technical.canonical_comparison_available",
                    level="technical",
                    text="Canonical comparison evidence is available, but no active current-vs-candidate row is present.",
                    tone="caution",
                    evidence_status="limited",
                    claim_type="material_claim",
                    source_refs=_source_ref("candidate_comparison.json", "$"),
                )
            )
        return

    row_index, row = row_entry
    candidate_id = _clean_text(row.get("candidate_id")) or _clean_text(
        _as_list(current_vs_candidate.get("selected_candidate_ids"))[0]
        if _as_list(current_vs_candidate.get("selected_candidate_ids"))
        else None
    )
    view_mode = _format_status(current_vs_candidate.get("view_mode"))
    status = _format_status(row.get("status"))
    summary_parts = []
    if candidate_id:
        summary_parts.append(f"candidate {candidate_id}")
    if view_mode:
        summary_parts.append(f"view mode {view_mode}")
    if status:
        summary_parts.append(f"row status {status}")
    screens["comparison"]["executive"].append(
        _text_item(
            item_id="comparison.executive.active_candidate",
            level="executive",
            text="The active comparison reviews the current portfolio against "
            + (", ".join(summary_parts) if summary_parts else "one diagnostic candidate")
            + ".",
            tone="neutral" if status == "available" else "caution",
            evidence_status="available",
            claim_type="material_claim",
            source_refs=_source_ref("current_vs_candidate.json", f"comparisons[{row_index}]"),
        )
    )

    for field, item_id, prefix, tone in (
        ("what_improved", "comparison.evidence.what_improved", "Improved evidence", "positive"),
        ("what_worsened", "comparison.evidence.what_worsened", "Worsened evidence", "caution"),
        ("risk_reduced", "comparison.evidence.risk_reduced", "Risk reduced", "positive"),
        ("risk_added", "comparison.evidence.risk_added", "Risk added", "caution"),
    ):
        labels = _joined_comparison_labels(row.get(field))
        if not labels:
            continue
        screens["comparison"]["evidence"].append(
            _text_item(
                item_id=item_id,
                level="evidence",
                text=f"{prefix}: {labels}.",
                tone=tone,
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("current_vs_candidate.json", f"comparisons[{row_index}].{field}"),
            )
        )

    success = _as_mapping(row.get("success_criteria_result"))
    success_status = _format_status(success.get("overall_status"))
    if success_status:
        screens["comparison"]["evidence"].append(
            _text_item(
                item_id="comparison.evidence.success_criteria",
                level="evidence",
                text=f"Success-criteria result is {success_status}.",
                tone="positive" if success_status == "met" else "caution",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref(
                    "current_vs_candidate.json",
                    f"comparisons[{row_index}].success_criteria_result",
                ),
            )
        )

    practicality = _as_mapping(row.get("practicality"))
    turnover = _as_mapping(practicality.get("turnover_required"))
    turnover_pct = _format_pct(turnover.get("turnover_half_sum_pct"), decimal_input=True)
    cost_pct = _format_pct(practicality.get("estimated_transaction_cost_pct"), decimal_input=True)
    if turnover_pct or cost_pct:
        parts = []
        if turnover_pct:
            parts.append(f"turnover required {turnover_pct}")
        if cost_pct:
            parts.append(f"estimated transaction cost {cost_pct}")
        screens["comparison"]["evidence"].append(
            _text_item(
                item_id="comparison.evidence.practicality",
                level="evidence",
                text="Practicality evidence: " + ", ".join(parts) + ".",
                tone="caution",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("current_vs_candidate.json", f"comparisons[{row_index}].practicality"),
            )
        )

    materiality = _as_mapping(row.get("materiality_for_decision_review"))
    materiality_status = _format_status(materiality.get("status"))
    if materiality_status:
        screens["comparison"]["technical"].append(
            _text_item(
                item_id="comparison.technical.materiality_gate",
                level="technical",
                text=f"Decision-review materiality gate status: {materiality_status}.",
                tone="neutral",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref(
                    "current_vs_candidate.json",
                    f"comparisons[{row_index}].materiality_for_decision_review",
                ),
            )
        )


def _append_verdict_copy_rules(
    screens: dict[str, dict[str, list[dict[str, Any]]]],
    warnings: list[str],
    *,
    current_vs_candidate: Mapping[str, Any],
    decision_verdict: Mapping[str, Any],
) -> None:
    """Populate verdict-screen copy only when verdict and comparison evidence exist."""

    row_entry = _comparison_row(current_vs_candidate)
    if not decision_verdict or row_entry is None:
        warning = "missing_source:current_vs_candidate.json"
        if warning not in warnings:
            warnings.append(warning)
        screens["verdict"]["executive"].append(
            _text_item(
                item_id="verdict.executive.blocked_until_comparison",
                level="executive",
                text="Verdict evidence is blocked until comparison evidence is available.",
                tone="caution",
                evidence_status="missing",
                claim_type="empty_state",
                source_refs=[],
            )
        )
        return

    verdict_id = _clean_text(decision_verdict.get("verdict_id"))
    confidence = _format_status(decision_verdict.get("confidence"))
    executive = _verdict_executive_text(verdict_id)
    if confidence:
        executive = f"{executive} Confidence is {confidence}."
    screens["verdict"]["executive"].append(
        _text_item(
            item_id="verdict.executive.decision_support_outcome",
            level="executive",
            text=executive,
            tone="caution" if confidence == "low" else "neutral",
            evidence_status="available",
            claim_type="material_claim",
            source_refs=_source_ref("decision_verdict.json", "verdict_id"),
        )
    )

    rationale = _clean_text(decision_verdict.get("rationale_summary"))
    if rationale:
        screens["verdict"]["evidence"].append(
            _text_item(
                item_id="verdict.evidence.rationale_summary",
                level="evidence",
                text=rationale,
                tone="neutral",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("decision_verdict.json", "rationale_summary"),
            )
        )

    no_trade = _as_mapping(decision_verdict.get("no_trade"))
    if no_trade.get("evaluated") is not None:
        applies = bool(no_trade.get("applies"))
        screens["verdict"]["evidence"].append(
            _text_item(
                item_id="verdict.evidence.no_trade",
                level="evidence",
                text=f"No-trade evidence was evaluated; applies is {applies}.",
                tone="neutral" if not applies else "caution",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("decision_verdict.json", "no_trade"),
            )
        )

    reason_id = _format_status(decision_verdict.get("verdict_reason_id"))
    limitations = _as_list(decision_verdict.get("confidence_limitations"))
    technical_parts = []
    if reason_id:
        technical_parts.append(f"reason id {reason_id}")
    if limitations:
        technical_parts.append(f"{len(limitations)} confidence limitations")
    if technical_parts:
        screens["verdict"]["technical"].append(
            _text_item(
                item_id="verdict.technical.reason_and_limits",
                level="technical",
                text="Verdict disclosure: " + ", ".join(technical_parts) + ".",
                tone="neutral",
                evidence_status="available",
                claim_type="material_claim",
                source_refs=_source_ref("decision_verdict.json", "verdict_reason_id"),
            )
        )


def _text_item(
    *,
    item_id: str,
    level: str,
    text: str,
    tone: str = "neutral",
    evidence_status: str,
    claim_type: str,
    source_refs: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    refs = list(source_refs or [])
    if claim_type == "material_claim" and not refs:
        raise ValueError(f"material claim {item_id!r} must include source_refs")
    _validate_source_refs(item_id=item_id, source_refs=refs)
    _validate_copy_guardrails(item_id=item_id, level=level, text=text)
    return {
        "id": item_id,
        "level": level,
        "text": text,
        "tone": tone,
        "evidence_status": evidence_status,
        "claim_type": claim_type,
        "source_refs": refs,
    }


def _validate_source_refs(*, item_id: str, source_refs: list[dict[str, str]]) -> None:
    """Validate the source-reference shape used to ground material claims."""

    allowed_artifacts = set(ALLOWED_SOURCE_ARTIFACTS)
    for index, ref in enumerate(source_refs):
        if not isinstance(ref, Mapping):
            raise ValueError(f"source_ref {index} in {item_id!r} must be an object")

        artifact = ref.get("artifact")
        field_path = ref.get("field_path")
        if not isinstance(artifact, str) or not artifact:
            raise ValueError(f"source_ref {index} in {item_id!r} must include artifact")
        if artifact not in allowed_artifacts:
            raise ValueError(
                f"source_ref {index} in {item_id!r} uses unsupported artifact {artifact!r}"
            )
        if not isinstance(field_path, str) or not field_path:
            raise ValueError(f"source_ref {index} in {item_id!r} must include field_path")


def _validate_copy_guardrails(*, item_id: str, level: str, text: str) -> None:
    """Reject advice-like or marketing-like generated product copy."""

    for label, pattern in FORBIDDEN_COPY_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"forbidden copy phrase {label!r} in {item_id!r}")

    if _OPTIMAL_PORTFOLIO_PATTERN.search(text):
        if level != "technical" or not _TECHNICAL_METHOD_CONTEXT_PATTERN.search(text):
            raise ValueError(
                f"'optimal portfolio' is allowed only in technical method context in {item_id!r}"
            )

    if item_id.startswith("candidate.") and _RECOMMENDATION_PATTERN.search(text):
        raise ValueError(f"candidate copy must not describe a recommendation in {item_id!r}")


def _add_skeleton_screen_items(
    screens: dict[str, dict[str, list[dict[str, Any]]]],
    source_artifacts: Mapping[str, str | None],
    warnings: list[str],
) -> None:
    for screen, candidate_sources in _SCREEN_SOURCE_GROUPS.items():
        refs = _source_refs_for_available(source_artifacts, candidate_sources)
        if refs:
            screens[screen]["technical"].append(
                _text_item(
                    item_id=f"{screen}.technical.source_availability",
                    level="technical",
                    text="Deterministic source artifacts are available for this screen.",
                    evidence_status="available",
                    claim_type="material_claim",
                    source_refs=refs,
                )
            )
            continue

        missing_source = _PRIMARY_MISSING_SOURCE_BY_SCREEN[screen]
        warning = f"missing_source:{missing_source}"
        if warning not in warnings:
            warnings.append(warning)
        screens[screen]["executive"].append(
            _text_item(
                item_id=f"{screen}.executive.empty_state",
                level="executive",
                text="Evidence is not available yet for this screen.",
                tone="caution",
                evidence_status="missing",
                claim_type="empty_state",
                source_refs=[],
            )
        )


def build_site_explanation_bundle(
    *,
    review_id: str | None = None,
    portfolio_xray: dict[str, Any] | None = None,
    stress_report: dict[str, Any] | None = None,
    client_fit_check: dict[str, Any] | None = None,
    problem_classification: dict[str, Any] | None = None,
    candidate_launchpad: dict[str, Any] | None = None,
    portfolio_alternatives_builder: dict[str, Any] | None = None,
    candidate_generation: dict[str, Any] | None = None,
    candidate_comparison: dict[str, Any] | None = None,
    current_vs_candidate: dict[str, Any] | None = None,
    selection_decision: dict[str, Any] | None = None,
    decision_verdict: dict[str, Any] | None = None,
    ai_commentary_context: dict[str, Any] | None = None,
    what_changed_summary: dict[str, Any] | None = None,
    monitoring_diff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the site-facing explanation hierarchy from deterministic artifacts."""

    artifacts_by_param: dict[str, Any] = {
        "portfolio_xray": portfolio_xray,
        "stress_report": stress_report,
        "client_fit_check": client_fit_check,
        "problem_classification": problem_classification,
        "candidate_launchpad": candidate_launchpad,
        "portfolio_alternatives_builder": portfolio_alternatives_builder,
        "candidate_generation": candidate_generation,
        "candidate_comparison": candidate_comparison,
        "current_vs_candidate": current_vs_candidate,
        "selection_decision": selection_decision,
        "decision_verdict": decision_verdict,
        "ai_commentary_context": ai_commentary_context,
        "what_changed_summary": what_changed_summary,
        "monitoring_diff": monitoring_diff,
    }
    source_artifacts = _source_artifacts(artifacts_by_param)
    warnings: list[str] = []
    screens = _empty_screens()
    _add_skeleton_screen_items(screens, source_artifacts, warnings)
    if _is_artifact_available(portfolio_xray) or _is_artifact_available(problem_classification):
        _append_diagnosis_copy_rules(
            screens,
            portfolio_xray=_as_mapping(portfolio_xray),
            problem_classification=_as_mapping(problem_classification),
        )
    if _is_artifact_available(stress_report):
        _append_stress_copy_rules(screens, stress_report=_as_mapping(stress_report))
    if _is_artifact_available(client_fit_check) or _is_artifact_available(problem_classification):
        _append_client_fit_copy_rules(
            screens,
            client_fit_check=_as_mapping(client_fit_check),
            problem_classification=_as_mapping(problem_classification),
        )
    if _is_artifact_available(candidate_generation):
        _append_candidate_copy_rules(
            screens,
            candidate_generation=_as_mapping(candidate_generation),
        )
    if _is_artifact_available(candidate_comparison) or _is_artifact_available(current_vs_candidate):
        _append_comparison_copy_rules(
            screens,
            candidate_comparison=_as_mapping(candidate_comparison),
            current_vs_candidate=_as_mapping(current_vs_candidate),
        )
    if _is_artifact_available(decision_verdict):
        _append_verdict_copy_rules(
            screens,
            warnings,
            current_vs_candidate=_as_mapping(current_vs_candidate),
            decision_verdict=_as_mapping(decision_verdict),
        )

    return {
        "schema_version": SITE_EXPLANATION_BUNDLE_VERSION,
        "review_id": review_id,
        "generated_at": _utc_now_iso(),
        "screens": screens,
        "source_artifacts": source_artifacts,
        "warnings": warnings,
        "guardrails": dict(REQUIRED_GUARDRAILS),
    }


def write_site_explanation_bundle_outputs(
    *,
    output_dir: str | Path,
    review_id: str | None = None,
    portfolio_xray: dict[str, Any] | None = None,
    stress_report: dict[str, Any] | None = None,
    client_fit_check: dict[str, Any] | None = None,
    problem_classification: dict[str, Any] | None = None,
    candidate_launchpad: dict[str, Any] | None = None,
    portfolio_alternatives_builder: dict[str, Any] | None = None,
    candidate_generation: dict[str, Any] | None = None,
    candidate_comparison: dict[str, Any] | None = None,
    current_vs_candidate: dict[str, Any] | None = None,
    selection_decision: dict[str, Any] | None = None,
    decision_verdict: dict[str, Any] | None = None,
    ai_commentary_context: dict[str, Any] | None = None,
    what_changed_summary: dict[str, Any] | None = None,
    monitoring_diff: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Write ``site_explanation_bundle.json`` and return its path."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = build_site_explanation_bundle(
        review_id=review_id,
        portfolio_xray=portfolio_xray,
        stress_report=stress_report,
        client_fit_check=client_fit_check,
        problem_classification=problem_classification,
        candidate_launchpad=candidate_launchpad,
        portfolio_alternatives_builder=portfolio_alternatives_builder,
        candidate_generation=candidate_generation,
        candidate_comparison=candidate_comparison,
        current_vs_candidate=current_vs_candidate,
        selection_decision=selection_decision,
        decision_verdict=decision_verdict,
        ai_commentary_context=ai_commentary_context,
        what_changed_summary=what_changed_summary,
        monitoring_diff=monitoring_diff,
    )
    path = out / SITE_EXPLANATION_BUNDLE_FILENAME
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=2, ensure_ascii=False, default=str)
    return {"site_explanation_bundle_json": path}
