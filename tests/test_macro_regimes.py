from __future__ import annotations

import numpy as np
import pandas as pd

from src import stress_factors as sf


def _frames(n: int = 220) -> tuple[pd.Series, pd.DataFrame]:
    idx = pd.date_range("2020-01-03", periods=n, freq="W-FRI")
    rng = np.random.default_rng(123)
    factors = pd.DataFrame(
        rng.normal(scale=0.01, size=(n, len(sf.BASE_FACTOR_COLUMN_ORDER))),
        index=idx,
        columns=list(sf.BASE_FACTOR_COLUMN_ORDER),
    )
    factors["us_growth"] = np.sin(np.linspace(0, 10, n)) + rng.normal(scale=0.05, size=n)
    factors["inflation"] = np.cos(np.linspace(0, 8, n)) + rng.normal(scale=0.05, size=n)
    factors["commodity"] = factors["inflation"] * 0.4 + rng.normal(scale=0.05, size=n)
    beta = np.array([0.3, -0.1, 0.2, 0.15, -0.05, 0.08, -0.02, 0.12])
    y = pd.Series(factors.loc[:, list(sf.BASE_FACTOR_COLUMN_ORDER)].values @ beta, index=idx)
    return y, factors


def _axis(labels: list[str], index: pd.DatetimeIndex, *, latest_near_zero: bool = False) -> pd.DataFrame:
    growth = []
    pressure = []
    for label in labels:
        if label == "goldilocks":
            growth.append(1.0)
            pressure.append(-1.0)
        elif label == "reflation":
            growth.append(1.0)
            pressure.append(1.0)
        elif label == "stagflation":
            growth.append(-1.0)
            pressure.append(1.0)
        else:
            growth.append(-1.0)
            pressure.append(-1.0)
    if latest_near_zero:
        growth[-1] = 0.1
    return pd.DataFrame(
        {"growth_score": growth, "inflation_pressure_score": pressure, "regime": labels},
        index=index[: len(labels)],
    )


def test_macro_regime_labels_cover_four_quadrants_without_neutral() -> None:
    assert sf._macro_regime_label(1.0, -1.0) == "goldilocks"
    assert sf._macro_regime_label(1.0, 1.0) == "reflation"
    assert sf._macro_regime_label(-1.0, 1.0) == "stagflation"
    assert sf._macro_regime_label(-1.0, -1.0) == "recession_disinflation"
    assert "neutral" not in sf.MACRO_REGIME_NAMES


def test_macro_regime_output_contract_and_axis_model_version() -> None:
    y, factors = _frames(220)
    out = sf.macro_regime_diagnostics_from_frames(y, factors, "2024-03-22")

    assert out["axis_model"]["version"] == "internal_market_proxy_v1"
    assert "inflation_pressure_proxy" in out["axis_model"]
    assert "growth_score" in out["axis_scores_latest"]
    assert "inflation_pressure_score" in out["axis_scores_latest"]
    assert out["method_disclaimer"] == sf.MACRO_REGIME_METHOD_DISCLAIMER


def test_macro_regime_confidence_low_and_transition_warning_near_zero(monkeypatch) -> None:
    y, factors = _frames(130)
    labels = ["reflation"] * 80 + ["goldilocks"] * 50
    monkeypatch.setattr(
        sf,
        "_macro_axis_frame",
        lambda _f: _axis(labels, factors.index, latest_near_zero=True),
    )

    out = sf.macro_regime_diagnostics_from_frames(y, factors, "2022-06-24")

    assert out["current_regime"] == "goldilocks"
    assert out["regime_confidence"] == "low"
    assert out["regime_transition_warning"] is True


def test_macro_regime_quality_status_thresholds() -> None:
    assert sf._macro_quality_status(0) == "no_observations"
    assert sf._macro_quality_status(35) == "insufficient_observations"
    assert sf._macro_quality_status(36) == "low_confidence"
    assert sf._macro_quality_status(51) == "low_confidence"
    assert sf._macro_quality_status(52) == "usable"
    assert sf._macro_quality_status(103) == "usable"
    assert sf._macro_quality_status(104) == "reliable"


def test_macro_regime_fallback_and_shrinkage_methods(monkeypatch) -> None:
    y, factors = _frames(170)
    labels = (
        ["reflation"] * 40
        + ["stagflation"] * 20
        + ["recession_disinflation"] * 110
    )
    monkeypatch.setattr(sf, "_macro_axis_frame", lambda _f: _axis(labels, factors.index))

    out = sf.macro_regime_diagnostics_from_frames(y, factors, "2023-04-07")

    low = out["regimes"]["reflation"]
    insufficient = out["regimes"]["stagflation"]
    none = out["regimes"]["goldilocks"]
    reliable = out["regimes"]["recession_disinflation"]
    assert low["quality_status"] == "low_confidence"
    assert low["used_fallback"] is True
    assert low["fallback_method"] == "linear_shrinkage_to_base_10y"
    assert low["fallback_target"] == "base_10y"
    assert 0.0 <= low["shrinkage_weight_regime"] <= 1.0
    assert insufficient["quality_status"] == "insufficient_observations"
    assert insufficient["used_fallback"] is True
    assert insufficient["fallback_method"] == "fallback_to_base_10y"
    assert none["quality_status"] == "no_observations"
    assert none["fallback_method"] == "no_observations_base_10y_reference_only"
    assert reliable["quality_status"] == "reliable"
    assert reliable["used_fallback"] is False


def test_macro_regime_negative_rc_serializes_with_interpretation() -> None:
    cov = pd.DataFrame(
        [[1.0, -0.9], [-0.9, 1.0]],
        index=["equity", "credit"],
        columns=["equity", "credit"],
    ).reindex(index=sf.BASE_FACTOR_COLUMN_ORDER, columns=sf.BASE_FACTOR_COLUMN_ORDER).fillna(0.0)
    betas = {"beta_eq": 1.0, "beta_credit": 0.5}

    rows = sf._macro_factor_rc(cov, betas)

    assert any(row["rc_sign"] == "negative" for row in rows)
    assert any(row["interpretation"] == "hedging_or_diversifying_contribution" for row in rows)


def test_macro_regime_csv_frames_include_required_outputs(monkeypatch) -> None:
    y, factors = _frames(130)
    labels = ["reflation"] * 60 + ["goldilocks"] * 70
    monkeypatch.setattr(sf, "_macro_axis_frame", lambda _f: _axis(labels, factors.index))

    out = sf.macro_regime_diagnostics_from_frames(y, factors, "2022-06-24")
    frames = sf.macro_regime_csv_frames(out)

    assert "macro_regime_labels_weekly.csv" in frames
    assert "macro_regime_factor_betas.csv" in frames
    assert "macro_regime_factor_covariance.csv" in frames
    assert "macro_regime_factor_rc.csv" in frames
