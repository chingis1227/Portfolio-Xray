# Stress Testing Specification

**Policy link.** This document is the source of truth for **diagnostic** portfolio stress testing. **Blocking** mandate max drawdown is defined in **docs/production_workflow.md** (full historical sample, **FAIL_MANDATE**).

> **2026-04-27 update:** Synthetic **pass** = **Loss (portfolio PnL vs mandate MaxDD)** only.
> **2026-04-28 update:** **RC Top1 / Top3** (`top1_rc_pct`, `top3_rc_sum_pct`, tickers) remain on each scenario row as **numeric diagnostics only** вЂ” no `rc1_ok` / `rc3_ok`, no `rc_diagnostic_codes`, no `rc_attention_codes`, no suite status change for RC-only patterns. Historical episode contract unchanged (episode max DD vs mandate). **dotcom** episode is in the historical list (see В§9).
> **2026-04-28 update:** Add **Recession severe** (`recession_severe`) as a hard-landing synthetic scenario. Its shock vector is calibrated from realized weekly factor moves in the existing **2008** and **2020** historical windows, selecting the episode with the worst model PnL for the current portfolio betas.
> **2026-04-28 update:** Portfolio factor regressions include **Breusch-Pagan** heteroskedasticity diagnostics on the same OLS residuals/rows as the reported factor betas.
> **2026-04-28 update:** Factor analytics now use a **nine-factor** weekly registry (`equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, `us_growth`, `oil`). Synthetic stress scenarios and recession calibration remain a **six-shock** engine and only map the first six factors into `shock_*` keys.
> **2026-04-29 update:** Historical stress rows now include **model-based factor attribution** when factor history is available. The primary attribution uses 5Y portfolio betas times realized episode factor shocks and must be labeled as model-based explainability, not pure realized causal decomposition.

---

## 0. Mandate vs diagnostic suite

| Layer | What | Stops weight release? |
|-------|------|------------------------|
| **Mandate** | Realized portfolio max drawdown on **full overlapping monthly history** vs `target_max_drawdown_pct` | **Yes** в†’ **FAIL_MANDATE** (`run_optimization.py`) |
| **Stress suite** (`run_stress`) | Synthetic factor shocks (whole portfolio), calibrated `recession_severe`, historical **episodes** (dotcom / 2008 / 2020 / 2022), RC concentration as **numbers only** (Top1 / Top3) | **No** в†’ **DIAG_ATTENTION** only for synthetic **Loss** or historical episode breach; **DIAG_PASS_WITH_WARNING** only for non-RC warnings (e.g. borderline history, data) where implemented |

Scenario and episode checks below are **for PM reporting**; they do not replace the mandate gate.

---

## 1. Pass criteria (per synthetic scenario)

- **`pass=true`** iff **Loss (mandate) test** passes: **Portfolio_PnL_% в‰Ґ в€’MaxDD_limit** (same `max_dd_limit` as historical/synthetic loss gate in `run_stress`). Violation в†’ row **`diagnostic_codes`** includes **DIAG_LOSS_*** and contributes to suite **DIAG_ATTENTION**.
- **RC concentration:** **`top1_rc_asset`**, **`top1_rc_pct`**, **`top3_rc_assets`**, **`top3_rc_sum_pct`** are reported for transparency; they **do not** set `pass`, **do not** add **DIAG_RC_*** codes, and **do not** change suite status.

**Outputs per scenario (synthetic):** `portfolio_pnl_pct`, **`pnl_by_asset_pct`** (per ticker), **`pnl_by_factor_pct`** (portfolio-level shockГ—beta per factor channel when `portfolio_betas` present), RC Top1/Top3 fields as above.


---

## 2. Mandatory scenarios

| # | Scenario            | Description / shocks |
|---|---------------------|----------------------|
| 1 | **Equity shock**    | Broad equity в€’40%. shock_eq = -0.40; others 0. |
| 2 | **Credit shock**    | HY stress: shock_credit = +0.04 (+400 bps); optionally shock_eq = -0.10; others 0. |
| 3 | **Rates shock**     | Real rates +200 bps: `shock_rr = +0.02`; others 0. |
| 4 | **Inflation/Stagflation** | `shock_cmd = +0.25`, `shock_eq = -0.20`, `shock_rr = +0.005`; `shock_inf`/`shock_usd` = 0 unless extended. |
| 5 | **Liquidity shock** | shock_eq = -0.25, shock_credit = +0.03 (+300 bps); RC uses stress covariance; others 0. |
| 6 | **Recession severe** | Hard-landing recession. `shock_eq` / `shock_rr` / `shock_credit` / `shock_inf` / `shock_usd` / `shock_cmd` are calibrated from realized factor moves in 2008 and 2020; the selected vector is the one with worst model PnL for current portfolio betas. RC uses stress covariance with `vol_mult = 1.60` and risk-on correlation override `0.95`. |

---

### 2.1 Recession severe calibration

`recession_severe` is not hand-entered in normal production runs. The report path builds the same weekly factor matrix used by stress factor diagnostics from 2007-01-01 through `analysis_end` and passes it to `run_stress`. The analytics matrix now includes `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, `us_growth`, and `oil`, but `run_stress` maps only the six stress factors below into synthetic shock keys.

For each calibration window (**2008** and **2020**, using the dates in `HISTORICAL_EPISODES`), the implementation sums weekly factor values over the window. The sums are mapped into shock keys:

- `equity` в†’ `shock_eq`
- `real_rates` в†’ `shock_rr`
- `credit` в†’ `shock_credit`
- `inflation` в†’ `shock_inf`
- `usd` в†’ `shock_usd`
- `commodity` в†’ `shock_cmd`

Analytics-only factors `vix`, `us_growth`, and `oil` are intentionally excluded from the synthetic shock mapping in the current production contract.

For each candidate vector, model PnL is:

```
model_pnl = shock_eq * beta_eq + shock_rr * beta_rr + shock_credit * beta_credit
            + shock_inf * beta_inf + shock_usd * beta_usd + shock_cmd * beta_cmd
```

The selected severe vector is the candidate with the lowest `model_pnl` for the current portfolio's 5Y factor betas. If portfolio betas are unavailable, the implementation selects the candidate with the highest risk-stress score based on equity drawdown, credit spread widening, USD strength, and commodity weakness. If factor history is unavailable, `run_stress` uses a conservative fallback vector and marks `recession_calibration.status = fallback_no_factor_history`.

`stress_report.json` includes `recession_calibration` with:

- `method`, `status`, `source_episodes`, `selected_source_episode`
- `episode_shocks`
- `selected_shock`
- `model_pnl_by_episode`
- `model_vs_realized` comparing model PnL with realized `pnl_real_episode` from `historical_results`
- `vol_mult` and `risk_on_corr`

The `scenario_results` row for `recession_severe` includes `shock_vector`, `calibration_source_episode`, `vol_mult`, and `risk_on_corr`.


For each asset *i* in the risk universe (aligned monthly columns; cash proxy excluded from shock path where applicable):

```
r_i(scenario) = ОІ_eq_i * shock_eq + ОІ_rr_i * shock_rr + ОІ_cr_i * shock_credit
                + ОІ_inf_i * shock_inf + ОІ_usd_i * shock_usd + ОІ_cmd_i * shock_cmd
```

(mapping of shock keys to per-asset beta columns follows `src/stress.py` / asset beta frame: `beta_eq`, `beta_rr`, вЂ¦)

- **PnL_i** = w_i Г— r_i (portfolio weights **w** on the same asset set used for the scenario).
- **Portfolio_PnL_%** = sum_i PnL_i.


---

## 4. Required outputs per scenario

For each scenario the production `run_stress` implementation outputs (see `scenario_results` in `stress_report.json`):

- **portfolio_pnl_pct** (aggregate scenario loss / gain)
- **shock_vector** (the factor shock values used for that scenario)
- **top1_rc_asset**, **top1_rc_pct**, **top3_rc_assets**, **top3_rc_sum_pct** (RC_vol вЂ” share of portfolio variance under base or stress covariance)
- **top3_loss_assets** (tickers with largest negative PnL contribution in the scenario)
- **loss_ok**, **pass** (equals **loss_ok**), **diagnostic_codes** (loss-related only on synthetic rows)


---

## 5. Loss test (diagnostic)

- **Criterion:** Portfolio_PnL_% в‰Ґ -|MaxDD_limit| (e.g. в‰Ґ -0.15 if MaxDD = -15%).
- If violated в†’ **DIAG_LOSS_*** (diagnostic; does not prevent release).
- For `recession_severe`, a synthetic loss breach emits **DIAG_LOSS_RECESSION_SEVERE**.

---

## 7. RC diagnostics (concentration in stress)

Report **Top1** and **Top3** contributors to portfolio variance (**RC_vol**) under the scenarioвЂ™s covariance (see В§10). There is **no** pass/fail threshold, no `rc1_ok` / `rc3_ok`, and no **DIAG_RC_*** codes in the production contract.

---

## 8. Factor validation (output only; limits optional in config)

The system must estimate and output:

- ОІ_equity (portfolio vs S&P)
- ОІ_real_rates (portfolio vs О”10Y real yield)
- ОІ_inflation (portfolio vs inflation surprise proxy)
- ОІ_credit (portfolio vs credit spread)
- ОІ_USD (portfolio vs DXY)

The full current analytics registry is `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, `us_growth`, and `oil`. In report JSON these appear as `beta_eq`, `beta_rr`, `beta_inf`, `beta_credit`, `beta_usd`, `beta_cmd`, `beta_vix`, `beta_us_growth`, and `beta_oil`.

If factor limits are set in config and violated в†’ **DIAG_BETA_*** / **DIAG_ATTENTION**; if no limits в†’ **DIAG_PASS_WITH_WARNING** (manual review). (Non-blocking.)

**Output windows (mandatory):**

- **5Y window (~260 weekly observations, Friday week-ends after inner join):** `factor_betas_5y`
- **10Y window (~520 weekly observations):** `factor_betas_10y`

For backward compatibility, `factor_betas` may be present and should mirror `factor_betas_5y`.

Each portfolio factor regression object (`factor_regression_5y`, `factor_regression_10y`) must report `r2`, `adj_r2`, and `idiosyncratic_risk`, where `idiosyncratic_risk = 1 - r2`. This is the residual share of portfolio-return variance not explained by the current factor model; it is diagnostic and measured at the full portfolio regression level, not per beta.

Rolling factor beta stability diagnostics must be reported under `factor_betas_stability`. This block is diagnostic only and does not affect weights, optimization, mandate status, or stress pass/fail. It must include `by_beta`, `thresholds`, `severity_distribution`, `severity_distribution_warning`, and `overall_severity`.

### 8.1 Factor multicollinearity (`factor_regression_*` only)

Portfolio weekly OLS in `factor_regression_5y` / `factor_regression_10y` must include **`factor_multicollinearity`** on the **same regressor rows** as the regression (after inner join and `valid` mask).

| Output field | Meaning |
|--------------|---------|
| `correlation` | Nested Pearson correlation matrix of factor columns |
| `pairwise_correlations` | All unordered pairs with `rho`, sorted by \|ПЃ\| descending |
| `cond_correlation_matrix` | cond(R) = О»_max / О»_min (eigvalsh on R; О»_min clipped at 1e-15); `null` if singular |
| `cond_correlation_matrix_singular` | Boolean if cond not finite |
| `vif_by_factor` | Classical VIF via auxiliary OLS (raw-scale X); `null` for a factor if VIF infinite |
| `max_vif`, `max_vif_factor`, `max_vif_is_infinite` | Summary |
| `strongest_pair` | Pair with largest \|ПЃ\| |
| `severity` | `low` \| `moderate` \| `high` \| `unknown` вЂ” see rules below |
| `assessment_ru` | Short Russian sentence for reports |

**Severity rules (fixed in code, `src/stress_factors.py`):**

- **high** if `max_vif_is_infinite` **or** max VIF в‰Ґ 10 **or** cond(R) в‰Ґ 80 **or** max \|ПЃ\| among pairs в‰Ґ 0.95
- else **moderate** if max VIF в‰Ґ 5 **or** cond(R) в‰Ґ 30 **or** max \|ПЃ\| в‰Ґ 0.85
- else **low**

**Note:** cond([1, X]) on raw units is **not** reported (misleading across scales); use **cond(correlation matrix)** and VIF.

### 8.2 Serial correlation of factor OLS residuals (`factor_regression_*`)

Each of `factor_regression_5y` / `factor_regression_10y` must include **`serial_correlation_diagnostics`** computed on the **same** OLS residuals as the reported betas (portfolio weekly return ~ intercept + factors, time order preserved).

| Field | Meaning |
|-------|---------|
| `durbin_watson` | DurbinвЂ“Watson statistic on the residual series (~2: little first-order serial correlation) |
| `breusch_godfrey` | List of objects, one per lag order `p` in `FACTOR_REGRESSION_BG_LAGS` (`src/stress_factors.py`, default **1, 2, 4**): `lags`, `lm_statistic`, `df_chi2` (= p), `p_value`, `n_aux_observations`, `aux_r_squared` |
| `method`, `h0`, `notes` | Fixed strings describing procedure |

**BreuschвЂ“Godfrey:** auxiliary regression of \(\hat u_t\) on intercept, \(X_t\), and \(\hat u_{t-1},\ldots,\hat u_{t-p}\); **LM = T Г— RВІ_aux** of that regression; under **Hв‚Ђ** (no serial correlation through lag p), LM в†’ **П‡ВІ(p)** (asymptotic).

### 8.3 Heteroskedasticity of factor OLS residuals (`factor_regression_*`)

Each of `factor_regression_5y` / `factor_regression_10y` must include **`heteroskedasticity_diagnostics`** computed on the **same** OLS residuals and factor rows as the reported betas.

| Field | Meaning |
|-------|---------|
| `breusch_pagan` | Object with `lm_statistic`, `df_chi2` (= number of factor regressors), `p_value`, `n_aux_observations`, `aux_r_squared`, `f_statistic`, `f_df_num`, `f_df_den`, `f_p_value` |
| `method`, `h0`, `auxiliary_regression`, `notes` | Fixed strings describing procedure |

**Breusch-Pagan:** auxiliary regression of \(\hat u_t^2\) on intercept and factor regressors \(X_t\); **LM = T Г— RВІ_aux** of that regression; under **Hв‚Ђ** (homoskedastic residuals), LM в†’ **П‡ВІ(k)** where \(k\) is the number of factor regressors. This is diagnostic/non-binding; if heteroskedasticity is indicated, beta point estimates remain OLS, and inference should rely on the HAC/Newey-West section below.

### 8.4 Robust (HAC / NeweyвЂ“West) inference for factor betas

Portfolio factor betas are **always** estimated via OLS (same as В§8: y = weekly portfolio return, X = weekly factor matrix).
However, when reporting **inference** (standard errors, t-statistics, p-values, confidence intervals), the project must use
**HAC/NeweyвЂ“West robust standard errors** on the same residual series:

- Kernel: **Bartlett**
- Max lags (weekly): `FACTOR_REGRESSION_HAC_LAGS = 4` (в‰€ 1 month)

Output convention in each `factor_regression_5y` / `factor_regression_10y`:

- Top-level beta fields (`betas`, classical `t`, `p`, `ci_low`, `ci_high`) correspond to **OLS with classic SE** (`se_type = "classic_ols"`).
- Section `hac_inference`:
  - `se_type`: `"hac_newey_west"`
  - `kernel`: `"bartlett"`
  - `max_lags`: integer (e.g. 4)
  - `se`, `t`, `p`, `ci_low`, `ci_high`: arrays (intercept first, then same factor order as in `betas`).

For reporting and decision rules:

- **Point estimates (ОІ)** are taken from OLS (`betas`).
- **Significance, p-values and confidence intervals in stress reports and PDFs must be interpreted using `hac_inference`**;
  classic OLS t/p are retained for diagnostics only.

### 8.5 Rolling beta stability diagnostics

`factor_betas_stability` evaluates whether each factor beta is reliable as a management signal across rolling windows and data frequencies.

Required inputs and companion outputs:

- Existing weekly rolling beta windows remain `factor_betas_rolling_windows_weeks = {3y: 156, 5y: 260, 10y: 520}` and `factor_betas_rolling_summary`.
- Monthly rolling beta windows are reported as `factor_betas_rolling_windows_months = {3y: 36, 5y: 60, 10y: 120}` and `factor_betas_rolling_monthly_summary`.
- `factor_beta_stability.csv` is a flat export of the main per-beta severity metrics.

Per beta, `factor_betas_stability.by_beta[beta_key]` must include:

- `sign_stability`: dominant sign, dominant sign share, sign change count, p10, p90, and severity.
- `magnitude_stability`: median, p90-minus-p10 band, relative band, and severity.
- `specification_sensitivity`: median span across weekly/monthly and 3Y/5Y/10Y specifications, relative median span, sign disagreement flag, by-specification medians, and severity.
- `oos_stability`: rolling-forward next-1Y diagnostics with sign match share, relative magnitude degradation, number of tests, by-specification rows, and severity.
- `combined_severity`: the maximum of sign, magnitude, specification, and OOS severity.

Fixed conservative thresholds:

- Sign severity is **high** if dominant sign share is below 0.65 or p10/p90 cross zero with at least 0.01 absolute margin; **moderate** if dominant sign share is below 0.80 or the p10/p90 range includes zero; otherwise **low**.
- Magnitude severity uses `relative_band = (p90 - p10) / max(abs(median), 0.05)`: **high** at `>= 2.0`, **moderate** at `>= 1.0`, otherwise **low**.
- Specification severity is **high** if weekly/monthly/window medians disagree in sign or relative median span is `>= 2.0`; **moderate** at relative median span `>= 1.0`; otherwise **low**.
- OOS severity is **high** if next-1Y sign match share is below 0.65 or relative magnitude degradation is `>= 2.0`; **moderate** if sign match share is below 0.80 or degradation is `>= 1.0`; otherwise **low**.

Severity distribution is computed from final `combined_severity` across beta keys. If high share is greater than 0.70, set `severity_distribution_warning` to indicate thresholds may be too strict and suggest reviewing magnitude thresholds around 1.5 / 2.5. If low share is greater than 0.80, set `severity_distribution_warning` to indicate thresholds may be too soft. This warning does not change thresholds automatically.

### 8.6 OOS episode explainability: ОІ Г— realized factor shocks

To verify that factor betas explain stress episodes out-of-sample (not only in-sample fit),
`stress_report.json` should include `factor_beta_shock_oos` with per-episode diagnostics:

- Uses the same episode windows as **`historical_results`** from `run_stress` (including **dotcom**, **2008**, **2020**, **2022** when present).
- Realized factor shock for episode = **sum of weekly factor series** over the episode window.
- Model PnL variants:
  - `pnl_model_5y` using `factor_betas_5y`
  - `pnl_model_10y` using `factor_betas_10y`
  - `pnl_model_roll3y_pre` using betas estimated on rolling 3Y window ending right before episode start
- Factor contributions in this diagnostic follow the full analytics registry, so `beta_vix`, `beta_us_growth`, and `beta_oil` should appear when factor history and betas are available.
- Real benchmark:
  - `pnl_real_episode` from historical episode portfolio return
- Error fields:
  - `abs_error_5y`, `abs_error_10y`, `abs_error_roll3y_pre`
- Summary:
  - mean absolute error by method over episodes with available `pnl_real_episode`.

This output is **diagnostic / non-binding** and should be shown in stress commentary.

---

### 8.7 Historical row attribution

After `factor_beta_shock_oos` is computed, report generation enriches each `historical_results` row with primary historical factor attribution. The primary attribution uses `factor_contrib_5y`, i.e. current `factor_betas_5y` multiplied by the realized weekly factor shock summed over that episode. This is meant to explain the current portfolio's structural vulnerability to the historical factor mix.

Each enriched historical row should include:

- `historical_factor_attribution`: object with `method`, `caveat`, `beta_source`, `factor_model_pnl_pct`, `factor_model_error_pct`, `factor_model_abs_error_pct`, `factor_shock_sum`, `pnl_by_factor_pct`, `top_factor_drivers`, and `largest_negative_factor`.
- Convenience mirrors at row level: `pnl_by_factor_pct`, `top_factor_drivers`, `largest_negative_factor`, `factor_model_pnl_pct`, `factor_model_error_pct`, `factor_model_abs_error_pct`, `factor_attribution_method`, and `factor_attribution_beta_source`.

`method` is `model_based_beta_times_realized_factor_shock`. The required caveat is that this is beta times realized factor shock and **not** a pure realized causal decomposition. `top_factor_drivers` is sorted by absolute model contribution, and `largest_negative_factor` is the single most negative model contribution when one exists.

This enrichment is diagnostic / non-binding. It does not change stress pass/fail, mandate status, optimizer behavior, or weight release.

---

### 8.8 Factor covariance analytics

`stress_report.json` includes `factor_covariance` when weekly factor history is available. This block is diagnostic / non-binding and does not change stress pass/fail, mandate status, optimizer behavior, or weight release.

The block must keep three regimes separate:

- `base`: **data_driven**, 5Y weekly sample covariance ending at `analysis_end`.
- `stress_empirical`: **data_driven**, weekly sample covariance using only crisis rows from the 2008, 2020, and 2022 historical stress windows.
- `stress_overlay`: **hypothetical**, derived from `stress_empirical` only, with deterministic correlation/covariance clamps and positive-semidefinite repair if needed.

There must be no implicit blended matrix. Each regime block includes `label`, `classification`, `matrix`, `variances`, `correlations`, and either `window` or `episodes_used`. The canonical factor order is the full weekly factor registry: `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, `us_growth`, and `oil`. Missing portfolio beta keys are zero-filled in `exposure_vector.zero_filled_beta_keys` and all matrices preserve the full order.

`stress_overlay.overlay_deltas` logs every clamp with `factor_i`, `factor_j`, pre/target/post correlation and covariance values, absolute and relative delta where meaningful, `clamp_reason`, and whether PSD repair was applied. The comparison block separates `empirical_change` (`stress_empirical` vs `base`) from `overlay_amplification` (`stress_overlay` vs `stress_empirical`).

Portfolio factor risk is computed under each regime as `b' Sigma_f b`, where `b` is the ordered portfolio factor beta vector and `Sigma_f` is that regime's factor covariance matrix. The report includes `portfolio_factor_variance`, `portfolio_factor_vol`, factor-level `portfolio_factor_rc`, and `beta_sensitivity`. `beta_sensitivity` recomputes `b' Sigma_f b` after applying +/- one rolling weekly beta standard deviation to the exposure vector; it is a sensitivity diagnostic, not a realized risk estimate.

`RC_stability_flag` compares factor RC shares in `base` vs `stress_empirical`; a factor is flagged when its absolute relative RC shift is greater than 30%. `covariance_stability_check` compares 5Y weekly base covariance with 2Y weekly base covariance and flags deviations greater than 35%, using absolute-difference fallback for near-zero denominators.

CSV artifacts written under `results_csv/` include:

- `factor_covariance_base_5y_weekly.csv`
- `factor_covariance_stress_empirical_weekly.csv`
- `factor_covariance_stress_overlay_weekly.csv`
- `factor_correlation_base_5y_weekly.csv`
- `factor_correlation_stress_empirical_weekly.csv`
- `factor_correlation_stress_overlay_weekly.csv`
- `portfolio_factor_rc_base.csv`
- `portfolio_factor_rc_stress_empirical.csv`
- `portfolio_factor_rc_stress_overlay.csv`
- `factor_covariance_overlay_deltas.csv`
- `factor_covariance_stability_check.csv`

`stress_commentary.txt` must label `base` and `stress_empirical` as data-driven and `stress_overlay` as hypothetical. It must report empirical change separately from overlay amplification.

---

## 9. Historical validation

Run portfolio through episodes (see `HISTORICAL_EPISODES` in `src/stress.py`):

- **dotcom:** 2000-03-01 в†’ 2002-10-31
- **2008:** 2007-10-01 в†’ 2009-03-31
- **2020:** 2020-02-01 в†’ 2020-04-30
- **2022:** 2021-11-01 в†’ 2022-10-31

Output: max drawdown, realized episode PnL, volatility spike, and, when factor history is available, model-based factor attribution as described in В§8.7.
Episode DD vs limit adds **DIAG_HIST_*** when breached; else episode contributes to **DIAG_PASS**. (Non-blocking.)

---

## 10. Stress covariance (for RC in stress)

- **Base:** ОЈ_base from project returns (monthly, ddof=1).
- **Stress:** For Equity / Credit / Liquidity scenarios (`stress_cov: true` in `src/stress.py`):
  - Pairs involving at least one ticker **outside** that set keep the **base** correlation from ОЈ_base (see `_stress_covariance`).
  - **Vol scaling:** equity/credit scenarios `vol_mult = 1.25`; liquidity shock `vol_mult = 1.50`.
- RC is computed on **current portfolio weights** using ОЈ_stress.

---

## 11. Factor data sources (FRED + fallback)

- **Equity (S&P):** FRED:SP500 or ETF proxy SPY (total return preferred).
- **10Y real yield:** FRED:DFII10; use О”(DFII10).
- **Inflation surprise:** FRED:T10YIE; use О”(T10YIE) as proxy.
- **Credit spread (HY):** FRED:BAMLH0A0HYM2; use О”(spread).
- **USD:** FRED:DTWEXBGS; use О” or % change.
- **Commodity:** ETF proxy DBC; use weekly/month-end percent change.
- **VIX:** FRED:VIXCLS; use weekly/month-end percent change.
- **US growth proxy:** FRED:WEI; shift week-ending-Saturday timestamps to Friday, then use weekly/month-end first difference.
- **Oil:** FRED:DCOILWTICO; use weekly/month-end percent change.

Betas: **weekly** changes/returns for reporting outputs in В§8 (`factor_betas_5y`, `factor_betas_10y`), with synchronized week-end dates (inner join), ending at **analysis_end**. Windows: **260 weeks (5Y)** and **520 weeks (10Y)** (see `src/stress_factors.py`: `FACTOR_WEEKS_5Y`, `FACTOR_WEEKS_10Y`). Use project series when available; FRED codes as fallback.

---

## 12. Final status and report (diagnostic suite)

- **Status:** **DIAG_PASS** | **DIAG_PASS_WITH_WARNING** | **DIAG_ATTENTION** (legacy **PASS** / **PASS_WITH_WARNING** may appear in old JSON).
- **primary_diagnostic_code** / **fail_reason_code** (when **DIAG_ATTENTION**): first **Loss** or **Historical** code only (e.g. **DIAG_LOSS_EQUITY_SHOCK**, **DIAG_HIST_2022**).
- **diagnostic_codes:** ordered list of **Loss** + **Historical** **DIAG_*** issues.
- **warning_code** (when **DIAG_PASS_WITH_WARNING**): e.g. **WARN_HIST_BORDERLINE**, **WARN_DATA_INSUFFICIENT** (no RC-only warning code in current builds).

View After Optimization does not stop on stress status; stress output is diagnostic only.
