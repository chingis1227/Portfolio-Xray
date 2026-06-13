# Block 4 v2 Session 00 — Current Artifacts and Contract Gap Audit

Date: 2026-05-29  
ExecPlan: [Block 4 v2 Evidence-to-Problem Translation](../exec_plans/2026-05-29_block_4_v2_evidence_to_problem_plan.md) Session 00  
Prerequisite: [Block 4 Session 09 — Problem Classification + Launchpad](2026-05-29_block_4_session_09_problem_classification_launchpad.md) (`ACCEPTED` for V1 entry)  
Target architecture: Block 4 v2 plan (Evidence Extraction → Scoring → Severity/Confidence → Prioritization → Actions → Launchpad)

---

## 1. Executive summary

| Question | Verdict |
| --- | --- |
| Is Block 4 entry implemented today... | **Yes (V1)** — `problem_classification_v1` + `candidate_launchpad_v1` in [`src/problem_classification.py`](../../src/problem_classification.py), [`src/candidate_launchpad.py`](../../src/candidate_launchpad.py). |
| Is V1 sufficient for target product architecture... | **No** — thin rule layer; legacy `sections.*` readers; 9 problem IDs; severity-only sort; no evidence extraction module, rejected problems, no-trade gate, or rich `evidence_refs`. |
| Are Blocks 2–3 product blocks ready as evidence sources... | **Yes** — `block_2_1` … `block_2_6` on `portfolio_xray.json`; `hedge_gap_analysis_v1` + `current_portfolio_stress_scorecard_v1` on `stress_report.json` (foundation closure `READY_FOR_DECISION_WORKFLOW`). |
| Recommended V2 migration strategy... | **Additive schema bump** — `problem_classification_v2` / `candidate_launchpad_v2` with dual-write adapter during Sessions 10–13; keep V1 contract validators until Session 14 freeze. |
| Session 00 gate | **PASS** — gap matrix complete; backward-compat decision recorded; pytest baseline captured. |

**Bottom line:** V1 is a valid **decision-entry stub** accepted in Session 09. V2 must replace the monolithic collector with an auditable pipeline without changing Blocks 2–3 formulas or Candidate Factory behavior.

---

## 2. Scope boundary (what Session 00 audited)

### In scope

- Block 4 **entry layer**: Problem Classification + Candidate Launchpad bridge.
- Evidence **read paths** from Blocks 2.1–2.6 and 3.3–3.4.
- V1 output contracts vs V2 target contracts.
- Runtime artifact placement ([`docs/runtime_artifact_contract.md`](../runtime_artifact_contract.md)).
- Product contract enforcement ([`scripts/core_mvp_validation_contract.py`](../../scripts/core_mvp_validation_contract.py)).

### Out of scope (explicitly not Block 4 entry)

| Area | Location | Why excluded |
| --- | --- | --- |
| Candidate Portfolio Factory 4.1–4.9 | `run_candidate_factory.py`, `src/candidate_factory.py` | Builds weights/artifacts after user selects a hypothesis |
| Portfolio Alternatives Builder execution | `src/portfolio_alternatives_builder.py` | Plan/delegation only; not diagnosis |
| Current vs Candidate / Decision Verdict | Block 5 adapters | Requires compare run |
| LLM commentary generation | `ai_commentary_context.json` grounding only | Explains JSON; must not write diagnosis |
| Optimizer / stress formula changes | Blocks 2–3 builders | Block 4 is read-only translation |

---

## 3. Current V1 implementation inventory

### 3.1 Writers and workflow

| Component | Path | When written |
| --- | --- | --- |
| Problem Classification | `src/problem_classification.py` | `run_report.py` when `not core_blocks_only` (~L2478) |
| Candidate Launchpad | `src/candidate_launchpad.py` | After PC, same gate |
| Core-only hygiene | `src/product_bundle_hygiene.py` | Removes PC + Launchpad from `analysis_subject/` |

**Modes:**

| CLI | `problem_classification.json` | `candidate_launchpad.json` |
| --- | --- | --- |
| `run_core_diagnostics.py` | Absent (pruned) | Absent (pruned) |
| `run_portfolio_review.py` (diagnosis) | Required | Required |
| `run_portfolio_review.py --candidates <id>` | Required | Required |

### 3.2 V1 problem taxonomy (9 IDs)

From [`PROBLEM_CLASSIFICATION_V1_IDS`](../../scripts/core_mvp_validation_contract.py) and [`src/problem_classification.py`](../../src/problem_classification.py):

| V1 `problem_id` | V2 target `problem_id` | Notes |
| --- | --- | --- |
| `high_drawdown_risk` | `high_drawdown` | Rename for consistency |
| `high_volatility` | `high_volatility` | Keep |
| `high_concentration` | `high_concentration` | Keep |
| `poor_diversification` | `poor_diversification` | Keep |
| `weak_hedge_behavior` | `weak_hedge_behavior` | Keep |
| `weak_crisis_resilience` | `weak_crisis_resilience` | Keep |
| `high_equity_beta` | `high_equity_beta` | Keep |
| `data_review_required` | `evidence_insufficient_data_quality` | Split + rename |
| `current_portfolio_acceptable` | `current_portfolio_acceptable` | Keep |

**V2 additions (not in V1):** `poor_rates_up_behavior`, `duration_rates_vulnerability`, `high_tail_risk`, `credit_liquidity_fragility`, `low_return_risk_efficiency`, `evidence_insufficient_conflicting_signals`.

### 3.3 V1 collectors (evidence sources actually read)

| Collector | Source artifact | Source path | Problems triggered |
| --- | --- | --- | --- |
| `_collect_block_2_6_weakness_map` | `portfolio_xray.json` | `block_2_6_portfolio_weakness_map.risk_types[]` | Mapped via `BLOCK_2_6_RISK_TYPE_TO_PROBLEM_IDS` |
| `_collect_allocation` | `portfolio_xray.json` | **`sections.asset_allocation`** (legacy) | `high_concentration` (substring "concentration") |
| `_collect_risk_metrics` | `portfolio_xray.json` | **`sections.risk_diagnostics`** (legacy) | `high_volatility` (vol ≥ 0.18), `high_drawdown_risk` (|DD| ≥ 0.15) |
| `_collect_factor_exposure` | `portfolio_xray.json` | **`sections.factor_exposure`** (legacy) | `high_equity_beta` (beta ≥ 0.8) |
| `_collect_data_review` | `portfolio_xray.json` | **`sections.*` status partial/unavailable** | `data_review_required` (≥3 sections) |
| `_collect_hedge_gap_v1` | `stress_report.json` | `hedge_gap_analysis_v1.summary` + `by_risk_type[]` | `weak_hedge_behavior` |
| `_collect_hedge_gap_legacy_fallback` | `stress_report.json` | `stress_conclusions.hedge_gap_status` | `weak_hedge_behavior` |
| `_collect_stress_scorecard_v1` | `stress_report.json` | `current_portfolio_stress_scorecard_v1` worst selectors | `weak_crisis_resilience`, `high_drawdown_risk` |
| `_collect_stress_legacy` | `stress_report.json` | `stress_conclusions`, `stress_scorecard_v1` | Same + mandate rollup |
| `_collect_stress_scorecard_v1_status_hooks` | `stress_report.json` | report `status`, legacy mandate | `weak_crisis_resilience` |

**Not read by V1 (product blocks available but unused):**

- `block_2_1_asset_allocation` (concentration flags, duplicate exposure, dominant dimensions)
- `block_2_2_portfolio_metrics` (vol, drawdown, VaR/ES, Sharpe, Sortino, beta)
- `block_2_3_factor_exposure` (factor betas, confidence, variance contribution)
- `block_2_4_hidden_exposure` (six alert statuses — only referenced in hedge-gap bridge metadata)
- `block_2_5_risk_budget_view` (RC top contributors, weight vs RC gap)
- Block 3.4 `pre_stress_confirmation_summary` (confirmation tier for prioritization)
- Block 3.4 `stress_diagnosis`, `hedge_gap_summary` (narrative hints only partially via signals)

### 3.4 V1 prioritization

```python
# src/problem_classification.py — build_problem_classification()
top = sorted(problems.values(), key=lambda row: (-severity_score, problem_id))[:3]
primary = top[0]  # highest severity only
```

**Gaps:** No decision_score, no root-cause elevation, no rejected list, no materiality floor, no confidence-based no-trade.

### 3.5 V1 Launchpad

| Feature | V1 status |
| --- | --- |
| Cards from `reasonable_paths_to_test` | Implemented |
| `GOAL_TO_METHODS` mapping | 9 goals; `Improve return/risk balance` not in PC paths |
| Max cards | Unbounded (dedupe by goal only) |
| `default_method`, trade-offs, skip rules | **Missing** |
| `no_trade_or_monitoring_view` | **Missing** |
| Launchpad → Factory wiring in review workflow | **Missing** (manual `run_one_candidate_from_method.py` or `--candidates`) |

### 3.6 V1 evidence shape

Flat objects per problem in `evidence[]`:

```json
{
  "source_artifact": "stress_report.json",
  "source_section": "hedge_gap_analysis_v1",
  "source_field": "summary.main_hedge_gap",
  "protection_profile": "mostly_weak_protection",
  "main_hedge_gap_offset_coverage_ratio": 0.0
}
```

**Gaps vs V2 `evidence_refs`:** no `evidence_id`, `signal`, `normalized_score`, `interpretation_en`, `why_relevant_to_problem_en`, `linked_assets`, `limitation_en`, confirmation tier.

---

## 4. Evidence source field matrix (Blocks 2–3 → V2)

Legend: **V1** = used today | **V2** = planned Session 03+ | **—** = not applicable

### 4.1 Block 2.1 — `block_2_1_asset_allocation`

| Signal / field | V1 | V2 target problem(s) | Session |
| --- | --- | --- | --- |
| `concentration_snapshot.top1_holding.weight_pct` | — | `high_concentration` | 03 |
| `concentration_snapshot.top3_weight` | — | `high_concentration` | 03 |
| `concentration_flags[]` (top1/top3/dominant class) | — | `high_concentration`, `poor_diversification` | 03 |
| `duplicate_exposure_flags[]` | — | `poor_diversification` | 03 |
| `dominant_asset_class` / region / currency | — | supporting evidence | 03 |
| `capital_allocation_breakdown.by_asset[]` | — | `linked_assets` | 03 |
| Legacy `sections.asset_allocation` text scan | V1 | **Deprecate** (fallback only) | 04 |

### 4.2 Block 2.2 — `block_2_2_portfolio_metrics`

| Signal / field | V1 | V2 target problem(s) | Session |
| --- | --- | --- | --- |
| `windows.primary.metrics.vol_annual` | V1 via legacy | `high_volatility` | 03 |
| `windows.primary.metrics.max_drawdown` | V1 via legacy | `high_drawdown` | 03 |
| `windows.primary.metrics.sharpe` / `sortino` | — | `low_return_risk_efficiency` | 03 |
| `windows.primary.metrics.beta_portfolio` | — | `high_equity_beta` (cross-check 2.3) | 03 |
| `tail_risk.var_95` / `es_95` / `es_99` | — | `high_tail_risk` | 03 |
| `drawdown_structure.time_underwater` | — | `high_drawdown` supporting | 03 |
| `rolling_metrics.*` | — | confidence / regime context only | 03 |
| Legacy `sections.risk_diagnostics` | V1 | **Deprecate** primary | 04 |

### 4.3 Block 2.3 — `block_2_3_factor_exposure`

| Signal / field | V1 | V2 target problem(s) | Session |
| --- | --- | --- | --- |
| `factor_betas_5y.beta_eq` / `beta_rr` / `beta_credit` | V1 via legacy item | `high_equity_beta`, rates, credit | 03 |
| `factor_signal_confidence` | — | confidence layer | 05 |
| `factor_beta_stability` | — | confidence penalty | 05 |
| `variance_contribution.top_drivers[]` | — | diversification / factor concentration | 03 |
| `factor_kalman_uncertainty` | — | confidence only | 05 |
| Legacy `sections.factor_exposure` | V1 | **Deprecate** primary | 04 |

### 4.4 Block 2.4 — `block_2_4_hidden_exposure`

| Alert id | V1 | V2 target problem(s) | Session |
| --- | --- | --- | --- |
| `hidden_equity_beta` | — (bridge meta only) | `high_equity_beta` | 03 |
| `duration_concentration` | — | `duration_rates_vulnerability` | 03 |
| `credit_liquidity_risk` | — | `credit_liquidity_fragility` | 03 |
| `correlation_concentration` | — | `poor_diversification` | 03 |
| `weak_hedge_behavior` | — | `weak_hedge_behavior` (pre-stress) | 03 |
| `tail_risk` | — | `high_tail_risk` | 03 |
| `contributing_assets[]` | — | `evidence_refs.linked_assets` | 03 |
| `confirmation_status` (per alert) | — | confirmation tier | 05 |

### 4.5 Block 2.5 — `block_2_5_risk_budget_view`

| Signal / field | V1 | V2 target problem(s) | Session |
| --- | --- | --- | --- |
| `rc_concentration.top1_share` / `top3_share` | — | `high_concentration`, `poor_diversification` | 03 |
| `top_risk_overweight_assets[]` | — | `high_concentration` | 03 |
| `top_risk_underweight_assets[]` | — | supporting | 03 |
| `risk_budget_by_bucket[]` | — | bucket imbalance hints | 03 |
| `weight_vs_rc_gap_table[]` | — | weight vs risk gap | 03 |

### 4.6 Block 2.6 — `block_2_6_portfolio_weakness_map`

| `risk_type` | V1 map | V2 target problem(s) | Session |
| --- | --- | --- | --- |
| `equity_shock` | `high_equity_beta`, `weak_crisis_resilience` | same + pre-stress cap | 03 |
| `credit_shock` | `weak_crisis_resilience` | + `credit_liquidity_fragility` | 04 |
| `rates_shock` | `high_drawdown_risk` | `poor_rates_up_behavior`, `duration_rates_vulnerability` | 04 |
| `inflation_stagflation` | `weak_crisis_resilience` | same | 03 |
| `liquidity_shock` | `poor_diversification`, `weak_crisis_resilience` | + `credit_liquidity_fragility` | 04 |
| `usd_shock` | `weak_crisis_resilience` | supporting | 03 |
| `commodity_shock` | `weak_crisis_resilience` | supporting | 03 |
| `recession_severe` | `weak_crisis_resilience`, `high_drawdown_risk` | same | 03 |

Per-row fields used V1: `severity`, `score_0_100`, `confidence`, `short_diagnosis`.  
V2 adds: confirmation tier from Block 3.4 bridges.

### 4.7 Block 3.3 — `hedge_gap_analysis_v1`

| Signal / field | V1 | V2 target problem(s) | Session |
| --- | --- | --- | --- |
| `summary.protection_profile` | V1 | `weak_hedge_behavior` | 03 |
| `summary.main_hedge_gap.offset_coverage_ratio` | V1 | `weak_hedge_behavior`, `weak_crisis_resilience` | 03 |
| `summary.main_hedge_gap.protection_status` | V1 | same | 03 |
| `summary.main_hedge_gap.portfolio_loss_pct` | V1 | severity magnitude | 05 |
| `by_risk_type[]` weak row count | V1 | same | 03 |
| `hidden_exposure_confirmation[]` | — | confidence boost | 05 |
| `weakness_map_confirmation[]` | — | confirmation tier | 05 |
| Legacy `stress_conclusions.hedge_gap_status` | V1 fallback | same | 03 |

### 4.8 Block 3.4 — `current_portfolio_stress_scorecard_v1`

| Signal / field | V1 | V2 target problem(s) | Session |
| --- | --- | --- | --- |
| `worst_synthetic_scenario.portfolio_loss_pct` | V1 | `weak_crisis_resilience` | 03 |
| `worst_historical_scenario.drawdown_pct` | V1 | `high_drawdown` | 03 |
| `problem_classification_signals.stress_severity` | V1 (implicit) | severity input | 05 |
| `problem_classification_signals.diagnosis_confidence` | V1 | confidence input | 05 |
| `pre_stress_confirmation_summary` | — | prioritization / confidence | 06 |
| `stress_diagnosis.headline_en` | — | `short_diagnosis_en` copy | 07 |
| `hedge_gap_summary` | — | hedge problems | 03 |
| Legacy stress paths | V1 fallback | same | 03 |

---

## 5. V1 vs V2 contract gap summary

| Capability | V1 | V2 target |
| --- | --- | --- |
| `schema_version` | `problem_classification_v1` | `problem_classification_v2` |
| Primary problem object | First row in `problems[]` | Explicit `primary_problem` + `secondary_problems[]` |
| Rejected problems | No | `rejected_problems[]` with `reject_reason` |
| Evidence | Flat `evidence[]` | Structured `evidence_refs[]` + `negative_evidence_refs[]` |
| Severity values | `low`, `moderate`, `high`, `unknown` | `Low`, `Medium`, `High`, `Unavailable` (normalize at export) |
| Confidence | Merged min across collectors | Separate classifier with documented formula |
| Prioritization | Severity sort | `decision_score` + root-cause rules |
| Suggested actions | `reasonable_paths_to_test` strings | `suggested_action_path_id` enum + top-level `suggested_actions[]` |
| No-trade | Implicit (`current_portfolio_acceptable`) | Explicit `no_trade_or_monitoring_view` |
| Launchpad cards | Basic goal + methods | Full card contract (trade-off, skip, default_method) |
| Product block readers | Mostly legacy `sections.*` | Canonical `block_2_*` primary |
| Ruleset versioning | None | `ruleset_version: block_4_v2_2026_06` |
| Configurable thresholds | Hardcoded in collectors | `config/block_4_thresholds.yml` |

---

## 6. Backward compatibility decision

**Decision (Session 00):** `DEC-2026-05-29-013` — **Additive V2 with transitional dual validation**

1. **Schema bump:** Write `schema_version: problem_classification_v2` when V2 pipeline ships (Session 10+).
2. **Transitional adapter (Sessions 10–13):** Emit compatibility shim:
   - Keep flat `problems[]` = `[primary_problem] + secondary_problems` (max 3) for UI/tools still on V1 shape.
   - Map V2 severity `Medium` → V1 `moderate` in shim if needed.
   - Map `high_drawdown` → legacy readers expecting `high_drawdown_risk` via alias field `problem_id_legacy` (optional, Session 01 spec).
3. **Contract validators:** Add `check_problem_classification_v2` alongside V1; live E2E switches to V2 at Session 12; remove V1 checks at Session 14 freeze.
4. **Filename unchanged:** Still `problem_classification.json` and `candidate_launchpad.json` under `analysis_subject/` (no new bundle file in Core MVP six-file set).
5. **Core-only hygiene unchanged:** Block 4 artifacts remain absent on `run_core_diagnostics.py`.
6. **No Candidate Factory changes** until Launchpad bridge session (post–Block 4 v2 freeze, separate ExecPlan item).

Rationale: Session 09 acceptance of V1 must not block V2 depth; operators and E2E need a predictable migration window.

---

## 7. Downstream integration gaps (documented, not Session 00 scope)

| Gap | Owner session | Notes |
| --- | --- | --- |
| Launchpad card → `portfolio_alternatives_builder` in review workflow | Post–v2 freeze | `scripts/run_one_candidate_from_method.py --run` exists |
| `../../diagnostic_journey/view_model.py` field mismatch | Session 13 | Reads `candidate_methods` vs `suggested_methods` |
| No persisted `selected_card_id` artifact | Future UX | Between Launchpad and Factory |
| `Improve return/risk balance` goal orphan | Session 07 | In Launchpad but not PC paths |

---

## 8. Verification baseline (Session 00)

```bash
python -m pytest tests/test_problem_classification.py \
  tests/test_candidate_launchpad.py \
  tests/test_block_4_decision_entry_contract.py -q
```

**Result (2026-05-29):** **20 passed** in 34.31s.

**Live artifacts:** No `analysis_subject/` on disk in this workspace at audit time. Re-verify after `python run_portfolio_review.py` in Session 12.

**Existing contract enforcement:**

- `problem_classification_v1_product_contract_violations`
- `candidate_launchpad_v1_product_contract_violations`
- `block_4_diagnosis_handoff_violations`
- Live E2E: `_validate_block_4_subject_bundle` in `src/live_core_e2e.py`

---

## 9. Session 00 acceptance checklist

| Criterion | Status |
| --- | --- |
| Block 2.1–2.6 fields mapped (used / unused / V2 planned) | **Done** §4 |
| Block 3.3–3.4 fields mapped | **Done** §4.7–4.8 |
| V1 collectors documented | **Done** §3.3 |
| V2 gap list complete | **Done** §5 |
| Backward-compat decision recorded | **Done** §6 |
| Pytest baseline captured | **Done** §8 |
| Block 4 vs Factory boundary explicit | **Done** §2 |

**Session 00 verdict:** **PASS** — ready for Session 01 (V2 output contract spec) + Session 02 (problem taxonomy registry).

---

## 10. Evidence log

| Category | Detail |
| --- | --- |
| Code | `src/problem_classification.py`, `src/candidate_launchpad.py`, `scripts/core_mvp_validation_contract.py`, `run_report.py` |
| Specs | `docs/specs/problem_classification_spec.md`, `candidate_launchpad_spec.md`, `portfolio_xray_diagnostics_spec.md`, `hedge_gap_analysis_spec.md`, `current_portfolio_stress_scorecard_spec.md` |
| Prior audit | `docs/audits/2026-05-29_block_4_session_09_problem_classification_launchpad.md` |
| Decision | `DEC-2026-05-29-013` (§6) |
