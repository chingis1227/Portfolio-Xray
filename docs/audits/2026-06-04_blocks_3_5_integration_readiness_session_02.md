# Blocks 3-5 Integration Readiness — Session 02 Live Validation

Date: 2026-06-04
ExecPlan: [Blocks 3-5 Integration Readiness Audit Plan](../exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md)
Scope: controlled live-output validation for Block 3 Stress Lab → Block 4 diagnosis / launchpad → Block 5 current-vs-candidate / decision verdict.

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| Did the canonical one-candidate command complete fresh subject materialization? | **No** — blocked before Block 3 refresh by live FRED risk-free loading. |
| Did the workspace validate as `product_one_candidate` after candidate factory / compare materialization? | **Yes** — `scripts/verify_live_core_e2e.py --profile product_one_candidate` returned OK. |
| Did Session 02 rebuild the selected candidate? | **No** — `equal_weight` was reused from an existing snapshot (`skipped_existing`). |
| Are Block 3 product keys present on the subject stress report? | **Yes** — `stress_results_v1`, `hedge_gap_analysis_v1`, and `current_portfolio_stress_scorecard_v1` are present. |
| Are Block 4 and Block 5 product contracts validator-clean together? | **Yes** — live E2E validator passed after factory/compare materialization. |

**Session 02 verdict:** **QUALIFIED_LIVE_VALIDATION_PASS**. The one-candidate product bundle is validator-clean after direct factory/compare materialization, but this session does **not** prove a fully fresh subject Stress Lab refresh because the canonical `run_portfolio_review.py --candidates equal_weight` path was blocked by FRED.

---

## 2. Commands and results

### 2.1 Canonical command attempted

Command:

```text
.\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight
```

Result:

```text
Step failed with exit code 1.
INFO: Loading risk-free rate from FRED:DTB3...
TypeError: deprecate_kwarg() missing 1 required positional argument: 'new_arg_name'
TimeoutError: The read operation timed out
```

Interpretation:

- `pandas_datareader` import reached a dependency compatibility error.
- The fallback FRED CSV path then timed out.
- This blocked fresh `analysis_subject` materialization before the product chain could refresh end-to-end.

### 2.2 Environment repair attempted

Commands:

```text
.\.venv\Scripts\python.exe -m ensurepip --upgrade
.\.venv\Scripts\python.exe -m pip install setuptools
```

Purpose: restore local venv packaging support and the `distutils` compatibility shim from `setuptools`.

Result: install succeeded, but the canonical command still failed on the `pandas_datareader`/FRED path. No repository code was changed.

### 2.3 Pre-materialization validator

Command:

```text
.\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile product_one_candidate
```

Result:

```text
detected_profile=diagnosis_only
ok=False
ERROR: missing candidate_factory_run.json: ...\Main portfolio\candidate_factory_run.json
```

Interpretation: the existing workspace had valid diagnosis evidence but no current one-candidate factory evidence at the root.

### 2.4 Direct factory / compare materialization

Command:

```text
.\.venv\Scripts\python.exe run_candidate_factory.py --candidates equal_weight --then-compare
```

Result:

```text
Run status: full_success
Summary: total=1 succeeded=0 failed=0 skipped_existing=1 skipped_dependency=0 rebuilt_stale=0 resumed_from_manifest=0
Execution: build_steps_executed=0 builder_invoked=0 in_process_build_steps=0 reused_existing=1 reused_existing_snapshot=1
```

Interpretation: the factory stayed scoped to `equal_weight`, reused the existing candidate snapshot, and refreshed root comparison / decision artifacts.

### 2.5 Post-materialization validator

Command:

```text
.\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile product_one_candidate
```

Result:

```text
ok=True
profile=product_one_candidate
factory_profile_id: explicit_list
factory_step_candidate_ids: ['equal_weight']
block_5_view_mode: one_candidate
decision_selected_candidate_id: equal_weight
live core E2E validation: OK
```

---

## 3. Artifact inspection

| Artifact | Observed status |
| --- | --- |
| `Main portfolio/analysis_subject/stress_report.json` | Exists; contains `stress_results_v1`, `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1`; subject stress mtime predates Session 02 compare artifacts. |
| `Main portfolio/analysis_subject/problem_classification.json` | Exists; `schema_version: problem_classification_v3`; primary problem `mixed_evidence_no_action`; stress source `current_portfolio_stress_scorecard_v1`. |
| `Main portfolio/analysis_subject/candidate_launchpad.json` | Exists; `schema_version: candidate_launchpad_v3`; `launchpad_outcome: do_not_act_yet`; two cards. |
| `Main portfolio/candidate_factory_run.json` | Exists after Session 02; `run_status: full_success`; `factory_profile_id: explicit_list`; one `equal_weight` step with `status: skipped_existing`. |
| `Main portfolio/candidate_comparison.json` | Exists after Session 02; includes `candidate_menu`, `hedge_gap_comparison`, and `stress_scorecard_comparison`. |
| `Main portfolio/current_vs_candidate.json` | Exists after Session 02; `schema_version: current_vs_candidate_v1`; `view_mode: one_candidate`; one comparison. |
| `Main portfolio/decision_verdict.json` | Exists after Session 02; `schema_version: decision_verdict_v1`; selected candidate `equal_weight`; verdict `rebalance_to_selected_candidate`. |
| `Main portfolio/ai_commentary_context.json` | Exists after Session 02; `schema_version: ai_commentary_context_v1`; includes Block 3 grounding context. |

---

## 4. Findings

### F1 — Canonical full one-candidate refresh remains externally blocked

The canonical command reached the intended product-one-candidate mode, but failed in the subject materialization step while loading FRED risk-free data. This is outside the Blocks 3-5 contract chain and prevents claiming freshly refreshed subject stress evidence.

**Status:** blocked for fresh subject refresh.

### F2 — Product-one-candidate bundle validates after factory/compare materialization

After `run_candidate_factory.py --candidates equal_weight --then-compare`, the live E2E validator passed with `profile=product_one_candidate`.

**Status:** pass for current workspace contract validation.

### F3 — Candidate was reused, not rebuilt

The factory run recorded `skipped_existing` for `equal_weight`. This is acceptable for a readiness validation, but it is not proof that the candidate builder can rebuild from scratch under current live data conditions.

**Status:** qualified pass.

### F4 — Block 3 comparison slices are present

`candidate_comparison.json` includes both `hedge_gap_comparison` and `stress_scorecard_comparison`. This confirms the Block 3 → comparison bridge is present on the materialized bundle.

**Status:** pass.

---

## 5. Readiness matrix

| Gate | Status | Notes |
| --- | --- | --- |
| Canonical `run_portfolio_review.py --candidates equal_weight` completes | **BLOCKED** | FRED risk-free live dependency timeout after `pandas_datareader` compatibility failure. |
| Subject Block 3 product keys present | **PASS** | Present on existing subject stress report; not freshly refreshed in Session 02. |
| Block 4 diagnosis / launchpad live contracts | **PASS** | Validator reports `problem_classification_v3` / `candidate_launchpad_v3`. |
| Candidate factory scoped to one candidate | **PASS** | `explicit_list`, step ids `['equal_weight']`. |
| Candidate rebuilt fresh | **NOT PROVEN** | Existing snapshot reused. |
| Block 5 current-vs-candidate / verdict live contracts | **PASS** | `one_candidate`, selected `equal_weight`. |
| AI grounding context | **PASS** | Validator passed; context JSON present. |
| Hedge gap and stress scorecard comparison slices | **PASS** | Both keys present in `candidate_comparison.json`. |

---

## 6. Session 02 closure

Session 02 is closed as a qualified live validation. It made no implementation changes. It did refresh generated root JSON under `Main portfolio/` through candidate factory / compare materialization.

Do not treat this as proof of a fully fresh subject Stress Lab refresh. A future session should first resolve or bypass the FRED live-data blocker in an approved way, then rerun:

```text
.\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight
.\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile product_one_candidate
```
