from __future__ import annotations

"""
Portfolio-first review CLI.

Runs existing entrypoints in the portfolio-first order:
analysis_subject diagnostics -> candidates -> comparison -> report package.
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
    resolve_review_candidate_profile,
    run_portfolio_review_plan,
    summarize_plan,
)
from src.utils import logger, setup_logging


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
        help="Skip candidate factory and compare existing candidate artifacts instead.",
    )
    parser.add_argument(
        "--mode",
        choices=sorted(REVIEW_MODES),
        default=DEFAULT_REVIEW_MODE,
        help=(
            "Review scope: core = benchmarks + risk budgets (default routine path); "
            "full = entire default_v1 menu including optimizers and robust suite."
        ),
    )
    parser.add_argument(
        "--candidate-profile",
        type=str,
        default=None,
        help=(
            "Override factory profile (e.g. core_v1, default_v1). "
            "When omitted, profile follows --mode."
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

    plan = build_portfolio_review_plan(
        cfg,
        project_root=project_root,
        no_cache=args.no_cache,
        skip_candidates=args.skip_candidates,
        review_mode=review_mode,
        candidate_profile=args.candidate_profile,
        candidate_ids=args.candidates,
        skip_existing_candidates=not args.no_skip_existing,
        force_candidates=args.force_candidates,
        resume_candidates=args.resume_candidates,
        fail_fast=args.fail_fast,
        skip_compare=args.skip_compare,
        skip_pdf=(args.skip_pdf or not (args.with_pdf or args.legacy_full_pdf)),
        legacy_full_pdf=args.legacy_full_pdf,
        factory_execution_mode=args.execution_mode,
        output_profile=effective_output_profile,
    )

    print(
        summarize_plan(
            plan,
            review_mode=review_mode,
            factory_profile=factory_profile if not args.candidates else "explicit_list",
        )
    )
    code = run_portfolio_review_plan(plan, project_root=project_root, dry_run=args.dry_run)
    if code == 0 and not args.dry_run:
        print("\nPortfolio review workflow completed.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
