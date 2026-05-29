# Block 2.6 Portfolio Weakness Map — Session 00 Baseline Audit

Date: 2026-05-29

Purpose: Establish the institutional-upgrade baseline for `block_2_6_portfolio_weakness_map` before Session 02 (contract v2). Read-only audit: inventory implementation, risk ID alignment vs Stress Lab, downstream consumers, upstream signal inventory from Blocks 2.1–2.5, and gap matrix vs heuristic_v2 target.

Related:

- Product contract (v1): [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.6.1
- v1 closure: [2026-05-26_block_2_6_portfolio_weakness_map_plan.md](../exec_plans/2026-05-26_block_2_6_portfolio_weakness_map_plan.md) (**Completed**)
- v2 upgrade plan: [2026-05-29_block_2_6_weakness_map_heuristic_v2_plan.md](../exec_plans/2026-05-29_block_2_6_weakness_map_heuristic_v2_plan.md) (**Active**)
- Implementation: `src/block_2_6_portfolio_weakness_map.py` → `build_block_2_6_portfolio_weakness_map`
- Stress Lab canonical IDs: `src/scenario_library.py` → `SYNTHETIC_SCENARIO_IDS`

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is Block 2.6 implemented as Core MVP product block? | **Yes** — top-level `block_2_6_portfolio_weakness_map` on `portfolio_xray.json`; `heuristic_v1`; 9 risk types. |
| Does it avoid reading Stress Lab / `stress_report`? | **Yes** — inputs are Blocks 2.1–2.5 only; `FORBIDDEN_STRESS_KEYS` scan; no `stress_report` import in module. |
| Are risk type IDs aligned with Stress Lab? | **No** — product uses weakness namespace (`equity_crash`, `rates_up`, …); Stress Lab uses 8 synthetic `scenario_id` values. |
| Is `usd_shock` properly scored? | **No** — empty `RISK_RULE_TABLES` signals → always `Unavailable`. |
| Does Block 2.6 consume Block 2.4 `heuristic_v2`? | **No** — only integer `alerts.*.score`; ignores `status`, `confidence`, `contributing_assets`, `limitations`. |
| Is narrative institutional-grade? | **No** — generic `explanation` boilerplate; no `short_diagnosis` / `why_status` / capped `key_evidence`. |
| Is downstream single source of truth? | **No** — Problem Classification + X-Ray HTML/text still driven by legacy `sections.weakness_map` (stress-coupled). |
| Institutional v2 complete? | **No** — Session 02+ required. |

**Bottom line:** Block 2.6 v1 delivers a valid pre-stress boundary and rule-based scores, but is **not** advisor-ready: wrong risk IDs vs Stress Lab, thin factor panel, placeholder USD, no 2.4 v2 integration, split downstream surfaces.

---

## 2. Files Inventoried

| Role | Path |
| --- | --- |
| Implementation | `src/block_2_6_portfolio_weakness_map.py` (~1040 lines) |
| Wiring | `src/portfolio_xray.py` L3496+ (`build_portfolio_xray_v2` after Block 2.5) |
| Upstream | `src/block_2_1_asset_allocation.py`, `block_2_2_portfolio_metrics.py`, `block_2_3_factor_exposure.py`, `block_2_4_hidden_exposure.py` (**heuristic_v2**), `block_2_5_risk_budget_view.py` |
| Legacy parallel | `src/portfolio_xray.py` → `_weakness_map_section()` (~L3197+); reads `stress_report` |
| Downstream (product) | `src/product_bundle_paths.py`, `src/live_core_e2e.py`, `src/live_full_e2e.py`, `src/ai_commentary_context.py` (status/summary only) |
| Downstream (legacy) | `src/problem_classification.py` → `_collect_weakness_map`, `portfolio_xray.py` formatters |
| Spec | `docs/specs/portfolio_xray_diagnostics_spec.md` §2.6 / §2.6.1 |
| v1 acceptance | `docs/audits/2026-05-26_block_2_6_portfolio_weakness_map_acceptance_audit.md` |
| Tests | `tests/test_block_2_6_portfolio_weakness_map.py` (**5 passed**, 2026-05-29) |
| Contract | `tests/test_portfolio_xray_contract.py`, `scripts/core_mvp_validation_contract.py` |
| Golden | `tests/fixtures/portfolio_xray_golden_v2.json` (Block 2.6 subtree, `heuristic_v1`, 9 risks) |

No separate `weakness_map.json` in the six-file product bundle (correct).

---

## 3. Risk ID Naming Mismatch

### Stress Lab canonical (8 synthetic) — `SYNTHETIC_SCENARIO_IDS`

```
equity_shock, credit_shock, rates_shock, inflation_stagflation,
liquidity_shock, usd_shock, commodity_shock, recession_severe
```

Source: `src/scenario_library.py` L31–39; `docs/specs/stress_lab_layer_spec.md` §3.1.2.

### Block 2.6 product (9 weakness types) — `RISK_TYPES` in `block_2_6_portfolio_weakness_map.py`

```
equity_crash, rates_up, inflation_shock, credit_spreads, liquidity_shock,
usd_shock, commodity_shock, volatility_spike, recession
```

### Mapping required for v2

| v1 `risk_type` | Target canonical `risk_type` | `next_tests` today (canonical ids) |
| --- | --- | --- |
| `equity_crash` | `equity_shock` | equity_shock, recession_severe, liquidity_shock |
| `rates_up` | `rates_shock` | rates_shock, inflation_stagflation |
| `inflation_shock` | `inflation_stagflation` | inflation_stagflation, commodity_shock |
| `credit_spreads` | `credit_shock` | credit_shock, liquidity_shock, recession_severe |
| `liquidity_shock` | `liquidity_shock` | (id aligns; namespace differs) |
| `usd_shock` | `usd_shock` | usd_shock |
| `commodity_shock` | `commodity_shock` | commodity_shock, inflation_stagflation |
| `volatility_spike` | **remove from product block** | volatility_spike (not in Stress Lab active suite) |
| `recession` | `recession_severe` | recession_severe, credit_shock, equity_shock |

Legacy `sections.weakness_map` uses yet another namespace (`rates`, `inflation`, `credit`, `equity_crash`, …) plus stress PnL fields — must remain non-product-driving after v2 migration.

---

## 4. Current v1 Scoring Model

| Property | Value |
| --- | --- |
| `RULE_VERSION` | `heuristic_v1` |
| Status bands | Low 0–39, Medium 40–69, High 70–100, Unavailable if `score_0_100` null |
| Per-signal score | `_score_signal(value, moderate, high)` → 0–100 piecewise linear |
| Aggregate | Weighted mean over signals with non-null values; renormalize by evaluable weight |
| `minimum_evaluable_weight` | 0.55 (most risks); `usd_shock` 0.10 but **zero signals** |
| Rule tables exported in JSON | **No** — only `metadata.rule_version` |
| Generic explanation | Yes — fixed string: *"pre-stress heuristic based on already-computed portfolio diagnostics"* |

### Signals actually used in v1 (metric → source)

| Metric | Block | Used in risk types |
| --- | --- | --- |
| `equity_weight` | 2.1 `by_asset_class` | equity_crash |
| `rates_duration_weight` | 2.1 `by_main_risk_factor` | rates_up |
| `credit_liquidity_weight` | 2.1 | credit_spreads |
| `commodity_weight`, `real_assets_weight` | 2.1 | inflation_shock, commodity_shock |
| `downside_beta` | 2.2 | equity_crash, recession |
| `beta_rr_abs` | 2.3 | rates_up |
| `*_rc_pct`, `top1_rc_share` | 2.5 | several |
| `hidden_*_score_frac` (2.4 score/100) | 2.4 | equity, rates, credit, liquidity, vol |

### Signals available upstream but **not** used by v1

| Signal | Block | Notes |
| --- | --- | --- |
| `risk_on_weight`, `by_risk_role` | 2.1 | Used in Block 2.4 v2 |
| `by_currency`, `concentration_flags`, `investor_currency` | 2.1 / 2.2 | Needed for USD v2 |
| `beta_portfolio`, `corr_base`, rolling correlation panel | 2.2 | equity_shock v2 target |
| `beta_eq`, `beta_usd`, `beta_credit`, `beta_vix`, `beta_cmd` | 2.3 `factor_beta_snapshot` | v1 uses only `beta_rr` |
| `factor_variance_contribution` | 2.3 | Per-factor variance shares |
| Block 2.4 v2 fields | 2.4 | `status`, `confidence`, `confidence_reason`, `contributing_assets`, `limitations`, `blocked_upstream_fields` |
| `weak_hedge_behavior` alert | 2.4 | Excluded from 2.6 v1 entirely |

---

## 5. USD Shock Baseline

| Item | State |
| --- | --- |
| `RISK_RULE_TABLES["usd_shock"]["signals"]` | `[]` (empty) |
| Evidence row | `usd_sensitivity` = null, direction `missing`, source incorrectly tagged `block_2_2` |
| Typical live outcome | `severity: Unavailable`, limitation: FX not estimated in 2.1–2.5 |
| v2 path | Score via 2.1 currency + 2.3 `beta_usd` + variance share, **or** explicit `blocked_upstream_fields` |

Block 2.4 already implements `_currency_concentration_evidence` and `_investor_currency_mismatch` — reusable patterns for 2.6 USD scoring without reading `stress_report`.

---

## 6. Stress Lab Boundary (verified)

| Check | Result |
| --- | --- |
| `build_block_2_6_portfolio_weakness_map` parameters | Only `block_2_1` … `block_2_5`, optional `thresholds` |
| Module imports | No `stress`, `stress_report`, `hedge_gap` |
| Forbidden key scan | `FORBIDDEN_STRESS_KEYS` on upstream dicts → warning in `data_quality_warnings` |
| Block 2.3 indirect stress | Factor betas/variance built when X-Ray runs (`build_block_2_3_factor_exposure(stress_report=…)`); Block 2.6 reads **exported** 2.3 JSON only — acceptable per architecture |

**Gap for v2:** add dedicated `tests/test_block_2_6_stress_boundary.py` (AST/import guard) — not present in v1 closure bundle.

---

## 7. Downstream Consumers

| Consumer | Reads | Drives product conclusions? |
| --- | --- | --- |
| `block_2_6_portfolio_weakness_map` | Product v2 block | **Should** (target) |
| `sections.weakness_map` | Legacy section | **Today yes** for Problem Class + reports |
| `src/problem_classification.py` | Legacy only (`_collect_weakness_map`) | Yes — problem_ids from fuzzy `risk` string |
| `src/ai_commentary_context.py` | `block_2_6` `.status` / `.summary` only | Partial |
| `portfolio_xray.py` HTML/text/commentary | Legacy `weakness_map` section rows | Yes for client-facing X-Ray exports |
| `src/product_bundle_paths.py` | Presence check `portfolio_xray_has_block_2_6` | Contract gate only |
| `live_core_e2e` / `live_full_e2e` | Block 2.6 presence + risk count | Gate only |
| PDF (`pdf_reports.py`) | No direct weakness reference | — |

---

## 8. Current JSON Contract (v1)

### Top-level

Present: `block`, `block_id`, `block_name`, `status`, `summary`, `data_quality_warnings`, `metadata`, `risk_types`, `next_tests_global`.

Missing for v2: `diagnostics_meta`, `blocked_upstream_fields`, Pareto narrative fields, `legacy_risk_aliases`, advanced `signal_scores`.

### Per `risk_types[]`

Present: `risk_type`, `risk_title`, `score_0_100`, `severity`, `confidence`, `evidence[]`, `explanation`, `why_it_matters`, `next_tests`, `limitations`.

Missing for v2: `short_diagnosis`, `why_status`, `key_evidence`, `linked_assets`, `confidence_reason`, `data_quality_warnings` (per risk).

Golden: `tests/fixtures/portfolio_xray_golden_v2.json` — `status: partial`, nine risks, `equity_crash` Medium 49.

---

## 9. Baseline Tests

```text
pytest tests/test_block_2_6_portfolio_weakness_map.py -q
5 passed in 0.20s
```

Coverage today: contract shape, nine risks, evidence schema, stress-key warning on upstream, unavailable when all inputs missing.

**Gaps:** no per-risk scoring golden tables; no canonical ID contract; no narrative anti-boilerplate test; no stress boundary import test; no Block 2.4 v2 fixture integration.

---

## 10. Gap Matrix (v1 → heuristic_v2)

| # | Area | v1 | v2 target | Session |
| --- | --- | --- | --- | --- |
| G1 | Risk IDs | 9 weakness ids | 8 canonical Stress Lab ids | 02, 03 |
| G2 | `volatility_spike` | In product block | Remove (legacy section only) | 02, 03 |
| G3 | Rule transparency | Tables in code only | `diagnostics_meta` + advanced `signal_scores` | 02, 03 |
| G4 | Factor signals | `beta_rr` only | Full beta panel + variance shares | 03 |
| G5 | Block 2.4 | score/100 only | v2 status, confidence, contributors | 05 |
| G6 | USD | Always Unavailable | Score or explicit blocked fields | 04 |
| G7 | Narrative | Generic explanation | short_diagnosis, why_status, key_evidence | 06 |
| G8 | Downstream | Split legacy/product | Problem Class + reports → Block 2.6 | 07 |
| G9 | Tests / golden | 5 tests | Per-risk + boundary + live | 08 |
| G10 | Docs / acceptance | v1 audit | v2 spec + acceptance audit | 09 |

---

## 11. Session 00 Sign-off

| Criterion | Status |
| --- | --- |
| Implementation file and wiring located | **Done** |
| Risk ID mismatch documented | **Done** |
| Downstream consumer matrix documented | **Done** |
| Upstream signal inventory (used vs available) | **Done** |
| Gaps mapped to Sessions 02–09 | **Done** |

**Next:** Session 02 — contract v2 in diagnostics spec + DECISIONS + Pareto UI spec (Session 01 in user plan = this baseline audit).

---

*Audit author: Block 2.6 heuristic_v2 upgrade (Session 00). No code changes in this session.*
