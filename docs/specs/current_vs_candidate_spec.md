# Current vs Candidate Comparison Specification

This document owns the V1 product-facing current-vs-candidate comparison adapter for the diagnosis-first Portfolio MRI migration.

Implementation: `src/current_vs_candidate.py`.

Canonical artifact: `current_vs_candidate.json`.

Status: implemented as an additive adapter in code migration Session 07 and expanded for the
Blocks 5-9 vertical product loop Session 05. It reads canonical comparison evidence and writes
a focused view. It does not replace `candidate_comparison.json`.

## Scope

The adapter projects the canonical multi-candidate comparison into an MVP view centered on the diagnosed baseline versus one selected candidate or a shortlist.

It reads:

- `candidate_comparison.json` in memory;
- optional `selection_decision.json` in memory for `favored_candidate_id`.
- optional `candidate_generation.json` in memory for the selected candidate's hypothesis,
  success criteria, weights, and transaction-cost assumption when those fields are available.
- optional `client_fit_check.json` in memory for Client Fit target rows.

It writes:

- `current_vs_candidate.json`.

It does not:

- change `candidate_comparison.json`;
- change Selection Engine formulas;
- change candidate registry behavior;
- build candidates;
- optimize weights;
- issue a Decision Verdict;
- crown a winner or approve suitability;
- convert Client Fit targets into optimizer behavior;
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
  "requested_candidate_ids": [],
  "selected_candidate_ids": [],
  "comparisons": [],
  "comparison_questions_answered": [],
  "source_artifacts": {
    "candidate_comparison": "candidate_comparison.json",
    "selection_decision": "selection_decision.json",
    "candidate_generation": "candidate_generation.json",
    "client_fit_check": "client_fit_check.json"
  },
  "guardrails": {
    "diagnostic_only": true,
    "does_not_issue_verdict": true,
    "does_not_crown_winner": true
  },
  "warnings": []
}
```

`view_mode` is:

- `diagnosis_only` when no selected comparison row can be produced;
- `one_candidate` when one candidate is compared;
- `shortlist` when two or more selected candidates are compared.

When a diagnosis-only portfolio review completes, root `current_vs_candidate.json` may be a **`no_candidate_v1` tombstone** (`tombstone`, `artifact_status: not_authoritative`) written by `apply_diagnosis_only_product_bundle_hygiene` — not a live comparison adapter output.

Each `comparisons[]` row contains candidate identity, status, artifact root, dimension deltas,
trade-off summaries, practicality fields, success-criteria evaluation, materiality for decision
review, data quality, and source files.

When `client_fit_check.json` is supplied, each comparison row also contains
`client_fit_target_comparison`. This block has schema
`current_vs_candidate_client_targets_v1`, profile/source-quality context, target rows for return,
volatility, historical drawdown, worst stress loss, and horizon when available, plus explicit
`does_not_issue_verdict` and `does_not_crown_winner` guardrails. These rows answer "how do current
and candidate evidence compare with the provided Client Fit targets?" They do not decide whether to
keep, rebalance, or approve the portfolio.

## Baseline and Candidate Selection

Baseline resolution:

1. `comparison_baseline_candidate_id` when available;
2. `analysis_subject`;
3. `current`.

Selected candidate resolution:

1. explicit `candidate_ids` supplied by a caller;
2. `selection.favored_candidate_id`;
3. first available non-baseline benchmark/optimizer/robust candidate as fallback.

`requested_candidate_ids` preserves the requested ids. `selected_candidate_ids` lists only candidates
that produced live `comparisons[]` rows, so `diagnosis_only` outputs do not treat an unavailable or
stale requested candidate as current comparison evidence.

## Dimension Deltas And Trade-off Content

V1 projects existing fields only and does not compute new optimizer outputs. The live comparison
row answers:

- what improved;
- what worsened;
- what stayed similar;
- what risk was reduced;
- what risk was added;
- turnover required when baseline and candidate weights are available;
- transaction-cost assumption and simple estimated cost when turnover is available;
- success-criteria result when criteria can be mapped to available metrics;
- Current vs Candidate vs Client Target rows when Client Fit evidence exists;
- whether evidence is material enough for decision review.

The adapter compares these evidence groups:

- return (`cagr`);
- volatility (`vol_annual`);
- max drawdown (`max_drawdown`);
- Sharpe (`sharpe`);
- worst stress loss from comparison stress scenarios;
- concentration evidence from `weight_concentration` and `diversification` when present;
- factor behavior from `beta_portfolio` and available factor-regression beta fields.

No new metric formulas are introduced. Deltas are simple candidate minus baseline values from
existing comparison evidence, except factor beta rows compare absolute exposure because the
product question is whether factor dependency increased or decreased. If a baseline or candidate
metric is missing, that dimension has `status: unavailable`, `direction: unknown`, and an
`unavailable_reason`; the adapter must not fake a pass or invent a value.

`what_improved`, `what_worsened`, `what_stayed_similar`, `risk_reduced`, and `risk_added` are
compact projections from `dimensions[]`. They are explanatory labels for product readers and do
not replace the underlying numeric deltas.

`practicality.turnover_required` is `available` only when both baseline and candidate weights are
present in comparison evidence or the selected `candidate_generation.json` candidate. Otherwise it
is explicitly `unavailable`. The transaction-cost assumption uses the selected candidate's
`transaction_cost_bps` when provided; otherwise it records the existing Action Engine default of
10 bps with source `action_engine_default`. Estimated transaction cost remains `null` when turnover
is unavailable.

`success_criteria_result` evaluates only simple criteria that can be mapped to available evidence
such as stress loss, drawdown, volatility, return, Sharpe, concentration, risk contribution, or
factor beta. Unmapped criteria are `not_evaluated`; mapped-but-missing criteria are
`unavailable`; worsened mapped metrics are `not_met`.

`materiality_for_decision_review` is a review gate, not a rebalance recommendation. It can say
`review_candidate`, `not_material`, or `insufficient_evidence`. The Decision Verdict remains the
place where action, no-action, or evidence-insufficient outcomes are evaluated.

Client Fit target rows are comparison references only. A candidate moving closer to the stated
return, volatility, drawdown, or stress-loss limit is evidence for later review, not a "winner" and
not a verdict. A candidate moving away from a target is a visible trade-off, not automatic trade
advice. Missing target evidence remains evidence-insufficient for that row rather than being filled
with a fake conclusion.

## Workflow Integration

`write_candidate_comparison_outputs()` writes `current_vs_candidate.json` after `selection_decision.json` is available. This lets the adapter use the favored candidate when Selection has one, while preserving the canonical comparison and Selection contracts.

For the Blocks 5-9 vertical product loop, `write_block8_current_vs_candidate_only_outputs()` provides
a narrower Block 8 boundary. It builds comparison evidence, scopes `candidate_comparison.json` to the
selected candidate, and writes `current_vs_candidate.json` without writing `decision_verdict.json`,
`action_plan.json`, `decision_journal.json`, or `ai_commentary_context.json`. If any of those
downstream files already exist, the Block 8 output records them under
`block_boundary.ignored_downstream_artifacts` and warns with
`stale_downstream_artifact_ignored:*`; they are not treated as current evidence.

When Block 8 is called from the vertical loop after Block 7, it passes the in-memory
`candidate_generation.json` document into this adapter so `success_criteria_result`,
candidate weights, and candidate-level transaction-cost assumptions can be used without reading
or trusting stale downstream verdict artifacts. If candidate-generation evidence is explicitly
tombstoned, `not_authoritative`, or `product_run.active: false`, Block 8 refuses it instead of
using it as a selected candidate source. Vertical-loop outputs carry optional `product_run` metadata
so `current_vs_candidate.json` can be tied back to the same candidate-generation run.

## Verification

Product contract (Session 10): `check_current_vs_candidate_v1`, `check_block_5_compare_handoff` in `scripts/core_mvp_validation_contract.py`; live gate `block_5_*` in `validate_live_core_artifacts` for profile `product_one_candidate`. Evidence: [Session 10 audit](../audits/2026-05-29_block_5_session_10_current_vs_candidate_decision_verdict.md).

Focused tests:

```text
python -m pytest tests/test_block_5_decision_compare_contract.py tests/test_current_vs_candidate.py tests/test_current_vs_candidate_comparison_contract.py tests/test_current_vs_candidate_success_criteria.py tests/test_current_vs_candidate_tradeoffs.py tests/test_block8_current_vs_candidate_boundary.py tests/test_no_stale_candidate_generation.py -q
```

Recommended adjacent checks:

```text
python -m pytest tests/test_block_5_decision_compare_contract.py tests/test_live_core_e2e_validation.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py -q
python run_portfolio_review.py --candidates equal_weight
python scripts/verify_live_core_e2e.py --profile product_one_candidate
```
