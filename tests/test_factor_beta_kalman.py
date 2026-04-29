"""Kalman factor beta diagnostics (no network)."""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from src import stress_factors as sf


def _factor_frame(n: int, seed: int = 123) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-03", periods=n, freq="W-FRI")
    vals = rng.normal(scale=0.025, size=(n, len(sf.FACTOR_COLUMN_ORDER)))
    return pd.DataFrame(vals, index=idx, columns=list(sf.FACTOR_COLUMN_ORDER))


def _test_output_dir(name: str) -> Path:
    root = Path.cwd() / "output" / "codex_test_artifacts" / name
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_kalman_constant_beta_tracks_true_exposure() -> None:
    factors = _factor_frame(180)
    y = 0.65 * factors["equity"] - 0.25 * factors["credit"]

    report, history, latest = sf.kalman_factor_betas_from_frames(
        y,
        factors,
        factor_betas_5y={"beta_eq": 0.65, "beta_credit": -0.25},
    )

    assert report["status"] == "available"
    assert abs(report["latest"]["beta_eq"] - 0.65) < 0.08
    assert abs(report["latest"]["beta_credit"] + 0.25) < 0.08
    assert not history.empty
    assert "beta_eq" in latest["beta"].values


def test_kalman_step_change_moves_toward_new_regime_smoothly() -> None:
    factors = _factor_frame(220, seed=456)
    first = 0.25 * factors["equity"].iloc[:110]
    second = 1.05 * factors["equity"].iloc[110:]
    y = pd.concat([first, second]).sort_index()

    report, history, _latest = sf.kalman_factor_betas_from_frames(y, factors)

    assert report["status"] == "available"
    before = float(history["beta_eq"].iloc[100])
    after = float(history["beta_eq"].iloc[-1])
    assert before < 0.60
    assert after > 0.65
    assert after < 1.25


def test_kalman_caps_excessive_beta_and_preserves_raw_value() -> None:
    factors = _factor_frame(160, seed=789)
    y = 5.0 * factors["equity"]

    report, _history, latest = sf.kalman_factor_betas_from_frames(y, factors)

    cap = report["cap_diagnostics"]["beta_eq"]
    assert report["latest"]["beta_eq"] == 3.0
    assert report["latest_raw"]["beta_eq"] > 3.0
    assert cap["was_capped"] is True
    assert cap["capped_value"] == 3.0
    row = latest[latest["beta"] == "beta_eq"].iloc[0]
    assert bool(row["was_capped"]) is True


def test_kalman_divergence_flags_sign_absolute_and_relative_gaps() -> None:
    latest = {"beta_eq": -0.10, "beta_credit": 0.60, "beta_usd": 0.12}
    five_year = {"beta_eq": 0.10, "beta_credit": 0.30, "beta_usd": 0.04}

    out = sf._kalman_divergence_vs_5y(latest, five_year)

    assert out["by_beta"]["beta_eq"]["reason"] == "sign_difference"
    assert out["by_beta"]["beta_credit"]["reason"] == "abs_gap"
    assert out["by_beta"]["beta_usd"]["reason"] == "relative_gap"
    assert set(out["divergent_betas"]) == {"beta_eq", "beta_credit", "beta_usd"}


def test_kalman_uncertainty_class_thresholds() -> None:
    assert sf._kalman_uncertainty_class(0.15) == "low"
    assert sf._kalman_uncertainty_class(0.35) == "moderate"
    assert sf._kalman_uncertainty_class(0.351) == "high"


def test_kalman_inner_alignment_drops_missing_rows() -> None:
    factors = _factor_frame(80)
    y = 0.4 * factors["equity"]
    y.iloc[3] = np.nan
    factors.iloc[5, factors.columns.get_loc("credit")] = np.nan

    report, _history, _latest = sf.kalman_factor_betas_from_frames(y, factors)

    assert report["status"] == "available"
    assert report["n_observations"] == 78


def test_kalman_too_few_observations_returns_unavailable() -> None:
    factors = _factor_frame(12)
    y = 0.4 * factors["equity"]

    report, history, latest = sf.kalman_factor_betas_from_frames(y, factors)

    assert report["status"] == "unavailable"
    assert "insufficient_observations" in report["diagnostics"]["warning_codes"]
    assert history.empty
    assert latest.empty


def test_attach_kalman_factor_betas_preserves_raw_ols_fields(monkeypatch) -> None:
    def fake_compute(**_kwargs):
        report = {
            "status": "available",
            "latest": {"beta_eq": 0.2},
            "latest_raw": {"beta_eq": 0.2},
            "latest_date": "2024-01-05",
            "n_observations": 60,
        }
        history = pd.DataFrame({"beta_eq": [0.1, 0.2]}, index=pd.date_range("2023-12-29", periods=2, freq="W-FRI"))
        latest = pd.DataFrame(
            [{"beta": "beta_eq", "latest_raw": 0.2, "latest": 0.2, "divergence_vs_5y": False}]
        )
        return report, history, latest

    monkeypatch.setattr(sf, "compute_portfolio_kalman_factor_betas_weekly", fake_compute)
    stress_report = {
        "factor_betas_5y": {"beta_eq": 0.3},
        "factor_betas_10y": {"beta_eq": 0.4},
        "factor_betas": {"beta_eq": 0.3},
    }
    out_dir = _test_output_dir("kalman")

    try:
        out = sf.attach_kalman_factor_betas_to_stress_report(
            stress_report,
            weights={"AAA": 1.0},
            tickers=["AAA"],
            analysis_end_str="2024-01-31",
            output_dir_csv=out_dir,
        )

        assert out["factor_betas_5y"] == {"beta_eq": 0.3}
        assert out["factor_betas"] == {"beta_eq": 0.3}
        assert out["factor_betas_kalman"]["latest"] == {"beta_eq": 0.2}
        assert (out_dir / "kalman_factor_betas_weekly.csv").is_file()
        assert (out_dir / "kalman_factor_betas_latest.csv").is_file()
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
