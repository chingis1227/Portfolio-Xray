# Blocks 1–3 Post-Audit Development Plan (Runtime Contract + Foundation Closure)

**Status: Active** — Phase A **complete** (Session 06 closed 2026-05-29). Optional Sessions 07–08 (R6–R7) remain backlog.

Origin audit: [Blocks 1–3 pre-decision foundation audit](../audits/2026-05-29_blocks_1_3_pre_decision_diagnostic_foundation_audit.md)  
Verdict at audit: `NOT_READY_RUNTIME_CONTRACT_MISMATCH`  
Target after Phase A (Sessions 01–06): `READY_FOR_DECISION_WORKFLOW`

Artifact contract (operators): [runtime_artifact_contract.md](../runtime_artifact_contract.md)

This ExecPlan follows [PLANS.md](../../PLANS.md). **One session = one new chat** for Sessions 02+.

---

## Purpose / Big Picture

Blocks 1–3 analytics (X-Ray + Stress) are test-backed and institutionally upgraded, but **runtime artifact scope** misleads operators: stale compare/verdict files, core-only runs leaving Block 4+ JSON on disk, and one-candidate runs writing a 19-row comparison menu. After this plan, each of the three canonical CLIs leaves a **predictable, authoritative** file set so Problem Classification and Decision Workflow can build on a frozen diagnostic foundation.

---

## Progress

- [x] (2026-05-29) **Session 00** — ExecPlan + [runtime_artifact_contract.md](../runtime_artifact_contract.md); README Active pointer; ROADMAP + CHANGELOG
- [x] (2026-05-29) **Session 01** — Report timing registry parity test; `export_stress_hedge_gap_bridge` in `REPORT_TIMING_BLOCK_KEYS`; pytest timing + core diagnostics entrypoint pass
- [x] (2026-05-29) **Session 02** — Product-scoped `candidate_comparison.json` write (R2); full on-disk scan in `candidate_comparison_registry.json` for `explicit_list` runs
- [x] (2026-05-29) **Session 03** — `product_bundle_hygiene` + diagnosis-only `no_candidate_v1` tombstones (R3)
- [x] (2026-05-29) **Session 04** — Core-only subject prune + root post-compare removal (R4)
- [x] (2026-05-29) **Session 05** — Live E2E validator profiles (R5): `detect_live_core_e2e_profile`, four profiles in `src/live_core_e2e.py`, `verify_live_core_e2e.py --profile`, offline tests
- [x] (2026-05-29) **Session 06** — Foundation re-audit closure; verdict `READY_FOR_DECISION_WORKFLOW`; evidence: [foundation closure audit](../audits/2026-05-29_blocks_1_3_foundation_closure_audit.md)
- [ ] **Sessions 07–08** — Optional 2.6/3.4 polish (R6–R7)
- [x] (2026-05-29) **Session 09** — Block 4 Problem Classification + Candidate Launchpad product contracts + live E2E gates; evidence: [Session 09 audit](../audits/2026-05-29_block_4_session_09_problem_classification_launchpad.md)
- [x] (2026-05-29) **Session 10** — Block 5 Current vs Candidate + Decision Verdict product contracts + live E2E gates; evidence: [Session 10 audit](../audits/2026-05-29_block_5_session_10_current_vs_candidate_decision_verdict.md)
- [ ] **Sessions 11–12** — Phase D Decision workflow (continued)

---

## Surprises & Discoveries

- Observation: `scoped_product_comparison` already existed; Session 02 wires product write to scoped doc and emits full scan as `candidate_comparison_registry.json`.
  Evidence: [pre-decision audit](../audits/2026-05-29_blocks_1_3_pre_decision_diagnostic_foundation_audit.md) §12 R2; `write_candidate_comparison_outputs` in `src/candidate_comparison.py`.

- Observation: Core diagnostics failed in audit until `export_stress_hedge_gap_bridge` was added to timing keys.
  Evidence: audit §2.1; Session 01 regression test prevents recurrence.

- Observation: A single `core_fast` comparison gate failed on workspaces after explicit-list or diagnosis-only runs (audit §11).
  Evidence: Session 05 — `validate_live_core_artifacts` auto-detects `core_blocks_1_3`, `diagnosis_only`, `product_one_candidate`, or `research_batch_core_fast` from factory/tombstone/subject layout.

---

## Decision Log

- Decision: Product-facing `candidate_comparison.json` will equal scoped document for `explicit_list` runs; full registry optional as `candidate_comparison_registry.json` (Session 02).
  Rationale: Operators must not filter 19 rows for one-candidate UX.
  Date/Author: 2026-05-29 / Session 00 planning.

- Decision: Diagnosis-only runs use explicit tombstone (`no_candidate_v1`) rather than silent delete when compare artifacts may be read by UI (Session 03).
  Rationale: Absent file vs stale file ambiguity.
  Date/Author: 2026-05-29 / Session 00 planning.

---

## Outcomes & Retrospective

**Phase A (Sessions 00–06) closed 2026-05-29.** Runtime artifact contract R1–R5 remediated; three canonical CLIs re-run on `Main portfolio/` with `validate_live_core_artifacts` OK per profile (`core_blocks_1_3`, `diagnosis_only`, `product_one_candidate`). One-candidate `candidate_comparison.json` holds **3** scoped rows (not 19). Focused pytest bundle: **261 passed**, 1 skipped. Verdict upgraded to **`READY_FOR_DECISION_WORKFLOW`** — see [foundation closure audit](../audits/2026-05-29_blocks_1_3_foundation_closure_audit.md). Decision `DEC-2026-05-29-010`.

**Remaining (optional):** Sessions 07–08 (R6 2.6/3.2 bridge copy, R7 scorecard `ok` criteria on demo). Phase D Decision workflow (Sessions 09–12) is the next product phase, not blocked by Phase A closure.

---

## Session prompts (copy into new chat)

### Session 02

Implement Session 02 only from this ExecPlan. Scope `candidate_comparison.json` product write (R2). Do not start Session 03. Update Progress + CHANGELOG + `DEC-2026-05-29-006`.

### Session 03

Implement Session 03 only: `product_bundle_hygiene` + diagnosis-only tombstones (R3). New chat required.

### Session 05

Implement Session 05 only: live E2E validator profiles (R5). Update Progress + CHANGELOG + `DEC-2026-05-29-009`. Verification: `python -m pytest tests/test_live_core_e2e_validation.py -q`.

### Session 06

Implement Session 06 only: foundation re-audit closure. Re-run three canonical CLIs; `scripts/verify_live_core_e2e.py` per profile; score acceptance criteria 1–18; publish [foundation closure audit](../audits/2026-05-29_blocks_1_3_foundation_closure_audit.md); update Progress + CHANGELOG + `DEC-2026-05-29-010`. Verification: closure audit §6 pytest bundle.

### Session 09

Implement Session 09 only: Block 4 Problem Classification + Candidate Launchpad — product contract validators in `scripts/core_mvp_validation_contract.py`, live E2E Block 4 gates in `src/live_core_e2e.py` (`diagnosis_only` + `product_one_candidate`), `tests/test_block_4_decision_entry_contract.py`. Update Progress + CHANGELOG + `DEC-2026-05-29-011`. Verification: `python -m pytest tests/test_block_4_decision_entry_contract.py tests/test_live_core_e2e_validation.py tests/test_problem_classification.py tests/test_candidate_launchpad.py -q`; `python scripts/verify_live_core_e2e.py --profile diagnosis_only`.

### Session 10

Implement Session 10 only: Block 5 Current vs Candidate + Decision Verdict — product contract validators in `scripts/core_mvp_validation_contract.py`, live E2E Block 5 gates in `src/live_core_e2e.py` (`product_one_candidate`), `tests/test_block_5_decision_compare_contract.py`. Update Progress + CHANGELOG + `DEC-2026-05-29-012`. Verification: `python -m pytest tests/test_block_5_decision_compare_contract.py tests/test_live_core_e2e_validation.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py -q`; `python run_portfolio_review.py --candidates equal_weight`; `python scripts/verify_live_core_e2e.py --profile product_one_candidate`.

---

## Phase D — Decision workflow (Sessions 09–12)

Session 09 closes the **Block 4 decision entry** layer: deterministic Problem Classification and Candidate Launchpad artifacts under `analysis_subject/`, with product-contract validation and live E2E gates on diagnosis-only and one-candidate runs. Session 10 closes **Block 5** root compare/verdict contracts (`current_vs_candidate_v1`, `decision_verdict_v1`) with live E2E on `product_one_candidate`. Sessions 11–12 cover AI commentary grounding and end-to-end decision package validation (TBD in follow-on sessions).

---

## Session 01 — Done criteria (reference)

- `tests/test_report_timing.py::test_run_report_timing_blocks_registered_in_module`
- `python -m pytest tests/test_report_timing.py tests/test_core_diagnostics_entrypoint.py -q`

---

## Validation and Acceptance (Phase A)

After Session 06, on a clean `{output_dir_final}`:

1. Three CLI modes per [runtime_artifact_contract.md](../runtime_artifact_contract.md).
2. `validate_live_core_artifacts` → `ok=True`.
3. [Pre-decision audit](../audits/2026-05-29_blocks_1_3_pre_decision_diagnostic_foundation_audit.md) acceptance criteria 1–18 pass.
4. Verdict upgraded to `READY_FOR_DECISION_WORKFLOW`.
