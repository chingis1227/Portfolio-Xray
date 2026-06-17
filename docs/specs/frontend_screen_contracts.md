# Frontend Screen Contracts

Status: current screen contract for the implemented Portfolio MRI Next.js frontend.

Scope: user-facing route responsibilities, screen order, required states, CTA boundaries, and copy guardrails. This document does not define backend formulas, JSON schemas, stress scenarios, optimizer rules, or generated-output contracts.

Use with:

- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for product-order boundaries;
- `docs/contracts/SCREEN_CONTRACTS.md` for canonical route-level QA checks;
- `docs/design/current_website_structure.md` for visible block order and current copy;
- `docs/contracts/PRESENTATION_LANGUAGE_RULES.md` for safe wording;
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` for visual rules.

## Current route chain

Canonical user path:

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

Local-only preview shortcut:

```text
/onboarding/name?dev_bypass=1
```

The shortcut is allowed for local testing while email sign-in is being stabilized. It must not be described as the canonical product path.

## Platform journey rail

| Step | Route | Screen label | Contract |
| --- | --- | --- | --- |
| 01 | `/portfolio-input` | Portfolio | Define factual current holdings and run diagnosis. |
| 02 | `/diagnosis` | Diagnosis | Explain current portfolio exposures and weaknesses. |
| 03 | `/evidence` | Stress Lab | Show stress behavior and evidence limits. |
| 04 | `/client-fit` | Client Fit | Compare current evidence with the provided planning profile. |
| 05 | `/hypothesis` | Hypothesis | Select, prepare, and generate one diagnostic test candidate. |
| 06 | `/comparison` | Comparison | Compare current vs one active generated candidate. |
| 07 | `/verdict` | Verdict | Produce non-binding decision support. |
| 08 | `/report` | Report | Produce a grounded client-ready preview. |

`/client-profile` is an advanced/manual Client Fit editor and must not be treated as Step 01.

## Global screen rules

1. The UI is diagnosis-first and current-portfolio-first.
2. A candidate is a diagnostic hypothesis test, not a recommendation and not a trade order.
3. Builder setup is setup-only until the user explicitly generates one candidate attempt.
4. Comparison must show trade-offs before Verdict.
5. Verdict is non-binding decision support. Keep-current, no material rebalance, test-another, candidate failed/infeasible, and evidence-insufficient states are valid.
6. Missing, locked, partial, stale, and evidence-insufficient states must be visible and distinct.
7. Raw artifact names, JSON keys, backend labels, run folders, booleans, and method IDs must not appear in primary UI copy.
8. Client Fit status is diagnostic context only; it is not suitability approval, optimizer mandate, or proof that no action is needed.
9. Report preview must stay grounded in active review evidence and limitations.

## Public route contracts

### Landing `/`

- Must not show platform sidebar or top journey rail.
- Must show product explanation blocks in this order: header/nav, hero, problem, workflow, architecture, precision, final CTA.
- `Enter Platform` must point to `/onboarding/sign-in`.
- Must explain diagnosis-first, current-first, candidate-tests-not-orders.

### Sign-in `/onboarding/sign-in`

- Must present email as the required canonical product entry before onboarding.
- Must support email/code flow when Supabase auth is enabled.
- May show a localhost-only fallback button: `Continue locally while Supabase is not ready`.
- Fallback must route into onboarding without becoming canonical product copy.

### Onboarding `/onboarding/name`, `/onboarding/investor-type`, `/onboarding/loading`

- Must collect friendly planning context before Portfolio Input.
- Must ask five one-question-at-a-time intake questions on `/onboarding/investor-type`.
- Must map answers into bounded Client Fit context from stress-loss reaction, withdrawal horizon, temporary-loss limit, return target, and concentration response.
- Must not call Client Fit suitability approval or investment advice.

## Platform screen contracts

### Portfolio Input `/portfolio-input`

- Must show `Step 01 / Portfolio to diagnose` and `Define the current portfolio`.
- Must show Client Fit profile summary, investor currency, holdings/weights table, validation/readiness, Run diagnosis CTA, and recovery panel.
- Must let `Adjust intake` update target rows and reclassify the displayed Client Fit preset from those edited values.
- Must block diagnosis until Client Fit context, currency, at least two valid holdings, and weights summing to 100% are valid.
- Must not show optimizer targets, tax settings, full constraints, suitability approval, or raw backend request details.

### Diagnosis `/diagnosis`

- Must lead with a shared `VerdictHero` using compact context `Step 02 of 8 - Portfolio Diagnosis`.
- Locked state must say `Complete Portfolio Input first to unlock Diagnosis.` and link to Portfolio Input.
- Ready state must explain current portfolio evidence before any candidate test through one dominant diagnosis headline, one interpretation sentence, up to three supporting facts, and a four-item Evidence Summary covering primary issue, severity, drivers, and evidence quality.
- Ready state must use a grouped Metric Matrix for diagnosis metrics: risk pressure, portfolio structure, evidence quality, and secondary observations.
- Ready state must keep professional metrics and technical evidence secondary behind collapsed advanced diagnostics instead of returning to a card wall by default.
- Ready state must not render a standalone `Diagnosis explanation` wall or repeat generic `Evidence available` badges across every fact.
- Must not recommend rebalance from Portfolio Diagnosis alone.

### Stress Test Lab `/evidence`

- Must show `Step 03 / Stress Test Lab` and `Stress Test Lab`.
- Locked state must say Stress Lab requires Portfolio Input / diagnosis first.
- Ready state must show one primary current-portfolio stress answer before detailed evidence.
- The primary surface must stay compact: no more than three supporting facts and no more than four primary metric cards.
- Stress scenarios, loss contributors, helped/hurt assets, hedge gaps, diagnosis confirmation, evidence trace, and limitations must remain available when present, but detailed scenario and technical sections should be collapsed by default.
- Repeated `Evidence available` badges should not appear across the primary stress cards; evidence quality should be summarized once and expanded in the evidence-quality drill-down.
- Must not create candidate, comparison, verdict, or rebalance language.

### Client Fit `/client-fit`

- Must show `Step 04 / Risk profile check` and `Your portfolio vs your risk profile`.
- Must lead with one concise verdict card (`Within your profile`, `Worth reviewing`, `Outside your profile`, `Goal and risk conflict`, or `Profile missing`) before detailed rows.
- Must explain Client Fit is separate from diagnostic quality and decision action.
- Locked state must route to Client Profile or Portfolio Input.
- Ready state must show source quality/profile confidence, two to three ranked reasons, compact target rows, portfolio values, limits, explanations, and next test context.
- Raw evidence hierarchy and technical provenance must be collapsed by default under `How we checked this`; repeated `Evidence available` badges must not appear in the primary UI.

### Hypothesis `/hypothesis`

- Must show `Step 05 / Hypothesis`.
- Must keep Launchpad, Builder setup, and candidate generation as one merged MVP screen unless a future route split is approved.
- Must render through a frontend Hypothesis screen model that normalizes compact review state into one primary diagnosis, one recommended diagnostic test, one primary CTA, secondary alternatives, Client Fit context, and collapsed evidence/technical details.
- Must preserve backend Launchpad priority: the primary test comes from the first eligible Launchpad card unless the user selected another eligible card.
- Must present candidates as tests only and show the decision boundary once in the main test/workstation surface.
- Must keep Client Fit as a secondary context panel; it must not override the selected diagnosis or approve suitability.
- Must place supporting evidence and technical details below the main workstation instead of competing with the primary CTA.
- Must show selected-card/builder lineage before candidate generation.
- Must not auto-generate candidates, display generated weights as primary Hypothesis content, or present a candidate as a recommended allocation.

### Comparison `/comparison`

- Must show `Step 06 / Comparison` and `Current vs Candidate Comparison`.
- Must require one active generated candidate.
- Must show the current allocation next to the generated candidate allocation before or while comparison evidence is produced.
- Must automatically attempt same-candidate comparison when the generated candidate is compare-ready, while preserving a retry path for failures.
- Must show improvements, worsening, similar/neutral results, unavailable evidence, practicality, and materiality.
- Must not crown a winner or issue a verdict.

### Verdict `/verdict`

- Must show `Step 07 / Verdict` and `Decision verdict`.
- Must require current comparison evidence or a safe evidence-insufficient/candidate-failed condition.
- Must present non-binding outcomes only.
- Must not say `trade now`, `must rebalance`, `best portfolio`, or `suitability approved`.

### Report `/report`

- Must show `Step 08 / Report` and `Client-ready report preview`.
- Must require active diagnosis, selected candidate, comparison, and verdict evidence before creating a grounded preview.
- Must show evidence used, unavailable evidence, warnings/limitations, timestamp, and next observation point.
- Must not invent unsupported conclusions.

### Manual Client Profile `/client-profile`

- Must be treated as advanced/manual diagnostic context editing.
- Must not be the canonical first step.
- Must keep Client Fit framed as non-binding context.

## Forbidden primary UI language

Do not show these terms in normal hero copy, CTAs, or primary cards:

- raw filenames such as `portfolio_xray.json`, `stress_report.json`, `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`;
- raw schema/backend fields such as `schema_version`, `artifact_status`, `can_generate_candidate`, `frontend_review_*`, `true`, `false`, `null`, `n/a`;
- execution/advice phrases such as `buy`, `sell`, `execute`, `trade now`, `must rebalance`, `best portfolio`, `guaranteed improvement`, `suitability approved`.

## Acceptance checklist

- [ ] Landing CTA goes to `/onboarding/sign-in`.
- [ ] Dev bypass remains documented only as local preview support.
- [ ] Platform rail has 8 steps and page headers use matching numbers.
- [ ] `/client-profile` is advanced/manual, not Step 01.
- [ ] Missing/locked states explain the next safe step.
- [ ] Candidate/verdict/report language remains non-binding and evidence-grounded.
- [ ] `docs/design/current_website_structure.md` matches current route blocks and copy.
