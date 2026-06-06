# Sample Output Walkthrough

This walkthrough uses the `defensive_rates_sensitive` demo portfolio because its current checked
outputs have the clearest story:

```text
Portfolio input
-> Diagnosis
-> Hypothesis
-> Builder setup
-> Candidate generated
-> What improved
-> What worsened
-> Verdict
-> What to monitor
```

Source config:

```text
config/demo_portfolios/defensive_rates_sensitive.yml
```

Output folder:

```text
output/demo_portfolios/defensive_rates_sensitive/final/
```

The values below are taken from the existing demo output files. If a field is absent in a future
run, treat that as a limitation and do not invent a value.

## 1. Portfolio input

Read:

```text
analysis_subject/run_metadata.json
```

Key fields:

- `analysis_setup.analysis_subject.type`
- `analysis_setup.analysis_subject.weights`
- `analysis_setup.analysis_subject.recommendation_status`
- `analysis_setup.resolved_assumptions.analysis_end`

Current output:

```text
analysis_subject.type: current_portfolio
analysis_subject.weights:
  BND: 0.32
  IEF: 0.16
  TLT: 0.10
  TIP: 0.14
  SHY: 0.08
  GLD: 0.08
  SCHD: 0.06
  SPY: 0.06
recommendation_status: diagnostic_current_portfolio_not_recommendation
analysis_end: 2026-05-31
```

Meaning: the system is diagnosing the user's current portfolio. These weights are not a new target
portfolio.

## 2. Diagnosis

Read:

```text
analysis_subject/problem_classification.json
```

Key fields:

- `primary_diagnosis.diagnosis_id`
- `primary_diagnosis.label_en`
- `primary_diagnosis.thesis_en`
- `key_evidence`
- `next_diagnostic_step`

Current output:

```text
primary_diagnosis.diagnosis_id: weak_crisis_resilience
primary_diagnosis.label_en: Weak crisis resilience
primary_diagnosis.thesis_en: Weak crisis resilience: Offset coverage ratio is 0.00 in the main hedge-gap scenario.
```

Important evidence:

```text
Worst synthetic stress loss: -11.9%
Main hedge-gap offset coverage ratio: 0.00
```

Meaning: the main diagnosed issue is weak crisis resilience. The portfolio is not being judged by a
generic score; the diagnosis is grounded in stress and hedge-gap evidence.

## 3. Hypothesis

Read:

```text
analysis_subject/candidate_launchpad.json
```

Key fields:

- `launchpad_outcome`
- `cards[].card_id`
- `cards[].card_type`
- `cards[].title`
- `cards[].is_rebalance_recommendation`

Current output includes:

```text
launchpad_outcome: proceed_to_launchpad
launchpad_01_improve_crisis_resilience: targeted_hypothesis_test
launchpad_02_reduce_duration_rates_sensitivity: targeted_hypothesis_test
launchpad_03_reduce_concentration: targeted_hypothesis_test
```

Meaning: the product creates hypothesis cards. These are candidate tests, not instructions to
rebalance.

## 4. Builder setup

Read:

```text
analysis_subject/portfolio_alternatives_builder.json
```

Key fields:

- `status`
- `can_generate_candidate`
- `candidate_setup.source_card_id`
- `candidate_setup.goal`
- `candidate_setup.hypothesis_to_test`
- `candidate_setup.selected_method`
- `candidate_setup.success_criteria`
- `candidate_setup.decision_boundary`

Current output:

```text
status: ok
can_generate_candidate: true
candidate_setup.source_card_id: launchpad_03_reduce_concentration
candidate_setup.goal: Reduce concentration
candidate_setup.selected_method: equal_weight
```

Hypothesis:

```text
Test whether reduce concentration improves high concentration enough to beat the current portfolio on the stated success criteria.
```

Success criteria:

```text
Lower the relevant concentration subtype: capital, risk contribution, factor, region, currency, or duplicate exposure.
Check that top-1/top-3 risk contribution falls, not only capital weight.
```

Meaning: the Builder prepared a specific Equal Weight test to reduce concentration. It still says
that the actual rebalance decision comes later, after comparison and verdict.

Limitation: this specific Builder setup is tied to the selected card `launchpad_03_reduce_concentration`,
even though the primary diagnosis is `weak_crisis_resilience`. That is allowed in the current demo
because the selected card can test a supporting issue, but it should be explained as a tested
hypothesis rather than the only possible response to the primary diagnosis.

## 5. Candidate generated

Read:

```text
candidate_generation.json
```

Key fields:

- `generation_status`
- `candidate.candidate_id`
- `candidate.method`
- `candidate.weights`
- `candidate.is_rebalance_recommendation`
- `handoff_to_comparison.can_compare`

Current output:

```text
generation_status: generated
candidate.candidate_id: equal_weight
candidate.method: equal_weight
candidate.is_rebalance_recommendation: false
handoff_to_comparison.can_compare: true
```

Candidate weights:

```text
BND: 0.125
IEF: 0.125
TLT: 0.125
TIP: 0.125
SHY: 0.125
GLD: 0.125
SCHD: 0.125
SPY: 0.125
```

Meaning: the system generated one Equal Weight candidate as a test portfolio. This is not a
recommendation and not a "best portfolio" claim.

## 6. What improved

Read:

```text
current_vs_candidate.json
```

Key fields:

- `comparison_status`
- `comparisons[].what_improved`
- `comparisons[].risk_reduced`
- `comparisons[].materiality_for_decision_review`

Current output:

```text
comparison_status: available
candidate_id: equal_weight
```

Examples from `what_improved`:

| Field label | Delta | Material |
| --- | ---: | --- |
| Return | 0.022 | true |
| Sharpe | 0.282 | true |
| Worst stress loss | 0.015 | true |
| Largest holding weight | -0.195 | true |
| Top-3 holding weight | -0.245 | true |
| Weight concentration HHI | -0.053 | true |

Examples from `risk_reduced`:

| Field label | Delta | Material |
| --- | ---: | --- |
| Worst stress loss | 0.015 | true |
| Largest holding weight | -0.195 | true |
| Top-3 holding weight | -0.245 | true |
| Weight concentration HHI | -0.053 | true |
| Largest risk contribution | -0.064 | true |

Meaning: the tested Equal Weight candidate improves several return, stress, and concentration
dimensions in this output.

## 7. What worsened

Read:

```text
current_vs_candidate.json
```

Key fields:

- `comparisons[].what_worsened`
- `comparisons[].risk_added`
- `comparisons[].practicality`

Current output examples from `what_worsened`:

| Field label | Delta | Material |
| --- | ---: | --- |
| Volatility | 0.007 | true |
| Max drawdown | -0.003 | false |
| Portfolio beta exposure | 0.094 | true |
| beta_eq absolute exposure | 0.098 | false |
| beta_usd absolute exposure | 0.042 | false |
| beta_cmd absolute exposure | 0.009 | false |

Practicality fields:

```text
turnover_required.status: unavailable
turnover_required.unavailable_reason: baseline_or_candidate_weights_missing
transaction_cost_assumption.status: available
transaction_cost_assumption.transaction_cost_bps: 10.0
estimated_transaction_cost_pct: null
```

Meaning: the candidate is not one-sided. It improves some areas but worsens volatility and beta
exposure. Also, turnover / estimated cost is not fully available, so implementation should not be
treated as automatic.

## 8. Verdict

Read:

```text
decision_verdict.json
```

Key fields:

- `verdict_id`
- `verdict_label`
- `verdict_reason_id`
- `recommended_action`
- `rationale_summary`
- `confidence`
- `guardrails`

Current output:

```text
verdict_id: rebalance_to_selected_candidate
verdict_label: Rebalance to selected candidate for review
verdict_reason_id: rebalance_when_material
confidence: medium
```

Recommended action text:

```text
Candidate equal_weight is material enough for rebalance review; confirm the documented trade-offs before any implementation.
```

Rationale:

```text
The selected candidate shows material improvement against the available comparison evidence.
```

Guardrails include:

```text
does_not_execute_trades: true
does_not_claim_best_portfolio: true
does_not_hide_tradeoffs: true
```

Meaning: the verdict says the candidate is material enough for review. It does not say "buy/sell
now", does not claim the candidate is the best portfolio, and does not hide the worsened fields.

## 9. What to monitor

Read:

```text
ai_commentary_context.json
```

Key fields:

- `client_explanation_draft.sentences`
- `commentary_topics.monitoring_next`
- `commentary_topics.monitoring_trigger`

Current limitation:

```text
what_changed_summary.json: absent
monitoring artifact: not provided
```

The commentary context states that when no monitoring artifact is provided, the next review trigger
should be based on Builder success criteria / skip condition rather than invented monitoring data.

Meaning: the demo can explain the diagnosis, candidate, comparison, and verdict. It cannot claim a
specific monitoring trigger unless a monitoring artifact exists.
