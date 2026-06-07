# Portfolio MRI Current Frontend to Stitch Handoff

## Purpose

This document is a Stitch-ready handoff extracted from the currently implemented Portfolio MRI Next.js/React frontend. The current frontend is the source of truth for recreating or updating the Stitch project.

The old Stitch import is not the source of truth for this pass. Do not use old imported HTML as the design reference. Use the implemented React frontend design language, screen structure, and product boundaries described here.

## Source of Truth

Current implemented frontend:

- Next.js app routes for the seven-screen journey.
- React components under the layout, UI, portfolio, diagnosis, evidence, hypothesis, comparison, verdict, and report component groups.
- Global CSS and Tailwind theme tokens.
- Demo review data only for product labels, screen meaning, and current copy patterns.
- Existing design docs only as secondary documentation; the implemented frontend overrides them.

No frontend code, Tailwind config, demo JSON, or backend/Python files should be changed when using this document.

---

## A. Current Frontend Design Summary

### Product Identity

**Product name:** Portfolio MRI  
**Product type:** premium institutional investment decision-support SaaS  
**Product metaphor:** Investment Decision Room

The implemented product is not a dashboard, not a trading terminal, not a crypto interface, and not an optimizer cockpit. It is a structured decision room that walks the user through:

Input portfolio → Diagnosis → Evidence → Hypothesis → Comparison → Verdict → Report

The dominant UX principle is **diagnosis-first, evidence-first, decision-boundary-first**. Candidates are hypothesis tests, not recommendations.

### Current Visual Direction

The implemented frontend uses a dark institutional premium visual system:

- deep navy app background;
- subtle radial blue and gold glow;
- layered navy cards;
- soft slate borders;
- restrained blue active states;
- gold decision accents;
- amber evidence/caution states;
- green improvement/completion states;
- sparse red risk state;
- rounded cards and panels;
- calm typography with strong hierarchy;
- institutional density: compact but not crowded.

### Color Tokens

The current palette is centralized in Tailwind and CSS variables, with some alpha/gradient values still used inline in classes. Stitch should preserve these colors and consolidate alpha variants into named tokens if possible.

| Role | Current value | Current usage |
| --- | --- | --- |
| App background | `#07111F` | Main dark institutional background. |
| Secondary background | `#0D1B2A` | Sidebar, table headers, secondary panels. |
| Card surface | `#12263A` | Main premium cards and panels. |
| Elevated surface | `#172B42` | Available surface token for elevated layers. |
| Dark panel | `#1C1F29` | Available neutral panel token. |
| Main border | `#334155` | Card borders, table dividers, navigation borders. |
| Soft border | `#434655` | Available softer border token. |
| Text primary | `#F8FAFC` | Headings, major values, high-priority labels. |
| Text secondary | `#CBD5E1` | Descriptions and body copy. |
| Text muted | `#94A3B8` | Captions, labels, inactive states. |
| Action blue | `#3B82F6` | Active journey state, focus ring, blue badges. |
| Blue soft | `#60A5FA` | Active text, step kickers, blue highlights. |
| Positive green | `#10B981` | Improvements, completed steps, sufficient input. |
| Warning amber | `#F59E0B` | Evidence quality, caution, trade-off cost. |
| Risk red | `#EF4444` | Worsening or risk states; use sparingly. |
| Premium gold | `#D4AF37` | Brand, decision boundaries, hero accents, verdict weight. |

### Surfaces

Current surface language:

- **Page background:** deep navy plus subtle blue/gold radial gradient.
- **Main cards:** `pmri-card` with slate border, navy gradient, and heavy soft shadow.
- **Interior panels:** low-opacity white overlays such as `bg-white/[0.03]`.
- **Status panels:** low-opacity semantic background, for example blue/gold/amber/green at about 10% opacity.
- **Tables:** dark secondary header, low-opacity row backgrounds, slate dividers, subtle hover state.

The core card background currently behaves like:

```text
border: rgba(51, 65, 85, 0.88)
background: linear-gradient(180deg, rgba(18, 38, 58, 0.92), rgba(13, 27, 42, 0.86))
shadow: 0 24px 80px rgba(0, 0, 0, 0.24)
```

### Borders

- Main cards: 1px slate border, often `border-pmri-border` or `border-pmri-border/80`.
- Important decision cards: gold-tinted border such as `border-pmri-gold/25` or `border-pmri-gold/30`.
- Active navigation: blue border around active step.
- Status panels: semantic low-opacity borders.
- Tables: slate row dividers and outer border.

### Shadows

- Main premium shadow: `0 24px 80px rgba(0, 0, 0, 0.24)`.
- Tailwind named shadow available: `decision = 0 24px 80px rgba(0, 0, 0, 0.26)`.
- Shadows are used for depth, not for floating consumer-card effects.

### Typography

- Primary font: **Inter**.
- Numeric/mono font: **JetBrains Mono** for step numbers and monospaced details.
- Numeric figures use tabular numerals via `.data-figure`.

Current hierarchy:

- Page title: 30-36px equivalent, semibold, tight tracking.
- Hero title: 30-36px equivalent, semibold, tight line height.
- Section title: 18-24px equivalent, semibold.
- Body: 14-16px equivalent, comfortable line-height.
- Caption/label: 11-12px equivalent, uppercase, semibold, letter-spaced.
- Badge text: 12px equivalent, semibold, compact.

Typography should remain calm, precise, and institutional. Avoid decorative fonts, excessive italics, oversized market-terminal numbers, or all-caps shouting.

### Spacing

Current spacing rhythm:

- App main: max width about 1440px.
- Main padding: `px-4 py-8`, `md:px-8`, `lg:px-10`.
- Page header bottom margin: about 32px.
- Page header bottom padding: about 24px.
- Card padding: 16px for compact metric cards, 20px for standard cards, 24-32px for hero/report cards.
- Grid gaps: usually 16px, 20px, 24px, or 28px depending on screen importance.
- Internal panel gaps: 12px to 24px.

Stitch should preserve generous breathing room around major decision areas while keeping supporting cards compact.

### Radii

Current radius system:

- Major cards and panels: `rounded-2xl`.
- Standard cards, table wrappers, nav items, inner panels: `rounded-xl`.
- Status badges and progress pills: fully rounded.
- Small status dots: fully rounded circles.

This rounded language is premium but restrained. Do not move toward sharp enterprise tables or overly playful pill-heavy UI.

### Layout Rules

- Desktop app shell uses a fixed-width left sidebar and a flexible main area.
- Sidebar appears at large breakpoint and above; hidden below that.
- Sticky top journey progress remains visible across screens.
- Each page begins with the same PageHeader pattern.
- Main content uses card grids and asymmetric panels, not freeform dashboard widgets.
- Every screen has one primary focal point.
- Tables are used for portfolio holdings and comparison details only.

### Sidebar Behavior

Current sidebar:

- hidden on smaller screens;
- 256px wide on desktop;
- dark secondary navy surface with right border;
- brand name in gold;
- subtitle: “Investment Decision Room”;
- seven journey steps;
- active step uses blue border/background and primary text;
- completed steps use green dot and secondary text;
- future steps use muted text and slate dot;
- bottom card reinforces sample review and decision-support boundary.

Preserve the sidebar as a journey navigator, not a general dashboard menu.

### Top Journey Progress

Current top progress:

- sticky at the top;
- translucent dark navy background with backdrop blur;
- small “Status” label;
- horizontal scrollable pill list;
- active step blue;
- completed steps green;
- upcoming steps muted;
- thin line separators between steps.

Preserve it as a calm journey orientation device.

### Page Structure

Every screen follows:

1. PageHeader with step kicker, title, explanation, and status badge.
2. Main focal section.
3. Supporting cards, metrics, tables, or panels.
4. Visible product boundary copy where needed.

### Card Types

Current card types:

- DecisionHeroCard: large conclusion/boundary card.
- MetricCard: compact diagnostic metric card.
- EvidenceCard: source/status/summary evidence card.
- HypothesisCard: candidate-as-test card.
- TradeoffSummary: gold-accented comparison interpretation panel.
- CandidateComparisonPanel: detailed comparison table panel.
- VerdictPanel sections: evidence and monitoring cards.
- ClientReadyReportPreview: report-like narrative panel.
- PortfolioInputTable: portfolio-level summary plus holdings table.

### Button Styles

There is no dedicated button component in the current implementation. The current UI uses `StatusBadge` components for status-like action labels such as “Run diagnosis” or “Preview only.”

For Stitch:

- If real buttons are added, style them as restrained rounded-xl or rounded-full institutional controls.
- Primary action: blue border/background at low opacity, blue-soft text.
- Decision boundary/action warning: gold or amber only when semantically justified.
- Avoid bright filled CTA buttons that make the product feel like a consumer app.
- Avoid trading verbs such as “Buy,” “Sell,” “Execute,” or “Rebalance now.”

### Status Badges

Current badge anatomy:

- inline-flex;
- rounded-full;
- 1px semantic border;
- low-opacity semantic background;
- 12px semibold text;
- compact horizontal padding.

Current tones:

- blue: action/status/review;
- gold: decision boundary/premium state;
- green: improvement/completion;
- amber: caution/evidence quality;
- red: risk/worsening;
- slate: neutral/inconclusive.

### Product Boundary Messages

Current frontend repeatedly reinforces:

- “Decision-support only.”
- “Not a trading instruction.”
- “Candidates are hypothesis tests, not recommended portfolios.”
- “Equal Weight is a diagnostic benchmark, not a recommendation.”
- “No-trade is valid.”
- “Evidence usable, not conclusive.”
- “Stress scenarios are diagnostic tests, not forecasts.”

These boundary messages must remain visible in Stitch. They are part of the product design, not legal footnotes.

---

## B. Screen-by-Screen Current Structure

### 1. Portfolio Input

**Current route meaning:** Portfolio Input  
**Current screen title:** “Define the portfolio under diagnosis”  
**Current status badge:** “Run diagnosis”

**Product purpose:** Establish the portfolio that will be diagnosed. The portfolio is the subject of review, not advice.

**Current sections:**

1. Page header with step kicker and diagnosis-first explanation.
2. Portfolio construction card.
3. Portfolio-level summary tiles:
   - Investor currency;
   - Total allocation;
   - Cash included.
4. Holdings table:
   - Ticker / Instrument;
   - Weight %.
5. Input boundary hero card.
6. Input assumptions card.

**Main components:** PageHeader, PortfolioInputTable, DecisionHeroCard, StatusBadge.

**Layout:** Two-column desktop layout: large portfolio table left, boundary/assumptions right. Collapses to stacked content on smaller screens.

**Visual hierarchy:** Portfolio table is primary. Boundary card is secondary but visually important due to gold accent.

**Key copy to preserve:**

- “Define the portfolio under diagnosis”
- “This is the current portfolio, not advice.”
- “Starting weights are the subject of diagnosis, not a recommendation.”
- “Currency is selected once at portfolio level.”

**Must preserve in Stitch:** The screen must feel like a portfolio review setup, not an order ticket or optimizer input form.

### 2. Diagnosis Summary

**Current screen title:** “Diagnosis summary before any candidate”  
**Current status badge:** “Diagnosis ready”

**Product purpose:** Explain the main current-portfolio problem before candidate generation.

**Current sections:**

1. Page header with “does not jump to optimization” framing.
2. Decision hero: diagnosis before action.
3. Evidence and next-step badges.
4. Metric cards.
5. Top diagnosis drivers.

**Main components:** PageHeader, DiagnosisSummaryPanel, DecisionHeroCard, MetricCard, StatusBadge.

**Layout:** Vertical stack: hero, metric row, driver grid.

**Visual hierarchy:** Hero diagnosis headline dominates, metrics provide compact evidence, driver cards explain rationale.

**Key copy to preserve:**

- “Diagnosis summary before any candidate”
- “Concentration and equity factor exposure dominate the current portfolio risk story.”
- “Diagnosis before action”
- “Diagnosis explains observed portfolio structure; it is not a suitability review or trading instruction.”

**Must preserve in Stitch:** Diagnosis must precede any candidate or optimization language.

### 3. Evidence Center

**Current screen title:** “Evidence Center”  
**Current status badge:** “Evidence first”

**Product purpose:** Organize X-Ray, stress, classification, and input-quality signals before any candidate test.

**Current sections:**

1. Page header.
2. Evidence hero card.
3. Metric cards.
4. Evidence card grid.

**Main components:** PageHeader, EvidenceCenter, DecisionHeroCard, MetricCard, EvidenceCard, StatusBadge.

**Layout:** Vertical stack with metrics row and two-column evidence card grid on desktop.

**Visual hierarchy:** Evidence headline first, then quantitative/context metrics, then individual evidence items.

**Key copy to preserve:**

- “X-Ray and Stress evidence point to concentrated growth-equity sensitivity with partial defensive ballast.”
- “Evidence usable, not conclusive”
- “Stress scenarios are diagnostic tests, not forecasts.”
- Evidence item types: X-Ray, Stress, Classification, Input Quality.

**Must preserve in Stitch:** Evidence should look curated and review-ready, not like raw data output.

### 4. Hypothesis Launchpad

**Current screen title:** “Launch a candidate hypothesis test”  
**Current status badge:** “Not a recommendation”

**Product purpose:** Choose one candidate hypothesis to test against the diagnosis.

**Current sections:**

1. Page header with explicit benchmark boundary.
2. Hypothesis card grid.
3. Guided test setup panel.
4. Guardrails before comparison.

**Main components:** PageHeader, HypothesisCard, HypothesisBuilderPanel, StatusBadge.

**Layout:** Desktop asymmetric layout: hypothesis cards in main area, guided setup panel on the right. Hypothesis cards use a two-column grid.

**Visual hierarchy:** Candidate hypotheses first, selected test/setup second, guardrails visible.

**Key copy to preserve:**

- “A candidate is a testable hypothesis against the diagnosis.”
- “Equal Weight and Risk Parity are diagnostic benchmarks, not recommendations.”
- “Candidates are hypothesis tests, not recommended portfolios.”
- “Show trade-offs before verdict.”

**Must preserve in Stitch:** Candidate cards must never read like recommended allocations.

### 5. Current vs Candidate Comparison

**Current screen title:** “Current vs candidate comparison”  
**Current status badge:** “Trade-off required”

**Product purpose:** Compare the current portfolio against the selected diagnostic benchmark and force balanced interpretation.

**Current sections:**

1. Page header.
2. Trade-off summary.
3. Detailed comparison panel.
4. Comparison table.

**Main components:** PageHeader, TradeoffSummary, CandidateComparisonPanel, StatusBadge.

**Layout:** Vertical stack. TradeoffSummary comes before the table. Inside TradeoffSummary, three desktop columns: What changed, What it costs, What remains unclear.

**Visual hierarchy:** Trade-off conclusion first, detailed metrics second.

**Key copy to preserve:**

- “Improvement is visible, but it does not automatically justify action.”
- “What changed”
- “What it costs”
- “What remains unclear”
- “Equal Weight is a diagnostic benchmark, not a recommendation.”
- “No-trade valid”

**Must preserve in Stitch:** Improvements and costs must be visually balanced. Avoid winner/loser framing.

### 6. Decision Verdict

**Current screen title:** “Decision verdict”  
**Current status badge:** “Decision-support only”

**Product purpose:** State whether evidence supports action, no-trade, or insufficient evidence.

**Current sections:**

1. Page header.
2. Verdict hero.
3. Verdict state/evidence/action metric cards.
4. Key evidence behind verdict.
5. Monitoring trigger.
6. Decision boundary note.

**Main components:** PageHeader, VerdictPanel, DecisionHeroCard, MetricCard, StatusBadge.

**Layout:** Vertical stack. Supporting evidence/monitoring uses two-column desktop grid.

**Visual hierarchy:** Verdict hero first, key metrics second, evidence and monitoring third.

**Key copy to preserve:**

- “No material rebalance is justified by the current evidence set.”
- “Evidence supports no-trade for now”
- “Verdict is decision-support only. It is not a trading instruction.”
- “Not a trading instruction”
- “Monitoring trigger”

**Must preserve in Stitch:** No-trade must look like a valid, premium decision outcome, not a failure state.

### 7. Client-ready Report

**Current screen title:** “Client-ready report preview”  
**Current status badge:** “Preview only”

**Product purpose:** Present a concise advisor/client-ready narrative without turning it into advice.

**Current sections:**

1. Page header.
2. Report preview card.
3. Report title and subtitle.
4. Executive summary gold panel.
5. Supporting report sections.
6. Monitoring panel.
7. Decision boundary panel.

**Main components:** PageHeader, ClientReadyReportPreview, StatusBadge.

**Layout:** Large report card. Supporting sections use a two-column grid; monitoring and boundary use an asymmetric two-column grid.

**Visual hierarchy:** Report title/subtitle, executive summary, supporting sections, monitoring/boundary.

**Key copy to preserve:**

- “Portfolio MRI decision-support summary”
- “Sample portfolio review for stakeholder discussion”
- “Executive summary”
- “This report explains decision-support evidence. It is not advice, suitability review, or a trading instruction.”

**Must preserve in Stitch:** The report preview should feel like a polished client-ready review summary, not a generated artifact viewer.

---

## C. Differences From Old Stitch Import

The old Stitch import was intentionally not used as a source for this handoff.

Obvious direction change:

- Source of truth is now the implemented Next.js/React frontend, not an imported Stitch/HTML artifact.
- Stitch should be updated or recreated to match the current implemented seven-screen decision-room UI.
- Any old Stitch screens that conflict with the current React routes, card system, color system, or product boundaries should be treated as stale.
- If the old Stitch import includes dashboard, optimizer cockpit, generic analytics, raw implementation language, or older product framing, it should be replaced by the current decision-room flow.

Recommended comparison, if needed later: open old Stitch only after this handoff is approved, then compare screen by screen against this document.

---

## D. Stitch MCP Capability Check

Available Stitch MCP tools in the current environment:

- `create_design_system`
- `update_design_system`
- `apply_design_system`
- `upload_design_md`
- `create_design_system_from_design_md`
- `list_design_systems`

### What appears supported

- Create a design system for a project.
- Update an existing project's design system.
- Upload a DESIGN.md file to a project.
- Create a design system from an uploaded DESIGN.md file.
- Apply an existing design system to selected screen instances.
- List design systems.

### What is not visible in the currently exposed Stitch tools

- Create a new Stitch project.
- Read/get an existing Stitch project structure.
- Create a new screen from scratch.
- Update screen layout/content directly.
- Recreate the seven screens directly from this MCP toolset.
- Import the current React frontend into Stitch as screens.

### Practical interpretation

The Stitch MCP is **not read-only**, because it can create/update/apply design systems. However, with the currently exposed tools, it looks **design-system-oriented**, not full project/screen-authoring-oriented.

To update an existing Stitch project through MCP, we would need at minimum:

- existing Stitch `projectId`;
- selected screen instance IDs;
- source screen resource names;
- confirmation to upload/apply a design system.

Without those IDs, the safe action is to prepare this handoff and wait.

---

## E. Recommended Safe Path

### Best path if Stitch project update is supported with IDs

1. User provides existing Stitch `projectId` and target screen instance IDs.
2. Upload this handoff as DESIGN.md using Stitch MCP.
3. Create or update the project design system from the uploaded DESIGN.md.
4. Apply the design system to existing screen instances.
5. Manually or separately recreate the actual screen layouts if Stitch MCP cannot author layouts.

### Best path if a new Stitch project must be created

The currently exposed Stitch MCP tools do not show project creation. If Stitch's UI supports creating a new project, create it manually in Stitch first, then provide the project ID. After that, use this handoff to create the design system.

### Best path if Stitch MCP remains design-system-only

Manually paste this handoff into Stitch as the design brief/context, then generate or recreate the seven screens in Stitch using the current frontend as reference.

### Best path if direct screen creation tools become available later

Use this document as the screen-by-screen generation spec and recreate:

1. Portfolio Input
2. Diagnosis Summary
3. Evidence Center
4. Hypothesis Launchpad
5. Current vs Candidate Comparison
6. Decision Verdict
7. Client-ready Report

Each generated screen should preserve the current React component hierarchy and decision-boundary copy.

---

## F. Preservation Checklist for Stitch

Stitch must preserve:

- Portfolio MRI as Investment Decision Room.
- Seven-screen journey and exact ordering.
- Dark institutional navy background.
- Premium navy card surfaces.
- Restrained blue active/action language.
- Gold decision accents.
- Amber evidence caution.
- Green improvement/completion.
- Red only for risk/worsening.
- Sidebar journey navigation.
- Sticky top journey progress.
- PageHeader pattern on every screen.
- DecisionHeroCard as main conclusion component.
- Evidence cards with source/status/summary.
- Trade-off summary before comparison table.
- Verdict as decision-support only.
- Client-ready report preview.
- Candidate does not mean recommendation.
- Verdict does not mean trading instruction.
- No-trade is valid.
- Evidence insufficient is valid.
- Equal Weight and Risk Parity are diagnostic benchmarks.
- AI commentary explains, but does not decide.

Stitch should avoid:

- dashboard framing;
- trading terminal aesthetics;
- crypto-terminal colors;
- optimizer cockpit language;
- “best portfolio” or “recommended allocation” labels;
- backend/API/JSON/raw artifact language;
- implementation notes in user-facing UI;
- raw data dumps;
- over-dense market widgets.

---

## Final Stitch Prompt

Using the current implemented Portfolio MRI frontend as the source of truth, recreate or update the Stitch project as a premium dark institutional Investment Decision Room. Preserve the seven-screen journey: Portfolio Input, Diagnosis Summary, Evidence Center, Hypothesis Launchpad, Current vs Candidate Comparison, Decision Verdict, and Client-ready Report. Match the current navy/gold/blue/amber/green visual language, sidebar journey navigation, sticky top progress, page headers, premium cards, status badges, evidence cards, trade-off panels, verdict panels, and report preview structure. Remove developer or implementation language. Preserve all decision-support boundaries: candidates are hypothesis tests, verdicts are not trading instructions, no-trade is valid, and evidence-insufficient is valid.
