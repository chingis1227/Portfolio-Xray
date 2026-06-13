# Blocks 3-5 Integration Readiness — Session 03 Fresh Refresh Recheck

Date: 2026-06-04
ExecPlan: [Blocks 3-5 Integration Readiness Audit Plan](../exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md)
Scope: Session 03 only — recheck the canonical one-candidate product path after Session 02 and determine whether the fresh subject refresh blocker is cleared.

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| Did the canonical one-candidate command complete fresh subject materialization... | **No** — still blocked by the live FRED `DTB3` risk-free dependency. |
| Did the lower-level FRED loader succeed for `DTB3`... | **No** — direct `fetch_fred_series("DTB3", ...)` ended in `TimeoutError`. |
| Did the existing one-candidate product bundle remain validator-clean... | **Yes** — `scripts/verify_live_core_e2e.py --profile product_one_candidate` returned OK. |
| Did Session 03 change implementation behavior or formulas... | **No** — audit/plan documentation only. |

**Session 03 verdict:** **BLOCKER_RECONFIRMED_CURRENT_BUNDLE_VALID**. The fully fresh `run_portfolio_review.py --candidates equal_weight` path remains blocked by external FRED access, but the existing materialized `product_one_candidate` bundle still validates.

---

## 2. Commands and results

### 2.1 Direct FRED loader probe

Command:

```text
@'
from src.data_fred import fetch_fred_series
try:
    s = fetch_fred_series('DTB3','2026-01-01','2026-06-04')
    print('ok', len(s), s.tail().to_dict())
except Exception as e:
    print('ERR', type(e).__name__, e)
'@ | .\.venv\Scripts\python.exe -
```

Result:

```text
ERR TimeoutError The read operation timed out
```

Interpretation: the FRED public CSV fallback remains unavailable from this environment. The `pandas_datareader` import path also remains incompatible in the project venv, so the loader still falls through to the CSV endpoint and then times out.

### 2.2 Canonical one-candidate command

Command:

```text
.\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight
```

Result:

```text
Mode: product_one_candidate
Runtime mode: product_one_candidate
Workflow state: one_candidate (candidate_count=1, source=candidate_ids)
Step failed with exit code 1.
INFO: Loading risk-free rate from FRED:DTB3...
TypeError: deprecate_kwarg() missing 1 required positional argument: 'new_arg_name'
TimeoutError: The read operation timed out
```

Interpretation: the command reaches the correct product-one-candidate orchestration mode, but fails before fresh `analysis_subject` materialization because risk-free loading cannot complete.

### 2.3 Existing live bundle validator

Command:

```text
.\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile product_one_candidate
```

Result:

```text
detected_profile=product_one_candidate
ok=True
profile=product_one_candidate
factory_profile_id: explicit_list
factory_step_candidate_ids: ['equal_weight']
block_5_view_mode: one_candidate
decision_selected_candidate_id: equal_weight
live core E2E validation: OK
```

Interpretation: the failed fresh-refresh attempt did not invalidate the existing Session 02 materialized one-candidate bundle.

---

## 3. Findings

### F1 — Fresh subject refresh remains blocked

The canonical one-candidate product command still cannot refresh the subject diagnostics because `FRED:DTB3` loading fails. This is the same external live-data blocker recorded in Session 02.

**Status:** blocked.

### F2 — Product orchestration still enters the correct mode

The command prints `Mode: product_one_candidate`, `Runtime mode: product_one_candidate`, and `Workflow state: one_candidate` before the data-layer failure.

**Status:** pass.

### F3 — Current materialized bundle remains usable for contract validation

The live E2E validator still passes on the existing root `Main portfolio/` bundle with `product_one_candidate`.

**Status:** pass, but not proof of fresh subject refresh.

---

## 4. Readiness matrix

| Gate | Status | Notes |
| --- | --- | --- |
| Canonical `run_portfolio_review.py --candidates equal_weight` completes | **BLOCKED** | FRED `DTB3` risk-free loading still times out after `pandas_datareader` compatibility failure. |
| Fresh subject Stress Lab refresh | **NOT PROVEN** | Command fails before fresh `analysis_subject` materialization. |
| Product-one-candidate orchestration mode | **PASS** | Correct mode and workflow state printed before failure. |
| Existing one-candidate live validator | **PASS** | `verify_live_core_e2e.py --profile product_one_candidate` returned OK. |
| Implementation/schema/formula change | **NONE** | Session 03 is documentation/audit only. |

---

## 5. Session 03 closure

Session 03 is closed as a blocker recheck, not as fresh-output closure. It reconfirms that the current blocker is the live FRED risk-free dependency, while the existing one-candidate product bundle remains validator-clean.

Next work should either:

1. resolve the FRED access/dependency path in the data layer with a documented, tested behavior change; or
2. rerun the same fresh-refresh commands when FRED is reachable from the environment.

Do not treat Session 03 as proof that `analysis_subject/stress_report.json` was freshly regenerated.
