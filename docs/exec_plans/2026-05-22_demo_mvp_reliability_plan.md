# Demo MVP Reliability Repair

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` in the repository root.

**Status:** Completed (2026-05-22).

## Purpose / Big Picture

The user needs one stable, repeatable, demo-ready command path for the current eight-ticker
portfolio: SPY 10%, QQQ 13%, GLD 9%, SLV 9%, BND 16%, SCHD 17%, SCHP 13%, and TLT 13%.
The intended path is existing portfolio-first analysis through decision artifacts, not new
features, new formulas, new stress scenarios, new optimizer methods, or UI work.

After this repair, a human should be able to run `python run_portfolio_review.py --mode core
--skip-pdf`, inspect `Main portfolio/`, and see clear factor diagnostics, stress attribution,
factory rebuild or reuse semantics, clean text outputs, and internally consistent decision
artifacts. The proof must come from generated artifacts, not only unit tests.

## Progress

- [x] (2026-05-22 00:00Z) Read repository workflow rules, stress specification, candidate factory
  specification, portfolio review workflow specification, and output contracts.
- [x] (2026-05-22 00:00Z) Created this scoped ExecPlan for reliability repair.
- [x] Reproduce or inspect the current factor, stress attribution, factor covariance, factory,
  text QA, and decision package failure modes.
- [x] Implement minimal repairs in existing owning modules.
- [x] Add or update focused tests that lock the repaired contracts.
- [x] Update owning documentation for any output contract or command behavior change.
- [x] Run the fresh proof path for the eight-ticker portfolio and inspect the real artifacts.
- [x] Record final outcomes and close this plan in the register.

## Surprises & Discoveries

- Observation: The working tree already contains many modified generated outputs and several
  modified source/config files before this repair starts.
  Evidence: `git status --short` shows modified generated candidate folders, PDF sidecars, root
  outputs, and source files such as `src/cache.py`, `src/config_schema.py`, and `src/data_loader.py`.

- Observation: Sandbox network restrictions can make the factor path degrade to equity-only, but
  the canonical matrix loads when network access is available.
  Evidence: the network-authorized check loaded `equity`, `real_rates`, `inflation`, `usd`,
  `commodity`, `vix`, `us_growth`, and `oil`; the authorized proof-run then produced
  `factor_attribution_scope="multi_factor"` and eight beta keys in `stress_report.json`.

- Observation: The preferred core demo command may reuse fresh candidate snapshots.
  Evidence: `candidate_factory_run.json` reports `succeeded=0`, `skipped_existing=6`,
  `builder_invoked=0`, and `reused_existing_snapshot=6`.

## Decision Log

- Decision: Keep the repair inside existing Blocks 1-5 and generated decision artifact contracts.
  Rationale: The user explicitly asked to stop scope expansion and not change formulas,
  methodology, optimizers, scenarios, or UI.
  Date/Author: 2026-05-22 / Codex.

- Decision: Treat generated outputs as proof artifacts but not as source edits to curate manually.
  Rationale: `OUTPUTS.md` says generated files are evidence; the user asked for a proof run, so
  generated files may change during verification, but fixes belong in source code, tests, and docs.
  Date/Author: 2026-05-22 / Codex.

## Outcomes & Retrospective

Completed. The final network-authorized proof-run completed with:

- `stress_report.json`: `factor_attribution_scope="multi_factor"`, beta coverage ratio `1.0`,
  populated factor PnL attribution for all eight scenarios, restored 5Y/10Y factor regression
  panels, and available factor covariance analytics.
- `candidate_factory_run.json`: explicit execution summary showing reused snapshots versus rebuilt
  candidates.
- `decision_package_summary.json` and `.txt`: aligned partial-score wording and factory reuse
  disclosure.
- `scripts/scan_generated_outputs.py`: passed after the fresh proof-run.

Remaining caveat: the preferred demo command is clean, but by default it may reuse fresh existing
candidate snapshots. A full rebuild requires the optional `run_candidate_factory.py --profile
default_v1 --no-skip-existing --then-compare` path and takes longer.

## Context and Orientation

The portfolio-first orchestrator is `run_portfolio_review.py`, which delegates to
`src/portfolio_review_workflow.py`. It materializes `analysis_subject` before candidates, then calls
the candidate factory and comparison pipeline.

Stress and factor diagnostics are mostly built in `run_report.py`, `src/stress.py`, and
`src/stress_factors.py`. `stress_report.json` is the main generated artifact for factor diagnostics,
synthetic/historical stress rows, factor covariance analytics, and user-readable stress commentary.

Candidate factory behavior is implemented in `src/candidate_factory.py` and exposed by
`run_candidate_factory.py`. The source of truth is `docs/specs/candidate_factory_spec.md`.

Comparison, scorecards, selection, action, and decision package are built from
`src/candidate_comparison.py`, `src/portfolio_health_score.py`, `src/robustness_scorecard.py`,
`src/selection_engine.py`, `src/action_engine.py`, and `src/decision_package_reporting.py`.

Generated text quality is checked through `scripts/scan_generated_outputs.py` and related tests.

## Plan of Work

First, inspect current source and generated artifacts to identify why canonical factor loading,
stress attribution, and factor covariance analytics degrade. Fix only clear bugs or missing
disclosure in the current path. Do not change formulas or stress scenario definitions.

Second, harden candidate factory reporting so `--no-skip-existing`, resume manifest reuse, and
candidate reuse/rebuild status are explicit in `candidate_factory_run.json`, the text summary, and
comparison disclosure.

Third, repair decision package wording so partial scorecard evidence is not mislabeled as unscored
and the JSON and TXT surfaces agree.

Fourth, ensure generated output QA catches common mojibake markers and can be run as part of the
proof checklist.

Finally, run the eight-ticker proof path and inspect the real JSON/TXT artifacts listed in the
user's acceptance checklist.

## Concrete Steps

Work from repository root `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`.

Run focused searches and artifact inspection with `rg` and small Python one-liners when needed.
Run focused pytest files around changed modules before the final CLI proof. Run the proof command:

    python run_portfolio_review.py --mode core --skip-pdf

When validating full rebuild semantics, also use:

    python run_candidate_factory.py --profile default_v1 --no-skip-existing --then-compare

The optional full command can be long-running; if it is not feasible in one turn, the final answer
must state exactly what ran and what remains unverified.

## Validation and Acceptance

Acceptance is artifact-based. After the fresh proof path, inspect these files under
`Main portfolio/` and `Main portfolio/analysis_subject/`:

- `analysis_subject/run_metadata.json`
- `analysis_subject/portfolio_xray.json`
- `analysis_subject/stress_report.json`
- `candidate_factory_run.json`
- `candidate_comparison.json`
- `portfolio_health_score.json`
- `robustness_scorecard.json`
- `selection_decision.json`
- `action_plan.json`
- `decision_package_summary.json`
- `decision_package_summary.txt`

The final checklist must state whether each artifact is valid and whether text outputs are clean.

## Idempotence and Recovery

The proof commands are intended to be repeatable. Candidate factory may reuse fresh candidates when
skip-existing is enabled; this must be disclosed. `--no-skip-existing` means attempt rebuilds unless
the resume manifest intentionally skips completed work, which must be disclosed as resume behavior.

No destructive git commands are part of this plan. Existing dirty files are not reverted.

## Artifacts and Notes

Final evidence will be recorded in this plan and in the assistant's final response.

## Interfaces and Dependencies

Use the existing Python project dependencies from `requirements.txt` and the repository's current
test suite. Do not add new runtime dependencies unless a clear existing bug cannot be fixed without
one; that is not expected for this repair.
