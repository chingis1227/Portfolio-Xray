---
description:
alwaysApply: true
---

# AGENTS.md

This file defines how agents work in this repository. It is not the place for long formulas, scenario definitions, verification matrices, or module-specific implementation contracts. Detailed behavior lives in [SPEC.md](SPEC.md), [TESTING.md](TESTING.md), and [docs/specs/](docs/specs/README.md).

Update this file only when agent workflow, documentation sync rules, source-of-truth order, generated-output policy, ExecPlan policy, verification source-of-truth routing, or operating instructions change.

## Project Summary

Portfolio X-Ray & Optimization Terminal / Portfolio MRI is a Python portfolio decision-support and reporting system. It diagnoses portfolio exposures, hidden risks, stress behavior, candidate allocations, robustness checks, and report artifacts.

The current implementation is report-first and CLI/file-driven. Full UI, formal Selection Engine, Portfolio Health Score, Monitoring, and Decision Journal remain target/TBD areas until separately specified and implemented.

Main flow:

1. `python run_optimization.py`
2. `python run_report.py`

Weights are optimizer outputs, not manual user inputs. Manual post-optimization tilt is allowed only through View After Optimization.

Product concept documents guide direction but do not override `SPEC.md`, canonical formulas, stress scenarios, policy logic, data rules, output contracts, or current code behavior.

## Stack

- Python
- pandas, numpy, scipy, scikit-learn
- yfinance, pandas-datareader
- PyYAML / ruamel.yaml
- matplotlib
- pytest

Install dependencies:

```bash
pip install -r requirements.txt
```

## Main Commands

Run tests:

```bash
python -m pytest
```

Use [TESTING.md](TESTING.md) to choose focused tests, CLI smoke runs, artifact checks, and Markdown link checks.

Run optimization:

```bash
python run_optimization.py [--no-cache] [--write-config] [--config PATH] [--profile NAME] [--no-report]
```

Run report:

```bash
python run_report.py [--no-cache] [--clear-cache] [--backtest-mode dynamic_nan_safe]
```

Run post-optimization tilt:

```bash
python run_view_after_optimization.py --asset VOO --delta 2
```

Candidate and robust portfolio commands are indexed in [docs/specs/candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md), [docs/specs/robust_mv_spec.md](docs/specs/robust_mv_spec.md), and [docs/specs/robust_scenario_optimization_spec.md](docs/specs/robust_scenario_optimization_spec.md).

## Source Of Truth Order

Before changing current behavior, formulas, portfolio logic, data flow, scenarios, outputs, or product-facing workflows, check the relevant source of truth first:

1. [RULES.md](RULES.md) for high-level project principles and source-of-truth ownership.
2. [SPEC.md](SPEC.md) for the current implementation contract and status matrix.
3. [DATA.md](DATA.md) for data sources, data structures, data pipeline, and data quality rules.
4. [TESTING.md](TESTING.md) for verification strategy, test selection, CLI smoke checks, artifact checks, and Markdown link checks.
5. [docs/specs/](docs/specs/README.md) for detailed module-specific behavior.
6. [README.md](README.md) for setup, commands, and user-facing documentation map.
7. [ARCHITECTURE.md](ARCHITECTURE.md) for module boundaries and execution flow.
8. Product concept documents, including [BUSINESS_VISION.md](BUSINESS_VISION.md), [PRODUCT.md](PRODUCT.md), and [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md), for target direction only.

Detailed specs:

- [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md) governs metric formulas, estimators, windows, returns, FX, beta, RC_vol, and rounding.
- [DATA.md](DATA.md) governs the high-level data-layer map, data sources, expected structures, quality rules, and data documentation sync triggers.
- [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md) governs optimizer policy and portfolio construction boundaries.
- [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md) governs NaN handling, young ETFs, return panels, and backtest handling.
- [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md) governs stress scenarios and stress diagnostics.
- [docs/specs/feasibility_constraints_spec.md](docs/specs/feasibility_constraints_spec.md) governs feasibility and weight constraints.
- [docs/specs/production_workflow.md](docs/specs/production_workflow.md) governs release statuses and blocking rules.
- [TESTING.md](TESTING.md) governs the quality and verification framework.

Do not invent formulas, estimators, scenarios, constraints, statuses, or data rules when a spec exists.

## Core Agent Rules

- Keep changes scoped to the requested behavior and the owning module or document.
- Prefer existing helpers and established repo patterns over new parallel implementations.
- Treat diagnostics as non-binding unless a canonical spec says otherwise.
- Do not manually require final weights in `config.yml`; optimization writes `portfolio_weights.yml` and `run_result.json`.
- ETF and stock taxonomy are annotation-only in V1 unless a canonical spec changes that boundary.
- Round only at final export/report stage when governed by metric specs.
- Preserve full precision during calculations.
- Do not treat generated outputs as source unless the task explicitly targets generated artifacts.

## Documentation Sync

Documentation sync is blocking for every meaningful code change.

Update the owning documentation when behavior, logic, formulas, configs, workflows, outputs, interfaces, or shared helpers change:

- Update [AGENTS.md](AGENTS.md) only for agent workflow, verification source-of-truth routing, source-of-truth order, or operating instructions.
- Update [SPEC.md](SPEC.md) for general implementation contract, workflows, inputs/outputs, behavior rules, edge cases, or status matrix changes.
- Update [DATA.md](DATA.md) when data sources, structures, data pipeline, NaN handling, FX logic, benchmark logic, risk-free inputs, factor/macro inputs, config fields, validation rules, fallback behavior, or data quality expectations change.
- Update [TESTING.md](TESTING.md) when verification strategy, required checks, test scope matrix, CLI smoke expectations, artifact checks, or quality gates change.
- Update `docs/specs/*.md` when detailed behavior of a specific module changes.
- Update [README.md](README.md) when setup, commands, project structure, outputs, or user-facing workflows change.
- Update [ARCHITECTURE.md](ARCHITECTURE.md) when module boundaries, execution flow, or architecture changes.
- Update [RULES.md](RULES.md) only when high-level project principles or source-of-truth ownership changes.

Verify no stale references remain to renamed or removed functions, configs, metrics, files, commands, outputs, workflows, or documents.

## Verification Loop

Follow [TESTING.md](TESTING.md) for the verification matrix, focused test selection, CLI smoke runs, artifact checks, and Markdown link checks.

After a meaningful code change, run the narrowest reliable verification first, broaden when the changed risk warrants it, and report any unverified area with the reason and blocker. If a test fails because of the change, fix the root cause and rerun.

## ExecPlans

For new complex tasks, large changes, or refactors, follow [PLANS.md](PLANS.md) before implementation.

- Read [PLANS.md](PLANS.md) fully before authoring or changing an ExecPlan.
- Create or update checked-in ExecPlans under `docs/exec_plans/`.
- Keep ExecPlans as living documents: update `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` as work proceeds.
- Small, localized fixes do not need a separate ExecPlan unless the user asks for one.

## Generated Outputs

Do not treat these as source unless the task explicitly targets generated artifacts:

- `cache/`
- `output/`
- `results_csv/`
- `Main portfolio/`
- `equal-weight portfolio/`
- `risk parity portfolio/`
- portfolio variant output folders
- `portfolio_weights.yml`
- `__pycache__/`
- `.pytest_cache/`
- generated PDFs and generated markdown report sources

## Editing Guidance

- Use `rg` or `rg --files` for searches when available.
- Use `apply_patch` for manual file edits.
- Do not revert user changes or unrelated dirty working-tree changes.
- Do not use destructive git commands unless explicitly requested.
- Prefer non-interactive git commands.
- Keep final responses concise and include changed files, verification performed, and any unverified area.
