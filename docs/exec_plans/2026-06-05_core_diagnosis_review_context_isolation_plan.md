# Core Diagnosis ReviewRunContext Isolation Runtime Fix

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document is maintained according to `PLANS.md` in the repository root.

## Purpose / Big Picture

The operator command `python run_portfolio_review.py --mode core --skip-candidates` should refresh the current portfolio diagnosis path needed for Blocks 1-5 handoff readiness without pulling candidate-generation, Decision Verdict, optimizer, or non-core shared factor/macro preload work. Today this command can move past the FRED risk-free blocker and then stall while preparing `ReviewRunContext`, a shared context originally intended to amortize monthly, daily, factor, synthetic-stress, and macro inputs across candidate review runs. After this fix, the diagnosis-only core command should materialize `Main portfolio/analysis_subject/` and diagnosis-only tombstones using only the report work needed for the product handoff gate. A human can see the fix by running the command and then seeing the readiness gate return `Block 4 v3 live validation: OK`, `live core E2E validation: OK`, and `docs verification: OK`.

This plan intentionally does not change optimizer behavior, Candidate Generation, Decision Verdict formulas, Stress Lab scenario logic, or Block 4 classification/launchpad/builder logic. It only changes orchestration: whether a diagnosis-only core run asks `run_report.py` to preload shared review context before materializing the analysis subject.

## Progress

- [x] (2026-06-05) Investigated where `--mode core --skip-candidates` enables `ReviewRunContext` and identified the minimal orchestration seam.
- [x] (2026-06-05) Created this standalone runtime-fix ExecPlan with root cause, target files, tests, and validation commands.
- [x] (2026-06-05) Implemented the minimal skip/flag change so diagnosis-only core materialization does not preload `ReviewRunContext` by default.
- [x] (2026-06-05) Added focused tests for the diagnosis-only plan-builder flag and the explicit materialization no-context path.
- [x] (2026-06-05) Rejected and removed a too-broad equity-only/non-core factor fast path because it affected ordinary `analysis_subject` factor/stress contracts.
- [ ] Run the diagnosis command and final readiness gate after a separate, explicitly scoped solution exists for the remaining in-report factor-matrix FRED blocker.

## Surprises & Discoveries

- Observation: `run_report.py` already has a `--no-review-run-context` switch and `run_materialize_analysis_subject_report(..., use_review_run_context=False)` path.
  Evidence: `run_report.py` parses `--no-review-run-context` and sets `subject_use_context = False`; `should_use_review_run_context_for_subject` returns the explicit override when provided.

- Observation: `src/portfolio_review_workflow.py` currently forces `--use-review-run-context` for every core portfolio-review diagnosis step, including diagnosis-only runs created by `run_portfolio_review.py --mode core --skip-candidates`.
  Evidence: in `build_portfolio_review_plan`, after building `subject_argv`, the code appends `--use-review-run-context` whenever `resolved_mode == "core"`.

- Observation: `ReviewRunContext` is heavier than the Blocks 1-5 diagnosis-only readiness gate requires because its preparation calls candidate-style shared preloads.
  Evidence: `src/candidate_run_context.py::prepare_review_run_context` calls `prepare_candidate_run_context(..., preload_factor_stress=True, preload_invariant_metrics=True)` and then `load_review_macro_panel(...)`. The factor preload builds daily panels, weekly factor betas, and factor matrices; the macro preload fetches the macro indicator panel.

- Observation: Existing tests encode the old behavior and must be updated intentionally, not bypassed accidentally.
  Evidence: `tests/test_portfolio_review_workflow.py::test_default_plan_materializes_subject_before_candidates` currently asserts `--use-review-run-context` is present for core mode, and `tests/test_analysis_subject_materialization.py::test_should_use_review_run_context_for_subject_defaults` currently asserts that `review_mode="core"` defaults to `True`.


- Observation: The safe `ReviewRunContext` isolation is not sufficient to make the live command complete. Once `--no-review-run-context` is active, the command still reaches full in-report factor diagnostics and can block in `compute_asset_factor_betas_from_daily_returns -> build_factor_matrix -> fetch_real_rates_weekly -> FRED`.
  Evidence: a faulthandler trace during `run_report.py --materialize-analysis-subject --output-profile site_api --review-mode core --no-review-run-context` showed the stack inside `src.data_fred.fetch_fred_series` called from `src.stress_factors.fetch_real_rates_weekly`, not inside `prepare_review_run_context`.

- Observation: An attempted equity-only/non-core factor skip was too broad and has been removed.
  Evidence: the condition applied to `analysis_subject + lightweight + site_api + no ReviewRunContext`, which also covers ordinary core product diagnosis materialization. That would change Block 2.3 Factor Exposure / Stress Lab surfaces, so it was reverted/limited out of this plan.

- Observation: Focused tests pass after limiting scope back to orchestration-only.
  Evidence: `.
venv\Scripts\python.exe -m pytest tests/test_portfolio_review_workflow.py tests/test_analysis_subject_materialization.py tests/test_factor_diagnostics_wiring.py -q` returned `43 passed`.

## Decision Log

- Decision: Treat this as an orchestration fix, not a data-loader, factor-model, macro-model, optimizer, candidate, Decision Verdict, Stress Lab, or Block 4 logic change.
  Rationale: The blocker is not incorrect factor/macro math; it is that a diagnosis-only readiness command pulls a broad shared preload that is unnecessary for proving Blocks 1-5 handoff readiness.
  Date/Author: 2026-06-05 / Codex.

- Decision: Prefer using the existing explicit `--no-review-run-context` path for diagnosis-only core runs instead of deleting `ReviewRunContext` or changing its internals first.
  Rationale: The repository already has a safe opt-out flag. Reusing it gives the smallest diff and keeps shared context available for candidate/core_fast workflows that may still benefit from it.
  Date/Author: 2026-06-05 / Codex.

- Decision: Keep `run_report.py --use-review-run-context` as an opt-in escape hatch and keep `run_report.py --review-mode full` without shared context by default.
  Rationale: Operators may still need to debug or benchmark the shared context path. The runtime-fix only changes what `run_portfolio_review.py --mode core --skip-candidates` asks for.
  Date/Author: 2026-06-05 / Codex.


- Decision: Do not use equity-only factor betas as an implicit fast path for ordinary core/product diagnosis.
  Rationale: Full product diagnosis must preserve the full factor matrix contract for Block 2.3 Factor Exposure and Stress Lab. Equity-only is acceptable only as a separately named, explicitly requested limited validation/fallback path with metadata warning, not as the default `site_api` analysis-subject behavior.
  Date/Author: 2026-06-05 / Codex.

## Outcomes & Retrospective

The orchestration part of this plan is implemented: diagnosis-only core plans now pass `--no-review-run-context`, and `run_report.py` treats shared context as explicit opt-in. The broader live hang is not fully solved by this plan because the remaining blocker is inside the full report factor matrix path, not `ReviewRunContext`. It establishes that the root cause is forced `ReviewRunContext` preload from the portfolio review workflow builder. Success will be recorded here after code/tests/docs are changed and the live readiness gate is rerun.

## Context and Orientation

The repository root is `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`. Use Windows PowerShell from that directory. Use `\.venv\Scripts\python.exe` if it exists; otherwise follow the repository's normal Python setup.

The command in scope is:

    .\.venv\Scripts\python.exe run_portfolio_review.py --mode core --skip-candidates

`run_portfolio_review.py` does not directly run report logic. It builds a list of subprocess commands through `src/portfolio_review_workflow.py::build_portfolio_review_plan`, then executes those steps. The first step is always diagnosis materialization through `run_report.py --materialize-analysis-subject`.

`ReviewRunContext` means a shared in-memory bundle prepared before report materialization. It is defined in `src/candidate_run_context.py`. It wraps a `CandidateRunContext` and may contain a macro panel. Preparing it currently loads monthly data, daily return panels, weekly factor beta inputs, invariant metrics, synthetic stress preparation inputs, and macro indicator data. That can be useful for candidate review batches but is too broad for the diagnosis-only readiness gate.

`diagnosis-only core` means current portfolio diagnostics under `Main portfolio/analysis_subject/` plus diagnosis-only root tombstones. It should not generate candidate portfolios, compare candidates, or issue a Decision Verdict. For this plan, it also should not preload non-core factor/macro/shared context merely because `--review-mode core` was selected.

## Root Cause

The immediate root cause is in `src/portfolio_review_workflow.py::build_portfolio_review_plan`: for every `resolved_mode == "core"`, it appends `--use-review-run-context` to the diagnosis step. This includes `run_portfolio_review.py --mode core --skip-candidates`, even though that is diagnosis-only and has no candidate batch to amortize.

The secondary root cause is in `run_report.py::should_use_review_run_context_for_subject`: if no explicit override is passed, it returns `True` for `review_mode="core"`. That default matches the old `core_fast` assumption but is unsafe for diagnosis-only readiness because it means a plain core analysis-subject materialization can choose broad shared preload.

The heavy work starts in `run_report.py::run_materialize_analysis_subject_report` when `want_shared_context` is true. It calls `prepare_review_run_context`. That function in `src/candidate_run_context.py` calls `prepare_candidate_run_context` with `preload_factor_stress=True` and `preload_invariant_metrics=True`, and then calls `load_review_macro_panel`. This is the factor/macro/shared preload that can stall after the FRED risk-free fallback has succeeded.

## Files to Change

Change `src/portfolio_review_workflow.py` first. In `build_portfolio_review_plan`, stop appending `--use-review-run-context` for diagnosis-only core steps. The minimal recommended behavior is:

- if `skip_candidates` is true, append `--no-review-run-context` to `subject_argv` when `resolved_mode == "core"`;
- if `skip_candidates` is false and the team still wants candidate/core_fast shared context, either leave the existing `--use-review-run-context` only for that candidate path or make it explicit behind a named function/condition such as `should_preload_review_context = resolved_mode == "core" and not skip_candidates`;
- keep full mode unchanged: it should not append `--use-review-run-context`.

Change `run_report.py` only if needed to make the default safer. The smallest acceptable change is to update `should_use_review_run_context_for_subject` so `review_mode="core"` no longer defaults to `True` unless explicitly requested. If this is done, update the CLI help for `--review-mode` and `--use-review-run-context` so it no longer says core uses shared context by default. If the workflow builder always passes either `--no-review-run-context` or `--use-review-run-context`, this default is less critical, but changing it reduces future accidental calls to broad preload.

Do not change `src/candidate_run_context.py` unless tests reveal a blocker. `prepare_review_run_context` can stay heavy because this plan is about not calling it for diagnosis-only core, not about redefining what the shared context does.

Update only the smallest owning docs if behavior changes are documented outside this plan. Likely candidates are `docs/runtime_entrypoints.md`, `docs/product_flow_operator_guide.md`, or `docs/specs/portfolio_review_workflow_spec.md` if they currently say core diagnosis preloads shared context. Do not update generated outputs unless a validation command refreshes them and the user explicitly wants generated artifacts committed.

## Tests to Add or Update

Add or update focused tests before broad live runs.

In `tests/test_portfolio_review_workflow.py`, update `test_default_plan_materializes_subject_before_candidates` or add a new explicit test for diagnosis-only:

    def test_core_skip_candidates_plan_disables_review_run_context(tmp_path: Path) -> None:
        plan = build_portfolio_review_plan(
            _cfg(),
            project_root=tmp_path,
            review_mode="core",
            skip_candidates=True,
            skip_pdf=True,
        )
        subject_argv = plan.steps[0].argv
        assert [step.stage for step in plan.steps] == ["diagnosis"]
        assert "--materialize-analysis-subject" in subject_argv
        assert "--no-review-run-context" in subject_argv
        assert "--use-review-run-context" not in subject_argv

If candidate/core mode should still use shared context, add or keep a separate assertion that `skip_candidates=False` may include `--use-review-run-context`. If the safer default is chosen for all core materialization, update the existing assertion to expect no `--use-review-run-context`.

In `tests/test_analysis_subject_materialization.py`, update `test_should_use_review_run_context_for_subject_defaults` if `run_report.py` default is changed. The desired default after this fix is:

    assert run_report.should_use_review_run_context_for_subject(review_mode="core") is False
    assert run_report.should_use_review_run_context_for_subject(
        review_mode="core",
        use_review_run_context=True,
    ) is True
    assert run_report.should_use_review_run_context_for_subject(review_mode="full") is False

Add a focused no-preload test for `run_materialize_analysis_subject_report` if the file already has monkeypatch-based materialization tests. The test should monkeypatch `run_report.prepare_review_run_context` to raise an AssertionError, call `run_materialize_analysis_subject_report(..., review_mode="core", use_review_run_context=False)`, and assert that the materialization proceeds to the monkeypatched `run_portfolio_report_for_weights` without calling the shared context function. This proves the skip flag protects the diagnosis path.

Do not add tests that require live FRED, live macro indicators, optimizer execution, candidate generation, or Decision Verdict generation for the unit-level proof.

## Plan of Work

First, make the plan builder express the correct runtime intent. Edit `src/portfolio_review_workflow.py::build_portfolio_review_plan` so the diagnosis step for `skip_candidates=True` passes `--no-review-run-context` instead of `--use-review-run-context`. Keep the code simple and readable. A named boolean is preferable to nested conditionals because future operators need to see why candidate and diagnosis-only paths differ.

Second, make `run_report.py` robust against direct accidental use. If no code outside `run_portfolio_review.py` depends on `review_mode="core"` defaulting to shared context, change `should_use_review_run_context_for_subject` to return `False` unless `use_review_run_context=True` is explicitly passed. If this breaks too many existing tests that represent intended candidate-run behavior, keep the default as-is but ensure the portfolio review plan passes `--no-review-run-context` for diagnosis-only. In either case, the acceptance criterion is that the scoped command does not log `Preparing ReviewRunContext for analysis_subject materialization.`

Third, update tests to lock the behavior. Start with the plan-builder test because it is the true CLI contract for `run_portfolio_review.py --mode core --skip-candidates`. Then update the materialization default/override tests only if `run_report.py` changes.

Fourth, run focused tests, then run the runtime command with a reasonable timeout. The runtime command should not hang in shared factor/macro context. It may still fail on external market data if no approved cache exists; if so, record that as a separate external-data blocker. The expected success path is exit code 0 and no log line saying `Preparing ReviewRunContext for analysis_subject materialization.`

Fifth, run the readiness gate again. If green, this blocker is closed and the project can move to Candidate Generation work.

## Concrete Steps

Run all commands from:

    D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА

Inspect the current plan builder and shared context default:

    Select-String -Path src\portfolio_review_workflow.py,run_report.py -Pattern "use-review-run-context|no-review-run-context|should_use_review_run_context_for_subject|prepare_review_run_context" -Context 3,5

After implementation, run focused tests:

    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_review_workflow.py tests/test_analysis_subject_materialization.py -q

Then run the diagnosis-only runtime command:

    .\.venv\Scripts\python.exe run_portfolio_review.py --mode core --skip-candidates

Expected useful evidence after the fix includes no line like:

    Preparing ReviewRunContext for analysis_subject materialization.

and the command should complete instead of stalling in shared factor/macro preload.

Then run the readiness gate:

    .\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis
    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Expected success transcript:

    Block 4 v3 live validation: OK
    live core E2E validation: OK
    docs verification: OK

## Validation and Acceptance

The fix is accepted when all of the following are true:

The plan-builder test proves that `run_portfolio_review.py --mode core --skip-candidates` builds a diagnosis-only plan whose first step includes `--no-review-run-context` and does not include `--use-review-run-context`.

The materialization test proves that when `use_review_run_context=False`, `run_materialize_analysis_subject_report` does not call `prepare_review_run_context`.

The live command `run_portfolio_review.py --mode core --skip-candidates` completes without hanging after FRED in factor/macro/shared preload. If it fails for an unrelated external data source, the terminal evidence must show that it did not enter `Preparing ReviewRunContext for analysis_subject materialization.` and the external data failure must be recorded separately.

The final readiness gate is green: `validate_block_4_live.py --refresh-diagnosis`, `verify_live_core_e2e.py --profile diagnosis_only`, and `verify_docs.py` all return success.

## Idempotence and Recovery

The tests are safe to repeat. `run_portfolio_review.py --mode core --skip-candidates` may refresh generated artifacts under `Main portfolio/`; those generated outputs are not source of truth and should not be committed unless explicitly requested. If the command is interrupted, rerun it after confirming no unrelated generated files are being staged. Do not delete caches as part of this plan unless a test explicitly creates a temporary cache.

If the change accidentally disables shared context for candidate runs and that is not desired, recover by making the condition explicit: `skip_candidates=True` gets `--no-review-run-context`, while `skip_candidates=False and resolved_mode == "core"` may keep `--use-review-run-context`.

## Artifacts and Notes

Investigation evidence from 2026-06-05:

    src/portfolio_review_workflow.py:
        if resolved_mode == "core":
            subject_argv.append("--use-review-run-context")

    run_report.py:
        def should_use_review_run_context_for_subject(...):
            if use_review_run_context is not None:
                return use_review_run_context
            mode = (review_mode or "core").strip().lower()
            return mode == "core"

    src/candidate_run_context.py:
        def prepare_review_run_context(...):
            factory_context = prepare_candidate_run_context(
                ..., preload_factor_stress=True, preload_invariant_metrics=True, ...
            )
            macro_panel, macro_panel_meta = load_review_macro_panel(...)

These snippets show why a diagnosis-only core command can pull non-core shared preload.

## Interfaces and Dependencies

Keep these interfaces stable:

`src.portfolio_review_workflow.build_portfolio_review_plan(...)` must continue returning a `PortfolioReviewPlan` whose first step materializes `analysis_subject` through `run_report.py --materialize-analysis-subject`.

`run_report.run_materialize_analysis_subject_report(..., use_review_run_context=False)` must continue accepting an explicit false override and must pass `run_context=None` into `run_portfolio_report_for_weights`.

`run_report.run_materialize_analysis_subject_report(..., use_review_run_context=True)` must remain available as an explicit opt-in path for debugging or future shared-context review runs.

`src.candidate_run_context.prepare_review_run_context(...)` should not be changed by this plan unless a test exposes an unrelated bug. Its heavy preload behavior remains valid for workflows that explicitly request it.

Revision note, 2026-06-05: Created standalone runtime-fix ExecPlan after investigating the core diagnosis hang. The plan identifies forced `--use-review-run-context` in `src/portfolio_review_workflow.py` and the core-default shared-context behavior in `run_report.py` as the root cause, and proposes a minimal diagnosis-only skip using the existing `--no-review-run-context` mechanism.

Revision note, 2026-06-05: Implemented and verified the safe `ReviewRunContext` opt-out. Removed a too-broad equity-only/non-core factor fast path after confirming it would affect ordinary product diagnosis factor/stress contracts. Remaining runtime blocker is full in-report factor matrix FRED access, which requires a separate explicitly scoped solution or limited validation path.
