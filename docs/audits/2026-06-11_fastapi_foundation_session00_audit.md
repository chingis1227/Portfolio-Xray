# FastAPI Foundation Session 00 Audit

Date: 2026-06-11

Status: read-only implementation audit for the FastAPI foundation plan. This audit did not change
runtime behavior, Python calculations, frontend behavior, dependencies, root `config.yml`, or
generated outputs.

## Current Bridge

The current frontend backend bridge is:

    Next.js screen
    -> Next.js API route under frontend/app/api/portfolio/
    -> Python bridge script scripts/run_review_from_payload.py
    -> run-local generated artifacts under runs/frontend_review_*/
    -> compact frontend review state and screen adapters

The visible frontend route chain is:

    /portfolio-input
    -> /diagnosis
    -> /evidence
    -> /hypothesis
    -> /comparison
    -> /verdict
    -> /report

The current API route tree contains:

    /api/portfolio/diagnose
    /api/portfolio/review/recover
    /api/portfolio/builder/prepare
    /api/portfolio/candidate/generate
    /api/portfolio/comparison/generate
    /api/portfolio/verdict/generate
    /api/portfolio/report/generate

These routes are useful and already enforce local lineage, but they are not a formal Python HTTP API
contract. The Python boundary is still a script invocation boundary.

## Artifact-to-Screen Map

The existing contract docs already define the primary artifact routing:

- Portfolio Input uses user input, `review_result.json`, and resolved input assumptions.
- Diagnosis uses `analysis_subject/portfolio_xray.json` and Problem Classification summary.
- Evidence uses `analysis_subject/stress_report.json`.
- Hypothesis uses `problem_classification.json`, `candidate_launchpad.json`,
  `portfolio_alternatives_builder.json`, and same-run `candidate_generation.json` only after user
  action.
- Comparison uses same-run `current_vs_candidate.json` and same-run `candidate_generation.json`.
- Verdict uses same-run `decision_verdict.json`, same-run comparison, and same-run candidate.
- Report uses grounded `ai_commentary_context.json` plus same-run verdict/comparison evidence.

The FastAPI migration should reuse this artifact ownership rather than inventing a new product flow.

## Existing Rules and Source of Truth

Relevant current rules already exist:

- `SPEC.md` defines the diagnosis-first Core MVP product flow.
- `OUTPUTS.md` defines generated output and product-bundle boundaries.
- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` defines step order and forbidden product behavior.
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` defines artifact-to-screen ownership and stale-data
  rules.
- `docs/contracts/SCREEN_CONTRACTS.md` defines each frontend screen responsibility.
- `docs/contracts/QA_CONTRACT.md` defines verification expectations.
- `../../frontend/README.md` documents the current bridge and run-local review strategy.

The FastAPI plan should update these documents only when implementation behavior changes.

## Duplicated Logic

The current implementation duplicates or repeats some boundary logic:

- Portfolio input validation exists in the frontend API route and in the Python bridge.
- Review id/path traversal validation appears in multiple frontend API routes.
- Failure scrubbing and result-path parsing are repeated across Next.js route handlers.
- Presentation mapping is concentrated in `frontend/lib/reviewState.tsx`, while some screen-specific
  mapping also lives in route pages and components.
- TypeScript types in `frontend/lib/types.ts` are manually maintained and are not generated from a
  backend OpenAPI contract.

The FastAPI migration should move canonical request/response validation to Pydantic models and
generate frontend types from OpenAPI. Frontend routes can keep user-friendly pre-validation, but it
should not be the canonical contract.

## Stale-Data Risks

The current project already has strong stale-data rules, but the migration must preserve them:

- Only active `runs/frontend_review_*` folders are authoritative for live frontend reviews.
- Root legacy artifacts such as `run_result.json`, `portfolio_weights.yml`, and root
  `stress_report.json` must not override `analysis_subject/`.
- Candidate, comparison, verdict, and report stages must belong to the same `review_id`, selected
  Launchpad card, and generated candidate.
- Generated PDFs, CSV/TXT/HTML/PNG sidecars, cache, and candidate portfolio folders are not active
  UI truth under the normal site/API path.

The FastAPI API must encode these rules as response validation and safe error states, not leave them
as frontend-only assumptions.

## API Candidates

The planned FastAPI v1 surface should replace the current bridge in this order:

1. `GET /api/v1/health` for server readiness and OpenAPI sanity.
2. `POST /api/v1/reviews` for portfolio diagnosis and review creation.
3. `GET /api/v1/reviews/{review_id}` for safe recovery.
4. `POST /api/v1/reviews/{review_id}/builder` for selected-card Builder setup.
5. `POST /api/v1/reviews/{review_id}/candidate` for one diagnostic candidate attempt.
6. `POST /api/v1/reviews/{review_id}/comparison` for same-candidate trade-off evidence.
7. `POST /api/v1/reviews/{review_id}/verdict` for non-binding Decision Verdict.
8. `POST /api/v1/reviews/{review_id}/report` for grounded report context.

These endpoints should return typed envelopes, not raw arbitrary artifact dumps.

## Frontend Adapter Risks

`frontend/lib/reviewState.tsx` is currently the central store for active review state, compact
summaries, storage cleanup, journey flags, and presentation mapping. This is useful for safety, but
it is too broad for long-term frontend maintainability.

The later adapter cleanup session should keep active review state and lineage in one shared layer,
but move screen-specific display shaping into dedicated screen adapters. Screens should consume
display-ready models and generated API types, not raw backend artifact internals.

## Session 00 Conclusion

The project is ready to start a phased FastAPI migration, but not by replacing everything at once.
The correct next step is Session 01: write the precise FastAPI v1 API contract and decide response
envelopes before adding the FastAPI app skeleton.
