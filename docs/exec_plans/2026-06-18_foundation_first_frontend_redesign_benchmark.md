# Foundation-first frontend redesign benchmark

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. This plan follows `PLANS.md` from the repository root.

## Purpose / Big Picture

This work gives Portfolio MRI a scalable frontend design foundation before additional screens are redesigned. A user should experience `/diagnosis` as a calm premium dark Investment Decision Room screen that answers the main diagnosis, evidence, next risk review, and next safe action before technical metrics appear. A developer should be able to preview shared UI primitives at `/sandbox/components` without changing backend behavior.

## Progress

- [x] (2026-06-18) Created branch `codex/design-system-diagnosis-benchmark`.
- [x] (2026-06-18) Read `RULES.md`, `WORKFLOW.md`, `DESIGN.md`, `PLANS.md`, `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`, `docs/contracts/SCREEN_CONTRACTS.md`, and `docs/design/current_website_structure.md`.
- [x] (2026-06-18) Audited frontend structure and identified repeated page-local button, card, badge, state, and disclosure styling.
- [x] (2026-06-18) Added reusable primitives under `frontend/components/ui/`.
- [x] (2026-06-18) Split diagnosis benchmark product blocks into `frontend/components/diagnosis/`.
- [x] (2026-06-18) Added `/sandbox/components` for foundation preview.
- [x] (2026-06-18) Rebuilt `/diagnosis` composition through product components while preserving review state and route gating.
- [x] (2026-06-18) Updated design and screen documentation.
- [x] (2026-06-18) Ran build and browser visual QA on fresh localhost port 3137.

## Surprises & Discoveries

- Observation: the repository already had a near-benchmark diagnosis shape in `DiagnosisSummaryPanel.tsx`, but the product blocks were local to the file rather than reusable product components.
  Evidence: `DiagnosisHero`, primary canvas, and advanced disclosure logic existed inside `frontend/components/diagnosis/DiagnosisSummaryPanel.tsx` before this change.
- Observation: Windows PowerShell blocks `npm.ps1` in this environment.
  Evidence: `npm run typecheck` failed with `PSSecurityException`; `npm.cmd run typecheck` passed.

## Decision Log

- Decision: keep backend, review-state, journey gating, and API calls unchanged.
  Rationale: the user explicitly scoped this to frontend design architecture and `/diagnosis` presentation.
  Date/Author: 2026-06-18 / Codex.
- Decision: add primitives in `frontend/components/ui/` and product-specific diagnosis blocks in `frontend/components/diagnosis/`.
  Rationale: primitives should update the product consistently, while diagnosis blocks represent Portfolio MRI-specific value and should not become generic dashboard widgets.
  Date/Author: 2026-06-18 / Codex.
- Decision: use `/sandbox/components` as the first gallery route.
  Rationale: it allows local design iteration without calling backend review APIs or altering production routes.
  Date/Author: 2026-06-18 / Codex.

## Outcomes & Retrospective

At this milestone, the reusable UI foundation exists, `/diagnosis` is composed from product blocks, and documentation captures the foundation-first workflow. Final acceptance still requires build and browser visual QA.

## Context and Orientation

The frontend is a Next.js app under `frontend/`. Production routes live in `frontend/app/`. Shared UI components live in `frontend/components/ui/`. Product-specific diagnosis components live in `frontend/components/diagnosis/`. The `/diagnosis` route renders `frontend/components/diagnosis/DiagnosisScreen.tsx`, which keeps review recovery and route gating logic and delegates the ready state to `DiagnosisSummaryPanel`.

## Plan of Work

First, preserve the current product journey and backend contracts. Add reusable primitives for buttons, surfaces, section headers, evidence items, advanced disclosure, and product-facing empty/loading/error states. Next, move diagnosis-specific hero, evidence strip, diagnostic canvas, and advanced metrics disclosure into separate product components. Then add `/sandbox/components` to preview the foundation. Finally, update design documentation and validate with typecheck, build, and browser QA.

## Concrete Steps

Run commands from `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА\frontend` unless otherwise stated.

- Typecheck: `npm.cmd run typecheck`.
- Build: `npm.cmd run build`.
- Local visual QA: start a fresh dev server on an unused port and inspect `/sandbox/components` and `/diagnosis`.

## Validation and Acceptance

Acceptance is met when `npm.cmd run typecheck` and `npm.cmd run build` pass, `/sandbox/components` renders the primitive gallery, and `/diagnosis` first viewport shows the top utility header, controlled diagnosis hero, four-item evidence strip, primary diagnostic canvas, and clear Stress Lab action before advanced metrics.

## Idempotence and Recovery

The changes are additive or local refactors. If a component import fails, run typecheck, restore the previous import from git, and reapply the primitive composition one file at a time. No generated outputs, backend artifacts, or persisted review data need to be modified.

## Artifacts and Notes

Relevant files added or changed include `frontend/components/ui/*`, `frontend/components/diagnosis/*`, `frontend/app/sandbox/components/page.tsx`, `frontend/styles/globals.css`, `DESIGN.md`, `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`, `docs/contracts/SCREEN_CONTRACTS.md`, `docs/design/current_website_structure.md`, and `frontend/README.md`.

## Interfaces and Dependencies

Use existing React, Next.js, Tailwind, and Framer Motion dependencies already present in the frontend. Do not add a new UI package. Primitives export React components with stable names: `Button`, `ButtonLink`, `Surface`, `Card`, `GlassPanel`, `SectionHeader`, `EvidenceItem`, `AdvancedDisclosure`, `EmptyState`, `LoadingState`, and `ErrorState`.


Update note (2026-06-18): Marked validation complete after typecheck, build, and Playwright visual QA confirmed the sandbox and Diagnosis benchmark rendered as intended.
