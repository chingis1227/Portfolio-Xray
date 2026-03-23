# Optimization Spec: Duration (Block Selection via Candidate Scoring)

This document defines **Duration block** selection only. No mean-variance optimization is run inside this block. Objective is hedge effectiveness: "helps when Growth is down", plus tail control. Other specs: **docs/docs/optimization_growth_spec.md**, **docs/docs/optimization_inflation_spec.md**, **docs/docs/optimization_proliquidity_spec.md**, **docs/docs/feasibility_constraints_spec.md**.

**Policy link.** This selection operationalizes **docs/portfolio_construction_policy.md** §5.2: Duration as shock absorber when Growth is down; criteria (downside beta, performance in worst-Growth months) implement that role.

---

## 0. Shared: Growth Proxy (fixed)

- **growth_proxy** = `"VOO"` always. Do NOT infer from portfolio contents.
- If VOO price/return series is unavailable in the dataset → return **FAIL_DATA** with reason `"VOO data missing"`.

---

## 1. Inputs (fixed for this routine)

- **RB_block** — risk budget share for Duration (from rc_block_targets).
- **RC_cap**, **weight caps**, **min weight** — from feasibility (see **docs/docs/feasibility_constraints_spec.md**); may be resolved from config or formulas.
- **Universe of the block** — built from user-provided role tickers (see Config below).
- **Baseline** — for ES95 comparison (see §1.1).

### 1.1 Baseline (for ES95 filter)

- **Baseline** = current internal weights of the Duration block from the **last policy snapshot** (previous rebalance date).
- If first run (no policy snapshot / baseline absent) → **baseline** = equal-weight over available tickers in the block.

---

## 2. Config: Duration Role Tickers

Role tickers are **user-provided at portfolio build time**. Do NOT auto-detect roles from names.

Config keys (add to config under a dedicated section, e.g. `duration_roles` or equivalent):

| Key | Description | Required |
|-----|-------------|----------|
| **duration_int_ticker** | Intermediate treasuries proxy (e.g. IEF) | Can be null |
| **duration_long_ticker** | Long treasuries proxy (e.g. TLT) | Can be null |
| **duration_ig_ticker** | Investment grade proxy (e.g. LQD) | Can be null |

- Build Duration universe from the **non-null** tickers provided.
- At least one of the three must be provided; otherwise Duration block is empty and selection is skipped (see A1.1).

---

## 3. A) Duration Block Selection

### A0) User-provided role tickers

- Use only the tickers from config (duration_int_ticker, duration_long_ticker, duration_ig_ticker).
- Duration universe = list of provided non-null tickers.

### A1) Build candidate mixes

Let **INT** = duration_int_ticker, **LONG** = duration_long_ticker, **IG** = duration_ig_ticker.

**Case A1.1:** Only one of {INT, LONG, IG} is provided  
- `candidates` = `[{ name: "D0", weights: { that_ticker: 1.0 } }]`  
- `selection_method` = `"SKIP_INTERNAL_SELECTION"`

**Case A1.2:** Exactly two of {INT, LONG, IG} are provided  
- Let (A, B) be the two tickers in deterministic order: filter [INT, LONG, IG] by non-null, then take in that order.  
- Minimum candidates:
  - D1: A 100% / B 0%
  - D2: A 50% / B 50%
  - D3: A 0% / B 100%
- Optional extra: D4: A 70% / B 30%, D5: A 30% / B 70%

**Case A1.3:** INT and LONG provided (IG optional)  
- Base treasury candidates:
  - D1: 100% INT
  - D2: 100% LONG
  - D3: 70% INT + 30% LONG
  - D4: 50% INT + 50% LONG
- If IG provided, add: D5: 40% INT + 40% LONG + 20% IG  
- If IG not provided, omit D5.

### A2) Downside Hedge Check (mandatory)

- **bad_months** = months where return(VOO) < 0.
- For each candidate c:
  - r_c = weighted monthly return series of the candidate.
  - **beta_down** = OLS beta of r_c on r_VOO using only **bad_months** (y = r_c[bad_months], x = r_VOO[bad_months]).
  - If too few bad_months, compute on full sample and set **low_sample_beta** = true.
  - Pass rule: beta_down ≤ 0.0 ideal; **soft pass** up to beta_down ≤ +0.2.
  - If beta_down > +0.2 → **discard** candidate.

### A3) Worst-Growth-Month Score (main ranking)

- **N_worst** = 12 (fixed).
- **worst_N_months** = 12 months with lowest return(VOO).
- For each remaining candidate:
  - avg_ret_in_worst = mean(r_c[worst_N_months])
  - worst_month_in_worst = min(r_c[worst_N_months])
  - **score_duration** = avg_ret_in_worst − 0.5 × |worst_month_in_worst|

### A4) Tail Filter (ES95)

- **ES95_c** = mean of bottom 5% monthly returns of r_c (full sample).
- **Baseline** defined in §1.1. If baseline exists: reject candidate if ES95_c is worse than baseline_ES95 by more than 0.003 (0.3% per month).
- If no baseline: use ES95 as tie-breaker only (higher ES95 = less negative = better).

### A5) Select + Apply Caps

- **Feasibility context:** Check feasibility in the context of the **full RiskPortfolio** (Growth + Duration + Inflation). Other blocks use their **current or target** weights; the candidate provides Duration internal weights. Global RC_cap and weight caps/mins must be satisfied. See **docs/docs/feasibility_constraints_spec.md**.

- Sort remaining candidates by: (1) score_duration descending, (2) ES95 descending.
- For each candidate in order:
  - Propose Duration internal weights = candidate weights.
  - Check RC_cap and weight caps/mins feasibility for the **full portfolio** with this candidate.
  - If feasible → **select and stop**.
- If none feasible → return **FAIL_FEASIBILITY** with reason `"No Duration candidate satisfies caps"` and list violated constraints.

---

## 4. Failure Handling

- **FAIL_DATA:** Stop pipeline immediately. Do not write weights. Return:
  `{ "status": "FAIL_DATA", "reason": "..." }`

- **FAIL_FEASIBILITY:** Stop pipeline immediately. Do not write weights. Return:
  `{ "status": "FAIL_FEASIBILITY", "reason": "...", "violated_constraints": [ ... ] }`

---

## 5. Output / Logging (mandatory)

Return for Duration block:

- **selected_candidate_name**
- **selected_internal_weights** (dict ticker → weight)
- **diagnostics:** beta_down, avg_ret_in_worst12, worst_month_in_worst, ES95, low_sample_beta (flag)
- If selection was skipped (e.g. single ticker): **selection_method** = `"SKIP_INTERNAL_SELECTION"`, **reason** (e.g. "Single Duration ticker")

---

## 6. References

- **docs/portfolio_construction_policy.md** — §5.2 Duration role, conditional hedge.
- **docs/docs/feasibility_constraints_spec.md** — RC cap, weight caps, achievability.
