"""
Macro two-axis regime classifier (`macro_two_axis_v1`).

Implements the indicator catalog, transforms, scoring, regime classification, and
per-regime monthly factor analytics described in
`docs/exec_plans/2026-05-05_macro_two_axis_regime_v1.md` and
`docs/docs/stress_testing_spec.md` §8.8.2.

The block is **diagnostic-only**: it must not change optimizer weights, mandate
gates, stress pass/fail, or weight release.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Callable

import numpy as np
import pandas as pd

from src.data_macro_sources import (
    IndicatorSpec,
    SourceSpec,
    resolve_indicator,
)
from src.pandas_compat import MONTH_END_FREQ

_LOG = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants (single source of truth for the v1 method)
# ---------------------------------------------------------------------------

MACRO_REGIME_METHOD_VERSION = "macro_two_axis_v1"
MACRO_REGIME_METHOD_DISCLAIMER = (
    "macro_two_axis_v1 is a diagnostic-only macro regime classifier. It does not "
    "affect optimizer weights, mandate gates, stress pass/fail, or weight release."
)
MACRO_REGIME_LOOK_AHEAD_CAVEAT = (
    "Look-ahead protection is a 1-month publication lag only. Release-date "
    "accurate vintage handling is out of scope for v1."
)

# Score window: rolling 10-year monthly z-score
MACRO_SCORE_WINDOW_MONTHS = 120
MACRO_SCORE_MIN_PERIODS = 60
MACRO_INDICATOR_SIGNAL_BAND = 0.5

# Composite blend (momentum-weighted per spec)
MACRO_COMPOSITE_MOMENTUM_WEIGHT = 0.6
MACRO_COMPOSITE_LEVEL_WEIGHT = 0.4

# Neutral band on composite scores
MACRO_REGIME_NEUTRAL_BAND_DEFAULT = 0.25

# Look-ahead lag (months)
MACRO_REGIME_SCORE_LAG_MONTHS = 1

# Regime labels (4 quadrants + transition)
MACRO_REGIME_NAMES: tuple[str, ...] = (
    "goldilocks",
    "reflation",
    "stagflation",
    "recession_disinflation",
    "neutral_transition",
)

# Per-regime n_obs gating thresholds (monthly observations)
MACRO_REGIME_INSUFFICIENT_MAX_ROWS = 12   # n < 12 -> insufficient_data (estimates suppressed)
MACRO_REGIME_LOW_CONFIDENCE_MIN_ROWS = 12
MACRO_REGIME_USABLE_MIN_ROWS = 24
MACRO_REGIME_RELIABLE_MIN_ROWS = 60

# Stability summary parameters (reuse weekly defaults as a global heuristic)
MACRO_REGIME_STABILITY_BETA_GAP = 0.25
MACRO_REGIME_STABILITY_WARNING = (
    "Stability threshold is a global heuristic, not factor-specific calibration."
)


def macro_quality_status(n_obs: int) -> str:
    """Map a monthly observation count to a quality label.

    See ExecPlan: <12 -> insufficient_data (estimates suppressed),
    12..23 -> low_confidence, 24..59 -> usable, 60+ -> reliable.
    """

    n = int(n_obs or 0)
    if n <= 0:
        return "no_observations"
    if n < MACRO_REGIME_INSUFFICIENT_MAX_ROWS:
        return "insufficient_data"
    if n < MACRO_REGIME_USABLE_MIN_ROWS:
        return "low_confidence"
    if n < MACRO_REGIME_RELIABLE_MIN_ROWS:
        return "usable"
    return "reliable"


# ---------------------------------------------------------------------------
# Indicator registry
# ---------------------------------------------------------------------------

# Convenience constructors for the most common source chain shapes.

def _fred_chain(series_id: str, *, also_manual_csv: bool = True, manual_locator: str = "") -> tuple[SourceSpec, ...]:
    chain: list[SourceSpec] = [SourceSpec(kind="fred", locator=series_id)]
    if also_manual_csv:
        chain.append(SourceSpec(kind="manual_csv", locator=manual_locator))
    return tuple(chain)


def _ism_chain(legacy_fred_id: str, vendor: str = "tradingeconomics") -> tuple[SourceSpec, ...]:
    return (
        SourceSpec(kind="fred", locator=legacy_fred_id),
        SourceSpec(kind="keyed_api", locator=vendor, requires_env=("ISM_API_KEY",)),
        SourceSpec(kind="manual_csv", locator=""),
    )


GROWTH_BLOCK_BUSINESS_ACTIVITY = "growth_business_activity"
GROWTH_BLOCK_LABOR = "growth_labor"
GROWTH_BLOCK_CONSUMER = "growth_consumer"
GROWTH_BLOCK_CREDIT = "growth_credit"
GROWTH_BLOCK_NOWCAST = "growth_nowcast"

INFLATION_BLOCK_CORE = "core_inflation"
INFLATION_BLOCK_HEADLINE = "headline_inflation"
INFLATION_BLOCK_WAGES = "wages"
INFLATION_BLOCK_EXPECTATIONS = "inflation_expectations"
INFLATION_BLOCK_PRICE_PRESSURE = "business_price_pressure"

GROWTH_BLOCKS: tuple[str, ...] = (
    GROWTH_BLOCK_BUSINESS_ACTIVITY,
    GROWTH_BLOCK_LABOR,
    GROWTH_BLOCK_CONSUMER,
    GROWTH_BLOCK_CREDIT,
    GROWTH_BLOCK_NOWCAST,
)
INFLATION_BLOCKS: tuple[str, ...] = (
    INFLATION_BLOCK_CORE,
    INFLATION_BLOCK_HEADLINE,
    INFLATION_BLOCK_WAGES,
    INFLATION_BLOCK_EXPECTATIONS,
    INFLATION_BLOCK_PRICE_PRESSURE,
)

OPTIONAL_BLOCKS: frozenset[str] = frozenset({GROWTH_BLOCK_NOWCAST})


INDICATORS: tuple[IndicatorSpec, ...] = (
    # ----- Growth: business activity -----
    IndicatorSpec(
        key="ism_manuf_pmi",
        block=GROWTH_BLOCK_BUSINESS_ACTIVITY,
        axis="growth",
        role="optional",
        sign="+",
        frequency="M",
        transform="level_and_three_m_change",
        source_chain=_ism_chain("NAPM"),
        description="ISM Manufacturing PMI (level + 3m change)",
    ),
    IndicatorSpec(
        key="ism_services_pmi",
        block=GROWTH_BLOCK_BUSINESS_ACTIVITY,
        axis="growth",
        role="optional",
        sign="+",
        frequency="M",
        transform="level_and_three_m_change",
        source_chain=_ism_chain("NMFBAI"),
        description="ISM Services PMI (level + 3m change)",
    ),
    # ----- Growth: labor -----
    IndicatorSpec(
        key="payems",
        block=GROWTH_BLOCK_LABOR,
        axis="growth",
        role="required",
        sign="+",
        frequency="M",
        transform="three_m_avg_mom",
        source_chain=_fred_chain("PAYEMS"),
        description="Nonfarm payrolls — 3m average M/M change",
    ),
    IndicatorSpec(
        key="unrate",
        block=GROWTH_BLOCK_LABOR,
        axis="growth",
        role="required",
        sign="-",
        frequency="M",
        transform="three_m_change",
        source_chain=_fred_chain("UNRATE"),
        description="Unemployment rate — 3m change (sign inverted)",
    ),
    # ----- Growth: consumer -----
    IndicatorSpec(
        key="real_pce",
        block=GROWTH_BLOCK_CONSUMER,
        axis="growth",
        role="required",
        sign="+",
        frequency="M",
        transform="three_m_yoy",
        source_chain=_fred_chain("PCEC96"),
        description="Real Personal Consumption Expenditures — 3m yoy",
    ),
    IndicatorSpec(
        key="real_dpi",
        block=GROWTH_BLOCK_CONSUMER,
        axis="growth",
        role="required",
        sign="+",
        frequency="M",
        transform="three_m_yoy",
        source_chain=_fred_chain("DSPIC96"),
        description="Real Disposable Personal Income — 3m yoy",
    ),
    # ----- Growth: credit -----
    IndicatorSpec(
        key="hy_oas",
        block=GROWTH_BLOCK_CREDIT,
        axis="growth",
        role="required",
        sign="-",
        frequency="M",
        transform="level_and_three_m_change",
        source_chain=_fred_chain("BAMLH0A0HYM2"),
        description="HY OAS spread — level + 3m change (sign inverted)",
    ),
    IndicatorSpec(
        key="nfci",
        block=GROWTH_BLOCK_CREDIT,
        axis="growth",
        role="required",
        sign="-",
        frequency="M",
        transform="level_and_three_m_change",
        source_chain=_fred_chain("NFCI"),
        description="Chicago Fed NFCI — level + 3m change (sign inverted)",
    ),
    # ----- Growth: nowcast (optional, confirmation_layer) -----
    IndicatorSpec(
        key="gdpnow",
        block=GROWTH_BLOCK_NOWCAST,
        axis="growth",
        role="optional",
        sign="+",
        frequency="Q",
        transform="quarterly_ffill_monthly_three_m_change",
        source_chain=(
            # Primary: FRED hosts the Atlanta Fed GDPNow nowcast as a quarterly
            # series (Percent Change at Annual Rate, SAAR) — see
            # https://fred.stlouisfed.org/series/GDPNOW. We forward-fill to
            # monthly so it can be aligned with the rest of the panel; the
            # commentary explicitly marks the monthly precision as illustrative.
            SourceSpec(kind="fred", locator="GDPNOW"),
            # Fallback: Atlanta Fed direct CSV (RealGDPTrackingSlides.csv).
            SourceSpec(
                kind="official_csv",
                locator="https://www.atlantafed.org/-/media/documents/cqer/researchcq/gdpnow/RealGDPTrackingSlides.csv",
            ),
            # Reference / human-facing landing page: Atlanta Fed GDPNow
            # https://www.atlantafed.org/research-and-data/data/gdpnow
            # (HTML, not a CSV; recorded so it appears in `sources_attempted`
            # for traceability when the FRED and direct-CSV sources fail).
            SourceSpec(
                kind="official_csv",
                locator="https://www.atlantafed.org/research-and-data/data/gdpnow",
            ),
            SourceSpec(kind="manual_csv", locator=""),
        ),
        description=(
            "Atlanta Fed GDPNow nowcast via FRED:GDPNOW (quarterly, ffilled "
            "to monthly; level + 3m change). Reference page: "
            "https://www.atlantafed.org/research-and-data/data/gdpnow"
        ),
    ),
    # NOTE: NY Fed Nowcast was retired from the active classifier on
    # 2026-05-07. The series was discontinued by the NY Fed in 2021 and only
    # provided historical values; GDPNow (via FRED:GDPNOW) is now the sole
    # nowcast indicator in the `growth_nowcast` block. The historical NY Fed
    # CSV remains documented as a deprecated reference in
    # `docs/exec_plans/2026-05-05_macro_two_axis_regime_v1.md` and
    # `docs/docs/stress_testing_spec.md` §8.8.2.
    # ----- Inflation: core -----
    IndicatorSpec(
        key="core_cpi_3m_ann",
        block=INFLATION_BLOCK_CORE,
        axis="inflation",
        role="required",
        sign="+",
        frequency="M",
        transform="three_m_annualized",
        source_chain=_fred_chain("CPILFESL"),
        description="Core CPI — 3m annualised",
    ),
    IndicatorSpec(
        key="core_pce_3m_ann",
        block=INFLATION_BLOCK_CORE,
        axis="inflation",
        role="required",
        sign="+",
        frequency="M",
        transform="three_m_annualized",
        source_chain=_fred_chain("PCEPILFE"),
        description="Core PCE — 3m annualised",
    ),
    # ----- Inflation: headline + energy -----
    IndicatorSpec(
        key="headline_cpi_3m_ann",
        block=INFLATION_BLOCK_HEADLINE,
        axis="inflation",
        role="required",
        sign="+",
        frequency="M",
        transform="three_m_annualized",
        source_chain=_fred_chain("CPIAUCSL"),
        description="Headline CPI — 3m annualised",
    ),
    IndicatorSpec(
        key="oil_3m_change",
        block=INFLATION_BLOCK_HEADLINE,
        axis="inflation",
        role="required",
        sign="+",
        frequency="M",
        transform="oil_monthly_avg_three_m_change",
        source_chain=(
            SourceSpec(kind="fred", locator="DCOILWTICO"),
            SourceSpec(kind="yahoo", locator="CL=F"),
            SourceSpec(kind="manual_csv", locator=""),
        ),
        description="WTI oil price — monthly average then 3m change",
    ),
    # ----- Inflation: wages -----
    IndicatorSpec(
        key="ahe",
        block=INFLATION_BLOCK_WAGES,
        axis="inflation",
        role="required",
        sign="+",
        frequency="M",
        transform="three_m_yoy",
        source_chain=_fred_chain("CES0500000003"),
        description="Average Hourly Earnings — 3m yoy",
    ),
    IndicatorSpec(
        key="eci",
        block=INFLATION_BLOCK_WAGES,
        axis="inflation",
        role="required",
        sign="+",
        frequency="Q",
        transform="quarterly_ffill_monthly_yoy",
        source_chain=_fred_chain("ECIWAG"),
        description="Employment Cost Index, wages (quarterly ffilled to monthly, yoy)",
    ),
    # ----- Inflation: expectations -----
    IndicatorSpec(
        key="breakeven_5y",
        block=INFLATION_BLOCK_EXPECTATIONS,
        axis="inflation",
        role="required",
        sign="+",
        frequency="M",
        transform="level_and_three_m_change",
        source_chain=_fred_chain("T5YIE"),
        description="5-year breakeven inflation (level + 3m change)",
    ),
    IndicatorSpec(
        key="breakeven_5y5y",
        block=INFLATION_BLOCK_EXPECTATIONS,
        axis="inflation",
        role="required",
        sign="+",
        frequency="M",
        transform="level_and_three_m_change",
        source_chain=_fred_chain("T5YIFR"),
        description="5y5y forward breakeven inflation (level + 3m change)",
    ),
    # ----- Inflation: business price pressure -----
    IndicatorSpec(
        key="ism_manuf_prices_paid",
        block=INFLATION_BLOCK_PRICE_PRESSURE,
        axis="inflation",
        role="optional",
        sign="+",
        frequency="M",
        transform="level_and_three_m_change",
        source_chain=_ism_chain("NAPMPRI"),
        description="ISM Manufacturing Prices Paid (level + 3m change)",
    ),
    IndicatorSpec(
        key="ism_services_prices_paid",
        block=INFLATION_BLOCK_PRICE_PRESSURE,
        axis="inflation",
        role="optional",
        sign="+",
        frequency="M",
        transform="level_and_three_m_change",
        source_chain=_ism_chain("NMFCI"),
        description="ISM Services Prices Paid (level + 3m change)",
    ),
)


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------


def _to_month_end(s: pd.Series) -> pd.Series:
    if s is None or s.empty:
        return pd.Series(dtype=float)
    out = s.dropna().astype(float)
    out.index = pd.to_datetime(out.index).tz_localize(None)
    return out.resample(MONTH_END_FREQ).last().dropna()


def _to_month_avg(s: pd.Series) -> pd.Series:
    if s is None or s.empty:
        return pd.Series(dtype=float)
    out = s.dropna().astype(float)
    out.index = pd.to_datetime(out.index).tz_localize(None)
    return out.resample(MONTH_END_FREQ).mean().dropna()


def _three_m_avg_mom(monthly: pd.Series) -> pd.Series:
    diff = monthly.diff()
    return diff.rolling(window=3, min_periods=2).mean()


def _three_m_change(monthly: pd.Series) -> pd.Series:
    return monthly.diff(3)


def _three_m_yoy(monthly: pd.Series) -> pd.Series:
    yoy = monthly / monthly.shift(12) - 1.0
    return yoy.rolling(window=3, min_periods=1).mean()


def _three_m_annualized(monthly: pd.Series) -> pd.Series:
    ratio = monthly / monthly.shift(3)
    with np.errstate(invalid="ignore"):
        return ratio.pow(4.0) - 1.0


def _quarterly_ffill_monthly_yoy(quarterly: pd.Series) -> pd.Series:
    s = _to_month_end(quarterly).reindex(
        pd.date_range(quarterly.index.min(), quarterly.index.max(), freq=MONTH_END_FREQ)
        if not quarterly.empty
        else pd.DatetimeIndex([]),
        method="ffill",
    )
    s = s.ffill().dropna()
    return s / s.shift(12) - 1.0


# Transform => returns dict {"level": Series, "momentum": Series}
TransformFn = Callable[[pd.Series], dict[str, pd.Series]]


def _t_level_and_three_m_change(raw: pd.Series) -> dict[str, pd.Series]:
    monthly = _to_month_end(raw)
    return {"level": monthly, "momentum": _three_m_change(monthly)}


def _t_three_m_avg_mom(raw: pd.Series) -> dict[str, pd.Series]:
    monthly = _to_month_end(raw)
    return {"level": monthly, "momentum": _three_m_avg_mom(monthly)}


def _t_three_m_change(raw: pd.Series) -> dict[str, pd.Series]:
    monthly = _to_month_end(raw)
    return {"level": monthly, "momentum": _three_m_change(monthly)}


def _t_three_m_yoy(raw: pd.Series) -> dict[str, pd.Series]:
    monthly = _to_month_end(raw)
    return {"level": monthly, "momentum": _three_m_yoy(monthly)}


def _t_three_m_annualized(raw: pd.Series) -> dict[str, pd.Series]:
    monthly = _to_month_end(raw)
    return {"level": monthly, "momentum": _three_m_annualized(monthly)}


def _t_oil_monthly_avg_three_m_change(raw: pd.Series) -> dict[str, pd.Series]:
    monthly_avg = _to_month_avg(raw)
    return {"level": monthly_avg, "momentum": monthly_avg.diff(3)}


def _quarterly_ffill_to_monthly(raw: pd.Series) -> pd.Series:
    """Resample a quarterly series to month-end with forward-fill.

    Used for series published quarterly (ECI) or whose published cadence is
    quarterly with intra-quarter revisions (Atlanta Fed GDPNow on FRED). The
    forward-filled monthly series carries no extra information between official
    releases — caller-side commentary must label this as illustrative monthly
    precision.
    """

    if raw is None or raw.empty:
        return pd.Series(dtype=float)
    s = raw.dropna().astype(float)
    s.index = pd.to_datetime(s.index).tz_localize(None)
    if s.empty:
        return pd.Series(dtype=float)
    monthly_index = pd.date_range(
        s.index.min().to_period("M").to_timestamp("M"),
        s.index.max().to_period("M").to_timestamp("M"),
        freq=MONTH_END_FREQ,
    )
    return s.resample(MONTH_END_FREQ).last().reindex(monthly_index).ffill()


def _t_quarterly_ffill_monthly_yoy(raw: pd.Series) -> dict[str, pd.Series]:
    monthly = _quarterly_ffill_to_monthly(raw)
    if monthly.empty:
        return {"level": pd.Series(dtype=float), "momentum": pd.Series(dtype=float)}
    momentum = monthly / monthly.shift(12) - 1.0
    return {"level": monthly, "momentum": momentum}


def _t_quarterly_ffill_monthly_three_m_change(raw: pd.Series) -> dict[str, pd.Series]:
    """Quarterly source -> monthly ffill -> level + 3m change.

    Suitable for series whose value is already a level / annualised growth rate
    (e.g. GDPNow nowcast: quarterly forecast of annualised real GDP growth).
    Taking YoY of an already-annualised number would double-count, so we use
    a 3-month change of the level instead.
    """

    monthly = _quarterly_ffill_to_monthly(raw)
    if monthly.empty:
        return {"level": pd.Series(dtype=float), "momentum": pd.Series(dtype=float)}
    return {"level": monthly, "momentum": monthly.diff(3)}


_TRANSFORMS: dict[str, TransformFn] = {
    "level_and_three_m_change": _t_level_and_three_m_change,
    "three_m_avg_mom": _t_three_m_avg_mom,
    "three_m_change": _t_three_m_change,
    "three_m_yoy": _t_three_m_yoy,
    "three_m_annualized": _t_three_m_annualized,
    "oil_monthly_avg_three_m_change": _t_oil_monthly_avg_three_m_change,
    "quarterly_ffill_monthly_yoy": _t_quarterly_ffill_monthly_yoy,
    "quarterly_ffill_monthly_three_m_change": _t_quarterly_ffill_monthly_three_m_change,
}


def apply_transform(name: str, raw: pd.Series) -> dict[str, pd.Series]:
    """Public alias for unit tests."""

    fn = _TRANSFORMS.get(name)
    if fn is None:
        raise KeyError(f"Unknown transform: {name}")
    return fn(raw)


# ---------------------------------------------------------------------------
# Indicator panel construction
# ---------------------------------------------------------------------------


def fetch_macro_indicators(
    start: str,
    end: str,
    *,
    indicators: tuple[IndicatorSpec, ...] | None = None,
    resolver: Callable[..., tuple[pd.Series, dict[str, Any]]] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build the monthly indicator panel and metadata.

    Returns a tuple ``(panel, meta)``.

    ``panel`` is a monthly DataFrame indexed by month-end dates (``MONTH_END_FREQ``).
    For every successfully resolved indicator we add two columns:
    ``<key>__level`` and ``<key>__momentum``.

    ``meta`` includes ``data_sources_used`` (per indicator), ``frequency_native``,
    ``historical_only``, ``available_indicators`` and ``unavailable_indicators``,
    plus reference data needed by ``compute_macro_scores`` to derive coverage
    metadata.
    """

    indicators = indicators or INDICATORS
    resolver = resolver or resolve_indicator

    panel_columns: dict[str, pd.Series] = {}
    data_sources_used: dict[str, str] = {}
    frequency_native: dict[str, str] = {}
    historical_only_map: dict[str, bool] = {}
    available_indicators: list[str] = []
    unavailable_indicators: list[str] = []
    transform_used: dict[str, str] = {}

    for spec in indicators:
        try:
            raw, src_meta = resolver(spec, start, end)
        except Exception as exc:  # defensive
            _LOG.debug("resolve_indicator(%s) raised: %s", spec.key, exc)
            raw = pd.Series(dtype=float)
            src_meta = {"available": False, "source_used": "error", "error": str(exc)}

        data_sources_used[spec.key] = str(src_meta.get("source_used") or "unavailable")
        frequency_native[spec.key] = str(src_meta.get("frequency_native") or spec.frequency)
        historical_only_map[spec.key] = bool(src_meta.get("historical_only", spec.historical_only))
        transform_used[spec.key] = spec.transform

        if not src_meta.get("available", False) or raw is None or raw.empty:
            unavailable_indicators.append(spec.key)
            continue

        try:
            transformed = apply_transform(spec.transform, raw)
        except Exception as exc:
            _LOG.debug("transform %s on %s failed: %s", spec.transform, spec.key, exc)
            unavailable_indicators.append(spec.key)
            continue

        level = transformed.get("level")
        momentum = transformed.get("momentum")
        if level is None or momentum is None or level.dropna().empty:
            unavailable_indicators.append(spec.key)
            continue

        panel_columns[f"{spec.key}__level"] = level
        panel_columns[f"{spec.key}__momentum"] = momentum
        available_indicators.append(spec.key)

    if panel_columns:
        panel = pd.concat(panel_columns, axis=1).sort_index()
        panel.index = pd.to_datetime(panel.index).tz_localize(None)
    else:
        panel = pd.DataFrame()

    meta: dict[str, Any] = {
        "data_sources_used": data_sources_used,
        "frequency_native": frequency_native,
        "historical_only": historical_only_map,
        "transform_used": transform_used,
        "available_indicators": sorted(available_indicators),
        "unavailable_indicators": sorted(unavailable_indicators),
        "indicator_specs": {spec.key: _spec_meta(spec) for spec in indicators},
    }
    return panel, meta


def _spec_meta(spec: IndicatorSpec) -> dict[str, Any]:
    return {
        "block": spec.block,
        "axis": spec.axis,
        "role": spec.role,
        "sign": spec.sign,
        "frequency": spec.frequency,
        "transform": spec.transform,
        "historical_only": spec.historical_only,
        "description": spec.description,
    }


# ---------------------------------------------------------------------------
# Scoring and regime classification
# ---------------------------------------------------------------------------


def _rolling_zscore(series: pd.Series, *, window: int, min_periods: int) -> pd.Series:
    s = pd.Series(series, dtype=float)
    mean = s.rolling(window=window, min_periods=min_periods).mean()
    std = s.rolling(window=window, min_periods=min_periods).std(ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (s - mean) / std
    return z.replace([np.inf, -np.inf], np.nan)


def _bucket_signal(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    if z > MACRO_INDICATOR_SIGNAL_BAND:
        return 1.0
    if z < -MACRO_INDICATOR_SIGNAL_BAND:
        return -1.0
    return 0.0


def _bucket_signals(series: pd.Series) -> pd.Series:
    return series.map(_bucket_signal).astype(float)


def _label_quadrant(growth: float, infl: float, *, neutral_band: float) -> str:
    if not np.isfinite(growth) or not np.isfinite(infl):
        return "neutral_transition"
    if abs(growth) <= neutral_band or abs(infl) <= neutral_band:
        return "neutral_transition"
    if growth > 0 and infl < 0:
        return "goldilocks"
    if growth > 0 and infl >= 0:
        return "reflation"
    if growth < 0 and infl >= 0:
        return "stagflation"
    return "recession_disinflation"


def compute_macro_scores(
    panel: pd.DataFrame,
    meta: dict[str, Any],
    *,
    neutral_band: float = MACRO_REGIME_NEUTRAL_BAND_DEFAULT,
    indicators: tuple[IndicatorSpec, ...] | None = None,
) -> pd.DataFrame:
    """Return a monthly DataFrame with growth/inflation block sub-scores, composite
    scores, the lagged regime label, and per-row coverage metadata.

    The frame index is at MONTH_END_FREQ. Columns include:
    - growth_block_<block>_level / _momentum
    - inflation_block_<block>_level / _momentum
    - growth_level / growth_momentum / growth_score
    - inflation_level / inflation_momentum / inflation_score
    - regime (after 1-month lag)
    - regime_unlagged (regime at the row's own date, useful for diagnostics)
    """

    indicators = indicators or INDICATORS
    spec_by_key = {spec.key: spec for spec in indicators}

    if panel is None or panel.empty:
        return pd.DataFrame()

    panel = panel.sort_index()
    panel.index = pd.to_datetime(panel.index).tz_localize(None)

    z_level: dict[str, pd.Series] = {}
    z_mom: dict[str, pd.Series] = {}
    for key, spec in spec_by_key.items():
        col_level = f"{key}__level"
        col_mom = f"{key}__momentum"
        if col_level in panel.columns:
            z_level[key] = _rolling_zscore(
                panel[col_level],
                window=MACRO_SCORE_WINDOW_MONTHS,
                min_periods=MACRO_SCORE_MIN_PERIODS,
            )
        if col_mom in panel.columns:
            z_mom[key] = _rolling_zscore(
                panel[col_mom],
                window=MACRO_SCORE_WINDOW_MONTHS,
                min_periods=MACRO_SCORE_MIN_PERIODS,
            )

    sig_level = {k: _bucket_signals(z) for k, z in z_level.items()}
    sig_mom = {k: _bucket_signals(z) for k, z in z_mom.items()}

    def _block_signal(block_keys: list[str], sig_map: dict[str, pd.Series]) -> pd.Series:
        if not block_keys:
            return pd.Series(np.nan, index=panel.index)
        signed_series: list[pd.Series] = []
        for k in block_keys:
            if k not in sig_map:
                continue
            sgn = 1.0 if spec_by_key[k].sign == "+" else -1.0
            signed_series.append(sig_map[k] * sgn)
        if not signed_series:
            return pd.Series(np.nan, index=panel.index)
        df = pd.concat(signed_series, axis=1)
        return df.mean(axis=1, skipna=True)

    growth_keys_by_block = {
        block: [s.key for s in indicators if s.axis == "growth" and s.block == block]
        for block in GROWTH_BLOCKS
    }
    inflation_keys_by_block = {
        block: [s.key for s in indicators if s.axis == "inflation" and s.block == block]
        for block in INFLATION_BLOCKS
    }

    out = pd.DataFrame(index=panel.index)
    growth_block_levels: list[pd.Series] = []
    growth_block_moms: list[pd.Series] = []
    inflation_block_levels: list[pd.Series] = []
    inflation_block_moms: list[pd.Series] = []

    for block in GROWTH_BLOCKS:
        keys = growth_keys_by_block.get(block, [])
        lvl = _block_signal(keys, sig_level)
        mom = _block_signal(keys, sig_mom)
        out[f"growth_block_{block}_level"] = lvl
        out[f"growth_block_{block}_momentum"] = mom
        growth_block_levels.append(lvl)
        growth_block_moms.append(mom)

    for block in INFLATION_BLOCKS:
        keys = inflation_keys_by_block.get(block, [])
        lvl = _block_signal(keys, sig_level)
        mom = _block_signal(keys, sig_mom)
        out[f"inflation_block_{block}_level"] = lvl
        out[f"inflation_block_{block}_momentum"] = mom
        inflation_block_levels.append(lvl)
        inflation_block_moms.append(mom)

    out["growth_level"] = pd.concat(growth_block_levels, axis=1).mean(axis=1, skipna=True)
    out["growth_momentum"] = pd.concat(growth_block_moms, axis=1).mean(axis=1, skipna=True)
    out["inflation_level"] = pd.concat(inflation_block_levels, axis=1).mean(axis=1, skipna=True)
    out["inflation_momentum"] = pd.concat(inflation_block_moms, axis=1).mean(axis=1, skipna=True)
    out["growth_score"] = (
        MACRO_COMPOSITE_MOMENTUM_WEIGHT * out["growth_momentum"]
        + MACRO_COMPOSITE_LEVEL_WEIGHT * out["growth_level"]
    )
    out["inflation_score"] = (
        MACRO_COMPOSITE_MOMENTUM_WEIGHT * out["inflation_momentum"]
        + MACRO_COMPOSITE_LEVEL_WEIGHT * out["inflation_level"]
    )

    # Per-row regime at the same date (for diagnostics).
    out["regime_unlagged"] = [
        _label_quadrant(g, p, neutral_band=neutral_band)
        for g, p in zip(out["growth_score"].values, out["inflation_score"].values)
    ]
    # 1-month lag — apply to the labels: row at date t carries the regime computed
    # from data ending at date (t - 1 month). We shift the labels by 1 row of the
    # monthly index so they are valid for "the month after the data".
    out["regime"] = out["regime_unlagged"].shift(MACRO_REGIME_SCORE_LAG_MONTHS)

    return out


# ---------------------------------------------------------------------------
# Coverage metadata
# ---------------------------------------------------------------------------


def _resolved_blocks(meta: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    """Return (available_blocks, missing_blocks, optional_blocks_missing)."""

    specs = meta.get("indicator_specs", {})
    available_indicators = set(meta.get("available_indicators") or [])
    blocks_to_indicators: dict[str, list[str]] = {}
    for key, sm in specs.items():
        block = sm.get("block")
        if not block:
            continue
        blocks_to_indicators.setdefault(block, []).append(key)

    available_blocks: set[str] = set()
    missing_blocks: set[str] = set()
    for block, keys in blocks_to_indicators.items():
        if any(k in available_indicators for k in keys):
            available_blocks.add(block)
        else:
            missing_blocks.add(block)

    optional_missing = {b for b in missing_blocks if b in OPTIONAL_BLOCKS}
    return available_blocks, missing_blocks, optional_missing


def _coverage_tier(
    available_blocks: set[str],
    missing_blocks: set[str],
    data_sources_used: dict[str, str],
    indicator_specs: dict[str, dict[str, Any]],
) -> tuple[str, float]:
    total_blocks = len(GROWTH_BLOCKS) + len(INFLATION_BLOCKS)
    n_available = len(available_blocks)
    coverage_ratio = float(n_available) / float(total_blocks) if total_blocks else 0.0

    required_blocks = {
        spec["block"]
        for spec in indicator_specs.values()
        if spec.get("role") == "required"
    }
    required_resolved = required_blocks.issubset(available_blocks)

    used_kinds = {kind for kind in data_sources_used.values() if kind not in {"unavailable", "error"}}

    if n_available < 5:
        tier = "insufficient"
    elif used_kinds and used_kinds.issubset({"fred"}):
        tier = "fred_baseline"
    elif n_available == total_blocks:
        tier = "full"
    elif n_available >= total_blocks - 2 and required_resolved:
        tier = "extended"
    else:
        tier = "reduced"

    return tier, coverage_ratio


def _confidence_level(
    *,
    growth_score: float,
    inflation_score: float,
    coverage_tier: str,
    neutral_band: float,
    optional_blocks_missing: set[str],
) -> str:
    near_boundary = (
        not np.isfinite(growth_score)
        or not np.isfinite(inflation_score)
        or abs(growth_score) <= neutral_band
        or abs(inflation_score) <= neutral_band
    )
    if near_boundary:
        return "low"
    if coverage_tier in {"full", "extended"}:
        return "high"
    if coverage_tier == "reduced":
        return "medium"
    if coverage_tier == "fred_baseline":
        # Optional blocks missing alone (e.g. growth_nowcast) does not pull below medium.
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Per-regime monthly factor analytics
# ---------------------------------------------------------------------------


def _macro_helpers():
    """Lazy import to avoid circular import with stress_factors at module load."""

    from src import stress_factors as sf

    return {
        "BASE_FACTOR_COLUMN_ORDER": sf.BASE_FACTOR_COLUMN_ORDER,
        "FACTOR_TO_BETA_KEY": sf.FACTOR_TO_BETA_KEY,
        "_macro_regression_from_arrays": sf._macro_regression_from_arrays,
        "_macro_covariance_block": sf._macro_covariance_block,
        "_macro_covariance_matrix": sf._macro_covariance_matrix,
        "_macro_factor_risk": sf._macro_factor_risk,
        "_macro_factor_rc": sf._macro_factor_rc,
        "_macro_policy_signal": sf._macro_policy_signal,
        "_macro_empty_regression": sf._macro_empty_regression,
        "_macro_beta_keys": sf._macro_beta_keys,
        "_macro_order": sf._macro_order,
    }


def _per_regime_block(
    *,
    regime: str,
    regime_dates: pd.DatetimeIndex,
    y_monthly: pd.Series,
    x_monthly: pd.DataFrame,
    factor_cols: list[str],
    base_betas: dict[str, float],
    base_cov: pd.DataFrame,
    helpers: dict[str, Any],
) -> dict[str, Any]:
    n_obs = int(len(regime_dates))
    quality = macro_quality_status(n_obs)

    if n_obs < MACRO_REGIME_INSUFFICIENT_MAX_ROWS:
        return {
            "label": regime,
            "n_obs": n_obs,
            "quality_status": quality,
            "historical_estimate_available": False,
            "used_fallback": True,
            "fallback_method": "no_estimates_below_minimum",
            "fallback_target": "base_10y",
            "factor_regression": {
                "status": quality,
                "label": regime,
                "n_obs": n_obs,
                "reason": "n_obs below minimum threshold of 12 monthly observations",
            },
            "factor_covariance": None,
            "portfolio_factor_risk": None,
            "portfolio_factor_rc": [],
        }

    y_r = y_monthly.reindex(regime_dates).astype(float)
    x_r = x_monthly.reindex(regime_dates).loc[:, factor_cols].astype(float)
    valid = ~(y_r.isna() | x_r.isna().any(axis=1))
    y_v = y_r.loc[valid]
    x_v = x_r.loc[valid]
    if len(y_v) < MACRO_REGIME_INSUFFICIENT_MAX_ROWS:
        return {
            "label": regime,
            "n_obs": int(len(y_v)),
            "quality_status": macro_quality_status(int(len(y_v))),
            "historical_estimate_available": False,
            "used_fallback": True,
            "fallback_method": "no_estimates_below_minimum",
            "fallback_target": "base_10y",
            "factor_regression": {
                "status": "insufficient_data",
                "label": regime,
                "n_obs": int(len(y_v)),
                "reason": "fewer than 12 valid monthly rows after NaN filtering",
            },
            "factor_covariance": None,
            "portfolio_factor_risk": None,
            "portfolio_factor_rc": [],
        }

    raw_reg = helpers["_macro_regression_from_arrays"](
        y_v.values.astype(float),
        x_v.values.astype(float),
        factor_cols,
        label=regime,
        n_obs=int(len(y_v)),
    )
    raw_cov = helpers["_macro_covariance_matrix"](x_v)
    raw_betas = {k: float(v) for k, v in (raw_reg.get("betas") or {}).items()}
    for beta_key in helpers["_macro_beta_keys"]():
        raw_betas.setdefault(beta_key, 0.0)

    used_fallback = False
    fallback_method: str | None = None
    shrinkage_weight: float | None = None
    if int(len(y_v)) < MACRO_REGIME_USABLE_MIN_ROWS:
        # 12..23 monthly observations -> linear shrinkage to base_10y
        used_fallback = True
        fallback_method = "linear_shrinkage_to_base_10y"
        shrinkage_weight = float(
            np.clip(
                (int(len(y_v)) - MACRO_REGIME_LOW_CONFIDENCE_MIN_ROWS)
                / (MACRO_REGIME_USABLE_MIN_ROWS - MACRO_REGIME_LOW_CONFIDENCE_MIN_ROWS),
                0.0,
                1.0,
            )
        )
        used_betas = {
            beta_key: shrinkage_weight * raw_betas.get(beta_key, 0.0)
            + (1.0 - shrinkage_weight) * base_betas.get(beta_key, 0.0)
            for beta_key in helpers["_macro_beta_keys"]()
        }
        used_cov = raw_cov * shrinkage_weight + base_cov * (1.0 - shrinkage_weight)
    else:
        used_betas = raw_betas
        used_cov = raw_cov

    factor_regression = dict(raw_reg)
    factor_regression["betas"] = {k: float(used_betas.get(k, 0.0)) for k in helpers["_macro_beta_keys"]()}
    factor_regression["estimate_used"] = "raw_regime" if not used_fallback else "shrunk_to_base_10y"
    factor_regression["variance_scale"] = "monthly"

    block = {
        "label": regime,
        "n_obs": int(len(y_v)),
        "quality_status": macro_quality_status(int(len(y_v))),
        "historical_estimate_available": True,
        "used_fallback": bool(used_fallback),
        "fallback_method": fallback_method,
        "fallback_target": "base_10y" if used_fallback else None,
        "shrinkage_weight_regime": shrinkage_weight,
        "factor_regression": factor_regression,
        "factor_covariance": helpers["_macro_covariance_block"](
            used_cov,
            label=regime,
            n_obs=int(len(y_v)),
            source="raw_regime" if not used_fallback else "shrunk_to_base_10y",
        ),
        "portfolio_factor_risk": helpers["_macro_factor_risk"](used_cov, used_betas, label=regime),
        "portfolio_factor_rc": helpers["_macro_factor_rc"](used_cov, used_betas),
    }
    if used_fallback:
        block["raw_factor_covariance"] = helpers["_macro_covariance_block"](
            raw_cov,
            label=f"{regime}_raw",
            n_obs=int(len(y_v)),
            source="raw_regime_low_confidence",
        )
    return block


def macro_two_axis_diagnostics_from_frames(
    portfolio_returns_monthly: pd.Series,
    factor_returns_monthly: pd.DataFrame,
    indicator_panel: pd.DataFrame,
    indicator_meta: dict[str, Any],
    analysis_end_str: str,
    *,
    neutral_band: float = MACRO_REGIME_NEUTRAL_BAND_DEFAULT,
    indicators: tuple[IndicatorSpec, ...] | None = None,
) -> dict[str, Any]:
    """Compute the full ``macro_two_axis_v1`` diagnostic from supplied frames."""

    helpers = _macro_helpers()
    factor_order = list(helpers["_macro_order"]())
    base_payload = {
        "axis_model": {
            "version": MACRO_REGIME_METHOD_VERSION,
            "frequency": "monthly",
            "neutral_band_abs": float(neutral_band),
            "score_blend": {
                "momentum": MACRO_COMPOSITE_MOMENTUM_WEIGHT,
                "level": MACRO_COMPOSITE_LEVEL_WEIGHT,
            },
            "look_ahead_protection": "lag_1m",
            "look_ahead_caveat": MACRO_REGIME_LOOK_AHEAD_CAVEAT,
            "score_window_months": int(MACRO_SCORE_WINDOW_MONTHS),
            "score_min_periods": int(MACRO_SCORE_MIN_PERIODS),
        },
        "method_disclaimer": MACRO_REGIME_METHOD_DISCLAIMER,
        "factor_order": factor_order,
        "beta_order": helpers["_macro_beta_keys"](),
    }

    available_blocks, missing_blocks, optional_missing = _resolved_blocks(indicator_meta or {})
    coverage_tier, coverage_ratio = _coverage_tier(
        available_blocks,
        missing_blocks,
        indicator_meta.get("data_sources_used", {}) if indicator_meta else {},
        indicator_meta.get("indicator_specs", {}) if indicator_meta else {},
    )

    if indicator_panel is None or indicator_panel.empty:
        return {
            **base_payload,
            "error": "empty_indicator_panel",
            "coverage_tier": "insufficient",
            "coverage_ratio": float(coverage_ratio),
            "available_blocks": sorted(available_blocks),
            "missing_blocks": sorted(missing_blocks),
            "optional_blocks_missing": sorted(optional_missing),
            "planned_not_loaded": [],
            "data_sources_used": (indicator_meta or {}).get("data_sources_used", {}),
            "score_lag_months": int(MACRO_REGIME_SCORE_LAG_MONTHS),
        }

    scores = compute_macro_scores(
        indicator_panel,
        indicator_meta or {},
        neutral_band=neutral_band,
        indicators=indicators,
    )
    if scores.empty:
        return {
            **base_payload,
            "error": "empty_scores",
            "coverage_tier": coverage_tier,
            "coverage_ratio": float(coverage_ratio),
            "available_blocks": sorted(available_blocks),
            "missing_blocks": sorted(missing_blocks),
            "optional_blocks_missing": sorted(optional_missing),
            "planned_not_loaded": [],
            "data_sources_used": (indicator_meta or {}).get("data_sources_used", {}),
            "score_lag_months": int(MACRO_REGIME_SCORE_LAG_MONTHS),
        }

    end_ts = pd.Timestamp(analysis_end_str).to_period("M").to_timestamp("M")
    scores = scores.loc[scores.index <= end_ts]

    # First date with a non-NaN composite score.
    composite_valid = scores.dropna(subset=["growth_score", "inflation_score"])
    score_start_date = (
        str(composite_valid.index[0].date()) if not composite_valid.empty else None
    )
    labelled = scores.dropna(subset=["growth_score", "inflation_score", "regime"])
    regime_label_start_date = (
        str(labelled.index[0].date()) if not labelled.empty else None
    )

    # Latest unlagged scores describe the most recent macro reading; the lagged
    # regime label is what should be used "for the next month".
    if composite_valid.empty:
        latest_growth = float("nan")
        latest_inflation = float("nan")
        latest_date = None
    else:
        latest_row = composite_valid.iloc[-1]
        latest_growth = float(latest_row["growth_score"])
        latest_inflation = float(latest_row["inflation_score"])
        latest_date = str(composite_valid.index[-1].date())

    # The "current_regime" should be the regime label at the latest available row
    # (already lagged by 1 month inside compute_macro_scores).
    current_regime = "neutral_transition"
    regime_transition_warning = True
    if not labelled.empty:
        current_regime = str(labelled.iloc[-1]["regime"])

    if np.isfinite(latest_growth) and np.isfinite(latest_inflation):
        regime_transition_warning = (
            abs(latest_growth) <= neutral_band or abs(latest_inflation) <= neutral_band
        )

    confidence_level = _confidence_level(
        growth_score=latest_growth,
        inflation_score=latest_inflation,
        coverage_tier=coverage_tier,
        neutral_band=neutral_band,
        optional_blocks_missing=optional_missing,
    )

    # Prepare per-regime factor analytics on monthly data.
    portfolio_returns_monthly = pd.Series(portfolio_returns_monthly, dtype=float).copy()
    portfolio_returns_monthly.index = pd.to_datetime(
        portfolio_returns_monthly.index
    ).tz_localize(None)
    factor_returns_monthly = factor_returns_monthly.copy()
    factor_returns_monthly.index = pd.to_datetime(
        factor_returns_monthly.index
    ).tz_localize(None)
    factor_cols = [c for c in factor_order if c in factor_returns_monthly.columns]
    if not factor_cols:
        return {
            **base_payload,
            "error": "missing_factor_columns",
            "coverage_tier": coverage_tier,
            "coverage_ratio": float(coverage_ratio),
            "available_blocks": sorted(available_blocks),
            "missing_blocks": sorted(missing_blocks),
            "optional_blocks_missing": sorted(optional_missing),
            "planned_not_loaded": [],
            "data_sources_used": (indicator_meta or {}).get("data_sources_used", {}),
            "score_lag_months": int(MACRO_REGIME_SCORE_LAG_MONTHS),
        }

    common = (
        portfolio_returns_monthly.dropna()
        .index.intersection(factor_returns_monthly[factor_cols].dropna().index)
        .intersection(scores.dropna(subset=["regime"]).index)
        .sort_values()
    )
    if len(common) < MACRO_REGIME_INSUFFICIENT_MAX_ROWS:
        return {
            **base_payload,
            "error": "insufficient_common_rows",
            "n_obs": int(len(common)),
            "coverage_tier": coverage_tier,
            "coverage_ratio": float(coverage_ratio),
            "available_blocks": sorted(available_blocks),
            "missing_blocks": sorted(missing_blocks),
            "optional_blocks_missing": sorted(optional_missing),
            "planned_not_loaded": [],
            "data_sources_used": (indicator_meta or {}).get("data_sources_used", {}),
            "score_lag_months": int(MACRO_REGIME_SCORE_LAG_MONTHS),
        }

    y_aligned = portfolio_returns_monthly.reindex(common).astype(float)
    x_aligned = factor_returns_monthly.reindex(common).loc[:, factor_cols].astype(float)
    scores_aligned = scores.reindex(common)

    base_reg = helpers["_macro_regression_from_arrays"](
        y_aligned.values.astype(float),
        x_aligned.values.astype(float),
        factor_cols,
        label="base_10y",
        n_obs=int(len(y_aligned)),
    )
    if isinstance(base_reg, dict):
        base_reg["variance_scale"] = "monthly"
    base_betas = {k: float(v) for k, v in (base_reg.get("betas") or {}).items()}
    for beta_key in helpers["_macro_beta_keys"]():
        base_betas.setdefault(beta_key, 0.0)
    base_cov = helpers["_macro_covariance_matrix"](x_aligned)

    regimes: dict[str, Any] = {}
    regime_betas_used: dict[str, dict[str, float]] = {}
    quality_by_regime: dict[str, str] = {}
    regime_counts: dict[str, int] = {regime: 0 for regime in MACRO_REGIME_NAMES}

    for regime in MACRO_REGIME_NAMES:
        regime_dates = scores_aligned.index[scores_aligned["regime"] == regime]
        regime_counts[regime] = int(len(regime_dates))
        block = _per_regime_block(
            regime=regime,
            regime_dates=regime_dates,
            y_monthly=y_aligned,
            x_monthly=x_aligned,
            factor_cols=factor_cols,
            base_betas=base_betas,
            base_cov=base_cov,
            helpers=helpers,
        )
        regimes[regime] = block
        quality_by_regime[regime] = block.get("quality_status", "no_observations")
        if block.get("historical_estimate_available"):
            regime_betas_used[regime] = {
                k: float(v)
                for k, v in (block.get("factor_regression", {}).get("betas") or {}).items()
            }

    available_regimes_count = sum(
        1 for q in quality_by_regime.values() if q in {"usable", "reliable"}
    )
    by_quality = {
        q: list(quality_by_regime.values()).count(q) for q in sorted(set(quality_by_regime.values()))
    }

    labels_monthly = []
    for ts, row in scores.dropna(subset=["growth_score", "inflation_score"]).iterrows():
        labels_monthly.append(
            {
                "date": pd.Timestamp(ts).strftime("%Y-%m-%d"),
                "growth_score": float(row["growth_score"]),
                "inflation_score": float(row["inflation_score"]),
                "growth_level": float(row["growth_level"]),
                "growth_momentum": float(row["growth_momentum"]),
                "inflation_level": float(row["inflation_level"]),
                "inflation_momentum": float(row["inflation_momentum"]),
                "regime": str(row.get("regime") or "neutral_transition"),
                "regime_unlagged": str(row.get("regime_unlagged") or "neutral_transition"),
            }
        )

    # Indicator panel rows — long-form: one row per (date, indicator) with level/momentum.
    indicator_panel_rows: list[dict[str, Any]] = []
    if indicator_panel is not None and not indicator_panel.empty:
        spec_by_key = {spec.key: spec for spec in (indicators or INDICATORS)}
        for ts in indicator_panel.index:
            for key, spec in spec_by_key.items():
                lvl_col = f"{key}__level"
                mom_col = f"{key}__momentum"
                if lvl_col not in indicator_panel.columns and mom_col not in indicator_panel.columns:
                    continue
                lvl = indicator_panel.at[ts, lvl_col] if lvl_col in indicator_panel.columns else np.nan
                mom = indicator_panel.at[ts, mom_col] if mom_col in indicator_panel.columns else np.nan
                if pd.isna(lvl) and pd.isna(mom):
                    continue
                indicator_panel_rows.append(
                    {
                        "date": pd.Timestamp(ts).strftime("%Y-%m-%d"),
                        "indicator": key,
                        "block": spec.block,
                        "axis": spec.axis,
                        "role": spec.role,
                        "sign": spec.sign,
                        "level": float(lvl) if pd.notna(lvl) else None,
                        "momentum": float(mom) if pd.notna(mom) else None,
                    }
                )

    payload = {
        **base_payload,
        "axis_scores_latest": {
            "date": latest_date,
            "growth_score": latest_growth,
            "inflation_score": latest_inflation,
            "growth_level": float(composite_valid["growth_level"].iloc[-1]) if not composite_valid.empty else float("nan"),
            "growth_momentum": float(composite_valid["growth_momentum"].iloc[-1]) if not composite_valid.empty else float("nan"),
            "inflation_level": float(composite_valid["inflation_level"].iloc[-1]) if not composite_valid.empty else float("nan"),
            "inflation_momentum": float(composite_valid["inflation_momentum"].iloc[-1]) if not composite_valid.empty else float("nan"),
            "growth_blocks": {
                block: float(composite_valid.get(f"growth_block_{block}_level", pd.Series([np.nan])).iloc[-1])
                if not composite_valid.empty
                else float("nan")
                for block in GROWTH_BLOCKS
            },
            "inflation_blocks": {
                block: float(composite_valid.get(f"inflation_block_{block}_level", pd.Series([np.nan])).iloc[-1])
                if not composite_valid.empty
                else float("nan")
                for block in INFLATION_BLOCKS
            },
        },
        "current_regime": current_regime,
        "regime_confidence": confidence_level,
        "regime_transition_warning": bool(regime_transition_warning),
        "score_lag_months": int(MACRO_REGIME_SCORE_LAG_MONTHS),
        "score_start_date": score_start_date,
        "regime_label_start_date": regime_label_start_date,
        "available_blocks": sorted(available_blocks),
        "missing_blocks": sorted(missing_blocks),
        "optional_blocks_missing": sorted(optional_missing),
        "planned_not_loaded": [],
        "coverage_ratio": float(coverage_ratio),
        "coverage_tier": coverage_tier,
        "confidence_level": confidence_level,
        "data_sources_used": (indicator_meta or {}).get("data_sources_used", {}),
        "regime_counts": regime_counts,
        "available_regimes_count": int(available_regimes_count),
        "available_regimes_by_quality": by_quality,
        "base_10y": {
            "n_obs": int(len(y_aligned)),
            "factor_regression": base_reg,
            "factor_covariance": helpers["_macro_covariance_block"](
                base_cov, label="base_10y", n_obs=int(len(y_aligned)), source="base_10y"
            ),
        },
        "regimes": regimes,
        "stability_summary": helpers["_macro_policy_signal"](regime_betas_used, quality_by_regime),
        "labels_monthly": labels_monthly,
        "indicator_panel_rows": indicator_panel_rows,
    }

    return payload


# ---------------------------------------------------------------------------
# Production entry point: fetches data and runs the full pipeline.
# ---------------------------------------------------------------------------


def _build_monthly_portfolio_and_factors(
    *,
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    factor_returns_monthly: pd.DataFrame | None,
    months_back: int = 240,
) -> tuple[pd.Series, pd.DataFrame, pd.Timestamp, pd.Timestamp]:
    """Build monthly portfolio + factor returns for the production path."""

    from src import stress_factors as sf
    from src.data_yf import download_all

    end_ts = pd.Timestamp(analysis_end_str)
    start_ts = end_ts - pd.DateOffset(months=int(months_back) + 6)
    start_dl = start_ts.strftime("%Y-%m-%d")
    end_dl = (end_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    use = [t for t in tickers if float(weights.get(t, 0.0)) > 0]
    if not use:
        use = list(tickers)
    use = [str(t).strip() for t in use if t and str(t).strip()]

    daily = download_all(use, start_dl, end_dl) if use else {}
    monthly_prices: dict[str, pd.Series] = {}
    for t in use:
        df = daily.get(t)
        if df is None or df.empty or "Close" not in df.columns:
            continue
        s = pd.Series(df["Close"], dtype=float).dropna()
        s.index = pd.to_datetime(s.index).tz_localize(None)
        monthly_prices[t] = s.resample(MONTH_END_FREQ).last()

    if not monthly_prices:
        empty = pd.Series(dtype=float)
        return empty, pd.DataFrame(), start_ts, end_ts

    prices = pd.DataFrame(monthly_prices).sort_index()
    asset_monthly = prices.pct_change().dropna(how="all")

    w_vec = np.array([float(weights.get(t, 0.0)) for t in asset_monthly.columns], dtype=float)
    valid = ~asset_monthly.isna()
    contrib = (asset_monthly.fillna(0.0).values * w_vec.reshape(1, -1))
    portfolio_monthly = pd.Series(contrib.sum(axis=1), index=asset_monthly.index, dtype=float)
    portfolio_monthly = portfolio_monthly.where(valid.any(axis=1), other=np.nan).dropna()

    if factor_returns_monthly is None or factor_returns_monthly.empty:
        factor_returns_monthly = sf.build_factor_matrix_monthly(start_dl, end_dl)
    factor_returns_monthly = factor_returns_monthly.copy()
    factor_returns_monthly.index = pd.to_datetime(factor_returns_monthly.index).tz_localize(None)
    factor_returns_monthly = factor_returns_monthly.sort_index()

    return portfolio_monthly, factor_returns_monthly, start_ts, end_ts


def macro_two_axis_diagnostics(
    *,
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    factor_returns_monthly: pd.DataFrame | None = None,
    neutral_band: float = MACRO_REGIME_NEUTRAL_BAND_DEFAULT,
    months_back: int = 240,
) -> dict[str, Any]:
    """Production entry: build monthly portfolio + factor returns, fetch macro
    indicator panel, and run the full ``macro_two_axis_v1`` diagnostic.
    """

    helpers = _macro_helpers()
    factor_order = list(helpers["_macro_order"]())
    base_payload = {
        "axis_model": {
            "version": MACRO_REGIME_METHOD_VERSION,
            "frequency": "monthly",
            "neutral_band_abs": float(neutral_band),
            "score_blend": {
                "momentum": MACRO_COMPOSITE_MOMENTUM_WEIGHT,
                "level": MACRO_COMPOSITE_LEVEL_WEIGHT,
            },
            "look_ahead_protection": "lag_1m",
            "look_ahead_caveat": MACRO_REGIME_LOOK_AHEAD_CAVEAT,
            "score_window_months": int(MACRO_SCORE_WINDOW_MONTHS),
            "score_min_periods": int(MACRO_SCORE_MIN_PERIODS),
        },
        "method_disclaimer": MACRO_REGIME_METHOD_DISCLAIMER,
        "factor_order": factor_order,
        "beta_order": helpers["_macro_beta_keys"](),
    }

    try:
        port_monthly, factors_monthly, start_ts, end_ts = _build_monthly_portfolio_and_factors(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            factor_returns_monthly=factor_returns_monthly,
            months_back=months_back,
        )
    except Exception as exc:
        _LOG.warning("macro_two_axis: failed to build monthly returns: %s", exc)
        return {
            **base_payload,
            "error": f"build_monthly_inputs_failed: {exc}",
            "coverage_tier": "insufficient",
            "coverage_ratio": 0.0,
            "score_lag_months": int(MACRO_REGIME_SCORE_LAG_MONTHS),
        }

    if port_monthly.empty or factors_monthly.empty:
        return {
            **base_payload,
            "error": "empty_monthly_inputs",
            "coverage_tier": "insufficient",
            "coverage_ratio": 0.0,
            "score_lag_months": int(MACRO_REGIME_SCORE_LAG_MONTHS),
        }

    panel_start = (end_ts - pd.DateOffset(months=int(months_back) + 12)).strftime("%Y-%m-%d")
    panel_end = (end_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        panel, meta = fetch_macro_indicators(panel_start, panel_end)
    except Exception as exc:
        _LOG.warning("macro_two_axis: fetch_macro_indicators failed: %s", exc)
        return {
            **base_payload,
            "error": f"fetch_macro_indicators_failed: {exc}",
            "coverage_tier": "insufficient",
            "coverage_ratio": 0.0,
            "score_lag_months": int(MACRO_REGIME_SCORE_LAG_MONTHS),
        }

    return macro_two_axis_diagnostics_from_frames(
        port_monthly,
        factors_monthly,
        panel,
        meta,
        analysis_end_str,
        neutral_band=neutral_band,
    )


# ---------------------------------------------------------------------------
# CSV builders
# ---------------------------------------------------------------------------


def macro_regime_csv_frames(report: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Return CSV-ready DataFrames.

    Produces (when data is present):
      - macro_regime_labels_monthly.csv
      - macro_regime_factor_betas.csv
      - macro_regime_factor_covariance.csv
      - macro_regime_factor_rc.csv
      - macro_regime_indicator_panel.csv
    """

    if not isinstance(report, dict) or report.get("error"):
        return {}

    frames: dict[str, pd.DataFrame] = {}
    labels = report.get("labels_monthly") or []
    if labels:
        frames["macro_regime_labels_monthly.csv"] = pd.DataFrame(labels)

    betas_rows: list[dict[str, Any]] = []
    cov_rows: list[dict[str, Any]] = []
    rc_rows: list[dict[str, Any]] = []
    regimes = report.get("regimes") or {}
    for regime, payload in regimes.items():
        if not isinstance(payload, dict):
            continue
        quality = payload.get("quality_status")
        used_fallback = payload.get("used_fallback")
        fallback_method = payload.get("fallback_method")
        if not payload.get("historical_estimate_available"):
            continue
        betas = ((payload.get("factor_regression") or {}).get("betas") or {})
        for beta_key, value in betas.items():
            betas_rows.append(
                {
                    "regime": regime,
                    "beta_key": beta_key,
                    "beta": value,
                    "quality_status": quality,
                    "used_fallback": used_fallback,
                    "fallback_method": fallback_method,
                    "n_obs": payload.get("n_obs"),
                }
            )
        cov_block = payload.get("factor_covariance") or {}
        matrix = cov_block.get("matrix") or {}
        for factor_i, row in matrix.items():
            if not isinstance(row, dict):
                continue
            for factor_j, value in row.items():
                cov_rows.append(
                    {
                        "regime": regime,
                        "factor_i": factor_i,
                        "factor_j": factor_j,
                        "covariance": value,
                        "quality_status": quality,
                        "used_fallback": used_fallback,
                        "n_obs": payload.get("n_obs"),
                    }
                )
        for row in payload.get("portfolio_factor_rc") or []:
            if isinstance(row, dict):
                rc_rows.append(
                    {
                        "regime": regime,
                        "quality_status": quality,
                        "used_fallback": used_fallback,
                        "n_obs": payload.get("n_obs"),
                        **row,
                    }
                )
    if betas_rows:
        frames["macro_regime_factor_betas.csv"] = pd.DataFrame(betas_rows)
    if cov_rows:
        frames["macro_regime_factor_covariance.csv"] = pd.DataFrame(cov_rows)
    if rc_rows:
        frames["macro_regime_factor_rc.csv"] = pd.DataFrame(rc_rows)

    panel_rows = report.get("indicator_panel_rows")
    if panel_rows:
        frames["macro_regime_indicator_panel.csv"] = pd.DataFrame(panel_rows)

    return frames


__all__ = [
    "MACRO_REGIME_METHOD_VERSION",
    "MACRO_REGIME_METHOD_DISCLAIMER",
    "MACRO_REGIME_LOOK_AHEAD_CAVEAT",
    "MACRO_REGIME_NAMES",
    "MACRO_REGIME_NEUTRAL_BAND_DEFAULT",
    "MACRO_REGIME_SCORE_LAG_MONTHS",
    "MACRO_REGIME_INSUFFICIENT_MAX_ROWS",
    "MACRO_REGIME_LOW_CONFIDENCE_MIN_ROWS",
    "MACRO_REGIME_USABLE_MIN_ROWS",
    "MACRO_REGIME_RELIABLE_MIN_ROWS",
    "MACRO_SCORE_WINDOW_MONTHS",
    "MACRO_SCORE_MIN_PERIODS",
    "GROWTH_BLOCKS",
    "INFLATION_BLOCKS",
    "OPTIONAL_BLOCKS",
    "INDICATORS",
    "IndicatorSpec",
    "SourceSpec",
    "macro_quality_status",
    "apply_transform",
    "fetch_macro_indicators",
    "compute_macro_scores",
    "macro_two_axis_diagnostics",
    "macro_two_axis_diagnostics_from_frames",
    "macro_regime_csv_frames",
]
