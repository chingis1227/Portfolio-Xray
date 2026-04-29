# Add explicit factor covariance analytics

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` in the repository root.

## Purpose / Big Picture

After this change, the report can show how common risk factors move together and how that joint movement changes in stress. The user can inspect `stress_report.json.factor_covariance`, the new CSV artifacts in `results_csv/`, and `stress_commentary.txt` to see three separate regimes: normal historical covariance (`base`), crisis-only historical covariance (`stress_empirical`), and a hypothetical overlay-tightened stress covariance (`stress_overlay`). The feature is diagnostic only and does not alter optimization, mandate gates, stress pass/fail, or weight release.

## Progress

- [x] (2026-04-29 00:00+02:00) Read the existing factor regression, stress report, commentary, and export paths.
- [x] (2026-04-29 00:00+02:00) Implemented factor covariance helpers with explicit base, stress_empirical, and stress_overlay regimes.
- [x] (2026-04-29 00:00+02:00) Wired `run_report.py` to attach `stress_report["factor_covariance"]` and export CSV artifacts.
- [x] (2026-04-29 00:00+02:00) Added stress commentary output for data-driven versus hypothetical factor covariance metrics.
- [x] (2026-04-29 00:00+02:00) Updated documentation and added focused tests.
- [x] (2026-04-29 00:00+02:00) Ran focused factor covariance tests: 4 passed.
- [x] (2026-04-29 00:00+02:00) Ran adjacent factor matrix and commentary tests: 6 passed.
- [x] (2026-04-29 00:00+02:00) Ran full test suite: 47 passed.
- [x] (2026-04-29 00:00+02:00) Updated outcomes after validation.

## Surprises & Discoveries

- Observation: The existing project already has a canonical nine-factor registry and rolling beta frames in `src/stress_factors.py`.
  Evidence: `FACTOR_COLUMN_ORDER`, `BETA_ROW_ORDER`, and `compute_portfolio_rolling_factor_betas_weekly` already provide the factor ordering and beta history required for this feature.
- Observation: Existing stress covariance in `src/stress.py` is asset-level covariance for RC diagnostics, not factor covariance.
  Evidence: `_stress_covariance` accepts an asset covariance matrix and risk-on tickers, so this feature must remain separate and live under factor analytics.

## Decision Log

- Decision: Use the full nine-factor registry as the canonical factor order for all matrices, exposure vectors, RC vectors, comparisons, and CSV exports.
  Rationale: This matches existing factor beta analytics and prevents factor-specific outputs from changing shape depending on available data.
  Date/Author: 2026-04-29 / Codex.
- Decision: Treat missing portfolio beta keys as zero and record them in `exposure_vector.zero_filled_beta_keys`.
  Rationale: The report should be deterministic and auditable when some beta estimates are unavailable.
  Date/Author: 2026-04-29 / Codex.
- Decision: Keep `base`, `stress_empirical`, and `stress_overlay` as separate JSON branches and CSV files.
  Rationale: The user explicitly requested no implicit blending and explicit labels for data-driven versus hypothetical metrics.
  Date/Author: 2026-04-29 / Codex.
- Decision: Use a fixed 30% threshold for RC stability and 35% threshold for 5Y-vs-2Y covariance stability.
  Rationale: These were specified in the user-approved implementation plan.
  Date/Author: 2026-04-29 / Codex.

## Outcomes & Retrospective

Completed. The report contract now has `stress_report.json.factor_covariance` with separate `base`, `stress_empirical`, and `stress_overlay` regime blocks, portfolio factor risk, beta sensitivity, RC stability, covariance stability, and overlay deltas. The implementation writes matching CSV artifacts and stress commentary labels data-driven versus hypothetical metrics. Validation passed with 47 tests.

## Context and Orientation

`run_report.py` is the reporting entrypoint. It already computes weekly factor betas, rolling beta diagnostics, stress report JSON, and stress commentary. `src/stress_factors.py` owns factor data construction, factor beta estimation, rolling beta diagnostics, and historical factor attribution. `src/portfolio_commentary.py` turns `stress_report.json` into `stress_commentary.txt`. `src/stress.py` owns synthetic and historical stress scenarios, but its covariance logic is asset-level and should not be reused as factor covariance.

Factor covariance means a covariance matrix across common factor time series, not across assets. Portfolio factor risk is computed as `b' Sigma_f b`, where `b` is the ordered portfolio factor beta vector and `Sigma_f` is one of the factor covariance matrices.

## Plan of Work

Add helpers to `src/stress_factors.py` that build an ordered weekly factor frame, compute sample covariance with `ddof=1`, derive correlations, create the three regime blocks, apply overlay clamps to `stress_empirical`, record overlay deltas, compute portfolio factor risk and factor RC, compute beta sensitivity using rolling beta standard deviations, compare base and stress RC shares, and compare 5Y and 2Y base covariance stability.

Update `run_report.py` after rolling factor beta diagnostics so it calls `factor_covariance_analytics`, attaches the result to `stress_report["factor_covariance"]`, and writes the required CSV artifacts under `results_csv/`.

Update `src/portfolio_commentary.py` to add a compact factor covariance section that labels `base` and `stress_empirical` as data-driven, `stress_overlay` as hypothetical, and prints empirical change separately from overlay amplification.

Update `docs/docs/stress_testing_spec.md`, `README.md`, and `SPEC.md` so the report contract and artifact list are documented.

## Concrete Steps

From the repository root, run:

    python -m pytest tests/test_factor_covariance.py -vv
    python -m pytest tests/test_factor_matrix_builders.py tests/test_portfolio_commentary.py -vv
    python -m pytest

If a full test run is too slow or blocked by local environment constraints, record the focused test results and the blocker for broader validation.

## Validation and Acceptance

Acceptance requires:

- `stress_report.json.factor_covariance.base`, `.stress_empirical`, and `.stress_overlay` exist and are not blended.
- Each regime has `classification` set to `data_driven` or `hypothetical`.
- Missing betas are zero-filled and reported.
- Overlay deltas list clamped pairs and value changes.
- `portfolio_factor_risk`, `beta_sensitivity`, `portfolio_factor_rc`, `RC_stability_flag`, and `covariance_stability_check` are present.
- CSV files for factor covariance, factor correlation, factor RC, overlay deltas, and covariance stability are written.
- `stress_commentary.txt` prints data-driven versus hypothetical labels and separates empirical change from overlay amplification.

## Idempotence and Recovery

The changes are additive. Re-running `run_report.py` overwrites generated report artifacts in the normal report output directories. If validation fails, inspect the failing test and adjust the relevant helper without changing optimizer behavior.

## Artifacts and Notes

The primary generated artifacts are:

    stress_report.json
    stress_commentary.txt
    results_csv/factor_covariance_base_5y_weekly.csv
    results_csv/factor_covariance_stress_empirical_weekly.csv
    results_csv/factor_covariance_stress_overlay_weekly.csv
    results_csv/factor_correlation_base_5y_weekly.csv
    results_csv/factor_correlation_stress_empirical_weekly.csv
    results_csv/factor_correlation_stress_overlay_weekly.csv
    results_csv/portfolio_factor_rc_base.csv
    results_csv/portfolio_factor_rc_stress_empirical.csv
    results_csv/portfolio_factor_rc_stress_overlay.csv
    results_csv/factor_covariance_overlay_deltas.csv
    results_csv/factor_covariance_stability_check.csv

## Interfaces and Dependencies

`src.stress_factors.factor_covariance_analytics` must accept `analysis_end_str`, `portfolio_betas`, optional `rolling_betas_weekly`, and optional prebuilt weekly `factor_returns`. It returns a JSON-serializable dictionary suitable for `stress_report.json`. The implementation depends only on existing pandas/numpy/scipy stack already used by the project.
