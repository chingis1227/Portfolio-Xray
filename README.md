# Portfolio MRI / Portfolio X-Ray

Portfolio MRI / Portfolio X-Ray is a Python portfolio diagnostics and investment decision-support system. The **canonical current product truth is “ДИАГНОСТИКА 2”**: diagnosis-first, current-portfolio-first, decision-support oriented, and not optimizer-first.

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

Its purpose is diagnosis before action, not black-box allocation. The system helps a user understand the current portfolio first, identify problems, test a selected candidate hypothesis when useful, compare trade-offs, and reach a defensible verdict.

The implementation remains CLI/file-driven and still contains older optimizer/report/scorecard-heavy infrastructure. That infrastructure is support code unless explicitly promoted by current specs. In particular, Portfolio Health Score, Robustness Scorecard, Macro Dashboard / Macro Overlay, full multi-candidate ranking/arena, Assumption Sensitivity, Pareto / Dominance, Regret Analysis, Model Risk Diagnostics, full Action Plan / Rebalancing Advisor, full Decision Journal, advanced monitoring, Crisis Replay UI, What Happens If UI, Client-Fit Check, Asset X-Ray, Max Sharpe, tax-aware optimization, turnover-aware optimizer objectives, tactical tilt, full custom constraints UI, multi-client workspace, and polished PDF report product are **advanced / backend / legacy / future-backlog**, not the current Core MVP product flow.

Product concept documents describe target direction only. Current behavior is governed by [SPEC.md](SPEC.md), [RULES.md](RULES.md), [DATA.md](DATA.md), [OUTPUTS.md](OUTPUTS.md), and detailed specs under [docs/specs/](docs/specs/README.md). Documentation migration records and archived legacy copies are retained for traceability; active behavior remains governed by the canonical specs and code.

Default execution is site/API-first: JSON contracts and cache are written for backend/UI
consumption, while CSV/TXT/HTML/PNG/PDF/Markdown/CSS presentation artifacts are disabled unless an
explicit export/report profile is selected. Default `run_portfolio_review.py` / `site_api` runs do
**not** refresh `pdf files/` — use `--with-pdf`, `--legacy-full-pdf`, or an explicit export profile
when client PDFs must match the latest JSON.

Runtime note: today `run_portfolio_review.py` still has a `--mode core` backend batch path
(`core_fast`, six candidates). That is current code behavior, but it is not the canonical product
story. For the “ДИАГНОСТИКА 2” product shape, prefer diagnosis-first output and explicit
one-hypothesis runs such as `python run_portfolio_review.py --candidates equal_weight`. Full menu
(`default_v1`, 16 builders) is advanced/research only. See [OUTPUTS.md](OUTPUTS.md) for the full
command matrix.

| Use case | Command | Factory profile |
| --- | --- | --- |
| Portfolio diagnosis / site/API backend run | `python run_portfolio_review.py` or `--mode core` | current code: `core_fast` backend batch |
| **Canonical product demo** (one selected hypothesis) | `python run_portfolio_review.py --candidates equal_weight` | explicit candidate id |
| Full advanced/research review (16 builders) | `python run_portfolio_review.py --mode full` | `default_v1` |
| Full menu factory + compare (standalone advanced/research) | `python run_candidate_factory.py --profile default_v1 --then-compare` | `default_v1` |
| Compare / decision package only | `python run_compare_variants.py` | — |
| Legacy policy optimize only (no report) | `python run_optimization.py` | — |
| Legacy policy + site/API report | `python run_optimization.py --with-report` | — |
| Full report exports | `python run_report.py --output-profile full_report` | — |
| Legacy export + PDF sidecars | `python run_report.py --output-profile legacy_export` | — |
| Portfolio-first PDF export | `python run_portfolio_review.py --with-pdf` | same as mode |
| Full legacy PDF suite | `python run_portfolio_review.py --legacy-full-pdf` or `python rebuild_pdf_reports.py` | — |
| Benchmark/timing run | `python run_candidate_factory.py --profile default_v1 --then-compare --parallel-lightweight-reports` | `default_v1` |

Each site/API run writes `output_manifest.json` under `output_dir_final` (machine-readable index of
JSON paths, disabled presentation classes, and per-type artifact counts). Cache under `cache/` is
internal; CSV/TXT/HTML/PNG/PDF/Markdown/CSS are export-only unless an explicit profile or PDF flag
is used. See [OUTPUTS.md](OUTPUTS.md) for the full command matrix and artifact policy.

## Current Scope

Current Core MVP product layer:

- Canonical portfolio-first workflow contract through `analysis_subject`; runtime transition is active
  and governed by [portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md).
- Portfolio-first CLI orchestration through `run_portfolio_review.py`.
- Additive diagnosis-first product-bundle artifacts and adapters: Problem Classification (`problem_classification.json`), Candidate Launchpad (`candidate_launchpad.json`), Current-vs-Candidate (`current_vs_candidate.json`), Decision Verdict (`decision_verdict.json`), AI Commentary grounding context (`ai_commentary_context.json`), and light What Changed summary (`what_changed_summary.json`). These are the current “ДИАГНОСТИКА 2” product-facing files where implemented.
- JSON generated artifacts by default; CSV, HTML, TXT, PNG, and PDF-style artifacts remain explicit export/report outputs.

Implemented backend / advanced / legacy support:

- Legacy CLI/file-driven policy optimization compatibility through `run_optimization.py`.
- Portfolio reporting and diagnostics through `run_report.py`.
- Input and Assumptions Layer V1: Core MVP needs only `tickers`, `current_weights` or `weights`, and `investor_currency` in `config.yml` (USD market defaults injected; optional real-cash labels such as `Cash USD`; legacy mandate/profile fields remain for optimizer paths). See [input_assumptions_spec.md](docs/specs/input_assumptions_spec.md).
- Portfolio metrics, dynamic NaN-safe backtesting, and risk contribution diagnostics.
- Stress diagnostics, stress commentary, factor diagnostics, macro/regime diagnostics, PCA, scenario libraries, and robustness diagnostics.
- Benchmark/candidate portfolios including Equal Weight, Risk Parity, HRP, Minimum Variance, Maximum Diversification, Minimum CVaR, Robust Mean-Variance, and Scenario-Based Robust Optimization.
- Candidate Portfolio Factory orchestration through `run_candidate_factory.py` as backend/advanced/research infrastructure.
- Canonical candidate comparison and generated V1 decision-support artifacts through `run_compare_variants.py`: robustness scorecard, Portfolio Health Score, Selection/No-Trade decision, trade-off/model-risk diagnostics, Assumption Sensitivity, Pareto / Dominance, Regret Analysis, Action Plan, current-vs-policy status, Monitoring / What Changed, generated Decision Journal, and decision package summary. These are **not** the current Core MVP product flow; they are advanced/backend/technical/generated support unless explicitly requested.
- ETF and stock taxonomy validation as annotation/diagnostic layers.
- Partial utility UIs: `config_ui/` (local config editor) and `results_dashboard/` (read-only results viewer). These are supported utility surfaces, not the full product workspace.

Target/TBD areas:

- Full interactive UI and saved analysis workspaces.
- Formal diagnosis-only product state beyond current generated artifacts.
- Full user-triggered Portfolio Alternatives Builder UX/service beyond the current backend one-candidate delegation plan.
- Current-vs-selected-candidate as the primary interactive UI beyond the current additive JSON adapter.
- Natural-language AI Commentary generation beyond the current deterministic grounding context
  (`ai_commentary_context.json`). Rule-based `commentary.txt` / `stress_commentary.txt` are current
  report exports, not LLM AI Commentary (see [AI commentary grounding spec](docs/specs/ai_commentary_grounding_spec.md)).
- Polished product UI and workspace flows around the existing file-first Candidate Portfolio Factory, current-vs-policy workflow, comparison, and decision package artifacts.
- More deliberately designed client-facing report packages beyond the current file-first summary/PDF-style surfaces.
- Advanced UX modules around the implemented file-first V1 artifacts.

## Main Pipeline

“ДИАГНОСТИКА 2” is the binding product workflow contract:

```text
current portfolio / analysis_subject
-> Portfolio X-Ray diagnostics
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> one selected candidate or generated shortlist
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary grounding
-> Monitoring / What Changed
```

The portfolio-first orchestrator is implemented and governed by
[portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md). Routine and
full-review commands:

```bash
python run_portfolio_review.py
python run_portfolio_review.py --mode core
python run_portfolio_review.py --dry-run
python run_portfolio_review.py --mode full
python run_portfolio_review.py --mode full --resume-candidates
python run_portfolio_review.py --skip-candidates
python run_portfolio_review.py --candidate-profile core_benchmarks
python run_portfolio_review.py --candidates equal_weight,risk_parity
```

| Review mode | Factory profile | Typical use |
| --- | --- | --- |
| **Core** (default) | `core_fast` (same six ids as `core_v1`, parallel lightweight reports by default) | Routine monthly review |
| **Core regression** | `core_v1` via `--candidate-profile core_v1` | Sequential parity/debug run |
| **Full** | `default_v1` (16 builders incl. optimizers + robust) | Explicit refresh of the full candidate menu |
| **Full resume** | `default_v1` with factory `--resume` | Recovery after an interrupted full factory run |

`run_portfolio_review.py` materializes `{output_dir_final}/analysis_subject/` first, then runs
the non-policy candidate factory and comparison path. It does not call `run_optimization.py` in the
default path. Inspect subject diagnostics before interpreting candidate or decision artifacts.

### Blocks 1-5 MVP core (first five product blocks)

Blocks 1-5 are the practical reliability core for the current file-first implementation: Input and
Assumptions, Portfolio X-Ray, Stress Lab, candidate hypothesis building, and optimizer-backed
candidate methods. This is not the Core MVP product story. Product-facing UX should route through
diagnosis, Candidate Launchpad, Alternatives Builder, comparison, and verdict language, while the
Candidate Factory remains backend/advanced/research orchestration. Optimizer-backed candidates are
supporting hypotheses for comparison, not black-box recommendations. The
active reliability plan is
[Blocks 1-5 MVP Core Reliability Plan](docs/exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md).

Routine command (site/API JSON/cache output; no PDF rebuild):

```bash
python run_portfolio_review.py --mode core
```

Offline acceptance gate (five tickers, explicit weights, no network):

```bash
python -m pytest tests/test_blocks_1_5_mvp_smoke.py -q --basetemp='tmp\pytest_blocks_1_5_smoke'
```

Weighted `current_portfolio` / `model_portfolio` subjects must not have a positive-weight sum above
`1.0`; partial sums below `1.0` remain valid as explicit cash-remainder diagnostics. Operator
details: [docs/operational_runbook.md](docs/operational_runbook.md) section 0; verification matrix:
[TESTING.md](TESTING.md).

The existing legacy policy flow remains callable for compatibility and historical policy runs.
By default, `run_optimization.py` writes policy weights and JSON metadata only; it does **not**
invoke `run_report.py` unless `--with-report` is passed:

```bash
python run_optimization.py
python run_optimization.py --with-report
python run_report.py
python run_report.py --output-profile full_report
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
python run_optimization.py --with-report --output-profile legacy_export
```

Report options:

```bash
python run_report.py --no-cache
python run_report.py --clear-cache
python run_report.py --backtest-mode dynamic_nan_safe
python run_report.py --materialize-analysis-subject
```

Optional read-only Interactive Brokers market data smoke check, with TWS / IB Gateway already open
and API sockets enabled:

```bash
python run_ibkr_market_data.py --symbols VOO,SPY --port 7497 --market-data-type 3
python run_ibkr_market_data.py --symbols VOO --history-symbol VOO --history-duration "1 M"
python run_ibkr_market_data.py --symbols SPY,QQQ,GLD,SLV,BND,SCHD,SCHP,TLT --history-all --provider ibkr --start 2026-05-01 --end 2026-05-22
```

Set `market_data_provider: ibkr_yfinance_fallback` in `config.yml` to make the main data loader try
IBKR first and use Yahoo Finance only for missing tickers. Use `yfinance` to keep the legacy source.

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
python run_candidate_factory.py --profile core_fast --then-compare
python run_candidate_factory.py --profile default_v1 --then-compare  # advanced/research full menu
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

Use `run_candidate_factory.py` to orchestrate multiple candidate builders before comparison as a
backend/advanced/research operation. Do not present standalone batch factory runs as the core product
UX; product-facing flows should start from diagnosis and user-selected hypotheses.
Default factory path for portfolio-first review: `--execution-mode standard` (weights +
`lightweight_comparison` snapshots for compare, no per-candidate Pandoc). Optional Phase 3:
`--full-candidate-reports` or `--selected-candidates-for-full-report` for HTML/commentary/rolling
betas on chosen candidates; pair with `--pdf-mode final_only` for one PDF rebuild after Phase 3.
Factory default `--pdf-mode none` skips per-candidate Pandoc (~3 min saved per candidate); use
`--pdf-mode per_candidate` only for legacy full PDF parity. Advanced factory-only runs can add
`--parallel-lightweight-reports --lightweight-report-workers 4` to eligible `standard` runs; this
parallelizes only Phase 2 `lightweight_comparison` report generation and falls back to sequential
mode for fail-fast, per-candidate PDF, Phase 3 full reports, and non-`standard` execution modes.
Details live in [docs/specs/candidate_factory_spec.md](docs/specs/candidate_factory_spec.md), [docs/specs/candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md), [docs/specs/robust_mv_spec.md](docs/specs/robust_mv_spec.md), and [docs/specs/robust_scenario_optimization_spec.md](docs/specs/robust_scenario_optimization_spec.md).

## Key Inputs

| File | Purpose |
| --- | --- |
| `config.yml` | Active local config. **Core MVP (portfolio-first):** `tickers`, `current_weights` or `weights`, and `investor_currency` only. USD risk-free, cash proxy, and benchmark resolve when omitted. Optional explicit bank cash (`Cash USD`, …) is a zero-return holding, not `cash_proxy_ticker`. Legacy optimizer/mandate fields (`client_profile`, liquidity, targets) stay in `config.yml.example` Sections 4–7 and are not required for `run_portfolio_review.py`. |
| `config.yml.example` | MVP-first template (Section 1 = Core MVP; Sections 4–7 = legacy/advanced). |
| `config/client_profiles.yml` | Client risk profile defaults (legacy optimizer / mandate; not Core MVP). |
| `config/etf_universe.yml` | ETF taxonomy source of truth for annotation and validation. |
| `config/stock_universe.yml` | Stock taxonomy source of truth for stock metadata validation. |
| `config/historical_stress_proxy_map.yml` | Historical stress fallback proxy map and thresholds. |
| `assets.yml` | Optional asset metadata. |
| `tests/fixtures/mvp_portfolios/*.yml` | Minimal USD validation fixtures (`minimal_usd_no_cash`, `minimal_usd_with_cash`). |

Portfolio-first input semantics live in
[docs/specs/portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md):
`analysis_subject` is the portfolio diagnosed before candidates, with supported types
`current_portfolio`, `model_portfolio`, and `universe_baseline`.

Core MVP input contract, field tiers, real cash, and export disclosure (`input_surface`,
`field_tiers` in `input_assumptions`) live in
[docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md). When you supply
`current_weights` or non-generated `weights` without an explicit `analysis_subject`, validation
injects `analysis_subject.type = current_portfolio` and
`analysis_mode = analyze_current_weights` (`src/mvp_input.py`). Legacy policy compatibility still
uses `analysis_mode: optimize_from_universe` when no user weights are supplied. Explicit
`analysis_subject` blocks remain supported for `model_portfolio`, `universe_baseline`, or custom ids.

Local **config UI** (`config_ui/`) mirrors the three Core MVP fields on the first screen; legacy
optimizer and mandate controls sit under collapsed Advanced settings.

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
| `DOCUMENTATION_MIGRATION_PLAN.md` | Documentation migration plan and session roadmap; draft/planning only. |
| `docs/archive/documentation_migration_2026_05_25/` | Archived pre-migration versions of replaced documentation. |
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
| Documentation migration records | [DOCUMENTATION_MIGRATION_PLAN.md](DOCUMENTATION_MIGRATION_PLAN.md), [DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md](DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md), and archived legacy docs |
| Planning protocol | [PLANS.md](PLANS.md) |
| Design rules | [DESIGN.md](DESIGN.md) |

## Contributor Rules

- Do not invent formulas when a spec exists.
- Do not treat product concept docs as automatic implementation changes.
- Keep production weights generated by the optimizer or approved post-optimization protocols.
- Preserve diagnostic-only boundaries unless a canonical spec changes them.
- Update docs when behavior, interfaces, outputs, commands, workflows, terminology, or source-of-truth ownership changes.
- Use `WORKFLOW.md` for the task process and `TESTING.md` for verification.
