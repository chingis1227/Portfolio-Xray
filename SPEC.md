# SPEC.md

This file is the compact technical entry point and implementation contract for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It defines what must work in the current product, which workflows are binding, which inputs and outputs are expected, which edge cases must be handled, and where detailed technical rules live. Do not duplicate long formulas or module-specific details here when an owning spec exists.

Update this file when the general implementation contract, workflows, inputs/outputs, behavior rules, edge cases, or product status matrix changes. Update [AGENTS.md](AGENTS.md) for agent operating rules. Update [TESTING.md](TESTING.md) for verification strategy and required checks. Update `docs/specs/*.md` for detailed behavior of a specific module.

## Status

`SPEC.md` is the canonical implementation entry point. It has higher authority than product concept documents such as [BUSINESS_VISION.md](BUSINESS_VISION.md), [PRODUCT.md](PRODUCT.md), and [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) when the question is current implementation behavior.

Product concept documents can describe target direction. They do not change formulas, scenarios, optimizer policy, data rules, output contracts, or code behavior until this spec and the relevant detailed specs are updated.

## Implementation Scope

The current implementation is a report-first, CLI/file-driven portfolio analytics system.

It supports:

- config validation and profile-derived targets
- market data loading, FX conversion, and return panel construction
- main policy optimization and weight release checks
- portfolio metrics, dynamic backtesting, risk contribution diagnostics, and stress diagnostics
- factor, macro/regime, PCA, scenario-library, and robustness diagnostics
- benchmark and candidate portfolio reports
- CSV, JSON, HTML, TXT, and PDF-style report artifacts

Target product areas remain TBD until separately specified and implemented:

- full interactive UI
- saved analysis workspaces
- formal Selection Engine
- formal Portfolio Health Score
- full Monitoring
- Decision Journal

## Main Workflows

Main policy workflow:

```text
config.yml
-> validated inputs
-> market data and return panels
-> main policy optimization
-> weight release checks
-> report and diagnostics
-> generated artifacts
```

Main commands:

```bash
python run_optimization.py
python run_report.py
```

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
| Data-layer map: sources, structures, pipeline, quality rules, and data-doc sync triggers | [DATA.md](DATA.md) |
| Testing and verification framework | [TESTING.md](TESTING.md) |
| Detailed spec index | [docs/specs/README.md](docs/specs/README.md) |
| Metrics, estimators, returns, FX, windows, covariance, beta, RC_vol, drawdown, rounding | [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md) |
| Portfolio construction, optimizer behavior, ProLiquidity, mandate gate, policy optimizer boundaries | [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md) |
| Feasibility and weight constraints | [docs/specs/feasibility_constraints_spec.md](docs/specs/feasibility_constraints_spec.md) |
| Data policy, NaN handling, young ETFs, return panels, backtest handling | [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md) |
| Stress scenarios and stress diagnostics | [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md) |
| Factor diagnostics and factor-risk outputs | [docs/specs/factor_diagnostics_spec.md](docs/specs/factor_diagnostics_spec.md) |
| Macro regime diagnostics | [docs/specs/macro_regime_spec.md](docs/specs/macro_regime_spec.md) |
| Scenario Library and normalized scenario view | [docs/specs/scenario_library_spec.md](docs/specs/scenario_library_spec.md) |
| Candidate and benchmark portfolios | [docs/specs/candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md) |
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

- ticker universe
- investor currency
- benchmark and local benchmark settings
- cash proxy and risk-free source
- return frequency
- optimization targets and constraints
- output directories and cache settings
- optional profile name

Generated weights are not normal user input. The main policy workflow writes `portfolio_weights.yml` and `run_result.json` when release is allowed.

## Outputs

Primary outputs include:

- `portfolio_weights.yml`
- `run_result.json`
- `run_metadata.json`
- `stress_report.json`
- metrics and diagnostics under `results_csv/`
- scenario library JSON/CSV artifacts where available
- commentary text artifacts
- generated HTML and PDF-style report artifacts
- candidate portfolio folders for benchmark variants

Generated outputs are not source files unless a task explicitly targets generated artifacts.

## Binding Behavior Rules

- Use adjusted close prices and convert FX before returns.
- Compute `analysis_end` as the last completed effective period before today according to the metrics spec.
- Align series using the rules in the relevant metric, beta, covariance, correlation, RC_vol, stress, or data spec.
- Preserve full precision internally and round only at final export/report stage.
- Do not invent formulas, scenarios, estimators, constraints, or statuses when a canonical spec exists.
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
| Main CLI optimization and report pipeline | Implemented |
| Config validation and profile-derived targets | Implemented |
| Portfolio metrics, backtests, risk contribution | Implemented |
| Stress testing and stress commentary | Implemented diagnostic/reporting layer |
| Factor diagnostics, PCA, macro/regime diagnostics, scenario analytics | Implemented diagnostic-only layer |
| Scenario Library and normalized scenario view | Implemented input-standardization/diagnostic layer |
| Benchmark and candidate portfolio builders | Implemented comparison layer |
| Robust Mean-Variance and Scenario-Based Robust Optimization | Implemented benchmark/candidate layer |
| ETF and stock taxonomy | Implemented annotation-only V1 |
| Generated CSV/JSON/HTML/TXT/PDF-style reports | Implemented |
| Full interactive UI | Target/TBD |
| Formal Selection Engine, Portfolio Health Score, Monitoring, Decision Journal | Target/TBD |

## Implementation Contract

Configuration must load and validate before data and optimization run. Data and return panels must be built consistently with the data and metrics specs. The main policy optimizer must either produce releasable weights or refuse release with a clear status. The report pipeline must produce diagnostics and artifacts from fixed weights. Candidate builders must create comparable alternatives without replacing the main policy optimizer. Taxonomy diagnostics must annotate and validate without changing optimizer membership in V1.

Any change to current behavior must update the owning detailed spec, this implementation contract when the general contract changes, and user-facing documentation when workflows or outputs change.
