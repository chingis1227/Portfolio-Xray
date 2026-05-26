# Portfolio X-Ray Layer Specification

Status: active source-of-truth for Block 2 (Portfolio X-Ray) implementation boundary.

This document maps sub-blocks 2.1 to 2.7 into current code contracts. It is diagnostic-only and
does not override mandate gates, stress pass/fail, optimizer weights, or candidate selection.

Detailed section contracts, thresholds, and field-level JSON rules live in
[portfolio_xray_diagnostics_spec.md](portfolio_xray_diagnostics_spec.md). Methodology provenance and
audit gaps are tracked in
[Portfolio X-Ray Methodology Map](../audits/2026-05-20_portfolio_xray_methodology_map.md).

## Scope

Portfolio X-Ray covers the current `analysis_subject` before candidates and the decision package:

- 2.1 Asset Allocation
- 2.2 Portfolio Metrics / Risk Diagnostics
- 2.3 Factor Exposure / Factor Sensitivity
- 2.4 Hidden Exposure / Hidden Risk Detector
- 2.5 Portfolio Archetype Classification
- 2.6 Risk Budget View
- 2.7 Portfolio Weakness Map

## Workflow position

```text
run_report.py (--materialize-analysis-subject) / snapshot rebuild
  -> snapshots, stress_report, results_csv, taxonomy, in-memory analytics
  -> build_portfolio_xray_v2 (src/portfolio_xray.py)
  -> portfolio_xray.json
  -> report.txt / report.html / commentary.txt (format_portfolio_xray_*)
```

Orchestration entry points:

- `src/snapshot.py` — `_xray_summary_from_output_dir` writes `{output_dir}/portfolio_xray.json`
  and embeds X-Ray in HTML/text reports.
- `run_report.py` — materializes `analysis_subject/` and passes pipeline outputs into the builder.
- `run_portfolio_review.py` — portfolio-first review consumes the same subject folder artifacts.

## Current contract

Primary artifact: `portfolio_xray.json` under the active portfolio output folder (portfolio-first:
`{output_dir_final}/analysis_subject/portfolio_xray.json`).

Required top-level fields (v2):

- `version`: `portfolio_xray_v2`
- `diagnostic_only`: `true`
- `diagnostic_only_disclaimer`
- `analysis_setup_summary`
- `thresholds`: copy of `XRAY_THRESHOLDS` (canonical registry in diagnostics spec §8)
- `block_2_1_asset_allocation`: product Block 2.1 capital structure contract
- `block_2_2_portfolio_metrics`: product Block 2.2 portfolio behavior contract
- `block_2_3_factor_exposure`: product Block 2.3 factor sensitivity contract
- `sections`: seven keys in fixed order (see `XRAY_SECTION_KEYS` in code)
- `legacy_summary`: backward-compatible v1-style summary
- `data_trust_signals` (`xray_data_trust_signals_v1`, RM-1016): rollup of section `warnings` plus
  optional `stress_report.data_trust_summary` lines for commentary; does not change X-Ray formulas.

Section JSON keys (stable; match `sections` in the artifact):

| Block | `sections` key |
| --- | --- |
| 2.1 | `asset_allocation` |
| 2.2 | `risk_diagnostics` |
| 2.3 | `factor_exposure` |
| 2.4 | `hidden_risk_detector` |
| 2.5 | `portfolio_archetype` |
| 2.6 | `risk_budget_view` |
| 2.7 | `weakness_map` |

Common section envelope (where implemented): `status`, `data_sources_used`, `method`, `frequency`,
`window`, `n_obs`, `benchmark`, `items`, `warnings`, `limitations`, `confidence`.

## Upstream inputs (do not recompute in X-Ray)

`build_portfolio_xray_v2` summarizes existing pipeline outputs only. Canonical formulas remain in
owning modules/specs:

| Input | Typical source | Used by |
| --- | --- | --- |
| Weights, `analysis_setup` | config / snapshot | 2.1, 2.6, 2.4 |
| `portfolio_metrics`, multi-window snapshots | `snapshot_{3y,5y,10y}.json` | 2.2 |
| `portfolio_analytics`, `drawdown_structure` | snapshot / report analytics | 2.2, 2.4, 2.5, 2.7 |
| `stress_report.json` | `src/stress.py` / `src/stress_factors.py` export | 2.3, 2.6, 2.7 |
| `rc_vol_{10y,5y,3y}.csv` | `results_csv/` via `load_rc_vol_map_from_csv` | 2.6, 2.4 |
| Taxonomy YAML | `config/etf_universe.yml`, `config/stock_universe.yml` | 2.1, 2.4, 2.7 |
| `XRAY_THRESHOLDS` | `src/portfolio_xray.py` | 2.4, 2.5, 2.7 (rule thresholds only) |

## Sub-block implementation map

### 2.1 Asset Allocation

- Legacy section builder: `src/portfolio_xray.py` — `_allocation_section` → `sections.asset_allocation`
- **Block 2.1 product contract (MVP):** `src/block_2_1_asset_allocation.py` — `build_block_2_1_asset_allocation` → top-level `block_2_1_asset_allocation` on `portfolio_xray.json` (wired from `build_portfolio_xray_v2`; ExecPlan **Completed** 2026-05-26)
- Spec ownership: [portfolio_xray_diagnostics_spec.md](portfolio_xray_diagnostics_spec.md) §2.1, §2.1.1, §2.1.2
- Taxonomy helpers: `src/risk_budgeting.py` (`load_merged_universe_rows`, `risk_budget_bucket_from_row`); real cash: `src/real_cash.py` + synthetic row in Block 2.1 builder
- Weight source: `src/analysis_setup.py` — `resolved_analysis_weights` (explicit snapshot weights override; else `analysis_portfolio.weights` from Input Layer)
- ExecPlan (completed): [2026-05-26_block_2_1_asset_allocation_plan.md](../exec_plans/2026-05-26_block_2_1_asset_allocation_plan.md); acceptance [audit](../audits/2026-05-26_block_2_1_asset_allocation_acceptance_audit.md)
- Tests (legacy): `test_portfolio_xray_weight_concentration_in_asset_allocation`, taxonomy partial / unknown weight warnings
- Tests (Block 2.1 MVP): `tests/test_block_2_1_asset_allocation.py`, `tests/test_block_2_1_threshold_registry.py`, `tests/test_block_2_1_pipeline_integration.py`

### 2.2 Portfolio Metrics / Risk Diagnostics

- Legacy section builder: `src/portfolio_xray.py` — `_risk_diagnostics_section` → `sections.risk_diagnostics`
- **Block 2.2 product contract (MVP):** `src/block_2_2_portfolio_metrics.py` — `build_block_2_2_portfolio_metrics` → top-level `block_2_2_portfolio_metrics` on `portfolio_xray.json` (wired from `build_portfolio_xray_v2`; ExecPlan **Active**, builder Session 03, 2026-05-26)
- Spec ownership: [portfolio_xray_diagnostics_spec.md](portfolio_xray_diagnostics_spec.md) §2.2, §2.2.1; formulas in [metrics_specification.md](metrics_specification.md)
- Metrics owner: `src/metrics_portfolio.py` — `portfolio_metrics_one_window` → snapshot `metrics` (Session 03 adds `downside_deviation`)
- Analytics owner: `src/portfolio_analytics.py` — `drawdown_structure`, `compute_tail_risk_historical`, `rolling_summary`; snapshot `analytics`, `drawdown_structure`
- Report pipeline: `run_report.py` STEP 7–8 (metrics, RC/corr CSV, rolling CSV, tail risk)
- Tail risk: daily historical VaR/ES via `portfolio_analytics.tail_risk` (not recomputed in X-Ray)
- Correlation matrix CSV: `src/io_export.py` — `correlation_matrix_{3y,5y,10y}.csv` under `results_csv/`; Block 2.2 top-3 pairs from primary matrix (Session 03)
- Multi-window panel (legacy only): `load_portfolio_windows_from_dir` + `multi_window_metrics` item
- ExecPlan (active): [2026-05-26_block_2_2_portfolio_metrics_plan.md](../exec_plans/2026-05-26_block_2_2_portfolio_metrics_plan.md); acceptance audit planned Session 08
- Tests (legacy): `test_portfolio_xray_section_provenance_metadata`,
  `test_portfolio_xray_multi_window_metrics_panel`, `test_portfolio_xray_ttr_in_primary_risk_metrics`,
  `tests/test_portfolio_metrics_deepening.py`, `tests/test_tail_risk.py`
- Tests (Block 2.2 MVP, planned): `tests/test_block_2_2_portfolio_metrics.py`, pipeline/E2E gates Session 07+

### 2.3 Factor Exposure / Factor Sensitivity

- Legacy section implementation: `src/portfolio_xray.py` — `_factor_exposure_section` -> `sections.factor_exposure`
- **Block 2.3 product contract (MVP):** `src/block_2_3_factor_exposure.py` — `build_block_2_3_factor_exposure` -> top-level `block_2_3_factor_exposure` on `portfolio_xray.json` (wired from `build_portfolio_xray_v2`; ExecPlan active 2026-05-26)
- Spec ownership: diagnostics spec §2.3;
  [factor_diagnostics_spec.md](factor_diagnostics_spec.md),
  [stress_testing_spec.md](stress_testing_spec.md) §8 (betas, inference)
- Stress owner: `src/stress_factors.py`, `stress_report` factor blocks
- Architecture boundary: Block 2.3 reads existing `stress_report` fields only and must not trigger OLS/HAC, Kalman, variance-decomposition, data-loading, candidate, or Stress Lab calculations. Missing fields degrade to `partial` / `unavailable`; upstream stress-report generation owns the fix.
- Read-only panels: OLS/HAC `factor_regression_inference` from `factor_regression_5y/10y` (Session 04)
- Kalman: `stress_report.factor_betas_kalman.latest` (legacy field names fallback only)
- Unavailable diagnostics: when factor beta/decomposition evidence is absent, `factor_exposure` remains `status: unavailable` and includes a structured `factor_exposure_unavailable` item sourced from `stress_report.factor_diagnostics_meta` with the user-readable reason.
- Tests: `test_portfolio_xray_factor_regression_inference_panel`,
  `test_portfolio_xray_v2_kalman_reads_factor_betas_kalman_latest`,
  `test_factor_exposure_unavailable_has_structured_reason`,
  `tests/test_block_2_3_factor_exposure.py`,
  `tests/test_block_2_3_pipeline_integration.py`

### 2.4 Hidden Exposure / Hidden Risk Detector

- Core implementation: `src/portfolio_xray.py` — `_hidden_risk_section`,
  `_hidden_risk_section_confidence`
- Spec ownership: diagnostics spec §2.4
- Rule engine: category order `HIDDEN_RISK_CATEGORY_ORDER`; thresholds from `XRAY_THRESHOLDS`
- Tests: hidden-risk flagged / below-threshold / unavailable cases in `tests/test_portfolio_xray.py`
- Drift guard: `tests/test_portfolio_xray_threshold_registry.py`

### 2.5 Portfolio Archetype Classification

- Core implementation: `src/portfolio_xray.py` — `_portfolio_archetype_section`
- Spec ownership: diagnostics spec §2.5
- Build order: **after** `weakness_map` so `conflicting_signals` can reference regime tensions
- Tests: archetype scorecard / conflict tests in `tests/test_portfolio_xray.py`

### 2.6 Risk Budget View

- Core implementation: `src/portfolio_xray.py` — `_risk_budget_section`,
  `resolve_rc_asset_for_xray`, `load_rc_vol_map_from_csv`
- Spec ownership: diagnostics spec §2.6; RC formula in [metrics_specification.md](metrics_specification.md)
- Evidence priority: full `rc_vol_10y.csv` → `rc_vol_5y.csv` → `rc_vol_3y.csv` → snapshot `RC_asset` top-N gap-fill
- Stress loss contrib: min `pnl_by_asset_pct` across scenarios (read-only)
- Deferred: factor RC, drawdown contribution, ES contribution by asset (methodology map G7)
- Tests: `test_resolve_rc_asset_prefers_full_csv_over_snapshot_top5`, provenance metadata test

### 2.7 Portfolio Weakness Map

- Core implementation: `src/portfolio_xray.py` — `_weakness_map_section`, `WEAKNESS_SCENARIO_MAP`
- Spec ownership: diagnostics spec §2.7; scenario names in [stress_testing_spec.md](stress_testing_spec.md)
- V2 fields: `exposure_present`, `adverse_evidence`, `severity`, `confidence`, `scenario_coverage`, drivers
- `volatility_spike` weakness row: **factor-only (Option B, `RM-948`)** — `beta_vix` + historical `es_95`; no synthetic scenario mapping
- Tests: weakness V2, crypto conditional, low-risk not overstated in `tests/test_portfolio_xray.py`

## Report surfaces

User-facing rendering (diagnostic tables, section order, English prose policy):

- Text: `format_portfolio_xray_text` in `src/portfolio_xray.py`
- HTML: `format_portfolio_xray_html`
- PDF-facing Markdown: `src/pdf_reports.py` (client summaries; not a raw JSON dump)

`commentary.txt` in portfolio folders follows [portfolio-commentary](../../.cursor/rules/portfolio-commentary.mdc)
rules separately from X-Ray JSON.

## Non-goals

- No portfolio optimization, weight changes, or mandate release from X-Ray diagnostics.
- No candidate selection or binding buy/sell/hold recommendations.
- No alternate formulas for metrics, RC_vol, factor betas, VaR/ES, or stress PnL inside the X-Ray builder.
- No UI product surface in this layer spec (CLI/file artifacts only).

## Post-audit governance wave (Phase 12)

Active ExecPlan:
[Portfolio X-Ray Post-Audit Roadmap](../exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md).

| Session | RM ID | Focus |
| --- | --- | --- |
| 07 | RM-947 | Allocation concentration (HHI, top-N) — **Done** |
| 08 | RM-948 | `volatility_spike` methodology — **Done** |
| 09 | RM-949 | Golden JSON contract tests — **Done** |
| 10 | RM-950 | Baseline snapshot audit + wave closure |

Historical deepening audit (Sessions 00–09, `RM-930`–`RM-939`):
[2026-05-19_portfolio_xray_layer_audit.md](../audits/2026-05-19_portfolio_xray_layer_audit.md).
