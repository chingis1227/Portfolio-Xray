# Adapter Architecture Plan — Session 8

Status: **Session 8 audit / architecture plan** for `docs/exec_plans/2026-06-10_product_code_design_synchronization_plan.md`.

Scope: this document audits current frontend adapter responsibilities and defines the later refactor boundary. It does **not** change frontend runtime code, backend code, JSON schemas, generated outputs, routes, tests, branches, commits, or pushes.

Related contracts:

- `docs/contracts/PRODUCT_FLOW_CONTRACT.md`
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`
- `docs/contracts/SCREEN_CONTRACTS.md`
- `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`
- `docs/contracts/QA_CONTRACT.md`
- `docs/contracts/DOC_SYNC_CONTRACT.md`

## Executive summary

`frontend/lib/reviewState.tsx` is currently both the active-review state store and a broad presentation adapter. It owns browser storage, run status, journey flags, compact summaries, stale downstream cleanup, API-stage result recording, diagnosis/X-Ray mapping, evidence summary mapping, Launchpad/Builder compaction, comparison summary mapping, verdict summary mapping, and many fallback display helpers.

That concentration is risky because changes for one screen can accidentally change another screen, backend/internal language can leak through generic helpers, stale candidate/comparison/verdict handling is hard to reason about, and the file is too broad to test or review as one unit. The later implementation direction should keep review lifecycle and lineage centralized, but split screen-specific artifact-to-screen mapping into small adapters or screen models.

No implementation should happen from this Session 8 document unless the user explicitly starts a later implementation session.

## Evidence reviewed

Read-only inspection covered:

- `frontend/lib/reviewState.tsx`
- `frontend/lib/displayLabels.ts`
- `frontend/lib/types.ts`
- `frontend/lib/journey.ts`
- `frontend/app/diagnosis/page.tsx`
- `frontend/app/evidence/page.tsx`
- `frontend/app/hypothesis/page.tsx`
- `frontend/app/comparison/page.tsx`
- `frontend/app/verdict/page.tsx`
- `frontend/app/report/page.tsx`
- relevant components under `frontend/components/diagnosis/`, `frontend/components/evidence/`, `frontend/components/hypothesis/`, `frontend/components/comparison/`, `frontend/components/verdict/`, and `frontend/components/report/`
- run-local lineage API references under `frontend/app/api/portfolio/*` only as context for `reviewId` and downstream artifact recovery boundaries

Targeted evidence commands used during the audit:

    rg -n "^(export (type|interface|const|function)|function |const |type |interface )" frontend\lib\reviewState.tsx
    rg -n "reviewState|displayLabels|from \"@/lib/types\"|from \"@/lib/journey\"|useReviewState|buildDiagnosisFromReview|buildCompactReviewSummary|normalizeDisplay|journeySteps|buildJourneySteps" frontend\app frontend\components frontend\lib -g "*.ts" -g "*.tsx"
    rg -n "localStorage|pmri\.activeReview|reviewId|review_id|selectedCardId|candidateId|comparisonMatchesCandidate|verdictMatchesCandidate|stale|lineage|recover|downstream|recordBuilderSetup|recordCandidateGeneration|recordComparisonResult|recordVerdictResult" frontend\lib\reviewState.tsx frontend\app\api\portfolio frontend\app frontend\components -g "*.ts" -g "*.tsx"

## Current responsibility map

### `frontend/lib/reviewState.tsx`

Current responsibilities observed:

1. Defines core frontend state types: `ReviewHolding`, `ReviewResult`, run mode/status, `CandidateGenerationSummary`, `ComparisonResultSummary`, `VerdictResultSummary`, `ReviewSummary`, `ActiveReviewState`, and `DiagnosisState`.
2. Owns `ReviewStateProvider`, `useReviewState`, browser hydration, and the active review context.
3. Owns browser storage keys: `pmri.activeReview.v2`, legacy `pmri.activeReview.v1`, and legacy raw review cleanup under `pmri.reviewResult.*`.
4. Stores only compact active review state and explicitly does not persist raw review JSON as active browser truth.
5. Cleans and normalizes persisted state with `cleanReviewState`.
6. Enforces some downstream lineage gates: candidate must match Builder card, comparison must match generated candidate, verdict must match generated candidate, and comparison readiness requires usable metrics.
7. Builds journey flags from active review booleans.
8. Records stage results from frontend API flows: Builder prepare, candidate generation, comparison generation, and verdict generation.
9. Compacts real diagnosis output into `ReviewSummary`, including X-Ray summary, evidence summary, problem fields, Launchpad fields, Builder setup, output paths, and storage metadata.
10. Maps raw `portfolio_xray`, `stress_report`, `problem_classification`, `candidate_launchpad`, `portfolio_alternatives_builder`, `current_vs_candidate`, and `decision_verdict` structures into UI-shaped summaries.
11. Provides many formatting and fallback helpers, including percent formatting, unknown handling, verdict wording, comparison dimension mapping, X-Ray labels, hidden risk labels, weakness labels, evidence lines, and holding classification labels.

Why this is a monolith risk:

- It mixes state lifecycle, artifact parsing, screen presentation wording, lineage policy, and storage hygiene in one large file.
- The same helper layer can affect Diagnosis, Hypothesis, Comparison, Verdict, and Report behavior, so a localized copy or adapter fix may create cross-screen regressions.
- Some screen-specific choices are hard-coded centrally even though the owning screen contract is screen-specific. Examples include verdict headlines/action framing, comparison summary rows, and X-Ray section labels.
- It is harder to test pure artifact mapping because the mapping functions are embedded near React provider state and browser storage concerns.
- It encourages screens to consume `ActiveReviewState` directly and then duplicate or patch state decisions locally, especially in `/hypothesis`, `/comparison`, `/verdict`, and `/report`.

### `frontend/lib/displayLabels.ts`

Current responsibilities observed:

1. Contains shared regex replacement rules and exact-label mappings.
2. Exports `normalizeDisplayLabel`, `formatUnknownValue`, `normalizeDisplaySentence`, `evidenceQualityLabel`, `evidenceTone`, `riskSeverityLabel`, `riskSeverityTone`, and `displayTitleLabel`.
3. Is already used by Diagnosis, Stress, Hypothesis, Comparison, Verdict, metrics, and `reviewState.tsx`.

Required role:

- Keep it as the shared translation boundary for backend/internal vocabulary, raw ids, filenames, enum-like strings, unknown values, evidence quality, severity, and safe title/sentence casing.
- Do not let it become a state machine, API layer, artifact parser, route unlock engine, or calculation layer.
- Treat it as product-language normalization only. If a future adapter needs to decide whether a comparison is stale or a verdict is usable, that belongs in state/screen adapters, not in `displayLabels.ts`.

### `frontend/lib/types.ts`

Current responsibilities observed:

1. Defines small shared UI types: `StatusTone`, `JourneyStepStatus`, `JourneyStep`, `Metric`, `EvidenceItem`, `Holding`, `Hypothesis`, and `ComparisonMetric`.
2. Is imported by `reviewState.tsx`, `journey.ts`, and UI components.

Required role:

- Keep generic, product-facing UI primitives here.
- Do not copy backend JSON schemas into this file.
- Screen-specific models should live beside the future adapter for that screen, or in a dedicated `frontend/lib/screenModels/*` area, and should import shared primitives from `types.ts`.
- If shared primitives grow, they must remain stable display contracts such as `Metric`, `StatusTone`, or `EvidenceItem`, not raw artifact contracts such as `decision_verdict.json` rows.

### `frontend/lib/journey.ts`

Current responsibilities observed:

1. Defines the current route order: Input, Diagnosis, Stress Lab, Hypothesis, Comparison, Verdict, Report.
2. Defines `JourneyFlags`, `JourneyStepWithStatus`, and route unlock helpers.
3. Converts central flags into layout/sidebar/top-progress states.

Required role:

- Keep route metadata and pure route-unlock functions here.
- Do not parse artifacts, inspect localStorage, call APIs, infer candidates, or know backend artifact filenames.
- Journey flags should remain derived from central active-review lifecycle state, not from screen-specific adapters scanning data independently.
- Adding a Candidate route, Monitoring route, or hidden advanced route requires contract updates before code changes.

## What should remain centralized

The following must stay centralized in or near `reviewState.tsx`:

1. `ReviewStateProvider` and `useReviewState`.
2. Active review identity: `reviewId`, run mode, run status, submitted state, and review error state.
3. Browser storage versioning, hydration, compact persisted state, and cleanup of legacy raw review storage.
4. The rule that browser storage stores compact state only and does not make raw JSON the source of truth.
5. Lifecycle flags used by `journey.ts`: diagnosis, evidence, improvement paths, candidate, comparison, and verdict readiness.
6. Same-run lineage gates:
   - Builder setup must match the active selected Launchpad card.
   - Candidate generation must match the active Builder setup.
   - Comparison must match the active selected card and generated candidate.
   - Verdict must match the active selected card and generated candidate.
   - Report must be based on the active verdict context.
7. Stage result recording entrypoints exposed to pages: `recordBuilderSetup`, `recordCandidateGeneration`, `recordComparisonResult`, `recordVerdictResult`.
8. Reset behavior that clears or invalidates downstream candidate/comparison/verdict/report readiness when upstream selection, candidate, or review identity changes.

Centralized code should answer: "What is the active review, what stage is it in, and which downstream evidence is still current..."

Centralized code should not answer: "How exactly should the Diagnosis screen phrase the risk-budget insight..." or "Which rows should the Comparison screen render..."

## What should split into screen-specific adapters or models

Future implementation sessions should split artifact-to-screen mapping into pure, testable modules. Suggested shape:

| Future adapter/model | Primary inputs | Primary output | Notes |
| --- | --- | --- | --- |
| `xrayDiagnosisAdapter` | `ActiveReviewState`, compact `reviewSummary`, `portfolio_xray`, `problem_classification` | `DiagnosisScreenModel` / `XRayScreenModel` | Can be extracted from `buildDiagnosisFromReview`, `buildDiagnosisFromRealResult`, and `compactXRaySummary`. |
| `stressLabAdapter` | `stress_report`, optional X-Ray confirmation context | `StressLabModel` | `frontend/components/evidence/stressLabModel.ts` is already close to this boundary; future work should keep it pure and avoid duplicating stress mapping in `reviewState.tsx`. |
| `hypothesisAdapter` | `problem_classification`, `candidate_launchpad`, `portfolio_alternatives_builder`, active selection, candidate generation summary | `HypothesisScreenModel` | Should absorb the many helper functions now embedded in `frontend/app/hypothesis/page.tsx`. |
| `comparisonAdapter` | active candidate summary, `current_vs_candidate`, comparison API result, lineage info | `ComparisonScreenModel` | Should distinguish no candidate, comparison not run, unavailable metrics, usable comparison, stale comparison, and failed comparison. |
| `verdictAdapter` | active candidate summary, active comparison summary, `decision_verdict`, lineage info | `VerdictScreenModel` | Should normalize verdict ids into non-binding states and treat evidence-insufficient/no-trade as valid outcomes. |
| `reportAdapter` | `ai_commentary_context`, active verdict/comparison/diagnosis/stress/hypothesis summaries, optional `what_changed_summary` | `ReportScreenModel` | Should hide grounding package internals and expose only supported report preview sections. |

These adapters should be pure functions where possible. They should accept data and return screen-ready models without using React hooks, localStorage, browser APIs, fetch, or route navigation.

## Screen-specific boundaries

### X-Ray / Diagnosis

Boundary:

- Owns current-portfolio diagnosis presentation before any candidate test.
- Primary inputs are compact `reviewSummary`, `portfolio_xray`, and the diagnosis bridge from `problem_classification`.
- May show X-Ray composition, risk profile, factor exposure, hidden risks, risk budget, weakness map, evidence quality, and next diagnostic step.
- May use Stress only as already-grounded cross-reference when available, not as a substitute for X-Ray.

Must not:

- Show candidate, comparison, verdict, optimizer, health-score, or full action-plan concepts as the primary diagnosis answer.
- Treat root legacy X-Ray artifacts as current portfolio truth.
- Turn pre-stress weakness into a rebalance instruction.
- Surface raw block ids, field paths, or backend filenames in primary copy.

Future adapter acceptance:

- `DiagnosisScreenModel` can be built without React context or localStorage.
- Missing X-Ray/problem evidence renders a partial/blocked diagnosis state, not invented conclusions.
- Product labels follow `PRESENTATION_LANGUAGE_RULES.md`.

### Stress Test Lab

Boundary:

- Owns current-portfolio stress evidence and X-Ray weakness confirmation.
- Primary input is same-review `stress_report`.
- `frontend/components/evidence/stressLabModel.ts` already acts as a stress adapter and should remain the main extraction point.

Must not:

- Create candidate, comparison, or verdict states.
- Present mandate pass/fail, `DIAG_*`, `loss_ok`, or raw scenario ids as Core MVP conclusions.
- Use root legacy stress artifacts or stale generated sidecars as active truth.

Future adapter acceptance:

- `StressLabModel` is produced from `stress_report` with translated scenario/protection labels.
- Missing stress detail produces a clear limited-evidence state.
- Stress output remains current-portfolio-only and routes to Hypothesis only as evidence.

### Hypothesis Builder

Boundary:

- Owns Problem Classification → Candidate Launchpad → selected test setup → explicit candidate generation.
- Primary inputs are `problem_classification`, `candidate_launchpad`, `portfolio_alternatives_builder`, active selected card, and same-run candidate generation result.
- Monitoring/data-quality cards are valid paths but do not generate candidates.

Must not:

- Display an optimizer zoo, full backend method catalog, disabled backend method cards, or raw `card_type` / `source_card_id` / `can_generate_candidate` booleans.
- Treat a generated candidate as a recommendation.
- Unlock Comparison from stale candidate attempts.

Future adapter acceptance:

- `HypothesisScreenModel` exposes recommended test, available test paths, selected setup, generation state, candidate preview, and comparison CTA state.
- Selecting a different hypothesis invalidates downstream candidate/comparison/verdict/report readiness unless a same-card candidate is regenerated.
- The adapter hides backend ids except where a diagnostic/operator detail view is explicitly approved.

### Current vs Candidate Comparison

Boundary:

- Owns trade-off comparison between the current portfolio and one active generated test candidate.
- Primary inputs are same-run `candidate_generation` and same-run `current_vs_candidate`.

Must not:

- Show fake rows filled with `n/a`, blank placeholders, or "winner" language.
- Use batch rankings, full candidate arena, or stale comparisons as current evidence.
- Issue or imply the final verdict.

Future adapter acceptance:

- `ComparisonScreenModel` distinguishes at least these states: no active candidate, comparison ready to run, comparison running, comparison unavailable/failed, partial metrics, usable comparison, stale comparison ignored.
- Usable comparison requires matching `selectedCardId` and `candidateId`.
- Verdict CTA appears only when current comparison evidence is usable or when a documented evidence-insufficient verdict path is supported.

### Decision Verdict

Boundary:

- Owns non-binding decision-support verdict after active comparison evidence.
- Primary inputs are same-run `decision_verdict`, same-run comparison, and same-run candidate generation.

Must not:

- Expose raw verdict ids as primary labels.
- Present `selected_candidate` as execution, trade, or recommendation.
- Treat no-trade, keep-current, no-material-rebalance, evidence-insufficient, candidate failed, or test-another outcomes as errors.
- Use stale verdicts after a candidate or selected hypothesis changes.

Future adapter acceptance:

- `VerdictScreenModel` maps backend verdict statuses into approved product states.
- Boundary note always says decision support only.
- Report CTA is available only for active matching verdict context.
- Evidence-insufficient and no-trade outcomes render professionally and do not look broken.

### Report / AI Commentary Grounding

Boundary:

- Owns grounded report preview based on active diagnosis, stress, hypothesis, comparison, and verdict evidence.
- Primary input is same-run report/grounding context plus active screen summaries; optional `what_changed_summary` remains a short deferred-monitoring note.

Must not:

- Expose `ai_commentary_context.json`, raw grounding package names, `does_not_call_llm`, source field paths, `No PDF generation`, or prototype/operator wording in primary copy.
- Claim the AI or LLM decided anything.
- Generate ungrounded sections from missing evidence.
- Treat PDF/export absence as product failure.

Future adapter acceptance:

- `ReportScreenModel` includes only supported sections and marks partial/unavailable sections plainly.
- Report generation requires active verdict context.
- Monitoring remains deferred unless a future contract promotes it.

## Stale, lineage, and localStorage boundaries

1. Browser storage is a convenience cache, not a backend artifact source of truth.
2. `pmri.activeReview.v2` should keep compact state only; raw JSON must not be relied on as persisted primary UI truth.
3. Recovery of a saved review may restore current portfolio diagnosis/launchpad/builder context, but candidate/comparison/verdict/report readiness must remain cleared unless regenerated or verified by same-run stage APIs.
4. Screen adapters must not scan disk, generated folders, or `output_manifest.json` and infer current downstream state by file existence alone.
5. Same-run identity must be carried through `reviewId`.
6. Same selected hypothesis must be carried through `selectedCardId`.
7. Same generated candidate must be carried through `candidateId`.
8. A stale downstream result should become a visible user state such as "Previous result ignored because it is outdated", not a silent unlock and not a technical error.
9. Sample/demo state must be explicit and must not create fake review lineage.
10. Root legacy policy artifacts and generated sidecars remain outside active frontend truth unless a task explicitly targets legacy or export artifacts.

## Forbidden backend-language boundary

Screen adapters and components must not show backend artifact names, JSON filenames, raw enum ids, field paths, raw booleans, raw `n/a`, operator run folder names, or internal implementation copy as primary UI language.

Use `displayLabels.ts` for shared translations, but keep screen-specific wording in the owning adapter or component when the state is domain-specific. For example, "Evidence insufficient for a verdict" belongs to the Verdict adapter, while turning `decision_verdict.json` into "Decision Verdict" belongs to the shared display-label layer.

The forbidden-language source of truth remains `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`.

## Incremental refactor sequence for later sessions

Do not perform these steps during Session 8. They are a safe future sequence once implementation is explicitly approved.

1. Add narrow characterization tests or fixtures for the current adapter outputs before moving code. Start with pure functions where possible and do not run `.next` writers concurrently.
2. Define small screen-model types for X-Ray/Diagnosis, Hypothesis, Comparison, Verdict, and Report. Keep shared primitives in `frontend/lib/types.ts`.
3. Extract X-Ray/Diagnosis pure mapping from `reviewState.tsx` into a diagnosis adapter. Keep the exported model shape stable for the Diagnosis page.
4. Keep `stressLabModel.ts` as the Stress adapter and remove any duplicate stress evidence summary logic only after tests prove equivalent screen behavior.
5. Extract Hypothesis helpers from `frontend/app/hypothesis/page.tsx` into a pure Hypothesis adapter, then let the page focus on UI state, API calls, and rendering.
6. Extract Comparison state derivation from `frontend/app/comparison/page.tsx` and `reviewState.tsx` into a Comparison adapter.
7. Extract Verdict state derivation and safe verdict wording into a Verdict adapter.
8. Extract Report preview/grounding mapping from `frontend/app/report/page.tsx` into a Report adapter.
9. Slim `reviewState.tsx` to provider, storage, lifecycle, stage recording, compact persisted state, and lineage gates.
10. Run the checks required by `docs/contracts/QA_CONTRACT.md` for the changed scope, including forbidden-term scans and visual QA when screen output changes.
11. Update owning docs through `docs/contracts/DOC_SYNC_CONTRACT.md` before reporting implementation complete.

## Acceptance criteria for future implementation sessions

Future code sessions that apply this plan should meet these criteria:

- `reviewState.tsx` no longer owns screen-specific presentation mapping beyond compact persisted summaries and lifecycle state.
- Each implemented screen adapter has a small, named, pure function that converts raw/compact evidence into a screen model.
- Screen models expose product states, not backend schema copies.
- Stale candidate/comparison/verdict/report evidence cannot unlock downstream screens.
- Same `reviewId`, `selectedCardId`, and `candidateId` lineage is enforced before downstream CTAs appear.
- `displayLabels.ts` stays a translation layer and does not gain API, storage, route, or artifact parsing responsibilities.
- `types.ts` contains shared UI primitives only; screen-specific types are colocated with their adapters.
- `journey.ts` remains route metadata and pure unlock helpers only.
- X-Ray/Diagnosis, Stress, Hypothesis, Comparison, Verdict, and Report boundaries match `docs/contracts/SCREEN_CONTRACTS.md`.
- Primary UI avoids forbidden backend/internal terms from `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`.
- No generated outputs are treated as source.
- Docs impact is checked and updated or explicitly waived under `docs/contracts/DOC_SYNC_CONTRACT.md`.

## Session 8 outcome

Session 8 produced this plan and updated the active ExecPlan. No frontend implementation/refactor was started. Session 9 must not start unless the user explicitly asks for it.
