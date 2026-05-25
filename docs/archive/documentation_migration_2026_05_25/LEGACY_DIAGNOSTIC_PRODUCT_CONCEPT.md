# Diagnostic Product Concept

This document is a living product blueprint, not a binding implementation spec.

## Status

This document describes the target product concept and target architecture for Portfolio X-Ray / Portfolio MRI. It is an evolving draft: sections may be added, edited, renamed, or removed as the project changes.

It is a product and architecture guide, not a canonical implementation specification. It does not replace `SPEC.md`, `RULES.md`, `DATA.md`, `docs/specs/*`, metric formulas, stress scenario definitions, investment policy logic, data rules, configuration schemas, source code behavior, or existing implementation contracts.

If this document mentions a metric, stress scenario, assumption, optimization method, UI block, or product module, that mention does not automatically require the current codebase to change. Implementation details must still be governed by the canonical specs and changed through normal planning, documentation sync, and verification.

Ideas from this document become binding only after they are promoted into the relevant canonical source of truth, such as `SPEC.md`, `DATA.md`, `docs/specs/*.md`, `ARCHITECTURE.md`, or an ExecPlan under `docs/exec_plans/`, and then implemented and verified.

Use this document for product direction, terminology, and future planning. Do not use it as the sole authority for current formulas, scenarios, optimizer policy, data handling, outputs, or code behavior.

## Concept Name

Working names:

- Portfolio X-Ray & Optimization Terminal
- Portfolio Research & Decision System
- Portfolio MRI

The system is a decision support product, not a machine that produces perfect portfolio weights.

Core user outcome:

> I understand what is really inside my portfolio, where hidden risk lives, how it may behave in a crisis, and which better allocation alternatives are available.

Core workflow:

```text
Diagnose -> Generate candidates -> Stress-test -> Compare robustness -> Choose / explain
```

The product helps the user diagnose a portfolio, compare alternatives, understand trade-offs, and make a defensible investment decision.

## Target Segments

### Private Investors / HNWI

Users with roughly $100k to $5m in investable assets.

Pain points:

- Portfolios assembled ad hoc across ETFs, stocks, bonds, crypto, and cash.
- Poor understanding of real risk.
- Unclear behavior under 2008, 2020, 2022, or similar stress events.
- Need for an intelligent, professional report.

Product message:

> Upload your portfolio and get an institutional risk X-ray in minutes.

### Family Offices / Wealth Managers

Pain points:

- Need to explain risk to clients quickly.
- Need to compare portfolios.
- Need polished reports.
- Need defensible rebalance rationale.

Product message:

> White-label institutional portfolio diagnostics for client reporting.

### Investment Advisors

Pain points:

- Need to look rigorous and prepared before client meetings.
- Need to automate portfolio analytics.
- Need professional PDF-style outputs.

Product message:

> Generate professional portfolio risk reports before every client meeting.

### Sophisticated Retail Investors

Pain points:

- Already use Portfolio Visualizer, Koyfin, Excel, or Python.
- Want deeper factor analysis, stress tests, macro context, backtests, and robustness checks.

Product message:

> Portfolio Visualizer, but deeper, more institutional, and macro-aware.

## Target Product Chain

The intended product chain is:

1. Input & Assumptions Layer
2. Portfolio X-Ray / Portfolio Diagnostics Layer
3. Stress Test Lab
4. Candidate Portfolio Factory / Portfolio Menu
5. Optimization Engine
6. Strategy Backtest
7. Scenario & Stress Evaluation for Candidates
8. Macro Highlight / Macro Risk Dashboard
9. Candidate Comparison Layer
10. Portfolio Comparison Arena
11. Portfolio Health Score
12. Robustness Score / Robustness Scorecard
13. Selection Engine
14. Assumption Sensitivity
15. Pareto Frontier / Dominance Check
16. Regret Analysis
17. Trade-off Explanation
18. Model Risk Diagnostics
19. Action Engine
20. Rebalancing Advisor
21. No-Trade Recommendation
22. AI Portfolio Commentary
23. Monitoring / What Changed
24. Decision Journal

## 1. Input & Assumptions Layer

This layer defines the analysis base.

### 1.1 Portfolio Input

The user or system defines:

- Asset universe.
- Concrete tickers or instruments.
- Current weights when an existing portfolio is analyzed.
- No current weights when the task is to build a portfolio from a universe.
- Portfolio currency.
- Benchmark.
- Risk profile.
- Investment horizon.

Purpose:

The system must know exactly which assets it is analyzing and whether an existing portfolio already exists.

### 1.2 Mandate Builder

The user defines investment goals and constraints, such as:

- Minimum and maximum asset weight.
- Minimum and maximum asset class weight.
- Target volatility.
- Maximum drawdown.
- Target or minimum return.
- Maximum CVaR.
- Maximum turnover.
- Liquidity constraints.
- Maximum equity beta.
- Whether shorting, leverage, or cash are allowed.

Purpose:

The system formalizes the client investment policy so it does not produce technically optimal but practically unacceptable portfolios.

### 1.3 Assumption Engine

The user or system defines calculation assumptions, such as:

- Data window: 3Y, 5Y, 10Y, or another configured window.
- Data frequency: daily, weekly, monthly.
- Expected return method.
- Covariance method.
- Risk-free rate source for the portfolio currency.
- Transaction costs.
- Rebalance frequency.
- Missing data logic.
- Cash proxy.
- Stress severity.
- FX assumptions.

Purpose:

The same portfolio can produce materially different conclusions under different windows, frequencies, and estimators. Assumptions must be explicit.

### Layer Result

The system has the full input set:

- Universe.
- Weights when available.
- Currency.
- Benchmark.
- Risk profile.
- Client goals.
- Constraints.
- Calculation assumptions.

## 2. Portfolio X-Ray / Portfolio Diagnostics Layer

This is the first analytical layer after portfolio input. The system does not optimize or recommend changes yet. It shows what the portfolio really contains, how it behaves, where risk comes from, and where weaknesses exist.

### 2.1 Asset Allocation

The system shows structure by:

- Asset.
- Asset class.
- Region.
- Currency.
- Sector.
- Risk bucket.

Purpose:

The user first sees what they actually hold and how capital is distributed.

### 2.2 Portfolio Metrics / Risk Diagnostics

The system can show metrics such as:

- Return.
- Volatility.
- Sharpe.
- Sortino.
- Drawdown.
- Rolling metrics.
- VaR / ES.
- Downside deviation.
- Skew / kurtosis.
- Beta.
- Downside beta.
- Upside beta.
- Correlation breakdown.
- Liquidity risk.
- Concentration risk.

Purpose:

The user sees portfolio behavior across return, risk, drawdowns, volatility, and tail losses.

Implementation note:

This list is product-level. Current implemented metrics are governed by `docs/specs/metrics_specification.md` and related source code.

### 2.3 Factor Exposure / Factor Sensitivity

The system shows sensitivity to factors such as:

- Equity.
- Rates.
- Inflation.
- Credit.
- USD.
- Commodity.
- Volatility / VIX.
- Growth.

Purpose:

The user sees the real factor bets of the portfolio, not only asset labels.

### 2.4 Hidden Exposure / Hidden Risk Detector

The system looks for hidden risks, such as:

- Hidden equity beta.
- Duration concentration.
- Credit risk.
- Liquidity risk.
- Correlation concentration.
- Weak hedge behavior.
- Tail risk.

Core idea:

> What you think you own vs what you actually own.

Purpose:

A portfolio can look diversified by holdings while being concentrated in one underlying source of risk.

### 2.5 Portfolio Archetype Classification

The system classifies portfolio behavior into archetypes, for example:

- Equity Growth Portfolio.
- Balanced 60/40-like.
- Credit Carry Portfolio.
- Duration-heavy Defensive.
- Inflation-sensitive.
- Pseudo-diversified Portfolio.

Example output:

> Portfolio looks diversified by holdings, but behaves like an equity-growth portfolio with hidden credit beta.

Purpose:

The user gets a plain-language description of portfolio behavior, not only tables.

### 2.6 Risk Budget View

The system compares:

- How much capital is allocated to each asset.
- How much risk each asset contributes.
- How much stress loss each asset contributes.

Example:

> Asset A = 10% weight, but 27% of risk. Asset B = 20% weight, but only 6% of risk.

Purpose:

The user sees the difference between capital weight and actual risk contribution.

### 2.7 Portfolio Weakness Map

The system maps vulnerabilities such as:

- Recession risk.
- Inflation risk.
- Rates risk.
- Credit risk.
- Liquidity risk.
- USD risk.
- Equity crash risk.
- Commodity shock risk.
- Volatility spike risk.

Each risk can be classified as low, medium, or high.

Purpose:

The user quickly sees which market environments are most dangerous for the portfolio.

### Layer Result

The Portfolio X-Ray layer answers:

- What is really inside the portfolio?
- How does it behave?
- Where does risk come from?
- What hidden exposures exist?
- Where are the portfolio's weak points?

## 3. Stress Test Lab

This is one of the central product screens. Its purpose is to understand how the current portfolio behaves in adverse market environments.

### 3.1 Scenario Library

Scenario Library provides a common set of historical and synthetic scenarios for portfolio stress evaluation.

Evaluation dimensions can include:

- Portfolio loss.
- Drawdown.
- CVaR.
- Contribution to loss.
- Worst scenario.
- Mandate pass / fail.

### 3.1.1 Historical Scenarios

Examples:

- Dotcom.
- Global Financial Crisis 2008.
- COVID crash 2020.
- Inflation / rates shock 2022.
- Banking stress 2023.
- China slowdown.
- Oil shock.
- USD spike.
- Volatility shock.

Implementation note:

This is a target product list. Current implemented historical scenarios are governed by `docs/specs/stress_testing_spec.md` and current code.

### 3.1.2 Synthetic Scenarios

Examples:

- Equity -20%.
- Equity -35%.
- Rates +150 bps.
- Rates -150 bps.
- Credit spreads +300 bps.
- Inflation surprise.
- USD +10%.
- Oil +40%.
- Liquidity shock.
- Crypto -50%.
- Severe recession.
- Severe stagflation.

Implementation note:

This is a target product list. Current implemented synthetic scenarios are governed by `docs/specs/stress_testing_spec.md` and current code.

### 3.2 Stress Conclusions

The output should be more than PnL. It should include:

- Expected portfolio loss.
- Top loss contributors.
- Top risk contributors.
- Assets that helped.
- Correlation breakdown.
- Pass / fail relative to mandate.
- Recovery estimate.
- Hedge gap.

Example:

> In a 2008-like shock, portfolio loses -24.6%. 68% of the loss comes from equity and credit-sensitive assets. Treasuries hedge only partially because duration exposure is too low.

### 3.3 What Happens If? Simulator

Target interactive feature:

The user moves sliders and immediately sees portfolio impact.

Example inputs:

- S&P 500: -20%.
- Rates: +100 bps.
- Credit spreads: +200 bps.
- USD: +8%.
- Oil: +30%.
- VIX: +20 points.

Example outputs:

- Portfolio loss.
- Top contributors.
- Hedge effectiveness.
- Broken assumptions.

Purpose:

This answers the investor's core question:

> What happens to my portfolio if the market goes wrong?

### 3.4 Crisis Replay

Target feature:

> Replay 2008 with your portfolio.

The system shows month-by-month:

- Portfolio decline.
- Assets pulling the portfolio down.
- Assets providing protection.
- Maximum drawdown timing.
- Recovery time.

Example:

> Your portfolio entered crisis with 0.88 equity beta and reached -31% drawdown after 9 months.

### 3.5 Hedge Gap Analysis

The system identifies hedge gaps, for example:

- Equity crash hedge: acceptable.
- Rates-up hedge: weak.
- Stagflation hedge: poor.
- Liquidity shock protection: poor.
- USD spike protection: medium.

Example:

> The main hedge gap is inflation/rates shock, not normal equity volatility.

### 3.6 Current Portfolio Stress Scorecard

The stress scorecard shows:

- Which scenarios the current portfolio survives.
- Where maximum loss occurs.
- Which assets drive losses.
- Which assets protect.
- Where hedge gaps appear.

For the current portfolio, it can capture:

- Base return / risk.
- Max drawdown.
- Stress PnL.
- CVaR / tail loss.
- Worst scenario.
- Asset risk contribution.
- Factor risk contribution.
- Mandate pass / fail.

Purpose:

The stress lab turns stress testing into a diagnosis of where the portfolio survives, where it breaks, why losses occur, and which assets are sources of risk or protection.

## 4. Candidate Portfolio Factory / Portfolio Menu

After diagnosing the current portfolio, macro context, and stress behavior, the system generates alternatives.

Purpose:

The system does not search for one ideal portfolio. It creates candidate portfolios that can be compared.

Target candidates:

- Current Portfolio.
- Equal Weight.
- Equal Weight by Asset Class.
- Risk Parity.
- HRP.
- Minimum Variance.
- Maximum Diversification.
- Minimum CVaR.
- Robust Mean-Variance.
- Custom Constraints.
- Tactical Tilt variant when enabled.

Each candidate is a hypothesis:

- One may distribute capital better.
- One may distribute risk better.
- One may reduce volatility.
- One may protect against tail risk.
- One may pass mandate constraints better.

Layer output:

- Candidate list.
- Candidate weights.
- Construction method.
- Base parameters.
- Constraint fit.
- Preparation for backtest, stress evaluation, and comparison.

## 5. Optimization Engine

The Optimization Engine builds candidate portfolios. The user action can be simplified as "Improve Portfolio", but the system should return alternatives rather than one absolute answer.

Target optimization variants:

- Minimum Volatility.
- Max Sharpe.
- Max Return under Risk Constraint.
- Minimum CVaR.
- Risk Parity.
- HRP.
- Maximum Diversification.
- Robust Mean-Variance.
- Drawdown-controlled.
- Macro-resilient.
- Stress-test optimized.
- Tax-aware / turnover-aware in later versions.

Core logic:

Optimization is not the final decision. It creates candidates that must be tested, compared, and explained.

Example:

> This portfolio has the highest expected return, but breaks in a 2008-like stress. This portfolio has lower expected return, but survives recession and stagflation better.

## 6. Strategy Backtest

After candidate generation, the system checks how each portfolio would have behaved historically.

Backtest can apply to:

- Current portfolio.
- Each candidate.
- Benchmark.
- 60/40.
- Custom strategy.

Backtest output can include:

- Growth of a starting amount.
- CAGR.
- Volatility.
- Sharpe.
- Sortino.
- Max drawdown.
- Time to recovery.
- Worst month.
- Worst year.
- Rolling returns.
- Rolling drawdowns.
- Rolling Sharpe.
- Calendar-year returns.

Rebalancing options:

- Monthly.
- Quarterly.
- Semiannual.
- Annual.
- Drift-based.
- No rebalance.

Out-of-sample examples:

- Optimize on 2014-2019, test on 2020-2025.
- Rolling optimization / walk-forward analysis.

Purpose:

Backtest evaluates historical behavior, but it does not replace the final decision.

## 7. Scenario & Stress Evaluation For Candidates

Each candidate is run through the same stress scenarios.

Purpose:

All candidates must be evaluated under the same conditions for comparison to be fair.

For each candidate, the system can capture:

- Base return / risk.
- Max drawdown.
- Stress PnL.
- CVaR / tail loss.
- Worst scenario.
- Asset risk contribution.
- Factor risk contribution.
- Mandate pass / fail.

The analysis should exist both at portfolio level and asset level.

Layer result:

The system shows which candidate survives adverse environments better and why.

## 8. Macro Highlight / Macro Risk Dashboard

This is an informational and diagnostic layer over the portfolio. It does not predict markets, control optimization, or determine weights by itself.

It answers:

- Where are we in the macro environment?
- In which regimes is the portfolio most vulnerable?
- In which regimes has the portfolio historically benefited?
- Which risks are currently most relevant?

### 8.1 Current Macro Regime

Example:

> Current regime: Stagflation pressure / low confidence transition.

Indicators can include:

- Growth momentum.
- Inflation pressure.
- Rates pressure.
- Credit spreads.
- Risk sentiment.
- Liquidity.

### 8.2 Macro Risk Dashboard

The dashboard can show:

- Current macro regime.
- Regime confidence.
- Growth score.
- Inflation score.
- Liquidity condition.
- Portfolio fit to current regime.
- Historical performance by regime.
- Best/worst assets by regime.
- Recommended watchpoints.

Example:

> Your portfolio historically performs best in reflation and worst in stagflation.

### 8.3 Regime Fit Score

Example:

```text
Goldilocks: 82/100
Reflation: 76/100
Stagflation: 41/100
Recession disinflation: 58/100
```

Example output:

> Portfolio is strong in goldilocks/reflation, but weak in stagflation.

### 8.4 Role Of Macro Overlay

Macro is a context layer:

- Current regime diagnostics.
- Risk warnings.
- Permission or restriction for tactical tilt.
- Scenario-weight adjustment in evaluation.

Example:

If the current regime is reflation with low confidence, an aggressive tilt may not be applied, while diagnostics pay closer attention to inflation, stagflation, and rates shocks.

## 9. Candidate Comparison Layer

After backtest and stress evaluation, all candidates are summarized in one comparison format.

Minimum comparison table:

- Return.
- Volatility.
- Sharpe.
- Max drawdown.
- CVaR.
- Worst stress.
- Top asset risk contribution.
- Top factor risk contribution.
- Turnover.
- Mandate fit.

Purpose:

This layer makes different optimizers and portfolio variants comparable.

## 10. Portfolio Comparison Arena

The user compares two to five portfolios side by side, for example:

- Current.
- Optimized.
- Risk Parity.
- Minimum CVaR.
- Benchmark.
- Custom candidate.

The system should show a verdict, not only charts.

Example:

> Optimized portfolio improves expected drawdown resilience but sacrifices 1.4 percentage points of CAGR. Risk parity has better crisis behavior but underperforms in bull markets.

Purpose:

The user sees where each portfolio wins, where it loses, and what compromise it offers.

## 11. Portfolio Health Score

Portfolio Health Score is a quick overall quality score.

It can apply to:

- Current portfolio.
- Each candidate.
- Final selected portfolio.

Example:

```text
Portfolio Health Score: 73 / 100
```

Components can include:

- Diversification score.
- Drawdown resilience.
- Factor balance.
- Macro regime fit.
- Liquidity score.
- Concentration score.
- Stress-test score.
- Risk-adjusted return score.

Important:

The score must not be a magic number. It must explain why the score is high or low.

Example:

> Score reduced mainly due to high equity risk concentration, weak stagflation resilience, and high downside beta.

## 12. Robustness Score / Robustness Scorecard

Robustness Score evaluates candidate resilience.

Example:

```text
Current Portfolio: 62 / 100
Risk Parity: 78 / 100
Minimum CVaR: 81 / 100
Robust Mean-Variance: 76 / 100
```

Possible indicators:

- Downside protection.
- Stress resilience.
- Diversification / risk contribution.
- Return efficiency.
- Factor stability.
- Mandate fit.

Example target weighting:

- 25% downside protection: MaxDD, downside volatility, ES / CVaR, recovery time.
- 20% stress resilience: 2008, 2020, 2022, rates shock, liquidity shock, stagflation shock.
- 20% diversification / RC: asset, asset class, and factor risk concentration.
- 15% return efficiency: CAGR, Sharpe, Sortino, return per unit of risk.
- 10% factor stability: factor betas, rolling beta, Kalman beta, factor concentration.
- 10% mandate fit: MaxDD, volatility, liquidity, weight limits, and other constraints.

Implementation note:

These weights are conceptual and TBD unless a future spec formalizes them.

## 13. Selection Engine

Selection Engine answers:

> Which candidate should be chosen, and why?

The decision is multi-criteria, not based on one metric.

Conceptual formula:

```text
Final Score =
  expected return
  + downside resilience
  + stress survival
  + diversification
  + factor concentration
  + mandate fit
  - turnover penalty
  - complexity penalty
```

The system considers:

- Expected return.
- Downside resilience.
- Stress survival.
- Diversification.
- Factor concentration.
- Mandate fit.
- Turnover penalty.
- Complexity penalty.

Purpose:

A portfolio with slightly lower expected return but better stress resilience and lower concentration may be better than an aggressive portfolio with strong historical return.

## 14. Assumption Sensitivity

Purpose:

Checks whether the winning candidate survives changes in assumptions.

Test dimensions can include:

- 3Y / 5Y / 10Y covariance.
- Expected returns +/- 20-30%.
- Stress severity.
- Rebalance frequency.
- Transaction costs.
- Correlation stress.

Example output:

> Portfolio A wins in 78% of assumption variants.

## 15. Pareto Frontier / Dominance Check

This block removes weak candidates.

A portfolio is dominated if it has:

- Lower return.
- Higher risk.
- Worse drawdown.
- Worse CVaR.
- Higher turnover.
- No compensating advantage.

Example:

> Candidate D is dominated. No clear reason to choose.

Purpose:

Not every generated candidate deserves serious consideration.

## 16. Regret Analysis

Regret Analysis shows the cost of choosing wrong.

Main question:

> If the user chooses portfolio A, how badly can it lose to B or C in scenarios where those portfolios are better?

Metrics can include:

- Average regret.
- Worst-case regret.
- Regret by scenario.
- Regret by regime.

Example:

> Portfolio A has strong base-case return, but high regret in stagflation and liquidity shock.

Purpose:

The system helps choose a more resilient decision, not only the prettiest base-case portfolio.

## 17. Trade-off Explanation

Trade-off Explanation describes the price paid for improvement.

Example:

> Optimized portfolio reduces MaxDD from -28% to -21%, improves CVaR by 18%, but lowers CAGR from 8.4% to 7.6% and requires 22% turnover.

The system shows:

- What improves.
- What worsens.
- Cost of change.
- Required turnover.
- Risk reduced.
- Return sacrificed.

Purpose:

The user understands not only what is better, but what they pay for the improvement.

## 18. Model Risk Diagnostics

This is the system's self-criticism layer.

Warnings can include:

- Expected returns unstable.
- Covariance unstable.
- Low factor model R2.
- High multicollinearity.
- Insufficient stress / regime data.
- Optimizer result too concentrated.
- Solution sensitive to window choice.

Purpose:

The system is honest about where conclusions are reliable and where caution is required.

## 19. Action Engine

Action Engine turns the selected decision into concrete action.

Example:

> To move to Portfolio B, reduce SPY by 6%, increase TLT by 4%, and add 2% GLD. Turnover = 12%. Expected MaxDD improvement = 4 percentage points; CVaR improvement = 11%.

Outputs:

- Target weights.
- Buy / sell / hold.
- Delta vs current.
- Turnover.
- Expected risk improvement.
- Expected cost.
- Priority trades.

Key metric:

```text
Risk improvement per 1% turnover
```

Purpose:

Not all trades are equally useful. The system shows which changes provide the most risk improvement for the least turnover.

## 20. Rebalancing Advisor

Rebalancing Advisor makes Action Engine practical.

It shows:

- Current weights.
- Target weights.
- Difference.
- What to buy.
- What to sell.
- Turnover.
- Estimated transaction impact.
- Risk improvement after rebalance.

Example:

> Reduce equity ETF by 6%, increase short-term Treasuries by 4%, increase gold by 2%. Expected max drawdown improves from -27% to -21%.

Purpose:

The user gets a concrete path from current allocation to target allocation.

## 21. No-Trade Recommendation

No-Trade Recommendation is an explicit refusal to recommend unnecessary changes.

If improvement is small and turnover is high, the system should say:

> No material rebalance recommended.

Example:

```text
Score improvement: +2 points
Turnover: 18%
Drawdown improvement: 0.7%
Recommendation: Not worth rebalancing.
```

Purpose:

The system should not always recommend trades. Sometimes the right decision is to do nothing.

## 22. AI Portfolio Commentary

AI Portfolio Commentary turns analytics into readable investment language.

It summarizes:

- Portfolio diagnostics.
- Main risks.
- Hidden exposures.
- Macro context.
- Stress behavior.
- Candidate comparison.
- Selected variant.
- Trade-offs.
- Actions.
- No-trade recommendation when applicable.

Example:

> The portfolio is growth-oriented, with high dependence on equity beta and moderate diversification across asset classes. Its main weakness is stagflation and rate-shock sensitivity. The current allocation is not fragile in normal markets, but losses become concentrated during liquidity shocks.

Purpose:

The user receives a coherent institutional-style explanation, not only tables and charts.

## 23. Monitoring / What Changed

Monitoring turns a one-time analysis into an ongoing process.

The system shows what changed since the last analysis:

- Risk score worsened.
- Equity beta increased.
- Worst scenario changed.
- Top risk contributor changed.
- Macro regime changed.
- Mandate breach appeared.
- Correlation concentration increased.

Example:

> Since last month, stress loss increased mainly due to higher equity-credit correlation.

Purpose:

The user sees whether the portfolio improved, worsened, or needs a new decision.

## 24. Decision Journal

Decision Journal records the investment process.

Stored fields can include:

- Analysis date.
- Selected portfolio.
- Rejected alternatives.
- Assumptions.
- Expected improvement.
- Accepted risks.
- Macro context.
- Rationale.

Post-review question:

> Was the decision good based on what was known at the time?

Purpose:

The system separates decision quality from outcome quality and creates a disciplined investment decision history.

## Questions The Product Should Answer

- What exactly is being analyzed?
- What goals and constraints does the client have?
- What assumptions is the analysis based on?
- What is really inside the portfolio?
- How is the portfolio distributed by assets, classes, currencies, regions, and factors?
- How does the portfolio behave by return, risk, and drawdown?
- Where is the main risk?
- Which assets contribute disproportionately to risk?
- What hidden exposures exist?
- What behavioral archetype does the portfolio match?
- Where is the portfolio most vulnerable?
- Where does the portfolio break in stress scenarios?
- Which assets pull the portfolio down in crisis?
- Which assets actually protect the portfolio?
- Where is the hedge gap?
- Which alternative portfolios can be built?
- How do alternatives behave historically?
- How do alternatives pass the same stress tests?
- Which alternative is better, and why?
- How robust is the selected variant to assumption changes?
- Which candidates can be rejected as weak?
- What is the cost of choosing wrong?
- What trade-off does the investor accept?
- How much can the user trust the calculations and conclusions?
- What exactly should be bought, sold, or changed?
- Is changing the portfolio worth it?
- How can the decision be explained to a client in plain investment language?
- What changed since the last analysis?
- Why was this exact decision made?
- Was the decision high-quality from a process perspective?

## Relationship To Current Implementation

This product concept should guide future planning and documentation, but the current implementation remains governed by:

- [SPEC.md](../../../SPEC.md)
- [Portfolio Construction Policy](../../specs/portfolio_construction_policy.md)
- [Metrics Specification](../../specs/metrics_specification.md)
- [Stress Testing Spec](../../specs/stress_testing_spec.md)
- [Feasibility Constraints](../../specs/feasibility_constraints_spec.md)
- [Data Policy](../../specs/data_policy_spec.md)
- [Production Workflow](../../specs/production_workflow.md)
- [PLANS.md](../../../PLANS.md)
- [AGENTS.md](../../../AGENTS.md)

Any implementation change derived from this concept must be specified separately, planned when needed, documented in the relevant source-of-truth file, and verified through the project verification loop.
