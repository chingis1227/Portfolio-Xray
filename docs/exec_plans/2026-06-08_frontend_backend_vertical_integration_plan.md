# Frontend Backend Vertical Integration Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is self-contained for a
new contributor who has only the current working tree and this file.

No product code implementation was done when this ExecPlan was created. Creating and
maintaining this plan is documentation work only. Root `config.yml` must not be modified
by this plan.

## Purpose / Big Picture

Portfolio MRI / Portfolio X-Ray / Diagnosis 2 is a diagnosis-first investment
decision-support product. It is not a dashboard and it is not an optimizer cockpit.
After this plan is implemented, a user can enter a portfolio in the Next.js frontend,
run the real Python diagnostics pipeline, choose one diagnostic hypothesis to test,
generate exactly one candidate, compare the current portfolio with that candidate,
see a non-trading decision verdict, and read a client-ready explanation grounded in
the produced JSON artifacts.

The end-to-end behavior to demonstrate is:

    Input portfolio
    -> Portfolio X-Ray
    -> Stress Test Lab
    -> Problem Classification
    -> Candidate Launchpad
    -> Builder Setup
    -> Candidate Generation
    -> Current vs Candidate Comparison
    -> Decision Verdict
    -> Client-ready Report / AI Commentary

Candidate means “a diagnostic portfolio test,” not a recommendation. Builder setup
means “parameters for the test,” not rebalance instructions. Verdict means
“decision-support interpretation,” not trading instruction. No-trade and evidence
insufficient are valid outcomes.

## Progress

- [x] (2026-06-08) ExecPlan created as planning-only documentation. No frontend or
  Python product code was changed by plan creation.
- [x] (2026-06-08) Session 00 baseline audit completed. `npm.cmd run typecheck`,
  `npm.cmd run build`, and `.\.venv\Scripts\python.exe -m pytest
  tests\test_frontend_review_bridge.py` all passed. No fixes, refactors, cleanup,
  candidate generation, dependency upgrades, or commits were performed.
- [x] (2026-06-08) Session 01 candidate generation discovery hardening completed.
  Existing one-candidate backend plumbing was inspected only; no candidate generation,
  factory run, product-code edit, frontend edit, dependency change, or commit was
  performed. The safe Session 02 path is to rebuild or validate a run-local Builder
  artifact so its `selected_card_id`/`candidate_setup.source_card_id` matches the
  frontend-selected Launchpad card before any Block 7 candidate generation is allowed.
- [x] (2026-06-08) Session 02 selected-card backend Builder setup completed.
  `scripts/run_review_from_payload.py` now has a run-local `--prepare-builder` path
  that rebuilds `analysis_subject/portfolio_alternatives_builder.json` from the
  frontend-selected Launchpad card and refuses mismatched Builder lineage before
  candidate generation. Focused bridge tests, frontend typecheck, and frontend build
  passed.
- [x] (2026-06-08) Session 03 candidate generation backend bridge completed.
  `scripts/run_review_from_payload.py` now has a run-local `--generate-candidate` path
  that validates selected Builder lineage, delegates exactly one candidate to existing
  Block 7 generation plumbing with run-local config/output paths, and refuses mismatched
  Candidate Generation or multi-candidate factory summaries. A backend API route was
  added at `/api/portfolio/candidate/generate`; UI wiring is left for Session 04.
- [x] (2026-06-08) Session 04 frontend Generate Candidate button completed.
  The Hypothesis Builder panel now enables Generate Candidate only when the selected
  backend Builder setup matches the selected Launchpad card and is generatable, calls
  `/api/portfolio/candidate/generate`, shows loading/safe error states, stores a
  compact `candidate_generation` summary in frontend review state, and displays the
  generated candidate status/weights without creating comparison or verdict artifacts.
  Frontend typecheck/build and focused bridge tests passed.
- [x] (2026-06-08) Session 05 current-vs-candidate discovery completed. Existing
  Block 8 code already exposes a run-local helper,
  `src.candidate_comparison.write_block8_current_vs_candidate_only_outputs()`, that
  writes `candidate_comparison.json` plus `current_vs_candidate.json` only, refuses
  `candidate_generation` artifacts marked tombstone / `not_authoritative` / inactive,
  and records stale downstream verdict artifacts as ignored rather than current.
  Session 06 should extend `scripts/run_review_from_payload.py` with a compare-only
  run-local path plus a Next.js API route mirroring the Session 04 candidate
  generation bridge pattern.
- [x] (2026-06-08) Session 06 current-vs-candidate backend connection completed.
  `scripts/run_review_from_payload.py` now exposes a run-local `--run-comparison`
  path that loads review-local `input.yml`, validates selected-card lineage against
  `candidate_generation.json`, re-checks one-candidate factory scope, calls
  `src.candidate_comparison.write_block8_current_vs_candidate_only_outputs()`, and
  writes `current_vs_candidate_result.json` without creating verdict or report
  artifacts. A dedicated API route was added at
  `/api/portfolio/comparison/generate`, and the required backend/frontend checks
  passed.
- [x] (2026-06-08) Session 07 comparison frontend connection completed.
  The Comparison page no longer reads demo JSON in the normal flow; it runs the
  selected active review through `/api/portfolio/comparison/generate`, stores a
  compact `current_vs_candidate` summary in frontend review state, renders
  improved/worsened/neutral/unclear evidence plus turnover, cost, materiality,
  and warnings, and keeps wording diagnostic-only with no winner/recommendation
  language.
- [x] (2026-06-08) Session 08 Decision Verdict backend connection completed.
  `scripts/run_review_from_payload.py` now exposes a run-local `--run-verdict` path
  that validates selected-card and selected-candidate lineage, writes exactly one
  `decision_verdict.json` from active Block 7/8 artifacts, refuses stale comparison
  scope, and allows failed/infeasible candidates only as non-rebalance verdicts. A
  dedicated API route was added at `/api/portfolio/verdict/generate`; frontend Verdict
  UI wiring is left for Session 09.
- [x] (2026-06-08) Session 09 Verdict frontend connection completed.
  The Verdict page now uses the active review only, calls
  `/api/portfolio/verdict/generate`, stores a compact `decision_verdict` summary in
  frontend review state, renders no-trade/evidence-insufficient/failed-candidate
  outcomes as normal decision-support states, and avoids demo fallback plus
  trade-instruction wording.
- [x] (2026-06-08) Session 10 Report / AI Commentary connection completed.
  `scripts/run_review_from_payload.py` now exposes a run-local `--run-report-context`
  path that validates selected-card, selected-candidate, comparison, and verdict
  lineage before writing a post-compare `ai_commentary_context.json`. A dedicated API
  route was added at `/api/portfolio/report/generate`; the Report page now renders
  active-review client-ready commentary from the grounded context instead of demo JSON.
- [x] (2026-06-08) Session 11 end-to-end vertical QA completed. Frontend
  typecheck, frontend build, and the focused frontend bridge pytest suite passed.
  Three representative backend verticals completed from Input through grounded
  Report context with matching active review/card/candidate lineage: `VOO`/`BND`/
  `Cash USD`, `VOO`/`BND`/`GLD` without cash, and `VOO`/`TLT`/`GLD`.
  One early wrapper run stalled on the second portfolio and was stopped; direct
  PowerShell reruns completed the remaining two portfolios. No Session 12 work was
  started.
- [x] (2026-06-08) Session 12 error handling and failure-state hardening completed.
  The Python frontend bridge now scrubs user-facing failure text, stdout tails, and
  stderr tails for tracebacks and absolute local paths, while returning safe failure
  detail codes for validation, timeout, missing-output, lineage/stage, and backend
  errors. All vertical frontend API routes now scrub returned `error` and `details`
  text before sending it to the client. Focused bridge tests, frontend typecheck, and
  frontend build passed.
- [x] (2026-06-08) Session 13 storage and state cleanup completed.
  Frontend persisted state now keeps compact summaries plus `reviewId` instead of
  permanently storing raw `review_result.json` in localStorage. Hydration/write removes
  legacy `pmri.reviewResult.*` raw keys, new portfolio input clears downstream stale
  state, and Evidence/Hypothesis can render from compact summaries after reload.
- [x] (2026-06-08) Session 14 visual/product polish completed.
  The real vertical flow now has a more premium decision-room shell, stronger stage
  header hierarchy, clearer workflow progress rail, sidebar operating-mode reminder,
  refined card/surface texture, and safer loading copy on Portfolio Input. No product
  contracts, backend bridge behavior, Python code, root `config.yml`, or dependency
  versions were changed.
- [x] (2026-06-08) Session 15 documentation and demo runbook completed.
  Added `docs/demo/frontend_backend_vertical_runbook.md` and linked it from
  `../../README.md`, `../../frontend/README.md`, and `../demo/README.md`; updated
  `CHANGELOG.md`. The docs now cover commands, run-local review directories,
  compact browser state, stale-artifact recovery, product wording boundaries, and
  the manual Input-to-Report demo path.
- [x] (2026-06-08) Session 16 final validation and handoff completed.
  Final frontend typecheck/build and focused bridge tests passed. The three Session 11
  review ids were re-inspected and each retained the required Input-to-Report artifact
  chain with completed comparison, verdict, report commentary, post-compare grounding,
  and no-trade execution guardrail. No new feature work was added in Session 16.

## Surprises & Discoveries

- Observation: Before this plan was created, the working tree already contained many
  frontend changes, a new API route tree, `scripts/run_review_from_payload.py`,
  `tests/test_frontend_review_bridge.py`, and `runs/` as untracked or modified paths.
  Evidence: initial `git status --short` showed those paths before this file existed.

- Observation: Session 01 found existing Block 7 plumbing in
  `scripts/generate_candidate_from_builder_setup.py` and `src/candidate_generation.py`.
  It reads one `portfolio_alternatives_builder.json`, extracts one validated
  `candidate_setup`, delegates to `run_candidate_factory.py --candidates <candidate_id>`,
  and writes one `candidate_generation.json`. It already treats failed or infeasible
  factory status as stronger evidence than stale `weights.json`.
  Evidence: `generate_candidate_from_builder_setup()` and
  `generation_kwargs_from_factory_result()`.

- Observation: Session 01 found an existing full Blocks 5-9 vertical demo script,
  `scripts/run_blocks_5_to_9_vertical_flow.py`, but it is not yet the frontend bridge.
  It runs diagnosis, removes stale vertical artifacts from the configured output
  directory, rebuilds one selected Builder document from Launchpad, generates one
  candidate attempt, writes comparison, verdict, and AI commentary context.
  Evidence: `run_blocks_5_to_9_vertical_flow()`, `STALE_VERTICAL_FILENAMES`, and
  `build_selected_builder_document()`.

- Observation: The current frontend bridge, `scripts/run_review_from_payload.py`,
  supports only `core_only` and `diagnosis_plus_problem`; it creates an isolated
  `runs/frontend_review_*` directory and reads diagnosis/problem artifacts from
  `analysis_subject/`, but it has no selected-card/candidate-generation mode yet.
  Evidence: `SUPPORTED_MODES = (MODE_CORE_ONLY, MODE_DIAGNOSIS_PLUS_PROBLEM)`.

- Observation: The likely Session 02 risk is not candidate generation itself, but stale
  or mismatched Builder setup reuse. Existing Builder documents contain
  `selected_card_id`, and Candidate Generation carries `source_builder_setup.source_card_id`
  plus `candidate.source_card_id`; the frontend/backend handoff must refuse to generate
  when those fields do not match the selected Launchpad card.

- Observation: Session 05 discovery found that the exact Block 8 backend helper already
  exists in `src/candidate_comparison.write_block8_current_vs_candidate_only_outputs()`.
  It scopes `candidate_comparison.json` to one selected candidate, calls
  `build_current_vs_candidate(..., candidate_generation=...)`, and intentionally does not
  create verdict or AI commentary artifacts.
  Evidence: `src/candidate_comparison.py` `write_block8_current_vs_candidate_only_outputs()`.

- Observation: Session 05 discovery found two separate comparison guard layers already
  implemented. `src.candidate_comparison._candidate_ids_from_candidate_generation()`
  rejects tombstone / `artifact_status=not_authoritative` / inactive
  `candidate_generation`, while `src.current_vs_candidate.candidate_generation_blocks_comparison()`
  blocks failed, infeasible, non-generated, weightless, non-comparable, or mismatched
  candidate ids.
  Evidence: `src/candidate_comparison.py` lines around `_candidate_ids_from_candidate_generation()`
  and `src/current_vs_candidate.py` lines around `candidate_generation_blocks_comparison()`.

- Observation: Session 05 discovery found the existing vertical demo script
  `scripts/run_blocks_5_to_9_vertical_flow.py` already orchestrates the exact safe
  order needed for Session 06 backend wiring: generate one candidate, call the Block 8
  helper with that candidate, then stop before verdict unless explicitly continuing.
  Evidence: `run_blocks_5_to_9_vertical_flow()` calls
  `write_block8_current_vs_candidate_only_outputs()` immediately after candidate generation.

- Observation: Session 05 discovery found the current frontend bridge has no compare-only
  path yet, but Session 04 already established the right transport pattern: a focused
  helper in `scripts/run_review_from_payload.py`, a dedicated Next.js route under
  `frontend/app/api/portfolio/...`, and bridge tests in `tests/test_frontend_review_bridge.py`.
  Evidence: `generate_selected_candidate()` in `scripts/run_review_from_payload.py` and
  `frontend/app/api/portfolio/candidate/generate/route.ts`.

- Observation: Session 06 implementation could reuse the existing Block 8 helper without
  changing comparison math, but it still needed an explicit bridge-side guard that the
  run-local `candidate_factory_run.json` contains only the selected candidate before the
  helper rebuilds `candidate_comparison.json`.
  Evidence: `compare_selected_candidate()` now calls the existing
  `_assert_factory_run_scoped_to_one_candidate()` before invoking
  `write_block8_current_vs_candidate_only_outputs()`.

- Observation: Session 06 implementation found the safest return contract is a dedicated
  `current_vs_candidate_result.json` wrapper rather than returning raw stdout. That keeps
  the API route pattern aligned with Session 04 and gives Session 07 a stable handoff for
  the Comparison page.
  Evidence: `scripts/run_review_from_payload.py` `--run-comparison` branch and
  `frontend/app/api/portfolio/comparison/generate/route.ts`.

- Observation: Session 06 verification found an environment-specific frontend quirk:
  `npm.cmd run typecheck` can fail before `next build` because `frontend/tsconfig.json`
  includes `.next/types/**/*.ts` and those files may not exist yet in a fresh state. A
  successful `next build` materializes them, after which `npm.cmd run typecheck` passes.
  Evidence: Session 06 verification output first showed TS6053 missing `.next/types/...`
  files, then `next build` succeeded, then `npm.cmd run typecheck` passed.

- Observation: Session 10 could reuse the existing deterministic AI Commentary context
  builder instead of inventing report prose. The bridge still needed its own active-run
  lineage guard so a stale `decision_verdict.json` or mismatched `current_vs_candidate.json`
  cannot become client-facing report copy.
  Evidence: `write_selected_report_context()` validates Candidate Generation, one-candidate
  factory scope, Block 8 scope, and Decision Verdict scope before calling
  `write_ai_commentary_context_outputs()`.

## Decision Log

- Decision: Use an isolated `runs/frontend_review_<timestamp_or_uuid>/` directory as
  the frontend review boundary.
  Rationale: The frontend must not mutate root `config.yml`, must not silently use old
  global candidate artifacts, and must have one review id that ties diagnosis, selected
  candidate, comparison, verdict, and report context together.
  Date/Author: 2026-06-08 / Codex.

- Decision: Implement one selected candidate at a time.
  Rationale: The product thesis rejects a candidate zoo. The user chooses one Launchpad
  card, the Builder prepares one setup, and the backend generates one candidate artifact.
  Date/Author: 2026-06-08 / Codex.

- Decision: Treat stale `current_vs_candidate.json` and `decision_verdict.json` as
  unsafe unless they match the current run lineage.
  Rationale: The frontend must never display tombstone or old post-compare outputs as
  if they belong to the current user input.
  Date/Author: 2026-06-08 / Codex.

- Decision: Session 06 comparison transport should mirror the Session 04 candidate
  generation transport shape instead of inventing a new multi-step RPC contract.
  Rationale: A dedicated `--run-comparison` bridge action plus one Next.js API route keeps
  the frontend/backend boundary small, review-local, and easy for Session 07 to consume.
  Date/Author: 2026-06-08 / Codex.

## Outcomes & Retrospective

This plan is complete as of Session 16. The planning step itself created only this ExecPlan and did not
implement product code. Sessions 00 and 01 were completed without product-code changes. Sessions 02 and 03
implemented the selected-card Builder handoff and one-candidate backend generation bridge.
Session 04 completed the frontend candidate generation wiring. Session 05 was the
discovery session for current-vs-candidate comparison.
Session 05 completed as discovery-only with no product-code edits. The main result is
that Session 06 does not need new comparison math; it should reuse the existing Block 8
helper and add only a run-local bridge/API wrapper plus lineage/staleness tests.
Session 06 completed that wrapper: the repository now has a selected-candidate-only
comparison backend path that stops before verdict/report generation. Session 07
connected that backend path to the frontend Comparison page and renders active-review
comparison evidence without demo fallback or recommendation language. Session 08
connected the selected-candidate Decision Verdict backend/API path while leaving the
Verdict page UI unchanged for Session 09. Session 09 connected the Verdict page to
that backend/API path and renders active-review verdict evidence without demo fallback
or trading-instruction language. Session 10 connected the Report page to the run-local
AI Commentary grounding context and kept the output deterministic, client-ready, and
non-trading. Session 11 validated the required frontend build/test gates and completed
the three-portfolio Input-to-Report backend vertical QA matrix. An early wrapper run
stalled on the no-cash portfolio and was stopped, but direct PowerShell reruns completed
the no-cash and TLT-substitution cases through grounded Report context.
Session 12 hardened recoverable failure output around the same vertical flow: bridge
result JSON and frontend API responses now hide tracebacks and local filesystem paths
while preserving safe stage-level failure messages and status codes.
Session 13 reduced browser state risk: compact review state now persists `reviewId`,
diagnosis/evidence/launchpad/builder summaries, selected candidate/comparison/verdict
summaries, and stage statuses, while raw backend JSON is not stored forever in
localStorage. Legacy raw localStorage keys are cleaned on hydration/write.
Session 14 polished the frontend presentation layer only: the app shell, page headers,
workflow rail, sidebar, card surfaces, and diagnosis loading copy now better communicate
the premium Investment Decision Room concept while preserving the diagnosis-first,
non-recommendation boundaries and existing data contracts.
Session 15 documented the completed frontend/backend vertical flow for human
operators: verification commands, dev-server startup, three sample portfolios, run-local
artifact chain, stale-artifact recovery, and safe product language are now captured in
a dedicated runbook and linked from README surfaces.
Session 16 completed final validation and handoff: frontend typecheck/build, focused
bridge tests, and three-run artifact inspection all passed; remaining limitations are
documented rather than hidden.

## Global Session Protocol

Every session must begin by running:

    git status --short

The session notes must clearly separate:

- Pre-existing dirty files: files already dirty before the session starts.
- Files changed in this session: files modified by the current session only.

Do not revert, clean, overwrite, or fix pre-existing dirty files unless the user
explicitly asks for that. Do not run destructive commands. Do not commit unless the
user explicitly instructs it. Every implementation session must end with a suggested
commit message, but must not create the commit. Do not run `npm audit fix --force`
unless explicitly approved. Do not upgrade major dependencies during these vertical
integration sessions. Never modify root `config.yml`. Never change Python calculation
logic unless explicitly approved.

Session 00 is stricter than implementation sessions. Session 00 is audit-only. It may
inspect status, document dirty files, run current verification commands, and confirm
whether the current frontend/API/Python bridge flow still works. It must not fix issues,
refactor, clean files, edit frontend code, edit Python code, generate candidates,
upgrade dependencies, commit, or create files except audit notes inside this ExecPlan
if needed.

## Context and Orientation

The repository root is `D:\Desktop\CURSOR TULA DIAGNOSTICS`. The frontend lives
under `frontend/` and is a Next.js/React application. The confirmed frontend API route
is `frontend/app/api/portfolio/diagnose/route.ts`, which posts portfolio input to a
Python bridge. The bridge is `scripts/run_review_from_payload.py`. It creates an
isolated frontend review run directory, writes `payload.json` and `input.yml`, invokes
the existing Python pipeline, then writes `review_result.json`.

The bridge currently supports these modes:

- `core_only`, which produces Portfolio X-Ray and Stress outputs.
- `diagnosis_plus_problem`, which runs the diagnosis-plus-problem bundle without
  candidates.

The existing candidate-related backend code includes
`scripts/generate_candidate_from_builder_setup.py` and
`scripts/run_blocks_5_to_9_vertical_flow.py`. These files are important discovery
targets. The plan must prefer existing helpers and repo patterns rather than creating
parallel calculation logic.

The product stages and plain meanings are:

- Diagnosis: what is going on in the current portfolio.
- Evidence: the X-Ray and stress facts supporting the diagnosis.
- Hypothesis: one possible diagnostic test from Candidate Launchpad.
- Builder setup: editable test parameters for one selected Launchpad card.
- Candidate generation: one generated diagnostic candidate, not a recommendation.
- Comparison: current portfolio versus the one candidate, with trade-offs.
- Verdict: decision-support conclusion where no-trade and evidence-insufficient are
  first-class outcomes.
- Report / AI Commentary: client-ready explanation grounded only in allowed artifacts.

## Current State Audit

The confirmed current state before implementation is:

- `frontend/` exists.
- The frontend has been confirmed by the user to run with `npm.cmd run dev`.
- The frontend has been confirmed by the user to pass `npm.cmd run typecheck`.
- The frontend has been confirmed by the user to pass `npm.cmd run build`.
- `frontend/app/api/portfolio/diagnose/route.ts` exists as a real API route.
- `scripts/run_review_from_payload.py` exists as the Python bridge.
- The bridge supports `core_only` and `diagnosis_plus_problem`.
- `diagnosis_plus_problem` is expected to produce `portfolio_xray.json`,
  `stress_report.json`, `problem_classification.json`, `candidate_launchpad.json`, and
  `portfolio_alternatives_builder.json`.
- The current frontend flow works for Portfolio Input -> API -> Python bridge ->
  Python pipeline -> Diagnosis.
- The current frontend flow works for Portfolio Input -> API -> Python bridge ->
  Python pipeline -> Evidence.
- The current frontend flow works for Portfolio Input -> API -> Python bridge ->
  Python pipeline -> Hypothesis.
- The Hypothesis page renders real Candidate Launchpad cards.
- Hypothesis card selection to Builder Setup preview works.
- Generate Candidate is visible but disabled.
- No real candidate generation is connected to the frontend yet.
- No comparison, verdict, or report live frontend flow is connected yet.
- Python/backend calculation logic must not be changed unless explicitly required.
- Root `config.yml` must not be modified.

Session 00 must refresh this audit with actual command output from the current working
tree.

## Target Final State

The final MVP target is a real vertical product flow:

    User enters portfolio
    -> Python computes real outputs
    -> user sees real Diagnosis
    -> user sees real Evidence
    -> user selects one real Hypothesis
    -> user sees Builder setup for that selected card
    -> user generates one Candidate
    -> user sees real Current vs Candidate Comparison
    -> user sees real Decision Verdict
    -> user sees a client-ready Report / AI Commentary summary

The final flow must not silently fall back to demo JSON after a real run. It must not
read old tombstone `decision_verdict` or `current_vs_candidate` artifacts as real
results. It must not expose backend paths or raw stack traces in user-facing UI.

## Architecture Diagram in Text

    Frontend UI screens
      Portfolio Input, Diagnosis, Evidence, Hypothesis, Builder, Candidate,
      Comparison, Verdict, Report
        |
        v
    Next.js API routes
      /api/portfolio/diagnose now; later candidate/comparison/verdict/report endpoints
        |
        v
    Python bridge scripts
      scripts/run_review_from_payload.py for diagnosis stages
      candidate bridge to be created or extended for selected candidate stages
        |
        v
    Existing Python pipeline
      run_report.py, run_portfolio_review.py, candidate builder/factory/comparison/verdict helpers
        |
        v
    Isolated run directory
      runs/frontend_review_<timestamp_or_uuid>/
        |
        v
    Product JSON outputs
      input.yml, payload.json, review_result.json, analysis_subject/,
      candidate_generation.json, current_vs_candidate.json, decision_verdict.json,
      ai_commentary_context.json if applicable
        |
        v
    Frontend review state
      compact current review id and stage summaries, not large raw blobs forever
        |
        v
    UI screens
      render only artifacts that belong to the active review id and selected candidate

## Run Directory Strategy

Every frontend-triggered review must use an isolated run directory:

    runs/frontend_review_<timestamp_or_uuid>/
      input.yml
      payload.json
      review_result.json
      analysis_subject/
        portfolio_xray.json
        stress_report.json
        problem_classification.json
        candidate_launchpad.json
        portfolio_alternatives_builder.json
      candidate_generation.json
      current_vs_candidate.json
      decision_verdict.json
      ai_commentary_context.json

If a stage cannot produce an artifact, it should write or return a structured failed
result for that stage rather than silently reusing an old artifact. Generated
`frontend_review_*` runs must remain ignored by git. Full raw outputs are useful for
debugging and provenance, but frontend state should not store all raw JSON forever.
The frontend should keep compact summaries and a `review_id`; raw access can be via
backend endpoints tied to that `review_id`.

Root `config.yml` must never be modified. The bridge may write an isolated `input.yml`
inside the run directory.

## Product Output Contract

Stage A output:

- `portfolio_xray`
- `stress_report`

Stage B output:

- `problem_classification`
- `candidate_launchpad`
- `portfolio_alternatives_builder`

Stage C output:

- `candidate_generation`

Stage D output:

- `current_vs_candidate`

Stage E output:

- `decision_verdict`

Stage F output:

- `ai_commentary_context` or a report-ready summary derived from it

Each stage must know its upstream `review_id` and selected candidate, where applicable.
Stage C and later must be scoped to exactly one selected candidate. Stage D and E must
reject or ignore stale artifacts that do not match the current review/candidate lineage.

## Required Verification Commands

Baseline frontend checks:

    cd D:\Desktop\CURSOR TULA DIAGNOSTICS\frontend
    npm.cmd run typecheck
    npm.cmd run build

Baseline backend bridge check:

    cd D:\Desktop\CURSOR TULA DIAGNOSTICS
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py

If `.venv` is missing, follow the Codex Windows Python rule: check `py -3 --version`,
`python --version`, `where py`, and `where python`; if `py -3` works, create `.venv`
with `py -3 -m venv .venv` and then run Python through `.\.venv\Scripts\python.exe`.

Add relevant backend tests as discovered. Likely tests include focused checks for:

- `scripts/run_review_from_payload.py`
- `scripts/generate_candidate_from_builder_setup.py`
- `scripts/run_blocks_5_to_9_vertical_flow.py`
- `src.candidate_comparison`
- `src.decision_verdict`
- stale artifact and lineage guards

## Global Safety Rules

Never modify root `config.yml`. Never change Python calculation logic unless explicitly
approved. Never run a candidate zoo accidentally. Never use stale candidates as the
selected candidate. Never expose tombstone verdict or comparison artifacts as real.
Never silently fall back to demo JSON after a real run. Never imply recommendation,
trading instruction, or rebalance instruction. Always run typecheck, build, and backend
bridge tests after implementation sessions unless the session is explicitly discovery-only.

Equal Weight and Risk Parity may be reference tests; they are not recommendations.
Evidence insufficient is a valid outcome. No-trade is a valid outcome.

## Session-by-Session Implementation Plan

### Session 00 — Baseline audit and lock current state

Goal: Audit the current working state without implementing anything.

Files likely to touch: This ExecPlan only, if audit notes need to be recorded.

Files forbidden to touch: all frontend code, all Python code, root `config.yml`,
dependency manifests, generated candidate/comparison/verdict files, and pre-existing
dirty files.

Commands to run:

    git status --short
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py

Expected outputs: status output listing pre-existing dirty files; successful frontend
typecheck; successful frontend build; successful bridge pytest. If checking current
flow is feasible without candidate generation, verify that the current diagnosis API
path still returns a completed `diagnosis_plus_problem` review or explain why it was
not run.

Pass/fail criteria: Pass if current checks complete successfully or any failures are
documented without fixes. Fail if product code is changed, dirty files are cleaned, or
candidate generation is run.

Rollback notes: There should be nothing to roll back except this ExecPlan audit note.
Do not clean generated verification output unless explicitly asked.

Manual test: If feasible, start the frontend with `npm.cmd run dev`, submit a small
portfolio, and confirm Diagnosis, Evidence, and Hypothesis show real data. Do not click
or enable Generate Candidate.

What must not happen: no fixes, no refactors, no cleanup, no frontend edits, no Python
edits, no candidate generation, no dependency upgrades, no commits.

Suggested commit message: not applicable because Session 00 is audit-only.

### Session 01 — Candidate generation discovery hardening

Goal: Inspect existing candidate generation behavior and document how a selected
Launchpad card should become a safe Builder setup for one candidate.

Files likely to touch: this ExecPlan or a future audit note only, unless the user
explicitly authorizes implementation.

Files forbidden to touch: root `config.yml`, Python calculation logic, frontend UI code,
dependency manifests.

Commands to run:

    git status --short
    Get-Content scripts\generate_candidate_from_builder_setup.py -TotalCount 420
    Get-Content scripts\run_blocks_5_to_9_vertical_flow.py -TotalCount 540
    rg -n "candidate_generation|portfolio_alternatives_builder|selected_card|current_vs_candidate" scripts src tests

Expected outputs: notes on `selected_card_id`, `candidate_setup`, existing stale
artifact protections, and whether candidate factory writes to run-local or global
folders.

Pass/fail criteria: Pass if the implementation path is clear enough for Session 02 and
stale artifact risks are listed. Fail if implementation starts.

Rollback notes: no product files should be modified.

Manual test: none; discovery-only.

What must not happen: no candidate generation, no factory run, no candidate zoo, no code
edits.

Suggested commit message: not applicable unless documentation notes are intentionally
committed later.

### Session 02 — Selected card to backend Builder setup

Goal: Implement a safe backend path that produces a matching
`portfolio_alternatives_builder.json` for the selected `selected_card_id` when the
current Builder artifact does not match the selected card.

Files likely to touch: bridge or helper code around selected-card Builder creation,
focused tests, and possibly API contract types.

Files forbidden to touch: root `config.yml`, calculation formulas, candidate factory
optimization logic, dependency manifests.

Commands to run:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py
    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_alternatives_builder.py
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build

Expected outputs: a run-local Builder artifact whose `selected_card_id` matches the
frontend-selected Launchpad card and whose validation blocks non-generatable cards.

Pass/fail criteria: Pass if selected card mismatch is impossible or explicitly blocked.
Fail if the backend can silently use a Builder setup from a different card.

Rollback notes: revert only files changed in this session, not pre-existing dirty files.

Manual test: select two different Launchpad cards and confirm the Builder preview changes
or blocks generation appropriately.

What must not happen: no candidate generation yet; no stale Builder artifact reuse; no
recommendation language.

Suggested commit message: `Add run-local selected-card builder setup guard`.

### Session 03 — Candidate generation bridge

Goal: Create or extend a bridge/API for generating exactly one selected candidate from
the active review and Builder setup.

Files likely to touch: new or extended Next.js API route, Python bridge script or bridge
mode, tests for one-candidate generation request/response.

Files forbidden to touch: root `config.yml`, Python calculation formulas, dependency
major versions, comparison/verdict UI.

Commands to run:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py
    .\.venv\Scripts\python.exe -m pytest tests\test_candidate_generation.py tests\test_no_stale_candidate_generation.py
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build

Expected outputs: `candidate_generation.json` only, scoped to the active review and one
candidate id.

Pass/fail criteria: Pass if one selected candidate can be generated and failures produce
safe structured errors. Fail if multiple candidates are generated or stale weights turn a
failed run into a comparable candidate.

Rollback notes: remove only the bridge/API changes from this session if needed.

Manual test: from a valid Builder setup, trigger the candidate bridge once and inspect
the run directory for exactly one `candidate_generation.json`.

What must not happen: no comparison, no verdict, no candidate zoo, no stale artifact
fallback.

Suggested commit message: `Connect one-candidate generation bridge`.

### Session 04 — Frontend Generate Candidate button

Goal: Enable the Generate Candidate button and connect it to the candidate generation
API.

Files likely to touch: Builder/Hypothesis UI components, frontend review state, frontend
types, candidate API client code.

Files forbidden to touch: root `config.yml`, Python calculation code, comparison/verdict
pages except navigation gating if necessary.

Commands to run:

    git status --short
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py

Expected outputs: UI loading state, safe error state, stored `candidate_generation`
summary, and visible status/weights summary when generated.

Pass/fail criteria: Pass if the button is enabled only for generatable Builder setups and
does not advance to comparison when candidate generation fails. Fail if stale candidate
data remains visible after a new review.

Rollback notes: revert only frontend changes from this session.

Manual test: select a Launchpad card, preview Builder setup, click Generate Candidate,
and verify one candidate status appears.

What must not happen: no comparison or verdict generation; no backend paths or stack
traces shown to the user.

Suggested commit message: `Enable frontend one-candidate generation flow`.

### Session 05 — Current vs Candidate discovery

Goal: Inspect existing comparison commands and required inputs from
`candidate_generation`.

Files likely to touch: this ExecPlan or audit notes only.

Files forbidden to touch: frontend code, Python implementation code, root `config.yml`.

Commands to run:

    git status --short
    rg -n "write_block8_current_vs_candidate_only_outputs|current_vs_candidate|candidate_comparison" src scripts tests
    Get-Content tests\test_block8_current_vs_candidate_boundary.py -TotalCount 220
    Get-Content tests\test_no_stale_candidate_generation.py -TotalCount 140

Expected outputs: exact comparison helper, required candidate ids, freshness constraints,
and stale artifact risks.

Pass/fail criteria: Pass if Session 06 can implement a run-local selected-candidate
comparison. Fail if discovery runs or writes comparisons.

Rollback notes: no implementation changes expected.

Manual test: none; discovery-only.

What must not happen: no comparison generation, no verdict generation, no code edits.

Suggested commit message: not applicable unless documentation notes are committed.

### Session 06 — Current vs Candidate backend connection

Goal: Connect backend comparison for the selected generated candidate only.

Files likely to touch: comparison bridge/API, bridge tests, stale artifact tests.

Files forbidden to touch: root `config.yml`, decision verdict UI, report UI, calculation
formulas.

Commands to run:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_block8_current_vs_candidate_boundary.py tests\test_no_stale_candidate_generation.py
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build

Expected outputs: run-local `current_vs_candidate.json` scoped to the selected generated
candidate.

Pass/fail criteria: Pass if comparison refuses inactive, stale, missing, or mismatched
candidate generation. Fail if verdict is produced unless unavoidable and explicitly
documented.

Rollback notes: revert only Session 06 bridge/API/test changes.

Manual test: generate one candidate and call comparison; inspect selected candidate ids
and lineage.

What must not happen: no tombstone comparison displayed; no winner language; no verdict
as part of this session unless unavoidable.

Suggested commit message: `Connect scoped current-vs-candidate backend flow`.

### Session 07 — Comparison frontend connection

Goal: Render real `current_vs_candidate` on the Comparison page.

Files likely to touch: `frontend/app/comparison/page.tsx`, frontend types, review state,
possibly journey gating.

Files forbidden to touch: root `config.yml`, Python logic, verdict/report pages except
navigation gating if necessary.

Commands to run:

    git status --short
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py

Expected outputs: Comparison page shows what improved, worsened, stayed neutral, or is
unclear, plus turnover/cost/trade-off information.

Pass/fail criteria: Pass if the page renders only active-review comparison and handles
missing/failed comparison safely. Fail if it uses winner language or stale data.

Rollback notes: revert only Session 07 frontend changes.

Manual test: complete candidate generation and comparison, then open Comparison page and
confirm real fields change with different inputs.

What must not happen: no winner language, no recommendation language, no tombstone data.

Suggested commit message: `Render real current-vs-candidate comparison`.


Session 07 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 07 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

Files changed in Session 07:

    frontend/app/comparison/page.tsx
    frontend/components/comparison/TradeoffSummary.tsx
    frontend/lib/reviewState.tsx
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Replaced the normal Comparison page demo-JSON rendering with a client-side active-review flow.
  The page now requires a compare-ready generated candidate, calls
  `/api/portfolio/comparison/generate` with the active `review_id` and selected Launchpad card id,
  and records only the returned active-review comparison summary.
- Added compact `ComparisonResultSummary` state to `frontend/lib/reviewState.tsx`. It stores the
  selected card id, candidate id, comparison status, display metrics, improved/worsened/neutral and
  unclear evidence, turnover, estimated cost, materiality, warnings, and artifact path. New portfolio
  submissions or candidate generations clear this comparison state, and hydration drops comparison
  summaries that no longer match the active generated candidate.
- Updated the comparison rendering to show backend-derived trade-offs, turnover/cost, decision-review
  materiality, and warnings. The copy remains diagnostic-only: no winner language, no recommendation
  language, and no trade instruction.
- Kept the page safe when comparison is missing or fails: it shows an empty state or scrubbed API
  error instead of stale demo content, tombstone data, or raw backend stack traces.

Verification commands and results:

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0. Build included `/api/portfolio/comparison/generate`,
    `/api/portfolio/candidate/generate`, and `/api/portfolio/diagnose` as dynamic routes.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py
    Result: failed in this environment before exercising Session 07 frontend code. One existing
    test used a pytest `tmp_path` under `C:\Users\ShumeikoYe\.cache\codex-pytest-temp`, while its
    fake config loader called `run_dir.relative_to(bridge.PROJECT_ROOT)`, which raises `ValueError`
    when the temp directory is outside the repository.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py --basetemp='tmp\pytest_frontend_bridge'
    Result: passed, 25 tests passed in 2.14 seconds. This keeps pytest temporary files inside the
    repository so the existing fake loader assumption holds.

Manual UI check: completed after Session 07 on 2026-06-08. Port 3000 was still occupied, so a
separate Next.js dev server was started on `127.0.0.1:3107`. Playwright first confirmed the locked
Comparison page renders a safe no-demo state when no active candidate exists. A second Playwright
check injected active review/candidate localStorage and mocked `/api/portfolio/comparison/generate`;
clicking `Run comparison` rendered active backend-shaped comparison evidence, turnover/cost,
materiality, warnings, and diagnostic-only boundary copy. Screenshot evidence:
`output/playwright/session07-comparison-page.png` and
`output/playwright/session07-comparison-active-state.png`. The temporary dev server on port 3107 was
stopped. No live candidate generation, live comparison artifact generation, verdict, or report
generation was executed. Root `config.yml` and Python calculation logic were not modified.

Suggested commit message: `Render real current-vs-candidate comparison`.

### Session 08 — Decision Verdict backend connection

Goal: Generate real `decision_verdict.json` for the selected candidate only.

Files likely to touch: verdict bridge/API, backend tests around no-trade and
evidence-insufficient outcomes.

Files forbidden to touch: root `config.yml`, frontend verdict UI, Python calculation
formulas, dependency manifests.

Commands to run:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict.py tests\test_decision_verdict_contract.py tests\test_decision_verdict_no_trade.py tests\test_decision_verdict_failed_candidate.py
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build

Expected outputs: `decision_verdict.json` scoped to active review and candidate.

Pass/fail criteria: Pass if failed/infeasible candidates cannot become rebalance
verdicts and no-trade/evidence-insufficient are valid. Fail if verdict is treated as a
trading instruction.

Rollback notes: revert only Session 08 bridge/API/test changes.

Manual test: run verdict after comparison and inspect selected candidate id, reasons,
confidence limitations, and no-trade/evidence-insufficient handling.

What must not happen: no stale verdict, no recommendation language, no trading
instruction.

Suggested commit message: `Connect scoped decision verdict backend flow`.


Session 08 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 08 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/comparison/TradeoffSummary.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

Files changed in Session 08:

    scripts/run_review_from_payload.py
    frontend/app/api/portfolio/verdict/generate/route.ts
    tests/test_frontend_review_bridge.py
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Added `write_selected_candidate_verdict()` to the frontend Python bridge. It resolves only safe
  `frontend_review_*` run directories, loads run-local `candidate_generation.json`, validates
  selected Launchpad card lineage, re-checks one-candidate factory scope, and writes run-local
  `decision_verdict.json` through the existing `write_decision_verdict_outputs()` Block 9 helper.
- Added stale comparison guards before verdict writing. If `current_vs_candidate.json` exists, its
  selected candidate ids and comparison rows must be scoped to the selected generated candidate.
  If the candidate generated successfully, missing `current_vs_candidate.json` is rejected; failed
  or infeasible candidates may still produce a non-rebalance failure verdict.
- Added CLI backend path: `scripts/run_review_from_payload.py --run-verdict --review-id
  <frontend_review_id> --selected-card-id <card_id>`. The path writes
  `decision_verdict_result.json` and does not create report or AI commentary artifacts.
- Added Next.js API route `/api/portfolio/verdict/generate` mirroring the existing candidate and
  comparison bridge route pattern. It returns scrubbed failure details and reads the bridge result
  file; it does not change the Verdict page UI.
- Added focused bridge tests for successful run-local Block 9 output, stale comparison candidate
  rejection, and failed-candidate handling that cannot become a rebalance verdict.

Verification commands and results:

    .\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict.py tests\test_decision_verdict_contract.py tests\test_decision_verdict_no_trade.py tests\test_decision_verdict_failed_candidate.py -q
    Result: passed, 13 tests passed in 0.94 seconds.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q
    Result: passed, 28 tests passed in 4.03 seconds.

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0. Build included `/api/portfolio/verdict/generate` as a dynamic
    server route along with the existing diagnosis, candidate, and comparison routes.

Manual test: not run in Session 08; this session is backend/API verdict wiring only and the
frontend Verdict page is intentionally left unchanged for Session 09. No report/AI commentary
generation was executed. Root `config.yml`, Python calculation formulas, dependency manifests, and
frontend verdict UI were not modified.

Suggested commit message: `Connect scoped decision verdict backend flow`.

### Session 09 — Verdict frontend connection

Goal: Render real `decision_verdict` on the Verdict page.

Files likely to touch: `frontend/app/verdict/page.tsx`, frontend types, review state,
journey gating.

Files forbidden to touch: root `config.yml`, Python logic, report UI except navigation
gating if necessary.

Commands to run:

    git status --short
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py

Expected outputs: Verdict page shows why, action framing, evidence quality, and what
would change the verdict.

Pass/fail criteria: Pass if no-trade and evidence-insufficient render as normal outcomes.
Fail if the UI implies trade/rebalance instructions.

Rollback notes: revert only Session 09 frontend changes.

Manual test: open Verdict after a full candidate/comparison/verdict run and verify the
language is decision-support only.

What must not happen: no stale verdict; no hidden fallback to demo text.

Suggested commit message: `Render real decision verdict in frontend`.


Session 09 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 09 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/comparison/TradeoffSummary.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... .cache/
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

Files changed in Session 09:

    frontend/app/verdict/page.tsx
    frontend/lib/reviewState.tsx
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Replaced normal Verdict page demo-JSON rendering with an active-review flow. The page now requires
  one active review, one generated candidate, and a matching current-vs-candidate comparison before
  calling `/api/portfolio/verdict/generate`.
- Added compact `VerdictResultSummary` state to `frontend/lib/reviewState.tsx`, including verdict
  status, confidence, safe headline/explanation/action framing, key evidence, limitations, metrics,
  artifact path, and selected card/candidate lineage. New portfolio, candidate, or comparison changes
  clear stale verdict state, and hydration drops verdict summaries that no longer match the active
  generated candidate.
- Rendered active backend verdict outcomes through `VerdictPanel` plus extra action framing, evidence
  quality, and ...what would change it... cards. No-trade, evidence-insufficient, and failed/infeasible
  candidate outcomes are rendered as normal states.
- Avoided raw trading-instruction wording in the UI by mapping backend verdict ids into
  decision-support copy. The page explicitly says it does not recommend trades, execute trades, or
  identify a best portfolio.

Verification commands and results:

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0. Build included `/api/portfolio/verdict/generate` as a dynamic
    route and `/verdict` as a static page.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q
    Result: failed before exercising bridge assertions because pytest attempted to remove
    `C:\Users\ShumeikoYe\.cache\codex-pytest-temp` and hit `PermissionError: [WinError 5]`.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp='tmp\pytest_frontend_bridge_session09'
    Result: passed, 28 tests passed in 2.35 seconds.

Manual test: not run in Session 09; no dev-server/browser click-through was executed. No Python
logic, root `config.yml`, report UI, dependency manifests, or backend formulas were modified.

Suggested commit message: `Render real decision verdict in frontend`.

### Session 10 — Report / AI Commentary connection

Goal: Connect the Report page to `ai_commentary_context` or a report-ready summary.

Files likely to touch: report API/bridge if needed, `frontend/app/report/page.tsx`,
frontend types, report summary mapping.

Files forbidden to touch: root `config.yml`, PDF designer code, Python calculation
formulas, dependency major versions.

Commands to run:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_ai_commentary_context.py tests\test_no_stale_verdict_in_ai_context.py
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build

Expected outputs: client-ready text summary grounded in allowed artifacts.

Pass/fail criteria: Pass if the Report page explains diagnosis, candidate test,
comparison, verdict, limitations, and next observation points without giving trading
instructions. Fail if it invents facts or uses raw debug JSON as copy.

Rollback notes: revert only Session 10 report/API changes.

Manual test: complete full flow and confirm Report text changes with input and verdict.

What must not happen: no PDF designer work; no trading instruction language; no stale
verdict in AI context.

Suggested commit message: `Connect grounded report commentary flow`.

### Session 11 — End-to-end vertical QA

Goal: Run the complete vertical flow from Input to Report across representative
portfolios.

Files likely to touch: this ExecPlan, QA notes, possibly targeted test fixtures if
failures reveal missing coverage and implementation is explicitly in scope.

Files forbidden to touch: root `config.yml`, unrelated frontend/Python code, dependency
manifests.

Commands to run:

    git status --short
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py

Expected outputs: complete flow works for at least three portfolios: with Cash USD,
without cash, and with TLT replacing BND or similar.

Pass/fail criteria: Pass if outputs change when inputs change and every stage belongs to
the active review/candidate. Fail if frontend shows old result or stale candidate.

Rollback notes: do not clean generated QA runs unless asked.

Manual test: run Input -> Diagnosis -> Evidence -> Hypothesis -> Builder -> Candidate
-> Comparison -> Verdict -> Report for all three portfolios.

What must not happen: no candidate zoo; no stale result reuse; no product copy claiming
recommendations.

Suggested commit message: `Validate frontend backend vertical flow`.

### Session 12 — Error handling and failure states

Goal: Harden user-facing failure states without exposing backend internals.

Files likely to touch: API error wrappers, frontend error components/state, bridge tests.

Files forbidden to touch: root `config.yml`, Python calculation formulas, dependency
major versions.

Commands to run:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build

Expected outputs: safe errors for invalid tickers, weights not 100, Python timeout,
candidate infeasible, missing outputs, stale candidate blocked, and data quality blocker.

Pass/fail criteria: Pass if each failure is recoverable and user-facing text is safe.
Fail if raw stack traces, absolute backend paths, or stale outputs are shown.

Rollback notes: revert only Session 12 error handling changes.

Manual test: trigger each failure condition manually where feasible.

What must not happen: no silent fallback to demo JSON; no path leakage.

Suggested commit message: `Harden vertical flow error states`.

### Session 13 — Storage and state cleanup

Goal: Reduce frontend state risk by storing compact summaries and a `review_id` instead
of large raw JSON forever.

Files likely to touch: frontend review state, frontend types, possibly API result
summary shape.

Files forbidden to touch: root `config.yml`, database migrations, Python calculation
formulas.

Commands to run:

    git status --short
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py

Expected outputs: review state tracks current review id, stage summaries, selected card,
selected candidate, and stage statuses. Raw result access strategy is documented for a
later DB or backend retrieval migration.

Pass/fail criteria: Pass if localStorage size risk is reduced and old review state is
cleared when new input starts. Fail if raw outputs are permanently stored as frontend
state.

Rollback notes: revert only Session 13 state changes.

Manual test: run two reviews and confirm old result does not appear in the new review.

What must not happen: no DB implementation; no stale frontend result.

Suggested commit message: `Compact frontend review state for vertical flow`.

### Session 14 — Visual/product polish pass

Goal: Polish the real flow after all backend connections work.

Files likely to touch: frontend screen components, layout components, copy, small visual
state refinements.

Files forbidden to touch: root `config.yml`, Python code, backend bridge behavior,
dependency major versions.

Commands to run:

    git status --short
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build

Expected outputs: premium Investment Decision Room feel across Input, Diagnosis,
Evidence, Hypothesis, Builder, Candidate, Comparison, Verdict, and Report.

Pass/fail criteria: Pass if polish improves clarity without adding new features or
changing data contracts. Fail if visual work masks missing real data.

Rollback notes: revert only visual changes from this session.

Manual test: click through every screen with a real review and inspect loading, empty,
error, and success states.

What must not happen: no new features; no fake data; no recommendation language.

Suggested commit message: `Polish vertical decision-room frontend`.

### Session 15 — Documentation and demo runbook

Goal: Update docs so a human can run and demo the completed vertical flow.

Files likely to touch: README, frontend README, integration docs, manual test guide,
demo script docs, CHANGELOG.

Files forbidden to touch: root `config.yml`, product code unless a doc command uncovers
an explicitly approved typo-only fix.

Commands to run:

    git status --short
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py

Expected outputs: docs explain commands, run directory strategy, product boundaries,
manual test guide, and demo script.

Pass/fail criteria: Pass if a new user can start the frontend and run the vertical demo
without knowing prior chats. Fail if docs call the candidate a recommendation or ignore
stale artifact risks.

Rollback notes: revert only Session 15 documentation changes.

Manual test: follow the runbook from a fresh terminal.

What must not happen: no product code edits; no dependency upgrades; no commits unless
explicitly instructed.

Suggested commit message: `Document frontend backend vertical integration runbook`.


### Session 16 ... Final validation and handoff summary

Goal: Validate the completed Sessions 10-15 vertical integration work, update final
ExecPlan status, and produce the requested final text result.

Files likely to touch: ExecPlan final notes, possibly CHANGELOG/docs if validation
uncovers a documentation-only correction.

Files forbidden to touch: root `config.yml`, product code, Python code, backend bridge
behavior, dependency manifests, dependency major versions, generated run artifacts unless
explicitly validating their existence.

Commands to run:

    git status --short
    cd frontend
    npm.cmd run typecheck
    npm.cmd run build
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py

Expected outputs: final acceptance notes show whether Sessions 10-16 completed, what
passed, what remains limited, and whether the plan is complete.

Pass/fail criteria: Pass if final validation confirms the frontend/backend vertical flow
contract, focused tests, frontend typecheck/build, three-portfolio QA evidence, safe
state/error handling, docs/runbook, and no forbidden-file changes from Session 16. Fail
if any required gate is missing or contradicted by current evidence.

Rollback notes: revert only Session 16 documentation/final-note changes.

Manual test: inspect the Session 11 run ids and the runbook; no new live browser
click-through is required unless final validation finds a contradiction.

What must not happen: no new features, no backend behavior changes, no product-code
refactors, no commits unless explicitly instructed.

Suggested commit message: `Finalize frontend backend vertical integration plan`.

## Validation and Acceptance

The complete plan is accepted only when:

- The ExecPlan file exists at
  `docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md`.
- Sessions 00-16 are present.
- The plan clearly says the planning step did not implement product code.
- Session 00 has been run and recorded if the user asked to start it.
- The final implemented product can run the vertical flow from Input to Report with
  real backend artifacts.
- Frontend typecheck and build pass.
- Backend bridge tests pass.
- At least three portfolios have been tested: with Cash USD, without cash, and TLT
  replacing BND or similar.
- Outputs change when inputs change.
- No stale candidate, comparison, verdict, or report context is displayed as current.

## Idempotence and Recovery

Most sessions are additive and should be safe to rerun. If a session fails, do not clean
pre-existing dirty files. First record the failure, inspect `git status --short`, and
revert only files changed in that session if the user requests rollback. Generated
run directories under `runs/` are not source of truth and should not be committed.
Do not delete generated runs during the session unless explicitly instructed.

If frontend port 3000 is occupied, use the port Next.js reports or stop the unrelated
process only with explicit user approval. If Python times out, preserve the failed
`review_result.json` and surface a safe timeout message instead of a stack trace.

## Risks and Mitigations

Stale disk artifacts: use run-local directories, review ids, product run metadata, and
lineage checks. Never read global tombstones as current results.

Global candidate folders: scope candidate generation to one selected candidate and one
run-local config. Reject old weights if the factory step failed or lineage is missing.

Long Python runtime: keep API timeout explicit, show loading state, and return safe
timeout errors.

Market data/cache dependency: surface data quality blockers as valid product outcomes.
Do not fake successful outputs.

NaN/Infinity JSON sanitation: preserve existing API sanitation and add tests where new
endpoints parse Python output.

localStorage size: store compact summaries and `review_id`, not full raw artifacts
forever.

Windows path issues: use `npm.cmd`, `.\.venv\Scripts\python.exe`, `path.join`, and
run-local relative paths. Scrub absolute backend paths in user-facing errors.

Port 3000 occupied: document the actual dev server URL and avoid assuming one port.

Concurrent runs: use timestamp/UUID run ids and do not use singleton frontend state for
backend artifact lookup.

Invalid tickers: validate input and return recoverable user-facing errors.

Real cash mapping: preserve `Cash USD` bridge behavior and verify with tests.

Frontend showing old result: clear downstream stage state when portfolio input or
selected card changes.

## Interfaces and Dependencies

Frontend API routes must run in Node.js runtime, not Edge, because they spawn Python or
read run-local files. Python bridge scripts must accept explicit paths and must write
JSON result files that the API can parse. Backend stage responses should include:

- `review_id`
- `status`
- `stage`
- selected `card_id` or `candidate_id` where relevant
- compact output summary
- safe `error` and `details` fields for failures

Do not introduce a database in this plan. Prepare the state shape so a later database
migration can store review metadata and artifact pointers.

## Artifacts and Notes

Initial pre-existing dirty files before this ExecPlan was created:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

Files changed by plan creation:

    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Session 00 audit notes, 2026-06-08:

Pre-existing dirty files at Session 00 start, excluding this new ExecPlan:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

Files changed in Session 00:

    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Verification commands and results:

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0. Build included /api/portfolio/diagnose as a dynamic
    server route and Diagnosis, Evidence, Hypothesis, Comparison, Verdict, and Report
    pages as static pages.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py
    Result: passed, 14 tests passed in 0.17 seconds.

Current flow verification note: no live browser/API diagnosis run was executed in
Session 00 because the session is audit-only and must avoid additional generated
artifacts where possible. The current route/page build and bridge contract tests passed,
which is the non-mutating baseline verification for the current Diagnosis, Evidence,
and Hypothesis integration state. No candidate generation was run.

Session 01 discovery notes, 2026-06-08:

Pre-existing dirty files at Session 01 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

Files changed in Session 01:

    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Discovery commands and results:

    git status --short
    Result: passed, exit code 0. Dirty files listed above.

    Get-Content scripts\generate_candidate_from_builder_setup.py -TotalCount 420
    Result: passed, exit code 0. The script reads one Builder artifact, extracts
    `candidate_setup`, runs one factory candidate with `--candidates`, writes one
    `candidate_generation.json`, and blocks stale weights from converting a failed
    factory attempt into a comparable candidate.

    Get-Content scripts\run_blocks_5_to_9_vertical_flow.py -TotalCount 540
    Result: passed, exit code 0. The script already demonstrates diagnosis -> one
    selected Builder -> one candidate -> comparison -> verdict -> AI commentary, but
    it targets configured output folders, not the current frontend API contract.

    rg -n "candidate_generation|portfolio_alternatives_builder|selected_card|current_vs_candidate" scripts src tests
    Result: passed, exit code 0. Relevant references found in candidate-generation,
    builder, current-vs-candidate, verdict, AI commentary, validation, bridge, and
    vertical-flow tests.

Additional focused inspection:

    Get-Content src\candidate_generation.py -TotalCount 260
    Result: passed, exit code 0. `candidate_setup_from_builder_document()` requires
    `can_generate_candidate is True`, while `build_candidate_generation_document()`
    preserves `source_card_id`, `candidate_setup_id`, method variant, comparability
    handoff, and diagnostic-only guardrails.

    Get-Content scripts\run_review_from_payload.py -TotalCount 280
    Result: passed, exit code 0. The frontend bridge currently supports diagnosis
    modes only and writes isolated `runs/frontend_review_*` directories.

Session 01 implementation path for Session 02:

1. Add or extend a backend helper/bridge path that receives `review_id` and
   `selected_card_id`, loads the active run's `analysis_subject/candidate_launchpad.json`,
   and builds or refreshes exactly one
   `analysis_subject/portfolio_alternatives_builder.json` for that selected card.
2. Validate that `portfolio_alternatives_builder.selected_card_id`,
   `builder_prefill.source_card_id`, and `candidate_setup.source_card_id` all equal the
   selected frontend card before returning a generatable Builder setup.
3. Reject non-generatable cards and missing/mismatched cards with structured safe
   errors. Do not silently reuse an older Builder document from another card.
4. Keep Session 02 free of candidate generation; only prepare the selected-card Builder
   setup and focused tests.

Stale artifact risks listed for later sessions:

- Default `scripts/generate_candidate_from_builder_setup.py` paths still point to
  `Main portfolio/...`; frontend integration must pass explicit run-local paths and
  config paths.
- `skipped_existing` is currently treated as a successful factory status. This is
  acceptable only when lineage/config/output directory match the active review; later
  candidate generation bridge work must guard that boundary.
- `run_blocks_5_to_9_vertical_flow.py` removes stale artifacts in a configured output
  directory, but the frontend path should avoid touching global folders and should
  operate inside `runs/frontend_review_*`.
- The current diagnosis bridge has no selected-card field in the response contract, so
  Session 02 needs an explicit selected-card request/response boundary before Block 7.

Manual test: none; Session 01 is discovery-only.

Verification not run: frontend typecheck/build and backend pytest were not run because
Session 01 is discovery-only and made no product-code changes.

Session 02 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 02 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

Files changed in Session 02:

    scripts/run_review_from_payload.py
    tests/test_frontend_review_bridge.py
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Added `prepare_selected_builder_setup()` to the frontend Python bridge. It resolves an
  existing `frontend_review_*` run directory safely, reads run-local
  `analysis_subject/candidate_launchpad.json`, selects exactly the frontend-selected
  `selected_card_id`, rebuilds `portfolio_alternatives_builder.json`, and returns a
  structured `builder_setup` result.
- Added `_assert_selected_builder_lineage()` so stale or mismatched Builder artifacts are
  rejected unless `portfolio_alternatives_builder.selected_card_id`,
  `builder_prefill.source_card_id`, and `candidate_setup.source_card_id` all equal the
  selected Launchpad card.
- Added a CLI backend path: `scripts/run_review_from_payload.py --prepare-builder
  --review-id <frontend_review_id> --selected-card-id <card_id>`. This path only prepares
  Builder setup; it does not generate candidates, run the candidate factory, write
  weights, compare portfolios, or write verdict artifacts.
- Added focused bridge tests for successful selected-card Builder rebuild, missing-card
  rejection, explicit lineage mismatch rejection, and review-id path traversal rejection.

Verification commands and results:

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py
    Result: passed, 18 tests passed in 0.38 seconds.

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0.

Manual test: not run in Session 02; this session is backend Builder handoff only and no
candidate generation was allowed.

Suggested commit message: `Add selected-card Builder setup bridge`.


Session 03 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 03 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

Files changed in Session 03:

    scripts/run_review_from_payload.py
    tests/test_frontend_review_bridge.py
    frontend/app/api/portfolio/candidate/generate/route.ts
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Added `generate_selected_candidate()` to the frontend Python bridge. It resolves only
  safe `frontend_review_*` run ids, requires run-local `input.yml` and the selected
  `analysis_subject/portfolio_alternatives_builder.json`, reuses the Session 02 Builder
  lineage guard, and delegates to existing `generate_candidate_from_builder_setup()`.
- Candidate generation is scoped to run-local paths: Builder input under
  `analysis_subject/`, output at run root `candidate_generation.json`, factory summary
  at run root `candidate_factory_run.json`, and config at run root `input.yml`.
- Added Candidate Generation lineage checks so `candidate.source_card_id`,
  `source_builder_setup.source_card_id`, and comparison handoff candidate id must match
  the selected card/candidate. Multi-candidate factory summaries are rejected.
- Added CLI backend path: `scripts/run_review_from_payload.py --generate-candidate
  --review-id <frontend_review_id> --selected-card-id <card_id>`. This path does not
  create comparison or verdict artifacts.
- Added Next.js API route `/api/portfolio/candidate/generate` for backend-only candidate
  generation. The Generate Candidate button remains intentionally unwired until Session
  04.
- Added focused tests for run-local candidate generation paths, Builder mismatch
  rejection, Candidate Generation lineage mismatch rejection, and multi-candidate factory
  summary rejection.

Verification commands and results:

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q
    Result: passed, 22 tests passed in 0.59 seconds.

    .\.venv\Scripts\python.exe -m pytest tests\test_candidate_generation.py tests\test_no_stale_candidate_generation.py -q
    Result: not run successfully because historical missing candidate-generation test file name does not
    exist in this working tree (`ERROR: file or directory not found`).

    .\.venv\Scripts\python.exe -m pytest tests\test_candidate_generation_from_builder_setup.py tests\test_candidate_generation_method_mapping.py tests\test_candidate_generation_no_recommendation_boundary.py tests\test_candidate_generation_failed_infeasible.py tests\test_no_stale_candidate_generation.py -q
    Result: passed, 21 tests passed in 9.66 seconds.

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0. Build included `/api/portfolio/candidate/generate` and
    `/api/portfolio/diagnose` as dynamic server routes.

Manual test: not run in Session 03; the frontend button is intentionally left disabled
until Session 04. No comparison, verdict, or candidate-zoo command was run.

Suggested commit message: `Connect one-candidate generation bridge`.


Session 04 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 04 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

Files changed in Session 04:

    frontend/app/hypothesis/page.tsx
    frontend/lib/reviewState.tsx
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Enabled the Hypothesis page Generate Candidate button for the selected card only
  when the run has a `review_id`, the backend Builder document matches
  `selected_card_id`, and the Builder setup reports it can generate a candidate.
- Wired the button to the existing `/api/portfolio/candidate/generate` route with the
  active `review_id` and selected Launchpad `card_id`. The page does not navigate to
  comparison and does not request comparison or verdict generation.
- Added loading and safe error states to the Builder panel. Client-visible errors use
  the API response message/details and do not expose backend stack traces or absolute
  paths beyond the API's existing scrubbed response.
- Added compact `candidateGeneration` state to `frontend/lib/reviewState.tsx`, storing
  selected card id, candidate id, generation status, compare-readiness, result path,
  and returned weights. New portfolio submissions clear this state so stale candidate
  data is not shown after a new review.
- The Builder panel displays generated candidate status and a compact weights summary
  only when the stored candidate summary matches the currently selected Launchpad card.

Verification commands and results:

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0. Build included `/api/portfolio/candidate/generate` and
    `/api/portfolio/diagnose` as dynamic server routes.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py
    Result: passed, 22 tests passed in 0.50 seconds.

Manual test: not run in Session 04; no dev server/browser click-through was executed.
No comparison, verdict, or candidate-zoo command was run. Root `config.yml` and Python
calculation code were not modified.

Suggested commit message: `Enable frontend one-candidate generation flow`.


Session 10 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 10 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/comparison/TradeoffSummary.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

    Note: `git status --short` also warned that `.cache/codex-pytest-temp/` could not
    be opened due to permission denial.

Files changed in Session 10:

    scripts/run_review_from_payload.py
    frontend/app/api/portfolio/report/generate/route.ts
    frontend/app/report/page.tsx
    tests/test_frontend_review_bridge.py
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Added `write_selected_report_context()` to the frontend Python bridge. It resolves only
  safe `frontend_review_*` run ids, requires active `candidate_generation.json` and
  `decision_verdict.json`, re-checks selected-card lineage, re-checks one-candidate factory
  scope, validates `current_vs_candidate.json` scope when the generated candidate is
  comparable, and refuses stale verdict candidates.
- Added CLI backend path:
  `scripts/run_review_from_payload.py --run-report-context --review-id <frontend_review_id>
  --selected-card-id <card_id>`. This writes run-local `ai_commentary_context.json` and
  `report_commentary_result.json`; it does not regenerate PDFs, change formulas, call an
  LLM, or create trading instructions.
- Added Next.js API route `/api/portfolio/report/generate` following the existing bridge
  transport pattern.
- Replaced normal Report page demo-JSON rendering with an active-review flow. The page now
  requires a matching active verdict, calls the report API, maps
  `client_explanation_draft.sentences` into a client-ready preview, and shows grounding path,
  timestamp, warnings, and an explicit decision-support-only boundary.
- Added focused bridge tests for successful grounded post-compare report context creation and
  stale verdict rejection.

Verification commands and results:

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp='tmp\pytest_frontend_bridge_session10'
    Result: passed, 30 tests passed in 4.10 seconds.

    .\.venv\Scripts\python.exe -m pytest tests\test_ai_commentary_context.py tests\test_no_stale_verdict_in_ai_context.py -q --basetemp='tmp\pytest_ai_context_session10'
    Result: passed, 16 tests passed in 10.64 seconds.

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0. Build included `/api/portfolio/report/generate` as a
    dynamic route and `/report` as a static page.

Manual test: not run in Session 10; no dev-server/browser click-through was executed.
Root `config.yml`, PDF designer code, Python calculation formulas, and dependency
manifests were not modified.

Suggested commit message: `Connect grounded report commentary flow`.


Session 11 QA notes, 2026-06-08:

Pre-existing dirty files at Session 11 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/comparison/TradeoffSummary.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

    Note: `git status --short` also warned that `.cache/codex-pytest-temp/` could not
    be opened due to permission denial.

Files changed in Session 11:

    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    runs/frontend_review_20260608T185306Z_ded63f33/ (generated QA run; full vertical)
    runs/frontend_review_20260608T185554Z_b4f0c6fd/ (generated QA run; partial/stopped)
    runs/frontend_review_20260608T185848Z_78fe6128/ (generated QA run; full vertical)
    runs/frontend_review_20260608T190213Z_e916d308/ (generated QA run; full vertical)
    minimum cvar constrained portfolio/baseline_weights_metadata.json
    minimum cvar constrained portfolio/summary.json
    minimum cvar constrained portfolio/weights.json
    minimum cvar constrained portfolio/builder_runtime_timing.json
    minimum cvar constrained portfolio/candidate_manifest.json
    minimum cvar constrained portfolio/candidate_weights_build.json

QA summary:

- Completed frontend verification gates required by Session 11.
- Completed three full backend vertical flows:
  - `with_cash_usd`: `VOO` 50%, `BND` 35%, `Cash USD` 15%; review id
    `frontend_review_20260608T185306Z_ded63f33`; selected card
    `launchpad_01_improve_crisis_resilience`; candidate
    `minimum_cvar_constrained`.
  - `without_cash`: `VOO` 60%, `BND` 30%, `GLD` 10%; review id
    `frontend_review_20260608T185848Z_78fe6128`; selected card
    `launchpad_01_compare_against_simple_benchmark`; candidate `equal_weight`.
  - `tlt_instead_of_bnd`: `VOO` 55%, `TLT` 35%, `GLD` 10%; review id
    `frontend_review_20260608T190213Z_e916d308`; selected card
    `launchpad_01_compare_against_simple_benchmark`; candidate `equal_weight`.
- Each completed run produced, in order, run-local `review_result.json`,
  `builder_setup_result.json`, `candidate_generation_result.json`,
  `current_vs_candidate_result.json`, `decision_verdict_result.json`,
  `report_commentary_result.json`, and `ai_commentary_context.json`.
- The second planned backend vertical (`VOO` 60%, `BND` 30%, `GLD` 10%; no cash)
  started as `frontend_review_20260608T185554Z_b4f0c6fd` but ran long during
  `diagnosis_plus_problem` backend orchestration. The wrapper was interrupted and the
  remaining QA processes for that run were stopped explicitly. This was a QA-wrapper
  limitation, not final product coverage; direct PowerShell reruns completed the
  no-cash and TLT-substitution matrix rows afterward.
- The first full vertical used `--force-candidate`, which generated side-effect changes
  in the generated candidate output folder `minimum cvar constrained portfolio/`.
  These are generated QA artifacts, not source-code changes; they were not cleaned or
  reverted in Session 11.

Verification commands and results:

    git status --short
    Result: passed, exit code 0. Dirty files listed above; permission warning for
    `.cache/codex-pytest-temp/`.

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp='tmp\pytest_frontend_bridge_session11'
    Result: passed, 30 tests passed in 4.34 seconds.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0. Build included all vertical API routes:
    `/api/portfolio/diagnose`, `/api/portfolio/candidate/generate`,
    `/api/portfolio/comparison/generate`, `/api/portfolio/verdict/generate`, and
    `/api/portfolio/report/generate`.

    .\.venv\Scripts\python.exe scripts\run_review_from_payload.py --payload <temp with_cash_usd.json> --mode diagnosis_plus_problem --timeout-seconds 900
    Result: passed, wrote
    `runs/frontend_review_20260608T185306Z_ded63f33/review_result.json`.

    .\.venv\Scripts\python.exe scripts\run_review_from_payload.py --prepare-builder --review-id frontend_review_20260608T185306Z_ded63f33 --selected-card-id launchpad_01_improve_crisis_resilience
    Result: passed, wrote
    `runs/frontend_review_20260608T185306Z_ded63f33/builder_setup_result.json`.

    .\.venv\Scripts\python.exe scripts\run_review_from_payload.py --generate-candidate --review-id frontend_review_20260608T185306Z_ded63f33 --selected-card-id launchpad_01_improve_crisis_resilience --force-candidate --factory-execution-mode fast
    Result: passed, wrote
    `runs/frontend_review_20260608T185306Z_ded63f33/candidate_generation_result.json`.

    .\.venv\Scripts\python.exe scripts\run_review_from_payload.py --run-comparison --review-id frontend_review_20260608T185306Z_ded63f33 --selected-card-id launchpad_01_improve_crisis_resilience
    Result: passed, wrote
    `runs/frontend_review_20260608T185306Z_ded63f33/current_vs_candidate_result.json`.

    .\.venv\Scripts\python.exe scripts\run_review_from_payload.py --run-verdict --review-id frontend_review_20260608T185306Z_ded63f33 --selected-card-id launchpad_01_improve_crisis_resilience
    Result: passed, wrote
    `runs/frontend_review_20260608T185306Z_ded63f33/decision_verdict_result.json`.

    .\.venv\Scripts\python.exe scripts\run_review_from_payload.py --run-report-context --review-id frontend_review_20260608T185306Z_ded63f33 --selected-card-id launchpad_01_improve_crisis_resilience
    Result: passed, wrote
    `runs/frontend_review_20260608T185306Z_ded63f33/report_commentary_result.json`.

    Direct PowerShell rerun for `without_cash` (`VOO`/`BND`/`GLD`) using
    `scripts/run_review_from_payload.py` diagnosis_plus_problem, prepare-builder,
    generate-candidate, run-comparison, run-verdict, and run-report-context.
    Result: passed, final report status `completed`, candidate id `equal_weight`,
    review id `frontend_review_20260608T185848Z_78fe6128`.

    Direct PowerShell rerun for `tlt_instead_of_bnd` (`VOO`/`TLT`/`GLD`) using
    `scripts/run_review_from_payload.py` diagnosis_plus_problem, prepare-builder,
    generate-candidate, run-comparison, run-verdict, and run-report-context.
    Result: passed, final report status `completed`, candidate id `equal_weight`,
    review id `frontend_review_20260608T190213Z_e916d308`.

    Artifact completeness check for all three Session 11 review ids.
    Result: passed; no missing `review_result.json`, `builder_setup_result.json`,
    `candidate_generation_result.json`, `current_vs_candidate_result.json`,
    `decision_verdict_result.json`, `report_commentary_result.json`, or
    `ai_commentary_context.json` files.

Manual test / QA limitation:

The planned three-portfolio backend vertical matrix completed through backend artifacts.
No live browser click-through was executed. One early wrapper run for the no-cash case
was stopped after it ran long, then replaced by direct PowerShell stage-by-stage checks.
No root `config.yml`, frontend source code, Python source code, or dependency manifest
was modified by Session 11. Generated candidate output files under
`minimum cvar constrained portfolio/` changed as a side effect of the first
`minimum_cvar_constrained` candidate generation run.

Suggested commit message: `Validate frontend backend vertical flow`.


Session 12 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 12 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/comparison/TradeoffSummary.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    M "minimum cvar constrained portfolio/baseline_weights_metadata.json"
    M "minimum cvar constrained portfolio/summary.json"
    M "minimum cvar constrained portfolio/weights.json"
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... "minimum cvar constrained portfolio/builder_runtime_timing.json"
    ...... "minimum cvar constrained portfolio/candidate_manifest.json"
    ...... "minimum cvar constrained portfolio/candidate_weights_build.json"
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

    Note: `git status --short` also warned that `.cache/codex-pytest-temp/` could not
    be opened due to permission denial.

Files changed in Session 12:

    scripts/run_review_from_payload.py
    tests/test_frontend_review_bridge.py
    frontend/app/api/portfolio/diagnose/route.ts
    frontend/app/api/portfolio/candidate/generate/route.ts
    frontend/app/api/portfolio/comparison/generate/route.ts
    frontend/app/api/portfolio/verdict/generate/route.ts
    frontend/app/api/portfolio/report/generate/route.ts
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Added bridge-side `scrub_failure_text()` and safe failure detail codes so failed
  `review_result.json` / stage result JSON keeps the recoverable reason but hides Python
  tracebacks and local absolute paths in `error`, `details`, `stdout_tail`, and
  `stderr_tail`.
- Hardened all vertical frontend API routes to scrub backend-returned `error` and
  `details` before sending responses to the client. This covers diagnosis, candidate
  generation, comparison, verdict, and report commentary routes.
- Added focused bridge tests for invalid input detail codes, traceback/path scrubbing,
  sanitized backend log tails, and missing-output failure results.
- Did not modify root `config.yml`, Python calculation formulas, dependency manifests,
  dependency major versions, or generated QA run directories.

Failure states covered by this session:

- invalid frontend payload / weights not accepted by the bridge as validation failures;
- backend timeout remains a safe timeout code/message path;
- missing expected backend outputs are reported as `missing_backend_output` without local
  path leakage;
- stale lineage / blocked stage errors remain recoverable stage failures without
  tracebacks;
- candidate infeasible / backend candidate failure remains a stage failure rather than a
  stale-output fallback;
- backend stderr/stdout tracebacks and absolute paths are scrubbed before client display.

Verification commands and results:

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp='tmp\pytest_frontend_bridge_session12'
    Result: passed, 33 tests passed in 3.63 seconds.

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0. Build included all vertical API routes:
    `/api/portfolio/diagnose`, `/api/portfolio/candidate/generate`,
    `/api/portfolio/comparison/generate`, `/api/portfolio/verdict/generate`, and
    `/api/portfolio/report/generate`.

Manual test: not run in Session 12; no live browser click-through was executed. Failure
state coverage was verified through focused bridge tests and frontend compile/build
checks.

Suggested commit message: `Harden vertical flow error states`.

Session 13 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 13 start:

    M .gitignore
    M CHANGELOG.md
    M frontend/README.md
    M frontend/app/comparison/page.tsx
    M frontend/app/diagnosis/page.tsx
    M frontend/app/evidence/page.tsx
    M frontend/app/hypothesis/page.tsx
    M frontend/app/layout.tsx
    M frontend/app/report/page.tsx
    M frontend/app/verdict/page.tsx
    M frontend/components/comparison/TradeoffSummary.tsx
    M frontend/components/hypothesis/HypothesisCard.tsx
    M frontend/components/layout/Sidebar.tsx
    M frontend/components/layout/TopJourneyProgress.tsx
    M frontend/components/portfolio/PortfolioInputTable.tsx
    M frontend/lib/journey.ts
    M frontend/lib/types.ts
    M "minimum cvar constrained portfolio/baseline_weights_metadata.json"
    M "minimum cvar constrained portfolio/summary.json"
    M "minimum cvar constrained portfolio/weights.json"
    ...... docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md
    ...... frontend/app/api/
    ...... frontend/components/layout/JourneyAdvanceActions.tsx
    ...... frontend/components/layout/JourneyGate.tsx
    ...... frontend/data/instrumentUniverse.ts
    ...... frontend/lib/reviewState.tsx
    ...... "minimum cvar constrained portfolio/builder_runtime_timing.json"
    ...... "minimum cvar constrained portfolio/candidate_manifest.json"
    ...... "minimum cvar constrained portfolio/candidate_weights_build.json"
    ...... runs/
    ...... scripts/run_review_from_payload.py
    ...... tests/test_frontend_review_bridge.py

    Note: `git status --short` also warned that `.cache/codex-pytest-temp/` could not
    be opened due to permission denial.

Files changed in Session 13:

    frontend/lib/reviewState.tsx
    frontend/app/evidence/page.tsx
    frontend/app/hypothesis/page.tsx
    frontend/app/comparison/page.tsx
    frontend/app/verdict/page.tsx
    frontend/app/report/page.tsx
    frontend/README.md
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Changed frontend persistence so `pmri.activeReview.v2` keeps compact state only:
  `reviewId`, portfolio input, diagnosis/evidence/launchpad/builder summaries, selected
  card/candidate, comparison/verdict summaries, stage statuses, and safe failure state.
- Stopped persisting full `review_result.json` into separate `pmri.reviewResult.*`
  localStorage keys. The raw result may remain in memory for the current tab immediately
  after an API response, but it is not written to or restored from browser storage.
- Added hydration/write cleanup for legacy `pmri.reviewResult.*` keys so old raw browser
  copies are removed automatically.
- Added compact Evidence, Launchpad card, and Builder setup summaries derived from the
  backend outputs. Evidence and Hypothesis pages can render after reload without raw
  `outputs.*` in browser state.
- Updated Comparison, Verdict, Report, and Hypothesis pages to use compact `reviewId`
  rather than requiring `activeReview.reviewResult.review_id`.
- New portfolio input and review error paths continue to clear candidate/comparison/verdict
  state, preventing stale downstream stage summaries from appearing for a new input.
- Updated `../../frontend/README.md` to document the compact localStorage contract and future
  `reviewId`-based raw access strategy.
- Did not modify root `config.yml`, database migrations, Python calculation formulas,
  dependency manifests, dependency major versions, or generated run folders.

Verification commands and results:

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: passed, exit code 0.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp='tmp\pytest_frontend_bridge_session13'
    Result: passed, 33 tests passed in 3.46 seconds.

Manual test: not run in Session 13; no live browser click-through was executed. The
stale-state behavior was reviewed in code: new input/error paths clear downstream stage
summaries, and persisted hydration no longer restores raw review JSON.

Suggested commit message: `Compact frontend review state for vertical flow`.


Session 14 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 14 start were the already accumulated Session 10-13
working-tree changes, generated run outputs, and generated candidate side effects shown
by `git status --short`; `.cache/codex-pytest-temp/` still emitted a permission warning.

Files changed in Session 14:

    frontend/styles/globals.css
    frontend/components/layout/PageHeader.tsx
    frontend/components/layout/TopJourneyProgress.tsx
    frontend/components/layout/Sidebar.tsx
    frontend/components/portfolio/PortfolioInputTable.tsx
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Added a refined glass/texture treatment to cards and the app background without changing
  layout data contracts or adding features.
- Upgraded `PageHeader` hierarchy into a premium decision-room header with explicit
  evidence-first / one-hypothesis / no-trade boundary copy.
- Polished the sticky workflow rail to show sealed-stage count and current stage context.
- Added a compact sidebar operating-mode reminder: current portfolio first, diagnostic
  candidate tests only, no orders.
- Improved Portfolio Input loading copy to explain that X-Ray, Stress, Problem
  Classification, and Launchpad evidence are being prepared, with no candidate or trade
  action created at that step.
- Did not modify root `config.yml`, Python code, backend bridge behavior, data contracts,
  dependency manifests, or dependency major versions.

Verification commands and results:

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    npm.cmd run build
    Result: first two attempts hit generated `.next`/Next worker cache errors; after
    removing only generated `frontend/.next` and rerunning with `NEXT_PRIVATE_BUILD_WORKER=1`,
    passed, exit code 0.

Manual test: no live browser click-through was executed in Session 14. The polish was
limited to visual/copy state refinements and verified by typecheck/build.

Suggested commit message: `Polish vertical decision-room frontend`.


Session 15 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 15 start were the already accumulated Session 10-14
working-tree changes, generated run outputs, generated candidate side effects, and the
`.cache/codex-pytest-temp/` permission warning shown by `git status --short`.

Files changed in Session 15:

    README.md
    frontend/README.md
    docs/demo/README.md
    docs/demo/frontend_backend_vertical_runbook.md
    CHANGELOG.md
    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Added a human operator runbook for the live frontend/backend vertical flow from
  Portfolio Input through grounded Report commentary.
- Documented verification commands, frontend startup, sample demo portfolios, run-local
  `runs/frontend_review_*` artifact strategy, expected artifact chain, stale-artifact
  recovery, and compact browser state boundaries.
- Linked the runbook from root README, frontend README, and the demo docs index.
- Added CHANGELOG coverage for the new runbook.
- Did not modify product code, Python code, root `config.yml`, dependency manifests,
  dependency versions, or generated run folders during Session 15.

Verification commands and results:

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    $env:NEXT_PRIVATE_BUILD_WORKER='1'; npm.cmd run build
    Result: passed, exit code 0.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp='tmp\pytest_frontend_bridge_session15'
    Result: passed, 33 tests passed in 2.93 seconds.

Manual test: no fresh browser click-through was executed in Session 15; the runbook now
contains the manual click-through path for a human operator to follow from a fresh
terminal.

Suggested commit message: `Document frontend backend vertical integration runbook`.


Session 16 implementation notes, 2026-06-08:

Pre-existing dirty files at Session 16 start were the accumulated Session 10-15
working-tree changes, generated run outputs, generated candidate side effects, and the
`.cache/codex-pytest-temp/` permission warning shown by `git status --short`.

Files changed in Session 16:

    docs/exec_plans/2026-06-08_frontend_backend_vertical_integration_plan.md

Implementation summary:

- Performed final validation only; no new features, product-code refactors, backend
  behavior changes, Python changes, root `config.yml` changes, dependency changes, or
  generated artifact rewrites were made.
- Re-ran frontend typecheck/build and focused bridge tests.
- Re-inspected the three Session 11 review ids: `frontend_review_20260608T185306Z_ded63f33`,
  `frontend_review_20260608T185848Z_78fe6128`, and
  `frontend_review_20260608T190213Z_e916d308`.
- Confirmed each review directory contains `review_result.json`,
  `builder_setup_result.json`, `candidate_generation_result.json`,
  `current_vs_candidate_result.json`, `decision_verdict_result.json`,
  `report_commentary_result.json`, and `ai_commentary_context.json`.
- Confirmed each inspected chain has `comparison_status=completed`,
  `verdict_status=completed`, `report_status=completed`, `grounding_phase=post_compare`,
  and `guardrails.does_not_execute_trades=true`.

Verification commands and results:

    git status --short
    Result: passed, exit code 0; warning persisted for `.cache/codex-pytest-temp/` permission denial.

    cd frontend
    npm.cmd run typecheck
    Result: passed, exit code 0.

    cd frontend
    $env:NEXT_PRIVATE_BUILD_WORKER='1'; npm.cmd run build
    Result: passed, exit code 0.

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp='tmp\pytest_frontend_bridge_session16'
    Result: passed, 33 tests passed in 3.49 seconds.

    Session 11 artifact inspection for three review ids
    Result: passed; no required artifacts missing, all comparison/verdict/report stages completed,
    `ai_commentary_context.json` is post-compare grounded, and no-trade execution guardrail is true.

Manual test: no new live browser click-through was executed in Session 16. Session 11
provided backend vertical artifact QA for three portfolios; Session 15 added the human
manual click-through runbook for future operators.

Outcome: Sessions 10-16 are complete. The frontend/backend vertical integration plan is
implemented and validated with documented limitations.

Suggested commit message: `Finalize frontend backend vertical integration plan`.

## Next Immediate Session

No next implementation session remains. Sessions 10-16 are complete; after Session 16 the plan is considered completed.
