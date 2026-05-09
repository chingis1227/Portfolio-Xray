# Minimum CVaR baselines (uncapped + constrained) v1

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Initial / Outcomes & Retrospective` should be updated if the feature evolves further.

Repository norms: [PLANS.md](../../PLANS.md) at the repo root.

## Purpose / Big Picture

Users can build two **baseline** portfolios that minimize **historical sample CVaR** (Rockafellar–Uryasev linear program) on **monthly simple returns**, then run the same metrics/stress/report pipeline as other baselines. **Uncapped** uses only `w_i ∈ [0,1]` and `sum w = 1` (no config min/max or Young caps in the LP). **Constrained** uses the same **`_build_bounds`** box as constrained MinVar/MaxDiv. Policy optimizer, mandate gates, and stress pass/fail logic are **unchanged**.

Observable: after implementation, `python run_minimum_cvar_uncapped.py` and `python run_minimum_cvar_constrained.py` write `minimum cvar uncapped portfolio/` and `minimum cvar constrained portfolio/` with `weights.json`, `baseline_weights_metadata.json`, and (on success) full variant reports.

## Progress

- [x] (2026-05-09) Implemented `_minimum_cvar_linprog`, `build_minimum_cvar_uncapped`, `build_minimum_cvar_constrained` in `src/portfolio_variants.py`.
- [x] (2026-05-09) Added `minimum_cvar_confidence_level` to `PortfolioConfig` / `validate_config` / `config.yml.example`.
- [x] (2026-05-09) Added CLI scripts and `mv_dirs` PDF entries; updated `AGENTS.md`, `SPEC.md`.
- [x] (2026-05-09) Added `tests/test_minimum_cvar_baseline.py`; full suite **255 passed**.

## Surprises & Discoveries

- Observation: With **symmetric** per-asset max caps, you cannot simultaneously have `sum of max ≥ 1` (feasible simplex) and `1/N > max` (equal-weight infeasible) for identical caps across `N` assets. Tests use **infeasible box** (`sum max < 1`) or compare uncapped vs constrained max weight instead of “EW infeasible in box” for symmetric caps.
  Evidence: `FAIL_INFEASIBLE_BOUNDS` when `max_w=0.25` for three assets (`3*0.25<1`).

## Decision Log

- Decision: Use **`scipy.optimize.linprog`**, `method="highs"`, no new dependencies.
  Rationale: Matches project stack; LP is the standard Rockafellar–Uryasev formulation. Date: 2026-05-09.

- Decision: Variable order **`[w..., alpha, z...]`**; inequalities as `-R_t·w - alpha - z_t ≤ 0`.
  Rationale: Consistent HiGHS `A_ub @ x <= b_ub` form. Date: 2026-05-09.

- Decision: **`tail_scenarios_used`** lists scenarios with **`z_t`** above a small threshold tied to `max(z)`.
  Rationale: Practical proxy for LP-active tail constraints; documented in metadata. Date: 2026-05-09.

- Decision: **`empirical_cvar_loss`** in metadata uses **mean of worst `ceil(T*(1-gamma))` losses** `L_t = -(Rw)_t` for reporting, separate from the LP objective value.
  Rationale: Discrete sample CVaR common in reporting; avoids conflating `alpha + λΣz` with a single Monte Carlo definition. Date: 2026-05-09.

## Outcomes & Retrospective

Delivered two baselines, shared LP core, config field **`minimum_cvar_confidence_level`** (default `0.95`), PDF suite entries, documentation updates, and **9** focused tests (full run **255 passed**). No changes to `run_optimization.py` or stress mandate logic.

## Context and Orientation

- Core: [`src/portfolio_variants.py`](../../src/portfolio_variants.py) — `_minimum_cvar_linprog`, builders, `minimum_cvar_baseline_metadata_export`.
- Bounds: [`src/optimization.py`](../../src/optimization.py) `_build_bounds` for constrained variant only.
- Data: [`load_monthly_data_shared`](../../src/data_loader.py) → **`monthly_returns`**; scenarios aligned with [`_mv_covariance_for_eligible`](../../src/portfolio_variants.py) column/window order.
- CLI: [`run_minimum_cvar_uncapped.py`](../../run_minimum_cvar_uncapped.py), [`run_minimum_cvar_constrained.py`](../../run_minimum_cvar_constrained.py).
- PDF: [`src/pdf_reports.py`](../../src/pdf_reports.py) `mv_dirs` tuples for both folders.

## Plan of Work

Implementation followed the approved dual-variant spec: uncapped `[0,1]` per asset without project caps; constrained project box; metadata keys including `cvar_objective_value`, `linprog_status`, `tail_effective_obs`, `tail_scenarios_used`, and constrained-only `bounds_used` / `constraint_summary`.

## Concrete Steps

From repository root:

    python -m pytest tests/test_minimum_cvar_baseline.py -q
    python -m pytest -q

Optional (requires data/network):

    python run_minimum_cvar_uncapped.py
    python run_minimum_cvar_constrained.py

## Validation and Acceptance

- `pytest tests/test_minimum_cvar_baseline.py` — all passed in CI/local run.
- Full `pytest` — **255 passed** (2026-05-09).

## Idempotence and Recovery

Re-running CLI overwrites the corresponding output folder. Safe to retry after partial failure.

## Artifacts and Notes

- Optimizer names: `minimum_cvar_uncapped`, `minimum_cvar_constrained`.
- Solver label in metadata: `HiGHS`.

## Interfaces and Dependencies

- `build_minimum_cvar_uncapped(cfg, monthly_returns, analysis_end, window_months, *, confidence_level=None)`
- `build_minimum_cvar_constrained(...)`
- `_minimum_cvar_linprog(R, gamma, w_bounds, scenario_dates=None)` → dict with `ok`, `w`, `cvar_objective_value`, tail fields, or failure reason.

Revision note (2026-05-09): ExecPlan filed post-implementation to close documentation milestone; code is source of truth for details.
