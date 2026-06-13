# Runtime Truth Session 07 — One-Candidate Demo Validation

Date: 2026-05-26

Purpose: Close **Session 07** of [Runtime Truth Reset ExecPlan](../exec_plans/2026-05-26_runtime_truth_reset_plan.md): validate the canonical product command `python run_portfolio_review.py --candidates equal_weight` after Sessions 03–06 (selected-candidate scoping, product manifest discovery, advanced gating).

Related:

- [Product Flow Demo Audit](2026-05-26_product_flow_demo_audit.md) (pre-fix live run; stale `risk_parity` verdict)
- [Product Flow Demo Baseline Snapshot](2026-05-25_product_flow_demo_baseline_snapshot.md)
- `scripts/validate_one_candidate_demo.py`
- `tests/test_one_candidate_demo_validation.py`

---

## 1. Executive Summary

| Question | Answer |
| --- | --- |
| Session 07 accepted... | **Yes.** Dry-run, offline stale-folder test, live run, and on-disk validator all **PASS**. |
| Canonical command | `python run_portfolio_review.py --candidates equal_weight` |
| Product scoping | **PASS** — `current_vs_candidate.selected_candidate_ids` = `["equal_weight"]`; `decision_verdict.selected_candidate_id` = `equal_weight`. |
| Stale folder hijack | **PASS (product layer)** — technical `candidate_comparison.json` still lists 19 rows on disk, but `product_candidate_scope` = `equal_weight` only; product adapters and verdict use EW. |
| Factory scope | **PASS** — `candidate_factory_run.json` steps: `equal_weight` only (`skipped_existing`). |
| Manifest / discovery | **PASS** — `product_discovery.product_bundle_complete` = true; `primary_output_surface` = `product_bundle`. |

**Bottom line:** The one-candidate Equal Weight demo is **honest** for product-facing JSON after runtime truth reset. Do not cite full `candidate_comparison.json` ranking as the product answer — use the six-file bundle and scoped adapters.

---

## 2. Commands Executed

| Step | Command | Result |
| --- | --- | --- |
| Dry-run | `python run_portfolio_review.py --dry-run --candidates equal_weight` | Exit **0**; `Runtime mode: product_one_candidate`; factory argv `--candidates equal_weight --then-compare` |
| Live run | `python run_portfolio_review.py --candidates equal_weight` | Exit **0**; ~121 s wall clock |
| On-disk validator | `python scripts/validate_one_candidate_demo.py` | Exit **0**; all checks **PASS** |
| Offline pytest | `python -m pytest tests/test_one_candidate_demo_validation.py -q` | **4 passed** |

---

## 3. Live Run Evidence (2026-05-26)

| Field | Value |
| --- | --- |
| `output_dir_final` | `Main portfolio/` (gitignored) |
| Workflow state | `one_candidate` (`candidate_count=1`, `source=candidate_ids`) |
| Runtime mode | `product_one_candidate` |
| Factory profile | `explicit_list` |
| Factory step | `equal_weight` → `skipped_existing` |

### Session 07 acceptance checks

| Check | Expected | Observed |
| --- | --- | --- |
| Factory touches only EW | `steps == [equal_weight]` | **PASS** |
| Current vs Candidate scope | `selected_candidate_ids == ["equal_weight"]` | **PASS** (`view_mode`: `one_candidate`) |
| Decision Verdict | `selected_candidate_id == equal_weight` or no-trade about EW | **PASS** (`verdict_id`: `rebalance_to_selected_candidate`) |
| Stale candidate controls verdict | Product outputs must not favor `risk_parity` | **PASS** (contrast: 2026-05-26 demo audit had `risk_parity`) |
| Six-file bundle + manifest discovery | `product_discovery.product_bundle_complete` | **PASS** |

### Technical note (not a Session 07 failure)

- `candidate_comparison.json` may still contain many candidate rows from existing variant folders (**19** in this run). Product scope metadata documents the explicit hypothesis:

```json
"product_candidate_scope": {
  "scope_type": "explicit_candidates",
  "candidate_ids": ["equal_weight"],
  "baseline_candidate_id": "analysis_subject",
  "excludes_unselected_candidates": true
}
```

UI/API should read **product bundle** + `product_discovery`, not raw composite ranking length.

---

## 4. Regression vs 2026-05-26 Demo Audit

| Issue (prior audit) | Session 07 status |
| --- | --- |
| C1 — Verdict favored `risk_parity` despite CLI | **Resolved** on refreshed run |
| C2 — Manifest missing product-bundle keys | **Resolved** (`product_discovery`, `generated_paths_by_category`) |
| Advanced package in product one-candidate | **Resolved** (`advanced_package_generated` absent / false on product compare path; no Health/Selection/Journal in product paths) |

---

## 5. Automation Added (Session 07)

| Artifact | Role |
| --- | --- |
| `scripts/validate_one_candidate_demo.py` | Operator/CI gate on `Main portfolio/` (or `--output-dir`) |
| `tests/test_one_candidate_demo_validation.py` | Dry-run CLI, workflow plan, stale-folder offline proof, validator negative case |

Recommended operator check after any one-candidate run:

```bash
python run_portfolio_review.py --candidates equal_weight
python scripts/validate_one_candidate_demo.py
```

---

## 6. Verdict

**Session 07 — PASS.** Runtime truth reset delivers a defensible Equal Weight one-candidate product demo on this workspace. Remaining ExecPlan work: Sessions **08** (regression boundaries) and **09** (final runtime truth audit).
