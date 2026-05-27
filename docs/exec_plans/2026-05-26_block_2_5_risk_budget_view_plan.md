# Block 2.5 Risk Budget View MVP

**Status: Completed** (Session 08 closed 2026-05-26). Prerequisite: [Block 2.4 Hidden Exposure MVP](2026-05-26_block_2_4_hidden_exposure_plan.md) **Completed**; [Block 2.1](2026-05-26_block_2_1_asset_allocation_plan.md)–[2.4](2026-05-26_block_2_4_hidden_exposure_plan.md) **Completed**. Evidence: [Block 2.5 acceptance audit](../audits/2026-05-26_block_2_5_risk_budget_acceptance_audit.md); closure pytest **44 passed**; live `run_portfolio_review.py` on root `config.yml`.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows [PLANS.md](../../PLANS.md) from the repository root. A future contributor should continue from this file alone without prior chat context.

**Canonical specs (read order):**

- [docs/specs/portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.5, §2.5.1 product contract; §2.6 archetype legacy
- [docs/specs/portfolio_xray_layer_spec.md](../specs/portfolio_xray_layer_spec.md)
- [docs/specs/metrics_specification.md](../specs/metrics_specification.md) (RC_vol definition — do not invent)
- [docs/specs/input_assumptions_spec.md](../specs/input_assumptions_spec.md) (Input Layer contract freeze)
- [docs/product_flow_operator_guide.md](../product_flow_operator_guide.md)

## Purpose / Big Picture

After this migration, a portfolio-first operator running `python run_portfolio_review.py` on the current [config.yml](../../config.yml) reads `{output_dir_final}/analysis_subject/portfolio_xray.json` and gets a **stable product-facing Block 2.5** that answers: *who really drives portfolio risk?* — not only where capital sits.

The block shows, per asset and in summary:

- capital weight vs volatility risk contribution (RC_vol / `risk_contribution_pct`)
- `weight_vs_risk_gap` (risk overweight / underweight vs capital weight)
- `top1_rc_asset`, `top3_rc_assets`, `top3_rc_share`
- ranked risk-overweight and risk-underweight holdings
- `risk_budget_bucket_contribution` (RC aggregated by taxonomy bucket)

**Stress loss contribution is out of scope** for this product block (Stress Test Lab owns scenario PnL). Legacy `sections.risk_budget_view` may still include stress fields for formatters; the new top-level block must not.

**Product numbering:** **Block 2.5 = Risk Budget View** (`block_2_5_risk_budget_view`). Portfolio Archetype remains legacy `sections.portfolio_archetype` only (not a product block).

**User-visible proof (Session 08):** open `Main portfolio/analysis_subject/portfolio_xray.json` → `block_2_5_risk_budget_view` with per-ticker weight %, RC %, and gap pp for the eight tickers in `config.yml`.

## Non-goals

- Portfolio Archetype product block (`block_2_5_portfolio_archetype` — forbidden)
- Stress scenario PnL / `worst_stress_loss_contribution_pct` in Block 2.5 product JSON
- Recomputing RC_vol, covariance, or factor models inside the block
- Optimizer, candidates, mandate gates, trade instructions
- HTML/PDF report redesign (legacy formatters may keep using `sections.risk_budget_view`)
- Problem Classification consuming Block 2.5 (post-MVP)

## Progress

- [x] (2026-05-26) **Session 00 — ExecPlan foundation:** Audited legacy `_risk_budget_section`, RC resolution path, product blocks 2.1–2.4, docs numbering conflict (archetype vs risk budget); created this ExecPlan; registered **Active** in [docs/exec_plans/README.md](README.md). No application code.
- [x] (2026-05-26) **Session 01 — Product contract (docs):** §2.5.1 in diagnostics spec; Core MVP table 2.1–2.5; layer spec; SPEC/OUTPUTS/DECISIONS/GLOSSARY/PRODUCT; `verify_docs.py`.
- [x] (2026-05-26) **Session 02 — Module scaffold + asset rows:** `src/block_2_5_risk_budget_view.py`, `tests/test_block_2_5_risk_budget.py` (assets, gaps, no stress keys).
- [x] (2026-05-26) **Session 03 — Portfolio aggregates:** top1/top3, overweight/underweight lists, summary sentence.
- [x] (2026-05-26) **Session 04 — Risk-budget bucket contribution:** aggregate RC by `risk_budget_bucket_from_row`; taxonomy wire-time only.
- [x] (2026-05-26) **Session 05 — Wire `build_portfolio_xray_v2`:** top-level `block_2_5_risk_budget_view`; legacy `sections.risk_budget_view` unchanged.
- [x] (2026-05-26) **Session 06 — Tests + golden:** regenerated `portfolio_xray_golden_v2.json`; `assert_block_2_5_product_contract`; contract tests for top-level `block_2_4`/`block_2_5`, fingerprint, golden surface; **17** pytest passed (`test_block_2_5_risk_budget` + `test_portfolio_xray_contract`).
- [x] (2026-05-26) **Session 07 — Product bundle + pipeline:** `PORTFOLIO_XRAY_BLOCK_2_5_KEY`, `portfolio_xray_has_block_2_5`, manifest `product_risk_budget_key`; `seed_block_2_5_subject_dir`; `tests/test_block_2_5_pipeline_integration.py`; E2E gates in `live_core_e2e` / `live_full_e2e`; smoke + `test_product_bundle_paths` updated.
- [x] (2026-05-26) **Session 08 — Live validation + closure:** `run_portfolio_review.py --skip-candidates` and `--candidates equal_weight`; `validate_one_candidate_demo.py` **PASS**; [acceptance audit](../audits/2026-05-26_block_2_5_risk_budget_acceptance_audit.md) with per-ticker table; closure pytest **44 passed**; CHANGELOG; plan **Completed**.

## Surprises & Discoveries

- Observation: Legacy risk budget logic exists and **mixes stress PnL** with RC_vol.
  Evidence: `_risk_budget_section` in `src/portfolio_xray.py` (~L1387–L1447) sets `worst_stress_loss_contribution_pct` and `data_sources_used` includes `stress_report.scenario_results.pnl_by_asset_pct`.

- Observation: RC evidence resolution is already centralized before sections are built.
  Evidence: `resolve_rc_asset_for_xray` in `src/portfolio_xray.py` (~L950–L981); `build_portfolio_xray_v2` calls it (~L3378–L3383).

- Observation: No `src/block_2_5_*` module and no `block_2_5_risk_budget_view` top-level key today.
  Evidence: `rg block_2_5` in `src/` hits only comments guarding archetype; `build_portfolio_xray_v2` return dict ends at `block_2_4_hidden_exposure` (~L3485–L3488).

- Observation: Docs currently assign product number 2.5 to **postponed Archetype** and 2.6 to Risk Budget (legacy section).
  Evidence: [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) Scope table (2026-05-26 archetype demotion pass). Session 01 must reassign **2.5 = Risk Budget Core MVP**.

- Observation: Block 2.1 product contract has `by_asset` weights but **no per-ticker `risk_budget_bucket`** field; bucket aggregation needs wire-time `taxonomy_rows` (same as legacy allocation items).
  Evidence: `BLOCK_2_1_TOP_LEVEL_KEYS` in `tests/test_block_2_1_asset_allocation.py`; `_risk_budget_bucket` helper in `portfolio_xray.py` (~L794–L798).

- Observation: Four existing tests cover legacy risk budget / RC resolution (baseline for regression).
  Evidence: `pytest --collect-only -k "risk_budget or rc_asset"` → 4 tests in `tests/test_portfolio_xray.py` (Session 00).

- Observation: `verify_docs.py` fails while this ExecPlan uses markdown links to planned paths not yet on disk.
  Evidence: Session 00 run lists missing `src/block_2_5_risk_budget_view.py`, tests, acceptance audit — expected until Sessions 02–08; use backtick paths in the plan until files exist.

## Decision Log

- Decision: Product **Block 2.5 = Risk Budget View** (`block_2_5_risk_budget_view`), not Portfolio Archetype.
  Rationale: User-approved product brief; archetype stays legacy `sections.portfolio_archetype` only.
  Date/Author: 2026-05-26 / Session 00.

- Decision: Add top-level product block; keep legacy `sections.risk_budget_view` unchanged in shape.
  Rationale: Same additive pattern as Blocks 2.1–2.4; golden tests and HTML formatters depend on legacy sections.
  Date/Author: 2026-05-26 / Session 00.

- Decision: Product Block 2.5 **excludes** stress loss contribution fields.
  Rationale: User requirement; Stress Test Lab owns scenario PnL; legacy section may still expose stress for compatibility.
  Date/Author: 2026-05-26 / Session 00.

- Decision: RC resolution stays in `build_portfolio_xray_v2`; Block 2.5 module receives resolved RC rows + sources only.
  Rationale: Single load path (`rc_vol_map` → snapshot → CSV); block remains a read-only adapter/summarizer.
  Date/Author: 2026-05-26 / Session 00.

- Decision: Implement in new module `src/block_2_5_risk_budget_view.py` (not inline-only in `portfolio_xray.py`).
  Rationale: Consistency with 2.1–2.4; `portfolio_xray.py` is already large.
  Date/Author: 2026-05-26 / Session 00.

- Decision: Display percentages at export with `REPORT_DECIMALS` (3 decimals); internal gaps as fractions where aligned with legacy `risk_weight_gap`.
  Rationale: [metrics_specification.md](../specs/metrics_specification.md) rounding at export; legacy gap = `rc_vol - weight` (fraction).
  Date/Author: 2026-05-26 / Session 00.

## Outcomes & Retrospective

**Session 00 (2026-05-26):** ExecPlan created; audit inventories embedded below; plan registered **Active**. No application code.

**Session 01 (2026-05-26):** Normative §2.5.1 in diagnostics spec; Core MVP 2.1–2.5; archetype demoted to §2.6; layer spec, SPEC, OUTPUTS, DECISIONS (DEC-2026-05-26-005), GLOSSARY, PRODUCT updated. `verify_docs.py` OK. No application code. Next: Session 02 module scaffold.

**Session 02 (2026-05-26):** Added `build_block_2_5_risk_budget_view` with per-asset weight/RC/gap rows, status (`ok`/`partial`/`unavailable`), envelope metadata; portfolio aggregates left empty for Session 03; five focused unit tests. Not wired into `build_portfolio_xray_v2` (Session 05).

**Session 03 (2026-05-26):** Portfolio aggregates (`top1_rc_asset`, `top3_rc_assets`, `top3_rc_share`, `top_risk_overweight_assets`, `top_risk_underweight_assets`) and enriched `summary`; two new unit tests + updated contract assertions. Not wired into `build_portfolio_xray_v2` (Session 05).

**Session 04 (2026-05-26):** `risk_budget_bucket_contribution` aggregates weight/RC/gap by `risk_budget_bucket_from_row` from wire-time `taxonomy_rows`; warnings when taxonomy missing or per-ticker row absent; three unit tests. Not wired into `build_portfolio_xray_v2` (Session 05).

**Session 05 (2026-05-26):** Wired `build_block_2_5_risk_budget_view` in `build_portfolio_xray_v2` after Block 2.4; top-level key `block_2_5_risk_budget_view`; legacy `sections.risk_budget_view` unchanged. Integration test `test_portfolio_xray_v2_includes_block_2_5_without_removing_legacy_section`. Golden fixture update deferred to Session 06.

**Session 06 (2026-05-26):** Regenerated `tests/fixtures/portfolio_xray_golden_v2.json` with `block_2_5_risk_budget_view` (golden SPY top1 RC 40%, HYG risk-overweight +15 pp, four buckets). Added `assert_block_2_5_product_contract` in `tests/test_block_2_5_risk_budget.py`; extended `tests/test_portfolio_xray_contract.py` (top-level keys 2.4/2.5, fingerprint, `test_golden_block_2_5_risk_budget_surface`). Verification: `python -m pytest tests/test_block_2_5_risk_budget.py tests/test_portfolio_xray_contract.py -q` → **17 passed**. Next: Session 07 product bundle.

**Session 07 (2026-05-26):** `product_bundle_paths` Block 2.5 discovery (`PORTFOLIO_XRAY_BLOCK_2_5_KEY`, `portfolio_xray_has_block_2_5`, `product_risk_budget_key` in manifest note); offline `seed_block_2_5_subject_dir`; `tests/test_block_2_5_pipeline_integration.py` (materialize path, `_xray_summary_from_output_dir`, manifest); `live_core_e2e` / `live_full_e2e` and `test_blocks_1_5_mvp_smoke` assert Blocks 2.4–2.5. Verification: `python -m pytest tests/test_block_2_5_pipeline_integration.py tests/test_block_2_5_risk_budget.py tests/test_portfolio_xray_contract.py tests/test_product_bundle_paths.py tests/test_blocks_1_5_mvp_smoke.py -q` → **44 passed**. Next: Session 08 live validation + closure.

**Session 08 (2026-05-26):** Live portfolio-first runs on root `config.yml` (`--skip-candidates`, `--candidates equal_weight`); `validate_one_candidate_demo.py` **PASS**; subject `portfolio_xray.json` includes `block_2_5_risk_budget_view` with 8-ticker weight/RC/gap table (SCHD top1 RC **19.5%**, SLV largest risk-overweight **+9.5** pp, equity bucket RC **51.7%**); no stress fields in product block; legacy `sections.risk_budget_view` preserved. [Acceptance audit](../audits/2026-05-26_block_2_5_risk_budget_acceptance_audit.md); closure pytest **44 passed**. ExecPlan **Completed**.

## Context and Orientation

Portfolio MRI is diagnosis-first. Block 2.5 follows Block 2.4 in the X-Ray stack and answers: **which holdings and risk buckets consume portfolio variance risk relative to their capital weights?**

Pipeline today (portfolio-first):

```text
config.yml (tickers, current_weights, investor_currency)
  -> validate_config / build_analysis_setup  (Block 1)
  -> run_report.py (portfolio metrics, RC_vol CSV, snapshots)
  -> build_portfolio_xray_v2 (src/portfolio_xray.py)
       -> block_2_1_asset_allocation
       -> block_2_2_portfolio_metrics
       -> block_2_3_factor_exposure
       -> block_2_4_hidden_exposure
       -> block_2_5_risk_budget_view  (target — Session 05+)
       -> sections.* (legacy, including risk_budget_view)
  -> {output_dir_final}/analysis_subject/portfolio_xray.json
```

**RC_vol** means percentage contribution to portfolio variance (not contribution to volatility). Canonical formula owner: [metrics_specification.md](../specs/metrics_specification.md). Block 2.5 must not recompute covariance.

**Risk budget bucket** means a taxonomy-derived label from `risk_budget_bucket_from_row` in [src/risk_budgeting.py](../../src/risk_budgeting.py), not the optimizer candidate family `risk_budget_by_asset`.

## Session 00 — Current State Audit

### 1. Code inventory

| Path | Role | Block 2.5 relevance |
| --- | --- | --- |
| `src/portfolio_xray.py` | `_risk_budget_section`, `resolve_rc_asset_for_xray`, `load_rc_vol_map_from_csv`, `build_portfolio_xray_v2` | Legacy section + RC wiring point |
| `src/block_2_1_asset_allocation.py` | `build_block_2_1_asset_allocation` | Primary weight input for product block |
| `src/block_2_2_portfolio_metrics.py` | Portfolio behavior | Not required for RC (optional cross-check only) |
| `src/block_2_4_hidden_exposure.py` | Hidden risk alerts | No read required for Block 2.5 |
| `src/risk_budgeting.py` | `risk_budget_bucket_from_row` | Bucket aggregation helper |
| `src/product_bundle_paths.py` | Manifest keys through `block_2_4` | Session 07 adds `block_2_5` |
| `run_report.py` | Writes `rc_vol_{10y,5y,3y}.csv` | Upstream RC evidence |

**Planned (Session 02):** `src/block_2_5_risk_budget_view.py` — does not exist yet (no markdown link until file lands; `verify_docs` gate).

### 2. JSON / output inventory

| Artifact | Location | Product-ready? | Notes |
| --- | --- | --- | --- |
| `block_2_1` … `block_2_4` | `analysis_subject/portfolio_xray.json` | **Yes** | Core MVP today |
| `block_2_5_risk_budget_view` | — | **Missing** | Target MVP |
| `sections.risk_budget_view` | same file | Legacy | `asset_risk_budget` items + stress fields |
| `rc_vol_10y.csv` | `results_csv/` | Upstream | Preferred full RC evidence |

### 3. Live demo config ([config.yml](../../config.yml))

| Ticker | Weight |
| --- | --- |
| SPY | 0.10 |
| QQQ | 0.13 |
| GLD | 0.09 |
| SLV | 0.09 |
| BND | 0.16 |
| SCHD | 0.17 |
| SCHP | 0.13 |
| TLT | 0.13 |

Session 08 will publish Block 2.5 weight % / RC % / gap pp for these tickers after a fresh review run.

### 4. Test inventory (baseline)

| Test | Coverage |
| --- | --- |
| `test_portfolio_xray_v2_risk_budget_covers_all_positive_weights_from_csv` | Legacy section completeness |
| `test_resolve_rc_asset_prefers_full_csv_over_snapshot_top5` | RC source priority |
| `test_resolve_rc_asset_prefers_snapshot_json_before_csv` | RC source priority |
| `test_portfolio_xray_v2_risk_budget_hidden_flags_archetype_and_weakness` | Combined legacy X-Ray |

**Session 06 target:** `tests/test_block_2_5_risk_budget.py`, `tests/test_block_2_5_pipeline_integration.py`.

### 5. Gap list (Session 00 → backlog)

| ID | Gap | Priority | Session |
| --- | --- | --- | --- |
| G1 | No `block_2_5_risk_budget_view` top-level key | P0 | 02–05 |
| G2 | No §2.5.1 normative product contract (Risk Budget) | P0 | **01 done** |
| G3 | Docs Scope table lists 2.5 = archetype, 2.6 = risk budget | P0 | **01 done** |
| G4 | Legacy section mixes stress PnL into risk budget | P1 | 05 (product block excludes; legacy unchanged) |
| G5 | Block 2.1 has no per-ticker risk bucket field | P1 | 04 (wire-time taxonomy) |
| G6 | `product_bundle_paths` stops at 2.4 | P1 | 07 |
| G7 | Golden fixture lacks `block_2_5` | P1 | **06 done** |
| G8 | No offline Block 2.5 fixture seeds | P2 | 07 |
| G9 | E2E gates may not assert Block 2.5 | P2 | 07 |
| G10 | HTML/PDF still use legacy section only | P2 | post-MVP |

## Product Contract (target — Session 01 normative detail)

**Top-level key:** `block_2_5_risk_budget_view`

**Envelope:** `block`, `block_id` (`2.5_risk_budget_view`), `block_name`, `status` (`ok` | `partial` | `unavailable`), `summary`, `data_quality_warnings`, `metadata` (`rc_sources`, `rc_window`, `rule_version`, `diagnostic_only`).

**Portfolio summary:**

- `top1_rc_asset`: `{ ticker, weight_pct, rc_pct, weight_vs_risk_gap_pp }`
- `top3_rc_assets`: up to 3 by `rc_pct` descending
- `top3_rc_share`: sum of top-3 `rc_pct`
- `top_risk_overweight_assets` / `top_risk_underweight_assets`: up to 5 each by `weight_vs_risk_gap_pp`
- `risk_budget_bucket_contribution`: `[{ bucket, weight_pct, rc_pct, gap_pp }]`

**Per-asset `assets[]`:**

- `ticker`, `weight_pct`, `rc_vol` (fraction), `risk_contribution_pct` (= `rc_vol * 100` at export), `weight_vs_risk_gap` (fraction), `weight_vs_risk_gap_pp`
- **Must not include** `worst_stress_loss_contribution_pct`, `worst_stress_scenario`

**Inputs (architecture boundary):**

- `block_2_1_asset_allocation` — capital weights
- `rc_asset_rows` + `rc_sources` — from `resolve_rc_asset_for_xray` at wire time only
- `taxonomy_rows` (optional) — bucket labels only; no file I/O inside module
- **Does not read** `stress_report`, Block 2.3, or Block 2.4 for core fields

## Plan of Work

Session 01 updates specs and Core MVP boundaries (2.1–2.5). Sessions 02–04 implement `build_block_2_5_risk_budget_view`. Session 05 wires `build_portfolio_xray_v2` after Block 2.4. Sessions 06–07 add tests, golden fixture, and bundle manifest. Session 08 runs live diagnosis on `config.yml`, writes `docs/audits/2026-05-26_block_2_5_risk_budget_acceptance_audit.md` with per-ticker Block 2.5 numbers, and closes the plan.

Do not change Block 2.1–2.4 output shapes. Do not remove or narrow legacy `sections.risk_budget_view` until an explicit later migration.

## Concrete Steps

From repository root, prefer project venv Python when present: `.\.venv\Scripts\python.exe` or `python`.

**Session 00 (completed) — baseline inventory:**

    rg "block_2_5" src/
    rg "_risk_budget_section" src/portfolio_xray.py
    python -m pytest tests/test_portfolio_xray.py -k "risk_budget or rc_asset" --collect-only -q

**Session 02+ — focused new tests (after implementation):**

    python -m pytest tests/test_block_2_5_risk_budget.py -q

**Session 06 — golden regeneration:**

    python tests/portfolio_xray_golden_inputs.py
    python -m pytest tests/test_portfolio_xray_contract.py -q

**Session 08 — live validation:**

    python run_portfolio_review.py --skip-candidates
    python run_portfolio_review.py --candidates equal_weight
    python scripts/validate_one_candidate_demo.py

Inspect: `Main portfolio/analysis_subject/portfolio_xray.json` → `block_2_5_risk_budget_view`.

## Validation and Acceptance

Acceptance is met when:

1. `portfolio_xray.json` includes top-level `block_2_5_risk_budget_view` with `status` in `ok`/`partial`/`unavailable`, per-asset rows for all positive-weight holdings when RC exists, portfolio summary fields (`top1`, `top3`, overweight/underweight, bucket contribution), and **no stress PnL fields** in the product block.
2. Legacy `sections.risk_budget_view` remains present on full X-Ray builds.
3. Block 2.5 does not read `stress_report` for its core contract (static test or code review).
4. Live run on [config.yml](../../config.yml) produces interpretable weight vs RC table for SPY, QQQ, GLD, SLV, BND, SCHD, SCHP, TLT (Session 08 audit).
5. Focused pytest closure bundle passes (target Session 08): Block 2.5 tests + contract + product_bundle_paths + pipeline integration.

## Idempotence and Recovery

Changes are additive. Regenerating the golden fixture in Session 06 is intentional. If the demo run refreshes generated artifacts, keep generated-output diffs separate from source commits. Re-run `run_portfolio_review.py` idempotently to refresh `analysis_subject/portfolio_xray.json`.

## Artifacts and Notes

**Session 00 baseline commands (2026-05-26):**

    rg "block_2_5" src/
    → comments only in portfolio_xray.py (archetype guard); no block_2_5_risk_budget_view module

    python -m pytest tests/test_portfolio_xray.py -k "risk_budget or rc_asset" --collect-only -q
    → 4 tests collected (legacy RC / risk_budget coverage)

**Session 08 live table (2026-05-26, `config.yml`):**

| Ticker | Weight % | RC % | Gap (pp) |
| --- | ---: | ---: | ---: |
| SPY | 10.0 | 12.9 | +2.9 |
| QQQ | 13.0 | 19.3 | +6.3 |
| GLD | 9.0 | 8.1 | -0.9 |
| SLV | 9.0 | 18.5 | +9.5 |
| BND | 16.0 | 6.4 | -9.6 |
| SCHD | 17.0 | 19.5 | +2.5 |
| SCHP | 13.0 | 5.2 | -7.8 |
| TLT | 13.0 | 10.1 | -2.9 |

Summary: top1 **SCHD**; top3 RC share **57.3%**; dominant RC bucket **equity** (51.7% RC vs 40.0% weight). Full audit: [2026-05-26_block_2_5_risk_budget_acceptance_audit.md](../audits/2026-05-26_block_2_5_risk_budget_acceptance_audit.md).

## Interfaces and Dependencies

**Session 02+ exports (module `src/block_2_5_risk_budget_view.py` — create in Session 02):**

- `BLOCK_2_5_ID = "2.5_risk_budget_view"`
- `BLOCK_2_5_NAME = "Risk Budget View"`
- `build_block_2_5_risk_budget_view(block_2_1, *, rc_asset_rows, rc_sources, taxonomy_rows=None) -> dict`

**Session 05 wiring in `src/portfolio_xray.py`:**

- Import `build_block_2_5_risk_budget_view`
- Call after `block_2_4_hidden_exposure`, passing `block_2_1`, `rc_asset_resolved`, `rc_sources`, `tax_rows`
- Add top-level key `block_2_5_risk_budget_view` to return dict

**Session 07 in `src/product_bundle_paths.py`:**

- `PORTFOLIO_XRAY_BLOCK_2_5_KEY`
- `portfolio_xray_has_block_2_5(doc) -> bool`
