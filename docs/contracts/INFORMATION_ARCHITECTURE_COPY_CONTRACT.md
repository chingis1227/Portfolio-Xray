# Information Architecture and Copy Contract

Status: **active product UI contract**.

This document governs Portfolio MRI user-facing information architecture and copy discipline across platform routes. It exists because product guardrails such as diagnosis-first, current-portfolio-first, and decision-support-only are necessary, but they must shape the UI structure rather than appear repeatedly as defensive labels.

## Core rule

Product guardrails are authoring constraints, not repeated primary UI copy.

Primary surfaces must answer the user's next question first:

1. Main finding or task.
2. Why it matters.
3. A concise evidence cluster.
4. The next action.
5. Advanced detail below or behind disclosure.

Do not use hero areas, top cards, route chrome, or primary CTAs to repeatedly reassure the user that Portfolio MRI is not an optimizer, not advice, not a rebalance instruction, or current-only. Those boundaries remain true, but the visible UI should communicate them through route order, neutral verbs, blocked states, and final evidence review.

## Primary surface restrictions

Primary UI surfaces include route heroes, top cards, shared platform header metadata, first-read action panels, and visible summary strips.

Primary surfaces must not show defensive phrases such as:

- `current only`, `current portfolio first`, or `scope: current`;
- `not a recommendation`, `not a rebalance`, or `not advice`;
- `before any candidate`, `before testing a candidate`, or `candidate testing` as generic guardrail copy;
- `diagnostic only` as a headline or status;
- repeated generic `evidence available`, `evidence quality`, or review-status badges.

Allowed exceptions:

- blocked, failed, or locked states may explain the concrete missing prerequisite and next step;
- final Verdict and Report may explain evidence limitations when directly tied to the displayed conclusion;
- advanced disclosures may include methodology, limitations, provenance, and safety boundaries;
- docs, tests, and internal code comments may state guardrails clearly.

## Screen rhythm

Each analytical route should have one dominant answer and one primary evidence cluster. Do not stack multiple components that restate the same metric or guardrail in different words.

Use this route rhythm:

- Portfolio Input: define the portfolio and show readiness.
- Diagnosis: state the main diagnosis, concise evidence, and Stress Lab next action.
- Stress Lab: show stress failure mode, drivers, and next route.
- Client Fit: show profile fit as context without overriding diagnosis.
- Hypothesis: select and prepare one test.
- Comparison: compare current and generated test evidence.
- Verdict: show the grounded decision verdict.
- Report: summarize the grounded review.

## Badge and status discipline

Badges are for specific risk severity, blocked/unavailable states, or compact materiality markers. Do not use them as legal disclaimers. A screen should normally have no more than one generic evidence-quality marker in the first-read area, and often none if evidence quality is already represented in the evidence strip or advanced detail.

Shared platform chrome must stay quiet. It may show route, portfolio label, currency, holding count, and data-window availability. It must not promote staged execution states such as `partial` into the main header metadata.

## Public technical-leakage discipline

Primary UI surfaces and public explanation cards must never expose raw backend, artifact, JSON, factory, lineage, or internal step-status language. This includes raw strings such as `factory step status:succeeded`, `factory profile id:explicit list`, `diff.supporting`, `Previous result ignored`, snake_case stage names, artifact filenames, JSON field paths, or success-status fragments.

When backend evidence is incomplete, stale, or degraded, public copy must translate that state into client-readable language, for example:

- "Some supporting comparison evidence is incomplete."
- "Earlier evidence was skipped because it did not match the active review."
- "Success criteria were not returned for this test."

Raw provenance may appear only inside an explicit developer/debug provenance disclosure. Collapsed user-facing limitations may describe methodology or evidence quality, but they must still use product-language labels rather than file names, schema keys, or backend IDs.

## Regression enforcement

The frontend static copy gate is:

```powershell
cd frontend
npm.cmd run test:copy
```

This test protects key route primary surfaces from defensive copy drift. If a future feature needs an exception, update this contract first and keep the exception tied to a concrete blocked, failed, final-verdict, or advanced-detail state rather than broad hero copy.
