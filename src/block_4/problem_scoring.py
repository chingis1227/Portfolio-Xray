"""Block 4 v2 evidence-to-problem scoring (Session 04–05).

Maps extracted evidence signals to taxonomy problem ids using required /
supporting / negative signal lists from ``PROBLEM_REGISTRY``. Thresholds load
from ``config/block_4_thresholds.yml`` (Session 05). Severity and confidence
bands are applied via ``severity_confidence.apply_severity_and_confidence``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.block_4.evidence_extraction import EvidenceExtractionResult, EvidenceSignal
from src.block_4.problem_taxonomy import (
    PROBLEM_REGISTRY,
    ProblemDefinition,
    all_problem_ids,
    is_root_cause_problem,
    outcome_problem_ids,
)
from src.block_4.thresholds import Block4Thresholds, get_block_4_thresholds

SCORING_RULESET_VERSION = "block_4_v3_scoring_heuristic_v1"
ACTIVATION_RAW_THRESHOLD = 0.35  # re-export default; runtime uses config

# Problems where required_evidence_signals are OR-groups (at least one group fully satisfied).
_REQUIRED_OR_GROUPS: dict[str, tuple[tuple[str, ...], ...]] = {
    "weak_crisis_resilience": (
        ("worst_synthetic_scenario",),
        ("worst_historical_scenario",),
    ),
    "high_equity_beta": (
        ("beta_portfolio", "beta_eq"),
        ("beta_eq",),
        ("beta_portfolio",),
    ),
    "high_concentration": (
        ("top1_weight_pct", "top3_weight_pct"),
        ("top1_weight_pct",),
        ("top3_weight_pct",),
    ),
    "poor_diversification": (
        ("duplicate_exposure", "correlation_concentration"),
        ("duplicate_exposure",),
        ("correlation_concentration",),
    ),
    "weak_hedge_behavior": (
        ("offset_coverage_ratio", "protection_status"),
        ("offset_coverage_ratio",),
        ("protection_status",),
    ),
    "high_tail_risk": (
        ("es_95", "tail_risk_alert"),
        ("es_95",),
        ("tail_risk_alert",),
    ),
    "credit_liquidity_fragility": (
        ("credit_liquidity_risk_alert", "block_2_6_credit_shock"),
        ("credit_liquidity_risk_alert",),
        ("block_2_6_credit_shock",),
    ),
    "duration_rates_vulnerability": (
        ("duration_concentration_alert", "fixed_income_weight"),
        ("duration_concentration_alert",),
    ),
    "poor_rates_up_behavior": (
        ("block_2_6_rates_shock", "rates_scenario_loss"),
        ("block_2_6_rates_shock",),
        ("rates_scenario_loss",),
    ),
    "low_return_risk_efficiency": (
        ("sharpe", "sortino"),
        ("sharpe",),
        ("sortino",),
    ),
}

_STRESS_SIGNALS = frozenset(
    {
        "offset_coverage_ratio",
        "protection_status",
        "main_hedge_gap",
        "worst_synthetic_scenario",
        "worst_historical_scenario",
        "stress_diagnosis",
        "rates_scenario_loss",
        "rates_shock_stress",
        "liquidity_shock_stress",
        "immaterial_stress_loss",
        "stress_loss_immaterial",
        "strong_offset_coverage",
        "strong_hedge_offset",
        "rates_hedge_present",
    }
)

_SPECIAL_PROBLEM_IDS = frozenset(outcome_problem_ids())

_ACTIONABLE_PROBLEM_IDS = frozenset(
    pid for pid in all_problem_ids() if pid not in _SPECIAL_PROBLEM_IDS
)


@dataclass(frozen=True)
class ProblemScoringBlock:
    raw_score: float
    decision_score: float
    stress_confirmation: str
    materiality: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_score": round(self.raw_score, 3),
            "decision_score": round(self.decision_score, 3),
            "stress_confirmation": self.stress_confirmation,
            "materiality": self.materiality,
        }


@dataclass
class ProblemScoreRow:
    problem_id: str
    scoring: ProblemScoringBlock
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    negative_evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    required_met: bool = False
    activated: bool = False
    severity: str = "unavailable"
    confidence: str = "low"
    reject_reason_code: str | None = None
    reject_reason_en: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "problem_id": self.problem_id,
            "scoring": self.scoring.to_dict(),
            "evidence_refs": self.evidence_refs,
            "negative_evidence_refs": self.negative_evidence_refs,
            "required_met": self.required_met,
            "activated": self.activated,
            "severity": self.severity,
            "confidence": self.confidence,
        }
        if self.reject_reason_code is not None:
            out["reject_reason_code"] = self.reject_reason_code
        if self.reject_reason_en is not None:
            out["reject_reason_en"] = self.reject_reason_en
        return out


@dataclass
class ProblemScoringResult:
    rows: dict[str, ProblemScoreRow] = field(default_factory=dict)
    activated_problem_ids: tuple[str, ...] = ()
    actionable_activated_ids: tuple[str, ...] = ()
    conflicting_signal_bundle: bool = False
    no_material_problem: bool = False
    problems_evaluated: int = 0

    def get_row(self, problem_id: str) -> ProblemScoreRow | None:
        return self.rows.get(problem_id)

    def activated_rows(self) -> list[ProblemScoreRow]:
        return [self.rows[pid] for pid in self.activated_problem_ids if pid in self.rows]


def score_problems(
    evidence: EvidenceExtractionResult,
    thresholds: Block4Thresholds | None = None,
) -> ProblemScoringResult:
    """Score all taxonomy problems against extracted evidence signals."""
    cfg = thresholds or get_block_4_thresholds()
    conflicting = _detect_conflicting_signals(evidence)
    rows: dict[str, ProblemScoreRow] = {}

    for problem_id in all_problem_ids():
        defn = PROBLEM_REGISTRY[problem_id]
        if problem_id == "evidence_insufficient_data_quality":
            rows[problem_id] = _score_data_quality_problem(evidence, defn, cfg)
        elif problem_id == "goal_risk_conflict":
            rows[problem_id] = _score_goal_risk_conflict_problem(evidence, defn, cfg)
        elif problem_id == "mixed_evidence_no_action":
            rows[problem_id] = _score_conflicting_problem(evidence, defn, conflicting, cfg)
        elif problem_id == "current_portfolio_acceptable":
            continue
        else:
            rows[problem_id] = _score_standard_problem(evidence, defn, cfg)

    actionable_activated = tuple(
        pid
        for pid in _ACTIONABLE_PROBLEM_IDS
        if pid in rows and rows[pid].activated
    )
    actionable_activated = tuple(
        sorted(actionable_activated, key=lambda pid: (-rows[pid].scoring.decision_score, pid))
    )

    root_cause_activated = tuple(
        pid for pid in actionable_activated if is_root_cause_problem(pid)
    )
    no_material = (
        len(actionable_activated) == 0
        and not evidence.has_signal("data_trust_failure")
        and not conflicting
    )
    rows["current_portfolio_acceptable"] = _score_acceptable_problem(
        evidence,
        PROBLEM_REGISTRY["current_portfolio_acceptable"],
        no_material=no_material,
        thresholds=cfg,
    )

    activated: list[str] = []
    if rows["evidence_insufficient_data_quality"].activated:
        activated.append("evidence_insufficient_data_quality")
    elif rows["goal_risk_conflict"].activated:
        activated.append("goal_risk_conflict")
    elif conflicting and not root_cause_activated:
        activated.append("mixed_evidence_no_action")
    else:
        activated.extend(actionable_activated)
        if no_material and rows["current_portfolio_acceptable"].activated:
            activated.append("current_portfolio_acceptable")

    for pid in _ACTIONABLE_PROBLEM_IDS:
        row = rows.get(pid)
        if row is None or row.activated:
            continue
        if row.required_met and row.scoring.raw_score < cfg.activation.raw_score_min:
            row.reject_reason_code = "below_activation_threshold"
            row.reject_reason_en = (
                f"Evidence for {PROBLEM_REGISTRY[pid].label_en} is below the activation threshold."
            )
        elif row.evidence_refs and not row.required_met:
            row.reject_reason_code = "required_evidence_incomplete"
            row.reject_reason_en = (
                f"Required evidence for {PROBLEM_REGISTRY[pid].label_en} is incomplete."
            )

    result = ProblemScoringResult(
        rows=rows,
        activated_problem_ids=tuple(activated),
        actionable_activated_ids=actionable_activated,
        conflicting_signal_bundle=conflicting,
        no_material_problem=no_material,
        problems_evaluated=len(all_problem_ids()),
    )
    from src.block_4.severity_confidence import apply_severity_and_confidence

    apply_severity_and_confidence(result, evidence, cfg)
    return result


def _score_standard_problem(
    evidence: EvidenceExtractionResult,
    defn: ProblemDefinition,
    thresholds: Block4Thresholds,
) -> ProblemScoreRow:
    required_signals, required_met = _resolve_required_signals(evidence, defn)
    supporting_signals = _collect_signals(evidence, defn.supporting_evidence_signals)
    negative_signals = _collect_signals(evidence, defn.negative_evidence_signals)

    weights = thresholds.scoring_weights
    activation = thresholds.activation

    required_strengths = [_signal_strength(sig, thresholds) for sig in required_signals]
    if required_met and required_strengths:
        if any(strength < activation.min_required_signal_strength for strength in required_strengths):
            required_met = max(required_strengths) >= activation.min_required_signal_strength

    supporting_strengths = [_signal_strength(sig, thresholds) for sig in supporting_signals]
    negative_strengths = [_signal_strength(sig, thresholds) for sig in negative_signals]

    if required_met and required_strengths:
        required_avg = sum(required_strengths) / len(required_strengths)
        support_avg = (
            sum(supporting_strengths) / len(supporting_strengths) if supporting_strengths else 0.0
        )
        raw = (
            weights.required * required_avg
            + weights.supporting * support_avg
            + weights.required_peak * max(required_strengths)
        )
    elif required_strengths:
        raw = 0.25 * (sum(required_strengths) / len(required_strengths))
    else:
        raw = 0.0

    raw = _clamp(raw, 0.0, 1.0)
    negative_penalty = sum(negative_strengths) * weights.negative_penalty_factor
    negative_block = any(strength >= weights.negative_block_threshold for strength in negative_strengths)

    stress_confirmation = _stress_confirmation(
        required_signals + supporting_signals,
        negative_signals,
    )
    decision = raw * _stress_multiplier(stress_confirmation, thresholds) - negative_penalty
    decision = _clamp(decision, 0.0, 1.0)

    materiality = _materiality_band(raw if required_met else min(raw, 0.35), thresholds)
    activated = (
        required_met
        and raw >= activation.raw_score_min
        and not negative_block
    )

    positive_refs = _build_evidence_refs(
        required_signals + supporting_signals,
        defn.problem_id,
        role="supporting",
        thresholds=thresholds,
    )
    negative_refs = _build_evidence_refs(
        negative_signals,
        defn.problem_id,
        role="negative",
        thresholds=thresholds,
    )

    row = ProblemScoreRow(
        problem_id=defn.problem_id,
        scoring=ProblemScoringBlock(
            raw_score=raw,
            decision_score=decision,
            stress_confirmation=stress_confirmation,
            materiality=materiality,
        ),
        evidence_refs=positive_refs,
        negative_evidence_refs=negative_refs,
        required_met=required_met,
        activated=activated,
    )
    if required_met and not activated and negative_block:
        row.reject_reason_code = "contradicted_by_negative_evidence"
        row.reject_reason_en = (
            f"Contradicting evidence weakens the {defn.label_en} hypothesis."
        )
    return row


def _score_data_quality_problem(
    evidence: EvidenceExtractionResult,
    defn: ProblemDefinition,
    thresholds: Block4Thresholds,
) -> ProblemScoreRow:
    trust_signals = _collect_signals(evidence, defn.required_evidence_signals)
    support_signals = _collect_signals(evidence, defn.supporting_evidence_signals)
    all_signals = trust_signals + support_signals
    hard_trust_failure = evidence.has_signal("data_trust_failure")
    partial_with_missing_stress = (
        evidence.has_signal("partial_sections")
        and evidence.has_signal("stress_block_unavailable")
    )
    required_met = hard_trust_failure or partial_with_missing_stress
    raw = 0.95 if hard_trust_failure else 0.75 if partial_with_missing_stress else 0.0
    activated = required_met
    refs = _build_evidence_refs(all_signals, defn.problem_id, role="supporting", thresholds=thresholds)
    return ProblemScoreRow(
        problem_id=defn.problem_id,
        scoring=ProblemScoringBlock(
            raw_score=raw,
            decision_score=raw,
            stress_confirmation="unavailable",
            materiality="high" if activated else "none",
        ),
        evidence_refs=refs,
        required_met=required_met,
        activated=activated,
    )


def _score_conflicting_problem(
    evidence: EvidenceExtractionResult,
    defn: ProblemDefinition,
    conflicting: bool,
    thresholds: Block4Thresholds,
) -> ProblemScoreRow:
    required_met = conflicting
    raw = 0.9 if conflicting else 0.0
    activated = conflicting
    bundle_signal = EvidenceSignal(
        signal="conflicting_signal_bundle",
        value={"conflict_detected": conflicting},
        source_block="block_4_scoring",
        source_artifact="portfolio_xray.json",
        evidence_path="primary",
        interpretation_en="Material contradictions detected across pre-stress and stress evidence.",
    )
    refs = (
        _build_evidence_refs([bundle_signal], defn.problem_id, role="supporting", thresholds=thresholds)
        if conflicting
        else []
    )
    return ProblemScoreRow(
        problem_id=defn.problem_id,
        scoring=ProblemScoringBlock(
            raw_score=raw,
            decision_score=raw,
            stress_confirmation="contradicted" if conflicting else "unavailable",
            materiality="high" if activated else "none",
        ),
        evidence_refs=refs,
        required_met=required_met,
        activated=activated,
    )


def _score_goal_risk_conflict_problem(
    evidence: EvidenceExtractionResult,
    defn: ProblemDefinition,
    thresholds: Block4Thresholds,
) -> ProblemScoreRow:
    """Score the Client Fit objective-consistency exception.

    This is deliberately separate from standard portfolio-structure scoring: a Client Fit
    breach can support or contradict existing diagnoses, but only the explicit
    ``goal_risk_conflict`` signal can activate this primary outcome.
    """

    required = _collect_signals(evidence, defn.required_evidence_signals)
    support = _collect_signals(evidence, defn.supporting_evidence_signals)
    required_met = bool(required)
    raw = 0.9 if required_met else 0.0
    refs = _build_evidence_refs(required + support, defn.problem_id, role="supporting", thresholds=thresholds)
    return ProblemScoreRow(
        problem_id=defn.problem_id,
        scoring=ProblemScoringBlock(
            raw_score=raw,
            decision_score=raw,
            stress_confirmation="unavailable",
            materiality="high" if required_met else "none",
        ),
        evidence_refs=refs,
        required_met=required_met,
        activated=required_met,
    )


def _score_acceptable_problem(
    evidence: EvidenceExtractionResult,
    defn: ProblemDefinition,
    *,
    no_material: bool,
    thresholds: Block4Thresholds,
) -> ProblemScoreRow:
    required_met = no_material
    raw = 0.85 if no_material else 0.0
    activated = no_material
    bundle_signal = EvidenceSignal(
        signal="no_material_problem",
        value={"actionable_problems_activated": 0},
        source_block="block_4_scoring",
        source_artifact="portfolio_xray.json",
        evidence_path="primary",
        interpretation_en="No material portfolio problem exceeded activation thresholds.",
    )
    refs = (
        _build_evidence_refs([bundle_signal], defn.problem_id, role="supporting", thresholds=thresholds)
        if no_material
        else []
    )
    return ProblemScoreRow(
        problem_id=defn.problem_id,
        scoring=ProblemScoringBlock(
            raw_score=raw,
            decision_score=raw,
            stress_confirmation="unavailable",
            materiality="low" if activated else "none",
        ),
        evidence_refs=refs,
        required_met=required_met,
        activated=activated,
    )


def _detect_conflicting_signals(evidence: EvidenceExtractionResult) -> bool:
    if evidence.has_signal("low_stress_loss_with_high_vol"):
        if evidence.has_signal("worst_synthetic_scenario") or evidence.has_signal("vol_annual"):
            return True
    if evidence.has_signal("stress_loss_immaterial") and evidence.has_signal("worst_synthetic_scenario"):
        syn = evidence.get_signals("worst_synthetic_scenario")
        if syn:
            loss = _nested_float(syn[0].value, "portfolio_loss_pct")
            if loss is not None and loss <= -0.08:
                return True
    if evidence.has_signal("strong_hedge_offset") or evidence.has_signal("strong_offset_coverage"):
        prot = evidence.get_signals("protection_status")
        if prot and str(prot[0].value) in {"weak_protection", "no_protection", "weak", "mostly_weak_protection"}:
            return True
    if evidence.has_signal("drawdown_recovered_quickly"):
        dd = evidence.get_signals("max_drawdown")
        worst_hist = evidence.get_signals("worst_historical_scenario")
        dd_val = _as_float(dd[0].value) if dd else None
        hist_val = _nested_float(worst_hist[0].value, "drawdown_pct", "portfolio_loss_pct") if worst_hist else None
        if dd_val is not None and dd_val <= -0.18 and hist_val is not None and hist_val <= -0.18:
            return True
    return False


def _resolve_required_signals(
    evidence: EvidenceExtractionResult,
    defn: ProblemDefinition,
) -> tuple[list[EvidenceSignal], bool]:
    or_groups = _REQUIRED_OR_GROUPS.get(defn.problem_id)
    if or_groups is None:
        signals = _collect_signals(evidence, defn.required_evidence_signals)
        met = len(signals) == len(defn.required_evidence_signals) and bool(defn.required_evidence_signals)
        return signals, met

    for group in or_groups:
        group_signals = _collect_signals(evidence, group)
        if len(group_signals) == len(group):
            return group_signals, True
    partial = _collect_signals(evidence, defn.required_evidence_signals)
    return partial, False


def _collect_signals(
    evidence: EvidenceExtractionResult,
    names: tuple[str, ...],
) -> list[EvidenceSignal]:
    out: list[EvidenceSignal] = []
    for name in names:
        out.extend(evidence.get_signals(name))
    return out


def _signal_strength(signal: EvidenceSignal, thresholds: Block4Thresholds) -> float:
    name = signal.signal
    value = signal.value
    t = thresholds.signal_strength
    severity_boost = {
        "high": t.severity_boost_high,
        "medium": t.severity_boost_medium,
        "low": 0.0,
    }.get(str(signal.severity or "").lower(), 0.0)

    if name == "vol_annual":
        vol = _as_float(value)
        return _clamp((vol - t.vol_baseline) / t.vol_range, 0.0, 1.0) + severity_boost if vol is not None else 0.4
    if name == "max_drawdown":
        dd = _as_float(value)
        return (
            _clamp((abs(dd) - t.max_drawdown_floor) / t.max_drawdown_range, 0.0, 1.0) + severity_boost
            if dd is not None
            else 0.4
        )
    if name in {"sharpe", "sortino"}:
        metric = _as_float(value)
        if metric is None:
            return 0.4
        return _clamp((t.sharpe_reference - metric) / t.sharpe_reference, 0.0, 1.0)
    if name in {"beta_eq", "beta_portfolio", "beta_rr", "beta_credit", "downside_beta"}:
        beta = _as_float(value)
        return (
            _clamp((abs(beta) - t.beta_reference) / t.beta_range, 0.0, 1.0) + severity_boost
            if beta is not None
            else 0.4
        )
    if name in {"top1_weight_pct", "top3_weight_pct"}:
        weight = _as_float(value)
        return (
            _clamp((weight - t.top_weight_baseline_pct) / t.top_weight_range_pct, 0.0, 1.0)
            if weight is not None
            else 0.4
        )
    if name == "rc_top1_share":
        rc = _as_float(value)
        return (
            _clamp((rc - t.rc_top1_baseline_pct) / t.rc_top1_range_pct, 0.0, 1.0)
            if rc is not None
            else 0.4
        )
    if name == "offset_coverage_ratio":
        ratio = _as_float(value)
        return (
            _clamp((t.offset_coverage_strong - ratio) / t.offset_coverage_strong, 0.0, 1.0) + severity_boost
            if ratio is not None
            else 0.4
        )
    if name == "protection_status":
        status = str(value).lower()
        if status in {"no_protection", "weak_protection", "weak", "mostly_weak_protection"}:
            return 0.85 + severity_boost
        if status in {"partial_protection"}:
            return 0.55
        return 0.2
    if name in {"worst_synthetic_scenario", "worst_historical_scenario"}:
        if isinstance(value, dict):
            loss = _nested_float(value, "portfolio_loss_pct", "drawdown_pct")
        else:
            loss = _as_float(value)
        if loss is None:
            return 0.45
        return _clamp((abs(loss) - t.stress_loss_floor) / t.stress_loss_range, 0.0, 1.0) + severity_boost
    if name == "rates_scenario_loss":
        loss = _as_float(value)
        return (
            _clamp((abs(loss) - t.rates_loss_floor) / t.rates_loss_range, 0.0, 1.0)
            if loss is not None
            else 0.4
        )
    if name in {"es_95", "var_95"}:
        tail = _as_float(value)
        return (
            _clamp((abs(tail) - t.es_95_floor) / t.es_95_range, 0.0, 1.0) + severity_boost
            if tail is not None
            else 0.4
        )
    if name == "concentration_flags":
        count = _as_float(value) or 1.0
        return _clamp(0.45 + 0.12 * count, 0.0, 1.0) + severity_boost
    if name in {"duplicate_exposure", "correlation_concentration"}:
        base = 0.65 if isinstance(value, dict) else 0.6
        if isinstance(value, dict) and str(value.get("status", "")).lower() == "high":
            base = 0.85
        return _clamp(base + severity_boost, 0.0, 1.0)
    if name.startswith("block_2_6_"):
        if isinstance(value, dict):
            score = _as_float(value.get("score_0_100"))
            if score is not None:
                return _clamp(score / 100.0, 0.0, 1.0)
        sev = str(signal.severity or "").lower()
        return {"high": 0.85, "medium": 0.6, "low": 0.3}.get(sev, 0.45)
    if name.endswith("_alert") or name in {
        "hidden_equity_beta",
        "duration_concentration_alert",
        "credit_liquidity_risk_alert",
        "weak_hedge_behavior_alert",
        "tail_risk_alert",
    }:
        if isinstance(value, dict):
            status = str(value.get("status", "")).lower()
            if status == "high":
                return 0.9
            if status == "medium":
                return 0.65
        return 0.55 + severity_boost
    if name in {"strong_offset_coverage", "strong_hedge_offset", "rates_hedge_present"}:
        return 0.7
    if name in {
        "immaterial_stress_loss",
        "stress_loss_immaterial",
        "low_stress_loss_with_high_vol",
        "drawdown_recovered_quickly",
        "broad_equal_weights",
        "low_correlation_breadth",
        "minimal_credit_weight",
        "short_duration_book",
    }:
        return 0.65
    if name in {"data_trust_failure", "partial_sections", "stress_block_unavailable"}:
        return 0.9
    if name == "goal_risk_conflict":
        return 0.9
    if name.startswith("client_fit_"):
        status = ""
        if isinstance(value, dict):
            status = str(value.get("status") or "").lower()
        elif isinstance(value, str):
            status = value.lower()
        if status in {"conflict", "breach"}:
            return 0.85 + severity_boost
        if status == "watch":
            return 0.65 + severity_boost
        if status == "fit":
            return 0.35
        return 0.45 + severity_boost
    if name in {"no_material_problem", "conflicting_signal_bundle"}:
        return 0.85
    return 0.45 + severity_boost


def _stress_confirmation(
    positive_signals: list[EvidenceSignal],
    negative_signals: list[EvidenceSignal],
) -> str:
    stress_negative = any(sig.signal in _STRESS_SIGNALS for sig in negative_signals)
    stress_positive = [sig for sig in positive_signals if sig.signal in _STRESS_SIGNALS]
    if stress_negative and stress_positive:
        return "contradicted"
    if not stress_positive:
        pre_stress = any(
            sig.evidence_path == "pre_stress_only"
            for sig in positive_signals
            if sig.signal not in _STRESS_SIGNALS
        )
        return "pre_stress_only" if pre_stress else "unavailable"
    paths = {sig.evidence_path for sig in stress_positive}
    if paths <= {"pre_stress_only"}:
        return "pre_stress_only"
    if "primary" in paths or "legacy_fallback" in paths:
        return "confirmed"
    return "unavailable"


def _stress_multiplier(stress_confirmation: str, thresholds: Block4Thresholds) -> float:
    return thresholds.stress_confirmation_multipliers.get(stress_confirmation, 0.95)


def _materiality_band(raw_score: float, thresholds: Block4Thresholds) -> str:
    bands = thresholds.materiality_bands
    if raw_score >= bands.high_min:
        return "high"
    if raw_score >= bands.medium_min:
        return "medium"
    if raw_score >= bands.low_min:
        return "low"
    return "none"


def _build_evidence_refs(
    signals: list[EvidenceSignal],
    problem_id: str,
    *,
    role: str,
    thresholds: Block4Thresholds,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for idx, sig in enumerate(signals, start=1):
        strength = _signal_strength(sig, thresholds)
        eid = f"ev_{problem_id}_{role}_{idx:02d}_{sig.signal}"
        ref: dict[str, Any] = {
            "evidence_id": eid,
            "source_block": sig.source_block,
            "source_artifact": sig.source_artifact,
            "signal": sig.signal,
            "value": sig.value,
            "normalized_score": round(strength, 3),
            "interpretation_en": sig.interpretation_en,
            "why_relevant_to_problem_en": (
                f"{'Contradicts' if role == 'negative' else 'Supports'} {problem_id} "
                f"via signal {sig.signal}."
            ),
            "evidence_path": sig.evidence_path,
        }
        if sig.severity is not None:
            ref["severity"] = sig.severity
        if sig.confidence is not None:
            ref["confidence"] = sig.confidence
        if sig.linked_assets:
            ref["linked_assets"] = list(sig.linked_assets)
        if sig.limitation_en is not None:
            ref["limitation_en"] = sig.limitation_en
        if sig.raw_field_path is not None:
            ref["raw_field_path"] = sig.raw_field_path
        refs.append(ref)
    return refs


def _nested_float(value: Any, *keys: str) -> float | None:
    if isinstance(value, dict):
        for key in keys:
            parsed = _as_float(value.get(key))
            if parsed is not None:
                return parsed
    return _as_float(value)


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
