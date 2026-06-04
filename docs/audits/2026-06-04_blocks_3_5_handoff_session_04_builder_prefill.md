# Blocks 3-5 Handoff Audit — Session 04: Launchpad -> Builder Prefill

Date: 2026-06-04
Scope: read-only audit of the `Candidate Launchpad -> Portfolio Alternatives Builder prefill` handoff.
Plan: `docs/exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md`.

## Question

Does a selected Launchpad card become a safe Builder prefill object that preserves the diagnostic
context, keeps benchmark cards as reference tests, blocks data-quality cases, and avoids running the
candidate factory, optimizers, or weight-writing paths automatically?

## Result

Status: **closed — pass**.

The current source and tests show that `build_builder_prefill_from_launchpad_card()` converts one
Launchpad v3 card into a diagnostic setup object only. It preserves the selected card's diagnosis,
goal, hypothesis, suggested methods, success criteria, tradeoff, skip rule, card/status metadata,
rebalance boundary, and optional next diagnostic step. The prefill object keeps
`is_rebalance_recommendation: false`. `candidate_generation_allowed` means only that a later explicit
user/caller action may generate a candidate; it is not auto-generation.

## Verification

Command run from repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py tests/test_candidate_launchpad_builder_handoff.py -q
```

Observed result:

```text
24 passed in 0.55s
```

Note: the older supporting plan evidence recorded `19 passed`; the current canonical rerun records
`24 passed` for the same Session 04 baseline bundle.

## Evidence map

| Handoff / safety point | Source evidence | Test evidence | Audit finding |
| --- | --- | --- | --- |
| Targeted Launchpad card -> guided Builder setup | `src/portfolio_alternatives_builder.py` builds `builder_mode`, `source_diagnosis_id`, `source_card_id`, `goal`, `hypothesis_to_test`, `suggested_method`, alternatives, constraints, success criteria, tradeoff, skip rule, card type, launch status, method role, and decision boundary. | `tests/test_candidate_launchpad_builder_handoff.py::test_weak_crisis_resilience_opens_targeted_crisis_resilience_setup`; `tests/test_portfolio_alternatives_builder.py::test_builder_prefill_from_launchpad_card_preserves_context`. | Pass. Targeted cards become `guided_from_diagnosis` setup with the diagnosis and context preserved. |
| Goal / method / success criteria / tradeoff preserved | `build_builder_prefill_from_launchpad_card()` copies `goal`, method rows, `success_criteria`, `tradeoff_to_watch`, and `when_to_skip` without rewriting the investment meaning. | `tests/test_portfolio_alternatives_builder.py::test_builder_prefill_from_launchpad_card_preserves_context`; `tests/test_candidate_launchpad_builder_handoff.py::test_current_portfolio_acceptable_keeps_monitoring_visible`. | Pass. The prefill retains the Launchpad card's setup context rather than inventing a recommendation. |
| Decision boundary and no rebalance recommendation | `src/portfolio_alternatives_builder.py` always sets `is_rebalance_recommendation: False` and copies the card `decision_boundary`; `scripts/core_mvp_validation_contract.py` rejects missing/weak boundaries and non-false rebalance flags. | `tests/test_candidate_launchpad_builder_handoff.py::test_weak_crisis_resilience_opens_targeted_crisis_resilience_setup`; `tests/test_portfolio_alternatives_builder.py::test_builder_prefill_contract_rejects_missing_decision_boundary`. | Pass. Builder prefill stays pre-verdict and cannot be validated as a rebalance recommendation. |
| Reference cards keep EW/RP as benchmarks | `_builder_method_role()` returns `reference_benchmark` for reference cards; validators require EW/RP rows on reference benchmark prefill to use the reference role. | `tests/test_candidate_launchpad_builder_handoff.py::test_mixed_evidence_no_action_opens_reference_comparison`; `tests/test_portfolio_alternatives_builder.py::test_reference_benchmark_prefill_preserves_reference_role`; `tests/test_portfolio_alternatives_builder.py::test_builder_prefill_contract_rejects_reference_methods_without_reference_role`. | Pass. Equal Weight and Risk Parity stay reference benchmarks, not rebalance instructions. |
| Data-quality cards block candidate setup | `_is_data_quality_card()` and `_builder_mode_for_card()` map data-quality / insufficient-evidence cards to `blocked_data_quality`; validator rejects generation, methods, EW/RP comparisons, and suggested method on data-quality prefill. | `tests/test_candidate_launchpad_builder_handoff.py::test_evidence_insufficient_data_quality_blocks_candidate_generation`; `tests/test_portfolio_alternatives_builder.py::test_builder_prefill_contract_rejects_data_quality_candidate_generation`. | Pass. Data-quality cards do not prepare unreliable candidate generation. |
| Prefill does not execute factory / optimizer / weights | `build_builder_prefill_from_launchpad_card()` only returns a dict; factory command creation is separate in `build_portfolio_alternative_plan()`, and execution is separate in `run_portfolio_alternative_plan()` with `dry_run=True` by default. Plan provenance records `does_not_generate_weights_until_executed: True`. | `tests/test_portfolio_alternatives_builder.py::test_build_portfolio_alternative_plan_delegates_to_single_candidate_factory`; `tests/test_portfolio_alternatives_builder.py::test_run_portfolio_alternative_plan_dry_run_does_not_execute`. | Pass. Builder prefill itself does not run candidate factory, optimizers, subprocesses, or write weights. |
| Unknown / unsafe methods are bounded | `METHOD_TO_CANDIDATE_ID` is an explicit allowlist; unsupported method ids raise `PortfolioAlternativesBuilderError`. | `tests/test_portfolio_alternatives_builder.py::test_build_portfolio_alternative_plan_rejects_unknown_method`. | Pass. Later explicit candidate planning is bounded to known methods. |

## Contract details confirmed

- Builder prefill source is `candidate_launchpad_v3`.
- Targeted cards use `builder_mode: guided_from_diagnosis` and normalize Launchpad
  `targeted_hypothesis` rows to Builder `targeted_candidate_method`.
- Reference benchmark cards keep `method_role: reference_benchmark`; Equal Weight and Risk Parity
  are allowed as references, not as a final recommendation.
- Monitor-only cards set no suggested method and `candidate_generation_allowed: false`.
- Data-quality cards use `builder_mode: blocked_data_quality`, set no suggested method, and keep
  `candidate_generation_allowed: false`.
- `build_builder_prefill_from_launchpad_card()` does not call `build_portfolio_alternative_plan()`,
  `run_candidate_factory.py`, `subprocess.run`, optimizers, or weight writers.
- A later `PortfolioAlternativeBuildPlan` is only a command plan. It delegates to
  `run_candidate_factory.py --candidates <candidate_id>` and records that weights are not generated
  until explicit execution.

## Gaps / follow-up notes

No blocking Session 04 gaps found.

Minor future improvement: add a compact regression guard that mocks or spies on
`build_portfolio_alternative_plan()` / `run_portfolio_alternative_plan()` while building prefill, to
make the "prefill never executes" boundary mechanically explicit. The current source separation and
dry-run execution test already protect the boundary sufficiently for this audit.

## Read-only boundary

No source code, tests, schemas, optimizer flows, candidate generation, weights, PDFs, or generated
portfolio artifacts were changed as part of this session. Only this audit note and the active
ExecPlan status are intended to change.
