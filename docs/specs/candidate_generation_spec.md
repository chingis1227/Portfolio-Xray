# Candidate Generation Specification

This document owns the Block 7 `candidate_generation.json` contract for Portfolio MRI / Portfolio X-Ray.

Implementation: `src/candidate_generation.py`.

Runtime script: `scripts/generate_candidate_from_builder_setup.py`.

## Product Boundary

Block 7 consumes one validated Block 6 `CandidateSetup` after an explicit Generate Candidate action. It creates exactly one candidate attempt for the selected hypothesis. It is not a candidate zoo, not a ranking arena, and not a rebalance recommendation.

Block 7 may preserve generated weights when a runtime caller supplies them, but it does not compare the candidate against the current portfolio and does not write a Decision Verdict. Current-vs-Candidate Comparison and Decision Verdict remain downstream blocks.

The runtime artifact is:

```text
{output_dir_final}/candidate_generation.json
```

The current default script path is portfolio-first:

```text
.\.venv\Scripts\python.exe scripts\generate_candidate_from_builder_setup.py
```

By default the script reads `Main portfolio/analysis_subject/portfolio_alternatives_builder.json`,
delegates one backend candidate id to `run_candidate_factory.py --execution-mode fast`, and writes
`Main portfolio/candidate_generation.json`. The script does not pass `--then-compare`; Block 8 owns
comparison and Block 9 owns the verdict.

## Public Helpers

The contract builder is:

```text
build_candidate_generation_document(candidate_setup, *, weights=None, status=None, failure_reason=None, infeasibility_reason=None, warnings=None) -> dict
```

The writer is:

```text
write_candidate_generation_outputs(output_dir, *, candidate_setup, weights=None, status=None, failure_reason=None, infeasibility_reason=None, warnings=None) -> dict[str, Path]
```

`candidate_setup_from_builder_document(builder_document)` extracts the validated `candidate_setup` from `portfolio_alternatives_builder.json` and refuses Builder artifacts where `can_generate_candidate` is not `true`.

## Artifact Contract

The schema version is `candidate_generation_v1`.

Top-level required fields:

- `candidate`
- `generation_status`
- `source_builder_setup`
- `method_availability`
- `warnings`
- `handoff_to_comparison`

The `candidate` object preserves:

- `candidate_id`
- `candidate_name`
- `source_card_id`
- `source_diagnosis_id`
- `source_launchpad_card_type`
- `source_builder_setup_id`
- `candidate_setup_id`
- `goal`
- `hypothesis_to_test`
- `method`
- `method_variant`
- `capped`
- `uncapped`
- `min_asset_weight`
- `max_asset_weight`
- `constraint_preset`
- `parameters`
- `constraints`
- `weights`
- `status`
- `failure_reason`
- `infeasibility_reason`
- `success_criteria`
- `tradeoff_to_watch`
- `decision_boundary`
- `is_rebalance_recommendation: false`
- `generation_source: block_6_builder_setup`

If weights are not available yet, the status is `attempt_created` and `handoff_to_comparison.can_compare` is `false`. Later runtime sessions may set `generated`, `failed`, or `infeasible`; failed and infeasible attempts must preserve the source setup and reason instead of silently falling back to another method.

When the Blocks 5-9 vertical script writes this artifact, it also adds optional `product_run` freshness metadata (`run_id`, `artifact_role`, `workflow_state`, `active`, `generated_at`, `upstream_run_ids`). Block 8 refuses a `candidate_generation.json` artifact that is explicitly tombstoned, `artifact_status: not_authoritative`, or `product_run.active: false`. This prevents a diagnosis-only or inactive candidate artifact from becoming a comparison input.

## Runtime Failure and Infeasible Handling

`scripts/generate_candidate_from_builder_setup.py` converts backend factory evidence into the
Block 7 artifact:

- factory `succeeded` or `skipped_existing` plus readable `weights.json` becomes
  `generation_status: generated`;
- factory failure with an infeasible reason, builder status, builder reason, or message becomes
  `generation_status: infeasible`;
- factory failure without infeasible evidence becomes `generation_status: failed`;
- missing factory evidence becomes `generation_status: failed`.

Failed and infeasible attempts keep `weights: null`, keep `is_rebalance_recommendation: false`, and
set `handoff_to_comparison.can_compare: false`. Existing `weights.json` files are ignored when the
current factory step is failed or infeasible, so stale artifacts cannot turn a failed attempt into a
candidate recommendation or comparison input.

## Method Mapping

Block 7 uses the guided Block 6 method mapping:

| Product method | Capped variant | Uncapped variant |
| --- | --- | --- |
| `equal_weight` | `equal_weight` | `equal_weight` |
| `risk_parity` | `risk_parity` | `risk_parity` |
| `hierarchical_risk_parity` | `hierarchical_risk_parity` | `hierarchical_risk_parity` |
| `minimum_variance` | `minimum_variance` | `minimum_variance_uncapped` |
| `minimum_cvar` | `minimum_cvar_constrained` | `minimum_cvar_uncapped` |
| `maximum_diversification` | `maximum_diversification` | `maximum_diversification_uncapped` |

Uncapped mode keeps `max_asset_weight: null`, `capped: false`, and the standard concentration warning. Candidates created through this artifact remain diagnostic comparison candidates, not automatic rebalance instructions.

## Guardrails

Block 7 must:

- reject missing, invalid, or non-generatable `CandidateSetup` inputs;
- create one candidate attempt only;
- keep `is_rebalance_recommendation: false`;
- preserve success criteria, tradeoff, and decision boundary from Block 6;
- avoid writing comparison, verdict, action, or trade-execution instructions;
- set `handoff_to_comparison.can_compare` only when candidate weights are available.

## Verification

Focused checks:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_candidate_generation_from_builder_setup.py tests\test_candidate_generation_method_mapping.py tests\test_candidate_generation_no_recommendation_boundary.py -q
```

Runtime failure/infeasible checks:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_candidate_generation_failed_infeasible.py -q
```
