# Block 4 v2 Session 05 — Severity and Confidence Classifiers

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 05  
Prerequisite: [Session 04 problem scoring](2026-05-29_block_4_v2_session_04_problem_scoring.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| `config/block_4_thresholds.yml` added? | **Yes** |
| Threshold loader implemented? | **Yes** — `src/block_4/thresholds.py` |
| Scoring uses config thresholds? | **Yes** — `score_problems(..., thresholds=...)` |
| Severity classifier? | **Yes** — `classify_severity()` |
| Confidence classifier? | **Yes** — `classify_confidence()` |
| Row fields populated? | **Yes** — `ProblemScoreRow.severity`, `.confidence` |
| Session 05 tests? | **Yes** — `tests/test_block_4_severity_confidence.py` (**6 passed**) |

**Session 05 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| Thresholds config | `config/block_4_thresholds.yml` |
| Threshold loader | `src/block_4/thresholds.py` |
| Severity / confidence | `src/block_4/severity_confidence.py` |
| Scoring integration | `src/block_4/problem_scoring.py` |
| Shared test fixtures | `tests/block_4_fixtures.py` |
| Unit tests | `tests/test_block_4_severity_confidence.py` |

---

## 3. Verification

```bash
python -m pytest tests/test_block_4_severity_confidence.py \
  tests/test_block_4_problem_scoring.py \
  tests/test_block_4_evidence_extraction.py \
  tests/test_block_4_problem_taxonomy.py \
  tests/test_block_4_v2_contract.py tests/test_block_4_decision_entry_contract.py -q
```

**Result:** **41 passed**.

---

## 4. Next session

**Session 06:** Problem prioritization (primary / secondary / rejected) using `decision_score`, severity, confidence, and `ROOT_CAUSE_ELEVATION_RULES`.

---

## 5. Evidence log

| Category | Detail |
| --- | --- |
| Config | `config/block_4_thresholds.yml` (`block_4_thresholds_v1`) |
| Code | `src/block_4/thresholds.py`, `src/block_4/severity_confidence.py` |
| Tests | `tests/test_block_4_severity_confidence.py` |
