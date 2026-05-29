# Block 4 v2 — Evidence-to-Problem Translation Layer

**Status: Completed** — Session 14 closed 2026-05-29. Evidence: [Session 14 institutional closure](../audits/2026-05-29_block_4_v2_session_14_institutional_closure.md).

Origin: Block 4 v2 product architecture plan; V1 baseline [Session 09 audit](../audits/2026-05-29_block_4_session_09_problem_classification_launchpad.md).

Session 00 evidence: [Block 4 v2 Session 00 gap audit](../audits/2026-05-29_block_4_v2_session_00_gap_audit.md).

Decision: `DEC-2026-05-29-013` (additive V2 + transitional V1 shim).

This ExecPlan follows [PLANS.md](../../PLANS.md). **One session = one new chat** for Sessions 01+.

---

## Purpose / Big Picture

After this plan, `run_portfolio_review.py` produces an **auditable Block 4 diagnosis**: one primary problem with structured evidence, up to two secondary problems, explicit rejected hypotheses, honest no-trade/monitor outcomes, and Launchpad cards that bridge to Portfolio Alternatives Builder without generating weights. A developer can trace every `evidence_ref` back to Blocks 2–3 JSON fields. The user sees a clear headline diagnosis and hypothesis cards—not a metric dump or rebalance instruction.

---

## Progress

- [x] (2026-05-29) **Session 00** — Gap audit + backward-compat decision; evidence: [Session 00 audit](../audits/2026-05-29_block_4_v2_session_00_gap_audit.md); pytest baseline **20 passed**
- [x] (2026-05-29) **Session 01** — V2 contract spec + validators; evidence: [Session 01 audit](../audits/2026-05-29_block_4_v2_session_01_contract_spec.md); pytest **27 passed** (20 V1 + 7 V2)
- [x] (2026-05-29) **Session 02** — Problem taxonomy registry; evidence: [Session 02 audit](../audits/2026-05-29_block_4_v2_session_02_problem_taxonomy.md); pytest **37 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 03** — Evidence extraction layer (`src/block_4/evidence_extraction.py`); evidence: [Session 03 audit](../audits/2026-05-29_block_4_v2_session_03_evidence_extraction.md); pytest **43 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 04** — Evidence-to-problem scoring; evidence: [Session 04 audit](../audits/2026-05-29_block_4_v2_session_04_problem_scoring.md); pytest **35 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 05** — Severity/confidence classifiers + `config/block_4_thresholds.yml`; evidence: [Session 05 audit](../audits/2026-05-29_block_4_v2_session_05_severity_confidence.md); pytest **41 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 06** — Problem prioritization (primary/secondary/rejected); evidence: [Session 06 audit](../audits/2026-05-29_block_4_v2_session_06_problem_prioritization.md); pytest **48 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 07** — Suggested action path mapping; evidence: [Session 07 audit](../audits/2026-05-29_block_4_v2_session_07_action_path_mapping.md); pytest **54 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 08** — Candidate Launchpad card generation (v2 fields); evidence: [Session 08 audit](../audits/2026-05-29_block_4_v2_session_08_launchpad_cards.md); pytest **60 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 09** — No-trade / evidence-insufficient gate; evidence: [Session 09 audit](../audits/2026-05-29_block_4_v2_session_09_no_trade_gate.md); pytest **67 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 10** — JSON wiring in `run_report.py` + manifest; evidence: [Session 10 audit](../audits/2026-05-29_block_4_v2_session_10_diagnosis_wiring.md); pytest **72 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 11** — Fixtures + tests (10 portfolio archetypes); evidence: [Session 11 audit](../audits/2026-05-29_block_4_v2_session_11_archetype_fixtures.md); pytest **87 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 12** — Product validation run (live E2E); evidence: [Session 12 audit](../audits/2026-05-29_block_4_v2_session_12_live_product_validation.md); pytest **90 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 13** — Documentation + operator guide + diagnostic_journey fixes; evidence: [Session 13 audit](../audits/2026-05-29_block_4_v2_session_13_documentation_sync.md); pytest **95 passed** (Block 4 bundle)
- [x] (2026-05-29) **Session 14** — Final audit and V1 validator removal / freeze; evidence: [Session 14 closure](../audits/2026-05-29_block_4_v2_session_14_institutional_closure.md); pytest **109 passed** (closure bundle)

---

## Surprises & Discoveries

- Observation: V1 Problem Classification reads **legacy** `sections.risk_diagnostics`, `sections.factor_exposure`, and `sections.asset_allocation` rather than canonical `block_2_2_*`, `block_2_3_*`, `block_2_1_*` product blocks.
  Evidence: [Session 00 gap audit](../audits/2026-05-29_block_4_v2_session_00_gap_audit.md) §3.3.

- Observation: Block 2.4/2.5 product blocks are fully implemented on X-Ray but **not wired** into V1 collectors (only hedge-gap bridge metadata references 2.4/2.6).
  Evidence: Session 00 field matrix §4.4–4.5.

- Observation: `DEC-2026-05-29-012` was already assigned to Block 5 Session 10; Block 4 v2 migration decision is **DEC-2026-05-29-013**.

---

## Decision Log

- Decision: Additive `problem_classification_v2` on same filenames with V1 compatibility shim until Session 14.
  Rationale: Session 09 E2E gates must not break mid-migration.
  Date/Author: 2026-05-29 / Session 00.

- Decision: New code under `src/block_4/` package; thin facade `build_block_4_diagnosis()` replaces monolithic growth in `problem_classification.py`.
  Rationale: Separates evidence extraction, scoring, and launchpad for testability.
  Date/Author: 2026-05-29 / Session 00 planning.

---

## Outcomes & Retrospective

**Closed 2026-05-29 (Session 14).**

- Shipped `problem_classification_v2` + `candidate_launchpad_v2` on unchanged bundle filenames via `src/block_4/`.
- Live E2E, operator validator (`validate_block_4_live.py`), 10 archetype fixtures, and diagnostic journey bridge all on v2.
- V1 product validators removed; `problems[]` JSON shim retained for transitional readers.
- Closure bundle: **109 passed**. Decision `DEC-2026-05-29-013` implemented.

Deferred: full Launchpad→Builder UX wiring; optional deletion of legacy V1 builder modules.

---

## Session guide (abbreviated)

Full session detail lives in the Block 4 v2 architecture plan (Sections C–M). Each session ends with: focused pytest, audit note if acceptance criteria met, and Progress checkbox update in this file.

All sessions complete. ExecPlan **Completed** 2026-05-29.
