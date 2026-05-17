# Trade-off Explanation and Model Risk Diagnostics Specification

This document owns the **Trade-off Explanation** and **Model Risk Diagnostics** diagnostic layers: structured artifacts that make the **price of improvement** and **limits of model confidence** explicit after comparison and selection, without changing favored profiles, scores, or trade lists.

It does not own metric formulas, stress scenario definitions, scorecard math, selection rules, action trade construction, or optimizer release policy. Those remain in [metrics_specification.md](metrics_specification.md), [stress_testing_spec.md](stress_testing_spec.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [robustness_scorecard_spec.md](robustness_scorecard_spec.md), [portfolio_health_score_spec.md](portfolio_health_score_spec.md), [selection_engine_spec.md](selection_engine_spec.md), and [action_engine_spec.md](action_engine_spec.md).

Implementation: [src/tradeoff_and_model_risk.py](../../src/tradeoff_and_model_risk.py) (post-audit Session 13; must not collide with `src/robustness.py` optimizer stability). This document is the contract.

## Scope

The trade-off and model-risk layers:

- read **`candidate_comparison.json`**, **`selection_decision.json`**, and optional **`action_plan.json`**, **`portfolio_health_score.json`**, **`robustness_scorecard.json`**, and per-candidate **`stress_report.json`** / **`run_result.json`** only through paths already recorded in comparison `source_files` (no duplicate metric formulas);
- emit **`tradeoff_explanation.json`** / **`.txt`** and **`model_risk_diagnostics.json`** / **`.txt`** under `output_dir_final`;
- express **deltas** (improves / worsens / cost of change) in neutral decision-support English;
- aggregate **model-risk warnings** into one machine-readable taxonomy with severity and plain-English notes;
- remain **diagnostic-only** and **non-binding** (do not change selection, action, mandate pass/fail, or weights);
- do **not** replace Selection `rationale.tradeoff_bullets` in V1 — they **supersede** them for journal and reporting when present (see [Downstream consumers](#downstream-consumers)).

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Trade-off Explanation** (this spec) | Candidate-level deltas vs baseline: return, risk, stress, turnover cost. |
| **Model Risk Diagnostics** (this spec) | Unified self-criticism layer: data, estimator, factor, stress-coverage, concentration, mandate warnings. |
| **Selection Engine** | Formal favored profile and No-Trade; may emit short `tradeoff_bullets` until this layer exists. |
| **Portfolio Health Score** | Holistic quality score; `mandate_and_model_risk` component is a score input, not this artifact. |
| **Portfolio commentary / X-Ray** | Narrative diagnostics per portfolio folder; not the canonical cross-candidate trade-off table. |
| **Assumption Sensitivity** | Selection stability under weight/window perturbations ([assumption_sensitivity_spec.md](assumption_sensitivity_spec.md)); complementary, not duplicate. |
| **Pareto / Dominance** | Multi-criteria dominance among candidates ([pareto_dominance_spec.md](pareto_dominance_spec.md)); complementary; may reuse turnover vs current definition. |

## Product Boundary

- Answers: *If I move from baseline A to favored B, what gets better, what gets worse, and what does it cost?* and *Where should I treat conclusions with extra caution?*
- Does **not** answer: *execute these trades*, *this portfolio will outperform*, or *override selection because model risk is high*.
- Forbidden in exported text: imperative buy/sell, performance guarantees, raw internal codes (`FAIL_*`, `DIAG_*`, `WARN_*`) in PDF-facing paths (map to English labels per [decision_package_reporting_spec.md](decision_package_reporting_spec.md)).

**Tone (V1):** institutional decision-support English, same as Selection and Action artifacts.

## V1 User Decisions (2026-05-17, Post-audit Session 12)

Recorded defaults when the user continues without overrides:

1. **Two artifacts:** separate `tradeoff_explanation_v1` and `model_risk_diagnostics_v1` JSON files plus companion TXT summaries (not one combined file).
2. **Primary trade-off pair:** **baseline** = `user_current` (`current`) when `status` is `available` or `degraded`; **target** = `selection_decision.favored_candidate_id` when present. If current is unavailable, emit `tradeoff_status: baseline_unavailable` and still allow **policy-vs-benchmark** secondary pairs documented below.
3. **Primary window:** `10y` for metric and drawdown deltas; stress deltas use comparison `stress` block (10y-aligned snapshot stress).
4. **Turnover:** prefer `action_plan.turnover_half_sum_pct` when action exists for the favored target; else compute half-sum absolute weight deltas from `snapshot_10y.final_weights_total` on baseline and target artifact roots (same definition as Action Engine).
5. **No new formulas:** all numeric deltas are differences of fields already exported in comparison or action artifacts, rounded to **three decimals** at export only per [metrics_specification.md](metrics_specification.md).
6. **Model risk:** normalize existing warnings into a catalog; do not invent new statistical tests in V1.
7. **Binding boundary:** artifacts are evidence for humans and reports; Selection output is unchanged by this layer.

## Canonical Artifacts

| File | Schema | Required |
| --- | --- | --- |
| `tradeoff_explanation.json` | `tradeoff_explanation_v1` | Yes when comparison exists |
| `tradeoff_explanation.txt` | plain English | Yes when JSON is written |
| `model_risk_diagnostics.json` | `model_risk_diagnostics_v1` | Yes when comparison exists |
| `model_risk_diagnostics.txt` | plain English | Yes when JSON is written |

Location: `{output_dir_final}/` (default `Main portfolio/`).

## Pipeline Placement

```text
run_compare_variants.py
  -> write_candidate_comparison_outputs
       -> comparison, robustness, health
       -> selection_decision
       -> [Session 13] tradeoff_explanation + model_risk_diagnostics  (this spec)
       -> current_vs_policy_status
       -> action_plan
       -> monitoring, journal, decision_package_reporting
```

**Order (V1):** immediately **after** `selection_decision.json` is written and **before** `action_plan.json`.

Rationale: trade-off needs `favored_candidate_id`; turnover in trade-off may read action when implementation chooses to run action first — **spec default** is compute turnover from weights when action is not yet available at trade-off write time, then allow reporting to prefer action turnover when both exist. Session 13 may either (a) write trade-off before action and omit action-sourced turnover until a later refresh, or (b) write trade-off after action; if (b) is chosen, update this section and add a regression test. **Default contract:** trade-off runs before action; turnover from weight deltas only; optional `action_turnover_reference` field filled when action exists on a second pass is **out of scope** for V1 — use weight-based turnover at trade-off write time.

## Inputs

### Required

| Input | Minimum fields |
| --- | --- |
| `candidate_comparison.json` | `analysis_end`, `primary_window`, `candidates[]` with `candidate_id`, `status`, `role`, `metrics`, `drawdown`, `stress`, `mandate`, `warnings`, `source_files` |
| `selection_decision.json` | `decision_status`, `favored_candidate_id`, `favored_display_name`, `rationale`, `warnings`, `input_artifacts` |

### Optional (improve coverage, never required to write artifacts)

| Input | Use |
| --- | --- |
| `action_plan.json` | Not read at trade-off write time in V1 (see pipeline note). |
| `portfolio_health_score.json` / `robustness_scorecard.json` | Propagate candidate-level `warnings` into model-risk aggregation. |
| `stress_report.json` (via `source_files`) | Factor regression HAC blocks, multicollinearity, rolling beta errors, scenario coverage. |
| `run_result.json` / `run_metadata.json` | Optimizer warnings, `portfolio_valid`, young-ETF model-risk flags. |
| `current_vs_policy_status.json` | No-Trade actionability context for trade-off narrative (informational only). |

### Skip behavior

| Condition | Behavior |
| --- | --- |
| Missing `candidate_comparison.json` | Do not write either artifact; run warning `tradeoff_skipped_missing_comparison`. |
| Missing `selection_decision.json` | Write `model_risk_diagnostics` from comparison only; `tradeoff_explanation` with `tradeoff_status: selection_unavailable` and empty pairs. |
| Missing favored target | `tradeoff_status: no_favored_target`; model risk still aggregates run-level warnings. |

---

## Part A — Trade-off Explanation (`tradeoff_explanation_v1`)

### Top-level JSON

```json
{
  "schema_version": "tradeoff_explanation_v1",
  "diagnostic_only": true,
  "non_executing": true,
  "generated_at": "ISO-8601",
  "analysis_end": "YYYY-MM-DD",
  "primary_window": "10y",
  "tradeoff_status": "complete",
  "baseline_candidate_id": "current",
  "target_candidate_id": "policy",
  "selection_decision_status": "no_material_rebalance",
  "pairs": [],
  "summary": {},
  "improves": [],
  "worsens": [],
  "cost_of_change": {},
  "warnings": [],
  "input_artifacts": {}
}
```

### `tradeoff_status`

| Value | Meaning |
| --- | --- |
| `complete` | Primary pair computed with at least one improves/worsens dimension. |
| `baseline_unavailable` | No `current` row or current not scored; secondary pairs may still be present. |
| `no_favored_target` | Selection did not name a favored candidate id. |
| `selection_unavailable` | `selection_decision.json` missing. |
| `insufficient_metrics` | Baseline and target exist but primary-window metrics missing on one side. |

### Comparison pairs (`pairs[]`)

Each pair is a structured delta block. V1 requires **at least one** entry when status is `complete`.

#### Primary pair (required when baseline available and favored target present)

| Field | Value |
| --- | --- |
| `pair_id` | `current_to_favored` |
| `baseline_candidate_id` | `current` |
| `target_candidate_id` | favored id |
| `baseline_display_name` / `target_display_name` | from comparison |
| `dimensions` | array of dimension objects (below) |

#### Secondary pairs (optional, V1)

| `pair_id` | When emitted |
| --- | --- |
| `policy_to_favored` | Favored is not `policy` but policy row is available. |
| `current_to_policy` | Both current and policy available (even when favored is policy — reinforces No-Trade context). |
| `favored_to_runner_up` | Second-highest composite from `selection_decision.composite_ranking` when scored and distinct from favored. |

### Dimension objects (`dimensions[]`)

Each dimension uses **pre-exported** comparison fields only. Direction labels are from the **investor perspective** (higher CAGR is "improves" for return; less negative max drawdown is "improves" for drawdown).

| `dimension_id` | Baseline field | Target field | Improves when |
| --- | --- | --- | --- |
| `return_cagr` | `metrics.10y.cagr` | same | target > baseline |
| `risk_vol` | `metrics.10y.vol_annual` | same | target < baseline |
| `drawdown` | `metrics.10y.max_drawdown` or `drawdown.max_drawdown` | same | target > baseline (less negative) |
| `risk_adjusted_sharpe` | `metrics.10y.sharpe` | same | target > baseline |
| `stress_worst_loss` | min `stress.scenarios[].portfolio_pnl_pct` or worst scenario field on row | same | target > baseline (smaller loss) |
| `stress_overall` | encoded rank of `stress.overall` | same | target better rank |
| `health_score` | `portfolio_health_score` total for id | same | target > baseline (optional) |
| `robustness_score` | `robustness_scorecard` total for id | same | target > baseline (optional) |

Each dimension object:

| Field | Type | Description |
| --- | --- | --- |
| `dimension_id` | string | Stable id from table above. |
| `baseline_value` | number \| null | |
| `target_value` | number \| null | |
| `delta` | number \| null | `target - baseline` for levels; for drawdown/stress loss, document sign in `delta_note`. |
| `delta_unit` | string | `pct`, `ratio`, `score_points`, `rank`. |
| `direction` | string | `improves` \| `worsens` \| `unchanged` \| `unknown`. |
| `plain_english` | string | One short sentence, e.g. "10y CAGR is 0.8 percentage points lower on the favored profile." |

Missing on either side: `direction: unknown`, omit from aggregate `improves`/`worsens` lists, add warning `tradeoff_dimension_missing_{dimension_id}`.

### Aggregate lists

| Field | Rule |
| --- | --- |
| `improves` | `dimension_id` list where `direction === improves` on primary pair. |
| `worsens` | `dimension_id` list where `direction === worsens` on primary pair. |
| `summary.headline` | 1–2 sentences: favored name, baseline name, counts of improves/worsens. |
| `summary.tradeoff_paragraph` | 2–4 sentences synthesizing return vs risk vs stress vs turnover (neutral). |

### `cost_of_change`

| Field | Source | Description |
| --- | --- | --- |
| `turnover_half_sum_pct` | weight deltas baseline vs target | Half-sum of absolute weight changes; null if weights missing. |
| `estimated_transaction_cost_pct` | optional | **Not computed in trade-off V1**; Action Engine owns 10 bps model. TXT may reference action artifact when present. |
| `weight_shifts_top` | optional | Up to 5 largest absolute weight deltas (ticker, delta_pct) from snapshots. |
| `no_trade_context` | selection | Copy `no_trade` summary fields when `decision_status === no_material_rebalance` (informational). |

### TXT format (`tradeoff_explanation.txt`)

Fixed sections:

1. Header — analysis end, tradeoff status, non-executing disclaimer.
2. Primary pair headline — baseline → target display names.
3. **What improves** — bullet list from `improves` with plain_english lines.
4. **What worsens** — bullet list from `worsens`.
5. **Cost of change** — turnover and top weight shifts when present.
6. **Selection context** — one line from `selection_decision_status` (no imperative rebalance).
7. Pointer to JSON for secondary pairs.

---

## Part B — Model Risk Diagnostics (`model_risk_diagnostics_v1`)

### Purpose

Collect **existing** warnings and diagnostic flags into one layer so reports do not require the user to open stress, optimizer, and score files separately. This is the system's **self-criticism** surface (product concept section 18).

### Top-level JSON

```json
{
  "schema_version": "model_risk_diagnostics_v1",
  "diagnostic_only": true,
  "generated_at": "ISO-8601",
  "analysis_end": "YYYY-MM-DD",
  "overall_severity": "moderate",
  "summary_plain_en": "Two high-severity items require review: low 10y factor R² on policy and incomplete stress scenario coverage for one candidate.",
  "warning_count": { "high": 1, "medium": 2, "low": 1, "info": 0 },
  "warnings": [],
  "by_category": {},
  "by_candidate": {},
  "run_level_notes": [],
  "input_artifacts": {}
}
```

### `overall_severity`

| Value | Rule |
| --- | --- |
| `none` | No warnings after deduplication. |
| `low` | Only `low` / `info`. |
| `moderate` | At least one `medium`, no `high`. |
| `high` | At least one `high`. |
| `critical` | Reserved for mandate `portfolio_valid === false` on **policy** or favored target (V1 maps to `high` with category `mandate` unless product later splits `critical`). |

### Warning object

| Field | Type | Description |
| --- | --- | --- |
| `warning_id` | string | Stable machine id (snake_case). |
| `category` | string | See [Categories](#warning-categories). |
| `severity` | string | `high` \| `medium` \| `low` \| `info`. |
| `candidate_id` | string \| null | null = run-wide. |
| `source_artifact` | string | e.g. `stress_report.json`, `candidate_comparison.json`. |
| `source_field` | string \| null | JSON path or code reference when known. |
| `code` | string \| null | Original upstream code when present (`WARN_*`, `fail_reason_code`, etc.). |
| `plain_english` | string | Client-safe explanation (no raw codes in PDF export path). |
| `review_hint` | string \| null | Optional: what to check next (still non-executing). |

Deduplicate by (`warning_id`, `candidate_id`) keeping highest severity.

### Warning categories

| `category` | V1 sources (examples) |
| --- | --- |
| `data_quality` | comparison `warnings`, `missing_fields`, degraded candidate status, young ETF flags from `run_result.json`. |
| `expected_return_estimation` | robust MV / optimizer messages about return instability when present in run metadata (policy folder). |
| `covariance_risk_model` | covariance condition or robust optimizer diagnostics when present in linked artifacts. |
| `factor_model` | low `adj_r2` on `factor_regression_10y`, high multicollinearity severity from stress report, rolling beta errors. |
| `stress_coverage` | missing scenarios, partial stress on comparison row, `stress_report` fallback noted in robustness scorecard. |
| `concentration` | high `weight_concentration` or `diversification` top1 metrics on policy/favored rows (thresholds: informational only in V1 — flag when top1 weight > 25% or top1 RC > 35% as **medium**, > 40% / > 45% as **high**; document in implementation, do not change mandate gates). |
| `window_sensitivity` | comparison run-level warning `mixed_analysis_dates` or mismatched `analysis_end` across candidates. |
| `mandate` | `mandate.portfolio_valid === false`, hard constraint failures. |
| `selection_confidence` | selection `warnings`, `data_review_required`, partial score inputs, `no_trade_not_evaluated`. |
| `score_degradation` | health/robustness `not_scored` or `not_computed` on favored or policy row. |

### Catalog (V1 required ids)

Implementation must emit a row when the upstream condition is true. Severity may be tuned in Session 13 but ids are stable.

| `warning_id` | Category | Typical severity | Trigger (summary) |
| --- | --- | --- | --- |
| `factor_adj_r2_low_10y` | `factor_model` | medium | policy or favored: `adj_r2` or `adj_r_squared` < 0.35 on 10y regression |
| `factor_multicollinearity_elevated` | `factor_model` | medium/high | stress multicollinearity `severity` in (`elevated`, `severe`) |
| `factor_rolling_betas_error` | `factor_model` | medium | `factor_betas_rolling_error` present on stress report |
| `stress_partial_coverage` | `stress_coverage` | medium | candidate `stress` in `missing_fields` or degraded stress |
| `stress_fail_on_favored` | `stress_coverage` | high | favored or policy `stress.overall` indicates fail (map per stress spec labels) |
| `candidate_degraded` | `data_quality` | medium | `status === degraded` on favored, policy, or current |
| `current_unavailable` | `selection_confidence` | low | current row unavailable — No-Trade not fully grounded |
| `selection_partial_scores` | `selection_confidence` | medium | selection warning `partial_score_inputs` |
| `selection_data_review` | `selection_confidence` | high | `decision_status === data_review_required` |
| `mandate_portfolio_invalid` | `mandate` | high | `mandate.portfolio_valid === false` on policy or favored |
| `concentration_weight_top1_high` | `concentration` | medium/high | top1 weight thresholds above |
| `concentration_rc_top1_high` | `concentration` | medium/high | top1 RC thresholds above |
| `mixed_analysis_dates` | `window_sensitivity` | medium | comparison run warning |
| `young_etf_weight_warn` | `data_quality` | medium | `WARN_MODEL_RISK_YOUNG_WEIGHT` in run_result |
| `health_not_scored_favored` | `score_degradation` | medium | favored id `score_status === not_scored` in health file |
| `robustness_not_scored_favored` | `score_degradation` | medium | same for robustness |

Additional upstream codes may be passed through as `code` with a generated `warning_id` prefix `upstream_`.

### `by_candidate` object

Keys = `candidate_id`. Values = arrays of `warning_id` for quick UI/report indexing.

### `by_category` object

Keys = category id. Values = count by severity.

### TXT format (`model_risk_diagnostics.txt`)

1. Header — overall severity, analysis end.
2. **Summary** — `summary_plain_en`.
3. **High and medium** — bullets grouped by severity (English only).
4. **Low / info** — optional collapsed section if more than three items.
5. **Per-candidate** — policy, current, favored only (omit unavailable ids).
6. Pointer to JSON for full catalog.

---

## Downstream consumers

| Consumer | V1 behavior |
| --- | --- |
| [decision_journal_spec.md](decision_journal_spec.md) | Prefer `tradeoff_explanation.summary.tradeoff_paragraph` and top improves/worsens over selection `tradeoff_bullets` when JSON exists. |
| [decision_package_reporting_spec.md](decision_package_reporting_spec.md) | Session 13 adds optional sections **Trade-offs** and **Model risk** sourced from these artifacts. |
| [selection_engine_spec.md](selection_engine_spec.md) | May continue to emit short `tradeoff_bullets`; not required to duplicate full trade-off when this layer is present. |
| PDF / `report.txt` | Summaries only; no raw warning codes. |

## Diagnostic Boundary

- Does **not** change `decision_status`, favored candidate, action trades, or optimizer weights.
- Does **not** upgrade or downgrade stress pass/fail or production release.
- High model-risk severity is **not** an automatic veto; narrative must say conclusions are less reliable, not "do not invest."

## Verification (Session 13)

- `tests/test_tradeoff_and_model_risk.py` — fixture comparison + selection; asserts JSON schema, primary pair deltas, deduplicated warnings, baseline_unavailable path.
- Integration: after `write_candidate_comparison_outputs`, both JSON files exist under `output_dir_final`.
- `python scripts/verify_docs.py` after doc updates.

## Related specifications

- [candidate_comparison_spec.md](candidate_comparison_spec.md)
- [selection_engine_spec.md](selection_engine_spec.md)
- [action_engine_spec.md](action_engine_spec.md)
- [portfolio_health_score_spec.md](portfolio_health_score_spec.md)
- [robustness_scorecard_spec.md](robustness_scorecard_spec.md)
- [stress_testing_spec.md](stress_testing_spec.md)
- [data_policy_spec.md](data_policy_spec.md)
- [decision_package_reporting_spec.md](decision_package_reporting_spec.md)
- [decision_journal_spec.md](decision_journal_spec.md)
- [reporting_outputs_spec.md](reporting_outputs_spec.md)
- [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md)
