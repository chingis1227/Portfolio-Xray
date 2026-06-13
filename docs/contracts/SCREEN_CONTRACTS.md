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

## Route contracts

| Route | Product role | Must show | Primary CTA / next step | Must not show |
| --- | --- | --- | --- | --- |
| `/` | Public landing and product explanation. | Header/nav, hero, problem, workflow, architecture, precision, final CTA. | `Enter Platform` -> `/onboarding/sign-in`. | Platform sidebar, top journey rail, optimizer cockpit language. |
| `/onboarding/sign-in` | Required email-first entry. | Email step, verification step, local fallback on localhost. | Continue to onboarding after auth or local fallback. | Treat local fallback as canonical product path. |
| `/onboarding/name` | Friendly personal setup. | Name input and Continue CTA. | `/onboarding/investor-type`. | Portfolio diagnostics or suitability language. |
| `/onboarding/investor-type` | Five-question Client Fit intake. | One question at a time, progress, Back/Next/final save. | `/onboarding/loading`. | Investment advice or optimizer mandates. |
| `/onboarding/loading` | Setup transition. | Setup progress and Client Fit context save messaging. | Auto-redirect to `/portfolio-input`. | Platform sidebar. |
| `/portfolio-input` | Step 01: define current portfolio. | Client Fit summary, currency, holdings/weights, validation, recovery. | Run diagnosis -> `/diagnosis`. | Optimizer targets, tax settings, suitability approval. |
| `/diagnosis` | Step 02: current portfolio X-Ray. | Diagnosis summary or locked state. | Continue to Stress Lab or return to Portfolio Input. | Rebalance recommendation from diagnosis alone. |
| `/evidence` | Step 03: Stress Test Lab. | Stress evidence, helped/hurt, hedge gaps, limitations, or locked state. | Continue to Client Fit. | Candidate/comparison/verdict language. |
| `/client-fit` | Step 04: profile-fit interpretation. | Fit status, source quality, target rows, explanations, or locked state. | Continue to Hypothesis. | Suitability approval or hiding diagnostic issues. |
| `/hypothesis` | Step 05: one diagnostic test path. | Diagnosis recap, Launchpad, Builder setup, candidate generation state. | Generate one test candidate / continue to Comparison. | Candidate as recommendation or auto-generated action. |
| `/comparison` | Step 06: current vs one candidate. | Improvements, worsening, similar/unavailable evidence, materiality. | Continue to Verdict. | Winner framing, final verdict, trade instruction. |
| `/verdict` | Step 07: decision support. | Non-binding verdict, rationale, limits, next safe step. | Report or test another. | `must rebalance`, `trade now`, `best portfolio`. |
| `/report` | Step 08: grounded report preview. | Evidence used, unavailable evidence, warnings, narrative preview. | Create preview when evidence is ready. | Unsupported conclusions or raw artifact viewer. |
| `/client-profile` | Advanced/manual Client Fit editor. | Manual planning inputs, suggested preset, target rows. | Save profile and continue to Portfolio Input. | Treat as canonical Step 01. |

## QA checklist

- [ ] Landing and onboarding do not show platform shell.
- [ ] Platform routes show the 8-step journey rail.
- [ ] Page-header step labels match the rail.
- [ ] Locked states show the current route step and the missing prerequisite.
- [ ] `/client-profile` stays advanced/manual.
- [ ] `/hypothesis` remains the merged Launchpad/Builder/Candidate screen unless a route split is intentionally approved.
- [ ] Monitoring / What Changed remains deferred unless a route decision promotes it.
- [ ] Same-review, same-selected-card, same-candidate, and same-stage-order lineage is preserved before unlocking downstream screens.
- [ ] Documentation impact was checked against `docs/contracts/DOC_SYNC_CONTRACT.md`.
