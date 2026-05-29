# Block 3.4 — Session 09 Candidate Comparison Targets + CC Migration

Date: 2026-05-29

Related: [institutional upgrade plan](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md), [candidate_comparison_spec.md](../specs/candidate_comparison_spec.md)

## Objective

Session 09 only: `candidate_comparison_targets` on Block 3.4; Candidate Comparison v1-primary stress scorecard slice + top-level `stress_scorecard_comparison`.

## Delivered

- `src/current_portfolio_stress_scorecard_block.py`
  - `candidate_comparison_targets`: `worst_synthetic_scenario_id`, `main_hedge_gap_scenario_id`, `compare_offset_coverage`
- `src/candidate_comparison.py`
  - Per-candidate `stress.current_portfolio_stress_scorecard_v1` compact slice (v1-primary)
  - `stress.stress_scorecard_source`; legacy `stress.scorecard` only when v1 missing
  - Top-level `stress_scorecard_comparison` (`stress_scorecard_comparison_v1`) with pairwise worst-loss and optional offset deltas
- `tests/test_stress_scorecard_candidate_comparison.py` (3 tests)
- Contract + downstream tests extended

## Must not change (honored)

- No AI Commentary grounding (Session 10)
- No snapshot mirror / live-output gates (Session 11)

## Verification

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py tests/test_stress_scorecard_candidate_comparison.py tests/test_stress_downstream_integration.py tests/test_hedge_gap_candidate_comparison.py -q
```

Result (2026-05-29): **47 passed**.

## Next

Session 10 — `ai_commentary_context` / AI Commentary v1-primary grounding.
