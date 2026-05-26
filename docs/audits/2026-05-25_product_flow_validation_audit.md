# Product-Flow Validation Audit — Portfolio MRI

Date: 2026-05-25 (original read-only audit). **Closure:** 2026-05-26 (Session 08, [Product Flow MVP Backend ExecPlan](../exec_plans/2026-05-25_product_flow_mvp_backend_plan.md)).

Purpose: Validate whether the project works today as a **coherent product flow** (diagnosis-first Portfolio MRI), not only as a set of modules. The 2026-05-25 body below is **historical evidence at audit time**. Session 08 adds closure status and links to remediation evidence; it does not rewrite every per-step table.

Related evidence:

- Product direction: [PRODUCT.md](../../PRODUCT.md), [ARCHITECTURE.md](../../ARCHITECTURE.md)
- Implementation contract: [SPEC.md](../../SPEC.md), [OUTPUTS.md](../../OUTPUTS.md), [TESTING.md](../../TESTING.md)
- Prior alignment: [2026-05-25 Full Project Architecture Alignment Audit](2026-05-25_full_project_architecture_alignment_audit.md), [Session 12 closure](2026-05-25_post_architecture_alignment_session12_closure_report.md)
- Remediation plan: [Product Flow MVP Backend ExecPlan](../exec_plans/2026-05-25_product_flow_mvp_backend_plan.md) (Sessions 01–08)
- Live bundle evidence: [Product Flow Demo Baseline Snapshot](2026-05-25_product_flow_demo_baseline_snapshot.md) (Session 07)
- Operator map: [Product flow operator guide](../product_flow_operator_guide.md)
- Backlog: `RM-ARCH-011` **Done** (2026-05-26); `RM-ARCH-010` (LLM AI Commentary) **deferred**

---

## Session 08 closure summary (2026-05-26)

| Question | Answer after remediation |
| --- | --- |
| Demo-ready MVP backend? | **Yes** — with documented operator discipline (see caveats). |
| Official one-hypothesis CLI | `python run_portfolio_review.py --candidates equal_weight` (or another factory id); routine `--mode core` stays six-candidate regression. |
| Six-file product bundle | **Offline gate:** `tests/test_product_bundle_integration.py`. **Live disk:** [demo baseline snapshot](2026-05-25_product_flow_demo_baseline_snapshot.md) — six JSON PASS under gitignored `Main portfolio/`. |
| `RM-ARCH-011` sidecar wiring | **Done** — `src/product_bundle_paths.py`; compare passes diagnosis bundle into AI commentary and What Changed; tests in `tests/test_product_bundle_paths.py` + integration gate. |
| Regression without network | **46 passed** (Session 08 bundle): product bundle paths/integration, AI commentary, light monitoring, review workflow, alternatives builder. |

**Residual caveats (accepted for MVP backend, not blockers for closure):**

- **C1 (audit):** No bundle JSON in git — by design (`Main portfolio/` gitignored). Live proof is the Session 07 snapshot, not the repo tree.
- **C2 (audit):** Default core still runs six candidates — **accepted**; product demo uses explicit `--candidates`.
- **C3 (audit):** Dirty tree — still deferred ([DIRTY_TREE_CLEANUP_PLAN.md](../../DIRTY_TREE_CLEANUP_PLAN.md)).
- **Demo C1 (snapshot):** One-candidate factory run may still compare against **stale** on-disk variant snapshots; `favored_candidate_id` may not match the requested id — operator must prune or use fresh `output_dir_final` for a clean story.
- **Demo C2 (snapshot):** After factory `--then-compare`, root `output_manifest.json` may list factory paths only, not Session 03 `product_bundle_*` keys — compare manifest intent vs factory writer; consumers resolve bundle paths via [OUTPUTS.md](../../OUTPUTS.md) / operator guide.

---

## 1. Executive Summary (at audit time, 2026-05-25)

| Question | Answer |
| --- | --- |
| Does the end-to-end product flow exist today? | **Partially.** The portfolio-first orchestrator and additive diagnosis-first adapters exist in source; the documented journey is implementable as a **CLI/file backend**, not as a single product UI. |
| Usable as coherent MVP backend flow? | **Yes, with caveats.** `python run_portfolio_review.py` chains subject diagnosis → factory → compare → decision package. Consumers must filter technical artifacts and resolve `analysis_subject/` paths for the six-file product bundle. |
| Only partially implemented? | **Yes.** Target UX (diagnosis-only default, one selected candidate, builder as front door, LLM commentary, formal workflow state on disk) is **not** the default runtime behavior. |
| What blocks “one product” feel? | (1) Default `--mode core` runs **six** candidates (`core_fast`), not one hypothesis. (2) Compare still emits the **full technical decision package** (health, robustness, Pareto, regret, etc.). (3) **RM-ARCH-011** wiring gaps (sidecar paths, `ai_commentary` inputs). (4) **Portfolio Alternatives Builder** is a plan generator, not wired into `run_portfolio_review.py`. (5) **No product-bundle JSON in the repo** (`Main portfolio/` is gitignored; workspace search found **zero** `problem_classification.json` / `decision_verdict.json` files). (6) Large **dirty tree** (~346 entries per Session 12) complicates reproducible demo baselines. (7) **~9 min** default core E2E (Blocks 1–5 timing audit) is heavy for a live demo without offline fixtures. |

**Bottom line (2026-05-25):** The backend **can** tell the product story after a successful portfolio-first run, but the **default command is a research batch path**, not the target “one hypothesis” MVP. Demo readiness requires **runtime verification** on a fresh run plus consumer discipline (or `RM-ARCH-011` fixes).

**Bottom line (2026-05-26 closure):** Remediation Sessions 01–08 delivered offline regression, sidecar wiring (`RM-ARCH-011` Done), operator documentation, and live six-file bundle evidence. The backend is **demo-ready** for the diagnosis → one hypothesis → compare → verdict CLI path when operators use `--candidates <id>` and read the six-file bundle per [product flow operator guide](../product_flow_operator_guide.md). UI, LLM commentary (`RM-ARCH-010`), and merged `product_bundle.json` remain out of scope.

---

## 2. Target Journey Validation

Classification key:

| Status | Meaning |
| --- | --- |
| **Implemented and wired** | Code + orchestration produce the artifact in the expected review path. |
| **Implemented but not product-facing** | Exists as backend/adapter; not default UX or buried in technical package. |
| **Partially implemented** | Artifact or logic exists; gaps in default path, wiring, or scope. |
| **Documented only** | Spec/product doc without runtime default. |
| **Missing** | No implementation found. |
| **Blocked by stale/generated output** | Code path exists; on-disk evidence absent or unreliable in this workspace. |

### 2.1 Current portfolio input

| Field | Detail |
| --- | --- |
| **Status** | **Implemented and wired** |
| **Owning modules** | `config.yml` (`analysis_subject`), [src/analysis_setup.py](../../src/analysis_setup.py), [docs/specs/input_assumptions_spec.md](../specs/input_assumptions_spec.md) |
| **CLI** | Resolved by `run_report.py --materialize-analysis-subject` (step 1 of `run_portfolio_review.py`) |
| **Expected output** | `analysis_setup` / `input_assumptions` in `analysis_subject/run_metadata.json`; weights in materialization |
| **Produced today** | **Requires runtime verification** on disk (`Main portfolio/analysis_subject/` gitignored) |
| **Connected prev/next** | Yes → X-Ray/stress in same materialization pass |
| **Product question** | “What portfolio am I diagnosing?” |
| **Gaps** | Legacy `weights` / root policy artifacts still coexist ([OUTPUTS.md](../../OUTPUTS.md) two-tree rule). No interactive input UI. |

### 2.2 Portfolio X-Ray

| Field | Detail |
| --- | --- |
| **Status** | **Implemented and wired** |
| **Owning modules** | [src/portfolio_xray.py](../../src/portfolio_xray.py), `run_report.py`, [docs/specs/portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) |
| **Expected output** | `{output_dir_final}/analysis_subject/portfolio_xray.json` (seven sections) |
| **Produced today** | **Requires runtime verification** (subject sidecar gitignored) |
| **Connected** | Feeds Problem Classification at report write time |
| **Product question** | “What do I own and where is risk concentrated?” |
| **Gaps** | Export TXT/HTML/PDF not default under `site_api`. |

### 2.3 Stress Test Lab

| Field | Detail |
| --- | --- |
| **Status** | **Implemented and wired** |
| **Owning modules** | [src/stress.py](../../src/stress.py), stress factors, `run_report.py`, [docs/specs/stress_testing_spec.md](../specs/stress_testing_spec.md), [docs/specs/stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) |
| **Expected output** | `analysis_subject/stress_report.json` (scorecard, conclusions, hedge gap, factor blocks per rules) |
| **Produced today** | **Requires runtime verification** |
| **Connected** | Feeds Problem Classification; subject row in `candidate_comparison.json` |
| **Product question** | “How does the portfolio behave under stress and crises?” |
| **Gaps** | Dominant factory time in macro/tail blocks (~9 min core path). |

### 2.4 Problem Classification

| Field | Detail |
| --- | --- |
| **Status** | **Partially implemented** |
| **Owning modules** | [src/problem_classification.py](../../src/problem_classification.py), `run_report.py` (`write_problem_classification_outputs`), [docs/specs/problem_classification_spec.md](../specs/problem_classification_spec.md) |
| **Expected output** | `problem_classification.json` under report `output_dir` → **`analysis_subject/problem_classification.json`** after materialization |
| **Produced today** | **Blocked by stale/generated output** in repo (no JSON found); code writes on successful materialization |
| **Connected** | → Launchpad in `run_report.py`; **weak** link to compare: `write_what_changed_summary_outputs` loads `out_dir / "problem_classification.json"` (root), not sidecar ([src/candidate_comparison.py](../../src/candidate_comparison.py) ~2210) — **RM-ARCH-011** |
| **Product question** | “What is wrong with this portfolio and what should we test?” |
| **Gaps** | Path mismatch root vs `analysis_subject/`. Not in offline decision-package E2E fixture list. |

### 2.5 Candidate Launchpad

| Field | Detail |
| --- | --- |
| **Status** | **Partially implemented** |
| **Owning modules** | [src/candidate_launchpad.py](../../src/candidate_launchpad.py), `run_report.py`, [docs/specs/candidate_launchpad_spec.md](../specs/candidate_launchpad_spec.md) |
| **Expected output** | `analysis_subject/candidate_launchpad.json` |
| **Produced today** | **Blocked by stale/generated output** in repo |
| **Connected** | Depends on Problem Classification; not passed into `write_ai_commentary_context_outputs` from compare (**RM-ARCH-011**) |
| **Product question** | “Which hypotheses are reasonable to try next?” |
| **Gaps** | Cards are not portfolios; no UI selection surface; compare/commentary grounding incomplete. |

### 2.6 Portfolio Alternatives Builder

| Field | Detail |
| --- | --- |
| **Status** | **Implemented but not product-facing** |
| **Owning modules** | [src/portfolio_alternatives_builder.py](../../src/portfolio_alternatives_builder.py), [docs/specs/portfolio_alternatives_builder_spec.md](../specs/portfolio_alternatives_builder_spec.md) |
| **Expected output** | No standalone JSON; `PortfolioAlternativeBuildPlan` → CLI argv for `run_candidate_factory.py --candidates <id> --then-compare` |
| **Produced today** | Plan only; **not** invoked by `run_portfolio_review.py` |
| **Connected** | Manual/service layer must execute returned command |
| **Product question** | “Build exactly one candidate for the hypothesis I chose.” |
| **Gaps** | Not default orchestration; no HTTP/API endpoint. |

### 2.7 Generate one candidate

| Field | Detail |
| --- | --- |
| **Status** | **Partially implemented** |
| **Owning modules** | [src/candidate_factory.py](../../src/candidate_factory.py), `run_candidate_factory.py`, per-candidate builders |
| **Expected output** | Candidate folder + `candidate_manifest.json` + `snapshot_10y.json` |
| **Produced today** | **Requires runtime verification** (candidate folders exist in dirty tree as untracked manifests per git status snapshot) |
| **Connected** | Factory `--then-compare` → product adapters at root |
| **Product question** | “Run this hypothesis as a portfolio.” |
| **Gaps** | Default review uses **`core_fast` (6 candidates)**, not one. One-candidate path: `--candidates <id>` or Alternatives Builder plan. |

### 2.8 Current vs Candidate Comparison

| Field | Detail |
| --- | --- |
| **Status** | **Implemented and wired** (adapter); **Implemented but not product-facing** (canonical table) |
| **Owning modules** | [src/current_vs_candidate.py](../../src/current_vs_candidate.py), [src/candidate_comparison.py](../../src/candidate_comparison.py), [docs/specs/current_vs_candidate_spec.md](../specs/current_vs_candidate_spec.md) |
| **Expected output** | `{output_dir_final}/current_vs_candidate.json` (`view_mode`: `one_candidate` \| `shortlist` \| `diagnosis_only`) |
| **Produced today** | **Requires runtime verification** after compare |
| **Connected** | After `candidate_comparison.json` + `selection_decision.json`; feeds Decision Verdict |
| **Product question** | “What improves and what worsens vs my portfolio?” |
| **Gaps** | Selection still drives favored candidate in batch mode; shortlist not the target “single selected hypothesis” UX. |

### 2.9 Decision Verdict

| Field | Detail |
| --- | --- |
| **Status** | **Implemented and wired** (product mapping); technical contract remains Selection |
| **Owning modules** | [src/decision_verdict.py](../../src/decision_verdict.py), [src/selection_engine.py](../../src/selection_engine.py), [docs/specs/decision_verdict_spec.md](../specs/decision_verdict_spec.md) |
| **Expected output** | `decision_verdict.json` (maps `selection_decision.json`) |
| **Produced today** | **Requires runtime verification** |
| **Connected** | Compare chain; → AI grounding, What Changed |
| **Product question** | “Keep, rebalance, review, no-trade, or insufficient evidence?” |
| **Gaps** | Product language ≠ schema rename (`selection_decision.json` still authoritative). |

### 2.10 AI Commentary / grounding context

| Field | Detail |
| --- | --- |
| **Status** | **Partially implemented** |
| **Owning modules** | [src/ai_commentary_context.py](../../src/ai_commentary_context.py), [docs/specs/ai_commentary_grounding_spec.md](../specs/ai_commentary_grounding_spec.md) |
| **Expected output** | `ai_commentary_context.json` (grounding-only, **no LLM**) |
| **Produced today** | **Requires runtime verification** |
| **Connected** | Compare writes after verdict; **does not** receive `problem_classification` / `candidate_launchpad` in current compare call |
| **Product question** | “What evidence may an explainer use without inventing metrics?” |
| **Gaps** | No generated natural-language AI Commentary (`RM-ARCH-010`). Deterministic `commentary.txt` is separate. |

### 2.11 Monitoring / What Changed

| Field | Detail |
| --- | --- |
| **Status** | **Implemented and wired** (technical + light summary) |
| **Owning modules** | [src/monitoring.py](../../src/monitoring.py), [src/light_monitoring_summary.py](../../src/light_monitoring_summary.py), [docs/specs/monitoring_spec.md](../specs/monitoring_spec.md), [docs/specs/light_monitoring_summary_spec.md](../specs/light_monitoring_summary_spec.md) |
| **Expected output** | `monitoring_diff.json`, `what_changed_summary.json`, snapshots under `monitoring/` |
| **Produced today** | **Requires runtime verification**; first run often `no_prior_snapshot` |
| **Connected** | After compare; uses verdict + optional problem (path gap) |
| **Product question** | “What changed since the last review?” |
| **Gaps** | Needs prior snapshot for meaningful diff; sidecar problem path (**RM-ARCH-011**). |

---

## 3. Runtime Flow Check

### 3.1 Trace: `run_portfolio_review.py` (default)

```text
run_portfolio_review.py [--mode core]
  → run_report.py --materialize-analysis-subject [--use-review-run-context]
       → Main portfolio/analysis_subject/  (X-Ray, stress, problem_classification, candidate_launchpad, snapshots)
  → run_candidate_factory.py --profile core_fast --execution-mode standard --then-compare
       → 6 candidate folders + candidate_factory_run.json
       → write_candidate_comparison_outputs (in-process)
            → technical + advanced JSON at Main portfolio root
            → product bundle adapters (current_vs_candidate, decision_verdict, ai_commentary_context, what_changed_summary)
  → (no PDF unless --with-pdf)
```

Workflow-state metadata on the plan: default core → `multiple_candidates` ([src/workflow_state.py](../../src/workflow_state.py), [docs/specs/workflow_state_spec.md](../specs/workflow_state_spec.md)). **Not persisted** as a generated artifact.

### 3.2 Trace: `run_report.py`

- Portfolio-first: `--materialize-analysis-subject` only (no legacy policy optimization in review plan).
- Legacy: full report at `output_dir_final` root (policy path) — **must not** be mixed with subject diagnostics.

### 3.3 Trace: `run_candidate_factory.py`

- Standalone factory; optional `--then-compare`.
- Profiles: `core_fast` (6), `core_v1` (6 sequential), `default_v1` (16).
- One-candidate: `--candidates <single_id> --then-compare`.

### 3.4 Trace: `run_compare_variants.py`

- Compare/decision writers only (no subject materialization, no factory).
- Assumes on-disk candidate snapshots and materialized `analysis_subject`.

### 3.5 Answers

| Question | Answer |
| --- | --- |
| Best command for target MVP flow today? | **Diagnosis + decision:** `python run_portfolio_review.py --skip-candidates` (diagnosis only) or full path: `python run_portfolio_review.py --mode core`. **One-candidate product story:** `python run_portfolio_review.py --candidates equal_weight` (or Alternatives Builder command plan + factory). |
| Does `--mode core` produce product-facing flow? | **Yes** for backend JSON contracts **if** run completes; **no** for target UX (6 candidates, technical package dominant). |
| One selected candidate or batch? | **Batch (6)** by default (`core_fast`). One candidate only with explicit `--candidates`. |
| Six product-facing JSON outputs? | **Code path: yes** after compare + materialization. **This workspace: not verified on disk** (gitignored / absent). |
| Where does old technical package dominate? | `write_candidate_comparison_outputs` always emits `candidate_comparison.json`, health, robustness, selection, trade-off, model risk, assumption sensitivity, Pareto, regret, action, monitoring, journal, `decision_package_summary.json` ([tests/mvp_offline_fixtures.py](../../tests/mvp_offline_fixtures.py) `MVP_DECISION_PACKAGE_ARTIFACTS`). Product surfaces must **filter** per [OUTPUTS.md](../../OUTPUTS.md) bundle policy. |

---

## 4. Product-Facing Output Bundle Check

| Artifact | Writer | Run stage | Path (portfolio-first) | On-disk in repo | In `output_manifest` | Tests |
| --- | --- | --- | --- | --- | --- | --- |
| `problem_classification.json` | `write_problem_classification_outputs` | Subject materialization | `analysis_subject/` | **Absent** (gitignored tree) | Listed under subject report dir when manifest written | `tests/test_problem_classification.py` |
| `candidate_launchpad.json` | `write_candidate_launchpad_outputs` | Subject materialization | `analysis_subject/` | **Absent** | Same | `tests/test_candidate_launchpad.py` |
| `current_vs_candidate.json` | `write_current_vs_candidate_outputs` | Compare | `output_dir_final` root | **Absent** | Via compare `generated_paths` | `tests/test_current_vs_candidate.py` |
| `decision_verdict.json` | `write_decision_verdict_outputs` | Compare | Root | **Absent** | Via compare | `tests/test_decision_verdict.py` |
| `ai_commentary_context.json` | `write_ai_commentary_context_outputs` | Compare | Root | **Absent** | Via compare | `tests/test_ai_commentary_context.py` |
| `what_changed_summary.json` | `write_what_changed_summary_outputs` | Compare | Root | **Absent** | Via compare | `tests/test_light_monitoring_summary.py` |

**Coherence assessment:**

- Schemas and writers are **aligned in documentation** ([OUTPUTS.md](../../OUTPUTS.md) § Product-Facing Output Bundle).
- **No merged `product_bundle.json`** (by design, Session 11 architecture alignment).
- `output_manifest.json` indexes paths but **does not** categorize product vs technical (**RM-ARCH-011**).
- Compare → What Changed / AI commentary **may omit** sidecar problem/launchpad unless consumers read `analysis_subject/` manually.

---

## 5. One-Candidate Journey Check

| Step | Works directly? | Notes |
| --- | --- | --- |
| Diagnosis-only state | **Yes** | `python run_portfolio_review.py --skip-candidates` → plan `diagnosis_only` ([tests/test_portfolio_review_workflow.py](../../tests/test_portfolio_review_workflow.py)) |
| Launchpad card | **Partial** | JSON after materialization; no UI |
| Builder plan | **Manual** | `src/portfolio_alternatives_builder.build_plan(...)` → run returned factory command |
| Generate exactly one candidate | **Yes, explicit flag** | `--candidates <id>` on review or factory; **not** default |
| Compare current vs that candidate | **Yes** | `current_vs_candidate.json` `view_mode=one_candidate` when one non-baseline row selected |
| Verdict | **Yes** | `decision_verdict.json` after selection |

**Verdict:** One-candidate journey works **only through explicit CLI** or builder delegation, **not** as the default `run_portfolio_review.py` path. **Requires runtime verification** for end-to-end disk proof.

Example commands (from specs/tests):

```bash
python run_portfolio_review.py --candidates equal_weight
python run_candidate_factory.py --candidates equal_weight --execution-mode standard --then-compare
```

---

## 6. Product UX Logic Check (backend evidence for screens)

| Screen | Status | Primary evidence |
| --- | --- | --- |
| Portfolio Diagnosis | **Backend-ready** | `portfolio_xray.json`, `input_assumptions`, `analysis_subject` row in comparison |
| Main Risks | **Backend partial** | X-Ray weakness/hidden risk sections + Problem Classification |
| Stress Behavior | **Backend-ready** | `stress_report.json`, stress scorecard/conclusions |
| Reasonable Paths to Test | **Backend partial** | `problem_classification.json` paths; Launchpad cards |
| Candidate Setup | **Backend partial** | Launchpad + Alternatives Builder plan; no setup artifact |
| Current vs Candidate Trade-off | **Backend-ready** | `current_vs_candidate.json` + `tradeoff_explanation.json` (technical) |
| Decision Verdict | **Backend-ready** | `decision_verdict.json` |
| What Changed | **Backend partial** | `what_changed_summary.json` (weak without prior snapshot / sidecar wiring) |

---

## 7. Tests / Verification Check

### 7.1 Existing tests (unit / contract — pass per Session 12 report)

| Area | Test file | Scope |
| --- | --- | --- |
| Problem Classification | `tests/test_problem_classification.py` | Builder/writer |
| Candidate Launchpad | `tests/test_candidate_launchpad.py` | Cards from problems |
| Alternatives Builder | `tests/test_portfolio_alternatives_builder.py` | Delegation plan |
| Current vs Candidate | `tests/test_current_vs_candidate.py` | Adapter view modes |
| Decision Verdict | `tests/test_decision_verdict.py` | Mapping |
| AI Commentary grounding | `tests/test_ai_commentary_context.py` | Grounding contract |
| What Changed summary | `tests/test_light_monitoring_summary.py` | Light monitoring |
| Review orchestration | `tests/test_portfolio_review_workflow.py` | Plan argv, workflow state |
| Workflow state | `tests/test_workflow_state.py` | Classification |
| Blocks 1–5 smoke | `tests/test_blocks_1_5_mvp_smoke.py` | Offline subject + factory + compare (no product bundle asserts) |
| Portfolio-first E2E offline | `tests/test_portfolio_first_e2e_offline.py` | Subject → `MVP_DECISION_PACKAGE_ARTIFACTS` (**excludes** six product bundle files) |

**Reported bundle:** Session 12 — **33 passed** for diagnosis-first adapter tests (~0.8 s). **Not re-run** in this audit session.

### 7.2 Missing / weak coverage (at audit time; closure in §11)

| Gap | Severity | Session 08 status |
| --- | --- | --- |
| No integration test asserting **all six** product bundle JSON files after full `write_candidate_comparison_outputs` with materialized `analysis_subject/` sidecar | **High** | **Resolved** — `tests/test_product_bundle_integration.py` (Session 01) |
| No offline test for **RM-ARCH-011** path resolution (problem/launchpad → compare/commentary/what_changed) | **High** | **Resolved** — `tests/test_product_bundle_paths.py` + integration sidecar-only case (Session 02) |
| No live-network E2E asserting product bundle on real `Main portfolio/` in CI | **Medium** (timing; optional) | **Partial** — Session 07 snapshot + manual checklist; not in CI |
| `test_portfolio_first_e2e_offline` reinforces **technical** package, not product bundle | **Medium** | **Accepted** — product bundle has dedicated integration gate |

### 7.3 Recommended smoke commands

| Intent | Command |
| --- | --- |
| Adapter unit bundle | `python -m pytest tests/test_problem_classification.py tests/test_candidate_launchpad.py tests/test_portfolio_alternatives_builder.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py tests/test_ai_commentary_context.py tests/test_light_monitoring_summary.py -q` |
| Orchestration plan | `python run_portfolio_review.py --dry-run` |
| Offline Blocks 1–5 gate | `python -m pytest tests/test_blocks_1_5_mvp_smoke.py -q` |
| **Product flow proof (approved refresh only)** | `python run_portfolio_review.py --mode core` then inspect `Main portfolio/analysis_subject/` + root bundle JSON (see OUTPUTS.md refresh table) |
| **One-candidate proof** | `python run_portfolio_review.py --candidates equal_weight` |

---

## 8. Gaps Ranked by Severity

### Critical

| ID | Finding |
| --- | --- |
| C1 | **No verifiable on-disk product bundle in workspace** — `Main portfolio/` gitignored; glob found **0** bundle JSON files. Cannot claim demo artifacts exist without a fresh run. |
| C2 | **Default product command contradicts target journey** — `--mode core` → **6 candidates**, not “user-selected one hypothesis.” |
| C3 | **Dirty tree (~346 entries)** — migration-related source and generated folders not committed; unstable baseline for product-flow validation ([Session 12 closure](2026-05-25_post_architecture_alignment_session12_closure_report.md)). |

### High

| ID | Finding |
| --- | --- |
| H1 | **RM-ARCH-011** — compare loads `problem_classification.json` from **root**; materialization writes under **`analysis_subject/`**; `ai_commentary_context` omit problem/launchpad at compare time. |
| H2 | **No E2E test for six-file product bundle** after portfolio-first compare with sidecar. |
| H3 | **Portfolio Alternatives Builder not orchestrated** — one-candidate path requires manual factory command or `--candidates`. |
| H4 | **Technical decision package remains default consumer surface** — 14+ JSON files vs 6 product files; easy to build wrong UI/API. |

### Medium

| ID | Finding |
| --- | --- |
| M1 | **~9 min** default core E2E — poor live-demo UX ([2026-05-24 Blocks 1–5 E2E timing audit](2026-05-24_blocks_1_5_e2e_timing_audit.md)). |
| M2 | **Workflow state** is plan metadata only — not a persisted product state machine. |
| M3 | **`output_manifest.json`** lacks product/technical categories. |
| M4 | **AI Commentary** is grounding-only — acceptable per spec, but product label “AI Commentary” over-promises until `RM-ARCH-010`. |

### Low

| ID | Finding |
| --- | --- |
| L1 | Terminology drift: Decision Verdict vs Selection Engine in mixed docs (handled in SPEC boundary). |
| L2 | Historical audits reference `core_v1` as default; active docs say `core_fast`. |

### Acceptable

| ID | Finding |
| --- | --- |
| A1 | Compare emits full technical/advanced package for traceability (Session 11 accepted). |
| A2 | No merged `product_bundle.json` (documented decision). |
| A3 | No LLM in pipeline (explicit `RM-ARCH-010` deferral). |
| A4 | Legacy policy path preserved for compatibility. |

**Counts:** Critical **3**, High **4**, Medium **4**, Low **2**, Acceptable **4**.

---

## 9. Recommended Next Sessions

### Session 01 — Product-flow smoke / offline fixture

| Field | Content |
| --- | --- |
| **Objective** | Add offline test: materialized `analysis_subject/` sidecar + compare → assert **six** product bundle files exist and schemas validate. |
| **Files likely affected** | `tests/test_portfolio_first_e2e_offline.py` or new `tests/test_product_bundle_integration.py`, `tests/mvp_offline_fixtures.py` |
| **Do not touch** | Formulas, stress scenarios, optimizer weights, generated `Main portfolio/` unless approved refresh |
| **Verification** | `python -m pytest tests/test_product_bundle_integration.py -q` |
| **Expected output** | Green test listing six paths under tmp workspace |

### Session 02 — One-candidate runtime path

| Field | Content |
| --- | --- |
| **Objective** | Document and verify `--candidates <id>` as default product demo path; optional CLI alias `--one-candidate` (if approved). |
| **Files likely affected** | `run_portfolio_review.py`, `docs/operational_runbook.md`, `PRODUCT.md` (if doc sync approved) |
| **Do not touch** | Factory builder formulas, `default_v1` menu |
| **Verification** | `python run_portfolio_review.py --candidates equal_weight --dry-run`; then approved live smoke |
| **Expected output** | Plan `workflow_state=one_candidate`; factory manifest 1 step |

### Session 03 — Product-facing output bundle verification (`RM-ARCH-011`)

| Field | Content |
| --- | --- |
| **Objective** | Resolve `analysis_subject/` paths in compare for problem/launchpad; pass into `ai_commentary_context` and `what_changed_summary`. |
| **Files likely affected** | `src/candidate_comparison.py`, optionally `src/output_policy.py` |
| **Do not touch** | JSON schema versions; Selection Engine contracts |
| **Verification** | Adapter tests + new integration test; optional approved refresh inspect |
| **Expected output** | Grounding references include problem/launchpad; what_changed uses sidecar |

### Session 04 — Report / AI commentary surface

| Field | Content |
| --- | --- |
| **Objective** | Clarify consumer mapping: `commentary.txt` vs `ai_commentary_context.json`; optional spec for future LLM (`RM-ARCH-010`). |
| **Files likely affected** | `docs/specs/ai_commentary_grounding_spec.md`, `src/pdf_reports.py` (only if PDF product copy needed) |
| **Do not touch** | Metric calculations |
| **Verification** | `rg` doc checks + `tests/test_ai_commentary_context.py` |
| **Expected output** | No doc claims “generates AI Commentary” for LLM |

### Session 05 — Demo portfolio run

| Field | Content |
| --- | --- |
| **Objective** | Approved **narrow** refresh: one-candidate + subject diagnosis; capture manifest + bundle JSON for demo baseline. |
| **Files likely affected** | Generated `Main portfolio/` only (separate commit if user requests) |
| **Do not touch** | Source code unless Session 03 incomplete |
| **Verification** | Manual checklist OUTPUTS.md § Output-bundle acceptance |
| **Expected output** | Six bundle files present; `view_mode=one_candidate` |

### Session 06 — Final MVP backend validation

| Field | Content |
| --- | --- |
| **Objective** | Re-run this audit checklist against fresh disk + green tests; update audit register. |
| **Files likely affected** | `docs/audits/README.md` (register row only, if user approves doc sync) |
| **Do not touch** | Schemas |
| **Verification** | Full adapter bundle + integration + optional timing note |
| **Expected output** | Demo-ready verdict with evidence paths |

---

## 10. Final Verdict

### At audit time (2026-05-25)

| Question | Blunt answer |
| --- | --- |
| **Can I demo this product flow today?** | **Not reliably from the repo alone.** You can demo **modules and offline decision-package logic**, but a **client-visible product walkthrough** needs a **fresh `run_portfolio_review.py` run** (prefer `--candidates <one>`) and inspection of gitignored `Main portfolio/`. Expect **~9 minutes** for default core batch. |
| **Shortest path to demo-ready backend?** | (1) Run `python run_portfolio_review.py --candidates equal_weight` (approved network). (2) Implement **Session 03 / RM-ARCH-011** so bundle JSON cross-references are coherent. (3) Add **Session 01** integration test so regressions are caught without live runs. (4) Commit migration source in allowlisted batches so demos are reproducible. |
| **Highest-leverage next fix?** | **`RM-ARCH-011` sidecar wiring + one-candidate default demo command** — aligns runtime with PRODUCT.md story without waiting for UI. |

### After Session 08 closure (2026-05-26)

| Question | Blunt answer |
| --- | --- |
| **Can I demo this product flow today?** | **Yes (MVP backend).** Run `python run_portfolio_review.py --candidates equal_weight` (~2 min subject+factory+compare in Session 07 baseline), then read six bundle JSON under `Main portfolio/` per [OUTPUTS.md](../../OUTPUTS.md). Offline proof: `python -m pytest tests/test_product_bundle_integration.py tests/test_product_bundle_paths.py -q`. |
| **Default command still wrong for product story?** | **Yes, by design** — use `--candidates <id>` for product demo; `--mode core` remains six-candidate regression. |
| **Highest-leverage next work?** | UI/API consumer; optional `RM-ARCH-010` LLM spec (Session 09 deferred); dirty-tree allowlisted commits; optional fix for stale multi-candidate compare on disk (demo C1). |

---

## 11. Remediation evidence (ExecPlan Sessions 01–08)

| Session | Deliverable | Evidence |
| --- | --- | --- |
| 01 | Offline six-file bundle gate | `tests/test_product_bundle_integration.py`, `tests/mvp_offline_fixtures.py` |
| 02 | `RM-ARCH-011` sidecar wiring | `src/product_bundle_paths.py`, `src/candidate_comparison.py`, `tests/test_product_bundle_paths.py` |
| 03 | Manifest `product_bundle_*` keys | `product_bundle_generated_paths_for_manifest` in compare manifest path; `OUTPUTS.md` |
| 04 | One-candidate product CLI (docs) | `docs/operational_runbook.md`, `WORKFLOW.md`, `test_official_one_candidate_product_path_equal_weight` |
| 05 | Launchpad → factory command | `docs/product_flow_operator_guide.md`, `scripts/run_one_candidate_from_method.py` |
| 06 | Operator guide + registers | [product_flow_operator_guide.md](../product_flow_operator_guide.md), `docs/exec_plans/README.md`, `AGENTS.md` |
| 07 | Live disk baseline | [2026-05-25_product_flow_demo_baseline_snapshot.md](2026-05-25_product_flow_demo_baseline_snapshot.md) |
| 08 | Audit closure + roadmap | This section; `RM-ARCH-011` → Done in [ROADMAP.md](../ROADMAP.md); pytest **46 passed** (2026-05-26) |

---

## Audit metadata

| Field | Value |
| --- | --- |
| Method (original) | Static review of docs/specs/code/tests; workspace glob for bundle JSON (0 hits); gitignored `Main portfolio/` noted |
| Runtime verification (original) | **Not executed** (per guardrails: no broad generated-output refresh) |
| Closure (Session 08) | 2026-05-26; ExecPlan Sessions 01–08 complete; pytest bundle 46 passed; live bundle [demo baseline snapshot](2026-05-25_product_flow_demo_baseline_snapshot.md) |
| Register status | **Historical** (superseded by closure); active operator entry: [product flow operator guide](../product_flow_operator_guide.md) |
| Recommended next work | Session 09 / `RM-ARCH-010` only if product approves LLM; UI consumer mapping; optional dirty-tree commit per DIRTY_TREE_CLEANUP_PLAN |
