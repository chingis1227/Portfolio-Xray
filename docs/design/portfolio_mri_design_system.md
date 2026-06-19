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

The interface must be calm, precise, trustworthy, dark, analytical, and client-ready. It must not feel like a trading terminal, optimizer cockpit, crypto exchange, glossy glass prototype, dashboard wall, or Excel clone.

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
| `#0A0A0A` | App background | Main shell and page canvas. |
| `#0A0A0A` | Secondary background | Section bands and shell chrome. |
| `#191919` | Card surface | Evidence cards and product panels. |
| `#1A1C20` | Raised surface | Hovered or nested surfaces without shadow elevation. |
| `#191919` | Panel surface | Forms and dense panels. |
| `#212327` | Border | Hairline dividers, cards, table rules, and inputs. |
| `rgba(255,255,255,0.25)` | Soft border | White-translucent pill and secondary outlines. |
| `#FFFFFF` | Primary text / white action | Headings, key values, active state, focus, and rare filled primary action. |
| `#DADBDF` | Secondary text / neutral accent | Body copy, interpretation, and formal neutral emphasis. |
| `#7D8187` | Muted text | Captions, metadata, inactive state. |
| `#A0C3EC` | Breeze Blue | Rare illustrative or informational accent only. |
| `#C4B5FD` | Twilight | Rare illustrative accent and subtle emphasis only. |
| `#FF7A17` | Sunset Orange | Material issue, error, failure, destructive action, or high-risk evidence. |
| `#FFC285` | Sunset Soft | Watch, caution, partial, evidence required, locked, or degraded confidence. |

Green is not a Portfolio MRI product/system status semantic. If legacy backend or adapter enums still emit `green`, frontend presentation must normalize it to neutral/ivory treatment unless a future contract explicitly reintroduces green.

## Typography

- Use the implemented `DM Sans` stack from `--font-pmri-sans` with Inter/system fallbacks.
- Use `IBM Plex Mono` through `--font-pmri-mono` for tracked technical labels.
- Keep weight 400 as the default and dominant weight.
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

Platform routes use a compact route-title top header, left sidebar, verdict-first page heroes on redesigned analytical routes, content cards, and clear locked/empty states. Redesigned analytical routes carry the compact step context inside `VerdictHero` and suppress the sticky top journey rail. The sidebar remains visible but should be visually secondary: active/current uses a light pill, completed uses muted neutral text, and locked/unavailable uses muted treatment.

## Component rules

- Cards use restrained rounded corners, thin hairline borders, flat dark surfaces, and no decorative shadow depth.
- Badges are sparse and evidence-backed. Page-level status belongs primarily in `VerdictHero`; row-level status appears only when it clarifies a specific metric.
- `EvidenceSummary` is capped at four items in one quiet strip and must not repeat the hero verdict.
- `MetricMatrix` groups analytical rows with metric, portfolio value, reference/threshold, status, and meaning. Fixed groups come first; material/problem rows sort first within each group.
- Primary CTAs use the white filled `.pmri-primary-action` treatment with near-black text for contrast and are reserved for the next safe product action.
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
