# Block 3.4 — Session 05 Hedge Gap Summary + Factor Attribution

Date: 2026-05-29

Related: [institutional upgrade plan](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md)

## Objective

Session 05 only: add v1.1 `hedge_gap_summary` (read-only from Block 3.3) and harden factor attribution row fallback.

## Delivered

- `src/current_portfolio_stress_scorecard_block.py`
  - `hedge_gap_summary` — compact copy from `hedge_gap_analysis_v1`: `main_hedge_gap_scenario_id`, `main_hedge_gap_risk_type`, `offset_coverage_ratio`, `protection_profile`, `hedge_gap_block_status`, `hedge_gap_ruleset_version`
  - `main_hedge_gap_scenario_id` equals `hedge_gap_analysis_v1.summary.main_hedge_gap.linked_scenario_id` (via summary alias when present)
  - `_build_factor_stress_attribution_summary` falls back to worst synthetic row `factor_attribution` when envelope drivers empty
  - Empty builder includes `hedge_gap_summary`
- `tests/test_current_portfolio_stress_scorecard_v1_contract.py`
  - Five new tests (3.3 linkage, unavailable paths, factor attribution parity + row fallback)

## Must not change (honored)

- No `stress_diagnosis` / `next_decision_uses[]` / downstream hooks (Sessions 06–10)
- No consumer migration (Sessions 08–10)
- MVP keys `main_hedge_gap`, top-level `hedge_gap_*` meta unchanged

## Verification

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py -q
```

Result (2026-05-29): **25 passed**.

## Next

Session 06 — `stress_diagnosis` object; `next_decision_uses[]`; forbidden phrase scan.
