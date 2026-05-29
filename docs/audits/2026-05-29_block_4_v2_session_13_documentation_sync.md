# Block 4 v2 Session 13 — Documentation Sync + Operator Guide + Diagnostic Journey

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 13  
Prerequisite: [Session 12 live product validation](2026-05-29_block_4_v2_session_12_live_product_validation.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| SPEC / OUTPUTS updated for v2 writers? | **Yes** |
| Operator guide Block 4 v2 section? | **Yes** — `docs/product_flow_operator_guide.md` |
| TESTING.md regression bundle? | **Yes** |
| `diagnostic_journey` v2 field mapping? | **Yes** — `suggested_methods`, v2 copy fields, primary diagnosis callout |
| Session 13 gate | **PASS** |

**Session 13 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| Root contract sync | `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, `CHANGELOG.md` |
| Operator guide | `docs/product_flow_operator_guide.md` § Block 4 v2 diagnosis |
| Runtime artifact contract | `docs/runtime_artifact_contract.md` (Session 12) |
| Module specs (V2 shipped pointers) | `docs/specs/problem_classification_spec.md`, `candidate_launchpad_spec.md`, `block_4_diagnosis_v2_spec.md` |
| Diagnostic journey UX | `docs/specs/diagnostic_journey_ux_draft.md` |
| View model + template | `diagnostic_journey/view_model.py`, `diagnostic_journey/templates/journey.html` |
| Tests | `tests/test_diagnostic_journey_view_model.py` (+3 v2 bridge tests) |

---

## 3. Diagnostic journey fixes

| Gap (Session 00) | Fix |
| --- | --- |
| Read `candidate_methods` instead of `suggested_methods` | `_launchpad_method_ids()` prefers `suggested_methods[]` with `candidate_method_id`; legacy keys retained as fallback |
| Missing v2 problem headline in bridge | `_bridge_diagnosis_from_problem()` reads `primary_problem` + `no_trade_or_monitoring_view` |
| Missing v2 card copy | `_bridge_card_from_launchpad()` uses `why_this_path_en`, `what_this_tests_en`, `title`, `description`, `default_method` |

Template: primary problem callout on `#bridge` when `problem_classification_v2` is present.

---

## 4. Verification

```bash
python -m pytest tests/test_diagnostic_journey_view_model.py tests/test_block_4_v2_live_validation.py \
  tests/test_block_4_v2_archetype_fixtures.py tests/test_block_4_v2_contract.py -q
```

Full Block 4 migration bundle (Session 13):

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
  tests/test_block_4_v2_contract.py \
  tests/test_block_4_v2_archetype_fixtures.py \
  tests/test_block_4_v2_live_validation.py \
  tests/test_block_4_decision_entry_contract.py \
  tests/test_diagnostic_journey_view_model.py -q
```

**Result:** **95 passed**

---

## 5. Known gaps / deferred

- V1 validators and builders remain until **Session 14** freeze (`DEC-2026-05-29-013`).
- Diagnostic journey CTA “Open in Builder” remains disabled (product wiring out of scope).
- `diagnostic_journey` CSS for `.diagnosis-callout` uses existing journey card styles only (no new design tokens).

---

## 6. Next session

**Session 14:** Final audit and V1 validator removal / freeze.

---

## 7. Evidence log

| Category | Detail |
| --- | --- |
| Docs | SPEC, OUTPUTS, TESTING, operator guide, module specs |
| UI bridge | `diagnostic_journey/view_model.py`, `journey.html` |
| Tests | `tests/test_diagnostic_journey_view_model.py` |
