# Block 5 Session 10 — Current vs Candidate + Decision Verdict

Date: 2026-05-29  
ExecPlan: [Blocks 1–3 post-audit development plan](../exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md) Phase D Session 10  
Prerequisite: [Block 4 Session 09](2026-05-29_block_4_session_09_problem_classification_launchpad.md), [Blocks 1–3 foundation closure](2026-05-29_blocks_1_3_foundation_closure_audit.md)

Specs: [current_vs_candidate_spec.md](../specs/current_vs_candidate_spec.md), [decision_verdict_spec.md](../specs/decision_verdict_spec.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| Are Current vs Candidate and Decision Verdict implemented... | **Yes** — `src/current_vs_candidate.py`, `src/decision_verdict.py`; written from `write_candidate_comparison_outputs()` in `src/candidate_comparison.py`. |
| Is Block 5 product contract enforced in tests... | **Yes** — `scripts/core_mvp_validation_contract.py` + `tests/test_block_5_decision_compare_contract.py`. |
| Does live E2E validate Block 5 on one-candidate runs... | **Yes** — `validate_live_core_artifacts` (`product_one_candidate`) calls Block 5 contract + handoff checks when compare artifacts exist. |
| Live demo portfolio (2026-05-29)... | **Pass** — `block_5_view_mode: one_candidate`, `block_5_n_comparisons: 1`, `block_5_verdict_id: rebalance_to_selected_candidate`. |

**Bottom line:** Block 5 compare/verdict layer is **accepted for Phase D continuation**. Operators can run `python run_portfolio_review.py --candidates equal_weight` and trust root `current_vs_candidate.json` + `decision_verdict.json` when `verify_live_core_e2e.py --profile product_one_candidate` reports `ok=True`.

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| CVC v1 contract | `current_vs_candidate_v1_product_contract_violations`, `check_current_vs_candidate_v1` |
| Verdict v1 contract | `decision_verdict_v1_product_contract_violations`, `check_decision_verdict_v1` |
| Cross-artifact handoff | `block_5_compare_handoff_violations`, `check_block_5_compare_handoff` |
| Tombstone guard | `no_candidate_v1` rejected as live compare output in handoff |
| Live E2E integration | `src/live_core_e2e.py` → `_validate_block_5_compare_root_bundle` |
| Regression tests | `tests/test_block_5_decision_compare_contract.py` |

---

## 3. Verification

```bash
python -m pytest tests/test_block_5_decision_compare_contract.py \
  tests/test_live_core_e2e_validation.py \
  tests/test_current_vs_candidate.py tests/test_decision_verdict.py -q
```

**Result:** **20 passed** (~64 s).

```bash
python run_portfolio_review.py --candidates equal_weight
python scripts/verify_live_core_e2e.py --profile product_one_candidate
```

**Live (2026-05-29):** `ok=True`; `block_5_view_mode=one_candidate`; `block_5_n_comparisons=1`; `block_5_verdict_id=rebalance_to_selected_candidate`; `block_5_verdict_family=core_compare`; `block_5_selection_status=selected_candidate`; `comparison_candidate_count=3` (scoped product menu).

**Artifacts (Main portfolio/):**

- `current_vs_candidate.json` — `schema_version: current_vs_candidate_v1`, `view_mode: one_candidate`, 1 comparison (`equal_weight`)
- `decision_verdict.json` — `schema_version: decision_verdict_v1`, `verdict_id: rebalance_to_selected_candidate`

---

## 4. Next session

**Session 11:** AI commentary / decision-package grounding on compare path (TBD per ExecPlan Phase D).

---

## 5. Evidence log

| Category | Detail |
| --- | --- |
| **Decision** | `DEC-2026-05-29-012` |
| **Code** | `scripts/core_mvp_validation_contract.py`, `src/live_core_e2e.py`, `tests/test_block_5_decision_compare_contract.py` |
