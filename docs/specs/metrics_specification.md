# Portfolio Metrics Specification (Single Source of Truth)

This document defines all formulas, conventions, and estimators for the Portfolio Metrics Standard. All code must implement these definitions exactly.

### Config `returns_frequency` (runtime contract)

- **Canonical main-metrics cadence:** monthly simple returns for all sections below unless a subsection explicitly names another cadence (for example daily regime diagnostics governed by `stress_testing_spec.md`).
- **Config field:** `returns_frequency` may be `monthly`, `weekly`, or `daily`, but the loader and report/optimizer pipelines **always build the main investor return panel at monthly cadence**. Non-monthly values are stored as `configured_returns_frequency` in `frequency_disclosure` and input-assumption metadata only.
- **Rationale:** Prevents mixed daily-vs-monthly portfolio metrics, covariance, RC_vol, correlation, mandate checks, and optimizer inputs when operators experiment with higher-frequency config values.

---

## 1. Analysis end and windows

### 1.1 analysis_end

**Definition:** `analysis_end` is the **last completed effective month-end (previous month-end)** = last effective month-end strictly before today.

- "Effective month-end" = last available trading day of that month in the price/return series.
- "Strictly before today" = the month-end date must be < today's date (no partial current month).

**Example:** If today is 2025-02-15, then `analysis_end` is 2025-01-31 (or the last trading day of January 2025, e.g. 2025-01-31). If today is 2025-02-01, then `analysis_end` is 2025-01-31.

**Implementation:** Given a monthly index (e.g. from resampled prices) and `today` (date or timestamp), take the set of month-end dates in the index that are strictly less than `today`, and set `analysis_end = max(that set)`.

### 1.2 Windows

- Windows are **fixed-length** in months: e.g. 36, 60, 120.
- Each window **ends at** `analysis_end`.
- Window start = the month such that the number of months from start to end (inclusive) equals the window length.
- **slice_window(series, analysis_end, window_months)** returns the subset of `series` with index from window start to `analysis_end` (inclusive).

---

## 2. Frequency and returns

### 2.1 Data source

- **All prices must be downloaded as Adj Close** (adjusted close). Daily **Adj Close** from yfinance.
- Resample to **effective month-end**: for each calendar month, take the **last available trading day** in that month (no interpolation).

### 2.2 FX

- Convert **prices** to `investor_currency` **before** computing returns.
- Spot FX tickers: e.g. `EURUSD=X` = units of USD per 1 EUR.
- Rules:
  - Asset in EUR, investor in USD: `P_USD = P_EUR * FX(EURUSD=X)`.
  - Asset in USD, investor in EUR: `P_EUR = P_USD / FX(EURUSD=X)`.
  - If investor != USD: convert asset -> USD, then USD -> investor:
    `P_USD = P_asset * FX(asset_ccyUSD=X)`,
    `P_investor = P_USD / FX(investor_ccyUSD=X)`.
- If FX ticker not available in required orientation, use inverse pair and invert: **FX = 1 / FX_inverse**.
- FX daily may be **forward-filled** to align with asset calendars; **asset returns are never interpolated**.

### 2.3 Return definitions

- **Monthly simple return:**
  **r_t = (P_t / P_{t-1}) - 1**
- **Monthly log return:**
  **lr_t = ln(P_t / P_{t-1})**

Returns are computed **after** converting prices to investor currency.

---

## 3. Estimators (sample, ddof=1)

All variance, covariance, and standard deviation used in metrics must use **sample** estimators with **ddof=1**:

- **Var(r)** = mean of squared deviations, with divisor (N-1): `np.var(r, ddof=1)` or `pd.Series(r).var(ddof=1)`.
- **Std(r)** = sqrt(Var(r)): `np.std(r, ddof=1)` or `pd.Series(r).std(ddof=1)`.
- **Cov(r_a, r_b)** = sample covariance with (N-1): `np.cov(r_a, r_b, ddof=1)[0,1]` or `pd.Series(r_a).cov(pd.Series(r_b))` (pandas uses ddof=1 by default for cov).

**Requirement:** In code, pass **ddof=1** explicitly wherever std/var/cov are used for these metrics and for Sigma in RC_vol. For **Beta_base** and **Beta_local** always use **var(..., ddof=1)** and **cov(..., ddof=1)**; do not rely on library defaults.

---

## 4. Alignment

- For **excess returns**, **Sharpe**, **Sortino**, **Treynor**, **Beta**, **cov**, **corr**, and **RC_vol**:
  - Align **asset returns**, **benchmark returns**, and **risk-free (rf)** series by **inner join** on date.
  - Use only dates where all required series have non-NaN values (synchronous observations).

---

## 5. Risk-free rate

- Built-in default for **USD**: **FRED DTB3** (3-Month Treasury Bill, secondary market, annual percent).
- Built-in default for **EUR**: **ECB €STR** (Euro Short-Term Rate, annual percent).
- Convert the annual percent series to **monthly effective rate:**
  **rf_monthly = (1 + y/100)^(1/12) - 1**
- Resample to month-end: use **last available value** in each month.
- If investor currency is not covered by a built-in default and no explicit rf source/ticker is
  provided: **fail fast** (do not guess).

---

## 6. Metrics per asset (per window)

All per-window metrics use **monthly simple returns** unless stated otherwise. Dates are aligned by inner join where needed.

### 6.1 CAGR

- **Base:** Equity curve from **monthly simple returns** (not log returns).
- **Equity_t = cumprod(1 + r_simple)** over the window (first value can be 1.0 or from first return).
- **CAGR = (Equity_end / Equity_start)^(12 / N_months) - 1**
  where N_months = number of months in the window.

### 6.2 Volatility (Vol)

- **Vol_monthly = std(r_simple, ddof=1)** over the window (aligned series).
- **Vol_annual = Vol_monthly * sqrt(12)**.

### 6.3 Sharpe ratio

- **Sharpe = (mean(r_simple - rf_monthly) * 12) / (std(r_simple, ddof=1) * sqrt(12))**.
- Numerator: annualized excess return (align r_simple and rf_monthly by inner join).
- **Volatility in the denominator must be calculated from raw returns (r_simple), not from excess returns.**

### 6.4 Sortino ratio

- Sortino must be computed relative to **MAR (Minimum Acceptable Return)**. By default **MAR_monthly = rf_monthly**; it can be overridden by explicitly setting a custom MAR parameter.
- **downside_t = min(0, r_simple_t - MAR_t)** (MAR scalar or series aligned by date).
- **dd_monthly = sqrt(mean(downside^2))** (downside deviation).
- **dd_annual = dd_monthly * sqrt(12)**.
- **Sortino = (mean(excess) * 12) / dd_annual**.

### 6.5 Beta (two types)

There are two types of beta - do not confuse them.

#### 6.5.1 Beta_base (portfolio management)

- **Beta_base = Cov(r_asset, r_benchmark) / Var(r_benchmark)**
  with **var(..., ddof=1)** and **cov(..., ddof=1)** explicitly; same dates (inner join). Do not rely on library defaults.
- Single base benchmark in investor currency for **unified market risk scale**:
  - **USD**: S&P 500 (proxy: SPY or VOO)
  - **EUR**: STOXX Europe 600 (proxy: VGK or EXSA.DE)
  - **JPY**: Nikkei 225 (proxy: EWJ)
  - **CHF**: Swiss Market Index SMI (proxy: EWL)
- Computed on **monthly simple returns**, same dates, same window, same method for all assets.
- Used for comparing assets and controlling total market exposure of portfolio.

#### 6.5.2 Beta_local (diagnostic, per-asset only)

- Computed for each asset individually to understand which "local market" the asset resembles.
- **Not a portfolio metric** - diagnostic only.
- Same calculation rules as Beta_base: monthly simple returns, one window, aligned dates, ddof=1.

**Local benchmark dictionary (proxies):**

| Asset class | Proxy ETF |
|-------------|-----------|
| US equity | VOO (S&P 500) |
| Europe equity | VGK |
| UK equity | EWU |
| Japan equity | EWJ |
| EM equity | VWO |
| China equity | MCHI |
| Asia ex-Japan equity | AAXJ |
| Canada equity | EWC |
| Australia equity | EWA |
| Global ex-US equity | VXUS |
| US Aggregate IG bonds | BND (or AGG) |
| US Treasuries 7-10Y | IEF |
| US Long Treasuries | TLT |
| US TIPS | TIP |
| US High Yield | HYG (or JNK) |
| US IG Corporates | LQD |
| Short T-Bills / Cash proxy | BIL |
| Broad commodities | PDBC (or DBC) |
| Industrial metals | DBB |
| Energy | XLE |

**Hard special rules:**
- **Crypto**: Beta_local = Beta_base, local benchmark = S&P 500 (proxy VOO).
- **Gold**: Beta_local = Beta_base, local benchmark = S&P 500 (proxy VOO).

### 6.6 Treynor ratio (diagnostic)

- **Treynor = (mean(excess) * 12) / Beta_base**
  where Beta_base is computed on the same window and same aligned dates.

### 6.7 Skewness and kurtosis (diagnostic)

- Compute on **monthly log returns** (lr_t) over the window.
- Use standard sample skewness/kurtosis (e.g. `scipy.stats` or pandas with appropriate ddof if applicable).

### 6.8 Max drawdown (MDD)

- **Equity** = cumprod(1 + r_simple) over the window.
- **Running max:** cummax(Equity).
- **Drawdown_t = Equity_t / cummax(Equity)_t - 1**.
- **Max Drawdown = min(Drawdown)** over the window.

### 6.9 Time to recovery (TTR)

- From the **peak immediately before the maximum drawdown trough**: count **monthly observations**
  until the first post-trough month where **Equity >= value at that peak**.
- Count months by return-index position, not by approximating calendar days.
- If no drawdown occurs in the window: **ttr = 0**, **recovered = True**.
- If equity never recovers to the prior peak by end of window: **ttr = NaN**, **recovered = False**.

---

## 7. Portfolio (NaN-safe dynamic)

- At each month **t**:
  - **w_avail** = target weights only for assets that have **non-NaN** return at t (do **not** renormalize).
  - **w_miss = 1 - sum(w_avail)**.
  - **R_p,t = sum(w_avail_i * R_i,t) + w_miss * R_cash,t**.
- Cash-proxy defaults: **BIL** for USD and **PEU** for EUR. If investor currency is not covered by
  a built-in cash-proxy default, require **explicit** `cash_proxy_ticker` in config.

---

## 8. RC_vol (percentage risk contribution)

- **RC_vol** must be defined as **percentage contribution to portfolio variance** (not contribution to volatility; not via correlations).
- **Sigma_window** = covariance matrix of **monthly simple returns** over the window (inner-joined, **ddof=1**).
- For each month **t** in the window:
  - **sigma_sq_t = w_t^T Sigma_window w_t** (portfolio variance at t).
  - **PC_{i,t} = (w_{i,t} * (Sigma_window w_t)_i) / sigma_sq_t**.
  - **RC_window_i = mean_t(PC_{i,t})** over the window.
- **PC must sum to 1** across assets at each t.
- Do not compute contribution to volatility or via correlations.

---

## 9. Output Formatting Standard

- **All reported numeric metrics must be rounded to 3 decimal places.**
- Rounding applies **only at the final output stage** (before exporting CSV or printing), not during intermediate calculations.
- Use standard half-up rounding via pandas **.round(3)** for DataFrames and Series.
- **Do not round** raw returns, covariance matrices, or intermediate values used in further calculations.
- **Persist full precision internally**; round only exported/report-facing results.
- No intermediate rounding must affect Sharpe, beta, RC_vol, CAGR, or any other metric calculations.

---

## 10. Output and persistence

- Export asset metrics to CSV: e.g. **asset_metrics_3y.csv**, **asset_metrics_5y.csv**, **asset_metrics_10y.csv** (flat columns). Apply **.round(3)** to metric DataFrames before saving.
- Persist **all input series** used (monthly prices, monthly returns, rf monthly, base benchmark returns, cash proxy returns, FX series used) at **full precision**; do not round inputs.

---

## 11. PORTFOLIO ANALYTICS STANDARD

### FOR PORTFOLIO WITH GIVEN WEIGHTS (windows 3Y / 5Y / 10Y monthly)

- 10Y: base "structural" estimate and full cycle. Use as anchor for long-term conclusions (average return, base volatility, base correlations, base beta_base).

- 5Y: test whether the structure is still valid in the current regime. If 5Y diverges strongly from 10Y, the regime likely changed and 10Y cannot be used without adjustments.

- 3Y: operational regime-shift radar (especially real rates / inflation / liquidity). Used for triggers and risk-control, not for strategic long-term allocation conclusions.

### RETURN AND BASE RISK

- Return: compute CAGR (geometric) for the window on log-returns and annualize; additionally compute annualized return on simple returns (for PnL intuition)

- Volatility: monthly and annualized on simple returns

- Correlation / Covariance / RC_vol: compute on the same simple returns (single base for risk analytics and risk contributions)

- Max Drawdown + Time to Recovery: computed on simple returns using the equity curve (peak-to-trough; recovery = period until equity >= peak)

- Sharpe / Sortino / Downside deviation (annualized): computed on simple returns; excess-return and MAR are relative to the investor cash rate (default USD 3M T-bill converted to the data periodicity)

- Beta_portfolio (relative to a single benchmark): computed on the same simple returns relative to one investor base benchmark (e.g., S&P 500)

- Treynor (if used): annualized portfolio excess return relative to investor cash rate divided by Beta_portfolio (same benchmark and same window/dates)

### ROLLING SHARPE / ROLLING SORTINO

- Rolling Sharpe/Sortino: computed on simple returns with investor cash rate subtracted (risk-free / MAR)

- Windows:

36 months primary

12 months fast indicator

Usage rule:
Take action only when deterioration is visible in the 36-month window.
If deterioration appears only in the 12-month window, treat it as temporary noise.

### DRAWDOWN STRUCTURE

- For every drawdown compute depth and length.

- Compute recovery time statistics: median + p90 (not only average).

- Compute time underwater:

percentage of time below peak

longest underwater period.

- Compute statistics separately for drawdowns greater than:

5%

10%

20%

Purpose:
MaxDD shows the depth of losses, while drawdown structure shows how long the portfolio may take to recover.

### RISK DYNAMICS

- Compute rolling volatility on monthly simple returns using a 12-month window, annualized.

- Compute vol-of-vol = std(rolling volatility) over the analysis period.

- Compute relative vol-of-vol = std(rolling volatility) / mean(rolling volatility) to compare assets.

- Optional fast radar: 6-month rolling volatility, but decisions should rely on the 12-month measure.

### RISK CONTRIBUTION OF ASSETS

Compute MRC (marginal risk contribution) and CTR / RC_vol (component risk contribution) for each asset using the covariance matrix of simple returns.


### RETURN ATTRIBUTION

- Compute Return Contribution of each asset to portfolio return (using simple returns in investor currency).

- Compare Return Contribution with RC_vol (CTR).

- Identify assets with consistently high return per unit of risk contribution (check on 10Y and rolling 36M windows).

Purpose:
Connect risk contribution and return contribution.

### BETA ANALYSIS

- Compute beta on simple returns for both the portfolio and individual assets.

- Compute each asset's contribution to portfolio beta:

wi * Cov(Ri , Rm) / Var(Rm)

The sum of contributions equals portfolio beta.

- Compute rolling beta using windows:

36 months primary

12 months radar

For rolling beta evaluate:

current value

mean

10-90% range

min/max optional.

- Downside beta:
compute using only months where market return < 0.

- Upside beta:
compute using only months where market return > 0.

Base: monthly simple returns for both market and portfolio/assets with identical dates.

### EFFECTIVE EQUITY EXPOSURE

Select months where benchmark return is in the worst 10% / 20% / 30%.

Compute crisis beta on those months:

beta_crisis using monthly simple returns.

Define:

EEE = beta_crisis * 100%

EEE measures how much the portfolio behaves like equities during stress periods.

### DISTRIBUTION SHAPE

- Compute skewness and kurtosis of portfolio returns using monthly log-returns over windows:

5Y

10Y

optional 3Y radar.

Diagnostic only.
Used as tail-risk flags, not as optimization targets.

Negative skew and high kurtosis indicate higher probability of sharp drawdowns.

### MONTE CARLO + IRR ANALYSIS

Purpose: evaluate distribution of future outcomes rather than predict markets.

Method:

Run 100,000 simulations using contiguous-segment bootstrap.

Randomly construct future paths by stitching real historical return segments (3-12 months) to preserve tails and regime persistence.

Data:

Use monthly simple returns for portfolio and assets so correlations are preserved.

Capital simulation:

Define starting capital, contribution schedule, and investment horizon.

Simulate capital via compounding plus contributions.

Metrics:

Compute distributions of final capital and CAGR/IRR percentiles:

P10, P25, P50, P75, P90.

Also compute probability of failing to achieve a minimum acceptable return (floor return):

share of simulations where IRR or CAGR < floor (for example below USD cash rate or below a predefined annual target).

IRR is computed in every simulation using all cash flows (contributions and final portfolio value).

### VAR AND EXPECTED SHORTFALL

- Horizons:

Compute

1M ES (primary tail risk measure relevant for MaxDD)

1D ES (operational indicator only)

- Method:

Use Historical VaR and Expected Shortfall from realized returns.

No Monte Carlo and no normality assumptions.

- Returns base:

Daily simple returns.

- Report / Diagnosis implementation (`run_report.py` STEP 9b):

Portfolio tail risk is computed on **daily** NaN-safe portfolio simple returns in investor currency,
sliced to each analysis window (3Y / 5Y / 10Y calendar months ending at `analysis_end`).
Outputs include `analytics.tail_risk` with `method`, `frequency`, `window_months`, `window_label`,
`n_obs`, and 95%/99% levels. Minimum 60 daily observations. Main-metrics cadence (monthly) is not
used for VaR/ES in the standard report pipeline.

- Confidence levels:

95% and 99%.

- ES contribution:

Decompose portfolio ES by assets to identify tail-risk contributors and enforce limits.

- Use rule:

If ES deteriorates, validate against historical stress periods (2008 / 2020 / 2022) before changing weights.

### EXPECTED RETURN

Historical baseline approach.

- Use 5Y and 10Y data.

- Compute monthly simple returns for assets and portfolio returns.

- Compute portfolio CAGR for the window (geometric return).

This serves as the historical baseline expected return.

### CORRELATION

- Compute correlation of asset/portfolio with investor base benchmark using monthly simple returns.

- Compute rolling correlation using windows:

36 months primary

12 months radar

For rolling correlation evaluate:

current value

mean

10-90% range.

Number of rolling points:

5Y window:

12M window -> 48 points

36M window -> 24 points

10Y window:

12M window -> 108 points

36M window -> 84 points.

### CORRELATION MATRIX OUTPUT

- Output full **correlation matrix** of portfolio assets for each window (3Y / 5Y / 10Y).

- Correlation matrix must be computed on **the same aligned dates (inner join)** used for all correlation and covariance calculations.

- Use **monthly simple returns** with **ddof=1** for consistency with all other estimators.

- Export as CSV: **correlation_matrix_3y.csv**, **correlation_matrix_5y.csv**, **correlation_matrix_10y.csv**.

- Round to 3 decimal places at export stage only (same as other metrics).
