# Design System Contract

Status: **canonical design-system contract** for Portfolio MRI / Portfolio X-Ray Core MVP product screens, frontend visual QA, status badges, card hierarchy, CTA placement, and client-ready dark institutional presentation.

Scope: enforceable visual rules for current MVP UI work. This contract translates `docs/design/portfolio_mri_design_system.md` into implementation-review rules. It does not change CSS, components, runtime behavior, backend artifacts, formulas, schemas, generated outputs, or copy contracts by itself.

This contract exists to prevent product-code-design drift. A future UI, component, route, badge, card, CTA, state, or visual QA change that changes Portfolio MRI's product look and hierarchy must update this file and the owning design/source documents in the same change.

## Source-of-truth order

Use this document for enforceable Core MVP visual rules. Use these documents for adjacent authority:

- `docs/design/portfolio_mri_design_system.md` for the canonical design direction and design rationale.
- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for product step order and product boundaries.
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` for artifact routing, stale-data rules, and same-run lineage.
- `docs/contracts/SCREEN_CONTRACTS.md` for route responsibilities, must-show sections, CTAs, empty states, and screen-specific forbidden terms.
- `docs/contracts/PRESENTATION_LANGUAGE_RULES.md` for user-facing wording, forbidden backend terms, and approved replacements.
- `DESIGN.md` only as historical/legacy visual reference. Portfolio MRI UI work must follow `docs/design/portfolio_mri_design_system.md` and this contract instead of the legacy Revolut-inspired direction.
- `docs/contracts/QA_CONTRACT.md` and `docs/contracts/DOC_SYNC_CONTRACT.md` for verification and documentation-impact enforcement.

## Design promise

Portfolio MRI must feel like a premium institutional investment decision room: calm, precise, trustworthy, analytical, and client-ready. It is not a trading terminal, crypto exchange, optimizer cockpit, colorful dashboard, Excel clone, or playful fintech app.

The interface must guide the user through diagnosis, evidence, hypothesis testing, comparison, verdict, and grounded explanation. Visual hierarchy must make the next safe product step obvious without implying a trading instruction.

## Dark institutional visual policy

The default visual environment is **near-black graphite / dark institutional navy**. Screens should use dark surfaces, slate borders, restrained contrast, and semantic color only where it changes product meaning.

Rules:

1. Use near-black or very dark graphite/navy for the app shell and page background.
2. Use slightly lifted dark surfaces for cards and panels; depth comes from surface contrast, thin borders, spacing, and hierarchy, not heavy shadows.
3. Keep the page calm: most pixels should be dark neutral, slate, and readable white/gray text.
4. Use bright color sparingly. A colorful screen means too many statuses are competing.
5. Do not use neon, rainbow gradients, glowing crypto accents, confetti, animated trading effects, or high-frequency chart colors.
6. Do not copy reference-brand assets, exact layouts, typography signatures, logos, gradients, or marketing language.

Recommended visual roles remain aligned to the design source:

| Role | Preferred family | Use |
| --- | --- | --- |
| App background | Near-black graphite / dark navy | Shell, route background, decision-room atmosphere. |
| Secondary surface | Dark slate/navy | Sidebar, section bands, secondary panels. |
| Card surface | Lifted dark slate | Evidence cards, hypothesis cards, comparison modules, verdict cards. |
| Text | White / cool slate | Headings, body, captions, metadata. |
| Border | Slate | Card outlines, dividers, table rules, disabled state outlines. |

## Color semantics

Color is a semantic system, not decoration. Every colored badge, border, chart mark, icon, or CTA must answer: what state does this color communicate?

| Color family | Meaning | Allowed uses | Limits |
| --- | --- | --- | --- |
| Blue | Primary action, focus, active journey step, selected navigation, inline link. | Primary CTA, current step, keyboard focus ring, selected tab/card outline, safe informational link. | Blue must not mean success, risk, recommendation, or generic decoration. |
| Amber | Caution, boundary, partial evidence, evidence insufficient, degraded confidence, blocked-by-limitation state. | Warning badges, evidence-quality caveats, boundary notes, partial/unavailable states, blocked setup explanation. | Amber must not be used as a cheerful accent or to hide an actual error. |
| Green | Generated, ready, complete, success, improved, risk reduced. | Completed journey evidence, ready-to-continue state, generated candidate/comparison/verdict/report, confirmed improvement/risk reduction. | Green must not imply recommendation, approval, suitability, trade execution, or guaranteed improvement. |
| Red | Actual error, destructive action, failed run, material risk, worsening, stress failure, negative trade-off. | Runtime failure, destructive confirmation, material worsening, actual risk/error state. | Red is forbidden for general emphasis, neutral caution, no-trade, or evidence-insufficient states. |
| Slate | Neutral, unavailable, inactive, not started, unchanged, metadata. | Inactive steps, neutral badges, table dividers, not evaluated metrics, muted captions. | Slate must not hide a required warning or blocker. |
| Gold / premium accent | Formal institutional boundary only when distinct from amber caution. | Rare divider, formal report-ready accent, selected institutional module edge. | Do not use gold as confetti, chart fill, generic brand flair, or status substitute. |

No neon rule: avoid electric cyan, magenta, lime, hot pink, saturated purple glows, rainbow gradients, or crypto-style highlight systems in Core MVP UI.

## Badge taxonomy and limits

Badges are compact state labels. They must be readable, sparse, and backed by evidence. A badge without an evidence anchor is decorative and should be removed.

### Approved badge families

| Family | Color | Examples | Meaning |
| --- | --- | --- | --- |
| Journey | Blue / green / amber / slate | Current step; Complete; Ready; Blocked; Deferred | Whether the user can proceed. |
| Evidence quality | Green / amber / slate | Strong evidence; Partial evidence; Limited evidence; Unavailable; Evidence insufficient | How much trust the screen can place in current evidence. |
| Candidate state | Green / amber / slate / red | Setup only; Ready to test; Candidate generated; Candidate failed; Candidate infeasible | State of the selected hypothesis and one candidate attempt. |
| Comparison direction | Green / red / slate / amber | Improved; Worsened; Similar; Not evaluated; Unavailable | Directional current-vs-candidate evidence. |
| Verdict | Green / amber / slate / red only for failure/risk | Keep current; No material rebalance; Rebalance review; Test another; Evidence insufficient; Candidate failed | Non-binding decision-support outcome. |
| Report / AI grounding | Green / amber / slate | Grounded preview; Partial evidence; Preview only; Export deferred | State of the explanation surface. |
| Monitoring | Amber / slate / green | Deferred; First review; No material change; Retest suggested; Changed | What Changed state when surfaced. |

### Badge limits

1. Use no more than one primary status badge per card header.
2. Use at most three badges in a single card unless the card is a dense technical drill-down.
3. Do not stack multiple colors next to each other unless the purpose is explicitly to compare improved and worsened evidence.
4. Do not use badge-only communication. Each badge needs a one-sentence interpretation or nearby label.
5. Do not show raw backend enum ids, artifact names, booleans, or placeholders inside badges.
6. No-trade, evidence insufficient, unavailable, partial, sample, and deferred states are not visual failures.

## Card hierarchy and density

Cards are the primary content unit. They must support decision reading, not become metric walls.

### Card hierarchy

| Level | Purpose | Visual treatment | Content limit |
| --- | --- | --- | --- |
| Hero / decision card | Answer the screen's main question. | Largest card, strongest title, one primary status, optional 1-3 key values. | One clear interpretation, next step, boundary note when action can be inferred. |
| Primary evidence card | Explain one major diagnosis, stress, hypothesis, comparison, or verdict point. | Standard lifted surface, subtle border, one status badge. | Title, one-sentence meaning, 1-3 values, evidence note, drill-down link if needed. |
| Secondary/support card | Provide context, assumptions, limitations, or source summary. | Lower contrast surface, lighter heading. | Short explanatory copy or compact list. |
| Technical drill-down | Show implementation detail only after the summary is understood. | Accordion/drawer/modal/secondary table. | Rawer detail allowed only outside primary UI and with clear source context. |

### Density and whitespace rules

1. One screen should answer one main user question.
2. Prefer summary cards before tables.
3. Use generous whitespace around hero and primary cards; do not fill every dark surface with metrics.
4. Use compact density only inside tables or technical drill-down.
5. Visible cards should usually show 1-3 decision-relevant values, not the full metric universe.
6. Keep technical detail, estimator notes, raw tables, logs, and artifact references in drill-down.
7. Avoid false precision: do not visually over-emphasize decimals that do not change the decision.
8. Pair "What improved" with "What worsened" or "Trade-off" when comparison evidence exists.

## Typography hierarchy

Typography should feel modern, neutral, and institutional. Recommended families remain Inter, Geist, SF Pro, or a similar neutral sans-serif. Numeric data should use tabular figures where available.

| Role | Relative hierarchy | Use |
| --- | --- | --- |
| Page title | Largest, 600 weight | Screen title and decision-room context. |
| Section title | Strong, 600 weight | Major stage section: Diagnosis, Stress Test Lab, Hypothesis, Comparison, Verdict. |
| Card title | Medium, 600 weight | Evidence cards, hypothesis cards, verdict modules. |
| UI label | Small, 500-600 weight | Badges, navigation, step labels, field labels. |
| Body | Readable, regular weight | Short explanatory copy. |
| Metadata | Small, muted | Sources, timestamps, confidence notes, assumptions. |
| Numeric emphasis | Large enough to scan, 600 weight | Only for decision-relevant top values. |

Rules:

1. Use sentence case for most labels.
2. Use small uppercase only for compact status labels; it must not dominate the voice.
3. Avoid playful display fonts, heavy all-caps marketing typography, and retail-app oversized hero slogans.
4. Do not make raw numbers louder than the diagnosis or verdict.
5. Use concise text blocks; long paragraphs belong in report preview or drill-down.

## CTA placement and states

Each screen should have one dominant next action. Secondary actions must not compete with the primary journey CTA.

### Placement rules

1. Place the primary CTA near the main decision card or at the end of the screen's main reading path.
2. Right-side panels may explain the next step, but should not host competing primary actions unless the layout clearly makes them the stage action.
3. Secondary CTAs should be visually quieter and used for review, drill-down, retry, or back navigation.
4. Destructive actions, if any, must be isolated and red only when they are truly destructive.
5. Do not place CTAs that imply trading execution, suitability approval, or tax advice.

### CTA state taxonomy

| State | Visual treatment | Meaning |
| --- | --- | --- |
| Primary | Blue filled or strongest blue treatment | The safe next product step is available. |
| Secondary | Slate/ghost/outline treatment | Optional review, drill-down, back, copy, or inspect action. |
| Disabled | Muted slate; no active hover; accessible explanation nearby | Temporarily cannot be used because required input is missing. |
| Unavailable | Muted slate or amber context; not just a disabled button | Not offered for this review, mode, or evidence state. Explain why. |
| Blocked | Amber warning context with clear blocker | The step needs cleaner data, a valid setup, or current evidence. |
| Running | Blue/slate with progress affordance | The system is working; do not expose raw backend states. |
| Error retry | Red only for actual failed run or destructive/error condition | Retry after failure; explain user-safe next step. |

Disabled and unavailable are different. Disabled usually means "complete the prerequisite"; unavailable means "this path is not part of this review or current MVP state."

## State visual rules

### Warning and boundary states

Use amber for:

- partial evidence;
- evidence insufficient;
- degraded confidence;
- blocked setup;
- unavailable comparison metrics;
- sample/demo boundary where confusion is likely;
- decision-support guardrails where action could be inferred.

Boundary notes should be visually present but not alarming. They should not use red unless there is an actual error, destructive action, or material risk.

### Generated and ready states

Use green for:

- diagnosis complete;
- setup ready to test;
- candidate generated;
- comparison complete;
- verdict available;
- report preview generated;
- confirmed improvement or risk reduction.

Green means "state exists / ready / improved." It must not mean "recommended", "approved", "trade", "best", or "guaranteed."

### Unavailable, blocked, partial, and evidence-insufficient states

These are valid product states and must be visually distinct:

| State | Color | Visual rule |
| --- | --- | --- |
| Unavailable | Slate or amber when consequential | Show what is unavailable and why, without raw `n/a` filler. |
| Blocked | Amber | Name the blocker and next safe step. |
| Partial | Amber | Show available sections and mark missing evidence honestly. |
| Evidence insufficient | Amber | Treat as a professional outcome, not a broken app. |
| Stale / ignored | Slate + amber note when user impact exists | Explain previous result was ignored because it is outdated. |
| Failed / error | Red | Use only when a run failed, candidate failed/infeasible, validation failed, or destructive/error state occurred. |

### Sample and demo states

Sample mode must be obvious near the top of the screen or in persistent context.

Rules:

1. Use labels such as `Sample review`, `Demo data`, `Example portfolio`, or `Sample evidence`.
2. Do not show fake review IDs, raw run folders, or `frontend_review_sample` as primary labels.
3. Sample/demo state can use slate with amber boundary text when confusion with a live review is possible.
4. A sample screen must not visually claim a live generated candidate, live verdict, or current client evidence.

## Current MVP route visual rules

### Portfolio Input (`/portfolio-input`)

- Visual job: a precise intake desk, not an optimizer setup.
- Hero card: current portfolio input, weight validation, reporting currency, assumptions note.
- Primary CTA: `Run diagnosis` in blue only when input is valid.
- State colors: green for valid/ready, amber for incomplete or weight issues, red only for true validation error or failed run.
- Must not show: optimizer cockpit layout, advanced constraints as primary panels, trading language, raw config/runtime IDs.

### Portfolio X-Ray / Diagnosis (`/diagnosis`)

- Visual job: show diagnosis before action.
- Hero card: one diagnosis sentence and top drivers.
- Use cards for allocation, concentration, risk behavior, factor exposure, hidden exposure, weakness map, and data limitations.
- Problem Classification should appear as a bridge into the next step, not as a backend table.
- Must not show: candidate CTAs before evidence context, score-first dashboard, Portfolio Health Score as hero, raw block IDs.

### Stress Test Lab (`/evidence`)

- Visual job: a controlled evidence lab, not a generic evidence dump.
- Hero card: worst meaningful stress finding, evidence quality, and what it means.
- Use paired cards for helped/hurt contributors, hedge gaps, scenario availability, and limitations.
- Use amber for unsupported/partial historical evidence, red only for actual stress risk/failure/worsening.
- Must not show: mandate pass/fail UI, raw scenario IDs as primary labels, dense scenario matrix as first view.

### Hypothesis Builder (`/hypothesis`)

- Visual job: choose and prepare one test path.
- Hypothesis cards should show target problem, expected trade-off, evidence source, and boundary note.
- Selected setup panel should visually differ from generated candidate state.
- Primary CTA progression: select test path -> prepare setup -> generate test candidate.
- Use green only when setup is ready or candidate was generated; candidate generated does not mean recommended.
- Must not show: optimizer zoo, disabled method catalog, advanced settings wall, weights before generation.

### Current vs Candidate Comparison (`/comparison`)

- Visual job: force balanced trade-off reading.
- Hero card: comparison readiness and materiality for review.
- Pair `What improved` and `What worsened / trade-off` cards when data exists.
- Use green for improved metrics and red for actual worsened/risk metrics; slate for similar; amber for unavailable/not evaluated.
- Tables should show decision-relevant rows first and use tabular numbers.
- Must not show: winner cards, final verdict language, batch rankings, fake `n/a` conclusions.

### Decision Verdict (`/verdict`)

- Visual job: non-binding decision support.
- Hero card: verdict family, rationale, evidence quality, boundary note.
- No-trade and no material rebalance must look like valid professional outcomes, not failures.
- Evidence insufficient should be amber, not red, unless caused by an actual failed run.
- Rebalance review may use blue/amber/green depending on state, but must not imply trade execution.
- Must not show: best portfolio, trade now, buy/sell, suitability approval, tax advice, full action-plan product.

### Report / AI Commentary Grounding (`/report`)

- Visual job: grounded client-readable explanation preview.
- Hero card: grounded preview state and evidence coverage.
- Use sections for diagnosis, stress evidence, hypothesis tested, trade-offs, verdict explanation, limitations, and optional What Changed note.
- Report preview should look polished but bounded; client-ready clarity must not erase evidence limits.
- Must not show: raw source artifact package, AI-as-decision-maker styling, PDF absence as product failure, completed Decision Journal product.

### Deferred Monitoring / What Changed

- Visual job when later surfaced: calm follow-up, not alerting/trading.
- Current MVP has no route. Do not add visual navigation unless product-flow, artifact, screen, design, QA, and doc-sync contracts are updated.
- If shown as a report note, use compact slate/amber/green state: first review, no comparable prior review, changed, no material change, retest suggested.
- Must not show: broker alerts, push notification style, scheduler product, automatic rebalance trigger, trade instruction.

## Forbidden visual directions

Do not build or approve Core MVP UI that looks like:

- crypto exchange;
- retail trading app;
- playful fintech;
- generic BI dashboard;
- Excel spreadsheet UI;
- optimizer cockpit;
- noisy chart terminal;
- multicolor status wall;
- gamified scoring product;
- robo-advisor recommendation funnel;
- broker order ticket;
- full PDF designer;
- advanced macro dashboard;
- full multi-candidate arena.

Visual anti-patterns:

1. Too many charts before the diagnosis.
2. Red/green everywhere without evidence meaning.
3. Green candidate/result cards that imply recommendation.
4. Red no-trade or evidence-insufficient states.
5. Dense tables as the first view.
6. Raw filenames, JSON keys, run IDs, or backend labels in visible cards.
7. Neon gradients, glowing borders, glassmorphism-heavy panels, animated market-ticker aesthetics.
8. Overweight shadows, low-contrast text, or decorative premium gold.
9. Multiple competing primary CTAs on one screen.
10. Advanced tools in the Core MVP navigation.

## QA and visual review checklist

Use this checklist before accepting future UI or visual changes. For docs-only Session 5, compare this contract against `docs/design/portfolio_mri_design_system.md` and run `git diff --check`.

- [ ] The screen follows the current MVP route role in `docs/contracts/SCREEN_CONTRACTS.md`.
- [ ] The visual hierarchy starts from the product question, not from available charts or backend files.
- [ ] Diagnosis appears before candidate/action framing.
- [ ] The dominant environment is dark institutional graphite/navy with restrained slate surfaces.
- [ ] Blue is used for primary/focus/journey only.
- [ ] Amber is used for caution, boundary, partial, blocked, or evidence-insufficient states.
- [ ] Green is used only for generated/ready/complete/success/improvement/risk-reduction states and does not imply recommendation.
- [ ] Red is used only for actual error, destructive action, material risk, failure, or worsening.
- [ ] No neon, crypto, trading-terminal, optimizer-cockpit, Excel, or noisy dashboard styling is present.
- [ ] Badges are sparse, readable, and backed by evidence.
- [ ] Each major card has a title, status/direction, one-sentence interpretation, limited key values, evidence/source context, and drill-down if needed.
- [ ] Technical details are in drill-down rather than primary hero/cards.
- [ ] Typography is calm, hierarchical, and readable; numbers do not overpower the diagnosis/verdict.
- [ ] There is one dominant primary CTA per screen.
- [ ] Disabled, unavailable, blocked, partial, evidence-insufficient, stale, generated, ready, sample, and demo states are visually distinct.
- [ ] Candidate is visually framed as a hypothesis test, not a recommendation.
- [ ] Verdict is visually framed as non-binding decision support, not a trading instruction.
- [ ] Report / AI Commentary is framed as grounded explanation, not AI authority.
- [ ] Monitoring remains deferred unless the full contract set is updated.
- [ ] Presentation language follows `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`.
- [ ] Product flow follows `docs/contracts/PRODUCT_FLOW_CONTRACT.md`.
- [ ] Artifact state and lineage follow `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`.

## Documentation impact rule

Any meaningful change to design tokens, color semantics, badge families, card hierarchy, visual route behavior, CTA placement, warning/generated/unavailable/sample states, or forbidden visual directions must update this contract and `docs/design/portfolio_mri_design_system.md` together, unless the final response explicitly explains why no design-doc update was needed.

If a visual implementation change also changes product role, route behavior, UI copy, artifact interpretation, or QA requirements, update the related product-flow, screen, language, artifact-map, QA, and doc-sync contracts in the same session.

## Validation for this contract

Session 5 is documentation-only. Minimum checks after editing this file:

    git diff --check

Required design-source comparison:

    Get-Content docs\design\portfolio_mri_design_system.md

The comparison should confirm that this contract preserves the source design's dark institutional decision-room direction, restrained semantic color, typography hierarchy, cards-first layout, route-specific product roles, UX boundaries, and forbidden visual directions.
