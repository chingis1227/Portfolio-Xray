# Business Vision

## Status

This document describes the business vision for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It is a product and business strategy document. It does not replace [SPEC.md](SPEC.md), implementation specs, metric formulas, stress scenario definitions, investment policy logic, configuration schemas, or current code behavior.

For source-of-truth ownership, start with [RULES.md](RULES.md). For workflow, use [WORKFLOW.md](WORKFLOW.md). For shared terminology, use [GLOSSARY.md](GLOSSARY.md). For living target product architecture ideas, see [Diagnostic Product Concept](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md). For current system behavior and canonical technical sources of truth, use [README.md](README.md) and [SPEC.md](SPEC.md).

## Big Idea

Portfolio MRI is a decision support system for portfolio diagnostics, comparison, and explainable action.

## One-Sentence Positioning

Portfolio MRI helps investors and advisors understand real portfolio risk, compare better allocation alternatives, and produce professional decision-ready reports.

The product helps investors and advisors answer a practical question:

> What is really inside this portfolio, where can it break, and what better allocation choices are available...

The system should not behave like a black-box optimizer that claims to know the perfect portfolio. It should behave like a professional portfolio research terminal: diagnose the current allocation, generate candidate portfolios, stress-test them, compare robustness, explain trade-offs, and support a disciplined final decision.

## End State

The long-term product should become a repeatable portfolio decision workflow:

```text
Input portfolio
-> Diagnose real exposures and hidden risks
-> Stress-test current allocation
-> Generate candidate portfolios
-> Backtest and stress-test candidates
-> Compare robustness and trade-offs
-> Select or reject changes
-> Produce client-ready explanation
-> Monitor what changed over time
```

The end-state product should feel closer to an institutional portfolio review desk than a simple allocation calculator.

## User Value

The core value is clarity under uncertainty.

Users should get:

- A clear view of what they actually own.
- A diagnosis of hidden concentrations and weak hedges.
- A realistic view of crisis behavior.
- A menu of alternative allocations.
- A comparison of return, risk, drawdown, stress loss, robustness, and turnover.
- A plain-language explanation of why one portfolio is preferable to another.
- A concrete rebalance or no-trade recommendation.
- A professional report suitable for review, client meetings, or decision records.

## Target Audience

### Private Investors / HNWI

Investors with meaningful portfolios who want professional-grade analysis without building an internal research stack.

Typical needs:

- Understand real portfolio risk.
- Detect hidden equity, duration, credit, or liquidity concentration.
- Compare current allocation against stronger alternatives.
- Receive an investment report they can understand and trust.

### Family Offices / Wealth Managers

Teams that need repeatable, explainable diagnostics across client portfolios.

Typical needs:

- Standardized portfolio reviews.
- Client-ready reporting.
- Faster explanation of risk and rebalance rationale.
- White-label or advisory-facing output.

### Investment Advisors

Advisors who need to prepare for client meetings with rigorous but understandable portfolio analysis.

Typical needs:

- Pre-meeting portfolio diagnostics.
- Professional PDF-style reports.
- Better explanation of why a rebalance is or is not recommended.
- Clear trade-off language.

### Sophisticated Retail Investors

Advanced users who already use Portfolio Visualizer, Koyfin, Excel, or Python.

Typical needs:

- Deeper factor and stress diagnostics.
- More transparent assumptions.
- Better portfolio comparison tooling.
- Macro and regime context.

## Customer Pain

Current portfolio analysis is often fragmented:

- Holdings may look diversified while behavior is concentrated.
- Investors often know weights but not risk contribution.
- Stress behavior is unclear until a crisis happens.
- Optimizers produce allocations without enough explanation.
- Backtests can look good while hidden tail risk remains.
- Advisors spend too much time turning analytics into client-friendly language.
- Reports often show metrics but do not help users make a decision.

The product opportunity is to connect diagnostics, candidate generation, stress testing, comparison, and explanation into one workflow.

## Value Proposition

### For Investors

> Get an institutional risk X-ray of your portfolio, understand where it can break, and compare better allocation alternatives before making a decision.

### For Advisors

> Generate professional portfolio diagnostics and rebalance explanations before every client meeting.

### For Wealth Managers / Family Offices

> Standardize portfolio review, stress testing, candidate comparison, and client reporting across portfolios.

### Internal Positioning

> Portfolio Visualizer, but deeper, more diagnostic, more explainable, and more decision-oriented.

This is internal shorthand, not necessarily the public slogan.

## Core Use Cases

### 1. Portfolio Health Check

The user uploads or defines a portfolio and receives:

- Asset allocation.
- Risk and return metrics.
- Risk contribution.
- Factor exposure.
- Hidden risk diagnosis.
- Stress scorecard.
- Plain-language portfolio commentary.

### 2. Crisis Readiness Review

The user wants to know how the portfolio might behave in bad markets.

Outputs:

- Historical crisis replay.
- Synthetic stress scenarios.
- Worst scenario.
- Loss contributors.
- Hedge gap.
- Mandate pass / fail where applicable.

### 3. Candidate Portfolio Comparison

The system generates or imports alternative portfolios and compares them.

Examples:

- Current vs optimized.
- Current vs Risk Parity.
- Current vs Minimum CVaR.
- Policy portfolio vs benchmark variants.

Outputs:

- Return/risk comparison.
- Drawdown comparison.
- Stress loss comparison.
- Robustness comparison.
- Trade-off explanation.

### 4. Rebalance Decision Support

The system determines whether a rebalance is worth doing.

Outputs:

- Target weights.
- Buy / sell / hold.
- Turnover.
- Expected risk improvement.
- Cost or friction estimate where available.
- No-trade recommendation when improvement is too small.

### 5. Advisor Client Report

An advisor generates a professional report before a client meeting.

Outputs:

- Portfolio diagnosis.
- Main risks.
- Stress behavior.
- Alternative comparison.
- Recommendation rationale.
- Client-friendly commentary.

### 6. Ongoing Monitoring

The system tracks what changed since the last review.

Outputs:

- Risk score change.
- Worst stress scenario change.
- Top risk contributor change.
- Macro regime change.
- New mandate breach.
- Rebalance trigger.

Status:

This is a target product workflow. Full monitoring behavior is TBD.

## Product Differentiation

The product should differentiate through:

- Diagnostic-first workflow, not optimizer-first workflow.
- Explicit separation between current implementation, target concept, and canonical specs.
- Portfolio X-Ray language that explains hidden exposures and real risk sources.
- Stress and robustness comparison across candidate portfolios.
- Strong explainability: why a portfolio wins, loses, or should not be traded.
- Professional reporting suitable for investors, advisors, and wealth managers.
- Practical action layer: target weights, trade deltas, turnover, and no-trade logic.

## Monetization

Monetization is TBD and should stay lightweight until the product shape is clearer.

Plausible models:

- Individual subscription for sophisticated retail investors and HNWI.
- Advisor subscription for recurring client reports and meeting preparation.
- Wealth manager / family office plan for multi-portfolio diagnostics and white-label output.
- One-time paid portfolio reports.
- API or white-label licensing for platforms.

Open questions:

- Pricing levels are TBD.
- Free tier scope is TBD.
- Whether the product is primarily self-serve SaaS, advisor tool, or API-first is TBD.
- Regulatory positioning and disclaimers are TBD.

## Business Direction

Near-term direction:

- Make the product understandable to a new developer, AI agent, or product collaborator.
- Stabilize documentation around product concept, technical specs, and current implementation.
- Keep the current optimizer/reporting engine reliable.
- Improve portfolio comparison and explanation layers.

Mid-term direction:

- Turn existing analytics into a clearer candidate comparison workflow.
- Build a stronger action layer: rebalance, no-trade, turnover-aware explanation.
- Formalize Portfolio Health Score and Robustness Score.
- Add assumption sensitivity and model risk diagnostics as decision-quality tools.
- Improve client-facing report structure and language.

Long-term direction:

- Become a full portfolio decision system for investors and advisors.
- Support recurring monitoring and decision journaling.
- Enable advisor/team workflows.
- Potentially support white-label reporting and API integration.

## Final Business Goal

The final business goal is to create a trusted portfolio decision platform that helps users make more disciplined, transparent, and defensible investment decisions.

Success means the product can consistently answer:

- What is inside the portfolio...
- Where is the real risk...
- How does the portfolio behave under stress...
- Which alternatives are better or worse...
- What trade-off does the user accept...
- What action should be taken, if any...
- How can the decision be explained professionally...

## Success Indicators

Potential success indicators:

- Users can understand portfolio risk without reading raw tables.
- Advisors can prepare client-ready reports faster.
- Users can compare multiple portfolio candidates in one workflow.
- Recommendations include both action and no-trade outcomes.
- Reports are clear enough to support real investment discussions.
- The system is trusted because it exposes assumptions, model risk, and uncertainty.

Metrics are TBD, but may include:

- Time to produce a portfolio review.
- Number of portfolios analyzed per user or advisor.
- Report export frequency.
- Candidate comparison usage.
- Rebalance recommendation acceptance.
- Retention after first report.
- Advisor/team adoption.

## Non-Goals

The product should not be positioned as:

- A guarantee of future performance.
- A fully automated investment manager.
- A black-box allocation oracle.
- A replacement for the canonical implementation specs.
- A reason to change formulas, scenarios, or policy logic without separate specification and verification.

## Relationship To Current Project

The current project already contains a substantial analytics and reporting engine. This business vision explains why the system exists and where it should go.

Business Vision does not override specs or code. If this document conflicts with canonical technical specs or current implementation behavior, the specs and code remain authoritative until a separate implementation change is planned, documented, and verified.

Current implementation details remain governed by:

- [RULES.md](RULES.md)
- [WORKFLOW.md](WORKFLOW.md)
- [README.md](README.md)
- [SPEC.md](SPEC.md)
- [DATA.md](DATA.md)
- [OUTPUTS.md](OUTPUTS.md)
- [GLOSSARY.md](GLOSSARY.md)
- [TESTING.md](TESTING.md)
- [Diagnostic Product Concept](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md)
- [Portfolio Construction Policy](docs/specs/portfolio_construction_policy.md)
- [Metrics Specification](docs/specs/metrics_specification.md)
- [Stress Testing Spec](docs/specs/stress_testing_spec.md)
- [PLANS.md](PLANS.md)
- [AGENTS.md](AGENTS.md)
