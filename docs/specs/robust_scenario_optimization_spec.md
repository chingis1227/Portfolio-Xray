# Scenario-Based Robust Optimization Specification

This document owns the contract for `robust_scenario_optimization_v1`.

## Role

Scenario-Based Robust Optimization is an additive candidate builder. It uses report artifacts as inputs and produces candidate weights for analysis. It does not run mandate gates and does not overwrite `portfolio_weights.yml`.

## Inputs

Primary inputs:

- `scenario_library_normalized.json` under **`output_dir_final`** (typically `Main portfolio/`) — shared Main/policy stress calibration, not per-candidate
- `stress_report.json` in the same folder — same shared scope
- active config
- scenario optimizer settings from CLI arguments or the optional `robust_scenario_optimization` YAML block

The candidate factory skips `robust_scenario` with `skipped_dependency` when either Main file is missing. Disclosure: factory `robust_paths_disclosure` and comparison `construction_disclosure.robust_paths` (`kind: robust_scenario_main_prerequisites`). See [operational_runbook.md](../operational_runbook.md) and [candidate_factory_spec.md](candidate_factory_spec.md).

The optimizer builds a scenario coefficient matrix from normalized scenarios and `stress_report.json.asset_factor_betas`. If per-ticker betas are unavailable, the implementation may use the documented portfolio-beta replication fallback and must report beta-load warnings.

## Objectives

Supported objective modes:

- `lower_half_mean`
- `maximin`
- `hybrid_legacy`

The implementation uses SLSQP multi-start optimization and exports CSV/JSON diagnostics.

## Outputs

Primary scripts:

- `run_robust_scenario_optimization.py`
- `run_robust_scenario_portfolio_report.py`

Primary artifacts:

- robust scenario candidate weights
- optimizer summary JSON
- objective and contribution CSVs where implemented
- full robust scenario portfolio report when `run_robust_scenario_portfolio_report.py` is run

## Solver Status Contract

`robust_optimization_v1_summary.json` includes a normalized `solver` block for the selected SLSQP
multi-start result:

- `name: SLSQP`
- `success`: boolean SciPy success flag for the selected result
- `status`: `OK` for a clean selected solve, otherwise `APPROXIMATE`
- `raw_status`, `message`, `iterations`, and `multi_start_count`
- `fallback_used` and `fallback_reason` (`false` / `null` in the current implementation)
- `optimization_quality_status`: `clean_solve` when the selected SLSQP result succeeded,
  otherwise `approximate_solver`

The summary also repeats `solver_success`, `solver_status`, `fallback_used`, `fallback_reason`, and
`optimization_quality_status` at top level for factory readers that consume compact summaries.
These fields disclose solver quality only; they do not change the objective, constraints, weights,
or candidate-only boundary.

When `run_robust_scenario_portfolio_report.py` materializes the `robust scenario portfolio/`
candidate folder and the source robust summary is present beside the weights file, it copies the
solver contract into `baseline_weights_metadata.json.optimizer_run_metadata`
(`robust_scenario_optimizer_run_metadata_v1`). This metadata lets the candidate factory and
candidate comparison expose robust scenario solver quality using the same
`construction_disclosure.optimizer_methodology` and `construction_disclosure.optimizer_quality`
surfaces used by other optimizer candidates.

## Boundaries

Scenario robust optimization creates candidate weights only. It does not change policy weights, mandate gates, stress pass/fail logic, or production release status.
