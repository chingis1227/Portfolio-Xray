# Block 2.4 Hidden Exposure — Institutional Upgrade (Sessions 01–13)

**Status: Completed** (closed 2026-05-29, Session 13)

Baseline: [Session 00 baseline audit](../audits/2026-05-29_block_2_4_session_00_baseline_audit.md).  
MVP origin: [Block 2.4 Hidden Exposure MVP](2026-05-26_block_2_4_hidden_exposure_plan.md) (**Completed** 2026-05-26, `heuristic_v1`).

## Purpose

Upgrade `block_2_4_hidden_exposure` from Core MVP `heuristic_v1` scaffold to institutional-grade `heuristic_v2`: expanded evidence, confidence model v2, contributing assets, wire-time stress/legacy cross-refs, matrix-backed tests, Core MVP validators, and live demo gates — without changing Blocks 2.1–2.3 shapes or running Stress Lab inside Block 2.4.

## Progress

- [x] (2026-05-29) Session 00 — Baseline audit + §10 matrix signed ([audit](../audits/2026-05-29_block_2_4_session_00_baseline_audit.md))
- [x] (2026-05-29) Session 01 — Contract stabilization + duplicate bugfix ([audit](../audits/2026-05-29_block_2_4_session_01_contract_stabilization.md))
- [x] (2026-05-29) Session 02 — Taxonomy / currency sub-signals ([audit](../audits/2026-05-29_block_2_4_session_02_taxonomy_currency.md))
- [x] (2026-05-29) Session 03 — Contributing assets ([audit](../audits/2026-05-29_block_2_4_session_03_contributing_assets.md))
- [x] (2026-05-29) Session 04 — Correlation sub-signals ([audit](../audits/2026-05-29_block_2_4_session_04_correlation_subsignals.md))
- [x] (2026-05-29) Session 05 — Factor concentration ([audit](../audits/2026-05-29_block_2_4_session_05_factor_concentration.md))
- [x] (2026-05-29) Session 06 — Confidence v2 ([audit](../audits/2026-05-29_block_2_4_session_06_confidence_v2.md))
- [x] (2026-05-29) Session 07 — Tail / vol ([audit](../audits/2026-05-29_block_2_4_session_07_tail_vol.md))
- [x] (2026-05-29) Session 08 — Weak hedge stress enrichment ([audit](../audits/2026-05-29_block_2_4_session_08_weak_hedge_stress.md))
- [x] (2026-05-29) Session 09 — Legacy PCA cross-ref ([audit](../audits/2026-05-29_block_2_4_session_09_legacy_pca_cross_ref.md))
- [x] (2026-05-29) Session 10 — Tests + golden ([audit](../audits/2026-05-29_block_2_4_session_10_tests_golden.md))
- [x] (2026-05-29) Session 11 — Core MVP validation ([audit](../audits/2026-05-29_block_2_4_session_11_core_mvp_validation.md))
- [x] (2026-05-29) Session 12 — Live demo + regression ([audit](../audits/2026-05-29_block_2_4_session_12_live_demo_regression.md))
- [x] (2026-05-29) Session 13 — Institutional closure ([audit](../audits/2026-05-29_block_2_4_session_13_institutional_closure.md))

## Decision Log

- Decision: Keep six product alerts; distribute factor/currency/FX signals as sub-signals and evidence rather than new alert ids.
  Rationale: Core MVP UX and Block 2.6 weakness-map wiring expect six hidden-exposure scores.
  Date: 2026-05-29.
- Decision: Defer upstream-only dimensions via `blocked_upstream_fields` (9 entries) instead of silent omission.
  Rationale: Session 00 matrix requires documented DEF rows until Block 2.1/2.2 exports expand.
  Date: 2026-05-29.
- Decision: Stress Lab and legacy PCA enter Block 2.4 only as wire-time enrichment summaries; scores remain `heuristic_v2` over 2.1–2.3.
  Rationale: Product boundary — Block 2.4 does not run Stress Lab (`does_not_run_stress_lab: true`).
  Date: 2026-05-29.

## Outcomes & Retrospective

Institutional upgrade **complete**. `block_2_4_hidden_exposure` ships `heuristic_v2`, confidence model `v2`, mandatory per-alert v2 fields, 69 matrix-backed evidence rows (pytest), 9-field blocked-upstream registry, Core MVP contract in `scripts/core_mvp_validation_contract.py`, live validator `scripts/validate_block_2_4_live.py`, and `live_core_e2e` Block 2.4 checks. Closure regression: **140 passed** (Session 13 bundle). Matrix sign-off: [completion matrix v2](../audits/2026-05-29_block_2_4_completion_matrix_v2_signoff.md).

Deferred post-upgrade (not Block 2.4 blockers): Block 2.1 `by_duration_bucket` / `by_credit_quality` / issuer-thematic aggregation; Block 2.2 rolling correlation instability and Sharpe instability exports; Asset X-Ray per-asset credit-equity correlation.

## Verification (closure bundle)

```bash
python -m pytest tests/test_core_mvp_block2_4_contract.py tests/test_block_2_4_hidden_exposure.py tests/test_block_2_4_matrix_coverage.py tests/test_portfolio_xray_contract.py tests/test_core_mvp_blocks_1_3_boundaries.py -q
python scripts/validate_block_2_4_live.py --refresh-xray
```
