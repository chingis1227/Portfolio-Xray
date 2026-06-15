# Screen Contracts

Status: canonical screen-level contract for current Portfolio MRI frontend routes, responsibilities, empty states, CTAs, and QA checks.

Scope: current MVP route behavior and product copy boundaries. Non-scope: backend formulas, JSON schemas, stress scenario definitions, generated output refresh, PDF generation, and detailed visual tokens.

Use with:

- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for product order;
- `docs/specs/frontend_screen_contracts.md` for route-specific screen requirements;
- `docs/design/current_website_structure.md` for current visible blocks and headings;
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` for visual rules;
- `docs/contracts/PRESENTATION_LANGUAGE_RULES.md` for wording.

## Current route reality

Canonical visible user path:

```text
/
-> /onboarding/sign-in
-> /onboarding/name
-> /onboarding/investor-type
-> /onboarding/loading
-> /workspace (returning signed-in account home)
-> /portfolio-input
-> /diagnosis
-> /evidence
-> /client-fit
-> /hypothesis
-> /comparison
-> /verdict
-> /report
```

Local development shortcut:

```text
/onboarding/name?dev_bypass=1
```

`/client-profile` exists as an advanced/manual Client Fit profile editor. It is not the first step of the normal web journey.

There is no current `/candidate`, `/monitoring`, `/what-changed`, optimizer-arena, action-plan, decision-journal, macro-dashboard, or PDF-product route. `/hypothesis` owns Problem Classification handoff, Candidate Launchpad, Builder setup, and the explicit candidate-generation attempt for the MVP.

## Global screen rules

1. Current portfolio evidence appears before candidate evidence.
2. A candidate is a diagnostic hypothesis test, not a recommendation or trade order.
3. Builder setup is setup-only until the user explicitly generates one candidate attempt.
4. Comparison is trade-off evidence, not a verdict.
5. Verdict is non-binding decision support.
6. Report preview is grounded explanation, not an invented AI recommendation.
7. Client Fit is diagnostic context, not suitability approval or optimizer mandate.
8. Missing, partial, stale, blocked, locked, and evidence-insufficient states are valid and visible.
9. Raw artifact filenames, JSON keys, booleans, backend IDs, run folder paths, and operator terms are not primary UI copy.
10. Evidence-provenance traces from `site_explanation_bundle.json` are hidden by default. Public explanation cards show product-language evidence labels; raw schema names, artifact filenames, and field paths may appear only in an explicit developer/debug provenance panel.
11. Staged diagnosis internals such as `Data check`, `pending`, `waiting`, provider freshness, backend stage IDs, and per-stage status rows are operational state, not normal product UI. Running diagnosis screens may show a simple product-facing preparation message and safe user-facing errors.

## Route contracts

| Route | Product role | Must show | Primary CTA / next step | Must not show |
| --- | --- | --- | --- | --- |
| `/` | Public landing and product explanation. | Header/nav, hero, problem, workflow, architecture, precision, final CTA. | `Enter Platform` -> `/onboarding/sign-in`. | Platform sidebar, top journey rail, optimizer cockpit language. |
| `/onboarding/sign-in` | Required email-first entry. | Email step, verification step, local fallback on localhost. | Continue to onboarding for new users; route completed signed-in users with saved workspace/history to `/workspace`; route completed users without saved workspace data to Portfolio Input. | Treat local fallback as canonical product path; do not run diagnosis or refresh market data during login. |
| `/onboarding/name` | Friendly personal setup. | Name input and Continue CTA. | `/onboarding/investor-type`. | Portfolio diagnostics or suitability language. |
| `/onboarding/investor-type` | Five-question Client Fit intake. | One question at a time, progress, Back/Next/final save; questions cover stress-loss reaction, withdrawal horizon, temporary-loss limit, return target, and concentration response. | `/onboarding/loading`. | Investment advice or optimizer mandates. |
| `/onboarding/loading` | Setup transition. | Setup progress and Client Fit context save messaging. | Auto-redirect to `/workspace` when saved workspace/history exists for a returning user; otherwise `/portfolio-input`. | Platform sidebar. |
| `/workspace` | Signed-in account home and review-history hub. | Current review, active portfolio, saved review count, portfolio library, past reviews, archive states, and clear no-auto-recalculation copy. | Continue latest review, start new review, open past review, or use a saved portfolio for a new review. | Act as a calculation step, auto-run diagnosis on login, imply a historical verdict applies to edited input, expose raw artifact paths, or replace the 8-step review rail. |
| `/portfolio-input` | Step 01: define current portfolio. | Client Fit summary, empty-by-default holdings/weights input, validation, recovery, and clear draft/new-review semantics when loaded from workspace. | Run diagnosis -> `/diagnosis`. | Prefilled demo allocation, optimizer targets, tax settings, suitability approval, technical staged-progress table, silent overwrite of completed review evidence. |
| `/diagnosis` | Step 02: current portfolio diagnosis. | One main finding, data-coverage state, up to three primary evidence facts, compact `What matters first`, historical behavior snapshot, collapsed advanced diagnostics, locked state, or simple product-facing running state. | Continue to Stress Lab or return to Portfolio Input. | Rebalance recommendation from diagnosis alone, standalone explanation wall, repeated generic evidence badges, Macro Dashboard/PCA diagnostics, technical staged-progress table. |
| `/evidence` | Step 03: Stress Test Lab. | Stress evidence, helped/hurt, hedge gaps, limitations, or locked state. | Continue to Client Fit. | Candidate/comparison/verdict language. |
| `/client-fit` | Step 04: profile-fit interpretation. | Concise risk-profile verdict, source quality, two to three ranked reasons, compact target rows, collapsed `How we checked this` evidence details, or locked/missing-profile state. | Continue to Hypothesis. | Suitability approval, hiding diagnostic issues, raw evidence walls, repeated generic evidence badges, or technical provenance in the primary UI. |
| `/hypothesis` | Step 05: one diagnostic test path. | Analyst-workstation view with one primary diagnosis, one recommended diagnostic test, selected setup/action console, secondary Client Fit context, collapsed alternatives, and evidence/technical details. | Generate one test candidate / continue to Comparison. | Candidate as recommendation, auto-generated action, Client Fit suitability approval, or technical evidence competing with the primary CTA. |
| `/comparison` | Step 06: current vs one candidate. | Improvements, worsening, similar/unavailable evidence, materiality. | Continue to Verdict. | Winner framing, final verdict, trade instruction. |
| `/verdict` | Step 07: decision support. | Non-binding verdict, rationale, limits, next safe step. | Report or test another. | `must rebalance`, `trade now`, `best portfolio`. |
| `/report` | Step 08: grounded report preview. | Evidence used, unavailable evidence, warnings, narrative preview. | Create preview when evidence is ready. | Unsupported conclusions or raw artifact viewer. |
| `/client-profile` | Advanced/manual Client Fit editor. | Manual planning inputs, suggested preset, target rows. | Save profile and continue to Portfolio Input. | Treat as canonical Step 01. |

## QA checklist

- [ ] Landing and onboarding do not show platform shell.
- [ ] Platform routes show the 8-step journey rail.
- [ ] Page-header step labels match the rail.
- [ ] Locked states show the current route step and the missing prerequisite.
- [ ] `/workspace` restores saved work without running diagnosis or market refresh automatically.
- [ ] Past reviews are clearly read-only unless full local evidence can be restored.
- [ ] Editing a completed review portfolio creates a new draft and does not mutate the old completed review.
- [ ] `/client-profile` stays advanced/manual.
- [ ] `/hypothesis` remains the merged Launchpad/Builder/Candidate screen unless a route split is intentionally approved.
- [ ] `/hypothesis` exposes one primary test and keeps Client Fit, alternatives, and technical evidence secondary.
- [ ] Monitoring / What Changed remains deferred unless a route decision promotes it.
- [ ] Same-review, same-selected-card, same-candidate, and same-stage-order lineage is preserved before unlocking downstream screens.
- [ ] Documentation impact was checked against `docs/contracts/DOC_SYNC_CONTRACT.md`.
