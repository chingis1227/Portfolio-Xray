"""Tests for the primary_regime + transition_flag/reason classification layer."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.pandas_compat import MONTH_END_FREQ
from src.stress_factors_macro import (
    INDICATORS,
    MACRO_PRIMARY_REGIME_NAMES,
    MACRO_REGIME_NAMES,
    MACRO_TRANSITION_REASON_BOTH,
    MACRO_TRANSITION_REASON_GROWTH,
    MACRO_TRANSITION_REASON_INFLATION,
    _label_quadrant,
    _primary_quadrant,
    _transition_status,
    build_regime_label_quality_check,
    compute_macro_scores,
)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_primary_quadrant_uses_sign_only() -> None:
    assert _primary_quadrant(0.05, -0.05) == "goldilocks"
    assert _primary_quadrant(0.05, 0.05) == "reflation"
    assert _primary_quadrant(-0.05, 0.05) == "stagflation"
    assert _primary_quadrant(-0.05, -0.05) == "recession_disinflation"
    assert _primary_quadrant(0.0, 0.0) == "reflation"  # both >= 0
    assert _primary_quadrant(0.0, -0.001) == "goldilocks"
    assert _primary_quadrant(float("nan"), 0.5) is None
    assert _primary_quadrant(0.5, float("nan")) is None


def test_transition_status_reasons() -> None:
    band = 0.20
    assert _transition_status(0.05, 0.05, neutral_band=band) == (
        True,
        MACRO_TRANSITION_REASON_BOTH,
    )
    assert _transition_status(0.05, -0.50, neutral_band=band) == (
        True,
        MACRO_TRANSITION_REASON_GROWTH,
    )
    assert _transition_status(-0.50, 0.05, neutral_band=band) == (
        True,
        MACRO_TRANSITION_REASON_INFLATION,
    )
    assert _transition_status(0.50, -0.50, neutral_band=band) == (False, None)
    assert _transition_status(float("nan"), 0.5, neutral_band=band) == (False, None)


def test_legacy_label_quadrant_still_returns_neutral_transition() -> None:
    """Legacy 5-bucket helper preserved for backward compatibility."""

    band = 0.20
    assert _label_quadrant(0.05, 0.05, neutral_band=band) == "neutral_transition"
    assert _label_quadrant(0.30, -0.30, neutral_band=band) == "goldilocks"
    assert _label_quadrant(float("nan"), 0.5, neutral_band=band) == "neutral_transition"
    assert "neutral_transition" not in MACRO_PRIMARY_REGIME_NAMES
    assert "neutral_transition" in MACRO_REGIME_NAMES


# ---------------------------------------------------------------------------
# compute_macro_scores: primary regime + legacy + transition columns
# ---------------------------------------------------------------------------


def _build_panel_with_axis_path(
    growth_path: list[float], inflation_path: list[float]
) -> tuple[pd.DataFrame, dict]:
    n = len(growth_path)
    pad = 70  # enough warmup for the rolling z-score (min_periods=60)
    idx = pd.date_range("2010-01-31", periods=n + pad, freq=MONTH_END_FREQ)
    growth_signal = np.concatenate([np.zeros(pad), np.array(growth_path)])
    inflation_signal = np.concatenate([np.zeros(pad), np.array(inflation_path)])
    rng = np.random.default_rng(0)
    noise = pd.Series(rng.normal(scale=0.02, size=len(idx)), index=idx)
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
        },
        index=idx,
    )
    meta = {
        "data_sources_used": {
            k: "fred" for k in {"payems", "unrate", "core_cpi_3m_ann", "core_pce_3m_ann"}
        },
        "available_indicators": ["payems", "unrate", "core_cpi_3m_ann", "core_pce_3m_ann"],
        "unavailable_indicators": [],
        "indicator_specs": {spec.key: {"axis": spec.axis, "block": spec.block} for spec in INDICATORS},
    }
    return panel, meta


def test_compute_macro_scores_emits_primary_and_legacy_columns() -> None:
    panel, meta = _build_panel_with_axis_path([1.0] * 12, [-1.0] * 12)
    scores = compute_macro_scores(panel, meta, neutral_band=0.20, persistence_months=1)
    expected_cols = {
        "regime",
        "regime_unlagged",
        "regime_unlagged_raw",
        "regime_legacy",
        "regime_legacy_unlagged",
        "regime_legacy_unlagged_raw",
        "transition_flag",
        "transition_flag_unlagged",
        "transition_reason",
        "transition_reason_unlagged",
    }
    assert expected_cols.issubset(set(scores.columns))

    primary = scores["regime_unlagged_raw"].dropna().tolist()
    assert primary, "primary regime series should be non-empty for a strong signal"
    assert set(primary).issubset(set(MACRO_PRIMARY_REGIME_NAMES))
    assert "neutral_transition" not in set(primary)


def test_primary_regime_assigns_one_of_four_quadrants_for_every_scored_month() -> None:
    panel, meta = _build_panel_with_axis_path([0.05] * 24 + [-0.05] * 24, [0.05] * 24 + [-0.05] * 24)
    scores = compute_macro_scores(panel, meta, neutral_band=0.20, persistence_months=1)
    valid = scores.dropna(subset=["growth_score", "inflation_score"])
    # Every scored month must carry a primary regime (no NaN, no neutral_transition).
    primary_values = set(valid["regime_unlagged_raw"].astype(str))
    assert primary_values.issubset(set(MACRO_PRIMARY_REGIME_NAMES))


def test_transition_flag_wired_consistently_with_score_band() -> None:
    """transition_flag/reason at every scored row must equal the helper output."""

    panel, meta = _build_panel_with_axis_path(
        [0.4] * 6 + [-0.4] * 6 + [0.0] * 6 + [-0.4] * 6,
        [0.4] * 6 + [-0.4] * 6 + [0.0] * 6 + [0.4] * 6,
    )
    band = 0.20
    scores = compute_macro_scores(panel, meta, neutral_band=band, persistence_months=1)
    valid = scores.dropna(subset=["growth_score", "inflation_score"])
    for _, row in valid.iterrows():
        expected_flag, expected_reason = _transition_status(
            row["growth_score"], row["inflation_score"], neutral_band=band
        )
        actual_flag_raw = row["transition_flag_unlagged"]
        actual_flag = bool(actual_flag_raw)
        assert actual_flag == expected_flag
        actual_reason = row["transition_reason_unlagged"]
        if expected_reason is None:
            assert actual_reason is None or (
                isinstance(actual_reason, float) and np.isnan(actual_reason)
            )
        else:
            assert actual_reason == expected_reason
        assert row["regime_unlagged_raw"] in MACRO_PRIMARY_REGIME_NAMES


def test_legacy_neutral_transition_preserved_for_backward_compat() -> None:
    panel, meta = _build_panel_with_axis_path([0.02] * 24, [0.02] * 24)
    scores = compute_macro_scores(panel, meta, neutral_band=0.20, persistence_months=1)
    valid = scores.dropna(subset=["growth_score", "inflation_score"])
    # Legacy series should still flag low-magnitude months as neutral_transition.
    assert (valid["regime_legacy_unlagged_raw"] == "neutral_transition").any()
    # Primary series must NOT contain neutral_transition.
    assert "neutral_transition" not in set(valid["regime_unlagged_raw"].astype(str))


# ---------------------------------------------------------------------------
# Quality check transition_summary block
# ---------------------------------------------------------------------------


def _quality_frame(seq: list[tuple[str, bool, str | None]]) -> pd.DataFrame:
    idx = pd.date_range("2018-01-31", periods=len(seq), freq=MONTH_END_FREQ)
    return pd.DataFrame(
        {
            "regime": [s[0] for s in seq],
            "regime_legacy": [
                s[0] if not s[1] else "neutral_transition" for s in seq
            ],
            "transition_flag": [s[1] for s in seq],
            "transition_reason": [s[2] for s in seq],
            "growth_score": [0.5 if s[0] in {"goldilocks", "reflation"} else -0.5 for s in seq],
            "inflation_score": [0.5 if s[0] in {"reflation", "stagflation"} else -0.5 for s in seq],
        },
        index=idx,
    )


def test_quality_check_reports_transition_summary_and_skips_neutral_for_lt24_warning() -> None:
    sequence = [
        ("reflation", False, None),
        ("reflation", False, None),
        ("reflation", True, MACRO_TRANSITION_REASON_GROWTH),
        ("goldilocks", True, MACRO_TRANSITION_REASON_BOTH),
        ("goldilocks", False, None),
        ("recession_disinflation", True, MACRO_TRANSITION_REASON_INFLATION),
    ] * 6  # 36 rows
    frame = _quality_frame(sequence)
    out = build_regime_label_quality_check(
        labels_with_regime=frame,
        coverage_tier="full",
        optional_blocks_missing=set(),
        available_blocks={"growth_labor"},
        missing_blocks=set(),
        neutral_band=0.20,
    )
    assert out["status"] == "available"
    by_regime = out["by_regime"]

    # neutral_transition must remain as a key with zero observations and no
    # quality_status that would trigger an "<24 observations" warning.
    nt = by_regime.get("neutral_transition")
    assert nt is not None
    assert nt["n_obs"] == 0
    assert nt["quality_status"] == "no_observations"

    # Stability warning list must NOT include "major regimes ... neutral_transition".
    insufficient = out["stability_summary"]["major_regimes_insufficient"]
    assert "neutral_transition" not in insufficient

    ts = out["transition_summary"]
    assert ts["n_scored_months"] == len(sequence)
    assert ts["n_transition_months"] > 0
    assert math.isclose(
        ts["transition_share"],
        ts["n_transition_months"] / ts["n_scored_months"],
        rel_tol=1e-6,
    )
    counts = ts["transition_reason_counts"]
    assert sum(counts.values()) == ts["n_transition_months"]
    pivot = ts["primary_vs_transition_pivot"]
    for primary in MACRO_PRIMARY_REGIME_NAMES:
        assert primary in pivot
        assert "transition" in pivot[primary]
        assert "non_transition" in pivot[primary]
    # Legacy share must be reported when regime_legacy is present.
    assert ts["legacy_neutral_transition_share"] is not None
