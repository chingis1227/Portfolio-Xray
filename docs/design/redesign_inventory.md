# Frontend Redesign Inventory

Status: Phase 0 implementation inventory for the Portfolio MRI frontend redesign.

This document maps the current frontend implementation to the redesign plan in `TASKS.md`. It is an implementation constraint document, not a backend change request. Backend formulas, diagnosis logic, stress logic, candidate generation, optimizer behavior, and API contracts remain unchanged.

## Inventory scope and baseline

Reviewed source areas:

- Covered route entries under `frontend/app`: `/diagnosis`, `/evidence`, `/client-fit`, `/hypothesis`, `/comparison`, `/verdict`, and `/report`.
- Route-level screen components under `frontend/components/diagnosis`, `frontend/components/evidence`, `frontend/components/client-fit`, `frontend/components/hypothesis`, `frontend/components/comparison`, `frontend/components/verdict`, and `frontend/components/report`.
- Shared layout and UI components under `frontend/components/layout` and `frontend/components/ui`.
- Frontend display/state helpers under `frontend/lib/reviewState.tsx`, `frontend/lib/diagnosisDisplayModel.ts`, and `frontend/lib/hypothesis/hypothesisScreenModel.ts`.

Excluded from Phase 0:

- Generated outputs, run-local artifacts, caches, PDFs, screenshots, and portfolio variant folders.
- Backend implementation changes, API contract changes, formulas, stress logic, candidate generation, optimizer logic, and generated report/PDF redesign.
- Existing dirty frontend/code changes in the working tree that predate this inventory. Phase 0 itself is documentation-only.

## Covered routes

The redesign covers the current diagnosis-first analytical route chain:

| Route | Current page entry | Primary screen/component | Redesign role |
| --- | --- | --- | --- |
| `/diagnosis` | `frontend/app/diagnosis/page.tsx` | `DiagnosisScreen`, `DiagnosisSummaryPanel`, `PortfolioXRayBlocks` | Dominant current-portfolio diagnosis. |
| `/evidence` | `frontend/app/evidence/page.tsx` | `EvidenceScreen`, `StressTestLab` | Current-portfolio-only Stress Test Lab evidence. |
| `/client-fit` | `frontend/app/client-fit/page.tsx` | `ClientFitScreen` | Non-binding Client Fit diagnostic context. |
| `/hypothesis` | `frontend/app/hypothesis/page.tsx` | `HypothesisScreen` | Diagnosis-led candidate test framing. |
| `/comparison` | `frontend/app/comparison/page.tsx` | `ComparisonScreen` | Current-vs-candidate trade-off comparison. |
| `/verdict` | `frontend/app/verdict/page.tsx` | `VerdictScreen` | Non-binding decision interpretation. |
| `/report` | `frontend/app/report/page.tsx` | `ReportScreen` | Concise narrative report preview. |

`/client-profile` is not part of the normal redesigned analytical route chain. It remains an advanced/manual Client Fit editor.

## Existing shared UI components

| Pattern | Current implementation | Inventory finding |
| --- | --- | --- |
| Platform shell | `AppShell` | Renders the sidebar and the full sticky `TopJourneyProgress` for platform routes. Redesign should suppress the full top stepper only on redesigned analytical routes. |
| Sidebar navigation | `Sidebar` | Already owns journey states, lock behavior, account/workspace entry, and active route highlighting. It should become visually quieter, not be removed or collapsed. |
| Top journey rail | `TopJourneyProgress` | Full horizontal route chain currently competes with page-level diagnosis/verdict hierarchy. Redesign should replace it with compact step context on covered routes. |
| Page header | `PageHeader` | Current page-level header is broad and often paired with status badges. Redesign should migrate analytical pages toward one strict `VerdictHero` pattern. |
| Decision hero card | `DecisionHeroCard` | Existing hero-like component is useful precedent but allows status badges in the header. New `VerdictHero` should be stricter. |
| Status badge | `StatusBadge` | Widely used across heroes, cards, rows, panels, empty states, and technical details. Redesign needs a status hierarchy to reduce repetition. |
| Metric card | `MetricCard` | Used for dense metrics and advanced diagnostics. High-metric pages should migrate key rows into `MetricMatrix` instead of card grids. |

## Route-specific component inventory

| Route | Major current child components | Shared dependencies | Primary redesign risk |
| --- | --- | --- | --- |
| `/diagnosis` | `DiagnosisSummaryPanel`, `PortfolioXRayBlocks`, diagnosis section navigation, behavior/advanced diagnostic blocks | `PageHeader`, `StatusBadge`, `MetricCard` | Existing diagnosis evidence can become a wall of cards and repeated badges instead of one dominant diagnosis. |
| `/evidence` | `StressTestLab`, `MainStressDiagnosisPanel`, `ScenarioLibraryPanel`, `SelectedScenarioDetailPanel`, `LossContributionPanel`, `HelpedHurtPanel`, `HedgeGapAnalysisPanel`, `FactorStressAttributionPanel`, `StressScorecardPanel`, `DataLimitationsPanel` | `PageHeader`, `StatusBadge`, stress story/model helpers | Stress Lab can look like multiple independent panels and imply a rebalance verdict if current-portfolio-only language is not prominent. |
| `/client-fit` | `ClientFitScreen`, `ClientFitContextCard`, reason cards, compact check rows | `PageHeader`, `StatusBadge` | Repeated fit labels can read like suitability approval or hide material diagnosis issues. |
| `/hypothesis` | `HypothesisScreen`, primary diagnosis panel, selected test panel, builder/action console, alternative tests, technical details | `StatusBadge`, `ClientFitContextCard`, hypothesis screen model | Builder controls can dominate and make the page feel optimizer-first. |
| `/comparison` | `ComparisonScreen`, `CandidateComparisonPanel`, `TradeoffSummary`, allocation lists, Client Fit context, action panels | `PageHeader`, `StatusBadge`, `ClientFitContextCard` | Candidate improvements can read as a recommendation unless trade-offs and boundaries are equally visible. |
| `/verdict` | `VerdictScreen`, `VerdictPanel`, evidence panels, confidence/monitoring/action framing blocks, Client Fit context | `PageHeader`, `StatusBadge`, `ClientFitContextCard` | Decision language can become trade advice if the hero is too direct or uses approval/safety wording. |
| `/report` | `ReportScreen`, `ClientReadyReportPreview`, report preview sections, evidence/warnings blocks | `PageHeader`, `StatusBadge` | The report can drift back into dashboard duplication instead of a concise diagnostic story. |

## Current top journey usage

`AppShell` imports and renders `TopJourneyProgress` for non-public routes. Because the covered routes are platform routes, they currently receive both the sidebar journey list and the full top journey rail.

Implementation constraint:

- Keep the sidebar visible.
- On covered analytical routes, do not render the full horizontal route chain.
- Use compact step context in the shared `VerdictHero`, such as `Step 2 of 8 - Portfolio Diagnosis`.
- Avoid changing onboarding and portfolio-input orientation unless a later task explicitly includes those routes.

## Card overload and repeated badge hotspots

| Route/component | Current pattern | Redesign constraint |
| --- | --- | --- |
| Diagnosis | `DiagnosisSummaryPanel` has a hero-like section, `WhatMattersFirst`, behavior cards, advanced metric cards, and `PortfolioXRayBlocks` with many card grids. | Make the dominant diagnosis the clearest message; use Evidence Summary and an expanded Metric Matrix for primary facts. Keep technical blocks secondary. |
| Stress Lab | `StressTestLab` has story metric cards, fact cards, section nav, scenario panels, and technical disclosures. | Show worst scenario, loss estimate, drivers, offset behavior, and evidence quality immediately. Consolidate repeated risk labels. |
| Client Fit | `ClientFitScreen` uses header badges, reason cards, compact rows, and repeated fit statuses. | Keep non-binding boundary visible; use matrix rows for profile checks; avoid repeating `Outside` on every surface. |
| Hypothesis | `HypothesisScreen` has diagnosis panel, selected test panel, action console, Client Fit context, alternative tests, and technical details. | Keep test thesis and success criteria first; builder controls stay secondary; do not use Metric Matrix as primary pattern. |
| Comparison | `ComparisonScreen` has header status, candidate/current allocation panels, comparison sections, Client Fit context, and multiple status cards. | Use outcome + boundary in the hero and comparison Metric Matrix for improvements, trade-offs, fit impact, and evidence quality. |
| Verdict | `VerdictScreen` uses header status, non-binding language, evidence panels, Client Fit context, action framing, confidence, and monitoring details. | Use cautious diagnostic verdict plus narrative rationale; avoid recommendation language. |
| Report | `ReportScreen` uses header status, preview status, report narrative, evidence cards, and warnings. | Make the page read like an executive summary with selected evidence only. |

## Status and color constraints

Current frontend types include legacy tone names such as `blue` and `green` in `StatusTone`. These names may remain as adapter compatibility labels, but the current design system normalizes visible Core MVP presentation to the `DESIGN.md` palette.

Redesign constraints:

- Do not use green as a product or system status semantic on redesigned analytical pages.
- Use white or neutral emphasis for active/current/selected state and the rare filled primary action.
- Use Breeze Blue and Twilight only as rare illustrative or informational accents, not as default action or navigation colors.
- Use Sunset Orange for material issue or serious risk.
- Use Sunset Soft for watch/caution/partial/evidence required.
- Use white, `#DADBDF`, and neutral gray for aligned, normal, unavailable, completed, read-only, or secondary states.
- Put the page-level status in `VerdictHero`.
- Use row-level status only where a specific metric row needs interpretation.

## Frontend data availability and fallback map

The current frontend can derive display content from existing review state without backend API changes. Availability is based on currently observed frontend state/types, not on generated artifact inspection.

| Route | Hero fields | Evidence summary fields | Matrix/comparison row fields | Source field paths | Fallback when unavailable |
| --- | --- | --- | --- | --- | --- |
| `/diagnosis` | Available: diagnosis headline, primary problem, severity/confidence, boundary. | Available/partial: primary evidence, drivers, x-ray facts, data coverage. | Available: display facts, behavior metrics, advanced metrics, x-ray risk/composition/factor blocks. | `activeReview.reviewSummary.diagnosis`, `primaryProblem`, `problemSeverity`, `problemConfidence`, `xraySummary`, `buildDiagnosisDisplayModel(...)`, `siteExplanation.screens.diagnosis`. | Locked/running/failed states already exist; missing facts should render `Unavailable` or stay in secondary technical details. |
| `/evidence` | Available when full model exists: worst/current stress story and current-portfolio-only boundary. | Available/partial: worst scenario, estimated loss, loss drivers, helped/hurt behavior, evidence quality. | Available when full model exists: synthetic/historical scenarios, contribution rows, hedge gaps, factor attribution, data limitations. | `activeReview.reviewSummary.stressLabModel`, `buildStressStoryViewModel(...)`, `siteExplanation.screens.evidence`; `frontend/data/demo/stress-lab.json` is sample-mode fixture only, not production truth. | Compact saved history may lack full detail; show limited evidence/recovery language instead of inventing scenarios. |
| `/client-fit` | Available/partial: status label/tone, main explanation, diagnostic-only boundary. | Available: mismatch reasons and fit dimensions when Client Fit summary exists. | Available: target rows/check rows with portfolio value, target/profile value, status, explanation. | `activeReview.reviewSummary.clientFit`, `activeReview.clientFitProfile`, `buildClientFitPresentation(...)`, `ClientFitDisplaySummary.target_rows`. | `not_provided` remains a compatibility state; do not fail the route or imply suitability approval. |
| `/hypothesis` | Available: proposed diagnostic test, source problem, hypothesis/test framing. | Available: why this test, success criteria, trade-off to watch, decision boundary. | Not primary pattern; builder state and candidate generation status are secondary. | `activeReview.reviewSummary.launchpadCards`, `recommendedFirstTest`, `suggestedActionPaths`, `builderSetup`, `candidateGeneration.successCriteria`, `candidateGeneration.tradeoffToWatch`, `hypothesisScreenModel`. | If live lineage is stale or setup is unavailable, preserve existing blocked/recovery state and ask for a new diagnosis. |
| `/comparison` | Available when comparison matches selected candidate: outcome summary plus candidate boundary. | Available: improved/worsened/neutral/unclear lists, warnings, evidence quality, materiality. | Available: `metrics`, current/candidate/change/direction rows, turnover, estimated cost, allocations. | `activeReview.comparisonResult.summary`, `metrics`, `improved`, `worsened`, `neutral`, `unclear`, `warnings`, `evidenceQuality`, `turnover`, `estimatedCost`, `candidateBoundary`, `clientFit`. | If comparison is absent or mismatched with the selected candidate, keep mismatch/generate-comparison state visible. |
| `/verdict` | Available when verdict matches selected candidate: headline, decision status, confidence, boundary note. | Available: key evidence, rationale/explanation, limitations, evidence used, what would change verdict. | Available: selected verdict metrics, monitoring trigger, action framing, confidence/evidence quality. | `activeReview.verdictResult.headline`, `decisionStatus`, `confidence`, `explanation`, `boundaryNote`, `keyEvidence`, `metrics`, `limitations`, `monitoringTrigger`, `actionFraming`, `whatWouldChangeVerdict`, `clientFit`. | If verdict is absent, insufficient, failed, or stale, use existing empty/mismatch states and avoid final decision language. |
| `/report` | Available after report generation: title, subtitle, boundary. | Available: narrative sections, evidence used, warnings, unavailable evidence, next observation. | Not a full matrix page; selected evidence only. | `activeReview.reportResult.title`, `subtitle`, `sections`, `evidenceUsed`, `unavailableEvidence`, `warnings`, `nextObservation`, `boundaryNote`, plus generated `report_display_model` adapter in `ReportScreen`. | If report is blocked by missing/stale comparison or verdict, keep current blocker message and do not duplicate all metrics. |

## Missing or constrained data

These are frontend constraints for the redesign. They are not backend requests for this work:

- Some saved browser states are compact history and do not include full Stress Lab scenario detail. The redesigned UI must show `Unavailable` or a recovery/rerun explanation rather than inventing detail.
- Some routes can be locked, read-only, sample-mode, or stale-lineage. The redesign must preserve current locked/empty/recovery behavior.
- Comparison and verdict results can be mismatched with the currently selected candidate. The redesign must keep lineage and mismatch warnings visible.
- Candidate metrics may be unavailable when candidate generation failed or was not run. Metric Matrix rows must omit, mark `Unavailable`, or explain the missing value.
- Client Fit can be `not_provided`; this is a compatibility state, not a failure.
- Evidence quality may be limited or partial. The UI should label that limitation instead of converting it into a green/positive pass.

## Design constraints confirmed for later phases

The following decisions are locked for the first redesign implementation pass:

1. Analytical pages use a clean top: compact step context only, no full top stepper.
2. A strict shared `VerdictHero` becomes the primary page message pattern.
3. Page-level status lives in `VerdictHero`; local statuses live only in Metric Matrix rows when needed.
4. Metric Matrix favors high transparency, with expanded rows instead of card overload.
5. Metric Matrix uses hybrid ordering: stable groups, with the most material/problematic rows first inside each group.
6. Green is removed from product and system status semantics on redesigned analytical pages.
7. Sidebar remains visible as a quiet navigator.
8. Hypothesis page explains the diagnostic test and success criteria before builder controls.
9. Comparison uses outcome + boundary framing.
10. Verdict uses a cautious diagnostic interpretation and never trade-advice language.

## Phase 0 acceptance status

- Covered routes and current components are listed.
- Required display data is mapped to existing frontend state where available.
- Missing display data is documented as a frontend constraint.
- No backend behavior, formulas, APIs, optimizer logic, candidate generation, or stress calculations are changed by this inventory.
