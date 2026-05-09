from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.pandas_compat import MONTH_END_FREQ
from src.stress_factors_macro import (
    INDICATORS,
    MACRO_CLIPPED_Z_MAX_ABS_DEFAULT,
    MACRO_PERSISTENCE_MONTHS_DEFAULT,
    MACRO_SCORING_METHOD_DEFAULT,
    _apply_persistence,
    _bucket_signal,
    _clipped_signal,
    build_regime_label_quality_check,
    compute_macro_scores,
)


def test_clipped_signal_clipping_and_rescaling() -> None:
    assert _clipped_signal(0.0, clip=2.0) == 0.0
    assert _clipped_signal(1.0, clip=2.0) == 0.5
    assert _clipped_signal(2.0, clip=2.0) == 1.0
    assert _clipped_signal(2.5, clip=2.0) == 1.0
    assert _clipped_signal(-1.5, clip=2.0) == -0.75
    assert _clipped_signal(-3.0, clip=2.0) == -1.0
    assert np.isnan(_clipped_signal(float("nan"), clip=2.0))


def test_clipped_signal_preserves_more_signal_than_discrete() -> None:
    """Clipped signals retain mid-range information that discrete buckets discard."""

    z_values = [-1.4, -0.7, -0.3, 0.0, 0.3, 0.7, 1.4]
    discrete = [_bucket_signal(z) for z in z_values]
    clipped = [_clipped_signal(z, clip=2.0) for z in z_values]
    assert discrete == [-1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 1.0]
    assert clipped == [-0.7, -0.35, -0.15, 0.0, 0.15, 0.35, 0.7]


def test_apply_persistence_requires_k_consecutive_to_switch() -> None:
    seq = [
        "neutral_transition",
        "reflation",
        "neutral_transition",
        "reflation",
        "reflation",
        "stagflation",
        "neutral_transition",
        "stagflation",
    ]
    smoothed = _apply_persistence(seq, k=2)
    assert smoothed == [
        "neutral_transition",
        "neutral_transition",
        "neutral_transition",
        "reflation",
        "reflation",
        "reflation",
        "reflation",
        "reflation",
    ]


def test_apply_persistence_disabled_for_k_le_1() -> None:
    seq = ["a", "b", "a", "b"]
    assert _apply_persistence(seq, k=1) == seq
    assert _apply_persistence(seq, k=0) == seq


def _build_synthetic_panel() -> tuple[pd.DataFrame, dict]:
    """Build a panel with two clear oscillating sine waves on growth/inflation indicators."""

    idx = pd.date_range(start="1990-01-31", periods=200, freq=MONTH_END_FREQ)
    rng = np.random.default_rng(42)
    rows = {}
    growth_signal = np.sin(np.linspace(0, 12 * np.pi, len(idx)))
    inflation_signal = np.cos(np.linspace(0, 8 * np.pi, len(idx)))
    for spec in INDICATORS:
        if spec.axis == "growth":
            base = growth_signal
        else:
            base = inflation_signal
        noise = rng.normal(scale=0.1, size=len(idx))
        level = base + noise
        rows[f"{spec.key}__level"] = level
        rows[f"{spec.key}__momentum"] = pd.Series(level, index=idx).diff().fillna(0.0).to_numpy()
    panel = pd.DataFrame(rows, index=idx)
    meta = {
        "data_sources_used": {spec.key: "synthetic" for spec in INDICATORS},
        "indicator_specs": {spec.key: {"axis": spec.axis, "block": spec.block} for spec in INDICATORS},
    }
    return panel, meta


def test_compute_macro_scores_supports_clipped_z_and_persistence() -> None:
    panel, meta = _build_synthetic_panel()
    discrete = compute_macro_scores(panel, meta, neutral_band=0.20, scoring_method="discrete")
    clipped = compute_macro_scores(panel, meta, neutral_band=0.20, scoring_method="clipped_z")
    assert "regime" in discrete.columns
    assert "regime" in clipped.columns
    assert "regime_unlagged_raw" in discrete.columns
    assert (discrete["growth_score"].abs() >= clipped["growth_score"].abs()).mean() >= 0.5

    # Persistence k=2 should not introduce one-month regimes.
    persisted = compute_macro_scores(
        panel,
        meta,
        neutral_band=0.20,
        scoring_method="discrete",
        persistence_months=2,
    )
    raw_unlagged = persisted["regime_unlagged_raw"].astype(str).tolist()
    smoothed = persisted["regime_unlagged"].astype(str).tolist()
    raw_changes = sum(1 for i in range(1, len(raw_unlagged)) if raw_unlagged[i] != raw_unlagged[i - 1])
    smoothed_changes = sum(1 for i in range(1, len(smoothed)) if smoothed[i] != smoothed[i - 1])
    assert smoothed_changes <= raw_changes


def test_compute_macro_scores_rejects_unknown_scoring_method() -> None:
    panel, meta = _build_synthetic_panel()
    with pytest.raises(ValueError):
        compute_macro_scores(panel, meta, scoring_method="bogus")


def test_quality_check_excludes_warmup_months() -> None:
    """Regime quality must count only months with valid scores, not warmup."""

    idx = pd.date_range(start="2000-01-31", periods=24, freq=MONTH_END_FREQ)
    seq = ["neutral_transition"] * 24
    growth = [float("nan")] * 12 + [0.6] * 12
    infl = [float("nan")] * 12 + [-0.6] * 12
    regimes = [None] * 12 + ["goldilocks"] * 12
    frame = pd.DataFrame(
        {
            "regime": regimes,
            "regime_unlagged": seq,
            "growth_score": growth,
            "inflation_score": infl,
        },
        index=idx,
    )
    out = build_regime_label_quality_check(
        labels_with_regime=frame,
        coverage_tier="full",
        optional_blocks_missing=set(),
        available_blocks={"growth_labor"},
        missing_blocks=set(),
        neutral_band=0.20,
    )
    assert out["status"] == "available"
    assert out["history_months"] == 12
    assert out["warmup_months_excluded"] == 12
    assert out["rows_input_total"] == 24
    assert out["by_regime"]["goldilocks"]["n_obs"] == 12


def test_default_constants_reflect_evidence_based_decision() -> None:
    """Documents the chosen defaults so accidental changes break the test."""

    assert MACRO_SCORING_METHOD_DEFAULT == "discrete"
    assert MACRO_PERSISTENCE_MONTHS_DEFAULT == 2
    assert MACRO_CLIPPED_Z_MAX_ABS_DEFAULT == 2.0
