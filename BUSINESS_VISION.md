# Business Vision

This document is part of the active project documentation after the documentation migration. It describes target direction and operating context, but it does not override `SPEC.md`, `RULES.md`, `OUTPUTS.md`, `DATA.md`, `TESTING.md`, `docs/specs/*.md`, formulas, stress scenario definitions, optimizer policy, generated-output contracts, or current code behavior. Current implementation claims must be verified against the canonical specs and code.

## 1. Business Positioning

Portfolio MRI / Portfolio X-Ray is a portfolio diagnostics and investment decision-support system.

It helps advisors and sophisticated investors understand what is really inside a portfolio, where
risk is concentrated, how the portfolio may behave under stress, which alternative allocation
hypothesis is worth testing, and whether a rebalance is justified.

The product is not positioned as a black-box optimizer. Optimizers and candidate builders may exist
inside the system, but the business value is the disciplined decision workflow:

```text
Input portfolio
-> Portfolio X-Ray
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary
-> Monitoring / What Changed
```

## 2. One-Sentence Positioning

Portfolio MRI helps advisors and serious self-directed investors turn a current portfolio into a
diagnosis, a stress-tested improvement hypothesis, and a defensible rebalance or no-trade decision.

## 3. Core Customer Question

The product should answer one practical question:

> What is really inside this portfolio, where can it break, what reasonable alternative should be
> tested, and should I rebalance or leave the portfolio unchanged?

This question is more important than showing every available metric or every possible optimization
method.

## 4. Primary ICP

### Independent Investment Advisors / Financial Advisors

The primary customer is an independent investment advisor or financial advisor who manages or
advises client portfolios of roughly `$250k-$5m`.

They need a fast, professional, client-ready portfolio risk review before meetings.

### Advisor Pain

- They need to understand client portfolio risk quickly.
- They need to explain hidden exposures, stress behavior, hedge gaps, and trade-offs in plain
  language.
- They need to justify a rebalance, partial rebalance, no-trade recommendation, or further review.
- They need credible reports without building an internal research stack.
- They need a repeatable process that makes the client conversation more professional and
  defensible.

### Advisor Value Proposition

> Generate a professional portfolio risk review before every client meeting: what the client owns,
> where the risk is, where the portfolio may break, what alternative is worth testing, and whether a
> rebalance or no-trade verdict is justified.

## 5. Secondary ICP

### Sophisticated Self-Directed Investors

The secondary customer is a serious self-directed investor with a meaningful portfolio, roughly
`$100k-$1m+`, who already uses broker analytics, Portfolio Visualizer, Koyfin, Excel, Python, or
similar tools.

They want institutional-style diagnostics without building their own analytics platform.

### Self-Directed Investor Pain

- They see tickers, weights, and performance, but not the real economic risk.
- They do not know whether the portfolio is truly diversified or just visually diversified.
- They do not know how the portfolio may behave in equity shocks, rates shocks, inflation shocks,
  credit stress, liquidity stress, or recession-like scenarios.
- They may see many metrics but still lack a decision-ready conclusion.
- They do not know whether changing the portfolio is worth the turnover, cost, and model risk.

### Self-Directed Investor Value Proposition

> Get an institutional-style Portfolio X-Ray, stress test, and rebalance/no-trade decision support
> for a serious self-managed portfolio.

## 6. Secondary / Later Segments To Preserve

The existing documentation also mentions HNWI, family offices, wealth managers, and broader
portfolio-review users. These should not be deleted.

Migration recommendation:

- Preserve them as secondary, later, or enterprise segments.
- Do not make them the primary ICP unless the commercial strategy explicitly changes.
- Do not remove white-label, multi-client, or family-office reporting concepts; classify them as
  advanced/later if they are not part of the MVP.

## 7. Top Client Pains

### Pain 1 — "I do not understand what I really own"

The user sees a list of funds, stocks, cash, and weights, but does not understand the real economic
exposure.

The portfolio may contain duplicated risk, hidden factor exposures, concentrated risk contribution,
or assets that look different but behave similarly.

Client-language version:

> I see the holdings, but I do not understand what real bet I am making.

### Pain 2 — "I do not know where the real risk is"

The portfolio can look diversified while the actual risk is dominated by equity beta, duration,
credit risk, currency exposure, weak hedge behavior, liquidity risk, or concentrated risk
contributors.

Client-language version:

> I thought the portfolio was diversified, but I do not know what will actually hit it in a bad
> market.

### Pain 3 — "I do not know what to do"

Even if the user sees metrics, charts, and backtests, they may not know whether to keep the current
portfolio, rebalance, test another candidate, make a minor adjustment, or wait because the evidence
is insufficient.

Client-language version:

> I do not know whether to change the portfolio, which alternative to test, or whether it is better
> to do nothing.

## 8. Product Philosophy

### Diagnosis Before Action

Every investment action should start with understanding the current portfolio: assets, weights,
risk contributors, hidden exposures, factor sensitivity, diversification quality, stress behavior,
and hedge gaps.

### Current Portfolio First

The product starts from the user's actual current portfolio. The system should diagnose the
portfolio as given before suggesting alternatives.

### Candidate Portfolio As Hypothesis

A candidate is not "the best portfolio." It is an investment hypothesis created to test whether a
specific diagnosed problem can be improved.

Examples:

- Reduce volatility.
- Reduce drawdown risk.
- Improve diversification.
- Improve crisis resilience.
- Compare against a simple benchmark.

### Guided, Not Prescriptive

The product should guide the user through evidence and trade-offs. It should not pretend to replace
professional judgment, tax analysis, suitability review, liquidity planning, or final advisor/client
responsibility.

### No-Trade Is A Valid Verdict

If a candidate improves the portfolio only modestly, requires high turnover, increases model risk,
or depends on weak data, the correct conclusion may be:

> No material rebalance recommended.

Doing nothing can be a disciplined investment decision.

### AI Commentary Is An Explanation Layer

AI may help translate deterministic calculations and generated JSON evidence into clear language.
AI should not be described as the source of metrics, stress results, data-quality statuses,
candidate freshness, optimizer readiness, or investment verdict evidence.

## 9. MVP Business Workflow

The target MVP should feel like a guided portfolio review:

1. User uploads or enters the current portfolio.
2. System runs Portfolio X-Ray.
3. System runs Stress Test Lab.
4. System classifies the most important portfolio problems.
5. System identifies 2-3 reasonable paths to test.
6. User selects one path or benchmark test.
7. System generates one selected candidate.
8. System compares current portfolio vs candidate.
9. System explains what improves, what worsens, turnover/cost implications, and evidence quality.
10. System produces a Decision Verdict.
11. System generates AI Commentary and a decision-ready report.
12. System records what should be monitored next.

## 10. MVP Verdict Types

The product should support several business-level verdicts:

- Keep current portfolio.
- Rebalance to selected candidate.
- Partial rebalance / minor adjustments.
- Candidate improves risk but the trade-off is too expensive.
- Test another candidate.
- No material rebalance recommended.
- Evidence insufficient due to data quality, model limits, or missing assumptions.

These labels are product direction. Exact current implementation labels and generated JSON fields
require code/spec verification.

## 11. What The Product Sells

The customer is not buying "15 modules" or "perfect weights."

The customer is buying:

- Diagnosis.
- Confidence.
- Hidden-risk visibility.
- Stress readiness.
- A reasonable alternative to test.
- A clear trade-off explanation.
- A defensible decision.
- A client-ready conversation.

For advisors, the economic value is time saved, better client explanation, reduced risk of a poorly
justified rebalance, and a more professional investment review process.

For self-directed investors, the value is institutional-style clarity without having to build the
analytics stack themselves.

## 12. Differentiation

Portfolio MRI should be differentiated by:

- Current-portfolio-first analysis.
- Hidden exposure and real risk diagnosis.
- Stress behavior and hedge-gap explanation.
- Candidate portfolios as hypotheses, not black-box recommendations.
- Current-vs-candidate trade-off analysis.
- No-trade as a serious output.
- Clear separation between deterministic evidence and AI commentary.
- Professional reporting suitable for advisors and serious investors.

Internal shorthand:

> Portfolio Visualizer, but deeper, more diagnostic, more stress-aware, and more decision-oriented.

This is internal positioning, not necessarily final public marketing copy.

## 13. Product Non-Goals

The product should not be positioned as:

- A black-box optimizer.
- A tool that always recommends changing the portfolio.
- A promise of perfect weights or guaranteed improvement.
- A replacement for advisor responsibility, tax analysis, client suitability, or final investment
  judgment.
- An AI system that invents calculations or hidden conclusions.
- A dashboard that overwhelms the user with every metric before answering the main decision
  question.

## 14. Advanced / Later Product Backlog

These are valuable but should not be forced into the core MVP business promise. Do not describe
them as implemented unless verified in `SPEC.md`, `docs/specs/*.md`, or code.

- Macro Risk Dashboard / Macro Overlay.
- Strategy Backtest as a separate block.
- Scenario & Stress Evaluation for Candidates.
- Full multi-candidate ranking / advanced research comparison.
- Out-of-sample / walk-forward analysis.
- Full Crisis Replay UI.
- What Happens If? Simulator.
- Portfolio Health Score / Robustness Scorecard as primary product modules.
- Assumption Sensitivity / Assumption Testing Mode.
- Pareto Frontier / Dominance Check.
- Regret Analysis.
- Model Risk Diagnostics.
- Rebalancing Advisor / Action Plan as full modules.
- Advanced Monitoring / full portfolio health monitoring.
- Macro regime monitoring.
- Advanced breach engine.
- Multi-client monitoring workspace.
- Max Sharpe.
- Custom Constraints.
- Advisor Custom Candidate.
- Tax-aware optimization.
- Turnover-aware optimization objective.
- Tactical Tilt.
- Full custom constraints UI.
- Multi-client workspace / saved workspaces.
- White-label / API integration.
- Full PDF report design.
- Advanced Parameter Builder settings.
- Asset X-Ray / Asset Diagnostics.
- Client-Fit Check / questionnaire.
- Portfolio Archetype Classification is an optional later diagnostic layer that can classify the
  portfolio by behavior, such as Equity Growth Portfolio, Balanced 60/40-like, Credit Carry
  Portfolio, Duration-heavy Defensive, Inflation-sensitive, or Pseudo-diversified Portfolio. It
  should not be part of the core MVP flow until explicitly implemented and approved.

Classify these as `Advanced`, `Later`, or `Requires Review`; do not delete them from project memory.

## 15. Relationship To Current Implementation

This draft describes the target business direction.

Current implementation must still be verified through:

- `SPEC.md`
- `RULES.md`
- `OUTPUTS.md`
- `DATA.md`
- `TESTING.md`
- `docs/specs/*.md`
- current source code and generated artifact contracts

Any statement that a target workflow step is implemented must be checked before being merged into
the current `BUSINESS_VISION.md` or any canonical technical document.

Examples that require code/spec verification before being claimed as current:

- Problem Classification as an implemented module.
- Candidate Launchpad as an implemented product layer.
- User-triggered one-candidate generation as the current default behavior.
- Current-vs-candidate as the only or main implemented comparison mode.
- Decision Verdict replacing current Selection Engine terminology or schemas.
- AI Commentary availability, scope, and source data.

## 16. Success Indicators

Business success should be measured by whether users can:

- Understand the real structure and risk of the current portfolio.
- Identify the top hidden risks or stress vulnerabilities.
- See one reasonable alternative hypothesis and its trade-offs.
- Understand why a rebalance is or is not justified.
- Use the output in a client meeting or personal investment decision.
- Trust that the system distinguishes current evidence from model limits and data-quality gaps.

For advisors, a practical validation question is:

> Would you use this report before a client meeting, and would it save enough time or improve enough
> trust to justify paying for it?

For self-directed investors:

> Does this help you make a clearer keep/rebalance/test-another-candidate decision than your current
> tools?
