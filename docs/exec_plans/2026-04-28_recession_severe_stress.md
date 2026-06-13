# Add calibrated recession severe stress scenario

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` in the repository root. It is self-contained so a future
contributor can continue the work from this file alone.

## Purpose / Big Picture

After this change, the stress report will include a separate hard-landing recession scenario
named `recession_severe`. Unlike a hand-written shock vector, this scenario is calibrated from
the realized factor moves in the existing historical stress windows for 2008 and 2020. A user can
see it working by running the focused stress tests or a normal report run and inspecting
`stress_report.json`: `scenario_results` contains `recession_severe`, and
`recession_calibration` explains which historical window supplied the severe vector and how
model PnL compares with realized episode PnL.

## Progress

- [x] (2026-04-28 17:11+02:00) Read `PLANS.md`, stress code, stress factor code, report/optimization stress call sites, and existing stress tests.
- [x] (2026-04-28 17:11+02:00) Created this ExecPlan before implementation because the work changes stress behavior, report schema, tests, and documentation.
- [x] (2026-04-28 17:23+02:00) Implemented calibrated `recession_severe` in `src/stress.py`.
- [x] (2026-04-28 17:23+02:00) Passed historical factor matrix into `run_stress` from `run_report.py` and `run_optimization.py` where available.
- [x] (2026-04-28 17:23+02:00) Updated stress documentation in `docs/specs/stress_testing_spec.md`; checked README/SPEC references and they point to the stress spec rather than enumerating scenarios.
- [x] (2026-04-28 17:23+02:00) Added focused tests for recession calibration, diagnostic code, and model-vs-realized validation.
- [x] (2026-04-28 17:23+02:00) Ran focused and broader stress/commentary tests and recorded evidence.

## Surprises & Discoveries

- Observation: `run_stress` currently receives asset betas and portfolio betas but not the factor matrix used to estimate them.
  Evidence: both `run_report.py` and `run_optimization.py` call `run_stress(...)` without factor history, then compute `factor_beta_shock_oos` separately.

- Observation: The default pytest temp cleanup path can fail under the Windows sandbox with `PermissionError`.
  Evidence: the broader subset passed all non-commentary stress tests but errored during temp cleanup; rerunning the same command with an explicit cache basetemp and approved escalation produced `9 passed`.

## Decision Log

- Decision: Add one scenario id, `recession_severe`, rather than adding mild/base/severe levels.
  Rationale: The user explicitly requested a single severe hard-landing recession and asked not to add separate severity levels.
  Date/Author: 2026-04-28 / Codex.

- Decision: Calibrate the severe vector from the realized factor moves in the 2008 and 2020 historical windows, then select the window with the worst model PnL for the current portfolio when portfolio betas are available.
  Rationale: This keeps the scenario anchored to history while making "severe" mean most painful for the current portfolio's measured factor exposures.
  Date/Author: 2026-04-28 / Codex.

- Decision: Extend `run_stress` with an optional `factor_returns` argument and keep existing callers/tests working when it is omitted.
  Rationale: The stress engine should stay backward compatible and testable without network data. Production report paths can pass factor history when available.
  Date/Author: 2026-04-28 / Codex.

## Outcomes & Retrospective

Completed. `run_stress` now emits a calibrated `recession_severe` synthetic scenario, includes the selected historical source episode and shock vector on the scenario row, and returns `recession_calibration` with model-vs-realized diagnostics. Report and optimization entry points pass factor history when available, while older callers remain compatible through the optional `factor_returns` argument and fallback metadata. No known functional gaps remain; production calibration still depends on factor data availability from the existing stress factor data sources.

## Context and Orientation

The stress suite is implemented in `src/stress.py`. Static synthetic scenarios are defined in
`SCENARIOS`, then `run_stress` applies each factor shock vector to per-asset betas and weights.
The six factor channels are equity, real rates, credit spreads, inflation, USD, and commodities.
Their shock keys in `src/stress.py` are `shock_eq`, `shock_rr`, `shock_credit`, `shock_inf`,
`shock_usd`, and `shock_cmd`. Their beta keys are `beta_eq`, `beta_rr`, `beta_credit`,
`beta_inf`, `beta_usd`, and `beta_cmd`.

The factor matrix is built in `src/stress_factors.py` by `build_factor_matrix(start, end)`.
It produces weekly factor series with columns `equity`, `real_rates`, `inflation`, `credit`,
`usd`, and `commodity`. Existing OOS explainability in `factor_oos_beta_shock_explainability`
already treats the sum of weekly factor series over an episode as the realized factor shock.
This plan uses the same convention so recession calibration matches the existing project rule.

Historical stress windows are defined by `HISTORICAL_EPISODES` in `src/stress.py`. For this
feature, only the existing `2008` and `2020` windows are used to calibrate `recession_severe`.

## Plan of Work

In `src/stress.py`, add helper functions to convert factor matrix columns into shock keys, compute
realized factor shocks for the `2008` and `2020` windows, score each vector using current
portfolio betas, and select the vector with the lowest model PnL as `recession_severe`. Add
`risk_on_corr` support to `_stress_covariance` so the recession scenario can use a higher
risk-on correlation than existing scenarios. Add recession calibration metadata and validation
output to the returned stress report.

In `run_report.py` and `run_optimization.py`, build a historical factor matrix from 2007-01-01 to
`analysis_end` when stress factor helpers are available, and pass it to `run_stress` as
`factor_returns`. If factor loading fails, leave behavior backward compatible.

In `docs/specs/stress_testing_spec.md`, document `recession_severe`, the calibration rule, the
selected output fields, and the diagnostic code `DIAG_LOSS_RECESSION_SEVERE`. Update README or
SPEC references only if they need more detail than linking to the stress spec.

In `tests/test_stress_mandate_pass.py` or a new focused test file, add deterministic factor data
covering the 2008 and 2020 windows. Assert that `recession_severe` appears in `scenario_results`,
that its shock vector is selected from the worse model-PnL episode, that
`recession_calibration.model_vs_realized` includes comparison rows, and that a loss breach emits
`DIAG_LOSS_RECESSION_SEVERE`.

## Concrete Steps

Work from the repository root:

    C:\Users\ShumeikoYe\OneDrive\Desktop\Cursor BlackRock Model 2

Run focused tests after implementation:

    python -m pytest tests\test_stress_mandate_pass.py tests\test_stress_historical_fields.py tests\test_factor_oos_explainability.py -vv

If those pass and runtime allows, run the broader stress/commentary subset:

    python -m pytest tests\test_portfolio_commentary.py tests\test_stress_mandate_pass.py tests\test_stress_historical_fields.py tests\test_factor_oos_explainability.py -vv

Actual validation:

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\test_stress_mandate_pass.py tests\test_stress_historical_fields.py tests\test_factor_oos_explainability.py -vv
    7 passed in 9.54s

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\test_portfolio_commentary.py tests\test_stress_mandate_pass.py tests\test_stress_historical_fields.py tests\test_factor_oos_explainability.py -vv --basetemp='C:\Users\ShumeikoYe\.cache\codex-pytest-temp-recession'
    9 passed in 2.15s

## Validation and Acceptance

Acceptance is met when focused tests pass and demonstrate the following behavior:

`run_stress(..., factor_returns=...)` returns a `scenario_results` row whose `scenario_id` is
`recession_severe`. The row includes `calibration_source_episode` and `shock_vector`, and its
`pnl_by_factor_pct` reflects the selected calibrated shock vector.

When the calibrated recession PnL breaches the MaxDD loss threshold, the row includes
`DIAG_LOSS_RECESSION_SEVERE` and the suite status becomes `DIAG_ATTENTION`.

The returned report includes `recession_calibration` with `method`,
`selected_source_episode`, `episode_shocks`, `selected_shock`, and `model_vs_realized` rows that
compare model PnL to realized historical episode PnL for 2008 and 2020 where realized portfolio
episode PnL is available.

## Idempotence and Recovery

The implementation is additive and safe to rerun. If factor data is unavailable, the optional
`factor_returns` argument can be omitted and existing stress behavior remains available. Any
manual code edits should be small patches that can be inspected with `git diff`; do not reset the
worktree because the repository may contain user changes.

## Artifacts and Notes

To be filled with final test output and key snippets after implementation.

Key proof from the new test:

    tests/test_stress_mandate_pass.py::test_recession_severe_is_calibrated_from_worst_2008_2020_model_pnl PASSED

The deterministic test builds 2008 and 2020 factor vectors, uses portfolio betas that make the 2008 vector worse, and verifies `DIAG_LOSS_RECESSION_SEVERE`, `vol_mult = 1.60`, `risk_on_corr = 0.95`, and model-vs-realized calibration rows.

## Interfaces and Dependencies

`src.stress.run_stress` must keep its existing positional parameters and add the optional keyword
argument `factor_returns: pd.DataFrame | None = None` before `**_`. The function returns the same
top-level fields as before plus `recession_calibration`.

`src.stress._stress_covariance` must accept a `risk_on_corr: float = 0.90` keyword so existing
scenarios keep their current covariance behavior while `recession_severe` can use `0.95`.

`run_report.py` and `run_optimization.py` should import `build_factor_matrix` from
`src.stress_factors` in the existing stress factor setup block and pass the resulting DataFrame to
`run_stress` when available.
