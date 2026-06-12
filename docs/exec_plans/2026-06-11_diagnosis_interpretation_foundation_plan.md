# Dynamic Diagnosis Interpretation Foundation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is self-contained for a new
contributor who has only the current working tree and this file.

## Purpose / Big Picture

Portfolio MRI already calculates Portfolio X-Ray, Stress Lab, Problem Classification, Launchpad,
candidate, comparison, verdict, and site explanation artifacts. The next product need is to make the
interpretation layer professional, dynamic, and auditable for many different user portfolios. After
this plan is complete, each submitted portfolio should produce a clear deterministic evidence chain:
metrics become evidence signals, evidence signals become a root-cause diagnosis, the diagnosis
becomes a testable hypothesis, and the website receives a display-ready explanation package without
using an LLM or inventing unsupported claims.

This plan is intentionally aligned with the ongoing FastAPI migration in
`docs/exec_plans/2026-06-11_fastapi_foundation_plan.md`. FastAPI remains the route to typed HTTP
contracts and the frontend remains a display surface. The diagnosis engine, rulebook, explanation
bundle, FastAPI envelopes, frontend adapters, and Browser/Playwright QA must converge on the same
source-backed product story.

## Progress

- [x] (2026-06-11) Session 00 created this ExecPlan and the read-only baseline audit at
  `docs/audits/2026-06-11_diagnosis_interpretation_session00_audit.md`. No formulas, portfolio
  calculations, runtime behavior, FastAPI route behavior, frontend behavior, or generated review
  artifacts were changed.
- [x] (2026-06-11) Session 01 created the professional methodology baseline spec at
  `docs/specs/diagnosis_interpretation_methodology_spec.md`, linked it from `docs/specs/README.md`
  and `SPEC.md`, and kept the change documentation-only: no formulas, thresholds, runtime behavior,
  generated artifacts, FastAPI behavior, or frontend behavior changed.
- [x] (2026-06-11) Session 02 defined the planned diagnosis rulebook contract and YAML schema at
  `docs/specs/diagnosis_rulebook_schema_spec.md`, linked it from `docs/specs/README.md`,
  `SPEC.md`, and the methodology spec, and kept the change documentation-only: no runtime behavior,
  formulas, thresholds, generated artifacts, FastAPI behavior, or frontend behavior changed.
- [x] (2026-06-11) Session 03 added `config/diagnosis_rulebook.yml`, the read-only
  loader/validator at `src/block_4/diagnosis_rulebook.py`, and parity tests in
  `tests/test_diagnosis_rulebook.py` against the current Block 4 taxonomy, action paths,
  root-cause elevation rules, and threshold references. The YAML remains `status: parity` and does
  not replace runtime Block 4 registries, scoring, prioritization, generated artifacts, FastAPI
  behavior, or frontend behavior.
- [x] (2026-06-11) Session 04 added deterministic additive interpretation-chain fields to
  `problem_classification_v3`: `interpretation_chain`, `diagnosis_evidence_items`,
  `root_cause_narrative`, `metric_to_diagnosis_trace`, and `professional_rationale_refs`.
  The fields are built from current Block 4 evidence, scoring, prioritization, and taxonomy output;
  they do not change diagnosis scoring, primary selection, thresholds, Launchpad behavior,
  generated-output refresh policy, FastAPI behavior, or frontend behavior.
- [x] (2026-06-11) Session 05 hardened root-cause-over-symptom prioritization and rejected-diagnosis
  explanations. A root-cause row now needs enough support before it can outrank symptoms (activated
  plus at least medium confidence or medium materiality), and activated symptoms rejected under a
  selected root cause receive a specific `symptom_supports_selected_root_cause` explanation instead
  of a generic lower-priority note. The change does not alter evidence extraction, scoring,
  threshold values, Launchpad behavior, generated-output refresh policy, FastAPI behavior, or
  frontend behavior.
- [x] (2026-06-11) Session 06 upgraded confidence and data-quality gates. Product-level X-Ray
  blocks with `partial` or `unavailable` status now emit `partial_sections`, actionable diagnoses
  stay confidence-capped under partial evidence, and `evidence_insufficient_data_quality` activates
  when partial X-Ray evidence is paired with unavailable Stress Lab evidence. Partial X-Ray evidence
  alone lowers confidence and marks the diagnosis artifact partial, but does not suppress Launchpad
  when Stress Lab still confirms a material primary diagnosis. The change does not alter numeric
  thresholds, generated-output refresh policy, FastAPI behavior, or frontend behavior.
- [x] (2026-06-11) Session 07 made `site_explanation_bundle.json` prefer the Block 4
  interpretation chain for diagnosis-screen copy. Diagnosis executive copy now uses
  `root_cause_narrative.statement_en` when available; evidence copy uses
  `root_cause_narrative.portfolio_manager_interpretation_en` and `diagnosis_evidence_items`; and
  technical copy exposes the root-cause boundary, metric-to-diagnosis trace count, and
  `interpretation_chain.next_step_link`. Legacy primary-diagnosis and X-Ray weakness-map fallbacks
  remain in place. The change does not alter Block 4 scoring, prioritization, thresholds,
  generated-output refresh policy, FastAPI behavior, or frontend behavior.
- [x] (2026-06-11) Session 08 expanded the FastAPI diagnosis display envelope and regenerated
  frontend API types. `DiagnosisSummary` now exposes bounded typed interpretation-chain display
  fields for evidence items, root-cause narrative, metric trace, rejected alternatives,
  professional rationale references, source artifacts, diagnosis role, and recommendation boundary
  when `problem_classification_v3.interpretation_chain` is present, while preserving the compact
  legacy fallback fields for older or partial artifacts. The change does not alter Block 4 scoring,
  prioritization, thresholds, generated review artifact schemas, Next.js route handlers, frontend
  screen behavior, portfolio calculations, root `config.yml`, or PDF behavior.
- [x] (2026-06-11) Session 09 aligned FastAPI comparison, verdict, and report responses with
  the evidence chain. `ComparisonData`, `VerdictData`, and `ReportData` now expose bounded
  `evidence_chain_context` display fields tying downstream stages back to selected diagnosis,
  tested hypothesis, success criteria, trade-off, candidate boundary, recommendation boundary, and
  source artifact roles. Verdict summaries also expose bounded `evidence_used` and
  `what_would_change_verdict` lists. Frontend OpenAPI types and screen-mapping governance were
  regenerated/updated. The change does not alter portfolio calculations, Block 4 scoring,
  prioritization, thresholds, generated review artifact schemas, Next.js route handlers, frontend
  screen behavior, root `config.yml`, or PDF behavior.
- [x] (2026-06-11) Session 10 refactored frontend display adapters to prefer FastAPI public
  display envelopes over raw same-run artifacts. `frontend/lib/reviewState.tsx` now builds
  diagnosis, candidate, comparison, and verdict summaries from `fastapi_envelope.data` fields first,
  including `DiagnosisSummary`, candidate/hypothesis summaries, downstream `evidence_chain_context`,
  verdict `evidence_used`, and `what_would_change_verdict`, with raw artifact parsing retained only
  as compatibility fallback. `frontend/lib/server/fastapiBridge.ts` report display mapping now also
  uses `ReportData.evidence_chain_context`. The change does not alter FastAPI schemas, portfolio
  calculations, generated review artifact schemas, Next.js route URLs, root `config.yml`, PDFs, or
  browser QA state.
- [x] (2026-06-11) Session 11 added a dynamic portfolio fixture matrix over the existing ten
  deterministic Block 4 archetypes. `tests/test_diagnosis_interpretation_fixture_matrix.py` now
  verifies that distinct source evidence produces distinct selected diagnoses, root-cause
  narratives, leading evidence signals, source-backed interpretation traces, and FastAPI diagnosis
  summaries, while `tests/test_block_4_v2_archetype_fixtures.py` continues to verify primary
  diagnosis, Launchpad outcome, contract validators, and suppressed/allowed launch behavior. The
  change does not alter Block 4 scoring, prioritization, thresholds, generated review artifact
  schemas, FastAPI schemas, frontend behavior, root `config.yml`, PDFs, or browser QA state.
- [x] (2026-06-12) Session 12 hardened active-review isolation and 100-user readiness. The
  frontend FastAPI bridge now rejects recovery, Builder, Candidate, Comparison, Verdict, and Report
  responses whose public envelope lineage does not match the active frontend `reviewId`,
  selected-card, candidate, comparison, or verdict before trusting downstream run-local artifacts.
  `frontend/tests/api-route-tests.cjs` covers cross-review candidate lineage rejection, and
  `tests/test_frontend_review_bridge.py` now proves 100 unique frontend review run directories are
  created without collision. The change does not alter portfolio calculations, Block 4 scoring,
  FastAPI schemas, generated review artifact schemas, frontend route URLs, root `config.yml`, PDFs,
  or browser state.
- [x] (2026-06-12) Session 13 added governance validation for sourced claims and
  anti-hallucination boundaries. The FastAPI contract governance script now verifies that public
  claim-carrying schemas keep source/provenance companions, that screen-mapping notes preserve
  recommendation/evidence boundaries, and that governed frontend/API copy does not introduce
  unqualified advice-like language. Focused tests cover missing provenance fields, missing mapping
  boundary notes, and unsafe best-portfolio phrasing. The change does not alter portfolio
  calculations, Block 4 scoring, FastAPI schemas, generated review artifact schemas, frontend route
  URLs, root `config.yml`, PDFs, or browser state.
- [x] (2026-06-12) Session 14 hardened Browser/Playwright vertical QA with a defensive
  live helper at `scripts/qa_browser_vertical.cjs`, a frontend `qa:vertical` script, and QA
  documentation. The helper starts fresh FastAPI and Next.js servers on free ports, uses a clean
  Playwright context, clears browser state per scenario, checks server readiness and Next compile
  diagnostics, captures screenshots or DOM/text fallbacks, verifies same-run lineage through
  frontend compatibility routes, and probes stale selected-card rejection. The change does not alter
  portfolio calculations, Block 4 scoring, FastAPI schemas, generated review artifact schemas,
  frontend route URLs, root `config.yml`, PDFs, or product copy.
- [x] (2026-06-12) Session 15 completed live FastAPI plus frontend vertical QA across three
  portfolio scenarios after hardening empty-cache handling and Browser navigation retries. The
  accepted run at `output/playwright/vertical-qa-2026-06-12T08-12-35-071Z/qa-report.json` proved
  fresh FastAPI and Next.js readiness, clean browser state, full frontend compatibility route flow
  from diagnosis through report, deterministic source-artifact evidence, stale selected-card
  rejection with HTTP 409, and distinct diagnosis summaries across the scenario matrix
  (`mixed_evidence_no_action` and `weak_crisis_resilience`).
- [x] (2026-06-12) Session 16 synchronized documentation and closed the plan. The plan
  register, changelog, and closure audit now record the accepted live QA evidence and final
  deterministic evidence-chain boundary; no portfolio calculations, generated review artifact
  schemas, FastAPI schemas, frontend route behavior, root `config.yml`, PDFs, or generated output
  refresh were changed.

## Surprises & Discoveries

- Observation: The repository already has the core ingredients of the requested dynamic framework,
  but they are distributed across several layers.
  Evidence: `src/block_4/problem_taxonomy.py`, `src/block_4/evidence_extraction.py`,
  `src/block_4/problem_scoring.py`, `src/block_4/problem_prioritization.py`,
  `src/block_4/diagnosis_builder.py`, `src/site_explanation_bundle.py`, and `src/api/models.py`
  already contain taxonomy, evidence extraction, scoring, diagnosis output, site copy hierarchy, and
  FastAPI display models.

- Observation: The current workspace already contains active FastAPI migration changes and a current
  FastAPI ExecPlan, so this plan must avoid re-owning the migration sequence.
  Evidence: `docs/exec_plans/2026-06-11_fastapi_foundation_plan.md` exists in the working tree and
  describes completed FastAPI foundation sessions, while `src/api/` and `tests/test_fastapi_app.py`
  are present as untracked or modified working-tree files.

- Observation: Browser QA stability is a product risk, not just a testing convenience.
  Evidence: `AGENTS.md`, `docs/contracts/SCREEN_CONTRACTS.md`, and the site explanation plan all
  mention stale browser state, stale generated artifacts, screenshot timeouts, and route-lineage
  verification as recurring visual QA risks.

- Observation: A research note for Session 01 already existed in the working tree and usefully
  separated professional source review from the canonical spec.
  Evidence: `docs/audits/2026-06-11_diagnosis_interpretation_framework_research.md` is an untracked
  research/audit artifact, while Session 01 promoted the durable methodology contract into
  `docs/specs/diagnosis_interpretation_methodology_spec.md`.

- Observation: The future rulebook needs to mirror two current sources, not one.
  Evidence: `src/block_4/problem_taxonomy.py` owns problem/action-path narrative metadata and
  root-cause elevation hints, while `config/block_4_thresholds.yml` owns numeric activation,
  scoring, materiality, severity, and confidence settings. Session 02 therefore specified
  threshold references instead of duplicating numeric values in the planned YAML.

- Observation: Some parity fields are intentionally copied from the existing Python taxonomy even
  when they are narrative strings rather than formulas.
  Evidence: Session 03 tests compare Launchpad titles, test copy, tradeoff copy, skip rules,
  do-not-overreact notes, false-positive notes, false-negative notes, and downstream comparison
  focus exactly between `config/diagnosis_rulebook.yml` and `src/block_4/problem_taxonomy.py`.

- Observation: The Session 03 validator can prove governance and parity without participating in
  the diagnosis runtime path.
  Evidence: `tests/test_diagnosis_rulebook.py::test_rulebook_validation_does_not_mutate_python_registries`
  snapshots the Python registries before validation and confirms they are unchanged afterward.

- Observation: Before Session 05, activated symptoms rejected after a root-cause primary could fall
  back to generic lower-priority wording when no explicit elevation rule was applied.
  Evidence: `src/block_4/problem_prioritization.py` filtered symptom rows out of secondary slots
  under a root-cause primary, but `_resolve_reject_reason` only had a specific root-cause explanation
  for explicit `ROOT_CAUSE_ELEVATION_RULES` demotions.

- Observation: Before Session 06, Core MVP product blocks with `partial` or `unavailable` status did
  not emit `partial_sections` unless legacy `sections.*` entries were also partial.
  Evidence: `src/block_4/evidence_extraction.py::_extract_data_quality` built `product_partial` but
  only emitted the `partial_sections` signal inside `if partial:`, so product-block quality limits
  could fail to cap confidence or combine with missing stress evidence.

- Observation: Before Session 07, the site explanation diagnosis screen still used
  `primary_diagnosis`, `why_this_matters`, and `key_evidence` first even when Session 04
  interpretation-chain fields were present.
  Evidence: `src/site_explanation_bundle.py::_append_diagnosis_copy_rules` read
  `problem_classification.primary_diagnosis` and `primary_diagnosis.key_evidence` directly, so the
  new root-cause narrative and metric-to-diagnosis trace were not the preferred site-facing source.

- Observation: Before Session 08, the FastAPI diagnosis envelope already had a compact
  `DiagnosisSummary`, but it did not expose the Session 04 interpretation-chain fields.
  Evidence: `src/api/models.py::DiagnosisSummary` contained only `primary_diagnosis`, `headline`,
  `confidence`, `evidence_chain`, and `next_diagnostic_step`, while
  `src/api/reviews.py::_diagnosis_summary` read `primary_diagnosis.key_evidence` before the new
  root-cause narrative, metric trace, rejected alternatives, or rationale refs.


- Observation: Before Session 09, downstream FastAPI envelopes exposed comparison/verdict/report
  stage summaries but did not carry an explicit bounded context tying those stages back to the
  selected diagnosis and hypothesis.
  Evidence: `src/api/models.py::ComparisonData`, `VerdictData`, and `ReportData` lacked a shared
  diagnosis-to-hypothesis display field, while `src/api/reviews.py::_comparison_data`,
  `_verdict_data`, and `_report_data` mapped only stage-local summary fields.

- Observation: Before Session 10, the normal frontend screens already avoided direct page-level raw
  artifact parsing, but the central state adapters still derived diagnosis, candidate, comparison,
  and verdict summaries primarily from raw `review_result.outputs.*` or stage artifact payloads.
  Evidence: `frontend/lib/reviewState.tsx::buildDiagnosisFromRealResult`,
  `recordCandidateGeneration`, `recordComparisonResult`, and `recordVerdictResult` read
  `portfolio_xray`, `stress_report`, `candidate_generation`, `current_vs_candidate`, and
  `decision_verdict` before the FastAPI display envelope fields added in Sessions 08-09.

- Observation: The repository already had ten compact Block 4 archetype fixtures from earlier
  diagnosis work, so Session 11 could reuse them instead of creating new generated review outputs.
  Evidence: `tests/block_4_fixtures.py` and
  `tests/fixtures/block_4/archetype_manifest.json` already define concentrated equity, balanced,
  duration-heavy, credit-carry, pseudo-diversified, cash-heavy, weak-hedge, insufficient-data,
  conflicting-signal, and acceptable/no-action cases; the new Session 11 matrix adds interpretation
  chain and FastAPI summary assertions on top of those fixtures.

- Observation: The backend and frontend already had strong run-local file-path and selected-card
  guards, but the frontend compatibility proxy did not independently reject a successful FastAPI
  envelope if that envelope reported a different review lineage.
  Evidence: Session 12 added `fastApiLineageErrors` / `fastApiLineageMismatchResponse` in
  `frontend/lib/server/fastapiBridge.ts` and a regression test proving a candidate-stage response
  for `frontend_review_user_b` is rejected before reading `frontend_review_user_a` downstream
  candidate artifacts.

- Observation: Session 14 proved screenshot capture itself can be a flaky QA dependency and should
  not be the only visual evidence path.
  Evidence: The first live Playwright run failed on `Page.captureScreenshot`;
  `scripts/qa_browser_vertical.cjs` now treats screenshot failure as non-fatal and writes HTML/text
  DOM fallbacks under `output/playwright/`.

- Observation: Session 15 initially exposed two live-QA reliability gaps before passing: transient empty yfinance
  responses could poison daily/monthly cache metadata, and Playwright route navigation could abort
  during first compile.
  Evidence: `src/data_loader.py` now avoids saving empty daily/monthly cache metadata,
  `scripts/qa_browser_vertical.cjs` retries diagnosis and route navigation, and
  `output/playwright/vertical-qa-2026-06-12T08-12-35-071Z/qa-report.json` records the accepted
  three-scenario run.

- Observation: Session 16 did not need another live portfolio run because the acceptance proof was
  already captured by Session 15 and the remaining work was documentation closure.
  Evidence: The accepted QA report remained
  `output/playwright/vertical-qa-2026-06-12T08-12-35-071Z/qa-report.json`; Session 16 updated
  documentation pointers and ran documentation/diff checks instead of refreshing generated outputs.

## Decision Log

- Decision: Session 00 is planning and audit only.
  Rationale: The requested work spans diagnosis methodology, rulebook configuration, generated
  artifacts, FastAPI contracts, frontend adapters, QA infrastructure, and documentation. The project
  rules require a checked-in ExecPlan and source-of-truth audit before broad implementation.
  Date/Author: 2026-06-11 / Codex.

- Decision: This plan extends, rather than replaces, the active FastAPI foundation plan.
  Rationale: FastAPI is the HTTP/API migration path. This plan owns the interpretation foundation
  that FastAPI and frontend will expose. Keeping those responsibilities separate avoids conflicting
  sessions and reduces risk.
  Date/Author: 2026-06-11 / Codex.

- Decision: The first implementation phase will be deterministic and LLM-free.
  Rationale: The user explicitly selected maximum stability and no hallucinations. AI may be added
  later only as a bounded editor over deterministic evidence, not as a diagnosis source.
  Date/Author: 2026-06-11 / Codex.

- Decision: User-facing site copy remains English-first for this phase.
  Rationale: Current frontend copy, specs, tests, and site explanation rules are English-first.
  Maintaining that default minimizes churn while the foundation is hardened.
  Date/Author: 2026-06-11 / Codex.

- Decision: The Session 01 methodology baseline is a spec, not code and not a threshold registry.
  Rationale: The next implementation sessions need a stable professional interpretation method, but
  changing formulas, thresholds, API fields, or generated artifacts before a rulebook parity check
  would make behavior drift hard to audit.
  Date/Author: 2026-06-11 / Codex.

- Decision: Contrary evidence and rejected alternatives are required methodology concepts for the
  future rulebook.
  Rationale: A professional diagnosis must explain why the selected root cause beat plausible
  alternatives, especially when symptoms such as high volatility or drawdown can have multiple
  causes.
  Date/Author: 2026-06-11 / Codex.

- Decision: The diagnosis rulebook YAML will be interpretation metadata first and threshold-free.
  Rationale: Duplicating numeric activation or scoring constants in a human-readable rulebook would
  create a second formula source and make parity hard to prove. The YAML should reference
  `config/block_4_thresholds.yml` keys by symbolic path while mirroring the current Python taxonomy
  before behavior changes are allowed.
  Date/Author: 2026-06-11 / Codex.

- Decision: Keep the Session 03 rulebook loader read-only and test-facing.
  Rationale: The session goal is parity evidence, not behavior migration. Importing the YAML into
  Problem Classification, scoring, prioritization, Launchpad generation, site explanation, FastAPI,
  or frontend adapters would make behavior drift possible before Sessions 04-10 add additive fields
  and display contracts.
  Date/Author: 2026-06-11 / Codex.

- Decision: Root-cause-over-symptom priority requires enough support, not just the `root_cause`
  taxonomy role.
  Rationale: The methodology says root causes should outrank symptoms when they explain the evidence
  with enough confidence and materiality. Promoting a low-confidence and low-materiality structural
  label over a stronger symptom would make the diagnosis less professional and less auditable.
  Date/Author: 2026-06-11 / Codex.

- Decision: Partial X-Ray evidence plus unavailable Stress Lab evidence is a data-quality blocker,
  while partial X-Ray evidence alone is a confidence cap.
  Rationale: Missing stress coverage removes the main confirmation layer for diagnosis, so candidate
  testing should wait. A single partial X-Ray block with otherwise usable stress evidence should not
  erase the diagnosis; it should make the confidence cautious and visible.
  Date/Author: 2026-06-11 / Codex.

- Decision: Site diagnosis copy should prefer the additive interpretation chain but keep legacy
  fallbacks.
  Rationale: Session 07 is an exposure-layer change, not a Block 4 behavior migration. Using the
  chain gives the site a more professional evidence story, while fallback behavior preserves
  compatibility for older or partial artifacts.
  Date/Author: 2026-06-11 / Codex.

- Decision: FastAPI should expose the interpretation chain as bounded diagnosis display fields, not
  as a raw `problem_classification.json` artifact dump.
  Rationale: Session 08 is an API display-contract change. The frontend needs typed, generated
  fields for evidence items, root-cause narrative, metric trace, rejected alternatives, and rationale
  references, but public envelopes must still avoid raw artifact trees and preserve legacy compact
  fallbacks for older generated runs.
  Date/Author: 2026-06-11 / Codex.


- Decision: Use one bounded `evidence_chain_context` model for comparison, verdict, and report
  responses instead of exposing raw `candidate_generation.json`, `current_vs_candidate.json`,
  `decision_verdict.json`, or `ai_commentary_context.json` trees.
  Rationale: The frontend needs the diagnosis-to-hypothesis chain for display and auditability, but
  raw artifacts would leak backend schema details and make screens parse implementation internals.
  A small shared display context keeps the chain visible without adding calculations or advice.
  Date/Author: 2026-06-11 / Codex.

- Decision: In Session 10, keep same-run raw artifact parsing as a compatibility fallback inside
  adapters rather than deleting it outright.
  Rationale: FastAPI public envelopes now contain the professional diagnosis and downstream context,
  but they do not yet expose every detailed comparison metric table used by the current comparison
  screen. Prefer public display fields for meaning and gates, while retaining raw same-run details
  only for fields not yet represented publicly.
  Date/Author: 2026-06-11 / Codex.

- Decision: Session 11 should reuse compact deterministic Block 4 archetype fixtures rather than
  running portfolio-review commands or writing new generated outputs.
  Rationale: The goal is to prove dynamic interpretation behavior across different evidence
  patterns, not to refresh run-local artifacts. Reusing fixture dictionaries keeps the test fast,
  source-backed, and isolated from network data, caches, stale review folders, PDFs, and browser
  state.
  Date/Author: 2026-06-11 / Codex.

- Decision: Session 12 hardening belongs at the frontend FastAPI bridge boundary as an additive
  public-envelope guard, not as a schema or portfolio-calculation change.
  Rationale: The risk is cross-user or stale active-review acceptance under compatibility proxy
  routes. Checking returned `lineage` against the active request before reading downstream artifacts
  prevents stale unlocks without changing FastAPI response models, generated artifact schemas, or
  portfolio math.
  Date/Author: 2026-06-12 / Codex.

- Decision: Browser/Playwright live QA should have a checked-in defensive helper rather than
  depend on ad hoc browser observations.
  Rationale: The recurring risks are stale servers, stale browser storage, stale run-local artifacts,
  stale element references, and weak diagnostics. A single helper can start fresh servers, clear
  state, verify lineage, save logs, and classify screenshot or data-provider failures consistently.
  Date/Author: 2026-06-12 / Codex.

- Decision: Session 15 acceptance requires a green multi-scenario QA report, not merely successful server
  startup or one completed review.
  Rationale: The full-plan acceptance requires completed live review chains with distinct
  source-backed explanations and stale-artifact rejection evidence. The accepted 2026-06-12 run
  satisfies this with three completed scenarios and per-scenario source artifacts.
  Date/Author: 2026-06-12 / Codex.

- Decision: Close the Diagnosis Interpretation Foundation plan after documentation synchronization
  instead of extending it into more runtime work.
  Rationale: The planned deterministic evidence-chain surfaces, FastAPI envelopes, frontend adapter
  consumption, lineage guards, governance checks, fixture matrix, and live vertical QA acceptance are
  complete. Further work belongs in the FastAPI foundation plan or future product/UI plans, not in
  this foundation plan.
  Date/Author: 2026-06-12 / Codex.

## Outcomes & Retrospective

Session 00 established the plan and audit baseline only. It did not change runtime behavior,
portfolio calculations, formula thresholds, generated artifacts, FastAPI route semantics, or frontend
screen behavior.

Session 01 established the professional methodology baseline in
`docs/specs/diagnosis_interpretation_methodology_spec.md`. The spec defines the evidence chain,
raw-metric-to-evidence-signal boundary, controlled problem-family boundary, root-cause-over-symptom
priority, contrary-evidence and rejected-alternative expectations, confidence/data-quality meaning,
hypothesis-test handoff, and downstream Decision Verdict boundary. It is documentation-only and does
not add formulas, thresholds, runtime fields, API fields, generated outputs, or frontend behavior.
Session 02 used this methodology to define the diagnosis rulebook contract and YAML schema without
changing Block 4 behavior.

Session 02 established the planned diagnosis rulebook schema in
`docs/specs/diagnosis_rulebook_schema_spec.md`. The spec defines the future
`diagnosis_rulebook.yml`-under-`config/` contract, including top-level YAML keys, action-path entries,
problem entries, required/supporting/contrary evidence references, threshold references, hypothesis
tests, success criteria, narrative templates, prioritization rules, and governance validation. It
keeps thresholds in `config/block_4_thresholds.yml`, requires Session 03 parity with the current
Python registries before behavior changes, and does not add runtime fields, generated outputs,
FastAPI fields, frontend behavior, formulas, or threshold changes.

Session 03 created the parity rulebook and validator. `config/diagnosis_rulebook.yml` mirrors the
current Block 4 problem registry, action-path registry, and root-cause elevation rules while keeping
numeric threshold values in `config/block_4_thresholds.yml`. `src/block_4/diagnosis_rulebook.py`
loads and validates the YAML as read-only parity evidence. `tests/test_diagnosis_rulebook.py` proves
schema/parity coverage and registry non-mutation. The session did not wire the YAML into runtime
diagnosis behavior, generated artifacts, FastAPI envelopes, frontend adapters, or `config.yml`.

Session 04 added the first runtime interpretation-chain surface to `problem_classification_v3`.
`src/block_4/diagnosis_builder.py` now emits `interpretation_chain` plus mirrored display-ready
top-level fields for source-backed evidence items, root-cause narrative, metric-to-diagnosis trace,
and professional rationale references. `src/block_4/problem_scoring.py` preserves raw source field
paths on evidence references when available, and `scripts/core_mvp_validation_contract.py` validates
the optional chain shape when present. This is additive explanation metadata only: the Session 03
YAML remains read-only parity evidence, and Block 4 scoring, prioritization, thresholds, Launchpad,
FastAPI, frontend adapters, and generated artifacts are not otherwise changed.

Session 05 hardened the root-cause-over-symptom handoff in `src/block_4/problem_prioritization.py`.
Root causes still outrank symptoms, but only after activation plus at least medium confidence or
medium materiality. Activated symptoms that lose to a selected root cause now receive
`symptom_supports_selected_root_cause` with the selected root-cause label, so the user can see that
the symptom is supporting evidence rather than an impossible or ignored alternative. Focused tests
cover both the support gate and the new rejected-symptom explanation.

Session 06 hardened confidence and data-quality gates in `src/block_4/evidence_extraction.py` and
`src/block_4/problem_scoring.py`, with a narrow `src/block_4/no_trade_gate.py` guard to keep
stress-confirmed material diagnoses Launchpad-eligible when the only limitation is partial X-Ray
evidence. Product-block partial/unavailable statuses now emit `partial_sections`; actionable rows
remain confidence-capped when partial evidence is present; and the data-quality outcome activates
when partial X-Ray evidence appears together with unavailable Stress Lab evidence. Focused scoring
tests cover the new blocker and the non-blocking confidence cap.

Session 07 updated the deterministic site explanation diagnosis hierarchy in
`src/site_explanation_bundle.py`. The diagnosis screen now prefers
`root_cause_narrative.statement_en`, `root_cause_narrative.portfolio_manager_interpretation_en`,
`diagnosis_evidence_items`, `metric_to_diagnosis_trace`, and `interpretation_chain.next_step_link`
when those fields are present in `problem_classification.json`. Chain evidence items can source
their material claims to the underlying deterministic artifact named by the evidence item, with
`problem_classification.json` as fallback. Legacy primary-diagnosis and X-Ray weakness-map copy
paths remain available for older artifacts.

Session 08 updated the FastAPI diagnosis display contract in `src/api/models.py` and
`src/api/reviews.py`. `DiagnosisSummary` now includes typed display fields for the selected
diagnosis role, source artifacts, diagnosis evidence items, root-cause narrative, metric-to-diagnosis
trace, rejected alternatives, professional rationale refs, and recommendation boundary. The adapter
prefers `problem_classification_v3.interpretation_chain` when present and keeps the compact legacy
fallback fields for older artifacts. `frontend/lib/generated/api-types.ts` was regenerated from the
live OpenAPI schema, and focused FastAPI tests cover the new public shape.

Session 10 moved the frontend adapter boundary forward without changing API schemas. The active
frontend state in `frontend/lib/reviewState.tsx` now prefers FastAPI public display envelopes for
diagnosis, generated candidate/hypothesis metadata, comparison context, and verdict evidence, while
falling back to same-run raw artifacts only for compatibility and detailed fields not yet public in
FastAPI. The report display adapter in `frontend/lib/server/fastapiBridge.ts` now uses
`ReportData.evidence_chain_context` for diagnosis/hypothesis/candidate boundary fallback copy,
source evidence labels, and recommendation boundary. This session did not change portfolio
calculations, generated review artifact schemas, FastAPI schemas, root config, PDFs, or browser
state.

Session 11 added a dynamic interpretation fixture matrix without changing runtime behavior. The new
test file `tests/test_diagnosis_interpretation_fixture_matrix.py` builds Block 4 diagnosis artifacts
for ten deterministic archetypes and proves that selected diagnoses, source-backed narratives,
leading signals, traces, and FastAPI diagnosis summaries vary with the input evidence. The existing
archetype end-to-end test remains the Launchpad/outcome contract gate. This session did not refresh
generated review outputs, run live portfolio review commands, change FastAPI schemas, or touch
frontend/browser state.

Session 12 hardened run-local review isolation for multi-user readiness. The frontend FastAPI bridge
now validates successful public envelopes against the active request lineage before trusting
run-local downstream artifacts, and rejects mismatched review/card/candidate/comparison/verdict
responses with a bounded 409 error. The test suite now covers both cross-review candidate response
rejection and 100 unique frontend review directory creation. This session did not change portfolio
calculations, Block 4 scoring, FastAPI schemas, generated artifact schemas, route URLs, root
`config.yml`, PDFs, or browser state.

Session 13 added contract governance for source-backed public claims and anti-advice boundaries.
`scripts/verify_fastapi_contract_governance.py` now checks that public diagnosis, comparison,
verdict, and report claim schemas keep source/provenance companions, that the screen mapping carries
recommendation-boundary notes, and that governed frontend/API copy does not introduce unqualified
advice-like language. Focused governance tests cover missing provenance, missing mapping notes, and
unsafe "best portfolio" style wording.

Session 14 added the defensive live Browser/Playwright vertical QA helper. The checked-in helper can
start fresh FastAPI and Next.js servers on free ports, use a clean Playwright context, clear browser
state per scenario, capture screenshots or DOM/text fallbacks, verify same-run lineage through the
frontend compatibility routes, and probe stale selected-card rejection. The command is documented as
`npm.cmd run qa:vertical -- --scenario-limit 3` from the frontend directory.

Session 15 completed live acceptance for the full evidence-chain foundation. The accepted report at
`output/playwright/vertical-qa-2026-06-12T08-12-35-071Z/qa-report.json` proved fresh server readiness,
clean browser state, diagnosis-through-report compatibility-route flow, deterministic source-artifact
evidence, stale selected-card rejection with HTTP 409, and distinct diagnosis summaries across the
scenario matrix.

Session 16 closed the plan as documentation synchronization only. The final handoff is that
Portfolio MRI now has a deterministic, LLM-free interpretation foundation from Block 4 evidence
signals through site/FastAPI/frontend display envelopes, with governance and live vertical QA proving
source-backed claims and stale-artifact rejection. Future implementation should treat this plan as
completed history and continue productization through the active FastAPI and frontend plans.

## Context and Orientation

Portfolio MRI is a diagnosis-first, current-portfolio-first portfolio decision-support system. The
current canonical flow is:

    Input portfolio
    -> Portfolio X-Ray
    -> Stress Test Lab
    -> Problem Classification
    -> Candidate Launchpad
    -> Portfolio Alternatives Builder
    -> Candidate Generation
    -> Current vs Candidate Comparison
    -> Decision Verdict
    -> AI Commentary / grounding
    -> Monitoring / What Changed

The phrase "evidence chain" in this plan means a structured explanation of why the system chose a
diagnosis. It starts with metrics or source fields, converts them into evidence signals, maps those
signals to candidate diagnoses, selects a root cause, records supporting symptoms and rejected
alternatives, then exposes a testable next step with success criteria. A root cause is the underlying
portfolio structure that most explains the problem. A symptom is a metric outcome such as high
volatility that may be caused by concentration, equity beta, weak crisis resilience, duration, credit,
liquidity, or data quality problems.

The most relevant files for future contributors are:

- `docs/specs/block_4_diagnosis_v3_spec.md`, which defines the current Problem Classification and
  Launchpad product contract.
- `src/block_4/problem_taxonomy.py`, which holds the current diagnosis and action-path registry.
- `src/block_4/evidence_extraction.py`, which translates Portfolio X-Ray and Stress Lab artifacts
  into evidence signals.
- `src/block_4/problem_scoring.py`, which turns evidence signals into scored diagnosis candidates.
- `src/block_4/problem_prioritization.py`, which chooses the primary diagnosis and secondary
  diagnoses.
- `src/block_4/diagnosis_builder.py`, which writes `problem_classification.json`.
- `src/site_explanation_bundle.py`, which builds the deterministic site-facing explanation bundle.
- `src/api/models.py` and `src/api/reviews.py`, which define and map the local FastAPI public
  response envelopes.
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` and `docs/contracts/SCREEN_CONTRACTS.md`, which
  explain how backend artifacts reach the current frontend screens.

## Plan of Work

Session 01 will create a methodology spec that explains the evidence-to-diagnosis framework in
plain language and records the professional portfolio-management principles that justify it. That
document will be a methodology and product-boundary source, not a formula source.

Session 02 created a rulebook specification for a human-readable diagnosis rulebook. The rulebook
describes interpretation, professional rationale, false positives, hypothesis tests, and success
criteria. Numeric activation thresholds remain in `config/block_4_thresholds.yml`.

Session 02 completed this as a documentation-only schema contract at
`docs/specs/diagnosis_rulebook_schema_spec.md`. Session 03 then added the YAML file and
loader/validator against that schema, with parity tests against `src/block_4/problem_taxonomy.py`,
`src/block_4/evidence_extraction.py`, and `config/block_4_thresholds.yml`.

Session 03 added the rulebook YAML and a loader/validator that proves parity with the current
Python registry. This session did not change Block 4 behavior.

Session 04 added additive interpretation-chain fields to `problem_classification_v3`:

    src/block_4/diagnosis_builder.py
    src/block_4/problem_scoring.py
    scripts/core_mvp_validation_contract.py
    tests/test_block_4_diagnosis_builder.py
    docs/specs/block_4_diagnosis_v3_spec.md
    docs/specs/diagnosis_interpretation_methodology_spec.md
    SPEC.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 04 verification commands:

    .\.venv\Scripts\python.exe -m pytest tests\test_block_4_diagnosis_builder.py tests\test_block_4_problem_scoring.py tests\test_block_4_problem_taxonomy.py tests\test_diagnosis_rulebook.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: focused Block 4 builder/scoring/taxonomy/rulebook tests pass, documentation links
remain valid, and the diff has no whitespace errors. No portfolio review, generated-output refresh,
FastAPI server run, frontend build, or browser QA is required because the session only adds
diagnosis artifact fields and does not change HTTP/frontend display contracts yet.

Session 05 updated:

    src/block_4/problem_prioritization.py
    tests/test_block_4_problem_prioritization.py
    docs/specs/block_4_diagnosis_v3_spec.md
    docs/specs/diagnosis_interpretation_methodology_spec.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 05 verification commands:

    .\.venv\Scripts\python.exe -m pytest tests\test_block_4_problem_prioritization.py tests\test_block_4_diagnosis_builder.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_block_4_problem_scoring.py tests\test_block_4_problem_taxonomy.py tests\test_diagnosis_rulebook.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: focused prioritization and builder tests pass, adjacent scoring/taxonomy/rulebook
tests still pass, documentation links remain valid, and the diff has no whitespace errors. No
portfolio review, generated-output refresh, FastAPI server run, frontend build, or browser QA is
required because Session 05 changes only Block 4 prioritization/explanation logic and docs.

Session 06 updated:

    src/block_4/evidence_extraction.py
    src/block_4/no_trade_gate.py
    src/block_4/problem_scoring.py
    tests/test_block_4_problem_scoring.py
    tests/test_block_4_diagnosis_builder.py
    docs/specs/block_4_diagnosis_v3_spec.md
    docs/specs/diagnosis_interpretation_methodology_spec.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 06 verification commands:

    .\.venv\Scripts\python.exe -m pytest tests\test_block_4_problem_scoring.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_block_4_problem_prioritization.py tests\test_block_4_diagnosis_builder.py tests\test_diagnosis_rulebook.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: focused scoring and adjacent Block 4 tests pass, documentation links remain valid,
and the diff has no whitespace errors. No portfolio review, generated-output refresh, FastAPI
server run, frontend build, or browser QA is required because Session 06 changes only Block 4
data-quality/confidence gating and docs.

Session 07 updated:

    src/site_explanation_bundle.py
    tests/test_site_explanation_diagnosis_stress.py
    docs/specs/site_explanation_bundle_spec.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 07 verification commands:

    .\.venv\Scripts\python.exe -m pytest tests\test_site_explanation_diagnosis_stress.py tests\test_site_explanation_bundle.py tests\test_site_explanation_sources.py tests\test_site_explanation_guardrails.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: focused site-explanation diagnosis, shape, source, and guardrail tests pass,
documentation links remain valid, and the diff has no whitespace errors. No portfolio review,
generated-output refresh, FastAPI server run, frontend build, or browser QA is required because
Session 07 changes only deterministic backend copy selection and docs.

Session 08 updated:

    src/api/models.py
    src/api/reviews.py
    tests/test_fastapi_app.py
    frontend/lib/generated/api-types.ts
    docs/contracts/FASTAPI_V1_API_CONTRACT.md
    frontend/README.md
    SPEC.md
    CHANGELOG.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 08 verification commands:

    .\.venv\Scripts\python.exe scripts\generate_fastapi_api_types.py
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_fastapi_contract_governance.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: FastAPI contract governance passes, focused FastAPI tests pass, generated frontend
API types match the live OpenAPI schema, documentation links remain valid, and the diff has no
whitespace errors. No portfolio review, generated-output refresh, FastAPI server run, frontend
screen changes, frontend build, or browser QA is required because Session 08 changes only typed
FastAPI diagnosis display envelopes, generated API types, tests, and documentation.


Session 09 updated:

    src/api/models.py
    src/api/reviews.py
    tests/test_fastapi_app.py
    frontend/lib/generated/api-types.ts
    docs/contracts/FASTAPI_V1_API_CONTRACT.md
    docs/contracts/FASTAPI_SCREEN_MAPPING.json
    SPEC.md
    CHANGELOG.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 09 verification commands:

    .\.venv\Scripts\python.exe scripts\generate_fastapi_api_types.py
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_fastapi_contract_governance.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: generated frontend API types match the live OpenAPI schema, FastAPI contract
governance passes, focused FastAPI/governance tests pass, documentation links remain valid, and the
diff has no whitespace errors. No portfolio review, generated-output refresh, FastAPI server run,
Next.js route change, frontend screen change, frontend build, browser QA, root `config.yml` update, or
PDF refresh is required because Session 09 changes only typed FastAPI downstream display envelopes,
generated API types, tests, and documentation.

Session 10 updated:

    frontend/lib/reviewState.tsx
    frontend/lib/server/fastapiBridge.ts
    frontend/tests/api-route-tests.cjs
    frontend/README.md
    docs/contracts/ARTIFACT_TO_SCREEN_MAP.md
    docs/contracts/FASTAPI_V1_API_CONTRACT.md
    SPEC.md
    CHANGELOG.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 10 verification commands:

    cd frontend
    npm.cmd run typecheck
    npm.cmd run test:api
    cd ..
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: frontend TypeScript typecheck passes, compatibility API route tests pass, FastAPI
contract governance still passes, documentation links remain valid, and the diff has no whitespace
errors. No FastAPI schema regeneration, portfolio review run, generated-output refresh, FastAPI
server run, Next.js build/dev server, browser QA, root `config.yml` update, or PDF refresh is
required because Session 10 consumes existing display envelopes and does not change public FastAPI
schemas or visible route order.

Session 11 updated:

    tests/test_diagnosis_interpretation_fixture_matrix.py
    docs/specs/block_4_diagnosis_v3_spec.md
    TESTING.md
    CHANGELOG.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 11 verification commands:

    .\.venv\Scripts\python.exe -m pytest tests\test_diagnosis_interpretation_fixture_matrix.py tests\test_block_4_v2_archetype_fixtures.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: the dynamic interpretation matrix and existing archetype contract tests pass,
documentation links remain valid, and the diff has no whitespace errors. No portfolio review,
generated-output refresh, FastAPI schema regeneration, frontend build, FastAPI server run, browser
QA, root `config.yml` update, or PDF refresh is required because Session 11 adds deterministic
test coverage and documentation only.

Session 12 updated:

    frontend/lib/server/fastapiBridge.ts
    frontend/tests/api-route-tests.cjs
    tests/test_frontend_review_bridge.py
    docs/contracts/ARTIFACT_TO_SCREEN_MAP.md
    TESTING.md
    CHANGELOG.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 12 verification commands:

    cd frontend
    npm.cmd run test:api
    npm.cmd run typecheck
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: the frontend compatibility proxy rejects cross-review FastAPI lineage before
trusting downstream artifacts, frontend TypeScript still typechecks, 100 frontend review directories
are collision-free in a temp directory, documentation links remain valid, and the diff has no
whitespace errors. No portfolio review, generated-output refresh, FastAPI schema regeneration,
server run, browser QA, root `config.yml` update, or PDF refresh is required because Session 12 is a
lineage/isolation guard and focused test change.

Session 13 updated:

    scripts/verify_fastapi_contract_governance.py
    tests/test_fastapi_contract_governance.py
    docs/contracts/FASTAPI_V1_API_CONTRACT.md
    frontend/README.md
    TESTING.md
    CHANGELOG.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 13 verification commands:

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_contract_governance.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: FastAPI contract governance verifies generated types, screen mapping,
source/provenance companions, recommendation-boundary mapping notes, and advice-like language
guards; focused governance tests pass; documentation links remain valid; and the diff has no
whitespace errors. No portfolio review, generated-output refresh, FastAPI schema regeneration,
server run, browser QA, root `config.yml` update, or PDF refresh is required because Session 13 is a
governance-validator and documentation change.

Sessions 04 through 06 will add additive interpretation-chain fields, harden root-cause selection,
and standardize confidence and data-quality gates. These changes must preserve the diagnostic-only
boundary and must not turn Problem Classification into a rebalance recommendation.

Session 07 exposed the new interpretation chain through `site_explanation_bundle` diagnosis copy.
Session 08 exposed the same chain through FastAPI diagnosis response envelopes and regenerated frontend
API types. Session 09 exposed bounded evidence-chain context through downstream FastAPI comparison,
verdict, and report envelopes and regenerated frontend API types. Session 10 continued that exposure
through frontend display adapters by preferring FastAPI public display envelopes in compact screen
state. The frontend must show display-ready product meaning, not raw artifact files or raw JSON keys.


Session 09 extended the typed downstream FastAPI display envelopes. `src/api/models.py` now defines
`DownstreamEvidenceChainContext` and includes it in comparison, verdict, and report response data.
`src/api/reviews.py` builds that context from same-run candidate-generation, comparison, verdict, and
report-grounding evidence where available, and keeps safe fallback source-artifact roles when a unit
fixture is intentionally compact. Verdict summaries additionally include bounded `evidence_used` and
`what_would_change_verdict` lists. `tests/test_fastapi_app.py` covers the new downstream fields,
`frontend/lib/generated/api-types.ts` was regenerated, and `docs/contracts/FASTAPI_SCREEN_MAPPING.json`
now lists `evidence_chain_context` for the affected operations. This is a public display-contract
change only; it does not change calculations, generated review artifact schemas, frontend route
handlers, screen behavior, root config, or PDFs.


Sessions 11 through 13 will add a multi-portfolio fixture matrix, review isolation tests, and
governance validators that prevent unsupported claims and advice-like language.

Session 14 hardened Browser/Playwright QA as its own workstream. QA now starts from clean servers,
clean browser state, verified active `reviewId`, and same-run lineage, with DOM fallbacks when
screenshots fail and diagnostics that distinguish product bugs from stale state, server compile
problems, and missing data.

Sessions 15 and 16 completed live acceptance and documentation synchronization. The accepted QA
report is the evidence for full-plan acceptance; Session 16 did not refresh generated outputs.

## Concrete Steps

Work from the repository root:

    D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА

Session 00 created:

    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md
    docs/audits/2026-06-11_diagnosis_interpretation_session00_audit.md

Session 01 created and linked:

    docs/specs/diagnosis_interpretation_methodology_spec.md
    docs/specs/README.md
    SPEC.md

Session 02 created and linked:

    docs/specs/diagnosis_rulebook_schema_spec.md
    docs/specs/README.md
    docs/specs/diagnosis_interpretation_methodology_spec.md
    SPEC.md

Session 03 created and updated:

    config/diagnosis_rulebook.yml
    src/block_4/diagnosis_rulebook.py
    tests/test_diagnosis_rulebook.py
    docs/specs/diagnosis_rulebook_schema_spec.md
    docs/specs/README.md
    SPEC.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 00 verification commands:

    rg -n "problem_classification|site_explanation_bundle|DiagnosisSummary|FastAPI" docs src frontend
    git diff --check

Expected result: the search finds existing Block 4, site explanation, FastAPI, frontend contract,
and frontend adapter references. `git diff --check` exits with code 0.

Session 01 verification commands:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: documentation links are valid and the diff has no whitespace errors.

Session 02 verification commands:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: the new schema spec links are valid and the diff has no whitespace errors.

Session 03 verification commands:

    .\.venv\Scripts\python.exe -m pytest tests\test_diagnosis_rulebook.py tests\test_block_4_problem_taxonomy.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: the focused parity tests pass, documentation links remain valid, and the diff has
no whitespace errors. No portfolio review, generated-output refresh, FastAPI server run, frontend
build, or browser QA is required because the YAML is read-only parity evidence.

Session 14 updated:

    scripts/qa_browser_vertical.cjs
    frontend/package.json
    frontend/package-lock.json
    docs/contracts/QA_CONTRACT.md
    TESTING.md
    frontend/README.md
    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md

Session 14 verification commands:

    node --check scripts\qa_browser_vertical.cjs

Expected result: the Playwright QA helper has valid Node syntax and documents a repeatable
defensive live QA path.

Session 15 attempted live command:

    node scripts\qa_browser_vertical.cjs --scenario-limit 3

Accepted result: FastAPI health and Next readiness passed; three scenarios completed diagnosis,
Builder, Candidate, Comparison, Verdict, and Report; stale selected-card probes returned HTTP 409;
and the report recorded source artifacts for diagnosis, comparison, verdict, and report. The accepted
QA report is `output/playwright/vertical-qa-2026-06-12T08-12-35-071Z/qa-report.json`.

Session 16 updated:

    docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md
    docs/exec_plans/README.md
    docs/audits/2026-06-12_diagnosis_interpretation_session16_closure.md
    docs/audits/README.md
    DECISIONS.md
    CHANGELOG.md

Session 16 verification commands:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Expected result: documentation links remain valid, the ExecPlan register shows the diagnosis
interpretation plan as completed, the closure audit records the accepted QA evidence, and the diff
has no whitespace errors. No generated-output refresh or live QA rerun is required because Session
15 already passed the full live acceptance gate.

## Validation and Acceptance

Session 00 is accepted when this ExecPlan exists, the audit exists, the audit identifies the current
Block 2, Block 3, Block 4, site explanation, FastAPI, and frontend contract baseline, and the
verification commands pass without changing formulas, generated artifacts, FastAPI behavior, or
frontend behavior.

Session 01 is accepted when `docs/specs/diagnosis_interpretation_methodology_spec.md` exists, is
linked from `docs/specs/README.md` and `SPEC.md`, defines the professional evidence-to-diagnosis
methodology in project terms, preserves the current Block 4 v3 diagnosis-first boundary, and passes
documentation verification without changing runtime code, generated artifacts, FastAPI behavior, or
frontend behavior.

Session 02 is accepted when `docs/specs/diagnosis_rulebook_schema_spec.md` exists, is linked from
`docs/specs/README.md`, `SPEC.md`, and the methodology spec, defines the planned
`diagnosis_rulebook.yml`-under-`config/` contract, separates interpretation metadata from
`config/block_4_thresholds.yml` numeric thresholds, covers evidence, rationale, false positives,
hypothesis tests, success criteria, narrative templates, action paths, prioritization rules, and
governance validation, and passes documentation verification without changing runtime code,
generated artifacts, FastAPI behavior, or frontend behavior.

Session 03 is accepted when `config/diagnosis_rulebook.yml` exists with `status: parity`,
`src/block_4/diagnosis_rulebook.py` loads and validates it read-only,
`tests/test_diagnosis_rulebook.py` passes against the current Python registries and threshold source,
and no Block 4 behavior or generated artifacts change.

Session 04 is accepted when `problem_classification_v3` builder output includes
`interpretation_chain`, `diagnosis_evidence_items`, `root_cause_narrative`,
`metric_to_diagnosis_trace`, and `professional_rationale_refs`; the chain is sourced from current
Block 4 evidence/scoring/prioritization output; validators accept the optional chain shape when
present; focused Block 4 tests pass; and no scoring, prioritization, thresholds, Launchpad behavior,
FastAPI behavior, frontend behavior, or generated artifacts are changed.

Session 05 is accepted when root-cause-over-symptom priority requires an activated root cause with
at least medium confidence or medium materiality, activated symptoms rejected under a selected root
cause receive `symptom_supports_selected_root_cause`, focused and adjacent Block 4 tests pass, docs
are synchronized, and no evidence extraction, scoring, threshold values, Launchpad behavior,
FastAPI behavior, frontend behavior, or generated artifacts are changed.

Session 06 is accepted when product-block partial/unavailable statuses emit `partial_sections`,
partial X-Ray evidence caps actionable diagnosis confidence, partial X-Ray plus unavailable Stress
Lab evidence activates `evidence_insufficient_data_quality`, stress-confirmed material diagnoses
remain Launchpad-eligible when partial X-Ray is the only limitation, focused and adjacent Block 4
tests pass, docs are synchronized, and no threshold values, generated-output refresh, FastAPI
behavior, or frontend behavior are changed.

Session 07 is accepted when `site_explanation_bundle.json` diagnosis copy prefers the
interpretation chain for root-cause narrative, portfolio-manager interpretation, evidence items,
metric trace disclosure, and next-step handoff; legacy primary-diagnosis and X-Ray fallbacks remain
available; focused site-explanation tests pass; docs are synchronized; and no Block 4 scoring,
prioritization, threshold, generated-output, FastAPI, or frontend behavior changes are introduced.

Session 08 is accepted when FastAPI `DiagnosisSummary` exposes the Block 4 interpretation-chain
display fields (`diagnosis_evidence_items`, `root_cause_narrative`, `metric_to_diagnosis_trace`,
`rejected_alternatives`, `professional_rationale_refs`, source artifacts, diagnosis role, and
recommendation boundary), legacy compact fallbacks remain available, generated frontend API types
match the live OpenAPI schema, focused FastAPI/governance tests pass, docs are synchronized, and no
Block 4 scoring, prioritization, threshold, generated review artifact schema, Next.js route handler,
frontend screen behavior, portfolio calculation, root `config.yml`, or PDF behavior changes are
introduced.


Session 09 is accepted when FastAPI comparison, verdict, and report public response data expose a
bounded `evidence_chain_context` tying the selected diagnosis and hypothesis to downstream stage
results; Verdict includes bounded `evidence_used` and `what_would_change_verdict` lists; generated
frontend API types match OpenAPI; screen-mapping governance lists the new public data field for
comparison, verdict, and report; focused FastAPI/governance tests and documentation checks pass; and
no portfolio calculations, generated review artifact schemas, Next.js route handlers, frontend screen
behavior, root `config.yml`, or PDF behavior changes are introduced.

Session 10 is accepted when frontend display adapters prefer FastAPI public display envelope fields
for diagnosis, candidate/hypothesis, comparison, verdict, and report summaries; raw same-run
artifact parsing remains only as compatibility fallback for details not yet public; TypeScript
typecheck and frontend API-route tests pass; FastAPI contract governance and documentation checks
still pass; and no portfolio calculations, FastAPI schemas, generated review artifact schemas, route
URLs, root `config.yml`, PDFs, or browser state are changed.

Session 11 is accepted when the deterministic fixture matrix builds Block 4 diagnosis artifacts for
all ten archetypes, proves that different evidence patterns produce different primary diagnoses,
root-cause narratives, leading signals, and FastAPI diagnosis summaries, confirms every
interpretation-chain evidence item and trace is source-backed, keeps existing Launchpad/outcome
contract validators passing, and does not change portfolio calculations, Block 4 scoring,
prioritization, thresholds, generated review artifact schemas, FastAPI schemas, frontend behavior,
root `config.yml`, PDFs, or browser state.

Session 12 is accepted when frontend FastAPI compatibility routes reject successful FastAPI
responses whose public lineage points to a different active review, selected card, candidate,
comparison, or verdict; recovery continues to restore only diagnosis/evidence/hypothesis setup;
100 generated frontend review IDs/directories are unique under a temp runs root; focused frontend
API-route, TypeScript, and bridge tests pass; docs are synchronized; and no portfolio calculations,
Block 4 scoring, FastAPI schemas, generated review artifact schemas, route URLs, root `config.yml`,
PDFs, or browser state are changed.

Session 13 is accepted when the FastAPI contract governance guard rejects public claim schemas that
lose required source/provenance companions, rejects missing recommendation/evidence boundary wording
in mapped downstream operations, rejects unqualified advice-like frontend/API copy, focused
governance tests and documentation checks pass, and no portfolio calculations, Block 4 scoring,
FastAPI schemas, generated review artifact schemas, frontend route URLs, root `config.yml`, PDFs, or
browser state are changed.

Session 14 is accepted when a checked-in Browser/Playwright QA helper can start fresh local
FastAPI and Next.js servers, use a clean browser context, avoid stale browser storage, check server
readiness and compile diagnostics, capture screenshot fallbacks, verify same-run lineage, probe stale
selected-card rejection, and document the live QA command in QA sources.

Session 15 is accepted only when the live helper completes at least three portfolio scenarios through
diagnosis, Builder, Candidate, Comparison, Verdict, and Report; the scenarios produce distinct
source-backed diagnosis summaries; stale selected-card or stale review artifacts cannot unlock
downstream stages; and the QA report records URL/ports, active review IDs, browser state, screenshots
or DOM fallbacks, and source-artifact evidence. The accepted 2026-06-12 run completed this gate.

The full plan is accepted only after live frontend/FastAPI QA proves that at least three different
input portfolios produce different evidence-backed explanations, that stale review artifacts cannot
unlock downstream stages, and that every material site claim has a valid deterministic source
reference.

Session 16 is accepted when the plan is marked complete, the ExecPlan register records it as a
completed plan, the changelog and closure audit summarize the accepted evidence-chain foundation, and
documentation/diff checks pass without refreshing generated outputs.

## Idempotence and Recovery

Session 00 is additive documentation work. If a later session is interrupted, resume from this file
and update `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective`
before proceeding. Do not delete or rewrite existing generated outputs to recover from a planning
session. If a future implementation session changes public API fields, regenerate frontend types and
update the FastAPI contract in the same session.

## Artifacts and Notes

Session 00 intentionally did not create or refresh generated review outputs. It did not run
portfolio review commands. It did not update root `config.yml`. It did not touch frontend `.next`,
browser storage, or run-local review folders.

Session 02 intentionally did not create the planned `diagnosis_rulebook.yml` file under `config/`;
that file belongs to
Session 03 after the schema is in place. It also did not refresh generated review outputs, run
portfolio review commands, update root `config.yml`, change threshold values, touch frontend
`.next`, browser storage, or run-local review folders.

Session 03 intentionally did not make the YAML active in runtime diagnosis. It did not refresh
generated review outputs, run portfolio review commands, update root `config.yml`, change threshold
values, touch frontend `.next`, browser storage, or run-local review folders.

Session 08 intentionally regenerated only the frontend API type contract at
`frontend/lib/generated/api-types.ts`. It did not refresh generated portfolio review outputs, run
portfolio review commands, start FastAPI or Next.js servers, update root `config.yml`, generate PDFs,
touch frontend `.next`, browser storage, or run-local review folders.

Session 10 intentionally did not regenerate FastAPI types because no FastAPI schema changed. It did
not refresh generated portfolio review outputs, run portfolio review commands, start FastAPI or
Next.js servers, update root `config.yml`, generate PDFs, touch frontend `.next`, browser storage, or
run-local review folders.

Session 11 intentionally reused compact test fixtures rather than generated review outputs. It did
not refresh generated portfolio review outputs, run portfolio review commands, regenerate FastAPI
types, start FastAPI or Next.js servers, update root `config.yml`, generate PDFs, touch frontend
`.next`, browser storage, or run-local review folders.

Session 12 intentionally added only lineage guards and focused tests. It did not refresh generated
portfolio review outputs, run portfolio review commands, regenerate FastAPI types, start FastAPI or
Next.js servers, update root `config.yml`, generate PDFs, touch frontend `.next`, browser storage,
or persistent run-local review folders.

Session 14 intentionally added a QA helper and frontend dev dependency for Playwright. It did not
refresh generated portfolio review outputs, change portfolio calculations, change FastAPI schemas,
change generated review artifact schemas, update root `config.yml`, generate PDFs, or rely on old
browser state.

Session 15 intentionally attempted live QA and wrote generated evidence under `output/playwright/`
and a failed run-local review folder under `runs/`. Those generated artifacts are evidence only and
are not source-of-truth files. The accepted rerun reached live acceptance. Earlier failed generated QA outputs remain evidence
only and are not source-of-truth files.

Session 16 intentionally changed only source documentation and did not run portfolio review commands,
refresh generated review outputs, regenerate FastAPI types, start FastAPI or Next.js servers, update
root `config.yml`, generate PDFs, or touch browser storage.

The current working tree contains pre-existing modified and untracked files related to the FastAPI
foundation and frontend contracts. Future sessions must inspect `git status --short` before editing
and must not revert unrelated user changes.

## Interfaces and Dependencies

The near-term interfaces introduced or planned by this ExecPlan are:

- the read-only parity YAML at `config/diagnosis_rulebook.yml`.
- a documentation contract for that YAML at
  `docs/specs/diagnosis_rulebook_schema_spec.md`.
- the read-only Block 4 diagnosis-rulebook loader and validator module at
  `src/block_4/diagnosis_rulebook.py`.
- Additive fields on `problem_classification_v3`, especially `interpretation_chain`,
  `diagnosis_evidence_items`, `root_cause_narrative`, `metric_to_diagnosis_trace`, and
  `professional_rationale_refs`.
- Additive FastAPI display fields on `DiagnosisSummary` in `src/api/models.py`, including typed
  diagnosis evidence items, root-cause narrative, metric-to-diagnosis trace, rejected alternatives,
  professional rationale refs, source artifacts, diagnosis role, and recommendation boundary.

No new runtime dependency is required by Session 00. Future sessions should use the project
`.venv\Scripts\python.exe` when running Python commands.

Revision note, 2026-06-11: Session 00 created this plan because the user requested implementation
of a multi-session professional diagnosis interpretation foundation and asked to stop after Session
00 succeeds.

Revision note, 2026-06-11: Session 01 added the methodology spec and source-of-truth links so the
next contributor can design the diagnosis rulebook schema from a stable evidence-to-diagnosis
foundation rather than from scattered narrative assumptions.

Revision note, 2026-06-11: Session 02 added the rulebook schema spec and links so the next
contributor can implement the planned `diagnosis_rulebook.yml` file under `config/` plus a
loader/validator as a parity check before any Block 4 behavior changes.

Revision note, 2026-06-11: Session 03 added the parity YAML, read-only validator, and tests so the
next contributor can add additive interpretation-chain fields in Session 04 without guessing whether
the human-readable rulebook still mirrors the current Block 4 registries.

Revision note, 2026-06-11: Session 04 added additive source-backed interpretation-chain fields to
`problem_classification_v3` so later sessions can move site explanation, FastAPI, and frontend
adapters toward display-ready diagnosis models without reading backend scoring rows directly.

Revision note, 2026-06-11: Session 06 hardened confidence and data-quality gates so product-block
partial status is visible to Block 4 and missing stress evidence can block diagnosis only when paired
with partial X-Ray evidence or a hard data-trust failure.

Revision note, 2026-06-11: Session 07 made the deterministic site explanation diagnosis hierarchy
prefer the Session 04 interpretation chain while preserving legacy fallback behavior for older or
partial artifacts.

Revision note, 2026-06-11: Session 08 exposed the Session 04 interpretation chain through FastAPI
`DiagnosisSummary` display fields and regenerated frontend API types while preserving legacy compact
diagnosis fallbacks.


Revision note, 2026-06-11: Session 09 added bounded downstream FastAPI evidence-chain context so
comparison, verdict, and report responses can explain how the selected diagnosis and hypothesis flow
through candidate testing without exposing raw generated artifacts or changing portfolio calculations.

Revision note, 2026-06-11: Session 10 refactored frontend adapters to consume those FastAPI display
envelopes first, leaving same-run raw artifact parsing only as fallback/debug support for fields not
yet exposed as public display summaries.

Revision note, 2026-06-11: Session 11 added a dynamic interpretation fixture matrix over ten
deterministic Block 4 archetypes so future sessions can prove diagnosis explanations vary by
portfolio evidence before live FastAPI/frontend QA.

Revision note, 2026-06-12: Session 12 added frontend FastAPI public-envelope lineage rejection and
100-review-id collision coverage so multi-user or stale FastAPI responses cannot unlock downstream
screens for the wrong active review.

Revision note, 2026-06-12: Session 13 added sourced-claim and advice-language governance to the
FastAPI contract guard so public display envelopes and governed UI/API copy cannot drift toward
unsupported conclusions or trading-advice framing without a failing check.

Revision note, 2026-06-12: Session 14 added the defensive live Browser/Playwright QA helper and documented the `qa:vertical` command so future vertical acceptance starts from fresh servers, clean browser state, same-run lineage, and screenshot/DOM fallback evidence.

Revision note, 2026-06-12: Session 15 passed after empty-cache and browser-navigation hardening; the accepted QA report is `output/playwright/vertical-qa-2026-06-12T08-12-35-071Z/qa-report.json`.

Revision note, 2026-06-12: Session 16 synchronized documentation, added the closure audit, updated
the ExecPlan register and changelog, and closed the Diagnosis Interpretation Foundation plan.
