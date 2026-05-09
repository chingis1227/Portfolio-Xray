"""
Default risk-budget presets (asset-class buckets).

Each preset maps canonical bucket names to targets that sum to 1.0.
See docs/exec_plans/2026-05-09_risk_budgeting_baseline_v1.md.
"""
from __future__ import annotations

from typing import Final

# Canonical bucket keys for class-level risk budgeting (and presets).
RISK_BUDGET_BUCKET_KEYS: Final[tuple[str, ...]] = (
    "equity",
    "fixed_income",
    "commodity",
    "cash",
    "crypto",
    "alternatives",
    "real_assets",
    "credit",
    "inflation_linked",
)

RISK_BUDGET_PRESET_NAMES: Final[tuple[str, ...]] = (
    "defensive",
    "balanced",
    "growth",
    "inflation_protection",
    "alternative_diversified",
)

# Numerically stable tables (each sums to 1.0).
RISK_BUDGET_PRESETS: Final[dict[str, dict[str, float]]] = {
    "defensive": {
        "equity": 0.15,
        "fixed_income": 0.45,
        "commodity": 0.05,
        "cash": 0.12,
        "crypto": 0.0,
        "alternatives": 0.08,
        "real_assets": 0.05,
        "credit": 0.05,
        "inflation_linked": 0.05,
    },
    "balanced": {
        "equity": 0.40,
        "fixed_income": 0.28,
        "commodity": 0.08,
        "cash": 0.05,
        "crypto": 0.02,
        "alternatives": 0.07,
        "real_assets": 0.05,
        "credit": 0.03,
        "inflation_linked": 0.02,
    },
    "growth": {
        "equity": 0.62,
        "fixed_income": 0.15,
        "commodity": 0.07,
        "cash": 0.03,
        "crypto": 0.03,
        "alternatives": 0.05,
        "real_assets": 0.03,
        "credit": 0.01,
        "inflation_linked": 0.01,
    },
    "inflation_protection": {
        "equity": 0.25,
        "fixed_income": 0.20,
        "commodity": 0.20,
        "cash": 0.05,
        "crypto": 0.02,
        "alternatives": 0.05,
        "real_assets": 0.10,
        "credit": 0.05,
        "inflation_linked": 0.08,
    },
    "alternative_diversified": {
        "equity": 0.35,
        "fixed_income": 0.20,
        "commodity": 0.10,
        "cash": 0.05,
        "crypto": 0.05,
        "alternatives": 0.15,
        "real_assets": 0.08,
        "credit": 0.01,
        "inflation_linked": 0.01,
    },
}


def get_preset(name: str) -> dict[str, float]:
    """Return a copy of the named preset."""
    key = str(name).strip().lower()
    if key not in RISK_BUDGET_PRESETS:
        raise KeyError(f"Unknown risk budget preset: {name!r}")
    return dict(RISK_BUDGET_PRESETS[key])
