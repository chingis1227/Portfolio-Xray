# Optimization Engine Layer Specification (Block 5)

This document is the canonical source of truth for the current Optimization Engine layer. It
describes existing behavior only. It does not add optimizer objectives, estimators, constraints,
statuses, runtime fields, generated artifacts, or release gates.

Related audit baseline: [Optimization Engine Methodology Map](../audits/2026-05-20_optimization_engine_methodology_map.md).
Related roadmap: [Optimization Engine Post-Audit Roadmap](../exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md).

## Status And Non-Goals

This spec governs Block 5 roles, boundaries, and disclosure language. Detailed formulas remain in
the owning method specs and code paths listed below.

Sessions 01-02 were documentation-only. Session 03 implements legacy policy disclosure in
`run_result.json.optimizer_run_metadata`. Session 04 implements candidate optimizer disclosure in
optimizer candidate `baseline_weights_metadata.json.optimizer_run_metadata`. Session 05 propagates
available normalized optimizer metadata into
`candidate_comparison.json` row `construction_disclosure.optimizer_methodology`. Session 06
formalizes fallback/failure quality so non-clean optimizer solves are visible in factory,
comparison, and selection surfaces. Session 07 adds normalized robust scenario solver status in
`robust_optimization_v1_summary.json` and copies it into robust scenario candidate
`baseline_weights_metadata.json.optimizer_run_metadata`. Session 08 makes estimator dates and input
fingerprints explicit for legacy policy and candidate optimizer metadata. Session 09 surfaces
covariance and Young ETF methodology in optimizer metadata and human-readable summaries without
changing covariance formulas. Session 10 formalizes optimization comparison readiness in
`candidate_comparison.json` row `construction_disclosure.optimization_readiness` without changing
optimizer formulas, comparison ranking, or row-status rules beyond the existing Session 06 quality
boundary. The following remain not implemented by this spec:

- new optimizer code;
- new generated artifacts;
- new hard constraints, mandate gates, objectives, or fallback semantics;
- target-only objectives such as Max Sharpe, drawdown-controlled, macro-resilient, tax-aware, or
  turnover-aware optimization.

Any new objective, estimator, hard constraint, solver status, output field, comparison gate, or
candidate id must be treated as a methodology proposal and requires a later spec decision before
implementation.

## Block 5.1 - Optimization Role And Boundary

The Optimization Engine builds or evaluates portfolio weights. It is not one unified production
allocator in the current product. It is a set of distinct paths with different authority.

| Path role | Current meaning | Binding effect |
| --- | --- | --- |
| Legacy policy | `run_optimization.py` / `src/optimization.py::run_max_return_optimization`; can write `portfolio_weights.yml` and `run_result.json` after release checks. | Production-compatible compatibility path only. Not the default portfolio-first subject. |
| Candidate-only | Builder scripts create fixed weights for comparison, then run the report pipeline. | Does not overwrite policy weights or change mandate gates. |
| Diagnostic-only | Metrics, stress, RC_vol, factor, macro, X-Ray, comparison, scorecards, health score, and most decision-support artifacts. | Informs review; does not bind weights unless another canonical spec says so. |
| Calibration-only | Tools such as Robust MV lambda calibration that select or evaluate parameters for later candidate builds. | Does not itself release policy weights and is not a candidate factory step unless a later spec changes it. |
| Target-only | Product concepts not shipped as optimizers. | No runtime behavior. Requires later spec decision before implementation. |

Portfolio-first review starts from `analysis_subject`, diagnoses it first, and only then compares
alternatives. The legacy policy optimizer remains callable for compatibility but is not reactivated
as the default portfolio-first starting point by this spec.

## Block 5.2 - Optimization Inputs And Data Preparation

Current optimizer inputs are sourced from config, monthly return panels, optional calibration files,
and generated Main report artifacts.

| Input area | Current behavior | Owning source |
| --- | --- | --- |
| Return panel | Investor-currency monthly simple returns from adjusted prices. | [metrics_specification.md](metrics_specification.md), [data_policy_spec.md](data_policy_spec.md) |
| Analysis date | `analysis_end` is the last completed effective period used by loaders/report windows. Candidate paths normally receive an already truncated panel and explicit wrapper date. | [metrics_specification.md](metrics_specification.md), [candidate_factory_spec.md](candidate_factory_spec.md) |
| Window | Legacy policy primary window defaults to 120 months; secondary robustness check defaults to 60 months. Candidate wrappers usually use the primary comparison window. | [portfolio_construction_policy.md](portfolio_construction_policy.md), candidate specs |
| Universe | Config tickers with available data; candidate variants apply coverage filtering. Cash proxy is excluded from risk optimization and added through policy cash handling where applicable. | [data_policy_spec.md](data_policy_spec.md), [portfolio_construction_policy.md](portfolio_construction_policy.md) |
| Young ETFs | Optional dual covariance / per-ticker caps where current implementation supports it. | [data_policy_spec.md](data_policy_spec.md), [portfolio_construction_policy.md](portfolio_construction_policy.md) |
| Scenario inputs | Robust scenario candidate reads Main `scenario_library_normalized.json` and `stress_report.json`. | [robust_scenario_optimization_spec.md](robust_scenario_optimization_spec.md) |

Beginning with Session 08, legacy policy and optimizer-candidate metadata include an
`input_fingerprints` block with `returns_panel_fingerprint`, `config_fingerprint`, and
`universe_fingerprint`. The return-panel fingerprint is a SHA-256 hash of the estimator's ordered
monthly return window, including dates, columns, values, and missing values. The config fingerprint
hashes optimizer-relevant config fields plus method/window parameters. The universe fingerprint
hashes the ordered estimator ticker set. These fields are disclosure and stale-input detection aids;
they do not change optimizer formulas, eligible-universe rules, or comparison ranking.

## Block 5.3 - Expected Return Estimation Matrix

| Path/objective | Expected return used... | Current estimator |
| --- | --- | --- |
| Legacy policy `max_return` | Yes | Sample mean of monthly simple returns over optimization window, or precomputed dual-covariance `mu` where that path is used. |
| Legacy policy `risk_parity` mode | No | Not applicable; objective is risk parity. |
| Minimum Variance | No | Not applicable. |
| Maximum Diversification | No explicit expected-return vector | Asset volatility from covariance drives the diversification ratio. |
| Minimum CVaR | No explicit expected-return vector | Realized monthly scenario matrix drives the LP. |
| Robust MV | Yes | James-Stein shrinkage of monthly sample means toward the cross-sectional grand mean. |
| Robust MV lambda calibration | Uses Robust MV candidate builds, then evaluates reported metrics and mandate-style diagnostics. | Same Robust MV estimator for builds. |
| Robust scenario | Yes, through scenario inputs | `base_historical.expected_returns_by_asset` from normalized scenario library plus scenario coefficients. |
| Max Sharpe | Not implemented | Target-only. |
| Drawdown-controlled / macro-resilient | Not implemented | Target-only. |

Expected-return assumptions are optimizer assumptions, not forecasts guaranteed by the product.

## Block 5.4 - Covariance And Risk Model Estimation Matrix

| Estimator/path | Current method | Notes |
| --- | --- | --- |
| Legacy policy sample covariance | Monthly sample covariance, optional Ledoit-Wolf via `covariance_shrinkage`. | Used by `run_max_return_optimization` unless precomputed covariance is supplied. |
| Legacy policy dual covariance | Young ETF policy can provide precomputed covariance and `mu`. | Current behavior is owned by young ETF and portfolio construction specs. |
| Minimum Variance / Maximum Diversification / HRP | Shared monthly covariance helper, PSD repair where needed; constrained variants may use young ETF caps where implemented. | Candidate-only. |
| Minimum Variance advanced | Ledoit-Wolf covariance regardless of general `covariance_shrinkage`. | Candidate-only advanced controls. |
| Minimum CVaR | LP uses monthly scenario return matrix; covariance fields may be emitted for diagnostics. | CVaR objective is not covariance minimization. |
| Robust MV | Ledoit-Wolf or OAS covariance plus PSD repair metadata. | Candidate-only robust benchmark. |
| Robust scenario | Base covariance from `base_historical` scenario library field. | Candidate-only; reads Main report artifacts. |

Session 08 records normalized covariance `analysis_end` and return-panel fingerprint in legacy
policy and optimizer-candidate metadata. The metadata identifies the estimator window used for the
covariance path; it does not change covariance formulas or PSD repair behavior.

Beginning with Session 09, optimizer metadata also includes explicit covariance methodology
disclosure. Legacy policy and optimizer-candidate `optimizer_run_metadata.covariance` blocks include
`methodology` (`optimizer_covariance_methodology_v1`) and `methodology_summary`; the top-level
metadata includes `young_etf_methodology` (`optimizer_young_etf_methodology_v1`). These fields
describe the already-used estimator, monthly frequency, join policy, `ddof`, shrinkage, PSD repair
status when known, Young ETF mode, bucket diagnostics, fallback reason, and per-ticker caps when
present. They are explanatory only and must not be used to recompute weights.

## Block 5.5 - Objective Matrix

| Current objective id | Implemented path | Objective role |
| --- | --- | --- |
| `max_return` | Legacy policy | Minimize `-mu'w` with optional soft target-vol, soft target-return, and skeleton tracking penalties. |
| `risk_parity` | Legacy policy diagnostic mode and separate risk-parity benchmark family | Equal risk contribution via Spinu CCD or SLSQP fallback depending path. |
| `minimum_variance_constrained` | Candidate-only | Minimize `0.5 * w.T @ covariance @ w` under project box bounds. |
| `minimum_variance_uncapped_long_only` | Diagnostic candidate-only | Same variance objective under long-only `[0,1]` bounds. |
| `minimum_variance_advanced_controls` | Candidate-only advanced diagnostic | Minimum variance with Ledoit-Wolf covariance, optional vol cap, optional L1 vs current weights. |
| `maximum_diversification_constrained` | Candidate-only | Maximize diversification ratio under project box bounds. |
| `maximum_diversification_unconstrained` | Diagnostic candidate-only | Same diversification ratio under long-only `[0,1]` bounds. |
| `minimum_cvar_constrained` | Candidate-only | Rockafellar-Uryasev LP minimizing empirical CVaR under project box bounds. |
| `minimum_cvar_uncapped` | Diagnostic candidate-only | Same CVaR LP under long-only `[0,1]` bounds. |
| `robust_mean_variance_*` | Candidate-only | Minimize `lambda * w' Sigma w - mu' w` using shrunk inputs. |
| `lower_half_mean`, `maximin`, `hybrid_legacy` | Robust scenario candidate | Scenario-return objective modes from normalized scenario library and Main stress artifacts. |

Target-only objective names such as Max Sharpe, drawdown-controlled, macro-resilient,
stress-test-optimized menu, tax-aware, and turnover-aware optimization are not implemented
optimizer objectives in the current runtime. Minimum-variance advanced may include an optional L1
term versus current weights, but that is not a general tax/turnover-aware optimizer product.

## Block 5.6 - Constraints And Diagnostic-Only Signals

Hard constraints affect optimizer feasibility or release behavior. Diagnostic-only signals may be
reported, ranked, or reviewed, but they do not bind weights unless a specific canonical spec says so.

| Signal or rule | Current classification | Current effect |
| --- | --- | --- |
| Long-only and fully invested risk weights | Hard optimizer constraint | Enforced in optimizer/candidate solves. |
| Config min weight and max single-security cap | Hard optimizer box bounds where that path uses project bounds. | Can make candidate/policy optimization infeasible. |
| Young ETF per-ticker caps | Hard optimizer bound only in paths where implemented. | Caps candidate/new tickers under dual covariance policy. |
| Cash/liquidity floor and vol-scaling cash | Policy post-processing / hard policy handling | Legacy policy overlay only, not candidate builders unless specified elsewhere. |
| Mandate max drawdown | Hard release gate for legacy policy | Can block writing policy weights through `FAIL_MANDATE`. |
| Minimum Variance advanced vol cap | Candidate-only hard constraint for that variant when configured/effective. | Can produce `FAIL_INFEASIBLE_VOL_TARGET`. |
| Robust MV lambda | Candidate parameter | Changes Robust MV trade-off; not a client-facing mandate dial. |
| Robust scenario scenario roles | Objective inputs / soft penalties in current objective modes | Do not change policy release gates. |
| RC_vol / Top1 / Top3 risk contribution | Diagnostic-only | Reported only; no RC cap, objective penalty, or release gate in current pipeline. |
| Stress diagnostics and `DIAG_*` / stress `FAIL_*` text | Diagnostic-only except mandate MaxDD path | Do not block release when mandate passes. |
| Factor and macro diagnostics | Diagnostic-only | Do not bind optimizer universe, weights, or selection. |
| ETF/stock taxonomy | Annotation and some benchmark bucketing | Does not generally select optimizer universe in V1. |
| Portfolio X-Ray and scorecards | Diagnostic-only | Do not optimize, release, or select weights by themselves. |

## Block 5.7 - Status, Failure, And Fallback Matrix

| Status family | Current source | Current interpretation |
| --- | --- | --- |
| `APPROVED` | Legacy `run_result.json.status` | Legacy policy release passed and optimizer did not return `OK_FALLBACK`; normalized optimizer quality is `clean_solve`. |
| `OK_FALLBACK` | Legacy optimizer status and sometimes run status | Alternative solution branch/fallback was used; weights may still be written when mandate passes, but normalized optimizer quality is `approximate_fallback`, not a clean solve. |
| `FAIL_MANDATE` | Legacy policy release gate | Blocks policy weight release when mandate MaxDD fails or cannot be checked. |
| `FAIL_DATA` | Policy/candidate builders | Missing/invalid data or config-side data failure. |
| `OK` | Candidate builders / optimizer diagnostics | Builder produced feasible weights by its current success checks. |
| `APPROXIMATE` | Candidate builders such as Min CVaR / Robust MV when feasible weights exist despite solver quality issues | Candidate may produce a report, but status must not be read as a clean solve. |
| `FAIL_CONFIG` | Candidate builders | Unsupported or missing required configuration/parameter, such as missing Robust MV lambda. |
| `FAIL_INFEASIBLE_UNIVERSE` | Candidate builders | Not enough eligible assets. |
| `FAIL_INFEASIBLE_BOUNDS` | Candidate builders | Box bounds cannot support a fully invested portfolio. |
| `FAIL_INFEASIBLE_TARGETS` | Builder/factory reason-code family | Infeasible targets where a builder reports that family. |
| `FAIL_INFEASIBLE_VOL_TARGET` | Minimum Variance advanced | Configured volatility cap is below minimum achievable variance under bounds. |
| `FAIL_NUMERICAL` | Candidate builders | Solver failed or produced invalid weights. |
| `FAIL_NO_ASSETS` | Builder/factory reason-code family | No usable assets where a builder reports that family. |
| `succeeded`, `failed`, `skipped_existing`, `skipped_dependency`, `skipped_profile` | Candidate factory | Orchestration status, not optimizer math status. |
| `available`, `degraded`, `unavailable` | Candidate comparison | Readiness of report artifacts for comparison; beginning Session 06, visible fallback/approximate optimizer quality degrades an otherwise available optimizer row, and failed optimizer/factory quality makes the row unavailable. |

Normalized optimizer quality values beginning with Session 06:

| Value | Meaning | Boundary behavior |
| --- | --- | --- |
| `clean_solve` | Solver/factory evidence reports success with no optimizer fallback. | May appear as ordinary optimizer construction evidence when other artifacts are fresh and complete. |
| `approximate_fallback` | Fallback branch or retry produced usable weights. | Must be surfaced in optimizer metadata, factory step evidence, comparison `optimizer_quality`, and Selection warnings if favored. Comparison degrades an otherwise `available` optimizer row. |
| `approximate_solver` | Feasible or usable output exists despite approximate/non-clean solver status. | Same boundary treatment as fallback: visible and degraded, not ordinary success. |
| `failed_solver` / `failed` | Solver or builder quality is failed. | Comparison marks the row unavailable when this quality is visible. |
| `unknown` | No normalized solver quality evidence was available. | Does not by itself invalidate a row; absence must not be interpreted as clean optimization. |

Factory step `status: succeeded` remains an orchestration result: the candidate script completed and
required snapshot artifacts exist. It is not proof of clean optimization. When upstream artifacts
expose optimizer quality, factory steps copy `optimization_quality_status`,
`optimization_quality_family`, fallback fields, and solver status. Candidate comparison applies the
selection boundary: failed factory steps make the row `unavailable`; approximate/fallback optimizer
quality degrades an otherwise available optimizer row; failed optimizer quality makes the row
`unavailable`. Selection may still consider degraded rows, but if such a row is favored it must warn
that the favored target used an approximate optimizer solve or fallback.

## Block 5.8 - Optimizer Path Role Matrix

| Path or construction | Current role | Implemented... | Notes |
| --- | --- | --- | --- |
| `run_optimization.py` / `max_return` | Legacy policy | Yes | Can write policy weights after release checks. |
| Legacy `risk_parity` objective mode | Diagnostic/code-supported | Yes | Not the default policy objective. |
| Equal weight, equal weight by asset class | Benchmark candidate | Yes | Not an optimizer policy. |
| Risk parity, risk budget, HRP | Benchmark / diagnostic candidate | Yes | Interact with risk math but do not release policy weights. |
| Minimum Variance constrained | Candidate-only | Yes | Primary constrained lowest-volatility baseline. |
| Minimum Variance uncapped | Diagnostic candidate-only | Yes | Relaxed-bounds reference. |
| Minimum Variance advanced | Candidate-only advanced diagnostic | Yes | Optional vol cap and L1 controls; not the primary constrained MinVar baseline. |
| Maximum Diversification constrained | Candidate-only | Yes | Uses project box bounds. |
| Maximum Diversification uncapped | Diagnostic candidate-only | Yes | Long-only relaxed-bounds reference. |
| Minimum CVaR constrained | Candidate-only | Yes | LP under project box bounds. |
| Minimum CVaR uncapped | Diagnostic candidate-only | Yes | LP under long-only relaxed bounds. |
| Robust MV constrained | Candidate-only | Yes | Requires lambda resolution before build. |
| Robust MV uncapped | Diagnostic candidate-only | Yes | Relaxed-bounds robust benchmark. |
| Robust MV lambda calibration | Calibration-only | Yes | Writes calibration artifacts/selected lambda; not a factory step by default. |
| Robust scenario | Robust candidate-only | Yes | Reads Main scenario/stress artifacts; does not overwrite policy. |
| Max Sharpe | Target-only | No | Requires later spec decision and implementation. |
| Drawdown-controlled optimizer | Target-only | No | Current drawdown metrics and mandate gate do not implement this candidate objective. |
| Macro-resilient optimizer | Target-only | No | Macro/regime diagnostics are non-binding overlays. |
| Tax/turnover-aware optimizer | Target-only | No | Current action/trade-off outputs may discuss turnover, but no shipped optimizer objective. |

## Block 5.9 - Calibration-Only And Target-Only Boundaries

Calibration-only outputs may guide a later candidate build, but they are not candidate rows by
themselves and do not release policy weights. Robust MV lambda calibration is the current canonical
example.

Target-only optimizer names may appear in product concept documents or future planning, but they are
not current behavior. When referenced in docs, they must be marked as one of:

- methodology proposal;
- deferred;
- requires later spec decision;
- not implemented.

They must not be listed as shipped candidate ids, hard constraints, output fields, or active
objectives unless the relevant later session updates specs, code, tests, and output contracts.

### Appendix A - Target-Only Objective Decision Register

Decision [DEC-2026-05-21-001](../../DECISIONS.md) records the project-level boundary for
target-only optimizer objectives. Until that decision is superseded, the following names remain
non-runtime concepts:

| Target-only name | Current allowed meaning | Current forbidden interpretation |
| --- | --- | --- |
| Max Sharpe | Future methodology proposal or product concept label. | Shipped policy objective, candidate builder, or comparison `candidate_id`. |
| Drawdown-controlled optimizer | Future methodology proposal; current drawdown metrics and mandate MaxDD gate remain separate. | Objective function, drawdown hard constraint, or candidate row. |
| Macro-resilient optimizer | Future methodology proposal; current factor and macro diagnostics remain diagnostic-only. | Macro-bound optimizer, hard regime gate, or candidate row. |
| Stress-test-optimized menu | Future product concept label; current robust scenario candidate is the shipped stress-aware candidate path. | Duplicate candidate id or automatic selection/release policy. |
| Tax-aware optimizer | Future methodology proposal; current action/trade-off outputs may discuss costs or turnover but not tax lots. | Tax-lot optimizer, taxable-account constraint, or output contract. |
| Turnover-aware optimizer | Future methodology proposal; minimum-variance advanced may use an optional L1 term versus current weights. | General turnover-aware product objective, tax proxy, or mandate gate. |

If one of these names is promoted later, the promoting session must add or update the owning spec,
runtime implementation, output contract, focused tests, documentation indexes, and a superseding or
companion decision record.

## Block 5.10 - Output And Disclosure Matrix

| Artifact or surface | Current producer | Current role |
| --- | --- | --- |
| `portfolio_weights.yml` | Legacy `run_optimization.py` | Generated policy weights when release is allowed. |
| `run_result.json` | Legacy `run_optimization.py` | Policy status, mandate check, optimizer status string, diagnostics, assumptions, and legacy `optimizer_run_metadata`. |
| `run_metadata.json` | Report pipeline | Run/report metadata and `analysis_setup` projection. |
| Candidate `weights.json` / `weights.txt` | Candidate builders | Fixed candidate weights for that candidate folder. |
| Candidate `summary.json` | Candidate builders/report wrappers | Builder/report summary; may include `status` and diagnostics. |
| Candidate `baseline_weights_metadata.json` | Candidate builders | Strongest current per-candidate construction disclosure where present; optimizer candidates include `optimizer_run_metadata` beginning with Session 04. |
| `robust_optimization_v1_summary.json` | Robust scenario optimizer | Scenario objective, lambdas, sorted returns, beta warnings, optimizer message, and normalized solver/fallback quality. |
| `candidate_factory_run.json` | Candidate factory | Builder orchestration status, freshness, config fingerprint, and robust path disclosure. |
| `candidate_comparison.json` | Candidate comparison | Read-only comparison table with construction disclosure passthrough, row readiness, and comparison-level optimizer methodology when upstream metadata exists. |
| Human report/TXT/PDF surfaces | Report and decision-package writers | User-facing summaries; not all optimizer internals are surfaced equally today. |

Session 03 adds `optimizer_run_metadata` to legacy policy `run_result.json` with:

- `schema_version: legacy_policy_optimizer_run_metadata_v1`;
- optimizer role, entrypoint, method id, objective mode, and soft target penalty parameters;
- `analysis_end`, primary and secondary windows, return frequency, and periods per year;
- expected-return and covariance source/method disclosure, including young ETF dual-covariance mode
  when used;
- configured, risk, and eligible universes plus cash proxy exclusion;
- long-only / fully invested constraint disclosure, resolved per-ticker bounds, global caps, and
  young ETF per-ticker caps;
- ProLiquidity cash policy inputs;
- solver/fallback quality derived from the existing optimizer status string;
- release status, mandate gate name, mandate pass/fail, and whether weights were written.

This block explains how the legacy policy output was built, but it does not change formulas,
constraints, fallback behavior, mandate gates, or generated weight semantics.

Session 04 adds `optimizer_run_metadata` to candidate optimizer `baseline_weights_metadata.json`
exports for Minimum Variance, Maximum Diversification, Minimum CVaR, and Robust Mean-Variance
families with:

- `schema_version: candidate_optimizer_run_metadata_v1`;
- optimizer role, method id, objective, monthly input window, and candidate-only status;
- expected-return usage, covariance method, PSD repair, Young ETF dual mode where known, eligible
  universe, active constraints, resolved bounds, and relevant parameters such as CVaR confidence,
  Robust MV lambda, L1/volatility controls;
- solver name, solver status/success/message, fallback flag, and normalized
  `optimization_quality_status`;
- output summary fields for final weights, portfolio variance, annualized volatility, and objective
  value when present.

The candidate block is explanatory only. It preserves existing metadata fields and does not change
optimizer formulas, constraints, fallback behavior, report metrics, mandate gates, generated
weights, or comparison semantics.

Session 05 adds comparison-level optimizer disclosure under
`candidate_comparison.json` row `construction_disclosure.optimizer_methodology`. The comparison
builder copies a compact subset from `baseline_weights_metadata.json.optimizer_run_metadata` for
optimizer candidates and from `run_result.json.optimizer_run_metadata` for legacy policy. The subset
shows source schema, role, candidate-only status, method id, objective, input window, expected-return
and covariance method disclosure, constraints, solver/fallback quality, and factory freshness fields
when present. It remains read-only evidence; it does not recompute methodology, alter row status,
change ranking, or change optimizer behavior.

Session 06 adds normalized optimizer-quality projection at comparison level under
`construction_disclosure.optimizer_quality` when source metadata or factory step evidence is
available. This block records `optimization_quality_status`, quality family, fallback flag/reason,
solver status, and source. It may change comparison readiness (`available` to `degraded`, or
`unavailable` for failed quality/factory failure), but it does not recompute weights, objectives, or
constraints.

Session 07 adds the robust scenario solver contract. `robust_optimization_v1_summary.json` now
contains a normalized `solver` block plus top-level compact fields (`solver_success`,
`solver_status`, `fallback_used`, `fallback_reason`, `optimization_quality_status`). When the robust
scenario portfolio report is materialized, `baseline_weights_metadata.json.optimizer_run_metadata`
uses `schema_version: robust_scenario_optimizer_run_metadata_v1` and discloses method id,
objective mode, scenario/stress input sources, base expected-return and covariance assumptions,
long-only/fully-invested/box-bound constraints, lambdas, solver/fallback quality, and output
summary fields. Factory and comparison consume this metadata as disclosure only; formulas,
constraints, fallback branches, generated weights, and mandate gates are unchanged.

Session 08 adds explicit estimator-input disclosure to legacy policy and candidate optimizer
metadata. Legacy policy `run_result.json.optimizer_run_metadata` and candidate optimizer
`baseline_weights_metadata.json.optimizer_run_metadata` now include:

- `input_window.returns_panel_start`, `input_window.returns_panel_end`, and
  `input_window.returns_panel_rows`;
- `input_fingerprints.returns_panel_fingerprint`, `input_fingerprints.config_fingerprint`, and
  `input_fingerprints.universe_fingerprint`;
- estimator `analysis_end` and `returns_panel_fingerprint` on expected-return and covariance
  disclosure blocks when those estimators use return-panel inputs;
- `universe.universe_fingerprint` and candidate `universe.estimator_input_columns`.

Candidate covariance helpers must pass the wrapper `analysis_end` explicitly into young-ETF dual
covariance estimation so the estimator cannot silently fall back to the panel maximum date. These
fields are explanatory and reproducibility metadata only; formulas, constraints, fallback branches,
mandate gates, generated weights, and comparison semantics are unchanged.

Session 09 adds covariance and Young ETF methodology disclosure to existing metadata and human
outputs:

- `optimizer_run_metadata.covariance.methodology` uses
  `schema_version: optimizer_covariance_methodology_v1`;
- `optimizer_run_metadata.covariance.methodology_summary` is a compact English line for report
  surfaces;
- `optimizer_run_metadata.young_etf_methodology` uses
  `schema_version: optimizer_young_etf_methodology_v1`;
- comparison rows copy `young_etf_methodology` into
  `construction_disclosure.optimizer_methodology` when source metadata provides it;
- `candidate_comparison.txt` and legacy `ips_summary.txt` include compact optimizer methodology
  notes.

This session changes disclosure only. It does not change covariance formulas, Young ETF bucket
rules, caps, fallback behavior, optimizer constraints, mandate gates, comparison ranking, or
generated weights.

## Block 5.11 - Optimization Readiness For Candidate Comparison

An optimized candidate is comparison-ready only when fixed weights and required report artifacts
exist and are fresh enough for the review. Comparison readiness is not the same as production
release.

Session 10 adds `construction_disclosure.optimization_readiness`
(`optimizer_comparison_readiness_v1`) for roles `optimizer_candidate`, `robust_candidate`, and
`policy`. The block is read-only evidence assembled from existing artifacts; it does not rerun
optimizers or change comparison ranking.

Blocks 1-5 reliability Session 05 (`RM-1014`) tightens the comparison boundary around that
readiness evidence. An optimizer-backed row that has report metrics but lacks required optimizer
methodology or optimizer-quality evidence is explicitly degraded instead of remaining ordinary
`available`. `optimizer_quality` normalized to `unknown` also degrades an otherwise available
optimizer-backed row. This does not change optimizer formulas, constraints, solvers, or weights; it
only aligns `optimizer_methodology`, `optimizer_quality`, and `optimization_readiness` disclosure.

| Readiness item | Current behavior |
| --- | --- |
| Fixed weights | Required check: `weights.json`, `snapshot_10y.final_weights_total`, or `baseline_weights_metadata` weights. |
| Snapshot metrics | Required check: `snapshot_10y.json` present; row `available` / `degraded` still governed by comparison status rules. |
| Stress summary | Required for `fair_comparison_ready`; absence may still allow `degraded` row status with gap `stress_summary`. |
| X-Ray/report diagnostics | Optional check: `portfolio_xray.json` when present; not required for fair comparison (G7). |
| Freshness | Required check uses factory `freshness_status`, snapshot `analysis_end`, and stale warnings. |
| Construction disclosure | Required check: `disclosure_status` available or partial; `available` required for fair comparison. |
| Optimizer methodology | Required for `fair_comparison_ready` on optimizer/robust rows via `optimizer_methodology`. |
| Optimizer quality | Copied from Session 06 `optimizer_quality`; `clean` required for `fair_comparison_ready`; missing or `unknown` evidence degrades an otherwise available optimizer-backed row. |
| Failed/stale candidates | `overall_status: failed` when row is `unavailable` or optimizer quality family is `failed`. |
| Selection boundary | `candidate_comparison.json` remains diagnostic-only; `fair_comparison_ready` is not a trade signal. |
| Fallback/approximate optimizer quality | `overall_status: degraded_quality`; `fair_comparison_ready: false`. |
| Fair comparison gate | `fair_comparison_ready: true` only when row is `available`, disclosure is `available`, required checks pass, methodology is present, and optimizer quality is `clean`. |

Benchmark, analysis-subject, and current rows do not emit `optimization_readiness`.

## Detailed Ownership

| Area | Governing document |
| --- | --- |
| Legacy policy objective, ProLiquidity, mandate release boundary | [portfolio_construction_policy.md](portfolio_construction_policy.md) |
| Release statuses and hard stops | [production_workflow.md](production_workflow.md) |
| Feasibility caps and RC diagnostic boundary | [feasibility_constraints_spec.md](feasibility_constraints_spec.md) |
| Metrics, returns, covariance, RC_vol, drawdown | [metrics_specification.md](metrics_specification.md) |
| Data policy and young ETFs | [data_policy_spec.md](data_policy_spec.md) |
| Candidate families and concept-candidate boundary | [candidate_portfolios_spec.md](candidate_portfolios_spec.md) |
| Candidate orchestration and factory statuses | [candidate_factory_spec.md](candidate_factory_spec.md) |
| Candidate comparison readiness and construction disclosure passthrough | [candidate_comparison_spec.md](candidate_comparison_spec.md) |
| Robust MV and lambda calibration | [robust_mv_spec.md](robust_mv_spec.md) |
| Scenario robust candidate | [robust_scenario_optimization_spec.md](robust_scenario_optimization_spec.md) |
| Generated output boundaries | [../../OUTPUTS.md](../../OUTPUTS.md) |

## Verification

For documentation-only changes to this spec, run:

```bash
python scripts/verify_docs.py
```

If optimizer behavior, output contracts, or runtime code changes in later sessions, run the focused
Block 5 bundle named in [TESTING.md](../../TESTING.md) and the active ExecPlan.

Golden JSON contract tests (Session 11 / `RM-1001`):

- `tests/fixtures/legacy_policy_optimizer_run_metadata_golden_v1.json`
- `tests/fixtures/candidate_optimizer_run_metadata_golden_v1.json`
- `tests/fixtures/optimization_comparison_block5_golden_v1.json`
- Regenerate: `python tests/optimization_engine_golden_inputs.py`
- Tests: `tests/test_optimization_engine_contract.py`
