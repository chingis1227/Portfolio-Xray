"""
Candidate Portfolio Factory orchestration.

See docs/specs/candidate_factory_spec.md.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.candidate_comparison import _REGISTRY_ROWS, candidate_registry_ids
from src.config_schema import PortfolioConfig
from src.candidate_robust_disclosure import (
    ROBUST_MV_CANDIDATE_IDS,
    ROBUST_SCENARIO_PREREQUISITES,
    build_robust_scenario_prerequisites_disclosure,
    merge_robust_paths_into_step,
)
from src.optimization_status import (
    optimizer_quality_from_solver_block,
    optimization_quality_family,
)
from src.snapshot import (
    CANDIDATE_CONFIG_FINGERPRINT_KEY,
    compute_candidate_config_fingerprint,
    snapshot_config_fingerprint,
)
from src.text_sanitizer import ascii_safe_text
from src.candidate_manifest import (
    compute_factory_run_status,
    write_candidate_manifest,
)
from src.candidate_run_context import CandidateRunContext, prepare_candidate_run_context
from src.candidate_weights import (
    CANDIDATE_WEIGHTS_BUILD_FILENAME,
    build_candidate_weights,
    candidate_weights_success,
    uses_lightweight_report_phase,
    uses_weights_only_phase,
    weights_build_freshness,
    write_candidate_weights,
    normalize_execution_mode,
)
from src.report_profile import REPORT_PROFILE_FULL, REPORT_PROFILE_LIGHTWEIGHT
from src.variant_builder_runtime import (
    ENV_SKIP_VARIANT_PDF,
    BuilderStepTiming,
    build_timing_summary,
    load_builder_runtime_timing,
    maybe_rebuild_pdfs_after_variant,
    merge_timing_into_step,
    normalize_pdf_mode,
    persist_builder_runtime_timing,
    subprocess_env_for_pdf_mode,
)

SCHEMA_VERSION = "candidate_factory_run_v1"
MANIFEST_SCHEMA_VERSION = "candidate_factory_manifest_v1"
MANIFEST_FILENAME = "candidate_factory_manifest.json"
RESUME_COMPLETE_STATUSES = frozenset({"succeeded", "skipped_existing"})
SNAPSHOT_MINIMUM = "snapshot_10y.json"
FULL_REPORT_SKIP_MARKER = "report.html"
DEFAULT_LIGHTWEIGHT_REPORT_WORKERS = 4
POLICY_EXCLUDED_IDS = frozenset({"policy", "current"})
SCRIPTS_WITH_CONFIG = frozenset(
    {
        "run_robust_scenario_optimization.py",
        "run_robust_mean_variance_constrained.py",
        "run_robust_mean_variance_uncapped.py",
    }
)

FACTORY_PROFILES: dict[str, list[str]] = {
    "core_benchmarks": ["equal_weight", "risk_parity", "equal_weight_by_asset_class"],
    "risk_budgets": [
        "risk_budget_by_asset",
        "risk_budget_by_asset_class",
        "hierarchical_risk_parity",
    ],
    "classic_optimizers": [
        "minimum_variance",
        "minimum_variance_uncapped",
        "minimum_variance_advanced",
        "maximum_diversification",
        "maximum_diversification_uncapped",
        "minimum_cvar_constrained",
        "minimum_cvar_uncapped",
    ],
    "robust_suite": ["robust_mv_constrained", "robust_mv_uncapped", "robust_scenario"],
}

DEFAULT_V1_CANDIDATE_ORDER: list[str] = (
    FACTORY_PROFILES["core_benchmarks"]
    + FACTORY_PROFILES["risk_budgets"]
    + FACTORY_PROFILES["classic_optimizers"]
    + FACTORY_PROFILES["robust_suite"]
)

# Lightweight portfolio-first review menu (benchmarks + risk budgets only).
CORE_V1_CANDIDATE_ORDER: list[str] = (
    FACTORY_PROFILES["core_benchmarks"] + FACTORY_PROFILES["risk_budgets"]
)

PRODUCT_MENU_PROFILE_ID = "default_v1"
REVIEW_MODE_PROFILES: dict[str, str] = {
    "core": "core_v1",
    "full": "default_v1",
}

CANDIDATE_ENTRY_SCRIPTS: dict[str, list[str]] = {
    "equal_weight": ["run_equal_weight.py"],
    "equal_weight_by_asset_class": ["run_equal_weight_by_asset_class.py"],
    "hierarchical_risk_parity": ["run_hierarchical_risk_parity.py"],
    "maximum_diversification": ["run_maximum_diversification.py"],
    "maximum_diversification_uncapped": ["run_maximum_diversification_unconstrained.py"],
    "minimum_cvar_constrained": ["run_minimum_cvar_constrained.py"],
    "minimum_cvar_uncapped": ["run_minimum_cvar_uncapped.py"],
    "minimum_variance": ["run_minimum_variance.py"],
    "minimum_variance_advanced": ["run_minimum_variance_advanced.py"],
    "minimum_variance_uncapped": ["run_minimum_variance_uncapped.py"],
    "risk_budget_by_asset": ["run_risk_budget_by_asset.py"],
    "risk_budget_by_asset_class": ["run_risk_budget_by_asset_class.py"],
    "risk_parity": ["run_risk_parity.py"],
    "robust_mv_constrained": ["run_robust_mean_variance_constrained.py"],
    "robust_mv_uncapped": ["run_robust_mean_variance_uncapped.py"],
    "robust_scenario": [
        "run_robust_scenario_optimization.py",
        "run_robust_scenario_portfolio_report.py",
    ],
}

BUILDER_SUMMARY_FILENAME = "summary.json"

# Maps builder summary.json `status` (FAIL_*) to factory step reason_code (Session 02 / G1).
_BUILDER_STATUS_TO_REASON: dict[str, str] = {
    "FAIL_CONFIG": "builder_fail_config",
    "FAIL_DATA": "builder_fail_data",
    "FAIL_INFEASIBLE_UNIVERSE": "builder_infeasible_universe",
    "FAIL_INFEASIBLE_TARGETS": "builder_infeasible_targets",
    "FAIL_INFEASIBLE_BOUNDS": "builder_infeasible_bounds",
    "FAIL_INFEASIBLE_VOL_TARGET": "builder_infeasible_vol_target",
    "FAIL_NUMERICAL": "builder_fail_numerical",
    "FAIL_NO_ASSETS": "builder_fail_no_assets",
}


def resolve_full_report_candidate_ids(
    candidate_ids: list[str],
    *,
    full_candidate_reports: bool,
    selected: list[str] | None,
) -> list[str]:
    """
    Phase 3 targets: explicit ``selected`` list, or all ``candidate_ids`` when
    ``full_candidate_reports`` is True. Empty when neither is requested.
    """
    if selected:
        unknown = [cid for cid in selected if cid not in candidate_ids]
        if unknown:
            raise FactoryValidationError(
                "Unknown candidate id(s) for full report export: "
                + ", ".join(unknown)
            )
        return list(selected)
    if full_candidate_reports:
        return list(candidate_ids)
    return []


def registry_row(candidate_id: str) -> dict[str, str] | None:
    for row in _REGISTRY_ROWS:
        if row["candidate_id"] == candidate_id:
            return row
    return None


def resolve_profile_candidate_ids(
    *,
    profile_id: str,
    explicit_candidates: list[str] | None,
) -> list[str]:
    if explicit_candidates is not None:
        return list(explicit_candidates)
    if profile_id == "default_v1":
        return list(DEFAULT_V1_CANDIDATE_ORDER)
    if profile_id == "core_v1":
        return list(CORE_V1_CANDIDATE_ORDER)
    if profile_id == "explicit_list":
        return []
    profile = FACTORY_PROFILES.get(profile_id)
    if profile is None:
        raise FactoryValidationError(f"Unknown factory profile: {profile_id}")
    return list(profile)


def validate_candidate_ids(candidate_ids: list[str]) -> list[str]:
    """Return unknown ids; empty list means all known script-backed ids."""
    known = set(candidate_registry_ids()) - POLICY_EXCLUDED_IDS
    return [cid for cid in candidate_ids if cid not in known]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _analysis_end_from_artifact_dir(path: Path) -> str | None:
    for name in ("snapshot_10y.json", "snapshot_5y.json", "snapshot_3y.json"):
        snap = _load_json(path / name)
        if snap and snap.get("analysis_end"):
            return str(snap["analysis_end"])
    meta = _load_json(path / "run_metadata.json")
    run_info = meta.get("run_info") if isinstance(meta, dict) else None
    if isinstance(run_info, dict):
        end = run_info.get("analysis_end_date")
        if end:
            return str(end)
    return None


def _resolve_analysis_end(project_root: Path, output_dir_final: str) -> str | None:
    final_dir = project_root / output_dir_final
    subject_end = _analysis_end_from_artifact_dir(final_dir / "analysis_subject")
    if subject_end:
        return subject_end
    return _analysis_end_from_artifact_dir(final_dir)


def _snapshot_analysis_end(snapshot_path: Path) -> str | None:
    snap = _load_json(snapshot_path)
    if not snap:
        return None
    end = snap.get("analysis_end")
    return str(end) if end else None


def _snapshot_freshness(
    snapshot_path: Path,
    *,
    expected_analysis_end: str | None,
    expected_config_fingerprint: str | None,
) -> tuple[str, str | None, str | None]:
    if not snapshot_path.is_file():
        return "missing", None, None
    snap = _load_json(snapshot_path)
    snapshot_end = _snapshot_analysis_end(snapshot_path)
    snapshot_fp = snapshot_config_fingerprint(snap)
    if not expected_analysis_end:
        return "unchecked", snapshot_end, snapshot_fp
    if snapshot_end != expected_analysis_end:
        return "stale", snapshot_end, snapshot_fp
    if expected_config_fingerprint and snapshot_fp != expected_config_fingerprint:
        return "stale_config", snapshot_end, snapshot_fp
    return "fresh", snapshot_end, snapshot_fp


def _robust_scenario_prerequisites_met(project_root: Path, output_dir_final: str) -> bool:
    final_dir = project_root / output_dir_final
    return all((final_dir / name).is_file() for name in ROBUST_SCENARIO_PREREQUISITES)


def _command_strings(commands: list[list[str]]) -> list[str]:
    return [" ".join(cmd) for cmd in commands]


def _read_builder_summary(artifact_dir: Path) -> dict[str, Any] | None:
    summary = _load_json(artifact_dir / BUILDER_SUMMARY_FILENAME)
    return summary if summary else None


def _optimizer_status_evidence(artifact_dir: Path) -> dict[str, Any]:
    """Read optimizer/fallback quality evidence from builder artifacts."""
    baseline = _load_json(artifact_dir / "baseline_weights_metadata.json")
    if baseline:
        metadata = baseline.get("optimizer_run_metadata")
        if isinstance(metadata, dict):
            solver = metadata.get("solver")
            if isinstance(solver, dict):
                quality = optimizer_quality_from_solver_block(solver)
                fallback_used = bool(solver.get("fallback_used", False))
                return {
                    "optimization_status_source": "baseline_weights_metadata.json.optimizer_run_metadata",
                    "optimization_quality_status": quality,
                    "optimization_quality_family": optimization_quality_family(
                        quality,
                        fallback_used=fallback_used,
                    ),
                    "optimizer_fallback_used": fallback_used,
                    "optimizer_fallback_reason": solver.get("fallback_reason"),
                    "optimizer_solver_status": solver.get("status")
                    or solver.get("solver_status"),
                }

    summary = _read_builder_summary(artifact_dir)
    if summary:
        solver_block = summary.get("solver")
        if isinstance(solver_block, dict):
            quality = optimizer_quality_from_solver_block(solver_block)
            fallback_used = bool(solver_block.get("fallback_used", False))
            return {
                "optimization_status_source": "summary.json.solver",
                "optimization_quality_status": quality,
                "optimization_quality_family": optimization_quality_family(
                    quality,
                    fallback_used=fallback_used,
                ),
                "optimizer_fallback_used": fallback_used,
                "optimizer_fallback_reason": solver_block.get("fallback_reason"),
                "optimizer_solver_status": solver_block.get("status")
                or solver_block.get("solver_status"),
            }
        if summary.get("solver_status") or summary.get("fallback_used") is not None:
            solver = {
                "solver_status": summary.get("solver_status"),
                "solver_success": summary.get("solver_success"),
                "fallback_used": summary.get("fallback_used", False),
                "fallback_reason": summary.get("fallback_reason"),
                "optimization_quality_status": summary.get("optimization_quality_status"),
            }
            quality = optimizer_quality_from_solver_block(solver)
            fallback_used = bool(solver.get("fallback_used", False))
            return {
                "optimization_status_source": "summary.json",
                "optimization_quality_status": quality,
                "optimization_quality_family": optimization_quality_family(
                    quality,
                    fallback_used=fallback_used,
                ),
                "optimizer_fallback_used": fallback_used,
                "optimizer_fallback_reason": solver.get("fallback_reason"),
                "optimizer_solver_status": solver.get("solver_status"),
            }
    return {}


def factory_reason_from_builder_summary(
    summary: dict[str, Any],
) -> tuple[str, str, str, str | None] | None:
    """
    Map builder summary.json FAIL_* status to factory reason_code.

    Returns (reason_code, message, builder_status, builder_reason) or None when
    summary does not describe a builder failure.
    """
    status = summary.get("status")
    if not isinstance(status, str) or not status.startswith("FAIL_"):
        return None
    reason_code = _BUILDER_STATUS_TO_REASON.get(status, "builder_failed")
    reason_text = summary.get("reason")
    builder_reason = str(reason_text) if reason_text else None
    message = f"Builder reported {status}."
    if builder_reason:
        message = f"{message} Reason: {builder_reason}"
    return reason_code, message, status, builder_reason


def _post_build_failure_details(
    artifact_dir: Path,
    *,
    exit_code: int,
    stderr_tail: str | None,
) -> tuple[str, str, str | None, str | None]:
    """Resolve factory reason after a build attempt (subprocess and/or missing snapshot)."""
    summary = _read_builder_summary(artifact_dir)
    if summary:
        mapped = factory_reason_from_builder_summary(summary)
        if mapped:
            return mapped
    if exit_code != 0:
        message = "Builder subprocess returned non-zero exit."
        if stderr_tail:
            message = f"{message} stderr tail: {stderr_tail}"
        return "subprocess_failed", message, None, None
    return (
        "missing_snapshot_after_build",
        f"{SNAPSHOT_MINIMUM} missing after successful builder exit.",
        None,
        None,
    )


def _build_subprocess_commands(
    scripts: list[str],
    *,
    python_exe: str,
    project_root: Path,
    config_path: Path | None,
) -> list[list[str]]:
    commands: list[list[str]] = []
    for script in scripts:
        script_path = project_root / script
        cmd = [python_exe, str(script_path)]
        if config_path is not None and script in SCRIPTS_WITH_CONFIG:
            cmd.extend(["--config", str(config_path)])
        commands.append(cmd)
    return commands


def _run_subprocess_chain(
    commands: list[list[str]],
    *,
    project_root: Path,
    runner: Any | None = None,
    subprocess_env: dict[str, str] | None = None,
) -> tuple[int, str | None]:
    stderr_parts: list[str] = []
    last_code = 0
    for cmd in commands:
        if runner is not None:
            try:
                code = int(
                    runner(cmd, cwd=str(project_root), env=subprocess_env)
                )
            except TypeError:
                code = int(runner(cmd, cwd=str(project_root)))
        else:
            proc = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                env=subprocess_env,
            )
            code = proc.returncode
            if proc.stderr:
                stderr_parts.append(proc.stderr)
        if code != 0:
            tail = "\n".join(stderr_parts)[-2000:] if stderr_parts else None
            return code, tail
    tail = "\n".join(stderr_parts)[-2000:] if stderr_parts else None
    return 0, tail


def _execute_weights_only_build(
    *,
    candidate_id: str,
    row: dict[str, str],
    artifact_dir: Path,
    artifact_root: str,
    entry_commands: list[str],
    context: CandidateRunContext,
    analysis_end: str | None,
    config_fingerprint: str,
    steps: list[dict[str, Any]],
    summary: dict[str, int],
    manifest: dict[str, Any],
    manifest_dir: Path,
    project_root: Path,
    output_dir_final: str,
    fail_fast: bool,
    record_factory_step: bool = True,
) -> bool:
    """
    Phase 1 weights build in-process. Returns False if factory loop should stop (fail-fast).

    When ``record_factory_step`` is False (standard mode before Phase 2 report), the caller
    records a single combined factory step after the report phase.
    """
    timing = BuilderStepTiming()
    timing.start_core()
    result = build_candidate_weights(context, candidate_id)
    timing.end_core()
    write_out = write_candidate_weights(
        context,
        candidate_id,
        result,
        artifact_dir=artifact_dir,
        config_fingerprint=config_fingerprint,
    )
    persist_builder_runtime_timing(artifact_dir, timing)
    duration = timing.total_seconds
    builder_timing = load_builder_runtime_timing(artifact_dir)
    weights_freshness, weights_end, weights_fp = weights_build_freshness(
        artifact_dir,
        expected_analysis_end=analysis_end,
        expected_config_fingerprint=config_fingerprint,
    )

    if not write_out.get("success") and not candidate_weights_success(result, candidate_id):
        mapped = factory_reason_from_builder_summary(
            {"status": result.status, "reason": result.diagnostics.get("reason")}
        )
        if mapped:
            reason_code, message, builder_status, builder_reason = mapped
        else:
            reason_code = "builder_failed"
            message = f"Weight build status {result.status}."
            builder_status = result.status
            builder_reason = str(result.diagnostics.get("reason") or "")
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code=reason_code,
            message=message,
            entry_commands=entry_commands,
            exit_code=0,
            duration_seconds=duration,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status=weights_freshness,
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=weights_fp,
            builder_status=builder_status,
            builder_reason=builder_reason,
        )
        step["execution_action"] = "weights_built_failed"
        step["phases_completed"] = ["weights"]
        merge_timing_into_step(step, builder_timing)
        if record_factory_step:
            _append_factory_step(
                steps,
                step,
                candidate_id=candidate_id,
                project_root=project_root,
                output_dir_final=output_dir_final,
            )
            _increment_summary(summary, "failed")
            _persist_manifest_step(
                manifest,
                output_dir=manifest_dir,
                candidate_id=candidate_id,
                step=step,
                project_root=project_root,
            )
        return not fail_fast

    step = {
        "candidate_id": candidate_id,
        "display_name": row["display_name"],
        "role": row["role"],
        "artifact_root": artifact_root,
        "status": "succeeded",
        "execution_action": "weights_built",
        "entry_commands": entry_commands,
        "exit_code": 0,
        "duration_seconds": duration,
        "reason_code": None,
        "message": None,
        "expected_analysis_end": analysis_end,
        "snapshot_analysis_end": weights_end,
        "freshness_status": weights_freshness,
        "expected_config_fingerprint": config_fingerprint,
        "snapshot_config_fingerprint": weights_fp,
        "phases_completed": ["weights"],
        "builder_status": result.status,
    }
    merge_timing_into_step(step, builder_timing)
    if record_factory_step:
        _append_factory_step(
            steps,
            step,
            candidate_id=candidate_id,
            project_root=project_root,
            output_dir_final=output_dir_final,
        )
        _increment_summary(summary, "succeeded")
        _persist_manifest_step(
            manifest,
            output_dir=manifest_dir,
            candidate_id=candidate_id,
            step=step,
            project_root=project_root,
        )
    return True


def _mark_weights_build_report_phase(artifact_dir: Path) -> None:
    path = artifact_dir / CANDIDATE_WEIGHTS_BUILD_FILENAME
    if not path.is_file():
        return
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(manifest, dict):
        return
    phases = list(manifest.get("phases_completed") or [])
    for label in ("weights", "report"):
        if label not in phases:
            phases.append(label)
    manifest["phases_completed"] = phases
    manifest["report_profile"] = REPORT_PROFILE_LIGHTWEIGHT
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _run_lightweight_report_worker(
    *,
    cfg: PortfolioConfig,
    candidate_id: str,
    row: dict[str, str],
    artifact_dir: Path,
    artifact_root: str,
    entry_commands: list[str],
    analysis_end: str | None,
    config_fingerprint: str,
    weights_reused: bool,
    run_context: CandidateRunContext | None = None,
) -> dict[str, Any]:
    """
    Phase 2: comparison-ready snapshots via ``lightweight_comparison`` report profile.

    This worker is intentionally candidate-local: it may write files under
    ``artifact_dir`` only and returns one factory step for the coordinator to
    register. It must not mutate run-level ``steps`` / ``summary`` / manifests.
    """
    from run_report import run_portfolio_report_for_weights

    weights_path = artifact_dir / "weights.json"
    if not weights_path.is_file():
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code="builder_failed",
            message="weights.json missing before lightweight report phase.",
            entry_commands=entry_commands,
            exit_code=None,
            duration_seconds=0.0,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status="missing",
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=None,
        )
        step["execution_action"] = "lightweight_report_failed"
        step["phases_completed"] = ["weights"] if weights_reused else ["weights"]
        return step

    try:
        weights = json.loads(weights_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code="builder_failed",
            message=f"Could not read weights.json: {exc}",
            entry_commands=entry_commands,
            exit_code=None,
            duration_seconds=0.0,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status="missing",
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=None,
        )
        step["execution_action"] = "lightweight_report_failed"
        return step

    if not isinstance(weights, dict) or not weights:
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code="builder_failed",
            message="weights.json is empty or not an object.",
            entry_commands=entry_commands,
            exit_code=None,
            duration_seconds=0.0,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status="missing",
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=None,
        )
        step["execution_action"] = "lightweight_report_failed"
        return step

    timing = BuilderStepTiming()
    prior_timing = load_builder_runtime_timing(artifact_dir)
    if prior_timing:
        timing.builder_core_seconds = float(prior_timing.get("builder_core_seconds") or 0.0)

    output_dir_csv = artifact_dir / "results_csv"
    output_dir_csv.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.now(timezone.utc).isoformat()
    timing.start_report()
    try:
        pm_summary, meta = run_portfolio_report_for_weights(
            cfg,
            weights,
            run_timestamp=run_timestamp,
            output_dir_csv=output_dir_csv,
            output_dir_final=artifact_dir,
            backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
            no_cache=run_context.no_cache if run_context else False,
            weights_source=f"candidate_factory.{candidate_id}",
            report_profile=REPORT_PROFILE_LIGHTWEIGHT,
            run_context=run_context,
        )
    except Exception as exc:
        timing.end_report()
        persist_builder_runtime_timing(artifact_dir, timing)
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code="builder_failed",
            message=f"Lightweight report failed: {exc}",
            entry_commands=entry_commands,
            exit_code=None,
            duration_seconds=timing.total_seconds,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status="missing",
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=None,
        )
        step["execution_action"] = "lightweight_report_failed"
        step["phases_completed"] = ["weights", "report"]
        merge_timing_into_step(step, timing.to_dict())
        return step

    timing.end_report()
    persist_builder_runtime_timing(artifact_dir, timing)
    snapshot_path = artifact_dir / SNAPSHOT_MINIMUM
    if not snapshot_path.is_file():
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code="builder_failed",
            message=f"{SNAPSHOT_MINIMUM} missing after lightweight report.",
            entry_commands=entry_commands,
            exit_code=None,
            duration_seconds=timing.total_seconds,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status="missing",
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=None,
        )
        step["execution_action"] = "lightweight_report_failed"
        step["phases_completed"] = ["weights", "report"]
        merge_timing_into_step(step, timing.to_dict())
        return step

    stress_report = meta.get("stress_report") or {}
    summary_payload: dict[str, Any] = {
        "portfolio_type": row.get("display_name") or candidate_id,
        "status": "OK",
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason"),
        "portfolio_valid": meta.get("portfolio_valid"),
        "report_profile": REPORT_PROFILE_LIGHTWEIGHT,
    }
    with open(artifact_dir / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary_payload, handle, indent=2, ensure_ascii=False)

    _mark_weights_build_report_phase(artifact_dir)
    freshness, snapshot_end, snapshot_fp = _snapshot_freshness(
        snapshot_path,
        expected_analysis_end=analysis_end,
        expected_config_fingerprint=config_fingerprint,
    )
    duration = timing.total_seconds
    execution_action = (
        "lightweight_report_reused_weights" if weights_reused else "lightweight_report_built"
    )
    step = {
        "candidate_id": candidate_id,
        "display_name": row["display_name"],
        "role": row["role"],
        "artifact_root": artifact_root,
        "status": "succeeded",
        "execution_action": execution_action,
        "entry_commands": entry_commands,
        "exit_code": 0,
        "duration_seconds": duration,
        "reason_code": None,
        "message": None,
        "expected_analysis_end": analysis_end,
        "snapshot_analysis_end": snapshot_end,
        "freshness_status": freshness,
        "expected_config_fingerprint": config_fingerprint,
        "snapshot_config_fingerprint": snapshot_fp,
        "phases_completed": ["weights", "report"],
        "report_profile": REPORT_PROFILE_LIGHTWEIGHT,
    }
    merge_timing_into_step(step, timing.to_dict())
    return step


def _record_lightweight_report_step(
    *,
    step: dict[str, Any],
    candidate_id: str,
    steps: list[dict[str, Any]],
    summary: dict[str, int],
    manifest: dict[str, Any],
    manifest_dir: Path,
    project_root: Path,
    output_dir_final: str,
) -> None:
    """Coordinator-owned registration for a lightweight report worker result."""
    _append_factory_step(
        steps,
        step,
        candidate_id=candidate_id,
        project_root=project_root,
        output_dir_final=output_dir_final,
    )
    _increment_summary(summary, str(step.get("status") or "failed"))
    _persist_manifest_step(
        manifest,
        output_dir=manifest_dir,
        candidate_id=candidate_id,
        step=step,
        project_root=project_root,
    )


def _execute_lightweight_report(
    *,
    cfg: PortfolioConfig,
    candidate_id: str,
    row: dict[str, str],
    artifact_dir: Path,
    artifact_root: str,
    entry_commands: list[str],
    analysis_end: str | None,
    config_fingerprint: str,
    steps: list[dict[str, Any]],
    summary: dict[str, int],
    manifest: dict[str, Any],
    manifest_dir: Path,
    project_root: Path,
    output_dir_final: str,
    fail_fast: bool,
    weights_reused: bool,
    run_context: CandidateRunContext | None = None,
) -> bool:
    """
    Sequential Phase 2 coordinator.

    The report work is isolated in ``_run_lightweight_report_worker`` so Session 2
    can run those workers concurrently while this coordinator remains the only
    writer of run-level factory state.
    """
    step = _run_lightweight_report_worker(
        cfg=cfg,
        candidate_id=candidate_id,
        row=row,
        artifact_dir=artifact_dir,
        artifact_root=artifact_root,
        entry_commands=entry_commands,
        analysis_end=analysis_end,
        config_fingerprint=config_fingerprint,
        weights_reused=weights_reused,
        run_context=run_context,
    )
    _record_lightweight_report_step(
        step=step,
        candidate_id=candidate_id,
        steps=steps,
        summary=summary,
        manifest=manifest,
        manifest_dir=manifest_dir,
        project_root=project_root,
        output_dir_final=output_dir_final,
    )
    if step.get("status") == "failed":
        return not fail_fast
    return True


def _lightweight_report_worker_crash_step(
    *,
    candidate_id: str,
    row: dict[str, str],
    artifact_root: str,
    entry_commands: list[str],
    analysis_end: str | None,
    config_fingerprint: str,
    exc: BaseException,
) -> dict[str, Any]:
    step = _failed_step(
        candidate_id=candidate_id,
        display_name=row["display_name"],
        role=row["role"],
        artifact_root=artifact_root,
        status="failed",
        reason_code="builder_failed",
        message=f"Lightweight report worker crashed: {exc}",
        entry_commands=entry_commands,
        exit_code=None,
        duration_seconds=0.0,
        expected_analysis_end=analysis_end,
        snapshot_analysis_end=None,
        freshness_status="missing",
        expected_config_fingerprint=config_fingerprint,
        snapshot_config_fingerprint=None,
    )
    step["execution_action"] = "lightweight_report_failed"
    step["phases_completed"] = ["weights", "report"]
    step["report_profile"] = REPORT_PROFILE_LIGHTWEIGHT
    return step


def _register_parallel_lightweight_report_results(
    pending_reports: list[dict[str, Any]],
    *,
    steps: list[dict[str, Any]],
    summary: dict[str, int],
    manifest: dict[str, Any],
    manifest_dir: Path,
    project_root: Path,
    output_dir_final: str,
) -> None:
    """Register parallel lightweight report results in candidate menu order."""
    for pending in pending_reports:
        future = pending["future"]
        try:
            step = future.result()
        except Exception as exc:  # noqa: BLE001 - convert worker crash to factory evidence
            step = _lightweight_report_worker_crash_step(
                candidate_id=pending["candidate_id"],
                row=pending["row"],
                artifact_root=pending["artifact_root"],
                entry_commands=pending["entry_commands"],
                analysis_end=pending["analysis_end"],
                config_fingerprint=pending["config_fingerprint"],
                exc=exc,
            )
        _record_lightweight_report_step(
            step=step,
            candidate_id=pending["candidate_id"],
            steps=steps,
            summary=summary,
            manifest=manifest,
            manifest_dir=manifest_dir,
            project_root=project_root,
            output_dir_final=output_dir_final,
        )
    pending_reports.clear()


def _lightweight_report_worker_count(
    requested_workers: int | None,
    *,
    candidate_count: int,
) -> int:
    if requested_workers is not None:
        return max(1, int(requested_workers))
    return max(1, min(DEFAULT_LIGHTWEIGHT_REPORT_WORKERS, candidate_count))


def _parallel_lightweight_reports_effective(
    *,
    requested: bool,
    execution_mode: str,
    fail_fast: bool,
    pdf_mode: str,
    full_report_ids: list[str],
) -> bool:
    return (
        requested
        and execution_mode == "standard"
        and not fail_fast
        and pdf_mode != "per_candidate"
        and not full_report_ids
    )


def _parallel_lightweight_report_fallback_reasons(
    *,
    requested: bool,
    execution_mode: str,
    fail_fast: bool,
    pdf_mode: str,
    full_report_ids: list[str],
) -> list[str]:
    if not requested:
        return []
    reasons: list[str] = []
    if execution_mode != "standard":
        reasons.append(f"execution_mode={execution_mode}")
    if fail_fast:
        reasons.append("fail_fast")
    if pdf_mode == "per_candidate":
        reasons.append("pdf_mode=per_candidate")
    if full_report_ids:
        reasons.append("full_candidate_reports")
    return reasons


def _parallel_lightweight_report_summary(
    *,
    requested: bool,
    effective: bool,
    workers: int,
    submitted_candidate_ids: list[str],
    registered_candidate_ids: list[str],
    wall_clock_seconds: float | None,
    fallback_reasons: list[str],
) -> dict[str, Any] | None:
    if not requested and not effective:
        return None
    if effective:
        status = "parallel" if submitted_candidate_ids else "parallel_no_work"
    else:
        status = "sequential_fallback"
    summary: dict[str, Any] = {
        "requested": requested,
        "effective": effective,
        "status": status,
        "workers": workers,
        "submitted_count": len(submitted_candidate_ids),
        "completed_count": len(registered_candidate_ids),
        "submitted_candidate_ids": submitted_candidate_ids,
        "registered_candidate_ids": registered_candidate_ids,
        "fallback_reasons": fallback_reasons,
    }
    if wall_clock_seconds is not None:
        summary["wall_clock_seconds"] = round(float(wall_clock_seconds), 3)
    return summary


def _mark_full_report_phase(artifact_dir: Path) -> None:
    path = artifact_dir / CANDIDATE_WEIGHTS_BUILD_FILENAME
    if not path.is_file():
        return
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(manifest, dict):
        return
    phases = list(manifest.get("phases_completed") or [])
    for label in ("weights", "report", "full_report"):
        if label not in phases:
            phases.append(label)
    manifest["phases_completed"] = phases
    manifest["report_profile"] = REPORT_PROFILE_FULL
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _rebuild_variant_pdfs_without_skip_env(
    *,
    timing: BuilderStepTiming | None = None,
) -> None:
    """Run variant PDF rebuild even when factory subprocesses set PORTFOLIO_SKIP_VARIANT_PDF."""
    prior = os.environ.get(ENV_SKIP_VARIANT_PDF)
    os.environ.pop(ENV_SKIP_VARIANT_PDF, None)
    try:
        maybe_rebuild_pdfs_after_variant(timing=timing)
    finally:
        if prior is not None:
            os.environ[ENV_SKIP_VARIANT_PDF] = prior


def _execute_full_report(
    *,
    cfg: PortfolioConfig,
    candidate_id: str,
    row: dict[str, str],
    artifact_dir: Path,
    artifact_root: str,
    entry_commands: list[str],
    analysis_end: str | None,
    config_fingerprint: str,
    steps: list[dict[str, Any]],
    summary: dict[str, int],
    manifest: dict[str, Any],
    manifest_dir: Path,
    project_root: Path,
    output_dir_final: str,
    fail_fast: bool,
    pdf_mode: str,
    run_context: CandidateRunContext | None = None,
) -> bool:
    """
    Phase 3: full ``report_profile`` (HTML, commentary, rolling betas, etc.) for one candidate.
    """
    from run_report import run_portfolio_report_for_weights

    weights_path = artifact_dir / "weights.json"
    if not weights_path.is_file():
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code="builder_failed",
            message="weights.json missing before full report export.",
            entry_commands=entry_commands,
            exit_code=None,
            duration_seconds=0.0,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status="missing",
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=None,
        )
        step["execution_action"] = "full_report_failed"
        step["phases_completed"] = ["full_report"]
        step["report_profile"] = REPORT_PROFILE_FULL
        _append_factory_step(
            steps,
            step,
            candidate_id=candidate_id,
            project_root=project_root,
            output_dir_final=output_dir_final,
        )
        _increment_summary(summary, "failed")
        _persist_manifest_step(
            manifest,
            output_dir=manifest_dir,
            candidate_id=candidate_id,
            step=step,
            project_root=project_root,
        )
        return not fail_fast

    try:
        weights = json.loads(weights_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code="builder_failed",
            message=f"Could not read weights.json: {exc}",
            entry_commands=entry_commands,
            exit_code=None,
            duration_seconds=0.0,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status="missing",
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=None,
        )
        step["execution_action"] = "full_report_failed"
        step["report_profile"] = REPORT_PROFILE_FULL
        _append_factory_step(
            steps,
            step,
            candidate_id=candidate_id,
            project_root=project_root,
            output_dir_final=output_dir_final,
        )
        _increment_summary(summary, "failed")
        _persist_manifest_step(
            manifest,
            output_dir=manifest_dir,
            candidate_id=candidate_id,
            step=step,
            project_root=project_root,
        )
        return not fail_fast

    if not isinstance(weights, dict) or not weights:
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code="builder_failed",
            message="weights.json is empty or not an object.",
            entry_commands=entry_commands,
            exit_code=None,
            duration_seconds=0.0,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status="missing",
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=None,
        )
        step["execution_action"] = "full_report_failed"
        step["report_profile"] = REPORT_PROFILE_FULL
        _append_factory_step(
            steps,
            step,
            candidate_id=candidate_id,
            project_root=project_root,
            output_dir_final=output_dir_final,
        )
        _increment_summary(summary, "failed")
        _persist_manifest_step(
            manifest,
            output_dir=manifest_dir,
            candidate_id=candidate_id,
            step=step,
            project_root=project_root,
        )
        return not fail_fast

    timing = BuilderStepTiming()
    prior_timing = load_builder_runtime_timing(artifact_dir)
    if prior_timing:
        timing.builder_core_seconds = float(prior_timing.get("builder_core_seconds") or 0.0)
        timing.report_seconds = float(prior_timing.get("report_seconds") or 0.0)

    output_dir_csv = artifact_dir / "results_csv"
    output_dir_csv.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.now(timezone.utc).isoformat()
    timing.start_report()
    try:
        pm_summary, meta = run_portfolio_report_for_weights(
            cfg,
            weights,
            run_timestamp=run_timestamp,
            output_dir_csv=output_dir_csv,
            output_dir_final=artifact_dir,
            backtest_mode_override=getattr(cfg, "backtest_mode", "dynamic_nan_safe"),
            no_cache=run_context.no_cache if run_context else False,
            weights_source=f"candidate_factory.{candidate_id}.full_report",
            report_profile=REPORT_PROFILE_FULL,
            run_context=run_context,
        )
    except Exception as exc:
        timing.end_report()
        persist_builder_runtime_timing(artifact_dir, timing)
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code="builder_failed",
            message=f"Full report export failed: {exc}",
            entry_commands=entry_commands,
            exit_code=None,
            duration_seconds=timing.total_seconds,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status="missing",
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=None,
        )
        step["execution_action"] = "full_report_failed"
        step["phases_completed"] = ["full_report"]
        step["report_profile"] = REPORT_PROFILE_FULL
        merge_timing_into_step(step, timing.to_dict())
        _append_factory_step(
            steps,
            step,
            candidate_id=candidate_id,
            project_root=project_root,
            output_dir_final=output_dir_final,
        )
        _increment_summary(summary, "failed")
        _persist_manifest_step(
            manifest,
            output_dir=manifest_dir,
            candidate_id=candidate_id,
            step=step,
            project_root=project_root,
        )
        return not fail_fast

    timing.end_report()
    if normalize_pdf_mode(pdf_mode) == "per_candidate":
        _rebuild_variant_pdfs_without_skip_env(timing=timing)

    persist_builder_runtime_timing(artifact_dir, timing)
    snapshot_path = artifact_dir / SNAPSHOT_MINIMUM
    if not snapshot_path.is_file():
        step = _failed_step(
            candidate_id=candidate_id,
            display_name=row["display_name"],
            role=row["role"],
            artifact_root=artifact_root,
            status="failed",
            reason_code="builder_failed",
            message=f"{SNAPSHOT_MINIMUM} missing after full report export.",
            entry_commands=entry_commands,
            exit_code=None,
            duration_seconds=timing.total_seconds,
            expected_analysis_end=analysis_end,
            snapshot_analysis_end=None,
            freshness_status="missing",
            expected_config_fingerprint=config_fingerprint,
            snapshot_config_fingerprint=None,
        )
        step["execution_action"] = "full_report_failed"
        step["phases_completed"] = ["full_report"]
        step["report_profile"] = REPORT_PROFILE_FULL
        merge_timing_into_step(step, timing.to_dict())
        _append_factory_step(
            steps,
            step,
            candidate_id=candidate_id,
            project_root=project_root,
            output_dir_final=output_dir_final,
        )
        _increment_summary(summary, "failed")
        _persist_manifest_step(
            manifest,
            output_dir=manifest_dir,
            candidate_id=candidate_id,
            step=step,
            project_root=project_root,
        )
        return not fail_fast

    stress_report = meta.get("stress_report") or {}
    summary_payload: dict[str, Any] = {
        "portfolio_type": row.get("display_name") or candidate_id,
        "status": "OK",
        "metrics_10y": pm_summary,
        "stress_status": stress_report.get("status"),
        "stress_fail_reason": stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason"),
        "portfolio_valid": meta.get("portfolio_valid"),
        "report_profile": REPORT_PROFILE_FULL,
    }
    with open(artifact_dir / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary_payload, handle, indent=2, ensure_ascii=False)

    _mark_full_report_phase(artifact_dir)
    freshness, snapshot_end, snapshot_fp = _snapshot_freshness(
        snapshot_path,
        expected_analysis_end=analysis_end,
        expected_config_fingerprint=config_fingerprint,
    )
    duration = timing.total_seconds
    step = {
        "candidate_id": candidate_id,
        "display_name": row["display_name"],
        "role": row["role"],
        "artifact_root": artifact_root,
        "status": "succeeded",
        "execution_action": "full_report_built",
        "entry_commands": entry_commands,
        "exit_code": 0,
        "duration_seconds": duration,
        "reason_code": None,
        "message": None,
        "expected_analysis_end": analysis_end,
        "snapshot_analysis_end": snapshot_end,
        "freshness_status": freshness,
        "expected_config_fingerprint": config_fingerprint,
        "snapshot_config_fingerprint": snapshot_fp,
        "phases_completed": ["weights", "report", "full_report"],
        "report_profile": REPORT_PROFILE_FULL,
    }
    merge_timing_into_step(step, timing.to_dict())
    _append_factory_step(
        steps,
        step,
        candidate_id=candidate_id,
        project_root=project_root,
        output_dir_final=output_dir_final,
    )
    _increment_summary(summary, "succeeded")
    _persist_manifest_step(
        manifest,
        output_dir=manifest_dir,
        candidate_id=candidate_id,
        step=step,
        project_root=project_root,
    )
    return True


def _run_full_candidate_reports_phase(
    *,
    cfg: PortfolioConfig,
    full_report_ids: list[str],
    steps: list[dict[str, Any]],
    summary: dict[str, int],
    manifest: dict[str, Any],
    manifest_dir: Path,
    project_root: Path,
    output_dir_final: str,
    analysis_end: str | None,
    config_fingerprint: str,
    skip_existing: bool,
    force: bool,
    fail_fast: bool,
    pdf_mode: str,
    run_context: CandidateRunContext | None,
) -> bool:
    """
    Phase 3 loop. Returns False when fail-fast should mark the run aborted after this phase.
    """
    if not full_report_ids:
        return True

    fail_fast_aborted = False
    for candidate_id in full_report_ids:
        row = registry_row(candidate_id)
        if row is None:
            continue
        artifact_root = row["artifact_root"]
        artifact_dir = project_root / artifact_root
        scripts = CANDIDATE_ENTRY_SCRIPTS.get(candidate_id, [])
        entry_commands = [
            f"{sys.executable} {script}" for script in scripts
        ] if scripts else []

        if (
            skip_existing
            and not force
            and (artifact_dir / FULL_REPORT_SKIP_MARKER).is_file()
        ):
            step = {
                "candidate_id": candidate_id,
                "display_name": row["display_name"],
                "role": row["role"],
                "artifact_root": artifact_root,
                "status": "skipped_existing",
                "execution_action": "full_report_skipped_existing",
                "entry_commands": entry_commands,
                "exit_code": 0,
                "duration_seconds": 0.0,
                "reason_code": None,
                "message": f"{FULL_REPORT_SKIP_MARKER} present; full report export skipped.",
                "expected_analysis_end": analysis_end,
                "snapshot_analysis_end": None,
                "freshness_status": "fresh",
                "expected_config_fingerprint": config_fingerprint,
                "snapshot_config_fingerprint": None,
                "phases_completed": ["full_report"],
                "report_profile": REPORT_PROFILE_FULL,
            }
            _append_factory_step(
                steps,
                step,
                candidate_id=candidate_id,
                project_root=project_root,
                output_dir_final=output_dir_final,
            )
            _increment_summary(summary, "skipped_existing")
            _persist_manifest_step(
                manifest,
                output_dir=manifest_dir,
                candidate_id=candidate_id,
                step=step,
                project_root=project_root,
            )
            continue

        if not _execute_full_report(
            cfg=cfg,
            candidate_id=candidate_id,
            row=row,
            artifact_dir=artifact_dir,
            artifact_root=artifact_root,
            entry_commands=entry_commands,
            analysis_end=analysis_end,
            config_fingerprint=config_fingerprint,
            steps=steps,
            summary=summary,
            manifest=manifest,
            manifest_dir=manifest_dir,
            project_root=project_root,
            output_dir_final=output_dir_final,
            fail_fast=fail_fast,
            pdf_mode=pdf_mode,
            run_context=run_context,
        ):
            fail_fast_aborted = True
            break

    if normalize_pdf_mode(pdf_mode) == "final_only" and not fail_fast_aborted:
        final_timing = BuilderStepTiming()
        _rebuild_variant_pdfs_without_skip_env(timing=final_timing)
        steps.append(
            {
                "candidate_id": "__factory_pdf_final__",
                "display_name": "Factory final PDF rebuild",
                "role": "orchestration",
                "artifact_root": "",
                "status": "succeeded",
                "execution_action": "full_report_final_pdf_rebuild",
                "entry_commands": [],
                "exit_code": 0,
                "duration_seconds": final_timing.pdf_seconds,
                "reason_code": None,
                "message": None,
                "pdf_mode": "final_only",
                "full_report_targets": list(full_report_ids),
            }
        )
        summary["total"] = summary.get("total", 0) + 1
        summary["succeeded"] = summary.get("succeeded", 0) + 1

    return not fail_fast_aborted


def _empty_summary() -> dict[str, int]:
    return {
        "total": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped_existing": 0,
        "skipped_dependency": 0,
        "skipped_profile": 0,
        "rebuilt_stale": 0,
        "resumed_from_manifest": 0,
    }


def compute_factory_run_checksum(
    *,
    factory_profile_id: str,
    candidate_ids: list[str],
    analysis_end: str | None,
    config_fingerprint: str,
) -> str:
    """Stable checksum for resume manifest compatibility (profile, menu, review context)."""
    payload = "|".join(
        [
            factory_profile_id,
            ",".join(candidate_ids),
            analysis_end or "",
            config_fingerprint,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def factory_manifest_path(output_dir: Path) -> Path:
    return output_dir / MANIFEST_FILENAME


def load_factory_manifest(path: Path) -> dict[str, Any] | None:
    data = _load_json(path)
    if not data or data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        return None
    return data


def manifest_step_record(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": step["candidate_id"],
        "status": step["status"],
        "reason_code": step.get("reason_code"),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def build_factory_manifest(
    *,
    run_checksum: str,
    factory_profile_id: str,
    candidate_ids: list[str],
    analysis_end: str | None,
    config_fingerprint: str,
    project_root: Path,
    output_dir_final: str,
    completed_steps: dict[str, Any] | None = None,
    last_completed_candidate_id: str | None = None,
) -> dict[str, Any]:
    steps = dict(completed_steps or {})
    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "run_checksum": run_checksum,
        "factory_profile_id": factory_profile_id,
        "candidate_ids": list(candidate_ids),
        "analysis_end": analysis_end,
        "config_fingerprint": config_fingerprint,
        "project_root": str(project_root),
        "output_dir_final": output_dir_final,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "last_completed_candidate_id": last_completed_candidate_id,
        "completed_steps": steps,
    }
    return manifest


def write_factory_manifest(manifest: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = factory_manifest_path(output_dir)
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return path


def _manifest_entry_resumable(
    entry: dict[str, Any],
    *,
    snapshot_path: Path,
    expected_analysis_end: str | None,
    expected_config_fingerprint: str,
) -> bool:
    status = entry.get("status")
    if status not in RESUME_COMPLETE_STATUSES:
        return False
    if not snapshot_path.is_file():
        return False
    freshness, _, _ = _snapshot_freshness(
        snapshot_path,
        expected_analysis_end=expected_analysis_end,
        expected_config_fingerprint=expected_config_fingerprint,
    )
    if status == "skipped_existing":
        return freshness == "fresh"
    if status == "succeeded":
        return freshness in ("fresh", "unchecked")
    return False


def _synthesize_step_from_manifest(
    entry: dict[str, Any],
    *,
    row: dict[str, str],
    entry_commands: list[str],
    analysis_end: str | None,
    config_fingerprint: str,
    snapshot_path: Path,
) -> dict[str, Any]:
    freshness, snapshot_end, snapshot_fp = _snapshot_freshness(
        snapshot_path,
        expected_analysis_end=analysis_end,
        expected_config_fingerprint=config_fingerprint,
    )
    status = str(entry["status"])
    if status == "skipped_existing":
        message = "snapshot_10y.json already present; resumed without rerun."
        reason_code = "skipped_existing"
    else:
        message = "Prior successful build resumed without rerun."
        reason_code = None
    return {
        "candidate_id": entry["candidate_id"],
        "display_name": row["display_name"],
        "role": row["role"],
        "artifact_root": row["artifact_root"],
        "status": status,
        "execution_action": "resumed_from_manifest",
        "entry_commands": entry_commands,
        "exit_code": None,
        "duration_seconds": 0.0,
        "reason_code": reason_code,
        "message": message,
        "expected_analysis_end": analysis_end,
        "snapshot_analysis_end": snapshot_end,
        "freshness_status": freshness,
        "expected_config_fingerprint": config_fingerprint,
        "snapshot_config_fingerprint": snapshot_fp,
        "resume_from_manifest": True,
    }


def _persist_manifest_step(
    manifest: dict[str, Any],
    *,
    output_dir: Path,
    candidate_id: str,
    step: dict[str, Any],
    project_root: Path | None = None,
) -> None:
    manifest["completed_steps"][candidate_id] = manifest_step_record(step)
    manifest["last_completed_candidate_id"] = candidate_id
    write_factory_manifest(manifest, output_dir)
    artifact_root = step.get("artifact_root")
    if project_root is not None and artifact_root:
        manifest_path = write_candidate_manifest(project_root / str(artifact_root), step)
        if manifest_path is not None:
            try:
                rel = manifest_path.relative_to(project_root)
                step["candidate_manifest_path"] = rel.as_posix()
            except ValueError:
                step["candidate_manifest_path"] = manifest_path.as_posix()


def _increment_summary(summary: dict[str, int], status: str) -> None:
    summary["total"] += 1
    key = status if status in summary else "failed"
    if key in summary:
        summary[key] += 1
    else:
        summary["failed"] += 1


def run_candidate_factory(
    cfg: PortfolioConfig,
    *,
    project_root: Path,
    profile_id: str = "default_v1",
    explicit_candidates: list[str] | None = None,
    skip_existing: bool = True,
    force: bool = False,
    fail_fast: bool = False,
    resume: bool = False,
    config_path: Path | None = None,
    pdf_mode: str = "none",
    execution_mode: str = "legacy_full",
    full_candidate_reports: bool = False,
    selected_candidates_for_full_report: list[str] | None = None,
    parallel_lightweight_reports: bool = False,
    lightweight_report_workers: int | None = None,
    runner: Any | None = None,
) -> dict[str, Any]:
    try:
        candidate_ids = resolve_profile_candidate_ids(
            profile_id=profile_id,
            explicit_candidates=explicit_candidates,
        )
    except FactoryValidationError:
        raise

    if profile_id == "explicit_list" and not candidate_ids:
        raise FactoryValidationError("explicit_list profile requires --candidates")

    unknown = validate_candidate_ids(candidate_ids)
    if unknown:
        raise FactoryValidationError(
            f"Unknown candidate id(s): {', '.join(unknown)}"
        )

    full_report_ids = resolve_full_report_candidate_ids(
        candidate_ids,
        full_candidate_reports=full_candidate_reports,
        selected=selected_candidates_for_full_report,
    )

    steps: list[dict[str, Any]] = []
    summary = _empty_summary()
    warnings: list[str] = []
    python_exe = sys.executable
    pdf_mode_normalized = normalize_pdf_mode(pdf_mode)
    execution_mode_normalized = normalize_execution_mode(execution_mode)
    in_process_phase = uses_weights_only_phase(execution_mode_normalized)
    lightweight_report_phase = uses_lightweight_report_phase(execution_mode_normalized)
    parallel_lightweight_reports_effective = _parallel_lightweight_reports_effective(
        requested=parallel_lightweight_reports,
        execution_mode=execution_mode_normalized,
        fail_fast=fail_fast,
        pdf_mode=pdf_mode_normalized,
        full_report_ids=full_report_ids,
    )
    parallel_lightweight_report_fallback_reasons = (
        _parallel_lightweight_report_fallback_reasons(
            requested=parallel_lightweight_reports,
            execution_mode=execution_mode_normalized,
            fail_fast=fail_fast,
            pdf_mode=pdf_mode_normalized,
            full_report_ids=full_report_ids,
        )
    )
    lightweight_report_worker_count = _lightweight_report_worker_count(
        lightweight_report_workers,
        candidate_count=len(candidate_ids),
    )
    lightweight_report_executor: ThreadPoolExecutor | None = (
        ThreadPoolExecutor(max_workers=lightweight_report_worker_count)
        if parallel_lightweight_reports_effective
        else None
    )
    pending_lightweight_reports: list[dict[str, Any]] = []
    parallel_lightweight_report_started_at: float | None = None
    parallel_lightweight_report_wall_clock_seconds: float | None = None
    parallel_lightweight_submitted_candidate_ids: list[str] = []
    parallel_lightweight_registered_candidate_ids: list[str] = []
    subprocess_env = subprocess_env_for_pdf_mode(pdf_mode_normalized)
    run_context: CandidateRunContext | None = None
    output_dir_final = cfg.output_dir_final
    analysis_end = _resolve_analysis_end(project_root, output_dir_final)
    config_fingerprint = compute_candidate_config_fingerprint(cfg)
    factory_profile_id = profile_id if explicit_candidates is None else "explicit_list"
    run_checksum = compute_factory_run_checksum(
        factory_profile_id=factory_profile_id,
        candidate_ids=candidate_ids,
        analysis_end=analysis_end,
        config_fingerprint=config_fingerprint,
    )
    manifest_dir = project_root / output_dir_final
    prior_manifest = (
        load_factory_manifest(factory_manifest_path(manifest_dir)) if resume else None
    )
    resume_manifest_active = bool(
        resume
        and prior_manifest
        and prior_manifest.get("run_checksum") == run_checksum
    )
    if resume and not resume_manifest_active:
        if prior_manifest is None:
            warnings.append("resume_manifest_missing:no_skip_from_prior_run")
        else:
            warnings.append("resume_manifest_stale:run_checksum_mismatch_full_execution")

    completed_steps: dict[str, Any] = {}
    if resume_manifest_active:
        completed_steps = dict(prior_manifest.get("completed_steps") or {})

    manifest = build_factory_manifest(
        run_checksum=run_checksum,
        factory_profile_id=factory_profile_id,
        candidate_ids=candidate_ids,
        analysis_end=analysis_end,
        config_fingerprint=config_fingerprint,
        project_root=project_root,
        output_dir_final=output_dir_final,
        completed_steps=completed_steps,
        last_completed_candidate_id=(
            prior_manifest.get("last_completed_candidate_id") if resume_manifest_active else None
        ),
    )

    fail_fast_aborted = False

    for candidate_id in candidate_ids:
        row = registry_row(candidate_id)
        if row is None:
            step = _failed_step(
                candidate_id=candidate_id,
                display_name=candidate_id,
                role="unknown",
                artifact_root="",
                status="failed",
                reason_code="unknown_candidate_id",
                message="Candidate id is not in the registry.",
                entry_commands=[],
                exit_code=None,
                duration_seconds=0.0,
            )
            _append_factory_step(
                steps,
                step,
                candidate_id=candidate_id,
                project_root=project_root,
                output_dir_final=output_dir_final,
            )
            _increment_summary(summary, "failed")
            _persist_manifest_step(
                manifest,
                output_dir=manifest_dir,
                candidate_id=candidate_id,
                step=step,
                project_root=project_root,
            )
            if fail_fast:
                fail_fast_aborted = True
                break
            continue

        artifact_root = row["artifact_root"]
        artifact_dir = project_root / artifact_root
        snapshot_path = artifact_dir / SNAPSHOT_MINIMUM
        scripts = CANDIDATE_ENTRY_SCRIPTS.get(candidate_id, [])
        if not scripts:
            step = _failed_step(
                candidate_id=candidate_id,
                display_name=row["display_name"],
                role=row["role"],
                artifact_root=artifact_root,
                status="failed",
                reason_code="unknown_candidate_id",
                message="No entry script mapping for candidate.",
                entry_commands=[],
                exit_code=None,
                duration_seconds=0.0,
            )
            _append_factory_step(
                steps,
                step,
                candidate_id=candidate_id,
                project_root=project_root,
                output_dir_final=output_dir_final,
            )
            _increment_summary(summary, "failed")
            _persist_manifest_step(
                manifest,
                output_dir=manifest_dir,
                candidate_id=candidate_id,
                step=step,
                project_root=project_root,
            )
            if fail_fast:
                fail_fast_aborted = True
                break
            continue

        commands = _build_subprocess_commands(
            scripts,
            python_exe=python_exe,
            project_root=project_root,
            config_path=config_path,
        )
        entry_commands = _command_strings(commands)

        if resume_manifest_active and not force:
            prior_entry = manifest["completed_steps"].get(candidate_id)
            if prior_entry and _manifest_entry_resumable(
                prior_entry,
                snapshot_path=snapshot_path,
                expected_analysis_end=analysis_end,
                expected_config_fingerprint=config_fingerprint,
            ):
                step = _synthesize_step_from_manifest(
                    prior_entry,
                    row=row,
                    entry_commands=entry_commands,
                    analysis_end=analysis_end,
                    config_fingerprint=config_fingerprint,
                    snapshot_path=snapshot_path,
                )
                _append_factory_step(
                    steps,
                    step,
                    candidate_id=candidate_id,
                    project_root=project_root,
                    output_dir_final=output_dir_final,
                )
                _increment_summary(summary, step["status"])
                summary["resumed_from_manifest"] += 1
                if not skip_existing:
                    warnings.append(
                        "resume_manifest_reused_completed_step_despite_no_skip_existing:"
                        f"{candidate_id}:builder_not_rerun"
                    )
                _persist_manifest_step(
                    manifest,
                    output_dir=manifest_dir,
                    candidate_id=candidate_id,
                    step=step,
                    project_root=project_root,
                )
                continue

        if in_process_phase and skip_existing and not force:
            snap_freshness, snap_end, snap_fp = _snapshot_freshness(
                snapshot_path,
                expected_analysis_end=analysis_end,
                expected_config_fingerprint=config_fingerprint,
            )
            if lightweight_report_phase and snap_freshness == "fresh":
                step = _failed_step(
                    candidate_id=candidate_id,
                    display_name=row["display_name"],
                    role=row["role"],
                    artifact_root=artifact_root,
                    status="skipped_existing",
                    reason_code="skipped_existing",
                    message="snapshot_10y.json already fresh; weights and report skipped.",
                    entry_commands=entry_commands,
                    exit_code=None,
                    duration_seconds=0.0,
                    expected_analysis_end=analysis_end,
                    snapshot_analysis_end=snap_end,
                    freshness_status=snap_freshness,
                    expected_config_fingerprint=config_fingerprint,
                    snapshot_config_fingerprint=snap_fp,
                )
                step["execution_action"] = "reused_existing_snapshot"
                step["phases_completed"] = ["weights", "report"]
                step["report_profile"] = REPORT_PROFILE_LIGHTWEIGHT
                _append_factory_step(
                    steps,
                    step,
                    candidate_id=candidate_id,
                    project_root=project_root,
                    output_dir_final=output_dir_final,
                )
                _increment_summary(summary, "skipped_existing")
                _persist_manifest_step(
                    manifest,
                    output_dir=manifest_dir,
                    candidate_id=candidate_id,
                    step=step,
                    project_root=project_root,
                )
                continue
            if not lightweight_report_phase:
                w_freshness, w_end, w_fp = weights_build_freshness(
                    artifact_dir,
                    expected_analysis_end=analysis_end,
                    expected_config_fingerprint=config_fingerprint,
                )
                if w_freshness == "fresh":
                    step = _failed_step(
                        candidate_id=candidate_id,
                        display_name=row["display_name"],
                        role=row["role"],
                        artifact_root=artifact_root,
                        status="skipped_existing",
                        reason_code="skipped_existing",
                        message=(
                            "candidate_weights_build.json already fresh; "
                            "weights step skipped."
                        ),
                        entry_commands=entry_commands,
                        exit_code=None,
                        duration_seconds=0.0,
                        expected_analysis_end=analysis_end,
                        snapshot_analysis_end=w_end,
                        freshness_status=w_freshness,
                        expected_config_fingerprint=config_fingerprint,
                        snapshot_config_fingerprint=w_fp,
                    )
                    step["execution_action"] = "reused_existing_weights"
                    _append_factory_step(
                        steps,
                        step,
                        candidate_id=candidate_id,
                        project_root=project_root,
                        output_dir_final=output_dir_final,
                    )
                    _increment_summary(summary, "skipped_existing")
                    _persist_manifest_step(
                        manifest,
                        output_dir=manifest_dir,
                        candidate_id=candidate_id,
                        step=step,
                        project_root=project_root,
                    )
                    continue

        if skip_existing and not force and snapshot_path.is_file() and not in_process_phase:
            freshness, snapshot_end, snapshot_fp = _snapshot_freshness(
                snapshot_path,
                expected_analysis_end=analysis_end,
                expected_config_fingerprint=config_fingerprint,
            )
            if freshness == "fresh":
                step = _failed_step(
                    candidate_id=candidate_id,
                    display_name=row["display_name"],
                    role=row["role"],
                    artifact_root=artifact_root,
                    status="skipped_existing",
                    reason_code="skipped_existing",
                    message="snapshot_10y.json already present; step skipped.",
                    entry_commands=entry_commands,
                    exit_code=None,
                    duration_seconds=0.0,
                    expected_analysis_end=analysis_end,
                    snapshot_analysis_end=snapshot_end,
                    freshness_status=freshness,
                    expected_config_fingerprint=config_fingerprint,
                    snapshot_config_fingerprint=snapshot_fp,
                )
                _append_factory_step(
                    steps,
                    step,
                    candidate_id=candidate_id,
                    project_root=project_root,
                    output_dir_final=output_dir_final,
                )
                _increment_summary(summary, "skipped_existing")
                _persist_manifest_step(
                    manifest,
                    output_dir=manifest_dir,
                    candidate_id=candidate_id,
                    step=step,
                    project_root=project_root,
                )
                continue
            if freshness == "unchecked":
                warnings.append(
                    f"unchecked_candidate_snapshot_rebuild_attempted:{candidate_id}:"
                    "review_analysis_end_unavailable"
                )
            elif freshness == "stale_config":
                warnings.append(
                    f"stale_candidate_config_fingerprint_rebuild_attempted:{candidate_id}:"
                    f"{snapshot_fp or 'missing'}!={config_fingerprint}"
                )
            else:
                warnings.append(
                    f"stale_candidate_snapshot_rebuild_attempted:{candidate_id}:"
                    f"{snapshot_end or 'missing_analysis_end'}!={analysis_end}"
                )

        if candidate_id == "robust_scenario" and not _robust_scenario_prerequisites_met(
            project_root, output_dir_final
        ):
            prereq_disc = build_robust_scenario_prerequisites_disclosure(
                project_root=project_root,
                output_dir_final=output_dir_final,
            )
            missing = prereq_disc.get("missing_artifacts") or list(
                ROBUST_SCENARIO_PREREQUISITES
            )
            step = _failed_step(
                candidate_id=candidate_id,
                display_name=row["display_name"],
                role=row["role"],
                artifact_root=artifact_root,
                status="skipped_dependency",
                reason_code="skipped_dependency",
                message=(
                    f"Missing Main prerequisites under {output_dir_final}: "
                    f"{', '.join(missing)}. "
                    f"{prereq_disc.get('recommended_before_factory', 'Run Main report first.')}"
                ),
                entry_commands=entry_commands,
                exit_code=None,
                duration_seconds=0.0,
            )
            _append_factory_step(
                steps,
                step,
                candidate_id=candidate_id,
                project_root=project_root,
                output_dir_final=output_dir_final,
            )
            _increment_summary(summary, "skipped_dependency")
            _persist_manifest_step(
                manifest,
                output_dir=manifest_dir,
                candidate_id=candidate_id,
                step=step,
                project_root=project_root,
            )
            continue

        if in_process_phase:
            weights_reused = False
            if skip_existing and not force:
                w_freshness, _, _ = weights_build_freshness(
                    artifact_dir,
                    expected_analysis_end=analysis_end,
                    expected_config_fingerprint=config_fingerprint,
                )
                weights_reused = w_freshness == "fresh"
            need_weights_build = force or not weights_reused
            if need_weights_build:
                if run_context is None:
                    run_context = prepare_candidate_run_context(
                        cfg, project_root=project_root
                    )
                if not _execute_weights_only_build(
                    candidate_id=candidate_id,
                    row=row,
                    artifact_dir=artifact_dir,
                    artifact_root=artifact_root,
                    entry_commands=entry_commands,
                    context=run_context,
                    analysis_end=analysis_end,
                    config_fingerprint=config_fingerprint,
                    steps=steps,
                    summary=summary,
                    manifest=manifest,
                    manifest_dir=manifest_dir,
                    project_root=project_root,
                    output_dir_final=output_dir_final,
                    fail_fast=fail_fast,
                    record_factory_step=not lightweight_report_phase,
                ):
                    if fail_fast:
                        fail_fast_aborted = True
                    break
            if lightweight_report_phase:
                report_weights_reused = weights_reused and not need_weights_build
                if parallel_lightweight_reports_effective:
                    assert lightweight_report_executor is not None
                    if parallel_lightweight_report_started_at is None:
                        parallel_lightweight_report_started_at = time.perf_counter()
                    future: Future[dict[str, Any]] = lightweight_report_executor.submit(
                        _run_lightweight_report_worker,
                        cfg=cfg,
                        candidate_id=candidate_id,
                        row=row,
                        artifact_dir=artifact_dir,
                        artifact_root=artifact_root,
                        entry_commands=entry_commands,
                        analysis_end=analysis_end,
                        config_fingerprint=config_fingerprint,
                        weights_reused=report_weights_reused,
                        run_context=run_context,
                    )
                    parallel_lightweight_submitted_candidate_ids.append(candidate_id)
                    pending_lightweight_reports.append(
                        {
                            "candidate_id": candidate_id,
                            "row": row,
                            "artifact_root": artifact_root,
                            "entry_commands": entry_commands,
                            "analysis_end": analysis_end,
                            "config_fingerprint": config_fingerprint,
                            "future": future,
                        }
                    )
                elif not _execute_lightweight_report(
                    cfg=cfg,
                    candidate_id=candidate_id,
                    row=row,
                    artifact_dir=artifact_dir,
                    artifact_root=artifact_root,
                    entry_commands=entry_commands,
                    analysis_end=analysis_end,
                    config_fingerprint=config_fingerprint,
                    steps=steps,
                    summary=summary,
                    manifest=manifest,
                    manifest_dir=manifest_dir,
                    project_root=project_root,
                    output_dir_final=output_dir_final,
                    fail_fast=fail_fast,
                    weights_reused=report_weights_reused,
                    run_context=run_context,
                ):
                    if fail_fast:
                        fail_fast_aborted = True
                    break
            continue

        t0 = time.perf_counter()
        exit_code, stderr_tail = _run_subprocess_chain(
            commands,
            project_root=project_root,
            runner=runner,
            subprocess_env=subprocess_env,
        )
        duration = round(time.perf_counter() - t0, 3)
        builder_timing = load_builder_runtime_timing(artifact_dir)

        if exit_code != 0 or not snapshot_path.is_file():
            reason_code, message, builder_status, builder_reason = _post_build_failure_details(
                artifact_dir,
                exit_code=exit_code,
                stderr_tail=stderr_tail,
            )
            freshness = "missing" if not snapshot_path.is_file() else None
            step = _failed_step(
                candidate_id=candidate_id,
                display_name=row["display_name"],
                role=row["role"],
                artifact_root=artifact_root,
                status="failed",
                reason_code=reason_code,
                message=message,
                entry_commands=entry_commands,
                exit_code=exit_code,
                duration_seconds=duration,
                expected_analysis_end=analysis_end,
                snapshot_analysis_end=None,
                freshness_status=freshness,
                expected_config_fingerprint=config_fingerprint,
                snapshot_config_fingerprint=None,
                builder_status=builder_status,
                builder_reason=builder_reason,
            )
            merge_timing_into_step(step, builder_timing)
            _append_factory_step(
                steps,
                step,
                candidate_id=candidate_id,
                project_root=project_root,
                output_dir_final=output_dir_final,
            )
            _increment_summary(summary, "failed")
            _persist_manifest_step(
                manifest,
                output_dir=manifest_dir,
                candidate_id=candidate_id,
                step=step,
                project_root=project_root,
            )
            if fail_fast:
                fail_fast_aborted = True
                break
            continue

        freshness, snapshot_end, snapshot_fp = _snapshot_freshness(
            snapshot_path,
            expected_analysis_end=analysis_end,
            expected_config_fingerprint=config_fingerprint,
        )
        if freshness == "stale":
            step = _failed_step(
                candidate_id=candidate_id,
                display_name=row["display_name"],
                role=row["role"],
                artifact_root=artifact_root,
                status="failed",
                reason_code="stale_snapshot_after_build",
                message=(
                    f"{SNAPSHOT_MINIMUM} analysis_end {snapshot_end or 'missing'} "
                    f"does not match review analysis_end {analysis_end} after builder exit."
                ),
                entry_commands=entry_commands,
                exit_code=exit_code,
                duration_seconds=duration,
                expected_analysis_end=analysis_end,
                snapshot_analysis_end=snapshot_end,
                freshness_status=freshness,
                expected_config_fingerprint=config_fingerprint,
                snapshot_config_fingerprint=snapshot_fp,
            )
            _append_factory_step(
                steps,
                step,
                candidate_id=candidate_id,
                project_root=project_root,
                output_dir_final=output_dir_final,
            )
            _increment_summary(summary, "failed")
            _persist_manifest_step(
                manifest,
                output_dir=manifest_dir,
                candidate_id=candidate_id,
                step=step,
                project_root=project_root,
            )
            if fail_fast:
                fail_fast_aborted = True
                break
            continue
        if freshness == "stale_config":
            step = _failed_step(
                candidate_id=candidate_id,
                display_name=row["display_name"],
                role=row["role"],
                artifact_root=artifact_root,
                status="failed",
                reason_code="stale_config_fingerprint_after_build",
                message=(
                    f"{SNAPSHOT_MINIMUM} {CANDIDATE_CONFIG_FINGERPRINT_KEY} "
                    f"{snapshot_fp or 'missing'} does not match review config fingerprint "
                    f"{config_fingerprint} after builder exit."
                ),
                entry_commands=entry_commands,
                exit_code=exit_code,
                duration_seconds=duration,
                expected_analysis_end=analysis_end,
                snapshot_analysis_end=snapshot_end,
                freshness_status=freshness,
                expected_config_fingerprint=config_fingerprint,
                snapshot_config_fingerprint=snapshot_fp,
            )
            _append_factory_step(
                steps,
                step,
                candidate_id=candidate_id,
                project_root=project_root,
                output_dir_final=output_dir_final,
            )
            _increment_summary(summary, "failed")
            _persist_manifest_step(
                manifest,
                output_dir=manifest_dir,
                candidate_id=candidate_id,
                step=step,
                project_root=project_root,
            )
            if fail_fast:
                fail_fast_aborted = True
                break
            continue

        step = {
            "candidate_id": candidate_id,
            "display_name": row["display_name"],
            "role": row["role"],
            "artifact_root": artifact_root,
            "status": "succeeded",
            "execution_action": "builder_invoked",
            "entry_commands": entry_commands,
            "exit_code": exit_code,
            "duration_seconds": duration,
            "reason_code": None,
            "message": None,
            "expected_analysis_end": analysis_end,
            "snapshot_analysis_end": snapshot_end,
            "freshness_status": freshness,
            "expected_config_fingerprint": config_fingerprint,
            "snapshot_config_fingerprint": snapshot_fp,
        }
        merge_timing_into_step(step, builder_timing)
        _append_factory_step(
            steps,
            step,
            candidate_id=candidate_id,
            project_root=project_root,
            output_dir_final=output_dir_final,
        )
        _increment_summary(summary, "succeeded")
        if any(
            w.startswith(
                (
                    f"stale_candidate_snapshot_rebuild_attempted:{candidate_id}:",
                    f"stale_candidate_config_fingerprint_rebuild_attempted:{candidate_id}:",
                    f"unchecked_candidate_snapshot_rebuild_attempted:{candidate_id}:",
                )
            )
            for w in warnings
        ):
            summary["rebuilt_stale"] += 1
        _persist_manifest_step(
            manifest,
            output_dir=manifest_dir,
            candidate_id=candidate_id,
            step=step,
            project_root=project_root,
        )

    if pending_lightweight_reports:
        _register_parallel_lightweight_report_results(
            pending_lightweight_reports,
            steps=steps,
            summary=summary,
            manifest=manifest,
            manifest_dir=manifest_dir,
            project_root=project_root,
            output_dir_final=output_dir_final,
        )
        parallel_lightweight_registered_candidate_ids = [
            str(s.get("candidate_id"))
            for s in steps
            if s.get("execution_action")
            in {
                "lightweight_report_built",
                "lightweight_report_reused_weights",
                "lightweight_report_failed",
            }
        ]
        if parallel_lightweight_report_started_at is not None:
            parallel_lightweight_report_wall_clock_seconds = (
                time.perf_counter() - parallel_lightweight_report_started_at
            )
    if lightweight_report_executor is not None:
        lightweight_report_executor.shutdown(wait=True)
    if parallel_lightweight_reports_effective:
        order = {candidate_id: idx for idx, candidate_id in enumerate(candidate_ids)}
        steps.sort(key=lambda step: order.get(str(step.get("candidate_id")), len(order)))
        if steps:
            manifest["last_completed_candidate_id"] = steps[-1].get("candidate_id")

    if full_report_ids:
        if run_context is None:
            run_context = prepare_candidate_run_context(
                cfg, project_root, no_cache=False
            )
        if not _run_full_candidate_reports_phase(
            cfg=cfg,
            full_report_ids=full_report_ids,
            steps=steps,
            summary=summary,
            manifest=manifest,
            manifest_dir=manifest_dir,
            project_root=project_root,
            output_dir_final=output_dir_final,
            analysis_end=analysis_end,
            config_fingerprint=config_fingerprint,
            skip_existing=skip_existing,
            force=force,
            fail_fast=fail_fast,
            pdf_mode=pdf_mode_normalized,
            run_context=run_context,
        ):
            fail_fast_aborted = True

    manifest_path = write_factory_manifest(manifest, manifest_dir)
    run_status = compute_factory_run_status(
        summary,
        fail_fast=fail_fast,
        fail_fast_aborted=fail_fast_aborted,
    )
    doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "run_status": run_status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "factory_profile_id": factory_profile_id,
        "project_root": str(project_root),
        "output_dir_final": output_dir_final,
        "config_path": str(config_path) if config_path else "config.yml",
        "analysis_end": analysis_end,
        "config_fingerprint": config_fingerprint,
        "options": {
            "skip_existing": skip_existing,
            "force": force,
            "fail_fast": fail_fast,
            "resume": resume,
            "then_compare": False,
            "pdf_mode": pdf_mode_normalized,
            "execution_mode": execution_mode_normalized,
            "parallel_lightweight_reports": parallel_lightweight_reports,
            "parallel_lightweight_reports_effective": parallel_lightweight_reports_effective,
            "lightweight_report_workers": lightweight_report_worker_count,
            "full_candidate_reports": bool(
                full_candidate_reports or selected_candidates_for_full_report
            ),
            "selected_candidates_for_full_report": selected_candidates_for_full_report,
        },
        "manifest": {
            "path": str(manifest_path),
            "run_checksum": run_checksum,
            "resume_manifest_active": resume_manifest_active,
        },
        "steps": steps,
        "summary": summary,
        "warnings": warnings,
        "next_recommended_command": compute_next_recommended_command(
            {
                "factory_profile_id": factory_profile_id,
                "steps": steps,
                "summary": summary,
                "warnings": warnings,
                "options": {
                    "skip_existing": skip_existing,
                    "force": force,
                    "fail_fast": fail_fast,
                    "resume": resume,
                    "then_compare": False,
                },
            }
        ),
    }
    parallel_summary = _parallel_lightweight_report_summary(
        requested=parallel_lightweight_reports,
        effective=parallel_lightweight_reports_effective,
        workers=lightweight_report_worker_count,
        submitted_candidate_ids=parallel_lightweight_submitted_candidate_ids,
        registered_candidate_ids=parallel_lightweight_registered_candidate_ids,
        wall_clock_seconds=parallel_lightweight_report_wall_clock_seconds,
        fallback_reasons=parallel_lightweight_report_fallback_reasons,
    )
    if parallel_summary is not None:
        doc["parallel_lightweight_report_summary"] = parallel_summary
    doc["execution_summary"] = build_factory_execution_summary(doc)
    doc["timing_summary"] = build_timing_summary(doc.get("steps") or [])
    return doc


def _append_factory_step(
    steps: list[dict[str, Any]],
    step: dict[str, Any],
    *,
    candidate_id: str,
    project_root: Path,
    output_dir_final: str,
) -> None:
    baseline_metadata: dict[str, Any] | None = None
    artifact_root = step.get("artifact_root")
    if artifact_root:
        evidence = _optimizer_status_evidence(project_root / str(artifact_root))
        for key, value in evidence.items():
            if value is not None:
                step[key] = value
    if candidate_id in ROBUST_MV_CANDIDATE_IDS:
        if artifact_root:
            meta = _load_json(project_root / artifact_root / "baseline_weights_metadata.json")
            if meta:
                baseline_metadata = meta
    steps.append(
        merge_robust_paths_into_step(
            step,
            candidate_id=candidate_id,
            project_root=project_root,
            output_dir_final=output_dir_final,
            baseline_metadata=baseline_metadata,
        )
    )


def _failed_step(
    *,
    candidate_id: str,
    display_name: str,
    role: str,
    artifact_root: str,
    status: str,
    reason_code: str,
    message: str,
    entry_commands: list[str],
    exit_code: int | None,
    duration_seconds: float,
    expected_analysis_end: str | None = None,
    snapshot_analysis_end: str | None = None,
    freshness_status: str | None = None,
    expected_config_fingerprint: str | None = None,
    snapshot_config_fingerprint: str | None = None,
    builder_status: str | None = None,
    builder_reason: str | None = None,
) -> dict[str, Any]:
    if status == "skipped_existing":
        execution_action = "reused_existing_snapshot"
    elif status == "skipped_dependency":
        execution_action = "skipped_dependency"
    elif status == "failed" and entry_commands:
        execution_action = "builder_invoked_failed"
    else:
        execution_action = "failed_before_build"
    step: dict[str, Any] = {
        "candidate_id": candidate_id,
        "display_name": display_name,
        "role": role,
        "artifact_root": artifact_root,
        "status": status,
        "execution_action": execution_action,
        "entry_commands": entry_commands,
        "exit_code": exit_code,
        "duration_seconds": duration_seconds,
        "reason_code": reason_code,
        "message": message,
        "expected_analysis_end": expected_analysis_end,
        "snapshot_analysis_end": snapshot_analysis_end,
        "freshness_status": freshness_status,
        "expected_config_fingerprint": expected_config_fingerprint,
        "snapshot_config_fingerprint": snapshot_config_fingerprint,
    }
    if builder_status is not None:
        step["builder_status"] = builder_status
    if builder_reason is not None:
        step["builder_reason"] = builder_reason
    return step


class FactoryValidationError(Exception):
    """Registry/profile validation failed before any builder runs."""


def _factory_resume_cli_command(doc: dict[str, Any]) -> str:
    """CLI fragment to resume the same menu as this run."""
    profile_id = str(doc.get("factory_profile_id") or "default_v1")
    if profile_id == "explicit_list":
        ids = [
            str(s["candidate_id"])
            for s in doc.get("steps") or []
            if s.get("candidate_id")
        ]
        if ids:
            return f"python run_candidate_factory.py --candidates {','.join(ids)} --resume"
        return "python run_candidate_factory.py --resume"
    return f"python run_candidate_factory.py --profile {profile_id} --resume"


def compute_next_recommended_command(doc: dict[str, Any]) -> str:
    """
    Contextual next step for operators (Session 10 / RM-980).

    Diagnostic only — does not execute commands.
    """
    summary = doc.get("summary") or {}
    warnings = [str(w) for w in (doc.get("warnings") or [])]
    profile_id = str(doc.get("factory_profile_id") or "default_v1")

    if summary.get("failed", 0) > 0:
        return _factory_resume_cli_command(doc)

    options = doc.get("options") or {}
    if (
        options.get("execution_mode") == "standard"
        and not options.get("full_candidate_reports")
        and not options.get("selected_candidates_for_full_report")
        and summary.get("succeeded", 0) > 0
    ):
        return (
            f"python run_candidate_factory.py --profile {profile_id} "
            "--execution-mode standard "
            "--selected-candidates-for-full-report equal_weight,risk_parity "
            "# optional deep-dive HTML/PDF for selected candidates"
        )

    if any(w.startswith("comparison_failed:") for w in warnings):
        return "python run_compare_variants.py"

    if any(w.startswith("resume_manifest_stale:") for w in warnings):
        if profile_id == "explicit_list":
            ids = [
                str(s["candidate_id"])
                for s in doc.get("steps") or []
                if s.get("candidate_id")
            ]
            if ids:
                return (
                    f"python run_candidate_factory.py --candidates {','.join(ids)} "
                    "--no-skip-existing"
                )
        return f"python run_candidate_factory.py --profile {profile_id} --no-skip-existing"

    options = doc.get("options") or {}
    if options.get("then_compare") and not any(
        w.startswith("comparison_failed:") for w in warnings
    ):
        return (
            "python run_compare_variants.py  "
            "# --then-compare already ran; inspect candidate_comparison.json"
        )

    return "python run_compare_variants.py"


def build_factory_execution_summary(doc: dict[str, Any]) -> dict[str, Any]:
    """Human/audit disclosure of which candidates were built vs reused."""
    steps = [s for s in doc.get("steps") or [] if isinstance(s, dict)]
    build_success_actions = {
        "builder_invoked",
        "weights_built",
        "lightweight_report_built",
        "lightweight_report_reused_weights",
        "full_report_built",
        "full_report_final_pdf_rebuild",
    }
    build_failed_actions = {
        "builder_invoked_failed",
        "weights_built_failed",
        "lightweight_report_failed",
        "full_report_failed",
    }
    in_process_build_actions = build_success_actions | build_failed_actions
    in_process_build_actions.discard("builder_invoked")
    in_process_build_actions.discard("builder_invoked_failed")
    reuse_actions = {
        "reused_existing_snapshot",
        "reused_existing_weights",
        "full_report_skipped_existing",
    }

    def _candidate_ids_for(actions: set[str]) -> list[str]:
        ids: list[str] = []
        seen: set[str] = set()
        for step in steps:
            if step.get("execution_action") not in actions:
                continue
            candidate_id = str(step.get("candidate_id"))
            if candidate_id in seen:
                continue
            ids.append(candidate_id)
            seen.add(candidate_id)
        return ids

    build_success_ids = _candidate_ids_for(build_success_actions)
    failed_build_ids = _candidate_ids_for(build_failed_actions)
    built_ids = [
        str(s.get("candidate_id"))
        for s in steps
        if s.get("execution_action") == "builder_invoked"
    ]
    failed_builder_ids = [
        str(s.get("candidate_id"))
        for s in steps
        if s.get("execution_action") == "builder_invoked_failed"
    ]
    reused_existing_ids = _candidate_ids_for(reuse_actions)
    reused_snapshot_ids = _candidate_ids_for({"reused_existing_snapshot"})
    reused_weights_ids = _candidate_ids_for({"reused_existing_weights"})
    resumed_ids = [
        str(s.get("candidate_id"))
        for s in steps
        if s.get("execution_action") == "resumed_from_manifest"
    ]
    skipped_dependency_ids = [
        str(s.get("candidate_id"))
        for s in steps
        if s.get("execution_action") == "skipped_dependency"
    ]
    return {
        "build_steps_executed": sum(
            1
            for s in steps
            if s.get("execution_action") in build_success_actions | build_failed_actions
        ),
        "build_steps_succeeded": sum(
            1 for s in steps if s.get("execution_action") in build_success_actions
        ),
        "build_steps_failed": sum(
            1 for s in steps if s.get("execution_action") in build_failed_actions
        ),
        "in_process_build_steps": sum(
            1 for s in steps if s.get("execution_action") in in_process_build_actions
        ),
        "builder_invoked": len(built_ids) + len(failed_builder_ids),
        "builder_invoked_succeeded": len(built_ids),
        "builder_invoked_failed": len(failed_builder_ids),
        "reused_existing": len(reused_existing_ids),
        "reused_existing_snapshot": len(reused_snapshot_ids),
        "reused_existing_weights": len(reused_weights_ids),
        "resumed_from_manifest": len(resumed_ids),
        "skipped_dependency": len(skipped_dependency_ids),
        "rebuilt_candidate_ids": build_success_ids,
        "failed_build_candidate_ids": failed_build_ids,
        "reused_candidate_ids": reused_existing_ids,
        "resumed_candidate_ids": resumed_ids,
        "skipped_dependency_candidate_ids": skipped_dependency_ids,
        "no_skip_existing_requested": not bool((doc.get("options") or {}).get("skip_existing", True)),
        "resume_requested": bool((doc.get("options") or {}).get("resume", False)),
    }


def build_factory_run_txt(doc: dict[str, Any]) -> str:
    lines = [
        "Candidate Portfolio Factory Run",
        f"Profile: {doc.get('factory_profile_id')}",
        f"Generated: {doc.get('generated_at')}",
        "",
    ]
    summary = doc.get("summary") or {}
    execution = doc.get("execution_summary") or build_factory_execution_summary(doc)
    run_status = doc.get("run_status")
    if run_status:
        lines.append(f"Run status: {run_status}")
    lines.append(
        "Summary: "
        f"total={summary.get('total', 0)} "
        f"succeeded={summary.get('succeeded', 0)} "
        f"failed={summary.get('failed', 0)} "
        f"skipped_existing={summary.get('skipped_existing', 0)} "
        f"skipped_dependency={summary.get('skipped_dependency', 0)} "
        f"rebuilt_stale={summary.get('rebuilt_stale', 0)} "
        f"resumed_from_manifest={summary.get('resumed_from_manifest', 0)}"
    )
    if run_status == "partial_success":
        lines.append(
            "Partial failure: one or more candidates failed; remaining steps continued "
            "(use --fail-fast to stop on first failure)."
        )
    lines.append(
        "Execution: "
        f"build_steps_executed={execution.get('build_steps_executed', 0)} "
        f"builder_invoked={execution.get('builder_invoked', 0)} "
        f"in_process_build_steps={execution.get('in_process_build_steps', 0)} "
        f"reused_existing={execution.get('reused_existing', 0)} "
        f"reused_existing_snapshot={execution.get('reused_existing_snapshot', 0)} "
        f"resumed_from_manifest={execution.get('resumed_from_manifest', 0)} "
        f"skipped_dependency={execution.get('skipped_dependency', 0)}"
    )
    options = doc.get("options") or {}
    if options.get("pdf_mode"):
        lines.append(f"PDF mode: {options.get('pdf_mode')}")
    if options.get("execution_mode"):
        lines.append(f"Execution mode: {options.get('execution_mode')}")
    parallel = doc.get("parallel_lightweight_report_summary") or {}
    if parallel:
        text = (
            "Parallel lightweight reports: "
            f"status={parallel.get('status')} "
            f"workers={parallel.get('workers')} "
            f"submitted={parallel.get('submitted_count')} "
            f"completed={parallel.get('completed_count')}"
        )
        if parallel.get("wall_clock_seconds") is not None:
            text += f" wall_clock_seconds={parallel.get('wall_clock_seconds')}"
        reasons = parallel.get("fallback_reasons") or []
        if reasons:
            text += f" fallback_reasons={','.join(str(r) for r in reasons)}"
        lines.append(text)
    if options.get("full_candidate_reports") or options.get(
        "selected_candidates_for_full_report"
    ):
        targets = options.get("selected_candidates_for_full_report")
        if targets:
            lines.append(f"Full report export: {', '.join(targets)}")
        else:
            lines.append("Full report export: all candidates in this run")
    timing = doc.get("timing_summary") or {}
    if timing.get("steps_with_timing", 0) > 0:
        lines.append(
            "Timing (seconds): "
            f"core={timing.get('builder_core_seconds', 0)} "
            f"report={timing.get('report_seconds', 0)} "
            f"pdf={timing.get('pdf_seconds', 0)} "
            f"total={timing.get('total_seconds', 0)} "
            f"(steps_with_timing={timing.get('steps_with_timing', 0)})"
        )
    if execution.get("no_skip_existing_requested"):
        lines.append(
            "--no-skip-existing requested: rows with build execution actions were "
            "rebuilt; rows with resumed_from_manifest were not rerun because resume "
            "was active."
        )
    manifest = doc.get("manifest") or {}
    if manifest.get("resume_manifest_active"):
        lines.append("Resume: prior manifest applied (completed steps not rerun).")
    failed_steps = [s for s in doc.get("steps") or [] if s.get("status") == "failed"]
    if failed_steps:
        lines.append(
            "Failed candidates: "
            + ", ".join(str(s.get("candidate_id")) for s in failed_steps)
        )
        lines.append("")
        lines.append("Failed step details (reason_code):")
        for step in failed_steps:
            cid = step.get("candidate_id") or "?"
            rc = step.get("reason_code") or "unknown"
            detail = f"  - {cid}: {rc}"
            message = step.get("message")
            if message:
                detail = f"{detail} — {message}"
            builder_status = step.get("builder_status")
            if builder_status:
                detail = f"{detail} [builder status {builder_status}]"
            lines.append(detail)
        lines.append(
            "  Playbook: docs/operational_runbook.md section 8 (reason codes and recovery)."
        )
    dep_skipped = [
        s["candidate_id"]
        for s in doc.get("steps") or []
        if s.get("status") == "skipped_dependency"
    ]
    if dep_skipped:
        lines.append(f"Skipped (dependency): {', '.join(dep_skipped)}")
    warnings = doc.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"  - {w}" for w in warnings)
    lines.append("")
    next_cmd = doc.get("next_recommended_command") or compute_next_recommended_command(doc)
    lines.append(f"Next: {next_cmd}")
    exit_hint = 1 if summary.get("failed", 0) > 0 else 0
    lines.append(f"CLI exit code (factory only): {exit_hint}")
    return "\n".join(lines) + "\n"


def write_candidate_factory_outputs(
    doc: dict[str, Any],
    *,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "candidate_factory_run.json"
    txt_path = output_dir / "candidate_factory_run.txt"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    txt_path.write_text(ascii_safe_text(build_factory_run_txt(doc)), encoding="utf-8")
    written: dict[str, Path] = {
        "candidate_factory_run_json": json_path,
        "candidate_factory_run_txt": txt_path,
    }
    manifest_block = doc.get("manifest") or {}
    manifest_path = manifest_block.get("path")
    if manifest_path:
        written["candidate_factory_manifest_json"] = Path(manifest_path)
    return written


def factory_exit_code(doc: dict[str, Any]) -> int:
    summary = doc.get("summary") or {}
    if summary.get("failed", 0) > 0:
        return 1
    return 0


def run_then_compare(
    cfg: PortfolioConfig,
    *,
    project_root: Path,
    factory_run: dict[str, Any] | None = None,
) -> tuple[dict[str, Path] | None, str | None]:
    from src.candidate_comparison import (
        COMPARISON_REBUILD_FACTORY_THEN_COMPARE,
        write_candidate_comparison_outputs,
    )

    try:
        paths = write_candidate_comparison_outputs(
            cfg,
            project_root=project_root,
            factory_run=factory_run,
            comparison_rebuild_source=COMPARISON_REBUILD_FACTORY_THEN_COMPARE,
        )
        return paths, None
    except Exception as exc:  # noqa: BLE001 — surface comparison failure in factory summary
        return None, str(exc)
