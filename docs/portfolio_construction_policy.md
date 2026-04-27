# Portfolio Construction Policy (no structural blocks)

## 1. System principle

Portfolios are built from a **single list of tickers** in `config.yml`. There are **no** Growth / Duration / Inflation blocks and **no** risk-budget targets between abstract sectors.

Optimization chooses weights that **maximize expected return** (sample mean of monthly simple returns on the primary window) subject to:

- long-only, weights sum to 1;
- minimum weight per held asset (`min_single_security_weight_pct` when set);
- **per-asset RC_vol cap** (share of portfolio variance — see `metrics_specification.md`);
- optional **max single name** weight;
- **liquidity floor** and **cash policy** via ProLiquidity (see below);
- soft penalties vs **target_vol_annual** and **target_nominal_return_annual** (optimizer objective).

Stress testing and factor diagnostics are **non-blocking** except where explicitly noted; the **mandate gate** on historical max drawdown can block writing weights.

---

## 2. Client profile

`client_profile` (Ultra Conservative … Aggressive) fills **targets only**:

- `target_vol_annual`
- `target_max_drawdown_pct` (mandate check on full overlapping history)
- `target_nominal_return_annual` (soft objective / reporting; not a hard constraint)
- `liquidity_floor_pct` (or derived from expenses × months / portfolio value)
- optional `min_single_security_weight_pct`

There is **no** `risk_budget` or `rc_block_targets`.

---

## 3. RC_vol and caps

- RC_vol is **percentage contribution to portfolio variance** on the estimation window, computed as in `metrics_specification.md`.
- **Per-asset cap:** either explicit `rc_asset_cap_pct` or the global formula in `docs/docs/feasibility_constraints_spec.md` §1 from the number of risk assets `N`.
- **Post-processing:** iterative reduction of weights that violate RC caps may reallocate to liquid core names; `rc_policy_mode` strict vs permissive controls whether weights are written if violations remain.

---

## 4. Liquidity and cash

- **Life liquidity floor:** minimum cash (cash proxy, e.g. BIL) from profile/config.
- **Vol-scaling cash:** when `cash_policy` allows, cash rises so that estimated annual vol moves toward `target_vol_annual`.
- **Cash prohibited:** alpha-shift toward target vol without cash (see `src/optimization.py`).

**Tail overlay (optional):** `tail_target_weight_pct` reserved for tail ETFs listed in code (`VIXY`, `UVXY`, `SVXY`) if present in `tickers`.

---

## 5. Optimization engine

- **Single stage:** `run_risk_budget_optimization` — `max_return` (default) or `risk_parity` for diagnostics.
- **Young / short-history ETFs:** optional dual covariance (`young_etf_optimization_policy`); no block-based thresholds.
- **Covariance:** sample monthly covariance; optional Ledoit–Wolf shrinkage via `covariance_shrinkage`.

---

## 6. NaN-safe backtest

Dynamic backtest uses **global equal redistribution** among risk tickers for missing monthly returns, then optional **RC-gated** fallback to simple “missing weight to cash” for that month. See `docs/data_policy_nan_young_etfs.md`.

---

## 7. Stress testing (diagnostic)

Synthetic scenarios, historical episodes, per-asset RC concentration checks — **DIAG_*** codes only; they do not block release. Mandate MaxDD is enforced in `run_optimization.py`. See `docs/docs/stress_testing_spec.md`.

---

## 8. PM view after optimization

Deterministic tilts per `docs/docs/view_after_optimization_spec.md` (updated): funding from **highest RC donors** among other names; gates: weights, vol, MaxDD, RC caps; stress diagnostic only.

---

## 9. Feasibility

Structural RB achievability checks are **removed**. Feasibility reduces to **weight bounds**, **RC formula**, and data coverage.

---

## 10. No manual final weights

Final weights come from optimization (+ ProLiquidity + optional tail overlay + RC post-process). PM tilts only through the view-after protocol.
