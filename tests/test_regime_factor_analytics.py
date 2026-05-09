"""Unit tests for ``regime_factor_analytics_v1`` (diagnostic-only)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

from src.regime_factor_analytics import (
    FACTOR_COLUMN_ORDER,
    REGIME_ANALYTICS_ANNUALIZATION_FACTOR,
    regime_factor_analytics,
    regime_factor_analytics_csv_frames,
    regime_factor_analytics_for_stress_report,
    regime_factor_analytics_summary,
    regime_factor_quality_daily,
)
from src.stress_factors import (
    FACTOR_MONTHS_10Y,
    FACTOR_TO_BETA_KEY,
    FACTOR_TRADING_DAYS_10Y,
    FACTOR_WEEKS_10Y,
)


def _month_end_index(n: int, start_year: int = 2015) -> pd.DatetimeIndex:
    return pd.date_range(f"{start_year}-01-01", periods=n, freq="ME")


def _business_daily_range(*, start: str, periods: int) -> pd.DatetimeIndex:
    return pd.bdate_range(start, periods=periods)


def _factor_frame(idx: pd.DatetimeIndex, *, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = {}
    for j, col in enumerate(FACTOR_COLUMN_ORDER):
        data[col] = rng.normal(0, 0.01, size=len(idx))
    return pd.DataFrame(data, index=idx)


def _make_labels(idx: pd.DatetimeIndex, regime_cycle: tuple[str, ...]) -> pd.Series:
    out = []
    for i in range(len(idx)):
        out.append(regime_cycle[i % len(regime_cycle)])
    return pd.Series(out, index=idx)


def _anchor_monthly_regimes(regimes: pd.Series) -> pd.Series:
    """Prepend a month-end label so daily ``ffill`` covers days before the first stamp."""

    if regimes is None or regimes.empty:
        return regimes
    anchor_ts = pd.Timestamp(regimes.index.min()) - pd.offsets.MonthEnd(1)
    head = pd.Series([str(regimes.iloc[0])], index=[anchor_ts])
    return pd.concat([head, regimes]).sort_index()


def _expect_ffill_daily_labels(
    daily_index: pd.DatetimeIndex,
    monthly_labels: pd.Series,
) -> pd.Series:
    labels_naive = pd.Series(
        monthly_labels.values,
        index=pd.DatetimeIndex(monthly_labels.index).normalize(),
        name="regime",
    ).dropna().astype(str).sort_index()
    target = pd.DatetimeIndex(daily_index).normalize().sort_values()
    return labels_naive.reindex(target, method="ffill")

# ---------------------------------------------------------------------------
# Daily production path
# ---------------------------------------------------------------------------


def test_daily_forward_fill_inherits_monthly_primary_regime():
    idx_m = pd.to_datetime(["2019-12-31", "2020-01-31", "2020-02-29"])
    regimes_m = pd.Series(["goldilocks", "reflation", "stagflation"], index=idx_m)
    idx_d = pd.bdate_range("2020-01-02", "2020-02-28")
    expected_l = _expect_ffill_daily_labels(idx_d, regimes_m)
    assert expected_l.loc["2020-01-10"] == "goldilocks"
    assert expected_l.loc["2020-02-03"] == "reflation"

    rng = np.random.default_rng(0)
    assets = pd.DataFrame(rng.normal(0, 0.02, (len(idx_d), 2)), index=idx_d, columns=["A", "B"])
    factors = _factor_frame(idx_d, seed=1)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes_m,
        frequency="daily",
    )
    assert out["regime_frequency"] == "monthly"
    assert out["analytics_frequency"] == "daily"
    assert out["daily_label_alignment"] == "daily_returns_inherit_latest_monthly_regime"
    g_n = int((expected_l == "goldilocks").sum())
    assert out["regimes"]["goldilocks"]["n_obs"] == g_n
    assert out["regimes"]["goldilocks"]["n_obs_daily"] == g_n


def test_daily_covariance_annualized_by_252_matches_sample_scaled():
    idx_d = _business_daily_range(start="2018-01-03", periods=320)
    idx_m = _month_end_index(24, start_year=2018)
    regimes = _anchor_monthly_regimes(_make_labels(idx_m, ("reflation",)))
    rng = np.random.default_rng(6)
    assets = pd.DataFrame(rng.normal(0, 0.02, (len(idx_d), 3)), index=idx_d, columns=["A", "B", "C"])
    factors = _factor_frame(idx_d, seed=7)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
        frequency="daily",
    )
    blk = out["regimes"]["reflation"]
    assert blk["covariance_scaled_to_annual"] is True
    assert blk["annualization_factor"] == REGIME_ANALYTICS_ANNUALIZATION_FACTOR
    a_cov = blk["asset_covariance"]
    ann = pd.DataFrame(a_cov["covariance"]).astype(float)
    a_slice = assets.loc[idx_d]
    complete = a_slice.dropna(how="any")

    lw = LedoitWolf(assume_centered=False).fit(complete.to_numpy(dtype=float))
    lw_cov_ann = pd.DataFrame(lw.covariance_, index=complete.columns, columns=complete.columns).astype(
        float
    ) * float(REGIME_ANALYTICS_ANNUALIZATION_FACTOR)
    ann2 = ann.reindex(index=lw_cov_ann.index, columns=lw_cov_ann.columns).astype(float)
    assert np.allclose(ann2.values, lw_cov_ann.values, rtol=1e-5, atol=1e-8)

    f_cov = blk["factor_covariance"]
    f_ann = pd.DataFrame(f_cov["covariance"]).astype(float)
    f_slice = factors.loc[idx_d]
    fc = f_slice.dropna(how="any")
    lw_f = LedoitWolf(assume_centered=False).fit(fc.to_numpy(dtype=float))
    lw_f_ann = pd.DataFrame(lw_f.covariance_, index=fc.columns, columns=fc.columns).astype(float) * float(
        REGIME_ANALYTICS_ANNUALIZATION_FACTOR
    )
    f_ann2 = f_ann.reindex(index=lw_f_ann.index, columns=lw_f_ann.columns).astype(float)
    assert np.allclose(f_ann2.values, lw_f_ann.values, rtol=1e-5, atol=1e-8)


def test_daily_volatility_uses_sqrt252():
    idx_d = _business_daily_range(start="2019-06-03", periods=200)
    idx_m = _month_end_index(12, start_year=2019)
    regimes = _anchor_monthly_regimes(_make_labels(idx_m, ("stagflation",)))
    rng = np.random.default_rng(11)
    assets = pd.DataFrame(rng.normal(0.0002, 0.015, (len(idx_d), 2)), index=idx_d, columns=["A", "B"])
    factors = _factor_frame(idx_d, seed=12)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
        frequency="daily",
    )
    blk = out["regimes"]["stagflation"]
    for col in ("A", "B"):
        v_blk = blk["asset_volatility_annual"][col]
        v_man = float(assets[col].std(ddof=1) * np.sqrt(252.0))
        assert abs(v_blk - v_man) < 1e-9


def test_daily_quality_gates_60_126_504():
    from src.regime_factor_analytics import (
        REGIME_DAILY_INSUFFICIENT_MAX,
        REGIME_DAILY_LOW_CONFIDENCE_MAX,
        REGIME_DAILY_USABLE_MAX,
    )

    assert regime_factor_quality_daily(59) == "insufficient_data"
    assert regime_factor_quality_daily(60) == "low_confidence"
    assert regime_factor_quality_daily(125) == "low_confidence"
    assert regime_factor_quality_daily(126) == "usable"
    assert regime_factor_quality_daily(503) == "usable"
    assert regime_factor_quality_daily(504) == "reliable"
    assert REGIME_DAILY_INSUFFICIENT_MAX == 60
    assert REGIME_DAILY_LOW_CONFIDENCE_MAX == 125
    assert REGIME_DAILY_USABLE_MAX == 503

    idx_m = _month_end_index(36, start_year=2015)

    def _run_daily(periods: int):
        idx_d = _business_daily_range(start="2015-01-05", periods=periods)
        regimes = _anchor_monthly_regimes(_make_labels(idx_m, ("goldilocks",)))
        rng = np.random.default_rng(periods)
        assets = pd.DataFrame(rng.normal(0, 0.02, (len(idx_d), 2)), index=idx_d, columns=["A", "B"])
        factors = _factor_frame(idx_d, seed=periods + 1)
        return regime_factor_analytics(
            monthly_returns=assets,
            monthly_factor_returns=factors,
            regime_labels=regimes,
            frequency="daily",
        )

    b50 = _run_daily(50)["regimes"]["goldilocks"]
    assert b50["quality_status"] == "insufficient_data"
    assert b50["asset_covariance_available"] is False

    b65 = _run_daily(65)["regimes"]["goldilocks"]
    assert b65["quality_status"] == "low_confidence"
    assert b65["asset_covariance_available"] is True

    b130 = _run_daily(130)["regimes"]["goldilocks"]
    assert b130["quality_status"] == "usable"

    b510 = _run_daily(510)["regimes"]["goldilocks"]
    assert b510["quality_status"] == "reliable"


def test_daily_filtering_primary_regimes_only_four_buckets():
    """Each primary regime appears for 9 calendar months (36 ME / 4) → mostly ≥126 trading days (usable)."""

    idx_m = _month_end_index(36, start_year=2015)
    regimes = _anchor_monthly_regimes(
        _make_labels(
            idx_m,
            ("goldilocks", "reflation", "stagflation", "recession_disinflation"),
        )
    )
    start = pd.Timestamp(idx_m.min()).replace(day=1)
    end = pd.Timestamp(idx_m.max()) + pd.offsets.MonthEnd(0)
    idx_d = pd.bdate_range(start, end)
    rng = np.random.default_rng(2)
    assets = pd.DataFrame(rng.normal(0, 0.02, (len(idx_d), 2)), index=idx_d, columns=["AAA", "BBB"])
    factors = _factor_frame(idx_d, seed=3)
    expected = _expect_ffill_daily_labels(idx_d, regimes)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
        weights={"AAA": 0.6, "BBB": 0.4},
        frequency="daily",
    )
    for r in ("goldilocks", "reflation", "stagflation", "recession_disinflation"):
        assert r in out["regimes"]
        blk = out["regimes"][r]
        assert blk["n_obs"] == int((expected == r).sum())
        assert blk["n_obs_daily"] == blk["n_obs"]
        assert blk["quality_status"] == "usable"
    assert "neutral_transition" not in out["regimes"]
    assert out["n_obs_total"] == len(idx_d)


def test_neutral_transition_not_a_primary_group_daily():
    idx_m = _month_end_index(20, start_year=2020)
    regimes = _anchor_monthly_regimes(
        pd.Series(
            ["goldilocks"] * 10 + ["neutral_transition"] * 10,
            index=idx_m,
        )
    )
    start = pd.Timestamp(idx_m.min()).replace(day=1)
    idx_d = pd.bdate_range(start, periods=120)
    rng = np.random.default_rng(4)
    assets = pd.DataFrame(rng.normal(0, 0.02, (len(idx_d), 2)), index=idx_d, columns=["A", "B"])
    factors = _factor_frame(idx_d, seed=5)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
        frequency="daily",
    )
    g = out["regimes"]["goldilocks"]
    exp = _expect_ffill_daily_labels(idx_d, regimes)
    assert int((exp == "goldilocks").sum()) == g["n_obs"]
    assert "neutral_transition" not in out["regimes"]


def test_csv_and_slim_carry_daily_meta_columns():
    idx_d = _business_daily_range(start="2021-01-04", periods=180)
    idx_m = _month_end_index(18, start_year=2021)
    regimes = _anchor_monthly_regimes(_make_labels(idx_m, ("goldilocks",)))
    rng = np.random.default_rng(31)
    assets = pd.DataFrame(rng.normal(0, 0.02, (len(idx_d), 2)), index=idx_d, columns=["A", "B"])
    factors = _factor_frame(idx_d, seed=32)
    out = regime_factor_analytics(
        monthly_returns=assets,
        monthly_factor_returns=factors,
        regime_labels=regimes,
        frequency="daily",
    )
    frames = regime_factor_analytics_csv_frames(out)
    cov = frames["regime_asset_covariance.csv"]
    assert not cov.empty
    assert cov["regime_frequency"].iloc[0] == "monthly"
    assert cov["analytics_frequency"].iloc[0] == "daily"
    assert cov["daily_label_alignment"].iloc[0] == "daily_returns_inherit_latest_monthly_regime"
    assert int(cov["n_obs_daily"].iloc[0]) == out["regimes"]["goldilocks"]["n_obs_daily"]
    assert cov["payload_annualization_factor"].iloc[0] == 252
    assert bool(cov["payload_covariance_scaled_to_annual"].iloc[0]) is True

    slim = regime_factor_analytics_for_stress_report(out)
    assert slim["annualization_factor"] == 252
    assert slim["covariance_scaled_to_annual"] is True
    sg = slim["regimes"]["goldilocks"]
    assert sg["n_obs_daily"] == out["regimes"]["goldilocks"]["n_obs_daily"]


# ---------------------------------------------------------------------------
# Monthly mode (legacy / compat)
# ---------------------------------------------------------------------------


def test_filtering_and_alignment_primary_regimes_only_monthly():
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
        assert blk.get("n_obs_daily") is None
    assert "neutral_transition" not in out["regimes"]
    assert out["n_obs_total"] == 48


def test_neutral_transition_not_a_primary_group_monthly():
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


def test_covariance_symmetry_and_corr_diagonal_monthly():
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


def test_beta_output_shape_hac_keys_monthly():
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


def test_gating_suppresses_under_12_monthly():
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


def test_variance_contribution_shares_sum_monthly():
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


def test_csv_stub_rows_when_suppressed_monthly():
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


def test_ledoit_wolf_covariance_when_complete_cases_exist_monthly():
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


def test_ten_year_portfolio_window_metadata_and_csv_daily():
    """Label history can exceed portfolio overlap; stats use sliced returns only (daily)."""

    from src.regime_factor_analytics import REGIME_FACTOR_PORTFOLIO_WINDOW_NOTE

    n_extra_days = 400
    n_full_days = FACTOR_TRADING_DAYS_10Y + n_extra_days
    idx_full_d = _business_daily_range(start="2000-01-03", periods=n_full_days)
    idx_m = _month_end_index(FACTOR_MONTHS_10Y + 60, start_year=2000)
    regimes_full = _anchor_monthly_regimes(_make_labels(idx_m, ("goldilocks",)))
    idx_10y = idx_full_d[-FACTOR_TRADING_DAYS_10Y:]
    rng = np.random.default_rng(99)
    assets_full = pd.DataFrame(
        rng.normal(0.0002, 0.02, (len(idx_full_d), 2)),
        index=idx_full_d,
        columns=["A", "B"],
    )
    factors_full = _factor_frame(idx_full_d, seed=100)
    assets_10y = assets_full.loc[idx_10y]
    factors_10y = factors_full.loc[idx_10y]
    span = {
        "start": idx_m.min().strftime("%Y-%m-%d"),
        "end": idx_m.max().strftime("%Y-%m-%d"),
        "n_months": int(len(idx_m)),
    }
    window = {
        "label": "10Y",
        "target_months": int(FACTOR_MONTHS_10Y),
        "target_weeks": int(FACTOR_WEEKS_10Y),
        "target_trading_days": int(FACTOR_TRADING_DAYS_10Y),
        "analysis_end": idx_10y.max().strftime("%Y-%m-%d"),
        "disclaimer": "unit test disclaimer",
    }
    out = regime_factor_analytics(
        monthly_returns=assets_10y,
        monthly_factor_returns=factors_10y,
        regime_labels=regimes_full,
        weights={"A": 0.5, "B": 0.5},
        regime_label_history_span=span,
        portfolio_regime_analytics_window=window,
        frequency="daily",
    )
    exp_n = int((_expect_ffill_daily_labels(idx_10y, regimes_full) == "goldilocks").sum())
    assert out["n_obs_total"] == len(idx_10y)
    assert out["regimes"]["goldilocks"]["n_obs"] == exp_n
    assert out["regime_label_history_span"]["n_months"] == len(idx_m)
    win_out = out["portfolio_regime_analytics_window"]
    assert win_out["label"] == "10Y"
    assert win_out["actual_n_periods"] == len(idx_10y)
    assert win_out["actual_n_periods"] == FACTOR_TRADING_DAYS_10Y
    assert out["portfolio_regime_analytics_note"] == REGIME_FACTOR_PORTFOLIO_WINDOW_NOTE
    slim = regime_factor_analytics_for_stress_report(out)
    assert slim["regime_label_history_span"]["n_months"] == len(idx_m)
    assert slim["portfolio_regime_analytics_window"]["actual_n_periods"] == FACTOR_TRADING_DAYS_10Y
    summ = regime_factor_analytics_summary(out)
    assert summ["portfolio_regime_analytics_window"]["target_weeks"] == FACTOR_WEEKS_10Y
    assert summ["portfolio_regime_analytics_window"]["target_trading_days"] == FACTOR_TRADING_DAYS_10Y
    frames = regime_factor_analytics_csv_frames(out)
    cov = frames["regime_asset_covariance.csv"]
    assert not cov.empty
    assert int(cov["regime_label_history_n_months"].iloc[0]) == len(idx_m)
    assert cov["portfolio_regime_analytics_window_label"].iloc[0] == "10Y"


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


def test_weekly_gating_uses_month_equivalent():
    from src.stress_factors_macro import macro_quality_status, macro_regime_obs_month_equivalent

    assert macro_regime_obs_month_equivalent(49, frequency="weekly") == 11
    assert macro_quality_status(49, frequency="weekly") == "insufficient_data"
    assert macro_regime_obs_month_equivalent(50, frequency="weekly") == 12
    assert macro_quality_status(50, frequency="weekly") == "low_confidence"
    assert macro_quality_status(10, frequency="monthly") == "insufficient_data"
