# Implement Diagnostic Case File UX

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root.

## Purpose / Big Picture

After this change, Portfolio MRI platform screens read like a diagnosis-first case file. A private investor sees the investment conclusion, why it matters, key evidence, and the next safe decision before seeing technical metric detail. The implementation can be seen by opening the platform routes `/portfolio-input`, `/diagnosis`, `/evidence`, `/client-fit`, `/hypothesis`, `/comparison`, `/verdict`, and `/report` and confirming that the first viewport no longer behaves like a generic metric dashboard or optimizer cockpit.

## Progress

- [x] (2026-06-18) Read repository rules, workflow, documentation-sync contract, design system, screen contracts, frontend screen contracts, and presentation-language rules.
- [x] (2026-06-18) Used the brainstorming process to compare three approaches and received user approval for the Diagnostic Case File pass.
- [x] (2026-06-18) Wrote the approved UX spec at `docs/superpowers/specs/2026-06-18-diagnostic-case-file-ux-design.md`.
- [x] (2026-06-18) Wrote the implementation plan at `docs/superpowers/plans/2026-06-18-diagnostic-case-file-ux-implementation-plan.md`.
- [x] (2026-06-18) Updated frontend shared presentation helpers and route components.
- [x] (2026-06-18) Updated owning documentation and changelog.
- [x] (2026-06-18) Ran typecheck, targeted language scan, and diff checks. Lint was blocked by interactive ESLint setup. Visual QA was blocked by existing concurrent Next dev servers using the same `.next` directory.

## Surprises & Discoveries

- Observation: The working tree already had uncommitted changes in `DESIGN.md`, several frontend shell/onboarding files, `frontend/components/portfolio/PortfolioInputTable.tsx`, and `frontend/styles/globals.css` before this implementation began.
  Evidence: `git status --short` showed those files as modified before this plan was created.

## Decision Log

- Decision: Implement the approved Option 1 Diagnostic Case File pass without backend schema or formula changes.
  Rationale: The user selected this path and it matches the current product boundary: diagnosis-first, current-portfolio-first, and non-binding decision support.
  Date/Author: 2026-06-18 / Codex.

- Decision: Keep `/hypothesis` as one route but split its visible content into Problem Classification, Candidate Launchpad, Alternatives Builder, and Candidate Generation Result.
  Rationale: A route split would be larger and riskier; the product contract already allows `/hypothesis` to own the merged MVP handoff.
  Date/Author: 2026-06-18 / Codex.

- Decision: Do not commit during this session unless explicitly asked.
  Rationale: Repository workflow says commits happen only when requested, even though the brainstorming skill normally asks for committing the spec.
  Date/Author: 2026-06-18 / Codex.

## Outcomes & Retrospective

This section will be updated after implementation and verification. Expected outcome: route first-read hierarchy and docs match the Diagnostic Case File UX spec, with any visual QA gaps reported explicitly.

- 2026-06-18: Frontend code and documentation have been updated. Verification remains in progress.
- 2026-06-18: TypeScript verification passed. Lint and visual QA need a clean frontend environment before they can be completed without changing project config or colliding with active dev servers.

## Context and Orientation

Portfolio MRI is a Next.js/React frontend in `frontend/` backed by Python APIs. Platform route components live under `frontend/components/` and route files under `frontend/app/`. Current product truth says the app is diagnosis-first and current-portfolio-first, not optimizer-first. Client Fit is diagnostic context only. A diagnostic candidate is a test candidate, not a recommendation.

The relevant docs are `DESIGN.md`, `docs/design/current_website_structure.md`, `docs/contracts/SCREEN_CONTRACTS.md`, `docs/specs/frontend_screen_contracts.md`, `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`, and `docs/contracts/DOC_SYNC_CONTRACT.md`. The new UX spec for this session is `docs/superpowers/specs/2026-06-18-diagnostic-case-file-ux-design.md`.

## Plan of Work

First, adjust shared wording where needed so top-level evidence and metric sections speak in investor-facing terms. Then edit each route component to lead with the approved case-file structure. Keep all backend calls, review-state gates, and data calculations unchanged. Finally, update route documentation and run frontend checks plus visual QA.

## Concrete Steps

From repository root `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`:

1. Edit shared components and route components with scoped patches.
2. Update docs listed in the plan.
3. Run frontend checks from `frontend`:

    npm run lint
    npm run typecheck

4. Run forbidden-language scans from repo root over `frontend/app` and `frontend/components` using patterns from `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`.
5. Start a fresh frontend server if possible and inspect changed routes at desktop and mobile widths.
6. Run:

    git diff --check
    git status --short

## Validation and Acceptance

Acceptance is user-visible. Each changed route should place the investment conclusion or route-specific next answer before dense metric detail. Top-layer metrics must carry investor meaning. Candidate language must show both investment hypothesis and mathematical method. Verdict wording must not say trade now, best portfolio, recommended portfolio, suitability approved, safe, or guaranteed improvement. Documentation must describe the same route order as the code.

## Idempotence and Recovery

The edits are source-only and can be repeated safely. No generated outputs are intentionally refreshed. If a local dev server or visual QA fails because of environment or pre-existing dirty files, record the blocker and keep code/docs changes reviewable through lint/typecheck and screenshots attempted.

## Artifacts and Notes

Created docs:

- `docs/superpowers/specs/2026-06-18-diagnostic-case-file-ux-design.md`
- `docs/superpowers/plans/2026-06-18-diagnostic-case-file-ux-implementation-plan.md`
- `docs/exec_plans/2026-06-18-diagnostic-case-file-ux.md`

## Interfaces and Dependencies

Use existing React components and TypeScript types. Do not add dependencies. Do not modify FastAPI routes, backend artifacts, formulas, or generated run folders. Use existing `useReviewState` data and existing route gates.
