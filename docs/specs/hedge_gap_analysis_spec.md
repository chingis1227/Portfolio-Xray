# Hedge Gap Analysis Specification

Status: diagnostic-only contract.

Stress Lab exposes two hedge-gap blocks on `stress_report.json`:

| Block | JSON key | Audience |
| --- | --- | --- |
| **Block 3.3 Core MVP** | `hedge_gap_analysis_v1` | Product-facing contribution-based offset diagnosis |
| **Legacy** | `hedge_gap_analysis` | Backward compatibility (`stress_scenario_hedge_evidence_v2`, taxonomy hedge labels) |

Core MVP operators and new integrations must read **`hedge_gap_analysis_v1`**. Do not extend the legacy block for Block 3.3 product behavior.

---

## Block 3.3 — `hedge_gap_analysis_v1` (Core MVP)

### Purpose

Answer, per key market risk type: did assets that helped offset losses from assets that hurt in the
mapped synthetic stress scenario, where is protection weak, and what is the main hedge gap?

- **No** pre-labeling holdings as hedge assets (no taxonomy `risk_role` gate).
- **No** second stress engine or PnL recomputation — read evidence from Block 3.1 / Block 3.2 only.
- **No** client mandate pass/fail, suitability gates, or `DIAG_*` on Block 3.3 product rows.
- **No** historical episode rows in v1 (`linked_episode: null`, `scenario_type: synthetic` only).

### Placement and wiring

- Artifact: `stress_report.json` (Stress Test Lab boundary — **not** `portfolio_xray.json`).
- Built **after** `attach_stress_results_v1` on the same report dict.
- `loss_gate_mode` copied from top-level report (`diagnostic` for Core MVP portfolio-first runs).

Module: `src/hedge_gap_analysis_block.py` (`BLOCK_3_3_VERSION = "hedge_gap_analysis_v1"`,
`RULESET_VERSION = "hedge_gap_rules_v1_2"` — bump from `hedge_gap_rules_v1_1` when main-gap
selection scoring changes).
MVP Sessions 02–08 (2026-05-27); institutional upgrade Sessions 02–12 (**Completed** 2026-05-29) — [acceptance audit](../audits/2026-05-29_block_3_3_institutional_upgrade_acceptance_audit.md).

### Risk type → scenario mapping (v1 — frozen)

Eight product protection areas map 1:1 to eight synthetic scenarios (seven fixed vectors plus
calibrated `recession_severe`).

| `risk_type` | `linked_scenario_id` |
| --- | --- |
| `equity_crash_protection` | `equity_shock` |
| `rates_up_shock_protection` | `rates_shock` |
| `stagflation_protection` | `inflation_stagflation` |
| `liquidity_shock_protection` | `liquidity_shock` |
| `usd_spike_protection` | `usd_shock` |
| `credit_shock_protection` | `credit_shock` |
| `commodity_inflation_shock_protection` | `commodity_shock` |
| `recession_severe_protection` | `recession_severe` |

Registry constant (implementation): `BLOCK_3_3_RISK_SCENARIO_MAP` in `src/hedge_gap_analysis_block.py`.
Do **not** reuse legacy weakness-bucket ids (`recession`, `inflation`, …) or
`HEDGE_GAP_SCENARIO_BY_RISK` as product `risk_type` strings.

Stable row order: keys of `BLOCK_3_3_RISK_SCENARIO_MAP` in definition order.

### Evidence inputs (read-only)

Preferred read path per linked scenario:

1. `stress_results_v1.synthetic_scenarios[]` row matching `linked_scenario_id` →
   `loss_contribution.pnl_by_asset_pct`
2. Fallback: `scenario_results[]` row → `pnl_by_asset_pct`

Also use for cross-check: `portfolio_loss_pct` from the same linked row (Block 3.2 or
`scenario_results[].portfolio_pnl_pct`).

Do **not** rely on Block 3.2 `assets_helped` on the global worst synthetic row — v1 needs **all**
positives and negatives from the full per-scenario map.

### Per-risk row (`by_risk_type[]`)

| Field | Rule | Unavailable when |
| --- | --- | --- |
| `risk_type` | Map key | — |
| `linked_scenario_id` | Map value | — |
| `linked_episode` | Always `null` in v1 | — |
| `scenario_type` | Always `"synthetic"` in v1 | — |
| `portfolio_loss_pct` | Linked scenario portfolio loss | Scenario row missing |
| `assets_hurt` | Tickers with `pnl_by_asset_pct < 0` (zeros excluded), sorted most negative first, ticker tie-break A→Z; `{ticker, pnl_pct}` | No `pnl_by_asset_pct` dict |
| `assets_helped` | Tickers with `pnl_by_asset_pct > 0` (zeros excluded), sorted largest positive first, ticker tie-break A→Z | Same |
| `gross_loss_from_assets_hurt` | `sum(abs(pnl_pct))` over hurt assets | No hurt assets |
| `positive_contribution_from_assets_helped` | `sum(pnl_pct)` over helped assets | No helped assets (ratio may still be 0) |
| `offset_coverage_ratio` | `positive_contribution / gross_loss` when `gross_loss > 0` and both terms finite; `0.0` when offset is zero; else `null` | `gross_loss == 0` or missing contrib |
| `loss_concentration` | `top3_share_of_gross_loss`: sum of abs top-3 hurt / `gross_loss` | `gross_loss` unavailable |
| `data_availability` | `available` \| `insufficient_data` \| `unavailable` | See reason codes below |
| `data_availability_reason` | Machine code when not `available` | — |
| `diagnosis_summary_en` | Template English from computed fields | Missing portfolio loss |
| `protection_type` | Product alias of `risk_type` (same string) | — |
| `scenario_id` | Product alias of `linked_scenario_id` | — |
| `top3_loss_assets` | First three `assets_hurt` entries | No hurt assets |
| `top3_helped_assets` | First three `assets_helped` entries | No helped assets |
| `protection_status` | See taxonomy below | `unavailable` when row not `available` |
| `confirmation_status` | `not_applicable` until bridges run; after Block 2.4 bridge: `confirmed` \| `partially_confirmed` \| `not_confirmed` \| `preliminary` | — |
| `confidence` | `high` \| `medium` \| `low` \| `unavailable` | From contribution completeness |
| `confidence_reason` | Machine-readable confidence driver | — |
| `limitations` | Per-row limitation strings (`[]` when none) | — |
| `client_diagnosis_en` | Shorter advisor-facing template | Same gates as `diagnosis_summary_en` |
| `next_decision_use` | Downstream hint (`candidate_hedge_gap_compare`, …) | — |

#### `protection_status` taxonomy (per row)

| Value | Rule |
| --- | --- |
| `strong_protection` | `offset_coverage_ratio >= 0.60` and portfolio loss &lt; 0 |
| `partial_protection` | `0.25 <= ratio < 0.60` and portfolio loss &lt; 0 |
| `weak_protection` | `0 < ratio < 0.25` and portfolio loss &lt; 0 |
| `no_protection` | `ratio == 0` and portfolio loss &lt; 0 |
| `not_needed_or_no_loss` | `portfolio_loss_pct >= 0` |
| `unavailable` | Row not `data_availability == available` |

**Formula:** `offset_coverage_ratio = positive_contribution_from_assets_helped / gross_loss_from_assets_hurt`
(example: hurt gross 12%, helped +2.5% → ratio ≈ 0.208 → ~21% in narrative).

#### `data_availability_reason` codes (per row)

| Code | Meaning |
| --- | --- |
| `scenario_row_missing` | Linked synthetic not in evidence arrays |
| `pnl_by_asset_unavailable` | Row present but no usable `pnl_by_asset_pct` |
| `no_assets_hurt` | Map present but no negative contributors (ratio N/A) |
| `zero_gross_loss` | Hurt list empty or gross loss is zero |

### Summary object (`summary`)

| Field | Derive rule |
| --- | --- |
| `main_hedge_gap` | Compact row for the selected main gap (includes `main_gap_score` when scored) |
| `weakest_protection_area` | `risk_type` of `main_hedge_gap` |
| `strongest_protection_area` | Maximum `offset_coverage_ratio` when ≥2 rows have ratio; else `null` |
| `main_gap_score` | Weighted severity score of the selected row (higher = worse gap); `null` on legacy fallback |
| `selection_reason_code` | `weighted_gap_score_v2_loss_scenarios` \| `weighted_gap_score_v2_no_loss_fallback` \| `fallback_min_offset_ratio` \| `no_ratio_rows` |
| `selection_reason_en` | English explanation of how `main_hedge_gap` was chosen |
| `diagnosis_summary_en` | Portfolio-level template (main gap + contrast vs stronger areas + selection reason) |
| `data_quality_warnings` | Missing contrib, scenario missing, all ratios unavailable, etc. |
| `average_offset_coverage_ratio` | Mean of numeric row ratios when present; else `null` |
| `protection_profile` | `mostly_weak_protection` \| `mostly_adequate_protection` \| `mixed_protection` \| `unavailable` |
| `client_summary_en` | Shorter portfolio-level advisor template | No main gap |
| `limitations` | Portfolio-level limitations (includes data-quality warnings) |
| `main_hedge_gap_scenario_id` | `main_hedge_gap.linked_scenario_id` | No main gap |
| `main_hedge_gap_offset_coverage_ratio` | From `main_hedge_gap` | No main gap |
| `main_hedge_gap_portfolio_loss_pct` | From `main_hedge_gap` | No main gap |
| `main_assets_hurt` / `main_assets_helped` | Full lists for main-gap risk row | No main gap |

#### Main hedge gap selection (ruleset v1.2)

Among rows with numeric `offset_coverage_ratio`, prefer rows with `portfolio_loss_pct < 0`.
If none are losing, use all ratio rows.

**Primary (v1.2):** maximize `main_gap_score` per candidate row:

`main_gap_score = offset_deficit × loss_severity × concentration_multiplier`

- `offset_deficit = 1 - min(max(offset_coverage_ratio, 0), 1)`
- `loss_severity = abs(portfolio_loss_pct)` when `portfolio_loss_pct < 0`
- `concentration_multiplier = 1 + 0.25 × min(top3_share_of_gross_loss, 1)` (0 when concentration unknown)

**Tie-break (higher wins):** larger `main_gap_score`, then larger `abs(portfolio_loss_pct)`, then lower `offset_coverage_ratio`, then `risk_type` A→Z.

**Fallback:** when no score can be computed, minimum `offset_coverage_ratio` with tie-break by more negative `portfolio_loss_pct` (`selection_reason_code = fallback_min_offset_ratio`).

### Top-level block shape

`stress_report.json.hedge_gap_analysis_v1`:

| Field | Description |
| --- | --- |
| `version` | `hedge_gap_analysis_v1` |
| `ruleset_version` | `hedge_gap_rules_v1_2` (bump when status/scoring logic changes) |
| `block_status` | `ok` \| `partial` \| `unavailable` (from row availability) |
| `loss_gate_mode` | Copy of report `loss_gate_mode` |
| `diagnosis_method` | `contribution_based_offset_coverage_v1` |
| `scenario_library` | `synthetic_ids` linkage copy from Block 3.2 / Scenario Library (for contract tests) |
| `scenario_coverage` | `{n_available, n_total, fraction_available}` |
| `by_risk_type` | Eight rows per mapping table (or explicit unavailable rows) |
| `summary` | See above |
| `n_risk_types` | Length of `by_risk_type` (expect 8 when map complete) |
| `hidden_exposure_confirmation` | Array of Block 2.4 alert ↔ stress offset confirmation rows (Session 05); empty until Portfolio X-Ray bridge runs |
| `weakness_map_confirmation` | Array of Block 2.6 canonical `risk_type` (scenario id) ↔ hedge-gap row confirmations (Session 06); empty until Portfolio X-Ray bridge runs |
| `bridge_meta` | `{block_2_4_hidden_exposure, block_2_6_portfolio_weakness_map, ruleset, n_alerts_linked, n_weakness_rows_linked}` when bridges applied |

#### `hidden_exposure_confirmation[]` row (Session 05)

| Field | Description |
| --- | --- |
| `alert_id` | Block 2.4 alert id (`hidden_equity_beta`, `weak_hedge_behavior`, …) |
| `alert_status` / `alert_score` | Copied from Block 2.4 alert |
| `confirmation_status` | Aggregate vs linked hedge-gap rows |
| `confirmation_reason_code` | Machine-readable bridge outcome |
| `confirmation_reason_en` | English explanation |
| `linked_risk_types` / `linked_scenario_ids` | Protection areas used for confirmation |
| `risk_type_confirmations` | Per-row `{risk_type, confirmation_status, offset_coverage_ratio, protection_status, …}` |

Bridge runs in `build_portfolio_xray_v2` after Block 2.4 is built (no `src.block_2_4` import in Block 3.3).
`attach_hedge_gap_analysis_v1(..., block_2_4_hidden_exposure=...)` may apply the same bridge when a 2.4 dict is already available.

#### `weakness_map_confirmation[]` row (Session 06)

| Field | Description |
| --- | --- |
| `risk_type` | Block 2.6 canonical scenario id (`equity_shock`, …) |
| `linked_protection_type` | Block 3.3 protection row id (`equity_crash_protection`, …) |
| `linked_scenario_id` | Same as `risk_type` (Stress Lab synthetic id) |
| `weakness_severity` / `weakness_score_0_100` | Copied from Block 2.6 risk row |
| `confirmation_status` | Aggregate stress offset confirmation vs pre-stress weakness |
| `confirmation_reason_code` / `confirmation_reason_en` | Machine and English bridge outcome |
| `protection_status` / `offset_coverage_ratio` / `portfolio_loss_pct` | Copied from linked hedge-gap row when available |

Block 2.6 bridge runs in `build_portfolio_xray_v2` after Block 2.6 is built (read-only; must not mutate Block 2.6).
`attach_hedge_gap_analysis_v1(..., block_2_6_portfolio_weakness_map=...)` may apply the same bridge when a 2.6 dict is already available.

**Forbidden on Block 3.3 product rows:** `pass`, `loss_ok`, `gap_detected`, `status` (legacy taxonomy),
`max_dd_limit`, mandate comparison fields.

### Narratives

- English template strings only (`diagnosis_summary_en`); **no** LLM-generated text in this block.
- Interpret offset coverage and concentration; do not imply buy/sell or mandate suitability.

---

## Legacy — `hedge_gap_analysis` (`stress_scenario_hedge_evidence_v2`)

`hedge_gap_analysis` identifies whether hedge-labeled holdings fail to offset portfolio loss in
mapped synthetic stress scenarios (per risk type) and in the global worst synthetic scenario.

### Inputs

- `scenario_results[*]` from `stress_report.json` (synthetic rows only for v2 mapping)
- optional hedge-labeled asset list from taxonomy (`risk_role` in ETF/stock universe metadata)

### Hedge label taxonomy

Holdings are hedge-labeled when ETF/stock universe metadata includes any of:

- `crisis_hedge`
- `defensive`
- `inflation_hedge`
- `tail_hedge`

`run_report.py` passes matching tickers into `run_stress` as `hedge_assets`. The output block
mirrors this list in `hedge_label_risk_roles`.

### Scenario mapping (v2)

Per-risk evaluation uses `HEDGE_GAP_SCENARIO_BY_RISK` in `src/stress.py`, aligned with
`portfolio_xray.WEAKNESS_SCENARIO_MAP`:

| `scenario_id` | `risk_type` |
| --- | --- |
| `recession_severe` | `recession` |
| `inflation_stagflation` | `inflation` |
| `rates_shock` | `rates` |
| `credit_shock` | `credit` |
| `liquidity_shock` | `liquidity` |
| `equity_shock` | `equity_crash` |
| `usd_shock` | `usd` |
| `commodity_shock` | `commodity_shock` |

For each `risk_type`, the evaluation scenario is the mapped row with minimum `portfolio_pnl_pct`
among rows present in `scenario_results`. If no mapped row is present, the per-type row is
`insufficient_data` with `status_reason` `scenario_not_available`.

### Method v1 (aggregate, retained)

1. Select worst synthetic scenario globally by minimum `portfolio_pnl_pct`.
2. For hedge-labeled assets, inspect `pnl_by_asset_pct` in that worst scenario.
3. If any hedge-labeled asset has non-positive contribution while portfolio loss is negative, flag gap.

Aggregate `status_reason` for a successful global evaluation with no gap uses `no_gap_evidence_global`
to distinguish from per-type `no_gap_evidence`.

### Method v2 (`by_risk_type[]`)

For each mapped `risk_type` (stable order in `HEDGE_GAP_RISK_TYPE_ORDER`):

1. Resolve `mapped_scenario_ids` from `HEDGE_GAP_SCENARIOS_BY_RISK`.
2. Pick the evaluation scenario row (minimum `portfolio_pnl_pct` among mapped ids present).
3. Apply the same hedge gap evidence rule as v1 on that row only.

Per-type rows do not change mandate pass/fail. They surface whether hedges failed in the scenario
relevant to that risk bucket, which may differ from the global worst scenario.

### Output block

`stress_report.json.hedge_gap_analysis`:

- `method`: `stress_scenario_hedge_evidence_v2`
- `scenario_mapping`: `HEDGE_GAP_SCENARIO_BY_RISK`
- `hedge_label_risk_roles`: canonical taxonomy roles used for hedge labeling
- `hedge_assets_considered`: list of tickers
- `n_hedge_assets_considered`: count of hedge-labeled tickers evaluated
- `worst_scenario_id`: global worst synthetic scenario id (minimum `portfolio_pnl_pct`)
- `worst_scenario_portfolio_pnl_pct`: portfolio PnL in that scenario (aggregate v1 evidence)
- `hedge_assets_negative_in_worst_scenario`: list of `{ticker, pnl_pct}` for aggregate evaluation
- `gap_detected`: boolean mirror of aggregate gap evidence (true only when aggregate `status` is `gap_detected`)
- `status`: aggregate status — `gap_detected` | `no_gap_detected` | `insufficient_data` | `not_applicable`
- `status_reason`: machine-readable aggregate reason code (see taxonomy below)
- `status_reason_en`: English explanation for commentary and PDF-facing text
- `by_risk_type`: array of per-risk-type rows (see below)
- `n_risk_types_evaluated`: length of `by_risk_type`
- `any_risk_type_gap_detected`: true if any `by_risk_type[*].gap_detected` is true

### `by_risk_type[]` row (legacy)

| Field | Description |
| --- | --- |
| `risk_type` | Weakness bucket id (e.g. `recession`, `inflation`) |
| `mapped_scenario_ids` | Scenario ids mapped to this risk type |
| `scenario_mapping` | `HEDGE_GAP_SCENARIO_BY_RISK` |
| `evaluation_scenario_id` | Scenario used for this row (worst mapped PnL), or null |
| `evaluation_scenario_portfolio_pnl_pct` | Portfolio PnL in evaluation scenario |
| `hedge_assets_negative` | Hedge tickers with non-positive `pnl_by_asset_pct` when portfolio losing |
| `gap_detected` | Per-type gap flag |
| `status` | `gap_detected` \| `no_gap_detected` \| `insufficient_data` |
| `status_reason` | `scenario_not_available`, `portfolio_pnl_unavailable`, `gap_evidence`, `no_gap_evidence` |
| `status_reason_en` | English explanation |

### Status and status_reason taxonomy (aggregate, legacy)

| `status` | `status_reason` | Meaning |
| --- | --- | --- |
| `not_applicable` | `no_hedge_labels` | No holdings carry hedge `risk_role` labels. |
| `insufficient_data` | `no_synthetic_scenarios` | Hedge labels exist but no synthetic scenario row is available. |
| `insufficient_data` | `portfolio_pnl_unavailable` | Global worst synthetic scenario exists but portfolio PnL is missing. |
| `gap_detected` | `gap_evidence` | Portfolio loss in global worst scenario with hedge non-positive contribution. |
| `no_gap_detected` | `no_gap_evidence_global` | Global evaluation found no hedge gap evidence. |

Do not treat `not_applicable` as `insufficient_data`.

`stress_conclusions.hedge_gap_status` copies aggregate legacy `hedge_gap_analysis.status` only.

## Notes

- Legacy v1/v2 aggregate and per-type blocks are scenario-based evidence using taxonomy labels, not
  live hedge effectiveness and not Block 3.3 offset coverage.
- Block 3.3 and legacy blocks are diagnostic and do not alter stress pass/fail or mandate checks.
