# Candidate Factory Parallel Lightweight Reports Timing Audit

Date: 2026-05-22

Purpose: record Session 5 verification evidence for the [Candidate Factory Parallel Lightweight Reports](../exec_plans/2026-05-22_candidate_factory_parallel_reports_plan.md) ExecPlan. This audit compares a two-candidate sequential `standard` lightweight-report run with an opt-in parallel lightweight-report run on the same workspace and current `config.yml`. The work is runtime orchestration only; no financial formulas, optimizer mathematics, stress scenarios, candidate weights, or comparison semantics were changed.

Scope: `equal_weight` and `risk_parity` only, run through the Python factory API with isolated temporary `project_root` folders under `tmp/candidate_parallel_session05/` so the repository's root generated portfolio folders were not intentionally refreshed.

---

## Verification bundle

Focused regression command:

    .\.venv\Scripts\python.exe -m pytest tests/test_candidate_factory.py tests/test_candidate_manifest.py -q --basetemp='tmp\pytest_candidate_parallel_session5'

Result: **48 passed** in 4.76s.

The focused suite covers parallel lightweight report overlap, failure continuation without `fail_fast`, sequential fallback when `fail_fast=True`, manifest writing, and candidate menu-order registration.

---

## Smoke run setup

The smoke used the project `.venv` Python 3.12.13 and loaded the current root `config.yml` with tickers `SPY, QQQ, GLD, SLV, BND, SCHD, SCHP, TLT`. Both runs used:

- `execution_mode='standard'`
- `pdf_mode='none'`
- `skip_existing=False`
- `force=True`
- `fail_fast=False`
- `full_candidate_reports=False`
- explicit candidates: `equal_weight,risk_parity`

Sequential project root:

    tmp/candidate_parallel_session05/sequential

Parallel project root:

    tmp/candidate_parallel_session05/parallel

The parallel run used:

    parallel_lightweight_reports=True
    lightweight_report_workers=2

Evidence JSON saved locally:

    tmp/candidate_parallel_session05/session05_smoke_summary.json

During live data/factor setup, Yahoo emitted expected historical availability warnings for instruments that did not exist in early historical windows, such as `GLD`, `SLV`, `BND`, `SCHD`, `SCHP`, `TLT`, and `DBC`. The runs still completed with `run_status: full_success`.

---

## Timing result

| Mode | Factory run status | Wall clock seconds | Factory report_seconds sum | Factory total_seconds sum | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| Sequential standard | `full_success` | 185.681 | 169.999 | 170.011 | two lightweight reports run one after another |
| Parallel standard, 2 workers | `full_success` | 120.014 | 223.465 | 223.482 | two lightweight reports overlapped; run-level parallel wall clock 111.969s |

Observed wall-clock improvement: **35.4%** for this two-candidate smoke.

Per-candidate timing:

| Mode | Candidate | builder_core_seconds | report_seconds | pdf_seconds | total_seconds | report_profile |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Sequential | `equal_weight` | 0.004 | 84.695 | 0.0 | 84.699 | `lightweight_comparison` |
| Sequential | `risk_parity` | 0.008 | 85.304 | 0.0 | 85.312 | `lightweight_comparison` |
| Parallel | `equal_weight` | 0.005 | 111.927 | 0.0 | 111.932 | `lightweight_comparison` |
| Parallel | `risk_parity` | 0.012 | 111.538 | 0.0 | 111.550 | `lightweight_comparison` |

The parallel run-level disclosure recorded:

    requested: true
    effective: true
    status: parallel
    workers: 2
    submitted_candidate_ids: [equal_weight, risk_parity]
    registered_candidate_ids: [equal_weight, risk_parity]
    wall_clock_seconds: 111.969
    fallback_reasons: []

---

## Artifact equivalence check

The smoke compared sequential and parallel candidate outputs for:

- `weights.json`
- `candidate_weights_build.json`
- `snapshot_10y.json`
- `stress_report.json`
- `summary.json`
- `candidate_manifest.json`

Volatile fields such as timestamps, generated-at fields, run durations, and timing fields were ignored. Numeric comparison used absolute tolerance `1e-3` for live floating-point report values.

Comparison-critical fields were equivalent for both candidates:

| Artifact area | `equal_weight` | `risk_parity` | Notes |
| --- | --- | --- | --- |
| `weights.json` | OK | OK | final weights matched |
| `candidate_weights_build.json` excluding `built_at` | OK | OK | build metadata matched after timestamp removal |
| `snapshot_10y.json` stress suite / constraints / portfolio params | OK | OK | comparison-facing snapshot values matched within tolerance |
| `stress_report.json` `stress_suite_results` | OK | OK | stress scenario pass/fail and PnL matched within tolerance |
| `stress_report.json` `stress_scorecard_v1` | OK | OK | scorecard matched |
| `stress_report.json` `stress_conclusions` | OK | OK | conclusions matched |
| `stress_report.json` `historical_methodology` | OK | OK | methodology disclosure matched |
| `summary.json` | OK | OK | summary matched after volatile-field removal |
| `candidate_manifest.json` | OK | OK | manifest matched after volatile-field removal |

Caveat: a full recursive JSON comparison of `stress_report.json` found non-comparison-critical differences in deeper diagnostic blocks, mainly `portfolio_pca` residual PCA and `factor_covariance.comparison.overlay_amplification` ordering/values. This appears tied to live factor/data refresh nondeterminism between the separate sequential and parallel smoke runs, not to candidate weights or comparison-facing status. The comparison-critical stress fields listed above remained equivalent.

---

## Acceptance summary

| Session 5 criterion | Status | Evidence |
| --- | --- | --- |
| Focused parallel factory tests pass | Met | `48 passed` focused pytest bundle |
| Sequential and parallel smoke runs complete | Met | both `run_status: full_success` |
| Candidate outputs are comparison-equivalent after ignoring timestamps/timing | Met with caveat | weights, snapshot comparison fields, stress suite/scorecard/conclusions, summaries, and manifests matched; full stress diagnostic JSON had live-data diagnostic drift noted above |
| Timing audit shows material wall-clock improvement | Met | 185.681s sequential vs 120.014s parallel; 35.4% faster |

---

## Maintenance notes

- Treat this as an observed baseline, not a performance SLA.
- Re-run after data-pipeline, factor-cache, stress-report, or shared-context changes.
- If future acceptance requires full recursive `stress_report.json` equality, use a pinned offline data fixture or a shared frozen data context; live network/cache refresh can change deeper diagnostics between back-to-back runs.
