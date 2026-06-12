# Client Fit V1 Foundation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is self-contained for implementing
Client Fit V1 in Portfolio MRI.

## Purpose / Big Picture

Portfolio MRI currently diagnoses a current portfolio, but it does not yet answer the personal
question, "Does this risk fit the client's stated goals?" Client Fit V1 adds that layer without
turning the product into an optimizer or an advice engine. After implementation, a web user
completes a short investment-profile questionnaire before diagnosis, Portfolio MRI writes a
`client_fit_check.json` artifact after Stress Lab, and downstream diagnosis, hypothesis, comparison,
and verdict screens can explain portfolio evidence against the client's return, volatility,
drawdown, and horizon targets.

The product must keep three questions separate: what the user owns, what the portfolio looks like,
and whether that evidence fits the provided client profile. A Client Fit pass is not enough to say
"everything is fine"; no-trade or keep-current requires both acceptable Client Fit and no material
unresolved diagnostic issue.

## Progress

- [x] (2026-06-12) Session 00 created branch `codex/client-fit-v1` and recorded the baseline audit
  at `docs/audits/2026-06-12_client_fit_v1_session00_baseline_audit.md`. No runtime behavior,
  generated artifacts, FastAPI routes, frontend routes, Supabase schema, or product logic changed.
- [x] (2026-06-12) Session 01 created Client Fit methodology/spec documents, linked them from the
  spec index and `SPEC.md`, and added glossary terms. This is documentation-only; no runtime
  behavior, generated artifacts, FastAPI routes, frontend routes, Supabase schema, or product logic
  changed.
- [x] (2026-06-12) Session 02 added `config/client_fit_questionnaire.yml`, Client Fit preset
  metadata on `config/client_profiles.yml`, read-only helpers in `src/client_fit.py`, and focused
  tests in `tests/test_client_fit_profiles.py` / `tests/test_client_fit_questionnaire.py`.
  Verification passed: focused tests, docs verification, and diff check. No portfolio analytics,
  generated artifacts, FastAPI routes, frontend routes, Supabase schema, or diagnosis behavior
  changed.
- [x] (2026-06-12) Session 03 extended the input/FastAPI request contract with optional
  `client_fit` context. `CreateReviewRequest` now accepts a strict Client Fit V1 object, the
  frontend-review bridge validates and preserves it in run-local `input.yml`, compatible legacy
  target fields are mirrored for disclosure continuity, generated FastAPI TypeScript types were
  refreshed, and focused tests were added. No `client_fit_check.json` artifact, diagnosis rule,
  candidate behavior, frontend route, Supabase schema, or suitability/advice copy changed.
- [x] (2026-06-12) Session 04 added the `client_fit_check_v1` artifact builder and runtime writer.
  `run_report.py` now writes `client_fit_check.json` after Stress Lab / X-Ray and before Block 4,
  including backend-compatible `not_provided` status when no Client Fit profile is supplied.
- [x] (2026-06-12) Session 05 integrated Client Fit context into Block 4 evidence extraction.
  `client_fit_status`, `goal_risk_conflict`, and per-dimension `client_fit_<dimension>` signals
  are available as backend evidence context and `problem_classification_v3.source_artifacts`
  records `client_fit_check.json` when present. The rulebook and diagnosis selection are not yet
  changed; that remains Session 06.
- [x] (2026-06-12) Session 06 updated the Block 4 diagnosis rulebook/runtime parity with Client
  Fit evidence. Dimension-level Client Fit signals now support or contradict existing diagnoses,
  `client_fit_within_profile` is contrary context, and `goal_risk_conflict` is the only Client
  Fit primary exception. Enforcement proof:
  `tests/test_client_fit_check.py::test_client_fit_breach_supports_existing_diagnosis_without_universal_primary`,
  `test_client_fit_fit_is_contrary_context_not_structural_suppression`,
  `test_client_fit_breach_alone_does_not_replace_portfolio_diagnosis`, and
  `test_goal_risk_conflict_is_the_only_client_fit_primary_exception`.
- [x] (2026-06-12) Session 07 added Client Fit context to the Problem Classification
  interpretation chain. `problem_classification_v3` now exposes `client_fit_status`,
  `diagnostic_quality_status`, and `client_fit_context`, and the interpretation chain mirrors the
  same separation. Enforcement proof:
  `tests/test_client_fit_check.py::test_client_fit_breach_alone_does_not_replace_portfolio_diagnosis`
  proves breach plus clean diagnostics can keep the objective diagnosis acceptable, and
  `test_client_fit_status_and_diagnostic_quality_status_remain_separate_with_material_issue`
  proves fit plus a material concentration issue still selects the structural diagnosis.
- [x] (2026-06-12) Session 08 updated site explanation/report copy hierarchy for Client Fit.
  `site_explanation_bundle_v1` now accepts `client_fit_check.json`, emits a separate
  `client_fit` screen hierarchy plus report evidence row, and blocks `suitable` / `approved` copy
  alongside buy/sell, best-portfolio, and must-rebalance language. Enforcement proof:
  `tests/test_site_explanation_guardrails.py::test_site_explanation_client_fit_report_hierarchy_separates_fit_from_diagnosis`
  proves Client Fit status and diagnostic quality appear as separate sourced rows with no forbidden
  language.
- [x] (2026-06-12) Session 09 updated Candidate Launchpad integration. Launchpad now carries compact
  `client_fit_context` / `client_fit_relevance_en` when Client Fit evidence exists, while keeping
  cards as diagnostic tests. Enforcement proof:
  `tests/test_block_4_launchpad_cards.py::test_client_fit_pass_with_material_issue_still_routes_to_review_test_path`
  proves `client_fit_status = fit` plus a material `high_concentration` diagnosis still produces a
  targeted review/test card rather than automatic no-action.
- [x] (2026-06-12) Session 09A completed the post-Launchpad stabilization checkpoint.
  Source-of-truth wording now consistently classifies Client Fit V1 as a partially implemented
  backend interpretation overlay with full web journey pending; `AGENTS.md`, `SPEC.md`, `OUTPUTS.md`,
  product/screen/artifact/FastAPI/runtime contracts, and this ExecPlan preserve that boundary.
- [x] (2026-06-12) Session 10 updated Builder prefill and `CandidateSetup` to carry Client Fit target
  rows as hypothesis-test criteria only. Enforcement proof:
  `tests/test_block_6_launchpad_to_builder_prefill.py::test_client_fit_targets_are_builder_success_criteria_not_optimizer_mandates`
  and `tests/test_block_6_candidate_setup_contract.py::test_candidate_setup_preserves_client_fit_criteria_outside_parameters_and_constraints`
  prove the target rows stay out of Builder `parameters` and `constraints`.
- [x] (2026-06-12) Session 11 extended Current vs Candidate with Current vs Candidate vs Client
  Target evidence. Enforcement proof:
  `tests/test_current_vs_candidate_comparison_contract.py::test_current_vs_candidate_shows_client_targets_without_verdict_or_winner`
  proves comparison shows target-reference rows while preserving `does_not_issue_verdict` and
  `does_not_crown_winner` guardrails.
- [x] (2026-06-12) Session 12 updated Decision Verdict rules for Client Fit. Enforcement proof:
  `tests/test_decision_verdict_client_fit.py::test_client_fit_pass_alone_cannot_create_keep_current_when_diagnosis_has_issue`
  proves Client Fit pass plus unresolved objective diagnosis does not produce keep-current/no-trade,
  and `test_goal_risk_conflict_routes_to_revise_objectives_language` proves conflict routes to
  revise-objectives language without an optimizer promise.
- [x] (2026-06-12) Session 13 updated FastAPI response models and generated frontend API types.
  Public `client_fit` envelopes now expose display-ready labels, tones, compact target rows,
  boundaries, and next-test text rather than raw artifacts. Enforcement proof: focused FastAPI
  tests assert no raw Client Fit schema/source-artifact fields appear in public `client_fit` data,
  `scripts/generate_fastapi_api_types.py` refreshed `frontend/lib/generated/api-types.ts`, and
  `scripts/verify_fastapi_contract_governance.py` passed.
- [x] (2026-06-12) Session 14 added compact Supabase storage/recovery for Client Fit display state.
  Enforcement proof: `tests/test_supabase_client_fit_compact_storage.py` proves the persistence
  helpers store/recover compact labels, tones, target rows, and boundaries only, with no
  `client_fit_check`, source-artifact maps, schema versions, local/generated paths, or raw JSON.
- [x] (2026-06-12) Session 15 added frontend Client Profile onboarding and route gating.
  `/client-profile` is now the first journey step, Portfolio Input requires a saved Client Fit
  profile before Run Diagnosis, the Next.js diagnosis bridge forwards bounded `client_fit` request
  data to FastAPI, and Hypothesis stays locked until Client Fit display evidence exists.
  Enforcement proof: frontend API tests assert route order and `client_fit` forwarding, while
  FastAPI/frontend bridge tests still prove backend compatibility with optional Client Fit.
- [x] (2026-06-12) Session 16 added the `/client-fit` screen UI. The screen shows four explicit
  sections: `Your stated profile`, `Portfolio vs your limits`, `What this means`, and `Next best
  test`, using bounded `ClientFitDisplaySummary` fields and green/amber/red tones only.
  Enforcement proof: frontend smoke/type/API checks pass and primary frontend advice/suitability
  guardrail search returns only existing safe "Equity sell-off" labels.
- [x] (2026-06-12) Session 17 updated Hypothesis, Comparison, and Verdict UI. These screens now show a bounded Client Fit context card as a separate overlay, with copy stating that a Client Fit pass does not hide structural diagnosis issues. Enforcement proof: frontend API/type checks pass and the static UI guardrail test proves the Client Fit card is present on all three screens with no forbidden advice/suitability language.
- [x] (2026-06-12) Session 18 added backend fixture-matrix anti-regression tests for conservative/balanced/aggressive interpretations, goal-risk conflict, fit-pass with concentration issue, missing Client Fit compatibility, and partial Client Fit evidence. Enforcement proof: `tests/test_client_fit_v1_matrix.py` plus existing Client Fit/verdict focused tests pass.
- [x] (2026-06-12) Session 19 ran end-to-end vertical API QA with explicit lineage checks. The
  QA verifies same-review / same-card / same-candidate / same-comparison / same-verdict lineage
  across diagnosis, Builder, candidate, comparison, verdict, and report where a candidate-generating
  Launchpad card exists; conflict/non-candidate cards are treated as objective-review stops rather
  than forced candidate runs.
- [x] (2026-06-12) Session 20 ran Browser/Playwright QA with screenshots for fit+clean,
  fit+material issue, breach, conflict, missing/blocked Client Fit, and no-advice copy. The passed
  run wrote artifacts under `output/playwright/vertical-qa-2026-06-12T14-37-52-812Z/` and captured
  fresh route screenshots from a clean browser context.
- [x] (2026-06-12) Session 21 synchronized documentation and added the final acceptance audit.
  Active source-of-truth wording no longer describes Client Fit as future-only or absent from the
  web journey, stale `client_fit_later` wording was replaced with `client_fit_v1`, and
  `docs/audits/2026-06-12_client_fit_v1_final_acceptance_audit.md` records the acceptance matrix.
  Focused Client Fit/docs/FastAPI/frontend checks passed; full backend `pytest -q` completed with
  1898 passed, 3 skipped, and 13 broad unrelated failures, so this close does not claim full-repo
  backend green status.

## Surprises & Discoveries

- Observation: Supabase is already implemented as optional compact app-data persistence, not as a
  generated-artifact store.
  Evidence: `docs/supabase/README.md` and
  `docs/exec_plans/2026-06-11_supabase_free_optional_persistence_plan.md` explicitly forbid
  uploading full artifacts and define compact stage summaries only.

- Historical observation before Sessions 15-16: the frontend route chain had no Client Fit route.
  Evidence at that time: `docs/contracts/SCREEN_CONTRACTS.md` and
  `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` listed `/portfolio-input -> /diagnosis -> /evidence ->
  /hypothesis -> /comparison -> /verdict -> /report`. Sessions 15-16 promoted `/client-profile`
  and `/client-fit`.

- Observation: The repository already has legacy profile ranges that can be reused as Client Fit
  presets while preserving compatibility.
  Evidence: `config/client_profiles.yml` contains ultra conservative through aggressive profiles
  with target return, volatility, max drawdown, and liquidity fields.

- Observation: Existing legacy profile defaults still need liquidity for compatibility even though
  Client Fit V1 excludes liquidity.
  Evidence: `tests/test_client_fit_profiles.py` verifies Client Fit preset ranges omit
  `liquidity_floor_pct`, while `src.client_profiles.get_profile_defaults("balanced")` still returns
  `liquidity_floor_pct` for legacy policy compatibility.

- Observation: The Block 4 rulebook is parity-validated against the Python taxonomy, so adding
  `goal_risk_conflict` requires updating both runtime registry entries and `config/diagnosis_rulebook.yml`.
  Evidence: `tests/test_diagnosis_rulebook.py` and
  `src/block_4/diagnosis_rulebook.py::validate_diagnosis_rulebook` compare problem ids, action path
  ids, signal lists, and Launchpad method ids.

- Historical observation after Sessions 08-09: Client Fit was partly implemented in backend/product
  artifacts and explanation/Launchpad layers, but not yet in the full web route chain.
  Evidence: `SPEC.md` and `OUTPUTS.md` already list `Client Fit Check` in the diagnosis-first flow,
  while `docs/contracts/SCREEN_CONTRACTS.md`,
  `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`, and
  `docs/contracts/FASTAPI_SCREEN_MAPPING.json` still described the visible route chain
  without `/client-profile` or `/client-fit`. `AGENTS.md` and
  `docs/contracts/PRODUCT_FLOW_CONTRACT.md` must be reviewed in Session 09A so they do not
  accidentally classify implemented Client Fit backend evidence as either a fully shipped UI product
  or as unrelated backlog.

- Observation: A broad adjacent comparison test outside the Client Fit path still expects `current`
  to be `unavailable` in optimize mode, while the current dirty working tree returns `degraded`.
  Evidence: `tests/test_candidate_comparison.py::test_current_unavailable_in_optimize_mode` failed
  during a broad optional run with `AssertionError: assert 'degraded' == 'unavailable'`. The focused
  Client Fit / Builder / Current-vs-Candidate enforcement tests passed, so this was not changed in
  Sessions 09A-11.


- Observation: Hypothesis, Comparison, and Verdict already carried bounded `clientFit` summaries in frontend state, but did not visibly explain the separation after `/client-fit`.
  Evidence: `frontend/lib/reviewState.tsx` had `clientFit` on review, comparison, verdict, and report summaries; Session 17 added `frontend/components/client-fit/ClientFitContextCard.tsx` and static frontend checks for the downstream screens.

- Observation from Session 19: `client_fit_check.json` was written run-locally but could be absent
  from `review_result.json` public outputs/paths in the FastAPI diagnosis envelope.
  Evidence: the first Browser QA attempts showed Client Fit files present under
  `runs/<review_id>/analysis_subject/client_fit_check.json`, while diagnosis API display data could
  fall back to `not_provided`. Session 19 added a safe run-local fallback in `src/api/reviews.py`
  that reads the artifact for the active `review_id` and exposes only bounded display fields plus a
  safe artifact reference.

- Observation from Session 20: a goal-risk-conflict Launchpad card is intentionally non-candidate
  (`generates_portfolio = false`).
  Evidence: the conflict QA run selected `launchpad_01_revise_objectives`; forcing Builder/Candidate
  on that card is the wrong product behavior. Session 20 updated browser QA to verify diagnosis,
  Client Fit, and Hypothesis screens for this stop state instead of requiring candidate lineage.

- Observation from Session 20: blocked Builder errors exposed an API contract mismatch: internal
  `select_another_card` is valid as a next action but not as `SafeError.user_action`.
  Evidence: a conflict QA attempt produced a Pydantic validation error for `SafeError.user_action`.
  Session 20 changed the bounded public user action to `return_to_hypothesis`.
- Observation from Session 21: full backend pytest is not green in the current working tree.
  Evidence: `pytest -q` completed in 26:43 with 1898 passed, 3 skipped, and 13 failed. The failures
  are outside the focused Client Fit path: current-vs-candidate/comparison status drift, pandas `QE`
  compatibility in macro tests, ETF/stock universe seed-size expectations, MVP workflow command
  expectations, factor covariance skip handling, and Portfolio X-Ray golden fixture drift.

## Decision Log

- Decision: Session 09A source-of-truth status is `partially implemented backend interpretation
  overlay; full web journey pending`.
  Rationale: Backend artifacts and downstream display/test criteria now exist, but dedicated
  `/client-profile` and `/client-fit` frontend routes, bounded API display envelopes, and Supabase
  persistence are later sessions.
  Date/Author: 2026-06-12 / Codex.

- Decision: Builder and Current vs Candidate may carry Client Fit targets only as display/test
  evidence.
  Rationale: The downstream decision matrix requires Client Fit status, diagnostic quality, and
  decision action to remain separate. Target rows help test a hypothesis but must not alter optimizer
  behavior or issue a verdict.
  Date/Author: 2026-06-12 / Codex.

- Decision: Client Fit V1 excludes liquidity.
  Rationale: The user selected this scope to keep V1 focused on target return, volatility,
  drawdown, and horizon. Existing liquidity fields remain legacy/advanced or future/backlog and do
  not drive Client Fit V1 gates.
  Date/Author: 2026-06-12 / Codex.

- Decision: Client Fit is a diagnostic interpretation overlay, not suitability approval.
  Rationale: Professional sources such as CFA IPS material, FINRA investor-profile concepts, and
  Vanguard questionnaire framing support gathering objectives, risk tolerance, and horizon, but
  Portfolio MRI must remain non-binding decision support and avoid trade/advice language.
  Date/Author: 2026-06-12 / Codex.

- Decision: The web journey will require Client Fit, while backend/CLI paths remain compatible when
  Client Fit is missing.
  Rationale: The product experience should answer "does it fit you?", but repository entrypoints and
  legacy workflows must continue to run for tests, operators, and compatibility.
  Date/Author: 2026-06-12 / Codex.

- Decision: Sessions 06 onward must include explicit enforcement checks for the known Client Fit
  failure modes.
  Rationale: The main implementation risk is not only code failure, but semantic drift: mixing
  objective diagnosis with personal fit, treating Client Fit as suitability approval, letting fit
  pass suppress structural risks, creating a universal Client Fit breach diagnosis, breaking legacy
  optimizer compatibility, or letting API/frontend/Supabase contracts drift apart. Each downstream
  session must add tests or QA checks that prove these failure modes are blocked.
  Date/Author: 2026-06-12 / Codex.

- Decision: `goal_risk_conflict` is the only Client Fit V1 primary Problem Classification
  exception; all other Client Fit signals are supporting, contrary, or display context.
  Rationale: This preserves the diagnosis-first boundary. A profile breach can help explain why an
  objective volatility, drawdown, or stress diagnosis matters, but it must not become a universal
  portfolio problem. Internal inconsistency in the stated objectives is different: it blocks
  interpretation until objectives are reviewed.
  Date/Author: 2026-06-12 / Codex.

- Historical decision before Sessions 15-16: Until the frontend route and screen contracts were
  updated, Client Fit V1 was a partially implemented Core MVP backend interpretation overlay, not a
  fully shipped web journey.
  Rationale: The backend writes `client_fit_check.json`, Block 4 and Launchpad can use bounded
  Client Fit context, and site/report explanation can surface it. However, the visible frontend
  route chain then had no `/client-profile` or `/client-fit` route. Source-of-truth docs
  must preserve this distinction to avoid both over-promoting Client Fit as complete UI and
  incorrectly treating implemented backend contracts as backlog.
  Date/Author: 2026-06-12 / Codex.

- Decision: Client Fit target return, volatility, drawdown, and horizon values are hypothesis-test
  and display criteria, not hidden optimizer mandates.
  Rationale: Builder, Candidate Generation, and optimizer/factory code must not silently translate
  `target_return_range`, `target_vol_range`, `target_max_drawdown_pct`, or `horizon_years` into
  optimizer objectives, hard constraints, mandate pass/fail gates, analysis-window overrides, or
  factory command changes. They may be displayed as success criteria, comparison references, and
  interpretation context only unless a later accepted spec explicitly changes optimizer behavior.
  Date/Author: 2026-06-12 / Codex.

- Decision: Downstream sessions must use an explicit Client Fit decision matrix before changing
  Builder, Comparison, or Verdict behavior.
  Rationale: `client_fit_status`, `diagnostic_quality_status`, and `decision_action` must not be
  inferred from each other. A fit result can coexist with a material objective issue; a breach can
  coexist with clean objective diagnostics; conflict means objectives need review first; missing or
  insufficient Client Fit evidence must not create Client Fit conclusions.
  Date/Author: 2026-06-12 / Codex.

- Decision: Public API and frontend surfaces must expose bounded display-ready Client Fit models,
  not raw `client_fit_check.json` or raw `client_fit_context` internals.
  Rationale: Raw artifact filenames, schema versions, source paths, backend status ids, and
  source-artifact maps are implementation vocabulary. Primary UI should consume compact display
  fields such as status label/tone, profile label, source-quality label, target/limit rows,
  boundary text, and next-test language.
  Date/Author: 2026-06-12 / Codex.

- Decision: Close Client Fit V1 with focused acceptance evidence and an explicit broad-suite caveat.
  Rationale: Session 21 changed documentation/source-of-truth wording and did not change the broad
  modules failing in full pytest. Focused Client Fit tests, docs verification, FastAPI governance,
  frontend API tests, frontend typecheck, stale-reference audit, guardrail search, and diff check all
  passed, while full-suite failures are recorded for separate owning work rather than hidden.
  Date/Author: 2026-06-12 / Codex.

## Outcomes & Retrospective

Session 00 safely created the implementation branch and audit record. Session 01 established the
source-of-truth documentation for Client Fit V1 without changing behavior. Session 02 added
read-only Client Fit presets/questionnaire config and validation helpers without wiring them into
runtime diagnosis or frontend behavior. Session 03 added the optional Client Fit request/input
contract and run-local preservation path without generating Client Fit artifacts or changing
diagnosis behavior. Sessions 04 and 05 added the generated Client Fit check artifact and made it
visible to Block 4 evidence extraction as context only, without changing the Block 4 rulebook or
selected diagnosis behavior.

Sessions 06 and 07 promoted Client Fit from raw context into governed Block 4 interpretation while
preserving the separation boundary. Client Fit dimension breaches can support relevant diagnoses
only when objective portfolio evidence is also present; `client_fit_within_profile` can be contrary
context; `goal_risk_conflict` can be selected as a primary objective-review outcome; and
`client_fit_status` remains separate from objective `diagnostic_quality_status`.

Sessions 08 and 09 extended that separation into site/report copy hierarchy and Candidate
Launchpad. The report/site explanation layer now has sourced Client Fit rows and stricter
forbidden-copy guards. Launchpad cards can show Client Fit context, but a fit status cannot suppress
a material objective diagnosis; it remains a hypothesis/review path until later comparison and
Decision Verdict evidence exists.

Sessions 09A, 10, and 11 stabilized the source-of-truth boundary and carried Client Fit into Builder
and Current vs Candidate without promoting it into optimizer behavior or verdict logic. Builder now
adds Client Fit target rows as hypothesis-test criteria, `CandidateSetup` keeps those rows outside
`parameters` and `constraints`, and Current vs Candidate can show target-reference rows while
explicitly stating that comparison does not issue a verdict or crown a winner.

Sessions 12, 13, and 14 carried Client Fit into Decision Verdict, public FastAPI envelopes, generated
frontend API types, and optional Supabase persistence while preserving the separation boundary. The
Decision Verdict now records `decision_action` and bounded Client Fit decision context; Client Fit
pass cannot by itself clear unresolved objective diagnosis; goal-risk conflict routes to
revise-objectives language; API envelopes expose display-ready Client Fit fields; and Supabase saves
only compact display summaries, not generated artifacts or raw Client Fit JSON.

Session 21 closed the Client Fit V1 foundation for the current implementation boundary. The
source-of-truth documents now describe Client Fit as an implemented V1 layer with active web
onboarding and display routes, while preserving backend/CLI missing-profile compatibility and the
Blocks 1-3 calculation boundary. The final acceptance audit records focused proof and the broad
full-suite caveat: Client Fit is accepted, but the repository-wide backend suite is not green until
separate unrelated failures are fixed.

## Context and Orientation

Portfolio MRI is a diagnosis-first, current-portfolio-first decision-support system. The current
foundation chain starts with portfolio input, then Portfolio X-Ray, Stress Lab, Client Fit Check,
Problem Classification, Candidate Launchpad, Builder, Candidate Generation, Current vs Candidate,
Decision Verdict, and grounded report context. Client Fit V1 is the personal-fit layer after Stress
Lab and before Problem Classification so that the diagnosis engine can distinguish objective
portfolio facts from client-specific interpretation.

`Client Fit` means a non-binding check that compares portfolio evidence against the user's provided
return, volatility, maximum drawdown, and horizon targets. It is not an optimizer mandate and not
legal suitability approval. `Client Fit status` answers whether the portfolio fits the provided
profile. `Diagnostic quality status` answers whether the portfolio has structural issues. `Decision
action` is the non-binding next step after comparing current portfolio evidence, client fit, and any
candidate evidence.

Important current files include `docs/specs/input_assumptions_spec.md` for input-layer boundaries,
`docs/specs/block_4_diagnosis_v3_spec.md` for Problem Classification, `config/client_profiles.yml`
for reusable profile ranges, `src/block_4/` for evidence-to-diagnosis logic, `src/api/` for FastAPI
contracts, `frontend/` for the Next.js app, and `docs/supabase/` for optional compact persistence.

## Plan of Work

The work proceeds in the sessions listed in `Progress`. Each session must be independently
verifiable and must update this ExecPlan before stopping. The implementation order is deliberately
additive: specs first, then configuration/validators, then backend artifact, then Block 4 evidence,
then downstream comparison/verdict, then API/frontend/Supabase, and finally end-to-end QA.

Do not remove legacy optimizer capabilities simply because Client Fit exists. Preserve them as
legacy/advanced unless a later session explicitly proves they conflict with the new product path and
updates the owning specs and tests.

Session 09A is a hard stabilization gate. Do not start Session 10 or later until Session 09A has:

- reconciled source-of-truth wording across `AGENTS.md`, `SPEC.md`, `OUTPUTS.md`,
  `docs/contracts/PRODUCT_FLOW_CONTRACT.md`, `docs/contracts/SCREEN_CONTRACTS.md`,
  `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`,
  `docs/contracts/FASTAPI_SCREEN_MAPPING.json`, and `docs/runtime_artifact_contract.md`;
- locked the post-Session-09 status as "partially implemented backend interpretation overlay;
  full web journey pending" unless the owning contracts are intentionally promoted together;
- proved Session 08 and Session 09 enforcement tests still pass after documentation sync;
- recorded any remaining source-of-truth mismatch as a known issue or explicit blocker before
  touching Builder, Comparison, Verdict, FastAPI, frontend, or Supabase code.

From Session 06 onward, every session must include an "enforcement proof" in this ExecPlan before it
can be marked complete. An enforcement proof is a focused test, contract check, UI screenshot, or
audit note that proves the session did not introduce one of the known semantic failures. The proof
must be specific; a generic passing test suite is not enough.

The mandatory semantic boundaries are:

- Objective diagnosis and Client Fit interpretation must remain separate. X-Ray and Stress metrics
  must not change merely because the client profile changes.
- Client Fit must not become a universal diagnosis. Except for `goal_risk_conflict`, primary
  diagnoses should remain portfolio-structure or evidence-quality diagnoses, with Client Fit as
  context, supporting evidence, or contrary evidence.
- Client Fit pass must not suppress material structural issues. A fit-pass portfolio with high
  concentration, weak crisis resilience, hedge gap, or other material issue must still route to
  monitor, review, or test-candidate language.
- Client Fit breach must not become trade advice. It can justify a hypothesis test or review, not a
  buy/sell/must-rebalance instruction.
- Goal-risk conflict must be handled as an objective inconsistency, not as an optimizer promise to
  find impossible return with low risk.
- Legacy optimizer/client-profile behavior must stay compatible until explicitly migrated. Existing
  `client_profile`, target fields, and legacy liquidity fields must not be silently repurposed into
  Client Fit V1 gates.
- FastAPI, frontend, Supabase, docs, and generated TypeScript types must describe the same display
  fields. The frontend must consume display-ready Client Fit models, not raw generated artifacts, in
  primary UI.
- Supabase must remain compact-only. It must not store `client_fit_check.json`, full X-Ray, full
  Stress Lab, generated folders, PDFs, price history, or other raw evidence artifacts.
- Primary UI copy must avoid "suitable", "approved", "best portfolio", "buy", "sell", "must
  rebalance", and similar advice/execution wording.

The mandatory downstream decision matrix is:

| Client Fit status | Diagnostic quality status | Candidate/comparison evidence | Required interpretation boundary |
| --- | --- | --- | --- |
| `fit` | `clean` | no candidate or no material improvement | Monitor / keep-current may be considered later, but only after verdict evidence confirms no material unresolved issue. |
| `fit` | `material_issue` or `issue` | any | Do not produce no-action from fit alone; preserve review, monitor, or test-candidate language tied to the objective diagnosis. |
| `breach` or `watch` | `clean` | no candidate | Treat as profile-risk review or hypothesis-test context, not trade advice and not an automatic rebalance. |
| `breach` or `watch` | `issue` or `material_issue` | any | Explain both layers separately: objective issue plus personal-fit concern; do not collapse them into one universal Client Fit diagnosis. |
| `conflict` | any | any | Route to revise-objectives / objective review before interpreting candidate tests; do not promise the optimizer can satisfy inconsistent goals. |
| `not_provided` | any | any | Backend/CLI-compatible generic diagnosis only; no Client Fit conclusion may be claimed. |
| `evidence_insufficient` | any | any | Evidence insufficient for Client Fit; do not infer fit, breach, keep-current, or rebalance from missing evidence. |

The mandatory Builder/optimizer boundary is:

- `target_return_range`, `target_vol_range`, `target_max_drawdown_pct`, and `horizon_years` may be
  copied into Builder or Comparison only as display context, success criteria, and hypothesis-test
  reference values.
- They must not change optimizer objective functions, constraints, mandate gates, factory method
  selection, analysis windows, portfolio weights, or candidate generation commands in V1.
- If a future session intentionally promotes any Client Fit value into optimizer behavior, it must
  create/update the owning optimizer/spec contract, tests, docs, and decision log before code
  changes.

The mandatory display-model boundary is:

- FastAPI/frontend primary screens must consume bounded Client Fit summaries rather than raw
  artifacts.
- Allowed display concepts include profile label, profile/source-quality label, status label,
  status tone, target/limit rows, most important breach/watch/conflict explanation, decision
  boundary, and next best test.
- Raw `client_fit_check.json`, `client_fit_context`, `schema_version`, `source_artifacts`,
  `field_path`, backend ids, and booleans may appear only in adapters, tests, operator/debug views,
  or source references; they must not appear in primary UI copy.

The mandatory UI/UX blueprint is:

- `/client-profile` answers "Who is this portfolio for?" It contains the mandatory web
  questionnaire, suggested preset, editable targets, source-quality disclosure, and the planning
  profile disclaimer. It must not show portfolio diagnostics because the portfolio has not been
  diagnosed yet.
- `/portfolio-input` answers "What do you own?" It shows holdings, weights, currency, validation,
  and a compact Client Fit profile chip with an edit link. It must not show optimizer targets as a
  primary input panel and must keep the Run Diagnosis CTA disabled until the web user has a valid
  Client Fit profile.
- `/diagnosis` answers "What does the portfolio look like?" It shows objective Portfolio X-Ray and
  Problem Classification bridge evidence. It may mention that Client Fit will be evaluated after
  Stress Lab, but it must not label the portfolio good/bad for the client on this screen.
- `/evidence` answers "How does it behave under stress?" It shows objective Stress Lab outcomes,
  hedge gaps, limitations, and contributors. It must not make client-fit conclusions directly; the
  next-step CTA should lead to Client Fit.
- `/client-fit` answers "Does this risk fit the provided profile?" It must have four visible
  sections: `Your stated profile`, `Portfolio vs your limits`, `What this means`, and `Next best
  test`. It must separate fit/watch/breach/conflict/evidence-insufficient states and show the
  source-quality disclosure.
- `/hypothesis` answers "What should we test?" It must show why the selected hypothesis matters for
  both the portfolio diagnosis and Client Fit, while preserving candidate-as-test language.
- `/comparison` answers "Did the candidate improve the diagnosis and fit?" It must show Current vs
  Candidate vs Client Target evidence, and must not issue a verdict.
- `/verdict` answers "What is the non-binding decision-support action?" It must show three separate
  rows or cards: Client Fit Status, Diagnostic Quality Status, and Decision Action. It must state
  decision-support-only language and must not imply suitability approval.
- `/report` answers "What evidence supports the story?" It must summarize the same diagnosis,
  Client Fit, hypothesis, comparison, and verdict chain without introducing new claims.

The mandatory visual hierarchy for Client Fit UI uses three primary semantic colors only:

- Green means within stated limits or acceptable evidence.
- Amber means watch, review, test candidate, missing/partial evidence, or evidence insufficient.
- Red means breach or goal-risk conflict, not "sell now".

Neutral grays may be used only for layout, borders, muted text, disabled controls, and background
surfaces. Blue may remain only for ordinary interactive controls such as links and buttons, not as a
fourth semantic status color. If a status cannot fit Green, Amber, or Red, it must be shown as Amber
with plain-language explanation.

The mandatory Client Fit screen copy pattern is:

    Your stated profile: <profile label>, target return, volatility comfort range,
    maximum temporary loss, horizon, and profile confidence/source quality.

    Portfolio vs your limits: a compact table with Dimension, Portfolio, Your target/limit,
    and Status.

    What this means: one source-backed paragraph that connects the most important check to
    the profile without saying suitable/approved.

    Next best test: one hypothesis-oriented CTA, such as testing a defensive or diversification
    candidate, or revising objectives when a goal-risk conflict is detected.

## Concrete Steps

Work from repository root:

    D:\Р Р°Р±РѕС‡РёР№ СЃС‚РѕР»\РљРЈР РЎРћР  РўРЈР›Рђ Р”РРђР“РќРћРЎРўРРљРђ

Use Windows PowerShell. If Python is needed, prefer:

    .\.venv\Scripts\python.exe

Session 01 verification commands are:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 02 verification commands and observed result:

    .\.venv\Scripts\python.exe -m pytest tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py -q
    4 passed


    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py tests\test_fastapi_app.py tests\test_blocks_5_to_9_vertical_flow.py -q
    49 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors

Future sessions must add the exact commands they run and the expected result in this section.

Session 03 verification commands and observed result:

    .\.venv\Scripts\python.exe scripts\generate_fastapi_api_types.py
    Wrote frontend\lib\generated\api-types.ts

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_frontend_review_bridge.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py -q
    52 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK

    git diff --check
    no whitespace errors

Session 04-05 verification commands and observed result:

    .\.venv\Scripts\python.exe -m pytest tests\test_client_fit_check.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py tests\test_block_4_evidence_extraction.py -q
    15 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_client_fit_check.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py tests\test_block_4_evidence_extraction.py tests\test_block_4_diagnosis_builder.py tests\test_mvp_portfolio_review_materialization.py -q
    31 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors (Git reported existing LF-to-CRLF working-copy warnings only)

Session 06-07 verification commands and observed result:

    .\.venv\Scripts\python.exe -m pytest tests\test_client_fit_check.py tests\test_block_4_problem_scoring.py tests\test_block_4_problem_prioritization.py tests\test_block_4_problem_taxonomy.py tests\test_diagnosis_rulebook.py -q
    48 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_client_fit_check.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py tests\test_block_4_evidence_extraction.py tests\test_block_4_diagnosis_builder.py tests\test_block_4_problem_scoring.py tests\test_block_4_problem_prioritization.py tests\test_block_4_problem_taxonomy.py tests\test_diagnosis_rulebook.py tests\test_mvp_portfolio_review_materialization.py -q
    74 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    cd frontend
    npm.cmd run typecheck
    tsc --noEmit passed
    cd ..

    rg -n "\bsuitable\b|\bsuitability approved\b|\bapproved\b|\bbuy\b|\bsell\b|\bmust rebalance\b|\bbest portfolio\b" frontend src docs config tests
    Returned existing docs/tests/guardrail-code matches and the safe Launchpad disclaimer phrase. The
    Session 06-07 changes removed a primary demo-report `suitable` phrase and do not add product
    conclusion copy using the forbidden terms.

    git diff --check
    no whitespace errors (Git reported existing LF-to-CRLF working-copy warnings only)

Session 08-09 verification commands and observed result:

    .\.venv\Scripts\python.exe -m pytest tests\test_site_explanation_guardrails.py tests\test_site_explanation_candidate_comparison_verdict.py tests\test_site_explanation_bundle.py tests\test_ai_commentary_context.py tests\test_block_4_launchpad_cards.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py -q
    44 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_site_explanation_guardrails.py tests\test_site_explanation_candidate_comparison_verdict.py tests\test_site_explanation_bundle.py tests\test_ai_commentary_context.py tests\test_block_4_launchpad_cards.py tests\test_client_fit_check.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py tests\test_block_4_evidence_extraction.py tests\test_block_4_diagnosis_builder.py tests\test_block_4_problem_scoring.py tests\test_block_4_problem_prioritization.py tests\test_block_4_problem_taxonomy.py tests\test_diagnosis_rulebook.py tests\test_frontend_review_bridge.py tests\test_fastapi_app.py -q
    153 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    rg -n "\bsuitable\b|\bsuitability approved\b|\bapproved\b|\bbuy\b|\bsell\b|\bmust rebalance\b|\bbest portfolio\b" frontend src docs config tests
    Returned existing documentation/test guardrail references, benign "Equity sell-off" display
    labels/demo strings, and existing generated-support/test phrases. The Session 08-09 changes add
    no primary UI/report copy that presents forbidden language as a product conclusion.

    git diff --check
    no whitespace errors (Git reported existing LF-to-CRLF working-copy warnings only)

Session 09A required verification commands and expected result:

    .\.venv\Scripts\python.exe -m pytest tests\test_site_explanation_guardrails.py tests\test_block_4_launchpad_cards.py tests\test_client_fit_check.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py tests\test_diagnosis_rulebook.py -q
    Expected: all pass; proves Session 08-09 copy/Launchpad boundaries, Client Fit no-liquidity
    compatibility, and diagnosis-rulebook parity still hold.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    Expected: docs verification OK after source-of-truth synchronization.

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    Expected: FastAPI contract governance OK if any API/display contract docs or generated API
    types are touched.

    rg -n "Client-Fit Check|Client Fit Check|Client Fit V1|client_fit_check|client-profile|client-fit" AGENTS.md SPEC.md OUTPUTS.md docs\contracts\PRODUCT_FLOW_CONTRACT.md docs\contracts\SCREEN_CONTRACTS.md docs\contracts\ARTIFACT_TO_SCREEN_MAP.md docs\contracts\FASTAPI_SCREEN_MAPPING.json docs\runtime_artifact_contract.md
    Expected: hits consistently describe Client Fit as a partially implemented backend
    interpretation overlay until frontend route contracts are intentionally updated; no file should
    simultaneously classify the same implemented backend layer as both current complete UI and
    unrelated backlog.

    rg -n "\bsuitable\b|\bsuitability approved\b|\bapproved\b|\bbuy\b|\bsell\b|\bmust rebalance\b|\bbest portfolio\b" frontend src docs config tests
    Expected: only explicit guardrail/docs/test references, safe non-product labels, or negated
    disclaimers; no primary UI/report/API display/rulebook conclusion copy may use forbidden
    advice/suitability wording.

    rg -n "target_return_range|target_vol_range|target_max_drawdown_pct|horizon_years|client_fit" src\portfolio_alternatives_builder.py src\candidate_generation.py src\candidate_comparison.py src\decision_verdict.py docs\specs docs\contracts
    Expected: downstream references treat Client Fit targets as display/test criteria unless an
    owning spec explicitly promotes optimizer behavior; no hidden Builder/factory/optimizer mandate
    is introduced before Session 10.

    git diff --check
    Expected: no whitespace errors.

Session 09A-11 verification commands and observed result:

    .\.venv\Scripts\python.exe -m pytest tests\test_site_explanation_guardrails.py tests\test_block_4_launchpad_cards.py tests\test_client_fit_check.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py tests\test_diagnosis_rulebook.py tests\test_block_6_launchpad_to_builder_prefill.py tests\test_block_6_candidate_setup_contract.py tests\test_current_vs_candidate_comparison_contract.py tests\test_current_vs_candidate.py tests\test_current_vs_candidate_success_criteria.py -q
    63 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_site_explanation_guardrails.py tests\test_block_4_launchpad_cards.py tests\test_client_fit_check.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py tests\test_diagnosis_rulebook.py -q
    44 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_block_6_builder_prefill_contract.py tests\test_block_6_launchpad_to_builder_prefill.py tests\test_block_6_candidate_setup_contract.py tests\test_block_6_builder_validation.py tests\test_block_6_parameter_builder_simple_mode.py tests\test_candidate_generation_from_builder_setup.py tests\test_current_vs_candidate_comparison_contract.py tests\test_current_vs_candidate.py tests\test_current_vs_candidate_success_criteria.py tests\test_current_vs_candidate_tradeoffs.py tests\test_candidate_comparison.py -q
    79 passed, 1 failed: existing adjacent `tests/test_candidate_comparison.py::test_current_unavailable_in_optimize_mode` expected `unavailable` but current code returned `degraded`; not changed because it is outside the Client Fit / Builder / Current-vs-Candidate target-row path.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    rg -n "Client-Fit Check|Client Fit Check|Client Fit V1|client_fit_check|client-profile|client-fit" AGENTS.md SPEC.md OUTPUTS.md docs\contracts\PRODUCT_FLOW_CONTRACT.md docs\contracts\SCREEN_CONTRACTS.md docs\contracts\ARTIFACT_TO_SCREEN_MAP.md docs\contracts\FASTAPI_SCREEN_MAPPING.json docs\runtime_artifact_contract.md
    Observed: hits consistently describe Client Fit as backend interpretation overlay with full web journey pending, while Builder/Comparison target rows are bounded display/test evidence.

    rg -n "\bsuitable\b|\bsuitability approved\b|\bapproved\b|\bbuy\b|\bsell\b|\bmust rebalance\b|\bbest portfolio\b" frontend src docs config tests
    Observed: returned explicit guardrail/docs/test references, safe negated Launchpad copy, legacy trade-row terminology, and non-product documentation examples; no new primary UI/report/API conclusion copy presents forbidden language as advice.

    rg -n "target_return_range|target_vol_range|target_max_drawdown_pct|horizon_years|client_fit" src\portfolio_alternatives_builder.py src\candidate_generation.py src\candidate_comparison.py src\decision_verdict.py docs\specs docs\contracts
    Observed: Builder and Comparison references describe Client Fit targets as display/test criteria or comparison references; no hidden optimizer mandate, verdict action, factory method change, or candidate weight behavior was introduced.

    git diff --check
    no whitespace errors (Git reported existing LF-to-CRLF working-copy warnings only)

Session 12-14 verification commands and observed result:

    .\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict_client_fit.py tests\test_decision_verdict.py tests\test_decision_verdict_no_trade.py tests\test_decision_verdict_contract.py tests\test_fastapi_app.py tests\test_supabase_client_fit_compact_storage.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py -q
    30 passed

    .\.venv\Scripts\python.exe scripts\generate_fastapi_api_types.py
    Wrote frontend\lib\generated\api-types.ts

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    cd frontend
    npm.cmd run typecheck
    tsc --noEmit passed
    cd ..

    .\.venv\Scripts\python.exe -m pytest tests\test_supabase_client_fit_compact_storage.py -q
    2 passed; static compact-storage audit found no raw client_fit_check, source-artifact maps,
    schema versions, local/generated paths, or raw JSON in Client Fit Supabase helpers.

Session 15-16 verification commands and observed result:

    cd frontend
    npm.cmd run typecheck
    tsc --noEmit passed

    npm.cmd run test:api
    11 passed; added checks prove `/client-profile -> /portfolio-input -> /diagnosis -> /evidence
    -> /client-fit -> /hypothesis` route gating and `client_fit` forwarding to FastAPI.

    npm.cmd run test:smoke
    1 passed; static Next smoke verified `/client-profile` and `/client-fit` render alongside the
    existing journey routes.

    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py tests\test_fastapi_app.py tests\test_frontend_review_bridge.py -q
    52 passed; backend/FastAPI compatibility still accepts optional Client Fit while frontend
    bridge tests remain stable.

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    rg -n "\bsuitable\b|\bsuitability approved\b|\bapproved\b|\bbuy\b|\bsell\b|\bmust rebalance\b|\bbest portfolio\b" frontend\app frontend\components frontend\lib
    Observed only existing safe `Equity sell-off` display-label matches; no Client Fit primary UI
    copy uses forbidden advice/suitability wording.

    Get-ChildItem frontend\app -Directory | Select-Object -ExpandProperty Name
    Observed active route folders include `client-profile` and `client-fit` and still exclude
    current `candidate`, `monitoring`, and `what-changed` routes.

    git diff --check
    no whitespace errors (Git reported existing LF-to-CRLF working-copy warnings only)


Session 17-18 verification commands and observed result:

    cd frontend
    npm.cmd run test:api
    12 passed; added static UI guardrail proves Hypothesis, Comparison, and Verdict all render the bounded Client Fit context card and that the checked downstream UI files avoid forbidden advice/suitability terms.

    npm.cmd run typecheck
    tsc --noEmit passed

    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_client_fit_v1_matrix.py tests\test_client_fit_check.py tests\test_decision_verdict_client_fit.py -q
    19 passed; the fixture matrix proves conservative/balanced/aggressive profiles change only Client Fit interpretation, goal-risk conflict routes to objective review, fit-pass plus concentration remains a structural issue and test-another verdict, missing Client Fit remains backend-compatible, and partial evidence becomes evidence-insufficient.


Session 19-20 verification commands and observed result:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_frontend_review_bridge.py tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py -q
    52 passed; FastAPI/frontend bridge compatibility still holds after Client Fit run-local fallback and safe-error user-action fix.

    cd frontend
    npm.cmd run test:api
    12 passed; frontend API route and lineage guard tests still pass.

    npm.cmd run typecheck
    tsc --noEmit passed.

    npm.cmd run qa:vertical -- --scenario-limit 5
    passed; fresh FastAPI and Next.js ports were used, browser localStorage/sessionStorage were cleared before each scenario, and screenshots plus `qa-report.json` were written to `output/playwright/vertical-qa-2026-06-12T14-37-52-812Z/`.
    Covered scenarios: `fit_material_issue` (green Client Fit with downstream lineage through report), `breach` (red Client Fit with downstream lineage through report), `fit_clean` (green Client Fit), `conflict` (red goal-risk conflict, non-candidate objective-review stop), and `missing_blocked_client_fit` (amber not-provided compatibility state).
    Active URLs in the passed run: frontend `http://127.0.0.1:58335`, FastAPI `http://127.0.0.1:58334`.

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK.

    rg -n "\bsuitable\b|\bsuitability approved\b|\bapproved\b|\bbuy\b|\bsell\b|\bmust rebalance\b|\bbest portfolio\b" frontend src docs config tests
    Observed only guardrail/docs/test references, the safe `Equity sell-off` label, and negated disclaimer language; Browser QA also scanned rendered route text after replacing the safe `Equity sell-off` label and found no forbidden advice/suitability copy.

    git diff --check
    no whitespace errors (Git reported existing LF-to-CRLF working-copy warnings only).

Session 21 verification commands and observed result:

    .\.venv\Scripts\python.exe -m pytest tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py tests\test_client_fit_check.py tests\test_client_fit_v1_matrix.py tests\test_decision_verdict_client_fit.py tests\test_input_assumptions.py -q
    49 passed.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK.

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    cd frontend
    npm.cmd run test:api
    12 passed.

    npm.cmd run typecheck
    tsc --noEmit passed.

    rg -n -i "full web journey pending|routes are still pending|Planned V1|future Client-Fit Check|later Client-Fit Check|later ? not Core MVP input|Client Fit V1 foundation input contract|Target/TBD.*Client|Client.*Target/TBD|no client profile in Core MVP|does not require client profile|client profile.*not required|not required.*client profile" AGENTS.md SPEC.md OUTPUTS.md README.md PRODUCT.md ARCHITECTURE.md DESIGN.md DATA.md TESTING.md GLOSSARY.md DECISIONS.md CHANGELOG.md docs/contracts docs/specs docs/runtime_artifact_contract.md frontend/README.md src tests config scripts
    No matches.

    rg -n "\bsuitable\b|\bsuitability approved\b|\bapproved\b|\bbuy\b|\bsell\b|\bmust rebalance\b|\bbest portfolio\b" frontend src docs config tests
    Returned explicit guardrail/docs/test references, safe `Equity sell-off` labels, legacy code variables, and negated disclaimers; no Session 21 primary UI/report/API conclusion copy presents forbidden language as advice.

    git diff --check
    no whitespace errors (Git reported existing LF-to-CRLF working-copy warnings only).

    .\.venv\Scripts\python.exe -m pytest -q
    1898 passed, 3 skipped, 13 failed in 26:43. Failures are broad unrelated repository regressions recorded in the final acceptance audit; this plan close does not claim full backend-suite green status.

Required enforcement commands and checks from Session 06 onward:

    rg -n "\bsuitable\b|\bsuitability approved\b|\bapproved\b|\bbuy\b|\bsell\b|\bmust rebalance\b|\bbest portfolio\b" frontend src docs config tests

This search may return documentation lines that explicitly list forbidden language. It must not
return primary UI copy, report copy, site explanation copy, API display strings, or rulebook
narrative that presents those words as product conclusions.

    .\.venv\Scripts\python.exe -m pytest tests\test_client_fit_profiles.py tests\test_client_fit_questionnaire.py -q

This focused compatibility check must continue to pass after every Client Fit session so legacy
profile defaults and V1 no-liquidity boundaries are not accidentally broken.

Sessions that touch FastAPI must also run:

    .\.venv\Scripts\python.exe scripts\generate_fastapi_api_types.py
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py

Sessions that touch frontend must also run:

    cd frontend
    npm.cmd run typecheck
    cd ..

Sessions 15, 16, 17, and 20 must also update or verify `docs/contracts/SCREEN_CONTRACTS.md`,
`docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`, and `docs/contracts/FASTAPI_SCREEN_MAPPING.json` so
the UI route order, screen question, source artifacts, adapter ownership, forbidden terms, and QA
checks match the mandatory UI/UX blueprint above.

Sessions that touch Supabase must include a compact-storage audit proving no full generated
artifact path or raw artifact JSON is written to Supabase persistence helpers.

## Validation and Acceptance

Final acceptance requires:

- Web users complete Client Fit before portfolio diagnosis.
- Backend/CLI paths continue with `client_fit_status = "not_provided"` when Client Fit is absent.
- `analysis_subject/client_fit_check.json` is generated after Stress Lab and before Problem
  Classification.
- Problem Classification uses Client Fit as evidence/context, not as a universal diagnosis.
- Client Fit status, Diagnostic Quality status, and Decision Action remain separate.
- Candidate Launchpad, Builder, Current vs Candidate, and Decision Verdict are client-fit-aware.
- Session 09A source-of-truth synchronization is complete before Builder, Comparison, Verdict, API,
  frontend, or Supabase sessions continue.
- No primary UI copy says "suitable", "approved", "buy", "sell", "must rebalance", or "best
  portfolio".
- Supabase stores only compact Client Fit/profile summaries and never full generated artifacts.
- Client Fit pass plus material diagnostic issue produces review/monitor/test-candidate language,
  not automatic no-trade.
- `goal_risk_conflict` produces revise-objectives or explicit trade-off-test language, not an
  optimizer promise.
- Same portfolio under conservative, balanced, and aggressive profiles changes Client Fit
  interpretation but does not change objective X-Ray or Stress metrics.
- Forbidden advice/suitability language is absent from primary UI, site explanation, API display
  strings, and rulebook user-facing narrative.
- Full backend tests, FastAPI contract governance, documentation verification, frontend typecheck,
  and Browser/Playwright QA pass.
- UI acceptance must prove the user can read the journey as three distinct questions before action:
  "what do you own?", "what does the portfolio look like?", and "does it fit you?"

## Idempotence and Recovery

All sessions should be additive until tests prove replacement is safe. If a session fails, stop with
the branch state visible in `git status --short`, record the blocker in this ExecPlan, and do not
mask failures by deleting generated or source artifacts. Generated outputs are not source unless a
session explicitly targets them.

## Artifacts and Notes

Session 21 final audit:

    docs/audits/2026-06-12_client_fit_v1_final_acceptance_audit.md

Session 00 audit:

    docs/audits/2026-06-12_client_fit_v1_session00_baseline_audit.md

Session 01 specs:

    docs/specs/client_fit_check_spec.md
    docs/specs/client_fit_questionnaire_spec.md

Session 02 config and validation helpers:

    config/client_fit_questionnaire.yml
    src/client_fit.py
    tests/test_client_fit_profiles.py
    tests/test_client_fit_questionnaire.py

Session 03 input/API contract files:

    src/api/models.py
    src/api/reviews.py
    scripts/run_review_from_payload.py
    src/config_schema.py
    src/input_assumptions.py
    frontend/lib/generated/api-types.ts
    tests/test_fastapi_app.py
    tests/test_frontend_review_bridge.py
    docs/contracts/FASTAPI_V1_API_CONTRACT.md
    docs/specs/input_assumptions_spec.md

Session 04-05 artifact/evidence files:

    src/client_fit.py
    run_report.py
    src/block_4/evidence_extraction.py
    src/block_4/diagnosis_builder.py
    tests/test_client_fit_check.py
    docs/specs/client_fit_check_spec.md
    docs/specs/block_4_diagnosis_v3_spec.md

Session 06-07 rulebook and interpretation files:

    config/diagnosis_rulebook.yml
    src/block_4/problem_taxonomy.py
    src/block_4/problem_scoring.py
    src/block_4/problem_prioritization.py
    src/block_4/no_trade_gate.py
    src/block_4/launchpad_cards.py
    src/block_4/diagnosis_builder.py
    src/block_4/evidence_extraction.py
    scripts/core_mvp_validation_contract.py
    tests/test_client_fit_check.py
    tests/test_block_4_problem_scoring.py
    tests/test_block_4_problem_taxonomy.py
    tests/test_diagnosis_rulebook.py

Session 08-09 explanation and Launchpad files:

    src/site_explanation_bundle.py
    src/ai_commentary_context.py
    src/block_4/launchpad_cards.py
    tests/test_site_explanation_guardrails.py
    tests/test_ai_commentary_context.py
    tests/test_block_4_launchpad_cards.py
    docs/specs/site_explanation_bundle_spec.md

Session 09A stabilization files:

    AGENTS.md
    SPEC.md
    OUTPUTS.md
    docs/contracts/PRODUCT_FLOW_CONTRACT.md
    docs/contracts/SCREEN_CONTRACTS.md
    docs/contracts/ARTIFACT_TO_SCREEN_MAP.md
    docs/contracts/FASTAPI_SCREEN_MAPPING.json
    docs/runtime_artifact_contract.md
    docs/exec_plans/2026-06-12_client_fit_v1_foundation_plan.md

Session 12-14 Verdict/API/Supabase files:

    src/decision_verdict.py
    src/api/models.py
    src/api/reviews.py
    frontend/lib/generated/api-types.ts
    frontend/lib/reviewState.tsx
    frontend/lib/server/fastapiBridge.ts
    frontend/lib/supabase/persistence.tsx
    scripts/run_blocks_5_to_9_vertical_flow.py
    scripts/run_review_from_payload.py
    src/candidate_comparison.py
    tests/test_decision_verdict_client_fit.py
    tests/test_fastapi_app.py
    tests/test_supabase_client_fit_compact_storage.py
    docs/specs/decision_verdict_spec.md
    docs/contracts/FASTAPI_V1_API_CONTRACT.md
    docs/contracts/FASTAPI_SCREEN_MAPPING.json
    docs/supabase/README.md

Session 15-16 frontend route and Client Fit UI files:

    frontend/app/client-profile/page.tsx
    frontend/app/client-fit/page.tsx
    frontend/app/page.tsx
    frontend/app/auth/callback/route.ts
    frontend/app/evidence/page.tsx
    frontend/app/hypothesis/page.tsx
    frontend/app/portfolio-input/page.tsx
    frontend/components/portfolio/PortfolioInputTable.tsx
    frontend/lib/journey.ts
    frontend/lib/reviewState.tsx
    frontend/lib/server/fastapiBridge.ts
    frontend/tests/api-route-tests.cjs
    frontend/tests/frontend-smoke-tests.cjs
    frontend/README.md
    docs/contracts/SCREEN_CONTRACTS.md
    docs/contracts/ARTIFACT_TO_SCREEN_MAP.md
    docs/contracts/FASTAPI_SCREEN_MAPPING.json
    docs/contracts/PRODUCT_FLOW_CONTRACT.md
    docs/runtime_artifact_contract.md
    docs/specs/frontend_screen_contracts.md
    SPEC.md

Session 17 frontend downstream UI files:

    frontend/components/client-fit/ClientFitContextCard.tsx
    frontend/app/hypothesis/page.tsx
    frontend/app/comparison/page.tsx
    frontend/app/verdict/page.tsx
    frontend/tests/api-route-tests.cjs
    docs/contracts/SCREEN_CONTRACTS.md
    docs/contracts/ARTIFACT_TO_SCREEN_MAP.md
    docs/contracts/FASTAPI_SCREEN_MAPPING.json
    docs/specs/frontend_screen_contracts.md

Session 18 backend fixture matrix files:

    tests/test_client_fit_v1_matrix.py
    tests/test_client_fit_check.py
    tests/test_decision_verdict_client_fit.py

Session 10-11 Builder and Current-vs-Candidate files:

    src/portfolio_alternatives_builder.py
    src/current_vs_candidate.py
    src/candidate_comparison.py
    src/block_4/diagnosis_builder.py
    scripts/run_review_from_payload.py
    scripts/run_blocks_5_to_9_vertical_flow.py
    tests/test_block_6_launchpad_to_builder_prefill.py
    tests/test_block_6_candidate_setup_contract.py
    tests/test_current_vs_candidate_comparison_contract.py
    docs/specs/portfolio_alternatives_builder_spec.md
    docs/specs/builder_prefill_spec.md
    docs/specs/candidate_setup_spec.md
    docs/specs/current_vs_candidate_spec.md

Session 08-09 site/report and Launchpad files:

    src/site_explanation_bundle.py
    src/ai_commentary_context.py
    src/block_4/launchpad_cards.py
    src/product_bundle_paths.py
    src/candidate_comparison.py
    run_report.py
    scripts/run_review_from_payload.py
    tests/test_site_explanation_guardrails.py
    tests/test_ai_commentary_context.py
    tests/test_block_4_launchpad_cards.py
    docs/specs/site_explanation_bundle_spec.md
    docs/specs/ai_commentary_grounding_spec.md
    docs/specs/reporting_outputs_spec.md
    docs/specs/block_4_diagnosis_v3_spec.md
    docs/specs/candidate_launchpad_spec.md

## Interfaces and Dependencies

Client Fit V1 will introduce these stable concepts:

    client_fit_status = fit | watch | breach | conflict | not_provided | evidence_insufficient
    diagnostic_quality_status = clean | watch | issue | material_issue | evidence_insufficient
    decision_action = keep_current | monitor | review_diversification | test_candidate |
      revise_objectives | rebalance_review | test_another_candidate | evidence_insufficient

The future artifact path is:

    analysis_subject/client_fit_check.json

The FastAPI request accepts an optional backend-compatible `client_fit` object. The active frontend
route chain includes `/client-profile` before `/portfolio-input` and `/client-fit` between
`/evidence` and `/hypothesis`.

The active frontend route responsibilities are fixed by this plan:

    /client-profile  -> who is this for?
    /portfolio-input -> what do you own?
    /diagnosis       -> what does the portfolio look like?
    /evidence        -> how does it behave under stress?
    /client-fit      -> does this risk fit the provided profile?
    /hypothesis      -> what should we test?
    /comparison      -> did the candidate improve the diagnosis and fit?
    /verdict         -> what is the non-binding decision-support action?
    /report          -> what evidence supports the story?

Downstream sessions must maintain these enforcement interfaces:

    client_fit_context must be contextual evidence, not the primary diagnosis container.
    diagnostic_quality_status must be computed independently from client_fit_status.
    decision_action must be chosen from combined evidence, not from client_fit_status alone.
    client_fit_check summaries exposed to API/frontend must be bounded display models.
    Supabase Client Fit persistence must store compact profile/check summaries only.
    Client Fit target fields must remain display/test criteria unless an optimizer-specific spec
    explicitly promotes them.
    Session 10+ code must preserve the decision matrix above and must not derive no-trade,
    keep-current, rebalance review, or evidence-insufficient from client_fit_status alone.

Revision note 2026-06-12: Initial Client Fit V1 ExecPlan created after Session 00 and updated for
Session 01 documentation-only completion.
Revision note 2026-06-12: Session 02 marked complete after adding read-only presets/questionnaire
configuration, validators, focused tests, and preserving legacy profile defaults.
Revision note 2026-06-12: Session 03 marked complete after adding the optional Client Fit V1
FastAPI/input contract, run-local preservation, generated API types, docs sync, and focused tests.
Revision note 2026-06-12: Sessions 06 onward were strengthened with mandatory enforcement gates for
known Client Fit semantic risks: diagnosis/fit separation, no universal Client Fit diagnosis,
fit-pass-not-enough-for-no-trade, no advice/suitability language, legacy compatibility, API/frontend
/Supabase synchronization, and compact-only persistence.
Revision note 2026-06-12: Sessions 06 and 07 marked complete after adding governed Client Fit
evidence to Block 4, adding the `goal_risk_conflict` objective-review outcome, exposing separate
Client Fit and diagnostic-quality interpretation fields, and recording focused enforcement tests.
Revision note 2026-06-12: Added explicit UI/UX Blueprint Enforcement for the Client Fit web journey,
including route responsibilities, Client Fit screen sections, status color semantics, required copy
pattern, and screen-contract synchronization requirements for frontend sessions.
Revision note 2026-06-12: Simplified Client Fit semantic status colors to three primary colors:
green, amber, and red. Gray is layout-only and blue is interaction-only, not status semantics.
Revision note 2026-06-12: Sessions 08 and 09 are treated as completed for the active planning
baseline, and Session 09A was added as a hard stabilization checkpoint before Builder/Comparison/
Verdict/API/UI/Supabase work. The plan now includes source-of-truth reconciliation, a downstream
decision matrix, the no-hidden-optimizer-mandate boundary, bounded display-model requirements, and
required verification commands for the checkpoint.
Revision note 2026-06-12: Sessions 08 and 09 marked complete after adding safe Client Fit
site/report hierarchy copy, extending forbidden-copy tests, wiring Client Fit context into
Launchpad cards, and proving that Client Fit pass plus material diagnosis still routes to a
review/test path.
Revision note 2026-06-12: Sessions 09A, 10, and 11 marked complete after source-of-truth synchronization, Builder Client Fit target criteria wiring, Current vs Candidate target-reference rows, focused enforcement tests, docs verification, FastAPI governance, guardrail searches, and diff check.

Revision note 2026-06-12: Sessions 12, 13, and 14 marked complete after Client Fit-aware Decision Verdict rules, bounded FastAPI display models and generated TypeScript types, compact-only Supabase persistence/recovery, focused enforcement tests, docs verification, FastAPI governance, frontend typecheck, and compact-storage audit.

Revision note 2026-06-12: Sessions 15 and 16 marked complete after adding `/client-profile`
onboarding, profile-required web diagnosis gating, `/client-fit` UI with the four required
sections, Client Fit forwarding through the Next.js FastAPI bridge, route/screen/artifact contract
promotion, focused frontend API/smoke/type checks, docs verification, FastAPI governance, and
frontend forbidden-copy guardrail search.

Revision note 2026-06-12: Sessions 17 and 18 marked complete after adding downstream Client Fit UI context cards, frontend static/type enforcement, and backend fixture-matrix anti-regression tests for Client Fit interpretation and decision-boundary cases.


Revision note 2026-06-12: Sessions 19 and 20 marked complete after vertical API lineage QA, Browser/Playwright screenshots for the five Client Fit states, safe Client Fit diagnosis-envelope fallback, non-candidate conflict QA handling, safe-error user-action fix, and no-advice rendered-copy checks.

Revision note 2026-06-12: Session 21 marked complete after documentation synchronization, stale-reference audit, final acceptance audit, focused Client Fit/backend/frontend contract verification, and recording the full backend-suite caveat.
