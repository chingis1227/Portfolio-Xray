# Diagnosis premium visual reset

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root.

## Purpose / Big Picture

The goal is to make the `/diagnosis` screen feel like a premium institutional portfolio case file instead of a dark dashboard wall. A user should be able to open Portfolio Diagnosis and understand the main diagnosis, the four evidence facts behind it, the next risk area to review, and the primary next click within the first viewport. The work is visual and structural only: backend calculations, review state, API contracts, Supabase persistence, candidate generation, and runtime flow must remain unchanged.

## Progress

- [x] (2026-06-18 08:58Z) Read repository operating rules, workflow, design sources, QA contract, frontend design skill, Playwright skill, and the current diagnosis/shell implementation.
- [x] (2026-06-18 08:58Z) Reviewed Fey.com as public visual inspiration only, with no use of its assets, logo, brand, screenshots, fonts, or proprietary visuals.
- [x] (2026-06-18 09:18Z) Refactored shell background, top utility header, sidebar styling, shared presentation components, and the Diagnosis screen hierarchy.
- [x] (2026-06-18 09:18Z) Updated design documentation for the new Diagnosis-first premium workspace structure.
- [x] (2026-06-18 09:36Z) Ran frontend verification and browser visual QA for `/diagnosis`.
- [ ] Complete diff review and final reporting.

## Surprises & Discoveries

- Observation: The active design documents already describe parts of a recent Diagnosis benchmark-screen direction, but the current implementation still renders a prominent evidence card and visible MetricMatrix before advanced disclosure.
  Evidence: `DESIGN.md` and `docs/design/current_website_structure.md` mention a compact evidence summary and primary diagnostic canvas, while `frontend/components/diagnosis/DiagnosisSummaryPanel.tsx` still renders `EvidenceSummary` with title `Why this diagnosis is showing` and a visible `MetricMatrix`.

- Observation: `npm.cmd run test:api` initially failed because the site explanation presenter returned the raw label `Available` where the API-route contract expects `Evidence available`.
  Evidence: The first run failed `site explanation presenter strips raw provenance from the public display model`; after restoring evidence-specific labels in `frontend/lib/siteExplanationPresenter.ts`, `npm.cmd run test:api` passed with 91 tests.

## Decision Log

- Decision: Treat this as a focused visual structure refactor, not a product-flow, data-contract, or backend change.
  Rationale: The request explicitly excludes backend calculations, JSON contracts, review state logic, API behavior, Supabase persistence, candidate generation, and runtime flow.
  Date/Author: 2026-06-18, Codex.

- Decision: Use Fey.com only for abstract visual principles: cinematic dark workspace, floating glass panels, restrained hierarchy, and low-noise spacing.
  Rationale: The user explicitly forbids copying Fey assets, brand, exact UI, fonts, screenshots, or proprietary visuals. Portfolio MRI must remain its own institutional diagnostic product.
  Date/Author: 2026-06-18, Codex.

## Outcomes & Retrospective

Implemented the Diagnosis visual reset as a frontend-only structure and styling change. `/diagnosis` now opens with a compact metadata-led header, a controlled diagnosis statement hero, one four-item evidence strip, and a two-column diagnostic canvas before any advanced metric table. MetricMatrix, professional metrics, evidence-chain notes, and full X-Ray detail are collapsed under `Advanced diagnostics and technical evidence`. Backend calculations, API contracts, review-state flow, Supabase persistence, and candidate generation were not changed.

Validation completed with `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:api`, `npm.cmd run test:smoke`, forbidden-term scans with manual review of expected code/test/onboarding matches, and a Playwright visual QA pass at `http://127.0.0.1:3137/diagnosis` using an injected completed-review fixture. Screenshot: `output/playwright/diagnosis_visual_reset_3137/diagnosis-visual-reset-1440x1000.png`.

## Context and Orientation

The frontend is a Next.js application in `frontend/`. Platform routes are wrapped by `frontend/components/layout/AppShell.tsx`, which renders `Sidebar`, `PlatformTopHeader`, and a constrained content area. `/diagnosis` renders `frontend/components/diagnosis/DiagnosisScreen.tsx`, which builds a diagnosis object from active review state and passes it to `frontend/components/diagnosis/DiagnosisSummaryPanel.tsx`. Shared visual components include `frontend/components/ui/VerdictHero.tsx`, `frontend/components/ui/EvidenceSummary.tsx`, and `frontend/components/ui/MetricMatrix.tsx`.

The current product flow is current-portfolio-first. Diagnosis must explain the current portfolio before Stress Lab, Client Fit, Hypothesis, Comparison, Verdict, and Report. Candidate tests are diagnostic tests, not trade recommendations.

## Plan of Work

First, update the platform shell so the background is a deeper cinematic black workspace, the top header is compact and metadata-led instead of badge-heavy, and the left rail is quieter while preserving all route steps and gating behavior.

Second, update shared presentation components so the diagnosis hero reads as a compact statement, evidence renders as one glass strip with no repeated generic badges, and metrics can be placed behind advanced disclosure without looking like the first product answer.

Third, restructure `DiagnosisSummaryPanel` so the first viewport order is hero, four-item evidence strip, and one two-column diagnostic canvas. The canvas must show what is driving the diagnosis on the left and where to review next on the right. MetricMatrix, professional metrics, full X-Ray detail, and technical evidence must be below the fold or collapsed.

Fourth, update `DESIGN.md`, `docs/design/current_website_structure.md`, and `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` to document the enforceable design changes. If the completed change is meaningful enough for project memory, update `CHANGELOG.md` only with a concise summary.

## Concrete Steps

Work from the repository root unless a command explicitly changes directory.

Use non-destructive edits only. Do not edit generated folders such as `frontend/.next`, `runs/`, `output/`, or cache folders.

Run frontend checks from `frontend/` after implementation:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

For browser QA, start a fresh local target and capture a screenshot under `output/playwright/`. Record URL, port, route, sample or real-data status, browser state reset, and any unverified state.

## Validation and Acceptance

Acceptance requires `/diagnosis` to show the compact hero, four-item evidence strip, and primary diagnostic canvas in the first viewport, without a visible card wall or Excel-like table before the diagnosis is understood. The sidebar must still show Workspace plus the full product journey: Portfolio, Diagnosis, Stress Lab, Client Fit, Hypothesis, Comparison, Verdict, and Report. The top header must not show noisy review-status or evidence-quality pills; status and evidence quality belong in quieter metadata or the evidence strip.

The standard frontend checks must pass, or any failure must be reported with the exact command and blocker. Visual QA must inspect `/diagnosis` on a fresh local server and capture a screenshot unless blocked.

## Idempotence and Recovery

The work is limited to frontend source and documentation. It is safe to rerun typecheck, build, smoke tests, and visual QA. If a visual change breaks a shared component, restore the previous prop shape or add an optional variant instead of rewriting route behavior. Do not use destructive git commands and do not revert unrelated user changes.

## Artifacts and Notes

Initial inspection found relevant source files:

    frontend/components/layout/AppShell.tsx
    frontend/components/layout/PlatformTopHeader.tsx
    frontend/components/layout/Sidebar.tsx
    frontend/components/diagnosis/DiagnosisSummaryPanel.tsx
    frontend/components/ui/VerdictHero.tsx
    frontend/components/ui/EvidenceSummary.tsx
    frontend/components/ui/MetricMatrix.tsx
    frontend/styles/globals.css
    frontend/tailwind.config.ts

## Interfaces and Dependencies

Use the existing React, Next.js, Tailwind, and Framer Motion dependencies only. Do not add a new UI framework, charting library, CSS-in-JS layer, or external design asset. Keep route links and review state hooks unchanged.
