# Multi-frequency returns for optimization and metrics (`returns_frequency`)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

Repository planning rules live in `PLANS.md` at the repo root; maintain this document in accordance with `PLANS.md`.

## Purpose / Big Picture

Users can set `returns_frequency` in `config.yml` to **`monthly`** (default), **`weekly`**, or **`daily`** so the main investor return panel backing **metrics, optimization inputs, correlation, RC_vol, and `dynamic_nan_safe` backtests** shares one cadence. Weekly uses `W-FRI` aggregation from adjusted daily prices; daily uses trading-day simple returns. Annualization constants are **12 / 52 / 252** via `src/returns_frequency.py`.

The stress engine’s **weekly** factor betas/regressions and **monthly** macro regime labels remain on their production cadences; the run now records **`stress_report.json.frequency_disclosure`** and **`periods_per_year`**, mirrors **`frequency_disclosure`** (and periods) into **`run_metadata.json`**, and extends **`commentary.txt`** / **`stress_commentary.txt`** when cross-cadence warnings apply (default monthly keeps legacy quiet `frequency_mismatch_warning=false`).

Verify with `python -m pytest tests/test_returns_frequency.py -q` after code changes; for regression, `python -m pytest -q`.

## Progress

- [x] (2026-05-08) Implemented `src/returns_frequency.py`, config field + validation, shared loader/cache wiring, calendar windows, optimizer annualization alignment (prior milestones in this worktree).
- [x] (2026-05-08) Threaded frequency through `run_report.py` (`load_monthly_data_shared`, MAR compounding, rolling analytics, inner-join cap scaling, `stress_report.frequency_disclosure`, commentary hooks).
- [x] (2026-05-08) Parameterized `src/portfolio_analytics.py` rolling Sharpe/Sortino/vol for calendar-mapped windows.
- [x] (2026-05-08) Mirrored disclosure into `export_run_metadata` / `run_optimization.py` stress export path; fixed `src/risk_contrib.py` `cov_matrix_monthly_robust` naming regression; reordered `PortfolioConfig.returns_frequency` field to satisfy dataclass defaults.
- [x] (2026-05-08) Baseline and utility scripts pass `returns_frequency` into `load_monthly_data_shared`; added `tests/test_returns_frequency.py`; updated `SPEC.md`, `AGENTS.md`, `config.yml.example`, `docs/docs/stress_testing_spec.md` changelog; filed this ExecPlan.

## Surprises & Discoveries

- Observation: `PortfolioConfig` required `returns_frequency` default to appear **after** required non-default fields (`coverage_threshold`, `output_dir`, …) or Python dataclasses raise `TypeError` during import.
  Evidence: pytest collection failed until the field was moved below `output_dir_final`.

- Observation: `cov_matrix_returns` insertion had left a broken tail in `src/risk_contrib.py`, dropping the `def` name for the MCD helper until restored as `cov_matrix_monthly_robust`.
  Evidence: `ImportError` from `young_etfs_dual_cov` during test collection; fixed and confirmed `from src.risk_contrib import cov_matrix_monthly_robust` succeeds.

## Decision Log

- Decision: Keep `frequency_mismatch_warning` **false** when `returns_frequency == "monthly"` even though factor stress is weekly and macro regimes are monthly.
  Rationale: Preserve legacy quiet reports; non-monthly paths surface explicit disclosure and commentary warnings.
  Date/Author: 2026-05-08 / implementation agent.

- Decision: Resample MAR from annual config with per-period compounding `(1+r_a)^(1/k)-1` via `per_period_eff_from_annual_simple` instead of `r_a/12` for weekly/daily.
  Rationale: Align Sortino MAR grid with the active return frequency without silently biasing downside risk metrics.
  Date/Author: 2026-05-08 / implementation agent.

## Outcomes & Retrospective

Delivered configurable return cadence across report and optimization entry points with explicit frequency disclosure artifacts and documentation. Phase 2 (not in this scope): deeper alignment or gating of stress/regime pipelines when optimization is strictly daily/weekly beyond disclosure.

## Context and Orientation

Primary modules: `src/returns_frequency.py`, `src/data_loader.py`, `src/portfolio_analytics.py`, `run_report.py`, `run_optimization.py`, `src/io_export.py`, `src/portfolio_commentary.py`, `src/config_schema.py`.

## Plan of Work

Completed as summarized in Progress; extend only if product requests tighter factor/regime alignment for non-monthly panels.

## Concrete Steps

From repository root:

    python -m pytest tests/test_returns_frequency.py -q
    python -m pytest -q

## Validation and Acceptance

- `tests/test_returns_frequency.py` passes (normalization, periods mapping, disclosure rules, RF resampling smoke, rolling weekly sanity).
- `stress_report.json` includes `frequency_disclosure` and integer `periods_per_year` after `run_report.py` or `run_optimization.py` stress export.
- `run_metadata.json` includes `frequency_disclosure` (and `periods_per_year` when present on the stress payload) for audit.

## Idempotence and Recovery

Re-running reports overwrites JSON/commentary; cached monthly panels key on `returns_frequency` in `compute_monthly_cache_key`.

## Artifacts and Notes

- `frequency_disclosure` keys: `optimization_frequency`, `returns_frequency`, `factor_stress_frequency`, `macro_regime_frequency`, `frequency_mismatch_warning`, optional `macro_regime_frequency_notes`.

## Interfaces and Dependencies

- `compute_frequency_disclosure`, `normalize_returns_frequency`, `periods_per_year`, `calendar_window_to_n_periods`, `per_period_eff_from_annual_simple`, `rf_series_annual_pct_to_returns_frequency`, `build_levels_and_returns_from_daily_prices` — `src/returns_frequency.py`.
- Constants `FACTOR_STRESS_FREQUENCY_DEFAULT`, `MACRO_REGIME_FREQUENCY_DEFAULT` — same module.
