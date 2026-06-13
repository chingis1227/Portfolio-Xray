# Current Frontend Design Documentation Synchronization

This ExecPlan records the 2026-06-13 documentation/code synchronization that made the implemented `frontend/` website the source for current design docs.

## Status

Completed.

## Goal

Synchronize active design, screen, and frontend documentation with the latest local website: public landing, required sign-in, onboarding, 8-step platform shell, graphite token palette, current page blocks, and local-only dev bypass.

## Progress

- [x] Replaced the old root external-reference `DESIGN.md` with current Portfolio MRI design authority.
- [x] Added `docs/design/current_website_structure.md` as the route-by-route website structure source.
- [x] Updated design/system/screen contracts to the 8-step journey and current token palette.
- [x] Changed landing `Enter Platform` to the canonical sign-in route.
- [x] Kept `/onboarding/name?dev_bypass=1` as local testing support only.
- [x] Corrected page-header step labels for Client Fit, Hypothesis, Comparison, Verdict, and Report.
- [x] Removed active outdated prototype handoff design documents from `docs/design/`.
- [x] Repaired pre-existing frontend source corruption where `?`, `?.`, `??`, and regex `?:` had been persisted as `...` tokens.

## Decisions

- The implemented frontend is the source for current design documentation.
- Canonical product path requires email sign-in before onboarding.
- Local dev bypass remains available but is not a product path.
- Root `DESIGN.md` remains because many project docs link to it; its content is current.

## Verification Plan

- Run stale-reference scans for old external/prototype design authority, obsolete route wording, `/client-profile` as primary entry, and old design tokens.
- Run `npm.cmd run test:api`, `npm.cmd run test:smoke`, `npm.cmd run typecheck`, and `npm.cmd run build` from `frontend/`.
- Run browser checks on landing, sign-in, dev bypass, onboarding, Portfolio Input, and locked platform routes.
- Run `git diff --check`.

## Outcome

Completed on 2026-06-13.

Verification completed:

- `npm.cmd run typecheck`
- `npm.cmd run test:api`
- `npm.cmd run test:smoke`
- `npm.cmd run build`
- Playwright browser check on `http://127.0.0.1:3028` for `/`, `/onboarding/sign-in`, `/onboarding/name?dev_bypass=1`, `/portfolio-input`, `/comparison`, and `/verdict`.
- Active stale-reference scan for old external/prototype design authority, obsolete route wording, `/client-profile` as primary entry, old seven-screen wording, and legacy design references.
- Full removed-design-reference markdown/source scan.
- Cyrillic/mojibake source scan for touched frontend and documentation paths.
- `git diff --check`
