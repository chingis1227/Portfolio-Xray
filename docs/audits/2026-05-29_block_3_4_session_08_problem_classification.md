# Block 3.4 — Session 08 Problem Classification Signals + PC Migration

Date: 2026-05-29

Related: [institutional upgrade plan](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md), [problem_classification_spec.md](../specs/problem_classification_spec.md)

## Objective

Session 08 only: emit `problem_classification_signals` on Block 3.4; migrate Problem Classification to v1-primary stress scorecard with explicit legacy fallback.

## Delivered

- `src/current_portfolio_stress_scorecard_block.py`
  - `problem_classification_signals`: `stress_severity`, `main_gap_risk_type`, `worst_synthetic_id`, `worst_historical_episode`, `diagnosis_confidence`
  - Empty/unavailable shape when `block_status = unavailable`
- `src/problem_classification.py`
  - Worst-scenario problems read `current_portfolio_stress_scorecard_v1` when `block_status` ∈ `{ok, partial}`
  - Legacy `stress_conclusions` / `stress_scorecard_v1` only when Block 3.4 missing or unavailable
  - Top-level `stress_scorecard_source` on `problem_classification.json`
  - Mandate rollup still uses legacy `stress_scorecard_v1.overall_status` (`legacy_mandate_rollup`)
- Spec updates: `problem_classification_spec.md`, `current_portfolio_stress_scorecard_spec.md` (status matrix)
- Tests: 5 new contract/PC tests

## Must not change (honored)

- No `candidate_comparison_targets` / CC migration (Session 09)
- No AI Commentary grounding (Session 10)
- No snapshot / live-output gates (Session 11)

## Verification

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py tests/test_problem_classification.py -q
```

Result (2026-05-29): **46 passed**.

## Next

Session 09 — `candidate_comparison_targets` + Candidate Comparison v1-primary migration.
