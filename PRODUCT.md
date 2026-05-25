# Product

This document is part of the active project documentation after the documentation migration. It describes target direction and operating context, but it does not override `SPEC.md`, `RULES.md`, `OUTPUTS.md`, `DATA.md`, `TESTING.md`, `docs/specs/*.md`, formulas, stress scenario definitions, optimizer policy, generated-output contracts, or current code behavior. Current implementation claims must be verified against the canonical specs and code.

## 1. Product Summary

Portfolio MRI / Portfolio X-Ray is a portfolio diagnostics and investment decision-support product.

The user does not start by choosing an optimizer. The user starts by submitting a current portfolio.
The product diagnoses what is inside that portfolio, where risk is hidden, how it behaves under
stress, what problem should be tested, which candidate hypothesis is reasonable, and whether the
trade-off justifies action.

Target MVP flow:

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

This target flow is product direction. Current implementation status must be checked against
`SPEC.md`, `OUTPUTS.md`, `docs/specs/*.md`, and code before any target step is described as
implemented.

## 2. Product Principles

- **Diagnosis before action.** The system must explain the current portfolio before proposing any
  change.
- **Current portfolio first.** User-supplied current weights are the starting point for the target
  MVP review flow.
- **Problems before methods.** The user should see "reduce drawdown" or "improve diversification"
  before seeing "Minimum Variance" or "Risk Parity."
- **Candidate equals hypothesis.** A candidate portfolio is a testable investment hypothesis, not an
  automatic recommendation.
- **Guided, not prescriptive.** The product guides the user toward a defensible decision; it does
  not pretend to replace advisor responsibility.
- **No-trade is valid.** The correct verdict may be to leave the portfolio unchanged.
- **AI explains, code calculates.** AI Commentary explains deterministic outputs and JSON evidence;
  it does not invent metrics, statuses, stress results, or verdict evidence.
- **Core view before appendix.** The main UX should show the decision-relevant evidence first and
  move advanced metrics to drill-down or appendix views.
- **Current vs target separation.** Product concepts do not override current implementation
  contracts.

## 3. Primary Users

### Independent Investment Advisor / Financial Advisor

Goal:

Prepare a professional, client-ready portfolio risk review before a meeting.

Expected product output:

- Clear portfolio diagnosis.
- Top hidden risks.
- Stress behavior and hedge gaps.
- One or more reasonable improvement hypotheses.
- Current-vs-candidate trade-off explanation.
- Rebalance, no-trade, test-another-candidate, or evidence-insufficient verdict.
- Client-friendly commentary.

### Sophisticated Self-Directed Investor

Goal:

Understand the real risk of a personal portfolio and decide whether changing allocation is worth
the cost and uncertainty.

Expected product output:

- Institutional-style Portfolio X-Ray.
- Stress testing.
- Plain-language explanation of what matters.
- Candidate hypothesis only when useful.
- Decision-ready conclusion.

### Secondary / Later Users

Family offices, wealth managers, HNWI users, multi-client operators, and white-label use cases
remain important but should be treated as secondary, advanced, or later product packaging unless the
business strategy explicitly promotes them.

## 4. Core MVP User Flow

### 4.1 Input Portfolio

User goal:

Submit the current portfolio for diagnosis.

Target MVP inputs:

- Tickers or instruments.
- Current weights.
- Investor currency.

System-level inputs and defaults:

- `analysis_subject = current_portfolio`
- benchmark / base benchmark
- cash proxy
- risk-free source
- FX logic
- market data provider
- calculation windows and quality thresholds

Target UX rule:

Do not overload the first screen with advanced assumptions. The first screen should ask for the
minimum needed to diagnose the current portfolio. System defaults should remain visible in an
assumptions/disclosure area.

Current implementation notes:

- Requires code/spec verification before claiming exact current UI behavior.
- Existing CLI/config fields and `analysis_subject` behavior are governed by current specs and code.

### 4.2 Portfolio X-Ray

User goal:

Understand what the portfolio really contains and where risk lives.

Target sections:

- Asset allocation.
- Asset class / region / currency / risk role breakdown where available.
- Portfolio metrics.
- Risk contribution.
- Factor exposure.
- Hidden exposure / hidden risk detector.
- Risk budget view.
- Weakness map.
- Data trust signals.

Questions answered:

- What do I actually own?
- What is the real economic exposure?
- Which assets dominate risk?
- Where does risk contribution differ from capital weight?
- Are different holdings actually duplicating the same risk?
- Is diversification real or only visual?

Product rule:

X-Ray diagnoses. It does not recommend a rebalance by itself.

### 4.3 Stress Test Lab

User goal:

Understand where the current portfolio may break.

Target sections:

- Synthetic stress scenarios.
- Historical stress scenarios where data supports them.
- Worst scenario.
- Stress loss contributors.
- Assets or sleeves that help offset losses.
- Hedge gap analysis.
- Stress data-quality disclosure.

Questions answered:

- How does the portfolio behave in bad markets?
- Which assets hurt most under stress?
- Which assets help?
- Where is the main hedge gap?
- Which market risks require further testing through a candidate?

Product rule:

Stress Test Lab should show vulnerability and evidence quality. It should not fabricate historical
evidence when data is insufficient.

### 4.4 Problem Classification

User goal:

Translate diagnostics into a small number of actionable improvement directions.

Target problem examples:

- High volatility.
- High drawdown risk.
- High equity beta.
- High concentration.
- Poor diversification.
- Weak hedge behavior.
- Poor rates-up behavior.
- Weak crisis resilience.
- Low return/risk efficiency.
- High turnover required.
- Current portfolio already acceptable.

Target output:

- Top 2-3 diagnosed problems.
- Evidence behind each problem.
- Reasonable paths to test.
- Clear indication when current portfolio is acceptable.

Implementation status:

Problem Classification is target product direction unless verified in current specs/code.

### 4.5 Candidate Launchpad

User goal:

Choose what kind of improvement to test.

Target cards:

- Reduce volatility.
- Reduce drawdown.
- Improve diversification.
- Reduce concentration.
- Improve crisis resilience.
- Improve return/risk balance.
- Compare against simple benchmark.
- Keep current portfolio and monitor.

Target behavior:

- Cards are not portfolios.
- Cards are entry points into the Portfolio Alternatives Builder.
- Each card should explain why it is suggested, using diagnosis and stress evidence.

Implementation status:

Candidate Launchpad is target product direction unless verified in current specs/code.

### 4.6 Portfolio Alternatives Builder

User goal:

Generate a selected candidate portfolio from a chosen hypothesis.

Target simple-mode fields:

- Goal.
- Suggested method, editable by user.
- Constraint preset.
- Max asset weight.
- Optional min asset weight.
- Optional volatility target.
- Rebalancing frequency.
- Transaction cost assumption.
- Generate candidate.

Candidate construction methods may include:

- Equal Weight.
- Equal Weight by Asset Class.
- Risk Parity.
- Hierarchical Risk Parity.
- Minimum Variance.
- Minimum CVaR.
- Maximum Diversification.
- Robust Mean Variance.

Product language rule:

Client-facing UX should emphasize the goal and trade-off, not just the optimizer name.

Advanced settings to keep out of core MVP unless separately approved:

- Full asset-class bounds.
- Custom risk budgets.
- Robust MV lambda controls.
- Advanced CVaR controls.
- Estimator selection.
- Covariance method selection.
- Expected return method selection.
- Leverage / short settings.
- Tax-aware settings.
- Complex universe builder.

Implementation status:

On-demand user-triggered candidate generation is target direction unless verified in current
implementation. Existing automatic or batch candidate capabilities should be preserved and
classified as current capability, advanced mode, research mode, or legacy as appropriate.

### 4.7 Candidate Shortlist / Comparison Arena

User goal:

See generated hypotheses in one place.

Target behavior:

- Zero candidates: diagnosis-only state.
- One candidate: current portfolio vs candidate.
- Two or more candidates: shortlist comparison.

Product rule:

The target core UX compares only candidates the user created or explicitly selected. It should not
force the user into a full 16-candidate research table by default.

Implementation status:

Requires code/spec verification before claiming shortlist behavior exists.

### 4.8 Current vs Candidate Comparison

User goal:

Understand whether the selected candidate is meaningfully better and at what cost.

Target comparison dimensions:

- Return / risk.
- Volatility.
- Max drawdown.
- Tail risk where available.
- Stress loss.
- Worst scenario.
- Risk contribution and concentration.
- Factor exposure changes.
- Hedge gap changes.
- Turnover.
- Transaction cost impact where available.
- Data quality and model confidence.

Questions answered:

- What improves?
- What worsens?
- Is the improvement material?
- Is turnover justified?
- Is the result robust enough to act on?
- Does the candidate solve the diagnosed problem?

Product rule:

Comparison should be evidence-first. Scores can support the conclusion, but the product should not
be "score says winner."

### 4.9 Decision Verdict

User goal:

Know what action is justified.

Target verdict examples:

- Keep current portfolio.
- Rebalance to selected candidate.
- Partial rebalance / minor adjustments.
- Candidate improves risk but turnover or cost is too high.
- Test another candidate.
- No material rebalance recommended.
- Evidence insufficient due to data quality, model limits, or missing assumptions.

One-screen target summary:

- Portfolio status.
- Main risk.
- Selected candidate or keep-current baseline.
- Recommended action.
- Confidence.
- Reason confidence is not higher.

Product rule:

Decision Verdict is not simply "pick the best portfolio." It answers whether the user should act.

Implementation status:

Current Selection Engine / decision artifact behavior must be verified before replacing terms or
schemas. Decision Verdict is target product language unless promoted into canonical specs.

### 4.10 AI Commentary

User goal:

Read a clear explanation of the diagnosis, stress results, trade-offs, and verdict.

Target commentary should cover:

- Portfolio diagnosis.
- Key problems.
- Stress behavior.
- Reasonable path to test.
- Candidate logic.
- Current-vs-candidate comparison.
- Trade-offs.
- Decision verdict.
- No-trade rationale if applicable.
- What to monitor next.

Product rule:

AI Commentary must be grounded in deterministic outputs and should not invent calculations.

Implementation status:

Requires code/spec verification before claiming current AI Commentary scope, inputs, or output
contracts.

### 4.11 Monitoring / What Changed

User goal:

Know what changed since the last review and what needs attention.

Target monitoring dimensions:

- Portfolio health / status change.
- Risk contributor changes.
- Worst stress scenario changes.
- Weight drift.
- New breaches or warnings.
- Candidate retest triggers.
- Assumption changes.

MVP status:

Monitoring can stay light in the core MVP. Full multi-client monitoring, macro regime monitoring,
advanced breach engines, and workspace-level tracking are later/advanced unless current specs say
otherwise.

## 5. Diagnosis-Only State

The target product should support a state where the user has not generated any candidate.

State:

```text
Portfolio diagnosed.
No candidate generated yet.
Reasonable paths to test available.
Quick benchmark tests available.
```

Outputs:

- Portfolio X-Ray.
- Stress & Risk Diagnosis.
- Top problems.
- Weakness map.
- Reasonable paths to test.
- No candidate generated yet.

Implementation status:

Requires code/spec verification.

## 6. Core MVP vs Advanced / Later

### Core MVP

- Current portfolio input.
- Portfolio X-Ray.
- Stress Test Lab.
- Problem Classification.
- Reasonable paths to test.
- User-triggered selected candidate generation.
- Current-vs-candidate comparison.
- Decision Verdict.
- AI Commentary as explanation.
- Light Monitoring / What Changed.

### Advanced / Later Product Backlog

These items are not Core MVP requirements. Do not describe them as implemented unless verified in
`SPEC.md`, `docs/specs/*.md`, or code. Preserve existing capabilities as `Current`, `Advanced`,
`Legacy`, or `Requires Review` as appropriate.

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

Advanced/later does not mean delete. Preserve existing capabilities and reclassify them carefully.

### Legacy / Compatibility

- Legacy policy optimization flow.
- Existing explicit export/report artifacts.
- Older PDF/report sidecars.
- Full batch candidate generation if used as current infrastructure or research mode.

Legacy does not mean broken. It means not the main target product UX.

## 7. User Outputs

Target core user outputs:

- Portfolio diagnosis summary.
- Top hidden risks.
- Stress behavior summary.
- Main hedge gaps.
- Reasonable paths to test.
- Generated candidate hypothesis.
- Current-vs-candidate comparison.
- Trade-off explanation.
- Decision Verdict.
- AI Commentary.
- Monitoring triggers.

Advanced / export outputs:

- Detailed metrics appendix.
- Full candidate comparison table.
- Scorecards.
- Backtest details.
- Scenario details.
- Data-quality appendix.
- PDF / DOCX / report package where supported.

Current generated-output contracts are governed by `OUTPUTS.md` and detailed specs.

## 8. Empty And Error States

Target product should clearly handle:

- Missing tickers.
- Invalid weights.
- Weights sum greater than allowed.
- Negative weights where not allowed.
- Unknown taxonomy.
- Missing price data.
- Insufficient history.
- Insufficient factor data.
- Stress scenario unavailable.
- Candidate generation failed.
- Candidate evidence stale.
- Candidate improves one dimension but worsens another.
- Evidence insufficient for a confident verdict.

Product rule:

Insufficient data is not a product failure if it is truthful and clearly explained.

Exact statuses and failure codes require code/spec verification.

## 9. Product Language

Preferred client-facing language:

| Internal / technical | Client-facing framing |
| --- | --- |
| Portfolio X-Ray | What you really own |
| Stress Test Lab | Where it can break |
| Candidate Factory | Better allocation alternatives |
| Optimization method | Way to test an improvement hypothesis |
| Candidate Comparison | What improves and what gets worse |
| Selection Engine | What to do now / Decision Verdict |
| Decision Journal | Why this decision was made |
| No-trade | No material rebalance recommended |

Do not rename public CLI flags, JSON fields, generated schemas, or canonical specs without a
separate migration plan.

## 10. Relationship To Current Implementation

This draft is target product direction.

Current implementation must be verified through:

- `SPEC.md`
- `RULES.md`
- `OUTPUTS.md`
- `DATA.md`
- `TESTING.md`
- `docs/specs/*.md`
- current code

Do not claim these as current without verification:

- Problem Classification module.
- Candidate Launchpad.
- Portfolio Alternatives Builder UI/service.
- User-triggered candidate generation as default behavior.
- Diagnosis-only state.
- Current-vs-candidate as the only/main implemented comparison mode.
- Decision Verdict replacing Selection Engine.
- AI Commentary scope and grounding.
- Any new JSON field, CLI flag, output file, or folder contract.

## 11. Product Non-Goals

The product should not:

- Promise perfect weights.
- Always recommend trading.
- Hide model limits, data gaps, or uncertainty.
- Treat AI as a calculation engine.
- Make advanced research modules mandatory for the core MVP.
- Present a giant optimizer menu before diagnosis.
- Delete legacy/advanced backend capability just because it is not the target user-facing MVP.

## 12. Open Product Questions

- Which target modules should become implemented contracts first: Problem Classification, Candidate
  Launchpad, Alternatives Builder, or Decision Verdict?
- Should current Selection Engine schemas be preserved and mapped to Decision Verdict language, or
  should a new schema be introduced later?
- How many reasonable paths to test should be shown in MVP: 2 or 3?
- Which candidate methods are available in core MVP vs full research mode?
- What is the minimum evidence threshold for "no material rebalance recommended"?
- What AI Commentary inputs and guardrails should be canonical?
- Which monitoring signals belong in MVP vs later advisor workspace?

## 13. Source-Of-Truth Relationship

Until reviewed and approved:

- `PRODUCT.md` is a draft.
- Existing `PRODUCT.md` remains the current product document.
- `SPEC.md` and `docs/specs/*.md` remain authoritative for implemented behavior.
- `OUTPUTS.md` remains authoritative for generated outputs.
- Product concepts become binding only after source-of-truth docs, code, and verification are
  updated through the normal workflow.
