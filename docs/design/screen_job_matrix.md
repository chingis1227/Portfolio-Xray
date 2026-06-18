# Screen Job Matrix

Status: UX implementation matrix for current Portfolio MRI routes. This document supports `docs/contracts/SCREEN_CONTRACTS.md` and the UX audit from `docs/audits/2026-06-18_ux_ui_product_audit_sprint.md`.

## Matrix

| Route | Screen job | First 5-second answer | Primary CTA | Secondary actions | Required states | Forbidden primary wording |
| --- | --- | --- | --- | --- | --- | --- |
| `/` | Explain Portfolio MRI and route to entry. | This is diagnosis-first decision support, not a trading app. | Enter Platform. | Learn workflow, review boundaries. | Public ready, mobile, long copy. | Optimizer cockpit, buy, sell, best portfolio. |
| `/onboarding/sign-in` | Require email-first entry. | Sign in before using the platform. | Continue. | Local fallback on localhost only. | Empty email, verification, local fallback, error. | Public bypass as normal path, backend, JSON. |
| `/onboarding/name` | Collect friendly identity. | Tell the product what to call you. | Continue. | Back to sign-in. | Empty, valid, error. | Diagnostics, suitability approval. |
| `/onboarding/investor-type` | Capture Client Fit context. | Your profile informs diagnosis but does not approve action. | Save and continue. | Back, edit answers. | Question progress, missing answer, saved, error. | Suitability approved, optimizer mandate. |
| `/onboarding/loading` | Transition after onboarding. | The platform is preparing your workspace. | Auto-continue. | None unless recovery needed. | Loading, saved profile, redirect error. | Backend stages, technical tables. |
| `/workspace` | Show account home and review history. | You can continue, start new, or open a saved review. | Continue latest or start new review. | Open history, use saved portfolio. | First-time empty, returning empty, read-only history, archived. | Auto-run diagnosis, raw artifact paths. |
| `/portfolio-input` | Define the current portfolio. | Add holdings and weights to diagnose the current portfolio. | Run diagnosis. | Recover review, adjust Client Fit. | Empty, invalid ticker, invalid total weight, loading, backend-safe error, recovered review. | Demo allocation as canonical input, optimizer targets, suitability approval. |
| `/diagnosis` | Explain current-portfolio diagnosis. | This is the main material issue in the current portfolio. | Review Stress Lab. | Back to Portfolio Input, advanced diagnostics. | Locked, running, failed, partial evidence, complete. | Rebalance recommendation, candidate answer, metric wall first. |
| `/evidence` | Review Stress Test Lab evidence. | This stress behavior explains why the diagnosis matters. | Continue to Client Fit. | Back to Diagnosis, technical drill-down. | Locked, limited stress evidence, unavailable model, ready. | Candidate verdict, trade instruction. |
| `/client-fit` | Interpret non-binding profile fit. | Profile context can constrain interpretation but cannot clear issues. | Continue to Hypothesis. | Adjust profile. | Missing profile, locked, partial fit, ready. | Suitability approval, proof no action is needed. |
| `/hypothesis` | Choose and generate one diagnostic test. | This is the one test path worth generating and why. | Generate one test candidate. | Review alternatives, adjust setup, return to Client Fit. | Locked, read-only history, ready, generating, failed, generated. | Candidate as recommendation, automatic action, optimizer arena. |
| `/comparison` | Compare current portfolio and one generated test candidate. | These are the material trade-offs; this is not the verdict. | Continue to Verdict. | Return to Hypothesis, retry comparison. | No candidate, candidate unavailable, running, metrics unavailable, stale lineage, ready. | Winner, switch, best portfolio, trade now. |
| `/verdict` | Interpret evidence as non-binding decision support. | This is the cautious conclusion and its limitations. | Open Report. | Test another path, return to Comparison. | Evidence insufficient, candidate failed, stale comparison, ready, read-only history. | Must rebalance, buy, sell, suitability approved, guaranteed improvement. |
| `/report` | Create a grounded report preview. | This preview summarizes selected evidence from the active review. | Create preview or open preview. | Return to Verdict or Workspace. | Locked, missing verdict, generating, partial context, ready preview, read-only history. | Polished PDF default, AI recommendation, raw artifact viewer. |
| `/client-profile` | Advanced manual Client Fit editor. | Advanced users can edit profile assumptions manually. | Save profile. | Back to Portfolio Input. | Empty, saved, invalid. | Canonical first onboarding step. |
| `/sandbox/components` | Review isolated UI states. | Component and state variants can be checked without full journey flow. | Open benchmark route. | Back to Workspace. | Normal, long text, mobile, loading, empty, locked, partial, stale, failed. | Product journey step, production backend action. |

## `/onboarding/goals` classification

`/onboarding/goals` is classified as a legacy compatibility route for this implementation wave. It is not part of the canonical current journey and must not be promoted in new route maps. Do not delete it in this wave because older checked-in plans and the compatibility page still reference it. A future cleanup may remove it only after a dedicated dependency search and route migration.

## Text wireframes

### `/portfolio-input`

Hero: define the current portfolio for diagnosis. Show Client Fit summary if present. Main canvas: holdings and weights table with inline validation. Side panel: assumptions, recovery, and draft/new-review explanation. Primary CTA: Run diagnosis. Mobile: form first, summary and recovery below.

### `/diagnosis`

Hero: one diagnosis and one interpretation sentence. Evidence strip: up to four facts. Canvas: drivers and next stress review. CTA: open Stress Lab. Advanced diagnostics: collapsed. Do not repeat generic current-only, evidence-quality, or candidate-boundary copy in the hero, cards, canvas, or CTA. Mobile: hero, evidence, CTA, drivers, advanced disclosure.

### `/hypothesis`

Hero: proposed diagnostic test and why it is the next safe test. Evidence summary: selected because, first success criterion, trade-off. Main column: diagnosis recap and proposed test. Right console: setup and generate action. Secondary details: Client Fit, alternatives, technical evidence. Mobile: action console moves below proposed test.

### `/comparison`

Hero: trade-off comparison status. Context strip: active diagnostic test. Evidence summary: improvement, cost/trade-off, evidence quality. Matrix: grouped risk improvement, trade-offs, fit impact, evidence quality. Secondary: allocations and warnings. Mobile: context and evidence before matrix.

### `/verdict`

Hero: cautious decision-support interpretation. Context strip: active diagnostic test and limitation. Evidence summary: rationale, major trade-off, evidence quality. Main card: verdict framing and what would change it. Client Fit remains one input. Mobile: limitation and next safe step remain visible before details.

### `/report`

Hero: grounded report preview status. Context strip: active diagnostic test. Preview card: executive narrative. Evidence cards: evidence used, unavailable evidence, limitations. Grounding trace: collapsed secondary detail. Mobile: preview first, trace collapsed.
