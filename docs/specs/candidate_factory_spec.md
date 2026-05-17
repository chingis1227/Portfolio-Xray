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

- replace `run_optimization.py` as the production policy path;
- write or overwrite `portfolio_weights.yml` except through the existing policy optimizer entry point (policy is outside the factory batch);
- merge candidate formulas into one optimizer;
- provide product UI/workspace (deferred).

## Problem Statement (V1)

Today, `run_compare_variants.py` / `write_candidate_comparison_outputs` correctly marks registry rows `unavailable` when artifact folders are missing (PSA-008). Comparison quality therefore depends on **which scripts the operator ran manually** before comparison. The factory closes that gap by making the **intended candidate set and run order** explicit and auditable.

## Product Boundary

| Role | Entry | Factory includes? |
| --- | --- | --- |
| **Production policy** | `run_optimization.py` → `run_report.py` on Main | **No** — run separately before or in parallel; factory documents this as **Step 0** in full workflows only |
| **User current (sidecar)** | `run_report.py --materialize-current` | **Optional** — see [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) |
| **Benchmark / optimizer candidates** | Per-family `run_*.py` scripts | **Yes** — factory core |
| **Comparison + decision package** | `run_compare_variants.py` | **Optional tail** (`--then-compare` in Session 11) |

**Main = production policy.** Robust MV and robust scenario paths are **candidate/benchmark inputs** only unless a future accepted decision changes release policy ([DEC-2026-05-17-007](../../DECISIONS.md)).

## V1 User Decisions (2026-05-17, Session 10)

Recorded defaults when the post-audit plan continues without overrides:

1. **Orchestrate before compare:** V1 adopts a factory layer; comparison remains read-only aggregation.
2. **No formula duplication:** each `candidate_id` maps to one existing entry script (or a documented two-step chain); Session 11 must subprocess or import those scripts, not copy optimization code.
3. **Default profile `default_v1`:** all **sixteen** script-backed registry rows (every row except `policy` and `current`).
4. **Skip-existing default:** when `{artifact_root}/snapshot_10y.json` exists, skip rerunning that candidate unless `--force` is set (Session 11).
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

### A. Full decision-support run (recommended)

| Step | Command | Purpose |
| --- | --- | --- |
| 0 Policy | `python run_optimization.py` then `python run_report.py` | Policy weights and Main diagnostics |
| 0b Current (optional) | `python run_report.py --materialize-current` | Current sidecar for No-Trade versus current |
| 1 Factory | `python run_candidate_factory.py --profile default_v1` | Build or refresh candidate artifact folders |
| 2 Compare | `python run_compare_variants.py` | `candidate_comparison.json` + decision package |

Factory may implement `--then-compare` to run step 2 automatically after step 1.

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

**Policy row (`policy`):** `run_optimization.py` + `run_report.py` on Main — documented in workflow A step 0, not invoked by factory profiles.

**Current row (`current`):** `run_report.py --materialize-current` — optional step 0b.

When `_REGISTRY_ROWS` changes in code, update this table and [candidate_portfolios_spec.md](candidate_portfolios_spec.md) in the same change set.

## Per-Step Execution Rules

For each `candidate_id` in the active profile:

1. Resolve `artifact_root` under project root.
2. If `--skip-existing` (default) and `{artifact_root}/snapshot_10y.json` exists and `--force` is not set → status `skipped_existing`.
3. If prerequisites fail (e.g. robust scenario missing scenario library) → status `skipped_dependency` with reason code; do not throw away the whole run unless `--fail-fast` (Session 11 optional flag).
4. Otherwise invoke entry script(s) in order with project Python, same `config.yml` as policy run.
5. On subprocess non-zero exit → status `failed` with `exit_code` and stderr tail (truncated); continue unless `--fail-fast`.
6. On success → status `succeeded`; verify minimum comparison inputs: `snapshot_10y.json` present (else `failed` with `missing_snapshot_after_build`).

**Robust scenario chain:** factory runs optimization script first; on success runs portfolio report script. One factory step row may represent the chain; both commands appear in `entry_commands` array in the run summary.

**Ordering within `default_v1`:** run `core_benchmarks` first, then `risk_budgets`, then `classic_optimizers`, then `robust_suite` (robust last because of policy-report dependencies and runtime). Session 11 may parallelize only if a future decision adds isolation guarantees; V1 is **sequential**.

## Canonical Factory Run Artifacts

| Field | Value |
| --- | --- |
| File name | `candidate_factory_run.json` |
| Location | `{output_dir_final}/candidate_factory_run.json` |
| Companion (optional) | `{output_dir_final}/candidate_factory_run.txt` |
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
  "options": {
    "skip_existing": true,
    "force": false,
    "fail_fast": false,
    "then_compare": false
  },
  "steps": [],
  "summary": {
    "total": 16,
    "succeeded": 0,
    "failed": 0,
    "skipped_existing": 0,
    "skipped_dependency": 0
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

### Reason codes (V1)

| Code | Meaning |
| --- | --- |
| `skipped_existing` | `snapshot_10y.json` already present and skip-existing active |
| `skipped_dependency` | Prerequisite artifacts missing (e.g. scenario library) |
| `missing_snapshot_after_build` | Script exited 0 but comparison minimum files absent |
| `subprocess_failed` | Builder returned non-zero exit |
| `subprocess_timeout` | Reserved; optional timeout in Session 11 |
| `unknown_candidate_id` | ID not in registry (explicit list mode) |

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
  [--skip-existing | --force] [--fail-fast] [--then-compare] [--config PATH]
```

| Flag | Default | Behavior |
| --- | --- | --- |
| `--profile` | `default_v1` | Select factory profile |
| `--candidates` | (none) | Overrides profile with explicit list |
| `--skip-existing` | on | Skip when `snapshot_10y.json` exists |
| `--force` | off | Rerun even when snapshot exists |
| `--fail-fast` | off | Stop factory on first failed step |
| `--then-compare` | off | Run `run_compare_variants.py` after factory |
| `--config` | `config.yml` | Config path passed to builders |

Exit codes (Session 11):

- `0` — all attempted steps succeeded or were skipped intentionally; no fail-fast abort
- `1` — one or more `failed` steps, or fail-fast abort
- `2` — configuration or registry validation error before any builder runs

## Verification (Session 10 vs 11)

| Session | Verification |
| --- | --- |
| **10 (this spec)** | `python scripts/verify_docs.py`; registry table matches `_REGISTRY_ROWS` |
| **11 (implementation)** | New focused factory tests under `tests/`; smoke: factory + compare increases `available` count on a fixture project |

## Related Documents

- [candidate_portfolios_spec.md](candidate_portfolios_spec.md) — builder families and shared behavior
- [candidate_comparison_spec.md](candidate_comparison_spec.md) — canonical comparison contract
- [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) — policy/current outside factory profiles
- [robust_scenario_optimization_spec.md](robust_scenario_optimization_spec.md) — two-step robust scenario chain
- [reporting_outputs_spec.md](reporting_outputs_spec.md) — output folder conventions
- [OUTPUTS.md](../../OUTPUTS.md) — generated artifact index
