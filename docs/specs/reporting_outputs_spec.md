# Reporting Outputs Specification

This document owns the detailed report and artifact contract. The root output map is [../../OUTPUTS.md](../../OUTPUTS.md). Detailed metric formulas are in [metrics_specification.md](metrics_specification.md), stress artifacts are in [stress_testing_spec.md](stress_testing_spec.md), and production status semantics are in [production_workflow.md](production_workflow.md).

## Main Report Flow

`run_report.py` and shared report helpers produce decision-ready artifacts for the main policy portfolio and candidate portfolios.

Primary report responsibilities:

- load fixed weights for the target portfolio
- expose the resolved Analysis Setup Summary for the analyzed portfolio
- build portfolio metrics and diagnostics
- run stress and factor diagnostics
- summarize asset allocation and risk contribution diagnostics
- build scenario libraries where inputs are available
- emit an explanatory Portfolio Diagnostic Verdict without scores or recommendations
- export CSV, JSON, HTML, TXT, and PDF-style artifacts
- generate English-only UTF-8 commentary files

## Primary Outputs

Common outputs include:

- `run_result.json`
- `stress_report.json`
- `run_metadata.json`
- `portfolio_xray.json`
- metric CSV files under `results_csv/`
- stress and scenario CSV files under `results_csv/`
- `commentary.txt`
- `stress_commentary.txt`
- generated HTML snapshots
- PDF-style reports under configured output folders

`run_result.json` and `run_metadata.json` expose `analysis_setup`, the resolved runtime contract governed by [input_assumptions_spec.md](input_assumptions_spec.md). They also expose `input_assumptions`, the reporting/reproducibility view projected from `analysis_setup`.

Variant folders follow the same report contract after their candidate weights are fixed.

## Candidate Comparison

The canonical multi-candidate artifact is `candidate_comparison.json` written under
`output_dir_final` (default: `Main portfolio/`). It aggregates per-candidate snapshots,
stress summaries, and mandate metadata into one diagnostic-only JSON contract.

See [candidate_comparison_spec.md](candidate_comparison_spec.md). Legacy
`portfolio_comparison.json` and `ew_rp_comparison.json` remain for backward compatibility until
Session 09 migrates producers and consumers to the canonical file.

## Portfolio X-Ray Summary

`report.txt`, `report.html`, and `commentary.txt` must make the analyzed portfolio understandable without requiring the user to inspect raw JSON first.

The Portfolio X-Ray summary is explanatory only. It must not create a black-box score, ranking, recommendation, selection decision, no-trade decision, or trade instruction.

`portfolio_xray.json` is the structured Portfolio X-Ray v2 artifact. Its top-level contract is:

- `version: "portfolio_xray_v2"`
- `diagnostic_only: true`
- `diagnostic_only_disclaimer`
- `sections`

The X-Ray v2 sections are `asset_allocation`, `risk_diagnostics`, `factor_exposure`, `hidden_risk_detector`, `portfolio_archetype`, `risk_budget_view`, and `weakness_map`. Each section must expose `status`, `data_sources_used`, `warnings`, `items`, and `limitations`.

Portfolio X-Ray v2 consumes existing report pipeline outputs and in-memory diagnostics. It must not recompute canonical metrics with alternative formulas. It must not optimize, change weights, change mandate gates, change stress pass/fail status, create a Portfolio Health Score, create a Selection Engine, or make scoring-driven portfolio decisions.

It must show:

- what portfolio was analyzed, including `portfolio_role`, `weight_source`, and `recommendation_status`
- where main capital concentration sits, using existing analyzed weights
- where main risk concentration sits, using existing `RC_vol`
- whether the portfolio is user current, generated policy/fixed report, or baseline
- the main diagnostic concern based only on existing diagnostics such as mandate gate status, stress status/scenarios, metrics, and RC concentration

`RC_vol` remains diagnostic-only and must not become an optimizer gate or recommendation rule.

Hidden risk flags and archetype rules must use centralized named thresholds, and those thresholds must be documented and covered by focused tests. The Weakness Map is an evidence summary from existing diagnostics, not a forecasting model.

## Output Rules

Reported numeric metrics are rounded only at final export/report stage. Internal calculations preserve full precision.

Generated outputs are not source files unless the task explicitly targets generated artifacts.

## Detailed Ownership

- Metrics and rounding: [metrics_specification.md](metrics_specification.md)
- Stress and factor artifact contracts: [stress_testing_spec.md](stress_testing_spec.md)
- Scenario Library outputs: [scenario_library_spec.md](scenario_library_spec.md)
- Production statuses: [production_workflow.md](production_workflow.md)
