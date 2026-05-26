# Input Layer MVP Migration — Acceptance Audit (Session 10)

Date: 2026-05-26

Purpose: Close [Input Layer MVP Migration ExecPlan](../exec_plans/2026-05-26_input_layer_mvp_migration.md) **Session 10** and record whether Core MVP input behavior (three-field surface, USD system defaults, real cash, disclosure export, portfolio-first integration) is accepted for «ДИАГНОСТИКА 2».

Related:

- Canonical spec: [input_assumptions_spec.md](../specs/input_assumptions_spec.md) (§ Core MVP, §1.1–1.6, Real Cash Holdings)
- [OUTPUTS.md](../../OUTPUTS.md) Blocks 1–5 MVP — Block 1 Input trust checks
- Offline regression: `tests/test_input_layer_mvp_regression.py` (Session 08)
- Product bundle validator: `scripts/validate_one_candidate_demo.py` (runtime truth; unchanged scope)

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Can Core MVP run with tickers + weights + `investor_currency` only? | **Yes** — `config.yml` demo + fixtures validate without mandate/liquidity/portfolio value. |
| Are USD RF / cash proxy / benchmark resolved without user entry? | **Yes** — live materialize logged `FRED:DTB3`, `BIL`, `SPY`; `analysis_setup.cash_handling.cash_proxy_ticker` = `BIL`. |
| Is real cash distinct from cash proxy? | **Yes** — normative rule in spec; `src/real_cash.py` + offline fixture `minimal_usd_with_cash.yml` covered in pytest (36 passed). |
| Is disclosure exported on diagnosis path? | **Yes** — post-materialize `run_metadata.json` includes `input_assumptions`, `input_surface`, `field_tiers`. |
| Does product one-candidate path still hold? | **Yes** — dry-run + on-disk `validate_one_candidate_demo.py` **PASS** (8 checks). |
| Is the full ExecPlan accepted? | **Yes — 10/10** criteria (see §3). |

**Bottom line:** Input Layer MVP migration is **complete**. Operators can use the slim Core MVP config and `config_ui` first screen; legacy/advanced keys remain in schema under `field_tiers` but are not required for `run_portfolio_review.py` diagnosis or one-candidate demo.

---

## 2. Session Rollup (01–10)

| Session | Objective | Status | Primary evidence |
| --- | --- | --- | --- |
| 01 | Contract & spec foundation | **Done** | `input_assumptions_spec.md` §1.1–1.6, Real Cash rule |
| 02 | MVP input normalization | **Done** | `src/mvp_input.py`, `tests/test_mvp_input_defaults.py` |
| 03 | Real cash holdings | **Done** | `src/real_cash.py`, `tests/test_real_cash.py` |
| 04 | Config & fixtures | **Done** | `tests/fixtures/mvp_portfolios/`, `config.yml.example` |
| 05 | config_ui MVP first screen | **Done** | `config_ui/app.py`, `tests/test_config_ui_mvp_first_screen.py` |
| 06 | Export & disclosure | **Done** | `input_surface`, `field_tiers` in `input_assumptions_v1` |
| 07 | Portfolio review integration | **Done** | `tests/test_mvp_portfolio_review_materialization.py` |
| 08 | Regression suite | **Done** | `tests/test_input_layer_mvp_regression.py` |
| 09 | Documentation sweep | **Done** | README, SPEC, WORKFLOW, OUTPUTS, GLOSSARY, operator guide |
| 10 | Acceptance report | **Done** | This document |

---

## 3. ExecPlan Acceptance Criteria

Criteria from ExecPlan § Acceptance Criteria (full migration):

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Core MVP config = tickers, weights/`current_weights`, `investor_currency` | **PASS** | Root `config.yml` (3 groups + technical run keys); fixtures ≤ 3 user keys |
| 2 | Real cash normative; proxy does not substitute | **PASS** | Spec + `tests/test_real_cash.py`; regression `minimal_usd_with_cash.yml` |
| 3 | USD defaults for RF, cash proxy, benchmark without user entry | **PASS** | Live materialize logs; `cash_handling.cash_proxy_ticker` = `BIL` in `run_metadata` |
| 4 | Client profile, liquidity, mandate caps, portfolio value not required for diagnosis | **PASS** | `resolved_config.client_profile` = null; dry-run diagnosis-only; deferred keys in `field_tiers` |
| 5 | Technical assumptions = backend defaults for Core MVP | **PASS** | `config.yml` technical block; `field_tiers` registry |
| 6 | Fixtures `minimal_usd_no_cash` / `minimal_usd_with_cash` pass validation | **PASS** | `tests/test_mvp_portfolio_fixtures.py` + regression gate |
| 7 | `product_diagnosis_only` / `product_one_candidate` unchanged | **PASS** | Dry-runs exit 0; runtime modes as documented |
| 8 | Six product bundle JSON on compare runs | **PASS** | `validate_one_candidate_demo.py` RESULT PASS |
| 9 | Documentation matches code | **PASS** | Session 09 sweep; `python scripts/verify_docs.py` OK |
| 10 | Targeted pytest suites pass | **PASS** | **36 passed** (MVP input layer bundle) |

**Input Layer MVP migration: ACCEPTED.**

---

## 4. Verification Executed (Session 10)

| Check | Command | Result |
| --- | --- | --- |
| Diagnosis-only dry-run | `python run_portfolio_review.py --dry-run` | Exit **0**; `product_diagnosis_only`; stages `input -> diagnosis` |
| One-candidate dry-run | `python run_portfolio_review.py --dry-run --candidates equal_weight` | Exit **0**; `product_one_candidate`; factory `--then-compare` |
| Demo config validation | `validate_config(config.yml)` | `analyze_current_weights`, `current_portfolio`, weights sum **1.0** |
| Live Block 1 materialize | `python run_report.py --materialize-analysis-subject --output-profile site_api --review-mode core --use-review-run-context` | Exit **0** (~85 s warm cache); `run_metadata` refreshed |
| On-disk product validator | `python scripts/validate_one_candidate_demo.py` | **PASS** (8 checks) |
| Input Layer pytest bundle | `pytest tests/test_mvp_portfolio_fixtures.py tests/test_mvp_input_defaults.py tests/test_real_cash.py tests/test_input_layer_mvp_regression.py -q` | **36 passed** |
| Docs verification | `python scripts/verify_docs.py` | **OK** |

### Live `run_metadata.json` sample (post Session 10 materialize, demo config)

| Field / block | Observed |
| --- | --- |
| `resolved_config.analysis_mode` | `analyze_current_weights` |
| `resolved_config.client_profile` | `null` |
| `analysis_setup.analysis_subject.type` | `current_portfolio` |
| `analysis_setup.analysis_portfolio.cash_handling.cash_proxy_ticker` | `BIL` |
| `input_assumptions.input_surface.profile` | `core_mvp` |
| `input_assumptions.input_surface.core_mvp_requirements_met` | `true` |
| `input_assumptions.field_tiers` | `field_tiers_v1` with deferred/legacy registry |
| `input_assumptions.input_surface.real_cash.holdings` | `[]` (demo has no `Cash USD`) |

**Note:** Pre–Session 10 on-disk `run_metadata.json` lacked `input_assumptions` until materialize was re-run; acceptance evidence uses the **2026-05-26T14:28** refresh.

---

## 5. Operator Checklist (Core MVP)

```bash
# Validate config semantics (optional one-liner via Python)
python -c "import yaml; from src.config_schema import validate_config; validate_config(yaml.safe_load(open('config.yml',encoding='utf-8')))"

# Diagnosis path (dry-run then live)
python run_portfolio_review.py --dry-run
python run_report.py --materialize-analysis-subject --output-profile site_api --review-mode core --use-review-run-context

# One-candidate product demo (after live compare refresh if needed)
python run_portfolio_review.py --candidates equal_weight
python scripts/validate_one_candidate_demo.py

# Offline regression gate
python -m pytest tests/test_mvp_portfolio_fixtures.py tests/test_mvp_input_defaults.py tests/test_real_cash.py tests/test_input_layer_mvp_regression.py -q
```

Inspect Block 1: `{output_dir_final}/analysis_subject/run_metadata.json` → `input_assumptions.input_surface` and `field_tiers`.

---

## 6. Residual Notes (non-blocking)

| ID | Note | Mitigation |
| --- | --- | --- |
| N1 | `resolved_config` snapshot may show `risk_free_source` / `cash_proxy_ticker` null while runtime resolves via `resolve_cash_and_rf` | Trust `analysis_setup` / materialize logs for resolved USD defaults |
| N2 | Legacy `run_optimization.py` still reads full schema | Use portfolio-first path for Core MVP; `field_tiers.legacy_advanced` |
| N3 | EUR explicit cash/RF paths not in USD fixtures | Documented in ExecPlan; EUR behavior unchanged |
| N4 | Product bundle on disk may predate latest materialize | Re-run `--candidates equal_weight` before external demo if compare artifacts are stale |

---

## 5. Live one-candidate verification (post-acceptance, 2026-05-26)

Full live path (not dry-run) after contract freeze request:

| Check | Command / evidence | Result |
| --- | --- | --- |
| Live review | `python run_portfolio_review.py --candidates equal_weight` | Exit **0** (~176 s); `product_one_candidate`; factory `explicit_list`, **total=1** |
| Product validator | `python scripts/validate_one_candidate_demo.py` | **PASS** (8 checks) |
| (1) Selected candidate only | `candidate_factory_run.steps` | `[equal_weight]` only; `decision_verdict.selected_candidate_id` = `equal_weight` |
| (2) No candidate zoo | `factory_profile_id` = `explicit_list`; not `default_v1` / `research_batch`; manifest `selected_candidates` = `["equal_weight"]` | **PASS** — product adapters scoped; technical `candidate_comparison.json` may still list stale disk rows; `product_candidate_scope.candidate_ids` = `["equal_weight"]`, `excludes_unselected_candidates`: true |
| (3) Cash USD not downloaded | Demo `config.yml` has no `Cash USD`; live logs list **8** risk ETFs only | **N/A on this run**; contract: `tests/test_real_cash.py::test_load_monthly_data_skips_download_for_cash_usd` **PASS** |
| (4) Cash USD not replaced by proxy | Same | **N/A on this run**; contract: `test_build_analysis_setup_real_cash_handling` + fixture `minimal_usd_with_cash.yml` in regression **PASS** |
| (5) Block 1 disclosure | `analysis_subject/run_metadata.json` | `input_assumptions.input_surface.profile` = `core_mvp`; `field_tiers.version` = `field_tiers_v1` |
| (6) Six product JSON | `output_manifest.product_discovery.product_bundle_complete` | **true**; all six paths present |

**Contract frozen** per `DEC-2026-05-26-001` and [input_assumptions_spec.md](../specs/input_assumptions_spec.md) § Contract freeze.

---

## 7. Closure

- ExecPlan [2026-05-26_input_layer_mvp_migration.md](../exec_plans/2026-05-26_input_layer_mvp_migration.md): **Sessions 01–10 complete**; plan **closed**; input contract **frozen**.
- Register: [docs/audits/README.md](README.md) — this audit listed as closure evidence.
- **Next product focus:** Blocks 2–5 / product-flow layers (X-Ray → Stress → Classification → Launchpad → compare/verdict), not input redesign — [product_flow_operator_guide.md](../product_flow_operator_guide.md).
