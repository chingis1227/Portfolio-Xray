# Portfolio Construction Policy

## 1. System principle

Portfolios are built from a **single list of tickers** in `config.yml`.

`config/etf_universe.yml` is a taxonomy and diagnostics source only. In V1 it annotates and validates the active `config.yml` ticker list, writes `etf_universe_validation.json`, and reports duplicate/canonical/unknown-ticker warnings. It does **not** select the optimizer universe, change weights, or replace data coverage and young-ETF eligibility rules.

Optimization chooses weights that **maximize expected return** (sample mean of monthly simple returns on the primary window) subject to:

- long-only, weights sum to 1;
- minimum weight per held asset (`min_single_security_weight_pct` when set);
- optional **max single name** weight (uniform cap by **N** and optional override — see `feasibility_constraints_spec.md`);
- **liquidity floor** and **cash policy** via ProLiquidity (see below);
- soft penalties vs **target_vol_annual** and **target_nominal_return_annual** (optimizer objective).

Stress testing and factor diagnostics are **non-binding** except where explicitly noted; the **mandate gate** on historical max drawdown can prevent writing weights.

---

## 2. Client profile

`client_profile` (Ultra Conservative … Aggressive) fills **targets only**:

- `target_vol_annual`
- `target_max_drawdown_pct` (mandate check on full overlapping history)
- `target_nominal_return_annual` (soft objective / reporting; not a hard constraint)
- `liquidity_floor_pct` (or derived from expenses × months / portfolio value)
- optional `min_single_security_weight_pct`

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
- **Young / short-history ETFs:** optional dual covariance (`young_etf_optimization_policy`).
- **Covariance:** sample monthly covariance; optional Ledoit–Wolf shrinkage via `covariance_shrinkage`.

---

## 6. NaN-safe backtest

Dynamic backtest uses **global equal redistribution** among risk tickers for missing monthly returns; any weight not placed on assets with an observed return for that month earns the **cash proxy** return (`w_miss` rule). See `data_policy_spec.md`.

---

## 7. Stress testing (diagnostic)

Synthetic scenarios, historical episodes, RC Top1/Top3 as reported numbers — **DIAG_*** codes apply to **loss** and **historical** checks only; they do not prevent release. Mandate MaxDD is enforced in `run_optimization.py`. See `stress_testing_spec.md`.

---

## 8. PM view after optimization

Deterministic **tactical** tilts per `view_after_optimization_spec.md`: funding from **highest RC_vol donors** among other names; gates: weights, vol, MaxDD; stress output remains diagnostic only.

---

## 9. Feasibility

Feasibility is based on **weight bounds** and data coverage.

---

## 10. No manual final weights

Final weights come from optimization (+ ProLiquidity / vol policy). PM tilts only through the view-after protocol.

This rule applies to **policy weights**. It does not prohibit user-supplied `current_weights` in `analysis_mode=analyze_current_weights`, because those weights represent an existing portfolio for diagnostics and fixed-weight reporting. Input-mode semantics are governed by [input_assumptions_spec.md](input_assumptions_spec.md).

---

## 11. Risk budgeting and other benchmark baselines (non-policy)

Scripts such as **`run_risk_budget_by_asset_class.py`** and **`run_risk_budget_by_asset.py`** construct **long-only, fully invested** weights for **comparison and diagnostics** only. They **do not** implement the client mandate optimizer, **do not** apply ProLiquidity overlays, and **do not** change stress **pass/fail** or weight-release rules—they run the same metrics/stress/report pipeline as other baselines after weights are fixed.

- **Class-level risk budgeting** matches **aggregated** percentage contributions to variance (per `metrics_specification.md` / static **Σ**) across **risk budget buckets** to targets in **`risk_budgeting`** (presets or manual `targets`). Taxonomy for buckets is the merged **`config/etf_universe.yml`** then **`config/stock_universe.yml`** record set, with sub-buckets inferred from row fields in code (`src/risk_budgeting.py`).
- **Per-asset risk budgeting** requires **`risk_budgeting.asset_targets`** summing to 1 over **every eligible** ticker; it uses **Spinu’s** risk-budget CCD with unequal `b_i` and an **SLSQP** fallback.

For the main portfolio, **§10** still applies: normal production weights come from **`run_optimization.py`** (and view-after where used), not from these baselines.
