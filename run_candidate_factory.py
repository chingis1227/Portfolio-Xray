from __future__ import annotations

"""
Candidate Portfolio Factory CLI.

Orchestrates existing per-candidate builder scripts without reimplementing formulas.
See docs/specs/candidate_factory_spec.md.
"""

import argparse
from pathlib import Path

from src.candidate_factory import (
    FactoryValidationError,
    build_factory_run_txt,
    factory_exit_code,
    profile_uses_review_run_context,
    run_candidate_factory,
    run_then_compare,
    write_candidate_factory_outputs,
)
from src.candidate_run_context import prepare_review_run_context
from src.config import load_validated_config
from src.config_schema import ConfigValidationError
from src.output_policy import OUTPUT_PROFILE_VALUES, output_policy_for_profile
from src.utils import logger, setup_logging


def _parse_candidates(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [part.strip() for part in raw.split(",") if part.strip()]


def _warn_standalone_full_menu_default(profile_id: str, explicit_candidates: list[str] | None) -> None:
    """Log when CLI runs the research full-menu profile without an explicit candidate list."""
    if explicit_candidates is not None:
        return
    if profile_id != "default_v1":
        return
    logger.warning(
        "Standalone factory default profile is default_v1 (full research menu, 16 builders). "
        "This is not the Core MVP product entry. Prefer: "
        "python run_portfolio_review.py --candidates <id> "
        "or run_portfolio_review.py --with-candidates for core_fast batch."
    )


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(
        description=(
            "Run candidate portfolio builders in a controlled factory profile. "
            "Backend/research CLI — not the default Core MVP diagnosis path "
            "(use run_portfolio_review.py for portfolio-first review)."
        ),
        epilog=(
            "Default --profile default_v1 runs the full research menu (~16 builders). "
            "For product demo, use run_portfolio_review.py --candidates <id> instead."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="default_v1",
        help=(
            "Factory profile id (default: default_v1 = full research menu). "
            "Not the Core MVP default; use run_portfolio_review.py for diagnosis-first flow."
        ),
    )
    parser.add_argument(
        "--candidates",
        type=str,
        default=None,
        help="Comma-separated candidate ids; overrides --profile.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip builders when snapshot_10y.json exists (default: on).",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_false",
        dest="skip_existing",
        help="Always attempt builders unless other skip rules apply.",
    )
    parser.add_argument("--force", action="store_true", help="Rerun even when snapshot exists.")
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop factory on first failed step.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume from candidate_factory_manifest.json: skip succeeded and "
            "fresh skipped_existing steps when run checksum matches."
        ),
    )
    parser.add_argument(
        "--then-compare",
        action="store_true",
        help="Run comparison and decision package after factory completes.",
    )
    parser.add_argument(
        "--pdf-mode",
        type=str,
        default="none",
        choices=["none", "final_only", "per_candidate"],
        help=(
            "Per-candidate PDF rebuild policy for factory subprocess builders "
            "(default: none — sets PORTFOLIO_SKIP_VARIANT_PDF=1). "
            "Standalone run_*.py scripts are unchanged unless this env is set."
        ),
    )
    parser.add_argument(
        "--execution-mode",
        type=str,
        default="standard",
        choices=["fast", "standard", "legacy_full"],
        help=(
            "fast: in-process weights only. standard: weights + lightweight_comparison "
            "report (snapshots for compare, no per-candidate PDF; default). legacy_full: full "
            "subprocess run_*.py chain for explicit parity/debug."
        ),
    )
    parser.add_argument(
        "--output-profile",
        type=str,
        default="site_api",
        choices=sorted(OUTPUT_PROFILE_VALUES),
        help=(
            "Output policy (default: site_api JSON/cache only). Use full_report or "
            "legacy_export for explicit export/report artifacts."
        ),
    )
    parallel_group = parser.add_mutually_exclusive_group()
    parallel_group.add_argument(
        "--parallel-lightweight-reports",
        action="store_true",
        default=None,
        help=(
            "Force parallel lightweight_comparison reports in standard mode. "
            "Profile core_fast enables parallel by default when this flag is omitted. "
            "Falls back to sequential with --fail-fast, --pdf-mode per_candidate, "
            "or Phase 3 full report export."
        ),
    )
    parallel_group.add_argument(
        "--no-parallel-lightweight-reports",
        action="store_true",
        default=None,
        help=(
            "Disable parallel lightweight reports (overrides core_fast profile default)."
        ),
    )
    parser.add_argument(
        "--lightweight-report-workers",
        type=int,
        default=None,
        help="Maximum workers for --parallel-lightweight-reports (default: 4 or candidate count).",
    )
    parser.add_argument(
        "--full-candidate-reports",
        action="store_true",
        help=(
            "After the main factory phases, export full report_profile artifacts "
            "(HTML, commentary, rolling betas) for all candidates in this run."
        ),
    )
    parser.add_argument(
        "--selected-candidates-for-full-report",
        type=str,
        default=None,
        help=(
            "Comma-separated candidate ids for Phase 3 full report export. "
            "Implies --full-candidate-reports when set."
        ),
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.yml (default: project root config.yml).",
    )
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parent
    config_path = Path(args.config) if args.config else project_root / "config.yml"

    try:
        cfg = load_validated_config(config_path)
    except (ConfigValidationError, FileNotFoundError) as exc:
        logger.error("Configuration error: %s", exc)
        return 2

    explicit = _parse_candidates(args.candidates)
    profile_id = "explicit_list" if explicit is not None else args.profile
    _warn_standalone_full_menu_default(profile_id, explicit)
    selected_full = _parse_candidates(args.selected_candidates_for_full_report)
    full_reports = bool(args.full_candidate_reports or selected_full)
    output_policy = output_policy_for_profile(args.output_profile)
    if args.parallel_lightweight_reports:
        parallel_lightweight_reports: bool | None = True
    elif args.no_parallel_lightweight_reports:
        parallel_lightweight_reports = False
    else:
        parallel_lightweight_reports = None

    shared_run_context = None
    if profile_uses_review_run_context(profile_id):
        logger.info("Preparing ReviewRunContext for core_fast factory run.")
        shared_run_context = prepare_review_run_context(cfg, project_root=project_root)

    try:
        doc = run_candidate_factory(
            cfg,
            project_root=project_root,
            profile_id=profile_id,
            explicit_candidates=explicit,
            skip_existing=args.skip_existing,
            force=args.force,
            fail_fast=args.fail_fast,
            resume=args.resume,
            config_path=config_path if config_path.is_file() else None,
            pdf_mode=args.pdf_mode,
            execution_mode=args.execution_mode,
            output_profile=args.output_profile,
            full_candidate_reports=full_reports,
            selected_candidates_for_full_report=selected_full,
            parallel_lightweight_reports=parallel_lightweight_reports,
            lightweight_report_workers=args.lightweight_report_workers,
            shared_run_context=shared_run_context,
        )
    except FactoryValidationError as exc:
        logger.error("%s", exc)
        return 2

    doc["options"]["then_compare"] = args.then_compare

    out_dir = project_root / cfg.output_dir_final
    written = write_candidate_factory_outputs(
        doc,
        output_dir=out_dir,
        write_txt=output_policy.write_txt,
    )

    if args.then_compare:
        paths, err = run_then_compare(
            cfg,
            project_root=project_root,
            factory_run=doc,
            output_profile=args.output_profile,
            advanced_package=doc.get("factory_profile_id") != "explicit_list",
        )
        if err:
            doc.setdefault("warnings", []).append(f"comparison_failed: {err}")
        elif paths:
            doc["comparison_outputs"] = {k: str(v) for k, v in paths.items()}
            write_candidate_factory_outputs(
                doc,
                output_dir=out_dir,
                write_txt=output_policy.write_txt,
            )
    logger.info("Factory run summary: %s", written["candidate_factory_run_json"])

    code = factory_exit_code(doc)
    print(build_factory_run_txt(doc))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
