# Stress Lab Layer Specification

Status: active source-of-truth for Block 3 (Stress Test Lab) implementation boundary.

This document maps Core MVP sub-blocks 3.1 to 3.4 and deferred/advanced Stress Lab capabilities into current code contracts. It is diagnostic-only and
does not override mandate gates from production workflow, optimizer weights, or candidate selection.

Detailed scenario math, pass/fail gates, factor inference, and field-level JSON rules live in
[stress_testing_spec.md](stress_testing_spec.md). Methodology provenance, audit gaps, and Phase 13
closure status are tracked in
[Stress Lab Methodology Map](../audits/2026-05-20_stress_lab_methodology_map.md).

## Scope

Stress Lab answers: where can the portfolio break, under which scenarios, why does it lose money,
which assets pull it down, which protect it, where are hedge gaps, and how much can we trust the
result?

Core MVP sub-blocks:

- 3.1 Scenario Library (historical + synthetic)
- 3.2 Stress Results (`stress_results_v1`)
- 3.3 Hedge Gap Analysis (`hedge_gap_analysis_v1`)
- 3.4 Current Portfolio Stress Scorecard (`current_portfolio_stress_scorecard_v1`)

Deferred / advanced (not Core MVP product blocks; implementation remains):

- What Happens If custom shock simulator API (no UI; no default artifact)
- Crisis Replay (month-by-month historical paths)
- Legacy `hedge_gap_analysis` (`stress_scenario_hedge_evidence_v2`, taxonomy hedge labels)

## Provenance legend

| Code | Meaning |
| --- | --- |
| **C** | Existing code behavior |
| **S** | Existing canonical spec |
| **A** | Generated artifact evidence |
| **T** | Target product concept (partially implemented) |
| **P** | NEW METHODOLOGY PROPOSAL — requires spec decision before implementation |

## Workflow position

```text
monthly returns + weekly asset/portfolio betas + factor history + taxonomy risk_role
  -> run_stress (src/stress.py)
  -> stress_report.json core blocks (scorecard, conclusions, hedge_gap, paths)
  -> run_report.py enrichment (factor regression, rolling betas, scenario library, analytics)
  -> build_scenario_library / normalized (src/scenario_library*.py)
  -> stress_scenario_analytics (src/stress_scenario_analytics.py)
  -> stress_commentary.txt (src/portfolio_commentary.py)
  -> snapshot_10y.stress_suite_results (src/snapshot.py)
```

Orchestration entry points:

- `run_report.py` — stress block (~lines 620–1400); materializes
  `{output_dir_final}/analysis_subject/` when `--materialize-analysis-subject`.
- `run_optimization.py` — calls `export_stress_report` so stress artifacts stay current even with
  `--no-report`.
- `run_portfolio_report_for_weights` — EW/RP variant folders get the same stress contract.

Portfolio-first primary path: `Main portfolio/analysis_subject/stress_report.json` (**A**).

**Core MVP stress contract:** when `analysis_mode=analyze_current_weights`, `run_stress` uses
`loss_gate_mode="diagnostic"`: suite status `ok` | `warning` | `insufficient_data`; scenario rows
and historical rows omit mandate `pass`/`loss_ok`/`diagnostic_code(s)`; `max_dd_limit` is null.
Legacy `optimize_from_universe` reports keep `loss_gate_mode="mandate"` and DIAG_* statuses for
backward compatibility.

## Current contract

Primary artifact: `stress_report.json` in each portfolio output folder.

### Core blocks from `run_stress` (Block 3.1–3.4 product + evidence)

| JSON key | Sub-block | Version / method |
| --- | --- | --- |
| `scenario_results` | 3.1.2 synthetic | rows with `synthetic_assumptions` |
| `historical_results` | 3.1.1 historical | per-episode `return_method`, `proxy_used` (legacy realized portfolio path; DEC-2026-05-20-001) |
| `historical_methodology` | 3.1.1 boundary | `historical_methodology_v1` |
| `historical_stress_replay_v1` | 3.1.1 Core MVP honest replay | `core_mvp_historical_stress_replay_v1`; `policy: direct_history_only` — **C** [core_mvp_historical_stress_replay_spec.md](core_mvp_historical_stress_replay_spec.md); DEC-2026-05-28-001 |
| `stress_results_v1` | 3.2 stress results | `stress_results_v1` |
| `stress_conclusions` | 3.2 conclusions rollup | `stress_conclusions_v1` |
| `hedge_gap_analysis_v1` | 3.3 hedge gap (Core MVP) | `hedge_gap_analysis_v1` — **S** scaffold Session 02; wiring Session 05+ |
| `current_portfolio_stress_scorecard_v1` | 3.4 scorecard (Core MVP) | `current_portfolio_stress_scorecard_v1` (adapter over 3.1–3.3; diagnostic-only) |
| `stress_scorecard_v1` | legacy scorecard | `stress_scorecard_v1` (legacy/compat; includes mandate-mode semantics) |
| `hedge_gap_analysis` | legacy hedge gap | `stress_scenario_hedge_evidence_v2` (backward compatibility) |
| `historical_episode_paths` | deferred crisis replay | `crisis_replay_v2` per episode |
| `status`, `fail_reason_code`, `failed_scenario`, `failed_test` | suite gate | diagnostic-only vs mandate (legacy mandate mode only; Core MVP uses `ok`/`warning`/`insufficient_data`) |
| `loss_gate_mode` | Core MVP vs legacy | `diagnostic` (portfolio-first) or `mandate` (legacy) |

Supporting keys on the same file (suite context, not separate sub-blocks):

- `factor_betas`, `factor_betas_5y`, `factor_betas_10y` — weekly portfolio betas for shock engine
  (**C** **S** §2)
- `recession_calibration`, `max_dd_limit` — calibration and loss-test limit (**C** **S** §2.1, §5)

### Extended blocks from `run_report.py` (same artifact)

Written after `run_stress`; required on full report paths per workspace stress-factor rules:

- `factor_diagnostics_meta` (availability/source/reason metadata for factor beta diagnostics; missing diagnostics must be visible to X-Ray and stress trust output)
- `factor_regression_5y`, `factor_regression_10y` (HAC inference, multicollinearity, serial correlation)
- `factor_betas_rolling_*`, `factor_betas_rolling_artifacts`, `factor_betas_stability`
- `scenario_library_meta`, `scenario_library_normalized_meta`
- `stress_scenario_analytics` (taxonomy_blend_v1 RC under stress — does not change scenario PnL)

Library sidecars (**A**): `scenario_library.json`, `scenario_library_normalized.json`, CSV summaries.

Crisis replay CSV (**A**): `results_csv/crisis_replay_{episode}.csv`,
`crisis_replay_{episode}_asset_contrib.csv` — see [crisis_replay_spec.md](crisis_replay_spec.md).

## Upstream inputs (do not redefine in Stress Lab)

| Input | Owner | Used by |
| --- | --- | --- |
| Monthly asset returns, `analysis_end` | `metrics_specification.md`, `data_policy_spec.md` | 3.1.1 historical |
| Weekly asset/portfolio factor betas | `src/stress_factors.py`, `stress_testing_spec.md` §2, §8 | 3.1.2 synthetic |
| `SCENARIOS`, `HISTORICAL_EPISODES` | `src/stress.py` | 3.1 |
| Taxonomy `risk_role` | `config/*_universe.yml` | legacy `hedge_gap_analysis` labels only (not Block 3.3 v1) |
| `stress_results_v1`, `scenario_results` | `run_stress` / Block 3.2 | 3.3 hedge gap v1 evidence (contribution-based) |
| `config.stress_scenario_overrides` | config schema | 3.1.2 shock overrides |

## Sub-block implementation map

### 3.1 Scenario Library

**Official product definition (Block 3.1 only).** Scenario Library is the unified set of test
scenarios for portfolio stress evaluation inside Block 3 (Stress Test Lab). It includes historical
and synthetic scenarios and allows the system to evaluate portfolio resilience under consistent
stress-testing conditions. This section defines **3.1 only**; other Block 3 sub-blocks (stress
results, hedge gap, scorecard, and related diagnostics) are documented separately below.

**Product boundary:** Block 3.1 is carried by `stress_report.json` scenario rows and Scenario
Library sidecars (`scenario_library.json`, `scenario_library_normalized.json`). There is **no**
`block_3_1_*` key on `portfolio_xray.json`.

#### 3.1.1 Historical Scenarios

Historical scenarios test how the **current portfolio** behaves during real market crises and stress
periods (realized monthly returns, static weights at analysis date).

**Active historical scenario set (fixed — do not add, rename, or extend without spec +
`DECISIONS.md`):**

`dotcom` · `2008` · `2020` · `2022` · `banking_2023`

Code registry: `HISTORICAL_EPISODES` in `src/stress.py`; canonical IDs:
`HISTORICAL_SCENARIO_IDS` in `src/scenario_library.py`. Contract:
`tests/test_stress_scenario_coverage_contract.py`.

#### 3.1.2 Synthetic Scenarios

Synthetic scenarios test the portfolio against predefined market shocks and factor stress
conditions (linear factor-beta shock engine).

**Active synthetic scenario set (fixed — do not add, rename, or extend without spec +
`DECISIONS.md`):**

`equity_shock` · `credit_shock` · `rates_shock` · `inflation_stagflation` · `liquidity_shock` ·
`usd_shock` · `commodity_shock` · `recession_severe`

Code registry: seven fixed vectors in `SCENARIOS` plus calibrated `recession_severe` merged in
`run_stress` (`src/stress.py`); canonical IDs: `SYNTHETIC_SCENARIO_IDS` in
`src/scenario_library.py`. Shock math and pass/fail: [stress_testing_spec.md](stress_testing_spec.md)
§2. **Not** in the active suite: `crypto_shock`, `volatility_shock` (deferred §2.3).

**Implementation question:** Which scenarios exist, with what inputs, shocks, and readiness metadata?

| Element | Rule | Provenance |
| --- | --- | --- |
| Synthetic IDs (8) | Fixed set in §3.1.2 above | **C** `SCENARIOS` + `run_stress` **S** §2 |
| Historical IDs (5) | Fixed set in §3.1.1 above | **C** `HISTORICAL_EPISODES` **S** §9 |
| Shock sizes | Hard-coded; override via `config.stress_scenario_overrides` | **C** **S** §2 |
| Library build | `scenario_library_v1` in `src/scenario_library.py` | **C** **S** [scenario_library_spec.md](scenario_library_spec.md) |
| Normalized view | Readiness + proxy waterfall for library only | **C** **S** scenario_library_spec |
| Version tags | `synthetic_assumptions_v1`, `calibrated_v1_assumptions` (RC taxonomy) | **C** **S** §2.2, §10 |

Core implementation: `src/stress.py`, `src/scenario_library.py`, `src/scenario_library_normalized.py`.

Tests: `tests/test_scenario_library.py`, `tests/test_scenario_library_normalized.py`,
`tests/test_stress_scenario_coverage_contract.py`, `tests/test_stress_synthetic_assumptions_contract.py`.

#### 3.1.1 Historical Scenarios — implementation

**Question:** How did the portfolio behave in past crises (realized)?

| Element | Rule | Provenance |
| --- | --- | --- |
| Frequency | Monthly simple returns, static weights at analysis date | **C** **S** metrics_spec |
| Pass/fail | Episode `max_dd` vs `max_dd_limit` | **C** **S** §9 | Legacy mandate mode only |
| Primary path | **Realized only** in `run_stress`; no proxy substitution | **C** **S** §9.3; DEC-2026-05-20-001 |
| Row disclosure | `return_method`, `proxy_used` on each `historical_results` row | **C** **S** Session 02 |
| Methodology block | `historical_methodology` (`historical_methodology_v1`) | **C** **S** §9.3 |
| Data quality | `n_obs`, `coverage_ratio`, `data_quality` buckets | **C** **S** §9.2 |
| Factor attribution on rows | Model-based enrichment (5Y betas × realized factor shock); not causal | **C** **S** §8.7 |
| Proxy elsewhere | Normalized library waterfall only (direct → proxy → class → factor replay) | **C** **S** historical_stress_fallback |
| Core MVP honest replay | `historical_stress_replay_v1` on portfolio-first diagnostic runs (`loss_gate_mode="diagnostic"`); per-position direct coverage; no proxy fields on product surface | **C** **S** [core_mvp_historical_stress_replay_spec.md](core_mvp_historical_stress_replay_spec.md); DEC-2026-05-28-001 |

Misleading-risk note: null episodes mean insufficient overlap (young ETFs), not zero loss (**A**).
On Core MVP paths, `portfolio_loss_pct` / `drawdown_pct` on Block 3.2 historical rows follow
`historical_stress_replay_v1` (`portfolio_level_result_available`); legacy `historical_results`
realized PnL must not restore full-portfolio metrics when replay is partial or unavailable.

Tests: `tests/test_stress_historical_fields.py`, `tests/test_stress_mandate_pass.py`,
`tests/test_core_mvp_historical_stress_replay*.py`, `tests/test_stress_results_historical_replay_contract.py`.

#### 3.1.2 Synthetic Scenarios — implementation

**Question:** What happens under hypothetical factor shocks?

| Element | Rule | Provenance |
| --- | --- | --- |
| Engine | `r_i = Σ beta_{i,k} * shock_k`; `PnL_i = w_i * r_i` | **C** **S** §2 |
| Betas | Weekly 5Y asset betas; missing → `shock_eq` proxy | **C** |
| Portfolio factor PnL | `shock_k * beta_portfolio_k` (six production factors) | **C** **S** §2 |
| RC diagnostics | `taxonomy_blend_v1` on stressed covariance; **does not** change scenario PnL | **C** **S** §2.2, §10 |
| `recession_severe` | Calibrated from 2008/2020 weekly factor sums | **C** **S** §2.1 |
| Pass/fail | `portfolio_pnl_pct >= -max_dd_limit` → `DIAG_LOSS_*` if fail | **C** **S** §1, §5 | Legacy mandate mode only |
| Not in `run_stress` | `crypto_shock`, `volatility_shock` — deferred ([DEC-2026-05-20-002](../../DECISIONS.md), [proposal](../proposals/2026-05-20_crypto_vol_stress_scenarios_proposal.md)); X-Ray weakness only | **C** **S** §2.3 |

Tests: `tests/test_stress_mandate_pass.py`, `tests/test_stress_covariance_taxonomy.py`,
`tests/test_stress_simulator_contract.py`.

### 3.2 Stress Results

**Question:** For each active stress scenario, what happened, what drove losses, what offset them,
and how trustworthy is the evidence — without parsing raw scenario rows?

| Element | Rule | Provenance |
| --- | --- | --- |
| Contract key | `stress_results_v1` on `stress_report.json` | **S** Session 01 |
| Product rows | `synthetic[]` (8) + `historical[]` (5), using canonical Scenario Library IDs and stable order | **S** Session 01 |
| Synthetic source | Adapt `scenario_results[]` rows; do not recompute scenario PnL | **C** **S** §12.1 |
| Historical source | Adapt `historical_results[]`; derive asset loss contribution from `historical_episode_paths[]` where available | **C** **S** Session 01 |
| Core MVP replay merge | When `historical_stress_replay_v1` is present, copy replay fields onto each `historical_episodes[]` row (`replay_status`, coverage %, `user_note`, `diagnosis_summary_en`, unavailable/available positions, episode dates). Portfolio loss/DD on product rows only when `portfolio_level_result_available` | **C** **S** [core_mvp_historical_stress_replay_spec.md](core_mvp_historical_stress_replay_spec.md); `src/stress_results_block.py` |
| Worst selectors | `worst_synthetic` by minimum `portfolio_loss_pct`; `worst_historical` by minimum `drawdown_pct` among available historical rows | **C** **S** §12.1 |
| Diagnostic boundary | In `loss_gate_mode="diagnostic"`, Block 3.2 product rows and raw evidence arrays omit mandate fields (`pass`, `loss_ok`, `diagnostic_code`, `diagnostic_codes`) | **S** Session 01 |
| Relationship to conclusions | `stress_conclusions` remains a backward-compatible worst-case rollup for snapshot/comparison/commentary consumers | **C** **S** Session 01 |

| Element | Rule | Provenance |
| --- | --- | --- |
| Worst synthetic | `min(portfolio_pnl_pct)` over `scenario_results` | **C** **S** §12.1 |
| Worst historical | `min(max_dd)` among rows with computed `max_dd` (not min `pnl_real_episode`) | **C** **S** §12.1; Session 01 |
| Top loss assets | `top3_loss_assets` from worst synthetic | **C** **S** §12.1 |
| Helped assets | Up to 3 positive-PnL assets in worst synthetic | **C** **S** §12.1 |
| Factor drivers | `top_factor_drivers_worst_scenario`, `helped_factors_worst_scenario` from worst synthetic `pnl_by_factor_pct` | **C** **S** Session 04 |
| Confidence | Worst of beta_confidence (synthetic) and historical `data_quality` | **C** **S** §12.1 |
| Hedge status mirror | `hedge_gap_status` from `hedge_gap_analysis.status` | **C** **S** §12.1 |
| Warnings | `data_quality_warnings` includes historical methodology flags | **C** Session 02 |

Core implementation: `src/stress_results_block.py`, `src/stress.py` (`_build_stress_conclusions`),
`src/core_mvp_historical_stress_replay.py` (replay block; wired from `run_report.py` on diagnostic runs).

Tests: `tests/test_stress_results_block_contract.py`, `tests/test_stress_results_historical_replay_contract.py`,
`tests/test_core_mvp_historical_stress_replay_contract.py`, `tests/test_stress_scorecard_contract.py`,
`tests/test_portfolio_commentary.py`.

### 3.3 Hedge Gap Analysis (Core MVP)

**Question:** For each key market risk type, did assets that helped offset losses from assets that hurt in the mapped synthetic scenario — where is protection weak, and what is the main hedge gap?

| Element | Rule | Provenance |
| --- | --- | --- |
| Contract key | `hedge_gap_analysis_v1` on `stress_report.json` | **S** Block 3.3 Session 01 |
| Diagnosis method | Contribution-based offset coverage from signed `pnl_by_asset_pct`; **no** taxonomy hedge pre-labeling | **S** [hedge_gap_analysis_spec.md](hedge_gap_analysis_spec.md) |
| Evidence source | Block 3.1 `scenario_results[]` and/or Block 3.2 `stress_results_v1.synthetic_scenarios[]` (`loss_contribution.pnl_by_asset_pct`); **no** stress PnL recompute | **S** Session 01 |
| Risk types | Eight product `risk_type` rows, 1:1 with eight synthetic scenarios (includes `recession_severe_protection`) | **S** ExecPlan Block 3.3 |
| Key metric | `offset_coverage_ratio` = positive help / gross hurt when gross hurt > 0 | **S** Session 01 |
| Summary | `main_hedge_gap`, `weakest_protection_area`, `strongest_protection_area`, portfolio `diagnosis_summary_en` | **S** Session 01 (builder Session 04+) |
| Diagnostic boundary | `loss_gate_mode="diagnostic"`; no mandate pass/fail on Block 3.3 product rows | **S** Core MVP |
| Legacy block | `hedge_gap_analysis` (`stress_scenario_hedge_evidence_v2`) retained unchanged for compatibility | **C** **S** §12.2.1 |

Planned implementation: `src/hedge_gap_analysis_block.py` (Session 02+). Tests (Session 07+):
`tests/test_hedge_gap_analysis_v1_contract.py`.

### 3.4 Current Portfolio Stress Scorecard

**Question:** Unified machine-readable stress summary for the **current portfolio** that connects Blocks 3.1–3.3 into a single diagnostic scorecard (no mandate pass/fail).

| Element | Rule | Provenance |
| --- | --- | --- |
| Contract (Core MVP) | `current_portfolio_stress_scorecard_v1`: summary over `stress_results_v1` + `hedge_gap_analysis_v1` | **C** (2026-05-27) |
| Worst synthetic | Minimum synthetic `portfolio_pnl_pct` (via Block 3.2 envelope) | **S** Block 3.2 |
| Worst historical | Minimum `max_dd` (via Block 3.2 envelope) | **S** Block 3.2 |
| Offset coverage + main hedge gap | Use Block 3.3 `hedge_gap_analysis_v1` summary and main-area helped/hurt lists | **S** Block 3.3 |
| Diagnostic boundary | No client mandate comparison, no DIAG_* language, no `pass` / `loss_ok` inside the Block 3.4 product key | **S** Core MVP |
| Legacy/compat | `stress_scorecard_v1` remains as legacy scorecard (mandate-mode semantics, older consumers) | **C** |

Tests: `tests/test_current_portfolio_stress_scorecard_v1_contract.py`, plus existing Stress Lab contract bundles.

## Deferred / advanced sub-blocks (not Core MVP)

These capabilities remain in code and specs but are **not** numbered Core MVP product blocks after Block 3.4.

### What Happens If API (no UI)

**Question:** Custom shock vectors with the same math as built-in scenarios?

| Element | Rule | Provenance |
| --- | --- | --- |
| Status | API implemented; **no UI**; **no default artifact write** | **C** **S** §12.3 |
| Functions | `simulate_custom_shock`, `shock_vector_from_scenario` | **C** |
| Engine | Same linear map as synthetic rows; no RC / pass-fail in simulator | **C** **S** §12.3 |
| Validation | Unknown `scenario_id` → `KeyError`; `vix`/`oil` not in shock keys | **C** |
| Persistence | Optional `custom_shock_runs.json` (`custom_shock_runs_v1`); opt-in only | **C** **S** §12.3 Session 09 |

Tests: `tests/test_stress_simulator_contract.py` (PnL equivalence to built-in rows).

### Crisis Replay

**Question:** Month-by-month crisis path, recovery, and static asset contribution — not aggregate only?

| Element | Rule | Provenance |
| --- | --- | --- |
| Method | `crisis_replay_v2` on each `historical_episode_paths[]` entry | **C** **S** [crisis_replay_spec.md](crisis_replay_spec.md) |
| Path rows | `date`, `portfolio_return`, `equity`, `drawdown` | **C** **S** |
| Recovery | `time_to_recovery_months`, `recovered` (metrics_spec §6.9) | **C** **S** Session 06 |
| Asset contrib | `asset_pnl_contrib_episode`, `top_loss_assets_episode` | **C** **S** Session 06 |
| CSV export | `run_report.py` → `crisis_replay_{episode}.csv`, `_asset_contrib.csv` | **C** **S** |
| Acceptance | Path max_dd == aggregate `historical_results.max_dd`; CSV rows == `n_obs` | **C** **S** |
| Not implemented | Per-asset path through time; factor path replay | **T** |

Tests: `tests/test_stress_historical_fields.py`.

### Legacy hedge gap (`hedge_gap_analysis`)

**Question:** Do taxonomy hedge-labeled holdings fail to protect in mapped stress scenarios?

| Element | Rule | Provenance |
| --- | --- | --- |
| Method | `stress_scenario_hedge_evidence_v2` (aggregate + `by_risk_type[]`) | **C** **S** [hedge_gap_analysis_spec.md](hedge_gap_analysis_spec.md) §Legacy |
| Hedge labels | Taxonomy `risk_role`: crisis_hedge, defensive, inflation_hedge, tail_hedge | **C** **S** §12.2.1 |
| Evaluation | Global worst synthetic + per weakness bucket via `HEDGE_GAP_SCENARIO_BY_RISK` | **C** **S** |
| Core MVP operators | Read **`hedge_gap_analysis_v1`** (Block 3.3), not this block | **S** Block 3.3 |

Core implementation: `src/stress.py` (`_build_hedge_gap_analysis`). Tests:
`tests/test_stress_hedge_gap_contract.py`.

## Report surfaces

User-facing narrative (English, diagnostic boundary vs mandate):

- `stress_commentary.txt` — `write_stress_commentary` / `src/portfolio_commentary.py`
- PDF-facing stress memo — `src/pdf_reports.py` (sanitized; not raw JSON)
- Portfolio `commentary.txt` — may reference stress conclusions per portfolio-commentary rules

Structured machine-readable surfaces:

- `stress_report.json` (this layer)
- `snapshot_10y.json` → `stress_suite_results` mirror
- `scenario_library.json` / normalized JSON for readiness review

## Downstream consumers (integration note)

Sessions 01–06 fields are wired in **Session 10** into `snapshot_10y.stress_suite_results`,
`candidate_comparison` `stress` blocks, and `stress_commentary.txt`:

- `stress_conclusions` (factor drivers, worst historical by `max_dd`, `data_quality_warnings`)
- `historical_methodology` + per-row `return_method` / `proxy_used` in commentary historical lines
- `hedge_gap_analysis` and (when present) `hedge_gap_analysis_v1` in snapshot, comparison, commentary
- `crisis_replay_summary` in snapshot/comparison; full `historical_episode_paths` in commentary

Health/robustness scorecards continue to use simplified `stress.overall` and abbreviated scenarios;
full conclusions remain on `stress_report.json` / snapshot mirror.

## Open gaps (Phase 13)

| ID | Gap | Status |
| --- | --- | --- |
| G1–G6 | Worst historical, methodology boundary, hedge N/A, factor drivers, hedge-by-type, crisis replay v2 | **Closed** Sessions 01–06 |
| G7 | Layer spec too shallow for handoff | **Closed** Session 07 (this document) |
| G8 | `crypto_shock` / `volatility_shock` deferred for `run_stress` | **Closed** Session 08 (spec + [DEC-2026-05-20-002](../../DECISIONS.md)) |
| G9 | ~~Custom shock runs not persisted~~ | **Closed** Session 09 (`custom_shock_runs.json`) |
| G10 | Downstream integration of Sessions 01–06 fields | **Closed** Session 10 |

## Phase 13 governance wave (Block 3)

Active ExecPlan:
[Stress Lab Methodology Governance Plan](../exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md).

| Session | RM ID | Focus |
| --- | --- | --- |
| 01 | RM-952 | Worst historical by `max_dd` — **Done** |
| 02 | RM-953 | Historical methodology boundary — **Done** |
| 03 | RM-954 | Hedge N/A transparency — **Done** |
| 04 | RM-955 | Factor drivers in conclusions — **Done** |
| 05 | RM-956 | Hedge gap v2 by risk type — **Done** |
| 06 | RM-957 | Crisis replay v2 — **Done** |
| 07 | RM-958 | Layer spec handoff (3.1–3.4 Core MVP + deferred sub-blocks) — **Done** |
| 08 | RM-959 | Crypto/vol scenarios — **Done** (deferred, proposal + DEC-2026-05-20-002) |
| 09 | RM-960 | Custom shock artifact (`custom_shock_runs.json`) — **Done** |
| 10 | RM-961 | Downstream integration — **Done** |
| 11 | RM-961 | Verification bundle + baseline refresh + closure — planned |

Prerequisite wave (do not redo):
[Stress Lab Post-Audit Roadmap](../exec_plans/2026-05-20_stress_lab_post_audit_roadmap.md) Sessions 00–10.

## Non-goals

- No UI simulator in this layer.
- No direct optimizer or mandate release impact from stress diagnostics.
- No investment recommendations.
- No silent new scenarios or shock vectors without spec + `DECISIONS.md` entry.
- No alternate formulas for stress PnL, historical returns, or factor betas inside layer navigation docs.

## Verification

- Doc link check: `python scripts/verify_docs.py`
- Stress Lab governance pytest bundle: [TESTING.md](../../TESTING.md) § Stress Lab Wave Regression Bundle
- Baseline fingerprints: [2026-05-20_stress_lab_baseline_snapshot.md](../audits/2026-05-20_stress_lab_baseline_snapshot.md)
