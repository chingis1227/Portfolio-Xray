# Portfolio X-Ray Methodology Map (Block 2)

Date: 2026-05-20

Status: Historical input (Phase 12 governance wave closed 2026-05-20). Baseline checklist:
[Portfolio X-Ray Baseline Snapshot](2026-05-20_portfolio_xray_baseline_snapshot.md).

Scope: current-portfolio diagnostics only (Block 2). Builds on the completed
[Portfolio X-Ray Diagnostics Deepening Plan](../exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md)
(Sessions 00–09, `RM-930`–`RM-939`) and the 2026-05-20 methodology audit.

This document is project memory for methodology transparency. It does not override canonical specs or
current code behavior.

## Provenance legend

| Code | Meaning |
| --- | --- |
| **C** | Existing code behavior |
| **S** | Existing canonical spec |
| **A** | Generated artifact evidence |
| **T** | Target product concept (partially implemented) |
| **N** | NEW METHODOLOGY PROPOSAL — requires spec decision before implementation |

## Executive summary

Portfolio X-Ray (`portfolio_xray_v2`) is a **diagnostic aggregator** over report pipeline outputs
([C] `src/portfolio_xray.py::build_portfolio_xray_v2`). It does not recompute metrics, RC_vol,
factor betas, VaR/ES, or stress PnL with alternate formulas.

**Maturity (2026-05-20, post Phase 12):** ~85% technical; ~80% audit-ready transparency for Block 2
governance scope (deferred G7: factor/drawdown/ES risk budget display).

**Strongest:** seven-section JSON contract, spec-owned thresholds, section provenance, factor
inference panel, multi-window metrics, concentration diagnostics, golden contract tests, layer spec,
Hidden Risk V2, Weakness Map V2 (incl. factor-only `volatility_spike`), Archetype V2, Risk Budget CSV
loading, report/HTML productization.

**Phase 12 closure (Sessions 00–10):** governance gaps G1–G6, G8–G11 closed; G7 deferred; baseline
snapshot in [2026-05-20_portfolio_xray_baseline_snapshot.md](2026-05-20_portfolio_xray_baseline_snapshot.md).

Primary artifact: `{output_dir_final}/analysis_subject/portfolio_xray.json` ([S][A] `OUTPUTS.md`).

## Architecture

```text
analysis_subject weights + snapshots + stress_report + rc_vol CSV + taxonomy YAML
  -> build_portfolio_xray_v2 (src/portfolio_xray.py)
  -> portfolio_xray.json
  -> report.txt / report.html / commentary.txt (format_portfolio_xray_*)
```

Orchestration: [src/snapshot.py](../../src/snapshot.py) `_xray_summary_from_output_dir`.

## Sub-block map

### 2.1 Asset Allocation

**Question:** What does the portfolio own, and where is capital concentrated?

| Element | Rule | Provenance |
| --- | --- | --- |
| Weights | Positive weights only from `analysis_setup` or snapshot | **C** |
| Taxonomy | Label-based from `config/etf_universe.yml` + `config/stock_universe.yml`; not look-through | **C** **S** spec §2.1 |
| `risk_bucket` | Derived via `risk_budget_bucket_from_row` | **C** `src/risk_budgeting.py` |
| Breakdowns | asset_class, region, currency, sector, risk_role, main_risk_factor, risk_bucket | **C** |
| Unknown taxonomy | Weight → `unknown`; section `partial` + warning | **C** **A** |
| Concentration | `weight_concentration` item: top-1/top-3 sums, HHI on capital weights; legacy summary mirrors | **C** **S** Session 07 (`RM-947`) |

**Tests:** `tests/test_portfolio_xray.py` (taxonomy partial).

### 2.2 Portfolio Metrics / Risk Diagnostics

**Question:** How has the portfolio behaved historically, and what risk did it take?

| Metric | Computation owner | Frequency | Window | X-Ray exposure | Provenance |
| --- | --- | --- | --- | --- | --- |
| CAGR, vol, Sharpe, Sortino, beta, Treynor, MaxDD | `portfolio_metrics_one_window` | monthly simple | 3Y/5Y/10Y calendar | primarily 10Y snapshot metrics item | **C** **S** metrics_spec |
| Skew/kurt | monthly log returns | monthly | same | yes | **C** Session 04 |
| Down/upside beta | benchmark sign split | monthly | same | yes | **C** |
| VaR/ES | `compute_tail_risk_historical` | **daily** simple | per window | `tail_risk` item | **C** **S** |
| Rolling beta/corr | summaries in analytics | monthly | 36m/12m | `rolling_metrics` item | **C** |
| TTR | computed in pipeline | monthly | same | `portfolio_metrics.ttr_months` + panel | **C** **S** Session 05 |
| Multi-window panel | three snapshots exist | — | 3Y/5Y/10Y | `multi_window_metrics` item | **C** **S** Session 05 |

**Tests:** `test_portfolio_metrics_deepening.py`, `test_tail_risk.py`, X-Ray tail disclosure test.

### 2.3 Factor Exposure / Factor Sensitivity

**Question:** Which factors is the portfolio sensitive to?

| Evidence | Source | X-Ray field | Provenance |
| --- | --- | --- | --- |
| OLS betas 5Y/10Y | `stress_report.factor_betas_*` weekly | `beta_5y`, `beta_10y` | **C** **S** stress §8 |
| Kalman current | `factor_betas_kalman.latest` | `kalman_current_beta` | **C** **S** factor_diagnostics |
| Variance shares | `factor_variance_decomposition` | per-factor + residual item | **C** **S** |
| Regression inference (t, p, HAC, VIF) | `factor_regression_5y/10y` | `factor_regression_inference` items | **C** **S** stress §8; **C** X-Ray §2.3 (`RM-944`) |

**Tests:** `test_portfolio_xray_v2_kalman_reads_factor_betas_kalman_latest`,
`test_portfolio_xray_factor_regression_inference_panel`.

### 2.4 Hidden Exposure / Hidden Risk Detector

**Question:** What risks are not obvious from headline allocation?

Eleven categories in fixed order ([C] `HIDDEN_RISK_CATEGORY_ORDER`). Each emits
`flagged` / `below_threshold` / `unavailable` with evidence, thresholds keys, section confidence
counts ([C] **S** spec §2.4).

Thresholds: `XRAY_THRESHOLDS` in [src/portfolio_xray.py](../../src/portfolio_xray.py) — **C** runtime;
**S** canonical registry in [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §8;
drift tests in `tests/test_portfolio_xray_threshold_registry.py` (Session 02 / `RM-942`).

**Tests:** hidden-risk flagged and below-threshold cases in `tests/test_portfolio_xray.py`.

### 2.5 Portfolio Archetype Classification

**Question:** What kind of portfolio is this, with evidence and caveats?

Ten archetypes; rule-based scorecard; primary/secondary; `conflicting_signals` with weakness-map
tensions ([C] **S** spec §2.5). Built **after** weakness map.

**Tests:** balanced, duration-heavy, inflation conflict, pseudo-diversified, equity growth tests.

### 2.6 Risk Budget View

**Question:** Which assets consume risk relative to capital weight?

| Field | Source | Provenance |
| --- | --- | --- |
| weight | analyzed weights | **C** |
| rc_vol | `rc_vol_10y.csv` → 5y → 3y fallback; snapshot top-N gap-fill only | **C** **S** |
| risk_weight_gap | rc_vol − weight | **C** |
| worst stress contrib | min `pnl_by_asset_pct` across scenarios | **C** |
| factor RC / drawdown contrib | not implemented | **T** **N** |

**Tests:** full CSV coverage, snapshot fallback tests.

### 2.7 Portfolio Weakness Map

**Question:** Under which scenarios/regimes is the portfolio vulnerable?

V2 contract: `exposure_present`, `adverse_evidence`, `severity`, `confidence`, `scenario_coverage`,
drivers ([C] **S** spec §2.7). Scenario map in `WEAKNESS_SCENARIO_MAP`; `crypto_shock` conditional.

**Contract (Session 08, Option B):** `volatility_spike` is **factor-only** — `beta_vix` and historical
`es_95`; no synthetic scenario mapping (**C** **S**). `scenario_coverage.evidence_mode=factor_only`.
Option A (dedicated synthetic scenario) deferred to stress spec.

**Tests:** low-risk not overstated, crypto conditional, missing scenario warnings.

## Cross-block gaps (priority)

| ID | Gap | Session |
| --- | --- | --- |
| G1 | Thresholds code-only | closed (02) |
| G2 | Section provenance metadata | closed (03) |
| G3 | Factor inference not in X-Ray | closed (04) |
| G4 | Single-window metrics | closed (05) |
| G5 | TTR not exposed | closed (05) |
| G6 | No HHI / concentration indices | closed (07) |
| G7 | No factor/drawdown/ES risk budget | deferred |
| G8 | volatility_spike scenario gap | closed (08) |
| G9 | Stale KNOWN_ISSUES / ROADMAP | closed (01) |
| G10 | No X-Ray baseline snapshot | closed (10) |
| G11 | No portfolio_xray_layer_spec.md | closed (06) |

## New methodology proposals (require spec before code)

| ID | Proposal | Default assumption |
| --- | --- | --- |
| N1 | Canonical threshold registry in spec | **implemented** Session 02 (`RM-942`) |
| N2 | Section metadata envelope | **implemented** Session 03 (`RM-943`) |
| N3 | Factor regression inference panel | **implemented** Session 04 (`RM-944`) |
| N4 | Multi-window metrics + TTR in X-Ray | **implemented** Session 05 (`RM-945`) |
| N5 | ES contribution by asset | pipeline first, X-Ray display only |
| N6 | Allocation concentration (HHI, top-N) | **implemented** Session 07 (`RM-947`) |
| N7 | volatility_spike: factor-only vs new scenario | **implemented** Session 08 (`RM-948`, Option B) |

## Verification references

- X-Ray tests: `tests/test_portfolio_xray.py` (incl. `test_portfolio_xray_weight_concentration_in_asset_allocation`),
  `tests/test_portfolio_xray_threshold_registry.py`, `tests/test_portfolio_xray_contract.py`
  (golden `tests/fixtures/portfolio_xray_golden_v2.json`, regenerate via `python tests/portfolio_xray_golden_inputs.py`)
- Metrics: `tests/test_portfolio_metrics_deepening.py`
- Tail: `tests/test_tail_risk.py`
- Cutoff: `tests/test_analysis_end_cutoff.py`
- Owning spec: [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md)
- Layer map: [portfolio_xray_layer_spec.md](../specs/portfolio_xray_layer_spec.md)
- Layer audit (historical): [2026-05-19_portfolio_xray_layer_audit.md](2026-05-19_portfolio_xray_layer_audit.md)

## Final verdict

Block 2 is an audit-grade diagnostic aggregator for the Phase 12 governance scope (threshold registry,
provenance, factor inference surfacing, multi-window/TTR, concentration, vol-spike contract, golden
tests, layer spec, baseline snapshot). Further work (G7 risk-budget extensions, UI, new heuristics)
requires explicit spec decisions outside the closed post-audit wave (`RM-940`–`RM-950`).
