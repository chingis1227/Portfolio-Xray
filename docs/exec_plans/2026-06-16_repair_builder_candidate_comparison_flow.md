# Repair the Builder to Report live review flow

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository includes `PLANS.md` at the repository root. Maintain this document in
accordance with `PLANS.md`: keep it self-contained, update it at each stopping point, and
make every milestone produce observable working behavior.

## Purpose / Big Picture

After this work, a user running the live Portfolio MRI frontend can open Hypothesis Builder,
choose simple Builder parameters, generate one fresh diagnostic candidate, compare the current
portfolio against that candidate, and continue to a grounded Verdict and Report. The flow must
not show "Comparison metrics unavailable" when candidate generation succeeded and same-run
candidate metrics are available.

The user-visible success path is:

    Portfolio Input
    -> Diagnosis
    -> Stress Lab
    -> Client Fit
    -> Hypothesis / Builder
    -> Candidate Generation
    -> Comparison
    -> Verdict
    -> Report

The final working behavior is visible in the browser: `/hypothesis` shows capped or uncapped
Builder controls and min/max weight fields, `/comparison` shows real current-vs-candidate metric
rows, `/verdict` shows an evidence-based decision-support verdict, and `/report` creates a
grounded preview from the same active review lineage.

## Progress

- [x] (2026-06-16 09:40Z) Created this ExecPlan and recorded the current root-cause findings and target acceptance.
- [x] (2026-06-16 09:50Z) Session 2 repaired backend candidate freshness and Comparison API evidence transport. FastAPI live candidate generation now forces the one-candidate factory rebuild, reused `skipped_existing` factory steps are marked not compare-ready, stale/unavailable comparison rows are rejected, and the public Comparison response now includes the same-run `current_vs_candidate` display artifact with `comparisons[].dimensions`.
- [x] (2026-06-16 10:02Z) Session 3 added frontend Builder controls and wired overrides/state cleanup. `/hypothesis` now exposes capped/uncapped mode, constraint preset, min/max asset weight fields, sends those values to FastAPI Builder prepare, clears candidate/comparison/verdict/report state when card or Builder settings change, and consumes full `current_vs_candidate.comparisons[].dimensions` when present.
- [x] (2026-06-16 10:25Z) Session 4 closed the plan. A fresh one-scenario browser vertical QA run reached `/report`, kept same-run lineage through Builder, Candidate, Comparison, Verdict, and Report, returned stale selected-card rejection HTTP 409, and documentation/project memory were synced.

## Surprises & Discoveries

- Observation: The canonical Builder specification already includes V1 simple fields `mode`, `constraint_preset`, `min_asset_weight`, and `max_asset_weight`, including `uncapped` mode.
  Evidence: `docs/specs/portfolio_alternatives_builder_spec.md` states that supported modes are `capped` and `uncapped`, and that the editable setup fields are `goal`, `method`, `mode`, `constraint_preset`, `max_asset_weight`, and `min_asset_weight`.

- Observation: The current Hypothesis page does not render those Builder controls. It displays selected method and candidate state, and the API bridge posts empty overrides.
  Evidence: `frontend/app/hypothesis/page.tsx` renders `Selected method` and `Candidate state`; `frontend/lib/server/fastapiBridge.ts` posts `overrides: {}` for Builder setup.

- Observation: A generated candidate can still be unusable for comparison when the factory reuses stale candidate artifacts.
  Evidence: Existing run-local artifacts showed `candidate_generation.json` with generated weights, while `candidate_comparison.json` marked the selected candidate unavailable with `stale_snapshot_analysis_end` and warnings including `factory_step_status:skipped_existing`.

- Observation: The FastAPI comparison response currently transports a compact `ComparisonSummary`, not the full `current_vs_candidate.comparisons[].dimensions` rows that the frontend uses to build visible metrics.
  Evidence: `src/api/models.py` defines `ComparisonData` with `comparison`, `evidence_chain_context`, `client_fit`, and `next_allowed_actions`, while `frontend/lib/reviewState.tsx` builds comparison UI metrics from `row.dimensions`.

- Observation: Session 2 focused backend tests pass after the API response schema update and generated TypeScript contract refresh.
  Evidence: `.\.venv\Scripts\python.exe -m pytest tests\test_staged_review_api.py tests\test_block8_current_vs_candidate_boundary.py tests\test_current_vs_candidate.py tests\test_decision_verdict.py tests\test_frontend_review_bridge.py::test_generate_selected_candidate_reused_factory_step_cannot_compare tests\test_frontend_review_bridge.py::test_compare_selected_candidate_rejects_stale_unavailable_comparison_row tests\test_fastapi_app.py::test_generate_candidate_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_run_comparison_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generated_frontend_api_types_match_openapi_schema -q` reported `25 passed`.

- Observation: Session 3 needed a small FastAPI contract addition before the frontend could send the canonical Builder preset.
  Evidence: `BuilderOverrides` already accepted method, mode, min asset weight, and max asset weight, but not `constraint_preset`; sending the UI field to the strict model would have rejected the Builder request. Session 3 added the public `constraint_preset` override and included Builder setup constraint fields in the public setup summary.

- Observation: Session 3 frontend checks pass after a warm retry of the smoke test.
  Evidence: `npm.cmd run typecheck` passed, `npm.cmd run test:api` reported 35 passed, `npm.cmd run test:smoke` first timed out while compiling `/` on a fresh Next dev server and then passed on retry, and `.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py::test_generated_frontend_api_types_match_openapi_schema tests\test_fastapi_app.py::test_prepare_builder_runs_adapter_and_returns_public_envelope -q` reported 2 passed.

- Observation: The broader `tests/test_frontend_review_bridge.py tests/test_fastapi_app.py` run still has one unrelated failure in `test_direct_staged_diagnosis_service_calls_materializer_without_subprocess`.
  Evidence: the failing assertion expects `use_review_run_context is False`, while the current direct staged diagnosis service passed `True`; Session 2 did not edit that service.

- Observation: `scripts/verify_fastapi_contract_governance.py` is currently blocked by existing frontend evidence-copy checks outside the Session 2 backend scope.
  Evidence: it reports advice-like phrases in `frontend\components\evidence\stressStoryModel.ts:43` (`best portfolio`, `must rebalance`, `trade now`, and `suitability approved`).

- Observation: Session 4 vertical QA passed on a clean local target with a fresh Playwright browser context.
  Evidence: `cd frontend && npm.cmd run qa:vertical -- --scenario-limit 1` reported `status: passed`, frontend URL `http://127.0.0.1:49564`, FastAPI URL `http://127.0.0.1:49563`, active review `frontend_review_20260616T101556Z_-Hy3DmwRHSAOZ8USTmRiEQ`, selected card `launchpad_demo_reduce_concentration`, candidate `equal_weight`, comparison `current_vs_candidate:equal_weight`, verdict `evidence_insufficient`, report evidence-chain context `true`, and stale selected-card probe status `409`.

- Observation: The vertical QA report contains generated diagnostic log snippets with mojibake for local path and console symbols.
  Evidence: `output/playwright/vertical-qa-2026-06-16T10-15-38-227Z/qa-report.json` is generated output, not source, and was not edited as part of this plan.

## Decision Log

- Decision: Treat `mix weight` as out of scope for this repair.
  Rationale: The current canonical Builder V1 contract requires `mode`, `constraint_preset`, `min_asset_weight`, and `max_asset_weight`; no current source-of-truth document makes `mix weight` mandatory.
  Date/Author: 2026-06-16 / Codex.

- Decision: Prefer correctness and same-run lineage over candidate factory reuse in the live frontend path.
  Rationale: A stale or reused candidate with weights but no fresh metrics creates a broken user journey and leads to evidence-insufficient Verdict and Report states.
  Date/Author: 2026-06-16 / Codex.

- Decision: Repair the full chain rather than masking the UI empty state.
  Rationale: Rendering fallback copy on `/comparison` would not fix the missing evidence needed by Verdict and Report.
  Date/Author: 2026-06-16 / Codex.

- Decision: In the live FastAPI candidate path, force one-candidate factory rebuilds instead of allowing resume reuse.
  Rationale: The frontend success path needs same-run candidate metrics; a reused `skipped_existing` snapshot can have weights but fail freshness checks later in comparison.
  Date/Author: 2026-06-16 / Codex.

- Decision: Keep the compact `ComparisonSummary` but add `current_vs_candidate` as a display-safe public field on `ComparisonData`.
  Rationale: This preserves existing consumers while giving the frontend access to canonical `comparisons[].dimensions`, practicality, materiality, success criteria, and warnings without inventing metric rows.
  Date/Author: 2026-06-16 / Codex.

- Decision: Add `constraint_preset` to the FastAPI Builder override contract during Session 3.
  Rationale: The canonical Builder V1 UI must expose and send the preset; without a public model field, the strict FastAPI request model would reject the frontend request before it reached the existing backend adapter that already supports the preset.
  Date/Author: 2026-06-16 / Codex.

## Outcomes & Retrospective

Session 1 created the executable plan and locked the target behavior. Session 2 completed the backend/API portion: candidate generation no longer advertises comparison readiness after factory reuse, comparison generation rejects stale or unavailable selected rows, and the public FastAPI Comparison response carries enough same-run evidence for frontend metric rows. Session 3 completed the frontend implementation: `/hypothesis` now has Builder setup controls, sends overrides to the Builder endpoint, clears stale downstream readiness after card/settings changes, and preserves full comparison dimensions for metric rows. Session 4 completed final acceptance: one-scenario browser vertical QA reached `/report` from a fresh local target with same-run Builder, Candidate, Comparison, Verdict, and Report lineage, stale selected-card rejection remained protected, `frontend/README.md` and project memory were updated, and this plan is closed.

## Context and Orientation

Portfolio MRI is a diagnosis-first, current-portfolio-first investment decision-support system. The current live frontend route chain is:

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

The relevant product artifacts are:

- `portfolio_alternatives_builder.json`: setup-only Builder artifact. It must not contain weights or verdicts.
- `candidate_generation.json`: one explicit generated diagnostic candidate or a failed/infeasible attempt.
- `current_vs_candidate.json`: current portfolio versus the active generated candidate.
- `decision_verdict.json`: non-binding decision-support verdict.
- `ai_commentary_context.json`: grounded report context.

The key source-of-truth documents are:

- `docs/specs/portfolio_alternatives_builder_spec.md`
- `docs/specs/current_vs_candidate_spec.md`
- `docs/specs/decision_verdict_spec.md`
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`
- `frontend/README.md`

The key implementation files are:

- `src/api/models.py`, which defines the public FastAPI response models.
- `src/api/reviews.py`, which implements staged Builder, Candidate, Comparison, Verdict, and Report API behavior.
- `scripts/run_review_from_payload.py`, which bridges run-local frontend reviews to candidate generation and comparison writers.
- `frontend/lib/server/fastapiBridge.ts`, which translates Next.js API calls to FastAPI.
- `frontend/lib/reviewState.tsx`, which stores compact active review state and maps API responses into display summaries.
- `frontend/app/hypothesis/page.tsx`, `frontend/app/comparison/page.tsx`, `frontend/app/verdict/page.tsx`, and `frontend/app/report/page.tsx`, which render the user journey.

Definitions used in this plan:

- "Same-run lineage" means that `reviewId`, selected Launchpad card, Builder setup, candidate id, comparison id, verdict id, and report context all belong to the same run-local review folder.
- "Fresh candidate metrics" means that the selected candidate's snapshot and stress artifacts match the active review's analysis date and config fingerprint closely enough for `candidate_comparison.json` to mark the candidate row available.
- "Displayable metric" means a comparison dimension where both current and candidate values are available and the direction is not unclear.

## Plan of Work

Session 2 repairs backend and API evidence transport. Update the live candidate generation path so it either forces a fresh candidate build for the selected review or refuses `can_compare=true` when candidate artifacts are reused without matching freshness. Then expand the comparison API response so the Next.js bridge receives the full `current_vs_candidate` artifact or a display-safe equivalent that includes `comparisons[].dimensions`, practicality, success criteria, materiality, warnings, and selected candidate ids. The comparison endpoint must not mark the stage successful for UI purposes if the selected candidate row is stale or unavailable.

Session 3 repairs the frontend. Add Simple Builder controls to `/hypothesis` for `mode`, `constraint_preset`, `min_asset_weight`, and `max_asset_weight`. Send those values as Builder overrides. Store the chosen setup in active review state. When the user changes selected card or Builder settings, clear candidate, comparison, verdict, and report readiness so old downstream artifacts cannot remain active. Update comparison mapping so metric rows are built from full dimensions returned by the API.

Session 4 verifies the full vertical flow and syncs docs. Start from a clean local dev server, use a new `reviewId`, generate a candidate, compare it, generate verdict, and create report preview. Record the active `reviewId`, selected card id, candidate id, comparison id, verdict id, route chain, and any screenshots captured. Update `frontend/README.md`, `CHANGELOG.md`, and `KNOWN_ISSUES.md` as needed.

## Concrete Steps

Run all commands from the repository root.

Before implementation sessions, read this ExecPlan and the source-of-truth documents listed above. Check current dirty files:

    git status --short

Backend implementation session should edit the backend/API files, then run:

    .\.venv\Scripts\python.exe -m pytest tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_block8_current_vs_candidate_boundary.py tests\test_current_vs_candidate.py tests\test_decision_verdict.py -q

Frontend implementation session should edit the frontend files, then run from `frontend`:

    npm run typecheck
    npm run test:api
    npm run test:smoke

Session 3 ran these checks on 2026-06-16. `npm.cmd run typecheck` passed. `npm.cmd run test:api` passed with 35 tests. `npm.cmd run test:smoke` first timed out while the fresh Next dev server was compiling `/`, then passed on retry. Session 3 also ran `.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py::test_generated_frontend_api_types_match_openapi_schema tests\test_fastapi_app.py::test_prepare_builder_runs_adapter_and_returns_public_envelope -q`, which passed with 2 tests.

Vertical QA session should start from a clean local target. If stale `.next` chunk errors appear, stop and restart the dev server before drawing UI conclusions.

Session 4 ran:

    cd frontend
    npm.cmd run qa:vertical -- --scenario-limit 1

It passed and wrote evidence to:

    output/playwright/vertical-qa-2026-06-16T10-15-38-227Z/qa-report.json

## Validation and Acceptance

Acceptance for Session 2:

- A candidate generated from the live frontend path does not advertise `can_compare=true` if its comparison row would be stale or unavailable.
- A successful comparison API response contains displayable comparison evidence, including `current_vs_candidate.comparisons[0].dimensions`.
- A backend regression test proves that stale candidate snapshots do not unlock comparison.
- A backend regression test proves that comparison API response data includes enough fields for the frontend to build metrics.

Acceptance for Session 3:

- `/hypothesis` visibly offers capped/uncapped mode, constraint preset, min asset weight, and max asset weight controls.
- The Builder prepare request sends those values as overrides.
- Switching to uncapped maps guided methods to uncapped backend variants where the Builder contract defines such variants.
- Changing Builder settings clears downstream candidate, comparison, verdict, and report state.
- `/comparison` shows metric rows when the API provides dimensions.

Acceptance for Session 4:

- A new live review reaches `/report` through the route chain without relying on old `runs/` artifacts. Session 4 evidence: active review `frontend_review_20260616T101556Z_-Hy3DmwRHSAOZ8USTmRiEQ` reached route checks through `client-profile`, `diagnosis`, `evidence`, `client-fit`, `hypothesis`, `comparison`, `verdict`, and `report`.
- `/comparison` does not show "Comparison metrics unavailable" after a fresh compare-ready candidate. Session 4 evidence: the comparison API succeeded for candidate `equal_weight`, the report records comparison source artifacts `candidate_generation`, `candidate_comparison`, `current_vs_candidate`, and `site_explanation_bundle`, and no failures or warnings were recorded.
- `/verdict` shows evidence-based decision-support output instead of only a forced empty state. Session 4 evidence: verdict id `evidence_insufficient` was produced from same-run candidate and comparison sources, which is an accepted decision-support outcome when evidence is insufficient.
- `/report` creates a grounded preview that references diagnosis, candidate, comparison, verdict, and limitations. Session 4 evidence: report sources include `candidate_generation`, `current_vs_candidate`, `decision_verdict`, `ai_commentary_context`, and `site_explanation_bundle`, with `report_has_evidence_chain_context: true`.
- The QA report names the URL/port, route chain, active `reviewId`, selected card id, candidate id, comparison id, verdict id, screenshots captured if any, and unverified areas. Session 4 evidence: `qa-report.json` records frontend URL `http://127.0.0.1:49564`, FastAPI URL `http://127.0.0.1:49563`, browser state reset, route checks, lineage ids, warnings `[]`, failures `[]`, and stale selected-card probe status `409`.

## Idempotence and Recovery

All implementation steps should be safe to repeat. Generated artifacts under `runs/`, root candidate folders, and `.next` are not source-of-truth for code changes. Do not manually trust old generated outputs during QA. If a dev server reports missing `.next` chunks or React manifest errors, restart the server and rerun the active flow from a fresh local target before evaluating UI behavior.

Do not use destructive git commands. Do not revert unrelated dirty files. Keep generated output changes out of commits unless a session explicitly targets generated artifacts.

## Artifacts and Notes

The current broken behavior has three known symptoms:

    1. Hypothesis Builder shows candidate generation controls but not the V1 Builder parameters.
    2. Candidate weights can appear while Comparison reports missing metrics.
    3. Verdict and Report degrade because active comparison evidence is missing or stale.

The known root causes are:

    1. Builder controls are present in backend/spec but missing from the current Hypothesis UI.
    2. Candidate generation can reuse stale candidate artifacts through skipped_existing behavior.
    3. The public comparison API response omits full current_vs_candidate dimensions.

## Interfaces and Dependencies

Backend API must preserve the staged endpoint names:

    POST /api/v1/reviews/{review_id}/builder
    POST /api/v1/reviews/{review_id}/candidate
    POST /api/v1/reviews/{review_id}/comparison
    POST /api/v1/reviews/{review_id}/verdict
    POST /api/v1/reviews/{review_id}/report

The Builder request keeps `selected_card_id` and `overrides`. The overrides used by this plan are:

    method_id: guided method id or null
    mode: "capped" or "uncapped"
    constraint_preset: "conservative", "balanced", "aggressive", "basic_reference", "custom", "uncapped", or null
    min_asset_weight: decimal 0..1 or null
    max_asset_weight: decimal 0..1 or null

Session 3 added `constraint_preset` deliberately to the public FastAPI Builder overrides and Next.js request shape. Do not add `mix weight` in this repair.

The Comparison response must provide either the canonical `current_vs_candidate` artifact or a display-safe field with equivalent `comparisons[].dimensions`. The frontend must consume that evidence without inventing metric values.

## Revision Notes

- 2026-06-16 / Codex: Updated after Session 2 implementation to record backend freshness guards, public Comparison evidence transport, tests run, and remaining Session 3 and Session 4 work.

- 2026-06-16 / Codex: Updated after Session 3 implementation to record frontend Builder controls, override transport, downstream state cleanup, full comparison-dimensions consumption, focused verification, and the remaining Session 4 vertical QA/documentation work.

- 2026-06-16 / Codex: Closed after Session 4 vertical QA and documentation sync. The final QA report proves a fresh local frontend/FastAPI route chain through Report with same-run selected card, candidate, comparison, verdict, report evidence, and stale-card 409 protection.
