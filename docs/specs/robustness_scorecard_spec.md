# Robustness Scorecard Specification

This document owns the **Robustness Scorecard** contract: a transparent, diagnostic-only resilience score for each portfolio candidate in a comparison run.

It does not own metric formulas, stress scenario definitions, candidate construction, or selection logic. Those remain in [metrics_specification.md](metrics_specification.md), [stress_testing_spec.md](stress_testing_spec.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), and (future) [selection_engine_spec.md](selection_engine_spec.md).

## Scope

The Robustness Scorecard:

- reads **`candidate_comparison.json`** as its primary input (Session 09 builder);
- produces **`robustness_scorecard.json`** (and optional **`robustness_scorecard.txt`**) under `output_dir_final`;
- scores **every registry candidate** that is `available` or `degraded`; marks `unavailable` candidates as `not_scored`;
- uses **relative normalization within the current comparison run** for component sub-scores (who is better among compared candidates);
- applies **absolute mandate checks** only inside the **mandate_fit** component (pass/fail and constraint status), not as the primary scaling method for the total score;
- stays **diagnostic-only**: no buy/sell language, no automatic portfolio selection, no override of stress pass/fail or optimizer release.

Implementation: **`src/robustness_scorecard.py`** (Session 11). This document is the contract.

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Robustness Scorecard** (this spec) | Multi-candidate resilience score 0–100 from comparison inputs. |
| **`src/robustness.py`** | Dual-horizon **optimizer weight stability** (10Y vs 5Y); unrelated to this scorecard. The scorecard implementation module (Session 11) must use a distinct module name and must not reuse `robustness.py`. |
| **Portfolio Health Score** | Separate future product score ([portfolio_health_score_spec.md](portfolio_health_score_spec.md) TBD, Session 12). |
| **Selection Engine** | Future formal decision artifact (Session 14+). |

## Product Boundary

- The scorecard answers: *among the candidates in this run, which profile appears more resilient across downside, stress, diversification, return efficiency, factor stability, and mandate fit?*
- It does **not** answer: *which portfolio should the client buy?*
- Allowed narrative: descriptive ranking and explanation bullets (e.g. "Minimum CVaR has the highest robustness score in this comparison because …").
- Forbidden: imperative trade advice, "recommended portfolio", or implying Selection Engine outcomes before that module exists.

## V1 User Decisions (2026-05-17)

Recorded for Session 10:

1. **Normalization:** primary sub-scores are **relative** among `scored` candidates in the same `candidate_comparison.json` run; **mandate_fit** also uses absolute pass/fail inputs from artifacts.
2. **Diversification (20%):** use **RC_vol from comparison** (not temporary vol/beta proxies). Requires a comparison extension (see [Comparison prerequisite](#comparison-prerequisite-diversification-block)); Session 11 implements builder + scorecard together.
3. **Primary window:** **10y** for metrics and drawdown; stress scenarios follow [stress_testing_spec.md](stress_testing_spec.md) ids and fields available in comparison or linked stress artifacts.
4. **Component weights:** product-concept defaults as **`default_weights_reviewable`** (sum = 1.0); may be revised after validation.

## Canonical Artifacts

| Field | Value |
| --- | --- |
| File name | `robustness_scorecard.json` |
| Location | `{output_dir_final}/robustness_scorecard.json` |
| Companion (optional) | `{output_dir_final}/robustness_scorecard.txt` |
| Schema version | `robustness_scorecard_v1` |
| Input | `{output_dir_final}/candidate_comparison.json` |

## Component Model

Six components. Weights apply to the **component score** (each 0–100 after within-run normalization).

| Component id | Display name | Default weight | Role |
| --- | --- | --- | --- |
| `downside_protection` | Downside protection | 0.25 | Drawdown depth, volatility, downside-oriented return metrics, recovery |
| `stress_resilience` | Stress resilience | 0.20 | Synthetic and historical stress PnL, suite overall, scenario pass flags |
| `diversification_rc` | Diversification / risk contribution | 0.20 | RC concentration (asset top1/top3); lower concentration scores higher |
| `return_efficiency` | Return efficiency | 0.15 | CAGR, Sharpe, Sortino, return per unit of risk |
| `factor_stability` | Factor stability | 0.10 | Factor regression fit and beta stability proxies |
| `mandate_fit` | Mandate fit | 0.10 | Portfolio valid, client fit, constraint status |

Weights profile id: **`default_weights_reviewable`**. Document any change in [DECISIONS.md](../../DECISIONS.md).

```json
{
  "downside_protection": 0.25,
  "stress_resilience": 0.20,
  "diversification_rc": 0.20,
  "return_efficiency": 0.15,
  "factor_stability": 0.10,
  "mandate_fit": 0.10
}
```

## Windows and Stress Scenario Set

### Metrics and drawdown

- **Primary window:** `10y` (from `candidate_comparison.primary_window`, default `10y`).
- Sub-indicators read `candidates[*].metrics.10y` and `candidates[*].drawdown` unless noted.

### Stress resilience

Use scenario rows from `candidates[*].stress.scenarios` when present. Scenario ids must match [stress_testing_spec.md](stress_testing_spec.md):

**Synthetic (mandatory suite):**

| scenario_id | Product label |
| --- | --- |
| `equity_shock` | Equity shock |
| `credit_shock` | Credit shock |
| `rates_shock` | Rates shock |
| `inflation_stagflation` | Inflation / stagflation |
| `liquidity_shock` | Liquidity shock |
| `recession_severe` | Recession severe |

**Historical episodes (when present in stress inputs):**

| scenario_id | Product label |
| --- | --- |
| `dotcom` | Dot-com |
| `2008` | 2008 GFC |
| `2020` | 2020 COVID |
| `2022` | 2022 rates |

Also use `stress.overall`, `stress.fail_reason_code`, and `stress.failed_scenario` when present.

**V1 comparison note:** `candidate_comparison` may truncate `stress.scenarios` to a subset. Session 11 implementation should prefer the **full** scenario list from `stress_report.json` via `source_files` when historical episodes are missing from the comparison row. The scorecard must record `stress_inputs_source` (`comparison` | `stress_report_fallback` | `partial`).

## Relative Normalization (Within-Run)

For each sub-indicator and each component:

1. Collect raw values across all candidates with `score_status: scored` (see below).
2. Determine direction: **higher is better** (e.g. Sharpe, CAGR) or **lower is better** (e.g. `max_drawdown`, `top1_rc_pct`, worse stress PnL).
3. Map to a 0–100 sub-score using **percentile rank** among scored candidates:
   - For "higher is better": `sub_score = 100 * rank_pct(value)` where best value gets 100.
   - For "lower is better": invert so the best (lowest) value gets 100.
4. **Ties:** equal raw values receive equal sub-scores.
5. **Single scored candidate:** all relative sub-scores default to **50** (neutral) with warning `single_candidate_comparison`.
6. **Missing sub-indicator** for a candidate: exclude from rank for that indicator; if fewer than two candidates have the indicator, set component status `partial` and document `missing_inputs`.

Component score = weighted mean of available sub-scores (re-normalize sub-weights to sum to 1 within the component when some sub-indicators are missing).

**Total score:**

```text
total_score = round( sum( component_score[c] * weight[c] ), 0 )
```

Round to **integer 0–100** at export only. Keep full precision internally until export.

## Mandate Fit (Absolute + Relative)

`mandate_fit` is the only component that **must** incorporate absolute artifact status:

| Input | Source | Scoring rule (V1) |
| --- | --- | --- |
| `portfolio_valid` | `candidates[*].mandate.portfolio_valid` | `false` -> cap component at 25 and add warning `mandate_portfolio_invalid` |
| `client_fit` | `mandate.client_fit` when present | Map pass/warn/fail to 100/50/0 before blending with relative rank |
| `constraints_status` | snapshot-derived in comparison when extended | `PASS` contributes positively; hard fails reduce sub-score |

After absolute adjustments, blend with relative rank among scored candidates (50% absolute mapping, 50% relative rank in V1 unless revised in Session 11).

## Component Sub-Indicators

### `downside_protection` (25%)

| Sub-id | Field | Direction | Notes |
| --- | --- | --- | --- |
| `max_drawdown` | `metrics.10y.max_drawdown` | lower is better | Less negative (closer to 0) ranks higher |
| `vol_annual` | `metrics.10y.vol_annual` | lower is better | |
| `sortino` | `metrics.10y.sortino` | higher is better | |
| `recovery` | `drawdown.recovered`, `drawdown.time_to_recovery_months` | higher is better | Recovered=true scores above false; shorter recovery ranks higher when recovered |

ES/CVaR: **not in V1** unless added to comparison metrics in a future release.

### `stress_resilience` (20%)

| Sub-id | Field | Direction |
| --- | --- | --- |
| `stress_overall` | encoded rank of `stress.overall` | higher is better | Order: `DIAG_PASS` > `DIAG_PASS_WITH_WARNING` > `DIAG_ATTENTION` > fail codes |
| `mean_scenario_pnl` | mean of `portfolio_pnl_pct` across used scenarios | higher is better |
| `worst_scenario_pnl` | min `portfolio_pnl_pct` | higher is better |
| `scenario_pass_rate` | share of scenarios with `pass: true` | higher is better |

Weight sub-indicators equally within the component unless Session 11 documents otherwise.

### `diversification_rc` (20%)

Requires [comparison prerequisite](#comparison-prerequisite-diversification-block).

| Sub-id | Field | Direction |
| --- | --- | --- |
| `top1_rc_pct` | `diversification.top1_rc_pct` | lower is better |
| `top3_rc_sum_pct` | `diversification.top3_rc_sum_pct` | lower is better |
| `rc_hhi` | optional `diversification.rc_hhi` | lower is better |

### `return_efficiency` (15%)

| Sub-id | Field | Direction |
| --- | --- | --- |
| `cagr` | `metrics.10y.cagr` | higher is better |
| `sharpe` | `metrics.10y.sharpe` | higher is better |
| `sortino` | `metrics.10y.sortino` | higher is better |
| `return_per_vol` | `cagr / vol_annual` when vol > 0 | higher is better |

### `factor_stability` (10%)

| Sub-id | Field | Direction |
| --- | --- | --- |
| `adj_r2_10y` | `factor_regime.factor_regression_10y.adj_r_squared` or `adj_r2` | higher is better |
| `beta_dispersion` | spread of absolute betas in 10y regression | lower is better |
| `rolling_beta_stability` | optional `factor_regime.rolling_beta_summary` | lower dispersion ranks higher |

Kalman beta: **not in V1** (no canonical artifact). Do not invent.

### `mandate_fit` (10%)

See [Mandate Fit (Absolute + Relative)](#mandate-fit-absolute--relative).

## Comparison Prerequisite: Diversification Block

Session 11 must extend [candidate_comparison_spec.md](candidate_comparison_spec.md) and `src/candidate_comparison.py` before the diversification component can score.

Add optional block `diversification` on each candidate:

```json
{
  "top1_rc_asset": "SCHP",
  "top1_rc_pct": 0.39,
  "top3_rc_assets": ["SCHP", "BND", "GLD"],
  "top3_rc_sum_pct": 0.766,
  "rc_hhi": null,
  "source_window": "10y"
}
```

**Source priority:** `snapshot_10y.json` -> `RC_asset` array (sum `rc_pct` for top3; top1 from first row); align with [metrics_specification.md](metrics_specification.md) RC_vol definitions.

When `diversification` is missing for a scored candidate:

- set `diversification_rc.status` to `not_computed`;
- re-weight remaining components proportionally for `total_score` and record `warnings` entry `diversification_inputs_missing`;
- do **not** use vol/beta proxies in V1.

## Top-Level JSON Contract

```json
{
  "schema_version": "robustness_scorecard_v1",
  "diagnostic_only": true,
  "generated_at": "ISO-8601",
  "weights_profile": "default_weights_reviewable",
  "weights": { },
  "primary_window": "10y",
  "input_artifact": "candidate_comparison.json",
  "comparison_schema_version": "candidate_comparison_v1",
  "candidates": [ ],
  "comparison_summary": { },
  "warnings": [ ]
}
```

### Candidate score object

```json
{
  "candidate_id": "minimum_cvar_constrained",
  "display_name": "Minimum CVaR (Constrained)",
  "score_status": "scored",
  "total_score": 81,
  "robustness_rank": 1,
  "components": {
    "downside_protection": {
      "score": 78,
      "weight": 0.25,
      "status": "complete",
      "sub_scores": { },
      "inputs_used": [ ],
      "missing_inputs": [ ]
    }
  },
  "explanation_bullets": [
    "Highest robustness score in this comparison (81/100).",
    "Downside protection ranks above peers on max drawdown and Sortino.",
    "Stress resilience benefits from a smaller loss in rates_shock and 2022 episode PnL."
  ],
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
| `highest_robustness_candidate_id` | `candidate_id` with max `total_score` (ties: alphabetical id) |
| `highest_robustness_display_name` | English display name |
| `highest_total_score` | integer 0–100 |
| `score_spread` | max total - min total among scored |
| `ranking_table` | ordered list of `{ candidate_id, display_name, total_score, robustness_rank }` |

Ranking: sort by `total_score` descending, then `candidate_id` ascending. `robustness_rank` starts at 1.

## Human-Readable Output

`robustness_scorecard.txt` (optional, English only):

```text
Robustness Scorecard (diagnostic only) — primary window 10y
Weights profile: default_weights_reviewable

Rank  Candidate                          Score
  1   Minimum CVaR (Constrained)          81
  2   Risk Parity                         78
  3   Current Portfolio                   62
...

Highest: Minimum CVaR (Constrained) — see robustness_scorecard.json for component detail.
```

## Explanation Templates

`explanation_bullets` are generated from component ranks (not free-form LLM text in V1). Rules:

1. First bullet: rank and total score.
2. Up to two bullets: name the **top two contributing components** (weighted contribution to total).
3. Up to one bullet: name the **weakest component** among scored peers.
4. Use comparative phrasing: "ranks above peers", "highest in this comparison", not "you should select".

Example (product concept):

> Minimum CVaR has the highest robustness score because it reduces tail loss and improves downside protection, even though expected return is lower.

Implementation maps this pattern to structured bullets from `sub_scores` and component ranks.

## Pipeline Placement (Session 11)

1. After `candidate_comparison.json` is written (`run_compare_variants.py` or dedicated CLI).
2. Read comparison JSON only; do not re-run optimizer or stress engine.
3. Write `robustness_scorecard.json` to the same `output_dir_final`.
4. Optional: append summary lines to report commentary only when reporting spec is updated.

## Tests (Session 11)

Focused tests should cover:

- schema version and required keys;
- relative ranking with three mock candidates;
- single-candidate warning;
- `unavailable` -> `not_scored`;
- mandate `portfolio_valid: false` cap;
- missing diversification block -> partial re-weight;
- tie-breaking on `total_score`;
- no duplicate metric formulas (mock comparison fixtures).

## Detailed Ownership

| Area | Spec / module |
| --- | --- |
| Comparison inputs | [candidate_comparison_spec.md](candidate_comparison_spec.md) |
| Metrics | [metrics_specification.md](metrics_specification.md) |
| Stress scenarios | [stress_testing_spec.md](stress_testing_spec.md) |
| Output location | [OUTPUTS.md](../../OUTPUTS.md) |
| Implementation | [src/robustness_scorecard.py](../../src/robustness_scorecard.py) (not `robustness.py`) |
| Optimizer weight stability (separate) | `src/robustness.py` |
| Selection / recommendation | [selection_engine_spec.md](selection_engine_spec.md) (TBD) |
