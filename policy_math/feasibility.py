from __future__ import annotations

"""
Centralized policy math for feasibility and risk-budget checks.

This module is the **single source of truth** for:
- per-asset RC caps
- Growth Core/Satellite weight caps
- global max-weight caps when there is no Core
- minimum required number of assets per block to achieve a given risk budget
- basic feasibility checks for the Growth/Duration/Inflation architecture

Formulas implement docs/docs/feasibility_constraints_spec.md.
Do not duplicate these formulas elsewhere in the codebase.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


DEFAULT_MIN_WEIGHT = 0.01

# RC cap mode: "global" = §1 with N = total RiskPortfolio size; "per_block_rb_k" = variant B (RB_block/k_block × multiplier).
RC_CAP_MODE_GLOBAL = "global"
RC_CAP_MODE_PER_BLOCK_RB_K = "per_block_rb_k"
DEFAULT_RC_CAP_RB_K_MULTIPLIER = 1.25


def risk_portfolio_tickers_list(blocks: Dict[str, List[str]]) -> List[str]:
    """Same universe as get_risk_portfolio_tickers (no src import)."""
    out: List[str] = []
    for b in ("Growth", "Duration", "Inflation"):
        out.extend(blocks.get(b, []))
    for b in ("Growth_HY", "Growth_EM_debt"):
        out.extend(blocks.get(b, []))
    return out


def ticker_to_block_for_rb_local(blocks: Dict[str, List[str]]) -> Dict[str, str]:
    """Mirror src.blocks.get_ticker_to_block_for_rb (Growth_HY / Growth_EM_debt → Growth)."""
    out: Dict[str, str] = {}
    for b in ("Growth", "Duration", "Inflation"):
        for t in blocks.get(b, []):
            out[t] = b
    for b in ("Growth_HY", "Growth_EM_debt"):
        for t in blocks.get(b, []):
            out[t] = "Growth"
    return out


def count_k_block(blocks: Dict[str, List[str]], block_name: str) -> int:
    if block_name == "Growth":
        return (
            len(blocks.get("Growth", []))
            + len(blocks.get("Growth_HY", []))
            + len(blocks.get("Growth_EM_debt", []))
        )
    return len(blocks.get(block_name, []))


def resolve_rc_cap_block_rb_k(
    rb_block: float,
    k_block: int,
    multiplier: float,
    equity_only_growth: bool,
) -> float:
    """
    Variant B: per-block RC cap from risk-budget share and block size.

    cap = min(0.25, (RB_block / k_block) * multiplier), at least RB_block/k_block;
    k==1: min(RB_block, 0.25) to avoid single-asset concentration overshoot.
    Equity-Only Growth: floor max(cap, 0.15) per §6 spirit.
    """
    if k_block <= 0:
        return 0.0
    mult = float(multiplier) if multiplier > 0 else DEFAULT_RC_CAP_RB_K_MULTIPLIER
    if k_block == 1:
        return float(min(rb_block, 0.25))
    fair = rb_block / k_block
    cap = min(0.25, fair * mult)
    cap = max(cap, fair)
    if equity_only_growth:
        cap = max(cap, 0.15)
    return float(cap)


def compute_rc_caps_by_block_from_targets(
    blocks: Dict[str, List[str]],
    rb_g: float,
    rb_d: float,
    rb_i: float,
    multiplier: float,
    equity_only: bool,
) -> Dict[str, float]:
    k_g = count_k_block(blocks, "Growth")
    k_d = count_k_block(blocks, "Duration")
    k_i = count_k_block(blocks, "Inflation")
    return {
        "Growth": resolve_rc_cap_block_rb_k(rb_g, k_g, multiplier, equity_only),
        "Duration": resolve_rc_cap_block_rb_k(rb_d, k_d, multiplier, False),
        "Inflation": resolve_rc_cap_block_rb_k(rb_i, k_i, multiplier, False),
    }


def build_rc_cap_per_ticker(
    blocks: Dict[str, List[str]],
    rc_block_targets: Dict[str, float] | None,
    rc_asset_cap_pct: float | None,
    rc_cap_mode: str,
    rc_cap_rb_k_multiplier: float,
    n_total_for_global: int,
) -> Dict[str, float]:
    """
    Per-ticker RC_vol cap (share of RiskPortfolio variance) for diagnostics and enforcement.

    - Explicit rc_asset_cap_pct > 0: that value for every risk ticker.
    - per_block_rb_k: cap from RB_block/k_block × multiplier per main block (HY/EM → Growth).
    - else: global §1 from n_total_for_global and RB_growth (equity-only floor).
    """
    tickers = risk_portfolio_tickers_list(blocks)
    ttb = ticker_to_block_for_rb_local(blocks)
    if not tickers:
        return {}

    if rc_asset_cap_pct is not None and rc_asset_cap_pct > 0:
        c = float(rc_asset_cap_pct)
        return {t: c for t in tickers}

    rb = rc_block_targets or {}
    rb_g = float(rb.get("Growth", 1.0 / 3))
    rb_d = float(rb.get("Duration", 1.0 / 3))
    rb_i = float(rb.get("Inflation", 1.0 / 3))
    s = rb_g + rb_d + rb_i
    if s <= 1e-12:
        rb_g, rb_d, rb_i = 1.0 / 3, 1.0 / 3, 1.0 / 3
    else:
        rb_g, rb_d, rb_i = rb_g / s, rb_d / s, rb_i / s
    equity_only = rb_g >= 0.90

    if rc_cap_mode == RC_CAP_MODE_PER_BLOCK_RB_K:
        caps_b = compute_rc_caps_by_block_from_targets(
            blocks, rb_g, rb_d, rb_i, rc_cap_rb_k_multiplier, equity_only
        )
        return {t: caps_b[ttb[t]] for t in tickers if t in ttb}

    scalar = resolve_rc_asset_cap(n_total_for_global, equity_only=equity_only)
    return {t: scalar for t in tickers}


def resolve_rc_asset_cap(n_assets: int, equity_only: bool = False) -> float:
    """
    Per-asset RC cap from feasibility_constraints_spec §1 and §6.

    - If N < 4: rc_asset_cap = 0.40
    - Else:     rc_asset_cap = min(0.25, max(0.10, 1.5 / N))
    - Equity-Only mode (RB_growth >= 0.90): rc_asset_cap = max(rc_asset_cap, 0.15)
    """
    if n_assets <= 0:
        return 0.0
    if n_assets < 4:
        base = 0.40
    else:
        base = min(0.25, max(0.10, 1.5 / n_assets))
    if equity_only:
        base = max(base, 0.15)
    return float(base)


def resolve_weight_caps(
    n_total: int,
    n_core: int,
    n_sat: int,
    equity_only: bool = False,
) -> Dict[str, float]:
    """
    Core/Satellite and global max-weight caps for Growth per feasibility spec §3.1 and §6.

    Returns dict with keys:
    - max_weight_core
    - max_weight_sat
    - max_weight_all (used when no Core; else None)
    """
    if n_total <= 0:
        return {"max_weight_core": 0.0, "max_weight_sat": 0.0, "max_weight_all": 0.0}

    # Equity-Only mode: rb_growth >= 0.90
    if equity_only:
        # §6.2: max_weight_core <= 0.50, max_weight_sat ∈ [0.10, 0.15]
        max_weight_core = 0.50
        max_weight_sat = 0.15
        return {
            "max_weight_core": float(max_weight_core),
            "max_weight_sat": float(max_weight_sat),
            "max_weight_all": None,
        }

    # No Core case (§4)
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

    # Standard Core/Satellite case (§3.1)
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


def required_k(rb_block: float, rc_cap: float, k_single_asset: bool) -> int:
    """
    Minimum required number of assets in a block to achieve its risk budget (§2, §5).

    - If block has exactly one asset (k_single_asset == True): k_required = 1
      (that asset can at most reach rc_cap share of RiskPortfolio RC; higher RB is
       redistributed by the caller into other blocks).
    - Else: k_required = ceil(RB_block / rc_cap)
    """
    if k_single_asset:
        return 1
    if rb_block <= 0 or rc_cap <= 0:
        return 0
    return int(math.ceil(rb_block / rc_cap))


@dataclass
class FeasibilityContext:
    """Inputs for feasibility checks across Growth / Duration / Inflation."""

    blocks: Dict[str, List[str]]
    rc_block_targets: Dict[str, float]
    n_total: int
    growth_core_candidates: List[str]
    equity_only: bool
    rc_asset_cap: float
    rc_cap_mode: str = RC_CAP_MODE_GLOBAL
    rc_cap_rb_k_multiplier: float = DEFAULT_RC_CAP_RB_K_MULTIPLIER
    rc_asset_cap_pct: float | None = None


def check_feasible(ctx: FeasibilityContext) -> Tuple[bool, Dict[str, str]]:
    """
    Check structural feasibility of RiskPortfolio architecture.

    Implements key checks from feasibility_constraints_spec:
    - risk budget achievability by RC (k_block >= ceil(RB_block / rc_cap))
    - Growth Core/Satellite weight capacity >= RB_growth
    - Equity-Only capacity >= 1.0 (Nc·max_core + Ns·max_sat >= 1.0)

    Returns (ok, reasons_dict) where reasons_dict maps a short code to a human-readable message.
    """
    reasons: Dict[str, str] = {}

    rb = ctx.rc_block_targets or {}
    rb_g = float(rb.get("Growth", 1.0 / 3))
    rb_d = float(rb.get("Duration", 1.0 / 3))
    rb_i = float(rb.get("Inflation", 1.0 / 3))
    total_rb = rb_g + rb_d + rb_i
    if total_rb <= 0:
        reasons["RB_SUM_NONPOSITIVE"] = "rc_block_targets sum must be positive."
        return False, reasons

    rb_g /= total_rb
    rb_d /= total_rb
    rb_i /= total_rb

    growth_tickers: List[str] = (
        list(ctx.blocks.get("Growth", []))
        + list(ctx.blocks.get("Growth_HY", []))
        + list(ctx.blocks.get("Growth_EM_debt", []))
    )
    duration_tickers = list(ctx.blocks.get("Duration", []))
    inflation_tickers = list(ctx.blocks.get("Inflation", []))

    k_growth = len(growth_tickers)
    k_duration = len(duration_tickers)
    k_inflation = len(inflation_tickers)

    # Per-block RC cap for achievability (explicit pct → global; per_block_rb_k → variant B; else §1 global)
    if ctx.rc_asset_cap_pct is not None and ctx.rc_asset_cap_pct > 0:
        cap_g = cap_d = cap_i = float(ctx.rc_asset_cap_pct)
    elif ctx.rc_cap_mode == RC_CAP_MODE_PER_BLOCK_RB_K:
        caps_b = compute_rc_caps_by_block_from_targets(
            ctx.blocks,
            rb_g,
            rb_d,
            rb_i,
            ctx.rc_cap_rb_k_multiplier,
            ctx.equity_only,
        )
        cap_g, cap_d, cap_i = caps_b["Growth"], caps_b["Duration"], caps_b["Inflation"]
    else:
        cap_g = cap_d = cap_i = ctx.rc_asset_cap

    # Risk budget achievability by RC (§2, §5)
    k_req_g = required_k(rb_g, cap_g, k_single_asset=(k_growth == 1))
    k_req_d = required_k(rb_d, cap_d, k_single_asset=(k_duration == 1))
    k_req_i = required_k(rb_i, cap_i, k_single_asset=(k_inflation == 1))

    if k_growth < k_req_g:
        reasons["RB_GROWTH_K"] = (
            f"Risk budget not achievable: Growth has {k_growth} assets, need at least "
            f"{k_req_g} (ceil(RB_growth/rc_cap_growth={cap_g:.4f}))."
        )
    if k_duration < k_req_d:
        reasons["RB_DURATION_K"] = (
            f"Risk budget not achievable: Duration has {k_duration} assets, need at least "
            f"{k_req_d} (ceil(RB_duration/rc_cap_duration={cap_d:.4f}))."
        )
    if k_inflation < k_req_i:
        reasons["RB_INFLATION_K"] = (
            f"Risk budget not achievable: Inflation has {k_inflation} assets, need at least "
            f"{k_req_i} (ceil(RB_inflation/rc_cap_inflation={cap_i:.4f}))."
        )

    # Growth Core/Satellite weight capacity (§3.1, §6)
    n_core = sum(1 for t in growth_tickers if t in ctx.growth_core_candidates)
    n_sat = k_growth - n_core
    caps = resolve_weight_caps(ctx.n_total, n_core, n_sat, equity_only=ctx.equity_only)
    max_core = caps["max_weight_core"] or 0.0
    max_sat = caps["max_weight_sat"] or 0.0

    growth_capacity = n_core * max_core + n_sat * max_sat
    if growth_capacity < rb_g - 1e-9:
        reasons["GROWTH_CAPACITY_RB"] = (
            f"Growth weight capacity {growth_capacity:.3f} < RB_growth {rb_g:.3f}. "
            "Increase Core/Satellite caps or add Growth assets."
        )

    if ctx.equity_only:
        # Equity-Only: Nc·max_core + Ns·max_sat >= 1.0 (§6.2)
        if growth_capacity < 1.0 - 1e-9:
            reasons["GROWTH_CAPACITY_EQUITY_ONLY"] = (
                f"Equity-Only: Growth capacity {growth_capacity:.3f} < 1.0. "
                "Need Nc·0.5 + Ns·0.15 >= 1.0."
            )

    ok = len(reasons) == 0
    return ok, reasons

