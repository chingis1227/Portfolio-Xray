# Code Migration to Diagnosis-First Portfolio MRI ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

Portfolio MRI is migrating from a CLI/file/report-first implementation toward a diagnosis-first product architecture. The target product flow is:

    Input portfolio
    -> Portfolio X-Ray
    -> Stress Test Lab
    -> Problem Classification
    -> Candidate Launchpad
    -> Portfolio Alternatives Builder
    -> Current vs Candidate Comparison
    -> Decision Verdict
    -> AI Commentary
    -> Monitoring / What Changed

The current repository already has important portfolio-first infrastructure. `run_portfolio_review.py` diagnoses `analysis_subject` before candidate generation, `run_report.py` produces the core diagnostics, `run_candidate_factory.py` orchestrates existing candidate builders, and `run_compare_variants.py` writes comparison and downstream decision artifacts. The migration must preserve these working capabilities while adding thin product-oriented layers around them.

The key principle is conservative migration. Do not rewrite calculators. Do not change metric formulas, stress scenarios, optimizer objectives, optimizer math, existing JSON fields, existing schemas, CLI behavior, or legacy flows. Add explicit orchestration and adapter layers, one focused session at a time, so the product can support diagnosis-only, one-candidate, and shortlist workflows without breaking current backend evidence generation.

## Current System Summary

The default current entrypoint is `run_portfolio_review.py`. It loads the validated config, builds a plan through `src.portfolio_review_workflow`, materializes `analysis_subject` diagnostics through `run_report.py --materialize-analysis-subject`, optionally runs `run_candidate_factory.py`, and writes comparison and decision-package outputs either through factory `--then-compare` or `run_compare_variants.py`.

`run_report.py` is the main diagnostics and reporting engine. Its `run_portfolio_report_for_weights()` function accepts fixed weights and writes snapshots, metrics, stress evidence, Portfolio X-Ray, commentary, and report artifacts. This function is a backend calculator and report writer, not a product workflow state manager.

`run_candidate_factory.py` is a controlled batch orchestration layer. It runs or reuses existing candidate builders, supports profiles such as `core_fast`, `core_v1`, and `default_v1`, writes `candidate_factory_run.json`, and can chain comparison. It should remain implemented as backend, advanced, or research infrastructure. It is not the same thing as the target Candidate Launchpad or on-demand Portfolio Alternatives Builder.

`run_compare_variants.py` writes `candidate_comparison.json` and downstream artifacts through `src.candidate_comparison.write_candidate_comparison_outputs()`. Those downstream artifacts include robustness scorecard, Portfolio Health Score, Selection/No-Trade decision, action plan, monitoring diff, decision journal, and decision package summary. The current technical decision contract is `selection_decision.json` from `src.selection_engine`, not product-facing Decision Verdict terminology.

`run_optimization.py` remains the legacy policy optimizer compatibility path. It must not be deleted, and it must not become the default diagnosis-first front door.

## Scope and Guardrails

This ExecPlan covers the code migration program from current CLI/file-driven Portfolio MRI toward the diagnosis-first architecture. It does not implement all sessions immediately. It defines the work so future sessions can be executed safely and independently.

The migration must obey these guardrails:

- Do not change formulas.
- Do not change optimizer math.
- Do not change stress scenarios.
- Do not change scoring formulas.
- Do not rename schemas.
- Do not rename JSON fields.
- Do not change CLI behavior until a focused session explicitly approves and tests it.
- Do not delete legacy flows.
- Do not delete or remove batch candidate factory.
- Do not treat generated outputs as source.
- Do not confuse product-facing Decision Verdict with current Selection Engine contracts.
- Do not claim target modules are implemented until verified in code and specs.
- Do not mix generated-output cleanup into migration work.

## Dirty Working Tree Blocker

Code migration must not begin until the dirty working tree is classified. Current inspection showed unrelated modified source/config/generated files and untracked files. Examples include `config.yml`, `config.yml.example`, `requirements.txt`, modified candidate output folders, generated PDFs, `src/action_engine.py`, `src/cache.py`, `src/candidate_comparison.py`, `src/config_schema.py`, `src/data_loader.py`, `src/data_trust_signals.py`, `src/live_core_e2e.py`, `src/selection_engine.py`, and untracked IBKR/data provider files and tests.

Before any code changes, classify each dirty group as one of: keep, revert, ignore, commit separately, or archive generated outputs. Do not use `git add -A`. Stage only explicitly reviewed files when staging is later requested.

## Architecture Direction

The target architecture should be implemented by layering product workflow artifacts and adapters over current backend calculators.

The Input Portfolio layer should reuse config validation, analysis setup, input assumptions, analysis subject materialization, data providers, cache, and data trust signals.

The Portfolio X-Ray layer should reuse `portfolio_xray.json` and `src.portfolio_xray`. It should remain diagnostic and must not issue investment verdicts.

The Stress Test Lab layer should reuse `stress_report.json`, stress scorecards, conclusions, hedge-gap evidence, scenario library evidence, and data-quality disclosures. It reports vulnerability and confidence; it does not generate trades.

The Problem Classification layer is target work. It should be a deterministic adapter over existing X-Ray and stress evidence. It should produce top user-understandable problems and suggested paths without changing any formulas.

The Candidate Launchpad layer is target work. It should create cards or data entries that let a user choose an improvement hypothesis. Launchpad cards are not portfolios and contain no weights.

The Portfolio Alternatives Builder layer is target work. It should generate one selected candidate by calling existing candidate builders and recording provenance. Batch factory remains a separate backend/advanced path.

The Current vs Candidate Comparison layer should initially be an adapter over canonical `candidate_comparison.json`, not a replacement for that contract. The MVP product should focus on `analysis_subject` versus one selected candidate or a shortlist, while the full multi-row comparison remains available for advanced use.

The Decision Verdict layer should map existing Selection/No-Trade output into product-facing language. It must not rename `selection_decision.json`, `selection_decision_v1`, or `decision_status`.

The AI Commentary layer should be a grounded explanation contract over deterministic JSON evidence. AI must not calculate metrics, set statuses, invent evidence, or contradict source artifacts.

The Monitoring / What Changed layer should reuse V1 monitoring and decision journal outputs for a light MVP summary. Full workspace monitoring remains advanced/later.

## Milestones

### Milestone 1: Inventory and state foundation

This milestone documents and freezes the current runtime before behavior changes. It classifies the dirty working tree, records current entrypoints and generated artifacts, and introduces a pure workflow state model. At the end of the milestone, future agents should know whether a run is diagnosis-only, one-candidate, or multiple-candidate without changing existing command behavior.

Acceptance evidence is a docs/audit inventory, a workflow state spec, unit tests for state classification, and passing portfolio review workflow tests.

### Milestone 2: Diagnosis-first product artifacts

This milestone adds deterministic product artifacts for Problem Classification and Candidate Launchpad. These artifacts read existing X-Ray and stress evidence. They do not calculate new metrics, build portfolios, or change existing JSON contracts. At the end of the milestone, a diagnosed portfolio can produce understandable problem labels and suggested hypothesis cards before candidate generation.

Acceptance evidence is new specs, new JSON artifacts if approved, unit tests with fixture inputs, and docs link verification.

### Milestone 3: On-demand candidate and focused comparison

This milestone adds a Portfolio Alternatives Builder wrapper and a current-vs-candidate comparison adapter. The builder delegates to existing candidate construction code. The comparison adapter reads canonical comparison evidence and narrows it to `analysis_subject` versus one selected candidate or a shortlist. At the end of the milestone, the MVP path no longer needs to expose a full 16-candidate research table by default.

Acceptance evidence is mocked or fixture-based builder tests, comparison adapter tests for one-candidate and shortlist cases, and unchanged candidate comparison contract tests.

### Milestone 4: Verdict, commentary, monitoring, and compatibility cleanup

This milestone maps Selection/No-Trade to product-facing Decision Verdict, defines AI Commentary grounding, and integrates light Monitoring / What Changed. It also documents that batch candidate factory remains advanced/research/backend. At the end of the milestone, the product-facing narrative can explain diagnosis, candidate trade-offs, verdict, and monitoring without changing technical schemas.

Acceptance evidence is verdict mapping tests, commentary grounding tests, monitoring projection tests, docs verification, and a dry-run of the portfolio review command.

## Session Plan

### Session 01 - Current runtime and entrypoint inventory

Objective: freeze a verified architecture inventory and add no behavioral changes.

Files likely affected: `CODE_MIGRATION_PLAN.md`, this ExecPlan progress section, and possibly a new docs-only audit if approved.

Files not to touch: all `src/*.py`, root `run_*.py`, `config.yml`, generated output folders.

Implementation steps: run `git status --short`; inspect CLI help for key entrypoints without executing workflows; read portfolio review, candidate factory, candidate comparison, selection, output, and monitoring specs; record current runtime flow and generated artifacts.

Tests/checks: `python scripts/verify_docs.py`.

Rollback risk: very low because the session is docs-only.

Expected output: verified current architecture inventory and dirty-state blocker list.

Commit scope: docs-only inventory. Do not include generated outputs.

### Session 02 - Define workflow state model: diagnosis-only, one candidate, multiple candidates

Objective: add a deterministic model for workflow state without changing CLI behavior.

Files likely affected: a new workflow state spec, a new pure helper module with a session-approved name, and focused tests.

Files not to touch: optimizer modules, candidate formulas, existing JSON schemas.

Implementation steps: define `diagnosis_only`, `one_candidate`, and `multiple_candidates`; derive state from existing artifacts/options; add pure helper functions; add fixture-based tests.

Tests/checks: workflow state tests and `python -m pytest tests/test_portfolio_review_workflow.py`.

Rollback risk: low if not wired into runtime decisions yet.

Expected output: state model, docs, tests, and no behavior change.

Commit scope: state helper, spec, and tests only.

### Session 03 - Make diagnosis-first flow explicit

Objective: expose diagnosis-first state in review orchestration while preserving existing flags and command behavior.

Files likely affected: `src/portfolio_review_workflow.py`, possibly `run_portfolio_review.py` help text, workflow spec, tests.

Files not to touch: `run_report.py` calculation logic, candidate builders, optimization math.

Implementation steps: preserve current CLI flags; annotate review plans with state metadata; map `--skip-candidates` to diagnosis-only; prove `analysis_subject` remains first and `run_optimization.py` is not called by default.

Tests/checks: `python -m pytest tests/test_portfolio_review_workflow.py tests/test_portfolio_first_e2e_offline.py`.

Rollback risk: low to medium because orchestration metadata can affect tests.

Expected output: explicit diagnosis-first workflow state with unchanged command behavior.

Commit scope: orchestration metadata, docs, and tests.

### Session 04 - Add or formalize Problem Classification artifact

Objective: create a deterministic artifact that translates existing X-Ray and stress evidence into top portfolio problems and suggested paths.

Files likely affected: a new Problem Classification module with a session-approved name, a new owning spec with a session-approved path, tests, and `OUTPUTS.md` if a generated artifact is added.

Files not to touch: X-Ray formulas, stress formulas, optimizer modules, existing JSON field names.

Implementation steps: define schema and filename; map existing evidence to labels such as high volatility, high drawdown, concentration, weak hedge behavior, and current acceptable; include evidence references and warnings; wire writer only after source artifacts exist.

Tests/checks: new unit tests with fixture X-Ray/stress documents; `python scripts/verify_docs.py`.

Rollback risk: medium because wording must not imply binding advice.

Expected output: `problem_classification` evidence generated from existing diagnostics.

Commit scope: new artifact module, spec, tests, and minimal wiring.

### Session 05 - Add Candidate Launchpad data layer

Objective: create launchpad cards from Problem Classification output without building portfolios.

Files likely affected: a new Candidate Launchpad module with a session-approved name, a new spec, tests, and output docs if a new artifact is written.

Files not to touch: candidate formulas, factory profiles, comparison schema.

Implementation steps: define launchpad card schema; map problems to suggested goals and methods; include "keep current and monitor" when appropriate; ensure cards contain no weights.

Tests/checks: unit tests for problem-to-card mappings; docs verification.

Rollback risk: low to medium because the layer is additive.

Expected output: deterministic Candidate Launchpad data for product surfaces.

Commit scope: launchpad module, spec, and tests.

### Session 06 - Add Portfolio Alternatives Builder wrapper around existing candidate builders

Objective: add an on-demand builder interface for one selected candidate while delegating to existing builders.

Files likely affected: a new Portfolio Alternatives Builder wrapper module with a session-approved name, wrapper tests, and spec.

Files not to touch: optimizer formula internals, `src.portfolio_variants` math, existing root candidate scripts unless only wrapping/importing.

Implementation steps: define simple request model; map methods to existing candidate IDs/builders; return provenance and artifact paths; keep batch factory separate.

Tests/checks: unit tests with mocked builders; no live optimizer runs unless separately approved.

Rollback risk: medium because wrappers can accidentally change behavior if they bypass existing paths.

Expected output: one-candidate builder API reusing current builders.

Commit scope: wrapper, spec, tests.

### Session 07 - Make Current vs Candidate the primary MVP comparison path

Objective: add a product-facing comparison adapter for `analysis_subject` versus selected candidate or shortlist.

Files likely affected: a new current-vs-candidate adapter module with a session-approved name, spec, tests, and output docs if a new artifact is written.

Files not to touch: canonical `candidate_comparison_v1` field names and selection formulas.

Implementation steps: read canonical comparison; select baseline and requested candidate rows; project existing metrics, stress, turnover, confidence, and warnings; preserve full comparison table for advanced/backend use.

Tests/checks: adapter tests for one candidate, shortlist, missing candidate, and degraded candidate.

Rollback risk: medium; canonical comparison semantics must remain unchanged.

Expected output: MVP comparison view centered on current versus selected candidate.

Commit scope: adapter, spec, tests, optional report wiring.

### Session 08 - Map Selection Engine / No-Trade technical outputs to product-facing Decision Verdict

Objective: create product-facing Decision Verdict language from existing Selection/No-Trade evidence without schema renames.

Files likely affected: a new Decision Verdict mapping module with a session-approved name, spec, tests, and decision package reporting adapter.

Files not to touch: `src.selection_engine` formulas, `selection_decision.json`, `selection_decision_v1`, existing `decision_status` values.

Implementation steps: define verdict labels; map current `decision_status`, `no_trade`, warnings, and action plan; include confidence and confidence limitations; write separate product artifact or report section.

Tests/checks: `python -m pytest tests/test_selection_engine.py` plus new verdict mapping tests.

Rollback risk: medium because wording must remain decision-support and non-imperative.

Expected output: Decision Verdict layer backed by existing technical contracts.

Commit scope: mapping module, spec, tests, report wording.

### Session 09 - Add AI Commentary grounding contract

Objective: define what AI Commentary may consume and say.

Files likely affected: AI Commentary grounding spec, possible evidence bundle module, commentary tests.

Files not to touch: calculators, optimizers, selection formulas, existing report schemas unless adding a separate evidence bundle.

Implementation steps: define allowed input artifacts; define evidence reference requirements; list forbidden claims; add deterministic evidence bundle builder; test missing-evidence and unsupported-claim cases where practical.

Tests/checks: unit tests for evidence bundle and generated-output language tests.

Rollback risk: low to medium because this is mostly contract and bundle.

Expected output: safe grounding contract for future AI explanation.

Commit scope: spec, evidence bundle, tests.

### Session 10 - Add Light Monitoring / What Changed integration

Objective: connect existing monitoring to diagnosis-first state and Decision Verdict.

Files likely affected: monitoring adapter or product projection, docs/spec, tests.

Files not to touch: existing monitoring history semantics and `monitoring_diff.json` schema unless separately approved.

Implementation steps: read existing snapshot/diff; project product "what changed" lines tied to subject, diagnosed problems, candidate/verdict, and retest triggers; keep full monitoring advanced.

Tests/checks: `python -m pytest tests/test_monitoring.py` plus new projection tests.

Rollback risk: medium if writing new history; start with a separate projection.

Expected output: light product Monitoring / What Changed summary.

Commit scope: additive projection, spec, tests.

### Session 11 - Preserve batch candidate factory as advanced/research mode

Objective: clarify that batch candidate factory remains implemented backend/advanced/research infrastructure.

Files likely affected: candidate factory docs/specs, help wording if needed, tests for unchanged routing.

Files not to touch: factory execution logic except wording/metadata if necessary, candidate formulas, profiles unless separately approved.

Implementation steps: audit wording that implies full factory is the core UX; classify full factory/full menu as advanced/research/backend; ensure default `run_portfolio_review.py --mode core` stays intact.

Tests/checks: `python -m pytest tests/test_candidate_factory_contract.py tests/test_portfolio_review_workflow.py`.

Rollback risk: low if docs/help only.

Expected output: clear product/backend boundary for candidate factory.

Commit scope: wording, spec, tests only.

### Session 12 - Final verification, docs sync, and regression checks

Objective: verify backward compatibility and diagnosis-first behavior across the migration.

Files likely affected: docs sync only unless focused fixes are needed.

Files not to touch: generated output cleanup, unrelated dirty files, broad rewrites.

Implementation steps: run narrow tests from changed areas; run docs verification; run `python run_portfolio_review.py --dry-run`; when clean and approved, run `python run_portfolio_review.py --mode core --skip-pdf`; inspect JSON contracts and output manifests for unintended changes.

Tests/checks: all relevant unit tests, docs links, dry-run, and approved smoke run.

Rollback risk: medium only if prior sessions changed wiring.

Expected output: regression evidence and synchronized docs.

Commit scope: final docs/test updates only.

## Verification Strategy

Use narrow checks first:

    python -m pytest tests/test_portfolio_review_workflow.py
    python -m pytest tests/test_analysis_subject_materialization.py
    python -m pytest tests/test_candidate_factory_contract.py
    python -m pytest tests/test_candidate_comparison_contract.py
    python -m pytest tests/test_selection_engine.py
    python -m pytest tests/test_monitoring.py
    python scripts/verify_docs.py
    python run_portfolio_review.py --dry-run

Use the broader smoke run only after dirty state is classified and runtime side effects are acceptable:

    python run_portfolio_review.py --mode core --skip-pdf

For any session that writes generated JSON, verify schema names, existing field names, output manifests, and no unintended generated-output changes. If generated files change as a side effect, classify them before staging anything.

## Progress

- [x] 2026-05-25: Created planning-only ExecPlan for code migration. No code changes, staging, or commits are part of this initial step.
- [x] Session 01: Current runtime and entrypoint inventory. Completed as docs-only audit `docs/audits/2026-05-25_code_migration_session01_runtime_inventory.md`; no code changes, generated-output cleanup, staging, or commit.
- [x] Session 01 verification: ran docs verification with `.\.venv\Scripts\python.exe scripts\verify_docs.py`. Result failed only on pre-existing archive references in `docs/archive/documentation_migration_2026_05_25/LEGACY_DIAGNOSTIC_PRODUCT_CONCEPT.md`; no Session 01 file link failures remain after removing future-path references from this ExecPlan.
- [x] Session 02: Define workflow state model. Added pure helper `src/workflow_state.py`, owning spec `docs/specs/workflow_state_spec.md`, and focused tests `tests/test_workflow_state.py`; no CLI behavior or generated-output contract changes.
- [x] Session 02 verification: `.\.venv\Scripts\python.exe -m pytest tests\test_workflow_state.py tests\test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_workflow_state_session02'` passed, 30 tests. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.
- [x] Session 03: Make diagnosis-first flow explicit. `PortfolioReviewPlan` now carries `workflow_state` metadata and `summarize_plan()` prints it; command order, CLI behavior, formulas, and generated schemas are unchanged.
- [x] Session 03 verification: `.\.venv\Scripts\python.exe -m pytest tests\test_workflow_state.py tests\test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_workflow_state_session03'` passed, 31 tests. `.\.venv\Scripts\python.exe run_portfolio_review.py --dry-run` passed and printed workflow state metadata. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.
- [x] Session 04: Add/formalize Problem Classification artifact. Added deterministic `problem_classification.json` writer backed by Portfolio X-Ray and stress evidence; no formula, optimizer, schema, CLI, or generated-output cleanup changes.
- [x] Session 04 verification: `.\.venv\Scripts\python.exe -m pytest tests\test_problem_classification.py tests\test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_problem_classification_session04'` passed, 24 tests. `run_portfolio_review.py --dry-run` passed. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.
- [x] Session 05: Add Candidate Launchpad data layer. Added deterministic `candidate_launchpad.json` writer backed by Problem Classification; cards contain no weights and do not execute builders.
- [x] Session 05 verification: `.\.venv\Scripts\python.exe -m pytest tests\test_candidate_launchpad.py tests\test_problem_classification.py tests\test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_candidate_launchpad_session05'` passed, 28 tests. `run_portfolio_review.py --dry-run` passed. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.
- [x] Session 06: Add Portfolio Alternatives Builder wrapper. Added pure one-candidate build-plan wrapper over existing candidate factory plumbing; no builder execution, formula changes, or CLI behavior changes.
- [x] Session 06 verification: `.\.venv\Scripts\python.exe -m pytest tests\test_portfolio_alternatives_builder.py tests\test_candidate_launchpad.py tests\test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_alternatives_builder_session06'` passed, 32 tests. `run_portfolio_review.py --dry-run` passed. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.
- [x] Session 07: Make Current vs Candidate primary MVP comparison path. Added additive `current_vs_candidate.json` adapter over canonical comparison and optional selection output; `candidate_comparison.json` contract remains unchanged.
- [x] Session 07 verification: `.\.venv\Scripts\python.exe -m pytest tests\test_current_vs_candidate.py tests\test_candidate_comparison_contract.py tests\test_selection_engine.py -q --basetemp='tmp\pytest_current_vs_candidate_session07'` passed, 29 tests. `run_portfolio_review.py --dry-run` passed. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.
- [x] Session 08: Map Selection Engine / No-Trade to Decision Verdict. Added additive `decision_verdict.json` mapping over `selection_decision.json`, optional current-vs-candidate, and action-plan context without changing Selection Engine contracts.
- [x] Session 08 verification: `.\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict.py tests\test_selection_engine.py tests\test_action_engine.py -q --basetemp='tmp\pytest_decision_verdict_session08'` passed, 29 tests. `run_portfolio_review.py --dry-run` passed. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.
- [x] Session 09: Add AI Commentary grounding contract. Added deterministic `ai_commentary_context.json` evidence bundle and grounding rules for future AI Commentary; no LLM calls, formula changes, verdict changes, or report-schema rewrites.
- [x] Session 09 verification: `.\.venv\Scripts\python.exe -m pytest tests\test_ai_commentary_context.py tests\test_decision_verdict.py tests\test_current_vs_candidate.py -q --basetemp='tmp\pytest_ai_commentary_session09'` passed, 12 tests; `tests\test_candidate_comparison_contract.py` passed, 8 tests. `run_portfolio_review.py --dry-run` passed. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.
- [x] Session 10: Add Light Monitoring / What Changed integration. Added additive `what_changed_summary.json` projection over existing `monitoring_diff.json`, optional Decision Verdict, Problem Classification, and current-vs-candidate context; monitoring schema/history semantics are unchanged.
- [x] Session 10 verification: `.\.venv\Scripts\python.exe -m pytest tests\test_light_monitoring_summary.py tests\test_monitoring.py -q --basetemp='tmp\pytest_light_monitoring_session10'` passed, 11 tests; `tests\test_candidate_comparison_contract.py` passed, 8 tests. `run_portfolio_review.py --dry-run` passed. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.
- [x] Session 11: Preserve batch candidate factory as advanced/research. Added static product-boundary helpers and docs clarifying that `run_candidate_factory.py` remains backend/advanced/research infrastructure while Launchpad and Alternatives Builder are product-facing layers.
- [x] Session 11 verification: `.\.venv\Scripts\python.exe -m pytest tests\test_candidate_factory.py tests\test_portfolio_alternatives_builder.py tests\test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_candidate_factory_boundary_session11'` passed, 79 tests. `run_portfolio_review.py --dry-run` passed. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.
- [x] Session 12: Final verification, docs sync, and regression checks. Ran final focused regression, dry-run, docs verification, and dirty-tree inspection; no generated-output cleanup, staging, or commits were performed.
- [x] Session 12 verification: focused migration regression passed with `.\.venv\Scripts\python.exe -m pytest ... -q --basetemp='tmp\pytest_code_migration_session12_focused'` (146 passed). Broader planned regression surfaced two blockers outside the safe Session 12 fix scope: `tests/test_analysis_subject_materialization.py::test_run_materialize_analysis_subject_writes_to_canonical_sidecar` attempted network-backed FRED/yfinance loading under sandbox, and `tests/test_candidate_factory_contract.py::test_live_factory_build_matches_golden_document` found an existing candidate-factory golden `options_keys` drift. `run_portfolio_review.py --dry-run` passed. `scripts\verify_docs.py` still fails only on pre-existing archived legacy documentation links under `docs/archive/documentation_migration_2026_05_25/`.

## Surprises & Discoveries

- 2026-05-25: The active product docs already mark several target layers as requiring code/spec verification: Problem Classification, Candidate Launchpad, user-triggered Portfolio Alternatives Builder, formal Decision Verdict terminology, AI Commentary grounding, and current-vs-selected-candidate as the primary UX.
- 2026-05-25: The current implementation already writes many downstream decision artifacts in the portfolio-first run, but these are generated backend/advanced evidence and should not automatically be treated as product UI modules.
- 2026-05-25: The working tree is dirty with unrelated source/config/generated changes, including untracked IBKR/data provider work. This blocks safe code migration until classified.
- 2026-05-25: During Session 01, plain `python` and `py -3` were unavailable in the shell, but `.\.venv\Scripts\python.exe` is available and reports Python 3.12.13. `run_portfolio_review.py --help` needs `PYTHONIOENCODING=utf-8` on this Windows console because its help text contains a Unicode arrow.
- 2026-05-25: Docs verification failed on archived documentation-migration legacy links that predate Session 01. The new Session 01 files initially referenced future module/spec paths as code spans; those were reworded as session-approved future names so the verifier no longer reports Session 01 missing-file failures.
- 2026-05-25: Session 02 kept workflow-state classification pure and additive. It intentionally uses a local static factory-profile count map rather than importing candidate factory code, so classification cannot execute or mutate candidate runtime.
- 2026-05-25: The first Session 02 pytest run without `--basetemp` failed during test setup because pytest could not remove `C:\Users\ShumeikoYe\.cache\codex-pytest-temp` on Windows. Re-running with a workspace basetemp passed. This is an environment/temp cleanup issue, not a workflow-state logic failure.
- 2026-05-25: Session 03 could make diagnosis-first state explicit without introducing a new artifact. The existing in-memory `PortfolioReviewPlan` was the safest place to attach the state because it avoids CLI/schema changes.
- 2026-05-25: Session 04 could add Problem Classification as a thin evidence translation layer after X-Ray generation. The safest integration point is immediately after `_xray_summary_from_output_dir()` in `run_report.py`, because both `portfolio_xray.json` and `stress_report.json` are available there.
- 2026-05-25: Session 05 could add Candidate Launchpad without touching candidate factory or builders. The artifact maps problems to hypothesis cards and suggested method ids only; the future Portfolio Alternatives Builder remains responsible for candidate creation.
- 2026-05-25: Session 06 did not need to import optimizer internals. Delegating one selected method to `run_candidate_factory.py --candidates <candidate_id>` preserves existing builders and avoids formula drift.
- 2026-05-25: Session 09 can ground future AI Commentary without generating commentary. The safe artifact is an evidence bundle with allowed source artifacts, forbidden claim categories, field-level references, and explicit warnings for missing context.
- 2026-05-25: Session 10 can integrate product-facing Monitoring without touching monitoring history. The safe layer is a separate `what_changed_summary.json` projection over `monitoring_diff.json`.
- 2026-05-25: Session 11 can preserve batch factory boundaries without changing generated schemas. Static helper functions and docs are enough to classify `core_fast` as backend routine batch and `default_v1` as advanced/research full batch.
- 2026-05-25: Session 12 broad regression surfaced two non-migration blockers: an analysis-subject materialization test can still attempt live FRED/yfinance data in this sandbox, and the candidate factory golden contract has an `options_keys` drift unrelated to Session 12 verification. These should be fixed in separate focused sessions before claiming a fully green broad suite.

## Decision Log

- 2026-05-25: Decision: migrate by adding thin orchestration/product adapters over existing calculators rather than rewriting calculators. Rationale: current specs prohibit formula, optimizer, schema, field, and CLI changes during planning; existing code already produces much of the required evidence.
- 2026-05-25: Decision: preserve batch candidate factory as backend / advanced / research infrastructure. Rationale: product docs say Candidate Launchpad and Portfolio Alternatives Builder are target layers, while the current factory is a batch orchestration capability that must not be removed.
- 2026-05-25: Decision: keep Decision Verdict as a product-facing mapping over Selection Engine until a separate schema migration is approved. Rationale: current technical contracts remain `selection_decision.json`, `selection_decision_v1`, and Selection/No-Trade.
- 2026-05-25: Decision: block code migration until dirty working tree state is classified. Rationale: unrelated dirty source/config/generated files make it unsafe to attribute or stage migration changes.
- 2026-05-25: Decision: Session 01 records the runtime inventory in a standalone audit file rather than updating `docs/audits/README.md`. Rationale: the audit register was already dirty before this session, and Session 01 should avoid mixing new migration documentation with unrelated dirty register changes.
- 2026-05-25: Decision: Session 02 does not wire workflow state into `run_portfolio_review.py` yet. Rationale: the session objective is to define the model without changing CLI behavior; Session 03 owns explicit orchestration wiring.
- 2026-05-25: Decision: Session 03 stores workflow state on `PortfolioReviewPlan` and includes it in `summarize_plan()`, but does not add CLI flags or write JSON. Rationale: this satisfies diagnosis-first visibility while preserving current runtime behavior and generated contracts.
- 2026-05-25: Decision: Problem Classification is diagnostic-only and additive. It writes a new artifact instead of modifying `portfolio_xray.json`, `stress_report.json`, `candidate_comparison.json`, or `selection_decision.json`. Rationale: target product needs the layer, but guardrails prohibit formula/schema changes and decision-contract renames.
- 2026-05-25: Decision: Candidate Launchpad cards never generate portfolios in V1 and always export `generates_portfolio: false`. Rationale: product docs define Launchpad cards as entry points into the Alternatives Builder, not portfolios.
- 2026-05-25: Decision: Portfolio Alternatives Builder Session 06 returns build plans and defaults to dry-run execution. Rationale: the migration needs a user-triggered wrapper boundary, but current guardrails require preserving CLI behavior and avoiding accidental generated-output writes.
- 2026-05-25: Decision: Session 09 implements `ai_commentary_context.json`, not natural-language AI commentary. Rationale: the target layer needs a grounding contract first; LLM prompts, provider calls, and generated prose would be a separate behavior/session with higher review risk.
- 2026-05-25: Decision: Session 10 writes a separate `what_changed_summary.json` instead of changing `monitoring_diff_v1`. Rationale: monitoring snapshot/diff semantics are already implemented and should remain stable; the migration only needs a light product projection.
- 2026-05-25: Decision: Session 11 does not write factory product-boundary metadata into `candidate_factory_run.json`. Rationale: user guardrails prohibit schema changes; static code helpers plus specs/tests provide the boundary without changing generated contracts.
- 2026-05-25: Decision: Session 12 does not run `run_portfolio_review.py --mode core --skip-pdf`. Rationale: the working tree remains heavily dirty with generated outputs and unrelated source/config changes; the command would write generated artifacts and make attribution worse without explicit approval.
- 2026-05-25: Decision: Session 12 does not repair archived legacy documentation links, the network-coupled materialization test, or the candidate factory golden drift. Rationale: each is a separate focused cleanup/fix task and should not be mixed into final migration verification.

## Outcomes & Retrospective

Initial outcome, 2026-05-25: This ExecPlan defines a conservative, multi-session migration program. It does not implement code behavior. It gives future sessions a safe order: inventory first, state model second, diagnosis-first orchestration third, then product artifacts and adapters. The main unresolved blocker is dirty working tree classification before any code changes.

Session 01 outcome, 2026-05-25: The current runtime and entrypoint inventory is documented in `docs/audits/2026-05-25_code_migration_session01_runtime_inventory.md`. The audit confirms that `run_portfolio_review.py` is the current portfolio-first orchestrator, `run_report.py` is the report/diagnostics backend, `run_candidate_factory.py` is batch backend/advanced/research infrastructure, `run_compare_variants.py` is the comparison and downstream decision-package writer, and `run_optimization.py` is the legacy policy compatibility flow. No code was changed. The next implementation session is Session 02, but code changes remain blocked until dirty working tree state is classified.

Session 01 verification note, 2026-05-25: Documentation verification was attempted through the repository virtual environment. It still fails because archived legacy documentation under `docs/archive/documentation_migration_2026_05_25/` contains stale relative links. Those failures were present outside the Session 01 scope and were not repaired here to avoid mixing archive cleanup into the migration inventory session.

Session 02 outcome, 2026-05-25: The workflow-state model now exists as a pure additive helper. It classifies candidate intent into `diagnosis_only`, `one_candidate`, or `multiple_candidates` from explicit candidate ids/counts, known factory profiles, supplied artifact ids, or review-plan argv. The helper does not run workflows, read generated artifacts, change existing orchestration, or alter CLI behavior. The next implementation session is Session 03, which may wire this state into review orchestration metadata if dirty-state handling is acceptable.

Session 02 verification outcome, 2026-05-25: Focused pytest passed with workspace basetemp: 30 passed. Documentation verification remains blocked by archived legacy links unrelated to Session 02.

Session 03 outcome, 2026-05-25: Diagnosis-first workflow state is now explicit in orchestration metadata. Default core/full plans classify as `multiple_candidates`, explicit single-candidate plans classify as `one_candidate`, and skip-candidates plans classify as `diagnosis_only`. This is an in-memory planning signal only; no generated output contract or CLI behavior changed.

Session 03 verification outcome, 2026-05-25: Focused pytest passed with workspace basetemp: 31 passed. Portfolio review dry-run passed and showed `Workflow state: multiple_candidates (candidate_count=6, source=factory_profile)` for the default core plan. Documentation verification remains blocked by archived legacy links unrelated to Session 03.

Session 04 outcome, 2026-05-25: Problem Classification is implemented as `src/problem_classification.py`, documented in `docs/specs/problem_classification_spec.md`, and wired into `run_report.py` after X-Ray generation. It produces at most three diagnostic problems with evidence references and reasonable paths to test. It does not build candidates or issue verdicts.

Session 04 verification outcome, 2026-05-25: Focused pytest passed with workspace basetemp: 24 passed. Portfolio review dry-run still passes. Documentation verification remains blocked by archived legacy links unrelated to Session 04.

Session 05 outcome, 2026-05-25: Candidate Launchpad is implemented as `src/candidate_launchpad.py`, documented in `docs/specs/candidate_launchpad_spec.md`, and wired into `run_report.py` after Problem Classification. It writes `candidate_launchpad.json` with cards that map source problems to user-facing goals and suggested method ids. It does not call candidate builders, write weights, or change factory behavior.

Session 05 verification outcome, 2026-05-25: Focused pytest passed with workspace basetemp: 28 passed. Portfolio review dry-run still passes. Documentation verification remains blocked by archived legacy links unrelated to Session 05.

Session 06 outcome, 2026-05-25: Portfolio Alternatives Builder is implemented as `src/portfolio_alternatives_builder.py` and documented in `docs/specs/portfolio_alternatives_builder_spec.md`. It maps selected Launchpad methods to existing candidate ids and returns a command plan for `run_candidate_factory.py --candidates <candidate_id> --execution-mode standard --output-profile site_api --then-compare`. It does not execute by default, does not write weights, and does not change candidate formulas.

Session 06 verification outcome, 2026-05-25: Focused pytest passed with workspace basetemp: 32 passed. Portfolio review dry-run still passes. Documentation verification remains blocked by archived legacy links unrelated to Session 06.

Session 07 outcome, 2026-05-25: Current-vs-candidate is implemented as `src/current_vs_candidate.py`, documented in `docs/specs/current_vs_candidate_spec.md`, and wired into `write_candidate_comparison_outputs()` after Selection output is available. It writes `current_vs_candidate.json` as a product-facing one-candidate/shortlist projection without changing canonical comparison or Selection contracts.

Session 07 verification outcome, 2026-05-25: Focused pytest passed with workspace basetemp: 29 passed. Portfolio review dry-run still passes. Documentation verification remains blocked by archived legacy links unrelated to Session 07.

Session 08 outcome, 2026-05-25: Decision Verdict is implemented as `src/decision_verdict.py`, documented in `docs/specs/decision_verdict_spec.md`, and wired into `write_candidate_comparison_outputs()` after `action_plan.json` is available. It maps Selection statuses to product-facing verdict ids while preserving `selection_decision.json`, `selection_decision_v1`, `decision_status`, Selection formulas, and No-Trade thresholds.

Session 08 verification outcome, 2026-05-25: Focused pytest passed with workspace basetemp: 29 passed. Portfolio review dry-run still passes. Documentation verification remains blocked by archived legacy links unrelated to Session 08.

Session 09 outcome, 2026-05-25: AI Commentary grounding is implemented as `src/ai_commentary_context.py`, documented in `docs/specs/ai_commentary_grounding_spec.md`, and wired into `write_candidate_comparison_outputs()` after `decision_verdict.json`. It writes `ai_commentary_context.json` with allowed source artifacts, forbidden claim categories, required grounding rules, evidence references, source-presence map, and warnings. It does not call an LLM, generate final commentary, calculate metrics, change Selection/Decision Verdict, or execute trades.

Session 09 verification outcome, 2026-05-25: Focused pytest passed with workspace basetemp: 12 passed for the new grounding/verdict/current-vs-candidate tests, plus 8 passed for candidate comparison contract regression. Portfolio review dry-run still passes. Documentation verification remains blocked by archived legacy links unrelated to Session 09.

Session 10 outcome, 2026-05-25: Light Monitoring / What Changed is implemented as `src/light_monitoring_summary.py`, documented in `docs/specs/light_monitoring_summary_spec.md`, and wired into `write_candidate_comparison_outputs()` after `monitoring_diff.json` is written. It writes `what_changed_summary.json` with product-level change lines, evidence references, retest triggers, optional problem/verdict/current-vs-candidate context, and guardrails. It does not change `monitoring_diff.json`, monitoring snapshot storage, history retention, formulas, thresholds, CLI behavior, or generated-output cleanup policy.

Session 10 verification outcome, 2026-05-25: Focused pytest passed with workspace basetemp: 11 passed for light monitoring and monitoring tests, plus 8 passed for candidate comparison contract regression. Portfolio review dry-run still passes. Documentation verification remains blocked by archived legacy links unrelated to Session 10.

Session 11 outcome, 2026-05-25: Batch candidate factory boundaries are now explicit. `src.candidate_factory` exposes static helper metadata (`candidate_factory_product_boundary()` and `candidate_factory_profile_classification()`) used by tests/docs only. The candidate factory remains preserved backend/advanced/research infrastructure; `default_v1` is classified as full advanced/research batch, `core_fast` as backend routine core batch, and the one-candidate product-facing path remains `src.portfolio_alternatives_builder`. No builder formulas, factory execution behavior, CLI flags, or generated JSON schemas changed.

Session 11 verification outcome, 2026-05-25: Focused pytest passed with workspace basetemp: 79 passed across candidate factory, alternatives builder, and portfolio review workflow tests. Portfolio review dry-run still passes. Documentation verification remains blocked by archived legacy links unrelated to Session 11.

Session 12 outcome, 2026-05-25: The migration program is verified at focused-regression level and the final status is documented. The new diagnosis-first layers remain additive: workflow state, Problem Classification, Candidate Launchpad, one-candidate Alternatives Builder wrapper, current-vs-candidate adapter, Decision Verdict mapping, AI Commentary grounding context, light What Changed summary, and batch-factory advanced/research boundary. No formulas, optimizer math, stress scenarios, CLI flags, existing generated JSON field names, or legacy flows were intentionally changed by Session 12.

Session 12 verification outcome, 2026-05-25: Focused migration regression passed with 146 tests. Portfolio review dry-run passed and still shows `analysis_subject` diagnosis before candidate factory. Documentation verification remains blocked by archived legacy links unrelated to this migration. The broader planned regression is not fully green: one materialization test attempted sandbox-blocked network data loading, and one candidate-factory golden contract test detected existing `options_keys` drift. Because the working tree is still dirty and generated-output folders are already modified, the approved final full smoke (`run_portfolio_review.py --mode core --skip-pdf`) was not run in Session 12.

## Out of Scope

This migration plan does not build a full UI, saved workspaces, broker import, broker execution, tax-aware workflows, macro regime monitoring workspace, or a new optimizer. It does not remove `run_optimization.py`, candidate factory, existing candidate scripts, generated reports, or legacy compatibility outputs. It does not change formulas, stress scenarios, optimizer math, schemas, JSON field names, or CLI behavior.

## First Recommended Next Action

Next recommended action after the migration sessions: classify the dirty working tree before staging or committing. Then handle three separate blockers in focused tasks: archived legacy docs link cleanup, network-free materialization test stabilization, and candidate-factory golden contract drift. Only after those are resolved or explicitly accepted should a full `run_portfolio_review.py --mode core --skip-pdf` smoke be run and reviewed for generated-output changes.
