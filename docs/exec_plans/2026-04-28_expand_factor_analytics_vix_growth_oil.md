# Expand factor analytics with VIX, US growth proxy, and oil

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` in the repository root. It is self-contained so a future
contributor can continue the work from this file alone.

## Purpose / Big Picture

After this change, the weekly factor-beta analytics used in `stress_report.json`,
rolling beta artifacts, and factor commentary will cover nine factors instead of six.
Users will be able to inspect portfolio and asset exposure not only to equity, real rates,
inflation, credit, USD, and commodity, but also to VIX, a US growth proxy, and oil.
The synthetic stress engine will remain a six-shock diagnostic suite, so the new factors
affect analytics and explainability without silently changing scenario PnL semantics.

## Progress

- [x] (2026-04-28 18:40+02:00) Read `PLANS.md`, `src/stress_factors.py`, `src/portfolio_commentary.py`, stress/report call sites, current factor tests, and documentation references.
- [x] (2026-04-28 18:40+02:00) Created this ExecPlan before implementation because the work changes shared factor analytics, report schema, tests, rolling charts, and documentation.
- [x] (2026-04-28 22:40+02:00) Implemented registry-driven factor definitions and new weekly/monthly factor loaders in `src/stress_factors.py`.
- [x] (2026-04-28 22:40+02:00) Updated rolling beta plotting/commentary paths to use dynamic factor ordering instead of six hardcoded beta keys.
- [x] (2026-04-28 22:40+02:00) Added focused tests for factor matrix construction, regression shape, OOS explainability, commentary rendering, rolling PNG layout, and stress-engine isolation.
- [x] (2026-04-28 22:40+02:00) Updated `README.md`, `RULES.md`, `SPEC.md`, `AGENTS.md`, and `docs/specs/stress_testing_spec.md`; verified stale six-factor analytics references were narrowed to synthetic stress shocks or removed.
- [x] (2026-04-28 22:40+02:00) Ran focused pytest subset and full `python -m pytest`; recorded validation evidence below.

## Surprises & Discoveries

- Observation: the current analytics pipeline hardcodes the six-factor order in several different places instead of deriving it from one source of truth.
  Evidence: `src/stress_factors.py` repeats the factor list in `FACTOR_TO_BETA_KEY`, `estimate_betas`, monthly helpers, rolling betas, and rolling plot titles; `src/portfolio_commentary.py` also maintains its own `_BETA_ROW_ORDER`.

- Observation: `WEI` is weekly but published as week-ending Saturday, while the portfolio factor pipeline is aligned to Friday week-ends.
  Evidence: FRED metadata for `WEI` uses weekly ending Saturday; `src/stress_factors.py` explicitly resamples other factors to `W-FRI`, so `WEI` needs an explicit date shift before inner joins.

- Observation: full-repo `pytest` collection was sensitive to inaccessible temp-like directories left in the repository root by older runs.
  Evidence: the first full run failed during collection on `commentary_*`, `factor_png_*`, and `tmp*` directories in the repo root. Adding `pytest.ini` with `testpaths = tests` made full test discovery deterministic and avoided collecting generated directories as tests.

## Decision Log

- Decision: implement US growth via FRED `WEI` rather than literal quarterly GDP growth.
  Rationale: the project's factor-beta analytics, rolling regressions, and OOS episode explainability are weekly and rely on synchronous inner joins; `WEI` is already weekly and explicitly scaled to GDP-related activity.
  Date/Author: 2026-04-28 / Codex.

- Decision: implement oil via FRED/EIA WTI spot `DCOILWTICO`, not `CL=F`.
  Rationale: the user asked for an efficient, stable historical factor series; WTI spot avoids futures roll and continuous-contract artifacts while preserving the intended oil exposure.
  Date/Author: 2026-04-28 / Codex.

- Decision: keep synthetic stress shocks unchanged in `src/stress.py`.
  Rationale: the requested scope is analytics-only; adding `shock_vix`, `shock_growth`, or `shock_oil` would alter scenario semantics and needs a separate spec.
  Date/Author: 2026-04-28 / Codex.

## Outcomes & Retrospective

Implemented a registry-driven factor analytics layer in `src/stress_factors.py` with nine ordered analytics factors:
`equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, `us_growth`, and `oil`.
The first six remain the only stress-participating factors, so `src/stress.py` synthetic scenarios and
recession calibration semantics did not change.

Rolling beta HTML/PNG outputs and commentary rendering now derive their ordering from the shared registry
instead of maintaining separate six-factor lists. This removed a class of report drift bugs where new beta
keys could exist in JSON but not appear in commentary or plots.

Focused tests were added/updated for factor matrix construction, regression shape, OOS explainability,
commentary rendering, rolling PNG generation, and the stress-engine boundary. A repository `pytest.ini`
was also added so full test discovery stays inside `tests/` and does not recurse into generated temp
directories under the project root.

## Context and Orientation

The shared factor analytics live in `src/stress_factors.py`. That module currently builds a
weekly factor matrix, estimates per-asset betas, estimates portfolio-level weekly OLS factor
regressions, computes rolling factor betas, and writes rolling HTML/PNG artifacts. The report
entry points `run_report.py` and `run_optimization.py` already consume these analytics through
existing functions, so the safest implementation path is to change the factor-definition layer
once and let existing callers inherit the extra columns.

`src/stress.py` is separate. It uses shock-key to beta-key mappings for synthetic scenario PnL
and recession calibration. This file must remain explicitly six-shock in this change even if the
factor matrix grows to nine columns.

`src/portfolio_commentary.py` renders stress-report analytics into human-readable text. It still
assumes six fixed beta keys when printing factor regressions and rolling summaries, so it must be
made dynamic or the new analytics will not surface in commentary.

## Plan of Work

In `src/stress_factors.py`, introduce a registry of ordered factor definitions that stores the
factor column name, beta key, display name, source label, weekly loader, monthly loader, and
whether the factor participates in synthetic stress shocks. Use this registry as the single source
of truth for factor column ordering, beta-key ordering, display names, and mapping dictionaries.
Add `vix`, `us_growth`, and `oil` to that registry while preserving the existing six factor names
and beta keys for backward compatibility.

Add weekly and monthly loaders for the three new factors. `vix` should use FRED `VIXCLS` with
level-to-return transforms. `oil` should use FRED `DCOILWTICO` with level-to-return transforms.
`us_growth` should use FRED `WEI`, shifting the weekly Saturday dates back one day to Friday and
then differencing the level for weekly and month-end series.

Refactor the existing factor-matrix builders, beta estimators, portfolio factor regression output,
rolling beta summaries, and rolling chart writers to derive ordering and names from the registry.
The rolling PNG writer must use a dynamic subplot grid so nine factors render as a `3 x 3` layout.

In `src/portfolio_commentary.py`, replace the fixed six-key beta order with registry-derived order.
Factor regression sections, HAC rows, and rolling summary blocks must iterate dynamically over
present beta keys while preserving the registry order.

Add focused tests for the new factor loaders and dynamic outputs, then update documentation to make
the analytics/stress boundary explicit and document the three new analytics-only factors.

## Concrete Steps

Work from the repository root:

    C:\Users\ShumeikoYe\OneDrive\Р Р°Р±РѕС‡РёР№ СЃС‚РѕР»\РљСѓСЂСЃРѕСЂ РњРѕРґРµР»СЊ Р‘Р»РµРєСЂРѕРєР° 2

Focused validation after implementation:

    python -m pytest tests\test_factor_matrix_builders.py tests\test_factor_oos_explainability.py tests\test_factor_regression_hac.py tests\test_factor_regression_heteroskedasticity.py tests\test_factor_regression_serial.py tests\test_portfolio_commentary.py tests\test_stress_historical_fields.py tests\test_stress_mandate_pass.py -vv

Broader validation:

    python -m pytest

Actual commands and outputs will be recorded here after implementation.

Implemented commands and outcomes:

    python -m pytest tests\test_factor_matrix_builders.py tests\test_factor_oos_explainability.py tests\test_portfolio_commentary.py tests\test_stress_mandate_pass.py tests\test_stress_historical_fields.py tests\test_factor_regression_hac.py tests\test_factor_regression_heteroskedasticity.py tests\test_factor_regression_serial.py -vv

Result:

    17 passed in 4.14s

    python -m pytest

Result:

    34 passed in 103.88s

## Validation and Acceptance

Acceptance is met when the following are true:

`build_factor_matrix` returns weekly columns `vix`, `us_growth`, and `oil` in addition to the
existing six columns, and `WEI` observations align to Friday after the one-day shift.

`portfolio_factor_regression_weekly` and the per-asset beta functions produce `beta_vix`,
`beta_us_growth`, and `beta_oil` in the expected registry order. `factor_beta_shock_oos`
includes contributions from the new beta keys when the factor matrix contains them.

`write_rolling_betas_plot_pngs` renders a dynamic grid with one panel per beta, and
`write_stress_commentary` prints the new beta keys without requiring hardcoded six-item lists.

`run_stress` keeps six-shock behavior: synthetic scenario PnL and `pnl_by_factor_pct` continue
to ignore analytics-only factors.

## Idempotence and Recovery

The change is additive. If any new factor series fails to load, existing analytics helpers should
still return the subset of factors that meets the minimum aligned history rules. Re-running the
implementation steps is safe because edits are ordinary source changes and tests are read-only with
respect to repo-tracked files.

## Artifacts and Notes

- New analytics-only beta keys in JSON/report outputs:
  - `beta_vix`
  - `beta_us_growth`
  - `beta_oil`
- New analytics factor columns in factor matrices:
  - `vix`
  - `us_growth`
  - `oil`
- Synthetic stress output remains six-shock and does not add `shock_vix`, `shock_us_growth`, or `shock_oil`.

## Interfaces and Dependencies

`src.stress_factors` must expose one registry-backed ordering for factor columns and beta keys so
that analytics producers and commentary consumers do not maintain separate factor lists.

The new public analytics keys added to report JSON and rolling outputs are:

- `beta_vix`
- `beta_us_growth`
- `beta_oil`

The weekly and monthly factor matrices must also expose:

- `vix`
- `us_growth`
- `oil`
