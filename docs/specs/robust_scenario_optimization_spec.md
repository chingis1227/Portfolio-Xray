# Scenario-Based Robust Optimization Specification

This document owns the contract for `robust_scenario_optimization_v1`.

## Role

Scenario-Based Robust Optimization is an additive candidate builder. It uses report artifacts as inputs and produces candidate weights for analysis. It does not run mandate gates and does not overwrite `portfolio_weights.yml`.

## Inputs

Primary inputs:

- `scenario_library_normalized.json`
- `stress_report.json`
- active config
- scenario optimizer settings from CLI arguments or the optional `robust_scenario_optimization` YAML block

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

## Boundaries

Scenario robust optimization creates candidate weights only. It does not change policy weights, mandate gates, stress pass/fail logic, or production release status.
