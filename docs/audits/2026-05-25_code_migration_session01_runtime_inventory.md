# Code Migration Session 01 Runtime and Entrypoint Inventory

Date: 2026-05-25  
Status: Session 01 complete; documentation-only inventory  
Related plan: `docs/exec_plans/2026-05-25_code_migration_to_diagnosis_first_portfolio_mri.md`  

This audit is a planning input for migrating the current codebase toward the diagnosis-first Portfolio MRI architecture. It records what the current runtime actually does before any migration code changes. It does not override `SPEC.md`, `OUTPUTS.md`, detailed specs, or code.

No code was changed for this inventory. No generated outputs were cleaned. No files were staged or committed.

## 1. Session Objective

Session 01 objective was to freeze a verified inventory of:

- current runtime flow;
- current entrypoints;
- current generated artifacts;
- current candidate factory / optimization / comparison / selection boundaries;
- dirty working tree blockers that must be classified before code migration starts.

This session intentionally does not implement workflow state, Problem Classification, Candidate Launchpad, Portfolio Alternatives Builder, Decision Verdict, AI Commentary, or Monitoring changes. Those are later sessions in the code migration ExecPlan.

## 2. Runtime Thesis Confirmed

The current system is partially portfolio-first but still CLI/file/report-first.

Current default runtime:

```text
run_portfolio_review.py
-> run_report.py --materialize-analysis-subject
-> run_candidate_factory.py
-> run_compare_variants.py / factory --then-compare
-> generated comparison and decision package artifacts
```

This confirms the main migration thesis:

- keep current calculators and generated contracts;
- add thin product-oriented orchestration/adapters;
- make diagnosis-only / one-candidate / multiple-candidate states explicit;
- preserve legacy policy and batch factory paths.

## 3. Entrypoint Inventory

### 3.1 `run_portfolio_review.py`

Role: current default portfolio-first orchestrator.

Verified from help text and source inspection:

- description says it materializes `analysis_subject` diagnostics before candidate generation, comparison, and report packaging;
- supports `--mode core|full`;
- default routine path is `core`, mapped by code to factory profile `core_fast` when profile is not overridden;
- supports `--skip-candidates` for subject-first review using existing candidate artifacts for comparison;
- supports explicit candidates through `--candidates`;
- forwards candidate factory controls such as `--no-skip-existing`, `--force-candidates`, `--resume-candidates`, `--fail-fast`, `--execution-mode`, and `--no-parallel-lightweight-reports`;
- supports `--skip-compare`;
- default output profile is `site_api`;
- PDFs are skipped by default unless `--with-pdf` or `--legacy-full-pdf`;
- `--dry-run` prints planned commands without executing them.

Source ownership:

- CLI file: `run_portfolio_review.py`;
- orchestration logic: `src/portfolio_review_workflow.py`.

Migration classification:

- preserve as CLI front door;
- later sessions may add explicit workflow state metadata;
- do not change current CLI behavior in Session 01.

### 3.2 `run_report.py`

Role: report/diagnostics engine and analysis-subject materializer.

Verified from help text and source inspection:

- supports `--materialize-analysis-subject`;
- supports `--materialize-current`;
- supports output profiles: `site_api`, `core_json`, `lightweight_comparison`, `full_report`, `legacy_export`;
- supports `--review-mode core|full` for subject materialization;
- supports `--use-review-run-context` and `--no-review-run-context`;
- `run_portfolio_report_for_weights()` is the core function that writes diagnostics and report artifacts from fixed weights.

Migration classification:

- preserve as calculator/report backend;
- do not change formulas, stress logic, X-Ray logic, output field names, or rounding behavior;
- later sessions can read its generated artifacts as evidence.

### 3.3 `run_candidate_factory.py`

Role: controlled batch candidate builder orchestration.

Verified from help text and source inspection:

- supports factory profiles and explicit candidate lists;
- supports skip/rebuild/resume/fail-fast controls;
- supports `--then-compare`;
- supports `--execution-mode fast|standard|legacy_full`;
- supports `--pdf-mode none|final_only|per_candidate`;
- supports output profiles;
- supports parallel lightweight comparison reports and Phase 3 full candidate reports.

Source ownership:

- CLI file: `run_candidate_factory.py`;
- factory runtime: `src/candidate_factory.py`;
- candidate weights: `src/candidate_weights.py`;
- shared context: `src/candidate_run_context.py`.

Migration classification:

- preserve as backend / advanced / research batch capability;
- do not confuse it with target Candidate Launchpad or Portfolio Alternatives Builder UX;
- do not remove it or demote implementation capability.

### 3.4 `run_compare_variants.py`

Role: comparison and decision-package writer from existing artifacts.

Verified from help text and source inspection:

- writes `candidate_comparison.json`;
- output profile defaults to `site_api`;
- calls `src.candidate_comparison.write_candidate_comparison_outputs()`;
- downstream output messages include robustness scorecard, portfolio health score, selection decision, action plan, monitoring diff, decision journal, decision package summary, and current-vs-policy status when written.

Migration classification:

- preserve as canonical comparison/decision backend;
- later sessions can add current-vs-candidate product adapter without changing canonical comparison schema.

### 3.5 `run_optimization.py`

Role: legacy policy optimization compatibility flow.

Verified from help text and source inspection:

- help explicitly describes it as a legacy policy optimization compatibility flow;
- help tells operators to use `run_portfolio_review.py` for the portfolio-first `analysis_subject` workflow;
- supports `--with-report` but report is disabled by default for site/API mode;
- supports `--no-report` as deprecated compatibility flag.

Migration classification:

- preserve as legacy compatibility;
- keep out of default diagnosis-first workflow;
- do not delete, rewrite, or change optimizer math.

## 4. Current Runtime Flow

Current portfolio-first flow is implemented by `src.portfolio_review_workflow.build_portfolio_review_plan()`.

Observed plan-building behavior from source:

1. Load and validate config through `load_validated_config()`.
2. Resolve review mode and factory profile.
3. Always add a diagnosis step first:

   ```text
   run_report.py --materialize-analysis-subject --output-profile <profile> --review-mode <core|full>
   ```

4. If review mode is `core`, subject materialization adds `--use-review-run-context`.
5. If candidates are not skipped, add `run_candidate_factory.py` with resolved profile or explicit candidate list.
6. Factory default execution mode in review orchestration is `standard`.
7. If comparison is not skipped, factory receives `--then-compare`; otherwise comparison can be run separately by `run_compare_variants.py`.
8. If PDF output is explicitly enabled, add `rebuild_pdf_reports.py`, either narrow portfolio-first PDFs or full legacy PDF suite.

The current runtime invariant is that `analysis_subject` diagnostics are materialized before candidate generation and before decision artifacts are interpreted.

## 5. Current Generated Artifact Inventory

Current generated artifacts observed under `Main portfolio/` include:

- `analysis_subject/`
- `candidate_factory_run.json`
- `candidate_factory_manifest.json`
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
- `monitoring_diff.json`
- `monitoring/`
- `decision_journal.json`
- `journal/`
- `decision_package_summary.json`
- `current_vs_policy_status.json`
- `portfolio_xray.json`
- `stress_report.json`
- `scenario_library.json`
- `scenario_library_normalized.json`
- `run_metadata.json`
- `run_result.json`
- snapshots such as `snapshot_10y.json`, `snapshot_5y.json`, `snapshot_3y.json`, `snapshot_assets.json`, and `snapshot_index.json`.

Generated artifacts under `Main portfolio/analysis_subject/` include:

- `portfolio_xray.json`;
- `stress_report.json`;
- `run_metadata.json`;
- snapshots;
- scenario library files;
- commentary/report files;
- output manifest.

These artifacts are evidence and generated outputs, not source files.

## 6. Current Candidate / Optimization / Comparison / Selection Boundaries

### Candidate factory

Current factory answers: what did the last factory orchestration attempt, reuse, skip, or fail?

It does not answer: what should the product suggest as a user-facing improvement path?

This distinction matters because target Candidate Launchpad cards are not portfolios and are not the same as factory profiles.

### Candidate comparison

Current comparison answers: what candidate evidence exists on disk and how does it compare under the canonical comparison contract?

It does not directly answer: what single current-vs-selected-candidate MVP view should the user see first?

The migration should add a focused adapter/view rather than changing `candidate_comparison_v1`.

### Optimization

Legacy policy optimization and optimizer-backed candidate construction already expose methodology, quality, readiness, and fallback evidence. Those disclosures are important and should be preserved.

No migration session should change optimizer objectives, constraints, covariance methodology, expected-return logic, or release gates unless a separate optimizer-specific plan approves it.

### Selection and No-Trade

Current technical decision contract is Selection Engine:

- implementation: `src/selection_engine.py`;
- artifact: `selection_decision.json`;
- schema: `selection_decision_v1`.

Product-facing Decision Verdict should map these outputs to user-facing language later. It should not rename the technical contract.

## 7. Current Target-Layer Implementation Status

| Target layer | Current verified status from Session 01 | Session 01 conclusion |
| --- | --- | --- |
| Input Portfolio | Implemented CLI/file-driven V1 through config, analysis setup, input assumptions, and `analysis_subject`. | Reuse backend. |
| Portfolio X-Ray | Implemented as generated diagnostic artifact and helpers. | Reuse backend. |
| Stress Test Lab | Implemented as stress report, scorecard, conclusions, scenario/factor evidence. | Reuse backend. |
| Problem Classification | No verified owning module or artifact in current code/specs. | Target/TBD; implement later. |
| Candidate Launchpad | No verified owning module or artifact. Factory profiles are not Launchpad. | Target/TBD; implement later. |
| Portfolio Alternatives Builder | Existing builders/factory exist, but no verified user-triggered product wrapper. | Target/TBD wrapper over current builders. |
| Current vs Candidate Comparison | Canonical comparison exists; primary one-candidate UX/view is not verified as current implementation. | Add adapter later. |
| Decision Verdict | Current Selection Engine exists; product-facing verdict replacement/mapping is target/TBD. | Add mapping later without schema rename. |
| AI Commentary | Deterministic commentary exists; formal AI grounding contract not verified. | Add grounding contract later. |
| Monitoring / What Changed | V1 monitoring exists. | Reuse and add light product projection later. |

## 8. Dirty Working Tree Classification Needed

Current `git status --short` shows substantial unrelated dirty state. Session 01 did not clean, revert, stage, or commit any of it.

Required classification before code migration:

| Category | Examples | Required decision before code changes |
| --- | --- | --- |
| Config/source/test changes | `config.yml`, `config.yml.example`, `requirements.txt`, `src/action_engine.py`, `src/cache.py`, `src/candidate_comparison.py`, `src/config_schema.py`, `src/data_loader.py`, `src/data_trust_signals.py`, `src/live_core_e2e.py`, `src/selection_engine.py`, `tests/test_data_cache_key.py` | Keep, revert, or commit separately. |
| Existing dirty docs/registers | `docs/audits/README.md`, `docs/exec_plans/README.md` | Determine whether they belong to the documentation migration or another task before editing further. |
| Generated candidate/report artifacts | candidate folders, `pdf files/`, `pdf_md_sources/`, report JSON/TXT/HTML/PNG/PDF outputs | Ignore, archive, or commit separately only if explicitly required. |
| Python bytecode/cache | `src/__pycache__/...` | Ignore/revert as generated cache. |
| Logs | `candidate_factory_session9_smoke.log`, `candidate_factory_stderr.log`, `candidate_factory_stdout.log`, `portfolio_review_stderr.log`, `portfolio_review_stdout.log` | Ignore/archive unless required evidence. |
| Untracked generated manifests | candidate `candidate_manifest.json` files | Classify as generated output unless explicitly targeted. |
| Untracked IBKR/data provider work | `run_ibkr_market_data.py`, `src/data_ibkr.py`, `src/data_provider.py`, `tests/test_data_ibkr.py`, `tests/test_data_provider.py` | Keep or commit separately; do not mix with Portfolio MRI migration. |

Because dirty docs registers already exist, Session 01 did not update `docs/audits/README.md`. This audit can be registered later once the register's unrelated dirty state is classified.

## 9. Python / Verification Environment Note

Plain `python` and `py -3` were not available in the shell during Session 01. The repository `.venv` Python exists and reports:

```text
Python 3.12.13
```

Use this command form for future checks unless the environment changes:

```text
.\.venv\Scripts\python.exe
```

`run_portfolio_review.py --help` initially hit a Windows console encoding error because the help text contains a Unicode arrow. Setting `PYTHONIOENCODING=utf-8` allowed the help command to succeed. Future documentation or CLI sessions on this Windows shell should use:

```text
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe run_portfolio_review.py --help
```

## 10. Session 01 Verification Performed

Performed:

- inspected `git status --short`;
- confirmed `.venv` Python version;
- inspected help output for:
  - `run_portfolio_review.py`;
  - `run_candidate_factory.py`;
  - `run_compare_variants.py`;
  - `run_report.py`;
  - `run_optimization.py`;
- inspected existing audit register without modifying it;
- wrote this docs-only runtime inventory.

Not performed:

- no tests that run project code beyond CLI help;
- no smoke run;
- no generated-output refresh;
- no staging;
- no commit.

## 11. Next Recommended Session

Next session remains:

**Session 02 - Define workflow state model: diagnosis-only, one candidate, multiple candidates**

Do not begin Session 02 code changes until dirty working tree classification is resolved or the user explicitly accepts working on top of the existing dirty state with a strict file allowlist.
