# Site/API Default Output — Session 07 Closure Report

Date: 2026-05-23

Purpose: Final closure for the [Site/API Default Output Refactor ExecPlan](../exec_plans/2026-05-23_site_api_default_output_refactor_plan.md). Confirms acceptance criteria, session deliverables (0–7), verification evidence, remaining risks, and recommended next optimization work. Scope was output routing and execution defaults only; formulas, optimizers, stress methodology, candidate weights, comparison ranking, and selection logic were not changed.

Related evidence:

- Session 6 timing and artifact audit: [Session 06 timing audit](2026-05-23_site_api_default_output_session06_timing_audit.md)
- Benchmark script: `scripts/site_api_session06_benchmark_smoke.py`
- Central policy: `src/output_policy.py`

---

## ExecPlan verdict

**Status: Completed (Sessions 0–7, 2026-05-23).**

Default project entrypoints now route through `site_api` unless the operator explicitly requests `full_report`, `legacy_export`, PDF flags, or `--with-report` on optimization.

---

## Acceptance criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Default workflow does not generate presentation/export artifacts | **Met** | `output_policy_for_profile("site_api")` disables CSV/TXT/HTML/PNG/PDF/Markdown/CSS; Session 6 isolated run: all presentation counts **0** |
| 2 | Required JSON contracts still generate | **Met** | Session 6: per-candidate `snapshot_10y.json`, `stress_report.json`, `output_manifest.json`; decision package **14/14** JSON |
| 3 | Cache continues to work | **Met** | Parquet/cache paths unchanged; factory/report reuse warm cache (Session 6 wall **171.6 s**) |
| 4 | Candidate generation and comparison still work | **Met** | `core_benchmarks` × 2 `full_success`; `comparison_succeeded` true |
| 5 | No formula/optimizer/stress/weight semantics change | **Met** | ExecPlan non-goals enforced; changes limited to `src/output_policy.py` and guarded writers |
| 6 | Legacy/export mode explicitly callable | **Met** | `full_report`, `legacy_export`, `--with-report`, `--legacy-full-pdf`, `rebuild_pdf_reports.py` |
| 7 | Documentation explains policy and commands | **Met** | Session 4: `README.md`, `ARCHITECTURE.md`, `OUTPUTS.md`, `PRODUCT.md`, reporting/review/factory specs |
| 8 | Focused tests pass | **Met** | Session 7 re-run: **38 passed** (bundle below) |
| 9 | Timing benchmark includes artifact counts | **Met** | Session 6 audit + `artifact_counts_by_type()` in smoke summary JSON |
| 10 | Closure report: risks and next step | **Met** | This document |

---

## Session deliverables (summary)

| Session | Outcome |
| --- | --- |
| 0 | Discovery, code/output map, ExecPlan authored |
| 1 | `src/output_policy.py`, `output_manifest.json` helper |
| 2 | Defaults on `run_report.py`, `run_portfolio_review.py`, `run_candidate_factory.py`, `run_optimization.py`, comparison writers |
| 3 | JSON-first RC resolution; rolling beta exports gated; factory passes `output_profile` |
| 4 | Documentation sync and command matrix |
| 5 | Focused tests (`test_output_policy.py`, offline MVP/review aligned to JSON-only) |
| 6 | Runtime benchmark smoke + [Session 06 audit](2026-05-23_site_api_default_output_session06_timing_audit.md) |
| 7 | Closure report, register updates, ExecPlan marked Completed |

---

## Verification (Session 7)

Focused pytest bundle (repository root, project `.venv`):

```text
python -m pytest tests/test_output_policy.py tests/test_report_profile.py \
  tests/test_portfolio_review_workflow.py tests/test_mvp_pipeline_offline.py \
  tests/test_portfolio_first_e2e_offline.py -q \
  --basetemp=tmp/pytest_site_api_session7
```

Result (2026-05-23): **38 passed** in ~143 s.

Optional live smoke (unchanged from Session 6):

```text
python scripts/site_api_session06_benchmark_smoke.py
```

Expect: exit code **0**, `acceptance.all_passed: true`, presentation artifact counts **0**.

---

## Default command matrix (operator)

| Goal | Command / flag |
| --- | --- |
| Site/API JSON review | `python run_portfolio_review.py` (default `site_api`, no PDF) |
| Site/API report only | `python run_report.py` (default `site_api`) |
| Site/API candidates + compare | `python run_candidate_factory.py --then-compare` (default `standard` + `site_api`) |
| Policy optimize, JSON only | `python run_optimization.py` (no report/PDF unless `--with-report`) |
| Full CSV/TXT/HTML exports | `--output-profile full_report` on report/factory/review/compare entrypoints |
| Legacy export bundle | `--output-profile legacy_export` |
| PDFs | `rebuild_pdf_reports.py`, review `--with-pdf` / `--legacy-full-pdf`, factory `--pdf-mode` |

---

## Remaining risks

1. **Stale working-tree artifacts** — Historical CSV/TXT/PDF in portfolio folders are not evidence of default behavior; use isolated `tmp/site_api_session06/` or the Session 6 smoke script.
2. **Hidden presentation dependencies** — Any new report block that writes CSV/TXT/HTML must call `output_policy` guards; code review should treat unguarded writers as regressions.
3. **Legacy operator expectations** — `run_optimization.py` no longer runs `run_report.py` or PDF rebuild by default; operators need `--with-report` for export paths.
4. **Report CPU bottleneck** — `site_api` removes presentation I/O but not macro/regime/tail-risk/PCA compute (~155 s report phase for 2-candidate smoke).

---

## Recommended next optimization step

Prioritize **compute-bound report blocks** under `site_api`, not re-enabling presentation exports:

1. Extend **shared evidence** / factory context so `macro_regime`, `daily_tail_risk`, and `portfolio_pca` run once per factory batch where safe (see [Candidate Factory Shared Evidence](../exec_plans/2026-05-23_candidate_factory_shared_evidence_plan.md) — completed; further wins likely incremental).
2. Optional **opt-in parallel lightweight reports** for large menus when operators accept soak risk ([Parallel Lightweight Reports](../exec_plans/2026-05-22_candidate_factory_parallel_reports_plan.md) — remains opt-in).
3. Add a **CI gate** that runs `site_api_session06_benchmark_smoke.py` (or pytest artifact-count fixtures) on output-routing PRs to prevent presentation regressions.

Do **not** treat restoring CSV/TXT/PDF as the default as an optimization; use explicit `full_report` / `legacy_export` / PDF commands.

---

## Register actions (Session 7)

- ExecPlan status → **Completed** in [ExecPlan register](../exec_plans/README.md).
- This audit linked from [Audit register](../audits/README.md).
- Session 06 timing audit status → **Historical** (superseded by this closure for plan status).
