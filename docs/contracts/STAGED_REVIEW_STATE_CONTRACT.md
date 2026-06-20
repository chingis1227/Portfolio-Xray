# Staged Review State Contract

Status: **implemented staged-review contract for the Portfolio MRI web migration**.

This document is the source of truth for the implemented web execution contract where a user clicks
`Run diagnosis`, receives a `review_id` immediately, sees stage progress, and then receives partial
results as backend stages complete. Sessions 2-7 implement the additive backend start/status
endpoints, run-local `review_state.json`, diagnosis-stage synchronization, deterministic Demo / QA
execution, frontend polling, optional compact Supabase persistence, account workspace recovery, refresh recovery, and explicit
downstream stage synchronization for candidate, comparison, verdict, and report. The current
synchronous FastAPI endpoint remains available as backend compatibility until a later retirement plan
explicitly removes it.

## Purpose

The staged-review contract closes the architectural gap between the frontend, which already thinks
in `reviewId`, stage, candidate, comparison, verdict, and report terms, and the backend, which still
uses run-local CLI artifacts as the primary execution surface. The target behavior is:

```text
User clicks Run diagnosis
-> backend creates review_id immediately
-> Portfolio Input stores the active review_id and navigates to Diagnosis without waiting for the full run
-> Diagnosis shows progress
-> backend runs stages
-> Diagnosis polls compact stage state
-> Diagnosis recovers same-run artifacts and unlocks partial results when the diagnosis chain is ready
```

This contract does not change formulas, stress scenarios, optimizer behavior, candidate generation
logic, or generated artifact schemas. It defines the web state wrapper and stage semantics around
existing deterministic artifacts.

## Source-of-truth order

Use this document for staged review state, stage names, stage status semantics, staged API shape, and
Supabase persistence boundaries. Use the following documents for lower-level authority:

- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for product step order and user-facing boundaries.
- `docs/contracts/FASTAPI_V1_API_CONTRACT.md` for existing FastAPI envelope and endpoint rules.
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` for artifact-to-route mapping and stale-data rules.
- `OUTPUTS.md` for generated-vs-source boundaries and output folders.
- `frontend/README.md` for current frontend route and browser-storage behavior.
- `docs/supabase/README.md` for optional compact Supabase persistence.
- `docs/specs/portfolio_review_workflow_spec.md` for portfolio-first diagnosis semantics.

If this document conflicts with formula-level or artifact-level specs, the owning detailed spec and
current code win. The staged wrapper must adapt to canonical artifacts; it must not invent new
calculation outputs.

## Staged API

The additive backend API is implemented in `src/api/app.py`, `src/api/models.py`, and
`src/api/reviews.py`. `src/api/reviews.py` remains the route and execution adapter, while
`src/api/staged_review_state.py` owns the narrower FastAPI-adjacent state helpers for
`review_state.json` IO, owner checks, safe public status projection, missing-state envelopes, and
legacy raw artifact-ref sanitization. The Review Case boundary lives in `src/review_case/`; it
supplies the canonical stage order, safe run-local artifact reference validation, an artifact
manifest helper for the existing public `artifacts` map, a narrow stage state machine for status
transitions, a downstream stage-readiness helper for explicit candidate/comparison/verdict/report
gates, a downstream artifact-lineage helper for candidate/comparison/verdict consistency over
existing generated dictionaries, a downstream evidence-chain context helper for bounded
comparison/verdict/report display context over existing generated dictionaries, an internal
Evidence Graph for relating stages, artifacts, and source evidence, a narrow screen read-model
projection for future UI/API migration, a
MarketDataSnapshot metadata seam for summarizing already-existing run metadata/provider/data-policy
evidence, an inactive-by-default execution-queue seam with an opt-in RQ/Redis prototype and
in-process fallback, and a run-local artifact storage seam that keeps existing run-local artifacts
as the source of truth while validating future S3/R2 object keys, and a run-local repository for
loading and saving `ReviewCase` objects through the existing `review_state_v1` file while preserving
the public API and artifact schemas.
The FastAPI state helper can project the sanitized public staged status into the internal screen read
model for compatibility tests and later API migration. It does this through an internal status
projection bundle that pairs the existing public `StagedReviewStatusResponse` with the internal
`ReviewCaseScreenReadModel`; current FastAPI routes must still return only the public status
envelope. The frontend counterpart is
`frontend/lib/review/reviewCaseClientState.ts`, which projects the public staged status shape into
screen-ready stage progress, safe artifact availability, progress counts, and diagnosis-chain
readiness without changing FastAPI routes or envelopes. Active-review compact progress should use
that helper rather than duplicating stage readiness or artifact-safety rules.

```text
POST /api/v1/reviews/staged
GET /api/v1/reviews/{review_id}/status
```

`POST /api/v1/reviews/staged` starts a web review and returns without waiting for the full Python
diagnosis. It creates the run folder, writes the initial payload and `review_state.json`, starts
background execution, and returns a compact response. Protected review API calls require a signed internal Next.js-to-FastAPI auth context. Staged creation stores that authenticated user id as `owner_id` in `review_state.json`; status, recovery, and downstream mutation endpoints must reject ownerless or different-owner state instead of recovering or mutating another user's run-local review.

```json
{
  "api_version": "v1",
  "schema_version": "review_started_v1",
  "review_id": "frontend_review_...",
  "stage": "diagnosis",
  "status": "running",
  "current_stage": "input",
  "mode": "demo_qa"
}
```

`GET /api/v1/reviews/{review_id}/status` returns the current `review_state_v1` document mapped into
a public, safe response. The status endpoint is the backend source of truth for staged progress and
recovery. It must not scan random run folders, expose raw generated artifact dumps, or return a
review whose stored `owner_id` differs from the signed internal caller.

The existing `POST /api/v1/reviews` synchronous diagnosis endpoint remains a compatibility path until
the staged path is fully adopted and tested.

Live mode still uses the existing diagnosis adapter in the background, but the staged
wrapper now synchronizes each diagnosis-stage row after execution. Required artifacts mark `input`,
`data_load`, `xray`, `stress`, `problem_classification`, and `launchpad_builder` completed when
present. Missing Client Fit context is non-blocking and records `client_fit` as `partial` so the UI
can use the `not_provided` compatibility state. Missing required artifacts produce a safe
`ARTIFACT_MISSING` error at the first affected stage while preserving earlier completed stages.
Runtime failures produce safe staged errors without tracebacks or absolute paths. `candidate`,
`comparison`, `verdict`, and `report` start as pending after diagnosis and are updated when the user explicitly runs those downstream actions. Downstream mutation is stage-gated: Candidate requires completed diagnosis/Launchpad Builder state, Comparison requires Candidate, Verdict requires Comparison, and Report requires Verdict. A later downstream blocker or failure must preserve earlier completed diagnosis evidence and leave the overall review recoverable as partial rather than erasing the run.

Live staged diagnosis reuses `ReviewRunContext` by default so daily/monthly/factor/macro inputs are prepared once and shared inside the backend run. Operators may set `PMRI_STAGED_REVIEW_SHARED_CONTEXT=0` only as a diagnostic rollback switch. This is an orchestration and performance boundary: formulas, required artifacts, public response fields, and stage semantics must remain unchanged.

`demo_qa` execution routes through frozen fixture materializers instead of live market-data-backed adapters. The fixture materializer writes the same run-local artifact roles needed by the
diagnosis stages under `analysis_subject/` (`run_metadata.json`, `portfolio_xray.json`,
`stress_report.json`, `client_fit_check.json`, `problem_classification.json`,
`candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `output_manifest.json`, and
`site_explanation_bundle.json`). This is for demo and QA reliability only; it does not replace live mode, CLI portfolio review behavior, formulas, or generated artifact schemas. Session 7 extends this deterministic fixture path through explicit candidate, comparison, verdict, and report actions so browser vertical QA can prove the whole route chain without external market-data providers.

## Canonical review state

The run-local authoritative file for staged web execution is `review_state.json` at the root of the
active `runs/frontend_review_*` folder. It uses this target shape:

New architecture code must treat `src/review_case/RunLocalReviewCaseRepository` as the typed
load/save seam for this file when working with the `ReviewCase` domain model. Existing staged API
compatibility code may still read or update the raw dictionary shape where required to preserve
legacy sanitization and public response behavior.

FastAPI route code that must work with raw staged dictionaries should use
`src/api/staged_review_state.py` rather than adding more state IO or public-status projection logic
to `src/api/reviews.py`. This helper is behavior-preserving: it writes the same `review_state_v1`
file, uses the same owner-check failure codes, and keeps the legacy public sanitizer that replaces
absolute local artifact refs with `logical://...` fallbacks without changing generated artifact
schemas.

New architecture code that updates one stage row should use
`src/review_case/ReviewCaseStageMachine` for the stage/status transition rules. The state machine is
intentionally narrow: it validates the requested canonical stage and status, preserves existing
`started_at` values, stamps terminal statuses with `completed_at`, updates `current_stage`, and lets
the FastAPI adapter keep its existing artifact-reference sanitizer for raw compatibility paths.

New architecture code that checks whether an explicit downstream stage may run should use
`src/review_case/stage_readiness.py`. The readiness helper reads the existing raw staged-state
dictionary, keeps the current `stage_not_ready` code and public-safe messages through the thin
FastAPI wrappers in `src/api/reviews.py`, and does not add fields to `review_state_v1` or the public
staged status response.

New architecture code that validates active downstream artifact lineage should use
`src/review_case/downstream_lineage.py`. The lineage helper consumes the existing
`candidate_generation.json`, `current_vs_candidate.json`, and `decision_verdict.json` dictionaries
and validates active candidate, comparison, and verdict consistency without changing generated
schemas. The FastAPI adapter keeps thin wrappers that translate internal lineage errors into the
same public safe-error envelopes and messages used before this helper existed.

New architecture code that builds bounded downstream evidence-chain display context should use
`src/review_case/downstream_context.py`. The context helper consumes existing
`candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, and
`ai_commentary_context.json` dictionaries, then serializes to the same public field names used by
comparison, verdict, and report response envelopes. It does not add fields to `review_state_v1`,
change generated artifact schemas, or change public response envelopes.

New architecture code that builds or validates the top-level staged `artifacts` map should use
`src/review_case/ReviewCaseArtifactManifest`. The manifest validates stable artifact keys and safe
run-local or `logical://` refs, then serializes back to the same public `dict[str, str]` shape. It
does not replace stage-level `artifact_refs`, generated artifact schemas, or the existing public
status-response sanitizer for old raw state that may contain unsafe refs.

New architecture code that needs an artifact-storage boundary should use
`src/review_case/artifact_storage.py`. The only active storage adapter is run-local filesystem
storage. It builds the same manifest entries from existing files under the active run folder and
does not upload, copy, rename, or migrate generated artifacts. Operators may set future-looking
S3-compatible or Cloudflare R2 environment names, but this session treats them as inactive intent and
falls back to run-local behavior. The storage config may expose safe internal metadata such as
requested backend, key prefix, whether a bucket or endpoint was configured, and bounded warnings. It
must not expose credentials or endpoint values in public envelopes, and it must not add fields to
`review_state_v1`.

New architecture code that needs to relate canonical stages, artifact manifest entries, and source
evidence should use `src/review_case/ReviewCaseEvidenceGraph`. The graph is internal and additive:
it validates declared stage, artifact, and source nodes plus safe run-local or `logical://` refs, but
it does not add fields to `review_state_v1`, replace generated artifact schemas, or force old raw
staged-state compatibility paths through strict validation.

New architecture code that needs screen-facing projections should use
`src/review_case/ReviewCaseScreenReadModel`. The read model is internal and additive: it projects a
validated `ReviewCase` plus an optional `ReviewCaseEvidenceGraph` into stage progress, artifact
availability, and evidence-link summaries for later API/frontend migration. It does not change
`review_state_v1`, public FastAPI status envelopes, generated artifact schemas, or the existing
public status-response sanitizer for old raw state. FastAPI compatibility code may build this read
model from the already-sanitized public status response to prove migration readiness. When it needs
both objects, it should use the internal status projection bundle in `src/api/staged_review_state.py`
so the public envelope and read model are derived from the same sanitized data. Public clients must
still receive only the existing staged status response.

Frontend code that needs the browser/client version of that projection should use
`frontend/lib/review/reviewCaseClientState.ts`. It accepts the existing staged start/status shapes
and compact stored progress, returns a `review_case_client_state_v1` display model, and drops
absolute or parent-directory artifact refs before exposing artifact availability to screens. It is
additive and does not add fields to the public FastAPI status response. Active-review state compacts
new staged status through this helper so screen readiness uses one client read-model rule set.

```json
{
  "schema_version": "review_state_v1",
  "review_id": "frontend_review_...",
  "status": "running",
  "current_stage": "xray",
  "mode": "demo_qa",
  "owner_id": "authenticated-user-id",
  "created_at": "2026-06-14T08:00:00Z",
  "updated_at": "2026-06-14T08:00:03Z",
  "stages": {
    "input": {
      "status": "completed",
      "started_at": "2026-06-14T08:00:00Z",
      "completed_at": "2026-06-14T08:00:01Z",
      "artifact_refs": []
    },
    "data_load": {
      "status": "completed",
      "artifact_refs": []
    },
    "xray": {
      "status": "running",
      "artifact_refs": ["analysis_subject/portfolio_xray.json"]
    }
  },
  "artifacts": {
    "portfolio_xray": "analysis_subject/portfolio_xray.json",
    "stress_report": "analysis_subject/stress_report.json",
    "client_fit_check": "analysis_subject/client_fit_check.json",
    "problem_classification": "analysis_subject/problem_classification.json",
    "candidate_launchpad": "analysis_subject/candidate_launchpad.json",
    "portfolio_alternatives_builder": "analysis_subject/portfolio_alternatives_builder.json"
  },
  "provider_status": {
    "source": "frozen_fixture",
    "freshness": "fixed_demo_dataset",
    "message": "Demo / QA mode uses deterministic fixture data."
  },
  "safe_error": null
}
```

Public responses may include compact summaries derived from this state, but they must not expose
absolute local paths, Python tracebacks, secrets, environment variables, or raw artifact trees.

MarketDataSnapshot metadata is an internal Review Case seam, not a new public `review_state_v1`
field. `src/review_case/market_data_snapshot.py` may summarize already-existing
`run_metadata.json`, provider status, and `data_policy.json` evidence into a stable internal
`review_case_market_data_snapshot_v1` shape. That shape may be used by later queue, storage, or
screen read-model work to identify the disclosed market-data basis of a review, but it must not be
treated as a raw price-panel fingerprint and must not trigger provider calls, formula changes, API
envelope changes, or generated artifact schema changes.

## Stage names and route mapping

The canonical stage names are:

```text
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
```

The web route mapping is:

| Frontend route | Required staged state |
| --- | --- |
| `/portfolio-input` | `input`, `data_load` start the review and persist the active `review_id` |
| `/diagnosis` | running staged progress, then `xray` completed or partial after same-run recovery |
| `/evidence` | `stress` completed or partial |
| `/client-fit` | `client_fit` completed or `not_provided` compatibility state |
| `/hypothesis` | `problem_classification` and `launchpad_builder` completed or partial |
| `/comparison` | `candidate` and `comparison` completed with same-run lineage |
| `/verdict` | `verdict` completed with same-comparison lineage |
| `/report` | `report` completed, or a grounded evidence-insufficient preview when allowed |

The route labels may remain product-facing. Raw stage names are implementation vocabulary and should
not become primary UI copy.

## Stage status semantics

Each stage has one of these statuses:

| Status | Meaning |
| --- | --- |
| `pending` | The stage has not started. |
| `running` | The backend is actively working on the stage or waiting on its direct dependency. |
| `completed` | The stage has enough evidence for its product role. |
| `partial` | The stage can be shown with explicit limitations. |
| `blocked` | The stage cannot run until user input, data, or prior lineage is fixed. |
| `failed` | Runtime execution failed for this stage. Earlier completed stages remain valid. |
| `skipped` | The stage was intentionally skipped by the selected mode. |

Stage transitions must be monotonic for a single run. A later failed stage must not erase earlier
completed evidence. Recovery must prefer `review_state.json` and same-run lineage over disk scans.
The internal `ReviewCaseStageMachine` centralizes these row-level transition rules without changing
the public `review_state_v1` schema.

## Safe error model

The staged safe error codes are:

```text
DATA_PROVIDER_FAILED
INVALID_TICKER
PYTHON_STAGE_FAILED
TIMEOUT
ARTIFACT_MISSING
LINEAGE_MISMATCH
```

The public error shape is:

```json
{
  "code": "DATA_PROVIDER_FAILED",
  "message": "Market data was unavailable for one or more holdings.",
  "user_action": "retry",
  "retryable": true,
  "stage": "data_load"
}
```

The backend may log richer internal exceptions, but public staged errors must remain bounded and
safe for UI display.

## Worker admission and bounded queue

The live staged review endpoint returns before Python diagnosis finishes. Backend execution is
bounded by `PMRI_STAGED_REVIEW_MAX_WORKERS` active diagnosis workers and
`PMRI_STAGED_REVIEW_MAX_QUEUED` additional accepted reviews waiting for an active slot. A review
that is accepted into the bounded waiting queue remains `running` until a worker slot is available;
only requests beyond active plus queued capacity may return HTTP 429 with a retryable safe error.

The default execution queue remains in-process and behavior-preserving. The
`src/review_case/execution_queue.py` module provides the narrow internal adapter used by
`src/api/reviews.py`; without
additional configuration it starts the same daemon-thread background worker path as before. Operators
may explicitly prototype RQ plus Redis by setting `PMRI_REVIEW_CASE_QUEUE_BACKEND=rq` and
`PMRI_REVIEW_CASE_REDIS_URL` or `REDIS_URL`. RQ and Redis are optional imports, not required local or
production dependencies. If the opt-in Redis URL, RQ package, Redis package, or enqueue operation is
unavailable, the adapter falls back to the in-process path and preserves the existing public staged
start/status envelopes. This prototype does not add public `review_state_v1` fields, does not start
or manage RQ workers, and does not change formulas, data providers, generated artifacts, or raw-state
public sanitization. The adapter validates unsupported backend names, unsafe queue names, and
unsupported Redis URL schemes back to safe internal behavior. Queue job ids, queue names, fallback
reasons, and Redis-URL-present flags may appear in backend logs or internal enqueue metadata, but
raw Redis URLs and credentials must not be exposed in public envelopes.

## Demo / QA mode and live mode

The staged web path has two modes:

- `demo_qa`: deterministic fixture data, no external market-data dependency, predictable runtime,
  and fixed data-freshness disclosure.
- `live`: live data provider path, visible provider status, visible freshness disclosure, and longer
  possible runtime.

The public first-run/demo experience should use `demo_qa` when product reliability matters more than
fresh market data. Live mode must disclose provider status and must not hide data-provider failures
behind generic backend errors.

Staged `demo_qa` is selected from the existing create-review request option
`options.sample_mode: true`; the staged start response and status response report `mode: "demo_qa"`
and provider source `frozen_fixture`. The frozen path writes diagnosis-stage fixture artifacts first
and then uses deterministic fixture writers for explicit candidate, comparison, verdict, and report
actions. Live mode remains on the normal adapter path.

## Supabase compact-only boundary

Supabase remains optional compact persistence. As of the workspace/history plan, the frontend may write compact staged progress while polling, compact completed stage summaries after local stage success, and compact account workspace records. It may store:

- `review_id`;
- authenticated user workspace pointers;
- active portfolio and active portfolio-version links;
- immutable compact portfolio-version snapshots;
- overall review status;
- current stage;
- stage statuses;
- compact stage summaries;
- archive timestamps for portfolios and reviews;
- timestamps;
- compact in-flight progress recorded from Portfolio Input or Diagnosis polling;
- compact verdict/report summaries;
- saved portfolio links and compact portfolio input records.

Supabase must not store:

- raw `runs/` folders;
- raw `portfolio_xray.json`;
- raw `stress_report.json`;
- raw `client_fit_check.json`;
- price history;
- full generated artifact bundles;
- PDFs, CSVs, sidecars, or generated candidate folders;
- local absolute paths or internal artifact path maps.

Before each cloud write, the frontend must strip local paths, artifact references, raw generated
artifact filenames, raw artifact maps, and other generated-output references. If a compact stage
summary exceeds the configured soft limit, the cloud write should be skipped and the local staged
review should continue.

Login, `/workspace` hydration, and compact history recovery must not trigger backend execution. They load compact state only. Compact cloud state is read-only unless the current FastAPI backend confirms same-owner run-local lineage for the active `review_id`; compact summaries alone must not unlock Builder, Candidate, Comparison, Verdict, or Report mutation actions. A completed review is treated as immutable history for its portfolio version. If the user edits the portfolio, the UI creates a new draft/review snapshot and clears downstream readiness instead of reusing old candidate, comparison, verdict, or report evidence as current.

## Validation for this contract

Session 1 is documentation-only. Minimum validation after editing this contract is:

```text
git diff --check
.\.venv\Scripts\python.exe scripts\verify_docs.py
rg -n "POST /api/v1/reviews/staged|review_state_v1|demo_qa|compact stage" docs frontend README.md SPEC.md
```

Session 2 backend validation is:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_staged_review_api.py -q
.\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
```

Session 3 backend stage-runner validation is:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_staged_review_api.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
.\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
git diff --check
```

Session 4 backend Demo / QA validation is:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_staged_review_api.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
.\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
.\.venv\Scripts\python.exe scripts\verify_docs.py
git diff --check
```

Session 5 frontend polling validation is:

```text
cd frontend
npm.cmd run test:api
npm.cmd run test:smoke
npm.cmd run typecheck
```

Later implementation sessions must add focused Supabase and browser QA tests before claiming the
full staged pipeline is implemented.

Session 6 Supabase validation is:

```text
cd frontend
npm.cmd run test:api
npm.cmd run typecheck
git diff --check
```

Session 7 closure validation is:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_staged_review_api.py -q
cd frontend
npm.cmd run test:api
npm.cmd run typecheck
npm.cmd run test:smoke
npm.cmd run qa:vertical -- --scenario-limit 1
cd ..
.\.venv\Scripts\python.exe scripts\verify_docs.py
git diff --check
```
