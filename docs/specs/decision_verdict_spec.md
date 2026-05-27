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

Focused tests:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict.py
```

Recommended adjacent checks:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict.py tests\test_selection_engine.py tests\test_action_engine.py
.\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
```
