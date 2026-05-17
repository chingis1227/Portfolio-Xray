# Assumption Sensitivity Specification

This document owns the **Assumption Sensitivity** diagnostic layer: a deterministic variant grid that tests whether the **selection outcome** and related ranking evidence remain stable under reviewable perturbations of decision weights and evidence windows, without re-running optimizers or recomputing canonical metrics.

It does not own metric formulas, stress scenario definitions, scorecard component math, selection rules, action trade construction, optimizer release policy, or input-assumption editing. Those remain in [metrics_specification.md](metrics_specification.md), [stress_testing_spec.md](stress_testing_spec.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [portfolio_health_score_spec.md](portfolio_health_score_spec.md), [robustness_scorecard_spec.md](robustness_scorecard_spec.md), [selection_engine_spec.md](selection_engine_spec.md), [input_assumptions_spec.md](input_assumptions_spec.md), and [tradeoff_and_model_risk_spec.md](tradeoff_and_model_risk_spec.md).

Implementation: post-audit Session 15 (new builder in the `src` package). This document is the contract.

## Scope

The Assumption Sensitivity layer:

- reads **`selection_decision.json`**, **`portfolio_health_score.json`**, **`robustness_scorecard.json`**, and **`candidate_comparison.json`** only through fields already exported (no duplicate metric formulas, no optimizer re-run);
- emits **`assumption_sensitivity.json`** and **`assumption_sensitivity.txt`** under `output_dir_final`;
- evaluates **deterministic variants** from a fixed V1 catalog (see [V1 perturbation catalog](#v1-perturbation-catalog));
- reports **stability** of the effective favored candidate and optional evidence ranks versus the baseline selection;
- remains **diagnostic-only** and **non-binding** (does not change `selection_decision.json`, action plans, mandate pass/fail, or weights);
- does **not** replace [tradeoff_and_model_risk_spec.md](tradeoff_and_model_risk_spec.md) or [model risk diagnostics](tradeoff_and_model_risk_spec.md) — it answers *ranking stability under stated perturbations*, not *model/data warning aggregation*.

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Assumption Sensitivity** (this spec) | Variant-grid stability of selection outcome and evidence ranks. |
| **Input assumptions / `analysis_setup`** | Runtime configuration of the run ([input_assumptions_spec.md](input_assumptions_spec.md)); not perturbed in V1. |
| **Selection Engine** | Produces baseline `favored_candidate_id`; unchanged by this layer in V1. |
| **Trade-off / Model Risk** | Price of change and warning catalog; complementary diagnostics. |
| **Pareto / Dominance** | Multi-criteria dominance pruning ([pareto_dominance_spec.md](pareto_dominance_spec.md)); implementation Session 17. |
| **Regret Analysis** | Scenario opportunity loss vs best available ([regret_analysis_spec.md](regret_analysis_spec.md)); implementation Session 19. |
| **`src/robustness.py`** | Optimizer weight stability across horizons; unrelated to this artifact. |

## Product Boundary

- Answers: *If we stress how much Health vs Robustness matter, or ignore the policy default, does the same profile still look favored? Do simpler metric-window rankings agree?*
- Does **not** answer: *re-optimize under new covariance*, *change expected-return forecasts*, *execute trades*, or *override selection because stability is low*.
- Forbidden in exported text: imperative buy/sell, performance guarantees, presenting stability % as automatic truth.

**Tone (V1):** institutional decision-support English, same as Selection and trade-off artifacts.

## V1 User Decisions (2026-05-17, Post-audit Session 14)

Recorded defaults from quant-review when the user continues without overrides:

1. **No optimizer re-run:** variants use **existing** `health_total`, `robustness_total`, `mandate_component`, and comparison `metrics` / `stress` blocks only.
2. **Primary stability target:** **`baseline_favored_id`** from `selection_decision.favored_candidate_id` compared to **`effective_favored_id`** per variant using the same selection rules as [selection_engine_spec.md](selection_engine_spec.md) with catalog overrides.
3. **Tier A (selection stability):** composite weight stress + **policy-default-off** variant — these count toward `favored_stable_rate`.
4. **Tier B (evidence stability):** per-window Sharpe rank and stress worst-loss rank — reported separately; **do not** change `selection_decision.json` and **do not** count toward `favored_stable_rate` unless the variant explicitly recomputes selection (Tier A only).
5. **Explicit V1 exclusions:** expected-return ±%, full covariance re-estimation, correlation-stress matrix rebuild, transaction-cost / rebalance-frequency grids, macro-regime relabeling, and re-scoring Health/Robustness components (deferred — would require scorecard recomputation).
6. **Binding boundary:** artifact is evidence for humans, decision package, and journal; Selection output is unchanged.

## Canonical Artifacts

| File | Schema | Required |
| --- | --- | --- |
| `assumption_sensitivity.json` | `assumption_sensitivity_v1` | Yes when comparison and selection exist |
| `assumption_sensitivity.txt` | plain English | Yes when JSON is written |

Location: `{output_dir_final}/` (default `Main portfolio/`).

## Pipeline Placement

```text
run_compare_variants.py
  -> write_candidate_comparison_outputs
       -> comparison, robustness, health
       -> selection_decision
       -> tradeoff_explanation + model_risk_diagnostics
       -> [Session 15] assumption_sensitivity  (this spec)
       -> pareto_dominance
       -> [Session 19] regret_analysis  ([regret_analysis_spec.md](regret_analysis_spec.md))
       -> current_vs_policy_status
       -> action_plan
       -> monitoring, journal, decision_package_reporting
```

**Order (V1):** immediately **after** trade-off / model-risk outputs and **before** `current_vs_policy_status.json`.

Rationale: needs `favored_candidate_id` and score totals; must not influence action or No-Trade gating.

## Inputs

### Required

| Input | Minimum fields |
| --- | --- |
| `selection_decision.json` | `favored_candidate_id`, `decision_status`, `composite_ranking[]`, `selection_weights_profile` |
| `portfolio_health_score.json` | `candidates[]` with `candidate_id`, `score_status`, `total_score`, `health_rank` |
| `robustness_scorecard.json` | `candidates[]` with `candidate_id`, `score_status`, `total_score`, `robustness_rank` |
| `candidate_comparison.json` | `candidates[]` with `candidate_id`, `status`, `role`, `mandate`, `metrics` (3y/5y/10y), `stress` |

### Optional

| Input | Use |
| --- | --- |
| `tradeoff_explanation.json` | Narrative cross-reference only (no formulas). |
| `model_risk_diagnostics.json` | Append stability caveat when `overall_severity` is high or medium. |

### Skip behavior

| Condition | Behavior |
| --- | --- |
| Missing `selection_decision.json` | `sensitivity_status: selection_unavailable`; write minimal JSON with warning; skip Tier A/B counts. |
| Missing health or robustness score file | Run Tier B only if comparison present; Tier A variants that need both scores are `skipped` with reason `partial_score_inputs`. |
| `favored_candidate_id` is null | `sensitivity_status: no_baseline_favored`; list variants as `not_applicable`. |
| Missing `candidate_comparison.json` | Do not write artifacts; run warning `sensitivity_skipped_missing_comparison`. |

## V1 Perturbation Catalog

All variants are **deterministic** and identified by stable `variant_id` strings. Implementation must not add random draws in V1.

### Tier A — Selection stability (counts toward `favored_stable_rate`)

Each variant recomputes `selection_score(c)` per [selection_engine_spec.md](selection_engine_spec.md) using exported totals and mandate rules, then applies favored-target rules with optional overrides.

| `variant_id` | Description | `w_health` | `w_robust` | `w_mandate` | `apply_policy_default` |
| --- | --- | --- | --- | --- | --- |
| `baseline_selection` | Mirror current selection weights and policy default | 0.45 | 0.45 | 0.10 | true |
| `health_heavy` | Stress decision toward Health | 0.55 | 0.35 | 0.10 | true |
| `robust_heavy` | Stress decision toward Robustness | 0.35 | 0.55 | 0.10 | true |
| `health_dominant` | Extreme Health emphasis | 0.60 | 0.30 | 0.10 | true |
| `robust_dominant` | Extreme Robustness emphasis | 0.30 | 0.60 | 0.10 | true |
| `health_only_proxy` | Health-only composite (robust weight 0; renormalize health+mandate to 1.0) | 0.90 | 0.00 | 0.10 | true |
| `robust_only_proxy` | Robustness-only composite | 0.00 | 0.90 | 0.10 | true |
| `composite_only_no_policy_default` | Baseline weights but **no** automatic policy favor; argmax composite among eligible non-current | 0.45 | 0.45 | 0.10 | **false** |

**Eligibility and tie-break:** same as Selection V1 (mandate hard exclude, tie-break on robustness rank then health rank then `candidate_id`).

**`baseline_selection` check:** `effective_favored_id` must equal `selection_decision.favored_candidate_id` when inputs are consistent; if not, emit warning `baseline_recompute_mismatch` (implementation bug or stale selection file).

### Tier B — Evidence stability (informational only)

Does **not** update `favored_stable_rate`. Reports whether the baseline favored candidate leads under a simple single-metric rule.

| `variant_id` | Rule | Primary field |
| --- | --- | --- |
| `sharpe_rank_3y` | Among `available`/`degraded` non-current candidates with `metrics.3y.sharpe`, highest Sharpe wins | `candidate_comparison.metrics.3y.sharpe` |
| `sharpe_rank_5y` | Same for 5y | `metrics.5y.sharpe` |
| `sharpe_rank_10y` | Same for 10y | `metrics.10y.sharpe` |
| `stress_worst_loss_rank` | Among same set with `stress.scenarios` or worst loss field, **least negative** worst loss wins (see below) | comparison `stress` block |

**Stress worst-loss tie-break:** use the minimum (algebraically largest) scenario PnL across abbreviated `stress.scenarios[]` when present; else skip variant with `skipped_reason: stress_summary_incomplete`.

**Tier B output per variant:** `evidence_leader_id`, `matches_baseline_favored` (bool), `runner_up_id` optional, `margin_sharpe` or `margin_worst_loss` when computable.

### Explicitly out of V1 catalog

| Topic | Rationale |
| --- | --- |
| Expected return ±20–30% | Requires optimizer or return-forecast layer not in comparison artifacts. |
| Covariance window 3Y/5Y/10Y re-estimation | Would recompute Health/Robustness; defer to V2 with scorecard re-run flag. |
| Stress severity / correlation stress | Owned by stress spec; not a lightweight comparison perturbation. |
| Rebalance frequency / transaction costs | No V1 cost model in selection path. |
| No-Trade threshold ±% | Deferred; can add `no_trade_threshold_stress` in V2 after Action/Selection threshold profiles stabilize. |
| Perturbing `analysis_setup` / FX / risk-free | Input-integrity layer ([input_assumptions_spec.md](input_assumptions_spec.md)); use data-quality warnings instead. |

## Stability Scoring (V1)

### Tier A aggregates

```text
favored_stable_rate =
  count(Tier A variants where effective_favored_id == baseline_favored_id)
  / count(Tier A variants with status == "evaluated")
```

| `stability_status` | Condition (Tier A) |
| --- | --- |
| `stable` | `favored_stable_rate` >= 0.80 |
| `moderate` | `favored_stable_rate` >= 0.60 and < 0.80 |
| `fragile` | `favored_stable_rate` < 0.60 |
| `not_evaluated` | No Tier A variants evaluated |

**Flippers:** list `variant_id` values where `effective_favored_id != baseline_favored_id` with `effective_favored_display_name` and short `flip_note` (e.g. "Robustness-heavy weights favor risk_parity over policy").

**Policy-default sensitivity:** if `composite_only_no_policy_default` disagrees with baseline, set `policy_default_sensitive: true` and explain in TXT summary (policy role vs pure composite).

### Tier B aggregates

| Field | Meaning |
| --- | --- |
| `evidence_agreement_rate` | Share of Tier B variants where `matches_baseline_favored` is true |
| `evidence_conflict_variants` | List of variant_ids with `matches_baseline_favored == false` |

Low Tier B agreement with high Tier A stability means: *selection rules are stable but simple metric leaders differ* — downgrade narrative confidence, not selection output.

### Confidence hints (diagnostic text only)

| Pattern | Suggested plain-English line |
| --- | --- |
| `stable` + high evidence agreement | "Favored profile is stable under reviewable weight and evidence checks." |
| `stable` + low evidence agreement | "Selection is stable under score weights, but single-metric window leaders sometimes differ; review drivers." |
| `fragile` or `policy_default_sensitive` | "Favored profile is assumption-sensitive; treat selection as provisional until trade-offs and model risk are reviewed." |
| `fragile` + high model risk severity | "Ranking instability coincides with elevated model-risk warnings." |

## Top-Level JSON (`assumption_sensitivity_v1`)

```json
{
  "schema_version": "assumption_sensitivity_v1",
  "diagnostic_only": true,
  "non_executing": true,
  "generated_at": "ISO-8601",
  "analysis_end": "YYYY-MM-DD",
  "sensitivity_status": "complete",
  "baseline_favored_id": "policy",
  "baseline_favored_display_name": "Policy (Optimized)",
  "baseline_decision_status": "selected_candidate",
  "stability_status": "stable",
  "favored_stable_rate": 0.875,
  "policy_default_sensitive": false,
  "tier_a_variants": [],
  "tier_b_variants": [],
  "flippers": [],
  "evidence_agreement_rate": 0.75,
  "summary_plain_en": "Favored profile policy remained favored in 7 of 8 selection-weight variants.",
  "warnings": [],
  "input_artifacts": {
    "selection_decision.json": "selection_decision.json",
    "portfolio_health_score.json": "portfolio_health_score.json",
    "robustness_scorecard.json": "robustness_scorecard.json",
    "candidate_comparison.json": "candidate_comparison.json"
  }
}
```

### Variant row (Tier A)

| Field | Type | Description |
| --- | --- | --- |
| `variant_id` | string | Catalog id |
| `tier` | string | `"A"` |
| `status` | string | `evaluated` \| `skipped` \| `not_applicable` |
| `skipped_reason` | string \| null | e.g. `partial_score_inputs` |
| `w_health`, `w_robust`, `w_mandate` | number | Weights used |
| `apply_policy_default` | bool | |
| `effective_favored_id` | string \| null | |
| `effective_favored_display_name` | string \| null | |
| `matches_baseline_favored` | bool | |
| `top_three_composite` | array | Optional: `candidate_id`, `selection_score` (3 decimals at export) |

### Variant row (Tier B)

| Field | Type | Description |
| --- | --- | --- |
| `variant_id` | string | Catalog id |
| `tier` | string | `"B"` |
| `status` | string | `evaluated` \| `skipped` |
| `evidence_leader_id` | string \| null | |
| `matches_baseline_favored` | bool | |
| `margin_vs_runner_up` | number \| null | Sharpe or loss gap; 3 decimals at export |

### Required top-level fields

| Field | Required | Description |
| --- | --- | --- |
| `schema_version` | yes | `assumption_sensitivity_v1` |
| `diagnostic_only` | yes | always `true` |
| `sensitivity_status` | yes | `complete` \| `selection_unavailable` \| `no_baseline_favored` \| `partial` |
| `baseline_favored_id` | when known | From selection |
| `stability_status` | yes | Tier A band |
| `favored_stable_rate` | yes | 0–1, three decimals at export |
| `tier_a_variants` | yes | Full catalog rows |
| `tier_b_variants` | yes | Full catalog rows |
| `summary_plain_en` | yes | 1–3 sentences, client-safe |
| `warnings` | yes | May be empty |

## TXT Summary (V1)

Plain English, fixed sections:

1. **Baseline** — favored profile and decision status (display names).
2. **Selection stability** — `stability_status`, `favored_stable_rate`, flipper list or "none".
3. **Policy-default check** — one line on `composite_only_no_policy_default`.
4. **Evidence checks** — Tier B agreement rate and conflicts.
5. **Interpretation** — one short paragraph using confidence hints; no buy/sell.

## Downstream Consumers

| Consumer | Use |
| --- | --- |
| [decision_package_reporting_spec.md](decision_package_reporting_spec.md) | Optional subsection after trade-off (Session 15). |
| [decision_journal_spec.md](decision_journal_spec.md) | Optional `assumption_stability` block citing `stability_status` and `summary_plain_en`. |
| PDF / `report.txt` | Short stability line when summary exists; map `fragile` to "assumption-sensitive" client wording. |

Journal and reporting must **not** override `selection_decision.json` when stability is `fragile`.

## Tests (Session 15 implementation)

Minimum focused tests:

1. Tier A `baseline_selection` matches `selection_decision.favored_candidate_id`.
2. `health_dominant` vs `robust_dominant` flip favored on synthetic unequal scores.
3. `composite_only_no_policy_default` can differ from baseline when policy is mandate-clean but not composite-best.
4. Tier B skipped when `metrics.10y.sharpe` missing for all candidates.
5. Missing selection → `selection_unavailable` without exception.
6. Pipeline integration: file emitted after trade-off in `write_candidate_comparison_outputs`.

## Related Specifications

- [selection_engine_spec.md](selection_engine_spec.md) — baseline favored rules and composite formula.
- [candidate_comparison_spec.md](candidate_comparison_spec.md) — metric and stress blocks for Tier B.
- [portfolio_health_score_spec.md](portfolio_health_score_spec.md) — `total_score` inputs.
- [robustness_scorecard_spec.md](robustness_scorecard_spec.md) — `total_score` inputs.
- [tradeoff_and_model_risk_spec.md](tradeoff_and_model_risk_spec.md) — complementary diagnostics.
- [decision_package_reporting_spec.md](decision_package_reporting_spec.md) — reporting integration (Session 15).
