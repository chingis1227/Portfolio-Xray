# Blocks 3-5 Handoff Session 02 — Block 3 -> Block 4 Behavior Audit

Date: 2026-06-04
Scope: read-only behavior audit for `Stress evidence -> Investment diagnosis`.
Plan: `docs/exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md`.

## Question

Does Block 3 stress evidence actually change or constrain Block 4 behavior, not merely exist as fields...

Required scenarios:

1. severe recession plus weak offset coverage;
2. rates shock plus duration concentration;
3. weak hedge behavior only when Hedge Gap evidence exists or confirms it;
4. missing or partial stress evidence lowers confidence or blocks action;
5. X-Ray-versus-stress contradiction produces mixed evidence / no immediate rebalance, not a forced rebalance.

## Commands Run

From repository root `D:\Desktop\CURSOR TULA DIAGNOSTICS`.

### Block 4 behavior baseline

Command:

    .\.venv\Scripts\python.exe -m pytest tests/test_block_4_evidence_extraction.py tests/test_block_4_diagnosis_builder.py tests/test_block_4_problem_prioritization.py tests/test_block_4_problem_scoring.py -q

Result:

    25 passed in 5.58s

### Stress / Hedge Gap baseline

The plan's literal command uses Unix-style globs:

    .\.venv\Scripts\python.exe -m pytest tests/test_stress_*.py tests/test_hedge_gap*.py -q

On Windows PowerShell, `pytest` did not expand the globs and returned:

    no tests ran in 0.01s
    ERROR: file or directory not found: tests/test_stress_*.py

I reran the same intended group by expanding the file list in PowerShell:

    $files = Get-ChildItem -LiteralPath tests -File | Where-Object { $_.Name -like 'test_stress_*.py' -or $_.Name -like 'test_hedge_gap*.py' } | ForEach-Object { $_.FullName }
    .\.venv\Scripts\python.exe -m pytest @files -q

Result:

    1 failed, 240 passed in 45.43s

Failure:

    tests/test_stress_hedge_gap_contract.py::test_stress_commentary_states_hedge_gap_not_applicable
    AssertionError: assert 'Hedge gap: not applicable' in generated stress commentary text

Interpretation: this is a generated commentary wording regression in the Stress Lab text surface. It is not direct evidence of a broken Block 3 -> Block 4 JSON handoff, but it is still a real failing stress/hedge-gap test and should be tracked before a final readiness verdict.

### Additional behavior checks used for this audit

These are not part of the minimum Session 02 baseline command, but they directly cover the requested behavior scenarios.

Command:

    .\.venv\Scripts\python.exe -m pytest tests/test_block_4_v2_archetype_fixtures.py tests/test_block_4_no_trade_gate.py tests/test_block_4_severity_confidence.py -q

Result:

    28 passed in 4.23s

Command:

    .\.venv\Scripts\python.exe -m pytest tests/test_hedge_gap_analysis_v1_contract.py::test_recession_severe_protection_row_when_evidence_present tests/test_hedge_gap_analysis_v1_contract.py::test_main_hedge_gap_can_select_recession_severe_when_weakest_offset -q

Result:

    2 passed in 2.77s

## Scenario Findings

| Scenario | Status | Evidence | Interpretation |
| --- | --- | --- | --- |
| Severe recession plus weak offset coverage | Covered with a gap | `tests/test_hedge_gap_analysis_v1_contract.py::test_recession_severe_protection_row_when_evidence_present` and `::test_main_hedge_gap_can_select_recession_severe_when_weakest_offset` prove `recession_severe` can become the weakest Hedge Gap area. `src/block_4/problem_taxonomy.py` maps `recession_severe` to `weak_crisis_resilience` and includes `offset_coverage_ratio` / `block_2_6_recession_severe` as supporting evidence. `tests/test_block_4_problem_scoring.py::test_golden_fixture_activates_stress_and_concentration_problems` proves stress-confirmed `weak_crisis_resilience` activates. | Behavior is present. Gap: there is no single end-to-end Block 4 test whose fixture explicitly combines `recession_severe` as the main weak-offset scenario and asserts the final primary diagnosis. Current proof is split across Hedge Gap unit tests plus Block 4 taxonomy/scoring tests. |
| Rates shock plus duration concentration | Covered | `tests/block_4_fixtures.py::archetype_duration_heavy_bonds` combines a `duration_concentration` alert, `block_2_6` `rates_shock`, and `rates_shock` stress loss. `tests/test_block_4_v2_archetype_fixtures.py::test_block_4_archetype_end_to_end` passes for all archetypes. `src/block_4/problem_taxonomy.py` defines `poor_rates_up_behavior` and `duration_rates_vulnerability`; `src/block_4/problem_taxonomy.py` root-cause rule `duration_over_rates_behavior` prefers structural duration when present. | Stress/X-Ray behavior is connected: rates stress plus duration evidence drives a rates/duration diagnosis and may proceed to Launchpad. |
| Weak hedge behavior only when Hedge Gap evidence exists / confirms it | Mostly covered | `src/block_4/problem_scoring.py` requires `offset_coverage_ratio` and/or `protection_status` for `weak_hedge_behavior`. `tests/test_block_4_severity_confidence.py::test_golden_fixture_assigns_severity_and_confidence` asserts `weak_hedge_behavior` is stress-confirmed. `tests/test_block_4_problem_prioritization.py::test_golden_fixture_elevates_crisis_resilience_over_hedge_behavior` and `tests/test_block_4_v2_archetype_fixtures.py::test_weak_hedge_elevates_crisis_over_labeled_hedge` prove weak hedge is demoted behind the stress-confirmed root cause. | Good guardrail: weak hedge is not treated as the root diagnosis when the broader stress root cause dominates. Gap: there is no explicit negative test named “no Hedge Gap evidence -> weak_hedge_behavior not actionable”; current proof is by required-signal logic and data-quality/low-confidence tests. |
| Missing or partial stress evidence lowers confidence or blocks action | Covered | `src/current_portfolio_stress_scorecard_block.py::_derive_diagnosis_confidence` returns `unavailable`, `low`, or `medium` when scorecard/hedge-gap/coverage evidence is missing or partial. `tests/test_block_4_problem_scoring.py::test_data_trust_failure_activates_evidence_quality_problem`, `tests/test_block_4_problem_prioritization.py::test_data_quality_problem_is_sole_primary`, `tests/test_block_4_diagnosis_builder.py::test_data_quality_diagnosis_status_partial_or_unavailable`, and `tests/test_block_4_no_trade_gate.py::test_data_quality_blocks_action` all pass. | Missing evidence becomes data-quality / do-not-act behavior rather than a false rebalance path. |
| X-Ray vs stress contradiction gives mixed evidence, not forced rebalance | Covered | `src/block_4/evidence_extraction.py` emits `low_stress_loss_with_high_vol` when X-Ray volatility is high but worst synthetic stress loss is mild. `tests/test_block_4_problem_scoring.py::test_conflicting_signals_activate_conflict_problem`, `tests/test_block_4_problem_prioritization.py::test_conflicting_signals_primary_blocks_secondaries`, `tests/test_block_4_no_trade_gate.py::test_conflicting_signals_block_action`, and `tests/test_block_4_v2_archetype_fixtures.py::test_insufficient_and_conflict_suppress_launchpad` pass. | Contradiction is routed to `mixed_evidence_no_action` and `OUTCOME_DO_NOT_ACT`, with “No immediate rebalance” wording. |

## Source Behavior Notes

- `src/block_4/evidence_extraction.py` extracts Block 3 Hedge Gap v1 into `offset_coverage_ratio`, `protection_status`, `main_hedge_gap`, `rates_scenario_loss`, and `rates_shock_stress`.
- `src/block_4/problem_scoring.py` treats those signals as stress signals and uses them to set `stress_confirmation` to `confirmed`, `pre_stress_only`, `contradicted`, or `unavailable`.
- `src/block_4/problem_taxonomy.py` maps stress scenarios to problem ids and has root-cause elevation rules that demote weaker symptoms when stress-confirmed root causes dominate.
- `src/block_4/no_trade_gate.py` blocks action on data-quality and mixed-evidence outcomes rather than implying a rebalance.

## Verdict for Session 02

Status: closed with minor coverage gaps and one unrelated-but-real failing stress commentary test.

Behavior verdict: Block 3 stress evidence does affect and constrain Block 4 behavior for the requested scenarios. It changes activation, confidence, prioritization, and no-trade gating. The strongest proof is the passing Block 4 baseline (`25 passed`) plus archetype/no-trade/severity checks (`28 passed`) plus targeted Hedge Gap recession checks (`2 passed`).

Gaps to carry forward:

1. The full stress/hedge-gap group has one failing commentary wording test. This should be treated as a stress text-surface regression, not as a proven JSON handoff break.
2. Severe recession + weak offset coverage is proven by split tests, but not by one explicit end-to-end Block 4 fixture whose main Hedge Gap scenario is `recession_severe` and whose final primary diagnosis is asserted.
3. Weak hedge gating is strongly implied by required-signal logic and positive/demotion tests, but a future post-audit plan should add an explicit negative test: no Hedge Gap v1 evidence means `weak_hedge_behavior` must not become an actionable Launchpad-driving diagnosis.

No source code, product docs, generated portfolio artifacts, candidates, optimizer outputs, PDFs, or weights were changed during this session.
