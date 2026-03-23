# Optimization Spec: Inflation (Block Selection via Candidate Scoring)

This document defines **Inflation block** selection only. No mean-variance optimization is run inside this block. Objective is hedge effectiveness across rate/inflation and monetary stress, plus tail control. Other specs: **docs/docs/optimization_growth_spec.md**, **docs/docs/optimization_duration_spec.md**, **docs/docs/optimization_proliquidity_spec.md**, **docs/docs/feasibility_constraints_spec.md**.

**Policy link.** This selection operationalizes **docs/portfolio_construction_policy.md** §5.3: Inflation block as protection for purchasing power and monetary anchor (CPI, monetary hedge, resource shock); Type1/Type2 stress windows implement rate shock vs monetary stress.

---

## 0. Shared: Growth Proxy (fixed)

- **growth_proxy** = `"VOO"` always. Do NOT infer from portfolio contents.
- If VOO is unavailable in the dataset → return **FAIL_DATA** with reason `"VOO data missing"`.

---

## 1. Inputs (fixed for this routine)

- **RB_block** — risk budget share for Inflation (from rc_block_targets).
- **RC_cap**, **weight caps**, **min weight** — from feasibility; see **docs/docs/feasibility_constraints_spec.md**.
- **Universe of the block** — from user-provided mechanism tickers or block list (see Config below).
- **Baseline** — for ES95 comparison (see §1.1).
- **Duration proxy** — for Type1 stress window (see B2); prefer duration_int_ticker, else duration_long_ticker from config.

### 1.1 Baseline (for ES95 filter)

- **Baseline** = current internal weights of the Inflation block from the **last policy snapshot** (previous rebalance date).
- If first run (no policy snapshot / baseline absent) → **baseline** = equal-weight over available tickers in the block.

---

## 2. Config: Inflation Mechanism Tickers

Mechanism tickers are **user-provided at portfolio build time** (preferred). Do NOT auto-detect mechanisms from names.

Config keys (add to config under a dedicated section, e.g. `inflation_mechanisms` or equivalent):

| Key | Description | Required |
|-----|-------------|----------|
| **tips_ticker** | CPI protection (e.g. TIP) | Can be null |
| **gold_ticker** | Monetary hedge (e.g. GLD) | Can be null |
| **comm_ticker** | Resource shock / commodities (e.g. PDBC) | Can be null |

- Build Inflation universe from **non-null** tickers.
- If user does **not** provide mechanism mapping, use the Inflation block universe as-is (from blocks.Inflation) and apply k==1 / k==2 logic below.

---

## 3. B) Inflation Block Selection

### B0) User-provided mechanism tickers

- If provided: use tips_ticker, gold_ticker, comm_ticker (non-null) to build universe and assign roles.
- If not provided: use Inflation universe from blocks; no role labels (use B1.1 / B1.2 only).

### B1) Candidate construction by number of tickers

**Case B1.1:** Inflation has 1 ticker  
- candidates = `[{ name: "I0", weights: { ticker: 1.0 } }]`  
- selection_method = `"SKIP_INTERNAL_SELECTION"`

**Case B1.2:** Inflation has 2 tickers  
- Let A, B be the two tickers in deterministic order (as given, else lexicographic).  
- candidates:
  - I1: A 70% / B 30%
  - I2: A 50% / B 50%
  - I3: A 30% / B 70%

**Case B1.3:** Full 3-mechanism (TIPS + GOLD + COMM all provided)  
- Enforce floors within Inflation block:
  - TIPS ≥ 0.30
  - GOLD ≥ 0.25
  - COMM ≥ 0.15
- Build fixed candidates (all respecting floors), e.g.:
  - I1: TIPS 0.30 / GOLD 0.25 / COMM 0.45
  - I2: TIPS 0.40 / GOLD 0.25 / COMM 0.35
  - I3: TIPS 0.50 / GOLD 0.25 / COMM 0.25
  - I4: TIPS 0.35 / GOLD 0.35 / COMM 0.30
  - I5: TIPS 0.45 / GOLD 0.35 / COMM 0.20

### B2) Define stress-month windows (market proxies; no CPI required)

- **Duration proxy for Type1:** Prefer duration_int_ticker; else duration_long_ticker. If neither provided → return **FAIL_DATA** `"Duration proxy missing for Type1 stress window"`.

- **Type1 months** (Rate/Inflation Shock proxy):  
  return(VOO) < 0 **AND** return(duration_proxy) < 0

- **Type2 months** (Monetary Stress proxy):  
  Requires gold_ticker. If gold_ticker not provided and Inflation has 1–2 tickers: user must map the gold-like ticker as gold_ticker, else set Type2 unavailable and use fallback.  
  return(VOO) < 0 **AND** return(gold_ticker) > 0

- **Fallback:** If Type1 or Type2 month count < 12, use **growth_worst12** = 12 months with lowest return(VOO).

### B3) Score Inflation candidates

For each candidate c:

- r_c = weighted monthly return series.
- avg_ret_type1 = mean(r_c[Type1]) if enough Type1 else mean(r_c[growth_worst12])
- avg_ret_type2 = mean(r_c[Type2]) if enough Type2 else mean(r_c[growth_worst12])
- worst_month_all = min(r_c) over all months
- **score_inflation** = 0.6 × avg_ret_type1 + 0.4 × avg_ret_type2 − 0.2 × |worst_month_all|

Set **low_sample** flags for Type1/Type2 when fallback was used.

### B4) Tail Filter (ES95)

- ES95_c = mean of bottom 5% monthly returns of r_c.
- **Baseline** per §1.1. If baseline exists: reject if ES95_c worse than baseline_ES95 by > 0.003.
- Else use ES95 as tie-breaker (higher ES95 = better).

### B5) Select + Apply Caps

- **Feasibility context:** Check feasibility in the context of the **full RiskPortfolio** (Growth + Duration + Inflation). Other blocks use their **current or target** weights; the candidate provides Inflation internal weights. Global RC_cap and weight caps/mins must be satisfied. See **docs/docs/feasibility_constraints_spec.md**.

- Sort candidates by: (1) score_inflation descending, (2) ES95 descending.
- For each candidate in order:
  - Propose Inflation internal weights = candidate weights.
  - Check RC_cap and weight caps/mins feasibility within overall portfolio constraints model.
  - If feasible → **select and stop**.
- If none feasible → return **FAIL_FEASIBILITY** with reason `"No Inflation candidate satisfies caps"` and violated_constraints.

---

## 4. Failure Handling

- **FAIL_DATA:** Stop pipeline immediately. Do not write weights. Return:
  `{ "status": "FAIL_DATA", "reason": "..." }`

- **FAIL_FEASIBILITY:** Stop pipeline immediately. Do not write weights. Return:
  `{ "status": "FAIL_FEASIBILITY", "reason": "...", "violated_constraints": [ ... ] }`

---

## 5. Output / Logging (mandatory)

Return for Inflation block:

- **selected_candidate_name**
- **selected_internal_weights** (dict ticker → weight)
- **diagnostics:** avg_ret_type1, avg_ret_type2, worst_month_all, ES95, low_sample flags for Type1/Type2
- If selection skipped (e.g. single ticker): **selection_method** = `"SKIP_INTERNAL_SELECTION"`, **reason**

---

## 6. References

- **docs/portfolio_construction_policy.md** — §5.3 Inflation role, three mechanisms.
- **docs/docs/feasibility_constraints_spec.md** — RC cap, weight caps.
- **docs/docs/optimization_duration_spec.md** — shared growth_proxy, Duration proxy for Type1.
