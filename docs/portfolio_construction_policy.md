# Portfolio Construction Policy (no structural blocks)

## 1. System principle

Portfolios are built from a **single list of tickers** in `config.yml`. There are **no** Growth / Duration / Inflation blocks and **no** risk-budget targets between abstract sectors.

Optimization chooses weights that **maximize expected return** (sample mean of monthly simple returns on the primary window) subject to:

- long-only, weights sum to 1;
- minimum weight per held asset (`min_single_security_weight_pct` when set);
- optional **max single name** weight (uniform cap by **N** and optional override — see `docs/docs/feasibility_constraints_spec.md`);
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

## 3. RC_vol (diagnostic only)

- RC_vol is **percentage contribution to portfolio variance** on the estimation window, computed as in `metrics_specification.md`.
- It is **reported** in metrics, stress scenarios (Top1 / Top3), and commentary — **not** a hard constraint, objective penalty, or post-processing gate in the optimization pipeline.

---

## 4. Liquidity and cash

- **Life liquidity floor:** minimum cash (cash proxy, e.g. BIL) from profile/config.
- **Vol-scaling cash:** when `cash_policy` allows, cash rises so that estimated annual vol moves toward `target_vol_annual`.
- **Cash prohibited:** alpha-shift toward target vol without cash (see `src/optimization.py`).

---

## 5. Optimization engine

- **Single stage:** `run_max_return_optimization` — `max_return` (default) or `risk_parity` for diagnostics.
- **Young / short-history ETFs:** optional dual covariance (`young_etf_optimization_policy`); no block-based thresholds.
- **Covariance:** sample monthly covariance; optional Ledoit–Wolf shrinkage via `covariance_shrinkage`.

---

## 6. NaN-safe backtest

Dynamic backtest uses **global equal redistribution** among risk tickers for missing monthly returns; any weight not placed on assets with an observed return for that month earns the **cash proxy** return (`w_miss` rule). See `docs/data_policy_nan_young_etfs.md`.

---

## 7. Stress testing (diagnostic)

Synthetic scenarios, historical episodes, RC Top1/Top3 as reported numbers — **DIAG_*** codes apply to **loss** and **historical** checks only; they do not block release. Mandate MaxDD is enforced in `run_optimization.py`. See `docs/docs/stress_testing_spec.md`.

---

## 8. PM view after optimization

Deterministic **tactical** tilts per `docs/docs/view_after_optimization_spec.md`: funding from **highest RC_vol donors** among other names; gates: weights, vol, MaxDD; stress output remains diagnostic only.

---

## 9. Feasibility

Structural RB achievability checks are **removed**. Feasibility reduces to **weight bounds** and data coverage.

---

## 10. No manual final weights

Final weights come from optimization (+ ProLiquidity / vol policy). PM tilts only through the view-after protocol.
