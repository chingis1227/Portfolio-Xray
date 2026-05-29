# Block 3.4 — Session 04 Loss + Risk Contribution Summaries

Date: 2026-05-29

Related: [institutional upgrade plan](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md)

## Objective

Session 04 only: add v1.1 `loss_contribution_summary` and `risk_contribution_summary` alongside MVP aliases; concentration share and RC/loss overlap flags per frozen spec.

## Delivered

- `src/current_portfolio_stress_scorecard_block.py`
  - `loss_contribution_summary` — mirrors `top_loss_contributors`; adds `loss_concentration_top3_share` on synthetic/historical branches when `loss_contribution.pnl_by_asset_pct` supports gross-loss math (Block 3.2 row lookup)
  - `risk_contribution_summary` — mirrors `top_risk_contributors`; adds `rc_overlap_with_loss_contributors` when both RC and synthetic loss top-3 tickers are available
  - Empty builder includes both v1.1 summary keys
- `tests/test_current_portfolio_stress_scorecard_v1_contract.py`
  - Five new tests (alias consistency, concentration math, RC overlap true/omitted-when-unavailable)

## Must not change (honored)

- No `hedge_gap_summary` / `stress_diagnosis` / downstream hooks (Sessions 05–10)
- No consumer migration (Sessions 08–10)
- MVP keys `top_loss_contributors` / `top_risk_contributors` unchanged and kept consistent with v1.1 aliases

## Verification

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py -q
```

Result (2026-05-29): **20 passed**.

## Next

Session 05 — `hedge_gap_summary` + `main_hedge_gap_scenario_id` from Block 3.3 only.
