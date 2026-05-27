# Scenario Library Specification

This document owns the contract for Scenario Library v1 and Scenario Library Normalized View v1.

**Product placement:** Scenario Library is **Block 3.1** inside **Block 3 (Stress Test Lab)**.
Official product definition and fixed active scenario IDs:
[stress_lab_layer_spec.md](stress_lab_layer_spec.md) §3.1. This file owns build artifacts and
normalization rules; it does not redefine the active scenario set.

## Block 3.1 — active scenario set (fixed)

Scenario Library is the unified set of test scenarios for portfolio stress evaluation. The active
sets below are **closed** unless changed via [stress_testing_spec.md](stress_testing_spec.md) and
`DECISIONS.md`.

### 3.1.1 Historical scenarios

Real market crises and stress periods: `dotcom`, `2008`, `2020`, `2022`, `banking_2023`.

### 3.1.2 Synthetic scenarios

Predefined factor shocks: `equity_shock`, `credit_shock`, `rates_shock`, `inflation_stagflation`,
`liquidity_shock`, `usd_shock`, `commodity_shock`, `recession_severe`.

**Code single source for IDs:** `HISTORICAL_SCENARIO_IDS` and `SYNTHETIC_SCENARIO_IDS` in
`src/scenario_library.py` (must match `HISTORICAL_EPISODES` / `run_stress` in `src/stress.py`).

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

`scenario_library_v1` is the implementation/version name and sidecar artifact contract. The Core
MVP `stress_report.json` does not expose a top-level `scenario_library_v1` key; it links to the
sidecar through `scenario_library_meta` (and related embedded summaries where present).

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

Canonical scenario IDs are the fixed Block 3.1 sets in §Block 3.1 above (not extensible by
library build alone).

## Historical Stress Fallback

`src/historical_stress_fallback.py` provides a per-asset historical episode return waterfall for normalized historical rows:

- direct ticker history
- ticker proxy
- asset-class proxy
- factor replay

It does not overwrite direct ETF history. Episodes ending before `2007-01-01` may use the long loose weekly factor panel passed by `run_report.py`; later episodes use the strict 2007+ factor matrix used by stress and scenario library paths.

## Boundaries

Scenario Library outputs can support candidate analysis and robust scenario optimization, but they are not production policy by themselves.
