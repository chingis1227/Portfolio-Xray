"""Unit tests for ``regime_factor_analytics_v1`` (diagnostic-only)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.regime_factor_analytics import (
    FACTOR_COLUMN_ORDER,
    regime_factor_analytics,
    regime_factor_analytics_csv_frames,
    regime_factor_analytics_for_stress_report,
    regime_factor_analytics_summary,
)
from src.stress_factors import FACTOR_TO_BETA_KEY


def _month_end_index(n: int, start_year: int = 2015) -> pd.DatetimeIndex:
    return pd.date_range(f"{start_year}-01-01", periods=n, freq="ME")


def _factor_frame(idx: pd.DatetimeIndex, *, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = {}
    for j, col in enumerate(FACTOR_COLUMN_ORDER):
        data[col] = rng.normal(0, 0.01, size=len(idx))
    return pd.DataFrame(data, index=idx)


def _make_labels(
    idx: pd.DatetimeIndex,
    regime_cycle: tuple[str, ...],
) -> pd.Series:
    out = []
    for i in range(len(idx)):
        out.append(regime_cycle[i % len(regime_cycle)])
    return pd.Series(out, index=idx)


def test_filtering_and_alignment_primary_regimes_only():
    idx = _month_end_index(48)
    regimes = _make_labels(
        idx,
        ("goldilocks", "reflation", "stagflation", "recession_disinflation"),
    )
    factors = _factor_frame(idx, seed=1)
    assets = pd.DataFrame(
        {
            "AAA": np.random.default_rng(2).normal(0.005, 0.02, len(idx)),
            "BBB": np.random.default_rng(3).normal(0.004, 0.02, len(idx)),
        },
        index=idx,
    )
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
        weights={"AAA": 0.6, "BBB": 0.4},
    )
    for r in ("goldilocks", "reflation", "stagflation", "recession_disinflation"):
        assert r in out["regimes"]
        blk = out["regimes"][r]
        assert blk["n_obs"] == 12
        assert blk["quality_status"] == "low_confidence"
    assert "neutral_transition" not in out["regimes"]
    assert out["n_obs_total"] == 48


def test_neutral_transition_not_a_primary_group():
    idx = _month_end_index(20)
    regimes = pd.Series(["goldilocks"] * 10 + ["neutral_transition"] * 10, index=idx)
    assets = pd.DataFrame(np.random.default_rng(4).normal(0, 0.02, (len(idx), 2)), index=idx, columns=["A", "B"])
    factors = _factor_frame(idx, seed=5)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
    )
    g = out["regimes"]["goldilocks"]
    assert g["n_obs"] == 10
    assert g["quality_status"] == "insufficient_data"
    assert g["asset_covariance_available"] is False


def test_covariance_symmetry_and_corr_diagonal():
    idx = _month_end_index(40)
    regimes = _make_labels(idx, ("reflation",))
    rng = np.random.default_rng(6)
    assets = pd.DataFrame(rng.normal(0, 0.02, (len(idx), 3)), index=idx, columns=["A", "B", "C"])
    factors = _factor_frame(idx, seed=7)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
    )
    blk = out["regimes"]["reflation"]
    assert blk["n_obs"] == 40
    cov_nested = blk["asset_covariance"]["covariance"]
    order = blk["asset_covariance"]["assets"]
    cov_df = pd.DataFrame(cov_nested).reindex(index=order, columns=order).astype(float)
    assert np.allclose(cov_df.values, cov_df.values.T, atol=1e-9)
    corr_nested = blk["asset_covariance"]["correlation"]
    corr_df = pd.DataFrame(corr_nested).reindex(index=order, columns=order).astype(float)
    assert np.allclose(np.diag(corr_df.values), 1.0, atol=1e-9)


def test_beta_output_shape_hac_keys():
    idx = _month_end_index(30)
    regimes = _make_labels(idx, ("stagflation",))
    rng = np.random.default_rng(8)
    assets = pd.DataFrame(rng.normal(0, 0.02, (len(idx), 2)), index=idx, columns=["A", "B"])
    factors = _factor_frame(idx, seed=9)
    out = regime_factor_analytics(monthly_returns=assets, monthly_factor_returns=factors, regime_labels=regimes)
    betas = out["regimes"]["stagflation"]["asset_factor_betas"]
    beta_keys = [FACTOR_TO_BETA_KEY[c] for c in FACTOR_COLUMN_ORDER]
    for t in ["A", "B"]:
        row = betas[t]
        assert row["available"] is True
        assert set(row["betas"].keys()) == set(beta_keys)
        hac = row["hac_inference"]
        assert "intercept" in hac["t"]
        for bk in beta_keys:
            assert bk in hac["p"]


def test_gating_suppresses_under_12():
    idx = _month_end_index(10)
    regimes = _make_labels(idx, ("goldilocks",))
    assets = pd.DataFrame(np.random.default_rng(10).normal(0, 0.02, (len(idx), 2)), index=idx, columns=["A", "B"])
    factors = _factor_frame(idx, seed=11)
    out = regime_factor_analytics(monthly_returns=assets, monthly_factor_returns=factors, regime_labels=regimes)
    blk = out["regimes"]["goldilocks"]
    assert blk["n_obs"] == 10
    assert blk["quality_status"] == "insufficient_data"
    assert blk["asset_covariance_available"] is False
    assert blk["factor_covariance_available"] is False
    assert blk["asset_factor_betas_available"] is False
    assert blk["factor_rc_available"] is False
    assert blk["asset_factor_betas"] == {}


def test_variance_contribution_shares_sum():
    idx = _month_end_index(35)
    regimes = _make_labels(idx, ("recession_disinflation",))
    rng = np.random.default_rng(12)
    assets = pd.DataFrame(rng.normal(0, 0.02, (len(idx), 2)), index=idx, columns=["A", "B"])
    factors = _factor_frame(idx, seed=13)
    w = {"A": 0.5, "B": 0.5}
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
        weights=w,
    )
    vc = out["regimes"]["recession_disinflation"]["factor_variance_contribution"]
    assert vc["available"] is True
    total = float(vc["total_factor_variance"])
    assert total > 1e-12
    ssum = sum(float(r["factor_risk_contribution_share"]) for r in vc["rows"])
    assert abs(ssum - 1.0) < 1e-8


def test_missing_inner_join_emits_empty_regimes():
    idx_a = _month_end_index(20, start_year=2020)
    idx_f = _month_end_index(20, start_year=2010)
    regimes = _make_labels(idx_a, ("goldilocks",))
    assets = pd.DataFrame(np.random.default_rng(14).normal(0, 0.02, (len(idx_a), 1)), index=idx_a, columns=["A"])
    factors = _factor_frame(idx_f, seed=15)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes.reindex(idx_a),
    )
    assert out["n_obs_total"] == 0
    assert any("no_overlap" in w for w in out.get("warnings", []))
    assert out["regimes"]["goldilocks"]["n_obs"] == 0


def test_transition_split_emits_split_keys():
    idx = _month_end_index(36)
    regimes = _make_labels(idx, ("goldilocks",))
    tf = pd.Series([i % 2 == 0 for i in range(len(idx))], index=idx)
    assets = pd.DataFrame(np.random.default_rng(16).normal(0, 0.02, (len(idx), 2)), index=idx, columns=["A", "B"])
    factors = _factor_frame(idx, seed=17)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
        transition_flag=tf,
        enable_transition_split=True,
    )
    assert "goldilocks__transition_false" in out["splits"]["transition"]
    assert "goldilocks__transition_true" in out["splits"]["transition"]


def test_weekly_forward_fill_alignment_tag():
    idx_w = pd.date_range("2020-01-03", periods=80, freq="W-FRI")
    idx_m = _month_end_index(24, start_year=2020)
    regimes_m = _make_labels(idx_m, ("reflation",))
    rng = np.random.default_rng(18)
    assets_w = pd.DataFrame(rng.normal(0, 0.02, (len(idx_w), 2)), index=idx_w, columns=["A", "B"])
    factors_w = pd.DataFrame(
        rng.normal(0, 0.01, (len(idx_w), len(FACTOR_COLUMN_ORDER))),
        index=idx_w,
        columns=list(FACTOR_COLUMN_ORDER),
    )
    out = regime_factor_analytics(
        monthly_returns=assets_w,
        monthly_factor_returns=factors_w,
        regime_labels=regimes_m,
        frequency="weekly",
        weekly_alignment="forward_fill_monthly_label",
    )
    assert out["frequency"] == "weekly"
    assert out["weekly_alignment"] == "forward_fill_monthly_label"


def test_csv_stub_rows_when_suppressed():
    idx = _month_end_index(8)
    regimes = _make_labels(idx, ("goldilocks",))
    assets = pd.DataFrame(np.random.default_rng(19).normal(0, 0.02, (len(idx), 2)), index=idx, columns=["A", "B"])
    factors = _factor_frame(idx, seed=20)
    out = regime_factor_analytics(monthly_returns=assets, monthly_factor_returns=factors, regime_labels=regimes)
    frames = regime_factor_analytics_csv_frames(out)
    cov = frames["regime_asset_covariance.csv"]
    assert not cov.empty
    stub = cov[(cov["estimate_suppressed"] == True) & (cov["regime"] == "goldilocks")]  # noqa: E712
    assert len(stub) >= 1


def test_stress_report_slice_omits_covariance_nests():
    idx = _month_end_index(30)
    regimes = _make_labels(idx, ("reflation",))
    assets = pd.DataFrame(np.random.default_rng(21).normal(0, 0.02, (len(idx), 2)), index=idx, columns=["A", "B"])
    factors = _factor_frame(idx, seed=22)
    full = regime_factor_analytics(monthly_returns=assets, monthly_factor_returns=factors, regime_labels=regimes)
    slim = regime_factor_analytics_for_stress_report(full)
    ac = slim["regimes"]["reflation"]["asset_covariance"]
    assert "covariance" not in ac
    assert "correlation" not in ac
    summ = regime_factor_analytics_summary(full)
    assert summ["regimes"]["reflation"]["n_obs"] == 30


def test_ledoit_wolf_covariance_when_complete_cases_exist():
    idx = _month_end_index(30)
    regimes = _make_labels(idx, ("reflation",))
    rng = np.random.default_rng(42)
    assets = pd.DataFrame(rng.normal(0, 0.02, (len(idx), 3)), index=idx, columns=["A", "B", "C"])
    factors = _factor_frame(idx, seed=43)
    out = regime_factor_analytics(monthly_returns=assets, monthly_factor_returns=factors, regime_labels=regimes)
    a_cov = out["regimes"]["reflation"]["asset_covariance"]
    f_cov = out["regimes"]["reflation"]["factor_covariance"]
    assert a_cov.get("covariance_estimator") == "ledoit_wolf"
    assert f_cov.get("covariance_estimator") == "ledoit_wolf"
    assert a_cov.get("ledoit_wolf_shrinkage") is not None
    assert 0.0 <= float(a_cov["ledoit_wolf_shrinkage"]) <= 1.0


def test_confidence_split_warns_without_series():
    idx = _month_end_index(25)
    regimes = _make_labels(idx, ("goldilocks",))
    assets = pd.DataFrame(np.random.default_rng(23).normal(0, 0.02, (len(idx), 2)), index=idx, columns=["A", "B"])
    factors = _factor_frame(idx, seed=24)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
        enable_confidence_split=True,
        confidence_level=None,
    )
    assert any("confidence_split_requested" in w for w in out.get("warnings", []))

