# CandidateSetup Specification

This document owns the Block 6 `CandidateSetup` contract for Portfolio MRI / Portfolio X-Ray.

Implementation: `src/portfolio_alternatives_builder.py`.

`CandidateSetup` is the validated setup object produced after Portfolio Alternatives Builder prefill is confirmed or edited. It is what Block 7 Candidate Generation may consume after an explicit Generate Candidate action. It is not a generated candidate portfolio.

## Product Boundary

Block 6 prepares and validates setup only. Block 7 owns candidate generation. Therefore `CandidateSetup` may say `can_generate_candidate: true`, but it must not contain candidate weights, candidate metrics, comparison results, or a Decision Verdict.

The runtime Builder artifact is:

```text
{output_dir_final}/analysis_subject/portfolio_alternatives_builder.json
```

For a valid targeted or reference card the document has `status: ok`, `can_generate_candidate: true`, a `builder_prefill` object, and a `candidate_setup` object. For data-quality blockers it has `status: blocked`, `can_generate_candidate: false`, `reason: data_quality_blocker`, and `candidate_setup: null`.

## Public Helpers

Candidate setup is built through:

```text
builder_prefill_to_candidate_setup(prefill, *, edits=None) -> dict | None
```

The runtime writer is:

```text
write_portfolio_alternatives_builder_outputs(output_dir, *, candidate_launchpad, problem_classification=None) -> dict[str, Path]
```

The writer materializes Block 6 setup after `candidate_launchpad.json` is written. It does not run candidate factory, does not call optimizers, and does not write `current_vs_candidate.json` or `decision_verdict.json`.

## Required Fields

A valid `CandidateSetup` contains:

- `candidate_setup_id`
- `builder_prefill_id`
- `source_card_id`
- `source_diagnosis_id`
- `source_launchpad_card_type`
- `goal`
- `hypothesis_to_test`
- `selected_method`
- `original_suggested_method`
- `method_changed_by_user`
- `parameters`
- `constraints`
- `success_criteria`
- `tradeoff_to_watch`
- `when_to_skip`
- `decision_boundary`
- `is_rebalance_recommendation`
- `can_generate_candidate`
- `validation_status`
- `validation_warnings`
- `created_at`

`source_launchpad_card_type`, `hypothesis_to_test`, `success_criteria`, `tradeoff_to_watch`, and `decision_boundary` preserve the Launchpad-to-Builder product context so Block 7 can generate a traceable candidate attempt without inventing rationale. `parameters` and `constraints` are the simple Builder setup fields selected or confirmed by the user: `goal`, `method`, `mode`, `constraint_preset`, `min_asset_weight`, and `max_asset_weight`. The only user-adjustable optimization fields in the MVP are `min_asset_weight` and `max_asset_weight`. Preset labels are visible setup labels; Block 6 does not translate them into hidden optimizer formulas.

Guided Block 6 methods are limited to `equal_weight`, `risk_parity`, `hierarchical_risk_parity`, `minimum_variance`, `minimum_cvar`, and `maximum_diversification`. Capped mode maps Minimum Variance, Minimum CVaR, and Maximum Diversification to the current constrained candidate engines; uncapped mode maps them to the uncapped engines. Uncapped setup must keep `min_asset_weight: 0.0`, `max_asset_weight: null`, `capped: false`, and the concentration warning defined in the Portfolio Alternatives Builder spec.

## Prohibited Fields

`CandidateSetup` must not contain:

- `candidate_id`
- `weights`
- `portfolio_metrics`
- `stress_results`
- `comparison`
- `verdict`

These fields are downstream artifacts of candidate generation, candidate diagnostics, current-vs-candidate comparison, or Decision Verdict.

## Validation Status

`CandidateSetup` is emitted only when Builder validation returns `validation_status: valid` and `can_generate_candidate: true`. Invalid, missing-method, unsupported-method, infeasible, reference-boundary, or data-quality blocked states keep `candidate_setup: null` in the runtime Builder document.

## Verification

Focused checks:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_block_6_candidate_setup_contract.py tests\test_block_6_product_runtime_wiring.py -q
```

Full Block 6 adjacent checks:

```text
$block6 = Get-ChildItem -Path .\tests -Filter 'test_block_6_*.py' | ForEach-Object { $_.FullName }; .\.venv\Scripts\python.exe -m pytest $block6 .\tests\test_portfolio_alternatives_builder.py .\tests\test_candidate_launchpad_builder_handoff.py -q
```
