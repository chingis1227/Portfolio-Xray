# Blocks 3-5 Product Handoff Audit — Session 00 and 00.1 Baseline

Date: 2026-06-04
ExecPlan: [Blocks 3-5 Product Handoff Integration Readiness Audit Plan](../exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md)
Scope: Session 00 and Session 00.1 only — read-only source-of-truth and baseline normalization.

---

## 1. Executive summary

The controlling plan is `docs/exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md`.
Its audit question is:

```text
Stress evidence -> Investment diagnosis -> Testable Launchpad card -> Builder prefill
```

Session 00 is closed as a read-only baseline/source-of-truth check. Session 00.1 is closed as a
baseline normalization pass. No source code was changed, no optimizer was run, no candidate was
generated, and no weights were written.

Key result: the actual handoff chain is owned by Stress Lab product blocks in `stress_report.json`,
Block 4 v3 diagnosis files under `analysis_subject/`, Candidate Launchpad v3 cards, and the pure
Builder prefill helper. Older one-candidate/readiness evidence and the Block 4 -> Builder handoff
plan are supporting evidence only; they do not replace the canonical sessions of the current plan.

---

## 2. Source-of-truth documents read

Baseline project rules and workflow documents:

- `AGENTS.md`
- `SPEC.md`
- `OUTPUTS.md`
- `TESTING.md`
- `WORKFLOW.md`
- `PLANS.md`

Relevant product/operator/spec documents:

- `docs/product_flow_operator_guide.md`
- `docs/runtime_entrypoints.md`
- `docs/specs/stress_lab_layer_spec.md`
- `docs/specs/stress_testing_spec.md`
- `docs/specs/current_portfolio_stress_scorecard_spec.md`
- `docs/specs/block_4_diagnosis_v3_spec.md`
- `docs/specs/candidate_launchpad_spec.md`
- `docs/specs/portfolio_alternatives_builder_spec.md`
- `docs/specs/candidate_portfolios_spec.md`
- `docs/specs/current_vs_candidate_spec.md`

Current contract hierarchy from these files:

1. `AGENTS.md`, `SPEC.md`, and detailed specs are current source of truth.
2. `block_4_diagnosis_v3_spec.md` is the current product contract for Block 4; v2 and legacy scoring-heavy surfaces are not the controlling product contract.
3. `candidate_launchpad_spec.md` explicitly says current V3 cards are produced by `src/block_4/launchpad_cards.py`; `src/candidate_launchpad.py` is legacy/unit-test compatibility.
4. `portfolio_alternatives_builder_spec.md` explicitly defines Builder prefill as a setup object only; it must not execute candidate factory, optimizer, or weight writes.

---

## 3. Real handoff ownership map

| Handoff step | Real artifact / interface | Owning files found | Baseline status |
| --- | --- | --- | --- |
| Stress Lab evidence | `analysis_subject/stress_report.json` with `stress_results_v1`, `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1` | `src/stress.py`, `src/stress_results_block.py`, `src/hedge_gap_analysis_block.py`, `src/current_portfolio_stress_scorecard_block.py`, `run_report.py` | Current product evidence source for this audit. |
| Stress/X-Ray evidence -> diagnosis | in-memory `portfolio_xray` + `stress_report` converted to `problem_classification_v3` | `src/block_4/evidence_extraction.py`, `src/block_4/problem_scoring.py`, `src/block_4/problem_prioritization.py`, `src/block_4/action_path_mapping.py`, `src/block_4/diagnosis_builder.py` | Main target for Session 01 and Session 02. |
| Diagnosis artifact | `analysis_subject/problem_classification.json`, schema `problem_classification_v3` | `src/block_4/diagnosis_builder.py`, `run_report.py`, validators in `scripts/core_mvp_validation_contract.py` | Current product Block 4 artifact. |
| Diagnosis -> Launchpad card | `analysis_subject/candidate_launchpad.json`, schema `candidate_launchpad_v3` | `src/block_4/launchpad_cards.py`, `src/block_4/diagnosis_builder.py`, validators in `scripts/core_mvp_validation_contract.py` | Current product Launchpad writer. |
| Launchpad card -> Builder prefill | `build_builder_prefill_from_launchpad_card(card, *, next_diagnostic_step=None) -> dict` | `src/portfolio_alternatives_builder.py`, `scripts/validate_block_4_live.py`, validator `check_builder_prefill` / `builder_prefill_product_contract_violations` | Pure setup/prefill boundary; no automatic generation. |

Important code facts found by static inspection:

- `src/stress.py` attaches `stress_results_v1`, `hedge_gap_analysis_v1`, and
  `current_portfolio_stress_scorecard_v1`.
- `run_report.py` re-attaches/enriches Stress Lab product blocks and then calls
  `write_block_4_diagnosis_outputs`.
- `src/block_4/diagnosis_builder.py` builds both `problem_classification.json` and
  `candidate_launchpad.json`, and records `next_diagnostic_step`.
- `src/block_4/launchpad_cards.py` sets `is_rebalance_recommendation: false` and carries the
  decision boundary into cards.
- `src/portfolio_alternatives_builder.py` contains the prefill helper and separate plan/run helpers;
  the prefill helper is the relevant interface for this audit, not candidate execution.

---

## 4. Supporting plans and evidence normalization

The following files are supporting evidence, not controlling plans:

- `docs/exec_plans/2026-06-04_block_4_portfolio_alternatives_builder_handoff.md`
- `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_01.md`
- `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_02.md`
- `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_03.md`
- `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_03_1.md`
- `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_04.md`

Normalization decision:

- The old broader one-candidate readiness sessions may be cited for validator and FRED-blocker context.
- They must not close the current plan's Stress -> diagnosis behavior audit unless they answer the
  exact canonical handoff question.
- The Block 4 -> Builder handoff plan may close the Launchpad -> Builder prefill part because its
  evidence matches the current plan's boundary: prefill preserves diagnosis context and does not
  generate candidates automatically.

---

## 5. Basis for Session 01

Session 01 should now produce a field-level Contract Map Audit with this shape:

```text
Source block / Field / Produced... / Consumed by next block... / Used in decision... / Gap
```

Minimum fields to map:

- `stress_results_v1.envelope.worst_synthetic`
- `stress_results_v1.envelope.worst_historical`
- `hedge_gap_analysis_v1.summary.main_hedge_gap`
- `hedge_gap_analysis_v1.summary.main_hedge_gap_offset_coverage_ratio`
- `current_portfolio_stress_scorecard_v1.stress_diagnosis`
- `current_portfolio_stress_scorecard_v1.problem_classification_signals`
- Block 2/X-Ray evidence used by Block 4: allocation, portfolio metrics, factor exposure, hidden exposure, risk budget, weakness map.
- `problem_classification_v3.primary_diagnosis`
- `problem_classification_v3.primary_problem`
- `problem_classification_v3.key_evidence`
- `problem_classification_v3.next_diagnostic_step`
- `candidate_launchpad_v3.cards[].source_diagnosis_id`
- `candidate_launchpad_v3.cards[].hypothesis_to_test`
- `candidate_launchpad_v3.cards[].suggested_methods`
- `candidate_launchpad_v3.cards[].success_criteria`
- `candidate_launchpad_v3.cards[].tradeoff_to_watch`
- `candidate_launchpad_v3.cards[].when_to_skip`
- `candidate_launchpad_v3.cards[].decision_boundary`
- `candidate_launchpad_v3.cards[].is_rebalance_recommendation`
- Builder prefill fields preserving the selected card context.

Session 01 should remain read-only. Missing coverage or broken handoff evidence should be recorded
as gaps for a later post-audit ExecPlan, not fixed during Session 01.

---

## 6. Verification performed

Read-only/static verification only:

- Read source-of-truth documents and relevant specs listed above.
- Used `rg --files` and targeted `rg -n` searches to locate specs, source modules, validators, tests,
  and handoff interfaces.
- Inspected current git status before writing this note.

Not run by design:

- No `pytest`.
- No `run_portfolio_review.py`.
- No optimizer or candidate factory.
- No candidate generation.
- No PDF/report generation.
- No weight-writing command.

---

## 7. Session closure

Session 00 verdict: **CLOSED — BASELINE_SOURCE_OF_TRUTH_IDENTIFIED**.

Session 00.1 verdict: **CLOSED — CURRENT_PLAN_NORMALIZED_SUPPORTING_EVIDENCE_SEPARATED**.

Next canonical session: Session 01 — Contract Map Audit.
