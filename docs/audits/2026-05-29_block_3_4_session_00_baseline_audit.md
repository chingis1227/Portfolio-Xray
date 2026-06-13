# Block 3.4 Current Portfolio Stress Scorecard — Session 00 Baseline Audit

Date: 2026-05-29

Purpose: Establish the institutional-upgrade baseline for `current_portfolio_stress_scorecard_v1` before Session 01 (contract v1.1). Read-only audit: field matrix vs target contract, legacy vs v1 consumer inventory, worst-scenario source, forbidden-key scan, live artifact spot-check, pytest baseline, test-theme coverage map.

Related:

- MVP closure: [2026-05-27_block_3_4_current_portfolio_stress_scorecard_acceptance_audit.md](2026-05-27_block_3_4_current_portfolio_stress_scorecard_acceptance_audit.md)
- MVP ExecPlan (Completed): [2026-05-27_block_3_4_current_portfolio_stress_scorecard_plan.md](../exec_plans/2026-05-27_block_3_4_current_portfolio_stress_scorecard_plan.md)
- Phase 2 ExecPlan (Active): [2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md)
- Implementation: `src/current_portfolio_stress_scorecard_block.py` (~465 lines)
- Block 3.3 prerequisite: [2026-05-29_block_3_3_institutional_upgrade_acceptance_audit.md](2026-05-29_block_3_3_institutional_upgrade_acceptance_audit.md)

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is Block 3.4 implemented on `stress_report.json`... | **Yes** — `current_portfolio_stress_scorecard_v1`, adapter over `stress_results_v1` + `hedge_gap_analysis_v1`. |
| Is wiring correct (after 3.2 and 3.3)... | **Yes** — `attach_current_portfolio_stress_scorecard_v1` in `src/stress.py` (`run_stress`, `_empty_report`), `run_report.py`, `run_optimization.py`. |
| Is the Phase 2 v1.1 product contract complete... | **No** — missing `block_status`, `ruleset_version`, `stress_diagnosis`, `diagnosis_confidence`, `hedge_gap_summary`, `pre_stress_confirmation_summary`, downstream signals, `next_decision_uses[]`, boolean `legacy_fallback_used`. |
| Are downstream consumers v1-primary... | **No** — Problem Classification, AI Commentary refs, Candidate Comparison stress bundle, and snapshot still prefer or only expose `stress_scorecard_v1`. |
| Is worst-scenario logic correct at MVP... | **Yes (via Block 3.2 envelope)** — scorecard reads `stress_results_v1.envelope.worst_synthetic` / `worst_historical`; contract test asserts parity. |
| Session 00 code changes... | **None** (audit + ExecPlan registration only). |

**Bottom line:** Block 3.4 MVP is **shipped and test-green (4 tests)**, but **not productized** for institutional v1.1 or full Core MVP decision path. Phase 2 Sessions 01–13 close contract, diagnosis object, bridges, downstream migration, and live-output gates.

---

## 2. Files Inventoried

| Role | Path |
| --- | --- |
| Implementation | `src/current_portfolio_stress_scorecard_block.py` |
| Upstream | `src/stress_results_block.py`, `src/hedge_gap_analysis_block.py`, `scenario_results[]`, `historical_results[]` on stress report |
| Legacy parallel | `src/stress.py` (`_build_stress_scorecard_v1`, mandate/diagnostic rows) |
| Wiring | `src/stress.py`, `run_report.py`, `run_optimization.py` |
| Downstream (legacy-primary) | `src/problem_classification.py`, `src/ai_commentary_context.py`, `src/candidate_comparison.py`, `src/snapshot.py`, `src/portfolio_commentary.py`, `src/data_trust_signals.py` |
| Downstream (partial v1) | `src/live_core_e2e.py` (reads 3.4 for evidence only) |
| Validation | `scripts/core_mvp_validation_contract.py` (presence key only; no `check_current_portfolio_stress_scorecard_v1` yet), `scripts/validate_core_mvp_block3_fixture_matrix.py` |
| Spec | `docs/specs/stress_lab_layer_spec.md` §3.4 (no dedicated scorecard spec file yet) |
| Tests | `tests/test_current_portfolio_stress_scorecard_v1_contract.py` (4 tests) |
| Fixtures | `tests/mvp_offline_fixtures.py` (builds 3.4 after synthetic stress_report) |
| Live artifact | `Main portfolio/analysis_subject/stress_report.json` |

---

## 3. Implemented MVP Contract (code truth)

### 3.1 Top-level keys (present on successful build)

| Field | Status |
| --- | --- |
| `version` | `current_portfolio_stress_scorecard_v1` |
| `block` | `"3.4"` |
| `loss_gate_mode` | Copied from stress report (`diagnostic` / `mandate`) |
| `scenario_library` | From `stress_results_v1` or hedge gap |
| `worst_synthetic_scenario` | From envelope; `availability`, `scenario_id`, `portfolio_loss_pct` |
| `worst_historical_scenario` | From envelope; `episode`, `portfolio_loss_pct`, `drawdown_pct` |
| `portfolio_loss_summary` | Synthetic PnL + historical `pnl_real_episode` |
| `historical_drawdown_summary` | `max_dd` from worst historical |
| `top_loss_contributors` | Synthetic + historical `top3_loss_assets` |
| `top_risk_contributors` | RC from worst synthetic row in `stress_results_v1.synthetic_scenarios[]` |
| `factor_stress_attribution_summary` | `top_factor_drivers` + `helped_factors` from conclusions |
| `assets_helped_hurt_summary` | Worst synthetic helped/hurt + hedge-gap main area |
| `offset_coverage_summary` | From `hedge_gap_analysis_v1` main row |
| `main_hedge_gap` | Weakest/strongest area + nested `main_hedge_gap` |
| `data_quality_warnings` | Trust + hedge gap + conclusions + historical partial count |
| `diagnosis_summary_en` | Template string from worst syn/hist + main gap |
| Optional meta | `hedge_gap_ruleset_version`, `hedge_gap_block_status`, `protection_profile` when 3.3 v1 present |

### 3.2 Top-level keys (Phase 2 target — missing)

| Field | Target session |
| --- | --- |
| `block_status` | 02 |
| `ruleset_version` | 02 |
| `scorecard_scope` | 01–02 |
| `source_blocks_used` | 02 |
| `stress_coverage` | 03 |
| `legacy_fallback_used` (boolean) | 02 |
| `limitations` | 02 |
| `loss_contribution_summary` / `risk_contribution_summary` | 04 |
| `hedge_gap_summary` (incl. `main_hedge_gap_scenario_id`) | 05 |
| `stress_diagnosis` (+ `diagnosis_confidence`) | 06 |
| `relatively_resilient_scenarios` / `less_damaging_scenarios` | 06 |
| `pre_stress_confirmation_summary` | 07 |
| `problem_classification_signals` | 08 |
| `candidate_comparison_targets` | 09 |
| `ai_commentary_context` (nested) | 10 |
| `next_decision_uses[]` | 06 |

### 3.3 Worst-scenario source (explicit)

| Selector | Rule | Implementation |
| --- | --- | --- |
| Worst synthetic | Min synthetic `portfolio_pnl_pct` / loss | **Not recomputed in 3.4** — `_build_worst_synthetic_block(stress_results_v1.envelope.worst_synthetic)` |
| Worst historical | Min historical `max_dd` | **Not recomputed in 3.4** — `_build_worst_historical_block(envelope.worst_historical)` |

Envelope ownership: Block 3.2 (`stress_results_block.py`). Contract test `test_worst_selectors_use_required_rules` locks parity.

### 3.4 Forbidden keys inside Block 3.4 product object

Contract test `test_no_mandate_pass_fail_language_inside_block` forbids: `pass`, `loss_ok`, `max_dd_limit`, `diagnostic_codes`, `primary_diagnostic_code`, `fail_reason_code`, `failed_scenario`, `failed_test`.

**Not yet tested:** phrase scan for “passes normally” (Session 06).

---

## 4. Consumer Inventory: `stress_scorecard_v1` vs `current_portfolio_stress_scorecard_v1`

| Consumer | Reads v1 (3.4) | Reads legacy | Phase 2 action |
| --- | --- | --- | --- |
| `problem_classification._collect_stress` | No | **Yes** (`overall_status`, confidence) | Session 08 — v1-primary |
| `ai_commentary_context._stress_refs` | No | **Yes** (`overall_status`) | Session 10 — v1 refs + nested context |
| `candidate_comparison` stress sidecar | No | **Yes** (`stress["scorecard"]`) | Session 09 — v1 slice + targets |
| `snapshot.py` stress suite | No | **Yes** (`scorecard` mirror) | Session 11 — prefer v1 |
| `portfolio_commentary` stress section | No | **Yes** | Session 10 |
| `data_trust_signals` | No | **Yes** (param name) | Review in Session 12 (may stay legacy param) |
| `live_core_e2e.py` | **Partial** (main gap risk_type evidence) | Listed in required keys | Session 11 — v1.1 gates |
| `core_mvp_validation_contract.py` | Key presence only | — | Session 11 — `check_*` helper |
| `current_portfolio_stress_scorecard_block` | N/A (builder) | Reads 3.2/3.3 only | — |
| Block 2.4 / 2.6 | No import of 3.4 | — | Session 07 attach only |

**Note:** `hedge_gap_analysis_v1` was migrated v1-primary in Problem Classification (Session 07 of Block 3.3 plan). Block 3.4 stress **scorecard** migration is still open.

---

## 5. Test-Theme Coverage Map (user requirements → baseline)

| # | Theme | MVP coverage | Gap / session |
| --- | --- | --- | --- |
| 1 | Contract integrity | Partial — MVP keys + forbidden mandate keys | 02, 13 |
| 2 | Worst scenario logic | **Yes** — envelope parity test | 03 (`stress_coverage`, edge cases) |
| 3 | Loss contribution | Partial — `top_loss_contributors` only | 04 concentration + aliases |
| 4 | Risk contribution | Partial — `top_risk_contributors`, no overlap flag | 04 |
| 5 | Factor attribution | Partial — drivers + helped_factors | 05 limitations + diagnosis |
| 6 | Hedge gap integration | **Yes** — copies 3.3 main gap; no `hedge_gap_summary` object | 05 |
| 7 | Pre-stress confirmation | **No** | 07 |
| 8 | Problem Classification | **No** (uses legacy scorecard) | 08 |
| 9 | Candidate Comparison | **No** | 09 |
| 10 | AI Commentary | **No** (legacy ref only) | 10 |
| 11 | Materialization | Partial — fixture matrix lists key; weak E2E | 11 |
| 12 | Backward compatibility | **Yes** — separate keys; 4 contract tests | 02 aliases |
| 13 | Live-output + language | **No** | 06, 11, 13 |
| 14 | diagnosis_confidence + next_decision_uses[] | **No** | 01, 06 |
| 15 | 2.4/2.6 graceful degradation | **No** | 01, 07 |

---

## 6. Live Artifact Spot-Check

**Path:** `Main portfolio/analysis_subject/stress_report.json`  
**`generated_at`:** `2026-05-29T12:56:19.317037` (may be stale vs latest code; refresh before Session 13 closure.)

| Check | Result |
| --- | --- |
| `current_portfolio_stress_scorecard_v1` present | **Yes** |
| `stress_results_v1` present | **Yes** |
| `hedge_gap_analysis_v1` present | **Yes** |
| `stress_scorecard_v1` present | **Yes** (legacy parallel) |
| Worst synthetic `scenario_id` | `recession_severe` (`portfolio_loss_pct` -0.2118) |
| Matches `stress_results_v1.envelope.worst_synthetic.scenario_id` | **Yes** |
| Worst historical `episode` | `2022` (`drawdown_pct` -0.1976) |
| `block_status` on 3.4 | **Absent** (expected until Session 02) |
| `stress_diagnosis` | **Absent** |
| `legacy_fallback_used` | **Absent** |
| `hedge_gap_analysis_v1.block_status` / `ruleset_version` on disk | **Absent** — subject file likely from run before Block 3.3 Phase 2 refresh; re-run review before closure live gates |

**Excerpt (MVP keys only):** 16 top-level fields under `current_portfolio_stress_scorecard_v1` per §3.1.

---

## 7. Pytest Baseline

Command (repo root):

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py -q
```

Result (2026-05-29): **4 passed** in ~4.9s

| Test | What it proves |
| --- | --- |
| `test_block_exists_and_has_required_keys` | MVP key set on `run_stress` output |
| `test_linkage_to_block_3_2_and_3_3` | Scenario library linkage |
| `test_worst_selectors_use_required_rules` | Envelope parity for worst syn/hist |
| `test_no_mandate_pass_fail_language_inside_block` | No forbidden mandate keys inside 3.4 |

**Not in bundle yet:** loss concentration, diagnosis_confidence, next_decision_uses, pre-stress bridge, live-output validator, forbidden phrase scan.

---

## 8. Gap IDs for Phase 2 (G1–G15)

| ID | Gap | Session |
| --- | --- | --- |
| G1 | No `block_status` / `ruleset_version` | 02 |
| G2 | No boolean `legacy_fallback_used` | 02 |
| G3 | No `stress_diagnosis` / `diagnosis_confidence` | 06 |
| G4 | No `next_decision_uses[]` | 06 |
| G5 | No `hedge_gap_summary.main_hedge_gap_scenario_id` | 05 |
| G6 | No `pre_stress_confirmation_summary` | 07 |
| G7 | PC not v1-primary for stress scorecard | 08 |
| G8 | CC not v1-primary | 09 |
| G9 | AI not v1-primary | 10 |
| G10 | Snapshot legacy scorecard mirror | 11 |
| G11 | No `check_current_portfolio_stress_scorecard_v1` validator | 11 |
| G12 | No live-output acceptance gates | 11, 13 |
| G13 | No dedicated `current_portfolio_stress_scorecard_spec.md` | 01 |
| G14 | No loss/risk summary v1.1 names + concentration | 04 |
| G15 | Committed subject stress may predate 3.3 v1.1 fields | Refresh at closure |

---

## 9. Session 00 Acceptance

- [x] Field matrix MVP vs v1.1 documented
- [x] Consumer table legacy vs v1 documented
- [x] Worst-scenario source = `stress_results_v1.envelope` documented
- [x] Forbidden mandate keys baseline documented
- [x] Live artifact spot-check with `generated_at` noted
- [x] Pytest baseline **4 passed**
- [x] 15 test themes mapped
- [x] No `src/` changes

**Next chat:** Session 01 — freeze `docs/specs/current_portfolio_stress_scorecard_spec.md` (v1.1), including `diagnosis_confidence`, `next_decision_uses[]`, language rules, 2.4/2.6 degradation, mandate boundary.
