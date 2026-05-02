# Add internal market-proxy macro regime diagnostics

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository contains `PLANS.md` at the repository root. Maintain this document in accordance
with `PLANS.md`.

## Purpose / Big Picture

After this change, `stress_report.json` will include a diagnostic-only `macro_regime_diagnostics`
block. The block labels weekly factor history into four internal market-proxy regimes using a
growth score and an inflation-pressure score, then reports regime-specific factor betas,
factor covariance, factor risk, factor risk contributions, confidence, fallback usage, and
policy signals. This lets a portfolio reviewer see whether factor exposures are stable across
market regimes without changing optimizer weights, mandate gates, or stress pass/fail status.

## Progress

- [x] (2026-04-30) Read `PLANS.md` and inspected current factor diagnostics, covariance analytics,
  report wiring, commentary, and existing tests.
- [x] (2026-04-30) Created this ExecPlan with the user-approved MVP scope.
- [x] (2026-04-30) Implemented `macro_regime_diagnostics` helpers in `src/stress_factors.py`.
- [x] (2026-04-30) Wired the block and CSV exports into `run_optimization.py` and `run_report.py`.
- [x] (2026-04-30) Added stress commentary output and no-network tests.
- [x] (2026-04-30) Updated documentation and ran focused, broader factor/stress, and full pytest validation.

## Surprises & Discoveries

- Observation: The repository already has a factor covariance block with `base`,
  `stress_empirical`, and `stress_overlay`, but it is not a four-regime growth/inflation
  classifier.
  Evidence: `src/stress_factors.py` has `factor_covariance_analytics`, and
  `docs/docs/stress_testing_spec.md` documents the three existing covariance regimes.
- Observation: Oil is intentionally excluded from production beta outputs and retained as a
  diagnostic warning-only signal.
  Evidence: `PROJECT_RULES.md` states that production factor order excludes Oil while extended
  diagnostic/stress factor order may include it.

## Decision Log

- Decision: Implement the first regime model as `internal_market_proxy_v1` using existing factor
  rows, not a new macro data layer.
  Rationale: This keeps the implementation local, testable without network access, and aligned
  with the current report architecture.
  Date/Author: 2026-04-30 / Codex
- Decision: Use `us_growth` as `growth_score` and the average rolling z-score of available
  `inflation` and `commodity` as `inflation_pressure_score`.
  Rationale: The user requested an internal proxy model and explicitly named this v1 formula.
  Date/Author: 2026-04-30 / Codex
- Decision: Do not create neutral regimes in the MVP.
  Rationale: The neutral band is used only for confidence and transition warnings, so the four
  regime labels remain stable.
  Date/Author: 2026-04-30 / Codex
- Decision: Keep the block diagnostic-only and exclude it from optimizer inputs.
  Rationale: The requested MVP should be useful for review without changing weight release logic.
  Date/Author: 2026-04-30 / Codex

## Outcomes & Retrospective

Implementation is complete. The new diagnostic block, CSV exports, commentary output, tests, and
documentation are in place. Focused tests, broader factor/stress tests, and full pytest pass.

## Context and Orientation

The project is a Python portfolio optimization and reporting system. `run_optimization.py` writes
optimized weights and a `stress_report.json` artifact, while `run_report.py` rebuilds report
artifacts from current weights and data. Factor diagnostics live mostly in `src/stress_factors.py`.
The existing factor registry includes production base factors `equity`, `real_rates`,
`inflation`, `credit`, `usd`, `commodity`, `vix`, and `us_growth`; Oil is diagnostic/stress only
and must not enter this MVP's production regime betas or covariance.

A regime is a label assigned to a weekly row of factor data. This MVP uses two rolling z-scores.
A z-score is the current value minus its rolling mean, divided by rolling standard deviation. The
MVP uses a 156-week rolling window and requires at least 52 observations before a score is trusted.
The four labels are `goldilocks`, `reflation`, `stagflation`, and `recession_disinflation`.

## Plan of Work

In `src/stress_factors.py`, add constants for the method version, disclaimer, regime names,
rolling window, neutral threshold, and quality thresholds. Add helpers to compute rolling z-scores,
assign four regime labels, classify quality by row count, run OLS plus HAC inference on rows within
one regime, compute covariance with `ddof=1`, compute factor risk as `b' Sigma b`, and label risk
contribution signs as `risk_adder` or `hedging_or_diversifying_contribution`.

Add `macro_regime_diagnostics_from_frames(portfolio_returns, factor_returns, analysis_end_str)`
for tests and for callers that already have weekly rows. Add `macro_regime_diagnostics(weights,
tickers, analysis_end_str, factor_returns=None)` for production paths. The production helper should
reuse existing weekly asset/factor row construction where possible, so it does not introduce a new
data download pattern.

Wire the output into `run_optimization.py` and `run_report.py` after existing factor diagnostics are
available. Export four CSV files in the configured CSV output directory: weekly labels, factor
betas, factor covariance, and factor risk contributions.

Update `src/portfolio_commentary.py` to add a short macro regime section with current regime,
latest scores, confidence, transition warning, usable/reliable regime count, top unstable betas,
policy signal counts, and the method disclaimer.

Update `docs/docs/stress_testing_spec.md`, `PROJECT_RULES.md`, `SPEC.md`, and `README.md` so the
report contract and diagnostic-only limitations are explicit.

## Concrete Steps

Work from the repository root:

    C:\Users\ShumeikoYe\OneDrive\Рабочий стол\Курсор Модель Блекрока 2

After implementation, run focused tests:

    python -m pytest tests/test_macro_regimes.py tests/test_factor_covariance.py tests/test_portfolio_commentary.py -vv

Then run broader factor/stress regression tests:

    python -m pytest tests/test_factor_beta_stability.py tests/test_factor_beta_kalman.py tests/test_factor_beta_adjusted_overlay.py tests/test_factor_variance_decomposition.py tests/test_factor_covariance.py tests/test_portfolio_pca.py tests/test_portfolio_commentary.py -vv

If time and environment allow, run full test suite:

    python -m pytest

## Validation and Acceptance

Acceptance is met when focused tests pass and `macro_regime_diagnostics` has the required top-level
fields: `axis_model.version`, `axis_scores_latest.growth_score`,
`axis_scores_latest.inflation_pressure_score`, `current_regime`, `regime_confidence`,
`regime_transition_warning`, `available_regimes_count`, and `method_disclaimer`.

No-network tests must prove that all four labels are possible, no neutral regime is created,
confidence falls to low near zero scores, transition warnings are emitted near regime boundaries,
quality status changes with observation count, low-confidence regimes shrink to `base_10y`,
insufficient regimes fall back to `base_10y`, negative risk contribution is serialized and labeled,
and the method disclaimer appears in JSON and commentary.

## Idempotence and Recovery

The implementation is additive. Re-running tests or reports should overwrite generated CSV and JSON
artifacts in the normal output directories without changing source files. If a test run creates
cache files, leave them as generated outputs. Do not revert unrelated user changes.

## Artifacts and Notes

Expected focused test result after completion should resemble:

    tests/test_macro_regimes.py ... PASSED
    tests/test_factor_covariance.py ... PASSED
    tests/test_portfolio_commentary.py ... PASSED

Observed focused validation:

    python -m pytest tests/test_macro_regimes.py tests/test_factor_covariance.py tests/test_portfolio_commentary.py -vv
    16 passed

Observed broader validation:

    python -m pytest tests/test_factor_beta_stability.py tests/test_factor_beta_kalman.py tests/test_factor_beta_adjusted_overlay.py tests/test_factor_variance_decomposition.py tests/test_factor_covariance.py tests/test_portfolio_pca.py tests/test_portfolio_commentary.py -vv
    40 passed

Observed full validation:

    python -m pytest
    110 passed

## Interfaces and Dependencies

`src.stress_factors.macro_regime_diagnostics_from_frames` must accept weekly portfolio returns and
weekly factor rows and return a JSON-serializable dictionary. `src.stress_factors.macro_regime_diagnostics`
must accept weights, tickers, `analysis_end_str`, and optional prebuilt factor returns, then return the
same dictionary plus CSV-ready nested rows. Use only existing dependencies: `numpy`, `pandas`, and
`scipy.stats` already used by `src/stress_factors.py`.
