# Site/API Default Output — Session 06 Runtime Benchmark Audit

Date: 2026-05-23

Purpose: Session 6 closure evidence for the [Site/API Default Output Refactor ExecPlan](../exec_plans/2026-05-23_site_api_default_output_refactor_plan.md). Measures wall-clock time, per-stage timing, artifact counts by type, required JSON presence, and presentation-artifact absence for the default `site_api` factory + decision-package path. Output routing only; no formula, optimizer, stress, or weight semantics changed.

Scope: `core_benchmarks` × 2 (`equal_weight`, `risk_parity`) in an isolated project root under `tmp/site_api_session06/benchmark/` (copied root `config.yml`; repository portfolio folders not refreshed).

Evidence JSON: `tmp/site_api_session06/session06_benchmark_summary.json`

Log: `tmp/site_api_session06/session06_benchmark.log`

Re-run: `python scripts/site_api_session06_benchmark_smoke.py` from repository root (`.venv` recommended).

---

## Verification bundle

```text
python -m pytest tests/test_output_policy.py tests/test_report_profile.py \
  tests/test_portfolio_review_workflow.py tests/test_mvp_pipeline_offline.py \
  tests/test_portfolio_first_e2e_offline.py -q \
  --basetemp=tmp/pytest_site_api_session6
```

Result (2026-05-23): **38 passed** in ~197 s.

---

## Smoke run setup

- Project `.venv` Python, root `config.yml` copied into isolated `project_root` (8 tickers).
- `profile_id='core_benchmarks'`, `explicit_candidates=['equal_weight', 'risk_parity']`
- `output_profile='site_api'` (CLI default)
- `execution_mode='standard'`, `pdf_mode='none'` (CLI defaults)
- `skip_existing=False`, `force=True`, `fail_fast=False`
- `then_compare=True` (decision-package chain after factory)
- `full_candidate_reports=False`, `parallel_lightweight_reports=False`

---

## Timing result vs pre–site_api baseline

Reference baseline: [Candidate Factory Timing Baseline](2026-05-22_candidate_factory_timing_baseline.md) — same 2-candidate `core_benchmarks` smoke with `standard` + `pdf_mode none` before presentation export was gated (`report_seconds` **208.671**).

| Metric | Pre–site_api baseline (2026-05-22) | Post–site_api Session 6 (2026-05-23) | Change |
| --- | ---: | ---: | --- |
| Factory `run_status` | `full_success` (2/2) | `full_success` (2/2) | same |
| Wall clock (s) | ~235 | **171.6** | **−27.0%** |
| `timing_summary.report_seconds` | 208.671 | **155.0** | **−25.7%** |
| `pdf_seconds` | 0.0 | 0.0 | same |
| `builder_core_seconds` | 0.025 | 0.018 | same order |

Per-candidate `report_seconds`:

| Candidate | Baseline (s) | Session 6 (s) |
| --- | ---: | ---: |
| `equal_weight` | 107.276 | 77.500 |
| `risk_parity` | 101.395 | 77.458 |

**Interpretation:** Faster wall clock is consistent with warm cache and shared-evidence report optimizations shipped in parallel plans; the Session 6 goal is artifact-policy proof, not a new timing target. Presentation I/O (CSV/TXT/HTML/PNG/PDF) is absent by count; compute-bound report blocks (`macro_regime`, `daily_tail_risk`, `portfolio_pca`, `snapshots`) remain the bottleneck.

Aggregated report block times (2 candidates):

| Block | Seconds (total) |
| --- | ---: |
| `macro_regime` | 23.6 |
| `daily_tail_risk` | 15.4 |
| `snapshots` | 12.7 |
| `portfolio_pca` | 7.3 |
| `scenario_library` | 1.0 |
| `factor_covariance` | 0.7 |
| Other blocks | < 0.4 each |

---

## Artifact counts by type

Counts from `artifact_counts_by_type()` over the isolated run tree (`src/output_policy.py`).

| Scope | json | csv | txt | html | png | pdf | md sidecars | css |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `project_root` | **54** | **0** | **0** | **0** | **0** | **0** | **0** | **0** |
| `Main portfolio/` | **21** | **0** | **0** | **0** | **0** | **0** | **0** | **0** |
| `equal-weight portfolio/` | 17 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `risk parity portfolio/` | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**ExecPlan acceptance (artifact policy):** all presentation classes **zero** at project root and per candidate; JSON contracts and `output_manifest.json` present.

---

## Required JSON contracts

| Check | Result |
| --- | --- |
| Per-candidate: `snapshot_10y.json`, `stress_report.json`, `output_manifest.json` | **pass** (2/2) |
| Factory: `candidate_factory_run.json`, `output_manifest.json` | **pass** |
| Decision package (14 MVP JSON files + schemas) | **pass** (all present, schema OK) |
| `comparison_succeeded` | **pass** |
| `acceptance.all_passed` in summary JSON | **true** |

Disabled artifact classes recorded in manifest: `csv`, `txt`, `html`, `png`, `pdf`, `markdown_pdf_sidecars`, `css_visual_assets`.

---

## Remaining bottlenecks and risks

1. **Report CPU still dominates** — site_api removes presentation I/O but not macro/regime/tail-risk/PCA compute.
2. **Stale repo artifacts** — historical CSV/TXT/PDF in the working tree are not evidence of default behavior; use isolated `tmp/site_api_session06/` or the smoke script.
3. **Plan closure** — see [Session 07 closure report](2026-05-23_site_api_default_output_session07_closure_report.md).

---

## Re-run checklist

1. `python scripts/site_api_session06_benchmark_smoke.py` → exit code **0**, `acceptance.all_passed: true`.
2. Confirm `artifact_counts_by_type` presentation columns are all **0**.
3. Re-run the pytest bundle above if output routing code changed.
