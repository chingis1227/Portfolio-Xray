# Hedge Gap Analysis Specification

Status: diagnostic-only contract.

`hedge_gap_analysis` identifies whether hedge-labeled holdings fail to offset portfolio loss in
the worst synthetic scenario.

## Inputs

- `scenario_results[*].pnl_by_asset_pct` from `stress_report.json`
- optional hedge-labeled asset list from taxonomy (`risk_role` in ETF/stock universe metadata)

## Method v1

1. Select worst synthetic scenario by minimum `portfolio_pnl_pct`.
2. For hedge-labeled assets, inspect `pnl_by_asset_pct` in that worst scenario.
3. If any hedge-labeled asset has negative contribution while portfolio loss is negative, flag gap.

## Output block

`stress_report.json.hedge_gap_analysis`:

- `method`: `stress_scenario_hedge_evidence_v1`
- `hedge_assets_considered`: list of tickers
- `n_hedge_assets_considered`: count of hedge-labeled tickers evaluated
- `worst_scenario_id`: scenario id used for evaluation (minimum `portfolio_pnl_pct`)
- `worst_scenario_portfolio_pnl_pct`: portfolio PnL in that scenario (evidence)
- `hedge_assets_negative_in_worst_scenario`: list of `{ticker, pnl_pct}` where hedge-labeled assets
  have non-positive contribution while `worst_scenario_portfolio_pnl_pct` is negative
- `gap_detected`: boolean mirror of gap evidence (true only when `status` is `gap_detected`)
- `status`: `gap_detected` | `no_gap_detected` | `insufficient_data`

`insufficient_data` when there are no hedge-labeled assets, no synthetic scenarios, or portfolio PnL
in the worst scenario is unavailable.

## Notes

- v1 is scenario-based evidence, not live hedge effectiveness estimation.
- This block is diagnostic and does not alter stress pass/fail or mandate checks.
