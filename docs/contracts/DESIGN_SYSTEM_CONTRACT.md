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

Portfolio MRI must feel like a premium dark institutional investment decision room: calm, precise, trustworthy, analytical, and client-ready. It must not look like a trading terminal, optimizer cockpit, crypto app, colorful dashboard, or Excel clone.

## Current token contract

The current frontend token set is the contract baseline:

| Meaning | Hex | Required behavior |
| --- | --- | --- |
| Background | `#050608` | Dominant cinematic platform shell. |
| Secondary surface | `#0B0D10` | Sidebar, onboarding, section panels. |
| Card surface | `#111318` | Floating case-file panels and standard content cards. |
| Raised surface | `#16191F` | Nested or lifted surfaces. |
| Panel | `#1A1E25` | Forms and dense panels. |
| Border | `#20242B` | Card/table/divider outlines. |
| Text | `#ECEFF3` | Headings and decisive values. |
| Secondary text | `#C4C9D1` | Body copy and interpretation. |
| Muted text | `#949BA6` | Captions and inactive states. |
| Steel Blue | `#4F7EA8` / `#7EA6C8` | Active/current/selected state, primary action, focus, and safe information emphasis. |
| Muted Copper Red | `#B66A61` | Material issue, error, failure, destructive action, and high-risk evidence. |
| Muted Amber Gold | `#C3A15F` | Watch, caution, partial evidence, locked, evidence required, and degraded confidence. |
| Ivory / neutral aligned | `#ECE7DC` | Normal, aligned, completed, generated, unavailable-neutral, unchanged, and secondary context. |
| Premium accent | `#AAB7C6` | Formal slate accent only. |

Any intentional code-token change must update this table and `DESIGN.md` in the same change.

## Color semantics

- Steel Blue is for action, active/current navigation, focus, selected state, and safe informational emphasis.
- Ivory and neutral gray are for normal, aligned, completed, generated, metadata, unavailable, unchanged, and secondary states.
- Muted Amber Gold is for watch, caution, evidence required, partial evidence, blocked or locked states.
- Muted Copper Red is for material issues, actual errors, failures, destructive actions, material worsening, and high-risk evidence.
- Green is not a Portfolio MRI product/system status semantic. Legacy enum values may exist in adapters, but visible Core MVP status color must normalize them to neutral/ivory treatment unless a future contract explicitly changes this.

No neon, rainbow, crypto-style glow systems, or decorative red/green chart coloring are allowed in Core MVP UI.

## Layout contract

- Landing and onboarding must not show the platform sidebar or top journey rail.
- Platform screens must show the visible left 8-step rail: Portfolio, Diagnosis, Stress Lab, Client Fit, Hypothesis, Comparison, Verdict, Report.
- The platform workspace must use a deep cinematic black background with subtle radial gradients and glass depth. It must not fall back to a flat gray dashboard wall.
- Platform top headers must be compact utility bars. They may show route title and quiet metadata, but must not show noisy review-status or evidence-quality pills as the main header treatment.
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
- Diagnosis must show the hero, four-item evidence strip, and primary diagnostic canvas before MetricMatrix, professional metrics, full X-Ray detail, technical evidence, or raw evidence-chain details.
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
