# Core MVP Historical Stress Replay (Stress Test Lab)

This ExecPlan is a living document. Maintain `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` per [PLANS.md](../../PLANS.md).

**Normative spec:** [docs/specs/core_mvp_historical_stress_replay_spec.md](../specs/core_mvp_historical_stress_replay_spec.md)

## Purpose / Big Picture

Portfolio-first Stress Test Lab must show honest historical crisis replay: **direct history only**, explicit unavailable positions, no false full-portfolio precision when young ETFs or stocks lack episode data.

## Progress

- [x] (2026-05-28) Session 1 — Direct-only spec, config/coverage helpers, proxy map labeled Advanced/Legacy, tests `test_core_mvp_historical_stress_replay_config.py`.
- [x] (2026-05-28) Session 2 — `build_historical_stress_replay_v1` + `build_episode_replay`; tests `test_core_mvp_historical_stress_replay.py` (cases A–D).
- [x] (2026-05-28) Session 3 — `run_report.py` diagnostic path + `stress_results_v1` merge; contract tests.
- [x] (2026-05-28) Session 4 — `format_episode_diagnosis_summary_en`, episode `diagnosis_summary_en`, Block 3.2 partial replay copy; tests in `test_core_mvp_historical_stress_replay.py` and `test_stress_results_historical_replay_contract.py`.
- [x] (2026-05-28) Session 5 — `test_core_mvp_historical_stress_replay_contract.py` (cases A–D parametrized, Block 3.2 merge, attach path); `episode_start`/`episode_end` merged on Block 3.2 rows.
- [x] (2026-05-28) Session 6 — Docs sync: `stress_lab_layer_spec.md`, `stress_testing_spec.md` §9.4, `OUTPUTS.md`, `DECISIONS.md` (DEC-2026-05-28-001), `TESTING.md`.
- [x] (2026-05-28) Session 7 — Live `run_portfolio_review.py --skip-candidates`; gate `scripts/verify_core_mvp_historical_stress_replay.py`; [acceptance audit](../audits/2026-05-28_core_mvp_historical_stress_replay_acceptance_audit.md); pytest **35 passed**.

## Decision Log

- Decision: Core MVP uses **direct history only** (no ETF proxy, factor, or asset-class substitution in Stress Lab outputs).
  Rationale: Product policy 2026-05-28; avoids false precision on dotcom/2008 for modern books.
  Date: 2026-05-28 / Session 1.

- Decision: `min_coverage_ratio = 0.45` and episode dates mirror `HISTORICAL_EPISODES` in `src/stress.py`.
  Rationale: Align direct usability with existing direct tier convention; single date registry.
  Date: 2026-05-28 / Session 1.

## Surprises & Discoveries

- Discovery: On the Core MVP demo book with a **2014+** aligned monthly panel, dotcom and 2008 replay as **unavailable** for all risk tickers (episode window predates panel). This is correct honest behavior — not a proxy fill — and Block 3.2 clears portfolio metrics accordingly.
- Discovery: 2020 / 2022 / banking_2023 show **full_replay** with portfolio loss/DD matching legacy `historical_results` where data is reliable.

## Outcomes & Retrospective

- **Shipped:** `historical_stress_replay_v1` (direct history only) on portfolio-first diagnostic `stress_report.json`, merged into Block 3.2, English copy, contract tests, docs (DEC-2026-05-28-001), live acceptance.
- **Evidence:** [2026-05-28_core_mvp_historical_stress_replay_acceptance_audit.md](../audits/2026-05-28_core_mvp_historical_stress_replay_acceptance_audit.md); `scripts/verify_core_mvp_historical_stress_replay.py`.
- **Follow-up:** Deeper pre-2014 monthly history (if product wants dotcom/2008 position-level replay on young books) is an operator/data-window choice, not a proxy substitution change.
