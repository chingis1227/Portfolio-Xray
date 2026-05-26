#!/usr/bin/env python3
"""Print or run the one-candidate command for a Launchpad candidate_method_id.

Maps Launchpad / Alternatives Builder method ids to the existing factory delegation plan.
Does not add flags to run_portfolio_review.py.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.portfolio_alternatives_builder import (  # noqa: E402
    PortfolioAlternativeRequest,
    build_portfolio_alternative_plan,
    run_portfolio_alternative_plan,
)


def _review_command(candidate_id: str) -> str:
    return f"{sys.executable} run_portfolio_review.py --candidates {candidate_id}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Map a Launchpad candidate_method_id to documented one-candidate commands "
            "(factory plan + portfolio review)."
        )
    )
    parser.add_argument(
        "--method",
        required=True,
        help="candidate_method_id from Candidate Launchpad (e.g. equal_weight).",
    )
    parser.add_argument(
        "--goal",
        default=None,
        help="Optional goal text recorded in plan provenance.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute the factory delegation command (network + disk). Default: print only.",
    )
    args = parser.parse_args()

    request = PortfolioAlternativeRequest(
        candidate_method_id=str(args.method).strip(),
        goal=args.goal,
    )
    plan = build_portfolio_alternative_plan(request, project_root=REPO_ROOT)
    factory_cmd = " ".join(plan.command)

    print("PortfolioAlternativeBuildPlan")
    print(f"  candidate_method_id: {plan.candidate_method_id}")
    print(f"  candidate_id:        {plan.candidate_id}")
    if plan.warnings:
        print(f"  warnings:            {', '.join(plan.warnings)}")
    print()
    print("Delegated factory command (builder default):")
    print(f"  {factory_cmd}")
    print()
    print("Equivalent manual commands (documented product path):")
    print(
        f"  {sys.executable} run_candidate_factory.py --candidates {plan.candidate_id} "
        "--execution-mode standard --then-compare"
    )
    print(f"  {_review_command(plan.candidate_id)}")
    print()
    print("Docs: docs/product_flow_operator_guide.md")

    if args.run:
        print("Running factory delegation...")
        completed = run_portfolio_alternative_plan(
            plan,
            project_root=REPO_ROOT,
            dry_run=False,
            runner=subprocess.run,
        )
        if completed is None:
            return 1
        return int(completed.returncode)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
