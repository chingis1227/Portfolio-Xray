# Candidate Factory Shared Evidence — Repeated Heavy Calculation Audit

Date: 2026-05-23

Purpose: evidence base for [Candidate Factory Shared Evidence ExecPlan](../exec_plans/2026-05-23_candidate_factory_shared_evidence_plan.md). Identifies which heavy computations are repeated 16× across `default_v1` Phase 2 `lightweight_comparison` reports and which can be computed once per factory run.

Scope: Blocks 1–5 / Candidate Factory orchestration only. No formula, optimizer, stress definition, or comparison semantic changes proposed here.

Related timing evidence:

- [Session 06 timing audit](2026-05-22_candidate_factory_parallel_reports_session06_timing_audit.md) — 16 candidates sequential: 1192.9 s report sum (~74.6 s/candidate); parallel 4 workers: 631 s wall (−47.9%)
- [Session 05 timing audit](2026-05-22_candidate_factory_parallel_reports_timing_audit.md) — 2 candidates: ~85 s/candidate
- [Timing baseline](2026-05-22_candidate_factory_timing_baseline.md) — post runtime-refactor: ~101–107 s/candidate lightweight

---

## Executive Summary

After Session 4 `CandidateRunContext` and Session 3 `lightweight_comparison`, Phase 2 still dominates factory runtime. Parallel reports reduce wall-clock via concurrency but **do not remove duplicate invariant work**.

**Already shared (1× per factory run):** monthly panel, daily universe returns, universe asset factor betas 5Y/10Y, recession/scenario factor matrices (`src/candidate_run_context.py`).

**Main remaining cost:** full `run_portfolio_report_for_weights` ×16, especially factor regression paths that re-call `download_all` + `build_factor_matrix` despite cached daily panel.

**Target:** extend shared evidence context so invariant blocks run once; candidate path = slice + linear algebra + artifact assembly.

---

## Repeated-Heavy-Calculation Map

| ID | Computation | Location | Weights? | Shared today? | ×16? |
| --- | --- | --- | --- | --- | --- |
| R1 | `portfolio_factor_regression_weekly` ×4 + `factor_variance_decomposition_weekly` | `run_report.py:1003–1041`, `1506`; `stress_factors.py:1750–1784` | y = R·w | No | Yes — **dominant** |
| R2 | Diagnostic extended asset OLS (`FACTOR_COLUMN_ORDER`) | `run_report.py:741–761`; `stress_factors.py:3107` | slice | Partial | Yes |
| R3 | Asset metrics all tickers × 3 windows | `run_report.py:482–523` | No | No | Yes |
| R4 | Correlation matrices | `run_report.py:601` | No | No | Yes |
| R5 | `run_stress` → `cov_base` | `stress.py:1166` | No (base) | No | Yes |
| R6 | Full `run_stress` suite | `run_report.py:934` | Yes (PnL, RC, historical) | Partial | Yes |
| R7 | `factor_covariance_analytics` | `run_report.py:1199` | overlay uses portfolio betas | Partial | Yes |
| R8 | `macro_regime_diagnostics` | `run_report.py:1288` | Yes | Partial | Yes |
| R9 | `portfolio_pca_diagnostics` | `run_report.py:1545` | Yes | No | Yes |
| R10 | Second `load_daily_asset_returns_shared` | `run_report.py:1806` | No (panel) | No | Yes |
| R11 | `save_inputs` + scenario library base | `run_report.py:437`, `1734` | Mixed | Partial | Yes |
| — | Phase 1 weights | `candidate_factory.py` | Yes | N/A | ~0.01 s |
| — | `build_candidate_comparison` | `candidate_comparison.py` | No | **1×** | No |

**Lightweight skips only:** rolling/Kalman/regime-analytics, HTML/commentary, `snapshot_assets` — not core stress/regressions/metrics.

---

## Invariant vs Candidate-Dependent

| Invariant (1× per analysis) | Candidate-dependent (per weights) |
| --- | --- |
| Monthly prices/returns, rf, benchmark, cash, FX | `portfolio_returns_nan_safe`, `weights_used` |
| Daily universe panel | Portfolio metrics, drawdown on port series |
| Universe asset factor betas 5Y/10Y | `portfolio_factor_betas`, sliced `beta_tickers` |
| Weekly factor matrices (recession, episode) | Factor regression y = R @ w |
| Asset-level metrics (all tickers) | Stress synthetic/historical PnL, RC Top1/3 |
| Base monthly cov, asset return correlations | Snapshots, per-folder scenario library |
| Scenario shock definitions | Comparison row content |

---

## Code Chain

    run_candidate_factory
      prepare_candidate_run_context()     # 1×
      Phase 1: build_candidate_weights    # fast
      Phase 2: _run_lightweight_report_worker ×16
        run_portfolio_report_for_weights(..., run_context)
      build_candidate_comparison()        # 1×

---

## Vectorization Opportunities

| Area | Feasibility | Notes |
| --- | --- | --- |
| Synthetic stress PnL | **High** | `r_asset` invariant; `portfolio_pnl = w @ r_asset` |
| `cov_base` | **High** | One `cov_matrix_monthly` on universe |
| Portfolio factor betas | **High** | Already `w @ B`; batch as matrix multiply |
| Portfolio factor regression | **High** | Shared X; varying y = R @ w |
| Asset metrics / corr | **High** | Fully invariant |
| RC_vol dynamic | **Low** | Depends on `weights_used` per month |
| Historical episodes | **Per candidate** | `sub @ w`; recession calibration uses portfolio_betas |

---

## Outputs at Risk if Sharing Wrong

| Artifact | Risk |
| --- | --- |
| `stress_report.json` | Wrong PnL, pass/fail, regression inference |
| `snapshot_10y.json` | Wrong CAGR/vol/beta/RC |
| `candidate_comparison.json` | Wrong ranking / stress summaries |
| `scenario_library*.json` | Must remain per-candidate |

Parity gates: `tests/test_report_profile.py`; Session 06 comparison-critical fields (13/13 succeeded candidates).

---

## Expected Speedup (after Sessions 1–6)

| Milestone | Report s/cand (est.) | 16-cand sequential |
| --- | ---: | ---: |
| Current baseline | ~75 | ~20 min |
| P1 cache only | 55–65 | 15–17 min |
| P1 + P2 factor dedup | 35–50 | 9–13 min |
| P1–P3 stress prepared | 25–40 | 7–11 min |

Measure with per-block instrumentation (Session 1) and full-menu timing audit (Session 6).

**Session 6 measured (2026-05-23):** [Session 06 timing audit](2026-05-23_candidate_factory_shared_evidence_session06_timing_audit.md) — sequential `report_seconds` **857.7 s** vs 2026-05-22 baseline **1192.9 s** (**−28.1%**); target −35% not met; dominant remaining blocks: `macro_regime`, `daily_tail_risk`, `portfolio_pca`.

---

## Maintenance

Re-run timing comparison after shared-context or factor-cache changes. Use [Session 06 timing audit](2026-05-23_candidate_factory_shared_evidence_session06_timing_audit.md) and `scripts/shared_evidence_session06_timing_smoke.py`.
