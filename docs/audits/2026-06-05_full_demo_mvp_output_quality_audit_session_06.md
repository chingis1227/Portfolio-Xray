# Full Demo MVP Output Quality Audit - Session 06

Date: 2026-06-05
Related plan: [Full Demo MVP Readiness Audit and Hardening](../exec_plans/2026-06-05_full_demo_mvp_readiness_audit_and_hardening_plan.md)
Status: **NOT_ACCEPTED_YET** for full demo output quality.

## Scope

This audit reads the three Session 02 demo output folders and checks whether the product story is understandable without the original developer explaining it orally:

- `output/demo_portfolios/balanced/final/`
- `output/demo_portfolios/equity_heavy/final/`
- `output/demo_portfolios/defensive_rates_sensitive/final/`

The audit does not treat generated outputs as source and does not refresh or edit generated artifacts. It uses them only as evidence.

## Acceptance standard

For each portfolio, the outputs should let a human explain in 5-7 sentences:

1. what the current portfolio problem is;
2. what hypothesis was tested;
3. what candidate or reference was generated, if any;
4. what improved;
5. what worsened;
6. whether action is justified;
7. what evidence is missing or should be monitored next.

The outputs must not imply a best portfolio without evidence, must not present a reference benchmark as a rebalance recommendation, and must not hide data-quality or model limitations.

## Portfolio 1 - Balanced diversified

### Product acceptance note

The current portfolio diagnosis is `mixed_evidence_no_action`: no dominant actionable problem is confirmed, and the evidence is mixed enough that an immediate rebalance is not justified. The Launchpad correctly proposes a reference test, not a recommendation: compare the current portfolio against simple references, with `equal_weight` selected by Builder. Candidate Generation creates an Equal Weight reference portfolio and explicitly says it is not a rebalance recommendation. Current vs Candidate cannot evaluate the reference because all 12 comparison dimensions have unavailable candidate metrics. Decision Verdict is therefore `evidence_insufficient`, with the recommended action to review missing or degraded evidence before acting. AI Commentary context has enough grounding to explain the diagnosis, candidate lineage, and evidence-insufficient verdict, but not enough grounded data to explain actual improvements or trade-offs. A client-ready explanation is possible only as an honest "we tested the path but comparison evidence is missing" explanation, not as a successful demo of improvement vs worsening.

### Audit result

| Gate | Result | Evidence |
| --- | --- | --- |
| Diagnosis clarity | Pass with caveat | `problem_classification.json` has `primary_diagnosis.diagnosis_id = mixed_evidence_no_action`, but `status = partial` and warning `legacy_sections_fallback_used`. |
| Hypothesis clarity | Pass | `candidate_launchpad.json` and Builder state that the test is a simple reference comparison and not an immediate rebalance. |
| Candidate lineage | Pass | `candidate_generation.json` links the Equal Weight candidate to the Launchpad card and Builder setup. |
| Comparison clarity | Fail for demo | `current_vs_candidate.json` comparison status is `unavailable`; 12/12 dimensions have unavailable candidate values; `what_improved` and `what_worsened` are empty. |
| Verdict clarity | Pass | `decision_verdict.json` gives `evidence_insufficient` and `no_available_comparison_metrics`. |
| Client-ready without explanation | Not accepted | The output can explain missing evidence, but cannot answer what improved or worsened. |

## Portfolio 2 - Equity-heavy / concentrated

### Product acceptance note

The current portfolio also receives `mixed_evidence_no_action`: the system does not identify a dominant actionable problem strongly enough to force a rebalance. Launchpad again chooses a simple reference comparison rather than an action recommendation. Builder and Candidate Generation produce an Equal Weight reference candidate and preserve the boundary that the candidate is not a recommendation. Current vs Candidate cannot compare the candidate because all 12 comparison dimensions are unavailable. The verdict is correctly `evidence_insufficient`, not a no-trade verdict and not a rebalance recommendation. AI Commentary context can cite diagnosis, candidate lineage, and confidence limitations, but cannot support claims about improvement, deterioration, or accepted trade-offs. This is honest, but it is not a complete product demo for this fixture.

### Audit result

| Gate | Result | Evidence |
| --- | --- | --- |
| Diagnosis clarity | Pass with caveat | `problem_classification.json` has `primary_diagnosis.diagnosis_id = mixed_evidence_no_action`, `status = partial`, and `legacy_sections_fallback_used`. |
| Hypothesis clarity | Pass | Launchpad and Builder describe a reference benchmark test. |
| Candidate lineage | Pass | Equal Weight is generated from the Builder setup with `generation_status = generated`. |
| Comparison clarity | Fail for demo | `current_vs_candidate.json` marks the comparison `unavailable`; 12/12 dimensions are unavailable; no improvement/worsening list exists. |
| Verdict clarity | Pass | `decision_verdict.json` correctly reports `evidence_insufficient` due to `no_available_comparison_metrics`. |
| Client-ready without explanation | Not accepted | Same blocker as balanced: the user cannot see the trade-off. |

## Portfolio 3 - Defensive / rates-sensitive

### Product acceptance note

The current portfolio diagnosis is `weak_crisis_resilience`, with the key human-readable evidence that the worst synthetic stress loss is -40.0%. The Launchpad outcome is `monitor`, and the available card is effectively a keep-current-and-monitor path, not a generated portfolio hypothesis. Builder blocks candidate generation with `reason = data_quality_blocker` and `can_generate_candidate = false`. Because no candidate is generated, there is no Current vs Candidate comparison and no Decision Verdict. The analysis-subject AI Commentary context is diagnosis-only and can explain the current problem and monitoring posture, but it cannot explain a candidate test, improvements, worsening, or a verdict. This is an honest blocked case, but it cannot count as one of three successful full-demo portfolios unless the demo explicitly includes a blocked-case story.

### Audit result

| Gate | Result | Evidence |
| --- | --- | --- |
| Diagnosis clarity | Pass with caveat | `problem_classification.json` has `weak_crisis_resilience`, `status = partial`, and a direct -40.0% worst-stress headline. |
| Hypothesis clarity | Partial | The system says to monitor rather than launch a portfolio-changing candidate, but the card title "Improve Crisis Resilience" may sound like an action path. |
| Candidate lineage | Not applicable / blocked | `portfolio_alternatives_builder.json` has `status = blocked`, `reason = data_quality_blocker`, and `can_generate_candidate = false`. |
| Comparison clarity | Not available | Root `candidate_generation.json`, `current_vs_candidate.json`, and `decision_verdict.json` are absent for this fixture. |
| Verdict clarity | Fail for full demo | No Block 9 verdict exists because the path blocks before candidate generation. |
| Client-ready without explanation | Not accepted for full demo | It is understandable as an honest data-quality/monitoring block, not as a complete candidate comparison demo. |

## Cross-portfolio findings

1. **Reference-vs-recommendation boundary is mostly safe.** The generated candidate and Builder outputs repeatedly state that Equal Weight is a reference benchmark and not a rebalance recommendation.
2. **The main demo blocker is comparison evidence, not candidate lineage.** Balanced and equity-heavy have clear lineage through Launchpad, Builder, and Candidate Generation, but Block 8 cannot populate candidate metrics.
3. **Evidence-insufficient is honest and consistent.** The verdict does not overstate the candidate and correctly points to missing comparison metrics.
4. **The outputs are still backend-oriented.** A non-developer can understand the high-level diagnosis only after reading several JSON fields; there is no concise product-facing acceptance summary artifact.
5. **Generated outputs predate the Session 04 product-run lineage hardening.** These Session 02 artifacts do not show the newer `product_run.run_id` metadata in the fields inspected here, so freshness must be inferred from file location and timestamps rather than lineage metadata.
6. **The defensive fixture is useful as a blocked-case regression, not as a full demo success.** It proves the system can refuse unsafe generation, but it does not satisfy the three-portfolio full-demo gate.

## Concrete output-quality improvements needed

These are output-quality improvements, not instructions to rewrite the commentary engine in Session 06:

1. **Add or expose a deterministic demo summary per portfolio** that states diagnosis, hypothesis, candidate status, comparison status, verdict, and missing evidence in 5-7 sentences.
2. **Make Block 8 unavailable status more product-facing** by summarizing which candidate metrics are missing and why no improvement/worsening can be claimed.
3. **Add a clear blocked-case summary for Builder blocks** so the defensive fixture has a root-level product artifact explaining why candidate/comparison/verdict were not produced.
4. **Preserve the reference benchmark boundary in all summaries**: Equal Weight is a transparent reference test, not a recommended rebalance.
5. **Avoid demo acceptance until at least two full fixtures can show grounded `what_improved` and `what_worsened`, or until the demo script explicitly positions the run as an evidence-insufficient demonstration.**

## Final Session 06 verdict

Session 06 output quality status: **NOT_ACCEPTED_YET**.

The outputs are truthful and do not overclaim, but the full demo story is incomplete. Balanced and equity-heavy cannot answer the core trade-off question because comparison metrics are unavailable. Defensive/rates-sensitive is a valid blocked path but not a complete comparison/verdict path. Session 07 should use this audit as input for AI Commentary grounding and product-facing summary hardening.
