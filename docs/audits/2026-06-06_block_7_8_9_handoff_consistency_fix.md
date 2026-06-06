# Block 7-8-9 Handoff Consistency Fix

Date: 2026-06-06

## Scope

Fix the contract mismatch discovered after the FRED/factor blocker was cleared:

`CandidateSetup -> factory execution -> candidate_generation.json -> current_vs_candidate.json -> decision_verdict.json -> ai_commentary_context.json`

No optimizer formulas, FRED/factor logic, UI/Builder features, or product philosophy were changed.

## Root Cause

Block 7 delegated one candidate to `run_candidate_factory.py` with the demo config, but then read
`candidate_factory_run.json` from the legacy default `Main portfolio/` location.

Demo configs write factory summaries under their config-isolated `output_dir_final`, for example:

- `output/demo_portfolios/balanced/final/candidate_factory_run.json`
- `output/demo_portfolios/equity_heavy/final/candidate_factory_run.json`
- `output/demo_portfolios/defensive_rates_sensitive/final/candidate_factory_run.json`

Block 8 already loaded the factory run from the config output directory, so it could build a fresh
comparison while Block 7 still marked candidate generation as failed. That produced the invalid state:

- `candidate_generation.generation_status: failed`
- `candidate.weights: null`
- `current_vs_candidate.comparison_status: available`
- `decision_verdict.verdict_reason_id: candidate_generation_failed`

## Fix Summary

Changed files:

- `scripts/generate_candidate_from_builder_setup.py`
  - Resolves the default `candidate_factory_run.json` path from the same config used by the factory.
  - Preserves legacy `Main portfolio/candidate_factory_run.json` fallback when no config is supplied.
- `src/candidate_generation.py`
  - Adds contract guards: `generated` requires non-empty weights and `can_compare=true`; failed/infeasible requires no weights and `can_compare=false`.
  - Adds `handoff_to_comparison.reason`.
- `src/current_vs_candidate.py`
  - Adds Block 7 consistency guard: normal available comparison requires generated candidate, weights, `can_compare=true`, and matching candidate id.
  - Failed/infeasible or invalid Block 7 evidence now produces `comparison_status: blocked_by_candidate_generation`.
- `src/decision_verdict.py`
  - Failed/infeasible candidate generation now yields explicit `candidate_failed_or_infeasible`.
  - Successful generated candidates with available comparison no longer fall through to `candidate_generation_failed`.
- `src/ai_commentary_context.py`
  - Adds a `pipeline_inconsistency` warning/top-level flag if future artifacts ever say candidate failed while comparison is available.
- Focused tests updated for the stricter Block 7 source-of-truth contract.

## Verification

Focused tests:

```powershell
$cg = Get-ChildItem tests -Filter 'test_candidate_generation_*.py' | ForEach-Object { $_.FullName }
.\.venv\Scripts\python.exe -m pytest @cg -q
# 19 passed

$cv = Get-ChildItem tests -Filter 'test_current_vs_candidate*.py' | ForEach-Object { $_.FullName }
.\.venv\Scripts\python.exe -m pytest @cv -q
# 12 passed

$dv = Get-ChildItem tests -Filter 'test_decision_verdict*.py' | ForEach-Object { $_.FullName }
.\.venv\Scripts\python.exe -m pytest @dv -q
# 16 passed

.\.venv\Scripts\python.exe -m pytest tests\test_ai_commentary_context.py -q
# 14 passed

.\.venv\Scripts\python.exe -m pytest tests\test_blocks_5_to_9_vertical_flow.py tests\test_reference_benchmark_vertical_flow.py -q
# 2 passed
```

Docs and factor cache:

```powershell
.\.venv\Scripts\python.exe scripts\verify_docs.py
# docs verification: OK

.\.venv\Scripts\python.exe scripts\warm_factor_cache.py --check-only --start 2007-01-01 --end 2026-06-05
# status: ok; cache_status: valid; missing_series: []; full_factor_matrix_available: true; demo_safe: true
```

## Three-Portfolio Standard Rerun Results

Commands:

```powershell
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\balanced.yml --method equal_weight --factory-execution-mode standard --force-candidate
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\equity_heavy.yml --method equal_weight --factory-execution-mode standard --force-candidate
.\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --config config\demo_portfolios\defensive_rates_sensitive.yml --method equal_weight --factory-execution-mode standard --force-candidate
```

| Fixture | Block 7 | Weights | Block 8 | Improvements / Worsening | Verdict | AI contradiction |
| --- | --- | ---: | --- | --- | --- | --- |
| balanced | `generated` | 8 | `available` | 10 / 9 | `rebalance_to_selected_candidate` (`rebalance_when_material`) | none |
| equity_heavy | `generated` | 6 | `available` | 14 / 5 | `rebalance_to_selected_candidate` (`rebalance_when_material`) | none |
| defensive_rates_sensitive | `generated` | 8 | `available` | 12 / 6 | `rebalance_to_selected_candidate` (`rebalance_when_material`) | none |

All three runs are fresh, config-isolated, and no longer contain the contradiction
“candidate failed but comparison available.”

## Final Readiness Status

`FULL_DEMO_MVP_READY`

Rationale:

- FRED/factor cache remains demo-safe.
- Block 7 now correctly ingests the successful fresh factory output and writes generated candidate weights.
- Block 8 normal comparison requires valid Block 7 generated-candidate evidence.
- Block 9 no longer reports `candidate_generation_failed` when a fresh generated candidate is compared.
- AI Commentary grounding has no candidate-failed/comparison-available contradiction and now has a guard for future inconsistency.
- The three primary demo fixtures produce understandable `what_improved` / `what_worsened` and a verdict from consistent evidence.

Residual caveats for operator narration, not blockers to this readiness gate:

- The verdicts are diagnostic decision-support verdicts, not trade execution instructions.
- The defensive fixture still tests an Equal Weight concentration hypothesis rather than a pure rates-duration candidate; this is acceptable as a diagnostic hypothesis but should be described plainly in demos.
