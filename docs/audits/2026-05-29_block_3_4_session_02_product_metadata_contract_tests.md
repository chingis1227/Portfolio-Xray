# Block 3.4 — Session 02 Product Metadata + Contract Tests

Date: 2026-05-29

Related: [institutional upgrade plan](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md)

## Objective

Implement v1.1 product metadata on `current_portfolio_stress_scorecard_v1` and extend contract tests (Session 02 scope only).

## Delivered

- `src/current_portfolio_stress_scorecard_block.py`
  - `RULESET_VERSION = current_portfolio_stress_scorecard_rules_v1_1`
  - Top-level: `block_status`, `ruleset_version`, `scorecard_scope`, `source_blocks_used`, `legacy_fallback_used`, `limitations`
  - `_derive_block_status`, `_derive_source_blocks_used`, `_derive_legacy_fallback_used`, `_derive_limitations`
  - Worst-selector availability tightened (null `scenario_id` / `episode` → `unavailable`)
- `tests/test_current_portfolio_stress_scorecard_v1_contract.py`
  - Six new tests for metadata contract; `overall_status` added to forbidden-key scan

## Must not change (honored)

- No worst-scenario recomputation beyond availability guard (Session 03)
- No `stress_coverage`, `stress_diagnosis`, downstream hooks, or pre-stress bridges (Sessions 03–10)
- No downstream consumer migration (Sessions 08–10)

## Verification

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py -q
```

Result (2026-05-29): **10 passed**.

## Next

Session 03 — worst scenario logic hardening and `stress_coverage`.
