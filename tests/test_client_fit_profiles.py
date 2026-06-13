from src.client_fit import load_client_fit_presets, validate_client_fit_presets
from src.client_profiles import get_profile_defaults


def test_client_fit_presets_validate_and_exclude_liquidity():
    result = validate_client_fit_presets()

    assert result.ok, result.errors
    presets = load_client_fit_presets()
    assert set(presets) == {"ultra_conservative", "conservative", "balanced", "growth", "aggressive"}
    assert presets["balanced"]["target_return_range"] == {"min": 0.05, "max": 0.07}
    assert presets["balanced"]["target_vol_range"] == {"min": 0.07, "max": 0.10}
    assert presets["balanced"]["target_max_drawdown_pct"] == -0.20
    assert "liquidity_floor_pct" not in presets["balanced"]


def test_legacy_profile_defaults_still_include_policy_compatibility_fields():
    defaults = get_profile_defaults("balanced")

    assert defaults["target_nominal_return_annual"] == 0.06
    assert defaults["target_vol_annual"] == 0.085
    assert defaults["target_max_drawdown_pct"] == -0.20
    assert defaults["liquidity_floor_pct"] == 0.10
