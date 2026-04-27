from __future__ import annotations

"""
Centralized policy math for feasibility constraints (no block / risk-budget architecture).

Single source of truth for:
- per-asset RC caps (global §1 from docs/docs/feasibility_constraints_spec.md §1 only)
- global max-weight caps when there is no Core (all assets treated uniformly)

Formulas implement docs/docs/feasibility_constraints_spec.md where still applicable.
"""

import math
from typing import Dict


DEFAULT_MIN_WEIGHT = 0.01


def resolve_rc_asset_cap(n_assets: int) -> float:
    """
    Per-asset RC cap from feasibility_constraints_spec §1.

    - If N < 4: rc_asset_cap = 0.40
    - Else:     rc_asset_cap = min(0.25, max(0.10, 1.5 / N))
    """
    if n_assets <= 0:
        return 0.0
    if n_assets < 4:
        return 0.40
    return float(min(0.25, max(0.10, 1.5 / n_assets)))


def resolve_weight_caps(
    n_total: int,
    n_core: int,
    n_sat: int,
    equity_only: bool = False,
) -> Dict[str, float]:
    """
    Max weights for portfolio construction without Growth/Duration/Inflation blocks.

    When n_core == 0 (no designated core list), uses §4 "No Core" global cap for every asset.
    equity_only is retained for API compatibility but ignored (no equity-only RB mode).
    """
    del equity_only  # no longer used
    if n_total <= 0:
        return {"max_weight_core": 0.0, "max_weight_sat": 0.0, "max_weight_all": 0.0}

    if n_core == 0:
        if n_total <= 3:
            max_weight_all = 0.40
        else:
            max_weight_all = min(0.25, max(0.10, 2.5 / n_total))
        return {
            "max_weight_core": float(max_weight_all),
            "max_weight_sat": float(max_weight_all),
            "max_weight_all": float(max_weight_all),
        }

    max_core = min(0.35, max(0.25, 2.0 / n_total))
    if n_sat <= 2:
        max_sat = 0.40
    else:
        term = (1.0 - n_core * max_core) / (n_total - n_core) + 0.02
        max_sat = min(
            0.25,
            max(
                min(0.10, max(0.05, 2.0 / n_total)),
                term,
            ),
        )
    return {
        "max_weight_core": float(max_core),
        "max_weight_sat": float(max_sat),
        "max_weight_all": None,
    }
