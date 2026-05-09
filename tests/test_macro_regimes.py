"""Tests for the monthly two-axis macro regime classifier (`macro_two_axis_v1`)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import stress_factors as sf
from src import stress_factors_macro as sfm
from src.pandas_compat import MONTH_END_FREQ


# ---------------------------------------------------------------------------
# Synthetic-panel utilities (no network access).
# ---------------------------------------------------------------------------


def _monthly_index(n: int, *, start: str = "2010-01-31") -> pd.DatetimeIndex:
    return pd.date_range(start=start, periods=n, freq=MONTH_END_FREQ)


def _build_panel_with_labels(labels: list[str], *, n: int | None = None) -> tuple[pd.DataFrame, dict]:
    """Build a synthetic indicator panel that, after compute_macro_scores, yields
    composite scores matching the requested labels for the trailing rows.

    We bypass the indicator transforms entirely by constructing per-indicator
    *level* columns whose values are already z-scored block-style signals: the
    rolling z-score over the synthetic panel produces ``+1 / -1`` extremes.
    """

    n = n or (len(labels) + sfm.MACRO_SCORE_MIN_PERIODS + 5)
    idx = _monthly_index(n)
    panel: dict[str, pd.Series] = {}
    rng = np.random.default_rng(0)
    # baseline noise so that rolling std > 0 even for inactive indicators
    noise = pd.Series(rng.normal(scale=0.01, size=n), index=idx)

    last_k = len(labels)
    growth_target = np.zeros(n)
    inflation_target = np.zeros(n)
    growth_target[-last_k:] = [1.0 if l in {"goldilocks", "reflation"} else -1.0 if l in {"stagflation", "recession_disinflation"} else 0.0 for l in labels]
    inflation_target[-last_k:] = [1.0 if l in {"reflation", "stagflation"} else -1.0 if l in {"goldilocks", "recession_disinflation"} else 0.0 for l in labels]

    # Strong driver indicators (one per axis) so the bucketed signal saturates to +/-1.
    growth_series = pd.Series(growth_target, index=idx) * 5.0 + noise
    inflation_series = pd.Series(inflation_target, index=idx) * 5.0 + noise

    panel["payems__level"] = growth_series
    panel["payems__momentum"] = growth_series
    panel["unrate__level"] = -growth_series  # spec sign is "-"
    panel["unrate__momentum"] = -growth_series
    panel["core_cpi_3m_ann__level"] = inflation_series
    panel["core_cpi_3m_ann__momentum"] = inflation_series
    panel["core_pce_3m_ann__level"] = inflation_series
    panel["core_pce_3m_ann__momentum"] = inflation_series

    df = pd.DataFrame(panel)
    df.index = idx

    meta = {
        "data_sources_used": {
            "payems": "fred",
            "unrate": "fred",
            "core_cpi_3m_ann": "fred",
            "core_pce_3m_ann": "fred",
        },
        "frequency_native": {
            "payems": "M",
            "unrate": "M",
            "core_cpi_3m_ann": "M",
            "core_pce_3m_ann": "M",
        },
        "available_indicators": ["payems", "unrate", "core_cpi_3m_ann", "core_pce_3m_ann"],
        "unavailable_indicators": [
            "ism_manuf_pmi",
            "ism_services_pmi",
            "real_pce",
            "real_dpi",
            "hy_oas",
            "nfci",
            "gdpnow",
            "headline_cpi_3m_ann",
            "oil_3m_change",
            "ahe",
            "eci",
            "breakeven_5y",
            "breakeven_5y5y",
            "ism_manuf_prices_paid",
            "ism_services_prices_paid",
        ],
        "indicator_specs": {spec.key: sfm._spec_meta(spec) for spec in sfm.INDICATORS},
    }
    return df, meta


def _build_factor_and_portfolio_returns(
    n_months: int,
    *,
    factor_cols: list[str] | None = None,
    seed: int = 7,
) -> tuple[pd.Series, pd.DataFrame]:
    factor_cols = factor_cols or list(sf.BASE_FACTOR_COLUMN_ORDER)
    idx = _monthly_index(n_months)
    rng = np.random.default_rng(seed)
    factors = pd.DataFrame(
        rng.normal(scale=0.02, size=(n_months, len(factor_cols))),
        index=idx,
        columns=factor_cols,
    )
    beta_vec = np.array([0.4, -0.2, 0.1, 0.2, -0.05, 0.1, 0.0, 0.05][: len(factor_cols)])
    y = pd.Series(factors.values @ beta_vec + rng.normal(scale=0.01, size=n_months), index=idx)
    return y, factors


# ---------------------------------------------------------------------------
# Constants / labels
# ---------------------------------------------------------------------------


def test_method_version_is_macro_two_axis_v1() -> None:
    assert sf.MACRO_REGIME_METHOD_VERSION == "macro_two_axis_v1"
    assert sfm.MACRO_REGIME_METHOD_VERSION == "macro_two_axis_v1"


def test_macro_regime_names_include_neutral_transition() -> None:
    assert "neutral_transition" in sfm.MACRO_REGIME_NAMES
    assert sfm.MACRO_REGIME_NAMES == sf.MACRO_REGIME_NAMES


def test_macro_quality_status_monthly_thresholds() -> None:
    assert sfm.macro_quality_status(0) == "no_observations"
    assert sfm.macro_quality_status(11) == "insufficient_data"
    assert sfm.macro_quality_status(12) == "low_confidence"
    assert sfm.macro_quality_status(23) == "low_confidence"
    assert sfm.macro_quality_status(24) == "usable"
    assert sfm.macro_quality_status(59) == "usable"
    assert sfm.macro_quality_status(60) == "reliable"
    assert sf._macro_quality_status(11) == "insufficient_data"
    assert sf._macro_quality_status(60) == "reliable"


# ---------------------------------------------------------------------------
# compute_macro_scores: 5 labels, 1-month lag, neutral band
# ---------------------------------------------------------------------------


def test_compute_macro_scores_yields_all_five_labels() -> None:
    labels = [
        "goldilocks",
        "reflation",
        "stagflation",
        "recession_disinflation",
        "neutral_transition",
        "reflation",
    ]
    panel, meta = _build_panel_with_labels(labels, n=80)
    # Disable persistence smoothing so each instantaneous label survives for the
    # purpose of checking that all four quadrants can be reached.
    scores = sfm.compute_macro_scores(panel, meta, persistence_months=1)
    assert not scores.empty
    unlagged = scores["regime_unlagged_raw"].dropna().tolist()
    assert {"goldilocks", "reflation", "stagflation", "recession_disinflation"}.issubset(unlagged)


def test_compute_macro_scores_lag_shifts_labels_by_one_month() -> None:
    labels = ["goldilocks", "reflation", "stagflation"]
    panel, meta = _build_panel_with_labels(labels, n=80)
    scores = sfm.compute_macro_scores(panel, meta, persistence_months=1)
    paired = scores[["regime_unlagged", "regime"]].dropna()
    # The lagged regime at row t equals the unlagged regime at row t-1.
    for ts in paired.index[1:]:
        prev = paired.index[paired.index.get_loc(ts) - 1]
        assert scores.loc[ts, "regime"] == scores.loc[prev, "regime_unlagged"]


def test_label_quadrant_neutral_band_logic() -> None:
    """Within ±neutral_band on either axis -> neutral_transition; outside -> quadrant."""

    band = sfm.MACRO_REGIME_NEUTRAL_BAND_DEFAULT
    assert sfm._label_quadrant(0.0, 0.0, neutral_band=band) == "neutral_transition"
    assert sfm._label_quadrant(0.10, 1.0, neutral_band=band) == "neutral_transition"
    assert sfm._label_quadrant(1.0, 0.10, neutral_band=band) == "neutral_transition"
    # Goldilocks: growth > 0, inflation < 0, both above band.
    assert sfm._label_quadrant(0.50, -0.50, neutral_band=band) == "goldilocks"
    # Reflation: growth > 0, inflation >= 0, both above band.
    assert sfm._label_quadrant(0.50, 0.50, neutral_band=band) == "reflation"
    # Stagflation: growth < 0, inflation >= 0, both above band.
    assert sfm._label_quadrant(-0.50, 0.50, neutral_band=band) == "stagflation"
    # Recession / disinflation: growth < 0, inflation < 0, both above band.
    assert sfm._label_quadrant(-0.50, -0.50, neutral_band=band) == "recession_disinflation"
    # NaN guard.
    assert sfm._label_quadrant(float("nan"), 0.5, neutral_band=band) == "neutral_transition"


# ---------------------------------------------------------------------------
# Diagnostics from frames: gating + JSON contract
# ---------------------------------------------------------------------------


def test_from_frames_returns_full_contract() -> None:
    labels = (["reflation"] * 30) + (["goldilocks"] * 35) + (["stagflation"] * 30)
    panel, meta = _build_panel_with_labels(labels, n=160)
    y, factors = _build_factor_and_portfolio_returns(len(panel))
    payload = sfm.macro_two_axis_diagnostics_from_frames(
        y, factors, panel, meta, panel.index[-1].strftime("%Y-%m-%d")
    )

    assert payload["axis_model"]["version"] == "macro_two_axis_v1"
    assert payload["axis_model"]["frequency"] == "monthly"
    assert payload["score_lag_months"] == 1
    assert "look_ahead_caveat" in payload["axis_model"]
    assert payload["current_regime"] in sfm.MACRO_REGIME_NAMES
    assert "growth_blocks" in payload["axis_scores_latest"]
    assert "inflation_blocks" in payload["axis_scores_latest"]
    for key in (
        "available_blocks",
        "missing_blocks",
        "optional_blocks_missing",
        "planned_not_loaded",
        "coverage_ratio",
        "coverage_tier",
        "confidence_level",
        "data_sources_used",
        "score_start_date",
        "regime_label_start_date",
    ):
        assert key in payload, key


def test_below_minimum_observations_suppress_estimates() -> None:
    labels = (["reflation"] * 70) + (["goldilocks"] * 8)  # goldilocks gets <12 rows
    panel, meta = _build_panel_with_labels(labels, n=160)
    y, factors = _build_factor_and_portfolio_returns(len(panel))
    payload = sfm.macro_two_axis_diagnostics_from_frames(
        y, factors, panel, meta, panel.index[-1].strftime("%Y-%m-%d")
    )

    block = payload["regimes"]["goldilocks"]
    assert block["quality_status"] in {"insufficient_data", "no_observations"}
    if block["quality_status"] == "insufficient_data":
        reg = block["factor_regression"]
        assert reg.get("status") == "insufficient_data"
        assert "betas" not in reg or reg.get("estimate_used") is None
        assert block["factor_covariance"] is None
        assert block["portfolio_factor_risk"] is None
        assert block["portfolio_factor_rc"] == []


def test_low_confidence_regime_uses_linear_shrinkage() -> None:
    # ~16 rows in stagflation -> low_confidence; reflation gets reliable
    labels = (["reflation"] * 70) + (["stagflation"] * 16)
    panel, meta = _build_panel_with_labels(labels, n=160)
    y, factors = _build_factor_and_portfolio_returns(len(panel))
    payload = sfm.macro_two_axis_diagnostics_from_frames(
        y, factors, panel, meta, panel.index[-1].strftime("%Y-%m-%d")
    )
    stag = payload["regimes"]["stagflation"]
    assert stag["quality_status"] == "low_confidence"
    assert stag["used_fallback"] is True
    assert stag["fallback_method"] == "linear_shrinkage_to_base_10y"
    assert 0.0 <= float(stag["shrinkage_weight_regime"]) <= 1.0


def test_csv_frames_emit_monthly_filenames() -> None:
    labels = (["reflation"] * 35) + (["goldilocks"] * 35) + (["recession_disinflation"] * 30)
    panel, meta = _build_panel_with_labels(labels, n=160)
    y, factors = _build_factor_and_portfolio_returns(len(panel))
    payload = sfm.macro_two_axis_diagnostics_from_frames(
        y, factors, panel, meta, panel.index[-1].strftime("%Y-%m-%d")
    )
    frames = sfm.macro_regime_csv_frames(payload)
    assert "macro_regime_labels_monthly.csv" in frames
    assert "macro_regime_factor_betas.csv" in frames
    assert "macro_regime_factor_covariance.csv" in frames
    assert "macro_regime_factor_rc.csv" in frames


def test_back_compat_shim_routes_through_new_module() -> None:
    # The old import name `macro_regime_diagnostics_from_frames` on stress_factors
    # must dispatch to the new monthly path.
    labels = (["reflation"] * 40) + (["goldilocks"] * 40)
    panel, meta = _build_panel_with_labels(labels, n=160)
    y, factors = _build_factor_and_portfolio_returns(len(panel))
    via_shim = sf.macro_regime_diagnostics_from_frames(
        y, factors, panel, meta, panel.index[-1].strftime("%Y-%m-%d")
    )
    direct = sfm.macro_two_axis_diagnostics_from_frames(
        y, factors, panel, meta, panel.index[-1].strftime("%Y-%m-%d")
    )
    assert via_shim["axis_model"]["version"] == direct["axis_model"]["version"] == "macro_two_axis_v1"
