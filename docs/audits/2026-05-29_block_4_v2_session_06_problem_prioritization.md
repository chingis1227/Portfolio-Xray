# Block 4 v2 Session 06 — Problem Prioritization

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 06  
Prerequisite: [Session 05 severity/confidence](2026-05-29_block_4_v2_session_05_severity_confidence.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| `prioritize_problems()` implemented? | **Yes** — `src/block_4/problem_prioritization.py` |
| Primary / secondary / rejected split? | **Yes** — 1 primary, max 2 secondary, explicit `rejected_problems[]` |
| Uses `decision_score`, severity, confidence? | **Yes** — ranked tuple with tie-breakers |
| Root-cause elevation rules applied? | **Yes** — `ROOT_CAUSE_ELEVATION_RULES` with demotion + score boost |
| Special primaries (data quality / conflict / acceptable)? | **Yes** |
| Session 06 tests? | **Yes** — `tests/test_block_4_problem_prioritization.py` (**7 passed**) |

**Session 06 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| Prioritization module | `src/block_4/problem_prioritization.py` |
| Package exports | `src/block_4/__init__.py` |
| Unit tests | `tests/test_block_4_problem_prioritization.py` |
| Spec pointer | `docs/specs/block_4_diagnosis_v2_spec.md` (Session 06 line) |

`prioritize_problems(scoring, evidence)` returns `ProblemPrioritizationResult` with:

- `primary_problem_id` / `primary_row`
- `secondary_problem_ids` (max 2) / `secondary_rows`
- `rejected_problems` — `RejectedProblemRow` with `reject_reason_code`, `reject_reason_en`, `top_evidence_refs`
- `problems_activated`, `elevation_rules_applied`

Reject reason codes include scoring-stage codes plus:

- `superseded_by_root_cause_diagnosis`
- `lower_priority_than_selected_problems`
- `stress_not_confirmed_below_materiality`

---

## 3. Verification

```bash
python -m pytest tests/test_block_4_problem_prioritization.py \
  tests/test_block_4_severity_confidence.py \
  tests/test_block_4_problem_scoring.py \
  tests/test_block_4_evidence_extraction.py \
  tests/test_block_4_problem_taxonomy.py \
  tests/test_block_4_v2_contract.py tests/test_block_4_decision_entry_contract.py -q
```

**Result:** **48 passed**.

Golden fixture: `weak_crisis_resilience` primary (not raw top `weak_hedge_behavior`); `weak_hedge_behavior` rejected via `hedge_gap_over_labeled_hedge`.

---

## 4. Next session

**Session 07:** Suggested action path mapping (`suggested_actions[]` deduped from primary + secondary).

---

## 5. Evidence log

| Category | Detail |
| --- | --- |
| Code | `src/block_4/problem_prioritization.py` |
| Tests | `tests/test_block_4_problem_prioritization.py` |
| Ruleset | `block_4_v2_prioritization_heuristic_v1` |
