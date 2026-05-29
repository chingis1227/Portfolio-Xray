# Block 3.4 — Session 06 Stress Diagnosis + Resilience Lists

Date: 2026-05-29

Related: [institutional upgrade plan](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md)

## Objective

Session 06 only: `stress_diagnosis` object, `relatively_resilient_scenarios` / `less_damaging_scenarios`, `next_decision_uses[]`, forbidden English phrase scan.

## Delivered

- `src/current_portfolio_stress_scorecard_block.py`
  - `stress_diagnosis`: `headline`, `diagnosis_summary_en`, `diagnosis_confidence`, `confidence_reason`, `confidence_reason_en`, `key_findings`
  - `relatively_resilient_scenarios` / `less_damaging_scenarios` from Block 3.2 synthetic rows
  - `next_decision_uses[]` — all four tokens when `block_status` ∈ `{ok, partial}`; `[]` when unavailable
  - Top-level `diagnosis_summary_en` mirrors `stress_diagnosis.diagnosis_summary_en`
  - `collect_forbidden_english_phrases()` for contract tests
- `tests/test_current_portfolio_stress_scorecard_v1_contract.py`
  - Six new tests (diagnosis, next uses, resilience lists, phrase scan)

## Must not change (honored)

- No `pre_stress_confirmation_summary` (Session 07)
- No downstream signals / consumer migration (Sessions 08–10)

## Verification

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py -q
```

Result (2026-05-29): **31 passed**.

## Next

Session 07 — `pre_stress_confirmation_summary`; graceful 2.4/2.6 degradation.
