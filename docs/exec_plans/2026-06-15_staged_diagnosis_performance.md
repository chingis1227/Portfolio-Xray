# Make staged diagnosis feel immediate and target 30-second warm runs

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. Any agent implementing this work must keep
this document self-contained and update it before stopping.

## Purpose / Big Picture

Users currently click `Run diagnosis` and can wait roughly one and a half minutes before the site
moves forward. The backend is already able to start a staged review and return a `review_id`
quickly, but the portfolio input screen still waits for the full diagnosis chain before navigating.
After this change, the user should immediately see staged progress and be able to refresh safely,
while the backend reuses already-loaded data and caches repeated data loads so a warm run can target
30 seconds without removing any diagnostic calculations.

## Progress

- [x] (2026-06-15 13:55Z) Created this checked-in ExecPlan before implementation.
- [x] (2026-06-15 14:35Z) Changed the frontend so `Run diagnosis` stores the `review_id` and navigates immediately to a progress-capable diagnosis route.
- [x] (2026-06-15 14:35Z) Moved staged polling and recovery into the diagnosis route so completed diagnosis evidence hydrates automatically.
- [x] (2026-06-15 14:35Z) Enabled shared review context for the staged backend diagnosis path, with `PMRI_STAGED_REVIEW_SHARED_CONTEXT=0` as an escape hatch.
- [x] (2026-06-15 14:35Z) Added safe read-through caches for repeated macro, FRED, factor, market-price, and YAML/taxonomy loads.
- [x] (2026-06-15 14:35Z) Added `scripts/diagnosis_performance_smoke.py` for cold-ish and warm diagnosis runs.
- [x] (2026-06-15 14:35Z) Added focused backend cache behavior tests in `tests/test_runtime_memory_caches.py`; frontend route behavior is covered by type/API/smoke checks.
- [x] (2026-06-15 14:40Z) Updated owning documentation and changelog after behavior was implemented.
- [x] (2026-06-15 14:45Z) Ran focused verification and recorded results here.

## Surprises & Discoveries

- Observation: The repository already had many modified files before this implementation began.
  Evidence: `git status --short` showed modified frontend, backend, docs, and test files. This
  implementation must avoid reverting unrelated changes.
- Observation: A previous local successful staged run took about 154 seconds from initial state to
  candidate-ready partial state.
  Evidence: `runs/frontend_review_20260615T122821Z_q53Uoxnn4lFKi6J8TfYH2Q/review_state.json`
  recorded `created_at` `2026-06-15T12:28:21Z` and `updated_at` `2026-06-15T12:30:55Z`.
- Observation: Profiling showed repeated market, macro, FRED, factor, and YAML parsing work as the
  dominant latency, not React rendering.
  Evidence: `cProfile` attributed large cumulative time to `macro_regime_diagnostics`,
  `fetch_fred_series`, `yfinance.download`, `build_factor_matrix`, and `yaml.safe_load`.

## Decision Log

- Decision: Make the first implementation optimize perceived latency first by navigating after
  `review_id` creation, then optimize backend runtime with shared context and caches.
  Rationale: This produces immediate user-visible improvement even when a cold external data
  provider remains slow.
  Date/Author: 2026-06-15 / Codex
- Decision: Treat 30 seconds as a warm/cache-ready target, not a guarantee for first-ever cold runs
  with slow external providers.
  Rationale: External market and macro providers can dominate cold runtime outside application
  control.
  Date/Author: 2026-06-15 / Codex

## Outcomes & Retrospective

Implemented the immediate-progress staged UX and backend warm-run performance path. Portfolio Input now returns control to the user as soon as the staged backend returns `review_id`; Diagnosis owns polling and same-run recovery. Live staged diagnosis reuses shared run context by default, and process-local caches avoid repeated YAML/taxonomy parsing, yfinance downloads, FRED fetches, factor matrix builds, and review macro panel loads inside a warm backend process.

Focused verification passed. The performance smoke using the existing local payload reported `cold_seconds=118.624`, `warm_seconds=16.570`, and `status=passed` against a 30-second warm threshold.

## Context and Orientation

The frontend route `/portfolio-input` renders `frontend/components/portfolio/PortfolioInputTable.tsx`.
Its `runPortfolioDiagnosis` function posts to `/api/portfolio/diagnose`, receives a staged
`review_id`, then currently polls and recovers before navigating. The Next.js API bridge is
`frontend/lib/server/fastapiBridge.ts`, which forwards the request to FastAPI
`POST /api/v1/reviews/staged`.

FastAPI routes live in `src/api/app.py`. The staged review implementation lives in
`src/api/reviews.py`, where `create_staged_review` writes `review_state.json` and starts a
background thread. The background thread calls `scripts/run_review_from_payload.py`, which routes
live staged diagnosis through `src/review_runtime/staged_diagnosis_service.py` and then into
`run_report.run_materialize_analysis_subject_report`.

A staged review is a backend run that has a stable `review_id` and a compact progress file
`review_state.json`. A warm run is a run where reusable market, macro, factor, and taxonomy data are
already available in process memory or cache. A cold run may need to fetch external data and can be
slower.

## Plan of Work

First, update the frontend flow. In `PortfolioInputTable.tsx`, keep the existing POST request and
error handling, but after a successful staged start call `startStagedReview` and navigate to
`/diagnosis` immediately. Do not wait for `pollStagedDiagnosis` or `recoverCompletedDiagnosis` on
the input screen. Keep input-screen progress display for users who remain there or return.

Second, update `frontend/app/diagnosis/page.tsx` so it can show progress for an active staged run.
The page should poll `/api/portfolio/review/status?reviewId=...` while the active review is running
and lacks a completed `reviewSummary`. When the diagnosis chain is ready, call
`/api/portfolio/review/recover`, then pass the recovered `review_result` to `submitPortfolioInput`.
If staged status fails, use `recordStagedProgress` and show the safe error. This keeps recovery
same-run and avoids disk scans.

Third, enable shared backend context for staged live diagnosis. In
`src/review_runtime/staged_diagnosis_service.py`, call `run_materialize_analysis_subject_report`
with `use_review_run_context=True` for live staged diagnosis unless explicitly disabled by an
environment variable. The shared context should remain an orchestration optimization only; it must
not alter formulas or output schemas.

Fourth, add safe caches. Cache YAML/taxonomy loaders by resolved path, mtime, and file size so
updates are picked up automatically. Cache macro and factor panels by date-window parameters and
FRED series by series/date/source parameters. Return copies of pandas dataframes or dictionaries
from caches so callers cannot mutate cached originals.

Fifth, add a performance smoke script. The script should accept a payload path, run diagnosis twice,
print cold-ish and warm wall-clock seconds, and return success if the warm run is at or below the
configured threshold. If a run fails because external providers are unavailable, the script should
print a clear blocker and return a distinct non-zero code.

Finally, update source-of-truth docs for staged UX, runtime performance behavior, testing commands,
and the changelog. Keep generated `runs/` output out of commits.

## Concrete Steps

From repository root, use PowerShell. Prefer the existing virtual environment:

    .\.venv\Scripts\python.exe --version

Edit the frontend staged start path and diagnosis page. Then run:

    cd frontend
    npm.cmd run typecheck
    npm.cmd run test:api
    npm.cmd run test:smoke
    cd ..

Edit backend shared context and cache helpers. Then run:

    .\.venv\Scripts\python.exe -m pytest tests\test_analysis_subject_materialization.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_blocks_1_5_mvp_smoke.py -q

After adding the performance smoke script, run it against an existing or fixture payload:

    .\.venv\Scripts\python.exe scripts\diagnosis_performance_smoke.py --payload runs\frontend_review_20260615T122821Z_q53Uoxnn4lFKi6J8TfYH2Q\payload.json --warm-threshold-seconds 30

If that local payload is unavailable in a fresh clone, create a small fixture payload under
`tests/fixtures/` and use that instead.

## Validation and Acceptance

Frontend acceptance: after clicking `Run diagnosis`, the user reaches `/diagnosis` shortly after
the backend returns `review_id`. The diagnosis page shows staged progress while running, survives a
refresh through stored active review state, and replaces progress with the completed diagnosis panel
after recovery.

Backend acceptance: staged live diagnosis still writes the same required run-local artifacts under
`analysis_subject/`. A warm repeated run of the standard payload should complete at or below 30
seconds when cache is available, or the performance script must identify a specific external-data
blocker.

Regression acceptance: existing FastAPI staged status/recovery behavior remains compatible, the
legacy synchronous endpoint remains available, and downstream candidate/comparison/verdict/report
routes still require same-run lineage.

## Idempotence and Recovery

The changes are additive and safe to rerun. If frontend polling starts for an already-completed
review, recovery should hydrate the active review and stop polling. If a backend worker fails, the
safe staged error remains in `review_state.json` and the UI should offer a retry by returning to
portfolio input. If cached source files change, mtime-aware cache keys must cause a reload without
manual cache clearing.

Generated run folders created during testing are evidence only and must not be committed.

## Artifacts and Notes

Expected successful performance smoke transcript shape:

    cold_seconds=...
    warm_seconds=...
    warm_threshold_seconds=30.0
    status=passed

Expected external-data blocker transcript shape:

    status=blocked
    blocker=DATA_PROVIDER_FAILED
    message=...

## Interfaces and Dependencies

Frontend should use existing `useReviewState` methods: `startStagedReview`,
`recordStagedProgress`, and `submitPortfolioInput`. If an additional helper is needed, add it to
`frontend/lib/reviewState.tsx` without changing persisted raw artifact boundaries.

Backend should use existing modules: `src.candidate_run_context.prepare_review_run_context`,
`src.review_runtime.staged_diagnosis_service.run_staged_diagnosis_service`, and existing data
loader functions. New cache helpers must be internal implementation details unless a test requires
explicit cache clearing.

## Verification Results

Completed on 2026-06-15:

- `.\.venv\Scripts\python.exe -m pytest tests\test_runtime_memory_caches.py -q` -> 5 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_analysis_subject_materialization.py -q` -> 10 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_blocks_1_5_mvp_smoke.py -q` -> 4 passed after repairing a pre-existing broken percent-string regex in `src/config_schema.py` that rejected values such as `35%`.
- `cd frontend; npm.cmd run typecheck` -> passed.
- `cd frontend; npm.cmd run test:api` -> 24 passed.
- `cd frontend; npm.cmd run test:smoke` -> 1 passed.
- `.\.venv\Scripts\python.exe scripts\diagnosis_performance_smoke.py --payload runs\frontend_review_20260615T122821Z_q53Uoxnn4lFKi6J8TfYH2Q\payload.json --warm-threshold-seconds 30 --timeout-seconds 420` -> `cold_seconds=118.624`, `warm_seconds=16.570`, `status=passed`.

