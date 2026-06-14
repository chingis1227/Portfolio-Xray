# Candidate Factory Layer Specification

Status: active source-of-truth for Block 4 (Candidate Portfolio Factory) implementation boundary.

This document maps sub-blocks 4.1 to 4.9 into current code contracts. It is diagnostic-only and
does not override mandate gates, stress pass/fail, optimizer weights, production release, or
candidate selection.

Detailed registry tables, factory run JSON, comparison row contracts, and per-family construction
rules live in the owning specs below. Methodology provenance, audit gaps G1–G10, and Phase 14
closure status are tracked in
[Candidate Factory Methodology Map](../audits/2026-05-20_candidate_factory_methodology_map.md).

## Scope

Block 4 answers: which alternative portfolios exist, how each was built, whether artifacts are
fresh and valid, why a factory step failed, and whether each row is ready for fair comparison and
downstream decision artifacts.

Sub-blocks:

- 4.1 Candidate Menu / Candidate Registry
- 4.2 Candidate Construction Methods (cross-cutting)
- 4.3 Benchmark Candidates
- 4.4 Optimizer-Based Candidates
- 4.5 Risk-Based Candidates
- 4.6 Robust / Scenario-Based Candidates
- 4.7 Candidate Factory Orchestration
- 4.8 Candidate Metadata, Freshness, and Status Contract
- 4.9 Candidate Readiness for Backtest, Stress, Evaluation, and Comparison

## Provenance legend

| Code | Meaning |
| --- | --- |
| **C** | Existing code behavior |
| **S** | Existing canonical spec |
| **A** | Generated artifact evidence |
| **T** | Target product concept (partially or not implemented) |
| **P** | NEW METHODOLOGY PROPOSAL — requires spec decision before implementation |

## Workflow position

```text
config.yml
  -> prepare_candidate_run_context()  # one monthly load + factor/scenario cache (fast/standard)
       -> build_candidate_weights / write_candidate_weights (per candidate)
       -> run_portfolio_report_for_weights(..., lightweight_comparison)  # standard Phase 2; optionally parallel per candidate
       -> optional run_portfolio_report_for_weights(..., full)  # Phase 3 (--full-candidate-reports)
  OR legacy_full:
       -> run_<family>.py (16 script-backed candidates)
            -> load_monthly_data_shared + portfolio_variants.build_*
            -> run_portfolio_report_for_weights (full report per subprocess)
  -> run_candidate_factory.py (optional batch orchestration)
       -> {output_dir_final}/candidate_factory_run.json
  -> write_candidate_comparison_outputs / run_compare_variants.py
       -> {output_dir_final}/candidate_comparison.json
       -> decision package (robustness, health, selection, action, journal)
```

Portfolio-first orchestration:

```text
run_portfolio_review.py
  -> materialize analysis_subject (diagnosis baseline)
  -> run_candidate_factory.py (--profile core_v1 | default_v1, --execution-mode standard, --then-compare)
  -> PDF rebuild (portfolio-first subset unless --legacy-full-pdf)
```

Legacy policy path (factory excludes `policy` / `current`):

```text
run_optimization.py -> run_report.py
  -> optional run_candidate_factory.py --then-compare
```

Primary comparison baseline in portfolio-first mode:
`{output_dir_final}/analysis_subject/` (**C** **S** `portfolio_review_workflow_spec.md`).

## Current contract

### Primary artifacts

| Artifact | Location | Schema / version |
| --- | --- | --- |
| Factory run summary | `{output_dir_final}/candidate_factory_run.json` | `candidate_factory_run_v1` |
| Multi-candidate comparison | `{output_dir_final}/candidate_comparison.json` | `candidate_comparison_v1` (+ row `construction_disclosure` v1.3) |
| Per-candidate diagnostics | `{artifact_root}/` under repo root (human-readable folder names) | `snapshot_10y.json`, `stress_report.json`, `weights.json`, `summary.json`, … |
| Partial menu disclosure | `candidate_comparison.json` → `candidate_menu` | `is_partial_menu`, `partial_menu_reason`, … |

### Registry (4.1)

| Element | Rule | Provenance |
| --- | --- | --- |
| Source of truth | `_REGISTRY_ROWS` in `src/candidate_comparison.py` | **C** **S** |
| Row count | 18 `candidate_id` values | **C** |
| Factory-built | 16 IDs in `CANDIDATE_ENTRY_SCRIPTS` | **C** |
| Excluded from factory | `policy`, `current` (`POLICY_EXCLUDED_IDS`) | **C** **S** |
| Product menu | `default_v1` (all 16 builders) | **C** **S** |
| Core MVP menu | `core_v1` (6 benchmarks + risk budgets) | **C** **S** |
| Portfolio-first policy row | `unavailable` + `legacy_policy_not_default_portfolio_first_candidate` when subject exists | **C** **S** |

Owning spec: [candidate_comparison_spec.md](candidate_comparison_spec.md) (registry, menu, row status).

### Factory orchestration (4.7)

| Element | Rule | Provenance |
| --- | --- | --- |
| CLI | `python run_candidate_factory.py` | **C** |
| Profiles | `default_v1`, `core_v1`, `core_benchmarks`, `risk_budgets`, `classic_optimizers`, `robust_suite`, `explicit_list` | **C** **S** |
| Default order (`default_v1`) | core_benchmarks → risk_budgets → classic_optimizers → robust_suite | **C** **S** |
| `--skip-existing` | Skip only when `snapshot_10y.json` is **fresh** vs review `analysis_end` | **C** **S** |
| Unchecked review date | Rebuild (no `skipped_existing` on unchecked freshness) | **C** Session 03 |
| `--force`, `--fail-fast`, `--then-compare` | Per [candidate_factory_spec.md](candidate_factory_spec.md) | **C** **S** |
| Exit codes | `0` success/skip only; `1` any failed step; `2` validation error | **C** **S** |
| Resumable manifest (`--resume`) | **Shipped** (RM-979 / Session 09; closes RM-921 resumable scope) | **C** **S** |
| Parallel lightweight reports | Opt-in `--parallel-lightweight-reports` for eligible `standard` Phase 2 reports; builders and final registration remain menu-ordered | **C** **S** |

Owning spec: [candidate_factory_spec.md](candidate_factory_spec.md).

Core implementation: `src/candidate_factory.py`, `run_candidate_factory.py`,
`src/portfolio_review_workflow.py`.

### Freshness and failure reasons (4.8)

| Factory `freshness_status` | Meaning |
| --- | --- |
| `fresh` | `snapshot_10y.analysis_end` == review `analysis_end` |
| `stale` | Mismatch → rebuild or fail |
| `missing` | No snapshot |
| `unchecked` | Review `analysis_end` not resolved → rebuild attempted; comparison warns |

| Factory `reason_code` (failed steps) | When |
| --- | --- |
| `builder_*` | Mapped from builder `summary.json` `FAIL_*` (Session 02) |
| `subprocess_failed` | Non-zero exit, no builder FAIL mapping |
| `missing_snapshot_after_build` | No `snapshot_10y.json` after subprocess |
| `skipped_dependency` | e.g. `robust_scenario` without Main stress/scenario JSON |

Comparison stale gate: row `unavailable`, `unavailable_reason: stale_snapshot_analysis_end`
when review date known (**C** **S** RM-902).

Config fingerprint freshness: **shipped** (G2 / Session 06 / RM-976); ETF/stock universe file hashing remains future scope.

Owning specs: [candidate_factory_spec.md](candidate_factory_spec.md),
[candidate_comparison_spec.md](candidate_comparison_spec.md).

### Construction disclosure (4.2 / comparison handoff)

Every comparison row includes `construction_disclosure` (passthrough only, no recomputation):

| Field | Source |
| --- | --- |
| `baseline_metadata` | `{artifact_root}/baseline_weights_metadata.json` |
| `builder_summary` | `{artifact_root}/summary.json` |
| `main_portfolio_excerpt` / `sidecar_excerpt` | Policy / subject folders when applicable |
| `factory_step` | Matching step from `candidate_factory_run.json` |

`disclosure_status`: `complete`, `partial`, or `minimal` per available files.

Owning spec: [candidate_comparison_spec.md](candidate_comparison_spec.md) § `construction_disclosure` (v1.3).

### Comparison readiness (4.9)

| Row `status` | Minimum |
| --- | --- |
| `available` | `snapshot_10y.json` with metrics (preferred) or `summary.json` + `metrics_10y`; fresh `analysis_end` when review date set |
| `degraded` | Partial metrics / missing stress or concentration blocks (`missing_fields`) |
| `unavailable` | Missing folder, stale snapshot, missing snapshot, legacy policy gating, etc. |

Downstream: Selection skips `unavailable`; robustness/health use `diversification` and
`weight_concentration` from 10Y snapshot when present (**C**).

## Upstream inputs (do not redefine in Block 4)

| Input | Owner | Used by |
| --- | --- | --- |
| Monthly returns, windows, `analysis_end` | [metrics_specification.md](metrics_specification.md), [data_policy_spec.md](data_policy_spec.md) | All builders |
| Eligible universe filter | `_eligible_universe_from_returns` in `portfolio_variants.py` | 4.2–4.6 |
| Box bounds, Young ETF caps | [feasibility_constraints_spec.md](feasibility_constraints_spec.md) | Constrained optimizers |
| Taxonomy | `config/etf_universe.yml`, `config/stock_universe.yml` | Class EW, risk budgets |
| Risk budgeting presets | `config.yml` `risk_budgeting` | 4.5 |
| Main `scenario_library_normalized.json`, `stress_report.json` | Stress Lab / `run_report.py` | 4.6 `robust_scenario` only |
| Robust MV λ | `analysis_robust_mv_lambda_calibration/selected_lambda.txt` or CLI | 4.6 robust MV (**C**; factory does not run calibration — G8) |

## Sub-block implementation map

### 4.1 Candidate Menu / Candidate Registry

- Core: `src/candidate_comparison.py` — `_REGISTRY_ROWS`, `build_candidate_menu`, policy gating
- Factory alignment: `src/candidate_factory.py` — `FACTORY_PROFILES`, `CANDIDATE_ENTRY_SCRIPTS`
- CLI: `run_compare_variants.py`, `run_candidate_factory.py --then-compare`
- Tests: `tests/test_candidate_comparison.py` (registry length, menu, policy, stale),
  `tests/test_candidate_factory.py` (profiles), `tests/test_portfolio_review_workflow.py`

### 4.2 Candidate Construction Methods (cross-cutting)

- Core: `src/portfolio_variants.py` — all `build_*` weight functions
- Post-weights: `run_report.run_portfolio_report_for_weights` (shared with EW/RP variants)
- Rules: no policy optimizer, no `portfolio_weights.yml` from candidate scripts (**S**)
- Typical outputs: `weights.json`, `baseline_weights_metadata.json`, `summary.json`, snapshots,
  `stress_report.json`, `commentary.txt`
- Spec: [candidate_portfolios_spec.md](candidate_portfolios_spec.md)
- Tests: family modules under `tests/test_*_baseline.py`, `test_risk_budgeting.py`, `test_hrp_weights.py`

### 4.3 Benchmark Candidates

| `candidate_id` | Builder | Folder (typical) |
| --- | --- | --- |
| `equal_weight` | `build_equal_weight_baseline` | `equal-weight portfolio/` |
| `equal_weight_by_asset_class` | `build_equal_weight_by_asset_class_baseline` | `equal-weight by asset-class portfolio/` |
| `risk_parity` | Spinu CCD / SLSQP equal RC_vol | `risk parity portfolio/` |
| `hierarchical_risk_parity` | HRP clustering | `hierarchical risk parity portfolio/` |

Scripts: `run_equal_weight.py`, `run_equal_weight_by_asset_class.py`, `run_risk_parity.py`,
`run_hierarchical_risk_parity.py`.

### 4.4 Optimizer-Based Candidates

| `candidate_id` | Objective (summary) | Bounds |
| --- | --- | --- |
| `minimum_variance` | Min variance | Project box |
| `minimum_variance_uncapped` | Min variance | `[0,1]` |
| `minimum_variance_advanced` | Min variance + optional vol/L1 vs current | Project box + extras |
| `maximum_diversification` | Max diversification ratio | Project box |
| `maximum_diversification_uncapped` | Same | `[0,1]` |
| `minimum_cvar_constrained` | Rockafellar–Uryasev CVaR LP | Project box |
| `minimum_cvar_uncapped` | Same | `[0,1]` |

Scripts: `run_minimum_variance.py`, `run_minimum_variance_uncapped.py`,
`run_minimum_variance_advanced.py`, `run_maximum_diversification.py`,
`run_maximum_diversification_uncapped.py`, `run_minimum_cvar_constrained.py`,
`run_minimum_cvar_uncapped.py`.

All are comparison hypotheses, not production releases (**S** diagnostic boundary).

### 4.5 Risk-Based Candidates

| `candidate_id` | Method |
| --- | --- |
| `risk_budget_by_asset_class` | Bucket targets via taxonomy + SLSQP vs class variance |
| `risk_budget_by_asset` | Per-asset targets from `risk_budgeting.asset_targets` |

Scripts: `run_risk_budget_by_asset_class.py`, `run_risk_budget_by_asset.py`.

Note: `risk_parity` is equal RC per asset (§4.3), not user-supplied budgets.

### 4.6 Robust / Scenario-Based Candidates

| `candidate_id` | Chain | Prerequisites |
| --- | --- | --- |
| `robust_mv_constrained`, `robust_mv_uncapped` | Single script | λ from calibration file or CLI ([robust_mv_spec.md](robust_mv_spec.md)) |
| `robust_scenario` | `run_robust_scenario_optimization.py` → `run_robust_scenario_portfolio_report.py` | Main `scenario_library_normalized.json` + `stress_report.json` |

Factory: `robust_scenario` → `skipped_dependency` when Main artifacts missing (**C**).
Does not overwrite `portfolio_weights.yml` (**S**).

Specs: [robust_mv_spec.md](robust_mv_spec.md),
[robust_scenario_optimization_spec.md](robust_scenario_optimization_spec.md).

Tests: `test_robust_mean_variance.py`, factory `test_robust_scenario_skipped_dependency`.

### 4.7 Candidate Factory Orchestration

See **Current contract** above and [candidate_factory_spec.md](candidate_factory_spec.md).

Review modes: `--mode core` → `core_v1`; `--mode full` → `default_v1` (**C**).

### 4.8 Candidate Metadata, Freshness, and Status Contract

Factory JSON: `generated_at`, `factory_profile_id`, `analysis_end`, `options`, `steps[]`,
`summary`, `warnings` — see [candidate_factory_spec.md](candidate_factory_spec.md).

Per-step fields: `status`, `reason_code`, `builder_status`, `builder_reason`, `freshness_status`,
`snapshot_analysis_end`, `expected_analysis_end`, `duration_sec`, `exit_code`, `entry_commands`.
When `--parallel-lightweight-reports` is requested, the run summary may also include
`parallel_lightweight_report_summary` with requested/effective status, fallback reasons, worker
count, menu-ordered submitted/registered candidate ids, and optional parallel wall-clock seconds.

### 4.9 Candidate Readiness for Backtest, Stress, Evaluation, and Comparison

When a builder succeeds, `run_portfolio_report_for_weights` produces the same diagnostic stack as
variant reports:

| Artifact | Consumer |
| --- | --- |
| `snapshot_{3y,5y,10y}.json` | Comparison metrics, RC, stress embed |
| `stress_report.json` | Comparison `stress` block |
| `results_csv/*` | Correlation, rolling betas, backtest exports |
| `portfolio_xray.json` | Portfolio Diagnosis technical layer (not required for comparison contract) |
| `commentary.txt` | Folder narrative |

Backtest: dynamic NaN-safe path via report pipeline (**C** `data_policy_spec.md`); no separate
factory backtest gate.

## Downstream consumers (integration note)

| Consumer | Needs from Block 4 |
| --- | --- |
| Robustness scorecard | `diversification` from 10Y snapshot on comparison rows |
| Portfolio Health Score | `weight_concentration`, metrics |
| Selection Engine | `available` / `degraded` only; skips `unavailable` |
| Action plan / monitoring / journal | Baseline + selected candidate context |
| `candidate_comparison.txt` / decision package summary | Menu warnings when `is_partial_menu` |

`construction_disclosure` supports human audit of **how** each hypothesis was built without opening
every candidate folder (**C** Session 04).

## Open gaps (Phase 14)

| ID | Gap | Status |
| --- | --- | --- |
| G1 | Builder FAIL_* collapsed to missing snapshot | **Closed** Session 02 (`RM-972`) |
| G3 | Unchecked freshness silent skip | **Closed** Session 03 (`RM-973`) |
| G6 | No `construction_disclosure` on comparison rows | **Closed** Session 04 (`RM-974`) |
| G7 | Layer spec too shallow for handoff | **Closed** Session 05 (this document) |
| G2 | ~~Config / universe fingerprint freshness~~ | **Closed** Session 06 (`RM-976`) |
| G4 | Full `default_v1` runtime / partial menu if factory not via review | Mitigated by `candidate_menu` (**C**); [operational_runbook.md](../operational_runbook.md) §8 (**Closed** Session 10 / `RM-980`) |
| G5 | Resumable factory (RM-921) | **Closed** Session 09 (`RM-979`) |
| G8 | Robust MV λ source opaque in factory | **Closed** Session 07 (`RM-977`) |
| G9 | Concept-only candidates not in registry | **Closed** Session 11 (`RM-981`, DEC-2026-05-20-003) |
| G10 | `robust_scenario` uses Main stress/scenario library | **Closed** Session 07 (`RM-977`) |

## Phase 14 governance wave (Block 4)

**Closed** 2026-05-20 (Sessions 00–11). Historical ExecPlan:
[Candidate Portfolio Factory Post-Audit Roadmap](../exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md).

| Session | RM ID | Focus |
| --- | --- | --- |
| 00 | RM-970 | Project memory — **Done** |
| 01 | RM-971 | Documentation sync — **Done** |
| 02 | RM-972 | Builder reason propagation (G1) — **Done** |
| 03 | RM-973 | Freshness unchecked (G3) — **Done** |
| 04 | RM-974 | `construction_disclosure` (G6) — **Done** |
| 05 | RM-975 | Layer spec handoff (4.1–4.9) — **Done** |
| 06 | RM-976 | Config fingerprint (G2) | **Done** |
| 07 | RM-977 | Robust paths disclosure (G8, G10) | **Done** |
| 08 | RM-978 | Golden tests + TESTING bundle | done |
| 09 | RM-979 | Resumable factory (RM-921) | done |
| 10 | RM-980 | Operational runbook | **Done** |
| 11 | RM-981 | Concept registry DEC + wave closure | **Done** |

Prerequisite waves (do not redo): RM-902 freshness, RM-920 core/full review modes, RM-922 partial
menu, factory CLI (post-audit Session 11 in prior roadmap).

## Non-goals

- No UI / saved workspace for candidate factory.
- No new `candidate_id` rows or optimizer formulas without spec + `DECISIONS.md`.
- No mandate release, stress pass/fail changes, or automatic portfolio selection from factory output.
- No recomputation of construction parameters inside comparison (passthrough only).
- No parallel factory builders in V1; shipped concurrency is limited to opt-in Phase 2
  `lightweight_comparison` report generation after weights exist.

## Verification

- Doc link check: `python scripts/verify_docs.py`
- Block 4 governance pytest bundle (baseline): `python -m pytest tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_portfolio_review_workflow.py -q`
- Methodology acceptance checklist: [Candidate Factory Methodology Map](../audits/2026-05-20_candidate_factory_methodology_map.md) §7
- Baseline fingerprints (when network/data available): [2026-05-20_candidate_factory_baseline_snapshot.md](../audits/2026-05-20_candidate_factory_baseline_snapshot.md)
