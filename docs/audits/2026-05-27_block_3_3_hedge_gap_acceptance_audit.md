# Block 3.3 Hedge Gap Analysis MVP — Acceptance Audit (Session 08)

Date: 2026-05-27

Purpose: Close [Block 3.3 Hedge Gap Analysis MVP ExecPlan](../exec_plans/2026-05-27_block_3_3_hedge_gap_analysis_plan.md) **Session 08** and record whether the product-facing `hedge_gap_analysis_v1` block is accepted on the portfolio-first diagnosis path.

Related:

- Canonical contract: [hedge_gap_analysis_spec.md](../specs/hedge_gap_analysis_spec.md)
- Stress Lab boundary: [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) §3.3
- Stress testing spec linkage: [stress_testing_spec.md](../specs/stress_testing_spec.md) §12
- Implementation: `src/hedge_gap_analysis_block.py`, wired from `src/stress.py`, `run_report.py`, `run_optimization.py`
- Operator guide: [product_flow_operator_guide.md](../product_flow_operator_guide.md) (step 3 — `analysis_subject/stress_report.json`)

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is `hedge_gap_analysis_v1` present on live portfolio-first diagnosis? | **Yes** — `run_portfolio_review.py --skip-candidates` refreshed `Main portfolio/analysis_subject/stress_report.json` with the v1 block. |
| Does Block 3.3 expose seven risk types with linked synthetic scenarios? | **Yes** — one `by_risk_type[]` row per Core MVP risk type, each mapped to its synthetic scenario. |
| Is `offset_coverage_ratio` computed wherever contribution data allows? | **Yes** — rows with available `pnl_by_asset_pct` carry `gross_loss_from_assets_hurt`, `positive_contribution_from_assets_helped`, and numeric `offset_coverage_ratio`. |
| Does the summary identify a main hedge gap and weakest/strongest protection areas? | **Yes** — `summary.main_hedge_gap`, `weakest_protection_area`, and `strongest_protection_area` are populated when ratios are available. |
| Is Core MVP in diagnostic mode without mandate fields on Block 3.3 rows? | **Yes** — `loss_gate_mode: diagnostic`; no mandate pass/fail fields on v1 rows. |
| Is the full ExecPlan accepted (Sessions 00–08)? | **Yes — 9/9** sessions complete (see §3). |

**Bottom line:** Block 3.3 Hedge Gap Analysis MVP is **complete**. Operators read contribution-based hedge gap diagnostics from `hedge_gap_analysis_v1` on subject `stress_report.json`; legacy `hedge_gap_analysis` remains for backward compatibility but product-facing flows use the v1 block.

---

## 2. Session Rollup (00–08)

| Session | Objective | Status | Primary evidence |
| --- | --- | --- | --- |
| 00 | ExecPlan foundation + field audit | **Done** | ExecPlan sections A–H |
| 01 | Product contract in specs | **Done** | Hedge Gap spec; Stress Lab renumbered (3.3 Hedge Gap) |
| 02 | Builder scaffold | **Done** | `src/hedge_gap_analysis_block.py` initial v1 builder + empty tests |
| 03 | Per-risk rows + ratio | **Done** | `by_risk_type[]` rows with hurt/helped, ratio math, concentration, diagnostics |
| 04 | Summary + narratives | **Done** | `summary.main_hedge_gap`, weakest/strongest protection, per-risk English templates |
| 05 | Wire `run_stress` + `run_report` refresh | **Done** | `attach_hedge_gap_analysis_v1` after `attach_stress_results_v1` in stress/report paths |
| 06 | Commentary/snapshot mirror (minimal) | **Done** | `portfolio_commentary.py` pointer; snapshot mirror key |
| 07 | Contract tests + regression bundle | **Done** | `test_hedge_gap_analysis_v1_contract.py`; TESTING.md Block 3.3 bundle; CHANGELOG |
| 08 | Live proof + closure | **Done** | This document; live run §5 |

---

## 3. ExecPlan Acceptance Criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `hedge_gap_analysis_v1` present on diagnosis run | **PASS** | Live `--skip-candidates`; §5.1 |
| 2 | Seven `by_risk_type[]` rows mapped to synthetic scenarios | **PASS** | Risk-type map matches spec (§5.2) |
| 3 | `offset_coverage_ratio` computed when contribution data available | **PASS** | Ratio fields populated with non-null values where `pnl_by_asset_pct` exists |
| 4 | Summary identifies `main_hedge_gap` and weakest/strongest protection | **PASS** | `summary` block on subject `stress_report.json` |
| 5 | `loss_gate_mode: diagnostic`; no mandate fields on Block 3.3 rows | **PASS** | §5.3 |
| 6 | Per-risk `diagnosis_summary_en` templates when data allows | **PASS** | §5.4 |
| 7 | Legacy `hedge_gap_analysis` preserved for compatibility | **PASS** | Present on stress engine output; v1 added alongside |
| 8 | Snapshot carries compact hedge gap mirror | **PASS** | `snapshot_10y.json` → `stress_suite_results.hedge_gap_analysis_v1` (key present) |
| 9 | Closure pytest bundle | **PASS** | **129 passed** (Block 3.3 + Stress Lab bundle) |

**Block 3.3 Hedge Gap Analysis MVP: ACCEPTED.**

---

## 4. Fixture-Locked Behavior (pytest)

Source: `tests/test_hedge_gap_analysis_v1_contract.py`, `tests/test_stress_results_block_contract.py`, `tests/test_stress_scenario_coverage_contract.py`, `tests/test_stress_diagnostic_mode.py`, `tests/test_stress_hedge_gap_contract.py`, `tests/test_stress_downstream_integration.py`.

| Check | Expected |
| --- | --- |
| `version` | `hedge_gap_analysis_v1` |
| Builder attaches from `run_stress` / `run_report.py` | Present on stress report dict after `attach_hedge_gap_analysis_v1` |
| Diagnostic mode | `loss_gate_mode: diagnostic` on v1 block; no mandate keys on product rows |
| Risk-type coverage | Seven rows in `by_risk_type[]` with canonical risk types and scenario IDs |
| Summary fields | `summary.main_hedge_gap`, `weakest_protection_area`, `strongest_protection_area` populated when ratios exist |

---

## 5. Live Verification (Session 08, root `config.yml`)

Commands (repository root, warm cache):

```bash
python run_portfolio_review.py --skip-candidates
python -m pytest tests/test_hedge_gap_analysis_v1_contract.py tests/test_stress_results_block_contract.py tests/test_stress_scenario_coverage_contract.py tests/test_stress_diagnostic_mode.py tests/test_stress_hedge_gap_contract.py tests/test_stress_downstream_integration.py -q
```

| Check | Result |
| --- | --- |
| Diagnosis-only review | Exit **0**; `product_diagnosis_only`; `analysis_subject` materialized |
| Closure pytest bundle | **129 passed** |

Artifact: `Main portfolio/analysis_subject/stress_report.json` (refreshed **2026-05-27**).

### 5.1 Block 3.3 hedge gap envelope (`hedge_gap_analysis_v1`)

| Field | Observed |
| --- | --- |
| `version` | `hedge_gap_analysis_v1` |
| `loss_gate_mode` | `diagnostic` |
| `diagnosis_method` | `contribution_based_offset_coverage_v1` |
| `scenario_library.synthetic_ids` | Includes `equity_shock`, `credit_shock`, `rates_shock`, `inflation_stagflation`, `liquidity_shock`, `usd_shock`, `commodity_shock`, `recession_severe` |

### 5.2 Per-risk `by_risk_type[]` rows

Risk-type to scenario mapping (v1 product contract):

| `risk_type` | `linked_scenario_id` |
| --- | --- |
| `equity_crash_protection` | `equity_shock` |
| `rates_up_shock_protection` | `rates_shock` |
| `stagflation_protection` | `inflation_stagflation` |
| `liquidity_shock_protection` | `liquidity_shock` |
| `usd_spike_protection` | `usd_shock` |
| `credit_shock_protection` | `credit_shock` |
| `commodity_inflation_shock_protection` | `commodity_shock` |

Each row exposes:

- `portfolio_loss_pct` aligned with linked synthetic scenario
- `assets_hurt` / `assets_helped` from signed `pnl_by_asset_pct`
- `gross_loss_from_assets_hurt`, `positive_contribution_from_assets_helped`, `offset_coverage_ratio`
- `loss_concentration.top3_share_of_gross_loss`
- `data_availability` / `data_availability_reason`
- `diagnosis_summary_en` when portfolio loss and contribution data are available

### 5.3 Diagnostic boundary

| Check | Result |
| --- | --- |
| `stress_report.json` `loss_gate_mode` | **diagnostic** |
| `hedge_gap_analysis_v1.loss_gate_mode` | **diagnostic** |
| Mandate keys on Block 3.3 product rows | **Absent** |

### 5.4 Summary fields

| Field | Behavior |
| --- | --- |
| `summary.main_hedge_gap` | Picks the weakest protection area among rows with numeric `offset_coverage_ratio` (min ratio, tie-break by more negative loss). |
| `summary.weakest_protection_area` | `risk_type` of `main_hedge_gap`. |
| `summary.strongest_protection_area` | Maximum `offset_coverage_ratio` when at least two rows have ratios; else `null`. |
| `summary.diagnosis_summary_en` | Portfolio-level narrative contrasting the main hedge gap vs stronger areas; English-only templates. |
| `summary.data_quality_warnings` | Notes when ratios are unavailable or input data is missing. |

---

## 6. Out of Scope / Deferred (documented)

| Item | Status |
| --- | --- |
| Historical-episode hedge gap rows (`linked_episode` non-null) | Deferred; v1 uses synthetic-only risk rows. |
| Mandate-mode hedge gap suitability gates | Legacy-only; Block 3.3 Core MVP remains diagnostic. |
| PDF/HTML redesign for hedge gap visuals | Post-MVP; current reports may reference Block 3.3 briefly but not as a separate redesigned section. |

---

## 7. Operator Checklist

1. Run diagnosis: `python run_portfolio_review.py --skip-candidates`
2. Open `{output_dir_final}/analysis_subject/stress_report.json` → `hedge_gap_analysis_v1`
3. Review `by_risk_type[]` rows for each protection area (equity crash, rates up, stagflation, liquidity, USD spike, credit, commodity inflation) and their `offset_coverage_ratio`.
4. Use `summary.main_hedge_gap`, `weakest_protection_area`, and `strongest_protection_area` to explain where protection is weakest vs relatively stronger.
5. For comparison flows, use `snapshot_10y.json` → `stress_suite_results.hedge_gap_analysis_v1` compact mirror when present.

---

**Closure:** ExecPlan [2026-05-27_block_3_3_hedge_gap_analysis_plan.md](../exec_plans/2026-05-27_block_3_3_hedge_gap_analysis_plan.md) marked **Completed** 2026-05-27.

