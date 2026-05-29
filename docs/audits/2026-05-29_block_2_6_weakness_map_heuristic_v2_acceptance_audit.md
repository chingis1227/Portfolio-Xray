# Block 2.6 Portfolio Weakness Map — heuristic_v2 Acceptance Audit (Session 09)

Date: 2026-05-29

Purpose: Close [Block 2.6 heuristic_v2 institutional upgrade ExecPlan](../exec_plans/2026-05-29_block_2_6_weakness_map_heuristic_v2_plan.md) **Session 09** and record whether the product-facing `block_2_6_portfolio_weakness_map` contract (`heuristic_v2`, eight canonical Stress Lab risk ids) is accepted on portfolio-first diagnosis.

Related:

- v1 closure: [Block 2.6 MVP acceptance audit](2026-05-26_block_2_6_portfolio_weakness_map_acceptance_audit.md) (`heuristic_v1`, nine weakness ids)
- Baseline: [Session 00 baseline audit](2026-05-29_block_2_6_session_00_baseline_audit.md)
- Tests: [Session 08 tests + golden](2026-05-29_block_2_6_session_08_tests_golden.md)
- Canonical contract: [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.6.1
- Decision: `DEC-2026-05-29-001`
- Implementation: `src/block_2_6_portfolio_weakness_map.py`, `build_portfolio_xray_v2` in `src/portfolio_xray.py`

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is `block_2_6_portfolio_weakness_map` on live diagnosis path with `heuristic_v2`? | **Yes** — subject X-Ray `metadata.rule_version` **heuristic_v2**, eight canonical `risk_type` rows. |
| Are `risk_type` values aligned with Stress Lab synthetic ids? | **Yes** — order matches `SYNTHETIC_SCENARIO_IDS`; `volatility_spike` absent from product block. |
| Is USD shock scored or explicitly blocked? | **Yes** — live subject: **Medium** 55; golden fixture documents `blocked_upstream_fields` when FX fields missing. |
| Does Block 2.6 consume Block 2.4 v2 fields? | **Yes** — alert `status`, `score`, `confidence`, `contributing_assets`, `limitations` on equity, rates, credit, liquidity, recession rows. |
| Is Stress Lab boundary enforced? | **Yes** — module import isolation + forbidden-key tests; no stress PnL in product block JSON. |
| Is narrative institutional (non-boilerplate)? | **Yes** — `short_diagnosis` / `why_status` / `key_evidence` (3–5) tied to evidence rows; anti-boilerplate unit assertion. |
| Is downstream SSOT Block 2.6? | **Yes** — Problem Classification + AI commentary grounding read `block_2_6_portfolio_weakness_map`; legacy `sections.weakness_map` tagged `legacy: true`. |
| Is heuristic_v2 ExecPlan accepted (Sessions 00–09)? | **Yes — 10/10** sessions complete (see §2). |

**Bottom line:** Block 2.6 **heuristic_v2** is **accepted**. Operators use eight pre-stress vulnerability hypotheses with canonical Stress Lab ids, transparent scores, and `next_tests` routing; Stress Lab continues to own scenario losses and pass/fail.

---

## 2. Session Rollup (00–09)

| Session | Objective | Status | Primary evidence |
| --- | --- | --- | --- |
| 00 | Baseline audit + gap matrix | **Done** | [Session 00 audit](2026-05-29_block_2_6_session_00_baseline_audit.md) |
| 02 | Contract v2 (spec §2.6.1, Pareto UI spec, DECISIONS) | **Done** | `DEC-2026-05-29-001`; [Pareto UI spec](../specs/block_2_6_weakness_map_ui_pareto_spec.md) |
| 03 | Rule engine `heuristic_v2`, eight risks | **Done** | `RISK_RULE_TABLES`, `RISK_TYPES` in `block_2_6_portfolio_weakness_map.py` |
| 04 | USD shock scoring / blocked fields | **Done** | `blocked_upstream_fields`; unit + live scored `usd_shock` |
| 05 | Block 2.4 v2 integration | **Done** | v2 alert fields in evidence + `linked_assets` |
| 06 | Narrative layer | **Done** | `short_diagnosis`, `why_status`, `key_evidence` |
| 07 | Downstream SSOT | **Done** | `problem_classification.py`, `ai_commentary_context.py` |
| 08 | Tests, golden, live validation | **Done** | [Session 08 audit](2026-05-29_block_2_6_session_08_tests_golden.md) |
| 09 | Documentation + acceptance closure | **Done** | This document; CHANGELOG; ExecPlan **Completed** |

---

## 3. ExecPlan Acceptance Criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Eight canonical `risk_type` = `SYNTHETIC_SCENARIO_IDS` | **PASS** | `test_canonical_risk_types_match_stress_lab_synthetic_ids`; live §5.1 |
| 2 | Each risk: score or Unavailable + severity band | **PASS** | `assert_block_2_6_product_contract`; live table §5.1 |
| 3 | USD: scored or Unavailable + `blocked_upstream_fields` | **PASS** | `test_usd_shock_*`; live `usd_shock` Medium 55 |
| 4 | Block 2.4 v2 fields consumed where mapped | **PASS** | equity `linked_assets`; duration/credit/tail evidence rows |
| 5 | No `stress_report` dependency in Block 2.6 | **PASS** | `tests/test_block_2_6_stress_boundary.py` |
| 6 | Narrative uses real signals (no generic boilerplate) | **PASS** | `GENERIC_NARRATIVE_BOILERPLATE` assertion; live `boiler False` on all rows |
| 7 | Problem Classification + AI grounding use Block 2.6 | **PASS** | `tests/test_problem_classification.py`, `tests/test_ai_commentary_context.py` |
| 8 | Pytest closure + live subject documented | **PASS** | §4, §5 |

**Block 2.6 Portfolio Weakness Map heuristic_v2: ACCEPTED.**

---

## 4. Verification Commands

```bash
python -m pytest tests/test_block_2_6_portfolio_weakness_map.py tests/test_block_2_6_stress_boundary.py tests/test_portfolio_xray_contract.py tests/test_problem_classification.py tests/test_ai_commentary_context.py tests/test_product_bundle_paths.py -q
python scripts/verify_docs.py
```

| Check | Result (2026-05-29) |
| --- | --- |
| Closure pytest bundle | **68 passed** |
| `verify_docs.py` | **OK** (after Session 09 doc adds) |

Regenerate golden after intentional Block 2.6 contract changes:

```bash
python tests/portfolio_xray_golden_inputs.py
```

---

## 5. Live Verification (root `config.yml`)

Artifact: `Main portfolio/analysis_subject/portfolio_xray.json` (portfolio-first `--skip-candidates`, warm cache).

### 5.1 Block envelope

| Field | Observed |
| --- | --- |
| `status` | **partial** |
| `metadata.rule_version` | **heuristic_v2** |
| `metadata.stress_lab_separation` | `no_stress_pnl_or_attribution` |
| `metadata.legacy_risk_aliases` | Present (v1 → canonical map) |
| `risk_types` count | **8** |
| `sections.weakness_map.legacy` | **true** |
| `sections.weakness_map.product_surface` | **false** |

### 5.2 Eight canonical risk types

| `risk_type` | Score | Severity | Notes |
| --- | ---: | --- | --- |
| `equity_shock` | 40 | Medium | `next_tests` includes `equity_shock` |
| `credit_shock` | 11 | Low | |
| `rates_shock` | 65 | Medium | |
| `inflation_stagflation` | 41 | Medium | |
| `liquidity_shock` | 19 | Low | |
| `usd_shock` | 55 | Medium | Scored (FX fields available on subject) |
| `commodity_shock` | 28 | Low | |
| `recession_severe` | — | Unavailable | Insufficient evaluable signal coverage (contract-allowed) |

### 5.3 Stress boundary (product block)

| Check | Result |
| --- | --- |
| `stress_report` key in block JSON | **Absent** |
| `scenario_results` / `pnl_by_asset_pct` in block | **Absent** |
| Forbidden upstream keys alter scores | **No** (parametrized boundary test) |

---

## 6. Deferred / Non-goals (unchanged)

| Item | Status |
| --- | --- |
| `volatility_spike` in product Block 2.6 | **Excluded** — legacy `sections.weakness_map` only |
| Scenario loss numbers on Block 2.6 | **Out of scope** — Stress Lab owns PnL |
| Retire legacy `sections.weakness_map` | **Deferred** — formatters/golden compatibility |

---

## 7. Sign-off

| Criterion | Status |
| --- | --- |
| Acceptance criteria §3 all PASS | **Done** |
| Live subject X-Ray validated | **Done** |
| Documentation synced (SPEC, diagnostics spec, CHANGELOG, registers) | **Done** |
| ExecPlan marked **Completed** | **Done** |

**Next:** None for this ExecPlan. Future work only via explicit product change (e.g. retire legacy weakness section or extend scenario set).
