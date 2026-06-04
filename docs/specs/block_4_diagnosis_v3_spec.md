# Block 4 v3 Diagnosis-First Contract

Status: **current product contract**. This replaces the prior Block 4 v2
score-heavy contract as the current product path.

Block 4 is an investment diagnosis handoff, not a scoring dashboard. Blocks 1-3
produce evidence; Block 4 converts that evidence into one clear current-portfolio
diagnosis and a small set of hypotheses to test next.

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
- `success_criteria`
- `backend_audit`

`backend_audit` may contain scoring rows and evidence bundles, but those fields
must not dominate the product surface.

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
- `suggested_methods`
- `success_criteria`
- `tradeoff_to_watch`
- `when_to_skip`
- `not_a_recommendation_disclaimer_en`

Cards are hypotheses to test, not trades. Monitor/no-action outcomes must not
generate misleading portfolio methods.

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

