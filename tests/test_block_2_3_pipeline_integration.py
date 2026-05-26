from __future__ import annotations

from src.product_bundle_paths import (
    PORTFOLIO_XRAY_BLOCK_2_3_KEY,
    portfolio_xray_has_block_2_3,
    product_bundle_manifest_extra,
)
from src.portfolio_xray import build_portfolio_xray_v2

from test_block_2_3_factor_exposure import _analysis_setup, _stress_report, assert_block_2_3_product_contract


def test_block_2_3_product_bundle_manifest_note() -> None:
    note = product_bundle_manifest_extra()["subject_diagnostics_contract"]["portfolio_xray_json"]

    assert note["product_factor_exposure_key"] == PORTFOLIO_XRAY_BLOCK_2_3_KEY
    assert "Block 2.3 factor exposure" in note["note"]


def test_portfolio_xray_has_block_2_3_helper_accepts_product_contract() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"VOO": 0.6, "BND": 0.4},
        rc_asset=[],
        stress_report=_stress_report(),
        portfolio_valid=True,
        portfolio_metrics={"window_months": 120, "cagr": 0.08, "vol_annual": 0.1},
    )

    assert portfolio_xray_has_block_2_3(xray)
    assert_block_2_3_product_contract(xray["block_2_3_factor_exposure"])


def test_portfolio_xray_has_block_2_3_helper_rejects_legacy_section_only() -> None:
    assert not portfolio_xray_has_block_2_3({"sections": {"factor_exposure": {}}})
