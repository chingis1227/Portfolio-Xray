# Public Presentation Boundary for Evidence Provenance

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. It is intentionally self-contained so a
future contributor can continue the work without prior chat context.

## Purpose / Big Picture

Portfolio MRI keeps exact backend evidence references so diagnosis text can be audited. Those
references include generated artifact names such as `portfolio_xray.json`, schema versions, and
field paths. The current UI accidentally shows that machine trace to ordinary users, making the
site look like a backend console instead of a client-ready product.

After this plan is implemented, public screens show only product-language evidence labels such as
`Evidence available` or `Limited evidence`. The raw evidence trace remains available in data for
audit and QA, but it is not rendered by default. Session 1 creates the public presenter boundary and
then stops; later sessions add opt-in developer provenance and harden the contracts.

## Progress

- [x] (2026-06-14) Created this ExecPlan at
  `docs/exec_plans/public_presentation_boundary_for_evidence_provenance.md`.
- [x] (2026-06-14) Session 1: Added the public presenter for site explanation bundles in
  `frontend/lib/siteExplanationPresenter.ts`.
- [x] (2026-06-14) Session 1: Made `SiteExplanationHierarchy` render the public display model instead of raw
  backend bundle fields.
- [x] (2026-06-14) Session 1: Added focused presenter/component tests and public route leak checks.
- [x] (2026-06-14) Session 1: Ran typecheck, frontend smoke/API tests, `git diff --check`, and targeted scans.
- [x] (2026-06-14) Session 1 stop point reached: report exactly
  `да — Session 1 завершена по плану Public Presentation Boundary for Evidence Provenance`.
- [x] (2026-06-14) Session 2: Added opt-in developer provenance display behind
  `showDeveloperProvenance`, off by default for public journey pages.
- [x] (2026-06-14) Session 2: Extended `buildPublicSiteExplanationDisplayModel` with an explicit
  `includeDeveloperProvenance` option that preserves schema, review id, warnings, and source refs
  only for debug display.
- [x] (2026-06-14) Session 3: Updated the site explanation spec and presentation/screen/artifact
  contracts to document the public presentation boundary and opt-in debug provenance rule.
- [x] (2026-06-14) Session 3: Added regression tests proving public display omits raw provenance,
  developer provenance requires an explicit option, and public journey pages do not opt in by
  default.
- [x] (2026-06-14) Session 3: Ran typecheck, focused provenance tests, smoke tests, `git diff
  --check`, and targeted scans. Full `npm.cmd --prefix frontend run test:api` remains blocked by
  pre-existing unrelated route/auth test failures.

## Surprises & Discoveries

- Observation: The leak is localized in the public explanation component rather than in backend
  artifact generation.
  Evidence: `frontend/components/explanation/SiteExplanationHierarchy.tsx` directly formats
  `item.source_refs` as `Source: artifact:field_path` and displays `site_explanation_bundle_v1`.

- Observation: `npm.cmd --prefix frontend run test:api` initially failed on stale assertions not
  caused by Session 1. The current `frontend/app/auth/callback/route.ts` redirects to
  `/client-profile`, and current `frontend/components/layout/Sidebar.tsx` no longer renders the old
  persistence widgets, while the test still expected `/onboarding/name`, `<PersistenceStatus />`,
  and `<SavedReviewsPanel />`.
  Evidence: The failing test was `Supabase staged persistence keeps canonical stage names and strips
  raw artifact references`; updating only those stale assertions made the full API test pass.

- Observation: A temporary unrelated diff changed portfolio API route runtime declarations to
  `edge` and added `export const runtime = "edge";` to the auth callback. This was outside Session 1
  scope and was manually restored before completion.
  Evidence: `git diff --name-only` after restoration no longer lists those route files.

- Observation: At the start of Sessions 2 and 3, the working tree still contained unrelated dirty
  API/auth route changes. The full frontend API test suite failed in those areas, while the new
  provenance tests passed.
  Evidence: `npm.cmd --prefix frontend run test:api` failed on builder prepare, auth callback,
  recovery, candidate, and report route assertions; `node --test --test-name-pattern
  "SiteExplanationHierarchy|site explanation|public journey pages" frontend/tests/api-route-tests.cjs`
  passed 4/4.

## Decision Log

- Decision: Keep backend `source_refs`, schema versions, artifact names, and field paths unchanged.
  Rationale: They are required for auditability and deterministic evidence grounding; the defect is
  public rendering, not data generation.
  Date/Author: 2026-06-14 / Codex.

- Decision: Session 1 introduces a frontend presenter boundary instead of only deleting visible
  strings from the component.
  Rationale: A presenter makes the safe public display model explicit and prevents future UI code
  from accidentally treating backend contracts as presentation contracts.
  Date/Author: 2026-06-14 / Codex.

- Decision: Stop after Session 1 and do not build debug provenance in the same implementation pass.
  Rationale: The user requested a three-session workflow and an explicit stop after Session 1.
  Date/Author: 2026-06-14 / Codex.

- Decision: Developer provenance is opt-in through component/presenter options, not a route-wide
  automatic toggle.
  Rationale: Keeping the default prop false prevents accidental public leakage and lets future
  developer/operator surfaces opt in deliberately when they need audit traces.
  Date/Author: 2026-06-14 / Codex.

- Decision: Session 3 regression coverage checks both the presenter output and the public journey
  pages.
  Rationale: The presenter test prevents raw provenance from entering the default display model,
  while the page-source guard prevents public routes from enabling the debug panel by accident.
  Date/Author: 2026-06-14 / Codex.

## Outcomes & Retrospective

Session 1 is complete. `SiteExplanationHierarchy` now renders a public display model from
`buildPublicSiteExplanationDisplayModel`, so normal explanation cards show user-facing evidence
labels and no longer print `Source: artifact:field_path` or `site_explanation_bundle_v1`. The
underlying `SiteExplanationBundle` type and `source_refs` remain unchanged for audit and QA.

Verification completed:

    npm.cmd --prefix frontend run typecheck
    npm.cmd --prefix frontend run test:api
    npm.cmd --prefix frontend run test:smoke
    git diff --check
    rg -n "Source:|site_explanation_bundle_v1|ref\.artifact|ref\.field_path|source_refs\.map" frontend/components/explanation frontend/lib/siteExplanationPresenter.ts

The targeted component/presenter scan returned no matches. A broader scan still finds expected
matches in data cleaning code and tests that preserve or assert against backend provenance; those are
not public rendering paths.

Sessions 2 and 3 are complete. `SiteExplanationHierarchy` now accepts
`showDeveloperProvenance`, which defaults to `false`. When a future developer surface explicitly
passes `showDeveloperProvenance={true}`, the component renders a collapsed `Developer provenance`
panel with schema version, review id, item ids, levels, claim types, raw evidence statuses, warnings,
and `artifact:field_path` references. Public journey pages do not pass that prop, so normal users
still see only product-language evidence labels.

Contract updates now document the boundary in `docs/specs/site_explanation_bundle_spec.md`,
`docs/contracts/PRESENTATION_LANGUAGE_RULES.md`, `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`, and
`docs/contracts/SCREEN_CONTRACTS.md`.

Verification completed for Sessions 2 and 3:

    npm.cmd --prefix frontend run typecheck
    node --test --test-name-pattern "SiteExplanationHierarchy|site explanation|public journey pages" frontend/tests/api-route-tests.cjs
    npm.cmd --prefix frontend run test:smoke
    git diff --check
    rg -n "Source:|site_explanation_bundle_v1|ref\.artifact|ref\.field_path|source_refs\.map" frontend/components/explanation frontend/lib/siteExplanationPresenter.ts frontend/tests

The targeted scan still finds expected matches in the presenter developer-provenance adapter and in
tests that assert public non-rendering. Full `npm.cmd --prefix frontend run test:api` was attempted
but remains blocked by unrelated dirty route/auth changes that predate Sessions 2 and 3.

## Context and Orientation

The relevant frontend data type is `SiteExplanationBundle` in `frontend/lib/types.ts`. It represents
the backend explanation artifact. A bundle has a `schema_version`, screen-level groups
(`executive`, `evidence`, and `technical`), and each text item may have `source_refs`. A source ref is
an internal audit pointer that names an artifact and field path.

The public renderer is `frontend/components/explanation/SiteExplanationHierarchy.tsx`. Before this
plan, it rendered backend fields directly: it displayed `site_explanation_bundle_v1` as a badge and
printed each source ref as `Source: portfolio_xray.json:...`. This file is the primary Session 1
target.

The new Session 1 boundary belongs in a frontend presenter module. In this repository, a presenter
means a small adapter that converts backend-shaped data into user-facing display data. The presenter
must not remove backend data from storage; it only controls what the UI component receives and
renders.

## Plan of Work

Session 1 adds `frontend/lib/siteExplanationPresenter.ts`. This module exports public display types
and a function that accepts a `SiteExplanationBundle`, screen key, and fallback title. It returns
`null` when there is no copy for the screen. Otherwise it returns a display model with only `title`,
`subtitle`, `executiveItems`, `evidenceItems`, and `technicalItems`. Each public item contains an
`id`, `text`, `tone`, `evidenceLabel`, and `evidenceTone`. It deliberately does not include raw
`source_refs`, `artifact`, `field_path`, `schema_version`, or raw status words.

Session 1 then updates `SiteExplanationHierarchy` to use this presenter. The component renders
`Decision evidence` and a product-language subtitle. It renders the user-facing evidence label in
the badge. It does not format source refs, display schema versions, or show raw backend field names.

Session 1 updates frontend tests. A focused test loads the presenter with a bundle containing raw
artifact names and verifies that the presenter output serializes without those raw backend strings.
A component source test verifies that `SiteExplanationHierarchy` no longer formats
`ref.artifact` or `ref.field_path`. The smoke test also rejects the public leak strings on the main
public journey routes.

Session 2 adds an explicit developer-only trace. The trace is not automatic, is not enabled by any
current public journey page, and must be requested through code by passing `showDeveloperProvenance`
to `SiteExplanationHierarchy` or `includeDeveloperProvenance` to the presenter. This trace is for
developer/operator audit only.

Session 3 updates the long-term contracts and regression guards. The owning spec and presentation
contracts now say that raw provenance is valid data but not default UI. Tests cover the default
public presenter, the explicit developer presenter, the component boundary, and public page source
usage.

## Concrete Steps

Work from the repository root:

    D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА

For Session 1, edit only the frontend presenter/component/test files plus this ExecPlan. Do not
rename backend artifacts. Do not change `SiteExplanationBundle` to remove `source_refs`.

Run these commands after implementation:

    npm.cmd --prefix frontend run typecheck
    npm.cmd --prefix frontend run test:api
    npm.cmd --prefix frontend run test:smoke
    git diff --check

Run a targeted source scan:

    rg -n "Source:|site_explanation_bundle_v1|ref\.artifact|ref\.field_path" frontend/components frontend/lib frontend/tests

Expected result after Session 1: remaining matches are allowed only in tests that assert the strings
are not publicly rendered, or in type/data cleaning code that preserves backend data without
rendering it.

## Validation and Acceptance

Session 1 is accepted when the frontend typecheck passes, API and smoke tests pass, and the public
route smoke test rejects raw provenance strings. A human can also start the frontend and open
`/diagnosis`; the explanation cards should show product-language evidence labels, not
`Source: portfolio_xray.json:...` or `site_explanation_bundle_v1`.

The focused presenter test must prove that a bundle containing `portfolio_xray.json`,
`problem_classification.json`, and field paths produces a public display model that does not contain
those strings. The component test must prove the renderer no longer formats raw refs.

Session 1 is done only when the executor stops and reports exactly:

    да — Session 1 завершена по плану Public Presentation Boundary for Evidence Provenance

## Idempotence and Recovery

These edits are safe to retry. The presenter is additive, and the component migration only changes
how existing bundle data is displayed. If typecheck fails, inspect the new presenter types and the
component props first. If smoke tests fail because a public route still leaks provenance, search the
rendering component for direct use of backend artifact names, schema versions, or source refs.

Do not use destructive git commands to recover. Review `git diff` and patch only the intended files.

## Artifacts and Notes

Initial evidence of the defect:

    frontend/components/explanation/SiteExplanationHierarchy.tsx renders:
    Source: {item.source_refs.map((ref) => `${ref.artifact}:${ref.field_path}`).join(" · ")}
    and displays:
    site_explanation_bundle_v1

Those lines are the immediate public leak. The root fix is a presenter boundary, not deleting
backend provenance from the data contract.

## Interfaces and Dependencies

Create this frontend interface in `frontend/lib/siteExplanationPresenter.ts`:

    export type PublicSiteExplanationItem = {
      id: string;
      text: string;
      tone: "neutral" | "caution" | "risk" | "positive";
      evidenceLabel: string;
      evidenceTone: StatusTone;
    };

    export type PublicSiteExplanationDisplayModel = {
      title: string;
      subtitle: string;
      executiveItems: PublicSiteExplanationItem[];
      evidenceItems: PublicSiteExplanationItem[];
      technicalItems: PublicSiteExplanationItem[];
    };

    export function buildPublicSiteExplanationDisplayModel(
      bundle: SiteExplanationBundle | undefined,
      screen: string,
      fallbackTitle?: string
    ): PublicSiteExplanationDisplayModel | null;

The presenter depends only on `frontend/lib/types.ts`. It must not import React or UI components.
