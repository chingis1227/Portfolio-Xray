# Product-Code-Design Synchronization Pass + Dynamic Documentation Governance

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document is maintained under `PLANS.md` from the repository root. It is intentionally self-contained so a future agent can continue the synchronization effort without prior chat context.

## Purpose / Big Picture

Portfolio MRI / Portfolio X-Ray already has backend product artifacts, frontend routes, tests, documentation, and design direction. The product risk is not lack of features; the risk is drift: documentation may define one product, backend artifacts may calculate another, frontend screens may present a third, and UI copy may expose internal implementation language. This plan gives the project an operating system for keeping product truth, code, adapters, design, tests, and documentation synchronized.

After this plan is executed, future product/code/design changes cannot be considered complete until the related documentation impact has been checked and either updated or explicitly waived with a reason. The immediate observable result of Session 0 is this plan file. Later sessions create durable contract documents under `docs/contracts/` and then apply those contracts to the frontend and docs.

This pass is docs-first and stabilization-first. Do not change backend calculations, JSON schemas, runtime behavior, UI implementation, generated artifacts, git branches, commits, pushes, or merges unless a later session explicitly asks for that scoped work.

## Progress

- [x] (2026-06-10) Session 0 started from the existing repository state and recorded the current dirty tree and branch before creating this plan.
- [x] (2026-06-10) Confirmed that `docs/exec_plans/2026-06-10_product_code_design_synchronization_plan.md` did not exist before this session.
- [x] (2026-06-10) Confirmed that `docs/contracts/` did not exist before this session.
- [x] (2026-06-10) Created this docs-only synchronization ExecPlan with dynamic documentation governance.
- [x] (2026-06-10) Session 1 created `docs/contracts/PRODUCT_FLOW_CONTRACT.md` as the cross-cutting Core MVP product-flow contract.
- [x] (2026-06-10) Session 2 created `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` as the artifact-to-screen and lineage contract.
- [x] (2026-06-10) Session 3 created `docs/contracts/SCREEN_CONTRACTS.md` as the current MVP screen-level contract.
- [x] (2026-06-10) Session 4 created `docs/contracts/PRESENTATION_LANGUAGE_RULES.md` as the presentation-language and forbidden-term contract.
- [x] (2026-06-10 14:40+02:00) Session 5 created `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` as the enforceable premium institutional SaaS design contract.
- [x] (2026-06-10 14:48+02:00) Session 6 created `docs/contracts/QA_CONTRACT.md` as the canonical QA and verification contract.
- [x] (2026-06-10 14:55+02:00) Session 7 created `docs/contracts/DOC_SYNC_CONTRACT.md` as the canonical documentation-governance contract and linked it from the existing contract docs.
- [x] (2026-06-10 15:03+02:00) Session 8 created `docs/audits/2026-06-10_adapter_architecture_plan.md` as the adapter responsibility audit and future screen-adapter split plan.
- [x] (2026-06-10 15:24+02:00) Session 9 applied contracts to Step 04 / Hypothesis Builder only.
- [x] (2026-06-10 15:52+02:00) Session 10 applied contracts to Step 05 / Current vs Candidate Comparison.
- [x] (2026-06-10 16:35+02:00) Session 11 applied contracts to Step 06 / Decision Verdict.
- [x] (2026-06-10 17:05+02:00) Session 12 aligned Step 07 / Report and grounded explanation presentation.
- [x] (2026-06-10 18:10+02:00) Session 13 ran full journey QA and fixed one small Report label leak.
- [x] (2026-06-10 22:51+02:00) Session 14 reconciled documentation after implementation sessions.
- [x] (2026-06-10 23:20+02:00) Session 15 created `docs/audits/2026-06-10_product_code_design_synchronization_closure_report.md` as the final alignment / closure report.

## Surprises & Discoveries

- Observation: The working tree was already dirty before this synchronization plan was created.
  Evidence: `git status --short` showed modified files including `AGENTS.md`, `CHANGELOG.md`, `docs/demo/frontend_backend_vertical_runbook.md`, multiple `frontend/app/*` pages, multiple `frontend/components/*` files, and several `frontend/lib/*` files. It also showed untracked files including `docs/audits/product_code_docs_design_alignment_audit.md`, `docs/exec_plans/2026-06-10_post_stress_frontend_flow_alignment_plan.md`, `docs/specs/frontend_screen_contracts.md`, `frontend/components/evidence/MainStressDiagnosisPanel.tsx`, and `frontend/test-results/`.

- Observation: The current branch is `ui-premium-monochrome-redesign`.
  Evidence: `git branch --show-current` returned `ui-premium-monochrome-redesign`.

- Observation: A related post-stress frontend alignment plan and frontend screen contract already exist as untracked or modified working-tree material.
  Evidence: `docs/exec_plans/2026-06-10_post_stress_frontend_flow_alignment_plan.md` and `docs/specs/frontend_screen_contracts.md` appeared in `git status --short` as untracked. Future sessions should inspect and reuse them rather than creating conflicting parallel guidance.

- Observation: `docs/contracts/` is not present yet.
  Evidence: `Test-Path docs\contracts` returned false during Session 0.

- Observation: `frontend/lib/reviewState.tsx` is the major frontend state and presentation mapping concentration point.
  Evidence: repository inspection showed it defines active review state, compact review summaries, candidate generation summaries, comparison summaries, verdict summaries, localStorage cleanup, journey flags, artifact compaction, and many display fallback helpers.

- Observation: Session 1 had to create the `docs/contracts/` directory before adding the first contract.
  Evidence: `git status --short` before Session 1 showed no `docs/contracts/` path, and Session 1 added `docs/contracts/PRODUCT_FLOW_CONTRACT.md`.

- Observation: A related untracked frontend screen contract already exists under `docs/specs/frontend_screen_contracts.md`.
  Evidence: Session 1 inspected the file and used it only as alignment context; the new Product Flow Contract remains higher-level and does not replace the planned Session 3 `docs/contracts/SCREEN_CONTRACTS.md`.

- Observation: Session 2 confirmed that frontend artifact presentation is concentrated in `frontend/lib/reviewState.tsx`, with additional label normalization in `frontend/lib/displayLabels.ts`, route gating in `frontend/lib/journey.ts`, stress-specific mapping in `frontend/components/evidence/stressLabModel.ts`, and run-local lineage enforcement in `frontend/app/api/portfolio/*` routes.
  Evidence: targeted `rg` for product artifact names in `frontend/` showed `reviewState.tsx` mapping `candidate_generation`, `current_vs_candidate`, `decision_verdict`, `portfolio_xray`, `stress_report`, `problem_classification`, `candidate_launchpad`, and `portfolio_alternatives_builder`; API routes write stage result envelopes and recovery sanitizes downstream artifacts.

- Observation: Session 2 confirmed that Monitoring / What Changed has backend product artifacts but no current frontend route.
  Evidence: `docs/product_flow_operator_guide.md`, `docs/runtime_artifact_contract.md`, `src/light_monitoring_summary.py`, and the frontend route list show `what_changed_summary.json` / `monitoring_diff.json` as optional or deferred evidence, while the visible MVP route chain ends at `/report`.

- Observation: Session 3 confirmed the current frontend route list is still the seven-route MVP chain and has no separate Candidate or Monitoring route.
  Evidence: `Get-ChildItem frontend/app -Directory` returned `api`, `comparison`, `diagnosis`, `evidence`, `hypothesis`, `portfolio-input`, `report`, and `verdict`; no `candidate`, `monitoring`, or `what-changed` route was present.

- Observation: A prior untracked draft already covers frontend screen behavior under `docs/specs/frontend_screen_contracts.md`.
  Evidence: Session 3 inspected that draft and reused it only as alignment context; the planned contract location for this synchronization plan is `docs/contracts/SCREEN_CONTRACTS.md`.

- Observation: Session 4 targeted language scans found current frontend examples that justify a dedicated language contract, but this docs-only session intentionally did not change runtime code.
  Evidence: `rg` found `Review ID` / `frontend_review_...` in `frontend/components/portfolio/PortfolioInputTable.tsx`, `AI Commentary context`, `No PDF generation`, and `implementation order` in `frontend/app/report/page.tsx`, and existing replacement logic in `frontend/lib/displayLabels.ts`.

- Observation: Session 5 confirmed that the design source describes the same premium dark decision-room direction, while some source labels are broader than the current seven-route MVP.
  Evidence: `docs/design/portfolio_mri_design_system.md` uses the journey label `Candidate` and an Evidence Center framing, while existing contracts define `/hypothesis` as the merged Launchpad / Builder / Candidate Generation route and `/evidence` as Stress Test Lab; `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` adapts the visual rules to the current MVP route reality without changing frontend code.

- Observation: Session 6 confirmed that the standard frontend QA commands already exist in `frontend/package.json` and match the existing frontend README, vertical runbook, and active ExecPlan expectations.
  Evidence: `frontend/package.json` declares `typecheck`, `build`, `test:api`, and `test:smoke` scripts; `../../frontend/README.md`, `docs/demo/frontend_backend_vertical_runbook.md`, and this ExecPlan reference the same Windows `npm.cmd run` command family and warn against concurrent `.next` writers.

- Observation: Session 8 confirmed that `frontend/lib/reviewState.tsx` currently combines active review lifecycle, compact storage, localStorage cleanup, journey flags, same-candidate lineage gates, and screen presentation mapping for X-Ray/Diagnosis, evidence summary, Launchpad/Builder, comparison, and verdict.
  Evidence: targeted `rg` showed `reviewState.tsx` exports state and summary types, `ReviewStateProvider`, `useReviewState`, `buildCompactReviewSummary`, `buildDiagnosisFromReview`, `recordBuilderSetup`, `recordCandidateGeneration`, `recordComparisonResult`, and `recordVerdictResult`, plus helpers for X-Ray, comparison, verdict, and evidence fallback wording.

- Observation: Session 8 found one existing partial split: Stress Test Lab mapping already lives mainly in `frontend/components/evidence/stressLabModel.ts`, while Hypothesis, Comparison, Verdict, and Report still keep significant screen-specific mapping inside route pages and `reviewState.tsx`.
  Evidence: targeted `rg` showed `buildStressLabModelFromOutputs` in `stressLabModel.ts`; `/hypothesis/page.tsx` contains Launchpad/Builder/card/candidate helpers; `/comparison/page.tsx`, `/verdict/page.tsx`, and `/report/page.tsx` repeat active `reviewId` / `selectedCardId` / `candidateId` matching and state derivation.

- Observation: Session 9 Browser visual QA on `/hypothesis...sample=1` confirmed the contracted Step 04 sequence and generated-state text, but the in-app browser runtime did not allow `networkidle`, read-only storage clearing, or full-page screenshot capture in this run.
  Evidence: the fresh local server on port 3029 returned `/hypothesis...sample=1` and `/hypothesis...sample=1&generated=1` with no dev-server errors; viewport screenshots were saved under `runs/session9_hypothesis_sample_3029_viewport.png` and `runs/session9_hypothesis_sample_generated_3029_viewport.png`; DOM checks found Current Diagnosis, Recommended Test, Available Test Paths, Selected Test Setup, Generate Test Candidate, Test Candidate Generated, Continue to Comparison, the secondary monitoring path, and no visible backend/artifact terms.

- Observation: Session 10 found that the shared `JourneyGate` hid the Comparison screen's own no-candidate empty state, so `/comparison...sample=1` showed a generic locked workflow message instead of the contracted Step 05 blocked state.
  Evidence: Browser QA on port 3034 first showed `/comparison...sample=1` behind the workflow gate; after removing the gate from the Comparison route, the same URL rendered `Generate a test candidate first` with no visible forbidden Comparison terms.

- Observation: Session 10 could not visually inspect synthetic unavailable/valid comparison states through in-app Browser state injection.
  Evidence: Browser security policy rejected the attempted localhost `javascript:` URL used to set test `localStorage`, and the session did not attempt a workaround via alternate browser surfaces. The visually verified state is candidate-not-generated on `/comparison...sample=1`; valid/unavailable comparison visual states remain unverified in Browser because this route has no dedicated sample-state query contract.

- Observation: Session 11 could not complete visual QA for `/verdict...sample=1` before the user's hard stop, so visual QA is explicitly unverified for this session.
  Evidence: frontend validation and scans completed, a fresh dev server attempt on port 3041 was stopped, and no Browser/Playwright screenshot or DOM evidence was captured. `git diff --check` still passed after the visual QA stop.

- Observation: Session 12 initially hit a stale/corrupt `.next` build state, then passed after safely removing only `frontend/.next` and rerunning validation sequentially.
  Evidence: the first `npm.cmd run build` compiled but failed during prerender with `clientModules` / manifest JSON errors; after verified deletion of `frontend/.next`, `npm.cmd run build` completed successfully.

- Observation: Session 12 could not capture a real Browser/Playwright visual screenshot for `/report...sample=1` in this environment.
  Evidence: `tool_search` did not expose a Browser navigation/screenshot tool, `node_repl` could not import `playwright`, `frontend/node_modules` had no Playwright/Puppeteer/jsdom package, and no Chrome/Edge executable was found. A fresh dev server on port 3052 returned HTTP 200 for `/report...sample=1`, but hydrated DOM visual inspection and screenshot remain unverified.

- Observation: Session 13 completed full journey visual QA through a fresh production localhost target using Chrome DevTools Protocol as the Browser/Playwright fallback.
  Evidence: after `npm.cmd run build`, a fresh `next start` target was opened at `http://localhost:3067`; a fresh Chrome user-data directory was used, `localStorage` was cleared, and a compact active-review QA state was seeded with `reviewId=frontend_review_session13_visual`, `selectedCardId=sample_reference_comparison`, and `candidateId=equal_weight_reference_candidate`. Screenshots were captured under `runs/session13_visual_qa/01_portfolio_input.png` through `runs/session13_visual_qa/07_report.png`, with the route summary saved to `runs/session13_visual_qa/session13_visual_qa_summary.json`. The checked route sequence was `/portfolio-input`, `/diagnosis`, `/evidence...sample=1`, `/hypothesis`, `/comparison`, `/verdict`, and `/report`.

- Observation: Session 13 found and fixed a small Report primary-copy label leak.
  Evidence: visual QA showed `/report` displayed the raw candidate id `equal_weight_reference_candidate` in the primary preview text. The fix in `frontend/app/report/page.tsx` now uses `displayTitleLabel(...)` so the visible copy says `Equal Weight Reference Candidate` while preserving the underlying candidate id for lineage checks.

- Observation: Session 13 confirmed a recurring `.next` lifecycle limitation in this repository's smoke script.
  Evidence: `npm.cmd run test:smoke` passed, but afterward `.next/BUILD_ID` was missing, so `next start` could not run until `npm.cmd run build` was rerun. This matches the existing Windows `.next` race/stale-state warning; Session 13 kept build, smoke, and visual QA sequential and did not run `.next` writers concurrently.

- Observation: Session 14 found the remaining stale documentation was narrow rather than systemic. The contracts and current implementation notes already separated Core MVP, advanced/backend/legacy, and deferred Monitoring correctly; the main stale areas were frontend/design wording that still called the surface a prototype, skipped Evidence/Report in one progress example, treated Candidate as a separate visible step, or used backend/operator terms in the vertical demo runbook.
  Evidence: targeted `rg` scans over `README.md`, `PRODUCT.md`, `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, `DESIGN.md`, `../../frontend/README.md`, `docs/contracts/`, `docs/demo/frontend_backend_vertical_runbook.md`, and `docs/design/portfolio_mri_design_system.md`; scoped docs updates in `../../frontend/README.md`, `docs/demo/frontend_backend_vertical_runbook.md`, `docs/design/portfolio_mri_design_system.md`, `PRODUCT.md`, and `CHANGELOG.md`.

- Observation: Session 15 found no separate Markdown full-journey QA report from Session 13; the available proof is the ExecPlan record plus machine-readable evidence and screenshots under `runs/session13_visual_qa/`.
  Evidence: `the missing full-journey QA Markdown report` was absent, while `runs/session13_visual_qa/session13_visual_qa_summary.json` and screenshots `01_portfolio_input.png` through `07_report.png` were present. The closure report references those files directly rather than inventing a missing audit document.

## Decision Log

- Decision: Session 0 creates only this synchronization ExecPlan and stops.
  Rationale: The user explicitly requested a serious audit/planning/contract creation pass, then clarified: after Session 00 succeeds, report success and stop. Creating contract files or applying frontend changes now would start later sessions prematurely.
  Date/Author: 2026-06-10 / Codex.

- Decision: Dynamic documentation governance is part of the synchronization plan, but the permanent `DOC_SYNC_CONTRACT.md` is scheduled for Session 7 rather than created during Session 0.
  Rationale: Session 0 is the audit/freeze and plan creation step. The user requested future project-wide adaptability, so this plan makes the governance non-optional and gives it its own contract session.
  Date/Author: 2026-06-10 / Codex.

- Decision: The future contract docs belong under `docs/contracts/`.
  Rationale: The repository has many detailed specs under `docs/specs/`, but this synchronization effort needs cross-cutting product-code-design contracts that bind screens, artifacts, language, design, QA, and doc-sync behavior. A dedicated folder avoids mixing these operating contracts with module-specific specs.
  Date/Author: 2026-06-10 / Codex.

- Decision: Existing dirty working-tree files must be treated as pre-existing user/worktree state.
  Rationale: The session found many modified and untracked files before this plan was written. Future agents must not revert, stage, or overwrite those files unless the user explicitly scopes that work.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 1 creates a cross-cutting product-flow contract only; it does not modify frontend code, backend code, generated outputs, runtime commands, or existing schemas.
  Rationale: The Session 1 scope is to define canonical steps, user questions, artifacts, allowed behavior, forbidden behavior, next-step logic, and boundaries. Implementation sessions are intentionally deferred to Sessions 8-15.
  Date/Author: 2026-06-10 / Codex.

- Decision: `docs/contracts/PRODUCT_FLOW_CONTRACT.md` is the product-order and boundary contract, while field-level and formula-level authority stays with the existing owning specs.
  Rationale: This avoids duplicating formulas or schema details and gives future screen, adapter, and documentation work a single product-flow starting point without overriding `SPEC.md`, `OUTPUTS.md`, or detailed `docs/specs/*` contracts.
  Date/Author: 2026-06-10 / Codex.

- Decision: `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` is the artifact routing, adapter, stale-data, and lineage contract; it maps artifacts to screens without changing schemas, API routes, or frontend implementation.
  Rationale: Session 2 acceptance is documentation-only. The durable contract must make every product artifact's user-facing meaning explicit while preserving schema authority in existing specs and deferring implementation changes to Sessions 8-15.
  Date/Author: 2026-06-10 / Codex.

- Decision: Monitoring / What Changed is documented as a deferred UI layer in the artifact map.
  Rationale: `what_changed_summary.json` and `monitoring_diff.json` can exist as backend evidence, but there is no current MVP route or component. Treating this as deferred prevents future agents from calling the absence of a screen a bug or inventing a monitoring product surface prematurely.
  Date/Author: 2026-06-10 / Codex.

- Decision: `docs/contracts/SCREEN_CONTRACTS.md` is the canonical screen-level contract for this synchronization pass, while the existing `docs/specs/frontend_screen_contracts.md` draft remains context rather than the active destination for Session 3.
  Rationale: Session 3 explicitly requires a contract under `docs/contracts/`. Creating that file avoids silently moving or overwriting a pre-existing untracked spec draft, and it keeps cross-cutting synchronization contracts together with Product Flow and Artifact-to-Screen Map.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 4 creates only `docs/contracts/PRESENTATION_LANGUAGE_RULES.md` and does not edit `frontend/lib/displayLabels.ts` or other frontend runtime files.
  Rationale: The user explicitly scoped Session 4 as docs-only unless implementation was requested. The contract records display-label responsibilities and future scan commands, while later implementation sessions can apply the contract to UI code.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 5 creates only `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` and does not edit CSS, frontend components, route code, runtime code, or generated artifacts.
  Rationale: The Session 5 scope is to make the premium institutional SaaS design rules enforceable as a contract. Implementation and visual QA application belong to later implementation sessions, not this docs-only contract session.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 6 creates only `docs/contracts/QA_CONTRACT.md` and updates this ExecPlan; it does not run frontend builds/tests, backend pytest, visual QA, or modify test/runtime/frontend/backend code.
  Rationale: Session 6 is docs-only and its acceptance is to define future QA checks, verify command names against existing sources, and run git hygiene checks. Running implementation tests would be unnecessary because no executable behavior changed.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 7 creates only `docs/contracts/DOC_SYNC_CONTRACT.md`, minimally links it from the existing contract docs, and updates this ExecPlan; it does not modify runtime, frontend, backend, test code, generated outputs, branches, commits, or pushes.
  Rationale: Session 7 is docs-only and its acceptance is to make dynamic documentation governance permanent. Runtime and implementation work begins no earlier than Session 8 and must not be started in this session.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 8 records adapter architecture as `docs/audits/2026-06-10_adapter_architecture_plan.md` and does not refactor frontend implementation.
  Rationale: The Session 8 scope is audit/architecture planning only. Changing route pages, components, `reviewState.tsx`, `displayLabels.ts`, `types.ts`, or `journey.ts` would start later implementation sessions without user approval.
  Date/Author: 2026-06-10 / Codex.

- Decision: Future adapter implementation should keep active review lifecycle, compact storage, journey flags, and same-run lineage centralized, while splitting screen-specific mapping into X-Ray/Diagnosis, Stress, Hypothesis, Comparison, Verdict, and Report adapters or screen models.
  Rationale: This keeps stale-data and route-unlock safety in one place but makes presentation mapping testable and aligned to the screen contracts.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 9 applies the contracts inside the Hypothesis route/component presentation layer and display-label boundary only, without expanding `reviewState.tsx` or changing backend candidate generation.
  Rationale: Session 8 says active review lifecycle and same-run lineage remain centralized, while Session 9 should keep screen-specific shaping in or near Hypothesis. The changes therefore filter and translate visible Step 04 test paths in `frontend/app/hypothesis/page.tsx` and `frontend/components/hypothesis/HypothesisCard.tsx` while leaving backend calculations, schemas, candidate generation logic, comparison, and verdict untouched.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 10 removes the shared `JourneyGate` wrapper from `/comparison` so the route can render its own contracted candidate-missing and comparison-unavailable states.
  Rationale: The screen contract requires candidate-not-generated, comparison-unavailable, and valid-comparison states to be distinct. Keeping the shared gate at the route boundary prevented the no-candidate state from rendering. The route still keeps same-run comparison lineage locally and only shows the Verdict CTA after a usable same-candidate comparison, so this does not start Session 11 or change verdict logic.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 11 removes the shared `JourneyGate` wrapper from `/verdict` and lets the Verdict route render its own contracted no-comparison, stale/mismatched, failed/infeasible, evidence-insufficient, and active-verdict states.
  Rationale: The screen contract requires Verdict-specific readiness and lineage states to be visibly distinct. A generic locked workflow message would hide the difference between no valid comparison, stale downstream evidence, evidence-insufficient outcome, and a valid evidence-supported verdict. The route still requires same selected card and same generated candidate before showing an active verdict or report CTA.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 12 keeps Report alignment at the presentation/readiness boundary and does not alter LLM generation, backend grounding schema, PDF generation, artifacts, or JSON schemas.
  Rationale: The acceptance criteria require a client-ready grounded explanation preview and same-run evidence readiness, while explicitly excluding backend grounding, PDF, calculation, and schema changes. Report can meet the contract by sanitizing visible copy, gating on active comparison/verdict lineage, and showing available/unavailable evidence clearly.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 15 closes the product-code-design synchronization pass as `ACCEPTED_FOR_CURRENT_SCOPE` with bounded follow-ups rather than extending the plan into adapter refactors or new test implementation.
  Rationale: Sessions 0-14 created the durable contract layer, applied the screen contracts to Steps 04-07, completed full journey QA, and reconciled documentation. Remaining work is useful hardening (adapter extraction and edge-state regression coverage), but it is outside the final-report scope and should be handled as a new milestone.
  Date/Author: 2026-06-10 / Codex.

## Outcomes & Retrospective

Session 0 outcome: This plan now exists as the controlling project-level synchronization plan. It captures the product-code-design problem, the dynamic documentation governance requirement, the contract documents to create, the session sequence, the mismatch register, and the QA/branch strategy. No runtime behavior, backend calculation, frontend UI implementation, generated output, commit, push, or merge was performed.

Remaining after Session 0: Sessions 1-7 must create the permanent contract layer, including `DOC_SYNC_CONTRACT.md`. Sessions 8-15 then plan and apply adapter, screen, report, QA, and documentation reconciliation work in small reviewable increments.

Session 1 outcome: `docs/contracts/PRODUCT_FLOW_CONTRACT.md` now exists. It states the canonical Core MVP flow, current MVP route reality, global product boundaries, the per-step user question and artifact/evidence chain, allowed and forbidden behavior, next-step logic, runtime/artifact boundaries, advanced-vs-Core exclusions, language guardrails, and the documentation impact rule. No frontend implementation, backend implementation, generated output, schema, runtime command, commit, push, or merge was changed.

Remaining after Session 1: Sessions 2-7 must create the rest of the contract layer: Artifact-to-Screen Map, Screen Contracts, Presentation Language Rules, Design System Contract, QA Contract, and DOC_SYNC_CONTRACT. Later implementation sessions should treat the Product Flow Contract as the first product-boundary check before changing screens or adapters.

Session 2 outcome: `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` now exists. It maps Core MVP artifacts and supporting technical artifacts to frontend routes, adapters, user-facing meanings, current risks, required contracts, runtime locations, stale-data rules, lineage rules, runtime-mode lifecycle states, and future acceptance checks. It explicitly keeps Monitoring / What Changed as a deferred UI layer and keeps advanced/legacy artifacts out of Core MVP navigation. No frontend implementation, backend implementation, generated output, schema, API route, runtime command, commit, push, or merge was changed.

Remaining after Session 2: Sessions 3-7 must create the rest of the contract layer: Screen Contracts, Presentation Language Rules, Design System Contract, QA Contract, and DOC_SYNC_CONTRACT. Later implementation sessions should use the Product Flow Contract and Artifact-to-Screen Map before changing adapters or screens.

Session 3 outcome: `docs/contracts/SCREEN_CONTRACTS.md` now exists. It defines the current MVP screen responsibilities for Portfolio Input, Portfolio X-Ray / Diagnosis, Stress Test Lab, Hypothesis Builder, Current vs Candidate Comparison, Decision Verdict, Report / AI Commentary Grounding, and deferred Monitoring / What Changed. Each screen now has a product role, user question, artifacts/evidence, adapter owner, must-show and must-not-show rules, primary CTA, next-step policy, forbidden language, current mismatch, empty/blocked state, and QA checks. It preserves `/hypothesis` as the merged Launchpad / Builder / Candidate Generation route and keeps Monitoring / What Changed deferred. No frontend implementation, backend implementation, generated output, schema, API route, runtime command, commit, push, or merge was changed.

Remaining after Session 3: Sessions 4-7 must create Presentation Language Rules, Design System Contract, QA Contract, and DOC_SYNC_CONTRACT. Later implementation sessions should use Product Flow, Artifact-to-Screen Map, and Screen Contracts together before changing adapters or screen components.

Session 4 outcome: `docs/contracts/PRESENTATION_LANGUAGE_RULES.md` now exists. It defines forbidden backend/internal/user-facing terms, approved replacements, product safety boundaries, display-label layer responsibilities, safe language for empty/blocked/generated/unavailable/partial/sample states, screen-specific language routing, and future `rg` scan commands. It explicitly preserves candidate-as-test, verdict-as-non-binding decision support, AI Commentary-as-grounded explanation, and the rule that backend/artifact/JSON vocabulary must not appear in primary UI. No frontend implementation, backend implementation, generated output, schema, runtime command, commit, push, or merge was changed.

Remaining after Session 4: Sessions 5-7 must create the Design System Contract, QA Contract, and DOC_SYNC_CONTRACT. Later implementation sessions should use Product Flow, Artifact-to-Screen Map, Screen Contracts, and Presentation Language Rules together before changing adapters, display labels, or screen components.

Session 5 outcome: `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` now exists. It turns the premium institutional SaaS design direction into enforceable rules for dark graphite/navy visual style, color semantics, badge taxonomy and limits, card hierarchy, typography, CTA placement, warning/boundary states, generated/ready states, unavailable/blocked/partial/sample/demo states, route-specific visual rules, forbidden visual directions, and future visual QA. It references Product Flow, Artifact-to-Screen Map, Screen Contracts, Presentation Language Rules, and the canonical design source. No frontend implementation, CSS, component, runtime, generated output, schema, commit, push, or merge was changed.

Remaining after Session 5: Sessions 6-7 must create the QA Contract and DOC_SYNC_CONTRACT. Later implementation sessions should use Product Flow, Artifact-to-Screen Map, Screen Contracts, Presentation Language Rules, and Design System Contract together before changing adapters, display labels, screen components, or visual design tokens.

Session 6 outcome: `docs/contracts/QA_CONTRACT.md` now exists. It defines standard frontend checks from `frontend/package.json` (`npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:api`, and `npm.cmd run test:smoke`), backend targeted pytest policy, visual QA reporting requirements, forbidden-term scan policy, git status and `git diff --check` gates, the Windows `.next` race warning, docs-only vs implementation verification matrices, final-response reporting requirements, change-to-check mapping, and source-of-truth links. No test code, runtime code, frontend implementation, backend implementation, generated output, commit, push, or branch change was made.

Remaining after Session 6: Session 7 must create `docs/contracts/DOC_SYNC_CONTRACT.md`. Do not start Session 7 unless the user explicitly asks for it. Later implementation sessions should use the QA Contract together with the product, artifact, screen, language, and design contracts before changing adapters, display labels, screen components, runtime behavior, or visual design.

Session 7 outcome: `docs/contracts/DOC_SYNC_CONTRACT.md` now exists. It makes documentation impact checks permanent, defines source-of-truth precedence, adds a dynamic doc sync matrix for product flow, artifacts/outputs, screens/routes/UI, language/copy, design, QA, backend logic, runtime commands, known issues, decisions, and changelog updates, records final-response reporting requirements, explains generated-output boundaries from `OUTPUTS.md`, and defines how future sessions must update active ExecPlans. Existing contract docs now link to the doc-sync contract. No runtime code, frontend implementation, backend implementation, test code, generated output, commit, push, or branch change was made.

Remaining after Session 7: Session 8 must produce the adapter architecture plan for `frontend/lib/reviewState.tsx`, `frontend/lib/displayLabels.ts`, `frontend/lib/types.ts`, `frontend/lib/journey.ts`, and screen components. Do not start Session 8 unless the user explicitly asks for it. Later implementation sessions should use all seven contracts together before changing adapters, display labels, screen components, runtime behavior, or visual design.


Session 8 outcome: `docs/audits/2026-06-10_adapter_architecture_plan.md` now exists and is registered in `docs/audits/README.md`. It documents what `reviewState.tsx` currently does, why it is a monolith risk, what must remain centralized, what should move into future screen-specific adapters/models, boundaries for X-Ray/Diagnosis, Stress, Hypothesis, Comparison, Verdict, and Report, the roles of `displayLabels.ts`, `types.ts`, and `journey.ts`, stale/lineage/localStorage boundaries, the forbidden backend-language boundary, an incremental future refactor sequence, and acceptance criteria for later implementation sessions. No frontend implementation, backend implementation, runtime behavior, schema, test code, generated output, commit, push, or branch change was made.

Remaining after Session 8: Session 9 is Step 04 Contract Application for Hypothesis Builder only. Do not start Session 9 unless the user explicitly asks for it. Later implementation sessions should use the Session 8 adapter plan together with all seven contracts before changing adapters, display labels, screen components, runtime behavior, or visual design.

Session 9 outcome: Step 04 / Hypothesis Builder now presents the contracted product sequence: Current Diagnosis -> Recommended Test -> Available Test Paths -> Selected Test Setup -> Generate Test Candidate -> Test Candidate Generated -> Continue to Comparison. The implementation keeps monitoring/data-quality paths secondary, filters visible candidate cards to contextual MVP methods, hides disabled or unsupported backend method options from the main UI, labels methods as test approaches, keeps candidate output framed as a diagnostic test rather than a recommendation, and preserves the explicit comparison gate after a usable generated candidate. The scoped implementation touched `frontend/app/hypothesis/page.tsx`, `frontend/components/hypothesis/HypothesisCard.tsx`, `CHANGELOG.md`, and this ExecPlan; it did not change backend calculations, candidate generation logic, JSON schemas, comparison/verdict logic, runtime output generation, branches, commits, pushes, or merges. Verification passed with `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:api`, `npm.cmd run test:smoke`, forbidden-term scans, Browser visual QA for `/hypothesis...sample=1` and `/hypothesis...sample=1&generated=1`, `git diff --check`, and `git status --short`.

Remaining after Session 9: Session 10 is Step 05 Contract Application for Current vs Candidate Comparison. Do not start Session 10 unless the user explicitly asks for it. The immediate next implementation should use the same contract stack and keep changes scoped to Comparison.

Session 10 outcome: Step 05 / Current vs Candidate Comparison now presents contracted trade-off evidence states. The route distinguishes no generated test candidate, generated-but-not-comparable candidate, comparison metrics unavailable, ready-to-run comparison, and valid same-candidate comparison. It filters out unavailable placeholder metric rows before rendering the metrics table, keeps the Comparison page free of final-decision, candidate-better, advice, and backend/internal primary copy, and preserves same-run lineage by requiring the active generated candidate and selected card to match before displaying a usable comparison or enabling the Verdict handoff. The scoped implementation touched `frontend/app/comparison/page.tsx`, `frontend/components/comparison/CandidateComparisonPanel.tsx`, `frontend/components/comparison/TradeoffSummary.tsx`, narrowly adjusted Comparison presentation helpers in `frontend/lib/reviewState.tsx`, updated `CHANGELOG.md`, and updated this ExecPlan. It did not change backend comparison calculations, backend artifacts, candidate generation logic, JSON schemas, verdict logic, runtime output generation, branches, commits, pushes, or merges. Verification passed with `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:api`, `npm.cmd run test:smoke`, targeted forbidden-term scans, Browser visual QA for `/comparison...sample=1` candidate-not-generated state, `git diff --check`, and `git status --short`.

Remaining after Session 10: Session 11 is Step 06 Contract Application for Decision Verdict. Do not start Session 11 unless the user explicitly asks for it. The next implementation should use the same contract stack and keep changes scoped to Verdict.

Session 11 outcome: Step 06 / Decision Verdict now presents contracted non-binding decision-support states. The route distinguishes no valid same-run comparison, stale/mismatched comparison evidence, stale/mismatched verdict evidence, failed/infeasible candidate evidence, evidence-insufficient outcome, ready-to-generate verdict, and active evidence-supported verdict. It maps selected-candidate style backend statuses to bounded rebalance review language rather than execution language, removes best-portfolio/trade-order framing from Verdict copy, keeps no-trade/no-material-rebalance/evidence-insufficient as professional outcomes, and preserves same-run lineage by requiring the active selected card and generated candidate before displaying a usable verdict or report handoff. The scoped implementation touched `frontend/app/verdict/page.tsx`, `frontend/components/verdict/VerdictPanel.tsx`, narrowly adjusted Verdict presentation helpers in `frontend/lib/reviewState.tsx`, updated `frontend/lib/displayLabels.ts` to use safe rebalance-review wording, updated `CHANGELOG.md`, and updated this ExecPlan. It did not change backend verdict calculations, backend artifacts, comparison calculations, candidate generation logic, JSON schemas, runtime output generation, branches, commits, pushes, or merges. Verification passed with `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:api`, `npm.cmd run test:smoke`, targeted forbidden-term scans, `git diff --check`, and `git status --short`. Visual QA for `/verdict...sample=1` remains unverified because the user issued a hard stop after the fresh localhost attempt; no screenshot was captured.

Remaining after Session 11: Session 12 was requested explicitly in the retry chat and is now complete. The next session is Session 13 full journey QA. Do not start Session 13 unless the user explicitly asks for it.

Session 12 outcome: Step 07 / Report now presents a bounded grounded explanation preview instead of a prototype/operator report. The route waits for active review readiness, generated candidate completion, same-candidate comparison readiness, and same-candidate verdict readiness before allowing report preview creation. Missing review, missing candidate, missing/mismatched comparison, and missing/mismatched verdict now render as specific blocked states rather than a generic locked workflow screen. Visible copy now frames the output as a client-ready evidence explanation preview, removes primary UI references to AI Commentary context, PDF generation, evidence package types, implementation order, artifact filenames, raw JSON/schema mechanics, winner/best-portfolio language, and trade execution framing, and shows evidence used plus unavailable evidence or warnings without exposing backend artifact mechanics. Report sentence and warning display now passes through existing label normalization plus a narrow safety cleanup for instruction-like, winner-like, and best-portfolio wording. Monitoring remains limited to a watch-note / prior-review-change boundary and does not claim a full Monitoring / What Changed UI exists. The scoped implementation touched `frontend/app/report/page.tsx`, `frontend/components/report/ClientReadyReportPreview.tsx`, `CHANGELOG.md`, and this ExecPlan. It did not change LLM generation, backend grounding schema, PDF generation, verdict/comparison/candidate calculation logic, backend artifacts, JSON schemas, generated outputs, branches, commits, pushes, or merges. Verification passed with `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:api`, `npm.cmd run test:smoke`, targeted Report forbidden-term scans, HTTP route check for `/report...sample=1`, `git diff --check`, and `git status --short`. The first build attempt exposed a stale `.next` manifest problem and passed after safely clearing only `frontend/.next`. Browser visual QA remains limited because no Browser screenshot tool, Playwright package, or system Chrome/Edge executable was available; no screenshot was captured.

Remaining after Session 12: Session 13 is full journey QA. Do not start Session 13 unless the user explicitly asks for it.

Session 13 outcome: Full journey QA was completed for the current MVP frontend/product flow. Verification passed with `npm.cmd run build`, `npm.cmd run typecheck`, `npm.cmd run test:api`, `npm.cmd run test:smoke`, targeted forbidden-term scans focused on primary UI copy, `git diff --check`, and `git status --short`. Visual QA used `http://localhost:3067` on a fresh production Next server and fresh Chrome profile. The visual route chain was Portfolio Input -> Diagnosis/X-Ray -> Stress Evidence -> Hypothesis -> Comparison -> Verdict -> Report. The seeded QA lineage remained consistent across the active review chain: `reviewId=frontend_review_session13_visual`, `selectedCardId=sample_reference_comparison`, generated `candidateId=equal_weight_reference_candidate`, matching comparison candidate, matching verdict candidate, and report-ready state. Screenshots were captured under `runs/session13_visual_qa/01_portfolio_input.png`, `02_diagnosis_xray.png`, `03_stress_evidence.png`, `04_hypothesis.png`, `05_comparison.png`, `06_verdict.png`, and `07_report.png`; the machine-readable summary is `runs/session13_visual_qa/session13_visual_qa_summary.json`. The QA pass found one small obvious primary-copy issue in `/report`: the generated candidate id was displayed as raw `equal_weight_reference_candidate`. Session 13 fixed it in `frontend/app/report/page.tsx` by formatting the visible label through `displayTitleLabel(...)`. Post-fix validation and visual QA passed. No backend calculations, schemas, generated product artifacts, branch, commit, push, or Session 14 content were changed.

Remaining after Session 13: Session 14 should reconcile documentation after implementation sessions. Do not start Session 14 unless the user explicitly asks for it.

Session 14 outcome: Documentation reconciliation is complete for the implementation sessions. The scoped docs pass updated `../../frontend/README.md` from prototype wording to the implemented frontend MVP surface, clarified that Candidate Generation is merged into Hypothesis/Builder, and kept Report framed as a grounded explanation preview. It updated `docs/demo/frontend_backend_vertical_runbook.md` to use product-facing test-path language instead of backend/operator phrasing in the manual click path. It updated `docs/design/portfolio_mri_design_system.md` so the journey progress includes Evidence and Report and does not promote Candidate as a separate current route, and it renamed the design-level AI Commentary card to grounded explanation language. It updated `PRODUCT.md` to state that the current frontend route surface covers Portfolio Input through Report while Monitoring / What Changed remains deferred as a separate UI layer. It added a concise `CHANGELOG.md` entry. No runtime code, backend calculations, schemas, generated outputs, routes, branches, commits, pushes, or merges were changed. Verification passed with targeted stale-language scans, `git diff --check`, and `git status --short`. Runtime tests were not run because this session changed documentation only and did not alter executable examples or behavior.

Remaining after Session 14: Session 15 was the final alignment report and is now complete.

Session 15 outcome: `docs/audits/2026-06-10_product_code_design_synchronization_closure_report.md` now exists and is registered in `docs/audits/README.md`. The report summarizes what was aligned, closed/open mismatch status, P0/P1/P2 status, verification proof, full journey QA evidence, known limitations, and the recommended next milestone. It closes this synchronization pass as `ACCEPTED_FOR_CURRENT_SCOPE`: no open P0 blockers remain, while adapter extraction and edge-state regression coverage are documented as bounded follow-ups. No runtime code, frontend implementation, backend calculations, schemas, generated outputs, routes, branches, commits, pushes, or merges were changed in Session 15. Verification passed with documentation review, `git diff --check`, and `git status --short`. Runtime tests were not run because this session changed documentation only and did not alter executable behavior.

Remaining after Session 15: This ExecPlan is complete for its current scope. Recommended next milestone is a new, separately scoped adapter extraction and edge-state regression coverage plan; do not start it unless the user explicitly asks for it.

## Context and Orientation

Portfolio MRI / Portfolio X-Ray is a diagnosis-first investment decision-support system. The current product truth is called `Diagnosis 2` in repository instructions and top-level documentation. The product is current-portfolio-first and not optimizer-first.

The canonical product flow is:

    Input Portfolio
    -> Portfolio X-Ray
    -> Stress Test Lab
    -> Problem Classification
    -> Candidate Launchpad
    -> Portfolio Alternatives Builder / Hypothesis Builder
    -> Candidate Generation
    -> Current vs Candidate Comparison
    -> Decision Verdict
    -> AI Commentary / grounding
    -> Monitoring / What Changed

The product boundaries are:

- Diagnosis happens before action.
- Candidate does not mean recommendation.
- Verdict does not mean trading instruction.
- No-trade is a valid professional outcome.
- Evidence insufficient is a valid professional outcome.
- AI Commentary explains grounded evidence; it does not decide.
- Backend calculates evidence.
- Adapters translate evidence into product states.
- Frontend presents decision-support meaning.
- Design system controls hierarchy and clarity.
- QA prevents drift.

The current frontend route reality is:

- `frontend/app/portfolio-input/page.tsx`
- `frontend/app/diagnosis/page.tsx`
- `frontend/app/evidence/page.tsx`
- `frontend/app/hypothesis/page.tsx`
- `frontend/app/comparison/page.tsx`
- `frontend/app/verdict/page.tsx`
- `frontend/app/report/page.tsx`

There is no separate current frontend route for Monitoring / What Changed. Candidate / Builder is currently merged into `/hypothesis` for the MVP frontend path. That merge must be treated as an intentional MVP route policy unless a later approved route split changes it.

The main frontend mapping files are:

- `frontend/lib/reviewState.tsx`: browser-side active review state, compact summaries, lineage checks, and much presentation mapping.
- `frontend/lib/displayLabels.ts`: shared user-facing label and sentence normalization.
- `frontend/lib/journey.ts`: journey step definitions and unlock logic.
- `frontend/lib/types.ts`: frontend shared types.

The main backend/runtime product artifacts are:

- `analysis_subject/portfolio_xray.json`
- `analysis_subject/stress_report.json`
- `analysis_subject/problem_classification.json`
- `analysis_subject/candidate_launchpad.json`
- `analysis_subject/portfolio_alternatives_builder.json`
- `candidate_generation.json`
- `current_vs_candidate.json`
- `decision_verdict.json`
- `ai_commentary_context.json`
- `what_changed_summary.json`
- `output_manifest.json` and product bundle metadata

Important source-of-truth documents include:

- `README.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`
- `SPEC.md`
- `OUTPUTS.md`
- `WORKFLOW.md`
- `AGENTS.md`
- `GLOSSARY.md`
- `CHANGELOG.md`
- `DECISIONS.md`
- `TESTING.md`
- `docs/product_flow_operator_guide.md`
- `docs/runtime_entrypoints.md`
- `docs/runtime_artifact_contract.md`
- `docs/design/portfolio_mri_design_system.md`
- `../../frontend/README.md`
- owning files under `docs/specs/`

Existing related working-tree documents to inspect before later sessions:

- `docs/audits/product_code_docs_design_alignment_audit.md`
- `docs/specs/frontend_screen_contracts.md`
- `docs/exec_plans/2026-06-10_post_stress_frontend_flow_alignment_plan.md`

## Executive Diagnosis

Overall status: partially aligned, not yet production-coherent, and still vulnerable to product-code-design drift.

Main product risk: UI can look more polished while still exposing internal workflow logic, backend artifact terms, or optimizer-menu assumptions.

Main engineering risk: presentation adapters and label mapping are scattered, with `frontend/lib/reviewState.tsx` doing too many jobs.

Main documentation risk: existing specs and audits are strong, but there is no permanent contract layer that forces future code, UI, design, and docs to move together.

Main UX risk: the user journey broadly follows the canonical flow, but merged stages, missing Monitoring surface, and prototype-like report copy can make the product feel like an internal workflow instead of a premium decision-support SaaS.

The immediate stabilization need is not a new feature. The immediate need is a disciplined synchronization layer: product flow contract, artifact-to-screen contract, screen contracts, language contract, design-system contract, QA contract, and documentation-sync contract.

## Current Implementation Map

This table is the Session 0 baseline. Later sessions must refine it in the contract files.

| Product Step | Frontend Route | Main Components / Files | Backend Artifacts | Presentation Source / Adapter | Current Status | Main Mismatch | Recommended Fix |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Portfolio Input | `/portfolio-input` | `frontend/components/portfolio/PortfolioInputTable.tsx` | input payload, review result, run-local review folder | `reviewState.tsx`, API route responses | Implemented | Recovery/review id language can feel operator-like | Contract input states and hide technical recovery copy from primary UI |
| X-Ray / Diagnosis | `/diagnosis` | `DiagnosisSummaryPanel`, `PortfolioXRayBlocks` | `portfolio_xray.json`, compact `problem_classification.json` | `reviewState.tsx` compact summary | Implemented | Problem Classification bridge needs contract-backed role | Screen contract must define diagnosis hero, X-Ray evidence, and bridge |
| Stress Lab | `/evidence` | `StressTestLab`, stress panels, `stressLabModel.ts` | `stress_report.json`, X-Ray bridge context | `stressLabModel.ts`, `displayLabels.ts` | Implemented and improved | Route is Evidence while product label is Stress Lab; evidence center vs stress-only boundary needs clarity | Contract the screen as Stress Test Lab, not generic dashboard |
| Problem Classification | merged into Diagnosis and Hypothesis | `hypothesis/page.tsx`, `reviewState.tsx` | `problem_classification.json` | inline page mapping and compact summary | Partially surfaced | It is a product step but no dedicated route | Contract as bridge card and Hypothesis input, not a separate MVP route |
| Candidate Launchpad | `/hypothesis` | `HypothesisCard`, inline mapping | `candidate_launchpad.json` | `hypothesis/page.tsx`, `displayLabels.ts` | Implemented | Can regress into backend Launchpad/card terminology | Screen + language contracts must ban raw fields and define test-path copy |
| Portfolio Alternatives Builder / Hypothesis Builder | `/hypothesis` | setup panels inside page | `portfolio_alternatives_builder.json` | inline mapping and `reviewState.tsx` | Implemented as merged MVP stage | Can look like optimizer cockpit or setup debug panel | Contract selected test setup, method visibility, blocked states |
| Candidate Generation | `/hypothesis` | generated candidate section | `candidate_generation.json` | API response + `reviewState.tsx` summary | Implemented | Candidate lacks separate screen; status can leak generation internals | Keep merged for MVP; contract candidate as diagnostic test only |
| Current vs Candidate Comparison | `/comparison` | `TradeoffSummary`, `CandidateComparisonPanel` | `current_vs_candidate.json` | `reviewState.tsx` summary | Implemented and improved | Needs stronger success criteria / unavailable-state contract | Contract valid vs unavailable comparison states and no fake rows |
| Decision Verdict | `/verdict` | `VerdictPanel` | `decision_verdict.json` | `reviewState.tsx` summary | Implemented and improved | Backend decision status can leak; no-trade/evidence insufficient needs taxonomy | Contract verdict state families and guardrail language |
| Report / Commentary | `/report` | `ClientReadyReportPreview` | `ai_commentary_context.json`, verdict/comparison context | local `reportFromResult()` in page | Implemented and aligned in Session 12 | Primary UI is now framed as a grounded explanation preview with same-run comparison/verdict readiness | Keep Report scoped to grounded explanation; do not expose artifact mechanics or imply full Monitoring UI |
| Monitoring / What Changed | no current route | none visible | `what_changed_summary.json` | none visible | Backend artifact / deferred UI | No frontend surface; report may imply monitoring without a route | Contract as deferred Monitoring layer until route is approved |

## Artifact-to-Screen Map

| Backend Artifact | Producer / Location | Consumer Screen | Adapter / State Source | User-Facing Meaning | Current Issue | Required Contract |
| --- | --- | --- | --- | --- | --- | --- |
| `portfolio_xray.json` | `analysis_subject/` from portfolio review / report materialization | Diagnosis | `reviewState.tsx`, diagnosis components | What the current portfolio owns and where risk/weakness appears | Adapter logic concentrated in `reviewState.tsx` | Define X-Ray sections, evidence quality, and forbidden raw block labels |
| `stress_report.json` | `analysis_subject/` from Stress Lab pipeline | Evidence / Stress Lab | `stressLabModel.ts` | How current portfolio behaves under stress | Strong mapping but separate from global adapter contract | Define Stress Lab screen model and scenario-label rules |
| `problem_classification.json` | `analysis_subject/` Block 4 diagnosis outputs | Diagnosis bridge, Hypothesis | `reviewState.tsx`, `hypothesis/page.tsx` | Main diagnosis and what should be tested next | Product step is split across screens | Define bridge and Hypothesis input contract |
| `candidate_launchpad.json` | `analysis_subject/` Block 4 diagnosis outputs | Hypothesis | `hypothesis/page.tsx` and `HypothesisCard` | Available hypothesis test paths | Raw card/method language can regress | Define Launchpad-to-Hypothesis presentation model |
| `portfolio_alternatives_builder.json` | `analysis_subject/` Builder setup output | Hypothesis | `hypothesis/page.tsx`, `reviewState.tsx` | Selected test setup | Setup can look technical | Define setup-only boundary and method visibility |
| `candidate_generation.json` | output root after explicit generate action | Hypothesis, Comparison gate | API response and `reviewState.tsx` | One generated diagnostic test candidate | Candidate has no own route and can be over-read as recommendation | Define candidate status taxonomy and lineage rules |
| `current_vs_candidate.json` | output root after comparison | Comparison, Verdict | `reviewState.tsx` | Trade-offs between current and selected candidate | Need contract for missing metrics and success criteria | Define valid / unavailable / insufficient states |
| `decision_verdict.json` | output root after verdict | Verdict, Report | `reviewState.tsx` | Non-binding decision-support outcome | Raw decision status can leak | Define verdict families and no-trade/evidence-insufficient display |
| `ai_commentary_context.json` | output root after report/verdict grounding | Report | `report/page.tsx` local mapping | Grounded explanation inputs, not final LLM authority | Report copy is still prototype/operator-like | Define grounded preview language and source references |
| `what_changed_summary.json` | output root after compare/monitoring when available | none currently | none currently | What changed since prior review | No visible UI surface | Define deferred Monitoring contract |
| manifest / product bundle metadata | `output_manifest.json`, generated paths | API/recovery/operator flows | API routes and docs | Path discovery and artifact freshness | Should not become user-facing copy | Define drill-down-only usage |

## Mismatch Register

Each mismatch is written as a future work item. Later sessions must refine, close, split, or re-severity these items as evidence changes.

### P0 — Trust-breaking / product truth issues

| ID | Severity | Location / File | Issue | Why It Matters | Expected Behavior | Suggested Fix | Acceptance Criteria | Risk If Ignored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0-01 | P0 | `frontend/app/report/page.tsx` | Closed in Session 12: primary Report UI no longer frames the page around AI Commentary context, PDF generation, evidence package types, implementation order, artifact filenames, raw JSON/schema mechanics, winner/best-portfolio language, or trade execution framing. | The final screen must maintain premium/client-ready trust. | Report describes a grounded explanation preview, not implementation details. | Keep future Report edits inside the same presentation/readiness boundary. | Forbidden-term scan should continue to pass for Report primary UI. | Regression would make the final decision stage look like an internal operator tool again. |
| P0-02 | P0 | No route/component for Monitoring | `what_changed_summary.json` is product-facing backend output but has no visible frontend surface. | Canonical flow ends with Monitoring / What Changed, but UI stops at Report. | Current UI must mark Monitoring as deferred, or surface a compact What Changed section. | Contracts define Monitoring as deferred until route decision; Report must not pretend full Monitoring exists. | Screen contract and artifact map explicitly mark Monitoring status. | Future agents may invent partial monitoring UI inconsistently. |
| P0-03 | P0 | Missing `docs/contracts/` | No durable cross-cutting contract layer exists. | Docs/code/design can drift again after this audit. | Product, artifact, screen, language, design, QA, and doc-sync contracts exist and are maintained. | Sessions 1-7 create contract docs. | All seven contract docs exist and are linked in relevant docs. | Stabilization depends on memory instead of enforceable docs. |
| P0-04 | P0 | `frontend/lib/reviewState.tsx` | Review state, artifact compaction, label cleanup, candidate/comparison/verdict summaries, and journey readiness are mixed. | A future change can leak backend truth or break stale-candidate scoping. | State persistence, artifact adapters, and screen presentation models should have explicit boundaries. | Session 8 creates adapter architecture plan before refactor. | Adapter plan says what stays centralized and what splits by screen. | Review state becomes a monolith and hidden product source of truth. |
| P0-05 | P0 | Working tree | Many pre-existing dirty files exist. | Broad edits, staging, or rewrites can destroy unrelated work. | Every session starts with dirty-tree inventory and stages only scoped files if committing is approved. | QA contract and DOC_SYNC contract require `git status --short` and scoped file list. | Final reports list changed files and pre-existing dirty areas. | Work becomes unrecoverable or mixed with unrelated changes. |

### P1 — Major clarity / UX / adapter issues

| ID | Severity | Location / File | Issue | Why It Matters | Expected Behavior | Suggested Fix | Acceptance Criteria | Risk If Ignored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1-01 | P1 | `/hypothesis` | Candidate / Builder is merged into Hypothesis, but this must remain explicit MVP policy. | Future agents may add a separate route or duplicate candidate state without decision. | Candidate remains merged for MVP unless a route split is explicitly approved. | Screen contract records route policy. | Contract states current MVP has no `/candidate` route. | Journey and docs diverge. |
| P1-02 | P1 | `frontend/lib/displayLabels.ts` and components | Label mapping exists but is not backed by a presentation-language contract. | Raw backend terms can re-enter UI. | Forbidden terms and approved replacements are documented and scanned. | Session 4 creates language contract. | QA contract includes rg patterns. | UI copy slowly regresses. |
| P1-03 | P1 | Step 04 method display | Method visibility must stay contextual and not become optimizer menu. | Hypothesis Builder can become optimizer cockpit. | Show only contextually relevant MVP methods; hide advanced methods. | Screen and language contracts define method visibility. | Step 04 scan shows no advanced/later method cards in main UI. | Product looks like optimizer cockpit. |
| P1-04 | P1 | `/comparison` | Comparison state has improved, but contract must prevent fake rows and unavailable metrics. | Fake `n/a` tables reduce trust. | Show candidate missing, metrics unavailable, or valid comparison distinctly. | Session 10 applies comparison contract. | Visual QA proves no fake unavailable table. | Users may interpret missing metrics as real comparison. |
| P1-05 | P1 | `/verdict` | Verdict state has improved, but outcome taxonomy needs contract enforcement. | No-trade and evidence-insufficient can look like errors. | Verdict families are first-class: keep current, no material rebalance, rebalance review, test another, evidence insufficient, failed/infeasible. | Session 11 applies verdict contract. | Verdict visual QA covers no-trade/evidence-insufficient. | Users overread or undertrust verdict. |
| P1-06 | P1 | Design system / components | Status badge taxonomy is not fully formalized. | Color and badge meanings can drift. | Blue action, amber caution, green success/improvement, red risk/worsening, slate neutral. | Session 5 creates design contract. | Components and contract agree on badge families. | UI becomes noisy or crypto/trading-like. |

### P2 — Maintainability / design-system issues

| ID | Severity | Location / File | Issue | Why It Matters | Expected Behavior | Suggested Fix | Acceptance Criteria | Risk If Ignored |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2-01 | P2 | Docs and specs | Existing docs are strong but distributed. | Future contributors may pick the wrong source of truth. | Contracts route each change to owning docs. | Session 7 creates DOC_SYNC contract. | Final reports include documentation impact checks. | Docs become stale again. |
| P2-02 | P2 | Sample/demo state | Static demo data and real review state can be confused. | Demo may be mistaken for active product evidence. | Sample mode is visibly labelled and QA checks active review id when relevant. | QA contract adds sample/demo checks. | Visual QA reports sample mode status. | False confidence from stale/demo data. |
| P2-03 | P2 | `docs/design/portfolio_mri_design_system.md` vs CSS/components | Design principles exist but are not enforced as a contract. | Visual changes can drift into flashy/dashboard style. | Design contract defines compact enforceable rules. | Session 5 creates design system contract. | New UI changes cite design contract. | Premium positioning erodes. |
| P2-04 | P2 | Test commands and runbooks | QA requirements are scattered across `TESTING.md`, frontend README, AGENTS, and runbooks. | Agents may run the wrong checks or race `.next`. | QA contract lists standard package and Windows Next race warning. | Session 6 creates QA contract. | Future implementation reports include checks run and unverified areas. | Passing work may be unverified or flaky. |

### Later / Advanced Scope

Keep these out of Core MVP screens unless an owning spec explicitly promotes them: macro overlay, full macro dashboard, advanced optimization, full custom constraints, tax-aware optimization, tactical tilt, full multi-candidate arena, robustness scorecards as product hero, Pareto frontier, regret analysis, assumption sensitivity, what-if simulator, full crisis replay, full monitoring workspace, client profile/suitability, asset diagnostics / Asset X-Ray, full PDF report design, full Decision Journal, multi-client workspace, and polished PDF report product.

If these exist in code or generated outputs, classify them as `Advanced`, `Backend evidence`, `Technical artifact`, `Legacy`, `Generated support artifact`, or `Future/backlog`.

## Dynamic Documentation Governance

This governance rule is mandatory for all later sessions in this plan and should be made permanent in `docs/contracts/DOC_SYNC_CONTRACT.md`.

Every meaningful change must include a documentation impact check. A meaningful change is any change to behavior, output, UI copy, route, artifact, adapter, design, QA, command, source-of-truth routing, product boundary, generated-output policy, or shared helper behavior.

If a meaningful change affects an owning document, update that document in the same session. If no documentation update is needed, the final response must include the exact statement:

    No docs updated because: <reason>

QA is incomplete until the documentation impact check is performed and reported. Future agents must not treat code as product truth alone. Docs, code, adapters, tests, and design must stay synchronized.

### Dynamic Doc Sync Matrix

| Change Type | Required Documentation Impact |
| --- | --- |
| Product flow / product boundary changes | Update `README.md`, `PRODUCT.md`, `SPEC.md`, `docs/product_flow_operator_guide.md`, and relevant contract docs. |
| Runtime commands / CLI behavior | Update `README.md`, `OUTPUTS.md`, `docs/runtime_entrypoints.md`, and `WORKFLOW.md`. |
| Backend artifact schema/output changes | Update `OUTPUTS.md`, owning `docs/specs/*`, `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`, and tests. |
| Frontend route/screen behavior | Update `../../frontend/README.md`, `docs/contracts/SCREEN_CONTRACTS.md`, `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`, and design contract if visual. |
| UI copy / labels / forbidden terms | Update `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`, `docs/contracts/SCREEN_CONTRACTS.md`, and `frontend/lib/displayLabels.ts` if implementation changes are made. |
| Design tokens/components/status badges | Update `docs/design/portfolio_mri_design_system.md` and `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`. |
| QA/test workflow changes | Update `TESTING.md`, `docs/contracts/QA_CONTRACT.md`, and the relevant runbook. |
| Known limitation / technical debt discovered | Update `KNOWN_ISSUES.md` or the active ExecPlan. |
| Architectural decision | Update `DECISIONS.md`. |
| Completed meaningful change | Update `CHANGELOG.md`. |

Session 7 turned this section into `docs/contracts/DOC_SYNC_CONTRACT.md` and linked it from the other contract docs.

## Contract Files To Create

Session 1 creates `docs/contracts/PRODUCT_FLOW_CONTRACT.md`. It defines canonical product steps, user question per step, backend artifacts per step, allowed behavior, forbidden behavior, next-step logic, and boundaries such as candidate is not recommendation and verdict is not trading instruction. It prevents drift by making product flow the starting point for screen, adapter, and docs changes.

Session 2 creates `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`. It maps backend artifacts to frontend screens and presentation adapters. It identifies unused artifacts, missing screens, stale/demo data risks, and lineage rules. It prevents drift by making every artifact's user-facing meaning explicit.

Session 3 creates `docs/contracts/SCREEN_CONTRACTS.md`. It defines each screen's product role, user question, artifacts used, must-show sections, must-not-show sections, primary CTA, next step, forbidden UI language, empty states, and QA checks. It prevents drift by giving every screen an owned contract.

Session 4 creates `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`. It defines forbidden backend/internal terms, approved user-facing labels, `displayLabels.ts` responsibilities, and QA search patterns. It prevents drift by blocking raw backend vocabulary from primary UI.

Session 5 creates `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`. It defines premium institutional visual rules, status badge taxonomy, card hierarchy, CTA rules, warning states, generated states, empty/unavailable states, and sample/demo labels. It prevents drift by turning design direction into enforceable product UI rules.

Session 6 creates `docs/contracts/QA_CONTRACT.md`. It defines required checks before commit: typecheck, build, tests, smoke, visual QA, forbidden-term scan, git diff checks, and the Windows `.next` race warning. It prevents drift by making QA a product contract, not an optional habit.

Session 7 creates `docs/contracts/DOC_SYNC_CONTRACT.md`. It defines which docs must change when product, code, design, outputs, routes, commands, QA, or boundaries change. It prevents drift by requiring documentation impact checks in every future session.

## Session-by-Session Execution Plan

### Session 0 — Audit and Freeze

Goal: Inventory the repository, capture current branch/dirty tree status, and create this synchronization plan.

Scope: docs-only plan creation.

Files likely touched: `docs/exec_plans/2026-06-10_product_code_design_synchronization_plan.md`.

Files explicitly not to touch: backend source, frontend source, generated outputs, existing dirty files, `docs/contracts/*`.

Acceptance criteria: this plan exists, includes dynamic doc-sync governance, records branch and dirty-tree status, and no runtime behavior changes.

Checks: `git status --short`, `git branch --show-current`, `Test-Path` for the target plan and `docs/contracts/`.

Expected output: Session 0 complete message with created path and stop.

Commit recommendation: no commit unless user approves after review.

Rollback risk: low; remove only this file if Session 0 must be undone.

### Session 1 — Product Flow Contract

Goal: Create `docs/contracts/PRODUCT_FLOW_CONTRACT.md`.

Scope: define canonical steps, user question per step, backend artifacts per step, allowed behavior, forbidden behavior, next-step logic, and boundaries.

Files likely touched: `docs/contracts/PRODUCT_FLOW_CONTRACT.md`.

Files explicitly not to touch: frontend implementation and backend runtime.

Acceptance criteria: contract clearly states the flow and all product boundaries; advanced/legacy/backlog features are not promoted.

Checks: doc review and `git diff --check`.

Expected output: contract file and documentation impact note.

Commit recommendation: docs-only commit after user approval.

Rollback risk: low.

### Session 2 — Artifact-to-Screen Contract

Goal: Create `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`.

Scope: map product artifacts to screens and presentation adapters, including deferred Monitoring.

Files likely touched: `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`.

Files explicitly not to touch: JSON schemas and API routes.

Acceptance criteria: every required product artifact has producer, location, consumer screen, adapter, user-facing meaning, issue, and contract.

Checks: targeted `rg` for artifact references and `git diff --check`.

Expected output: artifact map.

Commit recommendation: docs-only commit after user approval.

Rollback risk: low.

### Session 3 — Screen Contracts

Goal: Create `docs/contracts/SCREEN_CONTRACTS.md`.

Scope: define responsibilities for Portfolio Input, X-Ray, Stress Lab, Hypothesis Builder, Comparison, Verdict, Report, and deferred Monitoring.

Files likely touched: `docs/contracts/SCREEN_CONTRACTS.md`.

Files explicitly not to touch: route files and components.

Acceptance criteria: each screen has product role, user question, artifacts, adapter, must-show, must-not-show, CTA, next step, forbidden terms, current mismatch, and QA checks.

Checks: compare against route list and `git diff --check`.

Expected output: screen contract.

Commit recommendation: docs-only commit after user approval.

Rollback risk: low.

### Session 4 — Presentation Language Rules

Goal: Create `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`.

Scope: define forbidden backend/internal terms, approved replacements, display-label responsibilities, and rg patterns.

Files likely touched: `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`.

Files explicitly not to touch: `frontend/lib/displayLabels.ts` unless the user explicitly moves to implementation.

Acceptance criteria: the contract includes forbidden terms from the user brief and current findings, replacement labels, and scan commands.

Checks: run targeted `rg` scans for contract evidence; `git diff --check`.

Expected output: language rules.

Commit recommendation: docs-only commit after user approval.

Rollback risk: low.

### Session 5 — Design System Contract

Goal: Create `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`.

Scope: make the premium institutional SaaS design rules enforceable.

Files likely touched: `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`.

Files explicitly not to touch: CSS/components unless a later implementation session starts.

Acceptance criteria: contract defines dark institutional style, color semantics, badge taxonomy, card hierarchy, typography hierarchy, CTA placement, warning states, generated states, unavailable states, sample/demo states, and forbidden visual directions.

Checks: compare against `docs/design/portfolio_mri_design_system.md`; `git diff --check`.

Expected output: design contract.

Commit recommendation: docs-only commit after user approval.

Rollback risk: low.

### Session 6 — QA Contract

Goal: Create `docs/contracts/QA_CONTRACT.md`.

Scope: define standard checks for future sessions.

Files likely touched: `docs/contracts/QA_CONTRACT.md`.

Files explicitly not to touch: test code unless a later QA implementation session starts.

Acceptance criteria: contract defines frontend typecheck/build/API tests/smoke, backend targeted pytest, visual QA, forbidden-term scan, `git status`, `git diff --check`, and Windows `.next` race warning.

Checks: verify commands match `frontend/package.json` and existing project docs; `git diff --check`.

Expected output: QA contract.

Commit recommendation: docs-only commit after user approval.

Rollback risk: low.

### Session 7 — DOC_SYNC_CONTRACT

Goal: Create `docs/contracts/DOC_SYNC_CONTRACT.md`.

Scope: make dynamic documentation governance permanent.

Files likely touched: `docs/contracts/DOC_SYNC_CONTRACT.md`; possibly link from other contracts if they already exist.

Files explicitly not to touch: runtime code.

Acceptance criteria: includes documentation impact rule, dynamic doc sync matrix, final-response requirement, and examples of when to update README, SPEC, OUTPUTS, TESTING, DECISIONS, CHANGELOG, frontend README, design docs, and contracts.

Checks: `git diff --check`.

Expected output: doc sync contract.

Commit recommendation: docs-only commit after user approval.

Rollback risk: low.

### Session 8 — Adapter Architecture Plan

Goal: Audit adapter responsibilities and decide what remains centralized and what splits.

Scope: inspect `reviewState.tsx`, `displayLabels.ts`, `types.ts`, `journey.ts`, and screen components; create an adapter plan without refactoring unless explicitly approved.

Files likely touched: a new docs/audit or docs/exec plan addendum; possibly no source code.

Files explicitly not to touch: frontend implementation unless user approves.

Acceptance criteria: plan states screen-specific adapter boundaries for X-Ray, Stress, Hypothesis, Comparison, Verdict, and Report.

Checks: targeted `rg`, no runtime tests unless implementation begins.

Expected output: adapter plan.

Commit recommendation: docs-only commit after user approval.

Rollback risk: low.

### Session 9 — Step 04 Contract Application

Goal: Apply contracts to Hypothesis Builder only.

Scope: make Step 04 represent Current Diagnosis -> Recommended Test -> Available Test Paths -> Selected Test Setup -> Generate Test Candidate -> Test Candidate Generated -> Continue to Comparison.

Files likely touched: `frontend/app/hypothesis/page.tsx`, `frontend/components/hypothesis/HypothesisCard.tsx`, `frontend/lib/displayLabels.ts`, relevant contracts/docs.

Files explicitly not to touch: backend calculations, candidate generation logic, JSON schemas, comparison/verdict logic.

Acceptance criteria: contextual MVP methods only, monitoring path secondary, no disabled backend method cards, no backend/internal terms, candidate not recommendation.

Checks: frontend typecheck/build/test API/smoke sequentially; visual QA for `/hypothesis...sample=1`; forbidden-term scan.

Expected output: Step 04 implementation and docs sync.

Commit recommendation: one frontend/docs commit after approval.

Rollback risk: medium due existing dirty tree; stage only intended files.

### Session 10 — Step 05 Contract Application

Goal: Apply contracts to Current vs Candidate Comparison.

Scope: ensure comparison shows true trade-off only when candidate and metrics exist.

Files likely touched: `frontend/app/comparison/page.tsx`, `frontend/components/comparison/*`, `frontend/lib/reviewState.tsx`, relevant contracts/docs.

Files explicitly not to touch: comparison calculation logic and backend artifacts.

Acceptance criteria: candidate not generated, comparison unavailable, and valid comparison states are distinct; no fake `n/a` tables; no final verdict; no candidate-is-better language.

Checks: frontend validation; visual QA for `/comparison...sample=1`; forbidden-term scan.

Expected output: Step 05 implementation and docs sync.

Commit recommendation: one frontend/docs commit after approval.

Rollback risk: medium.

### Session 11 — Step 06 Contract Application

Goal: Apply contracts to Decision Verdict.

Scope: make verdict states professional and non-binding.

Files likely touched: `frontend/app/verdict/page.tsx`, `frontend/components/verdict/VerdictPanel.tsx`, `frontend/lib/reviewState.tsx`, relevant contracts/docs.

Files explicitly not to touch: verdict calculation logic and backend artifacts.

Acceptance criteria: keep current, no material rebalance, rebalance review, test another, evidence insufficient, candidate failed/infeasible, and monitoring outcomes display safely; no trading instruction or best-portfolio language.

Checks: frontend validation; visual QA for `/verdict...sample=1`; forbidden-term scan.

Expected output: Step 06 implementation and docs sync.

Commit recommendation: one frontend/docs commit after approval.

Rollback risk: medium.

### Session 12 — Report / Commentary Alignment

Goal: Align Report / AI Commentary grounding presentation.

Scope: Report explains grounded outputs only and avoids prototype/operator terms.

Files likely touched: `frontend/app/report/page.tsx`, `frontend/components/report/*`, relevant contracts/docs.

Files explicitly not to touch: LLM generation, backend grounding schema, PDF generation.

Acceptance criteria: no invented conclusions, no backend terms, no "No PDF generation" primary copy, no "AI Commentary context" primary copy; partial evidence handled clearly.

Checks: frontend validation; visual QA for `/report...sample=1` or active sample route if available; forbidden-term scan.

Expected output: Report alignment and docs sync.

Commit recommendation: one frontend/docs commit after approval.

Rollback risk: medium.

### Session 13 — Full Journey QA

Goal: Run full journey QA from Input through Report.

Scope: verify product logic, CTA flow, artifact usage, forbidden terms, visual hierarchy, sample/demo labeling, no recommendation leakage, and no backend leakage.

Files likely touched: QA report under `docs/audits/` or ExecPlan update; source changes only for small fixes if approved.

Files explicitly not to touch: backend calculations and generated output cleanup.

Acceptance criteria: QA report includes URL/port, route, active `reviewId` if relevant, sample mode status, reset/recovered browser state, screenshots if captured, and unverified areas.

Checks: frontend validation, visual QA, forbidden-term scan, git checks.

Expected output: full journey QA report.

Commit recommendation: QA/docs commit after approval.

Rollback risk: low for docs, medium if small fixes are included.

### Session 14 — Documentation Reconciliation

Goal: Update docs to reflect actual implemented flow after fixes.

Scope: reconcile README, PRODUCT, SPEC, OUTPUTS, frontend README, design docs, contracts, TESTING, CHANGELOG, DECISIONS, or KNOWN_ISSUES as required by `DOC_SYNC_CONTRACT.md`.

Files likely touched: owning docs only.

Files explicitly not to touch: runtime code unless a doc claim reveals a scoped bug and user approves fixing it.

Acceptance criteria: current MVP, advanced/later, legacy/backlog are separated; no stale references remain after renames or route decisions.

Checks: `rg` for stale terms; `git diff --check`; docs verification if available.

Expected output: documentation sync.

Commit recommendation: docs-only commit after approval.

Rollback risk: low.

### Session 15 — Final Alignment Report

Goal: Create final audit report.

Scope: summarize what was aligned, what remains, P0/P1/P2 status, test results, screenshots, known limitations, and next recommended milestone.

Files likely touched: `the closure report placeholder filename` and ExecPlan update.

Files explicitly not to touch: runtime code.

Acceptance criteria: final report lists closed/open mismatches and proof checks.

Checks: `git status --short`, `git diff --check`, docs review.

Expected output: final alignment report.

Commit recommendation: final docs commit after approval.

Rollback risk: low.

## QA Plan

For Session 0, only repository inspection and file verification are required because the session is docs-only.

For future frontend implementation sessions, run from `frontend/`:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

Run these sequentially on Windows. Do not run Next build and smoke/dev server against the same `.next` directory in parallel because this repository has known `.next` race risk.

For backend-relevant sessions, run the narrowest reliable pytest first, then broaden. Candidate/comparison/verdict changes should include the relevant targeted tests and one-candidate validation where applicable.

Visual QA for changed frontend routes must include a fresh local target, exact URL/port, route, active `reviewId` when relevant, sample mode status, browser state reset/recovery status, screenshots captured if any, and unverified areas.

Forbidden-term scans should include relevant frontend files and the terms:

    backend|artifact|JSON|source problem|selected hypothesis|setup preview|run-local|candidate generation readiness|not available yet|disabled|true|false|n/a|outputs\.|stale downstream|baseline_or_candidate|no comparison or verdict was generated|factory|candidate_generation|implementation order|source artifact|Backend does not expose

Every implementation session must also run:

    git status --short
    git diff --check

If committing is approved, keep commits atomic and avoid one large mixed backend/frontend/docs/design commit.

## Branch and Commit Strategy

Recommended strategy:

- One docs-only audit/plan commit for Session 0 if user approves.
- One contract commit or separate commits per contract group for Sessions 1-7.
- One implementation commit per screen for Sessions 9-12.
- One QA/final alignment commit for Sessions 13-15.
- No mixed mega-commit.
- No push until user approves.
- No merge until full journey QA passes.

Because the working tree was already dirty before Session 0, future sessions must stage only explicitly intended files and must never use broad `git add .`, broad checkout, reset, or cleanup commands.

## Immediate Next Action

Session 15 is complete. This ExecPlan is closed for its current scope.

Recommended next action: if the user wants more hardening, create a new scoped plan for adapter extraction and edge-state regression coverage. Do not start that follow-up unless the user explicitly asks for it.

## Final Response Contract For Session 0

When Session 0 completes, report:

- created document path;
- branch name;
- working tree status summary;
- whether code was changed;
- whether runtime behavior was changed;
- top P0 findings;
- top P1 findings;
- proposed session list;
- recommended immediate next action;
- tests/checks run;
- blocked or uncertain areas.

Then stop.

Revision note (2026-06-10 14:40+02:00 / Codex): Updated this living ExecPlan after Session 5 to record the new design-system contract, the docs-only implementation boundary, the outcome, and the next-session pointer.

Revision note (2026-06-10 14:48+02:00 / Codex): Updated this living ExecPlan after Session 6 to record the QA contract, command-verification evidence, docs-only implementation boundary, outcome, and next-session pointer. Do not start Session 7 unless the user explicitly asks for it.

Revision note (2026-06-10 14:55+02:00 / Codex): Updated this living ExecPlan after Session 7 to record the DOC_SYNC contract, links from existing contracts, docs-only implementation boundary, outcome, and next-session pointer. Do not start Session 8 unless the user explicitly asks for it.

Revision note (2026-06-10 15:03+02:00 / Codex): Updated this living ExecPlan after Session 8 to record the adapter architecture audit, `docs/audits/2026-06-10_adapter_architecture_plan.md`, the docs-only/no-refactor boundary, audit-register update, outcome, and next-session pointer. Do not start Session 9 unless the user explicitly asks for it.

Revision note (2026-06-10 15:52+02:00 / Codex): Updated this living ExecPlan after Session 10 to record the Step 05 Comparison contract application, the route-level JourneyGate decision, visual QA limitation for synthetic unavailable/valid states, verification evidence, outcome, and next-session pointer. Do not start Session 11 unless the user explicitly asks for it.

Revision note (2026-06-10 16:35+02:00 / Codex): Updated this living ExecPlan after Session 11 to record the Step 06 Verdict contract application, the route-level JourneyGate decision, safe non-binding verdict-state mapping, visual QA blocker after hard stop, verification evidence, outcome, and next-session pointer. Do not start Session 12 unless the user explicitly asks for it.

Revision note (2026-06-10 17:31+02:00 / Codex): Updated this living ExecPlan after Session 12 to record the Step 07 Report / grounded explanation contract application, evidence-lineage blockers, removal of prototype/internal primary UI language, final frontend validation results, visual QA tooling limitation, and next-session pointer. Do not start Session 13 unless the user explicitly asks for it.

Revision note (2026-06-10 18:10+02:00 / Codex): Updated this living ExecPlan after Session 13 to record full journey QA, the fresh localhost/CDP visual QA evidence, the same-chain lineage check, the small Report candidate-label fix, verification results, and the next-session pointer. Do not start Session 14 unless the user explicitly asks for it.
Revision note (2026-06-10 22:51+02:00 / Codex): Updated this living ExecPlan after Session 14 to record documentation reconciliation, narrowed stale-doc findings, docs-only/no-runtime boundary, verification evidence, and the next-session pointer. Do not start Session 15 unless the user explicitly asks for it.
Revision note (2026-06-10 23:20+02:00 / Codex): Updated this living ExecPlan after Session 15 to record the final closure report, audit-register update, accepted-for-current-scope verdict, bounded follow-ups, docs-only/no-runtime boundary, verification evidence, and plan closure.
