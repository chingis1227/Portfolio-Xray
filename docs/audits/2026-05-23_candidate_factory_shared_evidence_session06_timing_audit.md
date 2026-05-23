# Candidate Factory Shared Evidence — Session 06 Timing Audit

Date: 2026-05-23

Purpose: Session 6 closure evidence for the [Candidate Factory Shared Evidence ExecPlan](../exec_plans/2026-05-23_candidate_factory_shared_evidence_plan.md). Compares a **full `default_v1`** sequential `standard` lightweight-report factory run **after** Sessions 1–5 (shared context, factor weekly frames, prepared stress) against the pre-change Session 06 baseline from [Parallel Reports Session 06 Timing Audit](2026-05-22_candidate_factory_parallel_reports_session06_timing_audit.md). Orchestration and caching only; no formula, weight, or comparison semantic changes.

Scope: all **16** `default_v1` candidates in an isolated project root under `tmp/candidate_shared_evidence_session06/sequential/` (copied `config.yml`; candidate artifact folders under that root only).

Evidence JSON: `tmp/candidate_shared_evidence_session06/session06_smoke_summary.json`

Log: `tmp/candidate_shared_evidence_session06/session06_smoke.log` (when captured via redirect)

Re-run: `python scripts/shared_evidence_session06_timing_smoke.py` from repository root (`.venv` recommended).

---

## Verification bundle

```text
python -m pytest tests/test_candidate_factory.py tests/test_candidate_comparison.py \
  tests/test_report_profile.py tests/test_candidate_run_context.py \
  tests/test_report_timing.py tests/test_prepared_stress.py -q \
  --basetemp=tmp/pytest_shared_evidence_session6

python scripts/verify_docs.py
```

Result (2026-05-23): **106 passed** in ~216s; `docs verification: OK`.

---

## Smoke run setup

- Project `.venv` Python, root `config.yml` copied into isolated `project_root` (8 tickers: SPY, QQQ, GLD, SLV, BND, SCHD, SCHP, TLT).
- `profile_id='default_v1'` (16 candidates)
- `execution_mode='standard'`, `pdf_mode='none'`
- `skip_existing=False`, `force=True`, `fail_fast=False`
- `full_candidate_reports=False`, `parallel_lightweight_reports=False`
- Factory enables per-step `report_timing` / `report_timing_aggregate` (Session 1 instrumentation)

---

## Timing result vs Session 06 baseline

| Metric | Pre-change baseline (2026-05-22) | Post shared evidence (2026-05-23) | Change |
| --- | ---: | ---: | --- |
| Factory `run_status` | `partial_success` | `partial_success` | same |
| Wall clock (s) | 1210.631 | 877.078 | **−27.5%** |
| `timing_summary.report_seconds` | 1192.941 | 857.712 | **−28.1%** |
| Succeeded / failed / skipped_dependency | 13 / 2 / 1 | 13 / 2 / 1 | same |

**ExecPlan timing target:** ≥35% reduction in sequential Phase 2 `report_seconds` sum vs 1192.941 s.

**Outcome:** **Not met** (28.1% observed). Plan closure uses the ExecPlan **documented blocker** path; implementation Sessions 1–5 remain shipped; Session 7 (batch API) stays deferred.

Per-candidate `report_seconds` (13 succeeded, from `builder_runtime_timing.json`):

| Candidate | Report (s) |
| --- | ---: |
| equal_weight | 64.109 |
| risk_parity | 64.462 |
| equal_weight_by_asset_class | 66.102 |
| risk_budget_by_asset | 67.167 |
| risk_budget_by_asset_class | 70.618 |
| hierarchical_risk_parity | 70.957 |
| minimum_variance | 68.241 |
| minimum_variance_uncapped | 66.884 |
| minimum_variance_advanced | 72.318 |
| maximum_diversification | 65.871 |
| maximum_diversification_uncapped | 68.902 |
| minimum_cvar_constrained | 75.374 |
| minimum_cvar_uncapped | 53.164 |

Mean over succeeded: **~66.0 s/candidate** vs ~**74.6 s/candidate** implied by the 2026-05-22 aggregate (1192.9 / 16).

---

## Aggregated report block times (13 timed reports)

From `timing_summary.report_timing_aggregate.report_blocks_seconds_total` (factory run):

| Block | Total (s) | Notes |
| --- | ---: | --- |
| macro_regime | 136.236 | Still dominant; per-candidate |
| daily_tail_risk | 110.867 | Per-candidate; daily panel reused but work remains |
| portfolio_pca | 45.354 | Per-candidate |
| scenario_library | 8.295 | Per-candidate assembly |
| factor_covariance | 5.803 | Reduced vs pre-instrumentation expectation |
| factor_regression | 2.291 | Shared weekly R+X (Session 4) |
| rc_corr | 2.578 | Corr matrices shared (Session 2) |
| run_stress | 0.958 | Prepared synthetic + shared cov (Sessions 2/5) |
| asset_metrics | 0.116 | Shared invariant metrics (Session 2) |
| factor_betas | 0.351 | Universe betas reused |
| save_inputs | 0.461 | Lightweight skip when applicable (Session 3) |

Invariant-cache targets (R1–R5, factor dedup, prepared stress) show **near-zero aggregate** time for asset metrics, factor regression, and stress base legs. Remaining gap to −35% is dominated by **macro_regime**, **daily_tail_risk**, and **portfolio_pca**, which were out of scope for Sessions 2–5.

---

## Run status parity with baseline

Same factory summary shape as 2026-05-22 Session 06:

- `robust_mv_constrained`, `robust_mv_uncapped`: `failed` (missing `analysis_robust_mv_lambda_calibration/selected_lambda.txt` in isolated root)
- `robust_scenario`: `skipped_dependency` (missing Main `scenario_library_normalized.json` / `stress_report.json` in isolated root)

---

## Comparison-critical parity

- **Pytest:** `tests/test_report_profile.py` full vs `lightweight_comparison` contract; factory/comparison/context/prepared-stress suites in verification bundle (106 passed).
- **Live smoke:** no pre-change artifact tree in isolated tmp for byte-level diff; parity for comparison-critical fields is covered by automated tests and matches the Session 06 live-audit caveat (timestamps / diagnostic-only stress drift between separate runs).

---

## Session 06 closure decision

1. **Ship Sessions 1–5** as the RM-982 implementation wave; mark RM-982 **Done** with timing target **partially met** (28.1% vs 35% goal).
2. **Do not** claim −35% to −55% sequential speedup in operator docs; use measured **~28%** `report_seconds` reduction on this machine/menu until a follow-up wave addresses macro_regime / tail-risk / PCA duplication.
3. **Defer** Session 7 batch evaluation API per ExecPlan; optional follow-up ExecPlan if operators need sub-10 min sequential menus without parallel workers.
4. **Keep** `--parallel-lightweight-reports` opt-in (unchanged; see parallel Session 06 audit).

---

## Maintenance

- Re-run `scripts/shared_evidence_session06_timing_smoke.py` after further factory report caching or `lightweight_comparison` scope changes.
- Append a dated row here when re-measured.
