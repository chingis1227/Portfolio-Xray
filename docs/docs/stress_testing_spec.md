# Stress Testing Specification

**Policy link.** This document is the source of truth for **diagnostic** portfolio stress testing. It implements and extends **docs/portfolio_construction_policy.md** §§9–12. **Blocking** mandate max drawdown is defined in **docs/production_workflow.md** (full historical sample, **FAIL_MANDATE**).

---

## 0. Mandate vs diagnostic suite

| Layer | What | Blocks weights? |
|-------|------|-----------------|
| **Mandate** | Realized portfolio max drawdown on **full overlapping monthly history** vs `target_max_drawdown_pct` | **Yes** → **FAIL_MANDATE** (`run_optimization.py`) |
| **Stress suite** (`run_stress`) | Synthetic scenarios, historical **episodes** (2008 / 2020 / 2022), Role/RC in stress | **No** → **`DIAG_*` codes** and **DIAG_PASS** / **DIAG_PASS_WITH_WARNING** / **DIAG_ATTENTION** only |

Scenario and episode checks below are **for PM reporting**; they do not replace the mandate gate.

---

## 1. Pass criteria (per scenario)

A scenario is treated as **passed** (`pass=true`) only if **all** of the following hold (diagnostic semantics; failure adds **DIAG_*** codes and may set suite status **DIAG_ATTENTION**):

- **Loss test:** Portfolio_PnL_% ≥ -MaxDD_limit (reference limit; informational vs mandate). Violation → **DIAG_LOSS_***.
- **RC test:** Top1_RC_% and Top3_RC_sum_% within caps (§7). Violation → **DIAG_RC_***.
- **Role test:** Rules in §6. For **equity shock**, a **severe** defensive breach fails the scenario (**DIAG_ROLE_***); a **mild** breach still allows the scenario to pass if Loss and RC pass, but the suite may be **DIAG_PASS_WITH_WARNING** (§12).

Other scenarios: **Stagflation** Role failure → **DIAG_ROLE_*** as before.

---

## 2. Mandatory scenarios

| # | Scenario            | Description / shocks |
|---|---------------------|----------------------|
| 1 | **Equity shock**    | Broad equity −40%. shock_eq = -0.40; others 0. |
| 2 | **Credit shock**    | HY stress: shock_credit = +0.04 (+400 bps); optionally shock_eq = -0.10; others 0. |
| 3 | **Rates shock**     | Real rates +200 bps: shock_real_rates = +0.02; others 0. |
| 4 | **Inflation/Stagflation** | shock_cmd = +0.25, shock_eq = -0.20; optionally shock_real_rates = +0.005; others 0. |
| 5 | **Liquidity shock** | shock_eq = -0.25, shock_credit = +0.03 (+300 bps); RC uses stress covariance; others 0. |

---

## 3. Scenario PnL (factor-based with block fallback)

For each asset *i*:

```
r_i(scenario) = β_eq_i * shock_eq + β_rr_i * shock_real_rates + β_cr_i * shock_credit
                + β_inf_i * shock_infl + β_usd_i * shock_usd + β_cmd_i * shock_cmd
```

- **PnL_i** = w_i × r_i  
- **PnL_block** = sum(PnL_i for i in block)  
- **Portfolio_PnL** = sum(PnL_i)

**Fallback when β is missing for an asset:** apply block-level shock: Growth → shock_eq; Duration → shock_real_rates (or duration proxy); Inflation → shock_cmd (e.g. Gold/commodities); Liquidity → 0; Tail → scenario-specific or block rule.

---

## 4. Required outputs per scenario

For each scenario the system must output:

- **Portfolio_PnL_%**
- **PnL_by_block_%:** Growth, Duration, Inflation, Liquidity, Tail (Growth_HY and Growth_EM_debt aggregated into Growth)
- **Top1_RC_asset**, **Top1_RC_%**
- **Top3_RC_assets**, **Top3_RC_sum_%**
- **Top3_loss_assets** (assets with largest loss contribution by PnL)
- **equity_shock only:** `defensive_pnl_sum` = PnL_Duration + PnL_Inflation + PnL_Tail (decimal fractions, same units as `pnl_by_block_pct`); `role_equity_shock_severity` = `ok` | `warn` | `fail` (§6).

---

## 5. Loss test (diagnostic)

- **Criterion:** Portfolio_PnL_% ≥ -|MaxDD_limit| (e.g. ≥ -0.15 if MaxDD = -15%).
- If violated → **DIAG_LOSS_*** (diagnostic; does not block release).

---

## 6. Role test (minimal rules)

- **Stagflation:** FAIL if PnL_Inflation ≤ 0 (inflation block must be positive in its regime).
- **Equity shock:** Define **S** = PnL_Duration + PnL_Inflation + PnL_Tail (same decimal fraction units as block PnL in §4).
  - **S ≥ 0:** defensive bundle is net supportive → Role **ok** (no suite warning from this rule).
  - **−0.01 ≤ S < 0:** mild aggregate defensive drag (includes the illustrative band **−0.005 … 0**) → Role **warn**; scenario still **passes** if Loss and RC pass; suite status **PASS_WITH_WARNING** with **WARN_ROLE_EQUITY_DEFENSIVE_WEAK** (§12).
  - **S < −0.01:** severe lack of aggregate protection → Role **fail** → scenario **fail** → **DIAG_ROLE_***, e.g. **DIAG_ROLE_EQUITY_SHOCK**.

**Loss** and **Top1 / Top3 RC** (diagnostic) do not soften when Role is only a warning; failed checks add **DIAG_*** codes. They are **not** production hard gates (see §0).

---

## 7. RC test (concentration in stress)

- **Top1:** FAIL if Top1_RC_% > RC_asset_cap (RC_asset_cap from config or feasibility formula).
- **Top3:** FAIL if Top3_RC_sum_% > stress_top3_rc_sum_cap (default 0.70 = 70%).

RC in stress is computed using **stress covariance** (see §10).

---

## 8. Factor validation (output only; limits optional in config)

The system must estimate and output:

- β_equity (portfolio vs S&P)
- β_real_rates (portfolio vs Δ10Y real yield)
- β_inflation (portfolio vs inflation surprise proxy)
- β_credit (portfolio vs credit spread)
- β_USD (portfolio vs DXY)

If factor limits are set in config and violated → **DIAG_BETA_*** / **DIAG_ATTENTION**; if no limits → **DIAG_PASS_WITH_WARNING** (manual review). (Non-blocking.)

**Output windows (mandatory):**

- **5Y window (~260 weekly observations, Friday week-ends after inner join):** `factor_betas_5y`
- **10Y window (~520 weekly observations):** `factor_betas_10y`

For backward compatibility, `factor_betas` may be present and should mirror `factor_betas_5y`.

### 8.1 Factor multicollinearity (`factor_regression_*` only)

Portfolio weekly OLS in `factor_regression_5y` / `factor_regression_10y` must include **`factor_multicollinearity`** on the **same regressor rows** as the regression (after inner join and `valid` mask).

| Output field | Meaning |
|--------------|---------|
| `correlation` | Nested Pearson correlation matrix of factor columns |
| `pairwise_correlations` | All unordered pairs with `rho`, sorted by \|ρ\| descending |
| `cond_correlation_matrix` | cond(R) = λ_max / λ_min (eigvalsh on R; λ_min clipped at 1e-15); `null` if singular |
| `cond_correlation_matrix_singular` | Boolean if cond not finite |
| `vif_by_factor` | Classical VIF via auxiliary OLS (raw-scale X); `null` for a factor if VIF infinite |
| `max_vif`, `max_vif_factor`, `max_vif_is_infinite` | Summary |
| `strongest_pair` | Pair with largest \|ρ\| |
| `severity` | `low` \| `moderate` \| `high` \| `unknown` — see rules below |
| `assessment_ru` | Short Russian sentence for reports |

**Severity rules (fixed in code, `src/stress_factors.py`):**

- **high** if `max_vif_is_infinite` **or** max VIF ≥ 10 **or** cond(R) ≥ 80 **or** max \|ρ\| among pairs ≥ 0.95  
- else **moderate** if max VIF ≥ 5 **or** cond(R) ≥ 30 **or** max \|ρ\| ≥ 0.85  
- else **low**

**Note:** cond([1, X]) on raw units is **not** reported (misleading across scales); use **cond(correlation matrix)** and VIF.

---

## 9. Historical validation

Run portfolio through episodes:

- **2008:** 2007-10-01 → 2009-03-31  
- **2020:** 2020-02-15 → 2020-04-30  
- **2022:** 2021-11-01 → 2022-10-31  

Output: max drawdown, volatility spike, correlations in stress.  
Episode DD vs limit adds **DIAG_HIST_*** when breached; else episode contributes to **DIAG_PASS**. (Non-blocking.)

---

## 10. Stress covariance (for RC in stress)

- **Base:** Σ_base from project returns (monthly, ddof=1).
- **Stress:** For Equity / Credit / Liquidity scenarios:
  - Within risk-on basket (Growth + Growth_HY + Growth_EM_debt + Crypto if any): set **corr = 0.90**.
  - Between risk-on and defense (Duration, Inflation): keep base correlations; for Liquidity shock optionally raise to min(0.50, base+0.20).
  - **Vol scaling:** equity/credit scenarios vol_mult = 1.25; liquidity shock vol_mult = 1.50.
- RC is computed on **current portfolio weights** using Σ_stress.

---

## 11. Factor data sources (FRED + fallback)

- **Equity (S&P):** FRED:SP500 or ETF proxy SPY (total return preferred).
- **10Y real yield:** FRED:DFII10; use Δ(DFII10).
- **Inflation surprise:** FRED:T10YIE; use Δ(T10YIE) as proxy.
- **Credit spread (HY):** FRED:BAMLH0A0HYM2; use Δ(spread).
- **USD:** FRED:DTWEXBGS; use Δ or % change.

Betas: **weekly** changes/returns for reporting outputs in §8 (`factor_betas_5y`, `factor_betas_10y`), with synchronized week-end dates (inner join), ending at **analysis_end**. Windows: **260 weeks (5Y)** and **520 weeks (10Y)** (see `src/stress_factors.py`: `FACTOR_WEEKS_5Y`, `FACTOR_WEEKS_10Y`). Use project series when available; FRED codes as fallback.

---

## 12. Final status and report (diagnostic suite)

- **Status:** **DIAG_PASS** | **DIAG_PASS_WITH_WARNING** | **DIAG_ATTENTION** (legacy **PASS** / **PASS_WITH_WARNING** may appear in old JSON).
- **primary_diagnostic_code** / **fail_reason_code** (when **DIAG_ATTENTION**): e.g. **DIAG_LOSS_EQUITY_SHOCK**, **DIAG_ROLE_STAGFLATION**, **DIAG_RC_TOP1_LIQUIDITY_SHOCK**, **DIAG_RC_TOP3_CREDIT_SHOCK**, **DIAG_BETA_REAL_RATES**, **DIAG_HIST_2022**.
- **diagnostic_codes:** ordered list of all **DIAG_*** issues collected across scenarios and episodes.
- **warning_code** (when **DIAG_PASS_WITH_WARNING**): e.g. **WARN_ROLE_EQUITY_DEFENSIVE_WEAK**, **WARN_HIST_BORDERLINE**, **WARN_BETA_NO_LIMITS**, **WARN_DATA_INSUFFICIENT**.
- **Report must include:** worst scenario loss; failed scenario (if any); which test failed (Loss / Role / RC / Beta / Historical); Top1/Top3 RC and Top3 loss; per-episode **vol_annualized_episode**, **mean_monthly_return_by_block_pct** where computed.

View After Optimization no longer blocks on stress status; scenario tilt audit codes (**FAIL_STRESS_DURATION**, etc.) remain optional labels for documentation only.
