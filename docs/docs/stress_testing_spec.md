# Stress Testing Specification

**Policy link.** This document is the source of truth for **diagnostic** portfolio stress testing. **Blocking** mandate max drawdown is defined in **docs/production_workflow.md** (full historical sample, **FAIL_MANDATE**).

> **2026-04-27 update:** Synthetic **pass** = **Loss (portfolio PnL vs mandate MaxDD)** only.
> **2026-04-28 update:** **RC Top1 / Top3** (`top1_rc_pct`, `top3_rc_sum_pct`, tickers) remain on each scenario row as **numeric diagnostics only** вЂ” no `rc1_ok` / `rc3_ok`, no `rc_diagnostic_codes`, no `rc_attention_codes`, no suite status change for RC-only patterns. Historical episode contract unchanged (episode max DD vs mandate). **dotcom** episode is in the historical list (see В§9).
> **2026-04-28 update:** Add **Recession severe** (`recession_severe`) as a hard-landing synthetic scenario. Its shock vector is calibrated from realized weekly factor moves in the existing **2008** and **2020** historical windows, selecting the episode with the worst model PnL for the current portfolio betas.
> **2026-04-28 update:** Portfolio factor regressions include **Breusch-Pagan** heteroskedasticity diagnostics on the same OLS residuals/rows as the reported factor betas.
> **2026-04-28 update:** Factor analytics now use a **nine-factor** weekly registry (`equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, `us_growth`, `oil`). Synthetic stress scenarios and recession calibration remain a **six-shock** engine and only map the first six factors into `shock_*` keys.
> **2026-04-29 update:** Historical stress rows now include **model-based factor attribution** when factor history is available. The primary attribution uses 5Y portfolio betas times realized episode factor shocks and must be labeled as model-based explainability, not pure realized causal decomposition.
> **2026-04-29 update:** Stress reports now include a **diagnostic-only stability-adjusted beta overlay**. It shrinks unstable 5Y factor betas toward 10Y anchors, flags strong 5Y-vs-10Y divergence, and reports material raw-vs-adjusted factor-model PnL deltas.
> **2026-04-30 update:** Split factor contract. Production regression/beta/stability/OOS/adjusted-overlay/base variance decomposition use base factors only: `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, `us_growth`. `commodity` is the production сырьевой factor. Extended diagnostics/stress analytics use base factors plus `oil`; `beta_oil` is deprecated in production outputs and exposed through `diagnostic_oil_beta` or stress-layer metrics only.
> **2026-05-08 update:** Synthetic scenario **RC_top1 / RC_top3** concentration diagnostics now use **`taxonomy_blend_v1`**: a blend of sample monthly correlation with a block-structured target matrix (EQ / CR / ND / TI / CO / CA) resolved from `config/etf_universe.yml` and `config/stock_universe.yml`, per-scenario `lambda_blend`, explicit between-block overrides with defaults, per-block volatility multipliers, and PSD repair on the blended correlation. **Historical episodes** are unchanged (realized paths only). Optional `stress_cov_method="uniform_legacy"` restores the prior uniform risk-on correlation + scalar `vol_mult` for synthetic rows only. `rates_shock` and `inflation_stagflation` set `stress_cov=True` for RC diagnostics under the same taxonomy engine.

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
| 3 | **Rates shock**     | Real rates +200 bps: `shock_rr = +0.02`; others 0. RC uses **taxonomy_blend_v1** stress covariance. |
| 4 | **Inflation/Stagflation** | `shock_cmd = +0.25`, `shock_eq = -0.20`, `shock_rr = +0.005`, `shock_inf = +0.005` (+50 bps breakeven inflation); `shock_usd = 0`. RC uses **taxonomy_blend_v1** stress covariance. |
| 5 | **Liquidity shock** | shock_eq = -0.25, shock_credit = +0.03 (+300 bps); RC uses **taxonomy_blend_v1** stress covariance (`src/stress_covariance_taxonomy.py`); others 0. |
| 6 | **Recession severe** | Hard-landing recession. `shock_eq` / `shock_rr` / `shock_credit` / `shock_inf` / `shock_usd` / `shock_cmd` are calibrated from realized factor moves in 2008 and 2020; the selected vector is the one with worst model PnL for current portfolio betas. RC uses **taxonomy_blend_v1** stress covariance. Legacy scalars `vol_mult = 1.60` and `risk_on_corr = 0.95` remain on `recession_calibration` / scenario row for backward compatibility but **do not** define the RC covariance (taxonomy block multipliers and blended correlations apply). |

### 2.2 Synthetic stress covariance (`taxonomy_blend_v1`)

For each synthetic scenario with `stress_cov=True`, `run_stress` builds monthly `cov_base` from overlapping portfolio assets, then:

1. **Block assignment** per ticker via `resolve_stress_asset_block` (cash proxy → CA; ETF rows from `config/etf_universe.yml`; equities from `config/stock_universe.yml`; unknown tickers → EQ with `taxonomy_coverage.missing_tickers`).
2. **Target correlation** `C_target` from within-block targets, explicit between-block pairs (`RHO_PAIR_OVERRIDES`), and `RHO_DEFAULT_BETWEEN` for unlisted block pairs (see `src/stress_covariance_taxonomy.py`).
3. **Blend:** `C_blend = (1 - lambda_blend) * Corr(cov_base) + lambda_blend * C_target`, then **PSD repair** (`repair_correlation_matrix`).
4. **Volatility stress:** `sigma_i_stress = sigma_i_base * vol_mult_block[scenario][block(i)]`.
5. **Output covariance:** `cov_stress = D * C_blend * D` with `D = diag(sigma_stress)`.

**Portfolio scenario PnL** is unchanged (linear factor shocks × per-asset betas). Only **RC_vol** inputs use `cov_stress`.

**`run_stress` keyword** `stress_cov_method` (default `taxonomy_blend_v1`): set `uniform_legacy` to restore the previous uniform risk-on correlation override and scalar `vol_mult` from scenario params.

**Scenario rows** (`stress_report.json.scenario_results[*]`) add when `stress_cov` applies: `stress_cov_method`, `stress_cov_lambda`, `stress_cov_calibration_version` (current diagnostic pack: **`calibrated_v1_assumptions`** in `STRESS_COV_CALIBRATION_VERSION`), `taxonomy_coverage` (`missing_tickers`, `blocks_by_ticker`), **`vol_mult_by_block`** (the scenario’s per-block volatility multipliers), and **`key_rho_overrides_used`** (compact trace of primary between-block ρ overrides documented for calibration). When `stress_cov` is false, these fields are null or empty as implemented.

**Calibration table** `LAMBDA_BLEND`, `RHO_WITHIN`, `RHO_PAIR_OVERRIDES`, `VOL_MULT_BLOCK` in `src/stress_covariance_taxonomy.py` implement **`calibrated_v1_assumptions`** (diagnostic RC layer only; does not alter scenario shocks, optimizer, or pass/fail gates).

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
- `vol_mult` and `risk_on_corr` (legacy documentation scalars; RC uses taxonomy when `stress_cov_method` is `taxonomy_blend_v1`)
- `stress_cov_method` (**`taxonomy_blend_v1`** in normal production)
- `stress_cov_lambda` (scenario `lambda_blend` for recession_severe; **`calibrated_v1_assumptions`** uses **0.65**)
- `stress_cov_calibration_version`, `vol_mult_by_block`, `key_rho_overrides_used` (same semantics as synthetic scenario rows when taxonomy stress covariance applies)

The `scenario_results` row for `recession_severe` includes `shock_vector`, `calibration_source_episode`, `vol_mult`, `risk_on_corr` (legacy scalars), **`stress_cov_method`**, **`stress_cov_lambda`**, **`stress_cov_calibration_version`**, **`vol_mult_by_block`**, **`key_rho_overrides_used`**, and **`taxonomy_coverage`** when RC stress covariance applies.


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
- **`stress_cov_method`**, **`stress_cov_lambda`**, **`stress_cov_calibration_version`**, **`taxonomy_coverage`**, **`vol_mult_by_block`**, **`key_rho_overrides_used`** when the scenario uses synthetic stress covariance (null or empty when `stress_cov` is false)

Raw scenario rows remain the primary stress contract. Any stability-adjusted factor overlay must be reported in separate top-level blocks and must not overwrite `scenario_results[*].pnl_by_factor_pct` or the raw scenario PnL fields.


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

The base production factor registry is `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, and `us_growth`. In production beta JSON these appear as `beta_eq`, `beta_rr`, `beta_inf`, `beta_credit`, `beta_usd`, `beta_cmd`, `beta_vix`, and `beta_us_growth`. `commodity` is the production сырьевой factor.

The extended diagnostic/stress registry is the base registry plus `oil`, exposed as `beta_oil` only in extended diagnostics. `beta_oil` is deprecated and removed from new production beta outputs, rolling stability, OOS stability, adjusted production beta overlay, and base variance decomposition. Oil exposure must be read from `stress_report.json.diagnostic_oil_beta` or stress-layer metrics.

If factor limits are set in config and violated в†’ **DIAG_BETA_*** / **DIAG_ATTENTION**; if no limits в†’ **DIAG_PASS_WITH_WARNING** (manual review). (Non-blocking.)

**Output windows (mandatory):**

- **5Y window (~260 weekly observations, Friday week-ends after inner join):** `factor_betas_5y`
- **10Y window (~520 weekly observations):** `factor_betas_10y`

For backward compatibility, `factor_betas` may be present and should mirror `factor_betas_5y`.

`factor_betas_5y`, `factor_betas_10y`, and `factor_betas` must not contain `beta_oil` in new outputs.

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
  - `pnl_model_adjusted` using `factor_betas_adjusted.adjusted`
  - `pnl_model_roll3y_pre` using betas estimated on rolling 3Y window ending right before episode start
- Factor contributions in this production diagnostic follow the base registry, so `beta_vix` and `beta_us_growth` may appear when factor history and betas are available; `beta_oil` must not appear here.
- Real benchmark:
  - `pnl_real_episode` from historical episode portfolio return
- Error fields:
  - `abs_error_5y`, `abs_error_10y`, `abs_error_adjusted`, `abs_error_roll3y_pre`
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

### 8.7A Stability-adjusted beta overlay

`stress_report.json` must also include a diagnostic-only block `factor_betas_adjusted` with:

- `raw`: the raw 5Y beta map copied from `factor_betas_5y`
- `adjusted`: stability-adjusted beta map
- `confidence_by_beta`: shrinkage confidence per beta
- `severity_by_beta`: copied `combined_severity` per beta when available
- `anchor_source`: `10y_when_available_else_5y_raw`
- `shrinkage_method`: fixed code string describing severity-weighted shrinkage toward the 10Y anchor
- `adjustment_reason_by_beta`: short reason string per beta
- `beta_5y_vs_10y_divergence`: per-beta divergence diagnostics plus `strong_divergence_any` and `strong_divergence_betas`

The fixed severity-to-confidence map is:

- `low -> 1.00`
- `moderate -> 0.75`
- `high -> 0.50`
- `unknown -> 0.60`

For each beta, source beta is raw `factor_betas_5y[beta_key]`, anchor beta is `factor_betas_10y[beta_key]` when available else the same 5Y beta, and adjusted beta is `beta_adjusted = c * beta_5y + (1 - c) * beta_anchor`.

Strong 5Y-vs-10Y divergence is `true` if signs differ or `relative_gap = abs(beta_5y - beta_10y) / max(abs(beta_5y), 0.05)` is at least `1.0`.

This block is diagnostic only and must not replace raw `factor_betas_5y`, `factor_betas`, or the primary `run_stress` portfolio beta input. Production adjusted beta maps must exclude `beta_oil`.

### 8.7B Kalman time-varying beta diagnostics

`stress_report.json` may include a diagnostic-only block `factor_betas_kalman` when weekly portfolio returns and factor rows are available. This block estimates current portfolio factor betas with a random-walk Kalman filter over the extended weekly diagnostic registry. It must not replace `factor_betas`, `factor_betas_5y`, `factor_betas_10y`, mandate gates, optimizer inputs, or stress pass/fail logic.

### 8.6 Diagnostic Oil beta

`stress_report.json` must include `diagnostic_oil_beta` when extended diagnostic inputs are available:

- `role = "diagnostic_warning_only"`
- Oil beta estimates where available (`beta_oil_5y`, `beta_oil_10y`)
- Commodity production beta references (`beta_commodity_5y`, `beta_commodity_10y`)
- Oil/Commodity correlation and Oil/Commodity VIF or collinearity signal
- Kalman Oil estimate when available

Reports must label Oil as diagnostic/stress only and must not print Oil as a production beta.

The block includes:

- `latest`: capped latest Kalman beta map, using the same beta keys as raw factor betas.
- `latest_raw`: uncapped latest filtered beta map.
- `latest_date`, `method`, `window_weeks`, and `n_observations`.
- `beta_cap_abs`: fixed at `3.0`; reported beta values are clipped to `[-3.0, 3.0]`.
- `cap_diagnostics`: per-beta `was_capped`, `raw_value`, and `capped_value`.
- `state_uncertainty`: posterior standard deviation per beta.
- `uncertainty_by_beta`: `low` when posterior std is `<= 0.15`, `moderate` when `<= 0.35`, and `high` above `0.35`.
- `uncertainty_severity_distribution` and `high_uncertainty_betas`.
- `comparison_vs_5y` and `comparison_vs_10y`.
- `divergence_vs_5y`: flags a beta when the Kalman sign differs from 5Y, `abs_gap >= 0.25`, or `relative_gap = abs(kalman - beta_5y) / max(abs(beta_5y), 0.05) >= 0.75`.
- `diagnostics`: initialization status, initialization observations, observation variance, initial residual variance, factor order, beta order, and warning codes.

CSV artifacts are `kalman_factor_betas_weekly.csv` and `kalman_factor_betas_latest.csv`. These are report artifacts only.

### 8.7C Adjusted synthetic and historical PnL signal

The stress report must keep raw scenario rows unchanged and add separate top-level diagnostics:

- `synthetic_factor_pnl_adjusted`
- `factor_beta_shock_oos_adjusted`
- `raw_vs_adjusted_pnl_signal`

`synthetic_factor_pnl_adjusted.scenarios[*]` must include `scenario_id`, `pnl_model_raw`, `pnl_model_adjusted`, `adjusted_minus_raw`, `pnl_abs_delta`, `pnl_relative_delta`, `pnl_by_factor_pct_raw`, and `pnl_by_factor_pct_adjusted`.

`raw_vs_adjusted_pnl_signal` must include `synthetic`, `historical`, `material_difference_any`, and `material_scenarios`.

The material-difference rule is fixed in code: `material_difference = true` if `pnl_relative_delta >= 0.25` or `pnl_abs_delta >= 0.01`.

Historical rows may carry parallel adjusted attribution convenience fields with `_adjusted` suffixes such as `historical_factor_attribution_adjusted`, `pnl_by_factor_pct_adjusted`, and `factor_model_pnl_pct_adjusted`. These adjusted fields are diagnostic overlays and do not replace the primary raw 5Y attribution.

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

#### 8.8.1 Factor covariance forecast quality

`stress_report.json.factor_covariance.forecast_quality` is a diagnostic-only out-of-sample backtest of the factor covariance matrix as a risk forecast. It does not change stress pass/fail, mandate status, optimizer behavior, or weight release.

The test uses non-overlapping weekly windows:

- Training window: 260 weekly rows.
- Holdout window: the next 52 weekly rows.
- Step: 52 weekly rows.
- Forecast covariance: sample covariance with `ddof=1` on the training window.
- Realized covariance: sample covariance with `ddof=1` on the holdout window.
- Forecast portfolio factor risk: `sqrt(b' Sigma_train b)`, where `b` is the current ordered portfolio factor beta vector.
- Realized portfolio factor risk: `std(X_holdout b, ddof=1)`.

The block includes `status`, `method = rolling_5y_covariance_vs_next_1y_realized_factor_risk`, `variance_scale = weekly`, `train_weeks = 260`, `holdout_weeks = 52`, `step_weeks = 52`, `ddof = 1`, `summary`, and `rows`. If history is insufficient, `status = unavailable` and `reason = insufficient_factor_history`.

`summary` includes `n_forecasts`, median/mean absolute volatility forecast error, mean signed volatility forecast error, hit rates for absolute volatility error at 10%, 20%, and 30%, median correlation RMSE, median covariance relative Frobenius error, and `overall_severity`. Severity is `low` when median absolute volatility error is at most 15% and the 20% hit rate is at least 60%; `high` when median absolute volatility error is above 35% or the 20% hit rate is below 35%; otherwise `moderate`.

Each row includes `cutoff_date`, `realized_end_date`, train/holdout observation counts, model and realized factor variance/volatility, signed and absolute volatility error, correlation RMSE, covariance relative Frobenius error, and the worst correlation error pair. This diagnostic uses the current beta vector to isolate covariance forecast quality from beta forecast quality.

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
- `factor_covariance_forecast_quality.csv`

`stress_commentary.txt` must label `base` and `stress_empirical` as data-driven and `stress_overlay` as hypothetical. It must report empirical change separately from overlay amplification and include the forecast-quality summary when available.

---

### 8.8.2 Macro regime diagnostics

`stress_report.json.macro_regime_diagnostics` is diagnostic-only and non-binding. It does not change optimizer behavior, mandate status, stress pass/fail, weight release, or the primary raw 5Y/10Y beta outputs.

The method version is `macro_two_axis_v1`. The required disclaimer is:

`macro_two_axis_v1 is a diagnostic-only macro regime classifier. It does not affect optimizer weights, mandate gates, stress pass/fail, or weight release.`

The model is a **two-axis macro classifier on monthly data**. Indicators are loaded through a layered source resolver covering FRED → Yahoo Finance → official CSV (Atlanta Fed GDPNow) → official API → keyed third-party API → manual CSV (`cache/macro/<key>.csv`, override via `<KEY>_CSV_PATH` env var). When a source is unavailable (missing API key, network failure, paywalled) the indicator becomes `available=False` and the model degrades to a lower `coverage_tier` without crashing the run.

Indicator blocks (each with one or two indicators):

- Growth — `growth_business_activity` (ISM Manuf PMI, ISM Services PMI), `growth_labor` (PAYEMS, UNRATE), `growth_consumer` (Real PCE, Real DPI), `growth_credit` (HY OAS, NFCI), `growth_nowcast` (Atlanta Fed GDPNow via FRED:GDPNOW — quarterly, ffilled to monthly; reference page <https://www.atlantafed.org/research-and-data/data/gdpnow>; optional block, single indicator after NY Fed Nowcast was retired on 2026-05-07).
- Inflation — `core_inflation` (Core CPI 3m annualised, Core PCE 3m annualised), `headline_inflation` (Headline CPI 3m annualised, WTI oil monthly average then 3m change), `wages` (Average Hourly Earnings 3m yoy, ECI quarterly forward-filled to monthly yoy), `inflation_expectations` (5y breakeven, 5y5y forward breakeven), `business_price_pressure` (ISM Manuf Prices Paid, ISM Services Prices Paid).

Transforms applied per indicator: `level` (month-end unless an indicator-specific aggregation overrides it, e.g. WTI uses monthly average), and a momentum component derived as `m_over_m_change`, `three_m_avg_mom` (PAYEMS), `three_m_change` (UNRATE, sign inverted), `three_m_yoy` (real PCE/DPI, AHE), `three_m_annualized` (core/headline CPI, core PCE), `oil_monthly_avg_three_m_change` (WTI), `quarterly_ffill_monthly_yoy` (ECI; YoY of a level), or `quarterly_ffill_monthly_three_m_change` (GDPNow nowcast; level + 3m change of an already-annualised growth rate). Each indicator and its momentum series are normalised by a **rolling 10-year monthly z-score** with `window = 120` and `min_periods = 60`, then bucketed at `±0.5` to a `+1 / 0 / −1` signal. Block sub-scores are the sign-adjusted mean of available indicator signals. Composite axis scores are blended `0.6 · momentum_block_average + 0.4 · level_block_average`.

**Primary regime classification (4 quadrants by sign).** Every scored month is assigned a single ``primary_regime`` based on the **sign** of `growth_score` and `inflation_score`. The neutral band no longer produces a 5th regime bucket — uncertainty inside the band is reported separately via `transition_flag` and `transition_reason`:

- `goldilocks`: `growth_score >= 0` and `inflation_score < 0`.
- `reflation`: `growth_score >= 0` and `inflation_score >= 0`.
- `stagflation`: `growth_score < 0` and `inflation_score >= 0`.
- `recession_disinflation`: `growth_score < 0` and `inflation_score < 0`.

Transition metadata, reported alongside `primary_regime` per month and as part of `transition_summary`:

- `transition_flag = true` when `|growth_score| <= neutral_band` or `|inflation_score| <= neutral_band`.
- `transition_reason ∈ {growth_axis_near_neutral, inflation_axis_near_neutral, both_axes_near_neutral}` when the flag is true; `null` otherwise.
- `confidence_level` continues to follow the existing rules (`high / medium / low`) and is `low` whenever `transition_flag = true`.

**Backward compatibility.** The legacy 5-bucket label is preserved in `regime_legacy` (with `regime_legacy_unlagged` and `regime_legacy_unlagged_raw` for diagnostics) and reported in `regime_legacy_counts` plus the legacy `MACRO_REGIME_NAMES` list. New consumers must group asset / factor / RC analytics by `primary_regime` and may further split by `primary_regime + transition_flag` (e.g. `reflation_non_transition` vs `reflation_transition`) or `primary_regime + confidence_level`. ``primary_regime`` never takes the value `neutral_transition`; consumers iterating the legacy 5-tuple keep finding `neutral_transition` with zero observations under the new scheme.

Default `neutral_band = 0.20`. Implementations must verify regime stability under sensitivity testing at `±0.20`, `±0.25`, and `±0.35`. The 2026-05 sensitivity analysis (`docs/exec_plans/2026-05-07_macro_two_axis_regime_v1.md` / `2026-05-07_regime_label_quality_check.md`) showed that lowering the band from 0.25 to 0.20 reduces the `neutral_transition` share by ~8pp and pushes the major regimes (`reflation`, `goldilocks`) further away from the `<24-obs` low-confidence boundary, without breaking the macro-sanity windows.

**Indicator scoring method.** Two scoring modes are supported:

- `discrete` (default): rolling 10-year monthly z-score with `window = 120`, `min_periods = 60`, then bucketed at `±0.5` to a `+1 / 0 / −1` signal (preserves the historical behaviour and is the most decisive on extremes).
- `clipped_z` (alternative, diagnostic): the same rolling z-score is signed by indicator direction, clipped to `[-clipped_z_max_abs, +clipped_z_max_abs]` (default `2.0`) and rescaled to `[-1, +1]`. The 2026-05 comparison showed that under the existing block-averaging and momentum/level blend the clipped-z mode dampens block averages relative to the discrete mode and produces a higher `neutral_transition` share at every band, so it must not be the default until block aggregation is changed accordingly.

`axis_model.scoring_method`, `axis_model.clipped_z_max_abs`, and `axis_model.persistence_months` must be reported in `stress_report.json` for traceability.

**Persistence rule (smoothing only).** A 2-month confirmation rule is applied by default: a regime change is adopted only when at least `persistence_months` consecutive monthly labels agree on the new regime. At the tail of the series, when fewer than `persistence_months` future observations exist, the previous regime is held. Persistence is a smoothing layer only — it must not be used as the primary mechanism to reduce `neutral_transition`. The default `persistence_months = 2` eliminates one-month label flips while preserving real regime transitions; `persistence_months = 1` disables smoothing for diagnostics that need the raw label series. The unsmoothed labels are also retained in `regime_unlagged_raw` for inspection.

**Look-ahead protection**: a 1-month publication lag — labels at month `t` use composite scores computed from data ending at month `t − 1`. Release-date / vintage-accurate handling is **out of scope for v1**; this is documented in `axis_model.look_ahead_caveat`.

Top-level output fields include `axis_model.version`, `axis_model.frequency = "monthly"`, `axis_model.neutral_band_abs`, `axis_model.score_blend`, `axis_model.scoring_method`, `axis_model.clipped_z_max_abs`, `axis_model.persistence_months`, `axis_model.look_ahead_protection`, `axis_model.look_ahead_caveat`, `axis_scores_latest.growth_score`, `axis_scores_latest.inflation_score`, `axis_scores_latest.growth_blocks`, `axis_scores_latest.inflation_blocks`, `current_regime` (= primary regime), `current_primary_regime`, `current_regime_legacy`, `current_transition_flag`, `current_transition_reason`, `regime_confidence`, `confidence_level`, `regime_transition_warning`, `score_lag_months = 1`, `score_start_date`, `regime_label_start_date`, `available_blocks`, `missing_blocks`, `optional_blocks_missing`, `planned_not_loaded`, `coverage_ratio`, `coverage_tier`, `data_sources_used`, `available_regimes_count`, `available_regimes_by_quality`, `regime_counts` (primary, 5-key dict with `neutral_transition = 0`), `regime_legacy_counts` (legacy 5-bucket), `transition_summary`, `base_10y`, `regimes`, `stability_summary`, `labels_monthly` (carries `regime`, `regime_legacy`, `transition_flag`, `transition_reason`), and `method_disclaimer`.

`transition_summary` block must include `n_scored_months`, `n_transition_months`, `transition_share`, `transition_reason_counts` (counts per reason), `transition_reason_shares`, `transition_by_primary` (count of transition months per primary regime), `primary_vs_transition_pivot` (per primary regime, the `non_transition` vs `transition` count), and `legacy_neutral_transition_share`. The same block is mirrored under `regime_label_quality_check.transition_summary`.

`macro_regime_diagnostics` must also include `regime_label_quality_check` (diagnostic-only) with:

- `history_months`: number of months with valid composite scores **and** an assigned regime label (the warmup tail of the rolling z-score window is excluded).
- `rows_input_total`: total number of rows fed into the quality check.
- `warmup_months_excluded`: rows dropped because composite scores were not yet available (warmup of the rolling z-score window). Quality statistics are computed on scored months only.
- `by_regime`: n_obs, history share, first/last occurrence, episode-duration statistics, and quality status (`insufficient_data` / `low_confidence` / `usable` / `reliable`).
- `episode_history`: contiguous regime episodes (`regime`, `start_date`, `end_date`, `length_months`).
- `stability_summary`: switch count, average months between switches, one-month share, <3m share, and warning flags.
- `macro_sanity_checks`: directional plausibility checks for 2008, 2020, 2021–2022, 2022–2023 windows.
- `metadata_quality`: distributions for `coverage_tier`, `confidence_level`, and block-availability frequencies.
- `overall_assessment`: `history_usable`, caution/noise flags, and warning strings.

`coverage_tier` semantics:

- `full`: every block listed above has at least one resolved indicator.
- `extended`: at most two blocks unresolved and all required (non-optional) blocks resolved.
- `reduced`: more than two blocks unresolved but more than five blocks still resolved.
- `fred_baseline`: only FRED-resolvable blocks resolved (i.e. `data_sources_used` values are all `fred` or `unavailable`), regardless of count.
- `insufficient`: fewer than five blocks resolved.

Optional blocks (`growth_nowcast`) missing alone — for example, when GDPNow is temporarily unresolved — does not pull `confidence_level` below `medium` on its own. Historical reference: the NY Fed Nowcast was discontinued in 2021 and was retired from the active classifier on 2026-05-07; GDPNow (FRED:GDPNOW) is now the sole indicator in this block.

Confidence rules:

- If either composite score has `|score| <= neutral_band`, `confidence_level = low` and `regime_transition_warning = true`.
- Otherwise `confidence_level` follows `coverage_tier`: `full` / `extended` → `high`, `reduced` / `fred_baseline` → `medium`, `insufficient` → `low`.

Per-regime n_obs gating in monthly observations:

- `0`: `no_observations`.
- `1` to `11`: `insufficient_data`. `factor_regression`, `factor_covariance`, `portfolio_factor_risk`, and `portfolio_factor_rc` are reported as suppressed (status `insufficient_data`, no estimates).
- `12` to `23`: `low_confidence`. The block uses linear shrinkage to `base_10y` with `shrinkage_weight_regime = clip((n_obs - 12) / 12, 0, 1)`.
- `24` to `59`: `usable`. The block uses raw regime-specific estimates.
- `60+`: `reliable`. The block uses raw regime-specific estimates and is suitable for analytical use.

`portfolio_factor_rc` must include `rc_share`, `rc_sign`, and `interpretation`. Positive RC means `risk_adder`; negative RC means `hedging_or_diversifying_contribution`.

`stability_summary` uses a global beta-gap threshold of 0.25 and must include the warning `Stability threshold is a global heuristic, not factor-specific calibration.` Policy signals are `green/general_signal`, `yellow/regime_only`, and `red/do_not_use_as_single_signal`.

CSV artifacts written under `results_csv/` include:

- `macro_regime_labels_monthly.csv` (replaces the previous `macro_regime_labels_weekly.csv`).
- `macro_regime_factor_betas.csv` (filename preserved; contents now monthly).
- `macro_regime_factor_covariance.csv` (filename preserved; contents now monthly).
- `macro_regime_factor_rc.csv` (filename preserved; contents now monthly).
- `macro_regime_indicator_panel.csv` (new; per-month indicator level/momentum and z-scores).
- `regime_label_quality_by_regime.csv`.
- `regime_label_episode_history.csv`.
- `regime_label_stability_summary.csv`.

Additionally, the run writes `regime_label_quality_summary.json` to the variant output folder (for example `Main portfolio/`).

`stress_commentary.txt` must report method version, current regime, latest growth and inflation scores, the per-block sub-scores when present, `coverage_tier` with available/missing/optional blocks, regime confidence, transition warning, available usable/reliable regimes, the ECI quarterly-ffill caveat when ECI is available, the GDPNow quarterly-ffill caveat when GDPNow is available, the look-ahead lag/no-vintage caveat, top unstable betas, policy signal counts, the stability-threshold warning, and the method disclaimer. When `stress_report.json.regime_factor_analytics` is present, it must also state that `macro_two_axis_v1` label history may extend beyond the **10Y** `portfolio_regime_analytics_window` and that per-regime `n_obs` / matrices / betas / exposures / variance shares / average factor moves refer only to that overlap.

`stress_commentary.txt` must also include a short **Regime Label Quality Check** subsection with usability verdict, reliable/weak regimes, stability/noise interpretation, and explicit cautions when any regime has `<24` observations or switching is flagged as noisy.

#### 8.8.3 Regime-specific asset and factor analytics (`regime_factor_analytics_v1`)

`stress_report.json.regime_factor_analytics` is diagnostic-only statistical infrastructure for future regime-aware optimization. It does **not** change `macro_two_axis_v1`, optimizer behavior, mandate gates, stress pass/fail, or weight release.

**Inputs.** Primary regime labels remain **monthly** (lagged `macro_regime_diagnostics.labels_monthly`, which may span the full available macro history). The production `run_report.py` path joins them with **weekly** portfolio asset returns (Friday week-ends from the same daily price pipeline as stress factor betas) and the **weekly** nine-factor matrix from `build_factor_matrix`, forward-filling the latest monthly `regime` (and `transition_flag` when used) onto each week (`weekly_alignment = forward_fill_monthly_label`). If weekly asset/factor history cannot be built, the pipeline falls back to the legacy **monthly** inner join: monthly FX-converted asset returns and `build_factor_matrix_monthly`. Current portfolio weights feed bottom-up portfolio factor exposure in both modes.

**Portfolio analytics window (mandatory).** All portfolio-facing regime statistics are computed **only** on the standard **10Y** overlap ending at `analysis_end`, aligned with the main return/metrics/covariance/factor horizons: last `FACTOR_WEEKS_10Y` (≈520) aligned weekly rows when the weekly path is used, or `FACTOR_MONTHS_10Y` (120) month-ends when the monthly fallback is used. The macro classifier output in `macro_regime_diagnostics` may still cover a longer label history; `stress_report.json.regime_factor_analytics`, `regime_factor_analytics_summary.json`, and the `regime_*.csv` tables must disclose **`regime_label_history_span`** (full `labels_monthly` range) versus **`portfolio_regime_analytics_window`** (`label = 10Y`, targets, `analysis_end`, and the realized `actual_*` overlap). Per-regime **`n_obs` counts rows only inside that overlap** (weeks or months per `frequency`).

**Frequency.** `frequency = weekly` is the default production path (with monthly labels). `frequency = monthly` remains supported. JSON carries `frequency` and, when weekly, `weekly_alignment`.

**Gating.** `n_obs` in each regime slice is the **number of aligned rows** (weeks in weekly mode, months in monthly mode). Quality labels (`insufficient_data` / `low_confidence` / `usable` / `reliable`) use the **same calendar-duration intent** as §8.8.2 by mapping weekly counts to **month-equivalent** observations (`round(n_weeks * 12 / 52)`) before applying the `12 / 24 / 60` thresholds. Below ~12 month-equivalent, asset/factor covariance, asset betas, and factor RC in that slice are suppressed; `n_obs` and quality are still reported.

**Computations per primary regime.** Asset and factor covariance use **Ledoit–Wolf** shrinkage (`sklearn.covariance.LedoitWolf`, `assume_centered=False`) on **complete-case** rows (`dropna(how="any")`) when at least two such rows exist; correlations derive from that covariance. If Ledoit–Wolf fails, **complete-case** sample covariance (`ddof=1`) is used; if fewer than two complete rows exist, **pairwise** sample covariance on the regime slice applies. PSD is flagged (`psd` / `not_psd`) without silent repair unless a project-standard repair helper exists. Per-asset OLS of returns on all nine factors with HAC Newey–West inference (Bartlett kernel, lag rule `max(1, min(cap, floor(4*(n/100)^(2/9))))` with **monthly cap 12** and **weekly cap 15**). Portfolio factor betas = weighted sum of asset betas (weights_coverage reported). Factor variance contribution uses the **factor** Ledoit–Wolf (or fallback) covariance: `β_pf' Σ_factor β_pf` decomposed into `beta_i * (Σ beta)_i`, shares normalized to total factor variance; `dominant_factors` lists top contributors by absolute share.

**Outputs.** CSV under `results_csv/`: `regime_asset_covariance.csv`, `regime_asset_correlation.csv`, `regime_factor_covariance.csv`, `regime_factor_correlation.csv`, `regime_asset_factor_betas.csv`, `regime_portfolio_factor_exposures.csv`, `regime_factor_variance_contribution.csv`, `regime_factor_average_moves.csv`. Each row repeats the regime block metadata (`regime`, `n_obs`, `quality_status`, `not_for_optimization` (regime-level), `transition_split`, `confidence_split`, `data_start`, `data_end`, `estimate_suppressed` when applicable) and adds flattened **`regime_label_history_*`** and **`portfolio_regime_analytics_*`** columns so the label span vs 10Y analytics window is explicit on export. Summary JSON: `regime_factor_analytics_summary.json` in the variant final folder. The slim `stress_report.json` block omits full covariance nests; full matrices appear in CSV.

**Splits.** Optional `enable_transition_split` adds keys like `goldilocks__transition_true`. Per-month `confidence_level` splits require a time-aligned series; until available, `enable_confidence_split` logs a warning and skips.

**Errors.** On failure, `regime_factor_analytics_error` is set and the report continues.

#### 8.8.4 Regime-level daily portfolio metrics (`regime_portfolio_metrics_v1`)

`stress_report.json.regime_portfolio_metrics` is **diagnostic-only**. It does not change `macro_two_axis_v1`, optimizer behavior, mandate gates, stress pass/fail, or weight release.

**Purpose.** For each **primary** regime (`goldilocks`, `reflation`, `stagflation`, `recession_disinflation`), compute portfolio and per-asset metrics on **daily** simple returns using the same **conceptual** rules as the base monthly pipeline (`metrics_specification.md`): sample std/cov with `ddof=1`, **Sharpe** uses **raw** return volatility in the denominator, **Sortino** uses downside deviation vs MAR (default MAR = aligned daily risk-free; optional Series), **annualization** uses **252** trading days (`vol_annual = std * sqrt(252)`, mean excess scaled by `252` where applicable). **Treynor** is `(mean(excess) * 252) / beta_base` when `beta_base` is finite and non-zero. **CAGR** uses the daily equity curve with exponent `252 / n_trading_days`. Skewness and kurtosis use **log** daily returns. **Max drawdown** and **time to recovery** follow the monthly definitions applied to the daily equity curve; recovery is reported in **trading days** with `ttr_unit: "trading_days"`.

**Label alignment.** Monthly primary regime labels are **forward-filled** to each trading day (`regime_label_alignment = monthly_label_forward_filled_to_daily`), consistent with the daily `regime_factor_analytics` path.

**Weights and NaNs.** Portfolio return is a **fixed-weight** linear combination of held assets (positive optimizer weights only). Weights are **renormalized** over held names present in the daily return columns. Rows with **any** missing return among held assets are dropped (**complete-case** slice). This MVP does not apply the monthly `dynamic_nan_safe` cash redistribution to regime slices.

**Risk-free and benchmark.** Daily risk-free is built from the same monthly effective series as the main report, expanded to the trading-day index: `ffill` from month-end observations, then **`bfill`** so days **before** the first published month-end rate use the earliest available rate (no look-ahead into future month-ends). Benchmark daily returns match **Beta_base** rules for the investor currency (e.g. SPY/VOO for USD). Optional per-ticker **local** daily benchmarks feed **Beta_local** when provided.

**Quality gating (trading days).** Per-regime `quality_status` uses the same **daily** buckets as `regime_factor_analytics_v1` in daily mode: `n_obs_days < 60` → `insufficient_data`; `60–125` → `low_confidence`; `126–503` → `usable`; `504+` → `reliable`. All four primary regime keys are always present; empty regimes carry `no_observations` or warnings as appropriate.

**Covariance and RC_vol.** **Ledoit–Wolf** on complete-case asset returns per regime (same helper as §8.8.3 daily mode); covariance in JSON is **annualized** (`× 252`). **RC_vol** is percentage **contribution to portfolio variance** using **fixed** weights and the **daily** (non-annualized) regime covariance for PC denominators, averaged over regime days—consistent in spirit with `metrics_specification.md` RC_vol.

**Historical VaR/ES.** Computed on the regime portfolio return series when `n_obs_days >= 60` (same floor as `insufficient_data` for daily regime analytics); below that threshold, VAR/ES fields are marked unavailable with an explicit reason.

**Factor analytics reuse.** When `run_report.py` passes the existing `regime_factor_analytics` payload, each regime’s `factor_analytics` embeds a **slim** subset (exposures, variance contribution, betas, HAC metadata, etc.) **without** duplicating OLS. Full factor matrices remain in `regime_factor_analytics` CSV/JSON as today.

**vs base monthly report.** Not a full mirror: no rolling 12M/36M regime Sharpe strips, no mandate MaxDD gate, no replacement of snapshot monthly windows. Items that are not meaningful on a short regime slice are omitted or carry `metric_available: false` and `unavailable_reason`.

**Artifacts.** Slim block in `stress_report.json`. Summary: `regime_portfolio_metrics_summary.json` under `output_dir_final`. CSV exports under `results_csv/` (e.g. per-regime flattened metrics and covariance/correlation tables—see `regime_portfolio_metrics_csv_frames` in code).

**Errors.** On failure, `regime_portfolio_metrics_error` is set and the report continues.

---

### 8.9 Factor variance decomposition

`stress_report.json.factor_variance_decomposition` is a diagnostic-only 5Y weekly decomposition of total portfolio variance into base factor sources plus residual risk. It excludes Oil. It does not change stress pass/fail, mandate status, optimizer behavior, or weight release.

All variance quantities in this block use `variance_scale = "weekly"` and sample variance/covariance with `ddof=1`. The calculation must use the same weekly rows as `factor_regression_5y`: portfolio weekly return `y`, factor matrix `X`, and OLS factor beta vector `b` excluding the intercept.

Required formulas:

- `portfolio_total_variance = Var(y)`
- `Sigma_f = Cov(X)`
- `factor_variance = b' Sigma_f b`
- `variance_based_explained_share = factor_variance / portfolio_total_variance`
- `residual_share = 1 - R2`
- `net_component_variance_i = beta_i * (Sigma_f b)_i`
- `factor_rc_share_i = net_component_variance_i / factor_variance`
- `net_total_variance_share_i = factor_rc_share_i * R2`

The normalization rule is mandatory: `factor_rc_share` is normalized relative to `factor_variance` before applying `R2`. Signed `factor_rc_share` values should sum to `1.0` when `factor_variance > 0`; signed factor `net_total_variance_share` values should sum to `R2`.

Guardrails:

- If `n_obs < 30`, return `status = "unavailable"` and `reason = "insufficient_observations"`.
- If `portfolio_total_variance <= 1e-12`, return `status = "unavailable"` and `reason = "degenerate_portfolio_variance"`.
- If `factor_variance <= 1e-12`, return `status = "unavailable"` and `reason = "degenerate_factor_variance"`.
- If beta vector length, covariance matrix shape, covariance factor order, and factor matrix columns do not match exactly, return `status = "unavailable"` and `reason = "factor_dimension_mismatch"`.

The cross-check is mandatory when inputs are valid. `cross_check.status` compares `variance_based_explained_share` with `R2`: `pass` when absolute difference is `<= 0.005`, `warning` when it is `> 0.005` and `<= 0.02`, and `high_warning` when it is `> 0.02`. Warning codes are local diagnostics: `WARN_FACTOR_VARIANCE_DECOMP_MISMATCH` and `WARN_FACTOR_VARIANCE_DECOMP_HIGH_MISMATCH`.

Each factor row must include signed net fields (`net_component_variance`, `factor_rc_share`, `net_total_variance_share`, `direction`) and gross fields (`gross_component_variance_abs`, `gross_factor_rc_share`, `gross_total_variance_share`). Gross fields use `abs(net_component_variance)` to show concentration before hedge netting. `direction` is `neutral` when `abs(net_total_variance_share) < 1e-4`, otherwise `risk_adder` for positive signed contribution and `hedger` for negative signed contribution. The report must expose separate `risk_adders`, `hedgers`, `neutral_factors`, and `gross_top_contributors_abs` lists.

Sanity warnings are local only and must not change suite status:

- `WARN_FACTOR_VARIANCE_DECOMP_EXTREME_NET_SHARE` when any `abs(net_total_variance_share_i) > 1.0`.
- `WARN_FACTOR_VARIANCE_DECOMP_HIGH_GROSS_CONCENTRATION` when gross total share exceeds `R2 + 0.25`.
- `WARN_FACTOR_VARIANCE_DECOMP_SHARE_SUM_MISMATCH` when signed net shares do not sum to `R2` within `1e-6`.

Residual diagnostics classify `residual_share`: `low` below `0.35`, `moderate` from `0.35` to below `0.60`, and `high` at `0.60` or above. High residual means the current factor model leaves most portfolio variance unexplained and should prompt review of omitted factors, nonlinear exposures, asset-specific risk, factor definitions, and beta stability.

Stability v1 is intentionally minimal. When enough rolling weekly snapshots exist, report factor `sign_stability_share` and severity (`high` below `0.65`, `moderate` below `0.80`, otherwise `low`) plus R2 p10/p90 and severity (`high` when p10 R2 is below `0.25`, `moderate` below `0.40`, otherwise `low`). If rolling snapshots cannot be built, return `stability.status = "unknown"` and `reason = "insufficient_rolling_observations"`.

CSV artifacts written under `results_csv/` include:

- `factor_variance_decomposition_5y.csv`

### 8.10 Portfolio PCA diagnostics

`stress_report.json.portfolio_pca` is a diagnostic-only PCA block for hidden statistical
risk concentration. It does not change stress pass/fail, mandate status, optimizer
behavior, or weight release.

The universe is the current portfolio's positive-weight assets. If no positive weights are
available, all configured tickers may be used. Inputs are weekly Friday returns from
adjusted close prices, ending at `analysis_end`, with the default 5Y window of 260 weekly
observations. At least two assets and at least 52 aligned weekly rows are required; otherwise
the block returns `status = "unavailable"` with a `reason`.

The block reports two return layers:

- `raw`: PCA on original weekly asset returns.
- `residual`: PCA on each asset's OLS residual after regressing weekly asset returns on the
  current named factor registry (`equity`, `real_rates`, `inflation`, `credit`, `usd`,
  `commodity`, `vix`, `us_growth`, `oil`) when factor history is available.

Each layer contains two separate PCA interpretations:

- `covariance_pca` has `interpretation = "risk_dominance"`. It is PCA on the sample
  covariance matrix with `ddof=1`; PC1 measures how much total risk variance is dominated
  by one statistical direction, including asset volatility scale.
- `correlation_pca` has `interpretation = "structure"`. It is PCA on the sample correlation
  matrix, equivalently covariance PCA after standardizing each asset's weekly returns;
  PC1 measures common movement structure after removing volatility scale.

Each PCA object includes `explained_variance_ratio`, `cumulative_explained_variance_ratio`,
`components`, `pc1_explained_variance_ratio`, `pc1_concentration_ratio`,
`pc1_severity`, `effective_number_of_bets`, `effective_number_of_bets_ratio`,
`enb_severity`, `rolling_pc1`, and `pc1_factor_correlations` when factor rows are
available. Component signs are deterministic: the loading with largest absolute magnitude
is forced positive.

`pc1_concentration_ratio = pc1_explained_variance_ratio / (1 / n_assets)`. Severity is:
`low` when `pc1 < 0.40` and concentration `< 2.0`; `moderate` when `pc1 >= 0.40` or
concentration `>= 2.0`; `high` when `pc1 >= 0.60` or concentration `>= 3.0`; `extreme`
when `pc1 >= 0.75` or concentration `>= 4.0`.

Effective number of bets is `1 / sum(p_i^2)`, where `p_i` are PCA explained-variance
shares. `effective_number_of_bets_ratio = ENB / n_assets`. ENB severity is `high` below
`0.35`, `moderate` below `0.55`, otherwise `low`. Covariance ENB is effective risk bets;
correlation ENB is structural diversification.

`rolling_pc1` uses a 52-week window and 4-week step. Its summary includes latest, mean,
std, min, max, p10, p90, trend slope per year, latest-minus-mean, latest-minus-p10,
latest-minus-p90, window count, and stability severity. Stability severity is `high` when
the annualized trend slope is greater than `0.10` or latest PC1 is above p90, `moderate`
when slope is greater than `0.05` or latest is above mean plus one standard deviation,
otherwise `low`.

`pc1_factor_correlations` correlates PC1 scores with the current named factor matrix on
the same weekly rows and reports all correlations plus the top three by absolute value.
For raw PCA this helps label PC1 economically. For residual PCA it is an omitted-structure
check: strong residual PC1 correlation with a named factor suggests factor leakage,
definition mismatch, or an incomplete factor model.

CSV artifacts written under `results_csv/` include:

- `portfolio_pca_summary_5y.csv`
- `portfolio_pca_components_5y.csv`
- `portfolio_pca_rolling_pc1.csv`
- `portfolio_pca_pc1_factor_correlations.csv`

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
