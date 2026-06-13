# Full Factor Matrix FRED Dependency Stabilization

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is intentionally focused: it stabilizes full Block 2.3 Factor Exposure and Stress Lab factor-matrix loading when FRED real-rate or related factor sources time out. It does not change Block 4/5, candidate generation, decision verdicts, optimizer logic, or the product boundary between full factor diagnostics and equity-only fallback diagnostics.

## Purpose / Big Picture

A portfolio-first full diagnosis needs the complete factor matrix behind Block 2.3 Factor Exposure and Stress Lab. Today a live FRED outage or long wait around `DFII10` real rates, `DTB3` risk-free, or related FRED factor sources can make a run hang or silently lose non-equity factors. After this work, FRED factor downloads have bounded timeout and retry behavior; approved cached factor data can keep the full factor matrix working with visible warnings; and missing or invalid cache fails clearly instead of pretending an equity-only calculation is a full factor result.

A user can see the change working by running the focused factor tests and the portfolio-first validation commands listed below. In the success-with-cache path, factor diagnostics metadata contains `factor_data_fallback_used: true`, a cache key, per-series provenance, and the warning `FRED factor source timed out; using approved cached factor data.`

## Progress

- [x] (2026-06-05) Audited `build_factor_matrix` call sites, required FRED series, existing risk-free cache behavior, and missing factor-cache boundary.
- [x] (2026-06-05) Added bounded FRED CSV timeout/retry behavior in `src/data_fred.py`.
- [x] (2026-06-05) Added approved raw FRED factor-series cache fallback in `src/stress_factors.py` with metadata warnings and explicit failure when cache is absent or invalid.
- [x] (2026-06-05) Added focused regression tests for cached real-rate fallback, no-cache failure, invalid cache policy, partial cache behavior, and bounded retry attempts.
- [x] (2026-06-05) Ran the full requested verification matrix and recorded final results in `Outcomes & Retrospective`.

## Surprises & Discoveries

- Observation: The existing approved fallback is only for monthly risk-free data in `src/data_loader.py`; it scans `cache/monthly/v_*/rf_monthly.parquet` and checks `rf_source`, currency, return frequency, and analysis-end coverage.
  Evidence: `tests/test_data_cache_key.py` already covers `fred_timeout_cached_rf`, but `src/stress_factors.py` had no equivalent factor-series cache for `real_rates_weekly`.

- Observation: `build_factor_matrix` is the common weekly matrix constructor for full factor diagnostics. It is called by `run_report.py`, the legacy policy optimization runner under `legacy/runners/`, `src/candidate_run_context.py`, and several internal analytics helpers in `src/stress_factors.py`.
  Evidence: `rg -n "build_factor_matrix\(" --glob "*.py" .` lists those call sites plus unit tests.

- Observation: The full matrix FRED dependency is broader than `DTB3`. `DTB3` is risk-free, while the factor matrix needs `SP500`, `DFII10`, `T10YIE`, `BAMLH0A0HYM2`, optional credit fallback `BAA10Y`, `DTWEXBGS`, `VIXCLS`, `WEI`, and `DCOILWTICO`.
  Evidence: constants in `src/stress_factors.py` define the full FRED-backed factor registry.

## Decision Log

- Decision: Keep factor-cache fallback separate from the existing monthly risk-free fallback.
  Rationale: `DTB3` risk-free data is used for return metrics and MAR alignment, while `DFII10` and other FRED series are raw inputs to the full factor matrix. Mixing them would blur provenance and approval rules.
  Date/Author: 2026-06-05 / Codex

- Decision: Approve cache at the raw FRED series layer, not as an equity-only fallback or already-regressed beta fallback.
  Rationale: This preserves the full factor matrix contract and lets the existing weekly/monthly transforms continue to define factor columns.
  Date/Author: 2026-06-05 / Codex

- Decision: Partial cache is not a fake successful full calculation. Each required FRED-backed factor must either fetch live or independently pass cache approval; otherwise the run fails with the missing series named.
  Rationale: This prevents a cached `DFII10` series from masking a missing `T10YIE`, `WEI`, or other factor and avoids silently degrading Block 2.3 / Stress Lab to equity-only.
  Date/Author: 2026-06-05 / Codex

## Outcomes & Retrospective

Implementation outcome: the factor loading layer now has bounded FRED fetches and an approved cached factor-series fallback with visible metadata. Verification completed on 2026-06-05:

    python -m pytest tests/test_factor_matrix_builders.py -q
    11 passed

    python -m pytest tests/test_data_cache_key.py tests/test_factor_diagnostics_wiring.py tests/test_product_bundle_integration.py -q
    10 passed

    python -m pytest tests/test_stress_*.py tests/test_hedge_gap*.py -q
    241 passed

    python scripts/verify_docs.py
    docs verification: OK

    python scripts/validate_block_4_live.py --refresh-diagnosis
    Block 4 v3 live validation: OK

    python scripts/verify_live_core_e2e.py --profile diagnosis_only
    live core E2E validation: OK

The requested behavior is complete: cached factor data can preserve full factor-matrix calculations with warnings, while absent or invalid cache fails explicitly instead of fabricating success.

## Context and Orientation

`src/data_fred.py` fetches FRED time series. Before this plan, its CSV fallback used a 60-second URL timeout and `pandas_datareader` could still be attempted without a project-controlled timeout. This is risky when live FRED or local networking stalls.

`src/stress_factors.py` builds the full factor matrix. The main function is `build_factor_matrix(start, end, require_complete_rows=True)`, which delegates to `_build_factor_frame`. Factor columns include equity, real rates, inflation, credit, USD, commodity, VIX, US growth, and oil. The real-rate column `real_rates` comes from FRED `DFII10` through `fetch_real_rates_weekly`; this is separate from risk-free `DTB3` used by return metrics.

Existing cache directories under `cache/daily` and `cache/monthly` hold market data panels and `rf_monthly.parquet`. They do not represent approved full factor-series cache. The new factor cache lives under `cache/factors/v_<series_id>/` and contains raw FRED observations plus metadata.

## Plan of Work

In `src/data_fred.py`, keep `fetch_fred_series(series_id, start, end, ...)` as the public function but make its normal path use the public FRED CSV endpoint with explicit `timeout`, `retries`, and `retry_sleep` parameters. Default timeout is 10 seconds and default retry count is 2. If bounded CSV attempts time out, raise a clear RuntimeError instead of falling through to an unbounded path.

In `src/stress_factors.py`, add raw factor-series cache helpers. A successful live FRED factor fetch writes `cache/factors/v_<series_id>/series.parquet` and `meta.json`. A timeout-shaped FRED failure for a factor series attempts to load that series from approved cache. The approved cache policy is:

- `max_cache_age_days`: 7 calendar days by default.
- Required series coverage: every FRED-backed full-matrix series must be fetched live or have an approved cache entry; credit may use `BAA10Y` only under the existing HY OAS insufficient-coverage rule.
- Minimum date range: cached raw observations must cover the requested `start` and `end` dates.
- Required frequency alignment: metadata must declare support for `daily_raw`, `weekly_w_fri`, and `monthly_end` reconstruction because the same raw series feeds daily, weekly, and monthly factor helpers.
- Partial cache behavior: if only some series are cached, missing series must fetch live successfully; otherwise the run fails clearly with the timed-out series named.

When cached factor data is used, attach this metadata to `factor_load_diagnostics`: `factor_data_fallback_used`, `factor_data_fallback_reason: fred_timeout_cached_factor_data`, `factor_data_source_used: approved_cached_factor_series`, `factor_data_cache_key`, per-factor provenance, `warnings`, and `cache_validity_policy`.

Do not add an equity-only replacement to `build_factor_matrix`. Equity-only fallback remains limited to existing diagnostics that explicitly use cached equity proxy when the matrix is unavailable; it must not be reported as a full factor-matrix success.

## Concrete Steps

From repository root `D:\Desktop\CURSOR TULA DIAGNOSTICS`:

1. Inspect factor loading and cache behavior:

    rg -n "build_factor_matrix|real_rates_weekly|DTB3|FRED|risk....free|factor_matrix" -S .
    rg -n "fetch_fred_series\(" src tests -S

2. Implement bounded FRED fetches in `src/data_fred.py`.

3. Implement factor cache approval and metadata in `src/stress_factors.py`.

4. Add or update tests in `tests/test_factor_matrix_builders.py` and adjacent cache tests.

5. Update data documentation and changelog.

## Validation and Acceptance

Focused tests must prove these behaviors:

- FRED `DFII10` timeout plus valid factor cache builds the full factor matrix and records warning/provenance.
- FRED timeout plus no valid factor cache raises a clear `FactorDataUnavailableError`; it does not fabricate a full calculation.
- Expired cache, insufficient date coverage, bad frequency alignment metadata, and partial cache all fail clearly unless the missing series fetch live successfully.
- Block 2.3 / Stress Lab full matrix path does not degrade to equity-only.
- Timeout/retry attempts are bounded.

Run:

    python -m pytest tests/test_data_cache_key.py tests/test_factor_diagnostics_wiring.py tests/test_product_bundle_integration.py -q
    python -m pytest tests/test_stress_*.py tests/test_hedge_gap*.py -q
    python scripts/verify_docs.py
    python scripts/validate_block_4_live.py --refresh-diagnosis
    python scripts/verify_live_core_e2e.py --profile diagnosis_only

Also run the focused factor builder tests while developing:

    python -m pytest tests/test_factor_matrix_builders.py -q

## Idempotence and Recovery

The cache writer is additive and safe to rerun. It overwrites the per-series factor cache for the same FRED series with the latest successful live data. If a bad cache is written during development, delete only the affected `cache/factors/v_<series_id>/` directory and rerun with live FRED available. Do not delete portfolio monthly/daily cache unless the task explicitly requires a broader cache reset.

If live validation commands fail because FRED or market data providers are unavailable, keep the failure explicit in the final report. Do not mark a run successful by substituting equity-only diagnostics for the full factor matrix.

## Artifacts and Notes

Expected metadata excerpt when cached factor data is used:

    "factor_data_fallback_used": true,
    "factor_data_fallback_reason": "fred_timeout_cached_factor_data",
    "factor_data_source_used": "approved_cached_factor_series",
    "warnings": [
      "factor_data_fallback_used:fred_timeout_cached_factor_data",
      "FRED factor source timed out; using approved cached factor data."
    ]

Expected failure wording when no approved cache exists:

    FRED factor fetch timed out for FRED:DFII10; no valid approved factor cache was available.

## Interfaces and Dependencies

Public interfaces preserved:

- `src.data_fred.fetch_fred_series(series_id, start, end, api_key=None, *, timeout=10.0, retries=2, retry_sleep=0.5) -> pandas.Series`
- `src.stress_factors.build_factor_matrix(start, end, *, require_complete_rows=True) -> pandas.DataFrame`

New internal support:

- `src.stress_factors.FactorDataUnavailableError`
- `src.stress_factors.factor_cache_validity_policy() -> dict`
- factor cache files under `cache/factors/v_<series_id>/series.parquet` and `meta.json`
