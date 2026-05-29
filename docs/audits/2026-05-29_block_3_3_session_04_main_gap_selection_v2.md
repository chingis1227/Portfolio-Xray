# Block 3.3 — Session 04 Main Gap Selection v2 Closure

Date: 2026-05-29

Related: [institutional upgrade plan](../exec_plans/2026-05-29_block_3_3_hedge_gap_institutional_upgrade_plan.md), [hedge_gap_analysis_spec.md](../specs/hedge_gap_analysis_spec.md)

## Delivered

- `RULESET_VERSION = hedge_gap_rules_v1_2`
- Weighted `main_gap_score` on summary and compact `main_hedge_gap`
- `selection_reason_code`, `selection_reason_en` on summary
- Portfolio `diagnosis_summary_en` embeds selection reason when present
- Legacy fallback: min `offset_coverage_ratio` when score cannot be computed

## Verification

```bash
python -m pytest tests/test_hedge_gap_analysis_v1_contract.py -q
```

Result: **63 passed**.

## Next

Session 05 — `hidden_exposure_confirmation[]` bridge (Block 2.4).
