# Block 4 v3 Investment Diagnosis Plan

This ExecPlan is a living implementation record. It follows `PLANS.md` and is
self-contained enough for a new agent to continue the work from repository
state plus this document.

## Purpose / Big Picture

Replace the current the prior Block 4 contract scoring-heavy product contract with Block 4 v3:
a diagnosis-first investment handoff. Blocks 1-3 remain unchanged: Block 1
loads and validates the portfolio, Block 2 produces Portfolio X-Ray evidence,
and Block 3 produces stress evidence. Block 4 v3 turns that evidence into one
clear investment diagnosis, explains why it matters, explains why other
problems were not selected, and hands off at most three hypothesis cards to the
Candidate Launchpad.

The public output filenames stay the same:

- `analysis_subject/problem_classification.json`
- `analysis_subject/candidate_launchpad.json`

The schema versions change to:

- `problem_classification_v3`
- `candidate_launchpad_v3`

The old v2 product logic is replaced, not preserved as a current legacy product
path.

## Current State Before This Plan

the prior Block 4 contract currently has:

- `docs/specs/block_4_diagnosis_v2_spec.md`
- `src/block_4/problem_taxonomy.py`
- `src/block_4/evidence_extraction.py`
- `src/block_4/problem_scoring.py`
- `src/block_4/problem_prioritization.py`
- `src/block_4/diagnosis_builder.py`
- `src/block_4/launchpad_cards.py`
- validators in `scripts/core_mvp_validation_contract.py`
- live checks in `scripts/validate_block_4_live.py`
- E2E handoff checks in `src/live_core_e2e.py`

The v2 contract can make `the prior conflict-as-primary id` the
primary problem. That is honest as a diagnostic warning, but weak as a product
verdict because it can sound like the system failed to understand the portfolio.

## Target Product Contract

Block 4 v3 must answer four user-facing questions:

1. What is wrong...
2. Why does it matter...
3. How confident are we...
4. What hypothesis should be tested next...

User-facing diagnosis model:

- `primary_diagnosis`
- `root_cause`
- `supporting_symptoms`
- `key_evidence` (maximum 5)
- `why_this_matters`
- `why_not_other_problems`
- `confidence`
- `confidence_explanation`
- `materiality`
- `actionability`
- `suggested_hypothesis`
- `success_criteria`

Guardrails:

- One primary diagnosis/outcome.
- Maximum two secondary diagnoses.
- Maximum five key evidence points.
- Maximum three launchpad cards.
- Symptoms support root-cause diagnoses instead of competing as primary by
  default.
- `conflicting signals` is not a normal primary diagnosis. Usable mixed
  evidence becomes `mixed_evidence_no_action` or a warning/note. Bad data is
  separately classified as `evidence_insufficient_data_quality`.
- Scoring remains backend audit metadata, not the main user-facing product
  output.

## Implementation Sessions

### Session 01 — Contract & Product Spec Freeze

Context documents:

- `AGENTS.md`
- `RULES.md`
- `WORKFLOW.md`
- `SPEC.md`
- `docs/product_flow_operator_guide.md`
- current the prior Block 4 contract spec

Tasks:

- Add or update the Block 4 v3 spec.
- Define the user-facing diagnosis model.
- Define `mixed_evidence_no_action` / `no_dominant_actionable_problem`.
- State explicitly that Block 4 is an investment diagnosis, not a scoring
  dashboard.

Done when:

- v3 spec exists.
- Docs say scoring is backend audit metadata.
- Docs say v2 is replaced as the current product contract.

Verification:

- `rg "prior problem-classification schema|prior launchpad schema|legacy conflict wording" docs src tests scripts`
- `.\.venv\Scripts\python.exe scripts/verify_docs.py`

### Session 02 — Taxonomy Refactor: Root-cause vs Symptoms

Tasks:

- Add explicit diagnosis role/level to problem definitions.
- Split registry into root-cause, symptom, and outcome/status problems.
- Replace `the prior conflict-as-primary id` with
  `mixed_evidence_no_action`.

Done when:

- Taxonomy exposes root-cause vs symptom vs outcome role.
- Tests prove stress-confirmed root-cause beats symptoms.
- Old conflicting-signals id is no longer current taxonomy.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests/test_block_4_problem_taxonomy.py -q`

### Session 03 — Evidence & Triage Layer

Tasks:

- Keep existing evidence extraction; add a diagnosis evidence bundle layer.
- Track root-cause evidence, symptom evidence, negative evidence, conflict
  notes, and data-quality notes.
- Store mixed evidence as a note/warning when evidence is usable.

Done when:

- Bad data, mixed usable evidence, and no dominant issue are distinguishable.
- Strong crisis evidence with minor conflicts still selects
  `weak_crisis_resilience`.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests/test_block_4_evidence_extraction.py -q`

### Session 04 — Prioritization Rewrite

Tasks:

- Select primary diagnosis around the root-cause hierarchy.
- Use this order: data-quality blocker; stress-confirmed root-cause; structural
  root-cause; no dominant actionable problem; acceptable/monitor.
- Move symptoms into `supporting_symptoms`.
- Add `why_not_other_problems`.

Done when:

- Output always has one primary diagnosis/outcome.
- Max two secondary diagnoses.
- Max five key evidence points.
- Symptoms do not duplicate root-cause as primary by default.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests/test_block_4_problem_prioritization.py tests/test_block_4_problem_scoring.py -q`

### Session 05 — Diagnosis Narrative Builder

Tasks:

- Build the v3 user-facing diagnosis document.
- Add concentration subtypes.
- Keep scoring in audit/meta, not as the dominant product surface.

Done when:

- `problem_classification.json` reads as an investment thesis.
- `why_not_other_problems[]` exists.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests/test_block_4_diagnosis_builder.py tests/test_block_4_action_path_mapping.py -q`

### Session 06 — Launchpad v3 with Success Criteria

Tasks:

- Update launchpad schema to `candidate_launchpad_v3`.
- Add `source_diagnosis_id`, `hypothesis_to_test`, `suggested_methods`,
  `success_criteria`, `tradeoff_to_watch`, `when_to_skip`, and hypothesis
  disclaimer.
- Ensure monitor/no-action outcomes do not generate misleading methods.

Done when:

- Each card explains how success is judged.
- Maximum three user-facing cards.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests/test_block_4_launchpad_cards.py tests/test_block_4_no_trade_gate.py -q`

### Session 07 — Validators, Live E2E, Product Bundle Wiring

Tasks:

- Replace v2 validators with v3 validators:
  - `check_problem_classification_v3`
  - `check_candidate_launchpad_v3`
  - `check_block_4_v3_diagnosis_handoff`
- Update live validation and product bundle checks.

Done when:

- Product validators require v3.
- v2 is not accepted as current product contract.
- `run_report.py` writes v3 documents without v2 fallback.

Verification:

- `.\.venv\Scripts\python.exe -m pytest tests/test_block_4_v2_contract.py tests/test_block_4_decision_entry_contract.py tests/test_live_core_e2e_validation.py -q`
- `.\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis`

### Session 08 — Documentation Sync & Operator Guide

Tasks:

- Update `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, `CHANGELOG.md`, and
  `docs/product_flow_operator_guide.md`.
- Update read order: diagnosis first, evidence second, why-not third,
  launchpad success criteria fourth.

Done when:

- Docs match code.
- Operator guide explains Block 4 as investment diagnosis, not scoring output.

Verification:

- `rg "prior problem-classification schema|prior launchpad schema|the prior Block 4 contract" .`
- `.\.venv\Scripts\python.exe scripts/verify_docs.py`

### Session 09 — Final Live Proof on Current Config Portfolio

Tasks:

- Run the current portfolio-first diagnosis.
- Inspect generated Block 4 outputs.
- Confirm that current portfolio passes live validation.

Done when:

- Current portfolio emits a clear v3 diagnosis.
- Launchpad includes success criteria.
- Focused and bundle tests pass.

Verification:

- `.\.venv\Scripts\python.exe run_portfolio_review.py --skip-candidates`
- `.\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis`
- `.\.venv\Scripts\python.exe -m pytest tests/test_block_4_*.py -q`
- `.\.venv\Scripts\python.exe -m pytest tests/test_product_bundle_integration.py tests/test_product_bundle_paths.py -q`
- optional one-candidate demo:
  `.\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight`

## Progress

- [x] Plan accepted by user in chat.
- [x] Implementation branch created: `codex/block-4-v3-diagnosis`.
- [x] Session 01 — Contract & Product Spec Freeze.
- [x] Session 02 — Taxonomy Refactor.
- [x] Session 03 — Evidence & Triage Layer.
- [x] Session 04 — Prioritization Rewrite.
- [x] Session 05 — Diagnosis Narrative Builder.
- [x] Session 06 — Launchpad v3.
- [x] Session 07 — Validators, Live E2E, Product Bundle Wiring.
- [x] Session 08 — Documentation Sync.
- [x] Session 09 — Final Live Proof.

## Surprises & Discoveries

- 2026-06-04: Existing test filenames still include historical `v2` in a few names, but their assertions now target v3 contracts.
- 2026-06-04: Historical audit records retain old contract terminology for traceability; current specs/docs/code/tests use v3.

## Implementation Notes

- 2026-06-04: Implementation completed through documentation sync; final live proof completed through `scripts/validate_block_4_live.py --refresh-diagnosis` on the current `Main portfolio/analysis_subject`.


## Decision Log

- 2026-06-04: Use v3 schema bump instead of trying to preserve v2 schema.
- 2026-06-04: Treat mixed usable evidence as a no-action/monitoring posture or
  note, not as a normal primary diagnosis.
- 2026-06-04: Replace the current v2 product contract; do not keep old Block 4
  v2 as a current legacy product path.

## Outcomes & Retrospective

Completed 2026-06-04.

- Implemented `problem_classification_v3` and `candidate_launchpad_v3` on the same filenames.
- Current Block 4 user-facing output leads with `primary_diagnosis`, root cause/outcome, supporting symptoms, max-five evidence, why-not, confidence/materiality/actionability, suggested hypothesis, and success criteria.
- Current portfolio live Block 4 validation passed with `primary_diagnosis=mixed_evidence_no_action`, `key_evidence_len=5`, `why_not_len=5`, two Launchpad cards, and success criteria on both cards.
- Focused Block 4 regression bundle passed: 90 tests.
- Product bundle + diagnostic journey tests passed: 28 tests.
- Documentation verification passed.
- Full `run_portfolio_review.py --skip-candidates` did not complete because the run failed before Block 4 on external FRED/data dependency timeout (`distutils` import fallback + FRED CSV read timeout). Existing subject artifacts were valid for direct Block 4 refresh and validation.

