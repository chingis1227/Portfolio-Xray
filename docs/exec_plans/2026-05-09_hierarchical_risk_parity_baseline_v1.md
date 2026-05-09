# Hierarchical Risk Parity baseline v1 (`hierarchical_risk_parity`)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository contains `PLANS.md` at the repository root. Maintain this document in accordance with `PLANS.md`.

## Purpose / Big Picture

After this change, analysts can run a **canonical Hierarchical Risk Parity (HRP)** baseline alongside Equal-Weight, Risk Parity, Minimum-Variance, and Maximum-Diversification. The user receives long-only weights summing to one on the eligible universe, built from **correlation distance**, **hierarchical clustering**, **quasi-diagonal seriation**, and **recursive bisection** on the same monthly covariance path as constrained MinVar/MaxDiv (`_mv_covariance_for_eligible`), **without** policy box bounds, Young per-name caps as construction constraints, or SLSQP projection. Outputs live under **`hierarchical risk parity portfolio/`** (weights, metadata, full `run_portfolio_report_for_weights` pipeline).

Someone can verify success by running `python run_hierarchical_risk_parity.py` from the repo root and observing new artifacts in that folder plus `python -m pytest tests/test_hrp_weights.py -q` passing.

## Progress

- [x] (2026-05-09) Implemented `src/hrp_weights.py` (distance, linkage with Ward-then-average fallback, recursive bisection).
- [x] (2026-05-09) Wired `build_hierarchical_risk_parity_baseline` in `src/portfolio_variants.py` with metadata export keys.
- [x] (2026-05-09) Added `run_hierarchical_risk_parity.py` and English-only runner messages.
- [x] (2026-05-09) Added `tests/test_hrp_weights.py`; full suite `241 passed`.
- [x] (2026-05-09) Updated `AGENTS.md`, `SPEC.md`; authored this ExecPlan.

## Surprises & Discoveries

- Observation: SciPy `linkage(..., method='ward')` may be numerically fragile on condensed correlation-based distances; implementation tries Ward first, then falls back to `average` and records `hrp_linkage_fallback_from_ward` in diagnostics.
  Evidence: `_linkage_from_condensed` in `src/hrp_weights.py`.

## Decision Log

- Decision: Canonical HRP v1 matches **unconstrained** Risk Parity philosophy—no `_build_bounds`, no optimizer projection.
  Rationale: User requirement to keep HRP comparable as a pure diversification baseline; constrained boxed HRP is out of scope for v1.
  Date/Author: 2026-05-09 / Implementation agent.

- Decision: Reuse `_mv_covariance_for_eligible` for Σ estimation so HRP is comparable to MV/MD on the same covariance stack.
  Rationale: Project plan and SPEC consistency; shrinkage and Young dual covariance still apply to **estimation**, not to explicit per-name weight caps on the HRP construction path.
  Date/Author: 2026-05-09 / Implementation agent.

## Outcomes & Retrospective

v1 ships a runnable baseline script, reusable `hrp_long_only_weights`, integration tests, and documentation hooks in `AGENTS.md` / `SPEC.md`. Optional future work: extend `run_compare_variants.py` to include HRP columns; constrained/projected HRP only if a separate product decision is made.

## Context and Orientation

- **`src/hrp_weights.py`**: pure math (`correlation_from_covariance`, `hrp_long_only_weights`). No I/O.
- **`src/portfolio_variants.py`**: `build_hierarchical_risk_parity_baseline` uses eligible universe + `_mv_covariance_for_eligible`, packs `BaselineWeightsResult`, exports `hierarchical_risk_parity_baseline_metadata_export`.
- **`run_hierarchical_risk_parity.py`**: CLI entry; writes `weights.json`, `baseline_weights_metadata.json`, `weights.txt`, `summary.*`, calls `run_portfolio_report_for_weights`, then `try_rebuild_pdfs_after_variant` like other baselines.

## Plan of Work

Implementation followed additive baseline patterns: new module, new builder, new runner mirroring `run_risk_parity.py` / `run_maximum_diversification.py` structure, tests for numerical sanity, and spec/agent documentation updates.

## Concrete Steps

From the repository root (PowerShell):

    python -m pytest tests/test_hrp_weights.py -q
    python run_hierarchical_risk_parity.py

Expected: tests pass; HRP folder receives report artifacts when data and config allow.

## Validation and Acceptance

- `tests/test_hrp_weights.py` asserts nonnegative weights, sum to one, single-asset edge case, and correlation helper sanity.
- Full `python -m pytest -q` completes with all tests passed (241 passed at acceptance time).
- After a successful run, `hierarchical risk parity portfolio/summary.json` lists `hrp_linkage_method` and stress/metrics summary keys consistent with other baselines.

## Idempotence and Recovery

Re-running `run_hierarchical_risk_parity.py` overwrites the variant folder outputs. Safe to retry; no migrations.

## Artifacts and Notes

- New code: `src/hrp_weights.py`, additions in `src/portfolio_variants.py`, `run_hierarchical_risk_parity.py`, `tests/test_hrp_weights.py`.
- Doc: `AGENTS.md`, `SPEC.md`, this file under `docs/exec_plans/`.

## Interfaces and Dependencies

Public symbols:

- `src/hrp_weights.hrp_long_only_weights(cov: np.ndarray, *, prefer_ward: bool = True) -> tuple[np.ndarray, dict[str, Any]]`
- `src/portfolio_variants.build_hierarchical_risk_parity_baseline(cfg, monthly_returns, analysis_end, window_months) -> BaselineWeightsResult`
- `src/portfolio_variants.hierarchical_risk_parity_baseline_metadata_export`
- Constants: `BASELINE_HRP_LABEL`, `OPTIMIZER_NAME_HIERARCHICAL_RISK_PARITY`

Dependencies: existing `numpy`, `scipy` ( `scipy.cluster.hierarchy`, `scipy.spatial.distance.squareform`); no new packages.

---
Change log: Initial v1 completion 2026-05-09.
