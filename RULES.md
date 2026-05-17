# RULES.md

This file is the high-level rule map for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It defines the project-wide principles, boundaries, and required working discipline. Detailed formulas, scenario definitions, optimizer rules, data handling, UI rules, and agent workflow rules live in their canonical documents listed below. Do not duplicate those details here.

## Project Principles

- The product is a portfolio decision-support and reporting system, not a black-box allocator. It must make assumptions, inputs, diagnostics, constraints, and outputs visible enough for a user to evaluate.
- The current implementation is report-first and CLI/file-driven. Target product concepts do not change current behavior until the relevant implementation specs and code are updated.
- Product concept documents can guide direction, but they do not override `SPEC.md`, canonical formulas, stress scenarios, data rules, optimizer policy, release logic, or current code behavior.
- Optimized weights are system outputs. Manual post-optimization tilt is allowed only through the specified View After Optimization workflow.

## Rule Discipline

- Assumptions must be explicit and visible in code, reports, configs, or documentation.
- Diagnostics are not production policy unless a canonical spec says they are binding.
- Do not invent formulas, estimators, scenarios, constraints, statuses, or data rules when a spec exists.
- Before changing formulas, portfolio logic, data flow, stress behavior, optimizer policy, report outputs, interfaces, or product-facing workflows, check the relevant source of truth first.
- Generated outputs are not source files unless the task explicitly targets generated artifacts.
- Keep changes scoped to the requested behavior and the owning module or document.

## Change Requirements

- Meaningful code changes require relevant documentation sync.
- Meaningful code changes require verification with the narrowest reliable test, CLI command, script, or reproducible manual check, selected using [TESTING.md](TESTING.md).
- If a change affects behavior, logic, formulas, configs, workflows, outputs, interfaces, or shared helpers, update the canonical documentation that governs that area.
- Do not leave stale references to renamed or removed functions, configs, metrics, files, commands, outputs, workflows, or documents.
- Keep active known issues visible in [KNOWN_ISSUES.md](KNOWN_ISSUES.md) until they are fixed, verified, and documented.
- Record key decisions and rejected alternatives in [DECISIONS.md](DECISIONS.md) when project direction, methodology, or boundaries are chosen.
- Record meaningful completed changes in [CHANGELOG.md](CHANGELOG.md) with short entries, not long implementation notes.
- Report any uncertainty, assumption, unverified area, or blocker explicitly.

## Source Of Truth Map

| Area | Governing document |
| --- | --- |
| Current implementation contract, expected behavior, output contracts, and canonical spec index | [SPEC.md](SPEC.md) |
| Task workflow from request to implementation, verification, documentation sync, project memory, and commit | [WORKFLOW.md](WORKFLOW.md) |
| Analysis setup, input modes, current weights, mandate inputs, and calculation assumptions | [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md) |
| Generated outputs, report artifacts, output folders, formats, and generated-vs-source boundaries | [OUTPUTS.md](OUTPUTS.md) |
| Shared project terminology and short definitions | [GLOSSARY.md](GLOSSARY.md) |
| Product overview, setup, commands, documentation map, and high-level workflows | [README.md](README.md) |
| Data-layer map: sources, structures, pipeline, quality rules, and documentation sync triggers | [DATA.md](DATA.md) |
| Testing and verification framework, test selection, CLI smoke checks, artifact checks, and Markdown link checks | [TESTING.md](TESTING.md) |
| Known active issues, model limitations, testing gaps, technical debt, and weak spots | [KNOWN_ISSUES.md](KNOWN_ISSUES.md) |
| Key project decisions, rationale, rejected alternatives, assumptions, and consequences | [DECISIONS.md](DECISIONS.md) |
| Concise history of meaningful project changes | [CHANGELOG.md](CHANGELOG.md) |
| Product vision, target users, value proposition, and long-term direction | [BUSINESS_VISION.md](BUSINESS_VISION.md) |
| Target product flow, UX behavior, screens, and product modules | [PRODUCT.md](PRODUCT.md) |
| Architecture map, module boundaries, execution flow, and target architecture areas | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Living diagnostic product blueprint and target architecture ideas; non-binding until promoted to canonical specs | [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) |
| Metric formulas, estimators, returns, FX, windows, covariance, beta, drawdown, risk-free, rounding, and portfolio analytics rules | [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md) |
| Portfolio construction, optimizer behavior, ProLiquidity, mandate gate, RC_vol role, and policy optimizer boundaries | [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md) |
| Data policy, NaN handling, young ETF handling, return panels, and backtest handling | [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md) |
| Stress scenarios, stress diagnostics, factor diagnostics, macro/regime diagnostics, scenario analytics, and warning/failure codes | [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md) |
| Feasibility rules, weight constraints, caps, floors, and constraint diagnostics | [docs/specs/feasibility_constraints_spec.md](docs/specs/feasibility_constraints_spec.md) |
| View After Optimization tactical tilt protocol | [docs/specs/view_after_optimization_spec.md](docs/specs/view_after_optimization_spec.md) |
| Production workflow, release statuses, blocking rules, and operational states | [docs/specs/production_workflow.md](docs/specs/production_workflow.md) |
| ETF taxonomy schema, enums, canonical tickers, duplicate policy, and diagnostics statuses | [docs/specs/etf_universe_spec.md](docs/specs/etf_universe_spec.md) |
| Stock taxonomy schema, snapshot header requirements, and CLI workflow | [docs/specs/stock_universe_spec.md](docs/specs/stock_universe_spec.md) |
| Agent operating rules, documentation sync rules, generated-output policy, and editing guidance | [AGENTS.md](AGENTS.md) |
| Planning process and ExecPlan format for complex work | [PLANS.md](PLANS.md) |
| UI, dashboard, generated HTML, and visual design rules | [DESIGN.md](DESIGN.md) |

## Boundary Rule

When documents disagree, use the most specific canonical source for the affected behavior. `SPEC.md` is the implementation entry point, but detailed technical documents govern their own domains. Product concept documents describe direction only; they do not change current implementation contracts by themselves.
