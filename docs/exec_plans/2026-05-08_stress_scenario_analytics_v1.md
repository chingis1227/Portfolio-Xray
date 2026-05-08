# Stress Scenario Analytics v1 — ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

Reference: [PLANS.md](../../PLANS.md) at repository root.

## Purpose / Big Picture

After this change, every full `python run_report.py` run attaches a diagnostic block
`stress_scenario_analytics` to `stress_report.json` and writes nine scenario-analytics CSV files
under `results_csv/`. Analysts can compare historical (realized) and synthetic (shock × beta)
scenarios side by side: scenario PnL layers, asset and factor covariance/correlation, which
assets and factors drive variance (RC), raw vs shrinkage-adjusted synthetic PnL, and quality gates.
Nothing in this block changes optimizer weights, mandate checks, or stress pass/fail.

Verify: run `python run_report.py` (or tests), open `Main portfolio/stress_report.json` top-level
key `stress_scenario_analytics`, and confirm CSV files `stress_scenario_*.csv` in `results_csv/`.

## Progress

- [x] (2026-05-08) Spec section in `docs/docs/stress_testing_spec.md` for contract and shock-scale factor covariance.
- [x] (2026-05-08) Implemented `src/stress_scenario_analytics.py` and wired into `run_report.py` after beta overlay.
- [x] (2026-05-08) Added `tests/test_stress_scenario_analytics.py` and updated `AGENTS.md` / `SPEC.md`.

## Surprises & Discoveries

- `synthetic_factor_pnl_adjusted` stores per-scenario rows with `pnl_model_raw` / `pnl_model_adjusted` (not `portfolio_pnl_pct`); scenario analytics maps these explicitly.
- Base factor covariance for shock-scaling is taken from `stress_report["factor_covariance"]["base"]["matrix"]` (weekly, FACTOR_COVARIANCE_BASE_WEEKS), matching the existing factor covariance pipeline.
- `portfolio_factor_regression_weekly` returns no `status` field; `stress_scenario_analytics` treats non-empty `betas` as an available regression block for beta-quality gating.

## Decision Log

- Decision: Synthetic per-scenario factor covariance uses **base weekly factor correlation** from `factor_covariance.base` and **positive diagonal scaling** `sigma_k' = sigma_k * (1 + alpha * |shock_k|)` for the six production stress factors mapped via `FACTOR_BETA_TO_SYNTHETIC_SHOCK_KEY`, then eigenvalue PSD repair consistent with `_repair_covariance_psd`.
  Rationale: Aligns with user-selected "shock_scale" option and keeps cross-factor structure from data while stressing shocked factors' volatilities.
  Date: 2026-05-08.

- Decision: Historical realized portfolio PnL and returns are **never** Ledoit-shrunk; only covariance *estimates* may use `cov_matrix_monthly(..., use_shrinkage=True)` as a parallel diagnostic.
  Rationale: Plan and risk policy — shrinkage stabilizes parameters, not history.
  Date: 2026-05-08.

- Decision: `suitable_robust_optimization_input` is **true** only when both asset and factor scenario covariances are PSD-backed, quality is `usable` or `reliable`, and portfolio 5Y betas exist; still diagnostic-only for v1 (no optimizer wiring).
  Rationale: Conservative flag for future robust optimization without enabling optimization now.
  Date: 2026-05-08.

## Outcomes & Retrospective

Delivered `stress_scenario_analytics_v1` module, JSON contract, CSV exports, tests, and documentation. Future work could add richer episode-specific beta estimation (explicitly out of scope for v1) or reuse more of `factor_covariance` stress regimes per scenario name.

## Context (repository)

- Stress scenarios: [`src/stress.py`](../../src/stress.py) — `SCENARIOS`, `HISTORICAL_EPISODES `, `run_stress`.
- Factor covariance base matrix: [`factor_covariance_analytics`](../../src/stress_factors.py) in `src/stress_factors.py`.
- Beta overlay: [`build_factor_beta_diagnostic_overlay`](../../src/stress_factors.py).
- Report orchestration: [`run_report.py`](../../run_report.py) — call analytics **after** overlay, **before** `export_stress_report`.

## Acceptance

1. `python -m pytest tests/test_stress_scenario_analytics.py -q` passes.
2. `stress_report.json` contains `stress_scenario_analytics.version == "stress_scenario_analytics_v1"` and per-scenario entries for all synthetic + historical episodes.
3. All nine `stress_scenario_*.csv` files exist under `results_csv/` after a report run (when analytics step succeeds).
