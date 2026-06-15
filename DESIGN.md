# Portfolio MRI Current Design System

## Status

This file is the top-level source of truth for Portfolio MRI product UI, dashboard, generated HTML, and visual-interface work.

It replaces all former external-reference and prototype design guidance. Use the implemented frontend and the documents linked here as current design authority. For current website structure and route-by-route content, use [docs/design/current_website_structure.md](docs/design/current_website_structure.md). For enforceable UI review rules, use [docs/contracts/DESIGN_SYSTEM_CONTRACT.md](docs/contracts/DESIGN_SYSTEM_CONTRACT.md).

This document does not override `SPEC.md`, `RULES.md`, data rules, metric formulas, backend schemas, output contracts, or product-flow contracts.

## Design Thesis

Portfolio MRI is an Investment Decision Room, not a dashboard wall, trading terminal, optimizer cockpit, or portfolio recommendation engine.

The UI must help the user move through a calm, evidence-first sequence:

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

The product must present candidates as diagnostic tests and verdicts as non-binding decision support. It must never imply suitability approval, trade execution, or guaranteed improvement.

## Current Visual Language

The implemented frontend uses a near-black graphite decision-room style with cool slate surfaces, restrained blue action accents, muted semantic statuses, large rounded cards, subtle glass rails, and controlled depth.

The atmosphere should feel:

- institutional;
- precise;
- calm;
- premium dark;
- client-ready;
- analytical without looking like a terminal.

Avoid:

- crypto/neon palettes;
- retail trading app energy;
- optimizer-first language;
- dense Excel-like tables as the primary surface;
- colorful dashboard walls;
- old flat-only external-reference rules.

## Current Color Tokens

The current frontend tokens live in `frontend/styles/globals.css` and `frontend/tailwind.config.ts`. Documentation should mirror these values unless the code is intentionally changed in the same commit.

| Role | Token / Tailwind role | Hex | Current use |
| --- | --- | --- | --- |
| App background | `pmri.bg`, `--pmri-bg-primary` | `#090A0C` | Main shell and landing background. |
| Secondary surface | `pmri.secondary`, `--pmri-bg-secondary` | `#101114` | Sidebar, onboarding panels, secondary sections. |
| Card surface | `pmri.surface`, `--pmri-surface-card` | `#17181B` | Evidence cards and standard decision cards. |
| Raised surface | `pmri.surface2`, `--pmri-surface-raised` | `#1D1F23` | Lifted cards and nested panels. |
| Panel surface | `pmri.panel` | `#202329` | Dense form/table panels. |
| Border | `pmri.border`, `--pmri-border` | `#2A2D33` / `#25282E` | Dividers, cards, table rules. |
| Soft border | `pmri.borderSoft` | `#3A3E46` | Secondary outlines and separators. |
| Primary text | `pmri.text`, `--pmri-text-primary` | `#ECEFF3` | Headings, values, key labels. |
| Secondary text | `pmri.text2`, `--pmri-text-secondary` | `#C4C9D1` | Body copy and interpretation. |
| Muted text | `pmri.muted`, `--pmri-text-muted` | `#949BA6` | Captions, inactive steps, metadata. |
| Action blue | `pmri.blue`, `--pmri-action-blue` | `#3B82F6` | Primary CTA, active journey, focus. |
| Soft blue | `pmri.blueSoft` | `#60A5FA` | Links, hover, section accents. |
| Positive | `pmri.positive`, `--pmri-positive` | `#6FBF9B` | Ready, completed, improved, generated. |
| Amber | `pmri.amber`, `--pmri-warning` | `#C9A66B` | Caution, locked, partial, evidence required. |
| Risk | `pmri.risk`, `--pmri-risk` | `#D77A7A` | Error, worsening, material risk. |
| Premium accent | `pmri.gold`, `--pmri-premium-accent` | `#AAB7C6` | Formal slate accent, not decorative gold. |

## Color Semantics

- Blue means action, active journey state, selected navigation, focus, or safe informational emphasis.
- Green means ready, completed, generated, improved, or risk reduced. It must not imply suitability approval or a trade recommendation.
- Amber means caution, evidence required, partial evidence, locked state, or degraded confidence.
- Red means actual error, material worsening, failed run, destructive action, or high-risk evidence.
- Slate/gray means neutral, inactive, unavailable, metadata, or structural boundary.

Use color sparsely. Most pixels should remain graphite, slate, and readable white/gray text.

## Typography

Current implementation uses a modern sans stack through `--font-pmri-sans`, with Inter/Manrope/Helvetica Neue fallbacks. Numeric values use tabular-number styling through `.data-figure`.

Rules:

- Large page titles use restrained negative tracking and medium weight.
- Section titles are compact and clear.
- Body copy is short, concrete, and explanatory.
- Status labels are small and sparse.
- Numeric values should be decision-relevant, not decorative precision.
- Avoid playful display fonts and heavy all-caps as the dominant voice.

## Layout and Components

### Public landing

The landing page is public and does not show the platform sidebar or top journey rail. It uses a large centered hero, moving-grid atmosphere, dark sections, reveal animation, rounded CTA buttons, and structured blocks for problem, workflow, architecture, precision, and final CTA.

### Onboarding

Onboarding routes are public-frame screens without the platform sidebar. Canonical entry is `/onboarding/sign-in`; local testing may use `/onboarding/name?dev_bypass=1`. Onboarding collects a friendly profile and creates non-binding Client Fit context before Portfolio Input.

### Platform shell

Platform routes use:

- a left sidebar with 8 gated journey steps;
- a sticky top journey rail;
- a large page header card;
- dark cards and panels;
- sparse badges;
- explicit boundary notes;
- clear locked/empty states.

### Hypothesis Builder workstation

`/hypothesis` uses an Analyst Workstation layout rather than a stack of equal-weight evidence cards. The screen hierarchy is:

1. compact Hypothesis Builder header and journey stepper;
2. primary diagnosis recap;
3. one recommended diagnostic test with success criteria, trade-off, and decision boundary;
4. right-side action console for selected setup, candidate state, and the primary CTA;
5. secondary panels for Client Fit context, other possible tests, and evidence/technical details.

Client Fit, alternative tests, supporting evidence, and developer/technical details must not compete visually with the primary diagnostic test or the Generate/Continue action.

Current platform steps:

1. Portfolio
2. Diagnosis
3. Stress Lab
4. Client Fit
5. Hypothesis
6. Comparison
7. Verdict
8. Report

### Cards and metrics

Cards use rounded corners, thin borders, subtle gradients, and `shadow-decision`. Depth is allowed when it supports hierarchy. Metric cards show a label, optional status badge, a tabular value, and one short explanation. Avoid all-at-once metric walls.

Portfolio Diagnosis uses a diagnosis-first simplification pattern: one main finding, a maximum of three primary evidence facts, one compact `What matters first` strip, a three-item behavior snapshot, and advanced diagnostics hidden by default. Professional metrics such as VaR, ES, skewness, kurtosis, beta, Sharpe, Sortino, and Treynor remain available behind disclosure controls rather than dominating the first read.

### Badges

Badges must communicate evidence-backed state. Do not use badges as decoration. One primary badge per card header is preferred. Do not repeat generic evidence badges such as `Evidence available` across every Diagnosis fact; use one global data-coverage state and reserve per-row badges for material risk or review state.

### CTAs

Primary CTAs use the blue gradient `.pmri-primary-action`. Secondary CTAs use thin borders and dark transparent backgrounds. CTA copy must describe the next safe product step and must not imply trading or optimizer execution.

## Current Website Structure

The current route-by-route website structure, block order, visible headings, CTA behavior, and locked states are documented in [docs/design/current_website_structure.md](docs/design/current_website_structure.md). Keep that document synchronized whenever landing, onboarding, route order, page copy, CTA placement, visible metrics, or locked states change.

## Documentation Sync Rule

Any meaningful UI change must update:

- this file when visual style, tokens, layout, or components change;
- `docs/design/current_website_structure.md` when route structure, block order, visible copy, CTAs, or screen states change;
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` when enforceable design rules change;
- `docs/contracts/SCREEN_CONTRACTS.md` and `docs/specs/frontend_screen_contracts.md` when route responsibilities change;
- `frontend/README.md` and demo runbooks when operator flow changes.
