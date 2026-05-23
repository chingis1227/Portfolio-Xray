# Blocks 1–5 Actual Algorithm Walkthrough

Date: 2026-05-23  
Evidence basis: current repository code, canonical specs under `docs/specs/`, and generated artifacts from the proof portfolio on disk (`Main portfolio/`). Target product concepts (including `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`) are cited only where explicitly non-binding.

Proof portfolio (from `config.yml` and `Main portfolio/analysis_subject/run_metadata.json`):

| Field | Value |
| --- | --- |
| Tickers | SPY, QQQ, GLD, SLV, BND, SCHD, SCHP, TLT |
| Weights | SPY 10%, QQQ 13%, GLD 9%, SLV 9%, BND 16%, SCHD 17%, SCHP 13%, TLT 13% |
| `analysis_subject.type` | `current_portfolio` |
| `investor_currency` | USD |
| Base benchmark | SPY |
| `client_profile` | Balanced |
| `analysis_end` (resolved) | 2026-04-30 |

Preferred proof command (verified via dry-run):

```bash
python run_portfolio_review.py --mode core --skip-pdf
```

---

## 0. Scope and non-scope

This document covers **Blocks 1–5 only**:

1. Input & Assumptions  
2. Portfolio X-Ray  
3. Stress Test Lab  
4. Candidate Portfolio Factory  
5. Optimization Engine / candidate generation readiness  

**Explicitly excluded** (mentioned only if they appear as downstream generated files on disk):

- Selection Engine  
- Action Engine / Action Plan  
- Monitoring  
- Decision Journal  
- Final investment recommendation logic  
- Full interactive UI  
- PDF polish and client-facing narrative packaging beyond noting their role  

Blocks 6+ artifacts such as `decision_package_summary.json`, `action_plan.json`, and `selection_decision.json` may exist under `Main portfolio/` from prior runs but are **not** part of the Blocks 1–5 algorithm described here.

**Documentation note (2026-05-24):** glossary terms **Blocks 1–5 deliverable** vs **Decision package**
and factory/comparison evidence boundaries live in [GLOSSARY.md](../../GLOSSARY.md). The same
`run_portfolio_review.py` command can write decision JSON without making those files part of this
walkthrough’s scope. `candidate_factory_run.json` ≠ `candidate_comparison.json` scope — see
[candidate_comparison_spec.md](../specs/candidate_comparison_spec.md) and the
[core/full artifact confusion audit](2026-05-23_core_full_artifact_documentation_confusion_audit.md).

---

## 1. Executive summary

The current Blocks 1–5 path is a **CLI-orchestrated, deterministic Python pipeline**. A single command (`run_portfolio_review.py`) runs existing entrypoints in a fixed order; it does not embed portfolio math itself.

| Layer | What it is | Blocks 1–5 evidence |
| --- | --- | --- |
| **Deterministic code** | Config validation, assumption resolution, market-data load, return construction, metrics, RC_vol, stress PnL, factor betas (OLS/HAC), X-Ray section assembly, candidate weight builders, factory orchestration, comparison/readiness JSON | `run_report.py`, `src/analysis_setup.py`, `src/stress.py`, `src/portfolio_xray.py`, `src/candidate_factory.py`, `src/candidate_weights.py` |
| **Rule-based / heuristic** | X-Ray archetype and weakness-map thresholds; stress pass/fail vs mandate MaxDD; historical episode quality bands; factory freshness/skip rules; optimization readiness checklist | `src/portfolio_xray.py` (`XRAY_THRESHOLDS`), `src/stress.py`, `src/candidate_factory.py`, `src/optimization_readiness.py` |
| **AI / LLM** | **Not used** in Blocks 1–5 | Repository-wide search for `openai`, `anthropic`, `gpt-`, `llm` in `*.py` returned **no matches**. Commentary (`src/portfolio_commentary.py`) is template/rule-generated from JSON, not LLM text. Specs state scorecard bullets are not LLM-generated (`docs/specs/portfolio_health_score_spec.md`). |

**Bottom line:** The current path is **algorithmic and file-driven**, not AI-driven. LLM could only appear downstream in human interpretation of exported JSON/TXT/PDF; the calculation and status layers in Blocks 1–5 are code-owned.

**Important boundary:** Blocks 1–5 **diagnose and prepare candidates**; they do **not** emit a final “buy this portfolio” decision. Even stress `DIAG_*` codes are diagnostic; mandate `FAIL_*` gating applies to legacy policy optimization, not to the portfolio-first subject path (`SPEC.md`, `src/stress.py` module docstring).

---

## 2. Entry point and execution path

### 2.1 Command

```bash
python run_portfolio_review.py --mode core --skip-pdf
```

Defaults (from `run_portfolio_review.py` + `src/portfolio_review_workflow.py`):

- `review_mode=core` → factory profile `core_v1`  
- `skip_pdf=True` (PDF skipped unless `--with-pdf` or `--legacy-full-pdf`)  
- `output_profile=site_api` (JSON/cache core contracts; no CSV/TXT/HTML/PNG by default)  
- Candidates **not** skipped (`skip_candidates=False`)  
- Comparison **not** skipped (`skip_compare=False`)  
- Factory `--then-compare` enabled (comparison runs inside factory, not as a separate orchestrator step)

### 2.2 Verified stage order (dry-run output)

```
input → diagnosis → candidates
```

| Stage | Script / module | Blocking? | Produces |
| --- | --- | --- | --- |
| **diagnosis** | `run_report.py --materialize-analysis-subject --output-profile site_api` | **Yes** — non-zero exit stops workflow | `Main portfolio/analysis_subject/*` JSON contracts |
| **candidates** | `run_candidate_factory.py --profile core_v1 --execution-mode standard --output-profile site_api --then-compare` | **Yes** on factory failure (`fail_fast` optional) | `Main portfolio/candidate_factory_run.json`, per-candidate snapshots, `Main portfolio/candidate_comparison.json` |

### 2.3 What is **not** called on this path

| Entrypoint | Called? | Evidence |
| --- | --- | --- |
| `run_optimization.py` | **No** | `build_portfolio_review_plan()` never references it; factory label explicitly says “without legacy policy optimization” |
| `run_report.py` (legacy Main/policy weights path) | **No** | Only `--materialize-analysis-subject` |
| `run_compare_variants.py` | **No** (standalone) | Comparison invoked via factory `--then-compare` → `run_then_compare()` in `src/candidate_factory.py` |
| `rebuild_pdf_reports.py` | **No** | Omitted when `skip_pdf=True` |

### 2.4 Internal diagnosis pipeline (equivalent reporting)

`run_report.py --materialize-analysis-subject` calls `run_materialize_analysis_subject_report()` → `run_portfolio_report_for_weights()` with:

- `output_dir_final = {cfg.output_dir_final}/analysis_subject` (default `Main portfolio/analysis_subject/`)  
- `portfolio_role_override = "analysis_subject"`  
- Weights from `resolve_analysis_subject_materialization(cfg)`  

This is the **same core metrics/stress/report pipeline** used for candidate reports, parameterized by explicit weights (`run_report.py` docstring lines 301–323).

### 2.5 Where candidate factory begins

After subject diagnostics exist, `run_candidate_factory()` (`src/candidate_factory.py`):

1. Resolves candidate IDs from profile (`core_v1` → 6 builders)  
2. For `execution_mode=standard`: in-process **weights phase** + **lightweight_comparison report phase** per candidate  
3. On success with `--then-compare`: `write_candidate_comparison_outputs()` rebuilds `candidate_comparison.json`

### 2.6 Flow diagram (code-accurate)

```text
config.yml + analysis_subject
  → load_validated_config() / ConfigValidationError
  → resolve_analysis_subject (analysis_setup)
  → run_report.py --materialize-analysis-subject
       → load_monthly_data_shared()
       → portfolio_returns_nan_safe()
       → asset/portfolio metrics, RC_vol, correlation
       → run_stress() + factor pipeline
       → export run_metadata, stress_report, snapshots, portfolio_xray
  → run_candidate_factory.py --profile core_v1 --execution-mode standard --then-compare
       → per candidate: build/reuse weights → lightweight report → snapshot_10y.json
       → candidate_factory_run.json
       → candidate_comparison.json (readiness + menu metadata)
```

---

## 3. Input contract

### 3.1 Proof portfolio configuration

Configured in root `config.yml`:

```yaml
analysis_subject:
  type: current_portfolio
  id: analysis_subject
  display_name: Current Portfolio
  weights: { SPY: 0.10, QQQ: 0.13, ... }

investor_currency: USD
client_profile: Balanced
tickers: [SPY, QQQ, GLD, SLV, BND, SCHD, SCHP, TLT]
```

Derived at runtime (not necessarily in raw config):

- `base_benchmark_ticker`: SPY (USD default)  
- `cash_proxy_ticker`: BIL (via `resolve_cash_and_rf()`)  
- `risk_free_source`: FRED:DTB3 (USD)  
- `windows_months`: [36, 60, 120]  
- Mandate targets from `config/client_profiles.yml` for Balanced (e.g. `target_vol_annual=0.085`, `target_max_drawdown_pct=-0.2` in artifact)

### 3.2 Allowed `analysis_subject` types

From `src/analysis_setup.py`:

- `current_portfolio`  
- `model_portfolio`  
- `universe_baseline` (equal-weight if weights omitted)

### 3.3 Weight format and validation

| Check | Where | Behavior |
| --- | --- | --- |
| Numeric non-negative weights | `src/config_schema.py` | `ConfigValidationError` if non-numeric or negative |
| Sum > 1.0 | `src/config_schema.py` | **Blocked** (`ConfigValidationError`) for weighted subject types |
| Sum ≤ 0 | `src/config_schema.py` | **Blocked** |
| Sum < 1.0 (cash remainder) | `src/analysis_setup.weight_status()` | Allowed; status `partial_with_cash_remainder` |
| Sum = 1.0 | `weight_status()` | `fully_invested` |
| Unknown tickers | `preflight_explicit_analysis_subject_tickers()` | **Blocked** if not in ETF/stock universe YAML |

Proof artifact: `run_metadata.json` → `analysis_setup.analysis_subject.weight_status.status="fully_invested"`, `weight_sum=1.0`, `validation_result.status="valid"`.

### 3.4 Missing inputs

| Missing input | Behavior |
| --- | --- |
| Empty `analysis_subject.weights` for `current_portfolio` | Config validation error before run |
| Missing benchmark for non-USD without explicit config | Fail-fast in data/rf resolution (per metrics spec) |
| Missing risk-free for non-USD | Fail-fast (`portfolio-metrics` rules) |
| Missing ticker price data | Asset skipped in metrics; NaN-safe portfolio return uses cash proxy for missing months |

### 3.5 Resolved input artifact

Primary machine-readable contract:

- **`Main portfolio/analysis_subject/run_metadata.json`**  
  - Embeds `analysis_setup` (runtime contract)  
  - Embeds `input_assumptions` (exported reporting view via `src/input_assumptions.py`)  
  - `active_assumptions` / `resolved_config` for audit trail  

`input_assumptions.portfolio_input.current_weights_provided=false` is **expected** when weights come from `analysis_subject.weights`, not legacy `current_weights` (documented confusion in prior verification report).

---

## 4. Data requirements and data collection

### 4.1 Required market data (proof run, USD)

| Data | Source | Module | Frequency | Notes |
| --- | --- | --- | --- | --- |
| Asset prices | IBKR with yfinance fallback (`market_data_provider: ibkr_yfinance_fallback`) | `src/data_provider.py`, `src/data_yf.py` | Daily **Adj Close** | Converted to investor currency before returns |
| Base benchmark SPY | Same | `src/data_loader.py` | Daily → month-end | Used for beta_base |
| Cash proxy BIL | Same | `resolve_cash_and_rf()` | Daily → month-end | NaN-safe fallback return |
| Risk-free DTB3 | FRED | `src/data_fred.py` | Daily → month-end effective | `(1+y/100)^(1/12)-1` monthly |
| Local benchmarks | yfinance proxies per asset | `resolve_local_benchmarks()` | Monthly | Beta_local diagnostics |
| Factor series | SPY, FRED, DBC, etc. | `src/stress_factors.py` | Weekly (stress pipeline) | See artifact `factor_diagnostics_meta` |
| Stress scenario definitions | In-code `SCENARIOS`, `HISTORICAL_EPISODES` | `src/stress.py` | N/A | Not user-uploaded in V1 |

### 4.2 Processing chain

1. **Download** daily prices (`download_all_prices`)  
2. **FX convert** (`src/fx.convert_prices_to_investor_currency`) — forward-fill FX allowed; **never** interpolate asset returns  
3. **Resample** to effective month-end (`src/resample.to_month_end`) — last trading day per month  
4. **Returns** simple: `P_t/P_{t-1}-1` (`src/returns.py`)  
5. **analysis_end** = last month-end strictly before today (`src/windows.get_analysis_end`) → **2026-04-30** in proof artifact  
6. **Truncate** all panels to `analysis_end` (`truncate_to_analysis_end`)

### 4.3 Cache behavior

From `src/data_loader.py` + `run_report.py` docstring:

- **Daily cache**: raw prices; invalidated daily  
- **Monthly/panel cache**: returns/rf/benchmark; invalidated on month change or config fingerprint change  
- `--no-cache` bypasses cache reads  

### 4.4 Missing data behavior

| Situation | Behavior | Status producer |
| --- | --- | --- |
| Asset missing in window | Skipped in per-asset metrics if coverage < `coverage_threshold` (default 0.9) | Code (`coverage_ratio`, logs) |
| Missing cash proxy series | Zero cash return assumed | Code warning in `run_portfolio_report_for_weights` |
| Historical episode with no aligned months | `data_quality="insufficient_data"`, `n_obs=0` | **Code** (`src/stress._historical_data_quality`) |
| Factor regression unavailable | X-Ray section `unavailable` or `partial` | **Code** (`src/portfolio_xray._factor_exposure_section`) |

### 4.5 `insufficient_data` — code vs AI

**Answer: (A) code-generated data availability status.**

Examples:

- Historical stress: `_historical_data_quality()` returns `"insufficient_data"` when `n_obs < 2` or coverage rules fail (`src/stress.py` lines 586–596).  
- Scenario library normalized tiers: `"insufficient_data"` classification in `src/scenario_library_normalized.py`.  
- Tail risk: `unavailable_reason="insufficient_daily_obs_lt_{min_obs}"` in `src/portfolio_analytics.compute_tail_risk_historical`.

No LLM participates in assigning these strings. Commentary may **repeat** them in English prose (`src/portfolio_commentary.py`), still rule-based.

---

## 5. Return construction and alignment

### 5.1 Monthly metrics path (binding)

Despite configurable `returns_frequency`, main metrics are forced to **monthly** (`src/data_loader.py` docstring; `resolve_returns_frequencies()`).

### 5.2 FX

Rules in `src/fx.py` match `docs/specs/metrics_specification.md` (EURUSD=X orientation, USD pivot for non-USD investors).

### 5.3 Portfolio return (NaN-safe dynamic)

Default `backtest_mode=dynamic_nan_safe` (`run_report.py`):

Implementation: `src/portfolio_dynamic.portfolio_returns_nan_safe()`:

- At month *t*: use target weight if asset return non-NaN; else weight → 0  
- `w_miss` → cash proxy return  
- Optional redistribution among `risk_tickers` when configured  

Cash proxy aligned to monthly index; missing cash → zero return.

### 5.4 Alignment for metrics

- Excess-return metrics: **inner join** across portfolio, rf, benchmark (`src/metrics_asset._align`)  
- Covariance / RC_vol / correlation: synchronous observations on month-end simple returns, `ddof=1`  
- Windows: calendar `(analysis_end - horizon_months, analysis_end]` (`slice_calendar_window`)

### 5.5 analysis_end enforcement

Computed from loaded monthly index, not user-editable in proof config. Stored in every major artifact (`run_metadata.run_info.analysis_end_date`, snapshots, factory run).

---

## 6. Portfolio X-Ray algorithm

### 6.1 Producer

`portfolio_xray.json` is written by `src/snapshot._xray_summary_from_output_dir()` calling `build_portfolio_xray_v2()` after snapshots and `run_metadata` exist. It **summarizes** existing pipeline outputs; it does not recompute metrics (`src/portfolio_xray.py` disclaimer).

### 6.2 Schema

- Version: `portfolio_xray_v2`  
- Sections: `asset_allocation`, `risk_diagnostics`, `factor_exposure`, `hidden_risk_detector`, `portfolio_archetype`, `risk_budget_view`, `weakness_map`  
- Each section status: `available` | `partial` | `unavailable` via `_section()` — **`partial` iff items exist but warnings non-empty** (lines 285–290)

### 6.3 Section breakdown

| Section | Inputs | Calculation | Output | Degraded when |
| --- | --- | --- | --- | --- |
| **asset_allocation** | Weights, `config/etf_universe.yml`, `config/stock_universe.yml` | Taxonomy join per ticker; breakdown aggregations | Holdings, class/region/sector/risk_bucket weights | Missing taxonomy → warnings |
| **risk_diagnostics** | Portfolio metrics snapshots, tail risk block | Reads computed metrics / drawdown / tail risk | CAGR, vol, Sharpe, Sortino, beta, MDD, VaR/ES | Insufficient window obs → NaN fields |
| **factor_exposure** | `stress_report` factor betas, regression, decomposition | Maps beta keys to display names; attaches inference panels if present | Per-factor betas 5Y/10Y, residual share | No betas → `unavailable`; betas without inference → **`partial`** + warning |
| **hidden_risk_detector** | RC, PCA, stress RC, factor residual | Threshold rules (`XRAY_THRESHOLDS`) | Flagged concentration / factor gaps | Missing inputs → `unavailable` items |
| **portfolio_archetype** | Allocation + RC + stress | Rule-based classifier (equity/fi/balanced/defensive/concentrated) | Archetype label + evidence | Threshold-only |
| **risk_budget_view** | RC_vol, optional `risk_budgeting` config targets | Compares realized RC vs configured bucket targets | Asset and bucket RC rows | RC missing → degraded section |
| **weakness_map** | Factor betas, taxonomy, synthetic stress names | Maps weakness keys to scenarios/factors | Per-risk weakness rows | Unmapped factors listed explicitly |

### 6.4 Proof artifact state (2026-05-22 run on disk)

From `Main portfolio/analysis_subject/portfolio_xray.json`:

- `asset_allocation.status = "available"`  
- `factor_exposure.status = "available"` (12 items; 8 production factor keys present)  
- `stress_report.factor_diagnostics_meta.status = "available"`, `aligned_weekly_observations = 152`  

**Note:** An earlier verification snapshot (`docs/audits/2026-05-22_blocks_1_5_verification_report.md`) recorded `factor_exposure.status="partial"` for a prior artifact state. Current on-disk subject run shows full factor keys with regression panels present. Status logic is unchanged; artifact content differed between runs.

### 6.5 Partial factor exposure logic (code)

From `_factor_exposure_section()`:

1. Collect betas from `factor_betas_5y`, `factor_betas_10y`, Kalman, variance decomposition  
2. If **no items** → section forced to `unavailable` with reason from `factor_diagnostics_meta`  
3. If items exist but **`factor_regression_*` inference panels missing** → warning → section **`partial`**  
4. All inference present → **`available`**

---

## 7. Metrics algorithm

Formulas implemented in `src/metrics_asset.py` / `src/metrics_portfolio.py` per `docs/specs/metrics_specification.md`.

| Metric | Input | Frequency | Alignment | ddof | Annualization | Rounding | Output |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **CAGR** | Monthly simple returns, equity curve | Monthly | Window slice ending `analysis_end` | N/A | `(Equity_end/Equity_start)^(12/N)-1` | 3 dp at export | `snapshot_*`, `portfolio_xray`, CSV if enabled |
| **Vol** | Monthly simple returns | Monthly | Window slice | 1 | `std_monthly * sqrt(12)` | 3 dp | Same |
| **Sharpe** | Returns + rf | Monthly | Inner join excess | 1 (denom on raw returns) | `(mean(excess)*12)/(std*sqrt(12))` | 3 dp | Same |
| **Sortino** | Returns + rf/MAR | Monthly | Inner join | 1 | Uses downside deviation vs MAR | 3 dp | Same |
| **Max Drawdown** | Monthly equity curve | Monthly | Window slice | N/A | From cumprod | 3 dp | Same |
| **Beta (portfolio)** | Portfolio vs SPY | Monthly | Inner join | 1 | `cov/var` | 3 dp | Same |
| **VaR / ES** | Daily simple portfolio returns | Daily | Calendar window | Empirical quantile | Not annualized in tail block | 3 dp | `portfolio_xray` tail_risk item |
| **RC_vol** | Monthly returns + weights panel | Monthly | Per-month PC on variance | 1 | Mean of monthly PCs | 3 dp CSV | `rc_vol_*.csv` if export enabled; snapshot RC fields |
| **Correlation** | Monthly asset returns | Monthly | Same window as RC | 1 | N/A | 3 dp CSV | `correlation_matrix_*.csv` if enabled |

Tail risk method: historical simulation on daily returns (`TAIL_RISK_METHOD` in `src/portfolio_analytics.py`); unavailable if `n_obs < min_obs`.

---

## 8. Stress Test Lab algorithm

### 8.1 Producer

`run_stress()` in `src/stress.py`, invoked from `run_portfolio_report_for_weights()` after asset factor betas are computed. Exported via `export_stress_report()` to `stress_report.json`.

### 8.2 Synthetic scenarios

Defined in `SCENARIOS` dict (equity_shock, credit_shock, rates_shock, inflation_stagflation, liquidity_shock, usd_shock, commodity_shock) plus calibrated `recession_severe`.

Per scenario:

1. Asset betas (weekly OLS, cached daily returns path) × shock vector → portfolio PnL  
2. Optional stressed covariance blend (`stress_covariance_taxonomy_blend`)  
3. RC Top1/Top3 diagnostics (do **not** change pass/fail)  
4. **Pass** = portfolio PnL vs client `target_max_drawdown_pct` (loss gate)  

Proof artifact: 8 synthetic scenarios with `portfolio_pnl_pct`, `pnl_by_asset_pct`, `pnl_by_factor_pct`, `pass` boolean.

### 8.3 Historical episodes

Episodes in `HISTORICAL_EPISODES`: dotcom, 2008, 2020, 2022, banking_2023.

Primary path: **realized portfolio monthly returns only** (`HISTORICAL_PRIMARY_RETURN_METHOD = "realized_portfolio_monthly"`). No proxy waterfall in primary stress artifact.

Algorithm per episode (`run_stress` loop):

1. Slice monthly returns to episode date range  
2. Inner-dropna across assets → count `n_obs`  
3. `_historical_data_quality(n_obs, n_expected_obs)` → coverage + quality label  
4. If `n_obs < 2`: emit row with `pnl_real_episode=null`, `data_quality="insufficient_data"`  
5. Else: compound portfolio return, max drawdown, pass vs mandate  

Proof artifact:

| Episode | n_obs | data_quality | pnl_real_episode |
| --- | --- | --- | --- |
| dotcom | 0 | insufficient_data | null |
| 2008 | 0 | insufficient_data | null |
| 2020 | 3 | reliable | -0.78% |
| 2022 | 12 | reliable | -16.29% |
| banking_2023 | 4 | reliable | +0.72% |

**This is valid disclosed behavior**, not a bug: current ETF holdings lack aligned history for dotcom/2008 windows.

### 8.4 Factor beta estimation (stress block)

- Weekly alignment, windows `FACTOR_WEEKS_5Y=260`, `FACTOR_WEEKS_10Y=520` (`src/stress_factors.py`)  
- Portfolio regression with HAC/Newey-West inference (mandatory per project rules)  
- Rolling 3Y/5Y/10Y betas embedded in `stress_report` JSON; CSV/PNG only if output profile enables export  

### 8.5 Stress status fields

| Field | Meaning | Set by |
| --- | --- | --- |
| `status` | e.g. `DIAG_ATTENTION` | Code comparing scenarios vs mandate |
| `worst_scenario_loss_pct` | Min synthetic PnL | Code |
| `failed_scenario` / `failed_test` | Worst failing scenario | Code |
| `data_trust_summary` | Episode flags + plain English | Code (`src/data_trust_signals.py`) |

Proof: `status="DIAG_ATTENTION"`, `failed_scenario="recession_severe"`, `worst_scenario_loss_pct=-0.2216`.

### 8.6 Explicit answer: “insufficient data” in stress

| Case | Classification |
| --- | --- |
| Historical episode `data_quality="insufficient_data"` | **(A) code-generated** |
| X-Ray warning text | **(A) code-generated**, optionally echoed in commentary |
| Missing artifact file | **(C)** — would block downstream readers; not observed for subject stress in proof |
| LLM interpretation | **Not used** |

---

## 9. Candidate Portfolio Factory algorithm

### 9.1 Core mode scope

`REVIEW_MODE_PROFILES["core"] → "core_v1"` (`src/candidate_factory.py`).

**core_v1 candidate order (6):**

1. `equal_weight`  
2. `risk_parity`  
3. `equal_weight_by_asset_class`  
4. `risk_budget_by_asset`  
5. `risk_budget_by_asset_class`  
6. `hierarchical_risk_parity`  

**Not built in core mode** (available in `default_v1` / `--mode full` only):

- Classic optimizers: minimum_variance*, maximum_diversification*, minimum_cvar*, etc.  
- Robust suite: robust_mv_constrained, robust_mv_uncapped, robust_scenario  

### 9.2 standard execution mode (portfolio-first default)

From `src/candidate_weights.py`:

- **Phase 1 — weights:** in-process via `build_candidate_weights()` (no subprocess `run_*.py`)  
- **Phase 2 — report:** `run_portfolio_report_for_weights(..., report_profile=lightweight_comparison)` → `snapshot_10y.json` minimum for compare  

PDF: suppressed (`pdf_mode=none`, `PORTFOLIO_SKIP_VARIANT_PDF=1`).

### 9.3 Status semantics (factory evidence)

| Status / field | Meaning | Set by |
| --- | --- | --- |
| `succeeded` | Builder ran and produced fresh snapshot | Factory step aggregator |
| `skipped_existing` | `snapshot_10y.json` fresh (analysis_end + config fingerprint match) | `_snapshot_freshness()` |
| `failed` | Builder error / infeasible | Builder summary FAIL_* mapping |
| `freshness_status=fresh` | Snapshot matches expected analysis_end and fingerprint | Code |
| `freshness_status=stale` | analysis_end mismatch | Code |
| `freshness_status=stale_config` | config fingerprint mismatch | Code |
| `rebuilt_stale` | Forced rebuild of stale snapshot | Summary counter |

`--no-skip-existing` → sets `skip_existing=False` → always attempts builders unless other skip rules apply.

### 9.4 Proof factory run (on disk)

`Main portfolio/candidate_factory_run.json`:

- `factory_profile_id: "core_v1"`  
- `summary: { total: 6, skipped_existing: 6, succeeded: 0, failed: 0 }`  
- All six steps: `status="skipped_existing"`, `freshness_status="fresh"`, message “snapshot_10y.json already fresh”  

This proves **reuse path**, not a fresh rebuild path.

### 9.5 Artifacts

| Artifact | Purpose |
| --- | --- |
| `candidate_factory_run.json` | Factory run evidence (steps, timings, freshness) |
| `candidate_factory_manifest.json` | Resume checksum / per-candidate manifest |
| `{candidate}/snapshot_10y.json` | Comparison-ready metrics + weights |
| `{candidate}/candidate_manifest.json` | Per-candidate factory step record |
| `candidate_comparison.json` | Menu + readiness (includes on-disk rows beyond core menu) |

---

## 10. Optimization Engine / candidate builder logic

### 10.1 Core mode builders (proven path)

| Candidate | Method | Algorithm class | Constraints | Output | Failure modes |
| --- | --- | --- | --- | --- | --- |
| **equal_weight** | `build_equal_weight_baseline` | Closed-form 1/N | Long-only, fully invested | `weights.json`, metadata | `FAIL_INFEASIBLE_UNIVERSE` if <2 eligible assets |
| **risk_parity** | `build_risk_parity_baseline` | Spinu cyclical coordinate descent on Ledoit-Wolf Σ; SLSQP fallback | Long-only, no caps | Same | `FAIL_DATA`, `FAIL_NUMERICAL` |
| **equal_weight_by_asset_class** | `build_equal_weight_by_asset_class_baseline` | Equal weight across taxonomy buckets, then within bucket | Taxonomy from universe YAML | Same | Missing taxonomy exclusions |
| **risk_budget_by_asset** | `build_risk_budget_by_asset_baseline` | SLSQP on RC vs per-asset targets from `config.risk_budgeting.asset_targets` | Long-only | Same | `FAIL_INFEASIBLE_TARGETS` |
| **risk_budget_by_asset_class** | `build_risk_budget_by_asset_class_baseline` | SLSQP on aggregated bucket RC vs class targets | Uses `risk_budgeting.targets` preset balanced | Same | Config/taxonomy errors |
| **hierarchical_risk_parity** | `build_hierarchical_risk_parity_baseline` | HRP clustering + recursive bisection | Long-only, no policy box | Same | `FAIL_DATA` insufficient covariance history |

All use shared eligibility filter `_eligible_universe_from_returns()` (coverage vs `analysis_end` and optimization window).

### 10.2 Available but not proven by core proof path

Under `--mode full` / profile `default_v1` (16 candidates), additional **true optimizers** run via same factory framework:

- Minimum variance (constrained / uncapped / advanced)  
- Maximum diversification (constrained / unconstrained)  
- Minimum CVaR (constrained / uncapped)  
- Robust MV (constrained / uncapped)  
- Robust scenario optimization (+ report script chain)  

These invoke `src/portfolio_variants` optimizer paths and (in `legacy_full` execution mode) subprocess `run_*.py` scripts. **Not executed** in the documented core dry-run.

### 10.3 Legacy policy optimization

`run_optimization.py` remains a **separate compatibility entrypoint** for Main/policy weights. It is **outside** the portfolio-first core path documented here.

---

## 11. Candidate comparison readiness

### 11.1 What comparison does in Blocks 1–5

`write_candidate_comparison_outputs()` (`src/candidate_comparison.py`) after factory:

- Reads on-disk snapshots/stress for **analysis_subject + all registry candidates with artifacts**  
- Builds `candidate_comparison.json` with metrics, stress summaries, construction disclosure  
- Adds `optimization_readiness` for optimizer-backed rows via `src/optimization_readiness.py`  

### 11.2 Proof artifact menu semantics

From `Main portfolio/candidate_comparison.json`:

| Field | Value | Interpretation |
| --- | --- | --- |
| `candidate_menu.review_mode` | `core` | Orchestrator mode for this run |
| `candidate_menu.intended_menu_size` | 6 | core_v1 scope |
| `candidate_menu.product_menu_size` | 16 | full default_v1 registry size |
| `candidate_menu.is_partial_menu` | `true` | Explicit reduced-scope flag |
| `candidate_menu.partial_menu_reason` | `reduced_menu_scope_vs_product_default_v1` | Code-owned disclosure |
| `candidates.length` | 19 | Includes legacy `policy`, `current`, and full-menu rows still on disk |

### 11.3 Readiness evidence fields

For optimizer-backed candidates (when present), `construction_disclosure.optimization_readiness` includes:

- `overall_status` (e.g. `ready`, `degraded`)  
- `fair_comparison_ready` boolean  
- `required_checks`: weights, snapshot_10y, stress_summary, construction_disclosure, optimizer_quality, freshness  

**Blocks 1–5 stop here.** Ranking, selection, and action planning consume this JSON in later blocks.

### 11.4 What comparison does **not** prove

- Does not select a winning portfolio  
- Does not generate trade instructions  
- Does not prove all 16 default_v1 optimizers were rebuilt in a core run  
- Does not guarantee fair comparison for `degraded` optimizer rows (readiness warns explicitly)

---

## 12. Decision-making boundary

| Step | Who decides? | Input | Output | Deterministic? | Evidence |
| --- | --- | --- | --- | --- | --- |
| Input validation | **Code** (`config_schema`, `analysis_setup`) | config.yml | pass/fail exit | Yes | `ConfigValidationError` on bad weights |
| analysis_end | **Code** (`windows.get_analysis_end`) | price index, today | date string | Yes | `2026-04-30` in artifacts |
| Data sufficiency | **Code** (coverage, n_obs checks) | return panels | `insufficient_data`, warnings | Yes | stress historical rows |
| Metrics values | **Code** (metrics_*) | aligned returns | numeric metrics | Yes | snapshots |
| Factor exposure status | **Code** (xray section rules) | stress_report | available/partial/unavailable | Yes | `portfolio_xray.json` |
| Stress scenario PnL | **Code** (`run_stress`) | betas, shocks | `portfolio_pnl_pct` | Yes | `stress_report.json` |
| Stress pass/fail (loss gate) | **Code** vs mandate MaxDD | PnL, `target_max_drawdown_pct` | `pass`, `DIAG_*` | Yes | recession_severe fail in proof |
| Worst scenario | **Code** (min PnL selection) | scenario_results | `worst_scenario_loss_pct` | Yes | stress_report |
| Candidate build vs reuse | **Code** (freshness rules) | snapshot + fingerprint | skipped_existing/fresh | Yes | factory_run.json |
| Candidate readiness | **Code** (optimization_readiness) | artifacts checklist | ready/degraded | Yes | candidate_comparison.json |
| X-Ray archetype / weakness | **Rule thresholds** | weights, RC, stress | labels | Yes (given inputs) | XRAY_THRESHOLDS |
| Commentary narrative | **Rule/template code** | JSON sources | commentary.txt | Yes | portfolio_commentary.py |
| Partial menu disclosure | **Code** | review_mode vs registry | `is_partial_menu` | Yes | candidate_menu block |
| Final investment recommendation | **Outside Blocks 1–5** | N/A | selection/action artifacts | N/A | Not produced by core path alone |
| AI/LLM decision | **No AI evidence found** | — | — | — | No LLM imports in pipeline |

---

## 13. Artifact map

Legend: **Gen** = generated; **SoT** = suitable as machine contract source for this run; **Pres** = presentation-only.

### Block 1 — Input & Assumptions

| Path | Producer | Purpose | Gen/SoT/Pres |
| --- | --- | --- | --- |
| `Main portfolio/analysis_subject/run_metadata.json` | `export_run_metadata()` | Resolved config, `analysis_setup`, `input_assumptions`, validation | Gen / **SoT** / — |
| `Main portfolio/analysis_subject/data_policy.json` | `export_data_policy()` | NaN/backtest disclosure, first-available months | Gen / SoT / — |
| `config.yml` | User | Input configuration | Source input / — / — |

### Block 2 — Portfolio X-Ray

| Path | Producer | Purpose | Gen/SoT/Pres |
| --- | --- | --- | --- |
| `Main portfolio/analysis_subject/portfolio_xray.json` | `snapshot._xray_summary_from_output_dir` | Structured X-Ray v2 sections | Gen / **SoT** / — |
| `Main portfolio/analysis_subject/snapshot_{3y,5y,10y}.json` | `save_snapshot()` | Window metrics, weights, RC | Gen / SoT / — |
| `Main portfolio/analysis_subject/snapshot_index.json` | `save_snapshot()` | Index of snapshots | Gen / SoT / — |
| `Main portfolio/analysis_subject/results_csv/*.csv` | export_* (if `full_report`) | Tabular metrics | Gen / SoT* / Pres* |

\*CSV not written under default `site_api` profile; files on disk may be stale from prior export runs.

### Block 3 — Stress Test Lab

| Path | Producer | Purpose | Gen/SoT/Pres |
| --- | --- | --- | --- |
| `Main portfolio/analysis_subject/stress_report.json` | `export_stress_report()` | Scenarios, historical, factor regression, rolling summary | Gen / **SoT** / — |
| `Main portfolio/analysis_subject/scenario_library*.json` | scenario library builders | Extended scenario analytics | Gen / diagnostic / — |
| `Main portfolio/analysis_subject/stress_commentary.txt` | `write_stress_commentary()` | Human-readable stress summary | Gen / — / **Pres** |
| `Main portfolio/analysis_subject/rolling_factor_betas*.{csv,png,html}` | stress_factors writers | Rolling beta visuals | Gen / — / **Pres** (gated by output profile) |

### Block 4–5 — Factory & readiness

| Path | Producer | Purpose | Gen/SoT/Pres |
| --- | --- | --- | --- |
| `Main portfolio/candidate_factory_run.json` | `write_candidate_factory_outputs()` | Factory steps, freshness, timings | Gen / **SoT** / — |
| `Main portfolio/candidate_factory_manifest.json` | `write_candidate_manifest()` | Resume/manifest checksum | Gen / SoT / — |
| `Main portfolio/candidate_comparison.json` | `write_candidate_comparison_outputs()` | Menu, metrics, readiness | Gen / **SoT** (readiness only) / — |
| `{candidate portfolio}/snapshot_10y.json` | `run_portfolio_report_for_weights` | Candidate compare input | Gen / SoT / — |
| `{candidate portfolio}/candidate_manifest.json` | factory per step | Per-candidate factory evidence | Gen / SoT / — |

### Excluded downstream (on disk, not Blocks 1–5 logic)

| Path | Role |
| --- | --- |
| `Main portfolio/decision_package_summary.json` | Later decision packaging |
| `Main portfolio/action_plan.json` | Action engine |
| `Main portfolio/decision_journal.json` | Journal block |
| `pdf files/*.pdf` | Client presentation |

---

## 14. PDF / DOCX / report role

| Question | Answer (code-based) |
| --- | --- |
| Is PDF part of the core algorithm? | **No.** PDF rebuild is a separate step (`rebuild_pdf_reports.py`), omitted when `--skip-pdf` (default). |
| Is PDF only presentation/export? | **Yes.** `src/output_policy.py` states policy controls artifact routing only and must not change portfolio math. |
| Are JSON/CSV the machine-readable layer? | **Yes.** `site_api` profile sets `write_json=True`, disables CSV/TXT/HTML/PNG/PDF by default. Core contracts listed in `write_output_manifest()`. |
| Must PDF generation be required for MVP verification of Blocks 1–5? | **No.** Tests and live core E2E scripts use `--skip-pdf` (`scripts/verify_live_core_e2e.py`). |
| What does `--skip-pdf` mean for algorithm completeness? | **Algorithm complete without PDF.** All calculations and JSON contracts still run; only Pandoc/LaTeX presentation rebuild is skipped. |

Human-readable `commentary.txt` / `report.txt` are also **optional** under `site_api` (not written unless `full_report` / `legacy_export` profile).

---

## 15. Gaps, caveats, and uncertainty

| Caveat | Type | Evidence |
| --- | --- | --- |
| dotcom/2008 historical stress unavailable for current holdings | **Data limitation** (disclosed) | `stress_report.historical_results`: `n_obs=0`, `insufficient_data` |
| Core run leaves 16 product-menu optimizer artifacts on disk from prior full runs; comparison lists 19 candidates | **Design + artifact hygiene** | `candidate_menu.is_partial_menu=true`, `candidates` includes optimizers not rebuilt in core factory |
| Default `site_api` skips CSV/TXT/HTML; subject folder may contain presentation files from earlier export | **Documentation/operator** | `output_policy.write_csv=False`; files present on disk from prior `--output-profile full_report` |
| `analysis_mode=optimize_from_universe` in metadata while subject is `current_portfolio` | **Documentation/naming** | `run_metadata.resolved_config.analysis_mode` vs `analysis_subject.type` (noted in deep audit P17-G7) |
| IBKR adjusted close gaps | **Data limitation** (if provider misses bars) | `market_data_provider: ibkr_yfinance_fallback`; fallback behavior in `data_provider` — **not re-verified live in this pass** |
| Factor exposure status varies run-to-run | **Data/run dependent** | May 22 verification: partial; current disk: available with 8 factor keys |
| Invalid ticker preflight | **Partial validation gap** | Unknown tickers blocked at config preflight for explicit subject; warn-only paths noted in deep audit P17-G5 — **not re-tested here** |
| Selection engine treats `degraded` as eligible | **Outside Blocks 1–5 but handoff risk** | Documented in `docs/audits/2026-05-21_blocks_1_5_deep_audit_snapshot.md` P17-G1 |

---

## 16. Algorithmization assessment

### Fully deterministic (should remain code-owned)

- Config validation and assumption resolution  
- Price download, FX, resampling, return math  
- Portfolio NaN-safe dynamic backtest  
- Metrics, RC_vol, correlation  
- Stress PnL and historical episode quality  
- Factor OLS/HAC regression and rolling betas  
- Factory freshness/skip/rebuild decisions  
- Readiness checklist aggregation  

### Rule-based / heuristic (deterministic given inputs)

- X-Ray archetype, weakness map, hidden risk flags (`XRAY_THRESHOLDS`)  
- Stress diagnostic codes (`DIAG_*`) vs mandate thresholds  
- Factory menu partial flags  
- Commentary templating  

### Data-dependent (still code-owned)

- Which historical episodes compute  
- Which assets pass coverage threshold  
- Whether snapshots are fresh vs stale  

### Where AI is appropriate vs not

| Should NOT use AI (current code agrees) | May use AI later (not implemented) |
| --- | --- |
| Data sufficiency flags | Natural-language explanation of structured JSON for clients |
| Metric values | — |
| Stress PnL | — |
| Factory build/reuse status | — |
| Readiness pass/fail | — |

---

## 17. Final answer

**Is the current Blocks 1–5 path mostly algorithmic?**  
**Yes.** One orchestrator runs deterministic Python modules; statuses are code-generated; no LLM in the pipeline.

**Where could “AI walking in circles” happen?**  
Not inside Blocks 1–5 calculation code. Risk areas are **human or downstream interpretation**: reading mixed core/full artifacts as one menu, treating `DIAG_*` as mandate failure, ignoring `is_partial_menu`, or asking an external LLM to infer missing data instead of reading `data_trust_summary` / `data_quality` fields.

**Root cause if confusion appears**

| Symptom | Likely cause |
| --- | --- |
| Wrong algorithm assumed | **Documentation/product** overselling target UX vs CLI reality |
| Metrics/status disagree with narrative | **Report-generation** (commentary templates) or stale presentation files |
| Optimizer fairness unclear | **Artifact hygiene** (core run + full-menu files on disk) |

**Fix first for clarity (evidence-based, not feature proposals)**

1. Treat `run_metadata.json` + `analysis_setup` as the input contract SoT.  
2. Read `candidate_menu.review_mode` and `is_partial_menu` before interpreting `candidate_comparison.json`.  
3. Use `stress_report.data_trust_summary` for historical gaps — not inferred narrative.  
4. Under `--skip-pdf` + `site_api`, expect JSON-only fresh outputs; ignore stale CSV/HTML unless profile explicitly enables export.

---

## Verification log (this document)

| Check | Result |
| --- | --- |
| Entrypoint chain | Verified via `python run_portfolio_review.py --mode core --skip-pdf --dry-run` and source read of `src/portfolio_review_workflow.py` |
| LLM usage | Grep `*.py` for LLM providers: **none** |
| Proof artifacts | Read `Main portfolio/analysis_subject/{run_metadata,portfolio_xray,stress_report}.json`, `candidate_factory_run.json`, `candidate_comparison.json` |
| `scripts/verify_docs.py` | **Not run** — document uses relative links to existing spec paths only; no new doc routes added beyond this file |
| Full pytest | **Not run** — no code changed |
| Live networked re-run of proof | **Not run** — relied on on-disk artifacts timestamped 2026-05-22 |

**Files created:** `docs/audits/2026-05-23_blocks_1_5_actual_algorithm_walkthrough.md`  
**Files changed:** none (code/docs elsewhere untouched)
