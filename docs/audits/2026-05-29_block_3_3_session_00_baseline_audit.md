# Block 3.3 Hedge Gap Analysis — Session 01 Baseline Audit

Date: 2026-05-29

Purpose: Establish the institutional-upgrade baseline for `hedge_gap_analysis_v1` before Session 02 (contract v1.1). Read-only audit: inventory implementation, field matrix vs target contract, legacy vs v1 consumers, Block 2.4/2.6 bridge status, live artifact spot-check, pytest baseline, and file map for Sessions 02–12.

Related:

- v1 MVP closure: [2026-05-27_block_3_3_hedge_gap_acceptance_audit.md](2026-05-27_block_3_3_hedge_gap_acceptance_audit.md)
- v1 ExecPlan (Completed): [2026-05-27_block_3_3_hedge_gap_analysis_plan.md](../exec_plans/2026-05-27_block_3_3_hedge_gap_analysis_plan.md)
- Phase 2 ExecPlan (Active): [2026-05-29_block_3_3_hedge_gap_institutional_upgrade_plan.md](../exec_plans/2026-05-29_block_3_3_hedge_gap_institutional_upgrade_plan.md)
- Product contract (v1): [hedge_gap_analysis_spec.md](../specs/hedge_gap_analysis_spec.md)
- Implementation: `src/hedge_gap_analysis_block.py`
- Decision: DEC-2026-05-27-002 (legacy retained; downstream migration trigger)

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is Block 3.3 implemented as Core MVP on `stress_report.json`... | **Yes** — `hedge_gap_analysis_v1`, eight protection rows, contribution-based offset coverage. |
| Is wiring correct (after Block 3.2, before Block 3.4)... | **Yes** — `attach_hedge_gap_analysis_v1` in `run_stress`, `_empty_report`, `run_report.py`, `run_optimization.py`. |
| Is the Phase 2 product contract complete... | **No** — missing `block_status`, `ruleset_version`, `protection_status`, row bridges, `client_diagnosis_en`, AI/candidate/problem-classification v1 paths. |
| Is main hedge gap selection institutional-grade... | **Partial** — min `offset_coverage_ratio` + loss tie-break only; no severity-weighted scoring. |
| Is Block 2.4 connected... | **Partial** — stress enrichment reads v1 summary; coarse `confirmation_status` on alert; no dedicated `hidden_exposure_confirmation` bridge object on v1. |
| Is Block 2.6 connected... | **No** — by design 2.6 does not read stress; no `weakness_map_confirmation` on v1 yet. |
| Are downstream consumers on v1... | **No** — Problem Classification and Candidate Comparison use legacy; AI Commentary has no hedge gap refs. |
| Session 01 code changes... | **None** (audit + ExecPlan registration only). |

**Bottom line:** Block 3.3 v1 MVP is **shipped and test-green**, but **not productized** for the full Core MVP decision path. Phase 2 Sessions 02–12 close contract, scoring, bridges, and downstream migration.

---

## 2. Files Inventoried

| Role | Path |
| --- | --- |
| Implementation | `src/hedge_gap_analysis_block.py` (~539 lines) |
| Upstream evidence | `src/stress_results_block.py`, `src/scenario_library.py`, `scenario_results[]` on stress report |
| Legacy parallel | `src/stress.py` (`_build_hedge_gap_analysis`, `hedge_gap_status` in conclusions) |
| Wiring | `src/stress.py` (`run_stress`), `run_report.py`, `run_optimization.py` |
| Block 3.4 consumer | `src/current_portfolio_stress_scorecard_block.py` |
| Snapshot mirror | `src/snapshot.py` → `_hedge_gap_analysis_v1_mirror_for_snapshot` |
| Block 2.4 bridge | `src/block_2_4_hidden_exposure.py` → `build_block_2_4_stress_enrichment` |
| Block 2.6 (pre-stress only) | `src/block_2_6_portfolio_weakness_map.py` — must not import stress |
| Downstream (legacy) | `src/problem_classification.py`, `src/candidate_comparison.py`, `src/portfolio_commentary.py` (exec summary legacy), `src/io_export.py` |
| Downstream (missing v1) | `src/ai_commentary_context.py` |
| E2E / validation | `src/live_core_e2e.py`, `scripts/core_mvp_validation_contract.py`, `scripts/validate_core_mvp_block3_fixture_matrix.py` |
| Spec | `docs/specs/hedge_gap_analysis_spec.md` |
| v1 tests | `tests/test_hedge_gap_analysis_v1_contract.py` |
| Legacy tests | `tests/test_stress_hedge_gap_contract.py` |
| Integration | `tests/test_stress_downstream_integration.py`, `tests/test_block_2_4_hidden_exposure.py`, `tests/test_current_portfolio_stress_scorecard_v1_contract.py` |
| Live artifact (spot-check) | `Main portfolio/analysis_subject/stress_report.json` |

---

## 3. Implemented v1 Contract (code truth)

### 3.1 Top-level keys (present)

| Field | Status |
| --- | --- |
| `version` | Present (`hedge_gap_analysis_v1`) |
| `loss_gate_mode` | Present |
| `diagnosis_method` | Present (`contribution_based_offset_coverage_v1`) |
| `scenario_library` | Present (`version`, `synthetic_ids`) |
| `by_risk_type` | Present (8 rows) |
| `summary` | Present |
| `n_risk_types` | Present (`8`) |

### 3.2 Top-level keys (Phase 2 target — missing)

| Field | Session |
| --- | --- |
| `block_status` | 02 |
| `ruleset_version` | 02 |
| `bridges` / `hidden_exposure_confirmation` | 05 |
| `weakness_map_confirmation` | 06 |

### 3.3 Per-row keys (present)

`risk_type`, `linked_scenario_id`, `linked_episode`, `scenario_type`, `portfolio_loss_pct`, `assets_hurt`, `assets_helped`, `gross_loss_from_assets_hurt`, `positive_contribution_from_assets_helped`, `offset_coverage_ratio`, `loss_concentration` (`top3_share_of_gross_loss`), `data_availability`, `data_availability_reason`, `diagnosis_summary_en`.

### 3.4 Per-row keys (Phase 2 target — missing)

| Field | Notes | Session |
| --- | --- | --- |
| `protection_type` | Alias of `risk_type` (UPG-02) | 02 |
| `scenario_id` | Alias of `linked_scenario_id` | 02 |
| `top3_loss_assets` / `top3_helped_assets` | Derived from sorted lists | 02 |
| `protection_status` | Threshold-based enum | 02–03 |
| `confirmation_status` | vs 2.4/2.6 hypotheses | 05–06 |
| `confidence`, `confidence_reason` | From data availability | 02 |
| `limitations` | Per-row cap | 02 |
| `client_diagnosis_en` | Shorter advisor copy | 02 |
| `next_decision_use` | Downstream hint enum | 02 |

### 3.5 Summary keys (present)

`main_hedge_gap` (compact: `risk_type`, `linked_scenario_id`, `offset_coverage_ratio`, `portfolio_loss_pct`), `weakest_protection_area`, `strongest_protection_area`, `diagnosis_summary_en`, `data_quality_warnings`.

### 3.6 Summary keys (Phase 2 target — missing)

`main_hedge_gap_scenario_id`, flat main hurt/helped lists, `average_offset_coverage_ratio`, `protection_profile`, `client_summary_en`, `limitations`, `main_gap_score`, `selection_reason_en`.

### 3.7 Eight protection types → scenarios (frozen)

| `risk_type` | `linked_scenario_id` |
| --- | --- |
| `equity_crash_protection` | `equity_shock` |
| `rates_up_shock_protection` | `rates_shock` |
| `stagflation_protection` | `inflation_stagflation` |
| `liquidity_shock_protection` | `liquidity_shock` |
| `usd_spike_protection` | `usd_shock` |
| `credit_shock_protection` | `credit_shock` |
| `commodity_inflation_shock_protection` | `commodity_shock` |
| `recession_severe_protection` | `recession_severe` |

Aligns with Block 2.6 `RISK_TYPES` (canonical `scenario_id` strings) via inverse map — Session 06 bridge.

**Naming note:** User brief used `commodity_inflation_protection`; implementation keeps `commodity_inflation_shock_protection` (DEC / fixture matrix, UPG-03).

---

## 4. Core Calculation Behavior (implemented)

| Behavior | Status | Evidence |
| --- | --- | --- |
| Helped = `pnl_by_asset_pct > 0` | **Yes** | `_split_hurt_helped` |
| Hurt = `pnl < 0` | **Yes** | Same |
| `offset_coverage_ratio = helped_sum / gross_hurt` | **Yes** | `_build_risk_row` L497 |
| No division when `gross_loss <= 0` | **Yes** | `insufficient_data` branches |
| No taxonomy hedge labels | **Yes** | No `risk_role` in module |
| No `src.stress` import | **Yes** | `test_module_does_not_import_stress` |
| Template English only | **Yes** | `_format_*_diagnosis_summary_en` |
| Main gap = min ratio, tie more negative loss | **Yes** | `_build_summary` L163–168 |

**Gap:** Main gap does not weight loss severity / concentration / 2.6 relevance (Session 04).

---

## 5. Live Artifact Spot-Check

Source: `Main portfolio/analysis_subject/stress_report.json` (portfolio-first subject, diagnostic mode).

| Check | Value |
| --- | --- |
| `hedge_gap_analysis_v1.version` | `hedge_gap_analysis_v1` |
| `n_risk_types` | `8` |
| `loss_gate_mode` | `diagnostic` |
| `summary.main_hedge_gap` | `equity_crash_protection` / `equity_shock`, ratio `0.0`, loss `-16.17%` |
| Legacy `hedge_gap_analysis.status` | `not_applicable` |
| `stress_conclusions.hedge_gap_status` | `not_applicable` |

**Implication:** Problem Classification using `hedge_gap_status` alone will **not** surface weak hedge on this portfolio while v1 shows zero offset on equity crash — primary migration motivator for Session 07.

---

## 6. Legacy vs v1 Consumer Inventory

| Consumer | Legacy | v1 | Priority |
| --- | --- | --- | --- |
| `stress_conclusions.hedge_gap_status` | **Yes** (mirrors legacy status) | No | Deprecate after Session 07 |
| `current_portfolio_stress_scorecard_v1` | No | **Yes** | Done |
| `snapshot.stress_suite_results` | Both keys | Compact v1 mirror | Extend Session 10 |
| `block_2_4` weak_hedge enrichment | No | **Yes** (summary + by_risk) | Enhance Session 05 |
| `portfolio_commentary` exec summary | **Yes** (full legacy block) | Pointer only (`_append_hedge_gap_analysis_v1_section`) | Session 09 |
| `problem_classification` | **Yes** (`hedge_gap_status`) | **No** | Session 07 |
| `candidate_comparison` | **Yes** (`hedge_gap_analysis` load) | **No** | Session 08 |
| `ai_commentary_context` | No | **No** | Session 09 |
| `io_export` IPS summary | **Yes** | No | Low (legacy path) |
| `live_core_e2e` required keys | Lists both | Asserts v1 key | Extend Session 10 |

---

## 7. Block 2.4 and 2.6 Bridge Status

### Block 2.4 (post-stress confirmation — partial)

- `build_block_2_4_stress_enrichment()` reads `hedge_gap_analysis_v1` → `hedge_gap_summary`, `hedge_gap_by_risk_type`.
- `weak_hedge_behavior.confirmation_status`: `preliminary` → `confirmed` when enrichment exists (not scenario-level confirmed / partially_confirmed / not_confirmed).
- Tests: `tests/test_block_2_4_hidden_exposure.py`, `tests/test_block_2_4_matrix_coverage.py` (D9).

**Gap (Session 05):** Dedicated `hidden_exposure_confirmation[]` on v1; finer rules tying 2.4 alert severity to offset coverage per scenario.

### Block 2.6 (pre-stress — no direct link)

- `block_2_6_portfolio_weakness_map` uses canonical `scenario_id` risk types; does **not** read `stress_report`.
- `tests/test_block_2_6_stress_boundary.py` enforces boundary.

**Gap (Session 06):** `weakness_map_confirmation[]` on v1 built at attach time from optional 2.6 export (read-only); must not mutate 2.6 output.

---

## 8. Gap Matrix (Phase 2)

| ID | Gap | Severity | Session |
| --- | --- | --- | --- |
| G1 | Product contract fields (`block_status`, `protection_status`, aliases, client copy) | P0 | 02–03 |
| G2 | Main hedge gap scoring v2 | P0 | 04 |
| G3 | `hidden_exposure_confirmation` bridge | P1 | 05 |
| G4 | `weakness_map_confirmation` bridge | P1 | 06 |
| G5 | Problem Classification on v1 | P0 | 07 |
| G6 | Candidate hedge gap comparison | P1 | 08 |
| G7 | `hedge_gap_context` for AI | P1 | 09 |
| G8 | Commentary exec summary legacy-first | P2 | 09 |
| G9 | OUTPUTS.md still says v1 "Target Session 02+" | P2 | 11 |
| G10 | Acceptance audit says "seven" risk types (stale) | P3 | 11 (footnote) |

---

## 9. Pytest Baseline (Session 01)

Command:

```bash
python -m pytest tests/test_hedge_gap_analysis_v1_contract.py tests/test_stress_hedge_gap_contract.py -q
```

Result (2026-05-29): **55 passed** in ~6s.

Recommended regression bundle for later sessions (from TESTING.md / plan):

- Above plus `test_stress_downstream_integration.py`, `test_problem_classification.py`, `test_ai_commentary_context.py`, `test_block_2_4_hidden_exposure.py`, `test_block_2_6_stress_boundary.py`, `test_current_portfolio_stress_scorecard_v1_contract.py`

---

## 10. File Map for Sessions 02–12

| Session | Deliverable | Primary touchpoints |
| --- | --- | --- |
| 02 | Contract v1.1 + contract tests | `hedge_gap_analysis_block.py`, `hedge_gap_analysis_spec.md`, `test_hedge_gap_analysis_v1_contract.py` |
| 03 | Calculation hardening | `hedge_gap_analysis_block.py`, tests |
| 04 | Main gap scoring v2 | `hedge_gap_analysis_block.py`, spec §summary, tests |
| 05 | 2.4 bridge | `hedge_gap_analysis_block.py`, `block_2_4_hidden_exposure.py`, wire in `portfolio_xray.py` |
| 06 | 2.6 bridge | `hedge_gap_analysis_block.py`, `attach_hedge_gap_analysis_v1` optional args, `run_portfolio_review.py` |
| 07 | Problem Classification | `problem_classification.py`, tests, DEC-2026-05-27-002 review |
| 08 | Candidate comparison | `candidate_comparison.py`, `candidate_comparison_spec.md`, integration tests |
| 09 | AI + commentary | `ai_commentary_context.py`, `portfolio_commentary.py`, tests |
| 10 | Live + e2e | `snapshot.py`, scorecard, `live_core_e2e.py`, validation scripts |
| 11 | Docs | SPEC, OUTPUTS, TESTING, CHANGELOG |
| 12 | Acceptance | Full pytest + live demo + `2026-05-29_block_3_3_institutional_acceptance_audit.md` |

---

## 11. Session 01 Closure

| Criterion | Result |
| --- | --- |
| Implementation audited | **PASS** |
| Gap list and file map documented | **PASS** |
| Legacy vs v1 consumers listed | **PASS** |
| Live subject spot-check | **PASS** |
| Pytest baseline green | **PASS** (55 passed) |
| Application code changed | **N/A** (none by design) |

**Session 01: CLOSED.** Next: Session 02 — freeze product-facing contract v1.1 with aliases and status fields.
