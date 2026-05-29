from __future__ import annotations
"""
Thin orchestration for the legacy file-first MVP policy path:
input -> policy diagnosis -> comparison -> action.

Calls existing entrypoints only; does not change optimizer, metrics, or comparison logic.
Use run_portfolio_review.py for the portfolio-first analysis_subject workflow.
See docs/operational_runbook.md.
"""
from legacy.runners._paths import REPO_ROOT

import argparse
from pathlib import Path

from src.config import load_validated_config
from src.config_schema import ConfigValidationError
from src.mvp_workflow import (
    WORKFLOW_CHOICES,
    WORKFLOW_DIAGNOSIS_ONLY,
    WORKFLOW_FULL_DECISION,
    WORKFLOW_POLICY_CURRENT,
    WORKFLOW_POLICY_ONLY,
    build_mvp_workflow_plan,
    run_mvp_workflow_plan,
    summarize_plan,
)
from src.utils import logger, setup_logging


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(
        description=(
            "Run the legacy file-first MVP policy workflow (policy optimize/report, optional "
            "current materialization, optional candidate factory, comparison/decision package, "
            "PDF rebuild). Use run_portfolio_review.py for portfolio-first review."
        )
    )
    parser.add_argument(
        "--workflow",
        choices=WORKFLOW_CHOICES,
        default=WORKFLOW_POLICY_ONLY,
        help=(
            "policy-only: legacy optimize+report then compare; "
            "policy-current: legacy optimize+report plus --materialize-current when current_weights set; "
            "diagnosis-only: run_report then compare; "
            "full-decision: legacy policy path + factory + compare + PDF."
        ),
    )
    parser.add_argument(
        "--skip-optimize",
        action="store_true",
        help="Skip legacy run_optimization.py; run report/compare from existing weights.",
    )
    parser.add_argument("--no-cache", action="store_true", help="Pass --no-cache to data-heavy steps.")
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Pass --no-report to legacy run_optimization.py and run report explicitly afterward.",
    )
    parser.add_argument("--config", type=str, default=None, help="Path to config.yml.")
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        dest="optimizer_profile",
        help="Client profile name for legacy run_optimization.py.",
    )
    parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Do not run comparison / decision-package writers.",
    )
    parser.add_argument(
        "--skip-factory",
        action="store_true",
        help="For full-decision workflow, skip run_candidate_factory.py.",
    )
    parser.add_argument(
        "--factory-profile",
        type=str,
        default="default_v1",
        help="Factory profile when workflow=full-decision (default: default_v1).",
    )
    parser.add_argument(
        "--candidates",
        type=str,
        default=None,
        help="Comma-separated candidate ids for factory (overrides --factory-profile).",
    )
    parser.add_argument("--skip-pdf", action="store_true", help="Skip rebuild_pdf_reports.py.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned commands without executing them.",
    )
    args = parser.parse_args(argv)

    project_root = REPO_ROOT
    config_path = Path(args.config) if args.config else None

    try:
        cfg = load_validated_config(config_path)
    except ConfigValidationError as exc:
        logger.error("Config validation failed: %s", exc)
        return 1

    if args.workflow == WORKFLOW_DIAGNOSIS_ONLY:
        skip_optimize = True
    else:
        skip_optimize = args.skip_optimize

    plan = build_mvp_workflow_plan(
        cfg,
        project_root=project_root,
        workflow=args.workflow,
        skip_optimize=skip_optimize,
        no_cache=args.no_cache,
        no_report=args.no_report,
        config_path=config_path,
        optimizer_profile=args.optimizer_profile,
        skip_compare=args.skip_compare,
        skip_factory=args.skip_factory,
        factory_profile=args.factory_profile,
        factory_candidates=args.candidates,
        skip_pdf=args.skip_pdf,
    )

    print(summarize_plan(plan))
    code = run_mvp_workflow_plan(plan, project_root=project_root, dry_run=args.dry_run)
    if code == 0 and not args.dry_run:
        print("\nMVP workflow completed.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
