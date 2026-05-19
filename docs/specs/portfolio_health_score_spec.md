# Portfolio Health Score Specification

This document owns the **Portfolio Health Score** contract: a transparent, diagnostic-only holistic quality score for each portfolio candidate in a comparison run.

It does not own metric formulas, stress scenario definitions, candidate construction, robustness scoring logic, or selection logic. Those remain in [metrics_specification.md](metrics_specification.md), [stress_testing_spec.md](stress_testing_spec.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [robustness_scorecard_spec.md](robustness_scorecard_spec.md), and [selection_engine_spec.md](selection_engine_spec.md).

## Scope

The Portfolio Health Score:

- reads **`candidate_comparison.json`** as its **primary** input;
- may read **`robustness_scorecard.json`** for the optional **`resilience_reference`** component only (no duplicate robustness formulas);
- produces **`portfolio_health_score.json`** (and optional **`portfolio_health_score.txt`**) under `output_dir_final`;
- scores **every registry candidate** that is `available` or `degraded`; marks `unavailable` candidates as `not_scored`;
- blends **relative normalization within the current comparison run** with **absolute mandate and model-risk checks**;
- stays **diagnostic-only**: no buy/sell language, no automatic portfolio selection, no override of stress pass/fail or optimizer release.

Implementation: [src/portfolio_health_score.py](../../src/portfolio_health_score.py) (Session 13). This document is the contract.

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Portfolio Health Score** (this spec) | Holistic investor-facing quality score 0–100 with explanatory drivers. |
| **Robustness Scorecard** | Separate resilience ranking among candidates ([robustness_scorecard_spec.md](robustness_scorecard_spec.md)). |
| **`src/robustness.py`** | Dual-horizon **optimizer weight stability** (10Y vs 5Y); unrelated to either score. |
| **Selection Engine** | Formal decision artifact ([selection_engine_spec.md](selection_engine_spec.md); implementation Session 15). |

## Product Boundary

- The Health Score answers: *how balanced, implementable, and fit-for-mandate does this portfolio profile appear overall?*
- The Robustness Scorecard answers: *among these candidates, which profile appears more crisis-resilient?*
- It does **not** answer: *which portfolio should the client buy?*
- Allowed narrative: descriptive totals, component drivers, and comparative phrasing (e.g. "Current portfolio health is 62/100, mainly dragged by weight concentration and stagflation stress loss.").
- Forbidden: imperative trade advice, "recommended portfolio", or implying Selection Engine outcomes before that module exists.

Report surfaces should list **`analysis_subject`** first when the portfolio-first subject is
available (`display_priority`), then other candidates by `health_rank`. Legacy current-vs-policy
runs without an available `analysis_subject` keep the old `current`, then `policy` priority.

## V1 User Decisions (2026-05-17)

Recorded for Session 12:

1. **Candidate set:** score every `available` / `degraded` row in `candidate_comparison.json`; `unavailable` -> `not_scored`.
2. **Display priority:** portfolio-first reports and TXT summaries show `analysis_subject` as the
   priority row when it exists. Legacy current-vs-policy reports show `current` and `policy` before
   benchmarks when both exist.
3. **Normalization:** primary sub-scores use **within-run percentile ranks**; **`mandate_and_model_risk`** and parts of **`liquidity_implementation`** use **absolute** artifact status.
4. **Robustness boundary:** do **not** re-implement the six Robustness Scorecard components; optional **`resilience_reference`** (10%) ingests `robustness_scorecard.json` `total_score` when present.
5. **Component weights:** product-concept defaults as **`default_weights_reviewable`** (sum = 1.0); may be revised after validation.
6. **Primary window:** **10y** for metrics and drawdown; stress inputs follow [stress_testing_spec.md](stress_testing_spec.md) ids available in comparison or linked artifacts.

## Canonical Artifacts

| Field | Value |
| --- | --- |
| File name | `portfolio_health_score.json` |
| Location | `{output_dir_final}/portfolio_health_score.json` |
| Companion (optional) | `{output_dir_final}/portfolio_health_score.txt` |
| Schema version | `portfolio_health_score_v1` |
| Primary input | `{output_dir_final}/candidate_comparison.json` |
| Secondary input (optional) | `{output_dir_final}/robustness_scorecard.json` |

## Overlap With Robustness Scorecard

| Topic | Robustness Scorecard | Portfolio Health Score |
| --- | --- | --- |
| Primary lens | Crisis resilience, stress PnL, downside | Holistic quality, balance, fit, implementability |
| Stress | Central (20% component) | Lighter `stress_behavior` (10%); no duplicate full stress suite weighting |
| Diversification | RC-only `diversification_rc` | RC plus **weight** concentration |
| Return | `return_efficiency` | `risk_adjusted_return` (similar inputs, different weight and narrative role) |
| Factor | `factor_stability` (fit, rolling) | `factor_balance` (beta dispersion / concentration) |
| Mandate | `mandate_fit` (10%) | `mandate_and_model_risk` (absolute emphasis + warnings) |
| Cross-score | N/A | Optional `resilience_reference` reads robustness **total** only |

When both artifacts exist, reports may show both scores side by side. Health Score must **not** be labeled as a substitute for Robustness or Selection.

## Component Model

Ten components. Weights apply to the **component score** (each 0–100 after normalization).

| Component id | Display name | Default weight | Role |
| --- | --- | --- | --- |
| `structural_diversification` | Structural diversification (RC) | 0.15 | RC concentration from comparison `diversification` |
| `weight_concentration` | Weight concentration | 0.10 | Largest and top-3 **weights** (not RC) |
| `drawdown_resilience` | Drawdown resilience | 0.15 | Max drawdown and recovery (10y) |
| `stress_behavior` | Stress behavior | 0.10 | Stress overall, worst scenario, pass rate (abbreviated vs robustness) |
| `risk_adjusted_return` | Risk-adjusted return | 0.14 | CAGR, Sharpe, Sortino (10y) |
| `factor_balance` | Factor balance | 0.09 | Factor beta dispersion / balance (10y regression) |
| `macro_regime_fit` | Macro regime fit | 0.06 | Macro regime diagnostics when present |
| `liquidity_implementation` | Liquidity / implementation | 0.05 | Liquidity and tradability proxies from artifacts |
| `mandate_and_model_risk` | Mandate and model risk | 0.06 | Absolute validity, constraints, run warnings |
| `resilience_reference` | Resilience reference | 0.10 | Optional ingest of robustness `total_score` |

Weights profile id: **`default_weights_reviewable`**. Document any change in [DECISIONS.md](../../DECISIONS.md).

```json
{
  "structural_diversification": 0.15,
  "weight_concentration": 0.10,
  "drawdown_resilience": 0.15,
  "stress_behavior": 0.10,
  "risk_adjusted_return": 0.14,
  "factor_balance": 0.09,
  "macro_regime_fit": 0.06,
  "liquidity_implementation": 0.05,
  "mandate_and_model_risk": 0.06,
  "resilience_reference": 0.10
}
```

When `robustness_scorecard.json` is missing, set `resilience_reference.status` to `not_computed`, re-weight remaining components proportionally, and add warning `robustness_scorecard_missing`.

## Windows and Stress Inputs

### Metrics and drawdown

- **Primary window:** `10y` (from `candidate_comparison.primary_window`, default `10y`).
- Sub-indicators read `candidates[*].metrics.10y` and `candidates[*].drawdown` unless noted.

### Stress behavior

Use the same scenario id vocabulary as [robustness_scorecard_spec.md](robustness_scorecard_spec.md). Prefer abbreviated rows from `candidates[*].stress.scenarios`; fall back to `stress_report.json` via `source_files` when historical episodes are missing from the comparison row. Record `stress_inputs_source` (`comparison` | `stress_report_fallback` | `partial`).

Health Score uses **fewer** stress sub-indicators than Robustness (no separate mean/worst/pass-rate duplication beyond the three listed below).

## Relative Normalization (Within-Run)

Same rules as Robustness Scorecard unless noted:

1. Collect raw values across candidates with `score_status` in (`scored`, `partial`).
2. Direction: higher is better or lower is better per sub-indicator table.
3. Map to 0–100 via **percentile rank** among scored candidates.
4. Ties: equal raw values -> equal sub-scores.
5. **Single scored candidate:** relative sub-scores default to **50** with warning `single_candidate_comparison`.
6. **Missing sub-indicator:** exclude from rank; if fewer than two candidates have the indicator, set component `partial` and document `missing_inputs`.

Component score = weighted mean of available sub-scores (re-normalize sub-weights within the component when sub-indicators are missing).

**Total score:**

```text
total_score = round( sum( component_score[c] * weight[c] ), 0 )
```

Round to **integer 0–100** at export only. Keep full precision internally until export.

## Absolute Components

### `mandate_and_model_risk`

| Input | Source | Scoring rule (V1) |
| --- | --- | --- |
| `portfolio_valid` | `candidates[*].mandate.portfolio_valid` | `false` -> cap component at 20 and warning `mandate_portfolio_invalid` |
| `constraints_status` | snapshot / comparison mandate block | Map hard fails to low absolute sub-score before blending with relative rank |
| `warnings` | comparison candidate + run-level warnings | Each high-severity data-quality warning reduces absolute sub-score by fixed step (max -30 total) |

Blend: **60% absolute mapping, 40% relative rank** among scored candidates (V1).

### `liquidity_implementation`

| Input | Source | Scoring rule (V1) |
| --- | --- | --- |
| `pro_liquidity_status` | `run_metadata.json` / `run_result.json` when present | pass -> 100, warn -> 50, fail -> 0 |
| `liquidity_constraints` | snapshot constraints when present | absolute mapping when available |

When no liquidity fields exist: `status: not_computed`, re-weight, warning `liquidity_inputs_missing`. Do not invent liquidity scores from vol proxies.

## Component Sub-Indicators

### `structural_diversification` (15%)

Requires comparison `diversification` block ([candidate_comparison_spec.md](candidate_comparison_spec.md)).

| Sub-id | Field | Direction |
| --- | --- | --- |
| `top1_rc_pct` | `diversification.top1_rc_pct` | lower is better |
| `top3_rc_sum_pct` | `diversification.top3_rc_sum_pct` | lower is better |
| `rc_hhi` | optional `diversification.rc_hhi` | lower is better |

### `weight_concentration` (10%)

Requires [comparison prerequisite: weight_concentration block](#comparison-prerequisite-weight_concentration-block).

| Sub-id | Field | Direction |
| --- | --- | --- |
| `top1_weight_pct` | `weight_concentration.top1_weight_pct` | lower is better |
| `top3_weight_sum_pct` | `weight_concentration.top3_weight_sum_pct` | lower is better |
| `weight_hhi` | optional `weight_concentration.weight_hhi` | lower is better |

### `drawdown_resilience` (15%)

| Sub-id | Field | Direction |
| --- | --- | --- |
| `max_drawdown` | `metrics.10y.max_drawdown` | lower is better (less negative ranks higher) |
| `recovery` | `drawdown.recovered`, `drawdown.time_to_recovery_months` | higher is better |

### `stress_behavior` (10%)

| Sub-id | Field | Direction |
| --- | --- | --- |
| `stress_overall` | encoded rank of `stress.overall` | higher is better |
| `worst_scenario_pnl` | min `portfolio_pnl_pct` across used scenarios | higher is better |
| `scenario_pass_rate` | share of scenarios with `pass: true` | higher is better |

Do **not** duplicate Robustness `mean_scenario_pnl` as a separate Health sub-indicator in V1.

### `risk_adjusted_return` (14%)

| Sub-id | Field | Direction |
| --- | --- | --- |
| `cagr` | `metrics.10y.cagr` | higher is better |
| `sharpe` | `metrics.10y.sharpe` | higher is better |
| `sortino` | `metrics.10y.sortino` | higher is better |

### `factor_balance` (9%)

| Sub-id | Field | Direction |
| --- | --- | --- |
| `beta_dispersion` | spread of absolute factor betas in `factor_regime.factor_regression_10y` | lower is better |
| `adj_r2_10y` | `adj_r_squared` or `adj_r2` | higher is better (explains balance vs unexplained risk) |

Rolling beta stability: **not in V1** for Health (owned by Robustness `factor_stability`).

### `macro_regime_fit` (6%)

| Sub-id | Field | Direction |
| --- | --- | --- |
| `regime_fit_score` | `factor_regime.macro_regime.portfolio_fit` or spec-defined fit field | higher is better |
| `regime_confidence` | macro regime confidence when present | higher is better |

When `macro_regime` is absent: `not_computed`, re-weight, warning `macro_regime_missing`. See [macro_regime_spec.md](macro_regime_spec.md).

### `liquidity_implementation` (5%)

See [Absolute Components](#absolute-components) — `liquidity_implementation`.

### `mandate_and_model_risk` (6%)

See [Absolute Components](#absolute-components) — `mandate_and_model_risk`.

### `resilience_reference` (10%)

| Sub-id | Field | Direction |
| --- | --- | --- |
| `robustness_total` | matching row in `robustness_scorecard.json` `candidates[*].total_score` | higher is better (already 0–100; use as sub-score directly, no re-ranking) |

When scorecard row is `not_scored`, exclude component and re-weight.

## Comparison Prerequisite: weight_concentration Block

Session 13 must extend [candidate_comparison_spec.md](candidate_comparison_spec.md) and `src/candidate_comparison.py` before `weight_concentration` can score.

Add optional block `weight_concentration` on each candidate:

```json
{
  "top1_weight_asset": "VOO",
  "top1_weight_pct": 0.22,
  "top3_weight_assets": ["VOO", "BND", "GLD"],
  "top3_weight_sum_pct": 0.58,
  "weight_hhi": null,
  "source": "snapshot_10y.final_weights_total"
}
```

**Source priority:** `snapshot_10y.json` -> `final_weights_total` (risk weights may use `final_weights_risk_portfolio` when cash excluded; document choice in implementation). Align with [metrics_specification.md](metrics_specification.md) weight definitions.

When `weight_concentration` is missing for a scored candidate:

- set `weight_concentration.status` to `not_computed`;
- re-weight remaining components proportionally and record warning `weight_concentration_inputs_missing`;
- do **not** use RC pct as a proxy for weight concentration in V1.

## Top-Level JSON Contract

```json
{
  "schema_version": "portfolio_health_score_v1",
  "diagnostic_only": true,
  "generated_at": "ISO-8601",
  "weights_profile": "default_weights_reviewable",
  "weights": { },
  "primary_window": "10y",
  "input_artifacts": {
    "candidate_comparison": "candidate_comparison.json",
    "robustness_scorecard": "robustness_scorecard.json"
  },
  "comparison_schema_version": "candidate_comparison_v1",
  "robustness_schema_version": "robustness_scorecard_v1",
  "display_priority": ["analysis_subject"],
  "candidates": [ ],
  "comparison_summary": { },
  "warnings": [ ]
}
```

### Candidate score object

```json
{
  "candidate_id": "current",
  "display_name": "Current Portfolio",
  "score_status": "scored",
  "total_score": 62,
  "health_rank": 4,
  "components": {
    "structural_diversification": {
      "score": 55,
      "weight": 0.15,
      "status": "complete",
      "sub_scores": { },
      "inputs_used": [ ],
      "missing_inputs": [ ]
    }
  },
  "top_drivers": [
    { "component_id": "risk_adjusted_return", "direction": "positive", "label": "Risk-adjusted return ranks above peers on Sharpe and Sortino." }
  ],
  "top_drags": [
    { "component_id": "weight_concentration", "direction": "negative", "label": "Weight concentration is high versus peers (top-1 weight 28%)." }
  ],
  "explanation_bullets": [ ],
  "warnings": [ ]
}
```

### `score_status`

| Value | Meaning |
| --- | --- |
| `scored` | At least core components computed; included in ranking |
| `partial` | `total_score` present but one or more components `partial` or `not_computed` |
| `not_scored` | `candidate_comparison.status` was `unavailable` or insufficient data |

### `comparison_summary`

| Field | Description |
| --- | --- |
| `scored_count` | Number of candidates with `score_status` in (`scored`, `partial`) |
| `highest_health_candidate_id` | `candidate_id` with max `total_score` (ties: alphabetical id) |
| `highest_health_display_name` | English display name |
| `highest_total_score` | integer 0–100 |
| `score_spread` | max total - min total among scored |
| `policy_total_score` | `total_score` for `policy` when scored, else null |
| `current_total_score` | `total_score` for `current` when scored, else null |
| `ranking_table` | ordered list of `{ candidate_id, display_name, total_score, health_rank }` |

Ranking: sort by `total_score` descending, then `candidate_id` ascending. `health_rank` starts at 1.

## Human-Readable Output

`portfolio_health_score.txt` (optional, English only):

```text
Portfolio Health Score (diagnostic only) — primary window 10y
Weights profile: default_weights_reviewable

Priority rows:
  Current Portfolio                     62
  Policy (Optimized)                    71

Rank  Candidate                          Score
  1   Risk Parity                         78
  2   Policy (Optimized)                  71
  3   Current Portfolio                   62
...

See portfolio_health_score.json for component drivers (top_drivers / top_drags).
```

## Explanation Templates

`explanation_bullets` and structured `top_drivers` / `top_drags` are generated from component scores (not free-form LLM text in V1).

Rules:

1. First bullet: total score and health rank in this comparison.
2. `top_drivers`: up to **two** components with highest positive weighted contribution vs peer median.
3. `top_drags`: up to **two** components with largest negative weighted contribution vs peer median.
4. Use comparative phrasing; name metrics in plain English (e.g. "stagflation scenario loss", "top-1 weight").
5. Forbidden: "you should switch", "recommended portfolio", imperative rebalance language.

Example (product concept):

> Score reduced mainly due to high equity risk concentration, weak stagflation resilience, and high downside beta.

Implementation maps this pattern to structured fields from `sub_scores` and component ranks.

## Pipeline Placement (Session 13)

1. After `candidate_comparison.json` is written.
2. Prefer after `robustness_scorecard.json` when both are exported from the same CLI path.
3. Read comparison JSON (and optional scorecard); do not re-run optimizer or stress engine.
4. Write `portfolio_health_score.json` to the same `output_dir_final`.
5. Optional: summary lines in report commentary only when [reporting_outputs_spec.md](reporting_outputs_spec.md) is updated.

## Tests (Session 13)

Focused tests should cover:

- schema version and required keys;
- relative ranking with three mock candidates;
- single-candidate warning;
- `unavailable` -> `not_scored`;
- mandate `portfolio_valid: false` cap;
- missing `diversification` / `weight_concentration` -> partial re-weight;
- missing `robustness_scorecard.json` -> `resilience_reference` not_computed;
- `display_priority` fields for `analysis_subject` in portfolio-first and policy/current in legacy summary;
- tie-breaking on `total_score`;
- no duplicate metric formulas (mock comparison fixtures).

## Detailed Ownership

| Area | Spec / module |
| --- | --- |
| Comparison inputs | [candidate_comparison_spec.md](candidate_comparison_spec.md) |
| Robustness cross-reference | [robustness_scorecard_spec.md](robustness_scorecard_spec.md) |
| Metrics | [metrics_specification.md](metrics_specification.md) |
| Stress scenarios | [stress_testing_spec.md](stress_testing_spec.md) |
| Macro regime | [macro_regime_spec.md](macro_regime_spec.md) |
| Output location | [OUTPUTS.md](../../OUTPUTS.md) |
| Implementation | [src/portfolio_health_score.py](../../src/portfolio_health_score.py) |
| Selection / recommendation | [selection_engine_spec.md](selection_engine_spec.md) |
