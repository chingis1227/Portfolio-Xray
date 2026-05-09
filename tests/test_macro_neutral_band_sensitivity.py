"""Sensitivity tests for the neutral-band threshold (±0.20 / ±0.25 / ±0.35)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import stress_factors_macro as sfm
from src.pandas_compat import MONTH_END_FREQ


def _panel_with_known_score_path(target_growth: list[float], target_inflation: list[float]) -> tuple[pd.DataFrame, dict]:
    n = len(target_growth)
    assert n == len(target_inflation)
    pad = sfm.MACRO_SCORE_MIN_PERIODS + 5
    idx = pd.date_range("2010-01-31", periods=n + pad, freq=MONTH_END_FREQ)
    growth_signal = np.concatenate([np.zeros(pad), np.array(target_growth)])
    inflation_signal = np.concatenate([np.zeros(pad), np.array(target_inflation)])
    rng = np.random.default_rng(0)
    noise = pd.Series(rng.normal(scale=0.01, size=len(idx)), index=idx)

    panel = pd.DataFrame(
        {
            "payems__level": pd.Series(growth_signal * 5.0, index=idx) + noise,
            "payems__momentum": pd.Series(growth_signal * 5.0, index=idx) + noise,
            "unrate__level": pd.Series(-growth_signal * 5.0, index=idx) + noise,
            "unrate__momentum": pd.Series(-growth_signal * 5.0, index=idx) + noise,
            "core_cpi_3m_ann__level": pd.Series(inflation_signal * 5.0, index=idx) + noise,
            "core_cpi_3m_ann__momentum": pd.Series(inflation_signal * 5.0, index=idx) + noise,
            "core_pce_3m_ann__level": pd.Series(inflation_signal * 5.0, index=idx) + noise,
            "core_pce_3m_ann__momentum": pd.Series(inflation_signal * 5.0, index=idx) + noise,
        }
    )
    meta = {
        "data_sources_used": {k: "fred" for k in {"payems", "unrate", "core_cpi_3m_ann", "core_pce_3m_ann"}},
        "available_indicators": ["payems", "unrate", "core_cpi_3m_ann", "core_pce_3m_ann"],
        "unavailable_indicators": [],
        "indicator_specs": {spec.key: sfm._spec_meta(spec) for spec in sfm.INDICATORS},
    }
    return panel, meta


def test_strong_signal_rows_label_identically_across_bands() -> None:
    target_growth = [1.0] * 12
    target_inflation = [-1.0] * 12
    panel, meta = _panel_with_known_score_path(target_growth, target_inflation)

    labels_by_band = {}
    for band in (0.20, 0.25, 0.35):
        scores = sfm.compute_macro_scores(panel, meta, neutral_band=band)
        last = scores["regime_unlagged"].dropna().iloc[-1]
        labels_by_band[band] = last

    assert labels_by_band[0.20] == labels_by_band[0.25] == labels_by_band[0.35] == "goldilocks"


def test_borderline_label_quadrant_sensitivity_across_bands() -> None:
    """A borderline composite score crosses the band threshold smoothly."""

    g, p = 0.30, 0.30
    assert sfm._label_quadrant(g, p, neutral_band=0.35) == "neutral_transition"
    assert sfm._label_quadrant(g, p, neutral_band=0.25) == "reflation"
    assert sfm._label_quadrant(g, p, neutral_band=0.20) == "reflation"


def test_neutral_band_does_not_change_relative_label_distribution_too_much() -> None:
    rng = np.random.default_rng(42)
    target_growth = rng.uniform(-1.0, 1.0, size=120).tolist()
    target_inflation = rng.uniform(-1.0, 1.0, size=120).tolist()
    panel, meta = _panel_with_known_score_path(target_growth, target_inflation)

    counts_by_band: dict[float, dict[str, int]] = {}
    for band in (0.20, 0.25, 0.35):
        scores = sfm.compute_macro_scores(panel, meta, neutral_band=band)
        labels = scores["regime_unlagged"].dropna().iloc[-len(target_growth):]
        counts_by_band[band] = {
            label: int((labels == label).sum()) for label in sfm.MACRO_REGIME_NAMES
        }

    # As the band widens, neutral_transition share is monotonically non-decreasing.
    n20 = counts_by_band[0.20]["neutral_transition"]
    n25 = counts_by_band[0.25]["neutral_transition"]
    n35 = counts_by_band[0.35]["neutral_transition"]
    assert n20 <= n25 <= n35
