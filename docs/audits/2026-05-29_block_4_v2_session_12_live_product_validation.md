# Block 4 v2 Session 12 — Live Product Validation (E2E)

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 12  
Prerequisite: [Session 11 archetype fixtures](2026-05-29_block_4_v2_session_11_archetype_fixtures.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| Live v2 JSON on root `config.yml` subject? | **Yes** — refreshed via `validate_block_4_live.py --refresh-diagnosis` |
| v2 product + handoff contracts on live book? | **Yes** |
| `live_core_e2e` switched to v2 Block 4 gates? | **Yes** — `check_problem_classification_v2`, `check_candidate_launchpad_v2`, `check_block_4_v2_diagnosis_handoff` |
| Operator validator script? | **Yes** — `scripts/validate_block_4_live.py` |
| Session 12 gate | **PASS** |

**Session 12 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| Live operator validator | `scripts/validate_block_4_live.py` (`--refresh-diagnosis`) |
| Live E2E v2 gates | `src/live_core_e2e.py` → `_validate_block_4_subject_bundle` |
| Offline fixture seed → v2 | `tests/mvp_offline_fixtures.py` → `seed_analysis_subject_diagnosis_bundle` |
| Product bundle schema expectations | `PRODUCT_BUNDLE_ARTIFACTS` → v2 |
| Live validation tests | `tests/test_block_4_v2_live_validation.py` (**3 passed**) |
| Spec / runtime contract pointers | `docs/specs/block_4_diagnosis_v2_spec.md`, `docs/runtime_artifact_contract.md` |

---

## 3. Live validation contract

After diagnosis materialization (or refresh from existing subject X-Ray + stress):

```bash
python scripts/validate_block_4_live.py --refresh-diagnosis
```

Checks:

- `schema_version` = `problem_classification_v2` / `candidate_launchpad_v2`
- `ruleset_version` = `block_4_v2_2026_06`
- Primary problem row + no-trade gate + evidence_refs provenance
- Launchpad cards, disclaimer, handoff (`launchpad_outcome` ↔ PC `no_trade_outcome`)
- Cross-artifact `source_problem_id` linkage

Optional full live core gate (Block 4 evidence only when compare tombstones missing):

```bash
python scripts/verify_live_core_e2e.py --profile diagnosis_only
```

---

## 4. Live snapshot (root `config.yml`, 8 tickers, refreshed 2026-05-29)

Artifacts: `Main portfolio/analysis_subject/problem_classification.json`, `candidate_launchpad.json` (rebuilt from subject `portfolio_xray.json`, `stress_report.json`, `analysis_end=2026-04-30`).

| Field | Observed |
| --- | --- |
| PC `schema_version` | **problem_classification_v2** |
| LP `schema_version` | **candidate_launchpad_v2** |
| `ruleset_version` | **block_4_v2_2026_06** |
| `status` | **ok** |
| Primary problem | **evidence_insufficient_conflicting_signals** |
| No-trade outcome | **do_not_act_yet** |
| Secondary problems | **0** |
| Rejected problems | **12** |
| Launchpad cards | **2** |
| `hedge_gap_source` | **hedge_gap_analysis_v1** |
| `stress_scorecard_source` | **current_portfolio_stress_scorecard_v1** |

Interpretation: live book shows material pre-stress vs stress tension; Block 4 v2 correctly gates to **do not act yet** rather than forcing a misleading primary headline.

---

## 5. Verification

```bash
python scripts/validate_block_4_live.py --refresh-diagnosis
```

**Result:** Block 4 v2 live validation **OK**

```bash
python -m pytest tests/test_block_4_v2_live_validation.py \
  tests/test_block_4_decision_entry_contract.py \
  tests/test_live_core_e2e_validation.py -q
```

**Session 12 bundle:** **13 passed**

Full Block 4 migration bundle:

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
  tests/test_block_4_decision_entry_contract.py \
  tests/test_block_4_v2_live_validation.py -q
```

**Result:** **90 passed**

---

## 6. Known gaps / notes

- `verify_live_core_e2e.py --profile diagnosis_only` may fail when root `candidate_comparison.json` / compare tombstones are absent (pre-existing full-menu workspace state). Block 4 v2 evidence in that gate is valid when PC/LP files are present.
- Full `run_portfolio_review.py --skip-candidates` not re-run in Session 12; refresh path uses the same `write_block_4_diagnosis_outputs` facade as `run_report.py`.
- V1 contract tests remain in `tests/test_block_4_decision_entry_contract.py` until Session 14 freeze.

---

## 7. Next session

**Session 13:** Documentation + operator guide + `diagnostic_journey` fixes.

---

## 8. Evidence log

| Category | Detail |
| --- | --- |
| Script | `scripts/validate_block_4_live.py` |
| Live E2E | `src/live_core_e2e.py` |
| Tests | `tests/test_block_4_v2_live_validation.py` |
| Live artifacts | `Main portfolio/analysis_subject/problem_classification.json`, `candidate_launchpad.json` |
| Bundle | 90 passed (Block 4) |
