"""
Candidate Portfolio Factory orchestration.

See docs/specs/candidate_factory_spec.md.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.candidate_comparison import _REGISTRY_ROWS, candidate_registry_ids
from src.config_schema import PortfolioConfig

SCHEMA_VERSION = "candidate_factory_run_v1"
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

ROBUST_SCENARIO_PREREQUISITES = (
    "scenario_library_normalized.json",
    "stress_report.json",
)


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
) -> tuple[str, str | None]:
    if not snapshot_path.is_file():
        return "missing", None
    snapshot_end = _snapshot_analysis_end(snapshot_path)
    if not expected_analysis_end:
        return "unchecked", snapshot_end
    if snapshot_end == expected_analysis_end:
        return "fresh", snapshot_end
    return "stale", snapshot_end


def _robust_scenario_prerequisites_met(project_root: Path, output_dir_final: str) -> bool:
    final_dir = project_root / output_dir_final
    return all((final_dir / name).is_file() for name in ROBUST_SCENARIO_PREREQUISITES)


def _command_strings(commands: list[list[str]]) -> list[str]:
    return [" ".join(cmd) for cmd in commands]


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
    }


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
            steps.append(step)
            _increment_summary(summary, "failed")
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
            steps.append(step)
            _increment_summary(summary, "failed")
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

        if skip_existing and not force and snapshot_path.is_file():
            freshness, snapshot_end = _snapshot_freshness(
                snapshot_path,
                expected_analysis_end=analysis_end,
            )
            if freshness in ("fresh", "unchecked"):
                message = "snapshot_10y.json already present; step skipped."
                if freshness == "unchecked":
                    message = (
                        "snapshot_10y.json already present; step skipped, but review "
                        "analysis_end was unavailable so freshness could not be certified."
                    )
                    warnings.append("candidate_freshness_unchecked_no_review_analysis_end")
                step = _failed_step(
                    candidate_id=candidate_id,
                    display_name=row["display_name"],
                    role=row["role"],
                    artifact_root=artifact_root,
                    status="skipped_existing",
                    reason_code="skipped_existing",
                    message=message,
                    entry_commands=entry_commands,
                    exit_code=None,
                    duration_seconds=0.0,
                    expected_analysis_end=analysis_end,
                    snapshot_analysis_end=snapshot_end,
                    freshness_status=freshness,
                )
                steps.append(step)
                _increment_summary(summary, "skipped_existing")
                continue
            warnings.append(
                f"stale_candidate_snapshot_rebuild_attempted:{candidate_id}:"
                f"{snapshot_end or 'missing_analysis_end'}!={analysis_end}"
            )

        if candidate_id == "robust_scenario" and not _robust_scenario_prerequisites_met(
            project_root, output_dir_final
        ):
            step = _failed_step(
                candidate_id=candidate_id,
                display_name=row["display_name"],
                role=row["role"],
                artifact_root=artifact_root,
                status="skipped_dependency",
                reason_code="skipped_dependency",
                message=(
                    "Missing scenario_library_normalized.json or stress_report.json "
                    f"under {output_dir_final}; run policy report first."
                ),
                entry_commands=entry_commands,
                exit_code=None,
                duration_seconds=0.0,
            )
            steps.append(step)
            _increment_summary(summary, "skipped_dependency")
            continue

        t0 = time.perf_counter()
        exit_code, stderr_tail = _run_subprocess_chain(
            commands, project_root=project_root, runner=runner
        )
        duration = round(time.perf_counter() - t0, 3)

        if exit_code != 0:
            message = "Builder subprocess returned non-zero exit."
            if stderr_tail:
                message = f"{message} stderr tail: {stderr_tail}"
            step = _failed_step(
                candidate_id=candidate_id,
                display_name=row["display_name"],
                role=row["role"],
                artifact_root=artifact_root,
                status="failed",
                reason_code="subprocess_failed",
                message=message,
                entry_commands=entry_commands,
                exit_code=exit_code,
                duration_seconds=duration,
            )
            steps.append(step)
            _increment_summary(summary, "failed")
            if fail_fast:
                break
            continue

        if not snapshot_path.is_file():
            step = _failed_step(
                candidate_id=candidate_id,
                display_name=row["display_name"],
                role=row["role"],
                artifact_root=artifact_root,
                status="failed",
                reason_code="missing_snapshot_after_build",
                message=f"{SNAPSHOT_MINIMUM} missing after successful builder exit.",
                entry_commands=entry_commands,
                exit_code=exit_code,
                duration_seconds=duration,
                expected_analysis_end=analysis_end,
                snapshot_analysis_end=None,
                freshness_status="missing",
            )
            steps.append(step)
            _increment_summary(summary, "failed")
            if fail_fast:
                break
            continue

        freshness, snapshot_end = _snapshot_freshness(
            snapshot_path,
            expected_analysis_end=analysis_end,
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
            )
            steps.append(step)
            _increment_summary(summary, "failed")
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
        }
        steps.append(step)
        _increment_summary(summary, "succeeded")
        if freshness == "fresh" and any(
            w.startswith(f"stale_candidate_snapshot_rebuild_attempted:{candidate_id}:")
            for w in warnings
        ):
            summary["rebuilt_stale"] += 1

    doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "factory_profile_id": profile_id if explicit_candidates is None else "explicit_list",
        "project_root": str(project_root),
        "output_dir_final": output_dir_final,
        "config_path": str(config_path) if config_path else "config.yml",
        "analysis_end": analysis_end,
        "options": {
            "skip_existing": skip_existing,
            "force": force,
            "fail_fast": fail_fast,
            "then_compare": False,
        },
        "steps": steps,
        "summary": summary,
        "warnings": warnings,
        "next_recommended_command": "python run_compare_variants.py",
    }
    return doc


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
) -> dict[str, Any]:
    return {
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
    }


class FactoryValidationError(Exception):
    """Registry/profile validation failed before any builder runs."""


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
        f"rebuilt_stale={summary.get('rebuilt_stale', 0)}"
    )
    failed_ids = [
        s["candidate_id"]
        for s in doc.get("steps") or []
        if s.get("status") == "failed"
    ]
    if failed_ids:
        lines.append(f"Failed candidates: {', '.join(failed_ids)}")
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
    lines.append(f"Next: {doc.get('next_recommended_command')}")
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
    return {"candidate_factory_run_json": json_path, "candidate_factory_run_txt": txt_path}


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
