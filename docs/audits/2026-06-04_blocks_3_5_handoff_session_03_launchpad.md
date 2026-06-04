# Blocks 3-5 Handoff Audit — Session 03: Block 4 -> Launchpad

Date: 2026-06-04
Scope: read-only audit of the `Problem Classification -> Candidate Launchpad` handoff.
Plan: `docs/exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md`.

## Question

Does Block 4 diagnosis become safe, testable Candidate Launchpad cards, with the right card types
and launch statuses, and without implying a rebalance recommendation?

## Result

Status: **closed — pass, with one minor coverage note**.

The source and tests show that Block 4 outcomes map into Launchpad v3 cards as diagnostic
hypothesis tests, reference benchmark tests, monitor steps, or data-quality steps. The Launchpad
contract keeps cards diagnostic-only: cards do not generate portfolios, do not include weights,
and set `is_rebalance_recommendation: false` with a decision boundary that defers any actual
rebalance decision to Current vs Candidate Comparison and Decision Verdict.

## Verification

Command run from repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_block_4_launchpad_cards.py tests/test_block_4_action_path_mapping.py tests/test_block_4_no_trade_gate.py -q
```

Observed result:

```text
20 passed in 2.75s
```

## Evidence map

| Handoff / outcome | Source evidence | Test evidence | Audit finding |
| --- | --- | --- | --- |
| Actionable diagnosis -> targeted Launchpad card | `src/block_4/action_path_mapping.py` builds `suggested_action_path_id` and `suggested_actions[]`; `src/block_4/launchpad_cards.py` converts action paths to cards. | `tests/test_block_4_action_path_mapping.py::test_golden_fixture_maps_crisis_primary_action_paths`; `tests/test_block_4_launchpad_cards.py::test_actionable_problem_keeps_targeted_card_before_reference_tests`. | Pass. The golden stress-confirmed diagnosis maps to `weak_crisis_resilience`, then `improve_crisis_resilience`, then a first card with `card_type: targeted_hypothesis_test` and `launch_status: hypothesis_test`. |
| Diagnosis -> Launchpad contract handoff | `src/block_4/diagnosis_builder.py` builds `problem_classification.json` and then `candidate_launchpad.json`; `scripts/core_mvp_validation_contract.py` validates both sides and their handoff. | `tests/test_block_4_launchpad_cards.py::test_golden_fixture_handoff_with_problem_classification_stub`. | Pass. The Launchpad document links back to the Block 4 problem classification and passes the handoff validator. |
| Acceptable current portfolio -> reference benchmark / monitor path | `src/block_4/no_trade_gate.py` maps `current_portfolio_acceptable` to monitor / compare reference benchmarks; `src/block_4/launchpad_cards.py` gives reference cards `reference_benchmark_test` and `reference_test`. | `tests/test_block_4_action_path_mapping.py::test_acceptable_portfolio_suppresses_candidate_methods`; `tests/test_block_4_launchpad_cards.py::test_acceptable_portfolio_suppresses_builder_methods`; `tests/test_block_4_no_trade_gate.py::test_acceptable_portfolio_monitors`. | Pass. Acceptable portfolios do not become a rebalance card; they can expose Equal Weight / Risk Parity only as reference benchmarks. |
| Data-quality primary -> no candidate method | `src/block_4/no_trade_gate.py` maps data-quality failure to `do_not_act_yet`; `src/block_4/launchpad_cards.py` suppresses methods for no-user-action paths. | `tests/test_block_4_action_path_mapping.py::test_data_quality_problem_maps_do_not_act_path`; `tests/test_block_4_launchpad_cards.py::test_data_quality_primary_emits_do_not_act_outcome`; `tests/test_block_4_no_trade_gate.py::test_data_quality_blocks_action`. | Pass. Data-quality cards have no candidate methods, are not reference benchmark tests, and do not invite generation. |
| Conflicting / low-confidence evidence -> no immediate action | `src/block_4/no_trade_gate.py` returns `do_not_act_yet` or monitor when evidence contradicts or confidence is low without stress confirmation. | `tests/test_block_4_no_trade_gate.py::test_conflicting_signals_block_action`; `tests/test_block_4_no_trade_gate.py::test_low_confidence_pre_stress_actionable_primary_monitors_or_blocks`. | Pass. Mixed or weak evidence does not force Launchpad generation or rebalance language. |
| No rebalance recommendation | `src/block_4/launchpad_cards.py` sets `is_rebalance_recommendation: False`, `generates_portfolio: False`, and `DECISION_BOUNDARY_EN`; `scripts/core_mvp_validation_contract.py` rejects cards where this boundary is absent or weakened. | `tests/test_block_4_launchpad_cards.py::test_golden_fixture_builds_contract_valid_launchpad`; `tests/test_block_4_launchpad_cards.py::test_acceptable_portfolio_suppresses_builder_methods`; `tests/test_block_4_launchpad_cards.py::test_cards_include_v2_narrative_fields`. | Pass. Launchpad wording and flags are protected from rebalance interpretation. |

## Contract details confirmed

- Launchpad v3 document is `diagnostic_only: true`.
- Cards contain `source_diagnosis_id`, `hypothesis_to_test`, `card_type`, `launch_status`,
  success criteria, trade-off text, skip rules, disclaimer, and decision boundary.
- Launchpad cards set `generates_portfolio: false`; they are not candidate factory execution.
- `suggested_methods` may appear for hypothesis or reference tests, but the method rows are setup
  suggestions only. Equal Weight / Risk Parity on reference cards use `method_role:
  reference_benchmark`.
- Data-quality / no-action paths suppress candidate methods.
- The validator rejects `is_rebalance_recommendation != false`, missing rebalance boundary,
  `generates_portfolio != false`, `candidate_generation_allowed: true`, and card-level `weights`.

## Documentation consistency spot-check

The checked specs match the implementation boundary:

- `docs/specs/block_4_diagnosis_v3_spec.md` states that Block 4, Launchpad, and Builder prefill
  must not call these investment recommendations and that Decision Verdict is the downstream
  decision layer.
- `docs/specs/candidate_launchpad_spec.md` states that Launchpad cards are hypothesis/reference
  tests, not rebalance recommendations, and are Builder prefill sources rather than candidate
  generation.

This is a spot-check for Session 03 only. The full docs-vs-code contradiction table remains part of
Session 07.

## Gaps / follow-up notes

- Minor coverage note: the current bundle strongly covers the golden actionable path, acceptable
  portfolio/reference path, data-quality path, conflicting evidence, and low-confidence gating.
  It does not include a compact parameterized test that enumerates every problem taxonomy id and
  asserts its exact card type/status. This is not a blocker for the canonical handoff question,
  because the taxonomy-driven mapping and contract validator are covered, but it would be useful
  post-audit regression coverage.

## Read-only boundary

No source code, tests, schemas, optimizer flows, candidate generation, weights, PDFs, or generated
portfolio artifacts were changed as part of this session. Only this audit note and the active
ExecPlan status are intended to change.
