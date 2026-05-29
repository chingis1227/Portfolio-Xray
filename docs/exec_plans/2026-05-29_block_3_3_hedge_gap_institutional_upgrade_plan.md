# Block 3.3 Hedge Gap Analysis — Institutional Upgrade (Phase 2)

**Status: Completed** — Session 12 closed 2026-05-29. Evidence: [institutional upgrade acceptance audit](../audits/2026-05-29_block_3_3_institutional_upgrade_acceptance_audit.md).

Baseline: [Session 00 baseline audit](../audits/2026-05-29_block_3_3_session_00_baseline_audit.md).

v1 origin: [Block 3.3 Hedge Gap Analysis MVP](2026-05-27_block_3_3_hedge_gap_analysis_plan.md) (**Completed** 2026-05-27, contribution-based `hedge_gap_analysis_v1`, eight protection rows).

Prerequisites: Block 3.2 Stress Results (**Completed**); Block 3.4 Scorecard (**Completed**); Block 2.4 institutional upgrade (**Completed**); Block 2.6 `heuristic_v2` (**Completed**).

This ExecPlan follows [PLANS.md](../../PLANS.md). Update `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` at each session stop.

## Purpose / Big Picture

After this upgrade, operators and downstream blocks read `stress_report.json` → `hedge_gap_analysis_v1` and get **institutional-grade, deterministic** hedge-gap diagnostics: strict product contract, transparent main-gap selection, post-stress confirmation bridges to Blocks 2.4 and 2.6, and migrated consumers (Problem Classification, Candidate Comparison, AI Commentary) — without PDF, without re-running stress, and without taxonomy hedge pre-labeling.

Verify after full closure:

```bash
python run_portfolio_review.py --skip-candidates
# Inspect: {output_dir_final}/analysis_subject/stress_report.json
# Expect: hedge_gap_analysis_v1 with block_status, ruleset_version, protection_status,
#   bridges (hidden_exposure_confirmation, weakness_map_confirmation), enriched main_hedge_gap
python -m pytest tests/test_hedge_gap_analysis_v1_contract.py tests/test_problem_classification.py \
  tests/test_ai_commentary_context.py tests/test_stress_downstream_integration.py -q
```

## Architecture Boundary (hard)

Block 3.3 is a read-only adapter over Blocks **3.1–3.2** stress evidence.

Must **not**: run new scenarios; mutate `scenario_results` / `stress_results_v1`; optimize weights; pre-label hedge assets; call LLM for hedge judgments; mix RC_vol with stress loss contribution.

May **read optionally** (attach-time only, no circular imports): `portfolio_xray.json` slices for Block 2.4 alerts and Block 2.6 weakness map — for confirmation bridges and main-gap relevance scoring only.

## Non-goals

- PDF / HTML report redesign
- Full UI screen
- Historical crisis replay inside hedge gap
- Retirement of legacy `hedge_gap_analysis` (mark secondary; keep compatibility)
- Block 2.6 reading `stress_report` (forbidden)

## Progress

- [x] (2026-05-29) **Session 01 — Baseline audit:** field matrix, legacy consumer inventory, file map, pytest baseline → [audit](../audits/2026-05-29_block_3_3_session_00_baseline_audit.md)
- [x] (2026-05-29) **Session 02 — Contract v1.1:** `RULESET_VERSION`, `block_status`, row/summary product fields, aliases, `protection_status` taxonomy, contract tests; spec §v1.1 updated
- [x] (2026-05-29) **Session 03 — Calculation hardening:** finite PnL filter, safe ratio, deterministic splits → [audit](../audits/2026-05-29_block_3_3_session_03_calculation_hardening.md); pytest **60 passed**
- [x] (2026-05-29) **Session 04 — Main hedge gap selection v2:** weighted `main_gap_score`; `selection_reason_*`; ruleset `hedge_gap_rules_v1_2`
- [x] (2026-05-29) **Session 05 — Bridge Block 2.4:** `hidden_exposure_confirmation[]`; `enrich_block_2_4_weak_hedge_from_hedge_gap`; wire in `build_portfolio_xray_v2` + stress re-export in `run_report`
- [x] (2026-05-29) **Session 06 — Bridge Block 2.6:** `weakness_map_confirmation[]`; optional 2.6 input at attach → [audit](../audits/2026-05-29_block_3_3_session_06_block_2_6_bridge.md)
- [x] (2026-05-29) **Session 07 — Problem Classification:** v1-primary paths; legacy `hedge_gap_status` fallback only → [audit](../audits/2026-05-29_block_3_3_session_07_problem_classification.md)
- [x] (2026-05-29) **Session 08 — Candidate Comparison:** `hedge_gap_comparison` when both stress outputs exist → [audit](../audits/2026-05-29_block_3_3_session_08_candidate_comparison.md)
- [x] (2026-05-29) **Session 09 — AI Commentary:** `hedge_gap_context`; v1-primary stress commentary exec summary → [audit](../audits/2026-05-29_block_3_3_session_09_ai_commentary.md)
- [x] (2026-05-29) **Session 10 — Materialization:** snapshot mirror, scorecard linkage, core validation contract, live E2E → [audit](../audits/2026-05-29_block_3_3_session_10_materialization.md)
- [x] (2026-05-29) **Session 11 — Documentation sync:** SPEC, OUTPUTS, TESTING, CHANGELOG, DECISIONS; `DEC-2026-05-29-003` → [audit](../audits/2026-05-29_block_3_3_session_11_documentation_sync.md); pytest **98 passed** (doc-sync bundle)
- [x] (2026-05-29) **Session 12 — Acceptance audit + plan closure:** gap matrix G1–G10 closed; fixture matrix 7/7; pytest **89** (closure subset) / **106** (extended bundle) → [acceptance audit](../audits/2026-05-29_block_3_3_institutional_upgrade_acceptance_audit.md)

## Surprises & Discoveries

### Session 01 (2026-05-29)

- Observation: Live subject path shows legacy `hedge_gap_analysis.status = not_applicable` while v1 fully diagnoses offset coverage — confirms DEC-2026-05-27-002 migration trigger is real for Problem Classification.
  Evidence: `Main portfolio/analysis_subject/stress_report.json`; baseline audit §6.

- Observation: Acceptance audit (2026-05-27) still says "seven risk types" but implementation and pytest expect **eight** (`recession_severe_protection` added same day).
  Evidence: `test_block_3_3_risk_scenario_map_eight_entries`; Session 01 audit §3.

- Observation: `main_hedge_gap` selection is min `offset_coverage_ratio` only — can rank tiny-loss zero-offset above material-loss weak-offset until Session 04 scoring ships.
  Evidence: `_build_summary` in `src/hedge_gap_analysis_block.py` L163–168.

- Observation (Session 04): Main gap now uses `main_gap_score = offset_deficit × loss_severity × concentration_multiplier` with `RULESET_VERSION = hedge_gap_rules_v1_2`; legacy min-ratio fallback when score unavailable.
  Evidence: `_select_main_hedge_gap_row`, `tests/test_hedge_gap_analysis_v1_contract.py::test_main_gap_score_material_loss_beats_tiny_zero_offset`.

- Decision (Session 01): Product aliases `protection_type` / `scenario_id` mirror frozen keys `risk_type` / `linked_scenario_id` (user choice); no rename of `commodity_inflation_shock_protection`.

## Decision Log

| ID | Decision | Rationale |
| --- | --- | --- |
| UPG-01 | Phase 2 as new ExecPlan; v1 MVP plan stays Completed | Avoid rewriting closed acceptance history |
| UPG-02 | Add aliases, not rename canonical keys | Backward compatibility with scorecard, snapshot, 2.4 enrichment |
| UPG-03 | Keep `commodity_inflation_shock_protection` id | Frozen since 2026-05-27 acceptance + fixture matrix |
| UPG-04 | Optional upstream context via attach kwargs | Prevent 2.4 ↔ 3.3 circular imports |

## Outcomes & Retrospective

**Completed 2026-05-29.** Phase 2 delivered institutional-grade `hedge_gap_analysis_v1`: frozen eight-row protection map, v1.1 product fields, hardened ratio math, `hedge_gap_rules_v1_2` main-gap scoring, read-only bridges to Blocks 2.4 and 2.6, and v1-primary downstream (Problem Classification, Candidate Comparison, AI Commentary, snapshot/scorecard mirrors, Core MVP validator). Legacy `hedge_gap_analysis` remains secondary; no PDF or legacy retirement in this wave.

**What worked:** Attach-time kwargs avoided circular imports; weighted `main_gap_score` fixed min-ratio mis-ranking on live-like books; shared `check_hedge_gap_analysis_v1` unified fixture matrix and live E2E gates.

**Residual / follow-up:** Deprecate `stress_conclusions.hedge_gap_status`-only consumers when external integrations migrate; refresh committed `analysis_subject` stress artifacts on operator runs.

**Evidence:** [acceptance audit](../audits/2026-05-29_block_3_3_institutional_upgrade_acceptance_audit.md); `DEC-2026-05-29-003`; pytest **106 passed** (extended closure bundle).

## Session file map (02–12)

| Session | Primary files |
| --- | --- |
| 02–04 | `src/hedge_gap_analysis_block.py`, `docs/specs/hedge_gap_analysis_spec.md`, `tests/test_hedge_gap_analysis_v1_contract.py` |
| 05 | `hedge_gap_analysis_block.py`, `block_2_4_hidden_exposure.py`, `portfolio_xray.py` |
| 06 | `hedge_gap_analysis_block.py`, `run_portfolio_review.py` (optional attach inputs) |
| 07 | `problem_classification.py`, `tests/test_problem_classification.py` |
| 08 | `candidate_comparison.py`, `docs/specs/candidate_comparison_spec.md`, `tests/test_stress_downstream_integration.py` |
| 09 | `ai_commentary_context.py`, `portfolio_commentary.py`, `tests/test_ai_commentary_context.py` |
| 10 | `snapshot.py`, `current_portfolio_stress_scorecard_block.py`, `live_core_e2e.py`, `scripts/core_mvp_validation_contract.py` |
| 11–12 | SPEC, OUTPUTS, TESTING, CHANGELOG, DECISIONS, acceptance audit |
