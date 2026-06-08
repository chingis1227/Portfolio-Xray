# Vertical Integration Post-Audit Hardening Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.
This document follows `PLANS.md` from the repository root. It is self-contained for a
new contributor who has only the current working tree and this file.

## Purpose / Big Picture

Portfolio MRI / Portfolio X-Ray / ДИАГНОСТИКА 2 now has a local frontend-to-backend
vertical flow from Portfolio Input through Report / AI Commentary. The 2026-06-08 full
project audit found that the integration is logically connected and locally demo-ready
for a scripted path, but not yet robust enough for a natural product demo. The most
important gap is the handoff from a selected Candidate Launchpad card to a matching
Portfolio Alternatives Builder setup: the Python bridge already exposes a safe
`--prepare-builder` action, but the frontend does not call it before candidate generation.

After this plan is implemented, a user can select any backend-generatable Launchpad card
in the frontend, prepare a matching Builder setup for that card, generate exactly one
diagnostic candidate, compare current versus candidate, request a non-binding Decision
Verdict, and generate grounded Report / AI Commentary without using stale artifacts,
root `config.yml`, PDFs, or candidate-zoo behavior.

This plan does not change Python calculation logic, optimizer math, root `config.yml`,
PDF generation, macro dashboards, production auth, cloud deployment, database behavior,
or advanced multi-candidate research flows.

## Progress

- [x] (2026-06-08) Session 00 created this post-audit hardening ExecPlan and registered it in `docs/exec_plans/README.md`. No product code, Python calculation logic, root `config.yml`, generated artifacts, staging, or commit actions were changed. Stop after Session 00; the next implementation chat should begin with Session 01.
- [x] (2026-06-08) Session 01 added frontend Builder prepare API/state/UI handoff so selected Launchpad card -> Builder setup -> Candidate Generation is a real frontend flow. New route `POST /api/portfolio/builder/prepare` calls the existing safe Python `--prepare-builder` bridge action; Hypothesis now prepares run-local Builder setup before enabling one diagnostic candidate generation; compact state stores active Builder setup and clears downstream candidate/comparison/verdict summaries when setup changes.
- [x] (2026-06-08) Session 02 synchronized the human-facing frontend/backend runbook and frontend docs with the implemented Builder prepare UI/API flow. The documented manual path now includes selected Launchpad card -> `POST /api/portfolio/builder/prepare` -> matching Builder setup -> one diagnostic candidate generation, and the docs/index/changelog preserve non-production and non-recommendation boundaries.
- [x] (2026-06-08) Session 03 added direct route-level API tests for the Builder prepare endpoint validation and safe failure behavior. The tests invoke the Next route handler directly with mocked bridge process/readFile dependencies, covering invalid JSON, bad review id/path separators, missing selected card, backend failure, missing result path, successful pass-through, and client-side scrubbing of tracebacks and local paths without running live candidate factories.
- [x] (2026-06-08) Session 04 ran and documented a manual in-app browser demo from Portfolio Input through grounded Report commentary. The run completed on `http://localhost:3003` with review id `frontend_review_20260608T211411Z_37eacc28`, generated one `equal_weight` diagnostic candidate, comparison evidence, an evidence-insufficient decision-support verdict, and report commentary grounded in `ai_commentary_context.json`. Evidence was captured in `docs/audits/2026-06-08_vertical_integration_session04_browser_demo.md`. Important caveat: this browser run did not evidence a separate `/api/portfolio/builder/prepare` call or `builder_setup_result.json`; the UI showed `Builder setup prepared` immediately after selecting the first card and allowed candidate generation.
- [x] (2026-06-08) Session 05 improved active review reload/recovery without permanently persisting raw backend JSON in browser localStorage. New read-only route `GET|POST /api/portfolio/review/recover` validates `frontend_review_*` ids, reads only run-local `review_result.json`, returns sanitized diagnosis/evidence/launchpad/builder outputs, and excludes candidate/comparison/verdict/report artifacts from restored active state. Portfolio Input now includes a recovery control by review id; it rebuilds compact active state through the existing summary path and leaves downstream readiness false.
- [x] (2026-06-08) Session 06 centralized frontend API Python executable resolution while preserving repo `.venv\Scripts\python.exe` as the Windows/default path when present. New helper `frontend/lib/server/pythonBridge.ts` is used by all Python-backed portfolio API routes and falls back only when repo `.venv` is missing; direct route tests now assert the `.venv` command path without running live backend work.
- [x] (2026-06-08) Session 07 decided not to add Playwright because the project has no Playwright
  dependency or browser-install harness and the added setup cost is not justified for this narrow
  hardening pass. Instead, it added dependency-free `npm.cmd run test:smoke`, which starts a local
  Next dev server on an isolated port and verifies that the main journey pages render without
  running backend candidate factories, candidate zoo flows, or root `config.yml` mutation.

## Surprises & Discoveries

- Observation: The audit report already exists as `docs/audits/2026-06-08_vertical_integration_full_project_audit.md` and is the direct input to this plan.
  Evidence: It reports the main warning: backend supports `--prepare-builder`, but frontend has no prepare-builder route or button, so candidate generation only works for a selected card whose Builder setup already matches.

- Observation: The current ExecPlan register still points to the older Full Demo MVP readiness plan as Active before this Session 00 update.
  Evidence: `docs/exec_plans/README.md` had `Full Demo MVP Readiness Audit and Hardening` as the Active pointer before this plan was registered.

- Observation: Next.js build now exposes the missing Builder prepare API route alongside the existing diagnose/candidate/comparison/verdict/report routes.
  Evidence: `npm.cmd run build` listed `/api/portfolio/builder/prepare`, and `npm.cmd run typecheck` passed after the route/state/UI changes.

- Observation: The focused bridge suite now directly covers the natural mismatch flow: generation is blocked when the selected card does not match the active Builder setup, then succeeds after `prepare_selected_builder_setup()` rebuilds setup for that card.
  Evidence: `tests/test_frontend_review_bridge.py` passed with 34 tests, including the new mismatch-before-prepare / accepted-after-prepare test.

- Observation: Direct route tests found that the Builder prepare scrubber hid absolute project roots but could still leave a project-relative internal path such as `[project]\scripts\run_review_from_payload.py` in the client error text.
  Evidence: The new `frontend/tests/api-route-tests.cjs` backend-failure test failed until `frontend/app/api/portfolio/builder/prepare/route.ts` also scrubbed `[project]/...` and `[project]\...` path tails to `[path]`.

- Observation: The Session 04 browser demo completed the full Input -> Diagnosis -> Evidence -> Hypothesis -> Candidate -> Comparison -> Verdict -> Report path, but it did not produce the documented explicit Builder prepare artifact.
  Evidence: Dev-server logs for `frontend_review_20260608T211411Z_37eacc28` showed successful `diagnose`, `candidate/generate`, `comparison/generate`, `verdict/generate`, and `report/generate` calls, but no `builder/prepare` call. The run directory contained `review_result.json`, `candidate_generation_result.json`, `current_vs_candidate_result.json`, `decision_verdict_result.json`, `report_commentary_result.json`, and `ai_commentary_context.json`, but not `builder_setup_result.json`. The Hypothesis UI showed `Builder setup prepared` immediately after selecting `Compare Against Simple References`.

- Observation: Existing compact browser state already strips `reviewResult` before localStorage writes, but a browser restart without that compact state had no user-facing way to recover a run by `reviewId`.
  Evidence: `frontend/lib/reviewState.tsx` writes `reviewResult: undefined` to `pmri.activeReview.v2` and removes legacy `pmri.reviewResult.*` keys, while no existing frontend route matched `review/recover` before Session 05.

- Observation: Recovery can be made safer by intentionally narrowing returned outputs to diagnosis, evidence, Launchpad, and Builder setup artifacts only.
  Evidence: The new route-level test injects stale `candidate_generation`, `current_vs_candidate`, and `decision_verdict` fields into a mocked `review_result.json`; the response omits those fields and reports `downstream_artifacts_restored_as_active: false`.

- Observation: Centralizing the Python command required a small update to the direct route-test loader because the tested route now imports a shared TypeScript helper through the frontend `@/` alias.
  Evidence: The first `npm.cmd run test:api` attempt failed with `Cannot find module '@/lib/server/pythonBridge'`; after teaching `frontend/tests/api-route-tests.cjs` to transpile local alias imports, the suite passed and still mocked process/file reads.

- Observation: A Playwright smoke would require adding a new browser test dependency and browser
  installation harness, while a local Next HTTP smoke can cover accidental page-render breakage with
  no new packages.
  Evidence: `frontend/package.json` had no Playwright dependency or script; the new
  `npm.cmd run test:smoke` check passed by launching the existing Next CLI directly.

## Decision Log

- Decision: Make `docs/exec_plans/2026-06-08_vertical_integration_post_audit_hardening_plan.md` the Active plan for post-audit frontend/backend hardening work.
  Rationale: The audit found a specific frontend/backend integration gap that should be fixed before broader demo hardening work continues. The older Full Demo MVP readiness plan remains important history, but this plan is the immediate working pointer.
  Date/Author: 2026-06-08 / Codex.

- Decision: Session 01 will use Option A from the audit: add a real frontend Builder prepare API/UI step rather than merely documenting that only the prebuilt matching card can generate.
  Rationale: This creates the honest product flow `select card -> prepare Builder setup -> generate candidate`, reduces operator confusion, and uses the existing safe Python bridge action instead of bypassing lineage guards.
  Date/Author: 2026-06-08 / Codex.

- Decision: Do not implement Session 01 in the same chat as Session 00 when the user asks to stop after Session 00.
  Rationale: The user explicitly requested a stop after successfully completing Session 00, so this plan is created and registered first; implementation begins only in the next chat.
  Date/Author: 2026-06-08 / Codex.

- Decision: Session 05 recovery will restore only the completed diagnosis-side active review, not downstream candidate/comparison/verdict/report active state.
  Rationale: This gives operators a practical browser-restart recovery path while preserving the product rule that Candidate Generation, Current vs Candidate, Decision Verdict, and Report are explicit stage actions tied to current UI state and lineage guards. It also avoids making stale run-local artifacts active just because they exist on disk.
  Date/Author: 2026-06-08 / Codex.

- Decision: Session 07 will add a dependency-free local Next smoke rather than Playwright.
  Rationale: The smoke target is basic journey page availability, not full browser interaction or
  backend candidate generation. Avoiding Playwright keeps verification lightweight and avoids adding
  package/browser-install overhead to this hardening pass.
  Date/Author: 2026-06-08 / Codex.

## Outcomes & Retrospective

Session 00 established a single self-contained working plan after the vertical integration audit and updated the ExecPlan register so future chats know where to resume.

Session 01 implemented the P1 Builder handoff gap without changing Python calculation logic: the frontend can now call a prepare-builder API, store compact active Builder setup state, clear stale downstream summaries on setup replacement, and enable Candidate Generation only after the selected card has matching prepared Builder setup. Verification passed: `npm.cmd run typecheck`, `npm.cmd run build`, and `./.venv/Scripts/python.exe -m pytest tests/test_frontend_review_bridge.py -q --basetemp="tmp/pytest_frontend_bridge_builder_prepare"` (34 passed).

Session 02 synchronized operator-facing documentation with the Session 01 UI/API behavior. Updated docs now name the `Prepare Builder setup` UI step, `POST /api/portfolio/builder/prepare`, matching selected-card lineage, compact state boundaries, and the one-diagnostic-candidate/non-recommendation product language. This session intentionally did not add route-level API tests or perform the live browser demo; those remain Session 03 and Session 04.

Session 03 added direct route-level coverage for `POST /api/portfolio/builder/prepare` without starting the frontend server or invoking live Python candidate factories. The new `npm.cmd run test:api` command exercises the route handler directly through a small Node test harness with mocked `spawn` and `readFile`, and the Builder prepare route now also removes project-relative path tails from client-facing failure strings. Verification passed: `npm.cmd run test:api` (5 passed), `npm.cmd run typecheck`, and `npm.cmd run build`.

Session 04 completed a manual in-app browser demo from Portfolio Input through Report / AI Commentary grounding and captured the evidence in `docs/audits/2026-06-08_vertical_integration_session04_browser_demo.md`. The successful run used review id `frontend_review_20260608T211411Z_37eacc28`, generated the `equal_weight` diagnostic candidate, produced comparison evidence, returned an evidence-insufficient non-binding verdict, and rendered a grounded report summary that referenced `runs/frontend_review_20260608T211411Z_37eacc28/ai_commentary_context.json`. The session also found a hardening caveat: the observed manual flow did not call `POST /api/portfolio/builder/prepare` or write `builder_setup_result.json`, despite the UI showing `Builder setup prepared`; this should be corrected or explicitly reconciled before claiming the documented Builder prepare path is manually verified end-to-end.

Session 05 added safe review recovery by `reviewId`. The new `frontend/app/api/portfolio/review/recover/route.ts` reads run-local `review_result.json` without running Python, validates path traversal boundaries, sanitizes returned outputs to diagnosis/evidence/Launchpad/Builder setup artifacts, and explicitly does not restore downstream artifacts as active state. `frontend/components/portfolio/PortfolioInputTable.tsx` now exposes a recovery control that rebuilds active state through `submitPortfolioInput`, so localStorage still receives only compact summaries and downstream candidate/comparison/verdict readiness remains false. Verification passed: `npm.cmd run test:api` (7 passed), `npm.cmd run typecheck`, and `npm.cmd run build` with `/api/portfolio/review/recover` listed.

Session 06 removed duplicated Python executable construction from the frontend portfolio API routes. `frontend/lib/server/pythonBridge.ts` now resolves the Python command once, preferring repo `.venv\Scripts\python.exe`, then POSIX `.venv/bin/python`, and only then a system Python fallback. The diagnose, Builder prepare, candidate, comparison, verdict, and report routes now call that helper. Verification passed: `npm.cmd run test:api` (7 passed, including `.venv` command assertion), `npm.cmd run typecheck`, and `npm.cmd run build`. Note: an initial parallel `typecheck` run failed while `next build` was recreating `.next/types`; rerunning `typecheck` after build passed.

Session 07 added a lightweight frontend smoke without adding Playwright. `frontend/tests/frontend-smoke-tests.cjs` starts the existing Next CLI on an isolated localhost port, checks the main journey pages from Portfolio Input through Report return HTTP 200 and include stage text, then stops the dev server. This gives a cheap guard for broken page rendering while preserving the boundary that smoke does not run backend candidate factories, candidate-zoo flows, or root config mutation. Verification passed: `npm.cmd run test:smoke` (1 passed).

## Context and Orientation

The current product is a diagnosis-first investment decision-support workflow, not an optimizer-first trading system. Product language must preserve these boundaries: a candidate is a diagnostic hypothesis, comparison is trade-off evidence, Decision Verdict is non-binding decision support, and no-trade or evidence-insufficient are valid outcomes.

The frontend lives under `frontend/`. The relevant user screen for the main gap is `frontend/app/hypothesis/page.tsx`. The shared browser state lives in `frontend/lib/reviewState.tsx`. The existing API routes live under `frontend/app/api/portfolio/`. The Python bridge is `scripts/run_review_from_payload.py`. It already supports `--prepare-builder`, `--generate-candidate`, `--run-comparison`, `--run-verdict`, and `--run-report-context` actions. The focused Python bridge tests are in `tests/test_frontend_review_bridge.py`.

A real frontend diagnosis creates a generated run directory named `runs/frontend_review_<timestamp>_<id>/`. The bridge writes a run-local `input.yml` and result files in that directory. The frontend path must not mutate root `config.yml`, must not trust root `Main portfolio/`, must not use candidate portfolio folders as active state, and must not silently fall back to demo JSON after a real run.

The audit report `docs/audits/2026-06-08_vertical_integration_full_project_audit.md` found that the current chain is mostly coherent: frontend API routes call the Python bridge; the bridge writes isolated run-local artifacts; stale candidate/comparison/verdict guards are strong; generated artifacts are ignored; and failure text is scrubbed. The main gap is the missing frontend prepare-builder handoff.

## Plan of Work

Session 00 is documentation and workflow setup only. Create this file and update `docs/exec_plans/README.md` so this plan is the Active pointer for post-audit vertical hardening. Do not touch product code in Session 00.

Session 01 will add the missing Builder prepare frontend/backend handoff. Add a new Next.js API route `POST /api/portfolio/builder/prepare` that validates `review_id` and `selected_card_id`, calls `scripts/run_review_from_payload.py --prepare-builder --review-id <id> --selected-card-id <card>`, reads `builder_setup_result.json`, scrubs user-facing failures like the existing routes, and returns the result. Extend `frontend/lib/reviewState.tsx` with compact active Builder setup state for the selected card. Update `frontend/app/hypothesis/page.tsx` so the user selects a Launchpad card, prepares Builder setup for that card, and only then can generate one candidate. The UI must clearly say Builder setup is not a portfolio and candidate generation is not a recommendation. Add focused bridge/state tests so a mismatched Builder is blocked before prepare and accepted after prepare.

Session 02 will update human-facing docs to match the implemented UI. Update the vertical runbook, frontend README, changelog, and any needed index links so operators can run the demo without knowing the CLI internals. Do not claim production readiness.

Session 03 will add direct API route tests. The current test coverage strongly verifies the Python bridge but only indirectly verifies Next API routes through typecheck/build. Add minimal route-level tests for invalid JSON/payload, bad review id, missing selected card, backend failure, timeout or missing result, and scrubbed local paths/tracebacks. Do not run live candidate factories in these tests.

Session 04 will perform a manual browser demo and capture evidence. Start the frontend dev server, run the documented flow from Portfolio Input through Report, record the review id, and create a short audit note under `docs/audits/` with the artifact chain and wording boundaries observed. Do not stage generated run folders.

Session 05 will improve reload and recovery. Add a read-only way to recover run-local active review artifacts by `reviewId` without putting full raw JSON permanently back into localStorage. Keep path traversal guards and compact state. Do not restore stale or mismatched candidate/comparison/verdict artifacts as active.

Session 05 implementation note: the read-only recovery endpoint is `GET|POST /api/portfolio/review/recover`. It accepts `review_id`, requires a `frontend_review_*` basename, reads only `runs/<review_id>/review_result.json`, returns `stage: "review_recovery"`, and narrows `review_result.outputs` / `review_result.paths` to diagnosis, evidence, Launchpad, Builder setup, and AI grounding artifacts. Portfolio Input has a "Recover run-local review" control that calls the endpoint and then uses the existing compact-state summarizer. Candidate/comparison/verdict/report artifacts on disk are intentionally not made active.

Session 06 will centralize Python executable resolution for frontend API routes. Keep repo `.venv\Scripts\python.exe` as the default on Windows, avoid creating repo-level Codex instruction files, and preserve current behavior unless the executable is missing.

Session 07 will decide whether a browser smoke test is worth adding. If existing tooling is present or the setup is small, add a lightweight smoke that does not run candidate zoo or mutate root config. If the cost is too high, document the decision and rely on manual demo evidence plus focused tests.

Session 07 implementation note: the accepted lightweight smoke is `npm.cmd run test:smoke` from
`frontend/`. It intentionally uses the existing Next CLI and built-in Node test runner rather than
Playwright. It checks route rendering only; it does not call Python-backed portfolio API routes.

## Concrete Steps

For Session 00, from the repository root, create this file and update the register:

    Set-Content -LiteralPath docs\exec_plans\2026-06-08_vertical_integration_post_audit_hardening_plan.md -Value <this plan>

Then edit `docs/exec_plans/README.md` so the Current Pointer starts with this plan as Active and moves the prior active Full Demo MVP readiness plan to Previous Active.

For Session 01, start a new chat and read this ExecPlan, `AGENTS.md`, `RULES.md`, `WORKFLOW.md`, `SPEC.md`, the audit report, `scripts/run_review_from_payload.py`, `frontend/app/hypothesis/page.tsx`, `frontend/lib/reviewState.tsx`, and `tests/test_frontend_review_bridge.py`. Then implement only the Builder prepare handoff.

Do not start Session 02 until Session 01 is implemented and verified.

For Session 03, the implemented direct route tests live in `frontend/tests/api-route-tests.cjs` and are run from `frontend/` with:

    npm.cmd run test:api
    npm.cmd run typecheck
    npm.cmd run build

The route tests mock the bridge process and file read, so they do not execute `scripts/run_review_from_payload.py` and do not run live candidate factories.

For Session 05, the implemented recovery route lives in `frontend/app/api/portfolio/review/recover/route.ts`.
The Portfolio Input recovery UI lives in `frontend/components/portfolio/PortfolioInputTable.tsx`.
Run these checks from `frontend/`:

    npm.cmd run test:api
    npm.cmd run typecheck
    npm.cmd run build

Expected proof is that the API test suite reports 7 passing tests, including the recovery route tests,
and the Next build route table lists `/api/portfolio/review/recover`.

## Validation and Acceptance

Session 00 acceptance is documentation-only:

- `docs/exec_plans/2026-06-08_vertical_integration_post_audit_hardening_plan.md` exists.
- `docs/exec_plans/README.md` points to this plan as Active for post-audit frontend/backend hardening.
- `git status --short` shows only documentation changes plus any pre-existing untracked audit file.
- No product code or root `config.yml` is changed.

Session 01 acceptance will require at minimum:

- `npm.cmd run typecheck` from `frontend/` passes.
- `npm.cmd run build` from `frontend/` passes.
- `.\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp="tmp\pytest_frontend_bridge_builder_prepare"` from the repository root passes, using the actual project-local `.venv` path.
- A focused test proves that a mismatched Builder setup blocks candidate generation before prepare and that `prepare_selected_builder_setup()` rebuilds a matching Builder for the selected card.
- The Hypothesis UI enables candidate generation only after successful Builder prepare for the selected card.

Session 03 acceptance is complete when:

- `frontend/tests/api-route-tests.cjs` directly invokes the Builder prepare route handler and covers invalid JSON, invalid review id/path traversal, missing selected card, backend failure, missing result path, successful pass-through, and scrubbed client failure text.
- `npm.cmd run test:api` from `frontend/` passes.
- `npm.cmd run typecheck` from `frontend/` passes.
- `npm.cmd run build` from `frontend/` passes and lists `/api/portfolio/builder/prepare`.
- No live candidate factory, root `config.yml` mutation, or generated run-folder staging is required.

Session 05 acceptance is complete when:

- `GET|POST /api/portfolio/review/recover` validates `review_id`, rejects path traversal, and reads only run-local `runs/<review_id>/review_result.json`.
- The recovery response returns a completed active review basis with diagnosis/evidence/Launchpad/Builder setup outputs, but omits candidate generation, current-vs-candidate, decision verdict, and report artifacts from active restore.
- Portfolio Input exposes a recovery control for `frontend_review_*` ids and routes the recovered review through the existing compact summary path; `localStorage` still stores `reviewResult: undefined`.
- `npm.cmd run test:api` from `frontend/` passes and includes recovery route tests.
- `npm.cmd run typecheck` and `npm.cmd run build` from `frontend/` pass; the build route list includes `/api/portfolio/review/recover`.

## Idempotence and Recovery

Session 00 is idempotent: if this file already exists, update it rather than creating a duplicate. If the register already points here, leave the pointer and update only status text if needed.

For later sessions, all generated runtime paths under `runs/`, `.next/`, `tmp/`, `Main portfolio/`, candidate output folders, and `portfolio_weights.yml` are generated artifacts and must not be staged unless a task explicitly targets generated outputs. If a test or build creates generated files, leave them ignored.

If a Session 01 implementation attempt fails halfway, revert or repair only files touched by that session. Do not use destructive git commands. Do not delete generated run folders unless explicitly requested.

## Artifacts and Notes

Source audit: `docs/audits/2026-06-08_vertical_integration_full_project_audit.md`.

Main audit finding to resolve first:

    Backend supports --prepare-builder, but frontend has no prepare-builder API route/button.
    Generation is enabled only when an existing Builder setup matches the selected card.

Required product boundary to preserve:

    Candidate = hypothesis, not recommendation.
    Comparison = trade-off evidence, not winner selection.
    Verdict = decision-support, not trading instruction.
    No-trade and evidence-insufficient are valid outcomes.

## Interfaces and Dependencies

The planned Session 01 public API addition is:

    POST /api/portfolio/builder/prepare

Request body:

    {
      "review_id": "frontend_review_<id>",
      "selected_card_id": "<launchpad_card_id>"
    }

Expected successful response mirrors the Python bridge result shape for `prepare_selected_builder_setup()`:

    {
      "review_id": "frontend_review_<id>",
      "status": "completed",
      "stage": "builder_setup",
      "selected_card_id": "<launchpad_card_id>",
      "can_generate_candidate": true,
      "path": "runs/.../analysis_subject/portfolio_alternatives_builder.json",
      "portfolio_alternatives_builder": { ... }
    }

Failures must return safe JSON with `status: "failed"`, `stage: "builder_setup"`, `review_id`, `selected_card_id`, `error`, and `details`, with tracebacks and absolute local paths scrubbed before reaching the browser.

Frontend state should store only compact Builder setup summary needed for the UI and lineage checks. It must not permanently store full raw backend review JSON in localStorage and must clear downstream candidate/comparison/verdict state when a new Builder setup replaces the active selected card.


Revision note, 2026-06-08 / Codex: Session 03 updated this plan after adding direct Builder prepare route tests and strengthening client-facing path scrubbing. The note exists so the next contributor can resume at Session 04 without needing chat history.

Revision note, 2026-06-08 / Codex: Session 04 updated this plan after the manual browser demo. The demo reached grounded Report successfully, and the new audit note records both the successful artifact chain and the discovered mismatch where the explicit Builder prepare API/artifact was not observed in the live browser flow.
