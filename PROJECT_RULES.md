# Project Rules — Portfolio Metrics Standard

Always follow metrics_specification.md for all metric definitions, estimators, frequency, FX, and windowing. Do not invent formulas. For stress testing (scenarios, Loss/Role/RC tests, factor and historical validation), use **docs/docs/stress_testing_spec.md** as the source of truth.

**Portfolio weights** are the output of optimization (constraints + client metrics), not user input. Do not require or encourage manual weight entry in config; weights are exported after optimization and can be saved to config.

## Frequency standard

- **All prices must be downloaded as Adj Close** (adjusted close). Download daily Adj Close via yfinance.
- Convert prices to investor_currency BEFORE returns using spot FX tickers like EURUSD=X meaning "1 EUR in USD".
- FX daily may be forward-filled to align calendars; asset returns must never be interpolated.
- Resample to effective month-end: last available trading day of each month.

## Date/window standard

- **analysis_end** = last completed effective month-end (previous month-end) = last effective month-end strictly before today.
- Windows are fixed-length ending at analysis_end: 36M, 60M, 120M.

## Returns

- Monthly simple return: **r_t = P_t / P_{t-1} - 1**
- Monthly log return: **lr_t = ln(P_t / P_{t-1})**

## FX conversion rules (must be implemented explicitly)

- If asset_ccy=EUR and investor_ccy=USD: **P_USD = P_EUR * FX(EURUSD=X)**.
- If asset_ccy=USD and investor_ccy=EUR: **P_EUR = P_USD / FX(EURUSD=X)**.
- If investor_ccy != USD: convert via USD:
  - **P_USD = P_asset * FX(asset_ccyUSD=X)** (e.g., JPYUSD=X).
  - **P_investor = P_USD / FX(investor_ccyUSD=X)** (e.g., EURUSD=X).
- If FX ticker not available in required orientation, use inverse pair and invert: **FX = 1 / FX_inverse**.

## Estimators

- Use sample estimators everywhere: **ddof=1** explicitly for std/var/cov.
- For Beta_base and Beta_local always use sample estimators: **var(..., ddof=1)** and **cov(..., ddof=1)**. Do not rely on library defaults.

## Alignment

- For any excess-return metric, align dates via **inner join** across r_t, rf_t, and required benchmark series before computing.
- For cov/corr/beta/RC_vol use inner join (synchronous observations only).

## Risk-free

- Default FRED:DTB3 (annual percent). Convert to monthly effective: **(1 + y/100) ** (1/12) - 1**.
- Resample to month-end via last available value.
- If investor currency != USD and rf source is not explicitly provided, **fail fast** (no guessing).

## Benchmarks and Beta (two types)

There are two types of beta — do not confuse them.

### Beta_base (portfolio management)

- Single base benchmark in investor currency for **unified market risk scale**:
  - **USD**: S&P 500 (proxy: SPY or VOO)
  - **EUR**: STOXX Europe 600 (proxy: VGK or EXSA.DE)
  - **JPY**: Nikkei 225 (proxy: EWJ)
  - **CHF**: Swiss Market Index SMI (proxy: EWL)
- Computed on **monthly simple returns**, same dates, same window, same method for all assets.
- Used for comparing assets and controlling total market exposure of portfolio.

### Beta_local (diagnostic, per-asset only)

- Computed for each asset individually to understand which "local market" the asset resembles.
- **Not a portfolio metric** — diagnostic only.
- Same calculation rules as Beta_base: monthly simple returns, one window, aligned dates, ddof=1.

#### Local benchmark dictionary (proxies)

**Equity by region:**
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

**Bonds:**
| Asset class | Proxy ETF |
|-------------|-----------|
| US Aggregate IG | BND (or AGG) |
| US Treasuries 7–10Y | IEF |
| US Long Treasuries | TLT |
| US TIPS | TIP |
| US High Yield | HYG (or JNK) |
| US IG Corporates | LQD |
| Short T-Bills / Cash proxy | BIL |

**Commodities / real assets:**
| Asset class | Proxy ETF |
|-------------|-----------|
| Broad commodities | PDBC (or DBC) |
| Industrial metals | DBB |
| Energy | XLE |

#### Hard special rules

- **Crypto**: Beta_local = Beta_base, local benchmark = S&P 500 (proxy VOO).
- **Gold**: Beta_local = Beta_base, local benchmark = S&P 500 (proxy VOO).

## Metrics per asset per window

- **CAGR**: computed from equity curve using monthly simple returns:
  - Equity = cumprod(1 + r_simple)
  - CAGR = (Equity_end / Equity_start) ** (12 / N_months) - 1
- **Vol**: std(r_simple, ddof=1) monthly; annual = monthly * sqrt(12).
- **Sharpe**: Sharpe = (mean(r_simple − rf_monthly) × 12) / (std(r_simple, ddof=1) × sqrt(12)). Volatility in the denominator is from raw returns (r_simple), not from excess returns.
- **Sortino**: computed relative to MAR (Minimum Acceptable Return). By default MAR_monthly = rf_monthly; can be overridden by a custom MAR parameter. Downside = min(0, r_simple - MAR):
  - dd_monthly = sqrt(mean(downside^2))
  - dd_annual = dd_monthly * sqrt(12)
  - Sortino = (mean(excess) * 12) / dd_annual
- **Beta_base**: cov(r_asset, r_benchmark) / var(r_benchmark) with var(..., ddof=1) and cov(..., ddof=1) explicitly; same dates. See "Benchmarks and Beta" section for benchmark selection by investor currency.
- **Beta_local**: same formula vs local proxy from dictionary above; same estimator rule (ddof=1 explicit). For Gold and Crypto: beta_local == beta_base.
- **Treynor** (diagnostic): (mean(excess) * 12) / beta_base, where beta_base is computed on the same window/dates.
- **Skew/Kurt**: compute on monthly log returns (diagnostic).
- **Max Drawdown**: from monthly equity curve; dd = equity / cummax(equity) - 1.
- **Time to recovery**: months from peak to first month equity >= prior peak; if not recovered: ttr=NaN, recovered=False.

## Portfolio NaN-safe dynamic

- At each month t:
  - w_avail = w_target for assets with non-NaN return at t; do not renormalize.
  - w_miss = 1 - sum(w_avail).
  - **R_p,t = sum(w_avail_i * R_i,t) + w_miss * R_cash,t**.
- Default cash proxy BIL for USD; if investor currency != USD, require explicit cash proxy.

## RC_vol (percentage risk contribution)

- **RC_vol** is defined as **percentage contribution to portfolio variance** (not to volatility; not via correlations).
- For each month t in the window:
  - **σ²_t = w_tᵀ Σ_window w_t** (portfolio variance at t).
  - **PC_{i,t} = (w_{i,t} × (Σ_window w_t)_i) / σ²_t**.
  - **RC_window_i = mean_t(PC_{i,t})** over the window.
- **PC must sum to 1** across assets at each t.
- Do not compute contribution to volatility or via correlations.

## Output formatting (rounding)

- **All reported numeric metrics must be rounded to 3 decimal places** at the final output stage only (before exporting CSV or printing).
- Rounding applies **only at export/report stage**; do not round during intermediate calculations (Sharpe, beta, RC_vol, CAGR, etc. use full precision).
- Use standard half-up rounding via pandas **.round(3)** for DataFrames and Series at export.
- Do not round raw returns, covariance matrices, or any intermediate values used in further calculations. Persist full precision internally; round only exported/report-facing results.

---

## PORTFOLIO ANALYTICS STANDARD

### FOR PORTFOLIO WITH GIVEN WEIGHTS (windows 3Y / 5Y / 10Y monthly)

• 10Y: base "structural" estimate and full cycle. Use as anchor for long-term conclusions (average return, base volatility, base correlations, base beta_base).

• 5Y: test whether the structure is still valid in the current regime. If 5Y diverges strongly from 10Y, the regime likely changed and 10Y cannot be used without adjustments.

• 3Y: operational regime-shift radar (especially real rates / inflation / liquidity). Used for triggers and risk-control, not for strategic long-term allocation conclusions.

### RETURN AND BASE RISK

– Return: compute CAGR (geometric) for the window on log-returns and annualize; additionally compute annualized return on simple returns (for PnL intuition)

– Volatility: monthly and annualized on simple returns

– Correlation / Covariance / RC_vol: compute on the same simple returns (single base for risk budget and risk contributions)

– Max Drawdown + Time to Recovery: computed on simple returns using the equity curve (peak-to-trough; recovery = period until equity ≥ peak)

– Sharpe / Sortino / Downside deviation (annualized): computed on simple returns; excess-return and MAR are relative to the investor cash rate (default USD 3M T-bill converted to the data periodicity)

– Beta_portfolio (relative to a single benchmark): computed on the same simple returns relative to one investor base benchmark (e.g., S&P 500)

– Treynor (if used): annualized portfolio excess return relative to investor cash rate divided by Beta_portfolio (same benchmark and same window/dates)

### ROLLING SHARPE / ROLLING SORTINO

• Rolling Sharpe/Sortino: computed on simple returns with investor cash rate subtracted (risk-free / MAR)

• Windows:

36 months primary

12 months fast indicator

Usage rule:
Take action only when deterioration is visible in the 36-month window.
If deterioration appears only in the 12-month window, treat it as temporary noise.

### DRAWDOWN STRUCTURE

• For every drawdown compute depth and length.

• Compute recovery time statistics: median + p90 (not only average).

• Compute time underwater:

percentage of time below peak

longest underwater period.

• Compute statistics separately for drawdowns greater than:

5%

10%

20%

Purpose:
MaxDD shows the depth of losses, while drawdown structure shows how long the portfolio may take to recover.

### RISK DYNAMICS

• Compute rolling volatility on monthly simple returns using a 12-month window, annualized.

• Compute vol-of-vol = std(rolling volatility) over the analysis period.

• Compute relative vol-of-vol = std(rolling volatility) / mean(rolling volatility) to compare assets.

• Optional fast radar: 6-month rolling volatility, but decisions should rely on the 12-month measure.

### RISK CONTRIBUTION OF ASSETS

Compute MRC (marginal risk contribution) and CTR / RC_vol (component risk contribution) for each asset using the covariance matrix of simple returns.

Additionally aggregate RC across structural blocks (Growth / Duration / Inflation) to monitor risk budgets.

### RETURN ATTRIBUTION

• Compute Return Contribution of each asset to portfolio return (using simple returns in investor currency).

• Compare Return Contribution with RC_vol (CTR).

• Identify assets with consistently high return per unit of risk contribution (check on 10Y and rolling 36M windows).

Purpose:
Connect risk contribution and return contribution.

### BETA ANALYSIS

• Compute beta on simple returns for both the portfolio and individual assets.

• Compute each asset's contribution to portfolio beta:

wi × Cov(Ri , Rm) / Var(Rm)

The sum of contributions equals portfolio beta.

• Compute rolling beta using windows:

36 months primary

12 months radar

For rolling beta evaluate:

current value

mean

10–90% range

min/max optional.

• Downside beta:
compute using only months where market return < 0.

• Upside beta:
compute using only months where market return > 0.

Base: monthly simple returns for both market and portfolio/assets with identical dates.

### EFFECTIVE EQUITY EXPOSURE

Select months where benchmark return is in the worst 10% / 20% / 30%.

Compute crisis beta on those months:

β_crisis using monthly simple returns.

Define:

EEE = β_crisis × 100%

EEE measures how much the portfolio behaves like equities during stress periods.

### DISTRIBUTION SHAPE

• Compute skewness and kurtosis of portfolio returns using monthly log-returns over windows:

5Y

10Y

optional 3Y radar.

Diagnostic only.
Used as tail-risk flags, not as optimization targets.

Negative skew and high kurtosis indicate higher probability of sharp drawdowns.

### MONTE CARLO + IRR ANALYSIS

Purpose: evaluate distribution of future outcomes rather than predict markets.

Method:

Run 100,000 simulations using block bootstrap.

Randomly construct future paths by stitching real historical return blocks (3–12 months) to preserve tails and regime persistence.

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

• Horizons:

Compute

1M ES (primary tail risk measure relevant for MaxDD)

1D ES (operational indicator only)

• Method:

Use Historical VaR and Expected Shortfall from realized returns.

No Monte Carlo and no normality assumptions.

• Returns base:

Daily simple returns.

• Confidence levels:

95% and 99%.

• ES contribution:

Decompose portfolio ES by assets to identify tail-risk contributors and enforce limits.

• Use rule:

If ES deteriorates, validate against historical stress periods (2008 / 2020 / 2022) before changing risk budgets or weights.

### EXPECTED RETURN

Historical baseline approach.

• Use 5Y and 10Y data.

• Compute monthly simple returns for assets and portfolio returns.

• Compute portfolio CAGR for the window (geometric return).

This serves as the historical baseline expected return.

### CORRELATION

• Compute correlation of asset/portfolio with investor base benchmark using monthly simple returns.

• Compute rolling correlation using windows:

36 months primary

12 months radar

For rolling correlation evaluate:

current value

mean

10–90% range.

Number of rolling points:

5Y window:

12M window → 48 points

36M window → 24 points

10Y window:

12M window → 108 points

36M window → 84 points.

### CORRELATION MATRIX OUTPUT

• Output full **correlation matrix** of portfolio assets for each window (3Y / 5Y / 10Y).

• Correlation matrix must be computed on **the same aligned dates (inner join)** used for all correlation and covariance calculations.

• Use **monthly simple returns** with **ddof=1** for consistency with all other estimators.

• Export as CSV: **correlation_matrix_3y.csv**, **correlation_matrix_5y.csv**, **correlation_matrix_10y.csv**.

• Round to 3 decimal places at export stage only (same as other metrics).
