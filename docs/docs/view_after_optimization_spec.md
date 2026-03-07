# View After Optimization — Protocol v2

**Policy link.** This document defines the **only permitted exception** to the rule "No manual weight adjustments" in [portfolio_construction_policy.md](../portfolio_construction_policy.md). Views (tilts) may be applied to the Policy portfolio **only** through this protocol. Final weights must never be edited by hand; all view-driven changes are executed deterministically by the system and reported for audit.

---

## 0) Baseline (Policy)

1. Build the Policy portfolio using all rules: mandate, stress suite, RB targets, RC_caps, weight caps/mins.
2. Save baseline weights, baseline RB, and baseline stress results.
3. Never edit final weights manually. Views enter only through this protocol.

---

## 1) View Request (the only things the PM sets)

### 1.1 Choose View Type

- **HEDGE:** increase asset X to improve resilience/stress/tail behavior.
- **TACTICAL:** increase asset X as a return bet.

### 1.2 Choose Manual Tilt Size (Δchoice)

PM selects Δ from a fixed menu: **{+1%, +2%, +5%}** Δweight of total portfolio  
(optional finer menu: {0.5%, 1%, 2%, 5%}).

**Important:** Δchoice is a weight add-on, not "% of risk."

### 1.3 Define at least ONE hard "hedge benefit" metric (HEDGE only)

"No clear hedge metric" is not allowed. Pick at least one:

- Worst-case stress loss improves by **≥ 0.5% NAV** (recommended default), OR
- **#PASS** stress scenarios increases by **≥ 1**, OR
- Tail metric improves by **≥ threshold** (ES/CVaR if available).

If none is set, HEDGE tilts cannot be evaluated and must be rejected as ambiguous.

---

## 2) Gate Statuses (must be explicit)

### 2.1 RB status (clear PASS vs FAIL)

Define **RB_corridor** (e.g., target ±5pp) and **RB_deviation_threshold** (e.g., 2pp).

- If RB is inside corridor → **PASS_RB**
- If RB is outside corridor but deviation ≤ RB_deviation_threshold → **PASS_BUT_RB_OFF**
- If deviation > RB_deviation_threshold → **FAIL_RB_INFEASIBLE**

### 2.2 Stress status (must be specific, not generic)

Replace generic **FAIL_STRESS** with:

- **FAIL_STRESS_DURATION**
- **FAIL_STRESS_INFLATION**
- **FAIL_STRESS_LIQUIDITY**
- (optional) **FAIL_STRESS_TAIL**

Always include: which scenario(s) failed.

---

## 3) Funding Rules (deterministic, avoids damaging protection)

### 3.1 Contributions-first

If there are cash contributions, buy asset X using contributions first (no selling).

### 3.2 If selling is needed: donor priority depends on view type

Donor selection is not "max RC_vol everywhere" by default. It is block-aware:

**For HEDGE tilts** (e.g., adding Gold/TIPS/Duration):

1. Donors are from **Growth first**.
2. Do **not** sell protective instruments (Duration/Inflation/Liquidity/Tail) unless absolutely required to pass gates.
3. Within allowed donors, sell highest RC_vol first, respecting min_weight.

**For TACTICAL tilts** (adding X as a bet):

1. Donors are from the **same block as X** first (intra-block rotation).
2. Cross-block selling is allowed only if intra-block donors are insufficient.
3. Within allowed donors, sell highest RC_vol first, respecting min_weight.

No discretionary "sell Y, buy X" decisions.

---

## 4) Execution Logic (system does NOT search "largest feasible")

### 4.1 Attempt to execute exactly the requested Δchoice

The system tries to implement the requested Δchoice (Δweight).

### 4.2 Auto-shrink if gates fail

If the requested Δchoice fails any gate, automatically reduce:

**5% → 2% → 1%** (or per your menu).

If even the smallest Δ fails → **TILT_REJECTED**.

The system **never** increases Δ beyond the chosen Δchoice and **never** hunts for "largest feasible."

---

## 5) Gates to Validate on Every Attempt

Each attempted Δ must satisfy, **in order**:

1. **Mandate:** TargetVol / MaxDD / liquidity / leverage rules.
2. **Stress suite:** must PASS; otherwise return specific stress failure code.
3. **RC_caps + weight caps/mins:** must PASS.
4. **RB status:** classify as PASS_RB, PASS_BUT_RB_OFF, or FAIL_RB_INFEASIBLE (per thresholds).

### 5.1 HEDGE benefit check (HEDGE only)

If all gates pass, evaluate the hard hedge metric(s):

- If hedge benefit threshold is met → accept executed Δ.
- If not met → do **not** call it "success"; return **TILT_NO_BENEFIT** (gates passed but hedge benefit not achieved) and revert to baseline or smallest Δ that meets benefit (if you allow downward search).

(Recommended default: if benefit not met at Δchoice, try smaller Δ only if it still might meet benefit; otherwise return TILT_NO_BENEFIT.)

---

## 6) Required Reporting (always)

For auditability the system must output:

- **Baseline:** weights, RB, stress results.
- **Request:** view type, asset X, requested Δchoice.
- **Execution:** executed Δ (may be smaller than requested).
- **Funding:** contributions used, donors sold (tickers + amounts), donor block(s).
- **Outcome status:** one of
  - **TILT_ACCEPTED**
  - **TILT_REJECTED**
  - **TILT_NO_BENEFIT**
  - plus **RB status** (PASS_RB / PASS_BUT_RB_OFF / FAIL_RB_INFEASIBLE)
  - plus **stress failure code** if applicable (FAIL_STRESS_DURATION / INFLATION / LIQUIDITY / TAIL)
- **Broken gate:** exactly which gate failed (mandate / stress / RC / weight / RB / benefit) and the key metric value(s).

### Report format (machine-readable)

Output may be provided as **view_execution_report.json** (or equivalent) with fields:

- `baseline_weights`, `baseline_rb`, `baseline_stress`
- `request`: `view_type`, `asset`, `delta_choice`
- `execution_delta`, `funding_contributions`, `funding_donors_sold` (tickers + amounts), `donor_blocks`
- `outcome_status`, `rb_status`, `stress_failure_code`
- `broken_gate`, `key_metric_values`

---

## 7) Summary of the Philosophy (one line)

**PM chooses type + Δchoice; the system executes it deterministically, shrinks if needed, never breaks constraints, never edits weights manually, and always reports what happened and why.**
