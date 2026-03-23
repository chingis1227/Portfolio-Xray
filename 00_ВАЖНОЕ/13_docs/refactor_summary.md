# Portfolio construction refactor — summary

Refactor aligns implementation with the intended policy logic. Below: target architecture, files changed, and what is now **hard constraint**, **soft/diagnostic**, or **report-only**.

---

## 1. Target architecture (high level)

- **Single application of client profile**: Profile is applied once in `load_validated_config()` (config load). CLI `--profile` applies via `apply_profile_override(cfg, profile_id)` without re-reading the config file. `target_vol_annual` and `rc_block_targets` are derived only once.
- **Block selection hook**: `apply_block_selection(blocks, config, monthly_returns)` in `src/block_selection.py` runs before risk-budget optimization. Currently a pass-through; full Duration/Inflation candidate selection and mix logic belong here.
- **Optimization flow**: Load config → (optional) apply_profile_override → load data → apply_block_selection → run_risk_budget_optimization → ProLiquidity → diagnostics (RC by block, RB corridor, stress, RC breaches) → always write weights + run_result.json (status APPROVED | CANDIDATE_RB_BREACH | OK_FALLBACK) unless FAIL_DATA; then run report.
- **NaN-safe backtest**: Within-block equal redistribution first; then RC-gated (and optionally RB-gated) check; if violated, fallback to w_miss-to-cash for that month. Single liquidity framework: `liquidity_need_total = liquidity_need_months * monthly_expenses`, `liquidity_floor_pct = liquidity_need_total / portfolio_value`.

---

## 2. Files changed

| File | Changes |
|------|--------|
| **run_optimization.py** | Single `apply_profile_override(cfg, args.profile)`. Production workflow: RB corridor is quality gate (APPROVED vs CANDIDATE_RB_BREACH); Stress and MaxDD are warning-only; RC cap violations flagged but weights returned. Always write weights + run_result.json unless FAIL_DATA. Call to `apply_block_selection` before `run_risk_budget_optimization`. |
| **run_report.py** | `portfolio_returns_nan_safe` called with `blocks`, `rc_block_targets`, `rc_asset_cap_pct`, `cov_df`. `portfolio_valid` from MaxDD written to run metadata; no exit(1) when invalid (production workflow). |
| **src/config.py** | `apply_profile_override(cfg, profile_id)` added; imports `normalize_rc_block_targets`. |
| **src/config_schema.py** | `liquidity_need` is derived (`liquidity_need_months * monthly_expenses`). Comment: `target_nominal_return_annual` is report-only (comparison with realized CAGR). |
| **src/optimization.py** | `RB_CORRIDOR_PP = 0.05`, `rc_by_block_from_weights()`, `check_rb_corridor()`. Used in run_optimization for status/violations (quality gate, not exit). |
| **src/block_selection.py** | **New.** Stub `apply_block_selection(blocks, config, monthly_returns)` returning blocks unchanged; docstring describes future Duration/Inflation logic. |
| **src/portfolio_dynamic.py** | Within-block equal redistribution; optional RC-gated (and RB corridor) check with fallback to w_miss-to-cash. New params: `blocks`, `rc_block_targets`, `rc_asset_cap_pct`, `cov_df`. Backward compatible when `blocks` is None. |
| **src/io_export.py** | `export_run_metadata(..., portfolio_valid=None)`; writes `portfolio_valid` into run metadata. |
| **src/snapshot.py** | Module docstring: hard vs soft vs report-only constraints. |
| **config.yml** | Comment: liquidity_need derived; single liquidity framework (months × expenses, liquidity_floor_pct). |

---

## 3. Production workflow (quality gates, not hard stops)

- **Only hard stop**: FAIL_DATA (invalid config, missing/NaN data, covariance not computable). Weights are always written in all other cases.
- **RB corridor**: Quality check; realized block RC vs target ± 5 pp. If outside corridor → status = CANDIDATE_RB_BREACH, violation flag RB_BREACH with per-block deltas; weights still written.
- **Stress Judge**: Warning-only; if FAIL_STRESS → violation flag FAIL_STRESS with failed scenarios; weights still written; next_actions suggest e.g. increase liquidity, shorten duration.
- **RC caps**: Preferred enforcement; if solver uses fallback and per-asset RC is violated → status OK_FALLBACK, violation flag VIOL_RC_ASSET_CAP with tickers + RC + cap; weights still returned.
- **Max DD**: Diagnostic; if realized max drawdown exceeds mandate → violation flag MAX_DD_BREACH; weights still written.

---

## 4. Soft / diagnostic (no pipeline stop)

- Baseline coverage (sanity check; not used for allocation).
- RC caps and weight caps snapshots in `constraints_status`.
- RB corridor and target_vol in snapshot (informational after optimization).

---

## 5. Report-only (no constraint role)

- **target_nominal_return_annual**: Used only for comparison with realized CAGR in metadata and reports. Not an optimization constraint.
- **liquidity_need**: Derived from `liquidity_need_months * monthly_expenses`; not a standalone input. Portfolio logic uses months and monthly_expenses only.
- **liquidity_floor_pct** in client profiles: Hint/report-only; can be mapped to the single liquidity framework later.

---

## 6. Preserved behaviour

- FX handling, investor currency conversion.
- RC_vol logic, ddof=1.
- RC caps, HY/EM subcaps.
- Feasibility checks, ProLiquidity, Alpha Shift.
- Config schema validation and existing field set (with liquidity derived and comments for report-only).

---

## 7. Deliverables checklist

- [x] Identify files to change.
- [x] Describe target architecture.
- [x] Implement refactor (profile once, RB corridor, gatekeepers, block selection hook, NaN-safe with within-block + RC-gated fallback, liquidity derived, metadata portfolio_valid and target comparison).
- [x] Remove duplicate / misleading logic (double profile application, standalone liquidity_need as input).
- [x] Update config schema and validation (liquidity derived; report-only comments).
- [x] Mark hard constraint vs soft diagnostic vs report-only in code and docs.
- [x] Summarize changes (this document).
- [x] **Production workflow**: Code and policy docs describe the same behaviour — only FAIL_DATA stops; RB corridor, Stress, RC caps are quality/warning flags; weights always written; run_result.json carries status, violations, next_actions (single source of truth).
