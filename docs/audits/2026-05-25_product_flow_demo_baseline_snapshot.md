# Product Flow Demo Baseline Snapshot

Date: 2026-05-26

Purpose: Record **on-disk evidence** for the approved one-candidate product demo after ExecPlan Session 07. This snapshot complements the offline integration gate (Session 01) and RM-ARCH-011 wiring (Sessions 02–03). **Audit closure:** Session 08 (2026-05-26) — see [Product-Flow Validation Audit](2026-05-25_product_flow_validation_audit.md) § Session 08 closure.

Related:

- [Product-Flow Validation Audit](2026-05-25_product_flow_validation_audit.md)
- [Product Flow MVP Backend ExecPlan](../exec_plans/2026-05-25_product_flow_mvp_backend_plan.md) — Session 07
- [OUTPUTS.md](../../OUTPUTS.md) — Core MVP product bundle table
- [Product flow operator guide](../product_flow_operator_guide.md)

---

## 1. Run command and scope

| Field | Value |
| --- | --- |
| Command | `python run_portfolio_review.py --candidates equal_weight` |
| Run date (local) | 2026-05-26 |
| Wall clock (approx.) | ~120 s (subject materialization + factory reuse + compare/decision package) |
| `output_dir_final` | `Main portfolio/` (gitignored) |
| Workflow state | `one_candidate` (`candidate_count=1`, `source=candidate_ids`) |
| Factory profile | `explicit_list` |
| Factory step | `equal_weight` → `skipped_existing` (reused fresh `equal-weight portfolio/snapshot_10y.json`) |
| PDF | Not refreshed (`site_api`; no `--with-pdf`) |

Data notes:

- IBKR connection refused; daily tail panel fell back to yfinance (9 tickers).
- Subject stress: `DIAG_ATTENTION` (`DIAG_LOSS_RECESSION_SEVERE` on `recession_severe`).
- `problem_classification.json` / `candidate_launchpad.json` regenerated under `analysis_subject/` during subject materialization (2026-05-25T22:28:21–22Z).

---

## 2. Core MVP product bundle checklist

Per [OUTPUTS.md](../../OUTPUTS.md) § Core MVP product bundle. All six files **present** with expected `schema_version`.

| Relative path | `schema_version` | Size (bytes) | sha256 |
| --- | --- | ---: | --- |
| `analysis_subject/problem_classification.json` | `problem_classification_v1` | 2530 | `b3f723c39b2b3a0542ad42eb9b5e4484f7ec077d31b695b2863b82e76670cf84` |
| `analysis_subject/candidate_launchpad.json` | `candidate_launchpad_v1` | 5084 | `5d5e49d0e49fc5e1d4f0540670568e3411fbf3cb806582716c4c7d33b4ec78ca` |
| `current_vs_candidate.json` | `current_vs_candidate_v1` | 2573 | `d30f66f26958ba1c34852fd953907a968a8af3824b98c762f3561146d185a12c` |
| `decision_verdict.json` | `decision_verdict_v1` | 1558 | `f33e6bcd7ebb80dff68c2d614dcd915eeaf5a9438195881ed0c3eeb797297769` |
| `ai_commentary_context.json` | `ai_commentary_context_v1` | 5953 | `7db3b9f1a72d6978ae3ae14b655e2107535ffbd7529a0bb2ce4950d7c2d237d7` |
| `what_changed_summary.json` | `what_changed_summary_v1` | 2765 | `7fdacad4faa709a75f6d4a1bf8b56961ba84b46e5e8e44eed78ea0c951062967` |

**Bundle checklist:** **PASS** (six files + schema versions).

### RM-ARCH-011 sidecar wiring (spot check)

| Check | Result |
| --- | --- |
| Diagnosis JSON under `analysis_subject/` | **PASS** — both problem and launchpad in sidecar |
| `load_diagnosis_bundle_docs("Main portfolio")` | **PASS** — both documents load from sidecar paths |
| `ai_commentary_context.json` cites `problem_classification.json` / `candidate_launchpad.json` field paths | **PASS** — `evidence_references` include problems and launchpad cards |
| `what_changed_summary.json` `problem_ids` | **PASS** — `weak_crisis_resilience`, `high_concentration`, `high_drawdown_risk` aligned with problem classification |

---

## 3. Product demo narrative (this run)

| Product step | Evidence on disk |
| --- | --- |
| Current portfolio input | `config.yml` → `analysis_subject`; `analysis_subject/run_metadata.json` |
| Portfolio X-Ray | `analysis_subject/portfolio_xray.json` (subject materialization) |
| Stress Lab | `analysis_subject/stress_report.json`, `analysis_subject/snapshot_10y.json` |
| Problem Classification | `analysis_subject/problem_classification.json` (3 problems; top severity **high** on weak crisis resilience) |
| Candidate Launchpad | `analysis_subject/candidate_launchpad.json` (4 cards) |
| One hypothesis (factory) | `candidate_factory_run.json` — single step `equal_weight`, reused snapshot |
| Current vs Candidate | `current_vs_candidate.json` — `view_mode`: `one_candidate` |
| Decision Verdict | `decision_verdict.json` — `verdict_id`: `rebalance_to_selected_candidate` |

---

## 4. Caveats for Session 08 closure

These do **not** invalidate the six-file bundle presence but affect **demo interpretability**:

### C1 — Compare/selection used stale multi-candidate disk state

- Factory was invoked for **`equal_weight` only** (`skipped_existing`).
- `selection_decision.json` **`favored_candidate_id`**: `risk_parity` (not `equal_weight`).
- `composite_ranking` length: **12** candidates — indicates compare ranked **existing variant folders** on disk, not only the factory step for this run.
- `current_vs_candidate.json` **`selected_candidate_ids`**: `["risk_parity"]`.

**Operator implication:** For a clean one-hypothesis demo, use a fresh `output_dir_final` or prune stale variant snapshots before compare, **or** treat this baseline as “bundle contract proof” rather than “equal_weight won selection.” Track in Session 08 audit update.

### C2 — `output_manifest.json` missing product-bundle index keys

After the run, `output_manifest.json` has:

- `run_kind`: `candidate_factory`
- `generated_paths`: only `candidate_factory_run` + `candidate_factory_manifest`
- **Missing** all six `PRODUCT_BUNDLE_MANIFEST_KEYS` and `artifact_categories`

Compare/decision artifacts were written at the same timestamp, but the manifest on disk reflects the **factory** manifest writer, not the compare manifest with bundle paths (Session 03 intent). Session 08 should confirm whether factory `--then-compare` should preserve compare manifest keys.

---

## 5. Technical artifacts (reference, not product bundle)

Present at `Main portfolio/` after run (non-exhaustive):

- `candidate_comparison.json`, `selection_decision.json`, `candidate_factory_run.json`
- Full decision package: `portfolio_health_score.json`, `robustness_scorecard.json`, `action_plan.json`, `monitoring_diff.json`, etc.
- Legacy/root copies: `portfolio_xray.json`, `stress_report.json` (older timestamps than subject sidecar)

---

## 6. Verification commands

```bash
python run_portfolio_review.py --candidates equal_weight
```

Post-run spot check (repo root, `PYTHONPATH=.`):

```bash
python -m pytest tests/test_product_bundle_integration.py tests/test_product_bundle_paths.py -q
```

Offline gate remains the regression contract; this snapshot is **live disk evidence** for the same six paths.

---

## 7. Verdict

| Question | Answer |
| --- | --- |
| Six-file product bundle on disk under `Main portfolio/`? | **Yes** — checklist PASS |
| RM-ARCH-011 sidecar consumed in commentary/what-changed? | **Yes** — spot check PASS |
| Demo-ready backend (audit closure)? | **Yes (MVP)** — Session 08 closed audit with C1/C2 as **accepted operator caveats** (stale compare scope; factory manifest vs product_bundle manifest keys) |

**Closure:** [Product-Flow Validation Audit](2026-05-25_product_flow_validation_audit.md) Session 08 (2026-05-26); `RM-ARCH-011` → Done in [ROADMAP.md](../ROADMAP.md).
