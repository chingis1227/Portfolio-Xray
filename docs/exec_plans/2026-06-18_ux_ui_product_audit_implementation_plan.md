# UX/UI Product Audit Implementation Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. It implements the roadmap from
`docs/audits/2026-06-18_ux_ui_product_audit_sprint.md` without changing backend formulas,
portfolio math, data rules, generated outputs, or production infrastructure.

## Purpose / Big Picture

Portfolio MRI should feel like an investment decision room, not an optimizer cockpit. After this
work, a financially literate self-directed investor can move through the current portfolio-first
journey with clearer route jobs, consistent product-language states, isolated UI state coverage,
and safer diagnostic-test wording. The work is visible by opening the design foundation docs,
reviewing `/sandbox/components`, and checking the key routes from Portfolio Input through Report.

## Progress

- [x] (2026-06-18) Created this living ExecPlan from the UX/UI audit and the accepted implementation plan.
- [x] (2026-06-18) Created the no-code UX foundation documents for users/jobs, route jobs, component states, and text wireframes.
- [x] (2026-06-18) Added shared product-state components and active diagnostic test context for downstream routes.
- [x] (2026-06-18) Expanded `/sandbox/components` into a structured state gallery for isolated UI review.
- [x] (2026-06-18) Applied first-pass route wording and shared-state alignment for Diagnosis, Hypothesis, Comparison, Verdict, and Report.
- [x] (2026-06-18) Ran the full frontend verification set and browser visual QA on fresh localhost targets.
- [x] (2026-06-18) Applied visual-QA follow-up copy fixes for empty Verdict/Report diagnostic-test fallback states.

## Surprises & Discoveries

- Observation: The working tree already contained uncommitted design/frontend changes and untracked audit/sandbox/UI files before this implementation session.
  Evidence: `git status --short` showed modified `DESIGN.md`, contracts, diagnosis components, globals, and untracked sandbox/UI component files before new edits.
- Observation: `/onboarding/goals` is implemented only as a compatibility page and is referenced by an older 2026-06-12 ExecPlan, while current screen contracts omit it from the canonical journey.
  Evidence: `rg -n "onboarding/goals|goals" frontend docs` found `frontend/app/onboarding/goals/page.tsx` and legacy plan references, but current route contracts route onboarding through `/onboarding/investor-type` and `/onboarding/loading`.
- Observation: Some route files contained mojibake bullet/check symbols in visible list markup.
  Evidence: route components showed `вЂў`, `вњ“`, `в—Џ`, and `в—‹` in JSX before cleanup.

## Decision Log

- Decision: Treat the primary launch user as a financially literate self-directed investor.
  Rationale: This keeps the UI plain-language and avoids advisor-only professional jargon while preserving enough rigor for analysts and advisors as secondary users.
  Date/Author: 2026-06-18 / Codex.
- Decision: Use `Diagnostic test` as the primary user-facing concept and keep `candidate` only where current route names or internal backend concepts require it.
  Rationale: This reduces the risk that users interpret a generated candidate as a recommendation, winner, or trading instruction.
  Date/Author: 2026-06-18 / Codex.
- Decision: Expand `/sandbox/components` first instead of adopting Storybook in this implementation wave.
  Rationale: The repository already has a sandbox route; expanding it gives isolated state coverage without adding dependencies or maintenance overhead.
  Date/Author: 2026-06-18 / Codex.
- Decision: Classify `/onboarding/goals` as a legacy compatibility route for now, not a canonical journey step and not removed in this wave.
  Rationale: Current contracts exclude it, but older plans and the compatibility page still exist, so safe deletion requires a separate explicit cleanup.
  Date/Author: 2026-06-18 / Codex.

## Outcomes & Retrospective

The initial implementation establishes the foundation-first workflow requested by the audit: docs define the user, route jobs, state matrix, and wireframes; shared state components make valid product states reusable; the sandbox gives a local review surface before production routes; and key route copy now uses diagnostic-test language more consistently. Frontend typecheck, build, API-route tests, smoke tests, language scans, and fresh-localhost Playwright visual QA were run. Visual QA covered `/sandbox/components`, `/portfolio-input`, `/diagnosis`, `/hypothesis?sample=1`, `/comparison`, `/verdict`, and `/report`; final rechecks covered `/verdict` and `/report` empty-state fallbacks.

## Context and Orientation

The current product flow is current-portfolio-first: public landing, email sign-in, onboarding,
Portfolio Input, Portfolio Diagnosis, Stress Test Lab, Client Fit, Hypothesis, Current vs Candidate
Comparison, Decision Verdict, and Report Preview. The frontend lives under `frontend/`, with Next.js
routes in `frontend/app/` and reusable components in `frontend/components/`.

The important files for this plan are:

- `docs/audits/2026-06-18_ux_ui_product_audit_sprint.md`: audit input.
- `docs/design/ux_product_brief.md`: user/jobs/language foundation.
- `docs/design/screen_job_matrix.md`: route job and state matrix.
- `docs/design/component_state_matrix.md`: component state requirements and sandbox coverage.
- `frontend/components/ui/States.tsx`: reusable product-facing state shells.
- `frontend/components/ui/ActiveDiagnosticTestContext.tsx`: compact context strip for downstream route lineage.
- `frontend/app/sandbox/components/page.tsx`: isolated UI state gallery.
- `frontend/components/diagnosis/DiagnosisScreen.tsx`: benchmark route state handling.
- `frontend/components/hypothesis/HypothesisScreen.tsx`: high-complexity diagnostic-test route.
- `frontend/components/comparison/ComparisonScreen.tsx`, `frontend/components/verdict/VerdictScreen.tsx`, and `frontend/components/report/ReportScreen.tsx`: downstream consistency routes.

A diagnostic test candidate is a generated portfolio used for comparison only. It is not a
recommendation, a winner, or a trade order. Client Fit is diagnostic context only and cannot approve
suitability or hide material portfolio issues.

## Plan of Work

First, create the no-code foundation docs so the implementation has a stable target. Second, extend
the reusable state components and sandbox state gallery without changing backend behavior. Third,
connect the new state/context components to Diagnosis and downstream routes where they reduce local
state drift. Fourth, replace visible candidate-first wording with diagnostic-test wording where doing
so does not rename backend fields, route files, or API contracts. Fifth, validate with static checks,
forbidden-term scans, and browser QA.

## Concrete Steps

Run commands from the repository root unless a command says otherwise.

1. Inspect current contracts and files:

    Get-Content RULES.md -Raw
    Get-Content WORKFLOW.md -Raw
    Get-Content DESIGN.md -Raw
    Get-Content docs\contracts\SCREEN_CONTRACTS.md -Raw
    Get-Content docs\contracts\DESIGN_SYSTEM_CONTRACT.md -Raw
    Get-Content docs\contracts\PRESENTATION_LANGUAGE_RULES.md -Raw
    Get-Content docs\contracts\QA_CONTRACT.md -Raw

2. Create or update foundation docs under `docs/design/` and this ExecPlan under `docs/exec_plans/`.

3. Update shared frontend components:

    frontend\components\ui\States.tsx
    frontend\components\ui\ActiveDiagnosticTestContext.tsx
    frontend\app\sandbox\components\page.tsx

4. Update route components only for product-language state alignment and context display:

    frontend\components\diagnosis\DiagnosisScreen.tsx
    frontend\components\hypothesis\HypothesisScreen.tsx
    frontend\components\comparison\ComparisonScreen.tsx
    frontend\components\verdict\VerdictScreen.tsx
    frontend\components\report\ReportScreen.tsx

5. Run verification sequentially from `frontend/`:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

6. Run language scans from the repository root using the commands in
`docs/contracts/PRESENTATION_LANGUAGE_RULES.md`.

7. Run visual QA on a fresh localhost target. For full journey QA, use:

    cd frontend
    npm.cmd run qa:vertical -- --scenario-limit 3

8. Finish with:

    git diff --check
    git status --short

## Validation and Acceptance

Acceptance is behavior-based:

- `docs/design/ux_product_brief.md`, `docs/design/screen_job_matrix.md`, and
  `docs/design/component_state_matrix.md` exist and explain the UX foundation in English.
- `/sandbox/components` shows state coverage for normal, long-text, loading, empty, locked, partial,
  stale, read-only, evidence-insufficient, unavailable, and failed generation states.
- `/diagnosis` locked/running/failed states use shared product-state shells and the complete route
  still uses the benchmark Diagnosis composition.
- `/hypothesis` reads as one diagnostic-test workstation: proposed test, why it matters, success
  criteria, trade-off, and action console.
- `/comparison`, `/verdict`, and `/report` carry compact active diagnostic test context and avoid
  recommendation/winner/trade wording.
- Frontend typecheck, build, API route tests, and smoke tests pass.
- Browser QA records URL/port, route, sample/demo/real mode, browser state reset, screenshots, and
  any unverified states.
- `git diff --check` passes and `git status --short` is reviewed.

## Idempotence and Recovery

The document and component changes are additive or localized. Re-running the checks is safe. Do not
run frontend build/dev/test commands concurrently on Windows because `frontend/.next` can race. If a
visual QA server shows missing `.next` chunks or React manifest errors, stop the server, start a fresh
localhost target, and retest before drawing UX conclusions. Do not refresh generated outputs unless a
separate task explicitly targets them.

## Artifacts and Notes

This plan intentionally does not commit, push, change branches, or alter generated output folders.
If a later session continues the plan, update `Progress`, `Surprises & Discoveries`, `Decision Log`,
and `Outcomes & Retrospective` before stopping.

## Interfaces and Dependencies

No new runtime dependency is introduced in this wave. Storybook is deferred. The official isolated UI
workflow for this wave is the existing Next.js sandbox route at `/sandbox/components`. The new shared
component interface is:

    <LockedState title description missing action />
    <PartialEvidenceState title description evidence action />
    <ReadOnlyHistoryState title description action />
    <StaleLineageState title description action />
    <EvidenceInsufficientState title description details action />
    <CandidateUnavailableState title description reasons action />
    <GenerationFailedState title description reasons action />
    <ActiveDiagnosticTestContext testName purpose evidenceQuality candidateName limitation tone />

These components only change presentation. They must not change route unlock logic, backend request
payloads, API envelopes, calculations, or generated artifacts.

Revision note, 2026-06-18: Completed the first implementation wave, synchronized tests and docs, recorded visual QA outputs under generated output/visual_qa_* folders, and left full live vertical QA as a broader follow-up because the requested implementation was validated with static frontend checks, smoke routes, and route-level Playwright screenshots.
