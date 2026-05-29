# Block 3.4 — Session 01 Contract v1.1 Freeze

Date: 2026-05-29

Related: [institutional upgrade plan](../exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md), [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md), [Session 00 baseline](2026-05-29_block_3_4_session_00_baseline_audit.md)

## Objective

Freeze the Phase 2 product contract for `current_portfolio_stress_scorecard_v1` (ruleset
`current_portfolio_stress_scorecard_rules_v1_1`) without `src/` changes.

## Delivered

- New canonical spec: `docs/specs/current_portfolio_stress_scorecard_spec.md`
  - Ten product questions, read-only adapter boundary, mandate summarize-only rule
  - Frozen worst-scenario rules (envelope ownership Block 3.2)
  - `stress_diagnosis.diagnosis_confidence` enum (`high` \| `medium` \| `low` \| `unavailable`)
  - `next_decision_uses[]` token list (replaces singular `next_decision_use`)
  - Product language: `relatively_resilient_scenarios`, `less_damaging_scenarios`; forbidden keys and phrases
  - Optional 2.4/2.6 `pre_stress_confirmation_summary` graceful degradation (`not_applicable` bridges)
  - Downstream hook shapes for Sessions 08–10
  - MVP vs v1.1 implementation status matrix
- `docs/specs/stress_lab_layer_spec.md` §3.4 updated with spec link and v1.1 row index
- `docs/specs/README.md` spec index entry added

## Must not change (honored)

- No `src/` or test changes in Session 01

## Verification

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py -q
```

Result (2026-05-29): **4 passed** (unchanged baseline).

## Next

Session 02 — implement `block_status`, `ruleset_version`, `legacy_fallback_used`, and contract tests.
