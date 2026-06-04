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

## Public artifacts

Filenames stay unchanged:

| Artifact | Path | Schema |
| --- | --- | --- |
| Problem Classification | `{output_dir_final}/analysis_subject/problem_classification.json` | `problem_classification_v3` |
| Candidate Launchpad | `{output_dir_final}/analysis_subject/candidate_launchpad.json` | `candidate_launchpad_v3` |

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
- `backend_audit`

`backend_audit` may contain scoring rows and evidence bundles, but those fields
must not dominate the product surface.

`next_diagnostic_step` is required and must contain `type`, `label`, `reason`,
and `decision_boundary`. For `mixed_evidence_no_action` and
`current_portfolio_acceptable`, the step type is `reference_comparison` and the
default methods are `equal_weight` and `risk_parity`. For
`evidence_insufficient_data_quality`, the step is data improvement and must not
emit Equal Weight / Risk Parity reference tests while comparison evidence is
unreliable.

## Primary selection order

1. Data-quality blocker.
2. Stress-confirmed root-cause.
3. Structural root-cause with sufficient evidence.
4. Mixed evidence / no dominant actionable issue.
5. Current portfolio acceptable / monitor.

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

Cards are hypotheses or reference tests, not trades. Reference cards use
`card_type: "reference_benchmark_test"`, `launch_status: "reference_test"`,
`is_rebalance_recommendation: false`, and a `decision_boundary` stating that the
actual rebalance decision is made only after Current vs Candidate Comparison and
Decision Verdict. Equal Weight is the simple concentration benchmark; Risk
Parity is the risk-distribution benchmark.

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
- `check_block_4_v3_diagnosis_handoff`
