# Stress Lab Layer Specification

Status: active source-of-truth for Block 3 (Stress Test Lab) implementation boundary.

This document maps sub-blocks 3.1 to 3.6 into current code contracts. It is diagnostic-only and
does not override mandate gates from production workflow.

## Scope

Stress Lab covers:

- 3.1 Scenario Library (historical + synthetic)
- 3.2 Stress Conclusions
- 3.3 What Happens If API foundation (no UI)
- 3.4 Crisis Replay
- 3.5 Hedge Gap Analysis
- 3.6 Current Portfolio Stress Scorecard

## Current contract

Primary artifact: `stress_report.json` in each portfolio output folder.

Required top-level blocks:

- `scenario_results`
- `historical_results`
- `historical_episode_paths`
- `stress_scorecard_v1`
- `stress_conclusions`
- `hedge_gap_analysis`
- `stress_scenario_analytics`
- `scenario_library_meta`
- `scenario_library_normalized_meta`

## Sub-block implementation map

### 3.1 Scenario Library

- Core implementation: `src/stress.py`, `src/scenario_library.py`, `src/scenario_library_normalized.py`
- Spec ownership: `stress_testing_spec.md`, `scenario_library_spec.md`

### 3.2 Stress Conclusions

- Core implementation: `src/stress.py` (`stress_conclusions`) and `src/portfolio_commentary.py`
- User-facing summary is generated from structured fields; no standalone recommendation engine.

### 3.3 What Happens If API (no UI)

- Core implementation: `src/stress.py::simulate_custom_shock`, `shock_vector_from_scenario`
- Contract: `stress_testing_spec.md` §12.3
- Tests: `tests/test_stress_simulator_contract.py`
- Reuses the same linear shock engine as synthetic scenarios; PnL fields must match built-in
  `scenario_results` rows for equivalent shock vectors.

### 3.4 Crisis Replay

- Core implementation: `historical_episode_paths` in `src/stress.py`
- CSV export in `run_report.py` as `results_csv/crisis_replay_{episode}.csv`

### 3.5 Hedge Gap Analysis

- Core implementation: `hedge_gap_analysis` in `src/stress.py`
- Detailed interpretation rules: `hedge_gap_analysis_spec.md`

### 3.6 Stress Scorecard

- Core implementation: `stress_scorecard_v1` in `src/stress.py`
- Must be consumable by snapshots and comparison outputs without parsing commentary text.

## Non-goals

- No UI simulator in this layer.
- No direct optimizer or mandate release impact from stress diagnostics.
- No investment recommendations.
