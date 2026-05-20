# Candidate Portfolio Factory Methodology Map (Block 4)

Date: 2026-05-20

Status: **Active input** — methodology map for Block 4 governance (Phase 14). Active plan:
[Candidate Portfolio Factory Post-Audit Roadmap](../exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md).
Baseline: [Candidate Factory Baseline Snapshot](2026-05-20_candidate_factory_baseline_snapshot.md).
Does not override canonical specs or current code.

Scope: Candidate Portfolio Factory / Portfolio Menu (Block 4). Maps **what exists today** in code, specs, and artifacts; separates **target product** and **new proposals** from shippable behavior.

Related specs: [candidate_factory_spec.md](../specs/candidate_factory_spec.md), [candidate_portfolios_spec.md](../specs/candidate_portfolios_spec.md), [candidate_comparison_spec.md](../specs/candidate_comparison_spec.md), [robust_mv_spec.md](../specs/robust_mv_spec.md), [robust_scenario_optimization_spec.md](../specs/robust_scenario_optimization_spec.md).

Product concept (non-binding): [DIAGNOSTIC_PRODUCT_CONCEPT.md](../DIAGNOSTIC_PRODUCT_CONCEPT.md) §4–5.

## Provenance legend

| Code | Meaning |
| --- | --- |
| **C** | Existing code behavior |
| **S** | Existing canonical spec |
| **A** | Generated artifact evidence |
| **T** | Target product concept (partially or not implemented) |
| **P** | **NEW METHODOLOGY PROPOSAL** — requires spec decision before implementation |

---

## 1. Executive summary

Block 4 answers: **What alternative portfolios can we build from the same universe and data, how was each one constructed, is it fresh and valid, what can fail, and is it ready for fair backtest, stress evaluation, and comparison?**

**Architecture (shipped):**

```text
config.yml + load_monthly_data_shared
  -> run_<family>.py (per candidate)
       -> src/portfolio_variants.build_* (weights + diagnostics)
       -> run_portfolio_report_for_weights (metrics, stress, snapshots, CSV, commentary)
  -> run_candidate_factory.py (optional orchestration, subprocess chain)
  -> candidate_factory_run.json (per-step status + freshness)
  -> run_compare_variants.py / write_candidate_comparison_outputs
       -> candidate_comparison.json (+ decision package: health, selection, action, journal)
```

**Registry:** 18 comparison rows in `src/candidate_comparison.py` `_REGISTRY_ROWS` — **C** **S**  
3 core decision rows (`analysis_subject`, `policy`, `current`) + **16 script-backed** builder families. Factory profiles run only the 16; policy/current are workflow-gated (**C** **S** `candidate_factory_spec.md`).

**Maturity (2026-05-20):**

| Area | State | Provenance |
| --- | --- | --- |
| Per-family weight construction | Strong — centralized in `src/portfolio_variants.py` | **C** |
| Full diagnostics per candidate folder | Strong — shared `run_portfolio_report_for_weights` pipeline | **C** |
| Factory orchestration + run summary | Shipped (Session 11) | **C** **S** |
| Freshness (`analysis_end` gate) | Shipped (RM-902) in factory + comparison | **C** **S** |
| Partial menu disclosure (`candidate_menu`) | Shipped (core vs full review) | **C** **S** |
| Unified product UI / workspace | Not shipped | **T** |
| Config-hash / universe fingerprint freshness | Not shipped | **P** |
| Resumable factory progress | Deferred (RM-921) | **T** **P** |
| Explicit construction-metadata contract in comparison JSON | Partial (registry fields only) | **C** gap vs **T** |

**Portfolio-first boundary:** Diagnosed `analysis_subject` is the comparison baseline; legacy `policy` is **excluded from factory** and gated **`unavailable`** in portfolio-first comparison when subject exists (**C** **S**). Policy optimizer is **not** a default candidate in review workflow (**C** `portfolio_review_workflow.py`).

**Strongest for MVP:** `core_v1` menu (6 candidates: EW, EW-by-class, RP, risk budgets ×2, HRP) + subject diagnostics + comparison/decision package.

**Heaviest / dependency-bound:** `default_v1` (16 candidates) including classic optimizers and robust suite; `robust_scenario` requires Main `scenario_library_normalized.json` + `stress_report.json` (**C**).

**Primary audit artifacts:** per-candidate `weights.json`, `snapshot_10y.json`, `stress_report.json`, `{output_dir_final}/candidate_factory_run.json`, `{output_dir_final}/candidate_comparison.json` (**A**).

---

## 2. Block 4 methodology map by sub-block

### 4.1 Candidate Menu / Candidate Registry

**User question:** Which alternatives exist, which are in the product menu vs a reduced run, and how are they labeled for comparison?

| Element | Rule | Provenance |
| --- | --- | --- |
| Registry source of truth | `_REGISTRY_ROWS` in `src/candidate_comparison.py`; factory table must stay aligned | **C** **S** |
| Registry size | 18 `candidate_id` values | **C** |
| Script-backed builders | 16 IDs with `run_*.py` entry in `CANDIDATE_ENTRY_SCRIPTS` | **C** |
| Excluded from factory | `policy`, `current` (`POLICY_EXCLUDED_IDS`) | **C** **S** |
| Product reference menu | `default_v1` — all 16 script-backed IDs | **C** **S** |
| Core review menu | `core_v1` — 6 IDs (benchmarks + risk budgets) | **C** **S** |
| Sub-profiles | `core_benchmarks`, `risk_budgets`, `classic_optimizers`, `robust_suite` | **C** **S** |
| Naming | `candidate_id` snake_case; `display_name` English; folder `artifact_root` human-readable path under repo root | **C** **S** |
| Roles | `analysis_subject`, `policy`, `user_current`, `benchmark`, `optimizer_candidate`, `robust_candidate` | **C** **S** |
| `construction_method` | Stable short id per family (e.g. `risk_parity`, `minimum_cvar_constrained`) | **C** **S** |
| `weight_source` | e.g. `candidate_script.fixed_weights`, `optimization_result_released` | **C** **S** |
| User-visible menu | `candidate_comparison.json` → `candidate_menu`; optional `candidate_comparison.txt` | **C** **S** **A** |
| Partial menu flags | `is_partial_menu`, `partial_menu_reason`, `is_reduced_vs_product_menu`, `is_incomplete_intended_menu` | **C** **S** |
| Legacy policy as candidate | Row remains in registry; portfolio-first → `unavailable` + `legacy_policy_not_default_portfolio_first_candidate` | **C** **S** |
| Target: tactical tilt, custom constraints rows | Not in registry | **T** |

**Default vs optional vs legacy vs experimental**

| `candidate_id` | Default in product menu (`default_v1`) | Core MVP (`core_v1`) | Legacy / special |
| --- | --- | --- | --- |
| `analysis_subject` | Baseline row (not factory-built) | Yes (diagnosis step) | Portfolio-first baseline |
| `policy` | Registry only; not factory | No | Legacy compatibility row |
| `current` | Registry only; materialization workflow | No | User current / sidecar |
| `equal_weight` | Yes | Yes | Benchmark |
| `equal_weight_by_asset_class` | Yes | Yes | Benchmark |
| `risk_parity` | Yes | Yes | Benchmark |
| `risk_budget_by_asset` | Yes | Yes | Benchmark |
| `risk_budget_by_asset_class` | Yes | Yes | Benchmark |
| `hierarchical_risk_parity` | Yes | Yes | Benchmark |
| `minimum_variance` | Yes | No | Optimizer candidate |
| `minimum_variance_uncapped` | Yes | No | Optimizer candidate |
| `minimum_variance_advanced` | Yes | No | Optimizer candidate |
| `maximum_diversification` | Yes | No | Optimizer candidate |
| `maximum_diversification_uncapped` | Yes | No | Optimizer candidate |
| `minimum_cvar_constrained` | Yes | No | Optimizer candidate |
| `minimum_cvar_uncapped` | Yes | No | Optimizer candidate |
| `robust_mv_constrained` | Yes | No | Optimizer candidate |
| `robust_mv_uncapped` | Yes | No | Optimizer candidate |
| `robust_scenario` | Yes | No | Robust candidate; 2-step chain |

**How unavailable / skipped / failed / stale appear**

| Layer | Representation | Provenance |
| --- | --- | --- |
| Factory step | `status`: `succeeded`, `failed`, `skipped_existing`, `skipped_dependency`; `reason_code`, `freshness_status` | **C** **S** **A** |
| Comparison row | `status`: `available`, `degraded`, `unavailable`; `unavailable_reason` | **C** **S** |
| Stale snapshot | Factory rebuild or `failed`/`stale_snapshot_after_build`; comparison `unavailable` + `stale_snapshot_analysis_end` | **C** **S** |
| Missing folder | Comparison `missing_artifact_folder` | **C** **S** |
| Builder infeasible (script exits early) | Often **no** `snapshot_10y.json` → factory `missing_snapshot_after_build` or comparison `missing_snapshot` | **C** **A** |

**Inputs:** `config.yml` (tickers, windows, risk_budgeting, bounds, robust settings); taxonomy YAML for class-based candidates (**C**).

**Frequency / window:** Builders use **monthly** simple returns; primary construction window = last element of `cfg.windows_months` (typically **120M / 10Y**) (**C** **S** metrics_spec).

**Implementers:** `src/candidate_comparison.py`, `src/candidate_factory.py`, `run_compare_variants.py`, `run_candidate_factory.py`.

**Owning specs:** `candidate_comparison_spec.md` (registry + menu), `candidate_factory_spec.md` (profiles).

**User outputs:** `candidate_comparison.json`, `candidate_menu`, decision-package summary warnings when `is_partial_menu` (**A**).

**Limitations / misleading risks**

- Interpreting **core** run ranks as covering all 16 product candidates (**mitigated** by `candidate_menu` warnings — **C**).
- Treating **`policy`** as a peer alternative when `analysis_subject` exists (**mitigated** by gating — **C**).
- ~~**`skipped_existing` with `freshness_status: unchecked`** when review `analysis_end` unknown~~ — closed Session 03 (`RM-973`): factory rebuilds; comparison warns (**C**).

**Tests:** `tests/test_candidate_comparison.py` (registry length, menu, policy gating, stale), `tests/test_candidate_factory.py` (profiles), `tests/test_portfolio_review_workflow.py` (core vs full argv).

**Acceptance criteria**

- [ ] Registry in code matches spec tables (18 rows, 16 factory scripts).
- [ ] `candidate_menu.is_partial_menu` true when `core_v1` used vs `default_v1`.
- [ ] Portfolio-first run marks `policy` unavailable with legacy reason when subject folder exists.
- [ ] Every registry id appears in `candidates[]` even when unavailable.

---

### 4.2 Candidate Construction Methods (cross-cutting)

**User question:** By what rule is each candidate built, with what data, and is it deterministic?

| Element | Rule | Provenance |
| --- | --- | --- |
| Shared universe filter | `_eligible_universe_from_returns`: config tickers, window coverage ≥ `coverage_threshold` (default 0.90) | **C** |
| No policy overlays on candidates | Scripts explicitly avoid RC caps, ProLiquidity, mandate release, discretionary filters | **C** **S** candidate_portfolios_spec |
| Weight output | Dict ticker → float, long-only, sum ≈ 1 on eligible names; zero on ineligible | **C** |
| Post-weights pipeline | `run_portfolio_report_for_weights` — same metrics/stress/snapshot path as variants | **C** |
| Covariance (optimizer family) | Monthly Σ, inner join `dropna(how="any")`, Ledoit–Wolf optional, Young-ETF dual mode optional, PSD repair | **C** `_mv_covariance_for_eligible` |
| Taxonomy | `config/etf_universe.yml` + `config/stock_universe.yml` merged map | **C** |
| Determinism | Fixed config + data cache → reproducible; optimizers may have multi-start / numerical tolerance (`OK` vs `APPROXIMATE`) | **C** |
| Status taxonomy (builder) | `OK`, `APPROXIMATE`, `FAIL_INFEASIBLE_UNIVERSE`, `FAIL_DATA`, `FAIL_CONFIG`, `FAIL_INFEASIBLE_TARGETS`, `FAIL_INFEASIBLE_BOUNDS`, `FAIL_NUMERICAL`, … | **C** |

**Outputs per successful builder folder (typical):** `weights.json`, `weights.txt`, `baseline_weights_metadata.json` (some families), `summary.json`, `summary.txt`, `results_csv/*`, `snapshot_{3y,5y,10y}.json`, `stress_report.json`, `stress_commentary.txt`, `run_metadata.json`, `portfolio_xray.json` (via snapshot/report export), `commentary.txt`, PDFs after variant rebuild (**C** **A**).

**Implementers:** `src/portfolio_variants.py`, `run_*.py`, `run_report.run_portfolio_report_for_weights`, `src/snapshot.py`.

**Owning specs:** `candidate_portfolios_spec.md`, `metrics_specification.md`, `data_policy_spec.md`, `feasibility_constraints_spec.md` (bounds).

**Tests:** Family-specific tests under `tests/test_equal_weight_baselines.py`, `test_risk_parity_baseline.py`, `test_minimum_variance_baseline.py`, `test_minimum_cvar_baseline.py`, `test_maximum_diversification_baseline.py`, `test_hrp_weights.py`, `test_risk_budgeting.py`, `test_robust_mean_variance.py`, etc.

**Acceptance criteria**

- [ ] Candidate scripts do not call `run_optimization.py` or write `portfolio_weights.yml`.
- [ ] Eligible universe rules documented and match `_eligible_universe_from_returns` tests.
- [ ] Failed builder writes explicit `summary.json` status without pretending full report succeeded.

---

### 4.3 Benchmark Candidates

Shared: monthly returns, primary window months from `cfg.windows_months[-1]`, eligible-universe filter (**C**). All use **fixed weights** then full report (**C**).

#### Equal Weight (`equal_weight`)

| Field | Detail | Prov. |
| --- | --- | --- |
| Method | `w_i = 1/N` on eligible assets | **C** `build_equal_weight_baseline` |
| Constraints | Long-only, fully invested; no caps | **C** |
| Taxonomy | Not required | **C** |
| Failure | `<2` eligible → `FAIL_INFEASIBLE_UNIVERSE`; script writes summary, **no** full report | **C** |
| Artifacts | `equal-weight portfolio/` | **C** **S** |
| MVP role | Core benchmark — fair “naive diversification” | **C** **S** |

#### Equal Weight by Asset Class (`equal_weight_by_asset_class`)

| Field | Detail | Prov. |
| --- | --- | --- |
| Method | `1/n_classes` per **non-empty** taxonomy class; equal split within class | **C** `build_equal_weight_by_asset_class_baseline` |
| Taxonomy | Required; missing `asset_class` → excluded from weights, listed in diagnostics | **C** |
| Failure | No classified eligible tickers or `<2` kept → `FAIL_INFEASIBLE_UNIVERSE` | **C** |
| Artifacts | `equal-weight by asset-class portfolio/` | **C** **S** |
| MVP role | Core — tests diversification **across** asset classes | **C** |

#### Risk Parity (`risk_parity`)

| Field | Detail | Prov. |
| --- | --- | --- |
| Method | Equalize **RC_vol** per asset; Spinu CCD on `0.5 x'Σx - (1/N)Σ log(x_i)`; fallback SLSQP | **C** |
| Σ | Ledoit–Wolf monthly, PSD repair; inner join returns | **C** **S** RC_vol in metrics_spec |
| Constraints | Long-only, fully invested; **no** weight caps | **C** |
| Failure | `<2` eligible, insufficient rows → `FAIL_*`; solver → `APPROXIMATE` or numerical fail | **C** |
| Artifacts | `risk parity portfolio/`; RC in `weights.txt` when available | **C** |
| MVP role | Core risk-balanced benchmark | **C** **S** |

#### Hierarchical Risk Parity (`hierarchical_risk_parity`)

| Field | Detail | Prov. |
| --- | --- | --- |
| Method | Correlation distance → hierarchical clustering → recursive bisection (`hrp_long_only_weights`) | **C** |
| Σ | Same path as MinVar (`_mv_covariance_for_eligible`) | **C** |
| Constraints | Long-only, sum=1; **no** policy box bounds | **C** |
| Failure | Clustering/numerical → `FAIL_NUMERICAL` | **C** |
| Artifacts | `hierarchical risk parity portfolio/` | **C** **S** |
| MVP role | Core — diversification reference vs RP | **C** |

**Tests:** `test_equal_weight_baselines.py`, `test_risk_parity_baseline.py`, `test_risk_parity_spinu.py`, `test_hrp_weights.py`.

**Acceptance criteria:** Weights sum to 1 on eligible set; EW equal weights; RP RC dispersion below tolerance or `APPROXIMATE` flagged; HRP long-only and finite.

---

### 4.4 Optimizer-Based Candidates

All: **optimized weights** on monthly Σ (and scenario matrix for CVaR); **no** mandate optimizer (**C** **S**).

#### Minimum Variance — constrained (`minimum_variance`)

| Field | Detail | Prov. |
| --- | --- | --- |
| Objective | Minimize `0.5 w' Σ w` | **C** |
| Constraints | `sum(w)=1`; box via `_build_bounds` (min/max single, feasibility cap, Young caps) | **C** **S** feasibility_constraints |
| Σ | Shrinkage per config; Young dual optional | **C** |
| Failure | `FAIL_INFEASIBLE_BOUNDS`, `FAIL_DATA`, … | **C** |
| Role | **Primary** “lowest vol under project box bounds” baseline | **C** docstring |
| Script | `run_minimum_variance.py` | **C** |

#### Minimum Variance — uncapped (`minimum_variance_uncapped`)

| Objective | Same variance min | **C** |
| Bounds | `[0,1]` per asset only | **C** |
| Role | Diagnostic vs constrained | **C** |

#### Minimum Variance — advanced (`minimum_variance_advanced`)

| Extra | Forced Ledoit–Wolf; optional `target_vol_annual` cap; optional L1 vs **current** weights (`cfg.weights`) when λ>0 | **C** |
| Not | Primary lowest-vol baseline | **C** |

#### Maximum Diversification — constrained (`maximum_diversification`)

| Objective | Maximize diversification ratio ` (w'σ) / sqrt(w'Σw) ` (implementation in `_maximum_diversification_slsqp`) | **C** |
| Bounds | Same box as constrained MinVar | **C** |

#### Maximum Diversification — uncapped (`maximum_diversification_uncapped`)

| Bounds | Long-only `[0,1]` only | **C** |

#### Minimum CVaR — constrained (`minimum_cvar_constrained`)

| Objective | Rockafellar–Uryasev LP: min `α + (1/(T(1-γ))) Σ z` on losses `-(Rw)` | **C** `_minimum_cvar_linprog` |
| Data | Scenario matrix = aligned monthly returns rows | **C** |
| γ | From config / builder (see tests) | **C** |
| Bounds | Project box bounds | **C** |
| Failure | `FAIL_INFEASIBLE_BOUNDS` when Σ bounds infeasible | **C** tests |

#### Minimum CVaR — uncapped (`minimum_cvar_uncapped`)

| Bounds | `[0,1]` long-only | **C** |

**Actionable vs evidence:** All are **comparison hypotheses**, not production releases (**S** diagnostic boundary). Constrained variants map to “implementable under IPS-like bounds”; uncapped are **stress-test** extremes for concentration/tail talk (**C** intent in script headers).

**Tests:** `test_minimum_variance_baseline.py`, `test_minimum_cvar_baseline.py`, `test_maximum_diversification_baseline.py`.

**Acceptance criteria:** Solver success or explicit FAIL; weights respect bounds; constrained MinVar variance ≤ unconstrained on same Σ (sanity check on fixture).

---

### 4.5 Risk-Based Candidates

#### Risk Budget by Asset Class (`risk_budget_by_asset_class`)

| Field | Detail | Prov. |
| --- | --- | --- |
| Targets | `resolve_class_risk_targets(risk_cfg)` — preset + optional manual override | **C** |
| Mapping | Taxonomy buckets via `risk_budget_bucket_from_row` on merged universe | **C** |
| Optimizer | SLSQP on squared error vs bucket **percentage variance** targets | **C** |
| `FAIL_CONFIG` | Bad/missing risk_budgeting keys (`KeyError` → message) | **C** |
| `FAIL_INFEASIBLE_TARGETS` | Positive target on bucket with **no** eligible assets (unless `drop_empty_buckets: true` renormalize) | **C** **S** |
| Taxonomy | `missing_taxonomy: exclude` default | **C** |

#### Risk Budget by Asset (`risk_budget_by_asset`)

| Targets | `risk_budgeting.asset_targets` must list **every** eligible ticker with positive budget | **C** |
| `FAIL_CONFIG` | Empty/missing targets; missing eligible keys; extra keys | **C** |
| Solver | Spinu CCD + SLSQP fallback (per-asset budgets) | **C** |

**Note:** `risk_parity` is asset-level equal RC (§4.3), not user-supplied budgets.

**Tests:** `tests/test_risk_budgeting.py` (FAIL_CONFIG, FAIL_INFEASIBLE_TARGETS, universe).

**Acceptance criteria:** Realized bucket RC within tolerance or `APPROXIMATE`; config errors return FAIL_CONFIG without partial weights silently labeled OK.

---

### 4.6 Robust / Scenario-Based Candidates

#### Robust Mean-Variance — constrained / uncapped (`robust_mv_constrained`, `robust_mv_uncapped`)

| Field | Detail | Prov. |
| --- | --- | --- |
| Objective | `min λ w'Σw - μ'w` with James–Stein μ, stabilized Σ | **C** **S** robust_mv_spec |
| λ | `analysis_robust_mv_lambda_calibration/selected_lambda.txt` or CLI `--robust-mv-lambda`; **not** YAML `robust_mv_lambda` in CLI | **C** **S** |
| Bounds | Constrained = project box; uncapped = `[0,1]` | **C** |
| Auxiliary script | `run_robust_mv_lambda_calibration.py` — **not** in factory registry | **C** |
| MVP default menu | In `default_v1`, not `core_v1` | **C** **S** |

#### Robust Scenario (`robust_scenario`)

| Step 1 | `run_robust_scenario_optimization.py` — reads `scenario_library_normalized.json`, `stress_report.json` under `output_dir_final` | **C** **S** |
| Objectives | `lower_half_mean`, `maximin`, `hybrid_legacy` | **C** **S** |
| Betas | Asset betas from stress report; portfolio-beta fallback with warnings | **C** **S** |
| Step 2 | `run_robust_scenario_portfolio_report.py` — full report in `robust scenario portfolio/` | **C** **S** |
| Factory prereq | Both JSON files under Main; else `skipped_dependency` | **C** |
| Policy weights | Does **not** overwrite `portfolio_weights.yml` | **C** **S** |

**Target-only (product concept):** stress-test-optimized standalone candidate, macro-resilient optimizer, drawdown-controlled candidate as **separate** menu ids — overlap partially with existing builders but not 1:1 registry rows (**T**).

**Tests:** `test_robust_mean_variance.py`, `test_robust_mv_calibration.py`, `test_robust_mu_optimization.py` (scenario); factory `test_robust_scenario_skipped_dependency`.

**Acceptance criteria:** Robust MV fails closed on FAIL_CONFIG; scenario factory step skips without policy stress artifacts; two-command chain recorded in `entry_commands`.

---

### 4.7 Candidate Factory Orchestration

**User question:** How are candidates run in batch, what flags apply, and what happens on partial failure?

| Element | Detail | Prov. |
| --- | --- | --- |
| Entry | `python run_candidate_factory.py` | **C** |
| Profiles | `default_v1`, `core_v1`, `core_benchmarks`, `risk_budgets`, `classic_optimizers`, `robust_suite`, `explicit_list` | **C** **S** |
| Order (default_v1) | core_benchmarks → risk_budgets → classic_optimizers → robust_suite (sequential) | **C** **S** |
| `--skip-existing` | Default on; skip only when `snapshot_10y.json` exists and fresh; unchecked rebuilds | **C** **S** |
| `--force` | Rebuild even if snapshot exists | **C** |
| `--fail-fast` | Stop after first failed step | **C** |
| `--then-compare` | Calls `write_candidate_comparison_outputs`; warning `comparison_failed` on exception | **C** |
| Failure policy | `continue_on_error` (default): other candidates continue | **C** **S** |
| Exit codes | `0` success/skip only; `1` any failed step; `2` validation before run | **C** **S** |
| Subprocess | Project Python, cwd=repo root; `--config` passed for robust scripts only | **C** |
| Review orchestration | `run_portfolio_review.py` → diagnosis → factory (`--then-compare`) → PDF | **C** **S** portfolio_review_workflow |
| core vs full | `--mode core` → `core_v1`; `--mode full` → `default_v1` | **C** |
| Resumability | **Not** implemented (RM-921 deferred) | **T** **P** |
| Parallel builders | **Not** implemented | **T** **P** |

**Partial failure downstream:** Comparison still runs with `--then-compare`; failed/skipped candidates → `unavailable` rows; Selection skips `unavailable` (**C** `selection_engine.py`). Decision package may show partial menu warnings (**C**).

**Implementers:** `src/candidate_factory.py`, `run_candidate_factory.py`, `src/portfolio_review_workflow.py`.

**Tests:** `tests/test_candidate_factory.py`, `tests/test_portfolio_review_workflow.py`.

**Acceptance criteria**

- [ ] `candidate_factory_run.json` lists every attempted step with `entry_commands`.
- [ ] `--fail-fast` leaves later ids unattempted.
- [ ] `--then-compare` produces `candidate_comparison.json` when comparison succeeds even if some steps failed.
- [ ] Exit code 1 when any `failed` step exists.

---

### 4.8 Candidate Metadata, Freshness, and Status Contract

**User question:** Can we trust that a candidate folder matches this review date and config?

#### Factory run (`candidate_factory_run_v1`)

| Field | Purpose | Prov. |
| --- | --- | --- |
| `generated_at` | UTC ISO factory summary time | **C** **S** |
| `factory_profile_id` | Profile used | **C** **S** |
| `analysis_end` | Review date from `analysis_subject` snapshot/metadata, else Main | **C** **S** |
| `options` | skip_existing, force, fail_fast, then_compare | **C** |
| `steps[]` | Per-candidate status, reason, freshness, duration, exit_code | **C** **S** |
| `summary` | counts + `rebuilt_stale` | **C** |
| `warnings` | e.g. stale rebuild, unchecked freshness | **C** |

#### Per-step `freshness_status`

| Value | Meaning | Prov. |
| --- | --- | --- |
| `fresh` | `snapshot_10y.analysis_end` == review `analysis_end` | **C** **S** |
| `stale` | Mismatch → rebuild attempted or fail | **C** **S** |
| `missing` | No snapshot | **C** |
| `unchecked` | No review `analysis_end` resolved | **C** |

#### Comparison freshness (RM-902)

Stale snapshot → row `unavailable`, `unavailable_reason: stale_snapshot_analysis_end`, run-level warning (**C** **S**).

**Not in contract today**

| Gap | Prov. |
| --- | --- |
| Config hash / ticker universe fingerprint in freshness | **P** |
| `generated_at` per candidate vs factory batch time | Partial (**A** in snapshots only) |
| Propagation of builder `FAIL_*` into factory reason codes (often collapsed to missing snapshot) | **C** gap |

**Stale in comparison?** Blocked when `analysis_end` known (**C**). If comparison `analysis_end` null, stale gate may not fire (**C** risk).

**Tests:** Factory freshness tests; `test_stale_candidate_snapshot_marked_unavailable` in comparison.

**Acceptance criteria**

- [ ] Stale EW snapshot with fresh subject date triggers rebuild, not skip.
- [ ] Comparison marks stale candidate unavailable and warns.
- [ ] `skipped_existing` records `snapshot_analysis_end` and `expected_analysis_end`.

---

### 4.9 Candidate Readiness for Backtest, Stress, Evaluation, and Comparison

**User question:** Is each candidate ready for fair comparison and downstream decision artifacts?

#### Full report diagnostics (per candidate folder)

When builder succeeds → `run_portfolio_report_for_weights` produces (**C** **A**):

| Artifact | Used by |
| --- | --- |
| `snapshot_{3y,5y,10y}.json` | Comparison metrics, RC, weights, stress suite embed |
| `stress_report.json` | Comparison stress block, factor_regime |
| `stress_commentary.txt` | Human stress narrative |
| `portfolio_xray.json` | X-Ray layer (not required in comparison contract) |
| `results_csv/*` | Correlation, rolling betas, backtest exports |
| `run_metadata.json` | Mandate/setup |
| `commentary.txt` | Folder commentary |

#### Comparison minimum (`available`)

| Requirement | Prov. |
| --- | --- |
| `snapshot_10y.json` with metrics **or** `summary.json` + `metrics_10y` | **C** **S** |
| Prefer snapshot over summary | **C** |
| `degraded` if summary-only or missing stress/diversification blocks | **C** **S** |
| Fresh `analysis_end` when review date resolved | **C** **S** |

#### Downstream decision package

| Artifact | Needs from comparison | Prov. |
| --- | --- | --- |
| Robustness scorecard | `diversification` RC fields (10Y snapshot) | **C** **S** |
| Health score | `weight_concentration` + metrics | **C** **S** |
| Selection | `available`/`degraded` rows; skips `unavailable` | **C** |
| Action / monitoring / journal | Baseline + selected context | **C** **S** |

**Failed / partial candidates:** Excluded from ranking (`unavailable`); still listed in registry (**C**). Factory `failed` does not auto-remove folder from disk — old snapshots may confuse if not freshness-gated (**C** mitigated by RM-902).

**Machine- vs human-readable:** JSON contracts + `candidate_comparison.txt` + per-folder `commentary.txt` / PDFs (**C** **A**).

**Backtest:** Dynamic NaN-safe backtest via report pipeline / `results_csv` (same as subject) (**C** data_policy); not a separate “candidate backtest gate” in factory (**C**).

**Tests:** `test_candidate_comparison.py` (degraded, passthrough, weight_concentration, diversification); decision package `test_decision_package_reporting.py` partial menu.

**Acceptance criteria**

- [ ] No `available` candidate with mismatched `analysis_end` when review date set.
- [ ] Selection never ranks `unavailable` candidates.
- [ ] `degraded` lists `missing_fields` for absent stress or concentration blocks.
- [ ] Full `default_v1` run produces ≥1 `available` benchmark + subject `available` after successful review.

---

## 3. Existing implementation evidence

| Evidence type | Location |
| --- | --- |
| Registry (18 rows) | `src/candidate_comparison.py` `_REGISTRY_ROWS` |
| Factory profiles + scripts | `src/candidate_factory.py` `FACTORY_PROFILES`, `CANDIDATE_ENTRY_SCRIPTS` |
| Weight math | `src/portfolio_variants.py` `build_*` |
| CLI wrappers | `run_equal_weight.py`, `run_risk_parity.py`, … (16 scripts) |
| Orchestration CLI | `run_candidate_factory.py`, `run_portfolio_review.py` |
| Comparison CLI | `run_compare_variants.py` |
| Factory run artifact | `{output_dir_final}/candidate_factory_run.json` |
| Comparison artifact | `{output_dir_final}/candidate_comparison.json` |
| Spec contracts | `docs/specs/candidate_factory_spec.md`, `candidate_comparison_spec.md`, `candidate_portfolios_spec.md` |

**Representative test modules:** `test_candidate_factory.py`, `test_candidate_comparison.py`, `test_portfolio_review_workflow.py`, `test_equal_weight_baselines.py`, `test_risk_parity_baseline.py`, `test_risk_budgeting.py`, `test_minimum_variance_baseline.py`, `test_minimum_cvar_baseline.py`, `test_maximum_diversification_baseline.py`, `test_hrp_weights.py`, `test_robust_mean_variance.py`.

---

## 4. Current gaps and weak points

| ID | Gap | Risk | Prov. |
| --- | --- | --- | --- |
| G1 | Builder `FAIL_*` (infeasible) often surfaces as factory `missing_snapshot_after_build`, not builder status | Operator cannot see **why** from factory JSON alone | **C** |
| G2 | Freshness = `analysis_end` only; no config/universe hash | Reused snapshot after config change same month-end | **P** |
| G3 | ~~`freshness_status: unchecked` allows skip when subject date missing~~ | closed (03 / RM-973) | **C** |
| G4 | Full `default_v1` sequential run may exceed session/time limits | Incomplete menu without `is_partial_menu` if factory not run via review | **C** **S** RM-920 |
| G5 | No resumable step checkpoint (RM-921) | Re-running full factory is expensive | **T** |
| G6 | `construction_method` / diagnostics not copied into `candidate_comparison.json` rows | Comparison shows **what** family, not full **how** (targets, solver, FAIL reason) | **C** vs **T** |
| G7 | `portfolio_xray.json` per candidate not part of comparison readiness | X-Ray not in comparison arena table | **C** |
| G8 | ~~`run_robust_mv_lambda_calibration.py` outside factory menu~~ | closed (07 / RM-977) — `robust_paths_disclosure` + runbook | **C** |
| G9 | ~~Product concept lists Max Sharpe, tactical tilt, custom constraints — no registry rows~~ | closed Session 11 (`RM-981`, DEC-2026-05-20-003, spec appendix) | **C** |
| G10 | ~~Scenario library for robust_scenario tied to **Main** stress artifacts~~ | closed (07 / RM-977) — documented shared scope | **C** **S** |

---

## 5. New methodology proposals

### P1 — Factory reason propagation from builder summary

| Item | Detail |
| --- | --- |
| Source/basis | G1: scripts write `summary.json` with `status`/`reason` on FAIL |
| Reason | Audit trail should distinguish infeasible vs subprocess vs stale |
| Proposed method | After subprocess, if no snapshot, read `{artifact_root}/summary.json` and map `FAIL_*` → factory `reason_code` (`builder_infeasible`, `builder_fail_config`, …) |
| Modules | `src/candidate_factory.py`, `candidate_factory_spec.md` |
| Output contract | Extend `candidate_factory_run_v1` reason codes |
| Tests | Factory fixtures with summary-only failure folders |
| Acceptance | Factory step message cites builder `reason` string |

### P2 — Freshness key: config fingerprint + universe signature

| Item | Detail |
| --- | --- |
| Source/basis | G2, RM-902 follow-up in factory spec “Future work” |
| Reason | Same `analysis_end` after ticker/universe/risk_budget change is not comparable |
| Proposed method | Hash normalized `tickers`, `risk_budgeting`, bound fields, `investor_currency`; store in snapshot + factory step; mismatch → rebuild |
| Modules | `src/candidate_factory.py`, `src/snapshot.py`, `candidate_comparison_spec.md` |
| Tests | Same date, different ticker list → not `fresh` |
| Acceptance | Comparison warns `stale_config_fingerprint` when hash differs |

### P3 — Candidate construction disclosure block in comparison rows

| Item | Detail |
| --- | --- |
| Source/basis | G6, product concept “Construction method, base parameters” |
| Reason | Fair comparison requires visible targets/constraints |
| Proposed method | Optional `construction_disclosure` object sourced from `baseline_weights_metadata.json` / builder diagnostics JSON (no recomputation) |
| Modules | `src/candidate_comparison.py`, `candidate_comparison_spec.md` |
| Tests | Passthrough from fixture metadata |
| Acceptance | EW row shows `equal_weight_method`; risk budget row shows `target_risk_budgets_effective` |

### P4 — Resumable factory manifest (RM-921)

| Item | Detail |
| --- | --- |
| Source/basis | Operational runbook + ROADMAP RM-921 |
| Reason | Full menu rebuild resilience |
| Proposed method | `candidate_factory_manifest.json` with last completed id + checksum; `--resume` |
| Modules | `src/candidate_factory.py`, `run_candidate_factory.py` |
| Acceptance | Interrupted run resumes from next id without redoing `succeeded` |

### P5 — Explicit registry decision for non-implemented concept candidates (**Done** Session 11)

| Item | Detail |
| --- | --- |
| Source/basis | G9, DIAGNOSTIC_PRODUCT_CONCEPT §4–5 |
| Reason | Prevent silent addition of Max Sharpe / tactical tilt |
| Shipped method | Spec appendix + **DEC-2026-05-20-003** — **declined** / **deferred** / **covered_by_existing** per concept id |
| Modules | [candidate_portfolios_spec.md](../specs/candidate_portfolios_spec.md), [DECISIONS.md](../../DECISIONS.md) |
| Acceptance | **Met** — eight concept ids documented; no new registry rows |

---

## 6. P0 / P1 / P2 improvement plan

| Priority | Item | Type | Notes |
| --- | --- | --- | --- |
| **P0** | Document Block 4 map + register (this file) | Docs | Prerequisite for governance sessions |
| **P0** | Keep registry/factory spec tables synced with `_REGISTRY_ROWS` | Process | Already required in specs |
| **P0** | Verify core review path: subject → `core_v1` → compare → partial menu warnings | QA | `test_portfolio_review_workflow.py` |
| **P1** | P1 builder reason propagation | **P** spec first |
| **P1** | P3 construction disclosure in comparison | **P** spec first |
| **P1** | Golden fixture: one candidate per family minimum metadata | Test | Extends comparison contract tests |
| **P2** | P2 config fingerprint freshness | **P** |
| **P2** | P4 resumable factory (RM-921) | **P** |
| **P2** | ~~P5 concept-to-registry decision log~~ | **Done** Session 11 (`RM-981`, DEC-2026-05-20-003) |

**Non-goals for Block 4 governance wave:** UI workspace (**T**), new optimizer formulas (**P** + quant review), silent new `candidate_id` rows.

---

## 7. Verification checklist

Use before closing a Block 4 governance session:

- [ ] `python -m pytest tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_portfolio_review_workflow.py` — pass
- [ ] `python -m pytest tests/test_equal_weight_baselines.py tests/test_risk_parity_baseline.py tests/test_risk_budgeting.py` — pass (spot-check family math)
- [ ] `scripts/verify_docs.py` — registry tables match code (if link check includes factory table)
- [ ] Manual: `run_portfolio_review.py --dry-run` — plan shows `core_v1` + `--materialize-analysis-subject` + factory + compare
- [ ] Artifact: `candidate_factory_run.json` `schema_version` = `candidate_factory_run_v1`
- [ ] Artifact: `candidate_comparison.json` includes `candidate_menu` with `is_partial_menu` after core run
- [ ] No proposal marked **P** implemented without spec + DECISIONS entry

---

## 8. Final verdict

**Block 4 is partially audit-grade today.** Weight construction and per-folder diagnostics are **real, centralized, and test-backed** (**C**). Factory orchestration, freshness by `analysis_end`, portfolio-first policy exclusion, and partial-menu disclosure are **shipped and spec-owned** (**C** **S**). The layer **answers** “what alternatives exist and how were weights built” for operators who read `weights.json`, builder diagnostics, and folder summaries.

**Phase 14 governance (Sessions 00–11, 2026-05-20)** closed G1–G6, G8–G10, golden contracts, resumable factory, operator runbook, and G9 concept-registry DEC (P5). Remaining accepted gap: per-candidate X-Ray not in comparison (`KI-2026-05-20-008` / methodology G7 comparison scope).

**Handoff:** Use [Candidate Factory Baseline Snapshot](2026-05-20_candidate_factory_baseline_snapshot.md), [candidate_factory_layer_spec.md](../specs/candidate_factory_layer_spec.md), and [TESTING.md](../../TESTING.md) § Candidate Factory Governance Wave Bundle for regressions. New `candidate_id` rows require spec + DEC, not product concept text alone.

**Boundary reminder:** Candidate factory remains **diagnostic-only** — it does not select portfolios, release policy weights, or change stress pass/fail (**S** product boundary).
