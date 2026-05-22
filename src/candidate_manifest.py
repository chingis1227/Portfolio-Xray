"""
Per-candidate readiness manifest for the Candidate Portfolio Factory.

Orchestration only: records factory step outcome and artifact presence for comparison.
Does not change metrics, weights, or comparison formulas.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANDIDATE_MANIFEST_FILENAME = "candidate_manifest.json"
CANDIDATE_MANIFEST_SCHEMA = "candidate_manifest_v1"

SNAPSHOT_MINIMUM = "snapshot_10y.json"
STEP_STATUSES_SUCCESS = frozenset({"succeeded", "skipped_existing"})
STEP_STATUSES_INTENTIONAL_SKIP = frozenset({"skipped_dependency", "skipped_profile"})

RUN_STATUS_FULL_SUCCESS = "full_success"
RUN_STATUS_PARTIAL_SUCCESS = "partial_success"
RUN_STATUS_ALL_FAILED = "all_failed"
RUN_STATUS_ABORTED_FAIL_FAST = "aborted_fail_fast"


def _artifact_flags(artifact_dir: Path) -> dict[str, bool]:
    return {
        "weights_present": (artifact_dir / "weights.json").is_file(),
        "snapshot_10y_present": (artifact_dir / SNAPSHOT_MINIMUM).is_file(),
        "stress_report_present": (artifact_dir / "stress_report.json").is_file(),
        "summary_present": (artifact_dir / "summary.json").is_file(),
        "weights_build_present": (artifact_dir / "candidate_weights_build.json").is_file(),
    }


def _comparison_readiness_status(
    *,
    step_status: str,
    flags: dict[str, bool],
    phases_completed: list[str] | None,
) -> tuple[str, bool]:
    """Return (readiness_status, ready_for_comparison)."""
    if step_status in STEP_STATUSES_INTENTIONAL_SKIP:
        return "skipped_dependency", False
    if step_status == "failed":
        if flags.get("snapshot_10y_present"):
            return "stale_or_invalid", False
        if flags.get("weights_present"):
            return "weights_only", False
        return "not_ready", False
    if step_status in STEP_STATUSES_SUCCESS and flags.get("snapshot_10y_present"):
        return "ready", True
    if flags.get("weights_present"):
        return "weights_only", False
    return "not_ready", False


def _partial_failure_block(
    *,
    step: dict[str, Any],
    phases_completed: list[str] | None,
    flags: dict[str, bool],
) -> dict[str, Any] | None:
    if step.get("status") != "failed":
        return None
    phases = list(phases_completed or [])
    weights_ok = flags.get("weights_present") or "weights" in phases
    report_failed = (
        "report" in phases
        or step.get("execution_action", "").startswith("lightweight_report")
        or step.get("execution_action") == "builder_invoked_failed"
    )
    if weights_ok and not flags.get("snapshot_10y_present") and report_failed:
        return {
            "weights_phase": "succeeded" if flags.get("weights_present") else "unknown",
            "report_phase": "failed",
            "reason_code": step.get("reason_code"),
            "message": step.get("message"),
        }
    if phases == ["weights"] and step.get("execution_action") == "weights_built_failed":
        return {
            "weights_phase": "failed",
            "report_phase": "not_started",
            "reason_code": step.get("reason_code"),
            "message": step.get("message"),
        }
    return None


def build_candidate_manifest(
    step: dict[str, Any],
    *,
    artifact_dir: Path | None = None,
) -> dict[str, Any]:
    """Build ``candidate_manifest_v1`` from a factory step record."""
    artifact_root = str(step.get("artifact_root") or "")
    phases = list(step.get("phases_completed") or [])
    flags: dict[str, bool] = {}
    if artifact_dir is not None and artifact_dir.is_dir():
        flags = _artifact_flags(artifact_dir)
    step_status = str(step.get("status") or "failed")
    readiness_status, ready = _comparison_readiness_status(
        step_status=step_status,
        flags=flags,
        phases_completed=phases,
    )
    manifest: dict[str, Any] = {
        "schema_version": CANDIDATE_MANIFEST_SCHEMA,
        "candidate_id": step.get("candidate_id"),
        "display_name": step.get("display_name"),
        "role": step.get("role"),
        "artifact_root": artifact_root,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "factory_step": {
            "status": step_status,
            "execution_action": step.get("execution_action"),
            "reason_code": step.get("reason_code"),
            "message": step.get("message"),
            "phases_completed": phases,
            "report_profile": step.get("report_profile"),
            "duration_seconds": step.get("duration_seconds"),
        },
        "review_context": {
            "expected_analysis_end": step.get("expected_analysis_end"),
            "expected_config_fingerprint": step.get("expected_config_fingerprint"),
            "snapshot_analysis_end": step.get("snapshot_analysis_end"),
            "snapshot_config_fingerprint": step.get("snapshot_config_fingerprint"),
            "freshness_status": step.get("freshness_status"),
        },
        "artifacts": flags,
        "comparison_readiness": {
            "status": readiness_status,
            "ready_for_comparison": ready,
            **flags,
        },
    }
    partial = _partial_failure_block(
        step=step,
        phases_completed=phases,
        flags=flags,
    )
    if partial is not None:
        manifest["partial_failure"] = partial
    return manifest


def write_candidate_manifest(
    artifact_dir: Path,
    step: dict[str, Any],
) -> Path | None:
    """Write ``candidate_manifest.json`` under the candidate artifact folder."""
    if not artifact_dir or not str(step.get("artifact_root") or "").strip():
        return None
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_candidate_manifest(step, artifact_dir=artifact_dir)
    path = artifact_dir / CANDIDATE_MANIFEST_FILENAME
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return path


def load_candidate_manifest(artifact_dir: Path) -> dict[str, Any] | None:
    path = artifact_dir / CANDIDATE_MANIFEST_FILENAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or data.get("schema_version") != CANDIDATE_MANIFEST_SCHEMA:
        return None
    return data


def compute_factory_run_status(
    summary: dict[str, int],
    *,
    fail_fast: bool,
    fail_fast_aborted: bool,
) -> str:
    """
    Run-level outcome for partial-failure disclosure.

    - ``full_success``: no failed steps
    - ``partial_success``: mix of successes/skips and failures
    - ``all_failed``: every counted step failed (no success, no skip-existing)
    - ``aborted_fail_fast``: loop stopped early on first failure with ``--fail-fast``
    """
    failed = int(summary.get("failed") or 0)
    succeeded = int(summary.get("succeeded") or 0)
    skipped_existing = int(summary.get("skipped_existing") or 0)
    skipped_dependency = int(summary.get("skipped_dependency") or 0)

    if fail_fast and fail_fast_aborted and failed > 0:
        return RUN_STATUS_ABORTED_FAIL_FAST
    if failed == 0:
        return RUN_STATUS_FULL_SUCCESS
    productive = succeeded + skipped_existing
    if productive > 0:
        return RUN_STATUS_PARTIAL_SUCCESS
    if failed > 0 and skipped_dependency > 0 and succeeded == 0 and skipped_existing == 0:
        return RUN_STATUS_PARTIAL_SUCCESS
    if failed > 0:
        return RUN_STATUS_ALL_FAILED
    return RUN_STATUS_FULL_SUCCESS
