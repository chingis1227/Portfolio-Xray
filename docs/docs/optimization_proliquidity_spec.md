# Optimization Spec: ProLiquidity (Liquidity)

This document defines the **liquidity** optimization only. Other optimization specs (e.g. risk budget, RC caps) live in separate files under `docs/docs/`.

---

## 1. Liquidity Execution Logic

This section defines the deterministic execution logic for liquidity handling during portfolio construction.

Liquidity is applied only **after the RiskPortfolio has been constructed**.

The RiskPortfolio includes only the following blocks:

- Growth
- Duration
- Inflation

At the stage of liquidity execution:

- RiskPortfolio weights must already sum to **1.0**
- portfolio volatility and RC_vol must already be computed
- all calculations must use **RiskPortfolio only**
- no cash allocation is included yet

---

# 1.1 Required Inputs

The liquidity engine requires the following inputs:

Core parameters

- cash_policy
- cash_proxy_ticker
- target_vol_annual
- current_vol_annual
- portfolio_value (if null or not provided, use initial_investable_amount so that config and engine agree)

Life liquidity parameters

- liquidity_need_months
- monthly_expenses

Portfolio state

- weights
- role_map
- rc_vol_by_asset
- asset_vols

Optional configuration

- N_rc
- growth_core_candidates
- donor_shift_mode

---

# 1.2 Life Liquidity Floor

Life Liquidity represents structural liquidity required for real-world financial needs.

It ensures the investor does not become a forced seller of risky assets during drawdowns.

Computation:


liquidity_amount = liquidity_need_months * monthly_expenses
liquidity_floor_pct = clamp(liquidity_amount / portfolio_value, 0.0, 1.0)


**portfolio_value:** If null or not set in config, use initial_investable_amount before computing the floor (same rule as in config).

Execution rules:

- if `liquidity_need_months == 0` → `liquidity_floor_pct = 0`
- if `monthly_expenses == 0` and `liquidity_need_months > 0` → configuration error
- if `portfolio_value <= 0` → hard failure

Life liquidity is **independent from volatility scaling**.

---

# 1.3 Volatility Scaling Cash

Technical cash may be used to reduce total portfolio volatility.

Computation:


scaler = target_vol_annual / current_vol_annual
vol_scaling_cash_weight = max(0.0, 1.0 - scaler)


Execution rules:

- `current_vol_annual` must be computed on **RiskPortfolio only**
- if `scaler >= 1.0` → `vol_scaling_cash_weight = 0`
- leverage is not allowed
- if `current_vol_annual <= 0` → fail unless handled by upstream logic

---

# 1.4 Cash Policy Switch

Supported values:


cash_policy ∈ {"required_floor", "allowed_for_scaling", "prohibited"}


Execution behavior:

### required_floor

- portfolio must maintain at least the liquidity floor
- additional cash may be used for volatility scaling

### allowed_for_scaling

- liquidity floor may be zero
- volatility scaling cash is allowed

### prohibited

- cash allocation is forbidden
- portfolio volatility must be reduced by restructuring RiskPortfolio only

Invalid policy values must raise configuration error.

---

# 1.5 Final Cash Weight

If:


cash_policy == "prohibited"


then:


cash_weight = 0.0


Otherwise:


cash_weight = max(liquidity_floor_pct, vol_scaling_cash_weight)


Execution constraints:

- enforce `0 <= cash_weight <= 1`
- if cash_weight > 1 → fail
- if cash_weight < 0 → fail

---

# 1.6 Final Portfolio Assembly

Let RiskPortfolio weights sum to:


sum(weights_risky) = 1


If cash is allowed:


risky_weight = 1 - cash_weight

FinalPortfolio =
risky_weight * RiskPortfolio
+ cash_weight * cash_proxy_ticker


If cash_policy = prohibited:


FinalPortfolio = RiskPortfolio


Execution rules:

- final weights must sum to **1**
- portfolio must remain **long-only**
- RiskPortfolio weights are scaled by `risky_weight`
- cash is appended only at final stage

---

# 1.7 Deterministic Alpha Shift

Trigger condition:


cash_policy == "prohibited"
AND
current_vol_annual > target_vol_annual


Goal:


annualized_vol(RiskPortfolio) ≤ target_vol_annual


without introducing cash.

---

# 1.7.1 Identify Risk Drivers

Compute RC_vol per asset.

Select donors:


RC_top = top-N_rc assets by RC_vol


Sorting rule:

- descending RC_vol
- tie-break lexicographically by ticker

Constraints:

- long-only portfolio
- donor weights cannot fall below zero
- donor set must not be empty

---

# 1.7.2 Select Recipient

Recipient selection rule:

1. If `"VOO"` exists → recipient = `"VOO"`
2. Else if `"VT"` exists → recipient = `"VT"`
3. Else if `"VTI"` exists → recipient = `"VTI"`
4. Else:


hedge_set = assets where role_map ∈ {Duration, Inflation}
recipient = lowest-volatility asset within hedge_set


Tie-break rule:


alphabetical ticker order


Constraints:

- recipient must exist in portfolio
- do not select globally lowest-vol asset across all blocks
- recipient must belong to **Growth core** (e.g. VOO, VT, VTI) **or hedge blocks** (Duration, Inflation)

---

# 1.7.3 Solve Minimal Alpha

Find minimal:


alpha ∈ [0, alpha_max]


such that:


vol(shifted_portfolio) ≤ target_vol_annual


Algorithm:

- deterministic **bisection search**

Constraints:


alpha_max = total removable donor weight


Termination criteria:

- volatility constraint satisfied
- tolerance reached
- iteration limit reached

If portfolio already satisfies TargetVol:


alpha = 0


---

# 1.7.4 Apply Shift

Weight transfer rule:


remove alpha from donor assets
add alpha to recipient


Donor reduction modes:

- proportional
- equal

The chosen mode must remain **consistent across runs**.

Post-shift constraints:


sum(weights) = 1
weights ≥ 0


---

# 1.8 Failure Conditions

Return:


FAIL_CONSTRAINT


If any of the following occurs:

- TargetVol cannot be reached with `cash_policy = prohibited`
- no recipient asset exists
- donor set empty
- invalid configuration
- negative portfolio value
- final weights violate long-only constraint
- weights do not sum to 1

Required diagnostic message:


TargetVol cannot be achieved with cash_policy='prohibited'
given the current universe and constraints.


---

# 1.9 Determinism Requirement

The liquidity execution engine must be fully deterministic.

Given identical:

- inputs
- configuration
- portfolio universe
- market data

the system must produce identical:

- alpha
- final cash weight
- final portfolio weights

Randomized search methods are not allowed.
