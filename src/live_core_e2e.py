"""Live core E2E acceptance checks for portfolio-first Blocks 1-6 (Phase 17 RM-1021)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.portfolio_xray import XRAY_SECTION_KEYS
from src.product_bundle_paths import (
    portfolio_xray_has_block_2_1,
    portfolio_xray_has_block_2_2,
    portfolio_xray_has_block_2_3,
    portfolio_xray_has_block_2_4,
    portfolio_xray_has_block_2_5,
    portfolio_xray_has_block_2_6,
)

LIVE_CORE_REVIEW_MODE = "core"
LIVE_CORE_FACTORY_PROFILE = "core_fast"

_SUBJECT_REQUIRED_FILES = (
    "run_metadata.json",
    "portfolio_xray.json",
    "stress_report.json",
)

_STRESS_REQUIRED_KEYS = (
    "stress_results_v1",
    "stress_scorecard_v1",
    "stress_conclusions",
    "historical_methodology",
    "hedge_gap_analysis",
)


@dataclass
class LiveCoreE2EValidation:
    """Result of validating live core artifacts under ``output_dir_final``."""

    output_dir: Path
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def messages(self) -> list[str]:
        lines = [f"output_dir={self.output_dir}", f"ok={self.ok}"]
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


def validate_live_core_artifacts(
    output_dir: Path,
    *,
    require_factory_run: bool = True,
) -> LiveCoreE2EValidation:
    """
    Validate that a completed live ``run_portfolio_review.py --mode core`` run left
    subject diagnosis and comparison artifacts on disk.

    Does not download market data; callers run the orchestrator separately or pass
    ``scripts/verify_live_core_e2e.py --run``.
    """
    out = output_dir.resolve()
    result = LiveCoreE2EValidation(output_dir=out, ok=True)

    subject_dir = out / "analysis_subject"
    if not subject_dir.is_dir():
        result.errors.append(f"missing analysis_subject directory: {subject_dir}")
        result.ok = False
        return result

    for name in _SUBJECT_REQUIRED_FILES:
        path = subject_dir / name
        if not path.is_file():
            result.errors.append(f"missing subject artifact: {path}")
            result.ok = False

    if not result.ok:
        return result

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

    comparison_path = out / "candidate_comparison.json"
    if not comparison_path.is_file():
        result.errors.append(f"missing candidate_comparison.json: {comparison_path}")
        result.ok = False
        return result

    comparison = _load_json(comparison_path)
    menu = comparison.get("candidate_menu")
    if not isinstance(menu, dict):
        result.errors.append("candidate_comparison.json missing candidate_menu object")
        result.ok = False
        return result

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
        candidates = comparison.get("rows") if isinstance(comparison.get("rows"), list) else []
    result.evidence["comparison_candidate_count"] = len(candidates)
    result.evidence["comparison_baseline_id"] = comparison.get("comparison_baseline_candidate_id")

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

    subject_type = (
        (run_metadata.get("input_assumptions") or {})
        .get("analysis_subject", {})
        .get("type")
    )
    result.evidence["analysis_subject_type"] = subject_type
    result.evidence["analysis_end"] = run_metadata.get("analysis_end") or (
        (run_metadata.get("analysis_setup") or {}).get("analysis_end")
    )

    return result
