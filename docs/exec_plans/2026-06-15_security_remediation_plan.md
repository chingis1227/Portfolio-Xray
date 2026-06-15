# Security Remediation for Portfolio MRI Review APIs

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. This document follows `PLANS.md` from the repository root.

## Purpose / Big Picture

Portfolio MRI review APIs can contain portfolio holdings, diagnosis output, candidate alternatives, verdict context, and report grounding. After this plan is complete, public browser callers must authenticate before starting or reading review work, Next.js must call FastAPI through a signed internal server-to-server context, each run-local review must be bound to its owner before recovery or mutation, and the diagnosis workload must reject oversized or abusive requests before expensive work starts.

A developer can see Sessions 03-05 working by running `\.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q` from the repository root. The regression tests prove that protected routes require signed internal auth, staged status rejects a different owner with HTTP 403, downstream mutation rejects out-of-order stage lineage with HTTP 409, excessive holdings fail validation, and a full staged worker queue returns HTTP 429.

## Progress

- [x] (2026-06-15) Session 00: Created the security remediation plan and captured baseline validation status.
- [x] (2026-06-15) Session 01: Upgraded Next.js from the 14.x line to a safe 15.5.x line compatible with React 18 and confirmed the frontend build.
- [x] (2026-06-15) Session 02: Added central Next.js portfolio API authentication and signed internal FastAPI auth context for protected review routes.
- [x] (2026-06-15) Session 03: Persisted `owner_id` in run-local `review_state_v1` and enforced owner authorization on staged status and review recovery.
- [x] (2026-06-15) Session 04: Enforced owner authorization and stage lineage readiness on Builder, Candidate, Comparison, Verdict, and Report mutation endpoints.
- [x] (2026-06-15) Session 05: Added diagnosis workload abuse controls: request body size limit, holdings count bound, and staged background worker queue limits.
- [x] (2026-06-15) Session 06: Hardened the local configuration UI with local-only access, CSRF protection for mutating routes, loopback-only startup, and fixed broken inline JavaScript conditionals.
- [x] (2026-06-15) Session 07: Completed low/later hardening for review id entropy, FastAPI docs gating, results dashboard path containment, and deferred worklist reconciliation in TESTING/CHANGELOG/API contract docs.
- [ ] Session 08: Expand the full security regression layer.
- [ ] Session 09: Complete product-flow QA and documentation closure.

## Surprises & Discoveries

- Observation: The security remediation plan file named by the user was not present on disk when Sessions 03-05 started, even though the user provided its content in chat.
  Evidence: `Get-ChildItem docs\exec_plans | Where-Object Name -like '*security*'` returned no matching file, so this session restored `docs/exec_plans/2026-06-15_security_remediation_plan.md` as a checked-in living plan.
- Observation: Several security-adjacent files are marked with Git's `assume-unchanged`/hidden tracking state in this working tree, so `git status --short` does not list their modifications.
  Evidence: `git ls-files -v src\api\app.py src\api\models.py src\api\reviews.py tests\test_fastapi_app.py` printed `H` entries.
- Observation: `tests/test_fastapi_app.py` in this working tree did not yet include the HMAC-auth request helper described by earlier plan sessions.
  Evidence: the first focused pytest run returned HTTP 401 for authenticated-path tests until the test helper was updated to send `X-PMRI-User-Id`, `X-PMRI-Auth-Timestamp`, and `X-PMRI-Internal-Signature`.
- Observation: `config_ui/templates/config_form.html` contained invalid JavaScript ternaries rendered as `...`, which would break browser-side save/run actions.
  Evidence: `Select-String -Path config_ui\templates\config_form.html -Pattern '\.\.\.'` found the broken conditional expressions before Session 06; the same search returned no matches after the fix.

## Decision Log

- Decision: Store the authenticated owner as `owner_id` in run-local `review_state_v1` instead of creating a separate owner database.
  Rationale: The current product is run-local/file-driven. Keeping ownership next to staged state protects recovery and mutation without adding a new persistence dependency.
  Date/Author: 2026-06-15 / Codex.
- Decision: Reject recovery or mutation when `review_state.json` has no owner.
  Rationale: Legacy ownerless runs cannot be safely attributed to the current signed-in user; restarting the review is safer than allowing cross-user recovery.
  Date/Author: 2026-06-15 / Codex.
- Decision: Use narrow stage-readiness checks for downstream mutation endpoints.
  Rationale: Candidate requires completed diagnosis/Launchpad Builder state; Comparison requires Candidate; Verdict requires Comparison; Report requires Verdict. This blocks stale or out-of-order mutation while preserving existing artifact lineage checks.
  Date/Author: 2026-06-15 / Codex.
- Decision: Implement lightweight workload controls with Pydantic max holdings, a FastAPI request body limit, and in-process staged worker counters.
  Rationale: These checks stop obvious abusive inputs before expensive diagnosis work and fit the current local FastAPI process without introducing a full external queue.
  Date/Author: 2026-06-15 / Codex.
- Decision: Protect the Flask Config UI with a session CSRF token and local-only request guard instead of adding product authentication.
  Rationale: `config_ui/` is a local utility that can write `config.yml` and launch local commands. CSRF and loopback-only access mitigate drive-by browser and accidental LAN exposure without changing the current utility into a product login surface.
  Date/Author: 2026-06-15 / Codex.
- Decision: Disable FastAPI OpenAPI/Swagger/ReDoc HTTP routes by default and make them opt-in with `PMRI_FASTAPI_ENABLE_DOCS=1`.
  Rationale: The generated schema remains available to tests and type generation through `app.openapi()`, while local HTTP documentation routes are not exposed unless an operator deliberately enables them.
  Date/Author: 2026-06-15 / Codex.
- Decision: Increase new `frontend_review_*` id entropy by replacing the 8-hex-character UUID suffix with a 16-byte URL-safe random token while keeping legacy id recovery compatible.
  Rationale: New review ids become harder to guess without breaking older local run folders and focused tests that use simple fixture ids.
  Date/Author: 2026-06-15 / Codex.

## Outcomes & Retrospective

Sessions 03-07 are implemented. Staged review state now records an owner id, status/recovery/downstream endpoints reject mismatched owners, downstream mutation endpoints also require the previous stage to have completed, and diagnosis entrypoints have bounded holdings/body/worker controls. The local Config UI is loopback-only, requires CSRF tokens for write/run routes, and no longer ships broken inline JavaScript ternaries. New run-local review ids use higher entropy, FastAPI docs/OpenAPI HTTP routes are opt-in, and the Results Dashboard refuses configured output folders that escape the project root. Focused regression coverage for Sessions 06-07 passed with 36 tests. Remaining hardening is intentionally left to Sessions 08-09.

## Context and Orientation

The frontend public API routes live under `frontend/app/api/portfolio/` and proxy to FastAPI through `frontend/lib/server/fastapiBridge.ts`. The local FastAPI app is `src/api/app.py`; its protected review routes use `src/api/auth.py` to validate signed internal headers from Next.js. Review behavior lives in `src/api/reviews.py`. Staged web reviews persist run-local progress in `runs/<review_id>/review_state.json` using schema version `review_state_v1`.

An owner id is the authenticated user id supplied by the trusted internal FastAPI auth context. A mutation endpoint is any endpoint that can prepare Builder setup, generate a candidate, run comparison, generate verdict, or generate report context. Lineage binding means the requested review id and downstream ids must match the active run-local artifacts and stage order.

## Plan of Work

Sessions 03-05 add owner-aware staged state and enforce it at every protected read or mutation boundary. `src/api/reviews.py` writes `owner_id` when creating staged reviews, checks it before status and recovery, and checks it again before downstream stage mutation. Existing artifact lineage helpers still validate builder setup, candidate, comparison, and verdict ids. `src/api/models.py` bounds the holdings list. `src/api/app.py` rejects oversized review request bodies before model parsing. Staged background work is guarded by process-local active/queued counters configured with `PMRI_STAGED_REVIEW_MAX_WORKERS` and `PMRI_STAGED_REVIEW_MAX_QUEUED`.

Sessions 06-07 harden utility and low-risk surfaces without changing portfolio calculations. `config_ui/app.py` keeps the local Flask UI on loopback, rejects non-local requests unless explicitly allowed, and requires a session CSRF token for POST routes. `scripts/run_review_from_payload.py` creates higher-entropy review ids for new run-local reviews. `src/api/app.py` disables OpenAPI/Swagger/ReDoc HTTP routes unless `PMRI_FASTAPI_ENABLE_DOCS=1` is set. `../../results_dashboard/app.py` validates that `output_dir_final` resolves under the project root before reading generated artifacts.

## Concrete Steps

Implemented edits in Sessions 03-07:

    src/api/auth.py
    src/api/app.py
    src/api/models.py
    src/api/reviews.py
    scripts/run_review_from_payload.py
    config_ui/app.py
    config_ui/templates/config_form.html
    ../../results_dashboard/app.py
    frontend/lib/generated/api-types.ts
    tests/test_fastapi_app.py
    tests/test_frontend_review_bridge.py
    tests/test_config_ui_input_modes.py
    tests/test_config_ui_mvp_first_screen.py
    tests/test_config_ui_rc_cap_removed.py
    tests/test_config_ui_security.py
    tests/test_results_dashboard_security.py
    docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md
    docs/contracts/FASTAPI_V1_API_CONTRACT.md
    TESTING.md
    CHANGELOG.md
    docs/exec_plans/2026-06-15_security_remediation_plan.md

Validation command:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q --basetemp tmp\pytest_security_sessions_03_05_fifth

Observed result:

    18 passed in 6.14s

Additional validation command for Sessions 06-07:

    .\.venv\Scripts\python.exe scripts\generate_fastapi_api_types.py
    .\.venv\Scripts\python.exe -m pytest tests\test_config_ui_input_modes.py tests\test_config_ui_mvp_first_screen.py tests\test_config_ui_rc_cap_removed.py tests\test_config_ui_security.py tests\test_results_dashboard_security.py tests\test_frontend_review_bridge.py::test_create_run_dir_creates_unique_frontend_review_dirs_for_100_users tests\test_fastapi_app.py -q --basetemp tmp\pytest_security_sessions_06_07
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_contract_governance.py -q --basetemp tmp\pytest_security_sessions_06_07_governance
    npm.cmd run typecheck  # from frontend/
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Observed result:

    36 passed in 9.26s
    FastAPI contract governance OK.
    4 passed in 3.37s
    tsc --noEmit completed successfully.
    docs verification: OK

## Validation and Acceptance

Acceptance for Sessions 03-05 is:

- Staged review creation writes `owner_id` into `review_state_v1`.
- `GET /api/v1/reviews/{review_id}/status` rejects a different signed internal user with HTTP 403.
- `GET /api/v1/reviews/{review_id}` rejects ownerless or different-owner recovery.
- Downstream mutation endpoints reject owner mismatch and reject out-of-order stage progression with HTTP 409.
- Portfolio request validation rejects more than 50 holdings.
- Review POST bodies larger than `PMRI_FASTAPI_MAX_BODY_BYTES` are rejected before diagnosis work.
- Staged worker limits return HTTP 429 when configured capacity is exhausted.
- `tests/test_fastapi_app.py` passes.

Additional acceptance for Sessions 06-07 is:

- Config UI mutating routes reject missing/invalid CSRF tokens with HTTP 403 and accept the session token rendered by the page.
- Config UI rejects non-local requests unless `PMRI_CONFIG_UI_ALLOW_REMOTE=1` is explicitly set.
- Config UI starts on `127.0.0.1` and debug mode is opt-in through `PMRI_CONFIG_UI_DEBUG=1`.
- New `frontend_review_*` ids include a timestamp plus a 16-byte URL-safe random token.
- FastAPI `/openapi.json`, `/docs`, and `/redoc` HTTP routes are disabled by default and enabled only with `PMRI_FASTAPI_ENABLE_DOCS=1`.
- Results Dashboard returns a safe error instead of reading `output_dir_final` paths that resolve outside the project root.
- The deferred hardening worklist is reconciled in `TESTING.md`, `CHANGELOG.md`, and the FastAPI API contract.

## Idempotence and Recovery

The changes are additive and can be rerun. Ownerless legacy local reviews cannot be recovered through protected routes; restart the review to create a state file with an owner. Worker limits are process-local and reset when FastAPI restarts. To tune local capacity, set `PMRI_STAGED_REVIEW_MAX_WORKERS`, `PMRI_STAGED_REVIEW_MAX_QUEUED`, or `PMRI_FASTAPI_MAX_BODY_BYTES` before launching FastAPI. FastAPI docs can be enabled for local development with `PMRI_FASTAPI_ENABLE_DOCS=1`. Config UI remote access remains disabled by default; if an operator deliberately sets `PMRI_CONFIG_UI_ALLOW_REMOTE=1`, they must also provide a stable `PMRI_CONFIG_UI_SECRET_KEY` and an external network boundary.

## Artifacts and Notes

Important evidence from Sessions 03-05:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q --basetemp tmp\pytest_security_sessions_03_05_fifth
    # Result: 18 passed in 6.14s

Important evidence from Sessions 06-07:

    .\.venv\Scripts\python.exe -m pytest tests\test_config_ui_input_modes.py tests\test_config_ui_mvp_first_screen.py tests\test_config_ui_rc_cap_removed.py tests\test_config_ui_security.py tests\test_results_dashboard_security.py tests\test_frontend_review_bridge.py::test_create_run_dir_creates_unique_frontend_review_dirs_for_100_users tests\test_fastapi_app.py -q --basetemp tmp\pytest_security_sessions_06_07
    # Result: 36 passed in 9.26s
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    # Result: FastAPI contract governance OK.
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_contract_governance.py -q --basetemp tmp\pytest_security_sessions_06_07_governance
    # Result: 4 passed in 3.37s
    npm.cmd run typecheck
    # Result: tsc --noEmit completed successfully.
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    # Result: docs verification: OK

## Interfaces and Dependencies

`src/api/auth.py` defines:

    @dataclass(frozen=True)
    class InternalAuthContext:
        user_id: str

    def require_internal_auth(...) -> InternalAuthContext

`src/api/reviews.py` now treats service functions as owner-aware:

    create_staged_review(request, *, owner_id)
    get_staged_review_status(review_id, *, owner_id)
    recover_review_diagnosis(review_id, *, owner_id)
    prepare_builder_setup(review_id, request, *, owner_id)
    generate_candidate_from_builder(review_id, request, *, owner_id)
    run_current_vs_candidate(review_id, request, *, owner_id)
    generate_decision_verdict(review_id, request, *, owner_id)
    generate_report_grounding(review_id, request, *, owner_id)

`src/api/models.py` bounds `PortfolioInput.holdings` to 1-50 rows. `src/api/app.py` uses `PMRI_FASTAPI_MAX_BODY_BYTES` for protected review request body bounds. `src/api/reviews.py` uses `PMRI_STAGED_REVIEW_MAX_WORKERS` and `PMRI_STAGED_REVIEW_MAX_QUEUED` for process-local staged worker limits.

Session 06-07 interfaces:

    config_ui/app.py: POST routes require `X-CSRF-Token`; local-only access can be bypassed only by `PMRI_CONFIG_UI_ALLOW_REMOTE=1`.
    src/api/app.py: OpenAPI/Swagger/ReDoc HTTP routes require `PMRI_FASTAPI_ENABLE_DOCS=1`.
    scripts/run_review_from_payload.py: create_run_dir() emits `frontend_review_<timestamp>_<22-char-token>` for new reviews.
    ../../results_dashboard/app.py: output_dir_final must resolve under PROJECT_ROOT.

Revision note (2026-06-15 / Codex): Updated this living plan after implementing Sessions 06-07 so the next contributor can restart from the file and see completed hardening, decisions, validation evidence, and remaining Sessions 08-09 work.
