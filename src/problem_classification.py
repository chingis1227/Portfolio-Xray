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

PROBLEM_CLASSIFICATION_VERSION = "problem_classification_v1"
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


def _problem_id_from_risk(risk: str) -> str | None:
    text = risk.lower()
    if "drawdown" in text:
        return "high_drawdown_risk"
    if "volatility" in text or "vol" in text:
        return "high_volatility"
    if "hedge" in text:
        return "weak_hedge_behavior"
    if "crisis" in text or "stress" in text:
        return "weak_crisis_resilience"
    if "concentration" in text:
        return "high_concentration"
    if "divers" in text:
        return "poor_diversification"
    return None


def _collect_weakness_map(problems: dict[str, dict[str, Any]], sections: dict[str, Any]) -> None:
    for item in _items(sections.get("weakness_map")):
        risk = str(item.get("risk") or item.get("weakness_id") or item.get("type") or "")
        problem_id = _problem_id_from_risk(risk)
        if not problem_id:
            continue
        _add_problem(
            problems,
            problem_id,
            severity=_normalize_severity(item.get("severity") or item.get("risk_level")),
            confidence=_normalize_confidence(item.get("confidence") or item.get("evidence_confidence")),
            evidence={
                "source_artifact": "portfolio_xray.json",
                "source_section": "weakness_map",
                "source_item_type": item.get("type"),
                "risk": risk,
                "summary": item.get("summary") or item.get("description") or item.get("interpretation"),
            },
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


def _collect_stress(problems: dict[str, dict[str, Any]], stress_report: dict[str, Any] | None) -> None:
    if not isinstance(stress_report, dict):
        return
    conclusions = stress_report.get("stress_conclusions")
    conclusions = conclusions if isinstance(conclusions, dict) else {}
    scorecard = stress_report.get("stress_scorecard_v1")
    scorecard = scorecard if isinstance(scorecard, dict) else {}
    confidence = _normalize_confidence(
        conclusions.get("overall_confidence") or scorecard.get("overall_confidence")
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
        if severity in {"moderate", "high"}:
            _add_problem(
                problems,
                problem_id,
                severity=severity,
                confidence=confidence,
                evidence={
                    "source_artifact": "stress_report.json",
                    "source_section": "stress_conclusions",
                    "source_field": field,
                    "scenario_id": row.get("scenario_id") or row.get("episode"),
                    "loss_severity": severity,
                },
            )

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
            },
        )

    overall_status = str(scorecard.get("overall_status") or stress_report.get("status") or "")
    loss_gate_mode = str(stress_report.get("loss_gate_mode") or "mandate")
    if loss_gate_mode == "mandate" and overall_status in {"DIAG_ATTENTION", "FAIL_STRESS", "FAIL"}:
        _add_problem(
            problems,
            "weak_crisis_resilience",
            severity="high" if overall_status.startswith("FAIL") else "moderate",
            confidence=confidence,
            evidence={
                "source_artifact": "stress_report.json",
                "source_section": "stress_scorecard_v1",
                "source_field": "overall_status",
                "status": overall_status,
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
                "source_section": "stress_scorecard_v1",
                "source_field": "overall_status",
                "status": overall_status,
                "note": "data_quality_only_not_mandate_gate",
            },
        )


def build_problem_classification(
    *,
    portfolio_xray: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    analysis_end: str | None = None,
) -> dict[str, Any]:
    """Build ``problem_classification_v1`` from existing diagnostic artifacts."""

    problems: dict[str, dict[str, Any]] = {}
    sections = _sections(portfolio_xray)
    _collect_weakness_map(problems, sections)
    _collect_allocation(problems, sections)
    _collect_risk_metrics(problems, sections)
    _collect_factor_exposure(problems, sections)
    _collect_data_review(problems, sections)
    _collect_stress(problems, stress_report)

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
