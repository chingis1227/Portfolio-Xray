# Data Policy, NaN and “Young” ETFs: Single Logic (No Rewriting of History)

This document defines the data policy, handling of missing data (NaN), treatment of newly listed (“young”) ETFs, the dynamic NaN-safe backtest, and the baseline-vs-full comparison. It complements the general NaN-safe portfolio rule in **.cursor/rules/portfolio-metrics.mdc** by specifying within-block redistribution, RC-gated fallback, and reporting requirements.

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

### NaN Policy: Equal Redistribute Within-Block + RC-Gated (Fallback to Cash)

If an asset in block *X* has no return (NaN) in period *t*, it is temporarily excluded. Its target weight is **redistributed only within the same block *X*** in equal shares among the **available** assets of that block.

Then the following safeguards are mandatory:

1. Recompute **RC_vol** (and, if applicable, block weights relative to the RB corridor).
2. If after redistribution:
   - **RC_asset_cap** is violated, or  
   - the block moves outside the **RB corridor** (when a corridor is defined),  
   then the shortfall weight **w_miss** goes to the **cash proxy** (fallback), and must not increase risk.
3. Always respect:
   - **min_weight**
   - **weight caps**

### Formal Rule for Period *t*

- Let the missing weight in block *X* be **w_miss**.
- Let there be **K** available assets in block *X*.
- Then each available asset in the block receives an increment: **Δ = w_miss / K**.
- Weights within the block are updated: **w_i' = w_i + Δ** (only for assets in block *X* with data).

Then check:

- If **RC_asset_cap** and the **RB corridor** are satisfied → use **w_i'**.
- If not → transfer part of the weight to the cash proxy until constraints are satisfied.

**Meaning:** missing weight is not spread across the whole portfolio; the role of the block is preserved, but redistribution must not break RC or the RB architecture.

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
- **NaN policy:** within_block_equal_rc_gated + fallback rules to cash proxy.
- **Baseline vs full** metrics and the **comparison period** (after inception).
