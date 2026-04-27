from __future__ import annotations

"""
Centralized policy math for feasibility constraints (no block / risk-budget architecture).

Single source of truth for:
- per-asset RC caps (global §1 from docs/docs/feasibility_constraints_spec.md §1 only)
- uniform max weight per risk asset (§2 — same cap for every name in the risk universe)

Formulas implement docs/docs/feasibility_constraints_spec.md where still applicable.
"""

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
