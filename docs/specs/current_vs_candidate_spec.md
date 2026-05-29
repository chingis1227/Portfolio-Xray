# Current vs Candidate Comparison Specification

This document owns the V1 product-facing current-vs-candidate comparison adapter for the diagnosis-first Portfolio MRI migration.

Implementation: `src/current_vs_candidate.py`.

Canonical artifact: `current_vs_candidate.json`.

Status: implemented as an additive adapter in code migration Session 07. It reads canonical comparison evidence and writes a focused view. It does not replace `candidate_comparison.json`.

## Scope

The adapter projects the canonical multi-candidate comparison into an MVP view centered on the diagnosed baseline versus one selected candidate or a shortlist.

It reads:

- `candidate_comparison.json` in memory;
- optional `selection_decision.json` in memory for `favored_candidate_id`.

It writes:

- `current_vs_candidate.json`.

It does not:

- change `candidate_comparison.json`;
- change Selection Engine formulas;
- change candidate registry behavior;
- build candidates;
- optimize weights;
- issue a Decision Verdict;
- rename existing fields.

## Artifact Contract

Top-level shape:

```json
{
  "schema_version": "current_vs_candidate_v1",
  "diagnostic_only": true,
  "generated_at": "ISO-8601 UTC timestamp",
  "analysis_end": "YYYY-MM-DD",
  "primary_window": "10y",
  "view_mode": "one_candidate",
  "baseline": {},
  "selected_candidate_ids": [],
  "comparisons": [],
  "source_artifacts": {
    "candidate_comparison": "candidate_comparison.json",
    "selection_decision": "selection_decision.json"
  },
  "warnings": []
}
```

`view_mode` is:

- `diagnosis_only` when no selected comparison row can be produced;
- `one_candidate` when one candidate is compared;
- `shortlist` when two or more selected candidates are compared.

When a diagnosis-only portfolio review completes, root `current_vs_candidate.json` may be a **`no_candidate_v1` tombstone** (`tombstone`, `artifact_status: not_authoritative`) written by `apply_diagnosis_only_product_bundle_hygiene` — not a live comparison adapter output.

Each `comparisons[]` row contains candidate identity, status, artifact root, dimension deltas, data quality, and source files.

## Baseline and Candidate Selection

Baseline resolution:

1. `comparison_baseline_candidate_id` when available;
2. `analysis_subject`;
3. `current`.

Selected candidate resolution:

1. explicit `candidate_ids` supplied by a caller;
2. `selection.favored_candidate_id`;
3. first available non-baseline benchmark/optimizer/robust candidate as fallback.

## Dimension Deltas

V1 projects existing fields only:

- return (`cagr`);
- volatility (`vol_annual`);
- max drawdown (`max_drawdown`);
- Sharpe (`sharpe`);
- worst stress loss from comparison stress scenarios.

No new metric formulas are introduced. Deltas are simple candidate minus baseline values from existing comparison evidence.

## Workflow Integration

`write_candidate_comparison_outputs()` writes `current_vs_candidate.json` after `selection_decision.json` is available. This lets the adapter use the favored candidate when Selection has one, while preserving the canonical comparison and Selection contracts.

## Verification

Product contract (Session 10): `check_current_vs_candidate_v1`, `check_block_5_compare_handoff` in `scripts/core_mvp_validation_contract.py`; live gate `block_5_*` in `validate_live_core_artifacts` for profile `product_one_candidate`. Evidence: [Session 10 audit](../audits/2026-05-29_block_5_session_10_current_vs_candidate_decision_verdict.md).

Focused tests:

```text
python -m pytest tests/test_block_5_decision_compare_contract.py tests/test_current_vs_candidate.py -q
```

Recommended adjacent checks:

```text
python -m pytest tests/test_block_5_decision_compare_contract.py tests/test_live_core_e2e_validation.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py -q
python run_portfolio_review.py --candidates equal_weight
python scripts/verify_live_core_e2e.py --profile product_one_candidate
```
