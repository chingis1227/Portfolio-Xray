# Documentation Synchronization Contract

Status: **canonical documentation-governance contract** for Portfolio MRI / Portfolio X-Ray product, code, design, QA, generated-output, and ExecPlan work.

Scope: documentation impact rules, source-of-truth routing, dynamic documentation sync matrix, final-response reporting, generated-output boundaries, and examples of when owning docs must be updated or explicitly waived. This contract does not change runtime behavior, backend formulas, frontend implementation, tests, generated artifacts, routes, schemas, or visual styling by itself.

This contract exists to prevent product-code-design-doc drift. Future sessions must not treat a meaningful product, code, design, QA, workflow, output, or source-of-truth change as complete until the documentation impact has been checked and either updated or explicitly waived with a reason.

## Source-of-truth precedence

Use this order when deciding which document owns a change:

1. `AGENTS.md` for agent operating rules, repository routing, generated-output handling, browser QA hygiene, editing discipline, and final response expectations.
2. `WORKFLOW.md` for task flow: source-of-truth check, planning, implementation, documentation sync, verification, diff review, and reporting.
3. `PLANS.md` and the active `docs/exec_plans/*.md` file for large, risky, multi-session, or architectural work. ExecPlans are living documents and must be updated as work proceeds.
4. `SPEC.md` for current implementation behavior, general contracts, product status matrix, workflows, inputs, outputs, and behavior rules.
5. `DATA.md` for data sources, data pipeline, structures, quality rules, FX, benchmarks, risk-free inputs, factor/macro inputs, and data validation.
6. `OUTPUTS.md` for generated-output folders, artifact names, output profiles, formats, report packaging, product-bundle interpretation, and generated-vs-source boundaries.
7. `TESTING.md` for verification strategy, check selection, focused pytest routing, docs verification, generated-output checks, and known full-suite caveats.
8. `docs/contracts/*.md` for cross-cutting product-code-design contracts:
   - `docs/contracts/PRODUCT_FLOW_CONTRACT.md`
   - `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`
   - `docs/contracts/SCREEN_CONTRACTS.md`
   - `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`
   - `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`
   - `docs/contracts/QA_CONTRACT.md`
   - this `docs/contracts/DOC_SYNC_CONTRACT.md`
9. `docs/specs/*.md` for detailed module, schema, formula, runtime, and artifact behavior.
10. `README.md`, `PRODUCT.md`, `../../frontend/README.md`, `DESIGN.md`, `docs/design/*`, runbooks, audit docs, `KNOWN_ISSUES.md`, `DECISIONS.md`, and `CHANGELOG.md` for user-facing orientation, product direction, frontend operation, design direction, operator procedures, active risks, accepted decisions, and completed-change history.

Product concept documents and archived migration records guide direction and traceability, but they do not override `SPEC.md`, `DATA.md`, `OUTPUTS.md`, `TESTING.md`, detailed specs, contracts, or current code behavior.

## Documentation impact rule

Any meaningful change is incomplete until the owning documentation has been checked.

A meaningful change includes changes to behavior, formulas, estimators, inputs, configs, commands, runtime modes, output folders, artifact names, JSON/CSV/TXT/HTML/PDF contracts, frontend routes, adapters, UI copy, design tokens, visual states, QA commands, source-of-truth routing, known limitations, decisions, or product boundaries.

For every meaningful change, the agent must do one of the following before reporting completion:

1. update the owning docs in the same session; or
2. explicitly waive the documentation update in the final response with a clear reason.

The waiver must be specific. Acceptable examples:

- `Docs waived: typo-only comment change; no behavior, command, output, UI, or contract changed.`
- `Docs waived: implementation matched existing SPEC.md and OUTPUTS.md wording; no source-of-truth text changed.`
- `Docs waived: investigation only; no files changed.`

Unacceptable examples:

- `Docs not needed.`
- `Small change.`
- `Will update later.`

Documentation impact is part of QA. A session is not complete until docs updated/waived, checks run/waived, and unverified areas are reported.

## Dynamic documentation sync matrix

Use this matrix to decide which documents to inspect and update. Update the narrowest owning docs first, then update broad maps only when their contract, workflow, command, or source-of-truth summary changes.

| Change type | Primary docs to check/update | Also check/update when relevant |
| --- | --- | --- |
| Product flow, product boundary, Core MVP vs advanced/legacy/backlog status | `PRODUCT.md`, `SPEC.md`, `docs/contracts/PRODUCT_FLOW_CONTRACT.md`, `docs/contracts/SCREEN_CONTRACTS.md` | `README.md`, `docs/product_flow_operator_guide.md`, `docs/runtime_entrypoints.md`, `DECISIONS.md`, `CHANGELOG.md`, owning `docs/specs/*` |
| Artifact, schema, output folder, output profile, generated-output policy, or report/package behavior | `OUTPUTS.md`, owning `docs/specs/*`, `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` | `SPEC.md`, `README.md`, `TESTING.md`, `docs/runtime_artifact_contract.md`, `docs/product_flow_operator_guide.md`, `CHANGELOG.md`, `DECISIONS.md` |
| Screen, route, CTA, unlock state, empty/blocked state, active `reviewId` lineage, or frontend adapter behavior | `../../frontend/README.md`, `docs/contracts/SCREEN_CONTRACTS.md`, `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`, `docs/contracts/QA_CONTRACT.md` | `PRODUCT.md`, `README.md`, `docs/demo/frontend_backend_vertical_runbook.md`, `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`, `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`, `TESTING.md`, `CHANGELOG.md` |
| UI copy, labels, report wording, forbidden terms, presentation language, candidate/verdict/AI boundary language | `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`, `docs/contracts/SCREEN_CONTRACTS.md` | `../../frontend/README.md`, `PRODUCT.md`, `README.md`, `docs/design/portfolio_mri_design_system.md`, `docs/contracts/QA_CONTRACT.md`, `CHANGELOG.md` |
| Design tokens, colors, badge taxonomy, card hierarchy, layout, CTA styling, sample/demo visuals, visual QA standard | `docs/design/portfolio_mri_design_system.md`, `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` | `DESIGN.md`, `../../frontend/README.md`, `docs/contracts/SCREEN_CONTRACTS.md`, `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`, `docs/contracts/QA_CONTRACT.md`, `CHANGELOG.md` |
| QA/test workflow, package scripts, pytest routing, visual QA workflow, forbidden-term scan, docs verification | `TESTING.md`, `docs/contracts/QA_CONTRACT.md` | `../../frontend/README.md`, `docs/demo/frontend_backend_vertical_runbook.md`, `AGENTS.md` if agent/browser rules change, `WORKFLOW.md`, `CHANGELOG.md`, `DECISIONS.md` for permanent policy decisions |
| Backend formula, metric, estimator, stress logic, optimizer behavior, data alignment, rounding, fallback, or data quality behavior | `SPEC.md`, `DATA.md`, owning `docs/specs/*`, `TESTING.md` | `OUTPUTS.md`, `README.md`, `DECISIONS.md` for methodology choices, `KNOWN_ISSUES.md` for unresolved risk, `CHANGELOG.md` for meaningful completed changes |
| Runtime commands, CLI defaults, runtime modes, orchestration stage order, local setup commands, package scripts | `README.md`, `docs/runtime_entrypoints.md`, `WORKFLOW.md`, `TESTING.md` | `OUTPUTS.md`, `../../frontend/README.md`, runbooks under `docs/demo/` or `docs/operational_runbook.md`, `SPEC.md`, `CHANGELOG.md`, `DECISIONS.md` |
| Known issue, unresolved limitation, testing gap, accepted residual risk, technical debt | `KNOWN_ISSUES.md` | Active ExecPlan, `TESTING.md`, `DATA.md`, `SPEC.md`, owning `docs/specs/*`, `CHANGELOG.md` when fixed |
| Architectural, product, methodology, QA, source-of-truth, or governance decision | `DECISIONS.md` | Active ExecPlan Decision Log, `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, contracts, `CHANGELOG.md` when implemented |
| Completed meaningful change | `CHANGELOG.md` | Owning docs from the row above, active ExecPlan Outcomes, `DECISIONS.md` if a decision was made, `KNOWN_ISSUES.md` if an issue was fixed or accepted |

## Examples by document

### README.md

Update `README.md` when user-facing setup, common commands, product flow, runtime taxonomy, output locations, repository map, or current-vs-legacy orientation changes. Do not update it for internal helper refactors that do not affect how a user or operator understands the project.

Examples:

- Update when `run_portfolio_review.py` defaults change.
- Update when a new canonical demo command is introduced.
- Update when the current Core MVP flow changes.
- Update when generated-output default behavior changes from JSON-only to export-producing, or vice versa.

### PRODUCT.md

Update `PRODUCT.md` when product direction, user goals, Core MVP boundaries, advanced/later classification, product language, or the target/current relationship changes. Do not use `PRODUCT.md` to assert implementation status unless verified against `SPEC.md`, detailed specs, outputs, and code.

Examples:

- Update when Monitoring / What Changed is promoted from deferred/light context to a real route.
- Update when a candidate method is promoted into guided Core MVP.
- Update when "candidate is not recommendation" wording changes.

### SPEC.md

Update `SPEC.md` when the current implementation contract, workflow, input/output behavior, binding behavior rules, edge cases, or product status matrix changes. Keep long formulas and module-specific detail in owning `docs/specs/*`.

Examples:

- Update when an artifact becomes implemented or is demoted from current Core MVP.
- Update when a runtime path changes stage order.
- Update when a validation rule changes the accepted input contract.

### OUTPUTS.md

Update `OUTPUTS.md` when output folders, artifact names, artifact formats, output profiles, generated-vs-source boundaries, product-bundle interpretation, report packaging, or generated-output refresh policy changes.

Examples:

- Update when a new JSON artifact is written.
- Update when a generated folder changes purpose.
- Update when PDFs become part of a default workflow.
- Update when root legacy artifacts can or cannot be trusted for portfolio-first UI.

### TESTING.md

Update `TESTING.md` when verification strategy, required checks, focused pytest routing, docs verification, generated-output checks, CLI smoke expectations, or known full-suite caveats change.

Examples:

- Update when a new frontend check becomes mandatory.
- Update when a test file becomes the owning regression for a module.
- Update when a known full-suite failure is fixed or newly accepted.

### DECISIONS.md

Update `DECISIONS.md` when the project chooses one path among meaningful alternatives and that choice affects behavior, methodology, architecture, QA policy, source-of-truth ownership, product boundaries, or output contracts.

Examples:

- Update when choosing not to promote an advanced optimizer into Core MVP.
- Update when introducing a new source-of-truth contract layer.
- Update when changing the canonical demo path.

### CHANGELOG.md

Update `CHANGELOG.md` for meaningful completed changes. Keep entries concise and project-level. Do not log every tiny typo, comment, or mechanical formatting edit.

Examples:

- Update after adding a new durable contract.
- Update after a screen behavior change.
- Update after a bug fix with user/operator-visible impact.
- Update after a docs-only governance change that future agents must follow.

### ../../frontend/README.md

Update `../../frontend/README.md` when frontend routes, API routes, local commands, review-state storage, run-local artifact strategy, vertical demo flow, browser QA assumptions, or frontend scope boundaries change.

Examples:

- Update when adding a new `/api/portfolio/*` route.
- Update when `pmri.activeReview.v2` storage semantics change.
- Update when the frontend journey adds or removes a route.

### DESIGN.md and docs/design/*

Update `docs/design/portfolio_mri_design_system.md` and `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` for Portfolio MRI product UI design changes. Update `DESIGN.md` only when legacy/historical visual routing, project-wide visual governance, or generated HTML/dashboard design guidance changes.

Examples:

- Update design docs when status color semantics change.
- Update design docs when card hierarchy or CTA placement policy changes.
- Do not update design docs for a non-visual backend fix.

### Contract docs under docs/contracts/

Update contracts when a cross-cutting rule changes:

- `PRODUCT_FLOW_CONTRACT.md`: product order, Core MVP boundaries, step roles, next-step logic.
- `ARTIFACT_TO_SCREEN_MAP.md`: artifact routing, stale-data rules, lineage, adapter ownership.
- `SCREEN_CONTRACTS.md`: route responsibilities, CTAs, empty states, screen QA.
- `PRESENTATION_LANGUAGE_RULES.md`: UI/report wording and forbidden terms.
- `DESIGN_SYSTEM_CONTRACT.md`: visual style, badges, color semantics, cards, CTA hierarchy.
- `QA_CONTRACT.md`: required checks and final reporting evidence.
- `DOC_SYNC_CONTRACT.md`: documentation governance and documentation impact routing.

### docs/specs/*

Update the owning detailed spec when a module, artifact, schema, formula, status, command option, or data behavior changes. Top-level docs should point to the detailed spec instead of duplicating long technical details.

Examples:

- Update `docs/specs/current_vs_candidate_spec.md` when `current_vs_candidate.json` semantics change.
- Update `docs/specs/decision_verdict_spec.md` when verdict ids or evidence rules change.
- Update `docs/specs/input_assumptions_spec.md` when Core MVP input fields or defaults change.

### Runbooks

Update runbooks when operator procedures, demo steps, browser QA procedure, stale-artifact recovery, command order, or expected proof outputs change.

Examples:

- Update `docs/demo/frontend_backend_vertical_runbook.md` when the manual UI click path changes.
- Update `docs/operational_runbook.md` when a CLI recovery or candidate factory playbook changes.

### KNOWN_ISSUES.md

Update `KNOWN_ISSUES.md` when an active bug, risk, limitation, testing gap, or technical debt is discovered and not fixed immediately. Remove or mark fixed only after the fix is verified and docs are synced.

## Generated-output boundaries

Generated outputs are evidence and deliverables, not source files, unless the user explicitly targets generated artifacts.

Common generated paths and files include:

- `cache/`
- `output/`
- `results_csv/`
- `Main portfolio/`
- portfolio variant output folders
- `runs/frontend_review_*`
- `portfolio_weights.yml`
- `__pycache__/`
- `.pytest_cache/`
- `pdf files/`
- `pdf_md_sources/`
- generated CSV/TXT/HTML/PNG/PDF/Markdown/CSS sidecars

Rules:

1. Do not edit generated outputs as if they define behavior.
2. Do not refresh generated outputs unless the active task explicitly approves generated-output changes.
3. If generated outputs are intentionally refreshed, classify them separately from source/docs/code in `git status --short`.
4. Default `site_api` review writes JSON/cache only; PDFs and presentation sidecars may be stale unless explicitly regenerated.
5. Do not infer product truth from stale generated files. Prefer source specs, active contracts, and same-run artifact lineage.
6. Do not commit generated outputs unless the user explicitly asks for generated artifacts to be included.

See `OUTPUTS.md` for the authoritative generated-output policy and artifact map.

## Interaction with ExecPlans

For large, risky, multi-session, architectural, or contract-changing work, follow `PLANS.md` and the active ExecPlan under `docs/exec_plans/`.

ExecPlans are living documents. During planned work, update:

- `Progress` at every stopping point.
- `Surprises & Discoveries` when unexpected behavior, dirty-tree state, test caveats, or implementation constraints are discovered.
- `Decision Log` when a design, source-of-truth, product, QA, or implementation choice is made inside the plan.
- `Outcomes & Retrospective` after each major session or milestone.
- `Immediate Next Action` so the next agent knows exactly where to resume and where not to continue.

If a session is scoped to one ExecPlan session, do not start later sessions unless the user explicitly asks. Update the plan to point to the next session and stop.

## Final-response requirement

Every final response after meaningful work must include:

1. changed files;
2. documentation updated or documentation waived with reason;
3. checks run and results;
4. checks not run and why;
5. unverified areas, blockers, or assumptions;
6. whether runtime/frontend/backend code changed;
7. whether generated outputs changed;
8. whether a commit, push, branch switch, or PR was created.

For visual QA work, also include:

- URL/port;
- route;
- active `reviewId` when relevant;
- sample/demo/real mode;
- browser state reset or recovery;
- screenshots captured;
- unverified route or state coverage.

For docs-only sessions, explicitly state that runtime tests were not run because no runtime code changed, unless executable examples or command behavior changed and required verification.

## Acceptance checklist for future sessions

- [ ] The changed risk was classified.
- [ ] The owning source-of-truth docs were checked.
- [ ] The dynamic doc sync matrix was applied.
- [ ] Owning docs were updated or the final response includes a specific waiver reason.
- [ ] Generated outputs were not treated as source.
- [ ] ExecPlan living sections were updated when the session is part of an active plan.
- [ ] `git diff --check` and `git status --short` were run for meaningful file changes.
- [ ] Final response includes changed files, docs updated/waived, checks, unverified areas, runtime/frontend/backend/generated-output boundaries, and commit status.

## Validation for this contract

This session is documentation-only. Minimum checks after editing this file:

    git diff --check
    git status --short

This session does not require frontend builds, frontend tests, backend pytest, visual QA, runtime commands, or generated-output refresh because it creates a documentation-governance contract and does not change implementation code.
