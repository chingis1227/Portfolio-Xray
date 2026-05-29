"""Problem Classification artifact for diagnosis-first Portfolio MRI.

This module translates existing deterministic Portfolio X-Ray and Stress Test
Lab evidence into user-understandable portfolio problems. It does not calculate
new metrics, optimize, rank candidates, or issue a rebalance verdict.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.block_2_6_portfolio_weakness_map import RISK_TYPES

PROBLEM_CLASSIFICATION_VERSION = "problem_classification_v1"
WEAKNESS_MAP_SOURCE_BLOCK = "block_2_6_portfolio_weakness_map"
HEDGE_GAP_V1_BLOCK = "hedge_gap_analysis_v1"
HEDGE_GAP_V1_VERSION = "hedge_gap_analysis_v1"
HEDGE_GAP_SOURCE_V1 = HEDGE_GAP_V1_BLOCK
HEDGE_GAP_SOURCE_LEGACY = "stress_conclusions.hedge_gap_status"
SCORECARD_V1_BLOCK = "current_portfolio_stress_scorecard_v1"
SCORECARD_V1_VERSION = "current_portfolio_stress_scorecard_v1"
STRESS_SCORECARD_SOURCE_V1 = SCORECARD_V1_BLOCK
STRESS_SCORECARD_SOURCE_LEGACY = "stress_scorecard_v1"

_WEAK_PROTECTION_STATUSES = frozenset({"weak_protection", "no_protection"})
_PARTIAL_PROTECTION_STATUSES = frozenset({"partial_protection"})

# Canonical Block 2.6 risk_type → problem_id (no substring heuristics).
BLOCK_2_6_RISK_TYPE_TO_PROBLEM_IDS: dict[str, tuple[str, ...]] = {
    "equity_shock": ("high_equity_beta", "weak_crisis_resilience"),
    "credit_shock": ("weak_crisis_resilience",),
    "rates_shock": ("high_drawdown_risk",),
    "inflation_stagflation": ("weak_crisis_resilience",),
    "liquidity_shock": ("poor_diversification", "weak_crisis_resilience"),
    "usd_shock": ("weak_crisis_resilience",),
    "commodity_shock": ("weak_crisis_resilience",),
    "recession_severe": ("weak_crisis_resilience", "high_drawdown_risk"),
}
PROBLEM_CLASSIFICATION_FILENAME = "problem_classification.json"

PROBLEM_LABELS: dict[str, str] = {
    "high_drawdown_risk": "High drawdown risk",
    "high_volatility": "High volatility",
    "high_concentration": "High concentration",
    "poor_diversification": "Poor diversification",
    "weak_hedge_behavior": "Weak hedge behavior",
    "weak_crisis_resilience": "Weak crisis resilience",
    "high_equity_beta": "High equity beta",
    "data_review_required": "Evidence quality requires review",
    "current_portfolio_acceptable": "Current portfolio already acceptable",
}

PROBLEM_TO_PATHS: dict[str, tuple[str, ...]] = {
    "high_drawdown_risk": ("Reduce drawdown", "Improve crisis resilience"),
    "high_volatility": ("Reduce volatility", "Compare against simple benchmark"),
    "high_concentration": ("Reduce concentration", "Improve diversification"),
    "poor_diversification": ("Improve diversification", "Compare against simple benchmark"),
    "weak_hedge_behavior": ("Improve crisis resilience", "Keep current portfolio and monitor"),
    "weak_crisis_resilience": ("Improve crisis resilience", "Reduce drawdown"),
    "high_equity_beta": ("Reduce volatility", "Reduce drawdown"),
    "data_review_required": ("Review data quality", "Keep current portfolio and monitor"),
    "current_portfolio_acceptable": ("Keep current portfolio and monitor", "Compare against simple benchmark"),
}

_SEVERITY_SCORE = {"high": 3, "moderate": 2, "low": 1, "unknown": 0}
_CONFIDENCE_SCORE = {"low": 0, "medium": 1, "high": 2}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _sections(xray: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(xray, dict):
        return {}
    sections = xray.get("sections")
    return sections if isinstance(sections, dict) else {}


def _items(section: Any) -> list[dict[str, Any]]:
    if not isinstance(section, dict):
        return []
    raw = section.get("items")
    return [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []


def _confidence_min(a: str, b: str) -> str:
    score = min(_CONFIDENCE_SCORE.get(a, 1), _CONFIDENCE_SCORE.get(b, 1))
    return {v: k for k, v in _CONFIDENCE_SCORE.items()}[score]


def _normalize_severity(value: Any, default: str = "moderate") -> str:
    raw = str(value or default).lower()
    return raw if raw in _SEVERITY_SCORE else default


def _normalize_confidence(value: Any, default: str = "medium") -> str:
    raw = str(value or default).lower()
    return raw if raw in _CONFIDENCE_SCORE else default


def _add_problem(
    problems: dict[str, dict[str, Any]],
    problem_id: str,
    *,
    severity: str,
    confidence: str = "medium",
    evidence: dict[str, Any],
) -> None:
    row = problems.get(problem_id)
    if row is None:
        row = {
            "problem_id": problem_id,
            "label": PROBLEM_LABELS[problem_id],
            "severity": _normalize_severity(severity),
            "confidence": _normalize_confidence(confidence),
            "evidence": [],
            "reasonable_paths_to_test": list(PROBLEM_TO_PATHS[problem_id]),
        }
    else:
        current = str(row.get("severity") or "unknown")
        incoming = _normalize_severity(severity)
        if _SEVERITY_SCORE[incoming] > _SEVERITY_SCORE.get(current, 0):
            row["severity"] = incoming
        row["confidence"] = _confidence_min(
            str(row.get("confidence") or "medium"),
            _normalize_confidence(confidence),
        )
    row["evidence"].append(evidence)
    problems[problem_id] = row


def _block_2_6_severity_to_problem(severity: str) -> str | None:
    return {
        "High": "high",
        "Medium": "moderate",
        "Low": "low",
        "Unavailable": None,
    }.get(severity)


def _collect_block_2_6_weakness_map(
    problems: dict[str, dict[str, Any]],
    portfolio_xray: dict[str, Any] | None,
) -> None:
    """Product weakness hypotheses from Block 2.6 only (not legacy sections.weakness_map)."""
    if not isinstance(portfolio_xray, dict):
        return
    block = portfolio_xray.get(WEAKNESS_MAP_SOURCE_BLOCK)
    if not isinstance(block, dict):
        return
    for risk in block.get("risk_types") or []:
        if not isinstance(risk, dict):
            continue
        risk_type = str(risk.get("risk_type") or "")
        if risk_type not in RISK_TYPES:
            continue
        severity_band = str(risk.get("severity") or "")
        if severity_band in {"Low", "Unavailable"}:
            continue
        problem_severity = _block_2_6_severity_to_problem(severity_band)
        if not problem_severity:
            continue
        problem_ids = BLOCK_2_6_RISK_TYPE_TO_PROBLEM_IDS.get(risk_type, ())
        if not problem_ids:
            continue
        summary = (
            risk.get("short_diagnosis")
            or risk.get("why_status")
            or risk.get("explanation")
            or risk.get("risk_title")
        )
        confidence = _normalize_confidence(risk.get("confidence"), default="medium")
        evidence_base = {
            "source_artifact": "portfolio_xray.json",
            "source_section": WEAKNESS_MAP_SOURCE_BLOCK,
            "risk_type": risk_type,
            "score_0_100": risk.get("score_0_100"),
            "severity_band": severity_band,
            "summary": summary,
            "next_tests": list(risk.get("next_tests") or []),
        }
        for problem_id in problem_ids:
            _add_problem(
                problems,
                problem_id,
                severity=problem_severity,
                confidence=confidence,
                evidence=dict(evidence_base),
            )


def _collect_allocation(problems: dict[str, dict[str, Any]], sections: dict[str, Any]) -> None:
    for item in _items(sections.get("asset_allocation")):
        text = " ".join(str(item.get(k) or "") for k in ("type", "summary", "description", "interpretation"))
        if "concentration" in text.lower():
            _add_problem(
                problems,
                "high_concentration",
                severity="moderate",
                evidence={
                    "source_artifact": "portfolio_xray.json",
                    "source_section": "asset_allocation",
                    "source_item_type": item.get("type"),
                    "summary": item.get("summary") or item.get("description"),
                },
            )


def _collect_risk_metrics(problems: dict[str, dict[str, Any]], sections: dict[str, Any]) -> None:
    for item in _items(sections.get("risk_diagnostics")):
        vol = _as_float(
            item.get("vol_annual")
            or item.get("volatility")
            or item.get("portfolio_volatility")
            or item.get("volatility_annual")
        )
        drawdown = _as_float(item.get("max_drawdown") or item.get("drawdown") or item.get("max_dd"))
        if vol is not None and vol >= 0.18:
            _add_problem(
                problems,
                "high_volatility",
                severity="high" if vol >= 0.25 else "moderate",
                evidence={
                    "source_artifact": "portfolio_xray.json",
                    "source_section": "risk_diagnostics",
                    "source_item_type": item.get("type"),
                    "metric": "volatility",
                    "value": vol,
                },
            )
        if drawdown is not None and abs(drawdown) >= 0.15:
            _add_problem(
                problems,
                "high_drawdown_risk",
                severity="high" if abs(drawdown) >= 0.25 else "moderate",
                evidence={
                    "source_artifact": "portfolio_xray.json",
                    "source_section": "risk_diagnostics",
                    "source_item_type": item.get("type"),
                    "metric": "max_drawdown",
                    "value": drawdown,
                },
            )


def _collect_factor_exposure(problems: dict[str, dict[str, Any]], sections: dict[str, Any]) -> None:
    for item in _items(sections.get("factor_exposure")):
        beta = _as_float(item.get("beta_eq") or item.get("equity_beta"))
        if beta is not None and beta >= 0.8:
            _add_problem(
                problems,
                "high_equity_beta",
                severity="high" if beta >= 1.1 else "moderate",
                evidence={
                    "source_artifact": "portfolio_xray.json",
                    "source_section": "factor_exposure",
                    "source_item_type": item.get("type"),
                    "metric": "equity_beta",
                    "value": beta,
                },
            )


def _collect_data_review(problems: dict[str, dict[str, Any]], sections: dict[str, Any]) -> None:
    partial = [
        key
        for key, section in sections.items()
        if isinstance(section, dict) and section.get("status") in {"partial", "unavailable"}
    ]
    if len(partial) >= 3:
        _add_problem(
            problems,
            "data_review_required",
            severity="moderate",
            confidence="low",
            evidence={
                "source_artifact": "portfolio_xray.json",
                "source_section": "sections",
                "partial_or_unavailable_sections": partial,
            },
        )


def _hedge_gap_v1_block(stress_report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(stress_report, dict):
        return None
    block = stress_report.get(HEDGE_GAP_V1_BLOCK)
    if not isinstance(block, dict) or block.get("version") != HEDGE_GAP_V1_VERSION:
        return None
    return block


def _scorecard_v1_block(stress_report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(stress_report, dict):
        return None
    block = stress_report.get(SCORECARD_V1_BLOCK)
    if not isinstance(block, dict) or block.get("version") != SCORECARD_V1_VERSION:
        return None
    return block


def _confidence_from_scorecard_diagnosis(scorecard: dict[str, Any]) -> str:
    stress_diagnosis = scorecard.get("stress_diagnosis")
    if not isinstance(stress_diagnosis, dict):
        return "medium"
    raw = str(stress_diagnosis.get("diagnosis_confidence") or "medium").lower()
    if raw in _CONFIDENCE_SCORE:
        return raw
    return "medium"


def _severity_from_main_hedge_gap(main: dict[str, Any]) -> str:
    protection = str(main.get("protection_status") or "")
    loss = _as_float(main.get("portfolio_loss_pct"))
    if protection == "no_protection":
        return "high"
    if protection == "weak_protection" and loss is not None and abs(loss) >= 0.10:
        return "high"
    if protection in _WEAK_PROTECTION_STATUSES:
        return "moderate"
    if protection in _PARTIAL_PROTECTION_STATUSES:
        return "moderate"
    return "moderate"


def _collect_hedge_gap_v1(
    problems: dict[str, dict[str, Any]],
    stress_report: dict[str, Any],
    *,
    confidence: str,
) -> str | None:
    """Return hedge-gap source id when v1 was evaluated; None when legacy fallback is required."""
    v1 = _hedge_gap_v1_block(stress_report)
    if v1 is None:
        return None
    if str(v1.get("block_status") or "") == "unavailable":
        return None

    summary = v1.get("summary") if isinstance(v1.get("summary"), dict) else {}
    profile = str(summary.get("protection_profile") or "")
    main = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else None
    by_risk = [row for row in (v1.get("by_risk_type") or []) if isinstance(row, dict)]
    weak_rows = [
        row
        for row in by_risk
        if str(row.get("protection_status") or "") in _WEAK_PROTECTION_STATUSES
    ]
    weak_count = len(weak_rows)

    trigger = False
    severity = "moderate"
    reason_codes: list[str] = []

    if profile == "mostly_weak_protection":
        trigger = True
        severity = "high"
        reason_codes.append("protection_profile_mostly_weak")
    if isinstance(main, dict) and str(main.get("protection_status") or "") in _WEAK_PROTECTION_STATUSES:
        trigger = True
        severity = _severity_from_main_hedge_gap(main)
        reason_codes.append("main_hedge_gap_weak_or_no_offset")
    elif (
        isinstance(main, dict)
        and str(main.get("protection_status") or "") in _PARTIAL_PROTECTION_STATUSES
        and profile == "mixed_protection"
    ):
        trigger = True
        severity = "moderate"
        reason_codes.append("main_hedge_gap_partial_under_mixed_profile")
    if weak_count >= 3:
        trigger = True
        severity = "high"
        reason_codes.append("multiple_weak_protection_rows")
    elif weak_count >= 1 and not trigger:
        trigger = True
        severity = "moderate"
        reason_codes.append("at_least_one_weak_protection_row")

    if not trigger:
        return HEDGE_GAP_SOURCE_V1

    evidence: dict[str, Any] = {
        "source_artifact": "stress_report.json",
        "source_section": HEDGE_GAP_V1_BLOCK,
        "source_field": "summary.main_hedge_gap",
        "block_status": v1.get("block_status"),
        "ruleset_version": v1.get("ruleset_version"),
        "protection_profile": profile or None,
        "n_weak_protection_rows": weak_count,
        "reason_codes": reason_codes,
        "main_hedge_gap_risk_type": main.get("risk_type") if isinstance(main, dict) else None,
        "main_hedge_gap_scenario_id": (
            summary.get("main_hedge_gap_scenario_id")
            or (main.get("linked_scenario_id") if isinstance(main, dict) else None)
        ),
        "main_hedge_gap_offset_coverage_ratio": summary.get("main_hedge_gap_offset_coverage_ratio"),
        "main_hedge_gap_portfolio_loss_pct": summary.get("main_hedge_gap_portfolio_loss_pct"),
        "main_hedge_gap_protection_status": (
            main.get("protection_status") if isinstance(main, dict) else None
        ),
        "diagnosis_summary_en": summary.get("diagnosis_summary_en"),
    }
    bridge_meta = v1.get("bridge_meta")
    if isinstance(bridge_meta, dict):
        evidence["bridges_applied"] = {
            key: bool(bridge_meta.get(key))
            for key in ("block_2_4_hidden_exposure", "block_2_6_portfolio_weakness_map")
            if key in bridge_meta
        }

    row_confidence = confidence
    if isinstance(main, dict):
        row_confidence = _normalize_confidence(main.get("confidence"), default=confidence)

    _add_problem(
        problems,
        "weak_hedge_behavior",
        severity=severity,
        confidence=row_confidence,
        evidence=evidence,
    )
    return HEDGE_GAP_SOURCE_V1


def _collect_hedge_gap_legacy_fallback(
    problems: dict[str, dict[str, Any]],
    conclusions: dict[str, Any],
    *,
    confidence: str,
) -> str | None:
    hedge_status = str(conclusions.get("hedge_gap_status") or "")
    if hedge_status and hedge_status not in {"ok", "pass", "none", "not_applicable"}:
        _add_problem(
            problems,
            "weak_hedge_behavior",
            severity="high" if hedge_status == "high" else "moderate",
            confidence=confidence,
            evidence={
                "source_artifact": "stress_report.json",
                "source_section": "stress_conclusions",
                "source_field": "hedge_gap_status",
                "status": hedge_status,
                "evidence_path": "legacy_fallback",
            },
        )
        return HEDGE_GAP_SOURCE_LEGACY
    return None


def _loss_severity_from_values(values: Iterable[Any]) -> str | None:
    for value in values:
        v = _as_float(value)
        if v is None:
            continue
        mag = abs(v)
        if mag >= 0.25:
            return "high"
        if mag >= 0.15:
            return "moderate"
    return None


def _add_stress_scenario_problem(
    problems: dict[str, dict[str, Any]],
    *,
    problem_id: str,
    severity: str,
    confidence: str,
    source_section: str,
    source_field: str,
    scenario_id: Any,
    loss_severity: str,
    extra: dict[str, Any] | None = None,
) -> None:
    if severity not in {"moderate", "high"}:
        return
    evidence: dict[str, Any] = {
        "source_artifact": "stress_report.json",
        "source_section": source_section,
        "source_field": source_field,
        "scenario_id": scenario_id,
        "loss_severity": loss_severity,
    }
    if extra:
        evidence.update(extra)
    _add_problem(
        problems,
        problem_id,
        severity=severity,
        confidence=confidence,
        evidence=evidence,
    )


def _collect_stress_scorecard_v1(
    problems: dict[str, dict[str, Any]],
    stress_report: dict[str, Any],
    scorecard: dict[str, Any],
) -> None:
    confidence = _confidence_from_scorecard_diagnosis(scorecard)
    signals = scorecard.get("problem_classification_signals")
    signals = signals if isinstance(signals, dict) else {}

    worst_syn = scorecard.get("worst_synthetic_scenario")
    worst_syn = worst_syn if isinstance(worst_syn, dict) else {}
    if worst_syn.get("availability") == "available":
        syn_severity = _loss_severity_from_values((worst_syn.get("portfolio_loss_pct"),)) or "unknown"
        _add_stress_scenario_problem(
            problems,
            problem_id="weak_crisis_resilience",
            severity=syn_severity,
            confidence=confidence,
            source_section=SCORECARD_V1_BLOCK,
            source_field="worst_synthetic_scenario",
            scenario_id=worst_syn.get("scenario_id") or signals.get("worst_synthetic_id"),
            loss_severity=syn_severity,
            extra={
                "portfolio_loss_pct": worst_syn.get("portfolio_loss_pct"),
                "stress_severity": signals.get("stress_severity"),
            },
        )

    worst_hist = scorecard.get("worst_historical_scenario")
    worst_hist = worst_hist if isinstance(worst_hist, dict) else {}
    if worst_hist.get("availability") == "available":
        hist_severity = _loss_severity_from_values(
            (worst_hist.get("drawdown_pct"), worst_hist.get("portfolio_loss_pct"))
        ) or "unknown"
        _add_stress_scenario_problem(
            problems,
            problem_id="high_drawdown_risk",
            severity=hist_severity,
            confidence=confidence,
            source_section=SCORECARD_V1_BLOCK,
            source_field="worst_historical_scenario",
            scenario_id=worst_hist.get("episode") or signals.get("worst_historical_episode"),
            loss_severity=hist_severity,
            extra={
                "drawdown_pct": worst_hist.get("drawdown_pct"),
                "stress_severity": signals.get("stress_severity"),
            },
        )


def _collect_stress_legacy(
    problems: dict[str, dict[str, Any]],
    stress_report: dict[str, Any],
) -> None:
    conclusions = stress_report.get("stress_conclusions")
    conclusions = conclusions if isinstance(conclusions, dict) else {}
    legacy_scorecard = stress_report.get("stress_scorecard_v1")
    legacy_scorecard = legacy_scorecard if isinstance(legacy_scorecard, dict) else {}
    confidence = _normalize_confidence(
        conclusions.get("overall_confidence") or legacy_scorecard.get("overall_confidence")
    )

    for field, problem_id in (
        ("worst_synthetic_scenario", "weak_crisis_resilience"),
        ("worst_historical_episode", "high_drawdown_risk"),
    ):
        row = conclusions.get(field)
        if not isinstance(row, dict):
            continue
        severity = _normalize_severity(row.get("loss_severity"), default="unknown")
        if severity == "unknown":
            severity = _loss_severity_from_values(
                (row.get("portfolio_pnl_pct"), row.get("pnl_real_episode"), row.get("max_dd"))
            ) or "unknown"
        _add_stress_scenario_problem(
            problems,
            problem_id=problem_id,
            severity=severity,
            confidence=confidence,
            source_section="stress_conclusions",
            source_field=field,
            scenario_id=row.get("scenario_id") or row.get("episode"),
            loss_severity=severity,
            extra={"evidence_path": "legacy_fallback"},
        )

    overall_status = str(
        legacy_scorecard.get("overall_status") or stress_report.get("status") or ""
    )
    loss_gate_mode = str(stress_report.get("loss_gate_mode") or "mandate")
    if loss_gate_mode == "mandate" and overall_status in {"DIAG_ATTENTION", "FAIL_STRESS", "FAIL"}:
        _add_problem(
            problems,
            "weak_crisis_resilience",
            severity="high" if overall_status.startswith("FAIL") else "moderate",
            confidence=confidence,
            evidence={
                "source_artifact": "stress_report.json",
                "source_section": STRESS_SCORECARD_SOURCE_LEGACY,
                "source_field": "overall_status",
                "status": overall_status,
                "evidence_path": "legacy_fallback",
            },
        )
    elif loss_gate_mode == "diagnostic" and overall_status == "insufficient_data":
        _add_problem(
            problems,
            "weak_crisis_resilience",
            severity="moderate",
            confidence=confidence,
            evidence={
                "source_artifact": "stress_report.json",
                "source_section": STRESS_SCORECARD_SOURCE_LEGACY,
                "source_field": "overall_status",
                "status": overall_status,
                "note": "data_quality_only_not_mandate_gate",
                "evidence_path": "legacy_fallback",
            },
        )


def _collect_stress_scorecard_v1_status_hooks(
    problems: dict[str, dict[str, Any]],
    stress_report: dict[str, Any],
    *,
    confidence: str,
) -> None:
    loss_gate_mode = str(stress_report.get("loss_gate_mode") or "diagnostic")
    report_status = str(stress_report.get("status") or "")
    if loss_gate_mode == "diagnostic" and report_status == "insufficient_data":
        _add_problem(
            problems,
            "weak_crisis_resilience",
            severity="moderate",
            confidence=confidence,
            evidence={
                "source_artifact": "stress_report.json",
                "source_section": SCORECARD_V1_BLOCK,
                "source_field": "status",
                "status": report_status,
                "note": "data_quality_only_not_mandate_gate",
            },
        )
        return
    if loss_gate_mode != "mandate":
        return
    legacy_scorecard = stress_report.get("stress_scorecard_v1")
    legacy_scorecard = legacy_scorecard if isinstance(legacy_scorecard, dict) else {}
    overall_status = str(legacy_scorecard.get("overall_status") or "")
    if overall_status in {"DIAG_ATTENTION", "FAIL_STRESS", "FAIL"}:
        _add_problem(
            problems,
            "weak_crisis_resilience",
            severity="high" if overall_status.startswith("FAIL") else "moderate",
            confidence=confidence,
            evidence={
                "source_artifact": "stress_report.json",
                "source_section": STRESS_SCORECARD_SOURCE_LEGACY,
                "source_field": "overall_status",
                "status": overall_status,
                "evidence_path": "legacy_mandate_rollup",
            },
        )


def _collect_stress(
    problems: dict[str, dict[str, Any]],
    stress_report: dict[str, Any] | None,
) -> tuple[str | None, str | None]:
    """Return (hedge_gap_source, stress_scorecard_source)."""
    if not isinstance(stress_report, dict):
        return None, None

    conclusions = stress_report.get("stress_conclusions")
    conclusions = conclusions if isinstance(conclusions, dict) else {}
    legacy_scorecard = stress_report.get("stress_scorecard_v1")
    legacy_scorecard = legacy_scorecard if isinstance(legacy_scorecard, dict) else {}

    scorecard_v1 = _scorecard_v1_block(stress_report)
    stress_scorecard_source: str | None = None
    if scorecard_v1 is not None and str(scorecard_v1.get("block_status") or "") != "unavailable":
        confidence = _confidence_from_scorecard_diagnosis(scorecard_v1)
        _collect_stress_scorecard_v1(problems, stress_report, scorecard_v1)
        _collect_stress_scorecard_v1_status_hooks(
            problems,
            stress_report,
            confidence=confidence,
        )
        stress_scorecard_source = STRESS_SCORECARD_SOURCE_V1
    else:
        _collect_stress_legacy(problems, stress_report)
        confidence = _normalize_confidence(
            conclusions.get("overall_confidence") or legacy_scorecard.get("overall_confidence")
        )
        stress_scorecard_source = STRESS_SCORECARD_SOURCE_LEGACY

    hedge_gap_source = _collect_hedge_gap_v1(problems, stress_report, confidence=confidence)
    if hedge_gap_source is None:
        hedge_gap_source = _collect_hedge_gap_legacy_fallback(
            problems,
            conclusions,
            confidence=confidence,
        )
    return hedge_gap_source, stress_scorecard_source


def build_problem_classification(
    *,
    portfolio_xray: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    analysis_end: str | None = None,
) -> dict[str, Any]:
    """Build ``problem_classification_v1`` from existing diagnostic artifacts."""

    problems: dict[str, dict[str, Any]] = {}
    sections = _sections(portfolio_xray)
    _collect_block_2_6_weakness_map(problems, portfolio_xray)
    _collect_allocation(problems, sections)
    _collect_risk_metrics(problems, sections)
    _collect_factor_exposure(problems, sections)
    _collect_data_review(problems, sections)
    hedge_gap_source, stress_scorecard_source = _collect_stress(problems, stress_report)

    top = sorted(
        problems.values(),
        key=lambda row: (
            -_SEVERITY_SCORE.get(str(row.get("severity") or "unknown"), 0),
            str(row.get("problem_id") or ""),
        ),
    )[:3]
    if not top:
        top = [
            {
                "problem_id": "current_portfolio_acceptable",
                "label": PROBLEM_LABELS["current_portfolio_acceptable"],
                "severity": "low",
                "confidence": "medium",
                "evidence": [
                    {
                        "source_artifact": "portfolio_xray.json",
                        "source_section": "summary",
                        "summary": "No high-priority problem was detected by the deterministic classification rules.",
                    }
                ],
                "reasonable_paths_to_test": list(PROBLEM_TO_PATHS["current_portfolio_acceptable"]),
            }
        ]

    warnings: list[str] = []
    if not isinstance(portfolio_xray, dict):
        warnings.append("missing_portfolio_xray")
    if not isinstance(stress_report, dict):
        warnings.append("missing_stress_report")

    return {
        "schema_version": PROBLEM_CLASSIFICATION_VERSION,
        "diagnostic_only": True,
        "generated_at": _utc_now_iso(),
        "analysis_end": analysis_end,
        "source_artifacts": {
            "portfolio_xray": "portfolio_xray.json" if isinstance(portfolio_xray, dict) else None,
            "stress_report": "stress_report.json" if isinstance(stress_report, dict) else None,
        },
        "weakness_map_source": WEAKNESS_MAP_SOURCE_BLOCK
        if isinstance(portfolio_xray, dict)
        and isinstance(portfolio_xray.get(WEAKNESS_MAP_SOURCE_BLOCK), dict)
        else None,
        "hedge_gap_source": hedge_gap_source,
        "stress_scorecard_source": stress_scorecard_source,
        "problems": top,
        "summary": {
            "n_problems": len(top),
            "primary_problem_id": top[0]["problem_id"] if top else None,
            "current_portfolio_acceptable": top[0]["problem_id"] == "current_portfolio_acceptable",
        },
        "warnings": warnings,
    }


def write_problem_classification_outputs(
    *,
    output_dir: str | Path,
    portfolio_xray: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    analysis_end: str | None = None,
) -> Path:
    """Write ``problem_classification.json`` under ``output_dir``."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = build_problem_classification(
        portfolio_xray=portfolio_xray,
        stress_report=stress_report,
        analysis_end=analysis_end,
    )
    path = out / PROBLEM_CLASSIFICATION_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
    return path
