"""
Load client_profiles.yml and apply profile defaults to config.

Profiles provide midpoints for target_vol, max_dd, return, risk_budget (G/D/I), liquidity_floor.
When config has client_profile set, missing fields are filled from profile; rc_block_targets are normalized to sum 1.0.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Standard block names for risk budget
RISK_BUDGET_BLOCKS = ("Growth", "Duration", "Inflation")
PROFILE_IDS = ("ultra_conservative", "conservative", "balanced", "growth", "aggressive")


def _profiles_path() -> Path:
    return Path(__file__).resolve().parent.parent / "config" / "client_profiles.yml"


def load_profiles() -> dict[str, Any]:
    """Load client_profiles.yml; return { profile_id: profile_dict }."""
    path = _profiles_path()
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("profiles") or {}


def _midpoint_from_spec(spec: dict[str, Any] | None) -> float | None:
    """Get midpoint from profile spec (midpoint in decimal, or compute from min_pct/max_pct)."""
    if not spec or not isinstance(spec, dict):
        return None
    if "midpoint" in spec:
        return float(spec["midpoint"])
    min_pct = spec.get("min_pct")
    max_pct = spec.get("max_pct")
    if min_pct is not None and max_pct is not None:
        return (float(min_pct) + float(max_pct)) / 200.0  # pct -> decimal
    return None


def get_profile_defaults(profile_id: str) -> dict[str, Any]:
    """
    Return a flat dict of default values (midpoints) for the given profile.
    risk_budget midpoints are normalized to sum 1.0.
    Keys: target_nominal_return_annual, target_vol_annual, target_max_drawdown_pct,
          rc_block_targets (dict Growth/Duration/Inflation), liquidity_floor_pct (hint only).
    """
    profiles = load_profiles()
    pid = profile_id.strip().lower().replace(" ", "_")
    if pid not in profiles:
        return {}
    prof = profiles[pid]
    out: dict[str, Any] = {}

    tr = _midpoint_from_spec(prof.get("target_return_annual"))
    if tr is not None:
        out["target_nominal_return_annual"] = tr
    tv = _midpoint_from_spec(prof.get("target_vol_annual"))
    if tv is not None:
        out["target_vol_annual"] = tv
    if "target_max_drawdown_pct" in prof and isinstance(prof["target_max_drawdown_pct"], (int, float)):
        out["target_max_drawdown_pct"] = float(prof["target_max_drawdown_pct"])
    lf = _midpoint_from_spec(prof.get("liquidity_floor_pct"))
    if lf is not None:
        out["liquidity_floor_pct"] = lf  # hint; can map to liquidity_need_months etc. later

    rb = prof.get("risk_budget")
    if isinstance(rb, dict):
        blocks = {b: _midpoint_from_spec(rb.get(b)) for b in RISK_BUDGET_BLOCKS if rb.get(b)}
        blocks = {b: v for b, v in blocks.items() if v is not None}
        if blocks:
            total = sum(blocks.values())
            if total > 0:
                out["rc_block_targets"] = {b: v / total for b, v in blocks.items()}
            else:
                out["rc_block_targets"] = blocks
    return out


def normalize_rc_block_targets(rc_block_targets: dict[str, float] | None) -> dict[str, float] | None:
    """
    If rc_block_targets sum != 1.0, scale all proportionally so sum = 1.0.
    Returns new dict or same if already 1.0 or None/empty.
    """
    if not rc_block_targets or len(rc_block_targets) == 0:
        return rc_block_targets
    total = sum(rc_block_targets.values())
    if total <= 0:
        return rc_block_targets
    if abs(total - 1.0) < 1e-9:
        return rc_block_targets
    return {b: w / total for b, w in rc_block_targets.items()}


def apply_profile_to_config(raw: dict[str, Any]) -> dict[str, Any]:
    """
    If raw has client_profile set, set target/risk_budget fields from that profile (midpoints).
    Profile values overwrite whatever is in the config so that choosing a profile actually applies it.
    rc_block_targets from profile are normalized to sum 1.0.
    """
    profile_id = raw.get("client_profile")
    if not profile_id or not isinstance(profile_id, str):
        return raw
    defaults = get_profile_defaults(profile_id)
    if not defaults:
        return raw
    result = dict(raw)
    if "target_nominal_return_annual" in defaults:
        result["target_nominal_return_annual"] = defaults["target_nominal_return_annual"]
    if "target_vol_annual" in defaults:
        result["target_vol_annual"] = defaults["target_vol_annual"]
    if "target_max_drawdown_pct" in defaults:
        result["target_max_drawdown_pct"] = defaults["target_max_drawdown_pct"]
    if "rc_block_targets" in defaults:
        # Keep manual rc_block_targets from config (e.g. Duration=10% for single-asset block)
        raw_rbt = raw.get("rc_block_targets")
        if not raw_rbt or not isinstance(raw_rbt, dict) or len(raw_rbt) < 3:
            result["rc_block_targets"] = dict(defaults["rc_block_targets"])
        else:
            result["rc_block_targets"] = dict(raw_rbt)
    if "liquidity_floor_pct" in defaults:
        result["liquidity_floor_pct"] = defaults["liquidity_floor_pct"]
    return result
