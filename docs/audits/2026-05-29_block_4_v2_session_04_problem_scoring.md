# Block 4 v2 Session 04 — Evidence-to-Problem Scoring

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 04  
Prerequisite: [Session 03 evidence extraction](2026-05-29_block_4_v2_session_03_evidence_extraction.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| `score_problems()` implemented? | **Yes** — `src/block_4/problem_scoring.py` |
| All 15 taxonomy ids evaluated? | **Yes** — `problems_evaluated == 15` |
| Required / supporting / negative signal logic? | **Yes** — OR-groups for multi-signal problems |
| Composite signals (`no_material_problem`, `conflicting_signal_bundle`)? | **Yes** |
| Scoring audit fields (`raw_score`, `decision_score`, `stress_confirmation`, `materiality`)? | **Yes** |
| Session 04 tests? | **Yes** — `tests/test_block_4_problem_scoring.py` (**6 passed**) |

**Session 04 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| Problem scoring module | `src/block_4/problem_scoring.py` |
| Package exports | `src/block_4/__init__.py` |
| Unit tests | `tests/test_block_4_problem_scoring.py` |
| Spec pointer | `docs/specs/block_4_diagnosis_v2_spec.md` (Session 04 line) |

`score_problems(evidence)` returns `ProblemScoringResult` with:

- per-problem `ProblemScoreRow` (`scoring`, `evidence_refs`, `negative_evidence_refs`, `activated`, reject reasons)
- `activated_problem_ids` / `actionable_activated_ids`
- composite flags: `conflicting_signal_bundle`, `no_material_problem`

Severity and confidence row fields remain for **Session 05** (`config/block_4_thresholds.yml`).

---

## 3. Verification

```bash
python -m pytest tests/test_block_4_problem_scoring.py \
  tests/test_block_4_evidence_extraction.py \
  tests/test_block_4_problem_taxonomy.py \
  tests/test_block_4_v2_contract.py tests/test_block_4_decision_entry_contract.py -q
```

**Result:** **35 passed**.

---

## 4. Next session

**Session 05:** Severity and confidence classifiers + `config/block_4_thresholds.yml` (externalize inline heuristic thresholds from scoring).

---

## 5. Evidence log

| Category | Detail |
| --- | --- |
| Code | `src/block_4/problem_scoring.py` |
| Tests | `tests/test_block_4_problem_scoring.py` |
| Ruleset | `block_4_v2_scoring_heuristic_v1` (inline; moves to config Session 05) |
