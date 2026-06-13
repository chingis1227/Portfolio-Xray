# Runtime Truth Reset Plan for Portfolio MRI

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` in the repository root. It is intentionally self-contained: a future agent should be able to start from this file and understand why runtime must change, which files matter, what to edit in each session, and how to prove the result.

## Purpose / Big Picture

The documentation now says the current canonical product is “Diagnosis 2”: diagnose the current portfolio first, classify the problem, launch a selected candidate hypothesis when requested, compare current versus that candidate, and produce a Decision Verdict plus AI grounding and light What Changed. Runtime still behaves partly like the old optimizer/report/scorecard-heavy project: default review can generate a batch of candidates, compare can use stale candidate folders, and the old technical package can drive the selected candidate and verdict. After this runtime reset, a user can run a diagnosis-only product path or a one-candidate product path and see outputs that are about that current portfolio and that selected candidate, while the older full comparison package remains available only as advanced/research behavior.

The observable outcome is simple: after implementation, `python run_portfolio_review.py --candidates equal_weight` must produce a product bundle where `current_vs_candidate.json` and `decision_verdict.json` are scoped to `equal_weight` or a no-trade/evidence-insufficient decision about `equal_weight`, not a stale or higher-scoring candidate from an old folder.

## Progress

- [x] (2026-05-26 Europe/Budapest) Documentation Truth Reset was completed and committed before this plan. Commit observed: `920770e docs: reset canonical product truth`.
- [x] (2026-05-26 Europe/Budapest) Read `PLANS.md` before authoring this ExecPlan.
- [x] (2026-05-26 Europe/Budapest) Inspected runtime entrypoints and adapter modules named in the user request.
- [x] (2026-05-26 Europe/Budapest) Created this plan file only.
- [x] (2026-05-26 Europe/Budapest) Session 01 — Runtime mode policy implemented: added runtime mode resolver, stored `runtime_mode` on `PortfolioReviewPlan`, disclosed it in plan summaries, and covered default/research, diagnosis-only, one-candidate, and shortlist classifications in tests.
- [x] (2026-05-26 Europe/Budapest) Session 02 — Default product behavior implemented: plain `run_portfolio_review.py --dry-run` now resolves to `product_diagnosis_only` and plans only the diagnosis step; backend batch candidate generation is explicit through `--with-candidates`, `--mode full`, `--candidate-profile`, candidate factory control flags, or explicit `--candidates`.
- [x] (2026-05-26 Europe/Budapest) Session 03 — Selected-candidate scoping implemented: explicit-list factory runs now produce a product candidate scope, product comparison/adapters are filtered to baseline plus selected candidates, and tests cover stale/unselected candidate exclusion from product outputs.
- [x] (2026-05-26 Europe/Budapest) Session 04 — Product bundle first implemented: `output_manifest.json` declares `primary_output_surface=product_bundle`, includes `product_bundle_manifest_keys`, orders product bundle paths before technical/advanced paths, and factory `--then-compare` preserves product bundle manifest keys.
- [x] (2026-05-26 Europe/Budapest) Session 05 — Advanced artifact gating implemented: explicit one-candidate product compare skips the old advanced package by default (Health/Robustness/Selection Engine/Action/Monitoring/Journal); writes `candidate_comparison.json` plus the six product bundle files; batch/research comparison keeps the advanced package path.
- [x] (2026-05-26 Europe/Budapest) Session 06 — Output manifest and product discovery implemented: `generated_paths_by_category`, `product_discovery`, legacy/export/subject categories, `discover_product_bundle_paths` / `discover_paths_by_category`; compare, factory, and report manifests use `build_output_manifest_discovery_extra`.
- [x] (2026-05-26 Europe/Budapest) Session 07 — One-candidate demo validation: dry-run + live `run_portfolio_review.py --candidates equal_weight` PASS; `scripts/validate_one_candidate_demo.py` and `tests/test_one_candidate_demo_validation.py`; audit [2026-05-26_runtime_truth_session07_one_candidate_validation.md](../audits/2026-05-26_runtime_truth_session07_one_candidate_validation.md).
- [x] (2026-05-26 Europe/Budapest) Session 08 — Tests and regression boundaries: `tests/test_runtime_mode_regression_boundaries.py` enforces product vs research compare contracts (mode resolution, advanced package gating, stale-folder verdict, shortlist scope, bundle schemas); focused suite 111 passed.
- [x] (2026-05-26 Europe/Budapest) Session 09 — Final runtime truth audit: [2026-05-26_runtime_truth_final_audit.md](../audits/2026-05-26_runtime_truth_final_audit.md); ExecPlan acceptance 6/6 PASS; dry-run + validator + 64-test regression + docs verification OK.

## Surprises & Discoveries

- Observation: `current_vs_candidate.py` already accepts an explicit `candidate_ids` argument and will use it before selection fallback.
  Evidence: `src/current_vs_candidate.py` `_selected_ids()` returns explicit ids first, then falls back to `selection.favored_candidate_id`, then the first available candidate.

- Observation: the main compare writer does not pass explicit candidate ids into `write_current_vs_candidate_outputs()`.
  Evidence: `src/candidate_comparison.py` calls `write_current_vs_candidate_outputs(output_dir=out_dir, comparison=comparison, selection=selection_doc)` without `candidate_ids=...`.

- Observation: `selection_engine.py` chooses a favored candidate from ranked composite evidence and is not currently constrained by the user-requested explicit candidate list.
  Evidence: `_pick_favored_candidate()` in `src/selection_engine.py` iterates over the composite ranking and returns the first favor-eligible row.

- Observation: `run_portfolio_review.py` maps omitted candidate profile through `--mode core -> core_fast`, and `core_fast` is a six-candidate backend batch.
  Evidence: `run_portfolio_review.py` help text says core maps to `core_fast`; `src/candidate_factory.py` maps `REVIEW_MODE_PROFILES["core"] = CORE_FAST_PROFILE_ID`, and `CORE_V1_CANDIDATE_ORDER` is benchmarks plus risk budgets.

- Observation: `write_candidate_comparison_outputs()` writes the old advanced package before and around the product adapters.
  Evidence: in `src/candidate_comparison.py`, the writer builds `robustness_scorecard`, `portfolio_health_score`, `selection_decision`, tradeoff/model risk, assumption sensitivity, Pareto, regret, current-vs-policy, action, monitoring, and journal in the same path as `current_vs_candidate`, `decision_verdict`, `ai_commentary_context`, and `what_changed_summary`.

- Observation: Session 01 can classify runtime without changing execution behavior.
  Evidence: `python run_portfolio_review.py --dry-run --candidates equal_weight` now prints `Runtime mode: product_one_candidate` while still planning the existing explicit candidate factory command.

- Observation: Session 02 changed CLI default behavior but preserved an explicit backend batch escape hatch.
  Evidence: `python run_portfolio_review.py --dry-run` prints `Runtime mode: product_diagnosis_only` and only the diagnosis step; `python run_portfolio_review.py --dry-run --with-candidates` prints `Runtime mode: research_batch` and plans the `core_fast` factory.

- Observation: Session 03 can preserve full `candidate_comparison.json` while scoping product adapters.
  Evidence: the new comparison writer stores `product_candidate_scope` on the full comparison and uses a scoped projection for Selection, Current-vs-Candidate, Decision Verdict, AI grounding, monitoring summary, and downstream product-facing support.

- Observation: `run_candidate_factory.py --then-compare` rewrites `output_manifest.json` after comparison.
  Evidence: `run_candidate_factory.py` calls `write_candidate_factory_outputs()` before compare and again after attaching `comparison_outputs`; Session 04 therefore had to make the factory manifest product-aware too, not only the compare manifest.

- Observation: Decision Verdict previously depended on `selection_decision.json` as its mapping source.
  Evidence: `src/decision_verdict.py` mapped `selection.decision_status` to product verdict language. Session 05 added a support-only selection document for product mode so the product path can avoid writing the advanced Selection Engine artifact while still producing a selected-candidate verdict.

## Decision Log

- Decision: Treat runtime reset as a staged migration, not a deletion of old capabilities.
  Rationale: The user explicitly said old modules may remain as advanced/backend/generated support. Removing modules would risk breaking research and regression workflows.
  Date/Author: 2026-05-26 / Codex.

- Decision: Start implementation with runtime mode policy before invasive code changes.
  Rationale: Selected-candidate scoping is the highest-leverage behavioral fix, but without explicit mode names and CLI-to-mode mapping, later changes can accidentally break research batch or legacy behavior.
  Date/Author: 2026-05-26 / Codex.

- Decision: Product mode must prefer explicit candidate ids over Selection Engine favoring.
  Rationale: In the “Diagnosis 2” product, a candidate is a selected hypothesis. Selection Engine may still rank candidates in research mode, but it must not silently replace the user's selected hypothesis in the product verdict.
  Date/Author: 2026-05-26 / Codex.

- Decision: Plain `run_portfolio_review.py` should now be diagnosis-only, with backend batch retained behind explicit flags.
  Rationale: Documentation Truth Reset made “Diagnosis 2” the canonical product. A no-argument product command should not silently generate a six-candidate backend batch. `--with-candidates` preserves the old core batch path without deleting it.
  Date/Author: 2026-05-26 / Codex.

## Outcomes & Retrospective

**Status: COMPLETED (2026-05-26).** Sessions 01–09 are done. Runtime matches canonical «Diagnosis 2» at the product boundary per [final audit](../audits/2026-05-26_runtime_truth_final_audit.md). Residual operator caveats (technical comparison row count, disk hygiene) are documented there — not ExecPlan blockers.

Session 01 outcome: runtime mode policy is represented in code and tests; dry-run and plan summaries disclose `runtime_mode` for product/research/legacy classification.

Session 02 outcome: the no-argument CLI path plans diagnosis-only product behavior. Backend batch remains reachable with `--with-candidates`, and full research with `--mode full`.

Session 03 outcome: explicit `--candidates` factory runs now carry product scope into compare outputs. Product adapters use the selected candidate ids rather than letting unselected candidate folders control Current-vs-Candidate or Decision Verdict. Full comparison evidence is still written for technical visibility, but product outputs are scoped.

Session 04 outcome: product bundle discovery is now first-class. `output_manifest.json` declares `primary_output_surface=product_bundle`, includes `product_bundle_manifest_keys`, orders resolved product bundle paths before technical/advanced paths, and categorizes old package outputs separately. Factory `--then-compare` rewrites no longer hide the product bundle manifest keys.

Session 05 outcome: explicit one-candidate product compare no longer writes the old advanced package by default. It still writes `candidate_comparison.json` as technical evidence and the six product bundle files, but skips Health/Robustness/Selection Engine/Action/Monitoring/Journal/advanced diagnostics. Batch/research comparison keeps the advanced package path.

Session 06 outcome: `output_manifest.json` now indexes resolved paths by category (`product_bundle`, `technical_comparison`, `subject_diagnostics`, `advanced_evidence`, `orchestration`, `legacy_compatibility`, `generated_export`) and exposes a `product_discovery` block with `product_bundle_paths` and `read_order`. UI/API consumers can use `discover_product_bundle_paths()` without inferring filenames from flat `generated_paths`.

Session 07 outcome: canonical `python run_portfolio_review.py --candidates equal_weight` validated end-to-end on disk (factory single step, product adapters scoped to `equal_weight`, manifest `product_bundle_complete`). Prior demo audit C1/C2 failures are resolved on refreshed run. Operator gate: `python scripts/validate_one_candidate_demo.py`.

Session 08 outcome: `tests/test_runtime_mode_regression_boundaries.py` locks separate contracts — product explicit-list compare skips advanced package and scopes verdicts; research batch (`advanced_package=True`) keeps Health/Robustness/Selection/advanced paths; CLI default remains diagnosis-only while `--with-candidates` / profile plans stay research batch.

Session 09 outcome: final audit confirms all six ExecPlan acceptance criteria PASS. Product default, one-candidate scoping, manifest discovery, and research-batch preservation are evidenced by dry-runs, on-disk validator, regression tests, and docs verification. Plan closed — see `docs/audits/2026-05-26_runtime_truth_final_audit.md`.

## 1. Executive Summary

Runtime must be reset so the code behaves like the documented “Diagnosis 2” product rather than the older optimizer/report/scorecard-heavy system.

The main changes are:

- Default product flow must stop acting like research batch by default. It should either diagnose only or be clearly separated from the current backend `core_fast` regression/batch behavior.
- Selected-candidate behavior must be strict. If the user runs `python run_portfolio_review.py --candidates equal_weight`, product comparison and verdict must be about `equal_weight`, not a stale or higher-ranked candidate.
- Compare and selection scoping must separate product-selected candidates from research/full-menu candidates.
- The six product JSON files must become the product surface: `problem_classification.json`, `candidate_launchpad.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json`.
- Advanced/backend artifacts such as Health Score, Robustness, Selection Engine, Action Plan, Monitoring Diff, Decision Journal, Assumption Sensitivity, Pareto, Regret, and Model Risk must be gated, tagged, or hidden from product mode. They can still exist in research mode.

The implementation should not change formulas, stress scenarios, metric definitions, optimizer math, or existing advanced schemas unless a later session explicitly requires it. This plan is about routing, scoping, output classification, and default behavior.

## 2. Current Runtime Diagnosis

This section describes actual runtime behavior observed from source inspection. It is not a claim about desired product behavior.

`run_portfolio_review.py` is the portfolio-first CLI entrypoint. It accepts `--mode core|full`, `--skip-candidates`, `--candidate-profile`, and `--candidates`. Its help text says omitted candidate profile follows mode, with `core -> core_fast`, and full mode means the entire `default_v1` menu including optimizers and robust suite. It passes `candidate_ids=args.candidates` into `src/portfolio_review_workflow.py`.

`src/portfolio_review_workflow.py` builds the ordered subprocess plan. It resolves the candidate profile, then, unless `skip_candidates` is true, invokes `run_candidate_factory.py`. If `candidate_ids` is supplied it adds `--candidates <ids>`; otherwise it adds `--profile <factory_profile>`. If compare is not skipped, it adds `--then-compare`. This means explicit `--candidates equal_weight` constrains the factory invocation, but not necessarily the downstream comparison evidence scan or Selection Engine favoring.

`run_candidate_factory.py` is the standalone factory CLI. Its default profile is `default_v1`, which is advanced/research full batch behavior. It supports `--candidates`, which maps to explicit list behavior. It can also trigger comparison with `--then-compare`.

`src/candidate_factory.py` defines the candidate menus. `default_v1` contains core benchmarks, risk budgets, classic optimizers, and robust suite. `core_fast` and `core_v1` use the same six benchmark/risk-budget ids. `REVIEW_MODE_PROFILES` maps `core` to `core_fast` and `full` to `default_v1`. The file already classifies `default_v1` as `advanced_research_full_batch` and `core_fast` as `backend_routine_core_batch`, which is helpful but not sufficient for product routing.

`run_compare_variants.py` is a thin wrapper around `src.candidate_comparison.write_candidate_comparison_outputs()`. It does not expose product-vs-research mode selection today.

`src/candidate_comparison.py` is the central old-package writer. It builds `candidate_comparison.json`, then writes advanced and product outputs in one chain. It defines `PRODUCT_MENU_PROFILE_ID = "default_v1"`, which is old product language because the new product should be selected-candidate-first. The writer calls Health Score, Robustness Scorecard, Selection Engine, Current-vs-Candidate, Tradeoff/Model Risk, Assumption Sensitivity, Pareto, Regret, Current-vs-Policy, Action Engine, Decision Verdict, AI Commentary Context, Monitoring, What Changed Summary, and Decision Journal. This means the product bundle is generated, but it is downstream of the old technical package.

`src/current_vs_candidate.py` is close to the desired adapter. It can accept explicit `candidate_ids`. If explicit ids are provided, they are used. If not, it uses `selection.favored_candidate_id`, and if that is missing, it uses the first available non-baseline row. The gap is that `src/candidate_comparison.py` does not pass explicit product candidate ids into this writer.

`src/decision_verdict.py` maps Selection Engine and optional action/current-vs-candidate context into a product-facing `decision_verdict.json`. It uses `selection.favored_candidate_id` as `selected_candidate_id`. This is safe in research mode but risky in product one-candidate mode unless Selection Engine is scoped or the verdict builder can receive an explicit product candidate context.

`src/selection_engine.py` writes `selection_decision.json`. It builds composite rankings and chooses a favored candidate through `_pick_favored_candidate()`. It is not currently a product-selected-candidate gate; it is a technical selector over the comparison candidates. In product mode it should either be scoped to the selected candidate(s) or treated as hidden technical evidence that cannot override the product-selected candidate.

`src/action_engine.py` writes `action_plan.json` based on selection and comparison. This is an advanced/generated support artifact for the new product. It should not be the current product's visible action layer except through high-level `decision_verdict.json`.

`src/monitoring.py` writes technical monitoring snapshots and `monitoring_diff.json`. This is advanced technical evidence. The product should surface `src/light_monitoring_summary.py` and `what_changed_summary.json` first.

`src/decision_journal.py` writes generated V1 journal artifacts based on selection, action, monitoring, health, and robustness. This is not the current Core MVP product journal. It can remain in advanced mode.

`src/ai_commentary_context.py` writes deterministic grounding context, not LLM prose. This aligns with current product truth if clearly called grounding.

`src/light_monitoring_summary.py` writes `what_changed_summary.json` and should remain part of the product bundle.

The main current runtime problems are therefore:

- default review may run six candidates by profile instead of diagnosis-only or selected-candidate product flow;
- explicit `--candidates equal_weight` constrains factory build but not necessarily comparison scan, selection favoring, action, journal, or verdict;
- stale candidate folders can remain visible to comparison and ranking if not filtered by selected ids or run manifest;
- advanced artifacts are generated as part of the product compare path;
- `output_manifest.json` and path discovery can list many technical outputs unless product consumers filter them;
- the product bundle exists but is not structurally first.

## 3. Target Runtime Definition

Runtime must support four product/research modes and one legacy mode.

Mode A is `product_diagnosis_only`. It means: current portfolio -> X-Ray -> Stress -> Problem Classification -> Candidate Launchpad. It does not generate candidates. It does not compare candidates. It may write diagnosis bundle files under `analysis_subject/`. This should be the safest default product behavior if the project chooses to stop default batch candidate generation.

Mode B is `product_one_candidate`. It means: current portfolio -> diagnosis -> launchpad/builder -> selected candidate only -> Current vs Candidate -> Decision Verdict -> AI grounding -> What Changed. For example, `python run_portfolio_review.py --candidates equal_weight` should enter this mode. Product comparison, verdict, and action context must be about `equal_weight` only, or must explicitly say no-trade/evidence-insufficient for `equal_weight`.

Mode C is `product_shortlist`. It means the user explicitly selected two to five candidates. Runtime compares current portfolio against that shortlist only. It must not silently include stale candidate folders outside the shortlist.

Mode D is `research_batch`. It means batch candidates, full comparison, Health Score, Robustness, Selection Engine, Pareto, Regret, Action Plan, Decision Journal, and other old/advanced artifacts are allowed. `run_candidate_factory.py --profile default_v1 --then-compare` and `run_portfolio_review.py --mode full` belong here.

Mode E is `legacy_policy`. It means old optimization/report commands remain available: `run_optimization.py`, policy weights, legacy report exports, legacy current-vs-policy compatibility. This is not current product flow.

The target rule is: product modes can use technical artifacts internally, but the user's visible answer must be the six product JSON files and must respect the selected candidate scope.

## 4. Gap Analysis

Critical gap: batch candidate default. Files involved are `run_portfolio_review.py`, `src/portfolio_review_workflow.py`, and `src/candidate_factory.py`. This violates “Diagnosis 2” because the user starts with diagnosis and a selected hypothesis, not an automatic six-candidate batch. Recommended fix: add explicit runtime mode resolution and choose a staged default. The safe staged rollout is to keep CLI behavior initially but label it as `research_batch` or `backend_core_batch`, then add `--product-diagnosis-only` and later flip the default if approved. Verification: run `python run_portfolio_review.py --dry-run` and confirm the resolved runtime mode is printed or written in workflow state.

Critical gap: stale candidate folder scan. File involved is `src/candidate_comparison.py`. The comparison builder can aggregate evidence from disk wider than the last factory run. This violates product truth because stale candidates can influence product verdict. Recommended fix: add product candidate scope to comparison building, or add a product projection that filters comparison rows to `analysis_subject` plus selected ids before selection/current-vs-candidate/verdict. Verification: create a fixture with stale candidate rows and assert product mode excludes them.

Critical gap: selected-candidate compare not respected end-to-end. Files involved are `src/portfolio_review_workflow.py`, `src/candidate_factory.py`, `src/candidate_comparison.py`, `src/current_vs_candidate.py`, `src/selection_engine.py`, and `src/decision_verdict.py`. Explicit `--candidates equal_weight` constrains the factory, but current compare/selection may still favor another available candidate. Recommended fix: pass explicit candidate ids from factory run or CLI context into comparison output writing, then into `write_current_vs_candidate_outputs()` and selection/verdict scoping. Verification: `python run_portfolio_review.py --dry-run --candidates equal_weight` plus tests asserting selected id is equal_weight.

Critical gap: Health/Robustness/Selection/Action/Journal dominance. File involved is `src/candidate_comparison.py`. The old package is generated in the main writer. This violates the new product because advanced artifacts become the runtime center. Recommended fix: split writer into product bundle writer and advanced package writer, or add a mode flag that gates advanced artifacts. Verification: product mode writes/returns product bundle paths first and marks advanced package skipped or advanced-only.

High gap: product bundle vs technical package priority. Files involved are `src/candidate_comparison.py`, `src/product_bundle_paths.py`, and output manifest code. Product outputs are generated after technical selection/action in the writer. Recommended fix: make product output path discovery first-class and add product mode result summary. Verification: tests in `tests/test_product_bundle_paths.py` and `tests/test_product_bundle_integration.py`.

High gap: output manifest / product discovery. Files involved are `src/product_bundle_paths.py`, manifest writers, and possibly `OUTPUTS.md` in a later docs update. The manifest should index product bundle first and advanced evidence separately. Recommended fix: add artifact categories if missing and ensure product consumers can filter without reading advanced artifacts. Verification: manifest fixture asserts `product_bundle` contains exactly the six files in product mode.

High gap: one-candidate demo path. Files involved are `run_portfolio_review.py`, `src/portfolio_review_workflow.py`, `src/candidate_factory.py`, `src/candidate_comparison.py`, and product adapter tests. This path is the canonical demo and must be reliable. Recommended fix: define `--candidates` as product_one_candidate for one id and product_shortlist for multiple ids unless an explicit research flag is set. Verification: dry-run and focused test prove factory only submits equal_weight.

Medium gap: generated outputs contamination. Existing generated folders can contain old candidate artifacts. Files involved are comparison scanning and output policy. Recommended fix: product mode should either write to a clean run-scoped product context or filter by run manifest and explicit ids. Verification: fixture with extra folder proves product output ignores it.

Medium gap: legacy commands remain near product commands. Files involved are CLI help and docs later. Recommended fix: after runtime mode policy, update help text and docs to label legacy/research. Verification: `--help` output includes mode classification.

## 5. Session-by-Session Runtime Reset Plan

### Session 01 — Runtime mode policy

Objective: define explicit runtime modes: `product_diagnosis_only`, `product_one_candidate`, `product_shortlist`, `research_batch`, and `legacy_policy`.

Files likely affected: `src/portfolio_review_workflow.py`, `run_portfolio_review.py`, `run_candidate_factory.py`, `src/candidate_factory.py`, and tests in `tests/test_portfolio_review_workflow.py`. A small new runtime-mode module could be introduced later if it reduces circular imports, but Session 01 kept the resolver in `src/portfolio_review_workflow.py`.

Exact change type: add a pure resolver that maps CLI inputs to a runtime mode. For example, `skip_candidates=True` maps to `product_diagnosis_only`; one explicit candidate maps to `product_one_candidate`; multiple explicit candidates map to `product_shortlist`; `--mode full` or standalone `default_v1` maps to `research_batch`; `run_optimization.py` remains `legacy_policy`. The resolver should not change formulas, output schemas, optimizer math, or candidate construction.

What not to touch: do not change default behavior yet unless tests only cover the classification. Do not delete profiles.

Tests/checks: run `python -m pytest tests/test_portfolio_review_workflow.py -q`. Add unit tests for the resolver if a new module is created.

Rollback risk: low. A pure resolver can be removed without changing runtime behavior.

Expected output: dry-run or workflow plan can disclose the resolved runtime mode, even if actual behavior is still unchanged.

Commit scope: one small code/test commit named like `runtime: classify portfolio review modes`.

### Session 02 — Default product behavior

Objective: make default product behavior stop acting like batch research, or stage the rollout if changing default behavior is too risky.

Files likely affected: `run_portfolio_review.py`, `src/portfolio_review_workflow.py`, `README.md`, `OUTPUTS.md`, `docs/product_flow_operator_guide.md`, and tests. Documentation edits should happen only in the implementation session, not in this plan.

Exact change type: choose one of two rollout paths. Preferred product path: plain `python run_portfolio_review.py` becomes `product_diagnosis_only`, and candidate generation requires `--candidates` or explicit research mode. Safer staged path: keep current default temporarily, but print/write `runtime_mode=research_batch` or `backend_core_batch` and add a new explicit `--product-diagnosis-only` flag. The plan recommends the staged path if there is concern about breaking existing operator scripts.

What not to touch: do not remove `core_fast`; do not remove `--mode core`; do not change candidate builders.

Tests/checks: run `python run_portfolio_review.py --dry-run` and inspect that the stage list and mode are clear. Run `python -m pytest tests/test_portfolio_review_workflow.py -q`.

Rollback risk: medium if default behavior changes; low if staged with a new flag.

Expected output: a user can clearly run diagnosis-only without generating candidates, and default behavior is no longer mislabeled as the product story.

Commit scope: one behavior/docs-aligned commit if default changes; otherwise one classification commit.

### Session 03 — Selected-candidate scoping

Objective: when the user runs `--candidates equal_weight`, compare/verdict must use `equal_weight`, not all stale folders.

Files likely affected: `src/portfolio_review_workflow.py`, `src/candidate_factory.py`, `src/candidate_comparison.py`, `src/current_vs_candidate.py`, `src/selection_engine.py`, `src/decision_verdict.py`, `tests/test_current_vs_candidate.py`, `tests/test_selection_engine.py`, and `tests/test_candidate_comparison.py`.

Exact change type: carry explicit candidate ids from CLI/factory context into comparison writing. Add a product scope object, for example `product_candidate_ids=("equal_weight",)` or `comparison_scope={"mode": "product_one_candidate", "candidate_ids": [...]}`. Filter product comparison rows to baseline plus selected ids before building Current-vs-Candidate and Decision Verdict. Selection Engine can either receive the same scope or be bypassed for product verdict favoring so it cannot replace the selected hypothesis.

What not to touch: do not change research batch ranking rules; do not change Health Score or Robustness formulas.

Tests/checks: add a fixture where `equal_weight` and `risk_parity` both exist and `risk_parity` would otherwise rank higher. In product_one_candidate mode, assert `current_vs_candidate.selected_candidate_ids == ["equal_weight"]` and `decision_verdict.selected_candidate_id == "equal_weight"` or verdict is no-trade/evidence-insufficient about equal_weight. Run `python -m pytest tests/test_current_vs_candidate.py tests/test_decision_verdict.py tests/test_candidate_comparison.py -q`.

Rollback risk: medium because selection/verdict behavior changes in product mode. Keep research mode unchanged to reduce risk.

Expected output: explicit candidate command cannot be hijacked by stale candidate folders.

Commit scope: one focused code/test commit.

### Session 04 — Product bundle first

Objective: make the six product JSON files the main product-facing surface.

Files likely affected: `src/candidate_comparison.py`, `src/product_bundle_paths.py`, `src/current_vs_candidate.py`, `src/decision_verdict.py`, `src/ai_commentary_context.py`, `src/light_monitoring_summary.py`, tests for product bundle integration.

Exact change type: create a product-mode writer path or refactor `write_candidate_comparison_outputs()` so product bundle outputs are generated and returned as the primary result. The six files are `problem_classification.json`, `candidate_launchpad.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json`. In product mode, advanced paths may be absent, skipped, or written under an explicit advanced category.

What not to touch: do not create LLM commentary; `ai_commentary_context.json` remains grounding only.

Tests/checks: run `python -m pytest tests/test_product_bundle_paths.py tests/test_product_bundle_integration.py tests/test_ai_commentary_context.py tests/test_light_monitoring_summary.py -q`.

Rollback risk: medium because writer return paths and manifest behavior may shift. Keep compatibility aliases if existing tests expect them.

Expected output: product consumers can read the six-file bundle without traversing the old decision package.

Commit scope: one code/test commit.

### Session 05 — Advanced artifact gating

Objective: move or gate Health Score, Robustness, Selection Engine, Assumption Sensitivity, Pareto, Regret, Action Plan, Decision Journal, and full comparison package into advanced/research mode.

Files likely affected: `src/candidate_comparison.py`, output policy code, `run_compare_variants.py`, `src/portfolio_health_score.py`, `src/robustness_scorecard.py`, `src/selection_engine.py`, `src/action_engine.py`, `src/monitoring.py`, `src/decision_journal.py`, and associated tests.

Exact change type: add an output/runtime mode parameter such as `advanced_package=True|False` or `runtime_mode`. In `product_diagnosis_only`, `product_one_candidate`, and `product_shortlist`, do not present advanced outputs as product. Depending on compatibility needs, either skip writing them or write them with explicit advanced category and warnings. In `research_batch`, keep existing behavior.

What not to touch: do not delete modules; do not rename schemas casually; do not remove research batch.

Tests/checks: run advanced artifact tests such as `tests/test_portfolio_health_score.py`, `tests/test_robustness_scorecard.py`, `tests/test_selection_engine.py`, `tests/test_action_engine.py` if present, `tests/test_decision_journal.py`, plus product bundle tests.

Rollback risk: high if existing workflows expect files unconditionally. Mitigate by first gating presentation/manifest, then later gating generation.

Expected output: product mode is not dominated by old score/action/journal package, while research mode still emits it.

Commit scope: one or two commits: first manifest/presentation gating, then generation gating if approved.

### Session 06 — Output manifest and product discovery

Objective: make `output_manifest.json` or equivalent clearly index the product bundle first and advanced evidence separately.

Files likely affected: `src/product_bundle_paths.py`, output manifest writer modules, `run_report.py`, `src/candidate_comparison.py`, and tests.

Exact change type: ensure generated paths include a `product_bundle` category for the six current files and separate categories for `technical_comparison`, `advanced_evidence`, `legacy_compatibility`, and `generated_export`. Product consumers should not need to infer from filenames.

What not to touch: do not refresh generated output folders as part of source changes.

Tests/checks: run `python -m pytest tests/test_product_bundle_paths.py tests/test_product_bundle_integration.py -q`.

Rollback risk: low/medium. Manifest changes can affect UI/API consumers; maintain backward-compatible keys where possible.

Expected output: manifest clearly says what is product and what is advanced.

Commit scope: one code/test commit.

### Session 07 — One-candidate demo validation

Objective: run or dry-run the canonical command and prove product scoping works.

Files likely affected: no source files unless failures are found. If failures are found, return to Sessions 03-06.

Exact change type: validation only. Run `python run_portfolio_review.py --dry-run --candidates equal_weight` first. If safe and data prerequisites are available, run the actual command. Inspect `candidate_factory_run.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json`.

What not to touch: do not commit generated outputs unless the task explicitly asks to refresh them.

Tests/checks:

    python run_portfolio_review.py --dry-run --candidates equal_weight

Expected output:

- factory touches only `equal_weight`;
- `current_vs_candidate.selected_candidate_ids` is `["equal_weight"]`;
- `decision_verdict.selected_candidate_id` is `equal_weight`, or the verdict is no-trade/evidence-insufficient about `equal_weight`;
- no stale candidate folder controls verdict.

Rollback risk: low for dry-run; medium for actual run because generated artifacts may change.

Commit scope: no source commit unless fixes are required.

### Session 08 — Tests and regression boundaries

Objective: add or update tests proving product mode and research mode are different.

Files likely affected: `tests/test_portfolio_review_workflow.py`, `tests/test_candidate_comparison.py`, `tests/test_current_vs_candidate.py`, `tests/test_decision_verdict.py`, `tests/test_product_bundle_paths.py`, `tests/test_product_bundle_integration.py`, and possibly new fixtures.

Exact change type: add focused tests for mode resolution, selected-candidate scoping, stale folder exclusion, product bundle existence/schema versions, and research batch preservation.

What not to touch: do not weaken advanced tests to make product tests pass. Research batch must remain supported.

Tests/checks: run the focused tests above, then broaden to `python -m pytest` if risk warrants.

Rollback risk: low. Tests can be adjusted if they expose intended behavior conflicts.

Expected output: product and research modes have separate, enforced contracts.

Commit scope: one test commit, or combined with the code session that makes the tests pass.

### Session 09 — Final runtime truth audit

Objective: re-run a product-flow demo audit and verify the system now behaves as “Diagnosis 2”.

Files likely affected: new audit file under `docs/audits/` and possibly updates to exec plan progress/outcomes.

Exact change type: audit-only. Inspect commands, output bundle, manifest categories, and stale candidate behavior after implementation.

What not to touch: do not modify code in the audit session unless the user asks.

Tests/checks: run docs verification if docs changed, product bundle tests, selected-candidate tests, and one dry-run demo.

Rollback risk: low.

Expected output: a final audit states whether runtime now matches canonical product truth.

Commit scope: docs-only audit commit if requested.

## 6. What Not To Do

Do not delete old modules. Do not rename schemas casually. Do not remove advanced artifacts. Do not break research batch mode. Do not make LLM AI Commentary now; `ai_commentary_context.json` remains deterministic grounding only. Do not mix generated output refresh with source changes unless the user explicitly asks. Do not use `git add -A`; stage only intended files. Do not treat existing backend artifacts as current product just because they exist. Do not change formulas, stress scenarios, optimizer math, or canonical metric definitions as part of runtime routing. Do not silently change legacy policy behavior.

## 7. Verification Strategy

Use narrow tests first and broaden only when needed.

For diagnosis-only behavior:

    python run_portfolio_review.py --dry-run --skip-candidates
    python -m pytest tests/test_portfolio_review_workflow.py -q

Expected result: the dry-run shows subject materialization and diagnosis outputs without candidate factory steps.

For one-candidate product behavior:

    python run_portfolio_review.py --dry-run --candidates equal_weight
    python -m pytest tests/test_current_vs_candidate.py tests/test_decision_verdict.py tests/test_candidate_comparison.py -q

Expected result: product mode carries `equal_weight` through comparison and verdict.

For adapter bundle behavior:

    python -m pytest tests/test_problem_classification.py tests/test_candidate_launchpad.py tests/test_portfolio_alternatives_builder.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py tests/test_ai_commentary_context.py tests/test_light_monitoring_summary.py tests/test_product_bundle_paths.py tests/test_product_bundle_integration.py -q

Expected result: six product files have schema versions and are discoverable as product bundle.

For research batch regression:

    python run_candidate_factory.py --profile default_v1 --then-compare --dry-run

If `run_candidate_factory.py` does not support dry-run in the current code, use existing factory tests instead:

    python -m pytest tests/test_candidate_factory.py tests/test_candidate_factory_contract.py tests/test_portfolio_health_score.py tests/test_robustness_scorecard.py tests/test_selection_engine.py tests/test_decision_journal.py -q

Expected result: advanced/research code remains available.

For documentation verification if docs change:

    python scripts/verify_docs.py
    python -m pytest tests/test_docs_links.py -q

Expected result: docs verification is OK and docs link tests pass.

## 8. First Recommended Implementation Session

Start with **Session 01 — Runtime mode policy**, then immediately do **Session 03 — Selected-candidate scoping**.

Be blunt: the highest pain is selected-candidate scoping, because it can make the product demo lie by producing a verdict for a candidate the user did not select. However, the first implementation step should still be runtime mode policy because it creates the language and code hook needed to fix scoping safely without breaking research batch. A good first chat should implement a pure `runtime_mode` resolver, update dry-run disclosure, and add tests. The next chat should wire explicit candidate ids into product comparison/verdict.

## 9. Final Verdict

For the project to truly become “Diagnosis 2” at runtime, default and product flows must stop being controlled by the old batch comparison package. Runtime must diagnose the current portfolio first, require an explicit selected candidate for product comparison, scope Current-vs-Candidate and Decision Verdict to that candidate or shortlist, and expose the six product JSON files as the main surface.

Old behavior can remain as advanced/backend: candidate factory full menus, Health Score, Robustness Scorecard, Selection Engine, Action Plan, Monitoring Diff, Decision Journal, Assumption Sensitivity, Pareto, Regret, Model Risk, robust optimizers, legacy policy optimization, and PDF/report exports.

The highest-leverage runtime fix is **selected-candidate scoping**: when the user asks for `equal_weight`, no stale folder or old ranking engine should be able to turn the product verdict into a decision about another candidate. The second highest-leverage fix is gating the advanced downstream package so the product bundle is structurally first.

## Context and Orientation

The repository root is `D:\Desktop\CURSOR TULA DIAGNOSTICS`. Use Windows PowerShell by default. If Python is needed, prefer `.\.venv\Scripts\python.exe` because the project has a virtual environment.

Important terms:

Product bundle means the six JSON files the current product should show first: `problem_classification.json`, `candidate_launchpad.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json`.

Advanced package means old or research outputs that can support analysis but should not be the main product answer: `candidate_comparison.json`, `selection_decision.json`, `portfolio_health_score.json`, `robustness_scorecard.json`, `assumption_sensitivity.json`, `pareto_dominance.json`, `regret_analysis.json`, `model_risk_diagnostics.json`, `tradeoff_explanation.json`, `action_plan.json`, `monitoring_diff.json`, `decision_journal.json`, and `decision_package_summary.json`.

Selected-candidate scoping means that the explicit candidates requested by the user define the product comparison scope. If the user asks for one candidate, product outputs should talk about that one candidate only.

Key files:

- `run_portfolio_review.py` parses the portfolio review CLI.
- `src/portfolio_review_workflow.py` builds the ordered CLI steps.
- `run_candidate_factory.py` and `src/candidate_factory.py` build candidate menus and run candidate scripts.
- `run_compare_variants.py` calls comparison output writing.
- `src/candidate_comparison.py` builds comparison and writes both old advanced artifacts and new product adapters.
- `src/current_vs_candidate.py`, `src/decision_verdict.py`, `src/ai_commentary_context.py`, and `src/light_monitoring_summary.py` are product adapters.
- `src/selection_engine.py`, `src/action_engine.py`, `src/monitoring.py`, and `src/decision_journal.py` are technical/advanced support for the old decision package.

## Plan of Work

The work should proceed in small, safe sessions. First add runtime mode classification without changing behavior. Then wire explicit candidate ids into product comparison and verdict. Then make product bundle paths first-class. Then gate or tag advanced artifacts. Finally validate with dry-run and focused tests.

Each session should make one behavior observable and should not combine source changes with generated output refresh. If a session updates docs, it must run docs verification. If a session updates code, it must run the narrow tests named in that session.

## Concrete Steps

The first implementation session should run:

    cd "D:\Desktop\CURSOR TULA DIAGNOSTICS"
    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_review_workflow.py -q

Then add the runtime mode resolver and tests. After code edits, run the same test again and dry-run:

    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_review_workflow.py -q
    .\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
    .\.venv\Scripts\python.exe run_portfolio_review.py --dry-run --candidates equal_weight

Expected transcript after Session 01 should include a runtime mode disclosure such as `runtime_mode=product_one_candidate` for the explicit equal-weight dry-run. Exact wording can differ, but the mode must be visible in either terminal output, plan object, or workflow metadata.

## Validation and Acceptance

This plan is accepted when it exists as `docs/exec_plans/2026-05-26_runtime_truth_reset_plan.md` and no non-plan files were changed by creating it.

The future runtime reset is accepted when:

- diagnosis-only mode does not generate candidates;
- one-candidate mode uses only the selected candidate in product comparison and verdict;
- stale candidate folders do not control product verdict;
- product bundle files exist and are discoverable first;
- advanced/research mode still supports batch comparison and old artifacts;
- legacy policy commands still work as compatibility paths.

## Idempotence and Recovery

Creating this plan is additive and safe. Future implementation sessions should use additive mode flags, resolver functions, and tests before changing defaults. If a change breaks research batch, revert only that session's files and keep the mode resolver if it is still correct. Do not clean generated outputs or pycache as part of runtime truth reset unless a separate cleanup task is approved.

## Artifacts and Notes

Evidence gathered during plan creation:

    run_portfolio_review.py: omitted candidate profile follows mode, core -> core_fast.
    src/candidate_factory.py: REVIEW_MODE_PROFILES maps core to core_fast and full to default_v1.
    src/candidate_factory.py: default_v1 is classified as advanced_research_full_batch.
    src/current_vs_candidate.py: explicit candidate_ids are honored if passed.
    src/candidate_comparison.py: write_current_vs_candidate_outputs is called without candidate_ids.
    src/candidate_comparison.py: write_candidate_comparison_outputs writes Health, Robustness, Selection, Action, Monitoring, Journal, and product adapters in one chain.

## Interfaces and Dependencies

The Session 01 mode resolver lives in `src/portfolio_review_workflow.py`. If it is later split into a separate module, keep a small stable interface like this:

    RuntimeMode = Literal[
        "product_diagnosis_only",
        "product_one_candidate",
        "product_shortlist",
        "research_batch",
        "legacy_policy",
    ]

    def resolve_portfolio_review_runtime_mode(
        *,
        skip_candidates: bool,
        candidate_ids: str | None,
        review_mode: str,
        candidate_profile: str | None,
    ) -> str:
        ...

The exact implementation can vary, but it must be pure and easy to test. Later sessions can pass the resolved mode into comparison and output writers.

## Revision Notes

2026-05-26 / Codex: Initial plan created after Documentation Truth Reset commit `920770e`. The plan is source-only and does not modify runtime code.

2026-05-26 / Codex: Session 01 implementation recorded. Added runtime mode classification to `src/portfolio_review_workflow.py` and tests in `tests/test_portfolio_review_workflow.py`; dry-run now discloses runtime mode.

2026-05-26 / Codex: Session 02 implementation recorded. Changed `run_portfolio_review.py` default CLI execution planning to product diagnosis-only and added explicit `--with-candidates` backend batch flag plus tests for CLI execution flag resolution.

2026-05-26 / Codex: Session 03 implementation recorded. Added explicit factory-run candidate scope helpers to `src/candidate_comparison.py`, passed scoped comparison into product-facing writers, and added tests in `tests/test_candidate_comparison.py` and `tests/test_current_vs_candidate.py`.

2026-05-26 / Codex: Session 04 implementation recorded. Added product-first manifest helpers in `src/product_bundle_paths.py`, made compare and factory manifests product-aware, preserved product bundle keys after factory `--then-compare`, and added product-first manifest tests.

2026-05-26 / Codex: Session 05 implementation recorded. Added `advanced_package` gating to `write_candidate_comparison_outputs`, passed product explicit-list factory compare as advanced-gated, added product support selection for Decision Verdict, and covered gating in candidate comparison/product bundle tests.

2026-05-26 / Codex: Session 06 implementation recorded. Added manifest category bucketing and product discovery helpers in `src/product_bundle_paths.py`, wired `build_output_manifest_discovery_extra` into compare/factory/report manifests, and extended product bundle path/integration tests.

2026-05-26 / Codex: Session 07 validation recorded. Live one-candidate run PASS; added `scripts/validate_one_candidate_demo.py`, `tests/test_one_candidate_demo_validation.py`, and audit `docs/audits/2026-05-26_runtime_truth_session07_one_candidate_validation.md`.

2026-05-26 / Codex: Session 08 tests recorded. Added `tests/test_runtime_mode_regression_boundaries.py` for product vs research regression boundaries.

2026-05-26 / Codex: Session 09 closure recorded. Final audit `docs/audits/2026-05-26_runtime_truth_final_audit.md`; ExecPlan marked COMPLETED.
