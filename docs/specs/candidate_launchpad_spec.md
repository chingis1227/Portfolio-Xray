# Candidate Launchpad Specification

This document owns the Candidate Launchpad data artifact for the diagnosis-first Portfolio MRI migration.

**Current contract (V3):** [block_4_diagnosis_v3_spec.md](block_4_diagnosis_v3_spec.md) - diagnosis-linked card fields (`source_diagnosis_id`, `hypothesis_to_test`, `success_criteria`, trade-offs, skip rules, disclaimer).

Current V3 cards may be targeted hypothesis tests or reference benchmark tests.
Reference benchmark tests use Equal Weight and Risk Parity only to compare the
current allocation against simple alternatives; they are not rebalance
recommendations.

Implementation: `src/block_4/launchpad_cards.py` (V3 canonical); `src/candidate_launchpad.py` (legacy unit tests).

Canonical artifact: `candidate_launchpad.json`.

Status: **current V3 product contract plus legacy V1 compatibility notes**. The canonical product contract is [block_4_diagnosis_v3_spec.md](block_4_diagnosis_v3_spec.md). Production writer: `src/block_4/launchpad_cards.py`. The current product validator is v3; the old V1 artifact remains unit-test-only through `src/candidate_launchpad.py`.

## Scope

Candidate Launchpad cards expose the diagnosis-linked hypotheses, reference
benchmark comparisons, monitoring steps, or data-quality fixes that a user may
inspect next. They do not create candidates. A selected card can be handed to
Portfolio Alternatives Builder to pre-fill a candidate setup while preserving
the diagnosis and decision boundary.

It reads:

- `problem_classification.json`

It writes:

- `candidate_launchpad.json`

It does not:

- contain portfolio weights;
- run candidate builders;
- run optimizers;
- prefill Builder by itself without a user selecting a card;
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
| `card_type` | `targeted_hypothesis_test`, `reference_benchmark_test`, or monitor/data step. |
| `launch_status` | Whether the card is a targeted hypothesis, reference test, or monitor/data step. |
| `why_this_test` | Plain-English reason this test follows from the diagnosis. |
| `is_rebalance_recommendation` | Always `false`; actual rebalance decisions are made downstream. |
| `decision_boundary` | States that rebalance decisions are made only after Current vs Candidate Comparison and Decision Verdict. |
| `generates_portfolio` | Always `false` in V1. |
| `requires_user_action` | Whether the card expects the user to choose a test rather than simply monitor/review. |

## Card Boundary

Cards are not portfolios. They may suggest method ids such as `minimum_variance`, `risk_parity`, or `equal_weight`, but they do not create weights or artifacts. The Portfolio Alternatives Builder owns later candidate creation.

For reference benchmark cards, `suggested_methods[]` rows include
`method_role: reference_benchmark`. Equal Weight is used as a simple
concentration benchmark; Risk Parity is used as a risk-distribution benchmark.
If the primary diagnosis is actionable, the first card remains the targeted
hypothesis and reference benchmarks must not displace it.

## Builder Handoff Boundary

Launchpad v3 cards are the source for Builder prefill, not candidate generation.
When a user selects a card, Portfolio Alternatives Builder may copy
`source_diagnosis_id`, `card_id`, `goal`, `hypothesis_to_test`,
`suggested_methods`, `default_method`, `success_criteria`,
`tradeoff_to_watch`, `when_to_skip`, `card_type`, `launch_status`,
`is_rebalance_recommendation`, and `decision_boundary` into a Builder setup
object. The setup object must preserve the diagnostic boundary: it opens a
guided test or reference comparison and does not create weights until a separate
explicit user action asks for candidate generation.

Targeted cards can open a guided Builder setup. Reference benchmark cards can
open an Equal Weight / Risk Parity reference comparison. Monitor-only and
data-quality cards must not expose unreliable candidate generation; they should
open a monitor or resolve-data setup instead. In all cases, Launchpad-derived
Builder setup keeps `is_rebalance_recommendation: false`; Current vs Candidate
Comparison and Decision Verdict remain the downstream layers that decide whether
real action is justified.

`candidate_generation_allowed` on the Builder prefill means only that the
Builder may show a separate generate-candidate action. It is not an automatic
factory trigger, not a rebalance instruction, and not a Decision Verdict.

## Goal Mapping

V1 maps goals to guided Builder method ids only as suggestions. The full backend candidate factory menu remains advanced/legacy infrastructure and is not the Launchpad guided path.

- `Reduce volatility` -> `minimum_variance`, `risk_parity`, `equal_weight`
- `Reduce drawdown` -> `minimum_cvar`, `minimum_variance`, `risk_parity`
- `Improve diversification` -> `equal_weight`, `risk_parity`, `maximum_diversification`
- `Reduce concentration` -> `equal_weight`, `risk_parity`, `maximum_diversification`
- `Improve crisis resilience` -> `minimum_cvar`, `maximum_diversification`, `minimum_variance`
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

Product contract (current v3): `candidate_launchpad_v3_product_contract_violations` / `check_candidate_launchpad_v3` and `block_4_v3_diagnosis_handoff_violations` in `scripts/core_mvp_validation_contract.py`; live E2E via `validate_live_core_artifacts`.

Recommended adjacent checks:

```text
python -m pytest tests/test_candidate_launchpad.py tests/test_problem_classification.py tests/test_block_4_decision_entry_contract.py tests/test_live_core_e2e_validation.py -q
python run_portfolio_review.py
python scripts/verify_live_core_e2e.py --profile diagnosis_only
```
