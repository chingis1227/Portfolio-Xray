# OUTPUTS.md

This file is the root map for generated outputs, report artifacts, output folders, and output-format ownership in Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It explains what the project creates, where it is written, which formats are used, which files are source vs generated, and which detailed specs own the behavior. It does not replace metric formulas, stress logic, scenario definitions, or implementation contracts.

Update this file when output folders, artifact names, formats, report sections, generated-vs-source boundaries, visual/report packaging, or output-producing workflows change.

## Core Rule

Generated outputs are evidence and deliverables, not source files, unless a task explicitly targets generated artifacts.

Source files define behavior. Generated files show the result of a run.

## Main Output Flow

The current implementation is report-first and CLI/file-driven.

```text
config.yml
-> run_optimization.py
-> optimized weights and run metadata
-> run_report.py
-> metrics, diagnostics, stress reports, scenario libraries, commentary, snapshots, and report artifacts
```

Main commands:

```bash
python run_optimization.py
python run_report.py
```

## Output Producers

| Producer | Role | Common outputs |
| --- | --- | --- |
| `run_optimization.py` | Main policy optimization and release checks | `portfolio_weights.yml`, `run_result.json`, run metadata under `output_dir_final` |
| `run_report.py` | Main report and diagnostics flow | `stress_report.json`, `portfolio_xray.json`, metrics CSV, scenario libraries, commentary, HTML/PDF-style artifacts |
| Candidate portfolio scripts | Build fixed benchmark/candidate weights and run the report pipeline | Candidate output folders with the same report contract after weights are fixed |
| Robust/scenario scripts | Build robust candidate weights or reports from existing report artifacts | Robust/scenario JSON, CSV, and candidate report folders |
| Taxonomy scripts | Validate/list/export taxonomy diagnostics | Taxonomy validation/list/export artifacts where configured |
| PDF rebuild helpers | Rebuild PDF-style artifacts from report-sidecar content | `pdf files/` and `pdf_md_sources/` artifacts |

## Common Output Locations

| Location | Meaning | Source status |
| --- | --- | --- |
| `Main portfolio/` | Default main portfolio output folder, usually `output_dir_final`; hosts `candidate_comparison.json` | Generated |
| `results_csv/` | Tabular metrics, stress, factor, scenario, and diagnostic CSV outputs | Generated |
| `output/` | Auxiliary runtime output folder where configured | Generated |
| `cache/` | Cached data/runtime material | Generated |
| Candidate portfolio folders | Outputs for Equal Weight, Risk Parity, MinVar, CVaR, Robust MV, robust scenario, and other variants | Generated |
| `pdf files/` | Generated PDF-style report artifacts | Generated |
| `pdf_md_sources/` | Generated Markdown sidecars used for PDF-style report builds | Generated |
| `portfolio_weights.yml` | Optimizer-produced weights | Generated runtime output, not normal manual input |

Root documentation files such as `README.md`, `SPEC.md`, `DATA.md`, `TESTING.md`, `WORKFLOW.md`, `RULES.md`, `GLOSSARY.md`, `KNOWN_ISSUES.md`, `DECISIONS.md`, `CHANGELOG.md`, and this file are source documentation, not generated outputs.

## Output Formats

| Format | Used for | Rules |
| --- | --- | --- |
| YAML | Optimizer-produced weights and source configs | `config.yml` is source config; `portfolio_weights.yml` is generated output |
| JSON | Run metadata, stress reports, scenario libraries, diagnostics, candidate metadata | Preserve structured fields and explicit warnings/metadata for degraded diagnostics |
| CSV | Metrics, stress tables, factor/regime/scenario diagnostics | Tabular exports; numeric rounding only at final export/report stage |
| TXT | Human-readable commentary and stress commentary | Generated commentary files are English-only UTF-8 |
| HTML | Snapshots, dashboards, and generated visual report surfaces | Follow [DESIGN.md](DESIGN.md) for visual/interface work |
| PDF-style artifacts | Client/report packages where configured | Generated deliverables; source behavior stays in code and specs |
| Markdown sidecars | Intermediate report text for PDF-style builds | Generated when produced under `pdf_md_sources/` |

## Primary Artifacts

Common project artifacts include:

- `portfolio_weights.yml`
- `run_result.json`
- `run_metadata.json`
- `stress_report.json`
- `portfolio_xray.json`
- `scenario_library.json`
- `scenario_library_normalized.json`
- metric CSV files under `results_csv/`
- stress, factor, macro, regime, and scenario CSV files under `results_csv/`
- `commentary.txt`
- `stress_commentary.txt`
- generated HTML snapshots
- generated PDF-style reports
- candidate portfolio output folders
- `candidate_comparison.json` (under `output_dir_final`; see [candidate comparison spec](docs/specs/candidate_comparison_spec.md))
- `robustness_scorecard.json` and optional `robustness_scorecard.txt` (under `output_dir_final`; written by `run_compare_variants.py` / `write_candidate_comparison_outputs`; see [robustness scorecard spec](docs/specs/robustness_scorecard_spec.md))
- `portfolio_health_score.json` and optional `portfolio_health_score.txt` (under `output_dir_final`; Session 13; see [portfolio health score spec](docs/specs/portfolio_health_score_spec.md))
- `selection_decision.json` and optional `selection_decision.txt` (under `output_dir_final`; Session 15 implementation; contract in [selection engine spec](docs/specs/selection_engine_spec.md))
- `action_plan.json` and optional `action_plan.txt` (under `output_dir_final`; Session 16 implementation; contract in [action engine spec](docs/specs/action_engine_spec.md))
- `monitoring_diff.json` and optional `monitoring_diff.txt` (under `output_dir_final`; [monitoring spec](docs/specs/monitoring_spec.md); compares to prior `monitoring/latest/analysis_snapshot.json`)
- `monitoring/latest/analysis_snapshot.json` and `monitoring/history/analysis_snapshot_{analysis_end}.json` (generated monitoring snapshots; same spec)
- `decision_journal.json` and optional `decision_journal.txt` (under `output_dir_final`; written by `write_candidate_comparison_outputs`; see [decision journal spec](docs/specs/decision_journal_spec.md))
- `journal/latest/decision_journal.json` and `journal/history/decision_journal_{analysis_end}.json` (generated journal copies; same spec)
- `decision_package_summary.json` and `decision_package_summary.txt` (under `output_dir_final`; compact English summary of the full V1 decision package; see [decision package reporting spec](docs/specs/decision_package_reporting_spec.md))
- legacy `portfolio_comparison.json` and `ew_rp_comparison.json` (subset comparisons; superseded by canonical contract)

`portfolio_xray.json` is a generated, diagnostic-only Portfolio X-Ray artifact. It summarizes existing report pipeline outputs and in-memory diagnostics; it does not optimize, change weights, change mandate gates, change stress pass/fail status, or make portfolio selection decisions.

`run_result.json` and `run_metadata.json` include an `analysis_setup` block, the resolved runtime contract for the input and assumptions layer. They also include `input_assumptions`, the reporting view projected from `analysis_setup`, summarizing the input mode, tickers, fixed/current weight status, resolved market assumptions, mandate inputs, calculation settings, and known V1 gaps.

The exact artifact set can vary by config, available data, candidate type, and enabled report features.

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
| High-level report and artifact contract | [docs/specs/reporting_outputs_spec.md](docs/specs/reporting_outputs_spec.md) |
| Canonical candidate comparison JSON | [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md) |
| Robustness Scorecard JSON | [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md) |
| Portfolio Health Score JSON | [docs/specs/portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md) |
| Selection decision JSON | [docs/specs/selection_engine_spec.md](docs/specs/selection_engine_spec.md) |
| Monitoring snapshot and diff JSON | [docs/specs/monitoring_spec.md](docs/specs/monitoring_spec.md) |
| Metric formulas, windows, estimators, rounding | [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md) |
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
- `run_optimization.py`, `run_report.py`, or candidate scripts change what they write
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
