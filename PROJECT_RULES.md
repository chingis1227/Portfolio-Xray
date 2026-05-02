# Project Rules вЂ” Portfolio Metrics Standard

Always follow metrics_specification.md for all metric definitions, estimators, frequency, FX, and windowing. Do not invent formulas. For stress testing (scenarios, Loss and RC concentration tests, factor and historical validation), use **docs/docs/stress_testing_spec.md** as the source of truth.

**Stress factor betas** (outputs in `stress_report.json`): estimated on **weekly** aligned data (Friday week-ends). Regression windows ending at **`analysis_end`** are **`FACTOR_WEEKS_5Y = 260`** and **`FACTOR_WEEKS_10Y = 520`** in **`src/stress_factors.py`** (`compute_asset_factor_betas_weekly`). **`factor_betas`** duplicates **`factor_betas_5y`** for backward compatibility. Do not use a 156-week or monthly window for this pipeline unless the spec is explicitly changed.
Production factor order is `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, `us_growth`; `commodity` is the production сырьевой factor. Extended diagnostic/stress factor order is production factors plus `oil`. `beta_oil` is deprecated and removed from new production beta, rolling stability, OOS, adjusted overlay, and base variance-decomposition outputs; Oil exposure must be read from `diagnostic_oil_beta` or stress-layer metrics. `vix` and `oil` are week-end percent changes; `us_growth` is the first difference of FRED `WEI` after shifting its week-ending-Saturday timestamps back to Friday. Only the first six factors map into synthetic stress shock keys in `src/stress.py`; `vix`, `us_growth`, and `oil` are analytics-only in the current production contract. The `inflation_stagflation` synthetic scenario includes `shock_inf = +0.005` (+50 bps T10YIE breakeven inflation), so `beta_inf` contributes directly to that scenario PnL.

**Portfolio factor regression diagnostics** (`factor_regression_5y` / `factor_regression_10y` in `stress_report.json`) must report `idiosyncratic_risk = 1 - r2` and use base-factor weekly OLS rows for multicollinearity, serial correlation, Breusch-Pagan heteroskedasticity, and HAC/Newey-West inference; these diagnostics are non-binding. `factor_betas_stability` adds rolling beta sign, magnitude, specification, and OOS stability diagnostics across weekly/monthly 3Y/5Y/10Y windows; it is also non-binding.

**Kalman factor betas** (`stress_report.json.factor_betas_kalman`) are diagnostic-only current-regime estimates on the extended weekly factor registry. Reported Kalman betas are capped at `|beta| <= 3.0`, preserve uncapped latest values in `latest_raw`, flag Kalman-vs-5Y divergence by sign difference / `abs_gap >= 0.25` / `relative_gap >= 0.75`, and classify posterior state uncertainty as low/moderate/high at `0.15` and `0.35`. They must not replace raw OLS 5Y/10Y betas, optimizer inputs, mandate gates, or stress pass/fail logic. Oil Kalman exposure is surfaced through `diagnostic_oil_beta`.

**Factor covariance forecast quality** (`stress_report.json.factor_covariance.forecast_quality`) is diagnostic-only and non-binding. It compares a 260-week weekly factor covariance forecast with realized factor portfolio risk over the next 52 weekly rows, using 52-week non-overlapping steps and sample `ddof=1` covariance/volatility.

**Macro regime diagnostics** (`stress_report.json.macro_regime_diagnostics`) are diagnostic-only and non-binding. Method version `internal_market_proxy_v1` labels weekly rows into `goldilocks`, `reflation`, `stagflation`, and `recession_disinflation` using internal market proxies: rolling z-score of `us_growth` for `growth_score` and average rolling z-score of available `inflation` and `commodity` for `inflation_pressure_score`. This is not a full macroeconomic regime model, does not use PMI/NFP/CPI/PCE/copper/credit impulse inputs, and must not replace optimizer inputs, mandate gates, stress pass/fail logic, or raw 5Y/10Y beta outputs.

**Portfolio PCA diagnostics** (`stress_report.json.portfolio_pca`) are diagnostic-only and non-binding. They use weekly adjusted-close returns for current positive-weight portfolio assets, with a 260-week default window ending at `analysis_end`. Interpret covariance PCA as `risk_dominance` because volatility scale is included; interpret correlation PCA as `structure` because asset volatility is standardized. Raw PCA and factor-residual PCA must be interpreted separately.

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

There are two types of beta вЂ” do not confuse them.

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
- **Not a portfolio metric** вЂ” diagnostic only.
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
| US Treasuries 7вЂ“10Y | IEF |
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
- **Sharpe**: Sharpe = (mean(r_simple в€’ rf_monthly) Г— 12) / (std(r_simple, ddof=1) Г— sqrt(12)). Volatility in the denominator is from raw returns (r_simple), not from excess returns.
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
  - **ПѓВІ_t = w_tбµЂ ОЈ_window w_t** (portfolio variance at t).
  - **PC_{i,t} = (w_{i,t} Г— (ОЈ_window w_t)_i) / ПѓВІ_t**.
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

вЂў 10Y: primary long-horizon estimate and full cycle. Use as anchor for long-term conclusions (average return, base volatility, base correlations, base beta_base).

вЂў 5Y: test whether the structure is still valid in the current regime. If 5Y diverges strongly from 10Y, the regime likely changed and 10Y cannot be used without adjustments.

вЂў 3Y: operational regime-shift radar (especially real rates / inflation / liquidity). Used for triggers and risk-control, not for strategic long-term allocation conclusions.

### RETURN AND BASE RISK

вЂ“ Return: compute CAGR (geometric) for the window on log-returns and annualize; additionally compute annualized return on simple returns (for PnL intuition)

вЂ“ Volatility: monthly and annualized on simple returns

вЂ“ Correlation / Covariance / RC_vol: compute on the same simple returns (single base for risk analytics and risk contributions)

вЂ“ Max Drawdown + Time to Recovery: computed on simple returns using the equity curve (peak-to-trough; recovery = period until equity в‰Ґ peak)

вЂ“ Sharpe / Sortino / Downside deviation (annualized): computed on simple returns; excess-return and MAR are relative to the investor cash rate (default USD 3M T-bill converted to the data periodicity)

вЂ“ Beta_portfolio (relative to a single benchmark): computed on the same simple returns relative to one investor base benchmark (e.g., S&P 500)

вЂ“ Treynor (if used): annualized portfolio excess return relative to investor cash rate divided by Beta_portfolio (same benchmark and same window/dates)

### ROLLING SHARPE / ROLLING SORTINO

вЂў Rolling Sharpe/Sortino: computed on simple returns with investor cash rate subtracted (risk-free / MAR)

вЂў Windows:

36 months primary

12 months fast indicator

Usage rule:
Take action only when deterioration is visible in the 36-month window.
If deterioration appears only in the 12-month window, treat it as temporary noise.

### DRAWDOWN STRUCTURE

вЂў For every drawdown compute depth and length.

вЂў Compute recovery time statistics: median + p90 (not only average).

вЂў Compute time underwater:

percentage of time below peak

longest underwater period.

вЂў Compute statistics separately for drawdowns greater than:

5%

10%

20%

Purpose:
MaxDD shows the depth of losses, while drawdown structure shows how long the portfolio may take to recover.

### RISK DYNAMICS

вЂў Compute rolling volatility on monthly simple returns using a 12-month window, annualized.

вЂў Compute vol-of-vol = std(rolling volatility) over the analysis period.

вЂў Compute relative vol-of-vol = std(rolling volatility) / mean(rolling volatility) to compare assets.

вЂў Optional fast radar: 6-month rolling volatility, but decisions should rely on the 12-month measure.

### RISK CONTRIBUTION OF ASSETS

Compute MRC (marginal risk contribution) and CTR / RC_vol (component risk contribution) for each asset using the covariance matrix of simple returns.


### RETURN ATTRIBUTION

вЂў Compute Return Contribution of each asset to portfolio return (using simple returns in investor currency).

вЂў Compare Return Contribution with RC_vol (CTR).

вЂў Identify assets with consistently high return per unit of risk contribution (check on 10Y and rolling 36M windows).

Purpose:
Connect risk contribution and return contribution.

### BETA ANALYSIS

вЂў Compute beta on simple returns for both the portfolio and individual assets.

вЂў Compute each asset's contribution to portfolio beta:

wi Г— Cov(Ri , Rm) / Var(Rm)

The sum of contributions equals portfolio beta.

вЂў Compute rolling beta using windows:

36 months primary

12 months radar

For rolling beta evaluate:

current value

mean

10вЂ“90% range

min/max optional.

вЂў Downside beta:
compute using only months where market return < 0.

вЂў Upside beta:
compute using only months where market return > 0.

Base: monthly simple returns for both market and portfolio/assets with identical dates.

### EFFECTIVE EQUITY EXPOSURE

Select months where benchmark return is in the worst 10% / 20% / 30%.

Compute crisis beta on those months:

ОІ_crisis using monthly simple returns.

Define:

EEE = ОІ_crisis Г— 100%

EEE measures how much the portfolio behaves like equities during stress periods.

### DISTRIBUTION SHAPE

вЂў Compute skewness and kurtosis of portfolio returns using monthly log-returns over windows:

5Y

10Y

optional 3Y radar.

Diagnostic only.
Used as tail-risk flags, not as optimization targets.

Negative skew and high kurtosis indicate higher probability of sharp drawdowns.

### MONTE CARLO + IRR ANALYSIS

Purpose: evaluate distribution of future outcomes rather than predict markets.

Method:

Run 100,000 simulations using **contiguous-segment bootstrap**.

Randomly construct future paths by stitching those historical segments (3вЂ“12 months) to preserve tails and regime persistence.

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

вЂў Horizons:

Compute

1M ES (primary tail risk measure relevant for MaxDD)

1D ES (operational indicator only)

вЂў Method:

Use Historical VaR and Expected Shortfall from realized returns.

No Monte Carlo and no normality assumptions.

вЂў Returns base:

Daily simple returns.

вЂў Confidence levels:

95% and 99%.

вЂў ES contribution:

Decompose portfolio ES by assets to identify tail-risk contributors and enforce limits.

вЂў Use rule:

If ES deteriorates, validate against historical stress periods (2008 / 2020 / 2022) before changing risk limits, mandate, or target weights.

### EXPECTED RETURN

Historical baseline approach.

вЂў Use 5Y and 10Y data.

вЂў Compute monthly simple returns for assets and portfolio returns.

вЂў Compute portfolio CAGR for the window (geometric return).

This serves as the historical baseline expected return.

### CORRELATION

вЂў Compute correlation of asset/portfolio with investor base benchmark using monthly simple returns.

вЂў Compute rolling correlation using windows:

36 months primary

12 months radar

For rolling correlation evaluate:

current value

mean

10вЂ“90% range.

Number of rolling points:

5Y window:

12M window в†’ 48 points

36M window в†’ 24 points

10Y window:

12M window в†’ 108 points

36M window в†’ 84 points.

### CORRELATION MATRIX OUTPUT

вЂў Output full **correlation matrix** of portfolio assets for each window (3Y / 5Y / 10Y).

вЂў Correlation matrix must be computed on **the same aligned dates (inner join)** used for all correlation and covariance calculations.

вЂў Use **monthly simple returns** with **ddof=1** for consistency with all other estimators.

вЂў Export as CSV: **correlation_matrix_3y.csv**, **correlation_matrix_5y.csv**, **correlation_matrix_10y.csv**.

вЂў Round to 3 decimal places at export stage only (same as other metrics).
