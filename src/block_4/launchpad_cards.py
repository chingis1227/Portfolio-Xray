"""Block 4 v3 Candidate Launchpad card generation.

Builds v3 launchpad cards from mapped action paths and diagnosis rows.
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

LAUNCHPAD_BUILD_RULESET_VERSION = "block_4_v3_launchpad_cards_v1"
CANDIDATE_LAUNCHPAD_V3_VERSION = "candidate_launchpad_v3"
MAX_LAUNCHPAD_CARDS = 3
MAX_SUPPRESSED_CARDS = 2

LAUNCHPAD_V3_DISCLAIMER_EN = (
    "This card suggests a hypothesis to test, not a buy or sell instruction."
)
DECISION_BOUNDARY_EN = (
    "This is not a rebalance recommendation. Actual rebalance decision is made only after "
    "Current vs Candidate Comparison and Decision Verdict."
)

_SUCCESS_CRITERIA_BY_ACTION_PATH: dict[str, tuple[str, ...]] = {
    "reduce_volatility": (
        "Lower annualized volatility without materially worsening CAGR or stress loss.",
        "Keep turnover and concentration changes explainable.",
    ),
    "reduce_drawdown_risk": (
        "Lower max drawdown versus the current portfolio.",
        "Improve recovery profile or time-under-water without creating a larger stress tail.",
    ),
    "improve_diversification": (
        "Lower top-3 risk contribution share.",
        "Lower average correlation or duplicate-exposure pressure.",
        "Avoid replacing one hidden overlap with another.",
    ),
    "reduce_concentration": (
        "Lower the relevant concentration subtype: capital, risk contribution, factor, region, currency, or duplicate exposure.",
        "Check that top-1/top-3 risk contribution falls, not only capital weight.",
    ),
    "improve_crisis_resilience": (
        "Lower worst synthetic or historical stress loss versus the current portfolio.",
        "Improve offset coverage in the main hedge-gap scenario.",
        "Reduce top stress-loss concentration without excessive turnover.",
    ),
    "reduce_equity_beta": (
        "Lower equity beta and equity-shock loss versus the current portfolio.",
        "Avoid materially worsening crisis stress losses.",
    ),
    "reduce_duration_rates_sensitivity": (
        "Lower rates-shock loss and beta_rr exposure.",
        "Keep the duration/yield trade-off explicit.",
    ),
    "improve_hedge_behavior": (
        "Improve offset coverage ratio in the main hedge-gap scenario.",
        "Increase the reliability of helped assets during stress.",
    ),
    "reduce_tail_risk": (
        "Improve ES/CVaR or tail drawdown metrics.",
        "Reduce severe drawdown frequency without hiding risk in concentration.",
    ),
    "reduce_credit_liquidity_risk": (
        "Lower credit or liquidity shock loss.",
        "Reduce fragile carry exposure without over-penalizing intentional income sleeves.",
    ),
    "improve_return_risk_balance": (
        "Improve Sharpe/Sortino-like efficiency versus current.",
        "Do not worsen stress resilience enough to offset the efficiency gain.",
    ),
    "compare_against_simple_benchmark": (
        "Create a transparent reference point, not an action recommendation.",
        "Use the comparison to clarify whether the current diagnosis is material.",
    ),
    "keep_current_portfolio_and_monitor": (
        "No material deterioration in monitored risks.",
        "Re-open candidate testing only if a root-cause diagnosis becomes material.",
    ),
    "evidence_insufficient_do_not_act_yet": (
        "Resolve data-quality blockers or monitor mixed evidence before any rebalance test.",
        "Confirm that a root-cause diagnosis is material before launching candidates.",
    ),
    "test_another_candidate": (
        "Define a specific hypothesis before generating a candidate.",
        "Do not treat exploration as an allocation recommendation.",
    ),
}

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
        "hierarchical_risk_parity",
        "maximum_diversification",
        "minimum_cvar",
        "minimum_variance",
        "risk_parity",
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
    """Build v3 launchpad cards from action-path mapping output."""
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


def build_candidate_launchpad_v3_document(
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
    """Assemble top-level ``candidate_launchpad_v3`` document."""
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
        "schema_version": CANDIDATE_LAUNCHPAD_V3_VERSION,
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
    suggested_methods = [
        _suggested_method_row(mid, action.action_path_id) for mid in method_ids
    ]

    title = action_path.label_en
    if defn is not None and action.action_path_id == problem_row.get("suggested_action_path_id"):
        title = defn.launchpad_card_title_en

    card: dict[str, Any] = {
        "card_id": _card_id(action.action_path_id, priority_rank),
        "title": title,
        "goal": action_path.goal_label,
        "description": action_path.launchpad_description_en,
        "source_diagnosis_id": source_problem_id,
        "source_problem_id": source_problem_id,
        "source_problem_label": (problem_row or {}).get("label_en"),
        "rationale": _card_rationale(problem_row),
        "hypothesis_to_test": _hypothesis_to_test(action_path.label_en, problem_row),
        "card_type": _card_type(action.action_path_id),
        "launch_status": _launch_status(action.action_path_id),
        "is_rebalance_recommendation": False,
        "why_this_test": _why_this_test(action.action_path_id, problem_row),
        "suggested_methods": suggested_methods,
        "success_criteria": list(_success_criteria(action.action_path_id)),
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
        "tradeoff_to_watch": (
            defn.launchpad_tradeoff_en if defn is not None else _default_tradeoff(action.action_path_id)
        ),
        "not_a_recommendation_disclaimer_en": LAUNCHPAD_V3_DISCLAIMER_EN,
        "decision_boundary": DECISION_BOUNDARY_EN,
        "when_to_skip_this_test_en": (
            defn.launchpad_skip_when_en if defn is not None else "Skip when the diagnosis no longer applies."
        ),
        "when_to_skip": (
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
    if launchpad_suppressed and action_path_id != "compare_against_simple_benchmark":
        return ()

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


def _suggested_method_row(method_id: str, action_path_id: str) -> dict[str, str]:
    role = (
        "reference_benchmark"
        if action_path_id == "compare_against_simple_benchmark"
        else "targeted_hypothesis"
    )
    row = {"candidate_method_id": method_id, "method_role": role}
    if action_path_id == "compare_against_simple_benchmark":
        row["why_this_method"] = _why_reference_method(method_id)
    return row


def _why_reference_method(method_id: str) -> str:
    if method_id == "equal_weight":
        return "Equal Weight is used as a simple concentration benchmark."
    if method_id == "risk_parity":
        return "Risk Parity is used as a risk-distribution benchmark."
    return "This method is used as a transparent reference benchmark."


def _card_type(action_path_id: str) -> str:
    if action_path_id == "compare_against_simple_benchmark":
        return "reference_benchmark_test"
    if action_path_id in _NO_USER_ACTION_PATH_IDS:
        return "monitor_or_data_step"
    return "targeted_hypothesis_test"


def _launch_status(action_path_id: str) -> str:
    if action_path_id == "compare_against_simple_benchmark":
        return "reference_test"
    if action_path_id in _NO_USER_ACTION_PATH_IDS:
        return "monitor_or_resolve_data"
    return "hypothesis_test"


def _why_this_test(action_path_id: str, problem_row: dict[str, Any] | None) -> str:
    if action_path_id == "compare_against_simple_benchmark":
        return (
            "Immediate rebalance is not justified by current evidence. However, a reference "
            "comparison against Equal Weight and Risk Parity can test whether the current "
            "allocation is materially better than simple alternatives."
        )
    label = str((problem_row or {}).get("label_en") or "the primary diagnosis")
    return f"This test is linked to the current diagnosis: {label}."


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


def _hypothesis_to_test(action_label: str, problem_row: dict[str, Any] | None) -> str:
    label = str((problem_row or {}).get("label_en") or "the current diagnosis").lower()
    return (
        f"Test whether {action_label.lower()} improves {label} enough to beat the current portfolio "
        "on the stated success criteria."
    )


def _success_criteria(action_path_id: str) -> tuple[str, ...]:
    return success_criteria_for_action_path(action_path_id)


def success_criteria_for_action_path(action_path_id: str) -> tuple[str, ...]:
    return _SUCCESS_CRITERIA_BY_ACTION_PATH.get(
        action_path_id,
        (
            "Improve the diagnosed risk without creating a larger unaddressed risk.",
            "Keep implementation trade-offs explicit.",
        ),
    )


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
        "source_diagnosis_id": primary_problem_id,
        "source_problem_id": primary_problem_id,
        "source_problem_label": primary_row.get("label_en"),
        "rationale": _card_rationale(primary_row),
        "hypothesis_to_test": _hypothesis_to_test("keeping the current portfolio and monitoring", primary_row),
        "card_type": "monitor_or_data_step",
        "launch_status": "monitor_or_resolve_data",
        "is_rebalance_recommendation": False,
        "why_this_test": "Monitoring is appropriate until evidence justifies a specific diagnostic test.",
        "suggested_methods": [],
        "success_criteria": list(_success_criteria("keep_current_portfolio_and_monitor")),
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
        "tradeoff_to_watch": _default_tradeoff("keep_current_portfolio_and_monitor"),
        "not_a_recommendation_disclaimer_en": LAUNCHPAD_V3_DISCLAIMER_EN,
        "decision_boundary": DECISION_BOUNDARY_EN,
        "when_to_skip_this_test_en": (
            defn.launchpad_skip_when_en if defn else "N/A - this is the monitor path."
        ),
        "when_to_skip": (
            defn.launchpad_skip_when_en if defn else "N/A - this is the monitor path."
        ),
        "priority_rank": 1,
    }


def _card_id(action_path_id: str, rank: int) -> str:
    return f"launchpad_{rank:02d}_{action_path_id}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


