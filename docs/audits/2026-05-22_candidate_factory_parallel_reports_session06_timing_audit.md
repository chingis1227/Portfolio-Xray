# Candidate Factory Parallel Reports — Session 06 Timing Audit

Date: 2026-05-22

Purpose: record Session 6 default-mode decision evidence for the [Candidate Factory Parallel Lightweight Reports](../exec_plans/2026-05-22_candidate_factory_parallel_reports_plan.md) ExecPlan. This audit compares a **full `default_v1`** sequential `standard` lightweight-report run with an opt-in parallel run on the same workspace and current root `config.yml`. Runtime orchestration only; no formulas, weights, or comparison semantics were changed.

Scope: all **16** `default_v1` candidates in isolated temporary project roots under `tmp/candidate_parallel_session06/` so repository portfolio folders were not refreshed.

Evidence JSON: `tmp/candidate_parallel_session06/session06_smoke_summary.json`

Log: `tmp/candidate_parallel_session06/session06_smoke.log`

---

## Verification bundle

Focused regression command:

    .\.venv\Scripts\python.exe -m pytest tests/test_candidate_factory.py tests/test_candidate_manifest.py -q --basetemp=tmp/pytest_candidate_parallel_session6

Result: **48 passed** in 14.45s.

---

## Smoke run setup

Both runs used the project `.venv` Python, current root `config.yml` (8 tickers), and:

- `profile_id='default_v1'` (16 candidates)
- `execution_mode='standard'`
- `pdf_mode='none'`
- `skip_existing=False`, `force=True`, `fail_fast=False`
- `full_candidate_reports=False`

Sequential root: `tmp/candidate_parallel_session06/sequential`

Parallel root: `tmp/candidate_parallel_session06/parallel`

Parallel options: `parallel_lightweight_reports=True`, `lightweight_report_workers=4`

---

## Timing result

| Mode | Factory `run_status` | Wall clock (s) | Factory `timing_summary.report_seconds` | Parallel disclosure |
| --- | --- | ---: | ---: | --- |
| Sequential standard | `partial_success` | 1210.631 | 1192.941 | n/a |
| Parallel standard, 4 workers | `partial_success` | 631.117 | (per-step sum higher due overlap) | `status=parallel`, `wall_clock_seconds=616.902`, no fallback |

Observed wall-clock improvement: **47.9%** for the full 16-candidate menu on this machine.

---

## Run status parity

Both runs recorded identical factory summaries and per-candidate step statuses:

| Metric | Sequential | Parallel |
| --- | ---: | ---: |
| `total` | 16 | 16 |
| `succeeded` | 13 | 13 |
| `failed` | 2 | 2 |
| `skipped_dependency` | 1 | 1 |

Per-candidate status mismatches between modes: **none**.

Expected non-parallel failures (isolated roots, missing operator prerequisites):

- `robust_mv_constrained`, `robust_mv_uncapped`: `builder_failed` — missing `analysis_robust_mv_lambda_calibration/selected_lambda.txt`
- `robust_scenario`: `skipped_dependency` — missing Main `scenario_library_normalized.json` and `stress_report.json`

Parallel mode submitted **15** lightweight reports (all except `robust_scenario`) and registered results in **menu order**.

---

## Comparison-critical artifact parity (13 succeeded candidates)

For candidates with `snapshot_10y.json` and `stress_report.json` in both roots:

| Check | Result |
| --- | --- |
| `weights.json` exact match | 13/13 |
| `candidate_factory_run.json` step status/reason brief match | match |
| `candidate_factory_manifest.json` step status brief + summary | match |
| Stress comparison-critical fields (`status`, fail codes, scenario pass/PnL summary) | 13/13 match |

Volatile-only diffs (expected between separate live runs): snapshot `timestamp`, manifest `duration_seconds`, deeper diagnostic-only stress blocks (same caveat as Session 5).

---

## Session 06 default-mode decision

**Recommendation: keep `--parallel-lightweight-reports` opt-in; do not change the product default.**

Rationale:

1. **Timing evidence is strong** (~48% wall-clock improvement on full `default_v1`), and run-status / comparison-critical artifact parity matched for all succeeded candidates.
2. **Evidence is not sufficient alone to flip the default** because: (a) full menu still ended `partial_success` on this isolated setup due to pre-existing robust-suite prerequisites, not parallel behavior; (b) only one live machine/session of full-menu evidence; (c) automatic sequential fallback still applies to `fail_fast`, per-candidate PDF, and Phase 3 full reports; (d) portfolio-first review and operator docs intentionally document parallel as an advanced flag.
3. **Sequential mode remains the safe rollback/fallback** as shipped in Sessions 1–4.

No change to `DECISIONS.md` or `ROADMAP.md` (default not switched). Decision recorded in the ExecPlan Decision Log.

---

## Maintenance notes

- Re-run after shared run-context, factor-cache, or factory orchestration changes.
- For acceptance of full recursive `stress_report.json` equality, use pinned offline fixtures or a shared frozen data context (Session 5 caveat).
