"""
Candidate Portfolio Factory orchestration.

See docs/specs/candidate_factory_spec.md.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
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

SCHEMA_VERSION = "candidate_factory_run_v1"
MANIFEST_SCHEMA_VERSION = "candidate_factory_manifest_v1"
MANIFEST_FILENAME = "candidate_factory_manifest.json"
RESUME_COMPLETE_STATUSES = frozenset({"succeeded", "skipped_existing"})
SNAPSHOT_MINIMUM = "snapshot_10y.json"
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
) -> tuple[int, str | None]:
    stderr_parts: list[str] = []
    last_code = 0
    for cmd in commands:
        if runner is not None:
            code = int(runner(cmd, cwd=str(project_root)))
        else:
            proc = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )
            code = proc.returncode
            if proc.stderr:
                stderr_parts.append(proc.stderr)
        if code != 0:
            tail = "\n".join(stderr_parts)[-2000:] if stderr_parts else None
            return code, tail
    tail = "\n".join(stderr_parts)[-2000:] if stderr_parts else None
    return 0, tail


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
) -> None:
    manifest["completed_steps"][candidate_id] = manifest_step_record(step)
    manifest["last_completed_candidate_id"] = candidate_id
    write_factory_manifest(manifest, output_dir)


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

    steps: list[dict[str, Any]] = []
    summary = _empty_summary()
    warnings: list[str] = []
    python_exe = sys.executable
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
                manifest, output_dir=manifest_dir, candidate_id=candidate_id, step=step
            )
            if fail_fast:
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
                manifest, output_dir=manifest_dir, candidate_id=candidate_id, step=step
            )
            if fail_fast:
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
                _persist_manifest_step(
                    manifest,
                    output_dir=manifest_dir,
                    candidate_id=candidate_id,
                    step=step,
                )
                continue

        if skip_existing and not force and snapshot_path.is_file():
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
                manifest, output_dir=manifest_dir, candidate_id=candidate_id, step=step
            )
            continue

        t0 = time.perf_counter()
        exit_code, stderr_tail = _run_subprocess_chain(
            commands, project_root=project_root, runner=runner
        )
        duration = round(time.perf_counter() - t0, 3)

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
            _append_factory_step(
                steps,
                step,
                candidate_id=candidate_id,
                project_root=project_root,
                output_dir_final=output_dir_final,
            )
            _increment_summary(summary, "failed")
            _persist_manifest_step(
                manifest, output_dir=manifest_dir, candidate_id=candidate_id, step=step
            )
            if fail_fast:
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
                manifest, output_dir=manifest_dir, candidate_id=candidate_id, step=step
            )
            if fail_fast:
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
                manifest, output_dir=manifest_dir, candidate_id=candidate_id, step=step
            )
            if fail_fast:
                break
            continue

        step = {
            "candidate_id": candidate_id,
            "display_name": row["display_name"],
            "role": row["role"],
            "artifact_root": artifact_root,
            "status": "succeeded",
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
            manifest, output_dir=manifest_dir, candidate_id=candidate_id, step=step
        )

    manifest_path = write_factory_manifest(manifest, manifest_dir)
    doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
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
    step: dict[str, Any] = {
        "candidate_id": candidate_id,
        "display_name": display_name,
        "role": role,
        "artifact_root": artifact_root,
        "status": status,
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


def build_factory_run_txt(doc: dict[str, Any]) -> str:
    lines = [
        "Candidate Portfolio Factory Run",
        f"Profile: {doc.get('factory_profile_id')}",
        f"Generated: {doc.get('generated_at')}",
        "",
    ]
    summary = doc.get("summary") or {}
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
    txt_path.write_text(build_factory_run_txt(doc), encoding="utf-8")
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
) -> tuple[dict[str, Path] | None, str | None]:
    from src.candidate_comparison import write_candidate_comparison_outputs

    try:
        paths = write_candidate_comparison_outputs(cfg, project_root=project_root)
        return paths, None
    except Exception as exc:  # noqa: BLE001 — surface comparison failure in factory summary
        return None, str(exc)
