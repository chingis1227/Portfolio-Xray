# Decision Journal Specification

This document owns the **Decision Journal** contract: a generated, non-executing decision record that summarizes why a comparison run favored a profile (or concluded No-Trade / inconclusive), what was rejected, which assumptions and risks framed the choice, and where to find the underlying artifacts.

It does not own metric formulas, stress scenarios, scorecard math, selection ranking, action trade mechanics, monitoring diff math, or optimizer release policy. Those remain in [metrics_specification.md](metrics_specification.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [portfolio_health_score_spec.md](portfolio_health_score_spec.md), [robustness_scorecard_spec.md](robustness_scorecard_spec.md), [selection_engine_spec.md](selection_engine_spec.md), [action_engine_spec.md](action_engine_spec.md), and [monitoring_spec.md](monitoring_spec.md).

Implementation: `src/decision_journal.py` (`decision_journal_v1`). This document is the contract.

## Scope

Decision Journal V1:

- **projects** fields from existing decision-pipeline JSON only (no new formulas);
- writes **`decision_journal.json`** (and optional **`decision_journal.txt`**) under `{output_dir_final}/`;
- archives a copy under `{output_dir_final}/journal/history/decision_journal_{analysis_end}.json` and keeps **`journal/latest/decision_journal.json`** in sync with the root file;
- runs **after** monitoring outputs in `write_candidate_comparison_outputs` / `run_compare_variants.py`;
- uses **neutral decision-support** English in narrative fields;
- remains **non-executing** (no weight writes, no broker integration, no override of selection or stress pass/fail);
- separates **process record** (what was decided and why at analysis time) from **outcome quality** (post-hoc PnL review is out of scope for V1).

## V1 User Decisions (2026-05-17, Session 19)

Recorded defaults when the user continues the plan without overrides:

1. **Storage:** generated-only under `{output_dir_final}/`. No user-maintained journal file in V1.
2. **Retention:** root `decision_journal.json` plus `journal/latest/` and `journal/history/decision_journal_{analysis_end}.json` (one history file per distinct `analysis_end`).
3. **Always emit when selection exists:** write the journal whenever `selection_decision.json` was written for the run (including No-Trade, inconclusive, and `data_review_required`).
4. **`follow_up_review_date`:** optional field; default `null` in V1 (no automatic calendar rule).
5. **`process_review`:** reserved object for future "was this a good decision given what was known" review; V1 emits `null` or an empty object with `status: not_implemented`.

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Decision Journal** (this spec) | `decision_journal.json` — consolidated decision record for one run. |
| **Selection Engine** | Formal `decision_status` and composite ranking; journal copies status, does not re-rank. |
| **Action Engine** | Implementation plan (`action_plan.json`); journal summarizes action status and turnover, not trade execution. |
| **Monitoring / What Changed** | Temporal diff vs prior run; journal may embed `what_changed_summary` from `monitoring_diff.txt` / `summary_plain_en`. |
| **Scorecards / comparison** | Diagnostic evidence; journal cites scores and stress context, does not treat them as automatic truth. |
| **Commentary / X-Ray** | Analyst diagnostics; journal may reference paths but does not duplicate full commentary text in V1. |

## Canonical Artifacts

| Artifact | Location | Schema |
| --- | --- | --- |
| `decision_journal.json` (primary) | `{output_dir_final}/decision_journal.json` | `decision_journal_v1` |
| Latest copy | `{output_dir_final}/journal/latest/decision_journal.json` | `decision_journal_v1` |
| History | `{output_dir_final}/journal/history/decision_journal_{analysis_end}.json` | `decision_journal_v1` |
| Companion (optional) | `{output_dir_final}/decision_journal.txt` | Plain English summary |

Root and `journal/latest/` must contain the same logical content for a given run (duplicate paths for convenience and symmetry with `monitoring/latest/`).

## Pipeline Placement

1. After `monitoring_diff.json` (and snapshot persist) in `write_candidate_comparison_outputs` / `run_compare_variants.py`.
2. Read `selection_decision.json`, `action_plan.json`, `monitoring_diff.json` (if present), `candidate_comparison.json`, and score files already on disk.
3. Do not re-run optimizer, stress, scores, selection, action, or monitoring.

## Inputs

### Required

| Input | Minimum fields used |
| --- | --- |
| `selection_decision.json` | `schema_version`, `decision_status`, `favored_candidate_id`, `favored_display_name`, `rationale`, `rejected_candidates`, `no_trade`, `composite_ranking`, `warnings`, `input_artifacts` |
| `candidate_comparison.json` | `analysis_end`, `investor_currency`, `analysis_setup_summary`, `candidates[]` for favored/current/policy rows |

### Optional (degraded journal when missing)

| Input | Use |
| --- | --- |
| `action_plan.json` | `action_status`, `turnover_half_sum_pct`, `no_trades_reason`, `risk_context`, `priority_trades` (ids/count only in TXT) |
| `monitoring_diff.json` | `summary_plain_en`, `diff_status`, `rebalance_trigger` |
| `portfolio_health_score.json` / `robustness_scorecard.json` | Score deltas vs current for `expected_improvement` when not already on selection `no_trade` |
| Main `run_result.json` / `run_metadata.json` | `analysis_setup` projection when not fully on comparison `analysis_setup_summary` |

### Input failure

| Condition | Behavior |
| --- | --- |
| Missing `selection_decision.json` | Do not write journal; run warning `journal_skipped_missing_selection`. |
| Missing `candidate_comparison.json` | Do not write journal; warning `journal_skipped_missing_comparison`. |
| Missing `action_plan.json` | Still write journal; `implementation_plan` null with warning `journal_partial_missing_action`. |
| Missing `monitoring_diff.json` | Still write journal; `what_changed` null with warning `journal_no_monitoring_diff`. |

## Top-Level JSON Contract (`decision_journal_v1`)

```json
{
  "schema_version": "decision_journal_v1",
  "generated_only": true,
  "non_executing": true,
  "generated_at": "ISO-8601",
  "analysis_end": "YYYY-MM-DD",
  "investor_currency": "USD",
  "output_dir_final": "Main portfolio",
  "decision_record": {},
  "selected_portfolio": {},
  "rejected_alternatives": [],
  "assumptions": {},
  "expected_improvement": {},
  "accepted_risks": {},
  "macro_context": {},
  "rationale": {},
  "no_trade_status": {},
  "implementation_plan": {},
  "what_changed": {},
  "follow_up_review_date": null,
  "process_review": null,
  "artifact_refs": {},
  "warnings": []
}
```

### Required top-level fields

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | string | `decision_journal_v1` |
| `generated_only` | bool | Always `true` in V1 (not user-maintained source). |
| `non_executing` | bool | Always `true` in V1. |
| `generated_at` | string | ISO UTC timestamp. |
| `analysis_end` | string | From comparison. |
| `investor_currency` | string | From comparison. |
| `output_dir_final` | string | Relative path when possible. |
| `decision_record` | object | Projection from selection (see below). |
| `selected_portfolio` | object | Favored profile summary (see below). |
| `rejected_alternatives` | array | Copy of `selection_decision.rejected_candidates`. |
| `assumptions` | object | Analysis setup summary (see below). |
| `expected_improvement` | object | Structured deltas vs current (see below). |
| `accepted_risks` | object | Stress, concentration, mandate warnings (see below). |
| `macro_context` | object | Regime label and profile source (see below). |
| `rationale` | object | Copy/projection of selection `rationale` plus journal `summary`. |
| `no_trade_status` | object | No-Trade flag and materiality (see below). |
| `implementation_plan` | object \| null | Projection from `action_plan.json` when present. |
| `what_changed` | object \| null | Projection from `monitoring_diff.json` when present. |
| `follow_up_review_date` | string \| null | Optional ISO date; V1 default `null`. |
| `process_review` | object \| null | V1: `null` or `{ "status": "not_implemented" }`. |
| `artifact_refs` | object | Relative paths to all inputs used. |
| `warnings` | array | Run-level journal warnings. |

### `decision_record`

| Field | Source |
| --- | --- |
| `decision_status` | `selection_decision.decision_status` |
| `favored_candidate_id` | selection |
| `favored_display_name` | selection |
| `formal_decision` | copy `selection_decision.formal_decision` (always `true` when present) |
| `selection_weights_profile` | selection |
| `no_trade_thresholds_profile` | selection |
| `composite_rank_top3` | first three rows from `composite_ranking` (id, selection_score, rank) |

### `selected_portfolio`

| Field | Source |
| --- | --- |
| `candidate_id` | favored id |
| `display_name` | favored display name |
| `role` | comparison row `role` when available |
| `status` | comparison row `status` |
| `construction_method` | comparison row metadata when present |
| `mandate_portfolio_valid` | comparison `mandate.portfolio_valid` for favored row |

### `assumptions`

Project from `candidate_comparison.analysis_setup_summary` and, when needed, Main `analysis_setup`:

| Field | Description |
| --- | --- |
| `analysis_mode` | e.g. `optimize_from_universe`, `analyze_current_weights` |
| `primary_window` | V1 default narrative window `10y` when metrics use 10y blocks |
| `investor_currency` | copy |
| `weight_sources` | short map: which candidates use optimizer output vs user current |
| `data_quality_notes` | union of comparison/selection warnings relevant to inputs |

No new assumption inference in the journal module.

### `expected_improvement`

Structured comparison vs **`current`** when `current` is available; otherwise `status: not_applicable`.

| Field | Source |
| --- | --- |
| `status` | `available` \| `not_applicable` \| `degraded` |
| `health_score_delta` | selection `no_trade` or score files vs current |
| `robustness_score_delta` | same |
| `drawdown_improvement_pp` | action `risk_context` or comparison 10y drawdown fields |
| `turnover_half_sum_pct` | action or selection no_trade |
| `materiality_met` | `true` when `decision_status == selected_candidate`; `false` for no_trade; `null` otherwise |

Plain English one-liner in `summary` (neutral wording).

### `accepted_risks`

From favored (or current when no-trade vs policy) comparison row:

| Field | Source |
| --- | --- |
| `worst_scenario_id` | stress scenarios minimum `portfolio_pnl_pct` |
| `worst_scenario_loss_pct` | same |
| `stress_overall` | `stress.overall` |
| `top_risk_contributor` | `diversification.top1_rc_asset` |
| `top_risk_contributor_pct` | `diversification.top1_rc_pct` |
| `mandate_portfolio_valid` | `mandate.portfolio_valid` |
| `mandate_notes` | short English from mandate warnings on comparison row |

### `macro_context`

| Field | Source |
| --- | --- |
| `macro_regime_label` | favored row `factor_regime.macro_regime.label` or `regime` |
| `profile_id` | candidate id the label was taken from (`policy` or `current` per implementation default: favored, else `policy`) |

### `rationale`

| Field | Description |
| --- | --- |
| `summary` | 2–4 sentences combining selection `rationale.summary` and journal context (English, neutral). |
| `selection_bullets` | from selection `rationale.selection_bullets` |
| `no_trade_bullets` | from selection when present |
| `tradeoff_bullets` | from selection when present |
| `data_quality_notes` | from selection `rationale.data_quality_notes` |

Forbidden in narrative strings: imperative buy/sell, performance guarantees, raw internal codes in client-facing export paths.

### `no_trade_status`

| Field | Description |
| --- | --- |
| `is_no_trade` | `true` when `decision_status == no_material_rebalance` |
| `no_trade` | copy selection `no_trade` object when present, else `null` |
| `no_trades_reason` | copy action `no_trades_reason` when action present |

### `implementation_plan`

When `action_plan.json` exists:

| Field | Source |
| --- | --- |
| `action_status` | action |
| `target_candidate_id` | action |
| `turnover_half_sum_pct` | action |
| `estimated_transaction_cost_pct` | action |
| `trade_count` | length of `trades` |
| `priority_tickers` | up to 5 tickers from `priority_trades` |
| `no_trades_reason` | action |

### `what_changed`

When `monitoring_diff.json` exists:

| Field | Source |
| --- | --- |
| `diff_status` | monitoring |
| `summary_plain_en` | monitoring |
| `rebalance_trigger` | monitoring |
| `prior_analysis_end` | monitoring |

## TXT Summary (optional)

`decision_journal.txt` — English only, compact:

```text
Decision journal (generated, non-executing) — analysis end 2026-04-30
Status: no_material_rebalance
Selected profile for review: Policy (Optimized)

Rationale: Composite scores favor policy, but turnover versus current is high relative to score improvement.

Rejected alternatives: 3 candidates (see decision_journal.json).
Follow-up review: not scheduled in V1.

See artifact_refs in decision_journal.json for selection, action, and monitoring files.
```

## Diagnostic Boundary

| Artifact | Binding? |
| --- | --- |
| `decision_journal.json` | Process record and evidence index; **non-executing**. |
| `selection_decision.json` | Formal decision; journal must not contradict `decision_status`. |
| Scorecards / comparison | Remain diagnostic-only. |
| User notes / IC memos | Out of scope for V1 generated journal. |

Downstream PDF or report builders may summarize the journal using [reporting_outputs_spec.md](reporting_outputs_spec.md) and project PDF rules. V1 does not require PDF integration.

## Generated vs Source Boundary

| Type | Examples |
| --- | --- |
| **Generated (this spec)** | `decision_journal.json`, `journal/latest/`, `journal/history/` |
| **Generated inputs** | selection, action, monitoring, comparison, scorecards |
| **Source** | `config.yml`, specs, `DECISIONS.md` — not overwritten by journal |

Users must not treat `decision_journal.json` as mandate or weight source. Manual edits to generated journal files are overwritten on the next comparison run.

## Non-Goals (V1)

- User-maintained decision records or merge-with-generated workflows.
- Post-hoc outcome scoring ("was the decision good in hindsight").
- Automatic `follow_up_review_date` scheduling or alerts.
- PDF/report integration (Session 20+ follow-up allowed).
- Duplicating full `commentary.txt` or Portfolio X-Ray bodies.
- Multi-portfolio workspace journals.
- Recomputing metrics, scores, or selection inside the journal module.

## Tests (Session 20)

Focused tests should cover:

- schema version and required keys;
- journal written for `selected_candidate`, `no_material_rebalance`, `inconclusive`, and `data_review_required`;
- skip when selection missing;
- `artifact_refs` point to fixture inputs;
- `expected_improvement.status == not_applicable` when `current` unavailable;
- history file created under `journal/history/`;
- `latest` copy matches root `decision_journal.json`;
- rationale strings contain no forbidden imperative patterns (fixture lint);
- `process_review` is `null` or `not_implemented` in V1.

## Detailed Ownership

| Area | Spec / module |
| --- | --- |
| Selection inputs | [selection_engine_spec.md](selection_engine_spec.md) |
| Action inputs | [action_engine_spec.md](action_engine_spec.md) |
| Monitoring inputs | [monitoring_spec.md](monitoring_spec.md) |
| Comparison / assumptions | [candidate_comparison_spec.md](candidate_comparison_spec.md), [input_assumptions_spec.md](input_assumptions_spec.md) |
| Output location | [OUTPUTS.md](../../OUTPUTS.md) |
| Implementation | `src/decision_journal.py` (Session 20) |
