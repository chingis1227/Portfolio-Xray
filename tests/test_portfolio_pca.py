from __future__ import annotations

import numpy as np
import pandas as pd

from src import stress_factors as sf


def _weekly_index(n: int = 260) -> pd.DatetimeIndex:
    return pd.date_range("2021-01-01", periods=n, freq="W-FRI")


def test_portfolio_pca_common_factor_has_high_raw_pc1_and_factor_correlation() -> None:
    idx = _weekly_index()
    rng = np.random.default_rng(1)
    factor = rng.normal(scale=0.02, size=len(idx))
    returns = pd.DataFrame(
        {
            "A": 1.00 * factor + rng.normal(scale=0.002, size=len(idx)),
            "B": 0.90 * factor + rng.normal(scale=0.002, size=len(idx)),
            "C": 1.10 * factor + rng.normal(scale=0.002, size=len(idx)),
        },
        index=idx,
    )
    factors = pd.DataFrame({"equity": factor}, index=idx)

    out = sf.portfolio_pca_diagnostics_from_weekly_returns(returns, factor_returns=factors)

    raw_cov = out["raw"]["covariance_pca"]
    assert out["status"] == "available"
    assert raw_cov["pc1_explained_variance_ratio"] > 0.95
    top = raw_cov["pc1_factor_correlations"]["top_abs_correlations"][0]
    assert top["factor"] == "equity"
    assert abs(top["correlation"]) > 0.95


def test_portfolio_pca_correlation_differs_from_covariance_when_volatility_dominates() -> None:
    idx = _weekly_index()
    rng = np.random.default_rng(2)
    returns = pd.DataFrame(
        {
            "HIGH_VOL": rng.normal(scale=0.10, size=len(idx)),
            "LOW_VOL_1": rng.normal(scale=0.01, size=len(idx)),
            "LOW_VOL_2": rng.normal(scale=0.01, size=len(idx)),
        },
        index=idx,
    )

    out = sf.portfolio_pca_diagnostics_from_weekly_returns(returns)
    cov_pc1 = out["raw"]["covariance_pca"]["pc1_explained_variance_ratio"]
    corr_pc1 = out["raw"]["correlation_pca"]["pc1_explained_variance_ratio"]

    assert cov_pc1 > 0.90
    assert corr_pc1 < 0.45
    assert out["raw"]["covariance_pca"]["interpretation"] == "risk_dominance"
    assert out["raw"]["correlation_pca"]["interpretation"] == "structure"


def test_portfolio_pca_residual_reduces_pc1_after_factor_removal() -> None:
    idx = _weekly_index()
    rng = np.random.default_rng(3)
    factor = rng.normal(scale=0.025, size=len(idx))
    returns = pd.DataFrame(
        {
            "A": 0.8 * factor + rng.normal(scale=0.010, size=len(idx)),
            "B": 1.1 * factor + rng.normal(scale=0.010, size=len(idx)),
            "C": 0.9 * factor + rng.normal(scale=0.010, size=len(idx)),
        },
        index=idx,
    )
    factors = pd.DataFrame({"equity": factor}, index=idx)

    out = sf.portfolio_pca_diagnostics_from_weekly_returns(returns, factor_returns=factors)
    raw_pc1 = out["raw"]["covariance_pca"]["pc1_explained_variance_ratio"]
    residual_pc1 = out["residual"]["covariance_pca"]["pc1_explained_variance_ratio"]

    assert out["residual"]["status"] == "available"
    assert residual_pc1 < raw_pc1


def test_portfolio_pca_enb_formula_and_component_sign_are_deterministic() -> None:
    idx = _weekly_index()
    rng = np.random.default_rng(4)
    common = rng.normal(size=len(idx))
    returns = pd.DataFrame(
        {
            "A": common + rng.normal(scale=0.05, size=len(idx)),
            "B": common + rng.normal(scale=0.05, size=len(idx)),
            "C": common + rng.normal(scale=0.05, size=len(idx)),
        },
        index=idx,
    )

    out = sf.portfolio_pca_diagnostics_from_weekly_returns(returns)
    block = out["raw"]["correlation_pca"]
    ratios = np.asarray(block["explained_variance_ratio"], dtype=float)
    expected_enb = 1.0 / np.sum(ratios**2)
    pc1_loadings = block["components"][0]["loadings"]
    max_asset = max(pc1_loadings, key=lambda asset: abs(pc1_loadings[asset]))

    assert np.isclose(block["effective_number_of_bets"], expected_enb)
    assert pc1_loadings[max_asset] > 0
    assert np.all(ratios >= -1e-12)
    assert np.sum(ratios) <= 1.0 + 1e-10


def test_portfolio_pca_rolling_pc1_summary_fields() -> None:
    idx = _weekly_index(140)
    rng = np.random.default_rng(5)
    common = rng.normal(scale=0.02, size=len(idx))
    strength = np.linspace(0.1, 1.0, len(idx))
    returns = pd.DataFrame(
        {
            "A": strength * common + rng.normal(scale=0.015, size=len(idx)),
            "B": strength * common + rng.normal(scale=0.015, size=len(idx)),
            "C": strength * common + rng.normal(scale=0.015, size=len(idx)),
        },
        index=idx,
    )

    out = sf.portfolio_pca_diagnostics_from_weekly_returns(returns, window_weeks=140)
    summary = out["raw"]["covariance_pca"]["rolling_pc1"]["summary"]

    assert summary["n_windows"] > 1
    assert "std" in summary
    assert "trend_slope_per_year" in summary
    assert "latest" in summary
    assert "p90" in summary
    assert summary["stability_severity"] in {"low", "moderate", "high"}


def test_portfolio_pca_unavailable_for_insufficient_rows_or_assets() -> None:
    idx = _weekly_index(40)
    returns = pd.DataFrame({"A": np.arange(len(idx), dtype=float), "B": np.arange(len(idx), dtype=float)}, index=idx)
    short = sf.portfolio_pca_diagnostics_from_weekly_returns(returns, window_weeks=40)
    assert short["status"] == "unavailable"
    assert short["reason"] == "insufficient_aligned_weekly_returns"

    one_asset = sf.portfolio_pca_diagnostics_from_weekly_returns(returns[["A"]], window_weeks=40)
    assert one_asset["status"] == "unavailable"
