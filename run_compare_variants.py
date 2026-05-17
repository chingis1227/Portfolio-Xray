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
    print(msg)


if __name__ == "__main__":
    main()
