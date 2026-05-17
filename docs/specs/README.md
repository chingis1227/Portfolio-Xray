# Detailed Specifications

This directory contains the detailed source-of-truth documents for module-specific behavior.

Top-level documents stay compact:

- [../../RULES.md](../../RULES.md) maps project principles and source-of-truth ownership.
- [../../AGENTS.md](../../AGENTS.md) defines agent operating rules.
- [../../WORKFLOW.md](../../WORKFLOW.md) defines the task workflow from request to implementation, verification, documentation sync, project memory, and commit.
- [../../SPEC.md](../../SPEC.md) defines the current implementation contract and indexes these detailed specs.
- [../../OUTPUTS.md](../../OUTPUTS.md) maps generated output folders, artifacts, formats, report packaging, and generated-vs-source boundaries.
- [../../GLOSSARY.md](../../GLOSSARY.md) defines shared project terminology and short definitions.
- [../../DATA.md](../../DATA.md) maps data sources, structures, pipeline, quality rules, and data documentation sync triggers.
- [../../TESTING.md](../../TESTING.md) defines the quality and verification framework.
- [../../KNOWN_ISSUES.md](../../KNOWN_ISSUES.md) tracks active known issues, model limitations, testing gaps, and technical debt.
- [../../DECISIONS.md](../../DECISIONS.md) records key project decisions, rationale, rejected alternatives, assumptions, and consequences.
- [../../CHANGELOG.md](../../CHANGELOG.md) records concise history of meaningful project changes.

## Spec Index

| Area | Spec |
| --- | --- |
| Metrics, estimators, windows, returns, FX, beta, drawdown, RC_vol, rounding | [metrics_specification.md](metrics_specification.md) |
| Analysis setup, input modes, current weights, mandate inputs, and calculation assumptions | [input_assumptions_spec.md](input_assumptions_spec.md) |
| Portfolio construction and main optimizer policy | [portfolio_construction_policy.md](portfolio_construction_policy.md) |
| Feasibility and weight constraints | [feasibility_constraints_spec.md](feasibility_constraints_spec.md) |
| Task workflow from request to implementation, verification, docs sync, project memory, and commit | [../../WORKFLOW.md](../../WORKFLOW.md) |
| Generated output folders, artifacts, formats, and generated-vs-source boundaries | [../../OUTPUTS.md](../../OUTPUTS.md) |
| Shared project terminology and short definitions | [../../GLOSSARY.md](../../GLOSSARY.md) |
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
| Candidate portfolio factory orchestration | [candidate_factory_spec.md](candidate_factory_spec.md) |
| Canonical multi-candidate comparison artifact | [candidate_comparison_spec.md](candidate_comparison_spec.md) |
| Robustness Scorecard (diagnostic resilience scoring) | [robustness_scorecard_spec.md](robustness_scorecard_spec.md) |
| Portfolio Health Score (diagnostic holistic quality scoring) | [portfolio_health_score_spec.md](portfolio_health_score_spec.md) |
| Selection Engine and No-Trade Recommendation (formal decision contract) | [selection_engine_spec.md](selection_engine_spec.md) |
| Trade-off Explanation and Model Risk Diagnostics | [tradeoff_and_model_risk_spec.md](tradeoff_and_model_risk_spec.md) |
| Current-vs-policy workflow and No-Trade actionability | [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) |
| Action Engine and Rebalancing Advisor (implementation plan) | [action_engine_spec.md](action_engine_spec.md) |
| Monitoring snapshots and What Changed diff | [monitoring_spec.md](monitoring_spec.md) |
| Decision Journal (generated decision record) | [decision_journal_spec.md](decision_journal_spec.md) |
| Robust Mean-Variance baselines and lambda calibration | [robust_mv_spec.md](robust_mv_spec.md) |
| Scenario-Based Robust Optimization | [robust_scenario_optimization_spec.md](robust_scenario_optimization_spec.md) |
| Reporting outputs and artifacts | [reporting_outputs_spec.md](reporting_outputs_spec.md) |
| Decision package report/PDF summary | [decision_package_reporting_spec.md](decision_package_reporting_spec.md) |
| ETF and stock taxonomy | [taxonomy_spec.md](taxonomy_spec.md) |
| ETF taxonomy schema | [etf_universe_spec.md](etf_universe_spec.md) |
| Stock taxonomy schema | [stock_universe_spec.md](stock_universe_spec.md) |
| View After Optimization | [view_after_optimization_spec.md](view_after_optimization_spec.md) |
| Production workflow and release statuses | [production_workflow.md](production_workflow.md) |

When detailed behavior changes, update the owning spec here and keep top-level documents as indexes rather than copying long formulas or module contracts into them.
