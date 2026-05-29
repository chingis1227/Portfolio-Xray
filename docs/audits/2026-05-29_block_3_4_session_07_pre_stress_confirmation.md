# Block 3.4 — Session 07 Pre-Stress Confirmation Bridge

Date: 2026-05-29

Related: [institutional upgrade plan](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md)

## Objective

Session 07 only: `pre_stress_confirmation_summary` with graceful Block 2.4 / 2.6 degradation; refresh scorecard after Portfolio X-Ray bridges in `run_report.py`.

## Delivered

- `src/current_portfolio_stress_scorecard_block.py`
  - `pre_stress_confirmation_summary` with `hidden_exposure`, `weakness_map`, `aggregate_confirmation`
  - `not_applicable` when 2.4/2.6 not attached; copies `hidden_exposure_confirmation` / `weakness_map_confirmation` from Block 3.3 when bridges ran
  - Optional attach kwargs: `portfolio_xray`, `block_2_4_hidden_exposure`, `block_2_6_portfolio_weakness_map`
  - `source_blocks_used` adds `portfolio_xray` when either bridge block is attached
  - `block_status` unchanged by missing 2.4/2.6 bridges
- `run_report.py` — re-attach scorecard with `portfolio_xray=xray_summary` before `export_stress_report`
- `tests/test_current_portfolio_stress_scorecard_v1_contract.py` — three new tests

## Must not change (honored)

- No downstream signals / consumer migration (Sessions 08–10)
- No recompute of offset math in Block 3.4

## Verification

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py -q
```

Result (2026-05-29): **34 passed**.

## Next

Session 08 — `problem_classification_signals` + PC v1-primary migration.
