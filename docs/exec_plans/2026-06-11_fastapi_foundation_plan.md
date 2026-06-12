# FastAPI Foundation and Contract-First Frontend Migration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is self-contained for a new
contributor who has only the current working tree and this file.

## Purpose / Big Picture

Portfolio MRI currently has a working local frontend-to-backend vertical flow, but the normal
frontend path still uses Next.js API routes to launch Python scripts and then read generated JSON
files from `runs/frontend_review_*`. That bridge is acceptable for a local demo, but it is not the
strong long-term foundation for a product whose website must reliably display Python portfolio
diagnostics, candidate tests, comparisons, verdicts, and grounded report text.

After this plan is implemented, the normal frontend path will call a local FastAPI backend. FastAPI
will expose typed API endpoints, Pydantic models will define request and response contracts,
OpenAPI will describe those contracts, and the frontend will consume generated TypeScript types
instead of guessing backend JSON shapes. The product flow remains diagnosis-first and
current-portfolio-first: a candidate is a diagnostic test, comparison is trade-off evidence, and
Decision Verdict is non-binding decision support.

This plan intentionally starts with a read-only audit and documentation baseline before any FastAPI
code is added. Session 00 must not change Python calculations, frontend behavior, dependencies,
generated artifacts, root `config.yml`, or the existing bridge runtime.

## Progress

- [x] (2026-06-11) Session 00 created this FastAPI foundation ExecPlan, registered it as the Active
  plan, and wrote the read-only audit report at
  `docs/audits/2026-06-11_fastapi_foundation_session00_audit.md`. No FastAPI code, dependency
  changes, frontend runtime changes, Python calculation changes, or generated output refreshes were
  implemented in Session 00.
- [x] (2026-06-11) Session 01 designed the FastAPI v1 API contract and recorded public API
  envelopes versus internal artifacts in `docs/contracts/FASTAPI_V1_API_CONTRACT.md`. It also
  recorded the diagnosis interpretation research baseline at
  `docs/audits/2026-06-11_diagnosis_interpretation_framework_research.md`, tying external
  portfolio-risk research to the current evidence-to-diagnosis framework. No FastAPI code,
  dependency changes, frontend route switches, Python calculation changes, root `config.yml`
  changes, or generated-output refreshes were implemented in Session 01.
- [x] (2026-06-11) Session 02 added the FastAPI application skeleton at `src/api/app.py`, exposed
  `GET /api/v1/health`, confirmed `/openapi.json` includes only the Session 02 API surface, added
  FastAPI runtime/test dependencies, and covered the health/OpenAPI surface with
  `tests/test_fastapi_app.py`. The frontend remains on the existing Next.js-to-Python bridge; no
  portfolio calculations, generated review artifacts, root `config.yml`, or frontend routes were
  changed.
- [x] (2026-06-11) Session 03 added typed Pydantic API contracts in `src/api/models.py`, registered
  the full MVP FastAPI route surface as safe `stage_not_ready` OpenAPI placeholders, generated
  frontend TypeScript contract types at `frontend/lib/generated/api-types.ts`, and added the
  regeneration script `scripts/generate_fastapi_api_types.py`. The frontend still uses the existing
  Next.js-to-Python bridge; no portfolio calculations, generated review artifacts, root
  `config.yml`, dependency changes, or frontend route switches were made.
- [x] (2026-06-11) Session 04 migrated diagnosis review creation and safe review recovery to
  FastAPI. `POST /api/v1/reviews` now runs the existing deterministic
  `diagnosis_plus_problem` Python review path through `src/api/reviews.py` and returns a typed
  public envelope with review summary, diagnosis, Launchpad cards, safe artifact refs, lineage, and
  evidence quality. `GET /api/v1/reviews/{review_id}` now recovers only diagnosis/evidence/
  hypothesis setup state from a matching run-local `review_result.json` and explicitly does not
  restore candidate/comparison/verdict/report artifacts as active state. Builder, candidate,
  comparison, verdict, and report endpoints remain `501`/`stage_not_ready` placeholders. The
  frontend route path still uses the existing Next.js `/api/portfolio/*` bridge until a later
  route-switch session; no portfolio calculations, generated artifact schemas, dependency changes,
  root `config.yml`, or downstream stage behavior changed.
- [x] (2026-06-11) Session 05 migrated Builder setup and Candidate Generation to FastAPI.
  `POST /api/v1/reviews/{review_id}/builder` now prepares the selected-card Builder setup through
  the existing run-local Builder handoff and returns a typed setup envelope. `POST
  /api/v1/reviews/{review_id}/candidate` now resolves the active `builder_setup_id`, verifies
  same-review/same-card lineage, delegates to the existing one-candidate generation path, and
  returns a typed candidate envelope with compare readiness. Comparison, verdict, and report
  endpoints remain `501`/`stage_not_ready` placeholders. The visible frontend route path still uses
  the existing Next.js `/api/portfolio/*` bridge until a later route-switch session; no portfolio
  formulas, generated artifact schemas, dependency changes, root `config.yml`, or downstream
  comparison/verdict/report behavior changed.
- [x] (2026-06-11) Session 06 migrated Comparison, Verdict, and Report grounding to FastAPI.
  `POST /api/v1/reviews/{review_id}/comparison` now verifies the active run-local candidate,
  delegates to the existing one-candidate Block 8 comparison path, and returns a typed public
  comparison envelope. `POST /api/v1/reviews/{review_id}/verdict` resolves the same-candidate
  comparison, delegates to the existing Decision Verdict writer, and returns non-binding decision
  support in the public envelope. `POST /api/v1/reviews/{review_id}/report` verifies the active
  verdict, delegates to the existing grounded `ai_commentary_context.json` writer, and returns a
  compact deterministic report preview with `llm_generated=false`. The visible frontend route path
  still uses the existing Next.js `/api/portfolio/*` bridge until a later route-switch session; no
  portfolio formulas, generated review artifact schemas, dependency changes, root `config.yml`,
  frontend route switches, or PDF refreshes were made.
- [x] (2026-06-11) Session 07 retired the old Next.js-to-Python script bridge from the
  normal frontend path. The existing Next.js `/api/portfolio/*` URLs remain as compatibility
  routes for current screens, but they now proxy to FastAPI v1 endpoints and read same-run
  artifacts only to preserve the existing UI adapter shape. FastAPI `CreateReviewRequest` now
  accepts real cash rows so the route switch preserves the existing frontend input contract.
  `scripts/run_review_from_payload.py` remains a legacy/debug tool and an internal helper reused
  by FastAPI, but it is no longer spawned by the normal frontend route handlers.
- [x] (2026-06-11) Session 08 added dynamic FastAPI contract governance. The new
  `docs/contracts/FASTAPI_SCREEN_MAPPING.json` maps every live FastAPI v1 operation and every
  top-level public response `data` field to approved Core MVP screen routes, while
  `scripts/verify_fastapi_contract_governance.py` and
  `tests/test_fastapi_contract_governance.py` verify that the live OpenAPI schema, generated
  `frontend/lib/generated/api-types.ts`, and screen mapping stay synchronized. Backend schema
  changes now require regenerated frontend types and explicit screen mapping before UI promotion.
- [x] (2026-06-11) Session 09 simplified frontend display adapters. Diagnosis, Evidence,
  Hypothesis, Comparison, Verdict, and Report screens now consume compact display state from
  `reviewState` instead of reading `reviewResult.outputs.*` directly; Stress Test Lab display data is
  compacted into the review summary; the report proxy returns a `report_display_model` derived from
  the FastAPI public `ReportResponse` envelope. Raw same-run artifact fields remain in the
  compatibility proxy only as fallback/debug evidence while the normal screen path uses display
  models.
- [x] (2026-06-11) Session 10 completed final acceptance, browser QA, and handoff. Final
  verification passed: FastAPI contract governance OK; focused Python tests 45 passed; frontend API
  route tests 8 passed; frontend static smoke 1 passed; frontend typecheck and production build
  passed; docs verification OK; docs link tests 7 passed. Browser QA used fresh local FastAPI
  (`127.0.0.1:8010`) and Next.js (`127.0.0.1:3010`) servers with cleared browser storage and
  verified the normal frontend path through grounded Report preview. During QA, the default UI
  portfolio produced unavailable candidate comparison metrics; Session 10 fixed the frontend
  Comparison-to-Verdict gate so a current same-candidate comparison can proceed to a valid
  evidence-insufficient Decision Verdict and grounded Report preview instead of blocking. The
  acceptance record is `docs/audits/2026-06-11_fastapi_foundation_session10_acceptance.md`.

## Surprises & Discoveries

- Observation: FastAPI is not yet present in `requirements.txt`.
  Evidence: `requirements.txt` currently includes Flask and pytest but no `fastapi`, `uvicorn`, or
  `httpx`.

- Observation: The current local frontend backend path is already isolated by `reviewId` and
  generated `runs/frontend_review_*` folders.
  Evidence: `../../frontend/README.md`, `../contracts/ARTIFACT_TO_SCREEN_MAP.md`, and
  `scripts/run_review_from_payload.py` document or implement run-local review folders and
  same-run stage guards.

- Observation: The current frontend has the intended seven-route MVP chain and no separate
  Candidate or Monitoring route.
  Evidence: `frontend/app` contains `portfolio-input`, `diagnosis`, `evidence`, `hypothesis`,
  `comparison`, `verdict`, and `report`.

- Observation: Next.js portfolio API routes already centralize Python executable resolution in a
  helper, but they still use `spawn` to run Python scripts.
  Evidence: `frontend/lib/server/pythonBridge.ts` resolves `.venv\Scripts\python.exe`; targeted
  search shows the API route tree still imports the helper and launches bridge actions.

- Observation: The current Block 4 code already has the core of a professional
  evidence-to-diagnosis framework, but it is distributed across taxonomy, evidence extraction,
  scoring, prioritization, severity/confidence, action-path mapping, and diagnosis builder modules.
  Evidence: `src/block_4/problem_taxonomy.py`, `src/block_4/evidence_extraction.py`,
  `src/block_4/problem_scoring.py`, `src/block_4/problem_prioritization.py`,
  `src/block_4/severity_confidence.py`, `src/block_4/action_path_mapping.py`, and
  `src/block_4/diagnosis_builder.py`.

- Observation: Public materials from Morningstar, BlackRock Aladdin, CFA Institute, MSCI, AQR,
  Vanguard, FactSet, and Axioma support a layered process of portfolio look-through, risk/factor
  decomposition, scenario/stress testing, attribution to decision drivers, and controlled
  portfolio-construction tests.
  Evidence: Session 01 research notes and links in
  `docs/audits/2026-06-11_diagnosis_interpretation_framework_research.md`.

- Observation: Session 02 can prove FastAPI and OpenAPI readiness without touching portfolio
  artifacts.
  Evidence: `GET /api/v1/health` returns the documented public envelope and `/openapi.json` exposes
  only the health path in `tests/test_fastapi_app.py`.

- Observation: Session 03 can publish the future MVP API shape without changing runtime behavior.
  Evidence: the review, Builder, candidate, comparison, verdict, and report routes return safe
  `501`/`stage_not_ready` placeholders, while `/openapi.json` exposes typed request/response schemas
  and `tests/test_fastapi_app.py` proves the generated frontend types match the schema.

- Observation: Session 04 can make diagnosis creation and recovery live in FastAPI without changing
  the portfolio analytics engine or the visible Next.js frontend route path.
  Evidence: `src/api/reviews.py` converts the Pydantic `CreateReviewRequest` to the existing
  frontend-runner payload, invokes `run_from_payload(..., mode=diagnosis_plus_problem)`, maps the
  resulting run-local `review_result.json` into `CreateReviewResponse`, and recovers only
  diagnosis/evidence/hypothesis setup state in `ReviewRecoveryResponse`. `tests/test_fastapi_app.py`
  covers successful create/recover adapters and verifies later endpoints still return
  `stage_not_ready`.

- Observation: Session 05 can make Builder and Candidate runtime live in FastAPI by reusing the
existing bridge helpers directly instead of shelling out through the old Next.js routes.
Evidence: `src/api/reviews.py` calls `prepare_selected_builder_setup(...)` for Builder and
`generate_selected_candidate(...)` for Candidate after resolving the run-local Builder setup id.
`tests/test_fastapi_app.py` covers both public envelopes, and `tests/test_frontend_review_bridge.py`
remains green for the legacy bridge path.

- Observation: Session 06 can complete the backend one-candidate MVP FastAPI chain without
  changing analytics by reusing the existing vertical-loop helpers directly.
  Evidence: `src/api/reviews.py` calls `compare_selected_candidate(...)`,
  `write_selected_candidate_verdict(...)`, and `write_selected_report_context(...)` after resolving
  run-local candidate/comparison/verdict lineage. `tests/test_fastapi_app.py` covers all three live
  public envelopes and generated frontend API types now report `200` response status for
  comparison, verdict, and report operations.

- Observation: Session 07 can retire direct Next.js Python spawning without forcing a full screen
  adapter rewrite yet.
  Evidence: `frontend/lib/server/fastapiBridge.ts` calls FastAPI v1 endpoints from the existing
  `/api/portfolio/*` route handlers, then returns legacy-compatible screen payloads by reading only
  same-run artifacts. `frontend/tests/api-route-tests.cjs` verifies the proxy contract, safe error
  scrubbing, cash-row request mapping, and conservative recovery behavior.

- Observation: Session 08 can make schema drift fail without rewriting screen adapters yet.
  Evidence: `scripts/verify_fastapi_contract_governance.py` compares live OpenAPI, generated
  TypeScript types, and `docs/contracts/FASTAPI_SCREEN_MAPPING.json`; the mapping lists every
  current operation, response schema, data schema, public data field, and approved screen route.


- Observation: Final browser QA found that the backend already supported an evidence-insufficient
  Verdict when comparison metrics were unavailable, but the frontend adapter gate blocked the user
  on the Comparison screen because it required at least one displayable comparison metric.
  Evidence: `POST /api/v1/reviews/{review_id}/verdict` returned `verdict_id=evidence_insufficient`
  for `frontend_review_20260611T154145Z_fe2bd3a3`, while `/comparison` initially displayed
  "Comparison metrics unavailable" without a safe path to Verdict. Session 10 updated
  `frontend/lib/reviewState.tsx` and `frontend/app/comparison/page.tsx` so current comparisons can
  unlock the evidence-insufficient Verdict path.

## Decision Log

- Decision: Session 00 is audit and planning only.
  Rationale: The requested migration is architectural and touches backend contracts, frontend
  state, runtime entrypoints, generated types, docs, and tests. The repository rules require a
  checked-in ExecPlan and source-of-truth audit before broad implementation.
  Date/Author: 2026-06-11 / Codex.

- Decision: FastAPI should become the normal frontend backend API by the end of this plan, but the
  existing bridge remains untouched until replacement endpoints are implemented and tested.
  Rationale: Keeping the working bridge during early sessions lowers risk and preserves the local
  demo while the new contract-first API is introduced incrementally.
  Date/Author: 2026-06-11 / Codex.

- Decision: Dynamic UI does not mean automatic display of every new backend field.
  Rationale: New calculations should be captured by Pydantic/OpenAPI/TypeScript contracts
  automatically, but user-facing screens must still require an explicit artifact-to-screen mapping,
  adapter, wording review, and tests.
  Date/Author: 2026-06-11 / Codex.

- Decision: FastAPI v1 should return typed product envelopes, not raw generated artifact dumps.
  Rationale: The current frontend needs stable, safe, user-facing stage responses with lineage,
  stage status, evidence quality, and safe errors. Raw JSON artifacts remain source evidence or
  internal implementation details and should be translated through adapters before reaching screens.
  Date/Author: 2026-06-11 / Codex.

- Decision: Session 04 should reuse the existing deterministic diagnosis runner rather than create a
  second diagnosis implementation inside FastAPI.
  Rationale: Reusing `scripts/run_review_from_payload.py` in `diagnosis_plus_problem` mode keeps the
  migration scoped to the HTTP boundary and public response envelope. It avoids duplicate portfolio
  validation, data loading, X-Ray, stress, Problem Classification, and Launchpad logic while still
  making the FastAPI diagnosis/recovery API live and testable.
  Date/Author: 2026-06-11 / Codex.

- Decision: Session 05 should reuse the existing Builder and one-candidate generation helpers rather
than create parallel FastAPI-specific Builder/Candidate implementations.
Rationale: The migration boundary is the HTTP API and public envelope, not portfolio formulas,
factory semantics, or generated artifact schemas. Reusing the existing helpers preserves the
same-review/same-card lineage guards and keeps the visible Next.js route path unchanged until the
later route-switch session.
Date/Author: 2026-06-11 / Codex.

- Decision: Session 06 should reuse the existing Block 8/9/report-grounding vertical-loop helpers
  rather than create parallel FastAPI-specific comparison, verdict, or report writers.
  Rationale: The migration boundary is the HTTP API and public envelope, not comparison formulas,
  Decision Verdict mapping, or AI Commentary grounding semantics. Reusing the existing helpers
  preserves same-review/same-card/same-candidate lineage and keeps report grounding deterministic
  with `llm_generated=false`.
  Date/Author: 2026-06-11 / Codex.

- Decision: Session 07 should keep the existing Next.js `/api/portfolio/*` URLs as compatibility
  proxies while removing direct script spawning from the normal frontend path.
  Rationale: Current screens still consume legacy artifact-shaped payloads; a thin proxy lets the
  product path use FastAPI now without mixing a broad frontend adapter rewrite into Session 07.
  Session 09 remains responsible for simplifying screens to consume display models and generated
  API types directly.
  Date/Author: 2026-06-11 / Codex.

- Decision: Session 08 should use a machine-readable FastAPI screen-mapping contract in addition to
  generated TypeScript types.
  Rationale: Generated types prove shape compatibility but do not decide whether a field belongs on
  a screen. The JSON mapping makes UI promotion explicit and testable while keeping Session 09 free
  to refactor adapters without guessing backend contract ownership.
  Date/Author: 2026-06-11 / Codex.

- Decision: Diagnosis interpretation should be modeled as an evidence chain:
  metric signal -> evidence item -> problem hypothesis -> root-cause diagnosis -> suggested test ->
  candidate setup -> comparison success criteria -> verdict.
  Rationale: This keeps the product professional, auditable, and non-hallucinatory: metrics do not
  become recommendations directly, symptoms do not outrank root causes, and suggested actions remain
  diagnostic tests until Decision Verdict evaluates comparison evidence.
  Date/Author: 2026-06-11 / Codex.


- Decision: A current same-candidate comparison may unlock Verdict even when displayable candidate
  metrics are unavailable, as long as the comparison stage completed and the backend can safely
  produce an evidence-insufficient Decision Verdict.
  Rationale: Evidence-insufficient is a valid non-binding outcome. Blocking at Comparison would hide
  the professional decision-support state and contradict the FastAPI contract that Verdict owns
  no-trade, failed/infeasible, and evidence-insufficient outcomes. Comparison still must not crown a
  winner or recommend a trade.
  Date/Author: 2026-06-11 / Codex.

## Outcomes & Retrospective

Session 00 established the implementation baseline and did not change runtime behavior. The audit
confirmed that the existing bridge is coherent enough to migrate in phases: run-local artifacts,
same-review lineage, and product contracts already exist, but the bridge is not yet a formal HTTP
API contract.

Session 01 completed the contract-design milestone. The planned FastAPI v1 surface is now documented
as typed response envelopes, safe error models, endpoint responsibilities, public/internal artifact
boundaries, and lineage rules in `docs/contracts/FASTAPI_V1_API_CONTRACT.md`. Session 01 also
captured a research-backed diagnosis interpretation baseline in
`docs/audits/2026-06-11_diagnosis_interpretation_framework_research.md`. The next session should add
only the FastAPI skeleton, health endpoint, OpenAPI output, and focused tests without switching the
frontend from the existing bridge.

Session 02 completed the FastAPI skeleton milestone. The local backend now has an importable app
factory and app instance in `src/api/app.py`, a health endpoint at `GET /api/v1/health`, and the
standard FastAPI OpenAPI route at `/openapi.json`. The focused test verifies both the public health
envelope and that planned review/builder/candidate/comparison/verdict/report endpoints are not
registered prematurely during that session. Session 03 was then expected to add Pydantic response
models and OpenAPI-to-TypeScript generation without changing the frontend runtime path.

Session 03 completed the contract-first type generation milestone. The FastAPI app now has typed
Pydantic request and response models for the planned MVP API, all future stage routes appear in
OpenAPI, and each non-health route is still a safe blocked placeholder until its runtime migration
session. `scripts/generate_fastapi_api_types.py` regenerates `frontend/lib/generated/api-types.ts`
from the live OpenAPI schema, and the focused tests guard both the API schema and generated file.
The next session should migrate diagnosis creation/recovery to FastAPI without changing Builder,
candidate, comparison, verdict, report, calculations, or generated output policy.

Session 04 completed the diagnosis runtime migration milestone. FastAPI can now create a
diagnosis-first review and recover a completed run-local review through typed public envelopes. The
implementation is intentionally an adapter over the existing deterministic review runner, so it does
not change portfolio calculations, generated artifact schemas, or downstream product stages.
Recovery remains conservative: it restores diagnosis, evidence, and hypothesis setup only, and it
keeps candidate/comparison/verdict/report inactive until those stages are regenerated or verified by
their own future FastAPI endpoints.

Session 05 completed the Builder/Candidate runtime migration milestone. FastAPI can now prepare a
selected-card Builder setup and explicitly generate one diagnostic candidate through typed public
envelopes while still preserving the old visible Next.js route path. The Candidate endpoint resolves
the active `builder_setup_id` from the run-local Builder artifact before delegating to generation, so
stale or mismatched setup ids fail safely instead of silently generating from another card. The next
session should migrate Current-vs-Candidate Comparison, Decision Verdict, and grounded Report context
to FastAPI while preserving the same review/card/candidate lineage.

Session 06 completed the remaining backend runtime migration for the one-candidate MVP chain.
FastAPI can now run Current-vs-Candidate Comparison, generate a non-binding Decision Verdict, and
return grounded report context through typed public envelopes. The implementation remains an adapter
over the existing deterministic vertical-loop helpers and does not change portfolio calculations,
artifact schemas, root configuration, PDFs, or the visible Next.js route path.

Session 07 completed the normal frontend-path bridge retirement milestone. The frontend still calls
the existing Next.js `/api/portfolio/*` URLs, but those handlers are now compatibility proxies to
FastAPI v1 and no longer spawn `scripts/run_review_from_payload.py`. The proxy reads same-run
artifacts only to maintain the current screen adapter payload shape until Session 09. FastAPI input
contracts now preserve instrument and cash holdings, so the route switch does not regress the
Portfolio Input contract. The next session should add dynamic contract governance so backend schema
changes require regenerated frontend types and explicit screen mapping.

Session 08 completed the dynamic contract-governance milestone. FastAPI public schema drift now has
a repeatable gate: generated TypeScript types must match live OpenAPI, every operation must be listed
in the screen map, and every top-level response `data` field must have explicit route ownership
before frontend use. This session did not change FastAPI runtime behavior, frontend screen behavior,
portfolio calculations, generated review artifact schemas, root `config.yml`, or PDFs. Session 09 then
simplified frontend adapters so screens consume display models instead of raw backend artifacts.

Session 09 completed the frontend display-adapter simplification milestone. The visible screens now
read display-ready state (`reviewSummary`, `stressLabModel`, `builderSetup`, candidate/comparison/
verdict summaries, and `report_display_model`) instead of parsing raw backend artifact payloads. The
compatibility proxy still keeps raw same-run fields available for staged migration, tests, and debug
evidence, but normal screen rendering no longer depends on `reviewResult.outputs.*`. No portfolio
calculations, generated artifact schemas, root `config.yml`, PDFs, or FastAPI public schemas changed.
Session 10 completed final acceptance, browser QA, the evidence-insufficient verdict gate fix, and handoff.

## Context and Orientation

The current product truth is diagnosis-first and current-portfolio-first. The user enters a
portfolio, the system diagnoses that portfolio, tests one selected candidate hypothesis, compares
current versus candidate, issues a non-binding Decision Verdict, and creates grounded report text.
The current implementation is still partly file-driven and uses generated JSON artifacts as the
machine-readable source of truth.

The current frontend lives under `frontend/`. The visible MVP route chain is:
`/portfolio-input -> /diagnosis -> /evidence -> /hypothesis -> /comparison -> /verdict -> /report`.
The Next.js portfolio API routes live under `frontend/app/api/portfolio/`. They call the Python
bridge script `scripts/run_review_from_payload.py`, which writes and reads run-local files under
`runs/frontend_review_*`.

The existing product contract layer lives in `docs/contracts/`. The most relevant documents are
`PRODUCT_FLOW_CONTRACT.md`, `ARTIFACT_TO_SCREEN_MAP.md`, `SCREEN_CONTRACTS.md`,
`PRESENTATION_LANGUAGE_RULES.md`, `QA_CONTRACT.md`, and `DOC_SYNC_CONTRACT.md`. These documents
already define screen ownership, artifact routing, stale-data boundaries, forbidden UI language,
and verification expectations.

The FastAPI foundation must not promote advanced or legacy artifacts into the Core MVP. Root
`run_result.json`, root `portfolio_weights.yml`, candidate folders, PDFs, and old report sidecars
must remain non-authoritative for the active frontend review unless an explicit legacy/debug path is
being tested.

## Plan of Work

Session 01 will create the API contract before implementation. It will define the local FastAPI v1
endpoint list, request models, response envelopes, safe error model, and artifact mapping. It will
also state which existing JSON files remain internal implementation details and which fields are
safe to expose to the frontend.

Session 02 added only the FastAPI skeleton: `fastapi`, `uvicorn`, and `httpx` test support in the
project dependencies, a small app module with `GET /api/v1/health`, OpenAPI output, and a focused
test. It did not switch any frontend route to FastAPI.

Session 03 introduced Pydantic models and OpenAPI-to-TypeScript type generation. The frontend gained
generated API types, and the project gained a generator command and tests proving the schema contains
the required MVP endpoints. Session 04 then made the review creation and recovery endpoints live in
FastAPI while leaving Builder, Candidate Generation, Comparison, Verdict, and Report as safe typed
placeholders.

Sessions 04 through 06 migrated the existing bridge stages one group at a time: diagnosis first,
then Builder/Candidate, then Comparison/Verdict/Report. Each session preserved the same-review,
same-card, same-candidate lineage rules.

Session 07 retired the old bridge from the normal frontend path. `scripts/run_review_from_payload.py`
remains as a legacy/debug tool and as an internal helper reused by FastAPI, but the normal Next.js
portfolio API route handlers now call FastAPI instead of spawning it.

Sessions 08 through 09 added dynamic contract governance and simplified frontend adapters. Session
10 will prove the final flow with tests, browser QA, and handoff.

## Concrete Steps

Sessions 00 through 09 have already created the plan, audit report, contract baseline, FastAPI
skeleton, health endpoint, typed OpenAPI surface, generated frontend API types, live runtime
adapters for the one-candidate MVP chain, the Next.js FastAPI compatibility proxy layer, the
dynamic FastAPI contract-governance gate, and frontend display-model adapters. The next implementer
should begin Session 10 by reading this file, `AGENTS.md`, `RULES.md`, `WORKFLOW.md`, `SPEC.md`,
`OUTPUTS.md`, `TESTING.md`, `../../frontend/README.md`, the FastAPI contract, the FastAPI screen
mapping, `frontend/lib/reviewState.tsx`, and `frontend/lib/server/fastapiBridge.ts`.

Use Windows PowerShell commands from the repository root unless a command explicitly says to run
from `frontend/`.

Before adding FastAPI code in Session 02, verify Python availability according to the project
rules:

    py -3 --version
    python --version
    where py
    where python
    .\.venv\Scripts\python.exe --version

## Validation and Acceptance

Session 00 acceptance is complete when:

- this ExecPlan exists;
- `docs/exec_plans/README.md` points to it as the Active plan;
- the Session 00 audit report exists;
- no FastAPI code, dependency, frontend runtime, Python calculation, or generated-output refresh was
  performed;
- the planned verification commands are run and any failure is recorded honestly.

For future implementation sessions, the standard recurring verification set is:

    cd frontend
    npm.cmd run test:api
    npm.cmd run test:smoke
    npm.cmd run typecheck
    npm.cmd run build
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q

Later FastAPI sessions must add focused FastAPI tests and migrate this verification set away from
bridge-only tests once the normal frontend path no longer uses the bridge.

Session 08 governance verification:

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_fastapi_contract_governance.py -q
    cd frontend
    npm.cmd run typecheck

After Session 08, intentional FastAPI public schema changes must regenerate
`frontend/lib/generated/api-types.ts` and update `docs/contracts/FASTAPI_SCREEN_MAPPING.json`.

## Idempotence and Recovery

The migration must remain recoverable even after the old bridge is retired from the normal frontend
path. If a FastAPI endpoint fails, the compatibility proxy should return a safe error rather than
falling back to direct Python script spawning. Generated run folders under `runs/`, caches, `.next`,
and pytest temporary directories must not be treated as source. Do not delete or stage generated
output unless a later session explicitly targets generated artifact refresh.

## Artifacts and Notes

Session 00 audit report:

    docs/audits/2026-06-11_fastapi_foundation_session00_audit.md

Session 01 contract and research baseline:

    docs/contracts/FASTAPI_V1_API_CONTRACT.md
    docs/audits/2026-06-11_diagnosis_interpretation_framework_research.md

Planned FastAPI app path:

    src/api/app.py

Planned generated frontend type path:

    frontend/lib/generated/api-types.ts

Session 03 generator and Session 05 runtime adapter:

    scripts/generate_fastapi_api_types.py
    src/api/reviews.py

These paths are not created in Session 00 except for this plan and the audit report.

## Interfaces and Dependencies

The future FastAPI API must expose these local MVP endpoints:

    GET  /api/v1/health
    POST /api/v1/reviews
    GET  /api/v1/reviews/{review_id}
    POST /api/v1/reviews/{review_id}/builder
    POST /api/v1/reviews/{review_id}/candidate
    POST /api/v1/reviews/{review_id}/comparison
    POST /api/v1/reviews/{review_id}/verdict
    POST /api/v1/reviews/{review_id}/report

The Pydantic contract layer now includes request and response models for portfolio input, review
envelope, Builder setup result, Candidate Generation result, Current-vs-Candidate result, Decision
Verdict result, Report grounding result, and safe error response.

The frontend contract layer now has generated TypeScript types from the FastAPI OpenAPI schema. New
backend fields may be generated into types, but they must not appear in user-facing UI without an
explicit screen contract, adapter, and test.



Session 10 completed the FastAPI foundation acceptance and handoff milestone. The normal local
frontend path now runs through FastAPI-backed compatibility routes from Portfolio Input through
Report preview, with contract governance, focused backend tests, frontend API/smoke/typecheck/build,
documentation verification, and browser QA all passing. Browser QA also closed a final adapter gap:
when comparison metrics are unavailable, the UI now exposes the valid evidence-insufficient Verdict
path instead of treating the comparison as a dead end. The FastAPI public schema, portfolio
calculations, generated review artifact schemas, root `config.yml`, and PDF behavior were not
changed.
