# Regret Analysis Specification

This document owns the **Regret Analysis** diagnostic layer: scenario-level opportunity-loss evidence that quantifies how much a **reference profile** underperforms the best available candidate in the same comparison run, without re-running optimizers or recomputing canonical metrics.

It does not own stress scenario definitions, metric formulas, selection rules, Pareto dominance math, scorecard components, action trade construction, or mandate release policy. Those remain in [stress_testing_spec.md](stress_testing_spec.md), [metrics_specification.md](metrics_specification.md), [candidate_comparison_spec.md](candidate_comparison_spec.md), [selection_engine_spec.md](selection_engine_spec.md), [pareto_dominance_spec.md](pareto_dominance_spec.md), [assumption_sensitivity_spec.md](assumption_sensitivity_spec.md), and [tradeoff_and_model_risk_spec.md](tradeoff_and_model_risk_spec.md).

Implementation: `src/regret_analysis.py` (`regret_analysis_v1`); wired in `write_candidate_comparison_outputs` after Pareto. This document is the contract.

## Scope

The Regret Analysis layer:

- reads **`candidate_comparison.json`** as the primary input and may read **`selection_decision.json`**, **`pareto_dominance.json`**, and policy **`stress_report.json`** (macro block only) for cross-reference;
- emits **`regret_analysis.json`** and **`regret_analysis.txt`** under `output_dir_final`;
- computes **regret** per named stress scenario and optional summary slices for one or more **reference profiles**;
- identifies, per scenario, the **best available candidate** in the evaluable opportunity set;
- remains **diagnostic-only** and **non-binding** (does not change `selection_decision.json`, action plans, mandate pass/fail, or weights);
- does **not** replace Pareto dominance (static multi-metric weakness) or Assumption Sensitivity (ranking stability under weight perturbations).

## Naming Boundary

| Name | Meaning |
| --- | --- |
| **Regret Analysis** (this spec) | Scenario opportunity loss vs best available candidate in-run. |
| **Pareto / Dominance** | Whether a candidate is metric-dominated on the primary window; complementary. |
| **Assumption Sensitivity** | Whether favored selection survives weight/window perturbations; complementary. |
| **Trade-off Explanation** | Baseline→target deltas for one favored pair; not scenario regret. |
| **Selection Engine** | Produces `favored_candidate_id`; unchanged by this layer in V1. |
| **Macro regime diagnostics** | Binding labels in [macro_regime_spec.md](macro_regime_spec.md); regret uses regime slices only when exported data exist. |

## Product Boundary

- Answers: *If we commit to profile R, how much return (in stress PnL terms) do we give up versus the best other candidate in each named scenario... Where is regret largest...*
- Does **not** answer: *automatically switch selection*, *predict future scenarios*, or *guarantee ex-post optimality*.
- Forbidden in exported text: imperative buy/sell, performance guarantees, presenting regret as automatic investment truth.

**Tone (V1):** institutional decision-support English, same as comparison and selection artifacts.

## V1 User Decisions (2026-05-17, Post-audit Session 18)

Recorded defaults from product concept section 16, comparison-ranking guidance, and audit PSA-012 when the user continues without overrides:

1. **Opportunity set:** all comparison candidates with `status` in `available`, `degraded` and scenario PnL present; `unavailable` rows excluded from the best-candidate scan.
2. **Primary regret slice:** **named stress scenarios** from `stress.scenarios[]` (`scenario_id`, `portfolio_pnl_pct`) already exported in comparison (no new stress engine run).
3. **Reference profiles (always attempt):** `favored` from `selection_decision.favored_candidate_id`; `current` when role `user_current` is evaluable; `benchmark` when a candidate with role `benchmark` is evaluable.
4. **Regret formula (stress):** for scenario `s`, `regret_R(s) = best_pnl(s) - pnl_R(s)` where `best_pnl(s) = max portfolio_pnl_pct` over the opportunity set; values are **as exported** (three decimals at export per metrics spec).
5. **Headline summaries:** `mean_regret`, `worst_regret` (max over scenarios), and `worst_scenario_id` per reference profile; optional `regret_vs_pareto_set` deferred to V2.
6. **Macro regime slice (optional V1):** when policy `stress_report.json` exposes `macro_regime_diagnostics` with a primary label **and** comparison projects per-candidate regime summary PnL (see [Macro regime slice](#macro-regime-slice-optional-v1)), emit `regime_slices[]`; otherwise `regime_regret_status: not_available`.
7. **Metric slice (Tier B, informational):** optional primary-window `cagr_regret` vs best CAGR among the opportunity set; does **not** replace stress regret headlines.
8. **Binding boundary:** artifact is evidence for humans, decision package, and journal; Selection output is unchanged.

## Canonical Artifacts

| File | Schema | Required |
| --- | --- | --- |
| `regret_analysis.json` | `regret_analysis_v1` | Yes when comparison exists with at least one evaluable candidate and one scenario with PnL |
| `regret_analysis.txt` | plain English | Yes when JSON is written |

Location: `{output_dir_final}/` (default `Main portfolio/`).

## Pipeline Placement

```text
run_compare_variants.py
  -> write_candidate_comparison_outputs
       -> comparison, robustness, health
       -> selection_decision
       -> tradeoff_explanation + model_risk_diagnostics
       -> assumption_sensitivity
       -> pareto_dominance
       -> [Session 19] regret_analysis  (this spec)
       -> current_vs_policy_status
       -> action_plan
       -> monitoring, journal, decision_package_reporting
```

**Order (V1):** immediately **after** `pareto_dominance` and **before** `current_vs_policy_status.json`.

Rationale: needs full comparison stress scenarios and favored id; must not influence No-Trade or action gating.

## Inputs

### Required

| Input | Minimum fields |
| --- | --- |
| `candidate_comparison.json` | `primary_window`, `candidates[]` with `candidate_id`, `status`, `role`, `stress.scenarios[]` |

### Optional

| Input | Use |
| --- | --- |
| `selection_decision.json` | `favored_candidate_id`, `decision_status` for reference profile resolution |
| `pareto_dominance.json` | `non_dominated` list for narrative cross-reference only in V1 (no formula change) |
| `stress_report.json` (policy folder) | `macro_regime_diagnostics` for optional regime slice |

### Skip behavior

| Condition | Behavior |
| --- | --- |
| Missing `candidate_comparison.json` | Do not write artifacts; run warning `regret_skipped_missing_comparison`. |
| No evaluable candidates | `regret_status: insufficient_candidates`; minimal JSON with warning. |
| No scenario with PnL on any evaluable row | `regret_status: no_scenario_pnl`; minimal JSON; Tier B CAGR slice may still run when metrics exist. |
| Missing `selection_decision.json` | Still compute regret for `current` and `benchmark` references; `favored` reference `not_available`. |
| Favored id null | Skip `favored` reference block with reason `no_favored_profile`. |

## Opportunity Set (V1)

Candidates included in `best_pnl` and ranking:

| Criterion | Rule |
| --- | --- |
| `status` | `available` or `degraded` |
| Scenario PnL | `portfolio_pnl_pct` finite for the scenario being evaluated |
| Registry | all non-current roles allowed unless `unavailable` |

**Current** may be both a reference profile **and** a member of the opportunity set.

**Policy** is not special-cased in regret math: if `policy` is evaluable, it competes like any other candidate for `best_pnl`.

## Stress Scenario Regret (V1)

### Scenario union

Build the set of `scenario_id` values appearing on any evaluable candidate's `stress.scenarios[]`. For each `scenario_id`:

1. Collect `portfolio_pnl_pct` per evaluable candidate (skip missing).
2. If fewer than one value: mark scenario `insufficient_data`.
3. `best_pnl` = algebraic maximum (same convention as Pareto stress worst-loss: larger / less negative is better).
4. `best_candidate_id` = candidate with `best_pnl`; ties broken by stable sort on `candidate_id` ascending.

### Per reference profile R

For each reference in [Reference profiles](#reference-profiles-v1):

| Field | Description |
| --- | --- |
| `pnl` | R's `portfolio_pnl_pct` for the scenario, or null |
| `regret` | `best_pnl - pnl` when both finite; null when R missing PnL |
| `best_candidate_id` | Winner in opportunity set |
| `best_pnl` | Winner PnL |
| `rank_by_pnl` | 1-based rank of R among evaluable candidates with PnL (optional) |

**Non-negative regret:** when R has PnL, `regret >= 0` by construction. Implementation must not clamp negative values silently; negative regret indicates a data bug and must surface in `warnings`.

### Aggregates per reference

| Field | Description |
| --- | --- |
| `mean_regret` | Mean of finite `regret` over evaluated scenarios |
| `worst_regret` | Max `regret` over scenarios |
| `worst_scenario_id` | Scenario id at `worst_regret` |
| `scenarios_evaluated` | Count of scenarios with finite regret for R |
| `scenarios_with_zero_regret` | Count where R is tied for best |

## Reference Profiles (V1)

| `reference_id` | Resolution |
| --- | --- |
| `favored` | `selection_decision.favored_candidate_id` |
| `current` | First candidate with `role == user_current` and evaluable status |
| `benchmark` | First candidate with `role == benchmark` and evaluable status |

Each reference block includes `candidate_id`, `display_name`, `reference_status` (`complete` \| `not_available` \| `partial_scenarios`), and scenario rows.

## Macro Regime Slice (optional V1)

When **all** of the following exist:

- policy `stress_report.json` → `macro_regime_diagnostics.primary_regime` (or equivalent primary label field per stress spec);
- comparison row for policy (or favored) projects `factor_regime.macro_regime` with per-regime portfolio PnL or return summaries;

emit `regime_slices[]` with the same regret formula on regime-conditional PnL fields **as exported** (no new regime classifier).

Otherwise:

```json
"regime_regret_status": "not_available",
"regime_regret_note": "Macro regime regret requires projected regime PnL on comparison rows."
```

Session 19 may extend comparison projection; regret must still run when regime data are absent.

## Tier B — Primary-Window CAGR Regret (informational)

When `metrics.{primary_window}.cagr` exists for at least two evaluable candidates:

| Field | Description |
| --- | --- |
| `cagr_best_candidate_id` | Candidate with highest CAGR |
| `cagr_best` | Best CAGR value |
| `cagr_regret` | `cagr_best - cagr_R` per reference profile |

This slice is **not** a stress scenario and must be labeled informational in TXT and decision package. It does not drive `worst_regret` headline.

## Top-Level JSON (`regret_analysis_v1`)

```json
{
  "schema_version": "regret_analysis_v1",
  "diagnostic_only": true,
  "non_executing": true,
  "generated_at": "ISO-8601",
  "analysis_end": "YYYY-MM-DD",
  "primary_window": "10y",
  "regret_status": "complete",
  "opportunity_set_candidate_ids": ["policy", "equal_weight", "risk_parity"],
  "scenario_count": 8,
  "reference_profiles": [],
  "scenario_regret": [],
  "regime_regret_status": "not_available",
  "regime_slices": [],
  "metric_regret": {},
  "summary_plain_en": "Under the favored profile, worst stress regret versus the best available candidate is 2.1% in the GFC replay scenario.",
  "warnings": [],
  "input_artifacts": {
    "candidate_comparison.json": "candidate_comparison.json",
    "selection_decision.json": "selection_decision.json"
  }
}
```

### `reference_profiles[]` row

| Field | Type | Description |
| --- | --- | --- |
| `reference_id` | string | `favored` \| `current` \| `benchmark` |
| `candidate_id` | string \| null | Resolved registry id |
| `display_name` | string \| null | English label |
| `reference_status` | string | `complete` \| `not_available` \| `partial_scenarios` |
| `mean_regret` | number \| null | Stress-scenario mean |
| `worst_regret` | number \| null | Stress-scenario max |
| `worst_scenario_id` | string \| null | Scenario at worst regret |
| `scenarios_evaluated` | integer | |
| `scenarios_with_zero_regret` | integer | |

### `scenario_regret[]` row (compact cross-reference)

| Field | Type | Description |
| --- | --- | --- |
| `scenario_id` | string | Stress scenario id |
| `best_candidate_id` | string | |
| `best_pnl` | number | |
| `by_reference` | object | Map `reference_id` → `{pnl, regret, rank_by_pnl}` |

### Required top-level fields

| Field | Required | Description |
| --- | --- | --- |
| `schema_version` | yes | `regret_analysis_v1` |
| `diagnostic_only` | yes | always `true` |
| `regret_status` | yes | `complete` \| `insufficient_candidates` \| `no_scenario_pnl` \| `partial` |
| `reference_profiles` | yes | May be empty only when `regret_status` is not `complete` |
| `summary_plain_en` | yes | 1–3 sentences, client-safe |
| `warnings` | yes | May be empty |

## TXT Summary (V1)

Plain English, fixed sections:

1. **Scope** — opportunity set size, scenario count, reference profiles evaluated.
2. **Favored profile regret** — worst scenario, mean regret, best alternative name (when favored reference exists).
3. **Current vs best** — same for `current` when evaluable (informational for No-Trade context).
4. **Benchmark check** — when benchmark reference exists.
5. **Interpretation** — one short paragraph; stress regret is historical scenario PnL, not a forecast; no buy/sell.

## Downstream Consumers

| Consumer | Use |
| --- | --- |
| [decision_package_reporting_spec.md](decision_package_reporting_spec.md) | Optional subsection after Pareto (Session 19). |
| [decision_journal_spec.md](decision_journal_spec.md) | Optional `regret_summary` citing `worst_regret` for favored reference. |
| PDF / `report.txt` | Short regret line when summary exists. |

Journal and reporting must **not** override `selection_decision.json` when favored regret is high.

## Tests (Session 19 implementation)

Minimum focused tests:

1. Three candidates, one scenario: middle profile has positive regret; best has zero regret.
2. Tied best PnL: both have `regret == 0`; stable `best_candidate_id` tie-break.
3. Missing favored selection: `favored` reference `not_available`; `current` still computed.
4. No scenarios on any row → `no_scenario_pnl`; optional CAGR Tier B when metrics exist.
5. Negative regret from bad data → warning, not silent clamp.
6. Pipeline integration: file emitted after `pareto_dominance` in `write_candidate_comparison_outputs`.

## Related Specifications

- [candidate_comparison_spec.md](candidate_comparison_spec.md) — stress scenario blocks.
- [selection_engine_spec.md](selection_engine_spec.md) — favored profile (unchanged in V1).
- [pareto_dominance_spec.md](pareto_dominance_spec.md) — complementary dominance evidence.
- [assumption_sensitivity_spec.md](assumption_sensitivity_spec.md) — complementary stability evidence.
- [stress_testing_spec.md](stress_testing_spec.md) — scenario definitions and PnL meaning.
- [macro_regime_spec.md](macro_regime_spec.md) — regime labels for optional slice.
- [decision_package_reporting_spec.md](decision_package_reporting_spec.md) — reporting integration (Session 19).
