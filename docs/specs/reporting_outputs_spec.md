# Reporting Outputs Specification

This document owns the detailed report and artifact contract. The root output map is [../../OUTPUTS.md](../../OUTPUTS.md). Detailed metric formulas are in [metrics_specification.md](metrics_specification.md), stress artifacts are in [stress_testing_spec.md](stress_testing_spec.md), and production status semantics are in [production_workflow.md](production_workflow.md).

## Main Report Flow

`run_report.py` and shared report helpers produce decision-ready artifacts for the portfolio-first
`analysis_subject`, legacy policy portfolio, and candidate portfolios.

Default report execution uses the `site_api` output profile: JSON contracts and required cache only.
CSV, TXT, HTML, PNG, PDF, Markdown PDF sidecars, and CSS/visual assets are disabled by default and
are available only through explicit `full_report`, `legacy_export`, or PDF export commands. CSV
export code remains supported for audit, Excel review, debugging, and legacy reporting; CSV is not a
source of truth.

### Output profiles (`src/output_policy.py`)

| Profile | JSON + cache | Presentation exports |
| --- | --- | --- |
| `site_api` (CLI default) | Yes | None |
| `core_json` | Yes | None |
| `lightweight_comparison` | Yes | None |
| `full_report` | Yes | CSV, TXT, HTML, PNG |
| `legacy_export` | Yes | CSV, TXT, HTML, PNG, PDF, Markdown sidecars, CSS |

`run_report.py` accepts `--output-profile`. Legacy `report_profile=full` maps to `full_report` when
`--output-profile` is omitted. Each completed report run writes `output_manifest.json`
(`output_manifest_v1`) under `output_dir_final`.

### Command matrix (reporting)

| Use case | Command |
| --- | --- |
| Site/API report | `python run_report.py` |
| Full tabular + commentary export | `python run_report.py --output-profile full_report` |
| Legacy export + PDF sidecars | `python run_report.py --output-profile legacy_export` |
| Materialize portfolio-first subject | `python run_report.py --materialize-analysis-subject` |

Primary report responsibilities:

- load fixed weights for the target portfolio
- materialize resolved portfolio-first `analysis_subject` diagnostics to
  `{output_dir_final}/analysis_subject/` when invoked with `--materialize-analysis-subject`
- expose the resolved Analysis Setup Summary for the analyzed portfolio
- build portfolio metrics and diagnostics
- run stress and factor diagnostics
- summarize asset allocation and risk contribution diagnostics
- build scenario libraries where inputs are available
- emit an explanatory Portfolio Diagnostic Verdict without scores or recommendations
- export JSON by default, with CSV/HTML/TXT/PNG/PDF-style artifacts only in explicit export profiles
- generate English-only UTF-8 commentary files

## Primary Outputs

### Always (site/API profiles)

- `output_manifest.json` — artifact index for UI/API consumers
- `run_result.json`
- `stress_report.json`
- `run_metadata.json`
- `portfolio_xray.json`
- `client_fit_check.json` when the report run has Client Fit input; backend/CLI-compatible runs
  without Client Fit still write a `not_provided` Client Fit check on the portfolio-first subject path
- window snapshots (`snapshot_3y.json`, `snapshot_5y.json`, `snapshot_10y.json`, …)
- `scenario_library.json` / `scenario_library_normalized.json` when inputs allow

### Export profiles only (`full_report`, `legacy_export`)

- metric and diagnostic CSV files under `results_csv/`
- `commentary.txt`, `stress_commentary.txt`
- generated HTML snapshots and rolling-factor PNG/HTML when stress inputs succeed
- PDF-style reports and Markdown sidecars when `legacy_export` or explicit PDF rebuild runs

### Decision package (after compare; JSON required, TXT export-only)

- decision-package artifacts under `output_dir_final`: `candidate_comparison.json`,
  `robustness_scorecard.json`, `portfolio_health_score.json`, `selection_decision.json`,
  `tradeoff_explanation.json`, `model_risk_diagnostics.json`, `action_plan.json`,
  `monitoring_diff.json`, and `decision_journal.json`

### Product-facing output bundle vs evidence artifacts

The reporting pipeline may write many JSON contracts after report or comparison runs. Product
surfaces should present the diagnosis-first bundle before lower-level technical and advanced
evidence. This categorization does not rename files, fields, schemas, or owning specs.

| Category | Artifacts | Intended consumer |
| --- | --- | --- |
| **Core MVP product bundle** | `problem_classification.json`, `candidate_launchpad.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, `what_changed_summary.json` | Product/UI/API surfaces that explain the diagnosis-first flow. `ai_commentary_context.json` is deterministic grounding for a future commentary generator only; it is not generated AI prose and does not replace `commentary.txt` / PDF report text. |
| **Client Fit context** | `client_fit_check.json`, plus Client Fit rows inside `site_explanation_bundle.json` / `ai_commentary_context.json` | Provided-profile context shown after Stress Lab and before Problem Classification. It must keep Client Fit status separate from diagnostic quality and must not introduce suitability, approval, best-portfolio, buy/sell, or must-rebalance language. |
| **Technical contracts** | `candidate_comparison.json`, `selection_decision.json`, `candidate_factory_run.json`, `candidate_factory_manifest.json`, `candidate_manifest.json`, `output_manifest.json` | Pipeline orchestration, API indexing, and deterministic evidence joins. |
| **Advanced / research evidence** | `portfolio_health_score.json`, `robustness_scorecard.json`, `assumption_sensitivity.json`, `pareto_dominance.json`, `regret_analysis.json`, `tradeoff_explanation.json`, `model_risk_diagnostics.json` | Drill-down review, robustness/research analysis, and confidence diagnostics. |
| **Action / monitoring / journal evidence** | `action_plan.json`, `monitoring_diff.json`, `decision_journal.json`, `decision_package_summary.json` | Implementation review, audit trail, reporting projection, and change tracking. |
| **Legacy / compatibility** | `run_result.json`, `portfolio_weights.yml`, `current_vs_policy_status.json`, `portfolio_comparison.json`, `ew_rp_comparison.json` | Legacy policy workflows and backwards-compatible readers. |

`run_result.json` and `run_metadata.json` expose `analysis_setup`, the resolved runtime contract governed by [input_assumptions_spec.md](input_assumptions_spec.md). They also expose `input_assumptions`, the reporting/reproducibility view projected from `analysis_setup`.

Variant folders follow the same report contract after their candidate weights are fixed.
The `analysis_subject/` sidecar follows the same report contract after subject weights are resolved
from `analysis_subject`, compatibility current weights, or a universe-baseline equal-weight
diagnostic baseline.

## Candidate Comparison

The canonical multi-candidate artifact is `candidate_comparison.json` written under
`output_dir_final` (default: `Main portfolio/`). It aggregates per-candidate snapshots,
stress summaries, and mandate metadata into one diagnostic-only JSON contract.

See [candidate_comparison_spec.md](candidate_comparison_spec.md). Legacy
`portfolio_comparison.json` and `ew_rp_comparison.json` remain for backward compatibility as
subset comparison files; new consumers should use `candidate_comparison.json`.

## Decision Package Artifact Chain (V1)

`run_compare_variants.py` calls `write_candidate_comparison_outputs`, which writes a file-first
decision-support package under `output_dir_final` after candidate report folders already exist. The
package is generated evidence and workflow output; it does not rewrite optimizer weights, rerun
candidate builders, execute trades, or override stress pass/fail.

The V1 artifact chain is technical evidence. Product consumers should prefer the product-facing
bundle above when it exists and use this chain for traceability, drill-down, and compatibility:

1. `candidate_comparison.json` / `.txt` - diagnostic table centered on the portfolio-first
   `analysis_subject` baseline when materialized, followed by supported candidate alternatives.
   Legacy policy/current rows may still appear for compatibility. Combined current-vs-policy
   materialization and No-Trade actionability:
   [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md).
2. `robustness_scorecard.json` / `.txt` - diagnostic resilience scorecard from the comparison table.
3. `portfolio_health_score.json` / `.txt` - diagnostic holistic health score from comparison plus
   optional robustness reference.
4. `selection_decision.json` / `.txt` - formal, non-executing decision record with one decision
   status and optional No-Trade materiality.
5. `tradeoff_explanation.json` / `.txt` and `model_risk_diagnostics.json` / `.txt` - diagnostic
   trade-off deltas (baseline vs favored) and unified model-risk warnings ([tradeoff_and_model_risk_spec.md](tradeoff_and_model_risk_spec.md); implementation post-audit Session 13).
6. `action_plan.json` / `.txt` - non-executing implementation plan, turnover, optional trade rows for
   review, and simple transaction-cost estimate.
7. `monitoring_diff.json` / `.txt` plus `monitoring/latest/` and `monitoring/history/` snapshots -
   generated What Changed evidence versus the prior run.
8. `decision_journal.json` / `.txt` plus `journal/latest/` and `journal/history/` copies - generated
   decision record and artifact index for the run.

Product-facing adapters written around this chain include `current_vs_candidate.json`,
`decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json`. Earlier
report-stage adapters include `problem_classification.json` and `candidate_launchpad.json`
(V1 shipped; V3 contract: [block_4_diagnosis_v3_spec.md](block_4_diagnosis_v3_spec.md)).

Compact report/PDF-facing summaries are defined in
[decision_package_reporting_spec.md](decision_package_reporting_spec.md) and implemented in
[src/decision_package_reporting.py](../../src/decision_package_reporting.py). After
`write_candidate_comparison_outputs` completes, the pipeline also writes:

- `decision_package_summary.txt` — primary English summary for humans and `report.txt` append
- `decision_package_summary.json` — `decision_package_report_v1` index with section availability
- `current_vs_policy_status.json` / `.txt` — workflow completeness and No-Trade actionability per [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md)

The per-artifact JSON/TXT files above remain the authoritative structured contracts; the summary is a
read-only projection for reports and PDF rebuild.

Portfolio-first review (`run_portfolio_review.py`) uses `site_api` by default and does **not**
rebuild PDFs. Pass `--with-pdf` for the narrow portfolio-first PDF subset (decision package plus
`analysis_subject/` sidecar). Pass `--legacy-full-pdf` or run bare `rebuild_pdf_reports.py` for the
full legacy variant PDF suite. See [portfolio_review_workflow_spec.md](portfolio_review_workflow_spec.md).

## Portfolio Diagnosis Summary

`report.txt`, `report.html`, and `commentary.txt` must make the analyzed portfolio understandable without requiring the user to inspect raw JSON first.

The Portfolio Diagnosis summary is explanatory only. It must not create a black-box score, ranking, recommendation, selection decision, no-trade decision, or trade instruction.

`portfolio_xray.json` is the structured Portfolio Diagnosis v2 artifact. Its top-level contract is:

- `version: "portfolio_xray_v2"`
- `diagnostic_only: true`
- `diagnostic_only_disclaimer`
- `sections`

The Diagnosis v2 sections are `asset_allocation`, `risk_diagnostics`, `factor_exposure`, `hidden_risk_detector`, `portfolio_archetype`, `risk_budget_view`, and `weakness_map`. Each section must expose `status`, `data_sources_used`, `warnings`, `items`, and `limitations`.

Portfolio Diagnosis v2 consumes existing report pipeline outputs and in-memory diagnostics. It must not recompute canonical metrics with alternative formulas. It must not optimize, change weights, change mandate gates, change stress pass/fail status, create a Portfolio Health Score, create a Selection Engine, or make scoring-driven portfolio decisions.

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
- Candidate comparison: [candidate_comparison_spec.md](candidate_comparison_spec.md)
- Robustness Scorecard: [robustness_scorecard_spec.md](robustness_scorecard_spec.md)
- Portfolio Health Score: [portfolio_health_score_spec.md](portfolio_health_score_spec.md)
- Selection / No-Trade: [selection_engine_spec.md](selection_engine_spec.md)
- Action Engine / Rebalancing Advisor: [action_engine_spec.md](action_engine_spec.md)
- Monitoring / What Changed: [monitoring_spec.md](monitoring_spec.md)
- Decision Journal: [decision_journal_spec.md](decision_journal_spec.md)
