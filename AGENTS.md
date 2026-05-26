---
description:
alwaysApply: true
---

# AGENTS.md

This file defines agent operating rules for this repository. It is intentionally compact: detailed workflow, implementation contracts, verification matrices, output contracts, issue logs, decision logs, terminology, and module-specific specs live in the linked source-of-truth documents.

Update this file only when agent-specific operating instructions, source-of-truth routing, generated-output policy, or editing guidance changes.

## Project Summary

Portfolio MRI / Portfolio X-Ray is being reset around the **“ДИАГНОСТИКА 2” canonical product truth**. The current product is a Python portfolio diagnostics and investment decision-support system that is diagnosis-first, current-portfolio-first, and not optimizer-first.

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

The current implementation is still CLI/file-driven and partly carries older optimizer/report/scorecard-heavy infrastructure. Treat that older infrastructure as support code unless a task explicitly targets it.

Do **not** describe these as the current Core MVP product flow: Portfolio Health Score, Robustness Scorecard, Macro Dashboard / Macro Overlay, full multi-candidate ranking/arena, Assumption Sensitivity, Pareto/Dominance, Regret Analysis, Model Risk Diagnostics, full Action Plan / Rebalancing Advisor, full Decision Journal, advanced monitoring, Crisis Replay UI, What Happens If simulator UI, Client-Fit Check, Asset X-Ray, Max Sharpe, tax-aware optimization, turnover-aware optimizer objective, tactical tilt, full custom constraints UI, multi-client workspace, or polished PDF report product.

If those capabilities exist in code or generated outputs, classify them as `Advanced`, `Backend evidence`, `Technical artifact`, `Legacy`, `Generated support artifact`, or `Future/backlog`; do not treat existence in code as current product truth.

Main portfolio-first flow:

1. `python run_portfolio_review.py` for current portfolio diagnosis / product-bundle generation.
2. inspect `{output_dir_final}/analysis_subject/` before interpreting candidate or decision artifacts
3. for the current product demo path, prefer an explicit one-hypothesis run such as `python run_portfolio_review.py --candidates equal_weight`

Product-flow operator map (read order, six-file bundle paths, demo vs core commands, anti-patterns):
[docs/product_flow_operator_guide.md](docs/product_flow_operator_guide.md).

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

Product concept documents guide direction but do not override `SPEC.md`, canonical formulas, stress scenarios, policy logic, data rules, output contracts, or current code behavior. The current canonical product direction is “ДИАГНОСТИКА 2”; “ДИАГНОСТИКА 2 НА ПОТОМ” features are backlog/advanced/later unless explicitly promoted by specs and implementation.
Documentation migration records and archived legacy docs are retained for traceability only. They do not override current implementation contracts, canonical specs, or code.

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
python run_portfolio_review.py [--mode core|full] [--dry-run] [--skip-candidates] [--candidate-profile PROFILE] [--candidates ID,ID,...] [--no-parallel-lightweight-reports] [--with-pdf] [--legacy-full-pdf]
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
- [DOCUMENTATION_MIGRATION_PLAN.md](DOCUMENTATION_MIGRATION_PLAN.md), [DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md](DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md), and `docs/archive/documentation_migration_2026_05_25/` for documentation migration traceability only; verify current-implementation claims against `SPEC.md`, detailed specs, and code before treating them as implemented.

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
- Do not demote or delete existing implementation capabilities only because they are absent from a
  product concept draft; classify them as `Preserve`, `Advanced`, `Legacy`, or `Requires Review`
  unless a canonical spec or explicit task says otherwise.

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
