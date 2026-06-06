from __future__ import annotations

"""
Compare portfolio candidates: canonical candidate_comparison.json plus legacy subset files.

Reads existing per-candidate report artifacts (no optimizer or candidate-script reruns).
See docs/specs/candidate_comparison_spec.md.
"""

from pathlib import Path
import argparse

from src.candidate_comparison import (
    write_block8_current_vs_candidate_only_outputs,
    write_candidate_comparison_outputs,
)
from src.config import load_validated_config
from src.output_policy import OUTPUT_PROFILE_VALUES
from src.utils import setup_logging, logger


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(
        description=(
            "Write candidate comparison and decision JSON contracts. Technical boundary: "
            "use --block8-only --candidate <id> from the vertical product loop; default mode "
            "writes advanced/backend support artifacts and is not the Core MVP demo entry."
        )
    )
    parser.add_argument(
        "--output-profile",
        choices=sorted(OUTPUT_PROFILE_VALUES),
        default="site_api",
        help="Output policy (default: site_api JSON-only; use full_report for TXT/legacy exports).",
    )
    parser.add_argument(
        "--block8-only",
        action="store_true",
        help=(
            "Vertical product mode: write scoped candidate_comparison.json and "
            "current_vs_candidate.json only; do not write verdict/action/journal/AI context."
        ),
    )
    parser.add_argument(
        "--candidate",
        dest="candidate_ids",
        action="append",
        default=None,
        help=(
            "Selected candidate id for --block8-only. Can be repeated. If omitted, "
            "candidate_generation.json or explicit-list candidate_factory_run.json is used."
        ),
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.yml (default: project root config.yml).",
    )
    args = parser.parse_args()
    cfg = load_validated_config(args.config)
    project_root = Path(__file__).resolve().parent
    if args.block8_only:
        paths = write_block8_current_vs_candidate_only_outputs(
            cfg,
            project_root=project_root,
            candidate_ids=args.candidate_ids,
        )
    else:
        paths = write_candidate_comparison_outputs(
            cfg,
            project_root=project_root,
            output_profile=args.output_profile,
        )
    logger.info(
        "Comparison written: %s (legacy: %s; scorecard: %s)",
        paths.get("candidate_comparison_json"),
        paths.get("portfolio_comparison_json"),
        paths.get("robustness_scorecard_json"),
    )
    msg = f"Comparison written to {paths['candidate_comparison_json']}"
    if "candidate_comparison_txt" in paths:
        msg += f" and {paths['candidate_comparison_txt']}"
    if "robustness_scorecard_json" in paths:
        msg += f"\nRobustness scorecard: {paths['robustness_scorecard_json']}"
    if "portfolio_health_score_json" in paths:
        msg += f"\nPortfolio health score: {paths['portfolio_health_score_json']}"
    if "selection_decision_json" in paths:
        msg += f"\nSelection decision: {paths['selection_decision_json']}"
    if "action_plan_json" in paths:
        msg += f"\nAction plan: {paths['action_plan_json']}"
    if "monitoring_diff_json" in paths:
        msg += f"\nMonitoring diff: {paths['monitoring_diff_json']}"
    if "decision_journal_json" in paths:
        msg += f"\nDecision journal: {paths['decision_journal_json']}"
    if "decision_package_summary_txt" in paths:
        msg += f"\nDecision package summary: {paths['decision_package_summary_txt']}"
    if "current_vs_policy_status_json" in paths:
        msg += f"\nCurrent vs policy status: {paths['current_vs_policy_status_json']}"
        try:
            import json

            with open(paths["current_vs_policy_status_json"], encoding="utf-8") as f:
                status = json.load(f)
            user_line = status.get("user_message_en")
            if user_line:
                msg += f"\n  {user_line}"
            hint = (status.get("materialization") or {}).get("command_hint")
            if hint:
                msg += f"\n  Hint: {hint}"
            if status.get("no_trade_actionable"):
                msg += "\n  No-Trade versus current was evaluated in this run."
        except (OSError, json.JSONDecodeError):
            pass
    print(msg)


if __name__ == "__main__":
    main()
