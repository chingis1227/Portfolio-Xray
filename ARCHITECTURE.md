# Architecture

## Status

This document describes the current system architecture and the target product architecture boundaries for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It is an architecture map, not a formula specification. It does not override [SPEC.md](SPEC.md), metric formulas, stress scenario definitions, investment policy logic, data policy, configuration schemas, or current code behavior.

Related documents:

- [README.md](README.md) for project overview, commands, and documentation map.
- [RULES.md](RULES.md) for high-level principles and source-of-truth ownership.
- [WORKFLOW.md](WORKFLOW.md) for task flow, verification, documentation sync, and commit process.
- [SPEC.md](SPEC.md) for canonical technical sources of truth.
- [DATA.md](DATA.md) for data sources, structures, pipeline, quality rules, and data documentation sync triggers.
- [OUTPUTS.md](OUTPUTS.md) for generated outputs, report artifacts, folders, and source-vs-generated boundaries.
- [GLOSSARY.md](GLOSSARY.md) for shared project terminology.
- [DECISIONS.md](DECISIONS.md) for key project decisions and rationale.
- [Detailed Specifications](docs/specs/README.md) for module-specific behavior.
- [Portfolio Review Workflow](docs/specs/portfolio_review_workflow_spec.md) for the portfolio-first
  `analysis_subject` workflow and legacy policy boundary.
- [Business Vision](BUSINESS_VISION.md) for business goals and target users.
- [Product](PRODUCT.md) for user flow, screens, and feature behavior.
- [Diagnostic Product Concept](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) for living target product architecture ideas; non-binding until promoted to specs.
- [Portfolio Construction Policy](docs/specs/portfolio_construction_policy.md) for the main investment policy.

## Architecture Summary

The current project is a Python-based portfolio diagnostics, optimization, comparison, and reporting
system.

Portfolio-first target execution chain:

```text
analysis_subject
-> validation and assumptions
-> Portfolio X-Ray and diagnostics
-> stress / factor / macro / scenario diagnostics
-> candidate generation
-> comparison and decision artifacts
-> report / monitoring / journal
```

Legacy compatibility execution chain:

```text
config.yml
-> data loading / validation
-> optimization
-> weight release checks
-> report and diagnostics
-> generated artifacts
```

Target product chain:

```text
Input & assumptions
-> Portfolio X-Ray
-> Stress Test Lab
-> Candidate Portfolio Factory
-> Candidate comparison
-> Recommendation / no-trade
-> Report export
-> Monitoring / Decision Journal
```

The current implementation is site/API-first (JSON contracts + cache by default) and
CLI/file-driven. Supported partial utility UIs exist
(`config_ui/` for config editing, `results_dashboard/` for read-only result viewing). A full product
workspace UI remains TBD.

## System Boundaries

### In Scope Today

- Canonical portfolio-first workflow contract: resolve and diagnose `analysis_subject` before
  candidates or decision artifacts; runtime transition is active.
- Portfolio-first CLI orchestration that materializes the subject before candidate generation.
- Config-driven portfolio universe and analysis settings.
- Market data loading, FX conversion, and return panel construction.
- Legacy main policy optimization.
- Portfolio weight output and mandate release checks.
- Portfolio metrics and dynamic backtesting.
- Risk contribution diagnostics.
- Stress testing and stress commentary.
- Factor diagnostics, factor covariance analytics, PCA, macro regime diagnostics, scenario libraries, and regime analytics.
- Benchmark and alternative portfolio builders.
- Candidate Portfolio Factory orchestration.
- Canonical candidate comparison and V1 decision artifacts: robustness scorecard, Portfolio Health Score, Selection/No-Trade decision, trade-off/model-risk diagnostics, Assumption Sensitivity, Pareto / Dominance, Regret Analysis, Action Plan, current-vs-policy status, Monitoring / What Changed, generated Decision Journal, and decision package summary.
- CSV, JSON, HTML, TXT, and PDF-style report artifacts.
- Partial utility UIs (`config_ui/`, `results_dashboard/`) for config editing and read-only results.

### Target / TBD

- Full interactive product UI.
- User workspace and saved analyses.
- Portfolio Comparison Arena UI.
- Product UX around the existing file-first Candidate Portfolio Factory and current-vs-policy workflow.
- Dashboard surfaces for implemented diagnostics such as Assumption Sensitivity, Pareto / Dominance, Regret Analysis, and trade-off/model-risk.
- More polished report/PDF packaging beyond the current file-first decision package summary and PDF-style surfaces.
- Monitoring UI and user-maintained journal workflow beyond generated V1 artifacts.
- API / white-label integration.

## High-Level Data Flow

Portfolio-first flow:

```text
Analysis subject input
  -> Subject resolver and assumptions
  -> Subject report diagnostics
  -> Candidate builders
  -> Candidate report diagnostics
  -> Subject-centered comparison
  -> Selection / Action / Monitoring / Journal
  -> Report package
```

Legacy policy flow:

```text
Configuration
  -> Data loaders
  -> Return panels
  -> Optimization inputs
  -> Main policy optimizer
  -> ProLiquidity / release checks
  -> Portfolio weights
  -> Report pipeline
  -> Metrics / stress / factor / regime / scenario diagnostics
  -> Commentary and export artifacts
```

Benchmark variants follow a parallel flow:

```text
Configuration + eligible universe + return panels
  -> variant builder
  -> fixed candidate weights
  -> same report pipeline
  -> variant output folder
```

Scenario-based robust optimization follows an additive flow:

```text
Main report artifacts
  -> scenario_library_normalized.json + stress_report.json
  -> scenario robust optimizer
  -> robust scenario candidate weights
  -> robust scenario portfolio report
```

## Main Runtime Entry Points

| Entry point | Role | Primary outputs |
| --- | --- | --- |
| `run_portfolio_review.py` | Portfolio-first review orchestration | `{output_dir_final}/analysis_subject/`, candidate factory/comparison outputs |
| `run_optimization.py` | Legacy policy optimization compatibility flow | `portfolio_weights.yml`, `run_result.json`, diagnostics under `output_dir_final` |
| `run_report.py` | Main report and diagnostics flow | `stress_report.json`, scenario libraries, CSV/JSON/HTML/TXT/PDF-style artifacts |
| `run_view_after_optimization.py` | Approved post-optimization tactical tilt protocol | Tilted view outputs without changing policy rules outside the protocol |
| `run_compare_variants.py` | Variant comparison flow | Comparison and downstream decision-package artifacts across policy and benchmark portfolios |
| `run_candidate_factory.py` | Candidate factory orchestration (phased: weights → lightweight compare → optional full report export) | `candidate_factory_run.json` / `.txt`, per-candidate `candidate_manifest.json`, optional comparison tail |
| `run_rebalance.py` | Rebalance-oriented utility flow | Rebalance outputs where configured |

Factory `standard` mode builds candidate weights in menu order, then may run Phase 2
`lightweight_comparison` reports concurrently when `--parallel-lightweight-reports` is requested
and no fallback condition applies. Phase 3 full report export and candidate builders remain
sequential.

## Candidate And Baseline Entry Points

| Entry point | Candidate type | Architecture role |
| --- | --- | --- |
| `run_equal_weight.py` | Equal Weight by assets | Benchmark candidate |
| `run_equal_weight_by_asset_class.py` | Equal Weight by asset class | Benchmark candidate using taxonomy buckets |
| `run_risk_parity.py` | Risk Parity | Benchmark candidate |
| `run_risk_budget_by_asset_class.py` | Risk Budgeting by class | Benchmark candidate |
| `run_risk_budget_by_asset.py` | Risk Budgeting by asset | Benchmark candidate |
| `run_hierarchical_risk_parity.py` | HRP | Benchmark candidate |
| `run_minimum_variance.py` | Constrained Minimum Variance | Benchmark candidate under policy-like bounds |
| `run_minimum_variance_uncapped.py` | Uncapped long-only Minimum Variance | Benchmark candidate |
| `run_minimum_variance_advanced.py` | Advanced Minimum Variance controls | Benchmark candidate with advanced controls |
| `run_maximum_diversification.py` | Constrained Maximum Diversification | Benchmark candidate |
| `run_maximum_diversification_unconstrained.py` | Unconstrained long-only Maximum Diversification | Benchmark candidate |
| `run_minimum_cvar_uncapped.py` | Uncapped Minimum CVaR | Benchmark candidate |
| `run_minimum_cvar_constrained.py` | Constrained Minimum CVaR | Benchmark candidate |
| `run_robust_mv_lambda_calibration.py` | Robust MV lambda calibration | Calibration and candidate-selection support |
| `run_robust_mean_variance_uncapped.py` | Robust Mean-Variance uncapped | Benchmark candidate |
| `run_robust_mean_variance_constrained.py` | Robust Mean-Variance constrained | Benchmark candidate |
| `run_robust_scenario_optimization.py` | Scenario-Based Robust Optimization | Additive robust scenario candidate builder |
| `run_robust_scenario_portfolio_report.py` | Robust scenario candidate report | Full report for robust scenario weights |

These entry points create comparison portfolios. They do not replace the diagnosed
`analysis_subject` in the portfolio-first workflow, and they do not replace the legacy policy
optimizer unless a future canonical spec changes that rule.

## Module Layers

### 1. Configuration And Validation

Purpose:

Load and validate the analysis setup.

Key files:

- `config.yml`
- `config.yml.example`
- `config/client_profiles.yml`
- `assets.yml`
- `src/config.py`
- `src/config_schema.py`
- `src/analysis_setup.py`
- `src/input_assumptions.py`
- `src/client_profiles.py`

Inputs:

- Analysis mode.
- Tickers.
- Optional current weights for existing-portfolio diagnostics.
- Investor currency.
- Benchmark.
- Risk profile.
- Targets and constraints.
- Output directories.
- Return frequency.
- Feature settings.

Outputs:

- Validated config object.
- Resolved profile values.
- Cash and risk-free configuration.
- Validation errors for invalid setup.

Notes:

- Final production weights are not manually authored as the normal workflow.
- Existing-portfolio diagnostics may use user-supplied `current_weights` in `analysis_mode=analyze_current_weights`.
- Client profiles fill targets; they do not replace the optimizer.

### 2. Universe Taxonomy And Metadata

Purpose:

Annotate and validate ETF/stock metadata without changing optimizer membership in V1.

Key files:

- `config/etf_universe.yml`
- `config/stock_universe.yml`
- `src/etf_universe.py`
- `src/stock_universe.py`
- `run_etf_universe.py`
- `run_stock_universe.py`

Inputs:

- Active config ticker list.
- ETF taxonomy.
- Stock taxonomy.
- Optional asset metadata.

Outputs:

- Universe diagnostics.
- Taxonomy warnings.
- CSV/JSON exports.
- `etf_universe_validation.json` where applicable.

Boundary:

Taxonomy is annotation-only in V1. It does not select tickers, change optimizer eligibility, or change weights.

### 3. Data Loading, FX, And Return Panels

Purpose:

Load adjusted prices, convert currencies, align calendars, and build return panels.

Key files:

- `src/data_loader.py`
- `src/data_yf.py`
- `src/data_fred.py`
- `src/data_ecb.py`
- `src/fx.py`
- `src/returns.py`
- `src/returns_frequency.py`
- `src/resample.py`
- `src/windows.py`
- `src/cache.py`

Inputs:

- Tickers.
- Benchmark.
- Cash proxy.
- Risk-free source.
- Investor currency.
- Return frequency.
- Analysis windows.
- Cache settings.

Outputs:

- Adjusted price data.
- FX-adjusted price data.
- Return panels.
- `analysis_end`.
- Frequency disclosure.
- Risk-free series.

Core rules:

- Use adjusted close prices.
- Convert FX before returns.
- Use effective month-end for monthly returns.
- Use inner joins where specs require synchronous observations.
- Follow `returns_frequency` for the main investor return panel.

### 4. Legacy Main Policy Optimization

Purpose:

Generate policy portfolio weights under the legacy compatibility investment policy path.

Key files:

- `run_optimization.py`
- `src/optimization.py`
- `src/young_etfs_dual_cov.py`
- `src/robustness.py`
- `src/policy_math/`

Inputs:

- Validated config.
- Eligible risk tickers.
- Return panel.
- Expected returns.
- Covariance matrix.
- Weight bounds.
- Target volatility and return soft objective settings.
- Cash and liquidity settings.

Outputs:

- Risk asset weights.
- Cash-adjusted final weights.
- Optimization status.
- Robustness diagnostics.
- Release status.
- `portfolio_weights.yml` when release is allowed.
- `run_result.json`.

Architecture rule:

The policy optimizer remains callable and tested, but the portfolio-first workflow does not use it
as the default starting portfolio or default candidate. Benchmark variants are comparison tools.

### 5. Release Checks And Mandate Gates

Purpose:

Decide whether optimized weights can be released.

Key files:

- `run_optimization.py`
- `src/metrics_asset.py`
- `src/optimization.py`
- `docs/specs/production_workflow.md`
- `docs/specs/portfolio_construction_policy.md`

Inputs:

- Final candidate weights.
- Return history.
- Client targets.
- Mandate maximum drawdown.
- Stress diagnostics where applicable.

Outputs:

- `APPROVED`, `OK_FALLBACK`, `FAIL_DATA`, or `FAIL_MANDATE` style statuses.
- Violations and next actions.
- Released or blocked weights.

Boundary:

Historical mandate max drawdown can block release. Diagnostic stress outputs do not block release unless a canonical spec explicitly changes that behavior.

### 6. Portfolio Metrics And Backtest

Purpose:

Measure portfolio and asset behavior.

Key files:

- `src/metrics_asset.py`
- `src/metrics_portfolio.py`
- `src/metrics_daily.py`
- `src/portfolio_dynamic.py`
- `src/portfolio_analytics.py`
- `src/risk_contrib.py`

Inputs:

- Portfolio weights.
- Return panels.
- Benchmark returns.
- Risk-free series.
- Analysis windows.
- Backtest mode.

Outputs:

- Asset metrics.
- Portfolio metrics.
- Drawdown and recovery metrics.
- Rolling metrics where implemented.
- Dynamic NaN-safe portfolio returns.
- RC_vol diagnostics.

Boundary:

Metric definitions are governed by [Metrics Specification](docs/specs/metrics_specification.md). Architecture docs must not redefine formulas.

### 7. Stress, Factor, Regime, And Scenario Diagnostics

Purpose:

Diagnose crisis behavior, factor exposures, macro regimes, and scenario readiness.

Key files:

- `src/stress.py`
- `src/stress_factors.py`
- `src/stress_covariance_taxonomy.py`
- `src/stress_scenario_analytics.py`
- `src/stress_factors_macro.py`
- `src/data_macro_sources.py`
- `src/regime_factor_analytics.py`
- `src/regime_portfolio_metrics.py`
- `src/historical_stress_fallback.py`
- `src/scenario_library.py`
- `src/scenario_library_normalized.py`

Inputs:

- Portfolio weights.
- Return panels.
- Factor data.
- Macro data.
- Stress scenario definitions.
- Taxonomy metadata.
- Historical stress proxy map.

Outputs:

- `stress_report.json`.
- Factor betas and regression diagnostics.
- Factor covariance analytics.
- Portfolio PCA diagnostics.
- Macro regime diagnostics.
- Regime factor analytics.
- Regime portfolio metrics.
- Stress scenario analytics.
- `scenario_library.json`.
- `scenario_library_normalized.json`.
- CSV diagnostics under `results_csv/`.

Boundary:

These diagnostics contextualize portfolio behavior. They do not directly control optimizer weights unless a canonical spec explicitly defines such a path.

### 8. Candidate Portfolio Builders

Purpose:

Build alternative portfolios for comparison.

Key files:

- `src/portfolio_variants.py`
- `src/candidate_factory.py`
- `src/risk_parity_spinu.py`
- `src/risk_budgeting.py`
- `src/risk_budgeting_presets.py`
- `src/hrp_weights.py`
- `src/robust_mv.py`
- `src/robust_mv_calibration.py`
- `src/robust_mv_lambda_resolve.py`
- `src/robust_scenario_optimization.py`

Inputs:

- Eligible universe.
- Return panels.
- Covariance matrices.
- Taxonomy metadata.
- Variant-specific config.
- Scenario library artifacts for robust scenario optimization.

Outputs:

- Candidate weights.
- Candidate metadata.
- `candidate_factory_run.json` / `.txt` when the factory orchestration runs.
- Variant output folders.
- Full variant reports where supported.

Boundary:

Candidate builders support comparison and decision-making. They are not the main production policy engine.

### 9. Reporting, Commentary, And Exports

Purpose:

Convert analytics into human-readable and machine-readable artifacts.

Key files:

- `run_report.py`
- `src/snapshot.py`
- `src/portfolio_commentary.py`
- `src/decision_package_reporting.py`
- `src/pdf_reports.py`
- `src/io_export.py`

Inputs:

- Portfolio weights.
- Metrics.
- Stress report.
- Scenario libraries.
- Variant metadata.
- Output directory settings.

Outputs:

- CSV files.
- JSON files.
- HTML snapshots.
- `commentary.txt`.
- `stress_commentary.txt`.
- `decision_package_summary.json` / `.txt` after comparison when decision-package reporting runs.
- PDF-style report artifacts where configured.

Product priority:

Report-first before full UI, unless a future product decision changes this to TBD.

### 10. Comparison And Action Layer

Purpose:

Compare portfolios and translate selected decisions into actions.

Key files:

- `run_compare_variants.py`
- `run_compare_ew_rp.py`
- `run_rebalance.py`
- `src/candidate_comparison.py`
- `src/robustness_scorecard.py`
- `src/portfolio_health_score.py`
- `src/selection_engine.py`
- `src/tradeoff_and_model_risk.py`
- `src/assumption_sensitivity.py`
- `src/pareto_dominance.py`
- `src/regret_analysis.py`
- `src/action_engine.py`
- `src/current_vs_policy.py`
- `src/monitoring.py`
- `src/decision_journal.py`
- `src/decision_package_reporting.py`
- `src/rebalance.py`
- `src/view_after_optimization.py`

Inputs:

- Current weights.
- Candidate weights.
- Metrics and diagnostics.
- Constraints and mandate settings.
- Previous monitoring snapshots where available.

Outputs:

- `candidate_comparison.json` / `.txt`.
- `robustness_scorecard.json` / `.txt`.
- `portfolio_health_score.json` / `.txt`.
- `selection_decision.json` / `.txt`.
- `tradeoff_explanation.json` / `.txt`.
- `model_risk_diagnostics.json` / `.txt`.
- `assumption_sensitivity.json` / `.txt`.
- `pareto_dominance.json` / `.txt`.
- `regret_analysis.json` / `.txt`.
- `action_plan.json` / `.txt`.
- `current_vs_policy_status.json` / `.txt` when current weights are supplied.
- `monitoring_diff.json` / `.txt`.
- `decision_journal.json` / `.txt`.
- `decision_package_summary.json` / `.txt`.
- Rebalance deltas.
- Tactical tilt view where approved.
- Latest/history monitoring and journal copies.

TBD:

- Full Portfolio Comparison Arena UI.
- Product UI flows around existing comparison and decision-package outputs.
- More deliberately designed client-facing report packages.
- Full user-maintained Decision Journal workflow.

Boundary:

The file-first V1 decision artifacts are generated outputs. They support decision review, but they do
not change optimizer formulas, mandate gates, or production weight release unless a canonical spec says
so.

## Main Flow Details

### Portfolio-First Review Flow

```text
1. Load config
2. Resolve analysis_subject, assumptions, mandate, and validation result
3. Build data and return panels
4. Materialize diagnostics for analysis_subject
5. Generate allowed non-policy candidates
6. Materialize candidate diagnostics
7. Compare analysis_subject versus candidates
8. Write Selection / No-Trade, Action, Monitoring, Journal, and report package artifacts
```

Runtime support for this flow is implemented by the active portfolio-first transition sessions. The
required order is already canonical in the portfolio review workflow spec.

### Legacy Policy Compatibility Flow

```text
1. Load config
2. Resolve profile, cash proxy, benchmark, and risk-free settings
3. Validate taxonomy diagnostics where available
4. Load adjusted market data and FX-adjust prices
5. Build return panel and analysis_end
6. Build optimization inputs
7. Run legacy policy optimizer
8. Apply ProLiquidity / cash policy
9. Run mandate and release checks
10. Write weights and run metadata if allowed
11. Run report pipeline
12. Export metrics, stress, commentary, and report artifacts
```

### Report Flow

```text
1. Read config and weights
2. Load data and return panels
3. Compute portfolio and asset metrics
4. Compute dynamic backtest outputs
5. Compute RC_vol diagnostics
6. Run stress diagnostics
7. Run factor, macro, regime, PCA, and scenario diagnostics
8. Build scenario library artifacts
9. Generate commentary and snapshots
10. Export CSV/JSON/HTML/TXT/PDF-style artifacts
```

### Candidate Flow

```text
1. Load config and eligible universe
2. Build candidate-specific weights
3. Save candidate weights and metadata
4. Run the same report pipeline for candidate weights
5. Compare candidate against policy and other variants
```

## Inputs And Outputs

| Layer | Inputs | Outputs |
| --- | --- | --- |
| Configuration | YAML config, profiles, metadata, `analysis_subject` | Validated config, subject, profile-derived targets |
| Data | Tickers, FX, benchmark, risk-free source | Prices, returns, analysis_end, frequency disclosure |
| Legacy optimization | Returns, covariance, constraints, targets | Weights, status, run metadata |
| Release checks | Weights, returns, mandate | Approved or blocked release |
| Metrics | Weights, returns, benchmark, risk-free | Asset/portfolio metrics and RC_vol |
| Stress diagnostics | Weights, returns, factors, scenarios | `stress_report.json` (CSVs in export profiles only) |
| Scenario library | Stress and regime analytics | Scenario library JSON (CSVs in export profiles only) |
| Candidate builders | Universe, returns, covariance, variant settings | Candidate weights and metadata |
| Reporting | Metrics, stress, scenarios, commentary inputs | JSON contracts by default; CSV/HTML/TXT/PNG/PDF only in `full_report` / `legacy_export` |
| Comparison/action | Current and candidate outputs | Comparison, scores, selection, action, monitoring, journal, rebalance, tilt artifacts |

## Generated Artifacts

Generated artifacts are outputs, not source files, unless a task explicitly targets them.
Use [OUTPUTS.md](OUTPUTS.md) for the root output/reporting map and generated-vs-source rules.

Default execution is site/API-first. JSON contracts and required cache are the backend/UI source of
truth; CSV, TXT, HTML, PNG, PDF, Markdown PDF sidecars, and CSS/visual assets are explicit
export/report outputs only. The central policy lives in `src/output_policy.py`; entrypoints expose
`--output-profile` where export behavior is needed. Each major run writes `output_manifest.json`
under `output_dir_final` as the UI/API artifact index.

| Profile | JSON + cache | CSV/TXT/HTML/PNG | PDF / Markdown sidecars |
| --- | --- | --- | --- |
| `site_api` (default) | Yes | No | No |
| `core_json` | Yes | No | No |
| `lightweight_comparison` | Yes | No | No |
| `full_report` | Yes | Yes | No |
| `legacy_export` | Yes | Yes | Yes |

Command matrix (operator entrypoints): see [OUTPUTS.md](OUTPUTS.md#command-matrix) and
[README.md](README.md).

Common generated paths:

- `Main portfolio/`
- `results_csv/`
- `output/`
- `cache/`
- `portfolio_weights.yml`
- `equal-weight portfolio/`
- `risk parity portfolio/`
- `minimum variance portfolio/`
- `maximum diversification portfolio/`
- `minimum cvar constrained portfolio/`
- `robust mean variance constrained portfolio/`
- `robust scenario portfolio/`
- `pdf files/`
- `pdf_md_sources/`

## Dependency Direction

Preferred dependency direction:

```text
Config/data helpers
-> math and analytics modules
-> optimization and candidate builders
-> reporting/export modules
-> CLI entry points
```

Guidelines:

- Shared formulas belong in existing metric, optimization, stress, or risk modules, not in CLI scripts.
- CLI scripts should orchestrate modules rather than duplicate business logic.
- Reporting should consume analytics outputs rather than recompute inconsistent metrics.
- Product concept documents should guide planning but not redefine formulas.

## Architecture Boundaries

### Current Policy Boundaries

- The portfolio-first workflow starts from `analysis_subject` diagnostics before candidate generation
  or decision artifacts.
- The legacy policy optimizer is preserved, but it is not the default portfolio-first starting point
  or default candidate.
- The active optimizer universe comes from `config.yml`.
- ETF and stock taxonomy are annotation-only in V1.
- Final production weights come from the optimizer and approved post-processing protocols.
- RC_vol is diagnostic unless a canonical spec changes it.
- Stress, macro regime, PCA, Kalman, and scenario analytics are diagnostic unless a canonical spec changes them.
- Benchmark variants are comparison tools.

### Target Product Boundaries

- Product UI is report-first before full UI.
- Macro Dashboard is a diagnostic overlay after portfolio and candidate stress evaluation.
- Macro Dashboard contextualizes regime vulnerability without directly controlling optimizer weights.
- Selection Engine, Health Score, No-Trade Recommendation, Monitoring, and Decision Journal have file-first V1 implementations. Full UI/workspace surfaces and user-maintained workflows around them remain target product work.

## Source Of Truth

When architecture and implementation conflict, current code and canonical specs remain authoritative until a planned change updates them.

Primary sources:

- [RULES.md](RULES.md)
- [WORKFLOW.md](WORKFLOW.md)
- [SPEC.md](SPEC.md)
- [Portfolio Review Workflow](docs/specs/portfolio_review_workflow_spec.md)
- [OUTPUTS.md](OUTPUTS.md)
- [DATA.md](DATA.md)
- [TESTING.md](TESTING.md)
- [Portfolio Construction Policy](docs/specs/portfolio_construction_policy.md)
- [Metrics Specification](docs/specs/metrics_specification.md)
- [Stress Testing Spec](docs/specs/stress_testing_spec.md)
- [Feasibility Constraints](docs/specs/feasibility_constraints_spec.md)
- [Data Policy](docs/specs/data_policy_spec.md)
- [Production Workflow](docs/specs/production_workflow.md)
- [DECISIONS.md](DECISIONS.md)
- [CHANGELOG.md](CHANGELOG.md)
- [PLANS.md](PLANS.md)
- [AGENTS.md](AGENTS.md)

Product sources:

- [Business Vision](BUSINESS_VISION.md)
- [Product](PRODUCT.md)
- [Diagnostic Product Concept](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md)

## Open Architecture Questions

- What is the first product UI surface: static report package, local dashboard, or web app?
- Where should persistent analysis state live once the product moves beyond file-driven CLI runs?
- What is the formal data model for saved analyses, candidates, decisions, and monitoring snapshots?
- How should candidate generation be orchestrated before comparison?
- How should implemented V1 decision artifacts be packaged for reports, PDFs, and future UI surfaces?
- Which outputs should become stable API contracts?
- What should be batch-oriented for advisors and family offices?
