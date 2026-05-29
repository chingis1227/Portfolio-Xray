# Decision Verdict Specification

This document owns the V1 product-facing Decision Verdict mapping for the diagnosis-first Portfolio MRI migration.

Implementation: `src/decision_verdict.py`.

Canonical artifact: `decision_verdict.json`.

Status: implemented as an additive mapping in code migration Session 08. It does not replace the current Selection Engine contract.

## Scope

Decision Verdict translates existing Selection Engine / No-Trade evidence into product-facing action language.

It reads:

- `selection_decision.json`;
- optional `current_vs_candidate.json`;
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
  "no_trade": {},
  "recommended_action": "...",
  "confidence": "medium",
  "confidence_limitations": [],
  "rationale_summary": "...",
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
python -m pytest tests/test_block_5_decision_compare_contract.py tests/test_decision_verdict.py -q
```

Recommended adjacent checks:

```text
python -m pytest tests/test_block_5_decision_compare_contract.py tests/test_live_core_e2e_validation.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py -q
python run_portfolio_review.py --candidates equal_weight
python scripts/verify_live_core_e2e.py --profile product_one_candidate
```
