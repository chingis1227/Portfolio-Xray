# Block 4 Session 09 — Problem Classification + Candidate Launchpad

Date: 2026-05-29  
ExecPlan: [Blocks 1–3 post-audit development plan](../exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md) Phase D Session 09  
Prerequisite: [Blocks 1–3 foundation closure](2026-05-29_blocks_1_3_foundation_closure_audit.md) (`READY_FOR_DECISION_WORKFLOW`)

Specs: [problem_classification_spec.md](../specs/problem_classification_spec.md), [candidate_launchpad_spec.md](../specs/candidate_launchpad_spec.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| Are Problem Classification and Launchpad implemented... | **Yes** — `src/problem_classification.py`, `src/candidate_launchpad.py`; written from `run_report.py` on diagnosis materialize. |
| Is Block 4 product contract enforced in tests... | **Yes** — `scripts/core_mvp_validation_contract.py` + `tests/test_block_4_decision_entry_contract.py`. |
| Does live E2E validate Block 4 on diagnosis-only runs... | **Yes** — `validate_live_core_artifacts` (`diagnosis_only`, `product_one_candidate`) calls Block 4 contract + handoff checks. |
| Live demo portfolio (2026-05-29)... | **Pass** — `block_4_n_problems: 3`, `block_4_n_cards: 5`, primary problem `weak_hedge_behavior`. |

**Bottom line:** Block 4 decision entry is **accepted for Phase D continuation**. Operators can run `python run_portfolio_review.py` and trust `analysis_subject/problem_classification.json` + `candidate_launchpad.json` when `verify_live_core_e2e.py --profile diagnosis_only` reports `ok=True`.

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| PC v1 contract | `problem_classification_v1_product_contract_violations`, `check_problem_classification_v1` |
| Launchpad v1 contract | `candidate_launchpad_v1_product_contract_violations`, `check_candidate_launchpad_v1` |
| Cross-artifact handoff | `block_4_diagnosis_handoff_violations`, `check_block_4_diagnosis_handoff` |
| Live E2E integration | `src/live_core_e2e.py` → `_validate_block_4_subject_bundle` |
| Regression tests | `tests/test_block_4_decision_entry_contract.py` |

---

## 3. Verification

```bash
python -m pytest tests/test_block_4_decision_entry_contract.py \
  tests/test_live_core_e2e_validation.py \
  tests/test_problem_classification.py tests/test_candidate_launchpad.py -q
```

**Result:** **25 passed** (~64 s).

```bash
python run_portfolio_review.py
python scripts/verify_live_core_e2e.py --profile diagnosis_only
```

**Live (2026-05-29):** `ok=True`; `block_4_primary_problem_id=weak_hedge_behavior`; `block_4_hedge_gap_source=hedge_gap_analysis_v1`; `block_4_stress_scorecard_source=current_portfolio_stress_scorecard_v1`.

---

## 4. Next session

**Session 10:** Closed — see [Block 5 Session 10 audit](2026-05-29_block_5_session_10_current_vs_candidate_decision_verdict.md).

---

## 5. Evidence log

| Category | Detail |
| --- | --- |
| **Decision** | `DEC-2026-05-29-011` |
| **Code** | `scripts/core_mvp_validation_contract.py`, `src/live_core_e2e.py`, `tests/test_block_4_decision_entry_contract.py` |
