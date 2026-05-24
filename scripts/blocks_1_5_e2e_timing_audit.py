"""
End-to-end Blocks 1-5 timing audit (site_api / portfolio-first path).

Runs in an isolated project_root under tmp/ so repository portfolio folders are
not refreshed. Measures wall-clock per major stage, factory timing_summary,
report_timing_aggregate, PDF absence, and decision-package presence.

Scenarios:
  - default_core: legacy core_v1 sequential (Session 0 baseline)
  - core_fast_parallel: Session 7 core_fast path (ReviewRunContext + parallel)
  - full_menu_reference: default_v1 sequential (full menu regression)

Writes tmp/blocks_1_5_timing_audit/{scenario}_summary.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from dataclasses import dataclass
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
from run_report import (
    resolve_analysis_subject_materialization,
    run_materialize_analysis_subject_report,
    run_portfolio_report_for_weights,
)
from src.candidate_comparison import _REGISTRY_ROWS
from src.candidate_factory import (
    CORE_FAST_PROFILE_ID,
    run_candidate_factory,
    run_then_compare,
    write_candidate_factory_outputs,
)
from src.candidate_run_context import ReviewRunContext, prepare_review_run_context
from src.config import load_validated_config
from src.output_policy import (
    OUTPUT_PROFILE_SITE_API,
    artifact_counts_by_type,
    output_policy_for_profile,
)
from src.io_export import ensure_output_dir
from src.variant_builder_runtime import load_builder_runtime_timing

CORE_FAST_E2E_TARGET_SECONDS = 300.0
SESSION0_CORE_V1_BASELINE_SECONDS = 542.5

PRESENTATION_KEYS = ("csv", "txt", "html", "png", "pdf", "markdown_pdf_sidecars", "css_visual_assets")

CANDIDATE_REQUIRED_JSON = ("snapshot_10y.json", "stress_report.json", "output_manifest.json")

PRIOR_BASELINES = {
    "legacy_full_report_pdf_per_candidate_s": 228.0,
    "legacy_16_candidate_minutes": 57.0,
    "parallel_16_candidate_wall_s": 631.117,
    "shared_evidence_sequential_report_s": 857.712,
    "shared_evidence_sequential_wall_s": 877.078,
    "site_api_core2_report_s": 155.0,
    "site_api_core2_wall_s": 171.6,
}


def _artifact_root_for(candidate_id: str) -> str | None:
    for row in _REGISTRY_ROWS:
        if row.get("candidate_id") == candidate_id:
            return row.get("artifact_root")
    return None


def _presentation_absent(counts: dict[str, int]) -> tuple[bool, dict[str, int]]:
    violations = {key: counts[key] for key in PRESENTATION_KEYS if counts.get(key, 0) > 0}
    return len(violations) == 0, violations


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
        "all_present": all(present.values()),
        "all_schema_ok": all(schema_ok.values()),
    }


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_id: str
    review_mode: str
    factory_profile: str
    use_core_fast_path: bool = False


def _evaluate_core_fast_acceptance(summary: dict[str, Any]) -> dict[str, Any]:
    total = float(summary.get("total_wall_clock_seconds") or 0.0)
    target = CORE_FAST_E2E_TARGET_SECONDS
    gap = round(total - target, 3)
    timing_summary = (
        (summary.get("stages") or {}).get("candidate_factory") or {}
    ).get("timing_summary") or {}
    pdf_factory = timing_summary.get("pdf_seconds")
    pdf_sum = summary.get("per_candidate_pdf_seconds_sum")
    decision = summary.get("decision_package") or {}
    stages = summary.get("stages") or {}
    def _budget_miss(stage: str, measured: float, budget: float) -> dict[str, Any]:
        return {
            "stage": stage,
            "measured_seconds": measured,
            "budget_seconds": budget,
            "remaining_seconds_to_target": round(measured - budget, 3),
        }

    budget_notes: list[dict[str, Any]] = []
    subject_wall = float(
        (stages.get("analysis_subject_materialization") or {}).get("wall_clock_seconds") or 0.0
    )
    if subject_wall > 60.0:
        budget_notes.append(_budget_miss("analysis_subject_materialization", subject_wall, 60.0))
    factory_wall = float((stages.get("candidate_factory") or {}).get("wall_clock_seconds") or 0.0)
    if factory_wall > 230.0:
        budget_notes.append(_budget_miss("candidate_factory", factory_wall, 230.0))

    meets_target = total <= target
    blockers: list[dict[str, Any]] = []
    if not meets_target:
        blockers.append(_budget_miss("total_e2e", total, target))
        blockers.extend(budget_notes)

    return {
        "target_seconds": target,
        "measured_seconds": total,
        "gap_seconds": gap,
        "meets_target": meets_target,
        "baseline_core_v1_seconds": SESSION0_CORE_V1_BASELINE_SECONDS,
        "savings_vs_baseline_seconds": round(SESSION0_CORE_V1_BASELINE_SECONDS - total, 3),
        "pdf_seconds_factory": pdf_factory,
        "pdf_seconds_per_candidate_sum": pdf_sum,
        "pdf_absent": (pdf_factory in (0, 0.0, None)) and (pdf_sum in (0, 0.0, None)),
        "decision_package_all_present": bool(decision.get("all_present")),
        "decision_package_all_schema_ok": bool(decision.get("all_schema_ok")),
        "stage_budget_notes": budget_notes,
        "blockers": blockers,
    }


def run_scenario(
    *,
    repo_root: Path,
    scenario_id: str,
    review_mode: str,
    factory_profile: str,
    out_dir: Path,
    use_core_fast_path: bool = False,
) -> dict[str, Any]:
    project_root = out_dir / scenario_id
    if project_root.exists():
        shutil.rmtree(project_root)
    project_root.mkdir(parents=True, exist_ok=True)

    shutil.copy2(repo_root / "config.yml", project_root / "config.yml")
    cfg = load_validated_config(project_root / "config.yml")
    main_dir = project_root / str(cfg.output_dir_final)
    output_profile = OUTPUT_PROFILE_SITE_API
    policy = output_policy_for_profile(output_profile)
    run_timestamp = datetime.now(timezone.utc).isoformat()

    stages: dict[str, Any] = {}
    total_started = time.perf_counter()

    # --- Stage 1: analysis_subject materialization (Block 1-2 entry) ---
    config_load_started = time.perf_counter()
    materialization = resolve_analysis_subject_materialization(cfg)
    stages["input_validation"] = {
        "wall_clock_seconds": round(time.perf_counter() - config_load_started, 3),
        "status": materialization.get("status"),
    }
    if materialization["status"] != "resolved":
        raise RuntimeError(f"analysis_subject not resolved: {materialization}")

    shared_context: ReviewRunContext | None = None
    parallel_lightweight_reports: bool | None = False
    if use_core_fast_path:
        if factory_profile != CORE_FAST_PROFILE_ID:
            raise ValueError(
                f"use_core_fast_path requires factory_profile={CORE_FAST_PROFILE_ID!r}, "
                f"got {factory_profile!r}"
            )
        prep_started = time.perf_counter()
        shared_context = prepare_review_run_context(cfg, project_root=project_root, no_cache=False)
        stages["prepare_review_run_context"] = {
            "wall_clock_seconds": round(time.perf_counter() - prep_started, 3),
        }
        parallel_lightweight_reports = None

    subject_started = time.perf_counter()
    if use_core_fast_path:
        shared_context = run_materialize_analysis_subject_report(
            cfg,
            run_timestamp=run_timestamp,
            backtest_mode="dynamic_nan_safe",
            no_cache=False,
            output_profile=output_profile,
            review_run_context=shared_context,
            review_mode=review_mode,
            project_root=project_root,
            use_review_run_context=True,
        )
        subject_final = ensure_output_dir(main_dir / "analysis_subject")
        subject_meta: dict[str, Any] = {
            "report_profile": "lightweight_comparison",
            "review_run_context": True,
        }
    else:
        subject_final = ensure_output_dir(main_dir / "analysis_subject")
        subject_csv = subject_final / "results_csv"
        _metrics, subject_meta = run_portfolio_report_for_weights(
            cfg,
            materialization["weights"],
            run_timestamp=run_timestamp,
            output_dir_csv=subject_csv,
            output_dir_final=subject_final,
            backtest_mode_override="dynamic_nan_safe",
            no_cache=False,
            weights_source=str(materialization["weights_source"] or "analysis_subject"),
            portfolio_role_override="analysis_subject",
            output_profile=output_profile,
            enable_report_timing=True,
        )
    stages["analysis_subject_materialization"] = {
        "wall_clock_seconds": round(time.perf_counter() - subject_started, 3),
        "report_timing": subject_meta.get("report_timing"),
        "artifact_root": str(subject_final.relative_to(project_root)),
        "report_profile": subject_meta.get("report_profile"),
        "review_run_context": subject_meta.get("review_run_context"),
    }

    # --- Stage 2: candidate factory (Blocks 4-5 weights + lightweight reports) ---
    factory_started = time.perf_counter()
    doc = run_candidate_factory(
        cfg,
        project_root=project_root,
        profile_id=factory_profile,
        skip_existing=False,
        force=True,
        fail_fast=False,
        execution_mode="standard",
        pdf_mode="none",
        output_profile=output_profile,
        full_candidate_reports=False,
        parallel_lightweight_reports=parallel_lightweight_reports,
        shared_run_context=shared_context if use_core_fast_path else None,
    )
    factory_wall = time.perf_counter() - factory_started
    timing_summary = doc.get("timing_summary") or {}

    stages["candidate_factory"] = {
        "wall_clock_seconds": round(factory_wall, 3),
        "run_status": doc.get("run_status"),
        "summary": doc.get("summary"),
        "timing_summary": timing_summary,
        "pdf_seconds_total": timing_summary.get("pdf_seconds"),
        "builder_core_seconds": timing_summary.get("builder_core_seconds"),
        "report_seconds": timing_summary.get("report_seconds"),
        "report_timing_aggregate": timing_summary.get("report_timing_aggregate"),
    }

    # --- Stage 3: comparison + decision package ---
    write_candidate_factory_outputs(
        doc,
        output_dir=main_dir,
        write_txt=policy.write_txt,
    )
    compare_started = time.perf_counter()
    compare_paths, compare_err = run_then_compare(
        cfg,
        project_root=project_root,
        factory_run=doc,
        output_profile=output_profile,
    )
    compare_wall = time.perf_counter() - compare_started
    if compare_paths:
        doc["comparison_outputs"] = {k: str(v) for k, v in compare_paths.items()}
        write_candidate_factory_outputs(
            doc,
            output_dir=main_dir,
            write_txt=policy.write_txt,
        )

    stages["candidate_comparison_and_decision_package"] = {
        "wall_clock_seconds": round(compare_wall, 3),
        "error": compare_err,
        "outputs": {k: str(v) for k, v in (compare_paths or {}).items()},
    }

    total_wall = time.perf_counter() - total_started

    # Per-candidate detail
    per_candidate: list[dict[str, Any]] = []
    pdf_total = 0.0
    for step in doc.get("steps") or []:
        cid = str(step.get("candidate_id") or "")
        artifact_root = _artifact_root_for(cid)
        candidate_dir = project_root / artifact_root if artifact_root else None
        timing_doc = (
            load_builder_runtime_timing(candidate_dir)
            if candidate_dir and candidate_dir.is_dir()
            else None
        )
        pdf_s = float((timing_doc or {}).get("pdf_seconds") or step.get("pdf_seconds") or 0.0)
        pdf_total += pdf_s
        counts = artifact_counts_by_type(candidate_dir) if candidate_dir else {}
        absent, violations = _presentation_absent(counts)
        per_candidate.append(
            {
                "candidate_id": cid,
                "status": step.get("status"),
                "report_profile": step.get("report_profile"),
                "report_seconds": (timing_doc or {}).get("report_seconds"),
                "pdf_seconds": pdf_s,
                "report_timing": step.get("report_timing"),
                "presentation_artifacts_absent": absent,
                "presentation_violations": violations,
            }
        )

    project_counts = artifact_counts_by_type(project_root)
    project_absent, project_violations = _presentation_absent(project_counts)
    decision_package = _check_decision_package(main_dir) if main_dir.is_dir() else {}

    # Percentage breakdown (measured stages only)
    stage_keys = (
        "input_validation",
        "prepare_review_run_context",
        "analysis_subject_materialization",
        "candidate_factory",
        "candidate_comparison_and_decision_package",
    )
    breakdown_pct: dict[str, float | None] = {}
    for key in stage_keys:
        wall = float((stages.get(key) or {}).get("wall_clock_seconds") or 0.0)
        breakdown_pct[key] = round(wall / total_wall * 100.0, 1) if total_wall > 0 else None

    parallel_summary = (doc.get("options") or {}).get("parallel_lightweight_report_summary")
    parallel_effective = (parallel_summary or {}).get("effective") if parallel_summary else None
    if parallel_effective is None:
        parallel_effective = bool(
            (doc.get("options") or {}).get("parallel_lightweight_reports_effective")
        )

    result: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario_id,
        "review_mode": review_mode,
        "factory_profile": factory_profile,
        "use_core_fast_path": use_core_fast_path,
        "output_profile": output_profile,
        "pdf_mode": "none",
        "execution_mode": "standard",
        "parallel_lightweight_reports": parallel_effective,
        "parallel_lightweight_report_summary": parallel_summary,
        "project_root": str(project_root),
        "total_wall_clock_seconds": round(total_wall, 3),
        "stages": stages,
        "stage_percentage_of_total": breakdown_pct,
        "per_candidate": per_candidate,
        "per_candidate_pdf_seconds_sum": round(pdf_total, 3),
        "artifact_counts_by_type_project_root": project_counts,
        "presentation_artifacts_absent": project_absent,
        "presentation_violations": project_violations,
        "decision_package": decision_package,
        "prior_baselines": PRIOR_BASELINES,
    }
    if use_core_fast_path:
        result["core_fast_acceptance"] = _evaluate_core_fast_acceptance(result)
    return result


DEFAULT_SCENARIOS: tuple[ScenarioSpec, ...] = (
    ScenarioSpec("default_core", "core", "core_v1", use_core_fast_path=False),
    ScenarioSpec(
        "core_fast_parallel",
        "core",
        CORE_FAST_PROFILE_ID,
        use_core_fast_path=True,
    ),
    ScenarioSpec("full_menu_reference", "full", "default_v1", use_core_fast_path=False),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Blocks 1-5 E2E timing audit")
    parser.add_argument(
        "--only",
        action="append",
        dest="only_scenarios",
        metavar="SCENARIO_ID",
        help="Run subset of scenarios (repeatable). Default: all.",
    )
    parser.add_argument(
        "--skip-legacy",
        action="store_true",
        help="Skip default_core and full_menu_reference (Session 8 gate: core_fast only).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    out_dir = REPO_ROOT / "tmp" / "blocks_1_5_timing_audit"
    out_dir.mkdir(parents=True, exist_ok=True)

    scenarios = list(DEFAULT_SCENARIOS)
    if args.skip_legacy:
        scenarios = [s for s in scenarios if s.use_core_fast_path]
    if args.only_scenarios:
        allowed = {s.strip() for s in args.only_scenarios}
        scenarios = [s for s in scenarios if s.scenario_id in allowed]
        unknown = allowed - {s.scenario_id for s in scenarios}
        if unknown:
            print(f"Unknown scenario id(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2

    results: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "core_fast_e2e_target_seconds": CORE_FAST_E2E_TARGET_SECONDS,
        "scenarios": {},
    }

    exit_code = 0
    for spec in scenarios:
        print(
            f"\n=== Running scenario: {spec.scenario_id} ({spec.factory_profile}) ===",
            flush=True,
        )
        summary = run_scenario(
            repo_root=REPO_ROOT,
            scenario_id=spec.scenario_id,
            review_mode=spec.review_mode,
            factory_profile=spec.factory_profile,
            out_dir=out_dir,
            use_core_fast_path=spec.use_core_fast_path,
        )
        path = out_dir / f"{spec.scenario_id}_summary.json"
        path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        results["scenarios"][spec.scenario_id] = summary
        print(f"Wrote {path}", flush=True)
        print(
            f"total_wall={summary['total_wall_clock_seconds']}s "
            f"pdf_sum={summary['per_candidate_pdf_seconds_sum']}s "
            f"parallel={summary.get('parallel_lightweight_reports')}",
            flush=True,
        )
        acceptance = summary.get("core_fast_acceptance")
        if acceptance:
            results["core_fast_acceptance"] = acceptance
            if acceptance.get("meets_target"):
                print(
                    f"ACCEPTANCE PASS: core_fast E2E {acceptance['measured_seconds']}s "
                    f"<= {acceptance['target_seconds']}s",
                    flush=True,
                )
            else:
                exit_code = 1
                print(
                    f"ACCEPTANCE FAIL: core_fast E2E {acceptance['measured_seconds']}s "
                    f"> {acceptance['target_seconds']}s (gap {acceptance['gap_seconds']}s)",
                    flush=True,
                )
                for blocker in acceptance.get("blockers") or []:
                    print(
                        f"  blocker {blocker.get('stage')}: "
                        f"{blocker.get('measured_seconds')}s "
                        f"(budget {blocker.get('budget_seconds')}s, "
                        f"+{blocker.get('remaining_seconds_to_target')}s)",
                        flush=True,
                    )

    combined_path = out_dir / "combined_summary.json"
    combined_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {combined_path}", flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
