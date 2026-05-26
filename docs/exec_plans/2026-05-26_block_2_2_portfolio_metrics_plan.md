# Block 2.2 Portfolio Metrics / Risk Diagnostics MVP

**Status: Completed** (2026-05-26, Session 08). Acceptance:
[Block 2.2 acceptance audit](../audits/2026-05-26_block_2_2_portfolio_metrics_acceptance_audit.md). Prerequisite: [Block 2.1 Asset Allocation MVP](2026-05-26_block_2_1_asset_allocation_plan.md) **Completed**; [Input Layer MVP Migration](2026-05-26_input_layer_mvp_migration.md) **Completed** (contract frozen).

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows [PLANS.md](../../PLANS.md) in the repository root. A future contributor
should be able to continue this work from this file alone without prior chat context.

**Canonical specs (read order):**

- [docs/specs/portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.2, §2.2.1 (product contract)
- [docs/specs/portfolio_xray_layer_spec.md](../specs/portfolio_xray_layer_spec.md) §2.2 (code map)
- [docs/specs/metrics_specification.md](../specs/metrics_specification.md) (formulas — do not invent alternatives)
- [docs/specs/data_policy_spec.md](../specs/data_policy_spec.md) (panels, NaN, windows)
- [docs/specs/input_assumptions_spec.md](../specs/input_assumptions_spec.md) § Contract freeze (Input Layer — do not redesign)
- [docs/product_flow_operator_guide.md](../product_flow_operator_guide.md) (artifact read order)

## Purpose / Big Picture

After this migration, a portfolio-first operator running
`python run_portfolio_review.py` (diagnosis) or `python run_portfolio_review.py --candidates equal_weight`
(one candidate) gets a **stable, product-facing Block 2.2** answer inside
`{output_dir_final}/analysis_subject/portfolio_xray.json`:

how the current portfolio behaved as one investment organism — return, risk, risk-adjusted
efficiency, drawdowns, tail losses, benchmark dependence, rolling stability summaries, and
correlation breakdown — **without** optimization, candidates, scorecards, or trade instructions.

Block 2.2 is diagnostic-only portfolio behavior. It must treat **Cash USD** (real bank cash) via
the existing NaN-safe return path (0% return contribution, no `cash_proxy_ticker` substitution).

**User-visible proof:** open `Main portfolio/analysis_subject/portfolio_xray.json` and read top-level
`block_2_2_portfolio_metrics` (alongside existing `block_2_1_asset_allocation`).

## Non-goals

- Input Layer redesign; optimizer changes; candidate generation; macro layer; scorecard-first logic.
- Client profile / suitability / mandate builder in Block 2.2.
- Full correlation matrix in core MVP UI (advanced: `full_matrix_ref` + existing CSV only).
- New chart rendering engine; PDF/HTML report redesign.
- Trade recommendations or rebalance logic.
- Exposing raw `metric_quality` to end users (internal only → `data_quality_warnings`).

## Progress

- [x] (2026-05-26) **Session 00 — ExecPlan foundation:** Read `PLANS.md`, portfolio X-Ray specs, Block 2.1 closure, mini-audit inventories; created this ExecPlan; registered **Active** in [docs/exec_plans/README.md](README.md). No application code changes.
- [x] (2026-05-26) **Session 01 — Audit closure:** Re-ran `rg`/pytest inventory commands; gap list G1–G12 unchanged; evidence recorded in Artifacts and Notes. No application code changes.
- [x] (2026-05-26) **Session 02 — Product contract:** `portfolio_xray_diagnostics_spec.md` §2.2.1; layer spec + OUTPUTS; `DECISIONS.md` entry (`DEC-2026-05-26-003`). No application code.
- [x] (2026-05-26) **Session 03 — Builder:** `src/block_2_2_portfolio_metrics.py`, wire `build_portfolio_xray_v2`, correlation pairs helper, `downside_deviation` in metrics path.
- [x] (2026-05-26) **Session 04 — Input connection:** Weights/cash_handling pass-through; Block 2.1 + 2.2 coexist; no allocation duplication.
- [x] (2026-05-26) **Session 05 — Fixtures:** Reuse `demo_usd_asset_allocation_with_cash_5pct.yml`; offline snapshot seeds for Block 2.2.
- [x] (2026-05-26) **Session 06 — Tests:** `tests/test_block_2_2_portfolio_metrics.py` (+ optional contract/pipeline tests).
- [x] (2026-05-26) **Session 07 — Pipeline integration:** `product_bundle_paths`, E2E gates, manifest discovery, runtime modes.
- [x] (2026-05-26) **Session 08 — Live run & closure:** Live demo + acceptance audit + CHANGELOG; plan **Completed**.

## Surprises & Discoveries

- Observation: Block 2.2 logic is **mostly implemented** in the report pipeline and surfaced as `sections.risk_diagnostics`, not as a product block like Block 2.1.
  Evidence: `src/portfolio_xray.py` `_risk_diagnostics_section`; no `block_2_2_*` module; `grep block_2_2` → 0 matches in `src/`.

- Observation: `build_portfolio_xray_v2` **does not recompute** metrics — it summarizes snapshot inputs only (by design).
  Evidence: docstring at `build_portfolio_xray_v2` in `src/portfolio_xray.py` (~L3363–L3367).

- Observation: `metric_quality` is still exposed on legacy `portfolio_metrics` items inside `sections.risk_diagnostics`.
  Evidence: `_portfolio_metrics_item` includes `"metric_quality": metrics.get("metric_quality")` (~L354).

- Observation: `vol_of_vol` / `rel_vol_of_vol` are computed in `run_report.py` analytics but not mapped into X-Ray items today.
  Evidence: `run_report.py` ~L2152–L2163; `_risk_diagnostics_section` rolling keys list has no vol_of_vol.

- Observation: Asset correlation **matrix** is exported to CSV only; top-3 pair breakdown does not exist.
  Evidence: `src/io_export.py` `export_correlation_matrix_csv`; no `top_correlation_pairs` in codebase.

- Observation: `downside_deviation_annual` exists in `run_compare_ew_rp.py` but not in `portfolio_metrics_one_window`.
  Evidence: `src/metrics_portfolio.py` return dict; `run_compare_ew_rp.py` ~L229–L232.

- Observation: Demo root `config.yml` has eight market tickers, no Cash USD; 5% cash fixture already exists from Block 2.1.
  Evidence: `config.yml`; `tests/fixtures/mvp_portfolios/demo_usd_asset_allocation_with_cash_5pct.yml`.

- Observation (Session 01): `python scripts/verify_docs.py` reports missing paths for **planned** Block 2.2 files (`src/block_2_2_portfolio_metrics.py`, `tests/test_block_2_2_portfolio_metrics.py`, acceptance audit) referenced in this ExecPlan — expected until Sessions 03–08.
  Evidence: `verify_docs.py` run 2026-05-26 (Session 01).

## Decision Log

- Decision: Add product contract as top-level `block_2_2_portfolio_metrics` inside `portfolio_xray.json`; keep legacy `sections.risk_diagnostics` unchanged.
  Rationale: Same pattern as Block 2.1 (`DEC-2026-05-26-002`); golden contract tests depend on `sections` shape; UI/API reads stable product keys.
  Date/Author: 2026-05-26 / agent (Session 00).

- Decision: Implement builder in new module `src/block_2_2_portfolio_metrics.py`, called from `build_portfolio_xray_v2`.
  Rationale: `portfolio_xray.py` is already large (~4k lines); Block 2.2 has distinct product shaping and warning rules.
  Date/Author: 2026-05-26 / agent (Session 00).

- Decision: Primary metrics horizon = **10Y (120M)** when `snapshot_10y.json` metrics/analytics exist; else best available snapshot.
  Rationale: Aligns with operator stress/X-Ray habit and existing `snapshot_10y` materialize path in `_xray_summary_from_output_dir`.
  Date/Author: 2026-05-26 / agent (Session 00).

- Decision: Rolling “graphs” in core MVP = `series_ref` to existing CSV under `results_csv/` plus `latest` from `rolling_summary` — no new renderer.
  Rationale: User brief non-goals; CSVs already written by `run_report.py`.
  Date/Author: 2026-05-26 / agent (Session 00).

- Decision: Correlation top-3 pairs computed from primary-window correlation matrix (load `correlation_matrix_10y.csv` when present); full matrix remains advanced/drill-down.
  Rationale: Product brief; matrix already computed in report pipeline.
  Date/Author: 2026-05-26 / agent (Session 00).

- Decision: Do not reopen Input Layer; only pass-through bug-fix if Block 2.2 cannot read weights/cash_handling.
  Rationale: `DEC-2026-05-26-001` / input spec § Contract freeze.
  Date/Author: 2026-05-26 / agent (Session 00).

## Outcomes & Retrospective

**Session 00 (2026-05-26):** ExecPlan created; Session 01 audit inventories embedded below; plan registered Active. No application code.

**Session 01 (2026-05-26):** Audit closure complete. Re-ran inventory commands; all Session 00 observations confirmed (no `block_2_2` in `src/`; `_risk_diagnostics_section` at `portfolio_xray.py` L1084; `build_portfolio_xray_v2` at L3346; `block_2_1` wired, no `block_2_2_portfolio_metrics`; gap list G1–G12 unchanged). Pytest collect on five metrics/X-Ray modules: **25+ tests** enumerated. Fixture `demo_usd_asset_allocation_with_cash_5pct.yml` present; `config.yml` has no Cash USD. No §2.2.1 in diagnostics spec yet (G2). No application code.

**Session 02 (2026-05-26):** Product contract §2.2.1 added to diagnostics spec (top-level `block_2_2_portfolio_metrics`, field tables, upstream mapping, warning rule, primary 10Y horizon). Synced `portfolio_xray_layer_spec.md` §2.2, `OUTPUTS.md` Block 2 row, `DECISIONS.md` `DEC-2026-05-26-003`. Gap G2 closed in spec; G1 remains until Session 03 builder. No application code.

**Session 03 (2026-05-26):** Implemented `src/block_2_2_portfolio_metrics.py` (`build_block_2_2_portfolio_metrics`, `top_correlation_pairs`); wired `block_2_2_portfolio_metrics` in `build_portfolio_xray_v2`; added `downside_deviation_annual` / `downside_deviation` in `metrics_asset` + `portfolio_metrics_one_window`; refreshed golden contract (`portfolio_xray_golden_v2.json`, contract test top-level keys). Gaps G1, G4, G5, G7, G8, G9 partially closed in code (G3 legacy only; G6 vol_of_vol in metadata when present; G10 `full_matrix_ref`; dedicated Block 2.2 tests remain Session 06).

**Session 07 (2026-05-26):** Pipeline wiring: `portfolio_xray_has_block_2_2`, `PORTFOLIO_XRAY_BLOCK_2_2_KEY`, manifest `product_portfolio_behavior_key` in `subject_diagnostics_contract`; `live_core_e2e` / `live_full_e2e` require Block 2.2; `tests/test_block_2_2_pipeline_integration.py`; smoke + `test_product_bundle_paths` gates. G11 closed. Next: Session 08 live demo + closure.

**Session 08 (2026-05-26):** Live closure complete. Commands: `run_portfolio_review.py --skip-candidates`, `--candidates equal_weight`, `validate_one_candidate_demo.py` **PASS**; closure pytest **48 passed**; bundle/runtime regression **16 passed**; `verify_docs.py` OK. Live demo `config.yml` Block 2.2 (10Y): CAGR **0.099**, vol **0.096**, Sharpe **0.799**, MDD **-0.198**, beta **0.513**, top corr QQQ–SPY **0.918**. Fixture real-cash treatment in [acceptance audit](../audits/2026-05-26_block_2_2_portfolio_metrics_acceptance_audit.md) §4. ExecPlan **Completed**; gaps G1–G12 closed or deferred per audit §6.

**Session 04 (2026-05-26):** Input connection hardened. Block 2.2 now detects real-cash presence via Input Layer `analysis_setup.analysis_portfolio.cash_handling.real_cash_holdings` (in addition to weight tickers) so `metadata.cash_treatment` and `data_quality_warnings` remain correct even when weights are passed through without explicit Cash labels. Verified: `python -m pytest tests/test_portfolio_xray_contract.py -q`.

**Session 05 (2026-05-26):** Offline fixture helpers added to `tests/mvp_offline_fixtures.py`: `minimal_block_2_2_metrics`, `minimal_block_2_2_analytics`, `minimal_block_2_2_drawdown_structure`, `minimal_block_2_2_correlation_matrix`, `snapshot_10y_with_block_2_2`, `seed_block_2_2_subject_dir`, `seed_cash5pct_block_2_2_subject_dir`. Seeds write `snapshot_10y.json` (metrics + analytics + drawdown_structure), `run_metadata.json` (when analysis_setup supplied), and a deterministic `results_csv/correlation_matrix_10y.csv` for top-pair assertions. Cash-5%-USD fixture correctly wires `analysis_setup` with `cash_handling`. Smoke-tested with builder: all Block 2.2 contract fields populated, `data_quality_warnings` empty when data complete, top-pair list correct. Regression: `python -m pytest tests/test_portfolio_xray_contract.py tests/test_mvp_portfolio_fixtures.py -q` → 12/12 passed.

## Context and Orientation

Portfolio MRI is diagnosis-first. Block 2.2 answers: **how has this portfolio behaved as a whole
investment organism?** It follows Block 2.1 (what you own) in the X-Ray stack.

Pipeline today (portfolio-first):

```text
config.yml (tickers, current_weights, investor_currency)
  -> validate_config / build_analysis_setup
  -> run_report.py (portfolio_returns_nan_safe, portfolio_metrics_one_window, analytics, drawdown)
  -> snapshot_{3y,5y,10y}.json (metrics, analytics, drawdown_structure)
  -> build_portfolio_xray_v2 (src/portfolio_xray.py)
       -> sections.risk_diagnostics (legacy items[])
       -> block_2_1_asset_allocation (product)
       -> block_2_2_portfolio_metrics (product — Session 03+)
  -> {output_dir_final}/analysis_subject/portfolio_xray.json
```

Legacy policy path may also write root `{output_dir_final}/portfolio_xray.json`; portfolio-first
truth is **`analysis_subject/`** per [product_flow_operator_guide.md](../product_flow_operator_guide.md).

## Session 01 — Current State Audit

### 1. Portfolio metrics / risk diagnostics code inventory

| Path | Role | Block 2.2 relevance |
| --- | --- | --- |
| [src/metrics_portfolio.py](../../src/metrics_portfolio.py) | `portfolio_metrics_one_window`, `build_portfolio_metric_quality` | **Primary** window metrics (CAGR, vol, Sharpe, Sortino, beta, MDD, TTR, skew/kurt) |
| [src/metrics_asset.py](../../src/metrics_asset.py) | Asset-level formulas | Canonical estimators (ddof=1, monthly) |
| [src/portfolio_analytics.py](../../src/portfolio_analytics.py) | Rolling, drawdown, VaR/ES, EEE, `rolling_summary` | Tail + rolling + drawdown structure |
| [src/portfolio_dynamic.py](../../src/portfolio_dynamic.py) | `portfolio_returns_nan_safe` | Real cash / NaN-safe portfolio returns |
| [src/portfolio_xray.py](../../src/portfolio_xray.py) | `_risk_diagnostics_section`, `build_portfolio_xray_v2`, `load_portfolio_windows_from_dir` | Legacy section + wiring point |
| [run_report.py](../../run_report.py) | STEP 7 metrics, STEP 8 RC/corr CSV, analytics block | Produces snapshot inputs |
| [src/snapshot.py](../../src/snapshot.py) | `_xray_summary_from_output_dir` | Materializes `portfolio_xray.json` |
| [src/io_export.py](../../src/io_export.py) | `export_correlation_matrix_csv` | Advanced full matrix on disk |

**Planned (Session 03):** `src/block_2_2_portfolio_metrics.py` — does not exist yet.

### 2. Existing JSON / output inventory

| Artifact | Location | Product-ready? | Notes |
| --- | --- | --- | --- |
| `portfolio_xray.json` | `{output_dir_final}/analysis_subject/` | **Partial** | Has `block_2_1`; 2.2 only via `sections.risk_diagnostics` |
| `sections.risk_diagnostics` | inside above | Internal | `portfolio_metrics`, `multi_window_metrics`, `tail_risk`, `rolling_metrics`, `drawdown_structure` items |
| `block_2_2_portfolio_metrics` | — | **Missing** | Target MVP product contract |
| `snapshot_10y.json` | `analysis_subject/` | Upstream | `metrics`, `analytics`, `drawdown_structure` |
| `correlation_matrix_10y.csv` | `results_csv/` | Advanced | Full matrix; not in X-Ray JSON today |
| `rolling_sharpe_36m_10y.csv` etc. | `results_csv/` | Advanced series | Referenced via `series_ref` in product block |

### 3. Metrics coverage vs product brief

| Metric / feature | Status | Source |
| --- | --- | --- |
| CAGR, vol, Sharpe, Sortino, Treynor, beta, corr, down/up beta, skew, kurt, MDD, TTR | Implemented | `portfolio_metrics_one_window` → snapshot `metrics` |
| VaR/ES 95/99 (daily historical) | Implemented | `analytics.tail_risk` |
| Drawdown underwater %, counts >5/10/20%, recovery median/p90 | Implemented | `drawdown_structure()` |
| Rolling Sharpe/Sortino/vol/beta/corr summaries | Implemented | snapshot `analytics` |
| vol_of_vol, rel_vol_of_vol | Computed, not in product block | `run_report.py` analytics |
| downside_deviation (annual) | **Gap** | Inline in `run_compare_ew_rp.py` only |
| Top-3 correlation pairs | **Gap** | New helper Session 03 |
| `block_2_2_portfolio_metrics` | **Gap** | Session 02–03 |
| User-facing `metric_quality` | **Must not ship** in block | Map to `data_quality_warnings` |

### 4. Config and fixtures inventory

| File | Purpose |
| --- | --- |
| [config.yml](../../config.yml) | Live demo 8-ticker USD, no cash |
| [tests/fixtures/mvp_portfolios/demo_usd_asset_allocation_with_cash_5pct.yml](../../tests/fixtures/mvp_portfolios/demo_usd_asset_allocation_with_cash_5pct.yml) | 5% Cash USD regression (Block 2.1) |
| [tests/fixtures/portfolio_xray_golden_v2.json](../../tests/fixtures/portfolio_xray_golden_v2.json) | Golden `risk_diagnostics` section shape |

### 5. Test inventory (metrics / 2.2)

| Test module | Coverage |
| --- | --- |
| [tests/test_portfolio_metrics_deepening.py](../../tests/test_portfolio_metrics_deepening.py) | Beta shape, rolling, X-Ray exposure |
| [tests/test_metrics_drawdown.py](../../tests/test_metrics_drawdown.py) | TTR via `portfolio_metrics_one_window` |
| [tests/test_tail_risk.py](../../tests/test_tail_risk.py) | Daily VaR/ES metadata |
| [tests/test_portfolio_xray.py](../../tests/test_portfolio_xray.py) | `risk_diagnostics`, provenance, multi-window |
| [tests/test_portfolio_xray_contract.py](../../tests/test_portfolio_xray_contract.py) | Golden v2; requires `block_2_1` |

**Session 06 target:** `tests/test_block_2_2_portfolio_metrics.py`.

### 6. Gap list (Session 01 → implementation backlog)

| ID | Gap | Priority | Session |
| --- | --- | --- | --- |
| G1 | No `block_2_2_portfolio_metrics` top-level key | P0 | 02–03 |
| G2 | No §2.2.1 normative product contract in spec | P0 | ~~02~~ **closed** (Session 02) |
| G3 | `metric_quality` exposed in legacy `portfolio_metrics` item | P1 | 03 (strip in block only) |
| G4 | Top-3 highest/lowest correlation pairs | P0 | 03 |
| G5 | `downside_deviation` not in window metrics | P0 | 03 |
| G6 | `vol_of_vol` not in product block | P1 | 03 |
| G7 | Drawdown fields split across metrics vs `drawdown_structure` | P1 | 03 (normalize) |
| G8 | Rolling only as flat summaries, not `core_view` shape | P0 | 03 |
| G9 | `beta_base` alias (`beta_portfolio` in code) | P1 | 03 |
| G10 | Full matrix CSV only on disk | P2 | 03 (`full_matrix_ref`) |
| G11 | No `portfolio_xray_has_block_2_2` / manifest | P1 | ~~07~~ **closed** (Session 07) |
| G12 | No Block 2.2 dedicated tests | P0 | 06 |

### 7. Duplicated or legacy logic notes

- **Formulas:** single source in `metrics_asset` / `metrics_portfolio` / `portfolio_analytics` — Block 2.2 builder **maps only**, does not recompute in X-Ray.
- **Legacy** `sections.risk_diagnostics` remains for golden tests and formatters — product UI reads `block_2_2_portfolio_metrics`.
- **Regime metrics** (`src/regime_portfolio_metrics.py`) are stress adjunct — out of Block 2.2 MVP scope.

## Target Product Contract (normative in spec §2.2.1 from Session 02)

Top-level key on `portfolio_xray.json`:

```json
{
  "block": "2.2_portfolio_metrics",
  "analysis_subject": "current_portfolio",
  "analysis_mode": "analyze_current_weights",
  "investor_currency": "USD",
  "portfolio_behavior_snapshot": {
    "headline": null,
    "key_points": [],
    "overall_behavior_label": null
  },
  "return_risk_metrics": {
    "portfolio_cagr": null,
    "vol_annual": null,
    "sharpe": null,
    "sortino": null,
    "treynor": null,
    "skewness": null,
    "kurtosis": null
  },
  "drawdown_diagnostics": {
    "max_drawdown": null,
    "ttr_months": null,
    "recovered": null,
    "drawdown_depth": null,
    "drawdown_length": null,
    "recovery_months": null,
    "recovery_median": null,
    "recovery_p90": null,
    "pct_time_underwater": null,
    "longest_underwater": null,
    "count_drawdowns_gt_5": null,
    "count_drawdowns_gt_10": null,
    "count_drawdowns_gt_20": null
  },
  "tail_risk_diagnostics": {
    "var_95": null,
    "var_99": null,
    "es_95": null,
    "es_99": null,
    "downside_deviation": null,
    "eee_10": null
  },
  "benchmark_dependence": {
    "benchmark_ticker": null,
    "beta_portfolio": null,
    "beta_base": null,
    "corr_base": null,
    "downside_beta": null,
    "upside_beta": null
  },
  "rolling_diagnostics": {
    "core_view": {
      "rolling_sharpe_36m": { "available": false, "latest": null, "series_ref": null },
      "rolling_volatility_12m": { "available": false, "latest": null, "series_ref": null },
      "rolling_beta_or_correlation": {
        "available": false,
        "latest_beta": null,
        "latest_correlation": null,
        "series_ref": null
      }
    },
    "advanced_available": {
      "rolling_sharpe_12m": false,
      "rolling_sortino_36m": false,
      "rolling_sortino_12m": false,
      "rolling_beta_36m": false,
      "rolling_beta_12m": false,
      "rolling_correlation_36m": false,
      "rolling_correlation_12m": false
    }
  },
  "correlation_breakdown": {
    "top3_highest_correlation_pairs": [],
    "top3_lowest_correlation_pairs": [],
    "full_matrix_available": false,
    "full_matrix_ref": null
  },
  "data_quality_warnings": [],
  "metadata": {
    "source": "core_mvp_input",
    "cash_treatment": "real_cash_position_if_present",
    "cash_proxy_used_for_real_cash": false,
    "metric_quality_internal_only": true,
    "primary_window_months": 120,
    "primary_window_label": "10Y (120M)"
  }
}
```

**Warning rule:** when `n_obs` is below window expectation or metrics are NaN, append short English
strings such as *"Analysis is limited because of short history / incomplete data."* — never expose
raw `metric_quality` object to UI consumers of this block.

## Plan of Work (Sessions 02–08)

Session 02 adds §2.2.1 to diagnostics spec and syncs layer spec + OUTPUTS + DECISIONS.

Session 03 implements `build_block_2_2_portfolio_metrics()` and wires it in `build_portfolio_xray_v2`
(load correlation CSV from `output_dir_csv` when available).

Session 04 verifies Input Layer weights and real-cash metadata; Block 2.1 unchanged.

Session 05 extends offline fixtures with minimal metrics/analytics for Block 2.2 unit tests.

Session 06 adds `tests/test_block_2_2_portfolio_metrics.py` and updates contract tests.

Session 07 adds `portfolio_xray_has_block_2_2`, manifest discovery, E2E gates.

Session 08 runs live demo on `config.yml` + documents exact metrics in acceptance audit.

## Concrete Steps

**Session 00 (completed 2026-05-26):**

    Working directory: repository root

    # Confirm risk diagnostics entrypoints
    rg "_risk_diagnostics_section|build_portfolio_xray_v2" src/portfolio_xray.py

    # Confirm no Block 2.2 module yet
    rg "block_2_2" src/

    # Docs link check (optional)
    python scripts/verify_docs.py

**Session 01 (completed 2026-05-26):** Re-ran inventory commands; evidence in Artifacts and Notes below.

**Session 02 (completed 2026-05-26):** §2.2.1 in diagnostics spec; layer spec + OUTPUTS + `DEC-2026-05-26-003`.

**Session 03 (next):** `src/block_2_2_portfolio_metrics.py`, wire `build_portfolio_xray_v2`, correlation pairs, `downside_deviation`.

**Session 06 (future):**

    python -m pytest tests/test_block_2_2_portfolio_metrics.py tests/test_block_2_1_asset_allocation.py -q

**Session 08 (future):**

    python -m pytest tests/test_block_2_1_asset_allocation.py tests/test_block_2_2_portfolio_metrics.py -q
    python -m pytest tests/test_product_bundle_integration.py tests/test_runtime_mode_regression_boundaries.py -q
    python run_portfolio_review.py --skip-candidates
    python run_portfolio_review.py --candidates equal_weight
    python scripts/validate_one_candidate_demo.py
    python scripts/verify_docs.py

## Validation and Acceptance

**Session 00 acceptance (met 2026-05-26):**

- ExecPlan file exists at `docs/exec_plans/2026-05-26_block_2_2_portfolio_metrics_plan.md`.
- Register marks this plan **Active**.
- Session 01 audit inventories and gap list G1–G12 documented in this ExecPlan.
- No application code changes.

**Session 01 acceptance (met 2026-05-26):**

- Inventory commands re-run; gap list G1–G12 unchanged (recorded in Artifacts and Notes).
- No application code unless audit script (none added).

**Full plan acceptance (Session 08):**

- `analysis_subject/portfolio_xray.json` contains populated `block_2_2_portfolio_metrics` on diagnosis and one-candidate runs.
- Block 2.1 output unchanged; Block 2.2 coexists.
- Cash USD 5% fixture tests pass; final report with exact Block 2.2 numbers for `config.yml` demo.
- Acceptance audit: `docs/audits/2026-05-26_block_2_2_portfolio_metrics_acceptance_audit.md`.

## Idempotence and Recovery

Session 00 is read-only. Later sessions are additive to `portfolio_xray.json`. Re-running
`run_portfolio_review.py` overwrites generated artifacts under `Main portfolio/` — expected.

## Artifacts and Notes

Session 00 evidence (2026-05-26):

    rg "block_2_2" src/
    # -> no matches (expected before Session 03)

    rg "_risk_diagnostics_section" src/portfolio_xray.py
    # -> defined ~L1084, used in build_portfolio_xray_v2

Session 01 evidence (2026-05-26, repository root):

    rg "block_2_2" src/
    # -> no matches (G1/G12 confirmed)

    rg "_risk_diagnostics_section|build_portfolio_xray_v2" src/portfolio_xray.py
    # -> _risk_diagnostics_section L1084; build_portfolio_xray_v2 L3346; call L3406

    rg "block_2_1" src/portfolio_xray.py
    # -> import L13; build_block_2_1_asset_allocation L3398; key block_2_1_asset_allocation L3460
    # -> no block_2_2_portfolio_metrics key (G1)

    rg "top_correlation_pairs|block_2_2_portfolio_metrics" .
    # -> only ExecPlan/docs (G4, G1)

    rg "downside_deviation" src/metrics_portfolio.py
    # -> no matches (G5)

    rg "vol_of_vol" run_report.py
    # -> L2153–L2163 analytics block; not in _risk_diagnostics rolling_keys (G6)

    rg "metric_quality" src/portfolio_xray.py
    # -> _portfolio_metrics_item exposes metric_quality L354 (G3)

    rg "§2.2.1|2.2.1" docs/specs/portfolio_xray_diagnostics_spec.md
    # -> no matches (G2)

    python -m pytest tests/test_portfolio_metrics_deepening.py tests/test_metrics_drawdown.py \
      tests/test_tail_risk.py tests/test_portfolio_xray.py tests/test_portfolio_xray_contract.py \
      --collect-only -q
    # -> 25+ tests collected (inventory §5 confirmed)

    python scripts/verify_docs.py
    # -> FAILED: missing planned paths in this ExecPlan (expected until Sessions 03–08)

## Interfaces and Dependencies

**End state (Session 03):** in `src/block_2_2_portfolio_metrics.py`:

    BLOCK_2_2_ID = "2.2_portfolio_metrics"

    def build_block_2_2_portfolio_metrics(
        *,
        analysis_setup: dict[str, Any] | None,
        portfolio_metrics: dict[str, Any] | None,
        portfolio_analytics: dict[str, Any] | None,
        drawdown_structure: dict[str, Any] | None,
        portfolio_windows: dict[str, dict[str, Any]] | None = None,
        correlation_matrix: pd.DataFrame | None = None,
        correlation_matrix_ref: str | None = None,
        output_dir_csv: Path | str | None = None,
        primary_window_months: int = 120,
    ) -> dict[str, Any]: ...

    def top_correlation_pairs(
        corr: pd.DataFrame,
        *,
        n: int = 3,
        exclude_tickers: set[str] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]: ...

**Consumer:** `build_portfolio_xray_v2` sets `result["block_2_2_portfolio_metrics"] = ...`.

---

**Revision note (2026-05-26):** Initial ExecPlan created (Session 00); plan registered Active; Session 01 audit embedded from planning mini-audit.

**Revision note (2026-05-26):** Session 01 audit closure — inventories re-verified; gap list G1–G12 unchanged; Progress ticked; no application code.

**Revision note (2026-05-26):** Session 02 product contract — §2.2.1 in diagnostics spec; `OUTPUTS.md`, layer spec §2.2, `DEC-2026-05-26-003`; G2 closed; no application code.

**Revision note (2026-05-26):** Session 08 — plan **Completed**; live demo + [acceptance audit](../audits/2026-05-26_block_2_2_portfolio_metrics_acceptance_audit.md).
