# Portfolio MRI Design System

## Status

This file is the canonical UI/UX design direction for Portfolio MRI / Portfolio X-Ray / ДИАГНОСТИКА 2 product UI work.

It governs product screens, navigation, visual hierarchy, decision cards, generated HTML surfaces, and client-ready UI presentation. It does not override [SPEC.md](../../SPEC.md), [RULES.md](../../RULES.md), [OUTPUTS.md](../../OUTPUTS.md), implementation code, formulas, data rules, policy logic, or output contracts.

Reference systems were used only as inspiration:

- IBM: enterprise structure, trust, information architecture, accessibility discipline.
- Linear: clean workflow, minimal product UI, precise spacing, low-friction task progression.
- BMW / BMW M: premium dark atmosphere, engineering precision, restrained high-contrast accents.
- Stripe / Coinbase: financial trust, simple explanations, clear onboarding, understandable product cards and status language.

Do not copy brand assets, logos, exact layouts, signature gradients, brand typography, or marketing copy from those references.

---

## 1. Product Design Thesis

Portfolio MRI is not a dashboard.

Portfolio MRI is an **Investment Decision Room**.

The UI exists to guide the user through a decision journey:

```text
Portfolio Input
-> Diagnosis
-> Evidence
-> Hypothesis
-> Candidate
-> Comparison
-> Verdict
-> Report
```

The interface must feel calm, precise, trustworthy, dark, analytical, and client-ready. It should look like a premium institutional investment decision-support room, not a trading terminal or optimizer cockpit.

Primary user promise:

> Help the user understand what is wrong, what evidence supports that view, what candidate hypothesis can be tested, what improves or worsens, and whether the evidence is strong enough to support a decision.

The product must never imply that the system is giving a trading instruction.

---

## 2. Design Principles

1. **Diagnosis before action**  
   Show the portfolio diagnosis before showing candidates, comparisons, verdicts, or action framing.

2. **Decision journey, not dashboard**  
   Organize the UI as a guided sequence. Avoid an all-at-once metrics wall.

3. **Evidence first, recommendation never implied**  
   Every conclusion must point back to evidence quality, X-Ray findings, stress findings, or explicit limitations.

4. **Candidate is hypothesis, not recommendation**  
   A candidate portfolio is a hypothesis test. It is not a suggested trade, model answer, or preferred allocation.

5. **Verdict is decision-support, not trading instruction**  
   The verdict helps the user decide whether evidence supports a next step. It does not tell the user to buy, sell, or rebalance.

6. **No-trade is a valid outcome**  
   If the evidence does not support change, the UI must present no-trade as a serious, first-class result.

7. **Evidence insufficient is a valid outcome**  
   Incomplete, low-quality, conflicting, or degraded evidence must be shown honestly.

8. **Show top-level summary, hide technical detail in drill-down**  
   The main screen should answer the decision question. Technical tables, estimator notes, and raw diagnostics belong in expandable detail.

9. **Institutional depth, client-ready clarity**  
   The system can be analytically deep, but the surface must be explainable in five minutes.

10. **Calm, precise, premium, not flashy**  
    Use restraint. Avoid novelty visuals, unnecessary animations, high-frequency color, and terminal-like density.

---

## 3. Brand / Visual Direction

Portfolio MRI uses a hybrid art direction:

- **IBM-inspired structure**: rigorous information architecture, clear hierarchy, serious enterprise tone, accessibility discipline, and predictable navigation.
- **Linear-inspired clarity**: minimal SaaS workflow, compact decision surfaces, fast task progression, precise spacing, and low-friction interaction.
- **BMW-inspired premium dark precision**: deep dark surfaces, confident hierarchy, engineering luxury, technical calm, and high-contrast accents used only where they carry meaning.
- **Stripe / Coinbase-inspired financial trust**: clear product explanations, understandable cards, onboarding copy that reduces anxiety, and status language that frames risk safely.

This is not an imitation of any reference brand. Portfolio MRI’s own style is:

```text
Institutional decision room
+ premium dark analytical environment
+ structured B2B navigation
+ calm financial explanation
+ diagnosis-first product flow
```

Avoid these visual directions:

- crypto exchange;
- retail trading app;
- playful fintech;
- generic dashboard;
- Excel UI;
- optimizer cockpit;
- noisy chart terminal.

---

## 4. Color System

### Core Tokens

| Role | Token | Hex | Usage |
| --- | --- | --- | --- |
| Primary background | `--pmri-bg-primary` | `#07111F` | App shell, page background, decision-room atmosphere. |
| Secondary dark surface | `--pmri-bg-secondary` | `#0D1B2A` | Sidebar, section bands, secondary panels. |
| Card surface | `--pmri-surface-card` | `#12263A` | Evidence cards, verdict cards, comparison modules. |
| Primary text | `--pmri-text-primary` | `#F8FAFC` | Main labels, headings, decisive values. |
| Secondary text | `--pmri-text-secondary` | `#CBD5E1` | Supporting labels, explanatory copy. |
| Muted text | `--pmri-text-muted` | `#94A3B8` | Captions, metadata, inactive steps. |
| Slate border | `--pmri-border` | `#334155` | Card outlines, dividers, table rules. |
| Institutional blue | `--pmri-action-blue` | `#3B82F6` | Primary action, current journey step, navigation selection. |
| Soft blue | `--pmri-action-blue-soft` | `#60A5FA` | Hover, secondary emphasis, inline links. |
| Emerald | `--pmri-positive` | `#10B981` | Improvement, strengthening, risk reduction. |
| Amber | `--pmri-warning` | `#F59E0B` | Caution, evidence insufficient, degraded confidence. |
| Soft red | `--pmri-risk` | `#EF4444` | Worsening, risk, stress failure, material negative trade-off. |
| Muted gold | `--pmri-premium-accent` | `#D4AF37` | Premium boundary/status accent only. |

### Color Meaning

- **Blue = action / journey.** Use for primary CTA, active navigation, progress, and focus states.
- **Green = improvement.** Use only when a metric or diagnosis clearly improves.
- **Red = worsening / risk.** Use only for deterioration, risk, failure, or material negative trade-off.
- **Amber = caution / evidence insufficient.** Use when evidence is degraded, partial, conflicting, or not enough to support action.
- **Gold = premium boundary / status, not decoration.** Use sparingly for premium boundary lines, selected institutional modules, or formal report-ready status. Never use gold as confetti, chart fill, or generic emphasis.

### Usage Rules

- Keep the UI mostly dark navy, slate, and white text.
- Prefer thin borders and subtle surface shifts over heavy shadows.
- Never use red/green as decorative chart color. They must mean worsening/improvement.
- Do not create crypto-style neon palettes.
- Do not use brand-reference colors directly as brand signals.

---

## 5. Typography

Recommended font direction:

- Primary UI: Inter, Geist, SF Pro, or a similar modern neutral sans-serif.
- Numeric data: same family with tabular numbers where available.
- Avoid expressive display fonts, playful rounded type, or heavy all-caps marketing typography.

### Hierarchy

| Role | Suggested size | Weight | Usage |
| --- | --- | --- | --- |
| Page title | 32-40px | 600 | Screen title and decision-room context. |
| Section title | 22-28px | 600 | Major product stage: Diagnosis, Evidence, Verdict. |
| Card title | 16-20px | 600 | Decision cards and evidence modules. |
| UI label | 12-14px | 500-600 | Navigation, badges, field labels, step labels. |
| Body | 14-16px | 400 | Short explanatory copy. |
| Metadata | 12-13px | 400 | Sources, timestamps, confidence notes. |
| Numeric emphasis | 20-32px | 600 | Only for top-level decision-relevant values. |

### Typography Rules

- Use strong hierarchy, not long paragraphs.
- Keep main UI copy short and concrete.
- Use sentence case for most labels.
- Use small uppercase only for compact status labels, not as the dominant voice.
- Put technical evidence in expandable details.
- Use tabular figures for values in tables and metric cards.
- Avoid false precision: do not over-emphasize decimals when the decision does not depend on them.

---

## 6. Layout System

### App Frame

The default Portfolio MRI UI layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ Top journey progress: Input -> Diagnosis -> Hypothesis -> ... │
├──────────────┬───────────────────────────────┬───────────────┤
│ Left sidebar │ Main decision content         │ Optional      │
│ navigation   │                               │ right panel   │
│              │ Evidence cards, comparisons,  │ Explanation,  │
│              │ verdict, report preview       │ commentary,   │
│              │                               │ next step     │
└──────────────┴───────────────────────────────┴───────────────┘
```

### Left Sidebar Navigation

Use stable stage navigation:

1. Portfolio
2. Diagnosis
3. Evidence
4. Hypothesis
5. Comparison
6. Verdict
7. Report

Sidebar rules:

- Keep labels short.
- Show completion state and current stage.
- Do not show advanced tools in the main navigation.
- Keep legacy optimizer screens out of the Core MVP path.

### Top Journey Progress

Use the journey progress bar:

```text
Input -> Diagnosis -> Evidence -> Hypothesis -> Comparison -> Verdict -> Report
```

Progress rules:

- Blue marks the current active step.
- Muted slate marks not-yet-reached steps.
- Green may mark completed evidence only when completion is meaningful.
- Amber marks blocked, degraded, or evidence-insufficient steps.

### Main Decision Content

Main content should answer one question per screen:

- What did we receive?
- What is the diagnosis?
- What evidence supports it?
- What hypothesis are we testing?
- What changed versus current?
- Is the evidence enough for a verdict?
- How can this be explained to a client?

### Optional Right Panel

Use a right panel for:

- AI Commentary;
- evidence quality;
- decision boundary notes;
- evidence-source references in user-facing language;
- next-step explanation;
- monitoring or follow-up context when grounded and available.

Do not use the right panel for dense raw tables.

### Cards and Drill-Down

Cards are the primary content unit. Each card should have:

- title;
- status or direction;
- one-sentence interpretation;
- 1-3 key values if needed;
- evidence source;
- drill-down link for technical details.

Technical detail belongs in:

- accordion;
- drawer;
- modal with explicit source artifact;
- secondary table below a summary card.

---

## 7. Core Screens

### 7.1 Portfolio Input

**User question:**  
What portfolio am I diagnosing, and is the input good enough to continue?

**Top-level content:**

- Holdings and weights.
- Investor currency.
- Data availability status.
- Input completeness and validation.
- Clear distinction between current portfolio and model portfolio if applicable.

**Primary CTA:**  
Run diagnosis

**Secondary CTA:**  
Review input assumptions

**Hide in drill-down:**

- raw config mapping;
- ticker taxonomy detail;
- data source diagnostics;
- FX assumptions;
- cache metadata.

**Decision boundary:**  
Starting weights are the subject of diagnosis, not a recommendation.

**Risk of misunderstanding:**  
Users may think the system already validated investment suitability. It has not.

### 7.2 Decision Summary

**User question:**  
What is the current decision state in plain language?

**Top-level content:**

- diagnosis headline;
- evidence quality;
- candidate state if available;
- verdict state if available;
- next best product step.

**Primary CTA:**  
View diagnosis

**Secondary CTA:**  
Open evidence center

**Hide in drill-down:**

- metric tables;
- stress scenario internals;
- candidate factory metadata;
- scoring details.

**Decision boundary:**  
This is a summary of the decision-support journey, not an action instruction.

**Risk of misunderstanding:**  
Users may read a compact status as a recommendation. Use boundary notes directly on the card.

### 7.3 Evidence Center: X-Ray + Stress

**User question:**  
What evidence explains the portfolio problem?

**Top-level content:**

- X-Ray findings.
- Stress Test Lab findings.
- problem classification.
- evidence quality and limitations.
- top issues ranked by decision relevance.

**Primary CTA:**  
Create hypothesis

**Secondary CTA:**  
Inspect technical evidence

**Hide in drill-down:**

- raw stress tables;
- factor matrices;
- estimator notes;
- taxonomy warnings;
- detailed scenario trace.

**Decision boundary:**  
Stress loss is not the same as normal risk contribution. Pre-stress weakness is not confirmed stress failure.

**Risk of misunderstanding:**  
Users may confuse a stress scenario result with a forecast. Label it as diagnostic evidence.

### 7.4 Hypothesis Launchpad + Builder

**User question:**  
Which candidate hypothesis should we test against the diagnosis?

**Top-level content:**

- hypothesis cards from the launchpad;
- why each hypothesis exists;
- expected trade-off;
- builder constraints and selected method;
- candidate generation state.

**Primary CTA:**  
Test candidate

**Secondary CTA:**  
Compare hypothesis assumptions

**Hide in drill-down:**

- builder method internals;
- optimizer parameters;
- candidate factory logs;
- feasibility diagnostics.

**Decision boundary:**  
The candidate is a hypothesis test, not a recommended portfolio.

**Risk of misunderstanding:**  
Users may treat the first candidate as the system’s preferred choice. Use explicit “candidate” and “hypothesis test” language.

### 7.5 Current vs Candidate Comparison

**User question:**  
What improved, what worsened, and what trade-off did the candidate create?

**Top-level content:**

- current portfolio versus candidate;
- What Improved card;
- What Worsened card;
- unchanged or inconclusive areas;
- evidence quality;
- comparison table with only decision-relevant metrics.

**Primary CTA:**  
Review verdict

**Secondary CTA:**  
Inspect comparison details

**Hide in drill-down:**

- full metric universe;
- all candidate registry rows;
- optimizer scoring artifacts;
- raw JSON tables.

**Decision boundary:**  
Reference benchmark does not imply rebalance recommendation.

**Risk of misunderstanding:**  
Users may equate more green metrics with “best portfolio.” Force trade-off framing.

### 7.6 Decision Verdict + AI Commentary

**User question:**  
Is the evidence strong enough to support a decision?

**Top-level content:**

- verdict state;
- decision-support explanation;
- no-trade / proceed / evidence-insufficient framing;
- key evidence;
- key trade-off;
- monitoring or follow-up context when grounded and available.

**Primary CTA:**  
Create report preview

**Secondary CTA:**  
Return to evidence

**Hide in drill-down:**

- full commentary context;
- source artifact payloads;
- technical confidence notes;
- decision package internals.

**Decision boundary:**  
Verdict is decision-support, not a trading instruction. AI Commentary explains; it does not decide.

**Risk of misunderstanding:**  
Users may see AI language as authority. Keep commentary grounded and label it as explanation.

### 7.7 Report / Client-ready Explanation

**User question:**  
Can this result be explained clearly to a client or stakeholder?

**Top-level content:**

- short narrative summary;
- diagnosis;
- evidence;
- candidate hypothesis;
- comparison;
- verdict boundary;
- monitoring or follow-up context when grounded and available.

**Primary CTA:**  
Export or copy explanation

**Secondary CTA:**  
Edit client wording

**Hide in drill-down:**

- raw technical appendix;
- generated support artifacts;
- full logs;
- backend-only evidence.

**Decision boundary:**  
The report explains decision-support evidence. It is not advice, suitability review, or trading instruction.

**Risk of misunderstanding:**  
Client-ready clarity can make the output feel more definitive than it is. Keep evidence quality visible.

---

## 8. Component Guidelines

### Decision Status Card

Purpose: show the current decision state.

Content:

- status label;
- one-line interpretation;
- evidence quality;
- next step;
- boundary note.

States:

- Diagnosis ready;
- Candidate in test;
- Comparison ready;
- Verdict ready;
- No-trade supported;
- Evidence insufficient.

### Diagnosis Hero Card

Purpose: make the diagnosis visible before metrics.

Rules:

- Use one clear diagnosis sentence.
- Show top 2-3 drivers only.
- Link to Evidence Center.
- Avoid score-first framing.

### Evidence Card

Purpose: summarize one evidence item.

Content:

- evidence type: X-Ray, Stress, Classification, Data Quality;
- status;
- interpretation;
- source artifact;
- drill-down.

### Risk Badge

Purpose: compact risk or caution marker.

Rules:

- Red only for worsening/risk.
- Amber for caution or insufficient evidence.
- Never use badge color decoratively.

### Improvement / Worsening Badge

Purpose: show directional comparison.

Rules:

- Improvement uses emerald.
- Worsening uses soft red.
- Neutral / unclear uses muted slate or amber.
- Each badge needs a metric or evidence anchor.

### Hypothesis Card

Purpose: present a candidate test idea.

Content:

- hypothesis title;
- target problem;
- expected trade-off;
- method id if relevant;
- evidence source;
- CTA: Generate test candidate when setup is ready.

Required language:

- “hypothesis test”;
- “candidate”;
- “not a recommendation.”

### Builder Panel

Purpose: show how the selected test path becomes one diagnostic candidate attempt.

Rules:

- Show constraints at a human level.
- Keep technical builder details expandable.
- Show setup and candidate generation status separately.
- Do not make the builder feel like an optimizer cockpit.

### Comparison Table

Purpose: compare current and candidate.

Rules:

- Limit visible rows to decision-relevant metrics.
- Use direction labels, not only numbers.
- Add “trade-off” column where useful.
- Use tabular numbers.
- Put full metric detail in drill-down.

### What Improved / What Worsened Cards

Purpose: force balanced decision framing.

Rules:

- Always pair improvement with worsening or trade-off when available.
- If nothing material worsened, say so carefully and cite evidence quality.
- If evidence is incomplete, show amber caution.

### Verdict Card

Purpose: present final decision-support state.

Possible verdict language:

- Evidence supports further review;
- Evidence supports no-trade;
- Evidence insufficient;
- Candidate improves selected risks but introduces trade-offs;
- Candidate does not materially improve the diagnosis.

Rules:

- Never say “recommended portfolio.”
- Include “not a trading instruction.”
- Include evidence quality and monitoring trigger.

### Grounded Explanation Card

Purpose: explain, not decide.

Rules:

- Ground commentary in available evidence.
- Use short paragraphs.
- State limitations.
- Do not add new investment claims not present in evidence.
- Do not imply an LLM or AI system made the verdict.

### Light Decision Journal

Purpose: record the decision-support state without becoming a full decision journal product.

Content:

- date/time;
- subject portfolio;
- hypothesis tested;
- verdict state;
- evidence quality;
- monitoring trigger;
- short note.

### Client-ready Report Preview

Purpose: show a concise explanation suitable for review.

Rules:

- Use plain financial language.
- Keep diagnosis first.
- Show candidate as a test.
- Include boundary note.
- Keep appendix optional.

### Boundary / Compliance Note

Purpose: prevent over-interpretation.

Standard note:

> Portfolio MRI provides decision-support evidence. It does not provide a trading instruction, suitability determination, or guarantee of future outcomes.

Use on Verdict, Report Preview, and any screen where action could be inferred.

---

## 9. Copywriting Rules

### Must Use

Use these terms consistently:

- “hypothesis test”
- “candidate”
- “decision-support”
- “trade-off”
- “evidence quality”
- “monitoring trigger”
- “not a trading instruction”

### Must Not Use

Avoid these terms in product UI:

- “best portfolio”
- “optimal portfolio”
- “recommended portfolio”
- “guaranteed”
- “buy/sell”
- “sure outcome”
- “perfect allocation”

### Voice

- Calm, concise, and analytical.
- Serious B2B product tone.
- Explain what changed, why it matters, and what remains uncertain.
- Prefer “evidence suggests” over “the system knows.”
- Prefer “candidate improved X but worsened Y” over “candidate wins.”
- Prefer “no-trade remains valid” over “do nothing.”

---

## 10. UX Boundaries

These boundaries must be visible in UI behavior and copy:

- Candidate ≠ recommendation.
- Verdict ≠ trading instruction.
- Reference benchmark ≠ rebalance recommendation.
- No-trade is a valid decision.
- Evidence insufficient is a valid result.
- Stress loss ≠ normal risk contribution.
- Pre-stress weakness ≠ confirmed stress failure.
- AI Commentary explains; it does not decide.

### Practical UI Enforcement

- Any candidate screen must label the candidate as a hypothesis test.
- Any verdict screen must include a decision-support boundary note.
- Any report preview must mention evidence quality.
- Any comparison must show trade-offs, not only improvements.
- Any AI explanation must cite source artifacts or state that evidence is insufficient.

---

## 11. Data-to-UI Mapping

| Backend artifact | UI screen / component | UI interpretation |
| --- | --- | --- |
| `problem_classification.json` | Diagnosis Summary, Diagnosis Hero Card | Primary diagnosis, problem type, evidence state. |
| `candidate_launchpad.json` | Hypothesis Launchpad | Available hypothesis tests and why they exist. |
| `portfolio_alternatives_builder.json` | Hypothesis Builder, Builder Panel | Builder setup state and selected candidate method context. |
| `candidate_generation.json` | Candidate state | Candidate attempt status, generation readiness, failure or success state. |
| `current_vs_candidate.json` | Current vs Candidate Comparison | What improved, what worsened, trade-offs, comparison table. |
| `decision_verdict.json` | Verdict Card, Decision Status Card | Decision-support result, no-trade / proceed / insufficient evidence state. |
| `ai_commentary_context.json` | Grounded Explanation Card, Report Preview | Grounded explanation and report narrative context. |

### Mapping Rules

- UI must read `analysis_subject/` artifacts before candidate or verdict interpretation.
- Do not treat root legacy policy artifacts as the subject portfolio in portfolio-first UI.
- Generated support artifacts may inform technical drill-down, but they are not the primary Core MVP UI unless explicitly promoted by specs.

---

## 12. Do Not Build Yet

Keep these out of Core MVP UI:

- macro dashboard;
- full PDF designer;
- multi-client workspace;
- full optimizer zoo;
- advanced settings;
- tax-aware screens;
- Monte Carlo;
- asset diagnostics;
- full client suitability questionnaire;
- portfolio health score;
- robustness scorecard;
- what-if simulator.

If any of these exist in code or generated outputs, classify them as `Advanced`, `Backend evidence`, `Technical artifact`, `Legacy`, `Generated support artifact`, or `Future/backlog`, not as the current Core MVP UI.

---

## 13. Final Design Checklist

Before accepting any Portfolio MRI UI work, check:

- [ ] Does the UI answer what the user should do next?
- [ ] Is the diagnosis visible before metrics?
- [ ] Is the candidate clearly marked as a test?
- [ ] Is the verdict clearly decision-support?
- [ ] Are technical details in drill-down?
- [ ] Is no-trade treated as a real outcome?
- [ ] Is evidence insufficient explained honestly?
- [ ] Does the UI avoid false precision?
- [ ] Can a user understand the result in 5 minutes?
- [ ] Does the UI avoid looking like a crypto exchange, retail trading app, Excel UI, optimizer cockpit, or noisy chart terminal?

---

## Implementation Notes for UI Work

When building UI from this design system:

1. Start from the journey stage, not from available charts.
2. Build summary cards before detailed tables.
3. Use dark institutional surfaces and restrained semantic color.
4. Keep evidence-source references available in drill-down without exposing raw filenames as primary copy.
5. Use explicit boundary copy wherever an action could be inferred.
6. Prefer one primary CTA per screen.
7. Treat AI Commentary as grounded explanation only.
