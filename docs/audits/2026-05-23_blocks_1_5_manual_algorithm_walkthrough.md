# Blocks 1–5 Manual Algorithm Walkthrough

Date: 2026-05-23  
Evidence basis: current repository code, canonical specs under `docs/specs/`, `SPEC.md`, and on-disk artifacts from the proof portfolio (`Main portfolio/`, subject run timestamp 2026-05-22). Target product concepts (e.g. `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`) are non-binding and not used as implementation proof.

Proof portfolio and command:

| Item | Value |
| --- | --- |
| Tickers | SPY, QQQ, GLD, SLV, BND, SCHD, SCHP, TLT |
| Weights | 10%, 13%, 9%, 9%, 16%, 17%, 13%, 13% (sum = 1.0) |
| `analysis_subject.type` | `current_portfolio` |
| `investor_currency` | USD |
| Benchmark (resolved) | SPY |
| `client_profile` | Balanced |
| `analysis_end` (resolved) | 2026-04-30 |
| Proof command | `python run_portfolio_review.py --mode core --skip-pdf` |

**Scope:** Blocks 1–5 only. Selection Engine, Action Engine, Monitoring, Decision Journal, final investment recommendation, UI, and PDF design are **outside scope**. Files such as `action_plan.json` or `decision_package_summary.json` may exist on disk from other runs; they are downstream of Blocks 1–5.

---

## How to read this document

This is a **manual walkthrough**: what the system does step by step for the proof portfolio, as if performing the review by hand but strictly following current code. It does not describe ideal or target product behavior.

**Blocks 1–5 are code-driven, not AI-driven.** A search of `*.py` for LLM provider integrations (`openai`, `anthropic`, `gpt-`, `llm`) returned **no matches**. Status strings (`insufficient_data`, `partial`, `skipped_existing`, `DIAG_*`) are assigned by Python. Commentary (`src/portfolio_commentary.py`) is template/rule-generated from JSON when export profiles enable TXT—not generative AI.

**Core mode does not prove full mode.** This document’s proof path is `--mode core` (factory profile `core_v1`, six candidates). Full menu (`default_v1`, sixteen candidates including classic optimizers and robust suite) is **available in code** but **not proven** by the documented core command unless a separate full run is executed and evidenced.

**Documentation note (2026-05-24):** glossary **Blocks 1–5 deliverable** vs **Decision package**;
`candidate_factory_run.json` vs `candidate_comparison.json` scope — [GLOSSARY.md](../../GLOSSARY.md),
[candidate_comparison_spec.md](../specs/candidate_comparison_spec.md),
[portfolio_review_workflow_spec.md](../specs/portfolio_review_workflow_spec.md) (cross-links),
[core/full artifact confusion audit](2026-05-23_core_full_artifact_documentation_confusion_audit.md).

---

## 1. Input data

### 1.1 What the user provides

The mandatory handoff input is **`config.yml`** at the project root. For the proof portfolio it contains:

- `tickers`: the eight ETF symbols  
- `analysis_subject`: `type: current_portfolio`, `id`, `display_name`, explicit `weights`  
- `investor_currency: USD`  
- `client_profile: Balanced`  
- Technical settings: windows (36/60/120 months), `market_data_provider: ibkr_yfinance_fallback`, `output_dir_final: "Main portfolio"`, etc.

Weights are **not** taken from `run_optimization.py` or `portfolio_weights.yml` on this path. The artifact records `weights_source: config.analysis_subject.weights`.

### 1.2 What the system resolves (not necessarily in raw config)

| Resolved field | Proof value | Mechanism |
| --- | --- | --- |
| Base benchmark | SPY | USD default via config resolution |
| Cash proxy | BIL | `resolve_cash_and_rf()` |
| Risk-free | FRED:DTB3 | USD default |
| Mandate targets | e.g. target vol 8.5%, max DD −20%, target return 6% | `config/client_profiles.yml` for Balanced |
| `analysis_end` | 2026-04-30 | **Computed** — last effective month-end strictly before today (`src/windows.get_analysis_end`), not a user-typed field in proof config |

### 1.3 Launch mode

| CLI | Effect |
| --- | --- |
| `--mode core` | Factory profile `core_v1` (six candidates) |
| `--skip-pdf` | PDF rebuild step omitted (default unless `--with-pdf` / `--legacy-full-pdf`) |
| Default `output_profile` | `site_api` — JSON/cache core contracts; CSV/TXT/HTML/PNG not written by default |

### 1.4 Mandatory vs optional input

**Mandatory for this path:**

- Valid `config.yml` with `analysis_subject` and positive weights  
- Tickers present in taxonomy YAML (`config/etf_universe.yml` / `config/stock_universe.yml`)

**Optional / legacy (empty in proof):**

- `current_weights` (legacy; proof uses `analysis_subject.weights`)  
- Optimizer-produced `portfolio_weights.yml` (not used on subject materialization path)

### 1.5 Resolved assumptions artifacts

After Block 1 completes in step 1 of the review:

| Artifact | Role |
| --- | --- |
| `Main portfolio/analysis_subject/run_metadata.json` → `analysis_setup` | **Runtime contract** (source of truth for resolved subject and assumptions) |
| Same file → `input_assumptions` | Exported reporting view (`src/input_assumptions.py`) |

Proof evidence: `resolution_status=resolved`, `weight_status.status=fully_invested`, `weight_sum=1.0`, `validation_result.status=valid`, `recommendation_status=diagnostic_current_portfolio_not_recommendation`.

**Reading caveat:** `input_assumptions.portfolio_input.current_weights_provided=false` does **not** mean weights are missing—it means legacy `current_weights` was empty while `analysis_subject.weights` supplied the portfolio.

---

## 2. Initial validation

### 2.1 Orchestration order

`run_portfolio_review.py` → `build_portfolio_review_plan()` → `run_portfolio_review_plan()` (`src/portfolio_review_workflow.py`):

1. **Diagnosis:** `run_report.py --materialize-analysis-subject --output-profile site_api`  
2. **Candidates:** `run_candidate_factory.py --profile core_v1 --execution-mode standard --output-profile site_api --then-compare`

**Not called on this path:** `run_optimization.py`, standalone `run_compare_variants.py`, `rebuild_pdf_reports.py` (when `--skip-pdf`).

### 2.2 Ticker validation

- Explicit subject tickers are checked against ETF/stock universe YAML (`preflight_explicit_analysis_subject_tickers` in `src/analysis_setup.py`).  
- Unknown ticker → `ConfigValidationError` → process stops.  
- Proof: eight tickers, no blocking errors.

### 2.3 Weight validation

Rules in `src/config_schema.py` and `src/analysis_setup.weight_status()`:

| Condition | Behavior | Recorded status |
| --- | --- | --- |
| Sum = 1.0 (±1e-6) | Proceed | `fully_invested` |
| Sum < 1.0 | **Allowed** — cash remainder | `partial_with_cash_remainder` |
| Sum > 1.0 | **Hard fail** | `ConfigValidationError` |
| All weights ≤ 0 | **Hard fail** | `ConfigValidationError` |
| Non-numeric or negative | **Hard fail** | `ConfigValidationError` |
| Weight for ticker not in subject list | **Hard fail** | `ConfigValidationError` |

**Decision owner:** code only (not AI, not human in the loop).

### 2.4 Benchmark and risk-free

- **USD (proof):** SPY and FRED:DTB3 applied by defaults—not missing.  
- **Non-USD:** metrics spec requires explicit risk-free; code is expected to fail fast if unavailable—**not exercised** on the proof portfolio in this document.

### 2.5 Where validation is recorded

| Check | Location in artifacts |
| --- | --- |
| Full setup | `run_metadata.json` → `analysis_setup` |
| Weight status | `analysis_setup.analysis_subject.weight_status` |
| Validation summary | `analysis_setup.validation_result` |
| Reporting projection | `run_metadata.json` → `input_assumptions` |

---

## 3. Required data

For each type: purpose, source, module, behavior if missing, fail vs degraded.

### 3.1 Asset prices

| | |
| --- | --- |
| Purpose | Monthly returns, metrics, stress historical PnL |
| Source | IBKR with yfinance fallback |
| Module | `src/data_loader.load_monthly_data_shared()`, `src/data_provider.py`, `src/data_yf.py` |
| Frequency | Daily Adj Close → effective month-end |
| If missing | Asset skipped in per-asset metrics; NaN-safe path uses cash proxy for missing months |
| Outcome | **Degraded** (warnings), not always hard fail |

### 3.2 Benchmark (SPY)

| | |
| --- | --- |
| Purpose | Portfolio beta, beta_base |
| Module | `data_loader` |
| If missing | Beta NaN; other metrics may still run |
| Outcome | **Degraded** |

### 3.3 Risk-free (FRED:DTB3)

| | |
| --- | --- |
| Purpose | Sharpe, Sortino, excess returns |
| Module | `src/data_fred.py` via `data_loader` |
| If missing | Expected hard fail for required metrics—**not live-verified** in this document |

### 3.4 Cash proxy (BIL)

| | |
| --- | --- |
| Purpose | NaN-safe portfolio return fallback |
| If missing | Zero cash return assumed (warning in `run_report.py`) |
| Outcome | **Degraded** |

### 3.5 FX

| | |
| --- | --- |
| Purpose | Convert prices to investor currency before returns |
| Module | `src/fx.convert_prices_to_investor_currency` |
| Proof | Not required (USD assets, USD investor) |
| FX forward-fill | Allowed for FX series; **asset returns are not interpolated** |

### 3.6 Factor data

| | |
| --- | --- |
| Purpose | Factor betas, synthetic attribution, regression inference |
| Sources | SPY, FRED series, DBC, VIX, etc. (`src/stress_factors.py`) |
| If missing | Factor block degraded; X-Ray factor section `unavailable` or `partial` |
| Proof artifact | `factor_diagnostics_meta.status=available`, 152 aligned weekly observations |

### 3.7 Historical stress windows

| | |
| --- | --- |
| Purpose | Realized episode PnL and max drawdown |
| Definitions | Hardcoded in `src/stress.HISTORICAL_EPISODES` |
| Data | Portfolio monthly returns (already computed) |
| If no aligned months | `data_quality=insufficient_data`, PnL null |
| Outcome | **Disclosed limitation** (not treated as code bug for proof holdings) |

### 3.8 Synthetic scenario definitions

| | |
| --- | --- |
| Purpose | Shock PnL |
| Source | In-code `SCENARIOS` + `recession_severe` in `src/stress.py` |
| Proof | `beta_coverage_ratio=1.0` for all eight assets |

### 3.9 Taxonomy / asset class metadata

| | |
| --- | --- |
| Purpose | X-Ray allocation; equal-weight-by-class; risk budget by class |
| Source | `config/etf_universe.yml`, `config/stock_universe.yml` |
| If missing for ticker | Excluded per `risk_budgeting.missing_taxonomy` policy |
| Outcome | **Degraded** for affected constructions |

### 3.10 Candidate builder inputs

| | |
| --- | --- |
| Purpose | Alternative portfolio weights |
| Source | Shared monthly panel, config universe, `risk_budgeting` targets |
| Module | `src/candidate_weights.py`, `src/portfolio_variants.py` |
| If infeasible | Builder `FAIL_*` → factory step `failed` (whole review continues unless `--fail-fast`) |

---

## 4. From prices to calculations

### 4.1 Price → return chain

1. Download daily **adjusted close**.  
2. Resample to **effective month-end** — last trading day per calendar month (`src/resample.to_month_end`).  
3. **Simple return:** `r_t = P_t / P_{t-1} - 1` (`src/returns.py`).  
4. **Log return** for skew/kurt diagnostics only.

Main metrics always use **monthly** cadence (`resolve_returns_frequencies` may force non-monthly config to monthly for main metrics).

### 4.2 analysis_end

From monthly price index: last month-end **strictly before today** → proof **2026-04-30**. All panels truncated with `truncate_to_analysis_end`.

### 4.3 Alignment

- **Inner join** for beta/Sharpe: dates where portfolio, rf, and benchmark all have values.  
- **Aligned observations** for historical stress: months where all assets have returns after `dropna(how="any")`.  
- **Calendar windows** 36/60/120 months ending at `analysis_end` (row count may be less than horizon if gaps exist).

### 4.4 Dynamic NaN-safe portfolio returns

Default `backtest_mode=dynamic_nan_safe` (`src/portfolio_dynamic.portfolio_returns_nan_safe`):

- Valid return at month *t* → use target weight.  
- NaN return → weight 0 for that asset at *t*.  
- Missing weight mass → **cash proxy BIL** return.  
- Optional redistribution among risk tickers when configured.

Young ETFs: shorter history → more NaN months → more cash fallback → shorter effective samples for some windows.

### 4.5 Where `insufficient_data` appears

Assigned by **code** when observation counts or coverage fail thresholds—for example:

- Historical stress: `n_obs < 2` (`_historical_data_quality` in `src/stress.py`).  
- Tail risk: too few daily observations (`src/portfolio_analytics.compute_tail_risk_historical`).  
- Scenario library normalized tiers (`src/scenario_library_normalized.py`).

**Not assigned by AI.**

---

## 5. Portfolio X-Ray (Block 2)

`portfolio_xray.json` is produced by `build_portfolio_xray_v2()` (`src/portfolio_xray.py`), invoked from `src/snapshot._xray_summary_from_output_dir()` after snapshots exist. X-Ray **summarizes** pipeline outputs; it does not re-run the metrics engine. Disclaimer in JSON: diagnostic-only—no optimization, selection, or trade instructions.

### 5.1 Allocation breakdown

| | |
| --- | --- |
| Input | Analyzed weights, taxonomy YAML |
| Rule | Join ticker → asset_class, region, sector, risk_role, risk_bucket |
| Output | `sections.asset_allocation` — holdings and breakdown rows |
| Failure | Missing taxonomy → warnings |
| Status | Code: `_section()` → `available` / `partial` / `unavailable` |
| AI | No |

Proof: `asset_allocation.status=available`, eight holdings, top weight SCHD 17%.

### 5.2 Asset class breakdown

Same section: `type: breakdown` rows for asset_class, region, currency_exposure, sector, risk_role, risk_bucket.

### 5.3 Portfolio metrics

| | |
| --- | --- |
| Input | Precomputed metrics in `snapshot_*`, tail risk block |
| Output | `sections.risk_diagnostics` — CAGR, vol, Sharpe, Sortino, beta, MDD, VaR/ES |
| Status owner | Code |

Proof 10Y (from artifacts): CAGR ≈ 9.9%, vol ≈ 9.6%, Sharpe ≈ 0.80, Sortino ≈ 1.29, beta ≈ 0.51, max DD ≈ −19.8%.

### 5.4 Risk contribution

| | |
| --- | --- |
| Input | RC_vol from `src/risk_contrib.rc_vol_window` |
| Rule | Percentage contribution to **portfolio variance** (not volatility), mean over months in window |
| Output | `sections.risk_budget_view`, `legacy_summary.risk_contribution_summary` |
| Note | Diagnostic only—not an optimizer gate (stated in artifact disclaimer) |
| Status owner | Code |

Proof top RC: SCHD, QQQ, SLV among largest contributors.

### 5.5 Factor diagnostics

| | |
| --- | --- |
| Input | `stress_report.json` — betas 5Y/10Y, Kalman, variance decomposition, regression inference |
| Output | `sections.factor_exposure` items per `beta_key` |
| Status rules | No items → `unavailable`; items without inference panels → **`partial`** + warning; else `available` |
| Status owner | Code (`_factor_exposure_section`) |
| AI | No |

Proof (on-disk subject run): `factor_exposure.status=available`, eight production factor keys in `factor_diagnostics_meta`. An earlier verification snapshot recorded `partial` when inference panels were missing—status logic is unchanged; artifact content can differ between runs.

### 5.6 Data trust signals

| | |
| --- | --- |
| Input | validation_result, young ETF policy, stress gaps |
| Module | `src/data_trust_signals.py` |
| Output | `user_summary_lines` and related blocks in xray / input_assumptions |
| Status owner | Code (rule-based text assembly) |
| AI | No |

### 5.7 Warnings and partial status

`_section()` logic:

- No items → `unavailable`  
- Items + non-empty warnings → **`partial`**  
- Items, no warnings → `available`

---

## 6. Metrics

Per `docs/specs/metrics_specification.md`, implemented in `src/metrics_asset.py` and `src/metrics_portfolio.py`. **ddof=1** for std/cov/beta. Rounding to **3 decimal places** at export only.

| Metric | Data | Window | Computation (concept) | Written to |
| --- | --- | --- | --- | --- |
| CAGR | Monthly simple returns | 3Y / 5Y / 10Y calendar | Equity = cumprod(1+r); CAGR = (Equity_end/Equity_start)^(12/N) − 1 | `snapshot_*`, xray |
| Volatility | Monthly simple r | Same | std(r, ddof=1) × √12 | Same |
| Sharpe | r, rf | Same, inner join | mean(r−rf)×12 / (std(r)×√12); vol denominator uses raw r | Same |
| Sortino | r, rf/MAR | Same | Downside deviation vs MAR (default MAR = rf) | Same |
| Max Drawdown | Monthly equity curve | Same | Peak-to-trough on cumprod | Same |
| Beta | Portfolio vs SPY | Same | cov(r_p, r_b)/var(r_b), ddof=1 | Same |
| VaR | Daily portfolio returns | Per tail-risk window | Historical quantile | xray `tail_risk` |
| Expected Shortfall | Daily portfolio returns | Same | Mean loss beyond VaR threshold | xray `tail_risk` |
| RC_vol | Monthly asset returns, weights panel | Per window | Mean monthly PC to variance | snapshot, CSV if export enabled |

**Per-asset metrics:** skipped when coverage in window < `coverage_threshold` (default 0.9)—warning, not full pipeline stop.

**Portfolio metrics:** computed on the NaN-safe portfolio return series.

---

## 7. Stress Test Lab (Block 3)

Producer: `run_stress()` in `src/stress.py` → `Main portfolio/analysis_subject/stress_report.json`.

### 7.1 Synthetic scenarios

Eight scenarios in `SCENARIOS` plus calibrated **recession_severe**. For each:

1. Apply shock vector to asset factor betas.  
2. Aggregate to portfolio PnL (`portfolio_pnl_pct`).  
3. Optional stressed covariance blend (`stress_covariance_taxonomy_blend`).  
4. Report `pnl_by_asset_pct`, `pnl_by_factor_pct`, RC Top1/Top3 (diagnostics only).  
5. **`pass`** = portfolio PnL vs client max drawdown threshold (same as `loss_ok`). RC does **not** change pass/fail.

Proof: worst synthetic loss ≈ −22.16% on `recession_severe`; `status=DIAG_ATTENTION`, `failed_scenario=recession_severe`, `failed_test=Loss`. These are **diagnostic codes** (`DIAG_*`), not legacy mandate `FAIL_*` from policy optimization.

### 7.2 Historical scenarios

Episodes: dotcom, 2008, 2020, 2022, banking_2023 (`HISTORICAL_EPISODES`).

**Primary path:** realized portfolio monthly returns only (`HISTORICAL_PRIMARY_RETURN_METHOD=realized_portfolio_monthly`). Proxy waterfalls are **not** applied in the primary stress artifact (disclosed in `_historical_methodology_block`).

Per episode:

1. Slice returns to episode dates.  
2. `dropna(how="any")` across assets → `n_obs`.  
3. `_historical_data_quality(n_obs, n_expected_obs)` → quality label.  
4. If `n_obs < 2`: PnL null, `data_quality=insufficient_data`.  
5. Else: compound PnL, max drawdown, pass vs mandate.

Proof results:

| Episode | n_obs | data_quality | pnl_real_episode |
| --- | --- | --- | --- |
| dotcom | 0 | insufficient_data | null |
| 2008 | 0 | insufficient_data | null |
| 2020 | 3 | reliable | −0.78% |
| 2022 | 12 | reliable | −16.29% |
| banking_2023 | 4 | reliable | +0.72% |

### 7.3 dotcom / 2008 — bug or normal?

**Normal data limitation** for current ETF holdings: no aligned monthly observations across all eight assets in those date ranges. Code records `insufficient_data` and plain-English disclosure in `data_trust_summary`. This is **not** evidence of a stress-engine bug for the primary realized-only path.

### 7.4 Who writes `insufficient_data`?

**Python code** in `src/stress.py` (and related modules)—**not** AI, **not** human judgment in the pipeline.

### 7.5 Factor beta estimation and attribution

- Weekly OLS; windows 5Y (~260 weeks) and 10Y (~520 weeks) per `src/stress_factors.py`.  
- HAC/Newey-West inference in `stress_report` (mandatory per project rules).  
- `pnl_by_factor_pct` on synthetic rows from beta × shock mapping.  
- Rolling 3Y/5Y/10Y summaries in JSON; CSV/PNG/HTML only if output profile enables export.

### 7.6 Worst scenario and loss drivers

Code selects minimum `portfolio_pnl_pct` across synthetic scenarios. `stress_conclusions` includes worst synthetic scenario id, top loss assets, and top factor drivers.

### 7.7 Hedge gap

`hedge_gap_analysis` in `src/stress.py` compares holdings with hedge `risk_role` labels (e.g. `crisis_hedge`, `inflation_hedge`) against scenario outcomes. Status such as `not_applicable` when no hedge labels—**rule-based**, documented in stress spec/tests.

### 7.8 Data trust summary

`build_stress_data_trust_summary()` — code-generated episode flags and promoted warnings (template strings, not LLM).

---

## 8. Candidate Portfolio Factory (Block 4)

Runs after subject diagnostics exist.

### 8.1 Core mode

`--mode core` → factory profile **`core_v1`** (`REVIEW_MODE_PROFILES` in `src/candidate_factory.py`).

**Six candidates:**

| ID | Construction (high level) |
| --- | --- |
| `equal_weight` | 1/N on eligible universe |
| `risk_parity` | Equalize RC_vol; Spinu + Ledoit-Wolf cov |
| `equal_weight_by_asset_class` | Equal across taxonomy buckets, then within bucket |
| `risk_budget_by_asset` | SLSQP vs per-asset targets in `config.risk_budgeting.asset_targets` |
| `risk_budget_by_asset_class` | SLSQP vs class targets from balanced preset |
| `hierarchical_risk_parity` | HRP clustering + recursive bisection |

### 8.2 Not built in core mode

From `default_v1` (sixteen candidates) but **excluded** from `core_v1`:

- minimum_variance, minimum_variance_uncapped, minimum_variance_advanced  
- maximum_diversification, maximum_diversification_uncapped  
- minimum_cvar_constrained, minimum_cvar_uncapped  
- robust_mv_constrained, robust_mv_uncapped, robust_scenario  

### 8.3 Core vs full

| | core_v1 | default_v1 |
| --- | --- | --- |
| Menu size | 6 | 16 |
| CLI | `--mode core` | `--mode full` |
| Classic/robust optimizers | No | Yes |
| Proven by this document | **Yes (core path only)** | **No** |

### 8.4 Execution mode `standard` (portfolio-first default)

1. **Weights phase:** in-process `build_candidate_weights()` → `src/portfolio_variants.py` (no subprocess `run_*.py`).  
2. **Report phase:** `run_portfolio_report_for_weights(..., report_profile=lightweight_comparison)` → minimum `snapshot_10y.json` per candidate folder.

PDF suppressed (`pdf_mode=none`).

### 8.5 fresh / reused / skipped / failed / stale

| Term | Meaning |
| --- | --- |
| **fresh** | `snapshot_10y.json` matches expected `analysis_end` and config fingerprint |
| **stale** / **stale_config** | Snapshot end date or fingerprint mismatch → rebuild when not skipping |
| **skipped_existing** | Fresh snapshot present → builder and report skipped |
| **reused_existing_snapshot** | `execution_action` documenting reuse |
| **succeeded** | Builder ran and wrote new artifacts |
| **failed** | Builder returned FAIL_CONFIG / FAIL_DATA / FAIL_INFEASIBLE_* |

Recorded in **`Main portfolio/candidate_factory_run.json`** (`steps[]`, `summary`).

Proof factory run: all six steps `skipped_existing`, `freshness_status=fresh`, `summary.skipped_existing=6`, `succeeded=0`—factory verified freshness and did not rebuild.

**Reuse disclosure:** factory step records `message`, `snapshot_analysis_end`, `expected_analysis_end`, `config_fingerprint`, and comparison `candidate_menu.factory_execution_summary`—reuse is explicit in JSON, not silent.

### 8.6 `--then-compare`

Factory calls `write_candidate_comparison_outputs()` → rebuilds **`candidate_comparison.json`**. Standalone `run_compare_variants.py` is not a separate orchestrator step when `--then-compare` is set.

---

## 9. Optimization Engine within Blocks 1–5

### 9.1 `run_optimization.py`

**Not called** on portfolio-first core path (`src/portfolio_review_workflow.py` has no reference to it).

### 9.2 What participates in core path

**In-process candidate builders** in `src/portfolio_variants.py` (risk parity, risk budgets, HRP use numerical optimization). This is factory-level construction, not legacy Main policy optimization.

### 9.3 Optimizer-backed candidates in core

**None** of the named classic/robust optimizer candidates are in `core_v1`.

### 9.4 Full mode (available, not proven here)

`default_v1` adds ten candidates (min var, max div, min CVaR, robust MV, robust scenario, etc.). Artifacts for those folders may exist on disk from **prior** full runs; the documented core command does not prove their freshness in the same run.

---

## 10. Artifacts

### 10.1 Artifact map

| Path | Creator | Purpose | Machine-readable | SoT for run | Used by later code |
| --- | --- | --- | --- | --- | --- |
| `analysis_subject/run_metadata.json` | `export_run_metadata` | Resolved config, `analysis_setup`, `input_assumptions` | Yes | **Yes** | Compare, xray |
| `analysis_subject/data_policy.json` | `export_data_policy` | NaN/backtest disclosure | Yes | Yes | Trust signals |
| `analysis_subject/snapshot_{3y,5y,10y}.json` | `save_snapshot` | Window metrics, weights, RC | Yes | Yes | Compare |
| `analysis_subject/snapshot_index.json` | `save_snapshot` | Snapshot index | Yes | Meta | Navigation |
| `analysis_subject/stress_report.json` | `export_stress_report` | Stress + factors | Yes | **Yes** | Xray, compare |
| `analysis_subject/portfolio_xray.json` | `snapshot._xray_summary_from_output_dir` | X-Ray v2 sections | Yes | Diagnostic SoT | Commentary if TXT exported |
| `analysis_subject/output_manifest.json` | `write_output_manifest` | Output profile, paths written | Yes | Meta | Ops |
| `analysis_subject/scenario_library*.json` | scenario builders | Extended scenario analytics | Yes | Diagnostic | Optional |
| `candidate_factory_run.json` | factory | Factory steps, freshness | Yes | **Yes** | Compare menu |
| `candidate_factory_manifest.json` | factory | Resume checksum | Yes | Yes | Resume |
| `candidate_comparison.json` | `write_candidate_comparison_outputs` | Compare + readiness | Yes | Readiness evidence | Blocks 6+ (out of scope) |
| `{candidate}/snapshot_10y.json` | lightweight report | Candidate compare input | Yes | Yes | Compare |
| `{candidate}/candidate_manifest.json` | factory | Per-candidate step | Yes | Yes | Factory audit |
| `commentary.txt`, `*.csv`, `*.html`, `*.png` | report exporters | Human presentation | Mixed | No | Human only |

### 10.2 PDF and `--skip-pdf`

| Question | Answer |
| --- | --- |
| Is PDF part of the core algorithm? | **No.** PDF is produced by `rebuild_pdf_reports.py`, a separate presentation/export step. |
| What does `--skip-pdf` do? | Omits that step; calculations and JSON still run. |
| Does `--skip-pdf` break math? | **No.** |
| Machine-readable layer | **JSON** contracts under `analysis_subject/`, factory run, comparison, snapshots (`src/output_policy.py`: `site_api` writes JSON, not CSV/TXT/HTML/PNG/PDF by default). |

**Note:** Presentation files (CSV, HTML, commentary.txt) may remain on disk from earlier `full_report` or `legacy_export` runs—they are **not guaranteed refreshed** on `site_api` + `--skip-pdf` path.

### 10.3 Downstream artifacts (boundary only)

These may appear under `Main portfolio/` but are **after Blocks 1–5**:

- `selection_decision.json`, `action_plan.json`, `decision_package_summary.json`, `decision_journal.json`, `pdf files/*.pdf`

---

## 11. Decision table

| Step | What is decided | Who decides | Input | Output | Fully algorithmizable? | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Weight validation | Pass/fail load | **Code** | config weights | valid / error | Yes | `config_schema.py` |
| analysis_end | Cutoff date | **Code** | month-end index | date string | Yes | `windows.py` |
| Data sufficiency (coverage) | Skip asset / warn | **Code** | return panel | warnings | Yes | `coverage_ratio` |
| Metric values | CAGR, vol, … | **Formula + code** | aligned returns | numbers | Yes | `metrics_*.py` |
| Factor exposure status | available / partial / unavailable | **Code rules** | stress_report | xray section | Yes | `portfolio_xray.py` |
| Synthetic stress PnL | Loss % | **Code** | betas, shocks | scenario_results | Yes | `stress.py` |
| Stress pass (loss gate) | pass, DIAG_* | **Code rules** | PnL vs mandate DD | pass, codes | Yes | `stress.py` |
| insufficient_data | Episode quality | **Code rules** | n_obs, coverage | string | Yes | `_historical_data_quality` |
| Worst scenario | Min PnL id | **Code** | scenario_results | worst_* fields | Yes | `stress.py` |
| Candidate build vs skip | fresh / skip / build | **Code rules** | snapshot, fingerprint | factory step | Yes | `candidate_factory.py` |
| Candidate readiness | ready / degraded | **Code checklist** | artifacts | optimization_readiness | Yes | `optimization_readiness.py` |
| Final investment recommendation | Which portfolio to implement | **Outside Blocks 1–5** | — | selection artifacts | N/A | Not produced by core review |
| AI / LLM | Any Blocks 1–5 decision | **None** | — | — | N/A | No LLM in `*.py` |

---

## 12. Algorithmization analysis

### A. Fully deterministic code

Config validation; price→return; month-end and truncation; NaN-safe portfolio series; metric formulas; RC_vol and correlation; synthetic stress PnL; historical stress when data exists; factor OLS/HAC; rolling beta summaries; factory freshness checks; JSON serialization.

### B. Rule-based / heuristic

X-Ray archetype, weakness map, hidden-risk flags (`XRAY_THRESHOLDS`); stress `DIAG_*` vs mandate thresholds; historical quality bands; X-Ray `partial`/`unavailable`; `candidate_menu.is_partial_menu`; hedge gap status; template commentary and data_trust plain-English lines.

### C. Data-dependent (still code-owned)

Whether dotcom/2008 compute; depth of factor coverage; tail risk availability; per-asset coverage pass; factory skip vs rebuild.

### D. AI-suitable (not implemented in Blocks 1–5)

Client narrative explaining structured JSON; educational summaries. Could use LLM **outside** this pipeline on exported JSON—**not in current code**.

### E. AI should not decide

Data sufficiency labels; metric values; stress losses; pass/fail; factory status; optimizer readiness. Current implementation aligns with this boundary—no LLM in the calculation path.

---

## 13. Main conclusion

### Can Blocks 1–5 be described as an algorithm?

**Yes.** One ordered command runs a fixed sequence: validate → load data → returns → metrics → stress → xray → factory → comparison JSON. The process is reproducible given the same config, data, and code version.

### What is already algorithmic?

Groups A and B above constitute the vast majority of Blocks 1–5. **No AI participates in calculation or status assignment.**

### Where confusion can appear (evidence-based)

1. **Mixed artifacts:** core factory run with sixteen-candidate product menu still on disk—`candidate_comparison.json` may list nineteen rows while `intended_menu_size=6` and `is_partial_menu=true`.  
2. **Legacy naming:** `analysis_mode=optimize_from_universe` in metadata alongside `current_portfolio` subject.  
3. **Presentation vs JSON:** stale CSV/HTML/commentary beside fresh JSON when `site_api` and `--skip-pdf` are used.  
4. **DIAG_* vs mandate FAIL:** stress attention on subject path is diagnostic, not production gate.  
5. **External LLM** interpreting JSON without reading `candidate_menu` or `data_trust_summary`.

### If “AI goes in circles”

This is **not** explained by Blocks 1–5 pipeline code (no LLM). Likely layers: **artifact mixing**, **report/presentation**, **external prompt/human interpretation**, or **documentation** of core vs full scope.

### Clarity priorities (caveats already identified— not new features)

When reading outputs from the proof path:

1. Use `run_metadata.json` → `analysis_setup` as the input contract.  
2. Read `candidate_menu.review_mode` and `is_partial_menu` before interpreting `candidate_comparison.json`.  
3. Use `stress_report.data_trust_summary` for historical gaps—not inference.  
4. Under `--skip-pdf` + `site_api`, trust JSON timestamps; do not assume adjacent TXT/PDF/CSV are from the same run.

---

## Related document

Technical module reference (same evidence standard): [2026-05-23_blocks_1_5_actual_algorithm_walkthrough.md](2026-05-23_blocks_1_5_actual_algorithm_walkthrough.md).

---

## Verification log (this document)

| Check | Result |
| --- | --- |
| Code/docs alignment | Based on `portfolio_review_workflow.py`, `run_report.py`, `stress.py`, `portfolio_xray.py`, `candidate_factory.py`, `output_policy.py`, proof artifacts |
| Entrypoint grep | Confirmed in prior session: review → materialize-analysis-subject → core_v1 factory; no `run_optimization.py` |
| Live core re-run | **Not performed** for this file creation |
| DOCX | **Not created** (not requested in this task) |
