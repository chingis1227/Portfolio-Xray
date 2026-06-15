# Architecture Debt Roadmap for Staged Review Runtime, Frontend State, and Legacy Runners

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. Any agent implementing or revising this
plan must keep it self-contained and update it after each session. This roadmap was created as
Session 6 of `docs/exec_plans/2026-06-14_stabilize_run_diagnostics_high_risk_debt_plan.md`.

## Purpose / Big Picture

Portfolio MRI currently works through a mixed architecture: the website calls Next.js route
handlers, Next.js calls FastAPI, and FastAPI still reuses some CLI/file-driven helpers to run the
portfolio review and write run-local artifacts. That is acceptable for compatibility, but it makes
errors harder to classify, makes local route version mismatches easier to create, and leaves very
large frontend modules carrying too many responsibilities.

After this roadmap is implemented, a user should see the same Portfolio MRI product flow, but the
runtime should be easier to test and safer to evolve. FastAPI should call reusable service/module
functions directly where safe instead of shelling out to scripts for normal staged review work.
Frontend adapters should be split into small, testable modules without changing public routes. Root
legacy runner wrappers should have explicit retirement criteria so future cleanup does not remove
useful compatibility paths prematurely.

This plan is intentionally not a broad refactor to perform in one session. It decomposes the debt
into safe tracks that future chats can pick up independently.

## Progress

- [x] (2026-06-15 00:30Z) Roadmap created with three tracks: staged API/subprocess boundary, large frontend module seams, and legacy wrapper retirement criteria.
- [x] (2026-06-15 12:00Z) Track 1 discovery refreshed: staged FastAPI still enters `scripts/run_review_from_payload.py`, which still owns the `run_report.py` subprocess boundary.
- [ ] Track 1 implementation: replace the normal staged diagnosis subprocess with direct service calls where tests prove parity.
- [x] (2026-06-15 12:00Z) Track 2 discovery: selected pure low-risk seams for staged safe-error formatting and server-only FastAPI error scrubbing.
- [x] (2026-06-15 12:00Z) Track 2 implementation slice 1: moved staged safe-error formatting to `frontend/lib/review/stagedSafeError.ts` and moved FastAPI error scrubbing/mapping to `frontend/lib/server/fastapi/errors.ts`.
- [x] (2026-06-15 12:00Z) Track 3 discovery: classified root `run_*.py` commands in `docs/runtime_entrypoints.md` without deleting or hiding wrappers.
- [ ] Track 3 implementation: add retirement/deprecation gates only after docs, tests, and operator commands prove no current path depends on the wrapper.

## Surprises & Discoveries

- Observation: The normal staged FastAPI implementation already imports `scripts.run_review_from_payload` helpers directly in `src/api/reviews.py`, but that helper still runs `run_report.py` through `subprocess.run` for diagnosis materialization.
  Evidence: `src/api/reviews.py` imports `run_from_payload` and related helpers from `scripts/run_review_from_payload.py`; `scripts/run_review_from_payload.py` imports `subprocess` and defines `DEFAULT_TIMEOUT_SECONDS`.
- Observation: The Next.js FastAPI bridge is now a large adapter that mixes validation, transport, lineage checks, public response mapping, stale-route errors, and recovery.
  Evidence: `frontend/lib/server/fastapiBridge.ts` is about 1103 lines.
- Observation: The frontend review-state provider mixes browser storage, staged progress, Supabase persistence, summary compaction, display-model construction, and action recorders.
  Evidence: `frontend/lib/reviewState.tsx` is about 3388 lines.
- Observation: Root legacy wrappers already exist and delegate into `legacy/runners/`, but some wrapper docstrings still contain encoding-damaged punctuation in existing text.
  Evidence: `run_optimization.py` and `run_equal_weight.py` begin with a legacy wrapper banner and delegate to matching files under `legacy/runners/`. Do not normalize wrapper text in an unrelated architecture refactor unless that wrapper file is intentionally touched.
- Observation: The first frontend extraction can be pure and behavior-preserving because staged safe-error formatting has no React dependency and FastAPI legacy error scrubbing has no Next route dependency.
  Evidence: `frontend/lib/review/stagedSafeError.ts` and `frontend/lib/server/fastapi/errors.ts` are covered by `frontend/tests/api-route-tests.cjs`.
- Observation: Root runner inventory has no immediate deletion candidate under this plan because each legacy wrapper still represents either documented compatibility, advanced research, export, or smoke-test surface.
  Evidence: `docs/runtime_entrypoints.md` now classifies each root `run_*.py` and requires replacement docs plus focused verification before retirement.

## Decision Log

- Decision: Keep this plan as a deferred roadmap instead of changing runtime code during the Run Diagnostics stabilization branch.
  Rationale: The immediate production bug was malformed provider URLs and staged error classification. Mixing broad architecture changes into that branch would make verification and rollback harder.
  Date/Author: 2026-06-15 / Codex.
- Decision: Split the work into three tracks rather than one monolithic refactor.
  Rationale: API subprocess migration, frontend module extraction, and legacy wrapper retirement have different risks, tests, and rollback paths. Each can be implemented safely in separate sessions.
  Date/Author: 2026-06-15 / Codex.
- Decision: Preserve all public API routes, generated artifact names, browser storage keys, and CLI commands until a track explicitly proves a compatibility migration.
  Rationale: The current website and operator workflows depend on these contracts. Internal cleanup must not surprise users or invalidate existing run artifacts.
  Date/Author: 2026-06-15 / Codex.
- Decision: Implement Track 2 before Track 1 subprocess replacement in this session.
  Rationale: The repository already had dirty staged-failure files, and the frontend extraction seams are pure, testable, and lower risk. Replacing the diagnosis subprocess requires parity tests and a service boundary that should not be mixed with unrelated dirty changes.
  Date/Author: 2026-06-15 / Codex.
- Decision: Treat Track 3 implementation as documentation/inventory only for now.
  Rationale: Removing or changing wrapper behavior without proving no docs or tests depend on those commands would violate the compatibility boundary. The inventory is the safe prerequisite for future retirement gates.
  Date/Author: 2026-06-15 / Codex.

## Outcomes & Retrospective

The roadmap exists as a separate handoff artifact and no broad behavior change has been mixed into
the Run Diagnostics fix. The first implementation session completed two small Track 2 extractions
and the Track 3 root runner inventory. The next contributor can continue Track 1 by adding parity
tests for a direct staged diagnosis service, continue Track 2 by extracting another pure helper, or
continue Track 3 by adding retirement gates for a specific wrapper only after replacement docs and
smoke checks prove safety.

## Context and Orientation

Portfolio MRI is a diagnosis-first, current-portfolio-first investment decision-support system.
The current web route chain starts at portfolio input, runs staged review work through FastAPI, then
unlocks diagnosis, evidence, Client Fit, hypothesis, comparison, verdict, and report screens.

The staged backend boundary is mostly in `src/api/reviews.py`. It exposes FastAPI review endpoints
and maps generated artifacts into public response envelopes. It imports helpers from
`scripts/run_review_from_payload.py`, which validates the frontend payload, writes run-local input
files, invokes the existing review pipeline, and reads output artifacts.

The subprocess boundary is the place where Python starts another Python command instead of calling
a normal function in the same process. Subprocesses are useful for compatibility because they reuse
existing CLI entrypoints, but they hide typed errors, make timeouts coarse, and require parsing
stdout/stderr tails. In this repository, examples include `scripts/run_review_from_payload.py`,
`src/portfolio_review_workflow.py`, `src/candidate_factory.py`, and selected PDF/export helpers.

The frontend bridge boundary is mostly in `frontend/lib/server/fastapiBridge.ts`. It validates
legacy portfolio payloads, calls FastAPI, scrubs errors for the UI, checks lineage IDs, maps FastAPI
response envelopes into old route-compatible shapes, and handles downstream candidate/comparison/
verdict/report actions.

The frontend review-state boundary is mostly in `frontend/lib/reviewState.tsx`. It is a React
context provider that stores active review state in browser storage, records staged progress,
compacts backend artifacts into screen summaries, writes compact Supabase persistence records, and
exposes action methods to the route screens.

Root legacy runner wrappers are files such as `run_optimization.py`, `run_equal_weight.py`,
`run_minimum_variance.py`, and other root `run_*.py` scripts that delegate to implementations under
`legacy/runners/`. They are compatibility entrypoints, not the current Core MVP product front door.
Do not delete them just because they are old; remove or hide them only after the retirement criteria
in this plan are met.

## Plan of Work

Track 1 replaces the highest-value API subprocess boundary first. Start by mapping the current
staged diagnosis path from `src/api/reviews.py` into `scripts/run_review_from_payload.py` and then
into `run_report.py --materialize-analysis-subject`. Identify the smallest direct service function
that can perform the same diagnosis materialization without shelling out. If such a function does
not exist, create a thin service module that reuses existing validated helpers rather than copying
formulas. The first implementation milestone must keep the CLI path available and prove that the
FastAPI direct path writes the same required staged artifacts for a fixture portfolio.

Track 2 splits large frontend files by stable seams. In `frontend/lib/server/fastapiBridge.ts`, the
first safe extraction should be pure and server-only, such as moving scrubbed error handling,
lineage validation, or public response mapping into a neighboring module under
`frontend/lib/server/fastapi/`. In `frontend/lib/reviewState.tsx`, the first safe extraction should
be pure display/storage normalization, such as staged progress cleaning or compact summary helpers.
Do not change route URLs, response shapes, localStorage keys, Supabase persistence schema, or
screen behavior in the first extraction.

Track 3 defines legacy wrapper retirement criteria. Build an inventory of root `run_*.py` files and
classify each one as current product, explicit compatibility, research/advanced, export/report, or
retirement candidate. A wrapper can be retired only if no canonical doc or test uses it as an
operator command, there is a replacement command documented in `docs/runtime_entrypoints.md`, and
focused tests or smoke checks prove the replacement covers the use case. If a wrapper remains, its
warning text and docs should be encoding-clean English the next time that file is intentionally
touched.

## Concrete Steps

All commands are run from the repository root, referred to below as `<repo root>`.

Before each implementation session, run:

    git status --short

For Track 1 discovery, inspect and document the current call graph:

    rg -n "run_from_payload|subprocess|run_report.py|DEFAULT_TIMEOUT_SECONDS" src scripts run_portfolio_review.py run_report.py -S
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q

For Track 1 implementation, add or update tests before changing behavior. A safe first test should
prove that a fixture staged review produces the required diagnosis-stage artifacts without relying
on stdout/stderr parsing for success. Run at minimum:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_review_workflow.py -q
    cmd /c npm --prefix frontend run test:api

For Track 2 discovery, measure current module size and locate pure helper seams:

    (Get-Content -LiteralPath frontend\lib\server\fastapiBridge.ts).Count
    (Get-Content -LiteralPath frontend\lib\reviewState.tsx).Count
    rg -n "function |export function |const .* =" frontend\lib\server\fastapiBridge.ts frontend\lib\reviewState.tsx -S

For each Track 2 extraction, run:

    cmd /c npm --prefix frontend run test:api
    cmd /c npm --prefix frontend run typecheck

The first Track 2 extraction added focused coverage inside `frontend/tests/api-route-tests.cjs` for
`frontend/lib/review/stagedSafeError.ts` and `frontend/lib/server/fastapi/errors.ts`.

For Track 3 discovery, build the wrapper inventory:

    Get-ChildItem -LiteralPath . -File -Filter 'run_*.py' | Select-Object -ExpandProperty Name
    rg -n "run_[A-Za-z0-9_]+\.py|legacy/runners|Core MVP entrypoints" README.md AGENTS.md docs scripts tests -S

The current inventory lives in `docs/runtime_entrypoints.md` under "Root `run_*.py` inventory and
retirement classes".

For Track 3 implementation, run docs verification and focused smoke checks for any command whose
docs or warning text changes:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe -m pytest tests\test_docs_links.py -q

If code changes are made in any track, also update the owning docs according to
`docs/contracts/DOC_SYNC_CONTRACT.md` and run the narrowest relevant pytest or frontend checks from
`TESTING.md`.

## Validation and Acceptance

Track 1 is accepted only when the normal staged Run Diagnostics path can run through a direct
service/module boundary for the selected milestone, the old CLI compatibility path still works, and
provider/data-load failures still produce scrubbed `safe_error` responses. The public FastAPI
envelope shape must not change unless a separate contract migration plan is created.

Track 2 is accepted only when extracted frontend helpers are covered by existing or new tests, the
public Next.js compatibility routes still return the same fields, `frontend/lib/reviewState.tsx`
keeps the same storage keys, and typecheck passes.

Track 3 is accepted only when every root `run_*.py` wrapper has a documented classification and no
wrapper is removed without a replacement command, docs update, and focused verification. Retirement
means removal from the current operator surface, not deletion of useful source history.

The roadmap as a whole is accepted when each track can be completed independently and rolled back
without changing formulas, generated artifact schemas, route URLs, or the diagnosis-first product
flow.

## Idempotence and Recovery

Each track must be implemented in small commits or reviewable patches. If a direct service path in
Track 1 fails parity, keep the existing subprocess path as the fallback and stop. If a frontend
extraction in Track 2 causes route tests or typecheck to fail, revert only the extraction and keep
the tests. If wrapper classification in Track 3 finds that a legacy command is still used by docs or
tests, classify it as compatibility and do not remove it.

Never run destructive git commands for this work. Do not delete generated artifacts or user outputs
as part of architecture cleanup. Do not refactor `src/stress_factors.py`, `src/portfolio_xray.py`,
or candidate factory internals unless a future session writes a tiny, independently verified
extraction plan.

## Artifacts and Notes

Initial roadmap discovery evidence:

    frontend/lib/server/fastapiBridge.ts: about 1103 lines
    frontend/lib/reviewState.tsx: about 3388 lines
    src/api/reviews.py imports scripts.run_review_from_payload helpers
    scripts/run_review_from_payload.py imports subprocess and owns DEFAULT_TIMEOUT_SECONDS
    root run_*.py wrappers delegate to legacy/runners/ for legacy compatibility

This plan intentionally does not change runtime behavior. It is a handoff plan for future sessions.

## Interfaces and Dependencies

Stable public interfaces that must be preserved unless a future contract migration explicitly says
otherwise:

- FastAPI staged route: `POST /api/v1/reviews/staged`.
- FastAPI staged status route: `GET /api/v1/reviews/{review_id}/status`.
- Next.js compatibility route: `/api/portfolio/diagnose`.
- Browser storage keys in `frontend/lib/reviewState.tsx`: `pmri.activeReview.v2`,
  `pmri.activeReview.v1`, and the legacy cleanup prefix `pmri.reviewResult.`.
- Current Core MVP CLI entrypoints: `run_core_diagnostics.py`, `run_portfolio_review.py`, and
  `scripts/run_blocks_5_to_9_vertical_flow.py`.
- Legacy compatibility runner location: `legacy/runners/`.

Preferred new internal module locations:

- Python staged review service helpers under `src/api/` or `src/review_runtime/`, depending on the
  owning behavior.
- Server-only frontend FastAPI bridge helpers under `frontend/lib/server/fastapi/`.
- Pure frontend review-state normalization helpers under `frontend/lib/review/`.

## Revision Notes

- 2026-06-15 / Codex: Initial roadmap created from the Run Diagnostics stabilization plan Session 6
  requirement. It records the architecture debt tracks without changing runtime behavior.
- 2026-06-15 / Codex: First implementation pass completed behavior-preserving Track 2 helper
  extractions and Track 3 runner inventory documentation. Track 1 subprocess replacement remains
  pending because it needs dedicated parity tests before changing runtime execution.
