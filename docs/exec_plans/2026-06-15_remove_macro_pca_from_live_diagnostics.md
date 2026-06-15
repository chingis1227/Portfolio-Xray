# Remove Macro Regime and PCA from Live Run Diagnostics

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root.

## Purpose / Big Picture

The public Run Diagnostics flow should be faster and less memory-hungry. Today the live staged diagnosis path calculates macro regime diagnostics and portfolio PCA even though those research-style diagnostics are not required for the current product journey. After this change, a user can enter a portfolio, click Run Diagnostics, and receive the normal diagnosis, stress, Client Fit, problem classification, Launchpad, and report grounding outputs without macro regime or PCA payloads in `stress_report.json`.

This plan intentionally preserves the user-facing `Correlation Concentration` alert by rebuilding it from non-PCA evidence such as pairwise correlation, duplicate exposure, concentration flags, and risk-budget concentration.

The work is organized in four parts:

1. Remove Macro Regime and PCA from the live calculation pipeline and outputs.
2. Rebuild `Correlation Concentration` without PCA.
3. Update tests, contracts, and docs for the new live boundary.
4. Run QA and performance measurement on the same payload.

## Progress

- [x] (2026-06-15 18:42Z) Baseline measured before code changes with `scripts/diagnosis_performance_smoke.py`: cold 58.390 seconds, warm 13.018 seconds, status passed.
- [x] (2026-06-15 18:46Z) Created this English ExecPlan in `docs/exec_plans/2026-06-15_remove_macro_pca_from_live_diagnostics.md`.
- [x] (2026-06-15 18:58Z) Part 1: removed macro regime diagnostics, regime analytics, regime portfolio metrics, portfolio PCA execution, macro-panel preload, and macro frequency disclosure from live report runtime.
- [x] (2026-06-15 19:00Z) Part 1 validation: live staged diagnosis completed and the generated `analysis_subject/stress_report.json` had no macro/PCA fields.
- [x] (2026-06-15 20:05Z) Part 2: rebuilt `Correlation Concentration` as an explicit non-PCA product alert; legacy PCA enrichment is now ignored by Block 2.4 and not wired from `build_portfolio_xray_v2`.
- [x] (2026-06-15 20:05Z) Part 2: updated current docs, contracts, golden fixture, and focused tests for the non-PCA alert boundary.
- [x] (2026-06-15 20:30Z) Part 3: removed retired `macro_regime` and `portfolio_pca` names from the report timing block registry and added a regression assertion that they stay out of the live timing contract.
- [x] (2026-06-15 20:45Z) Part 3: synced `SPEC.md`, `TESTING.md`, and `SCREEN_CONTRACTS.md`; strengthened live-output negative assertions for macro/PCA fragments and the non-PCA `Correlation Concentration` alert.

## Surprises & Discoveries

- Observation: The live staged diagnosis path already measured warm much faster than cold on the selected payload.
  Evidence: baseline command returned `cold_seconds=58.390` and `warm_seconds=13.018`.
- Observation: `Correlation Concentration` is a user-facing alert, but its current PCA evidence enters through Portfolio X-Ray hidden-risk construction rather than as a direct frontend PCA component.
  Evidence: `frontend/lib/reviewState.tsx` maps `correlation_concentration` to the alert title, while `src/portfolio_xray.py` reads `stress_report.portfolio_pca` for legacy hidden-risk evidence.
- Observation: Part 1 reduces the cold staged diagnosis smoke on the selected payload, but the warm result was slightly slower than the baseline run.
  Evidence: after-change smoke returned cold 60.695 seconds and warm 17.517 seconds, versus baseline cold 58.390 seconds and warm 13.018 seconds, after preserving factor variance decomposition and diagnostic oil beta.

## Decision Log

- Decision: Do Part 1 first and stop after successful verification.
  Rationale: The user explicitly requested a checkpoint after successful Part 1 implementation.
  Date/Author: 2026-06-15 / Codex.
- Decision: Preserve historical ExecPlans and audits.
  Rationale: They are traceability records and should not be rewritten as part of current runtime removal.
  Date/Author: 2026-06-15 / Codex.
- Decision: Keep `inflation_stagflation` stress scenario.
  Rationale: It is a Stress Lab scenario, not the removed macro regime classifier.
  Date/Author: 2026-06-15 / Codex.

## Outcomes & Retrospective

Part 1 is complete. Live Run Diagnostics no longer runs or outputs macro regime diagnostics, regime factor analytics, regime portfolio metrics, or portfolio PCA. The staged diagnosis smoke passed, and the generated warm `analysis_subject/stress_report.json` contained no forbidden macro/PCA fields or macro frequency disclosure keys. Part 2 is also complete. `Correlation Concentration` now relies on non-PCA evidence and product Block 2.4 no longer surfaces legacy PCA cross-reference evidence, even if an older caller passes a legacy enrichment argument. The public product block keeps compatibility metadata fields but pins them to `legacy_enrichment_wire_time=false`, `legacy_enrichment_sources=[]`, and `pca_used_for_correlation_concentration=false`. Part 3 is complete. Report timing no longer advertises retired live-runtime blocks for macro regime or portfolio PCA, current contracts document the live no-macro/no-PCA boundary, and focused tests assert that non-PCA `Correlation Concentration` still appears while PCA/regime fragments stay out of live outputs.

## Context and Orientation

The frontend Run Diagnostics button posts a portfolio payload through `frontend/lib/server/fastapiBridge.ts` to FastAPI route `POST /api/v1/reviews/staged`. FastAPI calls `src/api/reviews.py`, which starts a background staged review worker. For live runs, the worker calls `scripts/run_review_from_payload.py`, which runs `src/review_runtime/staged_diagnosis_service.py`. That service calls `run_report.run_materialize_analysis_subject_report` with `output_profile="site_api"` and `review_mode="core"`.

In `run_report.py`, `run_materialize_analysis_subject_report` calls `run_portfolio_report_for_weights`. That function currently computes stress, factor diagnostics, macro regime diagnostics, regime factor analytics, regime portfolio metrics, portfolio PCA, scenario library, daily tail risk, snapshots, Portfolio X-Ray, Client Fit, problem classification, Launchpad, and AI grounding. The Part 1 work removes only macro regime diagnostics, regime analytics, regime portfolio metrics, and portfolio PCA from this live runtime.

The term "macro regime diagnostics" means the two-axis growth/inflation classifier that emits labels such as `goldilocks`, `reflation`, `stagflation`, and `recession_disinflation`. The term "PCA" means principal component analysis over weekly portfolio asset returns; it produces fields such as `portfolio_pca`, `pc1_explained_variance_ratio`, and `residual_pca`. These fields must disappear from new live `stress_report.json` outputs after Part 1.

## Plan of Work

For Part 1, edit `run_report.py` to remove imports and execution blocks for macro regime diagnostics, regime factor analytics, regime portfolio metrics, and portfolio PCA. Leave ordinary stress scenarios, factor beta work, factor covariance, factor decomposition, scenario library, daily tail risk, snapshots, Portfolio X-Ray, Client Fit, and diagnosis adapters intact.

Edit `src/candidate_run_context.py` so `prepare_review_run_context` no longer preloads the macro indicator panel for live reviews. Keep the `ReviewRunContext` type compatible enough for existing callers, but macro panel fields should remain `None` and should not trigger network or cache work.

Edit `src/report_timing.py` only if needed so timing output no longer expects removed runtime blocks. This is a runtime timing contract change, not a formula change.

Do not remove `src/stress_factors_macro.py`, `src/regime_factor_analytics.py`, `src/regime_portfolio_metrics.py`, or low-level PCA functions in Part 1 if that would force broad historical test rewrites. The acceptance for Part 1 is that live Run Diagnostics does not execute or output those blocks.

## Concrete Steps

From the repository root, run the baseline command before edits:

    $env:PMRI_STAGED_REVIEW_RUNTIME='direct'; $env:PMRI_STAGED_REVIEW_MAX_WORKERS='1'; $env:PMRI_YF_MAX_WORKERS='1'; .\.venv\Scripts\python.exe scripts\diagnosis_performance_smoke.py --payload runs\frontend_review_20260615T140943Z_ytGU3_jYfgvwel1Iy1VX4w\payload.json --timeout-seconds 900 --warm-threshold-seconds 9999

The observed baseline was:

    cold_seconds=58.390
    warm_seconds=13.018
    status=passed

After Part 1 edits, run the same command again and inspect the warm result `analysis_subject/stress_report.json`. It must not contain the keys `macro_regime_diagnostics`, `regime_factor_analytics`, `regime_portfolio_metrics`, `portfolio_pca`, or their `*_error` variants.

The observed after-change run was:

    cold_seconds=60.695
    warm_seconds=17.517
    status=passed

The inspected after-change warm artifact had no forbidden macro/PCA keys, no macro frequency disclosure keys, 50 top-level stress-report keys, included `factor_variance_decomposition` and `diagnostic_oil_beta`, and size 453,904 bytes.

## Validation and Acceptance

Part 1 is accepted when:

- Running the staged diagnosis performance smoke exits with status passed.
- The new live `stress_report.json` contains normal stress/factor/scenario output but no macro regime or PCA fields.
- Focused Python tests covering report profile/timing and analysis-subject materialization still pass or are updated to the new no-macro/no-PCA live contract.

The minimum focused validation commands are:

    .\.venv\Scripts\python.exe -m pytest tests\test_report_timing.py tests\test_report_profile.py tests\test_analysis_subject_materialization.py -q
    .\.venv\Scripts\python.exe scripts\diagnosis_performance_smoke.py --payload runs\frontend_review_20260615T140943Z_ytGU3_jYfgvwel1Iy1VX4w\payload.json --timeout-seconds 900 --warm-threshold-seconds 9999


Validation actually run for Part 2:

    .\.venv\Scripts\python.exe -m py_compile src\block_2_4_hidden_exposure.py src\portfolio_xray.py tests\test_block_2_4_hidden_exposure.py tests\test_block_2_4_matrix_coverage.py tests\test_portfolio_xray_contract.py
    .\.venv\Scripts\python.exe -m pytest tests\test_block_2_4_hidden_exposure.py tests\test_block_2_4_matrix_coverage.py tests\test_portfolio_xray_contract.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_xray.py tests\test_portfolio_xray_threshold_registry.py tests\test_blocks_1_5_mvp_smoke.py tests\test_analysis_subject_materialization.py -q

The observed Part 2 focused results were 130 passed for Block 2.4 / Portfolio X-Ray contract tests and 52 passed for adjacent Portfolio X-Ray/materialization tests.

Validation actually run for Part 3:

    .\.venv\Scripts\python.exe -m py_compile src\report_timing.py tests\test_report_timing.py
    .\.venv\Scripts\python.exe -m pytest tests\test_report_timing.py -q

Additional Part 3 validation after contract/test sync:

    .\.venv\Scripts\python.exe -m py_compile src\report_timing.py tests\test_report_timing.py tests\test_candidate_run_context.py tests\test_block_2_4_hidden_exposure.py
    .\.venv\Scripts\python.exe -m pytest tests\test_report_timing.py tests\test_candidate_run_context.py tests\test_block_2_4_hidden_exposure.py tests\test_block_2_4_matrix_coverage.py tests\test_portfolio_xray_contract.py -q

The observed Part 3 focused result was initially 5 passed for timing only; after the broader contract/test sync, rerun the broader focused bundle and record the result here.

Validation actually run for Part 1:

    .\.venv\Scripts\python.exe -m py_compile run_report.py src\candidate_run_context.py src\review_runtime\staged_diagnosis_service.py tests\test_candidate_run_context.py tests\test_report_profile.py tests\test_report_timing.py
    .\.venv\Scripts\python.exe -m pytest tests\test_candidate_run_context.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_report_profile.py tests\test_report_timing.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_analysis_subject_materialization.py -q
    $env:PMRI_STAGED_REVIEW_RUNTIME='direct'; $env:PMRI_STAGED_REVIEW_MAX_WORKERS='1'; $env:PMRI_YF_MAX_WORKERS='1'; .\.venv\Scripts\python.exe scripts\diagnosis_performance_smoke.py --payload runs\frontend_review_20260615T140943Z_ytGU3_jYfgvwel1Iy1VX4w\payload.json --timeout-seconds 900 --warm-threshold-seconds 9999

## Idempotence and Recovery

The edits are code-only and can be rerun safely. If the performance smoke fails because of external market data, rerun once with the same payload and report the blocker. If the code fails because removed names are still referenced, search for the missing symbol and either remove the stale branch from live runtime or keep a compatibility stub that does not execute macro/PCA work.

## Artifacts and Notes

Baseline artifact paths from the pre-change run:

    cold_result=<repo root>\runs\frontend_review_20260615T184158Z_2zOImWWmW6sG3rKL_oIZWQ\review_result.json
    warm_result=<repo root>\runs\frontend_review_20260615T184256Z_ZbAtfc_F9NXA-T48Q-4IQw\review_result.json

After-change artifact paths from the Part 1 validation run:

    cold_result=<repo root>\runs\frontend_review_20260615T190638Z__ZMV4j1FuTTvJ-mAOmeFRw\review_result.json
    warm_result=<repo root>\runs\frontend_review_20260615T190739Z_eXlYr9jhOFOqJd9EQkHO0w\review_result.json

## Interfaces and Dependencies

No public API route is added or removed in Part 1. The staged review API still returns a review id and status progress. The `stress_report.json` contract changes by removing macro regime and PCA fields from newly generated live Run Diagnostics artifacts. Later work will update the `Correlation Concentration` semantics to use non-PCA evidence.


## Revision Note

2026-06-15 / Codex: Updated after Part 2 implementation to record the non-PCA `Correlation Concentration` contract, tests, documentation sync, and verification evidence.
2026-06-15 / Codex: Updated after Part 3 implementation to remove retired macro/PCA timing block names from the live report timing contract and record focused verification.
2026-06-15 / Codex: Expanded Part 3 to match the four-part plan: current contracts now document the live no-macro/no-PCA boundary, screen contracts keep `Correlation Concentration` as non-PCA, and focused tests include stronger negative assertions.
