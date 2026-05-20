# Hedge Gap Analysis Specification

Status: diagnostic-only contract.

`hedge_gap_analysis` identifies whether hedge-labeled holdings fail to offset portfolio loss in
mapped synthetic stress scenarios (per risk type) and in the global worst synthetic scenario.

## Inputs

- `scenario_results[*]` from `stress_report.json` (synthetic rows only for v2 mapping)
- optional hedge-labeled asset list from taxonomy (`risk_role` in ETF/stock universe metadata)

## Hedge label taxonomy

Holdings are hedge-labeled when ETF/stock universe metadata includes any of:

- `crisis_hedge`
- `defensive`
- `inflation_hedge`
- `tail_hedge`

`run_report.py` passes matching tickers into `run_stress` as `hedge_assets`. The output block
mirrors this list in `hedge_label_risk_roles`.

## Scenario mapping (v2)

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

## Method v1 (aggregate, retained)

1. Select worst synthetic scenario globally by minimum `portfolio_pnl_pct`.
2. For hedge-labeled assets, inspect `pnl_by_asset_pct` in that worst scenario.
3. If any hedge-labeled asset has non-positive contribution while portfolio loss is negative, flag gap.

Aggregate `status_reason` for a successful global evaluation with no gap uses `no_gap_evidence_global`
to distinguish from per-type `no_gap_evidence`.

## Method v2 (`by_risk_type[]`)

For each mapped `risk_type` (stable order in `HEDGE_GAP_RISK_TYPE_ORDER`):

1. Resolve `mapped_scenario_ids` from `HEDGE_GAP_SCENARIOS_BY_RISK`.
2. Pick the evaluation scenario row (minimum `portfolio_pnl_pct` among mapped ids present).
3. Apply the same hedge gap evidence rule as v1 on that row only.

Per-type rows do not change mandate pass/fail. They surface whether hedges failed in the scenario
relevant to that risk bucket, which may differ from the global worst scenario.

## Output block

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

### `by_risk_type[]` row

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

### Status and status_reason taxonomy (aggregate)

| `status` | `status_reason` | Meaning |
| --- | --- | --- |
| `not_applicable` | `no_hedge_labels` | No holdings carry hedge `risk_role` labels. |
| `insufficient_data` | `no_synthetic_scenarios` | Hedge labels exist but no synthetic scenario row is available. |
| `insufficient_data` | `portfolio_pnl_unavailable` | Global worst synthetic scenario exists but portfolio PnL is missing. |
| `gap_detected` | `gap_evidence` | Portfolio loss in global worst scenario with hedge non-positive contribution. |
| `no_gap_detected` | `no_gap_evidence_global` | Global evaluation found no hedge gap evidence. |

Do not treat `not_applicable` as `insufficient_data`.

## Notes

- v1 aggregate and v2 per-type blocks are scenario-based evidence, not live hedge effectiveness.
- This block is diagnostic and does not alter stress pass/fail or mandate checks.
