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
| Background | `#090A0C` | Dominant page shell. |
| Secondary surface | `#101114` | Sidebar, onboarding, section panels. |
| Card surface | `#17181B` | Standard content cards. |
| Raised surface | `#1D1F23` | Nested or lifted surfaces. |
| Panel | `#202329` | Forms and dense panels. |
| Border | `#2A2D33` / `#25282E` | Card/table/divider outlines. |
| Text | `#ECEFF3` | Headings and decisive values. |
| Secondary text | `#C4C9D1` | Body copy and interpretation. |
| Muted text | `#949BA6` | Captions and inactive states. |
| Blue | `#3B82F6` / `#60A5FA` | Action, focus, active journey. |
| Positive | `#6FBF9B` | Ready, completed, generated, improved. |
| Amber | `#C9A66B` | Caution, locked, partial, evidence required. |
| Risk | `#D77A7A` | Error, failure, worsening, material risk. |
| Premium accent | `#AAB7C6` | Formal slate accent only. |

Any intentional code-token change must update this table and `DESIGN.md` in the same change.

## Color semantics

- Blue is for action, active navigation, focus, selected state, and safe informational emphasis.
- Green is for ready/completed/generated/improved states. It never means suitability approval or trade recommendation.
- Amber is for caution, evidence required, partial evidence, blocked or locked states.
- Red is for actual errors, failures, destructive actions, material worsening, and risk.
- Slate/gray is for neutral, inactive, metadata, unavailable, unchanged, or structural boundaries.

No neon, rainbow, crypto-style glow systems, or decorative red/green chart coloring are allowed in Core MVP UI.

## Layout contract

- Landing and onboarding must not show the platform sidebar or top journey rail.
- Platform screens must show the 8-step rail: Portfolio, X-Ray, Stress Lab, Client Fit, Hypothesis, Comparison, Verdict, Report.
- Page headers must use matching step numbers and route names.
- Locked screens must display the actual route step while explaining the missing prerequisite.
- Advanced/manual Client Fit editing remains `/client-profile` and is not the main onboarding path.

## Card and badge contract

- Use cards as decision-reading units, not as raw JSON containers.
- A card header should usually have at most one primary status badge.
- Badges must have nearby explanatory copy.
- Status labels must be product-facing, not backend enum names or file names.
- Empty, locked, partial, no-trade, evidence-insufficient, and unavailable states are valid product states and must not look like broken UI.

## CTA contract

- Primary CTA: next safe product step.
- Secondary CTA: navigation, recovery, or non-primary action.
- CTA copy must never imply trading execution, suitability approval, optimizer mandate, or guaranteed improvement.
- `Enter Platform` on the public landing uses the canonical sign-in route. The dev-bypass route may be documented only as local testing support.

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
