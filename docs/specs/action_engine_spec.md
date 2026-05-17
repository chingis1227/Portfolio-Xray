# Action Engine and Rebalancing Advisor Specification

This document owns the **Action Engine** and **Rebalancing Advisor** contract: a non-executing implementation plan that translates a formal selection outcome into weight deltas, optional trade rows, turnover, a simple transaction-cost estimate, and risk-benefit context versus the user's current allocation.

It does not own metric formulas, stress scenarios, candidate construction, scorecard math, selection ranking, optimizer release policy, or broker execution. Those remain in [metrics_specification.md](metrics_specification.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [selection_engine_spec.md](selection_engine_spec.md), [portfolio_construction_policy.md](portfolio_construction_policy.md), and `src/rebalance.py`.

Implementation: [src/action_engine.py](../../src/action_engine.py) (`action_plan_v1`). This document is the contract.

## Scope

The Action Engine:

- reads **`selection_decision.json`** and **`candidate_comparison.json`** as primary inputs;
- always writes **`action_plan.json`** (and optional **`action_plan.txt`**) under `output_dir_final` when comparison and selection artifacts exist for the run;
- resolves **current** (`role=user_current`) and **target** (favored candidate from selection) weights from each candidate's `snapshot_10y.json` → `final_weights_total` (same loader as Selection Engine);
- emits **trade rows** only when selection status is `selected_candidate` and both weight vectors load; otherwise `trades` is an empty array with an explicit **`no_trades_reason`**;
- uses **`src/rebalance.compute_trades`** for mechanical buy/sell/hold deltas (no NAV required in V1);
- applies a **simple transaction-cost model**: `10` basis points on turnover half-sum (reviewable constant in code);
- remains **non-executing** (no weight writes, no broker integration);
- uses **neutral decision-support** language in summary fields (structural `direction` values `buy` / `sell` are allowed in trade rows only).

The Rebalancing Advisor is the same artifact surfaced for humans: compact `.txt` summary plus structured JSON for downstream reports and [Decision Journal](decision_journal_spec.md).

## V1 User Decisions (2026-05-17, Session 16)

1. **Transaction costs:** `10` bps applied to turnover half-sum:  
   `estimated_transaction_cost_pct = turnover_half_sum_pct * transaction_cost_bps / 10000`.
2. **Always emit `action_plan`:** written after every comparison run that produces `selection_decision.json`, including No-Trade and inconclusive outcomes (`trades: []` with reason).
3. **Session delivery:** the V1 spec and implementation are delivered.

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Action Engine** (this spec) | `action_plan.json` — deltas, trades, turnover, costs, risk context. |
| **Rebalancing Advisor** | Human-facing summary in `action_plan.txt` (same run). |
| **Selection Engine** | Formal favored profile and `decision_status` (including No-Trade). |
| **`src/rebalance.py`** | Mechanical trade list; `threshold_pct` gates max per-ticker drift only. |
| **View After Optimization** | Post-policy manual tilt; outside Action Engine V1. |

## Canonical Artifacts

| Field | Value |
| --- | --- |
| File name | `action_plan.json` |
| Location | `{output_dir_final}/action_plan.json` |
| Companion (optional) | `{output_dir_final}/action_plan.txt` |
| Schema version | `action_plan_v1` |
| Primary inputs | `selection_decision.json`, `candidate_comparison.json` |

## Inputs

### Required

| Input | Minimum fields used |
| --- | --- |
| `selection_decision.json` | `schema_version`, `decision_status`, `favored_candidate_id`, `favored_display_name`, `no_trade`, `rationale` |
| `candidate_comparison.json` | `candidates[]` with `candidate_id`, `status`, `role`, `artifact_root` |

### Input failure

| Condition | Behavior |
| --- | --- |
| Missing `selection_decision.json` | Do not write action artifact; warning `action_skipped_missing_selection`. |
| Missing `candidate_comparison.json` | Do not write action artifact; warning `action_skipped_missing_comparison`. |

## Action Status (V1)

| `action_status` | When |
| --- | --- |
| `trades_for_review` | `decision_status == selected_candidate` and current + target weights loaded; non-empty or filtered trade list may still be empty if all deltas below `min_trade_pct` when set. |
| `no_trades_no_material_rebalance` | `decision_status == no_material_rebalance`. |
| `no_trades_other` | `inconclusive`, `data_review_required`, or `mandate_risk_reduction`. |
| `trades_skipped_missing_weights` | `selected_candidate` but current or target weights could not be loaded. |
| `advisory_only` | No favored target id on selection artifact. |

When [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) marks No-Trade as not actionable, `no_trades_reason` must use the workflow `user_message_en` or equivalent skip wording—not a No-Trade materiality conclusion.

When [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) marks No-Trade as not actionable, `no_trades_reason` must state that current-vs-policy was not evaluated (e.g. missing current materialization), not imply a completed No-Trade review.

## Transaction Costs (V1)

| Field | Value |
| --- | --- |
| `transaction_cost_bps` | `10` (reviewable default) |
| `transaction_cost_model` | `bps_on_turnover_half_sum` |
| `estimated_transaction_cost_pct` | `turnover_half_sum_pct * transaction_cost_bps / 10000` when turnover known, else `null` |

Full per-asset cost schedules remain out of scope for V1.

## Risk Context (V1)

Reuses comparison/selection projections only (no new formulas):

| Field | Source |
| --- | --- |
| `turnover_half_sum_pct` | Half-sum of absolute weight deltas (same as Selection No-Trade block). |
| `drawdown_improvement_pp` | Target max drawdown minus current (percentage points), 10y window fields on comparison rows. |
| `health_score_delta` | From selection `no_trade` when present, else computed from score files if available in implementation. |
| `robustness_score_delta` | Same as health delta sourcing. |
| `risk_improvement_per_one_pct_turnover` | `drawdown_improvement_pp / turnover_half_sum_pct` when both defined and turnover > 0. |

## JSON Shape (required top-level)

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | string | `action_plan_v1` |
| `non_executing` | bool | Always `true` in V1. |
| `generated_at` | string | ISO timestamp. |
| `action_status` | string | See action status table. |
| `selection_decision_status` | string | Copy of `selection_decision.decision_status`. |
| `baseline_candidate_id` | string | Always `current` when present in comparison, else `null`. |
| `target_candidate_id` | string \| null | Favored candidate from selection. |
| `target_display_name` | string \| null | English label. |
| `current_weights` | object \| null | Ticker → weight fraction. |
| `target_weights` | object \| null | Ticker → weight fraction. |
| `weight_deltas` | array | Per-ticker `{ ticker, current_weight, target_weight, delta_weight, delta_pct }`. |
| `trades` | array | `{ ticker, direction, delta_weight, delta_pct }` from `compute_trades`; empty when no trades. |
| `no_trades_reason` | string | Plain English explanation when `trades` is empty. |
| `turnover_half_sum_pct` | number \| null | |
| `transaction_cost_bps` | number | Default `10`. |
| `estimated_transaction_cost_pct` | number \| null | |
| `risk_context` | object | Drawdown/health/robust deltas and `risk_improvement_per_one_pct_turnover`. |
| `priority_trades` | array | Up to 5 largest \|delta_pct\| tickers for review ordering. |
| `warnings` | array | Run-level warnings. |
| `input_artifacts` | object | Relative paths to selection and comparison JSON. |

## Pipeline Placement

1. After `selection_decision.json` is written (`write_candidate_comparison_outputs` / `run_compare_variants.py`).
2. Do not re-run optimizer, stress, scores, or selection.
3. Write `action_plan.json` to `output_dir_final` whenever selection was written.
4. Monitoring consumes the action status and Decision Journal summarizes the resulting implementation-plan fields; Action Engine must not update monitoring or journal files directly.

## Diagnostic Boundary

| Artifact | Binding? |
| --- | --- |
| `action_plan.json` | Implementation plan for review only; **non-executing**. |
| `selection_decision.json` | Formal decision record; Action must not override its status. |
| Scorecards / comparison | Remain diagnostic-only. |

## Non-Goals (V1)

- NAV-based dollar amounts (optional in `compute_trades` but not required in JSON V1).
- Per-asset transaction cost tables or tax logic.
- Partial rebalance optimization or trade netting.
- Compact PDF/report integration beyond the generated JSON/TXT files.
- Automatic execution or `portfolio_weights.yml` updates.

## Tests

Focused tests should cover:

- schema version and required keys;
- always writes when selection + comparison exist;
- `no_trades_no_material_rebalance` with empty `trades` but populated weights and reason;
- `trades_for_review` with non-empty trades for `selected_candidate`;
- `no_trades_other` for mandate/inconclusive;
- `trades_skipped_missing_weights` when snapshots missing;
- transaction cost formula at 10 bps;
- `risk_improvement_per_one_pct_turnover` when inputs allow;
- priority trades ordering by \|delta_pct\|.

## Detailed Ownership

| Area | Spec / module |
| --- | --- |
| Selection inputs | [selection_engine_spec.md](selection_engine_spec.md) |
| Weight vectors | `snapshot_10y.json` via comparison `artifact_root` |
| Trade mechanics | `src/rebalance.py` |
| Output location | [OUTPUTS.md](../../OUTPUTS.md) |
| Implementation | `src/action_engine.py` |
| Downstream monitoring | [monitoring_spec.md](monitoring_spec.md) |
| Downstream journal | [decision_journal_spec.md](decision_journal_spec.md) |
