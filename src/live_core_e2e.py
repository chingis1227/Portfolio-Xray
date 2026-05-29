"""Live core E2E acceptance checks for portfolio-first Blocks 1-3 (Phase 17 RM-1021).

Validator profiles align with [runtime_artifact_contract.md](../docs/runtime_artifact_contract.md)
and Blocks 1-3 post-audit Session 05 (R5): auto-detect profile from on-disk artifacts instead of
assuming a single ``core_fast`` comparison menu.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from scripts.core_mvp_validation_contract import (
    check_block_2_4_hidden_exposure,
    check_block_4_diagnosis_handoff,
    check_block_5_compare_handoff,
    check_candidate_launchpad_v1,
    check_current_portfolio_stress_scorecard_v1,
    check_current_vs_candidate_v1,
    check_decision_verdict_v1,
    check_hedge_gap_analysis_v1,
    check_problem_classification_v1,
)
from src.candidate_comparison import product_candidate_ids_from_factory_run
from src.portfolio_xray import XRAY_SECTION_KEYS
from src.product_bundle_hygiene import (
    NO_CANDIDATE_TOMBSTONE,
    WORKFLOW_STATE_DIAGNOSIS_ONLY,
)
from src.product_bundle_paths import (
    portfolio_xray_has_block_2_1,
    portfolio_xray_has_block_2_2,
    portfolio_xray_has_block_2_3,
    portfolio_xray_has_block_2_4,
    portfolio_xray_has_block_2_5,
    portfolio_xray_has_block_2_6,
)
from src.problem_classification import PROBLEM_CLASSIFICATION_FILENAME
from src.candidate_launchpad import CANDIDATE_LAUNCHPAD_FILENAME
from src.ai_commentary_context import AI_COMMENTARY_CONTEXT_FILENAME

LiveCoreE2EProfile = Literal[
    "core_blocks_1_3",
    "diagnosis_only",
    "product_one_candidate",
    "research_batch_core_fast",
]

LIVE_CORE_E2E_PROFILE_CORE_BLOCKS_1_3: LiveCoreE2EProfile = "core_blocks_1_3"
LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY: LiveCoreE2EProfile = "diagnosis_only"
LIVE_CORE_E2E_PROFILE_PRODUCT_ONE_CANDIDATE: LiveCoreE2EProfile = "product_one_candidate"
LIVE_CORE_E2E_PROFILE_RESEARCH_BATCH_CORE_FAST: LiveCoreE2EProfile = (
    "research_batch_core_fast"
)

LIVE_CORE_E2E_PROFILE_VALUES: frozenset[str] = frozenset(
    {
        LIVE_CORE_E2E_PROFILE_CORE_BLOCKS_1_3,
        LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY,
        LIVE_CORE_E2E_PROFILE_PRODUCT_ONE_CANDIDATE,
        LIVE_CORE_E2E_PROFILE_RESEARCH_BATCH_CORE_FAST,
    }
)

# Legacy RM-1021 gate constants (research batch with core_fast factory).
LIVE_CORE_REVIEW_MODE = "core"
LIVE_CORE_FACTORY_PROFILE = "core_fast"

_SUBJECT_REQUIRED_FILES = (
    "run_metadata.json",
    "portfolio_xray.json",
    "stress_report.json",
)

_SUBJECT_DIAGNOSIS_BUNDLE_FILES = (
    PROBLEM_CLASSIFICATION_FILENAME,
    CANDIDATE_LAUNCHPAD_FILENAME,
    AI_COMMENTARY_CONTEXT_FILENAME,
)

_STRESS_REQUIRED_KEYS = (
    "stress_results_v1",
    "hedge_gap_analysis_v1",
    "current_portfolio_stress_scorecard_v1",
    "stress_scorecard_v1",
    "stress_conclusions",
    "historical_methodology",
    "hedge_gap_analysis",
)

_ROOT_POST_COMPARE_FILES = (
    "candidate_comparison.json",
    "current_vs_candidate.json",
    "decision_verdict.json",
    "candidate_factory_run.json",
)


@dataclass
class LiveCoreE2EValidation:
    """Result of validating live core artifacts under ``output_dir_final``."""

    output_dir: Path
    ok: bool
    profile: LiveCoreE2EProfile | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def messages(self) -> list[str]:
        lines = [f"output_dir={self.output_dir}", f"ok={self.ok}"]
        if self.profile is not None:
            lines.append(f"profile={self.profile}")
        for err in self.errors:
            lines.append(f"ERROR: {err}")
        for warn in self.warnings:
            lines.append(f"WARNING: {warn}")
        for key, value in sorted(self.evidence.items()):
            lines.append(f"  {key}: {value}")
        return lines


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"Expected JSON object at {path}")
    return data


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return _load_json(path)


def _is_no_candidate_tombstone(doc: dict[str, Any] | None) -> bool:
    if not isinstance(doc, dict):
        return False
    return doc.get("tombstone") == NO_CANDIDATE_TOMBSTONE


def detect_live_core_e2e_profile(output_dir: Path) -> LiveCoreE2EProfile:
    """
    Infer the runtime artifact profile from on-disk layout.

    Order: explicit-list factory → core_fast/core_v1 factory → diagnosis tombstones →
    core Blocks 1–3 absence of Block 4+ subject files → diagnosis bundle without factory.
    """
    out = output_dir.resolve()
    subject = out / "analysis_subject"
    factory_run = _load_json_if_exists(out / "candidate_factory_run.json")
    comparison = _load_json_if_exists(out / "candidate_comparison.json")
    profile_id = str((factory_run or {}).get("factory_profile_id") or "").strip()

    if profile_id == "explicit_list":
        return LIVE_CORE_E2E_PROFILE_PRODUCT_ONE_CANDIDATE
    if profile_id in ("core_fast", "core_v1"):
        return LIVE_CORE_E2E_PROFILE_RESEARCH_BATCH_CORE_FAST

    if _is_no_candidate_tombstone(comparison):
        return LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY

    has_diagnosis_bundle = any((subject / name).is_file() for name in _SUBJECT_DIAGNOSIS_BUNDLE_FILES)
    has_block4_subject = (subject / PROBLEM_CLASSIFICATION_FILENAME).is_file()
    has_root_compare = comparison is not None

    if not has_block4_subject and not has_root_compare and not factory_run:
        return LIVE_CORE_E2E_PROFILE_CORE_BLOCKS_1_3

    if has_diagnosis_bundle and not factory_run:
        return LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY

    if has_root_compare and not factory_run:
        return LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY

    return LIVE_CORE_E2E_PROFILE_RESEARCH_BATCH_CORE_FAST


def _validate_subject_blocks(
    result: LiveCoreE2EValidation,
    subject_dir: Path,
) -> dict[str, Any] | None:
    """Validate Blocks 1–3 subject JSON; return run_metadata when present."""
    for name in _SUBJECT_REQUIRED_FILES:
        path = subject_dir / name
        if not path.is_file():
            result.errors.append(f"missing subject artifact: {path}")
            result.ok = False

    if not result.ok:
        return None

    run_metadata = _load_json(subject_dir / "run_metadata.json")
    if "analysis_setup" not in run_metadata:
        result.errors.append("run_metadata.json missing analysis_setup")
        result.ok = False
    if "input_assumptions" not in run_metadata:
        result.errors.append("run_metadata.json missing input_assumptions")
        result.ok = False

    xray = _load_json(subject_dir / "portfolio_xray.json")
    sections = xray.get("sections")
    if not isinstance(sections, dict):
        result.errors.append("portfolio_xray.json missing sections object")
        result.ok = False
    else:
        missing_sections = [k for k in XRAY_SECTION_KEYS if k not in sections]
        if missing_sections:
            result.errors.append(
                f"portfolio_xray.json missing sections: {', '.join(missing_sections)}"
            )
            result.ok = False
    if not portfolio_xray_has_block_2_1(xray):
        result.errors.append(
            "portfolio_xray.json missing block_2_1_asset_allocation product contract"
        )
        result.ok = False
    else:
        block = xray["block_2_1_asset_allocation"]
        total = (block.get("portfolio_composition_snapshot") or {}).get("total_holdings")
        result.evidence["block_2_1_total_holdings"] = total
    if not portfolio_xray_has_block_2_2(xray):
        result.errors.append(
            "portfolio_xray.json missing block_2_2_portfolio_metrics product contract"
        )
        result.ok = False
    else:
        block_22 = xray["block_2_2_portfolio_metrics"]
        meta_22 = block_22.get("metadata") or {}
        result.evidence["block_2_2_primary_window_months"] = meta_22.get(
            "primary_window_months"
        )
    if not portfolio_xray_has_block_2_3(xray):
        result.errors.append(
            "portfolio_xray.json missing block_2_3_factor_exposure product contract"
        )
        result.ok = False
    else:
        block_23 = xray["block_2_3_factor_exposure"]
        result.evidence["block_2_3_status"] = block_23.get("status")
    if not portfolio_xray_has_block_2_4(xray):
        result.errors.append(
            "portfolio_xray.json missing block_2_4_hidden_exposure product contract"
        )
        result.ok = False
    else:
        block_24 = xray["block_2_4_hidden_exposure"]
        result.evidence["block_2_4_status"] = block_24.get("status")
        block_24_checks = check_block_2_4_hidden_exposure(block_24)
        result.evidence["block_2_4_ruleset"] = block_24_checks.get("ruleset")
        result.evidence["block_2_4_confidence_model"] = block_24_checks.get(
            "confidence_model"
        )
        result.evidence["block_2_4_alert_count"] = block_24_checks.get("alert_count")
        if not block_24_checks.get("institutional_v2_surface_ok"):
            violations = block_24_checks.get("contract_violations") or []
            preview = "; ".join(str(row) for row in violations[:3])
            suffix = "..." if len(violations) > 3 else ""
            result.errors.append(
                "block_2_4_hidden_exposure institutional v2 contract violated: "
                f"{preview}{suffix}"
            )
            result.ok = False
        elif not block_24_checks.get("stress_boundary_ok"):
            result.errors.append(
                "block_2_4_hidden_exposure stress boundary check failed "
                "(does_not_run_stress_lab or forbidden embedded stress keys)"
            )
            result.ok = False
    if not portfolio_xray_has_block_2_5(xray):
        result.errors.append(
            "portfolio_xray.json missing block_2_5_risk_budget_view product contract"
        )
        result.ok = False
    else:
        block_25 = xray["block_2_5_risk_budget_view"]
        result.evidence["block_2_5_status"] = block_25.get("status")
        top1 = block_25.get("top1_rc_asset") or {}
        result.evidence["block_2_5_top1_ticker"] = top1.get("ticker")

    if not portfolio_xray_has_block_2_6(xray):
        result.errors.append(
            "portfolio_xray.json missing block_2_6_portfolio_weakness_map product contract"
        )
        result.ok = False
    else:
        block_26 = xray["block_2_6_portfolio_weakness_map"]
        result.evidence["block_2_6_status"] = block_26.get("status")
        risks = block_26.get("risk_types")
        if isinstance(risks, list):
            result.evidence["block_2_6_risk_type_count"] = len(risks)

    stress = _load_json(subject_dir / "stress_report.json")
    for key in _STRESS_REQUIRED_KEYS:
        if key not in stress:
            result.errors.append(f"stress_report.json missing {key}")
            result.ok = False

    hedge_gap = stress.get("hedge_gap_analysis_v1")
    hedge_gap_checks = check_hedge_gap_analysis_v1(
        hedge_gap if isinstance(hedge_gap, dict) else None
    )
    result.evidence["hedge_gap_block_status"] = hedge_gap_checks.get("block_status")
    result.evidence["hedge_gap_ruleset_version"] = hedge_gap_checks.get("ruleset_version")
    result.evidence["hedge_gap_protection_profile"] = hedge_gap_checks.get(
        "protection_profile"
    )
    result.evidence["hedge_gap_n_weak_protection_rows"] = hedge_gap_checks.get(
        "n_weak_protection_rows"
    )
    bridges = hedge_gap_checks.get("bridges_applied")
    if isinstance(bridges, dict):
        result.evidence["hedge_gap_bridge_2_4"] = bridges.get("block_2_4_hidden_exposure")
        result.evidence["hedge_gap_bridge_2_6"] = bridges.get("block_2_6_portfolio_weakness_map")
    if not hedge_gap_checks.get("product_contract_ok"):
        violations = hedge_gap_checks.get("contract_violations") or []
        preview = "; ".join(str(row) for row in violations[:3])
        suffix = "..." if len(violations) > 3 else ""
        result.errors.append(
            "hedge_gap_analysis_v1 institutional product contract violated: "
            f"{preview}{suffix}"
        )
        result.ok = False

    scorecard = stress.get("current_portfolio_stress_scorecard_v1")
    scorecard_checks = check_current_portfolio_stress_scorecard_v1(
        scorecard if isinstance(scorecard, dict) else None
    )
    result.evidence["block_3_4_block_status"] = scorecard_checks.get("block_status")
    result.evidence["block_3_4_ruleset_version"] = scorecard_checks.get("ruleset_version")
    result.evidence["block_3_4_diagnosis_confidence"] = scorecard_checks.get(
        "diagnosis_confidence"
    )
    result.evidence["block_3_4_legacy_fallback_used"] = scorecard_checks.get(
        "legacy_fallback_used"
    )
    result.evidence["block_3_4_headline_present"] = scorecard_checks.get("headline_present")
    result.evidence["block_3_4_main_hedge_gap_scenario_id"] = scorecard_checks.get(
        "main_hedge_gap_scenario_id"
    )
    result.evidence["block_3_4_next_decision_uses_count"] = scorecard_checks.get(
        "next_decision_uses_count"
    )
    if not scorecard_checks.get("product_contract_ok"):
        violations = scorecard_checks.get("contract_violations") or []
        preview = "; ".join(str(row) for row in violations[:3])
        suffix = "..." if len(violations) > 3 else ""
        result.errors.append(
            "current_portfolio_stress_scorecard_v1 institutional product contract violated: "
            f"{preview}{suffix}"
        )
        result.ok = False

    subject_type = (
        (run_metadata.get("input_assumptions") or {})
        .get("analysis_subject", {})
        .get("type")
    )
    result.evidence["analysis_subject_type"] = subject_type
    result.evidence["analysis_end"] = run_metadata.get("analysis_end") or (
        (run_metadata.get("analysis_setup") or {}).get("analysis_end")
    )
    return run_metadata


def _validate_core_blocks_subject_and_root(
    result: LiveCoreE2EValidation,
    subject_dir: Path,
    out: Path,
) -> None:
    for name in _SUBJECT_DIAGNOSIS_BUNDLE_FILES:
        path = subject_dir / name
        if path.is_file():
            result.errors.append(
                f"core_blocks_1_3 must not retain Block 4+ subject file: {path.name}"
            )
            result.ok = False
    for name in _ROOT_POST_COMPARE_FILES:
        path = out / name
        if path.is_file():
            result.errors.append(
                f"core_blocks_1_3 must not retain root post-compare file: {name}"
            )
            result.ok = False
    registry = out / "candidate_comparison_registry.json"
    if registry.is_file():
        result.errors.append(
            "core_blocks_1_3 must not retain candidate_comparison_registry.json"
        )
        result.ok = False


def _validate_block_4_subject_bundle(
    result: LiveCoreE2EValidation,
    subject_dir: Path,
) -> None:
    """Validate Problem Classification + Candidate Launchpad product contracts (Block 4 entry)."""
    pc_path = subject_dir / PROBLEM_CLASSIFICATION_FILENAME
    lp_path = subject_dir / CANDIDATE_LAUNCHPAD_FILENAME
    pc = _load_json_if_exists(pc_path)
    lp = _load_json_if_exists(lp_path)
    if pc is None or lp is None:
        return

    pc_checks = check_problem_classification_v1(pc)
    result.evidence["block_4_n_problems"] = pc_checks.get("n_problems")
    result.evidence["block_4_primary_problem_id"] = pc_checks.get("primary_problem_id")
    result.evidence["block_4_hedge_gap_source"] = pc_checks.get("hedge_gap_source")
    result.evidence["block_4_stress_scorecard_source"] = pc_checks.get("stress_scorecard_source")
    if not pc_checks.get("product_contract_ok"):
        violations = pc_checks.get("contract_violations") or []
        preview = "; ".join(str(row) for row in violations[:3])
        suffix = "..." if len(violations) > 3 else ""
        result.errors.append(
            "problem_classification_v1 product contract violated: " f"{preview}{suffix}"
        )
        result.ok = False

    lp_checks = check_candidate_launchpad_v1(lp)
    result.evidence["block_4_n_cards"] = lp_checks.get("n_cards")
    result.evidence["block_4_primary_card_id"] = lp_checks.get("primary_card_id")
    if not lp_checks.get("product_contract_ok"):
        violations = lp_checks.get("contract_violations") or []
        preview = "; ".join(str(row) for row in violations[:3])
        suffix = "..." if len(violations) > 3 else ""
        result.errors.append(
            "candidate_launchpad_v1 product contract violated: " f"{preview}{suffix}"
        )
        result.ok = False

    handoff = check_block_4_diagnosis_handoff(pc, lp)
    if not handoff.get("handoff_ok"):
        violations = handoff.get("contract_violations") or []
        preview = "; ".join(str(row) for row in violations[:3])
        suffix = "..." if len(violations) > 3 else ""
        result.errors.append(f"block_4 diagnosis handoff violated: {preview}{suffix}")
        result.ok = False


def _validate_diagnosis_only_subject_and_root(
    result: LiveCoreE2EValidation,
    subject_dir: Path,
    out: Path,
) -> None:
    for name in (PROBLEM_CLASSIFICATION_FILENAME, CANDIDATE_LAUNCHPAD_FILENAME):
        path = subject_dir / name
        if not path.is_file():
            result.errors.append(f"diagnosis_only missing subject artifact: {path.name}")
            result.ok = False

    if result.ok:
        _validate_block_4_subject_bundle(result, subject_dir)

    factory_path = out / "candidate_factory_run.json"
    if factory_path.is_file():
        result.errors.append("diagnosis_only must not retain candidate_factory_run.json")
        result.ok = False

    comparison_path = out / "candidate_comparison.json"
    comparison = _load_json_if_exists(comparison_path)
    if comparison is None:
        result.errors.append(f"diagnosis_only missing tombstone: {comparison_path.name}")
        result.ok = False
    elif not _is_no_candidate_tombstone(comparison):
        result.errors.append(
            "candidate_comparison.json must carry no_candidate_v1 tombstone on diagnosis_only"
        )
        result.ok = False
    else:
        candidates = comparison.get("candidates")
        if isinstance(candidates, list) and candidates:
            result.errors.append(
                "diagnosis_only candidate_comparison.json must have empty candidates list"
            )
            result.ok = False

    current_vs = _load_json_if_exists(out / "current_vs_candidate.json")
    if not _is_no_candidate_tombstone(current_vs):
        result.errors.append(
            "current_vs_candidate.json must carry no_candidate_v1 tombstone on diagnosis_only"
        )
        result.ok = False
    elif isinstance(current_vs, dict):
        selected = current_vs.get("selected_candidate_ids")
        if isinstance(selected, list) and selected:
            result.errors.append(
                "diagnosis_only current_vs_candidate must have empty selected_candidate_ids"
            )
            result.ok = False

    verdict = _load_json_if_exists(out / "decision_verdict.json")
    if not _is_no_candidate_tombstone(verdict):
        result.errors.append(
            "decision_verdict.json must carry no_candidate_v1 tombstone on diagnosis_only"
        )
        result.ok = False
    elif isinstance(verdict, dict) and verdict.get("selected_candidate_id") is not None:
        result.errors.append(
            "diagnosis_only decision_verdict must not set selected_candidate_id"
        )
        result.ok = False

    registry = out / "candidate_comparison_registry.json"
    if registry.is_file():
        result.errors.append(
            "diagnosis_only must not retain candidate_comparison_registry.json"
        )
        result.ok = False

    result.evidence["workflow_state"] = WORKFLOW_STATE_DIAGNOSIS_ONLY


def _validate_product_one_candidate_root(
    result: LiveCoreE2EValidation,
    out: Path,
) -> None:
    factory_path = out / "candidate_factory_run.json"
    comparison_path = out / "candidate_comparison.json"
    if not factory_path.is_file():
        result.errors.append(f"missing candidate_factory_run.json: {factory_path}")
        result.ok = False
        return
    if not comparison_path.is_file():
        result.errors.append(f"missing candidate_comparison.json: {comparison_path}")
        result.ok = False
        return

    factory_run = _load_json(factory_path)
    profile = str(factory_run.get("factory_profile_id") or "")
    result.evidence["factory_profile_id"] = profile
    if profile != "explicit_list":
        result.errors.append(
            f"product_one_candidate factory_profile_id expected 'explicit_list', got {profile!r}"
        )
        result.ok = False

    comparison = _load_json(comparison_path)
    if _is_no_candidate_tombstone(comparison):
        result.errors.append(
            "product_one_candidate candidate_comparison.json must not be a tombstone"
        )
        result.ok = False

    product_ids = tuple(
        str(cid)
        for cid in (
            (comparison.get("product_candidate_scope") or {}).get("candidate_ids") or []
        )
        if str(cid).strip()
    )
    factory_ids = product_candidate_ids_from_factory_run(factory_run)
    result.evidence["product_candidate_ids"] = list(product_ids)
    result.evidence["factory_step_candidate_ids"] = list(factory_ids)

    if not product_ids:
        result.errors.append(
            "product_one_candidate missing product_candidate_scope.candidate_ids"
        )
        result.ok = False
    elif factory_ids and set(product_ids) != set(factory_ids):
        result.errors.append(
            "product_candidate_scope.candidate_ids must match explicit_list factory steps"
        )
        result.ok = False

    candidates = comparison.get("candidates")
    if not isinstance(candidates, list):
        candidates = comparison.get("rows") if isinstance(comparison.get("rows"), list) else []
    result.evidence["comparison_candidate_count"] = len(candidates)

    if product_ids:
        baseline_id = str(
            comparison.get("comparison_baseline_candidate_id") or "analysis_subject"
        )
        allowed = {baseline_id, "analysis_subject", "current", *product_ids}
        row_ids = {
            str(row.get("candidate_id"))
            for row in candidates
            if isinstance(row, dict) and row.get("candidate_id")
        }
        extra = row_ids - allowed
        if extra:
            result.errors.append(
                "product_one_candidate comparison rows include ids outside product scope: "
                f"{sorted(extra)}"
            )
            result.ok = False
        max_rows = len(product_ids) + 2
        if len(candidates) > max_rows:
            result.errors.append(
                f"product_one_candidate comparison has too many rows ({len(candidates)}); "
                f"expected at most baseline plus {len(product_ids)} selected id(s)"
            )
            result.ok = False

    scope = comparison.get("product_candidate_scope") or {}
    if scope.get("excludes_unselected_candidates") is not True:
        result.warnings.append(
            "product_candidate_scope.excludes_unselected_candidates is not true"
        )

    current_vs = _load_json_if_exists(out / "current_vs_candidate.json")
    if current_vs is None:
        result.errors.append("product_one_candidate missing current_vs_candidate.json")
        result.ok = False
    elif _is_no_candidate_tombstone(current_vs):
        result.errors.append(
            "product_one_candidate current_vs_candidate.json must not be a tombstone"
        )
        result.ok = False
    else:
        selected = current_vs.get("selected_candidate_ids")
        if not isinstance(selected, list) or not selected:
            result.errors.append(
                "product_one_candidate current_vs_candidate must list selected_candidate_ids"
            )
            result.ok = False
        elif product_ids and any(str(sid) not in product_ids for sid in selected):
            result.errors.append(
                "current_vs_candidate selected ids must be within product_candidate_scope"
            )
            result.ok = False

    verdict = _load_json_if_exists(out / "decision_verdict.json")
    if verdict is None:
        result.errors.append("product_one_candidate missing decision_verdict.json")
        result.ok = False
    elif _is_no_candidate_tombstone(verdict):
        result.errors.append(
            "product_one_candidate decision_verdict.json must not be a tombstone"
        )
        result.ok = False
    else:
        selected_id = verdict.get("selected_candidate_id")
        result.evidence["decision_selected_candidate_id"] = selected_id
        if product_ids and selected_id is not None and str(selected_id) not in product_ids:
            result.errors.append(
                "decision_verdict selected_candidate_id must be within product scope"
            )
            result.ok = False

    menu = comparison.get("candidate_menu")
    if isinstance(menu, dict):
        result.evidence["review_mode"] = menu.get("review_mode")
        result.evidence["factory_evidence_status"] = menu.get("factory_evidence_status")

    if result.ok and current_vs is not None and verdict is not None:
        _validate_block_5_compare_root_bundle(
            result,
            comparison=comparison,
            current_vs_candidate=current_vs,
            decision_verdict=verdict,
            selection=_load_json_if_exists(out / "selection_decision.json"),
        )


def _validate_block_5_compare_root_bundle(
    result: LiveCoreE2EValidation,
    *,
    comparison: dict[str, Any],
    current_vs_candidate: dict[str, Any],
    decision_verdict: dict[str, Any],
    selection: dict[str, Any] | None,
) -> None:
    """Validate Current vs Candidate + Decision Verdict product contracts (Block 5)."""
    cvc_checks = check_current_vs_candidate_v1(current_vs_candidate)
    result.evidence["block_5_view_mode"] = cvc_checks.get("view_mode")
    result.evidence["block_5_n_comparisons"] = cvc_checks.get("n_comparisons")
    if not cvc_checks.get("product_contract_ok"):
        violations = cvc_checks.get("contract_violations") or []
        preview = "; ".join(str(row) for row in violations[:3])
        suffix = "..." if len(violations) > 3 else ""
        result.errors.append(
            "current_vs_candidate_v1 product contract violated: " f"{preview}{suffix}"
        )
        result.ok = False

    verdict_checks = check_decision_verdict_v1(decision_verdict)
    result.evidence["block_5_verdict_id"] = verdict_checks.get("verdict_id")
    result.evidence["block_5_verdict_family"] = verdict_checks.get("verdict_family")
    result.evidence["block_5_selection_status"] = verdict_checks.get("selection_decision_status")
    if not verdict_checks.get("product_contract_ok"):
        violations = verdict_checks.get("contract_violations") or []
        preview = "; ".join(str(row) for row in violations[:3])
        suffix = "..." if len(violations) > 3 else ""
        result.errors.append(
            "decision_verdict_v1 product contract violated: " f"{preview}{suffix}"
        )
        result.ok = False

    handoff = check_block_5_compare_handoff(
        comparison,
        current_vs_candidate,
        decision_verdict,
        selection=selection,
    )
    if not handoff.get("handoff_ok"):
        violations = handoff.get("contract_violations") or []
        preview = "; ".join(str(row) for row in violations[:3])
        suffix = "..." if len(violations) > 3 else ""
        result.errors.append(f"block_5 compare handoff violated: {preview}{suffix}")
        result.ok = False


def _validate_research_batch_core_fast_root(
    result: LiveCoreE2EValidation,
    out: Path,
    *,
    require_factory_run: bool,
) -> None:
    comparison_path = out / "candidate_comparison.json"
    if not comparison_path.is_file():
        result.errors.append(f"missing candidate_comparison.json: {comparison_path}")
        result.ok = False
        return

    comparison = _load_json(comparison_path)
    if _is_no_candidate_tombstone(comparison):
        result.errors.append(
            "research_batch_core_fast candidate_comparison.json must not be a tombstone"
        )
        result.ok = False

    menu = comparison.get("candidate_menu")
    if not isinstance(menu, dict):
        result.errors.append("candidate_comparison.json missing candidate_menu object")
        result.ok = False
        return

    review_mode = menu.get("review_mode")
    result.evidence["review_mode"] = review_mode
    if review_mode != LIVE_CORE_REVIEW_MODE:
        result.errors.append(
            f"candidate_menu.review_mode expected {LIVE_CORE_REVIEW_MODE!r}, got {review_mode!r}"
        )
        result.ok = False

    factory_status = menu.get("factory_evidence_status")
    result.evidence["factory_evidence_status"] = factory_status
    if factory_status not in ("current", "stale", "missing", "not_authoritative"):
        result.warnings.append(
            f"unexpected factory_evidence_status: {factory_status!r}"
        )
    elif factory_status != "current":
        result.warnings.append(
            f"factory_evidence_status is not current ({factory_status!r}); "
            "re-run factory with --then-compare or refresh comparison after factory"
        )

    result.evidence["comparison_generated_at"] = comparison.get("generated_at")
    candidates = comparison.get("candidates")
    if not isinstance(candidates, list):
        candidates = (
            comparison.get("rows") if isinstance(comparison.get("rows"), list) else []
        )
    result.evidence["comparison_candidate_count"] = len(candidates)
    result.evidence["comparison_baseline_id"] = comparison.get(
        "comparison_baseline_candidate_id"
    )

    scope = comparison.get("product_candidate_scope") or {}
    if scope.get("excludes_unselected_candidates"):
        result.warnings.append(
            "research_batch_core_fast comparison is product-scoped; "
            "expected full registry in candidate_comparison.json"
        )

    if require_factory_run:
        factory_path = out / "candidate_factory_run.json"
        if not factory_path.is_file():
            result.errors.append(f"missing candidate_factory_run.json: {factory_path}")
            result.ok = False
        else:
            factory_run = _load_json(factory_path)
            profile = factory_run.get("factory_profile_id")
            result.evidence["factory_profile_id"] = profile
            if profile != LIVE_CORE_FACTORY_PROFILE:
                result.errors.append(
                    f"factory_profile_id expected {LIVE_CORE_FACTORY_PROFILE!r}, got {profile!r}"
                )
                result.ok = False
            result.evidence["factory_generated_at"] = factory_run.get("generated_at")


def validate_live_core_artifacts(
    output_dir: Path,
    *,
    profile: LiveCoreE2EProfile | str | None = None,
    require_factory_run: bool | None = None,
) -> LiveCoreE2EValidation:
    """
    Validate live portfolio-first artifacts for Blocks 1–3 and runtime contract roots.

    When ``profile`` is omitted, :func:`detect_live_core_e2e_profile` selects the check
    set from on-disk layout (core-only, diagnosis-only tombstones, explicit-list compare,
    or legacy ``core_fast`` research batch).
    """
    out = output_dir.resolve()
    resolved_profile: LiveCoreE2EProfile
    if profile is None:
        resolved_profile = detect_live_core_e2e_profile(out)
    else:
        normalized = str(profile).strip()
        if normalized not in LIVE_CORE_E2E_PROFILE_VALUES:
            raise ValueError(
                f"Unknown live core E2E profile {profile!r}; "
                f"expected one of: {', '.join(sorted(LIVE_CORE_E2E_PROFILE_VALUES))}"
            )
        resolved_profile = normalized  # type: ignore[assignment]

    result = LiveCoreE2EValidation(
        output_dir=out,
        ok=True,
        profile=resolved_profile,
    )
    result.evidence["detected_profile"] = resolved_profile

    subject_dir = out / "analysis_subject"
    if not subject_dir.is_dir():
        result.errors.append(f"missing analysis_subject directory: {subject_dir}")
        result.ok = False
        return result

    _validate_subject_blocks(result, subject_dir)
    if not result.ok:
        return result

    if resolved_profile == LIVE_CORE_E2E_PROFILE_CORE_BLOCKS_1_3:
        _validate_core_blocks_subject_and_root(result, subject_dir, out)
    elif resolved_profile == LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY:
        _validate_diagnosis_only_subject_and_root(result, subject_dir, out)
    elif resolved_profile == LIVE_CORE_E2E_PROFILE_PRODUCT_ONE_CANDIDATE:
        _validate_product_one_candidate_root(result, out)
        if result.ok:
            _validate_block_4_subject_bundle(result, subject_dir)
    elif resolved_profile == LIVE_CORE_E2E_PROFILE_RESEARCH_BATCH_CORE_FAST:
        need_factory = (
            require_factory_run
            if require_factory_run is not None
            else True
        )
        _validate_research_batch_core_fast_root(
            result, out, require_factory_run=need_factory
        )

    return result


__all__ = [
    "LIVE_CORE_E2E_PROFILE_CORE_BLOCKS_1_3",
    "LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY",
    "LIVE_CORE_E2E_PROFILE_PRODUCT_ONE_CANDIDATE",
    "LIVE_CORE_E2E_PROFILE_RESEARCH_BATCH_CORE_FAST",
    "LIVE_CORE_E2E_PROFILE_VALUES",
    "LIVE_CORE_FACTORY_PROFILE",
    "LIVE_CORE_REVIEW_MODE",
    "LiveCoreE2EProfile",
    "LiveCoreE2EValidation",
    "detect_live_core_e2e_profile",
    "validate_live_core_artifacts",
]
