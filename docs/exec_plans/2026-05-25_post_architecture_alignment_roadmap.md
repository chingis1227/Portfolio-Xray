# Post-Audit Portfolio MRI Architecture Alignment Roadmap

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `PLANS.md` at the repository root. It is intentionally self-contained so a future agent can continue the work without reading chat history. It follows from the audit `docs/audits/2026-05-25_full_project_architecture_alignment_audit.md`, but it repeats the required context here.

## Purpose / Big Picture

Portfolio MRI has moved from an optimizer-first framing toward a diagnosis-first and decision-support architecture. The intended product chain is: input portfolio, Portfolio X-Ray, Stress Test Lab, Problem Classification, Candidate Launchpad, Portfolio Alternatives Builder, Current vs Candidate Comparison, Decision Verdict, AI Commentary, and Monitoring / What Changed.

The immediate user-visible goal is not to add new calculations. The goal is to make the repository safe to continue developing: current docs, specs, runtime descriptions, output contracts, and working-tree state must stop contradicting each other. After this roadmap is complete, a new contributor should be able to open the project documentation and know which files describe current behavior, which features are target UI, which outputs are technical evidence, and which dirty files must not be staged with architecture work.

The first implementation session creates this roadmap and records the dirty-tree baseline only. It does not change code, existing docs, generated outputs, staging, commits, schemas, or generated field names.

## Progress

- [x] (2026-05-25 22:45 +02:00) Read `PLANS.md` fully and confirmed the required ExecPlan sections and living-document rules.
- [x] (2026-05-25 22:45 +02:00) Inspected `docs/audits/2026-05-25_full_project_architecture_alignment_audit.md` and confirmed the highest-priority findings: dirty-tree baseline risk, Target/TBD versus implemented-artifact contradiction, `core_v1` versus `core_fast` command-matrix drift, candidate factory product-boundary risk, stale generated outputs, and AI Commentary grounding-only status.
- [x] (2026-05-25 22:45 +02:00) Captured the current dirty-tree summary: `git status --short` reported 332 entries, including 306 modified/tracked entries and 26 untracked entries before this ExecPlan file was added.
- [x] (2026-05-25 22:45 +02:00) Created `docs/exec_plans/2026-05-25_post_architecture_alignment_roadmap.md` as the single artifact for Session 01.
- [x] (2026-05-25 22:52 +02:00) Session 02 reconciled active source-of-truth docs so new diagnosis-first layers are no longer simultaneously described as target-only and implemented additive artifacts. Updated `README.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `SPEC.md`, and `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`. `OUTPUTS.md` already listed the additive artifacts and was left for Session 05 output-category work.
- [x] (2026-05-25 22:56 +02:00) Session 03 fixed command matrices so default `run_portfolio_review.py --mode core` is documented as `core_fast`, with `core_v1` as sequential/regression compatibility. Updated `README.md`, `OUTPUTS.md`, `docs/specs/candidate_factory_spec.md`, and `docs/operational_runbook.md`; `docs/specs/portfolio_review_workflow_spec.md` already matched this behavior.
- [x] (2026-05-25 23:00 +02:00) Session 04 cleaned Candidate Factory product-boundary wording so full batch generation cannot be mistaken for Core MVP UX. Updated `README.md`, `PRODUCT.md`, and `docs/specs/candidate_factory_spec.md`; no CLI behavior, schemas, code, or generated outputs were changed.
- [x] (2026-05-25 23:02 +02:00) Session 05 defined the product-facing output bundle versus technical/advanced/legacy evidence outputs. Updated `OUTPUTS.md`, `docs/specs/reporting_outputs_spec.md`, and `docs/specs/README.md`; no schemas, code, generated outputs, staging, or commits were changed.
- [x] (2026-05-25 23:04 +02:00) Session 06 updated verification guidance for the new diagnosis-first adapter layers. Updated `TESTING.md` with post-architecture alignment checks, change-type verification, adapter test map, output-bundle acceptance checks, and a Change-To-Check Matrix row; no code, generated outputs, staging, or commits were changed.
- [x] (2026-05-25 23:06 +02:00) Session 07 defined generated-output refresh policy and did not run a refresh because the user requested the session but did not explicitly approve rewriting generated artifacts. Updated `OUTPUTS.md` and `WORKFLOW.md`; no code, generated outputs, staging, or commits were changed.
- [x] (2026-05-25 23:08 +02:00) Session 08 updated documentation registers so the active audit and this ExecPlan are discoverable by future sessions. Updated `docs/audits/README.md`, `docs/exec_plans/README.md`, and `docs/ROADMAP.md`; no code, generated outputs, staging, or commits were changed.
- [x] (2026-05-25 23:15 +02:00) Session 09 fixed archive-link hygiene: corrected relative links in `docs/archive/documentation_migration_2026_05_25/LEGACY_DIAGNOSTIC_PRODUCT_CONCEPT.md`; added archive link guidance to `TESTING.md`; `python scripts/verify_docs.py` and `tests/test_docs_links.py` pass. No code, generated outputs, staging, or commits.
- [x] (2026-05-25 23:25 +02:00) Session 10 locked AI Commentary as grounding-context only: updated active docs/specs (`GLOSSARY.md`, `BUSINESS_VISION.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `SPEC.md`, `OUTPUTS.md`, `README.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`, `docs/specs/ai_commentary_grounding_spec.md`, `docs/specs/reporting_outputs_spec.md`, `docs/specs/README.md`, `docs/ROADMAP.md`, `TESTING.md`). Added backlog `RM-ARCH-010` for future prose-generation spec. No code, schemas, generated outputs, staging, or commits.
- [x] (2026-05-25 23:40 +02:00) Session 11 reviewed runtime product flow in `run_report.py`, `write_candidate_comparison_outputs`, and product adapter modules. Decision: documentation/consumer filtering is sufficient for the Core MVP bundle boundary; a merged `product_bundle.json` writer is not required. Deferred wiring gaps to backlog `RM-ARCH-011` (separate implementation plan). No schemas, orchestration, generated outputs, staging, or commits changed.
- [x] (2026-05-25) Session 12 ran final alignment audit (red-flag searches, docs verification, adapter test bundle **33 passed**), created [Session 12 closure report](../audits/2026-05-25_post_architecture_alignment_session12_closure_report.md), updated exec-plan and audit registers, and closed this ExecPlan. No code, schemas, generated outputs, staging, or commits were changed.

## Surprises & Discoveries

- Observation: The audit file was created and is currently untracked, so even the new active evidence is not yet part of a stable committed baseline.
  Evidence: `git status --short -- docs/audits/2026-05-25_full_project_architecture_alignment_audit.md` showed `?? docs/audits/2026-05-25_full_project_architecture_alignment_audit.md` during the audit handoff.

- Observation: The dirty tree is large enough that any broad command which writes outputs would make attribution worse.
  Evidence: current status before this file showed 332 dirty entries, with many generated portfolio folders, PDFs, Markdown PDF sidecars, pycache files, config files, and unrelated data-provider files.

- Observation: Some source modules for the diagnosis-first layers exist in the working tree, but the active docs still disagree about whether those layers are implemented or target-only.
  Evidence: `SPEC.md` status rows describe `problem_classification.json`, `candidate_launchpad.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json` as implemented additive artifacts, while `PRODUCT.md`, `ARCHITECTURE.md`, and `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` still contain verification/TBD wording for several of the same layers.

- Observation: Session 02 could reconcile implementation status without touching command matrices or generated outputs.
  Evidence: Targeted search after edits leaves only appropriate verification warnings for exact UI behavior, formal diagnosis-only UI state, Selection Engine schema replacement, and remaining unverified target modules; it no longer shows false target-only wording for Problem Classification, Candidate Launchpad, Decision Verdict, or AI grounding.

- Observation: `docs/specs/portfolio_review_workflow_spec.md` already had the correct command semantics before Session 03 edits.
  Evidence: Targeted search showed default `run_portfolio_review.py --mode core` resolving to the `core_fast` factory profile, with `core_v1` described as a regression sequential menu.

- Observation: `docs/specs/candidate_factory_spec.md` still contains product-boundary wording around `default_v1` that is intentionally deferred to Session 04.
  Evidence: Targeted search still finds `Standard product comparison arena` for `default_v1`; Session 03 only corrected command/profile mapping, not candidate factory product framing.

- Observation: Session 04 could remove the most dangerous product-boundary phrase without changing factory contracts.
  Evidence: `Standard product comparison arena` was replaced with advanced/research full-menu language for `default_v1`, while the CLI default `--profile default_v1` remains documented as a standalone factory technical default.

- Observation: Output-category cleanup could be handled as documentation policy without renaming or deleting any generated artifacts.
  Evidence: `OUTPUTS.md` and `docs/specs/reporting_outputs_spec.md` now classify product-facing bundle, technical contracts, advanced/research evidence, action/monitoring/journal evidence, legacy compatibility artifacts, and generated/export artifacts while preserving current file names and specs.

- Observation: The required diagnosis-first adapter tests already exist in the repository.
  Evidence: `tests/test_problem_classification.py`, `tests/test_candidate_launchpad.py`, `tests/test_portfolio_alternatives_builder.py`, `tests/test_current_vs_candidate.py`, `tests/test_decision_verdict.py`, `tests/test_ai_commentary_context.py`, and `tests/test_light_monitoring_summary.py` are present and are now indexed in `TESTING.md`.

- Observation: Session 07 could complete the policy portion without refreshing generated files.
  Evidence: `OUTPUTS.md` now defines when refreshes are allowed, which narrow commands to prefer, and which product-bundle/manifests to inspect; `WORKFLOW.md` now routes generated-output refreshes to that policy. No portfolio folders or manifests were regenerated.

- Observation: The plan and audit registers were stale before Session 08.
  Evidence: `docs/exec_plans/README.md` still had `Active: none`, and `docs/audits/README.md` did not list the 2026-05-25 architecture alignment audit as an active input.

- Observation: Session 09 could clear the long-standing `verify_docs` blocker with link-path fixes only.
  Evidence: Nine broken references at the end of `LEGACY_DIAGNOSTIC_PRODUCT_CONCEPT.md` used one-level-up repo-root and `specs/` relative paths that resolved under `docs/archive/` instead of the repository root and `docs/specs/`; correcting to three-level-up and two-level-up targets made `python scripts/verify_docs.py` return OK without excluding `docs/archive/` from the verifier.

- Observation: Session 10 could complete AI Commentary wording without code changes because most active docs already said grounding-only after Session 02; the main gap was conflation with deterministic `commentary.txt` and one business-workflow line that implied generated AI Commentary already ships.
  Evidence: Targeted `rg` before edits found `BUSINESS_VISION.md` step 11 "generates AI Commentary"; `GLOSSARY.md` defined AI Commentary without a separate grounding-context term; `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` §5.9 lacked implementation-status separation.

- Observation: Session 11 found the Core MVP bundle is already produced by per-artifact adapters, not by one merged writer. Diagnosis adapters run in `run_report.py` under `analysis_subject/`; compare adapters run at `output_dir_final` root via `write_candidate_comparison_outputs`.
  Evidence: `write_problem_classification_outputs` / `write_candidate_launchpad_outputs` in `run_report.py` (~2326–2344); `write_current_vs_candidate_outputs`, `write_decision_verdict_outputs`, `write_ai_commentary_context_outputs`, `write_what_changed_summary_outputs` in `src/candidate_comparison.py` (~2062–2221).

- Observation: Compare still emits the full technical/advanced decision package by design; product leakage risk is consumer-side, not missing bundle files.
  Evidence: `write_candidate_comparison_outputs` always calls health, robustness, selection, pareto, regret, tradeoff, model-risk, journal, and decision-package writers before product adapters.

- Observation: Two runtime wiring gaps remain for portfolio-first consumers even though docs define the bundle.
  Evidence: `write_ai_commentary_context_outputs` in `candidate_comparison.py` does not pass `problem_classification` or `candidate_launchpad` although the builder accepts them; `what_changed_summary` loads `out_dir / "problem_classification.json"` (root) while portfolio-first materialization writes under `analysis_subject/`.

- Observation: Session 12 closure could confirm alignment without refreshing generated outputs or touching the dirty tree.
  Evidence: Red-flag `rg` checks clear on active docs/specs; `verify_docs.py` OK; adapter tests **33 passed**; dirty tree count **346** at closure — unchanged from pre-roadmap risk, explicitly deferred.

## Decision Log

- Decision: Session 01 creates only this ExecPlan and records dirty-tree context; it does not update registers, source docs, code, generated files, or test fixtures.
  Rationale: The audit says the dirty tree is the main safety blocker. Changing multiple files before establishing the working plan would make the baseline less clear.
  Date/Author: 2026-05-25 / Codex.

- Decision: Existing JSON schema names, generated field names, Selection Engine contracts, and candidate factory CLI behavior are not to be renamed or changed by this roadmap unless a later session explicitly creates and approves a schema migration plan.
  Rationale: The audit and active docs state that product-facing Decision Verdict language maps over current technical contracts; it does not silently replace them.
  Date/Author: 2026-05-25 / Codex.

- Decision: Generated outputs are out of scope until Session 07, and even there they require explicit approval before refresh.
  Rationale: Current generated folders are stale relative to new contracts, but refreshing them now would create large noisy diffs and hide source/documentation work.
  Date/Author: 2026-05-25 / Codex.

- Decision: AI Commentary remains a deterministic grounding-context layer for now, not LLM-generated prose.
  Rationale: The implemented artifact described by current specs is `ai_commentary_context.json`; generating natural-language AI commentary is a separate product and safety decision.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 02 updates product and architecture docs to say the new diagnosis-first layers are implemented as additive backend/file artifacts where current specs/code support that, while preserving target status for full UI, default user-triggered candidate generation, schema replacement, and generated AI prose.
  Rationale: The audit identified an internal source-of-truth contradiction. The safest fix is wording/status reconciliation only, not code or schema changes.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 03 changes documentation only. Default portfolio-first core review is documented as `core_fast`; `core_v1` is documented only as a sequential regression/parity profile; `default_v1` is documented as explicit full-menu behavior.
  Rationale: Current code and `docs/specs/portfolio_review_workflow_spec.md` already established this behavior. The risk was stale command-matrix wording, not CLI implementation.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 04 preserves the batch Candidate Factory as implemented backend/advanced/research infrastructure and does not rename factory profiles, generated schemas, or CLI flags.
  Rationale: The audit called for product-boundary cleanup, not code or contract migration. Product-facing language should route through Candidate Launchpad / Alternatives Builder, while factory-only full-menu runs remain available for evidence generation, timing, parity, debugging, and research.
  Date/Author: 2026-05-25 / Codex.

- Decision: The Core MVP product output bundle is `problem_classification.json`, `candidate_launchpad.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json`. `candidate_comparison.json`, `selection_decision.json`, factory manifests, and `output_manifest.json` remain technical contracts. Health, robustness, sensitivity, Pareto/dominance, regret, trade-off, and model-risk outputs remain advanced/research evidence unless a later approved spec changes that.
  Rationale: The new diagnosis-first product flow needs a clear presentation boundary over existing generated evidence without destabilizing current readers or schema contracts.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 06 documents verification selection only. It does not run broad tests, live E2E, CLI refresh, or generated-output refresh because this session changes documentation strategy rather than runtime behavior.
  Rationale: The current dirty tree is large, generated artifacts are intentionally deferred to Session 07, and the safest check for this session is targeted documentation verification.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 07 does not run `run_portfolio_review.py` or any generated-output refresh command.
  Rationale: The roadmap says refresh is optional and only after explicit approval. The user's request to implement Session 07 is enough to define the policy, but not specific enough to approve large generated diffs in the already-dirty tree.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 08 registers the 2026-05-25 architecture alignment audit and this ExecPlan as active project-memory pointers, but does not rewrite historical phases or archived plans.
  Rationale: Registers should help a new chat find the current diagnosis-first alignment work while preserving older roadmaps as implementation history.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 09 fixes broken archive relative links instead of exempting `docs/archive/` from `verify_docs`.
  Rationale: Link-path correction is the least invasive fix, keeps archive docs checkable, and preserves historical archive wording.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 10 keeps AI Commentary at `ai_commentary_context.json` grounding only until `RM-ARCH-010` (future natural-language generation spec) is approved. Deterministic `commentary.txt` / report summaries remain report-pipeline exports and must not be described as LLM AI Commentary.
  Rationale: The audit and current code call only the grounding writer; conflating rule-based commentary with the target AI Commentary product layer would misstate shipped behavior.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 11 — **documentation and consumer filtering are sufficient** for the Core MVP product bundle. UI/API/product surfaces should read the six documented bundle JSON files (resolving `analysis_subject/` paths for diagnosis adapters) and treat `output_manifest.json` as a technical index of all generated paths, not as the product answer. **Do not add a merged `product_bundle.json` writer** in this roadmap; it would duplicate schemas, increase refresh noise, and is unnecessary while per-artifact adapters already exist.
  Rationale: Runtime already writes each bundle artifact via dedicated modules; Sessions 05–10 defined presentation boundaries. A separate merged writer is optional sugar, not required for architecture alignment.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 11 defers small runtime wiring fixes (sidecar path resolution for problem/launchpad in compare + ai_commentary inputs; optional `artifact_categories` in `output_manifest_v1`) to backlog **`RM-ARCH-011`** under a **separate approved implementation plan**. Session 11 does not change orchestration, schemas, or generated outputs.
  Rationale: The plan forbids runtime changes without an explicit implementation plan; the gaps are real but narrow and do not invalidate the filtering-first product boundary decision.
  Date/Author: 2026-05-25 / Codex.

- Decision: Session 12 closes this ExecPlan as **Completed** without code, generated-output refresh, or git staging. Remaining Critical item (dirty tree) and stale generated outputs stay **deferred** with explicit human-review / approved-refresh gates. `RM-ARCH-010` and `RM-ARCH-011` remain backlog-only.
  Rationale: All documentation-alignment sessions (02–11) delivered their scoped outcomes; final audit shows no unresolved High doc contradictions in active canonical sources.
  Date/Author: 2026-05-25 / Codex.

## Outcomes & Retrospective

Session 01 outcome, 2026-05-25: This ExecPlan was created as the roadmap artifact requested after the full architecture alignment audit. It records the planned sequence of work, the dirty-tree baseline, the allowlist discipline for future sessions, and the constraints that code, generated outputs, staging, and commits must not be touched in Session 01.

Remaining after Session 01: The active docs still need reconciliation, command matrices still need the `core_fast` correction, Candidate Factory product-boundary wording still needs cleanup, output categories still need a product-facing bundle policy, generated outputs remain stale, and registers are not yet updated to point at this plan. Those are intentionally deferred to later sessions so each chat can keep context small.

Session 02 outcome, 2026-05-25: Active docs now distinguish implemented additive artifacts from target product UI. `README.md` lists the new diagnosis-first artifacts as current backend/file artifacts while leaving full interactive UX as future scope. `PRODUCT.md`, `ARCHITECTURE.md`, and `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` now describe Problem Classification, Candidate Launchpad, Portfolio Alternatives Builder backend plan, Current-vs-Candidate adapter, Decision Verdict mapping, AI grounding context, and light What Changed summary as implemented additive artifacts where applicable. `SPEC.md` now separates these additive artifacts from remaining target UI/schema/prose work.

Remaining after Session 02: Command matrices still need the `core_fast` versus `core_v1` correction in Session 03. Candidate Factory product-boundary wording still needs cleanup in Session 04. Product-facing output bundle categories remain for Session 05. Generated outputs remain stale and must not be refreshed until Session 07 with explicit approval.

Session 03 outcome, 2026-05-25: Active command matrices now describe default portfolio review correctly: `python run_portfolio_review.py` and `python run_portfolio_review.py --mode core` use factory profile `core_fast`; `core_v1` is a sequential regression/parity profile; `default_v1` is explicit full-menu behavior through `--mode full` or standalone full factory commands. `README.md`, `OUTPUTS.md`, `docs/specs/candidate_factory_spec.md`, and `docs/operational_runbook.md` were updated. No code, generated outputs, schemas, staging, or commits were changed.

Remaining after Session 03: Candidate Factory product-boundary wording remains for Session 04, especially phrasing that can make `default_v1` full batch generation sound like the product UX. Product-facing output categories remain for Session 05. Verification guidance remains for Session 06. Generated outputs remain stale and must not be refreshed until Session 07 with explicit approval.

Session 04 outcome, 2026-05-25: Candidate Factory product-boundary wording is clearer. `README.md` now says standalone batch factory runs are backend/advanced/research operations, not the core product UX. `PRODUCT.md` maps product-facing language to Candidate Launchpad / Alternatives Builder and keeps Candidate Factory as a backend evidence-building tool. `docs/specs/candidate_factory_spec.md` now describes `default_v1` as a standalone factory technical default and advanced/research full menu, not as a standard product comparison arena.

Remaining after Session 04: Product-facing output bundle categories remain for Session 05. Verification guidance remains for Session 06. Generated outputs remain stale and must not be refreshed until Session 07 with explicit approval. Some historical references to Blocks 1-5 and older factory plans remain as traceability; they should not be rewritten unless later sessions find active-source contradictions.

Session 05 outcome, 2026-05-25: Output policy now has explicit categories. `OUTPUTS.md` contains a Product-Facing Output Bundle Policy table. `docs/specs/reporting_outputs_spec.md` mirrors the bundle-vs-evidence boundary for reporting consumers. `docs/specs/README.md` summarizes the category rule for future spec readers. The policy preserves all current JSON file names and schema ownership while making clear what should be product-facing versus technical, advanced/research, action/monitoring/journal, legacy, or generated/export evidence.

Remaining after Session 05: Verification guidance remains for Session 06. Generated outputs remain stale and must not be refreshed until Session 07 with explicit approval. Documentation registers still need Session 08 cleanup. AI prose wording remains for Session 10 after output categories are stable.

Session 06 outcome, 2026-05-25: `TESTING.md` now contains a dedicated Post-Architecture Alignment Checks section. It separates docs-only, command-matrix, output-contract, product-adapter, runtime-orchestration, and generated-output-refresh verification. It maps each diagnosis-first adapter to focused tests and describes output-bundle acceptance checks for a future generated-refresh session. The Change-To-Check Matrix now has a diagnosis-first product adapter row.

Remaining after Session 06: Generated outputs remain stale and must not be refreshed until Session 07 with explicit approval. Documentation registers still need Session 08 cleanup. Archive/docs verification hygiene remains for Session 09. AI prose wording remains for Session 10.

Session 07 outcome, 2026-05-25: Generated-output refresh policy is now explicit. `OUTPUTS.md` defines approved refresh intents, preferred narrow commands, expected artifact checks, generated-diff classification, and the rule that generated artifacts must not be staged or committed automatically. `WORKFLOW.md` now reminds agents not to run refresh commands unless generated artifact changes are explicitly approved and points to the policy. No refresh command was run in this session.

Remaining after Session 07: The current generated outputs may still be stale relative to new diagnosis-first output policy. If the user wants fresh artifacts, start a separate generated-refresh session and explicitly approve the narrow command to run. Documentation registers still need Session 08 cleanup. Archive/docs verification hygiene remains for Session 09. AI prose wording remains for Session 10.

Session 08 outcome, 2026-05-25: Documentation registers now point future agents to the active architecture alignment work. `docs/audits/README.md` lists `docs/audits/2026-05-25_full_project_architecture_alignment_audit.md` as active input. `docs/exec_plans/README.md` marks this ExecPlan as Active and adds it to Major Plan History. `docs/ROADMAP.md` now states the current diagnosis-first / decision-support product direction and clarifies that older phases are historical project memory, not current product direction.

Remaining after Session 08: Archive/docs verification hygiene remains for Session 09. AI prose wording remains for Session 10. Runtime product flow review remains for Session 11. Final closure remains for Session 12.

Session 09 outcome, 2026-05-25: Archive documentation verification hygiene is fixed. The footer links in `docs/archive/documentation_migration_2026_05_25/LEGACY_DIAGNOSTIC_PRODUCT_CONCEPT.md` now resolve to current repo-root and `docs/specs/` targets. `TESTING.md` documents the archive relative-link convention. `python scripts/verify_docs.py` and `python -m pytest tests/test_docs_links.py -q` both pass.

Remaining after Session 09: AI prose wording remains for Session 10. Runtime product flow review remains for Session 11. Final closure remains for Session 12.

Session 10 outcome, 2026-05-25: Active docs now distinguish three commentary concepts: (1) target AI Commentary product layer, (2) implemented `ai_commentary_context.json` grounding only (no LLM), and (3) deterministic report commentary (`commentary.txt`, stress commentary, decision-package summaries). Misleading wording such as "generates AI Commentary" in `BUSINESS_VISION.md` was corrected. Future LLM prose is deferred to backlog `RM-ARCH-010` in `docs/ROADMAP.md`, referenced from the grounding spec. No code, schemas, generated outputs, staging, or commits were changed.

Remaining after Session 10: Runtime product flow review remains for Session 11. Final closure remains for Session 12.

Session 11 outcome, 2026-05-25: Runtime product flow was reviewed end-to-end for portfolio-first review. The Core MVP bundle is already implemented as six separate adapter writers at two stages (diagnosis under `analysis_subject/`, compare at `output_dir_final` root). **Product boundary = documented bundle list + consumer filtering**, not a new merged bundle file. Compare continues to emit technical/advanced evidence for traceability; product surfaces must not promote health/robustness/selection/Pareto/regret as the main answer. `output_manifest.json` remains a technical path index without product/technical categories until `RM-ARCH-011`. `OUTPUTS.md` now documents default portfolio-first paths for bundle resolution. No code, schemas, generated outputs, staging, or commits were changed in Session 11.

Remaining after Session 11: Optional `RM-ARCH-011` implementation (sidecar path wiring, ai_commentary inputs, manifest categories). Generated outputs may still be stale until an approved refresh session. Final alignment audit and ExecPlan closure remain for Session 12.

Session 12 outcome, 2026-05-25: Final alignment audit completed. Red-flag searches show no active-doc contradictions for command matrices, Candidate Factory product boundary, AI Commentary grounding, or false target-only wording for implemented additive artifacts. `python scripts/verify_docs.py` OK; `tests/test_docs_links.py` **6 passed**; diagnosis-first adapter bundle **33 passed**. Critical/High audit findings are **resolved**, **accepted** (compare emits full technical package; consumer filtering), or **deferred** (dirty tree **346** entries, stale generated outputs, `RM-ARCH-011`, `RM-ARCH-010`, config/provider human review). Closure report: [2026-05-25_post_architecture_alignment_session12_closure_report.md](../audits/2026-05-25_post_architecture_alignment_session12_closure_report.md). ExecPlan and audit registers updated to **Completed** / **Historical**. No code, schemas, generated outputs, staging, or commits were changed in Session 12.

**Roadmap closed.** Next work is outside this ExecPlan: allowlisted migration commit, optional generated refresh, or separate plans for `RM-ARCH-010` / `RM-ARCH-011`.

## Context and Orientation

The repository root is `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`. User-facing chat should be in Russian by default, but project source files and documentation remain English unless the user explicitly requests otherwise.

Portfolio MRI is a Python portfolio diagnostics and investment decision-support project. The important product distinction is that it should not be framed as a black-box optimizer. Optimizers and candidate builders are implementation capabilities used to create hypotheses and evidence. The target product flow starts with the user's current or model portfolio, diagnoses it, stress-tests it, classifies problems, suggests hypothesis paths, compares a current portfolio to one selected candidate or shortlist, produces a decision verdict, grounds commentary in deterministic evidence, and monitors what changed.

The current implementation is still CLI/file-driven. The main normal entrypoint is `run_portfolio_review.py`, which materializes `{output_dir_final}/analysis_subject/` before running candidate factory and comparison steps. Legacy policy optimization remains in `run_optimization.py` and must stay compatibility-only unless a future task explicitly changes it.

The key audit input is `docs/audits/2026-05-25_full_project_architecture_alignment_audit.md`. That audit found that the project is conceptually mostly aligned, but not systemically clean. Its critical problems are: unsafe dirty tree, docs disagreeing about implementation status, and generated outputs being stale relative to new output contracts. Its high-priority problems include `core_v1` versus `core_fast` docs drift, Candidate Factory boundary drift, old score/selection artifacts dominating runtime output, standalone factory defaulting to `default_v1`, AI Commentary being only grounding context, active-register mismatch, archive-link verification blockers, and mixed config/provider changes.

`DIRTY_TREE_CLASSIFICATION.md` already classifies much of the dirty tree. Use it as an input, not as a source of truth that overrides current `git status`. It says migration-related code/docs/specs/tests should be kept for later review, generated artifacts should not be committed with migration work, `config.yml`, `config.yml.example`, and `requirements.txt` need human review, and unrelated IBKR/data-provider work should not be staged with Portfolio MRI architecture migration.

Important terms used in this plan:

- Core MVP means the minimal product experience that should be shown as the main Portfolio MRI user journey.
- Technical contract means a JSON schema, field name, module API, CLI flag, or generated artifact that current code depends on and that must not be renamed casually.
- Additive artifact means a new output or adapter added next to existing contracts without replacing or renaming them.
- Generated output means files produced by running the project, such as portfolio folders, PDFs, `pdf_md_sources`, JSON report outputs, pycache, and caches. These are not source-of-truth unless a task explicitly targets them.
- Product-facing output means an output intended to support the target diagnosis-first user journey, such as `decision_verdict.json`. Technical evidence outputs like `selection_decision.json` may remain current contracts while not being the main product answer.

## Plan of Work

The work must be split into separate sessions. Do not try to complete multiple sessions in one chat unless the user explicitly asks and the tree is already clean enough. Each session should begin by reading this ExecPlan, the full architecture audit, `AGENTS.md`, `WORKFLOW.md`, `SPEC.md`, `OUTPUTS.md`, and any detailed specs relevant to the session. Each session should end by updating this ExecPlan's `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` sections.

Session 02 reconciles source-of-truth status. It updates active product and implementation docs so they no longer describe the same new diagnosis-first layers as both target-only and implemented. It should touch only active docs such as `README.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `SPEC.md`, `OUTPUTS.md`, and `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`. It must preserve the distinction between implemented backend artifacts, target UI, and future schema migrations.

Session 03 fixes command matrices. It updates docs that still say default core review uses `core_v1`. Current code and `docs/specs/portfolio_review_workflow_spec.md` say default `--mode core` uses `core_fast`. `core_v1` should be described as a sequential regression or compatibility profile. This session should not alter `src/candidate_factory.py` or CLI behavior.

Session 04 cleans Candidate Factory product-boundary language. It removes or reframes phrases like `Standard product comparison arena` for `default_v1`. It must keep `run_candidate_factory.py --profile default_v1` available as advanced/research backend infrastructure, not as the Core MVP user journey. It must not change candidate factory JSON schemas or command behavior.

Session 05 defines product-facing output bundle policy. It clarifies which JSON files are part of the diagnosis-first product flow and which are technical, advanced, legacy, or generated evidence. The product bundle should include `problem_classification.json`, `candidate_launchpad.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json`. Technical/advanced evidence includes `candidate_comparison.json`, `selection_decision.json`, `portfolio_health_score.json`, `robustness_scorecard.json`, `assumption_sensitivity.json`, `pareto_dominance.json`, and `regret_analysis.json`.

Session 06 updates verification guidance. It adds a clear test matrix for the new diagnosis-first adapters and for docs-only, output-contract, product-adapter, and generated-refresh changes. Use existing tests where available, such as `tests/test_problem_classification.py`, `tests/test_candidate_launchpad.py`, `tests/test_portfolio_alternatives_builder.py`, `tests/test_current_vs_candidate.py`, `tests/test_decision_verdict.py`, `tests/test_ai_commentary_context.py`, `tests/test_light_monitoring_summary.py`, and comparison/manifest contract tests. If Python is needed on Windows, prefer the project `.venv` Python if it exists, otherwise follow the repository's Python setup rules.

Session 07 handles generated-output policy and optional refresh. It must not run refresh commands unless the user explicitly approves. If approved, run the narrowest portfolio-first refresh needed to produce the new product-facing JSON artifacts and updated manifests, then classify generated diffs separately from source/docs. Do not commit generated outputs automatically.

Session 08 updates documentation registers. It registers the full architecture audit as active input and this ExecPlan as active plan, and adds a roadmap note that the current product direction is diagnosis-first while old phases are historical implementation memory. It should not rewrite archive docs.

Session 09 fixes archive-link or docs-verification hygiene. It determines why `scripts/verify_docs.py` fails on archive links and chooses the least invasive solution: fix broken relative links or adjust verification policy for archive-only docs. It must not rewrite historical product content.

Session 10 locks AI Commentary wording. It checks active docs/specs for false claims that AI already writes final commentary or makes decisions. It should preserve `ai_commentary_context.json` as deterministic grounding and move any AI prose generation to a future explicit spec/backlog item.

Session 11 reviews runtime product flow. After docs/output policy cleanup, inspect `src/candidate_comparison.py` and product adapter modules to decide whether documentation filtering is enough or whether a separate product bundle writer is needed. Record the decision in this ExecPlan. Do not change schemas or runtime orchestration without a separate approved implementation plan.

Session 12 closes the roadmap with a final alignment check. Repeat red-flag searches, review docs/spec/code/output consistency, update this ExecPlan's retrospective, and create a short closure note. The closure condition is that no Critical or High contradictions remain except those explicitly accepted or deferred.

## Concrete Steps

For Session 01, already performed in this file creation session:

1. From the repository root, read `PLANS.md` completely.
2. Inspect the architecture audit headings and high-priority findings.
3. Run `git status --short` and summarize the dirty tree.
4. Create `docs/exec_plans/2026-05-25_post_architecture_alignment_roadmap.md` with this self-contained plan.
5. Verify only this new ExecPlan file was added by this session.

For Session 02, start a new chat and do only source-of-truth status reconciliation. The recommended opening commands are:

    cd "D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА"
    git status --short
    rg -n "Target/TBD|requires code/spec verification|Problem Classification|Candidate Launchpad|Decision Verdict|AI Commentary|what_changed_summary|implemented additive" README.md PRODUCT.md ARCHITECTURE.md SPEC.md OUTPUTS.md docs\DIAGNOSTIC_PRODUCT_CONCEPT.md

For Session 03, start a new chat after Session 02 is complete. The recommended opening search is:

    rg -n "core_v1|core_fast|--mode core|default_v1" README.md OUTPUTS.md docs\specs\candidate_factory_spec.md docs\specs\portfolio_review_workflow_spec.md docs\operational_runbook.md

For Session 04, start a new chat after Session 03 is complete. The recommended opening search is:

    rg -n -i "standard product comparison arena|default_v1|batch candidate|full menu|product UX|advanced|research" docs\specs\candidate_factory_spec.md README.md PRODUCT.md ARCHITECTURE.md docs\DIAGNOSTIC_PRODUCT_CONCEPT.md

For every session, update this ExecPlan before stopping. If the session changes files, run at least:

    git status --short
    git diff --name-only

Do not stage or commit unless the user explicitly asks.

## Validation and Acceptance

Session 01 acceptance is simple and file-based. `docs/exec_plans/2026-05-25_post_architecture_alignment_roadmap.md` must exist and `git status --short -- docs/exec_plans/2026-05-25_post_architecture_alignment_roadmap.md` must show it as untracked or modified. No code, generated outputs, config files, existing docs, staging, or commits should be changed by Session 01.

For later documentation sessions, validation should combine targeted search and lightweight doc checks. Because the current audit reports that `scripts/verify_docs.py` may fail on archive links, do not treat that failure as a blocker for early sessions unless the session is specifically fixing docs verification. Capture the exact failure in `Surprises & Discoveries` if it happens.

For code-adjacent later sessions, use the narrowest relevant tests. Do not run full generated-output refresh commands until Session 07 and only with explicit user approval.

The final roadmap acceptance is that a future audit can say: active docs agree on implemented versus target status, command matrices match actual code, Candidate Factory is not framed as the Core MVP UX, product-facing outputs are clearly separated from technical/advanced evidence, AI is not framed as decision-maker or calculator, and generated-output refresh policy is explicit.

## Idempotence and Recovery

This plan is safe to read and update repeatedly. If Session 01 is run again and this file already exists, do not overwrite it blindly. Read it, update `Progress` with a new note, and preserve existing decisions and discoveries.

Do not clean or delete generated files as part of this roadmap unless a later session explicitly asks for generated-output cleanup and records the decision. Do not use destructive git commands. Do not stage unrelated files. The dirty tree contains unrelated and generated changes; use `git status --short -- <path>` to verify each path before editing or reporting it.

If a session accidentally changes files outside its scope, stop and report the exact paths. Do not revert user changes unless explicitly requested. Prefer a narrow follow-up plan for cleanup.

## Artifacts and Notes

Important evidence from Session 01:

    Current audit file:
    docs/audits/2026-05-25_full_project_architecture_alignment_audit.md

    Current dirty-tree summary before this ExecPlan file:
    total git status entries: 332
    modified/tracked entries: 306
    untracked entries: 26

    Existing target plan check before creation:
    Test-Path docs\exec_plans\2026-05-25_post_architecture_alignment_roadmap.md
    False

Important files that are safe to consider as architecture-migration candidates in later sessions, subject to fresh `git status` verification:

- Active source-of-truth docs: `README.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `SPEC.md`, `OUTPUTS.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.
- Candidate factory and workflow specs: `docs/specs/candidate_factory_spec.md`, `docs/specs/portfolio_review_workflow_spec.md`, `docs/specs/README.md`.
- New diagnosis-first specs: `docs/specs/problem_classification_spec.md`, `docs/specs/candidate_launchpad_spec.md`, `docs/specs/portfolio_alternatives_builder_spec.md`, `docs/specs/current_vs_candidate_spec.md`, `docs/specs/decision_verdict_spec.md`, `docs/specs/ai_commentary_grounding_spec.md`, `docs/specs/light_monitoring_summary_spec.md`, `docs/specs/workflow_state_spec.md`.
- Registers only after early fixes: `docs/audits/README.md`, `docs/exec_plans/README.md`, `docs/ROADMAP.md`.

Important paths that must not be committed with architecture docs unless a later session explicitly scopes them:

- Generated portfolio folders such as `hierarchical risk parity portfolio/`, `maximum diversification unconstrained portfolio/`, `minimum cvar constrained portfolio/`, `minimum cvar uncapped portfolio/`, `risk budget by asset portfolio/`, `risk budget by asset-class portfolio/`, `robust mean variance constrained portfolio/`, and `robust mean variance uncapped portfolio/`.
- Generated report/export folders such as `pdf files/`, `pdf_md_sources/`, `Main portfolio/` generated artifacts, `cache/`, and `__pycache__/`.
- Config/environment files `config.yml`, `config.yml.example`, and `requirements.txt` until reviewed separately.
- Unrelated data-provider and IBKR work such as `run_ibkr_market_data.py`, `src/data_ibkr.py`, `src/data_provider.py`, `tests/test_data_ibkr.py`, and `tests/test_data_provider.py` until reviewed separately.

## Interfaces and Dependencies

This roadmap does not introduce public Python APIs, JSON schemas, CLI flags, or generated fields. It is a documentation and planning artifact.

The later sessions must preserve these existing interfaces unless a separate approved plan says otherwise:

- `run_portfolio_review.py` remains the main portfolio-first CLI entrypoint.
- `run_optimization.py` remains legacy policy optimization compatibility.
- `run_candidate_factory.py` remains backend/advanced/research candidate-building infrastructure.
- `candidate_comparison.json` remains the canonical technical comparison contract.
- `selection_decision.json` and Selection Engine fields remain technical decision contracts.
- `decision_verdict.json` remains an additive product-facing mapping over Selection/No-Trade evidence.
- `ai_commentary_context.json` remains deterministic grounding context and does not call an LLM.

Revision note, 2026-05-25: Initial ExecPlan created from the post-audit roadmap requested by the user. The first session is intentionally limited to creating this plan and recording dirty-tree context so future sessions can proceed safely one at a time.

Revision note, 2026-05-25 (Session 12): Roadmap closed. See [Session 12 closure report](../audits/2026-05-25_post_architecture_alignment_session12_closure_report.md).
