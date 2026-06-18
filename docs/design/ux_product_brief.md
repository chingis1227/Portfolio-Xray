# UX Product Brief

Status: UX foundation for the Portfolio MRI frontend. This document implements the no-code foundation requested by `docs/audits/2026-06-18_ux_ui_product_audit_sprint.md` and supports the current contracts in `DESIGN.md`, `docs/contracts/SCREEN_CONTRACTS.md`, and `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`.

## Product promise

Portfolio MRI is an investment decision room. It helps a user understand the current portfolio first, review stress evidence, add non-binding Client Fit context, test one bounded diagnostic alternative, compare trade-offs, and read a cautious decision-support verdict. It is not a trading terminal, optimizer cockpit, suitability approval workflow, or PDF-first report product.

## Primary and secondary users

The primary launch user is a financially literate self-directed investor who owns a portfolio and wants a defensible risk review before considering changes. This user may understand holdings, weights, drawdowns, and basic risk language, but should not need backend, quant, or artifact vocabulary to complete the journey.

Secondary users are advisors, analysts, and internal demo operators. The UI may support their need for evidence and traceability through secondary or collapsed detail, but the first-read experience stays plain-language and current-portfolio-first.

## User jobs

1. Understand the product: decide whether this is a diagnostic review, not a trading or optimizer tool.
2. Enter the current portfolio: provide holdings, weights, and currency with clear validation.
3. Understand current risk: see the dominant current-portfolio diagnosis before any candidate test.
4. Trust the evidence: review stress behavior, evidence quality, and limitations.
5. Add personal context: understand whether the evidence fits the stated profile without treating that as suitability approval.
6. Choose one diagnostic test: see why one test path is worth generating and what success would mean.
7. Compare trade-offs: understand what improves, worsens, or remains uncertain versus the current portfolio.
8. Interpret the verdict: read non-binding decision support with limitations and what would change the conclusion.
9. Save or explain: create a grounded report preview that summarizes selected evidence without inventing recommendations.

## Stage-by-stage anxieties and product responses

- Landing: the user may ask whether Portfolio MRI will tell them what to buy. The response is diagnosis-first decision support.
- Sign-in and onboarding: the user may worry personal answers are used as suitability approval. The response is diagnostic context only.
- Portfolio Input: the user may fear ticker or weight mistakes. The response is inline validation and clear recovery.
- Diagnosis: the user may expect an immediate rebalance answer. The response is current-portfolio diagnosis before alternatives.
- Stress Lab: the user may see stress evidence as advanced analytics. The response is a focused explanation of why the current diagnosis matters.
- Client Fit: the user may overread alignment as approval. The response is explicit non-binding context.
- Hypothesis: the user may think a candidate is a recommendation. The response is diagnostic-test wording and success criteria.
- Comparison: the user may look for a winner. The response is trade-off evidence only.
- Verdict: the user may treat the verdict as instruction. The response is non-binding interpretation and limitations.
- Report: the user may expect a polished PDF product. The response is grounded preview only.

## Terminology rules

Use `diagnostic test`, `test path`, `test setup`, and `generated test candidate` in primary UI. Keep `candidate` only where it is part of an established product label, backend field, route contract, or a phrase that clearly says it is a diagnostic test candidate.

Use `current portfolio`, `Portfolio Diagnosis`, `Stress Test Lab`, `Client Fit context`, `trade-off comparison`, `decision-support verdict`, and `grounded report preview`.

Avoid primary UI terms such as backend, artifact, JSON, factory, Review ID, stale downstream, selected hypothesis, best portfolio, winner, trade now, buy, sell, execute, guaranteed improvement, suitability approved, and must rebalance.

## Decision-support boundary

Every generated or interpreted result is diagnostic and non-binding. Client Fit is one context input, not approval. A diagnostic test candidate is generated for comparison only. Comparison is not a verdict. Verdict is not trade advice. Report preview summarizes evidence; it does not invent new conclusions.

## UX success criteria

A first-time user should be able to explain, without help, what the current step is asking them to decide, why the next step is safe, what evidence is missing when a route is blocked, and why the product is not issuing a trade instruction. Each route should have one dominant screen job and one primary next action.
