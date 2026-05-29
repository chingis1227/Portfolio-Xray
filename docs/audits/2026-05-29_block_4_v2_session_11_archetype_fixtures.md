# Block 4 v2 Session 11 — Archetype Fixtures and Regression Tests

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 11  
Prerequisite: [Session 10 diagnosis wiring](2026-05-29_block_4_v2_session_10_diagnosis_wiring.md)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| Ten portfolio archetype fixtures? | **Yes** — `tests/block_4_fixtures.py` + `tests/fixtures/block_4/archetype_manifest.json` |
| End-to-end `build_block_4_diagnosis()` per archetype? | **Yes** — `tests/test_block_4_v2_archetype_fixtures.py` (**15 passed**) |
| v2 product + handoff contracts on every archetype? | **Yes** |
| Session 11 gate | **PASS** (10/10 archetypes; 100% fixture assertions) |

**Session 11 verdict:** **PASS**

---

## 2. Deliverables

| Item | Location |
| --- | --- |
| Archetype builders + stress helpers | `tests/block_4_fixtures.py` |
| Manifest (expected primary / outcome) | `tests/fixtures/block_4/archetype_manifest.json` |
| Parametrized E2E tests | `tests/test_block_4_v2_archetype_fixtures.py` |
| Pytest marker | `pytest.ini` → `block_4_v2` |
| Spec pointer | `docs/specs/block_4_diagnosis_v2_spec.md` |

---

## 3. Archetype matrix

| Archetype | Expected primary (allowed set) | No-trade outcome |
| --- | --- | --- |
| `concentrated_equity` | `high_concentration` | `proceed_to_launchpad` |
| `balanced_60_40` | `current_portfolio_acceptable` | `monitor` or `proceed_to_launchpad` |
| `duration_heavy_bonds` | `duration_rates_vulnerability`, `poor_rates_up_behavior` | `proceed_to_launchpad` |
| `high_credit_carry` | `credit_liquidity_fragility`, `weak_crisis_resilience` | `proceed_to_launchpad` |
| `pseudo_diversified_equity_etfs` | `poor_diversification`, `high_equity_beta` | `proceed_to_launchpad` |
| `cash_heavy_conservative` | `current_portfolio_acceptable` | `monitor` or `proceed_to_launchpad` |
| `weak_hedge` | `weak_crisis_resilience`, `weak_hedge_behavior` | `proceed_to_launchpad` |
| `insufficient_data` | `evidence_insufficient_data_quality` | `do_not_act_yet` |
| `conflicting_signals` | `evidence_insufficient_conflicting_signals` | `do_not_act_yet` |
| `acceptable_no_action` | `current_portfolio_acceptable` | `monitor` |

Per-fixture assertions: primary id, gate outcome, ≤2 secondaries, evidence_refs provenance, v2 PC + Launchpad contracts, handoff, launchpad suppression rules.

---

## 4. Verification

```bash
python -m pytest tests/test_block_4_v2_archetype_fixtures.py -q
```

**Archetype bundle:** **15 passed**

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
  tests/test_block_4_decision_entry_contract.py -q
```

**Result:** **87 passed**

---

## 5. Known gaps / notes

- `balanced_60_40` and `cash_heavy_conservative` allow `proceed_to_launchpad` in the manifest when materiality is borderline; tests require `launchpad_may_proceed=False` so monitor paths suppress Launchpad.
- `high_credit_carry` may elevate `weak_crisis_resilience` when credit stress loss is material; both ids are accepted as primary.
- Live `run_portfolio_review.py` validation remains **Session 12**.

---

## 6. Next session

**Session 12:** Product validation run (live E2E).

---

## 7. Evidence log

| Category | Detail |
| --- | --- |
| Fixtures | `tests/block_4_fixtures.py`, `tests/fixtures/block_4/archetype_manifest.json` |
| Tests | `tests/test_block_4_v2_archetype_fixtures.py` |
| Bundle | 87 passed (Block 4) |
