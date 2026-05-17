from __future__ import annotations

"""
Compare portfolio candidates: canonical candidate_comparison.json plus legacy subset files.

Reads existing per-candidate report artifacts (no optimizer or candidate-script reruns).
See docs/specs/candidate_comparison_spec.md.
"""

from pathlib import Path

from src.candidate_comparison import write_candidate_comparison_outputs
from src.config import load_validated_config
from src.utils import setup_logging, logger


def main() -> None:
    setup_logging()
    cfg = load_validated_config()
    project_root = Path(__file__).resolve().parent
    paths = write_candidate_comparison_outputs(cfg, project_root=project_root)
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
