# Regime-level daily portfolio metrics v1 (`regime_portfolio_metrics_v1`)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

Repository planning rules live in `PLANS.md` at the repo root; this document must be maintained in accordance with `PLANS.md`.

## Purpose / Big Picture

After this change, a full `run_report.py` (with daily regime factor analytics enabled) produces **per-primary-regime daily portfolio and asset diagnostics** in `stress_report.json` under `regime_portfolio_metrics`, plus `regime_portfolio_metrics_summary.json` and CSV exports under `results_csv/`. Consumers can compare CAGR, volatility, Sharpe, Sortino, beta, Treynor, drawdown, VaR/ES (when sample length allows), Ledoit–Wolf covariance, and RC_vol **inside** each macro quadrant without touching the optimizer or stress gates.

Verify by running `python -m pytest tests/test_regime_portfolio_metrics.py` (all pass) and inspecting `stress_report.json` after a report run when daily data is available.

## Progress

- [x] (2026-05-08) Add `src/metrics_daily.py` (daily CAGR, vol, Sharpe, Sortino, beta, Treynor, skew/kurt on log returns, MDD, TTR in trading days; 252-day annualization; Sharpe denominator uses raw returns).
- [x] (2026-05-08) Add `src/regime_portfolio_metrics.py` (per-regime slices, quality via `regime_factor_quality_daily`, portfolio + asset packs with `metric_available`, LW covariance, RC_vol, VaR/ES with `n_obs_days >= 60`, slim `factor_analytics` from existing `regime_factor_analytics` payload).
- [x] (2026-05-08) Wire in `run_report.py` after daily `regime_factor_analytics`; slim JSON; summary + CSV export; `regime_portfolio_metrics_error` on failure.
- [x] (2026-05-08) Add `tests/test_regime_portfolio_metrics.py`.
- [x] (2026-05-08) Update `docs/specs/stress_testing_spec.md` §8.8.4, `AGENTS.md`, `SPEC.md`.

## Surprises & Discoveries

- Observation: Forward-fill-only monthly `rf` left leading trading days as NaN before the first month-end print; tests expect a finite rate on those days.
  Evidence: `test_expand_rf_monthly_ffill_to_daily` failure until `expand_rf_monthly_to_daily` applied `bfill()` after `reindex(..., method="ffill")`, documented as earliest published rate without look-ahead.

- Observation: VaR/ES at `n=30` with `insufficient_data` quality was inconsistent if the VAR floor was only 20 days.
  Evidence: Raised `VAR_ES_MIN_OBS` to `60` to align with daily regime quality `REGIME_DAILY_INSUFFICIENT_MAX` and documented in stress spec §8.8.4.

## Decision Log

- Decision: Use `bfill()` after monthly rf forward-fill to daily index.
  Rationale: Stabilizes early-window excess-return metrics and matches test and practical backtest “first known” rate convention without peeking at future month-ends.
  Date/Author: 2026-05-08 / implementation agent.

- Decision: Set historical VaR/ES minimum observations to 60 trading days.
  Rationale: Same floor as `insufficient_data` in daily regime analytics; avoids reporting tail risk estimates on slices flagged low quality.
  Date/Author: 2026-05-08 / implementation agent.

- Decision: Embed slim `factor_analytics` from the existing `regime_factor_analytics` payload instead of recomputing OLS when the payload is passed.
  Rationale: Saves CPU and guarantees consistency with the daily factor block.
  Date/Author: 2026-05-08 / plan / implementation agent.

## Outcomes & Retrospective

Delivered `regime_portfolio_metrics_v1`: contract in stress spec §8.8.4, implementation in `src/regime_portfolio_metrics.py` and `src/metrics_daily.py`, integration and artifacts from `run_report.py`, focused tests passing. Remaining optional work (out of scope unless requested): surface summaries in client PDFs or `stress_commentary.txt`; mirror block in `--no-report` optimization-only paths if product requires `stress_report` parity without full report.

## Context and Orientation

The repo is a Python portfolio optimizer and reporting system. Main report entry: `run_report.py`. Monthly metrics live in `src/metrics_asset.py` and `src/metrics_portfolio.py`; stress JSON is assembled in the report path. Macro regimes come from `macro_regime_diagnostics` (`macro_two_axis_v1` in `src/stress_factors_macro.py`). Daily regime factor statistics are built in `src/regime_factor_analytics.py`. The new block adds **portfolio-level** daily analytics sliced by the same primary regime labels, reusing Ledoit–Wolf helpers and optional factor summaries.

**Primary regime** means one of: `goldilocks`, `reflation`, `stagflation`, `recession_disinflation`.

## Plan of Work

Implemented as designed: extract daily metric helpers; orchestrate per-regime complete-case portfolio returns with renormalized weights; compute covariance and RC; attach VaR/ES when `n_obs_days >= 60`; merge slim factor block; export summary and CSV; document in stress spec and agent index.

## Concrete Steps

From repository root (Windows PowerShell example):

    Set-Location <repo-root>
    python -m pytest tests/test_regime_portfolio_metrics.py -q

Expect: `6 passed`.

For a full regression when changing shared helpers:

    python -m pytest -q

## Validation and Acceptance

- `tests/test_regime_portfolio_metrics.py` passes (rf expansion, regime filter, annualization sanity, LW/RC metadata, VaR gated below 60 days, all four regime keys present).
- `stress_report.json` contains `regime_portfolio_metrics.version = regime_portfolio_metrics_v1` when daily pipeline succeeds; on failure `regime_portfolio_metrics_error` is set.
- Variant folder contains `regime_portfolio_metrics_summary.json` after a successful full report with daily regime analytics.

## Idempotence and Recovery

Re-running `run_report.py` overwrites `regime_portfolio_metrics*` artifacts idempotently. If the block errors, previous `stress_report` keys may be absent or stale; fix the error and rerun the report.

## Artifacts and Notes

Key modules:

- `src/metrics_daily.py`
- `src/regime_portfolio_metrics.py`
- `run_report.py` (daily branch)

Constants of note: `VAR_ES_MIN_OBS = 60` in `regime_portfolio_metrics.py`; daily quality buckets shared via `regime_factor_quality_daily` in `regime_factor_analytics.py`.

## Interfaces and Dependencies

- Public: `expand_rf_monthly_to_daily`, `build_regime_portfolio_metrics`, `regime_portfolio_metrics_for_stress_report`, `regime_portfolio_metrics_summary`, `regime_portfolio_metrics_csv_frames` from `src/regime_portfolio_metrics.py`.
- Dependencies: `pandas`, `numpy`, `src.regime_factor_analytics._covariance_with_ledoit_wolf`, `src.portfolio_analytics.var_historical` / `es_historical`, `src.risk_contrib.percentage_contributions_variance`, `src.metrics_daily` helpers.

---

Revision note (2026-05-08): Initial ExecPlan filed after implementation; sections record delivery state and key decisions (rf bfill, VaR floor 60).
