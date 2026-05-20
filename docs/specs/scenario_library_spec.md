# Scenario Library Specification

This document owns the contract for Scenario Library v1 and Scenario Library Normalized View v1.

## Scenario Library v1

`src/scenario_library.py` implements `scenario_library_v1`.

Purpose:

- standardize scenario inputs after stress and regime analytics are built
- collect base, stress, historical, macro/regime, and scenario analytics into normalized scenario objects
- expose scenario metadata for reporting and later candidate analysis

The library is input-standardization only. It does not change optimizer inputs, mandate gates, stress pass/fail logic, or weight release.

Primary report outputs:

- `scenario_library.json` in the final output directory
- `scenario_library_summary.csv`
- `scenario_library_missing_inputs.csv`
- `scenario_library_warnings.csv`
- `stress_report.scenario_library_meta`

## Scenario Library Normalized View v1

`src/scenario_library_normalized.py` implements `scenario_library_normalized_v1`.

Purpose:

- derive an optimization-input view on top of Scenario Library v1
- preserve upstream analytics unchanged
- classify readiness for synthetic, historical, base, and macro scenarios
- disclose pipeline return frequency versus optimization frequency
- optionally wire historical-stress fallback metadata

Primary outputs:

- `scenario_library_normalized.json`
- normalized summary and warning artifacts where implemented
- `stress_report.scenario_library_normalized_meta`

Current canonical scenario ids are sourced from `src/stress.py` and include synthetic
`equity_shock`, `credit_shock`, `rates_shock`, `inflation_stagflation`, `liquidity_shock`,
`usd_shock`, `commodity_shock`, `recession_severe`, plus historical `dotcom`, `2008`, `2020`,
`2022`, and `banking_2023`.

## Historical Stress Fallback

`src/historical_stress_fallback.py` provides a per-asset historical episode return waterfall for normalized historical rows:

- direct ticker history
- ticker proxy
- asset-class proxy
- factor replay

It does not overwrite direct ETF history. Episodes ending before `2007-01-01` may use the long loose weekly factor panel passed by `run_report.py`; later episodes use the strict 2007+ factor matrix used by stress and scenario library paths.

## Boundaries

Scenario Library outputs can support candidate analysis and robust scenario optimization, but they are not production policy by themselves.
