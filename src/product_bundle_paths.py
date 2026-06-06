"""Resolve Core MVP product bundle paths for portfolio-first consumers (RM-ARCH-011).

Bundle phases (six JSON files, no merged ``product_bundle.json``):

- **After diagnosis / materialize (#1–2):** ``problem_classification.json``,
  ``candidate_launchpad.json`` under ``{output_dir_final}/analysis_subject/``.
- **After compare only (#3–6):** ``current_vs_candidate.json``, ``decision_verdict.json``,
  ``ai_commentary_context.json``, ``what_changed_summary.json`` at variant root.

``output_manifest.json`` → ``product_discovery`` exposes which keys exist on disk;
``product_bundle_complete`` is true only when all six are present.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from src.block_2_1_asset_allocation import BLOCK_2_1_ID
from src.block_2_2_portfolio_metrics import BLOCK_2_2_ID
from src.block_2_3_factor_exposure import BLOCK_2_3_ID
from src.block_2_4_hidden_exposure import BLOCK_2_4_ID
from src.block_2_5_risk_budget_view import BLOCK_2_5_ID
from src.block_2_6_portfolio_weakness_map import BLOCK_2_6_ID
from src.candidate_launchpad import CANDIDATE_LAUNCHPAD_FILENAME
from src.portfolio_alternatives_builder import PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
from src.problem_classification import PROBLEM_CLASSIFICATION_FILENAME

PORTFOLIO_XRAY_BLOCK_2_1_KEY = "block_2_1_asset_allocation"
PORTFOLIO_XRAY_BLOCK_2_2_KEY = "block_2_2_portfolio_metrics"
PORTFOLIO_XRAY_BLOCK_2_3_KEY = "block_2_3_factor_exposure"
PORTFOLIO_XRAY_BLOCK_2_4_KEY = "block_2_4_hidden_exposure"
PORTFOLIO_XRAY_BLOCK_2_5_KEY = "block_2_5_risk_budget_view"
PORTFOLIO_XRAY_BLOCK_2_6_KEY = "block_2_6_portfolio_weakness_map"

ANALYSIS_SUBJECT_SIDECAR_SUBDIR = "analysis_subject"

DiagnosisResolution = Literal["sidecar", "root", "missing"]


def _resolve_artifact_path(
    output_dir_final: Path,
    filename: str,
) -> tuple[Path | None, DiagnosisResolution]:
    """Prefer ``analysis_subject/``; fall back to variant root for legacy runs."""
    base = Path(output_dir_final)
    sidecar_path = base / ANALYSIS_SUBJECT_SIDECAR_SUBDIR / filename
    root_path = base / filename
    if sidecar_path.is_file():
        return sidecar_path, "sidecar"
    if root_path.is_file():
        return root_path, "root"
    return None, "missing"


def resolve_problem_classification_path(output_dir_final: Path) -> Path | None:
    path, _ = _resolve_artifact_path(output_dir_final, PROBLEM_CLASSIFICATION_FILENAME)
    return path


def resolve_candidate_launchpad_path(output_dir_final: Path) -> Path | None:
    path, _ = _resolve_artifact_path(output_dir_final, CANDIDATE_LAUNCHPAD_FILENAME)
    return path


def resolve_portfolio_alternatives_builder_path(output_dir_final: Path) -> Path | None:
    path, _ = _resolve_artifact_path(
        output_dir_final, PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
    )
    return path


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    return doc if isinstance(doc, dict) else None


PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS: tuple[str, ...] = (
    "problem_classification_json",
    "candidate_launchpad_json",
    "portfolio_alternatives_builder_json",
)

PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS: tuple[str, ...] = (
    "current_vs_candidate_json",
    "decision_verdict_json",
    "ai_commentary_context_json",
    "what_changed_summary_json",
)

PRODUCT_BUNDLE_MANIFEST_KEYS: tuple[str, ...] = (
    *PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS,
    *PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS,
)

TECHNICAL_COMPARISON_MANIFEST_KEYS: tuple[str, ...] = (
    "candidate_comparison_json",
    "selection_decision_json",
)

ADVANCED_EVIDENCE_MANIFEST_KEYS: tuple[str, ...] = (
    "portfolio_health_score_json",
    "robustness_scorecard_json",
    "tradeoff_explanation_json",
    "model_risk_diagnostics_json",
    "assumption_sensitivity_json",
    "pareto_dominance_json",
    "regret_analysis_json",
    "current_vs_policy_status_json",
    "action_plan_json",
    "monitoring_diff_json",
    "decision_journal_json",
    "decision_package_summary_json",
)

ORCHESTRATION_MANIFEST_KEYS: tuple[str, ...] = (
    "candidate_factory_run_json",
    "candidate_factory_manifest_json",
    "candidate_factory_run",
    "candidate_factory_manifest",
    "output_manifest_json",
)

LEGACY_COMPATIBILITY_MANIFEST_KEYS: tuple[str, ...] = (
    "run_result_json",
    "portfolio_weights_yml",
    "portfolio_weights_yaml",
    "current_vs_policy_status_json",
    "portfolio_comparison_json",
    "ew_rp_comparison_json",
    "portfolio_comparison_txt",
    "ew_rp_comparison_txt",
)

SUBJECT_DIAGNOSTICS_MANIFEST_KEYS: tuple[str, ...] = (
    "run_metadata",
    "data_policy",
    "portfolio_xray",
    "stress_report",
    "snapshot_10y",
    "snapshot_index",
    "run_metadata_json",
    "data_policy_json",
    "portfolio_xray_json",
    "stress_report_json",
    "snapshot_10y_json",
    "snapshot_index_json",
)

GENERATED_EXPORT_MANIFEST_SUFFIXES: tuple[str, ...] = (
    "_csv",
    "_txt",
    "_html",
    "_png",
    "_pdf",
)

ARTIFACT_CATEGORY_ORDER: tuple[str, ...] = (
    "product_bundle",
    "technical_comparison",
    "subject_diagnostics",
    "advanced_evidence",
    "orchestration",
    "legacy_compatibility",
    "generated_export",
)


def _normalize_manifest_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def product_bundle_generated_paths_for_manifest(output_dir_final: Path) -> dict[str, str]:
    """Resolved on-disk paths for Core MVP bundle artifacts (for output_manifest)."""
    base = Path(output_dir_final)
    out: dict[str, str] = {}

    problem_path = resolve_problem_classification_path(base)
    if problem_path is not None and problem_path.is_file():
        out["problem_classification_json"] = _normalize_manifest_path(problem_path)

    launchpad_path = resolve_candidate_launchpad_path(base)
    if launchpad_path is not None and launchpad_path.is_file():
        out["candidate_launchpad_json"] = _normalize_manifest_path(launchpad_path)

    builder_path = resolve_portfolio_alternatives_builder_path(base)
    if builder_path is not None and builder_path.is_file():
        out["portfolio_alternatives_builder_json"] = _normalize_manifest_path(builder_path)

    for key, filename in (
        ("current_vs_candidate_json", "current_vs_candidate.json"),
        ("decision_verdict_json", "decision_verdict.json"),
        ("ai_commentary_context_json", "ai_commentary_context.json"),
        ("what_changed_summary_json", "what_changed_summary.json"),
    ):
        path = base / filename
        if path.is_file():
            out[key] = _normalize_manifest_path(path)
    return out



def build_product_first_generated_paths(
    output_dir_final: Path,
    generated_paths: dict[str, str | Path | None] | None = None,
) -> dict[str, str | Path]:
    """Return manifest paths with Core MVP product bundle keys first."""
    ordered: dict[str, str | Path] = dict(
        product_bundle_generated_paths_for_manifest(output_dir_final)
    )
    for key, value in (generated_paths or {}).items():
        if value is None or str(key) in ordered:
            continue
        ordered[str(key)] = value
    return ordered


def _is_generated_export_manifest_key(key: str) -> bool:
    normalized = str(key).lower()
    return any(normalized.endswith(suffix) for suffix in GENERATED_EXPORT_MANIFEST_SUFFIXES)


def manifest_key_category(key: str) -> str:
    """Classify a manifest ``generated_paths`` key for UI/API discovery."""
    normalized = str(key)
    if normalized in PRODUCT_BUNDLE_MANIFEST_KEYS:
        return "product_bundle"
    if normalized in TECHNICAL_COMPARISON_MANIFEST_KEYS:
        return "technical_comparison"
    if normalized in SUBJECT_DIAGNOSTICS_MANIFEST_KEYS:
        return "subject_diagnostics"
    if normalized in ADVANCED_EVIDENCE_MANIFEST_KEYS:
        return "advanced_evidence"
    if normalized in ORCHESTRATION_MANIFEST_KEYS:
        return "orchestration"
    if normalized in LEGACY_COMPATIBILITY_MANIFEST_KEYS:
        return "legacy_compatibility"
    if _is_generated_export_manifest_key(normalized):
        return "generated_export"
    return "technical_comparison"


def product_bundle_artifact_categories() -> dict[str, list[str]]:
    """Manifest artifact categories: product first, old package separated."""
    return {
        "product_bundle": list(PRODUCT_BUNDLE_MANIFEST_KEYS),
        "technical_comparison": list(TECHNICAL_COMPARISON_MANIFEST_KEYS),
        "subject_diagnostics": list(SUBJECT_DIAGNOSTICS_MANIFEST_KEYS),
        "advanced_evidence": list(ADVANCED_EVIDENCE_MANIFEST_KEYS),
        "orchestration": list(ORCHESTRATION_MANIFEST_KEYS),
        "legacy_compatibility": list(LEGACY_COMPATIBILITY_MANIFEST_KEYS),
        "generated_export": [
            f"*{suffix}" for suffix in GENERATED_EXPORT_MANIFEST_SUFFIXES
        ],
    }


def _normalize_generated_paths_map(
    generated_paths: dict[str, str | Path | None] | None,
) -> dict[str, str]:
    return {
        str(key): str(value).replace("\\", "/")
        for key, value in (generated_paths or {}).items()
        if value is not None
    }


def build_generated_paths_by_category(
    generated_paths: dict[str, str | Path | None] | None,
) -> dict[str, dict[str, str]]:
    """Bucket resolved manifest paths by artifact category."""
    clean = _normalize_generated_paths_map(generated_paths)
    buckets: dict[str, dict[str, str]] = {
        category: {} for category in ARTIFACT_CATEGORY_ORDER
    }
    for key, path in clean.items():
        category = manifest_key_category(key)
        if category not in buckets:
            buckets[category] = {}
        buckets[category][key] = path
    return {category: paths for category, paths in buckets.items() if paths}


def _product_bundle_phase(
    diagnosis_paths: dict[str, str],
    post_compare_paths: dict[str, str],
) -> str:
    diagnosis_complete = len(diagnosis_paths) == len(PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS)
    post_compare_count = len(post_compare_paths)
    if diagnosis_complete and post_compare_count == len(PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS):
        return "complete"
    if diagnosis_complete and post_compare_count == 0:
        return "diagnosis_only"
    if diagnosis_complete or post_compare_count:
        return "post_compare_partial"
    return "absent"


def build_product_discovery_block(
    generated_paths: dict[str, str | Path | None] | None,
) -> dict[str, Any]:
    """Product-consumer manifest block: resolved bundle paths and presence phase."""
    clean = _normalize_generated_paths_map(generated_paths)
    product_paths = {
        key: clean[key] for key in PRODUCT_BUNDLE_MANIFEST_KEYS if key in clean
    }
    diagnosis_paths = {
        key: clean[key]
        for key in PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS
        if key in clean
    }
    post_compare_paths = {
        key: clean[key]
        for key in PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS
        if key in clean
    }
    diagnosis_complete = len(diagnosis_paths) == len(PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS)
    post_compare_complete = len(post_compare_paths) == len(
        PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS
    )
    return {
        "primary_output_surface": "product_bundle",
        "product_bundle_paths": product_paths,
        "product_bundle_complete": diagnosis_complete and post_compare_complete,
        "diagnosis_bundle_paths": diagnosis_paths,
        "diagnosis_bundle_complete": diagnosis_complete,
        "post_compare_bundle_paths": post_compare_paths,
        "post_compare_bundle_complete": post_compare_complete,
        "product_bundle_phase": _product_bundle_phase(diagnosis_paths, post_compare_paths),
        "read_order": list(PRODUCT_BUNDLE_MANIFEST_KEYS),
        "diagnosis_read_order": list(PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS),
        "post_compare_read_order": list(PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS),
    }


def discover_product_bundle_paths(manifest: dict[str, Any]) -> dict[str, str]:
    """Return resolved Core MVP paths from an ``output_manifest.json`` document."""
    discovery = manifest.get("product_discovery") or {}
    product_paths = discovery.get("product_bundle_paths")
    if isinstance(product_paths, dict):
        return {
            str(key): str(path).replace("\\", "/")
            for key, path in product_paths.items()
            if path
        }
    generated = manifest.get("generated_paths") or {}
    return {
        str(key): str(generated[key]).replace("\\", "/")
        for key in PRODUCT_BUNDLE_MANIFEST_KEYS
        if key in generated and generated[key]
    }


def discover_paths_by_category(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Return category-indexed paths; rebuild from ``generated_paths`` when needed."""
    by_category = manifest.get("generated_paths_by_category")
    if isinstance(by_category, dict) and by_category:
        return {
            str(category): {
                str(key): str(path).replace("\\", "/")
                for key, path in (paths or {}).items()
                if path
            }
            for category, paths in by_category.items()
            if isinstance(paths, dict)
        }
    generated = manifest.get("generated_paths") or {}
    return build_generated_paths_by_category(generated)


def portfolio_xray_has_block_2_1(doc: dict[str, Any] | None) -> bool:
    """True when ``portfolio_xray.json`` carries the Block 2.1 product contract."""
    if not isinstance(doc, dict):
        return False
    block = doc.get(PORTFOLIO_XRAY_BLOCK_2_1_KEY)
    return isinstance(block, dict) and block.get("block") == BLOCK_2_1_ID


def portfolio_xray_has_block_2_2(doc: dict[str, Any] | None) -> bool:
    """True when ``portfolio_xray.json`` carries the Block 2.2 product contract."""
    if not isinstance(doc, dict):
        return False
    block = doc.get(PORTFOLIO_XRAY_BLOCK_2_2_KEY)
    return isinstance(block, dict) and block.get("block") == BLOCK_2_2_ID


def portfolio_xray_has_block_2_3(doc: dict[str, Any] | None) -> bool:
    """True when ``portfolio_xray.json`` carries the Block 2.3 product contract."""
    if not isinstance(doc, dict):
        return False
    block = doc.get(PORTFOLIO_XRAY_BLOCK_2_3_KEY)
    return isinstance(block, dict) and block.get("block") == BLOCK_2_3_ID


def portfolio_xray_has_block_2_4(doc: dict[str, Any] | None) -> bool:
    """True when ``portfolio_xray.json`` carries the Block 2.4 product contract."""
    if not isinstance(doc, dict):
        return False
    block = doc.get(PORTFOLIO_XRAY_BLOCK_2_4_KEY)
    return isinstance(block, dict) and block.get("block") == BLOCK_2_4_ID


def portfolio_xray_has_block_2_5(doc: dict[str, Any] | None) -> bool:
    """True when ``portfolio_xray.json`` carries the Block 2.5 product contract."""
    if not isinstance(doc, dict):
        return False
    block = doc.get(PORTFOLIO_XRAY_BLOCK_2_5_KEY)
    return isinstance(block, dict) and block.get("block") == BLOCK_2_5_ID


def portfolio_xray_has_block_2_6(doc: dict[str, Any] | None) -> bool:
    """True when ``portfolio_xray.json`` carries the Block 2.6 product contract."""
    if not isinstance(doc, dict):
        return False
    block = doc.get(PORTFOLIO_XRAY_BLOCK_2_6_KEY)
    return isinstance(block, dict) and block.get("block") == BLOCK_2_6_ID


def subject_diagnostics_manifest_note() -> dict[str, Any]:
    """Manifest disclosure: product X-Ray blocks live inside ``portfolio_xray.json``."""
    return {
        "portfolio_xray_json": {
            "contract_version": "portfolio_xray_v2",
            "product_capital_structure_key": PORTFOLIO_XRAY_BLOCK_2_1_KEY,
            "product_portfolio_behavior_key": PORTFOLIO_XRAY_BLOCK_2_2_KEY,
            "product_factor_exposure_key": PORTFOLIO_XRAY_BLOCK_2_3_KEY,
            "product_hidden_exposure_key": PORTFOLIO_XRAY_BLOCK_2_4_KEY,
            "product_risk_budget_key": PORTFOLIO_XRAY_BLOCK_2_5_KEY,
            "product_weakness_map_key": PORTFOLIO_XRAY_BLOCK_2_6_KEY,
            "note": (
                "Block 2.1 capital allocation, Block 2.2 portfolio metrics, Block 2.3 factor exposure, "
                "Block 2.4 hidden exposure, Block 2.5 risk budget view, and Block 2.6 weakness map are nested under "
                "portfolio_xray.json (analysis_subject/ on portfolio-first runs), not separate "
                "bundle files."
            ),
        },
    }


def product_bundle_manifest_extra() -> dict[str, Any]:
    """Common manifest metadata that makes the Core MVP surface explicit."""
    return {
        "primary_output_surface": "product_bundle",
        "product_bundle_manifest_keys": list(PRODUCT_BUNDLE_MANIFEST_KEYS),
        "product_bundle_contract": {
            "artifact_count": len(PRODUCT_BUNDLE_MANIFEST_KEYS),
            "diagnosis_artifact_keys": list(PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS),
            "post_compare_artifact_keys": list(PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS),
            "diagnosis_present_after": "portfolio_review diagnosis or run_report materialize",
            "post_compare_present_after": (
                "candidate factory + compare (--candidates, --with-candidates, --mode full)"
            ),
            "merged_product_bundle_json": False,
            "advanced_artifacts_are_product_surface": False,
        },
        "subject_diagnostics_contract": subject_diagnostics_manifest_note(),
        "artifact_categories": product_bundle_artifact_categories(),
    }


def build_output_manifest_discovery_extra(
    generated_paths: dict[str, str | Path | None] | None = None,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Manifest ``extra`` payload: categories, resolved buckets, and product discovery."""
    doc = {
        **product_bundle_manifest_extra(),
        "generated_paths_by_category": build_generated_paths_by_category(generated_paths),
        "product_discovery": build_product_discovery_block(generated_paths),
    }
    if extra:
        doc.update(extra)
    return doc


def load_diagnosis_bundle_docs(output_dir_final: Path) -> dict[str, Any]:
    """Load diagnosis-phase JSON from resolved on-disk paths (subject sidecar first)."""
    problem_path, problem_resolution = _resolve_artifact_path(
        output_dir_final, PROBLEM_CLASSIFICATION_FILENAME
    )
    launchpad_path, launchpad_resolution = _resolve_artifact_path(
        output_dir_final, CANDIDATE_LAUNCHPAD_FILENAME
    )
    builder_path, builder_resolution = _resolve_artifact_path(
        output_dir_final, PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
    )
    xray_path, xray_resolution = _resolve_artifact_path(output_dir_final, "portfolio_xray.json")
    stress_path, stress_resolution = _resolve_artifact_path(output_dir_final, "stress_report.json")
    return {
        "problem_classification": _load_json(problem_path),
        "candidate_launchpad": _load_json(launchpad_path),
        "portfolio_alternatives_builder": _load_json(builder_path),
        "portfolio_xray": _load_json(xray_path),
        "stress_report": _load_json(stress_path),
        "problem_classification_path": problem_path,
        "candidate_launchpad_path": launchpad_path,
        "portfolio_alternatives_builder_path": builder_path,
        "portfolio_xray_path": xray_path,
        "stress_report_path": stress_path,
        "problem_classification_resolution": problem_resolution,
        "candidate_launchpad_resolution": launchpad_resolution,
        "portfolio_alternatives_builder_resolution": builder_resolution,
        "portfolio_xray_resolution": xray_resolution,
        "stress_report_resolution": stress_resolution,
    }


__all__ = [
    "PORTFOLIO_XRAY_BLOCK_2_1_KEY",
    "PORTFOLIO_XRAY_BLOCK_2_2_KEY",
    "PORTFOLIO_XRAY_BLOCK_2_3_KEY",
    "PORTFOLIO_XRAY_BLOCK_2_4_KEY",
    "PORTFOLIO_XRAY_BLOCK_2_5_KEY",
    "PORTFOLIO_XRAY_BLOCK_2_6_KEY",
    "ADVANCED_EVIDENCE_MANIFEST_KEYS",
    "ARTIFACT_CATEGORY_ORDER",
    "DiagnosisResolution",
    "GENERATED_EXPORT_MANIFEST_SUFFIXES",
    "LEGACY_COMPATIBILITY_MANIFEST_KEYS",
    "ORCHESTRATION_MANIFEST_KEYS",
    "PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS",
    "PRODUCT_BUNDLE_MANIFEST_KEYS",
    "PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS",
    "SUBJECT_DIAGNOSTICS_MANIFEST_KEYS",
    "TECHNICAL_COMPARISON_MANIFEST_KEYS",
    "build_generated_paths_by_category",
    "build_output_manifest_discovery_extra",
    "build_product_discovery_block",
    "build_product_first_generated_paths",
    "discover_paths_by_category",
    "discover_product_bundle_paths",
    "load_diagnosis_bundle_docs",
    "manifest_key_category",
    "product_bundle_artifact_categories",
    "portfolio_xray_has_block_2_1",
    "portfolio_xray_has_block_2_2",
    "portfolio_xray_has_block_2_3",
    "portfolio_xray_has_block_2_4",
    "portfolio_xray_has_block_2_5",
    "portfolio_xray_has_block_2_6",
    "product_bundle_generated_paths_for_manifest",
    "product_bundle_manifest_extra",
    "resolve_candidate_launchpad_path",
    "resolve_portfolio_alternatives_builder_path",
    "subject_diagnostics_manifest_note",
    "resolve_problem_classification_path",
]
