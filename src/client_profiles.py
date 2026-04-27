"""
Load client_profiles.yml and apply profile defaults to config.

Profiles provide midpoints for target_vol, max_dd, return, liquidity_floor.
When config has client_profile set, missing fields are filled from profile.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

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
    Keys: target_nominal_return_annual, target_vol_annual, target_max_drawdown_pct,
          liquidity_floor_pct (hint only), min_single_security_weight_pct (optional).
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
        out["liquidity_floor_pct"] = lf
    if "min_single_security_weight_pct" in prof and isinstance(prof["min_single_security_weight_pct"], (int, float)):
        out["min_single_security_weight_pct"] = float(prof["min_single_security_weight_pct"])
    return out


def apply_profile_to_config(raw: dict[str, Any]) -> dict[str, Any]:
    """
    If raw has client_profile set, set target fields from that profile (midpoints).
    Profile values overwrite whatever is in the config so that choosing a profile actually applies it.
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
    if "liquidity_floor_pct" in defaults:
        result["liquidity_floor_pct"] = defaults["liquidity_floor_pct"]
    if result.get("min_single_security_weight_pct") is None and "min_single_security_weight_pct" in defaults:
        result["min_single_security_weight_pct"] = defaults["min_single_security_weight_pct"]
    return result
