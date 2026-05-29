# Blocks 1–3 Diagnostic Foundation — Phase A Closure Audit (Session 06)

Date: 2026-05-29  
Scope: Re-audit after [Blocks 1–3 post-audit development plan](../exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md) Phase A Sessions 01–06 (runtime artifact contract R1–R5).  
Supersedes verdict in: [Blocks 1–3 pre-decision foundation audit](2026-05-29_blocks_1_3_pre_decision_diagnostic_foundation_audit.md).

Operator contract: [runtime_artifact_contract.md](../runtime_artifact_contract.md).

---

## 1. Executive verdict

| Question | Answer |
| --- | --- |
| Are Blocks 1–3 analytics present and test-backed? | **Yes** — unchanged from pre-decision audit; institutional 3.3/3.4 v1 primary. |
| Are three canonical runtime modes operational with predictable artifacts? | **Yes** — live re-run 2026-05-29 on demo `config.yml` / `Main portfolio/`. |
| Does `validate_live_core_artifacts` pass per mode? | **Yes** — `core_blocks_1_3`, `diagnosis_only`, `product_one_candidate` all `ok=True`. |
| Is one-candidate `candidate_comparison.json` product-scoped? | **Yes** — **3** rows (baseline + scoped peers), not 19; `product_candidate_scope.candidate_ids: ["equal_weight"]`. |
| Ready for Decision Workflow (Phase D)? | **Yes** — verdict **`READY_FOR_DECISION_WORKFLOW`**. |

**Bottom line:** Runtime artifact contract gaps R1–R5 from the pre-decision audit are closed. Operators can trust the three canonical CLIs plus `scripts/verify_live_core_e2e.py` on a refreshed tree. Residual P2 items (2.6 `recession_severe` availability vs 3.2, scorecard `block_status: partial`) remain optional polish (ExecPlan Sessions 07–08) and do not block Decision Workflow entry.

---

## 2. Remediation closure (R1–R5)

| ID | Gap (pre-decision) | Session | Closure evidence |
| --- | --- | --- | --- |
| R1 | Core diagnostics timing `KeyError` | 01 | `export_stress_hedge_gap_bridge` in `REPORT_TIMING_BLOCK_KEYS`; `tests/test_report_timing.py` |
| R2 | 19-row `candidate_comparison.json` on one-candidate run | 02 | Product write scoped; `candidate_comparison_registry.json` optional; live: **3** rows, scope `explicit_candidates` |
| R3 | Stale compare/verdict after diagnosis-only | 03 | `apply_diagnosis_only_product_bundle_hygiene` → `no_candidate_v1` tombstones; E2E `diagnosis_only` OK |
| R4 | Core-only left Block 4+ subject JSON | 04 | `apply_core_blocks_product_bundle_hygiene`; E2E `core_blocks_1_3` OK |
| R5 | Live E2E false failures on real workspace | 05 | Profile auto-detect + `--profile`; all three product profiles pass (this audit §3) |

---

## 3. Run mode verification (live, sequential)

Commands on repo `config.yml`, output `Main portfolio/`, 2026-05-29:

| # | Command | Exit | E2E profile (forced) | `validate_live_core_artifacts` |
| --- | --- | ---: | --- | --- |
| 1 | `python run_core_diagnostics.py` | 0 | `core_blocks_1_3` | **OK** |
| 2 | `python run_portfolio_review.py` | 0 | `diagnosis_only` | **OK** (`workflow_state: diagnosis_only`) |
| 3 | `python run_portfolio_review.py --candidates equal_weight` | 0 | `product_one_candidate` | **OK** (`comparison_candidate_count: 3`, `factory_profile_id: explicit_list`, `selected: equal_weight`) |

Auto-detect after step 3: `detected_profile=product_one_candidate`.

---

## 4. Artifact spot-check (after step 3)

| Artifact | Expected (one-candidate) | Observed |
| --- | --- | --- |
| `candidate_comparison.json` | Baseline + selected only | **3** candidates; `product_candidate_scope.excludes_unselected_candidates: true` |
| `current_vs_candidate.json` | `selected_candidate_ids: ["equal_weight"]` | **Pass** |
| `decision_verdict.json` | Present, not tombstone | **Pass** (`decision_verdict_v1`) |
| `candidate_factory_run.json` | `explicit_list` | **Pass** |
| `analysis_subject/portfolio_xray.json` | Blocks 2.1–2.6 | **Pass** (live subject refreshed) |
| `analysis_subject/stress_report.json` | 3.2–3.4 v1 | **Pass** |

---

## 5. Acceptance criteria scorecard (pre-decision §13, re-scored)

| # | Criterion | Pre-decision | Closure |
| --- | --- | --- | --- |
| 1 | Three runtime modes execute | Pass | **Pass** |
| 2 | Core mode = Blocks 1–3 only | Fail (R4) | **Pass** (hygiene + E2E) |
| 3 | No-candidate review = no zoo | Fail (R3) | **Pass** (tombstones + E2E) |
| 4 | EW = one selected candidate | Partial (R2) | **Pass** (scoped comparison + CVC) |
| 5 | `portfolio_xray` 2.1–2.6 | Pass | **Pass** |
| 6 | `stress_report` 3.2–3.4 v1 | Pass | **Pass** |
| 7 | Block 1 cash | Pass | **Pass** |
| 8 | Block 2 consistent | Pass / partial | **Pass** / partial statuses |
| 9 | Block 3 consistent | Pass / partial | **Pass** / partial 3.4 |
| 10 | 3.3/3.4 v1 primary | Pass | **Pass** |
| 11 | PC without stale legacy | Fail (R2) | **Pass** |
| 12 | AI context grounded | Pass | **Pass** |
| 13 | No stale candidates by default | Fail (R2) | **Pass** (product scope) |
| 14 | Documentation matches runtime | Pass | **Pass** ([runtime_artifact_contract.md](../runtime_artifact_contract.md)) |
| 15 | Advanced not Core MVP | Pass | **Pass** |
| 16 | Semantic contradictions | Pass (moderate note) | **Pass** (unchanged moderate 2.6/3.2 note) |
| 17 | Tests pass | Pass | **Pass** (261 passed, 1 skipped — §6) |
| 18 | Clear final verdict | NOT_READY | **`READY_FOR_DECISION_WORKFLOW`** (this document) |

---

## 6. Test results

**Focused Blocks 1–3 bundle** (pre-decision §11 + Session 01–05 regressions):

```bash
python -m pytest tests/test_mvp_input_defaults.py tests/test_input_assumptions.py \
  tests/test_portfolio_xray_contract.py tests/test_block_2_4_hidden_exposure.py \
  tests/test_block_2_6_portfolio_weakness_map.py tests/test_hedge_gap_analysis_v1_contract.py \
  tests/test_current_portfolio_stress_scorecard_v1_contract.py tests/test_problem_classification.py \
  tests/test_ai_commentary_context.py tests/test_live_core_e2e_validation.py \
  tests/test_core_mvp_blocks_1_3_fixture_matrix.py tests/test_core_diagnostics_entrypoint.py \
  tests/test_report_timing.py tests/test_product_bundle_hygiene.py \
  tests/test_runtime_mode_regression_boundaries.py -q
```

**Result:** **261 passed**, **1 skipped**, 0 failed (~129 s).

**Operator gate:**

```bash
python scripts/verify_live_core_e2e.py
python scripts/verify_live_core_e2e.py --profile diagnosis_only
python scripts/verify_live_core_e2e.py --profile product_one_candidate
```

All **OK** on this audit date after §3 live runs.

---

## 7. Residual (non-blocking)

| ID | Item | Status |
| --- | --- | --- |
| R6 | 2.6 `recession_severe` Unavailable vs 3.2 worst case | Open — ExecPlan Sessions 07–08 (optional) |
| R7 | Scorecard `block_status: partial` on demo | Open — documentation / data polish |
| R8 | Historical dotcom/2008 empty (2014+ panel) | Accepted data-policy disclosure |

---

## 8. Final readiness verdict

### `READY_FOR_DECISION_WORKFLOW`

**Rationale:** Analytical Blocks 1–3 remain implementated and test-green. Runtime artifact scope now matches [runtime_artifact_contract.md](../runtime_artifact_contract.md) for all three canonical CLIs; live E2E validation passes per profile; product `candidate_comparison.json` is scoped for `explicit_list` runs.

**Recommended next step:** Start ExecPlan Phase D (Decision workflow, Sessions 09–12) or product UX work that consumes Problem Classification → Launchpad → Current vs Candidate → Decision Verdict on a refreshed tree.

---

## 9. Session evidence log

| Category | Detail |
| --- | --- |
| **Audited** | R1–R5 closure, acceptance criteria 1–18, three CLI modes, live E2E profiles |
| **Live runs** | `run_core_diagnostics.py`, `run_portfolio_review.py`, `run_portfolio_review.py --candidates equal_weight` (2026-05-29) |
| **Key paths** | `Main portfolio/analysis_subject/{portfolio_xray,stress_report}.json`, `Main portfolio/{candidate_comparison,current_vs_candidate,decision_verdict,candidate_factory_run}.json` |
| **Decision** | `DEC-2026-05-29-010` |

---

## 10. Audit register

| Date | Audit | Status |
| --- | --- | --- |
| 2026-05-29 | Blocks 1–3 Foundation Closure (this document) | **Active closure** |
| 2026-05-29 | [Blocks 1–3 Pre-Decision Diagnostic Foundation](2026-05-29_blocks_1_3_pre_decision_diagnostic_foundation_audit.md) | **Superseded** by this closure |
