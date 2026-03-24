# Stress Testing Specification

**Policy link.** This document is the source of truth for portfolio stress testing. It implements and extends **docs/portfolio_construction_policy.md** §§9–12 and aligns with **docs/docs/view_after_optimization_spec.md** for stress failure codes.

---

## 1. Pass criteria (per scenario)

A scenario is treated as **passed** (`pass=true`) only if **all** of the following hold:

- **Loss test:** Portfolio_PnL_% ≥ -MaxDD_limit (mandate; no separate stress_limit unless configured). Violation → **FAIL_STRESS**.
- **RC test:** Top1_RC_% and Top3_RC_sum_% within caps (§7). Violation → **FAIL_STRESS**.
- **Role test:** Rules in §6. For **equity shock**, a **severe** defensive breach fails the scenario (**FAIL_STRESS**); a **mild** breach still allows the scenario to pass if Loss and RC pass, but the suite may be **PASS_WITH_WARNING** (§12).

Other scenarios: **Stagflation** Role failure → **FAIL_STRESS** as before.

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

## 5. Loss test

- **Criterion:** Portfolio_PnL_% ≥ -|MaxDD_limit| (e.g. ≥ -0.15 if MaxDD = -15%).
- If violated → **FAIL_STRESS** (Loss).

---

## 6. Role test (minimal rules)

- **Stagflation:** FAIL if PnL_Inflation ≤ 0 (inflation block must be positive in its regime).
- **Equity shock:** Define **S** = PnL_Duration + PnL_Inflation + PnL_Tail (same decimal fraction units as block PnL in §4).
  - **S ≥ 0:** defensive bundle is net supportive → Role **ok** (no suite warning from this rule).
  - **−0.01 ≤ S < 0:** mild aggregate defensive drag (includes the illustrative band **−0.005 … 0**) → Role **warn**; scenario still **passes** if Loss and RC pass; suite status **PASS_WITH_WARNING** with **WARN_ROLE_EQUITY_DEFENSIVE_WEAK** (§12).
  - **S < −0.01:** severe lack of aggregate protection → Role **fail** → scenario **fail** → **FAIL_STRESS** (Role), e.g. **FAIL_ROLE_EQUITY_SHOCK**.

**Loss** and **Top1 / Top3 RC** limits remain **hard** gates: they do not soften when Role is only a warning.

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

If factor limits are set in config and violated → FAIL_STRESS; if no limits → PASS_WITH_WARNING (manual approval).

**Output windows (mandatory):**

- **5Y window (~260 weekly observations, Friday week-ends after inner join):** `factor_betas_5y`
- **10Y window (~520 weekly observations):** `factor_betas_10y`

For backward compatibility, `factor_betas` may be present and should mirror `factor_betas_5y`.

---

## 9. Historical validation

Run portfolio through episodes:

- **2008:** 2007-10-01 → 2009-03-31  
- **2020:** 2020-02-15 → 2020-04-30  
- **2022:** 2021-11-01 → 2022-10-31  

Output: max drawdown, volatility spike, correlations in stress.  
If defensive blocks systematically behave “against role” → FAIL_STRESS; else PASS or PASS_WITH_WARNING.

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

## 12. Final status and report

- **Status:** one of PASS | PASS_WITH_WARNING | FAIL_STRESS.
- **fail_reason_code** (when FAIL_STRESS): specific code, e.g.  
  **FAIL_LOSS_EQUITY_SHOCK**, **FAIL_ROLE_STAGFLATION**, **FAIL_RC_TOP1_LIQUIDITY_SHOCK**, **FAIL_RC_TOP3_CREDIT_SHOCK**, **FAIL_BETA_REAL_RATES**, **FAIL_HIST_2022**.
- **warning_code** (when PASS_WITH_WARNING): e.g. **WARN_ROLE_EQUITY_DEFENSIVE_WEAK**, **WARN_HIST_BORDERLINE**, **WARN_BETA_NO_LIMITS**, **WARN_DATA_INSUFFICIENT**.
- **Report must include:** worst scenario loss; failed scenario (if any); which test failed (Loss / Role / RC / Beta / Historical); Top1/Top3 RC and Top3 loss.

When View After Optimization is used, stress failure must use specific codes: **FAIL_STRESS_DURATION**, **FAIL_STRESS_INFLATION**, **FAIL_STRESS_LIQUIDITY**, (optional) **FAIL_STRESS_TAIL**. The **fail_reason_code** above provides the detailed scenario/test code for audit.
