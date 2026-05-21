# Optimization Engine Methodology Map (Block 5)

Date: 2026-05-20

Status: **Active input** - methodology map for Block 5 governance. Does not override canonical
specs or current code behavior.

Scope: Optimization Engine layer. This map separates current code, canonical specs, generated
artifact evidence, target product concept, and proposed methodology before any optimizer, objective,
constraint, estimator, fallback, or output contract is changed.

Related specs: [portfolio_construction_policy.md](../specs/portfolio_construction_policy.md),
[feasibility_constraints_spec.md](../specs/feasibility_constraints_spec.md),
[metrics_specification.md](../specs/metrics_specification.md),
[data_policy_spec.md](../specs/data_policy_spec.md),
[candidate_portfolios_spec.md](../specs/candidate_portfolios_spec.md),
[candidate_factory_spec.md](../specs/candidate_factory_spec.md),
[candidate_comparison_spec.md](../specs/candidate_comparison_spec.md),
[robust_mv_spec.md](../specs/robust_mv_spec.md),
[robust_scenario_optimization_spec.md](../specs/robust_scenario_optimization_spec.md),
[production_workflow.md](../specs/production_workflow.md).

Product concept (non-binding): [DIAGNOSTIC_PRODUCT_CONCEPT.md](../DIAGNOSTIC_PRODUCT_CONCEPT.md),
[PRODUCT.md](../../PRODUCT.md), [BUSINESS_VISION.md](../../BUSINESS_VISION.md).

## Provenance legend

| Code | Meaning |
| --- | --- |
| **C** | Existing code behavior |
| **S** | Existing canonical spec |
| **A** | Generated artifact evidence |
| **T** | Target product concept (not binding until specified and implemented) |
| **P** | **NEW METHODOLOGY PROPOSAL — requires spec decision before implementation** |

---

## 1. Executive summary

Block 5 answers:

**How are optimized portfolios built, what assumptions drive them, what constraints bind them, what
can fail, how robust are the weights, and can these optimized candidates be fairly tested,
compared, and explained?**

The current Optimization Engine is not one unified production allocator. It is a set of distinct
paths:

```text
Legacy policy path:
config.yml -> load_monthly_data_shared -> run_max_return_optimization
  -> ProLiquidity / cash policy -> mandate MaxDD release gate
  -> Main portfolio/run_result.json + portfolio_weights.yml when gate passes

Optimizer candidate path:
config.yml -> load_monthly_data_shared -> portfolio_variants.build_*
  -> fixed candidate weights -> run_portfolio_report_for_weights
  -> candidate folder weights/summary/metadata/snapshot/stress/X-Ray
  -> candidate_factory_run.json -> candidate_comparison.json

Robust scenario path:
Main portfolio/scenario_library_normalized.json + stress_report.json
  -> robust scenario optimizer -> robust scenario weights
  -> robust scenario portfolio report as a candidate
```

Current maturity:

| Area | State | Provenance |
| --- | --- | --- |
| Legacy policy optimizer | Implemented and still callable; compatibility path, not default portfolio-first starting point | **C** **S** |
| Candidate optimizer suite | Implemented as comparison candidates, not production policy | **C** **S** |
| Objective math in code | Mostly explicit in functions and metadata for MinVar, MaxDiv, CVaR, Robust MV, robust scenario | **C** **A** |
| Unified Block 5 owning spec | Missing; behavior spread across policy, metrics, data, candidate, robust specs | **P** |
| Expected return assumptions | Policy uses sample monthly mean; Robust MV uses James-Stein; MinVar/MaxDiv/CVaR do not optimize expected return | **C** **S** |
| Covariance assumptions | Sample ddof=1, optional Ledoit-Wolf, PSD repair, young ETF dual covariance in selected paths | **C** **S** |
| Feasibility/failure audit trail | Present but fragmented; builder `FAIL_*`, factory status, comparison availability, policy release status are separate | **C** **A** |
| Max Sharpe / drawdown-controlled / macro-resilient objectives | Not implemented; product concept only | **T** |
| Full reproducibility bundle per optimizer | Partial; metadata exists but not enough for a single audit-grade reproduction contract | **C** gap |

Block 5 has enough implemented math to be useful, but it is not yet audit-grade as a single
portfolio-construction layer. The main weak point is not missing optimizers; it is that optimizer
roles, inputs, constraints, parameter provenance, output contracts, and failure semantics are
distributed across scripts and artifacts.

---

## 2. Block 5 methodology map by sub-block

### 5.1 Optimization Role and Boundary

**User question:** What is the Optimization Engine responsible for, and when are optimized weights
production policy versus comparison candidates?

| Element | Current rule | Provenance |
| --- | --- | --- |
| Optimization Engine responsibility | Build weights from config universe, return panels, objectives, constraints, and selected risk/return estimators; disclose status and diagnostics | **C** |
| Legacy policy role | `run_optimization.py` is compatibility infrastructure. It can release `portfolio_weights.yml` only after mandate gate passes. | **C** **S** |
| Portfolio-first boundary | `run_portfolio_review.py` diagnoses `analysis_subject` first; default review does not call `run_optimization.py` unless a future accepted spec reactivates policy as candidate | **C** **S** |
| Candidate optimizer role | MinVar, MaxDiv, Min CVaR, Robust MV, robust scenario are comparison hypotheses; they do not overwrite policy weights or change mandate gates | **C** **S** |
| Candidate Factory boundary | Factory orchestrates scripts and freshness/status; it does not define formulas or silently modify optimizer logic | **C** **S** |
| Reporting/comparison boundary | Candidate weights become comparable only after report pipeline produces snapshot/stress/X-Ray/comparison fields | **C** **S** |
| Stress boundary | Stress diagnostics are non-binding except legacy policy MaxDD mandate check; scenario stress does not block candidate creation | **C** **S** |
| Taxonomy boundary | ETF/stock taxonomy annotates and buckets some candidates; it does not select the optimizer universe in V1 | **C** **S** |
| Manual weights boundary | Generated policy weights are not manual input; user-supplied current/model weights are allowed for diagnostics; post-optimization tilt only via View After Optimization | **S** |

**Production / candidate / legacy / target classification**

| Optimizer or construction path | Status | Why |
| --- | --- | --- |
| `run_max_return_optimization` inside `run_optimization.py` | Legacy production-compatible | Can write policy weights when `FAIL_MANDATE` is absent; not portfolio-first default |
| `objective_mode="risk_parity"` in `run_max_return_optimization` | Diagnostic/code-supported mode | Implemented in shared optimizer, but not the default policy objective |
| `minimum_variance_constrained` | Candidate-only production-quality baseline | Shared box bounds; full report after fixed weights |
| `minimum_variance_uncapped_long_only` | Candidate-only diagnostic baseline | Relaxed bounds reference |
| `minimum_variance_advanced_controls` | Candidate-only advanced diagnostic | Adds forced LW covariance, optional vol cap and L1 vs current |
| `maximum_diversification_constrained` | Candidate-only | Same box bounds as constrained MinVar |
| `maximum_diversification_unconstrained` | Candidate-only diagnostic | Long-only [0,1] reference |
| `minimum_cvar_constrained` | Candidate-only | LP under box bounds |
| `minimum_cvar_uncapped` | Candidate-only diagnostic | LP under [0,1] |
| `robust_mean_variance_constrained` | Candidate-only robust benchmark | Requires lambda resolution; not policy replacement |
| `robust_mean_variance_uncapped` | Candidate-only diagnostic robust benchmark | Relaxed bounds |
| `run_robust_mv_lambda_calibration.py` | Calibration tool, not candidate factory step | Writes lambda artifacts and optional selected portfolio bundle |
| `robust_scenario` | Candidate-only | Uses Main scenario/stress artifacts; no policy overwrite |
| Risk budgeting / risk parity / HRP | Candidate constructions with optimizer/algorithmic internals | Owned mainly by Block 4 but interact with Optimization Engine math |
| Max Sharpe | Target-only | No shipped `run_max_sharpe.py`; spec says deferred |
| Max Return under Risk Constraint | Covered by legacy policy concept only | No separate candidate id |
| Drawdown-controlled / macro-resilient | Target-only | No shipped objective |

**Input data used:** config universe, monthly return panel, cash proxy, target vol/return/drawdown,
min/max weights, young ETF policy, optional calibration files, scenario/stress artifacts.

**Frequency/window:** Main optimizer and candidate optimizers use monthly simple returns. Legacy
policy primary window defaults to `primary_window_months=120`, secondary robustness check defaults
to `secondary_window_months=60`. Candidate scripts use `cfg.windows_months[-1]` where the wrappers
pass the primary comparison window, usually 120 months.

**Implementing files/functions:** `run_optimization.py`, `src/optimization.py`,
`src/portfolio_variants.py`, `src/robust_mv.py`, `src/robust_mv_calibration.py`,
`src/robust_scenario_optimization.py`, candidate `run_*.py` wrappers.

**Owning spec:** Should be an explicit Block 5 spec. Today ownership is split across
`portfolio_construction_policy.md`, `candidate_portfolios_spec.md`, `robust_mv_spec.md`,
`robust_scenario_optimization_spec.md`, `feasibility_constraints_spec.md`, `production_workflow.md`.

**Generated artifact evidence:** `Main portfolio/run_result.json.status`,
`optimization_status`, `portfolio_weights.yml`; candidate folders `weights.json`,
`summary.json`, `baseline_weights_metadata.json`; `candidate_factory_run.json`;
`candidate_comparison.json`.

**User-visible outputs:** Main `portfolio_weights.yml`, `run_result.json`, candidate `weights.txt`,
`summary.txt`, `candidate_comparison.txt`, report sections, decision package.

**Limitations/risks:** Users can misread candidate optimizers as production recommendations; legacy
policy can be mistaken for portfolio-first default; target concept names can be mistaken for
implemented objectives.

**Could mislead:** Any row with a polished report but weak construction disclosure may look equally
defensible even if it is uncapped, diagnostic-only, stale, or built from fallback prerequisites.

**Tests:** `test_current_vs_policy_workflow.py`, `test_portfolio_review_workflow.py`,
`test_candidate_factory.py`, `test_candidate_comparison.py`, optimizer family tests listed below.

**Acceptance criteria:**

- Every optimizer row states role: production-compatible legacy, candidate-only, diagnostic-only,
  calibration-only, or target-only.
- Portfolio-first review never silently treats legacy policy as default subject.
- Any new optimizer or role change has a spec decision before code changes.

---

### 5.2 Optimization Inputs and Data Preparation

**User question:** What data enters optimization, at what frequency/window, and is it the same data
used later for reporting and comparison?

| Input/rule | Current behavior | Provenance |
| --- | --- | --- |
| Return panel | `load_monthly_data_shared` builds investor-currency monthly simple returns from adjusted close prices | **C** **S** |
| Frequency | Main metrics and optimizer inputs are monthly even if `returns_frequency` config is weekly/daily; non-monthly is disclosure metadata | **C** **S** |
| `analysis_end` | Last completed effective month-end; used by loader/report windows and legacy policy dual covariance call | **C** **S** |
| Window | Legacy policy primary: `primary_window_months` default 120; secondary robustness: 60; candidates: requested comparison window, usually 120 | **C** |
| Eligible universe | Config tickers present in returns; candidate variants filter by coverage threshold (default 0.90) over window | **C** **S** |
| Cash proxy | Excluded from risk optimizer universe; added after legacy policy optimization through ProLiquidity/cash policy | **C** **S** |
| Risk-free rate | Used in reporting metrics, not in current optimizer objectives except no Max Sharpe objective exists | **C** **S** |
| Benchmark | Used for metrics/stress/factor diagnostics; not a binding optimizer objective in shipped candidate optimizers | **C** **S** |
| FX | Prices converted to investor currency before returns | **C** **S** |
| Taxonomy | Annotation; used for risk-budget buckets and equal-weight-by-class; not a general optimizer filter | **C** **S** |
| Missing data | Generic covariance/corr/RC uses inner join; dynamic backtest uses NaN-safe rule; optimizer covariance may use young ETF dual covariance | **C** **S** |
| Young ETFs | Optional dual covariance and per-ticker caps for policy/constrained optimizer variants; fallback to full inner join if core unavailable | **C** **S** |

**Formulas/rules/parameters:**

- Monthly return: `P_t / P_{t-1} - 1`.
- Cov/corr/beta/RC alignment: inner join on required series.
- Coverage threshold: `cfg.coverage_threshold` default `0.90`.
- Policy minimum periods in `run_max_return_optimization`: at least calendar ~11 months, via
  `calendar_window_to_n_periods(11, returns_frequency)`.
- Candidate eligible universe: `_eligible_universe_from_returns` keeps tickers whose non-NaN
  coverage in the window meets threshold.
- Young ETF buckets: `eligible`, `candidate`, `new` from `young_etf_optimization_policy`.

**Source files/functions:** `src/data_loader.py::load_monthly_data_shared`,
`src/windows.py::slice_calendar_window` / `slice_window`, `src/portfolio_variants.py::_eligible_universe_from_returns`,
`src/young_etfs_dual_cov.py::build_dual_covariance_and_mu`, `src/optimization.py::get_risk_portfolio_tickers`.

**Owning spec:** `metrics_specification.md`, `data_policy_spec.md`,
`portfolio_construction_policy.md`, `candidate_portfolios_spec.md`.

**Generated artifact fields:** `run_result.json.analysis_setup`, `input_assumptions`,
`young_etf_dual_cov_enabled`, `young_etf_diagnostics`; `run_metadata.json`; candidate
`baseline_weights_metadata.json.eligible_universe`; `snapshot_index.json.analysis_end`;
`results_csv/inputs/monthly_returns.csv` when report pipeline exports it.

**Outputs the user sees:** Data policy disclosure, input assumptions, report metadata, candidate
comparison freshness/status, weights and diagnostics.

**Limitations/risks:**

- Candidate variant helper `_mv_covariance_for_eligible` calls dual covariance without explicitly
  passing `analysis_end`; this appears to depend on the already-truncated panel from the loader.
  NEW METHODOLOGY PROPOSAL — requires spec decision before implementation: make `analysis_end`
  explicit in every optimization estimator call.
- Risk-free and benchmark are visible in reports, but users may assume they influence optimization
  objectives such as Sharpe. They generally do not.
- Coverage filtering is not exposed uniformly in every optimizer summary row.

**Could mislead:** A young ETF cap or fallback covariance can materially affect weights while only
some artifacts make that obvious.

**Tests:** `test_returns_frequency.py`, `test_analysis_end_cutoff.py`, `test_young_etfs_dual_cov.py`,
`test_etf_universe.py`, optimizer family tests.

**Acceptance criteria:**

- Every optimizer artifact records `analysis_end`, `window_months`, universe before/after coverage,
  covariance method, and any young ETF fallback/caps.
- Optimizer and report artifacts agree on `analysis_end`.
- No optimizer uses raw incomplete current-period data.

---

### 5.3 Expected Return Estimation

**User question:** Are expected returns used, how are they estimated, and are the assumptions visible?

| Path/objective | Expected return usage | Estimator | Provenance |
| --- | --- | --- | --- |
| Legacy policy `max_return` | Directly maximizes `mu'w` with soft penalties | Sample mean of monthly simple returns over optimization window, or dual-cov `mu` non-NaN mean | **C** **S** |
| Legacy policy `risk_parity` mode | Not used in risk parity objective | N/A | **C** |
| Minimum Variance | Not used in objective | N/A | **C** |
| Maximum Diversification | Not used in objective | Asset vol from covariance only | **C** |
| Minimum CVaR | Uses realized monthly scenarios, not explicit expected-return vector | Scenario return matrix `R` | **C** |
| Robust MV | Directly uses expected returns | James-Stein shrinkage of monthly sample means toward cross-sectional grand mean | **C** **S** |
| Robust MV lambda calibration | Uses Robust MV weights, then evaluates realized/report metrics | James-Stein via Robust MV builder | **C** **S** |
| Robust scenario | Uses base scenario expected returns and scenario coefficients | `base_historical.expected_returns_by_asset` from normalized scenario library | **C** **S** |
| Max Sharpe | Not implemented | N/A | **T** |
| Drawdown/macro objective | Not implemented | N/A | **T** |

**Formulas/rules:**

- Legacy policy: minimize `-mu'w + soft_vol_penalty + soft_return_penalty + optional tracking`.
- Robust MV: `raw_mu_i = mean(r_i)`, shrink toward `mu_bar`; for `p >= 3`,
  `c = max(0, 1 - (p - 2) * psi / SS)`, `mu_JS_i = mu_bar + c * (raw_mu_i - mu_bar)`.
- Robust scenario: `mu_base` comes from `base_historical.expected_returns_by_asset`.

**Frequency/window:** Monthly simple returns. Legacy policy default 120M primary, 60M secondary
diagnostic; Robust MV candidate window usually 120M; scenario robust uses scenario library produced
by report from Main artifacts.

**Source files/functions:** `src/optimization.py::run_max_return_optimization`,
`src/young_etfs_dual_cov.py::build_dual_covariance_and_mu`,
`src/robust_mv.py::james_stein_shrink_means`,
`src/robust_scenario_optimization.py::build_robust_optimization_inputs`.

**Owning spec:** `portfolio_construction_policy.md`, `robust_mv_spec.md`,
`robust_scenario_optimization_spec.md`, `metrics_specification.md` expected return section.

**Generated artifact fields:** `run_result.json.optimization_status` only says objective mode, not
mu values; Robust MV `baseline_weights_metadata.json.raw_mu`, `shrunk_mu`,
`shrinkage_target`, `shrinkage_intensity`; robust scenario
`robust_optimization_v1_summary.json.base_expected_return_monthly`.

**Outputs the user sees:** Robust MV metadata and text include lambda/objective/covariance; legacy
policy output does not expose the full expected-return vector in a compact optimizer-specific JSON.

**Limitations/risks:**

- Legacy policy expected return is unstable historical sample mean, yet it drives production-compatible
  weights. Soft target penalties reduce but do not remove this risk.
- Expected-return vector for legacy policy is not disclosed as clearly as Robust MV.
- Robust MV makes expected-return assumptions visible, but lambda can dominate interpretation.

**Could mislead:** Users may interpret optimized return as forecast quality rather than historical
sample assumption. Candidate comparison can show performance metrics without showing the mu vector
that created weights.

**Tests:** `test_optimization_fallback.py`, `test_robust_mu_optimization.py`,
`test_robust_mean_variance.py`, `test_robust_scenario_optimization.py`.

**Acceptance criteria:**

- Every return-aware optimizer artifact records expected-return source, window, vector or digest,
  shrinkage method, and whether expected returns were used in the objective.
- Non-return objectives explicitly state "expected returns not used".

---

### 5.4 Covariance / Risk Model Estimation

**User question:** What risk model drives weights, and what happens when covariance is weak,
singular, young, or unstable?

| Estimator/path | Method | Provenance |
| --- | --- | --- |
| Sample covariance | Monthly simple returns, inner join, `ddof=1` | **C** **S** |
| Optional Ledoit-Wolf in generic covariance | `covariance_shrinkage: true` uses Ledoit-Wolf in covariance helpers | **C** **S** |
| Young ETF dual covariance | Core eligible sample/LW/MCD option, pairwise overlaps for short-history assets shrunk to pooled core median, PSD repair | **C** **S** |
| Minimum Variance / MaxDiv / CVaR covariance | `_mv_covariance_for_eligible`; sample/LW/young dual; PSD repair | **C** |
| Advanced MinVar covariance | Forced Ledoit-Wolf monthly covariance, regardless of `covariance_shrinkage` | **C** |
| Robust MV covariance | Ledoit-Wolf or OAS sklearn covariance; PSD status/repair recorded | **C** **S** |
| Robust scenario covariance | `base_historical.asset_covariance_monthly_equivalent` from normalized scenario library; PSD repair | **C** **S** |
| Factor covariance | Diagnostic, not optimizer input for shipped optimizers | **C** **S** |
| Robust covariance / MCD | Supported as young dual core option in helper, not production default | **C** |
| Scenario covariance | Used by robust scenario summary/regularization, not policy covariance | **C** |

**Formulas/rules/parameters:**

- `cov_matrix_returns(ret, ddof=1, use_shrinkage=...)`.
- PSD repair via eigenvalue clipping/repair in `src.risk_parity_spinu.repair_covariance_psd` or
  young ETF helper.
- Young ETF caps for `candidate` and `new` buckets via `per_ticker_young_weight_caps`.
- Robust MV `robust_mv_covariance_method`: `ledoit_wolf` or `oas`.

**Frequency/window:** Monthly. Optimizer window is usually 120M for construction. Advanced MinVar
uses same window but forced LW. Robust scenario uses Main scenario library scope.

**Source files/functions:** `src.risk_contrib.cov_matrix_returns`,
`src.risk_contrib.cov_matrix_monthly`, `src.young_etfs_dual_cov.build_dual_covariance_and_mu`,
`src.portfolio_variants._mv_covariance_for_eligible`, `src.robust_mv.shrunk_covariance_monthly`,
`src.robust_scenario_optimization._nested_cov_to_sigma`.

**Owning spec:** `metrics_specification.md`, `data_policy_spec.md`, `robust_mv_spec.md`,
`robust_scenario_optimization_spec.md`.

**Generated artifact fields:** candidate `baseline_weights_metadata.json.covariance_method`,
`shrinkage_used`, `psd_repair_used`, `young_etf_dual_mode`; Robust MV `psd_status`,
`covariance_shrinkage_sklearn`; `run_result.json.young_etf_diagnostics`.

**Outputs the user sees:** Mostly in metadata JSON and some weights text. Main report exposes
covariance/correlation diagnostics but not always optimizer-specific risk model detail.

**Limitations/risks:**

- Singular/unstable covariance may be repaired and then produce plausible weights; repair status is
  metadata, not always surfaced in human summary.
- Young ETF dual covariance avoids truncating history, but can create model risk if user ignores
  bucket/cap diagnostics.
- Covariance method is not consistently pulled into `candidate_comparison.json` rows for all
  optimizers.

**Could mislead:** A candidate may look better because it used a different covariance estimator or
relaxed bounds, not because its objective is intrinsically superior.

**Tests:** `test_young_etfs_dual_cov.py`, `test_factor_covariance.py` (diagnostic),
`test_minimum_variance_baseline.py`, `test_maximum_diversification_baseline.py`,
`test_minimum_cvar_baseline.py`, `test_robust_mean_variance.py`.

**Acceptance criteria:**

- Every optimizer records covariance estimator, ddof/shrinkage/PSD repair, window, aligned rows, and
  young ETF mode/caps.
- Comparison disclosure distinguishes estimator differences before ranking candidate quality.

---

### 5.5 Objective Functions

**User question:** What exactly is minimized or maximized, by which solver, and can it fail?

#### Objective audit table

| Objective | Mathematical objective | Uses | Solver/formulation | Status | Provenance |
| --- | --- | --- | --- | --- | --- |
| Legacy max return | Minimize `-mu'w + lambda_vol*(sigma_ann-target_vol)^2 + lambda_ret*(ret_ann-target_ret)^2 + optional tracking` | Sample/dual `mu`, covariance for soft vol | SLSQP with box + sum=1; L-BFGS-B feasibility start; fallback feasible point | Implemented legacy production-compatible | **C** **S** |
| Legacy risk parity mode | Spinu CCD on `0.5*x'Sigma*x - (1/N) sum log(x_i)`, else SLSQP squared RC deviation | Covariance, RC | Spinu CCD + SLSQP fallback | Implemented diagnostic mode | **C** |
| Minimum Variance | Minimize `0.5*w'Sigma*w` | Covariance | SLSQP with analytic gradient `Sigma w` | Implemented candidate | **C** **S** |
| Maximum Diversification | Maximize `(sigma'w)/sqrt(w'Sigma*w)` by minimizing negative DR | Covariance diagonal vol + covariance | SLSQP with analytic gradient, then fallback | Implemented candidate | **C** **S** |
| Minimum CVaR | Rockafellar-Uryasev LP: minimize `alpha + 1/(T*(1-gamma))*sum(z_t)` subject to `z_t >= -(R_t w)-alpha`, `z_t>=0` | Monthly scenario returns | `scipy.optimize.linprog(method="highs")` | Implemented candidate | **C** |
| Robust MV | Minimize `lambda*w'Sigma*w - mu_JS'w` | James-Stein mu, LW/OAS covariance | SLSQP with analytic gradient | Implemented candidate | **C** **S** |
| Robust scenario lower-half mean | Minimize negative mean of worst ceil(N/2) scenario returns plus vol/stress/HHI penalties | Scenario coefficient matrix, base Sigma/mu | SLSQP multi-start | Implemented candidate | **C** **S** |
| Robust scenario maximin | Minimize negative minimum scenario return | Scenario returns | SLSQP multi-start | Implemented candidate objective mode | **C** **S** |
| Robust scenario hybrid legacy | Minimize `-mu_base'w + lambda_vol*sigma + stress penalty + hhi` | Base mu/Sigma, stress returns | SLSQP multi-start | Implemented objective mode | **C** **S** |
| Max Sharpe | N/A | Would use rf/excess return | N/A | Target-only/deferred | **T** |
| Max Return under Risk Constraint | Covered by legacy policy concept, no separate candidate | Would need hard risk constraint | N/A | Not separate candidate | **T** **S** |
| Drawdown-controlled | N/A | Would use drawdown path/loss constraints | N/A | Target-only | **T** |
| Macro-resilient | N/A | Would use macro/regime diagnostics | N/A | Target-only | **T** |

**Convexity/heuristic notes:**

- Minimum Variance with PSD covariance and linear constraints is convex.
- Minimum CVaR LP is convex.
- Robust MV is convex if covariance PSD and lambda non-negative.
- Maximum Diversification is generally non-convex; implementation uses SLSQP heuristic.
- Legacy max return plus squared soft vol/return penalties can be non-convex because annualized
  vol includes square root; implementation is SLSQP heuristic.
- Robust scenario lower-half/maximin/hybrid are heuristic SLSQP formulations.
- Risk parity Spinu core is convex in transformed positive variables; bounds are handled by
  post-check/fallback rather than native box constraints in the Spinu branch.

**What can fail:**

- No eligible assets, insufficient aligned rows, infeasible bounds, unsupported config, non-finite
  covariance/weights, SLSQP/linprog failure, missing scenario artifacts, missing Robust MV lambda.

**Source files/functions:** `src/optimization.py::run_max_return_optimization`,
`src/portfolio_variants.py::_minimum_variance_slsqp`, `_maximum_diversification_slsqp`,
`_minimum_cvar_linprog`, `_build_robust_mean_variance_core`,
`src/robust_mv.py::solve_robust_mean_variance`,
`src/robust_scenario_optimization.py::robust_objective_loss`.

**Owning spec:** Current partial specs. NEW METHODOLOGY PROPOSAL — requires spec decision before
implementation: create a future Optimization Engine layer spec as the single objective and
optimizer provenance map.

**Generated artifact fields:** `baseline_weights_metadata.json.objective`,
`objective_minimize`, `solver`, `solver_success`, `solver_message`, `objective_value`,
`cvar_objective_value`, `empirical_cvar_loss`, `diversification_ratio`;
`run_result.json.optimization_status`; robust scenario `robust_optimization_v1_summary.json`.

**Outputs the user sees:** Weights text/JSON, summaries, candidate comparison; objective details are
mostly JSON/metadata, not always front-and-center in human summaries.

**Could mislead:** Comparing heuristic objectives and convex objectives without showing solver
status/objective/bounds can make them look equally certain.

**Tests:** `test_optimization_fallback.py`, `test_minimum_variance_baseline.py`,
`test_maximum_diversification_baseline.py`, `test_minimum_cvar_baseline.py`,
`test_robust_mean_variance.py`, `test_robust_scenario_optimization.py`,
`test_risk_parity_spinu.py`, `test_risk_budgeting.py`.

**Acceptance criteria:**

- Every objective has a canonical formula, solver, convexity/heuristic status, input estimator, and
  failure status list.
- Any objective not in this table is marked target-only or proposal before implementation.

---

### 5.6 Constraints and Mandate Rules

**User question:** Which limits bind the optimizer, which are only diagnostics, and how are
infeasible limits handled?

| Constraint/rule | Binding where? | Current implementation | Provenance |
| --- | --- | --- | --- |
| Long-only | All shipped optimizers | Bounds non-negative; no short selling despite config flags | **C** **S** |
| Fully invested risk sleeve | All optimizer/candidate weight builders | `sum(w)=1` for risk candidate universe | **C** |
| Min single weight | Policy and constrained candidates | `_build_bounds`; default `MIN_WEIGHT_DEFAULT=0.01` if config absent/zero | **C** |
| Max single weight | Policy and constrained candidates | min(feasibility cap, `max_single_security_weight_pct`, young cap) | **C** **S** |
| Feasibility cap by N | Policy and constrained candidates | `resolve_max_weight_per_asset_cap(N)` | **C** **S** |
| Young ETF per-ticker cap | Policy and constrained candidates where dual enabled | Candidate/new buckets capped, default 2% | **C** **S** |
| Cash / liquidity floor | Legacy policy only | ProLiquidity after risk weights; candidate scripts do not apply it | **C** **S** |
| Vol-scaling cash | Legacy policy cash policy | Cash weight can rise when current vol exceeds target | **C** **S** |
| Cash prohibited alpha shift | Legacy policy only | Shift away from top RC donors toward low-vol/VOO/VT/VTI heuristic | **C** **S** |
| Target volatility | Legacy policy soft penalty; advanced MinVar optional hard cap | Policy: soft objective; advanced MinVar: inequality `w'Sigma w <= target_vol^2/12` | **C** |
| Target nominal return | Legacy policy soft penalty | Soft squared penalty; not hard constraint | **C** **S** |
| Target max drawdown | Legacy policy release gate; robust lambda calibration evaluation | Does not enter policy objective; blocks weight write if failed | **C** **S** |
| Max CVaR | Not implemented as mandate constraint | CVaR objective exists, but no max-CVaR gate | **C** gap / **T** |
| Beta limits | Not optimizer constraints | Diagnostic only | **C** **S** |
| Turnover limit | Advanced MinVar optional L1 penalty vs current; no hard turnover cap | Candidate-only | **C** |
| Asset-class limits | Not general optimizer constraints | Risk budgeting uses taxonomy targets; no global class cap | **C** gap / **T** |
| Liquidity/security tradability floor | Only cash floor; no per-asset liquidity screen | Target concept only | **T** |
| Stress diagnostics | Not binding except policy MaxDD mandate and Robust MV calibration optional checks | Scenario stress statuses are diagnostic-only | **C** **S** |

**Feasibility formula:** `resolve_max_weight_per_asset_cap(N)`:

```text
N <= 0: 0
N <= 3: 0.40
else: min(0.25, max(0.10, 2.5 / N))
```

Feasible box requires `sum(lower_bounds) <= 1 <= sum(upper_bounds)`.

**Source files/functions:** `policy_math/feasibility.py`,
`src/optimization.py::_build_bounds`, `src/optimization.py::proliquidity`,
`src/optimization.py::_alpha_shift_to_target_vol`, `src/portfolio_variants.py::_budget_simplex_intersects_box`,
`src.metrics_asset.mandate_max_drawdown_full_history_check`.

**Owning spec:** `feasibility_constraints_spec.md`, `portfolio_construction_policy.md`,
`production_workflow.md`, `view_after_optimization_spec.md`.

**Generated artifact fields:** `run_result.json.violations`, `mandate_check`,
`stress_summary`, `weights`; candidate metadata `bounds_used`, `active_constraints`,
`binding_constraints`, `constraint_summary`, `volatility_constraint_feasible`.

**Outputs the user sees:** Main run status `APPROVED`, `OK_FALLBACK`, `FAIL_MANDATE`; candidate
summary status; weights text may include client-fit line after report.

**Limitations/risks:**

- Candidate reports may display "Client-fit" after report diagnostics, but construction did not use
  ProLiquidity or release gates.
- Vol target is soft in policy, hard only in advanced MinVar; this difference can mislead.
- Asset-class/beta/turnover constraints are mostly not binding despite product concept language.

**Tests:** `test_config_weights_sync.py`, `test_stress_mandate_pass.py`,
`test_minimum_variance_baseline.py`, `test_maximum_diversification_baseline.py`,
`test_minimum_cvar_baseline.py`, `test_robust_mv_calibration.py`.

**Acceptance criteria:**

- Artifacts separate "optimizer constraints" from "post-optimization release checks" and
  "diagnostic-only warnings".
- Infeasible bounds fail closed with zero weights and explicit reason.

---

### 5.7 Feasibility and Failure Handling

**User question:** What statuses can occur, how are reasons detected, and can failures silently
produce misleading weights?

#### Current status taxonomy

| Layer | Status/reason | Meaning | Provenance |
| --- | --- | --- | --- |
| Shared optimizer | `OK` | SLSQP/Spinu solved without fallback | **C** |
| Shared optimizer | `OK_FALLBACK` | Feasible fallback branch used in policy optimizer | **C** **S** |
| Shared optimizer | `FAIL_DATA:*` | Missing/insufficient return/cov data | **C** |
| Candidate builder | `OK` | Weights valid and solver quality acceptable | **C** |
| Candidate builder | `APPROXIMATE` | Sum/bounds valid but fallback/non-success/approx solver path | **C** |
| Candidate builder | `FAIL_CONFIG` | Unsupported/missing config, e.g. Robust MV lambda unset or bad covariance method | **C** |
| Candidate builder | `FAIL_DATA` | Insufficient synchronous rows or setup failed | **C** |
| Candidate builder | `FAIL_INFEASIBLE_UNIVERSE` | Fewer than 2 eligible assets | **C** |
| Candidate builder | `FAIL_INFEASIBLE_TARGETS` | Risk budget target cannot be matched to eligible assets | **C** |
| Candidate builder | `FAIL_INFEASIBLE_BOUNDS` | Box does not intersect full-investment simplex | **C** |
| Candidate builder | `FAIL_INFEASIBLE_VOL_TARGET` | Advanced MinVar vol cap below minimum achievable variance | **C** |
| Candidate builder | `FAIL_NUMERICAL` | Non-finite weights, solver failure, LP failure | **C** |
| Policy release | `APPROVED` | Weights written | **C** **S** |
| Policy release | `FAIL_MANDATE` | MaxDD mandate failed or not evaluable; weights not written | **C** **S** |
| Factory | `succeeded`, `failed`, `skipped_existing`, `skipped_dependency`, `resumed_from_manifest` | Orchestration status | **C** **S** |
| Comparison row | `available`, `degraded`, `unavailable` | Artifact readiness status | **C** **S** |

**Failure propagation:**

- Candidate script failure usually writes `summary.json` with `status` and `reason`.
- Candidate factory maps `FAIL_*` builder status to `reason_code` such as
  `builder_fail_config`, `builder_infeasible_bounds`, `builder_fail_numerical`.
- Comparison marks stale/missing/incomplete candidates `unavailable` or `degraded`.
- Policy `FAIL_MANDATE` writes `run_result.json` but does not write `portfolio_weights.yml`.

**Source files/functions:** `src/portfolio_variants.py::BaselineWeightsResult`,
`src/candidate_factory.py::factory_reason_from_builder_summary`,
`src/candidate_comparison.py::_evaluate_artifact_candidate`,
`run_optimization.py`.

**Owning spec:** `production_workflow.md`, `candidate_factory_spec.md`,
`candidate_comparison_spec.md`. Block 5 failure taxonomy should be spec-owned explicitly. **P**

**Generated artifact fields:** `summary.json.status`, `summary.json.reason`,
`candidate_factory_run.json.steps[].status`, `reason_code`, `message`,
`candidate_comparison.json.candidates[].status`, `unavailable_reason`,
`run_result.json.status`, `violations`.

**Outputs the user sees:** CLI exit codes/logs, summary text, comparison availability, decision
package skips unavailable rows.

**Limitations/risks:**

- `APPROXIMATE` can still generate a full candidate report; user may not notice solver fallback.
- Some policy optimizer fallback weights may be normalized feasible points, not optimizer optima.
- `run_robust_scenario_optimization` records `optimizer_message` but does not expose a formal
  success boolean/status in summary.

**Could mislead:** A full report folder can exist for an approximate solve and appear equally final
unless the metadata/status is surfaced.

**Tests:** `test_candidate_factory.py`, `test_candidate_comparison.py`,
`test_optimization_fallback.py`, `test_minimum_variance_baseline.py`,
`test_minimum_cvar_baseline.py`, `test_robust_mean_variance.py`.

**Acceptance criteria:**

- No failed optimizer produces non-zero weights labeled as `OK`.
- Approximate/fallback solutions remain visible through factory and comparison.
- Every failure reason survives into the highest-level artifact used by comparison or operation.

---

### 5.8 Optimizer Variants

**User question:** For every implemented optimizer path, what exactly constructs weights?

#### Variant matrix

| Variant | Construction logic | Inputs | Constraints | Solver | Artifacts | Tests | Mode |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Legacy main policy optimizer | Max sample monthly `mu'w` with soft vol/return penalties; ProLiquidity after risk weights; MaxDD gate before write | Monthly returns, target vol/return, cash policy, bounds, young policy | Sum=1, long-only, min/max/young caps; cash overlay after | SLSQP + fallback | `Main portfolio/run_result.json`, `portfolio_weights.yml`, `run_metadata.json` | `test_optimization_fallback.py`, workflow tests | Legacy production-compatible |
| Minimum variance constrained | Min `0.5*w'Sigma*w` | Eligible monthly returns, Sigma | Sum=1, `_build_bounds` | SLSQP | `minimum variance portfolio/*` | `test_minimum_variance_baseline.py` | Full menu candidate |
| Minimum variance uncapped | Same objective | Eligible monthly returns, Sigma | Sum=1, `[0,1]` | SLSQP | `minimum variance uncapped portfolio/*` | `test_minimum_variance_baseline.py` | Full menu diagnostic |
| Minimum variance advanced | Min variance; forced LW; optional hard vol cap; optional L1 vs current | Monthly returns, cfg current weights, target vol | Sum=1, `_build_bounds`, optional `w'Sigma w <= target^2/12`, optional L1 slack | SLSQP extended variables / fallback | `minimum variance advanced portfolio/*` | `test_minimum_variance_baseline.py` | Full menu advanced diagnostic |
| Maximum diversification constrained | Max diversification ratio | Monthly Sigma | Sum=1, `_build_bounds` | SLSQP | `maximum diversification portfolio/*` | `test_maximum_diversification_baseline.py` | Full menu candidate |
| Maximum diversification unconstrained | Same DR objective | Monthly Sigma | Sum=1, `[0,1]` | SLSQP | `maximum diversification unconstrained portfolio/*` | `test_maximum_diversification_baseline.py` | Full menu diagnostic |
| Minimum CVaR constrained | LP sample CVaR of monthly losses | Monthly scenario return matrix | Sum=1, `_build_bounds`, RU `z` constraints | HiGHS linprog | `minimum cvar constrained portfolio/*` | `test_minimum_cvar_baseline.py` | Full menu candidate |
| Minimum CVaR uncapped | Same LP | Monthly scenario returns | Sum=1, `[0,1]` | HiGHS linprog | `minimum cvar uncapped portfolio/*` | `test_minimum_cvar_baseline.py` | Full menu diagnostic |
| Robust MV constrained | Min `lambda*w'Sigma*w - mu_JS'w` | James-Stein mu, LW/OAS Sigma, lambda | Sum=1, `_build_bounds`, young caps | SLSQP | `robust mean variance constrained portfolio/*` | `test_robust_mean_variance.py` | Full menu robust candidate |
| Robust MV uncapped | Same | James-Stein mu, LW/OAS Sigma, lambda | Sum=1, `[0,1]` | SLSQP | `robust mean variance uncapped portfolio/*` | `test_robust_mean_variance.py` | Full menu robust diagnostic |
| Robust MV lambda calibration | Grid-search lambda, build constrained Robust MV, report metrics/stress, choose feasible/borderline lambda | Monthly returns, mandate targets, optional calibration YAML | Evaluation constraints: MaxDD, target vol, max weight, optional synthetic RC caps | Repeated Robust MV + report pipeline | `analysis_robust_mv_lambda_calibration/*` | `test_robust_mv_calibration.py` | Prerequisite/tool |
| Scenario-based robust optimization | SLSQP on scenario objective modes | Main normalized scenarios + stress report betas | Sum=1, `_build_bounds` without young caps | SLSQP multi-start | `robust_optimization_*`, `robust scenario portfolio/*` | `test_robust_scenario_optimization.py` | Full menu robust candidate |
| Risk parity | Equalize variance contributions | Monthly Sigma | Sum=1, long-only; candidate baseline no policy boxes | Spinu CCD + SLSQP fallback | `risk parity portfolio/*` | `test_risk_parity_baseline.py`, `test_risk_parity_spinu.py` | Core menu benchmark |
| Risk budget by asset/class | Match target percentage variance contributions | Monthly Sigma, taxonomy/budget config | Long-only, sum=1; budget targets | Spinu/SLSQP | risk budget folders | `test_risk_budgeting.py` | Core menu benchmark |
| HRP | Cluster correlation distance, recursive bisection | Monthly Sigma | Long-only normalized; no box projection | Hierarchical algorithm | `hierarchical risk parity portfolio/*` | `test_hrp_weights.py` | Core menu benchmark |

**MVP core vs full:** Core review profile runs benchmarks/risk budgets/HRP. Classic and robust
optimizers are in `default_v1` full menu, not `core_v1`.

**Failure modes:** As in 5.7, plus scenario missing dependencies (`skipped_dependency`) and Robust
MV missing lambda (`FAIL_CONFIG`).

**Limitations/risks:**

- The term "unconstrained" means no project caps, but still long-only and sum=1.
- "Advanced" MinVar is not the primary constrained minimum-variance answer.
- Robust MV constrained depends on lambda calibration readiness, but factory does not run
  calibration automatically.

**Acceptance criteria:**

- Every script-backed optimizer writes `weights.json`, `summary.json`,
  `baseline_weights_metadata.json` (or equivalent robust scenario summary), and report artifacts
  when build succeeds.
- Every optimizer-backed candidate is represented in `candidate_comparison.json` as available,
  degraded, or unavailable with construction disclosure.

---

### 5.9 Robust / Scenario-Aware Optimization

**User question:** How is uncertainty represented, how is lambda selected, and does robust
optimization change production policy weights?

| Topic | Current behavior | Provenance |
| --- | --- | --- |
| Robust MV uncertainty | Shrink expected returns and covariance; lambda penalizes monthly variance | **C** **S** |
| Robust MV lambda | Calibration file `analysis_robust_mv_lambda_calibration/selected_lambda.txt` or CLI override; YAML lambda not read by baseline CLIs | **C** **S** |
| Lambda grid | Primary `(0.1,0.2,0.3,0.5,0.8,1.0)`, extended `(1.5,2,3,5,7.5,10)` if needed | **C** |
| Lambda selection | Lowest feasible/borderline lambda in the phase, tie-break highest 10Y CAGR; if none, least-bad diagnostic | **C** |
| Scenario robust uncertainty | Normalized scenario library coefficients; historical/synthetic stress scenario returns; base covariance regularizer | **C** **S** |
| Scenario objectives | `lower_half_mean`, `maximin`, `hybrid_legacy` | **C** **S** |
| Scenario artifacts required | Main `scenario_library_normalized.json` and `stress_report.json` | **C** **S** |
| Asset betas | Prefer `stress_report.asset_factor_betas`; fallback may replicate portfolio betas and warn | **C** **S** |
| Production boundary | Robust MV and robust scenario create candidates only; no policy weight overwrite | **C** **S** |

**Robust penalty formulas:**

- Robust MV: `lambda*w'Sigma*w - mu_JS'w`.
- Robust scenario lower-half default: `-lower_half_mean(Cw) + lambda_vol*sigma_base
  + lambda_stress*confidence_weight*max(0,-scenario_return) + lambda_hhi*sum(w_i^2)`.
- Maximin: `-min(Cw)`.
- Hybrid legacy: `-mu_base'w + lambda_vol*sigma + stress penalty + HHI`.

**Source files/functions:** `src.robust_mv.py`, `src.robust_mv_calibration.py`,
`run_robust_mv_lambda_calibration.py`, `src.robust_scenario_optimization.py`,
`run_robust_scenario_optimization.py`, `run_robust_scenario_portfolio_report.py`.

**Owning spec:** `robust_mv_spec.md`, `robust_scenario_optimization_spec.md`,
`candidate_factory_spec.md` for prerequisites/disclosure.

**Generated artifact fields:** Robust MV metadata `raw_mu`, `shrunk_mu`, `robust_mv_lambda`,
`objective_value`, `psd_status`; calibration summary `feasible_lambda_found`,
`selected_lambda`, `failed_constraints_by_grid`, `no_feasible_lambda_diagnostic`;
robust scenario summary `objective_mode`, `lambdas`, `lower_half_mean`,
`sorted_scenario_returns_at_optimum`, `beta_load_warnings`.

**Outputs the user sees:** Robust candidate folders and comparison rows. Lambda calibration outputs
are separate and must be run/read by operator.

**Limitations/risks:**

- Robust does not mean guaranteed; it is model-dependent shrinkage/scenario scoring.
- Robust scenario uses Main/policy stress artifacts, not per-candidate stress artifacts, to build
  weights.
- Scenario objective modes are heuristic and penalty weights are config/tool assumptions.
- Lambda calibration evaluates mandate-like checks but does not change policy mandate gates.

**Could mislead:** A robust candidate can be interpreted as production-ready because it includes
stress-aware language; current spec says it is comparison-only.

**Tests:** `test_robust_mean_variance.py`, `test_robust_mv_calibration.py`,
`test_robust_mu_optimization.py`, `test_robust_scenario_optimization.py`,
`test_candidate_factory.py` robust dependency checks.

**Acceptance criteria:**

- Robust candidate comparison row discloses lambda source/readiness and scenario artifact
  prerequisites.
- Missing lambda or missing scenario artifacts fail/skip clearly.
- Robust summaries disclose model-risk warnings and fallback beta behavior.

---

### 5.10 Optimizer Outputs and Diagnostics

**User question:** Are outputs sufficient to reproduce, audit, and explain optimized weights?

#### Current generated outputs

| Output | Producer | Key fields | Provenance |
| --- | --- | --- | --- |
| `portfolio_weights.yml` | Legacy policy optimizer | Released rounded weights only when mandate passes | **C** **A** |
| `run_result.json` | Legacy policy optimizer | `weights`, `status`, `optimization_status`, `analysis_setup`, `mandate_check`, `violations`, `stress_summary`, `young_etf_diagnostics` | **C** **A** |
| `run_metadata.json` | Report pipeline | Analysis setup and report metadata | **C** **A** |
| Candidate `weights.json` | Candidate wrappers | Full fixed candidate weights | **C** **A** |
| Candidate `summary.json` | Candidate wrappers | `status`, metadata block, stress status, portfolio_valid | **C** **A** |
| `baseline_weights_metadata.json` | Candidate wrappers | Objective, solver, covariance, constraints, final weights, risk diagnostics | **C** **A** |
| `weights.txt` | Candidate wrappers | Human-readable weights; sometimes RC/objective notes | **C** **A** |
| `snapshot_10y.json` | Report pipeline | Metrics, weights, stress snippets, concentration/diversification | **C** **A** |
| `stress_report.json` | Report pipeline | Stress status/scenarios/betas/diagnostics | **C** **A** |
| `portfolio_xray.json` | Report pipeline | Diagnostic X-Ray for fixed weights | **C** **A** |
| `candidate_factory_run.json` | Factory | Step status, reason, freshness, robust path disclosures | **C** **A** |
| `candidate_comparison.json` | Comparison | Row status, metrics, stress, construction disclosure, menu status | **C** **A** |
| Robust scenario `robust_optimization_v1_summary.json` | Scenario optimizer | Objective mode, lambdas, scenario returns, warnings | **C** **A** |

**Rounding/full precision:** Internal calculations preserve full precision; report-facing metrics
rounded at export. Some weight files round differently: robust scenario optimizer exports six
decimals; policy weights YAML uses rounded dict from `run_optimization.py`.

**Reproducibility status:** Partial.

Current artifacts generally disclose objective, solver, covariance, constraints, and final weights
for candidate optimizers. They do not uniformly provide one complete reproducibility envelope with:
config fingerprint, exact return rows used, expected-return vector for policy, covariance matrix
hash, optimizer parameters, solver tolerances, warm starts, and dependency artifact hashes.

**Source files/functions:** `run_optimization.py`, candidate `run_*.py` wrappers,
`src.portfolio_variants.*_metadata_export`, `run_report.run_portfolio_report_for_weights`,
`src.candidate_factory`, `src.candidate_comparison`.

**Owning spec:** `OUTPUTS.md`, `reporting_outputs_spec.md`, candidate/robust specs. Block 5
optimizer-output contract is missing. **P**

**Generated artifact evidence:** Existing folders listed in workspace show Main and candidate
artifacts. Representative fields:

- `minimum variance portfolio/baseline_weights_metadata.json.optimizer_name =
  minimum_variance_constrained`, `solver = SLSQP`, `objective = 0.5 * w.T @ covariance @ w`.
- `minimum cvar constrained portfolio/baseline_weights_metadata.json.solver = HiGHS`,
  `cvar_confidence_level = 0.95`, `n_scenarios = 120`.
- `robust mean variance constrained portfolio/baseline_weights_metadata.json.robust_mv_lambda = 2.0`.
- `Main portfolio/run_result.json.status = APPROVED`,
  `optimization_status = OK | OBJECTIVE_MODE=max_return | ...`.

**User-visible outputs:** Report text, weights text, comparison text, decision package; many audit
fields remain JSON-only.

**Limitations/risks:**

- Human-readable reports can omit objective internals that exist in metadata.
- Legacy policy output is weaker than candidate metadata on expected-return and covariance disclosure.
- Robust scenario status lacks a formal solver success field in summary.

**Could mislead:** "Weights written" can be interpreted as full optimizer auditability, but it only
proves release gate passed, not that all assumptions are visible.

**Tests:** `test_candidate_comparison_contract.py`, `test_candidate_factory_contract.py`,
`test_decision_package_reporting.py`, optimizer family tests.

**Acceptance criteria:**

- Every optimizer output includes machine-readable method id, role, objective, solver, solver status,
  input window, `analysis_end`, universe, estimator, constraints, parameter values, failure/fallback
  status, and final weights.
- Human-readable summary includes enough to prevent confusing uncapped/diagnostic candidates with
  constrained/production-compatible outputs.

---

### 5.11 Optimization Readiness for Candidate Comparison

**User question:** After weights are produced, are optimized portfolios valid, fresh, diagnosed, and
fairly comparable?

| Readiness requirement | Current behavior | Provenance |
| --- | --- | --- |
| Fixed weights exist | Candidate wrappers write `weights.json` on successful/approx builds | **C** **A** |
| Full diagnostics after weights | Wrappers call `run_portfolio_report_for_weights` to produce snapshots, stress, X-Ray, report | **C** **S** |
| Freshness | Factory/comparison check `analysis_end`; config/universe fingerprint not currently complete for optimizer methodology | **C** **S** gap |
| Snapshot metrics | `snapshot_10y.json` primary comparison source | **C** **S** |
| Stress report | Required/preferred for available non-degraded row | **C** **S** |
| Portfolio X-Ray | Produced for candidate folders, but not core comparison-readiness gate | **C** |
| Failed candidates | Factory/comparison marks failed/missing/stale as unavailable | **C** **S** |
| Partial optimized candidates | Can be `degraded` or `unavailable` depending artifacts | **C** |
| Construction method visible | Registry + construction disclosure; deeper optimizer parameters partially passed through | **C** **S** |
| Stale optimized candidates | Blocked by `analysis_end` mismatch when review date resolved | **C** **S** |
| Method/constraints/freshness shown clearly | Partial; JSON stronger than TXT | **C** gap |

**Source files/functions:** candidate wrappers, `run_report.run_portfolio_report_for_weights`,
`src.candidate_factory`, `src.candidate_comparison`, `src.selection_engine`.

**Owning spec:** `candidate_factory_spec.md`, `candidate_comparison_spec.md`,
`candidate_portfolios_spec.md`. Block 5 should own optimizer readiness disclosures. **P**

**Generated artifact fields:** `candidate_comparison.json.candidates[].status`,
`missing_fields`, `construction_disclosure`, `factory_step`, `freshness_status`;
`candidate_factory_run.json.steps[]`; per-folder snapshots/stress/X-Ray.

**Outputs the user sees:** Candidate comparison table, decision package, selection/no-trade
artifacts, per-candidate reports.

**Limitations/risks:**

- A candidate may be comparison-ready in metrics but not methodology-ready if objective/constraints
  are hidden from the user.
- `analysis_end` freshness does not prove same config/universe/estimator parameters.
- Selection can rank available rows without a methodology confidence score.

**Could mislead:** Ranking by metrics alone can hide that one candidate is uncapped, one is robust
with missing lambda provenance, and another is production-compatible legacy.

**Tests:** `test_candidate_comparison.py`, `test_candidate_comparison_contract.py`,
`test_candidate_factory.py`, `test_selection_engine.py`, optimizer family tests.

**Acceptance criteria:**

- Every optimized candidate has `weights`, `snapshot_10y`, `stress_report`, `portfolio_xray`,
  construction disclosure, freshness disclosure, and failure/approx status before it is ranked.
- Failed/stale candidates are excluded from selection but still listed with reason.
- Comparison text clearly says method, constraints, freshness, and failure status.

---

## 3. Existing implementation evidence

| Evidence type | Location |
| --- | --- |
| Legacy policy optimizer | `run_optimization.py`, `src/optimization.py::run_max_return_optimization` |
| Shared bounds | `src/optimization.py::_build_bounds`, `policy_math/feasibility.py` |
| ProLiquidity/cash overlay | `src/optimization.py::proliquidity`, `_alpha_shift_to_target_vol` |
| Candidate optimizer math | `src/portfolio_variants.py` |
| Robust MV math | `src/robust_mv.py`, `src/robust_mv_calibration.py` |
| Scenario robust math | `src/robust_scenario_optimization.py`, `run_robust_scenario_optimization.py` |
| Young ETF estimator | `src/young_etfs_dual_cov.py` |
| Candidate factory propagation | `src/candidate_factory.py` |
| Comparison readiness | `src/candidate_comparison.py` |
| Output contracts | `OUTPUTS.md`, candidate/robust/report specs |

Representative generated evidence:

- `Main portfolio/run_result.json`: `status`, `optimization_status`, `mandate_check`,
  `young_etf_diagnostics`, `stress_summary`.
- `Main portfolio/portfolio_weights.yml`: released legacy policy weights.
- `minimum variance portfolio/baseline_weights_metadata.json`: objective, solver, covariance,
  constraints, variance, annualized vol, final weights.
- `minimum cvar constrained portfolio/baseline_weights_metadata.json`: HiGHS LP diagnostics,
  confidence level, scenarios, CVaR values.
- `robust mean variance constrained portfolio/baseline_weights_metadata.json`: lambda, James-Stein
  mu, covariance shrinkage, objective value.
- `Main portfolio/robust_optimization_v1_summary.json`: scenario objective mode, lambdas, scenario
  returns.
- `Main portfolio/candidate_factory_run.json` and `candidate_comparison.json`: status propagation
  and readiness.

Representative tests:

- `tests/test_optimization_fallback.py`
- `tests/test_minimum_variance_baseline.py`
- `tests/test_maximum_diversification_baseline.py`
- `tests/test_minimum_cvar_baseline.py`
- `tests/test_robust_mean_variance.py`
- `tests/test_robust_mv_calibration.py`
- `tests/test_robust_mu_optimization.py`
- `tests/test_robust_scenario_optimization.py`
- `tests/test_young_etfs_dual_cov.py`
- `tests/test_candidate_factory.py`
- `tests/test_candidate_comparison.py`

---

## 4. Current gaps and weak points

| ID | Gap | Risk | Provenance |
| --- | --- | --- | --- |
| G1 | No single Block 5 optimization-engine spec | Optimizer facts are scattered; future changes can happen silently | **P** |
| G2 | Legacy policy expected-return vector and covariance details are not disclosed as fully as candidate metadata | Production-compatible path is less auditable than candidates | **C** gap |
| G3 | Candidate metadata exists but comparison text does not always surface objective/solver/constraint/fallback details | Users can rank without seeing methodology differences | **C** gap |
| G4 | `APPROXIMATE` and fallback paths can still produce full reports | Reports may look final unless status is prominent | **C** |
| G5 | Freshness mostly checks `analysis_end`, not full config/universe/estimator fingerprint | Same date but changed config can reuse stale method artifacts | **C** gap / **P** |
| G6 | Robust scenario summary lacks formal solver success/status field | Harder to distinguish SLSQP quality from valid-looking outputs | **C** gap |
| G7 | Young ETF dual covariance assumptions are not uniformly exposed in human summaries | Short-history model risk can be under-read | **C** gap |
| G8 | Target product objectives (Max Sharpe, drawdown-controlled, macro-resilient) are not implemented | Product concept can be confused with current capability | **T** |
| G9 | Stress diagnostics are sometimes named like failures but are diagnostic-only | User may think stress `FAIL_STRESS` blocks release | **C** **S** |
| G10 | Portfolio X-Ray exists per optimized candidate but is not a formal comparison-readiness gate | Comparison may be metrics-ready but not full-diagnostics-ready | **C** gap |

---

## 5. New methodology proposals, if any

### P1 - Create a canonical Optimization Engine layer spec

| Item | Detail |
| --- | --- |
| Source/basis | G1; user request for transparent, auditable, defensible Block 5 |
| Reason | Prevent silent optimizer/objective/constraint changes |
| Proposed method | Add a future Optimization Engine layer spec owning roles, objectives, estimators, constraints, statuses, outputs, and comparison readiness |
| Files/modules likely affected | Docs first: `SPEC.md`, `RULES.md`, `OUTPUTS.md`, `docs/specs/README.md`; code only after accepted spec |
| Output contract | Spec tables for every optimizer and status; no formula changes |
| Tests required | `scripts/verify_docs.py`; targeted docs link tests |
| Acceptance criteria | Every optimizer path in 5.8 has a spec-owned row and provenance marker |

### P2 - Optimizer reproducibility envelope

| Item | Detail |
| --- | --- |
| Source/basis | G2, G5 |
| Reason | Current outputs are not one-click reproducible/auditable |
| Proposed method | Add optional `optimizer_run_metadata` block to policy and candidate metadata: config fingerprint, universe, `analysis_end`, window, estimator, covariance hash, mu hash/vector source, bounds hash, solver options, warm starts, dependency files |
| Files/modules likely affected | `run_optimization.py`, candidate wrappers, `src/portfolio_variants.py`, `src/candidate_comparison.py`, output specs |
| Output contract | Machine-readable JSON block; human summary only key fields |
| Tests required | Golden fixture tests for metadata presence and stable hashing |
| Acceptance criteria | Same `analysis_end` but changed config/universe is detectable |

### P3 - Comparison-level optimizer disclosure

| Item | Detail |
| --- | --- |
| Source/basis | G3 |
| Reason | Fair comparison requires method, objective, constraints, estimator, solver/fallback status in the comparison artifact |
| Proposed method | Extend `construction_disclosure` for optimizer candidates with normalized `objective`, `solver`, `constraints`, `estimator`, `status`, `fallback_used`, `is_uncapped`, `is_candidate_only` |
| Files/modules likely affected | `src/candidate_comparison.py`, candidate comparison spec, candidate wrappers |
| Output contract | `candidate_comparison.json.candidates[].construction_disclosure.optimizer_methodology` |
| Tests required | Contract fixture with MinVar, CVaR, Robust MV, robust scenario |
| Acceptance criteria | Text/JSON comparison distinguishes constrained vs uncapped and OK vs APPROXIMATE |

### P4 - Formal fallback and approximate-solve policy

| Item | Detail |
| --- | --- |
| Source/basis | G4 |
| Reason | Fallback weights can be valid but not optimal |
| Proposed method | Define when fallback can be `APPROXIMATE`, when it must be `FAIL_NUMERICAL`, and how fallback status propagates to factory/comparison/selection |
| Files/modules likely affected | `src/optimization.py`, `src/portfolio_variants.py`, `src/candidate_factory.py`, specs/tests |
| Output contract | `fallback_used`, `fallback_reason`, `solver_success`, `optimization_quality_status` |
| Tests required | Forced solver failure fixtures; selection excludes or penalizes unacceptable fallback if spec decides |
| Acceptance criteria | No fallback is hidden behind plain `OK` |

### P5 - Explicit `analysis_end` and dependency fingerprint in all estimator calls

| Item | Detail |
| --- | --- |
| Source/basis | 5.2 risk; G5 |
| Reason | Avoid hidden dependence on panel tail and stale raw/incomplete data |
| Proposed method | Pass `analysis_end` explicitly through candidate covariance/young ETF helpers and store dependency fingerprints |
| Files/modules likely affected | `src/portfolio_variants.py`, `src/young_etfs_dual_cov.py`, candidate scripts |
| Output contract | Metadata `analysis_end_used_by_estimator`, `returns_panel_fingerprint` |
| Tests required | Fixture with raw panel containing later incomplete date |
| Acceptance criteria | Optimizer estimator date equals snapshot/report `analysis_end` |

### P6 - Robust scenario solver status contract

| Item | Detail |
| --- | --- |
| Source/basis | G6 |
| Reason | Robust scenario currently records message/objective but not normalized success/failure |
| Proposed method | Add `solver_success`, `solver_status`, `n_starts`, `best_start_index`, `failure_reason` to robust scenario summary |
| Files/modules likely affected | `src/robust_scenario_optimization.py`, robust scenario spec/tests |
| Output contract | `robust_optimization_v1_summary.json.solver_*` |
| Tests required | SLSQP success and forced invalid input tests |
| Acceptance criteria | Factory/comparison can show robust scenario solver quality |

### P7 - Target-only objective decision log

| Item | Detail |
| --- | --- |
| Source/basis | G8 |
| Reason | Prevent silent Max Sharpe/drawdown/macro optimizer additions |
| Proposed method | Add decision table for target-only Block 5 objectives: Max Sharpe, Max Return under Risk Constraint, Drawdown Controlled, Macro Resilient, Tax/Turnover Aware |
| Files/modules likely affected | `DECISIONS.md`, candidate/optimization specs |
| Output contract | No code behavior change |
| Tests required | Docs link checks |
| Acceptance criteria | Each concept objective is `implemented`, `covered_by_existing`, `deferred`, or `declined` |

---

## 6. P0 / P1 / P2 improvement plan

| Priority | Item | Type | Notes |
| --- | --- | --- | --- |
| **P0** | Accept this Block 5 methodology map as the audit baseline | Docs | No optimizer changes |
| **P0** | Create canonical Optimization Engine layer spec (P1) | Spec | Required before methodology changes |
| **P0** | Add decision log for target-only objectives (P7) | Governance | Prevent silent optimizer additions |
| **P1** | Add comparison-level optimizer disclosure (P3) | Output/spec | Makes current candidates explainable without formula changes |
| **P1** | Formal fallback/approximate policy (P4) | Spec/code | Clarifies whether fallback can be ranked |
| **P1** | Robust scenario solver status contract (P6) | Output/code | Small, high audit value |
| **P2** | Full reproducibility envelope (P2) | Output/code | Broader change; requires contract design |
| **P2** | Explicit estimator `analysis_end` and fingerprint everywhere (P5) | Data/code | Reduces stale/incomplete-period risk |
| **P2** | Human-readable optimizer methodology appendix in reports | Reporting | No UI; generated report text only after spec |

Non-goals for this governance step:

- No UI work.
- No new optimizers.
- No formula, objective, constraint, estimator, mandate gate, fallback, or status change without
  accepted spec decision.

---

## 7. Verification checklist

Use this before closing a Block 5 governance session:

- [ ] `python -m pytest tests/test_optimization_fallback.py`
- [ ] `python -m pytest tests/test_minimum_variance_baseline.py tests/test_maximum_diversification_baseline.py tests/test_minimum_cvar_baseline.py`
- [ ] `python -m pytest tests/test_robust_mean_variance.py tests/test_robust_mv_calibration.py tests/test_robust_scenario_optimization.py`
- [ ] `python -m pytest tests/test_young_etfs_dual_cov.py`
- [ ] `python -m pytest tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_candidate_comparison_contract.py`
- [ ] Artifact inspection: one policy `run_result.json`, one MinVar metadata file, one CVaR metadata
  file, one Robust MV metadata file, one robust scenario summary.
- [ ] Verify `candidate_comparison.json` excludes unavailable/stale optimizer candidates from ranking.
- [ ] Verify all target-only objectives are marked **T** or **P**, not implied implemented.
- [ ] Verify no new objective/constraint/status appears in code without spec update.
- [ ] `python scripts/verify_docs.py` after adding/updating owning specs.

Documentation-only changes normally do not require full pytest, but any code/output contract change
under Block 5 should run the focused bundle above and broaden if shared optimizer helpers changed.

---

## 8. Final verdict

Block 5 is **implemented but not yet fully governed as a single auditable layer**.

The code contains serious optimizer machinery: production-compatible legacy max-return policy,
classic convex candidates, heuristic diversification candidates, CVaR LP, Robust MV with shrinkage
and lambda calibration, and scenario-aware optimization. Most formulas and solver details are
present in code and candidate metadata. The major deficit is not math coverage; it is methodology
governance and disclosure consistency.

Current safe interpretation:

- Legacy policy optimization can produce released weights only through `run_optimization.py` and
  mandate gate semantics.
- Candidate optimizers are comparison hypotheses, not production policy.
- Stress/factor/macro diagnostics do not silently bind optimization.
- Target product objectives such as Max Sharpe, drawdown-controlled, and macro-resilient are not
  shipped optimizers.

Before implementing any next Block 5 session, the project should first create a canonical
Optimization Engine spec and decide which gaps are documentation-only versus behavior/output
changes. Any new objective, constraint, estimator, robustness rule, fallback, status, or candidate
generation rule remains a **NEW METHODOLOGY PROPOSAL — requires spec decision before implementation**.
