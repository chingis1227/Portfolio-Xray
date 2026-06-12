# Block 4 v3 Diagnosis-First Contract

Status: **current product contract**. This replaces the prior Block 4 v2
score-heavy contract as the current product path.

Block 4 is an investment diagnosis handoff, not a scoring dashboard. Blocks 1-3
produce evidence; Block 4 converts that evidence into one clear current-portfolio
diagnosis and a small set of hypotheses to test next. It identifies the
diagnosis and the `next_diagnostic_step`; Candidate Launchpad exposes that step
as testable cards; Portfolio Alternatives Builder consumes a selected card only
to pre-fill a candidate setup. Candidate generation is downstream and requires
an explicit user action.

Block 4 must never end with an empty path. It may conclude that no immediate
rebalance is justified, but it still emits a `next_diagnostic_step`: either a
targeted hypothesis test, a reference benchmark comparison, monitoring, or a
data-quality improvement step. Block 4, Launchpad, and Builder prefill must not
call these investment recommendations. Decision Verdict is the only downstream
product layer that decides whether action is justified after current-vs-candidate
comparison evidence exists.

Client Fit V1 is accepted as optional backend evidence context via
`client_fit_check.json`. Evidence extraction may emit `client_fit_status`,
`goal_risk_conflict`, `client_fit_within_profile`, and `client_fit_<dimension>` signals from that
artifact. The rulebook may use dimension-level Client Fit signals as supporting or contrary
evidence for existing diagnoses, but a generic Client Fit breach is not a universal primary
diagnosis. The only Client Fit primary exception in Block 4 is `goal_risk_conflict`, which is an
objective-profile consistency outcome and routes to objective review before candidate testing.

## Public artifacts

Filenames stay unchanged:

| Artifact | Path | Schema |
| --- | --- | --- |
| Problem Classification | `{output_dir_final}/analysis_subject/problem_classification.json` | `problem_classification_v3` |
| Candidate Launchpad | `{output_dir_final}/analysis_subject/candidate_launchpad.json` | `candidate_launchpad_v3` |

Optional upstream context:

| Artifact | Path | Schema |
| --- | --- | --- |
| Client Fit Check | `{output_dir_final}/analysis_subject/client_fit_check.json` | `client_fit_check_v1` |

## Product principles

- One primary diagnosis/outcome.
- Maximum two secondary diagnoses.
- Maximum five key evidence points.
- Maximum three Launchpad cards.
- Root-cause diagnoses outrank symptoms.
- Symptoms support the diagnosis; they do not normally compete as primary.
- Mixed usable evidence is handled as `mixed_evidence_no_action` or as a warning
  note. It is not a normal “conflicting signals” primary verdict.
- Bad data is separate: `evidence_insufficient_data_quality`.
- Scoring is backend audit metadata only. User-facing output must read as an
  investment thesis.

## Problem roles

Root-cause diagnoses:

- `weak_crisis_resilience`
- `poor_diversification`
- `high_concentration`
- `duration_rates_vulnerability`
- `credit_liquidity_fragility`
- `weak_hedge_behavior`

Symptoms:

- `high_volatility`
- `high_drawdown`
- `high_equity_beta`
- `high_tail_risk`
- `low_return_risk_efficiency`
- `poor_rates_up_behavior`

Outcome/status diagnoses:

- `current_portfolio_acceptable`
- `goal_risk_conflict`
- `mixed_evidence_no_action`
- `evidence_insufficient_data_quality`

## `problem_classification_v3` required user-facing fields

- `primary_diagnosis`
- `root_cause`
- `supporting_symptoms`
- `key_evidence`
- `why_this_matters`
- `why_not_other_problems`
- `confidence`
- `confidence_explanation`
- `materiality`
- `actionability`
- `suggested_hypothesis`
- `next_diagnostic_step`
- `success_criteria`
- `interpretation_chain`
- `diagnosis_evidence_items`
- `root_cause_narrative`
- `metric_to_diagnosis_trace`
- `professional_rationale_refs`
- `backend_audit`
- `client_fit_status`
- `diagnostic_quality_status`
- `client_fit_context`

`backend_audit` may contain scoring rows and evidence bundles, but those fields
must not dominate the product surface.

`interpretation_chain` is an additive Session 04 field emitted by the Block 4
builder. It must be deterministic and diagnostic-only. It does not rescore or
reprioritize problems; it exposes the already-selected diagnosis as a sourced
chain:

```text
source artifact field
-> evidence signal / evidence item
-> selected diagnosis
-> root-cause narrative
-> rejected alternatives
-> next diagnostic step
```

The top-level `diagnosis_evidence_items`, `root_cause_narrative`,
`metric_to_diagnosis_trace`, and `professional_rationale_refs` mirror the same
objects inside `interpretation_chain` for display adapters that should not parse
backend scoring rows. These fields are source-backed explanation fields, not a
new formula source and not a rebalance recommendation.

`client_fit_status` and `diagnostic_quality_status` are separate fields. `client_fit_status`
summarizes the provided profile fit (`fit`, `watch`, `breach`, `conflict`, `not_provided`, or
`evidence_insufficient`). `diagnostic_quality_status` summarizes portfolio diagnostic quality
(`clean`, `watch`, `issue`, `material_issue`, or `evidence_insufficient`) from objective Block 4
evidence. A portfolio can have `client_fit_status = breach` and
`diagnostic_quality_status = clean`, or `client_fit_status = fit` and
`diagnostic_quality_status = material_issue`; neither field may overwrite the other.

`next_diagnostic_step` is required and must contain `type`, `label`, `reason`,
and `decision_boundary`. For `mixed_evidence_no_action` and
`current_portfolio_acceptable`, the step type is `reference_comparison` and the
default methods are `equal_weight` and `risk_parity`. For
`evidence_insufficient_data_quality`, the step is data improvement and must not
emit Equal Weight / Risk Parity reference tests while comparison evidence is
unreliable.

For `goal_risk_conflict`, the step type is `client_objective_review`; it asks the user to clarify
return, volatility, drawdown, and horizon trade-offs before interpreting candidate tests. This is
not a promise that an optimizer can satisfy inconsistent goals.

## Confidence and data-quality gates

Confidence is evidence quality, not severity. A high-severity problem can still
be low confidence when source evidence is partial, stress coverage is missing,
or the diagnosis relies on fallback artifacts.

The runtime emits `partial_sections` for both legacy `sections.*.status` and
Core MVP product blocks `block_2_1_*` through `block_2_6_*` when any relevant
status is `partial` or `unavailable`. It emits `stress_block_unavailable` when
the stress handoff is unavailable. Actionable diagnoses are confidence-capped
when `partial_sections` is present, even if they still activate.

`evidence_insufficient_data_quality` becomes the primary blocker when either:

- the hard `data_trust_failure` signal is present; or
- partial X-Ray evidence and missing Stress Lab evidence appear together.

Partial X-Ray evidence alone does not automatically block diagnosis or suppress
Launchpad when Stress Lab still confirms a material primary diagnosis; it lowers
confidence and marks the artifact `partial` unless paired with missing stress
evidence or a hard trust failure.

## Primary selection order

1. Data-quality blocker.
2. Stress-confirmed root-cause.
3. Structural root-cause with sufficient evidence.
4. Mixed evidence / no dominant actionable issue.
5. Current portfolio acceptable / monitor.

`sufficient evidence` means the activated root-cause row has at least medium confidence or at least
medium materiality. A low-confidence and low-materiality root-cause label must not automatically
outrank a better-supported symptom. When a supported root cause is selected, activated symptom rows
that are not selected as secondary diagnoses are rejected with a symptom-over-root-cause explanation
rather than a generic lower-priority note.

## Launchpad v3 card contract

Each card must include:

- `source_diagnosis_id`
- `hypothesis_to_test`
- `card_type`
- `launch_status`
- `why_this_test`
- `suggested_methods`
- `success_criteria`
- `tradeoff_to_watch`
- `when_to_skip`
- `is_rebalance_recommendation`
- `decision_boundary`
- `not_a_recommendation_disclaimer_en`
- optional `client_fit_context`
- optional `client_fit_relevance_en`

Cards are hypotheses or reference tests, not trades. Reference cards use
`card_type: "reference_benchmark_test"`, `launch_status: "reference_test"`,
`is_rebalance_recommendation: false`, and a `decision_boundary` stating that the
actual rebalance decision is made only after Current vs Candidate Comparison and
Decision Verdict. Equal Weight is the simple concentration benchmark; Risk
Parity is the risk-distribution benchmark.

When `client_fit_check.json` is available, Candidate Launchpad may include a compact
`client_fit_context` and card-level `client_fit_relevance_en`. These fields explain how the
provided-profile status relates to the test path, but they must not change the objective diagnosis,
issue trade instructions, or suppress material structural issues. In particular,
`client_fit_status = fit` plus `diagnostic_quality_status = material_issue` must still leave the
material diagnosis eligible for a review/test card rather than automatically routing to no-action.

When an actionable primary diagnosis exists, the first card must remain the
targeted hypothesis for that diagnosis. Equal Weight / Risk Parity reference
tests may appear only as secondary reference tests and must not displace the
targeted card.

## Portfolio Alternatives Builder handoff

Launchpad v3 cards are valid Builder prefill sources. The Builder handoff keeps
the diagnostic context visible by preserving `source_diagnosis_id`,
`hypothesis_to_test`, `success_criteria`, `tradeoff_to_watch`, `when_to_skip`,
`decision_boundary`, and `is_rebalance_recommendation: false`.

For actionable diagnoses, Builder opens `builder_mode: guided_from_diagnosis`
with a targeted candidate setup. For mixed or acceptable evidence, Builder opens
an Equal Weight / Risk Parity reference benchmark setup. For data-quality
blockers or monitor-only outcomes, Builder opens a blocked or monitor setup with
`candidate_generation_allowed: false`. In all cases,
`candidate_generation_allowed: true` only means the UI may show an explicit
generate-candidate action; it never means automatic candidate generation.

## Success criteria examples

| Action path | Success criteria |
| --- | --- |
| `improve_crisis_resilience` | lower worst stress loss; improve offset coverage |
| `improve_diversification` | lower top-3 risk contribution, correlation, or duplicate exposure |
| `reduce_concentration` | lower the relevant concentration subtype |
| `reduce_duration_rates_sensitivity` | lower rates loss and `beta_rr` |
| `improve_hedge_behavior` | higher offset coverage and more reliable helped assets |
| `reduce_tail_risk` | improve ES/CVaR or severe drawdown tail |

## Validators

Current product validators live in `scripts/core_mvp_validation_contract.py`:

- `check_problem_classification_v3`
- `check_candidate_launchpad_v3`

## Dynamic fixture matrix

The diagnosis interpretation chain is regression-tested against ten deterministic portfolio
archetypes in `tests/block_4_fixtures.py` and
`tests/test_diagnosis_interpretation_fixture_matrix.py`. The matrix covers concentrated equity,
balanced, duration-heavy, credit-carry, pseudo-diversified equity, cash-heavy, weak-hedge,
insufficient-data, conflicting-signal, and acceptable/no-action cases. These fixtures are not
generated portfolio-review outputs; they are compact source-backed inputs for the Block 4 builder.

The matrix must prove that different portfolio evidence produces different selected diagnosis IDs,
root-cause narratives, leading evidence signals, Launchpad outcomes, and FastAPI diagnosis summaries.
It must also preserve the diagnostic-only boundary: evidence items and traces cite deterministic
source artifacts, and no fixture can turn Problem Classification or Launchpad into a rebalance
recommendation.
- `check_block_4_v3_diagnosis_handoff`
