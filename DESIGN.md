# Portfolio MRI Design System

## Status

This file is the single current source of truth for Portfolio MRI product UI, dashboard, generated HTML, and visual-interface work.

This document replaces the former cinematic glass / blue-accent design direction. Do not restore older graphite-glass, blue-gradient CTA, shadow-heavy, or floating-card design rules unless a future source-of-truth update explicitly changes this file.

Use this file together with:

- `docs/design/current_website_structure.md` for route-by-route visible structure and copy.
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` for enforceable UI review rules.
- `docs/contracts/INFORMATION_ARCHITECTURE_COPY_CONTRACT.md` for primary-surface copy discipline and defensive-copy limits.
- `docs/contracts/SCREEN_CONTRACTS.md` and `docs/specs/frontend_screen_contracts.md` for route responsibilities.

This document does not override `SPEC.md`, `RULES.md`, data rules, metric formulas, backend schemas, output contracts, or product-flow contracts.

## Product Design Thesis

Portfolio MRI is a diagnosis-first Investment Decision Room, not a dashboard wall, trading terminal, optimizer cockpit, or portfolio recommendation engine.

The interface must keep the user inside a calm evidence chain:

```text
Landing
-> Required email sign-in
-> Onboarding
-> Portfolio Input
-> Portfolio Diagnosis
-> Stress Test Lab
-> Client Fit
-> Hypothesis
-> Current vs Candidate Comparison
-> Decision Verdict
-> Report Preview
```

Candidates are diagnostic tests. Verdicts are non-binding decision support. The UI must never imply suitability approval, trade execution, automatic rebalancing, or guaranteed improvement. These boundaries should be enforced through route order, neutral actions, blocked states, and final evidence review rather than repeated primary-surface disclaimers.

## Visual Language

Portfolio MRI uses a restrained engineered dark-canvas language:

- near-black page canvas;
- white primary typography;
- flat charcoal cards;
- 1 px hairline borders;
- pill-shaped actions;
- monospace uppercase labels;
- weight-400 typography;
- rare sunset / twilight / breeze accents only for evidence emphasis.

The atmosphere should feel:

- engineered;
- restrained;
- precise;
- research-lab dark;
- diagnosis-first;
- analytical without becoming a trading terminal.

Avoid:

- light mode;
- broad filled CTA usage beyond the rare primary action;
- drop shadows as the main elevation cue;
- glossy glassmorphism;
- crypto/neon palettes;
- optimizer-first language;
- dense Excel-like tables as the primary surface;
- colorful dashboard walls.

## Tokens

The current frontend tokens live in `frontend/styles/globals.css` and `frontend/tailwind.config.ts`. Documentation must mirror those values when code changes.

| Role | Token / Tailwind role | Value | Use |
| --- | --- | --- | --- |
| App background | `pmri.bg`, `--pmri-bg-primary` | `#0A0A0A` | Main shell and page canvas. |
| Secondary background | `pmri.secondary`, `--pmri-bg-secondary` | `#0A0A0A` | Section bands and shell chrome. |
| Card surface | `pmri.surface`, `--pmri-surface-card` | `#191919` | Evidence cards and product panels. |
| Raised surface | `pmri.surface2`, `--pmri-surface-raised` | `#1A1C20` | Hovered or nested surfaces without shadow elevation. |
| Panel surface | `pmri.panel`, `--pmri-surface-panel` | `#191919` | Forms and dense panels. |
| Border | `pmri.border`, `--pmri-border` | `#212327` | Hairline dividers, cards, table rules. |
| Soft border | `pmri.borderSoft`, `--pmri-hairline` | `rgba(255,255,255,0.25)` | White-translucent pill and secondary outlines. |
| Primary text | `pmri.text`, `--pmri-text-primary` | `#FFFFFF` | Headings, values, key labels. |
| Secondary text | `pmri.text2`, `--pmri-text-secondary` | `#DADBDF` | Body copy and interpretation. |
| Muted text | `pmri.muted`, `--pmri-text-muted` | `#7D8187` | Captions, inactive steps, metadata. |
| Breeze Blue | `pmri.blue`, `pmri.steelBlue` | `#A0C3EC` | Rare illustrative or informational accent. |
| Twilight | `pmri.blueSoft`, `--pmri-premium-accent` | `#C4B5FD` | Rare illustrative accent and subtle emphasis. |
| White | `pmri.ivory`, `pmri.positive`, `--pmri-action-blue` | `#FFFFFF` | Primary foreground, outlines, focus, rare filled CTA. |
| Sunset Soft | `pmri.amber`, `pmri.amberGold`, `--pmri-warning` | `#FFC285` | Watch, caution, locked, partial, evidence required. |
| Sunset Orange | `pmri.risk`, `pmri.copperRed`, `--pmri-risk` | `#FF7A17` | Material issue, error, failure, destructive action, high-risk evidence. |
| Neutral accent | `pmri.gold` | `#DADBDF` | Formal neutral accent, not decorative gold. |

## Color Semantics

- White means foreground, active/current state, focus, and the rare filled primary action.
- Breeze Blue and Twilight are rare illustrative accents, not default action colors.
- Sunset Soft means watch, caution, evidence required, partial evidence, locked state, or degraded confidence.
- Sunset Orange means material issue, actual error, material worsening, failed run, destructive action, or high-risk evidence.
- Neutral gray means normal, aligned, completed, unavailable, unchanged, metadata, or secondary context.
- Green is not a Portfolio MRI product/system status semantic. Legacy API enum values may still be normalized by adapters, but Core MVP UI must not rely on green as the visible status color.

Use color sparsely. Most pixels should remain near-black, charcoal, white, and gray.

## Typography

The implemented frontend uses `DM Sans` as the geometric sans substitute and `IBM Plex Mono` as the tracked technical label face. Both are loaded at weight 400.

Rules:

- Use weight 400 as the default and dominant weight.
- Use negative tracking for large display headings.
- Use uppercase tracked mono labels for eyebrows, metadata labels, step numbers, and technical captions.
- Use tabular-number styling through `.data-figure` for key metrics.
- Avoid playful display fonts, heavy bold hierarchy, and all-caps body copy.
- Numeric values should be decision-relevant, not decorative precision.

Shared type classes:

- `.pmri-type-page-title` for page-level hero H1.
- `.pmri-type-section-title` for section H2.
- `.pmri-type-card-title` for card titles.
- `.pmri-type-body` for body copy.
- `.pmri-type-meta` and `.pmri-label` for compact mono labels.
- `.pmri-type-data` and `.data-figure` for tabular metrics.

## Shapes, Surfaces, and Elevation

- Buttons and action links use `9999px` pill shapes.
- Cards use restrained `8px` or existing route-level rounded corners when the layout requires larger containers.
- Elevation is expressed with hairline borders and surface contrast, not decorative shadow.
- Shadows should be `none` by default. Use focus rings only for accessibility.
- Panels should be flat dark fills: `#191919` or `#1A1C20`.
- Avoid glass blur, glossy gradients, and floating-depth effects.

## Components

### Buttons and CTAs

Primary CTA:

- `.pmri-primary-action`
- white filled pill;
- near-black text;
- rare use only for the next safe product action.

Secondary CTA:

- transparent dark pill;
- white-translucent border;
- white or secondary text;
- no blue gradient.

CTA copy must describe the next safe product step and must not imply trading, optimization execution, suitability approval, or guaranteed improvement.

### Cards and Panels

Cards are flat evidence containers:

- dark fill;
- 1 px hairline border;
- no decorative shadow;
- short diagnosis-oriented copy;
- no repeated generic evidence badges.

Metric cards show:

- mono label;
- optional status badge;
- tabular value;
- one short explanation.

Avoid all-at-once metric walls. Platform screens should not show more than three major surface blocks before the first scroll.

### Badges

Badges must communicate evidence-backed state. Do not use badges as decoration.

- One primary badge per card header is preferred.
- Reserve per-row badges for material issue, watch, unavailable, or workflow state.
- Use a small colored signal dot and a hairline surface.
- Avoid glow except for focus visibility.

### Forms and Inputs

Inputs use:

- dark `canvas-soft` / panel fill;
- white text;
- hairline border;
- 8 px radius;
- clear focus ring.

Inputs should look like evidence capture fields, not retail trading widgets.

## Layout Rules

### Public Landing

The landing page is public and does not show the platform sidebar or top journey rail.

It uses:

- sparse near-black hero;
- mono eyebrow;
- oversized weight-400 headline;
- pill CTAs;
- hairline section bands;
- flat section cards for workflow, system map, boundaries, and final CTA.

### Onboarding

Onboarding routes are public-frame screens without the platform sidebar. Canonical entry is `/onboarding/sign-in`; local testing may use `/onboarding/name?dev_bypass=1`.

Onboarding collects a friendly profile and creates non-binding Client Fit context before Portfolio Input.

### Platform Shell

Platform routes use:

- persistent compact `PlatformTopHeader`;
- route title as the top-header focus, without portfolio/currency/holdings metadata in the header;
- near-black journey rail on wide screens;
- current journey rail item as a light active pill with inactive steps muted;
- compact dark dock on smaller screens;
- gated journey navigation with 8 icon-led steps: Portfolio, Diagnosis, Stress Lab, Client Fit, Hypothesis, Comparison, Verdict, Report;
- platform content width around 1180-1240 px;
- narrow-screen portfolio-entry controls should render as stacked cards rather than requiring
  horizontal table scrolling;
- public and platform shells should expose a keyboard-visible skip link to the main content area;
- flat hairline case-file panels;
- sparse badges;
- explicit boundary notes;
- clear locked and empty states.

### Analytical Pages

Redesigned analytical pages use shared `VerdictHero`, `CaseFileTopCards`, `EvidenceSummary`, and `MetricMatrix` patterns.

- `VerdictHero` carries the page-level message with compact step context, one interpretation sentence, optional supporting facts, and restrained pill actions.
- `CaseFileTopCards` carries the first-read case-file answer: main finding, why it matters, key evidence, or the route-specific equivalent.
- `EvidenceSummary` is capped at four items in one flat hairline evidence strip.
- `MetricMatrix` groups rows with metric, portfolio value, reference/threshold, status, and meaning.
- Material/problem rows sort first inside fixed groups and stay secondary to the first-read diagnosis.
- Primary cards must not lead with generic operational states such as `Evidence available`, `Unavailable`, `Diagnostic only`, `No rebalancing`, or `Comparison pending`; those states belong in compact status notes, limitations, or collapsed details.

`/diagnosis` is the benchmark screen for the foundation:

```text
PlatformTopHeader
-> DiagnosisHero
-> EvidenceStrip
-> DiagnosticCanvas
-> AdvancedDiagnostics collapsed below
```

The first viewport must answer the main diagnosis, supporting evidence, next risk area, and next safe action before showing professional metrics, legacy technical `portfolio_xray.json` details, raw evidence-chain notes, or technical limitations.

### Hypothesis Builder Workstation

`/hypothesis` uses an Analyst Workstation layout rather than a stack of equal-weight evidence cards.

Screen hierarchy:

1. compact Hypothesis Builder header and journey stepper;
2. primary diagnosis recap;
3. one recommended diagnostic test with success criteria, trade-off, and decision boundary;
4. right-side action console for selected setup, candidate state, and primary CTA;
5. secondary panels for Client Fit context, other possible tests, and evidence/technical details.

Client Fit, alternative tests, supporting evidence, and developer/technical details must not compete visually with the primary diagnostic test or Generate/Continue action.

## Motion

Motion should make the decision room calmer and more legible, not flashier.

Use Framer Motion for:

- route fades;
- section reveals;
- active-rail movement;
- onboarding question changes;
- selected or hovered decision surfaces where motion clarifies hierarchy or state.

Prefer opacity and transform with restrained timing. Always respect reduced-motion preferences. Do not add decorative motion that competes with portfolio evidence, stress results, Client Fit boundaries, candidate trade-offs, or verdict language.

## Documentation Sync Rule

Any meaningful UI change must update:

- this file when visual style, tokens, layout, or components change;
- `docs/design/current_website_structure.md` when route structure, block order, visible copy, CTAs, or screen states change;
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` when enforceable design rules change;
- `docs/contracts/SCREEN_CONTRACTS.md` and `docs/specs/frontend_screen_contracts.md` when route responsibilities change;
- `frontend/README.md` and demo runbooks when operator flow changes.

## Foundation-First Workflow

Visible product UI changes follow this sequence:

```text
user journey
-> screen contracts
-> design tokens
-> primitive components
-> product components
-> sandbox/gallery
-> page templates
-> real screens
```

The reusable frontend foundation lives in `frontend/components/ui/`. Product-specific diagnosis composition lives in `frontend/components/diagnosis/` and keeps first-read diagnosis separate from advanced technical evidence.

Local design iteration should use `frontend/app/sandbox/components/page.tsx` at `/sandbox/components` before broad production route changes. Sandbox content is not a product route and must not change journey gating, backend behavior, review state logic, or API contracts.
