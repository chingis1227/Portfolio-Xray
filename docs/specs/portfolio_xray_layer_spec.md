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
- `sections`: seven keys in fixed order (see `XRAY_SECTION_KEYS` in code)
- `legacy_summary`: backward-compatible v1-style summary

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
| `stress_report.json` | `src/stress.py` export | 2.3, 2.6, 2.7 |
| `rc_vol_{10y,5y,3y}.csv` | `results_csv/` via `load_rc_vol_map_from_csv` | 2.6, 2.4 |
| Taxonomy YAML | `config/etf_universe.yml`, `config/stock_universe.yml` | 2.1, 2.4, 2.7 |
| `XRAY_THRESHOLDS` | `src/portfolio_xray.py` | 2.4, 2.5, 2.7 (rule thresholds only) |

## Sub-block implementation map

### 2.1 Asset Allocation

- Core implementation: `src/portfolio_xray.py` — `_allocation_section`
- Spec ownership: [portfolio_xray_diagnostics_spec.md](portfolio_xray_diagnostics_spec.md) §2.1
- Taxonomy helpers: `src/risk_budgeting.py` (`risk_budget_bucket_from_row`)
- Tests: `test_portfolio_xray_weight_concentration_in_asset_allocation`, taxonomy partial / unknown weight warnings

### 2.2 Portfolio Metrics / Risk Diagnostics

- Core implementation: `src/portfolio_xray.py` — `_risk_diagnostics_section`
- Spec ownership: diagnostics spec §2.2; formulas in [metrics_specification.md](metrics_specification.md)
- Metrics owner: `src/metrics_portfolio.py`, snapshot `metrics` blocks
- Tail risk: daily historical VaR/ES via `portfolio_analytics.tail_risk` (not recomputed in X-Ray)
- Multi-window panel: `load_portfolio_windows_from_dir` + `multi_window_metrics` item (Session 05)
- Tests: `test_portfolio_xray_section_provenance_metadata`,
  `test_portfolio_xray_multi_window_metrics_panel`, `test_portfolio_xray_ttr_in_primary_risk_metrics`,
  `tests/test_portfolio_metrics_deepening.py`, `tests/test_tail_risk.py`

### 2.3 Factor Exposure / Factor Sensitivity

- Core implementation: `src/portfolio_xray.py` — `_factor_exposure_section`
- Spec ownership: diagnostics spec §2.3;
  [factor_diagnostics_spec.md](factor_diagnostics_spec.md),
  [stress_testing_spec.md](stress_testing_spec.md) §8 (betas, inference)
- Stress owner: `src/stress_factors.py`, `stress_report` factor blocks
- Read-only panels: OLS/HAC `factor_regression_inference` from `factor_regression_5y/10y` (Session 04)
- Kalman: `stress_report.factor_betas_kalman.latest` (legacy field names fallback only)
- Tests: `test_portfolio_xray_factor_regression_inference_panel`,
  `test_portfolio_xray_v2_kalman_reads_factor_betas_kalman_latest`

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
