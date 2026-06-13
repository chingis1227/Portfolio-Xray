# Current-vs-Policy Workflow Specification

This document owns the **current-vs-policy workflow**: how a user supplies current portfolio weights, materializes policy and current diagnostics in one comparison context, and when **No-Trade** and **Action Plan** outcomes are actionable versus explicitly skipped.

It does not own metric formulas, No-Trade materiality thresholds, selection composite weights, or trade-list mechanics. Those remain in [metrics_specification.md](metrics_specification.md), [selection_engine_spec.md](selection_engine_spec.md), and [action_engine_spec.md](action_engine_spec.md).

Implementation of the combined workflow is in **Session 09** (`run_report.py --materialize-current`, comparison sidecar resolution, status artifact). This spec is the contract for that work.

## Scope

The current-vs-policy workflow covers:

- config and CLI steps to make **policy** and **current** both `available` in `candidate_comparison.json` for the same `analysis_end`;
- **sidecar materialization** of current-portfolio report artifacts without overwriting policy artifacts on Main;
- machine-readable **workflow status** for reporting surfaces;
- **No-Trade actionability** rules for Selection, Action, and [decision package reporting](decision_package_reporting_spec.md);
- explicit skip reasons when the user has not completed the workflow.

It does not cover:

- full product UI/workspace (deferred);
- candidate factory orchestration ([candidate_factory_spec.md](candidate_factory_spec.md), post-audit Session 11 implementation);
- changing optimizer release policy or stress pass/fail.

## Product boundary

- The workflow answers: *given my current allocation and the policy target from this run, is a move materially worthwhile...*
- It remains **non-executing**: no broker integration, no automatic weight writes.
- **Policy** weights still come only from `run_optimization.py` and approved release paths ([portfolio_construction_policy.md](portfolio_construction_policy.md)).
- **Current** weights are user-supplied context ([input_assumptions_spec.md](input_assumptions_spec.md)); they are not policy replacements.

## Definitions

| Term | Meaning |
| --- | --- |
| **Policy** | Candidate `policy` (`role=policy`): optimizer-released weights and Main report artifacts after `optimize_from_universe`. |
| **Current** | Candidate `current` (`role=user_current`): user `current_weights` and materialized current diagnostics. |
| **Combined comparison context** | One `candidate_comparison.json` where `policy` is `available` or `degraded` and `current` is `available` or `degraded`, with the same `analysis_end`. |
| **Materialization** | Running the report pipeline for current weights into a **sidecar folder** without replacing policy `snapshot_*` / `run_metadata.json` on Main. |
| **No-Trade actionable** | Selection may evaluate materiality and emit `no_material_rebalance` or `selected_candidate` with a populated `no_trade` block; reporting may show a No-Trade headline. |
| **No-Trade not actionable** | Current row missing or weights not loadable; Selection must not imply "no material rebalance" versus current; reporting uses skip wording. |

## V1 user decisions (2026-05-17, post-audit Session 08)

Recorded defaults when the user continues the plan without overrides:

1. **Primary workflow:** `optimize_from_universe` + user `current_weights` in config, then **policy path** (optimize + report on Main), then **current materialization** into a sidecar, then **`run_compare_variants.py`** for the full decision package.
2. **Sidecar location:** `{output_dir_final}/current_portfolio/` (default `Main portfolio/current_portfolio/`). Policy artifacts stay at `{output_dir_final}/` root.
3. **Single-config mode:** Users keep `analysis_mode: optimize_from_universe`; they do not switch the whole config to `analyze_current_weights` to answer "should I move to policy..." (that mode remains a **current-only diagnostic** path).
4. **Status artifact:** `current_vs_policy_status.json` records workflow completeness and No-Trade actionability for reporting (see below).
5. **Deferred alternatives:** two full Main runs with toggled `analysis_mode` on the same folder (artifact overwrite risk); UI-only workflow without CLI materialization.

## Supported workflows

### A. Combined current-vs-policy (V1 primary)

**Goal:** Actionable No-Trade and trade-for-review when both weight vectors exist.

**Prerequisites in `config.yml`:**

- `analysis_mode: optimize_from_universe`
- `tickers` aligned with `current_weights` keys
- `current_weights` non-empty, non-negative, sum strictly positive

**Steps:**

| Step | Command | Writes / updates |
| --- | --- | --- |
| 1 Policy optimize | `python run_optimization.py` | `portfolio_weights.yml`, policy `run_result.json` / `run_metadata.json` on Main with `portfolio_role` consistent with generated policy |
| 2 Policy report | `python run_report.py` | Main `snapshot_*.json`, `stress_report.json`, commentary, etc., for **policy** weights |
| 3 Current materialize | `python run_report.py --materialize-current` | Sidecar `current_portfolio/snapshot_*.json`, `current_portfolio/run_metadata.json` with `analysis_portfolio.portfolio_role = user_current_portfolio`, weights from `current_weights` |
| 4 Compare + decision package | `python run_compare_variants.py` | `candidate_comparison.json` with both rows available; downstream selection, action, monitoring, journal, `decision_package_summary.*`, `current_vs_policy_status.json` |

**Comparison builder rule:** For `current`, resolve `artifact_root` to `{output_dir_final}/current_portfolio/` when that folder contains minimum files; otherwise apply existing gating (`missing_current_report`, etc.).

**CLI success line:** `run_compare_variants.py` prints workflow status and materialization hints when current is missing.

### B. Policy-only (default today)

**Goal:** Policy diagnostics and favored policy selection without versus-current materiality.

**Steps:** Steps 1–2 above only; optional `run_compare_variants.py`.

**Comparison:** `policy` available; `current` `unavailable` with `not_applicable_for_analysis_mode` or `missing_current_report` per [candidate_comparison_spec.md](candidate_comparison_spec.md).

**Selection:** May favor `policy` with `decision_status: selected_candidate` when scores allow; **No-Trade is not evaluated**; warnings include `no_trade_skipped_missing_current` or equivalent.

**Reporting:** Do not show "No material rebalance suggested versus current weights." Use: *Current portfolio not in this comparison; No-Trade versus current was not evaluated.*

### C. Current-only diagnostic

**Goal:** Diagnose holdings without a fresh policy target in the same run.

**Config:** `analysis_mode: analyze_current_weights`, `current_weights` set.

**Steps:** `python run_report.py` only (`run_optimization.py` must reject this mode).

**Comparison:** `current` available on Main; `policy` `unavailable` or `degraded` with `stale_policy_snapshot` if old policy snapshots remain.

**Out of scope for primary No-Trade question:** This path does not define the combined "move to policy..." workflow. Document in user-facing text as **holdings diagnostic**, not policy comparison.

## Sidecar artifact contract (`current_portfolio/`)

Minimum files for `current` to be `available` in combined context:

| File | Requirement |
| --- | --- |
| `current_portfolio/snapshot_10y.json` | Required; same schema as Main snapshots; `final_weights_total` must reflect `current_weights` |
| `current_portfolio/run_metadata.json` | Required; `analysis_setup.analysis_portfolio.portfolio_role = user_current_portfolio` |
| `current_portfolio/summary.json` | Optional; enables `degraded` instead of `unavailable` when snapshot partial |

Policy root (`{output_dir_final}/`) must retain its own `snapshot_10y.json` and `run_metadata.json` for **policy** from step 2. Materialization must **not** overwrite policy snapshots or `portfolio_weights.yml`.

## Workflow status artifact

| Field | Value |
| --- | --- |
| File name | `current_vs_policy_status.json` |
| Location | `{output_dir_final}/current_vs_policy_status.json` |
| Schema version | `current_vs_policy_status_v1` |
| Writer | Comparison pipeline after selection (`write_candidate_comparison_outputs`) |

### Required top-level fields

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | string | `current_vs_policy_status_v1` |
| `generated_at` | string | ISO timestamp |
| `analysis_end` | string | From comparison |
| `workflow_profile` | string | `combined_current_vs_policy` \| `policy_only` \| `current_only_diagnostic` \| `portfolio_first_review` |
| `combined_context_complete` | bool | True when policy and current rows are both `available` or `degraded` |
| `no_trade_actionable` | bool | True when Selection rules allow No-Trade evaluation (see matrix) |
| `policy_row_status` | string | `available` \| `degraded` \| `unavailable` |
| `current_row_status` | string | Same enum |
| `current_artifact_root` | string \| null | Relative path, e.g. `Main portfolio/current_portfolio` |
| `skip_reason` | string \| null | Machine code when `no_trade_actionable` is false |
| `user_message_en` | string | Plain English line for CLI and decision package summary |
| `materialization` | object | `{ "required": bool, "completed": bool, "command_hint": string \| null }` |

Companion optional: `current_vs_policy_status.txt` — one short English paragraph mirroring `user_message_en`.

## No-Trade actionability matrix

Rules align with [selection_engine_spec.md](selection_engine_spec.md) § No-Trade Recommendation. This table adds **reporting** obligations.

| `workflow_profile` | `current` in comparison | `policy` favored + target weights | `no_trade_actionable` | Selection behavior | Reporting (decision package § Selection / Action) |
| --- | --- | --- | --- | --- | --- |
| Combined, complete | `available` or `degraded` | yes | **true** | Evaluate No-Trade; may emit `no_material_rebalance` or `selected_candidate` | Show No-Trade bullets when `no_trade.evaluated` or status `no_material_rebalance` |
| Combined, current degraded | `degraded` | yes | **true** (with warnings) | Evaluate with warnings propagated | Show evaluation + data-quality note |
| Policy-only, no `current_weights` | `unavailable` / `not_applicable_for_analysis_mode` | yes | **false** | Skip No-Trade; warning | Skip No-Trade headline; state current not provided |
| Policy-only, weights in config, no sidecar | `unavailable` / `missing_current_report` | yes | **false** | Skip No-Trade; warning | Instruct: run current materialization (step 3) |
| Current-only diagnostic | `available` | policy N/A or stale | **false** | No-Trade vs policy not primary | State holdings diagnostic only |
| Missing target weights | any | no | **false** | `inconclusive` / `data_review_required` | No trade list; data review wording |
| `mandate_risk_reduction` | any | — | **false** | Status per selection spec | No No-Trade headline; mandate wording |

**Forbidden when `no_trade_actionable` is false:** Client-facing text that reads as a completed No-Trade decision (e.g. "No material rebalance suggested versus current weights") without a populated, evaluated `no_trade` block.

## Skip reason codes

| Code | When | `user_message_en` (template) |
| --- | --- | --- |
| `current_not_configured` | No positive `current_weights` in optimize mode | Current weights were not supplied; No-Trade versus current was not evaluated. |
| `current_not_materialized` | Weights present, sidecar missing | Current weights are configured but not materialized; run current materialization before comparing to policy. |
| `current_only_diagnostic_mode` | `analyze_current_weights` on Main | This run diagnoses current holdings only; compare to policy after a combined workflow. |
| `policy_target_unavailable` | Policy row unavailable | Policy target is unavailable; No-Trade versus current was not evaluated. |
| `weights_not_loadable` | Rows present but snapshots lack `final_weights_total` | Weight vectors could not be loaded; No-Trade and trades were skipped. |
| `mandate_or_data_block` | `mandate_risk_reduction` or `data_review_required` | Resolve mandate or data issues before interpreting versus-current results. |

Portfolio-first compatibility profile: when `candidate_comparison.json` has an available
`analysis_subject` baseline, this artifact may still be written for legacy consumers, but
`workflow_profile` is `portfolio_first_review`, `no_trade_actionable` is false, `skip_reason` is
`portfolio_first_review`, and the user message states that current-vs-policy status is
compatibility-only for the run. Portfolio-first report summaries must not display this as a main
workflow section.

## Downstream module contracts

### Candidate comparison

- In combined context, `current.artifact_root` resolves to `{output_dir_final}/current_portfolio/`.
- Registry row for `current` remains; gating in [candidate_comparison_spec.md](candidate_comparison_spec.md) is extended, not replaced.
- `analysis_setup_summary` on comparison continues to reflect **policy** Main metadata; add `current_materialization_root` in comparison or status JSON when implemented (Session 09).

### Selection engine

- No change to thresholds or formulas in Session 08.
- When `no_trade_actionable` is false: `no_trade` is `null` or omitted; `rationale.no_trade_bullets` empty; include warning `no_trade_not_actionable` with `skip_reason`.
- When actionable and evaluation runs: existing `no_trade` block and statuses unchanged.

### Action engine

- `trades_for_review` only when `decision_status == selected_candidate` and both weight vectors load (unchanged).
- When `no_trade_actionable` is false and status is not `no_material_rebalance`: `action_status` per [action_engine_spec.md](action_engine_spec.md); `no_trades_reason` must cite skip reason in plain English.

### Decision package reporting

- Section **Selection:** No-Trade summary only when `current_vs_policy_status.no_trade_actionable` is true or `selection_decision.no_trade.evaluated` is true.
- Section **Action:** If selection skipped No-Trade due to missing current, use skip wording; do not imply zero turnover means No-Trade.

## Non-goals (V1)

- Automatic detection of current weights from external custodians.
- Merging policy and current into one snapshot file on Main root.
- Changing Selection composite weights or No-Trade thresholds.
- Requiring UI for materialization.

## Tests (Session 09 implementation)

Focused tests should cover:

- combined context: policy on Main + sidecar current → both `available`, `combined_context_complete` true, `no_trade_actionable` true;
- `current_weights` without sidecar → `missing_current_report`, `no_trade_actionable` false;
- policy-only → `no_trade_actionable` false, no false No-Trade headline in reporting fixtures;
- materialization does not overwrite Main `snapshot_10y.json` policy weights;
- `current_vs_policy_status.json` schema and `skip_reason` codes;
- selection warnings when actionable false.

## Detailed ownership

| Area | Spec / module |
| --- | --- |
| Input modes and `current_weights` | [input_assumptions_spec.md](input_assumptions_spec.md) |
| Comparison rows and gating | [candidate_comparison_spec.md](candidate_comparison_spec.md) |
| No-Trade math and statuses | [selection_engine_spec.md](selection_engine_spec.md) |
| Trades and costs | [action_engine_spec.md](action_engine_spec.md) |
| Summary surfaces | [decision_package_reporting_spec.md](decision_package_reporting_spec.md) |
| Output locations | [OUTPUTS.md](../../OUTPUTS.md) |
| Implementation | `run_report.py`, `src/candidate_comparison.py`, `src/current_vs_policy.py`, `run_compare_variants.py` |
