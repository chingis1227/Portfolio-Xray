"""Load Block 4 v2 scoring thresholds from ``config/block_4_thresholds.yml``."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

THRESHOLDS_VERSION = "block_4_thresholds_v1"
DEFAULT_THRESHOLDS_PATH = Path(__file__).resolve().parents[2] / "config" / "block_4_thresholds.yml"

_DEFAULT_STRESS_MULTIPLIERS = {
    "confirmed": 1.12,
    "pre_stress_only": 0.88,
    "contradicted": 0.55,
    "unavailable": 0.95,
}


@dataclass(frozen=True)
class ActivationThresholds:
    raw_score_min: float = 0.35
    min_required_signal_strength: float = 0.12


@dataclass(frozen=True)
class ScoringWeights:
    required: float = 0.55
    supporting: float = 0.30
    required_peak: float = 0.15
    negative_penalty_factor: float = 0.18
    negative_block_threshold: float = 0.55


@dataclass(frozen=True)
class MaterialityBands:
    high_min: float = 0.65
    medium_min: float = 0.45
    low_min: float = 0.25


@dataclass(frozen=True)
class SignalStrengthThresholds:
    vol_baseline: float = 0.10
    vol_range: float = 0.12
    max_drawdown_floor: float = 0.08
    max_drawdown_range: float = 0.18
    sharpe_reference: float = 0.55
    beta_reference: float = 0.65
    beta_range: float = 0.55
    top_weight_baseline_pct: float = 12.0
    top_weight_range_pct: float = 35.0
    rc_top1_baseline_pct: float = 20.0
    rc_top1_range_pct: float = 35.0
    offset_coverage_strong: float = 0.55
    stress_loss_floor: float = 0.05
    stress_loss_range: float = 0.15
    es_95_floor: float = 0.012
    es_95_range: float = 0.018
    rates_loss_floor: float = 0.03
    rates_loss_range: float = 0.12
    severity_boost_high: float = 0.15
    severity_boost_medium: float = 0.08


@dataclass(frozen=True)
class SeverityThresholds:
    high_decision_score_min: float = 0.60
    medium_decision_score_min: float = 0.42
    high_requires_materiality: str = "high"
    inactive_band: str = "unavailable"
    monitor_band: str = "low"
    evidence_quality_band: str = "high"
    conflict_band: str = "medium"


@dataclass(frozen=True)
class ConfidenceThresholds:
    confirmed_stress_tier: str = "high"
    pre_stress_only_tier: str = "low"
    contradicted_tier: str = "low"
    unavailable_stress_tier: str = "medium"
    legacy_fallback_cap: str = "medium"
    partial_data_cap: str = "low"
    data_trust_cap: str = "low"
    inactive_tier: str = "low"
    acceptable_tier: str = "medium"


@dataclass(frozen=True)
class Block4Thresholds:
    version: str = THRESHOLDS_VERSION
    ruleset_version: str = "block_4_v2_2026_06"
    activation: ActivationThresholds = field(default_factory=ActivationThresholds)
    scoring_weights: ScoringWeights = field(default_factory=ScoringWeights)
    materiality_bands: MaterialityBands = field(default_factory=MaterialityBands)
    stress_confirmation_multipliers: dict[str, float] = field(default_factory=lambda: dict(_DEFAULT_STRESS_MULTIPLIERS))
    signal_strength: SignalStrengthThresholds = field(default_factory=SignalStrengthThresholds)
    severity: SeverityThresholds = field(default_factory=SeverityThresholds)
    confidence: ConfidenceThresholds = field(default_factory=ConfidenceThresholds)


def _merge_section(raw: dict[str, Any], cls: type, defaults: Any) -> Any:
    if not raw:
        return defaults
    valid = {item.name for item in fields(defaults)}
    kwargs = {key: raw[key] for key in raw if key in valid}
    base = {item.name: getattr(defaults, item.name) for item in fields(defaults)}
    base.update(kwargs)
    return cls(**base)


def parse_block_4_thresholds(data: dict[str, Any] | None) -> Block4Thresholds:
    """Parse YAML dict into ``Block4Thresholds`` with defaults for missing keys."""
    raw = data if isinstance(data, dict) else {}
    defaults = Block4Thresholds()
    multipliers = raw.get("stress_confirmation_multipliers")
    if isinstance(multipliers, dict):
        merged = dict(defaults.stress_confirmation_multipliers)
        merged.update({str(k): float(v) for k, v in multipliers.items()})
    else:
        merged = dict(defaults.stress_confirmation_multipliers)
    return Block4Thresholds(
        version=str(raw.get("version") or defaults.version),
        ruleset_version=str(raw.get("ruleset_version") or defaults.ruleset_version),
        activation=_merge_section(raw.get("activation") or {}, ActivationThresholds, defaults.activation),
        scoring_weights=_merge_section(raw.get("scoring_weights") or {}, ScoringWeights, defaults.scoring_weights),
        materiality_bands=_merge_section(raw.get("materiality_bands") or {}, MaterialityBands, defaults.materiality_bands),
        stress_confirmation_multipliers=merged,
        signal_strength=_merge_section(raw.get("signal_strength") or {}, SignalStrengthThresholds, defaults.signal_strength),
        severity=_merge_section(raw.get("severity") or {}, SeverityThresholds, defaults.severity),
        confidence=_merge_section(raw.get("confidence") or {}, ConfidenceThresholds, defaults.confidence),
    )


def load_block_4_thresholds(path: Path | str | None = None) -> Block4Thresholds:
    """Load thresholds YAML; fall back to embedded defaults when file is missing."""
    target = Path(path) if path is not None else DEFAULT_THRESHOLDS_PATH
    if not target.is_file():
        return Block4Thresholds()
    with target.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return parse_block_4_thresholds(data)


@lru_cache(maxsize=1)
def get_block_4_thresholds() -> Block4Thresholds:
    return load_block_4_thresholds()
