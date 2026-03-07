# Feasibility Constraints Spec (Structural Constraints)

This document defines **formulas and checks** for the Technical Feasibility Layer only. It is the single source of truth for derived caps and achievability tests. No duplication of these formulas appears in the Portfolio Construction Policy.

**Config resolution:** If in `config.yml` the fields `rc_asset_cap_pct`, `max_single_security_weight_pct`, or `min_single_security_weight_pct` are **null** or **0**, the system uses the values given by the formulas below (from this spec). If a numeric value is set, that value is used as an override.

---

## Notation

- **N** — number of assets in RiskPortfolio (excluding cash proxy, e.g. BIL).
- **Nc** — number of core assets (only in Growth block).
- **Ns** = N − Nc (satellite count in Growth).
- **RB_growth, RB_duration, RB_inflation** — risk budget share of each block (sum = 1.0).
- **k_block** — actual number of assets in the block.
- **min_weight** = 0.01 (default minimum weight per asset).

**Invariant:** `sum(max_weight_i across all assets) >= 1.0` must hold (otherwise full allocation is impossible).

---

## 1. Global RC Cap

```
if N < 4:
    rc_asset_cap = 0.40
else:
    rc_asset_cap = min(0.25, max(0.10, 1.5 / N))
```

---

## 2. Risk Budget achievability (by RC)

For each block:

- **k_required_block** = ceil(RB_block / rc_asset_cap)

**Check:** For each block, **k_block ≥ k_required_block**.

If not satisfied → RB is not achievable with the current block composition. Either add assets to the block or change RB. The feasibility layer does not guarantee achieving RB; it only checks that it is not impossible under the caps.

---

## 2a. Constraints inside Growth (summary)

All of the following apply **only to the Growth block** and to risk measured on **RiskPortfolio** (Growth + Duration + Inflation) **before** adding BIL/cash.

- **Where risk is measured:** RC_vol and risk budget are computed only on RiskPortfolio (Growth + Duration + Inflation), before any cash/BIL is added.
- **Constraint priority:** RC_vol cap overrides weight cap. If a weight is within its cap but RC_vol is exceeded, the weight must be reduced until the RC cap is satisfied.
- **Global RC cap (per asset)** for RiskPortfolio: see **§1** — if N < 4 then rc_asset_cap = 0.40, else rc_asset_cap = min(0.25, max(0.10, 1.5/N)).
- **Growth risk budget achievability (by RC):**  
  Minimum number of assets in Growth: **k_growth ≥ ceil(RB_growth / rc_asset_cap)**.  
  If not satisfied, RB_growth is not achievable with the current Growth composition (add assets or change RB).
- **Weight caps inside Growth** (only Growth has Core/Satellite):  
  - Core (e.g. VOO, VT, VTI): max_weight_core = min(0.35, max(0.25, 2/N)).  
  - Satellite: if Ns ≤ 2 then max_weight_sat = 0.40; else use the formula in **§3.1**.  
  - Feasibility by weights: **Nc·max_weight_core + Ns·max_weight_sat ≥ W_growth**.
- **Equity-Only Mode** (when RB_growth ≥ 0.90): see **§6** — RC is tightened (rc_asset_cap = max(rc_asset_cap, 0.15)); max_weight_core ≤ 0.50, max_weight_sat ∈ [0.10, 0.15]; caps are not derived from N; achievability check: **Nc·max_weight_core + Ns·max_weight_sat ≥ 1.0**.

### 2b. High Yield (HY) sub-limit within Growth

High Yield within Growth is limited so it does not act as a second “hidden equity” and amplify tail risk.

- **Definition:** Assets in the **Growth_HY** sub-block (e.g. config `blocks.Growth_HY`: JNK, HYG) are treated as High Yield.
- **Rule (RC):**  
  **RC_vol(HY) ≤ 10% × RC_vol(Growth block)**  
  i.e. the sum of RC_vol over all HY assets must not exceed 10% of the total RC_vol of the Growth block.
- **Intent:** HY can add return and carry in good periods, but must not dominate risk or become a hidden second equity that increases portfolio tail risk.

### 2c. EM Debt sub-limit within Growth

EM Debt within Growth is limited in the same way as High Yield, so that credit beta (HY + EM Debt) does not dominate Growth risk.

- **Definition:** Assets in the **Growth_EM_debt** sub-block (e.g. config `blocks.Growth_EM_debt`: EM bond ETFs) are treated as EM Debt.
- **Rule (RC):**  
  **RC_vol(EM Debt) ≤ 10% × RC_vol(Growth block)**  
  i.e. the sum of RC_vol over all EM Debt assets must not exceed 10% of the total RC_vol of the Growth block.
- **Intent:** Same as HY: EM Debt can add return and carry, but must not dominate risk within the Growth block.

---

## 3. Weight Caps

### 3.1 Core/Satellite (Growth only)

- **Core:** e.g. VOO, VT, VTI (broad index equity ETFs; see config `growth_core_candidates`).  
- **Max weight for Core (within Growth):**  
  `max_weight_core = min(0.35, max(0.25, 2 / N))`
- **Max weight for Satellite (within Growth):**  
  If Ns ≤ 2:  
  `max_weight_sat = 0.40`  
  Else:  
  `max_weight_sat = min(0.25, max(min(0.10, max(0.05, 2/N)), (1 − Nc·max_weight_core) / (N − Nc) + 0.02))`

**Feasibility (Growth):**  
`Nc·max_weight_core + Ns·max_weight_sat ≥ W_growth`

### 3.2 Duration and Inflation

Core/Satellite does **not** apply. For any block *b*:

- `sum(max_weight_i in block b) ≥ W_b`
- If the block has one asset: `max_weight_single_asset ≥ W_b`

---

## 4. No Core case

If there is **no** Core (Nc = 0):

- If N ≤ 3: `max_weight_all = 0.40`  
- Else: `max_weight_all = min(0.25, max(0.10, 2.5/N))`

**Check:** `N·max_weight_all ≥ 1.0`

---

## 5. Minimum number of assets for Risk Budget

- k_growth   ≥ ceil(RB_growth   / rc_asset_cap)
- k_duration ≥ ceil(RB_duration / rc_asset_cap)
- k_inflation ≥ ceil(RB_inflation / rc_asset_cap)

*k* is the minimum number of assets in the block required to physically achieve the block’s risk budget.  
`RB_growth + RB_duration + RB_inflation = 1.0`.

---

## 6. Equity-Only Mode

**Activation:** RB_growth ≥ 0.90.

### 6.1 RC Cap

`rc_asset_cap = max(rc_asset_cap, 0.15)`

### 6.2 Weight Caps

- `max_weight_core ≤ 0.50`
- `max_weight_sat ∈ [0.10, 0.15]`

Caps are **not** derived from N. **Check:**  
`Nc·max_weight_core + Ns·max_weight_sat ≥ 1.0`

---

## 7. Default values when config is null or zero

When the system resolves constraints and finds **null** or **0** in config for:

- **rc_asset_cap_pct** → use the **Global RC Cap** formula above (and Equity-Only adjustment if applicable).
- **max_single_security_weight_pct** → use the appropriate cap from above (Core/Sat or max_weight_all, depending on block and Core presence).
- **min_single_security_weight_pct** → use **min_weight = 0.01** (1%).

Any explicit positive value in config overrides the formula for that parameter.
