"""
Report output profiles for ``run_portfolio_report_for_weights``.

Orchestration only: controls which presentation artifacts are written, not metric formulas.
"""

from __future__ import annotations

REPORT_PROFILE_FULL = "full"
REPORT_PROFILE_LIGHTWEIGHT = "lightweight_comparison"

REPORT_PROFILE_VALUES = frozenset({REPORT_PROFILE_FULL, REPORT_PROFILE_LIGHTWEIGHT})
DEFAULT_REPORT_PROFILE = REPORT_PROFILE_FULL


def normalize_report_profile(profile: str | None) -> str:
    normalized = (profile or DEFAULT_REPORT_PROFILE).strip().lower()
    if normalized not in REPORT_PROFILE_VALUES:
        raise ValueError(
            f"Invalid report_profile {profile!r}; expected one of: "
            f"{', '.join(sorted(REPORT_PROFILE_VALUES))}"
        )
    return normalized


def is_lightweight_comparison(profile: str | None) -> bool:
    return normalize_report_profile(profile) == REPORT_PROFILE_LIGHTWEIGHT
