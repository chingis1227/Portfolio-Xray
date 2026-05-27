# Final Architecture Consistency Audit Plan

**Date:** 2026-05-27  
**Type:** Read-only audit + session-based cleanup plan (no code or doc fixes in this session)  
**Scope:** Code, documentation, runtime behavior, JSON output contracts, AI Commentary boundaries, legacy contamination  
**Product truth audited:** ДИАГНОСТИКА 2 — diagnosis-first, portfolio-first, decision-support (not black-box optimizer)

**Evidence used:** `SPEC.md`, `README.md`, `OUTPUTS.md`, `AGENTS.md`, `docs/product_flow_operator_guide.md`, `docs/operational_runbook.md`, `docs/specs/portfolio_review_workflow_spec.md`, `docs/specs/ai_commentary_grounding_spec.md`, core modules under `src/`, entrypoints `run_portfolio_review.py` / `run_report.py` / `run_candidate_factory.py`, targeted greps, and live dry-runs:

```text
python run_portfolio_review.py --dry-run
  → Runtime mode: product_diagnosis_only; workflow state: diagnosis_only; stages: input -> diagnosis only

python run_portfolio_review.py --candidates equal_weight --dry-run
  → stages: input -> diagnosis -> candidates (factory + --then-compare)
```

Related prior audits (not duplicated here): [Core MVP Blocks 1–3 cleanup acceptance](../audits/2026-05-27_core_mvp_blocks_1_3_cleanup_acceptance_audit.md), [Core MVP runtime integration audit](core_mvp_runtime_integration_and_entrypoint_audit_plan.md).

---

## A. Executive Summary

### Alignment verdict

| Dimension | Verdict | Notes |
| --- | --- | --- |
| **Code vs documentation** | **Partially aligned** | Canonical trio (`SPEC.md`, `README.md`, `product_flow_operator_guide.md`, `portfolio_review_workflow_spec.md`) matches diagnosis-only default. Several operator/runbook/audit/agent surfaces still describe batch `core_fast` as the **default** review behavior. |
| **Documentation vs runtime** | **Mostly aligned at canonical docs; misaligned in runbooks** | Live dry-run confirms default path is diagnosis-only under `analysis_subject/`. `docs/operational_runbook.md` still documents default `run_portfolio_review.py` → `core_fast` factory + compare. |
| **AI Commentary grounding** | **Split boundary — structurally sound for future LLM; legacy narrative still active elsewhere** | `ai_commentary_context.json` is evidence-only and well-guarded, but is **not** produced on diagnosis-only runs; it omits X-Ray/stress field refs in `evidence_references`. Rule-based `commentary.txt` / `stress_commentary.txt` (legacy export) still emit mandate/gate narrative and PASS/FAIL wording. |
| **Code vs product architecture** | **Core Blocks 1–3 clean; decision layer still mandate-aware** | Portfolio-first materialization avoids optimizer by default. Selection Engine / Decision Verdict / legacy commentary retain mandate semantics for advanced/compare paths. |

### Top 5 architecture inconsistencies

1. **`docs/operational_runbook.md` default command matrix contradicts code** — table rows label plain `run_portfolio_review.py` as **Core (default) → `core_fast` six candidates**; code default is `diagnosis_only` with `factory profile: none` (verified dry-run 2026-05-27).

2. **Six-file product bundle vs default runtime** — operator guide read order lists `decision_verdict.json` and `ai_commentary_context.json` as Core MVP bundle files, but they are written only after **compare** (`write_candidate_comparison_outputs`); default diagnosis-only run produces bundle **#1–2** only (`problem_classification`, `candidate_launchpad` under `analysis_subject/`).

3. **`ai_commentary_context.json` allowed artifacts vs emitted references** — spec and module list `portfolio_xray.json` / `stress_report.json` as allowed sources, but `build_ai_commentary_context` never adds field-path references from those files (hallucination risk when LLM layer is added).

4. **Dual narrative layers not distinguished in all docs** — README correctly separates LLM grounding (`ai_commentary_context.json`) from rule-based `commentary.txt`; legacy `portfolio_commentary.py` still generates mandate/gate prose (`Client MaxDD gate`, `mandate_check`) on **full_report/legacy_export** paths, easy to confuse with “AI Commentary”.

5. **`PRODUCT_MENU_PROFILE_ID = "default_v1"` in comparison code** — `src/candidate_comparison.py` embeds full-menu semantics as “product menu” while canonical product truth is current-vs-selected-candidate; harmless when one explicit `--candidates` id runs, confusing when interpreting `candidate_menu` after partial runs.

### Overall posture

The **implemented Core MVP diagnostic path (Blocks 1–3, subject-first materialization)** is largely consistent with ДИАГНОСТИКА 2. Residual risk is **documentation staleness**, **decision-layer mandate vocabulary**, **legacy report/commentary surfaces**, and **incomplete product-bundle artifacts on the default command** — not a wholesale optimizer-first code regression.

---

## B. Code vs Docs Findings

| ID | File path | Doc / code location | Exact mismatch | Why it matters | Severity | Recommended action |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | `docs/operational_runbook.md` | § Portfolio-first commands, lines 54–57, 86–90, 121 | Docs: default `run_portfolio_review.py` runs `core_fast` (6 candidates). Code: `resolve_candidate_execution_flags` → diagnosis-only unless `--candidates`, `--with-candidates`, `--mode full`, etc. | Operators/agents run wrong command and interpret stale `candidate_comparison.json` as “the” product answer. | **High** (active contradiction) | Rewrite runbook default table to match `portfolio_review_workflow_spec.md` Session 09; move `core_fast` under `--with-candidates` only. |
| B2 | `docs/operational_runbook.md` | Blocks 1–5 checklist step 2 (line ~121) | Pass criterion: `--mode core --skip-pdf` completes factory + comparison. | Acceptance checklist encodes old batch-first behavior. | **High** | Update checklist to diagnosis-only default + explicit branches for batch/demo. |
| B3 | `docs/specs/portfolio_review_workflow_spec.md` | Operational Model §340–341 | Text: “portfolio-first `--mode core` uses `core_fast`” without stating `--mode` applies only when candidates run. | Implies `--mode core` alone triggers factory; default run ignores factory profile. | **Medium** (documentation mismatch) | Clarify: `--mode core` selects profile **when** candidates are requested; default CLI is diagnosis-only regardless of mode label. |
| B4 | `docs/audits/2026-05-23_blocks_1_5_actual_algorithm_walkthrough.md` | Commands section | Still documents `python run_portfolio_review.py --mode core --skip-pdf` as routine path. | Archived walkthrough cited as evidence in regressions. | **Medium** (stale docs) | Add banner “superseded by diagnosis-only default (2026-05-26+)” or update commands. |
| B5 | `docs/audits/2026-05-26_canonical_product_truth_reset_audit.md` | Finding #4 | States default still runs batch `core_fast`. | Partially **fixed in code** but audit reads as current truth. | **Medium** (stale docs) | Append closure note referencing dry-run evidence; link to this audit. |
| B6 | `.cursor/agents/portfolio-ux-thinking-agent.md` | Core journey diagram §65–81 | Lists Macro Dashboard, Robustness/Health Score, Selection Engine, Rebalancing Advisor as sequential product journey. | Agent guidance contradicts `SPEC.md` Core MVP scope; steers UX/design toward advanced modules. | **High** (active contradiction for agents) | Re-label diagram: Core MVP path vs Advanced/Legacy path; align with `product_flow_operator_guide.md`. |
| B7 | `.cursor/agents/portfolio-ux-thinking-agent.md` | Screen table §154 | “Robustness / Health Score” as standard screen. | Same as B6 for Cursor agents. | **Medium** | Mark advanced/backend; point to `decision_verdict.json` for Core MVP. |
| B8 | `README.md` vs `run_candidate_factory.py` | README § command matrix vs CLI `--profile` default | README labels factory as backend/advanced; standalone CLI still defaults to `default_v1` (16 builders). | Risk if operators use factory CLI as product front door. | **Medium** (advanced/later poorly labelled) | README/runbook: warn “standalone factory default = research full menu”. |
| B9 | `OUTPUTS.md` | Command matrix | Aligned with diagnosis-only default (verified). | — | — | Keep as reference; ensure runbook matches OUTPUTS. |
| B10 | `SPEC.md` | Terminology boundary | Product: Decision Verdict; technical: Selection Engine — documented. | Code still exposes `mandate_risk_reduction` in verdict mapping. | **Low** (harmless if labelled legacy) | Document in `decision_verdict_spec.md` that mandate statuses are advanced/legacy policy semantics. |
| B11 | `src/candidate_comparison.py` | `PRODUCT_MENU_PROFILE_ID = "default_v1"` | Product truth: selected candidate / shortlist; code constant names full menu as product menu. | Comparison warnings (`reduced_menu_scope_vs_product_default_v1`) mislead on one-candidate demos. | **Medium** | Rename constant/doc to `FULL_MENU_PROFILE_ID`; product default = explicit candidate id. |
| B12 | `docs/specs/portfolio_xray_diagnostics_spec.md` vs `src/portfolio_xray.py` | Spec: Blocks 2.1–2.6 Core; §2.7 archetype not Core | Code still builds `sections.portfolio_archetype` and `format_portfolio_xray_commentary` includes archetype lines. | UI consuming `sections.*` treats non-Core block as product truth. | **Medium** | Docs already warn; add contract test forbidding archetype in `block_2_*` keys (may exist). |
| B13 | `AGENTS.md` | Main Commands | Lists `run_optimization.py` before portfolio review in legacy section; primary path is `run_portfolio_review.py` — **aligned**. | Minor: “being reset around ДИАГНОСТИКА 2” reads as in-progress. | **Low** (stale comment) | Tighten wording to “canonical product is ДИАГНОСТИКА 2”. |
| B14 | `docs/product_flow_operator_guide.md` | Six-file bundle table | Bundle #4–6 require compare; read order does not state “absent until `--candidates` / compare”. | New chats expect `decision_verdict.json` after default run. | **Medium** | Add explicit “present only after compare” column. |
| B15 | `run_report.py` | Materialize path | Writes `problem_classification.json` + `candidate_launchpad.json` on subject materialization — **matches** Blocks 4 prep docs. | Launchpad without user-triggered builder is OK as “suggested hypotheses”. | — | Document as “post-diagnosis, pre-candidate” artifacts. |

---

## C. Runtime vs Docs Findings

| ID | Command / mode | Documented behavior | Actual behavior (2026-05-27 dry-run / code) | Output paths | Mismatch | Recommended action |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | `python run_portfolio_review.py` | **Canonical docs:** diagnosis-only (`product_flow_operator_guide`, `portfolio_review_workflow_spec`, `README`). **Runbook:** `core_fast` batch. | `runtime_mode=product_diagnosis_only`, `workflow_state=diagnosis_only`, single stage `run_report.py --materialize-analysis-subject --output-profile site_api`. | `{output_dir_final}/analysis_subject/*`; no root compare artifacts | Runbook vs code | Fix `operational_runbook.md` (B1). |
| R2 | `python run_portfolio_review.py --candidates equal_weight` | One hypothesis + compare + verdict bundle | Dry-run: diagnosis + `run_candidate_factory.py --candidates equal_weight ... --then-compare` | `analysis_subject/` + root `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, etc. | **Aligned** | Keep as official demo command. |
| R3 | `python run_portfolio_review.py --with-candidates` | Backend `core_fast` batch (`OUTPUTS.md`, workflow spec) | Code: `explicit_batch_request` → factory with resolved profile `core_fast` | Factory + comparison artifacts | **Aligned** with canonical docs (not runbook default) | Label “advanced/research” in runbook header. |
| R4 | `python run_portfolio_review.py --mode full` | `default_v1` full menu | Code: `mode == "full"` triggers batch | 16-candidate evidence | **Aligned** | Anti-pattern already in operator guide. |
| R5 | Default output profile `site_api` | JSON/cache only; no PDF/TXT (`OUTPUTS.md`, `portfolio_run_scope` rule 6) | `output_policy.py`: `write_txt=false` → no `commentary.txt` on default review | JSON under `analysis_subject/` | Docs **aligned**; user may expect commentary files | Reinforce in operator guide: TXT/PDF require `--output-profile full_report` or `--with-pdf`. |
| R6 | `python run_optimization.py` | Legacy policy-only (`SPEC.md`, `README`) | Still optimizes + stress; writes root `Main portfolio/` artifacts | Root `stress_report.json`, `portfolio_weights.yml` | **Aligned** as legacy | Ensure all guides say “not Core MVP entry”. |
| R7 | `python run_candidate_factory.py` (no args) | Not product default; profile default `default_v1` in code | Runs full 16-builder menu if invoked bare | `candidate_factory_run.json`, variant folders | Poorly labelled standalone default (B8) | Change CLI help text + docs warning. |
| R8 | Product bundle on R1 | Operator read order steps 7–9 | `decision_verdict.json`, `ai_commentary_context.json`, `what_changed_summary.json` **not created** without compare | N/A | Docs imply always present | Document conditional presence (B14). |
| R9 | `portfolio_xray.json` keys | Spec: `block_2_1`…`block_2_6` Core MVP | Live acceptance audit (2026-05-27): blocks present; `legacy_summary._scope.product_surface=false` | `analysis_subject/portfolio_xray.json` | **Aligned** | Maintain contract tests. |
| R10 | `stress_report.json` keys | Block 3 product keys; diagnostic `loss_gate_mode` | Acceptance audit: no row-level `pass`/`loss_ok` in product rows | `analysis_subject/stress_report.json` | **Aligned** for Core MVP path | Keep `test_stress_diagnostic_mode.py` green. |
| R11 | `run_mvp_workflow.py --workflow diagnosis-only` | Legacy wrapper (`operational_runbook`) | Chains `run_report.py` without portfolio-first subject contract guarantees | Root outputs | Parallel legacy path vs `run_portfolio_review.py` | Document “prefer `run_portfolio_review.py` for product contract”. |

---

## D. AI Commentary Boundary Findings

| ID | File path | Function / module | What is generated | JSON evidence | Grounded? | Recommended action |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | `src/ai_commentary_context.py` | `build_ai_commentary_context` | Deterministic grounding stub: rules, `evidence_references`, `warnings` | Pulls refs from problem_classification, launchpad, comparison, selection, verdict, action, monitoring — **not** from xray/stress bodies | **Partial** — rules good; evidence refs incomplete vs allowed list | Add optional xray/stress refs (summary fields only); fail warnings when missing on diagnosis-only. |
| D2 | `src/ai_commentary_context.py` | `_warnings` | Requires comparison, current_vs_candidate, selection, verdict | On diagnosis-only: all missing → `missing_required_source:*` | **Correct behavior** for compare bundle; confusing if reader expects file after R1 | Document: file only after compare; optional diagnosis-only stub without verdict warnings. |
| D3 | `docs/specs/ai_commentary_grounding_spec.md` | Product role § | States target flow Decision Verdict → AI Commentary | V1: no LLM; context only | **Aligned** | Keep; cross-link operator guide anti-pattern. |
| D4 | `src/portfolio_commentary.py` | `write_portfolio_commentary` | Full `commentary.txt` sections (Executive Summary … Final Conclusion) from metrics + stress + RC | Numbers from `portfolio_metrics`, `stress_report`, snapshots; synthesis prose in Python | **Grounded in numbers** but **narrative synthesis in code** (not AI layer); uses `portfolio_valid` → “Client MaxDD gate PASS/FAIL” | Mark as **legacy report export**, not AI Commentary; gate wording policy-only. |
| D5 | `src/portfolio_commentary.py` | `write_stress_commentary` | Stress narrative; line ~1802 references `mandate_check`, weight-release | `stress_report.json` | **Risky wording** for Core MVP (mandate language) | Gate behind `loss_gate_mode=mandate` or remove mandate phrases in diagnostic mode. |
| D6 | `src/portfolio_xray.py` | `format_portfolio_xray_commentary` | Archetype / hidden risk / weakness sentences for commentary embed | `portfolio_xray.json` sections | Deterministic template from structured fields — **OK** if labelled diagnostic | Do not route to `ai_commentary_context`; keep out of client AI path. |
| D7 | `src/decision_verdict.py` | `_recommended_action`, `STATUS_TO_VERDICT` | Product strings e.g. “Rebalance to selected candidate”, “Review mandate/risk reduction…” | Maps from `selection_decision.json` | **Grounded** in selection status; `mandate_risk_reduction` is policy-era status | Expose `verdict_family: policy_mandate` in JSON for UI filtering on Core MVP. |
| D8 | `src/problem_classification.py` | `build_problem_classification` | Rule-based problems + fallback `current_portfolio_acceptable` | Evidence links to xray sections / stress | **Grounded** — deterministic classification | Safe for product; not LLM. |
| D9 | `src/pdf_reports.py` | `build_commentary_report_md`, `_english_commentary_md` | Client PDF narrative from `commentary.txt` or synthesized KPI blocks | Structured run outputs | Second narrative layer; sanitized | Ensure PDF path never default on `site_api` (already disabled). |
| D10 | `src/selection_engine.py` | Rationale text, regex guards | Technical decision record; blocks “recommended buy/sell” phrases | `candidate_comparison`, health/robustness scores | Engine is **not** AI but produces decision narrative | Keep as backend evidence; product UI uses `decision_verdict.json`. |
| D11 | `src/stress_factors.py` | `residual_recommendation` strings | Factor decomposition interpretive text | Factor regression block | Diagnostic metadata | OK in stress evidence; forbid copy into Core MVP product bundle without citation. |
| D12 | N/A (future) | LLM consumer of `ai_commentary_context.json` | Not implemented (RM-ARCH-010 deferred) | — | **Risk:** allowed artifacts include xray/stress but refs absent (D1) | Session 4 below. |

**Boundary summary:** The **correct** product boundary is implemented for `ai_commentary_context.json` (no LLM, no new metrics). The **leak** is legacy **`portfolio_commentary.py`** and **PDF builders** still producing mandate/gate narrative on export paths, which violates the spirit of “AI Commentary explains structured JSON” if operators conflate files.

---

## E. Legacy Contamination Inventory

### Core-breaking (fix before claiming clean Core MVP UX)

| Item | Location | Classification |
| --- | --- | --- |
| Runbook default = `core_fast` batch | `docs/operational_runbook.md` | Active contradiction with code |
| Agent UX journey includes Health Score / Selection / Macro as core | `.cursor/agents/portfolio-ux-thinking-agent.md` | Active contradiction for agents |

### Confusing but harmless (if labelled)

| Item | Location | Classification |
| --- | --- | --- |
| `PRODUCT_MENU_PROFILE_ID = "default_v1"` | `src/candidate_comparison.py` | Advanced/later poorly labelled |
| `mandate_risk_reduction` → Decision Verdict copy | `src/decision_verdict.py`, `selection_engine.py` | Legacy policy semantics in compare path |
| `sections.*` + archetype in X-Ray | `src/portfolio_xray.py` | Legacy section coupling; product blocks clean |
| Root `portfolio_xray.json` / `stress_report.json` after policy runs | `Main portfolio/` | Legacy artifact staleness vs `analysis_subject/` |
| 33× `run_*.py` entrypoints at repo root | repo root | Legacy/advanced scripts look like product commands |

### Advanced / later (implemented, not Core MVP)

| Item | Location |
| --- | --- |
| Portfolio Health Score, Robustness Scorecard | `src/portfolio_health_score.py`, `src/robustness_scorecard.py` |
| Selection Engine, Action Plan, Decision Journal | `src/selection_engine.py`, `src/action_engine.py`, journal writers |
| Macro/regime diagnostics | stress + macro modules |
| Full candidate factory `default_v1` | `run_candidate_factory.py` |
| Pareto, regret, assumption sensitivity | compare pipeline |

### Legacy / archive

| Item | Location |
| --- | --- |
| `run_optimization.py` / `run_mvp_workflow.py` policy workflows | documented compatibility |
| `config/client_profiles.yml` | legacy mandate |
| Archived audits with batch-default commands | `docs/audits/2026-05-23_*`, `2026-05-26_canonical_*` |
| Historical ExecPlans with optimizer-first wording | `docs/exec_plans/*` (see register disclaimer) |

### Stale docs / comments

| Item | Location |
| --- | --- |
| “portfolio-first `--mode core` uses core_fast” without candidate guard | `portfolio_review_workflow_spec.md` |
| Blocks 1–5 checklist requiring factory on default run | `operational_runbook.md` |
| `AGENTS.md` “being reset around ДИАГНОСТИКА 2” | minor |

### Generated artifact staleness

| Item | Notes |
| --- | --- |
| `Main portfolio/` gitignored outputs | May reflect old batch runs; must not be cited as spec proof |
| PDFs under `pdf files/` after `site_api` review | Stale vs JSON per `portfolio_run_scope` rule 6 |
| `candidate_comparison.json` after partial factory | `factory_evidence_status` may be stale |

### Needs verification

| Item | Notes |
| --- | --- |
| Whether `run_report.py` materialize always attaches Block 2.3 when factor pipeline fails | F8 in runtime integration audit |
| Full pytest green (9 failures noted in Blocks 1–3 acceptance audit) | Separate from architecture doc alignment |

---

## F. Session-Based Cleanup Plan

Each session is scoped for a **fresh chat**. Do not mix unrelated refactors.

### Session 1 — Documentation truth audit and correction plan

**Objective:** Single source of truth for default runtime and Core MVP scope across operator-facing docs.

**Files likely touched:** `docs/operational_runbook.md`, `docs/audits/2026-05-26_canonical_product_truth_reset_audit.md` (banner), `docs/audits/2026-05-23_blocks_1_5_actual_algorithm_walkthrough.md`, `.cursor/agents/portfolio-ux-thinking-agent.md`, `AGENTS.md` (wording only).

**Tasks:**
- Replace runbook default matrix with diagnosis-only default; relocate `core_fast` to `--with-candidates`.
- Update Blocks 1–5 acceptance checklist step 2.
- Split UX agent journey into Core MVP vs Advanced/Legacy.
- Add “superseded” banners on stale audits or update commands.

**Tests:** `python scripts/verify_docs.py`; `pytest tests/test_documentation_links.py` (if present).

**Commands:** `rg -n "core_fast.*default|default.*core_fast" docs README.md OUTPUTS.md`

**Acceptance:** No doc states plain `run_portfolio_review.py` runs factory by default; agent diagram matches `SPEC.md`.

**Must not change:** Formulas, stress scenarios, optimizer code, JSON schemas.

---

### Session 2 — Runtime documentation alignment

**Objective:** Align workflow spec and runbook with `resolve_candidate_execution_flags` behavior.

**Files likely touched:** `docs/specs/portfolio_review_workflow_spec.md`, `docs/operational_runbook.md`, `docs/product_flow_operator_guide.md` (bundle presence column), `TESTING.md` command tables.

**Tasks:**
- Clarify `--mode core` only affects factory profile when candidates run.
- Document `runtime_mode` / `workflow_state` values from dry-run output.
- Add decision-tree: diagnosis → one candidate → batch → full.

**Tests:** `pytest tests/test_runtime_mode_regression_boundaries.py tests/test_mvp_portfolio_review_materialization.py -q`

**Commands:**
```bash
python run_portfolio_review.py --dry-run
python run_portfolio_review.py --candidates equal_weight --dry-run
python run_portfolio_review.py --with-candidates --dry-run
```

**Acceptance:** Dry-run transcripts match documented stages for all four commands.

**Must not change:** `run_portfolio_review.py` logic unless a doc bug reveals a real code bug (file separate ticket).

---

### Session 3 — JSON output contract alignment

**Objective:** Product bundle and comparison contracts match “selected candidate first” truth.

**Files likely touched:** `src/candidate_comparison.py` (constant naming/comments only), `docs/specs/candidate_factory_spec.md`, `OUTPUTS.md`, `docs/product_flow_operator_guide.md`, `src/product_bundle_paths.py` docstrings.

**Tasks:**
- Rename/document `PRODUCT_MENU_PROFILE_ID` as full-menu research profile.
- Document bundle files #4–6 as post-compare only.
- Verify `output_manifest.json` `artifact_categories.product_bundle` reflects presence/absence.

**Tests:** `pytest tests/test_product_bundle_paths.py tests/test_product_bundle_integration.py -q`

**Acceptance:** Offline bundle tests pass; manifest keys documented for diagnosis-only vs one-candidate.

**Must not change:** Selection formulas, comparison math, factory builders.

---

### Session 4 — AI Commentary grounding audit

**Objective:** Close gap between allowed artifacts and evidence references; separate legacy commentary from AI layer.

**Files likely touched:** `src/ai_commentary_context.py`, `docs/specs/ai_commentary_grounding_spec.md`, `src/portfolio_commentary.py` (mandate wording gates), `README.md` (narrative layer table).

**Tasks:**
- Add xray/stress summary refs to `evidence_references` (top-level summary fields only).
- Optional: diagnosis-only `ai_commentary_context` with `purpose=diagnosis_grounding_only` and no compare warnings.
- Gate `mandate_check` / PASS/FAIL commentary behind legacy export + mandate mode.

**Tests:** `pytest tests/test_ai_commentary_context.py tests/test_portfolio_commentary.py tests/test_generated_output_language.py -q`

**Acceptance:** Spec lists match emitted refs; diagnostic materialize does not write misleading mandate PASS/FAIL in `site_api` path.

**Must not change:** Selection Engine statuses; do not add LLM calls.

---

### Session 5 — Legacy language cleanup

**Objective:** Label legacy/advanced surfaces consistently in code comments and user-facing strings.

**Files likely touched:** `run_candidate_factory.py` help text, `decision_verdict.py` (metadata): `src/selection_engine.py` docstrings, `docs/specs/decision_verdict_spec.md`, `docs/specs/selection_engine_spec.md`, historical ExecPlan register entries.

**Tasks:**
- CLI warnings for standalone factory default `default_v1`.
- Document `mandate_risk_reduction` as policy-path status in verdict spec.
- Ensure `portfolio_xray` archetype section labelled non-Core in HTML/commentary formatters.

**Tests:** `pytest tests/test_decision_verdict.py tests/test_selection_engine.py -q`

**Acceptance:** Core MVP JSON outputs contain no new mandate fields; legacy paths unchanged functionally.

**Must not change:** Mandate gate math in `run_optimization.py` legacy path.

---

### Session 6 — Regression tests for architecture consistency

**Objective:** Automated guards against doc/runtime drift and commentary boundary regressions.

**Files likely touched:** `tests/test_runtime_mode_regression_boundaries.py`, a new architecture-consistency test module (filename to be created in implementation session), `scripts/verify_docs.py` (optional grep rules).

**Tasks:**
- Assert dry-run plan stages for default vs `--candidates` vs `--with-candidates`.
- Assert `site_api` does not write `commentary.txt`.
- Assert diagnosis-only materialization does not write `decision_verdict.json` at root.
- Optional: doc lint forbidding “default.*core_fast” in `operational_runbook.md`.

**Tests:** New tests + existing runtime boundary tests.

**Commands:** `python -m pytest <new_architecture_consistency_test_module> tests/test_runtime_mode_regression_boundaries.py -q`

**Acceptance:** CI catches reintroduction of batch-default documentation strings if linted; runtime tests green.

**Must not change:** Production formulas.

---

### Session 7 — Final acceptance audit

**Objective:** Close this ExecPlan with a checked-in audit mirroring Blocks 1–3 acceptance format.

**Files likely touched:** a new final acceptance audit markdown under `docs/audits/` (filename to be created in implementation session), `docs/exec_plans/README.md` pointer, `CHANGELOG.md` (one line).

**Tasks:**
- Live run: `run_portfolio_review.py` (diagnosis) + `--candidates equal_weight` (demo).
- Verify read order files exist per path.
- Re-run targeted pytest + `verify_docs.py`.
- Record remaining global pytest failures separately.

**Acceptance criteria:** See section G below.

**Must not change:** Scope beyond verification and audit markdown.

---

## G. Acceptance Criteria

The project is **architecture-clean** for ДИАГНОСТИКА 2 Core MVP when all of the following hold:

1. **Docs describe what code does** — Default `run_portfolio_review.py` documented as diagnosis-only everywhere operators look (`operational_runbook`, audits, agents).
2. **Runtime commands match docs** — Dry-run stages match command matrix for default, one-candidate, batch, and full modes.
3. **JSON outputs match specs** — `analysis_subject/portfolio_xray.json` has `block_2_1`–`block_2_6`; `stress_report.json` has Block 3 product keys without mandate row fields in diagnostic mode; product bundle files #1–2 always after materialize; #3–6 only after compare.
4. **AI Commentary grounded** — `ai_commentary_context.json` references include diagnosis artifacts when present; no LLM; legacy `commentary.txt` clearly separated and not default on `site_api`.
5. **Legacy labelled** — Optimizer, Health Score, Selection Engine, macro, full factory menu marked legacy/advanced in docs and agent rules.
6. **Core MVP posture** — Diagnosis-first, portfolio-first, decision-support language in canonical docs; no black-box optimizer framing for default path.
7. **Verification** — `scripts/verify_docs.py` OK; `tests/test_runtime_mode_regression_boundaries.py` + architecture consistency tests pass; acceptance audit filed.

---

## Progress (audit session)
  
- [x] Read canonical specs and entrypoints
- [x] Dry-run default and one-candidate commands
- [x] Review AI commentary modules and legacy commentary
- [x] Inventory legacy contamination
- [x] Draft session cleanup plan
- [x] Session 1 — Documentation truth audit and correction plan
- [x] Session 2 — Runtime documentation alignment (2026-05-27)
- [x] Session 3 — JSON output contract alignment (2026-05-27)
- [x] Session 4 — AI Commentary grounding audit (2026-05-27)
- [x] Session 5 — Legacy language cleanup (2026-05-27)
- [x] Session 6 — Regression tests for architecture consistency (2026-05-27)
- [x] Session 7 — Final acceptance audit (2026-05-27)

## Surprises & Discoveries

- Default dry-run already reports `product_diagnosis_only` / `diagnosis_only` — code moved ahead of `operational_runbook.md`.
- `site_api` disables TXT, so rule-based commentary is not the default runtime narrative surface (reduces but does not eliminate confusion with future LLM layer).

## Decision Log

| ID | Decision | Rationale |
| --- | --- | --- |
| AD-1 | Treat Blocks 1–3 subject path as **accepted** baseline | Per 2026-05-27 Blocks 1–3 acceptance audit |
| AD-2 | Prioritize runbook/agent doc fixes over code refactors | Largest user-facing drift is documentation, not default CLI |
| AD-3 | Do not conflate `commentary.txt` with `ai_commentary_context.json` | Different pipelines and output profiles |

## Outcomes & Retrospective

This session delivered a **read-only** discrepancy map and seven implementation sessions. Core diagnostic architecture is largely aligned with ДИАГНОСТИКА 2; remaining work is **documentation/agent alignment**, **product-bundle presence clarity**, **AI grounding completeness**, and **legacy narrative gating** — not a fundamental redesign.
  
---
  
### Session 7 closure (2026-05-27)

**Commands run**

- `python run_portfolio_review.py`
- `python run_portfolio_review.py --candidates equal_weight --no-skip-existing --force-candidates`
- `python scripts/validate_one_candidate_demo.py --output-dir "Main portfolio" --candidate-id equal_weight`
- `python scripts/verify_docs.py`
- `python -m pytest tests/test_runtime_mode_regression_boundaries.py tests/test_architecture_consistency.py tests/test_docs_links.py -q`

**Artifacts verified**

- Diagnosis-only subject path: `Main portfolio/analysis_subject/run_metadata.json`, `portfolio_xray.json`, `stress_report.json`, `problem_classification.json`, `candidate_launchpad.json`, `snapshot_10y.json`, `output_manifest.json`.
- Post-compare product bundle: `Main portfolio/current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, `what_changed_summary.json`, `candidate_factory_run.json`, `candidate_comparison.json`.

**Validation results**

- `validate_one_candidate_demo.py` reported **RESULT: PASS** for `equal_weight` (factory steps, scoping, verdict id, AI context, `what_changed_summary`, output manifest product bundle discovery).
- `scripts/verify_docs.py` reported **docs verification: OK** (including operational runbook architecture lint).

**Tests passed**

- `tests/test_runtime_mode_regression_boundaries.py`
- `tests/test_architecture_consistency.py`
- `tests/test_docs_links.py`

**Runtime confirmation**

- Diagnosis-only CLI (`python run_portfolio_review.py`) runs with `runtime_mode=product_diagnosis_only`, materializes `analysis_subject/*` and does **not** refresh root compare/product-bundle JSON.
- One-candidate CLI (`python run_portfolio_review.py --candidates equal_weight --no-skip-existing --force-candidates`) refreshes subject diagnostics, runs a single factory builder, and writes the six-file product bundle at `Main portfolio/` scoped to `equal_weight` (confirmed by validator and timestamps).

**Remaining caveats**

- Full-suite `python -m pytest` may still report known contract-drift failures (tracked separately in `KNOWN_ISSUES.md`) that are outside this ExecPlan’s architecture-scope.
- Legacy/advanced modules (Selection Engine, full factory menus, Health Score, macro diagnostics, policy optimizer) remain available and must stay clearly labelled non-Core in docs and agent guidance.

**Final status**

- **ExecPlan status:** completed / accepted for ДИАГНОСТИКА 2 Core MVP architecture consistency.
  
### Session 6 closure (2026-05-27)

- Added `tests/test_architecture_consistency.py`: dry-run stage contracts (default / `--candidates` / `--with-candidates`), `site_api` no TXT on materialize, no root post-compare JSON on diagnosis-only.
- Extended `src/docs_verify.py`: operational runbook architecture lint (required diagnosis-only anchors + forbidden batch-default patterns).
- Extended `tests/test_docs_links.py`: `test_operational_runbook_architecture_contract`.
- Verified: `pytest tests/test_architecture_consistency.py tests/test_runtime_mode_regression_boundaries.py tests/test_docs_links.py -q`; `python scripts/verify_docs.py`.

### Session 5 closure (2026-05-27)

- `run_candidate_factory.py`: CLI description/epilog + warning when standalone default is `default_v1` full research menu.
- `src/decision_verdict.py`: `verdict_family` metadata (`core_compare` vs `policy_mandate` for `mandate_risk_reduction`).
- `src/selection_engine.py`: docstrings label `mandate_risk_reduction` as legacy policy-path status.
- `src/portfolio_xray.py`: legacy scope labels for `portfolio_archetype` / related sections in text, HTML, and commentary formatters.
- Updated `docs/specs/decision_verdict_spec.md`, `docs/specs/selection_engine_spec.md`.
- Verified: `pytest tests/test_decision_verdict.py tests/test_selection_engine.py -q`.

### Session 4 closure (2026-05-27)

- `src/ai_commentary_context.py`: xray/stress summary `evidence_references`; `purpose` / `grounding_phase`; diagnosis-only warnings.
- Diagnosis materialize writes `ai_commentary_context.json` via `run_report.py`; compare path passes xray/stress from `load_diagnosis_bundle_docs`.
- `src/portfolio_commentary.py`: mandate PASS/FAIL and `mandate_check` narrative gated on `loss_gate_mode=mandate`.
- Updated `docs/specs/ai_commentary_grounding_spec.md`, `README.md` narrative table.
- Verified: `pytest tests/test_ai_commentary_context.py tests/test_portfolio_commentary.py tests/test_generated_output_language.py -q`.

### Session 3 closure (2026-05-27)

- Renamed comparison constant to `FULL_MENU_RESEARCH_PROFILE_ID` (`PRODUCT_MENU_PROFILE_ID` alias); `candidate_menu` adds `full_menu_baseline_profile_id`; `partial_menu_reason` → `reduced_menu_scope_vs_full_menu_default_v1`.
- `product_bundle_paths.py`: diagnosis vs post-compare manifest keys; `product_discovery.product_bundle_phase` / `diagnosis_bundle_complete` / `post_compare_bundle_complete`.
- Updated `OUTPUTS.md`, `product_flow_operator_guide.md`, `candidate_factory_spec.md`, `candidate_comparison_spec.md`.
- Verified: `pytest tests/test_product_bundle_paths.py tests/test_product_bundle_integration.py -q`.

### Session 2 closure (2026-05-27)

- Updated `portfolio_review_workflow_spec.md`: `runtime_mode` table, `--mode` vs candidate execution, decision tree, dry-run transcripts; fixed `--mode core` / `core_fast` wording in Operational Model.
- Updated `product_flow_operator_guide.md`: bundle **When present** column; runtime dry-run table.
- Updated `operational_runbook.md`: §0.1a runtime dry-run matrix; clarified `--mode core` does not run factory alone.
- Updated `workflow_state_spec.md`: default plan → `diagnosis_only`.
- Updated `TESTING.md`: live core E2E and CLI smoke commands use `--with-candidates` / default diagnosis paths.
- Verified: four dry-run commands match documented stages; `pytest tests/test_runtime_mode_regression_boundaries.py tests/test_mvp_portfolio_review_materialization.py -q`.
