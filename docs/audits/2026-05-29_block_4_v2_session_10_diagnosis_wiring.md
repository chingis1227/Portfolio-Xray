# Block 4 v2 Session 10 — JSON Wiring and Manifest

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 10  
Prerequisite: [Session 09 no-trade gate](2026-05-29_block_4_v2_session_09_no_trade_gate.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| `build_block_4_diagnosis()` facade... | **Yes** — `src/block_4/diagnosis_builder.py` |
| `write_block_4_diagnosis_outputs()`... | **Yes** — writes both bundle JSON files |
| `run_report.py` wired to v2... | **Yes** — replaces V1 write path when not `core_blocks_only` |
| Manifest `block_4_diagnosis` extra... | **Yes** — via `block_4_manifest_extra()` |
| V1 `problems[]` shim... | **Yes** — `label`, `evidence`, `medium` → `moderate` |
| Session 10 tests... | **Yes** — `tests/test_block_4_diagnosis_builder.py` (**5 passed**) |

**Session 10 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| Diagnosis facade | `src/block_4/diagnosis_builder.py` |
| Report wiring | `run_report.py` |
| Package exports | `src/block_4/__init__.py` |
| Unit tests | `tests/test_block_4_diagnosis_builder.py` |
| Spec pointer | `docs/specs/block_4_diagnosis_v2_spec.md` (Session 10 line) |

Pipeline: evidence → scoring → prioritization → action paths → no-trade gate → PC v2 + Launchpad v2 JSON.

Same filenames as V1: `problem_classification.json`, `candidate_launchpad.json` under report output dir (`analysis_subject/` when materialized).

---

## 3. Verification

```bash
python -m pytest tests/test_block_4_diagnosis_builder.py \
  tests/test_block_4_no_trade_gate.py \
  tests/test_block_4_launchpad_cards.py \
  tests/test_block_4_action_path_mapping.py \
  tests/test_block_4_problem_prioritization.py \
  tests/test_block_4_severity_confidence.py \
  tests/test_block_4_problem_scoring.py \
  tests/test_block_4_evidence_extraction.py \
  tests/test_block_4_problem_taxonomy.py \
  tests/test_block_4_v2_contract.py tests/test_block_4_decision_entry_contract.py -q
```

**Result:** **72 passed**.

---

## 4. Next session

**Session 11:** Fixtures + tests (10 portfolio archetypes).

---

## 5. Evidence log

| Category | Detail |
| --- | --- |
| Code | `src/block_4/diagnosis_builder.py`, `run_report.py` |
| Tests | `tests/test_block_4_diagnosis_builder.py` |
| Facade | `build_block_4_diagnosis_v1` |
