# Block 4 v2 Session 01 — V2 Output Contract Design

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 01  
Prerequisite: [Session 00 gap audit](2026-05-29_block_4_v2_session_00_gap_audit.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| V2 JSON contract documented? | **Yes** — [block_4_diagnosis_v2_spec.md](../specs/block_4_diagnosis_v2_spec.md) |
| Contract validators implemented? | **Yes** — `scripts/core_mvp_validation_contract.py` (v2 section) |
| Contract tests? | **Yes** — `tests/test_block_4_v2_contract.py` (**7 passed**) |
| V1 still authoritative at runtime? | **Yes** — builder unchanged until Session 10 |

**Session 01 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| V2 spec (PC + Launchpad + handoff) | `docs/specs/block_4_diagnosis_v2_spec.md` |
| V2 contract validators | `problem_classification_v2_product_contract_violations`, `candidate_launchpad_v2_product_contract_violations`, `block_4_v2_diagnosis_handoff_violations` |
| Contract tests | `tests/test_block_4_v2_contract.py` |
| Spec cross-links | `problem_classification_spec.md`, `candidate_launchpad_spec.md`, `docs/specs/README.md`, `runtime_artifact_contract.md`, `reporting_outputs_spec.md` |

---

## 3. Contract highlights

- **Schema versions:** `problem_classification_v2`, `candidate_launchpad_v2`
- **Ruleset:** `block_4_v2_2026_06`
- **15 problem ids**, **15 action path ids**, structured `EvidenceRef`, `RejectedProblemRow`, `no_trade_or_monitoring_view`
- **Launchpad v2 cards:** max 4; required disclaimer, trade-off, skip text, `default_method`
- **V1 shim:** `problems[]` mirror retained in spec §3.1

---

## 4. Verification

```bash
python -m pytest tests/test_block_4_v2_contract.py tests/test_block_4_decision_entry_contract.py -q
```

**Result:** **27 passed**.

---

## 5. Next session

**Session 02:** `src/block_4/problem_taxonomy.py` — registry for all 15 problems with action paths and method hints.

---

## 6. Evidence log

| Category | Detail |
| --- | --- |
| Spec | `docs/specs/block_4_diagnosis_v2_spec.md` |
| Validators | `scripts/core_mvp_validation_contract.py` (Block 4 v2 section) |
| Tests | `tests/test_block_4_v2_contract.py` |
