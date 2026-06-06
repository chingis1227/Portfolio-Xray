# Three-Portfolio Vertical Demo Rerun After FRED Fix

Date: 2026-06-06

## Scope

Rerun the canonical Blocks 5-9 vertical product demo after the FRED / factor cache blocker was fixed.
The audit checks product quality, not only file existence:

`Diagnosis -> Hypothesis -> Builder Setup -> Candidate -> Comparison -> Verdict -> AI Commentary grounding`

Allowed readiness statuses: `FULL_DEMO_MVP_READY`, `DEMO_READY_WITH_LIMITATIONS`, `NOT_READY_BLOCKED`.

## Commands

Initial canonical runs, using the script default `fast` candidate factory mode:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\balanced.yml --method equal_weight --force-candidate
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\equity_heavy.yml --method equal_weight --force-candidate
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\defensive_rates_sensitive.yml --method equal_weight --force-candidate
```

Because `fast` mode produced weights-only factory steps and left Block 8 unavailable, the audit also ran the best supported fresh comparison mode:

```powershell
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\balanced.yml --method equal_weight --force-candidate --factory-execution-mode standard
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\equity_heavy.yml --method equal_weight --force-candidate --factory-execution-mode standard
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\defensive_rates_sensitive.yml --method equal_weight --force-candidate --factory-execution-mode standard
```

Factor cache gate:

```powershell
.\.venv\Scripts\python.exe scripts\warm_factor_cache.py --check-only --start 2007-01-01 --end 2026-06-05
```

Log files:

- `output/demo_portfolios/_logs/2026-06-06_vertical_balanced.log`
- `output/demo_portfolios/_logs/2026-06-06_vertical_equity_heavy.log`
- `output/demo_portfolios/_logs/2026-06-06_vertical_defensive_rates_sensitive.log`
- `output/demo_portfolios/_logs/2026-06-06_vertical_balanced_standard_retry.log`
- `output/demo_portfolios/_logs/2026-06-06_vertical_equity_heavy_standard_retry.log`
- `output/demo_portfolios/_logs/2026-06-06_vertical_defensive_rates_sensitive_standard_retry.log`

## Cross-Run Findings

### FRED / factor cache status

PASS for the prior FRED blocker.

- `warm_factor_cache.py --check-only --start 2007-01-01 --end 2026-06-05`: `status: ok`, `source_used: cache_hit`, `cache_status: valid`, `missing_series: []`, `full_factor_matrix_available: true`, `demo_safe: true`.
- The vertical-flow logs contained no `FRED`, `timeout`, `warning`, or `ERROR` matches.
- Each subject `stress_report.json` includes `factor_diagnostics_meta.factor_attribution_scope: multi_factor`, `missing_factors: []`, and factor load diagnostics with `source_used: cache_hit` / `cache_status: valid` for the FRED-backed factors.
- Stress reports still have `status: warning` and low trust because historical episodes such as dotcom / 2008 are unavailable for these ETF histories. That is a data-history limitation, not the prior FRED timeout blocker.

### Output chain freshness

PASS for artifact freshness and config isolation.

For all three fixtures, the following files were refreshed in the fixture-specific output tree during the standard rerun:

- `analysis_subject/problem_classification.json`
- `analysis_subject/candidate_launchpad.json`
- `analysis_subject/portfolio_alternatives_builder.json`
- `candidate_generation.json`
- `candidate_comparison.json`
- `current_vs_candidate.json`
- `decision_verdict.json`
- `ai_commentary_context.json`

`candidate_factory_run.json` used `factory_profile_id: explicit_list`, `options.execution_mode: standard`, `force: true`, and one `equal_weight` step with `status: succeeded`, `execution_action: lightweight_report_built`, `phases_completed: [weights, report]`, `freshness_status: fresh`, and matching config fingerprints.

### Main product blocker discovered

FAIL for `FULL_DEMO_MVP_READY`.

The standard reruns produce meaningful Block 8 comparisons, but Block 7 still writes:

- `candidate_generation.generation_status: failed`
- `candidate.status: failed`
- `candidate.weights: null`
- `failure_reason: factory_run_json_missing_or_invalid; returncode=0; ... Factory run summary: ...candidate_factory_run.json`

This contradicts the fresh factory evidence and the available Block 8 comparison. As a result, Block 9 writes:

- `verdict_id: evidence_insufficient`
- `verdict_reason_id: candidate_generation_failed`
- rationale: `Candidate generation did not produce comparable weights, so no action verdict can be supported.`

This is not client-ready because the user sees usable improvements/worsening in Block 8 but the verdict says the candidate was not comparable.

## Portfolio 1 - Balanced Diversified

Fixture: `config/demo_portfolios/balanced.yml`
Output root: `output/demo_portfolios/balanced/final/`

### Run status

Completed with exit code 0. Product status: weak demo case / blocked for full readiness because Block 7 and Block 9 contradict Block 8.

### FRED / factor status

- No FRED timeout warnings in logs.
- `factor_attribution_scope: multi_factor`.
- `missing_factors: []`.
- Factor load diagnostics: `source_used: cache_hit`, `cache_status: valid`.

### Primary diagnosis

- `diagnosis_id: mixed_evidence_no_action`
- Label: `Mixed evidence - reference test available`
- Thesis: no dominant actionable problem is confirmed; evidence is usable but mixed, so a rebalance is not justified yet.
- Confidence: low.
- Supporting symptoms: poor rates-up behavior and high tail risk.

### Launchpad card / hypothesis

- Selected card: `launchpad_01_compare_against_simple_benchmark`
- Card type: `reference_benchmark_test`
- Suggested method: `equal_weight`, role `reference_benchmark`
- Boundary: not a rebalance recommendation; decision only after comparison and verdict.
- Hypothesis: use Equal Weight only as a simple reference to clarify whether the mixed diagnosis is material.

### Builder setup

- Status: `ok`
- Method: `equal_weight`
- Method role: `reference_benchmark`
- Mode: `capped`
- Constraint preset: `basic_reference`
- `max_asset_weight: null`, `min_asset_weight: null`
- Success criteria: create a transparent reference point and clarify whether the diagnosis is material.

### Candidate generation

- Factory step succeeded and was fresh.
- Block 7 candidate status: `failed`.
- Candidate weights in `candidate_generation.json`: `null`.
- Candidate is correctly marked as not a recommendation.
- Failure reason says factory JSON was missing or invalid even though `candidate_factory_run.json` exists and is successful.

### Current vs Candidate

Comparison status: `available` across 20 dimensions.

What improved:

- Worst stress loss improved by about +3.1 percentage points and is material.
- Largest holding weight, top-3 holding weight, weight HHI, top-1 risk contribution, top-3 risk contribution, and risk contribution HHI improved materially.
- Portfolio beta / equity exposure improved materially by the configured thresholds.

What worsened:

- Return fell by about -0.6 percentage points and is material.
- Max drawdown and Sharpe worsened slightly but were not material.
- Rates / inflation / credit / USD / commodity factor absolute exposures worsened, mostly not material.

Neutral / unavailable:

- Turnover is unavailable because Block 8 says baseline or candidate weights are missing.
- Transaction-cost assumption exists at 10 bps, but estimated cost is unavailable.
- Success criteria are `not_evaluated` because the reference-benchmark criteria are not mapped to available metrics.

### Decision Verdict

- `verdict_id: evidence_insufficient`
- `verdict_reason_id: candidate_generation_failed`
- Rationale: candidate generation did not produce comparable weights, so no action verdict can be supported.

This verdict is inconsistent with the available comparison. It is conservative, but it needs developer explanation to reconcile with Block 8.

### AI Commentary grounding

Partially useful, not client-ready.

Grounding has good source citations for diagnosis, stress behavior, hypothesis, improvements, worsening, and verdict. However, it also says the candidate status is failed while the comparison is available. That backend inconsistency leaks into the explanation and would confuse an advisor/client.

### Human-readable explanation

This balanced portfolio does not show one clear actionable problem; the system sees mixed evidence and recommends using Equal Weight only as a reference benchmark. The Equal Weight comparison suggests concentration and stress loss could improve, but expected return would fall. Some rates and inflation factor exposures would also get worse. Because turnover and transaction-cost impact are unavailable, the comparison is incomplete. The final verdict says evidence is insufficient because candidate generation failed, even though Block 8 produced a comparison. This case is not ready as a polished client demo without explaining the backend inconsistency.

### Final assessment

Weak demo case. Balanced is directionally useful, but not `FULL_DEMO_MVP_READY` because the verdict is not consistent with the available comparison and turnover/cost are unavailable.

## Portfolio 2 - Equity-Heavy / Concentrated

Fixture: `config/demo_portfolios/equity_heavy.yml`
Output root: `output/demo_portfolios/equity_heavy/final/`

### Run status

Completed with exit code 0. Product status: weak demo case / blocked for full readiness because Block 7 and Block 9 contradict Block 8.

### FRED / factor status

- No FRED timeout warnings in logs.
- `factor_attribution_scope: multi_factor`.
- `missing_factors: []`.
- Factor load diagnostics: `source_used: cache_hit`, `cache_status: valid`.

### Primary diagnosis

- `diagnosis_id: mixed_evidence_no_action`
- Label: `Mixed evidence - reference test available`
- Thesis: no dominant actionable problem is confirmed; evidence is usable but mixed, so a rebalance is not justified yet.
- Confidence: low.
- Supporting symptoms: high tail risk, high equity beta, and high volatility.

This is understandable but weaker than expected for a concentrated equity-heavy fixture. The system does see equity/tail-risk evidence, but it keeps the primary outcome as mixed evidence / no immediate action.

### Launchpad card / hypothesis

- Selected card: `launchpad_01_compare_against_simple_benchmark`
- Card type: `reference_benchmark_test`
- Suggested method: `equal_weight`, role `reference_benchmark`
- Boundary: not a rebalance recommendation.
- Hypothesis: use Equal Weight as a reference to clarify whether the mixed diagnosis is material.

### Builder setup

- Status: `ok`
- Method: `equal_weight`
- Method role: `reference_benchmark`
- Mode: `capped`
- Constraint preset: `basic_reference`
- `max_asset_weight: null`, `min_asset_weight: null`
- Success criteria: create a transparent reference point and clarify diagnosis materiality.

### Candidate generation

- Factory step succeeded and was fresh.
- Block 7 candidate status: `failed`.
- Candidate weights in `candidate_generation.json`: `null`.
- Candidate is not presented as a recommendation.
- Failure reason again says factory JSON was missing or invalid despite a successful factory run.

### Current vs Candidate

Comparison status: `available` across 20 dimensions.

What improved:

- Volatility improved by about -3.1 percentage points and is material.
- Max drawdown improved by about +4.4 percentage points and is material.
- Worst stress loss improved by about +10.5 percentage points and is material.
- Largest holding, top-3 holdings, weight HHI, and largest risk contribution improved materially.

What worsened:

- Return fell by about -2.7 percentage points and is material.
- Rates, inflation, USD, and commodity factor absolute exposures worsened, mostly not material.

Neutral / unavailable:

- Turnover is unavailable due baseline/candidate weights missing in Block 8 practicality.
- Estimated transaction cost is unavailable.
- Success criteria are `not_evaluated` because the reference-benchmark criteria are not mapped.

### Decision Verdict

- `verdict_id: evidence_insufficient`
- `verdict_reason_id: candidate_generation_failed`
- Rationale: candidate generation did not produce comparable weights, so no action verdict can be supported.

The verdict is not consistent with the meaningful comparison metrics. It blocks the client-ready story.

### AI Commentary grounding

Partially useful, not client-ready.

It can cite the strong stress/concentration improvements and the return give-up, but it also cites candidate status `failed` and says the verdict is evidence-insufficient because generation failed. This is a backend leakage/conflict.

### Human-readable explanation

This equity-heavy portfolio shows high tail risk, high equity beta, and high volatility as supporting concerns, but the system still frames the primary diagnosis as mixed evidence rather than a clear rebalance trigger. The Equal Weight reference comparison would reduce volatility, drawdown, stress loss, and concentration. The trade-off is a material expected-return reduction. Turnover and transaction cost are not available, so the execution burden cannot be judged. The formal verdict says evidence is insufficient because candidate generation failed, even though comparison metrics are present. This needs a code/contract fix before it can be shown as a clean demo.

### Final assessment

Weak demo case. It is the strongest comparison story, but not full-ready because the primary diagnosis is conservative/mixed and the verdict contradicts Block 8.

## Portfolio 3 - Defensive / Bond-Heavy / Rates-Sensitive

Fixture: `config/demo_portfolios/defensive_rates_sensitive.yml`
Output root: `output/demo_portfolios/defensive_rates_sensitive/final/`

### Run status

Completed with exit code 0. Product status: weak demo case / blocked for full readiness because Block 7 and Block 9 contradict Block 8.

### FRED / factor status

- No FRED timeout warnings in logs.
- `factor_attribution_scope: multi_factor`.
- `missing_factors: []`.
- Factor load diagnostics: `source_used: cache_hit`, `cache_status: valid`.

### Primary diagnosis

- `diagnosis_id: weak_crisis_resilience`
- Label: `Weak crisis resilience`
- Thesis: offset coverage ratio is 0.00 in the main hedge-gap scenario.
- Confidence: high.
- Supporting symptom: poor rates-up behavior, high severity / medium confidence.
- Stress behavior: worst synthetic stress is `rates_shock` at about -11.9%; worst historical drawdown is 2022 at about -15.7%; main hedge gap is rates-up shock protection.

This is the best diagnosis of the three because it clearly identifies the rates-sensitive issue.

### Launchpad card / hypothesis

- Selected card: `launchpad_03_reduce_concentration`
- Card type: `targeted_hypothesis_test`
- Suggested method: `equal_weight`, role `targeted_hypothesis`
- Boundary: not a rebalance recommendation.
- Hypothesis: test whether reducing concentration improves the concentration problem enough to beat the current portfolio on success criteria.

The selected card is not perfectly aligned with the primary rates/crisis diagnosis: it tests concentration rather than a direct duration/rates hypothesis. That is acceptable as a diagnostic test only if stated clearly, but it weakens demo clarity.

### Builder setup

- Status: `ok`
- Method: `equal_weight`
- Method role: `targeted_candidate_method`
- Mode: `capped`
- Constraint preset: `basic_reference`
- `max_asset_weight: 0.15`, `min_asset_weight: 0.0`
- Success criteria: lower relevant concentration subtype and confirm top-1/top-3 risk contribution falls.

### Candidate generation

- Factory step succeeded and was fresh.
- Block 7 candidate status: `failed`.
- Candidate weights in `candidate_generation.json`: `null`.
- Candidate is not presented as a recommendation.
- Failure reason again says factory JSON was missing or invalid despite a successful factory run.

### Current vs Candidate

Comparison status: `available` across 20 dimensions.

What improved:

- Return improved by about +2.2 percentage points and is material.
- Sharpe improved by about +0.282 and is material.
- Worst stress loss improved by about +1.5 percentage points and is material.
- Largest holding, top-3 holdings, weight HHI, and largest risk contribution improved materially.

What worsened:

- Volatility worsened by about +0.7 percentage points and is material.
- Portfolio beta exposure worsened by about +0.094 and is material.
- Max drawdown worsened slightly but was not material.
- Equity / USD / commodity factor absolute exposures worsened, mostly not material.

Neutral / unavailable:

- Turnover is unavailable due baseline/candidate weights missing in Block 8 practicality.
- Estimated transaction cost is unavailable.
- Success criteria are `met` for the mapped risk-contribution concentration metric.

### Decision Verdict

- `verdict_id: evidence_insufficient`
- `verdict_reason_id: candidate_generation_failed`
- Rationale: candidate generation did not produce comparable weights, so no action verdict can be supported.

The verdict is not consistent with the comparison and success criteria. This is the clearest readiness blocker.

### AI Commentary grounding

Partially useful, not client-ready.

AI grounding has a coherent rates/crisis diagnosis and cites meaningful improvements/worsening. But it also says the candidate failed and the verdict is evidence-insufficient due candidate-generation failure. This is confusing and leaks backend state.

### Human-readable explanation

This defensive portfolio has a clear rates/crisis problem: the stress test says the main vulnerability is rates-up shock protection, with no offset coverage in the main hedge-gap scenario. The Equal Weight test selected by the Launchpad mainly checks concentration, not duration directly, so the hypothesis is only partly aligned with the diagnosis. The comparison says the candidate could improve return, Sharpe, stress loss, and concentration. It would also increase volatility and portfolio beta exposure. The formal success criteria for concentration are met, but turnover and transaction cost are unavailable. The verdict still says evidence is insufficient because candidate generation failed, so this cannot be presented as a clean recommendation or no-trade story.

### Final assessment

Weak demo case. It has the best primary diagnosis, but the selected hypothesis is only partly aligned and the final verdict contradicts the available comparison.

## Final Readiness Verdict

`DEMO_READY_WITH_LIMITATIONS`

Do not promote to `FULL_DEMO_MVP_READY` yet.

### Why not FULL_DEMO_MVP_READY

- FRED/factor blocker appears closed for this demo gate.
- Three fixture chains are fresh and config-isolated.
- Block 8 now provides meaningful `what_improved` and `what_worsened` under `standard` mode.
- But Block 7 still records `candidate_generation: failed` and `weights: null` even when the factory step is fresh and successful.
- Block 9 uses that Block 7 failure and writes `evidence_insufficient`, so the verdict is not consistent with the comparison.
- Turnover / transaction cost remain unavailable in all three comparisons.
- AI Commentary grounding can cite the evidence, but it exposes the backend conflict and is not clean client-ready language.
- The defensive fixture has a good rates-sensitive diagnosis, but the selected Launchpad card tests concentration rather than directly testing duration/rates sensitivity.

### Blockers / next actions before FULL_DEMO_MVP_READY

1. Fix the Block 7 adapter contract so a successful fresh factory run is accepted and `candidate_generation.json` either records comparable weights or clearly records why weights are intentionally not copied while still allowing verdict logic to use the successful candidate evidence.
2. Recompute Block 9 from the same evidence used by Block 8 so `decision_verdict.json` is consistent with `current_vs_candidate.json`.
3. Restore or explain turnover calculation from baseline/current weights and candidate weights; do not leave execution burden unavailable in the full demo.
4. Improve AI Commentary grounding text so it does not say both “candidate failed” and “comparison available” without an explicit reconciliation.
5. Consider selecting a rates/duration-aligned Launchpad card for the defensive fixture, or make the concentration hypothesis explicitly secondary.
6. Rerun the same three fixtures after the contract fix and require `candidate_generation`, `current_vs_candidate`, `decision_verdict`, and `ai_commentary_context` to tell the same story.

## Bottom Line

The FRED blocker is closed for full demo purposes. The product output is stronger than the previous gate because Block 8 now contains meaningful improvement and deterioration evidence. However, the vertical product chain is still not fully demo-ready because Candidate Generation and Decision Verdict do not agree with the available comparison evidence. A client can understand the diagnosis and trade-offs, but still needs a developer to explain why the final verdict says evidence is insufficient after a successful comparison. That fails the `FULL_DEMO_MVP_READY` bar.
