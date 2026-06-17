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

The implemented frontend uses a near-black graphite decision-room style with cool slate surfaces, restrained steel-blue evidence accents, muted semantic statuses, large rounded cards, floating glass navigation, and controlled depth. The public landing now uses a premium-fintech diagnostic cockpit language: dark stage, glass device preview, compact evidence feed, white primary CTA, and a dock preview inspired by modern investment interfaces while preserving Portfolio MRI's diagnosis-first boundaries.

The atmosphere should feel:

- institutional;
- precise;
- calm;
- premium dark;
- current-portfolio-first;
- client-ready;
- analytical without looking like a trading terminal.

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
| Steel Blue | `pmri.blue`, `pmri.steelBlue`, `--pmri-steel-blue`, `--pmri-action-blue` | `#6EA8D7` | Primary CTA, active/current/selected navigation, focus, informational emphasis. |
| Soft Steel Blue | `pmri.blueSoft` | `#9DCCF0` | Links, hover, section accents. |
| Ivory | `pmri.ivory`, `pmri.positive`, `--pmri-ivory`, `--pmri-positive` | `#ECE7DC` | Normal, aligned, completed, generated, unavailable-neutral, and secondary states. This is not a green status. |
| Muted Amber Gold | `pmri.amber`, `pmri.amberGold`, `--pmri-amber-gold`, `--pmri-warning` | `#C3A15F` | Watch, caution, locked, partial, evidence required. |
| Muted Copper Red | `pmri.risk`, `pmri.copperRed`, `--pmri-copper-red`, `--pmri-risk` | `#B66A61` | Material issue, error, failure, destructive action, or high-risk evidence. |
| Premium accent | `pmri.gold`, `--pmri-premium-accent` | `#AAB7C6` | Formal slate accent, not decorative gold. |

## Color Semantics

- Steel Blue means action, active/current journey state, selected navigation, focus, or safe informational emphasis.
- Ivory and neutral gray mean normal, aligned, completed, generated, unavailable, metadata, unchanged, or secondary context.
- Muted Amber Gold means watch, caution, evidence required, partial evidence, locked state, or degraded confidence.
- Muted Copper Red means material issue, actual error, material worsening, failed run, destructive action, or high-risk evidence.
- Green is not a Portfolio MRI product/system status semantic. Legacy API enum values may still be normalized by adapters, but Core MVP UI must not rely on green as the visible status color.

Use color sparsely. Most pixels should remain graphite, slate, and readable white/gray text.

## Typography

Current implementation uses Manrope through `--font-pmri-sans`, with Helvetica Neue and Arial fallbacks. Numeric values use tabular-number styling through `.data-figure`.

Rules:

- Large page titles use restrained negative tracking and medium weight.
- Section titles are compact and clear.
- Body copy is short, concrete, and explanatory.
- Status labels are small and sparse.
- Numeric values should be decision-relevant, not decorative precision.
- Avoid playful display fonts and heavy all-caps as the dominant voice.

## Layout and Components

### Public landing

The landing page is public and does not show the platform dock or top journey rail. It uses an asymmetric hero, premium-fintech glass cockpit preview, compact diagnosis metrics, a dock preview, reveal animation, rounded white primary CTAs, and structured blocks for diagnosis architecture, canonical flow, decision boundary, and final CTA.

### Onboarding

Onboarding routes are public-frame screens without the platform sidebar. Canonical entry is `/onboarding/sign-in`; local testing may use `/onboarding/name?dev_bypass=1`. Onboarding collects a friendly profile and creates non-binding Client Fit context before Portfolio Input.

### Platform shell

Platform routes use:

- a fixed bottom floating glass dock with 8 gated journey steps and icon emblems;
- a separate Workspace dock control and optional account control on wider screens;
- a sticky compact step context rail instead of a full horizontal journey stepper on redesigned routes;
- a verdict-first page hero on redesigned analytical routes;
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

Redesigned analytical pages use shared `VerdictHero`, `EvidenceSummary`, and `MetricMatrix` patterns. `VerdictHero` carries the page-level message with compact step context, one interpretation sentence, up to three supporting facts, and an optional boundary note. `EvidenceSummary` is capped at four items in one quiet strip. `MetricMatrix` groups rows with metric, portfolio value, reference/threshold, status, and meaning; material/problem rows sort first inside fixed groups.

Portfolio Diagnosis uses a diagnosis-first simplification pattern: one dominant hero finding, a maximum four-item evidence summary, an expanded Metric Matrix, and advanced diagnostics hidden by default. Professional metrics such as VaR, ES, skewness, kurtosis, beta, Sharpe, Sortino, and Treynor remain available behind disclosure controls rather than dominating the first read.

### Motion and micro-interactions

Motion should make the decision room feel calmer and more legible, not flashier. Use Framer Motion for route fades, section reveals, active-rail movement, onboarding question changes, and selected/hovered decision surfaces where the motion clarifies hierarchy or state. Prefer opacity and transform with restrained spring physics, keep stagger timing subtle, and always respect reduced-motion preferences. Pressed CTAs and compact control pills may use a small tactile scale/translate response. Do not add decorative movement that competes with portfolio evidence, stress results, Client Fit boundaries, candidate trade-offs, or verdict language.

### Badges

Badges must communicate evidence-backed state. Do not use badges as decoration. One primary badge per card header is preferred. Do not repeat generic evidence badges such as `Evidence available` across every Diagnosis fact; use one global data-coverage state and reserve per-row badges for material risk or review state. Blue, amber, and red badges use a small colored signal dot plus subdued glow; slate and ivory/neutral badges stay quieter.

### CTAs

Primary CTAs use the brighter blue gradient `.pmri-primary-action` with dark text for contrast. Secondary CTAs use thin borders and dark transparent backgrounds. CTA copy must describe the next safe product step and must not imply trading or optimizer execution.

## Current Website Structure

The current route-by-route website structure, block order, visible headings, CTA behavior, and locked states are documented in [docs/design/current_website_structure.md](docs/design/current_website_structure.md). Keep that document synchronized whenever landing, onboarding, route order, page copy, CTA placement, visible metrics, or locked states change.

## Documentation Sync Rule

Any meaningful UI change must update:

- this file when visual style, tokens, layout, or components change;
- `docs/design/current_website_structure.md` when route structure, block order, visible copy, CTAs, or screen states change;
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` when enforceable design rules change;
- `docs/contracts/SCREEN_CONTRACTS.md` and `docs/specs/frontend_screen_contracts.md` when route responsibilities change;
- `frontend/README.md` and demo runbooks when operator flow changes.
