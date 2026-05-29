# Block 3.4 Current Portfolio Stress Scorecard — Institutional Upgrade (Phase 2)

**Status: Completed** — Session 13 closed 2026-05-29. Evidence: [institutional upgrade acceptance audit](../audits/2026-05-29_block_3_4_institutional_upgrade_acceptance_audit.md).

Baseline: [Session 00 baseline audit](../audits/2026-05-29_block_3_4_session_00_baseline_audit.md).  
Contract: [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md) (frozen Session 01).

v1 origin: [Block 3.4 Current Portfolio Stress Scorecard MVP](2026-05-27_block_3_4_current_portfolio_stress_scorecard_plan.md) (**Completed** 2026-05-27).

Prerequisites: Block 3.2 `stress_results_v1` (**Completed**); Block 3.3 institutional `hedge_gap_analysis_v1` (**Completed** 2026-05-29).

This ExecPlan follows [PLANS.md](../../PLANS.md). Update `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` at each session stop.

## Purpose / Big Picture

Block 3.4 is the **executive stress diagnosis layer** inside Stress Test Lab. It answers ten product questions by **reading** Blocks 3.1–3.3 and optional 2.4/2.6 context—never by re-running stress.

After closure, `stress_report.json` → `current_portfolio_stress_scorecard_v1` carries a frozen v1.1 contract; Problem Classification, Candidate Comparison, and AI Commentary cite this key first; legacy `stress_scorecard_v1` remains only as explicit fallback.

Verify after full closure:

```bash
python run_portfolio_review.py --skip-candidates
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py \
  tests/test_problem_classification.py tests/test_ai_commentary_context.py \
  tests/test_stress_downstream_integration.py tests/test_live_core_e2e_validation.py -q
```

## Architecture boundary (hard)

Block 3.4 is a read-only adapter over Blocks **3.1–3.3** stress evidence.

**Must not:** recompute scenarios; mutate `stress_results_v1` / `hedge_gap_analysis_v1`; optimize; generate candidates; **create mandate pass/fail inside Core MVP 3.4**; use legacy `hedge_gap_analysis` when v1 exists; import 3.4 from 2.4/2.6; use wording such as “passes normally”.

**Must:** deterministic adapter; compact Pareto-level fields; `legacy_fallback_used` as explicit boolean; separate loss contribution vs RC_vol; `stress_diagnosis.diagnosis_confidence` (`high` | `medium` | `low` | `unavailable`).

**Mandate boundary:** Block 3.4 may **summarize** pass/fail only when a **separate mandate layer** (e.g. legacy `stress_scorecard_v1` under `loss_gate_mode=mandate`) already provides it; Core MVP `current_portfolio_stress_scorecard_v1` must **not** compute or emit mandate pass/fail internally.

**Product language:** use `relatively_resilient_scenarios`, `less_damaging_scenarios`, `protection_status`, loss severity / offset coverage — not “passes normally” or mandate-style pass/fail.

**Optional 2.4 / 2.6 graceful degradation:** If Block 2.4 or 2.6 context is unavailable at attach time, Block 3.4 **must still run**. Set `pre_stress_confirmation_summary` sub-blocks to `unavailable` / `not_applicable`; derive `block_status` from stress data (3.1–3.3) only.

**Worst scenario rules (read from Block 3.2 envelope):** worst synthetic = min `portfolio_pnl_pct` / `portfolio_loss_pct`; worst historical = min `max_dd` — never mix synthetic PnL with historical drawdown.

**Ruleset target:** `current_portfolio_stress_scorecard_rules_v1_1` (frozen Session 01–02).

## Progress

- [x] (2026-05-29) Plan checked in; README **Active** pointer set
- [x] (2026-05-29) **Session 00 — Baseline audit** → [audit](../audits/2026-05-29_block_3_4_session_00_baseline_audit.md); pytest **4 passed**
- [x] (2026-05-29) **Session 01 — Contract spec v1.1 freeze** → [audit](../audits/2026-05-29_block_3_4_session_01_contract_v1_1.md); spec [current_portfolio_stress_scorecard_spec.md](../specs/current_portfolio_stress_scorecard_spec.md); pytest **4 passed** (no code changes)
- [x] (2026-05-29) **Session 02 — Product metadata + contract tests** → [audit](../audits/2026-05-29_block_3_4_session_02_product_metadata_contract_tests.md); pytest **10 passed**
- [x] (2026-05-29) **Session 03 — Worst scenario logic hardening + stress_coverage** → [audit](../audits/2026-05-29_block_3_4_session_03_worst_scenario_stress_coverage.md); pytest **15 passed**
- [x] (2026-05-29) **Session 04 — Loss + risk contribution summaries** → [audit](../audits/2026-05-29_block_3_4_session_04_loss_risk_summaries.md); pytest **20 passed**
- [x] (2026-05-29) **Session 05 — Factor attribution + hedge_gap_summary** → [audit](../audits/2026-05-29_block_3_4_session_05_hedge_gap_summary.md); pytest **25 passed**
- [x] (2026-05-29) **Session 06 — stress_diagnosis + next_decision_uses[]** → [audit](../audits/2026-05-29_block_3_4_session_06_stress_diagnosis.md); pytest **31 passed**
- [x] (2026-05-29) **Session 07 — Pre-stress confirmation bridge** → [audit](../audits/2026-05-29_block_3_4_session_07_pre_stress_confirmation.md); pytest **34 passed**
- [x] (2026-05-29) **Session 08 — problem_classification_signals + PC migration** → [audit](../audits/2026-05-29_block_3_4_session_08_problem_classification.md); pytest **46 passed**
- [x] (2026-05-29) **Session 09 — candidate_comparison_targets + CC migration** → [audit](../audits/2026-05-29_block_3_4_session_09_candidate_comparison.md); pytest **47 passed**
- [x] (2026-05-29) **Session 10 — AI Commentary grounding** → [audit](../audits/2026-05-29_block_3_4_session_10_ai_commentary.md); pytest **67 passed** (closure bundle)
- [x] (2026-05-29) **Session 11 — Materialization + E2E validators + live-output gates** → [audit](../audits/2026-05-29_block_3_4_session_11_materialization.md); pytest **71 passed** (closure bundle)
- [x] (2026-05-29) **Session 12 — Documentation sync** → [audit](../audits/2026-05-29_block_3_4_session_12_documentation_sync.md); `verify_docs` OK; pytest **71 passed** (doc-sync bundle)
- [x] (2026-05-29) **Session 13 — Acceptance audit + plan closure** → [acceptance audit](../audits/2026-05-29_block_3_4_institutional_upgrade_acceptance_audit.md); fixture matrix **7/7**; pytest **67** (closure) / **142** (extended); ExecPlan **Completed**

## Surprises & Discoveries

### Session 13 (2026-05-29)

- Observation: Acceptance closed test/fixture locked without committed `analysis_subject/stress_report.json`; Block 3 matrix **7/7** includes `current_portfolio_stress_scorecard_v1` validation.
  Evidence: [acceptance audit](../audits/2026-05-29_block_3_4_institutional_upgrade_acceptance_audit.md) §6.

### Session 12 (2026-05-29)

- Observation: Top-level SPEC/OUTPUTS still described Block 3.4 v1.1 as “rolling out” through Session 11 despite Sessions 02–11 code closure; Session 12 aligned status to **Implemented** without code changes.
  Evidence: [Session 12 audit](../audits/2026-05-29_block_3_4_session_12_documentation_sync.md); `DEC-2026-05-29-005`.

### Session 11 (2026-05-29)

- Observation: `validate_live_core_artifacts` now requires `current_portfolio_stress_scorecard_v1` and runs `check_current_portfolio_stress_scorecard_v1` (live-output gates when `block_status` ∈ `{ok, partial}`).
  Evidence: `tests/test_stress_scorecard_materialization.py`; offline smoke scorecard may remain `unavailable` without failing structural contract.

- Observation: `snapshot_10y.stress_suite_results.current_portfolio_stress_scorecard_v1` mirrors compact Block 3.4 fields (diagnosis, worst selectors, hedge-gap summary, `next_decision_uses`).
  Evidence: `test_snapshot_scorecard_v1_mirror_includes_institutional_fields`.

### Session 10 (2026-05-29)

- Observation: `ai_commentary_context.json` cites Block 3.4 `stress_diagnosis` paths when v1 is present; legacy `stress_scorecard_v1.overall_status` is omitted from evidence refs.
  Evidence: `test_ai_commentary_context_scorecard_v1_primary`.

- Observation: `stress_commentary.txt` executive summary uses Block 3.4 headline and does not print legacy `overall_status` when v1 is attached.
  Evidence: `test_write_stress_commentary_prefers_scorecard_v1_over_legacy`.

### Session 09 (2026-05-29)

- Observation: Candidate Comparison sets `stress.scorecard` only when Block 3.4 is missing; v1 path exposes `stress.current_portfolio_stress_scorecard_v1` and `stress_scorecard_source`.
  Evidence: `test_stress_from_artifacts_legacy_scorecard_when_v1_missing`.

- Observation: `stress_scorecard_comparison` pairwise uses `worst_synthetic_loss_pct_delta`; offset delta only when both peers have `compare_offset_coverage`.
  Evidence: `test_build_candidate_comparison_emits_stress_scorecard_comparison`.

### Session 08 (2026-05-29)

- Observation: Problem Classification reads worst scenarios from Block 3.4 selectors when `block_status` is ok/partial; legacy `stress_conclusions` ids are ignored on the same report.
  Evidence: `test_problem_classification_scorecard_v1_ignores_legacy_worst_conclusions`.

- Observation: Mandate `overall_status` rollup remains on legacy `stress_scorecard_v1` even when Block 3.4 is primary (`evidence_path: legacy_mandate_rollup`).
  Evidence: `_collect_stress_scorecard_v1_status_hooks`.

### Session 07 (2026-05-29)

- Observation: Scorecard must be re-attached after `build_portfolio_xray_v2` so exported `stress_report.json` carries populated `pre_stress_confirmation_summary` confirmation rows.
  Evidence: `run_report.py` refresh before `export_stress_report`.

- Observation: Missing Block 2.4/2.6 bridges do not downgrade `block_status`; only `pre_stress_confirmation_summary` sub-blocks become `not_applicable`.
  Evidence: `test_block_status_independent_of_pre_stress_bridges`.

### Session 06 (2026-05-29)

- Observation: Resilience lists read only `stress_results_v1.synthetic_scenarios[]` rows with `availability=available`; non-library scenario ids in raw 3.1 evidence are ignored by Block 3.2 row lists.
  Evidence: `test_relatively_resilient_and_less_damaging_scenarios` (canonical `SYNTHETIC_SCENARIO_IDS`).

- Observation: `diagnosis_summary_en` top-level alias now mirrors `stress_diagnosis.diagnosis_summary_en` on every build.
  Evidence: `test_stress_diagnosis_present_on_minimal_run`.

### Session 05 (2026-05-29)

- Observation: `hedge_gap_summary` copies Block 3.3 summary/meta only; when main gap is missing but v1 block exists, meta fields (`hedge_gap_block_status`, etc.) still surface with `availability=unavailable`.
  Evidence: `test_hedge_gap_summary_unavailable_when_main_gap_missing`.

- Observation: Factor drivers fall back to worst synthetic row `factor_attribution` when envelope `top_factor_drivers` is empty.
  Evidence: `test_factor_stress_attribution_falls_back_to_synthetic_row`.

### Session 04 (2026-05-29)

- Observation: `loss_concentration_top3_share` uses Block 3.2 row `loss_contribution.pnl_by_asset_pct` for gross loss; omitted when only envelope top-3 exists without per-asset map.
  Evidence: `test_loss_concentration_top3_share_computed_from_pnl_by_asset`.

- Observation: `rc_overlap_with_loss_contributors` is emitted only when RC and synthetic loss top-3 are both available; omitted when RC block is unavailable.
  Evidence: `test_rc_overlap_omitted_when_rc_unavailable`.

### Session 03 (2026-05-29)

- Observation: `stress_coverage` uses scenario-library totals when row lists are empty (`fraction_*` is `0.0` when total > 0 and none available, not `null`).
  Evidence: `test_stress_coverage_uses_scenario_library_when_row_lists_empty`.

- Observation: Worst selectors expose frozen `selection_metric` / `selection_source`; envelope drift vs row lists surfaces as `limitations` without recomputing worst ids in Block 3.4.
  Evidence: `test_worst_selector_consistency_limitation_on_envelope_drift`.

### Session 02 (2026-05-29)

- Observation: Worst-selector builders now require non-null `scenario_id` / `episode` so empty Block 3.2 envelopes correctly yield `block_status=unavailable` instead of false `available`.
  Evidence: `test_block_status_unavailable_when_stress_results_missing`.

### Session 01 (2026-05-29)

- Observation: No dedicated scorecard spec existed before Session 01; `stress_lab_layer_spec.md` §3.4 was the only index. Phase 2 contract is now owned by `current_portfolio_stress_scorecard_spec.md` with explicit MVP vs v1.1 session matrix.
  Evidence: Session 01 audit; G13 closed in baseline gap list.

### Session 00 (2026-05-29)

- Observation: Committed `Main portfolio/analysis_subject/stress_report.json` (`generated_at` 2026-05-29T12:56:19) has MVP Block 3.4 but **no** v1.1 fields (`block_status`, `stress_diagnosis`, `legacy_fallback_used`); `hedge_gap_analysis_v1` on the same file lacks `block_status` / `ruleset_version` (pre–Phase 2 3.3 shape on disk).
  Evidence: Session 00 audit §6; refresh subject stress after upstream sessions before closure live gates.

- Observation: Downstream still reads legacy `stress_scorecard_v1` in Problem Classification, AI Commentary refs, Candidate Comparison stress bundle, and snapshot mirror — confirms Phase 2 migration scope.
  Evidence: Session 00 audit §5.

## Decision Log

| ID | Decision | Rationale |
| --- | --- | --- |
| UPG-34-01 | Phase 2 ExecPlan; MVP plan stays Completed | Preserve 2026-05-27 acceptance history |
| UPG-34-02 | Ruleset `current_portfolio_stress_scorecard_rules_v1_1` | Distinguish from MVP implicit contract |
| UPG-34-03 | Add v1.1 keys + keep MVP key aliases one release | Avoid breaking snapshot/tests |
| UPG-34-04 | Optional `portfolio_xray` attach kwarg | Same circular-import pattern as Block 3.3 |
| UPG-34-05 | Do not remove `stress_scorecard_v1` | Legacy mandate path; explicit fallback only |
| UPG-34-06 | `stress_diagnosis.diagnosis_confidence` enum | Weak coverage/DQ must not sound fully confident |
| UPG-34-07 | `next_decision_uses[]` replaces singular `next_decision_use` | One diagnosis feeds multiple downstream blocks |
| UPG-34-08 | `relatively_resilient_scenarios` / `less_damaging_scenarios` | Avoid mandate-adjacent “passes normally” |
| UPG-34-09 | 2.4/2.6 optional attach with not_applicable bridges | Scorecard always runs; `block_status` from stress only |
| UPG-34-10 | Mandate summarize-only boundary | Core MVP 3.4 never creates internal mandate pass/fail |

## Outcomes & Retrospective

**Closed 2026-05-29 (Session 13).**

- Delivered `current_portfolio_stress_scorecard_rules_v1_1` on `stress_report.json` with executive `stress_diagnosis`, structured summaries, optional pre-stress bridges, and downstream signal blocks.
- Migrated Problem Classification, Candidate Comparison, AI Commentary grounding, snapshot mirror, and Core MVP validation to v1-primary paths; legacy `stress_scorecard_v1` remains for mandate rollup only.
- Fifteen baseline gaps (G1–G15) closed; **40** contract tests + materialization/downstream/live E2E coverage; Block 3 fixture matrix **7/7**.
- **Deferred:** retirement of `stress_scorecard_v1`; committed live `analysis_subject` refresh left to operators (G15).
- **Evidence:** [acceptance audit](../audits/2026-05-29_block_3_4_institutional_upgrade_acceptance_audit.md); `DEC-2026-05-29-004`, `DEC-2026-05-29-005`.

## Gap matrix (baseline → target)

| Area | Current (`src/current_portfolio_stress_scorecard_block.py`) | Target v1.1 |
| --- | --- | --- |
| Product metadata | `version`, `block` only | `block_status`, `ruleset_version`, `scorecard_scope`, `source_blocks_used`, `stress_coverage`, `legacy_fallback_used` (bool) |
| Summaries | `top_loss_contributors`, `top_risk_contributors`, split offset/main_gap | `loss_contribution_summary`, `risk_contribution_summary`, `hedge_gap_summary` (+ MVP aliases) |
| Diagnosis | `diagnosis_summary_en` only | `stress_diagnosis` + `diagnosis_confidence` + short `diagnosis_summary_en` |
| Pre-stress | None | `pre_stress_confirmation_summary` |
| Downstream | Legacy scorecard primary in PC/AI/CC/snapshot | v1-primary; legacy explicit fallback |
| Signals | None | `problem_classification_signals`, `candidate_comparison_targets`, `ai_commentary_context`, `next_decision_uses[]` |

## Live-output acceptance (canonical — Session 11+)

After fresh `run_portfolio_review.py --skip-candidates`, on `analysis_subject/stress_report.json`:

1. `stress_diagnosis.headline` non-empty when `block_status` ∈ `{ok, partial}`
2. `stress_diagnosis.diagnosis_confidence` present
3. `hedge_gap_summary.main_hedge_gap_scenario_id` when `hedge_gap_analysis_v1` available
4. `legacy_fallback_used` explicit `true` / `false`
5. `next_decision_uses` non-empty when `block_status` ∈ `{ok, partial}`
6. No “passes normally” under `current_portfolio_stress_scorecard_v1`

## Session file map (01–13)

| Session | Primary files |
| --- | --- |
| 01 | `docs/specs/current_portfolio_stress_scorecard_spec.md`, `docs/specs/stress_lab_layer_spec.md` |
| 02–06 | `src/current_portfolio_stress_scorecard_block.py`, `tests/test_current_portfolio_stress_scorecard_v1_contract.py` |
| 07 | `current_portfolio_stress_scorecard_block.py`, `run_report.py`, `run_portfolio_review.py` |
| 08 | `problem_classification.py`, `tests/test_problem_classification.py` |
| 09 | `candidate_comparison.py`, `tests/test_stress_downstream_integration.py` |
| 10 | `ai_commentary_context.py`, `portfolio_commentary.py`, `tests/test_ai_commentary_context.py` |
| 11 | `snapshot.py`, `scripts/core_mvp_validation_contract.py`, `src/live_core_e2e.py` |
| 12–13 | SPEC, OUTPUTS, TESTING, CHANGELOG, DECISIONS, acceptance audit |

## Session 00 — Baseline audit (closed)

**Objective:** Gap matrix, consumer inventory, pytest baseline — no `src/` changes.

**Deliverable:** [2026-05-29_block_3_4_session_00_baseline_audit.md](../audits/2026-05-29_block_3_4_session_00_baseline_audit.md)

**Tests:** `python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py -q` → **4 passed**

**Must not change:** Any product code (honored).

## Sessions 01–13 (outline)

Full per-session objectives, acceptance, risks, and “must not change” blocks are in the planning transcript and gap matrix above. **Run one session per chat** in order; do not skip ahead.

| Session | One-line goal |
| --- | --- |
| 01 | Freeze v1.1 spec + diagnosis_confidence + next_decision_uses + language/mandate rules |
| 02 | `block_status`, `ruleset_version`, `legacy_fallback_used`, contract tests |
| 03 | Worst scenario tests; `stress_coverage` |
| 04 | Loss/risk summaries + concentration + RC limitation |
| 05 | `hedge_gap_summary` + `main_hedge_gap_scenario_id` from 3.3 only |
| 06 | `stress_diagnosis` object; `next_decision_uses[]`; forbidden phrase scan |
| 07 | `pre_stress_confirmation_summary`; graceful 2.4/2.6 degradation |
| 08 | PC v1-primary + `problem_classification_signals` |
| 09 | `candidate_comparison_targets` + CC v1-primary |
| 10 | AI `current_portfolio_stress_scorecard_context` |
| 11 | Snapshot, validator, live-output gates |
| 12 | Documentation sync |
| 13 | Acceptance audit + plan closure |

## Test theme → session map

| # | Theme | Sessions |
| --- | --- | --- |
| 1 | Contract integrity | 02, 13 |
| 2 | Worst scenario logic | 03, 13 |
| 3 | Loss contribution | 04, 13 |
| 4 | Risk contribution | 04, 13 |
| 5 | Factor attribution | 05, 13 |
| 6 | Hedge gap integration | 05, 13 |
| 7 | Pre-stress confirmation | 07, 13 |
| 8 | Problem Classification | 08, 13 |
| 9 | Candidate Comparison | 09, 13 |
| 10 | AI Commentary | 10, 13 |
| 11 | Materialization | 11, 13 |
| 12 | Backward compatibility | 02, 04, 13 |
| 13 | Live-output + language | 06, 11, 13 |
| 14 | diagnosis_confidence + next_decision_uses[] | 01, 02, 06, 11 |
| 15 | 2.4/2.6 graceful degradation | 01, 07, 11 |

## Out of scope

PDF/HTML UI, crisis replay UI, What-If simulator, macro overlay, candidate factory, optimizer, **internal** mandate pass/fail inside Core MVP 3.4, retirement of `stress_scorecard_v1`.
