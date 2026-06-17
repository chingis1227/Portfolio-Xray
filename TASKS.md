# Portfolio MRI Redesign Tasks

This task plan translates `PRD.md` into implementation phases and actionable tasks.

## Scope Guardrails

- Preserve the diagnosis-first, current-portfolio-first journey.
- Do not change backend formulas, diagnosis logic, candidate generation algorithms, or optimizer behavior.
- Keep Stress Lab current-portfolio-only.
- Keep Client Fit diagnostic and non-binding.
- Keep Hypothesis and Candidate flows framed as tests, not recommendations.
- Keep Verdict language non-binding unless current product contracts explicitly change.
- Do not introduce green as a system-level status color.
- Do not redesign generated PDF output unless requested separately.

## Phase 0: Product and UI Inventory

Goal: map the current frontend implementation to the PRD before changing screens.

Tasks:

- [x] Identify all frontend routes covered by the redesign:
  - `/diagnosis`
  - `/evidence`
  - `/client-fit`
  - `/hypothesis`
  - `/comparison`
  - `/verdict`
  - `/report`
- [x] Map existing components used for page titles, hero sections, step context, sidebars, cards, badges, and metric displays.
- [x] Identify duplicated or competing status treatments across hero areas, cards, badges, and tables.
- [x] Identify where current pages use high-density card grids that should become Metric Matrix layouts.
- [x] Confirm which existing data fields are available for verdicts, evidence summaries, metric rows, and comparison rows.
- [x] Record any missing frontend data fields as implementation constraints, not backend change requests.

Acceptance checks:

Evidence: `docs/design/redesign_inventory.md`.

- [x] Covered routes and components are listed.
- [x] Required data for each redesigned page is known or explicitly marked unavailable.
- [x] No backend behavior changes are proposed in this phase.

## Phase 1: Design Tokens and Visual System Foundation

Goal: establish the calm premium visual system shared by all redesigned pages.

Tasks:

- [x] Define semantic color tokens for:
  - Soft White / Ivory
  - Steel Blue
  - Muted Copper Red
  - Muted Amber Gold
- [x] Remove or demote green from system-level status semantics.
- [x] Define neutral dark surface tokens for background, primary surface, secondary surface, borders, dividers, and muted text.
- [x] Define typography tokens for verdict headlines, explanations, evidence labels, metric values, row text, and technical notes.
- [x] Define spacing rules for page sections, hero blocks, evidence summaries, matrices, and technical details.
- [x] Update shared frontend styles and design documentation that own these tokens.

Acceptance checks:

- [x] The four semantic colors are documented and used consistently.
- [x] Green is not used for system status language.
- [x] New tokens support high readability on dark backgrounds.
- [x] Visual hierarchy relies more on spacing and typography than nested borders.

## Phase 2: Shared Layout Components

Goal: build reusable structure before redesigning individual pages.

Tasks:

- [x] Create or refactor a shared `Verdict Hero` component.
- [x] Support the hero structure:
  - compact step context label;
  - page-level verdict headline;
  - one concise interpretation sentence;
  - optional two to three supporting facts.
- [x] Create or refactor a compact top step context component using `Step X of 8 - Page Name`.
- [x] Remove or disable the full horizontal top journey stepper on redesigned pages.
- [x] Refactor the desktop sidebar to be quieter while keeping:
  - product name;
  - short subtitle;
  - journey step list;
  - completed, current, and unavailable states.
- [x] Use Steel Blue only for the active/current sidebar step.
- [x] Reduce heavy borders, bright outlines, dots, repeated micro-elements, and competing badges in navigation.

Acceptance checks:

- [x] Major pages can render a consistent Verdict Hero.
- [x] The top of each redesigned page no longer duplicates the full journey.
- [x] The sidebar remains visible and readable but visually secondary to page content.
- [x] No collapsed sidebar or presentation mode is introduced.

## Phase 3: Shared Analytical Components

Goal: replace card overload with reusable analytical patterns.

Tasks:

- [x] Create or refactor an `Evidence Summary` component.
- [x] Support three to four concise evidence items in one quiet shared container or strip.
- [x] Create or refactor a `Metric Matrix` component.
- [x] Support grouped metric rows with:
  - metric name;
  - portfolio value;
  - reference value or threshold where relevant;
  - status;
  - short explanation.
- [x] Create a comparison variant of Metric Matrix with:
  - current portfolio;
  - candidate portfolio;
  - change;
  - interpretation.
- [x] Add restrained row-level status styling.
- [x] Reduce repeated badge usage by centralizing status display rules.
- [x] Create a secondary technical detail pattern for raw tables, drill-downs, scenario evidence, and explanations.

Acceptance checks:

- [x] High-metric pages can use Metric Matrix instead of card grids.
- [x] Evidence Summary never exceeds four primary evidence items.
- [x] Status badges are sparse and tied to the four-color semantic system.
- [x] Technical details are secondary but still accessible.

## Phase 4: Diagnosis Page Redesign

Goal: make the dominant portfolio diagnosis immediately clear.

Tasks:

- [x] Add a Diagnosis Verdict Hero describing the dominant diagnosis.
- [x] Add an Evidence Summary with primary issue, severity, main drivers, and evidence quality.
- [x] Replace large diagnostic card grids with a Metric Matrix.
- [x] Group diagnosis metrics into:
  - risk pressure;
  - portfolio structure;
  - evidence quality;
  - secondary observations.
- [x] Move technical diagnostic evidence below the main matrix.
- [x] Remove repeated status badges that duplicate the page-level verdict.

Acceptance checks:

- [x] The main diagnosis is the largest and clearest message on the page.
- [x] Evidence directly explains the diagnosis before technical details.
- [x] The page does not feel like a grid of equal-weight cards.

## Phase 5: Stress Lab Page Redesign

Goal: show current-portfolio stress behavior without implying a rebalance verdict.

Tasks:

- [x] Add a Stress Lab Verdict Hero, such as `Material stress vulnerability detected`.
- [x] State clearly that Stress Lab is current-portfolio-only.
- [x] Add an Evidence Summary with worst scenario, estimated loss, main loss drivers, offset behavior, and evidence quality.
- [x] Use Metric Matrix for stress metrics and scenario evidence.
- [x] Replace many small panels with one analytical canvas for scenario contribution and asset impact.
- [x] Avoid repeating `Material vulnerability` or similar risk badges across many elements.

Acceptance checks:

- [x] The user can identify the worst stress scenario and estimated loss immediately.
- [x] The page does not create or imply a rebalance recommendation.
- [x] Scenario and asset impact evidence is consolidated and easy to scan.

## Phase 6: Client Fit Page Redesign

Goal: explain alignment with the stated risk profile while preserving non-binding diagnostic boundaries.

Tasks:

- [x] Add a Client Fit Verdict Hero, such as `Portfolio is outside stated risk profile`.
- [x] State that Client Fit is diagnostic context only.
- [x] State that Client Fit is not suitability approval, trade advice, or a replacement for portfolio diagnosis.
- [x] Add an Evidence Summary with the main mismatch dimensions.
- [x] Use Metric Matrix for profile checks such as volatility, drawdown, stress loss, and other relevant dimensions.
- [x] Avoid repeating `Outside` on every card or row unless needed for clarity.

Acceptance checks:

- [x] The user understands the main fit mismatch quickly.
- [x] Non-binding Client Fit language is visible and unambiguous.
- [x] Repeated outside-profile status treatment is reduced.

## Phase 7: Hypothesis Page Redesign

Goal: frame candidate creation as a diagnostic test, not an optimization dashboard.

Tasks:

- [x] Add a Hypothesis Verdict Hero focused on the proposed test, such as `Improve crisis resilience`.
- [x] Show why the test was selected.
- [x] Show success criteria clearly.
- [x] Make builder controls visually secondary and calm.
- [x] Reduce excessive panels around controls.
- [x] Preserve language that the candidate is a test, not a rebalance recommendation.
- [x] Do not use Metric Matrix as the primary pattern on this page.

Acceptance checks:

- [x] The selected diagnostic test is clear before controls appear.
- [x] Success criteria are visible and easy to understand.
- [x] The page does not feel optimizer-first.

## Phase 8: Comparison Page Redesign

Goal: make current-vs-candidate trade-offs clear.

Tasks:

- [x] Add a Comparison Verdict Hero summarizing the comparison outcome.
- [x] Replace comparison card overload with a comparison Metric Matrix.
- [x] Use columns for current portfolio, candidate portfolio, change, and interpretation.
- [x] Group comparison rows by:
  - risk improvement;
  - trade-offs;
  - fit impact;
  - evidence quality.
- [x] Highlight only material differences.
- [x] Avoid turning each comparison metric into a standalone card.

Acceptance checks:

- [x] The user can see what improved, what worsened, and what trade-offs were introduced.
- [x] Material differences stand out without excessive badges.
- [x] Current and candidate values are aligned and easy to compare.

## Phase 9: Verdict Page Redesign

Goal: present a decision interpretation instead of a dense metric dashboard.

Tasks:

- [x] Add a decision-level Verdict Hero.
- [x] Present the decision, rationale, major trade-offs, and boundaries.
- [x] Use narrative summary and selected evidence instead of a full Metric Matrix.
- [x] Preserve non-binding diagnostic language.
- [x] Remove low-priority metric density that competes with the decision summary.

Acceptance checks:

- [x] The final decision interpretation is clear at the top.
- [x] The rationale is understandable without reading a dense dashboard.
- [x] The page avoids recommendation or trade-instruction language.

## Phase 10: Report Page Redesign

Goal: make the report page read like an executive summary.

Tasks:

- [x] Convert the report page into a narrative report structure.
- [x] Include the main diagnosis.
- [x] Include selected stress evidence.
- [x] Include Client Fit context.
- [x] Include comparison outcome.
- [x] Include final verdict.
- [x] Use selected evidence only instead of every metric from every screen.
- [x] Remove dashboard-like clutter.

Acceptance checks:

- [x] The report can be reviewed as a concise diagnostic story.
- [x] The report is shareable without requiring deep product navigation knowledge.
- [x] The report does not duplicate every analytical metric.

## Phase 11: Badge, Status, and Container Rationalization

Goal: apply the visual simplification consistently across all redesigned pages.

Tasks:

- [x] Audit repeated badges after page redesigns.
- [x] Keep page-level status primarily in the Verdict Hero.
- [x] Keep row-level status only where it clarifies a specific metric.
- [x] Remove duplicate status language across hero, cards, rows, and side panels.
- [x] Reduce nested cards and excessive borders.
- [x] Replace bright or inconsistent gradients with calm dark surfaces.
- [x] Use spacing and typography to define hierarchy.
- [x] Ensure technical details are visually secondary.

Acceptance checks:

- [x] Repeated labels such as `Outside`, `Limited evidence`, and `Material vulnerability` are not overused.
- [x] Page hierarchy is clearer than the previous panel-heavy interface.
- [x] The interface feels calmer and more premium.

## Phase 12: Documentation and QA

Goal: verify that the redesign matches the PRD and project contracts.

Tasks:

- [x] Update design documentation for the new visual system, page architecture, and shared patterns.
- [x] Update screen or frontend contracts if route responsibilities, page structure, or component behavior changed.
- [x] Verify diagnostic and non-binding product boundary language across redesigned pages.
- [x] Run focused frontend checks for changed components.
- [ ] Run visual QA on the redesigned route chain using a fresh local target.
- [ ] Confirm the active review state and route data are not stale during browser QA.
- [ ] Capture screenshots for redesigned pages where practical.
- [x] Check for stale references to the old top stepper, old card-heavy patterns, and green status semantics.
- [x] Record any unverified areas or blocked checks.

Acceptance checks:

- [x] Every major page has one obvious primary verdict.
- [x] The top stepper no longer duplicates the full journey.
- [x] The sidebar remains visible but visually quieter.
- [x] High-metric pages use Metric Matrix instead of card overload.
- [x] Repeated badges are reduced.
- [x] The visual system uses the four documented colors consistently.
- [x] Green is not used as a system status color.
- [x] Diagnostic and non-binding product boundaries remain intact.
- [x] Verification results and unverified areas are reported.





Verification note: frontend `npm.cmd run typecheck` and `npm.cmd run build` passed on 2026-06-17. Sub-agent review scored the first pass 6.5/10; follow-up fixes parameterized `MetricMatrix`, suppressed top journey rail on redesigned routes, removed the duplicate Client Fit hero, and cleaned visible placeholder bullets. Fresh browser visual QA was not completed in this pass and remains unverified.
