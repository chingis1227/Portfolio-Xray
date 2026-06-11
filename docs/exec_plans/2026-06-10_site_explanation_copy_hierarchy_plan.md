# Site Explanation Copy Hierarchy Pipeline

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. It is intentionally self-contained so
another agent can resume the work from this file without relying on chat history.

## Purpose / Big Picture

Portfolio MRI already produces deterministic evidence artifacts such as `portfolio_xray.json`,
`stress_report.json`, `problem_classification.json`, `current_vs_candidate.json`,
`decision_verdict.json`, and `ai_commentary_context.json`. The current frontend still has places
where high-level client-facing summaries, supporting evidence, and technical details are mixed
together. After this change, the product will expose a generated `site_explanation_bundle.json`
that separates every screen's copy into three levels: executive text visible first, evidence text
supporting the conclusion, and technical text reserved for disclosure or expansion. The user should
see clearer explanations that update when portfolio inputs and calculations change, without adding
LLM-generated claims or investment advice.

## Progress

- [x] (2026-06-10) Session 1 created this ExecPlan and the governing bundle contract in `docs/specs/site_explanation_bundle_spec.md`.
- [x] (2026-06-11) Session 2 implemented the backend bundle skeleton in `src/site_explanation_bundle.py` and added focused shape/write tests in `tests/test_site_explanation_bundle.py`.
- [x] (2026-06-11) Session 3 added runtime copy guardrails and focused tests for forbidden phrases, constrained `optimal portfolio` usage, and candidate-not-recommendation wording.
- [x] (2026-06-11) Session 4 added material-claim source validation tests and centralized source-reference shape checks.
- [x] (2026-06-11) Session 5 populated diagnosis and stress copy rules and added focused hierarchy tests.
- [x] (2026-06-11) Session 6 populated candidate, comparison, and verdict copy rules and added focused hierarchy tests.
- [x] (2026-06-11) Session 7 integrated bundle writing into portfolio review, comparison, and frontend bridge runtime paths.
- [x] (2026-06-11) Session 8 added frontend hierarchy rendering for executive, evidence, and technical copy.
- [x] (2026-06-11) Session 9 ran live CLI and browser QA, fixed a candidate-copy guardrail false positive discovered in the run, and verified run-local diagnosis/comparison/verdict bundle output.
- [x] (2026-06-11) Session 10 updated closing documentation, changelog, and regression evidence.

## Surprises & Discoveries

- Observation: The project already has a deterministic grounding layer, `src/ai_commentary_context.py`, and an AI Commentary spec. The new bundle should not replace that layer; it should consume or align with it and add UI hierarchy.
  Evidence: `docs/specs/ai_commentary_grounding_spec.md` says `ai_commentary_context.json` is grounding only, not generated natural-language AI commentary.
- Observation: Frontend screen contracts already forbid raw backend terms in primary UI copy, which fits the copy hierarchy goal.
  Evidence: `docs/specs/frontend_screen_contracts.md` contains a user-facing copy boundary and forbidden primary UI terms.
- Observation: The first backend skeleton can satisfy the final JSON shape without generating substantive product conclusions yet.
  Evidence: `src/site_explanation_bundle.py` creates all required screen and hierarchy keys, records source availability, and emits cautious empty states when evidence is absent.
- Observation: The guardrail layer belongs at text-item construction time rather than only as a test scan over the current skeleton output.
  Evidence: `src/site_explanation_bundle.py` now rejects forbidden generated copy through `_text_item()`, and `tests/test_site_explanation_guardrails.py` verifies direct rejection before richer copy-rule sessions add more text.
- Observation: Source-reference validation should run inside `_text_item()` alongside copy guardrails, not only in whole-bundle tests.
  Evidence: `src/site_explanation_bundle.py` now rejects material claims without sources, rejects unsupported source artifact names, and rejects missing `field_path` values; `tests/test_site_explanation_sources.py` covers those cases plus generated bundle material claims.
- Observation: The v1 screen-key contract has no separate `stress` screen, so Stress Test Lab copy belongs under the existing `evidence` screen until a later schema migration says otherwise.
  Evidence: `docs/specs/site_explanation_bundle_spec.md` lists required screen keys and Session 5 now emits worst synthetic stress, historical replay, loss-contributor, hedge-gap, and coverage copy under `screens.evidence`.
- Observation: Verdict copy needs a stronger gate than source availability because a stale or isolated
  verdict artifact must not create an action/no-action conclusion without active comparison evidence.
  Evidence: Session 6 emits `verdict.executive.decision_support_outcome` only when
  `decision_verdict.json` is supplied together with an active `current_vs_candidate.json.comparisons[]`
  row; otherwise it emits `verdict.executive.blocked_until_comparison`.


- Observation: Adding `site_explanation_bundle_json` to the existing product bundle required keeping it optional rather than part of the legacy six-file completeness gate.
  Evidence: `tests/test_product_bundle_paths.py::test_build_product_discovery_complete_phase` failed when the new key was counted as required post-compare completeness; Session 7 changed `src/product_bundle_paths.py` so the key is categorized as product-surface output without changing `product_bundle_complete`.
- Observation: Frontend hierarchy rendering can be added without replacing existing artifact-specific panels.
  Evidence: `frontend/components/explanation/SiteExplanationHierarchy.tsx` reads the bundle and renders executive/evidence/technical levels above the existing diagnosis, stress, hypothesis, comparison, verdict, and report content; `npm.cmd run typecheck` and `npm.cmd run test:smoke` passed.
- Observation: Live frontend comparison found a guardrail false positive in candidate-screen copy.
  Evidence: `runs/frontend_review_20260611T111013Z_38b1701e/current_vs_candidate_result.json`
  initially failed because `candidate.evidence.success criteria` included the safe source phrase
  "not an action recommendation"; Session 9 added candidate-copy sanitization and a regression
  test so candidate hierarchy text no longer contains `recommend*` wording.
- Observation: The run-local frontend bridge can write the downstream root bundle after comparison
  and verdict, but the browser journey may still stop before verdict when candidate metric values
  are unavailable.
  Evidence: after the fix, `runs/frontend_review_20260611T111013Z_38b1701e/site_explanation_bundle.json`
  contained populated `comparison`, `verdict`, and `report` screen keys; the Comparison page still
  showed a metrics-unavailable state because the candidate comparison dimensions had
  `candidate_value: null`, which is outside the explanation-bundle contract.
- Observation: In-app Browser screenshot capture timed out during Session 9, but DOM snapshots were
  usable for hierarchy QA.
  Evidence: repeated `tab.screenshot(...)` calls timed out with `Page.captureScreenshot`; DOM
  snapshots confirmed `Explanation hierarchy` and `site_explanation_bundle_v1` on `/diagnosis`,
  `/evidence`, `/hypothesis`, and `/comparison` for the active run.

## Decision Log


- Decision: Implement a new `site_explanation_bundle_v1` rather than overloading `ai_commentary_context.json`.
  Rationale: `ai_commentary_context.json` is a grounding and guardrail artifact. The new bundle is a screen-facing copy hierarchy artifact with executive, evidence, and technical levels.
  Date/Author: 2026-06-10 / Codex
- Decision: Use English product copy for the first implementation.
  Rationale: Current frontend copy, specs, tests, and examples are already in English, so English minimizes churn and keeps the MVP coherent.
  Date/Author: 2026-06-10 / Codex
- Decision: Treat every non-static claim as material and require source references unless it is explicitly marked as a boundary note.
  Rationale: The product must remain decision-support and evidence-grounded; unsupported claims are the highest trust risk.
  Date/Author: 2026-06-10 / Codex
- Decision: Session 2 should emit only source-availability technical items and missing-evidence empty states, leaving diagnosis, stress, candidate, comparison, and verdict wording for later copy-rule sessions.
  Rationale: This keeps the writer observable and schema-complete while avoiding premature material conclusions before Sessions 5 and 6 define the content rules.
  Date/Author: 2026-06-11 / Codex
- Decision: Enforce forbidden language and candidate recommendation boundaries inside `_text_item()` instead of relying only on final-document lint tests.
  Rationale: Later sessions will add many screen-specific copy rules; central validation makes unsafe text fail at creation time and keeps the artifact from being written with advice-like or marketing-like language.
  Date/Author: 2026-06-11 / Codex
- Decision: Validate all provided `source_refs` against the allowed deterministic artifact list and require a non-empty `field_path`.
  Rationale: Material claims need to be traceable to known review artifacts, and malformed references would make the future frontend hierarchy look sourced while remaining unverifiable.
  Date/Author: 2026-06-11 / Codex
- Decision: Map verdict IDs to bounded decision-support copy instead of reusing backend
  `verdict_label` or `recommended_action` strings directly.
  Rationale: Some backend labels/actions are legacy or implementation-facing and can sound too
  action-oriented for the site explanation hierarchy. The bundle should preserve the verdict
  evidence while avoiding automatic trade-instruction wording.
  Date/Author: 2026-06-11 / Codex


- Decision: Keep `site_explanation_bundle_json` optional in product discovery instead of making it part of `PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS`.
  Rationale: The artifact is additive screen-copy hierarchy. Existing `product_bundle_complete` semantics measure the pre-existing Core MVP product bundle and should not regress because the explanation bundle is missing or newly added.
  Date/Author: 2026-06-11 / Codex
- Decision: Render the hierarchy as an additive explanation panel rather than replacing existing screen panels.
  Rationale: Existing panels still own detailed interactive UI for X-Ray, Stress Lab, Hypothesis, Comparison, Verdict, and Report; the new bundle supplies the text hierarchy and source discipline above those panels.
  Date/Author: 2026-06-11 / Codex
- Decision: Sanitize recommendation wording in candidate-screen source text instead of weakening the central candidate recommendation guardrail.
  Rationale: Candidate copy should never read as a recommendation, and even negated source phrases
  such as "not a recommendation" can trip simple UI scans. Rewriting only the candidate-screen
  emitted text preserves strict runtime validation while keeping the underlying deterministic
  source artifact unchanged.
  Date/Author: 2026-06-11 / Codex

## Outcomes & Retrospective

Session 1 completed the contract lock only. Session 2 added the additive backend module and focused
shape/write tests. Session 3 added centralized generated-copy guardrails and focused regression
tests for forbidden terms, `optimal portfolio` constraints, and candidate-not-recommendation
wording. Session 4 added centralized source-reference validation and focused source tests for
material claims. Session 5 added deterministic diagnosis copy from Block 4 / X-Ray fallback and
stress copy under the evidence screen from Stress Test Lab summary blocks. Session 6 added
deterministic candidate, comparison, and verdict copy rules, including a verdict gate that requires
active comparison evidence before outcome copy appears. Session 7 wired the writer into
`run_report.py`, `src/candidate_comparison.py`, and `scripts/run_review_from_payload.py`; the
bundle now appears in diagnosis sidecars and root compare/verdict bridge outputs. Session 8 added
frontend rendering through `SiteExplanationHierarchy`, preserving existing screen panels while
showing executive copy first, supporting evidence second, and technical details in disclosure UI.
Session 9 ran live CLI and browser QA against a fresh frontend server on
`http://127.0.0.1:3037` and active review
`frontend_review_20260611T111013Z_38b1701e`. The live run verified hierarchy rendering on
diagnosis, evidence, hypothesis, and comparison DOM snapshots, verified diagnosis sidecar output
under `Main portfolio/analysis_subject/site_explanation_bundle.json`, and verified run-local root
bundle output under `runs/frontend_review_20260611T111013Z_38b1701e/site_explanation_bundle.json`.
It also found and fixed a candidate-copy guardrail false positive caused by safe "not a
recommendation" wording in candidate source fields. Session 10 updated the governing spec,
CHANGELOG, and this plan, and ran the closing regression sweep. One UI area remains not fully
browser-verified: the live frontend journey did not unlock the Verdict and Report pages because
the run-local comparison had unavailable candidate metric values. Backend verdict generation with
the correct selected card ID succeeded and refreshed the root bundle, so this is recorded as a
frontend/demo-data gate limitation rather than an explanation-bundle writer failure.

## Context and Orientation

The current Portfolio MRI product is diagnosis-first and current-portfolio-first. The main
portfolio review flow writes evidence files under the configured output folder and, for the
reviewed portfolio, under `analysis_subject/`. `run_report.py` materializes the current portfolio
diagnosis and currently writes `ai_commentary_context.json` after Block 4 diagnosis. The candidate
comparison path in `src/candidate_comparison.py` writes downstream artifacts such as
`current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, and
`what_changed_summary.json`. The local frontend bridge in `scripts/run_review_from_payload.py`
creates run-local folders under `runs/frontend_review_*` and returns compact JSON to the Next.js UI.

The phrase "copy hierarchy" means that screen copy is not all treated equally. Level 1 executive
text is the short summary shown immediately. Level 2 evidence text contains sourced facts that
support the summary. Level 3 technical text contains method, coverage, quality, and limitation
details that should be shown only in drill-down, disclosure, or expandable UI.

## Plan of Work

The implementation is split into ten sessions so each chat can stop at a clear acceptance point.
Session 1 locks the contract and the plan. Session 2 adds a deterministic backend writer with the
final JSON shape. Session 3 adds guardrails against advice-like and marketing-like language.
Session 4 enforces source references for material claims. Sessions 5 and 6 populate the screen copy
rules for diagnosis, stress, candidate, comparison, and verdict stages. Session 7 integrated the
writer into `run_report.py`, `src/candidate_comparison.py`, and `scripts/run_review_from_payload.py`.
Session 8 updated the frontend to render executive text first, evidence second, and technical text
inside disclosure UI. Session 9 performs live end-to-end QA. Session 10 updates closing docs and
records the final verification matrix.

## Concrete Steps

From the repository root `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`, Session 1 creates:

    docs/exec_plans/2026-06-10_site_explanation_copy_hierarchy_plan.md
    docs/specs/site_explanation_bundle_spec.md

Then run:

    rg "site_explanation_bundle|copy hierarchy|executive text|evidence text|technical text" docs SPEC.md OUTPUTS.md

Expected result: matches in the new ExecPlan, the new spec, and the specs index. No Python tests
are required for Session 1 because this session changes only documentation contracts.

## Validation and Acceptance

Session 1 is accepted when the new ExecPlan exists, the spec defines the three copy hierarchy
levels, the spec explicitly bans `buy`, `sell`, `must rebalance`, `best portfolio`, and
`guaranteed`, the spec allows `optimal portfolio` only for technical method context, and the spec
states that material claims require `source_refs`.

The full project is accepted only after later sessions show that `site_explanation_bundle.json` is
written by live review paths, contains hierarchy data for all Core MVP screens, passes guardrail and
source tests, and is rendered by the frontend without exposing raw backend terms in primary copy.

## Idempotence and Recovery

All Session 1 changes are additive documentation changes except for the specs index row. If a later
session changes the schema, update this ExecPlan and the spec together. If runtime implementation
is rolled back, keep this plan and mark incomplete sessions in `Progress` so the next agent can
resume safely.

## Artifacts and Notes

No generated output is part of Session 1. Do not edit `runs/`, `output/`, `Main portfolio/`, cache
folders, PDFs, or other generated artifacts while implementing this plan unless a later session
explicitly targets generated-output refresh.

## Interfaces and Dependencies

The future backend module must expose:

    SITE_EXPLANATION_BUNDLE_VERSION = "site_explanation_bundle_v1"
    SITE_EXPLANATION_BUNDLE_FILENAME = "site_explanation_bundle.json"
    build_site_explanation_bundle(...) -> dict
    write_site_explanation_bundle_outputs(output_dir, ...) -> dict

Session 2 implemented those interfaces in `src/site_explanation_bundle.py`. The current skeleton
accepts deterministic artifact dictionaries as optional keyword arguments, writes
`site_explanation_bundle.json`, includes all required screens and hierarchy arrays, and records the
required guardrails. It must not be treated as runtime-integrated until Session 7 wires it into
`run_report.py`, `src/candidate_comparison.py`, and `scripts/run_review_from_payload.py`.

The bundle must consume existing deterministic artifacts only. It must not call an LLM, must not
calculate new portfolio metrics, must not issue trade instructions, and must not turn a candidate
into a recommendation.

Session 2 verification transcript:

    D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА> .\.venv\Scripts\python.exe -m pytest tests/test_site_explanation_bundle.py
    collected 4 items
    tests\test_site_explanation_bundle.py .... [100%]
    4 passed

Session 3 verification transcript:

    D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА> .\.venv\Scripts\python.exe -m pytest tests/test_site_explanation_bundle.py tests/test_site_explanation_guardrails.py -q
    ............                                                             [100%]
    12 passed in 0.31s

Revision note, 2026-06-11: Session 3 updated this plan after adding centralized copy guardrails and
focused tests. The note exists so a future agent can resume Session 4 from this file without chat
history.

Session 4 verification transcript:

    D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА> .\.venv\Scripts\python.exe -m pytest tests/test_site_explanation_bundle.py tests/test_site_explanation_guardrails.py tests/test_site_explanation_sources.py -q
    .................                                                        [100%]
    17 passed in 0.47s

Revision note, 2026-06-11: Session 4 updated this plan after adding material-claim source
validation. The note exists so a future agent can resume Session 5 from this file without chat
history.

Session 5 verification transcript:

    D:\Р Р°Р±РѕС‡РёР№ СЃС‚РѕР»\РљРЈР РЎРћР  РўРЈР›Рђ Р”РРђР“РќРћРЎРўРРљРђ> .\.venv\Scripts\python.exe -m pytest tests/test_site_explanation_bundle.py tests/test_site_explanation_guardrails.py tests/test_site_explanation_sources.py tests/test_site_explanation_diagnosis_stress.py -q
    ....................                                                     [100%]
    20 passed in 0.59s

Revision note, 2026-06-11: Session 5 updated this plan after adding diagnosis and stress copy
rules. The note exists so a future agent can resume Session 6 from this file without chat history.

Session 6 verification transcript:

    D:\Р В Р В°Р В±Р С•РЎвЂЎР С‘Р в„– РЎРѓРЎвЂљР С•Р В»\Р С™Р Р€Р В Р РЋР С›Р В  Р СћР Р€Р вЂєР С’ Р вЂќР ВР С’Р вЂњР СњР С›Р РЋР СћР ВР С™Р С’> .\.venv\Scripts\python.exe -m pytest tests/test_site_explanation_bundle.py tests/test_site_explanation_guardrails.py tests/test_site_explanation_sources.py tests/test_site_explanation_diagnosis_stress.py tests/test_site_explanation_candidate_comparison_verdict.py -q
    .......................                                                  [100%]
    23 passed in 0.60s

Revision note, 2026-06-11: Session 6 updated this plan after adding candidate, comparison, and
verdict copy rules. The note exists so a future agent can resume Session 7 from this file without
chat history.


Session 7-8 verification transcript:

    <repo> .\.venv\Scripts\python.exe -m pytest tests/test_site_explanation_bundle.py tests/test_site_explanation_guardrails.py tests/test_site_explanation_sources.py tests/test_site_explanation_diagnosis_stress.py tests/test_site_explanation_candidate_comparison_verdict.py -q
    .......................                                                  [100%]
    23 passed in 0.65s

    <repo> .\.venv\Scripts\python.exe -m pytest tests/test_product_bundle_paths.py tests/test_product_bundle_integration.py tests/test_ai_commentary_context.py tests/test_light_monitoring_summary.py tests/test_portfolio_review_workflow.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py -q
    ........................................................................ [ 84%]
    .............                                                            [100%]
    85 passed in 26.24s

    <repo>\frontend npm.cmd run typecheck
    > portfolio-mri-frontend@0.1.0 typecheck
    > tsc --noEmit

    <repo>\frontend npm.cmd run test:api
    tests 7
    pass 7

    <repo>\frontend npm.cmd run test:smoke
    tests 1
    pass 1

Revision note, 2026-06-11: Sessions 7 and 8 updated this plan after runtime integration and
frontend hierarchy consumption. The note exists so a future agent can resume Session 9 live QA from
this file without chat history.

Session 9-10 verification transcript:

    <repo> .\.venv\Scripts\python.exe -m pytest tests/test_site_explanation_bundle.py tests/test_site_explanation_guardrails.py tests/test_site_explanation_sources.py tests/test_site_explanation_diagnosis_stress.py tests/test_site_explanation_candidate_comparison_verdict.py -q
    .......................                                                  [100%]
    23 passed in 1.10s

    <repo> .\.venv\Scripts\python.exe -m pytest tests/test_product_bundle_paths.py tests/test_product_bundle_integration.py tests/test_ai_commentary_context.py tests/test_light_monitoring_summary.py tests/test_portfolio_review_workflow.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py -q
    ........................................................................ [ 84%]
    .............                                                            [100%]
    85 passed in 38.45s

    <repo>\frontend npm.cmd run typecheck
    > portfolio-mri-frontend@0.1.0 typecheck
    > tsc --noEmit

    <repo>\frontend npm.cmd run test:api
    tests 7
    pass 7

    <repo>\frontend npm.cmd run test:smoke
    tests 1
    pass 1

    <repo> .\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight --skip-pdf
    completed after the original shell timeout; verified:
    Main portfolio\analysis_subject\site_explanation_bundle.json
    equal-weight portfolio\site_explanation_bundle.json

    Browser QA used fresh Next dev:
    <repo>\frontend npm.cmd run dev -- --hostname 127.0.0.1 --port 3037
    URL: http://127.0.0.1:3037
    active reviewId: frontend_review_20260611T111013Z_38b1701e
    verified DOM hierarchy markers on /diagnosis, /evidence, /hypothesis, and /comparison:
    Explanation hierarchy
    site_explanation_bundle_v1

    Live QA fix:
    <repo> .\.venv\Scripts\python.exe -m pytest tests/test_site_explanation_candidate_comparison_verdict.py tests/test_site_explanation_guardrails.py -q
    ...........                                                              [100%]
    11 passed in 0.75s

    Backend verdict bridge check:
    <repo> .\.venv\Scripts\python.exe scripts\run_review_from_payload.py --run-verdict --review-id frontend_review_20260611T111013Z_38b1701e --selected-card-id launchpad_01_compare_against_simple_benchmark
    runs/frontend_review_20260611T111013Z_38b1701e/decision_verdict_result.json
    decision_verdict_result.json: status completed, verdict_id evidence_insufficient

    <repo> .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    <repo> .\.venv\Scripts\python.exe -m pytest tests/test_docs_links.py -q
    .......                                                                  [100%]
    7 passed

Revision note, 2026-06-11: Sessions 9 and 10 updated this plan after live QA, the candidate-copy
guardrail sanitization fix, closing documentation updates, and regression verification. Browser
Verdict/Report route rendering remains not fully verified for the live run because frontend
comparison gating correctly stopped when candidate metrics were unavailable; backend verdict and
root bundle refresh were verified at the artifact level.
