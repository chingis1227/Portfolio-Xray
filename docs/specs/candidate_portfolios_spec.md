# Candidate Portfolios Specification

This document owns the high-level contract for benchmark and candidate portfolio builders.

## Scope

Candidate portfolios are comparison portfolios. In the portfolio-first workflow, they are generated
only after `analysis_subject` diagnostics exist and are compared against that subject. They run
through the same report pipeline after weights are fixed, but they do not replace the diagnosed
subject and do not reactivate `run_optimization.py` as a default candidate unless a future canonical
spec changes that rule.

## Shared Behavior

Candidate builders use the eligible universe and return panels defined by the current config and data policy. Candidate report folders contain fixed candidate weights, analytics, stress diagnostics, and report artifacts for comparison.

Unless explicitly stated, candidate scripts do not apply ProLiquidity overlays, client mandate release logic, or policy weight release behavior.

Optimizer candidate folders that write `baseline_weights_metadata.json` include a normalized
`optimizer_run_metadata` block (`candidate_optimizer_run_metadata_v1`) for Minimum Variance,
Maximum Diversification, Minimum CVaR, and Robust Mean-Variance families. The block records the
candidate-only role, method id, objective, monthly input window, expected-return usage, covariance
method, eligible universe, resolved constraints/bounds, solver/fallback quality, relevant
parameters, input fingerprints, and output summary fields while preserving the older top-level
metadata fields. Session 08 adds `returns_panel_fingerprint`, `config_fingerprint`, and
`universe_fingerprint`, plus return-panel start/end/row disclosure, to optimizer candidate metadata.
Candidate young-ETF dual covariance estimation receives the wrapper `analysis_end` explicitly. This
is disclosure only and does not change weights, formulas, constraints, mandate gates, or comparison
ranking.

Session 09 adds explicit covariance and Young ETF methodology disclosure to the same optimizer
metadata envelope: `covariance.methodology` (`optimizer_covariance_methodology_v1`),
`covariance.methodology_summary`, and `young_etf_methodology`
(`optimizer_young_etf_methodology_v1`). These fields describe already-used estimator choices,
join policy, shrinkage, PSD repair status, Young ETF mode/buckets/fallback reason, and per-ticker
caps where applicable. They do not recompute covariance or change candidate weights.

Beginning with Optimization Engine Session 06, normalized quality values use `clean_solve`,
`approximate_fallback`, `approximate_solver`, `failed_solver`, `failed`, or `unknown`. Candidate
builders still own only their construction artifacts; factory, comparison, and selection decide how
to surface fallback/failure quality downstream.

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
Implementation: `run_candidate_factory.py` (post-audit Session 11); operator playbooks in
[operational_runbook.md](../operational_runbook.md) §8 (Phase 14 Session 10).

## Comparison Artifact

After individual candidate reports exist (manually or via the factory), the canonical
multi-candidate table is [candidate_comparison.json](../../OUTPUTS.md) under `output_dir_final`,
governed by [candidate_comparison_spec.md](candidate_comparison_spec.md). That contract includes
`analysis_subject`, legacy policy and current rows when materialized, benchmarks, and optimizer
candidates with explicit `unavailable` status when folders are missing.

## Concept candidates not in registry

Non-binding product names in [DIAGNOSTIC_PRODUCT_CONCEPT.md](../DIAGNOSTIC_PRODUCT_CONCEPT.md) §4–5
must not be treated as shipped `candidate_id` values. The implementation registry is
`_REGISTRY_ROWS` in `src/candidate_comparison.py` (18 rows including `analysis_subject`, `policy`,
`current`, and optimizer/benchmark families above). Governance: **DEC-2026-05-20-003**, Phase 14
Session 11 (`RM-981`).

| Concept id | Product reference | Status | Rationale | Existing overlap / workflow |
| --- | --- | --- | --- | --- |
| `concept_custom_constraints` | §4 Custom Constraints | **deferred** | No user-defined constraint builder or factory step in V1. | Feasibility bounds live in [feasibility_constraints_spec.md](feasibility_constraints_spec.md); policy path uses mandate boxes. |
| `concept_tactical_tilt_menu` | §4 Tactical Tilt variant | **declined** | Not a standalone comparison hypothesis; tilts apply after policy release. | [view_after_optimization_spec.md](view_after_optimization_spec.md), `run_view_after_optimization.py`. |
| `concept_max_sharpe` | §5 Max Sharpe | **deferred** | No `run_max_sharpe.py`; Sharpe-max with project bounds needs spec + quant review. | Constrained optimizers (min variance, max diversification, robust MV) remain the shipped menu. |
| `concept_max_return_under_risk` | §5 Max Return under Risk Constraint | **covered_by_existing** | Production max-return path is legacy policy optimization, not factory. | `run_optimization.py` + Main `policy` row (portfolio-first: legacy-only when `analysis_subject` exists). |
| `concept_drawdown_controlled` | §5 Drawdown-controlled | **deferred** | No drawdown-target optimizer candidate script. | Drawdown metrics in snapshots/stress; no mandate-binding DD optimizer in factory. |
| `concept_macro_resilient` | §5 Macro-resilient | **deferred** | No dedicated macro-resilient weight builder. | Macro/regime diagnostics are non-binding overlays per [macro_regime_spec.md](macro_regime_spec.md). |
| `concept_stress_test_optimized_menu` | §5 Stress-test optimized | **covered_by_existing** (partial) | Scenario-robust weights are a candidate, not a second menu id. | `robust_scenario` (`run_robust_scenario_optimization.py`); separate standalone id **deferred**. |
| `concept_tax_turnover_aware` | §5 Tax-aware / turnover-aware | **deferred** | Explicitly “later versions” in product concept. | Turnover appears in trade-off/action artifacts, not candidate construction. |

**Adding a row:** requires accepted spec amendment, builder script, factory profile entry, golden
fixture update, DEC (or supersede DEC-2026-05-20-003 for that id), and roadmap row — not product
concept text alone.

## Detailed Ownership

- Canonical comparison contract: [candidate_comparison_spec.md](candidate_comparison_spec.md)
- Portfolio policy boundaries: [portfolio_construction_policy.md](portfolio_construction_policy.md)
- Weight bounds and feasibility: [feasibility_constraints_spec.md](feasibility_constraints_spec.md)
- Metrics and RC_vol definitions: [metrics_specification.md](metrics_specification.md)
- Robust MV: [robust_mv_spec.md](robust_mv_spec.md)
- Scenario robust optimization: [robust_scenario_optimization_spec.md](robust_scenario_optimization_spec.md)
