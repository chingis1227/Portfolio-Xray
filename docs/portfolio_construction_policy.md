# Portfolio Construction Policy

# Portfolio Construction Policy

## 1. System Principle

The system constructs portfolios based on the **roles of structural blocks**, not on attempts to predict or “optimize for” market regimes.

Market regimes are not treated as an optimization target. Instead, they are used strictly as **diagnostic tools**. Regimes serve three functions:

- to run portfolio stress tests across different macro environments,
- to calibrate the **risk budget across blocks**, and
- to verify whether correlations and hedges break under stress.

Optimization is applied **only within a predefined portfolio architecture**. Its purpose is to determine how best to implement the role of each block, not to predict which market regime will occur next.

Within this framework, the **Growth block** is the primary source of expected return. This is where the portfolio intentionally takes risk in order to capture long-term upside.

All other blocks exist primarily to support **strategy survivability**, not to maximize metrics like Sharpe ratio. Their role is to:

- limit tail risk,
- reduce the probability of behavioral capitulation during drawdowns,
- improve the portfolio’s ability to survive prolonged adverse environments without forcing liquidation.

Therefore, the objective of the system is defined as:

**upside capture combined with strict downside control**, rather than maximizing a single metric such as Sharpe.

A key assumption for honest risk assessment is that **correlations within the Growth block should be treated as approximately 1 during stress conditions**.

This means that multiple equity ETFs inside the Growth block do **not** meaningfully diversify tail risk during crises, because they tend to fall together. Their purpose is different: they may diversify **sources of return over time** (different factors, styles, or segments), but they should never be treated as protection against extreme downside events.

## 2. Rule Hierarchy

When rules conflict, the system always applies them **from top to bottom**.  
A higher-level rule has strict priority and cannot be violated by lower-level rules or by optimization results.

### 2.1 Mandate Risk Guardrails

Purpose: define the **non-negotiable risk boundaries** of the portfolio.

Components typically include:
- TargetVol (annualized)
- Max Drawdown.

Rule: a portfolio configuration is considered **invalid** if it violates any mandate guardrail, regardless of expected return or statistical attractiveness.

---

### 2.2 Block-Level Risk Budget (Architecture)

Purpose: define the **structural allocation of risk** across the main portfolio blocks:

- Growth
- Duration
- Inflation

Calculation rule: the risk budget is defined and enforced **only on the RiskPortfolio**, which consists of:

Growth + Duration + Inflation

Cash-like instruments (BIL, short T-bills, or other liquidity buffers) are **excluded** from risk budget calculations.

Implication: optimization is **not allowed to alter the predefined risk budget shares of the blocks**. The architecture of risk allocation is fixed at this level.

---

### 2.3 Stress Judge

Purpose: verify that the chosen architecture remains **robust under predefined stress scenarios and factor shocks**.

Rule: if the portfolio **fails the stress validation**, the system must adjust the **architecture** (risk budget, hedge structure, liquidity buffers, overlays), rather than tuning optimization parameters.

---

### 2.4 Risk Contribution Caps (RC_vol)

Purpose: limit **risk concentration** at the asset or sub-block level using risk contribution to portfolio volatility (RC_vol).

Priority rule: **RC_vol caps override weight caps**.

If a weight cap allows the current weight but the RC_vol cap is violated, the weight must be reduced until the RC constraint is satisfied.

---

### 2.5 Weight Caps and Minimums

Purpose: enforce structural constraints related to:

- capital concentration
- liquidity
- implementability of the portfolio.

Rule: weight caps and minimum weights are applied **only after RC caps are satisfied** and must never cause RC constraints to be violated.

---

### 2.6 Optimization

Purpose: determine the best weights **within the predefined architecture and constraints**.

Rule: optimization is an **execution tool**, not a decision authority. It cannot:

- relax mandate guardrails,
- modify block risk budgets,
- override the Stress Judge verdict,
- violate RC caps or weight caps/minimums.

---

### Decision Logic Summary

The system follows the hierarchy:

1. **Mandate** defines the acceptable risk boundaries.  
2. **Risk Budget** defines the architecture of risk allocation.  
3. **Stress Judge** verifies the robustness of that architecture.  
4. **RC Caps and Weight Caps** enforce concentration control.  
5. **Optimization** selects the best feasible solution within those constraints.

## 3. Mandate Constraints

The **Mandate** defines the non-optimizable boundaries of portfolio risk and implementability.  
These parameters cannot be “improved” or overridden by statistical properties, covariance estimates, or backtest results.

If a portfolio configuration violates the mandate, it is considered **invalid**, regardless of its expected return or historical performance.

The mandate specifies the following elements:

### Target Return (desired)

The long-term target return of the portfolio (for example 6–8% annual nominal return).

This value serves as a **strategic orientation**, not as a guarantee.  
It is used to guide the selection of the **risk budget** and the structural allocation to the Growth block.

---

### TargetVol (annualized)

The target range for annualized portfolio volatility (for example 12–15%).

This parameter defines the acceptable level of overall portfolio risk and is used to determine whether additional liquidity scaling or structural adjustments are required.

---

### Max Drawdown

The maximum acceptable portfolio drawdown (for example −30% to −35%).

If a stress scenario or expected tail event implies a drawdown exceeding this threshold, the portfolio configuration must be rejected or restructured.

---

### Investment Horizon

The strategic investment horizon (for example 10 years).

The horizon determines the acceptable allocation to risky assets and the required strength of defensive blocks.

Shorter horizons require stronger downside protection and higher structural liquidity.

---

### Liquidity Constraint

The portfolio must maintain sufficient liquidity to ensure both structural stability and operational flexibility.

This includes:

- a permanent **structural minimum of cash-like liquidity**, and
- the ability to **reduce portfolio risk quickly without forced selling or destruction of hedge structures**.

Liquidity must therefore be treated as a structural component of the portfolio design.

---

### Leverage

Leverage is either:

- completely prohibited, or
- allowed only under **strict limitations defined by the mandate**.

Any leverage usage must be explicitly authorized and must not violate other mandate guardrails.

---

### Rebalancing Policy

The rebalancing framework is defined as part of the mandate and must be specified in advance.

It includes:

- the rebalancing frequency,
- deviation thresholds,
- trigger conditions,
- and permissible actions during stress events.

Rebalancing rules must ensure that the portfolio remains consistent with its risk architecture while avoiding unnecessary turnover.
## 4. Regime Grid


The portfolio must be structurally robust across the key macroeconomic environments.  
These regimes are **not predicted and not optimized for**. Instead, they are treated as a mandatory set of environments through which the portfolio must pass without violating the mandate or the core policy constraints.

The purpose of the regime grid is to verify that the portfolio architecture remains functional under different macro conditions.

### Required Survival Regimes

The portfolio must remain structurally coherent in the following environments:

**Growth / Disinflation (Risk-on)**  
Economic growth with slowing inflation.  
In this regime the portfolio should participate in upside primarily through the Growth block, while maintaining controlled overall risk.

**Reflation / Overheat**  
Economic growth with accelerating inflation.  
The portfolio must protect purchasing power and manage exposure to inflation and rising interest rates.

**Deflation / Recession**  
Falling economic growth combined with declining inflation.  
Defensive blocks should act as shock absorbers, reducing the drawdown of the Growth block and limiting the depth of the portfolio decline.

**Stagflation / Monetary Stress**  
Falling growth combined with rising inflation.  
Traditional hedges may degrade in this environment, making the Inflation block and structural liquidity particularly important.

---

### Liquidity Shock (Overlay Scenario)

In addition to the macro regimes above, the system explicitly considers a **Liquidity Shock**, which can occur within any macro regime.

Characteristics of this environment include:

- correlations between risk assets approaching 1,
- widening credit spreads,
- forced selling and margin-driven deleveraging,
- periods where market liquidity deteriorates and a “market without buyers” emerges.

In such scenarios, the portfolio must remain **operationally survivable**.  
It must avoid becoming a forced seller of risk assets and must retain sufficient liquidity to rebalance and stabilize the portfolio structure.


## 5. Portfolio Blocks and Roles

### 5.1 Growth


**Purpose of the Growth block**

The Growth block is responsible for **long-term capital appreciation** through exposure to corporate earnings, valuation expansion, and the credit cycle.

It is the **primary source of expected return** for the portfolio.

---

**Behavior under stress**

During recessions, financial crises, or panic-driven market environments, Growth assets typically decline significantly.

Within the Growth block, correlations between assets tend to **approach 1 under stress conditions**.  
For this reason, Growth assets are **not treated as sources of portfolio hedging**.

---

**Structure and sub-blocks**

All instruments that primarily express **equity-like risk** belong to the Growth block.

These include the following subcategories:

**Broad Equity (Core Index)**  
Broad market equity ETFs representing the core equity risk premium of the market.

**Quality / Dividend Equity**  
Equity strategies emphasizing quality companies, stable profitability, and dividend characteristics.  
These exposures represent a relatively more defensive form of equity risk within the Growth block.

**High Growth / Thematic Equity**  
High-beta segments or thematic exposures that amplify upside potential, typically at the cost of increased volatility and tail risk.

**Credit Beta (High Yield)**  
High-yield bonds are treated as **equity-like credit exposure**.  
During credit cycle deterioration, high-yield bonds tend to behave similarly to equities and can amplify portfolio drawdowns.

**Crypto / Optionality**  
A limited allocation to crypto assets may be included as **optionality within the Growth block**.  
This exposure introduces asymmetric upside potential but also extremely high volatility and tail risk.

---

**Key structural principle**

Diversification within the Growth block should **not be interpreted as diversification of tail risk**.

Because correlations between Growth assets tend to converge during crises, multiple Growth instruments do not materially reduce downside tail exposure.

Instead, diversification within Growth primarily provides **diversification of return sources over time** (different factors, styles, or sectors), rather than protection during systemic market stress.


### 5.2 Duration


**Purpose of the Duration block**

The Duration block serves as a **shock absorber during falling interest rate environments and deflationary downturns**.  
Its role is to reduce the depth of portfolio drawdowns through sensitivity to declining yields, rather than to generate the primary source of portfolio return.

---

**Behavior under stress**

In deflationary or recessionary scenarios, Duration assets typically **rise or decline much less than the Growth block**, partially offsetting losses from risk-on assets.

This stabilizing behavior helps limit the overall drawdown of the portfolio during economic contraction.

---

**Structure and sub-blocks**

Instruments assigned to this block include:

**Long Duration Sovereigns**  
Long-term government bonds provide the strongest exposure to falling yields and therefore the most powerful protection in deflationary shocks.

**Intermediate Duration (Aggregate / BND)**  
Intermediate-duration bond exposure provides a more balanced rate-sensitive stabilizer.  
If a fund is a mixed aggregate product (for example an aggregate bond ETF), it is classified according to its **dominant risk factor**. In this framework, aggregate bond funds are treated primarily as **rate instruments**.

**Investment Grade Credit (IG)**  
Investment-grade corporate bonds always belong to the Duration block and function as a **rate-sensitive stabilizer with carry**.

In this system, credit risk as an independent tail-risk source is implemented through **High Yield within the Growth block**, therefore IG bonds are **not treated as a separate credit-risk block**.

---

**Key limitations (conditional hedge)**

Duration should be treated as a **conditional hedge**, not a guaranteed protection.

The protective function of Duration can degrade when **real yields rise sharply**.

If the correlation **corr(Growth, Duration)** becomes persistently positive, the protective function of the Duration block is considered compromised.

In such cases, the defensive architecture must be re-evaluated, potentially involving:

- adjustments to the Duration structure,
- a stronger role for the Inflation block,
- increased structural liquidity,
- or the introduction of additional overlays.

### 5.3 Inflation

**Purpose of the Inflation block**

The Inflation block is designed to **protect the purchasing power of capital** and to act as a **monetary anchor** during periods of inflationary pressure and monetary instability.

---

**Behavior under stress**

This block is intended to stabilize the portfolio in environments such as:

- inflationary regimes,
- supply shocks,
- monetary stress.

In these environments the Growth block may suffer, and the Duration block may lose its protective function (for example during rising real yields).  
The Inflation block therefore provides an alternative form of portfolio stabilization.

---

**Structure and sub-blocks**

Instruments assigned to this block fall into three distinct protection mechanisms:

**CPI Protection (TIPS)**  
Treasury Inflation-Protected Securities (TIPS) serve as a hedge against CPI inflation.  
However, exposure to duration must be actively managed so that the block does not unintentionally become a hidden Duration risk.

**Monetary Hedge (Gold)**  
Gold always belongs to the Inflation block and serves as a monetary hedge during crises of confidence, currency debasement, or financial repression.

**Resource Shock Protection (Broad Commodities / Industrial Metals)**  
Commodity exposure protects the portfolio in scenarios involving resource shortages, supply shocks, or rising commodity-driven inflation.

---

**Key construction rule**

The Inflation block must **not be constructed using a single instrument**.

This is because the block represents **three distinct protection mechanisms**:

- CPI hedge (TIPS)
- monetary hedge (Gold)
- resource shock protection (commodities / metals)

These mechanisms are **not interchangeable** and each provides protection under different types of inflationary stress.

### 5.4 Liquidity


**Purpose of the Liquidity block**

The Liquidity block exists to ensure the **operational survivability of the portfolio during crisis conditions** and to preserve the ability to manage risk.

Liquidity serves three primary functions:

1. **Reduce the probability of forced selling** during liquidity shocks or market stress.
2. **Provide capital for rebalancing**, allowing the portfolio to add risk after drawdowns or rebalance toward target allocations.
3. **Allow volatility control toward TargetVol**, when such volatility scaling is permitted by the cash policy.

---

**Instruments**

Liquidity is implemented through **cash-like exposures** with minimal risk and high market liquidity, such as:

- short-term Treasury Bills (for example BIL),
- money market or cash-like instruments,
- ultra-short duration fixed income.

---

**Core rule (non-negotiable)**

The Liquidity block is **not a source of portfolio risk** and therefore must not participate in risk budgeting.

As a result:

- the Liquidity block is **excluded from the risk budget**, and
- both **risk budgeting and RC_vol calculations are performed only on the RiskPortfolio**, defined as:

Growth + Duration + Inflation

These calculations are performed **before any cash allocation is added to the portfolio**.

### 5.5 Tail Overlay

## 6. Risk Budget Rules
## 7. RC_vol and Weight Cap Rules
## 8. Feasibility Layer
## 9. Policy Profiles
## 10. Stress Testing Rules
## 11. Stress Pass/Fail Criteria
## 12. Required Output