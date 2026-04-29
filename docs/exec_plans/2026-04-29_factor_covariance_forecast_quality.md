# Factor covariance forecast quality

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root.

## Purpose / Big Picture

The portfolio report already shows factor covariance regimes and stability, but it does not answer whether a historical factor covariance matrix would have predicted future realized risk. After this change, `stress_report.json.factor_covariance.forecast_quality`, `results_csv/factor_covariance_forecast_quality.csv`, and `stress_commentary.txt` will show a diagnostic-only out-of-sample backtest. The backtest estimates a 5Y weekly factor covariance matrix at each cutoff and compares the model-implied portfolio factor volatility against realized factor volatility over the next 1Y weekly holdout.

## Progress

- [x] (2026-04-29) Read `PLANS.md` and the existing factor covariance/reporting code paths.
- [x] (2026-04-29) User selected 1Y weekly holdout as the primary horizon.
- [x] (2026-04-29) Implemented the forecast-quality helper and wired it into `factor_covariance_analytics`.
- [x] (2026-04-29) Exported `factor_covariance_forecast_quality.csv` from `run_report.py`.
- [x] (2026-04-29) Added stress commentary output for forecast-quality summary.
- [x] (2026-04-29) Updated project documentation and specs.
- [x] (2026-04-29) Added focused no-network tests and ran focused/adjacent pytest commands.

## Surprises & Discoveries

- Observation: Existing `factor_covariance_analytics` already owns ordered weekly factor returns, portfolio beta exposure vector, covariance matrices, and CSV export wiring.
  Evidence: `src/stress_factors.py` contains `_ordered_factor_frame`, `_factor_covariance_matrix`, `_correlation_from_covariance`, `_exposure_vector`, and `factor_covariance_analytics`; `run_report.py` exports factor covariance matrices and stability CSVs.

- Observation: The first forecast-quality test can prove the model-risk formula without network access by using a deterministic factor fixture and checking the first 260-week training covariance directly.
  Evidence: `tests/test_factor_covariance.py::test_factor_covariance_forecast_quality_uses_5y_train_and_1y_holdout` passed in the focused pytest run.

## Decision Log

- Decision: Implement the new metric under `stress_report.json.factor_covariance.forecast_quality`.
  Rationale: The metric evaluates the same factor covariance object and should remain grouped with regime covariance analytics.
  Date/Author: 2026-04-29 / Codex

- Decision: Use a non-overlapping 260-week train, 52-week holdout, and 52-week step schedule.
  Rationale: This matches the user-approved 1Y weekly forecast horizon and produces easy-to-read annual OOS checks.
  Date/Author: 2026-04-29 / Codex

- Decision: Keep all quantities weekly-scale and diagnostic-only.
  Rationale: Existing factor covariance analytics are weekly and non-binding; annualization would add an unnecessary convention to v1.
  Date/Author: 2026-04-29 / Codex

## Outcomes & Retrospective

Implemented. `stress_report.json.factor_covariance.forecast_quality` now reports a diagnostic-only 260-week covariance forecast versus next-52-week realized factor-risk backtest, `run_report.py` exports `results_csv/factor_covariance_forecast_quality.csv`, and `stress_commentary.txt` summarizes the key forecast-quality metrics. Focused validation passed with 8 tests, and adjacent factor diagnostics passed with 20 tests.

## Context and Orientation

`src/stress_factors.py` owns factor data construction, factor beta estimation, rolling beta diagnostics, factor covariance analytics, and factor variance decomposition. `run_report.py` calls these helpers, stores outputs in `stress_report`, and exports CSV artifacts under `results_csv/`. `src/portfolio_commentary.py` writes `stress_commentary.txt` from the final stress report. The source-of-truth behavior for stress/factor diagnostics is documented in `docs/docs/stress_testing_spec.md`, while `README.md`, `SPEC.md`, and `PROJECT_RULES.md` summarize user-facing and project-wide contracts.

In this plan, "forecast covariance" means the sample covariance matrix of weekly factor returns estimated from the prior 260 weekly rows. "Realized risk" means the sample standard deviation of the weekly factor portfolio return series `X_holdout @ beta_vector` over the next 52 weekly rows. The beta vector is the current reported 5Y portfolio factor beta vector passed into `factor_covariance_analytics`; this isolates covariance forecast quality from beta forecast quality.

## Plan of Work

Add constants for forecast-quality train, holdout, and step windows near existing factor covariance constants in `src/stress_factors.py`. Add a helper that accepts ordered factor returns and the exposure vector, walks non-overlapping 260/52/52 windows, computes forecast covariance, realized covariance, model and realized factor volatility, relative volatility errors, correlation RMSE, covariance relative Frobenius error, and the worst correlation error pair. Return an unavailable object when fewer than 312 weekly rows exist or no valid OOS rows can be built.

Wire the helper into `factor_covariance_analytics` after `beta_vec` is built. Add the returned object as `forecast_quality` in the factor covariance payload. In `run_report.py`, export `forecast_quality.rows` to `results_csv/factor_covariance_forecast_quality.csv` when rows exist.

Update `src/portfolio_commentary.py` so the factor covariance section prints a compact "Forecast quality" summary: number of forecasts, median absolute volatility error, 10/20/30 percent hit rates, median correlation RMSE, and severity. Update `docs/docs/stress_testing_spec.md`, `SPEC.md`, `README.md`, and `PROJECT_RULES.md` to describe the new diagnostic-only contract and confirm it does not change weights or status.

Add no-network tests in `tests/test_factor_covariance.py` for the output contract, window settings, model volatility formula, and regime-shift severity. Update `tests/test_portfolio_commentary.py` with fixture data and assertions for the new commentary text.

## Concrete Steps

From the repository root, edit only source, tests, documentation, and this ExecPlan. Run:

    python -m pytest tests/test_factor_covariance.py tests/test_portfolio_commentary.py -vv

Then run the adjacent factor diagnostics if feasible:

    python -m pytest tests/test_factor_matrix_builders.py tests/test_factor_beta_stability.py tests/test_factor_covariance.py tests/test_portfolio_commentary.py -vv

## Validation and Acceptance

Acceptance requires `stress_report.json.factor_covariance.forecast_quality` to exist whenever factor covariance analytics can run. With enough factor history, it must report `status = "available"`, `method = "rolling_5y_covariance_vs_next_1y_realized_factor_risk"`, `train_weeks = 260`, `holdout_weeks = 52`, `step_weeks = 52`, weekly-scale model and realized risk rows, and a populated summary. When history is insufficient, it must report `status = "unavailable"` and `reason = "insufficient_factor_history"`.

The new tests should fail before implementation because `forecast_quality` does not exist, and pass after implementation. The focused pytest command should pass with the new commentary assertion.

## Idempotence and Recovery

All changes are additive and can be rerun safely. The CSV export overwrites the same generated artifact during report generation, matching existing report behavior. If tests fail, inspect the specific assertion, adjust only the affected helper/export/commentary path, and rerun the focused command.

## Artifacts and Notes

Expected new generated artifact:

    results_csv/factor_covariance_forecast_quality.csv

Expected report JSON path:

    stress_report.json.factor_covariance.forecast_quality

Validation transcript:

    python -m pytest tests/test_factor_covariance.py tests/test_portfolio_commentary.py -vv
    8 passed in 13.57s

    python -m pytest tests/test_factor_matrix_builders.py tests/test_factor_beta_stability.py tests/test_factor_covariance.py tests/test_portfolio_commentary.py -vv
    20 passed in 7.55s

## Interfaces and Dependencies

Use only existing dependencies: `numpy`, `pandas`, and existing helpers in `src.stress_factors`. Add no network calls. The helper should be internal to `src/stress_factors.py` and should not require config changes.
