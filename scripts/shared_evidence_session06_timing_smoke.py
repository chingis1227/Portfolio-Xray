"""
Session 6 timing smoke for Candidate Factory Shared Evidence ExecPlan.

Runs a full default_v1 sequential standard lightweight-report factory in an isolated
project_root under tmp/ so repository portfolio folders are not refreshed.
Writes tmp/candidate_shared_evidence_session06/session06_smoke_summary.json.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.candidate_comparison import _REGISTRY_ROWS
from src.candidate_factory import run_candidate_factory
from src.config import load_validated_config
from src.variant_builder_runtime import load_builder_runtime_timing


def _artifact_root_for(candidate_id: str) -> str | None:
    for row in _REGISTRY_ROWS:
        if row.get("candidate_id") == candidate_id:
            return row.get("artifact_root")
    return None

BASELINE_REPORT_SECONDS_SUM = 1192.941
TARGET_IMPROVEMENT_PCT = 35.0


def main() -> int:
    repo_root = REPO_ROOT
    out_dir = repo_root / "tmp" / "candidate_shared_evidence_session06"
    project_root = out_dir / "sequential"
    project_root.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "session06_smoke.log"

    src_config = repo_root / "config.yml"
    dst_config = project_root / "config.yml"
    shutil.copy2(src_config, dst_config)

    cfg = load_validated_config(dst_config)
    started = time.perf_counter()
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n--- smoke started {datetime.now(timezone.utc).isoformat()} ---\n")
        log.flush()
        doc = run_candidate_factory(
            cfg,
            project_root=project_root,
            profile_id="default_v1",
            skip_existing=False,
            force=True,
            fail_fast=False,
            execution_mode="standard",
            pdf_mode="none",
            full_candidate_reports=False,
            parallel_lightweight_reports=False,
        )
        log.write(f"run_status={doc.get('run_status')}\n")
        log.flush()

    wall = time.perf_counter() - started
    timing = doc.get("timing_summary") or {}
    report_seconds = float(timing.get("report_seconds") or 0.0)
    improvement_pct = (
        (1.0 - report_seconds / BASELINE_REPORT_SECONDS_SUM) * 100.0
        if BASELINE_REPORT_SECONDS_SUM > 0
        else 0.0
    )
    meets_target = improvement_pct >= TARGET_IMPROVEMENT_PCT

    steps = doc.get("steps") or []
    per_candidate = []
    for step in steps:
        cid = step.get("candidate_id")
        report_seconds_val = None
        artifact_root = _artifact_root_for(str(cid or ""))
        if artifact_root:
            timing_doc = load_builder_runtime_timing(project_root / artifact_root)
            if timing_doc:
                report_seconds_val = timing_doc.get("report_seconds")
        per_candidate.append(
            {
                "candidate_id": cid,
                "status": step.get("status"),
                "report_seconds": report_seconds_val,
                "report_profile": step.get("report_profile"),
            }
        )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "profile_id": "default_v1",
        "execution_mode": "standard",
        "parallel_lightweight_reports": False,
        "run_status": doc.get("run_status"),
        "summary": doc.get("summary"),
        "wall_clock_seconds": round(wall, 3),
        "timing_summary": timing,
        "baseline_report_seconds_sum": BASELINE_REPORT_SECONDS_SUM,
        "target_improvement_pct": TARGET_IMPROVEMENT_PCT,
        "observed_improvement_pct": round(improvement_pct, 2),
        "meets_timing_target": meets_target,
        "per_candidate": per_candidate,
    }
    summary_path = out_dir / "session06_smoke_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if meets_target else 2


if __name__ == "__main__":
    raise SystemExit(main())
