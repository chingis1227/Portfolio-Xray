# FastAPI v1 API Contract

Status: **Session 10 accepted one-candidate MVP runtime contract with governance gates, frontend display adapters, and browser-QA handoff** for the local FastAPI backend.
`GET /api/v1/health`, `POST /api/v1/reviews`, `GET /api/v1/reviews/{review_id}`,
`POST /api/v1/reviews/{review_id}/builder`, and
`POST /api/v1/reviews/{review_id}/candidate`,
`POST /api/v1/reviews/{review_id}/comparison`,
`POST /api/v1/reviews/{review_id}/verdict`, and
`POST /api/v1/reviews/{review_id}/report` are implemented as live FastAPI endpoints.
Diagnosis interpretation Session 08 expands the diagnosis display envelope with typed
interpretation-chain fields. Diagnosis interpretation Session 09 carries the same evidence-chain
context into comparison, verdict, and report responses and regenerates frontend API types. Diagnosis
interpretation Session 10 updates the frontend compatibility/display adapters to consume those
public display fields before falling back to same-run artifact internals. Diagnosis interpretation
Session 13 extends governance so public claim schemas must retain source/provenance companions and
governed frontend/API copy cannot add unqualified advice-like language.

This contract preserves the current Portfolio MRI product truth: diagnosis-first,
current-portfolio-first, and candidate-as-diagnostic-test. FastAPI must expose typed envelopes over
existing deterministic artifacts; it must not promote generated folders, legacy optimizer outputs,
advanced scorecards, or PDFs into the normal site/API truth.

## Source-of-truth order

Use this document for the planned FastAPI HTTP API shape. Use the following documents for lower-level
meaning:

- `SPEC.md` for the current implementation contract and product scope.
- `OUTPUTS.md` for generated-vs-source boundaries and product-bundle artifact policy.
- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for product step order and forbidden behavior.
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` for screen ownership and stale-data rules.
- `docs/contracts/SCREEN_CONTRACTS.md` for user-facing route responsibilities.
- `docs/specs/block_4_diagnosis_v3_spec.md` for Problem Classification and Launchpad semantics.
- `docs/specs/portfolio_alternatives_builder_spec.md`, `docs/specs/candidate_setup_spec.md`, and
  `docs/specs/candidate_generation_spec.md` for Builder and one-candidate generation boundaries.
- `docs/specs/current_vs_candidate_spec.md`, `docs/specs/decision_verdict_spec.md`, and
  `docs/specs/ai_commentary_grounding_spec.md` for comparison, verdict, and grounded explanation.

If this API contract conflicts with a formula, metric, stress scenario, optimizer behavior, data
rule, or generated artifact schema, the owning detailed spec and code win. The API should adapt by
wrapping or mapping those canonical artifacts, not by inventing new calculations.

## Plain-language API purpose

The FastAPI backend should become the normal local API used by the frontend. It should give the
frontend a small set of typed responses that answer product questions:

1. What current portfolio was diagnosed?
2. What did Portfolio X-Ray find?
3. What did Stress Test Lab confirm or fail to confirm?
4. What is the main diagnosis and why?
5. What hypothesis can the user test next?
6. What one candidate was generated after explicit user action?
7. Did that candidate improve the diagnosed problem enough, and what got worse?
8. What non-binding Decision Verdict follows from the evidence?
9. What grounded explanation can be shown without hallucinating unsupported claims?

The API must not simply dump raw artifact trees. It should return response envelopes with lineage,
stage status, safe errors, evidence quality, and display-ready summaries backed by artifact
references.

## API version and namespace

All planned endpoints live under `/api/v1`. Session 03 registered the full typed MVP route surface
without switching the frontend from the existing Next.js-to-Python bridge. Session 04 implemented the
FastAPI runtime adapters for diagnosis review creation and safe review recovery. Session 05
implemented Builder setup and Candidate Generation adapters. Session 06 implemented
Current-vs-Candidate Comparison, Decision Verdict, and grounded Report context adapters.
Diagnosis interpretation Session 09 adds bounded downstream `evidence_chain_context` fields to
comparison, verdict, and report envelopes so each stage can display the diagnosis-to-hypothesis
chain without parsing raw artifacts. Diagnosis interpretation Session 10 makes the frontend
`reviewState` and report display adapters prefer these public envelope fields for compact screen
state while preserving same-run artifact fallbacks for details that are not yet public display
fields. Session 07
retired the old Next.js-to-Python script bridge from the normal frontend path: the existing
`/api/portfolio/*` route handlers are now thin compatibility proxies to FastAPI and no longer
spawn `scripts/run_review_from_payload.py`.

API versioning rule:

- additive response fields are allowed inside `data`, `warnings`, `evidence`, and `debug` sections;
- renamed or removed public fields require a new contract update and regenerated frontend types;
- raw internal artifact fields may change according to their owning specs, but public envelopes should
  remain stable where possible.

## Common envelope

Every successful response should use this shape:

    {
      "api_version": "v1",
      "schema_version": "<endpoint_schema_version>",
      "review_id": "frontend_review_... or api_review_...",
      "stage": "diagnosis|builder|candidate|comparison|verdict|report|health|recovery",
      "status": "ok|partial|blocked|failed",
      "lineage": {
        "review_id": "...",
        "selected_card_id": "... or null",
        "builder_setup_id": "... or null",
        "candidate_id": "... or null",
        "comparison_id": "... or null",
        "verdict_id": "... or null",
        "product_run_id": "... or null"
      },
      "data": {},
      "warnings": [],
      "safe_error": null,
      "evidence": {
        "source_artifacts": [],
        "data_quality": "ok|partial|blocked|unknown",
        "confidence": "high|medium|low|unknown"
      }
    }

Important rules:

- `status: ok` means the stage has enough evidence for its product role, not that investing action is
  recommended.
- `status: partial` means the stage can be shown with explicit limitations.
- `status: blocked` means the next stage should not unlock until the blocker is resolved.
- `status: failed` means runtime execution failed; the frontend should show a retry or recovery path.
- `safe_error` must never contain local absolute paths, Python tracebacks, environment variables,
  secrets, raw stack frames, or long generated artifact dumps.

## Safe error model

Errors should use this public shape:

    {
      "code": "invalid_portfolio_input|review_not_found|lineage_mismatch|stage_not_ready|backend_failed|artifact_missing|artifact_stale|data_quality_blocker|candidate_generation_blocked|comparison_unavailable|verdict_unavailable|report_unavailable|unknown_error",
      "message": "Plain-language explanation safe for the UI.",
      "user_action": "fix_input|retry|return_to_hypothesis|rerun_comparison|rerun_verdict|contact_operator|none",
      "retryable": true,
      "details": []
    }

The API may log richer internal exceptions server-side, but the public error should stay bounded and
client-safe.

## Endpoint list

### `GET /api/v1/health`

Purpose: prove the FastAPI server is alive and expose API/OpenAPI readiness.

Implementation status: implemented in Session 02 by `src/api/app.py` and typed with a Pydantic
response model in Session 03.

Response data:

    {
      "service": "portfolio-mri-api",
      "status": "ok",
      "api_version": "v1",
      "openapi_available": true
    }

This endpoint must not read portfolio artifacts or run diagnostics.

### `POST /api/v1/reviews`

Purpose: create a new portfolio-first diagnosis review from user portfolio input.

Implementation status: implemented in Session 04 by `src/api/reviews.py` and `src/api/app.py`.
The endpoint reuses the existing deterministic Python diagnosis runner in `diagnosis_plus_problem`
mode and returns a typed public envelope over run-local artifacts. It does not switch the visible
Next.js frontend route yet.

Request model:

    {
      "portfolio": {
        "investor_currency": "USD|EUR",
        "holdings": [
          {"type": "instrument", "ticker": "VOO", "weight_pct": 40.0},
          {"type": "cash", "currency": "USD", "weight_pct": 5.0}
        ]
      },
      "client_fit": {
        "preset_id": "balanced",
        "source": "questionnaire",
        "source_quality": "medium",
        "source_quality_reason": "Based on the short Client Fit questionnaire and user confirmation.",
        "horizon_years": 7,
        "target_return_range": {"min": 0.05, "max": 0.07},
        "target_vol_range": {"min": 0.07, "max": 0.10},
        "target_max_drawdown_pct": -0.20
      },
      "options": {
        "mode": "diagnosis_only",
        "output_profile": "site_api",
        "sample_mode": false
      }
    }

Response data should include:

- `review_summary`: review id, analysis window, investor currency, input weights, and data-quality
  status.
- `diagnosis`: compact display summary over `portfolio_xray.json`, Stress Lab evidence, and
  `problem_classification.json`. When `problem_classification_v3.interpretation_chain` is present,
  `diagnosis` also exposes typed display fields:
  - `selected_diagnosis_role`;
  - `source_artifacts`;
  - `diagnosis_evidence_items`;
  - `root_cause_narrative`;
  - `metric_to_diagnosis_trace`;
  - `rejected_alternatives`;
  - `professional_rationale_refs`;
  - `recommendation_boundary`.
  These fields are a bounded display model over the deterministic Block 4 interpretation chain, not
  raw artifact dumps and not a rebalance recommendation. Older or partial artifacts may still return
  the legacy compact fields (`primary_diagnosis`, `headline`, `confidence`, `evidence_chain`, and
  `next_diagnostic_step`) only.
- `launchpad`: compact `candidate_launchpad.json` card summaries.
- `client_fit`: bounded display summary over Client Fit status/profile/target rows when available.
- `next_allowed_actions`: normally `prepare_builder`, `recover_review`, or `resolve_data_quality`.
- `artifact_refs`: public references to allowed run-local artifacts, not absolute paths.

Boundary: this endpoint diagnoses the current portfolio and writes/reads run-local artifacts. It must
not auto-generate a candidate, compare alternatives, produce a verdict, refresh PDFs, or modify root
`config.yml`. The Session 07 request contract accepts both instrument holdings and real cash rows so
the FastAPI path preserves the existing Portfolio Input behavior.

Client Fit V1 request boundary: `client_fit` is optional for backend/CLI compatibility. When
provided, FastAPI validates the V1 profile fields (`preset_id`, source/source quality, horizon,
return range, volatility range, and target max drawdown), passes the full object into the run-local
input config, and maps compatible fields to legacy target keys for disclosure continuity. The
portfolio review runtime may generate `client_fit_check.json`; Block 4 may use Client Fit
dimension signals as supporting/contrary evidence and may select `goal_risk_conflict` as the
objective-review exception. This still does not approve suitability or issue trade instructions.

Client Fit response boundary: public envelopes expose a bounded `client_fit` display summary when
available. It contains display-ready fields such as status label/tone, profile label,
source-quality label, compact target rows, a decision boundary, and next-test language. Public
responses must not expose raw `client_fit_check.json`, raw `client_fit_context`, schema versions,
source-artifact maps, local paths, or backend field paths as primary UI data.

### `GET /api/v1/reviews/{review_id}`

Purpose: safely recover the active review state.

Implementation status: implemented in Session 04 by `src/api/reviews.py` and `src/api/app.py`.
The endpoint reads only the run-local `review_result.json` for a matching `frontend_review_*` id and
restores diagnosis, evidence, and hypothesis setup state. Candidate, comparison, verdict, and report
artifacts are not restored as active state during recovery.

Response data should include diagnosis, evidence, Launchpad, and Builder setup if those artifacts are
current. Candidate/comparison/verdict/report readiness should be restored only when same-review and
same-lineage evidence can be verified. If not verified, downstream readiness must be false with a
clear warning.

### `POST /api/v1/reviews/{review_id}/builder`

Purpose: prepare a Builder setup from one selected Launchpad card.

Implementation status: implemented in Session 05 by `src/api/reviews.py` and `src/api/app.py`.
The endpoint prepares one run-local Builder setup from the selected Launchpad card by reusing the
existing deterministic Builder handoff path. It writes and returns setup state only.

Request model:

    {
      "selected_card_id": "launchpad_...",
      "overrides": {
        "method_id": "equal_weight|risk_parity|hierarchical_risk_parity|minimum_variance|minimum_cvar|maximum_diversification",
        "mode": "capped|uncapped",
        "min_asset_weight": null,
        "max_asset_weight": null
      }
    }

Response data should include:

- `builder_setup`: selected diagnosis, selected card, method, mode, success criteria, trade-off to
  watch, skip rule, decision boundary, and generation readiness.
- `candidate_generation_allowed`: true only when setup is valid and the card is not monitor/data-only.
- `next_allowed_actions`: `generate_candidate` when allowed; otherwise `resolve_data_quality`,
  `select_another_card`, or `monitor`.

Boundary: Builder is setup-only. It must not create weights, candidate artifacts, comparison, verdict,
or report. In Session 07 the normal Next.js `/api/portfolio/*` path calls this FastAPI endpoint
through a compatibility proxy instead of launching the old script bridge.

### `POST /api/v1/reviews/{review_id}/candidate`

Purpose: explicitly generate one diagnostic candidate from the active Builder setup.

Implementation status: implemented in Session 05 by `src/api/reviews.py` and `src/api/app.py`.
The endpoint resolves the active run-local Builder setup by `builder_setup_id`, verifies same-review
and same-card lineage, and delegates to the existing one-candidate generation path.

Request model:

    {
      "builder_setup_id": "builder_setup_..."
    }

Response data should include:

- `candidate`: candidate id, method label, generation status, high-level weight summary when
  available, and infeasible/failed reason when not available.
- `hypothesis`: diagnosis-linked hypothesis, success criteria, trade-off, and decision boundary.
- `is_rebalance_recommendation`: always false for the candidate stage.
- `next_allowed_actions`: `run_comparison` only when candidate evidence is compare-ready.

Boundary: one candidate attempt only. This endpoint must not rank multiple candidates, run
comparison, issue a Decision Verdict, or treat the candidate as a rebalance recommendation. In
Session 07 the normal Next.js `/api/portfolio/*` path calls this FastAPI endpoint through a
compatibility proxy instead of launching the old script bridge.

### `POST /api/v1/reviews/{review_id}/comparison`

Purpose: compare the current portfolio with the same selected generated candidate.

Implementation status: implemented in Session 06 by `src/api/reviews.py` and `src/api/app.py`.
The endpoint verifies the request against the active run-local `candidate_generation.json`, reuses
the existing selected-candidate comparison helper, and returns a typed public envelope over
`candidate_comparison.json`, `current_vs_candidate.json`, and refreshed site explanation evidence.

Request model:

    {
      "candidate_id": "candidate_..."
    }

Response data should include:

- `comparison`: current label, candidate label, success-criteria result, what improved, what worsened,
  what stayed similar, unavailable metrics, turnover/cost practicality when available, and materiality
  for decision review.
- `client_fit`: bounded display summary for Client Fit target/status context when available.
- `evidence_chain_context`: bounded display context tying the comparison back to the selected
  diagnosis, tested hypothesis, success criteria, trade-off to watch, candidate boundary,
  recommendation boundary, and source artifact roles.
- `lineage`: must prove the comparison belongs to the same review, selected card, Builder setup, and
  candidate.
- `next_allowed_actions`: `generate_verdict` when comparison is current or when a safe
  evidence-insufficient verdict can be generated.

Boundary: comparison explains trade-offs; it must not crown a winner, recommend a trade, or unlock
report without Verdict.

### `POST /api/v1/reviews/{review_id}/verdict`

Purpose: translate current-vs-candidate evidence into non-binding decision support.

Implementation status: implemented in Session 06 by `src/api/reviews.py` and `src/api/app.py`.
The endpoint resolves the active same-candidate comparison, delegates to the existing
`decision_verdict.json` writer, and maps the non-binding Decision Verdict into the public FastAPI
envelope.

Request model:

    {
      "comparison_id": "comparison_..."
    }

Response data should include:

- `verdict`: one of keep current / no material rebalance / rebalance review / test another candidate /
  candidate failed or infeasible / evidence insufficient, expressed in user-facing wording.
- `rationale`: concise evidence used, improvements, worsening, confidence, limitations, and what would
  change the verdict. The public `verdict` summary includes bounded `evidence_used` and
  `what_would_change_verdict` lists when available.
- `client_fit`: bounded display summary that keeps Client Fit Status separate from Diagnostic
  Quality Status and Decision Action.
- `evidence_chain_context`: the same selected diagnosis, hypothesis, success criteria, candidate
  boundary, and recommendation-boundary context used by the comparison stage.
- `decision_support_only`: true.
- `next_allowed_actions`: `generate_report`, `test_another_hypothesis`, `rerun_comparison`, or
  `resolve_data_quality`.

Boundary: verdict is not trade execution, tax advice, suitability approval, or best-portfolio ranking.
No-trade and evidence-insufficient are valid successful outcomes.

### `POST /api/v1/reviews/{review_id}/report`

Purpose: return a grounded explanation preview from current diagnosis, hypothesis, candidate,
comparison, and verdict evidence.

Implementation status: implemented in Session 06 by `src/api/reviews.py` and `src/api/app.py`.
The endpoint verifies the active same-candidate verdict, delegates to the existing grounded
`ai_commentary_context.json` writer, and returns a compact deterministic report preview. It does
not call an LLM and does not refresh PDFs.

Request model:

    {
      "verdict_id": "verdict_..."
    }

Response data should include:

- `report_preview`: executive summary, current portfolio diagnosis, stress evidence, tested
  hypothesis, candidate boundary, comparison trade-offs, verdict explanation, evidence limitations,
  and optional monitoring note.
- `grounding`: compact source references and unavailable sections.
- `client_fit`: the same bounded Client Fit display summary where available.
- `evidence_chain_context`: bounded diagnosis-to-hypothesis-to-verdict context for primary report
  copy and provenance without exposing raw artifact trees.
- `llm_generated`: false until a later approved AI Commentary implementation exists.

Boundary: report is grounded preview/context. It must not invent conclusions, imply an LLM decided, or
present missing PDF export as a product failure.

## Public response envelopes versus internal artifacts

The following artifacts can be sources for public envelopes, but the API should not expose them as raw
primary payloads:

| Artifact | Public API use | Raw artifact status |
| --- | --- | --- |
| `run_metadata.json` / `analysis_setup` / `input_assumptions` | portfolio and assumptions summary | internal/source evidence |
| `portfolio_xray.json` | diagnosis/X-Ray display model using product Blocks 2.1-2.6 | internal artifact, not raw API response |
| `stress_report.json` | Stress Lab display model, scenario summaries, hedge gaps, stress scorecard | internal artifact, not raw API response |
| `problem_classification.json` | diagnosis, root cause, evidence, confidence, next step | public meaning through envelope |
| `candidate_launchpad.json` | hypothesis cards and test paths | public meaning through envelope |
| `portfolio_alternatives_builder.json` | selected setup and generation readiness | public meaning through envelope |
| `candidate_generation.json` | one candidate attempt status and summary | public meaning through envelope |
| `current_vs_candidate.json` | trade-off comparison summary | public meaning through envelope |
| `decision_verdict.json` | non-binding verdict summary | public meaning through envelope |
| `ai_commentary_context.json` | grounding references and report-preview inputs | public meaning through envelope |
| `what_changed_summary.json` | optional short monitoring note | deferred/optional public note only |
| `output_manifest.json` | path discovery and QA support | internal support; do not show raw paths |

These remain internal, advanced, legacy, generated support, or debug-only unless a later contract
promotes them:

- root `run_result.json`, root `portfolio_weights.yml`, root legacy `portfolio_xray.json`, and root
  legacy `stress_report.json` from policy runs;
- `candidate_factory_run.json`, `candidate_factory_manifest.json`, per-candidate folders, and batch
  candidate registry evidence except as hidden provenance or same-candidate support;
- `selection_decision.json`, `portfolio_health_score.json`, `robustness_scorecard.json`,
  `assumption_sensitivity.json`, `pareto_dominance.json`, `regret_analysis.json`,
  `tradeoff_explanation.json`, and `model_risk_diagnostics.json` unless explicitly mapped as advanced
  drill-down evidence;
- `action_plan.json`, `decision_journal.json`, and full monitoring artifacts;
- CSV/TXT/HTML/PNG/PDF/Markdown sidecars and `pdf files/` under the normal site/API path;
- cache directories, generated `runs/` folder internals, and local absolute file paths.

## Lineage and stale-data rules

FastAPI must enforce the same product chain the frontend currently guards:

    review -> selected Launchpad card -> Builder setup -> candidate -> comparison -> verdict -> report

Rules:

- A downstream request must fail safely with `lineage_mismatch` if it references a different review,
  card, setup, candidate, comparison, or product run.
- Recovery must not silently trust candidate/comparison/verdict/report artifacts from old runs.
- Missing artifacts should produce `artifact_missing` or `stage_not_ready`, not fabricated summaries.
- Stale artifacts should be ignored or exposed only as debug/provenance, never as active UI truth.
- The API must prefer run-local review artifacts for live frontend reviews and `analysis_subject/` for
  portfolio-first subject diagnostics.

## Diagnosis interpretation framework baseline

The API should expose diagnosis output as a structured explanation chain, not as an isolated score.
The public model should be:

    Metric signal -> evidence item -> problem hypothesis -> root-cause diagnosis -> suggested test
    -> candidate setup -> comparison success criteria -> verdict

For example:

- a high top-3 capital weight plus high top-1 risk contribution becomes evidence for concentration;
- concentration may support the root-cause diagnosis `high_concentration` or symptom
  `poor_diversification`;
- the suggested test may be Equal Weight, Risk Parity, or Maximum Diversification depending on the
  diagnosis and Builder allowlist;
- the candidate is only a diagnostic test;
- comparison checks whether concentration/risk contribution improved without unacceptable trade-offs;
- only Verdict decides whether no-trade, test-another, evidence-insufficient, or rebalance review is
  justified.

This chain must include evidence references, confidence, materiality, actionability, and negative
or contrary evidence where available. Scoring rows may exist as backend audit metadata, but the public
API should lead with the explanation chain.

Diagnosis interpretation Session 08 maps the additive Block 4 fields into the public
`DiagnosisSummary` model:

- `root_cause_narrative` prefers `root_cause_narrative.statement_en` and
  `portfolio_manager_interpretation_en` for display-ready diagnosis copy.
- `diagnosis_evidence_items` carries bounded source artifact, block, field-path, signal,
  interpretation, severity, confidence, and limitation fields.
- `metric_to_diagnosis_trace` links source metric/signal rows to the selected diagnosis.
- `rejected_alternatives` explains why plausible alternatives did not become the primary diagnosis.
- `professional_rationale_refs` names the deterministic specs/config/code sources that justify the
  diagnosis framework.
- `recommendation_boundary` keeps the non-binding Decision Verdict boundary visible.

Diagnosis interpretation Session 09 maps the downstream half of the same chain into
`ComparisonData`, `VerdictData`, and `ReportData` through `evidence_chain_context`. Verdict summaries
also expose bounded `evidence_used` and `what_would_change_verdict` lists. These are display models
over same-run candidate/comparison/verdict/report evidence, not new calculations and not trade
recommendations.

## Frontend type generation and screen-mapping governance

Session 03 introduced TypeScript generation from FastAPI OpenAPI into:

    frontend/lib/generated/api-types.ts

Generated types are a contract safety net, not automatic UI promotion. Session 09 keeps raw generated artifacts behind adapters: Core MVP screens consume compact display models from `reviewState` and FastAPI public envelopes, while raw same-run compatibility fields remain fallback/debug evidence only. Session 08 adds a
machine-readable governance map:

    docs/contracts/FASTAPI_SCREEN_MAPPING.json

New backend fields may appear in generated types, but a field becomes visible only after the
screen-mapping contract, `ARTIFACT_TO_SCREEN_MAP.md`, `SCREEN_CONTRACTS.md`, a frontend adapter, and
tests explicitly map it. The governance guard compares the live OpenAPI schema, the generated
TypeScript types, and the screen map so a public backend schema change cannot pass silently without:

- regenerating `frontend/lib/generated/api-types.ts`;
- listing every FastAPI operation in `FASTAPI_SCREEN_MAPPING.json`;
- listing every top-level public response `data` field for that operation;
- assigning non-health operations to the approved Core MVP screen routes.

Diagnosis interpretation Session 13 adds two anti-hallucination checks to the same guard:

- public diagnosis, comparison, verdict, and report claim schemas must keep source/provenance or
  boundary fields such as evidence-item source paths, rationale refs, grounding refs,
  `evidence_chain_context`, `llm_generated`, and `decision_support_only`;
- governed frontend/API copy is scanned for unqualified advice-like phrases such as best-portfolio,
  winner, must-rebalance, trade-now, guaranteed-improvement, or suitability-approved framing. Such
  phrases are allowed only when they are explicitly used as a negative boundary or guardrail.

Regenerate the file after intentional FastAPI contract changes with:

    .\.venv\Scripts\python.exe scripts\generate_fastapi_api_types.py

Focused verification:

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_contract_governance.py -q
    cd frontend
    npm.cmd run typecheck


## Session 10 validation and handoff

Session 10 acceptance is recorded in
`docs/audits/2026-06-11_fastapi_foundation_session10_acceptance.md`. The final browser QA used a
fresh FastAPI server on `127.0.0.1:8010`, a fresh Next.js server on `127.0.0.1:3010`, cleared browser
storage, and verified the normal frontend path from Portfolio Input through grounded Report preview.
The tested run produced an evidence-insufficient Decision Verdict after comparison metrics were
unavailable; this is a valid Core MVP outcome, not a frontend failure.

Frontend gating rule: a same-review, same-candidate comparison may unlock Verdict when it is current
and can safely produce an evidence-insufficient verdict, even if it has no displayable comparison
metrics. Comparison still must not recommend a trade or crown a winner; the Verdict stage owns the
non-binding evidence-insufficient outcome.

## Diagnosis interpretation Session 09 validation

Diagnosis interpretation Session 09 validation is:

    .\.venv\Scripts\python.exe scripts\generate_fastapi_api_types.py
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_fastapi_contract_governance.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Diagnosis interpretation Session 09 does not change portfolio calculations, generated review
artifact schemas, root `config.yml`, Next.js route handlers, frontend screen behavior, or PDF
refresh behavior. It changes typed FastAPI display envelopes for comparison, verdict, and report,
regenerates frontend API types, and updates the FastAPI screen-mapping governance contract.

## Session 08 validation

Session 08 validation is:

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_fastapi_contract_governance.py -q
    cd frontend
    npm.cmd run typecheck

Session 08 does not change portfolio calculations, generated review artifact schemas, root
`config.yml`, Next.js route handlers, frontend screens, or PDF refresh behavior. It adds a governance
gate that makes contract drift visible before later frontend adapter simplification.

## Session 07 validation

Session 07 validation is:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
    cd frontend
    npm.cmd run test:api
    npm.cmd run typecheck
    cd ..

Session 07 switches the normal Next.js portfolio API route handlers to FastAPI compatibility
proxies. It does not change portfolio calculations, generated review artifact schemas, dependency
versions, PDF refresh behavior, or root `config.yml`. `scripts/run_review_from_payload.py` remains
a legacy/debug helper and as an internal implementation helper reused by FastAPI, but it is no
longer launched by the normal frontend route handlers.
