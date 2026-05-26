# Block 2.1 Asset Allocation MVP

**Status: Completed** (2026-05-26, Session 08). Acceptance:
[Block 2.1 acceptance audit](../audits/2026-05-26_block_2_1_asset_allocation_acceptance_audit.md).

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows [PLANS.md](../../PLANS.md) in the repository root. A future contributor
should be able to continue this work from this file alone without prior chat context.

**Canonical specs (read order):**

- [docs/specs/portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.1 (current diagnostic contract)
- [docs/specs/portfolio_xray_layer_spec.md](../specs/portfolio_xray_layer_spec.md) §2.1 (code map)
- [docs/specs/input_assumptions_spec.md](../specs/input_assumptions_spec.md) § Contract freeze (Input Layer — do not redesign)
- [docs/product_flow_operator_guide.md](../product_flow_operator_guide.md) (artifact read order)

**Prerequisite (closed):** [Input Layer MVP Migration](2026-05-26_input_layer_mvp_migration.md) — Core MVP
three-field input, real cash in `analysis_setup.cash_handling`, frozen 2026-05-26.

## Purpose / Big Picture

After this migration, a portfolio-first operator running
`python run_portfolio_review.py` (diagnosis) or `python run_portfolio_review.py --candidates equal_weight`
(one candidate) gets a **stable, product-facing Block 2.1** answer inside
`{output_dir_final}/analysis_subject/portfolio_xray.json`:

what the portfolio owns, where capital is concentrated, duplicate exposure warnings, and a short
economic-exposure summary — **without** optimization, candidates, scorecards, or trade instructions.

Block 2.1 is diagnostic-only capital allocation. It must treat **Cash USD** (real bank cash) as a
normal holding with synthetic taxonomy, never substituting `cash_proxy_ticker` (BIL).

## Progress

- [x] (2026-05-26) Read `PLANS.md`, portfolio X-Ray specs, Input Layer freeze, operator guide, code audit.
- [x] (2026-05-26) **Session 01 — Audit & inventory:** Code/doc inventories, gap list, target contract sketch, Session 02–08 plan; registered ExecPlan as **Active** in [docs/exec_plans/README.md](README.md). No application code changes.
- [x] (2026-05-26) **Session 02 — Product contract:** `portfolio_xray_diagnostics_spec.md` §2.1.1–§2.1.2; layer spec + OUTPUTS; `DEC-2026-05-26-002`; `verify_docs.py` OK.
- [x] (2026-05-26) **Session 03 — Builder:** `src/block_2_1_asset_allocation.py`, wired into `build_portfolio_xray_v2`; enriched taxonomy for legacy `asset_allocation`; `tests/test_block_2_1_asset_allocation.py` + threshold registry test.
- [x] (2026-05-26) **Session 04 — Input connection:** `resolved_analysis_weights` in `analysis_setup.py`; X-Ray uses Input Layer weights; legacy `cash_weight` prefers real cash; MVP cash fixture regression tests; Input Layer pytest gate.
- [x] (2026-05-26) **Session 05 — Fixture:** `tests/fixtures/mvp_portfolios/demo_usd_asset_allocation_with_cash_5pct.yml` (config tickers, 5% Cash USD).
- [x] (2026-05-26) **Session 06 — Tests:** `tests/test_block_2_1_asset_allocation.py` (+ `tests/test_block_2_1_threshold_registry.py`); demo fixture integration, §2.1.1 contract guard, 21 pytest passed.
- [x] (2026-05-26) **Session 07 — Pipeline integration:** `analysis_subject/portfolio_xray.json` via `_xray_summary_from_output_dir` on materialize path; manifest `subject_diagnostics_contract`; offline fixtures + live E2E gate; `tests/test_block_2_1_pipeline_integration.py`.
- [x] (2026-05-26) **Session 08 — Live run & closure:** Diagnosis + one-candidate live runs; `validate_one_candidate_demo.py` PASS; acceptance audit; `CHANGELOG.md` / `DECISIONS.md`; plan **Completed**.

## Surprises & Discoveries

- Observation: Block 2.1 allocation logic already exists as `sections.asset_allocation` inside `portfolio_xray_v2`, not as a separate product JSON file.
  Evidence: `src/portfolio_xray.py` `_allocation_section`, `build_portfolio_xray_v2`; `grep duplicate_group portfolio_xray.py` → no matches.

- Observation: `Cash USD` is implemented in Input Layer and metrics pipeline but has **no** row in `config/etf_universe.yml`; X-Ray would classify it as unknown taxonomy today.
  Evidence: `src/real_cash.py`; `tests/test_input_layer_mvp_regression.py`; `_allocation_section` increments `unknown_weight` when taxonomy row missing.

- Observation: Capital-weight concentration thresholds requested for Block 2.1 MVP are **not** in `XRAY_THRESHOLDS` (registry is RC/hidden-risk/archetype oriented).
  Evidence: `src/portfolio_xray.py` `XRAY_THRESHOLDS` keys; `docs/specs/portfolio_xray_diagnostics_spec.md` §8 table.

- Observation: `duplicate_group_id` / `canonical_ticker` are validated at universe load (`src/etf_universe.py`) but never surfaced in X-Ray allocation output.
  Evidence: `tests/test_etf_universe.py` duplicate group tests; no `duplicate` in `portfolio_xray.py`.

- Observation: Demo root `config.yml` has eight market tickers summing to 100% with **no** real cash; `minimal_usd_with_cash.yml` uses 10% cash, not 5%.
  Evidence: `config.yml` lines 9–19; `tests/fixtures/mvp_portfolios/minimal_usd_with_cash.yml`.

## Decision Log

- Decision: Add product contract as top-level `block_2_1_asset_allocation` inside `portfolio_xray.json`; keep legacy `sections.asset_allocation.items[]` unchanged.
  Rationale: Operator guide step 2 already points to `analysis_subject/portfolio_xray.json`; six-file product bundle stays unchanged; golden contract tests depend on `items[]` shape.
  Date/Author: 2026-05-26 / agent (Session 01 audit).

- Decision: Implement builder in new module `src/block_2_1_asset_allocation.py`, called from `build_portfolio_xray_v2`.
  Rationale: `portfolio_xray.py` is already large (~4k lines); Block 2.1 has distinct thresholds and product shaping.
  Date/Author: 2026-05-26 / agent.

- Decision: Session 05 fixture uses `config.yml` tickers rescaled ×0.95 + `Cash USD: 0.05`; do not change root `config.yml` until Session 08 live demo unless operator requests it.
  Rationale: Preserve default demo config; deterministic test fixture name `demo_usd_asset_allocation_with_cash_5pct.yml`.
  Date/Author: 2026-05-26 / agent.

- Decision: Do not reopen Input Layer design; only bug-fix pass-through if Block 2.1 cannot read weights/cash_handling.
  Rationale: `DEC-2026-05-26-001` / input spec § Contract freeze.
  Date/Author: 2026-05-26 / agent.

- Decision: Sector/subtype/thematic tags remain **out** of core Block 2.1 product contract (advanced); sector may remain in legacy `items[]` breakdowns.
  Rationale: User brief “later / advanced, not core now”.
  Date/Author: 2026-05-26 / agent.

- Decision: Duplicate-group diagnostic severity uses fixed 10% / 20% combined-weight bands (not in `ALLOCATION_CONCENTRATION_THRESHOLDS` table).
  Rationale: Separate product rule from single-bucket dominance; documented in spec §2.1.1.
  Date/Author: 2026-05-26 / agent (Session 02).

## Outcomes & Retrospective

**Session 01 (2026-05-26):** Audit and ExecPlan foundation complete. Inventories below are the Session 01 deliverable.

**Session 02 (2026-05-26):** Normative product contract in [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.1.1 (`block_2_1_asset_allocation` field tables), §2.1.2 (`ALLOCATION_CONCENTRATION_THRESHOLDS`), top-level JSON contract updated to `portfolio_xray_v2` + optional `block_2_1_asset_allocation`. [portfolio_xray_layer_spec.md](../specs/portfolio_xray_layer_spec.md) and [OUTPUTS.md](../../OUTPUTS.md) Block 2 row updated. Decision `DEC-2026-05-26-002`.

**Session 03 (2026-05-26):** Implemented `src/block_2_1_asset_allocation.py` (`build_block_2_1_asset_allocation`, `enrich_taxonomy_with_real_cash`, `ALLOCATION_CONCENTRATION_THRESHOLDS`). `build_portfolio_xray_v2` emits `block_2_1_asset_allocation` and passes enriched taxonomy to `_allocation_section`. Tests: `tests/test_block_2_1_asset_allocation.py` (7 passed), `tests/test_block_2_1_threshold_registry.py` (1 passed). Next: Session 04 input regression + Session 05 fixture.

**Session 04 (2026-05-26):** `resolved_analysis_weights` wires Block 2.1 and legacy X-Ray to `analysis_setup.analysis_portfolio.weights` (snapshot weights still override when non-empty). Legacy `asset_allocation_summary.cash_weight` sums real-cash holdings instead of `cash_proxy_ticker`. Regression: `tests/test_block_2_1_asset_allocation.py` MVP `minimal_usd_with_cash.yml` path; `tests/test_input_layer_mvp_regression.py` gate unchanged. Next: Session 05 fixture.

**Session 05 (2026-05-26):** Added `tests/fixtures/mvp_portfolios/demo_usd_asset_allocation_with_cash_5pct.yml` (`config.yml` weights ×0.95 + `Cash USD: 0.05`). Fixture validation in `tests/test_mvp_portfolio_fixtures.py`; `tests/fixtures/README.md` updated. Next: Session 06 Block 2.1 tests against this fixture.

**Session 06 (2026-05-26):** Expanded `tests/test_block_2_1_asset_allocation.py` with `assert_block_2_1_product_contract` (§2.1.1 shape), demo-fixture snapshot assertions (SCHD 16.15%, top3 43.7%, 5% Cash USD, 9 holdings), concentration/economic-summary checks, duplicate medium-only band, breakdown sort guard. `tests/test_block_2_1_threshold_registry.py` unchanged. Verification: `python -m pytest tests/test_block_2_1_asset_allocation.py tests/test_block_2_1_threshold_registry.py tests/test_portfolio_xray_contract.py -q` → **21 passed**. Next: Session 07 pipeline integration.

**Session 07 (2026-05-26):** Pipeline wiring verified end-to-end: `run_report` / `_xray_summary_from_output_dir` writes `block_2_1_asset_allocation` under `analysis_subject/`; `product_bundle_manifest_extra()` adds `subject_diagnostics_contract` (Block 2.1 nested in `portfolio_xray_json`); offline seeds use `refresh_analysis_subject_portfolio_xray`; `live_core_e2e` / `live_full_e2e` require Block 2.1; `tests/test_block_2_1_pipeline_integration.py` (diagnosis + one-candidate plan modes, materialize path, manifest note). Verification: `python -m pytest tests/test_block_2_1_pipeline_integration.py tests/test_block_2_1_asset_allocation.py tests/test_portfolio_xray_contract.py tests/test_product_bundle_paths.py tests/test_blocks_1_5_mvp_smoke.py -q` → **25+ passed**. Next: Session 08 live demo + closure.

**Session 08 (2026-05-26):** Live closure complete. Commands: `run_portfolio_review.py --skip-candidates`, `--candidates equal_weight`, `validate_one_candidate_demo.py` **PASS**; pytest closure bundle **44 passed**; `verify_docs.py` OK. Live demo `config.yml` Block 2.1: 8 holdings, SCHD top1 **17.0%**, top3 **46.0%**, US region medium + USD currency medium/high flags. Fixture-locked real-cash numbers in [acceptance audit](../audits/2026-05-26_block_2_1_asset_allocation_acceptance_audit.md) §4 (SCHD **16.15%**, top3 **43.7%**, Cash USD **5%**). ExecPlan **Completed**; gaps G1–G8 closed; G9–G11 deferred post-MVP per plan.

## Context and Orientation

Portfolio MRI is diagnosis-first. Block 2.1 is the first Portfolio X-Ray sub-block: **what do I
actually own and where is capital concentrated?**

Pipeline today (portfolio-first):

```text
config.yml (tickers, current_weights, investor_currency)
  -> validate_config / build_analysis_setup
  -> run_report.py --materialize-analysis-subject
  -> snapshots, stress_report, portfolio metrics
  -> build_portfolio_xray_v2 (src/portfolio_xray.py)
  -> {output_dir_final}/analysis_subject/portfolio_xray.json
  -> problem_classification.json (reads sections.asset_allocation heuristically)
```

Legacy policy path may also write root `{output_dir_final}/portfolio_xray.json`; portfolio-first
truth is **`analysis_subject/`** per [product_flow_operator_guide.md](../product_flow_operator_guide.md).

## Session 01 — Current State Audit

### 1. Allocation-related code inventory

| Path | Role | Block 2.1 relevance |
| --- | --- | --- |
| [src/portfolio_xray.py](../../src/portfolio_xray.py) | `_allocation_section`, `_weight_concentration_item`, `_aggregate_values`, `build_portfolio_xray_v2`, formatters | **Primary** — partial 2.1 in `sections.asset_allocation` |
| [src/risk_budgeting.py](../../src/risk_budgeting.py) | `load_merged_universe_rows`, `risk_budget_bucket_from_row` | Taxonomy load + `risk_bucket` derivation |
| [src/etf_universe.py](../../src/etf_universe.py), [src/stock_universe.py](../../src/stock_universe.py) | Universe YAML + validation | Taxonomy source; `duplicate_group_id` validation |
| [src/real_cash.py](../../src/real_cash.py) | Real cash labels, zero-return panels, `cash_handling` enrichment | Input/metrics — **not** wired to X-Ray taxonomy yet |
| [src/analysis_setup.py](../../src/analysis_setup.py) | Weights, `cash_handling`, subject type | Weight source for X-Ray |
| [src/snapshot.py](../../src/snapshot.py) | `_xray_summary_from_output_dir` | Writes/loads `portfolio_xray.json` on report path |
| [run_report.py](../../run_report.py) | Full report orchestration | Produces subject diagnostics |
| [src/problem_classification.py](../../src/problem_classification.py) | `_collect_allocation` | Downstream; text grep for "concentration" only |
| [src/candidate_comparison.py](../../src/candidate_comparison.py) | `weight_concentration` on comparison rows | Cross-artifact top1/top3/HHI formulas aligned with X-Ray |
| [src/data_trust_signals.py](../../src/data_trust_signals.py) | Rolls X-Ray section warnings | Trust surfacing for UI |

**Planned (Sessions 03–04):** `src/block_2_1_asset_allocation.py` — does not exist yet.

### 2. Taxonomy fields inventory

ETF/stock universe **required** annotation fields (from `src/etf_universe.py` `REQUIRED_FIELDS`):

`ticker`, `name`, `issuer`, `asset_class`, `subtype`, `sector`, `thematic_primary`, `thematic_tags`,
`risk_role` (list), `main_risk_factor`, `secondary_risk_factors`, `region`, `currency_exposure`,
`duration_bucket`, `credit_quality`, `duplicate_group_id`, `canonical_ticker`, `data_source`.

**Used today in X-Ray allocation** (`_allocation_section` holding items + breakdown dimensions):

| Taxonomy field | In holding item | In breakdown dimension |
| --- | --- | --- |
| `asset_class` | yes | yes |
| `region` | yes | yes |
| `currency_exposure` | yes | yes (as `currency_exposure`) |
| `sector` | yes | yes |
| `risk_role` | yes (list, split weight) | yes |
| `main_risk_factor` | yes | yes |
| `secondary_risk_factors` | yes (stored, not aggregated in MVP product contract) | no |
| `duration_bucket`, `credit_quality` | yes (stored) | no |
| derived `risk_bucket` | yes | yes |
| `duplicate_group_id`, `canonical_ticker` | **no** | **no** |
| `subtype`, `thematic_*` | **no** | **no** |

**Real cash (planned synthetic row, Session 04):** `asset_class=cash`, `currency_exposure` from label,
`risk_role=[cash, liquidity, defensive]`, `main_risk_factor=cash`, `taxonomy_source=real_cash_synthetic_v1`.

### 3. Existing JSON / output inventory

| Artifact | Location | Product-ready? | Notes |
| --- | --- | --- | --- |
| `portfolio_xray.json` | `{output_dir_final}/analysis_subject/` | **Partial** | Seven sections; 2.1 is internal `items[]` model |
| `sections.asset_allocation` | inside above | Internal | `holding`, `breakdown`, `weight_concentration` items |
| `legacy_summary.asset_allocation_summary` | inside above | Overview | top1/top3/HHI; uses `cash_proxy_ticker` weight for `cash_weight` — not real cash |
| `block_2_1_asset_allocation` | — | **Missing** | Target MVP product contract (Session 03) |
| `asset_allocation.json` (standalone) | — | Not used | Would break operator read order |
| Six-file product bundle | variant root | N/A | Does not include X-Ray; step 2 is separate |
| `problem_classification.json` | `analysis_subject/` | Downstream | Weak allocation signal via text grep |
| `ai_commentary_context.json` | variant root | Future hook | No Block 2.1 fields yet |

### 4. Config and fixtures inventory

| File | Purpose |
| --- | --- |
| [config.yml](../../config.yml) | Demo 8-ticker USD portfolio, no cash, weights sum 1.0 |
| [config.yml.example](../../config.yml.example) | MVP-first template |
| [tests/fixtures/mvp_portfolios/minimal_usd_no_cash.yml](../../tests/fixtures/mvp_portfolios/minimal_usd_no_cash.yml) | Input regression |
| [tests/fixtures/mvp_portfolios/minimal_usd_with_cash.yml](../../tests/fixtures/mvp_portfolios/minimal_usd_with_cash.yml) | 10% Cash USD |
| [tests/fixtures/portfolio_xray_golden_v2.json](../../tests/fixtures/portfolio_xray_golden_v2.json) | Golden `portfolio_xray_v2` contract |

**Session 05 target:** `tests/fixtures/mvp_portfolios/demo_usd_asset_allocation_with_cash_5pct.yml`.

### 5. Test inventory (allocation / X-Ray)

| Test module | Coverage |
| --- | --- |
| [tests/test_portfolio_xray.py](../../tests/test_portfolio_xray.py) | `test_portfolio_xray_weight_concentration_in_asset_allocation`, taxonomy partial/unknown |
| [tests/test_portfolio_xray_contract.py](../../tests/test_portfolio_xray_contract.py) | Golden v2 shape, `has_weight_concentration` |
| [tests/test_portfolio_xray_threshold_registry.py](../../tests/test_portfolio_xray_threshold_registry.py) | `XRAY_THRESHOLDS` drift — **no** allocation capital thresholds |
| [tests/test_real_cash.py](../../tests/test_real_cash.py), [tests/test_input_layer_mvp_regression.py](../../tests/test_input_layer_mvp_regression.py) | Input Layer cash — not X-Ray allocation |
| [tests/test_blocks_1_5_mvp_smoke.py](../../tests/test_blocks_1_5_mvp_smoke.py) | Block 2 smoke via comparison weight_concentration |

**Session 06 target:** `tests/test_block_2_1_asset_allocation.py`.

### 6. Gap list (Session 01 → implementation backlog)

| ID | Gap | Priority | Session |
| --- | --- | --- | --- |
| G1 | No stable `block_2_1_asset_allocation` product contract | P0 | 02–03 |
| G2 | No `portfolio_composition_snapshot` / dominants as named fields | P0 | 03 |
| G3 | No `concentration_flags[]` with Medium/High severity rules | P0 | 02–03 |
| G4 | No `duplicate_exposure_flags[]` from taxonomy groups | P0 | 03 |
| G5 | No `actual_economic_exposure_summary` (headline + key_points) | P0 | 03 |
| G6 | Real cash → unknown taxonomy in allocation | P0 | 04 |
| G7 | `legacy_summary.cash_weight` uses cash proxy, not real cash | P1 | 04 or document as legacy-only |
| G8 | Capital allocation thresholds not in spec registry | P0 | 02 |
| G9 | Sector in legacy items but excluded from product contract | P2 | 02 (document) |
| G10 | `problem_classification` does not read structured flags | P2 | post-MVP |
| G11 | Report/HTML formatters do not render Block 2.1 product view | P2 | post-MVP |

### 7. Duplicated or legacy logic notes

- **Single implementation** of capital breakdowns: `_allocation_section` only (not duplicated in stress/metrics).
- **Legacy** `build_portfolio_xray_summary` / `legacy_summary` parallel to v2 sections — keep; Block 2.1 product view is additive.
- **Root vs sidecar** `portfolio_xray.json` — legacy policy runs; product-first uses `analysis_subject/`.
- **Scorecard / health** modules exist elsewhere; Block 2.1 must not call them (diagnostic-only boundary).

## Target Product Contract (normative in spec §2.1.1 since Session 02)

Top-level key on `portfolio_xray.json`:

```json
{
  "block": "2.1_asset_allocation",
  "analysis_subject": "current_portfolio",
  "analysis_mode": "analyze_current_weights",
  "investor_currency": "USD",
  "portfolio_composition_snapshot": {
    "total_holdings": 9,
    "top1_holding": { "ticker": "SCHD", "weight_pct": 16.15 },
    "top3_holdings": [
      { "ticker": "SCHD", "weight_pct": 16.15 },
      { "ticker": "BND", "weight_pct": 15.2 },
      { "ticker": "QQQ", "weight_pct": 12.35 }
    ],
    "top3_weight_pct": 43.7,
    "dominant_asset_class": { "name": "equity", "weight_pct": null },
    "dominant_risk_role": { "name": null, "weight_pct": null },
    "dominant_main_risk_factor": { "name": null, "weight_pct": null },
    "dominant_region": { "name": null, "weight_pct": null },
    "dominant_currency": { "name": null, "weight_pct": null }
  },
  "capital_allocation_breakdown": {
    "by_asset": [],
    "by_asset_class": [],
    "by_main_risk_factor": [],
    "by_risk_role": [],
    "by_region": [],
    "by_currency": []
  },
  "concentration_flags": [],
  "duplicate_exposure_flags": [],
  "actual_economic_exposure_summary": {
    "headline": null,
    "key_points": []
  },
  "data_quality_warnings": [],
  "metadata": {
    "source": "core_mvp_input",
    "cash_treatment": "real_cash_position_if_present",
    "cash_proxy_used_for_real_cash": false
  }
}
```

Weights in code: fractions 0–1; `weight_pct` at export = fraction × 100, rounded per [metrics_specification.md](../specs/metrics_specification.md) export rules (3 decimals where applicable).

### MVP concentration thresholds (to register in Session 02)

| `flag_id` | Medium | High |
| --- | ---: | ---: |
| `top_holding_concentration` | top1 ≥ 20% | top1 ≥ 30% |
| `top3_concentration` | top3 ≥ 50% | top3 ≥ 65% |
| `single_asset_class_dominance` | class ≥ 60% | class ≥ 75% |
| `single_main_risk_factor_dominance` | factor ≥ 60% | factor ≥ 75% |
| `single_region_dominance` | region ≥ 70% | region ≥ 85% |
| `single_currency_dominance` | currency ≥ 70% | currency ≥ 85% |

Registry name: `ALLOCATION_CONCENTRATION_THRESHOLDS` in `src/block_2_1_asset_allocation.py` (separate from `XRAY_THRESHOLDS` to avoid RC drift tests).

## Plan of Work (Sessions 02–08)

Session 02 updates [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) with §2.1.1
and threshold table; links from [portfolio_xray_layer_spec.md](../specs/portfolio_xray_layer_spec.md).

Session 03–04 implement `build_block_2_1_asset_allocation()` and call it from `build_portfolio_xray_v2`
after `_allocation_section`, passing enriched taxonomy (YAML + real-cash synthetic).

Session 05 adds the 5% cash fixture from `config.yml` weights × 0.95 + `Cash USD: 0.05`.

Session 06 adds unit/integration tests; Session 07 verifies product runtime modes; Session 08 live
demo + closure docs.

## Concrete Steps

**Session 01 (completed 2026-05-26):**

    Working directory: repository root

    # Confirm allocation entrypoints exist
    rg "_allocation_section|build_portfolio_xray_v2" src/portfolio_xray.py

    # Confirm duplicate_group not in X-Ray yet
    rg "duplicate_group" src/portfolio_xray.py

    # Docs link check (optional)
    python scripts/verify_docs.py

**Session 02 (completed 2026-05-26):** Spec §2.1.1–§2.1.2; `python scripts/verify_docs.py` → OK.

**Session 03 (next):** Implement `src/block_2_1_asset_allocation.py`.

**Session 06 (future):**

    python -m pytest tests/test_block_2_1_asset_allocation.py tests/test_portfolio_xray.py tests/test_portfolio_xray_contract.py -q

**Session 08 (future):**

    python run_portfolio_review.py --skip-candidates
    python run_portfolio_review.py --candidates equal_weight
    python scripts/validate_one_candidate_demo.py

## Validation and Acceptance

**Session 02 acceptance (met 2026-05-26):**

- `docs/specs/portfolio_xray_diagnostics_spec.md` contains §2.1.1 and §2.1.2 with stable field names.
- Top-level `portfolio_xray.json` contract documents `block_2_1_asset_allocation`.
- `python scripts/verify_docs.py` passes.

**Session 01 acceptance (met 2026-05-26):**

- Written inventories for code, taxonomy fields, outputs, config/fixtures, tests.
- Gap list G1–G11 with session mapping.
- Target contract and thresholds documented in this ExecPlan.
- No application code changes (docs-only Session 01).

**Full plan acceptance (Session 08):**

- `analysis_subject/portfolio_xray.json` contains populated `block_2_1_asset_allocation` on diagnosis and one-candidate runs.
- Cash USD 5% fixture tests pass; `validate_one_candidate_demo.py` PASS; final report with exact Block 2.1 numbers.

## Idempotence and Recovery

Session 01 is read-only. Later sessions are additive to `portfolio_xray.json`. Re-running
`run_portfolio_review.py` overwrites generated artifacts under `Main portfolio/` — expected.

## Artifacts and Notes

Session 01 evidence commands (2026-05-26):

    rg "_allocation_section" src/portfolio_xray.py
    # -> _allocation_section defined ~line 963, used in build_portfolio_xray_v2

    rg "duplicate_group" src/portfolio_xray.py
    # -> no matches

## Interfaces and Dependencies

**End state (Session 03):** in `src/block_2_1_asset_allocation.py`:

    ALLOCATION_CONCENTRATION_THRESHOLDS: dict[str, float]

    def build_block_2_1_asset_allocation(
        *,
        analysis_setup: dict[str, Any] | None,
        weights: dict[str, float],
        taxonomy_rows: dict[str, dict[str, Any]] | None,
        taxonomy_sources: dict[str, str] | None,
    ) -> dict[str, Any]: ...

    def enrich_taxonomy_with_real_cash(
        weights: dict[str, float],
        taxonomy_rows: dict[str, dict[str, Any]],
        taxonomy_sources: dict[str, str],
    ) -> tuple[dict[str, dict[str, Any]], dict[str, str]]: ...

**Consumer:** `build_portfolio_xray_v2` sets `result["block_2_1_asset_allocation"] = ...`.

---

**Revision note (2026-05-26):** Initial ExecPlan created; Session 01 audit inventories and gap list committed; plan registered Active.

**Revision note (2026-05-26):** Session 02 — normative contract in diagnostics spec §2.1.1–§2.1.2; DEC-2026-05-26-002; OUTPUTS + layer spec sync.

**Revision note (2026-05-26):** Session 08 — plan **Completed**; live demo + [acceptance audit](../audits/2026-05-26_block_2_1_asset_allocation_acceptance_audit.md).
