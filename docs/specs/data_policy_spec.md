# Data Policy, NaN and “Young” ETFs: Single Logic (No Rewriting of History)

This document defines the data policy, handling of missing data (NaN), treatment of newly listed (“young”) ETFs, the dynamic NaN-safe backtest, and the baseline-vs-full comparison. It complements the general NaN-safe portfolio rule in **.cursor/rules/portfolio-metrics.mdc** by specifying **global** redistribution among risk tickers, the **`w_miss` → cash proxy** rule for any weight not on assets with an observed return that month, and reporting requirements.

---

## 1. Main Principle

**Returns are not fabricated.** Any missing value (NaN) means “no data”, not “0%” and not a reason to rewrite history.

---

## 2. Series Alignment (Join Policy)

- **For cov / corr / beta / RC_vol:** use the **intersection of dates** (inner join) across the assets that participate in the calculation.  
  Statistics are computed only where data actually exist for all series involved.

- **For a single-asset chart:** outer join is allowed, because alignment with other assets is not required.

---

## 3. “Young” ETFs: History Is Not Cut to the Youngest

- The code **must not** truncate the entire backtest to the inception date of the youngest ETF.

- **Before** the inception of a new ETF, the portfolio is computed only over assets that actually existed.

- The new ETF is included **from the first full monthly point** (first complete monthly return), so that partial months are not used.

---

## 4. Dynamic (NaN-Safe) Backtest: Main Mode (No Rewriting of History)

The portfolio is computed **period by period**. In each period *t*, only assets with an observed return participate.

### NaN Policy: Equal Redistribute Among Risk Tickers + `w_miss` to Cash

Risk tickers are all portfolio names **except** the cash proxy (e.g. BIL). If a risk asset has no return (NaN) in period *t*, it is temporarily excluded. Its target weight is **redistributed in equal shares** among the **other risk tickers** that have a valid return in *t*.

Portfolio return for the month uses weights actually applied: **sum of (weight × return)** for assets with data, plus **`w_miss` × cash proxy return**, where `w_miss` is the share of portfolio weight not on assets with an observed return that month (including any residual after redistribution). **RC_vol is not used** to gate or revert this path.

**Meaning:** NaN months do not rewrite history; redistribution spreads missing risk-sleeve weight across peers with data; any remainder is treated as **cash** for that month.

---

## 5. Adding a New ETF = Strategy Update (Not “Improving History”)

- **Before** the ETF’s inception date, it is not in the portfolio. This reflects the investable universe; it is not “under-investment”.

- **From** the ETF’s inception date:
  - it is added;
  - target weights are recalculated according to the predefined rule (typically via optimization with fixed inputs);
  - the report must record the **inception date**, the **date of inclusion**, and that this is a **new strategy version**.

- **Past history is not rewritten** and must not be “extended” backward with the new asset.

---

## 6. Baseline vs Full: Honest Check of New Assets’ Contribution

To avoid decisions driven by a “nice” but regime-dependent segment:

- **Baseline portfolio:** computed only over assets with **sufficient history in the window** (e.g. **coverage ≥ 90%**). This gives an honest view of structural risk and stability.

- **Full portfolio:** computed over **all assets**, using the main Dynamic NaN-safe mode from §4.

- **Comparison** must be done correctly:
  - the main **“baseline vs full”** comparison is made **after** the new ETF’s inception, where both strategies are actually implementable;
  - “before / after” is presented as a **strategy version change**, not as proof of superiority over the full history.

*(This “baseline (high-coverage) vs full (all assets)” is distinct from the diagnostic baseline portfolios in §6 of portfolio_construction_policy.md.)*

---

## 7. What Must Be Documented in the Report

- **Join policy:** inner for cov/RC; outer for single-asset charts.
- **Inception dates** and **effective inclusion dates** (first full monthly point).
- **NaN policy:** global_equal_among_risk + `w_miss` to cash proxy.
- **Baseline vs full** metrics and the **comparison period** (after inception).

---

## 8. Dual covariance for young ETFs (implementation)

For **mean–variance / RC_vol inputs used by the policy optimizer** (primary and secondary windows), the pipeline may use a **dual covariance** so the estimation window is not collapsed to the shortest-listed history:

- **Eligible** assets (default: ≥ 48 months of observations in the optimization window) form the **core** matrix via the usual synchronous sample on that core set only.
- **Candidate** (default: 12–47 months) and **new** (< 12 months) assets get pairwise covariances from their available overlap with each peer, **shrunk** toward the **median covariance of the eligible core slice** (single pooled “Risk” anchor for pairwise anchors). Shrinkage weight for “new” uses `new_shrinkage_alpha` (default 0.1); between candidate bounds it ramps linearly to 1.0 at eligibility.
- **Weight cap:** candidate and new tickers are capped by `max_weight_candidate_or_new_pct` (default 2% each).
- **Warning (not a hard fail):** if the **sum of optimized RiskPortfolio weights** of all candidate + new tickers exceeds `aggregate_candidate_new_warn_pct` (default 10%), `run_result.json` records `WARN_MODEL_RISK_YOUNG_WEIGHT`.
- **Fallback:** if fewer than two eligible assets exist, optimization reverts to the legacy **full inner join** covariance on all risk tickers in the window.

Configuration: `young_etf_optimization_policy` in `config.yml` (defaults injected by `config_schema`). Set `enabled: false` to restore the legacy inner-join-only optimizer covariance.

**Note:** §2 above still applies to **generic** cov/corr/RC on a fixed panel (reports, correlation CSVs): those continue to use **inner join** unless a separate spec says otherwise. The dual matrix is specific to **optimization inputs** in `run_optimization.py`.
