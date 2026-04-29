"""Factor covariance regime analytics (no network)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import stress_factors as sf


def _factor_fixture() -> pd.DataFrame:
    idx = pd.date_range("2007-01-05", "2026-02-27", freq="W-FRI")
    rng = np.random.default_rng(42)
    data = rng.normal(scale=0.01, size=(len(idx), len(sf.FACTOR_COLUMN_ORDER)))
    df = pd.DataFrame(data, index=idx, columns=list(sf.FACTOR_COLUMN_ORDER))

    # Make the last two years materially different so covariance_stability_check fires.
    df.iloc[-sf.FACTOR_COVARIANCE_STABILITY_WEEKS :] *= 3.0
    # Keep a simple deterministic relationship for one pair in the base window.
    df.loc[df.index[-260:], "credit"] = 0.5 * df.loc[df.index[-260:], "equity"] + 0.002
    return df


def test_factor_covariance_base_uses_5y_weekly_ddof_and_order() -> None:
    factors = _factor_fixture()
    out = sf.factor_covariance_analytics(
        analysis_end_str="2026-02-28",
        portfolio_betas={"beta_eq": 0.5, "beta_credit": -0.2},
        factor_returns=factors,
    )

    assert out["factor_order"] == list(sf.FACTOR_COLUMN_ORDER)
    expected = factors.tail(sf.FACTOR_COVARIANCE_BASE_WEEKS).loc[:, list(sf.FACTOR_COLUMN_ORDER)].cov(ddof=1)
    got = pd.DataFrame(out["base"]["matrix"]).T.reindex(index=sf.FACTOR_COLUMN_ORDER, columns=sf.FACTOR_COLUMN_ORDER)
    assert np.isclose(got.loc["equity", "equity"], expected.loc["equity", "equity"])
    assert np.isclose(got.loc["equity", "credit"], expected.loc["equity", "credit"])
    assert out["base"]["classification"] == "data_driven"
    assert out["stress_empirical"]["classification"] == "data_driven"
    assert out["stress_overlay"]["classification"] == "hypothetical"


def test_factor_covariance_stress_overlay_deltas_and_zero_fill() -> None:
    factors = _factor_fixture()
    out = sf.factor_covariance_analytics(
        analysis_end_str="2026-02-28",
        portfolio_betas={"beta_eq": 0.5},
        rolling_betas_weekly={"5y": pd.DataFrame({"beta_eq": [0.4, 0.6, 0.5]})},
        factor_returns=factors,
    )

    zero_filled = out["exposure_vector"]["zero_filled_beta_keys"]
    assert "beta_credit" in zero_filled
    assert out["stress_overlay"]["overlay_deltas"]
    first_delta = out["stress_overlay"]["overlay_deltas"][0]
    assert "pre_overlay_cov" in first_delta
    assert "post_overlay_cov" in first_delta
    assert first_delta["clamp_reason"]

    empirical = pd.DataFrame(out["stress_empirical"]["matrix"]).T
    overlay = pd.DataFrame(out["stress_overlay"]["matrix"]).T
    assert not empirical.equals(overlay)
    # The empirical block is still the raw stress covariance, not overwritten by overlay.
    expected_emp = sf._factor_covariance_matrix(sf._stress_empirical_rows(factors.loc[:, list(sf.FACTOR_COLUMN_ORDER)]))
    assert np.isclose(empirical.loc["equity", "credit"], expected_emp.loc["equity", "credit"])


def test_factor_risk_sensitivity_rc_and_covariance_stability_flags() -> None:
    factors = _factor_fixture()
    betas = {
        "beta_eq": 0.7,
        "beta_rr": -0.3,
        "beta_inf": 0.1,
        "beta_credit": -0.4,
        "beta_usd": 0.2,
        "beta_cmd": 0.1,
        "beta_vix": -0.2,
        "beta_us_growth": 0.05,
        "beta_oil": -0.1,
    }
    rolling = {
        "5y": pd.DataFrame(
            {
                beta_key: [value - 0.1, value, value + 0.1]
                for beta_key, value in betas.items()
            }
        )
    }
    out = sf.factor_covariance_analytics(
        analysis_end_str="2026-02-28",
        portfolio_betas=betas,
        rolling_betas_weekly=rolling,
        factor_returns=factors,
    )

    base_cov = pd.DataFrame(out["base"]["matrix"]).T.reindex(index=sf.FACTOR_COLUMN_ORDER, columns=sf.FACTOR_COLUMN_ORDER)
    beta_vec = np.array([betas[sf.FACTOR_TO_BETA_KEY[f]] for f in sf.FACTOR_COLUMN_ORDER])
    expected_var = float(beta_vec.T @ base_cov.values.astype(float) @ beta_vec)
    assert np.isclose(out["portfolio_factor_risk"]["base"]["portfolio_factor_variance"], expected_var)

    sens = out["beta_sensitivity"]["base"]
    assert sens["variance_min"] <= sens["variance_current"] <= sens["variance_max"]
    rc_rows = out["portfolio_factor_rc"]["base"]
    assert np.isclose(sum(float(row["rc_share"]) for row in rc_rows), 1.0)
    assert "overall_flag" in out["RC_stability_flag"]
    assert out["covariance_stability_check"]["threshold_pct"] == 35.0
    assert out["covariance_stability_check"]["overall_flag"] is True


def test_factor_covariance_comparison_separates_empirical_and_overlay() -> None:
    out = sf.factor_covariance_analytics(
        analysis_end_str="2026-02-28",
        portfolio_betas={"beta_eq": 0.4, "beta_credit": -0.2},
        factor_returns=_factor_fixture(),
    )

    comparison = out["comparison"]
    assert "empirical_change" in comparison
    assert "overlay_amplification" in comparison
    assert comparison["empirical_change"][0]["factor_i"] in sf.FACTOR_COLUMN_ORDER
    assert comparison["overlay_amplification"][0]["factor_i"] in sf.FACTOR_COLUMN_ORDER
