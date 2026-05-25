# OUTPUTS.md

This file is the root map for generated outputs, report artifacts, output folders, and output-format ownership in Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It explains what the project creates, where it is written, which formats are used, which files are source vs generated, and which detailed specs own the behavior. It does not replace metric formulas, stress logic, scenario definitions, or implementation contracts.

Update this file when output folders, artifact names, formats, report sections, generated-vs-source boundaries, visual/report packaging, or output-producing workflows change.

## Core Rule

Generated outputs are evidence and deliverables, not source files, unless a task explicitly targets generated artifacts.

Source files define behavior. Generated files show the result of a run.

Documentation migration records such as `DOCUMENTATION_MIGRATION_PLAN.md`, `DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md`, and archived legacy Markdown files are source/planning documents, not generated run outputs. They do not define output contracts.

Default execution is now site/API-first: JSON contracts and required cache are the machine-readable
source of truth for new workflows. CSV, TXT, HTML, PNG, PDF, Markdown PDF sidecars, and CSS/visual
presentation assets are export/report artifacts only and must be requested explicitly through
`full_report`, `legacy_export`, or PDF export commands. CSV exporters remain supported for audit,
Excel review, debugging, and legacy reporting, but CSV is not produced by default.

## Read this first

When `{output_dir_final}` is `Main portfolio/` (typical), **two artifact trees coexist**. They describe
**different portfolios** — do not merge them when interpreting a portfolio-first review.

| Location | Meaning | Authoritative for |
| --- | --- | --- |
| `{output_dir_final}/analysis_subject/` | Portfolio-first **subject** diagnosed before candidates | Starting weights, Blocks 1–3 diagnostics (X-Ray, stress, snapshots, `run_metadata.json`) for the reviewed portfolio |
| `{output_dir_final}/` root — `run_result.json`, `portfolio_weights.yml`, root `portfolio_xray.json`, `stress_report.json`, `run_metadata.json` | **Legacy policy optimization** (`run_optimization.py`, optionally `--with-report`) | Policy release checks and historical policy runs only — **not** the portfolio-first subject |

**Operator rules:**

1. After `python run_portfolio_review.py`, open **`analysis_subject/` first**; candidate comparison uses that baseline.
2. Do **not** mix subject weights/diagnostics with root policy weights or root stress/X-Ray files.
3. Default `site_api` review writes **JSON + cache only**. TXT, HTML, PNG, CSV under `analysis_subject/` or variant folders, and PDFs under `pdf files/`, may be **stale** from earlier export runs unless you explicitly requested `--with-pdf`, `--legacy-full-pdf`, or `--output-profile full_report` / `legacy_export`.
4. `candidate_factory_run.json` records the **last factory orchestration** (profile, steps, reuse). `candidate_comparison.json` aggregates **evidence scanned from disk** — wider than the last factory run when snapshots are reused. Read `candidate_menu` before trusting rankings.

Operator detail: [WORKFLOW.md § Portfolio-First Operator Checklist](WORKFLOW.md#portfolio-first-operator-checklist);
[docs/operational_runbook.md §0.1](docs/operational_runbook.md#01-read-this-first-main-portfolio-layout);
factory playbooks: [runbook §8](docs/operational_runbook.md#8-candidate-portfolio-factory-operator-playbook).
Confusion audit:
[2026-05-23 core/full artifact audit](docs/audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md).

## Command Matrix

**Review default vs full menu:** routine portfolio review (`run_portfolio_review.py` with no mode
flag, or `--mode core`) runs factory profile **`core_v1`** (six candidates). The full optimizer and
robust menu (**`default_v1`**, 16 builders) runs only with **`--mode full`** on review, or via
standalone **`run_candidate_factory.py --profile default_v1`**. Do not treat a **`core_v1`** review
as proof that the full menu was built.

### Portfolio-first review (orchestrated)

| Use case | Command | Factory profile |
| --- | --- | --- |
| Portfolio review site/API (**core**, default) | `python run_portfolio_review.py` or `--mode core` | `core_v1` |
| Full review (16 builders + compare) | `python run_portfolio_review.py --mode full` | `default_v1` |
| Compare / decision package only (no subject/factory) | `python run_compare_variants.py` | — |
| Portfolio-first PDF export | `python run_portfolio_review.py --with-pdf` | same as mode |
| Full legacy PDF suite | `python run_portfolio_review.py --legacy-full-pdf` or `python rebuild_pdf_reports.py` | — |

### Standalone candidate factory

Use when refreshing candidates without a full portfolio review, or when resuming a factory run.
Profile must match the menu you intend to score (`core_v1` vs `default_v1`).

| Use case | Command | Factory profile |
| --- | --- | --- |
| Full menu factory + compare | `python run_candidate_factory.py --profile default_v1 --then-compare` | `default_v1` |
| Core menu factory + compare | `python run_candidate_factory.py --profile core_v1 --then-compare` | `core_v1` |
| Benchmark/timing run (parallel Phase 2) | `python run_candidate_factory.py --profile default_v1 --then-compare --parallel-lightweight-reports` | `default_v1` |

### Legacy policy and report exports

| Use case | Command |
| --- | --- |
| Default site/API report | `python run_report.py` |
| Legacy policy optimize only | `python run_optimization.py` |
| Legacy policy + site/API report | `python run_optimization.py --with-report` |
| Legacy/full report exports | `python run_report.py --output-profile full_report` |
| Legacy export + PDF-capable sidecars | `python run_report.py --output-profile legacy_export` |

## Output Policy

Central routing: `src/output_policy.py`. Default profile: `site_api`.

| Profile | JSON contracts | Cache | CSV / TXT / HTML / PNG | PDF / Markdown sidecars / CSS |
| --- | --- | --- | --- | --- |
| `site_api` (default) | Yes | Yes | No | No |
| `core_json` | Yes | Yes | No | No |
| `lightweight_comparison` | Yes | Yes | No | No |
| `full_report` | Yes | Yes | Yes | No |
| `legacy_export` | Yes | Yes | Yes | Yes |

`output_manifest.json` (`output_manifest_v1`) is written under `output_dir_final` after report,
factory, compare, and portfolio-review runs. It indexes `output_profile`, required JSON paths,
`disabled_artifact_classes`, optional `cache_keys`, and `artifact_counts_by_type` for UI/API
consumers. Cache under `cache/` is internal infrastructure, not a client-facing contract.

CSV exporters remain in source for audit, Excel review, debugging, and legacy reporting; they are
not invoked unless `full_report`, `legacy_export`, or an explicit PDF/export command requests them.

## Main Output Flow

The current implementation is site/API-first and CLI/file-driven.

Portfolio-first output flow contract:

```text
analysis_subject
-> subject diagnostics
-> candidate outputs
-> subject-centered comparison and decision package
```

The portfolio-first orchestrator (`run_portfolio_review.py`) follows this order by default. The
legacy policy output flow remains callable for compatibility only:

```text
config.yml
-> run_optimization.py
-> optimized weights and run metadata
-> run_report.py
-> metrics, diagnostics, stress reports, scenario libraries, commentary, snapshots, and report artifacts
```

Compatibility commands:

```bash
python run_optimization.py
python run_optimization.py --with-report
python run_report.py
python run_report.py --output-profile full_report
```

## Output Producers

| Producer | Role | Common outputs |
| --- | --- | --- |
| Portfolio-first subject materialization | Subject diagnostics before candidates | `{output_dir_final}/analysis_subject/` snapshots, metadata, X-Ray, and diagnostics from `run_report.py --materialize-analysis-subject` |
| `run_optimization.py` | Legacy policy optimization and release checks | `portfolio_weights.yml`, `run_result.json`, run metadata under `output_dir_final` |
| `run_report.py` | Main report and diagnostics flow | JSON contracts by default (`stress_report.json`, `portfolio_xray.json`, snapshots, scenario libraries); CSV/TXT/HTML/PNG/PDF only with `full_report` / `legacy_export` |
| Candidate portfolio scripts | Build fixed benchmark/candidate weights and run the report pipeline | Candidate output folders with the same report contract after weights are fixed |
| Robust/scenario scripts | Build robust candidate weights or reports from existing report artifacts | Robust/scenario JSON, CSV, and candidate report folders |
| Taxonomy scripts | Validate/list/export taxonomy diagnostics | Taxonomy validation/list/export artifacts where configured |
| PDF rebuild helpers | Rebuild PDF-style artifacts from report-sidecar content | `pdf files/` and `pdf_md_sources/` artifacts |

## Common Output Locations

| Location | Meaning | Source status |
| --- | --- | --- |
| `Main portfolio/` | Default main portfolio output folder, usually `output_dir_final`; hosts `candidate_comparison.json` | Generated |
| `{output_dir_final}/analysis_subject/` | Portfolio-first diagnostics folder for the subject analyzed before candidates | Generated |
| `results_csv/` | Tabular metrics, stress, factor, scenario, and diagnostic CSV outputs | Generated |
| `output/` | Auxiliary runtime output folder where configured | Generated |
| `cache/` | Cached data/runtime material | Generated |
| Candidate portfolio folders | Outputs for Equal Weight, Risk Parity, MinVar, CVaR, Robust MV, robust scenario, and other variants | Generated |
| `pdf files/` | Generated PDF-style report artifacts | Generated only when explicitly requested (`run_portfolio_review.py --with-pdf`, `--legacy-full-pdf`, `run_report.py --output-profile legacy_export`, or `rebuild_pdf_reports.py`); default site/API review does not write PDFs |
| `pdf_md_sources/` | Generated Markdown sidecars used for PDF-style report builds | Generated |
| `portfolio_weights.yml` | Optimizer-produced weights | Generated runtime output, not normal manual input |

Root documentation files such as `README.md`, `SPEC.md`, `DATA.md`, `TESTING.md`, `WORKFLOW.md`, `RULES.md`, `GLOSSARY.md`, `KNOWN_ISSUES.md`, `DECISIONS.md`, `CHANGELOG.md`, this file, `DOCUMENTATION_MIGRATION_PLAN.md`, `DOCUMENTATION_MIGRATION_SESSION09_AUDIT.md`, and archived legacy Markdown files are source/planning documentation, not generated outputs.

Target product concepts from the documentation migration, including diagnosis-only state, Problem
Classification, Candidate Launchpad, Portfolio Alternatives Builder, Decision Verdict language, and
AI Commentary, do not create new artifact contracts until an owning spec and implementation define
their concrete files, schemas, and output policy.

Output terminology boundary: product-facing `Decision Verdict` language may map to current generated
Selection/No-Trade evidence, but it does not rename `selection_decision.json`, Selection Engine
contracts, No-Trade artifacts, or any existing output fields. Advanced/backend generated artifacts
such as robustness scorecard, Portfolio Health Score, Selection/No-Trade, action, monitoring, and
journal outputs may remain current implementation outputs without becoming Core MVP product UI.

## Output Formats

| Format | Used for | Rules |
| --- | --- | --- |
| YAML | Optimizer-produced weights and source configs | `config.yml` is source config; `portfolio_weights.yml` is generated output |
| JSON | Run metadata, stress reports, scenario libraries, diagnostics, candidate metadata | Preserve structured fields and explicit warnings/metadata for degraded diagnostics |
| CSV | Metrics, stress tables, factor/regime/scenario diagnostics | Export-only (`full_report` / `legacy_export`); numeric rounding only at final export stage |
| TXT | Human-readable commentary and stress commentary | Export-only; English-only UTF-8 when enabled |
| HTML | Snapshots, dashboards, and generated visual report surfaces | Export-only; follow [DESIGN.md](DESIGN.md) for visual/interface work |
| PDF-style artifacts | Client/report packages | Export-only (`legacy_export`, explicit PDF rebuild, or `--with-pdf`) |
| Markdown sidecars | Intermediate report text for PDF-style builds | Export-only under `pdf_md_sources/` when PDF pipeline runs |

## Primary Artifacts

Default `site_api` runs produce the JSON rows below (plus cache). CSV, TXT, HTML, PNG, PDF, and
Markdown sidecar rows apply only when an export profile or explicit PDF command enables them.

Common project artifacts include:

- `output_manifest.json` — UI/API index (`output_manifest_v1`; profile, paths, disabled classes, counts)

- `portfolio_weights.yml`
- `run_result.json`
- `run_metadata.json`
- `stress_report.json`
- Custom shock simulator API (no generated file by default): `src/stress.py::simulate_custom_shock` and
  `shock_vector_from_scenario`; contract in [stress testing spec](docs/specs/stress_testing_spec.md) §12.3
- `custom_shock_runs.json` (optional, opt-in only): versioned audit trail for
  `record_custom_shock_run` / `write_custom_shock_runs`; not written by `run_stress` or default
  `run_report.py` paths; envelope `custom_shock_runs_v1` per stress spec §12.3
- `stress_report.json.stress_scorecard_v1` (unified stress scorecard block)
- `stress_report.json.stress_conclusions` (aggregated stress conclusions)
- `stress_report.json.hedge_gap_analysis` (hedge gap diagnostic block)
- `stress_report.json.historical_episode_paths` (path-level crisis replay block)
- `stress_report.json.data_trust_summary` (`stress_data_trust_summary_v1`; episode quality, young-ETF and taxonomy warnings for user-readable surfaces; RM-1016)
- `portfolio_xray.json`
- `portfolio_xray.json.data_trust_signals` and `input_assumptions.data_trust_signals` (`input_data_trust_signals_v1`; rolled section warnings plus stress trust; RM-1016)
- `scenario_library.json`
- `scenario_library_normalized.json`
- metric CSV files under `results_csv/`
- stress, factor, macro, regime, and scenario CSV files under `results_csv/`
- `results_csv/crisis_replay_{episode}.csv` (path-level historical replay export)
- `results_csv/crisis_replay_{episode}_asset_contrib.csv` (static-weight asset episode attribution)
- `commentary.txt`
- `stress_commentary.txt`
- generated HTML snapshots
- generated PDF-style reports
- candidate portfolio output folders
- `{output_dir_final}/analysis_subject/` (portfolio-first subject diagnostics from `run_report.py --materialize-analysis-subject`; see [portfolio review workflow spec](docs/specs/portfolio_review_workflow_spec.md))
- `candidate_factory_run.json`, optional `candidate_factory_run.txt`, and `candidate_factory_manifest.json` (under `output_dir_final`; factory orchestration from `run_candidate_factory.py`; `--resume` reads the manifest; top-level `run_status` and `execution_summary` disclose partial failure vs full success; `execution_action` per step; contract in [candidate factory spec](docs/specs/candidate_factory_spec.md); methodology map [§4](docs/audits/2026-05-20_candidate_factory_methodology_map.md))
- `candidate_factory_run.json.parallel_lightweight_report_summary` (optional; present when `--parallel-lightweight-reports` is requested or effective; records requested/effective status, fallback reasons, worker count, menu-ordered submitted/registered candidate ids, and optional wall-clock seconds for Phase 2 lightweight report generation)
- `{artifact_root}/candidate_manifest.json` per script-backed candidate folder (`candidate_manifest_v1`; factory-written readiness: comparison gates, artifact presence, optional `partial_failure` when weights succeeded but report/snapshot did not; see [candidate factory spec](docs/specs/candidate_factory_spec.md) Session 5)
- `candidate_comparison.json` (under `output_dir_final`; includes the portfolio-first `analysis_subject` baseline row when materialized; `candidate_menu` reports `factory_evidence_status`, `factory_steps_used`, `factory_evidence_warnings`, and `factory_execution_summary` for `candidate_factory_run.json` freshness and rebuild/reuse disclosure; per-row `construction_disclosure` passthrough including `optimizer_methodology`, `optimizer_quality`, and `optimization_readiness` (`fair_comparison_ready` checklist) for optimizer-backed rows when artifacts exist; optimizer-backed rows with missing methodology/quality or `unknown` quality degrade instead of ordinary `available` evidence; see [candidate comparison spec](docs/specs/candidate_comparison_spec.md))
- `robustness_scorecard.json` and optional `robustness_scorecard.txt` (under `output_dir_final`; written by `run_compare_variants.py` / `write_candidate_comparison_outputs`; see [robustness scorecard spec](docs/specs/robustness_scorecard_spec.md))
- `portfolio_health_score.json` and optional `portfolio_health_score.txt` (under `output_dir_final`; Session 13; see [portfolio health score spec](docs/specs/portfolio_health_score_spec.md))
- `selection_decision.json` and optional `selection_decision.txt` (under `output_dir_final`; contract in [selection engine spec](docs/specs/selection_engine_spec.md))
- `tradeoff_explanation.json` and optional `tradeoff_explanation.txt` (under `output_dir_final`; [src/tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py); [trade-off and model risk spec](docs/specs/tradeoff_and_model_risk_spec.md))
- `model_risk_diagnostics.json` and optional `model_risk_diagnostics.txt` (under `output_dir_final`; same module and spec)
- `assumption_sensitivity.json` and `assumption_sensitivity.txt` (under `output_dir_final` after compare; [assumption sensitivity spec](docs/specs/assumption_sensitivity_spec.md))
- `pareto_dominance.json` and `pareto_dominance.txt` (under `output_dir_final` after compare; [pareto dominance spec](docs/specs/pareto_dominance_spec.md))
- `regret_analysis.json` and `regret_analysis.txt` (under `output_dir_final` after compare; [regret analysis spec](docs/specs/regret_analysis_spec.md); implementation post-audit Session 19)
- `action_plan.json` and optional `action_plan.txt` (under `output_dir_final`; contract in [action engine spec](docs/specs/action_engine_spec.md))
- `monitoring_diff.json` and optional `monitoring_diff.txt` (under `output_dir_final`; [monitoring spec](docs/specs/monitoring_spec.md); compares to prior `monitoring/latest/analysis_snapshot.json`)
- `monitoring/latest/analysis_snapshot.json` and `monitoring/history/analysis_snapshot_{analysis_end}.json` (generated monitoring snapshots; same spec)
- `decision_journal.json` and optional `decision_journal.txt` (under `output_dir_final`; written by `write_candidate_comparison_outputs`; see [decision journal spec](docs/specs/decision_journal_spec.md))
- `journal/latest/decision_journal.json` and `journal/history/decision_journal_{analysis_end}.json` (generated journal copies; same spec)
- `decision_package_summary.json` and `decision_package_summary.txt` (under `output_dir_final`; compact English summary of the full V1 decision package; see [decision package reporting spec](docs/specs/decision_package_reporting_spec.md))
- `current_vs_policy_status.json` and optional `current_vs_policy_status.txt` (under `output_dir_final`; legacy current-vs-policy workflow status and No-Trade actionability; portfolio-first runs may write it with `workflow_profile: portfolio_first_review` as compatibility-only metadata; see [current vs policy workflow spec](docs/specs/current_vs_policy_workflow_spec.md); written after comparison in Session 09 implementation)
- `{output_dir_final}/current_portfolio/` (sidecar folder for materialized current-portfolio snapshots when using the combined current-vs-policy workflow; does not replace policy artifacts on Main root)
- legacy `portfolio_comparison.json` and `ew_rp_comparison.json` (subset comparisons; superseded by canonical contract)

`portfolio_xray.json` is a generated, diagnostic-only Portfolio X-Ray artifact. It summarizes existing report pipeline outputs and in-memory diagnostics; it does not optimize, change weights, change mandate gates, change stress pass/fail status, or make portfolio selection decisions. Its section and disclosure contract is owned by [docs/specs/portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md). Human-readable surfaces are rendered from this JSON via `format_portfolio_xray_text` (`report.txt`), `format_portfolio_xray_html` (`report.html`), and `format_portfolio_xray_commentary` (`commentary.txt` compact block).

`run_result.json` and `run_metadata.json` include an `analysis_setup` block, the resolved runtime contract for the input and assumptions layer. They also include `input_assumptions`, the reporting view projected from `analysis_setup`, summarizing the input mode, tickers, fixed/current weight status, resolved market assumptions, mandate inputs, calculation settings, and known V1 gaps. Legacy policy `run_result.json` also includes `optimizer_run_metadata` (`legacy_policy_optimizer_run_metadata_v1`) with objective, estimator, window, input fingerprints, universe, bounds/caps, cash policy, solver/fallback, release-gate disclosure, covariance methodology, and Young ETF methodology. Optimizer candidate `baseline_weights_metadata.json` exports for Minimum Variance, Maximum Diversification, Minimum CVaR, and Robust Mean-Variance include `optimizer_run_metadata` (`candidate_optimizer_run_metadata_v1`) with candidate-only role, method/objective, input window, input fingerprints, estimator/constraint, solver/fallback, parameter, output-summary disclosure, covariance methodology, and Young ETF methodology while preserving legacy top-level metadata fields. Materialized Robust Scenario candidate metadata may include `optimizer_run_metadata` (`robust_scenario_optimizer_run_metadata_v1`) copied from `robust_optimization_v1_summary.json`, including SLSQP solver/fallback quality. `candidate_comparison.json` copies the comparison-ready subset to `construction_disclosure.optimizer_methodology` when those upstream metadata blocks exist and projects normalized fallback/failure quality to `construction_disclosure.optimizer_quality` when metadata or factory evidence is available. `candidate_comparison.txt` and legacy `ips_summary.txt` include compact optimizer methodology notes when source metadata is present.

The exact artifact set can vary by config, available data, candidate type, and enabled report features.

Optimization output disclosure is governed by the current artifact contracts above and the
[Optimization Engine layer spec](docs/specs/optimization_engine_layer_spec.md). Session 03 adds
legacy policy `optimizer_run_metadata` to `run_result.json`; Session 04 adds candidate optimizer
`optimizer_run_metadata` inside optimizer candidate `baseline_weights_metadata.json` exports.
Session 05 propagates those normalized blocks into `candidate_comparison.json`
`construction_disclosure.optimizer_methodology` without changing optimizer behavior or generated
weights. Session 06 adds `construction_disclosure.optimizer_quality` and factory step optimizer
quality evidence so fallback/approximate solves are degraded, failed factory/optimizer quality is
unavailable, and Selection warnings can surface favored fallback targets. Session 07 adds robust
scenario SLSQP solver status to `robust_optimization_v1_summary.json` and propagates it through the
materialized robust scenario candidate metadata for factory and comparison disclosure. Session 08
adds `input_fingerprints` (`returns_panel_fingerprint`, `config_fingerprint`,
`universe_fingerprint`) and return-panel start/end/row disclosure to legacy policy and optimizer
candidate metadata so stale or mismatched estimator inputs can be audited without regenerating
weights. Session 09 adds `optimizer_covariance_methodology_v1` and
`optimizer_young_etf_methodology_v1` disclosure to optimizer metadata and surfaces compact
methodology notes in `candidate_comparison.txt` / `ips_summary.txt`. Session 10 adds
`construction_disclosure.optimization_readiness` (`optimizer_comparison_readiness_v1`) and compact
readiness notes in `candidate_comparison.txt` for optimizer-backed comparison rows.

## Blocks 1-5 MVP Output Acceptance

When validating the first-five-block MVP core (offline smoke or a representative
`run_portfolio_review.py --mode core --skip-pdf` run), inspect generated artifacts under
`{output_dir_final}/analysis_subject/` before candidate or decision outputs:

| Block | Minimum artifacts | Trust checks |
| --- | --- | --- |
| 1 Input | `run_metadata.json` with `analysis_setup` and `input_assumptions` | Explicit current/model weights sum to at most `1.0`; partial sums disclose cash remainder |
| 2 X-Ray | `portfolio_xray.json` (seven sections) | `data_trust_signals.user_summary_lines` when data-quality warnings exist |
| 3 Stress | `stress_report.json` with scorecard, conclusions, historical methodology, hedge gap | `data_trust_summary.user_summary_lines` for episode/taxonomy/young-ETF warnings |
| 4 Factory | `candidate_factory_run.json` at review root | Comparison `candidate_menu.factory_evidence_status` must be `current` or explicitly not authoritative |
| 4–5 Bundle | `candidate_comparison.json` → `review_bundle_context` | `review_bundle_fingerprint` and `mode_subject_consistency` link subject/factory/comparison; read `user_summary_lines` when `analysis_mode` label differs from `analysis_subject.type` |
| 5 Optimizers | Candidate folders + comparison rows | Optimizer-backed rows are `available` only when readiness-critical evidence is complete; otherwise `degraded` with warning codes |

Generated outputs remain evidence, not source files. Do not commit routine run refreshes unless a
session explicitly targets generated artifacts. Offline gate:
`tests/test_blocks_1_5_mvp_smoke.py` ([TESTING.md](TESTING.md)).

## Output Rules

- Preserve full precision inside calculations.
- Round numeric metrics only at final export/report stage.
- If diagnostics degrade because inputs are missing or weak, expose warnings, coverage, confidence, usability flags, or metadata.
- Do not silently imply full confidence when fallback data or partial coverage was used.
- Do not manually edit generated weights or report artifacts as if they were source behavior.
- If generated outputs are refreshed by a run, commit them only when the task explicitly targets generated artifacts.
- Keep output names and folders stable unless a spec or explicit task changes them.

## Detailed Ownership

| Area | Governing document |
| --- | --- |
| Current implementation output contract | [SPEC.md](SPEC.md) |
| Portfolio-first workflow order and `analysis_subject` output role | [docs/specs/portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md) |
| Portfolio X-Ray JSON and seven-section diagnostic output | [docs/specs/portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) |
| High-level report and artifact contract | [docs/specs/reporting_outputs_spec.md](docs/specs/reporting_outputs_spec.md) |
| Candidate factory run summary JSON | [docs/specs/candidate_factory_spec.md](docs/specs/candidate_factory_spec.md) |
| Candidate Factory layer handoff (Block 4.1–4.9) | [docs/specs/candidate_factory_layer_spec.md](docs/specs/candidate_factory_layer_spec.md) |
| Block 4 methodology map and governance gaps G1–G10 | [docs/audits/2026-05-20_candidate_factory_methodology_map.md](docs/audits/2026-05-20_candidate_factory_methodology_map.md) |
| Canonical candidate comparison JSON | [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md) |
| Robustness Scorecard JSON | [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md) |
| Portfolio Health Score JSON | [docs/specs/portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md) |
| Selection decision JSON | [docs/specs/selection_engine_spec.md](docs/specs/selection_engine_spec.md) |
| Trade-off explanation and model risk diagnostics JSON | [docs/specs/tradeoff_and_model_risk_spec.md](docs/specs/tradeoff_and_model_risk_spec.md) |
| Assumption sensitivity JSON | [docs/specs/assumption_sensitivity_spec.md](docs/specs/assumption_sensitivity_spec.md) |
| Pareto / Dominance JSON | [docs/specs/pareto_dominance_spec.md](docs/specs/pareto_dominance_spec.md) |
| Regret Analysis JSON | [docs/specs/regret_analysis_spec.md](docs/specs/regret_analysis_spec.md) |
| Current-vs-policy workflow and status JSON | [docs/specs/current_vs_policy_workflow_spec.md](docs/specs/current_vs_policy_workflow_spec.md) |
| Monitoring snapshot and diff JSON | [docs/specs/monitoring_spec.md](docs/specs/monitoring_spec.md) |
| Metric formulas, windows, estimators, rounding | [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md) |
| Optimization Engine roles, current optimizer output disclosure, and target-only optimizer boundaries | [docs/specs/optimization_engine_layer_spec.md](docs/specs/optimization_engine_layer_spec.md) |
| Stress, factor, macro, regime, and stress CSV/JSON artifacts | [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md) |
| Scenario Library and normalized scenario outputs | [docs/specs/scenario_library_spec.md](docs/specs/scenario_library_spec.md) |
| Portfolio construction and weight-release outputs | [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md) |
| Production statuses and release semantics | [docs/specs/production_workflow.md](docs/specs/production_workflow.md) |
| Data inputs, data quality, and data-output boundaries | [DATA.md](DATA.md) |
| Output verification and artifact checks | [TESTING.md](TESTING.md) |
| UI, dashboard, HTML, and visual styling | [DESIGN.md](DESIGN.md) |

## Update Rules

Update [OUTPUTS.md](OUTPUTS.md) when any of these change:

- a new output folder or generated artifact is added
- an output folder, file name, or artifact format is renamed or removed
- JSON/CSV/TXT/HTML/PDF-style report contracts change
- report sections, commentary files, snapshots, or generated packages change meaningfully
- generated-vs-source boundaries change
- portfolio-first subject materialization, `run_optimization.py`, `run_report.py`, or candidate scripts
  change what they write
- visual/report formatting rules for generated HTML or PDF-style artifacts change
- verification requirements for generated outputs change

Also update related docs when needed:

- [SPEC.md](SPEC.md) for general output contract changes.
- [docs/specs/reporting_outputs_spec.md](docs/specs/reporting_outputs_spec.md) for detailed report artifact contract changes.
- Owning detailed specs for metrics, stress, scenario, data, optimizer, or production-status behavior.
- [README.md](README.md) for user-facing commands, folders, and output descriptions.
- [TESTING.md](TESTING.md) for output verification strategy.
- [CHANGELOG.md](CHANGELOG.md) for meaningful completed output/reporting changes.
- [DECISIONS.md](DECISIONS.md) when a key output contract or formatting decision is made.
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md) when an output/reporting limitation or bug is discovered but not fixed immediately.

Do not update this file for routine generated-output refreshes that do not change format, meaning, naming, workflow, or contract.

## Verification

For output/reporting changes, use [TESTING.md](TESTING.md).

Typical checks:

- focused tests for the affected report, metric, stress, scenario, or commentary path
- `python run_report.py` when report orchestration or generated artifacts change
- affected candidate or robust script when variant output behavior changes
- artifact inspection for changed JSON/CSV/TXT/HTML/PDF-style outputs
- Markdown link and stale-reference checks when output docs or artifact names change
