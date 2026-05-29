from __future__ import annotations

"""
Portfolio-first review CLI.

    Runs existing entrypoints in the portfolio-first order. By default this is now
    the diagnosis-only product path; candidate generation/comparison is explicit.
"""

import argparse
from pathlib import Path

from src.config import load_validated_config
from src.config_schema import ConfigValidationError
from src.candidate_weights import EXECUTION_MODES
from src.output_policy import OUTPUT_PROFILE_VALUES
from src.portfolio_review_workflow import (
    DEFAULT_REVIEW_MODE,
    REVIEW_MODES,
    build_portfolio_review_plan,
    resolve_portfolio_review_runtime_mode,
    resolve_review_candidate_profile,
    run_portfolio_review_plan,
    summarize_plan,
)
from src.runtime_entrypoint_labels import print_portfolio_review_banner
from src.utils import logger, setup_logging


def resolve_candidate_execution_flags(
    *,
    skip_candidates: bool = False,
    skip_compare: bool = False,
    candidates: str | None = None,
    with_candidates: bool = False,
    mode: str = DEFAULT_REVIEW_MODE,
    candidate_profile: str | None = None,
    no_skip_existing: bool = False,
    force_candidates: bool = False,
    resume_candidates: bool = False,
    fail_fast: bool = False,
) -> tuple[bool, bool, bool]:
    """Return (effective_skip_candidates, effective_skip_compare, run_candidates).

    Plain ``run_portfolio_review.py`` is the product diagnosis-only path. Candidate
    generation is explicit via selected candidates, full/research mode, profile
    override, or candidate factory control flags.
    """
    explicit_candidate_request = bool(candidates)
    explicit_batch_request = (
        with_candidates
        or mode == "full"
        or bool(candidate_profile)
        or no_skip_existing
        or force_candidates
        or resume_candidates
        or fail_fast
    )
    run_candidates = (
        not skip_candidates
        and (explicit_candidate_request or explicit_batch_request)
    )
    effective_skip_candidates = not run_candidates
    effective_skip_compare = skip_compare or not run_candidates
    return effective_skip_candidates, effective_skip_compare, run_candidates


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(
        description=(
            "Run the portfolio-first review workflow: materialize analysis_subject "
            "diagnostics before candidate generation, comparison, and report packaging."
        )
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Pass --no-cache to analysis_subject materialization.",
    )
    parser.add_argument(
        "--skip-candidates",
        action="store_true",
        help="Skip candidate factory. In the default product path this is already true.",
    )
    parser.add_argument(
        "--with-candidates",
        action="store_true",
        help=(
            "Run the backend candidate factory using the resolved profile. "
            "Use --candidates for the canonical one-candidate product path."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=sorted(REVIEW_MODES),
        default=DEFAULT_REVIEW_MODE,
        help=(
            "Review scope when candidates are requested: core = backend core_fast batch; "
            "full = advanced/research default_v1 menu including optimizers and robust suite."
        ),
    )
    parser.add_argument(
        "--candidate-profile",
        type=str,
        default=None,
        help=(
            "Override factory profile (e.g. core_v1 for sequential regression, "
            "default_v1). When omitted, profile follows --mode (core → core_fast)."
        ),
    )
    parser.add_argument(
        "--candidates",
        type=str,
        default=None,
        help="Comma-separated candidate ids; overrides --candidate-profile.",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Ask candidate factory to rerun builders even when snapshots exist.",
    )
    parser.add_argument(
        "--force-candidates",
        action="store_true",
        help="Pass --force to candidate factory.",
    )
    parser.add_argument(
        "--resume-candidates",
        action="store_true",
        help=(
            "Pass --resume to candidate factory. Use after an interrupted full "
            "candidate run to continue from candidate_factory_manifest.json."
        ),
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Pass --fail-fast to candidate factory.",
    )
    parser.add_argument(
        "--execution-mode",
        type=str,
        default=None,
        choices=sorted(EXECUTION_MODES),
        help=(
            "Factory execution mode (default when omitted: standard — in-process weights "
            "plus lightweight_comparison report, no per-candidate PDF). Use legacy_full "
            "for subprocess run_*.py parity/debug."
        ),
    )
    parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Do not run comparison / decision-package writers.",
    )
    parser.add_argument(
        "--output-profile",
        choices=sorted(OUTPUT_PROFILE_VALUES),
        default="site_api",
        help="Output policy (default: site_api JSON/cache only).",
    )
    parser.add_argument(
        "--with-pdf",
        action="store_true",
        help="Explicitly rebuild the narrow portfolio-first PDF subset after JSON workflow.",
    )
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Deprecated compatibility flag; PDF is skipped by default unless --with-pdf or --legacy-full-pdf is used.",
    )
    parser.add_argument(
        "--legacy-full-pdf",
        action="store_true",
        help=(
            "Rebuild the full legacy PDF suite (EW/RP, policy Main, optimizer baselines). "
            "Default rebuild is portfolio-first only (analysis_subject + decision package)."
        ),
    )
    parser.add_argument(
        "--no-parallel-lightweight-reports",
        action="store_true",
        help=(
            "Disable parallel Phase 2 lightweight reports in candidate factory "
            "(overrides core_fast profile default; debugging)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned commands without executing them.",
    )
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parent

    try:
        cfg = load_validated_config()
    except ConfigValidationError as exc:
        logger.error("Config validation failed: %s", exc)
        return 1

    review_mode, factory_profile = resolve_review_candidate_profile(
        review_mode=args.mode,
        candidate_profile=args.candidate_profile,
    )
    effective_output_profile = (
        "legacy_export"
        if (args.with_pdf or args.legacy_full_pdf) and args.output_profile == "site_api"
        else args.output_profile
    )
    effective_skip_candidates, effective_skip_compare, run_candidates = (
        resolve_candidate_execution_flags(
            skip_candidates=args.skip_candidates,
            skip_compare=args.skip_compare,
            candidates=args.candidates,
            with_candidates=args.with_candidates,
            mode=args.mode,
            candidate_profile=args.candidate_profile,
            no_skip_existing=args.no_skip_existing,
            force_candidates=args.force_candidates,
            resume_candidates=args.resume_candidates,
            fail_fast=args.fail_fast,
        )
    )

    runtime_mode = resolve_portfolio_review_runtime_mode(
        skip_candidates=effective_skip_candidates,
        skip_compare=effective_skip_compare,
        review_mode=review_mode,
        candidate_profile=args.candidate_profile,
        candidate_ids=args.candidates,
    )
    print_portfolio_review_banner(
        runtime_mode=runtime_mode,
        candidates=(args.candidates.split(",")[0].strip() if args.candidates else None),
    )
    print()

    plan = build_portfolio_review_plan(
        cfg,
        project_root=project_root,
        no_cache=args.no_cache,
        skip_candidates=effective_skip_candidates,
        review_mode=review_mode,
        candidate_profile=args.candidate_profile,
        candidate_ids=args.candidates,
        skip_existing_candidates=not args.no_skip_existing,
        force_candidates=args.force_candidates,
        resume_candidates=args.resume_candidates,
        fail_fast=args.fail_fast,
        skip_compare=effective_skip_compare,
        skip_pdf=(args.skip_pdf or not (args.with_pdf or args.legacy_full_pdf)),
        legacy_full_pdf=args.legacy_full_pdf,
        factory_execution_mode=args.execution_mode,
        output_profile=effective_output_profile,
        no_parallel_lightweight_reports=args.no_parallel_lightweight_reports,
    )

    print(
        summarize_plan(
            plan,
            review_mode=review_mode,
            factory_profile=(
                "none"
                if not run_candidates
                else factory_profile
                if not args.candidates
                else "explicit_list"
            ),
        )
    )
    code = run_portfolio_review_plan(plan, project_root=project_root, dry_run=args.dry_run)
    if code == 0 and not args.dry_run:
        print("\nPortfolio review workflow completed.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
