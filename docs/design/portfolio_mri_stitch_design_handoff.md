# Portfolio MRI Stitch Design Handoff

## 1. Product Identity

**Product name:** Portfolio MRI  
**Product type:** investment decision-support SaaS  
**Product metaphor:** Investment Decision Room

Portfolio MRI is not a dashboard. It is not a trading app, crypto terminal, optimizer cockpit, market-monitoring console, or generic analytics workspace. The interface should feel like a calm institutional room where an advisor reviews a portfolio, organizes evidence, tests a hypothesis, compares trade-offs, and reaches a decision-support verdict.

The product should communicate:

- diagnosis before action;
- current portfolio before candidates;
- evidence before verdict;
- trade-offs before any conclusion;
- client-ready clarity without implying advice.

## 2. Target User

Primary users:

- independent investment advisors and financial advisors;
- sophisticated self-directed investors;
- client-facing investment professionals who need to explain portfolio decisions clearly.

The UI must feel:

- client-ready;
- calm;
- premium;
- institutional;
- trustworthy;
- precise without looking technical or developer-oriented.

Avoid visual drama, excessive charts, neon-finance styling, trading-terminal density, or consumer crypto aesthetics.

## 3. Core User Journey

Portfolio MRI follows a seven-screen decision journey:

1. **Portfolio Input** — define the portfolio under review.
2. **Diagnosis** — identify the main portfolio problem before any candidate appears.
3. **Evidence** — organize X-Ray, stress, classification, and quality signals as decision evidence.
4. **Hypothesis** — choose one candidate hypothesis test.
5. **Comparison** — compare current portfolio vs candidate and expose trade-offs.
6. **Verdict** — state whether the evidence supports action, no-trade, or insufficient evidence.
7. **Report** — preview a client-ready decision-support summary.

The root experience redirects into the decision journey. Stitch should preserve the seven-step flow and the feeling that the user is moving through a structured investment review, not browsing a dashboard.

## 4. Visual Direction

The current frontend uses a dark institutional premium direction:

- **Dark institutional background:** deep navy page background with subtle blue and gold radial light.
- **Premium navy surfaces:** layered navy cards and panels with soft borders and low-opacity glass-like surfaces.
- **Restrained blue actions:** blue is used for active journey state, focus, primary status, and review actions.
- **Gold decision/status accents:** gold marks decision boundaries, premium brand identity, key verdict moments, and hero emphasis.
- **Green improvement:** green marks improvement, completion, positive change, or sufficient input quality.
- **Amber caution/evidence quality:** amber marks usable-but-not-conclusive evidence, caution, trade-off cost, or review quality.
- **Red risk/worsening:** red is reserved for material risk, deterioration, or worsening. It should be used sparingly.
- **Card-based layout:** every screen is built from strong rounded cards with clear internal hierarchy.
- **Sidebar navigation:** fixed left decision-room navigation on desktop.
- **Top journey progress:** sticky horizontal journey status at the top of the main content.
- **Decision hero cards:** major screen conclusions use large premium cards with gold/blue glow accents.
- **Evidence cards:** evidence is packaged into calm, readable cards with source and status.
- **Trade-off panels:** comparison must show what improved, what it costs, and what remains unclear.
- **Verdict panels:** verdict must feel serious, bounded, and non-instructional.
- **Report preview panels:** report screen should look like a polished client-facing summary, not a raw output viewer.

## 5. Color System

Current colors are partially centralized as frontend tokens. Exact hex values exist for the primary palette, but several surface overlays, alpha borders, gradients, and white translucency values are used directly in components. This means the design system **needs token consolidation** before a final production design system.

| Role | Hex / Value | Intended Usage |
| --- | --- | --- |
| Background primary | `#07111F` | Main app background; deepest institutional navy. |
| Background secondary | `#0D1B2A` | Sidebar, table headers, secondary page surfaces. |
| Surface card | `#12263A` | Main card base and premium panels. |
| Surface elevated | `#172B42` | Secondary elevated surface; available token, not consistently used. |
| Dark panel | `#1C1F29` | Dark neutral panel token; available but not a dominant current surface. |
| Border | `#334155` | Main borders, table dividers, card outlines. |
| Border soft | `#434655` | Softer border token; available but not consistently used. |
| Text primary | `#F8FAFC` | Main headings, key values, high-priority copy. |
| Text secondary | `#CBD5E1` | Descriptions, body copy, explanatory text. |
| Text muted | `#94A3B8` | Labels, captions, inactive states, metadata. |
| Action blue | `#3B82F6` | Active navigation, focus ring, primary review status, blue panels. |
| Action blue soft | `#60A5FA` | Kicker labels, active status text, blue highlights. |
| Gold accent | `#D4AF37` | Brand mark, decision boundaries, premium accent, hero emphasis. |
| Success green | `#10B981` | Improvement, completed steps, sufficient inputs, positive status. |
| Warning amber | `#F59E0B` | Evidence quality, caution, trade-off cost, inconclusive signals. |
| Risk red | `#EF4444` | Risk, worsening, material deterioration. Use only when needed. |
| Card gradient | `linear-gradient(180deg, rgba(18, 38, 58, 0.92), rgba(13, 27, 42, 0.86))` | Current premium card background. Needs token consolidation. |
| Page glow | blue/gold radial gradients | Subtle institutional depth; should stay soft and non-decorative. Needs token consolidation. |
| Translucent surface | `rgba(255,255,255,0.03)` and nearby values | Interior panels and quiet contrast. Needs token consolidation. |

Color guidance for Stitch:

- Use navy as the dominant environment.
- Use gold for decision significance, not for every highlight.
- Use blue for active state and interaction, not as a loud CTA color.
- Use amber to communicate evidence caution, not failure.
- Use green for improvement, not investment performance promises.
- Use red only for risk or worsening; avoid alarming the interface.

## 6. Typography

**Font family:** Inter for all primary UI text.  
**Mono/numeric font:** JetBrains Mono for step numbers and numeric figure styling where useful. Numeric values should use tabular numerals.

Typography behavior:

- **Headings:** semibold, tight tracking, calm and precise. Main page titles use large 3xl-4xl sizing with slight negative letter spacing.
- **Section headings:** semibold, usually 18-24px equivalent, with clear spacing above body copy.
- **Body text:** 14-16px equivalent, comfortable line-height, muted secondary text color.
- **Labels/captions:** uppercase, small, semibold, wide tracking; used for stages, metadata, evidence type, and panel labels.
- **Badges:** small semibold text inside rounded pill borders.
- **Numbers:** tabular, calm, precise; avoid oversized trading-terminal numerics.

Italic guidance:

- Avoid excessive italic text.
- Do not use italics as the main premium cue.
- If italics are used, reserve them for rare editorial emphasis in report-like copy, not navigation, labels, metrics, or verdicts.

Overall tone: calm, exact, institutional, not decorative.

## 7. Layout System

### App shell

The app uses a full-height dark shell with a desktop sidebar and a main content region. The main content sits inside a maximum width of about 1440px with responsive horizontal padding.

### Sidebar

The sidebar is a 256px desktop navigation rail. It contains:

- product name in gold;
- product metaphor subtitle;
- seven journey steps;
- active, complete, and inactive step states;
- a bottom boundary card reminding that the review is decision-support only.

On smaller screens, the current sidebar is hidden and the top progress bar carries journey orientation.

### Top journey progress

The top progress bar is sticky. It uses small rounded pills for each journey step, with blue for active, green for completed, and muted borders for upcoming steps. It should feel like review progress, not a task tracker.

### Page header

Each page begins with:

- uppercase blue step kicker;
- large page title;
- explanatory description;
- one right-aligned status badge.

### Main content width

Main content should remain spacious and readable. Do not push the interface into dense terminal-like layouts. Wide screens can use two-column or three-column grids, but every screen needs a clear focal point.

### Card grid

Current grids use:

- 2-column cards for hypothesis and evidence;
- 3-card metric rows;
- 2-column verdict/report supporting sections;
- asymmetric layouts for input and hypothesis setup.

### Responsive expectations

- Desktop: sidebar + sticky top progress + multi-column cards.
- Tablet: top progress remains, cards collapse gradually.
- Mobile: single-column journey, strong page header, horizontal overflow only where tables require it.

### Page-level focal point rule

Every screen needs one dominant focal point:

- Input: the portfolio table.
- Diagnosis: the diagnosis hero.
- Evidence: the evidence hero plus evidence cards.
- Hypothesis: the selected hypothesis and setup panel.
- Comparison: trade-off summary first, table second.
- Verdict: verdict hero first, evidence/monitoring second.
- Report: executive summary preview first.

## 8. Component Language

### AppShell

**Purpose:** create the Investment Decision Room frame.  
**Visual behavior:** full-height dark navy environment, sidebar on desktop, sticky top journey progress, centered content.  
**Communicates:** structured review, controlled environment, premium decision context.  
**Do not:** turn it into a generic dashboard shell with crowded widgets.

### Sidebar

**Purpose:** orient the user in the seven-step journey.  
**Visual behavior:** dark navy rail, gold brand, active blue step, completed green dots, muted future steps.  
**Communicates:** progression through an investment review.  
**Do not:** add trading menu items, market widgets, account settings, or generic admin navigation.

### TopJourneyProgress

**Purpose:** keep journey context visible at all times.  
**Visual behavior:** sticky translucent top bar with compact step pills.  
**Communicates:** current review status.  
**Do not:** make it a loud progress meter or gamified checklist.

### PageHeader

**Purpose:** define each screen's role in the decision journey.  
**Visual behavior:** blue uppercase kicker, large semibold title, explanatory copy, status badge.  
**Communicates:** where the user is and why this screen matters.  
**Do not:** use technical route names, implementation labels, or backend status copy.

### DecisionHeroCard

**Purpose:** show the screen's primary conclusion or boundary.  
**Visual behavior:** large premium card, gold/blue subtle glow, strong title, supporting explanation, optional badges.  
**Communicates:** the main decision-room insight.  
**Do not:** use it for raw data dumps, logs, or dense tables.

### EvidenceCard

**Purpose:** package one evidence item into a readable unit.  
**Visual behavior:** rounded card, evidence type label, title, status badge, summary, evidence source.  
**Communicates:** why a conclusion is supported or limited.  
**Do not:** expose raw files, JSON, backend artifacts, or internal source names.

### MetricCard

**Purpose:** show one compact metric or state.  
**Visual behavior:** label, status badge if relevant, large tabular value, muted detail.  
**Communicates:** a diagnostic measurement, not a performance promise.  
**Do not:** overemphasize numbers like a trading terminal.

### StatusBadge

**Purpose:** mark state, evidence quality, boundary, improvement, caution, or risk.  
**Visual behavior:** small rounded pill with low-opacity colored background and border.  
**Communicates:** classification without shouting.  
**Do not:** use badges as decorative confetti or imply recommendations.

### PortfolioInputTable

**Purpose:** show the portfolio being reviewed.  
**Visual behavior:** premium card with portfolio-level summary tiles and holdings table.  
**Communicates:** these weights are the subject of diagnosis.  
**Do not:** frame the table as an order ticket, model portfolio editor, or advice form.

### DiagnosisSummaryPanel

**Purpose:** summarize the main portfolio problem before candidates.  
**Visual behavior:** decision hero, metric row, top diagnosis driver cards.  
**Communicates:** diagnosis-first thinking.  
**Do not:** jump to optimization, portfolio scores, or action recommendations.

### HypothesisCard

**Purpose:** present a testable candidate hypothesis.  
**Visual behavior:** card with test approach, target problem, expected trade-off, evidence source, and boundary note.  
**Communicates:** candidate as hypothesis, not recommendation.  
**Do not:** call candidates “best portfolio,” “recommended allocation,” or “optimal.”

### HypothesisBuilderPanel

**Purpose:** guide the user toward one bounded hypothesis test.  
**Visual behavior:** right-side setup panel with selected method, boundary note, and guardrails.  
**Communicates:** disciplined test setup.  
**Do not:** create a full optimizer cockpit or multi-candidate arena.

### CandidateComparisonPanel

**Purpose:** compare current portfolio and candidate in a balanced way.  
**Visual behavior:** calm panel with summary, quality badges, boundary note, and comparison table.  
**Communicates:** changes, direction, and trade-offs.  
**Do not:** rank candidates as winners or imply an automatic action.

### TradeoffSummary

**Purpose:** force balanced interpretation before verdict.  
**Visual behavior:** gold-accented hero panel with three sections: what changed, what it costs, what remains unclear.  
**Communicates:** improvement is not automatically a reason to trade.  
**Do not:** hide costs, uncertainty, or mandate fit questions.

### VerdictPanel

**Purpose:** state the decision-support verdict and boundaries.  
**Visual behavior:** decision hero, metrics, key evidence panel, monitoring trigger panel.  
**Communicates:** evidence supports action, no-trade, or insufficient evidence.  
**Do not:** convert the verdict into trading instructions.

### ClientReadyReportPreview

**Purpose:** preview a polished client-facing summary.  
**Visual behavior:** report-like card, gold executive summary block, supporting sections, monitoring and boundary panels.  
**Communicates:** advisor-ready narrative with clear limits.  
**Do not:** show implementation notes, raw artifacts, backend labels, or developer disclaimers.

## 9. Product Copy Rules

Remove developer, backend, and internal language from user-facing UI.

Stitch should avoid these words and phrases in the interface:

- JSON;
- backend;
- API;
- static demo data;
- source artifact;
- no live backend connected;
- implementation notes;
- raw data;
- technical plumbing;
- generated artifact;
- route;
- component;
- config;
- payload.

Use these alternatives:

- portfolio review;
- sample review;
- evidence source;
- diagnostic benchmark;
- decision-support only;
- hypothesis test;
- review data;
- evidence quality;
- monitoring trigger;
- input completeness;
- review preview;
- current portfolio;
- candidate hypothesis;
- decision boundary.

Copy tone:

- calm, precise, institutional;
- clear enough for advisor/client discussion;
- never overconfident;
- avoid sales hype;
- avoid quant jargon unless the screen explains it;
- prefer “supports,” “indicates,” “suggests,” and “requires review” over “proves.”

## 10. Product Boundaries

Stitch must preserve these product boundaries:

- Candidate does not mean recommendation.
- Verdict does not mean trading instruction.
- No-trade is a valid outcome.
- Evidence insufficient is a valid outcome.
- Equal Weight and Risk Parity are diagnostic benchmarks, not allocation advice.
- AI commentary explains, but does not decide.
- Diagnosis is not suitability review.
- Stress scenarios are diagnostic tests, not forecasts.
- Client-specific constraints are required before real action.

## 11. Screen-by-Screen Design Guidance

### 1. Portfolio Input

**Purpose:** define the current portfolio under review.  
**Main focal point:** portfolio construction table and portfolio-level input summary.  
**Key sections:** page header, portfolio table, input boundary hero, input assumptions.  
**Key components:** PageHeader, PortfolioInputTable, DecisionHeroCard, StatusBadge.  
**Visual hierarchy:** table and allocation summary first; boundary note second; assumptions third.  
**Words/labels to avoid:** order, trade, optimize now, backend, raw data, JSON, upload payload.  
**Premium feel:** this screen should feel like an advisor preparing a review file, not filling a retail trading form.

### 2. Diagnosis

**Purpose:** explain the primary portfolio issue before any candidate is considered.  
**Main focal point:** diagnosis hero card.  
**Key sections:** diagnosis headline, evidence quality, next step, metrics, top diagnosis drivers.  
**Key components:** PageHeader, DecisionHeroCard, MetricCard, StatusBadge, DiagnosisSummaryPanel.  
**Visual hierarchy:** headline problem first; metrics second; drivers third.  
**Words/labels to avoid:** scorecard as final truth, optimize, best portfolio, recommendation, trading signal.  
**Premium feel:** a calm investment committee diagnosis note, not a flashing alert dashboard.

### 3. Evidence

**Purpose:** organize the evidence behind the diagnosis.  
**Main focal point:** evidence center hero and evidence cards.  
**Key sections:** evidence headline, evidence quality, metrics, evidence cards.  
**Key components:** PageHeader, DecisionHeroCard, MetricCard, EvidenceCard.  
**Visual hierarchy:** evidence conclusion first; quality and limits visible; individual evidence cards follow.  
**Words/labels to avoid:** raw source, backend file, implementation artifact, JSON, data dump.  
**Premium feel:** like a curated diligence packet with evidence quality clearly marked.

### 4. Hypothesis

**Purpose:** choose one candidate hypothesis test after evidence review.  
**Main focal point:** selected hypothesis and guided setup panel.  
**Key sections:** hypothesis cards, selected test setup, guardrails.  
**Key components:** PageHeader, HypothesisCard, HypothesisBuilderPanel, StatusBadge.  
**Visual hierarchy:** candidate-as-test framing first; selected method second; guardrails third.  
**Words/labels to avoid:** recommended portfolio, optimal portfolio, allocation advice, one-click rebalance, optimizer cockpit.  
**Premium feel:** structured investment reasoning, not a portfolio construction game.

### 5. Comparison

**Purpose:** compare current portfolio vs candidate and expose trade-offs.  
**Main focal point:** trade-off summary.  
**Key sections:** what changed, what it costs, what remains unclear, detailed comparison table.  
**Key components:** PageHeader, TradeoffSummary, CandidateComparisonPanel, StatusBadge.  
**Visual hierarchy:** balanced trade-off interpretation first; table detail second.  
**Words/labels to avoid:** winner, better portfolio, recommended action, automatic rebalance, final ranking.  
**Premium feel:** an investment committee comparison memo with explicit uncertainty.

### 6. Verdict

**Purpose:** state whether the evidence supports action, no-trade, or insufficient evidence.  
**Main focal point:** verdict hero card.  
**Key sections:** verdict state, evidence quality, key evidence, monitoring trigger, decision boundary.  
**Key components:** PageHeader, VerdictPanel, DecisionHeroCard, MetricCard, StatusBadge.  
**Visual hierarchy:** verdict first; evidence and monitoring second; boundary always visible.  
**Words/labels to avoid:** buy, sell, execute, trade now, instruction, guaranteed outcome.  
**Premium feel:** serious, bounded, and boardroom-ready; no-trade should look as legitimate as action.

### 7. Report

**Purpose:** preview a client-ready decision-support narrative.  
**Main focal point:** executive summary report block.  
**Key sections:** report title/subtitle, executive summary, evidence, candidate hypothesis, comparison, verdict boundary, monitoring.  
**Key components:** PageHeader, ClientReadyReportPreview, StatusBadge.  
**Visual hierarchy:** executive summary first; supporting sections second; monitoring and decision boundary last.  
**Words/labels to avoid:** generated markdown, artifact, PDF pipeline, backend output, raw data, implementation note.  
**Premium feel:** polished advisor-client review summary that can be read aloud in a meeting.

## 12. What Stitch Should Generate Next

Using this design system, generate an updated Portfolio MRI interface with the same 7-screen decision journey, preserving the current dark institutional premium direction, but removing developer-language and improving density, hierarchy and client-ready polish.

The generated interface should:

- keep Portfolio MRI as an Investment Decision Room;
- preserve the seven screens: Portfolio Input, Diagnosis, Evidence, Hypothesis, Comparison, Verdict, Report;
- maintain dark navy institutional surfaces, restrained blue actions, gold decision accents, green improvement, amber caution, and red risk;
- make every screen feel client-ready and advisor-usable;
- improve spacing, hierarchy, and polish without making the UI look decorative;
- avoid backend, API, JSON, raw artifact, or implementation language;
- preserve all decision-support boundaries.

## 13. Do Not Include

Do not include:

- raw backend details;
- Python architecture;
- API implementation;
- implementation labels;
- code snippets except design tokens;
- trading instructions;
- recommendation language;
- optimizer-cockpit framing;
- crypto-terminal aesthetics;
- generic dashboard framing.
