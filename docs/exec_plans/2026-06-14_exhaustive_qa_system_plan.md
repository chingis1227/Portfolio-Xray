# Build the Exhaustive QA System

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. Maintain this document in accordance
with that file. This plan is self-contained for the current QA workstream: a new contributor
should be able to read only this file, inspect the repository, and continue safely.

## Purpose / Big Picture

Portfolio MRI needs a repeatable release-grade QA system, not a one-off manual test pass. The
most urgent user-visible risk is that a deployed frontend can show `failed` immediately after the
user clicks `Run diagnosis` even though the portfolio input is valid. The most likely cause observed
in local logs is a frontend/backend version mismatch: the frontend calls `POST /api/v1/reviews/staged`,
while the active backend responds with `405 Method Not Allowed` because that backend process or
deployment does not support the staged review endpoint.

After this plan is complete, an operator can run one QA command, receive a timestamped report, and
see whether local and staging environments support the current diagnosis-first web flow. The first
session deliberately stops after the baseline and the P0 Run Diagnosis compatibility guard so the
operator can review the result before widening the gate.

## Progress

- [x] (2026-06-14 00:00Z) Session 01 plan accepted by the user: implement only the baseline QA
  orchestrator and P0 Run Diagnosis compatibility guard, then stop before Session 02.
- [x] (2026-06-14 14:26Z) Session 01 implementation created this ExecPlan, registered it in
  `docs/exec_plans/README.md`, added `scripts/qa_exhaustive.ps1` and `scripts/qa_exhaustive.cmd`,
  and produced a passing local QA summary at `output/qa_runs/20260614T142601Z/qa-summary.md`.
- [x] (2026-06-14 14:27Z) Session 01 focused backend validation passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_staged_review_api.py -q`
  reported 19 passed.
- [x] (2026-06-14 14:28Z) Session 01 frontend API validation was run and recorded rather than hidden:
  `cd frontend && npm.cmd run test:api` reported 14 passed and 6 failed. The diagnosis staged-route
  tests passed; unrelated builder, Supabase callback, recovery, candidate lineage, and report rows failed.
- [x] (2026-06-14 14:29Z) Session 01 git gates were run. `git diff --check` passed with only a line-ending
  warning for `docs/exec_plans/README.md`; `git status --short` showed the intended Session 01 files only.
- [x] (2026-06-14 15:01Z) Session 02 implementation expanded `scripts/qa_exhaustive.ps1` into the
  full local exhaustive gate with environment readiness, sequential backend/frontend/docs/Supabase
  commands, per-step logs, summary files, findings files, and `known_failure` / `new_failure`
  classification.
- [x] (2026-06-14 16:50Z) Session 02 validation passed in baseline mode:
  `.\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive` completed and wrote
  `output/qa_runs/20260614T163703Z/qa-summary.md` with schema `qa_exhaustive_session02_v1`,
  status `passed_with_known_failures`, 10 passed steps, 5 known failures, and 0 new failures.
- [x] (2026-06-14 19:51Z) Session 03 implementation added browser vertical QA orchestration,
  staging route-chain journey checks, Session 03 summary/findings schemas, and
  `qa-release-readiness.json` / `qa-release-readiness.md` with P0/P1/P2 blocker counts.
- [x] (2026-06-14 19:51Z) Session 03 local static validation passed at the runner level:
  `.\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive -ScenarioLimit 1` completed and wrote
  `output/qa_runs/20260614T193913Z/qa-summary.md` with schema `qa_exhaustive_session03_v1`,
  run status `passed_with_known_failures`, 10 passed steps, 5 known failures, 0 new failures,
  1 skipped browser step, and release readiness `not_ready` because known P0/P1/P2 blockers remain.
- [x] (2026-06-14 19:52Z) Session 03 browser vertical validation was run directly:
  `cd frontend && npm.cmd run qa:vertical -- --scenario-limit 1` failed at Builder setup with
  HTTP 500 because the Edge-runtime frontend bridge could not read run-local artifacts. This is
  recorded as `KNOWN_ISSUES.md` `KI-2026-06-14-002` and is a P0 release-readiness blocker, not a
  QA-system implementation failure.
- [x] (2026-06-14 20:31Z) Repair session resolved `KI-2026-06-14-002`: frontend downstream
  compatibility routes now consume FastAPI public response payloads and explicit lineage ids instead
  of reading run-local files from Next.js Edge route handlers. `cd frontend && npm.cmd run qa:vertical
  -- --scenario-limit 1` passed at `output/playwright/vertical-qa-2026-06-14T20-11-40-898Z/`, and
  `cd frontend && npm.cmd run qa:vertical -- --scenario-limit 5` passed at
  `output/playwright/vertical-qa-2026-06-14T20-31-32-204Z/` with same-run lineage and stale selected-card
  HTTP 409 proof.

## Surprises & Discoveries

- Observation: Recent local FastAPI logs showed `POST /api/v1/reviews/staged HTTP/1.1" 405 Method Not Allowed`.
  Evidence: this matches the user-reported production symptom where `Run diagnosis` showed `failed`.
- Observation: The current checked-out FastAPI code exposes `POST /api/v1/reviews/staged` in OpenAPI, and focused
  backend staged tests passed before this plan was written.
  Evidence: `tests/test_fastapi_app.py` and `tests/test_staged_review_api.py` are the focused backend guards.
- Observation: The current frontend API test suite is not globally green, but the diagnosis route tests that map
  frontend portfolio input to `POST /api/v1/reviews/staged` passed during planning.
  Evidence: `npm.cmd run test:api` previously reported 14 passed and 6 failed; diagnosis-route rows were among the
  passed tests. Session 01 must record such failures, not hide them.
- Observation: Direct `.ps1` execution can be blocked by Windows Execution Policy in this desktop shell, while the
  `.cmd` wrapper runs the same script with `-ExecutionPolicy Bypass`.
  Evidence: `.\scripts\qa_exhaustive.ps1 -LocalOnly` was blocked, then `.\scripts\qa_exhaustive.cmd -LocalOnly`
  executed the guard successfully.
- Observation: Inside the long Session 02 gate, `npm.cmd run build` can return exit code `-1` after full pytest even
  though the same frontend build command passes when run standalone.
  Evidence: `output/qa_runs/20260614T160725Z/qa-summary.md` and
  `output/qa_runs/20260614T162235Z/qa-summary.md` recorded the build as a new failure; a standalone
  `npm.cmd run build` from `frontend/` passed with exit code 0. This is tracked as
  `KNOWN_ISSUES.md` `KI-2026-06-14-001` and is classified as a known QA-runner baseline in the final Session 02 run.
- Observation: The full pytest baseline moved after the 2026-06-12 audit.
  Evidence: the Session 02 exhaustive run reported `34 failed, 1887 passed, 3 skipped`; `KNOWN_ISSUES.md` now records
  this as the current full-suite baseline until a newer audit supersedes it.
- Observation: The browser vertical route chain is blocked after diagnosis recovery because the Edge-runtime frontend
  bridge tries to read run-local artifacts from the filesystem for Builder setup and downstream routes.
  Evidence: `npm.cmd run qa:vertical -- --scenario-limit 1` failed on 2026-06-14 with
  `Builder setup prepare finished but the result could not be read` and the runtime detail
  `Run-local artifact reads are unavailable in the Cloudflare Pages runtime`; generated report:
  `output/playwright/vertical-qa-2026-06-14T19-52-09-529Z/qa-report.json`.
- Observation: After removing run-local reads from Next.js route handlers, the five-scenario vertical
  helper initially exposed a stale status-polling issue: the third scenario's run-local state was
  complete on disk, but the frontend status route kept seeing an earlier `data_load` state.
  Evidence: `output/playwright/vertical-qa-2026-06-14T20-12-44-974Z/qa-report.json` timed out while
  `runs/frontend_review_20260614T201330Z_adadfa45/review_state.json` was already `partial` with
  diagnosis-stage artifacts complete. Adding `cache: "no-store"` to the FastAPI bridge fetch fixed
  the polling path.
- Observation: Demo QA mode intentionally uses fixed fixture diagnosis content across different
  Client Fit scenarios.
  Evidence: `npm.cmd run qa:vertical -- --scenario-limit 5` completed all route-chain steps but the
  helper's old distinct-diagnosis assertion failed before it was changed to a warning. The passing
  report `output/playwright/vertical-qa-2026-06-14T20-31-32-204Z/qa-report.json` preserves the fixed
  diagnosis warning while proving route lineage and stale selected-card 409.

## Decision Log

- Decision: Build the QA system as a three-session workstream and stop after Session 01.
  Rationale: The Run Diagnosis failure is P0 and should be guarded immediately before broadening to heavy local,
  live, and staging checks.
  Date/Author: 2026-06-14 / Codex.
- Decision: Use environment variables for staging checks instead of hard-coded Cloudflare or Render URLs.
  Rationale: No checked-in Cloudflare or Render deployment configuration files were found in the repository. The
  same QA command should work for any preview or staging deployment once URLs are supplied.
  Date/Author: 2026-06-14 / Codex.
- Decision: Treat generated QA reports under `output/qa_runs/` as generated evidence, not source.
  Rationale: `output/` is already a generated-output path in `AGENTS.md`; reports should be reproducible and not
  committed unless explicitly requested.
  Date/Author: 2026-06-14 / Codex.
- Decision: Treat the current browser vertical failure as a release-readiness blocker to report, not as scope creep to
  repair inside the QA-system Session 03 implementation.
  Rationale: Session 03's job is to add the release gate and preserve detailed findings. The failing Edge-runtime
  artifact-read behavior belongs to the frontend bridge and is now captured as `KI-2026-06-14-002` for a repair
  session.
  Date/Author: 2026-06-14 / Codex.
- Decision: The deployment-safe frontend bridge contract is FastAPI-envelope-first, not filesystem-first.
  Rationale: Next.js Edge-compatible route handlers cannot read `runs/...` files. Downstream routes must
  pass `builder_setup_id`, `candidate_id`, `comparison_id`, and `verdict_id` from frontend state when
  available, let FastAPI validate run-local lineage, and build screen-compatible responses from the
  FastAPI public envelope.
  Date/Author: 2026-06-14 / Codex.
- Decision: The vertical helper should warn, not fail, when demo QA scenarios share the same fixed
  diagnosis fixture.
  Rationale: The release-readiness purpose of `qa:vertical` is same-run lineage, route-chain completion,
  bounded Client Fit context, and stale-card rejection. Requiring different diagnosis text from a frozen
  demo fixture creates false failures unrelated to release safety.
  Date/Author: 2026-06-14 / Codex.

## Outcomes & Retrospective

Session 01 delivered the baseline exhaustive QA shell and P0 Run Diagnosis compatibility guard. The local guard
passed and wrote `output/qa_runs/20260614T142601Z/qa-summary.md`, proving the checked-out FastAPI app exposes
`POST /api/v1/reviews/staged`. Focused backend staged validation passed with 19 tests. Frontend API validation was
not green: `npm.cmd run test:api` reported 14 passed and 6 failed. The Run Diagnosis staged-route tests passed, so
the P0 guard target is covered; the remaining frontend API failures are recorded as follow-up work and must not be
hidden before Session 02 or release readiness.

Session 02 converted the orchestrator from a P0-only guard into the local release-candidate runner. It now writes
per-step command logs under `output/qa_runs/<timestamp>/logs/`, keeps `qa-summary.json` / `qa-summary.md`, and adds
Session 02 `qa-findings.json` / `qa-findings.md` evidence. Known non-green baselines documented before this session
are classified as `known_failure`; unexpected command failures are classified as `new_failure`.

Session 02 validation completed with generated evidence at `output/qa_runs/20260614T163703Z/`. The run status is
`passed_with_known_failures`, not fully green. The known failures are the existing frontend API baseline, the fast QA
wrapper that includes that frontend API baseline, the full pytest baseline, the isolated Supabase frontend API row
from that same frontend suite, and `KI-2026-06-14-001` for the Next build exit `-1` behavior inside the long
orchestrator. The P0 staged Run Diagnosis OpenAPI guard passed and no `new_failure` remained in the final run.

Session 03 completed the QA-system buildout. The orchestrator now has a Session 03 schema, optional local browser
vertical QA, staging Run Diagnosis and route-chain checks, detailed findings that include passed/skipped/failed
critical evidence, and a separate release-readiness file that counts P0/P1/P2 blockers. The safe validation run
`output/qa_runs/20260614T193913Z/` proves the Session 03 summary/findings/readiness writers work in `-SkipLive` mode.
Release readiness is currently `not_ready`, not green, because known local QA baselines remain and the direct browser
vertical helper exposed `KI-2026-06-14-002`: downstream frontend bridge routes cannot read run-local artifacts in Edge
runtime.

Repair session outcome: `KI-2026-06-14-002` is fixed and removed from `KNOWN_ISSUES.md` after passing
`npm.cmd run qa:vertical -- --scenario-limit 1` and `npm.cmd run qa:vertical -- --scenario-limit 5`.
The frontend bridge no longer depends on local filesystem reads in Next.js route handlers for Builder,
Candidate, Comparison, Verdict, or Report. Remaining release readiness is still not globally green
because other known baselines remain, including `KI-2026-06-14-001` and the full-pytest drift index.

## Context and Orientation

Portfolio MRI is a diagnosis-first, current-portfolio-first investment decision-support system. The current user
path starts from a portfolio input, runs diagnosis and stress evidence, then moves through Client Fit, Hypothesis,
Candidate, Comparison, Verdict, and Report. The web path now uses staged review execution: clicking `Run diagnosis`
starts `POST /api/v1/reviews/staged`, receives a `review_id` quickly, and polls `GET /api/v1/reviews/{review_id}/status`.

The important files for this workstream are:

- `scripts/qa_fast.ps1` and `scripts/qa_contracts.ps1`, existing quick QA gates.
- `frontend/package.json`, the source of truth for frontend scripts such as `test:api`, `test:smoke`, `typecheck`,
  `build`, and `qa:vertical`.
- `tests/test_fastapi_app.py` and `tests/test_staged_review_api.py`, focused backend guards for FastAPI public
  routes and staged review state.
- `frontend/tests/api-route-tests.cjs`, Node tests for Next.js API route compatibility with FastAPI.
- `docs/contracts/QA_CONTRACT.md`, the current cross-cutting QA contract.
- `docs/demo/frontend_backend_vertical_runbook.md`, the operator runbook for the vertical web flow.

A "staged endpoint" means the FastAPI route `POST /api/v1/reviews/staged`. A "frontend/backend version mismatch"
means the frontend expects that route but the backend URL points to an older or wrong backend that returns `404`,
`405`, or an OpenAPI schema without that route.

## Plan of Work

Session 01 creates the minimal persistent structure. Add `scripts/qa_exhaustive.ps1` as a Windows PowerShell
orchestrator and `scripts/qa_exhaustive.cmd` as the matching command wrapper. The script must create
`output/qa_runs/<timestamp>/`, write per-run `qa-summary.json` and `qa-summary.md`, and run the local P0 guard by
importing the current FastAPI app and checking that its OpenAPI schema contains `POST /api/v1/reviews/staged`.

The same script must support an optional staging guard. Staging checks are enabled only when the caller passes
`-Staging` and sets `PMRI_QA_ALLOW_STAGING=1`, `PMRI_QA_FRONTEND_URL`, and `PMRI_QA_FASTAPI_URL`. In that mode the
script checks FastAPI health, checks OpenAPI for `POST /api/v1/reviews/staged`, and posts a safe demo portfolio to
the frontend `/api/portfolio/diagnose` route. A response with no `review_id`, `status: failed`, or an HTTP `404`/`405`
must be reported as a failure. A backend `404` or `405` around the staged endpoint must be classified as
`frontend_backend_version_mismatch`.

Session 01 also registers this plan in `docs/exec_plans/README.md` as the active plan. Session 01 must not implement
the full local gate, Playwright vertical QA, staging route-chain QA, or future hardening scenario matrix. Those belong
to Sessions 02 and 03.

Session 02 will expand `qa_exhaustive.ps1` to run the sequential local gates: environment readiness,
`scripts/qa_fast.ps1`, `scripts/qa_contracts.ps1`, FastAPI governance, full pytest, frontend typecheck/build/API/smoke,
docs verification, and Supabase compact/privacy tests. It will classify results as `passed`, `known_failure`,
`new_failure`, `blocked_external`, or `skipped_not_configured`.

Session 03 adds the browser vertical journey and staging release readiness. Without `-SkipLive`, the orchestrator runs
`npm.cmd run qa:vertical -- --scenario-limit 5`, captures active `reviewId` lineage, selected Launchpad card, Builder
setup, candidate, comparison, verdict, report status, screenshots or DOM fallbacks, and stale selected-card 409
evidence from `output/playwright/vertical-qa-*/qa-report.json`. With `-Staging` and the required environment
variables, it checks staging Run Diagnosis compatibility and the frontend route chain through Report. It writes a
final release-readiness summary with P0/P1/P2 blockers. The detailed findings file preserves passed evidence, failed
checks, warnings, flaky or retried checks, skipped checks, external blockers, file paths to logs/screenshots/DOM
fallbacks, suspected owner area, severity, reproduction command, and recommended next fix. This detailed file is the
backlog handoff for later repair sessions; do not rely on chat history as the only place where QA findings are stored.

Future hardening after the Core MVP gate is stable will expand coverage for all candidate methods, failed candidate
generation, infeasible candidate generation, stale selected candidate, missing comparison/verdict/report artifacts,
invalid ticker input, invalid weights, cash-only portfolio, overweight and underweight portfolios, empty and
conflicting Client Fit, degraded Supabase read/write state, legacy artifact compatibility, and research batch mode.

## Concrete Steps

From the repository root, implement Session 01:

    Create docs/exec_plans/2026-06-14_exhaustive_qa_system_plan.md.
    Update docs/exec_plans/README.md so the Current Pointer marks this plan as Active.
    Add scripts/qa_exhaustive.ps1.
    Add scripts/qa_exhaustive.cmd.

Run the Session 01 local orchestrator:

    .\scripts\qa_exhaustive.ps1 -LocalOnly

Expected result:

    A new output/qa_runs/<timestamp>/ folder exists.
    qa-summary.json records at least the local FastAPI staged OpenAPI guard.
    qa-summary.md states whether POST /api/v1/reviews/staged is present.

Run focused backend validation:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_staged_review_api.py -q

Run frontend API validation:

    cd frontend
    npm.cmd run test:api

If frontend API tests fail because of existing unrelated rows, record the output in the Session 01 retrospective.
Do not hide it and do not proceed to Session 02.

Finish with git gates from the repository root:

    git diff --check
    git status --short

From the repository root, implement Session 02:

    Update scripts/qa_exhaustive.ps1 so -LocalOnly runs the full local exhaustive gate.
    Preserve scripts/qa_exhaustive.cmd as the ExecutionPolicy-safe wrapper.
    Update TESTING.md and docs/contracts/QA_CONTRACT.md with the new exhaustive gate.
    Update this ExecPlan as a living document.

Run the Session 02 syntax and local gate validation:

    powershell -NoProfile -ExecutionPolicy Bypass -Command '$errors=$null; [void][System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath "scripts\qa_exhaustive.ps1"), [ref]$errors); if ($errors) { $errors; exit 1 } else { Write-Output OK }'
    .\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive

Expected result:

    A new output/qa_runs/<timestamp>/ folder exists.
    qa-summary.json uses schema qa_exhaustive_session02_v1.
    logs/ contains one log file per command-backed step.
    qa-findings.json records at least the P0 staged Run Diagnosis OpenAPI proof and any failed checks.
    Pre-recorded non-green baselines are classified as known_failure; unexpected failures are new_failure.

Finish Session 02 with git gates from the repository root:

    git diff --check
    git status --short

From the repository root, implement Session 03:

    Update scripts/qa_exhaustive.ps1 so live local browser QA runs unless -SkipLive is supplied.
    Keep scripts/qa_exhaustive.cmd as the ExecutionPolicy-safe wrapper.
    Add staging route-chain checks behind -Staging and the PMRI_QA_* environment variables.
    Add qa-release-readiness.json and qa-release-readiness.md.
    Update TESTING.md, docs/contracts/QA_CONTRACT.md, KNOWN_ISSUES.md if blockers are discovered, and this ExecPlan.

Run the Session 03 syntax and safe local validation:

    powershell -NoProfile -ExecutionPolicy Bypass -Command '$errors=$null; [void][System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath "scripts\qa_exhaustive.ps1"), [ref]$errors); if ($errors) { $errors; exit 1 } else { Write-Output OK }'
    .\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive -ScenarioLimit 1

Expected result:

    A new output/qa_runs/<timestamp>/ folder exists.
    qa-summary.json uses schema qa_exhaustive_session03_v1.
    qa-findings.json uses schema qa_findings_session03_v1.
    qa-release-readiness.json uses schema qa_release_readiness_session03_v1.
    Browser and staging checks are recorded as skipped when -SkipLive and -LocalOnly are supplied.
    Known baseline failures remain known_failure; unexpected failures remain new_failure.

Run the browser helper directly when checking live local vertical readiness without rerunning the full local static gate:

    cd frontend
    npm.cmd run qa:vertical -- --scenario-limit 1

For full release readiness after the current browser blocker is fixed, run:

    .\scripts\qa_exhaustive.cmd -LocalOnly

For staging release readiness, set the environment variables and run:

    $env:PMRI_QA_ALLOW_STAGING="1"
    $env:PMRI_QA_FRONTEND_URL="https://..."
    $env:PMRI_QA_FASTAPI_URL="https://..."
    .\scripts\qa_exhaustive.cmd -Staging

## Validation and Acceptance

Session 01 is accepted when `scripts/qa_exhaustive.ps1 -LocalOnly` creates a QA run folder and passes the local P0
staged endpoint guard. Focused backend staged tests should pass. Frontend API validation must be run and reported; a
pre-existing failure does not permit claiming the frontend API suite is green, but it should not be silently skipped.

The most important behavioral acceptance is that a backend or staging environment missing `POST /api/v1/reviews/staged`
is not treated as healthy. If staging is configured and the backend returns `404` or `405`, the report must classify
the problem as `frontend_backend_version_mismatch`.

After Session 01 is complete, stop. Do not start Session 02 until the user explicitly asks for it.

Session 02 is accepted when `scripts/qa_exhaustive.cmd -LocalOnly -SkipLive` can execute the full local gate in a
single sequence and write timestamped summary, findings, and log files. The command may finish with
`passed_with_known_failures` while the documented full-pytest and frontend-API baselines remain non-green, but any
new failure must keep the run status `failed` and preserve reproduction evidence in `qa-findings.*`.

Session 03 is accepted when the orchestrator supports three release modes: local static with `-LocalOnly -SkipLive`,
local browser vertical with `-LocalOnly`, and staging release readiness with `-Staging` plus the required environment
variables. Every run must write `qa-summary.*`, `qa-findings.*`, and `qa-release-readiness.*`. The readiness file must
count P0/P1/P2 blockers from findings and say `not_ready` when any such blocker remains. Browser vertical evidence
must include the Playwright report path, server logs, screenshots or DOM fallbacks, active review ids, selected card
ids, downstream ids, and stale selected-card 409 evidence when the helper reaches that stage. A failing browser
vertical run is acceptable as Session 03 QA-system evidence only if it is preserved as a P0 blocker with reproduction
details and not reported as release-ready.

## Idempotence and Recovery

The orchestrator is additive and safe to rerun. Each run writes a new timestamped folder under `output/qa_runs/`.
Generated QA folders are evidence only and are not source. If a run fails halfway, rerun the command; the next run
will use a new folder and will not overwrite the prior report.

The script must not stop or kill local servers, rewrite generated source files, run migrations, commit changes, or
modify deployment state. Staging checks are read-only except for posting a safe diagnosis request through the frontend
API route, which may create a normal staged review in the configured environment.

## Artifacts and Notes

The main generated artifacts are:

    output/qa_runs/<timestamp>/qa-summary.json
    output/qa_runs/<timestamp>/qa-summary.md
    output/qa_runs/<timestamp>/qa-findings.json
    output/qa_runs/<timestamp>/qa-findings.md
    output/qa_runs/<timestamp>/qa-release-readiness.json
    output/qa_runs/<timestamp>/qa-release-readiness.md

These artifacts should include the command mode, timestamp, step names, statuses, classifications, messages, and the
staging URLs used when staging is enabled. After Session 03, `qa-findings.json` and `qa-findings.md` must be more
detailed than the summary and must be suitable as a repair backlog. Each finding should include a stable id, severity
(`P0`, `P1`, `P2`, or `P3`), status/classification, affected subsystem, exact command or route, observed result,
expected result, evidence paths, suspected cause when known, and a recommended next action. Include successful critical
evidence too, especially the Run Diagnosis staged compatibility proof and same-run lineage proof, so future agents can
distinguish fixed behavior from untested behavior. Do not commit generated QA artifacts unless the user explicitly asks
for a snapshot.

## Interfaces and Dependencies

Use Windows PowerShell by default. Prefer `.\.venv\Scripts\python.exe` when it exists. If it does not exist, use
`py -3` according to the repository agent rules.

The Session 01 `scripts/qa_exhaustive.ps1` interface is:

    .\scripts\qa_exhaustive.ps1 [-LocalOnly] [-Staging] [-SkipLive]

`-LocalOnly` runs only local static/in-process guards. `-Staging` enables the environment-driven staging guard.
`-SkipLive` is accepted for forward compatibility with Session 02 but has no Session 01 effect beyond being recorded
in the summary.

The Session 02 local gate runs these checks sequentially when invoked with `-LocalOnly -SkipLive`:

    environment readiness
    local FastAPI staged OpenAPI guard
    scripts/qa_fast.ps1
    scripts/qa_contracts.ps1
    scripts/verify_fastapi_contract_governance.py
    python -m pytest tests/test_fastapi_app.py tests/test_fastapi_contract_governance.py -q
    python -m pytest
    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke
    scripts/verify_docs.py
    python -m pytest tests/test_docs_links.py -q
    python -m pytest tests/test_supabase_client_fit_compact_storage.py -q
    node --test --test-name-pattern=Supabase tests/api-route-tests.cjs

The staging guard uses:

    PMRI_QA_ALLOW_STAGING=1
    PMRI_QA_FRONTEND_URL=https://...
    PMRI_QA_FASTAPI_URL=https://...

The Session 03 runner adds:

    .\scripts\qa_exhaustive.cmd [-LocalOnly] [-Staging] [-SkipLive] [-ScenarioLimit <int>]

`-SkipLive` skips browser vertical QA. Without `-SkipLive`, the local browser helper runs from `frontend/` as:

    npm.cmd run qa:vertical -- --scenario-limit <ScenarioLimit>

`-Staging` is ignored when `-LocalOnly` is supplied. Without `-LocalOnly`, `-Staging` runs the staging compatibility
guard and route-chain journey after the local checks.

The safe diagnosis payload for frontend staging checks is:

    investor_currency: USD
    holdings:
      instrument SPY, weight 80
      cash USD, weight 20

Revision note 2026-06-14: Initial plan file created for Session 01. The plan includes the user's stop-after-session
instruction and the future hardening scenario matrix.

Revision note 2026-06-14: Added the post-Session 03 requirement to write detailed `qa-findings.json` and
`qa-findings.md` files so every discovered issue and proof point is preserved as a future repair backlog.

Revision note 2026-06-14: Session 02 expanded the local exhaustive QA gate, documented the permanent command in
`TESTING.md` and `docs/contracts/QA_CONTRACT.md`, and updated this plan with Session 02 acceptance criteria and
command sequence.

Revision note 2026-06-14: Session 02 validation evidence was added after the final local gate run. The plan now records
the `passed_with_known_failures` baseline, the current full pytest count, and the `KI-2026-06-14-001` QA-runner build
finding discovered during validation.

Revision note 2026-06-14: Session 03 added browser vertical orchestration, staging route-chain readiness, release
readiness artifacts, and detailed findings enrichment. Validation recorded
`output/qa_runs/20260614T193913Z/` for the safe local static runner and
`output/playwright/vertical-qa-2026-06-14T19-52-09-529Z/qa-report.json` for the direct browser blocker now tracked as
`KI-2026-06-14-002`.

Revision note 2026-06-14: Repair session resolved `KI-2026-06-14-002` by making the frontend FastAPI
bridge consume public FastAPI envelopes and explicit lineage ids instead of run-local filesystem reads
inside Next.js route handlers. Validation passed with `qa:vertical -- --scenario-limit 1` and
`qa:vertical -- --scenario-limit 5`; demo QA's fixed diagnosis text is now a helper warning, not a
route-chain failure.
