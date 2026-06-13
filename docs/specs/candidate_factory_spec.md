# Candidate Portfolio Factory Specification

This document owns the **Candidate Portfolio Factory** orchestration contract: how the project runs the existing per-candidate builder scripts in a controlled order, records per-candidate outcomes, and hands off to the canonical comparison pipeline.

It does not own metric formulas, optimizer mathematics, stress scenarios, comparison field definitions, or selection logic. Those remain in [metrics_specification.md](metrics_specification.md), [candidate_portfolios_spec.md](candidate_portfolios_spec.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [portfolio_construction_policy.md](portfolio_construction_policy.md), and [selection_engine_spec.md](selection_engine_spec.md).

Implementation: **`run_candidate_factory.py`** and **`src/candidate_factory.py`** (post-audit Session 11, 2026-05-17). This spec is the contract.

Product terminology boundary: the factory is a current backend orchestration capability for building candidate evidence. Product-facing `Candidate Launchpad` or `Portfolio Alternatives Builder` UX must not be inferred from this spec unless separately specified and implemented.

## Portfolio MRI product boundary (2026-05-25 code migration Session 11)

The batch Candidate Portfolio Factory is preserved as implemented infrastructure, but it is not the
default product UX.

| Surface | Classification | Notes |
| --- | --- | --- |
| `run_portfolio_review.py` default review | Product/front-door orchestrator | Materializes `analysis_subject` first, then may call the factory as backend plumbing. |
| Candidate Launchpad | Product-facing hypothesis cards | Does not build portfolios and contains no weights. |
| Portfolio Alternatives Builder | Product-facing one-candidate wrapper | Returns a delegated one-candidate factory command plan. |
| `run_candidate_factory.py --profile core_fast` | Backend routine core batch | Used by default portfolio review orchestration; still not a standalone product UI. |
| `run_candidate_factory.py --profile core_v1` | Backend legacy core batch | Sequential core profile retained for compatibility/regression. |
| `run_candidate_factory.py --profile default_v1` | Advanced/research full batch | Builds the full 16-candidate research menu; not the default product experience. |
| Family profiles and explicit candidate lists | Advanced/research subset batch | Useful for research, debugging, refresh, and backend operations. |

Implementation helpers:

- `candidate_factory_product_boundary()` returns static boundary metadata for tests/docs.
- `candidate_factory_profile_classification(profile_id)` classifies profiles without changing
  execution behavior or generated JSON contracts.

These helpers are not written into `candidate_factory_run.json`. They exist only to prevent future
sessions from confusing the batch factory with product-facing Launchpad or Alternatives Builder UX.

**Comparison menu baseline (Session 3, architecture audit):** `src/candidate_comparison.py` uses
`FULL_MENU_RESEARCH_PROFILE_ID` (`default_v1`) only as the sixteen-candidate **research reference**
in `candidate_menu` (legacy JSON key `product_menu_profile_id`). Core MVP product truth is
**selected-candidate-first** (`run_portfolio_review.py --candidates <id>`). A one-candidate demo may
set `partial_menu_reason` to `reduced_menu_scope_vs_full_menu_default_v1`; that is expected and does
not mean the run failed.

**Active runtime refactor (orchestration only, no formula changes):**
[Candidate Factory Runtime Refactor Plan](../exec_plans/2026-05-22_candidate_factory_runtime_refactor_plan.md)
— phased weights / lightweight report / PDF modes. **Session 1 (shipped):** factory default
`--pdf-mode none` sets `PORTFOLIO_SKIP_VARIANT_PDF=1` on builder subprocesses; per-step timing
buckets in `candidate_factory_run.json`. **Session 2 (shipped):** `--execution-mode fast|standard`
runs Phase 1 weights in-process via `src/candidate_weights.py` (no `run_*.py` subprocess, no
report). **Session 3 (shipped):** `report_profile=lightweight_comparison` in
`run_portfolio_report_for_weights`; factory `--execution-mode standard` Phase 2 report.
**Session 4 (shipped):** `CandidateRunContext` shared monthly + factor/scenario cache.
**Session 5 (shipped):** per-candidate `candidate_manifest.json` readiness JSON;
run-level `run_status` (`full_success`, `partial_success`, `all_failed`, `aborted_fail_fast`).
**Session 6 (shipped):** `run_portfolio_review.py` forwards `--execution-mode standard` to the
factory by default (core and full); `--execution-mode legacy_full` for subprocess parity.

**Session 8 (shipped):** optional Phase 3 full report export via `--full-candidate-reports` and
`--selected-candidates-for-full-report`; `report_profile=full` for HTML/commentary/rolling betas;
`--pdf-mode final_only` triggers one variant PDF rebuild after Phase 3.
**Session 7 (shipped):** `run_compare_ew_rp.py` parses only numeric tail-risk columns from
`var_es_10y.csv` (metadata such as `method` = `historical` is not coerced to float); PDF rebuild
after EW/RP runs is reliable.

**Parallel lightweight reports (shipped, opt-in):**
[Candidate Factory Parallel Lightweight Reports](../exec_plans/2026-05-22_candidate_factory_parallel_reports_plan.md)
adds `--parallel-lightweight-reports` and `--lightweight-report-workers` for eligible
`--execution-mode standard` runs. This is runtime orchestration only: formulas, weights,
comparison semantics, stress scenarios, and full-report/PDF behavior are unchanged.

## Output policy (site/API default)

Factory and downstream compare honor `src/output_policy.py`. CLI default: `--output-profile site_api`
(JSON contracts + cache only; no CSV/TXT/HTML/PNG/PDF by default). Pass `--output-profile full_report`
or `legacy_export` for explicit presentation exports. Phase 2/3 reports receive the same profile via
`run_portfolio_report_for_weights(..., output_profile=...)`. Factory completion writes
`output_manifest.json` under `output_dir_final`.

| Use case | Command |
| --- | --- |
| Core menu factory + compare | `python run_candidate_factory.py --profile core_fast --then-compare` |
| Core sequential regression factory + compare | `python run_candidate_factory.py --profile core_v1 --then-compare` |
| Full menu factory + compare (advanced/research) | `python run_candidate_factory.py --profile default_v1 --then-compare` |
| Core benchmarks only | `python run_candidate_factory.py --profile core_benchmarks --then-compare` |
| Full export per candidate | `python run_candidate_factory.py --profile default_v1 --output-profile full_report` |
| Timing / parallel Phase 2 | add `--parallel-lightweight-reports` (standard mode only) |

These commands are backend/advanced/research operations. Routine product usage should start from
`run_portfolio_review.py` or a future product surface that delegates to the one-candidate Alternatives
Builder wrapper.

`--execution-mode standard` (default) builds weights in-process and runs `lightweight_comparison`
reports for compare-ready snapshots without per-candidate PDF. PDF modes (`--pdf-mode`) are orthogonal
to `output_profile`; Pandoc runs only when PDF flags or `legacy_export` request it.

## Scope

The Candidate Portfolio Factory:

- invokes **existing** root-level `run_*.py` candidate scripts without reimplementing their formulas;
- uses the **same `candidate_id` registry** as [candidate_comparison_spec.md](candidate_comparison_spec.md) (`_REGISTRY_ROWS` in `src/candidate_comparison.py`);
- records a machine-readable **factory run summary** before comparison;
- supports **profiles** (default candidate sets) and **per-step status** (`succeeded`, `failed`, `skipped`, …);
- optionally chains **`run_compare_variants.py`** after builders complete;
- stays **non-binding**: factory output does not change policy release, stress pass/fail, or Selection Engine outcomes.

The factory does **not**:

- replace the portfolio-first `analysis_subject` diagnosis step;
- replace `run_optimization.py` in legacy policy workflows;
- write or overwrite `portfolio_weights.yml` except through the existing policy optimizer entry point (policy is outside the factory batch);
- merge candidate formulas into one optimizer;
- provide product UI/workspace (deferred).

## Problem Statement (V1)

Today, `run_compare_variants.py` / `write_candidate_comparison_outputs` correctly marks registry rows `unavailable` when artifact folders are missing (PSA-008). Comparison quality therefore depends on **which scripts the operator ran manually** before comparison. The factory closes that gap by making the **intended candidate set and run order** explicit and auditable.

## Product Boundary

| Role | Entry | Factory includes... |
| --- | --- | --- |
| **Portfolio-first subject** | `run_report.py --materialize-analysis-subject` via `run_portfolio_review.py` | **No** — must exist before factory output is interpreted |
| **Legacy production policy** | `run_optimization.py` then `run_report.py` on Main | **No** — run only in compatibility workflows |
| **User current (sidecar)** | `run_report.py --materialize-current` | **Optional** — see [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) |
| **Benchmark / optimizer candidates** | Per-family `run_*.py` scripts | **Yes** — factory core |
| **Comparison + decision package** | `run_compare_variants.py` | **Optional tail** (`--then-compare` in Session 11) |

In the portfolio-first workflow, the diagnosed `analysis_subject` is the comparison baseline.
Legacy Main policy output remains available for compatibility. Robust MV and robust scenario paths
are **candidate/benchmark inputs** only unless a future accepted decision changes release policy
([DEC-2026-05-17-007](../../DECISIONS.md)).

## V1 User Decisions (2026-05-17, Session 10)

Recorded defaults when the post-audit plan continues without overrides:

1. **Orchestrate before compare:** V1 adopts a factory layer; comparison remains read-only aggregation.
2. **No formula duplication:** each `candidate_id` maps to one existing entry script (or a documented two-step chain); Session 11 must subprocess or import those scripts, not copy optimization code.
3. **Standalone factory CLI default profile `default_v1`:** all **sixteen** script-backed registry rows (every row except `policy` and `current`). This is a technical CLI default for factory-only advanced/research runs; it is not the default product UX and is not the default `run_portfolio_review.py --mode core` profile.
4. **Skip-existing default with freshness:** when `{artifact_root}/snapshot_10y.json` exists, skip rerunning that candidate only when its `analysis_end` matches the review `analysis_end`; otherwise attempt a rebuild unless `--force` or dependency rules dictate a different outcome.
5. **Failure policy `continue_on_error`:** one failed candidate does not abort the whole factory run; failures appear in the run summary and as `unavailable` / `degraded` in comparison.
6. **Run summary location:** `{output_dir_final}/candidate_factory_run.json` and optional `candidate_factory_run.txt`.
7. **Registry source of truth:** `src/candidate_comparison.py` `_REGISTRY_ROWS`; factory spec table below must stay aligned when registry changes.

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Candidate Portfolio Factory** (this spec) | Orchestration of builder scripts + run summary |
| **Candidate builder** | Single `run_*.py` script that fixes weights and runs the report pipeline for one family |
| **Candidate Comparison** | Read-only merge into `candidate_comparison.json` |
| **Decision package** | Downstream artifacts from `write_candidate_comparison_outputs` |

## Supported End-to-End Workflows

### A. Portfolio-first decision-support run (default)

| Step | Command | Purpose |
| --- | --- | --- |
| 0 Subject | `python run_portfolio_review.py` | Materialize `analysis_subject`, build the default core hypothesis set through backend factory plumbing, and compare through the orchestrator |
| 1 Factory only (advanced) | `python run_candidate_factory.py --profile default_v1` | Build or refresh the full research candidate artifact set after subject diagnostics exist |
| 2 Compare only (advanced) | `python run_compare_variants.py` | Rebuild `candidate_comparison.json` + decision package from existing artifacts |

Factory may implement `--then-compare` to run step 2 automatically after step 1.

### A-legacy. Policy compatibility run

Use only when the intended baseline is generated legacy policy weights.

| Step | Command | Purpose |
| --- | --- | --- |
| 0 Policy | `python run_optimization.py --with-report` (or optimize then `run_report.py`) | Legacy policy weights and Main diagnostics |
| 0b Current (optional) | `python run_report.py --materialize-current` | Current sidecar for No-Trade versus current |
| 1 Factory | `python run_candidate_factory.py --profile default_v1` | Advanced/legacy compatibility refresh of candidate artifact folders |
| 2 Compare | `python run_compare_variants.py` | Compatibility comparison and decision package |

### B. Benchmarks-only refresh

Profile `core_benchmarks`: equal-weight, risk parity, equal-weight by asset class. Use when robust optimizers are too slow for a quick pass.

### C. Manual (legacy, still valid)

Operator runs individual `run_*.py` scripts, then `run_compare_variants.py`. Factory is **not required** for comparison to work; missing folders remain `unavailable`.

## Factory Profiles

Profiles select which registry `candidate_id` values the factory attempts. IDs must exist in `candidate_registry_ids()`.

| Profile id | Candidate IDs included | Typical use |
| --- | --- | --- |
| `core_benchmarks` | `equal_weight`, `risk_parity`, `equal_weight_by_asset_class` | Fast baseline trio |
| `risk_budgets` | `risk_budget_by_asset`, `risk_budget_by_asset_class`, `hierarchical_risk_parity` | Risk-budget family |
| `classic_optimizers` | `minimum_variance`, `minimum_variance_uncapped`, `minimum_variance_advanced`, `maximum_diversification`, `maximum_diversification_uncapped`, `minimum_cvar_constrained`, `minimum_cvar_uncapped` | Traditional optimizer candidates |
| `robust_suite` | `robust_mv_constrained`, `robust_mv_uncapped`, `robust_scenario` | Robust benchmarks only |
| `default_v1` | All sixteen script-backed IDs (union of rows above) | Advanced/research full menu for backend refresh, timing, parity, and evidence generation; not the default product UX |
| `core_v1` | Same six ids as `core_benchmarks` + `risk_budgets` (menu order) | Regression / sequential lightweight core menu |
| `core_fast` | Same six ids as `core_v1` | Routine core menu with parallel Phase 2 lightweight reports by default (4 workers); disable via `--no-parallel-lightweight-reports` |
| `explicit_list` | User-supplied `--candidates id1,id2,...` | Ad hoc reruns |

`policy` and `current` are **never** started by factory profiles; they use the workflows in [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) and policy runners.

## Registry and Entry Scripts

Paths are relative to the **project root** (repository root). `artifact_root` must match `candidate_comparison` registry strings exactly.

| `candidate_id` | `role` | Entry script(s) | `artifact_root` | Prerequisites |
| --- | --- | --- | --- | --- |
| `equal_weight` | benchmark | `run_equal_weight.py` | `equal-weight portfolio` | Valid `config.yml`, data cache |
| `equal_weight_by_asset_class` | benchmark | `run_equal_weight_by_asset_class.py` | `equal-weight by asset-class portfolio` | Same |
| `hierarchical_risk_parity` | benchmark | `run_hierarchical_risk_parity.py` | `hierarchical risk parity portfolio` | Same |
| `maximum_diversification` | optimizer_candidate | `run_maximum_diversification.py` | `maximum diversification portfolio` | Same |
| `maximum_diversification_uncapped` | optimizer_candidate | `run_maximum_diversification_unconstrained.py` | `maximum diversification unconstrained portfolio` | Same |
| `minimum_cvar_constrained` | optimizer_candidate | `run_minimum_cvar_constrained.py` | `minimum cvar constrained portfolio` | Same |
| `minimum_cvar_uncapped` | optimizer_candidate | `run_minimum_cvar_uncapped.py` | `minimum cvar uncapped portfolio` | Same |
| `minimum_variance` | optimizer_candidate | `run_minimum_variance.py` | `minimum variance portfolio` | Same |
| `minimum_variance_advanced` | optimizer_candidate | `run_minimum_variance_advanced.py` | `minimum variance advanced portfolio` | Same |
| `minimum_variance_uncapped` | optimizer_candidate | `run_minimum_variance_uncapped.py` | `minimum variance uncapped portfolio` | Same |
| `risk_budget_by_asset` | benchmark | `run_risk_budget_by_asset.py` | `risk budget by asset portfolio` | Same |
| `risk_budget_by_asset_class` | benchmark | `run_risk_budget_by_asset_class.py` | `risk budget by asset-class portfolio` | Same |
| `risk_parity` | benchmark | `run_risk_parity.py` | `risk parity portfolio` | Same |
| `robust_mv_constrained` | optimizer_candidate | `run_robust_mean_variance_constrained.py` | `robust mean variance constrained portfolio` | Same |
| `robust_mv_uncapped` | optimizer_candidate | `run_robust_mean_variance_uncapped.py` | `robust mean variance uncapped portfolio` | Same |
| `robust_scenario` | robust_candidate | `run_robust_scenario_optimization.py` then `run_robust_scenario_portfolio_report.py` | `robust scenario portfolio` | Policy `run_report.py` must have produced `scenario_library_normalized.json` and `stress_report.json` under `output_dir_final` |

**Policy row (`policy`):** `run_optimization.py` + `run_report.py` on Main; legacy compatibility
only, not invoked by factory profiles.

**Current row (`current`):** `run_report.py --materialize-current` — optional step 0b.

When `_REGISTRY_ROWS` changes in code, update this table and [candidate_portfolios_spec.md](candidate_portfolios_spec.md) in the same change set.

## Per-Step Execution Rules

For each `candidate_id` in the active profile:

1. Resolve `artifact_root` under project root.
2. If `--skip-existing` (default) and `{artifact_root}/snapshot_10y.json` exists and `--force` is not set → status `skipped_existing` **only when freshness is `fresh`** (review `analysis_end` known and matches the candidate snapshot).
3. If prerequisites fail (e.g. robust scenario missing scenario library) → status `skipped_dependency` with reason code; do not throw away the whole run unless `--fail-fast` (Session 11 optional flag).
4. Otherwise invoke entry script(s) in order with project Python, same `config.yml` as policy run.
5. On subprocess non-zero exit → status `failed` with `exit_code` and stderr tail (truncated); continue unless `--fail-fast`.
6. On success → status `succeeded`; verify minimum comparison inputs: `snapshot_10y.json` present (else `failed` with `missing_snapshot_after_build`).

Freshness addendum (RM-902 / RM-973, supersedes item 2): the skip-existing rule is date-gated. Factory must read
`snapshot_10y.json.analysis_end` before reusing an existing candidate artifact. Reuse is allowed
only when that value matches the review `analysis_end`, resolved from
`{output_dir_final}/analysis_subject/` first and Main artifacts second. When review `analysis_end`
cannot be resolved, `freshness_status` is `unchecked` and the factory **rebuilds** (warning
`unchecked_candidate_snapshot_rebuild_attempted:{candidate_id}:review_analysis_end_unavailable`);
it must **not** emit `skipped_existing`. Stale snapshots are rebuilt, not silently skipped. If a
builder exits 0 but the candidate `snapshot_10y.json` remains stale, the step status is `failed`
with reason `stale_snapshot_after_build`.

Config fingerprint addendum (RM-976 / G2): reuse also requires
`snapshot_10y.json.candidate_config_fingerprint` to match the review run fingerprint computed from
`config.yml` (investor currency, sorted tickers, `risk_budgeting`, min/max single-security weight
bounds). The factory writes `config_fingerprint` at the run root and per-step
`expected_config_fingerprint` / `snapshot_config_fingerprint`. When the date matches but the
fingerprint does not, `freshness_status` is `stale_config` and the factory rebuilds (warning
`stale_candidate_config_fingerprint_rebuild_attempted:{candidate_id}:…`). After build, mismatch
fails with `stale_config_fingerprint_after_build`. New reports stamp the fingerprint on all window
snapshots via `run_portfolio_report_for_weights`.

**Robust scenario chain:** factory runs optimization script first; on success runs portfolio report script. One factory step row may represent the chain; both commands appear in `entry_commands` array in the run summary.

**Ordering within `default_v1`:** run `core_benchmarks` first, then `risk_budgets`, then `classic_optimizers`, then `robust_suite` (robust last because of policy-report dependencies and runtime). Candidate weight/build orchestration remains menu-ordered. In `standard` mode only, lightweight comparison reports may run concurrently when the operator opts in with `--parallel-lightweight-reports`; final step registration still follows candidate menu order.

### Operational limits and deferred improvements (RM-920–RM-922)

**Current state:** freshness gating (RM-902) prevents silent reuse of stale `snapshot_10y.json` when
`analysis_end` differs from the review date. Factory statuses (`succeeded`, `skipped_existing`,
`failed`, stale rebuild warnings) are the operator source of truth.

**Deferred gap:** rebuilding **all** script-backed optimizers in `default_v1` is intentionally
sequential and can exceed practical one-shot `run_portfolio_review.py` or agent session limits when
many candidates are stale. That is an **operational** limitation, not a broken comparison contract.

**Implemented product model (Session 09 / RM-939):**

| Mode | CLI | Factory profile | Intended scope |
| --- | --- | --- | --- |
| **core-run** (default, Wave 2 — [Performance Wave 2 ExecPlan](../exec_plans/2026-05-24_blocks_1_5_performance_wave2_plan.md)) | `python run_portfolio_review.py --with-candidates` or `python run_portfolio_review.py --mode core --with-candidates` | `core_fast` | Same six candidate ids as `core_v1`; factory `execution_mode=standard`; shared `ReviewRunContext` for explicit candidate/core_fast orchestration; diagnosis-only core materialization uses `--no-review-run-context`; parallel Phase 2 lightweight reports by default; site/API JSON output. Disable parallel with `--no-parallel-lightweight-reports`. Acceptance: E2E ≤ 300 s warm cache. |
| **core sequential regression** | `python run_portfolio_review.py --candidate-profile core_v1` or `python run_candidate_factory.py --profile core_v1` | `core_v1` | Same six candidate ids as `core_fast`, but sequential Phase 2. Retained for parity/debug vs pre-Wave 2 core menu. |
| **core-fast factory only** | `python run_candidate_factory.py --profile core_fast` | `core_fast` | Standalone backend routine core batch with the same default parallel lightweight-report behavior as portfolio-first core review. |
| **full-run** | `python run_portfolio_review.py --mode full` | `default_v1` | Explicit full-menu refresh (16 candidates) for advanced/research evidence; factory `execution_mode=standard` (phased weights + lightweight report); site/API JSON output |
| **full-run (legacy builders)** | `python run_portfolio_review.py --mode full --execution-mode legacy_full` | `default_v1` | Subprocess `run_*.py` chain for parity/debug |

`--candidate-profile` overrides `--mode` when an explicit profile is required. Partial-menu disclosure
is emitted in `candidate_comparison.json` → `candidate_menu` and in the decision-package summary.

**Resumable factory (RM-979 / RM-921):** `{output_dir_final}/candidate_factory_manifest.json`
records `run_checksum` (profile, candidate menu, `analysis_end`, `config_fingerprint`) and
per-step `completed_steps`. `python run_candidate_factory.py --resume` skips `succeeded` and
fresh `skipped_existing` steps when the checksum matches; failed steps are retried. Manifest is
updated after each step so an interrupted run can resume without redoing succeeded builders.
Parallel candidate **builders** remain future scope; shipped parallelism is limited to Phase 2
`lightweight_comparison` report generation after candidate weights exist. Universe-file hashing and
weight-source keys remain future scope.

## Canonical Factory Run Artifacts

| Field | Value |
| --- | --- |
| File name | `candidate_factory_run.json` |
| Location | `{output_dir_final}/candidate_factory_run.json` |
| Companion (export-only) | `{output_dir_final}/candidate_factory_run.txt` |
| Resume manifest | `{output_dir_final}/candidate_factory_manifest.json` (`candidate_factory_manifest_v1`) |
| Schema version | `candidate_factory_run_v1` |

### Top-level JSON contract (`candidate_factory_run_v1`)

```json
{
  "schema_version": "candidate_factory_run_v1",
  "diagnostic_only": true,
  "run_status": "full_success",
  "generated_at": "ISO-8601",
  "factory_profile_id": "default_v1",
  "project_root": ".",
  "output_dir_final": "Main portfolio",
  "config_path": "config.yml",
  "analysis_end": "YYYY-MM-DD",
  "config_fingerprint": "sha256-hex",
  "options": {
    "skip_existing": true,
    "force": false,
    "fail_fast": false,
    "resume": false,
    "then_compare": false,
    "pdf_mode": "none",
    "execution_mode": "standard",
    "parallel_lightweight_reports": true,
    "parallel_lightweight_reports_effective": true,
    "lightweight_report_workers": 4,
    "full_candidate_reports": false,
    "selected_candidates_for_full_report": null
  },
  "parallel_lightweight_report_summary": {
    "requested": true,
    "effective": true,
    "status": "parallel",
    "workers": 4,
    "submitted_count": 2,
    "completed_count": 2,
    "submitted_candidate_ids": ["equal_weight", "risk_parity"],
    "registered_candidate_ids": ["equal_weight", "risk_parity"],
    "fallback_reasons": [],
    "wall_clock_seconds": 12.345
  },
  "timing_summary": {
    "steps_with_timing": 0,
    "builder_core_seconds": 0.0,
    "report_seconds": 0.0,
    "pdf_seconds": 0.0,
    "total_seconds": 0.0
  },
  "manifest": {
    "path": "Main portfolio/candidate_factory_manifest.json",
    "run_checksum": "sha256-hex",
    "resume_manifest_active": false
  },
  "steps": [],
  "summary": {
    "total": 16,
    "succeeded": 0,
    "failed": 0,
    "skipped_existing": 0,
    "skipped_dependency": 0,
    "rebuilt_stale": 0,
    "resumed_from_manifest": 0
  },
  "execution_summary": {
    "build_steps_executed": 0,
    "build_steps_succeeded": 0,
    "build_steps_failed": 0,
    "in_process_build_steps": 0,
    "builder_invoked": 0,
    "builder_invoked_succeeded": 0,
    "builder_invoked_failed": 0,
    "reused_existing": 0,
    "reused_existing_snapshot": 0,
    "reused_existing_weights": 0,
    "resumed_from_manifest": 0,
    "skipped_dependency": 0,
    "rebuilt_candidate_ids": [],
    "failed_build_candidate_ids": [],
    "reused_candidate_ids": [],
    "resumed_candidate_ids": [],
    "skipped_dependency_candidate_ids": [],
    "no_skip_existing_requested": false,
    "resume_requested": false
  },
  "warnings": [],
  "next_recommended_command": "python run_compare_variants.py"
}
```

### Per-step object

| Field | Type | Description |
| --- | --- | --- |
| `candidate_id` | string | Registry id |
| `display_name` | string | From registry |
| `role` | string | From registry |
| `artifact_root` | string | Expected output folder |
| `status` | string | `succeeded` \| `failed` \| `skipped_existing` \| `skipped_dependency` \| `skipped_profile` |
| `execution_action` | string | What happened operationally, including `builder_invoked`, `builder_invoked_failed`, `weights_built`, `weights_built_failed`, `lightweight_report_built`, `lightweight_report_reused_weights`, `lightweight_report_failed`, `full_report_built`, `full_report_failed`, `full_report_skipped_existing`, `reused_existing_snapshot`, `reused_existing_weights`, `resumed_from_manifest`, `skipped_dependency`, or `failed_before_build`. |
| `entry_commands` | array of strings | Commands attempted (repr for audit) |
| `exit_code` | int or null | Last command exit code when applicable |
| `duration_seconds` | number | Wall time for the step (factory subprocess, all paths) |
| `builder_core_seconds` | number or null | From `builder_runtime_timing.json` when present |
| `report_seconds` | number or null | From `builder_runtime_timing.json` when present |
| `pdf_seconds` | number or null | From `builder_runtime_timing.json` when present (often `0` under `--pdf-mode none`) |
| `total_seconds` | number or null | Bucket sum when timing file present; else mirrors `duration_seconds` |
| `reason_code` | string or null | Machine code when not succeeded |
| `message` | string or null | Short English explanation |
| `builder_status` | string or null | Optional; raw `status` from `{artifact_root}/summary.json` when a builder FAIL_* was mapped (Session 02) |
| `builder_reason` | string or null | Optional; builder `reason` string from `summary.json` when present |
| `expected_analysis_end` | string or null | Review `analysis_end` used for freshness checks. Prefer `{output_dir_final}/analysis_subject/` metadata/snapshots, then Main metadata/snapshots. |
| `expected_config_fingerprint` | string or null | Review config fingerprint for the step (RM-976). |
| `snapshot_analysis_end` | string or null | `analysis_end` read from candidate `snapshot_10y.json` before reuse or after build. |
| `snapshot_config_fingerprint` | string or null | `candidate_config_fingerprint` read from candidate `snapshot_10y.json` when present. |
| `freshness_status` | string or null | `fresh` when date and config fingerprint match; `stale` when date mismatches; `stale_config` when date matches but fingerprint mismatches or is missing; `missing` when no snapshot; `unchecked` when no review date. |
| `resume_from_manifest` | boolean or null | Optional; `true` when `--resume` reused a prior manifest entry without invoking builders. |
| `robust_paths_disclosure` | object or null | Present for `robust_mv_constrained`, `robust_mv_uncapped`, and `robust_scenario` (Session 07 / RM-977). λ resolution snapshot or Main prerequisite checklist; see [robust_mv_spec.md](robust_mv_spec.md) and comparison `construction_disclosure.robust_paths`. |

### Manifest JSON (`candidate_factory_manifest_v1`)

Written incrementally during a factory run and read on `--resume`.

| Field | Description |
| --- | --- |
| `schema_version` | `candidate_factory_manifest_v1` |
| `run_checksum` | SHA-256 of profile id, comma-separated candidate ids, `analysis_end`, `config_fingerprint` |
| `factory_profile_id` | Profile used for the run |
| `candidate_ids` | Ordered menu for this run |
| `analysis_end` | Review date used for freshness |
| `config_fingerprint` | Review config fingerprint (RM-976) |
| `completed_steps` | Map of `candidate_id` → `{status, reason_code, recorded_at}` |
| `last_completed_candidate_id` | Last step persisted (crash recovery hint) |
| `updated_at` | ISO-8601 timestamp |

Resume skips a prior `succeeded` or fresh `skipped_existing` entry only when `run_checksum` matches the current run and the candidate snapshot is still fresh.

If `--resume` reuses a completed manifest step while `--no-skip-existing` is also requested, the
factory must write an explicit warning
`resume_manifest_reused_completed_step_despite_no_skip_existing:{candidate_id}:builder_not_rerun`.
This prevents reports from implying that a full rebuild occurred when the resume manifest actually
reused a candidate.

### Reason codes (V1)

| Code | Meaning |
| --- | --- |
| `skipped_existing` | `snapshot_10y.json` already present and skip-existing active |
| `skipped_dependency` | Prerequisite artifacts missing (robust_scenario: `scenario_library_normalized.json` and/or `stress_report.json` under `output_dir_final`; message lists missing names) |
| `missing_snapshot_after_build` | Script exited 0 but comparison minimum files absent |
| `stale_snapshot_after_build` | Script exited 0 but `snapshot_10y.json.analysis_end` still does not match the review `analysis_end` |
| `stale_config_fingerprint_after_build` | Script exited 0 but `snapshot_10y.json.candidate_config_fingerprint` still does not match review `config_fingerprint` |
| `subprocess_failed` | Builder returned non-zero exit and no FAIL_* in `summary.json` |
| `subprocess_timeout` | Reserved; optional timeout in Session 11 |
| `unknown_candidate_id` | ID not in registry (explicit list mode) |
| `builder_fail_config` | Builder `summary.json` status `FAIL_CONFIG` |
| `builder_fail_data` | Builder `summary.json` status `FAIL_DATA` |
| `builder_infeasible_universe` | Builder `FAIL_INFEASIBLE_UNIVERSE` |
| `builder_infeasible_targets` | Builder `FAIL_INFEASIBLE_TARGETS` |
| `builder_infeasible_bounds` | Builder `FAIL_INFEASIBLE_BOUNDS` |
| `builder_infeasible_vol_target` | Builder `FAIL_INFEASIBLE_VOL_TARGET` |
| `builder_fail_numerical` | Builder `FAIL_NUMERICAL` |
| `builder_fail_no_assets` | Builder `FAIL_NO_ASSETS` |
| `builder_failed` | Other builder `FAIL_*` status not listed above |

After each build attempt, when `snapshot_10y.json` is absent or the subprocess exits non-zero, the factory reads `{artifact_root}/summary.json` when present and maps builder `status`/`reason` to the codes above. `missing_snapshot_after_build` applies only when the subprocess exited zero, no snapshot exists, and `summary.json` does not report a FAIL_* status.

Beginning with Optimization Engine Session 06, factory step `status` remains an orchestration
status, not optimizer quality. A step can be `succeeded` because the script exited and
`snapshot_10y.json` exists while the optimizer solve was fallback or approximate. When
`baseline_weights_metadata.json.optimizer_run_metadata` or `summary.json` exposes solver quality,
the step copies these fields:

| Field | Meaning |
| --- | --- |
| `optimization_status_source` | Artifact path used for quality evidence, such as `baseline_weights_metadata.json.optimizer_run_metadata`. |
| `optimization_quality_status` | Normalized quality: `clean_solve`, `approximate_fallback`, `approximate_solver`, `failed_solver`, `failed`, or `unknown`. |
| `optimization_quality_family` | Grouped quality: `clean`, `approximate`, `failed`, or `unknown`. |
| `optimizer_fallback_used` | Boolean fallback disclosure. |
| `optimizer_fallback_reason` | Source fallback reason when available. |
| `optimizer_solver_status` | Source solver status when available. |

These fields are diagnostic disclosure only. They do not rerun builders, change weights, or convert
factory orchestration statuses. Downstream comparison uses them to avoid treating fallback or failed
optimization quality as ordinary available evidence.

Beginning with Optimization Engine Session 07, the `robust_scenario` chain writes normalized solver
quality through `robust scenario portfolio/baseline_weights_metadata.json.optimizer_run_metadata`
(`robust_scenario_optimizer_run_metadata_v1`) when the source
`robust_optimization_v1_summary.json` is present. The factory reads that block with the same fields
above, so robust scenario SLSQP status is visible separately from factory orchestration success.

Human-readable `.txt` summarizes profile, counts, failed IDs, and the next recommended command. Wording must stay **diagnostic** (no buy/sell, no "recommended portfolio").

### Run status (`run_status`, Session 5)

Top-level `run_status` summarizes whether the factory run completed with partial failures:

| Value | Meaning |
| --- | --- |
| `full_success` | No `failed` steps |
| `partial_success` | Mix of `succeeded` / `skipped_existing` and `failed` (default `continue_on_error`) |
| `all_failed` | Every counted step `failed` (no productive rows) |
| `aborted_fail_fast` | `--fail-fast` stopped the loop after the first `failed` step |

Exit code remains `1` when `summary.failed > 0` (including partial success). Operators use
`run_status` and per-candidate manifests for API/resume UX without parsing every factory step.

### Per-candidate manifest (`candidate_manifest_v1`, Session 5)

After each factory step, `{artifact_root}/candidate_manifest.json` records readiness for
comparison and partial phase failure (weights without `snapshot_10y.json`).

| Field | Description |
| --- | --- |
| `schema_version` | `candidate_manifest_v1` |
| `candidate_id`, `display_name`, `role`, `artifact_root` | Registry identity |
| `factory_step` | Copy of orchestration status, `execution_action`, `phases_completed`, `report_profile` |
| `review_context` | Expected vs snapshot `analysis_end` / config fingerprint, `freshness_status` |
| `artifacts` | Booleans: `weights_present`, `snapshot_10y_present`, `stress_report_present`, … |
| `comparison_readiness` | `status` (`ready`, `weights_only`, `not_ready`, `skipped_dependency`), `ready_for_comparison` |
| `partial_failure` | Optional when weights exist but report/snapshot failed |

Factory steps may include `candidate_manifest_path` (relative to project root, POSIX slashes).
Implementation: `src/candidate_manifest.py`; written from `_persist_manifest_step`.

## Integration with Comparison and Decision Package

After factory completes (or after manual builders):

1. `run_compare_variants.py` calls `write_candidate_comparison_outputs`.
2. Comparison stays read-only and validates whether `candidate_factory_run.json` is current evidence
   for the comparison context before copying `steps[]` into candidate rows.
3. Downstream artifacts (robustness, health, selection, action, monitoring, journal, decision package summary) emit when comparison runs; factory does not write them directly.

Blocks 1-5 reliability Session 03 (`RM-1012`) adds a comparison-side trust boundary: missing, stale,
or not-authoritative factory summaries are reported in `candidate_comparison.json.candidate_menu`,
but their per-step factory evidence is not treated as current row evidence. This means an old failed
factory step cannot make a fresh candidate row unavailable after a later comparison rebuild, and an
old successful step cannot be read as proof that the current comparison was refreshed by factory.

If `--then-compare` is set and comparison fails, factory run summary should add warning `comparison_failed` with nested error message; factory step statuses remain authoritative for builders.

## Runtime PDF modes (Session 1)

Factory orchestration controls **per-candidate** Pandoc rebuilds only. Standalone
`python run_equal_weight.py` (and siblings) keep today's default full PDF behavior unless
`PORTFOLIO_SKIP_VARIANT_PDF=1` is set in the environment.

| `--pdf-mode` | Subprocess env | Per-candidate `try_rebuild_pdfs_after_variant` |
| --- | --- | --- |
| `none` (default) | `PORTFOLIO_SKIP_VARIANT_PDF=1` | Skipped in each `run_*.py` |
| `final_only` | `PORTFOLIO_SKIP_VARIANT_PDF=1` | Skipped during factory loop; one-shot final PDF rebuild is future scope (Session 8+) |
| `per_candidate` | env unset | Legacy behavior (~181s per candidate when Pandoc succeeds) |

Implementation: `src/variant_builder_runtime.py` (`maybe_rebuild_pdfs_after_variant` /
`maybe_rebuild_pdfs_only`); factory passes env via `subprocess_env_for_pdf_mode` in
`src/candidate_factory.py`.

## Per-step timing buckets (Session 1)

When a builder writes `{artifact_root}/builder_runtime_timing.json`, factory steps include:

| Field | Description |
| --- | --- |
| `builder_core_seconds` | Data load + weight construction (wall clock) |
| `report_seconds` | `run_portfolio_report_for_weights` (wall clock) |
| `pdf_seconds` | Variant PDF rebuild (0 when skipped) |
| `total_seconds` | Sum of buckets when file present; else factory falls back to `duration_seconds` |

Run-level `timing_summary` aggregates timing buckets across steps that expose timing fields.
Run-level `execution_summary` separately discloses build/reuse counts across legacy subprocess
builders and in-process `fast` / `standard` phases. Human summary in `candidate_factory_run.txt`.

## Execution modes and Phase 1 weights (Session 2)

| `--execution-mode` | Builder path | Report | Typical use |
| --- | --- | --- | --- |
| `legacy_full` (default) | Subprocess each `run_*.py` | Full (inside builder) | Parity / debug |
| `fast` | In-process `build_candidate_weights` | None (Phase 1 only) | API / weights refresh |
| `standard` | In-process weights (Phase 1) | `lightweight_comparison` (Phase 2) | Portfolio-first review default (`run_portfolio_review.py`) |

**Phase 3 (optional, Session 8):** after Phases 1–2 (or when `weights.json` already exists), export
`report_profile=full` for all candidates in the run (`--full-candidate-reports`) or a subset
(`--selected-candidates-for-full-report`). Skip when `report.html` exists and `--skip-existing`
(unless `--force`). Factory step `execution_action`: `full_report_built`, `full_report_failed`,
`full_report_skipped_existing`. With `--pdf-mode per_candidate`, Pandoc runs after each Phase 3
candidate; with `final_only`, one `full_report_final_pdf_rebuild` step after all Phase 3 targets.

Implementation: `src/candidate_run_context.py` (`prepare_candidate_run_context`,
`FactoryFactorStressInputs`), `src/candidate_weights.py` (`build_candidate_weights`,
`write_candidate_weights`). One shared `load_monthly_data_shared` and one invariant factor/scenario
preload per factory run when mode is `fast` or `standard`.

### Shared run context (Session 4)

`CandidateRunContext` holds data reused across all candidates in one factory invocation.
`run_portfolio_report_for_weights(..., run_context=...)` skips reloading monthly data and reuses
cached factor matrices when the context provides `factor_stress`.

| Input | Scope | Notes |
| --- | --- | --- |
| `monthly_data` (`load_monthly_data_shared`) | **Invariant** | Same `config.yml` tickers, `analysis_end`, FX/rf/benchmark |
| `assets_meta`, `cash_proxy`, `rf_source`, `local_benchmark_map` | **Invariant** | Resolved once in `prepare_candidate_run_context` |
| `report_tickers` | **Invariant** | `portfolio_total_tickers` on full config universe |
| `robust_mv_lambda` resolution | **Invariant** | Shared by `robust_mv_*` weight builders |
| Daily returns panel for factor betas | **Invariant** | `load_daily_asset_returns_shared` once per run |
| `recession_factor_returns`, `scenario_episode_factor_returns` | **Invariant** | `build_factor_matrix` once per `analysis_end` |
| Asset factor betas 5Y/10Y (universe) | **Invariant** | Precomputed on full `report_tickers`; sliced per candidate |
| Portfolio weights | **Candidate-dependent** | Each `weights.json` |
| Portfolio returns / snapshots / stress PnL | **Candidate-dependent** | From weights + shared monthly panel |
| `beta_tickers` (positive-weight legs) | **Candidate-dependent** | Subset of universe; portfolio betas recomputed |
| Scenario library JSON under candidate folder | **Candidate-dependent** | Built per report output dir |
| `robust_scenario` Main prerequisites | **Invariant path** | Reads `{output_dir_final}/scenario_library_normalized.json` once per run |

### Shared Evidence Context v2 (shipped — RM-982)

**Status:** Shipped (Sessions 1–6, 2026-05-23). Closed in
[Shared Evidence ExecPlan](../exec_plans/2026-05-23_candidate_factory_shared_evidence_plan.md).
Timing evidence:
[Session 06 timing audit](../audits/2026-05-23_candidate_factory_shared_evidence_session06_timing_audit.md).

**Purpose:** extend Session 4 `CandidateRunContext` so Phase 2 `lightweight_comparison` does not
recompute invariant evidence 16× per `default_v1` menu. Orchestration and caching only — formulas,
stress scenario definitions, and comparison semantics unchanged.

**Evidence:** [Shared evidence audit](../audits/2026-05-23_candidate_factory_shared_evidence_audit.md)
(pre-implementation map); post-ship timing in Session 06 audit above.

| Input | Scope (v2 target) | Session | Notes |
| --- | --- | --- | --- |
| `monthly_data`, daily universe, universe betas 5Y/10Y, recession/scenario factors | **Invariant** | 4 (shipped) | Existing `FactoryFactorStressInputs` |
| Asset metrics all tickers × windows | **Invariant** | 2 | Precompute in context; per-candidate CSV export may remain |
| Correlation matrices (returns only) | **Invariant** | 2 | RC_vol still per candidate |
| Monthly `cov_base` for stress | **Invariant** | 2 | Pass into `run_stress` optionally |
| Extended-column universe betas (`FACTOR_COLUMN_ORDER`) | **Invariant** | 3 | Remove per-candidate OLS rebuild |
| Daily panel for tail VaR/ES | **Invariant** | 3 | Reuse context daily; no second `load_daily_asset_returns_shared` |
| Weekly asset returns R + factor matrix X (5Y/10Y) | **Invariant** | 4 | Shared frames for regression/decomposition/PCA |
| Prepared synthetic stress `r_asset` per scenario | **Invariant** | 5 | Candidate PnL = `w @ r_asset` + existing RC/historical legs |
| `save_inputs` monthly panel copy | **Optional skip** | 3 | Lightweight may omit duplicate `results_csv/inputs/` |
| Portfolio returns, metrics, stress PnL, snapshots | **Candidate-dependent** | — | Unchanged |
| Per-candidate `stress_report.json`, scenario library | **Candidate-dependent** | — | Assembly from shared + weights |

**Parity contract:** `tests/test_report_profile.py` (full vs lightweight); Session 06
comparison-critical fields (`weights.json`, stress status/PnL summaries) must match pre-change
baseline within documented tolerance.

**Timing (measured 2026-05-23):** sequential Phase 2 `report_seconds` sum **857.7 s** vs pre-change
baseline **1192.9 s** (**−28.1%** on full `default_v1` menu, warm cache, isolated tmp smoke).
ExecPlan target was −35% to −55%; gap documented in Session 06 audit (remaining:
`macro_regime`, `daily_tail_risk`, `portfolio_pca` per candidate). Re-run:
`python scripts/shared_evidence_session06_timing_smoke.py`.

Per-candidate artifacts (minimum):

- `weights.json`, `weights.txt`, `summary.json`
- `baseline_weights_metadata.json` when the family exports metadata
- `candidate_weights_build.json` (`candidate_weights_build_v1`) with `analysis_end`,
  `config_fingerprint`, `status`, `phases_completed: ["weights"]`
- `builder_runtime_timing.json` with `report_seconds: 0` (core only)

Factory step `execution_action` values: `weights_built`, `weights_built_failed`,
`reused_existing_weights`, `reused_existing_snapshot`, `lightweight_report_built`,
`lightweight_report_reused_weights`, `lightweight_report_failed`. Skip-existing:
`fast` — fresh `candidate_weights_build.json`; `standard` — fresh `snapshot_10y.json`
(weights-only skip when snapshot stale/missing).

## Report profiles (Session 3)

`run_portfolio_report_for_weights(..., report_profile=...)`:

| Profile | Snapshots / stress | Skipped (presentation) |
| --- | --- | --- |
| `full` (default) | All windows + `stress_report.json` | — |
| `lightweight_comparison` | `snapshot_10y.json` + `stress_report.json` (10Y window only: tail-risk loop and snapshot writes; `snapshot_index.json` lists 10Y only) | HTML report, commentary, stress_commentary, rolling beta CSV/PNG/HTML, `snapshot_assets.json`, `snapshot_3y.json`, `snapshot_5y.json`, most optional CSV exports |

Comparison reads `snapshot_10y.json` metrics and `stress_report.json` / snapshot stress suite;
rows should be `available` (not `degraded` from `summary.json`-only) when Phase 2 completes.

Implementation: `src/report_profile.py`, factory `_execute_lightweight_report`.

`robust_scenario` in-process: runs scenario optimization into `{output_dir_final}` then copies
weights into `robust scenario portfolio/` (same prerequisites as subprocess chain).

## Parallel lightweight reports (opt-in)

`--parallel-lightweight-reports` applies only to Phase 2 `lightweight_comparison` reports in
`--execution-mode standard`. Phase 1 candidate weights are still built and validated in candidate
menu order. When a candidate needs a lightweight report, the factory may submit the candidate-owned
report work to a `ThreadPoolExecutor`; the coordinator remains the only writer of run-level
`candidate_factory_run.json`, `candidate_factory_manifest.json`, and summary counters.

Eligibility:

| Condition | Behavior |
| --- | --- |
| `--execution-mode standard`, no `--fail-fast`, `--pdf-mode` not `per_candidate`, no Phase 3 full reports | Parallel lightweight reports are effective. |
| `--fail-fast` | Sequential fallback, because the run must stop immediately on the first failed candidate. |
| `--pdf-mode per_candidate` | Sequential fallback, because per-candidate PDF side effects are outside the lightweight-report parallel scope. |
| `--full-candidate-reports` or `--selected-candidates-for-full-report` | Sequential fallback, because Phase 3 full report export is outside the parallel scope. |
| `--execution-mode fast` or `legacy_full` | Sequential/no-op fallback; there is no Phase 2 lightweight report batch to parallelize. |

`--lightweight-report-workers N` caps the thread count. When omitted, the factory uses the smaller
of `4` and the number of candidate reports to submit, with a minimum of `1`.

When parallel mode is requested, `candidate_factory_run.json` includes
`parallel_lightweight_report_summary`. `status` is `parallel` when reports were submitted,
`parallel_no_work` when the mode was effective but no report needed to run, and
`sequential_fallback` when a requested run was not eligible. `submitted_candidate_ids` and
`registered_candidate_ids` are recorded in candidate menu order even if worker completion order
differs. `candidate_factory_run.txt` prints the same status, worker count, submitted/completed
counts, optional wall-clock seconds, and fallback reasons.

## CLI Contract

Entry point at repository root:

```bash
python run_candidate_factory.py [--profile PROFILE] [--candidates ID,ID,...]
  [--skip-existing | --force] [--fail-fast] [--resume] [--then-compare]
  [--pdf-mode none|final_only|per_candidate]
  [--execution-mode fast|standard|legacy_full]
  [--parallel-lightweight-reports]
  [--lightweight-report-workers N]
  [--full-candidate-reports]
  [--selected-candidates-for-full-report ID,ID,...]
  [--config PATH]
```

| Flag | Default | Behavior |
| --- | --- | --- |
| `--profile` | `default_v1` | Select factory profile. This standalone CLI default is the full advanced/research menu, not the product default core review profile. |
| `--candidates` | (none) | Overrides profile with explicit list |
| `--skip-existing` | on | Skip when `snapshot_10y.json` exists |
| `--force` | off | Rerun even when snapshot exists |
| `--fail-fast` | off | Stop factory on first failed step |
| `--resume` | off | Skip prior `succeeded` / fresh `skipped_existing` steps when manifest checksum matches |
| `--then-compare` | off | Run `run_compare_variants.py` after factory |
| `--pdf-mode` | `none` | Per-candidate PDF policy for factory subprocesses (see Runtime PDF modes) |
| `--execution-mode` | `legacy_full` | `fast`/`standard` = in-process phases; `legacy_full` = subprocess builders |
| `--parallel-lightweight-reports` | off | Opt into concurrent Phase 2 `lightweight_comparison` reports for eligible `standard` runs; sequential fallback is automatic for `--fail-fast`, `--pdf-mode per_candidate`, Phase 3 full reports, and non-`standard` execution modes |
| `--lightweight-report-workers` | auto | Maximum workers for `--parallel-lightweight-reports`; default is `min(4, submitted report count)` |
| `--full-candidate-reports` | off | Phase 3: `report_profile=full` for every candidate in this run |
| `--selected-candidates-for-full-report` | (none) | Phase 3 subset; enables Phase 3 when set without `--full-candidate-reports` |
| `--config` | `config.yml` | Config path passed to builders |

Exit codes:

- `0` — all attempted steps succeeded or were skipped intentionally; no fail-fast abort
- `1` — one or more `failed` steps, or fail-fast abort
- `2` — configuration or registry validation error before any builder runs

Operator playbooks (reason codes, recovery, partial menu): [operational_runbook.md](../operational_runbook.md) §8.

`next_recommended_command` is set from run context (resume after failures, full rebuild when manifest checksum mismatches, otherwise comparison). Human summary: `candidate_factory_run.txt` lists failed `reason_code` values and the factory-only exit hint.

## Verification

Governance regression (Phase 14 Session 08 / `RM-978`): golden JSON fixtures and contract tests —
see [TESTING.md](../../TESTING.md) § Candidate Factory Governance Wave Bundle;
regenerate with `python tests/candidate_factory_golden_inputs.py`.

| Milestone | Verification |
| --- | --- |
| **Operator runbook (Session 10 / RM-980)** | [operational_runbook.md](../operational_runbook.md) §8; `python scripts/verify_docs.py`; registry table matches `_REGISTRY_ROWS` |
| **Implementation** | `tests/test_candidate_factory.py`, `tests/test_candidate_factory_contract.py`; smoke: factory + compare increases `available` count on a fixture project |

## Related Documents

- [candidate_portfolios_spec.md](candidate_portfolios_spec.md) — builder families and shared behavior
- [candidate_comparison_spec.md](candidate_comparison_spec.md) — canonical comparison contract
- [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) — policy/current outside factory profiles
- [robust_scenario_optimization_spec.md](robust_scenario_optimization_spec.md) — two-step robust scenario chain
- [reporting_outputs_spec.md](reporting_outputs_spec.md) — output folder conventions
- [OUTPUTS.md](../../OUTPUTS.md) — generated artifact index
