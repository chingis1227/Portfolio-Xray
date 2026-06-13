# Stress Lab Methodology Map (Block 3)

Date: 2026-05-20

Status: **Historical** — Phase 13 governance wave closed 2026-05-20 (Sessions 00–11). Baseline checklist:
[Stress Lab Baseline Snapshot](2026-05-20_stress_lab_baseline_snapshot.md).

Scope: current-portfolio stress diagnostics (Block 3). Builds on the completed
[Stress Lab Post-Audit Roadmap](../exec_plans/2026-05-20_stress_lab_post_audit_roadmap.md)
(Sessions 00–10) and the 2026-05-20 methodology audit.

This document is project memory for methodology transparency. It does not override canonical specs or
current code behavior.

Governance plan (closed): [Stress Lab Methodology Governance Plan](../exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md).

## Provenance legend

| Code | Meaning |
| --- | --- |
| **C** | Existing code behavior |
| **S** | Existing canonical spec |
| **A** | Generated artifact evidence |
| **T** | Target product concept (partially implemented) |
| **P** | NEW METHODOLOGY PROPOSAL — requires spec decision before implementation |

## Executive summary

Stress Test Lab is the **diagnostic stress layer** centered on `stress_report.json` under
`{output_dir_final}/analysis_subject/` after `run_report.py --materialize-analysis-subject`.

**Core question:** Where can the portfolio break, under which scenarios, why does it lose money, which
assets pull it down, which protect it, where are hedge gaps, and how much can we trust the result...

**Maturity (2026-05-20, post Sessions 00–11):** audit-grade for methodology handoff. Scorecard,
conclusions, hedge gap v2 (`by_risk_type[]`), crisis replay v2, historical methodology disclosure,
factor drivers in conclusions, layer spec, optional custom-shock persistence, and downstream mirrors
(snapshot, comparison, commentary) are shipped. Governance gaps G1–G10 closed (G8 deferred per
DEC-2026-05-20-002).

**Strongest:** eight synthetic + five historical scenarios; linear factor-beta shock engine with
explicit `synthetic_assumptions`; taxonomy_blend_v1 RC diagnostics; historical data-quality fields;
`stress_scorecard_v1` / `stress_conclusions`; crisis replay paths; hedge gap evidence v1; custom
shock simulator API; stress commentary with mandate boundary wording.

**Boundary:** Stress suite is **diagnostic-only** — does not release/block weights. Mandate max drawdown
gate is separate (`FAIL_MANDATE` in optimization). **C** **S** `stress_testing_spec.md` §0.

Primary artifact: `Main portfolio/analysis_subject/stress_report.json` (**A**).

## Architecture

```text
monthly returns + weekly asset/portfolio betas + factor history + taxonomy risk_role
  -> run_stress (src/stress.py)
  -> stress_report.json (+ scorecard, conclusions, hedge_gap, historical_episode_paths)
  -> build_scenario_library / normalized (src/scenario_library*.py)
  -> stress_scenario_analytics (src/stress_scenario_analytics.py)
  -> stress_commentary.txt (src/portfolio_commentary.py)
  -> snapshot_10y.stress_suite_results (src/snapshot.py)
```

Orchestration: [run_report.py](../../run_report.py) stress block (~lines 620–1400).

## Sub-block map

### 3.1 Scenario Library

**Question:** Which scenarios exist, with what inputs, shocks, and readiness metadata...

| Element | Rule | Provenance |
| --- | --- | --- |
| Synthetic IDs (8) | `equity_shock`, `credit_shock`, `rates_shock`, `inflation_stagflation`, `liquidity_shock`, `usd_shock`, `commodity_shock`, `recession_severe` | **C** `SCENARIOS` + calibration in `src/stress.py` **S** §2 |
| Historical IDs (5) | `dotcom`, `2008`, `2020`, `2022`, `banking_2023` | **C** `HISTORICAL_EPISODES` **S** §9 |
| Shock sizes | Hard-coded in `SCENARIOS`; override via `config.stress_scenario_overrides` | **C** **S** §2 |
| Library version | `scenario_library_v1` | **C** `src/scenario_library.py` **S** scenario_library_spec |
| Normalized view | Readiness classification; historical proxy waterfall separate from primary stress | **C** **S** scenario_library_spec |
| Version tracking | `synthetic_assumptions_v1`, `calibrated_v1_assumptions` (RC taxonomy) | **C** **S** §2.2, §4 |

**Artifacts:** `scenario_library.json`, `scenario_library_normalized.json`, CSV summaries/warnings (**A**).

**Tests:** `tests/test_scenario_library.py`, `tests/test_scenario_library_normalized.py`,
`tests/test_stress_scenario_coverage_contract.py`.

### 3.1.1 Historical Scenarios

**Question:** How did the portfolio behave in past crises (realized)...

| Element | Rule | Provenance |
| --- | --- | --- |
| Frequency | Monthly simple returns, fixed weights at analysis date | **C** **S** metrics_spec |
| Pass/fail | Episode **max drawdown** vs `max_dd_limit` | **C** **S** §9 |
| Alignment | `dropna(how="any")` on episode window — all assets must have return | **C** |
| Data quality | `n_obs`, `n_expected_obs`, `coverage_ratio`, `data_quality` buckets | **C** **S** §9.2 |
| Factor attribution | Post-run enrichment: 5Y betas × realized weekly factor shock sum; model-based, not causal | **C** **S** §8.7 |
| Proxy in primary stress | **None** — realized only in `run_stress` | **C** |
| Proxy in library normalized | Waterfall: direct → ticker proxy → asset-class → factor replay | **C** **S** historical_stress_fallback |

**Representative evidence (analysis_subject):** dotcom/2008 `insufficient_data` (young ETFs); 2020/2022/banking_2023 `reliable` (**A**).

**Misleading risk:** null episodes look like missing analysis, not zero loss; young ETF strict join (**G2**).

### 3.1.2 Synthetic Scenarios

**Question:** What happens under hypothetical factor shocks...

| Element | Rule | Provenance |
| --- | --- | --- |
| Engine | `r_i = Σ beta_{i,k} * shock_k`; `PnL_i = w_i * r_i` | **C** **S** §2 |
| Betas | Weekly 5Y asset betas; missing row → `shock_eq` proxy | **C** |
| Portfolio factor PnL | `shock_k * beta_portfolio_k` (6 production factors) | **C** **S** §2 |
| RC diagnostics | `taxonomy_blend_v1` on stressed covariance; **does not** change scenario PnL | **C** **S** §2.2, §10 |
| recession_severe | Calibrated from 2008/2020 weekly factor sums; worst model PnL vs 5Y betas | **C** **S** §2.1 |
| Pass/fail | `portfolio_pnl_pct >= -max_dd_limit` → `DIAG_LOSS_*` if fail | **C** **S** §1, §5 |
| Absent scenarios | `crypto_shock`, `volatility_shock` — X-Ray weakness only; **deferred** in `run_stress` ([DEC-2026-05-20-002](../../DECISIONS.md), proposal P4) | **C** **S** §2.3 **P** |

**Artifacts:** `scenario_results[*]` with `synthetic_assumptions`, taxonomy metadata (**A**).

**Tests:** `tests/test_stress_mandate_pass.py`, `tests/test_stress_covariance_taxonomy.py`,
`tests/test_stress_synthetic_assumptions_contract.py`, `tests/test_stress_simulator_contract.py`.

### 3.2 Stress Conclusions

**Question:** Worst case, drivers, confidence, hedge status — without parsing all scenario rows...

| Element | Rule | Provenance |
| --- | --- | --- |
| Worst synthetic | `min(portfolio_pnl_pct)` over `scenario_results` | **C** **S** §12.1 |
| Worst historical | `min(max_dd)` among rows with computed `max_dd` — aligned with pass/fail | **C** **S** §12.1 |
| Top loss assets | `top3_loss_assets` from worst synthetic row | **C** **S** §12.1 |
| Helped assets | Up to 3 assets with positive PnL in worst synthetic scenario | **C** **S** §12.1 |
| Factor drivers | **In conclusions** — `top_factor_drivers_worst_scenario`, `helped_factors_worst_scenario` from worst synthetic `pnl_by_factor_pct` | **A** ~~G4~~ closed Session 04 |
| Confidence | Worst of beta_confidence (synthetic) and historical data_quality | **C** **S** §12.1 |
| Mandate boundary | Commentary states stress is non-binding vs mandate gates | **C** **S** §0 |

**Artifacts:** `stress_conclusions_v1`, `stress_commentary.txt` (**A**).

**Tests:** `tests/test_stress_scorecard_contract.py`, `tests/test_portfolio_commentary.py`.

### 3.3 What Happens If... Simulator

**Question:** Custom shock vectors with same math as built-in scenarios...

| Element | Rule | Provenance |
| --- | --- | --- |
| Status | API implemented; **no UI**; **no default artifact write** | **C** **S** §12.3 |
| Functions | `simulate_custom_shock`, `shock_vector_from_scenario` | **C** |
| Engine | Same linear map as synthetic rows; no RC / pass-fail | **C** **S** §12.3 |
| Validation | Unknown scenario_id → KeyError; vix/oil not in shock keys | **C** |

**Tests:** `tests/test_stress_simulator_contract.py` (PnL equivalence to built-in rows).

**Artifact (opt-in):** `custom_shock_runs.json` via `record_custom_shock_run` (**A** Session 09); not
written by `run_stress`.

### 3.4 Crisis Replay

**Question:** Month-by-month crisis path, not aggregate only...

| Element | Rule | Provenance |
| --- | --- | --- |
| Status | v2 (`crisis_replay_v2`) — path + recovery + static asset contrib | **C** **S** crisis_replay_spec |
| Rows | `date`, `portfolio_return`, `equity`, `drawdown` | **C** **S** |
| Recovery | `time_to_recovery_months`, `recovered` (metrics_spec §6.9) | **C** **S** Session 06 |
| Asset contrib | `asset_pnl_contrib_episode`, `top_loss_assets_episode`; CSV `_asset_contrib` | **C** **S** Session 06 |
| Acceptance | Path max_dd == aggregate `historical_results.max_dd`; CSV rows == n_obs | **C** **S** |
| Not implemented | Per-asset path through time, factor path replay | **T** |

**Artifacts:** `historical_episode_paths`, `results_csv/crisis_replay_{episode}.csv` (**A**).

**Tests:** `tests/test_stress_historical_fields.py`.

### 3.5 Hedge Gap Analysis

**Question:** Do hedge-labeled holdings fail to protect in stress...

| Element | Rule | Provenance |
| --- | --- | --- |
| Method | `stress_scenario_hedge_evidence_v2` (aggregate + `by_risk_type[]`) | **C** **S** hedge_gap_analysis_spec |
| Hedge labels | Taxonomy `risk_role`: crisis_hedge, defensive, inflation_hedge, tail_hedge | **C** **S** §12.2 |
| Evaluation | Global worst synthetic + per `risk_type` worst mapped scenario (`HEDGE_GAP_SCENARIO_BY_RISK`) | **C** **S** Session 05 |
| Status | Aggregate + per-type: `gap_detected` \| `no_gap_detected` \| `insufficient_data` \| `not_applicable` | **C** **S** |
| N/A disclosure | `status_reason` / `status_reason_en`; `no_hedge_labels` → `not_applicable` | **C** **S** Session 03 |
| Per-type mapping | `by_risk_type[]`, `any_risk_type_gap_detected`; aligned with `WEAKNESS_SCENARIO_MAP` | **C** **S** Session 05 |

**Representative evidence:** current portfolio `n_hedge_assets_considered=0` → `not_applicable` + `no_hedge_labels` (**A**).

**Tests:** `tests/test_stress_hedge_gap_contract.py`.

### 3.6 Current Portfolio Stress Scorecard

**Question:** Unified machine-readable stress summary...

| Element | Rule | Provenance |
| --- | --- | --- |
| Contract | `stress_scorecard_v1` with synthetic + historical rows, severity, confidence | **C** **S** §12.1 |
| Scope | Any portfolio passed to `run_stress` (subject, candidates, variants) | **C** |
| Consumers | snapshot, commentary, candidate_comparison; health/robustness use simplified overall | **C** |
| Factor drivers in scorecard | Scorecard rows still RC + loss assets only; factor **why** surfaced via `stress_conclusions.top_factor_drivers_worst_scenario` (Session 04) | **C** **A** |

**Artifacts:** `stress_scorecard_v1` in stress_report; mirror in `snapshot_10y.stress_suite_results` (**A**).

**Tests:** `tests/test_stress_scorecard_contract.py`, `tests/test_stress_artifacts_priority.py`.

## Cross-block gaps (Phase 13 — closed 2026-05-20)

| ID | Gap | Priority | Target session |
| --- | --- | --- | --- |
| G1 | ~~Worst historical in conclusions uses pnl not max_dd~~ | Closed Session 01 | — |
| G2 | ~~Historical realized vs proxy boundary not explicit in primary rows~~ | Closed Session 02 | — |
| G3 | ~~Hedge `insufficient_data` ambiguous when no taxonomy labels~~ | Closed Session 03 | — |
| G4 | ~~Factor drivers absent from stress_conclusions / scorecard header~~ | Closed Session 04 | — |
| G5 | ~~Hedge gap only worst synthetic, not per risk type~~ | Closed Session 05 | — |
| G6 | ~~Crisis replay lacks recovery + asset episode contrib~~ | Closed Session 06 | — |
| G7 | ~~stress_lab_layer_spec.md too shallow for handoff~~ | Closed Session 07 | — |
| G8 | ~~crypto/vol synthetic scenarios not in run_stress~~ | Closed Session 08 — deferred ([DEC-2026-05-20-002](../../DECISIONS.md), [proposal](../proposals/2026-05-20_crypto_vol_stress_scenarios_proposal.md)) | — |
| G9 | ~~Custom shock runs not persisted~~ | Closed Session 09 | — |
| G10 | ~~Downstream integration of Sessions 01–06 fields~~ | Closed Session 10 | — |

## New methodology proposals (require spec before code)

| ID | Proposal | Status |
| --- | --- | --- |
| P1 | Primary historical proxy in run_stress | **Deferred** (DEC-2026-05-20-001) — realized-only + disclosure shipped Session 02 |
| P2 | Hedge gap v2 by risk type (`by_risk_type[]`) | **Done** Session 05 |
| P3 | Crisis replay v2 (recovery_months, asset_pnl_contrib_episode) | **Done** Session 06 |
| P4 | Synthetic `crypto_shock` / `volatility_shock` in run_stress | **Deferred** Session 08 ([DEC-2026-05-20-002](../../DECISIONS.md)) |
| P5 | Factor drivers in stress_conclusions | **Done** Session 04 |
| P6 | Optional `custom_shock_runs` artifact | **Done** Session 09 |

## Verification references

- Stress Lab governance bundle (Phase 13 closure): [TESTING.md](../../TESTING.md) § Stress Lab Governance Wave Bundle — **90 passed** Session 11
- Stress Lab post-audit bundle: [TESTING.md](../../TESTING.md) § Stress Lab Wave Regression Bundle
- Baseline fingerprints: [2026-05-20_stress_lab_baseline_snapshot.md](2026-05-20_stress_lab_baseline_snapshot.md)
- Owning specs: [stress_testing_spec.md](../specs/stress_testing_spec.md),
  [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md),
  [scenario_library_spec.md](../specs/scenario_library_spec.md),
  [hedge_gap_analysis_spec.md](../specs/hedge_gap_analysis_spec.md),
  [crisis_replay_spec.md](../specs/crisis_replay_spec.md)
- Core runtime: [src/stress.py](../../src/stress.py)

## Final verdict

Block 3 is an **audit-grade diagnostic stress layer** with explicit contracts for scenarios, scorecard,
conclusions, hedge evidence v2, crisis replay v2, historical methodology disclosure, layer-spec handoff,
and simulator API. Phase 13 (`RM-951`–`RM-961`) is **closed** (2026-05-20): trust gaps G1–G3,
decision-useful extensions G4–G7 and G10, deferred crypto/vol synthetics (G8), and optional custom-shock
persistence (G9) — without UI or silent new scenarios.

For new Block 3 work, start from [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) and
[stress_testing_spec.md](../specs/stress_testing_spec.md); refresh artifact hashes after
`run_report.py --materialize-analysis-subject` per [baseline snapshot](2026-05-20_stress_lab_baseline_snapshot.md).
