# Blocks 3-5 Handoff Session 01 — Contract Map Audit

Date: 2026-06-04

Plan: `docs/exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md`

Scope: read-only field-level audit for the product handoff:

    Stress evidence -> Investment diagnosis -> Testable Launchpad card -> Builder prefill

This session inspected source and specs only. It did not change source code, run candidate generation,
run optimizers, refresh generated portfolio artifacts, write weights, or treat any Launchpad/Builder
object as a rebalance recommendation.

## Inspection performed

Commands / targeted reads:

- `rg -n "stress_diagnosis|hedge_gap|weakness_map|hidden_risk|risk_budget|factor_exposure|next_diagnostic_step|decision_boundary|is_rebalance_recommendation|source_diagnosis_id|primary_diagnosis|hypothesis|launch_status|card_context|candidate_launchpad_v3|builder_prefill" src scripts tests docs -S`
- Targeted reads of:
  - `src/block_4/evidence_extraction.py`
  - `src/block_4/diagnosis_builder.py`
  - `src/block_4/problem_taxonomy.py`
  - `src/block_4/problem_scoring.py`
  - `src/block_4/severity_confidence.py`
  - `src/block_4/launchpad_cards.py`
  - `src/portfolio_alternatives_builder.py`
  - `scripts/core_mvp_validation_contract.py`
  - `docs/specs/block_4_diagnosis_v3_spec.md`
  - `docs/specs/candidate_launchpad_spec.md`
  - `docs/specs/portfolio_alternatives_builder_spec.md`

## Contract map table

| Source block | Field | Produced... | Consumed by next block... | Used in decision... | Gap |
| --- | --- | --- | --- | --- | --- |
| Block 3.4 Current Portfolio Stress Scorecard | `current_portfolio_stress_scorecard_v1.stress_diagnosis` | Yes. Built by `src/current_portfolio_stress_scorecard_block.py`; spec says the object contains headline, summary, confidence, and findings. | Yes. `src/block_4/evidence_extraction.py::_extract_scorecard_v1` emits signal `stress_diagnosis` from this field. | Yes, but as diagnosis evidence/support and confidence input, not as a standalone action. It supports `weak_crisis_resilience` in `src/block_4/problem_taxonomy.py` and can cap/lower confidence through `src/block_4/severity_confidence.py`. | No blocking gap found. Session 02 should verify behavior under the requested severe-recession scenarios. |
| Block 3.3 Hedge Gap | `hedge_gap_analysis_v1.summary.main_hedge_gap.offset_coverage_ratio` | Yes. Built by `src/hedge_gap_analysis_block.py` and summarized into scorecard. | Yes. `_extract_hedge_gap_v1` emits `offset_coverage_ratio`, and also `strong_offset_coverage` / `strong_hedge_offset` when ratio is strong. | Yes. Required for `weak_hedge_behavior`; also supports `weak_crisis_resilience` and can contradict equity-beta/stress-loss interpretations. | No field-level gap found. Behavior still needs Session 02 proof that weak hedge behavior activates only with Hedge Gap evidence, not labels alone. |
| Block 3.3 Hedge Gap | `hedge_gap_analysis_v1.summary.main_hedge_gap.protection_status` | Yes. Built by `src/hedge_gap_analysis_block.py`. | Yes. `_extract_hedge_gap_v1` emits `protection_status`. | Yes. Required for `weak_hedge_behavior`. | No field-level gap found. Scenario behavior remains for Session 02. |
| Block 3.3 / 3.4 Hedge Gap Summary | `hedge_gap_analysis_v1.summary.main_hedge_gap` and `current_portfolio_stress_scorecard_v1.hedge_gap_summary` | Yes. Hedge gap is produced by Block 3.3 and mirrored/summarized by Block 3.4. | Yes. `_extract_hedge_gap_v1` and `_extract_scorecard_v1` emit `main_hedge_gap`. | Yes. Supporting evidence for `weak_hedge_behavior`; also appears in key evidence copied into `problem_classification_v3.primary_diagnosis.key_evidence`. | No blocking gap found. Potential duplicate signal sources are deliberate provenance, not a found bug. |
| Block 3.4 Stress Scorecard | `current_portfolio_stress_scorecard_v1.worst_synthetic_scenario` | Yes. Built by `src/current_portfolio_stress_scorecard_block.py`. | Yes. `_extract_scorecard_v1` emits `worst_synthetic_scenario` and `immaterial_stress_loss` / `stress_loss_immaterial` when loss is not material. | Yes. Required for `weak_crisis_resilience`; immaterial loss acts as negative evidence for crisis/equity-beta interpretations. | No field-level gap found. Session 02 should verify severe recession and contradiction cases. |
| Block 3.4 Stress Scorecard | `current_portfolio_stress_scorecard_v1.worst_historical_scenario` | Yes. Built by `src/current_portfolio_stress_scorecard_block.py`. | Yes. `_extract_scorecard_v1` emits `worst_historical_scenario`. | Yes. Required for `weak_crisis_resilience`; supports drawdown diagnosis. | No field-level gap found. |
| Block 2.6 Portfolio Weakness Map | `block_2_6_portfolio_weakness_map.risk_types[]` | Yes. Produced by Portfolio X-Ray Block 2.6. | Yes. `_extract_block_2_6` emits signals named `block_2_6_<risk_type>` for material risk rows; examples include `block_2_6_recession_severe`, `block_2_6_rates_shock`, `block_2_6_credit_shock`, and `block_2_6_equity_shock`. | Yes. These signals support or are required by several diagnoses: rates, credit/liquidity, crisis resilience, volatility, drawdown, and equity beta. | No field-level gap found. Full behavior under rates shock and x-ray-vs-stress tension remains Session 02. |
| Block 2.4 Hidden Exposure | `block_2_4_hidden_exposure.alerts.*` | Yes. Produced by Portfolio X-Ray Block 2.4. | Yes. `_extract_block_2_4` maps alert ids to signals such as `hidden_equity_beta`, `duration_concentration_alert`, `credit_liquidity_risk_alert`, `correlation_concentration`, `weak_hedge_behavior_alert`, and `tail_risk_alert`. | Yes. These signals are required/supporting evidence for equity beta, duration, credit/liquidity, diversification, weak hedge, and tail-risk diagnoses. | No field-level gap found. Important boundary: weak hedge alert alone is not the full weak hedge diagnosis; Hedge Gap evidence is still required by taxonomy. |
| Block 2.5 Risk Budget View | `block_2_5_risk_budget_view.top1_rc_asset.rc_pct` | Yes. Produced by Portfolio X-Ray Block 2.5. | Partially. `_extract_block_2_5` emits `rc_top1_share` only. | Yes, as supporting evidence for `high_concentration`. | Partial gap: the handoff consumes top-1 risk-contribution share, not a full risk-budget table or top-3 RC field. This is not automatically blocking for current Session 01, but should be recorded as limited risk-budget coverage for Session 06/08. |
| Block 2.3 Factor Exposure | `block_2_3_factor_exposure.factor_betas_5y.betas.beta_eq` / `beta_rr` / `beta_credit` | Yes. Produced by Portfolio X-Ray Block 2.3. | Yes. `_extract_block_2_3` emits `beta_eq`, `beta_rr`, and `beta_credit`; legacy fallback can emit `beta_eq` / `beta_portfolio` if canonical block is unavailable. | Yes. Used in equity beta, rates/duration, and credit/liquidity diagnoses. | Partial gap: factor beta handoff exists, but broader factor exposure summaries are not consumed at field level by Block 4. No blocking gap for the requested canonical fields. |
| Block 2.2 Portfolio Metrics | `block_2_2_portfolio_metrics.return_risk_metrics`, drawdown, tail, benchmark, rolling, correlation fields | Yes. Produced by Portfolio X-Ray Block 2.2. | Yes. `_extract_block_2_2` emits `vol_annual`, `sharpe`, `sortino`, `cagr`, `max_drawdown`, `time_underwater`, `var_95`, `es_95`, `beta_portfolio`, `downside_beta`, `rolling_volatility`, `avg_pairwise_correlation`, and negative/counter signals. | Yes. Used across volatility, drawdown, tail risk, return/risk efficiency, diversification, and contradiction handling. | No field-level gap found. |
| Block 4 Evidence Extraction | `EvidenceSignal` rows with `source_block`, `source_artifact`, `evidence_path`, `confidence`, `raw_field_path` | Yes. Produced by `extract_evidence_signals`. | Yes. Consumed by `score_problems`, `build_diagnosis_evidence_bundle`, `prioritize_problems`, action mapping, and diagnosis builder. | Yes. These rows are the field-level bridge into primary/secondary diagnoses and key evidence. | No field-level gap found. This is backend audit metadata; product surface remains diagnosis-first. |
| Block 4 Diagnosis | `problem_classification_v3.primary_diagnosis` | Yes. Built by `src/block_4/diagnosis_builder.py::_build_primary_diagnosis`. | Yes. Consumed by Launchpad through action mapping/scoring context and by live validators; copied into user-facing diagnosis artifact. | Yes. This is the current portfolio diagnosis, but not a final rebalance decision. | No field-level gap found. |
| Block 4 Diagnosis | `problem_classification_v3.primary_diagnosis.diagnosis_id` / `root_cause` / `key_evidence` / `confidence` | Yes. Built from prioritized problem, scoring, and compact evidence refs. | Yes. Launchpad cards copy source diagnosis id and rationale; Builder later preserves source diagnosis id and test context. | Yes. Used to choose the next diagnostic step and card framing. | No field-level gap found. |
| Block 4 Diagnosis | `problem_classification_v3.next_diagnostic_step` | Yes. `_next_diagnostic_step` always returns a targeted hypothesis, reference comparison, or data-quality improvement object with `decision_boundary`. | Yes. `scripts/validate_block_4_live.py` passes it to `build_builder_prefill_from_launchpad_card`; Builder prefill preserves it when supplied. | Yes as workflow routing, not as action approval. It decides what kind of test/setup is safe next. | No field-level gap found. |
| Block 4 Diagnosis | `problem_classification_v3.success_criteria` | Yes. Derived from the action path. | Yes. Launchpad cards also emit success criteria; Builder prefill preserves card success criteria. | Yes as test-evaluation criteria. Not final decision by itself. | No field-level gap found. |
| Candidate Launchpad | `candidate_launchpad_v3.cards[].source_diagnosis_id` | Yes. `_build_card` and `_fallback_monitor_card` set it from the source problem/diagnosis. | Yes. `build_builder_prefill_from_launchpad_card` copies it into `source_diagnosis_id`. | Yes for traceability and safe setup; no final rebalance decision. | No field-level gap found. |
| Candidate Launchpad | `candidate_launchpad_v3.cards[].hypothesis_to_test` | Yes. `_hypothesis_to_test` builds it from action path and source problem. | Yes. Builder prefill copies it unchanged. | Yes as the test hypothesis that candidates/reference benchmarks must prove. | No field-level gap found. |
| Candidate Launchpad | `candidate_launchpad_v3.cards[].suggested_methods` / `default_method` | Yes. `_method_ids_for_card` and `_suggested_method_row` build method suggestions; reference benchmarks use Equal Weight and Risk Parity roles. | Yes. Builder prefill reads methods, chooses a suggested method, and preserves alternative/suggested method rows. | Yes for candidate setup availability only. It does not execute generation or recommend rebalance. | No field-level gap found. |
| Candidate Launchpad | `candidate_launchpad_v3.cards[].card_type` / `launch_status` | Yes. `_card_type` and `_launch_status` produce targeted, reference, or monitor/data statuses. | Yes. Builder prefill uses these to set `builder_mode` and `method_role`. | Yes for gating safe setup: data-quality/monitor cards block generation; reference cards remain references. | No field-level gap found. |
| Candidate Launchpad | `candidate_launchpad_v3.cards[].success_criteria` / `tradeoff_to_watch` / `when_to_skip` | Yes. Built in `launchpad_cards.py`. | Yes. Builder prefill copies these fields unchanged. | Yes as setup guardrails and evaluation criteria. Not a final action decision. | No field-level gap found. |
| Candidate Launchpad | `candidate_launchpad_v3.cards[].is_rebalance_recommendation` | Yes. Set to `false` for targeted and fallback monitor cards. Validators reject non-false values. | Yes. Builder prefill forces/preserves `is_rebalance_recommendation: false`. | Yes as a safety boundary: prevents pre-verdict rebalance interpretation. | No field-level gap found. |
| Candidate Launchpad | `candidate_launchpad_v3.cards[].decision_boundary` | Yes. Set to `DECISION_BOUNDARY_EN` in cards. Validators require text blocking rebalance interpretation. | Yes. Builder prefill copies it and validators check it. | Yes as workflow boundary: final action waits for Current vs Candidate Comparison and Decision Verdict. | No field-level gap found. |
| Candidate Launchpad / Builder | `candidate_generation_allowed` | Launchpad validators require cards not to set this to true; Builder prefill computes it from suggested method plus safe builder mode. | Yes. Builder prefill emits a boolean. Data-quality/monitor cards become false; targeted/reference setups may be true only as explicit UI permission. | Yes as generation gating. It is not automatic candidate generation and not a rebalance recommendation. | No field-level gap found. Note: Builder mode treats reference benchmark cards with methods as `guided_from_diagnosis`; tests/spec preserve their `reference_benchmark` method role, so this is naming noise rather than a contract break. |

## Key evidence from code/specs

- `src/block_4/evidence_extraction.py` is the main Block 2/3 -> Block 4 field bridge. It emits named `EvidenceSignal` objects with provenance fields and raw field paths.
- `src/block_4/problem_taxonomy.py` defines which signals are required, supporting, or negative evidence for each diagnosis. The weak hedge diagnosis requires both `offset_coverage_ratio` and `protection_status`, so labels/alerts alone should not activate it.
- `src/block_4/diagnosis_builder.py` always emits `primary_diagnosis`, `next_diagnostic_step`, and `success_criteria`; for mixed/acceptable outcomes it routes to reference comparison, and for data-quality blockers it routes to data-quality improvement.
- `src/block_4/launchpad_cards.py` builds V3 cards with `source_diagnosis_id`, `hypothesis_to_test`, `launch_status`, `success_criteria`, `tradeoff_to_watch`, `when_to_skip`, `decision_boundary`, and `is_rebalance_recommendation: false`.
- `src/portfolio_alternatives_builder.py::build_builder_prefill_from_launchpad_card` is a pure prefill helper. It copies Launchpad context and does not run the factory, optimizer, subprocesses, or weight writes.
- `scripts/core_mvp_validation_contract.py` validates the no-rebalance boundary and Builder prefill fields, including `decision_boundary`, `is_rebalance_recommendation`, and `candidate_generation_allowed` constraints.

## Gaps and follow-up items

1. **Risk budget coverage is partial.** Block 4 consumes `block_2_5_risk_budget_view.top1_rc_asset.rc_pct` as `rc_top1_share`, but this audit did not find broad consumption of a full risk-budget table or top-3 risk contribution. Record as a minor coverage gap unless a spec requires broader risk-budget diagnosis now.
2. **Factor exposure coverage is focused.** Block 4 consumes factor betas (`beta_eq`, `beta_rr`, `beta_credit`) but not a broad factor exposure summary. This is adequate for current diagnosis taxonomy fields found in code, but should be listed in Session 06 coverage.
3. **Behavior still needs proof.** Field mapping exists, but Session 02 must still prove behavior for severe recession, rates shock, weak hedge gating, missing evidence confidence, and X-Ray-vs-stress contradiction.
4. **Reference-card Builder naming is slightly broad.** Reference benchmark cards with methods become `builder_mode: guided_from_diagnosis` while preserving `card_type: reference_benchmark_test` and `method_role: reference_benchmark`. Existing specs/tests accept the reference role; no Session 01 blocker found.

## Session 01 verdict

Session 01 is **closed with minor documented coverage gaps**.

The field-level handoff exists from Block 3 stress and Block 2 X-Ray evidence into Block 4 signals, from Block 4 diagnosis into Launchpad cards, and from selected Launchpad cards into Builder prefill. The main safety boundary is present: cards and prefill preserve `is_rebalance_recommendation: false`, carry `decision_boundary`, and do not execute candidate generation automatically.

This does not close Session 02, because Session 02 is behavioral and must prove the requested scenarios with tests/source inspection.
