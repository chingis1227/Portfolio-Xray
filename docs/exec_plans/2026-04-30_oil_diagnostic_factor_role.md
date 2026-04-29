# Oil diagnostic factor role

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` in the repository root.

## Purpose / Big Picture

The project currently uses one factor registry for both production beta modeling and extended diagnostics. That makes `oil` appear as a normal production beta even though it overlaps strongly with `commodity` and is intended to act as a regime warning signal. After this change, production factor outputs use a base registry without `oil`, while stress and diagnostic outputs can still inspect oil separately. A user can verify the result by running the focused factor tests and checking that `stress_report.json.factor_betas_5y` has no `beta_oil`, while `stress_report.json.diagnostic_oil_beta.role` is `diagnostic_warning_only`.

## Progress

- [x] (2026-04-30 00:00+02:00) Read `PLANS.md` and inspected the factor registry, report, optimization, commentary, and tests.
- [x] (2026-04-30 00:20+02:00) Add base factor registry constants and route production beta paths through the base registry.
- [x] (2026-04-30 00:35+02:00) Add `diagnostic_oil_beta` and route extended diagnostic paths so oil remains available.
- [x] (2026-04-30 00:55+02:00) Update commentary, docs, and focused tests.
- [x] (2026-04-30 01:15+02:00) Run focused test suite and full pytest; record outcomes.

## Surprises & Discoveries

- Observation: `FACTOR_COLUMN_ORDER` currently feeds both production paths and diagnostics.
  Evidence: `portfolio_factor_regression_weekly`, rolling beta helpers, OOS stability, Kalman, PCA, covariance, and variance decomposition all reference `FACTOR_COLUMN_ORDER`.
- Observation: `run_report.py` already had a local fix from the previous turn that renamed a shadowing variable in the PCA export block.
  Evidence: `git status --short` shows `run_report.py` modified before this task's implementation began.
- Observation: Sandboxed full pytest could not create or clean pytest temporary directories under the default cache path.
  Evidence: full pytest first failed with `PermissionError` on `C:\Users\ShumeikoYe\.cache\codex-pytest-temp`; rerunning the same suite with escalated filesystem access passed.

## Decision Log

- Decision: Keep `FACTOR_DEFINITIONS` and `FACTOR_COLUMN_ORDER` as the extended diagnostics/stress registry, and introduce new `BASE_*` constants for production paths.
  Rationale: This preserves existing extended diagnostics behavior while making production usage explicit and less likely to accidentally re-include `oil`.
  Date/Author: 2026-04-30 / Codex.
- Decision: Production helper defaults should use the base registry; diagnostic callers must explicitly request the extended registry.
  Rationale: Defaults should protect production outputs from `beta_oil` leaks.
  Date/Author: 2026-04-30 / Codex.
- Decision: Commentary prints Oil only in a dedicated `Oil diagnostic/stress warning` section.
  Rationale: This prevents `beta_oil` from being interpreted as a production beta while still surfacing Oil/Commodity collinearity and Kalman oil diagnostics.
  Date/Author: 2026-04-30 / Codex.

## Outcomes & Retrospective

Implemented. Production beta/regression/rolling stability/OOS/adjusted overlay/base variance decomposition now default to the base factor registry without Oil. Extended factor matrix, factor covariance, PCA, Kalman diagnostics, and the new `diagnostic_oil_beta` block retain Oil as a `diagnostic_warning_only` signal. Focused tests passed (`45 passed`), and full pytest passed after rerunning outside the sandbox temp-directory restriction (`74 passed`).

## Context and Orientation

The key implementation file is `src/stress_factors.py`. It defines `FactorDefinition`, downloads and aligns weekly/monthly factors, estimates asset and portfolio factor betas, computes rolling beta stability, Kalman diagnostics, factor covariance, variance decomposition, and PCA. `run_report.py` and `run_optimization.py` call these helpers and export `stress_report.json`. `src/portfolio_commentary.py` converts `stress_report.json` into text commentary.

In this plan, "base production factors" means factors used for the normal portfolio beta and regression model: `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, and `us_growth`. "Extended diagnostics/stress factors" means the base factors plus `oil`. Oil remains available for diagnostics because it can signal energy shocks, but it is no longer a production beta.

## Plan of Work

First, add `BASE_FACTOR_DEFINITIONS`, `BASE_FACTOR_COLUMN_ORDER`, and `BASE_BETA_ROW_ORDER` next to the existing factor constants in `src/stress_factors.py`. Add small helper functions that select and order factor columns and beta keys for base or extended use.

Next, update production helpers to use base factor columns by default. This includes `estimate_betas`, `_portfolio_factor_weekly_ols_rows`, `portfolio_factor_regression_weekly`, `compute_asset_factor_betas_weekly`, `estimate_betas_monthly`, rolling beta helpers, OOS beta helpers, `factor_beta_stability_diagnostics`, `factor_beta_stability_rows`, `build_factor_beta_adjustment_overlay`, and `factor_variance_decomposition_weekly`.

Then, keep diagnostic helpers on the extended registry. `factor_covariance_analytics`, `portfolio_pca_diagnostics`, and Kalman diagnostics continue to use `FACTOR_COLUMN_ORDER`. `attach_kalman_factor_betas_to_stress_report` will explicitly request extended weekly rows. Add a `diagnostic_oil_beta` builder that combines production-safe oil diagnostics from extended beta estimates, Oil/Commodity collinearity, and Kalman oil data.

Finally, update `run_report.py` and `run_optimization.py` to compute and export `diagnostic_oil_beta`, update commentary to label oil as `diagnostic_warning_only`, update docs, and revise tests.

## Concrete Steps

All commands run from the repository root:

    C:\Users\ShumeikoYe\OneDrive\Рабочий стол\Курсор Модель Блекрока 2

Run focused tests:

    python -m pytest tests/test_factor_matrix_builders.py tests/test_factor_beta_stability.py tests/test_factor_beta_adjusted_overlay.py tests/test_factor_beta_kalman.py tests/test_factor_variance_decomposition.py tests/test_factor_covariance.py tests/test_portfolio_pca.py tests/test_portfolio_commentary.py -vv

Run the full suite:

    python -m pytest

## Validation and Acceptance

Acceptance is satisfied when focused tests and full pytest pass and the report contract has these observable properties: production beta outputs contain no `beta_oil`; base regression, stability, OOS, adjusted overlay, and base variance decomposition exclude oil; extended factor matrix, stress/scenario analytics, extended covariance diagnostics, extended PCA, Kalman diagnostics, and `diagnostic_oil_beta` keep oil; commentary labels oil only as diagnostic/stress.

## Idempotence and Recovery

The code changes are source edits and can be rerun safely. Generated outputs in `Main portfolio`, `results_csv`, `output`, `cache`, and `pdf_md_sources` are not source of truth unless the user explicitly asks to regenerate them. If tests fail, inspect the failing assertion, update source or tests, and rerun the narrow test before the full suite.

## Artifacts and Notes

The implementation should leave `stress_report.json.factor_betas_5y` shaped like:

    {
      "beta_eq": ...,
      "beta_rr": ...,
      "beta_inf": ...,
      "beta_credit": ...,
      "beta_usd": ...,
      "beta_cmd": ...,
      "beta_vix": ...,
      "beta_us_growth": ...
    }

and add:

    {
      "diagnostic_oil_beta": {
        "role": "diagnostic_warning_only",
        ...
      }
    }

## Interfaces and Dependencies

No new package dependencies are required. The main new public constants are `src.stress_factors.BASE_FACTOR_DEFINITIONS`, `src.stress_factors.BASE_FACTOR_COLUMN_ORDER`, and `src.stress_factors.BASE_BETA_ROW_ORDER`. The new report interface is `stress_report.json.diagnostic_oil_beta`.
