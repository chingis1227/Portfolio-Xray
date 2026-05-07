# Regime Label Quality Check for `macro_two_axis_v1`

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository contains `PLANS.md` at the repository root. Maintain this document in
accordance with `PLANS.md`.

## Purpose / Big Picture

After this change, `stress_report.json.macro_regime_diagnostics` will include a dedicated
diagnostic block that tells a reviewer whether regime labels are usable before relying on
regime-specific betas, covariance, and RC interpretation. The check is still diagnostic-only:
it does not alter optimizer decisions, mandate checks, or stress pass/fail status.

A user will see new artifacts in run outputs: one JSON summary and three CSV files for regime
quality, plus a short “Regime Label Quality Check” section in `stress_commentary.txt`.

## Progress

- [x] (2026-05-07 18:55Z) Reviewed current macro regime pipeline, stress spec section 8.8.2, and commentary/test surfaces.
- [x] (2026-05-07 19:01Z) Implemented regime quality diagnostics in `src/stress_factors_macro.py` and attached `regime_label_quality_check` to macro payload.
- [x] (2026-05-07 19:02Z) Added artifact export wiring: JSON summary in `run_report.py` / `run_optimization.py`; CSV artifacts from `macro_regime_csv_frames`.
- [x] (2026-05-07 19:02Z) Extended stress commentary macro section with “Regime Label Quality Check” and required caution warnings.
- [x] (2026-05-07 19:03Z) Added tests in `tests/test_macro_regime_label_quality.py` and expanded `tests/test_portfolio_commentary.py`.
- [x] (2026-05-07 19:05Z) Ran targeted tests and full `run_report.py`; verified new artifacts are produced.

## Surprises & Discoveries

- Observation: `src/stress_factors.py` already provides thin shims to `src/stress_factors_macro.py`, so implementing quality logic in the macro module keeps call sites stable.
  Evidence: `macro_regime_diagnostics` / `macro_regime_csv_frames` wrappers exist around lines ~3997 and ~4025 in `src/stress_factors.py`.

## Decision Log

- Decision: Put all label-quality computations in `src/stress_factors_macro.py` and expose only final payload/artifacts to callers.
  Rationale: Keeps macro diagnostics cohesive and avoids duplicating business logic in `run_report.py` and `run_optimization.py`.
  Date/Author: 2026-05-07 / Codex.

- Decision: Implement episode sanity checks as directional plausibility checks over fixed historical windows, with “intuitive/questionable/insufficient_data” outcomes and notes, without forcing labels.
  Rationale: Matches requirement to assess economic sense without hardcoding outcomes into the classifier.
  Date/Author: 2026-05-07 / Codex.

## Outcomes & Retrospective

Planned outcome:

- Regime label quality status is explicit and reproducible in JSON/CSV outputs.
- Commentary warns whenever any regime has `<24` observations or switching is too noisy.
- Diagnostics remain non-binding.
- Implementation outcome (2026-05-07): achieved. `stress_report.json.macro_regime_diagnostics` now contains `regime_label_quality_check`, artifacts are exported, and commentary includes mandatory caution language for low n_obs / noisy switching.

## Context and Orientation

Relevant files:

- `src/stress_factors_macro.py`: computes `macro_two_axis_v1` diagnostics and CSV frames.
- `src/stress_factors.py`: exposes thin shim functions used by runners.
- `run_report.py` and `run_optimization.py`: call macro diagnostics and currently export only macro CSV frames.
- `src/portfolio_commentary.py`: renders macro diagnostics text into `stress_commentary.txt`.
- `tests/test_macro_indicators.py`: existing macro unit tests; new quality tests should live alongside.
- `tests/test_portfolio_commentary.py`: verifies stress commentary content.

The new quality block must stay diagnostic-only and should be consumed by analysts before
trusting regime-specific analytics. It is not a gating mechanism.

## Plan of Work

Add a regime-label quality builder in `src/stress_factors_macro.py` that consumes:
monthly labeled regime history (`labels_monthly`), and per-row metadata (`coverage_tier`,
`confidence_level`, available/missing blocks). It will compute per-regime sample depth,
episode-duration stats, switching/noise stats, metadata distributions, and directional sanity
checks over major historical windows.

Attach this block to the macro payload as `regime_label_quality_check`, then extend
`macro_regime_csv_frames` to emit:
`regime_label_quality_by_regime.csv`, `regime_label_episode_history.csv`,
`regime_label_stability_summary.csv`.

In `run_report.py` and `run_optimization.py`, write
`regime_label_quality_summary.json` from that block into the variant final output folder.

In `src/portfolio_commentary.py`, add a concise “Regime Label Quality Check” subsection under
Macro regime diagnostics with required cautions:
if any regime has `<24` observations, warn that regime-specific betas/covariance/RC are
cautious-use only; if switching is noisy, warn classifier may be noisy.

## Concrete Steps

From repository root:

1. Implement quality builder + payload integration in `src/stress_factors_macro.py`.
2. Extend macro CSV frame exporter in the same module.
3. Update `run_report.py` and `run_optimization.py` to export JSON summary.
4. Update `src/portfolio_commentary.py` rendering.
5. Add tests in `tests/test_macro_regime_label_quality.py` and extend
   `tests/test_portfolio_commentary.py`.
6. Run tests:
   - `python -m pytest tests/test_macro_regime_label_quality.py tests/test_portfolio_commentary.py`
   - `python -m pytest tests/test_macro_indicators.py`
7. Run one integration check:
   - `python run_report.py`

## Validation and Acceptance

Acceptance is met when:

- `stress_report.json.macro_regime_diagnostics.regime_label_quality_check` exists with:
  per-regime quality stats, switching metrics, sanity checks, metadata distributions, and
  overall warnings.
- Output artifacts include:
  `regime_label_quality_summary.json`,
  `regime_label_quality_by_regime.csv`,
  `regime_label_episode_history.csv`,
  `regime_label_stability_summary.csv`.
- `stress_commentary.txt` contains “Regime Label Quality Check” and prints caution text when:
  any regime has `<24` observations and/or switching is too noisy.
- Tests cover thresholds, episode logic, switch counts, and metadata distributions.

## Idempotence and Recovery

All computations are additive diagnostics over generated run data; re-running the same commands
overwrites artifacts deterministically. If any step fails, fix code and rerun the same command;
no destructive migrations are involved.

## Artifacts and Notes

Expected new files after `python run_report.py`:

- `Main portfolio/regime_label_quality_summary.json`
- `results_csv/regime_label_quality_by_regime.csv`
- `results_csv/regime_label_episode_history.csv`
- `results_csv/regime_label_stability_summary.csv`

## Interfaces and Dependencies

Planned new internal helpers in `src/stress_factors_macro.py`:

- `_regime_episode_runs(labels: pd.Series) -> list[dict[str, Any]]`
- `_regime_quality_from_labels(...) -> dict[str, Any]`
- `_regime_metadata_distributions(...) -> dict[str, Any]`
- `_regime_macro_sanity_checks(...) -> dict[str, Any]`
- `_regime_label_quality_check(...) -> dict[str, Any]`

Payload interface:

- `macro_regime_diagnostics["regime_label_quality_check"]` (diagnostic-only summary object)

CSV exporter interface:

- `macro_regime_csv_frames(report)` additionally returns DataFrames keyed by:
  `regime_label_quality_by_regime.csv`,
  `regime_label_episode_history.csv`,
  `regime_label_stability_summary.csv`.

Revision note (2026-05-07): Updated this living ExecPlan after implementation and validation to reflect completed steps, concrete outputs, and final behavior for restartability.
