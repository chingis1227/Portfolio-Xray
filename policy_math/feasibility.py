from __future__ import annotations

"""
Centralized policy math for feasibility constraints.

Single source of truth for:
- uniform max weight per risk asset (feasibility_constraints_spec §2 — same cap for every name)

RC caps were removed from the construction layer; RC_vol remains a diagnostic metric only.
"""

DEFAULT_MIN_WEIGHT = 0.01


def resolve_max_weight_per_asset_cap(n_total: int) -> float:
    """
    Uniform upper bound on weight for each risk asset (feasibility_constraints_spec §2).

    - If N <= 0: 0.0
    - If N <= 3: 0.40
    - Else: min(0.25, max(0.10, 2.5 / N))
    """
    if n_total <= 0:
        return 0.0
    if n_total <= 3:
        return 0.40
    return float(min(0.25, max(0.10, 2.5 / n_total)))
