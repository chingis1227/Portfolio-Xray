# Regime Factor Analytics v1 (`regime_factor_analytics_v1`)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository contains `PLANS.md` at the repository root. Maintain this document in
accordance with `PLANS.md`.

## Purpose / Big Picture

After this change, each full portfolio report run can attach a diagnostic-only
`regime_factor_analytics` block to `stress_report.json`, export eight `regime_*.csv`
tables and `regime_factor_analytics_summary.json`, and expose per-primary-regime
asset/factor covariance, asset-level nine-factor betas with HAC inference, bottom-up
portfolio factor exposure, and factor variance contribution — without modifying the
macro classifier, the optimizer, mandate gates, or stress pass/fail logic. Analysts
gain a statistical foundation for future regime-aware optimization.

## Progress

- [x] (2026-05-07) Authored ExecPlan and aligned with implementation plan (module + wiring + tests + spec).
- [x] (2026-05-07) Implemented `src/regime_factor_analytics.py` with gating, CSV helpers, stress-report slice.
- [x] (2026-05-07) Wired `run_report.py` after `macro_regime_diagnostics`; added `build_factor_matrix_monthly`.
- [x] (2026-05-07) Added `tests/test_regime_factor_analytics.py`; documented §8.8.3 in stress spec; updated AGENTS.md.

## Surprises & Discoveries

- Observation: Monthly factor returns for nine factors reuse `FACTOR_DEFINITIONS` monthly loaders via a thin `build_factor_matrix_monthly` wrapper; alignment is inner-join with asset returns and lagged regime labels from `labels_monthly`.
  Evidence: `src/stress_factors.py` `_build_factor_frame(..., monthly=True)` and `run_report.py` call path.

## Decision Log

- Decision: Store full numeric detail in CSV files and `regime_factor_analytics_summary.json`; attach a slim `regime_factor_analytics` object to `stress_report.json` (no full covariance nests, no per-asset beta tables) to control JSON size.
  Rationale: Matches contract in task §10 while keeping reproducible exports on disk.
  Date/Author: 2026-05-07 / Implementation agent.

- Decision: Default `enable_transition_split` / `enable_confidence_split` to false in `run_report.py`; confidence split remains unsupported until a per-month series exists (optional Phase 3).
  Rationale: Avoids explosive CSV size and duplicate computation unless explicitly enabled later.
  Date/Author: 2026-05-07 / Implementation agent.

## Outcomes & Retrospective

Planned outcome: diagnostic regime-specific asset/factor structure + portfolio factor risk decomposition with sample-size gating, tests green, documentation updated.

Implementation outcome (2026-05-07): `src/regime_factor_analytics.py` implements v1 gating, HAC OLS, CSV + summary JSON helpers, and a slim `stress_report` slice; `run_report.py` wires the pipeline after macro diagnostics; `build_factor_matrix_monthly` added; tests in `tests/test_regime_factor_analytics.py`; `docs/docs/stress_testing_spec.md` §8.8.3; AGENTS/SPEC/README updated. Full suite: `166 passed`.

## Context and Orientation

Key files:

- `src/stress_factors_macro.py` — `macro_two_axis_v1` labels (`labels_monthly`), lagged primary regimes, `macro_quality_status`.
- `src/stress_factors.py` — factor definitions, `build_factor_matrix`, `_build_factor_frame`, OLS/HAC helpers.
- `src/regime_factor_analytics.py` — new pipeline entry point and CSV/summary builders.
- `run_report.py` — calls macro diagnostics then regime factor analytics; writes CSVs and JSON summaries.
- `docs/docs/stress_testing_spec.md` — §8.8.3 describes outputs and contracts.

## Plan of Work

Add `build_factor_matrix_monthly` in `src/stress_factors.py`. Implement or complete
`src/regime_factor_analytics.py` per gating rules (12 / 24 / 60). Wire after the
`macro_regime_diagnostics` try-block in `run_report.py`: build monthly factor frame,
convert `labels_monthly` to aligned Series, call `regime_factor_analytics`, assign
`stress_report["regime_factor_analytics"]` via `regime_factor_analytics_for_stress_report`,
write CSVs via `regime_factor_analytics_csv_frames`, write summary JSON to
`output_dir_final`. On failure set `regime_factor_analytics_error` and continue.

## Concrete Steps

From repository root (Windows PowerShell):

1. `python -m pytest tests/test_regime_factor_analytics.py -q`
2. `python -m pytest tests/test_macro_regimes.py tests/test_macro_regime_label_quality.py -q`
3. `python run_report.py` (network/cache as usual)
4. `python -m pytest -q`

## Validation and Acceptance

- `stress_report.json` contains `regime_factor_analytics` with `version: regime_factor_analytics_v1`, four primary regimes, and no embedded full covariance matrices.
- `results_csv/` contains the eight `regime_*.csv` files when the pipeline succeeds.
- `Main portfolio/regime_factor_analytics_summary.json` (or configured `output_dir_final`) exists after a full report.
- On pipeline failure, `regime_factor_analytics_error` is set and the report still completes.

## Idempotence and Recovery

Re-running `run_report.py` overwrites regime CSVs and summary JSON. Safe to retry.

## Artifacts and Notes

Indicative artifacts: `regime_asset_covariance.csv`, `regime_factor_variance_contribution.csv`,
`regime_factor_analytics_summary.json`.

## Interfaces and Dependencies

Public symbols: `regime_factor_analytics`, `regime_factor_analytics_csv_frames`,
`regime_factor_analytics_summary`, `regime_factor_analytics_for_stress_report`,
`REGIME_FACTOR_ANALYTICS_VERSION`.

---

Revision: 2026-05-07 — Initial filled ExecPlan matching implemented v1 scope.
