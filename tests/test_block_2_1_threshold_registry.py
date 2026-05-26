"""Drift guard for Block 2.1 allocation concentration thresholds (spec §2.1.2)."""
from __future__ import annotations

from src.block_2_1_asset_allocation import ALLOCATION_CONCENTRATION_THRESHOLDS

CANONICAL_ALLOCATION_THRESHOLDS: dict[str, float] = {
    "top_holding_concentration_medium": 0.20,
    "top_holding_concentration_high": 0.30,
    "top3_concentration_medium": 0.50,
    "top3_concentration_high": 0.65,
    "single_asset_class_dominance_medium": 0.60,
    "single_asset_class_dominance_high": 0.75,
    "single_main_risk_factor_dominance_medium": 0.60,
    "single_main_risk_factor_dominance_high": 0.75,
    "single_region_dominance_medium": 0.70,
    "single_region_dominance_high": 0.85,
    "single_currency_dominance_medium": 0.70,
    "single_currency_dominance_high": 0.85,
}


def test_allocation_concentration_threshold_registry_matches_spec() -> None:
    assert ALLOCATION_CONCENTRATION_THRESHOLDS == CANONICAL_ALLOCATION_THRESHOLDS
