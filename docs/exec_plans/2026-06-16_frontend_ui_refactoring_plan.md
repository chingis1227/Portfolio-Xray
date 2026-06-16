# Refactor frontend route styling into components

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is self-contained for the current UI refactoring task.

## Purpose / Big Picture

The goal is to make Portfolio MRI route files read like product composition rather than visual styling scripts. After this change, route files under `frontend/app/**/page.tsx` should mostly import and render reusable screen or stage components, while visual styling such as card surfaces, typography, badges, buttons, borders, and state colors lives inside components under `frontend/components/`.

The user-visible behavior must remain the same. A reviewer can see the work by comparing the route files before and after the refactor and by running `npm.cmd run typecheck` from `frontend/`. The route chain, copy, CTAs, local storage behavior, API calls, and review lineage must not change.

## Progress

- [x] (2026-06-16 20:47Z) Read the explicit `ui-refactoring` skill and repository rules in `WORKFLOW.md`, `RULES.md`, `PLANS.md`, `DESIGN.md`, `TESTING.md`, `frontend/README.md`, `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`, and `docs/contracts/SCREEN_CONTRACTS.md`.
- [x] (2026-06-16 20:47Z) Inspected frontend route and component inventory under `frontend/app` and `frontend/components`.
- [x] (2026-06-16 21:05Z) Refactored public landing and onboarding routes so their visual surfaces live in `frontend/components/landing/` and `frontend/components/onboarding/`, leaving the route files as thin composition wrappers.
- [x] (2026-06-16 21:05Z) Ran the narrowest validation for the public/onboarding block from `frontend/`.
- [x] (2026-06-16 21:13Z) Refactored the first platform block: `portfolio-input`, `diagnosis`, `evidence`, `client-fit`, and `client-profile` route styling now lives in stage screen components.
- [x] (2026-06-16 21:13Z) Ran focused validation after the first platform block.
- [x] (2026-06-16 21:18Z) Refactored downstream decision routes `comparison`, `verdict`, and `report` into screen components.
- [x] (2026-06-16 21:18Z) Ran focused validation after the downstream decision block.
- [x] (2026-06-16 21:21Z) Refactored the `hypothesis` route into `frontend/components/hypothesis/HypothesisScreen.tsx`.
- [x] (2026-06-16 21:21Z) Ran focused validation after the `hypothesis` route extraction.
- [x] (2026-06-16 21:24Z) Refactored the remaining `workspace` route into `frontend/components/workspace/WorkspaceScreen.tsx`.
- [x] (2026-06-16 21:24Z) Ran focused validation after the remaining platform route extraction.
- [x] (2026-06-16 21:28Z) Removed cosmetic style override props where safely possible: `StatusBadge` no longer accepts `className`, `BrandMark` uses semantic `size`, `Reveal` uses semantic `layout`, and workspace `CardShell` no longer accepts local class overrides.
- [x] (2026-06-16 21:30Z) Ran final validation and started diff review for generated files, unrelated user changes, and stale page-level styling.

## Surprises & Discoveries

- Observation: The working tree already contained unrelated modified documentation files and untracked documentation before this UI task started.
  Evidence: `git status --short` showed modified `OUTPUTS.md`, `PRODUCT.md`, `README.md`, `SPEC.md`, `TESTING.md`, `WORKFLOW.md`, `docs/contracts/DOC_SYNC_CONTRACT.md`, `docs/exec_plans/README.md`, plus untracked archive/plan docs.

- Observation: `BrandMark` and `Reveal` accepted direct `className` overrides from landing/onboarding callers.
  Evidence: Searches for `BrandMark className` and `<Reveal ... className` found callers in `LandingPage`, `Sidebar`, `OnboardingFrame`, sign-in, and loading components before the refactor.

## Decision Log

- Decision: Treat this refactor as route/component ownership cleanup, not as a visual redesign.
  Rationale: The request asks to preserve behavior and move styling ownership; `DESIGN.md` already defines the current visual system and no token or product-flow change is requested.
  Date/Author: 2026-06-16, Codex.

- Decision: Prefer extracting route-level screen components into existing `frontend/components/<stage>/` folders before introducing new visual primitives.
  Rationale: The existing repository convention already has stage folders such as `diagnosis`, `evidence`, `hypothesis`, `comparison`, `verdict`, and `report`. Moving page-owned styled JSX there removes cosmetic page overrides while preserving the route contracts.
  Date/Author: 2026-06-16, Codex.

- Decision: Use `npm.cmd run typecheck` as the minimum repeated validation gate.
  Rationale: This refactor changes TypeScript/React component boundaries without changing backend APIs or formulas. Typecheck is the narrowest reliable check for import/export and prop-shape regressions; broader browser QA is reserved for intentional visual redesign or behavior changes.
  Date/Author: 2026-06-16, Codex.

- Decision: Replace `BrandMark` sizing `className` with a semantic `size` prop and replace `Reveal` layout `className` with a semantic `layout` prop.
  Rationale: This removes cosmetic pass-throughs from callers while preserving the existing landing/onboarding appearance.
  Date/Author: 2026-06-16, Codex.

## Outcomes & Retrospective

This section will be completed after the refactor milestones and validation are done.

Milestone outcome: Route files under `frontend/app/**/page.tsx` are now composition wrappers. All former route-local visual JSX for landing, onboarding, workspace, diagnosis, stress lab, Client Fit, hypothesis, comparison, verdict, and report lives under `frontend/components/**`. The only remaining `className` under `frontend/app` is the root `frontend/app/layout.tsx` font-variable wiring on `<html>`, which is framework setup rather than component skinning.

The work did not intentionally change product flow, backend calls, local storage keys, API contracts, or screen copy beyond fixing transferred mojibake where touched.

## Context and Orientation

The frontend is a Next.js application in `frontend/`. Routes live under `frontend/app/**/page.tsx`. Reusable visual and product-stage components live under `frontend/components/`. The design system uses Tailwind utility classes and Portfolio MRI CSS helpers such as `pmri-card`, `pmri-primary-action`, `pmri-focus`, and token names like `pmri-text`.

For this plan, "route file" means a `page.tsx` file that Next.js uses as a URL entrypoint. "Component-owned styling" means the route file does not assemble a component's final visual appearance with cosmetic `className`, inline `style`, or utility-class strings. A route may still compose layout by choosing which components appear and in what order, but the component itself should own its surface, typography, button skin, badge skin, borders, and colors.

The canonical current product route chain is `/`, `/onboarding/sign-in`, `/onboarding/name`, `/onboarding/investor-type`, `/onboarding/loading`, `/portfolio-input`, `/diagnosis`, `/evidence`, `/client-fit`, `/hypothesis`, `/comparison`, `/verdict`, and `/report`. `/workspace` is an account home and `/client-profile` is the advanced/manual Client Fit editor.

## Plan of Work

First, move styled public landing and onboarding screen code into components under `frontend/components/landing/` and `frontend/components/onboarding/`. Keep route files as thin exports that render those components.

Second, move styled platform page code into stage folders under `frontend/components/`. For example, `frontend/app/comparison/page.tsx` should delegate to a `ComparisonScreen` component in `frontend/components/comparison/`, and `frontend/app/verdict/page.tsx` should delegate to a `VerdictScreen` component in `frontend/components/verdict/`.

Third, review shared primitive APIs for cosmetic override props. When a prop only exists to pass CSS from callers, replace it with semantic props such as `size`, `tone`, or component variants, or remove it when unused.

At each milestone, run `npm.cmd run typecheck` from `frontend/` and fix any type errors before moving on.

## Concrete Steps

Work from the repository root unless a command explicitly changes directory.

Use these commands during implementation:

    cd frontend
    npm.cmd run typecheck

A successful typecheck exits with code 0 and prints no TypeScript errors. If it fails, fix the import, export, prop, or JSX issue before continuing.

## Validation and Acceptance

Acceptance criteria:

Route files under `frontend/app/**/page.tsx` no longer contain page-owned cosmetic class utility blocks except for unavoidable Next.js root layout/font wiring. Stage screens and reusable components under `frontend/components/` own the visual styling.

The commands below pass from `frontend/`:

    npm.cmd run typecheck

If time and scope permit, run one final `npm.cmd run test:smoke` after the route extraction to confirm basic frontend route expectations still pass.

## Idempotence and Recovery

The refactor is file-structure and import based. It is safe to rerun `npm.cmd run typecheck` repeatedly. If an extraction creates a bad import, restore by moving the component code back or correcting the import path. Do not use destructive git commands. Do not edit generated folders such as `frontend/.next`, `runs/`, `output/`, or cache directories.

Existing unrelated dirty documentation files must be left untouched. Only files required for this UI refactor and this ExecPlan should be changed by this task.

## Artifacts and Notes

Initial inspection commands:

    git status --short
    rg --files frontend/app frontend/components
    rg -n "className=|style=|cn\\(|clsx\\(|twMerge|classNames" frontend/app frontend/components -g "*.tsx" -g "*.ts"

The search found many styled route files, with especially large route-local JSX in `frontend/app/hypothesis/page.tsx`, `frontend/app/verdict/page.tsx`, `frontend/app/comparison/page.tsx`, `frontend/app/report/page.tsx`, and `frontend/app/workspace/page.tsx`.

Public/onboarding validation transcript:

    cd frontend
    npm.cmd run typecheck
    > portfolio-mri-frontend@0.1.0 typecheck
    > tsc --noEmit

First platform block validation transcript:

    cd frontend
    npm.cmd run typecheck
    > portfolio-mri-frontend@0.1.0 typecheck
    > tsc --noEmit

Downstream decision block validation transcript:

    cd frontend
    npm.cmd run typecheck
    > portfolio-mri-frontend@0.1.0 typecheck
    > tsc --noEmit

Hypothesis block validation transcript:

    cd frontend
    npm.cmd run typecheck
    > portfolio-mri-frontend@0.1.0 typecheck
    > tsc --noEmit

Workspace block validation transcript:

    cd frontend
    npm.cmd run typecheck
    > portfolio-mri-frontend@0.1.0 typecheck
    > tsc --noEmit

Primitive cleanup validation transcript:

    cd frontend
    npm.cmd run typecheck
    > portfolio-mri-frontend@0.1.0 typecheck
    > tsc --noEmit

Final smoke validation transcript:

    cd frontend
    npm.cmd run test:smoke
    ✔ frontend static journey pages respond on a local Next server
    tests 1
    pass 1

## Interfaces and Dependencies

Use existing React and Next.js dependencies only. Do not add a CSS-in-JS library or a new component framework. Keep imports based on the configured `@/` alias already used in the frontend.

Screen components should export named React functions such as `LandingPage`, `SignInPage`, `ComparisonScreen`, `VerdictScreen`, and `WorkspaceScreen`. Page files should import the matching component and return it from the default Next.js page export.

Revision note, 2026-06-16: Updated this plan after implementation to record route extractions, primitive API cleanup, validation transcripts, and the final milestone outcome. The reason is that ExecPlans in this repository are living documents and must preserve what changed, why it changed, and how it was verified.
