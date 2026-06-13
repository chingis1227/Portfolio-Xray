# Monitoring and What Changed Specification

This document owns the **Monitoring** snapshot and **What Changed** (`monitoring_diff`) contract: non-binding, generated-only artifacts that compare the current analysis run to the most recent prior snapshot so the user can see how portfolio risk and formal decision outputs evolved over time.

It does not own metric formulas, stress scenarios, scorecard math, selection ranking, action trade mechanics, or optimizer release policy. Those remain in [metrics_specification.md](metrics_specification.md), [stress_testing_spec.md](stress_testing_spec.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [portfolio_health_score_spec.md](portfolio_health_score_spec.md), [robustness_scorecard_spec.md](robustness_scorecard_spec.md), [selection_engine_spec.md](selection_engine_spec.md), and [action_engine_spec.md](action_engine_spec.md).

Implementation: [src/monitoring.py](../../src/monitoring.py) (`analysis_snapshot_v1`, `monitoring_diff_v1`). This document is the contract.

## Scope

Monitoring V1:

- projects **analysis_subject**, **current**, and **policy** profile fields from existing decision-pipeline JSON (no new formulas);
- writes **`analysis_snapshot.json`** under `{output_dir_final}/monitoring/latest/` and archives a copy under `monitoring/history/` keyed by `analysis_end`;
- writes **`monitoring_diff.json`** (and optional **`monitoring_diff.txt`**) under `{output_dir_final}/` after each comparison run that produces score and selection artifacts;
- compares the new snapshot to the **previous** `monitoring/latest/analysis_snapshot.json` when `analysis_end` differs;
- uses **neutral decision-support** English in summaries;
- remains **non-executing** (no weight writes, no broker integration, no override of stress pass/fail or selection).

## V1 User Decisions (2026-05-17, Sessions 17–18)

1. **Storage:** generated-only under `{output_dir_final}/monitoring/` (`latest/` + `history/`). No separate `analyses/` workspace in V1.
2. **Monitored profiles:** **`analysis_subject`**, **`current`**, and **`policy`** when `status` is `available` or `degraded` in `candidate_comparison.json`.
3. **Retention:** keep `latest` plus **history** files named `analysis_snapshot_{analysis_end}.json` (one file per distinct `analysis_end`).
4. **Primary diff focus:** **`analysis_subject`** profile risk and mandate fields when available; legacy runs fall back to `current`, then `policy`. Decision and action blocks remain at run level.
5. **Session delivery:** the V1 spec and implementation are delivered; future work may add report/PDF surfacing or scheduled monitoring.

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Analysis snapshot** | Frozen projection of one run (`analysis_snapshot_v1`). |
| **What Changed** | `monitoring_diff.json` — deltas vs prior snapshot. |
| **Selection / Action** | Formal decision and implementation-plan artifacts; diff copies status fields only. |
| **Scorecards** | Diagnostic-only; diff reports score deltas, not binding recommendations. |

## Canonical Artifacts

| Artifact | Location | Schema |
| --- | --- | --- |
| `analysis_snapshot.json` (latest) | `{output_dir_final}/monitoring/latest/analysis_snapshot.json` | `analysis_snapshot_v1` |
| History snapshot | `{output_dir_final}/monitoring/history/analysis_snapshot_{analysis_end}.json` | `analysis_snapshot_v1` |
| `monitoring_diff.json` | `{output_dir_final}/monitoring_diff.json` | `monitoring_diff_v1` |
| Companion (optional) | `{output_dir_final}/monitoring_diff.txt` | Plain English summary |

## Pipeline Placement

1. After `action_plan.json` is written in `write_candidate_comparison_outputs` / `run_compare_variants.py`.
2. Load prior snapshot from `monitoring/latest/analysis_snapshot.json` **before** overwriting.
3. Do not re-run optimizer, stress, scores, or selection.
4. Decision Journal runs after monitoring and may summarize `monitoring_diff.json`; monitoring itself does not write journal files.

## Analysis Snapshot (`analysis_snapshot_v1`)

### Required top-level

| Field | Description |
| --- | --- |
| `schema_version` | `analysis_snapshot_v1` |
| `generated_at` | ISO UTC timestamp |
| `analysis_end` | From comparison |
| `investor_currency` | From comparison |
| `output_dir_final` | Relative path when possible |
| `profiles` | Object keyed by `analysis_subject`, `current`, `policy` (omit keys when unavailable) |
| `decision` | Projection from `selection_decision.json` |
| `action` | Projection from `action_plan.json` |
| `artifact_refs` | Relative paths to source JSON files |
| `warnings` | Run-level warnings |

### Profile object (per `analysis_subject` / `current` / `policy`)

| Field | Source |
| --- | --- |
| `candidate_id`, `display_name`, `status` | comparison row |
| `health_score`, `robustness_score` | scorecard `candidates[]` by id |
| `metrics_10y` | comparison `metrics.10y` (vol, beta, max_drawdown, cagr, sharpe) |
| `stress_overall` | comparison `stress.overall` |
| `worst_scenario_id`, `worst_scenario_loss_pct` | minimum `portfolio_pnl_pct` in stress scenarios when present |
| `top_risk_contributor` | comparison `diversification.top1_rc_asset` |
| `top_risk_contributor_pct` | `diversification.top1_rc_pct` |
| `macro_regime_label` | `factor_regime.macro_regime.label` or `regime` when present |
| `mandate_portfolio_valid` | comparison `mandate.portfolio_valid` |

## Monitoring Diff (`monitoring_diff_v1`)

### Diff status

| `diff_status` | When |
| --- | --- |
| `no_prior_snapshot` | No readable prior in `monitoring/latest/` or same `analysis_end` as prior |
| `diff_available` | Prior loaded and primary profile compared |
| `diff_degraded` | Prior exists but primary profile missing in current or prior |

When `diff_status` is `no_prior_snapshot`, the diff must not imply a real prior comparison:
`prior_analysis_end` is `null`, `profile_changes` is `{}`, decision/action change flags are
`false` with prior fields `null`, `input_artifacts.prior_snapshot` is `null`, and
`summary_plain_en` is narrative-only (first snapshot or same `analysis_end` re-run). Warning
`prior_same_analysis_end_ignored` is set when a prior file exists but shares `analysis_end`
with the current run.

### Required top-level

| Field | Description |
| --- | --- |
| `schema_version` | `monitoring_diff_v1` |
| `generated_at` | ISO UTC |
| `diff_status` | See table above |
| `primary_profile_id` | Normally `analysis_subject`; `current` if subject unavailable; `policy` if both are unavailable |
| `prior_analysis_end` | From prior snapshot or `null` |
| `current_analysis_end` | From current snapshot |
| `profile_changes` | Object keyed by profile id (`current`, `policy`) with numeric/string deltas |
| `decision_changes` | `decision_status_changed`, prior/current statuses, favored candidate ids |
| `action_changes` | `action_status_changed`, prior/current action statuses |
| `rebalance_trigger` | `true` when selection is `selected_candidate` or action suggests trades for review |
| `summary_plain_en` | 2–4 sentences, neutral wording |
| `warnings` | Missing-field notes |
| `input_artifacts` | Paths to current/prior snapshots |

### Profile change fields (when both sides present)

| Field | Meaning |
| --- | --- |
| `health_score_delta` | current minus prior |
| `robustness_score_delta` | current minus prior |
| `vol_annual_delta` | current minus prior |
| `beta_delta` | current minus prior |
| `max_drawdown_delta` | current minus prior (more negative = worse) |
| `worst_scenario_changed` | bool |
| `worst_scenario_loss_delta` | current loss minus prior (more negative = worse stress) |
| `top_risk_contributor_changed` | bool |
| `macro_regime_changed` | bool |
| `mandate_status_changed` | bool (`mandate_portfolio_valid` flip) |

## Input Failure

| Condition | Behavior |
| --- | --- |
| Missing `candidate_comparison.json` | Skip monitoring writes; warning `monitoring_skipped_missing_comparison`. |
| Missing score or selection files | Still write snapshot/diff with `null` fields and warnings where needed. |

## Diagnostic Boundary

| Artifact | Binding... |
| --- | --- |
| `analysis_snapshot.json` | Evidence only; generated output. |
| `monitoring_diff.json` | Decision-support summary; **non-executing**. |
| Selection / stress pass-fail | Monitoring must not override. |

## Non-Goals (V1)

- Scheduled monitoring jobs or email alerts.
- Durable user-maintained workspace outside `output_dir_final`.
- Compact PDF/report integration beyond the generated JSON/TXT files.
- Multi-portfolio workspace comparison.
- Recomputing metrics inside the monitoring module.

## Tests

Focused tests should cover:

- snapshot schema and profile projection for current/policy;
- `no_prior_snapshot` diff;
- normal diff with numeric deltas;
- `diff_degraded` when prior profile missing;
- `worst_scenario_changed` and `macro_regime_changed` flags;
- history file written on snapshot persist;
- same `analysis_end` does not diff against self.

## Detailed Ownership

| Area | Spec / module |
| --- | --- |
| Inputs | comparison, health, robustness, selection, action JSON |
| Output location | [OUTPUTS.md](../../OUTPUTS.md) |
| Implementation | `src/monitoring.py` |
| Downstream journal | [decision_journal_spec.md](decision_journal_spec.md) (consumes `monitoring_diff`) |
