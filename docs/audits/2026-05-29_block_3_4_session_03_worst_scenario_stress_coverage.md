# Block 3.4 — Session 03 Worst Scenario Hardening + stress_coverage

Date: 2026-05-29

Related: [institutional upgrade plan](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md)

## Objective

Session 03 only: harden worst-scenario adapter logic (envelope copy, metric discipline) and implement `stress_coverage` per v1.1 spec.

## Delivered

- `src/current_portfolio_stress_scorecard_block.py`
  - `stress_coverage` object (`n_*`, `fraction_*`) from Block 3.2 row lists / scenario library fallback
  - Worst blocks: `selection_metric` (`portfolio_pnl_pct` / `max_dd`), `selection_source` (`stress_results_v1.envelope`)
  - Non-numeric envelope loss/drawdown → `unavailable` with explicit `reason_en`
  - `_worst_selector_consistency_limitations` — drift detection only; no recompute in 3.4
  - `empty_current_portfolio_stress_scorecard_v1` includes empty `stress_coverage`
- `tests/test_current_portfolio_stress_scorecard_v1_contract.py`
  - Five new tests (coverage, metric metadata, historical min-dd vs min-pnl, non-numeric guard, envelope drift)

## Must not change (honored)

- No `loss_contribution_summary` / `risk_contribution_summary` (Session 04)
- No `hedge_gap_summary` / `stress_diagnosis` / downstream hooks (Sessions 05–10)
- No consumer migration (Sessions 08–10)

## Verification

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py -q
```

Result (2026-05-29): **15 passed**.

## Next

Session 04 — loss/risk contribution summaries + concentration flags.
