# SPEC.md

This file is the compact technical entry point and implementation contract for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It defines what must work in the current product, which workflows are binding, which inputs and outputs are expected, which edge cases must be handled, and where detailed technical rules live. Do not duplicate long formulas or module-specific details here when an owning spec exists.

Update this file when the general implementation contract, workflows, inputs/outputs, behavior rules, edge cases, or product status matrix changes. Use [RULES.md](RULES.md) and [WORKFLOW.md](WORKFLOW.md) to decide which companion docs also need updates. Detailed module behavior belongs in `docs/specs/*.md`.

## Status

`SPEC.md` is the canonical implementation entry point. It has higher authority than product concept documents such as [BUSINESS_VISION.md](BUSINESS_VISION.md), [PRODUCT.md](PRODUCT.md), and [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) when the question is current implementation behavior.

Product concept documents can describe target direction. They do not change formulas, scenarios, optimizer policy, data rules, output contracts, or code behavior until this spec and the relevant detailed specs are updated.

## Implementation Scope

The current implementation is a report-first, CLI/file-driven portfolio analytics system.

The canonical portfolio-first workflow contract is now [Portfolio Review Workflow
Specification](docs/specs/portfolio_review_workflow_spec.md): resolve `analysis_subject`, diagnose
that portfolio first, then generate and compare alternatives. Runtime migration is active under the
[Portfolio-First Transition Plan](docs/exec_plans/2026-05-18_portfolio_first_transition_plan.md);
`run_portfolio_review.py` now provides the portfolio-first orchestration entrypoint. Existing
policy-first entrypoints remain callable as compatibility infrastructure, but they are not the
target default portfolio-first contract.

It supports:

- config validation and profile-derived targets
- market data loading, FX conversion, and return panel construction
- legacy policy optimization and weight release checks
- portfolio metrics, dynamic backtesting, risk contribution diagnostics, and stress diagnostics
- factor, macro/regime, PCA, scenario-library, and robustness diagnostics
- benchmark and candidate portfolio reports
- canonical candidate comparison and V1 decision artifacts: robustness scorecard, Portfolio Health Score, Selection/No-Trade decision, trade-off and model-risk diagnostics, Assumption Sensitivity, Action Plan, Monitoring / What Changed, generated Decision Journal, current-vs-policy status, and candidate factory run summary
- decision package report summary (`decision_package_summary.txt` / `.json`, optional `report.txt` append, decision-package PDF after comparison)
- CSV, JSON, HTML, TXT, and PDF-style report artifacts

Target product areas remain TBD until separately specified and implemented:

- full interactive UI and saved analysis workspaces
- user-maintained journal/workflow layers beyond the generated V1 Decision Journal

## Main Workflows

Portfolio-first review workflow (binding transition contract):

```text
analysis_subject
-> resolved assumptions and validation
-> subject diagnostics / Portfolio X-Ray
-> stress, factor, macro, and scenario diagnostics
-> allowed candidate generation
-> candidate diagnostics
-> comparison: analysis_subject versus candidates
-> keep / rebalance / review / no-trade decision artifacts
-> action plan, monitoring, journal, and report package
```

The subject must be diagnosed before candidate generation or candidate decision artifacts are
presented as the main result. Supported subject types are `current_portfolio`, `model_portfolio`,
and `universe_baseline`; details live in
[portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md).

Legacy policy workflow (compatibility while the transition is implemented):

```text
config.yml
-> validated inputs
-> market data and return panels
-> main policy optimization
-> weight release checks
-> report and diagnostics
-> generated artifacts
```

Primary and compatibility commands:

```bash
python run_portfolio_review.py
python run_optimization.py
python run_report.py
python run_mvp_workflow.py
```

`run_portfolio_review.py` is the portfolio-first orchestration entrypoint: it runs
`run_report.py --materialize-analysis-subject`, then the candidate factory/comparison path.
`run_optimization.py` and `run_mvp_workflow.py` remain legacy/compatibility entrypoints. The
default portfolio-first orchestrator must not call `run_optimization.py` unless a future accepted
spec reactivates the policy engine as an optional candidate generator. See
[docs/operational_runbook.md](docs/operational_runbook.md) for the current runbook.

Benchmark candidate workflow:

```text
config.yml
-> eligible universe and return panels
-> candidate builder
-> fixed candidate weights
-> same report pipeline
-> candidate output folder
```

Scenario robust candidate workflow:

```text
Main report artifacts
-> scenario_library_normalized.json + stress_report.json
-> scenario robust optimizer
-> robust scenario candidate weights
-> robust scenario portfolio report
```

## Detailed Spec Index

| Area | Source |
| --- | --- |
| High-level project principles and source-of-truth ownership | [RULES.md](RULES.md) |
| Agent operating rules | [AGENTS.md](AGENTS.md) |
| Task workflow from request to implementation, verification, docs sync, project memory, and commit | [WORKFLOW.md](WORKFLOW.md) |
| Generated outputs, report artifacts, output folders, formats, and generated-vs-source boundaries | [OUTPUTS.md](OUTPUTS.md) |
| Shared project terminology and short definitions | [GLOSSARY.md](GLOSSARY.md) |
| Data-layer map: sources, structures, pipeline, quality rules, and data-doc sync triggers | [DATA.md](DATA.md) |
| Testing and verification framework | [TESTING.md](TESTING.md) |
| Known active issues, model limitations, testing gaps, and technical debt | [KNOWN_ISSUES.md](KNOWN_ISSUES.md) |
| Key decisions, rationale, rejected alternatives, assumptions, and consequences | [DECISIONS.md](DECISIONS.md) |
| Concise history of meaningful project changes | [CHANGELOG.md](CHANGELOG.md) |
| Detailed spec index | [docs/specs/README.md](docs/specs/README.md) |
| Portfolio-first review workflow, `analysis_subject`, and legacy policy boundary | [docs/specs/portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md) |
| Portfolio X-Ray diagnostics and `portfolio_xray.json` contract | [docs/specs/portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) |
| Analysis setup, input modes, current weights, mandate inputs, and calculation assumptions | [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md) |
| Metrics, estimators, returns, FX, windows, covariance, beta, RC_vol, drawdown, rounding | [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md) |
| Portfolio construction, optimizer behavior, ProLiquidity, mandate gate, policy optimizer boundaries | [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md) |
| Feasibility and weight constraints | [docs/specs/feasibility_constraints_spec.md](docs/specs/feasibility_constraints_spec.md) |
| Data policy, NaN handling, young ETFs, return panels, backtest handling | [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md) |
| Stress scenarios and stress diagnostics | [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md) |
| Factor diagnostics and factor-risk outputs | [docs/specs/factor_diagnostics_spec.md](docs/specs/factor_diagnostics_spec.md) |
| Macro regime diagnostics | [docs/specs/macro_regime_spec.md](docs/specs/macro_regime_spec.md) |
| Scenario Library and normalized scenario view | [docs/specs/scenario_library_spec.md](docs/specs/scenario_library_spec.md) |
| Candidate and benchmark portfolios | [docs/specs/candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md) |
| Canonical candidate comparison artifact | [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md) |
| Robustness Scorecard (diagnostic; `src/robustness_scorecard.py`) | [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md) |
| Portfolio Health Score | [docs/specs/portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md), [src/portfolio_health_score.py](src/portfolio_health_score.py) |
| Selection Engine and No-Trade Recommendation | [docs/specs/selection_engine_spec.md](docs/specs/selection_engine_spec.md), [src/selection_engine.py](src/selection_engine.py) |
| Current-vs-policy workflow | [docs/specs/current_vs_policy_workflow_spec.md](docs/specs/current_vs_policy_workflow_spec.md) |
| Action Engine and Rebalancing Advisor | [docs/specs/action_engine_spec.md](docs/specs/action_engine_spec.md), [src/action_engine.py](src/action_engine.py) |
| Robust Mean-Variance baselines and lambda calibration | [docs/specs/robust_mv_spec.md](docs/specs/robust_mv_spec.md) |
| Scenario-Based Robust Optimization | [docs/specs/robust_scenario_optimization_spec.md](docs/specs/robust_scenario_optimization_spec.md) |
| Reporting outputs and artifacts | [docs/specs/reporting_outputs_spec.md](docs/specs/reporting_outputs_spec.md) |
| ETF and stock taxonomy | [docs/specs/taxonomy_spec.md](docs/specs/taxonomy_spec.md) |
| View After Optimization tactical tilt protocol | [docs/specs/view_after_optimization_spec.md](docs/specs/view_after_optimization_spec.md) |
| Production workflow and release statuses | [docs/specs/production_workflow.md](docs/specs/production_workflow.md) |
| Architecture and module boundaries | [ARCHITECTURE.md](ARCHITECTURE.md) |

## Inputs

Primary source inputs:

- `config.yml`
- `config.yml.example`
- `config/client_profiles.yml`
- `assets.yml`
- `config/etf_universe.yml`
- `config/stock_universe.yml`
- optional historical stress proxy map and external data source settings

The data-layer map is [DATA.md](DATA.md). Keep it aligned when data sources, expected structures, data pipeline, NaN handling, FX logic, benchmarks, risk-free inputs, factor/macro inputs, config fields, or data validation rules change.

Primary runtime inputs:

- `analysis_subject` for the portfolio-first review workflow: the current, model, or
  universe-baseline portfolio diagnosed before candidates; explicit config is resolved in
  `analysis_setup.analysis_subject`
- resolved `analysis_setup` for the input and assumptions layer
- ticker universe
- investor currency
- benchmark and local benchmark settings
- cash proxy and risk-free source
- return frequency
- optimization targets and constraints
- output directories and cache settings
- optional profile name

Generated weights are not normal user input. The legacy policy workflow writes
`portfolio_weights.yml` and `run_result.json` when release is allowed, but generated policy weights
are not the default `analysis_subject` in the portfolio-first workflow.

`analysis_setup` is the resolved runtime contract for portfolio input, mandate, assumptions, and validation metadata. `input_assumptions` is an exported/reporting view of that contract, not a separate business-logic source.

## Outputs

The root output map is [OUTPUTS.md](OUTPUTS.md).

Primary outputs include:

- `portfolio_weights.yml`
- `run_result.json`
- `run_metadata.json`
- `stress_report.json`
- `portfolio_xray.json`
- `candidate_comparison.json`
- `robustness_scorecard.json`
- `portfolio_health_score.json`
- `selection_decision.json`
- `tradeoff_explanation.json` and `model_risk_diagnostics.json` (via [src/tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py))
- `assumption_sensitivity.json` (via [src/assumption_sensitivity.py](src/assumption_sensitivity.py))
- `pareto_dominance.json` (via [src/pareto_dominance.py](src/pareto_dominance.py))
- `action_plan.json`
- `monitoring_diff.json`
- `decision_journal.json`
- metrics and diagnostics under `results_csv/`
- scenario library JSON/CSV artifacts where available
- commentary text artifacts
- generated HTML and PDF-style report artifacts
- candidate portfolio folders for benchmark variants

Generated outputs are not source files unless a task explicitly targets generated artifacts.

Portfolio-first runtime can materialize the diagnosed `analysis_subject` before candidate generation
with:

```bash
python run_report.py --materialize-analysis-subject
```

The canonical subject diagnostic folder is `{output_dir_final}/analysis_subject/`; detailed output
ownership remains in [OUTPUTS.md](OUTPUTS.md) and the portfolio review workflow spec.

`portfolio_xray.json` is generated by the report path as a diagnostic-only X-Ray summary. It consumes existing report pipeline outputs and in-memory diagnostics; it does not optimize, change weights, change mandate gates, change stress pass/fail status, or select portfolios. Its detailed section contract is [docs/specs/portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md).

`run_result.json` and `run_metadata.json` include `analysis_setup` plus projected `input_assumptions`.

## Binding Behavior Rules

- Use adjusted close prices and convert FX before returns.
- Compute `analysis_end` as the last completed effective period before today according to the metrics spec.
- Align series using the rules in the relevant metric, beta, covariance, correlation, RC_vol, stress, or data spec.
- Preserve full precision internally and round only at final export/report stage.
- Do not invent formulas, scenarios, estimators, constraints, or statuses when a canonical spec exists.
- In the portfolio-first workflow, diagnose `analysis_subject` before generating candidates or
  presenting comparison/decision artifacts as the main review outcome.
- The old policy optimizer is legacy/compatibility infrastructure in the portfolio-first transition;
  it is not the default starting portfolio and is not a default candidate unless a future accepted
  spec changes that boundary.
- Final policy weights come from optimization plus approved post-processing only.
- View After Optimization is the only permitted manual post-optimization tilt protocol.
- Taxonomy validates and annotates in V1; it does not select tickers or change weights.
- Diagnostic blocks do not affect optimizer inputs, mandate gates, stress pass/fail, or weight release unless a canonical spec says so.
- Scenario stress is diagnostic; mandate maximum drawdown can block weight release.
- Default report backtest mode is `dynamic_nan_safe`.

## Edge Cases And Required Handling

The implementation must fail clearly or degrade explicitly for:

- invalid config fields or unsupported config values
- missing cash proxy or unsupported risk-free assumptions
- investor-currency risk-free gaps where no explicit source is provided
- insufficient return history for required windows
- missing or partial market data
- young or short-history ETFs
- NaN return panels and dynamic backtest gaps
- infeasible weight constraints
- missing factor, macro, scenario, or taxonomy inputs
- candidate portfolios whose fixed weights cannot be reported consistently

When a diagnostic degrades because inputs are missing, the output must expose the relevant warning, quality flag, or metadata rather than silently implying full confidence.

## Product Status Matrix

| Area | Current status |
| --- | --- |
| Portfolio-first review workflow (`analysis_subject` first) | Canonical spec accepted; runtime transition active |
| Main CLI optimization and report pipeline | Implemented |
| Input and Assumptions Layer | Implemented CLI/file-driven V1 |
| Config validation and profile-derived targets | Implemented |
| Portfolio metrics, backtests, risk contribution | Implemented |
| Stress testing and stress commentary | Implemented diagnostic/reporting layer |
| Factor diagnostics, PCA, macro/regime diagnostics, scenario analytics | Implemented diagnostic-only layer |
| Scenario Library and normalized scenario view | Implemented input-standardization/diagnostic layer |
| Benchmark and candidate portfolio builders | Implemented comparison layer |
| Robust Mean-Variance and Scenario-Based Robust Optimization | Implemented benchmark/candidate layer |
| Canonical candidate comparison | Implemented (`candidate_comparison.json` via [src/candidate_comparison.py](src/candidate_comparison.py)); includes `analysis_subject` baseline row when materialized |
| Robustness Scorecard | Implemented diagnostic artifact (`robustness_scorecard.json` via [src/robustness_scorecard.py](src/robustness_scorecard.py)) |
| Portfolio Health Score | Implemented diagnostic artifact (`portfolio_health_score.json` via [src/portfolio_health_score.py](src/portfolio_health_score.py)) |
| ETF and stock taxonomy | Implemented annotation-only V1 |
| Generated CSV/JSON/HTML/TXT/PDF-style reports | Implemented |
| Full interactive UI | Target/TBD |
| Formal Selection Engine and No-Trade | Implemented (`selection_decision.json` via [src/selection_engine.py](src/selection_engine.py)); portfolio-first baseline is `analysis_subject`, with legacy fallback to `current` |
| Trade-off Explanation and Model Risk Diagnostics | Implemented ([src/tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py); [tradeoff_and_model_risk_spec.md](docs/specs/tradeoff_and_model_risk_spec.md)) |
| Assumption Sensitivity | Implemented ([src/assumption_sensitivity.py](src/assumption_sensitivity.py); [assumption_sensitivity_spec.md](docs/specs/assumption_sensitivity_spec.md)) |
| Pareto / Dominance Check | Implemented ([src/pareto_dominance.py](src/pareto_dominance.py); [pareto_dominance_spec.md](docs/specs/pareto_dominance_spec.md)) |
| Regret Analysis | Implemented ([regret_analysis_spec.md](docs/specs/regret_analysis_spec.md); `src/regret_analysis.py`, `regret_analysis.json` / `.txt`) |
| Action Engine and Rebalancing Advisor | Implemented (`action_plan.json` via [src/action_engine.py](src/action_engine.py)) |
| Monitoring / What Changed | Implemented (V1) - [monitoring_spec.md](docs/specs/monitoring_spec.md), `src/monitoring.py` |
| Decision Journal | Implemented (V1) - [decision_journal_spec.md](docs/specs/decision_journal_spec.md), `src/decision_journal.py` |

## Implementation Contract

Configuration must load and validate before data, diagnostics, candidate generation, or legacy
optimization run. Data and return panels must be built consistently with the data and metrics specs.
The portfolio-first path must resolve and diagnose `analysis_subject` before alternatives are
generated or compared. The legacy policy optimizer must either produce releasable weights or refuse
release with a clear status when that compatibility path is explicitly run. The report pipeline must
produce diagnostics and artifacts from fixed weights. Candidate builders must create comparable
alternatives without replacing the portfolio-first subject or legacy policy optimizer boundaries.
Taxonomy diagnostics must annotate and validate without changing optimizer membership in V1.

Any change to current behavior must update the owning detailed spec, this implementation contract when the general contract changes, and user-facing documentation when workflows or outputs change.
