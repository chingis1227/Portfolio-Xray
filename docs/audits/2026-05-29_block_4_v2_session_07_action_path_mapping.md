# Block 4 v2 Session 07 — Suggested Action Path Mapping

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 07  
Prerequisite: [Session 06 prioritization](2026-05-29_block_4_v2_session_06_problem_prioritization.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| `map_action_paths()` implemented? | **Yes** — `src/block_4/action_path_mapping.py` |
| Per-problem action fields populated? | **Yes** — `suggested_action_path_id`, `secondary_action_path_ids`, methods, paths |
| Top-level `suggested_actions[]` deduped? | **Yes** — primary first, then secondary primaries, then secondary paths |
| ProblemRow narrative stubs? | **Yes** — `short_diagnosis_en`, `why_it_matters_en`, optional guardrails |
| Session 07 tests? | **Yes** — `tests/test_block_4_action_path_mapping.py` (**6 passed**) |

**Session 07 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| Action path mapping module | `src/block_4/action_path_mapping.py` |
| Package exports | `src/block_4/__init__.py` |
| Unit tests | `tests/test_block_4_action_path_mapping.py` |
| Spec pointer | `docs/specs/block_4_diagnosis_v2_spec.md` (Session 07 line) |

`map_action_paths(prioritization, scoring)` returns `ActionPathMappingResult` with:

- `primary_problem` / `secondary_problems` — v2 `ProblemRow`-shaped dicts
- `suggested_actions` — deduped `SuggestedActionRow` list with `priority` starting at 1
- `problem_rows` — compatibility shim tuple `[primary] + secondaries`

---

## 3. Verification

```bash
python -m pytest tests/test_block_4_action_path_mapping.py \
  tests/test_block_4_problem_prioritization.py \
  tests/test_block_4_severity_confidence.py \
  tests/test_block_4_problem_scoring.py \
  tests/test_block_4_evidence_extraction.py \
  tests/test_block_4_problem_taxonomy.py \
  tests/test_block_4_v2_contract.py tests/test_block_4_decision_entry_contract.py -q
```

**Result:** **54 passed**.

Golden fixture: primary action `improve_crisis_resilience`; demoted symptoms reflected in `do_not_overreact_reason_en`.

---

## 4. Next session

**Session 08:** Candidate Launchpad card generation (v2 fields from mapped action paths).

---

## 5. Evidence log

| Category | Detail |
| --- | --- |
| Code | `src/block_4/action_path_mapping.py` |
| Tests | `tests/test_block_4_action_path_mapping.py` |
| Ruleset | `block_4_v2_action_path_mapping_v1` |
