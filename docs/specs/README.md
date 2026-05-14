# Detailed Specifications

This directory contains the detailed source-of-truth documents for module-specific behavior.

Top-level documents stay compact:

- [../../RULES.md](../../RULES.md) maps project principles and source-of-truth ownership.
- [../../AGENTS.md](../../AGENTS.md) defines agent operating rules.
- [../../SPEC.md](../../SPEC.md) defines the current implementation contract and indexes these detailed specs.
- [../../DATA.md](../../DATA.md) maps data sources, structures, pipeline, quality rules, and data documentation sync triggers.
- [../../TESTING.md](../../TESTING.md) defines the quality and verification framework.
- [../../KNOWN_ISSUES.md](../../KNOWN_ISSUES.md) tracks active known issues, model limitations, testing gaps, and technical debt.
- [../../DECISIONS.md](../../DECISIONS.md) records key project decisions, rationale, rejected alternatives, assumptions, and consequences.
- [../../CHANGELOG.md](../../CHANGELOG.md) records concise history of meaningful project changes.

## Spec Index

| Area | Spec |
| --- | --- |
| Metrics, estimators, windows, returns, FX, beta, drawdown, RC_vol, rounding | [metrics_specification.md](metrics_specification.md) |
| Portfolio construction and main optimizer policy | [portfolio_construction_policy.md](portfolio_construction_policy.md) |
| Feasibility and weight constraints | [feasibility_constraints_spec.md](feasibility_constraints_spec.md) |
| Data-layer map, sources, structures, pipeline, quality rules | [../../DATA.md](../../DATA.md) |
| Testing and verification framework | [../../TESTING.md](../../TESTING.md) |
| Known active issues, model limitations, testing gaps, and technical debt | [../../KNOWN_ISSUES.md](../../KNOWN_ISSUES.md) |
| Key project decisions and rationale | [../../DECISIONS.md](../../DECISIONS.md) |
| Concise history of meaningful project changes | [../../CHANGELOG.md](../../CHANGELOG.md) |
| Detailed data policy, NaN handling, young ETFs, return panels | [data_policy_spec.md](data_policy_spec.md) |
| Stress scenarios and stress diagnostics | [stress_testing_spec.md](stress_testing_spec.md) |
| Factor diagnostics and factor-risk outputs | [factor_diagnostics_spec.md](factor_diagnostics_spec.md) |
| Macro regime diagnostics | [macro_regime_spec.md](macro_regime_spec.md) |
| Scenario Library and normalized scenario view | [scenario_library_spec.md](scenario_library_spec.md) |
| Candidate and benchmark portfolios | [candidate_portfolios_spec.md](candidate_portfolios_spec.md) |
| Robust Mean-Variance baselines and lambda calibration | [robust_mv_spec.md](robust_mv_spec.md) |
| Scenario-Based Robust Optimization | [robust_scenario_optimization_spec.md](robust_scenario_optimization_spec.md) |
| Reporting outputs and artifacts | [reporting_outputs_spec.md](reporting_outputs_spec.md) |
| ETF and stock taxonomy | [taxonomy_spec.md](taxonomy_spec.md) |
| ETF taxonomy schema | [etf_universe_spec.md](etf_universe_spec.md) |
| Stock taxonomy schema | [stock_universe_spec.md](stock_universe_spec.md) |
| View After Optimization | [view_after_optimization_spec.md](view_after_optimization_spec.md) |
| Production workflow and release statuses | [production_workflow.md](production_workflow.md) |

When detailed behavior changes, update the owning spec here and keep top-level documents as indexes rather than copying long formulas or module contracts into them.
