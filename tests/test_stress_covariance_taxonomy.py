"""Tests for taxonomy_blend_v1 stress covariance (RC diagnostics only)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.risk_contrib import cov_matrix_monthly, percentage_contributions_variance
from src.stress import run_stress
from src.stress_covariance_taxonomy import (
    LAMBDA_BLEND,
    STRESS_COV_CALIBRATION_VERSION,
    VOL_MULT_BLOCK,
    build_target_correlation,
    key_rho_overrides_used_for_scenario,
    repair_correlation_matrix,
    resolve_stress_asset_block,
    stress_covariance_taxonomy_blend,
)


def test_repair_correlation_matrix_psd() -> None:
    c = np.array([[1.0, -0.95, 0.95], [-0.95, 1.0, -0.95], [0.95, -0.95, 1.0]])
    r = repair_correlation_matrix(c)
    ev = np.linalg.eigvalsh(r)
    assert float(np.min(ev)) >= -1e-7
    assert np.allclose(np.diag(r), 1.0)


def test_resolve_blocks_known_etfs() -> None:
    r1 = resolve_stress_asset_block("VOO", cash_proxy_ticker="BIL")
    assert r1.block == "EQ"
    assert r1.source == "etf_universe"
    r2 = resolve_stress_asset_block("TLT", cash_proxy_ticker="BIL")
    assert r2.block == "ND"
    r3 = resolve_stress_asset_block("GLD", cash_proxy_ticker="BIL")
    assert r3.block == "CO"
    r4 = resolve_stress_asset_block("BIL", cash_proxy_ticker="BIL")
    assert r4.block == "CA"
    assert r4.source == "cash_proxy"


def test_resolve_unknown_ticker() -> None:
    r = resolve_stress_asset_block("NOTINTHERE", cash_proxy_ticker="BIL")
    assert r.block == "EQ"
    assert r.source == "unknown"


def test_build_target_correlation_symmetric() -> None:
    blocks = ["EQ", "ND", "CA"]
    c = build_target_correlation(blocks, "equity_shock")
    assert c.shape == (3, 3)
    assert np.allclose(c, c.T)
    assert np.allclose(np.diag(c), 1.0)


def test_calibrated_v1_lambda_blend_values() -> None:
    assert LAMBDA_BLEND["equity_shock"] == 0.45
    assert LAMBDA_BLEND["credit_shock"] == 0.54
    assert LAMBDA_BLEND["liquidity_shock"] == 0.54
    assert LAMBDA_BLEND["recession_severe"] == 0.65
    assert LAMBDA_BLEND["rates_shock"] == 0.38
    assert LAMBDA_BLEND["inflation_stagflation"] == 0.44


def test_calibrated_v1_vol_multipliers() -> None:
    assert VOL_MULT_BLOCK["credit_shock"]["CR"] == 1.48
    assert VOL_MULT_BLOCK["credit_shock"]["EQ"] == 1.18
    assert VOL_MULT_BLOCK["rates_shock"]["ND"] == 1.42
    assert VOL_MULT_BLOCK["rates_shock"]["TI"] == 1.35
    assert VOL_MULT_BLOCK["rates_shock"]["EQ"] == 1.08
    assert VOL_MULT_BLOCK["inflation_stagflation"]["CO"] == 1.46
    assert VOL_MULT_BLOCK["inflation_stagflation"]["TI"] == 1.26
    assert VOL_MULT_BLOCK["inflation_stagflation"]["EQ"] == 1.22


def test_calibrated_v1_key_rho_overrides_in_target_corr() -> None:
    c_cr = build_target_correlation(["EQ", "CR"], "credit_shock")
    assert abs(float(c_cr[0, 1]) - 0.74) < 1e-9
    c_inf = build_target_correlation(["CO", "TI"], "inflation_stagflation")
    assert abs(float(c_inf[0, 1]) - 0.64) < 1e-9
    c_rt = build_target_correlation(["EQ", "ND", "TI"], "rates_shock")
    i_eq, i_nd, i_ti = 0, 1, 2
    assert abs(float(c_rt[i_nd, i_ti]) - 0.93) < 1e-9
    assert abs(float(c_rt[i_eq, i_nd]) - (-0.42)) < 1e-9


def test_key_rho_overrides_trace_matches_table() -> None:
    assert key_rho_overrides_used_for_scenario("credit_shock") == {"CR_EQ": 0.74}
    assert key_rho_overrides_used_for_scenario("inflation_stagflation") == {"CO_TI": 0.64}
    assert key_rho_overrides_used_for_scenario("rates_shock") == {"EQ_ND": -0.42, "ND_TI": 0.93}


def test_stress_covariance_taxonomy_blend_psd() -> None:
    rng = np.random.default_rng(0)
    n = 5
    cols = ["VOO", "IEF", "HYG", "GLD", "BIL"]
    x = rng.normal(size=(120, n))
    df = pd.DataFrame(x, columns=cols)
    cov_b = cov_matrix_monthly(df, ddof=1)
    cov_s, diag = stress_covariance_taxonomy_blend(
        cov_b, cols, "equity_shock", cash_proxy_ticker="BIL"
    )
    ev = np.linalg.eigvalsh(cov_s.values)
    assert float(np.min(ev)) >= -1e-9
    assert diag["stress_cov_method"] == "taxonomy_blend_v1"
    assert diag.get("stress_cov_calibration_version") == STRESS_COV_CALIBRATION_VERSION
    assert isinstance(diag.get("vol_mult_by_block"), dict)
    assert "EQ" in diag["vol_mult_by_block"]
    assert diag.get("key_rho_overrides_used") == {}
    assert "BIL" not in (diag.get("taxonomy_coverage") or {}).get("missing_tickers", [])


def test_run_stress_taxonomy_rows_have_metadata() -> None:
    cols = ["VOO", "IEF", "BIL"]
    rng = np.random.default_rng(1)
    df = pd.DataFrame(rng.normal(size=(60, 3)), columns=cols)
    betas = pd.DataFrame(
        {
            "beta_eq": [1.0, 0.1, 0.0],
            "beta_rr": [0.0, -5.0, 0.0],
            "beta_credit": [0.0, 0.0, 0.0],
            "beta_inf": [0.0, 0.0, 0.0],
            "beta_usd": [0.0, 0.0, 0.0],
            "beta_cmd": [0.0, 0.0, 0.0],
        },
        index=cols,
    )
    w = {"VOO": 0.5, "IEF": 0.3, "BIL": 0.2}
    pb = {"beta_eq": 1.0, "beta_rr": -0.5, "beta_credit": 0.0, "beta_inf": 0.0, "beta_usd": 0.0, "beta_cmd": 0.0}
    out = run_stress(cols, w, df, betas, pb, 0.25, cash_proxy_ticker="BIL", factor_returns=None)
    rows = out["scenario_results"]
    eq_row = next(r for r in rows if r["scenario_id"] == "equity_shock")
    assert eq_row["stress_cov_method"] == "taxonomy_blend_v1"
    assert eq_row["stress_cov_lambda"] == 0.45
    assert "blocks_by_ticker" in (eq_row.get("taxonomy_coverage") or {})
    rates_row = next(r for r in rows if r["scenario_id"] == "rates_shock")
    assert rates_row["stress_cov_method"] == "taxonomy_blend_v1"
    assert rates_row["stress_cov_lambda"] == 0.38
    assert rates_row.get("stress_cov_calibration_version") == STRESS_COV_CALIBRATION_VERSION
    assert isinstance(rates_row.get("vol_mult_by_block"), dict)
    assert rates_row.get("key_rho_overrides_used") == {"EQ_ND": -0.42, "ND_TI": 0.93}
    cr_row = next(r for r in rows if r["scenario_id"] == "credit_shock")
    assert cr_row["stress_cov_lambda"] == 0.54
    assert cr_row.get("vol_mult_by_block", {}).get("CR") == 1.48


def test_uniform_legacy_stress_covariance() -> None:
    cols = ["VOO", "IEF", "BIL"]
    rng = np.random.default_rng(2)
    df = pd.DataFrame(rng.normal(size=(60, 3)), columns=cols)
    betas = pd.DataFrame(
        {"beta_eq": [1.0, 0.1, 0.0], "beta_rr": [0.0, -5.0, 0.0], "beta_credit": [0.0, 0.0, 0.0],
         "beta_inf": [0.0, 0.0, 0.0], "beta_usd": [0.0, 0.0, 0.0], "beta_cmd": [0.0, 0.0, 0.0]},
        index=cols,
    )
    w = {"VOO": 0.5, "IEF": 0.3, "BIL": 0.2}
    pb = {"beta_eq": 1.0, "beta_rr": -0.5, "beta_credit": 0.0, "beta_inf": 0.0, "beta_usd": 0.0, "beta_cmd": 0.0}
    out = run_stress(
        cols, w, df, betas, pb, 0.25, cash_proxy_ticker="BIL", factor_returns=None, stress_cov_method="uniform_legacy"
    )
    row = next(r for r in out["scenario_results"] if r["scenario_id"] == "equity_shock")
    assert row["stress_cov_method"] == "uniform_legacy"
    assert row["stress_cov_lambda"] is None
    assert row.get("stress_cov_calibration_version") is None
    assert row.get("vol_mult_by_block") is None
    assert row.get("key_rho_overrides_used") is None


def test_unknown_ticker_blend_no_nan() -> None:
    rng = np.random.default_rng(99)
    cols = ["VOO", "NOTINTHERE", "BIL"]
    df = pd.DataFrame(rng.normal(size=(60, 3)) * 0.02, columns=cols)
    cov_b = cov_matrix_monthly(df, ddof=1)
    cov_s, diag = stress_covariance_taxonomy_blend(
        cov_b, cols, "credit_shock", cash_proxy_ticker="BIL"
    )
    assert "NOTINTHERE" in (diag.get("taxonomy_coverage") or {}).get("missing_tickers", [])
    assert not np.isnan(cov_s.values).any()
    assert np.isfinite(cov_s.values).all()


def test_rc_snapshot_equity_shock_taxonomy() -> None:
    cols = ["VOO", "IEF", "HYG", "GLD", "BIL"]
    rng = np.random.default_rng(42)
    df = pd.DataFrame(rng.normal(size=(80, 5)) * 0.02, columns=cols)
    cov_b = cov_matrix_monthly(df, ddof=1)
    cov_s, _ = stress_covariance_taxonomy_blend(cov_b, cols, "equity_shock", cash_proxy_ticker="BIL")
    w = np.array([0.4, 0.2, 0.15, 0.15, 0.1])
    rc_base = percentage_contributions_variance(w, cov_b.values)
    rc_st = percentage_contributions_variance(w, cov_s.values)
    assert np.isfinite(rc_st).all()
    assert abs(float(rc_st.sum()) - 1.0) < 1e-9
    assert not np.allclose(rc_base, rc_st)
