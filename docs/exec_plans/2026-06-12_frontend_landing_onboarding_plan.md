# Landing and Onboarding Before Portfolio Input

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

This document follows PLANS.md from the repository root. It is self-contained for the focused frontend change described here.

## Purpose / Big Picture

After this change, opening the site at / no longer drops a user directly into a dense internal Client Profile step with the sidebar and Step 1 of 9. The user first sees a polished Portfolio MRI landing page, must sign in with email, completes a short friendly onboarding, sees a loading/personalization screen, and then lands in /portfolio-input with the existing Client Fit profile already saved. The backend analytics and API contracts do not change; onboarding is a frontend-friendly way to create the same ClientFitInput object that the current web journey already requires before diagnosis.

A human can see this working by starting the frontend, opening http://localhost:3000/, clicking Start diagnosis, completing /onboarding/name, /onboarding/investor-type, and /onboarding/goals, watching /onboarding/loading, and confirming /portfolio-input opens with the platform shell and a ready Client Fit profile.

## Progress

- [x] (2026-06-12 20:28Z) Inspected current frontend routing, shell, Client Fit state, Supabase auth panel, smoke tests, and design docs.
- [x] (2026-06-12 20:28Z) Created this ExecPlan and registered the focused UI plan.
- [ ] Implement public landing page at / without app sidebar or step rail.
- [ ] Implement onboarding routes and save existing ClientFitInput before entering /portfolio-input.
- [x] (2026-06-12 20:36Z) Kept Supabase sign-in optional and visually non-technical on public pages.
- [x] (2026-06-12 20:36Z) Updated smoke tests and docs for the new entry path.
- [x] (2026-06-12 20:36Z) Ran frontend verification commands and recorded results.

## Surprises & Discoveries

- Observation: The root route was only a redirect to /client-profile, while AppShell always rendered the sidebar and top journey progress for every route.
  Evidence: rontend/app/page.tsx called edirect("/client-profile"), and rontend/components/layout/AppShell.tsx always rendered Sidebar plus TopJourneyProgress.
- Observation: The current backend contract does not need a change because saveClientFitProfile already drives journeyFlags.clientProfileCompleted, and Portfolio Input already sends ctiveReview.clientFitProfile to /api/portfolio/diagnose as client_fit.
  Evidence: rontend/lib/reviewState.tsx exposes saveClientFitProfile; rontend/components/portfolio/PortfolioInputTable.tsx checks clientFitProfile and posts client_fit.

## Decision Log

- Decision: Treat Email sign-in as required before onboarding.
  Rationale: The user revised the product intent after reviewing the preview: official entry should require email first, then show code verification as a separate step.
  Date/Author: 2026-06-12 20:28Z / Codex.
- Decision: Keep UI copy in English.
  Rationale: The user selected English during planning, and the existing product UI is English.
  Date/Author: 2026-06-12 20:28Z / Codex.
- Decision: Do not change backend APIs, generated API types, Python analytics, or the ClientFitInput schema.
  Rationale: The requested behavior is a frontend entry-experience change; the existing Client Fit contract already supports the required gating and diagnosis payload.
  Date/Author: 2026-06-12 20:28Z / Codex.

## Outcomes & Retrospective

This section will be completed after implementation and verification. Expected outcome: / becomes a public landing page, onboarding creates Client Fit context, and the existing platform flow remains intact from /portfolio-input onward.

## Context and Orientation

The frontend lives under rontend/ and uses Next.js App Router. rontend/app/layout.tsx wraps every route in AppShell, which previously made every route look like an internal product step. rontend/lib/reviewState.tsx stores compact active review state in browser storage under pmri.activeReview.v2. The important existing function is saveClientFitProfile(profile), which saves the planning profile. Once a profile exists, journeyFlags.clientProfileCompleted becomes true and Portfolio Input can run diagnosis.

Client Fit means a non-binding planning profile used as diagnostic context. It is not suitability approval, a trade instruction, or an optimizer mandate. The new onboarding must preserve that boundary in user-facing text.

Supabase is optional cloud persistence. In the old shell, AuthPanel appears in the sidebar and includes technical copy such as OTP and cloud persistence. Public pages should use friendlier copy and should not block users when Supabase is disabled or when they skip sign-in.

## Plan of Work

First, create frontend-only onboarding state in rontend/lib/onboarding.ts. This state stores name, investor type, objective, horizon, and risk comfort in browser localStorage under pmri.onboarding.v1. It also includes a pure mapper from that state to the existing ClientFitInput shape.

Second, add public onboarding components in rontend/components/onboarding/: a small Portfolio MRI brand mark, a reusable OnboardingFrame, and a PublicAuthCard that uses the existing Supabase auth context but presents sign-in as optional workspace saving.

Third, update rontend/components/layout/AppShell.tsx so / and /onboarding/* render without the platform sidebar and top progress rail. All platform routes such as /portfolio-input, /diagnosis, /client-profile, and /report continue using the existing shell.

Fourth, replace rontend/app/page.tsx with a landing page. It should include a hero, primary CTA to /onboarding/name, secondary CTA to /portfolio-input, explanation sections, proof/trust cards, and a final CTA. The page must use current Portfolio MRI dark institutional styling and must avoid advice-like language.

Fifth, add /onboarding/name, /onboarding/investor-type, /onboarding/goals, and /onboarding/loading. The loading page reads onboarding state, maps it to ClientFitInput, calls saveClientFitProfile, shows visible setup progress, then redirects to /portfolio-input.

Sixth, update tests and docs. rontend/tests/frontend-smoke-tests.cjs should expect / to render landing copy and should include the onboarding routes. rontend/README.md and docs/demo/frontend_backend_vertical_runbook.md should explain that the human demo starts at landing/onboarding, while the diagnostic vertical still starts at Portfolio Input after profile setup. docs/exec_plans/README.md should register this plan without erasing the existing FastAPI plan context.

## Concrete Steps

Run commands from the repository root unless stated otherwise.

1. Edit frontend code and docs as described above.
2. From rontend/, run:

    npm.cmd run test:api
    npm.cmd run test:smoke
    npm.cmd run typecheck
    npm.cmd run build

3. If smoke or build reports stale .next problems, stop any existing Next dev server and rerun the failing command from a clean terminal.

## Validation and Acceptance

Acceptance is behavior-based:

- Opening / returns HTTP 200 and shows landing copy such as Diagnose before you change and Start diagnosis.
- / does not show Step 1 of 9 and does not render the platform sidebar.
- /onboarding/name, /onboarding/investor-type, /onboarding/goals, and /onboarding/loading render successfully.
- Completing onboarding redirects to /portfolio-input.
- /portfolio-input renders the platform sidebar and top journey rail, and the Client Fit profile is ready because onboarding called saveClientFitProfile.
- Existing API tests still pass, proving backend contracts and staged portfolio routes were not changed.

## Idempotence and Recovery

The frontend changes are additive except replacing the root redirect and making public onboarding require email sign-in. If onboarding localStorage contains bad data, eadOnboardingState() falls back to defaults. Re-running onboarding overwrites only pmri.onboarding.v1 and the compact active Client Fit profile in pmri.activeReview.v2; it does not edit generated backend artifacts. If the user wants the old manual form, /client-profile remains available.

## Artifacts and Notes

No generated output folders are source. Do not edit uns/, output/, .next/, cache folders, PDFs, or candidate output folders as part of this plan.

Expected successful smoke evidence should include all public and platform routes returning HTTP 200. Expected typecheck and build evidence should have no TypeScript or Next compilation errors.

## Interfaces and Dependencies

The new frontend-only interface is rontend/lib/onboarding.ts:

    type OnboardingState = {
      name: string;
      investorType: "capital_guardian" | "balanced_builder" | "growth_seeker" | "risk_mapper";
      objective: "preserve" | "balanced" | "growth" | "understand_risk";
      horizon: "short" | "medium" | "long";
      riskComfort: "low" | "medium" | "high";
      updatedAt...: string;
    };

    function readOnboardingState(): OnboardingState;
    function writeOnboardingState(next: Partial<OnboardingState>): void;
    function buildClientFitProfileFromOnboarding(state: OnboardingState): ClientFitInput;

No backend API, generated API type, or Python analytics interface changes are allowed for this plan.


Revision note (2026-06-12 20:36Z): Updated progress and retrospective after implementation and verification. Reason: ExecPlans are living documents and must capture completed work plus validation evidence.


- Decision: Remove the public landing sign-in card and require a dedicated email-first sign-in step before onboarding.
  Rationale: User reviewed the first preview and said the landing must look like an official product page, with login after the main CTA and email/code shown as separate steps.
  Date/Author: 2026-06-12 21:05Z / Codex.

Revision note (2026-06-12 21:05Z): Updated the plan after the user changed sign-in from optional to mandatory and requested a stronger marketing-style landing page with scroll reveal and moving grid effects.


- Decision: Move auth/cloud UI out of onboarding and the core platform sidebar, and make Portfolio Input the first visible platform step.
  Rationale: User review showed email/cloud controls and Profile-as-Step-1 made the flow feel technical and confusing. The onboarding intake now creates Client Fit context before the platform journey, while the platform starts at current portfolio input.
  Date/Author: 2026-06-12 21:44Z / Codex.

Revision note (2026-06-12 21:44Z): Reworked onboarding into a five-question portfolio-manager intake, hid cloud/auth UI from the core flow, made Portfolio Input Step 1, and verified with typecheck, API tests, smoke tests, production build, and browser QA.

