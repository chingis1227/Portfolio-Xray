# Candidate Portfolios Specification

This document owns the high-level contract for benchmark and candidate portfolio builders.

## Scope

Candidate portfolios are comparison portfolios. They run through the same report pipeline as the main policy portfolio after weights are fixed, but they do not replace `run_optimization.py` as the main policy optimizer unless a future canonical spec changes that rule.

## Shared Behavior

Candidate builders use the eligible universe and return panels defined by the current config and data policy. Candidate report folders contain fixed candidate weights, analytics, stress diagnostics, and report artifacts for comparison.

Unless explicitly stated, candidate scripts do not apply ProLiquidity overlays, client mandate release logic, or policy weight release behavior.

## Candidate Families

Implemented candidate and benchmark families include:

- Equal Weight by asset: `run_equal_weight.py`
- Equal Weight by asset class then assets: `run_equal_weight_by_asset_class.py`
- Risk Parity: `run_risk_parity.py`
- Risk Budgeting by taxonomy bucket: `run_risk_budget_by_asset_class.py`
- Risk Budgeting by asset: `run_risk_budget_by_asset.py`
- Hierarchical Risk Parity: `run_hierarchical_risk_parity.py`
- Minimum Variance constrained: `run_minimum_variance.py`
- Minimum Variance uncapped long-only: `run_minimum_variance_uncapped.py`
- Minimum Variance advanced controls: `run_minimum_variance_advanced.py`
- Maximum Diversification constrained: `run_maximum_diversification.py`
- Maximum Diversification unconstrained long-only: `run_maximum_diversification_unconstrained.py`
- Minimum CVaR uncapped: `run_minimum_cvar_uncapped.py`
- Minimum CVaR constrained: `run_minimum_cvar_constrained.py`
- Robust Mean-Variance uncapped: `run_robust_mean_variance_uncapped.py`
- Robust Mean-Variance constrained: `run_robust_mean_variance_constrained.py`
- Scenario-Based Robust Optimization: `run_robust_scenario_optimization.py`

## Candidate Portfolio Factory

Orchestration of the per-family builder scripts (default profiles, run summary, handoff to
comparison) is defined in [candidate_factory_spec.md](candidate_factory_spec.md). The factory
invokes the scripts listed in **Candidate Families** above; it does not change their formulas.
Implementation: Session 11 (`run_candidate_factory.py`); spec accepted in post-audit Session 10.

## Comparison Artifact

After individual candidate reports exist (manually or via the factory), the canonical
multi-candidate table is [candidate_comparison.json](../../OUTPUTS.md) under `output_dir_final`,
governed by [candidate_comparison_spec.md](candidate_comparison_spec.md). That contract includes
policy, user current (when materialized), benchmarks, and optimizer candidates with explicit
`unavailable` status when folders are missing.

## Detailed Ownership

- Canonical comparison contract: [candidate_comparison_spec.md](candidate_comparison_spec.md)
- Portfolio policy boundaries: [portfolio_construction_policy.md](portfolio_construction_policy.md)
- Weight bounds and feasibility: [feasibility_constraints_spec.md](feasibility_constraints_spec.md)
- Metrics and RC_vol definitions: [metrics_specification.md](metrics_specification.md)
- Robust MV: [robust_mv_spec.md](robust_mv_spec.md)
- Scenario robust optimization: [robust_scenario_optimization_spec.md](robust_scenario_optimization_spec.md)
