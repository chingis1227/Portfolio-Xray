# Pareto / Dominance Check Specification

This document owns the **Pareto / Dominance Check** diagnostic layer: pairwise and summary dominance classification of portfolio candidates using metrics already exported in the comparison run, without re-running optimizers or recomputing canonical formulas.

It does not own metric formulas, stress scenario definitions, selection rules, scorecard math, trade construction, or mandate release policy. Those remain in [metrics_specification.md](metrics_specification.md), [stress_testing_spec.md](stress_testing_spec.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [selection_engine_spec.md](selection_engine_spec.md), [tradeoff_and_model_risk_spec.md](tradeoff_and_model_risk_spec.md), and [assumption_sensitivity_spec.md](assumption_sensitivity_spec.md).

Implementation: [src/pareto_dominance.py](../../src/pareto_dominance.py) (post-audit Session 17). This document is the contract.

## Scope

The Pareto / Dominance layer:

- reads **`candidate_comparison.json`** as the primary input and may read **`selection_decision.json`** for cross-reference only;
- may read **`tradeoff_explanation.json`** for precomputed `turnover_half_sum_pct` vs **current** when the current row exists;
- emits **`pareto_dominance.json`** and **`pareto_dominance.txt`** under `output_dir_final`;
- classifies each eligible candidate as **`non_dominated`**, **`dominated`**, or **`not_evaluated`** using strict Pareto rules on a fixed V1 objective set;
- records **who dominates whom** with objective-level evidence (no duplicate metric math);
- remains **diagnostic-only** and **non-binding** (does not change `selection_decision.json`, action plans, mandate pass/fail, or weights);
- does **not** replace Selection, Health Score, Robustness Scorecard, Assumption Sensitivity, or Regret Analysis.

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Pareto / Dominance** (this spec) | Multi-criteria dominance pruning evidence among comparison candidates. |
| **Selection Engine** | Produces `favored_candidate_id`; unchanged by this layer in V1. |
| **Assumption Sensitivity** | Stability of favored profile under weight perturbations; complementary. |
| **Trade-off Explanation** | Baseline→target deltas and turnover vs current for one favored pair; complementary. |
| **Regret Analysis** | Scenario opportunity loss vs best available ([regret_analysis_spec.md](regret_analysis_spec.md)); implementation Session 19. |
| **Mandate / stress pass-fail** | Binding construction gates; **excluded** from dominance objectives in V1. |

## Product Boundary

- Answers: *Which candidates are clearly weaker than another option on return, risk, drawdown, stress loss, and (when known) turnover vs current—with no compensating metric advantage?*
- Does **not** answer: *automatically drop candidates from Selection*, *execute trades*, or *override mandate/stress release*.
- Forbidden in exported text: imperative buy/sell, performance guarantees, presenting dominance as automatic investment truth.

**Tone (V1):** institutional decision-support English, same as comparison and selection artifacts.

## V1 User Decisions (2026-05-17, Post-audit Session 16)

Recorded defaults from product concept section 15 and audit PSA-012 when the user continues without overrides:

1. **Strict Pareto only:** candidate **A dominates B** when A is **weakly better** on every evaluated objective and **strictly better** on at least one (see [Dominance rule](#dominance-rule-v1)).
2. **Primary evidence window:** `candidate_comparison.primary_window` (V1 default **`10y`**).
3. **Objective set (metric-only):** `cagr` (↑), `vol_annual` (↓), `max_drawdown` (↑), `stress_worst_loss` (↑), optional `es_95` (↑), optional `turnover_vs_current_half_sum_pct` (↓). Mandate validity, Health/Robustness totals, and selection composite are **out of scope** for dominance in V1.
4. **Eligible rows:** `status` in `available`, `degraded`; registry rows with `unavailable` are listed with `not_evaluated` and excluded from pairwise dominance.
5. **Current row:** included when `status` allows; may be dominated like any other candidate; No-Trade logic remains in Selection / current-vs-policy specs.
6. **Favored candidate:** `selection_decision.favored_candidate_id` is echoed for context; dominance does **not** remove or downgrade it in V1.
7. **Binding boundary:** artifact is evidence for humans, decision package, and journal; Selection output is unchanged.

## Canonical Artifacts

| File | Schema | Required |
| --- | --- | --- |
| `pareto_dominance.json` | `pareto_dominance_v1` | Yes when comparison exists with at least two evaluable candidates |
| `pareto_dominance.txt` | plain English | Yes when JSON is written |

Location: `{output_dir_final}/` (default `Main portfolio/`).

## Pipeline Placement

```text
run_compare_variants.py
  -> write_candidate_comparison_outputs
       -> comparison, robustness, health
       -> selection_decision
       -> tradeoff_explanation + model_risk_diagnostics
       -> assumption_sensitivity
       -> [Session 17] pareto_dominance  (this spec)
       -> [Session 19] regret_analysis  ([regret_analysis_spec.md](regret_analysis_spec.md))
       -> current_vs_policy_status
       -> action_plan
       -> monitoring, journal, decision_package_reporting
```

**Order (V1):** immediately **after** `assumption_sensitivity` and **before** `current_vs_policy_status.json`.

Rationale: needs full comparison metrics/stress; must not influence No-Trade or action gating.

## Inputs

### Required

| Input | Minimum fields |
| --- | --- |
| `candidate_comparison.json` | `primary_window`, `candidates[]` with `candidate_id`, `status`, `metrics`, `stress`, `drawdown` |

### Optional

| Input | Use |
| --- | --- |
| `selection_decision.json` | `favored_candidate_id`, `decision_status` for summary cross-reference |
| `tradeoff_explanation.json` | `turnover_half_sum_pct` for favored vs current; per-candidate turnover map when Session 17 precomputes or extends trade-off rows |

### Skip behavior

| Condition | Behavior |
| --- | --- |
| Missing `candidate_comparison.json` | Do not write artifacts; run warning `pareto_skipped_missing_comparison`. |
| Fewer than two evaluable candidates | `dominance_status: insufficient_candidates`; write minimal JSON with warning. |
| Missing `primary_window` metrics on a row | Row `evaluation_status: partial_objectives`; exclude from dominating others until required objectives present. |

## V1 Objective Catalog

All values are taken **as exported** in comparison (three decimals at export per metrics spec). Implementation must **not** recompute CAGR, vol, or drawdown from raw prices.

| `objective_id` | Direction | Source field | Required for pairwise |
| --- | --- | --- | --- |
| `cagr` | higher is better | `metrics.{primary_window}.cagr` | yes |
| `vol_annual` | lower is better | `metrics.{primary_window}.vol_annual` | yes |
| `max_drawdown` | higher is better (less negative) | `metrics.{primary_window}.max_drawdown` or `drawdown.max_drawdown` | yes |
| `stress_worst_loss` | higher is better (smaller loss) | min `stress.scenarios[].portfolio_pnl_pct` when present; else abbreviated worst field on `stress` | yes when any candidate has stress scenarios |
| `es_95` | higher is better (less negative tail) | `metrics.{primary_window}.es_95` when projected into comparison | no — omit from pairwise check when missing on either row |
| `turnover_vs_current` | lower is better | `turnover_vs_current_half_sum_pct` on candidate row (Session 17) or trade-off map vs `current` | no — only when `current` is evaluable and turnover known for both rows |

**Stress worst-loss tie-break:** same rule as [assumption_sensitivity_spec.md](assumption_sensitivity_spec.md) Tier B: algebraically largest (least negative) scenario PnL across `stress.scenarios[]`.

**ES / CVaR note:** historical **ES 95%** (`es_95`) may be projected into comparison metrics in Session 17 implementation from `snapshot_{primary_window}.json` without new formulas. Until projected, `es_95` is skipped per pair with `objective_skipped: es_95_missing`.

**Turnover note:** product concept lists turnover as a dominance axis. V1 uses **half-sum absolute weight delta vs `current`** only (same definition as Action Engine / trade-off). Pairwise turnover comparison applies among candidates only when both values exist; otherwise the objective is dropped for that pair.

### Explicitly out of V1 objectives

| Topic | Rationale |
| --- | --- |
| Health / Robustness totals | Scorecard rankings, not Pareto evidence axes in V1. |
| Mandate `portfolio_valid` | Binding gate; dominance is metric-only. |
| Sharpe-only or single-metric dominance | Covered partially by Assumption Sensitivity Tier B; not duplicated here. |
| Multi-window Pareto surfaces | Deferred to V2 (`pareto_by_window` optional block). |

## Dominance Rule (V1)

For candidates **A** and **B** (A ≠ B), with evaluated objective set **O**:

1. For each objective `o` in **O** that is **required and present** for both rows, A must be **not worse** than B (weak dominance).
2. At least one objective in **O** must be **strictly better** for A vs B.
3. If any **required** objective is missing on either row, the pair `(A, B)` is `not_comparable` with `reason: missing_objectives`.

**Direction helpers:**

- `higher_better`: A dominates on `o` when `A[o] >= B[o]` and strict when `A[o] > B[o]`.
- `lower_better`: A dominates on `o` when `A[o] <= B[o]` and strict when `A[o] < B[o]`.

**Transitivity:** implementation may compute dominators via all-pairs scan (V1 N is small). Optional `dominance_graph` lists direct dominators only.

**Symmetric output:** store both `A_dominates_B` and derived `B_dominated_by_A` in candidate summary to avoid client recomputation.

## Per-Candidate Classification

After all-pairs evaluation among evaluable candidates:

| `pareto_status` | Condition |
| --- | --- |
| `non_dominated` | No other evaluable candidate dominates this row |
| `dominated` | At least one other evaluable candidate dominates this row |
| `not_evaluated` | `status` is `unavailable` or required objectives missing on row |

| Field | Description |
| --- | --- |
| `dominated_by[]` | List of `{candidate_id, display_name, strict_objectives[]}` |
| `dominates[]` | List of candidates this row dominates (direct) |
| `non_dominated_alternatives_count` | Count of other `non_dominated` rows (informational) |

**Favored profile line:** when `selection_decision.favored_candidate_id` is dominated, set `favored_is_dominated: true` and `favored_dominance_note` (plain English, non-binding). Do **not** change selection.

## Top-Level JSON (`pareto_dominance_v1`)

```json
{
  "schema_version": "pareto_dominance_v1",
  "diagnostic_only": true,
  "non_executing": true,
  "generated_at": "ISO-8601",
  "analysis_end": "YYYY-MM-DD",
  "primary_window": "10y",
  "dominance_status": "complete",
  "objectives_evaluated": ["cagr", "vol_annual", "max_drawdown", "stress_worst_loss"],
  "objectives_optional": ["es_95", "turnover_vs_current"],
  "evaluable_candidate_count": 8,
  "non_dominated_count": 3,
  "dominated_count": 4,
  "not_evaluated_count": 1,
  "favored_candidate_id": "policy",
  "favored_is_dominated": false,
  "candidates": [],
  "pairwise_dominance": [],
  "summary_plain_en": "Three candidates are on the Pareto-efficient set; four are dominated on return, risk, and stress loss.",
  "warnings": [],
  "input_artifacts": {
    "candidate_comparison.json": "candidate_comparison.json",
    "selection_decision.json": "selection_decision.json"
  }
}
```

### Candidate row

| Field | Type | Description |
| --- | --- | --- |
| `candidate_id` | string | Registry id |
| `display_name` | string | English label |
| `status` | string | From comparison |
| `pareto_status` | string | `non_dominated` \| `dominated` \| `not_evaluated` |
| `evaluation_status` | string | `complete` \| `partial_objectives` \| `unavailable` |
| `objectives` | object | Resolved values used (3 decimals at export) |
| `dominated_by` | array | Dominator summaries |
| `dominates` | array | Dominated-peer summaries |
| `dominance_note` | string \| null | Short plain-English line when dominated |

### Pairwise row (optional compact list)

| Field | Type | Description |
| --- | --- | --- |
| `dominator_id` | string | A |
| `dominated_id` | string | B |
| `strict_objectives` | array | Objective ids where A is strictly better |
| `objectives_skipped` | array | Optional ids not compared |

### Required top-level fields

| Field | Required | Description |
| --- | --- | --- |
| `schema_version` | yes | `pareto_dominance_v1` |
| `diagnostic_only` | yes | always `true` |
| `dominance_status` | yes | `complete` \| `insufficient_candidates` \| `partial` |
| `objectives_evaluated` | yes | Objective ids used in required set |
| `candidates` | yes | One row per registry candidate |
| `summary_plain_en` | yes | 1–3 sentences, client-safe |
| `warnings` | yes | May be empty |

## TXT Summary (V1)

Plain English, fixed sections:

1. **Scope** — primary window and objective list.
2. **Efficient set** — count and names of `non_dominated` candidates.
3. **Dominated profiles** — bullet list with dominator and one-line reason (no internal codes).
4. **Favored profile check** — whether selection favorite is dominated (informational).
5. **Interpretation** — one short paragraph; no buy/sell.

## Downstream Consumers

| Consumer | Use |
| --- | --- |
| [decision_package_reporting_spec.md](decision_package_reporting_spec.md) | Optional subsection after assumption sensitivity (Session 17). |
| [decision_journal_spec.md](decision_journal_spec.md) | Optional `pareto_summary` citing `non_dominated_count` and `favored_is_dominated`. |
| PDF / `report.txt` | Short dominance line when summary exists. |

Journal and reporting must **not** override `selection_decision.json` when the favored profile is dominated.

## Comparison Builder Extension (Session 17)

To support optional `es_95` without duplicate formulas, Session 17 may extend [candidate_comparison_spec.md](candidate_comparison_spec.md) metric projection:

| Field | Source |
| --- | --- |
| `metrics.{window}.es_95` | `snapshot_{window}.json` → `metrics.es_95` when present |

This extension is **optional** for dominance; dominance must still run when `es_95` is absent (objective skipped).

## Tests (Session 17 implementation)

Minimum focused tests:

1. Synthetic three-candidate chain: middle candidate dominated by top on all required objectives.
2. Missing `vol_annual` on one row → pair `not_comparable`; row `partial_objectives`.
3. `stress_worst_loss` skipped when no scenarios on either row; dominance uses remaining objectives.
4. Favored candidate dominated → `favored_is_dominated: true` without mutating selection file.
5. Fewer than two evaluable candidates → `insufficient_candidates`.
6. Pipeline integration: file emitted after assumption sensitivity in `write_candidate_comparison_outputs`.

## Related Specifications

- [candidate_comparison_spec.md](candidate_comparison_spec.md) — metric and stress blocks.
- [selection_engine_spec.md](selection_engine_spec.md) — favored profile (unchanged in V1).
- [tradeoff_and_model_risk_spec.md](tradeoff_and_model_risk_spec.md) — turnover vs current definition.
- [assumption_sensitivity_spec.md](assumption_sensitivity_spec.md) — complementary stability diagnostics.
- [decision_package_reporting_spec.md](decision_package_reporting_spec.md) — reporting integration (Session 17).
