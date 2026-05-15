# Reporting Outputs Specification

This document owns the detailed report and artifact contract. The root output map is [../../OUTPUTS.md](../../OUTPUTS.md). Detailed metric formulas are in [metrics_specification.md](metrics_specification.md), stress artifacts are in [stress_testing_spec.md](stress_testing_spec.md), and production status semantics are in [production_workflow.md](production_workflow.md).

## Main Report Flow

`run_report.py` and shared report helpers produce decision-ready artifacts for the main policy portfolio and candidate portfolios.

Primary report responsibilities:

- load fixed weights for the target portfolio
- build portfolio metrics and diagnostics
- run stress and factor diagnostics
- build scenario libraries where inputs are available
- export CSV, JSON, HTML, TXT, and PDF-style artifacts
- generate English-only UTF-8 commentary files

## Primary Outputs

Common outputs include:

- `run_result.json`
- `stress_report.json`
- `run_metadata.json`
- metric CSV files under `results_csv/`
- stress and scenario CSV files under `results_csv/`
- `commentary.txt`
- `stress_commentary.txt`
- generated HTML snapshots
- PDF-style reports under configured output folders

Variant folders follow the same report contract after their candidate weights are fixed.

## Output Rules

Reported numeric metrics are rounded only at final export/report stage. Internal calculations preserve full precision.

Generated outputs are not source files unless the task explicitly targets generated artifacts.

## Detailed Ownership

- Metrics and rounding: [metrics_specification.md](metrics_specification.md)
- Stress and factor artifact contracts: [stress_testing_spec.md](stress_testing_spec.md)
- Scenario Library outputs: [scenario_library_spec.md](scenario_library_spec.md)
- Production statuses: [production_workflow.md](production_workflow.md)
