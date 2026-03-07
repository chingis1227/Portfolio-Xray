# Optimization Spec: Growth

This document defines the **Growth block** optimization only. Other optimization specs (e.g. ProLiquidity, feasibility, RC caps) live in separate files under `docs/docs/`.

---

## 1. Role of the Growth Block

- Growth is the **only block** that deliberately "buys" expected return.
- In stress: Growth's role is **not to hedge**; it is to **absorb the hit**.
- Defensive function is provided by Duration and Inflation, not by Growth.

---

## 2. Optimization Objective

**Goal:** Maximize expected return of the Growth block subject to the **given risk architecture**.

- **Objective:** maximize expected return (e.g. mean of returns) of the Growth block.
- **Scope:** only weights (and possibly composition) of assets **inside** the Growth block; block weight in RiskPortfolio may be implied by risk budget, not chosen by this step.

---

## 3. What Is Fixed (Not Optimized)

- **Growth risk budget** is fixed. Optimization **must not** increase Growth's share of RiskPortfolio risk (RC_vol share of Growth vs. total RiskPortfolio).
- Architecture of risk allocation (RB_growth, RB_duration, RB_inflation) is **input** to this step, not an output.
- All feasibility constraints apply: RC_vol caps, weight caps (Core/Satellite with Core = e.g. VOO, VT, VTI; min weight), Growth_HY and Growth_EM_debt sub-limits. See **docs/docs/feasibility_constraints_spec.md**.

---

## 4. Key Prohibition: No "Risk Diversification" Optimization Inside Growth

- **Do not** optimize for "diversification of risk" within the Growth block (e.g. do not minimize variance or minimize concentration of risk within Growth using in-sample correlations).
- **Reason:** In stress, correlations within Growth **tend to 1**. Historically low correlation within Growth is not a reliable tail-risk diversifier.
- **Implication:** Multiple Growth ETFs do **not** reduce tail risk; they provide **different return sources over time**, but in a crisis they fall together. The optimizer must not assume otherwise.

---

## 5. Execution Rules (Summary)

| Rule | Description |
|------|-------------|
| Objective | Maximize expected return of the Growth block. |
| Fixed | Growth risk budget; overall risk architecture. |
| Forbidden | Optimizing for in-Growth "risk diversification" or treating in-Growth correlation as tail protection. |
| Constraints | Feasibility (RC cap, weight caps, min weight, Growth_HY and Growth_EM_debt caps); long-only; weights sum to block allocation. |

---

## 6. References

- **docs/portfolio_construction_policy.md** — block roles, "No risk diversification optimization inside Growth", mandate hierarchy.
- **docs/docs/feasibility_constraints_spec.md** — RC cap, weight caps, Growth achievability, Equity-Only, Growth_HY and Growth_EM_debt sub-limits.
