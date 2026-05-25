# Documentation Alignment Audit

Date: 2026-05-25

Scope: current project Markdown documentation after the documentation migration commit `cf2811e`. This audit is documentation-only. It does not modify code, CLI behavior, JSON schemas, generated artifacts, formulas, public fields, or output contracts.

New product architecture used as audit baseline:

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

Required product boundaries:

- diagnosis-first;
- current portfolio first;
- Portfolio MRI / Portfolio X-Ray is a diagnostics and investment decision-support system, not a black-box optimizer;
- candidate portfolios are investment hypotheses, not automatic recommendations;
- no-trade is a valid verdict;
- AI Commentary explains deterministic evidence and must not be the source of calculations or decisions;
- Advanced / Later features stay outside Core MVP unless separately specified, implemented, tested, and approved;
- current implementation claims must remain separate from target architecture and must be checked against `SPEC.md`, `DATA.md`, `OUTPUTS.md`, `TESTING.md`, `RULES.md`, `docs/specs/*.md`, and code.

## 1. Executive Summary

The documentation is now **broadly aligned** with the new Portfolio MRI direction at the top-product layer. The canonical product/vision/architecture docs now clearly present the diagnosis-first and current-portfolio-first workflow, preserve no-trade as a valid outcome, frame candidate portfolios as hypotheses, and separate target architecture from current implementation.

Main remaining inconsistencies:

1. **README.md and AGENTS.md still carry legacy naming**: `Portfolio X-Ray & Optimization Terminal / Portfolio MRI`. This is acceptable as historical/current implementation context, but it slightly weakens the new no-black-box-optimizer positioning.
2. **Some implementation/spec docs still use Selection Engine / No-Trade Recommendation terminology.** This is currently valid because schemas and generated artifacts still use those names, but product-facing docs should continue mapping them to `Decision Verdict` rather than renaming contracts prematurely.
3. **Advanced analytics are implemented or specified in places, but product docs demote them from Core MVP.** This is not a contradiction if the docs say: preserve as current/advanced/backend capability, do not make it core UX.
4. **CHANGELOG.md and historical ExecPlans contain older recommendation/optimizer-first language.** These should normally be preserved as historical records, not rewritten, but should not be treated as current product positioning.
5. **Some specs describe implemented V1 capabilities that the new product direction calls Advanced / Later from a UX perspective**: Portfolio Health Score, Robustness Scorecard, Pareto, Regret, Assumption Sensitivity, Model Risk diagnostics. This requires careful labeling rather than deletion.
6. **Macro/regime materials exist in specs and historical docs.** They should remain preserved/advanced, not Core MVP.
7. **Portfolio Archetype appears in older audit/known issue context.** It should remain optional/later unless implemented and approved.
8. **No serious red flag was found in active product docs claiming AI as calculation source or target modules as implemented without verification.** Remaining risk is mostly in older specs/plans and terminology drift.

Overall status: **Partially aligned but safe**. The active product narrative is aligned; some supporting technical/history docs need light alignment notes, not wholesale rewrites.

## 2. File-by-File Audit

### README.md

- Status: **Partially aligned**
- Correct:
  - Preserves current implementation and source-of-truth hierarchy.
  - Mentions Portfolio X-Ray diagnostics and portfolio-first flow.
  - Separates target product modules from current implementation.
- Conflicts / concerns:
  - Title still says `Portfolio X-Ray & Optimization Terminal`, which can imply optimizer-first positioning.
  - Current project map is still more implementation/CLI/report oriented than product-flow oriented.
- Recommended change:
  - Lightly reframe title/intro to lead with `Portfolio MRI / Portfolio X-Ray` and describe optimization as supporting infrastructure.
  - Preserve all commands, generated-output warnings, and source-of-truth routing.
- Risk: **Medium** because README is the project front door.

### BUSINESS_VISION.md

- Status: **Aligned**
- Correct:
  - Strongly states diagnostics and decision-support identity.
  - Includes the target MVP workflow.
  - Frames candidates as hypotheses and no-trade as valid.
  - States AI is an explanation layer.
  - Advanced / Later Product Backlog is clearly outside Core MVP.
- Conflicts / concerns:
  - Contains the phrase `no-trade recommendation`; acceptable in context but product wording could later prefer `no-trade verdict`.
- Recommended change:
  - Optional wording polish only: use `no-trade verdict` where product-facing tone matters.
- Risk: **Low**.

### PRODUCT.md

- Status: **Aligned**
- Correct:
  - Contains the full target workflow.
  - Clearly separates Core MVP vs Advanced / Later.
  - Keeps Portfolio Archetype Classification as optional/later.
  - States AI explains and code calculates.
  - Marks target modules as requiring code/spec verification.
- Conflicts / concerns:
  - Still maps `Selection Engine` to decision behavior in some glossary/product mapping sections. This is safe if treated as backend/current terminology.
- Recommended change:
  - Keep Selection Engine mapping, but ensure product-facing wording consistently says `Decision Verdict`.
- Risk: **Low**.

### ARCHITECTURE.md

- Status: **Aligned**
- Correct:
  - Explicit current implementation / target architecture / advanced / legacy labels.
  - Target architecture is diagnosis-first and current-portfolio-first.
  - Preserves current CLI/file-driven architecture.
  - Advanced backlog is outside Core MVP.
- Conflicts / concerns:
  - Some current modules are mapped into target layers but remain unresolved as actual product modules.
- Recommended change:
  - No immediate patch required; future architecture patch should only follow code/spec verification.
- Risk: **Low**.

### docs/DIAGNOSTIC_PRODUCT_CONCEPT.md

- Status: **Aligned**
- Correct:
  - Matches the new diagnostic product concept.
  - Contains target flow, Core MVP, Advanced / Later backlog, and current implementation boundary.
  - Portfolio Archetype Classification is optional/later.
- Conflicts / concerns:
  - Some rows classify implemented backend artifacts as target/core-facing concepts; this is acceptable if interpreted as product blueprint, not implementation truth.
- Recommended change:
  - No immediate patch. Later, add a small note that implementation status is owned by specs/code.
- Risk: **Low**.

### SPEC.md

- Status: **Partially aligned**
- Correct:
  - Clearly says `SPEC.md` is current implementation contract.
  - Separates target-only concepts: Problem Classification, Candidate Launchpad, Decision Verdict wording, AI Commentary, etc.
  - Preserves generated artifact contracts.
- Conflicts / concerns:
  - Current implementation still has Selection Engine / No-Trade Recommendation terminology, which is correct technically but product-facing language has moved toward Decision Verdict.
  - Some current advanced artifacts can look like core product capabilities if read without PRODUCT/ARCHITECTURE context.
- Recommended change:
  - Add no broad rewrite. If patched, only add a short cross-reference: Decision Verdict is product language; Selection Engine remains current contract until schema changes are approved.
- Risk: **High** because SPEC governs implementation contracts.

### OUTPUTS.md

- Status: **Partially aligned**
- Correct:
  - Strong generated-vs-source boundary.
  - Notes that target product concepts do not create artifact contracts.
  - Preserves JSON/cache default output policy.
- Conflicts / concerns:
  - Existing output lists necessarily include Selection/Health/Robustness artifacts that product docs demote from core UX.
- Recommended change:
  - Keep all output contracts. Optionally add labels: `current generated artifact`, `advanced/backend evidence`, or `not necessarily Core MVP UI`.
- Risk: **High** because it governs generated artifacts.

### WORKFLOW.md

- Status: **Aligned**
- Correct:
  - Preserves safe implementation workflow and doc-sync rules.
  - Tells agents to keep target product language separate from implementation claims.
- Conflicts / concerns:
  - Does not itself describe the new product architecture in detail; this is fine because it is a workflow doc.
- Recommended change:
  - No patch required.
- Risk: **Low**.

### DECISIONS.md

- Status: **Partially aligned**
- Correct:
  - Contains migration decision and preserves rationale.
  - Historical decisions correctly explain why current artifacts exist.
  - Several decisions already prevent policy output from becoming default recommendation.
- Conflicts / concerns:
  - Older decisions use `Selection Engine`, `No-Trade Recommendation`, `recommendation`, Health Score, and Robustness Scorecard language.
  - These are historical/technical decisions; they should not be rewritten casually.
- Recommended change:
  - Add future decision only if the project formally renames product-facing decision language from Selection Engine to Decision Verdict. Do not edit old decisions except with explicit approval.
- Risk: **Medium**.

### AGENTS.md

- Status: **Partially aligned**
- Correct:
  - Strong operating rules, source-of-truth routing, generated-output policy, CLI commands.
  - Notes product concepts do not override current specs/code.
- Conflicts / concerns:
  - Project summary still starts with `Portfolio X-Ray & Optimization Terminal / Portfolio MRI`.
  - Lists Portfolio Health Score and Robustness Scorecard among V1 decision artifacts; this is implementation-true but can look core-MVP product-facing.
- Recommended change:
  - Lightly reframe summary: `Portfolio MRI / Portfolio X-Ray is diagnosis-first; current implementation remains report-first and CLI/file-driven.`
  - Preserve all commands and operational rules.
- Risk: **Medium** because this file controls agent behavior.

### GLOSSARY.md

- Status: **Aligned**
- Correct:
  - Defines Problem Classification, Candidate Launchpad, Portfolio Alternatives Builder, Decision Verdict, AI Commentary, Monitoring / What Changed.
  - Notes current/current-vs-target boundaries.
- Conflicts / concerns:
  - Selection Engine remains a current term; acceptable if distinguished from Decision Verdict.
- Recommended change:
  - No immediate patch required.
- Risk: **Low**.

### DATA.md

- Status: **Aligned for its role**
- Correct:
  - Owns data-layer rules and generated-output/source-data distinctions.
  - Does not overclaim product behavior.
- Conflicts / concerns:
  - Does not reference the new target product workflow; not necessary unless data contracts change.
- Recommended change:
  - No patch required unless new product modules introduce new data inputs.
- Risk: **Low**.

### TESTING.md

- Status: **Aligned for its role**
- Correct:
  - Strong verification framing.
  - Covers generated outputs and Portfolio X-Ray test bundles.
  - Reinforces current implementation verification.
- Conflicts / concerns:
  - Does not have a specific documentation-alignment checklist for target-vs-current claims.
- Recommended change:
  - Optional: add a small documentation-only verification checklist for product migration tasks.
- Risk: **Low**.

### RULES.md

- Status: **Aligned**
- Correct:
  - Clear source-of-truth hierarchy.
  - Current implementation remains report-first/CLI-file driven.
  - Generated outputs are not source files.
- Conflicts / concerns:
  - Does not lead with new product identity; acceptable because this is a rule map.
- Recommended change:
  - No patch required.
- Risk: **Low**.

### CHANGELOG.md

- Status: **Partially aligned / historical**
- Correct:
  - Historical record of implemented features and sessions.
  - Should preserve old facts and implementation history.
- Conflicts / concerns:
  - Contains many older references to implemented advanced artifacts and recommendation/selection language.
  - Does not include the latest documentation migration commit entry unless added later.
- Recommended change:
  - Add a new top entry for the documentation migration if the project requires changelog updates.
  - Do not rewrite historical entries.
- Risk: **Low to Medium**.

### KNOWN_ISSUES.md

- Status: **Partially aligned**
- Correct:
  - Separates active issues from future ideas.
  - Mentions Portfolio Archetype as an audit finding, not a core implemented feature.
- Conflicts / concerns:
  - Portfolio Archetype evidence could be misread as a current product requirement if not labeled carefully.
- Recommended change:
  - If patched, add a note that Portfolio Archetype is optional/later and not Core MVP unless approved.
- Risk: **Low**.

### docs/specs/*.md

- Status: **Partially aligned as implementation/spec contracts**
- Correct:
  - Detailed specs are implementation-contract documents and should preserve current field names, schemas, formulas, gates, and artifact contracts.
  - Many specs already use diagnostic-only and non-recommendation boundaries.
  - Portfolio-first specs are mostly compatible with the new direction.
- Conflicts / concerns:
  - `selection_engine_spec.md` title and sections use `No-Trade Recommendation`; product docs now prefer `Decision Verdict` / no-trade verdict.
  - `portfolio_health_score_spec.md`, `robustness_scorecard_spec.md`, `pareto_dominance_spec.md`, `regret_analysis_spec.md`, `assumption_sensitivity_spec.md`, and `tradeoff_and_model_risk_spec.md` may look core if read alone, even though product docs classify many of them as Advanced / Later or backend evidence.
  - `macro_regime_spec.md` and stress/macro specs preserve macro functionality that is not Core MVP UX.
  - `candidate_factory_spec.md` and `candidate_portfolios_spec.md` can imply batch candidate generation as a normal backend flow; product direction wants user-triggered hypotheses as core UX.
- Recommended change:
  - Do not rename schemas or public fields.
  - Add non-breaking notes in affected specs: product-facing Core MVP may expose only a subset; implemented artifacts may be backend/advanced evidence.
  - Reframe `No-Trade Recommendation` wording only if schema/API compatibility is preserved.
- Risk: **High** because specs are current contracts.

### docs/exec_plans/*.md

- Status: **Partially aligned / historical planning memory**
- Correct:
  - ExecPlans are living/historical records, not current product source-of-truth.
  - They preserve why advanced modules and decision artifacts were created.
- Conflicts / concerns:
  - Older plans contain optimizer-first, recommendation, scorecard, selection, and advanced-module language from prior direction.
  - Some completed plans may appear to promote advanced artifacts as core unless read historically.
- Recommended change:
  - Do not rewrite completed plans.
  - Update `docs/exec_plans/README.md` if necessary to state that product direction is now owned by canonical docs and migration records.
- Risk: **Low** if treated as history; **Medium** if users read plans as current roadmap.

### docs/audits/*.md

- Status: **Partially aligned / historical audit evidence**
- Correct:
  - Audits are evidence snapshots and should not be rewritten to match new product language.
- Conflicts / concerns:
  - Older audits include Macro Dashboard, Health Score, Robustness Scorecard, Selection Engine, and recommendation language.
- Recommended change:
  - Preserve as historical evidence.
  - Ensure audit register explains old audits are snapshot-at-time, not active product direction.
- Risk: **Low**.

### docs/archive/*

- Status: **Legacy reference only**
- Correct:
  - Old canonical docs were archived under `docs/archive/documentation_migration_2026_05_25/`.
- Conflicts / concerns:
  - Archived legacy files contain older product framing and must not be treated as active source-of-truth.
- Recommended change:
  - No content changes. Keep archive path clearly marked as legacy.
- Risk: **Low**.

### DOCUMENTATION_MIGRATION_PLAN.md and DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md

- Status: **Aligned as migration records**
- Correct:
  - Explain migration logic, source-of-truth boundaries, and session audit.
- Conflicts / concerns:
  - Contain `NEW_*` references as historical process notes; this is acceptable.
- Recommended change:
  - No patch required.
- Risk: **Low**.

### DESIGN.md, PLANS.md, docs/ROADMAP.md, docs/operational_runbook.md, docs/optimization_run_checks.md

- Status: **Partially aligned / not fully audited line-by-line**
- Correct:
  - These are supporting docs, not primary product direction docs.
- Conflicts / concerns:
  - May still contain UI/report/optimization-first assumptions depending on section.
- Recommended change:
  - Include in a later narrow patch pass if the user wants full repo-wide documentation consistency.
- Risk: **Medium** for `docs/ROADMAP.md`, **Low** for operational runbooks unless product language is surfaced to users.

## 3. Red-Flag Search

Search was run over important Markdown files excluding `.venv`, `tmp`, `.pytest_cache`, and generated `pdf_md_sources`.

### Findings by phrase/theme

- `black-box optimizer`
  - Active product docs use this mostly in the correct negative framing: the product is **not** a black-box optimizer.
  - No immediate patch needed.

- `best portfolio`
  - Appears in product docs mostly as a warning that a candidate is **not** the best portfolio.
  - Older/technical specs may use `best available` for regret analysis; this is a technical metric phrase, not product recommendation language.

- `automatic recommendation` / `recommendation`
  - Active product docs largely avoid prescriptive recommendations.
  - Remaining technical terms include `No-Trade Recommendation` in specs and decisions. This is current contract language but should be product-mapped to `Decision Verdict`.

- `optimizer-first`
  - Appears mainly in migration/history context.
  - Older ExecPlan `2026-05-18_portfolio_first_transition_plan.md` contains optimizer-first historical notes; preserve as planning history.

- `automatic batch candidate generation as core UX`
  - No active product doc appears to make this the new Core MVP UX.
  - Candidate factory specs preserve backend batch/factory behavior and should be labeled as implementation/back-end capability, not core UX.

- `Selection Engine as always picking the winner`
  - No active product doc claims it always picks a winner.
  - `selection_engine_spec.md` still owns current decision artifact language; should remain until schema migration is approved.

- `Macro Dashboard as Core MVP`
  - Active product docs place Macro Risk Dashboard / Macro Overlay in Advanced / Later.
  - Older legacy/archive/audit docs contain prior Macro Dashboard framing; treat as legacy/historical.

- `Portfolio Health Score / Robustness Scorecard as main product output`
  - Active product docs demote these from primary product modules.
  - Specs and CHANGELOG correctly document existing artifacts; add labels later if needed to prevent UX confusion.

- `AI as calculation or decision source`
  - Active product docs explicitly say AI explains deterministic evidence.
  - No serious active-doc red flag found.

- `target modules described as implemented without verification`
  - Top product docs contain verification guardrails.
  - Remaining risk is in specs/plans where current artifacts are implemented but target modules have new names.

## 4. Core vs Advanced Check

### Correctly outside Core MVP in active product docs

- Macro Overlay / Macro Risk Dashboard: **Advanced / Later**.
- Strategy Backtest / full backtest block: **Advanced / Later**.
- Scenario & Stress Evaluation for Candidates as full module: **Advanced / Later**.
- Full multi-candidate ranking / advanced research comparison: **Advanced / Later**.
- Portfolio Health Score / Robustness Scorecard as primary product modules: **Advanced / Later / backend evidence**, not primary Core MVP output.
- Assumption Sensitivity: **Advanced / Later**.
- Pareto / Regret / Model Risk: **Advanced / Later / backend evidence**.
- Asset X-Ray: **Advanced / Later**.
- Client-Fit Check: **Advanced / Later**.
- Portfolio Archetype Classification: **Optional / Later diagnostic layer**.
- Advanced optimizer cockpit: **Advanced / Later**.
- Tax-aware / turnover-aware / tactical tilt: **Advanced / Later / target-only unless implemented by accepted spec**.

### Items requiring careful labeling

- Some of these advanced items already have specs or implementation artifacts. That does **not** mean they should become Core MVP UX. They should be documented as current backend/advanced capabilities where verified, or target/later where not verified.

## 5. Current vs Target Check

Potential current-vs-target confusion areas:

1. **Decision Verdict vs Selection Engine**
   - Product target: `Decision Verdict`.
   - Current contract: `selection_decision.json` / Selection Engine specs.
   - Required guardrail: do not rename fields or schemas until approved.

2. **Candidate Launchpad / Portfolio Alternatives Builder**
   - Product target: user-triggered hypothesis workflow.
   - Current implementation: CLI/file-driven candidate factory and comparison artifacts.
   - Required guardrail: do not claim full Launchpad UI or user-triggered product layer is implemented.

3. **AI Commentary**
   - Product target: explanation layer.
   - Current implementation status: requires code/spec verification for exact module scope.
   - Required guardrail: never describe AI as source of calculations or final decision.

4. **Problem Classification**
   - Product target: user-facing classification layer.
   - Current implementation: diagnostic warnings, gates, labels may exist in specs/artifacts.
   - Required guardrail: do not claim formal product Problem Classification module is implemented unless verified.

5. **Monitoring / What Changed**
   - Product target: light monitoring.
   - Current implementation: monitoring artifacts exist, but full monitoring workspace is advanced/later.
   - Required guardrail: distinguish generated monitoring diff artifacts from full product monitoring UI.

## 6. Recommended Patch Plan

Minimal patch plan only; do not execute until approved.

### Patch 1: README.md

- Section: title and first overview paragraphs.
- Replace/reframe:
  - From: `Portfolio X-Ray & Optimization Terminal / Portfolio MRI`
  - To: `Portfolio MRI / Portfolio X-Ray` with note that optimization/candidate builders are supporting infrastructure.
- Preserve:
  - Commands.
  - Source-of-truth map.
  - Current CLI/file-driven implementation notes.
  - Generated-output policy.
- Requires human approval: **Yes**, because README is public/front-door documentation.

### Patch 2: AGENTS.md

- Section: `Project Summary`.
- Replace/reframe:
  - Lead with diagnosis-first decision-support identity.
  - Keep current implementation as report-first and CLI/file-driven.
  - Clarify Health/Robustness/Selection artifacts are current generated artifacts, not necessarily Core MVP product UI.
- Preserve:
  - All commands.
  - Source-of-truth hierarchy.
  - Generated-output policy.
  - Editing and verification rules.
- Requires human approval: **Yes**, because AGENTS.md controls agent behavior.

### Patch 3: SPEC.md and OUTPUTS.md

- Section: current-vs-target / generated outputs notes.
- Add only non-breaking clarification:
  - `Decision Verdict is product-facing target language; Selection Engine / selection_decision remain current implementation contracts until schema migration is explicitly approved.`
  - `Advanced/backend generated artifacts may exist without being Core MVP UX.`
- Preserve:
  - All schemas, commands, fields, generated paths, formulas, and module specs.
- Requires human approval: **Yes**, because these are technical source-of-truth docs.

### Patch 4: docs/specs/*.md selected notes

Candidate files:

- `docs/specs/selection_engine_spec.md`
- `docs/specs/candidate_factory_spec.md`
- `docs/specs/candidate_portfolios_spec.md`
- `docs/specs/portfolio_health_score_spec.md`
- `docs/specs/robustness_scorecard_spec.md`
- `docs/specs/assumption_sensitivity_spec.md`
- `docs/specs/pareto_dominance_spec.md`
- `docs/specs/regret_analysis_spec.md`
- `docs/specs/tradeoff_and_model_risk_spec.md`
- `docs/specs/macro_regime_spec.md`

Recommended wording:

- Add a short status note where missing: `This spec documents current/advanced backend artifacts. Product Core MVP exposure is governed by PRODUCT.md and ARCHITECTURE.md.`
- Preserve all implementation contracts.
- Requires human approval: **Yes**.

### Patch 5: CHANGELOG.md / docs/exec_plans/README.md / docs/audits/README.md

- Add current migration note if desired.
- Clarify old audits/plans are historical snapshots and do not override current product direction.
- Preserve historical entries.
- Requires human approval: **Optional**.

## 7. Verification

Performed during audit:

- `git status --short` before creating the audit.
- Markdown inventory using targeted paths; a broad recursive PowerShell inventory hit access-denied errors inside `tmp/pytest_*`, so generated/temp paths were excluded from the effective audit scope.
- Red-flag search with `rg` over Markdown excluding `.venv/**`, `tmp/**`, `.pytest_cache/**`, and `pdf_md_sources/**`.
- Target phrase checks over canonical docs.

Post-creation verification required:

- Run `git status --short`.
- Confirm only `DOCUMENTATION_ALIGNMENT_AUDIT.md` is new/changed for this task, apart from unrelated pre-existing dirty files already present in the working tree.

## 8. Final Assessment

The active product docs are aligned enough to continue. The safest next step is not a large rewrite, but a small patch pass focused on README/AGENTS and a non-breaking clarification in SPEC/OUTPUTS/specs that product-facing `Decision Verdict` is not yet a schema rename, and that advanced artifacts are preserved capabilities rather than Core MVP UX.
