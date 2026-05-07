# Macro two-axis regime v1 (`macro_two_axis_v1`)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository contains `PLANS.md` at the repository root. Maintain this document in
accordance with `PLANS.md`.

## Purpose / Big Picture

After this change, `stress_report.json.macro_regime_diagnostics` switches from the prior
weekly two-factor proxy (`internal_market_proxy_v1`, growth = rolling z-score of
`us_growth`, inflation pressure = average rolling z-score of `inflation` and `commodity`)
to a real **macro-data** classifier (`macro_two_axis_v1`) operating at **monthly**
frequency. The new model:

- composes a **Growth Score** from five blocks (business activity, labor, consumer,
  credit, growth nowcast) and an **Inflation Score** from five blocks (core inflation,
  headline inflation, wages, inflation expectations, business price pressure);
- normalises every indicator with a **rolling 10-year monthly z-score** (window 120,
  `min_periods=60`), maps to a `-1 / 0 / +1` signal at thresholds `±0.5`, then averages
  per block, blends `0.6·momentum + 0.4·level`, and labels the latest month as
  `goldilocks / reflation / stagflation / recession_disinflation` outside the
  `±0.25` neutral band, otherwise `neutral_transition`;
- applies a **1-month look-ahead lag** (data for month `t` labels month `t+1`) and
  explicitly states that release-date / vintage handling is out of scope for v1;
- runs **per-regime monthly OLS + HAC inference, factor covariance, factor risk and
  RC** for the base factors, with explicit observation gating: `n_obs < 12 →
  insufficient_data` (estimates suppressed), `12 ≤ n < 24 → low_confidence`,
  `24 ≤ n < 60 → usable`, `n ≥ 60 → reliable`;
- ingests indicators through a layered **source resolver** in
  `src/data_macro_sources.py` covering FRED, Yahoo Finance, official CSV (Atlanta
  Fed GDPNow, NY Fed Nowcast historical), official API, keyed third-party API, and
  manual CSV fallback, each entry declaring its `source_chain`, `transform`, `sign`,
  `role` (`required` / `optional`), and required env keys. Missing API keys do not
  crash the run; the indicator becomes `available=False` and the model degrades to
  a lower `coverage_tier`.

A portfolio reviewer can run `python run_report.py --no-cache` and inspect
`stress_report.json.macro_regime_diagnostics` to see: latest `growth_score` and
`inflation_score` with per-block sub-scores; `current_regime` and `regime_confidence`;
`coverage_tier` (`full / extended / reduced / fred_baseline / insufficient`),
`available_blocks`, `missing_blocks`, `optional_blocks_missing`, `data_sources_used`,
`score_lag_months: 1`, `look_ahead_caveat`; per-regime factor regression (with HAC
inference), covariance, factor risk and RC; `stability_summary` with policy signals;
plus four CSVs in `results_csv/` — `macro_regime_labels_monthly.csv` (replaces the
old weekly file), `macro_regime_factor_betas.csv`, `macro_regime_factor_covariance.csv`,
`macro_regime_factor_rc.csv` — and a new additive `macro_regime_indicator_panel.csv`.
The `stress_commentary.txt` macro section is rewritten to report the same fields in
client-grade English, including the lag/no-vintage caveat and the ECI quarterly-ffill
caveat.

The block remains **diagnostic-only** per `AGENTS.md` Core Rules: it does not change
optimizer weights, mandate gates, stress pass/fail, or weight release.

## Progress

- [x] (2026-05-05) Authored the planning summary in `.cursor/plans/macro_two-axis_regime_v1_*.plan.md` and refined the `coverage_tier` semantics, NY Fed Nowcast handling, generic `level` definition, and CSV rename rule.
- [x] (2026-05-06) Create checked-in ExecPlan `docs/exec_plans/2026-05-05_macro_two_axis_regime_v1.md` (this file).
- [x] Built `src/data_macro_sources.py` with `IndicatorSpec` / `SourceSpec` and `resolve_indicator(...)` covering FRED → Yahoo → official CSV → official API → keyed API → manual CSV.
- [x] Built `src/stress_factors_macro.py` with the indicator registry, transforms, scoring, regime classifier, and monthly per-regime analytics (HAC inference flows through the existing `_macro_regression_from_arrays` helper in `src/stress_factors.py`).
- [x] Replaced the `internal_market_proxy_v1` weekly axis helper and entry points in `src/stress_factors.py`; back-compat imports `macro_regime_diagnostics`, `macro_regime_diagnostics_from_frames`, `macro_regime_csv_frames` redirect to the new module.
- [x] `run_optimization.py` and `run_report.py` continue to call `macro_regime_diagnostics(weights=…, tickers=…, analysis_end_str=…, factor_returns=…)` unchanged; the legacy `factor_returns` kwarg is preserved (ignored by v1) so existing call sites keep working without edits.
- [x] Updated `src/portfolio_commentary._append_macro_regime_section` to render `coverage_tier`, `available_blocks`, `missing_blocks`, `optional_blocks_missing`, `confidence_level`, `score_lag_months`, the lag/no-vintage caveat, the ECI ffill caveat, and `neutral_transition`.
- [x] Rewrote `tests/test_macro_regimes.py`; added `tests/test_macro_indicators.py`, `tests/test_macro_source_resolver.py`, `tests/test_macro_neutral_band_sensitivity.py`; updated `tests/test_portfolio_commentary.py`.
- [x] Rewrote `docs/docs/stress_testing_spec.md` §8.8.2; refreshed `AGENTS.md`, `PROJECT_RULES.md`, `SPEC.md`, `README.md`.
- [x] Ran focused, broader factor/stress, and full pytest. See `Artifacts and Notes`.

## Surprises & Discoveries

- Observation: ISM PMI / ISM Prices Paid have no stable free FRED API in 2024–2026.
  Evidence: FRED legacy series like `NAPM` (ISM Manufacturing PMI) end before 2017;
  ISM website is paywalled. Implementation must accept manual CSV fallback at
  `cache/macro/<key>.csv` (path overridable via `<KEY>_CSV_PATH` env var).
- Update (2026-05-07): Atlanta Fed GDPNow is **available via FRED:GDPNOW** as a
  quarterly nowcast (Percent Change at Annual Rate, SAAR). Source:
  https://fred.stlouisfed.org/series/GDPNOW. Wired into the resolver as the
  primary source for the `gdpnow` indicator with frequency `Q` and a new
  `quarterly_ffill_monthly_three_m_change` transform; the Atlanta Fed direct
  CSV remains as a secondary source.
- Observation: NY Fed Nowcast was discontinued in 2021.
  Evidence: NY Fed publishes the historical CSV but no current values; therefore it
  must be tagged `historical_only` and its absence at the current month must not
  push `confidence_level` down nor flip `coverage_tier` from `full` / `extended`
  on its own.
- Observation: The existing weekly helpers in `src/stress_factors.py`
  (`_macro_regression_from_arrays`, `_macro_covariance_block`, `_macro_factor_risk`,
  `_macro_factor_rc`, `_macro_policy_signal`, `_macro_quality_status`) are
  factor-frequency-agnostic.
  Evidence: They take pandas frames and numpy arrays without weekly assumptions.
  Implication: We can reuse them from the new module by passing monthly inputs and
  by re-tuning only the quality thresholds and quality-status name (`insufficient_data`
  for `n < 12`).

## Decision Log

- Decision: Choose **Option A** — implement the full source architecture up front
  and keep `MACRO_REGIME_METHOD_VERSION = "macro_two_axis_v1"` even when ISM /
  GDPNow / NY Fed Nowcast cannot be resolved; expose the actual resolution outcome
  through `coverage_tier` and `data_sources_used`.
  Rationale: A coverage-aware tier is more honest than a tiered method version and
  keeps the JSON contract stable across runs.
  Date/Author: 2026-05-06 / Codex.
- Decision: Frequency = **monthly**, end-of-month effective dates per
  `metrics_specification.md`.
  Rationale: Spec is monthly; macro indicators are mostly monthly natively; per-regime
  factor stability is more meaningful on monthly rows than weekly noise.
  Date/Author: 2026-05-06 / Codex.
- Decision: Look-ahead protection = **1-month lag** only. Release-date / vintage
  handling is out of scope for v1.
  Rationale: Vintage-accurate handling is a major project (FRED ALFRED-style data),
  not part of MVP. The 1-month lag covers most release calendars (CPI, payrolls,
  PCE) and is documented in `axis_model.look_ahead_caveat`.
  Date/Author: 2026-05-06 / Codex.
- Decision: Add a fifth label `neutral_transition` to `MACRO_REGIME_NAMES`.
  Rationale: The user spec requires explicit handling of the neutral band; without a
  dedicated label we would either misclassify or hide the state.
  Date/Author: 2026-05-06 / Codex.
- Decision: Per-regime n_obs gating: `<12 hidden`, `12–23 low`, `24–59 usable`,
  `60+ reliable`. Below 12 monthly observations the regression / covariance / RC
  blocks contain only `n_obs` and `quality_status = "insufficient_data"`.
  Rationale: Avoid presenting noisy estimates as meaningful.
  Date/Author: 2026-05-06 / Codex.
- Decision: CSV — replace the old weekly labels file with
  `macro_regime_labels_monthly.csv` (the weekly file is no longer written); preserve
  `macro_regime_factor_betas.csv`, `macro_regime_factor_covariance.csv`,
  `macro_regime_factor_rc.csv`; add a new additive
  `macro_regime_indicator_panel.csv`.
  Rationale: Honest about the change, minimises downstream consumer churn.
  Date/Author: 2026-05-06 / Codex.

## Outcomes & Retrospective

Implementation matches the purpose:

- `stress_report.json.macro_regime_diagnostics.axis_model.version` is now
  `macro_two_axis_v1` and the same shape contract is maintained on every run.
- The pipeline is monthly with rolling 10-year z-score normalisation, a `0.6 ·
  momentum + 0.4 · level` blend, a 1-month publication lag, and an explicit
  `neutral_transition` label inside the `±0.25` band by default.
- Indicator coverage is honest: `coverage_tier` reports `full`, `extended`,
  `reduced`, `fred_baseline`, or `insufficient`; missing optional blocks
  (`growth_nowcast`) do not pull `confidence_level` below `medium` on their
  own.
- Per-regime monthly OLS / covariance / RC analytics are gated by n_obs:
  estimates are suppressed below 12 monthly observations, linearly shrunk to
  `base_10y` between 12–23 rows, used raw between 24–59, and treated as
  reliable from 60+.
- Reports (`stress_commentary.txt` and downstream PDFs via the unchanged
  `_append_macro_regime_section`) carry the look-ahead lag/no-vintage caveat
  and the ECI ffill caveat in English, alongside the method disclaimer.

Trade-offs / lessons:

- ISM PMI / ISM Prices Paid are not freely available via FRED post-2017; the
  resolver supports a keyed-API stub plus manual CSV fallback. Without an ISM
  feed the model honestly reports `coverage_tier = reduced` rather than
  silently inventing values.
- NY Fed Nowcast was discontinued in 2021. The registry tags it
  `historical_only=True` so its absence at the latest month does not penalise
  current confidence.
- Vintage / release-date accuracy remains out of scope and is documented in
  `axis_model.look_ahead_caveat`. A future iteration could integrate FRED
  ALFRED-style vintage data.

## Context and Orientation

- `src/stress_factors.py` is ~5290 lines and hosts factor matrix construction,
  weekly/monthly factor regressions, factor covariance / variance decomposition /
  PCA / Kalman / OOS analytics, and the prior weekly macro regime diagnostic.
  Constants `MACRO_REGIME_METHOD_VERSION`, `MACRO_REGIME_NAMES`,
  `MACRO_REGIME_SCORE_WINDOW_WEEKS`, etc. live here.
- `src/data_fred.py` exposes `fetch_fred_series(series_id, start, end, api_key=None)`
  using `pandas_datareader.get_data_fred`, picking up `FRED_API_KEY` from the
  environment; failures return an empty Series only when re-wrapped.
- `src/data_yf.py` exposes `fetch_daily(ticker, start, end)` and
  `download_all(tickers, start, end)` using yfinance.
- `run_optimization.py` and `run_report.py` import
  `macro_regime_diagnostics`, `macro_regime_csv_frames` from `src.stress_factors`
  and call them inside try/except blocks; we keep these import names but redirect
  them to the new monthly entry points.
- `src/portfolio_commentary.py` has `_append_macro_regime_section(lines, st)` reading
  from `st["macro_regime_diagnostics"]`.
- `tests/test_macro_regimes.py` covers the prior weekly contract; rewritten in this
  ExecPlan.

A "regime" is a label assigned to the latest available monthly row of macro
indicators after a 1-month lag. The label is one of `goldilocks`, `reflation`,
`stagflation`, `recession_disinflation`, `neutral_transition`. A regime is reported
together with `regime_confidence` (low / medium / high), `coverage_tier`
(`full / extended / reduced / fred_baseline / insufficient`), and a list of
`available_blocks` / `missing_blocks` / `optional_blocks_missing` so the user can
read the macro narrative even when some indicators are unavailable.

## Plan of Work

1. Add `src/data_macro_sources.py`. Define `SourceSpec` and `IndicatorSpec`
   dataclasses, and `resolve_indicator(spec, start, end)` that walks
   `spec.source_chain` (FRED → Yahoo → official CSV → official API → keyed API →
   manual CSV) and returns `(series, meta)` where `meta` includes `source_used`,
   `available`, `frequency_native`, `last_observation_date`, `historical_only`, and
   any error. Fail closed: every loader returns an empty `Series` on error rather
   than raising. Helper for the manual CSV reader: read `cache/macro/<key>.csv` or
   `<KEY>_CSV_PATH` env var, schema `date,value`.
2. Add `src/stress_factors_macro.py`.
   - Static `INDICATORS: tuple[IndicatorSpec, ...]` listing the 14 FRED-served
     indicators plus 5 non-FRED indicators (ISM Manuf PMI, ISM Services PMI,
     ISM Manuf Prices Paid, ISM Services Prices Paid, GDPNow, NY Fed Nowcast).
   - Transforms: `level` (month-end), `m_over_m_change`, `three_m_avg_mom`
     (used for PAYEMS), `three_m_change` (used for UNRATE etc.), `three_m_yoy`
     (used for real PCE / DPI / AHE), `three_m_annualized` (used for core / headline
     CPI, core PCE), `oil_monthly_avg_three_m_change` (DCOILWTICO daily → monthly
     mean → 3m change), `quarterly_ffill_monthly` (ECI Q → M ffill), and a generic
     `level + 3m change` pair for ISM / breakevens / NFCI / HY OAS.
   - `fetch_macro_indicators(start, end) -> (panel, meta)`. Iterates `INDICATORS`,
     calls `resolve_indicator`, applies the spec's transform, writes monthly columns
     `<key>_level`, `<key>_momentum`, and registers `data_sources_used[key]`,
     `frequency_native[key]`, `historical_only[key]` in `meta`.
   - `compute_macro_scores(panel, meta, *, neutral_band=0.25) -> pd.DataFrame`.
     Rolling 10y monthly z-score (window 120, `min_periods=60`), bucketed signal
     (`+1 / 0 / -1` at `±0.5`), per-block mean of available signals (with sign map),
     composite blend `0.6·momentum + 0.4·level`. Labels per row including
     `neutral_transition` when either composite is in `[-band, +band]`. Apply the
     1-month lag (`shift(1)`) before labelling. Compute and write `score_start_date`,
     `regime_label_start_date`, `available_blocks`, `missing_blocks`,
     `optional_blocks_missing`, `coverage_ratio`, `coverage_tier`, `confidence_level`.
   - `macro_two_axis_diagnostics_from_frames(portfolio_returns_monthly,
     factor_returns_monthly, indicator_panel, indicator_meta, analysis_end_str,
     *, neutral_band=0.25) -> dict`. Reuses `_macro_regression_from_arrays`,
     `_macro_covariance_block`, `_macro_factor_risk`, `_macro_factor_rc`,
     `_macro_policy_signal` from `src/stress_factors.py`. Implements per-regime
     gating (`insufficient_data`, `low_confidence`, `usable`, `reliable`) and
     populates `regimes`, `base_10y`, `axis_scores_latest`, `current_regime`,
     `regime_confidence`, `regime_transition_warning`, plus the new metadata.
   - `macro_two_axis_diagnostics(weights, tickers, analysis_end_str, *,
     factor_returns_monthly=None, neutral_band=0.25) -> dict`. Builds
     monthly portfolio + factor returns from existing helpers
     (`download_all`, `build_factor_matrix_monthly`) when `factor_returns_monthly`
     is None; otherwise reuses the supplied matrix. Calls `fetch_macro_indicators`
     for the panel, then `_from_frames` for the analytics.
   - `macro_regime_csv_frames(payload) -> dict[str, pd.DataFrame]`. Emits four
     existing filenames plus `macro_regime_indicator_panel.csv`.
3. Update `src/stress_factors.py`:
   - `MACRO_REGIME_METHOD_VERSION = "macro_two_axis_v1"`.
   - `MACRO_REGIME_METHOD_DISCLAIMER` updated to v1 wording.
   - Quality thresholds for monthly: `MACRO_REGIME_INSUFFICIENT_MAX_ROWS = 12`,
     `MACRO_REGIME_LOW_CONFIDENCE_MIN_ROWS = 12`,
     `MACRO_REGIME_USABLE_MIN_ROWS = 24`, `MACRO_REGIME_RELIABLE_MIN_ROWS = 60`.
   - `MACRO_REGIME_NAMES = ("goldilocks", "reflation", "stagflation",
     "recession_disinflation", "neutral_transition")`.
   - `_macro_quality_status` returns `insufficient_data` for `0 < n < 12`,
     `no_observations` for `n == 0`, `low_confidence` for `12 ≤ n < 24`,
     `usable` for `24 ≤ n < 60`, `reliable` for `n ≥ 60`.
   - Delete `_macro_axis_frame`. Re-export `macro_regime_diagnostics`,
     `macro_regime_diagnostics_from_frames`, `macro_regime_csv_frames` as thin shims
     over the new module so existing import sites and tests keep working.
4. Wire `run_optimization.py` and `run_report.py` import sites; no signature change.
5. Update `_append_macro_regime_section` to render block scores, coverage tier,
   missing/optional blocks, ECI ffill caveat, lag/no-vintage caveat, and
   `neutral_transition`.
6. Rewrite tests as listed in Progress.
7. Update documentation.

## Concrete Steps

Working directory: `c:\Users\ShumeikoYe\.cursor\worktrees\exp-pf-arch-v2-dc9c2cc6`.

After implementation, run focused tests:

    python -m pytest tests/test_macro_regimes.py tests/test_macro_indicators.py tests/test_macro_source_resolver.py tests/test_macro_neutral_band_sensitivity.py tests/test_portfolio_commentary.py -vv

Then broader factor/stress regression:

    python -m pytest tests/test_factor_beta_stability.py tests/test_factor_beta_kalman.py tests/test_factor_beta_adjusted_overlay.py tests/test_factor_variance_decomposition.py tests/test_factor_covariance.py tests/test_portfolio_pca.py tests/test_portfolio_commentary.py -vv

Then full suite:

    python -m pytest

End-to-end smoke (requires network for FRED / yfinance):

    python run_report.py --no-cache

## Validation and Acceptance

Acceptance is met when:

- Focused tests pass without network.
- `stress_report.json.macro_regime_diagnostics.axis_model.version == "macro_two_axis_v1"`.
- `axis_scores_latest` exposes `growth_score`, `inflation_score`,
  `growth_blocks`, `inflation_blocks`.
- `current_regime` is one of the five labels.
- `coverage_tier`, `available_blocks`, `missing_blocks`, `optional_blocks_missing`,
  `data_sources_used`, `score_lag_months: 1`, `look_ahead_caveat`,
  `score_start_date`, `regime_label_start_date` are present.
- `regimes.<label>.factor_regression.status == "insufficient_data"` whenever
  `n_obs < 12`.
- `results_csv/` contains `macro_regime_labels_monthly.csv`,
  `macro_regime_factor_betas.csv`, `macro_regime_factor_covariance.csv`,
  `macro_regime_factor_rc.csv`, `macro_regime_indicator_panel.csv`.
- `stress_commentary.txt` macro section includes `coverage_tier`,
  the lag/no-vintage caveat, and the ECI ffill caveat in English.

## Idempotence and Recovery

The implementation is additive in code structure; reruns overwrite generated CSV
and JSON artifacts in the standard output directories. No destructive operations.
Failures degrade to `coverage_tier="insufficient"` and an error field rather than
crashing the run.

## Artifacts and Notes

Focused tests (no network):

    python -m pytest tests/test_macro_indicators.py tests/test_macro_source_resolver.py \
                     tests/test_macro_regimes.py tests/test_macro_neutral_band_sensitivity.py \
                     tests/test_portfolio_commentary.py
    => 31 passed in 3.92s

Broader factor / stress regression (no network):

    python -m pytest tests/test_factor_beta_stability.py tests/test_factor_beta_kalman.py \
                     tests/test_factor_beta_adjusted_overlay.py \
                     tests/test_factor_variance_decomposition.py \
                     tests/test_factor_covariance.py tests/test_portfolio_pca.py
    => 38 passed in 6.20s

Full suite (no network):

    python -m pytest
    => 135 passed, 23 warnings in 25.95s
       (warnings are pre-existing pandas deprecation notices unrelated to
       this change)

End-to-end `python run_report.py --no-cache` was not executed in this iteration
(network-dependent FRED / yfinance fetch). The shim in
`src/stress_factors.py` keeps the import surface intact, so the call site in
`run_report.py` runs the new monthly pipeline without further edits.

## Interfaces and Dependencies

In `src/data_macro_sources.py`:

    @dataclass(frozen=True)
    class SourceSpec:
        kind: Literal["fred", "yahoo", "official_csv", "official_api", "keyed_api", "manual_csv"]
        locator: str
        requires_env: tuple[str, ...] = ()
        historical_only: bool = False

    @dataclass(frozen=True)
    class IndicatorSpec:
        key: str
        block: str
        axis: Literal["growth", "inflation"]
        role: Literal["required", "optional"]
        sign: Literal["+", "-"]
        frequency: Literal["M", "Q"]
        transform: str
        source_chain: tuple[SourceSpec, ...]

    def resolve_indicator(
        spec: IndicatorSpec, start: str, end: str
    ) -> tuple[pd.Series, dict[str, Any]]: ...

In `src/stress_factors_macro.py`:

    INDICATORS: tuple[IndicatorSpec, ...]

    def fetch_macro_indicators(start: str, end: str) -> tuple[pd.DataFrame, dict[str, Any]]: ...
    def compute_macro_scores(
        panel: pd.DataFrame, meta: dict[str, Any], *, neutral_band: float = 0.25
    ) -> pd.DataFrame: ...
    def macro_two_axis_diagnostics_from_frames(
        portfolio_returns_monthly: pd.Series,
        factor_returns_monthly: pd.DataFrame,
        indicator_panel: pd.DataFrame,
        indicator_meta: dict[str, Any],
        analysis_end_str: str,
        *,
        neutral_band: float = 0.25,
    ) -> dict[str, Any]: ...
    def macro_two_axis_diagnostics(
        weights: dict[str, float],
        tickers: list[str],
        analysis_end_str: str,
        *,
        factor_returns_monthly: pd.DataFrame | None = None,
        neutral_band: float = 0.25,
    ) -> dict[str, Any]: ...
    def macro_regime_csv_frames(payload: dict[str, Any]) -> dict[str, pd.DataFrame]: ...

`src/stress_factors.py` re-exports `macro_regime_diagnostics`,
`macro_regime_diagnostics_from_frames`, and `macro_regime_csv_frames` for
back-compat (call sites in `run_optimization.py` and `run_report.py` are unchanged).
