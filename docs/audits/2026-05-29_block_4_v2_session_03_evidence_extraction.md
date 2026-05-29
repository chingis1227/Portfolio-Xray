# Block 4 v2 Session 03 — Evidence Extraction Layer

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 03  
Prerequisite: [Session 02 problem taxonomy](2026-05-29_block_4_v2_session_02_problem_taxonomy.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| `extract_evidence_signals()` implemented? | **Yes** — `src/block_4/evidence_extraction.py` |
| Canonical Blocks 2.1–2.6 readers? | **Yes** — primary `evidence_path` |
| Blocks 3.3–3.4 readers? | **Yes** — hedge gap + stress scorecard with legacy fallback |
| Legacy `sections.*` fallback? | **Yes** — tagged `legacy_fallback`; sets `legacy_sections_fallback_used` |
| Session 03 tests? | **Yes** — `tests/test_block_4_evidence_extraction.py` (**6 passed**) |

**Session 03 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| Evidence extraction module | `src/block_4/evidence_extraction.py` |
| Package exports | `src/block_4/__init__.py` |
| Unit tests | `tests/test_block_4_evidence_extraction.py` |
| Spec pointer | `docs/specs/block_4_diagnosis_v2_spec.md` (Session 03 line) |

`extract_evidence_signals(portfolio_xray, stress_report)` returns `EvidenceExtractionResult` with:

- `signals`: map of taxonomy signal name → `EvidenceSignal` rows
- `signal_count`, `legacy_sections_fallback_used`, `data_quality_warnings`
- `source_provenance`: `hedge_gap_source`, `stress_scorecard_source`

Composite scoring-only signals (`conflicting_signal_bundle`, `no_material_problem`) remain for Session 04+.

---

## 3. Verification

```bash
python -m pytest tests/test_block_4_evidence_extraction.py \
  tests/test_block_4_problem_taxonomy.py \
  tests/test_block_4_v2_contract.py tests/test_block_4_decision_entry_contract.py \
  tests/test_problem_classification.py tests/test_candidate_launchpad.py -q
```

**Result:** **43 passed**.

---

## 4. Next session

**Session 04:** Evidence-to-problem scoring using extracted signals + `PROBLEM_REGISTRY` required/supporting/negative signal lists.

---

## 5. Evidence log

| Category | Detail |
| --- | --- |
| Code | `src/block_4/evidence_extraction.py` |
| Tests | `tests/test_block_4_evidence_extraction.py` |
| Fixture | `tests/fixtures/portfolio_xray_golden_v2.json` |
