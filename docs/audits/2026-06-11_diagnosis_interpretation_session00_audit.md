# Diagnosis Interpretation Foundation Session 00 Audit

Status: **Session 00 baseline audit** for
`docs/exec_plans/2026-06-11_diagnosis_interpretation_foundation_plan.md`.

This audit is planning evidence only. It does not override `SPEC.md`, `RULES.md`, `OUTPUTS.md`,
`TESTING.md`, detailed specs, current code behavior, formulas, data rules, stress scenarios, or
generated artifact contracts.

## Question

What is already present in the current project for a deterministic, dynamic interpretation layer,
and what must the new plan strengthen without disrupting the active FastAPI migration...

## Baseline Findings

### Block 2 / Portfolio X-Ray

Portfolio X-Ray already has product-facing Blocks 2.1 through 2.6 documented in
`docs/specs/portfolio_xray_diagnostics_spec.md`. These blocks provide the pre-stress evidence base:
allocation, metrics, factor exposure, hidden exposure, risk budget, and weakness map. They are
diagnostic-only and must not become recommendations.

### Block 3 / Stress Lab

Stress Lab evidence is governed by stress specs and is already used by downstream Problem
Classification. The current product meaning is not simply "a loss number"; stress evidence should
confirm whether X-Ray weaknesses matter under market shocks, hedge gaps, or scenario losses.

### Block 4 / Problem Classification

The current Block 4 v3 contract in `docs/specs/block_4_diagnosis_v3_spec.md` already has the
correct product philosophy: one primary diagnosis, up to two secondary diagnoses, root-cause
diagnoses outranking symptoms, a required `next_diagnostic_step`, and Launchpad cards that are
hypothesis tests rather than rebalance recommendations.

The implementation is distributed across:

- `src/block_4/problem_taxonomy.py`
- `src/block_4/evidence_extraction.py`
- `src/block_4/problem_scoring.py`
- `src/block_4/problem_prioritization.py`
- `src/block_4/diagnosis_builder.py`

The next foundation work should not replace this stack. It should make the interpretation rulebook
more explicit, auditable, and display-ready.

### Site explanation bundle

`src/site_explanation_bundle.py` already creates `site_explanation_bundle.json` as a deterministic
screen-copy hierarchy. The existing guardrails are aligned with the requested no-hallucination
direction: it does not call an LLM, does not calculate new metrics, does not issue trade
instructions, and requires source references for material claims.

The next improvement is to make diagnosis copy prefer a structured interpretation chain from
`problem_classification.json` instead of relying on scattered fields or fallback summaries.

### FastAPI migration

The active FastAPI foundation plan is present at
`docs/exec_plans/2026-06-11_fastapi_foundation_plan.md`. It is already the project-level path for
moving the frontend from the old Next.js-to-Python bridge to typed FastAPI/OpenAPI/Pydantic
contracts. This new interpretation plan must extend that work rather than conflict with it.

`src/api/models.py` already contains a compact `DiagnosisSummary` with fields such as
`primary_diagnosis`, `headline`, `confidence`, `evidence_chain`, and `next_diagnostic_step`. Future
sessions should add display fields additively and regenerate frontend TypeScript types.

### Frontend contracts

`docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` and `docs/contracts/SCREEN_CONTRACTS.md` already define
the current route chain and artifact-to-screen boundaries:

    /portfolio-input
    -> /diagnosis
    -> /evidence
    -> /hypothesis
    -> /comparison
    -> /verdict
    -> /report

The frontend should consume display-ready product meaning and must not promote raw artifact names,
raw JSON keys, stale artifacts, or candidate-as-recommendation language into primary UI copy.

### Browser / Playwright QA

Browser QA already has known failure modes recorded in project guidance: stale dev servers, stale
browser state, stale `runs/frontend_review_*` artifacts, old Playwright element references,
concurrent `.next` writers, screenshot timeouts, and uncertain active `reviewId`. The requested plan
correctly adds a dedicated Browser/Playwright QA hardening session so product conclusions are not
made from stale UI state.

## Session 00 Scope Boundary

Session 00 creates only the plan and this audit. It does not:

- change portfolio formulas;
- change stress scenarios;
- change Block 4 scoring thresholds;
- change generated artifact schemas;
- change FastAPI runtime behavior;
- change frontend rendering;
- refresh generated outputs;
- edit root `config.yml`.

## Verification

Session 00 verification commands:

    rg -n "problem_classification|site_explanation_bundle|DiagnosisSummary|FastAPI" docs src frontend
    git diff --check

Expected result: the search finds the existing diagnosis, explanation, FastAPI, and frontend contract
surfaces. `git diff --check` exits successfully.

## Conclusion

The current project already has a strong starting point for deterministic diagnosis. The missing
foundation is not "more metrics" and not an LLM layer. The missing foundation is an explicit,
professional, source-backed interpretation chain that can be validated in backend artifacts, exposed
through FastAPI, rendered by the frontend, and tested across multiple portfolios and browser states.
