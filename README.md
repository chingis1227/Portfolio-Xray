# Portfolio X-Ray & Optimization Terminal

Portfolio X-Ray & Optimization Terminal, also described as Portfolio MRI, is a portfolio research and decision support system. Its purpose is not to output a single "perfect" allocation. Its purpose is to help an investor, advisor, or portfolio manager understand what is inside a portfolio, where hidden risk lives, how the portfolio behaves under stress, which alternative allocations are available, and what trade-offs come with changing the portfolio.

The product workflow is:

```text
Diagnose -> Generate candidates -> Stress-test -> Compare robustness -> Choose / explain
```

The current codebase is a Python portfolio optimization and reporting system. It builds optimized portfolio weights, runs portfolio analytics, stress diagnostics, robustness checks, benchmark portfolio variants, and exports CSV, JSON, HTML, TXT, and PDF-style report artifacts.

## Product Principle

This project is a decision system, not an automatic truth machine.

The user should be able to answer:

- What exactly is being analyzed?
- What are the client mandate, constraints, and assumptions?
- What does the portfolio actually hold by asset, class, currency, region, sector, and factor?
- Where does portfolio risk really come from?
- Which assets contribute disproportionately to risk or stress losses?
- How does the portfolio behave in historical and synthetic crises?
- Which candidate portfolios are available, and why does one look better than another?
- What trade-off is accepted when choosing a portfolio?
- What concrete rebalance action is implied, if any?
- When is the right answer to avoid trading?

The product concept comes from [Diagnostic Product Concept](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md), but that document is target product architecture, not a complete technical specification. If a metric, stress scenario, assumption, or module is mentioned there, it does not automatically replace the existing implementation. Current formulas, scenarios, constraints, policy logic, data rules, and output contracts remain governed by the canonical specs listed in this README and in [SPEC.md](SPEC.md).

## Target Users

- Private investors and HNWI who need an institutional-grade view of portfolio risk.
- Family offices and wealth managers who need explainable client reporting.
- Investment advisors who need repeatable portfolio diagnostics before client meetings.
- Sophisticated retail investors who already use tools such as Portfolio Visualizer, Koyfin, Excel, or Python and want deeper factor, stress, and robustness analysis.

## Current System Scope

Implemented today:

- Portfolio optimization through `run_optimization.py`.
- Portfolio reporting through `run_report.py`.
- Portfolio metrics across configured windows.
- Dynamic NaN-safe backtesting.
- Risk contribution diagnostics.
- Stress testing and stress commentary.
- Factor regression diagnostics, factor covariance analytics, portfolio PCA, macro regime diagnostics, regime analytics, and scenario libraries.
- Benchmark candidate portfolios: Equal Weight, Equal Weight by asset class, Risk Parity, Risk Budgeting, HRP, Minimum Variance, Maximum Diversification, Minimum CVaR, Robust Mean-Variance, and Scenario-Based Robust Optimization.
- ETF and stock taxonomy validation as annotation and diagnostics layers.

Product layers that are partially implemented or still TBD:

- Interactive "What Happens If?" simulator.
- Full Portfolio Comparison Arena UI.
- Formal Portfolio Health Score and Selection Engine scoring formula.
- Assumption Sensitivity dashboard.
- Regret Analysis.
- Decision Journal.
- Ongoing Monitoring / What Changed workflow.
- Tax-aware and turnover-aware workflows beyond the currently implemented rebalance and variant tooling.

## Investment Policy

The main portfolio construction policy is documented in [Portfolio Construction Policy](docs/specs/portfolio_construction_policy.md).

Current policy summary:

- The optimizer universe comes from the single ticker list in `config.yml`.
- Final production weights come from optimization plus approved post-processing protocols.
- Manual final weights in `config.yml` are not the normal workflow.
- The main optimizer maximizes expected return on the primary return window subject to practical constraints.
- Constraints include long-only weights, sum-to-one, minimum held weight when configured, max single-name caps when configured, liquidity floor, cash policy, and feasibility rules.
- `target_vol_annual` and `target_nominal_return_annual` are soft objective terms, not hard guarantees.
- ProLiquidity applies cash and liquidity policy after optimization.
- Historical mandate max drawdown can block weight release.
- RC_vol, stress testing, factor diagnostics, macro regime diagnostics, Kalman betas, PCA, and scenario analytics are diagnostic unless a spec explicitly says otherwise.
- Benchmark portfolio scripts are comparison tools; they do not replace `run_optimization.py` as the main policy optimizer.

## Main Pipeline

### 1. Optimization

```bash
python run_optimization.py
```

Useful options:

```bash
python run_optimization.py --no-cache
python run_optimization.py --write-config
python run_optimization.py --config PATH
python run_optimization.py --profile NAME
python run_optimization.py --no-report
```

This command reads `config.yml`, applies a client profile when configured, loads market data, builds expected return and covariance inputs, runs the optimizer, applies ProLiquidity, runs release checks, and writes optimized weights and run metadata under `output_dir_final`, usually `Main portfolio/`.

If the mandate max drawdown gate fails, production weights are not released.

### 2. Report

```bash
python run_report.py
```

Useful options:

```bash
python run_report.py --no-cache
python run_report.py --clear-cache
python run_report.py --backtest-mode dynamic_nan_safe
```

This command reads optimized weights, computes metrics, diagnostics, stress reports, scenario libraries, commentary, snapshots, and report artifacts. CSV outputs are usually written under `results_csv/`; portfolio-level outputs are usually written under `Main portfolio/`.

### 3. Standard Order

Run the main production flow in this order:

```bash
python run_optimization.py
python run_report.py
```

## Candidate Portfolio Factory

Candidate portfolios are alternative hypotheses, not automatic final answers. They allow the system to compare different construction philosophies under the same reporting and stress framework.

Common candidate commands:

```bash
python run_equal_weight.py
python run_equal_weight_by_asset_class.py
python run_risk_parity.py
python run_risk_budget_by_asset_class.py
python run_risk_budget_by_asset.py
python run_hierarchical_risk_parity.py
python run_minimum_variance.py
python run_minimum_variance_uncapped.py
python run_minimum_variance_advanced.py
python run_maximum_diversification.py
python run_maximum_diversification_unconstrained.py
python run_minimum_cvar_uncapped.py
python run_minimum_cvar_constrained.py
python run_robust_mv_lambda_calibration.py
python run_robust_mean_variance_uncapped.py
python run_robust_mean_variance_constrained.py
python run_robust_scenario_optimization.py
python run_robust_scenario_portfolio_report.py
```

Use these outputs for comparison, diagnostics, robustness analysis, and client explanation. Do not treat them as replacements for the main policy optimizer unless a future spec explicitly changes that rule.

## Conceptual Architecture

### Input & Assumptions Layer

Defines what is being analyzed:

- Universe of assets.
- Current weights when analyzing an existing portfolio.
- Investor currency.
- Benchmark.
- Risk profile.
- Investment horizon.
- Client mandate and constraints.
- Calculation assumptions such as data window, return frequency, covariance method, risk-free source, cash proxy, rebalance frequency, and missing-data policy.

Current source files include `config.yml`, `config.yml.example`, `config/client_profiles.yml`, `assets.yml`, and validation logic in `src/config_schema.py`.

### Portfolio X-Ray / Diagnostics Layer

Shows what is inside the portfolio before changing it:

- Asset allocation.
- Portfolio return and risk metrics.
- Risk contribution.
- Factor exposure.
- Hidden concentration and hedge-gap diagnostics.
- Drawdown, volatility, beta, Sharpe, Sortino, VaR/ES where implemented.
- Portfolio commentary and report snapshots.

Current source areas include `src/metrics_asset.py`, `src/metrics_portfolio.py`, `src/risk_contrib.py`, `src/portfolio_analytics.py`, `src/portfolio_commentary.py`, and `src/snapshot.py`.

### Stress Test Lab

Tests how the portfolio behaves in adverse environments:

- Historical stress episodes.
- Synthetic shocks.
- Scenario Library.
- Stress contribution by asset and factor.
- Hedge gap and stress commentary.
- Diagnostic stress analytics for candidate portfolios.

Current source areas include `src/stress.py`, `src/stress_factors.py`, `src/stress_covariance_taxonomy.py`, `src/stress_scenario_analytics.py`, `src/scenario_library.py`, and `src/scenario_library_normalized.py`.

### Macro And Regime Diagnostics

Adds market context without replacing the optimizer:

- Current macro regime diagnostics.
- Growth and inflation axes.
- Regime-specific factor analytics.
- Regime portfolio metrics.
- Confidence and coverage warnings.

Current source areas include `src/stress_factors_macro.py`, `src/data_macro_sources.py`, `src/regime_factor_analytics.py`, and `src/regime_portfolio_metrics.py`.

### Comparison, Selection, And Action

The intended product layer compares candidates and explains trade-offs:

- Candidate comparison by return, risk, drawdown, CVaR, stress loss, risk contribution, turnover, and mandate fit.
- Robustness scorecards.
- Pareto and dominance checks.
- Regret analysis.
- Trade-off explanation.
- Rebalance recommendations.
- No-trade recommendation when improvement is too small for the required turnover.

Some comparison and rebalance functionality exists today through scripts such as `run_compare_variants.py`, `run_compare_ew_rp.py`, `run_rebalance.py`, and `src/rebalance.py`. The full product-level Selection Engine and Decision Journal are TBD.

## Key Configuration Files

| File | Purpose |
| --- | --- |
| `config.yml` | Active local configuration: tickers, investor currency, benchmark, client profile, targets, windows, cash policy, return frequency, output paths, and feature settings. |
| `config.yml.example` | Reference configuration template. |
| `config/client_profiles.yml` | Client risk profile defaults such as target volatility, max drawdown, target return, liquidity floor, and optional minimum position size. |
| `config/etf_universe.yml` | ETF taxonomy source of truth for annotation and validation. It does not select the optimizer universe in V1. |
| `config/stock_universe.yml` | Stock taxonomy source of truth for current S&P 500 constituents. It is CLI-only in V1 and does not change optimizer or report membership. |
| `config/historical_stress_proxy_map.yml` | Historical stress fallback proxy map and coverage thresholds. |
| `assets.yml` | Optional asset metadata, including asset currency metadata. |

## Outputs

Generated outputs are not source files unless a task explicitly targets generated artifacts.

Common output locations:

- `Main portfolio/`
- `results_csv/`
- `output/`
- `cache/`
- `equal-weight portfolio/`
- `risk parity portfolio/`
- `minimum variance portfolio/`
- `maximum diversification portfolio/`
- `minimum cvar constrained portfolio/`
- `robust mean variance constrained portfolio/`
- `robust scenario portfolio/`

Common artifacts:

- `portfolio_weights.yml`
- `run_result.json`
- `stress_report.json`
- `scenario_library.json`
- `scenario_library_normalized.json`
- `commentary.txt`
- `stress_commentary.txt`
- CSV diagnostics under `results_csv/`
- HTML and PDF-style report artifacts where configured

## Repository Map

| Path | Purpose |
| --- | --- |
| `ARCHITECTURE.md` | Main architecture map: modules, flow, inputs, outputs, and boundaries. |
| `run_optimization.py` | Main policy optimization entry point. |
| `run_report.py` | Main report and diagnostics entry point. |
| `run_*.py` | Baseline, comparison, taxonomy, robust optimization, and utility entry points. |
| `src/optimization.py` | Main optimization logic and ProLiquidity-related behavior. |
| `src/portfolio_variants.py` | Baseline portfolio builders. |
| `src/metrics_*.py` | Asset, portfolio, and daily metrics. |
| `src/stress*.py` | Stress testing, factor diagnostics, covariance overlays, macro and scenario analytics. |
| `src/scenario_library*.py` | Scenario Library and normalized optimization-input view. |
| `src/robust_*.py` | Robust Mean-Variance and Scenario-Based Robust Optimization components. |
| `src/risk_*.py` | Risk contribution, risk parity, and risk budgeting components. |
| `docs/specs/` | Detailed behavior specs for metrics, policy, data, stress, reporting, taxonomy, and candidate portfolios. |
| `docs/exec_plans/` | Checked-in ExecPlans for larger changes and refactors. |
| `tests/` | Pytest coverage for behavior and regression checks. |

## Installation

```bash
pip install -r requirements.txt
```

Python dependencies include pandas, numpy, scipy, scikit-learn, yfinance, pandas-datareader, PyYAML / ruamel.yaml, matplotlib, and pytest.

## Verification

Run the full test suite:

```bash
python -m pytest
```

For focused changes, run the narrowest reliable pytest file first, then broaden when the change touches portfolio math, optimizer behavior, data alignment, config schema, stress logic, or report exports.

Documentation-only changes do not require tests unless they alter executable examples, commands, or documented behavior that should be verified.

## Documentation Sources Of Truth

Start with [RULES.md](RULES.md) for the high-level project rule map, then use [SPEC.md](SPEC.md) as the canonical implementation entry point.

| Area | Source |
| --- | --- |
| High-level project principles, boundaries, and source-of-truth map | [RULES.md](RULES.md) |
| Portfolio construction, optimizer behavior, ProLiquidity, mandate gate, RC_vol role | [Portfolio Construction Policy](docs/specs/portfolio_construction_policy.md) |
| Metric formulas, dates, windows, FX, covariance, RC_vol, beta, stress metrics | [Metrics Specification](docs/specs/metrics_specification.md) |
| Feasibility and weight constraints | [Feasibility Constraints](docs/specs/feasibility_constraints_spec.md) |
| Stress scenarios, diagnostics, failure and warning codes | [Stress Testing Spec](docs/specs/stress_testing_spec.md) |
| View After Optimization tactical tilt protocol | [View After Optimization Spec](docs/specs/view_after_optimization_spec.md) |
| NaN, young ETF, and backtest handling | [Data Policy](docs/specs/data_policy_spec.md) |
| Production workflow and release statuses | [Production Workflow](docs/specs/production_workflow.md) |
| Main architecture map | [Architecture](ARCHITECTURE.md) |
| Target product concept and product architecture | [Diagnostic Product Concept](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) |
| ETF taxonomy | [ETF Universe Spec](docs/specs/etf_universe_spec.md) |
| Stock taxonomy | [Stock Universe Spec](docs/specs/stock_universe_spec.md) |
| Large-change planning protocol | [PLANS.md](PLANS.md) and checked-in plans under [docs/exec_plans/](docs/exec_plans/) |
| Agent and contributor operating rules | [AGENTS.md](AGENTS.md) |

## Contributor Rules

- Do not invent formulas when a spec exists.
- Do not treat the Diagnostic product concept as an automatic change request for metrics, stress scenarios, configs, or code behavior.
- Keep final production weights generated by the optimizer or approved post-optimization protocols.
- Keep ETF and stock taxonomy annotation-only unless a future spec changes that behavior.
- Preserve diagnostic-only boundaries for RC_vol, stress analytics, macro regimes, Kalman betas, PCA, and scenario analytics unless a canonical spec explicitly changes them.
- Update documentation when behavior, interfaces, outputs, commands, or workflows change.
- For large changes, follow `PLANS.md` and maintain an ExecPlan under `docs/exec_plans/`.
- Prefer focused tests for focused changes and broader tests for shared math, optimizer, data, stress, or reporting changes.

## Roadmap / TBD

- Define the formal Portfolio Health Score formula.
- Define the Selection Engine scoring model and governance.
- Define Assumption Sensitivity outputs and thresholds.
- Define Regret Analysis methodology.
- Define interactive simulator requirements.
- Define Decision Journal schema.
- Define Monitoring / What Changed cadence and output contract.
- Decide which product-facing UI surfaces should be built first.
