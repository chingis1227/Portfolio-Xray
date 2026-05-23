---
description:
alwaysApply: true
---

# AGENTS.md

This file defines agent operating rules for this repository. It is intentionally compact: detailed workflow, implementation contracts, verification matrices, output contracts, issue logs, decision logs, terminology, and module-specific specs live in the linked source-of-truth documents.

Update this file only when agent-specific operating instructions, source-of-truth routing, generated-output policy, or editing guidance changes.

## Project Summary

Portfolio X-Ray & Optimization Terminal / Portfolio MRI is a Python portfolio decision-support and reporting system. It diagnoses portfolio exposures, hidden risks, stress behavior, candidate allocations, robustness checks, decision artifacts, and report outputs.

The current implementation is report-first and CLI/file-driven. V1 decision artifacts are implemented as generated files: candidate comparison, robustness scorecard, Portfolio Health Score, Selection/No-Trade decision, Action Plan, Monitoring / What Changed, and generated Decision Journal. Full UI, saved analysis workspaces, richer report/PDF decision packaging, and advanced product workflows remain future scope until separately specified and implemented.

Main portfolio-first flow:

1. `python run_portfolio_review.py`
2. inspect `{output_dir_final}/analysis_subject/` before interpreting candidate or decision artifacts

Legacy policy compatibility flow:

1. `python run_optimization.py`
2. `python run_report.py`

Optional legacy MVP orchestration (thin wrapper; same policy entrypoints):

```bash
python run_mvp_workflow.py [--workflow policy-only|policy-current|full-decision|diagnosis-only]
```

Legacy policy weights are optimizer outputs, not manual user inputs. User-supplied
`analysis_subject` weights are allowed for `current_portfolio` and `model_portfolio` diagnostics.
Manual post-optimization tilt is allowed only through View After Optimization.

Product concept documents guide direction but do not override `SPEC.md`, canonical formulas, stress scenarios, policy logic, data rules, output contracts, or current code behavior.

## Main Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest
```

Run portfolio-first review:

```bash
python run_portfolio_review.py [--mode core|full] [--dry-run] [--skip-candidates] [--candidate-profile PROFILE] [--candidates ID,ID,...] [--with-pdf] [--legacy-full-pdf]
```

Default output profile is `site_api` (JSON/cache only); a routine review **does not** refresh
`pdf files/`. Use `--with-pdf` for portfolio-first decision PDFs (`analysis_subject` + decision
package). Use `--legacy-full-pdf` to regenerate the full legacy variant PDF suite.

Run legacy policy optimization:

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

Run candidate factory (orchestrate benchmark/optimizer builders before compare):

```bash
python run_candidate_factory.py [--profile default_v1] [--candidates ID,ID,...] [--force] [--fail-fast] [--then-compare]
```

Candidate and robust portfolio commands are indexed in [docs/specs/candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md), [docs/specs/candidate_factory_spec.md](docs/specs/candidate_factory_spec.md), [docs/specs/robust_mv_spec.md](docs/specs/robust_mv_spec.md), and [docs/specs/robust_scenario_optimization_spec.md](docs/specs/robust_scenario_optimization_spec.md).

## Source Of Truth

Before changing behavior, follow [WORKFLOW.md](WORKFLOW.md) and start from [RULES.md](RULES.md).

Key sources:

- [SPEC.md](SPEC.md) for the current implementation contract.
- [DATA.md](DATA.md) for data sources, pipeline, structures, and quality rules.
- [OUTPUTS.md](OUTPUTS.md) for generated outputs, folders, formats, and generated-vs-source boundaries.
- [TESTING.md](TESTING.md) for verification strategy and test selection.
- [GLOSSARY.md](GLOSSARY.md) for shared terminology.
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for active issues and technical debt.
- [DECISIONS.md](DECISIONS.md) for key decisions and rationale.
- [CHANGELOG.md](CHANGELOG.md) for concise completed-change history.
- [docs/audits/README.md](docs/audits/README.md) for the audit register and audit-to-plan links.
- [docs/exec_plans/README.md](docs/exec_plans/README.md) for the plan register and current active-plan pointer.
- [docs/specs/](docs/specs/README.md) for detailed module-specific behavior.
- [PLANS.md](PLANS.md) for ExecPlan requirements on large or risky work.
- [DESIGN.md](DESIGN.md) for UI, dashboard, generated HTML, and visual-interface work.

Do not invent formulas, estimators, scenarios, constraints, statuses, or data rules when a canonical spec exists.

## Core Agent Rules

- In chat with the user, communicate in Russian by default and as with a non-professional developer: explain ongoing work in simple terms, point out misunderstandings or risky assumptions clearly and respectfully, and ask necessary project questions in plain language without unexplained technical jargon. This applies to assistant-user communication only; source code, product copy, generated reports, project documentation, and other in-project artifacts remain in English unless explicitly requested otherwise.
- Keep changes scoped to the requested behavior and owning files.
- Prefer existing helpers and repo patterns over new parallel implementations.
- Treat diagnostics as non-binding unless a canonical spec says otherwise.
- Do not manually require final weights in `config.yml`; optimization writes `portfolio_weights.yml` and `run_result.json`.
- ETF and stock taxonomy are annotation-only in V1 unless a canonical spec changes that boundary.
- Round only at final export/report stage when governed by metric specs.
- Preserve full precision during calculations.
- Do not treat generated outputs as source unless the task explicitly targets generated artifacts; use [OUTPUTS.md](OUTPUTS.md) for output boundaries.

## Documentation And Verification

Documentation sync is required for meaningful code changes. Use [WORKFLOW.md](WORKFLOW.md) to decide which documents to update and [TESTING.md](TESTING.md) to decide which checks to run.

After meaningful changes:

- update owning docs when behavior, logic, formulas, configs, workflows, outputs, interfaces, or shared helpers change;
- verify no stale references remain after renames, removals, or moved documents;
- run the narrowest reliable verification first and broaden when risk warrants it;
- report any unverified area with the reason and blocker.

## ExecPlans

For new complex tasks, large changes, or refactors, follow [PLANS.md](PLANS.md) before implementation.

- Read [PLANS.md](PLANS.md) fully before authoring or changing an ExecPlan.
- Create or update checked-in ExecPlans under `docs/exec_plans/`.
- Keep ExecPlans as living documents: update `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` as work proceeds.
- Small, localized fixes do not need a separate ExecPlan unless the user asks for one.

## Generated Outputs

Do not treat generated artifacts as source unless the task explicitly targets them.

Common generated paths include:

- `cache/`
- `output/`
- `results_csv/`
- `Main portfolio/`
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
