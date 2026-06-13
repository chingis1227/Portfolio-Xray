# Candidate Factory Parallel Lightweight Reports

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows [PLANS.md](../../PLANS.md) in the repository root.

**Status:** Completed.

**Constraint:** runtime orchestration only. Do not change financial formulas, optimizer
mathematics, stress scenario definitions, candidate weights, output meaning, comparison semantics,
or legacy/full-report compatibility.

## Purpose / Big Picture

The Candidate Portfolio Factory already avoids per-candidate PDF rebuilds in `standard` mode, but
it still runs each candidate's `lightweight_comparison` report one after another. Optimizer cores
are fast; the remaining product bottleneck is per-candidate report and stress artifact generation.

After this plan, an operator or backend can opt into parallel `lightweight_comparison` reports for
independent candidates while preserving sequential mode as the safe fallback. A user can see the
change working by running the factory in `standard` mode with the future parallel flag and observing
that `candidate_factory_run.json` still records the same candidate statuses and comparison-ready
artifacts while wall-clock report time drops.

## Progress

- [x] (2026-05-22) Session 0 started: created this ExecPlan from the post-audit roadmap.
- [x] (2026-05-22) Session 0 completed: marked this plan Active in `docs/exec_plans/README.md`.
- [x] (2026-05-22) Session 1 completed: split lightweight report execution into a candidate-owned
  worker step and a coordinator-owned registration step; sequential behavior remains the only
  runtime mode.
- [x] (2026-05-22) Session 1 verified: `tests/test_candidate_factory.py` and
  `tests/test_candidate_manifest.py` passed with 45 tests.
- [x] (2026-05-22) Session 2 completed: added opt-in parallel lightweight report execution
  for eligible `standard` runs through `ThreadPoolExecutor`, while keeping sequential behavior
  as the default and as the fallback for `fail_fast`, per-candidate PDF mode, and Phase 3 full
  reports.
- [x] (2026-05-22) Session 2 verified: `tests/test_candidate_factory.py` and
  `tests/test_candidate_manifest.py` passed with 48 tests, including overlap, failure-continuation,
  and fail-fast fallback coverage.
- [x] (2026-05-22) Session 3 completed: added optional parallel lightweight-report
  timing/status disclosure and tests proving reverse completion still records menu-order evidence.
- [x] (2026-05-22) Session 3 verified: `tests/test_candidate_factory.py` and
  `tests/test_candidate_manifest.py` passed with 48 tests.
- [x] (2026-05-22) Session 4 completed: updated operator and source-of-truth documentation for
  opt-in parallel lightweight reports, fallback disclosure, and run-output fields.
- [x] (2026-05-22) Session 5 completed: ran focused factory/manifest verification and recorded
  the two-candidate sequential-vs-parallel timing audit in
  `docs/audits/2026-05-22_candidate_factory_parallel_reports_timing_audit.md`.
- [x] (2026-05-22) Session 5 verified: `tests/test_candidate_factory.py` and
  `tests/test_candidate_manifest.py` passed with 48 tests; the isolated smoke showed
  185.681s sequential wall clock vs 120.014s parallel wall clock for `equal_weight` and
  `risk_parity`, with comparison-critical artifacts equivalent after ignoring timestamps,
  timing fields, unordered diagnostic lists, and live floating-point noise up to `1e-3`.
- [x] (2026-05-22) Session 6 completed: full `default_v1` sequential-vs-parallel timing audit recorded in
  `docs/audits/2026-05-22_candidate_factory_parallel_reports_session06_timing_audit.md`;
  **decision: keep parallel opt-in** (do not change CLI/product default).
- [x] (2026-05-22) Session 6 verified: `tests/test_candidate_factory.py` and
  `tests/test_candidate_manifest.py` passed with 48 tests; isolated full-menu smoke showed
  1210.631s sequential vs 631.117s parallel wall clock (47.9% improvement), identical factory
  summaries and step statuses, and matching weights plus stress comparison-critical fields for all
  13 succeeded candidates.

## Surprises & Discoveries

- Observation: The pre-existing `_execute_lightweight_report` mixed candidate-local report work
  with shared orchestration mutation.
  Evidence: It called `run_portfolio_report_for_weights`, then directly appended to `steps`,
  incremented `summary`, and wrote `candidate_factory_manifest.json`.

- Observation: Parallel workers can finish in a different order than the candidate menu, so the
  coordinator must wait on futures in the submitted menu order before writing final run evidence.
  Evidence: Session 2 test `test_parallel_lightweight_reports_overlap_and_keep_menu_order` blocks
  two fake reports at a barrier, proves both are active at once, and asserts final `steps` order is
  `equal_weight`, then `risk_parity`.

- Observation: Live back-to-back report smokes can differ in deeper diagnostic-only stress blocks
  even when candidate weights and comparison-facing fields match.
  Evidence: Session 5's full recursive JSON comparison found drift mainly under
  `stress_report.portfolio_pca` residual PCA and
  `factor_covariance.comparison.overlay_amplification`, while `weights.json`, `snapshot_10y.json`
  comparison-facing fields, `stress_suite_results`, `stress_scorecard_v1`, `stress_conclusions`,
  summaries, and manifests remained equivalent within the documented tolerance.

## Decision Log

- Decision: Start with a boundary refactor before introducing `ThreadPoolExecutor`.
  Rationale: The worker must write only candidate-owned artifacts before parallel execution is safe.
  Date/Author: 2026-05-22 / Codex.

- Decision: Keep `sequential` as the only implemented mode through Session 1.
  Rationale: This session should be behavior-preserving and should not introduce executor or CLI
  compatibility risk.
  Date/Author: 2026-05-22 / Codex.

- Decision: Use `ThreadPoolExecutor` in the future Session 2 rather than `ProcessPoolExecutor`.
  Rationale: The report path shares a large pandas-based `CandidateRunContext`; Windows process
  spawning and pickling would be expensive and riskier than threads for this I/O and numpy/pandas
  workload.
  Date/Author: 2026-05-22 / planning audit.

- Decision: Expose parallel lightweight reports as opt-in `--parallel-lightweight-reports` plus an
  optional `--lightweight-report-workers` cap.
  Rationale: The default operator path remains unchanged, while advanced runs can choose parallel
  report generation without changing formulas, weights, or comparison semantics.
  Date/Author: 2026-05-22 / Codex.

- Decision: Treat `--fail-fast`, `--pdf-mode per_candidate`, and any Phase 3 full report export as
  automatic sequential fallbacks even when parallel is requested.
  Rationale: These modes either need immediate stop-on-failure behavior or have report/PDF side
  effects outside the Session 2 lightweight-report scope.
  Date/Author: 2026-05-22 / Codex.

- Decision: Keep `--parallel-lightweight-reports` **opt-in** after Session 6 full-menu timing evidence.
  Rationale: Session 6 showed ~48% wall-clock improvement and matching run statuses plus
  comparison-critical artifacts for succeeded candidates, but a default switch is deferred until
  more production soak, portfolio-first review adoption, and operator sign-off; sequential mode
  remains the safe default and automatic fallback.
  Date/Author: 2026-05-22 / Codex.

## Outcomes & Retrospective

Session 0 established this checked-in handoff plan and made it the active project-level ExecPlan.

Session 1 prepared the code for future parallelism without enabling it. The lightweight report path
now has a worker function that reads `weights.json`, runs `run_portfolio_report_for_weights` with
`report_profile=lightweight_comparison`, writes only candidate-owned artifacts, and returns one step
dictionary. The coordinator function then appends factory evidence, updates counts, and persists
the run-level and per-candidate manifests. This is the required safety boundary before Session 2.
Verification used the project `.venv` and an explicit workspace-local pytest temp directory:
`python -m pytest tests\test_candidate_factory.py tests\test_candidate_manifest.py -q
--basetemp='tmp\pytest_candidate_parallel_session1'`, which reported 45 passed.

Session 2 added the first opt-in parallel runtime path. `run_candidate_factory` now accepts
`parallel_lightweight_reports` and `lightweight_report_workers`, and the CLI exposes them as
`--parallel-lightweight-reports` and `--lightweight-report-workers`. Eligible `standard` runs submit
candidate-local lightweight report workers to a `ThreadPoolExecutor`; the coordinator records their
results in candidate menu order and remains the only writer of run-level manifests and summaries.
The sequential path remains the default and is also used automatically for `fail_fast=True`,
`pdf_mode=per_candidate`, and Phase 3 full report exports. Verification command:
`python -m pytest tests\test_candidate_factory.py tests\test_candidate_manifest.py -q
--basetemp='tmp\pytest_candidate_parallel_session2'`, which reported 48 passed.

Session 3 added optional run-level `parallel_lightweight_report_summary` disclosure. When parallel
lightweight reports are requested, the factory now records requested/effective status, fallback
reasons, worker count, submitted and registered candidate ids, and parallel wall-clock seconds
without changing the existing per-step timing buckets or aggregate `timing_summary`. Tests now force
`risk_parity` to finish before `equal_weight` while asserting submitted, registered, and final
factory step evidence remains in candidate menu order; fallback disclosure is also covered for
`fail_fast=True`. Verification command:
`python -m pytest tests\test_candidate_factory.py tests\test_candidate_manifest.py -q
--basetemp='tmp\pytest_candidate_parallel_session3'`, which reported 48 passed.

Session 4 synchronized operator and source-of-truth documentation without changing runtime code.
`candidate_factory_spec.md` now owns the CLI flags, eligibility matrix, fallback reasons, and
`parallel_lightweight_report_summary` contract. `candidate_factory_layer_spec.md`,
`operational_runbook.md`, `OUTPUTS.md`, `TESTING.md`, `README.md`, `ROADMAP.md`,
`KNOWN_ISSUES.md`, and `CHANGELOG.md` now route operators to the opt-in Phase 2 report mode while
still stating that parallel candidate builders and Phase 3 full reports remain outside this scope.

Session 5 recorded live timing evidence for the opt-in parallel lightweight-report path without
changing runtime code. The focused factory/manifest suite passed with 48 tests. An isolated
two-candidate smoke using `equal_weight` and `risk_parity` completed successfully in both sequential
and parallel modes; the parallel run used two workers and recorded `status: parallel` with no
fallback reasons. Sequential wall clock was 185.681 seconds, while parallel wall clock was 120.014
seconds, a 35.4% improvement on this machine. The audit also records that comparison-critical
candidate artifacts matched after excluding volatile timestamps/timing and tolerating live
floating-point noise, while full recursive `stress_report.json` equality is not a reliable live
acceptance check because deeper diagnostic-only PCA/covariance blocks drifted between separate
data/factor refreshes.

Session 6 closed the ExecPlan with a full `default_v1` sequential-vs-parallel timing audit on
isolated roots. Focused tests passed with 48 tests. Sequential wall clock was 1210.631 seconds;
parallel wall clock was 631.117 seconds (47.9% faster) with four workers and
`parallel_lightweight_report_summary.status: parallel`. Both runs ended `partial_success` with
identical summaries (13 succeeded, 2 failed robust MV builders missing lambda calibration, 1
`robust_scenario` skipped for Main prerequisites). All 13 succeeded candidates had matching
`weights.json` and stress comparison-critical fields; factory run/manifest step statuses matched.
**Product decision:** keep parallel opt-in; sequential remains the default and rollback path.

## Context and Orientation

The factory entry point is `run_candidate_factory.py`. It calls `src/candidate_factory.py`
`run_candidate_factory`, which iterates candidate ids from profiles such as `core_v1` and
`default_v1`.

`standard` execution mode has two phases. Phase 1 builds weights in-process through
`src/candidate_weights.py` and writes files such as `weights.json` and
`candidate_weights_build.json` under each candidate folder. Phase 2 calls
`run_report.py` `run_portfolio_report_for_weights` with `report_profile=lightweight_comparison` so
comparison can read real `snapshot_10y.json` and `stress_report.json` without full HTML,
commentary, rolling beta plots, or per-candidate PDF work.

The shared run-level files are `{output_dir_final}/candidate_factory_manifest.json`,
`{output_dir_final}/candidate_factory_run.json`, and `{output_dir_final}/candidate_factory_run.txt`.
These must be written by the coordinator, not by parallel workers. A candidate-owned artifact folder
is a folder such as `equal-weight portfolio/` or `risk parity portfolio/`; a worker may write only
inside that folder.

## Plan of Work

Session 0 creates this plan and updates `docs/exec_plans/README.md` so future chats know this is
the active project-level plan.

Session 1 changes only the internal structure of `src/candidate_factory.py`. Refactor
`_execute_lightweight_report` so it delegates report construction to a worker helper and then
registers the returned step through a coordinator helper. The worker must not receive `steps`,
`summary`, `manifest`, or `manifest_dir`. It may still write candidate-local artifacts such as
`summary.json`, `builder_runtime_timing.json`, and `candidate_weights_build.json`.

Session 2 added opt-in parallel execution with `ThreadPoolExecutor`. It runs only for
`execution_mode=standard`, `fail_fast=False`, no per-candidate PDF, and no Phase 3 full reports.
Results are registered in candidate menu order, not completion order.

Session 3 will add timing disclosure. The existing work-time buckets stay intact; new wall-clock
parallel fields will be optional and must not break older readers.

Sessions 4 through 6 update docs, verify live behavior, and decide whether parallel should remain
opt-in or become a product default.

## Concrete Steps

Run commands from the repository root:

    D:\Desktop\CURSOR TULA DIAGNOSTICS

For Session 1, after editing:

    python -m pytest tests/test_candidate_factory.py tests/test_candidate_manifest.py -q

For Session 2, after editing:

    python -m pytest tests/test_candidate_factory.py tests/test_candidate_manifest.py -q --basetemp='tmp\pytest_candidate_parallel_session2'

For Session 4 documentation sync:

    python scripts/verify_docs.py

For Session 5 verification and timing evidence:

    .\.venv\Scripts\python.exe -m pytest tests/test_candidate_factory.py tests/test_candidate_manifest.py -q --basetemp='tmp\pytest_candidate_parallel_session5'

    Run the isolated Python API smoke recorded in
    docs/audits/2026-05-22_candidate_factory_parallel_reports_timing_audit.md. It creates
    tmp/candidate_parallel_session05/sequential and tmp/candidate_parallel_session05/parallel,
    runs equal_weight and risk_parity in standard mode, and writes
    tmp/candidate_parallel_session05/session05_smoke_summary.json.

If the bundled runtime is needed on this Windows workspace, use the project-approved Python command
prefix already used in prior sessions.

## Validation and Acceptance

Session 1 is accepted when all existing factory behavior remains sequential and tests show that the
candidate-local report worker does not write the run-level factory manifest. A failed lightweight
report must still become a normal failed factory step, and `fail_fast` behavior must remain
unchanged.

Session 2 is accepted because tests prove two fake lightweight reports can overlap in time in
parallel mode, one failed candidate does not stop the run when `fail_fast=False`, and `fail_fast=True`
forces the sequential fallback.

Session 4 is accepted when operator and source-of-truth docs describe `--parallel-lightweight-reports`,
`--lightweight-report-workers`, automatic sequential fallback conditions, and
`parallel_lightweight_report_summary`, and `python scripts/verify_docs.py` passes.

Session 5 is accepted because sequential and parallel smoke runs completed with comparison-critical
candidate artifacts equivalent after ignoring timestamps, timing fields, unordered diagnostic lists,
and live floating-point noise up to `1e-3`, and the timing audit shows material wall-clock
improvement. Full recursive `stress_report.json` equality is explicitly not part of the live
acceptance evidence because deeper diagnostic-only PCA/covariance blocks can drift between separate
live data/factor refreshes.

## Idempotence and Recovery

All sessions should be additive and safe to rerun. If the parallel path fails in a future session,
operators must be able to use sequential mode with the same CLI and artifact contracts. Do not delete
candidate outputs or cache directories as part of this plan unless a test fixture explicitly creates
temporary files under `tmp_path`.

## Artifacts and Notes

Important files for this plan:

- `src/candidate_factory.py`
- `run_candidate_factory.py`
- `src/portfolio_review_workflow.py`
- `tests/test_candidate_factory.py`
- `tests/test_candidate_manifest.py`
- `docs/specs/candidate_factory_spec.md`
- `docs/specs/candidate_factory_layer_spec.md`
- `OUTPUTS.md`
- `TESTING.md`
- `docs/operational_runbook.md`

## Interfaces and Dependencies

At the end of Session 1, `src.candidate_factory` must expose internal helpers equivalent to:

    def _run_lightweight_report_worker(...) -> dict[str, Any]:
        ...

    def _record_lightweight_report_step(...) -> None:
        ...

These helpers are private implementation details. The public CLI and `run_candidate_factory`
signature changed in Session 2 to accept opt-in parallel report execution:

    run_candidate_factory(..., parallel_lightweight_reports=False, lightweight_report_workers=None)

The CLI now accepts:

    python run_candidate_factory.py --execution-mode standard --parallel-lightweight-reports --lightweight-report-workers 4

Revision note (2026-05-22 / Codex): updated this plan after completing Session 2 so the living
progress, decisions, outcomes, verification command, and current interface match the implemented
parallel lightweight-report path.

Revision note (2026-05-22 / Codex): updated this plan during Session 4 so documentation-sync
progress, outcomes, validation, and operator/source-of-truth scope match the shipped opt-in
parallel lightweight-report path.

Revision note (2026-05-22 / Codex): updated this plan during Session 5 with focused verification,
isolated sequential-vs-parallel timing evidence, audit-link routing, and the live diagnostic drift
caveat discovered while comparing full stress reports.

Revision note (2026-05-22 / Codex): closed this plan after Session 6 with full `default_v1` timing
evidence, the opt-in default decision, and links to the Session 06 timing audit.
