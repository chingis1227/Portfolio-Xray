# Staged Review State Contract

Status: **implemented staged-review contract for the Portfolio MRI web migration**.

This document is the source of truth for the implemented web execution contract where a user clicks
`Run diagnosis`, receives a `review_id` immediately, sees stage progress, and then receives partial
results as backend stages complete. Sessions 2-7 implement the additive backend start/status
endpoints, run-local `review_state.json`, diagnosis-stage synchronization, deterministic Demo / QA
execution, frontend polling, optional compact Supabase persistence, refresh recovery, and explicit
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
-> frontend shows progress
-> backend runs stages
-> frontend polls compact stage state
-> frontend unlocks partial results when each stage is ready
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
`src/api/reviews.py`:

```text
POST /api/v1/reviews/staged
GET /api/v1/reviews/{review_id}/status
```

`POST /api/v1/reviews/staged` starts a web review and returns without waiting for the full Python
diagnosis. It creates the run folder, writes the initial payload and `review_state.json`, starts
background execution, and returns a compact response:

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
recovery. It must not scan random run folders or expose raw generated artifact dumps.

The existing `POST /api/v1/reviews` synchronous diagnosis endpoint remains a compatibility path until
the staged path is fully adopted and tested.

Live mode still uses the existing diagnosis adapter in the background, but the staged
wrapper now synchronizes each diagnosis-stage row after execution. Required artifacts mark `input`,
`data_load`, `xray`, `stress`, `problem_classification`, and `launchpad_builder` completed when
present. Missing Client Fit context is non-blocking and records `client_fit` as `partial` so the UI
can use the `not_provided` compatibility state. Missing required artifacts produce a safe
`ARTIFACT_MISSING` error at the first affected stage while preserving earlier completed stages.
Runtime failures produce safe staged errors without tracebacks or absolute paths. `candidate`,
`comparison`, `verdict`, and `report` start as pending after diagnosis and are updated when the user explicitly runs those downstream actions. A later downstream blocker or failure must preserve earlier completed diagnosis evidence and leave the overall review recoverable as partial rather than erasing the run.

`demo_qa` execution routes through frozen fixture materializers instead of live market-data-backed adapters. The fixture materializer writes the same run-local artifact roles needed by the
diagnosis stages under `analysis_subject/` (`run_metadata.json`, `portfolio_xray.json`,
`stress_report.json`, `client_fit_check.json`, `problem_classification.json`,
`candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `output_manifest.json`, and
`site_explanation_bundle.json`). This is for demo and QA reliability only; it does not replace live mode, CLI portfolio review behavior, formulas, or generated artifact schemas. Session 7 extends this deterministic fixture path through explicit candidate, comparison, verdict, and report actions so browser vertical QA can prove the whole route chain without external market-data providers.

## Canonical review state

The run-local authoritative file for staged web execution is `review_state.json` at the root of the
active `runs/frontend_review_*` folder. It uses this target shape:

```json
{
  "schema_version": "review_state_v1",
  "review_id": "frontend_review_...",
  "status": "running",
  "current_stage": "xray",
  "mode": "demo_qa",
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
| `/portfolio-input` | `input`, `data_load` start the review |
| `/diagnosis` | `xray` completed or partial |
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

Supabase remains optional compact persistence. As of Session 6, the frontend may write compact
staged progress while polling and compact completed stage summaries after local stage success. It
may store:

- `review_id`;
- overall review status;
- current stage;
- stage statuses;
- compact stage summaries;
- timestamps;
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
