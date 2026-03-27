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


## 1.1 Core System Rules

**One instrument = one home.**  
Each ETF or instrument belongs to exactly one block: Growth, Duration, Inflation, Liquidity, or Tail.  
Reassigning an instrument to a different block is only possible by changing the inputs and rebuilding the system.

**No manual weight adjustments.**  
Final portfolio weights are **produced by optimization** (constraints, client metrics, optimization specs); they must not be set by hand in config. After optimization runs, weights can be exported and saved (e.g. to config for the next run). Any change to the portfolio must be implemented through changes in the input parameters (mandate, risk budget, caps, asset universe, cash_policy) followed by a full system rebuild. The **only permitted exception** is applying a PM view (tilt) via the protocol defined in **docs/docs/view_after_optimization_spec.md** ("Add My View After Optimization"): the system executes the requested tilt deterministically, may auto-shrink the tilt if gates fail, and always reports the outcome; manual editing of final weights remains prohibited.

**Optimization by roles, not by regimes.**  
Market regimes are not predicted or optimized for.  
They are used only as a diagnostic judge through stress testing, hedge degradation checks, and risk budget calibration.

**Mandate has absolute priority.**  
TargetVol and Max Drawdown (optionally ES/CVaR) are hard constraints.  
They cannot be overridden by optimization, covariance estimates, or backtest results.

**Risk budget defines the architecture.**  
The distribution of risk between Growth, Duration, and Inflation is determined at the risk budget level.  
Optimization within blocks cannot alter the predefined block risk shares.

**Risk budget and RC are calculated only on RiskPortfolio.**  
Risk budgeting and RC_vol calculations are performed only on:

RiskPortfolio = Growth + Duration + Inflation

Liquidity (BIL / short T-bills) and Tail overlays are excluded from the risk budget and must not dilute RC signals.

**RC_vol cap has absolute priority.**  
When constraints conflict, RC_vol caps override weight caps.  
If a weight cap allows the current allocation but the RC cap is violated, the weight must be reduced until the RC constraint is satisfied.

**No “risk diversification optimization” inside Growth.**  
Under stress conditions, correlations within the Growth block should be treated as approximately 1.  
Different Growth instruments diversify sources of return over time but do not meaningfully reduce tail risk.

**Duration is a conditional hedge.**  
If real yields rise significantly or the correlation corr(Growth, Duration) becomes persistently positive, the defensive function of Duration is considered degraded.  
In such cases, the standard “Growth ranges for MaxDD” lose validity and the defensive architecture must be rebuilt, typically through adjustments to Duration, Inflation exposure, and liquidity.

**Liquidity has two separate functions and must not be mixed.**

Life Liquidity Floor  
A minimum structural cash buffer designed to cover financial obligations and avoid forced selling during drawdowns.

Vol-Scaling Cash  
Technical cash used only to reduce portfolio volatility toward TargetVol when the cash policy allows it.

**Leverage (prohibited by default).**  
The base policy of the system assumes no leverage.  
If current volatility is below TargetVol, risk is not increased through leverage; instead, vol-scaling cash is reduced or eliminated.  
Leverage may only be enabled as a separate mandate regime with explicit limits, activation rules, and additional Stress Judge validation.

**If cash is prohibited, risk reduction occurs through RiskPortfolio restructuring.**  
In this case, the adjustment process is deterministic: assets with the highest RC_vol (top RC donors) are reduced, and weight is transferred to a predefined recipient (VOO/VT or the lowest-volatility assets within Duration and Inflation) until TargetVol is satisfied while respecting minimum weight constraints.

**Tail overlay is not a return driver.**  
Tail positions are distribution insurance.  
They are maintained at small weights, expected to have negative carry in normal environments, and are held purely for convexity during crisis events.

**MaxDD honesty rule.**  
If the investor cannot psychologically tolerate the declared Max Drawdown, the mandate itself is invalid.  
In such a case, the portfolio will fail during the first severe stress event regardless of how attractive the model appears statistically.

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

Operational target-selection order (when profile ranges are available):

1. Use profile midpoint (`rc_block_targets`) as the first optimization target.  
2. If no acceptable solution is found, search targets inside profile `min/max` ranges with the simplex condition `Growth + Duration + Inflation = 1`.  
3. If still no acceptable solution is found, run an expanded fallback search with `min - 5 pp` and `max + 5 pp` (clipped to `[0, 1]`).

The **RB corridor check remains unchanged**: for each tested target, realized RC must be within target ± corridor (default ±5 pp).

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

Specific formulas and achievement tests for these constraints are set in **docs/docs/feasibility_constraints_spec.md** (no duplication here).

---

### 2.6 Optimization

Purpose: determine the best weights **within the predefined architecture and constraints**.

Rule: optimization is an **execution tool**, not a decision authority. It cannot:

- relax mandate guardrails,
- modify block risk budgets,
- override the Stress Judge verdict,
- violate RC caps or weight caps/minimums.

---

### 2.7 Data Policy, NaN, Young ETFs and Dynamic Backtest

For **data policy**, handling of **NaN**, treatment of **young ETFs**, the **dynamic NaN-safe backtest** (within-block equal redistribution, RC-gated fallback to cash), and **baseline vs full** reporting, see **docs/data_policy_nan_young_etfs.md**.
That document is the source of truth for: no rewriting of history, join policy (inner for cov/RC, outer for single-asset charts), inclusion from first full monthly point, mandatory report items (inception dates, NaN policy, comparison period), and **§8** (dual covariance / eligibility for risk-budget **optimization** via `young_etf_optimization_policy` in config).

---

### Production workflow (implementation)

In production runs, the pipeline **writes portfolio weights** when the **mandate historical max drawdown** check passes and there is no **FAIL_DATA / FAIL_FEASIBILITY / FAIL_RC** exit.

- **Mandate (blocking):** **FAIL_MANDATE** if realized portfolio max drawdown on the **full overlapping monthly history** exceeds `target_max_drawdown_pct`, or if that check is inconclusive (insufficient data). No weights written.
- **RB corridor (target ± 5 pp):** If realized block RC is outside the corridor, status is set to **CANDIDATE_RB_BREACH** and violation **RB_BREACH** is recorded; weights are still written if the mandate passed.
- **Stress diagnostics (non-blocking):** Scenario PnL, historical episodes (2008 / 2020 / 2022), Role/RC flags produce **`DIAG_*` codes** and **`DIAG_ATTENTION`** / **`DIAG_PASS`** statuses. They are recorded in **`stress_diagnostic_report`** and **`stress_summary`**; optional informational violation **`FAIL_STRESS`** with `note: diagnostic_only` may appear; **weights are still written** if the mandate passed.
- **RC_vol caps:** RC caps are enforced when the solver allows; if the solver uses a fallback and per-asset RC is violated, status is **OK_FALLBACK**, violation **VIOL_RC_ASSET_CAP** lists breached tickers and cap level; weights are still returned and written when the mandate passed.

The single output object (**run_result.json**) carries: weights, status (APPROVED | CANDIDATE_RB_BREACH | OK_FALLBACK | FAIL_DATA | FAIL_FEASIBILITY | FAIL_RC | **FAIL_MANDATE**), **mandate_check**, **stress_diagnostic_report**, violations, rb_deltas_pp, rc_breaches, stress_summary, next_actions, and resolved_config. **Code behaviour and this policy document are aligned** (single source of truth).

For a concise reference on **what blocks writing weights** and **how to interpret each status**, see **docs/production_workflow.md**.

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

**Composition and sub-blocks (all instruments belong only here)**

Within the Growth block, all instruments are classified as follows. **Core** is the only non-satellite sub-block; everything else are **Satellites**.

**Broad Equity (Core Index)**  
Wide index equity ETF as the base carrier of the market risk premium. Core candidates include, for example, **VOO**, **VT**, **VTI** (and any other broad market index ETF designated as Core in config).

**Satellites** (all other Growth instruments):

- **Quality / Dividend Equity** — Equity with a focus on quality, sustainable profitability, and dividend profile as a more "defensive" form of equity risk within Growth.
- **Defensive Sector Equity (Staples/Utilities/Healthcare)** — Sector "defensive" stocks with more stable demand and cash flows, which typically fall less in recessions but remain equity beta; utilities are additionally sensitive to rates.
- **Cyclical Sector Equity (Discretionary/Financials/Industrials/Energy)** — Sector cyclical stocks that amplify portfolio sensitivity to economic growth, credit cycle, and commodity prices; in risk-off and credit stress they often underperform the market.
- **US Size Tilts (Mid/Small)** — Mid/small-cap tilts as an equity-premium enhancer and "internal" diversifier within the US; typically higher volatility and deeper drawdowns in tightening/recessions.
- **Regional / ex-US Equity (Diversifiers)** — Regional and ex-US exposures adding currency and country cycle, reducing dependence on the US and a single market; in global liquidity shocks correlations still rise, but over the horizon they help through rotation of regional leadership.
- **High Growth / Thematic** — High-beta segments and thematic exposures that amplify upside at the cost of tail risk.
- **Credit Beta (High Yield + EM Debt + Preferred)** — Credit as equity-like risk: in credit cycle deterioration it behaves like equities, spreads widen, drawdowns deepen.
- **Crypto / Optionality** — Limited optionality within Growth (asymmetry, but high volatility and tail risk).
- **Real Assets Equity (REIT / Infrastructure Equity)** — Public "real assets" equity (REITs, infrastructure) giving exposure to nominal cash flows (rent, tariffs, contracts) and potentially benefiting from moderate inflation via revenue growth. This is equity-like risk, sensitive to rates, funding cost, and credit cycle, so in tightening and liquidity stress it often falls with the market.
- **Real Assets Equity (Commodity-linked equity: miners/E&P)** — Equity in extractive and upstream oil & gas companies providing operational leverage to commodity prices. This is not a commodity hedge but equity with dual beta: to the market (risk-off) and to the commodity cycle (supply/demand, CAPEX, OPEC, geopolitics). In liquidity crises it can sell off like equity even when commodities hold; in commodity supercycles it can outperform the physical commodity.

**Risk limits within Growth (RC)**  
High Yield risk within Growth is limited via risk contribution:

- **RC_vol(HY) ≤ 10% × RC_vol(Growth block)**  
  (sum of RC_vol over all High Yield assets in the Growth block must not exceed 10% of the total RC_vol of the Growth block.)

The same cap applies to **EM Debt** within Growth:

- **RC_vol(EM Debt) ≤ 10% × RC_vol(Growth block)**  
  (sum of RC_vol over all EM Debt assets in the Growth block must not exceed 10% of the total RC_vol of the Growth block.)

See **docs/docs/feasibility_constraints_spec.md** for definitions of Growth_HY and Growth_EM_debt sub-blocks and formulas.

---

**Key structural principle**

Diversification within the Growth block should **not be interpreted as diversification of tail risk**.

Because correlations between Growth assets tend to converge during crises, multiple Growth instruments do not materially reduce downside tail exposure.

Instead, diversification within Growth primarily provides **diversification of return sources over time** (different factors, styles, or sectors), rather than protection during systemic market stress.

**Growth optimization rule.** The objective and constraints for optimizing weights within the Growth block are defined in **docs/docs/optimization_growth_spec.md**. In short: maximize expected return of the Growth block; Growth risk budget is fixed; optimization must not target "risk diversification" within Growth, because in stress intra-Growth correlations tend to 1.

---

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

**Duration block selection rule.** The objective and procedure for choosing the internal composition of the Duration block (candidate scoring by downside hedge and worst-Growth-month performance, no mean-variance) are defined in **docs/docs/optimization_duration_spec.md**.

---

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

**Inflation block selection rule.** The objective and procedure for choosing the internal composition of the Inflation block (candidate scoring by Type1/Type2 stress windows and tail filter, no mean-variance) are defined in **docs/docs/optimization_inflation_spec.md**.

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

---

**Liquidity Structure: Life Liquidity vs Technical Cash**

The Liquidity block can serve two distinct purposes that must be clearly separated in the system:

1) **Life Liquidity (Liquidity Floor)**  
2) **Volatility Scaling Cash (Technical Cash)**

These functions serve different objectives and must not be confused.

---

**Life Liquidity (Liquidity Floor)**

Life Liquidity represents a **structural reserve of cash-like assets** intended to cover living expenses or external obligations.

The goal is to ensure that the investor **does not become a forced seller of risky assets during drawdowns or market crises**.

Key characteristics:

- The liquidity floor is determined by **real financial needs**, not portfolio optimization.
- It represents a **minimum structural allocation to cash-like instruments**.
- This allocation is independent from portfolio volatility management.

Typical inputs may include:

- number of months of expenses to cover,
- estimated monthly expenses,
- current portfolio value.

(Config: liquidity_need_months, monthly_expenses, portfolio_value; if portfolio_value is not set, initial_investable_amount is used.)

If no life-liquidity requirement exists, the liquidity floor may be set to zero.

---

**Volatility Scaling Cash (Technical Cash)**

In addition to life liquidity, cash may be used as a **technical tool to control total portfolio volatility**.

This function exists only when allowed by the portfolio's **cash policy**.

In this case:

- the system may temporarily allocate a portion of the portfolio to cash-like instruments,
- the objective is to reduce total portfolio volatility toward **TargetVol**,
- this cash allocation is purely **risk-management driven**, not related to living expenses.

---

**Cash Policy**

The behavior of liquidity in the system is controlled by a configurable **cash policy**.

The cash policy determines whether cash is:

- mandatory as a structural floor,
- allowed as a volatility management tool,
- or completely prohibited.

Typical policy modes include:

- **required_floor**  
  The portfolio must maintain at least the life-liquidity floor.  
  Additional cash may be used for volatility scaling.

- **allowed_for_scaling**  
  The life-liquidity floor may be zero.  
  Cash can still be used for volatility scaling if needed.

- **prohibited**  
  Cash allocations are not allowed.  
  Portfolio volatility must be controlled **only by restructuring the RiskPortfolio** (Growth, Duration, Inflation).

---

**Portfolio Construction Order**

Liquidity is applied **after** the RiskPortfolio is constructed.

The sequence is therefore:

1. Construct the RiskPortfolio using the blocks:
   Growth + Duration + Inflation.

2. Compute portfolio risk metrics (volatility, RC_vol, etc.) using only the RiskPortfolio.

3. Apply liquidity rules according to the cash policy.

4. If cash is used, the final portfolio becomes a combination of:

RiskPortfolio + Liquidity

This ordering ensures that **cash does not distort risk budgeting or risk contribution calculations**.

### 5.5 Tail Overlay

The Tail overlay represents **distribution insurance rather than a source of return**.  
It is added on top of the core portfolio blocks and is designed to protect against rare but destructive events when correlations between risk assets approach 1 and traditional hedges stop functioning.

The typical allocation to the Tail overlay is **0.5–2% of the portfolio**.  
It is **excluded from the risk budget** and is not treated as a driver of expected portfolio return.

Typical instruments include **long volatility strategies**, as well as **protective puts or put spreads**.

The economics of the Tail overlay are interpreted as an **insurance premium**:  
under normal market conditions it usually generates negative carry, but during panic phases it provides **convexity** and helps reduce the depth of portfolio drawdowns.

## 6. Sanity Check vs Policy Portfolio

The system distinguishes between the **Policy Portfolio** and a set of **baseline diagnostic portfolios**.

The **Policy Portfolio** is the only portfolio that is intended for implementation and rebalancing.  
It is constructed according to the full system architecture: mandate constraints, block roles, risk budgeting across blocks, risk concentration limits, structural constraints, and optimization used strictly as an execution tool.

Alongside the Policy Portfolio, the system constructs a set of **baseline reference portfolios** built on the same universe of risk assets. These baseline portfolios are not intended for investment and are used exclusively for diagnostic comparison.

Typical baseline constructions include:

- an **equal-weight portfolio**, where all risk assets receive the same capital allocation,
- a **risk-parity portfolio**, where risk contributions are balanced across assets.

These baseline portfolios serve as neutral reference points. Their purpose is to provide transparency regarding what the chosen architecture of the Policy Portfolio adds in terms of performance, risk structure, and stress resilience.

The system therefore evaluates the Policy Portfolio relative to these baselines across key dimensions such as return characteristics, volatility behavior, drawdown profile, stress-test outcomes, and concentration of risk across assets and blocks.

This comparison ensures that the structural decisions embedded in the Policy Portfolio are intentional and that any additional complexity introduced by the architecture is justified by improved robustness or return characteristics.


### 6.1 Baseline Construction Rules (EW / RP)

To keep the baseline comparison clean and interpretable, **Equal-Weight (EW)** and **Risk-Parity (RP)** must be treated as pure diagnostic references.

- **EW baseline:** all eligible risk assets receive equal capital weights.
- **RP baseline:** weights are selected to equalize **asset-level RC_vol** as closely as numerically feasible, under long-only and fully-invested conditions.

For EW/RP baselines, the system must **not** apply Policy-portfolio construction logic, including:

- block-role construction rules,
- block risk-budget targets,
- RC concentration caps from Policy construction,
- Policy-specific weight caps or discretionary overlays,
- hidden or ad-hoc filters introduced only for Policy optimization.

EW/RP are therefore intentionally simple, so that any difference versus the Policy Portfolio can be attributed to architecture rather than to hidden implementation choices.


### 6.2 Baseline Evaluation and Interpretation

EW and RP must be evaluated with the **same data pipeline and validation framework** as the Policy Portfolio (same return definitions, windows, metrics, stress framework, and client-fit checks).

Comparison should explicitly cover:

- return characteristics (e.g., CAGR),
- risk and downside profile (volatility, drawdown, downside/tail metrics),
- stress-test status and fail reasons,
- concentration/diversification of risk across assets and blocks.

A baseline may pass one gate (for example, MaxDD gate) and fail another gate (for example, stress role checks).  
This is expected and should be interpreted as a **multi-constraint diagnostic signal**, not as a logical inconsistency.


## 7. Risk Budget Orientation

Risk budgeting defines the **strategic distribution of risk across the core portfolio blocks**.

Only blocks that represent active sources of portfolio risk participate in the risk budget.  
These blocks are typically:

- Growth
- Duration
- Inflation

Liquidity and Tail overlays are not considered active risk sources and therefore do not participate in risk budgeting.

The purpose of the risk budget is to define the **architectural balance of risk** within the portfolio.  
It determines which block is expected to carry the primary exposure to market risk and which blocks are responsible for stabilizing the system under adverse conditions.

Different investor profiles imply different orientations of the risk budget.  
More conservative profiles allocate a larger share of risk to defensive blocks, while more growth-oriented profiles concentrate risk more heavily in the Growth block.

These orientations represent **strategic profiles**, not deterministic allocations.  
They serve as starting frameworks for portfolio construction and must always be validated through stress testing and structural risk analysis.


## 8. Max Drawdown Interpretation

Maximum drawdown represents the **upper bound of acceptable portfolio pain**, but it cannot be mechanically translated into a fixed allocation to the Growth block.

Tables linking drawdown targets directly to equity exposure should therefore be interpreted only as **initial hypotheses**, not as deterministic rules.

The actual drawdown behavior of a portfolio depends primarily on the effectiveness of its defensive architecture.  
Several structural factors determine the true drawdown profile, including:

- the current correlation structure between the portfolio blocks,
- whether the Duration block is functioning as a genuine hedge,
- the quality and composition of the Inflation block,
- the size and role of Liquidity and Tail overlays.

If defensive blocks degrade or lose their hedging properties—for example due to rising real yields or structural correlation shifts—the previously assumed relationship between Growth exposure and drawdown risk may no longer hold.

In such situations, the appropriate response is not to rely on static allocation ranges but to **rebuild the defensive architecture** of the portfolio.


## 9. Stress Testing Framework

Stress testing is a central validation tool of the system.  
Its purpose is to evaluate whether the portfolio architecture remains functional under severe but plausible adverse conditions.

The portfolio must be evaluated across a set of predefined stress environments that represent different forms of systemic pressure on financial markets.

These stress environments include shocks to equity markets, credit markets, interest rates, inflation dynamics, and market liquidity conditions.

The goal of stress testing is not to forecast future events but to verify that the portfolio structure can survive a range of adverse scenarios without violating mandate constraints or losing its internal defensive logic.

Stress testing therefore functions as a **structural judge of portfolio robustness**, not as a predictive model.


## 10. Stress Validation Logic

A portfolio configuration is considered to pass the stress framework only if several conditions are simultaneously satisfied.

First, the simulated portfolio loss must remain within the limits defined by the mandate.  
If a stress scenario implies losses beyond the maximum acceptable drawdown threshold, the configuration must be considered invalid.

Second, the defensive blocks of the portfolio must perform their intended roles.  
In environments where Growth assets suffer significant declines, at least one defensive mechanism must provide stabilization.

Third, the portfolio must avoid excessive concentration of risk.  
Stress environments often cause correlations between risk assets to increase, and the system therefore verifies that risk concentration does not become dominated by a small number of positions.

Failure of any of these conditions indicates that the portfolio architecture is not sufficiently robust and must be reconsidered.


## 11. Factor Exposure Diagnostics

In addition to scenario-based stress tests, the system evaluates the portfolio's sensitivity to key macro-financial factors.

These factor diagnostics help identify whether the portfolio has unintended exposures to major market drivers such as equity markets, real interest rates, inflation shocks, credit spreads, or currency movements.

Factor analysis does not automatically invalidate a portfolio configuration.  
However, extreme or unintended sensitivities may indicate structural weaknesses that require further review.

Where explicit limits for factor exposures are defined by policy, violations must trigger a stress warning or failure condition depending on severity.


## 12. Stress Evaluation Outcome

The stress testing process produces a clear evaluation of the portfolio's structural robustness.

The result of the stress evaluation can fall into one of several categories:

- **Pass**, indicating that the portfolio satisfies mandate limits, defensive roles remain functional, and risk concentration remains acceptable.
- **Pass with warning**, indicating that the portfolio remains within mandate limits but exhibits structural sensitivities that require monitoring or manual review.
- **Fail**, indicating that the portfolio violates one or more critical constraints and must be restructured before implementation.

When the **View After Optimization** protocol (docs/docs/view_after_optimization_spec.md) is used, stress failure must be reported with a **specific scenario code**, not a generic "Fail": **FAIL_STRESS_DURATION**, **FAIL_STRESS_INFLATION**, **FAIL_STRESS_LIQUIDITY**, or (if applicable) **FAIL_STRESS_TAIL**, so that the tilt outcome and broken gate are auditable.

The final stress report documents the most severe scenario losses, the dominant contributors to portfolio risk, and the key sources of vulnerability observed during the stress analysis.

This reporting ensures that portfolio decisions remain transparent and that the structural consequences of the chosen architecture are fully understood.