# Global Information Architecture and Defensive Copy Cleanup

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is self-contained so a future contributor can understand why the work exists, what changed, and how to validate it without relying on chat history.

## Purpose / Big Picture

Portfolio MRI has strong product guardrails: diagnosis first, current portfolio first, and decision support rather than trading advice. Those guardrails are correct, but the frontend had started to show them repeatedly as visible copy: badges, scope notes, candidate warnings, and review-status metadata. The result felt defensive and technical rather than like a clear diagnostic product.

After this change, guardrails remain authoring constraints in documentation and tests, but primary UI surfaces lead with the user's answer: the finding, why it matters, concise evidence, and the next action. A user can see the improvement by opening the Diagnosis route: it should no longer show repeated evidence-quality pills, scope warnings, or candidate-boundary copy above the advanced detail.

## Progress

- [x] (2026-06-18) Read the governing workflow and planning docs: `RULES.md`, `WORKFLOW.md`, and `PLANS.md`.
- [x] (2026-06-18) Added a failing frontend copy/IA regression test in `frontend/tests/copy-ia-tests.cjs` and wired `npm.cmd run test:copy`.
- [x] (2026-06-18) Proved the new test failed before implementation because Diagnosis repeated candidate-boundary copy, evidence quality, and review status in the header.
- [x] (2026-06-18) Cleaned the Diagnosis benchmark route by removing the duplicate top-card layer, hero evidence badge, scope aside, candidate-boundary canvas row, and defensive CTA copy.
- [x] (2026-06-18) Removed review execution status from the platform top header primary metadata.
- [x] (2026-06-18) Cleaned Hypothesis primary/fallback copy that repeated defensive candidate/rebalance language.
- [x] (2026-06-18) Finished source-of-truth documentation sync and project memory updates, including the new IA/copy contract, design docs, `DECISIONS.md`, `CHANGELOG.md`, and `TESTING.md`.
- [x] (2026-06-18) Ran frontend, docs, and visual QA checks and recorded the outcome.

## Surprises & Discoveries

- Observation: The project already had design contracts discouraging repeated evidence badges, but the code still hardcoded repeated defensive copy in several components.
  Evidence: `npm.cmd run test:copy` failed on `DiagnosisSummaryPanel.tsx`, `DiagnosisHero.tsx`, `DiagnosticCanvas.tsx`, `StressLabCta.tsx`, and `PlatformTopHeader.tsx` before the cleanup.

- Observation: The noisy `Review partial` label was not a backend problem. It was produced by frontend header normalization that translated staged execution state into visible primary metadata.
  Evidence: `PlatformTopHeader.tsx` contained `normalizeStatus()` and appended normalized review status to the metadata array.

## Decision Log

- Decision: Treat diagnosis-first/current-portfolio-first/not-advice language as internal authoring rules, not primary UI copy.
  Rationale: Repeating guardrails in badges and hero cards makes the product feel like a legal disclaimer instead of a diagnostic case file. Product safety is better preserved through route order, neutral verbs, blocked states, and explicit final evidence review.
  Date/Author: 2026-06-18 / Codex.

- Decision: Use `/diagnosis` as the benchmark route for the first implementation pass while adding a global static guard over all key route components.
  Rationale: The reported screenshots came from Diagnosis, and the route already owns the clearest first-read IA. A global static guard prevents the same class of copy from immediately returning elsewhere.
  Date/Author: 2026-06-18 / Codex.

- Decision: Remove review execution status from the top header primary metadata instead of renaming `partial` to a softer label.
  Rationale: The header is platform chrome, not the place to explain staged execution internals. Stage-specific screens can still explain blocked or running states when they matter.
  Date/Author: 2026-06-18 / Codex.

## Outcomes & Retrospective

Completed validation shows a cleaner Diagnosis route, quieter platform chrome, and a regression test that fails if defensive copy returns to primary surfaces. Visual QA screenshots were captured under `output/ia-copy-visual-qa/` for `/diagnosis`, `/evidence?sample=1`, `/hypothesis?sample=1`, and `/verdict` using a fresh browser context with compact localStorage fixture state.

Validation completed:

    cd frontend && npm.cmd run test:copy
    cd frontend && npm.cmd run typecheck
    cd frontend && npm.cmd run test:api
    cd frontend && npm.cmd run test:smoke
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

All listed checks passed.

## Context and Orientation

The relevant frontend route components live under `frontend/components/`. `PlatformTopHeader.tsx` renders shared route chrome. `frontend/components/diagnosis/DiagnosisSummaryPanel.tsx` composes the Diagnosis screen from `DiagnosisHero`, `EvidenceStrip`, `DiagnosticCanvas`, `StressLabCta`, and `AdvancedDiagnostics`. `frontend/lib/hypothesis/hypothesisScreenModel.ts` provides fallback copy for Hypothesis state, so it can reintroduce defensive wording even when component text is clean.

A primary UI surface means visible hero, top cards, route chrome, action panels, and first-read state copy. Advanced details, blocked states, and error recovery may explain limitations, but they should not repeat broad legal-style guardrails as normal page content.

Defensive copy means visible text whose main purpose is to reassure the reader that Portfolio MRI is not doing something else, for example `current only`, `not a recommendation`, `not a rebalance`, `before any candidate`, `candidate testing`, `diagnostic only`, or repeated generic evidence/status badges. These ideas remain true as product constraints, but they should not dominate the UI.

## Plan of Work

First, keep the new static regression test in `frontend/tests/copy-ia-tests.cjs`. It scans key route components and fails when defensive guardrails appear in primary surfaces. Keep this test intentionally narrow: it does not ban the word candidate everywhere; it bans defensive phrases that turn the UI into a warning wall.

Second, simplify the Diagnosis composition. `DiagnosisSummaryPanel` should lead with one hero, one evidence strip, one diagnostic canvas, one Stress Lab action, and collapsed detailed diagnostics. Do not re-add the removed top-card layer unless it contains genuinely new investor-facing content rather than restating the same metrics.

Third, keep `PlatformTopHeader` as quiet route chrome. It may show route title, portfolio name, currency, holding count, and data-window availability. It must not translate staged review status such as `partial` into the primary metadata line.

Fourth, update source-of-truth docs so future agents understand that product guardrails are authoring constraints. Documentation may state the product boundary, but should not instruct agents to solve safety by repeating defensive labels in hero copy, badges, or top cards.

## Concrete Steps

Run commands from the repository root unless a command explicitly changes directory.

1. TDD proof:

    cd frontend
    npm.cmd run test:copy

   Before the cleanup this command failed on three tests. After cleanup it should report 3 passing tests.

2. Frontend regression checks:

    cd frontend
    npm.cmd run typecheck
    npm.cmd run test:api
    npm.cmd run test:smoke

3. Documentation checks:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

4. Visual QA:

   Start a fresh local frontend target, use a clean browser context, and capture screenshots for at least `/diagnosis`, `/evidence`, `/hypothesis`, and `/verdict`. Record the URL, port, browser state reset, screenshots, and unverified areas in the final report.

## Validation and Acceptance

Acceptance is behavior-oriented:

- `npm.cmd run test:copy` passes and fails if defensive phrases return to the key primary route files.
- The Diagnosis route no longer shows an evidence-quality hero badge, scope note panel, duplicate top cards, candidate-boundary row, or CTA text about testing candidates.
- The platform top header no longer shows `Review partial`, `Review completed`, or other normalized staged review statuses in primary metadata.
- Source docs point to the IA/copy contract instead of encouraging repeated visible guardrails.
- Visual QA screenshots show a cleaner first-read hierarchy on the changed routes.

## Idempotence and Recovery

The edits are source-only and safe to repeat. If a validation command fails, inspect the specific failing file rather than broadening the scope. Do not regenerate portfolio outputs or run live portfolio review commands for this UI/copy cleanup unless a visual QA route explicitly needs fresh local demo data.

## Artifacts and Notes

Initial TDD failure evidence:

    npm.cmd run test:copy
    tests 3, pass 0, fail 3
    Failures: repeated candidate-boundary copy, repeated evidence-quality copy, and review status in PlatformTopHeader.

Post-cleanup expected evidence:

    npm.cmd run test:copy
    tests 3, pass 3, fail 0

## Interfaces and Dependencies

No backend API, schema, formula, artifact, optimizer, or generated-output interface changes are part of this plan. The only new command interface is the frontend script:

    npm.cmd run test:copy

It runs `node --test tests/copy-ia-tests.cjs` from `frontend/package.json`.
