# Portfolio MRI Design System

## Status

This is the canonical UI/UX design direction for the implemented Portfolio MRI frontend. It mirrors the current Next.js site in `frontend/` and should be updated whenever the actual site structure, tokens, layout, or visual rules change.

Use this with:

- `DESIGN.md` for top-level design orientation;
- `docs/design/current_website_structure.md` for route-by-route page structure and visible content;
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` for enforceable review rules;
- `docs/contracts/SCREEN_CONTRACTS.md` for screen responsibilities.

Old external-reference guidance and prototype handoffs are not current design authority.

## Product design thesis

Portfolio MRI is an Investment Decision Room. The UI guides a user from public explanation to sign-in, onboarding, current portfolio input, diagnosis, stress evidence, Client Fit context, one hypothesis test, comparison, non-binding verdict, and grounded report preview.

The interface must be calm, precise, trustworthy, dark, analytical, and client-ready. It must not feel like a trading terminal, optimizer cockpit, crypto exchange, dashboard wall, or Excel clone.

## Current route journey

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

Platform rail:

1. Portfolio
2. Diagnosis
3. Stress Lab
4. Client Fit
5. Hypothesis
6. Comparison
7. Verdict
8. Report

Local testing shortcut `/onboarding/name?dev_bypass=1` is allowed only for local preview while sign-in is being stabilized.

## Principles

1. Diagnose the current portfolio before showing candidate tests.
2. Treat candidates as hypotheses, never recommendations.
3. Treat verdicts as non-binding decision support.
4. Make no-trade and evidence-insufficient outcomes look valid, not broken.
5. Show one decision question per screen.
6. Keep technical detail available but secondary.
7. Use color only when it communicates product meaning.
8. Keep the UI premium, dark, sparse, and structured.

## Current color system

| Role | Hex | Usage |
| --- | --- | --- |
| `#090A0C` | App background | Landing and app shell. |
| `#101114` | Secondary background | Sidebar, onboarding frames, secondary panels. |
| `#17181B` | Card surface | Cards and evidence modules. |
| `#1D1F23` | Raised surface | Nested/lifted cards. |
| `#202329` | Panel surface | Forms and dense panels. |
| `#2A2D33` | Border | Standard card and table borders. |
| `#3A3E46` | Soft border | Secondary outlines. |
| `#ECEFF3` | Primary text | Headings and key values. |
| `#C4C9D1` | Secondary text | Body and explanations. |
| `#949BA6` | Muted text | Captions, metadata, inactive state. |
| `#4F7EA8` | Steel Blue | Active/current/selected state, primary action, focus, and safe information emphasis. |
| `#7EA6C8` | Soft Steel Blue | Links, hover, and restrained section accents. |
| `#B66A61` | Muted Copper Red | Material issue, error, failure, destructive action, or high-risk evidence. |
| `#C3A15F` | Muted Amber Gold | Watch, caution, partial, evidence required, locked, or degraded confidence. |
| `#ECE7DC` | Ivory / neutral aligned | Normal, aligned, completed, generated, unavailable-neutral, unchanged, or secondary context. |
| `#AAB7C6` | Premium slate accent | Formal accent and technical premium tone. |

Green is not a Portfolio MRI product/system status semantic. If legacy backend or adapter enums still emit `green`, frontend presentation must normalize it to neutral/ivory treatment unless a future contract explicitly reintroduces green.

## Typography

- Use the current sans stack from `--font-pmri-sans` with Inter/Manrope fallbacks.
- Use tabular numbers for metric values via `.data-figure`.
- Use strong but restrained negative tracking for large headings.
- Keep body copy short and explanatory.
- Avoid expressive display fonts and decorative all-caps.

## Layout system

### Public landing

Landing uses no platform shell. It is a product explanation page with header navigation, hero, problem, workflow, architecture, precision, and final CTA blocks.

### Onboarding

Onboarding uses a focused public frame. It should feel simple and human: sign in, name, five questions, setup transition. It writes Client Fit context but must not sound like suitability approval.

### Platform shell

Platform routes use a left sidebar, verdict-first page heroes on redesigned analytical routes, content cards, and clear locked/empty states. Redesigned analytical routes carry the compact step context inside `VerdictHero` and suppress the sticky top journey rail. The sidebar remains visible but should be visually secondary: active/current uses Steel Blue, completed uses neutral text, and locked/unavailable uses muted treatment.

## Component rules

- Cards use rounded corners, thin slate borders, dark surfaces, subtle gradients, and `shadow-decision` depth.
- Badges are sparse and evidence-backed. Page-level status belongs primarily in `VerdictHero`; row-level status appears only when it clarifies a specific metric.
- `EvidenceSummary` is capped at four items in one quiet strip and must not repeat the hero verdict.
- `MetricMatrix` groups analytical rows with metric, portfolio value, reference/threshold, status, and meaning. Fixed groups come first; material/problem rows sort first within each group.
- Primary CTAs use the Steel Blue `.pmri-primary-action` treatment.
- Secondary CTAs use border/transparent dark styling.
- Tables must be readable and bounded by explanatory copy.
- Locked states must explain the missing prerequisite and provide a safe CTA.

## Motion rules

- Motion is part of the premium decision-room feel: calm, brief, and explanatory.
- Use Framer Motion for route transitions, scroll reveals, active journey indicators, onboarding question changes, and subtle card/CTA feedback.
- Prefer GPU-friendly opacity and transform changes with restrained spring physics.
- Stagger lists only enough to improve scan order; do not create showy cascades.
- Respect reduced-motion preferences on every animation.
- Do not animate evidence in a way that implies recommendation strength, suitability approval, trade urgency, or guaranteed improvement.

## Screen structure authority

Do not duplicate route block order in this file. The implemented page-by-page structure is maintained in `docs/design/current_website_structure.md`.
