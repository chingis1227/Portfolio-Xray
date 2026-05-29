"""Block 4 v2 severity and confidence classifiers (Session 05)."""

from __future__ import annotations

from src.block_4.evidence_extraction import EvidenceExtractionResult
from src.block_4.problem_scoring import ProblemScoreRow, ProblemScoringResult
from src.block_4.thresholds import Block4Thresholds, get_block_4_thresholds

_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
_SPECIAL_SEVERITY: dict[str, str] = {
    "current_portfolio_acceptable": "monitor_band",
    "evidence_insufficient_data_quality": "evidence_quality_band",
    "evidence_insufficient_conflicting_signals": "conflict_band",
}


def apply_severity_and_confidence(
    result: ProblemScoringResult,
    evidence: EvidenceExtractionResult,
    thresholds: Block4Thresholds | None = None,
) -> ProblemScoringResult:
    """Mutate score rows in place with ``severity`` and ``confidence`` bands."""
    cfg = thresholds or get_block_4_thresholds()
    for row in result.rows.values():
        row.severity = classify_severity(row, cfg)
        row.confidence = classify_confidence(row, evidence, cfg)
    return result


def classify_severity(row: ProblemScoreRow, thresholds: Block4Thresholds) -> str:
    """Map scoring output to product severity band."""
    sev_cfg = thresholds.severity
    special_key = _SPECIAL_SEVERITY.get(row.problem_id)
    if special_key is not None:
        return str(getattr(sev_cfg, special_key))

    if not row.activated:
        return sev_cfg.inactive_band

    scoring = row.scoring
    if (
        scoring.decision_score >= sev_cfg.high_decision_score_min
        and scoring.materiality == sev_cfg.high_requires_materiality
    ):
        return "high"
    if scoring.decision_score >= sev_cfg.medium_decision_score_min:
        return "medium"
    return "low"


def classify_confidence(
    row: ProblemScoreRow,
    evidence: EvidenceExtractionResult,
    thresholds: Block4Thresholds,
) -> str:
    """Map evidence quality and stress confirmation to confidence band."""
    conf_cfg = thresholds.confidence

    if row.problem_id == "current_portfolio_acceptable" and row.activated:
        return conf_cfg.acceptable_tier
    if row.problem_id == "evidence_insufficient_data_quality" and row.activated:
        return conf_cfg.data_trust_cap
    if not row.activated:
        return conf_cfg.inactive_tier

    tiers: list[str] = [_stress_confirmation_tier(row.scoring.stress_confirmation, conf_cfg)]
    tiers.extend(_ref_confidence_tiers(row))
    tiers.append(_evidence_path_tier(row, evidence, conf_cfg))

    if evidence.legacy_sections_fallback_used:
        tiers.append(conf_cfg.legacy_fallback_cap)
    if evidence.has_signal("partial_sections"):
        tiers.append(conf_cfg.partial_data_cap)
    if evidence.has_signal("data_trust_failure"):
        tiers.append(conf_cfg.data_trust_cap)

    stress_diag = evidence.get_signals("stress_diagnosis")
    if stress_diag and stress_diag[0].confidence:
        tiers.append(_normalize_confidence_band(stress_diag[0].confidence))

    return _min_confidence_tier(tiers)


def _stress_confirmation_tier(stress_confirmation: str, conf_cfg) -> str:
    mapping = {
        "confirmed": conf_cfg.confirmed_stress_tier,
        "pre_stress_only": conf_cfg.pre_stress_only_tier,
        "contradicted": conf_cfg.contradicted_tier,
        "unavailable": conf_cfg.unavailable_stress_tier,
    }
    return mapping.get(stress_confirmation, conf_cfg.unavailable_stress_tier)


def _ref_confidence_tiers(row: ProblemScoreRow) -> list[str]:
    tiers: list[str] = []
    for ref in row.evidence_refs:
        band = ref.get("confidence")
        if band:
            tiers.append(_normalize_confidence_band(str(band)))
    return tiers


def _evidence_path_tier(
    row: ProblemScoreRow,
    evidence: EvidenceExtractionResult,
    conf_cfg,
) -> str:
    paths = {str(ref.get("evidence_path") or "") for ref in row.evidence_refs}
    if "legacy_fallback" in paths:
        return conf_cfg.legacy_fallback_cap
    if paths and paths <= {"pre_stress_only"}:
        return conf_cfg.pre_stress_only_tier
    if row.scoring.stress_confirmation == "confirmed":
        return conf_cfg.confirmed_stress_tier
    if evidence.data_quality_warnings:
        return conf_cfg.partial_data_cap
    return conf_cfg.unavailable_stress_tier


def _normalize_confidence_band(raw: str) -> str:
    value = str(raw or "").strip().lower()
    if value in _CONFIDENCE_RANK:
        return value
    if value in {"moderate"}:
        return "medium"
    return "medium"


def _min_confidence_tier(tiers: list[str]) -> str:
    if not tiers:
        return "medium"
    return min(tiers, key=lambda tier: _CONFIDENCE_RANK.get(tier, 1))
