# Staged Review Pipeline Migration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. It is self-contained for the staged review
pipeline migration: a future contributor should be able to read only this plan plus the current
working tree and continue the work safely.

## Purpose / Big Picture

The current web user experience can make the user wait for a long synchronous diagnosis run before a
stable `review_id` and screen-ready evidence are available. This migration makes the web path feel
like a platform: `Run diagnosis` creates a review immediately, the frontend shows progress, the
backend records stage state as work completes, and the user can see partial results such as X-Ray and
Stress evidence before later candidate, comparison, verdict, and report stages exist.

This migration is intentionally incremental. It does not rewrite formulas or optimizer logic. It
adds a staged state wrapper around the current deterministic Python and FastAPI workflow, keeps the
existing synchronous endpoint for compatibility until migration is complete, keeps Supabase as
compact-only persistence, and adds deterministic Demo / QA mode so demos do not depend on live
market-data provider behavior.

## Progress

- [x] (2026-06-14 08:46Z) Session 1 source-of-truth pass started after reading `RULES.md`,
  `WORKFLOW.md`, and `PLANS.md`.
- [x] (2026-06-14 08:46Z) Added the target staged state contract at
  `docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`.
- [x] (2026-06-14 08:46Z) Registered this ExecPlan as the active project plan and synced the
  documentation boundary for staged API, `review_state_v1`, Supabase compact-only persistence, and
  Demo / QA mode.
- [x] (2026-06-14 08:46Z) Session 1 validation passed: `scripts/verify_docs.py`, `git diff --check`,
  targeted staged-contract coverage search, and targeted stale-language search over changed
  source-of-truth files.
- [x] (2026-06-14 09:04Z) Session 2 implemented backend staged review start and status endpoints.
  `POST /api/v1/reviews/staged` creates `review_id`, writes `payload.json` and
  `review_state.json`, starts the existing diagnosis adapter in a daemon background thread, and
  returns the compact `review_started_v1` response. `GET /api/v1/reviews/{review_id}/status`
  returns a safe public `review_state_v1` response without absolute paths or tracebacks.
- [x] (2026-06-14 09:04Z) Session 2 tests and contract checks passed:
  `tests/test_fastapi_app.py -q`, `tests/test_staged_review_api.py -q`,
  `scripts/verify_fastapi_contract_governance.py`, and `git diff --check`.
- [x] (2026-06-14 09:10Z) Session 3 implemented backend stage-runner synchronization and
  safe staged errors. The background staged runner now derives each diagnosis-stage row from
  run-local artifacts, treats missing Client Fit context as non-blocking `partial`, fails safely
  with `ARTIFACT_MISSING` when required artifacts are absent, and preserves earlier completed
  stages when a later runtime failure occurs.
- [x] (2026-06-14 10:17Z) Session 4 implemented deterministic backend Demo / QA mode for staged
  reviews. `options.sample_mode: true` / `demo_qa` now writes frozen fixture diagnosis artifacts,
  records `frozen_fixture` provider status, skips the live diagnosis adapter, and leaves candidate,
  comparison, verdict, and report pending for later explicit actions.
- [x] (2026-06-14 10:30Z) Session 5 implemented frontend staged progress UX and status polling.
  `POST /api/portfolio/diagnose` now starts `POST /api/v1/reviews/staged`, the new
  `GET /api/portfolio/review/status?reviewId=...` proxy polls staged status, Portfolio Input
  stores `reviewId` immediately, shows stage progress, and hydrates screen summaries through the
  existing same-run recovery path after the diagnosis chain is available.
- [x] (2026-06-14 10:47Z) Session 6 implemented Supabase staged compact persistence and privacy
  controls. Signed-in staged polling now attempts compact cloud upserts for `reviews` plus
  non-pending canonical stage rows, the Supabase schema accepts canonical staged stage names, cloud
  review recovery can restore compact in-flight staged progress, and frontend cloud writes sanitize
  local paths, raw artifact refs, generated artifact filenames, and artifact path maps before
  measuring the 55 KB soft limit.
- [x] (2026-06-14 11:01Z) Session 7 implemented product cleanup, refresh recovery, downstream staged-state synchronization, deterministic Demo / QA downstream fixtures, vertical QA script repair, and plan closure. Candidate, comparison, verdict, and report FastAPI actions now update run-local `review_state.json`; frontend state advances downstream staged progress after successful explicit actions; Portfolio Input resumes an in-flight staged diagnosis after refresh from the saved `reviewId`; and `npm.cmd run qa:vertical -- --scenario-limit 1` passed against staged Demo / QA mode.

## Surprises & Discoveries

- Observation: The current documentation already recognizes the core architectural gap: the
  frontend uses `reviewId` and stage-like concepts, while the backend remains partly
  CLI/file-driven.
  Evidence: `frontend/README.md` documents Next.js compatibility proxies to FastAPI and compact
  `pmri.activeReview.v2` state, while `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` still treats
  `runs/frontend_review_*` folders and generated artifacts as the active local evidence chain.
- Observation: Supabase is already correctly bounded as compact optional persistence, so Session 1
  should strengthen that boundary rather than promote Supabase into an artifact store.
  Evidence: `docs/supabase/README.md` already forbids raw `runs/`, raw X-Ray/Stress artifacts, price
  history, PDFs, and generated artifact bundles.
- Observation: The existing diagnosis bridge always created its own `frontend_review_*` folder, which
  would have made staged start return a different `review_id` than the background diagnosis output.
  Evidence: `scripts/run_review_from_payload.py` called `create_run_dir()` inside `run_from_payload`.
  Session 2 extended that helper with optional `review_id` and `run_dir` parameters so the staged
  state and diagnosis artifacts share the same run-local folder.
- Observation: The diagnosis adapter remains monolithic from the staged API point of view, so
  Session 3 cannot stream true intra-run Block 2/Stress/Block 4 progress without deeper runtime
  instrumentation.
  Evidence: `run_from_payload()` returns only after the existing diagnosis command and artifact read
  pass finish. Session 3 therefore synchronizes stage rows from artifacts immediately after the
  adapter returns and before the frontend polling contract trusts later stages.
- Observation: The existing FastAPI request already had `options.sample_mode`, so Session 4 could
  implement Demo / QA mode without adding a new public request field or regenerating API types.
  Evidence: `CreateReviewOptions.sample_mode` existed before Session 4, and the staged start
  endpoint already mapped it to `mode: "demo_qa"`.
- Observation: The generated FastAPI TypeScript types had invalid optional-property syntax before
  Session 5 typechecking.
  Evidence: `npm.cmd run typecheck` failed on `frontend/lib/generated/api-types.ts` because the
  generator wrote optional fields as `field...` instead of TypeScript `field?`. Session 5 fixed
  `scripts/generate_fastapi_api_types.py`, regenerated `frontend/lib/generated/api-types.ts`, and
  `npm.cmd run typecheck` then passed.
- Observation: The existing optional Supabase schema only allowed coarse review stage rows
  (`diagnosis`, `builder`, `candidate`, `comparison`, `verdict`, `report`), so staged progress
  rows such as `xray`, `stress`, and `launchpad_builder` would have failed the database check.
  Evidence: Session 6 expanded `review_stage_summaries_stage_check` in
  `docs/supabase/supabase_free_schema.sql` and added an idempotent constraint replacement for
  already-created Supabase projects.
- Observation: The browser vertical QA helper had been corrupted by `...` tokens where JavaScript
  ternary `?` operators were intended, and it still expected the old synchronous diagnosis response.
  Evidence: `npm.cmd run qa:vertical -- --scenario-limit 1` initially failed with `SyntaxError:
  Unexpected token '...'`; after syntax repair it failed because `POST /api/portfolio/diagnose` now
  returns `review_started_v1`. Session 7 updated the helper to use staged start, status polling, and
  recovery before reading Launchpad cards.
- Observation: Backend Demo / QA mode was deterministic only through diagnosis, while downstream
  comparison still used the live adapter and rejected the fixture provider.
  Evidence: vertical QA failed at comparison with `market_data_provider must be one of ... got
  'frozen_fixture'`. Session 7 added deterministic fixture branches for Demo / QA comparison,
  verdict, and report actions while leaving live mode on existing adapters.

## Decision Log

- Decision: Add a new contract document, `docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, instead
  of embedding the staged state schema only in the FastAPI or frontend docs.
  Rationale: The staged state crosses backend, frontend, Supabase, generated artifacts, and product
  route gates. A separate contract prevents each subsystem from creating its own version of the
  stage language.
  Date/Author: 2026-06-14 / Codex.
- Decision: Use additive staged endpoints, `POST /api/v1/reviews/staged` and
  `GET /api/v1/reviews/{review_id}/status`, while keeping the current synchronous
  `POST /api/v1/reviews` endpoint as compatibility during migration.
  Rationale: This lowers implementation risk and allows the frontend to migrate once the stage state
  contract is tested.
  Date/Author: 2026-06-14 / Codex.
- Decision: Keep Supabase compact-only and exclude raw artifacts from cloud persistence.
  Rationale: Portfolio holdings, Client Fit context, generated X-Ray/Stress artifacts, and price
  evidence are sensitive financial data. Compact summaries are enough for browser recovery and saved
  review lists in this phase.
  Date/Author: 2026-06-14 / Codex.
- Decision: Make Demo / QA mode mandatory for the first-run/demo path and separate it from live mode.
  Rationale: A public first experience should not depend on random live market-data provider delays,
  missing quotes, rate limits, or network behavior.
  Date/Author: 2026-06-14 / Codex.
- Decision: Reuse the existing diagnosis adapter for Session 2 background execution and defer a
  granular stage-by-stage runner to Session 3.
  Rationale: The Session 2 goal is additive start/status API behavior without rewriting formulas or
  diagnostics. Reusing the existing adapter preserves synchronous compatibility and lets the status
  endpoint become testable before deeper runner instrumentation.
  Date/Author: 2026-06-14 / Codex.
- Decision: Mark a successful Session 2 staged diagnosis as overall `partial` with `candidate` as
  the current stage after diagnosis artifacts exist.
  Rationale: The start endpoint only runs the diagnosis-through-Launchpad chain. Candidate,
  comparison, verdict, and report remain pending because they require later explicit user actions
  and later migration sessions.
  Date/Author: 2026-06-14 / Codex.
- Decision: Implement Session 3 as a stage-state synchronizer around the existing diagnosis adapter,
  not as a rewrite of the analytics runtime.
  Rationale: This preserves current formulas and generated artifact schemas while still making the
  status endpoint honest about which canonical artifacts exist. A deeper streaming runner can be
  added later if product UX requires live per-block progress during the Python run.
  Date/Author: 2026-06-14 / Codex.
- Decision: Treat absent `client_fit_check.json` as non-blocking `partial`, while absent X-Ray,
  Stress, Problem Classification, or Launchpad/Builder artifacts fail the first affected stage with
  `ARTIFACT_MISSING`.
  Rationale: Client Fit V1 has a compatibility boundary where missing context becomes
  `not_provided`, but X-Ray, Stress, Problem Classification, and Launchpad/Builder artifacts are
  required to unlock the current diagnosis and hypothesis screens.
  Date/Author: 2026-06-14 / Codex.
- Decision: Implement `demo_qa` as a staged-only frozen fixture materializer rather than changing
  the live diagnosis adapter, CLI review commands, or calculation modules.
  Rationale: Session 4 is a reliability path for demos and QA. It must avoid live provider
  dependency without replacing live mode or rewriting formulas.
  Date/Author: 2026-06-14 / Codex.
- Decision: Keep staged status as progress state and continue using same-run recovery to hydrate
  screen-ready diagnosis summaries after polling confirms the diagnosis chain is ready.
  Rationale: `review_state_v1` is a compact progress wrapper, not a raw artifact transport. Reusing
  the existing recovery path lets the frontend keep display models sourced from run-local canonical
  artifacts without storing raw artifact trees in browser state.
  Date/Author: 2026-06-14 / Codex.
- Decision: Fix the FastAPI TypeScript generator as part of Session 5 before relying on new staged
  frontend types.
  Rationale: The frontend migration adds typed staged status handling, so the generated contract
  file must be valid TypeScript and reproducible from the generator.
  Date/Author: 2026-06-14 / Codex.
- Decision: Persist staged progress as compact Supabase app-data rows and sanitize every review or
  stage payload before size checks and writes.
  Rationale: Supabase is useful for refresh/history recovery, but it must not become a generated
  artifact store. Sanitizing before the 55 KB check prevents raw local paths, artifact references,
  generated filenames, and artifact maps from being counted as acceptable compact state.
  Date/Author: 2026-06-14 / Codex.
- Decision: Synchronize explicit downstream FastAPI actions back into run-local `review_state.json`.
  Rationale: The staged contract should remain the canonical recovery/progress source after the user
  moves beyond diagnosis. Candidate, comparison, verdict, and report remain explicit actions, but a
  successful action now advances its stage in the same review state used by refresh recovery and
  optional cloud compact persistence.
  Date/Author: 2026-06-14 / Codex.
- Decision: Add Demo / QA fixture branches for downstream comparison, verdict, and report instead
  of forcing frozen fixture runs through live market-data-backed adapters.
  Rationale: Demo / QA mode exists to make first-run and QA flows deterministic. Letting the live
  comparison adapter consume `frozen_fixture` run metadata made the vertical QA path fail for reasons
  unrelated to product flow or UI readiness.
  Date/Author: 2026-06-14 / Codex.
- Decision: Treat in-flight refresh recovery as a frontend auto-resume path, not a manual-only hidden
  recovery form.
  Rationale: A user who refreshes after `review_id` creation should see progress continue from the
  saved staged state. The advanced manual recovery form remains hidden support UI, while normal
  recovery uses stored `stagedProgress` and status polling.
  Date/Author: 2026-06-14 / Codex.

## Outcomes & Retrospective

Session 1 outcome: the staged migration received a named ExecPlan and a canonical staged contract.
Documentation verification and diff whitespace checks passed.

Session 2 outcome: the backend now has additive staged start/status endpoints while the synchronous
`POST /api/v1/reviews` path remains available. A staged start creates a run-local folder, writes
initial `review_state.json`, starts background diagnosis execution against the same run folder, and
allows status polling through a safe compact response. Session 2 does not migrate the frontend, does
not implement deterministic fixture execution, and does not add granular per-stage instrumentation
beyond marking the diagnosis-through-Launchpad chain after the reused adapter finishes.

Session 3 outcome: the backend staged runner now records honest per-stage status after the diagnosis
adapter returns. It writes only safe run-local artifact references, preserves completed earlier
stages on later failure, classifies missing required artifacts as `ARTIFACT_MISSING`, and keeps
Client Fit absence as a partial compatibility state rather than a failed run. This still does not
implement deterministic Demo / QA mode, frontend polling, Supabase persistence, or true streaming
progress inside the monolithic Python diagnosis command.

Session 4 outcome: staged backend Demo / QA mode is now deterministic. When staged review creation
receives `options.sample_mode: true`, the background runner writes frozen fixture artifacts under the
same run-local `analysis_subject/` roles used by live diagnosis-stage synchronization, reports
provider source `frozen_fixture`, and does not call the live market-data-backed diagnosis adapter.
This does not migrate the frontend to polling, does not add Supabase persistence, does not implement
downstream candidate/comparison/verdict/report stages, and does not change live mode.

Session 5 outcome: the normal frontend diagnosis path now starts staged execution, records the
returned `reviewId` immediately in compact browser state, polls the staged status endpoint, shows
stage-by-stage progress on Portfolio Input, and unlocks the existing diagnosis screen flow after
same-run recovery hydrates the compact screen summaries. The synchronous FastAPI endpoint remains a
backend compatibility path, but the Next.js diagnosis compatibility route now targets staged start.
This does not add Supabase compact staged persistence, full refresh recovery semantics for in-flight
polling, or browser click-through QA.

Session 6 outcome: optional Supabase persistence now supports staged progress without storing raw
artifacts. While signed in, frontend state changes with `stagedProgress` attempt compact cloud
upserts for the review row and non-pending canonical stage rows. Saved cloud reviews can recover an
in-flight compact staged progress state even before completed diagnosis display summaries exist.
Cloud payloads are scrubbed before writes, and the Supabase schema accepts the canonical staged
stage names. This does not complete product copy cleanup, browser click-through QA, or full
refresh/resume behavior after the backend worker is no longer running.

Session 7 outcome and full-plan closure: the staged review pipeline is implemented for the current
web migration scope. The backend now keeps `review_state.json` synchronized through explicit
candidate, comparison, verdict, and report actions; downstream failures preserve earlier diagnosis
evidence as partial progress. Demo / QA mode now covers diagnosis plus deterministic downstream
fixture comparison, verdict, and grounded report context, so vertical QA no longer depends on live
market data. The frontend product copy now uses reader-facing progress labels, shows provider
freshness, auto-resumes an in-flight staged diagnosis after refresh, and advances compact staged
progress after successful downstream actions. The QA helper now exercises staged start, status
polling, recovery, downstream same-run lineage, route navigation, and stale-card rejection. Focused
backend, frontend, docs, smoke, and one-scenario vertical QA checks passed; full multi-scenario live
network QA remains a release-level/manual gate rather than a requirement for this closed plan.

## Context and Orientation

Portfolio MRI is a diagnosis-first, current-portfolio-first decision-support system. The current
frontend route chain is:

    /
    -> /onboarding/sign-in
    -> /onboarding/name
    -> /onboarding/investor-type
    -> /onboarding/loading
    -> /portfolio-input
    -> /diagnosis
    -> /evidence
    -> /client-fit
    -> /hypothesis
    -> /comparison
    -> /verdict
    -> /report

The current normal frontend API URLs live under `frontend/app/api/portfolio/*` and proxy to the
FastAPI backend. The FastAPI app is implemented in `src/api/app.py`, `src/api/models.py`, and
`src/api/reviews.py`. The synchronous diagnosis path ultimately uses the existing Python review
runtime and generated artifacts under `runs/frontend_review_*`.

The active frontend browser state is compact state stored in `pmri.activeReview.v2` by
`frontend/lib/reviewState.tsx`. Supabase persistence, when enabled, is optional compact persistence
implemented under `frontend/lib/supabase/*`; it is not a raw artifact store.

The target contract for this plan is `review_state_v1`. It is a run-local `review_state.json` file
that records overall review status, current stage, per-stage status, artifact references, provider
status, and safe errors. It is not a replacement for canonical calculation artifacts; it is the web
orchestration state that points to those artifacts.

## Plan of Work

Session 1 creates the source-of-truth contract and registers this plan. It does not change runtime
behavior.

Session 2 adds additive backend endpoints. `POST /api/v1/reviews/staged` creates the review id and
run folder, writes `review_state.json`, starts background execution, and returns immediately.
`GET /api/v1/reviews/{review_id}/status` reads the state file and returns a safe public status
response. The current synchronous `POST /api/v1/reviews` endpoint remains available.

Session 3 adds the stage runner wrapper. The wrapper updates each canonical diagnosis stage to
`pending`, `running`, `completed`, `partial`, or `failed`, adds artifact references only when files
exist, and records safe errors without tracebacks or absolute paths. It leaves later candidate,
comparison, verdict, and report rows pending until later explicit stage work.

Session 4 adds deterministic Demo / QA mode. Demo / QA mode uses frozen fixture evidence and does
not call external market-data providers. Live mode remains available with provider and freshness
disclosures. This session is backend-only and is selected by the existing `options.sample_mode`
request field.

Session 5 migrates the frontend diagnosis path to staged execution. The Portfolio Input screen saves
`reviewId` immediately, shows progress, polls the status endpoint, and unlocks routes as stage state
becomes available.

Session 6 extends optional Supabase persistence for staged compact state. Supabase may store compact
stage statuses and summaries, but it must never store raw generated artifacts, price history, full
artifact trees, local paths, PDFs, or generated folders.

Session 7 closes product readiness naming, recovery behavior, downstream staged-state synchronization, deterministic Demo / QA downstream execution, and vertical QA.

## Concrete Steps

From the repository root, use PowerShell.

For Session 1:

    git status --short
    Get-Content -Raw -LiteralPath RULES.md
    Get-Content -Raw -LiteralPath WORKFLOW.md
    Get-Content -Raw -LiteralPath PLANS.md
    Add the staged contract and register this ExecPlan.
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

For Session 2:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py

For Session 3:

    .\.venv\Scripts\python.exe -m pytest tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

For Session 4:

    .\.venv\Scripts\python.exe -m pytest tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

For frontend implementation sessions:

    cd frontend
    npm.cmd run test:api
    npm.cmd run test:smoke
    npm.cmd run typecheck

For Session 6:

    cd frontend
    npm.cmd run test:api
    npm.cmd run test:smoke
    npm.cmd run typecheck
    cd ..
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

For Session 7 closure:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_staged_review_api.py -q
    cd frontend
    npm.cmd run test:api
    npm.cmd run typecheck
    npm.cmd run test:smoke
    npm.cmd run qa:vertical -- --scenario-limit 1
    cd ..
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 5 also fixes and uses the FastAPI TypeScript generator when the generated contract file
needs regeneration:

    .\.venv\Scripts\python.exe scripts\generate_fastapi_api_types.py

## Validation and Acceptance

Session 1 acceptance is documentation-only:

- `docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md` exists and defines stage names, statuses, API
  targets, `review_state_v1`, Demo / QA mode, live mode, safe errors, route mapping, and Supabase
  compact-only boundaries.
- `docs/exec_plans/README.md` points to this plan as active.
- Product, FastAPI, artifact-to-screen, frontend, Supabase, decision, changelog, and spec docs
  reference the target staged contract without claiming runtime behavior is already implemented.
- `scripts/verify_docs.py` and `git diff --check` pass or any failures are documented.

Full-plan acceptance after Session 7:

- A user clicking `Run diagnosis` receives a `review_id` immediately from staged start under normal local conditions.
- The UI shows progress immediately and can recover progress after refresh.
- X-Ray, Stress, Client Fit, Hypothesis, Candidate, Comparison, Verdict, and Report unlock from canonical staged state plus same-run lineage checks.
- Demo / QA mode is deterministic across diagnosis and explicit downstream actions and does not use external market data.
- Supabase stores only compact state and never raw artifacts.
- The synchronous compatibility path remains available until explicitly retired by a later plan.

Session 2 acceptance is backend-only:

- `POST /api/v1/reviews/staged` is present in OpenAPI, accepts the existing create-review request
  body, writes `runs/frontend_review_*/review_state.json`, and returns `review_started_v1` without
  waiting for full diagnosis completion.
- `GET /api/v1/reviews/{review_id}/status` is present in OpenAPI and returns a safe
  `review_state_v1` view from the run-local state file.
- Public staged responses do not expose Python tracebacks, local absolute paths, raw artifact trees,
  secrets, or environment variables.
- `frontend/lib/generated/api-types.ts` and `docs/contracts/FASTAPI_SCREEN_MAPPING.json` are updated
  for the two staged operations.

Session 3 acceptance is backend-only:

- The staged background runner updates diagnosis-stage rows from run-local artifact presence rather
  than marking all rows completed blindly.
- A successful diagnosis with required artifacts present marks `input`, `data_load`, `xray`,
  `stress`, `problem_classification`, and `launchpad_builder` completed and leaves `candidate`,
  `comparison`, `verdict`, and `report` pending.
- Missing `client_fit_check.json` is non-blocking and records `client_fit` as `partial`.
- Missing required diagnosis artifacts after an apparent adapter success produce safe
  `ARTIFACT_MISSING` state at the first affected stage.
- Runtime failures preserve earlier completed stages and expose no Python traceback or local
  absolute path in public status JSON.

Session 4 acceptance is backend-only:

- Starting a staged review with `options.sample_mode: true` records `mode: "demo_qa"` and provider
  source `frozen_fixture`.
- The `demo_qa` background runner does not call the live diagnosis adapter or external
  market-data providers.
- The frozen fixture path writes the run-local diagnosis-stage artifacts required by the staged
  synchronizer under `analysis_subject/`.
- The public staged status marks diagnosis stages from fixture artifact presence and leaves
  `candidate`, `comparison`, `verdict`, and `report` pending.
- Live staged mode remains on the existing diagnosis adapter path.

Session 5 acceptance is frontend-focused:

- `POST /api/portfolio/diagnose` proxies to `POST /api/v1/reviews/staged` and returns
  `review_started_v1` without reading `review_result.json` synchronously.
- `GET /api/portfolio/review/status?reviewId=...` proxies to
  `GET /api/v1/reviews/{review_id}/status` and rejects mismatched review IDs.
- Portfolio Input persists the staged `reviewId` immediately, shows current stage progress,
  provider/freshness disclosure, and safe staged errors while polling.
- When X-Ray, Stress, Problem Classification, and Launchpad/Builder are ready, the frontend uses
  same-run recovery to hydrate compact diagnosis, evidence, Client Fit, and Hypothesis summaries
  before navigating to `/diagnosis`.
- `npm.cmd run test:api`, `npm.cmd run test:smoke`, and `npm.cmd run typecheck` pass.

Session 6 acceptance is Supabase-focused:

- Signed-in frontend state with `stagedProgress` can upsert a compact `reviews` row and compact
  non-pending canonical stage rows without requiring completed `reviewSummary`.
- `docs/supabase/supabase_free_schema.sql` allows the canonical staged stage names in
  `review_stage_summaries`.
- Cloud review recovery can restore compact in-flight staged progress when completed diagnosis
  summaries are not yet available.
- Cloud persistence strips local paths, artifact references, raw generated artifact filenames, and
  artifact path maps before stage summary size checks and before Supabase writes.
- `npm.cmd run test:api`, `npm.cmd run test:smoke`, `npm.cmd run typecheck`,
  `scripts/verify_docs.py`, and `git diff --check` pass or any failures are documented.

Session 7 acceptance is full-plan closure:

- Candidate, comparison, verdict, and report FastAPI actions update `review_state.json` for the same
  `review_id` and preserve previous completed stages if a later action is blocked or failed.
- Portfolio Input auto-resumes an in-flight staged diagnosis after refresh using saved
  `stagedProgress.reviewId`, polls status, recovers the completed diagnosis chain, and navigates to
  `/diagnosis`.
- Product progress copy uses reader-facing labels, provider/freshness disclosure, and refresh-safe
  messaging rather than raw implementation stage names.
- Demo / QA mode provides deterministic fixture-backed comparison, verdict, and report context for
  vertical QA while live mode keeps using the normal adapters.
- `npm.cmd run qa:vertical -- --scenario-limit 1` passes and records screenshots/logs under
  `output/playwright/vertical-qa-*`; generated QA outputs remain non-source artifacts.
- The plan is closed as completed after backend, frontend, docs, smoke, typecheck, and vertical QA
  checks pass.

## Idempotence and Recovery

The Session 1 documentation edits are safe to repeat because they add one contract and one plan
record. The synchronous endpoint and current CLI workflows remain available as compatibility paths.
Generated `runs/` folders are not source and should not be edited as part of this plan. If a staged
run fails after implementation, rerunning `POST /api/v1/reviews/staged` should create a new review
folder rather than mutating an unrelated old run.

## Artifacts and Notes

The canonical staged stage list is:

    input
    data_load
    xray
    stress
    client_fit
    problem_classification
    launchpad_builder
    candidate
    comparison
    verdict
    report

The staged endpoints are:

    POST /api/v1/reviews/staged
    GET /api/v1/reviews/{review_id}/status

The staged state file is:

    runs/frontend_review_*/review_state.json

## Interfaces and Dependencies

Backend implementation sessions should use the existing FastAPI app modules:
`src/api/app.py`, `src/api/models.py`, and `src/api/reviews.py`. Additive Pydantic models should
represent staged start and staged status responses. Do not remove or rename the current synchronous
review models during this migration.

Frontend implementation sessions should use the existing Next.js compatibility routes under
`frontend/app/api/portfolio/*`, the active review state provider in `frontend/lib/reviewState.tsx`,
and optional Supabase helpers in `frontend/lib/supabase/*`.

Supabase implementation sessions should use the existing compact tables and the existing 55 KB
summary soft limit. They must not introduce Supabase Storage, service-role keys, Realtime, Edge
Functions, or raw generated artifact uploads for this migration.

## Revision Notes

- 2026-06-14 09:04Z / Codex: Updated the living plan after Session 2 implementation to record the
  backend staged endpoints, same-run adapter reuse decision, validation commands, and remaining
  frontend/Demo/Supabase work.
- 2026-06-14 09:10Z / Codex: Updated the living plan after Session 3 implementation to record the
  backend stage-runner synchronizer, Client Fit partial compatibility behavior, safe
  `ARTIFACT_MISSING` handling, and validation commands.
- 2026-06-14 10:17Z / Codex: Updated the living plan after Session 4 implementation to record the
  backend deterministic Demo / QA fixture materializer, live-mode separation, focused validation
  commands, and remaining frontend/Supabase work.
- 2026-06-14 10:30Z / Codex: Updated the living plan after Session 5 implementation to record the
  frontend staged start/status proxy, Portfolio Input polling UX, same-run recovery hydration
  decision, FastAPI TypeScript generator fix, and focused frontend validation commands.
- 2026-06-14 10:47Z / Codex: Updated the living plan after Session 6 implementation to record the
  optional Supabase staged progress upsert path, canonical staged stage names in the Supabase
  schema, cloud payload sanitization, compact in-flight recovery, and focused validation commands.
- 2026-06-14 11:01Z / Codex: Finalized the plan after Session 7 closure. Recorded downstream
  staged-state synchronization, frontend auto-resume behavior, deterministic Demo / QA downstream
  fixtures, vertical QA helper repair, passing focused validation, and full-plan completion.
