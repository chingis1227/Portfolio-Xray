# Block 2.6 Portfolio Weakness Map — heuristic_v2 Institutional Upgrade

**Status: Completed** (Session 09 closed 2026-05-29)

Baseline: [Session 00 baseline audit](../audits/2026-05-29_block_2_6_session_00_baseline_audit.md).  
v1 origin: [Block 2.6 Portfolio Weakness Map MVP](2026-05-26_block_2_6_portfolio_weakness_map_plan.md) (**Completed** 2026-05-26, `heuristic_v1`, nine weakness risk types).

Prerequisite: [Block 2.4 Institutional Upgrade](2026-05-29_block_2_4_institutional_upgrade_plan.md) (**Completed** 2026-05-29, `heuristic_v2` on hidden exposure).

This ExecPlan follows [PLANS.md](../../PLANS.md). Update `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` at each session stop.

## Purpose / Big Picture

After this upgrade, a wealth manager opening `portfolio_xray.json` → `block_2_6_portfolio_weakness_map` sees **eight pre-stress vulnerability hypotheses** named exactly like Stress Lab scenarios, each with a transparent 0–100 score, plain-English *why High/Medium/Low*, and `next_tests` pointing to the right crash tests — **without** any scenario loss numbers.

Verify after full closure:

```bash
python run_portfolio_review.py
# Inspect: {output_dir_final}/analysis_subject/portfolio_xray.json
# Expect: metadata.rule_version == "heuristic_v2", len(risk_types) == 8,
#   canonical risk_type ids, usd_shock scored OR Unavailable with blocked_upstream_fields
```

## Architecture Boundary (hard)

Block 2.6 is a read-only adapter over Blocks **2.1–2.5** only.

Must **not** read: `stress_report`, `scenario_results`, scenario PnL, `pnl_by_asset_pct`, hedge gap, pass/fail, loss attribution.

May read: exported Block 2.3 fields (including factor variance adapted at X-Ray build time).

## Progress

- [x] (2026-05-29) **Session 00 — Baseline audit:** risk ID mismatch, downstream split, upstream signals, gap matrix → [audit](../audits/2026-05-29_block_2_6_session_00_baseline_audit.md)
- [x] (2026-05-29) **Session 02 — Contract v2:** diagnostics spec §2.6.1, Pareto UI spec, DECISIONS, canonical 8 risk IDs
- [x] (2026-05-29) **Session 03 — Rule engine v2:** `RISK_RULE_TABLES`, eight risks in `block_2_6_portfolio_weakness_map.py`
- [x] (2026-05-29) **Session 04 — USD shock:** full scoring or explicit Unavailable + `blocked_upstream_fields`
- [x] (2026-05-29) **Session 05 — Block 2.4 v2 integration:** status, confidence, contributing_assets, limitations
- [x] (2026-05-29) **Session 06 — Narrative layer:** `short_diagnosis`, `why_status`, `key_evidence`, `linked_assets` implemented in Block 2.6 builder and covered by focused unit test updates
- [x] (2026-05-29) **Session 07 — Downstream SSOT:** problem_classification + ai_commentary + X-Ray formatters use `block_2_6_portfolio_weakness_map`; legacy `sections.weakness_map` marked `legacy` / non-product
- [x] (2026-05-29) **Session 08 — Tests and fixtures:** per-risk tests, stress boundary test, golden regen, live validation → [audit](../audits/2026-05-29_block_2_6_session_08_tests_golden.md)
- [x] (2026-05-29) **Session 09 — Documentation and acceptance:** SPEC/CHANGELOG, Pareto UI spec, acceptance audit, plan **Completed** → [acceptance audit](../audits/2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md)

## Surprises & Discoveries

- Observation: Block 2.6 `next_tests` already use canonical Stress Lab `scenario_id` strings while `risk_type` uses a parallel weakness namespace — creates operator confusion only on the id field, not on Stress Lab routing.
  Evidence: `_RISK_COPY` in `src/block_2_6_portfolio_weakness_map.py` L173–240 vs `RISK_TYPES` L17–27.

- Observation: Block 2.4 v2 ships currency and factor evidence that v1 Block 2.6 ignores for USD — USD v2 can reuse 2.1/2.3 patterns without new upstream exports.
  Evidence: Session 00 audit §5; `block_2_4_hidden_exposure.py` `_currency_concentration_evidence`.

- Observation: Problem Classification `_problem_id_from_risk` uses substring heuristics on legacy `risk` labels — migrating to Block 2.6 requires an explicit canonical `risk_type` → `problem_id` map, not fuzzy matching.
  Evidence: `src/problem_classification.py` L119–133.

- Observation: Plain `explanation` reuse was insufficient for UI Pareto needs; risk-level narratives require deterministic extraction of top evidence rows, status rationale, and concise linked assets per risk.
  Evidence: Session 06 implementation in `src/block_2_6_portfolio_weakness_map.py` now builds `short_diagnosis`, `why_status`, and `key_evidence` from ranked evidence rows.

## Decision Log

- Decision: Product Block 2.6 v2 uses **eight** canonical risk types = `SYNTHETIC_SCENARIO_IDS` (same string as `scenario_id`).
  Rationale: User requirement + Stress Lab alignment; `next_tests` and `risk_type` share one namespace.
  Date: 2026-05-29 / plan author.

- Decision: Remove `volatility_spike` from product Block 2.6; keep only in legacy `sections.weakness_map` if needed.
  Rationale: Not in Stress Lab active synthetic suite (`stress_testing_spec.md` §2.3 deferred).
  Date: 2026-05-29.

- Decision: Publish `LEGACY_RISK_ALIASES` in `diagnostics_meta` for one release (v1 weakness id → canonical id).
  Rationale: Soften breaking change for any client parsing v1 `risk_type` strings.
  Date: 2026-05-29.

- Decision: Legacy `sections.weakness_map` remains stress-coupled but gains `legacy: true`; must not drive Problem Classification after Session 07.
  Rationale: Preserve golden/report compatibility without split-brain product conclusions.
  Date: 2026-05-29.

- Decision: Build Session 06 narrative fields directly from existing Block 2.6 evidence rows (deterministic ranking by evidence direction) instead of introducing a second, parallel narrative ruleset.
  Rationale: Keep explanations transparent and auditable; avoid divergence between scoring evidence and UI-facing narrative.
  Date: 2026-05-29.

- Decision: Problem Classification, AI commentary grounding, and X-Ray text/HTML/commentary use `block_2_6_portfolio_weakness_map` only; legacy `sections.weakness_map` is tagged `legacy: true` / `product_surface: false` and must not feed classification.
  Rationale: Eliminate split-brain product conclusions between stress-coupled legacy section and pre-stress product block.
  Date: 2026-05-29.

- Decision: Session 08 verification uses dedicated stress-boundary tests plus `assert_block_2_6_product_contract` on golden and live builds; golden fixture regen is required when Block 2.6 narrative/scoring contract changes.
  Rationale: Close gap matrix G9 (per-risk + boundary + golden + live) before Session 09 acceptance audit.
  Date: 2026-05-29.

## Outcomes & Retrospective

**Plan status: Completed** (2026-05-29, Session 09).

**Delivered:** Product Block 2.6 now ships `heuristic_v2` with eight canonical Stress Lab-aligned `risk_type` values, transparent rule tables over Blocks 2.1–2.5, institutional narrative fields, explicit USD blocked-field registry when FX evidence is missing, stress-boundary enforcement (tests + metadata warnings), and downstream SSOT for Problem Classification and AI commentary. Legacy `sections.weakness_map` remains for formatters with `legacy: true`.

**Verification:** Closure pytest **68 passed**; live subject X-Ray on root `config.yml` shows `heuristic_v2`, eight risks, scored `usd_shock`; [acceptance audit](../audits/2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md).

**Deferred:** Retire legacy weakness section; optional `signal_scores` UI surface; extend beyond eight synthetic scenarios without Stress Lab spec change.

## Context and Orientation

- Pipeline: `run_portfolio_review.py` → `build_portfolio_xray_v2` in `src/portfolio_xray.py` → writes `block_2_6_portfolio_weakness_map` after Block 2.5.
- v1 module: `src/block_2_6_portfolio_weakness_map.py` (`heuristic_v1`, 9 risks, ~5 unit tests).
- Canonical scenarios: `src/scenario_library.py` `SYNTHETIC_SCENARIO_IDS`.

## Plan of Work (Sessions 02–09)

Detailed task breakdown is in the Cursor plan `block_2.6_heuristic_v2` and Session 00 audit gap matrix §10. Execute in order; do not skip Session 02 (contract) before changing scoring ids in code.

### Session 02 — Contract v2

Update `docs/specs/portfolio_xray_diagnostics_spec.md` §2.6.1; add `docs/specs/block_2_6_weakness_map_ui_pareto_spec.md`; DECISIONS entry; validator field lists in `scripts/core_mvp_validation_contract.py` (stubs OK if tests not yet updated).

### Sessions 03–06 — Implementation

Single owner file: `src/block_2_6_portfolio_weakness_map.py` — refactor to `heuristic_v2`, eight risks, narrative builder, 2.4 v2 helpers.

### Session 07 — Downstream

`src/problem_classification.py`, `src/ai_commentary_context.py`, `src/portfolio_xray.py` formatters.

### Session 08 — Verification

```bash
python -m pytest tests/test_block_2_6_portfolio_weakness_map.py tests/test_block_2_6_stress_boundary.py tests/test_portfolio_xray_contract.py tests/test_problem_classification.py -q
python run_portfolio_review.py
```

### Session 09 — Closure

Acceptance audit under `docs/audits/2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md`; CHANGELOG; mark this plan **Completed** in `docs/exec_plans/README.md`.

## Acceptance Criteria (closure gate)

- Eight canonical `risk_type` values aligned with `SYNTHETIC_SCENARIO_IDS`
- Each risk: score 0–100 or Unavailable with limitations; Low/Medium/High/Unavailable
- USD: scored or explicit Unavailable with `blocked_upstream_fields`
- Block 2.4 v2 fields consumed where mapped
- No `stress_report` dependency inside Block 2.6 (tests prove)
- Narrative explains status with real signals (no generic boilerplate)
- Problem Classification and AI grounding use `block_2_6_portfolio_weakness_map`
- Pytest closure + live subject X-Ray validation documented in acceptance audit

Plan update note (2026-05-29): Session 06 was marked complete after implementing narrative-field builders (`short_diagnosis`, `why_status`, `key_evidence`, `linked_assets`) in Block 2.6 and extending focused unit tests; this update keeps the ExecPlan state aligned with the working tree and avoids ambiguity for Session 07 downstream wiring.

Plan update note (2026-05-29): Session 08 closed with `tests/test_block_2_6_stress_boundary.py`, expanded Block 2.6 contract tests, golden regen, and live subject validation — see [Session 08 audit](../audits/2026-05-29_block_2_6_session_08_tests_golden.md). Next: Session 09 acceptance + plan closure.
