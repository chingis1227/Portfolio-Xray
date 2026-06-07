# Portfolio MRI - Investment Decision Room MVP UI/UX Specification

Status: design proposal
Scope: MVP web interface concept only; does not change runtime formulas, output contracts, data rules, or product logic.
Canonical product frame: diagnosis-first, current-portfolio-first, one explicit hypothesis test before verdict.
Illustrative values in the companion mockup are sample review values; production must replace them with approved calculated values from the runtime contracts.

## 1. Product Positioning

Portfolio MRI should feel like an institutional **Investment Decision Room**, not a generic analytics dashboard, trading app, or method-selection cockpit.

The interface guides the user through one defensible review:

```text
Portfolio Input
-> Diagnosis Summary
-> Evidence Center: X-Ray + Stress
-> Hypothesis Launchpad + Builder
-> Current vs Candidate Comparison
-> Decision Verdict + AI Commentary
-> Client-ready Report
```

Primary user feeling after five minutes:

> I know what is inside the portfolio. I know where the real risk is. I know what breaks under stress. I know which hypothesis was tested. I understand what improved, what worsened, what remains unclear, and whether action is justified.

## 2. UX Principles

1. **Decision journey before metrics.** The first screen after input is a decision-state summary, not a chart wall.
2. **Current portfolio first.** Investor currency is set once at portfolio level; candidate generation is explicit and never automatic.
3. **Hypothesis, not allocation advice.** Candidate portfolios are tests. They are never called "best," "optimal," or allocation instructions.
4. **No-trade is a valid decision.** The verdict can justify keeping the current portfolio and monitoring.
5. **Evidence-insufficient is a valid result.** Blocked states explain what happened, why it matters, and what to do next.
6. **Technical evidence is subordinate.** Top-level screens avoid detailed regression output, factor tables, method metadata, file names, and data dump language.
7. **AI explains; it does not decide.** AI Commentary translates the deterministic verdict into client-ready language.
8. **Stress and normal risk are distinct.** Stress loss is not the same as normal risk contribution; pre-stress weakness is not treated as confirmed stress failure.

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

Visible statuses:

- `complete`
- `active`
- `locked`
- `blocked`
- `needs action`

### Persistent decision panel

When useful, a right-side panel explains:

- current workflow state;
- decision boundary;
- why the user is seeing this screen;
- what evidence is missing;
- next CTA.

## 4. Visual Direction

### Style

Premium, calm, institutional, precise, and analytical. The experience should feel closer to an investment committee memo room than a trading terminal.

### Color meaning

- Blue = action / navigation
- Green = improvement
- Amber = caution / evidence insufficient
- Red = risk / worsening
- Gold = premium boundary or decision-room emphasis, used sparingly

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
- decision-state labels: 11-12px uppercase;
- card titles: 14-16px semibold;
- body copy: 13-15px, concise;
- badges: 11-12px uppercase.

### Layout

Desktop MVP:

- fixed left sidebar, 248px;
- top journey bar, 64-72px;
- main content max width around 1180-1500px;
- optional right decision panel, 300-430px;
- one dominant hero block per screen;
- 3-5 supporting cards per screen section;
- no market ticker tape, live-price strip, or crypto-style visual treatment.

## 5. Screen Specifications

## Screen 1 - Portfolio Input

Goal: let the user enter or upload the current portfolio quickly and understand that diagnosis comes before any candidate.

Top copy:

- App title: **Portfolio MRI**
- Page title: **Upload current portfolio**
- Subtitle: "Start with holdings, weights, and investor currency. Portfolio MRI diagnoses the current portfolio before any candidate is created."

Main components:

1. **Portfolio-level controls**
   - Investor currency
   - Total allocation
   - Cash treatment
2. **Portfolio setup summary**
   - "5 positions - 100% allocated - Investor currency: USD - Cash included"
3. **Input table**
   - Ticker / Instrument
   - Weight %
   - Row remove control
4. **Allocation validation**
   - Total allocation: 100%
   - Cash included: 10%
   - No candidate generated
   - Analyze portfolio disabled until allocation equals 100%
5. **Example portfolio strip**
   - SPY 40%, QQQ 20%, BND 20%, GLD 10%, Cash 10%
   - Treat as visually secondary sample input chips.
6. **Portfolio guardrail**
   - Portfolio MRI analyzes the existing allocation before suggesting any hypothesis test. No candidate is generated automatically.

Currency rule:

- Investor currency is selected once at portfolio level.
- Do not repeat currency selectors on every holding row.
- Cash remains a row, for example Cash 10%, and inherits the portfolio-level investor currency in the MVP surface.
- Future explicit cash-currency overrides belong in advanced settings only if promoted by scope.

Ticker input rule:

- Ticker / Instrument uses a searchable dropdown against the approved universe of assets.
- The user can type to search and select from the universe; the mockup can use a static sample universe.
- The portfolio table should not ask the user to manually type asset type.
- Asset classification is inferred from the selected instrument and belongs in later evidence screens, not in the input table.

Row editing rule:

- The user can add another position from the input card.
- The user can remove any existing position row.
- Weight remains a manual numeric input.
- Allocation validation updates immediately when a ticker, row, investor currency, or weight changes.

Blocking rule:

- If total allocation is below or above 100%, the **Analyze portfolio** CTA is disabled.
- The validation copy should show the current total and how much is missing or excessive.
- The UI should make the block visible without implying that any candidate has been generated.

CTAs:

- Primary: **Analyze portfolio**
- Secondary: **Upload CSV**
- Tertiary: **Add position**

Do not show:

- target return;
- risk profile questionnaire;
- liquidity needs;
- tax settings;
- method setup;
- advanced assumptions.

Input screen must communicate:

> Only tickers, weights, and investor currency are needed.

Primary state: `Input active`, downstream steps locked.

## Screen 2 - Diagnosis Summary

Goal: central cockpit of the product; explain the portfolio state in under 30 seconds.

Hero card: **Portfolio diagnosis**

The top of the screen must contain a visually dominant **decision-state panel**:

- Current state: **Diagnosis complete**
- Candidate state: **Candidate not tested yet** / **Candidate tested** / **Verdict ready**
- Primary diagnosis: **Risk is concentrated in a small number of equity-growth drivers, while stress protection appears limited.**
- Next best test: **Compare against Equal Weight as a diversification reference**
- Decision status: **No immediate rebalance justified. A reference test is needed before action.** / **Verdict ready — no material rebalance recommended** / **Evidence insufficient**

Main diagnosis copy:

> Risk is concentrated in a small number of equity-growth drivers, while stress protection appears limited.

Top evidence list:

1. Risk contribution is concentrated in QQQ/SPY.
2. Worst stress area is an equity shock / recession-like scenario.
3. Offset coverage is limited in stress scenarios.

Supporting cards:

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
   - decision boundary: "This is a hypothesis test, not a rebalance instruction."

Hierarchy rules:

- Primary diagnosis dominates the page.
- Use one status badge only; avoid repeating "diagnosis complete / no candidate tested" across multiple components.
- Separate the screen into Diagnosis, Evidence, Next test, and Current decision state.
- The suggested next test should feel like guided diagnostic progression, not a random recommendation.

CTAs:

- Primary: **Choose hypothesis**
- Secondary: **View evidence**

Supported summary states:

- Diagnosis complete, no candidate tested yet
- Candidate tested, verdict ready
- Evidence insufficient
- No material rebalance recommended
- Rebalance justified, based on tested candidate evidence

## Screen 3 - Evidence Center: X-Ray + Stress

Goal: show the evidence story before detailed cards.

Top evidence headline:

> Risk is concentrated in equity-growth exposure, and stress protection appears limited.

Top 3 evidence block:

1. Risk contribution is concentrated in QQQ/SPY.
2. Worst stress area is equity shock / recession-like scenario.
3. Offset coverage is limited in stress scenarios.

Then group evidence into three decision columns:

1. **What you own**
   - Capital structure
   - Hidden risks
2. **Where risk comes from**
   - Risk concentration
   - Factor drivers
3. **What breaks under stress**
   - Stress behavior
   - Hedge gap / offset coverage

Each evidence card should answer a decision question, not simply display a metric.

### Section A - Portfolio X-Ray

Cards:

- Capital allocation
- Risk contribution
- Factor exposure
- Hidden risk alerts
- Weakness map

Each card includes:

- short diagnosis;
- 2-3 key metrics or sample review values;
- risk level badge;
- **View details** link.

### Section B - Stress Evidence

Cards:

- Worst synthetic scenario
- Worst historical scenario
- Assets hurt / helped
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
- detailed correlation tables;
- scenario tables;
- run metadata;
- data quality warnings.

## Screen 4 - Hypothesis Launchpad + Builder

Goal: turn diagnosis into a ranked, testable portfolio hypothesis without making the screen feel like a method menu.

Screen title:

> Choose a hypothesis to test

Two-column layout.

### Left column - Ranked suggested tests

Suggested tests are ranked, not presented as equally important:

1. **Recommended first test: Compare against Equal Weight**
   - Why test this: use as a simple diversification reference against the current allocation.
   - Method: Equal Weight.
   - Success: lower concentration without excessive turnover.
   - Trade-off to watch: less concentration may reduce the current return profile.
2. **Reference benchmark: Compare against Risk Parity**
   - Why test this: checks whether risk-balanced exposure improves stress behavior.
   - Method: Risk Parity.
   - Success: better risk distribution and offset coverage.
   - Trade-off to watch: more defensive exposure may change upside participation.
3. **Targeted test: Improve crisis resilience**
   - Why test this: stress evidence shows weak offset coverage and concentrated stress losses.
   - Method: Minimum CVaR.
   - Success: lower worst stress loss; improve offset coverage; reduce stress loss concentration.
   - Trade-off to watch: downside improvement may require turnover or lower expected return.
4. **Secondary test: Improve diversification**
   - Why test this: current evidence suggests concentration in a few drivers.
   - Method: Maximum Diversification.
   - Success: reduce risk concentration.
   - Trade-off to watch: diversification benefit must be material after implementation friction.
5. **Optional test: Reduce concentration**
   - Why test this: risk contribution may be dominated by top holdings.
   - Method: Minimum Variance.
   - Success: lower concentration without excessive turnover.
   - Trade-off to watch: lower volatility alone does not justify action.

Boundary on every test:

> This is a hypothesis test, not a rebalance instruction.

Reference benchmark rule:

- Equal Weight and Risk Parity are reference benchmark tests, not recommendations.
- Do not label them as the "best" or preferred portfolio.

Selection behavior:

- Clicking a suggested test visibly selects that test card.
- The right-side Builder must update Goal, Method, Success criteria, and Decision boundary from the selected test.
- Changing Method manually should update the active test when it matches a known method.
- Generate test candidate must pass the selected method and hypothesis into the Comparison screen; it must not always show Equal Weight.

### Right column - Configure hypothesis test

Panel title: **Configure test**

Helper copy:

> This setup defines how the hypothesis will be tested. It does not create a recommendation.

Keep only these fields:

- Goal
- Method
- Constraint preset
- Capped / Uncapped
- Min asset weight
- Max asset weight
- Success criteria
- Decision boundary
- Generate test candidate

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

Constraint behavior:

- Preset changes update Capped / Uncapped and the min/max asset weight fields.
- Basic reference defaults to 0% minimum and 25% maximum.
- Conservative defaults to 2% minimum and 20% maximum.
- Balanced defaults to 0% minimum and 30% maximum.
- Aggressive defaults to 0% minimum and 40% maximum.
- Uncapped hides min/max asset weight fields because those caps no longer apply.
- Custom leaves the user-facing fields editable.

Uncapped warning:

> Uncapped mode may create concentrated portfolios. Use only for diagnostic comparison, not as an automatic rebalance instruction.

CTAs:

- Primary: **Generate test candidate**
- Secondary: **Back to diagnosis**

## Screen 5 - Current vs Candidate Comparison

Goal: show the practical trade-off between current portfolio and tested candidate.

Top caution line:

> Improvement is not the same as action. The verdict depends on materiality, turnover, cost, and evidence quality.

Top block:

- Candidate tested
- Hypothesis tested
- Method
- Constraint preset
- Candidate status
- Badge: **Test result**

Dynamic handoff rule:

- Candidate tested, Hypothesis, Method, and Constraint preset are populated from the selected Hypothesis Builder state.
- If the user selects Hierarchical Risk Parity, Minimum CVaR, Minimum Variance, Maximum Diversification, Risk Parity, or Equal Weight, the Comparison screen must show that selected method.
- Do not hardcode Equal Weight after the user selected a different hypothesis or method.

Hero trade-off summary before the table:

> The candidate improves selected risk metrics, but requires turnover and may reduce return profile.

Split the interpretation into:

1. **Improvements**
   - Volatility
   - Drawdown
   - Worst stress loss
   - Offset coverage
2. **Costs / Worsening**
   - Turnover
   - Transaction cost
   - Possible return-profile trade-off
3. **Unclear / Needs judgment**
   - Materiality after cost
   - Evidence quality
   - Whether another candidate improves downside risk with lower turnover

The table remains available below this interpretation, but it must not be the only primary object.

Main table columns:

- Metric
- Current
- Tested candidate
- Change
- Interpretation

Rows:

- Volatility
- Max drawdown
- Worst stress loss
- Offset coverage
- Risk concentration
- Expected turnover
- Transaction cost
- Return trade-off

Sample review values may use realistic labels such as:

- Volatility: 9.6% -> 8.8%
- Max drawdown: -19.8% -> -17.4%
- Worst stress loss: -21.2% -> -18.5%
- Offset coverage: 11.5% -> 18.9%
- Expected turnover: 22%
- Transaction cost: 10 bps assumption

Below-table cards:

1. **What improved**
   - Lower worst stress loss
   - Better risk distribution
   - Improved offset coverage
2. **What worsened**
   - Higher turnover
   - Possible lower return profile
   - More implementation friction
3. **What is unclear**
   - Whether improvement is material after costs
   - Whether another candidate would improve risk with lower turnover
   - Whether evidence quality is sufficient for action

Required wording:

> Candidate improves selected risk metrics, but action depends on trade-off quality.

Avoid blanket comparison wording:

Do not make any blanket claim that the tested candidate is superior overall.

## Screen 6 - Decision Verdict + AI Commentary

Goal: answer clearly whether the user should act or not.

Hero verdict card supports:

- Keep current portfolio
- Rebalance to selected candidate when the tested evidence justifies it
- No material rebalance recommended
- Selected candidate improves risk but turnover is too high
- Test another candidate
- Evidence insufficient due to data quality
- Evidence insufficient due to method feasibility or construction quality

Dominant verdict card for the current review state:

- Verdict: **No material rebalance recommended**
- Why: **The candidate improves selected risk metrics, but the improvement does not appear material enough after turnover and transaction cost.**
- Action: **Keep current portfolio and monitor.**
- Evidence quality: **Moderate**

No-trade presentation rule:

- "No material rebalance recommended" must look like a valid professional outcome, not a weak or missing result.
- Present **Why**, **Action**, and **Evidence quality** as strong first-class fields.

What would change this verdict:

- Stress loss worsens materially
- Top risk contributor changes
- Portfolio weights drift materially
- Another candidate improves downside risk with lower turnover

AI Commentary format:

> Your portfolio's main weakness is... We tested... The candidate improved... However... Therefore... Monitor...

Boundary always visible:

> This is decision-support, not a trading instruction.

Light Decision Journal:

- date;
- current portfolio;
- selected tested candidate;
- tested / untested alternatives;
- key assumptions;
- accepted trade-offs;
- rejected trade-offs;
- verdict;
- next review trigger.

## Screen 7 - Report / Client-ready Explanation

Goal: provide a premium advisor-facing summary that can be copied or exported later.

Visual treatment:

- off-white paper preview, not harsh pure white;
- subtle document metadata:
  - Portfolio MRI Review Summary
  - Current review session
  - Candidate tested: Equal Weight reference
  - Verdict: No material rebalance recommended
- stronger executive summary at the top;
- increased spacing;
- short paragraphs;
- clear section labels;
- **Copy summary** as primary action;
- disabled export control only as an MVP boundary, not a focal action;
- no file names, implementation artifact names, or data dump labels.

Sections:

0. Executive summary
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
- A disabled secondary control can say: "PDF export outside MVP."
- Do not expose implementation artifacts or file names.

## 6. State Model

### Diagnosis only

State: no candidate generated yet.
UI:

- Diagnosis Summary is available.
- Evidence Center is available.
- Hypothesis Launchpad is available.
- Comparison, Verdict, and Report are locked or partial.
- Message: **No candidate generated yet. Suggested tests are available.**

### Candidate setup ready

State: hypothesis selected, builder configured, candidate not generated.
UI:

- Builder panel shows selected fields.
- Primary CTA is **Generate candidate**.
- Decision boundary remains visible.
- Message: **Hypothesis selected. Candidate not generated yet.**

### Candidate generated

State: candidate exists, comparison available.
UI:

- Comparison step active or complete.
- Candidate badge says **Test result**.
- Message: **Candidate exists. Comparison available.**

### Verdict ready

State: Decision Verdict available.
UI:

- Verdict and AI Commentary are available.
- Report can be copied.
- Message: **Decision verdict available.**

### Evidence insufficient

State: evidence is insufficient for action.
UI:

- Show why evidence is insufficient.
- Show what to do next.
- Do not show normal action-oriented comparison.
- Message: **Evidence is insufficient for action.**

### Candidate failed / infeasible

State reasons:

- constraints made the candidate infeasible;
- required data is missing or low quality;
- construction quality is insufficient;
- method result is not stable enough for decision use.

UI:

1. What happened
2. Why it matters
3. What you can do next

Copy pattern:

> Candidate generation failed because the selected constraints made the method infeasible. This matters because the comparison cannot separate portfolio improvement from construction failure. Try a less restrictive preset or test a reference benchmark.

## 7. Core UX Boundaries

- Candidate is not a recommendation.
- Verdict is not a trading instruction.
- Reference benchmark is not a rebalance instruction.
- No-trade is a valid decision.
- Evidence insufficient is a valid result.
- Stress loss is not normal risk contribution.
- Pre-stress weakness is not confirmed stress failure.
- AI Commentary explains; it does not decide.

## 8. Explicit Non-MVP Items

Do not include in the MVP UI:

- macro dashboard;
- multi-candidate arena;
- method cockpit;
- client suitability questionnaire;
- tax-aware settings;
- Monte Carlo;
- advanced analytics screens;
- new financial calculations;
- full PDF designer;
- multi-client workspace;
- full backtest lab;
- asset diagnostics.

## 9. Design Canon Alignment

This specification and the companion mockup are aligned to
`docs/design/portfolio_mri_design_system.md` as the canonical UI/UX direction for
Portfolio MRI / Portfolio X-Ray / ДИАГНОСТИКА 2.

### Applied design thesis

- **Diagnosis before action:** the journey starts with Portfolio Input and a dominant Diagnosis Summary before any candidate is generated.
- **Decision journey, not dashboard:** navigation follows Portfolio -> Diagnosis -> Evidence -> Hypothesis -> Comparison -> Verdict -> Report instead of an all-at-once metric wall.
- **Evidence first, recommendation never implied:** Evidence Center opens with an evidence headline and Top 3 Evidence before X-Ray and Stress support cards.
- **Candidate is hypothesis, not recommendation:** Hypothesis Launchpad and Builder use hypothesis-test language and show explicit decision boundaries.
- **Verdict is decision-support:** Verdict explains why, action stance, monitoring triggers, and boundary copy instead of issuing an instruction.
- **No-trade and evidence-insufficient remain valid:** the state model includes no material rebalance and evidence-insufficient outcomes as first-class states.
- **Institutional depth, client-ready clarity:** the report preview uses concise sections and avoids implementation artifact names, dense tables, and data-dump language.

### Visual canon applied

- **IBM-inspired structure:** stable left navigation, top journey progress, clear state labels, and explicit screen responsibilities.
- **Linear-inspired clarity:** one primary question per screen, compact copy, ranked next steps, and reduced UI noise.
- **BMW-inspired premium dark precision:** deep navy app shell, restrained gold boundary accents, thin borders, and high-contrast dark cards.
- **Stripe/Coinbase-inspired financial trust:** plain-language status copy, visible evidence quality, and clear action boundaries.

### Color and component alignment

- Uses the canon palette: `#07111F`, `#0D1B2A`, `#12263A`, `#F8FAFC`, `#CBD5E1`, `#94A3B8`, `#334155`, `#3B82F6`, `#60A5FA`, `#10B981`, `#F59E0B`, `#EF4444`, and rare `#D4AF37`.
- Blue is reserved for journey state and action.
- Green marks improvement only.
- Amber marks caution, uncertainty, or insufficient evidence.
- Red marks risk or worsening.
- Gold is limited to premium boundary/status accents.

### Mockup changes driven by the canon

- Portfolio Input now uses one portfolio-level Investor currency field instead of repeating currency controls on every row.
- Diagnosis Summary now has a stronger decision-state panel with diagnosis, evidence, next test, and current decision state.
- Evidence Center now reads as an evidence story first, grouped by What you own, Where risk comes from, and What breaks under stress.
- Hypothesis Builder now reads as **Configure test**, with goal, method, constraints, success criteria, and decision boundary.
- Comparison now frames the candidate as a trade-off review before the table, with improvements, costs/worsening, and judgment dependencies.
- Verdict now has a dominant card answering whether action is justified, why, what to do, and what would change the verdict.
- Report preview now uses an off-white paper surface, document metadata, an executive summary, copy action, and an explicit decision-support boundary.

### Why it is closer to an Investment Decision Room

The user is guided through a controlled review sequence rather than dropped into a collection of widgets. The product state is visible first, evidence is presented before testing, the candidate is framed as a controlled hypothesis, and the verdict explains decision quality without becoming a trading command.

### Later, outside this scope

- Wiring mockup states to real runtime state and output contracts.
- Replacing sample values with approved calculated values.
- Production accessibility pass, keyboard navigation, and responsive QA.
- Future export integration if promoted by product scope.
- Full frontend app implementation, auth, database, and server integration.

## 10. Premium UI Polish Pass v3

This pass refines the existing HTML mockup and specification only. It does not add product features, change Python behavior, change the runtime pipeline, introduce auth/database/frontend architecture, or alter the canonical design direction in `docs/design/portfolio_mri_design_system.md`.

### What was fixed

- Fixed input currency logic: Investor currency is selected once at portfolio level, and the holdings table contains ticker/instrument, optional asset type, and weight.
- Made Portfolio Input cleaner with a portfolio setup card, allocation validation, a setup summary line, calmer example chips, and clearer CTA hierarchy.
- Reduced the internal-draft feeling by making the primary surfaces more intentional: one dominant hero per screen, lighter support cards, and quieter drill-down cards.
- Strengthened Diagnosis Summary as the core decision-room screen with a dominant state panel showing diagnosis, evidence, next test, and current decision state.
- Made Evidence Center story-first: headline and Top 3 Evidence are shown before decision-question evidence columns.
- Ranked Hypothesis tests by decision priority: recommended first test, reference benchmark, targeted test, secondary test, and optional test.
- Reframed the Builder as **Configure test** with helper copy that the setup defines a test and does not create a recommendation.
- Made Comparison trade-off first by adding a hero trade-off summary before the table and strengthening **Improvements / Costs / Judgment** as decision interpretation cards.
- Strengthened Verdict around **Why**, **Action**, **Evidence quality**, and **What would change this verdict**.
- Refined Report as a premium client-ready preview with off-white paper, document metadata, an executive summary, section labels, **Copy summary**, and a restrained export boundary.

### Layout and responsive changes

- Main content is now centered in a responsive container instead of feeling pinned to the left on wide screens.
- Desktop screens use balanced 2-column layouts where appropriate while preserving a dominant main content zone.
- The sidebar collapses into a compact top navigation grid on narrower widths.
- Cards move from multi-column layouts to 2-column and then 1-column layouts at tablet/mobile breakpoints.
- Journey steps wrap instead of forcing page-level horizontal overflow.
- Input and comparison tables scroll inside their card containers, so narrow screens do not require page-level horizontal scroll.
- Fixed-width inline layout rules in the Hypothesis screen were replaced by reusable responsive grid classes.
- Evidence columns, setup controls, report metadata, and trade-off cards collapse from desktop columns to tablet and mobile stacks.

### Design canon alignment

- Uses the Portfolio MRI canon: IBM structure, Linear clarity, BMW premium dark precision, and Stripe/Coinbase financial trust.
- Keeps the deep navy app shell, dark card surfaces, thin slate borders, blue journey/action states, amber caution, red risk/worsening, green real improvement, and rare gold boundary/status accents.
- Uses hierarchy and spacing rather than adding new widgets: hero cards carry the main decision, support cards carry evidence, and detail cards carry subordinate notes.
- Keeps the product away from optimizer-cockpit, trading-terminal, crypto-exchange, and generic-dashboard patterns.

### Boundaries preserved

- Candidate is not a recommendation.
- Verdict is not a trading instruction.
- Reference benchmark is not a rebalance instruction.
- No-trade is a valid decision.
- Evidence insufficient is a valid result.
- AI Commentary explains; it does not decide.

### Remaining limitations

- This is still an HTML mockup, not a production frontend app.
- Sample values are not wired to runtime artifacts.
- Browser QA is lightweight; production implementation would still need a formal accessibility, keyboard, and real-data-density pass.
- Responsive behavior is improved for desktop/tablet widths, but small mobile usability remains a later production concern.
- PDF export remains explicitly outside the MVP surface.

## 11. Design Revision Notes

### What was overloaded

- Portfolio Input repeated currency at row level, making the first screen feel operationally noisy.
- Diagnosis Summary mixed diagnosis, evidence, next steps, and status without a dominant state model.
- Evidence Center had useful cards but read too much like a metrics dashboard.
- Hypothesis Launchpad presented tests as roughly equal choices.
- Builder copy could be interpreted as method configuration rather than hypothesis setup.
- Comparison relied on generic placeholder language and did not put enough weight on materiality, costs, and uncertainty.
- Report preview felt closer to a plain document surface than a polished client-ready summary.
- The report boundary was not visible enough for a client-ready surface.

### What changed

- Moved currency to one portfolio-level Investor currency field and removed repeated per-row currency selectors.
- Added allocation validation and a portfolio setup summary line on the input screen.
- Added a dominant decision-state panel to the Diagnosis Summary.
- Added a top evidence headline and Top 3 Evidence block before grouped evidence columns.
- Ranked suggested tests as recommended first test, reference benchmark, targeted test, secondary test, and optional test.
- Renamed the right panel to **Configure test** and added helper copy that the setup does not create a recommendation.
- Replaced placeholder/draft copy with client-ready review language.
- Added a comparison caution line, a trade-off hero summary, and separated improvements / costs / judgment.
- Strengthened the verdict card with explicit **Why**, **Action**, and **What would change this verdict** sections.
- Refined the report preview with off-white paper, metadata, executive summary, more spacing, section labels, and **Copy summary** as the primary action.
- Added a visible report boundary explaining that the summary is decision-support evidence.

### Why the revised version is more decision-oriented

The revised journey makes the product state visible first, then evidence, then a single hypothesis test, then trade-off interpretation, and only then a verdict. The user is not asked to hunt through charts to infer whether action is justified. Every screen reinforces the boundary that a candidate is a test result and that the verdict is decision-support, not a trading instruction.

### What remains for later UI implementation

- Wire the mockup states to real runtime state flags.
- Replace sample values with calculated values from approved output contracts.
- Add accessible focus states and keyboard flow for the production app.
- Run deeper production responsive QA after real data replaces sample values, especially on small mobile screens.
- Connect copy-to-clipboard behavior to the production app shell and add future export integration when the product scope promotes it.
- Validate real data density after sample values are replaced.
- Test whether users still over-read a no-material-rebalance verdict as advice; if so, strengthen the boundary note.

### UX risks that remain

- Real calculated values may be denser than the sample values and could reintroduce dashboard-like pressure.
- Users may still treat the first ranked hypothesis as a preferred allocation unless boundary copy remains visible.
- Client-ready language can feel authoritative, so evidence quality and decision-support notes must remain visible in production.
- Mobile layouts need a separate usability pass before a production release.

## 12. Lightweight Browser / Screenshot QA Instructions

Mockup file:

`docs/proposals/portfolio_mri_decision_room_mockup.html`

Manual open:

1. Open the file directly in Chrome, Edge, or another modern browser.
2. Click the left sidebar items from Portfolio through Report.
3. Optionally capture screenshots of Diagnosis, Evidence, Hypothesis, Comparison, Verdict, and Report.

Visual checks:

- Diagnosis has one dominant decision-state panel and can be understood in under 30 seconds.
- Evidence starts with a headline and Top 3 Evidence before cards.
- Hypothesis tests are visibly ranked; Equal Weight is the first suggested action.
- Builder reads as hypothesis setup, not a technical method cockpit.
- Comparison values are realistic sample review values and do not claim live calculation.
- Verdict clearly states whether action is justified and why.
- Report feels like a client-ready paper preview and does not expose implementation artifacts.

Pass / fail:

- **Pass** if the mockup feels premium, calm, institutional, and decision-oriented; candidate language stays test-oriented; no prohibited portfolio-superiority language appears.
- **Fail** if any screen reads primarily as a metrics dashboard, a trading app, a method menu, or an implementation report; or if the candidate is framed as an allocation instruction.

## 13. High-Fidelity Mockup File

Interactive-style HTML mockup:

`docs/proposals/portfolio_mri_decision_room_mockup.html`
