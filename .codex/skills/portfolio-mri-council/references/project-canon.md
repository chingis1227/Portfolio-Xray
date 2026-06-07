# Portfolio MRI council canon

Use this reference only when the task needs extra Portfolio MRI-specific framing beyond the main skill instructions.

## Current product truth

Treat this as the canonical product direction:

```text
Input portfolio
-> Portfolio X-Ray
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary / grounding
-> Monitoring / What Changed
```

Important: `AGENTS.md` also notes supporting layers often discussed around this flow:

- Hidden Risk Detector
- Weakness Map
- Hedge Gap Analysis

Use repository truth first if there is any mismatch between shorthand names and actual code/docs.

## What the council should keep checking

Pressure-test these questions repeatedly:

1. Does this help the user make a better decision?
2. Is the next action obvious?
3. Does this overload the MVP?
4. Is there a clean link between diagnosis and action?
5. Can the verdict be trusted?
6. Does AI Commentary explain evidence instead of inventing conclusions?

## Expert lenses

### Investment-decision experts

- **Portfolio Manager**: clarity of diagnosis, link to action, usefulness of verdict
- **Risk Manager**: concentration, drawdown, tail risk, liquidity, turnover, risk contribution
- **Macro / Stress Analyst**: regime logic, real break scenarios, whether stress confirms X-Ray hypotheses
- **Quant / Model Skeptic**: data quality, robustness, false precision, optimizer overreach
- **Execution Advisor**: minimum practical next step, MVP fit, workflow simplicity

### Product-strategy experts

- **Product Strategist**: core product vs advanced layer, sequence, value proposition
- **UX Simplifier**: decision-ready outputs, user comprehension, excess screens and jargon
- **MVP Operator**: fastest credible validation path, manual-first shortcuts, what to delay
- **Commercial / GTM Skeptic**: pain sharpness, strongest wedge, pay-for value
- **Technical Scope Controller**: complexity control, dependency risk, architecture sprawl

### Institutional-trust experts

- **Institutional PM**: professional defensibility, signal-to-verdict continuity
- **Research Reviewer**: evidence sufficiency, confidence labels, conflicting signals
- **Risk Governance Reviewer**: overtrading risk, guardrails, limitations disclosure
- **Compliance / Suitability Skeptic**: recommendation risk, disclaimers, cautious phrasing
- **Audit Trail Architect**: traceability, evidence refs, rejected alternatives, assumption capture

## Typical verdict vocabulary

Prefer explicit verdicts such as:

- `build`
- `build now`
- `defer`
- `simplify`
- `test`
- `test manually`
- `remove`
- `reject`
- `no-trade`
- `evidence insufficient`
- `trust-ready`
- `needs guardrails`
- `too black-box`

## Anti-patterns

Call out these mistakes when they appear:

- building candidate machinery before the problem is clearly diagnosed
- adding analytics without changing the decision
- presenting optimizer output as if it were the decision
- mixing ordinary risk contribution with stress loss contribution
- pretending weak evidence is high-confidence
- turning AI Commentary into opinion detached from evidence
- expanding MVP scope before one strong workflow is proven
