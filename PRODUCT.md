# Product

This document owns Portfolio MRI product direction, user goals, Core MVP boundaries, advanced/later
classification, product language, and product non-goals. It does not override `SPEC.md`,
`OUTPUTS.md`, `DATA.md`, `TESTING.md`, `docs/contracts/*.md`, `docs/specs/*.md`, formulas, schemas,
runtime behavior, or code.

Keep this file product-facing and maintainable. Do not duplicate long implementation details,
schemas, formulas, artifact inventories, or command matrices here. Link to the owning source of
truth instead.

## Product Summary

Portfolio MRI is a diagnosis-first, current-portfolio-first investment decision-support product.

The user starts by submitting a current portfolio, not by choosing an optimizer. The product explains
what the user owns, where risk is hidden, how the portfolio behaves under stress, how that evidence
fits non-binding client context, what problem is worth testing, and whether a selected candidate
hypothesis justifies rebalance review, no action, another test, or an evidence-insufficient verdict.

Canonical Core MVP flow:

```text
Input Portfolio
-> Portfolio Diagnosis
-> Stress Test Lab
-> Client Fit Check
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Candidate Generation
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary / grounding
-> Monitoring / What Changed
```

The cross-step product contract is
[`docs/contracts/PRODUCT_FLOW_CONTRACT.md`](docs/contracts/PRODUCT_FLOW_CONTRACT.md). Current
implementation status is owned by `SPEC.md`, `OUTPUTS.md`, detailed specs, contracts, and code.

## Product Principles

- Diagnosis before action.
- Current portfolio first.
- Problems before methods.
- Candidate equals hypothesis, not recommendation.
- Guided, not prescriptive.
- No-trade is a valid outcome.
- Missing, stale, or partial evidence must be visible.
- Client Fit is non-binding context, not suitability approval.
- AI explains grounded evidence; code and specs own calculations.
- Advanced capabilities should support the core journey, not replace it.

These principles are product-authoring constraints. They should shape route order, screen hierarchy,
and action labels; they should not be repeated as defensive badges, hero disclaimers, or primary
card copy. User-facing information architecture and copy discipline are governed by
[`docs/contracts/INFORMATION_ARCHITECTURE_COPY_CONTRACT.md`](docs/contracts/INFORMATION_ARCHITECTURE_COPY_CONTRACT.md).

## Primary Users

### Independent Advisor / Financial Advisor

Goal: prepare a professional portfolio risk review before a client conversation.

Expected value:

- clear current-portfolio diagnosis;
- stress behavior and hidden-risk explanation;
- reasonable improvement hypotheses;
- current-vs-candidate trade-off summary;
- non-binding verdict and client-friendly commentary.

### Sophisticated Self-Directed Investor

Goal: understand the real risk of a personal portfolio and decide whether changing allocation is
worth the cost and uncertainty.

Expected value:

- institutional-style diagnosis;
- stress testing;
- plain-language explanation of what matters;
- candidate test only when useful;
- decision-ready conclusion.

Family offices, wealth managers, multi-client operators, and white-label users remain possible
future packaging, but they are not the default Core MVP audience unless strategy changes.

## Core MVP Behavior

### Input Portfolio

The MVP asks for factual current-portfolio inputs: instruments, current weights, and investor
currency. Advanced mandate targets, tax settings, custom constraints, liquidity needs, and optimizer
parameters are not required to diagnose the portfolio.

### Portfolio Diagnosis

Diagnosis explains the current portfolio before alternatives appear. It should show allocation,
concentration, risk/return behavior, hidden exposure, factor/risk concentration, weakness, and data
trust signals. Diagnosis alone must not issue a trade recommendation.

### Stress Test Lab

Stress Test Lab explains where the current portfolio can break and which assets, exposures, or
missing hedges drive that behavior. It must disclose unavailable, partial, or stale evidence instead
of fabricating stress facts.

### Client Fit Check

Client Fit V1 compares portfolio evidence with the provided profile as bounded context. It may show
fit, watch, breach, conflict, not-provided, or evidence-insufficient states. It must not be described
as suitability approval, trade advice, or a reason to hide material portfolio issues.

### Problem Classification and Candidate Launchpad

Problem Classification turns diagnosis and stress evidence into a small set of understandable
problems and test paths. Candidate Launchpad cards are hypotheses to test. They are not portfolios,
weights, recommendations, or executed factory runs.

### Portfolio Alternatives Builder and Candidate Generation

The Builder validates the selected hypothesis and prepares a candidate test setup. Candidate
Generation is an explicit diagnostic attempt. A generated candidate is not automatically better than
the current portfolio and is not a trade order.

### Current vs Candidate Comparison

Comparison should show what improved, worsened, stayed similar, or could not be evaluated. It should
make trade-offs visible before any verdict language appears.

### Decision Verdict

Decision Verdict is non-binding decision support. Valid outcomes include keep current, no material
rebalance, rebalance review, test another candidate, candidate failed/infeasible, and evidence
insufficient. A rebalance-review verdict means evidence is material enough for review; it does not
mean execute a trade.

### AI Commentary / Grounding

AI Commentary is grounded explanation. In the current product boundary, the grounding context
explains deterministic evidence and gaps; it must not invent calculations, statuses, scenarios,
recommendations, or verdict evidence.

### Monitoring / What Changed

Monitoring / What Changed is a light follow-up summary when prior evidence exists. It may explain
changed risks or retest triggers, but it does not create scheduler behavior, broker alerts, or
automatic trades.

## Current Frontend Route Reality

The canonical new-user frontend route chain is:

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

Returning signed-in users with completed onboarding and saved workspace, portfolio, draft, or
review history may branch from sign-in/loading to `/workspace`. `/workspace` restores saved account
context and compact history without running diagnosis, refreshing market data, generating
candidates, comparing portfolios, or producing verdict/report artifacts automatically.

`/onboarding/goals` is a compatibility-only redirect to `/onboarding/investor-type`, retained for
older links and not part of the current product journey. `/client-profile` is an advanced/manual
Client Fit editor, not the normal onboarding entry step. `/sandbox/components` and developer/debug
provenance views are local review/debug surfaces, not product journey routes.
Route responsibilities are owned by
[`docs/contracts/SCREEN_CONTRACTS.md`](docs/contracts/SCREEN_CONTRACTS.md) and
[`frontend/README.md`](frontend/README.md).

## Core MVP vs Advanced / Legacy

### Core MVP

- Current portfolio input.
- Portfolio Diagnosis.
- Stress Test Lab.
- Client Fit Check.
- Problem Classification.
- Candidate Launchpad.
- Selected candidate test setup and generation.
- Current-vs-candidate comparison.
- Decision Verdict.
- Grounded AI Commentary context.
- Light Monitoring / What Changed.

### Advanced / Later

These may be useful, and some may exist in code or generated artifacts, but they are not the current
Core MVP product flow unless promoted by current specs and implementation:

- Portfolio Health Score or Robustness Scorecard as the main answer.
- Macro Dashboard / Macro Overlay.
- Full multi-candidate ranking or optimizer arena.
- Assumption Sensitivity, Pareto / Dominance, Regret Analysis, and Model Risk Diagnostics as primary
  screens.
- Full Action Plan / Rebalancing Advisor.
- Full Decision Journal.
- Advanced monitoring, full portfolio-health monitoring, macro-regime monitoring, and multi-client
  monitoring workspace.
- Crisis Replay UI and What Happens If simulator UI.
- Client Fit suitability approval.
- Asset Diagnostics, Max Sharpe, tax-aware optimization, turnover-aware optimizer objective,
  tactical tilt, full custom constraints UI, and multi-client workspace.
- Polished PDF report product as the default output path.

Advanced does not mean broken or deleted. It means not the default user-facing Core MVP journey.

### Legacy / Compatibility

Legacy policy optimization, older report sidecars, explicit export/PDF flows, and full candidate
factory batches may remain available for compatibility, research, or backend evidence. They must not
be presented as the default product story unless current specs and code promote them.

## Product Language

Use:

- "diagnosis", not "optimization result", for the current portfolio review;
- "candidate test" or "hypothesis", not "recommended portfolio";
- "rebalance review", not "trade now";
- "keep current" or "no material rebalance", not "failure";
- "evidence insufficient", not fabricated certainty;
- "Client Fit context", not suitability approval.

Do not promise perfect weights, guaranteed risk reduction, tax suitability, trade execution, or
advisor replacement.

## User Outputs

Target core user outputs are:

- portfolio diagnosis summary;
- top hidden risks;
- stress behavior summary;
- Client Fit context;
- reasonable paths to test;
- selected candidate test result;
- current-vs-candidate comparison;
- trade-off explanation;
- Decision Verdict;
- grounded commentary;
- light monitoring or retest context when available.

Output files and generated-vs-source boundaries are owned by `OUTPUTS.md`.

## Product Non-Goals

Portfolio MRI should not:

- start with a giant optimizer menu;
- always recommend trading;
- hide model limits or data gaps;
- treat AI as a calculation engine;
- convert Client Fit into suitability approval;
- make advanced research modules mandatory for the Core MVP;
- delete legacy or advanced backend capability only because it is not the target product flow.

## Open Product Questions

- Which implemented artifacts should be promoted into the first fully interactive product UI?
- How many reasonable test paths should the MVP show by default?
- Which candidate methods belong in Core MVP versus advanced/research mode?
- What is the minimum evidence threshold for no material rebalance?
- Which monitoring signals belong in MVP versus a later advisor workspace?

## Source-Of-Truth Relationship

For conflicts, use this order:

1. `SPEC.md`, `OUTPUTS.md`, `DATA.md`, `TESTING.md`, contracts, detailed specs, and code for current
   implementation behavior.
2. `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for cross-step product flow.
3. This file for product direction and boundaries.
4. Historical audits, completed ExecPlans, archived legacy docs, and concept docs for traceability
   only.

Product concepts become binding only after the owning source-of-truth docs, implementation, and
verification are updated through the normal workflow.
