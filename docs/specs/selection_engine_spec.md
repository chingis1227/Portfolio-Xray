# Selection Engine and No-Trade Recommendation Specification

This document owns the **Selection Engine** and **No-Trade Recommendation** contract: the first formal, machine-readable decision layer that states which portfolio profile is favored in a comparison run and whether a move from the user's current allocation appears materially worthwhile.

It does not own metric formulas, stress scenario definitions, candidate construction, scorecard component math, rebalance trade lists, or optimizer release policy. Those remain in [metrics_specification.md](metrics_specification.md), [stress_testing_spec.md](stress_testing_spec.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [robustness_scorecard_spec.md](robustness_scorecard_spec.md), [portfolio_health_score_spec.md](portfolio_health_score_spec.md), [portfolio_construction_policy.md](portfolio_construction_policy.md), and [action_engine_spec.md](action_engine_spec.md).

Implementation: [src/selection_engine.py](../../src/selection_engine.py) (`selection_decision_v1`). This document is the contract.

Product terminology boundary: product-facing docs may refer to this decision layer as `Decision Verdict`, but this spec continues to own the current `Selection Engine`, `selection_decision.json`, and No-Trade technical contracts until a separate migration changes them.

## Scope

The Selection Engine:

- reads **`candidate_comparison.json`**, **`portfolio_health_score.json`**, and **`robustness_scorecard.json`** as primary inputs;
- may read linked **`snapshot_10y.json`** / **`run_result.json`** fields already projected into comparison or mandate blocks (no duplicate metric formulas);
- produces **`selection_decision.json`** (and optional **`selection_decision.txt`**) under `output_dir_final`;
- emits exactly one **decision status** per run with structured rationale, rejected alternatives, no-trade materiality, and warnings;
- uses **neutral decision-support wording** in all exported text (no imperative buy/sell, no guaranteed outcomes);
- does **not** change optimizer weights, stress pass/fail, mandate MaxDD release gates, or `portfolio_weights.yml`;
- does **not** replace Portfolio Diagnosis, commentary, or diagnostic scorecards (those remain evidence inputs only).

The No-Trade Recommendation is a **first-class outcome** of the same module when a target profile is identified but the benefit of moving from the portfolio-first **baseline** does not clear reviewable materiality thresholds. The preferred baseline is `analysis_subject`; legacy runs fall back to `current`.

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Selection Engine** (this spec) | Formal decision artifact: favored candidate and decision status. |
| **No-Trade Recommendation** | Outcome `no_material_rebalance` when change is below materiality thresholds. |
| **Portfolio Health Score** | Diagnostic holistic quality score; not a binding decision. |
| **Robustness Scorecard** | Diagnostic resilience ranking; not a binding decision. |
| **Candidate Comparison** | Diagnostic evidence table; remains `diagnostic_only: true`. |
| **Action Engine / Rebalancing Advisor** | Existing non-executing implementation-plan artifact (`action_plan.json`) that consumes selection output. |
| **`src/rebalance.py`** | Mechanical trade list from two weight vectors; `threshold_pct` gates max per-ticker drift only, not Selection or No-Trade logic. |

## Product Boundary

- The Selection Engine answers: *given this comparison run, which candidate profile is favored for further review, and is a move from the user's current allocation materially worthwhile...*
- It does **not** answer: *execute these trades now* or *this portfolio will outperform*.
- Allowed narrative: "Policy profile is favored in this comparison", "No material rebalance suggested versus current weights", "Decision inconclusive due to missing current portfolio weights".
- Forbidden: imperative trade advice ("buy X", "sell Y"), performance guarantees, overriding stress **pass/fail** or optimizer **release** status, or presenting diagnostic scores as automatic investment truth.

**Tone (V1):** institutional **decision-support** English. Client-facing PDFs may summarize the decision; they must follow [reporting_outputs_spec.md](reporting_outputs_spec.md) and project PDF rules (no raw internal codes, no Russian text).

## V1 User Decisions (2026-05-17, Session 14)

Recorded defaults when the user continues the plan without overrides:

1. **Decision tone:** neutral decision-support only (no direct trade imperatives in Selection/No-Trade artifacts).
2. **Default favored candidate:** legacy current-vs-policy runs keep `policy` as default when `status` is `available` or `degraded` and mandate gates allow. Portfolio-first runs with `analysis_subject` do not use the policy default; they select the highest **composite selection score** among scored alternatives.
3. **No-Trade baseline:** compare **`analysis_subject`** to the **favored target**. If `analysis_subject` is unavailable, fall back to legacy **`current`** (role `user_current`). If no baseline is available, No-Trade is not computed; decision may still select a favored non-baseline candidate with a warning.
4. **V1 scope:** composite ranking from Health + Robustness + mandate gates only. **Pareto dominance** is specified in [pareto_dominance_spec.md](pareto_dominance_spec.md) as a **diagnostic-only** layer that does not change Selection output in V1. **Regret analysis** is specified in [regret_analysis_spec.md](regret_analysis_spec.md) as a **diagnostic-only** layer that does not change Selection output in V1. **Assumption sensitivity** is specified in [assumption_sensitivity_spec.md](assumption_sensitivity_spec.md) as a **diagnostic-only** layer that does not change Selection output in V1.
5. **Binding boundary:** Selection output is a **formal decision record** for the product workflow, but it remains **non-executing** (no broker integration, no automatic weight writes).

## Canonical Artifacts

| Field | Value |
| --- | --- |
| File name | `selection_decision.json` |
| Location | `{output_dir_final}/selection_decision.json` |
| Companion (optional) | `{output_dir_final}/selection_decision.txt` |
| Schema version | `selection_decision_v1` |
| Primary inputs | `candidate_comparison.json`, `portfolio_health_score.json`, `robustness_scorecard.json` |

## Inputs

### Required

| Input | Minimum fields used |
| --- | --- |
| `candidate_comparison.json` | `schema_version`, `candidates[]` with `candidate_id`, `status`, `role`, `mandate`, `metrics`, `drawdown`, `stress`, `weight_concentration`, `missing_fields` |
| `portfolio_health_score.json` | `candidates[]` with `candidate_id`, `score_status`, `total_score`, `health_rank`, `sub_scores`, `warnings` |
| `robustness_scorecard.json` | `candidates[]` with `candidate_id`, `score_status`, `total_score`, `robustness_rank`, `sub_scores`, `warnings` |

### Optional

| Input | Use |
| --- | --- |
| `run_result.json` / `run_metadata.json` on Main | `portfolio_valid`, release status, `fail_reason_code` when not already on comparison `policy` row |
| Per-candidate `snapshot_10y.json` | `final_weights_total` for turnover vs current (when not inlined in comparison) |

### Input failure

| Condition | Behavior |
| --- | --- |
| Missing `candidate_comparison.json` | Do not write decision artifact; set run warning `selection_skipped_missing_comparison`. |
| Missing both score files | `decision_status`: `data_review_required`; reason `missing_score_artifacts`. |
| Missing one score file | Proceed with renormalized composite weights; list warning `partial_score_inputs`. |
| No scored candidates | `decision_status`: `inconclusive`; reason `no_scored_candidates`. |

## Eligible Candidates

| `status` | Composite ranking | Favored target |
| --- | --- | --- |
| `available` | Full participation when mandate and scores allow. | Allowed when favoring rules below pass. |
| `degraded` | May appear in `composite_ranking` for diagnostic transparency. | **Never** favored (Phase 17 RM-1022). |
| `unavailable` | Excluded from ranking; may appear in `rejected_candidates` with `reason_code: unavailable`. | Never favored. |
| `not_scored` (health/robustness) | Excluded from composite; if all non-baseline are `not_scored`, `inconclusive`. | Never favored. |

### Favoring eligibility (Phase 17 RM-1022)

A candidate may become `favored_candidate_id` only when:

1. `status` is **`available`** (degraded rows are never favored).
2. For `optimizer_candidate` / `robust_candidate` rows, `construction_disclosure.optimization_readiness.fair_comparison_ready` is **`true`** (see [optimization_engine_layer_spec.md](optimization_engine_layer_spec.md)).
3. Mandate hard-exclusion rules in this spec still apply (`portfolio_valid === false`, etc.).

Baseline rows (`analysis_subject`, `current`) remain eligible for No-Trade materiality when
`available` or `degraded`; they are never favored targets.

When `candidate_menu.is_partial_menu` is true, the decision must emit warning
`partial_candidate_menu` and a plain-English `data_quality_notes` line that rankings apply only to
the **intended** menu profile, not the full product optimizer menu.

Optimization Engine Session 06 adds a quality boundary for optimizer candidates. If comparison
marks a candidate `degraded` because `construction_disclosure.optimizer_quality` is
`approximate_fallback` or `approximate_solver`, Selection may still list it in `composite_ranking`,
but it cannot be favored. If a clean `available` optimizer row is favored, no extra quality warning
is required beyond `fair_comparison_ready`. Candidates marked `unavailable` because of failed
factory or failed optimizer quality remain excluded like other unavailable rows.

**Role rules (V1):**

- `policy` — default favored target only in legacy current-vs-policy runs when present and mandate-allowed.
- `analysis_subject` — portfolio-first baseline only; excluded from favored-target ranking.
- `user_current` (`current`) — legacy No-Trade baseline only when `analysis_subject` is absent; excluded from favored-target ranking.
- `benchmark` / `optimizer_candidate` / `robust_candidate` — may win composite only when `policy` is unavailable or fails hard mandate exclusion (see gates).

Hard exclusion from favored target:

- `mandate.portfolio_valid === false` on that candidate row;
- `score_status === not_scored` in both score files when the other score is also missing for that id.

## Decision Outcomes

Exactly one `decision_status` per run:

| `decision_status` | Meaning | Typical user-facing line (English) |
| --- | --- | --- |
| `selected_candidate` | A favored non-current profile is identified and materiality vs current is met or current is absent. | "Favored profile: Policy (Optimized) for this comparison." |
| `no_material_rebalance` | Favored target exists but move from **current** is below No-Trade thresholds. | "No material rebalance suggested versus current weights." |
| `inconclusive` | Conflicting scores, ties unresolved, or no eligible favored profile. | "Selection inconclusive; review comparison and score drivers." |
| `data_review_required` | Critical inputs missing or degraded beyond safe decision. | "Decision requires data review before acting on results." |
| `mandate_risk_reduction` | Current or policy shows mandate breach requiring risk reduction before allocation change. | "Mandate constraints require risk reduction; allocation change is not advised until resolved." |

**Core MVP boundary:** `mandate_risk_reduction` is a **legacy policy-path** outcome. It applies only when
`candidate_comparison.json` includes mandate validation on **policy** or legacy **current** rows
(`mandate.portfolio_valid === false`). Portfolio-first runs with baseline `analysis_subject` and no
policy row typically never emit this status. Core MVP UI should treat it as advanced/legacy policy
semantics; product-facing filtering may use `decision_verdict.json` → `verdict_family: policy_mandate`.
Diagnosis-only runs do not produce `selection_decision.json`.

`no_trade` object is present when `decision_status` is `no_material_rebalance`; otherwise `no_trade` may be `null` or omitted.

## Selection Model (V1)

### Composite selection score

For each eligible candidate `c` (excluding `current` unless policy is unavailable — see role rules):

```text
selection_score(c) =
  w_health   * health_total(c)
+ w_robust   * robustness_total(c)
+ w_mandate  * mandate_component(c)
```

Default weights (`selection_weights_profile`: **`default_weights_reviewable`**):

| Component | Symbol | Default weight | Source |
| --- | --- | --- | --- |
| Health total | `w_health` | 0.45 | `portfolio_health_score.json` → `total_score` |
| Robustness total | `w_robust` | 0.45 | `robustness_scorecard.json` → `total_score` |
| Mandate fit | `w_mandate` | 0.10 | Absolute 0–100 from mandate flags (not within-run rank) |

If one score file is missing, renormalize `w_health` and `w_robust` to sum to 0.90 and keep `w_mandate` at 0.10. If both missing, stop (see input failure).

**`mandate_component(c)` (absolute):**

| Condition | Points |
| --- | --- |
| `mandate.portfolio_valid === true` and no mandate warnings on row | 100 |
| `portfolio_valid` true but `degraded` or comparison warnings | 70 |
| `portfolio_valid === false` | 0 (hard exclude from favored target) |
| `portfolio_valid` unknown / missing | 50 and flag `mandate_unknown` |

### Default favored candidate

1. If `analysis_subject` is available: favored id = argmax `selection_score(c)` over eligible non-baseline candidates.
2. Else if `policy` is eligible and `mandate_component(policy) > 0`: favored id = `policy` for legacy current-vs-policy compatibility.
3. Else: favored id = argmax `selection_score(c)` over eligible non-baseline candidates.
4. Tie-break order: higher `robustness_rank` (lower number wins), then higher `health_rank`, then lexicographic `candidate_id`.

### Relationship to score ranks

Health and Robustness **ranks** are explanatory. The favored candidate is **not** required to be rank 1 on both scores. The composite score is the primary selector when policy is unavailable; when policy is available and mandate-clean, policy is favored regardless of benchmark ranks unless `policy` is `unavailable`.

## No-Trade Recommendation (V1)

### When evaluated

No-Trade runs only when:

- `analysis_subject` or fallback `current` baseline is `available` or `degraded`, and
- a **favored target** `target_id` is identified (`policy` or composite winner), and
- weight vectors can be resolved for both (from comparison-linked snapshots or `final_weights_total`).

**Actionability:** When the current row is missing or weights cannot load, No-Trade is **not** evaluated. Reporting must not present a completed No-Trade conclusion. See [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) for workflow profiles, `current_vs_policy_status.json`, and skip reason codes (`no_trade_not_actionable` warning in selection output).

**Workflow and actionability:** combined policy + current context, materialization, and reporting skip rules are defined in [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md). When that spec's conditions for "not actionable" apply, do not emit `no_material_rebalance` or imply No-Trade in downstream summaries; use explicit warnings such as `no_trade_skipped_missing_weights` or `no_trade_not_evaluated` as appropriate.

### Turnover metric

Use **half-sum absolute weight change** (reported as percent of portfolio):

```text
turnover_half_sum_abs_delta_pct = 0.5 * sum_i |w_target_i - w_current_i| * 100
```

Align tickers on the union of keys; missing ticker = 0 weight. Do not use `src/rebalance.py` `threshold_pct` as the No-Trade gate (that gate is per-ticker max drift for trade lists only).

### Materiality thresholds

Profile id: **`default_no_trade_thresholds_reviewable`**

| Threshold id | Default | Comparison |
| --- | --- | --- |
| `min_health_score_delta` | 3.0 | `health_total(target) - health_total(current)` |
| `min_robustness_score_delta` | 3.0 | `robustness_total(target) - robustness_total(current)` |
| `max_turnover_half_sum_pct` | 15.0 | No-Trade if **both** deltas below mins **and** turnover above max |
| `min_max_drawdown_improvement_pp` | 1.0 | Improvement in 10y max drawdown (percentage points, less negative is better) from comparison `drawdown` block |

**No-Trade rule:** emit `no_material_rebalance` when **all** of the following hold:

1. `health_delta < min_health_score_delta` **and** `robustness_delta < min_robustness_score_delta`, **and**
2. `turnover_half_sum_abs_delta_pct > max_turnover_half_sum_pct` **or** (`health_delta` and `robustness_delta` both below mins and `drawdown_improvement_pp < min_max_drawdown_improvement_pp`).

If drawdown fields are missing, skip drawdown clause and warn `no_trade_drawdown_unknown`.

Otherwise, when favored target differs materially from the baseline, `decision_status` = `selected_candidate`.

**Clarification:** Small score improvement with **low** turnover may still be `selected_candidate` (user may prefer to implement small trades). No-Trade targets the case where **benefit is small and turnover is high**, or benefit is small across scores and drawdown.

### No-Trade JSON block

```json
"no_trade": {
  "evaluated": true,
  "baseline_candidate_id": "current",
  "target_candidate_id": "policy",
  "health_score_delta": 2.1,
  "robustness_score_delta": 1.4,
  "turnover_half_sum_abs_delta_pct": 18.2,
  "drawdown_improvement_pp": 0.4,
  "thresholds_profile": "default_no_trade_thresholds_reviewable",
  "materiality_pass": false,
  "summary": "No material rebalance suggested versus current weights."
}
```

## Mandate Risk Reduction

Emit `mandate_risk_reduction` when **any** of:

- `current` has `mandate.portfolio_valid === false` and stress/mandate warnings indicate active breach;
- `policy` has `portfolio_valid === false` while user is on released or current weights that also fail fit;
- `run_result.json` / comparison projects `fail_reason_code` tied to mandate MaxDD on the active portfolio role.

This status **does not** select an aggressive alternative. List `risk_reduction_notes` with plain English references to mandate fields (not raw codes in PDF-facing strings).

**Classification:** legacy **policy compare path** — not part of the Core MVP diagnosis-only default. Prefer filtering via `decision_verdict.json` → `verdict_family: policy_mandate` when presenting product UI.

## Top-Level JSON Contract

```json
{
  "schema_version": "selection_decision_v1",
  "formal_decision": true,
  "non_executing": true,
  "generated_at": "ISO-8601",
  "analysis_end": "YYYY-MM-DD",
  "investor_currency": "USD",
  "output_dir_final": "Main portfolio",
  "decision_status": "no_material_rebalance",
  "baseline_candidate_id": "analysis_subject",
  "baseline_display_name": "Starting Portfolio",
  "favored_candidate_id": "policy",
  "favored_display_name": "Policy (Optimized)",
  "selection_weights_profile": "default_weights_reviewable",
  "no_trade_thresholds_profile": "default_no_trade_thresholds_reviewable",
  "composite_ranking": [],
  "rationale": {},
  "no_trade": {},
  "rejected_candidates": [],
  "warnings": [],
  "input_artifacts": {},
  "missing_inputs": []
}
```

### Required top-level fields

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | string | `selection_decision_v1` |
| `formal_decision` | bool | Always `true` (distinguishes from diagnostic score files). |
| `non_executing` | bool | Always `true` in V1. |
| `generated_at` | string | ISO timestamp. |
| `decision_status` | string | One of the outcome table ids. |
| `baseline_candidate_id` | string \| null | `analysis_subject` when available, else legacy `current`, else `null`. |
| `baseline_display_name` | string \| null | English label from comparison for the baseline row. |
| `favored_candidate_id` | string \| null | Favored profile; null when inconclusive or mandate-only message. |
| `favored_display_name` | string \| null | English label from comparison. |
| `selection_weights_profile` | string | Active composite weights profile. |
| `no_trade_thresholds_profile` | string | Active No-Trade thresholds profile. |
| `composite_ranking` | array | Sorted rows: `candidate_id`, `selection_score`, `health_total`, `robustness_total`, `mandate_component`, `rank`. |
| `rationale` | object | Structured bullets (see below). |
| `rejected_candidates` | array | Id, display_name, reason_code, short_note. |
| `warnings` | array | Run-level warnings. |
| `input_artifacts` | object | Relative paths to comparison and score JSON used. |

### `rationale` object

| Field | Description |
| --- | --- |
| `summary` | 1–3 sentences, neutral English. |
| `selection_bullets` | Up to 5 bullets: why favored target won (policy default, composite, mandate). |
| `no_trade_bullets` | Present when No-Trade fired; materiality numbers in plain English. |
| `tradeoff_bullets` | Optional short bullets from comparison (no new formulas). When [tradeoff_and_model_risk_spec.md](tradeoff_and_model_risk_spec.md) artifacts exist, journal and reporting prefer those over this field. |
| `data_quality_notes` | Missing fields, degraded candidates, partial scores. |
| `risk_reduction_notes` | Present when `decision_status` is `mandate_risk_reduction`; plain-English mandate blockers suitable for TXT/PDF summaries. |

Forbidden in `rationale` strings: imperative rebalance language, "recommended buy/sell", internal codes (`FAIL_*`, `DIAG_*`) in PDF-facing export paths.

## TXT Summary (optional)

`selection_decision.txt` — English only, compact:

```text
Selection decision (formal, non-executing) — primary window 10y
Status: no_material_rebalance
Favored profile: Policy (Optimized)

Versus current: health +2.1, robustness +1.4, turnover (half-sum) 18.2%
Conclusion: No material rebalance suggested versus current weights.

See selection_decision.json for composite ranking and rejected candidates.
```

## Pipeline Placement

1. After `candidate_comparison.json`, `robustness_scorecard.json`, and `portfolio_health_score.json` are written (same path as `write_candidate_comparison_outputs` / `run_compare_variants.py`).
2. Do not re-run optimizer, stress engine, or score formulas.
3. Write `selection_decision.json` to `output_dir_final`.
4. Report/PDF-facing summaries are owned by [reporting_outputs_spec.md](reporting_outputs_spec.md); until the compact decision-package report surface is implemented, `selection_decision.json` / `.txt` are the direct generated selection surfaces.

## Diagnostic Artifacts Remain Non-Binding

| Artifact | Still diagnostic-only... |
| --- | --- |
| `candidate_comparison.json` | Yes (`diagnostic_only: true` unchanged). |
| `robustness_scorecard.json` | Yes. |
| `portfolio_health_score.json` | Yes. |
| `portfolio_xray.json`, commentary | Yes. |
| `selection_decision.json` | **Formal decision record** for workflow; still **non-executing**. |

Downstream commentary may **reference** the decision artifact but must not contradict its status. PDF client text uses decision-support phrasing per [production_workflow.md](production_workflow.md).

## Non-Goals (V1)

- Pareto / dominance pruning (implemented in [pareto_dominance_spec.md](pareto_dominance_spec.md); diagnostic-only in V1).
- Regret analysis and assumption sensitivity grids.
- Transaction cost models beyond Action Engine V1 simple bps-on-turnover (see [action_engine_spec.md](action_engine_spec.md)).
- Automatic weight release or optimizer re-run.
- User-maintained decision journal writes (see [decision_journal_spec.md](decision_journal_spec.md); generated-only V1).
- Multi-period or monitoring-based selection. Monitoring consumes selection output; it must not change the selection status.

## Tests

Focused tests should cover:

- schema version and required keys;
- policy favored when available and mandate-clean;
- composite winner when policy unavailable;
- `no_material_rebalance` when thresholds not met;
- `selected_candidate` when deltas and turnover pass materiality;
- `inconclusive` with no scored candidates;
- `data_review_required` when comparison or both scores missing;
- `mandate_risk_reduction` when `portfolio_valid` false on current/policy;
- `analysis_subject` baseline disables legacy policy default and drives No-Trade materiality when available;
- missing baseline → no No-Trade block, still may select a candidate;
- partial score file → renormalized weights warning;
- tie-break ordering;
- rationale strings contain no forbidden imperative patterns (fixture lint).

## Detailed Ownership

| Area | Spec / module |
| --- | --- |
| Comparison inputs | [candidate_comparison_spec.md](candidate_comparison_spec.md) |
| Current-vs-policy workflow | [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) |
| Health inputs | [portfolio_health_score_spec.md](portfolio_health_score_spec.md) |
| Robustness inputs | [robustness_scorecard_spec.md](robustness_scorecard_spec.md) |
| Mandate / release | [portfolio_construction_policy.md](portfolio_construction_policy.md), [production_workflow.md](production_workflow.md) |
| Trade lists | [action_engine_spec.md](action_engine_spec.md), `src/action_engine.py`, `src/rebalance.py` |
| Output location | [OUTPUTS.md](../../OUTPUTS.md) |
| Implementation | `src/selection_engine.py` |
