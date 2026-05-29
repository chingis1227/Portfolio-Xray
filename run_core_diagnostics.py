from __future__ import annotations

"""
Core diagnostics CLI (Blocks 1-3 only).

    Input Layer -> Portfolio X-Ray -> Stress Test Lab

Does not run Problem Classification, Candidate Launchpad, candidate factory,
comparison, Decision Verdict, AI Commentary, monitoring, optimizers, or PDF exports.
"""

import argparse
from pathlib import Path

from src.config import load_validated_config
from src.config_schema import ConfigValidationError
from src.core_diagnostics_workflow import (
    build_core_diagnostics_plan,
    run_core_diagnostics_plan,
    summarize_core_diagnostics_plan,
)
from src.output_policy import OUTPUT_PROFILE_VALUES
from src.runtime_entrypoint_labels import print_core_diagnostics_banner
from src.utils import logger, setup_logging


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(
        description=(
            "Run core portfolio diagnostics only (Blocks 1-3): "
            "input normalization, Portfolio X-Ray, and Stress Test Lab."
        )
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Pass --no-cache to the materialization step.",
    )
    parser.add_argument(
        "--output-profile",
        choices=sorted(OUTPUT_PROFILE_VALUES),
        default="site_api",
        help="Output policy (default: site_api JSON/cache only).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned commands without executing them.",
    )
    args = parser.parse_args(argv)

    print_core_diagnostics_banner()
    print()

    project_root = Path(__file__).resolve().parent
    try:
        cfg = load_validated_config()
    except ConfigValidationError as exc:
        logger.error("Config validation failed: %s", exc)
        return 1

    plan = build_core_diagnostics_plan(
        cfg,
        project_root=project_root,
        no_cache=args.no_cache,
        output_profile=args.output_profile,
    )
    print(summarize_core_diagnostics_plan(plan))
    code = run_core_diagnostics_plan(plan, project_root=project_root, dry_run=args.dry_run)
    if code == 0 and not args.dry_run:
        sidecar = Path(getattr(cfg, "output_dir_final", "Main portfolio")) / "analysis_subject"
        print("\nCore diagnostics completed.")
        print(f"  Artifacts: {sidecar}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
