# Stabilize Run Diagnostics and Retire High-Risk Repository Debt

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. Any agent implementing or revising this
plan must keep it self-contained and update it after each session.

## Purpose / Big Picture

The website Run Diagnostics action must reliably create a portfolio diagnosis instead of failing
during data loading because a market-data URL is malformed. After the first milestone, a user can
start the local FastAPI and Next.js site, run a normal live diagnosis, and avoid the specific FRED
404 failure caused by `fredgraph.csv...id=DTB3`. After the full plan, provider failures will be
reported as provider/data-load failures, local QA will catch stale FastAPI route deployments, QA
documents will match current test reality, generated outputs will stop confusing source review,
and larger architecture debt will be separated into a dedicated future roadmap.

The work is split into sessions so each chat can make a small, verifiable change and stop before
touching the next subsystem.

## Progress

- [x] (2026-06-14 23:20Z) Session 1 implemented: fixed malformed FRED and ECB query separators, added URL-shape tests, and verified the previously failing `run_report.py` command exits with code 0 on retry.
- [x] (2026-06-14 23:55Z) Session 2 implemented: staged failure classification now inspects scrubbed `stdout_tail` and `stderr_tail`, provider-like failures map to `DATA_PROVIDER_FAILED`, timeouts remain `TIMEOUT`, and focused FastAPI tests cover the behavior.
- [x] (2026-06-14 23:55Z) Session 3 implemented: `scripts/verify_staged_route_compatibility.py` checks the local FastAPI OpenAPI route plus the Next.js diagnosis bridge, `scripts/qa_fast.ps1` runs the guard, and the diagnosis proxy reports a frontend/backend version mismatch when the staged route is missing.
- [x] (2026-06-15 00:00Z) Session 4 implemented: `TESTING.md` now matches the 2026-06-14 full-suite baseline in `KNOWN_ISSUES.md`, and stale frontend API known-failure labels were removed from the exhaustive QA runner.
- [x] (2026-06-15 00:00Z) Session 5 implemented: tracked generated files under `pdf files/` and `pdf_md_sources/` were classified as routine export artifacts, removed from git tracking while left on disk, and ignored for future runs.
- [x] (2026-06-15 00:30Z) Session 6 implemented: created the longer-term architecture debt roadmap for API/subprocess boundaries, large frontend modules, and legacy wrappers in `docs/exec_plans/2026-06-15_architecture_debt_roadmap_plan.md`.

## Surprises & Discoveries

- Observation: The live diagnosis failure was caused by malformed query URLs, not by Python being unavailable.
  Evidence: `src/data_fred.py` built `FRED_API_OBSERVATIONS_URL + "..." + urlencode(query)` and `FRED_CSV_GRAPH_URL + "..." + urlencode(query)`, which produced URLs such as `fredgraph.csv...id=DTB3` and a FRED HTTP 404.
- Observation: The same separator bug existed in the EUR risk-free helper.
  Evidence: `src/data_ecb.py` built `f"{ESTR_API}...{params}"`.
- Observation: Existing mocked FRED tests checked for base URL and parameters but did not assert the query separator.
  Evidence: The focused tests passed before the fix even though the live URL was invalid.
- Observation: The first live `run_report.py` verification timed out at 184 seconds, but a retry with a longer timeout exited with code 0.
  Evidence: The retry command wrote `EXIT=0` and ended with `Done (core diagnostics Blocks 1-3).`
- Observation: The staged failure classifier previously ignored safe subprocess tails where provider failures are most visible.
  Evidence: Session 2 added tests where `stderr_tail` contains `HTTP Error 404: FRED series DTB3 download failed`; the classifier now returns `DATA_PROVIDER_FAILED`.
- Observation: The frontend diagnosis proxy already called the staged endpoint, but fast local QA did not fail early with a route-contract-specific message.
  Evidence: Session 3 added `scripts/verify_staged_route_compatibility.py` and inserted it into `scripts/qa_fast.ps1` before broader backend/frontend checks.
- Observation: The recorded full-suite status was split across docs: `KNOWN_ISSUES.md` had the 2026-06-14 exhaustive baseline, while `TESTING.md` still showed the older 2026-06-12 count.
  Evidence: Session 4 updated `TESTING.md` from 13 failed / 1898 passed / 3 skipped to 34 failed / 1887 passed / 3 skipped.
- Observation: Exact generated PDF and Markdown sidecar filenames are referenced by code/tests as output paths, but the checked-in files themselves are not used as fixtures.
  Evidence: Session 5 searched references outside `pdf files/` and `pdf_md_sources/`; tests monkeypatch temp sidecar directories, and current docs classify both folders as generated/export artifacts.

## Decision Log

- Decision: Fix only the malformed FRED and ECB URL construction in Session 1, without changing formulas, cache policy, or frontend live/sample mode behavior.
  Rationale: The immediate user-visible crash had a narrow root cause, and changing frontend mode or data policy would mix product decisions into a bug fix.
  Date/Author: 2026-06-14 / Codex.
- Decision: Add exact URL-shape assertions to the existing factor matrix test file instead of creating a separate FRED test module.
  Rationale: The existing tests already monkeypatch FRED network calls and validate FRED fallback behavior; extending them is the smallest regression guard.
  Date/Author: 2026-06-14 / Codex.
- Decision: Normalize touched ECB docstrings to English text without special-character shorthand.
  Rationale: Repository-authored prose must be English-only and avoid mojibake; spelling out "Euro Short-Term Rate" is clear and encoding-safe.
  Date/Author: 2026-06-14 / Codex.
- Decision: Keep staged provider classification internal to `src/api/reviews.py` and preserve the public envelope shape.
  Rationale: The site needs better user-facing codes without a schema migration or frontend contract churn.
  Date/Author: 2026-06-14 / Codex.
- Decision: Implement the stale-server guard as an import-based local OpenAPI/script check rather than requiring a live FastAPI server.
  Rationale: `qa_fast.ps1` should stay lightweight, deterministic, and safe to run before broader local QA.
  Date/Author: 2026-06-14 / Codex.
- Decision: Remove stale `npm.cmd run test:api` known-failure labels from the exhaustive QA runner instead of preserving a historical known-failure classification.
  Rationale: The current frontend API route test suite is expected to pass; if it fails now, QA should report a new failure.
  Date/Author: 2026-06-15 / Codex.
- Decision: Remove routine generated PDF and Markdown sidecar files from git tracking with `git rm --cached`, not filesystem deletion.
  Rationale: The files are generated exports, not source fixtures; local user artifacts should remain on disk while future generated sidecars stay ignored.
  Date/Author: 2026-06-15 / Codex.

## Outcomes & Retrospective

Session 1 removed the specific malformed URL failure and proved the previously failing run can complete. Session 2 made staged provider failures retryable and distinguishable from unknown Python crashes by inspecting safe subprocess tails. Session 3 added a fast local compatibility guard and a clear frontend/backend version-mismatch message for missing staged FastAPI routes. Session 4 synchronized QA documentation and runner known-failure labels. Session 5 removed routine generated PDF and Markdown sidecars from source tracking while preserving local files. Session 6 separated the larger architecture debt into a dedicated future roadmap without changing runtime behavior.

## Context and Orientation

The product is Portfolio MRI, a diagnosis-first investment decision-support system. The normal web journey starts with portfolio input and runs a staged review through Next.js compatibility routes and a local FastAPI backend. The current backend still uses a script bridge: FastAPI calls Python helpers that run CLI-style diagnostics and write artifacts under `runs/frontend_review_*`.

The immediate failure happens in the risk-free data layer. Risk-free data is the short-term return used by portfolio metrics. For USD portfolios, `src/data_fred.py` fetches FRED series such as `DTB3`. For EUR portfolios, `src/data_ecb.py` fetches Euro Short-Term Rate history from `api.estr.dev`. Both helpers must build normal query URLs using `?` before encoded query parameters.

The staged review API lives primarily in `src/api/reviews.py`. The frontend compatibility adapter lives in `frontend/lib/server/fastapiBridge.ts`, and portfolio input calls `/api/portfolio/diagnose` from `frontend/components/portfolio/PortfolioInputTable.tsx`.

Generated outputs are files produced by runs, not normal source. This repository currently has tracked files under `pdf files/` and `pdf_md_sources/`; later sessions must classify them carefully before changing git tracking.

## Plan of Work

Session 1 is the narrow production bug fix. In `src/data_fred.py`, replace the malformed `"..."` separator with `"?"` in both official FRED API and public CSV fallback URL construction. In `src/data_ecb.py`, replace the malformed separator in the Euro Short-Term Rate URL and normalize touched docstrings to clear English. Extend `tests/test_factor_matrix_builders.py` so mocked network calls assert that the final URLs start with the expected base URL plus `?` and do not contain the base URL plus `...`. Add a focused ECB URL test using a monkeypatched `urllib.request.urlopen`.

Session 2 improves user-facing diagnosis failures without changing public response fields. In `src/api/reviews.py`, update `_classify_staged_failure` so it inspects `stdout_tail` and `stderr_tail` from the safe failure result in addition to `error` and `details`. Provider-like failures mentioning FRED, Yahoo, market data, price, quote, HTTP errors, timeouts, or download failures should map to `DATA_PROVIDER_FAILED` unless the failure is a timeout, which remains `TIMEOUT`. Add tests in `tests/test_fastapi_app.py` that directly exercise the classifier or a staged failure path: FRED HTTP failure maps to `DATA_PROVIDER_FAILED`, timeout maps to `TIMEOUT`, and unknown Python failure remains `PYTHON_STAGE_FAILED`. Preserve scrubbed output boundaries and do not expose raw paths or tracebacks.

Session 3 adds compatibility guardrails for stale local servers. Add a lightweight local QA check, preferably to `scripts/qa_fast.ps1`, that reads FastAPI OpenAPI from the local backend or invokes the local app object and confirms `POST /api/v1/reviews/staged` exists. The same guard should clearly report frontend/backend version mismatch when the staged route is missing. Do not change route URLs. Update only the minimal operator docs needed to explain that route contract changes require backend/frontend restart and that stale `.next` chunks invalidate visual QA conclusions.

Session 4 synchronizes QA truth. Update `TESTING.md` so the known full-suite status matches `KNOWN_ISSUES.md`: the latest recorded audit on 2026-06-14 reported 34 failed, 1887 passed, and 3 skipped. Update stale known-failure text in `scripts/qa_exhaustive.ps1` and any matching fast QA text so frontend API tests are no longer described as known failing when `npm run test:api` passes. Do not claim the full suite is green.

Session 5 handles generated outputs and encoding debt. First list tracked files under `pdf files/` and `pdf_md_sources/` and search for references to those exact paths. If they are not source fixtures, remove them from git tracking while leaving local files alone when possible, and ensure `.gitignore` covers routine generated PDFs and Markdown sidecars. If any file is intentionally source-like evidence, document that exception instead of removing it. Normalize mojibake only in files touched by this work.

Session 6 creates the future architecture roadmap. Add a separate self-contained ExecPlan under `docs/exec_plans/` for replacing the FastAPI-to-script subprocess bridge with direct service calls where safe, splitting large frontend modules by stable adapter boundaries, and defining retirement criteria for root legacy runner wrappers. Do not perform broad refactors in this session. This was completed in `docs/exec_plans/2026-06-15_architecture_debt_roadmap_plan.md`.

## Concrete Steps

All commands are run from the repository root.


Before each session, run:

    git status --short

For Session 1, edit `src/data_fred.py`, `src/data_ecb.py`, and `tests/test_factor_matrix_builders.py`, then run:

    .\.venv\Scripts\python.exe -m pytest tests\test_factor_matrix_builders.py -k "fred_api_key_is_primary or fred_csv_fallback or fred_csv_fetch_pushes_requested_date_range_into_url or ecb_estr_fetch_pushes_requested_date_range_into_url" -q
    .\.venv\Scripts\python.exe -m pytest tests\test_factor_matrix_builders.py -k "fred_api_key_is_primary or fred_csv_fallback" -q
    .\.venv\Scripts\python.exe run_report.py --materialize-analysis-subject --core-diagnostics-only --output-profile site_api --review-mode core --config runs\frontend_review_20260614T205042Z_2f7441bc\input.yml --no-review-run-context

Expected Session 1 proof is that focused tests pass and `run_report.py` reaches:

    Done (core diagnostics Blocks 1-3).

For Session 2, run:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
    cmd /c npm --prefix frontend run test:api

For Session 3, run:

    .\scripts\qa_fast.ps1
    cmd /c npm --prefix frontend run test:api
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q

For Session 4, run:

    cmd /c npm --prefix frontend run test:api
    cmd /c npm --prefix frontend run typecheck
    .\.venv\Scripts\python.exe scripts\verify_docs.py

For Session 5, run:

    git ls-files -- "pdf files" "pdf_md_sources"
    .\.venv\Scripts\python.exe scripts\verify_docs.py

For Session 6, if only docs change, run:

    .\.venv\Scripts\python.exe scripts\verify_docs.py

There is no Session 7 in this ExecPlan as of the 2026-06-15 Session 6 update. Do not invent a
seventh session without a separate user-approved scope.

## Validation and Acceptance

The full plan is accepted only when all session-specific checks pass or any remaining failure is explicitly identified as pre-existing or external. The most important user-visible acceptance is that website Run Diagnostics no longer fails because FRED or ECB URLs use `"..."` instead of `"?"`.

For Session 1, acceptance is:

- `src/data_fred.py` builds FRED URLs with `?`.
- `src/data_ecb.py` builds the Euro Short-Term Rate URL with `?`.
- URL-shape tests fail against the old `"..."` behavior and pass with the fix.
- The previously failing run no longer reports `fredgraph.csv...id=DTB3`.

For Session 2, acceptance is:

- Provider failures classify as `DATA_PROVIDER_FAILED` and remain retryable.
- Timeouts classify as `TIMEOUT`.
- Unknown Python failures classify as `PYTHON_STAGE_FAILED`.
- The public FastAPI/Next envelope shape does not change.

For Session 3, acceptance is:

- Local QA reports a clear version mismatch if `POST /api/v1/reviews/staged` is unavailable.
- Current local FastAPI passes the staged route guard.

For Session 4, acceptance is:

- `TESTING.md`, `KNOWN_ISSUES.md`, and QA runner text agree on the current full-suite status.
- Frontend API tests are not incorrectly labeled as known failing.

For Session 5, acceptance is:

- Tracked generated PDFs and Markdown sidecars are either documented as intentional source-like artifacts or removed from tracking safely.
- `.gitignore` prevents routine generated sidecars from returning.
- No new mojibake is introduced.

For Session 6, acceptance is:

- A separate checked-in architecture ExecPlan exists and can be handed to another agent without this chat history.
- No Session 7 exists in this plan; any additional session must be scoped separately before work begins.

## Idempotence and Recovery

All sessions should be safe to rerun. URL changes are simple deterministic replacements. Tests monkeypatch network calls and do not require live provider access except the explicit live/semi-live `run_report.py` proof. If the live command fails because of an external provider outage, keep the code changes if URL tests pass and record the provider failure separately.

Do not run destructive git commands. For generated output cleanup, use git-aware removal only after references are checked, and do not delete untracked user artifacts. If a session changes generated run folders during validation, do not stage them unless the session explicitly targets generated output policy.

## Artifacts and Notes

Session 1 verification produced the following concise evidence:

    5 passed, 14 deselected
    3 passed, 16 deselected
    EXIT=0
    Done (core diagnostics Blocks 1-3).

The first `run_report.py` attempt timed out after 184 seconds, so the accepted proof is the second run with a longer timeout. The run still printed provider warnings from Yahoo for old VOO history, but those were not the malformed FRED URL failure and did not prevent completion.

Session 2-3 implementation added the expected focused checks:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
    cmd /c npm --prefix frontend run test:api
    .\scripts\qa_fast.ps1

The expected behavior is that provider-like FRED/Yahoo/market-data text in safe tails maps to
`DATA_PROVIDER_FAILED`, unknown Python text remains `PYTHON_STAGE_FAILED`, and fast QA prints that
the staged Run Diagnosis compatibility guard passed.

## Interfaces and Dependencies

No public API, schema, or frontend route changes are required for Session 1. The stable functions remain:

- `src.data_fred.fetch_fred_series(series_id, start, end, api_key=None, timeout=..., retries=..., retry_sleep=...)`
- `src.data_ecb.fetch_estr(start, end)`

Session 2 must preserve existing FastAPI response models and only improve internal classification. Session 3 must preserve current route URLs. Session 5 must preserve source fixtures if any generated-looking file is intentionally referenced by tests or docs. Session 6 is documentation-only unless a later user explicitly asks to implement that architecture roadmap.

## Revision Notes

- 2026-06-14 / Codex: Initial checked-in ExecPlan created after Session 1 implementation so future sessions can continue without relying on chat history.
- 2026-06-14 / Codex: Updated after Sessions 2-3 to record staged error classification, the local staged-route QA guard, and remaining deferred sessions.
- 2026-06-15 / Codex: Updated after Sessions 4-5 to record QA status synchronization and generated PDF/Markdown sidecar tracking cleanup.
- 2026-06-15 / Codex: Updated after Session 6 to link the separate architecture debt roadmap and clarify that this plan has no Session 7.
