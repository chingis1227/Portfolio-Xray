# Stress Testing Specification

**Policy link.** This document is the source of truth for **diagnostic** portfolio stress testing. **Blocking** mandate max drawdown is defined in **docs/production_workflow.md** (full historical sample, **FAIL_MANDATE**).

> **2026-04 update:** Block-level **Role** tests (stagflation / equity-shock defensive bundle) are **removed** from `run_stress`. The suite keeps **Loss**, **RC Top1 / Top3**, historical episodes, and factor diagnostics.

---

## 0. Mandate vs diagnostic suite

| Layer | What | Stops weight release? |
|-------|------|------------------------|
| **Mandate** | Realized portfolio max drawdown on **full overlapping monthly history** vs `target_max_drawdown_pct` | **Yes** → **FAIL_MANDATE** (`run_optimization.py`) |
| **Stress suite** (`run_stress`) | Synthetic scenarios, historical **episodes** (2008 / 2020 / 2022), RC concentration in stress | **No** → **`DIAG_*` codes** and **DIAG_PASS** / **DIAG_PASS_WITH_WARNING** / **DIAG_ATTENTION** only |

Scenario and episode checks below are **for PM reporting**; they do not replace the mandate gate.

---

## 1. Pass criteria (per scenario)

A scenario is treated as **passed** (`pass=true`) only if **all** of the following hold (diagnostic semantics; failure adds **DIAG_*** codes and may set suite status **DIAG_ATTENTION**):

- **Loss test:** Portfolio_PnL_% ≥ -MaxDD_limit (reference limit; informational vs mandate). Violation → **DIAG_LOSS_***.
- **RC test:** Top1_RC_% and Top3_RC_sum_% within caps (§7). Violation → **DIAG_RC_***.

(Legacy §6 **Role** / block-aggregate rules are **not** implemented in production `run_stress`; they are kept below **for archive only** — no **DIAG_ROLE_*** codes are emitted.)

---

## 2. Mandatory scenarios

| # | Scenario            | Description / shocks |
|---|---------------------|----------------------|
| 1 | **Equity shock**    | Broad equity −40%. shock_eq = -0.40; others 0. |
| 2 | **Credit shock**    | HY stress: shock_credit = +0.04 (+400 bps); optionally shock_eq = -0.10; others 0. |
| 3 | **Rates shock**     | Real rates +200 bps: `shock_rr = +0.02`; others 0. |
| 4 | **Inflation/Stagflation** | `shock_cmd = +0.25`, `shock_eq = -0.20`, `shock_rr = +0.005`; `shock_inf`/`shock_usd` = 0 unless extended. |
| 5 | **Liquidity shock** | shock_eq = -0.25, shock_credit = +0.03 (+300 bps); RC uses stress covariance; others 0. |

---

## 3. Scenario PnL (per-asset factors; no portfolio blocks)

For each asset *i* in the risk universe (aligned monthly columns; cash proxy excluded from shock path where applicable):

```
r_i(scenario) = β_eq_i * shock_eq + β_rr_i * shock_rr + β_cr_i * shock_credit
                + β_inf_i * shock_inf + β_usd_i * shock_usd + β_cmd_i * shock_cmd
```

(mapping of shock keys to per-asset beta columns follows `src/stress.py` / asset beta frame: `beta_eq`, `beta_rr`, …)

- **PnL_i** = w_i × r_i (portfolio weights **w** on the same asset set used for the scenario).  
- **Portfolio_PnL_%** = sum_i PnL_i.

**Fallback when per-asset β is missing:** use **equity shock only** — `r_i = shock_eq` (see `_scenario_return_per_asset` in `src/stress.py`). There is **no** separate “block” shock layer for Growth/Duration/Inflation portfolio segments.

---

## 4. Required outputs per scenario

For each scenario the production `run_stress` implementation outputs (see `scenario_results` in `stress_report.json`):

- **portfolio_pnl_pct** (aggregate scenario loss / gain)
- **top1_rc_asset**, **top1_rc_pct**, **top3_rc_assets**, **top3_rc_sum_pct** (RC_vol under base or stress covariance per scenario flags)
- **top3_loss_assets** (tickers with largest negative PnL contribution in the scenario)
- **loss_ok**, **rc1_ok**, **rc3_ok**, **pass**, **diagnostic_codes**

**Legacy / archive:** older specs referred to **PnL_by_block_%**, **defensive_pnl_sum**, and **role_equity_shock_severity**; these are **not** produced by the current asset-level suite. Do not require them for compliance with this spec version.

---

## 5. Loss test (diagnostic)

- **Criterion:** Portfolio_PnL_% ≥ -|MaxDD_limit| (e.g. ≥ -0.15 if MaxDD = -15%).
- If violated → **DIAG_LOSS_*** (diagnostic; does not block release).

---

## 6. Role test (archived — not in `run_stress`)

Historically the spec defined **Role** checks (stagflation “inflation block”, equity-shock “defensive bundle” **S**) using **aggregated PnL by portfolio block**. That layer depended on a **block map** on the portfolio.

**Current code:** `src/stress.py` evaluates only **Loss** (portfolio PnL vs limit) and **RC Top1 / Top3** under stress covariance where enabled. **No** `DIAG_ROLE_*`, **no** `pnl_by_block_pct`, **no** `defensive_pnl_sum` in the reference implementation.

If reintroducing block-level diagnostics, do so in a **separate** spec revision and keep this document’s **§1 / §7** as the binding minimum for the asset-level suite.

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

### 8.2 Serial correlation of factor OLS residuals (`factor_regression_*`)

Each of `factor_regression_5y` / `factor_regression_10y` must include **`serial_correlation_diagnostics`** computed on the **same** OLS residuals as the reported betas (portfolio weekly return ~ intercept + factors, time order preserved).

| Field | Meaning |
|-------|---------|
| `durbin_watson` | Durbin–Watson statistic on the residual series (~2: little first-order serial correlation) |
| `breusch_godfrey` | List of objects, one per lag order `p` in `FACTOR_REGRESSION_BG_LAGS` (`src/stress_factors.py`, default **1, 2, 4**): `lags`, `lm_statistic`, `df_chi2` (= p), `p_value`, `n_aux_observations`, `aux_r_squared` |
| `method`, `h0`, `notes` | Fixed strings describing procedure |

**Breusch–Godfrey:** auxiliary regression of \(\hat u_t\) on intercept, \(X_t\), and \(\hat u_{t-1},\ldots,\hat u_{t-p}\); **LM = T × R²_aux** of that regression; under **H₀** (no serial correlation through lag p), LM → **χ²(p)** (asymptotic).

### 8.3 Robust (HAC / Newey–West) inference for factor betas

Portfolio factor betas are **always** estimated via OLS (same as §8: y = weekly portfolio return, X = weekly factor matrix).
However, when reporting **inference** (standard errors, t-statistics, p-values, confidence intervals), the project must use
**HAC/Newey–West robust standard errors** on the same residual series:

- Kernel: **Bartlett**
- Max lags (weekly): `FACTOR_REGRESSION_HAC_LAGS = 4` (≈ 1 month)

Output convention in each `factor_regression_5y` / `factor_regression_10y`:

- Top-level beta fields (`betas`, classical `t`, `p`, `ci_low`, `ci_high`) correspond to **OLS with classic SE** (`se_type = "classic_ols"`).
- Block `hac_inference`:
  - `se_type`: `"hac_newey_west"`
  - `kernel`: `"bartlett"`
  - `max_lags`: integer (e.g. 4)
  - `se`, `t`, `p`, `ci_low`, `ci_high`: arrays (intercept first, then same factor order as in `betas`).

For reporting and decision rules:

- **Point estimates (β)** are taken from OLS (`betas`).
- **Significance, p-values and confidence intervals in stress reports and PDFs must be interpreted using `hac_inference`**;
  classic OLS t/p are retained for diagnostics only.

### 8.4 OOS episode explainability: β × realized factor shocks

To verify that factor betas explain stress episodes out-of-sample (not only in-sample fit),
`stress_report.json` should include `factor_beta_shock_oos` with per-episode diagnostics:

- Uses the same episode windows as historical validation (`2008`, `2020`, `2022`).
- Realized factor shock for episode = **sum of weekly factor series** over the episode window.
- Model PnL variants:
  - `pnl_model_5y` using `factor_betas_5y`
  - `pnl_model_10y` using `factor_betas_10y`
  - `pnl_model_roll3y_pre` using betas estimated on rolling 3Y window ending right before episode start
- Real benchmark:
  - `pnl_real_episode` from historical episode portfolio return
- Error fields:
  - `abs_error_5y`, `abs_error_10y`, `abs_error_roll3y_pre`
- Summary:
  - mean absolute error by method over episodes with available `pnl_real_episode`.

This block is **diagnostic / non-blocking** and should be shown in stress commentary.

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
- **Stress:** For Equity / Credit / Liquidity scenarios (`stress_cov: true` in `src/stress.py`):
  - **Risk-on set:** all portfolio risk tickers **except the cash proxy** (no Growth/Duration/Inflation block map): pairwise correlations within this set are set to **0.90**, then vol scaling is applied.
  - Pairs involving at least one ticker **outside** that set keep the **base** correlation from Σ_base (see `_stress_covariance`).
  - **Vol scaling:** equity/credit scenarios `vol_mult = 1.25`; liquidity shock `vol_mult = 1.50`.
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
- **primary_diagnostic_code** / **fail_reason_code** (when **DIAG_ATTENTION**): e.g. **DIAG_LOSS_EQUITY_SHOCK**, **DIAG_RC_TOP1_LIQUIDITY_SHOCK**, **DIAG_RC_TOP3_CREDIT_SHOCK**, **DIAG_HIST_2022** (prefix families depend on `_build_diagnostic_code` in `src/stress.py`).
- **diagnostic_codes:** ordered list of all **DIAG_*** issues collected across scenarios and episodes.
- **warning_code** (when **DIAG_PASS_WITH_WARNING**): e.g. **WARN_HIST_BORDERLINE**, **WARN_BETA_NO_LIMITS**, **WARN_DATA_INSUFFICIENT** (see stress module / commentary builders).
- **Report must include:** worst scenario loss; failed scenario (if any); which test failed (**Loss** / **RC_Top1** / **RC_Top3** / **Historical**); Top1/Top3 RC and top loss names; per-episode **vol_annualized_episode**, **volatility_spike_ratio**, **max_dd**, **pnl_real_episode** where computed. **Block-aggregated** mean returns (**mean_monthly_return_by_block_pct**) are **not** part of the current `run_stress` contract.

View After Optimization no longer blocks on stress status; scenario tilt audit codes (**FAIL_STRESS_DURATION**, etc.) remain optional labels for documentation only.
