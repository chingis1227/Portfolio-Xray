# Code Migration Plan: Diagnosis-First Portfolio MRI Architecture

Date: 2026-05-25  
Status: planning-only; no code changes included

This plan translates the migrated Portfolio MRI product documentation into a practical code migration program. It is intentionally conservative: it preserves current formulas, optimizer math, schemas, JSON fields, CLI behavior, generated-output contracts, and legacy flows until a focused implementation session explicitly changes them.

## 1. Executive Summary

The current codebase is already partly portfolio-first: `run_portfolio_review.py` materializes `analysis_subject` diagnostics before candidate generation and comparison. However, the runtime is still mostly CLI/file/report-first. It produces a rich decision package, but the product architecture now calls for a clearer diagnosis-first user journey:

```text
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
```

The safest migration is not a rewrite. The code should keep existing calculators and contracts, then add thin orchestration and product-facing adapter layers around them. In particular:

- preserve `run_report.py`, `src.portfolio_xray`, `src.stress`, candidate builders, candidate comparison, Selection Engine, Action Engine, Monitoring, and Decision Journal as current backend evidence generators;
- make the diagnosis-only state explicit before any candidate is created;
- add a Problem Classification artifact that derives from existing X-Ray and stress evidence without inventing new formulas;
- add a Candidate Launchpad data layer that suggests improvement paths but does not create portfolios by itself;
- wrap existing candidate builders in a Portfolio Alternatives Builder interface for one selected candidate or a shortlist;
- make current-vs-selected-candidate the primary MVP comparison surface while preserving the full candidate comparison table as backend/advanced evidence;
- map current `selection_decision.json` / No-Trade outputs to product-facing Decision Verdict language without renaming schemas or fields;
- define AI Commentary as grounded explanation over deterministic JSON evidence, not as a calculation source;
- keep batch candidate factory as backend / advanced / research infrastructure, not the default UX.

No target module should be claimed as implemented until verified in code and an owning spec/artifact exists. Current docs explicitly mark Problem Classification, Candidate Launchpad, user-triggered Portfolio Alternatives Builder, formal Decision Verdict terminology, and AI Commentary grounding as target/TBD or requiring code/spec verification.

## 2. Current Code Inventory

### 2.1 Current entrypoints

| Entrypoint | Current role | Migration classification |
| --- | --- | --- |
| `run_portfolio_review.py` | Default portfolio-first orchestrator. Builds a plan that materializes `analysis_subject`, runs candidate factory unless skipped, runs comparison/decision package, and optionally rebuilds PDFs. | Preserve as current CLI front door; later make diagnosis-first states explicit without breaking flags. |
| `run_report.py` | Core report/diagnostics engine. `run_portfolio_report_for_weights()` computes metrics, stress, X-Ray, commentary, snapshots, and report artifacts from fixed weights. Supports `--materialize-analysis-subject` and `--materialize-current`. | Preserve as calculator/report backend. Do not change formulas or output schemas. |
| `run_candidate_factory.py` | Controlled batch candidate orchestration. Runs or reuses candidate builders, supports profiles (`core_fast`, `core_v1`, `default_v1`, etc.), execution modes, manifests, resume, and optional `--then-compare`. | Preserve as backend / advanced / research batch mode. Do not remove or demote implementation capability. |
| `run_compare_variants.py` | Reads existing candidate artifacts and writes canonical `candidate_comparison.json` plus downstream scorecard, health, selection, action, monitoring, journal, and decision package artifacts. | Preserve as comparison/decision backend. Later add focused current-vs-candidate adapter. |
| `run_optimization.py` | Legacy policy optimizer compatibility path. Produces optimized policy weights and legacy policy report artifacts. | Preserve as legacy compatibility; keep out of default diagnosis-first flow unless explicitly requested. |
| `run_mvp_workflow.py` | Optional legacy MVP orchestration wrapper over policy/current/full-decision/diagnosis-only modes. | Preserve for compatibility; do not make it the target product architecture. |
| Candidate scripts such as `run_equal_weight.py`, `run_risk_parity.py`, `run_minimum_variance.py`, `run_robust_mean_variance_constrained.py` | Build fixed candidate weights and/or candidate report artifacts. | Preserve as candidate construction backends. Later wrap through Portfolio Alternatives Builder. |

### 2.2 Current runtime flow

Current default portfolio-first review:

1. `run_portfolio_review.py` loads and validates config.
2. `src.portfolio_review_workflow.build_portfolio_review_plan()` creates ordered CLI steps.
3. First step calls `run_report.py --materialize-analysis-subject` to write `{output_dir_final}/analysis_subject/`.
4. Candidate step calls `run_candidate_factory.py` unless `--skip-candidates`.
5. Factory runs selected candidate IDs using `src.candidate_factory` and `src.candidate_weights`; standard mode builds weights and lightweight comparison reports.
6. Comparison step happens either through factory `--then-compare` or `run_compare_variants.py`.
7. `src.candidate_comparison.write_candidate_comparison_outputs()` writes comparison and downstream artifacts.
8. Optional PDF export is explicit (`--with-pdf` or `--legacy-full-pdf`).

Legacy policy compatibility flow remains:

1. `run_optimization.py`
2. `run_report.py`
3. optional candidate factory
4. `run_compare_variants.py`

### 2.3 Relevant `src` modules

| Module | Current responsibility | Target reuse |
| --- | --- | --- |
| `src/portfolio_review_workflow.py` | Thin subprocess orchestration for portfolio-first review. | Extend cautiously for explicit workflow states; avoid changing CLI semantics first. |
| `src/analysis_setup.py`, `src/input_assumptions.py`, `src/config.py`, `src/config_schema.py` | Config validation, analysis subject, resolved inputs, assumptions. | Input Portfolio layer backend. |
| `src/data_loader.py`, `src/data_provider.py`, `src/data_trust_signals.py`, `src/cache.py` | Data loading, provider selection, cache, data trust signals. | Input/data trust backend. |
| `src/portfolio_xray.py` | Portfolio X-Ray JSON and render helpers. | Portfolio X-Ray layer backend; also source evidence for Problem Classification. |
| `src/stress.py`, `src/stress_factors.py`, `src/stress_scenario_analytics.py`, `src/scenario_library.py`, `src/scenario_library_normalized.py` | Stress, factor, scenario, hedge-gap, and stress evidence. | Stress Test Lab backend; source evidence for Problem Classification and comparison. |
| `src/candidate_factory.py` | Batch candidate orchestration, manifests, profile handling, execution summaries. | Preserve as backend/advanced/research; not the product-facing Launchpad. |
| `src/candidate_weights.py`, `src/portfolio_variants.py`, `src/optimization.py`, `src/robust_mv.py`, `src/robust_scenario_optimization.py` | Candidate weight construction and optimization helpers. | Portfolio Alternatives Builder backend; formulas unchanged. |
| `src/candidate_comparison.py` | Canonical multi-candidate comparison and menu/factory disclosure. | Reuse for current-vs-candidate and shortlist comparison. |
| `src/robustness_scorecard.py`, `src/portfolio_health_score.py` | Diagnostic scores written after comparison. | Preserve as evidence; do not turn scores into automatic product truth. |
| `src/selection_engine.py` | Technical Selection Engine and No-Trade contract (`selection_decision_v1`). | Backend evidence for product-facing Decision Verdict mapping. |
| `src/action_engine.py` | Non-executing action plan from comparison and selection. | Preserve as optional downstream action summary. |
| `src/monitoring.py` | V1 monitoring snapshot and diff. | Light Monitoring / What Changed backend. |
| `src/decision_journal.py` | Generated decision journal. | Preserve as downstream record; not core architecture layer by itself. |
| `src/portfolio_commentary.py`, `src/decision_package_reporting.py` | Deterministic human-readable commentary/report package text. | Reuse as deterministic commentary; later define AI Commentary grounding. |

### 2.4 Current generated output folders and JSON contracts

Current generated artifacts under `Main portfolio/` include, among others:

- `analysis_subject/`
- `candidate_factory_run.json`
- `candidate_factory_manifest.json`
- `candidate_comparison.json`
- `robustness_scorecard.json`
- `portfolio_health_score.json`
- `selection_decision.json`
- `tradeoff_explanation.json`
- `model_risk_diagnostics.json`
- `assumption_sensitivity.json`
- `pareto_dominance.json`
- `regret_analysis.json`
- `action_plan.json`
- `monitoring_diff.json`
- `monitoring/latest/analysis_snapshot.json`
- `monitoring/history/analysis_snapshot_{analysis_end}.json`
- `decision_journal.json`
- `decision_package_summary.json`
- `current_vs_policy_status.json`
- `portfolio_xray.json`
- `stress_report.json`
- snapshots such as `snapshot_10y.json`, `snapshot_5y.json`, `snapshot_3y.json`

Current candidate output folders include benchmark, risk-budget, optimizer, and robust candidate folders such as `equal-weight portfolio/`, `risk parity portfolio/`, `hierarchical risk parity portfolio/`, `minimum variance portfolio/`, `maximum diversification unconstrained portfolio/`, and `robust mean variance constrained portfolio/`.

Generated outputs are evidence, not source. Do not manually clean or regenerate them inside code migration sessions unless that session explicitly targets generated artifacts.

### 2.5 Current candidate factory / optimization / comparison / selection logic

- Candidate factory profiles define intended candidate sets and run order. Factory output answers what the last factory orchestration attempted; it is not the same as the comparison row set.
- Candidate comparison scans the registry and existing artifacts. It can include `analysis_subject` as baseline when materialized, and it can mark rows `available`, `degraded`, or `unavailable`.
- Optimizer-backed candidates and legacy policy optimizer expose methodology/quality/readiness metadata; comparison degrades or excludes evidence when readiness is incomplete.
- Selection Engine consumes `candidate_comparison.json`, `portfolio_health_score.json`, and `robustness_scorecard.json`. It writes `selection_decision.json` and may produce `no_material_rebalance`.
- Product-facing Decision Verdict language must not be confused with the current technical Selection Engine contract. Do not rename `selection_decision.json`, `decision_status`, or related fields until a separate schema migration is specified and implemented.

## 3. Current vs Target Gap Analysis

### 3.1 Input Portfolio

- Currently exists: config validation, `analysis_subject`, `current_portfolio` / `model_portfolio` / `universe_baseline` support, input assumptions, analysis setup, data provider/cache/trust signals.
- Reuse: `src.config_schema`, `src.analysis_setup`, `src.input_assumptions`, `src.data_loader`, `src.data_trust_signals`, `run_report.py --materialize-analysis-subject`.
- Missing: a product-facing workflow state model that cleanly says "input accepted, diagnosis pending/done, no candidate generated yet".
- Legacy/advanced: `portfolio_weights.yml` and legacy policy optimizer remain compatibility output/input to legacy flows only.
- New orchestration needed: state resolver that records whether the run is diagnosis-only, one-candidate, or multi-candidate without changing config schemas first.

### 3.2 Portfolio X-Ray

- Currently exists: `portfolio_xray.json`, X-Ray text/HTML/commentary renderers, seven-section diagnostic behavior governed by specs.
- Reuse: `src.portfolio_xray` and existing subject/candidate report artifacts.
- Missing: explicit product handoff from X-Ray evidence into Problem Classification.
- Legacy/advanced: deep PCA/archetype/factor diagnostics remain advanced where specs classify them as such.
- New orchestration needed: stable evidence reader that extracts only existing X-Ray fields for downstream product layers.

### 3.3 Stress Test Lab

- Currently exists: `stress_report.json`, stress scorecard, conclusions, historical/synthetic stress, hedge gap, scenario library, data-quality disclosures.
- Reuse: `src.stress`, `src.stress_factors`, scenario modules, current generated stress artifacts.
- Missing: a product-level Stress Test Lab summary artifact distinct from raw technical stress details.
- Legacy/advanced: macro/regime and broad factor diagnostics can remain advanced overlays unless the target MVP explicitly promotes them.
- New orchestration needed: a deterministic stress evidence projection for Problem Classification, comparison, verdict, and commentary.

### 3.4 Problem Classification

- Currently exists: no verified owning module or artifact. X-Ray weakness map and stress conclusions provide source evidence, but Problem Classification is target/TBD.
- Reuse: `portfolio_xray.json`, `stress_report.json`, data trust warnings, health/robustness evidence if already generated.
- Missing: canonical artifact, labels, severity rules, confidence/status fields, tests, docs.
- Legacy/advanced: Portfolio archetype classification is not the same as Problem Classification and should not be relabeled.
- New orchestration needed: add a thin deterministic classifier that outputs top 2-3 user-understandable problems and suggested paths without changing formulas.

### 3.5 Candidate Launchpad

- Currently exists: no verified owning module or artifact. Candidate factory profiles exist, but they are batch builder profiles, not product launchpad cards.
- Reuse: Problem Classification output, candidate method registry, candidate factory/profile metadata, existing candidate families.
- Missing: launchpad card schema, suggested method mapping, "keep current and monitor" path, tests, docs.
- Legacy/advanced: full `default_v1` factory menu stays backend/advanced/research.
- New orchestration needed: a data layer that turns diagnosed problems into suggested hypotheses/cards without building portfolios.

### 3.6 Portfolio Alternatives Builder

- Currently exists: candidate scripts, `src.candidate_weights`, `src.portfolio_variants`, optimizer helpers, robust builders, batch factory.
- Reuse: all existing candidate construction functions and scripts.
- Missing: user-triggered on-demand builder abstraction for one selected candidate/hypothesis; simple-mode parameter model; provenance link from launchpad card to candidate artifact.
- Legacy/advanced: advanced optimizer controls, robust lambda controls, custom budgets, full batch generation, and research profiles stay out of default MVP.
- New orchestration needed: wrapper that calls existing builders for one requested method/candidate and records candidate provenance without changing math.

### 3.7 Current vs Candidate Comparison

- Currently exists: `candidate_comparison.json` supports `analysis_subject` baseline and multi-candidate registry rows; comparison is diagnostic-only.
- Reuse: `src.candidate_comparison`, existing snapshots, stress, construction disclosure, health/robustness scorecards, tradeoff/model-risk modules.
- Missing: primary product shape for current vs one selected candidate and shortlist-only comparison.
- Legacy/advanced: full 16-row comparison table remains backend/advanced/research evidence.
- New orchestration needed: adapter/view artifact that narrows comparison to `analysis_subject` vs selected candidate or shortlist while preserving canonical comparison unchanged.

### 3.8 Decision Verdict

- Currently exists: technical `selection_decision.json` and No-Trade outputs via `src.selection_engine`; action plan via `src.action_engine`.
- Reuse: current decision status, favored candidate, no-trade materiality, warnings, rationale, action plan context.
- Missing: product-facing Decision Verdict vocabulary and one-screen summary contract.
- Legacy/advanced: Selection Engine schema and technical names remain current contract.
- New orchestration needed: product-facing mapping layer that reads `selection_decision.json` and writes a new artifact or report section without renaming existing fields.

### 3.9 AI Commentary

- Currently exists: deterministic commentary/report text in `src.portfolio_commentary` and `src.decision_package_reporting`. No verified formal AI Commentary grounding contract.
- Reuse: deterministic generated evidence and report summary lines.
- Missing: grounding input bundle, allowed/forbidden claims, citation/evidence references, tests for unsupported statements.
- Legacy/advanced: existing commentary remains deterministic product/report text until AI scope is specified.
- New orchestration needed: AI Commentary contract that explains evidence, does not calculate, and does not invent data-quality statuses or verdicts.

### 3.10 Monitoring / What Changed

- Currently exists: V1 `monitoring_diff.json`, snapshots, history, and Decision Journal.
- Reuse: `src.monitoring`, `src.decision_journal`, comparison/selection/action projections.
- Missing: product-facing light monitoring integration after Decision Verdict and candidate retest triggers.
- Legacy/advanced: full multi-client/workspace monitoring remains advanced/later.
- New orchestration needed: connect monitoring summary to diagnosis-first workflow states and Decision Verdict without changing existing monitoring schemas first.

## 4. Migration Strategy

1. Change orchestration first, not formulas.
   - Keep metric, stress, optimization, scoring, and selection math unchanged.
   - Do not adjust thresholds or formulas while adding product layers.

2. Preserve calculators and generated contracts.
   - Treat `run_report.py`, `src.portfolio_xray`, `src.stress`, `src.candidate_comparison`, `src.selection_engine`, and `src.monitoring` as source calculators/evidence generators.
   - Add adapters around them rather than replacing them.

3. Add thin wrapper layers where possible.
   - Prefer small modules that read existing JSON contracts and produce product-layer artifacts.
   - Avoid new parallel implementations of calculations.

4. Keep old entrypoints working.
   - `run_portfolio_review.py`, `run_candidate_factory.py`, `run_compare_variants.py`, `run_report.py`, and `run_optimization.py` must keep current CLI behavior until a later CLI migration is explicitly approved.

5. Make the diagnosis-first flow explicit.
   - Add a state model before changing UI or CLI defaults.
   - Support diagnosis-only as a real state, not just `--skip-candidates`.

6. Move batch/full research flow out of default UX.
   - Preserve batch factory capabilities.
   - Reclassify full factory/full menu as advanced/research/backend where product-facing docs and future UI need clarity.

7. Never confuse Decision Verdict with Selection Engine.
   - Product language may map Selection/No-Trade evidence to a verdict.
   - Technical contracts remain `selection_decision.json` and `selection_decision_v1` unless a separate schema migration is approved.

## 5. Session-by-Session Code Migration Plan

### Session 01 - Current runtime and entrypoint inventory

- Objective: freeze a verified inventory of current entrypoints, runtime flow, generated artifacts, and module ownership before any behavior change.
- Files likely affected: `CODE_MIGRATION_PLAN.md`, a new audit/doc under `docs/audits/` or `docs/specs/` if approved, possibly `docs/exec_plans/...` progress only.
- Files not to touch: all `src/*.py`, root `run_*.py`, `config.yml`, generated output folders.
- Implementation steps:
  1. Re-run `git status --short` and record dirty-state categories.
  2. Confirm CLI help for key entrypoints without executing workflows.
  3. Read current specs for portfolio review, candidate factory, candidate comparison, selection, outputs, and monitoring.
  4. Produce a concise current-runtime inventory document.
- Tests/checks: `python scripts/verify_docs.py`; no runtime generation.
- Rollback risk: very low; docs-only.
- Expected output: verified current architecture inventory and blocker list.
- Commit scope: docs-only inventory, separate from dirty generated artifacts.

### Session 02 - Define workflow state model: diagnosis-only, one candidate, multiple candidates

- Objective: define a deterministic workflow state model without changing CLI behavior.
- Files likely affected: new spec such as `docs/specs/workflow_state_spec.md`, possible new small module `src/workflow_state.py`, focused tests.
- Files not to touch: optimizer modules, candidate formulas, JSON schemas for existing artifacts.
- Implementation steps:
  1. Define states: `diagnosis_only`, `one_candidate`, `multiple_candidates`.
  2. Define state inputs from existing artifact presence and intended run options.
  3. Add pure functions that inspect existing artifacts/options and return state.
  4. Add tests using fixtures; do not run candidate builders.
- Tests/checks: new unit tests plus `tests/test_portfolio_review_workflow.py`.
- Rollback risk: low if module is pure and not wired into runtime decisions yet.
- Expected output: state model and docs, no behavior change.
- Commit scope: workflow state spec + pure helper + tests.

### Session 03 - Make diagnosis-first flow explicit

- Objective: wire the workflow state into review orchestration/reporting so diagnosis-first is visible and testable.
- Files likely affected: `src/portfolio_review_workflow.py`, `run_portfolio_review.py` help text only if needed, workflow state tests, portfolio review workflow spec.
- Files not to touch: `run_report.py` calculation logic, candidate builders, optimization math.
- Implementation steps:
  1. Preserve current CLI flags.
  2. Annotate review plan with diagnosis-first state metadata.
  3. Ensure `--skip-candidates` clearly maps to diagnosis-only state.
  4. Add or update tests proving `analysis_subject` remains first and `run_optimization.py` is not called by default.
- Tests/checks: `python -m pytest tests/test_portfolio_review_workflow.py tests/test_portfolio_first_e2e_offline.py`.
- Rollback risk: low to medium; orchestration labeling can affect expectations.
- Expected output: explicit diagnosis-first workflow state with unchanged command behavior.
- Commit scope: orchestration metadata/help/docs/tests only.

### Session 04 - Add or formalize Problem Classification artifact

- Objective: create a deterministic Problem Classification artifact from existing X-Ray and stress evidence.
- Files likely affected: new `src/problem_classification.py`, new `docs/specs/problem_classification_spec.md`, tests, `OUTPUTS.md` if a generated artifact is added.
- Files not to touch: `src.portfolio_xray` formulas, `src.stress` formulas, optimizer modules, existing JSON field names.
- Implementation steps:
  1. Define schema version and output filename, e.g. `problem_classification.json`.
  2. Map only existing evidence to labels such as high volatility, high drawdown, concentration, weak hedge behavior, acceptable current portfolio.
  3. Include evidence references and confidence/warnings.
  4. Add writer after `analysis_subject` materialization only when source artifacts exist.
- Tests/checks: new unit tests with fixture X-Ray/stress inputs; docs link verification.
- Rollback risk: medium; new artifact must not imply investment advice.
- Expected output: top 2-3 diagnosed problems and suggested paths.
- Commit scope: new artifact module/spec/tests and minimal wiring.

### Session 05 - Add Candidate Launchpad data layer

- Objective: convert Problem Classification output into launchpad cards that suggest hypotheses but do not build portfolios.
- Files likely affected: new `src/candidate_launchpad.py`, new spec, tests, `OUTPUTS.md` if `candidate_launchpad.json` is generated.
- Files not to touch: candidate builder formulas, factory profiles, comparison schema.
- Implementation steps:
  1. Define launchpad card schema: problem id, suggested goal, suggested method(s), rationale evidence refs.
  2. Include "keep current and monitor" when classification says current is acceptable or evidence is insufficient.
  3. Ensure cards are not portfolios and contain no weights.
  4. Add tests for common problem-to-card mappings.
- Tests/checks: new unit tests; `python scripts/verify_docs.py`.
- Rollback risk: low to medium; mostly additive.
- Expected output: deterministic Launchpad data artifact for product surfaces.
- Commit scope: launchpad module/spec/tests only.

### Session 06 - Add Portfolio Alternatives Builder wrapper around existing candidate builders

- Objective: add an on-demand builder interface that can build one selected candidate by delegating to existing candidate construction code.
- Files likely affected: new `src/portfolio_alternatives_builder.py`, candidate builder wrapper tests, docs/spec.
- Files not to touch: `src.optimization`, `src.portfolio_variants` formula internals, existing root candidate scripts unless only importing/wrapping.
- Implementation steps:
  1. Define simple request model in code/docs without changing external JSON schemas yet.
  2. Map allowed methods to existing candidate IDs/builders.
  3. Return provenance and artifact paths.
  4. Keep batch factory separate and unchanged.
- Tests/checks: unit tests with mocked builders; no live optimizer runs unless later approved.
- Rollback risk: medium; wrapper must avoid hidden behavior changes.
- Expected output: one-candidate builder API that reuses existing builders.
- Commit scope: wrapper/spec/tests only.

### Session 07 - Make Current vs Candidate the primary MVP comparison path

- Objective: add a product-facing comparison view for `analysis_subject` vs one selected candidate or a shortlist.
- Files likely affected: new `src/current_vs_candidate.py` or comparison adapter, spec/tests, output docs if new artifact is written.
- Files not to touch: canonical `candidate_comparison_v1` field names and selection formulas.
- Implementation steps:
  1. Read canonical `candidate_comparison.json`.
  2. Select baseline `analysis_subject` and requested candidate(s).
  3. Project existing metrics/stress/turnover/model-risk evidence into a smaller artifact/view.
  4. Keep full comparison table available for advanced/backend use.
- Tests/checks: tests for one candidate, multiple shortlist, missing candidate, degraded candidate.
- Rollback risk: medium; avoid changing canonical comparison semantics.
- Expected output: MVP comparison artifact/view centered on current vs selected candidate.
- Commit scope: adapter/spec/tests and optional report wiring.

### Session 08 - Map Selection Engine / No-Trade technical outputs to product-facing Decision Verdict

- Objective: add a product-facing verdict mapping that reads existing Selection/No-Trade evidence without renaming schemas.
- Files likely affected: new `src/decision_verdict.py`, spec/tests, decision package reporting adapter.
- Files not to touch: `src.selection_engine` formulas, `selection_decision.json` schema, existing `decision_status` field names.
- Implementation steps:
  1. Define product verdict labels and mapping from current `decision_status`, `no_trade`, warnings, and action plan.
  2. Include confidence and "reason confidence is not higher" from existing evidence.
  3. Output product-facing text/artifact separately from `selection_decision.json`.
  4. Add tests for selected candidate, no material rebalance, data review required, inconclusive, mandate risk reduction.
- Tests/checks: `python -m pytest tests/test_selection_engine.py` plus new verdict tests.
- Rollback risk: medium; wording must avoid trade advice.
- Expected output: Decision Verdict layer backed by current technical contracts.
- Commit scope: mapping module/spec/tests/report wording only.

### Session 09 - Add AI Commentary grounding contract

- Objective: define what AI Commentary may read and say, without using AI as a calculation source.
- Files likely affected: new spec such as `docs/specs/ai_commentary_grounding_spec.md`, possible evidence bundle module, commentary tests.
- Files not to touch: calculators, optimizers, selection formulas, existing report schemas unless adding an evidence bundle.
- Implementation steps:
  1. Define allowed input artifacts and required evidence references.
  2. Define forbidden claims: invented metrics, unsupported statuses, imperative trade advice, schema renames.
  3. Add deterministic evidence bundle builder.
  4. Add tests that reject missing evidence and unsupported claim categories where practical.
- Tests/checks: unit tests for evidence bundle; generated-output language tests.
- Rollback risk: low to medium; mostly contract and bundle.
- Expected output: grounding contract that future AI layer can safely consume.
- Commit scope: spec/evidence bundle/tests only.

### Session 10 - Add Light Monitoring / What Changed integration

- Objective: connect V1 monitoring to the diagnosis-first flow and product verdict.
- Files likely affected: `src.monitoring` adapter or new product monitoring projection, docs/spec/tests.
- Files not to touch: monitoring history storage semantics, existing `monitoring_diff.json` schema unless separately approved.
- Implementation steps:
  1. Read existing monitoring snapshot/diff.
  2. Project product-level "what changed" lines tied to subject, problem classification, candidate/verdict, and retest triggers.
  3. Preserve full monitoring as advanced/later.
  4. Add tests for no prior snapshot, changed risk contributor, changed worst scenario, new warning.
- Tests/checks: `python -m pytest tests/test_monitoring.py` plus new projection tests.
- Rollback risk: medium if writing new history; keep projection separate first.
- Expected output: light monitoring product summary backed by current monitoring.
- Commit scope: additive projection/spec/tests.

### Session 11 - Preserve batch candidate factory as advanced/research mode

- Objective: make code/docs boundaries clear: batch factory remains implemented backend/advanced/research, not default UX.
- Files likely affected: candidate factory docs/specs, command help wording if needed, tests for unchanged CLI behavior.
- Files not to touch: candidate factory execution logic except wording/metadata if necessary, candidate formulas, profiles unless a separate decision approves.
- Implementation steps:
  1. Audit wording that implies full factory is the core user experience.
  2. Add advanced/research classification where appropriate.
  3. Ensure `run_portfolio_review.py --mode core` remains default and full batch remains explicit.
  4. Add tests only if help/routing changes.
- Tests/checks: `python -m pytest tests/test_candidate_factory_contract.py tests/test_portfolio_review_workflow.py`.
- Rollback risk: low if docs/help only.
- Expected output: clear boundary preserving factory capabilities.
- Commit scope: wording/spec/tests only.

### Session 12 - Final verification, docs sync, and regression checks

- Objective: verify the complete migration remains backward compatible and diagnosis-first.
- Files likely affected: docs sync only unless regressions require focused fixes.
- Files not to touch: generated output cleanup, unrelated dirty files, broad rewrites.
- Implementation steps:
  1. Run narrow unit tests from all changed areas.
  2. Run docs link verification.
  3. Run `python run_portfolio_review.py --dry-run`.
  4. When environment is clean and approved, run `python run_portfolio_review.py --mode core --skip-pdf`.
  5. Inspect output manifests and JSON contracts for unintended schema changes.
- Tests/checks: see Section 7.
- Rollback risk: medium only if prior sessions changed wiring; fix by reverting focused adapters, not calculators.
- Expected output: regression evidence and docs synchronized.
- Commit scope: final docs/test updates only.

## 6. What Not To Do

- Do not perform a broad rewrite.
- Do not run `git add -A`.
- Do not stage files in planning or migration-prep sessions unless explicitly requested.
- Do not commit generated outputs with code migration unless a session explicitly targets them.
- Do not rename JSON fields.
- Do not rename existing output files such as `candidate_comparison.json` or `selection_decision.json`.
- Do not change optimizer formulas, optimizer objectives, covariance estimators, stress scenarios, scoring formulas, or thresholds.
- Do not change CLI behavior yet.
- Do not delete legacy policy flows.
- Do not delete or demote existing implementation capabilities only because product docs moved them out of the default UX.
- Do not remove batch candidate factory; classify it as backend / advanced / research unless a later session changes it.
- Do not confuse product-facing Decision Verdict with current technical Selection Engine contracts.
- Do not claim Problem Classification, Candidate Launchpad, Alternatives Builder UX, Decision Verdict replacement, or AI Commentary is implemented until code/spec verification proves it.
- Do not mix generated-output cleanup into migration sessions.
- Do not start code changes without a focused session plan and dirty-working-tree classification.

## 7. Verification Strategy

Use the narrowest reliable verification first and broaden only when risk warrants it.

### 7.1 Unit and contract tests

Recommended baseline checks for future implementation sessions:

- `python -m pytest tests/test_portfolio_review_workflow.py`
- `python -m pytest tests/test_analysis_subject_materialization.py`
- `python -m pytest tests/test_candidate_factory_contract.py`
- `python -m pytest tests/test_candidate_comparison_contract.py`
- `python -m pytest tests/test_selection_engine.py`
- `python -m pytest tests/test_monitoring.py`

Add focused tests for each new adapter or artifact before wiring it into orchestration.

### 7.2 Smoke and dry-run checks

- `python run_portfolio_review.py --dry-run`
- Later, when dirty state and runtime cost are acceptable: `python run_portfolio_review.py --mode core --skip-pdf`

### 7.3 JSON contract checks

For any session that writes or reads generated JSON:

- verify existing schema names remain unchanged;
- verify new artifacts use new names and versions rather than overloading old contracts;
- verify existing fields are not renamed or repurposed;
- verify current `candidate_comparison.json` and `selection_decision.json` consumers still pass.

### 7.4 Output manifest checks

When a run is allowed, inspect:

- `{output_dir_final}/analysis_subject/`
- `{output_dir_final}/candidate_factory_run.json`
- `{output_dir_final}/candidate_comparison.json`
- `{output_dir_final}/output_manifest.json` where present
- new product-layer artifacts, if added by the focused session

### 7.5 Docs and link sync

- `python scripts/verify_docs.py`
- Search stale wording after terminology changes: `rg "policy-first|Selection Engine|Decision Verdict|Candidate Launchpad|Problem Classification|Alternatives Builder"`.

### 7.6 No unintended generated output changes

Before any commit, inspect `git status --short`. If generated files changed as a side effect of tests or smoke runs, classify them explicitly and do not include them with code unless the session required generated artifact updates.

## 8. Dirty Working Tree Warning

Code migration must not start until the current dirty state is classified. The repository currently has unrelated dirty files in source/config/generated outputs and untracked files.

Observed dirty categories include:

- Modified config/source/test files: `config.yml`, `config.yml.example`, `requirements.txt`, `src/action_engine.py`, `src/cache.py`, `src/candidate_comparison.py`, `src/config_schema.py`, `src/data_loader.py`, `src/data_trust_signals.py`, `src/live_core_e2e.py`, `src/selection_engine.py`, `tests/test_data_cache_key.py`.
- Modified documentation registers: `docs/audits/README.md`, `docs/exec_plans/README.md`.
- Modified generated candidate/report/PDF artifacts under candidate folders, `pdf files/`, and `pdf_md_sources/`.
- Modified Python bytecode under `src/__pycache__/`.
- Untracked logs: `candidate_factory_session9_smoke.log`, `candidate_factory_stderr.log`, `candidate_factory_stdout.log`, `portfolio_review_stderr.log`, `portfolio_review_stdout.log`.
- Untracked generated manifests: candidate `candidate_manifest.json` files.
- Untracked IBKR/data provider work: `run_ibkr_market_data.py`, `src/data_ibkr.py`, `src/data_provider.py`, `tests/test_data_ibkr.py`, `tests/test_data_provider.py`.

Before migration code changes, classify each dirty group as one of:

- keep as intentional work in progress;
- revert because unrelated or accidental;
- ignore because generated/cache/log output;
- commit separately because it belongs to another completed task;
- archive generated outputs outside the code migration commit.

No migration session should use `git add -A`; stage only explicitly reviewed files when staging is later requested.

## 9. First Recommended Next Action

First actionable code session after this plan:

**Session 01 - Current runtime and entrypoint inventory**

Goal: freeze a verified architecture inventory and add no behavioral changes. It should document current runtime flow, generated artifacts, entrypoints, module ownership, and dirty-working-tree classification before any migration code starts.

Suggested first commands for that session:

- `git status --short`
- `python run_portfolio_review.py --help`
- `python run_candidate_factory.py --help`
- `python run_compare_variants.py --help`
- `python run_report.py --help`
- `python run_optimization.py --help`
- targeted reads of `docs/specs/portfolio_review_workflow_spec.md`, `docs/specs/candidate_factory_spec.md`, `docs/specs/candidate_comparison_spec.md`, `docs/specs/selection_engine_spec.md`, `OUTPUTS.md`, and `SPEC.md`

Do not start Sessions 02-12 until Session 01 confirms what is clean, what is dirty, and what current runtime behavior must be preserved.
