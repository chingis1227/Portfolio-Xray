# Kalman factor beta diagnostics

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root.

## Purpose / Big Picture

The project already reports fixed-window and rolling factor betas, but those estimates can jump
when the window changes or when a noisy recent observation enters the sample. This change adds a
diagnostic-only Kalman-filter estimate of current portfolio factor betas. A Kalman filter treats
each beta as a hidden state that changes gradually through time, then updates that state as each
new weekly portfolio return and factor row arrives. After implementation, `stress_report.json`
contains `factor_betas_kalman`, and `results_csv/` contains `kalman_factor_betas_weekly.csv` plus
`kalman_factor_betas_latest.csv`.

## Progress

- [x] (2026-04-29 00:00+02:00) Read `PLANS.md` and inspected existing factor beta, rolling beta, stress report, and commentary paths.
- [x] (2026-04-29 00:20+02:00) Designed V1 as diagnostic-only so it cannot change optimizer weights, mandate gates, or primary OLS beta fields.
- [x] (2026-04-29 00:45+02:00) Implemented Kalman helpers, stress report attachment, report integrations, commentary, tests, and documentation updates.
- [x] (2026-04-29 01:10+02:00) Ran focused Kalman tests, adjacent factor tests, commentary tests, syntax checks, and full pytest suite.

## Surprises & Discoveries

- Observation: The repository already has `_portfolio_factor_weekly_ols_rows`, which prepares aligned weekly portfolio returns and factor rows.
  Evidence: `portfolio_factor_regression_weekly` uses that helper for the same weekly OLS rows reported in `stress_report.json`.
- Observation: Existing factor diagnostics are documented as non-binding.
  Evidence: `docs/docs/stress_testing_spec.md` says rolling beta stability does not affect weights, optimization, mandate status, or stress pass/fail.

## Decision Log

- Decision: Implement Kalman betas without adding `pykalman`, `filterpy`, or another dependency.
  Rationale: `numpy` is already available and the needed random-walk state update is compact and testable.
  Date/Author: 2026-04-29 / Codex.
- Decision: Keep V1 diagnostic-only.
  Rationale: The current optimizer does not use factor betas as binding inputs, and changing weight construction would require a separate policy change.
  Date/Author: 2026-04-29 / Codex.
- Decision: Report capped betas with `|beta| <= 3.0`, while preserving raw latest filtered values.
  Rationale: Capping prevents noisy state updates from producing unrealistic dashboard/report values while retaining auditability.
  Date/Author: 2026-04-29 / Codex.
- Decision: Flag Kalman-vs-5Y divergence on sign difference, absolute gap at least `0.25`, or relative gap at least `0.75`.
  Rationale: This captures both clear sign changes and material size changes, including small-denominator cases.
  Date/Author: 2026-04-29 / Codex.
- Decision: Classify state uncertainty from posterior standard deviation as low at `<=0.15`, moderate at `<=0.35`, and high above that.
  Rationale: The thresholds are simple, visible, and suitable for first-pass diagnostic triage.
  Date/Author: 2026-04-29 / Codex.

## Outcomes & Retrospective

Implemented. The result is an additive `factor_betas_kalman` diagnostic block with CSV artifacts
and commentary. Focused tests and the full test suite passed. The implementation stayed
diagnostic-only and preserved existing raw OLS beta contracts.

## Context and Orientation

Factor analytics live primarily in `src/stress_factors.py`. `run_report.py` and
`run_optimization.py` build `stress_report.json` by computing raw 5Y and 10Y factor betas, rolling
beta stability, adjusted beta overlays, factor covariance, factor variance decomposition, and PCA.
`src/portfolio_commentary.py` converts the JSON fields into human-readable commentary.

The new Kalman path reuses the existing weekly factor data. The state is an intercept plus one beta
per factor. The observation equation is `portfolio_return_t = intercept_t + factor_row_t * beta_t
+ noise`. The transition equation is a random walk: the previous state is the best prediction for
the next state until a new observation arrives.

## Plan of Work

Add constants for Kalman beta capping, divergence thresholds, uncertainty thresholds, and minimum
observations to `src/stress_factors.py`. Add a core helper that accepts aligned weekly portfolio
returns and factor returns, initializes the state from OLS, runs the Kalman update row by row, caps
reported betas, computes divergence vs 5Y, and returns a JSON-ready report plus CSV-ready frames.

Add a portfolio wrapper that reuses `_portfolio_factor_weekly_ols_rows`, then add an attachment
helper that writes `factor_betas_kalman` into an existing stress report and exports CSV artifacts.
Call this attachment helper from both `run_report.py` and `run_optimization.py`.

Add commentary rendering that lists latest capped Kalman betas, capped values, Kalman-vs-5Y
divergence flags, high uncertainty betas, and the non-binding caveat.

Update the stress testing spec, project rules, README, and SPEC. Check `AGENTS.md`; edit it only if
the agent workflow or rules need to change.

## Concrete Steps

From the repository root, edit the files described above. Then run:

    python -m pytest tests/test_factor_beta_kalman.py -vv
    python -m pytest tests/test_factor_beta_stability.py tests/test_factor_beta_adjusted_overlay.py tests/test_factor_matrix_builders.py -vv
    python -m pytest

If the full suite is too slow or blocked by environment-specific data access, record the focused
test results and the blocker explicitly.

## Validation and Acceptance

Acceptance requires `stress_report.json.factor_betas_kalman` to appear when weekly factor rows are
available. It must contain latest capped betas, raw latest betas, cap diagnostics, Kalman-vs-5Y
divergence diagnostics, posterior state uncertainty, uncertainty classes, and comparison fields.
The existing `factor_betas`, `factor_betas_5y`, and `factor_betas_10y` fields must remain unchanged.

The focused tests must prove that constant betas are tracked, step changes are followed smoothly,
excessive raw beta values are capped, divergence rules fire, uncertainty thresholds map to the
expected classes, missing rows are aligned safely, insufficient data returns unavailable diagnostics,
and the attachment helper writes CSV artifacts without mutating raw OLS fields.

## Idempotence and Recovery

The implementation is additive. Re-running report or optimization overwrites the same Kalman CSV
files in `results_csv/`, matching existing artifact behavior. If Kalman calculation fails, the
stress report records `factor_betas_kalman_error` or an unavailable diagnostic block while existing
stress analytics continue.

## Artifacts and Notes

Expected new output files:

    results_csv/kalman_factor_betas_weekly.csv
    results_csv/kalman_factor_betas_latest.csv

Expected new JSON field:

    stress_report.json.factor_betas_kalman

## Interfaces and Dependencies

No new dependency is added. The implementation uses `numpy` and `pandas`.

`src.stress_factors.kalman_factor_betas_from_frames(...)` returns a tuple of:
report dictionary, date-indexed capped beta history DataFrame, and latest comparison DataFrame.

`src.stress_factors.compute_portfolio_kalman_factor_betas_weekly(...)` builds weekly aligned
portfolio/factor rows from existing project helpers and returns the same tuple.

`src.stress_factors.attach_kalman_factor_betas_to_stress_report(...)` mutates the supplied stress
report only by adding `factor_betas_kalman` and optional artifact names inside that block.
