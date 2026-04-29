# Factor beta stability diagnostics

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root.

## Purpose / Big Picture

After this change, the stress report will not only show rolling factor betas, but will also state whether those betas are stable enough to interpret. The user can see this in `stress_report.json`, the generated stress commentary, and CSV diagnostics. The feature is diagnostic only: it does not alter portfolio weights, optimization, mandate checks, or stress pass/fail status.

## Progress

- [x] (2026-04-29 00:00+02:00) Read `PLANS.md`, inspected existing rolling beta code in `src/stress_factors.py`, `run_report.py`, and `src/portfolio_commentary.py`.
- [x] (2026-04-29 00:00+02:00) Confirmed product decisions: weekly+monthly diagnostics, OOS next 1Y holdout, fixed conservative thresholds, diagnostic-only output.
- [x] (2026-04-29 00:25+02:00) Implemented monthly rolling beta helpers and stability/OOS diagnostics.
- [x] (2026-04-29 00:25+02:00) Wired diagnostics into `run_report.py` outputs and commentary.
- [x] (2026-04-29 00:25+02:00) Added focused tests and updated documentation.
- [x] (2026-04-29 00:25+02:00) Ran focused pytest command; 14 tests passed.
- [x] (2026-04-29 00:35+02:00) Ran broader factor-suite pytest command; 22 tests passed.

## Surprises & Discoveries

- Observation: Weekly rolling beta output already exists for 3Y/5Y/10Y and is persisted as CSV/PNG/HTML.
  Evidence: `run_report.py` writes `factor_betas_rolling_windows_weeks`, `factor_betas_rolling_summary`, and rolling artifacts.
- Observation: Monthly factor matrix support already exists but is not wired into rolling stability.
  Evidence: `src/stress_factors.py` contains `build_factor_matrix_monthly` and `estimate_betas_monthly`.

## Decision Log

- Decision: Keep all new stability diagnostics non-binding.
  Rationale: User explicitly requested no impact on weights or optimization.
  Date/Author: 2026-04-29 / Codex
- Decision: Use next 1Y OOS holdout for rolling-forward stability.
  Rationale: User selected this option; it provides enough observations for both weekly and monthly checks.
  Date/Author: 2026-04-29 / Codex
- Decision: Keep thresholds fixed in code and documentation for this version.
  Rationale: User requested conservative defaults without config surface.
  Date/Author: 2026-04-29 / Codex

## Outcomes & Retrospective

Implementation now produces `factor_betas_stability` with sign, magnitude, specification, and OOS stability diagnostics, plus severity distribution warnings. Focused tests and the broader factor-suite validation passed.

## Context and Orientation

Factor betas are estimated in `src/stress_factors.py`. Weekly rolling beta diagnostics currently use `compute_portfolio_rolling_factor_betas_weekly` and `rolling_beta_summary`, then `run_report.py` stores their output in `stress_report.json`. Stress commentary is generated in `src/portfolio_commentary.py`.

The new feature adds a diagnostic layer on top of rolling beta series. "Sign stability" means whether beta keeps the same positive or negative direction. "Magnitude stability" means whether beta estimates have limited spread. "Specification sensitivity" means whether estimates remain consistent when changing window length and data frequency. "OOS stability" means estimating beta on a rolling window and comparing it with beta estimated over the next one-year holdout period.

## Plan of Work

In `src/stress_factors.py`, add monthly rolling beta computation from existing monthly returns and monthly factor matrix. Add generic stability helpers that accept weekly and monthly rolling beta frames and produce `factor_betas_stability`. Add OOS rolling-forward helpers that compute in-sample beta over 3Y/5Y/10Y windows and OOS beta over the next 1Y holdout.

In `run_report.py`, compute weekly and monthly rolling beta frames, summaries, OOS diagnostics, and stability diagnostics. Persist monthly rolling CSV files and `factor_beta_stability.csv`. Add the new JSON fields while preserving the existing weekly fields.

In `src/portfolio_commentary.py`, append a concise stability section with per-factor severity, sign share, magnitude band, specification sensitivity, OOS sign match/degradation, severity distribution, and any threshold warning.

Update docs and tests to cover the new contract.

## Concrete Steps

Run commands from the repository root:

    C:\Users\ShumeikoYe\OneDrive\Рабочий стол\Курсор Модель Блекрока 2

After implementation, run:

    python -m pytest tests\test_factor_beta_stability.py tests\test_factor_matrix_builders.py tests\test_portfolio_commentary.py -vv

Then run the broader factor suite:

    python -m pytest tests\test_factor_matrix_builders.py tests\test_factor_multicollinearity.py tests\test_factor_oos_explainability.py tests\test_factor_regression_hac.py tests\test_factor_regression_heteroskedasticity.py tests\test_factor_regression_serial.py tests\test_portfolio_commentary.py tests\test_factor_beta_stability.py -vv

If `python` is not on PATH, use the bundled Python executable reported by `load_workspace_dependencies`.

## Validation and Acceptance

Acceptance requires `stress_report.json` to contain `factor_betas_stability` with `by_beta`, `thresholds`, `severity_distribution`, `severity_distribution_warning`, and `overall_severity`. Existing weekly rolling fields must remain unchanged. Tests must prove stable betas produce low severity, sign flips produce high sign severity, wide beta ranges produce magnitude severity, weekly/monthly sign disagreement produces specification severity, OOS sign mismatch/degradation affects combined severity, and severity distribution warnings fire at the requested shares.

## Idempotence and Recovery

The implementation is additive. Re-running report generation should overwrite generated CSV/JSON artifacts deterministically. If a diagnostic cannot be computed due to insufficient data, it should return empty structures or `unknown` severity rather than fail the report run.

## Artifacts and Notes

Important generated artifacts after a successful report run:

    stress_report.json
    rolling_factor_betas_monthly_3y.csv
    rolling_factor_betas_monthly_5y.csv
    rolling_factor_betas_monthly_10y.csv
    factor_beta_stability.csv

## Interfaces and Dependencies

No new third-party dependency is required. Use pandas and numpy, already present in the project.

New or updated public helper functions in `src/stress_factors.py`:

    compute_portfolio_rolling_factor_betas_monthly(...)
    factor_beta_oos_stability_diagnostics(...)
    factor_beta_stability_diagnostics(...)

These helpers must return plain dictionaries and pandas DataFrames suitable for JSON export and CSV persistence.

Revision note 2026-04-29 / Codex: Updated progress after implementation, focused tests, and broader factor-suite validation. The remaining work is final review of changed files and stale-reference checks.
