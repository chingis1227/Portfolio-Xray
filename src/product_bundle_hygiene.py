"""Product bundle hygiene for diagnosis-only and core Blocks 1–3 runtime modes.

- Diagnosis-only: tombstone stale post-compare root JSON (`no_candidate_v1`).
- Core Blocks 1–3 only: remove Block 4+ subject JSON and all root compare/decision files.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ai_commentary_context import AI_COMMENTARY_CONTEXT_FILENAME
from src.candidate_comparison import SCHEMA_VERSION as CANDIDATE_COMPARISON_SCHEMA_VERSION
from src.candidate_launchpad import CANDIDATE_LAUNCHPAD_FILENAME
from src.current_vs_candidate import (
    CURRENT_VS_CANDIDATE_FILENAME,
    CURRENT_VS_CANDIDATE_VERSION,
)
from src.decision_verdict import DECISION_VERDICT_FILENAME, DECISION_VERDICT_VERSION
from src.portfolio_alternatives_builder import PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
from src.problem_classification import PROBLEM_CLASSIFICATION_FILENAME
from src.product_bundle_scope import PRODUCT_BUNDLE_SCOPE_CORE_BLOCKS_1_3

NO_CANDIDATE_TOMBSTONE = "no_candidate_v1"
ARTIFACT_STATUS_NOT_AUTHORITATIVE = "not_authoritative"
WORKFLOW_STATE_DIAGNOSIS_ONLY = "diagnosis_only"

TOMBSTONE_COMPARE_FILENAMES: tuple[str, ...] = (
    CURRENT_VS_CANDIDATE_FILENAME,
    DECISION_VERDICT_FILENAME,
    "candidate_comparison.json",
)

STALE_POST_COMPARE_REMOVE_FILENAMES: tuple[str, ...] = (
    "candidate_comparison_registry.json",
    "candidate_comparison.txt",
    "candidate_factory_run.json",
    "candidate_factory_run.txt",
    "selection_decision.json",
    "selection_decision.txt",
    "portfolio_health_score.json",
    "portfolio_health_score.txt",
    "robustness_scorecard.json",
    "robustness_scorecard.txt",
    "action_plan.json",
    "action_plan.txt",
    "monitoring_diff.json",
    "monitoring_diff.txt",
    "decision_journal.json",
    "decision_journal.txt",
    "tradeoff_explanation.json",
    "model_risk_diagnostics.json",
    "assumption_sensitivity.json",
    "pareto_dominance.json",
    "regret_analysis.json",
    "portfolio_comparison.json",
    "portfolio_comparison.txt",
    "what_changed_summary.json",
)

CORE_BLOCKS_SUBJECT_BLOCK4_FILENAMES: tuple[str, ...] = (
    PROBLEM_CLASSIFICATION_FILENAME,
    CANDIDATE_LAUNCHPAD_FILENAME,
    PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME,
    AI_COMMENTARY_CONTEXT_FILENAME,
)

CORE_BLOCKS_ROOT_REMOVE_FILENAMES: tuple[str, ...] = (
    *TOMBSTONE_COMPARE_FILENAMES,
    *STALE_POST_COMPARE_REMOVE_FILENAMES,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_no_candidate_current_vs_candidate(
    *,
    analysis_end: str | None = None,
    output_dir_final: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": CURRENT_VS_CANDIDATE_VERSION,
        "diagnostic_only": True,
        "tombstone": NO_CANDIDATE_TOMBSTONE,
        "artifact_status": ARTIFACT_STATUS_NOT_AUTHORITATIVE,
        "generated_at": _utc_now_iso(),
        "analysis_end": analysis_end,
        "primary_window": "10y",
        "view_mode": "diagnosis_only",
        "workflow_state": WORKFLOW_STATE_DIAGNOSIS_ONLY,
        "baseline": {
            "candidate_id": "analysis_subject",
            "display_name": None,
            "status": None,
            "role": "analysis_subject",
        },
        "selected_candidate_ids": [],
        "comparisons": [],
        "source_artifacts": {
            "candidate_comparison": None,
            "selection_decision": None,
        },
        "output_dir_final": output_dir_final,
        "product_run": build_product_run_metadata(
            run_id=f"diagnosis_only:{analysis_end or 'unknown'}:{output_dir_final or 'unknown'}",
            artifact_role=CURRENT_VS_CANDIDATE_FILENAME,
            workflow_state=WORKFLOW_STATE_DIAGNOSIS_ONLY,
            active=False,
        ),
        "warnings": ["no_candidate_selected", "product_bundle_hygiene"],
    }


def build_no_candidate_decision_verdict(
    *,
    analysis_end: str | None = None,
    output_dir_final: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": DECISION_VERDICT_VERSION,
        "diagnostic_only": True,
        "tombstone": NO_CANDIDATE_TOMBSTONE,
        "artifact_status": ARTIFACT_STATUS_NOT_AUTHORITATIVE,
        "generated_at": _utc_now_iso(),
        "analysis_end": analysis_end,
        "workflow_state": WORKFLOW_STATE_DIAGNOSIS_ONLY,
        "verdict_id": "no_candidate_selected",
        "verdict_label": "No candidate selected for comparison",
        "verdict_family": "core_compare",
        "selection_decision_status": "data_review_required",
        "baseline_candidate_id": "analysis_subject",
        "selected_candidate_id": None,
        "no_trade": {"evaluated": False, "applies": False, "source": None},
        "recommended_action": (
            "Diagnosis-only run completed; use --candidates to compare a hypothesis "
            "or read Blocks 1–3 evidence under analysis_subject/."
        ),
        "confidence": "low",
        "confidence_limitations": ["no_candidate_selected", "product_bundle_hygiene"],
        "rationale_summary": None,
        "source_artifacts": {
            "selection_decision": None,
            "current_vs_candidate": CURRENT_VS_CANDIDATE_FILENAME,
            "action_plan": None,
        },
        "output_dir_final": output_dir_final,
        "warnings": ["no_candidate_selected", "product_bundle_hygiene"],
        "guardrails": {
            "does_not_rename_selection_engine_contract": True,
            "does_not_change_selection_formulas": True,
            "does_not_execute_trades": True,
        },
        "product_run": build_product_run_metadata(
            run_id=f"diagnosis_only:{analysis_end or 'unknown'}:{output_dir_final or 'unknown'}",
            artifact_role=DECISION_VERDICT_FILENAME,
            workflow_state=WORKFLOW_STATE_DIAGNOSIS_ONLY,
            upstream_run_ids={"current_vs_candidate": f"diagnosis_only:{analysis_end or 'unknown'}:{output_dir_final or 'unknown'}"},
            active=False,
        ),
    }


def build_no_candidate_comparison_tombstone(
    *,
    analysis_end: str | None = None,
    output_dir_final: str | None = None,
    investor_currency: str = "USD",
) -> dict[str, Any]:
    return {
        "schema_version": CANDIDATE_COMPARISON_SCHEMA_VERSION,
        "diagnostic_only": True,
        "tombstone": NO_CANDIDATE_TOMBSTONE,
        "artifact_status": ARTIFACT_STATUS_NOT_AUTHORITATIVE,
        "generated_at": _utc_now_iso(),
        "analysis_end": analysis_end,
        "investor_currency": investor_currency,
        "output_dir_final": output_dir_final,
        "comparison_baseline_candidate_id": "analysis_subject",
        "workflow_state": WORKFLOW_STATE_DIAGNOSIS_ONLY,
        "candidates": [],
        "candidate_menu": {
            "is_partial_menu": True,
            "partial_menu_reason": "diagnosis_only_no_candidate_scope",
            "factory_evidence_status": "not_applicable",
        },
        "product_candidate_scope": None,
        "product_run": build_product_run_metadata(
            run_id=f"diagnosis_only:{analysis_end or 'unknown'}:{output_dir_final or 'unknown'}",
            artifact_role="candidate_comparison.json",
            workflow_state=WORKFLOW_STATE_DIAGNOSIS_ONLY,
            active=False,
        ),
        "warnings": ["no_candidate_selected", "product_bundle_hygiene"],
    }



def build_product_run_metadata(
    *,
    run_id: str,
    artifact_role: str,
    workflow_state: str,
    upstream_run_ids: Mapping[str, str | None] | None = None,
    active: bool = True,
) -> dict[str, Any]:
    """Return compact freshness metadata for product-bundle artifacts.

    The metadata is intentionally generic so historical files can remain on disk
    while readers can tell whether candidate, comparison, verdict, and AI context
    belong to the same vertical product run.
    """

    return {
        "run_id": str(run_id),
        "artifact_role": str(artifact_role),
        "workflow_state": str(workflow_state),
        "active": bool(active),
        "generated_at": _utc_now_iso(),
        "upstream_run_ids": dict(upstream_run_ids or {}),
    }


def attach_product_run_metadata(
    document: Mapping[str, Any],
    *,
    run_id: str,
    artifact_role: str,
    workflow_state: str,
    upstream_run_ids: Mapping[str, str | None] | None = None,
    active: bool = True,
) -> dict[str, Any]:
    """Return a copy of ``document`` with product-run freshness metadata."""

    enriched = copy.deepcopy(dict(document))
    enriched["product_run"] = build_product_run_metadata(
        run_id=run_id,
        artifact_role=artifact_role,
        workflow_state=workflow_state,
        upstream_run_ids=upstream_run_ids,
        active=active,
    )
    return enriched


def product_run_id(document: Mapping[str, Any] | None) -> str | None:
    """Extract a product-run id from an artifact, if present."""

    product_run = document.get("product_run") if isinstance(document, Mapping) else None
    if not isinstance(product_run, Mapping):
        return None
    value = product_run.get("run_id")
    text = str(value or "").strip()
    return text or None


def _write_json(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, default=str)


def _remove_files(directory: Path, filenames: tuple[str, ...]) -> list[str]:
    removed: list[str] = []
    for name in filenames:
        path = directory / name
        if path.is_file():
            path.unlink()
            removed.append(name)
    return removed


def _remove_stale_post_compare_artifacts(output_dir: Path) -> list[str]:
    return _remove_files(output_dir, STALE_POST_COMPARE_REMOVE_FILENAMES)


def apply_diagnosis_only_product_bundle_hygiene(
    output_dir_final: str | Path,
    *,
    analysis_end: str | None = None,
    investor_currency: str = "USD",
) -> dict[str, Any]:
    """Refresh root compare/decision artifacts for diagnosis-only workflow."""
    out = Path(output_dir_final)
    out_rel = str(out).replace("\\", "/")
    removed = _remove_stale_post_compare_artifacts(out)

    current_vs_doc = build_no_candidate_current_vs_candidate(
        analysis_end=analysis_end,
        output_dir_final=out_rel,
    )
    verdict_doc = build_no_candidate_decision_verdict(
        analysis_end=analysis_end,
        output_dir_final=out_rel,
    )
    comparison_doc = build_no_candidate_comparison_tombstone(
        analysis_end=analysis_end,
        output_dir_final=out_rel,
        investor_currency=investor_currency,
    )

    written: dict[str, str] = {}
    for filename, doc in (
        (CURRENT_VS_CANDIDATE_FILENAME, current_vs_doc),
        (DECISION_VERDICT_FILENAME, verdict_doc),
        ("candidate_comparison.json", comparison_doc),
    ):
        path = out / filename
        _write_json(path, doc)
        written[filename] = str(path)

    return {
        "tombstone": NO_CANDIDATE_TOMBSTONE,
        "workflow_state": WORKFLOW_STATE_DIAGNOSIS_ONLY,
        "written": written,
        "removed_stale": removed,
    }


def apply_core_blocks_product_bundle_hygiene(
    output_dir_final: str | Path,
    *,
    subject_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Remove Block 4+ subject JSON and root post-compare artifacts for core-only runs."""
    out = Path(output_dir_final)
    subject = Path(subject_dir) if subject_dir is not None else out / "analysis_subject"
    removed_subject = (
        _remove_files(subject, CORE_BLOCKS_SUBJECT_BLOCK4_FILENAMES)
        if subject.is_dir()
        else []
    )
    removed_root = _remove_files(out, CORE_BLOCKS_ROOT_REMOVE_FILENAMES)
    return {
        "product_bundle_scope": PRODUCT_BUNDLE_SCOPE_CORE_BLOCKS_1_3,
        "removed_subject_block4": removed_subject,
        "removed_root_post_compare": removed_root,
    }


__all__ = [
    "NO_CANDIDATE_TOMBSTONE",
    "CORE_BLOCKS_ROOT_REMOVE_FILENAMES",
    "CORE_BLOCKS_SUBJECT_BLOCK4_FILENAMES",
    "TOMBSTONE_COMPARE_FILENAMES",
    "attach_product_run_metadata",
    "build_product_run_metadata",
    "product_run_id",
    "apply_core_blocks_product_bundle_hygiene",
    "apply_diagnosis_only_product_bundle_hygiene",
    "build_no_candidate_comparison_tombstone",
    "build_no_candidate_current_vs_candidate",
    "build_no_candidate_decision_verdict",
]
