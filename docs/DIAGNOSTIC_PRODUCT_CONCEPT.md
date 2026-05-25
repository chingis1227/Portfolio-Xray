# Diagnostic Product Concept

This document is part of the active project documentation after the documentation migration. It is a product concept and target architecture guide, not a canonical implementation spec. It does not override `../SPEC.md`, `../RULES.md`, `../OUTPUTS.md`, `../DATA.md`, `../TESTING.md`, `specs/*.md`, formulas, stress scenario definitions, optimizer policy, generated-output contracts, or current code behavior. Current implementation claims must be verified against the canonical specs and code.

## 1. Concept Name And Identity

Working names:

- Portfolio MRI
- Portfolio X-Ray
- Portfolio Research & Decision System

Preferred product identity:

> Portfolio MRI is a portfolio diagnostics and investment decision-support system.

The product is not a black-box optimizer. It helps an advisor or sophisticated investor understand
the current portfolio, identify hidden risks, test a reasonable improvement hypothesis, compare
trade-offs, and reach a defensible investment verdict.

Core user outcome:

> I understand what is really inside my portfolio, where risk is concentrated, where it can break,
> which improvement hypothesis is worth testing, and whether I should rebalance or do nothing.

## 2. Target Users

### Primary ICP — Independent Investment Advisors / Financial Advisors

Advisors who manage or advise client portfolios of roughly `$250k-$5m` and need professional
portfolio risk reviews before client meetings.

Primary job:

- Diagnose the client portfolio quickly.
- Explain hidden risk, stress behavior, and trade-offs.
- Support a rebalance, partial rebalance, no-trade, or further-review conversation.
- Produce a client-ready narrative.

### Secondary ICP — Sophisticated Self-Directed Investors

Serious self-directed investors with meaningful portfolios, roughly `$100k-$1m+`, who already use
broker analytics, Portfolio Visualizer, Excel, Koyfin, Python, or similar tools.

Primary job:

- Understand real portfolio risk.
- See hidden concentrations and factor exposures.
- Test whether a candidate allocation actually improves the current portfolio.
- Avoid acting on attractive but fragile analytics.

### Preserved / Later Segments

HNWI, family offices, wealth managers, white-label users, and multi-client operators remain valid
project directions. They should be preserved as secondary, advanced, or later packaging unless the
business strategy explicitly promotes them to the primary ICP.

## 3. Product Philosophy

### Diagnosis Before Action

The product must explain the current portfolio before suggesting changes. A user should first see
what they own, where the risk sits, which exposures dominate, and where the portfolio is vulnerable.

### Current Portfolio First

The target MVP starts from the user's current portfolio. Candidate portfolios are evaluated against
the actual current allocation, not against an abstract optimizer output.

### Problem Before Method

The product should not start with an optimizer menu. It should first classify the portfolio problem:
high volatility, high drawdown risk, concentration, weak hedge behavior, poor diversification, or
current portfolio acceptable.

### Candidate As Hypothesis

A candidate portfolio is an investment hypothesis:

```text
Candidate = diagnosed problem + improvement goal + construction method + constraints + evidence + trade-off
```

The candidate is not "the best portfolio." It is a structured test of whether a diagnosed problem
can be improved.

### Guided, Not Prescriptive

The system should guide the user through evidence and trade-offs. It should not claim to replace
advisor responsibility, tax analysis, suitability review, liquidity planning, or final investment
judgment.

### No-Trade As A Valid Verdict

If the improvement is weak, turnover is too high, evidence quality is poor, or model risk is too
large, the right conclusion may be to leave the current portfolio unchanged.

### AI Commentary As Explanation Layer

AI can explain deterministic outputs in plain language. It should not be the source of metrics,
stress results, data-quality statuses, candidate freshness, optimizer readiness, or verdict
evidence.

## 4. Target MVP Product Chain

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

This replaces the older 24-block product concept as the core MVP story. Older modules should be
reclassified as core, advanced/later, legacy, or requires review rather than deleted.

## 5. Core MVP Blocks

### 5.1 Input Portfolio

Purpose:

Capture the portfolio that should be diagnosed.

Target MVP user-facing inputs:

- Tickers / instruments.
- Current weights.
- Investor currency.

System-resolved inputs and assumptions:

- `analysis_subject = current_portfolio`
- benchmark / base benchmark
- cash proxy
- risk-free source
- FX logic
- market data provider
- data windows
- quality thresholds
- calculation defaults

UX rule:

The first screen should stay simple. Advanced assumptions should be visible in disclosure or
advanced settings, not forced into the initial user input.

Current implementation boundary:

- `analysis_subject` exists as the current portfolio-first runtime contract in specs/code.
- Exact current required fields and generated contract details are owned by `SPEC.md`, `OUTPUTS.md`,
  detailed specs, and code.
- Any full UI behavior remains target product work.

### 5.2 Portfolio X-Ray

Purpose:

Show what is really inside the current portfolio.

Target outputs:

- Allocation breakdown.
- Asset class / region / currency / sector / risk role breakdown where available.
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
- Which risk factors dominate?
- Which assets contribute more risk than their capital weight suggests?
- Which holdings duplicate the same risk?
- Is diversification real or only visual?

Boundary:

Portfolio X-Ray is diagnostic. It should not be framed as the decision engine.

### 5.3 Stress Test Lab

Purpose:

Show how the current portfolio may behave in bad markets.

Target outputs:

- Synthetic stress scenarios.
- Historical stress scenarios where data supports them.
- Worst scenario.
- Loss contributors.
- Assets that help offset losses.
- Hedge gap analysis.
- Stress data-quality disclosure.

Questions answered:

- Where can the portfolio break?
- Which assets hurt most in stress?
- Which assets help?
- Which market risks should be tested through a candidate hypothesis?
- Is there enough data to support the stress conclusion?

Boundary:

The system should report insufficient data honestly. It should not fabricate crisis evidence.

### 5.4 Problem Classification

Purpose:

Translate diagnostics into 2-3 understandable improvement directions.

Target problem labels:

- High volatility.
- High drawdown.
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

- Top diagnosed problems.
- Evidence behind each problem.
- Reasonable paths to test.
- Indication that no candidate is needed when the current portfolio is acceptable.

Implementation status:

Target direction unless verified against code/specs.

### 5.5 Candidate Launchpad

Purpose:

Let the user choose which improvement hypothesis to test.

Target launchpad cards:

- Reduce volatility.
- Reduce drawdown.
- Improve diversification.
- Reduce concentration.
- Improve crisis resilience.
- Improve return/risk balance.
- Compare against simple benchmark.
- Keep current portfolio and monitor.

Important distinction:

Launchpad cards are not portfolios. They are entry points into the Portfolio Alternatives Builder.

Implementation status:

Target direction unless verified against code/specs.

### 5.6 Portfolio Alternatives Builder

Purpose:

Generate one selected candidate portfolio from a chosen goal and method.

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

Potential methods:

- Equal Weight.
- Equal Weight by Asset Class.
- Risk Parity.
- Hierarchical Risk Parity.
- Minimum Variance.
- Minimum CVaR.
- Maximum Diversification.
- Robust Mean Variance.

UX rule:

The product should present methods as ways to test an improvement hypothesis, not as the starting
point of the product.

Implementation status:

User-triggered on-demand candidate generation is target direction unless verified against current
code/specs. Existing automatic/batch capabilities should be preserved as current infrastructure,
advanced mode, research mode, or legacy as appropriate.

### 5.7 Current vs Candidate Comparison

Purpose:

Show whether the selected candidate improves the current portfolio and what it costs.

Target comparison dimensions:

- Return / risk.
- Volatility.
- Drawdown.
- Tail risk where available.
- Stress loss.
- Worst scenario.
- Risk concentration.
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
- Does the candidate solve the diagnosed problem?
- Is the evidence strong enough to act?

### 5.8 Decision Verdict

Purpose:

Answer whether action is justified.

Target verdicts:

- Keep current portfolio.
- Rebalance to selected candidate.
- Partial rebalance / minor adjustments.
- Candidate improves risk but turnover or cost is too high.
- Test another candidate.
- No material rebalance recommended.
- Evidence insufficient due to data quality, model limits, or missing assumptions.

Boundary:

Decision Verdict should not be framed as "the system always selects the winner." The central
question is whether the user should act.

Implementation status:

Requires code/spec verification before replacing or renaming current Selection Engine contracts.

### 5.9 AI Commentary

Purpose:

Translate evidence into an understandable narrative.

Target commentary should explain:

- Portfolio diagnosis.
- Key risks.
- Stress behavior.
- Reasonable path to test.
- Candidate logic.
- Current-vs-candidate trade-offs.
- Decision verdict.
- No-trade rationale if applicable.
- What to monitor next.

Boundary:

AI Commentary explains evidence. It does not create the evidence.

Implementation status:

- Implemented now: `ai_commentary_context.json` grounding context only (`src/ai_commentary_context.py`; no LLM).
- Implemented now (separate): deterministic `commentary.txt` / `stress_commentary.txt` and decision-package summaries from structured evidence via `src/portfolio_commentary.py` and `src/decision_package_reporting.py`. These are report-pipeline prose, not the target AI Commentary product layer.
- Not implemented: generated natural-language AI Commentary. Requires a separate future spec (see roadmap backlog) with prompts, provider policy, output contract, and guardrail tests.

### 5.10 Monitoring / What Changed

Purpose:

Track what should be watched after the verdict.

Target MVP monitoring can remain light:

- Key risk contributor changes.
- Worst stress scenario changes.
- Weight drift.
- New warnings or breaches.
- Candidate retest triggers.
- Assumption changes.

Advanced monitoring can include multi-client workspaces, macro regime monitoring, breach engines,
and full decision history.

## 6. Diagnosis-Only State

The target MVP should support:

```text
Portfolio diagnosed.
No candidate generated yet.
Reasonable paths to test available.
Quick benchmark tests available.
```

This state matters because a user may only need diagnosis and stress review before deciding whether
to test a candidate.

Target outputs:

- Portfolio X-Ray.
- Stress & Risk Diagnosis.
- Top problems.
- Weakness map.
- Reasonable paths to test.
- Clear statement that no candidate has been generated.

Implementation status:

Current generated artifacts and workflow-state metadata can support this state, but a formal
diagnosis-only product UI/workspace state remains target product work.

## 7. Candidate State Model

Target candidate progression:

```text
0 candidates -> diagnosis only
1 candidate  -> current vs candidate comparison
2+ candidates -> shortlist / comparison arena
```

Target candidate record:

- candidate id
- name
- source
- goal
- method
- parameters
- constraints
- weights
- created-from problem
- status
- evidence / quality fields

Exact fields and schemas require code/spec verification.

## 8. Core, Advanced, Legacy, Requires Review

### Core MVP

- Input current portfolio.
- Portfolio X-Ray.
- Stress Test Lab.
- Problem Classification.
- Candidate Launchpad.
- Portfolio Alternatives Builder simple mode.
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

### Legacy / Compatibility

- Legacy policy optimization flow.
- Legacy policy/report entrypoints.
- Existing PDF/report export sidecars.
- Batch candidate generation where used as current infrastructure or research mode.

### Requires Review

- Any claim that target modules exist today.
- Any schema rename.
- Any CLI behavior change.
- Any generated-output contract change.
- Any public terminology migration that could confuse existing operators.

## 9. Old 24-Block Concept Reclassification

The older concept listed 24 product blocks. Reclassify them as follows:

| Old concept block | New classification |
| --- | --- |
| Input & Assumptions Layer | Core MVP, simplified first screen plus system defaults. |
| Portfolio X-Ray / Diagnostics | Core MVP. |
| Portfolio Archetype Classification | Advanced / Later optional diagnostic layer; not part of core Portfolio X-Ray until explicitly implemented and approved. |
| Stress Test Lab | Core MVP. |
| Candidate Portfolio Factory / Portfolio Menu | Reframed as Candidate Launchpad + Alternatives Builder; current batch factory preserved as implementation/advanced/research as applicable. |
| Optimization Engine | Internal candidate construction capability; not the product front door. |
| Strategy Backtest | Advanced / Later unless required by current specs. |
| Scenario & Stress Evaluation for Candidates | Advanced / Later or research mode. |
| Macro Highlight / Macro Risk Dashboard | Advanced / Later optional diagnostic overlay. |
| Candidate Comparison Layer | Core when current-vs-candidate; full multi-candidate comparison is advanced/research unless current core behavior requires it. |
| Portfolio Comparison Arena | Advanced when multi-candidate; core only for generated shortlist. |
| Portfolio Health Score | Supporting evidence; not the main product answer. |
| Robustness Score / Scorecard | Supporting / Advanced evidence; not the main product answer. |
| Selection Engine | Reframe as Decision Verdict language after code/spec review. |
| Assumption Sensitivity | Advanced / Later. |
| Pareto Frontier / Dominance Check | Advanced / Later. |
| Regret Analysis | Advanced / Later. |
| Trade-off Explanation | Core, inside Current vs Candidate Comparison and Verdict. |
| Model Risk Diagnostics | Advanced / supporting evidence; core only as simple confidence/disclosure. |
| Action Engine | Later or light action summary unless current specs require generated artifacts. |
| Rebalancing Advisor | Later / advanced; core can show high-level rebalance/no-trade verdict. |
| No-Trade Recommendation | Core MVP. |
| AI Portfolio Commentary | Core explanation layer, not calculation source. |
| Monitoring / What Changed | Core light version; full monitoring later. |
| Decision Journal | Light version inside commentary or later full journal. |

## 10. Product Questions The System Should Answer

From diagnosis:

- What is actually in the current portfolio?
- What is the real economic exposure?
- Where are capital and risk concentrated?
- Which factors dominate the portfolio?
- Which assets contribute most to total risk?
- Where does weight differ from risk contribution?
- Which hidden exposures exist?
- Is diversification real?
- Where is the portfolio most vulnerable?

From stress:

- How does the portfolio behave in historical and synthetic stress scenarios?
- Which assets drive losses?
- Which assets help offset losses?
- Where is the main hedge gap?
- Which stress problem should be tested through an alternative?

From candidate generation:

- Which diagnosed problem deserves a candidate hypothesis?
- Which improvement path is reasonable?
- Which construction method fits the selected hypothesis?
- What constraints and parameters are appropriate?
- Was the candidate actually generated from the diagnosed problem?

From comparison and verdict:

- What improves and what worsens versus the current portfolio?
- Is the improvement material?
- Is turnover/cost justified?
- Is the evidence reliable enough?
- Should the user keep, rebalance, test another candidate, no-trade, or mark evidence insufficient?

## 11. Current Implementation Guardrails

This document is target product direction and should be read alongside current implementation
contracts.

Current additive artifacts verified by current specs/code include:

- Problem Classification artifact (`problem_classification.json`).
- Candidate Launchpad artifact (`candidate_launchpad.json`).
- Portfolio Alternatives Builder backend delegation plan.
- Current-vs-Candidate adapter (`current_vs_candidate.json`).
- Decision Verdict additive mapping (`decision_verdict.json`).
- AI Commentary grounding context (`ai_commentary_context.json`).
- Light What Changed summary (`what_changed_summary.json`).

Do not overstate these as implemented product capabilities:

- Full Portfolio Alternatives Builder UI/service.
- User-triggered one-candidate generation as default behavior.
- Formal diagnosis-only product UI state beyond current metadata/artifacts.
- Current-vs-candidate as the only or main implemented comparison mode.
- Decision Verdict replacing or renaming Selection Engine.
- Generated natural-language AI Commentary.
- Any new JSON field, CLI flag, schema, output file, or folder contract.

Current implementation truth must come from:

- `SPEC.md`
- `RULES.md`
- `OUTPUTS.md`
- `DATA.md`
- `TESTING.md`
- `docs/specs/*.md`
- current source code

## 12. Non-Goals

The product concept should not:

- Promise perfect weights.
- Force a rebalance recommendation.
- Hide model limits or data-quality issues.
- Present AI as the calculation engine.
- Make macro dashboard mandatory for MVP.
- Make full multi-candidate research mode the default UX.
- Delete existing advanced or legacy backend capabilities because they are not core UX.
- Rename public schemas, CLI flags, or generated fields without a migration plan.

## 13. Migration Note

If this document is approved, merge it into `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` only after:

1. Reviewing the current concept file.
2. Preserving non-binding status language.
3. Preserving advanced/later capabilities as project memory.
4. Checking all implementation claims against current specs/code.
5. Updating links from `PRODUCT.md`, `ARCHITECTURE.md`, and `README.md` only after the replacement is
   approved.
