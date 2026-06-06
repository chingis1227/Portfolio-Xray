# Portfolio MRI - Investment Decision Room MVP UI/UX Specification

Status: design proposal  
Scope: MVP web interface concept only; does not change runtime formulas, output contracts, or product logic.  
Canonical product frame: diagnosis-first, current-portfolio-first, one explicit hypothesis test before verdict.

## 1. Product Positioning

Portfolio MRI should feel like an institutional **Investment Decision Room**, not a generic analytics dashboard and not an optimizer cockpit.

The interface guides the user through one defensible review:

```text
Portfolio Input
-> Diagnosis Summary
-> Evidence Center: X-Ray + Stress
-> Hypothesis Builder
-> Current vs Candidate Comparison
-> Decision Verdict + AI Commentary
-> Client-ready Report
```

Primary user feeling:

> I know what I own. I know where the risk is. I know what breaks under stress. I tested one alternative. I understand the trade-off. I know whether action is justified.

## 2. UX Principles

1. **Decision journey before metrics.** The first screen after input is an executive diagnosis, not charts.
2. **Current portfolio first.** Candidate generation is explicit and never automatic.
3. **Hypothesis, not recommendation.** Candidate portfolios are tests. They are never called "best," "optimal," or allocation instructions.
4. **No-trade is a valid decision.** The verdict can justify monitoring instead of action.
5. **Evidence-insufficient is a valid result.** Blocked states explain what happened, why it matters, and what to do next.
6. **Technical evidence is drill-down.** Top-level screens avoid raw regression output, factor tables, optimizer metadata, and JSON names.
7. **AI explains; it does not decide.** AI Commentary is grounded explanation after the deterministic verdict.

## 3. Information Architecture

### Left sidebar

1. Portfolio
2. Diagnosis
3. Evidence
4. Hypothesis
5. Comparison
6. Verdict
7. Report

### Top journey progress

Input -> Diagnosis -> Hypothesis -> Candidate -> Comparison -> Verdict

Each step supports these visible statuses:

- `complete`
- `active`
- `locked`
- `blocked`
- `needs action`

### Persistent right panel

When useful, a right-side panel explains:

- current workflow state;
- decision boundary;
- why the user is seeing this screen;
- what evidence is still missing;
- next CTA.

## 4. Visual Direction

### Style

Premium, calm, institutional, precise, analytical. More -investment committee review- than -trading app.-

### Palette

- Primary background: `#07111F`
- Secondary surface: `#0D1B2A`
- Card surface: `#12263A`
- Accent blue: `#3B82F6`
- Soft blue: `#60A5FA`
- Positive: `#10B981`
- Warning: `#F59E0B`
- Risk: `#EF4444`
- Primary text: `#F8FAFC`
- Secondary text: `#CBD5E1`
- Muted text: `#94A3B8`
- Border: `#334155`
- Premium accent, rare: `#D4AF37`

### Typography

Use a modern sans stack: Geist, Inter, SF Pro, system sans.  
Hierarchy:

- page titles: 32-40px, tight line-height;
- hero diagnosis: 24-28px;
- card titles: 14-16px uppercase or semibold;
- body copy: 13-15px, concise;
- badges: 11-12px uppercase.

### Layout

Desktop MVP:

- fixed left sidebar, 248px;
- top journey bar, 64px;
- main content max width around 1180-1280px;
- optional right decision panel, 300-340px;
- card grid with restrained density;
- no market tickers tape, no live-price treatment.

## 5. Screen Specifications

## Screen 1 - Portfolio Input

Goal: let the user enter or upload the current portfolio quickly.

Top copy:

- App title: **Portfolio MRI**
- Page title: **Upload current portfolio**
- Subtitle: -Start with tickers, weights, and investor currency. The system diagnoses the portfolio before suggesting any action.-

Main components:

1. **Input table**
   - Ticker / Instrument
   - Weight %
   - Currency
2. **Example portfolio strip**
   - SPY 40%, QQQ 20%, BND 20%, GLD 10%, Cash 10%
3. **Trust message**
   - Portfolio MRI analyzes the current portfolio first. No candidate is generated automatically.-

CTAs:

- Primary: **Analyze portfolio**
- Secondary: **Upload CSV**
- Tertiary: **Add position**

Do not show:

- target return;
- risk profile;
- liquidity needs;
- tax;
- optimizer settings;
- advanced assumptions.

Primary state: `Input active`, downstream steps locked.

## Screen 2 - Decision Summary

Goal: main product screen; explain the portfolio's primary issue in 30 seconds.

Hero card: **Portfolio MRI Summary**

Fields:

- Main diagnosis
- Main evidence: 3 strongest facts
- Suggested next step
- Current workflow status
- Verdict status

Example hero copy:

> Main diagnosis: Risk appears concentrated in a small number of equity growth drivers, while stress protection is limited.  
> Suggested next step: Test whether a simple diversification reference improves stress behavior without creating unacceptable turnover.  
> Status: Diagnosis complete. No candidate tested yet.

Cards:

1. **What you own**
   - holdings count;
   - dominant asset class;
   - dominant risk factor;
   - dominant currency;
   - top 3 holdings.
2. **Where the risk is**
   - top risk contributor;
   - top 3 risk contributors;
   - risk concentration;
   - hidden exposure summary.
3. **What breaks under stress**
   - worst synthetic scenario;
   - worst historical episode;
   - main hedge gap;
   - offset coverage ratio.
4. **What to test next**
   - suggested hypothesis;
   - suggested method;
   - success criteria;
   - decision boundary: -This is a hypothesis test, not a rebalance recommendation.-

CTAs:

- Primary: **Choose hypothesis**
- Secondary: **View evidence**

Supported summary states:

- Diagnosis complete, no candidate tested yet
- Candidate tested, verdict ready
- Evidence insufficient
- No material rebalance recommended
- Rebalance justified, based on tested candidate

## Screen 3 - Evidence Center: X-Ray + Stress

Goal: show evidence behind the diagnosis without overwhelming the user.

Main question:

> When the portfolio loses money, what actually helps

Section A: **Portfolio X-Ray**

Top cards:

- Capital allocation
- Risk contribution
- Factor exposure
- Hidden risk alerts
- Weakness map

Each card includes:

- short diagnosis;
- 2-3 key metrics;
- risk level badge;
- **View details** link.

Example top message:

> You may own many tickers, but risk is concentrated in 2-3 drivers.

Section B: **Stress Evidence**

Top cards:

- Worst synthetic scenario
- Worst historical scenario
- Assets hurt
- Assets helped
- Offset coverage ratio
- Main hedge gap

Visualizations:

- simple assets hurt/helped bar chart;
- compact stress loss chart;
- offset coverage gauge;
- risk level badges.

Drill-down only:

- factor betas;
- OLS/HAC confidence;
- raw correlations;
- scenario tables;
- run metadata;
- data quality warnings.

## Screen 4 - Hypothesis Launchpad + Builder

Goal: turn diagnosis into a testable portfolio hypothesis.

Screen title:

> Test a hypothesis

Two-column layout.

### Left column - Suggested tests

Cards:

1. **Compare against Equal Weight**
2. **Compare against Risk Parity**
3. **Improve diversification**
4. **Improve crisis resilience**
5. **Reduce concentration**

Each card includes:

- why this test is relevant;
- suggested method;
- success criteria;
- decision boundary.

Example card:

Title: **Improve crisis resilience**  
Why: Current stress results show weak offset coverage and concentrated stress losses.  
Suggested method: Minimum CVaR  
Success criteria:

- lower worst stress loss;
- improve offset coverage;
- reduce stress loss concentration.

Boundary:

> This is a hypothesis test, not a rebalance recommendation.

### Right column - Hypothesis Builder

Fields:

- Goal
- Method
- Constraint preset
- Capped / Uncapped
- Min asset weight
- Max asset weight
- Success criteria
- Decision boundary

Methods:

- Equal Weight
- Risk Parity
- Hierarchical Risk Parity
- Minimum Variance
- Minimum CVaR
- Maximum Diversification

Constraint presets:

- Conservative
- Balanced
- Aggressive
- Basic reference
- Custom
- Uncapped

Uncapped warning:

> Uncapped mode may create concentrated portfolios. Use only for diagnostic comparison, not as an automatic rebalance recommendation.

CTAs:

- Primary: **Run candidate test**
- Secondary: **Back to diagnosis**

## Screen 5 - Current vs Candidate Comparison

Goal: show the practical trade-off between current portfolio and candidate.

Top block:

- Candidate tested
- Hypothesis tested
- Method
- Constraint preset
- Candidate status
- Badge: **Not a recommendation**

Main table columns:

- Metric
- Current
- Candidate
- Change
- Interpretation

Top rows:

- Volatility
- Max drawdown
- Worst stress loss
- Offset coverage
- Risk concentration
- Expected turnover
- Transaction cost
- Return trade-off

Below-table cards:

1. **What improved**
   - lower volatility;
   - lower drawdown;
   - lower worst stress loss;
   - better risk distribution;
   - improved offset coverage.
2. **What worsened**
   - lower return;
   - higher turnover;
   - higher concentration;
   - weaker hedge behavior;
   - higher complexity.
3. **What is unclear**
   - evidence insufficient;
   - data quality limitation;
   - optimizer quality limitation;
   - metric unavailable.

Required wording:

> Candidate improves X, but worsens Y.

Avoid blanket comparison wording:

Do not make any blanket claim that the tested candidate is superior overall.

## Screen 6 - Decision Verdict + AI Commentary

Goal: answer whether action is justified.

Hero verdict card supports:

- Keep current portfolio
- Rebalance to selected candidate
- No material rebalance recommended
- Selected candidate improves risk but turnover is too high
- Test another candidate
- Evidence insufficient due to data quality
- Evidence insufficient due to optimizer quality

Verdict fields:

- verdict;
- confidence / evidence quality;
- why;
- action logic;
- accepted trade-offs;
- rejected trade-offs;
- next review trigger.

Example:

> Verdict: No material rebalance recommended  
> Why: Candidate reduces drawdown slightly, but the improvement is not material enough after turnover and transaction cost.  
> Action: Keep current portfolio and monitor.  
> Next trigger: Re-test if top risk contributor changes, stress loss worsens, or portfolio weights drift.

AI Commentary format:

> Your portfolio's main weakness is... We tested... The candidate improved... However... Therefore... Monitor...

Boundary always visible:

> This is decision-support, not a trading instruction.

Light Decision Journal:

- date;
- current portfolio;
- selected candidate;
- tested / untested alternatives;
- key assumptions;
- accepted trade-offs;
- verdict;
- next review trigger.

## Screen 7 - Report / Client-ready Explanation

Goal: provide a clean advisor-facing summary that can be copied or exported later.

Sections:

1. Portfolio diagnosis
2. Key risks
3. Stress behavior
4. Hypothesis tested
5. Candidate comparison
6. Trade-offs
7. Verdict
8. Monitoring triggers

CTA:

- **Copy summary**

MVP boundary:

- Do not design full PDF export yet.
- A disabled placeholder can say: -PDF export planned later.-
- Do not expose raw backend output or JSON names.

## 6. State Model

### Diagnosis only

State: no candidate generated yet.  
UI:

- Diagnosis Summary is available.
- Evidence Center is available.
- Hypothesis Launchpad is available.
- Comparison, Verdict, Report are locked or partial.

### Candidate setup ready

State: hypothesis selected, builder configured, candidate not generated.  
UI:

- Builder panel shows selected fields.
- Primary CTA is **Run candidate test**.
- Decision boundary remains visible.

### Candidate generated

State: candidate exists, comparison available.  
UI:

- Comparison step active or complete.
- Candidate badge says **Test result**, not recommendation.

### Verdict ready

State: Decision Verdict available.  
UI:

- Verdict and AI Commentary are available.
- Report can be copied.

### Blocked / evidence insufficient

State reasons:

- data quality issue;
- factor data unavailable;
- candidate failed;
- optimizer infeasible;
- evidence insufficient.

Blocked card structure:

1. What happened
2. Why it matters
3. What you can do next

Example:

> Candidate generation failed because constraints made the method infeasible. This matters because the comparison cannot separate portfolio improvement from construction failure. Try a less restrictive preset or test a reference benchmark.

## 7. Core UX Boundaries

- Candidate != recommendation
- Verdict != trading instruction
- Reference benchmark != rebalance recommendation
- No-trade is a valid decision
- Evidence insufficient is a valid result
- Stress loss != normal risk contribution
- Pre-stress weakness != confirmed stress failure
- AI Commentary explains; it does not decide

## 8. Explicit Non-MVP Items

Do not include in MVP UI:

- macro dashboard;
- full PDF designer;
- multi-client workspace;
- full optimizer zoo;
- advanced settings UI;
- tax-aware screens;
- full backtest lab;
- Monte Carlo;
- asset diagnostics;
- client suitability questionnaire.

## 9. Self-Critique Before Final Revision

### Risks found

1. **Too dashboard-like risk:** Evidence Center can become a grid of metrics.  
   Revision: add a prominent question headline and make each evidence card answer a decision question, not just show values.
2. **Too optimizer-first risk:** Hypothesis Builder could look like method selection.  
   Revision: rename screen to -Test a hypothesis,- lead with suggested tests, and keep method as a secondary implementation detail.
3. **Overloaded summary risk:** Decision Summary could show too many metrics.  
   Revision: hero uses one diagnosis, three facts, one next step; metrics are pushed into four compact cards.
4. **Recommendation ambiguity risk:** Candidate and verdict copy might imply trading advice.  
   Revision: every candidate/comparison/verdict screen includes boundary badges and neutral language.
5. **Technical artifact leakage risk:** backend output names could appear in UI.  
   Revision: report and evidence screens use user-facing labels only; raw metadata lives in drill-down.

### Final revision decisions

- Use Investment Decision Room as the main mental model.
- Use Candidate tested and Hypothesis tested, never recommendation-style portfolio labels.
- Make the top journey bar stateful and persistent.
- Make the right decision panel persistent on screens where the user might confuse evidence with action.
- Keep -Copy summary- as the only Report CTA in MVP; PDF is future placeholder only.

## 10. High-Fidelity Mockup File

Interactive-style static prototype:

`docs/proposals/portfolio_mri_decision_room_mockup.html`

Open the file in a browser. The top screen tabs simulate the MVP journey and states.

## 11. Manual Browser Review Notes - v1 Revision

Manual review was performed by opening the HTML mockup in Chrome and inspecting key screens: Diagnosis Summary, Hypothesis, Comparison, and Verdict.

Findings and revisions:

- The concept reads as premium / institutional: dark surfaces, restrained accent colors, and decision-room framing work better than a backend report style.
- The 30-second journey is understandable: diagnosis leads to hypothesis selection, then candidate trade-off, then verdict.
- The Hypothesis screen was the most overloaded screen; this is acceptable for MVP only because the builder sits on the right and suggested tests remain card-based. Future implementation should collapse lower-priority test cards on smaller screens.
- The Comparison screen risked becoming too table-like, so interpretation copy was revised toward trade-off language rather than backend metric reporting.
- Decorative unicode markers were removed from the HTML because they can render inconsistently in local browser/headless screenshots.
- The primary builder CTA was revised in the mockup from "Generate candidate" to "Run candidate test" to reduce optimizer-first interpretation while preserving the explicit candidate-generation boundary.


