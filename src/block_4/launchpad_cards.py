"""Block 4 v2 Candidate Launchpad card generation (Session 08).

Builds v2 launchpad cards from mapped action paths and problem rows.
Cards are hypotheses to test — no weights, no builder execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.block_4.action_path_mapping import ActionPathMappingResult, SuggestedActionRow
from src.block_4.evidence_extraction import EvidenceExtractionResult
from src.block_4.no_trade_gate import NoTradeGateResult, gate_from_primary_problem_id
from src.block_4.problem_scoring import ProblemScoringResult
from src.block_4.problem_taxonomy import get_action_path, get_problem_definition
from src.block_4.thresholds import get_block_4_thresholds

LAUNCHPAD_BUILD_RULESET_VERSION = "block_4_v2_launchpad_cards_v1"
CANDIDATE_LAUNCHPAD_V2_VERSION = "candidate_launchpad_v2"
MAX_LAUNCHPAD_CARDS = 4
MAX_SUPPRESSED_CARDS = 2

LAUNCHPAD_V2_DISCLAIMER_EN = (
    "This card suggests a hypothesis to test, not a buy or sell instruction."
)

_MONITOR_ACTION_PATH_IDS = frozenset(
    {
        "keep_current_portfolio_and_monitor",
        "compare_against_simple_benchmark",
        "evidence_insufficient_do_not_act_yet",
        "test_another_candidate",
    }
)

_NO_USER_ACTION_PATH_IDS = frozenset(
    {
        "keep_current_portfolio_and_monitor",
        "evidence_insufficient_do_not_act_yet",
    }
)

_KNOWN_METHOD_IDS = frozenset(
    {
        "equal_weight",
        "equal_weight_by_asset_class",
        "maximum_diversification",
        "minimum_cvar_constrained",
        "minimum_variance",
        "risk_budget_by_asset",
        "risk_parity",
        "robust_mv_constrained",
        "robust_scenario",
    }
)


@dataclass
class LaunchpadCardsResult:
    cards: tuple[dict[str, Any], ...] = ()
    launchpad_outcome: str = "proceed_to_launchpad"
    launchpad_suppressed: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_summary_dict(self, *, launchpad_outcome: str | None = None) -> dict[str, Any]:
        outcome = launchpad_outcome or self.launchpad_outcome
        return {
            "n_cards": len(self.cards),
            "primary_card_id": self.cards[0]["card_id"] if self.cards else None,
            "has_portfolio_generating_options": any(
                bool(card.get("suggested_methods")) for card in self.cards
            ),
            "has_keep_current_option": any(
                card.get("goal") == "Keep current portfolio and monitor" for card in self.cards
            ),
            "launchpad_outcome": outcome,
        }


def build_launchpad_cards(
    mapping: ActionPathMappingResult,
    *,
    no_trade_gate: NoTradeGateResult | None = None,
    launchpad_outcome: str | None = None,
    launchpad_suppressed: bool | None = None,
) -> LaunchpadCardsResult:
    """Build v2 launchpad cards from action-path mapping output."""
    primary_id = str(mapping.primary_problem["problem_id"])
    gate = no_trade_gate or gate_from_primary_problem_id(primary_id)
    suppressed = (
        launchpad_suppressed
        if launchpad_suppressed is not None
        else gate.launchpad_suppressed
    )
    outcome = launchpad_outcome or gate.outcome

    problem_rows_by_id = {
        str(row["problem_id"]): row for row in mapping.problem_rows
    }
    selected_actions = _select_actions_for_cards(
        mapping.suggested_actions,
        primary_problem_id=primary_id,
        launchpad_suppressed=suppressed,
    )

    cards: list[dict[str, Any]] = []
    warnings: list[str] = []
    for rank, action in enumerate(selected_actions, start=1):
        card = _build_card(
            action,
            problem_rows_by_id=problem_rows_by_id,
            priority_rank=rank,
            launchpad_suppressed=suppressed,
        )
        if card is not None:
            cards.append(card)

    if not cards:
        warnings.append("no_cards_from_suggested_actions")
        cards.append(_fallback_monitor_card(primary_id, mapping.primary_problem))

    return LaunchpadCardsResult(
        cards=tuple(cards),
        launchpad_outcome=outcome,
        launchpad_suppressed=suppressed,
        warnings=tuple(warnings),
    )


def build_candidate_launchpad_v2_document(
    mapping: ActionPathMappingResult,
    *,
    analysis_end: str | None = None,
    generated_at: str | None = None,
    scoring: ProblemScoringResult | None = None,
    evidence: EvidenceExtractionResult | None = None,
    no_trade_gate: NoTradeGateResult | None = None,
    launchpad_outcome: str | None = None,
    launchpad_suppressed: bool | None = None,
    ruleset_version: str | None = None,
) -> dict[str, Any]:
    """Assemble top-level ``candidate_launchpad_v2`` document (Session 10 wiring uses this)."""
    from src.block_4.no_trade_gate import evaluate_no_trade_gate

    cfg = get_block_4_thresholds()
    gate = no_trade_gate
    if gate is None and scoring is not None and evidence is not None:
        gate = evaluate_no_trade_gate(mapping, scoring, evidence)
    cards_result = build_launchpad_cards(
        mapping,
        no_trade_gate=gate,
        launchpad_outcome=launchpad_outcome,
        launchpad_suppressed=launchpad_suppressed,
    )
    outcome = launchpad_outcome or cards_result.launchpad_outcome
    summary = cards_result.to_summary_dict(launchpad_outcome=outcome)

    return {
        "schema_version": CANDIDATE_LAUNCHPAD_V2_VERSION,
        "diagnostic_only": True,
        "ruleset_version": ruleset_version or cfg.ruleset_version,
        "generated_at": generated_at or _utc_now_iso(),
        "analysis_end": analysis_end,
        "source_artifacts": {"problem_classification": "problem_classification.json"},
        "launchpad_outcome": outcome,
        "cards": list(cards_result.cards),
        "summary": summary,
        "warnings": list(cards_result.warnings),
    }


def _select_actions_for_cards(
    suggested_actions: tuple[SuggestedActionRow, ...],
    *,
    primary_problem_id: str,
    launchpad_suppressed: bool,
) -> tuple[SuggestedActionRow, ...]:
    max_cards = MAX_SUPPRESSED_CARDS if launchpad_suppressed else MAX_LAUNCHPAD_CARDS
    defn = get_problem_definition(primary_problem_id)
    suppress_methods = defn is not None and defn.suppress_launchpad_methods

    selected: list[SuggestedActionRow] = []
    for action in suggested_actions:
        if len(selected) >= max_cards:
            break
        if launchpad_suppressed and action.action_path_id not in _MONITOR_ACTION_PATH_IDS:
            continue
        if suppress_methods and action.action_path_id not in _MONITOR_ACTION_PATH_IDS:
            continue
        selected.append(action)
    return tuple(selected)


def _build_card(
    action: SuggestedActionRow,
    *,
    problem_rows_by_id: dict[str, dict[str, Any]],
    priority_rank: int,
    launchpad_suppressed: bool,
) -> dict[str, Any] | None:
    action_path = get_action_path(action.action_path_id)
    if action_path is None:
        return None

    source_problem_id = _pick_source_problem_id(action, problem_rows_by_id)
    problem_row = problem_rows_by_id.get(source_problem_id or "")
    defn = get_problem_definition(source_problem_id) if source_problem_id else None

    method_ids = _method_ids_for_card(action.action_path_id, problem_row, launchpad_suppressed)
    suggested_methods = [{"candidate_method_id": mid} for mid in method_ids]

    title = action_path.label_en
    if defn is not None and action.action_path_id == problem_row.get("suggested_action_path_id"):
        title = defn.launchpad_card_title_en

    card: dict[str, Any] = {
        "card_id": _card_id(action.action_path_id, priority_rank),
        "title": title,
        "goal": action_path.goal_label,
        "description": action_path.launchpad_description_en,
        "source_problem_id": source_problem_id,
        "source_problem_label": (problem_row or {}).get("label_en"),
        "rationale": _card_rationale(problem_row),
        "suggested_methods": suggested_methods,
        "generates_portfolio": False,
        "requires_user_action": action.action_path_id not in _NO_USER_ACTION_PATH_IDS,
        "why_this_path_en": _why_this_path_en(problem_row, action_path.label_en),
        "what_this_tests_en": (
            defn.launchpad_what_this_tests_en
            if defn is not None
            else action_path.launchpad_description_en
        ),
        "simple_constraints": _simple_constraints(action.action_path_id, problem_row),
        "expected_tradeoff_to_check_en": (
            defn.launchpad_tradeoff_en if defn is not None else _default_tradeoff(action.action_path_id)
        ),
        "not_a_recommendation_disclaimer_en": LAUNCHPAD_V2_DISCLAIMER_EN,
        "when_to_skip_this_test_en": (
            defn.launchpad_skip_when_en if defn is not None else "Skip when the diagnosis no longer applies."
        ),
        "priority_rank": priority_rank,
    }
    if method_ids:
        card["default_method"] = method_ids[0]
    return card


def _pick_source_problem_id(
    action: SuggestedActionRow,
    problem_rows_by_id: dict[str, dict[str, Any]],
) -> str | None:
    for problem_id in action.source_problem_ids:
        if problem_id in problem_rows_by_id:
            return problem_id
    return action.source_problem_ids[0] if action.source_problem_ids else None


def _method_ids_for_card(
    action_path_id: str,
    problem_row: dict[str, Any] | None,
    launchpad_suppressed: bool,
) -> tuple[str, ...]:
    if launchpad_suppressed and action_path_id == "compare_against_simple_benchmark":
        path = get_action_path(action_path_id)
        if path is None:
            return ()
        return tuple(mid for mid in path.candidate_method_ids if mid in _KNOWN_METHOD_IDS)

    if action_path_id in _NO_USER_ACTION_PATH_IDS:
        return ()

    path = get_action_path(action_path_id)
    if path is None or not path.candidate_method_ids:
        return ()

    allowed_path_methods = [mid for mid in path.candidate_method_ids if mid in _KNOWN_METHOD_IDS]
    if problem_row:
        from_problem = [
            str(item.get("candidate_method_id"))
            for item in problem_row.get("candidate_method_suggestions") or []
            if str(item.get("candidate_method_id")) in allowed_path_methods
        ]
        if from_problem:
            return tuple(from_problem)

    return tuple(allowed_path_methods)


def _card_rationale(problem_row: dict[str, Any] | None) -> dict[str, Any]:
    if not problem_row:
        return {"severity": "unknown", "confidence": "low", "evidence": []}
    evidence = list(problem_row.get("evidence_refs") or [])[:3]
    return {
        "severity": problem_row.get("severity"),
        "confidence": problem_row.get("confidence"),
        "evidence": evidence,
    }


def _why_this_path_en(problem_row: dict[str, Any] | None, action_label: str) -> str:
    if problem_row:
        headline = str(problem_row.get("short_diagnosis_en") or "").strip()
        if headline:
            return f"{headline} This path tests whether {action_label.lower()} helps."
    return f"The diagnosis supports testing whether {action_label.lower()} improves the portfolio profile."


def _simple_constraints(action_path_id: str, problem_row: dict[str, Any] | None) -> list[str]:
    if action_path_id in _NO_USER_ACTION_PATH_IDS:
        return []
    constraints: list[str] = []
    if problem_row:
        severity = str(problem_row.get("severity") or "")
        if severity == "high":
            constraints.append("Prioritize risk reduction over return maximization in this test.")
        materiality = str((problem_row.get("scoring") or {}).get("materiality") or "")
        if materiality in {"high", "medium"}:
            constraints.append("Compare candidate stress behavior against the current portfolio.")
    return constraints


def _default_tradeoff(action_path_id: str) -> str:
    if action_path_id == "compare_against_simple_benchmark":
        return "Transparency and simplicity vs fidelity to the current mandate."
    if action_path_id == "keep_current_portfolio_and_monitor":
        return "Stability vs opportunity cost of exploration."
    return "Risk improvement vs expected return and implementation turnover."


def _fallback_monitor_card(
    primary_problem_id: str,
    primary_row: dict[str, Any],
) -> dict[str, Any]:
    action_path = get_action_path("keep_current_portfolio_and_monitor")
    defn = get_problem_definition(primary_problem_id)
    return {
        "card_id": "launchpad_01_keep_current_portfolio_and_monitor",
        "title": defn.launchpad_card_title_en if defn else "Keep Current Portfolio and Monitor",
        "goal": action_path.goal_label if action_path else "Keep current portfolio and monitor",
        "description": (
            action_path.launchpad_description_en
            if action_path
            else "Track diagnostics over time without generating a candidate portfolio."
        ),
        "source_problem_id": primary_problem_id,
        "source_problem_label": primary_row.get("label_en"),
        "rationale": _card_rationale(primary_row),
        "suggested_methods": [],
        "generates_portfolio": False,
        "requires_user_action": False,
        "why_this_path_en": _why_this_path_en(primary_row, "keeping the current portfolio and monitoring"),
        "what_this_tests_en": (
            defn.launchpad_what_this_tests_en
            if defn
            else "Whether conditions change enough to warrant a new candidate test."
        ),
        "simple_constraints": [],
        "expected_tradeoff_to_check_en": _default_tradeoff("keep_current_portfolio_and_monitor"),
        "not_a_recommendation_disclaimer_en": LAUNCHPAD_V2_DISCLAIMER_EN,
        "when_to_skip_this_test_en": (
            defn.launchpad_skip_when_en if defn else "N/A — this is the monitor path."
        ),
        "priority_rank": 1,
    }


def _card_id(action_path_id: str, rank: int) -> str:
    return f"launchpad_{rank:02d}_{action_path_id}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
