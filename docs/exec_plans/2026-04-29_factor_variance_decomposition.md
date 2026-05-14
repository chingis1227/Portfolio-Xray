# Add weekly factor variance decomposition

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` in the repository root.

## Purpose / Big Picture

After this change, a user reading `stress_report.json`, `stress_commentary.txt`, or the CSV exports can see what share of weekly portfolio variance is explained by each factor and what share remains residual. The metric separates signed net factor effects from gross factor concentration, distinguishes risk adders from hedgers, and warns when the factor variance implied by betas and factor covariance is inconsistent with regression R-squared. This is diagnostic only and does not change optimization, stress pass/fail, mandate status, or weight release.

## Progress

- [x] (2026-04-29 00:00+02:00) Read `PLANS.md`, current factor regression, factor covariance, report export, and commentary paths.
- [x] (2026-04-29 00:00+02:00) Add same-row weekly decomposition helpers in `src/stress_factors.py`.
- [x] (2026-04-29 00:00+02:00) Wire `run_report.py` to export JSON and CSV artifacts.
- [x] (2026-04-29 00:00+02:00) Add stress commentary output.
- [x] (2026-04-29 00:00+02:00) Update specs and user-facing docs.
- [x] (2026-04-29 00:00+02:00) Add focused tests for formula, guardrails, cross-check, net/gross, residual, and stability behavior.
- [x] (2026-04-29 00:00+02:00) Run focused decomposition and commentary tests: 8 passed.
- [x] (2026-04-29 00:00+02:00) Run adjacent factor covariance, beta stability, and factor matrix tests: 16 passed.
- [x] (2026-04-29 00:00+02:00) Run full test suite: 53 passed.

## Surprises & Discoveries

- Observation: `portfolio_factor_regression_weekly` already computes the exact weekly portfolio return rows and factor rows needed for a methodologically consistent variance decomposition.
  Evidence: The function builds `y_valid` and `X_valid` after the same inner join and valid mask used for OLS.
- Observation: Existing `factor_covariance.base` is a useful regime analytic, but decomposition cross-checks should use covariance computed on OLS rows to avoid comparing different samples.
  Evidence: `factor_covariance_analytics` builds a 5Y base covariance from factor history, while regression rows also depend on available portfolio asset returns.

## Decision Log

- Decision: Use weekly variance scale only for the v1 decomposition.
  Rationale: Factor regressions and factor covariance analytics are weekly; mixing annualized values would make R-squared cross-checks ambiguous.
  Date/Author: 2026-04-29 / Codex.
- Decision: Normalize `factor_rc_share` inside `factor_variance = b' Sigma_f b` before applying R-squared.
  Rationale: This keeps factor RC as an Euler attribution of factor variance and makes `net_total_variance_share = factor_rc_share * R2` reproducible.
  Date/Author: 2026-04-29 / Codex.
- Decision: Return unavailable status rather than partial attribution for degenerate variance, insufficient observations, or factor dimension mismatch.
  Rationale: A partial variance decomposition can look numerically precise while carrying the wrong economic meaning.
  Date/Author: 2026-04-29 / Codex.
- Decision: Keep v1 stability minimal: factor sign stability and R-squared p10/p90 only.
  Rationale: This provides a useful noise check without delaying the base metric behind a larger rolling analytics project.
  Date/Author: 2026-04-29 / Codex.

## Outcomes & Retrospective

Completed. The report contract now includes `stress_report.json.factor_variance_decomposition` with weekly same-row variance scale, R2 cross-check, guardrails, signed net factor contributions, gross concentration, risk adders, hedgers, neutral factors, residual severity, and minimal stability diagnostics. `run_report.py` exports `results_csv/factor_variance_decomposition_5y.csv`, and `stress_commentary.txt` summarizes the diagnostics. Validation passed with the full test suite: 53 tests.

## Context and Orientation

`run_report.py` is the reporting entrypoint. It builds weekly factor betas and portfolio factor regression diagnostics, then exports `stress_report.json` and CSV artifacts. `src/stress_factors.py` owns factor matrix construction, factor regressions, rolling beta diagnostics, and factor covariance analytics. `src/portfolio_commentary.py` writes `stress_commentary.txt` from `stress_report.json`.

Factor variance decomposition means attributing total weekly portfolio variance to factor sources plus residual. "Net" contribution is signed and can be negative when a factor hedges other factor risk through covariance. "Gross" contribution uses absolute component variance to show concentration before netting hedges. "Residual" is `1 - R2`, the variance share not explained by the current linear factor model.

## Plan of Work

Add a same-row decomposition helper to `src/stress_factors.py`. It must prepare the same weekly portfolio returns and factor rows used by OLS, compute weekly sample portfolio variance and factor covariance with `ddof=1`, estimate OLS betas, compute `factor_variance = b' Sigma_f b`, and return unavailable status before normalization if any guardrail fails.

Add a public `factor_variance_decomposition_weekly` function that computes the 5Y decomposition and a minimal stability layer from 3Y, 5Y, and 10Y weekly snapshots where available. The JSON result must include status, reason, method, `variance_scale`, cross-check, net/gross rows, risk adders, hedgers, neutral factors, residual diagnostics, warnings, and stability.

Update `run_report.py` to call the new helper after `factor_regression_5y`, store the result in `stress_report["factor_variance_decomposition"]`, export `results_csv/factor_variance_decomposition_5y.csv`, and log local warnings without changing stress status.

Update `src/portfolio_commentary.py` to add a compact section that prints decomposition status, cross-check status, residual severity, risk adders, hedgers, neutral factors, gross concentration, local warnings, and stability severity.

Update `docs/specs/stress_testing_spec.md`, `README.md`, and `SPEC.md` with the formulas, weekly scale, guardrails, cross-check thresholds, net/gross definitions, neutral threshold, residual thresholds, and stability v1 rules.

## Concrete Steps

From the repository root, run:

    python -m pytest tests/test_factor_variance_decomposition.py -vv
    python -m pytest tests/test_factor_covariance.py tests/test_portfolio_commentary.py -vv
    python -m pytest tests/test_factor_beta_stability.py tests/test_factor_matrix_builders.py -vv
    python -m pytest

If the full suite is too slow or blocked by external data, record the focused tests and the blocker.

## Validation and Acceptance

Acceptance requires `stress_report.json.factor_variance_decomposition` to exist after `run_report.py` when factor data and portfolio returns are available. It must use `variance_scale="weekly"`, include `cross_check`, preserve signed negative contributions, split `risk_adders` and `hedgers`, include gross fields, report residual severity, and return explicit unavailable reasons when guardrails fail. The CSV artifact `results_csv/factor_variance_decomposition_5y.csv` must contain the row-level decomposition fields.

Focused tests must prove formula normalization, weekly scale, degeneracy guardrails, dimension mismatch handling, neutral classification, local warnings, cross-check thresholds, net/gross behavior, residual severity, stability unknown and severity behavior, and commentary output.

## Idempotence and Recovery

The implementation is additive. Re-running `run_report.py` overwrites generated JSON, commentary, and CSV artifacts in the normal output directories. If validation fails, fix the helper or tests and rerun the focused command. Do not change optimizer behavior or top-level stress status for decomposition warnings.

## Artifacts and Notes

The primary generated artifacts are:

    stress_report.json
    stress_commentary.txt
    results_csv/factor_variance_decomposition_5y.csv

## Interfaces and Dependencies

In `src/stress_factors.py`, define:

    factor_variance_decomposition_weekly(
        *,
        weights: dict[str, float],
        tickers: list[str],
        analysis_end_str: str,
        window_weeks: int = FACTOR_WEEKS_5Y,
        rolling_windows_weeks: dict[str, int] | None = None,
    ) -> dict[str, Any]

The function depends only on pandas, numpy, scipy, and existing project factor/data helpers.
