# SPEC.md

This file is the compact technical entry point and implementation contract for Portfolio MRI / Portfolio X-Ray.

It defines what must work in the current product, which workflows are binding, which inputs and outputs are expected, which edge cases must be handled, and where detailed technical rules live. Do not duplicate long formulas or module-specific details here when an owning spec exists.

Update this file when the general implementation contract, workflows, inputs/outputs, behavior rules, edge cases, or product status matrix changes. Use [RULES.md](RULES.md) and [WORKFLOW.md](WORKFLOW.md) to decide which companion docs also need updates. Detailed module behavior belongs in `docs/specs/*.md`.

## Status

`SPEC.md` is the canonical implementation entry point. It has higher authority than product concept documents such as [BUSINESS_VISION.md](BUSINESS_VISION.md), [PRODUCT.md](PRODUCT.md), and [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) when the question is current implementation behavior.

The current canonical product truth is **ДИАГНОСТИКА 2**. Product concept documents can describe target direction, but the active product interpretation must follow this distinction:

- current Core MVP = diagnosis-first/current-portfolio-first ДИАГНОСТИКА 2 flow;
- ДИАГНОСТИКА 2 НА ПОТОМ = backlog / advanced / later;
- older optimizer/report/scorecard-heavy modules may remain implemented as backend evidence, technical artifacts, generated support, legacy compatibility, or advanced research, but they are not the current Core MVP product flow unless explicitly promoted by specs and code.

They do not change formulas, scenarios, optimizer policy, data rules, output contracts, or code behavior until this spec and the relevant detailed specs are updated.

The documentation migration replaced the active business, product, diagnostic concept, and architecture docs while archiving their prior versions under `docs/archive/documentation_migration_2026_05_25/`. Product and architecture docs still do not override this implementation contract; target modules remain non-binding until promoted into owning specs and code.

Terminology boundary: product-facing documents should describe the current user-facing decision layer as `Decision Verdict`. The technical contracts remain `Selection Engine`, `selection_decision.json`, and No-Trade artifacts until a separate schema/output migration is specified and implemented. Those technical contracts are backend evidence, not the canonical product language.

## Canonical Product Scope

Canonical current product flow:

```text
Input portfolio
-> Portfolio X-Ray
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary / grounding
-> Monitoring / What Changed
```

This is the ДИАГНОСТИКА 2 product truth. The implementation is still CLI/file-driven and partially report-first, but current product surfaces must be interpreted through this flow, not through the older optimization/scorecard/report package.

## Implementation Scope

The canonical portfolio-first workflow contract is [Portfolio Review Workflow
Specification](docs/specs/portfolio_review_workflow_spec.md): resolve `analysis_subject`, diagnose
that portfolio first, then generate and compare alternatives. `run_portfolio_review.py` is the
portfolio-first orchestration entrypoint (`--mode core` default, `--mode full`,
`--resume-candidates` for interrupted full factory runs). Legacy policy-first entrypoints remain
callable as compatibility infrastructure only; they are not the default starting path.

Blocks 1-5 MVP core reliability (input validation, factory freshness, resumability, optimizer
readiness disclosure, offline smoke, data-trust summaries) is governed by the active
[Blocks 1-5 MVP Core Reliability Plan](docs/exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md).

**Artifact and audit-scope boundaries:** the portfolio-first CLI may still write Blocks 1-5
diagnostics and the older V1 decision-support package in one orchestrated path. That does not make
every generated file part of the current Core MVP product. Blocks 1-5 audits/walkthroughs
**exclude** Selection, Action, Monitoring, and Journal interpretation unless the task explicitly
targets those backend/advanced artifacts. `candidate_factory_run.json` records last factory
orchestration; `candidate_comparison.json` aggregates on-disk candidate evidence (may be wider than
the last factory run). Operator definitions:
[GLOSSARY.md](GLOSSARY.md) (**Blocks 1–5 deliverable**, **Decision package**, factory/comparison
evidence terms); confusion register:
[2026-05-23 core/full artifact confusion audit](docs/audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md);
remediation plan:
[2026-05-23 core/full artifact documentation confusion plan](docs/exec_plans/2026-05-23_core_full_artifact_documentation_confusion_plan.md).

Current Core MVP product layer:

- portfolio-first `analysis_subject` diagnosis
- Portfolio X-Ray diagnostics (**Block 2.1–2.6** product contracts on `portfolio_xray.json`; legacy X-Ray section 2.7 (archetype) is not Core MVP)
- Stress Test Lab evidence
- Problem Classification
- Candidate Launchpad
- Portfolio Alternatives Builder backend delegation plan
- Current-vs-Candidate adapter
- Decision Verdict mapping
- AI Commentary grounding context
- light What Changed summary

Implemented backend / advanced / legacy support:

- config validation and profile-derived targets
- market data loading, FX conversion, and return panel construction
- legacy policy optimization and weight release checks
- portfolio metrics, dynamic backtesting, risk contribution diagnostics, and stress diagnostics
- factor, macro/regime, PCA, scenario-library, and robustness diagnostics
- benchmark and candidate portfolio reports
- canonical candidate comparison and V1 decision-support artifacts: robustness scorecard, Portfolio Health Score, Selection/No-Trade decision, trade-off and model-risk diagnostics, Assumption Sensitivity, Action Plan, technical Monitoring, generated Decision Journal, current-vs-policy status, and candidate factory run summary. These are not current Core MVP product flow; they are advanced/backend/technical/generated support unless explicitly requested.
- decision package report summary (`decision_package_summary.txt` / `.json`, optional `report.txt` append, decision-package PDF after comparison)
- CSV, JSON, HTML, TXT, and PDF-style report artifacts

Target product areas that remain TBD until separately specified and implemented:

- full interactive UI and saved analysis workspaces
- formal diagnosis-only product state beyond current generated artifacts and workflow-state metadata
- full Candidate Launchpad / Portfolio Alternatives Builder UI and user-triggered candidate
  generation as the default product behavior
- current-vs-selected-candidate UX as the primary interactive comparison mode beyond the current
  additive JSON adapter
- Decision Verdict replacing or renaming current Selection Engine terminology
- generated natural-language AI Commentary beyond the current grounding context
- user-maintained journal/workflow layers beyond the generated V1 Decision Journal
- Portfolio Health Score / Robustness Scorecard as standalone/current primary product modules (not current Core MVP; advanced/backend/backlog only)
- Portfolio Archetype Classification as a Core MVP / product-facing Block 2 module (legacy `sections.portfolio_archetype` may remain on full X-Ray builds; product contract is Blocks 2.1–2.6 — archetype is §2.7, not Core MVP — see [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md))
- Macro Dashboard / Macro Overlay as a product module
- full multi-candidate ranking/arena as default product UX
- full Action Plan / Rebalancing Advisor as product module
- advanced monitoring workspace
- Crisis Replay UI, What Happens If UI, Client-Fit Check, Asset X-Ray, Max Sharpe, tax-aware optimization, turnover-aware optimizer objective, tactical tilt as product UX, full custom constraints UI, multi-client workspace, and polished PDF report product

Do not describe target UI/schema migration work as current implementation unless the relevant source
code, generated artifacts, and owning specs verify that status.

## Main Workflows

Portfolio-first review workflow (binding transition contract, interpreted through ДИАГНОСТИКА 2):

```text
analysis_subject / current portfolio
-> resolved assumptions and validation
-> Portfolio X-Ray
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> selected candidate or generated shortlist
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary grounding
-> Monitoring / What Changed
```

The subject must be diagnosed before candidate generation or candidate decision artifacts are
presented as the main result. Technical comparison, scorecard, selection, action, monitoring diff,
journal, and report package artifacts may exist, but they must not be presented as the current Core
MVP answer. Supported subject types are `current_portfolio`, `model_portfolio`,
and `universe_baseline`; details live in
[portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md).

Legacy policy workflow (compatibility only):

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
| Portfolio X-Ray layer mapping (Block 2.1-2.7) | [docs/specs/portfolio_xray_layer_spec.md](docs/specs/portfolio_xray_layer_spec.md) |
| Analysis setup, input modes, current weights, mandate inputs, and calculation assumptions | [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md) |
| Metrics, estimators, returns, FX, windows, covariance, beta, RC_vol, drawdown, rounding | [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md) |
| Portfolio construction, optimizer behavior, ProLiquidity, mandate gate, policy optimizer boundaries | [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md) |
| Optimization Engine layer roles, objective/estimator/constraint/status/output matrices, and target-only boundaries | [docs/specs/optimization_engine_layer_spec.md](docs/specs/optimization_engine_layer_spec.md) |
| Feasibility and weight constraints | [docs/specs/feasibility_constraints_spec.md](docs/specs/feasibility_constraints_spec.md) |
| Data policy, NaN handling, young ETFs, return panels, backtest handling | [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md) |
| Stress scenarios and stress diagnostics | [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md) |
| Stress Lab layer mapping (Block 3.1-3.6), provenance, and handoff index | [docs/specs/stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md) |
| Stress Lab methodology map (Block 3 audit baseline) | [docs/audits/2026-05-20_stress_lab_methodology_map.md](docs/audits/2026-05-20_stress_lab_methodology_map.md) |
| Hedge gap analysis contract | [docs/specs/hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md) |
| Crisis replay path contract | [docs/specs/crisis_replay_spec.md](docs/specs/crisis_replay_spec.md) |
| Factor diagnostics and factor-risk outputs | [docs/specs/factor_diagnostics_spec.md](docs/specs/factor_diagnostics_spec.md) |
| Macro regime diagnostics | [docs/specs/macro_regime_spec.md](docs/specs/macro_regime_spec.md) |
| Scenario Library and normalized scenario view | [docs/specs/scenario_library_spec.md](docs/specs/scenario_library_spec.md) |
| Candidate and benchmark portfolios | [docs/specs/candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md) |
| Candidate portfolio factory orchestration | [docs/specs/candidate_factory_spec.md](docs/specs/candidate_factory_spec.md) |
| Candidate Factory layer mapping (Block 4.1–4.9) | [docs/specs/candidate_factory_layer_spec.md](docs/specs/candidate_factory_layer_spec.md) |
| Candidate Factory methodology map (Block 4 audit baseline; gaps G1–G10) | [docs/audits/2026-05-20_candidate_factory_methodology_map.md](docs/audits/2026-05-20_candidate_factory_methodology_map.md) |
| Candidate Factory governance ExecPlan (Phase 14 Sessions 00–11) | [docs/exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md](docs/exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md) |
| Optimization Engine layer specification (Block 5 canonical source of truth) | [docs/specs/optimization_engine_layer_spec.md](docs/specs/optimization_engine_layer_spec.md) |
| Optimization Engine methodology map (Block 5 audit baseline; gaps G1-G10) | [docs/audits/2026-05-20_optimization_engine_methodology_map.md](docs/audits/2026-05-20_optimization_engine_methodology_map.md) |
| Optimization Engine governance ExecPlan (Phase 15 Sessions 00–12; closed 2026-05-21) | [docs/exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md](docs/exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md) |
| Canonical candidate comparison artifact | [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md) |
| Downstream decision readiness (Blocks 6–7 eligibility guards) | [docs/specs/downstream_decision_readiness_spec.md](docs/specs/downstream_decision_readiness_spec.md), [src/downstream_decision_readiness.py](src/downstream_decision_readiness.py) |
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
- `config.yml.example` (MVP-first Section 1; legacy mandate/optimizer in Sections 4–7)
- `config/client_profiles.yml` (legacy optimizer profiles; not required for Core MVP diagnosis)
- `assets.yml`
- `config/etf_universe.yml`
- `config/stock_universe.yml`
- optional historical stress proxy map and external data source settings
- `tests/fixtures/mvp_portfolios/` minimal USD fixtures for validation and offline tests

The data-layer map is [DATA.md](DATA.md). Keep it aligned when data sources, expected structures, data pipeline, NaN handling, FX logic, benchmarks, risk-free inputs, factor/macro inputs, config fields, or data validation rules change.

**Core MVP user-facing config** (portfolio-first `run_portfolio_review.py`; canonical detail in
[input_assumptions_spec.md](docs/specs/input_assumptions_spec.md) § Core MVP Input Surface):

| Required user input | Config keys |
| --- | --- |
| Instruments | `tickers` |
| Allocation | `weights`, `current_weights`, or `analysis_subject.weights` (positive map) |
| Reporting currency | `investor_currency` |

`validate_config` calls `apply_mvp_input_defaults` (`src/mvp_input.py`): when the user supplies
`current_weights` or non-generated `weights` without explicit `analysis_subject`, the system
injects `analysis_subject.type = current_portfolio` and
`analysis_mode = analyze_current_weights`. For USD/EUR Core MVP, `risk_free_source`,
`cash_proxy_ticker`, and `base_benchmark_ticker` resolve via `src/config.py` when omitted.
`client_profile`, liquidity floors, `portfolio_value`, and mandate caps are **not** required for
the diagnosis path; they remain `legacy_advanced` tiers for `run_optimization.py` and full mandate
runs.

**Real cash holdings:** labels such as `Cash USD` are explicit zero-return positions in weights;
they must not be replaced by `cash_proxy_ticker` (BIL/PEU). Implementation: `src/real_cash.py`.

Primary runtime inputs (resolved after validation):

- `analysis_subject` for the portfolio-first review workflow: the current, model, or
  universe-baseline portfolio diagnosed before candidates; explicit config is resolved in
  `analysis_setup.analysis_subject`
- resolved `analysis_setup` for the input and assumptions layer
- ticker universe and investor currency
- benchmark, cash proxy, and risk-free source (user override or currency defaults)
- return frequency, optimization targets/constraints, output paths (technical defaults for Core MVP)
- optional profile name (legacy optimizer)

Generated weights are not normal user input. The legacy policy workflow writes
`portfolio_weights.yml` and `run_result.json` when release is allowed, but generated policy weights
are not the default `analysis_subject` in the portfolio-first workflow.

`analysis_setup` is the resolved runtime contract for portfolio input, mandate, assumptions, and validation metadata. `input_assumptions` is an exported/reporting view of that contract (including `input_surface` and `field_tiers` disclosure), not a separate business-logic source. Downstream analytics consume `analysis_setup` or `PortfolioConfig`, not `input_assumptions` alone.

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

`portfolio_xray.json` is generated by the report path as a diagnostic-only X-Ray summary. It consumes existing report pipeline outputs and in-memory diagnostics; it does not optimize, change weights, change mandate gates, change stress pass/fail status, or select portfolios. **Core MVP product diagnosis** uses top-level `block_2_1_asset_allocation` through `block_2_6_portfolio_weakness_map`; `sections.portfolio_archetype` and legacy `sections.weakness_map` are advanced/backlog compatibility for formatters. UI/API should prefer product blocks 2.1–2.6 over legacy `sections.*` where both exist. Detailed contracts: [docs/specs/portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md).

`run_result.json` and `run_metadata.json` include `analysis_setup` plus projected `input_assumptions`.
Legacy policy `run_result.json` also includes `optimizer_run_metadata` describing the policy
optimizer objective, input window, estimators, universe, bounds/caps, cash policy, solver/fallback
status, release gate, estimator input fingerprints, covariance methodology, and Young ETF
methodology.

Optimizer candidate `baseline_weights_metadata.json` exports for Minimum Variance, Maximum
Diversification, Minimum CVaR, Robust Mean-Variance, and materialized Robust Scenario include a candidate-only
`optimizer_run_metadata` envelope. It explains method, objective, input window, estimator,
constraints/bounds, solver/fallback quality, relevant parameters, input fingerprints, and output
summary fields, including covariance and Young ETF methodology disclosure, without changing
candidate formulas, weights, mandate gates, or comparison semantics.

`candidate_comparison.json` propagates available normalized optimizer metadata into each row's
`construction_disclosure.optimizer_methodology`. This is read-only disclosure of method, objective,
constraints, covariance/Young ETF methodology, solver/fallback quality, candidate-only status, and
freshness. `candidate_comparison.txt` and legacy `ips_summary.txt` summarize those methodology
fields for human review when source metadata is present.

Beginning with Optimization Engine Session 06, `candidate_factory_run.json` step excerpts and
`candidate_comparison.json` rows also surface normalized optimizer quality. Fallback or approximate
optimizer quality is not clean success: comparison degrades otherwise available optimizer rows and
Selection warns when such a row is favored. Failed current factory or optimizer quality makes the
row unavailable. These boundaries do not change optimizer formulas, fallback branches, generated
weights, or mandate gates.

## Binding Behavior Rules

- Use adjusted close prices and convert FX before returns.
- Compute `analysis_end` as the last completed effective period before today according to the metrics spec.
- Align series using the rules in the relevant metric, beta, covariance, correlation, RC_vol, stress, or data spec.
- Preserve full precision internally and round only at final export/report stage.
- Do not invent formulas, scenarios, estimators, constraints, or statuses when a canonical spec exists.
- In the portfolio-first workflow, diagnose `analysis_subject` before generating candidates or
  presenting comparison/decision artifacts as the main review outcome.
- The old policy optimizer is legacy/compatibility infrastructure only; it is not the default
  starting portfolio and is not a default candidate unless a future accepted spec changes that
  boundary.
- Explicit weighted `current_portfolio` / `model_portfolio` subjects reject material
  overallocations at config validation; partial weights below `1.0` export
  `partial_with_cash_remainder` in `analysis_setup` / `input_assumptions`.
- `candidate_comparison.json` must treat `candidate_factory_run.json` as current, missing, stale, or
  not authoritative via `candidate_menu.factory_evidence_status`; stale factory `steps[]` are not
  row-level construction evidence.
- Optimizer-backed comparison rows with missing methodology/quality or `unknown` solver quality
  degrade rather than remain ordinary `available` evidence.
- Final policy weights come from optimization plus approved post-processing only.
- View After Optimization is the only permitted manual post-optimization tilt protocol.
- Taxonomy validates and annotates in V1; it does not select tickers or change weights.
- Diagnostic blocks do not affect optimizer inputs, mandate gates, stress pass/fail, or weight release unless a canonical spec says so.
- Scenario stress is diagnostic; mandate maximum drawdown can block weight release.
- Optimization Engine roles and target-only objective boundaries are governed by [docs/specs/optimization_engine_layer_spec.md](docs/specs/optimization_engine_layer_spec.md). Max Sharpe, drawdown-controlled, macro-resilient, tax-aware, and turnover-aware optimizer objectives are not current runtime behavior unless a later accepted spec and implementation add them.
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
| Portfolio-first review workflow (`analysis_subject` first) | Implemented; `run_portfolio_review.py` is the default entrypoint |
| Blocks 1-5 MVP core reliability (Phase 16) | **Done** (Sessions 01-09, `RM-1010`-`RM-1018`); offline acceptance bundle and operator runbook govern routine verification |
| Main CLI optimization and report pipeline | Implemented |
| Input and Assumptions Layer | Implemented CLI/file-driven V1; Core MVP three-field surface, MVP defaults injection, real-cash holdings, `input_surface` / `field_tiers` export ([input_assumptions_spec.md](docs/specs/input_assumptions_spec.md); [Input Layer MVP Migration](docs/exec_plans/2026-05-26_input_layer_mvp_migration.md) Sessions 01–09) |
| Portfolio X-Ray Core MVP (Blocks 2.1–2.6) | Blocks 2.1–2.6 **implemented** on `portfolio_xray.json` ([portfolio_xray_layer_spec.md](docs/specs/portfolio_xray_layer_spec.md), [Block 2.6 acceptance audit](docs/audits/2026-05-26_block_2_6_portfolio_weakness_map_acceptance_audit.md)) |
| Risk Budget View (Block 2.5) | Product block `block_2_5_risk_budget_view` **implemented** (Sessions 00–08, 2026-05-26); legacy `sections.risk_budget_view` preserved ([portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §2.5.1) |
| Portfolio Weakness Map (Block 2.6) | Product block `block_2_6_portfolio_weakness_map` **implemented** (Sessions 00–08, 2026-05-26); pre-stress over Blocks 2.1–2.5; legacy `sections.weakness_map` preserved ([portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §2.6.1, [acceptance audit](docs/audits/2026-05-26_block_2_6_portfolio_weakness_map_acceptance_audit.md)) |
| Portfolio Archetype Classification (Block 2.7) | Legacy section implemented (`sections.portfolio_archetype`); **postponed** for product — advanced/backlog, not Core MVP ([portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §2.7) |
| Config validation and profile-derived targets | Implemented |
| Portfolio metrics, backtests, risk contribution | Implemented |
| Stress testing and stress commentary | Implemented diagnostic/reporting layer |
| Factor diagnostics, PCA, macro/regime diagnostics, scenario analytics | Implemented diagnostic-only layer |
| Scenario Library and normalized scenario view | Implemented input-standardization/diagnostic layer |
| Optimization Engine layer governance | Implemented source of truth; Sessions 03-04 add legacy policy and candidate optimizer disclosure without changing optimizer behavior |
| Benchmark and candidate portfolio builders | Implemented comparison layer |
| Candidate Factory runtime | Implemented backend/advanced/research infrastructure; `standard` mode supports opt-in parallel Phase 2 `lightweight_comparison` reports while builders and Phase 3 full reports remain sequential; not the default product UX |
| Robust Mean-Variance and Scenario-Based Robust Optimization | Implemented benchmark/candidate layer |
| Canonical candidate comparison | Implemented (`candidate_comparison.json` via [src/candidate_comparison.py](src/candidate_comparison.py)); includes `analysis_subject` baseline row when materialized |
| Robustness Scorecard | Implemented diagnostic artifact (`robustness_scorecard.json` via [src/robustness_scorecard.py](src/robustness_scorecard.py)) |
| Portfolio Health Score | Implemented diagnostic artifact (`portfolio_health_score.json` via [src/portfolio_health_score.py](src/portfolio_health_score.py)) |
| ETF and stock taxonomy | Implemented annotation-only V1 |
| Generated CSV/JSON/HTML/TXT/PDF-style reports | Implemented |
| Full interactive UI | Target/TBD |
| Diagnosis-only product state as formal UX/workflow state | Target/TBD; current generated artifacts may support diagnosis review, but a formal product state requires code/spec verification |
| Problem Classification | Implemented diagnostic artifact (`problem_classification.json` via [src/problem_classification.py](src/problem_classification.py)); translates existing X-Ray/stress evidence into problems and paths to test without changing formulas or making decisions |
| Candidate Launchpad | Implemented data artifact (`candidate_launchpad.json` via [src/candidate_launchpad.py](src/candidate_launchpad.py)); translates Problem Classification into hypothesis cards only, not portfolios or builder execution |
| Portfolio Alternatives Builder as user-triggered candidate UX | Backend wrapper implemented (`PortfolioAlternativeBuildPlan` via [src/portfolio_alternatives_builder.py](src/portfolio_alternatives_builder.py)); returns one-candidate factory delegation plans, while full UX remains Target/TBD and batch factory remains backend/advanced/research |
| Current-vs-selected-candidate as primary interactive UX | Adapter artifact implemented (`current_vs_candidate.json` via [src/current_vs_candidate.py](src/current_vs_candidate.py)); interactive UX remains Target/TBD, canonical comparison remains unchanged |
| Decision Verdict product language | Implemented additive mapping artifact (`decision_verdict.json` via [src/decision_verdict.py](src/decision_verdict.py)); current technical contract remains Selection Engine / No-Trade |
| AI Commentary formal explanation layer | Grounding context only (`ai_commentary_context.json` via [src/ai_commentary_context.py](src/ai_commentary_context.py); no LLM). Deterministic `commentary.txt` / stress commentary are separate report exports. Generated natural-language AI commentary remains Target/TBD (`RM-ARCH-010` in [docs/ROADMAP.md](docs/ROADMAP.md)) |
| Formal Selection Engine and No-Trade | Implemented (`selection_decision.json` via [src/selection_engine.py](src/selection_engine.py)); portfolio-first baseline is `analysis_subject`, with legacy fallback to `current` |
| Trade-off Explanation and Model Risk Diagnostics | Implemented ([src/tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py); [tradeoff_and_model_risk_spec.md](docs/specs/tradeoff_and_model_risk_spec.md)) |
| Assumption Sensitivity | Implemented ([src/assumption_sensitivity.py](src/assumption_sensitivity.py); [assumption_sensitivity_spec.md](docs/specs/assumption_sensitivity_spec.md)) |
| Pareto / Dominance Check | Implemented ([src/pareto_dominance.py](src/pareto_dominance.py); [pareto_dominance_spec.md](docs/specs/pareto_dominance_spec.md)) |
| Regret Analysis | Implemented ([regret_analysis_spec.md](docs/specs/regret_analysis_spec.md); `src/regret_analysis.py`, `regret_analysis.json` / `.txt`) |
| Action Engine and Rebalancing Advisor | Implemented (`action_plan.json` via [src/action_engine.py](src/action_engine.py)) |
| Monitoring / What Changed | Implemented (V1) - [monitoring_spec.md](docs/specs/monitoring_spec.md), `src/monitoring.py`; light product summary implemented as `what_changed_summary.json` via [src/light_monitoring_summary.py](src/light_monitoring_summary.py) |
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
