# Candidate Comparison Specification

This document owns the canonical **Candidate Comparison** artifact contract. It defines how multiple portfolio candidates are assembled into one machine-readable comparison table for diagnostics, scorecards, selection, monitoring, and report surfaces.

It does not own metric formulas, stress scenarios, candidate construction methods, or optimizer policy. Those remain in [metrics_specification.md](metrics_specification.md), [stress_testing_spec.md](stress_testing_spec.md), [candidate_portfolios_spec.md](candidate_portfolios_spec.md), and [portfolio_construction_policy.md](portfolio_construction_policy.md).

## Scope

The Candidate Comparison layer:

- reads **existing** per-candidate report artifacts (snapshots, stress reports, run metadata);
- normalizes them into one JSON contract;
- marks candidates `available`, `unavailable`, or `degraded`;
- stays **diagnostic-only** (no selection, no-trade, ranking, or trade instructions).

Implementation: `src/candidate_comparison.py` (builder) and `run_compare_variants.py` (CLI). Legacy `portfolio_comparison.json` / `ew_rp_comparison.json` remain for backward compatibility.

## Product Boundary

- Comparison output is **evidence for decision support**, not a recommendation.
- Wording in downstream reports must not imply "choose this portfolio" unless [selection_engine_spec.md](selection_engine_spec.md) decision artifacts and reporting rules explicitly allow decision-support phrasing for that surface.
- Portfolio X-Ray, commentary, and stress diagnostics remain non-binding inputs; comparison does not override them.

## Canonical Artifact

| Field | Value |
| --- | --- |
| File name | `candidate_comparison.json` |
| Location | `{output_dir_final}/candidate_comparison.json` (default folder: `Main portfolio/`) |
| Companion (optional) | `{output_dir_final}/candidate_comparison.txt` - human-readable summary table |
| Schema version | `candidate_comparison_v1` |

`output_dir_final` is the configured main output folder from `config.yml` (see [input_assumptions_spec.md](input_assumptions_spec.md)).

Do not place the canonical file under a separate project-root `comparison/` folder in V1.

## V1 User Decisions (2026-05-17)

Recorded for Session 08:

1. **Candidate set:** full registry of supported families; each row may be `unavailable` when its artifact folder or required files are missing.
2. **Current portfolio:** include candidate `current` (role `user_current`) when the user runs or has materialized a current-portfolio report (`analyze_current_weights` or equivalent artifacts tagged `user_current_portfolio`).
3. **Location:** single canonical JSON under `output_dir_final` (Main).

## Top-Level JSON Contract

```json
{
  "schema_version": "candidate_comparison_v1",
  "diagnostic_only": true,
  "generated_at": "ISO-8601 timestamp",
  "analysis_end": "YYYY-MM-DD",
  "investor_currency": "USD",
  "output_dir_final": "Main portfolio",
  "analysis_setup_summary": { },
  "windows": ["3y", "5y", "10y"],
  "primary_window": "10y",
  "candidates": [ ],
  "legacy_artifacts": {
    "portfolio_comparison_json": "portfolio_comparison.json",
    "ew_rp_comparison_json": "ew_rp_comparison.json"
  },
  "warnings": [ ]
}
```

### Required top-level fields

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | string | Always `candidate_comparison_v1` for this contract. |
| `diagnostic_only` | bool | Always `true` in V1. |
| `generated_at` | string | UTC or local ISO timestamp when the file was written. |
| `analysis_end` | string | Effective month-end used for windows (from config or dominant snapshot). |
| `investor_currency` | string | Investor currency code. |
| `output_dir_final` | string | Relative or absolute path to main output folder. |
| `analysis_setup_summary` | object | Projected summary from `analysis_setup` / `input_assumptions` (mode, roles, weight sources). |
| `windows` | array | Window labels present in the comparison (`3y`, `5y`, `10y`). |
| `primary_window` | string | Default window for summary tables (V1: `10y`). |
| `candidates` | array | One object per registered candidate (see below). |
| `legacy_artifacts` | object | Paths to pre-canonical comparison files, if present. |
| `warnings` | array | Run-level warnings (stale artifacts, mixed analysis dates, partial coverage). |

## Candidate Object Contract

Each element of `candidates[]`:

```json
{
  "candidate_id": "equal_weight",
  "display_name": "Equal-Weight Portfolio",
  "role": "benchmark",
  "construction_method": "equal_weight_by_asset",
  "weight_source": "candidate_script.fixed_weights",
  "artifact_root": "equal-weight portfolio",
  "status": "available",
  "unavailable_reason": null,
  "portfolio_role": null,
  "recommendation_status": null,
  "metrics": { },
  "stress": { },
  "drawdown": { },
  "factor_regime": { },
  "mandate": { },
  "missing_fields": [ ],
  "warnings": [ ],
  "source_files": [ ]
}
```

### Identity and metadata

| Field | Required | Description |
| --- | --- | --- |
| `candidate_id` | yes | Stable machine id (snake_case, see registry). |
| `display_name` | yes | English label for reports. |
| `role` | yes | `policy` \| `user_current` \| `benchmark` \| `optimizer_candidate` \| `robust_candidate`. |
| `construction_method` | yes | Short id matching candidate family (e.g. `risk_parity`, `minimum_cvar_constrained`). |
| `weight_source` | yes | How weights were fixed (e.g. `optimization_result_released`, `config.current_weights`, `candidate_script.fixed_weights`). |
| `artifact_root` | yes | Project-relative folder containing that candidate's report outputs, or `output_dir_final` for policy/current on Main. |
| `status` | yes | `available` \| `unavailable` \| `degraded`. |
| `unavailable_reason` | if unavailable | Machine code, e.g. `missing_artifact_folder`, `missing_snapshot`, `not_applicable_for_analysis_mode`. |
| `portfolio_role` | when known | From `analysis_setup.analysis_portfolio.portfolio_role` when this row is the analyzed Main report. |
| `recommendation_status` | when known | From run metadata; must not be interpreted as advice. |

### Status rules

| Status | Meaning |
| --- | --- |
| `available` | Required primary-window metrics and stress summary loaded successfully. |
| `degraded` | Partial data (e.g. metrics without stress, or only `summary.json` fallback). List gaps in `missing_fields` and `warnings`. |
| `unavailable` | Candidate is in the V1 registry but artifacts are missing or not applicable for this run. |

**Do not omit** registry candidates from `candidates[]` when artifacts are missing; emit them with `status: unavailable` and a clear `unavailable_reason`.

## Metric, Stress, and Diagnostic Blocks

All numeric values follow [metrics_specification.md](metrics_specification.md) rounding: **three decimals at export only**. The comparison builder must not recompute canonical metrics with alternate formulas; it aggregates from existing artifacts.

### `metrics` (per window)

Keyed by `3y`, `5y`, `10y`. Each window object may include:

| Field | Source priority |
| --- | --- |
| `cagr`, `vol_annual`, `max_drawdown`, `sharpe`, `sortino`, `beta_portfolio` | `snapshot_{window}.json` → `metrics`; else `summary.json` → `metrics_{window}` |
| `correlation_benchmark` | snapshot or summary when present |

### `stress`

| Field | Source |
| --- | --- |
| `overall` | `snapshot_*`.stress_suite_results.overall or `summary.json`.stress_status |
| `fail_reason_code`, `failed_scenario` | stress suite or `stress_report.json` |
| `scenarios` | optional abbreviated list from snapshot stress suite |

### `drawdown`

| Field | Source |
| --- | --- |
| `max_drawdown` | metrics block (duplicate allowed for convenience) |
| `recovered`, `time_to_recovery_months` | snapshot metrics when present |

### `factor_regime`

Optional in V1. Populate when `stress_report.json` or snapshot embeds factor/regime summaries:

| Field | Source |
| --- | --- |
| `factor_regression_5y`, `factor_regression_10y` | `stress_report.json` (betas + HAC inference blocks per stress spec) |
| `macro_regime` | macro/regime artifacts when present in candidate folder |

### `mandate`

| Field | Source |
| --- | --- |
| `portfolio_valid`, `client_fit` | `run_metadata.json`, `summary.json`, or snapshot constraints |
| `constraints_status` | snapshot.constraints_status when present |

### `diversification` (comparison v1.1 — Session 11)

Required for [Robustness Scorecard](robustness_scorecard_spec.md) `diversification_rc` component. Populated from `snapshot_10y.json` `RC_asset` when present (Session 11).

| Field | Source |
| --- | --- |
| `top1_rc_asset`, `top1_rc_pct` | `snapshot_10y.json` -> `RC_asset[0]` (ticker, `rc_pct`) |
| `top3_rc_assets`, `top3_rc_sum_pct` | sum of top three `RC_asset` rows by `rc_pct` |
| `rc_hhi` | optional Herfindahl of `RC_asset` shares when implemented |
| `source_window` | `10y` |

When snapshot has no `RC_asset`, leave block empty and list `diversification` in `missing_fields`.

### `weight_concentration` (comparison v1.2 — Session 13)

Required for [Portfolio Health Score](portfolio_health_score_spec.md) `weight_concentration` component. Populated from `snapshot_10y.json` `final_weights_total` when present (Session 13).

| Field | Source |
| --- | --- |
| `top1_weight_asset`, `top1_weight_pct` | largest weight in `final_weights_total` |
| `top3_weight_assets`, `top3_weight_sum_pct` | top three weights by pct |
| `weight_hhi` | optional Herfindahl of weight shares when implemented |
| `source` | `snapshot_10y.final_weights_total` |

When snapshot has no weight block, leave empty and list `weight_concentration` in `missing_fields`.

### `source_files`

Relative paths from repo root or `artifact_root` for auditability, e.g. `snapshot_10y.json`, `stress_report.json`, `run_metadata.json`.

## Candidate Registry (V1 Full Set)

Project root is the repository root. `artifact_root` is relative to project root unless noted.

### Core decision rows

| candidate_id | role | construction_method | artifact_root | Notes |
| --- | --- | --- | --- | --- |
| `policy` | `policy` | `policy_optimizer` | `{output_dir_final}` | Optimizer-released weights; Main report after `run_optimization` + `run_report`. |
| `current` | `user_current` | `user_supplied_weights` | `{output_dir_final}` | **Included when** `analysis_mode=analyze_current_weights` **or** Main `run_metadata` / `analysis_setup` shows `portfolio_role=user_current_portfolio`. If `current_weights` exist in config but no report was run, status `unavailable`, reason `missing_current_report`. |
| `equal_weight` | `benchmark` | `equal_weight_by_asset` | `equal-weight portfolio` | |
| `risk_parity` | `benchmark` | `risk_parity` | `risk parity portfolio` | |
| `robust_scenario` | `robust_candidate` | `scenario_robust_optimization` | `robust scenario portfolio` | |

### Optimizer / baseline candidates (same registry; may be unavailable)

| candidate_id | role | construction_method | artifact_root |
| --- | --- | --- | --- |
| `robust_mv_constrained` | `optimizer_candidate` | `robust_mean_variance_constrained` | `robust mean variance constrained portfolio` |
| `robust_mv_uncapped` | `optimizer_candidate` | `robust_mean_variance_uncapped` | `robust mean variance uncapped portfolio` |
| `minimum_variance` | `optimizer_candidate` | `minimum_variance_constrained` | `minimum variance portfolio` |
| `minimum_variance_uncapped` | `optimizer_candidate` | `minimum_variance_uncapped` | `minimum variance uncapped portfolio` |
| `minimum_variance_advanced` | `optimizer_candidate` | `minimum_variance_advanced` | `minimum variance advanced portfolio` |
| `maximum_diversification` | `optimizer_candidate` | `maximum_diversification_constrained` | `maximum diversification portfolio` |
| `maximum_diversification_uncapped` | `optimizer_candidate` | `maximum_diversification_unconstrained` | `maximum diversification unconstrained portfolio` |
| `minimum_cvar_constrained` | `optimizer_candidate` | `minimum_cvar_constrained` | `minimum cvar constrained portfolio` |
| `minimum_cvar_uncapped` | `optimizer_candidate` | `minimum_cvar_uncapped` | `minimum cvar uncapped portfolio` |
| `equal_weight_by_asset_class` | `benchmark` | `equal_weight_by_asset_class` | `equal-weight by asset-class portfolio` |
| `risk_budget_by_asset_class` | `benchmark` | `risk_budget_by_asset_class` | `risk budget by asset-class portfolio` |
| `risk_budget_by_asset` | `benchmark` | `risk_budget_by_asset` | `risk budget by asset portfolio` |
| `hierarchical_risk_parity` | `benchmark` | `hierarchical_risk_parity` | `hierarchical risk parity portfolio` |

Construction methods and script entry points are defined in [candidate_portfolios_spec.md](candidate_portfolios_spec.md).

### Policy vs current on the same folder

`policy` and `current` both use `{output_dir_final}` but are **not** both `available` from a single config mode:

- `optimize_from_universe`: expect `policy` available when optimization/report artifacts exist; `current` is `unavailable` unless a separate current-portfolio report was materialized with `user_current_portfolio` tagging (future builder may support explicit refresh).
- `analyze_current_weights`: expect `current` available from Main report; `policy` is `unavailable` with reason `not_applicable_for_analysis_mode` unless a prior optimization snapshot still exists and is explicitly linked (then `degraded` with warning `stale_policy_snapshot`).

## Assembly Rules

The comparison builder must:

1. Load config and resolve `output_dir_final`.
2. Iterate the V1 registry in stable order: `policy`, `current`, then remaining ids alphabetically by `candidate_id` (or fixed table order above).
3. For each row, resolve `artifact_root`; if the folder or minimum files are missing, emit `unavailable`.
4. Minimum files for `available`: `snapshot_10y.json` **or** (`summary.json` with `metrics_10y`).
5. Prefer snapshot over summary for all blocks.
6. Copy `analysis_setup_summary` from Main `run_result.json` or `run_metadata.json` when present.
7. Write `candidate_comparison.json` to `output_dir_final`.
8. Optionally refresh legacy `portfolio_comparison.json` for backward compatibility (subset: policy, equal_weight, risk_parity, robust_scenario).

The builder must **not** call the optimizer or candidate scripts; it only reads artifacts.

## Downstream Decision-Package Wiring

`write_candidate_comparison_outputs` is the V1 orchestration point for the generated decision package.
After journal export it also writes the compact report summary via
[decision_package_reporting_spec.md](decision_package_reporting_spec.md).
After writing `candidate_comparison.json`, it writes the existing downstream artifacts in this order:
`robustness_scorecard.json`, `portfolio_health_score.json`, `selection_decision.json`,
`action_plan.json`, `monitoring_diff.json`, and `decision_journal.json` when their required inputs are
available.

This wiring does not change the comparison artifact boundary. `candidate_comparison.json` remains
`diagnostic_only: true`; the formal decision status lives only in `selection_decision.json`, the
implementation-plan surface lives only in `action_plan.json`, temporal change evidence lives in
`monitoring_diff.json`, and the run-level process record lives in `decision_journal.json`.

## Legacy Artifacts

| File | Producer | V1 status |
| --- | --- | --- |
| `portfolio_comparison.json` | `run_compare_variants.py` | Legacy subset; keep until reports migrate to canonical file. |
| `ew_rp_comparison.json` | `run_compare_ew_rp.py` | Legacy EW vs RP deep comparison; optional cross-link in `legacy_artifacts`. |

Canonical consumers (Robustness Scorecard, Health Score, Selection Engine) must read `candidate_comparison.json`, not legacy files.

## Human-Readable Summary

`candidate_comparison.txt` is optional. When written, it should list `display_name`, primary-window CAGR, vol, max drawdown, Sharpe, stress overall, and mandate/client-fit in a fixed-width table. English only.

## Tests

Focused tests should cover:

- schema version and required top-level keys;
- full registry length and stable ordering;
- `unavailable` when folder missing;
- `current` available vs unavailable by analysis mode;
- `degraded` when only `summary.json` exists;
- no duplicate formulas (mock snapshots, assert passthrough values).

## Detailed Ownership

| Area | Spec |
| --- | --- |
| Candidate construction | [candidate_portfolios_spec.md](candidate_portfolios_spec.md) |
| Input modes and current weights | [input_assumptions_spec.md](input_assumptions_spec.md) |
| Report artifacts per portfolio | [reporting_outputs_spec.md](reporting_outputs_spec.md) |
| Output locations | [OUTPUTS.md](../../OUTPUTS.md) |
| Robustness Scorecard | [robustness_scorecard_spec.md](robustness_scorecard_spec.md) |
| Portfolio Health Score | [portfolio_health_score_spec.md](portfolio_health_score_spec.md) |
| Selection / No-Trade | [selection_engine_spec.md](selection_engine_spec.md) |
| Action Engine / Rebalancing Advisor | [action_engine_spec.md](action_engine_spec.md) |
| Monitoring / What Changed | [monitoring_spec.md](monitoring_spec.md) |
| Decision Journal | [decision_journal_spec.md](decision_journal_spec.md) |
