"""
Session 6 benchmark smoke for Site/API Default Output Refactor ExecPlan.

Runs core_benchmarks factory with default site_api output policy in an isolated
project_root under tmp/ so repository portfolio folders are not refreshed.
Collects wall-clock timing, per-stage timing when available, artifact counts by
type, required JSON presence, and presentation-artifact absence checks.

Writes tmp/site_api_session06/session06_benchmark_summary.json.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
tests_root = REPO_ROOT / "tests"
if str(tests_root) not in sys.path:
    sys.path.insert(0, str(tests_root))

from mvp_offline_fixtures import MVP_DECISION_PACKAGE_ARTIFACTS
from src.candidate_comparison import _REGISTRY_ROWS
from src.candidate_factory import (
    run_candidate_factory,
    run_then_compare,
    write_candidate_factory_outputs,
)
from src.config import load_validated_config
from src.output_policy import (
    OUTPUT_PROFILE_SITE_API,
    artifact_counts_by_type,
    output_policy_for_profile,
)
from src.variant_builder_runtime import load_builder_runtime_timing

PRESENTATION_KEYS = (
    "csv",
    "txt",
    "html",
    "png",
    "pdf",
    "markdown_pdf_sidecars",
    "css_visual_assets",
)

BASELINE_REPORT_SECONDS_SUM = 208.671  # 2026-05-22 core_benchmarks x2, standard, pdf none

CANDIDATE_REQUIRED_JSON = (
    "snapshot_10y.json",
    "stress_report.json",
    "output_manifest.json",
)

FACTORY_REQUIRED_JSON = (
    "candidate_factory_run.json",
    "output_manifest.json",
)


def _artifact_root_for(candidate_id: str) -> str | None:
    for row in _REGISTRY_ROWS:
        if row.get("candidate_id") == candidate_id:
            return row.get("artifact_root")
    return None


def _check_required_json(root: Path, relative_paths: tuple[str, ...]) -> dict[str, bool]:
    return {name: (root / name).is_file() for name in relative_paths}


def _check_decision_package(main_dir: Path) -> dict[str, Any]:
    present: dict[str, bool] = {}
    schema_ok: dict[str, bool] = {}
    for filename, schema_version in MVP_DECISION_PACKAGE_ARTIFACTS:
        path = main_dir / filename
        present[filename] = path.is_file()
        if path.is_file():
            doc = json.loads(path.read_text(encoding="utf-8"))
            schema_ok[filename] = doc.get("schema_version") == schema_version
        else:
            schema_ok[filename] = False
    return {
        "present": present,
        "schema_ok": schema_ok,
        "all_present": all(present.values()),
        "all_schema_ok": all(schema_ok.values()),
    }


def _presentation_absent(counts: dict[str, int]) -> tuple[bool, dict[str, int]]:
    violations = {key: counts[key] for key in PRESENTATION_KEYS if counts[key] > 0}
    return len(violations) == 0, violations


def main() -> int:
    repo_root = REPO_ROOT
    out_dir = repo_root / "tmp" / "site_api_session06"
    project_root = out_dir / "benchmark"
    project_root.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "session06_benchmark.log"

    src_config = repo_root / "config.yml"
    dst_config = project_root / "config.yml"
    shutil.copy2(src_config, dst_config)

    cfg = load_validated_config(dst_config)
    main_dir = project_root / str(cfg.output_dir_final)
    output_profile = OUTPUT_PROFILE_SITE_API
    policy = output_policy_for_profile(output_profile)

    started = time.perf_counter()
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n--- benchmark started {datetime.now(timezone.utc).isoformat()} ---\n")
        log.flush()
        doc = run_candidate_factory(
            cfg,
            project_root=project_root,
            profile_id="core_benchmarks",
            explicit_candidates=["equal_weight", "risk_parity"],
            skip_existing=False,
            force=True,
            fail_fast=False,
            execution_mode="standard",
            pdf_mode="none",
            output_profile=output_profile,
            full_candidate_reports=False,
            parallel_lightweight_reports=False,
        )
        doc["options"]["then_compare"] = True
        write_candidate_factory_outputs(
            doc,
            output_dir=main_dir,
            write_txt=policy.write_txt,
        )
        compare_paths, compare_err = run_then_compare(
            cfg,
            project_root=project_root,
            factory_run=doc,
            output_profile=output_profile,
        )
        log.write(f"run_status={doc.get('run_status')}\n")
        if compare_err:
            log.write(f"comparison_error={compare_err}\n")
        elif compare_paths:
            doc["comparison_outputs"] = {k: str(v) for k, v in compare_paths.items()}
            write_candidate_factory_outputs(
                doc,
                output_dir=main_dir,
                write_txt=policy.write_txt,
            )
        log.flush()

    wall = time.perf_counter() - started
    timing = doc.get("timing_summary") or {}
    report_seconds = float(timing.get("report_seconds") or 0.0)

    steps = doc.get("steps") or []
    per_candidate: list[dict[str, Any]] = []
    for step in steps:
        cid = str(step.get("candidate_id") or "")
        artifact_root = _artifact_root_for(cid)
        candidate_dir = project_root / artifact_root if artifact_root else None
        candidate_counts = artifact_counts_by_type(candidate_dir) if candidate_dir else {}
        absent, violations = _presentation_absent(candidate_counts)
        timing_doc = (
            load_builder_runtime_timing(candidate_dir)
            if candidate_dir and candidate_dir.is_dir()
            else None
        )
        per_candidate.append(
            {
                "candidate_id": cid,
                "status": step.get("status"),
                "report_profile": step.get("report_profile"),
                "artifact_root": artifact_root,
                "report_seconds": (timing_doc or {}).get("report_seconds"),
                "artifact_counts_by_type": candidate_counts,
                "presentation_artifacts_absent": absent,
                "presentation_violations": violations,
                "required_json": _check_required_json(
                    candidate_dir, CANDIDATE_REQUIRED_JSON
                )
                if candidate_dir
                else {},
            }
        )

    project_counts = artifact_counts_by_type(project_root)
    project_absent, project_violations = _presentation_absent(project_counts)
    main_counts = artifact_counts_by_type(main_dir)
    main_absent, main_violations = _presentation_absent(main_counts)

    decision_package = _check_decision_package(main_dir) if main_dir.is_dir() else {}

    summary: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exec_plan": "docs/exec_plans/2026-05-23_site_api_default_output_refactor_plan.md",
        "session": 6,
        "project_root": str(project_root),
        "output_profile": output_profile,
        "factory_profile_id": "core_benchmarks",
        "candidate_ids": ["equal_weight", "risk_parity"],
        "execution_mode": "standard",
        "pdf_mode": "none",
        "then_compare": True,
        "run_status": doc.get("run_status"),
        "summary": doc.get("summary"),
        "wall_clock_seconds": round(wall, 3),
        "timing_summary": timing,
        "baseline_report_seconds_sum": BASELINE_REPORT_SECONDS_SUM,
        "report_seconds_delta_pct": round(
            (report_seconds / BASELINE_REPORT_SECONDS_SUM - 1.0) * 100.0, 2
        )
        if BASELINE_REPORT_SECONDS_SUM > 0
        else None,
        "comparison_error": compare_err,
        "comparison_outputs": {k: str(v) for k, v in (compare_paths or {}).items()},
        "artifact_counts_by_type": {
            "project_root": project_counts,
            "main_portfolio": main_counts,
        },
        "presentation_artifacts_absent": {
            "project_root": project_absent,
            "main_portfolio": main_absent,
        },
        "presentation_violations": {
            "project_root": project_violations,
            "main_portfolio": main_violations,
        },
        "required_json": {
            "factory": _check_required_json(main_dir, FACTORY_REQUIRED_JSON),
            "decision_package": decision_package,
        },
        "disabled_artifact_classes": policy.disabled_artifact_classes,
        "per_candidate": per_candidate,
        "acceptance": {
            "presentation_absent_project_root": project_absent,
            "presentation_absent_main_portfolio": main_absent,
            "all_candidates_presentation_absent": all(
                row.get("presentation_artifacts_absent") for row in per_candidate
            ),
            "factory_json_present": all(
                _check_required_json(main_dir, FACTORY_REQUIRED_JSON).values()
            ),
            "decision_package_complete": decision_package.get("all_present", False),
            "decision_package_schema_ok": decision_package.get("all_schema_ok", False),
            "comparison_succeeded": compare_err is None,
        },
    }

    all_ok = all(summary["acceptance"].values())
    summary["acceptance"]["all_passed"] = all_ok

    summary_path = out_dir / "session06_benchmark_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
