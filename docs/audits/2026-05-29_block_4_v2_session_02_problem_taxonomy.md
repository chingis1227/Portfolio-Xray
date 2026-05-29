# Block 4 v2 Session 02 — Problem Taxonomy Registry

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 02  
Prerequisite: [Session 01 contract spec](2026-05-29_block_4_v2_session_01_contract_spec.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| 15-problem registry implemented? | **Yes** — `src/block_4/problem_taxonomy.py` |
| Action paths (15) + Launchpad goals? | **Yes** — `ACTION_PATH_REGISTRY` |
| Block 2.6 v2 mapping? | **Yes** — `BLOCK_2_6_RISK_TYPE_TO_PROBLEM_IDS_V2` |
| V1 legacy id mapping? | **Yes** — `PROBLEM_ID_V1_TO_V2` |
| Root-cause elevation hints? | **Yes** — `ROOT_CAUSE_ELEVATION_RULES` (Session 06 input) |
| Contract SSOT alignment? | **Yes** — registry keys match `PROBLEM_CLASSIFICATION_V2_IDS` and `BLOCK_4_V2_ACTION_PATH_IDS` |

**Session 02 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| Problem + action taxonomy | `src/block_4/problem_taxonomy.py` |
| Package exports | `src/block_4/__init__.py` |
| Registry tests | `tests/test_block_4_problem_taxonomy.py` (**10 passed**) |
| Spec pointer | `docs/specs/block_4_diagnosis_v2_spec.md` (taxonomy line) |

Each `ProblemDefinition` includes: labels, PM interpretation, required/supporting/negative evidence signal names, action paths, default methods, Launchpad card hints, false positive/negative guards, downstream compare focus, `when_not_to_select_as_primary`.

---

## 3. Verification

```bash
python -m pytest tests/test_block_4_problem_taxonomy.py \
  tests/test_block_4_v2_contract.py tests/test_block_4_decision_entry_contract.py \
  tests/test_problem_classification.py tests/test_candidate_launchpad.py -q
```

**Result:** **37 passed**.

---

## 4. Next session

**Session 03:** `extract_evidence_signals()` in `src/block_4/evidence_extraction.py` reading canonical Block 2.1–2.6 and 3.3–3.4 fields.

---

## 5. Evidence log

| Category | Detail |
| --- | --- |
| Code | `src/block_4/problem_taxonomy.py` |
| Tests | `tests/test_block_4_problem_taxonomy.py` |
