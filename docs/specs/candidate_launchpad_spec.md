# Candidate Launchpad Specification

This document owns the V1 Candidate Launchpad data artifact for the diagnosis-first Portfolio MRI migration.

**Current contract (V3):** [block_4_diagnosis_v3_spec.md](block_4_diagnosis_v3_spec.md) ?5 - diagnosis-linked card fields (`source_diagnosis_id`, `hypothesis_to_test`, `success_criteria`, trade-offs, skip rules, disclaimer).

Implementation: `src/block_4/launchpad_cards.py` (V3 canonical); `src/candidate_launchpad.py` (legacy unit tests).

Canonical artifact: `candidate_launchpad.json`.

Status: **legacy V1** — canonical contract is [block_4_diagnosis_v3_spec.md](block_4_diagnosis_v3_spec.md) §5. Production writer: `src/block_4/launchpad_cards.py`. The current product validator is v3; the old V1 artifact remains unit-test-only.

## Scope

Candidate Launchpad cards let a user choose which improvement hypothesis to test next.

It reads:

- `problem_classification.json`

It writes:

- `candidate_launchpad.json`

It does not:

- contain portfolio weights;
- run candidate builders;
- run optimizers;
- change candidate factory behavior;
- rank existing candidates;
- compare candidates;
- make Selection Engine or Decision Verdict decisions;
- rename any existing schema or JSON field.

## Artifact Contract

Top-level shape:

```json
{
  "schema_version": "candidate_launchpad_v1",
  "diagnostic_only": true,
  "generated_at": "ISO-8601 UTC timestamp",
  "analysis_end": "YYYY-MM-DD",
  "source_artifacts": {
    "problem_classification": "problem_classification.json"
  },
  "cards": [],
  "summary": {
    "n_cards": 3,
    "primary_card_id": "launchpad_01_reduce_volatility",
    "has_portfolio_generating_options": true,
    "has_keep_current_option": false
  },
  "warnings": []
}
```

Each `cards[]` row contains:

| Field | Meaning |
| --- | --- |
| `card_id` | Stable generated card id for this artifact. |
| `goal` | User-facing hypothesis such as `Reduce volatility` or `Improve diversification`. |
| `description` | Plain-English description of what the user would test. |
| `source_problem_id` | Problem Classification problem that produced the card. |
| `source_problem_label` | Human-readable problem label. |
| `rationale` | Severity, confidence, and evidence copied from the source problem. |
| `suggested_methods` | Candidate method ids that a later Portfolio Alternatives Builder may use. |
| `generates_portfolio` | Always `false` in V1. |
| `requires_user_action` | Whether the card expects the user to choose a test rather than simply monitor/review. |

## Card Boundary

Cards are not portfolios. They may suggest method ids such as `minimum_variance`, `risk_parity`, or `equal_weight`, but they do not create weights or artifacts. The Portfolio Alternatives Builder owns later candidate creation.

## Goal Mapping

V1 maps goals to backend method ids only as suggestions:

- `Reduce volatility` -> `minimum_variance`, `risk_parity`, `equal_weight`
- `Reduce drawdown` -> `minimum_variance`, `minimum_cvar_constrained`, `risk_parity`
- `Improve diversification` -> `equal_weight`, `equal_weight_by_asset_class`, `maximum_diversification`
- `Reduce concentration` -> `equal_weight`, `equal_weight_by_asset_class`, `risk_budget_by_asset`
- `Improve crisis resilience` -> `minimum_cvar_constrained`, `robust_mv_constrained`, `robust_scenario`
- `Compare against simple benchmark` -> `equal_weight`, `risk_parity`
- `Keep current portfolio and monitor` -> no builder method
- `Review data quality` -> no builder method

## Workflow Integration

`run_report.py` writes `candidate_launchpad.json` after `problem_classification.json` is built. This keeps the diagnosis-first handoff explicit:

```text
Portfolio X-Ray / Stress
-> Problem Classification
-> Candidate Launchpad
```

No CLI behavior changes in Session 05.

## Verification

Focused tests:

```text
python -m pytest tests/test_candidate_launchpad.py tests/test_block_4_decision_entry_contract.py
```

Product contract (Session 14 / v2 freeze): `candidate_launchpad_v3_product_contract_violations` / `check_candidate_launchpad_v3` and `block_4_v3_diagnosis_handoff_violations` in `scripts/core_mvp_validation_contract.py`; live E2E via `validate_live_core_artifacts`.

Recommended adjacent checks:

```text
python -m pytest tests/test_candidate_launchpad.py tests/test_problem_classification.py tests/test_block_4_decision_entry_contract.py tests/test_live_core_e2e_validation.py -q
python run_portfolio_review.py
python scripts/verify_live_core_e2e.py --profile diagnosis_only
```
