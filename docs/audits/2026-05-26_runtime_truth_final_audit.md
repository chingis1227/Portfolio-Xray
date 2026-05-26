# Runtime Truth Reset — Final Audit (Session 09)

Date: 2026-05-26

Purpose: Close [Runtime Truth Reset ExecPlan](../exec_plans/2026-05-26_runtime_truth_reset_plan.md) **Session 09** and state whether runtime behavior now matches canonical **«ДИАГНОСТИКА 2»** product truth after Sessions 01–08.

Related:

- [Runtime Truth Session 07 validation](2026-05-26_runtime_truth_session07_one_candidate_validation.md)
- [Product Flow Demo Audit (pre-reset)](2026-05-26_product_flow_demo_audit.md)
- [Product-Flow Validation Audit](2026-05-25_product_flow_validation_audit.md)
- ExecPlan: `docs/exec_plans/2026-05-26_runtime_truth_reset_plan.md`

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Does runtime match «ДИАГНОСТИКА 2» at the product boundary? | **Yes — accepted.** |
| Is the ExecPlan acceptance criteria met? | **Yes — 6/6** (see §3). |
| Can we demo diagnosis-first without batch candidates? | **Yes** — `run_portfolio_review.py` default → `product_diagnosis_only`. |
| Can we demo one selected hypothesis honestly? | **Yes** — `--candidates equal_weight` → product adapters and verdict scoped to `equal_weight` (validated live + on-disk validator). |
| Is research / backend batch still available? | **Yes** — `--with-candidates`, `--mode full`, factory profiles; advanced package preserved in tests. |
| Are there residual operator caveats? | **Yes — documented** (§6): technical `candidate_comparison.json` may list many disk folders; UI must use product bundle + `product_discovery`. |

**Bottom line:** Runtime truth reset is **complete**. The backend implements diagnosis-first product routing, selected-candidate scoping, product-first manifest discovery, and advanced gating without removing research batch or legacy paths. Stakeholders should present the **six-file product bundle** and `product_discovery` paths — not raw Selection Engine ranking or full comparison row counts.

---

## 2. Session Rollup (01–09)

| Session | Objective | Status | Primary evidence |
| --- | --- | --- | --- |
| 01 | Runtime mode policy | **Done** | `resolve_portfolio_review_runtime_mode`, dry-run disclosure |
| 02 | Default product behavior | **Done** | CLI default diagnosis-only; `--with-candidates` → research batch |
| 03 | Selected-candidate scoping | **Done** | `product_candidate_scope`, stale-folder tests |
| 04 | Product bundle first | **Done** | `primary_output_surface=product_bundle`, manifest key order |
| 05 | Advanced artifact gating | **Done** | Product one-candidate skips Health/Selection/Journal path |
| 06 | Manifest product discovery | **Done** | `generated_paths_by_category`, `product_discovery` |
| 07 | One-candidate demo validation | **Done** | Live run + `scripts/validate_one_candidate_demo.py` PASS |
| 08 | Regression boundaries | **Done** | `tests/test_runtime_mode_regression_boundaries.py` |
| 09 | Final audit | **Done** | This document |

---

## 3. ExecPlan Acceptance Criteria

Criteria from ExecPlan § Validation and Acceptance (runtime reset complete when all hold):

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Diagnosis-only mode does not generate candidates | **PASS** | Dry-run: `Runtime mode: product_diagnosis_only`; stages = diagnosis only |
| 2 | One-candidate mode uses only selected candidate in product comparison and verdict | **PASS** | `validate_one_candidate_demo.py` RESULT PASS; Session 07 live run |
| 3 | Stale candidate folders do not control product verdict | **PASS** | Offline tests + post-reset disk: `decision_verdict.selected_candidate_id` = `equal_weight` despite `risk_parity` on disk |
| 4 | Product bundle files exist and are discoverable first | **PASS** | `product_discovery.product_bundle_complete` = true; six keys in manifest |
| 5 | Advanced/research mode still supports batch comparison and old artifacts | **PASS** | `--with-candidates` dry-run → `research_batch`, 6 candidates; `test_research_batch_compare_contract_preserves_advanced_package` |
| 6 | Legacy policy commands remain compatibility paths | **PASS** | `run_optimization.py` not in product plan argv; no removal in Sessions 01–08 |

**ExecPlan runtime reset: ACCEPTED.**

---

## 4. Verification Executed (Session 09)

| Check | Command | Result |
| --- | --- | --- |
| One-candidate dry-run | `python run_portfolio_review.py --dry-run --candidates equal_weight` | Exit **0**; `product_one_candidate`; `--candidates equal_weight --then-compare` |
| Diagnosis-only dry-run | `python run_portfolio_review.py --dry-run` | Exit **0**; `product_diagnosis_only`; diagnosis stage only |
| Research batch dry-run | `python run_portfolio_review.py --dry-run --with-candidates` | Exit **0**; `research_batch`; `candidate_count=6` |
| On-disk demo validator | `python scripts/validate_one_candidate_demo.py` | **PASS** (8 checks) |
| Regression pytest | `pytest tests/test_runtime_mode_regression_boundaries.py` + workflow + bundle + Session 07 | **64 passed** |
| Docs verification | `python scripts/verify_docs.py` | **OK** |

### On-disk sample (`Main portfolio/`, post Session 07 live run)

| Artifact / field | Observed |
| --- | --- |
| `current_vs_candidate.selected_candidate_ids` | `["equal_weight"]` |
| `decision_verdict.selected_candidate_id` | `equal_weight` |
| `candidate_factory_run` steps | `equal_weight` only |
| `output_manifest.primary_output_surface` | `product_bundle` |
| `product_discovery.product_bundle_complete` | `true` |
| `generated_paths_by_category` | `product_bundle`, `technical_comparison`, `orchestration` present |
| `candidate_comparison` row count (technical) | May include many disk folders (~19); **not** the product answer |
| `product_candidate_scope.candidate_ids` | `["equal_weight"]` |

---

## 5. Regression vs Pre-Reset Audits

| Issue | Pre-reset (2026-05-26 demo audit) | Post-reset (Session 09) |
| --- | --- | --- |
| Default CLI implied batch research | Plain review could plan `core_fast` six-pack | Default = **diagnosis-only**; batch via `--with-candidates` |
| `--candidates equal_weight` verdict | `risk_parity` favored | **`equal_weight`** in product adapters |
| Manifest product index | Factory-only manifest; missing bundle keys | **`product_discovery`** + categorized paths |
| Advanced package in product path | Health/Selection/Journal dominated compare chain | **Gated off** for explicit-list product compare |
| Honest EW demo narrative | **No** | **Yes** (with technical comparison caveat) |

---

## 6. Residual Risks and Operator Rules

These are **not** blockers for ExecPlan closure; they are presentation and hygiene rules.

| ID | Risk | Mitigation |
| --- | --- | --- |
| R1 | `candidate_comparison.json` scans all variant folders on disk | Product UI/API: read `product_discovery.product_bundle_paths` and scoped adapters only |
| R2 | Stale folders inflate technical ranking tables | Prune unused variant folders before demos, or rely on explicit-list factory + scope metadata |
| R3 | `output_manifest.run_kind` may be `candidate_factory` after `--then-compare` | Use `product_discovery` and `generated_paths_by_category`, not `run_kind` alone |
| R4 | Internal stress codes (`DIAG_*`) in technical JSON | Map in UI; product bundle uses classification/verdict adapters |
| R5 | No LLM prose — grounding only | `ai_commentary_context.json` is deterministic grounding per spec |

**Recommended operator checklist (one-candidate demo):**

```bash
python run_portfolio_review.py --candidates equal_weight
python scripts/validate_one_candidate_demo.py
```

---

## 7. Automation and Docs Index

| Asset | Role |
| --- | --- |
| `scripts/validate_one_candidate_demo.py` | Post-run disk gate |
| `tests/test_one_candidate_demo_validation.py` | Session 07 CI |
| `tests/test_runtime_mode_regression_boundaries.py` | Session 08 product vs research contracts |
| `src/product_bundle_paths.py` | Manifest discovery helpers |
| `TESTING.md` | Session 07–08 verification rows |
| `OUTPUTS.md` | Product bundle + manifest categories |

---

## 8. Final Verdict

| Scope | Verdict |
| --- | --- |
| Runtime Truth Reset ExecPlan (Sessions 01–09) | **COMPLETE — ACCEPTED** |
| Runtime aligns with «ДИАГНОСТИКА 2» product truth | **YES** at product boundary |
| Safe to proceed to UI/integration consuming product bundle | **YES**, following §6 operator rules |

**Signed closure:** 2026-05-26 — Session 09 final audit. No further runtime-truth sessions required unless product truth or CLI contracts change.
