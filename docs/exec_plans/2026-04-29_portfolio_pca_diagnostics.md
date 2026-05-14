# Add portfolio PCA diagnostics

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` in the repository root.

## Purpose / Big Picture

After this change, a user reading `stress_report.json`, `results_csv/`, or
`stress_commentary.txt` can see whether the current portfolio is driven by one hidden
statistical risk direction. The diagnostic computes PCA on weekly returns for the assets
actually used in the portfolio, both before and after removing the named factor model.
It separates covariance PCA, which measures risk dominance, from correlation PCA, which
measures common movement structure after volatility standardization.

The feature is diagnostic only. It must not change optimized weights, stress pass/fail,
mandate status, or weight release.

## Progress

- [x] (2026-04-29 00:00+02:00) Read `PLANS.md`, the report stress analytics flow, factor
  regression helpers, commentary writer, and existing factor diagnostics tests.
- [x] (2026-04-29 00:00+02:00) User decisions captured: v1 uses current portfolio assets,
  includes raw and residual PCA, exports JSON + CSV + text, includes covariance and
  correlation PCA, PC1 stability, ENB, and PC1 factor correlations.
- [x] (2026-04-29 00:00+02:00) Implemented PCA helpers in `src/stress_factors.py`.
- [x] (2026-04-29 00:00+02:00) Wired PCA into `run_report.py` and CSV exports.
- [x] (2026-04-29 00:00+02:00) Added stress commentary output.
- [x] (2026-04-29 00:00+02:00) Updated docs and tests.
- [x] (2026-04-29 00:00+02:00) Ran focused and full verification.

## Surprises & Discoveries

- Observation: The current report path already has a natural home for PCA next to
  `factor_covariance` and `factor_variance_decomposition`.
  Evidence: `run_report.py` builds factor diagnostics before exporting `stress_report.json`.

## Decision Log

- Decision: Keep PCA diagnostic-only and non-binding.
  Rationale: The project treats factor covariance, factor variance decomposition, and beta
  stability as report diagnostics. PCA should explain hidden concentration without changing
  optimization or gates.
  Date/Author: 2026-04-29 / Codex

- Decision: Use current positive-weight portfolio assets as the v1 universe.
  Rationale: This directly explains the portfolio being reported and avoids a new S&P 500
  constituent data dependency.
  Date/Author: 2026-04-29 / User and Codex

- Decision: Compute both covariance PCA and correlation PCA.
  Rationale: Covariance PCA reveals risk dominance including volatility scale; correlation
  PCA reveals common movement structure after standardization.
  Date/Author: 2026-04-29 / User and Codex

## Outcomes & Retrospective

Completed. The report contract now includes `stress_report.json.portfolio_pca` with raw
and factor-residual PCA, covariance PCA for risk dominance, correlation PCA for structure,
PC1 stability, effective number of bets, and PC1 factor correlations. `run_report.py`
and `run_optimization.py` both export PCA summary, components, rolling PC1, and
PC1-factor-correlation CSV files. `stress_commentary.txt` now prints a compact PCA
interpretation. Validation passed with the full test suite: 61 tests, and a follow-up
sync added the same PCA block to the optimization path.

Focused validation:

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\test_portfolio_pca.py tests\test_portfolio_commentary.py -vv
    8 passed

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest tests\test_factor_variance_decomposition.py tests\test_factor_covariance.py tests\test_portfolio_commentary.py -vv
    14 passed

Full validation:

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest
    61 passed

## Context and Orientation

`run_report.py` is the main reporting entrypoint. It builds weekly factor betas, portfolio
factor regressions, factor covariance analytics, factor variance decomposition, and PCA,
then exports `stress_report.json` through `src.io_export.export_stress_report`.

`run_optimization.py` also writes `stress_report.json` and `stress_commentary.txt` as part
of the optimization pipeline. The PCA contract should stay aligned across both entrypoints.

`src/stress_factors.py` owns factor matrix construction and factor diagnostics. It already
contains `asset_weekly_returns_from_daily`, `build_factor_matrix`, and helpers that download
daily adjusted close data through `src.data_yf.download_all`.

`src/portfolio_commentary.py` writes `stress_commentary.txt` from the in-memory
`stress_report`. The new PCA section should be appended near the other factor diagnostics.

PCA means principal component analysis. In this implementation it is the eigen-decomposition
of a weekly covariance or correlation matrix. PC1 is the first principal component, the
direction that explains the largest share of total variance in the chosen matrix.

ENB means effective number of bets. It is computed from PCA variance shares as
`1 / sum(p_i^2)`, where `p_i` is each component's explained variance ratio. A low ENB means
that a portfolio that appears to hold several assets is effectively driven by fewer
independent risk directions.

## Plan of Work

Add pure PCA functions in `src/stress_factors.py` that accept weekly returns and optional
factor returns. The functions must return unavailable status instead of raising when there
are too few rows, too few assets, degenerate variance, or empty factor alignment.

Wire the main wrapper into both `run_report.py` and `run_optimization.py`. Export a
summary CSV, component/loadings CSV, rolling PC1 CSV, and PC1-factor-correlation CSV under
`results_csv/`.

Add a compact PCA section to `src/portfolio_commentary.py`. The text must interpret
covariance PCA as risk dominance and correlation PCA as structure, and must call out high
residual PC1 as hidden common risk not explained by the named factor model.

Update `docs/specs/stress_testing_spec.md`, `SPEC.md`, `README.md`, and `RULES.md`
so the JSON contract, user-visible outputs, and non-binding rule are explicit.

## Concrete Steps

From the repository root:

    python -m pytest tests/test_portfolio_pca.py tests/test_portfolio_commentary.py -vv

Then run:

    python -m pytest tests/test_factor_variance_decomposition.py tests/test_factor_covariance.py tests/test_portfolio_commentary.py -vv

If those pass and changes touch shared helpers, run:

    python -m pytest

## Validation and Acceptance

Acceptance requires `stress_report.json.portfolio_pca` after both `run_report.py` and
`run_optimization.py` when there are at least two positive-weight assets and at least 52
aligned weekly observations. It must include raw and residual blocks, and each must
include `covariance_pca` and `correlation_pca`.

Each PCA block must include PC1 share, PC1 severity, ENB, ENB severity, rolling PC1
stability summary, components/loadings, and PC1 factor correlations when factor data is
available. CSV artifacts must be written under `results_csv/`.

Focused tests must prove that covariance PCA can differ from correlation PCA, residual PCA
can reduce PC1 concentration after factor removal, ENB is computed from eigenvalue shares,
rolling PC1 trend/severity works, and commentary renders without breaking unavailable cases.

## Idempotence and Recovery

The implementation is additive. Re-running `run_report.py` or `run_optimization.py`
overwrites generated `stress_report.json`, `stress_commentary.txt`, and PCA CSV artifacts.
If factor data or asset history is unavailable, the PCA block returns `status =
"unavailable"` and does not change stress status.

## Artifacts and Notes

Expected new generated CSV artifacts:

    results_csv/portfolio_pca_summary_5y.csv
    results_csv/portfolio_pca_components_5y.csv
    results_csv/portfolio_pca_rolling_pc1.csv
    results_csv/portfolio_pca_pc1_factor_correlations.csv

## Interfaces and Dependencies

Use existing dependencies only: `numpy`, `pandas`, and existing project data helpers. Do
not add a scikit-learn dependency for PCA because eigen-decomposition of covariance and
correlation matrices is small, deterministic, and already available through NumPy.

In `src/stress_factors.py`, define:

    def portfolio_pca_diagnostics(
        *,
        weights: dict[str, float],
        tickers: list[str],
        analysis_end_str: str,
        window_weeks: int = FACTOR_WEEKS_5Y,
        factor_returns: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        ...

Also define pure helpers used by tests:

    def portfolio_pca_diagnostics_from_weekly_returns(
        asset_returns: pd.DataFrame,
        *,
        factor_returns: pd.DataFrame | None = None,
        window_weeks: int = FACTOR_WEEKS_5Y,
    ) -> dict[str, Any]:
        ...

Revision note 2026-04-29: initial ExecPlan created before implementation to satisfy the
project requirement for complex feature work.

Revision note 2026-04-29: updated after implementation with completed progress and
validation evidence.

Revision note 2026-04-29: updated to keep the optimization path aligned with the reporting
path so PCA is present immediately after `run_optimization.py`.
