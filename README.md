# Portfolio X-Ray & Optimization Terminal

Portfolio X-Ray & Optimization Terminal, also described as Portfolio MRI, is a Python portfolio research, optimization, diagnostics, and reporting system.

Its purpose is decision support, not black-box allocation. The system helps a user understand portfolio exposures, hidden risks, stress behavior, candidate allocations, robustness trade-offs, and generated report artifacts.

Product concept documents describe target direction only. Current behavior is governed by [SPEC.md](SPEC.md), [RULES.md](RULES.md), [DATA.md](DATA.md), [OUTPUTS.md](OUTPUTS.md), and detailed specs under [docs/specs/](docs/specs/README.md).

## Current Scope

Implemented today:

- Canonical portfolio-first workflow contract through `analysis_subject`; runtime transition is active
  and governed by [portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md).
- Portfolio-first CLI orchestration through `run_portfolio_review.py`.
- Legacy CLI/file-driven policy optimization compatibility through `run_optimization.py`.
- Portfolio reporting and diagnostics through `run_report.py`.
- Input and Assumptions Layer V1 through `analysis_mode`, `tickers`, optional `current_weights`, profile/target fields, and technical calculation settings in `config.yml`.
- Portfolio metrics, dynamic NaN-safe backtesting, and risk contribution diagnostics.
- Stress diagnostics, stress commentary, factor diagnostics, macro/regime diagnostics, PCA, scenario libraries, and robustness diagnostics.
- Benchmark/candidate portfolios including Equal Weight, Risk Parity, HRP, Minimum Variance, Maximum Diversification, Minimum CVaR, Robust Mean-Variance, and Scenario-Based Robust Optimization.
- Candidate Portfolio Factory orchestration through `run_candidate_factory.py`.
- Canonical candidate comparison and V1 decision artifacts through `run_compare_variants.py`: robustness scorecard, Portfolio Health Score, Selection/No-Trade decision, trade-off/model-risk diagnostics, Assumption Sensitivity, Pareto / Dominance, Regret Analysis, Action Plan, current-vs-policy status, Monitoring / What Changed, generated Decision Journal, and decision package summary.
- CSV, JSON, HTML, TXT, and PDF-style generated artifacts.
- ETF and stock taxonomy validation as annotation/diagnostic layers.
- Partial utility UIs: `config_ui/` (local config editor) and `results_dashboard/` (read-only results viewer). These are supported utility surfaces, not the full product workspace.

Target/TBD areas:

- Full interactive UI and saved analysis workspaces.
- Polished product UI and workspace flows around the existing file-first Candidate Portfolio Factory, current-vs-policy workflow, comparison, and decision package artifacts.
- More deliberately designed client-facing report packages beyond the current file-first summary/PDF-style surfaces.
- Advanced UX modules around the implemented file-first V1 artifacts.

## Main Pipeline

Portfolio-first is the binding product workflow contract:

```text
analysis_subject
-> Portfolio X-Ray diagnostics
-> stress / factor / macro diagnostics
-> candidate generation
-> comparison and decision artifacts
```

Runtime migration to that order is in progress under the active
[Portfolio-First Transition Plan](docs/exec_plans/2026-05-18_portfolio_first_transition_plan.md).
The portfolio-first orchestrator is:

```bash
python run_portfolio_review.py
python run_portfolio_review.py --dry-run
python run_portfolio_review.py --skip-candidates
python run_portfolio_review.py --candidate-profile core_benchmarks
python run_portfolio_review.py --candidates equal_weight,risk_parity
```

`run_portfolio_review.py` materializes `{output_dir_final}/analysis_subject/` first, then runs
the non-policy candidate factory and comparison path. It does not call `run_optimization.py` in the
default path. Subject-centered comparison and decision wording continue under later transition
sessions.

The existing legacy policy flow remains callable for compatibility and historical policy runs:

```bash
python run_optimization.py
python run_report.py
```

Optional single command for the legacy file-first MVP policy path:

```bash
python run_mvp_workflow.py --workflow policy-only
python run_mvp_workflow.py --workflow policy-current
python run_mvp_workflow.py --workflow full-decision
```

See [docs/operational_runbook.md](docs/operational_runbook.md) for stage definitions and manual step equivalents.

Legacy policy optimization options:

```bash
python run_optimization.py --no-cache
python run_optimization.py --write-config
python run_optimization.py --config PATH
python run_optimization.py --profile NAME
python run_optimization.py --no-report
```

Report options:

```bash
python run_report.py --no-cache
python run_report.py --clear-cache
python run_report.py --backtest-mode dynamic_nan_safe
python run_report.py --materialize-analysis-subject
```

`run_optimization.py` reads config, loads market data, builds optimizer inputs, runs the legacy
policy optimizer, applies release checks, and writes optimized weights and run metadata. It remains
callable for compatibility, but it is not the default starting point for the portfolio-first
workflow. `run_report.py` reads fixed weights and produces metrics, diagnostics, stress reports,
scenario libraries, commentary, snapshots, and report artifacts.
`run_report.py --materialize-analysis-subject` writes the resolved portfolio-first subject to
`{output_dir_final}/analysis_subject/` so candidate generation can happen only after subject
diagnostics exist.

## Candidate Portfolios

Candidate portfolios are comparison hypotheses, not automatic replacements for the diagnosed
`analysis_subject`. The legacy policy optimizer is not a default portfolio-first candidate unless a
future accepted spec reactivates it for that role.

Common candidate commands:

```bash
python run_candidate_factory.py --then-compare
python run_equal_weight.py
python run_equal_weight_by_asset_class.py
python run_risk_parity.py
python run_risk_budget_by_asset_class.py
python run_risk_budget_by_asset.py
python run_hierarchical_risk_parity.py
python run_minimum_variance.py
python run_minimum_variance_uncapped.py
python run_minimum_variance_advanced.py
python run_maximum_diversification.py
python run_maximum_diversification_unconstrained.py
python run_minimum_cvar_uncapped.py
python run_minimum_cvar_constrained.py
python run_robust_mv_lambda_calibration.py
python run_robust_mean_variance_uncapped.py
python run_robust_mean_variance_constrained.py
python run_robust_scenario_optimization.py
python run_robust_scenario_portfolio_report.py
```

Use `run_candidate_factory.py` to orchestrate multiple candidate builders before comparison. Details live in [docs/specs/candidate_factory_spec.md](docs/specs/candidate_factory_spec.md), [docs/specs/candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md), [docs/specs/robust_mv_spec.md](docs/specs/robust_mv_spec.md), and [docs/specs/robust_scenario_optimization_spec.md](docs/specs/robust_scenario_optimization_spec.md).

## Key Inputs

| File | Purpose |
| --- | --- |
| `config.yml` | Active local config: tickers, investor currency, benchmark, client profile, targets, windows, cash policy, return frequency, output paths, and feature settings. |
| `config.yml.example` | Reference config template. |
| `config/client_profiles.yml` | Client risk profile defaults. |
| `config/etf_universe.yml` | ETF taxonomy source of truth for annotation and validation. |
| `config/stock_universe.yml` | Stock taxonomy source of truth for stock metadata validation. |
| `config/historical_stress_proxy_map.yml` | Historical stress fallback proxy map and thresholds. |
| `assets.yml` | Optional asset metadata. |

Portfolio-first input semantics live in
[docs/specs/portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md):
`analysis_subject` is the portfolio diagnosed before candidates, with supported types
`current_portfolio`, `model_portfolio`, and `universe_baseline`.

Analysis setup and legacy input mode details live in
[docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md). Default
compatibility `analysis_mode` is `optimize_from_universe`; use
`analysis_mode: analyze_current_weights` plus `current_weights` to diagnose an existing
fixed-weight portfolio with `run_report.py`. New portfolio-first configs may use explicit
`analysis_subject` with type `current_portfolio`, `model_portfolio`, or `universe_baseline`.

Data rules are governed by [DATA.md](DATA.md) and [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md).

## Outputs

Generated outputs are not source files unless a task explicitly targets generated artifacts. Use [OUTPUTS.md](OUTPUTS.md) as the root output/reporting map.

Common locations:

- `Main portfolio/`
- `results_csv/`
- `output/`
- `cache/`
- candidate portfolio folders
- `pdf files/`
- `pdf_md_sources/`

Common artifacts:

- `portfolio_weights.yml`
- `run_result.json`
- `run_metadata.json`
- `stress_report.json`
- `portfolio_xray.json`
- `candidate_comparison.json`
- `robustness_scorecard.json`
- `portfolio_health_score.json`
- `selection_decision.json`
- `tradeoff_explanation.json`
- `model_risk_diagnostics.json`
- `assumption_sensitivity.json`
- `pareto_dominance.json`
- `regret_analysis.json`
- `action_plan.json`
- `current_vs_policy_status.json`
- `monitoring_diff.json`
- `decision_journal.json`
- `decision_package_summary.json`
- `candidate_factory_run.json`
- `scenario_library.json`
- `scenario_library_normalized.json`
- `commentary.txt`
- `stress_commentary.txt`
- CSV diagnostics
- HTML and PDF-style artifacts where configured

`portfolio_xray.json` is diagnostic-only. It summarizes existing report diagnostics and does not optimize, change weights, change mandate gates, change stress pass/fail status, or select portfolios.

Detailed report/output behavior lives in [docs/specs/reporting_outputs_spec.md](docs/specs/reporting_outputs_spec.md).

## Repository Map

| Path | Purpose |
| --- | --- |
| `RULES.md` | High-level project principles and source-of-truth map. |
| `WORKFLOW.md` | Task workflow from request to implementation, verification, docs sync, project memory, and commit. |
| `SPEC.md` | Current implementation contract and detailed spec index. |
| `OUTPUTS.md` | Root output/reporting map. |
| `DATA.md` | Data-layer map and data documentation sync triggers. |
| `TESTING.md` | Verification framework and test/check selection. |
| `GLOSSARY.md` | Shared terminology. |
| `KNOWN_ISSUES.md` | Active issues, model limitations, testing gaps, and technical debt. |
| `DECISIONS.md` | Key decisions, rationale, alternatives, assumptions, and consequences. |
| `CHANGELOG.md` | Concise history of meaningful project changes. |
| `ARCHITECTURE.md` | Architecture map, module layers, flows, inputs, outputs, and boundaries. |
| `PRODUCT.md` | Target product flow, UX behavior, screens, and product modules. |
| `docs/ROADMAP.md` | Ordered development roadmap, backlog phases, prerequisites, and audit-to-session mapping. |
| `BUSINESS_VISION.md` | Business vision, users, value proposition, and long-term direction. |
| `DESIGN.md` | UI, dashboard, HTML, and visual design rules. |
| `PLANS.md` | ExecPlan protocol for large/risky work. |
| `docs/specs/` | Detailed behavior specs. |
| `docs/exec_plans/` | Checked-in ExecPlans. |
| `tests/` | Pytest coverage. |

## Installation

```bash
pip install -r requirements.txt
```

Python dependencies include pandas, numpy, scipy, scikit-learn, yfinance, pandas-datareader, PyYAML / ruamel.yaml, matplotlib, and pytest.

## Verification

Use [TESTING.md](TESTING.md) to choose the right verification level.

Full test suite:

```bash
python -m pytest
```

For focused changes, run the narrowest reliable pytest file first, then broaden when the change touches portfolio math, optimizer behavior, data alignment, config schema, stress logic, report exports, or generated artifact contracts.

## Documentation Sources Of Truth

Start with [RULES.md](RULES.md), then use [SPEC.md](SPEC.md) as the implementation entry point.

| Area | Source |
| --- | --- |
| Project principles and source-of-truth map | [RULES.md](RULES.md) |
| Task workflow | [WORKFLOW.md](WORKFLOW.md) |
| Current implementation contract | [SPEC.md](SPEC.md) |
| Portfolio-first review workflow and `analysis_subject` | [docs/specs/portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md) |
| Architecture and module boundaries | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Data layer | [DATA.md](DATA.md) |
| Outputs and generated artifacts | [OUTPUTS.md](OUTPUTS.md) |
| Testing and verification | [TESTING.md](TESTING.md) |
| Shared terminology | [GLOSSARY.md](GLOSSARY.md) |
| Known issues and debt | [KNOWN_ISSUES.md](KNOWN_ISSUES.md) |
| Decisions and rationale | [DECISIONS.md](DECISIONS.md) |
| Change history | [CHANGELOG.md](CHANGELOG.md) |
| Detailed specs | [docs/specs/README.md](docs/specs/README.md) |
| Roadmap and backlog | [docs/ROADMAP.md](docs/ROADMAP.md) |
| Input and assumptions | [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md) |
| Product direction | [PRODUCT.md](PRODUCT.md), [BUSINESS_VISION.md](BUSINESS_VISION.md), [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) |
| Planning protocol | [PLANS.md](PLANS.md) |
| Design rules | [DESIGN.md](DESIGN.md) |

## Contributor Rules

- Do not invent formulas when a spec exists.
- Do not treat product concept docs as automatic implementation changes.
- Keep production weights generated by the optimizer or approved post-optimization protocols.
- Preserve diagnostic-only boundaries unless a canonical spec changes them.
- Update docs when behavior, interfaces, outputs, commands, workflows, terminology, or source-of-truth ownership changes.
- Use `WORKFLOW.md` for the task process and `TESTING.md` for verification.
