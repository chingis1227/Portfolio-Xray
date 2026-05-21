# Candidate Portfolio Factory Specification

This document owns the **Candidate Portfolio Factory** orchestration contract: how the project runs the existing per-candidate builder scripts in a controlled order, records per-candidate outcomes, and hands off to the canonical comparison pipeline.

It does not own metric formulas, optimizer mathematics, stress scenarios, comparison field definitions, or selection logic. Those remain in [metrics_specification.md](metrics_specification.md), [candidate_portfolios_spec.md](candidate_portfolios_spec.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [portfolio_construction_policy.md](portfolio_construction_policy.md), and [selection_engine_spec.md](selection_engine_spec.md).

Implementation: **`run_candidate_factory.py`** and **`src/candidate_factory.py`** (post-audit Session 11, 2026-05-17). This spec is the contract.

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

| Role | Entry | Factory includes? |
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
3. **Default profile `default_v1`:** all **sixteen** script-backed registry rows (every row except `policy` and `current`).
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
| 0 Subject | `python run_portfolio_review.py` | Materialize `analysis_subject`, build candidates, and compare through the orchestrator |
| 1 Factory only (advanced) | `python run_candidate_factory.py --profile default_v1` | Build or refresh candidate artifact folders after subject diagnostics exist |
| 2 Compare only (advanced) | `python run_compare_variants.py` | Rebuild `candidate_comparison.json` + decision package from existing artifacts |

Factory may implement `--then-compare` to run step 2 automatically after step 1.

### A-legacy. Policy compatibility run

Use only when the intended baseline is generated legacy policy weights.

| Step | Command | Purpose |
| --- | --- | --- |
| 0 Policy | `python run_optimization.py` then `python run_report.py` | Legacy policy weights and Main diagnostics |
| 0b Current (optional) | `python run_report.py --materialize-current` | Current sidecar for No-Trade versus current |
| 1 Factory | `python run_candidate_factory.py --profile default_v1` | Build or refresh candidate artifact folders |
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
| `default_v1` | All sixteen script-backed IDs (union of rows above) | Standard product comparison arena |
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

**Ordering within `default_v1`:** run `core_benchmarks` first, then `risk_budgets`, then `classic_optimizers`, then `robust_suite` (robust last because of policy-report dependencies and runtime). Session 11 may parallelize only if a future decision adds isolation guarantees; V1 is **sequential**.

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
| **core-run** | `python run_portfolio_review.py` (default `--mode core`) | `core_v1` | Benchmarks + risk budgets (6 script-backed candidates) + compare + decision package |
| **full-run** | `python run_portfolio_review.py --mode full` | `default_v1` | Full menu including classic optimizers and robust suite (16 candidates) |

`--candidate-profile` overrides `--mode` when an explicit profile is required. Partial-menu disclosure
is emitted in `candidate_comparison.json` → `candidate_menu` and in the decision-package summary.

**Resumable factory (RM-979 / RM-921):** `{output_dir_final}/candidate_factory_manifest.json`
records `run_checksum` (profile, candidate menu, `analysis_end`, `config_fingerprint`) and
per-step `completed_steps`. `python run_candidate_factory.py --resume` skips `succeeded` and
fresh `skipped_existing` steps when the checksum matches; failed steps are retried. Manifest is
updated after each step so an interrupted run can resume without redoing succeeded builders.
Optional parallel builders remain future scope. Universe-file hashing and weight-source keys
remain future scope.

## Canonical Factory Run Artifacts

| Field | Value |
| --- | --- |
| File name | `candidate_factory_run.json` |
| Location | `{output_dir_final}/candidate_factory_run.json` |
| Companion (optional) | `{output_dir_final}/candidate_factory_run.txt` |
| Resume manifest | `{output_dir_final}/candidate_factory_manifest.json` (`candidate_factory_manifest_v1`) |
| Schema version | `candidate_factory_run_v1` |

### Top-level JSON contract (`candidate_factory_run_v1`)

```json
{
  "schema_version": "candidate_factory_run_v1",
  "diagnostic_only": true,
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
    "then_compare": false
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
| `entry_commands` | array of strings | Commands attempted (repr for audit) |
| `exit_code` | int or null | Last command exit code when applicable |
| `duration_seconds` | number | Wall time for the step |
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

## Integration with Comparison and Decision Package

After factory completes (or after manual builders):

1. `run_compare_variants.py` calls `write_candidate_comparison_outputs`.
2. Comparison behavior is **unchanged** — still read-only; factory only increases `available` row count.
3. Downstream artifacts (robustness, health, selection, action, monitoring, journal, decision package summary) emit when comparison runs; factory does not write them directly.

If `--then-compare` is set and comparison fails, factory run summary should add warning `comparison_failed` with nested error message; factory step statuses remain authoritative for builders.

## CLI Contract

Entry point at repository root:

```bash
python run_candidate_factory.py [--profile PROFILE] [--candidates ID,ID,...]
  [--skip-existing | --force] [--fail-fast] [--resume] [--then-compare] [--config PATH]
```

| Flag | Default | Behavior |
| --- | --- | --- |
| `--profile` | `default_v1` | Select factory profile |
| `--candidates` | (none) | Overrides profile with explicit list |
| `--skip-existing` | on | Skip when `snapshot_10y.json` exists |
| `--force` | off | Rerun even when snapshot exists |
| `--fail-fast` | off | Stop factory on first failed step |
| `--resume` | off | Skip prior `succeeded` / fresh `skipped_existing` steps when manifest checksum matches |
| `--then-compare` | off | Run `run_compare_variants.py` after factory |
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
