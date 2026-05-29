"""Block 4 v2 diagnosis facade and JSON writers (Session 10).

Orchestrates evidence extraction through launchpad card generation and writes
``problem_classification.json`` + ``candidate_launchpad.json`` (v2 schema).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.block_4.action_path_mapping import ActionPathMappingResult, map_action_paths
from src.block_4.evidence_extraction import EvidenceExtractionResult, extract_evidence_signals
from src.block_4.launchpad_cards import build_candidate_launchpad_v2_document
from src.block_4.no_trade_gate import (
    NoTradeGateResult,
    build_diagnosis_summary,
    evaluate_no_trade_gate,
)
from src.block_4.problem_prioritization import ProblemPrioritizationResult, prioritize_problems
from src.block_4.problem_scoring import ProblemScoringResult, score_problems
from src.block_4.thresholds import get_block_4_thresholds
from src.candidate_launchpad import CANDIDATE_LAUNCHPAD_FILENAME
from src.problem_classification import PROBLEM_CLASSIFICATION_FILENAME

PROBLEM_CLASSIFICATION_V2_VERSION = "problem_classification_v2"
BLOCK_4_DIAGNOSIS_FACADE_VERSION = "build_block_4_diagnosis_v1"

HEDGE_GAP_SOURCE_V1 = "hedge_gap_analysis_v1"
HEDGE_GAP_SOURCE_LEGACY = "stress_conclusions.hedge_gap_status"
STRESS_SCORECARD_SOURCE_V1 = "current_portfolio_stress_scorecard_v1"
STRESS_SCORECARD_SOURCE_LEGACY = "stress_scorecard_v1"
WEAKNESS_MAP_SOURCE_BLOCK = "block_2_6_portfolio_weakness_map"


@dataclass
class Block4DiagnosisResult:
    problem_classification: dict[str, Any]
    candidate_launchpad: dict[str, Any]
    evidence: EvidenceExtractionResult
    scoring: ProblemScoringResult
    prioritization: ProblemPrioritizationResult
    mapping: ActionPathMappingResult
    gate: NoTradeGateResult
    status: str

    @property
    def primary_problem_id(self) -> str:
        return str(self.problem_classification["primary_problem"]["problem_id"])


@dataclass(frozen=True)
class Block4DiagnosisWriteResult:
    problem_classification_path: Path
    candidate_launchpad_path: Path
    diagnosis: Block4DiagnosisResult


def build_block_4_diagnosis(
    *,
    portfolio_xray: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    analysis_end: str | None = None,
    generated_at: str | None = None,
) -> Block4DiagnosisResult:
    """Run the Block 4 v2 evidence-to-problem pipeline and return both JSON documents."""
    xray = portfolio_xray if isinstance(portfolio_xray, dict) else {}
    stress = stress_report if isinstance(stress_report, dict) else {}

    evidence = extract_evidence_signals(xray, stress)
    scoring = score_problems(evidence)
    prioritization = prioritize_problems(scoring, evidence)
    mapping = map_action_paths(prioritization, scoring)
    gate = evaluate_no_trade_gate(mapping, scoring, evidence, prioritization=prioritization)

    status = _builder_status(evidence, xray, stress)
    warnings = _builder_warnings(evidence, xray, stress)
    hedge_gap_source, stress_scorecard_source = _provenance_sources(xray, stress)

    rejected_rows = [row.to_dict() for row in prioritization.rejected_problems]
    problems_shim = [_mirror_problem_row_for_v1_shim(row) for row in mapping.problem_rows]

    cfg = get_block_4_thresholds()
    problem_classification: dict[str, Any] = {
        "schema_version": PROBLEM_CLASSIFICATION_V2_VERSION,
        "diagnostic_only": True,
        "diagnosis_mode": "current_portfolio_problem_classification",
        "ruleset_version": cfg.ruleset_version,
        "status": status,
        "generated_at": generated_at or _utc_now_iso(),
        "analysis_end": analysis_end,
        "source_artifacts": {
            "portfolio_xray": "portfolio_xray.json" if xray else None,
            "stress_report": "stress_report.json" if stress else None,
        },
        "primary_problem": mapping.primary_problem,
        "secondary_problems": list(mapping.secondary_problems),
        "rejected_problems": rejected_rows,
        "suggested_actions": [row.to_dict() for row in mapping.suggested_actions],
        "no_trade_or_monitoring_view": gate.to_dict(),
        "data_quality_warnings": list(evidence.data_quality_warnings),
        "diagnostics_meta": {
            "evidence_signal_count": evidence.signal_count,
            "problems_evaluated": scoring.problems_evaluated,
            "problems_activated": prioritization.problems_activated,
            "block_4_facade_version": BLOCK_4_DIAGNOSIS_FACADE_VERSION,
            "legacy_sections_fallback_used": evidence.legacy_sections_fallback_used,
        },
        "problems": problems_shim,
        "summary": build_diagnosis_summary(
            mapping,
            gate,
            n_rejected=len(rejected_rows),
        ),
        "warnings": warnings,
    }

    if hedge_gap_source is not None:
        problem_classification["hedge_gap_source"] = hedge_gap_source
    if stress_scorecard_source is not None:
        problem_classification["stress_scorecard_source"] = stress_scorecard_source
    if isinstance(xray.get(WEAKNESS_MAP_SOURCE_BLOCK), dict):
        problem_classification["weakness_map_source"] = WEAKNESS_MAP_SOURCE_BLOCK

    candidate_launchpad = build_candidate_launchpad_v2_document(
        mapping,
        analysis_end=analysis_end,
        generated_at=problem_classification["generated_at"],
        scoring=scoring,
        evidence=evidence,
        no_trade_gate=gate,
        ruleset_version=cfg.ruleset_version,
    )

    return Block4DiagnosisResult(
        problem_classification=problem_classification,
        candidate_launchpad=candidate_launchpad,
        evidence=evidence,
        scoring=scoring,
        prioritization=prioritization,
        mapping=mapping,
        gate=gate,
        status=status,
    )


def write_block_4_diagnosis_outputs(
    *,
    output_dir: str | Path,
    portfolio_xray: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    analysis_end: str | None = None,
) -> Block4DiagnosisWriteResult:
    """Write v2 ``problem_classification.json`` and ``candidate_launchpad.json``."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    diagnosis = build_block_4_diagnosis(
        portfolio_xray=portfolio_xray,
        stress_report=stress_report,
        analysis_end=analysis_end,
    )

    pc_path = out / PROBLEM_CLASSIFICATION_FILENAME
    lp_path = out / CANDIDATE_LAUNCHPAD_FILENAME

    with pc_path.open("w", encoding="utf-8") as handle:
        json.dump(diagnosis.problem_classification, handle, indent=2, ensure_ascii=False, default=str)
    with lp_path.open("w", encoding="utf-8") as handle:
        json.dump(diagnosis.candidate_launchpad, handle, indent=2, ensure_ascii=False, default=str)

    return Block4DiagnosisWriteResult(
        problem_classification_path=pc_path,
        candidate_launchpad_path=lp_path,
        diagnosis=diagnosis,
    )


def block_4_manifest_extra(
    problem_classification: dict[str, Any] | None,
    candidate_launchpad: dict[str, Any] | None,
) -> dict[str, Any]:
    """Manifest ``extra`` block for Block 4 v2 wiring."""
    if not isinstance(problem_classification, dict):
        return {}
    if problem_classification.get("schema_version") != PROBLEM_CLASSIFICATION_V2_VERSION:
        return {}
    summary = problem_classification.get("summary") if isinstance(problem_classification.get("summary"), dict) else {}
    return {
        "block_4_diagnosis": {
            "schema_version": PROBLEM_CLASSIFICATION_V2_VERSION,
            "launchpad_schema_version": (
                candidate_launchpad.get("schema_version")
                if isinstance(candidate_launchpad, dict)
                else None
            ),
            "ruleset_version": problem_classification.get("ruleset_version"),
            "status": problem_classification.get("status"),
            "primary_problem_id": summary.get("primary_problem_id"),
            "no_trade_outcome": summary.get("no_trade_outcome"),
            "facade_version": BLOCK_4_DIAGNOSIS_FACADE_VERSION,
        }
    }


def _mirror_problem_row_for_v1_shim(row: dict[str, Any]) -> dict[str, Any]:
    mirrored = dict(row)
    mirrored["label"] = row.get("label_en")
    severity = str(row.get("severity") or "")
    if severity == "medium":
        mirrored["severity"] = "moderate"
    evidence_refs = row.get("evidence_refs") if isinstance(row.get("evidence_refs"), list) else []
    mirrored["evidence"] = [_compact_evidence_ref(ref) for ref in evidence_refs if isinstance(ref, dict)]
    return mirrored


def _compact_evidence_ref(ref: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "source_artifact": ref.get("source_artifact"),
        "source_block": ref.get("source_block"),
        "signal": ref.get("signal"),
        "interpretation_en": ref.get("interpretation_en"),
        "value": ref.get("value"),
        "evidence_path": ref.get("evidence_path"),
    }
    if ref.get("linked_assets"):
        compact["linked_assets"] = ref.get("linked_assets")
    if ref.get("limitation_en"):
        compact["limitation_en"] = ref.get("limitation_en")
    return compact


def _builder_status(
    evidence: EvidenceExtractionResult,
    portfolio_xray: dict[str, Any],
    stress_report: dict[str, Any],
) -> str:
    if not portfolio_xray or not stress_report:
        return "unavailable"
    if evidence.data_quality_warnings or evidence.has_signal("partial_sections"):
        return "partial"
    if evidence.has_signal("stress_block_unavailable"):
        return "partial"
    return "ok"


def _builder_warnings(
    evidence: EvidenceExtractionResult,
    portfolio_xray: dict[str, Any],
    stress_report: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if not portfolio_xray:
        warnings.append("missing_portfolio_xray")
    if not stress_report:
        warnings.append("missing_stress_report")
    if evidence.legacy_sections_fallback_used:
        warnings.append("legacy_sections_fallback_used")
    return warnings


def _provenance_sources(
    portfolio_xray: dict[str, Any],
    stress_report: dict[str, Any],
) -> tuple[str | None, str | None]:
    hedge_gap_source: str | None = None
    stress_scorecard_source: str | None = None

    if stress_report.get("hedge_gap_analysis_v1"):
        hedge_gap_source = HEDGE_GAP_SOURCE_V1
    elif stress_report.get("stress_conclusions"):
        hedge_gap_source = HEDGE_GAP_SOURCE_LEGACY

    if stress_report.get("current_portfolio_stress_scorecard_v1"):
        stress_scorecard_source = STRESS_SCORECARD_SOURCE_V1
    elif stress_report.get("stress_scorecard_v1") or stress_report.get("stress_conclusions"):
        stress_scorecard_source = STRESS_SCORECARD_SOURCE_LEGACY

    return hedge_gap_source, stress_scorecard_source


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
