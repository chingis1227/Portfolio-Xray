# Design System Contract

Status: enforceable visual contract for the current Portfolio MRI frontend.

This contract translates the current design system into implementation-review rules. It does not change CSS, runtime behavior, backend artifacts, schemas, formulas, or generated outputs by itself.

## Source-of-truth order

Use these documents together:

- `DESIGN.md` for the top-level current design system.
- `docs/design/portfolio_mri_design_system.md` for canonical design direction.
- `docs/design/current_website_structure.md` for route-by-route current website structure.
- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for product step order and boundaries.
- `docs/contracts/SCREEN_CONTRACTS.md` for route responsibilities and required states.
- `docs/contracts/PRESENTATION_LANGUAGE_RULES.md` for safe wording.
- `docs/contracts/QA_CONTRACT.md` for visual QA expectations.

Old external-reference and prototype documents are not current design authority.

## Design promise

Portfolio MRI must feel like a restrained dark institutional investment decision room: calm, precise, trustworthy, analytical, and client-ready. It must not look like a trading terminal, optimizer cockpit, crypto app, colorful dashboard, glossy glass prototype, or Excel clone.

## Current token contract

The current frontend token set is the contract baseline:

| Meaning | Hex | Required behavior |
| --- | --- | --- |
| Background | `#0A0A0A` | Dominant near-black app canvas. |
| Secondary background | `#0A0A0A` | Section bands and shell chrome. |
| Card surface | `#191919` | Flat evidence cards and product panels. |
| Raised surface | `#1A1C20` | Hovered or nested surfaces without shadow elevation. |
| Panel | `#191919` | Forms and dense panels. |
| Border | `#212327` | Card, table, divider, and input outlines. |
| Soft border | `rgba(255,255,255,0.25)` | Secondary outlines and pill borders. |
| Text | `#FFFFFF` | Headings, key values, active state, focus, and rare filled primary action. |
| Secondary text | `#DADBDF` | Body copy and interpretation. |
| Muted text | `#7D8187` | Captions, metadata, and inactive states. |
| Breeze Blue | `#A0C3EC` | Rare illustrative or informational accent only. |
| Twilight | `#C4B5FD` | Rare illustrative accent and subtle emphasis only. |
| Sunset Orange | `#FF7A17` | Material issue, error, failure, destructive action, and high-risk evidence. |
| Sunset Soft | `#FFC285` | Watch, caution, partial evidence, locked, evidence required, and degraded confidence. |
| Neutral accent | `#DADBDF` | Formal neutral accent, not decorative gold. |

Any intentional code-token change must update this table and `DESIGN.md` in the same change.

## Color semantics

- White is for foreground, active/current state, focus, and the rare filled primary action.
- Breeze Blue and Twilight are rare illustrative accents, not default action or navigation colors.
- Neutral gray is for normal, aligned, completed, generated, metadata, unavailable, unchanged, and secondary states.
- Sunset Soft is for watch, caution, evidence required, partial evidence, blocked or locked states.
- Sunset Orange is for material issues, actual errors, failures, destructive actions, material worsening, and high-risk evidence.
- Green is not a Portfolio MRI product/system status semantic. Legacy enum values may exist in adapters, but visible Core MVP status color must normalize them to neutral/ivory treatment unless a future contract explicitly changes this.

No neon, rainbow, crypto-style glow systems, decorative blue action gradients, or decorative red/green chart coloring are allowed in Core MVP UI.

## Layout contract

- Landing and onboarding must not show the platform sidebar or top journey rail.
- Platform screens must show the visible left 8-step rail: Portfolio, Diagnosis, Stress Lab, Client Fit, Hypothesis, Comparison, Verdict, Report. The current route uses a light active pill; inactive unlocked steps stay muted.
- The platform workspace must use a restrained near-black background with subtle texture only where it improves orientation. It must not use glossy glass depth, blue-gradient spectacle, or a flat gray dashboard wall.
- Platform top headers must be compact utility bars. They show the route title and restrained actions, but must not show portfolio/currency/holdings/update metadata, noisy review-status, or evidence-quality pills as the main header treatment.
- Platform top headers must not translate staged execution states such as `partial` into primary metadata. If a stage is blocked or failed, explain it inside the affected route state.
- Redesigned platform routes suppress the top journey rail and use compact step context inside `VerdictHero` instead of the full horizontal top stepper.
- Verdict-first heroes must use matching step numbers and route names.
- Locked screens must display the actual route step while explaining the missing prerequisite.
- Advanced/manual Client Fit editing remains `/client-profile` and is not the main onboarding path.

## Card and badge contract

- Use cards as decision-reading units, not as raw JSON containers.
- A card header should usually have at most one primary status badge.
- `VerdictHero` has a fixed structure: compact step context, headline, one-sentence interpretation, up to three supporting facts, optional boundary note, and restrained tone.
- `EvidenceSummary` must show at most four concise items in one quiet floating strip and must not repeat the page-level verdict.
- `MetricMatrix` rows use metric, portfolio value, reference/threshold, status, and meaning. Comparison variants use current portfolio, candidate portfolio, change, and interpretation. Fixed groups remain in product order; material/problem rows sort first within each group.
- Badges must have nearby explanatory copy.
- Diagnosis must not repeat generic evidence-availability badges across every fact. Use one global evidence-quality state in the evidence strip or advanced detail, not in the main top header, and reserve row-level badges for material risk, review state, or unavailable states.
- Primary surfaces must follow [Information Architecture and Copy Contract](INFORMATION_ARCHITECTURE_COPY_CONTRACT.md): product guardrails are authoring constraints, not repeated visible disclaimers.
- Diagnosis must show the hero, four-item evidence strip, and primary diagnostic canvas before MetricMatrix, professional metrics, legacy technical `portfolio_xray.json` detail, technical evidence, or raw evidence-chain details.
- Status labels must be product-facing, not backend enum names or file names.
- Empty, locked, partial, no-trade, evidence-insufficient, and unavailable states are valid product states and must not look like broken UI.

## CTA contract

- Primary CTA: next safe product step.
- Secondary CTA: navigation, recovery, or non-primary action.
- CTA copy must never imply trading execution, suitability approval, optimizer mandate, or guaranteed improvement.
- `Enter Platform` on the public landing uses the canonical sign-in route. The dev-bypass route may be documented only as local testing support.

## Motion contract

- Motion must be calm, short, and state-explanatory; it must not become a decorative or gamified layer.
- Framer Motion may be used for route fades, scroll reveals, active journey rail movement, onboarding question transitions, and subtle card or CTA feedback.
- Animations must primarily use opacity and transform, with restrained spring physics.
- Reduced-motion preferences must be respected.
- Motion must never make candidate tests, Client Fit output, comparison evidence, or verdicts feel like recommendations, trade instructions, suitability approval, or guaranteed improvement.

## Website structure contract

Whenever a route's visible blocks, headings, CTA, locked state, metric display, or page order changes, update `docs/design/current_website_structure.md` in the same change.

## Review checklist

Before accepting UI/design changes, verify:

1. No active docs refer to old external-reference or prototype output as design authority.
2. Landing/onboarding/platform shell separation is preserved.
3. The 8-step rail and page-header step labels match.
4. Colors match the current token contract or docs are updated with intentional changes.
5. Candidate, verdict, Client Fit, and report wording remains non-binding and evidence-grounded.
6. Browser QA uses a fresh localhost server and fresh browser state.

## Foundation and sandbox contract

Implementation must prefer shared primitives in `frontend/components/ui/` before page-local styling. Repeated actions, surfaces, evidence facts, disclosure controls, and empty/loading/error states should be represented by reusable components such as `Button`, `Surface`, `SectionHeader`, `EvidenceItem`, `AdvancedDisclosure`, and state components.

Product-specific blocks should compose primitives and live near their domain. The Diagnosis benchmark uses `DiagnosisHero`, `EvidenceStrip`, `DiagnosticCanvas`, and `AdvancedDiagnostics` in `frontend/components/diagnosis/`.

`/sandbox/components` is the local component gallery for foundation review. It may show sample copy and sample values, but it must not become a canonical product journey route and must not call backend review APIs.
