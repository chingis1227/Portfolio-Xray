# Decision Verdict Specification

This document owns the V1 product-facing Decision Verdict mapping for the diagnosis-first Portfolio MRI migration.

Implementation: `src/decision_verdict.py`.

Canonical artifact: `decision_verdict.json`.

Status: implemented as an additive mapping in code migration Session 08 and expanded in Blocks 5-9 vertical loop Session 06 with a direct Block 7/8 evidence builder. It does not replace the current Selection Engine contract.

## Scope

Decision Verdict translates either existing Selection Engine / No-Trade evidence or the direct vertical product-loop evidence into product-facing action language.

It reads:

- either `selection_decision.json` or `candidate_generation.json`;
- `current_vs_candidate.json`;
- optional `analysis_subject/client_fit_check.json`;
- optional `analysis_subject/problem_classification.json`;
- optional `action_plan.json`.

It writes:

- `decision_verdict.json`.

It does not:

- rename `selection_decision.json`;
- rename `selection_decision_v1`;
- rename `decision_status`;
- change Selection Engine formulas;
- change No-Trade thresholds;
- execute trades;
- modify candidate comparison;
- optimize weights.
- claim that a candidate is the "best portfolio";
- hide trade-offs that appear in `current_vs_candidate.json`.

## Artifact Contract

Top-level shape:

```json
{
  "schema_version": "decision_verdict_v1",
  "diagnostic_only": false,
  "generated_at": "ISO-8601 UTC timestamp",
  "verdict_id": "no_material_rebalance_recommended",
  "verdict_label": "No material rebalance recommended",
  "verdict_family": "core_compare",
  "selection_decision_status": "no_material_rebalance",
  "baseline_candidate_id": "analysis_subject",
  "selected_candidate_id": "risk_parity",
  "reviewed_candidate_id": "risk_parity",
  "verdict_reason_id": "no_material_rebalance",
  "decision_action": "keep_current",
  "no_trade": {},
  "recommended_action": "...",
  "confidence": "medium",
  "confidence_limitations": [],
  "rationale_summary": "...",
  "evidence_summary": {},
  "source_artifacts": {},
  "guardrails": {}
}
```

## Status Mapping

| Selection `decision_status` | Product `verdict_id` |
| --- | --- |
| `selected_candidate` | `rebalance_to_selected_candidate` |
| `no_material_rebalance` | `no_material_rebalance_recommended` |
| `inconclusive` | `test_another_candidate_or_review_evidence` |
| `data_review_required` | `evidence_insufficient` |
| `mandate_risk_reduction` | `risk_reduction_required` |

Unknown technical statuses map to `evidence_insufficient`.

## Direct Block 7/8 Builder

`build_decision_verdict_from_block7_8()` is the Block 9 builder for the vertical product loop. It consumes one `candidate_generation_v1` attempt plus the Block 8 `current_vs_candidate_v1` comparison for the same selected candidate. It may also consume `client_fit_check.json` and `problem_classification.json` as bounded decision context. It keeps the existing `decision_verdict_v1` status vocabulary for compatibility, but adds product-specific evidence fields:

- `reviewed_candidate_id` records the generated candidate under review even when the final verdict is no-trade or evidence insufficient.
- `verdict_reason_id` explains the direct Block 9 reason, such as `candidate_generation_failed`, `candidate_generation_infeasible`, `insufficient_data_quality`, `insufficient_optimizer_or_method_quality`, `no_material_rebalance`, `keep_current_portfolio`, `rebalance_when_material`, `test_another_candidate`, or `risk_improved_but_turnover_too_high`.
- `decision_action` records the non-binding action family (`keep_current`, `test_another_candidate`, `rebalance_review`, `revise_objectives`, or `evidence_insufficient`).
- `evidence_summary` mirrors the Block 7 generation status, method availability, materiality review, success-criteria result, risk reduced/added, improvements, deteriorations, and practicality/turnover evidence used by the verdict.
- `evidence_summary.client_fit_decision_context` carries display-ready Client Fit context. It is not raw `client_fit_check.json` and must not be used to treat Client Fit as suitability approval.

Direct outcome mapping:

| Direct evidence condition | `selection_decision_status` | `verdict_id` |
| --- | --- | --- |
| Candidate generation missing, failed, infeasible, or not comparable | `data_review_required` | `evidence_insufficient` |
| Current-vs-candidate evidence missing, degraded, or materially incomplete | `data_review_required` | `evidence_insufficient` |
| Method availability or optimizer/construction disclosure is degraded enough to block trust | `data_review_required` | `evidence_insufficient` |
| Materiality is insufficient and the hypothesis is not worth action | `no_material_rebalance` | `no_material_rebalance_recommended` |
| Candidate misses stated success criteria | `no_material_rebalance` | `no_material_rebalance_recommended` |
| Risk improves but turnover or estimated cost is too high | `no_material_rebalance` | `no_material_rebalance_recommended` |
| Evidence is mixed or the criterion cannot be evaluated clearly enough | `inconclusive` | `test_another_candidate_or_review_evidence` |
| Candidate shows material improvement, success criteria are not failed, and practicality does not block review | `selected_candidate` | `rebalance_to_selected_candidate` |
| `client_fit_status = fit` but `diagnostic_quality_status` is `issue` or `material_issue` and the candidate evidence would otherwise produce no-trade | `inconclusive` | `test_another_candidate_or_review_evidence` |
| `goal_risk_conflict` is present in Client Fit or Problem Classification evidence | `revise_objectives` | `revise_objectives` |

The direct builder uses simple practicality thresholds as Block 9 guardrails: turnover half-sum at or above 50% or estimated transaction cost at or above 0.5% blocks a rebalance verdict and produces a no-trade reason when risk improved. These thresholds are presentation-layer decision guardrails only; they do not change optimizer formulas or candidate weights.

No-trade is valid. Evidence insufficient is valid. A rebalance verdict means "material enough for rebalance review", not automatic trade execution.

Client Fit boundary:

- a Client Fit pass alone cannot produce keep-current/no-trade when the objective diagnosis still has an unresolved issue;
- a goal-risk conflict routes to objective-review / revise-objectives language before candidate interpretation;
- Client Fit context is displayed separately from diagnostic quality and decision action.

### `verdict_family` (UI filtering)

| `verdict_family` | When | Core MVP note |
| --- | --- | --- |
| `core_compare` | Default for all compare outcomes except mandate reduction | Standard Decision Verdict for portfolio-first one-candidate demos |
| `policy_mandate` | `selection_decision_status` is `mandate_risk_reduction` | **Legacy policy-path** semantics from mandate breach on comparison rows (`portfolio_valid === false`). Filter or label separately in Core MVP UI; not emitted on diagnosis-only runs. |

`mandate_risk_reduction` originates in the Selection Engine when legacy policy/current comparison rows show mandate validation failure. Decision Verdict maps it to `risk_reduction_required` without changing Selection formulas. See [selection_engine_spec.md](selection_engine_spec.md) § Mandate Risk Reduction.

## Boundary With Selection Engine

Selection Engine remains the technical source of truth for favored candidate and No-Trade status. Decision Verdict is a presentation/mapping layer over that evidence. Any change to Selection formulas, thresholds, or schema must happen in the Selection Engine spec and implementation, not here.

## Workflow Integration

`write_candidate_comparison_outputs()` writes `decision_verdict.json` after `action_plan.json` is available. This lets the product-facing verdict include action-plan context while preserving current downstream artifacts.

## Verification

Product contract (Session 10): `check_decision_verdict_v1`, `check_block_5_compare_handoff` in `scripts/core_mvp_validation_contract.py`; live gate `block_5_*` in `validate_live_core_artifacts` for profile `product_one_candidate`. Evidence: [Session 10 audit](../audits/2026-05-29_block_5_session_10_current_vs_candidate_decision_verdict.md).

Focused tests:

```text
python -m pytest tests/test_block_5_decision_compare_contract.py tests/test_decision_verdict.py tests/test_decision_verdict_contract.py tests/test_decision_verdict_no_trade.py tests/test_decision_verdict_rebalance_when_material.py tests/test_decision_verdict_evidence_insufficient.py tests/test_decision_verdict_failed_candidate.py -q
```

Recommended adjacent checks:

```text
python -m pytest tests/test_block_5_decision_compare_contract.py tests/test_live_core_e2e_validation.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py -q
python run_portfolio_review.py --candidates equal_weight
python scripts/verify_live_core_e2e.py --profile product_one_candidate
```
