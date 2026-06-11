# Post-Stress Frontend Flow Alignment Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document is maintained under `PLANS.md` from the repository root. It saves the full implementation plan requested for the Portfolio MRI frontend post-Stress flow alignment. Session 00 is audit and planning only. Later sessions must implement small, reviewable frontend-only changes.

## Purpose / Big Picture

Portfolio MRI is an Investment Decision Room. After Stress Lab, the frontend should guide a user through a professional investment decision-support flow instead of exposing backend architecture. The target user-visible journey is: Stress Lab, Problem Classification, Hypothesis Builder, Test Setup, Generate Candidate, Comparison, Verdict, and Report.

After the full plan is implemented, the user should see Step 4 as a clear Hypothesis Builder that starts from the portfolio problem classification, Step 5 as a comparison page that never shows fake unavailable metric tables, and Step 6 as a professional verdict page where no-trade and evidence-insufficient outcomes look intentional rather than like pipeline errors.

This is strictly frontend presentation, UI logic, copy, naming, and hierarchy cleanup. It must not change backend calculations, API contracts, JSON artifact structures, candidate generation logic, comparison calculation logic, decision verdict logic, runtime modes, routes unless absolutely necessary, existing backend outputs, or existing stress/diagnosis/candidate/comparison/verdict artifacts.

## Progress

- [x] (2026-06-10) Session 00 audit completed without code changes. Relevant Step 4-6 files, shared state files, label helpers, and raw backend term leak points were identified.
- [x] (2026-06-10) Full implementation plan saved in `docs/exec_plans/2026-06-10_post_stress_frontend_flow_alignment_plan.md`.
- [x] (2026-06-10) Session 1: User-facing naming and copy cleanup foundation.
- [x] (2026-06-10) Session 2: Add Problem Classification as the first visible section in Step 4.
- [x] (2026-06-10) Session 3: Rebuild Hypothesis cards and Test Setup.
- [x] (2026-06-10) Session 4: Add or centralize presentation label mapping.
- [x] (2026-06-10) Session 5: Fix Comparison page states.
- [x] (2026-06-10) Session 6: Fix Verdict page states.
- [x] (2026-06-10) Session 7: Cross-screen cleanup and final QA.

## Surprises & Discoveries

- Observation: The repository already has unrelated dirty working-tree changes before this plan file was created.
  Evidence: `git status --short` showed modified files including `AGENTS.md`, several `frontend/components/evidence/*` files, `frontend/app/evidence/page.tsx`, `frontend/lib/journey.ts`, and untracked documentation/components. Later sessions must not revert or stage unrelated changes.

- Observation: Step 4 currently contains multiple user-facing backend/product-internal terms.
  Evidence: `frontend/app/hypothesis/page.tsx` includes `Real Candidate Launchpad`, `Builder setup`, `Candidate Launchpad card`, `outputs.candidate_launchpad`, `Card type`, `Source problem`, `Default method`, and boolean `true`/`false` display.

- Observation: A presentation label helper already exists.
  Evidence: `frontend/lib/displayLabels.ts` contains `normalizeDisplayLabel`, `normalizeDisplaySentence`, evidence-quality helpers, and exact/replacement label maps. Later sessions should extend this instead of creating a parallel label system unless there is a clear reason.

- Observation: Running `next build` concurrently with the frontend smoke test can race on `.next` output files.
  Evidence: The first Session 07 parallel validation attempt returned `PageNotFoundError: Cannot find module for page: /_document`; rerunning `npm.cmd run build` by itself passed.

## Decision Log

- Decision: Treat the work as frontend-only presentation and readiness-state cleanup.
  Rationale: The user explicitly said not to change backend calculations, API contracts, JSON artifact structures, candidate generation logic, comparison logic, verdict logic, routes unless absolutely necessary, or runtime modes.
  Date/Author: 2026-06-10 / Codex.

- Decision: Save the plan as a checked-in ExecPlan-style Markdown file under `docs/exec_plans/`.
  Rationale: The task is multi-session and risky enough to need a durable plan; `AGENTS.md` and `PLANS.md` require complex work to use checked-in ExecPlans under this directory.
  Date/Author: 2026-06-10 / Codex.

- Decision: Session 00 stops after audit and plan persistence.
  Rationale: The user explicitly clarified: finish Session 00, stop, say so, and save the whole plan as Markdown. No implementation sessions should be started in this turn.
  Date/Author: 2026-06-10 / Codex.

## Outcomes & Retrospective

Session 00 outcome: The current frontend implementation was audited, relevant files were identified, and the complete multi-session implementation plan was saved in this file. No Step 4-6 frontend code has been changed yet. The next work session should start with Session 1 and make only naming/copy foundation changes.

Session 01 outcome: Step 4 user-facing naming was changed from Candidate Launchpad framing to Hypothesis Builder / Test setup language, the primary Step 4 CTA now says Generate candidate, and the shared page-header boundary note no longer mentions trade execution. Backend fields, API contracts, routes, and calculation logic were not changed.

Session 02 outcome: Step 4 now renders a `Problem Classification` section before hypothesis cards and test setup. The section reads `outputs.problem_classification` when present and falls back to the compact review summary fields when only partial diagnosis data is available. It shows the primary diagnosis/status, explanation, key evidence when available, confidence/materiality/actionability, recommended next test, and decision boundary without changing backend artifacts, API contracts, routes, candidate generation, comparison, or verdict logic.

Session 03 outcome: Step 4 hypothesis cards now present hypothesis, test type, why this test, suggested methods, success criteria, trade-off to watch, and decision boundary. The Test setup panel no longer exposes normal user-facing raw backend fields such as card type, source problem, default method, raw booleans, or setup-only internals; it now shows goal, suggested method, constraint preset, success criteria, trade-off, decision boundary, and candidate generation readiness with a clear unavailable state. The primary generation CTA remains `Generate candidate`. Backend artifacts, API contracts, routes, candidate generation, comparison, and verdict logic were not changed.

Session 04 outcome: `frontend/lib/displayLabels.ts` now centralizes presentation mappings for candidate methods, diagnostic problem IDs, comparison/verdict unavailable reason codes, boolean-like values, and `n/a`-style missing values. Step 4-6 presentation code now routes normal UI values through shared display/sentence formatting so raw enum IDs, JSON artifact filenames, and raw availability booleans are less likely to leak into the user-facing flow. Backend artifacts, API contracts, routes, candidate generation, comparison, and verdict logic were not changed.

Session 05 outcome: Step 5 now distinguishes candidate-not-generated, comparison-metrics-unavailable, and valid-comparison states. The page no longer renders a detailed comparison table when the active candidate is missing, not compare-ready, or has no usable comparison metrics; it instead shows clear next steps back to Hypothesis Builder. Valid comparisons keep the trade-off summary first, then the detailed table, success-criteria evaluation, turnover/cost, warnings, and Continue to Verdict. Backend artifacts, API contracts, routes, candidate generation, comparison calculations, and verdict logic were not changed.

Session 06 outcome: Step 6 now distinguishes verdict-unavailable, evidence-insufficient, and valid-verdict states. The unavailable state explains that a valid Current vs Candidate Comparison is required and routes the user back to Hypothesis Builder. Evidence-insufficient is shown as a professional no-decision outcome with why/next-step/decision-boundary copy instead of a backend failure. Verdict labels, confidence/status text, and stored verdict summaries now use presentation-safe formatting, and recording a verdict no longer forces `comparisonReady` to true when the existing comparison is not actually ready. Backend artifacts, API contracts, routes, candidate generation, comparison calculations, and verdict calculation logic were not changed. Validation passed from `frontend/`: `npm.cmd run typecheck`, `npm.cmd run build`, `npm.cmd run test:api`, and `npm.cmd run test:smoke`.

Session 07 outcome: Step 4-6 received a final presentation-safety pass. Step 4 now normalizes backend error text before display, sanitizes the hidden diagnosis-source text, and displays generated candidate identifiers through presentation labels. Step 5 no longer uses `implementation order` copy and now consistently names the page `Current vs Candidate Comparison`. Shared display-label normalization now catches remaining launchpad/setup/backend artifact terms if they arrive from backend messages. No backend calculations, API contracts, routes, JSON structures, candidate generation logic, comparison logic, or verdict logic were changed. Validation from `frontend/`: `npm.cmd run typecheck` passed; `npm.cmd run test:api` passed; `npm.cmd run test:smoke` passed; `npm.cmd run build` first failed only while run concurrently with smoke because of a `.next` race, then passed when rerun alone. A targeted `rg` pass over Step 4-6 UI files found no banned presentation terms from the Session 07 checklist; internal `reviewState.tsx` stage/JSON keys were intentionally preserved.

## Context and Orientation

Portfolio MRI is currently a Python-backed portfolio diagnostics and investment decision-support system with a Next.js/React frontend under `frontend/`. The user-facing product is diagnosis-first and current-portfolio-first. It is not an optimizer cockpit, trading app, crypto terminal, dashboard, or black-box advisor.

The relevant frontend flow is the 7-step journey: Portfolio, X-Ray, Stress Lab, Hypothesis, Comparison, Verdict, Report. Navigation state is defined in `frontend/lib/journey.ts` and displayed through `frontend/components/layout/Sidebar.tsx` and `frontend/components/layout/TopJourneyProgress.tsx`.

The relevant post-Stress screens are:

- `frontend/app/hypothesis/page.tsx`: Step 4 page. It reads the review state, maps candidate launchpad cards into `Hypothesis` objects, handles test setup preparation through `/api/portfolio/builder/prepare`, and generates one candidate through `/api/portfolio/candidate/generate`.
- `frontend/components/hypothesis/HypothesisCard.tsx`: Card presentation for a hypothesis/test path.
- `frontend/components/hypothesis/HypothesisBuilderPanel.tsx`: Existing sample-mode builder panel.
- `frontend/app/comparison/page.tsx`: Step 5 page. It runs comparison through `/api/portfolio/comparison/generate` and displays trade-off summary plus detailed table when available.
- `frontend/components/comparison/CandidateComparisonPanel.tsx`: Detailed comparison table.
- `frontend/components/comparison/TradeoffSummary.tsx`: Top-level comparison summary.
- `frontend/app/verdict/page.tsx`: Step 6 page. It runs verdict generation through `/api/portfolio/verdict/generate` and displays verdict output.
- `frontend/components/verdict/VerdictPanel.tsx`: Main verdict display.
- `frontend/lib/reviewState.tsx`: Shared browser-side review state and summary mapping from backend responses to frontend-friendly summaries.
- `frontend/lib/displayLabels.ts`: Existing presentation label and sentence normalization helper.
- `frontend/lib/types.ts`: Shared frontend types including `Hypothesis`, `ComparisonMetric`, and `Metric`.
- `frontend/components/layout/PageHeader.tsx`: Common page hero/header. Session 01 replaced the default boundary note that previously mentioned trade execution.

Important product definitions for later sessions:

Problem Classification means the main issue or status of the current portfolio. Hypothesis means what should be tested next. Test Setup means how exactly the hypothesis will be tested. Candidate Generation means creating one diagnostic candidate after explicit user action. Comparison means showing what improves, worsens, remains unclear, and what it costs. Verdict means whether there is enough evidence to act, not act, test another candidate, or declare evidence insufficient.

Important product boundaries:

A candidate is not a recommendation. A hypothesis is not a portfolio. Test setup is not a rebalance instruction. A candidate is generated only after explicit user action. Comparison does not select a winner. Verdict is not a trading instruction. No-trade is a valid professional outcome. Evidence insufficient is a valid professional outcome. AI and UI commentary explain but do not decide.

## Full Plan of Work

### Session 0 — Audit and implementation plan only

Goal: Inspect the current frontend implementation for Step 4 Hypothesis, Step 5 Comparison, and Step 6 Verdict. Do not change code in this session.

Find relevant route/page files, relevant components, presentation/data mapping files, review state files, labels/copy helpers, status badge components, comparison/verdict data handling, and where raw backend terms reach the UI.

Output a short implementation plan with files involved, current problems by screen, proposed sessions, expected risk, what each session will change, and validation commands. Do not modify code and do not commit. In this repository, the user subsequently requested saving the whole plan as Markdown, so this plan file is the only Session 00 repository mutation.

Session 00 audit findings:

Primary Step 4-6 files:

- `frontend/app/hypothesis/page.tsx`
- `frontend/components/hypothesis/HypothesisCard.tsx`
- `frontend/components/hypothesis/HypothesisBuilderPanel.tsx`
- `frontend/app/comparison/page.tsx`
- `frontend/components/comparison/CandidateComparisonPanel.tsx`
- `frontend/components/comparison/TradeoffSummary.tsx`
- `frontend/app/verdict/page.tsx`
- `frontend/components/verdict/VerdictPanel.tsx`

Shared state, labels, and navigation files:

- `frontend/lib/reviewState.tsx`
- `frontend/lib/displayLabels.ts`
- `frontend/lib/types.ts`
- `frontend/lib/journey.ts`
- `frontend/components/layout/PageHeader.tsx`
- `frontend/components/layout/Sidebar.tsx`
- `frontend/components/layout/TopJourneyProgress.tsx`
- `frontend/components/ui/StatusBadge.tsx`
- `frontend/components/ui/MetricCard.tsx`

Tests and validation files:

- `frontend/tests/api-route-tests.cjs`
- `frontend/tests/frontend-smoke-tests.cjs`
- `frontend/package.json`

Current problems by screen:

Step 4 currently shows `Real Candidate Launchpad` as the main title. Problem Classification is not the first visible section. Hypothesis cards and setup panels expose backend/internal terms such as `Candidate Launchpad card`, `Builder setup`, `outputs.candidate_launchpad`, `Card type`, `Source problem`, `Default method`, and boolean `true`/`false`. The CTA says `Test hypothesis`, but the action creates a diagnostic candidate.

Step 5 has an active comparison path, but unavailable states are not precise enough. It can still surface technical phrasing like `current-vs-candidate` and can show metric rows derived from unavailable comparison dimensions with `n/a`, `Unclear`, or raw unavailable reasons.

Step 6 has an active verdict path and some evidence-insufficient support, but unavailable/evidence-insufficient states can still sound like backend/pipeline status. Raw confidence/status identifiers and technical candidate/comparison framing can leak into the normal UI.

### Session 1 — User-facing naming and copy cleanup foundation

Goal: Remove obviously wrong titles and raw product/backend language from the normal UI. This session is copy/naming only and should not rebuild logic.

In `frontend/app/hypothesis/page.tsx`, change the Step 4 hero title from `Real Candidate Launchpad` to `Hypothesis Builder`. Change the subtitle to `Turn the portfolio diagnosis into a testable investment hypothesis.` Change the boundary copy to `No candidate or rebalance recommendation is created until you explicitly generate a candidate.`

Remove or replace user-facing wording: `Real Candidate`, `Candidate Launchpad` as main title, `Launchpad card`, `trade execution`, `no trade execution`, and `Builder setup` as a main user-facing title. Use `Hypothesis Builder`, `Hypothesis test`, `Test setup`, `Reference benchmark test`, `Monitoring path`, and `No candidate or rebalance verdict is created here`.

In `frontend/components/layout/PageHeader.tsx`, replace the default boundary note so it no longer says `trade execution`.

Ensure left navigation and top journey remain: Portfolio, X-Ray, Stress Lab, Hypothesis, Comparison, Verdict, Report.

Validation commands from `frontend/`:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

Commit message:

    Refine post-stress journey naming

### Session 2 — Add Problem Classification as first visible section in Step 4

Goal: Problem Classification must be visible before any hypothesis cards or candidate setup.

Step 4 page structure should become:

1. Problem Classification
2. Recommended Next Test
3. Hypothesis Cards
4. Test Setup
5. Generate Candidate

In `frontend/app/hypothesis/page.tsx`, add a top section named `Problem Classification`. It should use `activeReview.reviewResult.outputs.problem_classification` if available. If only partial data is available, build a clean user-facing fallback from `activeReview.reviewSummary.primaryProblem`, `problemSeverity`, `problemConfidence`, and `suggestedActionPaths`. Do not invent metrics.

The section should show primary diagnosis/status, root-cause explanation, 3-5 key evidence points if available, confidence/materiality/actionability if available, recommended next diagnostic step, and decision boundary.

Use these user-facing examples as copy patterns, adapting only when existing data supports it:

Mixed evidence / no immediate rebalance justified:

    Primary diagnosis: Mixed evidence / no immediate rebalance justified
    Explanation: The current portfolio shows stress weaknesses, but current evidence is not strong enough to justify immediate portfolio change. A simple reference comparison can test whether the current allocation is materially better than basic alternatives.
    Next diagnostic step: Compare current portfolio against simple reference tests: Equal Weight and Risk Parity.
    Decision boundary: This is not a rebalance recommendation. A real decision requires Current vs Candidate Comparison and Decision Verdict.

Weak crisis resilience:

    Primary diagnosis: Weak crisis resilience
    Explanation: The portfolio is vulnerable in severe stress scenarios because losses concentrate in a few positions and helped assets offset only a limited share of losses.
    Next diagnostic step: Test whether a crisis-resilience candidate can reduce worst stress loss, improve offset coverage, and reduce stress loss concentration.

Evidence insufficient:

    Primary diagnosis: Evidence insufficient
    Explanation: The available data is not strong enough to support a reliable candidate test or comparison.
    Next diagnostic step: Resolve data quality before testing candidates.

Do not show raw diagnosis IDs, backend field names, JSON artifact names, or artifact paths. If data is unavailable, show:

    Problem classification unavailable
    The portfolio diagnosis could not be loaded. Continue only after the review outputs are available.

Validation commands from `frontend/`:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

Commit message:

    Add problem classification to hypothesis flow

### Session 3 — Rebuild Hypothesis cards and Test Setup

Goal: Make Step 4 feel like Diagnosis, Next test, Test setup, Generate candidate.

Clean Hypothesis cards. Each card should show title, test type, why this test, suggested methods, success criteria, trade-off to watch, and decision boundary.

Do not show `card_type`, `launch_status`, `method_role`, `source_card`, `source_problem`, `monitor_or_resolve_data`, `setup_only`, `n/a`, `true`, `false`, `outputs`, `artifact`, `backend`, `candidate_launchpad`, `is_rebalance_recommendation`, or `generates_portfolio` in the normal UI.

Example card copy:

    Title: Compare against simple references
    Test type: Reference benchmark test
    Why this test: Checks whether the current portfolio justifies its complexity versus Equal Weight and Risk Parity.
    Suggested methods: Equal Weight, Risk Parity
    Success criteria: The current portfolio should remain competitive on risk-adjusted return, drawdown, stress loss, and risk concentration.
    Trade-off to watch: Avoid unnecessary turnover unless simple references expose a material weakness.
    Decision boundary: This is not a rebalance recommendation.

Monitoring path example:

    Title: Keep current portfolio and monitor
    Test type: Monitoring path
    Why this path: Current evidence does not justify immediate rebalance. Monitor key risks before testing another candidate.
    Monitoring focus: Stress loss, hedge gap, concentration, and data quality.
    Decision boundary: No portfolio change is recommended from this step.

Rename user-facing `Builder setup` to `Test setup`. Before card selection, show `Select a hypothesis to prepare a test setup.` After card selection, show `Test setup prepared`.

The Test Setup panel should show Goal, Suggested method, Constraint preset if available, Success criteria, Trade-off to watch, Decision boundary, and Candidate generation readiness.

The CTA must be `Generate candidate`, not `Test hypothesis`, because the next explicit action creates a diagnostic candidate.

If generation is not possible, show:

    Candidate cannot be generated yet
    Reason: [clean user-facing reason]
    Next step: [select another hypothesis / resolve data quality / adjust setup]

Do not show raw `true`, `false`, or `n/a`.

Validation commands from `frontend/`:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

Commit message:

    Clean hypothesis cards and test setup

### Session 4 — Add or centralize presentation label mapping

Goal: Prevent backend enums and raw values from leaking into UI.

Extend `frontend/lib/displayLabels.ts` rather than creating a parallel helper unless there is a clear reason. Add mappings such as:

- `equal_weight` to `Equal Weight`
- `risk_parity` to `Risk Parity`
- `minimum_variance` to `Minimum Variance`
- `minimum_cvar` to `Minimum CVaR`
- `hrp` to `Hierarchical Risk Parity`
- `maximum_diversification` to `Maximum Diversification`
- `monitor_or_resolve_data` to `Monitor or improve data quality`
- `setup_only` to `Setup only`
- `reference_benchmark_test` to `Reference benchmark test`
- `targeted_hypothesis_test` to `Targeted hypothesis test`
- `mixed_evidence_no_action` to `Mixed evidence / no immediate rebalance justified`
- `evidence_insufficient_data_quality` to `Evidence insufficient due to data quality`
- `current_portfolio_acceptable` to `Current portfolio acceptable with monitoring`
- `weak_crisis_resilience` to `Weak crisis resilience`
- `poor_diversification` to `Poor diversification`
- `high_concentration` to `High concentration`
- `weak_hedge_behavior` to `Weak hedge behavior`
- `duration_rates_vulnerability` to `Duration / rates vulnerability`
- `credit_liquidity_fragility` to `Credit / liquidity fragility`
- `baseline_or_candidate_metric_missing` to `Candidate metric unavailable`
- `no_available_comparison_metrics` to `Comparison metrics unavailable`
- `stale_downstream_artifact_ignored` to `Previous result ignored because it is outdated`
- `true` to `Available`
- `false` to `Not available`
- `n/a` to `Not available yet`

Prefer hiding technical fields completely unless they are user-relevant.

Add a user-facing fallback function, `formatUnknownValue(value)`. If the value is null, undefined, or empty, return `Not available yet`. If the value is snake_case, convert it to readable title case only as a fallback. Never show raw JSON artifact filenames in normal UI.

Apply this mapping to Step 4-6 and relevant `reviewState.tsx` summary construction. Technical/debug values can go into a collapsed `Technical details` section closed by default if needed.

Validation commands from `frontend/`:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

Commit message:

    Add presentation labels for decision flow

### Session 5 — Fix Comparison page states

Goal: Comparison must not show fake comparison tables when no valid candidate or comparison exists.

In `frontend/app/comparison/page.tsx` and `frontend/components/comparison/*`, implement clear states.

State A, candidate not generated:

    Title: Comparison unavailable
    Body: A valid candidate must be generated before Portfolio MRI can compare current vs candidate trade-offs.
    Next step: Return to Hypothesis Builder and generate a candidate.
    CTA: Return to Hypothesis Builder

Do not show a metric comparison table.

State B, candidate generated but metrics unavailable:

    Title: Comparison metrics unavailable
    Body: The candidate exists, but the system does not have enough candidate metrics to compare it against the current portfolio.
    What is missing:
    - Candidate metrics are unavailable
    - Current vs candidate comparison could not be completed
    Next step: Regenerate candidate, adjust setup, or resolve data quality.
    CTA: Return to Hypothesis Builder

Do not show fake rows with `n/a`, `Unclear`, or raw identifiers.

State C, valid comparison available: show Trade-off summary, What improves, What worsens, What remains unclear, What it costs, Success criteria evaluation, Detailed comparison table, Turnover / cost, and Continue to Verdict.

Comparison hero copy:

    This step compares the current portfolio with one generated diagnostic candidate. It does not select a winner or create a rebalance instruction.

Remove raw UI terms: `baseline_or_candidate_metric_missing`, `no_available_comparison_metrics`, `stale_downstream_artifact_ignored`, `current_vs_candidate`, `decision_verdict.json`, `n/a`, and repeated `Unclear` badges when the whole comparison is unavailable.

Use `Not available yet`, `Candidate metric unavailable`, and `Comparison unavailable`.

Validation commands from `frontend/`:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

Commit message:

    Fix comparison readiness states

### Session 6 — Fix Verdict page states

Goal: Verdict must not look like a backend or pipeline error when evidence is insufficient or comparison is unavailable.

In `frontend/app/verdict/page.tsx`, `frontend/components/verdict/VerdictPanel.tsx`, and `frontend/lib/reviewState.tsx`, implement clear verdict states.

State A, valid comparison available: show actual decision-support verdict. Allowed user-facing outcomes include Keep current portfolio, No material rebalance recommended, Rebalance to selected candidate, Test another candidate, Evidence insufficient, and Candidate failed or infeasible.

State B, comparison unavailable:

    Title: Verdict unavailable
    Body: A valid Current vs Candidate Comparison is required before a decision-support verdict can be formed.
    Why: Portfolio MRI cannot determine whether changing the portfolio improves the diagnosed weakness without a valid candidate comparison.
    Next step: Return to Hypothesis Builder and generate a valid candidate.
    CTA: Return to Hypothesis Builder

State C, evidence insufficient:

    Title: Evidence insufficient
    Body: Do not make a portfolio decision from this evidence yet.
    Why: The candidate comparison is incomplete or degraded. Portfolio MRI cannot determine whether the candidate improves the diagnosed weakness.
    Next step: Generate a valid candidate, test another hypothesis, or keep the current portfolio under monitoring.
    Decision boundary: This is not a trade instruction or rebalance recommendation.

Remove from normal UI: `candidate_generation:factory...`, `current_vs_candidate...`, `no_available_comparison_metrics`, `decision_verdict.json`, `stale_downstream_artifact_ignored`, raw confidence identifiers, raw artifact paths, and raw JSON names.

If technical details are needed, use a collapsed `Technical details` section closed by default.

Validation commands from `frontend/`:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

Commit message:

    Clarify verdict availability states

### Session 7 — Cross-screen cleanup and final QA

Goal: Run a final pass across Step 4-6 to ensure the full post-Stress journey is coherent.

Check these outcomes:

1. Step 4 starts with Problem Classification.
2. Step 4 explains why a hypothesis is suggested.
3. Step 4 uses Hypothesis Builder, not Real Candidate Launchpad.
4. Step 4 does not show raw backend fields.
5. Step 4 has one clear primary CTA: Generate candidate.
6. Step 5 does not show fake comparison when comparison unavailable.
7. Step 5 shows trade-off summary before detailed table when comparison is valid.
8. Step 6 does not show raw artifact/debug errors.
9. Step 6 presents Evidence insufficient as a professional outcome, not a crash.
10. Every page has a clear next step.
11. Candidate is never presented as recommendation.
12. Verdict is never presented as trading instruction.
13. No `true`, `false`, or `n/a` in normal UI.
14. No raw backend artifact names in normal UI.

Remove from normal user UI everywhere in Step 4-6: `Real Candidate Launchpad`, `Candidate Launchpad` as main title, `Launchpad card`, `Card type`, `Default method`, `Source problem`, `Source card`, `Builder setup`, `setup_only`, `monitor_or_resolve_data`, `equal_weight` as raw lowercase, `risk_parity` as raw lowercase, `true`, `false`, `n/a`, `baseline_or_candidate_metric_missing`, `no_available_comparison_metrics`, `stale_downstream_artifact_ignored`, `decision_verdict.json`, `current_vs_candidate`, `candidate_generation`, `factory`, `artifact`, `backend`, `API`, `outputs`, `trade execution`, and `implementation order`.

Use instead: `Hypothesis Builder`, `Hypothesis test`, `Test setup`, `Suggested method`, `Diagnosis source`, `Reference benchmark test`, `Monitoring path`, `Candidate metric unavailable`, `Comparison unavailable`, `Previous result ignored because it is outdated`, `Equal Weight`, `Risk Parity`, `Available`, `Not available`, `Not available yet`, `No candidate or rebalance verdict is created here`, and `This is not a rebalance recommendation`.

Final validation commands from `frontend/`:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

Optional if available: run frontend screenshot smoke or Playwright visual smoke in a stable environment. For visual QA, use a clean local target, a fresh localhost port when possible, confirm the exact URL, and do not assume an old tab or old dev server is current. Report URL/port, route, active `reviewId` if relevant, whether sample mode was used, what browser state was reset or recovered, screenshots captured, and any unverified area.

Final report should include commits made, changed files by session, what was intentionally not changed, validation results, remaining limitations, and recommended next step. Do not push, merge, or make unrelated changes.

## Concrete Steps

For Session 00, the concrete steps were:

1. Inspect frontend route, component, state, label, and test files without editing code.
2. Identify raw backend/internal language leak points in Step 4-6.
3. Save this full plan as `docs/exec_plans/2026-06-10_post_stress_frontend_flow_alignment_plan.md`.
4. Stop and report that Session 00 is complete.

For later implementation sessions, work from the repository root `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`. Run frontend validation from `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА\frontend`.

Do not stage unrelated dirty files. If committing per session, stage only files intentionally changed for that session, for example:

    git add frontend/app/hypothesis/page.tsx frontend/components/layout/PageHeader.tsx
    git commit -m "Refine post-stress journey naming"

Before every commit, verify staged files with:

    git diff --cached --name-only

## Validation and Acceptance

Session 00 acceptance: The plan exists as a Markdown file in `docs/exec_plans/`, no Step 4-6 source code has been modified by Session 00, and the next agent can implement Session 1 without needing prior chat context.

Later sessions must validate with these commands from `frontend/`:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

Expected acceptance for the completed full plan:

- `/hypothesis` shows `Hypothesis Builder` and begins with `Problem Classification`.
- `/hypothesis` uses `Test setup` and `Generate candidate`, not `Real Candidate Launchpad`, backend field labels, or raw booleans.
- `/comparison` shows `Comparison unavailable` or `Comparison metrics unavailable` instead of fake metric tables when no valid comparison exists.
- `/comparison` shows trade-off summary before detailed metrics when a valid comparison exists.
- `/verdict` shows `Verdict unavailable`, `Evidence insufficient`, or a clean decision-support verdict depending on available evidence.
- No normal Step 4-6 UI shows raw artifact names, raw JSON filenames, `true`, `false`, `n/a`, or backend architecture terms.

## Idempotence and Recovery

This plan is safe to read and revise. Future sessions should be small and independently validated. If a session partially fails, keep unrelated working-tree changes untouched, inspect `git diff` for only the files touched in that session, and either complete the intended frontend-only edit or revert only the session's own changes.

Do not delete generated outputs, do not modify backend artifacts, and do not run destructive git commands. The repository already had unrelated dirty files before this plan file was created, so do not use broad `git add .`, broad checkout, or reset commands.

## Artifacts and Notes

Raw-term search used during Session 00 included patterns such as `Real Candidate Launchpad`, `Candidate Launchpad`, `Builder setup`, `current_vs_candidate`, `decision_verdict.json`, `baseline_or_candidate_metric_missing`, `no_available_comparison_metrics`, `stale_downstream_artifact_ignored`, `candidate_generation`, `factory`, `artifact`, `outputs`, `trade execution`, `setup_only`, `monitor_or_resolve_data`, `equal_weight`, `risk_parity`, `n/a`, `true`, and `false`.

The audit found representative user-facing raw terms in:

    frontend/app/hypothesis/page.tsx
    frontend/app/comparison/page.tsx
    frontend/app/verdict/page.tsx
    frontend/lib/reviewState.tsx
    frontend/components/layout/PageHeader.tsx

## Interfaces and Dependencies

No backend interfaces, API routes, JSON artifact schemas, or candidate/comparison/verdict calculation logic should change.

Frontend code should continue to use existing Next.js/React architecture. UI presentation should continue using existing components where possible, including `PageHeader`, `StatusBadge`, `DecisionHeroCard`, and card/table components. Shared label formatting should extend `frontend/lib/displayLabels.ts` and use existing helpers such as `normalizeDisplayLabel` where appropriate.

Types may be extended in `frontend/lib/types.ts` if needed for better user-facing hypothesis card fields, but the external backend payloads must remain unchanged. If a helper is added, prefer pure frontend functions that transform unknown backend values into clean display strings without mutating source data.

## Change Notes

- 2026-06-10: Created from the user-approved post-Stress frontend alignment plan after Session 00 audit. The user clarified that implementation should stop after Session 00 for now and that the whole plan should be saved as Markdown in the repository.
- 2026-06-10: Updated after Session 06 implementation to record verdict-state cleanup, validation results, and the remaining Session 07 final QA step.
