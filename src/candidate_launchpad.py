"""Candidate Launchpad data layer for diagnosis-first Portfolio MRI.

Legacy V1 builder (``candidate_launchpad_v1``). Production pipeline uses
``src/block_4/launchpad_cards.py`` (``candidate_launchpad_v2``) since Block 4 v2
Session 10. Retained for unit tests and migration reference only.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANDIDATE_LAUNCHPAD_VERSION = "candidate_launchpad_v1"
CANDIDATE_LAUNCHPAD_FILENAME = "candidate_launchpad.json"

GOAL_TO_METHODS: dict[str, tuple[str, ...]] = {
    "Reduce volatility": ("minimum_variance", "risk_parity", "equal_weight"),
    "Reduce drawdown": ("minimum_variance", "minimum_cvar_constrained", "risk_parity"),
    "Improve diversification": (
        "equal_weight",
        "equal_weight_by_asset_class",
        "maximum_diversification",
    ),
    "Reduce concentration": ("equal_weight", "equal_weight_by_asset_class", "risk_budget_by_asset"),
    "Improve crisis resilience": (
        "minimum_cvar_constrained",
        "robust_mv_constrained",
        "robust_scenario",
    ),
    "Improve return/risk balance": ("maximum_diversification", "robust_mv_constrained"),
    "Compare against simple benchmark": ("equal_weight", "risk_parity"),
    "Keep current portfolio and monitor": (),
    "Review data quality": (),
}

GOAL_DESCRIPTIONS: dict[str, str] = {
    "Reduce volatility": "Test whether a lower-volatility construction improves the diagnosed risk profile.",
    "Reduce drawdown": "Test whether downside-risk-focused candidates reduce drawdown exposure.",
    "Improve diversification": "Test whether simpler diversified benchmarks improve concentration and balance.",
    "Reduce concentration": "Test whether caps or equalized exposures reduce dominant holdings.",
    "Improve crisis resilience": "Test whether stress-aware candidates improve weak crisis or hedge behavior.",
    "Improve return/risk balance": "Test whether diversified return/risk methods improve efficiency.",
    "Compare against simple benchmark": "Compare the diagnosed portfolio with transparent benchmark candidates.",
    "Keep current portfolio and monitor": "Do not generate a candidate yet; track changes and warnings.",
    "Review data quality": "Resolve evidence-quality gaps before relying on candidate comparisons.",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_goal(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    return text if text else None


def _problem_rows(problem_classification: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(problem_classification, dict):
        return []
    rows = problem_classification.get("problems")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _card_id(goal: str, idx: int) -> str:
    slug = (
        goal.lower()
        .replace("/", " ")
        .replace("-", " ")
        .replace("  ", " ")
        .strip()
        .replace(" ", "_")
    )
    return f"launchpad_{idx:02d}_{slug}"


def _method_labels(method_ids: tuple[str, ...]) -> list[dict[str, str]]:
    return [{"candidate_method_id": method_id} for method_id in method_ids]


def build_candidate_launchpad(
    *,
    problem_classification: dict[str, Any] | None,
    analysis_end: str | None = None,
) -> dict[str, Any]:
    """Build Candidate Launchpad cards from Problem Classification output."""

    cards: list[dict[str, Any]] = []
    seen_goals: set[str] = set()
    problems = _problem_rows(problem_classification)

    for problem in problems:
        problem_id = str(problem.get("problem_id") or "")
        if problem_id == "current_portfolio_acceptable":
            candidate_goals = ["Keep current portfolio and monitor", "Compare against simple benchmark"]
        else:
            raw_paths = problem.get("reasonable_paths_to_test")
            candidate_goals = [
                goal
                for goal in (_normalize_goal(path) for path in raw_paths or [])
                if goal is not None
            ]
        for goal in candidate_goals:
            if goal in seen_goals:
                continue
            seen_goals.add(goal)
            method_ids = GOAL_TO_METHODS.get(goal, ())
            cards.append(
                {
                    "card_id": _card_id(goal, len(cards) + 1),
                    "goal": goal,
                    "description": GOAL_DESCRIPTIONS.get(goal, "Test this improvement hypothesis."),
                    "source_problem_id": problem_id or None,
                    "source_problem_label": problem.get("label"),
                    "rationale": {
                        "severity": problem.get("severity"),
                        "confidence": problem.get("confidence"),
                        "evidence": problem.get("evidence") or [],
                    },
                    "suggested_methods": _method_labels(method_ids),
                    "generates_portfolio": False,
                    "requires_user_action": goal not in {
                        "Keep current portfolio and monitor",
                        "Review data quality",
                    },
                }
            )

    if not cards:
        cards.append(
            {
                "card_id": "launchpad_01_keep_current_portfolio_and_monitor",
                "goal": "Keep current portfolio and monitor",
                "description": GOAL_DESCRIPTIONS["Keep current portfolio and monitor"],
                "source_problem_id": None,
                "source_problem_label": None,
                "rationale": {
                    "severity": "unknown",
                    "confidence": "low",
                    "evidence": [],
                },
                "suggested_methods": [],
                "generates_portfolio": False,
                "requires_user_action": False,
            }
        )

    warnings: list[str] = []
    if not isinstance(problem_classification, dict):
        warnings.append("missing_problem_classification")
    elif problem_classification.get("warnings"):
        warnings.append("problem_classification_has_warnings")

    return {
        "schema_version": CANDIDATE_LAUNCHPAD_VERSION,
        "diagnostic_only": True,
        "generated_at": _utc_now_iso(),
        "analysis_end": analysis_end or (problem_classification or {}).get("analysis_end"),
        "source_artifacts": {
            "problem_classification": "problem_classification.json"
            if isinstance(problem_classification, dict)
            else None,
        },
        "cards": cards,
        "summary": {
            "n_cards": len(cards),
            "primary_card_id": cards[0]["card_id"] if cards else None,
            "has_portfolio_generating_options": any(bool(card["suggested_methods"]) for card in cards),
            "has_keep_current_option": any(
                card.get("goal") == "Keep current portfolio and monitor" for card in cards
            ),
        },
        "warnings": warnings,
    }


def write_candidate_launchpad_outputs(
    *,
    output_dir: str | Path,
    problem_classification: dict[str, Any] | None,
    analysis_end: str | None = None,
) -> Path:
    """Write ``candidate_launchpad.json`` under ``output_dir``."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = build_candidate_launchpad(
        problem_classification=problem_classification,
        analysis_end=analysis_end,
    )
    path = out / CANDIDATE_LAUNCHPAD_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
    return path
