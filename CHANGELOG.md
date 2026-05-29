# CHANGELOG.md

This file is the concise living history of meaningful project changes.

It records what was added, changed, removed, fixed, or deprecated at a project level. It is not a full git log, not a roadmap, and not a replacement for specs, tests, or ExecPlans.

Date: 2026-05-29

Category: Added

- **Block 4 v2 Session 14 (closure):** V1 product validators removed from `scripts/core_mvp_validation_contract.py`; decision-entry tests migrated to v2; ExecPlan **Completed**; evidence: [Session 14 acceptance audit](docs/audits/2026-05-29_block_4_v2_session_14_institutional_closure.md); pytest **109 passed** (Block 4 closure bundle).

Category: Added

- **Block 4 v2 Session 13:** Documentation sync (SPEC, OUTPUTS, TESTING, operator guide, diagnostic journey v2 bridge); evidence: [Session 13 audit](docs/audits/2026-05-29_block_4_v2_session_13_documentation_sync.md).

Category: Added

- **Block 4 v2 Session 12:** Live product validation — `scripts/validate_block_4_live.py`, live E2E v2 gates in `src/live_core_e2e.py`; evidence: [Session 12 audit](docs/audits/2026-05-29_block_4_v2_session_12_live_product_validation.md).

Category: Added

- **Blocks 1–3 diagnostic journey UX draft:** Flask prototype `diagnostic_journey/` (port 5006) — guided Setup → X-Ray → Stress Lab → problem bridge; `diagnostic_journey/presentation.py` translates JSON into advisor-ready copy (human labels, formatted %, no raw backend keys at top level); spec [diagnostic_journey_ux_draft.md](docs/specs/diagnostic_journey_ux_draft.md). Tests: `tests/test_diagnostic_journey_view_model.py`.

Category: Fixed

- **Core MVP X-Ray tail-risk wiring:** `run_report.py` now passes per-window snapshot analytics (`snapshot_10y` → `5y` → `3y`) into `build_portfolio_xray_v2` via `resolve_xray_snapshot_inputs` in `src/snapshot.py`, so `analytics.tail_risk` reaches Block 2.2 `tail_risk_diagnostics` and Block 2.4 `tail_risk` alert evidence. Block 2.2 product contract adds `metric_available`, method/frequency/window metadata. Tests: `tests/test_xray_tail_risk_wiring.py`.

Category: Added

- **Blocks 1–3 post-audit plan (Session 10 / Phase D):** Block 5 compare/verdict — product contracts for `current_vs_candidate_v1` and `decision_verdict_v1` in `scripts/core_mvp_validation_contract.py`; live E2E Block 5 gates in `src/live_core_e2e.py` (`product_one_candidate`); `tests/test_block_5_decision_compare_contract.py`. Decision [DEC-2026-05-29-012](DECISIONS.md). Evidence: [Session 10 audit](docs/audits/2026-05-29_block_5_session_10_current_vs_candidate_decision_verdict.md).

Category: Added

- **Blocks 1–3 post-audit plan (Session 09 / Phase D):** Block 4 decision entry — product contracts for `problem_classification_v1` and `candidate_launchpad_v1` in `scripts/core_mvp_validation_contract.py`; live E2E Block 4 gates in `src/live_core_e2e.py`; `tests/test_block_4_decision_entry_contract.py`. Decision [DEC-2026-05-29-011](DECISIONS.md). Evidence: [Session 09 audit](docs/audits/2026-05-29_block_4_session_09_problem_classification_launchpad.md).

Category: Added

- **Blocks 1–3 post-audit plan (Session 06):** Phase A closure — live re-run of three canonical CLIs; `validate_live_core_artifacts` OK for `core_blocks_1_3`, `diagnosis_only`, `product_one_candidate`; verdict **`READY_FOR_DECISION_WORKFLOW`**. Evidence: [foundation closure audit](docs/audits/2026-05-29_blocks_1_3_foundation_closure_audit.md). Decision [DEC-2026-05-29-010](DECISIONS.md). Pytest bundle **261 passed**, 1 skipped.

Category: Fixed

- **Blocks 1–3 post-audit plan (Session 05):** Live core E2E validator profiles — `detect_live_core_e2e_profile` and profile-specific checks in `src/live_core_e2e.py` (`core_blocks_1_3`, `diagnosis_only`, `product_one_candidate`, `research_batch_core_fast`); `scripts/verify_live_core_e2e.py` prints detected profile and accepts `--profile`. Decision [DEC-2026-05-29-009](DECISIONS.md).

Category: Fixed

- **Blocks 1–3 post-audit plan (Session 04):** Core-only materialize runs `apply_core_blocks_product_bundle_hygiene` — removes stale Block 4+ JSON under `analysis_subject/` (`problem_classification`, `candidate_launchpad`, `ai_commentary_context`) and deletes root post-compare/decision files. Decision [DEC-2026-05-29-008](DECISIONS.md).

Category: Fixed

- **Blocks 1–3 post-audit plan (Session 03):** Diagnosis-only materialize runs `apply_diagnosis_only_product_bundle_hygiene` — root `current_vs_candidate.json`, `decision_verdict.json`, and `candidate_comparison.json` get explicit `no_candidate_v1` tombstones; stale advanced compare files removed. Decision [DEC-2026-05-29-007](DECISIONS.md).

Category: Fixed

- **Blocks 1–3 post-audit plan (Session 02):** For `explicit_list` factory runs, product `candidate_comparison.json` now writes scoped baseline + selected candidate rows only; full on-disk registry scan moves to optional `candidate_comparison_registry.json`. Decision [DEC-2026-05-29-006](DECISIONS.md).

Category: Added

- **Blocks 1–3 post-audit plan (Session 00–01):** Active ExecPlan [2026-05-29_blocks_1_3_post_audit_development_plan.md](docs/exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md); operator [runtime_artifact_contract.md](docs/runtime_artifact_contract.md); Session 01 regression `test_run_report_timing_blocks_registered_in_module` (timing block keys parity with `run_report.py`).

Category: Added

- **Runtime entrypoints:** `run_core_diagnostics.py` (Blocks 1-3 only via `--core-diagnostics-only`); active CLI matrix in [docs/runtime_entrypoints.md](docs/runtime_entrypoints.md); legacy optimizer/policy runners under `legacy/runners/` with root wrappers; tests `tests/test_core_diagnostics_entrypoint.py`.

Category: Added

- **Block 3.4 institutional upgrade Session 13 (closure):** Acceptance audit — gap matrix G1–G15 closed; fixture matrix **7/7**; pytest **142 passed** (extended bundle); ExecPlan **Completed**; evidence: [acceptance audit](docs/audits/2026-05-29_block_3_4_institutional_upgrade_acceptance_audit.md).
- **Block 3.4 institutional upgrade Session 12:** Documentation sync — SPEC/OUTPUTS/TESTING/CHANGELOG/DECISIONS (`DEC-2026-05-29-005`); Block 3.4 regression bundle; [Session 12 audit](docs/audits/2026-05-29_block_3_4_session_12_documentation_sync.md); pytest **71 passed** (doc-sync bundle).
- **Block 3.4 institutional upgrade Session 11:** Materialization — snapshot `stress_suite_results.current_portfolio_stress_scorecard_v1` mirror, `check_current_portfolio_stress_scorecard_v1` in Core MVP validator, live E2E gate; [Session 11 audit](docs/audits/2026-05-29_block_3_4_session_11_materialization.md); pytest **71 passed**.
- **Block 3.4 institutional upgrade Session 10:** AI Commentary — `current_portfolio_stress_scorecard_context` on `ai_commentary_context.json`; v1-primary stress commentary; [Session 10 audit](docs/audits/2026-05-29_block_3_4_session_10_ai_commentary.md); pytest **67 passed**.
- **Block 3.4 institutional upgrade Session 09:** `candidate_comparison_targets` on Block 3.4; Candidate Comparison `stress.current_portfolio_stress_scorecard_v1` v1-primary + top-level `stress_scorecard_comparison`; [Session 09 audit](docs/audits/2026-05-29_block_3_4_session_09_candidate_comparison.md); pytest **47 passed**.
- **Block 3.4 institutional upgrade Session 08:** `problem_classification_signals` on `current_portfolio_stress_scorecard_v1`; Problem Classification v1-primary worst-scenario path with `stress_scorecard_source`; [Session 08 audit](docs/audits/2026-05-29_block_3_4_session_08_problem_classification.md); pytest **46 passed**.
- **Block 3.4 institutional upgrade Sessions 02–07:** v1.1 product metadata, worst selectors + `stress_coverage`, loss/risk summaries, `hedge_gap_summary`, `stress_diagnosis` + `next_decision_uses[]`, `pre_stress_confirmation_summary` (optional 2.4/2.6 bridges); audits under `docs/audits/2026-05-29_block_3_4_session_0[2-7]_*.md`; contract tests **34 passed** after Session 07.
- **Block 3.4 institutional upgrade Session 01:** Frozen v1.1 contract in [current_portfolio_stress_scorecard_spec.md](docs/specs/current_portfolio_stress_scorecard_spec.md) (`current_portfolio_stress_scorecard_rules_v1_1`, `diagnosis_confidence`, `next_decision_uses[]`, mandate boundary, 2.4/2.6 degradation, product language); [stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md) §3.4 linked; [Session 01 audit](docs/audits/2026-05-29_block_3_4_session_01_contract_v1_1.md); no code changes; pytest **4 passed**.
- **Block 2.4 UI Pareto presenter:** `src/block_2_4_hidden_exposure_ui.py` (`build_hidden_risk_cards_pareto`); `tests/test_block_2_4_hidden_exposure_ui.py`; fixes `verify_docs.py` link check for [block_2_4_hidden_exposure_ui_pareto_spec.md](docs/specs/block_2_4_hidden_exposure_ui_pareto_spec.md).
- **Block 3.3 institutional upgrade Session 12 (closure):** Acceptance audit — gap matrix G1–G10 closed; fixture matrix 7/7; pytest **106 passed** (extended bundle); ExecPlan **Completed**; evidence: [acceptance audit](docs/audits/2026-05-29_block_3_3_institutional_upgrade_acceptance_audit.md).
- **Block 3.3 institutional upgrade Session 11:** Documentation sync — SPEC/OUTPUTS/TESTING/CHANGELOG/DECISIONS (`DEC-2026-05-29-003`); expanded Block 3.3 regression bundle; Session 11 audit.
- **Block 3.3 institutional upgrade Session 10:** Materialization — snapshot `stress_suite_results.hedge_gap_analysis_v1` mirror, scorecard `hedge_gap_*` linkage, `check_hedge_gap_analysis_v1` in Core MVP validator, live E2E gate; [Session 10 audit](docs/audits/2026-05-29_block_3_3_session_10_materialization.md).
- **Block 3.3 institutional upgrade Session 09:** AI Commentary — `hedge_gap_context` on `ai_commentary_context.json`; v1-primary stress commentary executive summary; [Session 09 audit](docs/audits/2026-05-29_block_3_3_session_09_ai_commentary.md).
- **Block 3.3 institutional upgrade Session 08:** Candidate Comparison adds `hedge_gap_comparison` and per-candidate `stress.hedge_gap_analysis_v1` when v1 stress blocks exist on baseline and peers.
- **Block 3.3 institutional upgrade Session 07:** Problem Classification uses `hedge_gap_analysis_v1` as primary hedge-gap path; legacy `hedge_gap_status` fallback only; `hedge_gap_source` on `problem_classification.json`.
- **Block 3.3 institutional upgrade Session 06:** Block 2.6 bridge — `weakness_map_confirmation[]` on `hedge_gap_analysis_v1`, optional `attach_hedge_gap_analysis_v1(..., block_2_6_portfolio_weakness_map=...)`, wired from `build_portfolio_xray_v2` (read-only on 2.6); dual-bridge clears pre-stress limitation flags.
- **Block 3.3 institutional upgrade Session 05:** Block 2.4 bridge — `hidden_exposure_confirmation[]` on `hedge_gap_analysis_v1`, per-row `confirmation_status`, `weak_hedge_behavior.hedge_gap_bridge`, wired from `build_portfolio_xray_v2`; Block 2.4 adds `partially_confirmed` / `not_confirmed`; contract tests **66+** passed.
- **Block 3.3 institutional upgrade Session 04:** Main hedge gap selection v2 — weighted `main_gap_score` (offset deficit × loss severity × concentration boost), `selection_reason_code` / `selection_reason_en`, ruleset bump to `hedge_gap_rules_v1_2`; [hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md) §summary updated; contract tests **63 passed**.
- **Block 3.3 institutional upgrade Session 03:** Calculation hardening — finite PnL parsing, safe offset ratio, deterministic hurt/helped split, parametrized `protection_status` tests; contract tests **60 passed**.
- **Block 3.3 institutional upgrade Session 02:** Product contract v1.1 on `hedge_gap_analysis_v1` (`ruleset_version`, `block_status`, `scenario_coverage`, row aliases, `protection_status`, `client_diagnosis_en`, enriched `summary`); [hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md) updated; contract tests **47 passed**.

Category: Added

- **Block 2.6 heuristic_v2 closure (Sessions 00–09):** Product `block_2_6_portfolio_weakness_map` uses eight canonical Stress Lab `risk_type` ids, `heuristic_v2` rule tables, Block 2.4 v2 evidence, narrative fields (`short_diagnosis`, `why_status`, `key_evidence`, `linked_assets`), stress-boundary tests, Problem Classification / AI grounding SSOT, and legacy `sections.weakness_map` tagged non-product. Evidence: [heuristic_v2 acceptance audit](docs/audits/2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md), [UI Pareto spec](docs/specs/block_2_6_weakness_map_ui_pareto_spec.md), `DEC-2026-05-29-001`; closure pytest **68 passed**.

Category: Added

- **Block 2.4 UI Pareto layer spec:** [block_2_4_hidden_exposure_ui_pareto_spec.md](docs/specs/block_2_4_hidden_exposure_ui_pareto_spec.md) — Hidden Risk Cards contract (6 alerts), backend→UI mapping, prioritization, mocks, acceptance criteria; presentation-only (no backend change).

Category: Added

- **Block 2.4 Session 13 (institutional upgrade closure):** Matrix v2 sign-off ([completion matrix](docs/audits/2026-05-29_block_2_4_completion_matrix_v2_signoff.md)); institutional upgrade ExecPlan **Completed**; Sessions 01–13 closed. Evidence: [Session 13 audit](docs/audits/2026-05-29_block_2_4_session_13_institutional_closure.md).

Category: Added

- **Block 2.4 Session 12 (institutional upgrade):** Live demo validation on `Main portfolio/analysis_subject/portfolio_xray.json` (`heuristic_v2`, six alerts); `scripts/validate_block_2_4_live.py` with `--refresh-xray`; `live_core_e2e` Block 2.4 v2 contract checks. Evidence: [Session 12 audit](docs/audits/2026-05-29_block_2_4_session_12_live_demo_regression.md).

Category: Added

- **Block 2.4 Session 11 (institutional upgrade):** Shared Block 2.4 v2 product contract in `scripts/core_mvp_validation_contract.py`; `check_block_2_4_hidden_exposure` wired into `validate_core_mvp_block2_fixture_matrix.py`; `tests/test_core_mvp_block2_4_contract.py`; boundaries/contract tests use shared validator.

Category: Added

- **Block 2.4 Session 10 (institutional upgrade):** Matrix row coverage tests (`tests/test_block_2_4_matrix_coverage.py`, 69 parametrized ✅ v2 rows + deferred registry/limitation checks); `assert_block_2_4_product_contract` and golden Block 2.4 v2 surface test in `tests/test_portfolio_xray_contract.py`; expanded `contract_fingerprint` Block 2.4 fields; golden fixture regenerated.

Category: Added

- **Block 2.4 Session 09 (institutional upgrade):** Legacy PCA wire-time cross-ref on `correlation_concentration` via `build_block_2_4_legacy_enrichment` (`portfolio_pca` PC1 raw/residual, factor residual share); limitations point to `sections.hidden_risk_detector`; scores unchanged under `heuristic_v2`. Tests, spec §2.4.1, OUTPUTS note, and golden fixture updated.

Category: Added

- **Block 2.4 Session 08 (institutional upgrade):** Block 3 wire-time stress enrichment for `weak_hedge_behavior` (`confirmation_status`, `hedge_gap_analysis_v1` summary, worst-scenario hedge offset check, `factor_oos_mae_5y` evidence) and `duration_concentration` stagflation/commodity cross-ref; `build_block_2_4_stress_enrichment` wired from `build_portfolio_xray_v2`. Scores unchanged under `heuristic_v2`. Tests and spec §2.4.1 updated; golden fixture regenerated.

Category: Added

- **Block 2.4 Session 07 (institutional upgrade):** `tail_risk` scored signals from Block 2.2 — `var_95/99`, `downside_deviation`, `max_drawdown`, underwater persistence (`pct_time_underwater`, `longest_underwater_months`, `unrecovered_drawdown`), `count_drawdowns_gt_5`; vol instability evidence (`vol_of_vol`, `rel_vol_of_vol`, `rolling_volatility_12m_latest`). Tests and spec §2.4.1 updated; golden fixture regenerated.

Category: Added

- **Block 2.4 Session 06 (institutional upgrade):** `heuristic_v2` ruleset with confidence model v2 (factor penalties, cross-signal agreement, Block 2.2 warning propagation); High status capped to Medium when confidence is low; `weak_hedge_behavior` preliminary confidence cap. Tests and spec §2.4.1 updated; golden fixture regenerated.

Category: Added

- **Block 2.4 Session 05 (institutional upgrade):** Factor concentration sub-signals from Block 2.3 (`factor_variance_contribution`, `factor_risk_ranking`, `production_factor_confidence`, `production_factor_betas_5y`, `factor_beta_stability`, `kalman_current_betas`, supplemental `beta_inf`/`beta_usd`/`beta_cmd`/`beta_vix`/`beta_rr`/`beta_us_growth`) distributed across alerts; evidence-only under `heuristic_v1`. Tests and spec §2.4.1 updated.

Category: Added

- **Block 2.4 Session 04 (institutional upgrade):** Block 2.2 exports `correlation_breakdown.avg_pairwise_correlation`; Block 2.4 wires lowest-pair / average / `lack_of_diversifying_pairs` evidence on `correlation_concentration` and `equity_like_high_correlation_pairs` on `hidden_equity_beta` (evidence-only, `heuristic_v1` scores unchanged). Removed `avg_pairwise_correlation` from blocked-upstream registry. Tests and spec §2.2.1 / §2.4.1 updated.

Category: Added

- **Block 2.4 Session 03 (institutional upgrade):** Mandatory `contributing_assets[]` (max 3) per alert from Block 2.1 `by_asset` + wire-time `taxonomy_rows`; `portfolio_xray.py` passes taxonomy into `build_block_2_4_hidden_exposure`. Tests and spec §2.4.1 updated.

Category: Added

- **Block 2.4 Session 02 (institutional upgrade):** Taxonomy/currency sub-signals from Block 2.1 `concentration_flags` and `by_currency`; `investor_currency_mismatch` evidence on `correlation_concentration`; equity/risk-on evidence on `hidden_equity_beta`. Tests extended; spec §2.4.1 updated.

Category: Fixed

- **Block 2.4 Session 01 (institutional upgrade):** `correlation_concentration.duplicate_exposure_weight` now reads Block 2.1 `combined_weight` / `combined_weight_pct`; per-alert `limitations[]` and `confidence_reason`; `diagnostics_meta.blocked_upstream_fields` scaffold; duplicate group evidence rows. Tests in `tests/test_block_2_4_hidden_exposure.py`; spec §2.4.1 updated.

Category: Added

- **Stock Batch 1 pipeline:** Index-based controlled US stock expansion — `src/stock_batch_ingestion.py`, `scripts/build_stock_batch1.py`, merge path `--stock-batch-dir` on `scripts/merge_draft_universe.py`; production `index_membership` extended to `SP500` / `R1000` / `R3000`; tests `tests/test_stock_batch_ingestion.py`; spec updates in `universe_ingestion_spec.md` and `stock_universe_spec.md`.

Date: 2026-05-28

Category: Added

- **Asset taxonomy onboarding:** Cursor agent
  `.cursor/agents/asset-taxonomy-stress-classification-agent.md`,
  [asset_taxonomy_onboarding_spec.md](docs/specs/asset_taxonomy_onboarding_spec.md),
  `src/taxonomy_stress_blocks.py`, `scripts/taxonomy_onboard_report.py`,
  `tests/test_taxonomy_onboard_report.py`.

- **Core MVP historical stress replay (Session 7):** Live acceptance on subject
  `stress_report.json`; [acceptance audit](docs/audits/2026-05-28_core_mvp_historical_stress_replay_acceptance_audit.md);
  gate `scripts/verify_core_mvp_historical_stress_replay.py`; ExecPlan closed.

- **Core MVP historical stress replay (Session 6):** Documentation sync — `DEC-2026-05-28-001`,
  `stress_lab_layer_spec.md`, `stress_testing_spec.md` §9.4, `OUTPUTS.md`, `TESTING.md`.

- **Core MVP historical stress replay (Session 5):** Contract tests cases A–D on replay and Block
  3.2 merge (`tests/test_core_mvp_historical_stress_replay_contract.py`); Block 3.2 copies
  `episode_start` / `episode_end` from replay.

- **Core MVP historical stress replay (Session 4):** English `diagnosis_summary_en` templates on
  replay episodes (`format_episode_diagnosis_summary_en`); Block 3.2 uses replay narrative when
  `portfolio_level_result_available` is false; `data_trust_summary` prefers replay diagnosis text.

- **Core MVP historical stress replay (Session 3):** Wired `historical_stress_replay_v1` on
  portfolio-first diagnostic runs (`run_report.py`); Block 3.2 `historical_episodes[]` merges replay
  fields; partial replay omits portfolio loss/DD. Tests: `tests/test_stress_results_historical_replay_contract.py`.

- **Core MVP historical stress replay (Session 2):** `build_historical_stress_replay_v1` and
  `build_episode_replay` in `src/core_mvp_historical_stress_replay.py` (direct history only;
  portfolio loss/DD only when all risk positions covered). Tests:
  `tests/test_core_mvp_historical_stress_replay.py`.

- **Core MVP historical stress replay (Session 1):** Normative spec
  [docs/specs/core_mvp_historical_stress_replay_spec.md](docs/specs/core_mvp_historical_stress_replay_spec.md)
  (direct history only; no proxies in Core MVP). New module
  `src/core_mvp_historical_stress_replay.py` with episode registry, `min_coverage_ratio` 0.45,
  and direct-coverage helpers. `config/historical_stress_proxy_map.yml` labeled Advanced/Legacy only.
  Tests: `tests/test_core_mvp_historical_stress_replay_config.py`.

Date: 2026-05-27

Category: Changed

- **Block 2.3 Core MVP upgrade (Sessions 2–7, product surface):** Extended
  `block_2_3_factor_exposure` with `factor_betas_3y`, `factor_signal_confidence` (HAC→OLS fallback,
  no raw p/t in product JSON), `factor_kalman_uncertainty`, `factor_beta_stability` (3Y/5Y/10Y point
  betas only), and narrative `factor_exposure_summary` (`factor_highlights`, `main_caveat`). Upstream
  `factor_betas_3y` / `factor_regression_3y` in `run_report.py` and `run_optimization.py`. Fixture-matrix
  Block 2.3 validator and golden `portfolio_xray_golden_v2.json` updated. Full regression package remains
  in `stress_report.json` only ([portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §2.3.1).

- **Kalman weekly path + real cash:** `_portfolio_factor_weekly_ols_rows` no longer downloads
  real-cash labels (e.g. `Cash USD`) via yfinance; cash receives zero weekly returns in-panel.
  Hardened `fetch_daily` for duplicate/MultiIndex columns. Block 2.3 maps
  `factor_betas_kalman_error` to precise unavailable reasons. Fixture-matrix validators use
  `scripts/core_mvp_validation_contract.py` (Core MVP rollup vs optional diagnostics).

- **Block 3.3 Hedge Gap — eighth protection area:** Added `recession_severe_protection` →
  `recession_severe` to `BLOCK_3_3_RISK_SCENARIO_MAP` (`src/hedge_gap_analysis_block.py`) so
  `hedge_gap_analysis_v1.by_risk_type` emits offset coverage and hurt/helped fields for severe
  recession alongside the existing seven mappings. Scorecard `main_hedge_gap` / offset summary
  already select the weakest ratio across all rows and now include severe recession when it is
  the weakest. Updated [hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md),
  [stress_testing_spec.md](docs/specs/stress_testing_spec.md), fixture-matrix audit FXM-004, and
  hedge-gap contract tests (`n_risk_types` = 8).

- **Block 2.2 correlation breakdown:** Passed the runtime primary-window correlation matrix into
  Portfolio X-Ray / Block 2.2 directly, so JSON-only `site_api` runs can populate top high/low
  correlation pairs without writing CSV solely for this block. CSV references remain supported for
  full/export profiles and legacy reloads.

- **Analysis-subject Kalman diagnostics:** Kept candidate `lightweight_comparison` reports on the
  fast skip path, but enabled Kalman factor beta diagnostics for product-facing `analysis_subject`
  JSON bundles (`site_api` / `core_json`). This fixes the misleading Core MVP Block 2.3
  `kalman_module_not_available` outcome for current-portfolio diagnostics when factor rows are
  available.

- **Credit factor 10Y fallback:** Added a disclosed fallback for the credit spread factor:
  primary FRED `BAMLH0A0HYM2` HY OAS remains first choice, but when its history is too short
  for the requested factor window the factor matrix uses FRED `BAA10Y` as a longer-history
  spread proxy. Factor diagnostics now expose `fallback_used`, `primary_source`, and
  `fallback_reason`; future data work should review a better long-history HY/OAS source.

- **Core MVP Runtime Integration and Entrypoint Audit (Sessions 1–7, closed):** Locked
  portfolio-first runtime contract (`run_portfolio_review.py` default = diagnosis-only;
  `--candidates` = one-candidate product path; batch/full = research/advanced). Added ExecPlan
  [core_mvp_runtime_integration_and_entrypoint_audit_plan.md](docs/exec_plans/core_mvp_runtime_integration_and_entrypoint_audit_plan.md),
  legacy-runtime doc isolation (README/OUTPUTS/operator guide), boundary regressions
  (`tests/test_core_mvp_blocks_1_3_boundaries.py`, materialization E2E smoke), and live canonical
  acceptance in isolated temp output (`VOO/QQQ/TLT/GLD/Cash USD`).

- **Core MVP Blocks 1-3 cleanup Session 6:** Completed final live portfolio-first acceptance run
  for the cleanup plan. Fresh `Main portfolio/analysis_subject` outputs passed the JSON acceptance
  probe for Block 1 minimal input, Block 2 product keys 2.1-2.6, Block 3 product keys, diagnostic
  stress raw-field cleanliness, and Scenario Library sidecar/meta alignment. Added acceptance audit:
  [docs/audits/2026-05-27_core_mvp_blocks_1_3_cleanup_acceptance_audit.md](docs/audits/2026-05-27_core_mvp_blocks_1_3_cleanup_acceptance_audit.md).
  Targeted Core MVP suite passed; full repository pytest currently has 9 failures outside this
  cleanup acceptance surface.

- **Core MVP Blocks 1-3 cleanup Session 5:** Aligned source documentation and comments with the
  cleaned Core MVP boundaries: minimal Block 1 product input contract, Block 2 product blocks 2.1-2.6
  over `legacy_summary`, diagnostic-mode Stress Lab raw-field behavior, and Scenario Library
  `scenario_library_meta` + sidecar artifact pattern. No generated artifacts were hand-edited.

- **Core MVP Blocks 1-3 cleanup Session 1:** Added `core_mvp_input_surface` on `analysis_setup_v1`
  and `core_mvp_input_contract` on `input_assumptions_v1` so Block 1 exposes a clean Core MVP input
  contract (tickers, allocation, investor currency) while retaining mandate/client/liquidity fields
  as legacy/advanced disclosure only. Real-cash behavior unchanged.

- **Core MVP Blocks 1-3 cleanup Session 2:** Marked `portfolio_xray.json.legacy_summary` as
  legacy/report-formatter compatibility (`_scope.product_surface=false`), removed the old
  `mandate_gate` verdict field from live builds in favor of legacy compatibility metadata, and
  corrected the Core MVP Block 2 comment to Blocks 2.1-2.6. Product-facing Blocks 2.1-2.6 unchanged.

- **Core MVP Blocks 1-3 cleanup Session 3:** In `loss_gate_mode=diagnostic`, raw Stress Lab evidence
  rows no longer emit mandate fields (`pass`, `loss_ok`, `diagnostic_code(s)`). Legacy mandate mode
  keeps those fields gated behind `loss_gate_mode=mandate`; Block 3 product keys remain unchanged.

- **Core MVP Blocks 1-3 cleanup Session 4:** Added consolidated regression coverage for Core MVP
  Blocks 1-3 boundaries (`tests/test_core_mvp_blocks_1_3_boundaries.py`): minimal Block 1 input
  contract + real cash, clean Block 2 product blocks, clean Block 3 diagnostic raw/product outputs,
  and gated legacy mandate stress mode.

- **Block 3.4 Current Portfolio Stress Scorecard MVP:** Added a new Core MVP diagnostic-only product key
  `current_portfolio_stress_scorecard_v1` on `stress_report.json`, built as an adapter over Blocks
  3.1–3.3 (`stress_results_v1` + `hedge_gap_analysis_v1`). Wired it in `src/stress.py`, `run_report.py`,
  and `run_optimization.py`; added contract tests (`tests/test_current_portfolio_stress_scorecard_v1_contract.py`).
  Decision recorded as `DEC-2026-05-27-003`.

- **Block 3.3 Hedge Gap Analysis MVP (Session 07, tests):** Extended `tests/test_hedge_gap_analysis_v1_contract.py`
  and `tests/test_stress_diagnostic_mode.py` for `hedge_gap_analysis_v1` diagnostic-mode coverage,
  activated the Block 3.3 regression bundle in `TESTING.md`, and recorded this session in the ExecPlan
  without changing runtime hedge-gap behavior.

- **Block 3.3 Hedge Gap Analysis MVP (Session 02, scaffold):** Added
  `src/hedge_gap_analysis_block.py` (`build_hedge_gap_analysis_v1`, `empty_hedge_gap_analysis_v1`,
  `attach_hedge_gap_analysis_v1` stub, `BLOCK_3_3_RISK_SCENARIO_MAP` with seven risk types) and
  `tests/test_hedge_gap_analysis_v1_contract.py`. Placeholder `by_risk_type[]` rows only; no
  `run_stress` wiring until Session 05.

- **Block 3.3 Hedge Gap Analysis MVP (Session 01, docs):** Product contract
  `hedge_gap_analysis_v1` on `stress_report.json` (contribution-based offset coverage, seven
  synthetic-linked risk types, diagnostic-only). Stress Lab Core MVP renumbered to 3.3 Hedge Gap /
  3.4 Scorecard; simulator and crisis replay marked deferred/advanced. Docs:
  [hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md),
  [stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md),
  [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §12.2.2,
  [PRODUCT.md](PRODUCT.md) §4.3.3; `DEC-2026-05-27-002`. No runtime code yet.

- **Block 3.2 Stress Results MVP (Session 08, closure):** Live portfolio-first proof on root
  `config.yml` — `Main portfolio/analysis_subject/stress_report.json` ships `stress_results_v1`
  (8 synthetic + 5 historical rows, `loss_gate_mode: diagnostic`, envelope worst synthetic
  `recession_severe` / worst historical `2022` aligned with `stress_conclusions`). Acceptance:
  [docs/audits/2026-05-27_block_3_2_stress_results_acceptance_audit.md](docs/audits/2026-05-27_block_3_2_stress_results_acceptance_audit.md);
  ExecPlan **Completed**; Block 3.2 pytest bundle **75 passed**.

- **Block 3.2 Stress Results MVP (Session 07, tests):** Contract and regression closure for
  `stress_results_v1` on `stress_report.json` — builder contract tests
  (`tests/test_stress_results_block_contract.py`), diagnostic-mode Block 3.2 gates
  (`tests/test_stress_diagnostic_mode.py`), scenario-library alignment
  (`tests/test_stress_scenario_coverage_contract.py`), Stress Lab governance bundle + dedicated
  Block 3.2 bundle in [TESTING.md](TESTING.md); live core E2E requires `stress_results_v1`.
  Implementation Sessions 02–06 delivered builder, wiring, and downstream mirror.

Date: 2026-05-26

Category: Changed

- **Core MVP mandate boundary**: portfolio-first Block 1–3 no longer use client mandate/profile
  targets for product-facing pass/fail. Stress Lab adds `loss_gate_mode=diagnostic` for
  `analyze_current_weights` (status ok/warning/insufficient_data; no row pass/loss_ok vs MaxDD).
  Legacy `loss_gate_mode=mandate` + DIAG_* preserved for optimization reports. Docs: `PRODUCT.md`,
  `input_assumptions_spec.md`, `stress_testing_spec.md` §0, `stress_lab_layer_spec.md`, `SPEC.md`.

Category: Changed

- **Block 3.1 Scenario Library — official product definition**: fixed active historical
  (`dotcom`, `2008`, `2020`, `2022`, `banking_2023`) and synthetic (eight `*_shock` +
  `recession_severe`) sets documented in [stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md)
  §3.1, [scenario_library_spec.md](docs/specs/scenario_library_spec.md), `PRODUCT.md` §4.3.1,
  `GLOSSARY.md`, `SPEC.md`; cross-ref in [stress_testing_spec.md](docs/specs/stress_testing_spec.md)
  §2; ID registry comments in `src/scenario_library.py`. No new scenarios; IDs unchanged in code.

Category: Changed

- **Block 2.6 Portfolio Weakness Map MVP closed** (ExecPlan Sessions 00–08,
  `DEC-2026-05-26-006`): product-facing `block_2_6_portfolio_weakness_map` on
  `portfolio_xray.json` aggregates Blocks 2.1–2.5 into nine pre-stress risk hypotheses
  (0–100 score, severity, evidence, `next_tests`); excludes stress PnL/attribution;
  legacy `sections.weakness_map` preserved. Evidence:
  [acceptance audit](docs/audits/2026-05-26_block_2_6_portfolio_weakness_map_acceptance_audit.md);
  live demo rates_up **65** Medium, equity_crash **36** Low; pytest **35 passed**;
  `validate_one_candidate_demo.py` **PASS**.

Date: 2026-05-26

Category: Changed

- **Block 2.5 Risk Budget View MVP closed** (ExecPlan Sessions 00–08,
  `DEC-2026-05-26-005`): product-facing `block_2_5_risk_budget_view` on
  `portfolio_xray.json` compares capital weights to RC_vol, top1/top3 RC, risk
  overweight/underweight lists, and taxonomy bucket RC; excludes stress PnL;
  legacy `sections.risk_budget_view` preserved. Evidence:
  [acceptance audit](docs/audits/2026-05-26_block_2_5_risk_budget_acceptance_audit.md);
  live demo SCHD top1 RC 19.5%, SLV +9.5 pp risk-overweight; pytest **44 passed**;
  `validate_one_candidate_demo.py` **PASS**.

Date: 2026-05-26

Category: Changed

- **Block 2.5 Risk Budget View product contract (Session 01, docs):** Core MVP extended to Blocks
  2.1–2.5; normative §2.5.1 `block_2_5_risk_budget_view` in
  [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md); archetype
  renumbered to §2.6 (legacy only). Updated [portfolio_xray_layer_spec.md](docs/specs/portfolio_xray_layer_spec.md),
  [SPEC.md](SPEC.md), [OUTPUTS.md](OUTPUTS.md), [DECISIONS.md](DECISIONS.md) (DEC-2026-05-26-005),
  [GLOSSARY.md](GLOSSARY.md). Implementation Sessions 02–05 pending.

Date: 2026-05-26

Category: Changed

- **Full pytest suite contract drift registered (6 failures):** post–Block 2.4 full run
  (1037 passed / 6 failed) failures tracked as separate tech debt **KI-2026-05-26-001** … **006** in
  [KNOWN_ISSUES.md](KNOWN_ISSUES.md) and [TESTING.md](TESTING.md); not Block 2.4 regressions.

Date: 2026-05-26

Category: Planning

- **Block 2.5 Risk Budget View MVP ExecPlan (Session 00):** Active plan
  [2026-05-26_block_2_5_risk_budget_view_plan.md](docs/exec_plans/2026-05-26_block_2_5_risk_budget_view_plan.md);
  audit confirms legacy `sections.risk_budget_view` (with stress fields) and no
  `block_2_5_risk_budget_view` yet; product Block 2.5 = risk budget (archetype stays legacy section).

Date: 2026-05-26

Category: Changed

- **Portfolio Archetype Classification (Block 2.5) demoted from Core MVP docs:** product diagnosis
  remains Blocks 1 + 2.1–2.4 only; `sections.portfolio_archetype` stays on full X-Ray builds for
  legacy/formatters; no `block_2_5_*` module. Specs: [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §2.5,
  [portfolio_xray_layer_spec.md](docs/specs/portfolio_xray_layer_spec.md), [SPEC.md](SPEC.md).

Date: 2026-05-26

Category: Changed

- **Block 2.4 Hidden Exposure / Hidden Risk Detector MVP added**:
  product-facing `block_2_4_hidden_exposure` on `portfolio_xray.json` reads completed
  Blocks 2.1, 2.2, and 2.3 only, emits six structured rule-based alerts with `heuristic_v1`
  scoring/evidence, keeps Weak Hedge Behavior preliminary without Stress Lab, and preserves legacy
  `sections.hidden_risk_detector`.

Date: 2026-05-26

Category: Changed

- **Block 2.3 Factor Exposure / Factor Sensitivity MVP added** (`DEC-2026-05-26-004`):
  product-facing `block_2_3_factor_exposure` on `portfolio_xray.json` adapts existing
  `stress_report` factor diagnostics only, validates production factor/beta naming, degrades missing
  fields to partial/unavailable with warnings, and stays separate from Stress Lab calculations.

Date: 2026-05-26

Category: Fixed

- **Block 2.2 drawdown_structure wiring:** `build_block_2_2_portfolio_metrics` now reads
  `drawdown_structure` from `portfolio_analytics` when the top-level snapshot key is absent (live
  lightweight path). Extended `drawdown_diagnostics` fields populate on live X-Ray; MDD/TTR unchanged.
  Evidence: [bugfix audit](docs/audits/2026-05-26_block_2_2_drawdown_wiring_bugfix.md); **6** Block 2.2
  tests passed; live demo `pct_time_underwater` **0.567**, counts **4 / 1 / 0**.

Date: 2026-05-26

Category: Changed

- **Block 2.2 Portfolio Metrics / Risk Diagnostics MVP closed** (ExecPlan Sessions 01–08,
  `DEC-2026-05-26-003`): product-facing `block_2_2_portfolio_metrics` on
  `analysis_subject/portfolio_xray.json` for diagnosis and one-candidate runs; live demo
  (`config.yml` 10Y: CAGR 9.9%, vol 9.6%, Sharpe 0.799, MDD -19.8%, beta 0.513); real-cash
  fixture proof via pytest. Evidence:
  [acceptance audit](docs/audits/2026-05-26_block_2_2_portfolio_metrics_acceptance_audit.md);
  closure pytest **48 passed**; bundle/runtime **16 passed**; `validate_one_candidate_demo.py` PASS.

Date: 2026-05-26

Category: Changed

- **Block 2.1 Asset Allocation MVP closed** (ExecPlan Sessions 01–08, `DEC-2026-05-26-002`):
  product-facing `block_2_1_asset_allocation` on `analysis_subject/portfolio_xray.json` for diagnosis
  and one-candidate runs; live demo (`config.yml`: SCHD top1 17.0%, top3 46.0%); real-cash fixture
  proof (5% `Cash USD`, SCHD 16.15%, top3 43.7%). Evidence:
  [acceptance audit](docs/audits/2026-05-26_block_2_1_asset_allocation_acceptance_audit.md);
  closure pytest **44 passed**; `validate_one_candidate_demo.py` PASS.

Date: 2026-05-26

Category: Changed

- **Block 2.1 pipeline integration** (ExecPlan Session 07): `analysis_subject/portfolio_xray.json`
  on portfolio-first materialize paths includes `block_2_1_asset_allocation`; `output_manifest.json`
  documents nested Block 2.1 via `subject_diagnostics_contract`; live/offline gates and
  `tests/test_block_2_1_pipeline_integration.py`.

Date: 2026-05-26

Category: Changed

- **Block 2.1 Input Layer connection** (ExecPlan Session 04): `resolved_analysis_weights` in
  `src/analysis_setup.py`; Portfolio X-Ray and legacy `cash_weight` use `analysis_portfolio.weights`
  and real-cash holdings (not `cash_proxy_ticker`). Regression on `minimal_usd_with_cash.yml`.

Date: 2026-05-26

Category: Changed

- **Block 2.1 Asset Allocation builder shipped** (ExecPlan Session 03): `src/block_2_1_asset_allocation.py`
  builds `block_2_1_asset_allocation` on `portfolio_xray.json`; real-cash synthetic taxonomy;
  concentration and duplicate-exposure flags. Tests: `tests/test_block_2_1_asset_allocation.py`.

Date: 2026-05-26

Category: Changed

- **Block 2.1 Asset Allocation product contract specified** (`DEC-2026-05-26-002`): Added
  `portfolio_xray_diagnostics_spec.md` §2.1.1 (`block_2_1_asset_allocation` JSON contract) and §2.1.2
  (`ALLOCATION_CONCENTRATION_THRESHOLDS`). Implementation in `src/block_2_1_asset_allocation.py` follows
  ExecPlan Session 03+. Docs: layer spec, OUTPUTS Block 2 row.

Date: 2026-05-26

Category: Changed

- **Input Layer MVP Migration closed and frozen** (`DEC-2026-05-26-001`): Core MVP three-field
  input, real cash, `input_surface` / `field_tiers` export; ExecPlan Sessions 01–10 complete.
  Live verification: `run_portfolio_review.py --candidates equal_weight` + `validate_one_candidate_demo.py`
  PASS. Contract freeze in [input_assumptions_spec.md](docs/specs/input_assumptions_spec.md);
  evidence [acceptance audit](docs/audits/2026-05-26_input_layer_mvp_acceptance_audit.md) §5.
  Active product focus moves to downstream Blocks 2–5 / product bundle layers (not more input redesign).

Date: 2026-05-24

Category: Changed

- Performance Wave 2 **closed** Session 8 (`RM-983`): `core_fast_parallel` E2E **210.7 s** warm cache
  (target ≤ 300 s; baseline `core_v1` 542.5 s). Extended
  `scripts/blocks_1_5_e2e_timing_audit.py` with `core_fast_parallel` scenario and acceptance gate;
  post-wave table in [E2E timing audit](docs/audits/2026-05-24_blocks_1_5_e2e_timing_audit.md).
  Parity bundle **138 passed**; `verify_docs.py` OK.

Date: 2026-05-24

Category: Changed

- Performance Wave 2 Session 7 (`RM-983`): `--mode core` routes to factory profile `core_fast`
  (parallel lightweight reports by default, `ReviewRunContext` on factory via
  `run_candidate_factory.py`); `--no-parallel-lightweight-reports` on `run_portfolio_review.py`;
  regression sequential menu via `--candidate-profile core_v1`. Tests:
  `tests/test_portfolio_review_workflow.py`; live core E2E expects `core_fast`.

Date: 2026-05-24

Category: Added

- Performance Wave 2 Session 5 (`RM-983`): core `analysis_subject` materialization uses
  `lightweight_comparison` + `ReviewRunContext` (`run_materialize_analysis_subject_report`,
  `run_report.py --review-mode core --use-review-run-context`, portfolio review diagnosis step);
  `--mode full` uses full report profile without shared context. Tests:
  `tests/test_analysis_subject_materialization.py`, `tests/test_portfolio_review_workflow.py`.

Date: 2026-05-24

Category: Added

- Performance Wave 2 Session 4 (`RM-983`): `lightweight_comparison` skips 3Y/5Y tail-risk loop
  iterations and writes `snapshot_10y.json` only (`snapshot_index.json` lists 10Y only); `full_report`
  unchanged (3Y/5Y/10Y + assets). Tests: `tests/test_report_profile.py` **6 passed**.

Date: 2026-05-24

Category: Added

- Performance Wave 2 Session 3 (`RM-983`): `portfolio_pca_diagnostics_with_weekly_frames` in
  `src/stress_factors.py`; `run_report.py` PCA block reuses factory/review `weekly_factor_frames`
  (no per-report `download_all` when frames cover tickers; legacy path unchanged as fallback).
  Tests: `tests/test_candidate_run_context.py` **25 passed** (`download_all` skip + PCA parity).

Date: 2026-05-24

Category: Added

- Performance Wave 2 Session 2 (`RM-983`): macro indicator panel cached on `ReviewRunContext`
  (`load_review_macro_panel`, `macro_panel_fetch_window`); `macro_regime_diagnostics_with_panel` in
  `src/stress_factors.py`; `run_report.py` macro block uses cached panel when `ReviewRunContext` is
  present; candidate factory passes full review context to report workers via `report_run_context`.
  Tests: `tests/test_candidate_run_context.py` **23 passed** (fetch-once + macro/snapshot parity).

Date: 2026-05-24

Category: Added

- Performance Wave 2 Session 1 (`RM-983`): `ReviewRunContext` (`review_run_context_v1`) and
  `prepare_review_run_context` in `src/candidate_run_context.py`; `coerce_factory_run_context` for
  report/factory entrypoints; optional `shared_run_context` on `run_candidate_factory`. Macro/PCA cache
  slots reserved; no review workflow wiring yet. Tests: `tests/test_candidate_run_context.py` **20 passed**.

Date: 2026-05-24

Category: Added

- Performance Wave 2 Session 6 (`RM-983`): factory profile `core_fast` (same six candidate ids as
  `core_v1`) with parallel Phase 2 lightweight reports enabled by default (4 workers);
  `resolve_parallel_lightweight_report_options`; CLI `--no-parallel-lightweight-reports`;
  `core_v1` remains sequential. Tests: `tests/test_candidate_factory.py` **48 passed**.

Date: 2026-05-24

Category: Added

- Performance Wave 2 Session 0 (`RM-983`): [ExecPlan](docs/exec_plans/2026-05-24_blocks_1_5_performance_wave2_plan.md)
  Active; baseline locked from [E2E timing audit](docs/audits/2026-05-24_blocks_1_5_e2e_timing_audit.md)
  (`core_v1` E2E **542.5 s**); `core_fast` contract stubs in
  [candidate_factory_spec.md](docs/specs/candidate_factory_spec.md) and
  [portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md); register updates in
  [exec_plans/README.md](docs/exec_plans/README.md) and [ROADMAP.md](docs/ROADMAP.md). No runtime code
  changes (Sessions 1–8 pending).

Date: 2026-05-24

Category: Added

- Core/full artifact confusion remediation Session 06 closure (`RM-1106`): remediation status in
  [confusion audit](docs/audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md);
  ExecPlan
  [2026-05-23_core_full_artifact_documentation_confusion_plan.md](docs/exec_plans/2026-05-23_core_full_artifact_documentation_confusion_plan.md)
  marked **Completed**; [exec_plans/README.md](docs/exec_plans/README.md) Active pointer cleared;
  [audits/README.md](docs/audits/README.md) confusion audit row → Historical.

Date: 2026-05-24

Category: Added

- Core/full artifact confusion remediation Session 05 (`RM-1105`): [GLOSSARY.md](GLOSSARY.md) Blocks 1–5
  vs decision package and factory/comparison evidence terms; factory vs comparison scope note in
  [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md); cross-links in
  [portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md); walkthrough notes
  in both Blocks 1–5 walkthrough audits; [SPEC.md](SPEC.md) artifact-boundary pointer.

Date: 2026-05-24

Category: Added

- Core/full artifact confusion remediation Session 04 (`RM-1104`): [ARCHITECTURE.md](ARCHITECTURE.md)
  Candidate Flow baseline (`analysis_subject`; legacy `policy` row optional); [.cursor/rules/portfolio_run_scope.mdc](.cursor/rules/portfolio_run_scope.mdc)
  portfolio-first PDF default vs legacy rebuild scope; [AGENTS.md](AGENTS.md) Main Commands clarify
  default review does not refresh `pdf files/` (`--with-pdf` / `--legacy-full-pdf`).

Date: 2026-05-24

Category: Added

- Core/full artifact confusion remediation Session 03 (`RM-1103`): command matrix split in
  [OUTPUTS.md](OUTPUTS.md) (core `core_v1` review vs standalone/full `default_v1` factory); §20 disk
  caveat in [Blocks 1–5 verification report](docs/audits/2026-05-22_blocks_1_5_verification_report.md);
  [README.md](README.md) PDF one-liner and aligned summary table; [audits/README.md](docs/audits/README.md)
  Blocks 1–5 row updated.

Date: 2026-05-24

Category: Added

- Core/full artifact confusion remediation Session 02 (`RM-1102`): portfolio-first operator checklist
  in [WORKFLOW.md](WORKFLOW.md); [operational_runbook.md](docs/operational_runbook.md) §8 cross-links
  to checklist and §0.1; [OUTPUTS.md](OUTPUTS.md) Read this first links to WORKFLOW + §8.

Date: 2026-05-23

Category: Added

- Core/full artifact and documentation confusion remediation Session 01 (`RM-1101`): P0 Read this first
  in [OUTPUTS.md](OUTPUTS.md) and runbook §0.1.

Category: Added

- Core/full artifact and documentation confusion remediation Session 00 (`RM-1100`): active ExecPlan
  [2026-05-23_core_full_artifact_documentation_confusion_plan.md](docs/exec_plans/2026-05-23_core_full_artifact_documentation_confusion_plan.md)
  from audit
  [2026-05-23_core_full_artifact_documentation_confusion_audit.md](docs/audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md);
  docs-only Sessions 03–06 pending (command matrix, ARCHITECTURE, glossary, closure).

Category: Added

- Site/API Default Output Refactor Sessions 0–7: `src/output_policy.py` with `site_api` default;
  `output_manifest.json`; presentation exports gated; entrypoint defaults on report, review, factory,
  optimization; Session 07 closure
  (`docs/audits/2026-05-23_site_api_default_output_session07_closure_report.md`); verification bundle
  **38 passed**.

Category: Added

- Candidate Factory Shared Evidence Sessions 1–5 (RM-982): factory `CandidateRunContext` v2–v5
  (invariant asset metrics/corr/cov, extended betas, weekly factor frames, prepared synthetic stress);
  optional `report_timing` blocks and factory aggregate; Session 6 closure audit
  (`docs/audits/2026-05-23_candidate_factory_shared_evidence_session06_timing_audit.md`);
  full-menu sequential `report_seconds` **−28.1%** vs 1192.9 s baseline (below −35% goal);
  verification bundle **106 passed**; `scripts/shared_evidence_session06_timing_smoke.py`.

Date: 2026-05-22

Category: Fixed

- Candidate Factory Session 9: `prepare_candidate_run_context` passes `cli_lambda=None` to
  `resolve_robust_mv_lambda_for_baseline` (unblocks live `--execution-mode standard` factory runs);
  regression test in `tests/test_candidate_run_context.py`.

Category: Added

- Candidate Factory Parallel Reports Session 4: operator/source-of-truth docs now describe
  `--parallel-lightweight-reports`, `--lightweight-report-workers`, sequential fallback conditions,
  and `parallel_lightweight_report_summary` in factory run outputs.

- Candidate Factory Session 9: timing baseline audit
  `docs/audits/2026-05-22_candidate_factory_timing_baseline.md`; ExecPlan Sessions 0–9 marked
  Completed; verification bundle **102 passed** (factory/comparison/report_profile/run_context/manifest/compare_ew_rp/review).

Category: Added

- Candidate Factory Session 8: Phase 3 full report export (`--full-candidate-reports`,
  `--selected-candidates-for-full-report`) with `report_profile=full`; `final_only` PDF rebuild
  after Phase 3; KNOWN_ISSUES G4 operator guidance; tests in `tests/test_candidate_factory.py`.

Category: Fixed

- Candidate Factory Session 7: `run_compare_ew_rp.py` reads only numeric columns from `var_es_10y.csv` (skips `method` = `historical` and other metadata) so EW/RP compare and PDF rebuild no longer raise on tail-risk CSV layout; `tests/test_compare_ew_rp.py`.

Category: Changed

- Candidate Factory Session 6: `run_portfolio_review.py` forwards factory `--execution-mode standard` by default for core and full review (phased weights + lightweight_comparison); `--execution-mode legacy_full` for subprocess parity; tests in `tests/test_portfolio_review_workflow.py`.

Category: Added

- Candidate Factory Session 5: `{artifact_root}/candidate_manifest.json` (`candidate_manifest_v1`) with comparison readiness and optional `partial_failure`; factory `run_status` on `candidate_factory_run.json`; tests in `tests/test_candidate_manifest.py`.

Category: Added

- Candidate Factory Session 4: `src/candidate_run_context.py` with `CandidateRunContext` / `FactoryFactorStressInputs`; factory `fast`/`standard` modes reuse one monthly load and invariant factor/scenario inputs; `run_portfolio_report_for_weights(..., run_context=...)`; tests in `tests/test_candidate_run_context.py`.

Category: Added

- Candidate Factory Session 3: `report_profile` (`full` | `lightweight_comparison`) on `run_portfolio_report_for_weights`; factory `--execution-mode standard` Phase 2 emits compare-ready `snapshot_10y.json` and `stress_report.json` without HTML/PNG/commentary; tests in `tests/test_report_profile.py`.

Category: Added

- Candidate Factory Session 2: `src/candidate_weights.py` with in-process `build_candidate_weights` / `write_candidate_weights` for all sixteen registry families; factory `--execution-mode fast|standard` (Phase 1 weights only, default remains `legacy_full`).

Category: Changed

- `run_candidate_factory.py` and `candidate_factory_spec.md` document execution modes, report profiles, `candidate_weights_build.json`, and skip-existing semantics for `fast` vs `standard`.

---

## How To Use

- Add entries only for meaningful project changes: behavior, formulas, data flow, configs, commands, outputs, docs structure, source-of-truth rules, or user-facing workflows.
- Keep each bullet short: one change, one sentence, no implementation essay.
- Do not log every typo, formatting edit, generated-output refresh, or internal refactor with no project-facing effect.
- Link the owning document or module when it helps.
- When an item from [KNOWN_ISSUES.md](KNOWN_ISSUES.md) is fixed, remove it from active issues and add one short `Fixed` entry here if the fix is meaningful.
- For large changes, use this file as the summary and keep detailed rationale in an ExecPlan under `docs/exec_plans/`.

## Entry Format

Use date-based sections unless formal releases are introduced later.

```markdown
Date: YYYY-MM-DD

Category: Added

- Short change summary.

Category: Changed

- Short change summary.

Category: Fixed

- Short change summary.

Category: Removed

- Short change summary.
```

Omit empty categories.

## 2026-05-22

### Fixed

- Hardened the portfolio-first demo path: factor proxy failures now disclose available/missing
  factors, factor covariance returns an explicit unavailable reason instead of a Timestamp warning,
  and candidate factory summaries disclose rebuilt vs reused/resumed candidates.

### Added

- Candidate factory Session 1 runtime: `--pdf-mode` on `run_candidate_factory.py` (default `none`);
  `PORTFOLIO_SKIP_VARIANT_PDF` gating in per-candidate `run_*.py` via
  [src/variant_builder_runtime.py](src/variant_builder_runtime.py); per-step timing buckets and
  run-level `timing_summary` in `candidate_factory_run.json` / `.txt`.
- Active ExecPlan [docs/exec_plans/2026-05-22_candidate_factory_runtime_refactor_plan.md](docs/exec_plans/2026-05-22_candidate_factory_runtime_refactor_plan.md) (Session 0): phased candidate factory runtime refactor plan (weights vs report vs PDF); documentation only, no runtime behavior change yet.

- Interactive Brokers market data provider path: `src/data_ibkr.py`, `src/data_provider.py`,
  `market_data_provider`, provider-aware cache keys, `run_ibkr_market_data.py`, docs, and tests.

- Phase 17 Session 09 (`RM-1028`): Blocks 8–10 package truthfulness —
  `src/package_truthfulness.py`; decision package **Review scope (read first)** banner and JSON
  `package_truthfulness`; action plan `partial_candidate_menu_action_context` warning;
  `tests/test_package_truthfulness.py`, `tests/test_blocks_8_10_downstream_integration.py`.
- Phase 17 Session 08 (`RM-1027`): Blocks 6–7 downstream readiness —
  `docs/specs/downstream_decision_readiness_spec.md`, `src/downstream_decision_readiness.py`;
  guarded stress artifact load in `portfolio_health_score.py` and `robustness_scorecard.py`;
  `tests/test_downstream_decision_readiness.py`, `tests/test_blocks_6_7_downstream_integration.py`.
- Phase 17 Session 07 (`RM-1026`): review bundle disclosure — `src/review_bundle_context.py`;
  `candidate_comparison.json` → `review_bundle_context` (`review_bundle_fingerprint`, alignment,
  `mode_subject_consistency`, `user_summary_lines`); `input_assumptions` → `review_bundle_disclosure`
  and merged `data_trust_signals.user_summary_lines`; specs and `test_review_bundle_context.py`.
- Phase 17 Session 06 (`RM-1025`): factory vs comparison timestamp semantics —
  `comparison_rebuild_source` (`factory_then_compare` / `standalone`), in-memory factory handoff,
  factory JSON written before `--then-compare`, 120s standalone timing-skew tolerance when
  `analysis_end` and `config_fingerprint` match; tests and `candidate_comparison_spec.md` update.
- Phase 17 Session 05 (`RM-1024`): Block 1 ticker preflight — explicit `analysis_subject`
  tickers must exist in ETF or stock taxonomy (`preflight_explicit_analysis_subject_tickers`);
  config validation fails before report; legacy paths remain warn-only via
  `etf_universe_validation.json`.
- Phase 17 Session 04 (`RM-1023`): offline full-menu optimizer fair-comparison gate —
  `tests/optimizer_fair_comparison_fixtures.py`, `tests/test_optimizer_fair_comparison_full_menu.py`,
  golden `tests/fixtures/optimization_comparison_full_menu_fair_ready_golden_v1.json`; runbook §8.6
  rebuild guidance for on-disk optimizer artifacts.
- Phase 17 Session 03 (`RM-1022`): selection favoring guards —
  `candidate_eligible_for_favoring` in `src/optimization_readiness.py`; degraded rows and
  non-fair-ready optimizers excluded from `favored_candidate_id`; `partial_candidate_menu`
  warnings in selection, health score, and decision-package summary labels; specs and focused
  pytest coverage.
- Phase 17 Session 02 (`RM-1021`): live core E2E gate — `src/live_core_e2e.py`,
  `scripts/verify_live_core_e2e.py`, pytest marker `tests/test_blocks_1_5_live_core_e2e.py`
  (`--live-core` / `PORTFOLIO_LIVE_CORE_E2E=1`), offline validator
  `tests/test_live_core_e2e_validation.py`; documented in `TESTING.md` and
  `docs/operational_runbook.md`. Live run `verify_live_core_e2e.py --run` validated subject +
  comparison with `review_mode: core`.

### Changed

- Closed P17-G9 in `KNOWN_ISSUES.md` (Blocks 6–7 guarded handoff spec and implementation).
- Closed P17-G7 and P17-G8 in `KNOWN_ISSUES.md` (mode/subject interpretation and review bundle
  fingerprint via `review_bundle_context` / input trust lines).
- Closed P17-G6 in `KNOWN_ISSUES.md` (false `factory_evidence_status: stale` on same-run review).
- Closed P17-G5 in `KNOWN_ISSUES.md` (unknown tickers hard-rejected for explicit
  `analysis_subject`).
- Closed P17-G3 in `KNOWN_ISSUES.md` (fair-ready optimizer rows provable offline; operator refresh
  via `--no-skip-existing` documented).
- Closed P17-G1 in `KNOWN_ISSUES.md`; P17-G2 notes partial menu warnings until Session 09
  (`RM-1028`).
- Closed P17-G4 in `KNOWN_ISSUES.md` (live core proof is operator-gated; offline
  `test_blocks_1_5_mvp_smoke.py` remains default CI closure).

## 2026-05-22

### Added

- Phase 17 Session 10 (`RM-1029`): live full + resume E2E gate — `src/live_full_e2e.py`,
  `scripts/verify_live_full_e2e.py`, pytest marker `--live-full`, offline validators; Phase 17
  closure bundle in `TESTING.md`; runbook § live full.

### Changed

- Phase 17 Session 10 (`RM-1029`): Phase 17 wave **closed** — live full orchestrator proof
  (`review_mode: full`, 16 `default_v1` steps, `factory_evidence_status: current`); resume proof
  (`resumed_from_manifest: 16`); offline closure bundle **72 passed**; `verify_docs` OK; ExecPlan
  register Active cleared; `KNOWN_ISSUES.md` Phase 17 index marked closed.

## 2026-05-21

### Added

- Phase 17 Session 01 (`RM-1020`): post-deep-audit project memory — [Post-Deep-Audit Foundation Plan](docs/exec_plans/2026-05-21_post_deep_audit_foundation_plan.md), [Blocks 1–5 Deep Audit Snapshot](docs/audits/2026-05-21_blocks_1_5_deep_audit_snapshot.md), Phase 17 roadmap rows `RM-1021`–`RM-1029`, ExecPlan register Active pointer, Phase 17 gap index in `KNOWN_ISSUES.md`; documentation-only.

### Changed

- Blocks 1-5 MVP core reliability Session 09 (`RM-1018`): Phase 16 wave **closed** — offline
  acceptance bundle **125 passed**, `verify_docs` OK, dry-run core/full resume OK, live core
  subject materialization smoke refreshed `Main portfolio/analysis_subject/`; ExecPlan register
  and ROADMAP mark Phase 16 Done.

### Fixed

- Blocks 1-5 MVP core reliability Session 09: `tests/conftest.py` and direct
  `mvp_offline_fixtures` imports so offline MVP smoke tests are not broken by a third-party
  `tests` package in site-packages.

- Blocks 1-5 MVP core reliability Session 08 (`RM-1017`): documentation handoff — `README.md`,
  `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, and `docs/operational_runbook.md` now describe Blocks 1-5
  MVP core, portfolio-first core/full/resume commands, trust-signal outputs, factory-evidence
  boundaries, and offline acceptance without chat context; documentation-only.

### Added

- Blocks 1-5 MVP core reliability Session 07 (`RM-1016`): promoted data-quality and young-ETF trust
  signals in `stress_report.data_trust_summary`, `input_assumptions.data_trust_signals`, and
  `portfolio_xray.data_trust_signals`, with commentary/stress-commentary summary lines; no formula
  changes.

- Blocks 1-5 MVP core reliability Session 06 (`RM-1015`): added an offline
  `tests/test_blocks_1_5_mvp_smoke.py` gate covering a five-ticker explicit weighted subject
  through diagnostics, X-Ray, stress, current factory evidence, and comparison baseline checks.

- Blocks 1-5 MVP core reliability Session 05 (`RM-1014`): optimizer-backed comparison rows now
  explicitly degrade when optimizer methodology or quality evidence is missing, or when solver
  quality normalizes to `unknown`, keeping readiness disclosure visible.

- Blocks 1-5 MVP core reliability Session 04 (`RM-1013`): `run_portfolio_review.py` now supports
  `--resume-candidates`, passing factory `--resume` through the portfolio-first full-review path
  after interrupted candidate runs.

- Blocks 1-5 MVP core reliability Session 01 (`RM-1010`): active
  [ExecPlan](docs/exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md), ROADMAP Phase 16
  (`RM-1010`-`RM-1018`), ExecPlan register pointer, and active known issues for input validation,
  factory freshness, resumable full review, and optimizer readiness gaps; documentation-only.

- Block 5 governance Session 12 (`RM-1002`): Phase 15 wave closure — baseline snapshot closure
  section, ROADMAP Phase 15 **Done** (`RM-990`–`RM-1002`), ExecPlan and registers marked complete;
  Block 5 gap index in `KNOWN_ISSUES.md`; governance bundle **159 passed**, `verify_docs` OK.

- Block 5 governance Session 11 (`RM-1001`): golden contract fixtures
  (`legacy_policy_optimizer_run_metadata_golden_v1.json`,
  `candidate_optimizer_run_metadata_golden_v1.json`,
  `optimization_comparison_block5_golden_v1.json`), `tests/optimization_engine_golden_inputs.py`,
  `tests/test_optimization_engine_contract.py`; `TESTING.md` Block 5 bundle finalized.

- Block 5 governance Session 01 (`RM-991`): canonical
  [optimization_engine_layer_spec.md](docs/specs/optimization_engine_layer_spec.md) for Block 5.1–5.11
  roles, matrices, and boundaries (documentation only).

- Block 5 governance Session 10 (`RM-1000`): `candidate_comparison.json` rows for optimizer-backed
  candidates now include `construction_disclosure.optimization_readiness` with
  `fair_comparison_ready` and artifact checklist gates without changing optimizer formulas or
  comparison ranking.

- Block 5 governance Session 09 (`RM-999`): legacy and candidate optimizer metadata now disclose
  covariance methodology and Young ETF methodology, with compact human summaries in comparison and
  IPS TXT outputs, without changing covariance formulas or weights.

- Block 5 governance Session 08 (`RM-998`): legacy and candidate optimizer metadata now disclose
  estimator `analysis_end`, return-panel start/end/rows, and input fingerprints without changing
  optimizer formulas or weights.

- Block 5 governance Session 07 (`RM-997`): Robust Scenario now emits normalized SLSQP solver
  status and propagates it through candidate metadata, factory quality evidence, and comparison
  optimizer disclosure.

- Block 5 governance Session 06 (`RM-996`): optimizer fallback/failure quality now propagates
  through factory steps, comparison readiness, and Selection warnings so fallback is not ordinary
  clean optimization evidence.

- Block 5 governance Session 05 (`RM-995`): comparison rows now expose
  `construction_disclosure.optimizer_methodology` from upstream optimizer metadata without changing
  optimizer behavior.

- Block 5 governance Session 04 (`RM-994`): candidate optimizer
  `baseline_weights_metadata.json.optimizer_run_metadata` disclosure for Minimum Variance, Maximum
  Diversification, Minimum CVaR, and Robust Mean-Variance without changing optimizer behavior.

- Block 5 governance Session 03 (`RM-993`): legacy policy `run_result.json.optimizer_run_metadata`
  disclosure for objective, estimator/window, universe, bounds/caps, cash policy, solver/fallback,
  and release gate without changing optimizer behavior.

- Block 5 governance Session 02 (`RM-992`): **DEC-2026-05-21-001** target-only optimizer objective boundary and [optimization_engine_layer_spec.md](docs/specs/optimization_engine_layer_spec.md) appendix for Max Sharpe, drawdown, macro, stress-test, tax, and turnover concepts.

### Fixed

- Blocks 1-5 MVP core reliability Session 03 (`RM-1012`): candidate comparison now reports
  missing/stale factory evidence in `candidate_menu` and ignores stale factory `steps[]` as current
  row evidence.

- Blocks 1-5 MVP core reliability Session 02 (`RM-1011`): weighted current/model
  `analysis_subject` inputs now hard-fail material overallocations while partial weights remain
  explicit cash-remainder diagnostics.

## 2026-05-20

### Added

- Block 4 governance Session 11 (`RM-981`): **DEC-2026-05-20-003** concept registry boundary;
  [candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md) § Concept candidates not in registry;
  Phase 14 wave closure (baseline snapshot, methodology map verdict, registers); G9 / `KI-2026-05-20-007` closed.

- Block 4 governance Session 10 (`RM-980`): [operational_runbook.md](docs/operational_runbook.md) §8
  (factory exit codes, reason-code table, scenario playbooks); contextual `next_recommended_command` and
  richer `candidate_factory_run.txt` in [candidate_factory.py](src/candidate_factory.py); G4 operator
  playbook documented.

- Block 4 governance Session 09 (`RM-979`): resumable candidate factory — `candidate_factory_manifest.json`,
  `--resume` on `run_candidate_factory.py`, incremental manifest persistence per step, `resumed_from_manifest`
  summary field; closes RM-921 resumable scope and G5; [candidate_factory_spec.md](docs/specs/candidate_factory_spec.md).

- Block 4 governance Session 00 (`RM-970`): [Candidate Factory Methodology Map](docs/audits/2026-05-20_candidate_factory_methodology_map.md),
  [Candidate Factory Baseline Snapshot](docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md), active
  [Candidate Portfolio Factory Post-Audit Roadmap](docs/exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md),
  ROADMAP Phase 14 (`RM-970`–`RM-981`), TESTING.md governance bundle stub.

- Block 4 governance Session 01 (`RM-971`): documentation sync — G1–G10 gap index and eight active
  `KNOWN_ISSUES` entries mapped to Phase 14 `RM-972`–`RM-981`; [SPEC.md](SPEC.md) and [OUTPUTS.md](OUTPUTS.md)
  link methodology map, layer spec scaffold, and governance ExecPlan; `KI-2026-05-19-005` cross-ref G4/G5.

- Block 4 governance Session 08 (`RM-978`): golden contract tests —
  `tests/fixtures/candidate_factory_run_golden_v1.json`,
  `tests/fixtures/candidate_comparison_golden_v1.json`,
  `tests/candidate_factory_golden_inputs.py`,
  `tests/test_candidate_factory_contract.py`,
  `tests/test_candidate_comparison_contract.py`; Phase 14 governance bundle finalized in [TESTING.md](TESTING.md).

- Block 4 governance Session 07 (`RM-977`): robust paths disclosure — `src/candidate_robust_disclosure.py`,
  factory `robust_paths_disclosure` on robust suite steps, comparison `construction_disclosure.robust_paths`,
  operational runbook robust prerequisites; G8 / G10 and `KI-2026-05-20-005` / `006` closed.

- Block 4 governance Session 06 (`RM-976`): config fingerprint freshness — `candidate_config_fingerprint`
  on window snapshots, factory `config_fingerprint` / `stale_config` gating, comparison
  `stale_config_fingerprint` unavailable reason; G2 / `KI-2026-05-20-002` closed.

- Block 4 governance Session 05 (`RM-975`): [candidate_factory_layer_spec.md](docs/specs/candidate_factory_layer_spec.md)
  active handoff for Block 4.1–4.9 (workflow, artifacts, sub-block map, Phase 14 gap table); G7 closed.

- Block 4 governance Session 04 (`RM-974`): `construction_disclosure` on every
  `candidate_comparison.json` row — passthrough from `baseline_weights_metadata.json`, builder
  `summary.json`, policy/subject excerpts, and optional factory step; [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md) v1.3.

- Block 3 governance Session 11 (`RM-961` closure): Phase 13 wave closed — governance pytest bundle
  **90 passed**, `verify_docs` OK; baseline snapshot Session 11 section and G1–G10 table;
  [Stress Lab Methodology Governance Plan](docs/exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md)
  marked Completed; ROADMAP Phase 13 Done.

- Block 3 governance Session 10 (`RM-961` part 1): downstream integration — `crisis_replay_summary`
  on `snapshot_10y.stress_suite_results` and `candidate_comparison` `stress` blocks;
  `historical_methodology` mirror; commentary lines for methodology, crisis replay v2, hedge
  `by_risk_type`, and per-episode `return_method`; `tests/test_stress_downstream_integration.py`;
  G10 closed.

- Block 3 governance Session 09 (`RM-960`): optional `custom_shock_runs.json` audit trail
  (`custom_shock_runs_v1`) via `record_custom_shock_run` in [src/stress.py](src/stress.py); opt-in
  only (not written by `run_stress`); [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §12.3;
  [OUTPUTS.md](OUTPUTS.md); G9 closed.

- Block 3 governance Session 08 (`RM-959`): crypto/vol synthetic stress **proposal** and
  [docs/proposals/README.md](docs/proposals/README.md); [DEC-2026-05-20-002](DECISIONS.md) defers
  `crypto_shock` / `volatility_shock` in `run_stress` (no `SCENARIOS` changes);
  [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §2.3; methodology map G8 closed.

- Block 3 governance Session 07 (`RM-958`): handoff-grade
  [stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md) — provenance per sub-block 3.1–3.6,
  JSON contract index, Phase 13 session table; indexed in [SPEC.md](SPEC.md) and
  [docs/specs/README.md](docs/specs/README.md); methodology map G7 closed.

- Block 3 governance Session 06 (`RM-957`): crisis replay v2 — `time_to_recovery_months`,
  `recovered`, `asset_pnl_contrib_episode`, `top_loss_assets_episode` on `historical_episode_paths`;
  `crisis_replay_{episode}_asset_contrib.csv` export; [crisis_replay_spec.md](docs/specs/crisis_replay_spec.md);
  G6 closed.

- Block 3 governance Session 05 (`RM-956`): hedge gap v2 — `by_risk_type[]` per weakness bucket
  via `HEDGE_GAP_SCENARIO_BY_RISK` (aligned with X-Ray `WEAKNESS_SCENARIO_MAP`); method
  `stress_scenario_hedge_evidence_v2`; [hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md);
  extended `tests/test_stress_hedge_gap_contract.py`; G5 closed.

- Block 3 governance Session 04 (`RM-955`): factor drivers in `stress_conclusions` —
  `top_factor_drivers_worst_scenario` and `helped_factors_worst_scenario` from worst synthetic
  `pnl_by_factor_pct`; [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §12.1;
  stress commentary factor driver lines; G4 closed.

- Block 3 governance Session 03 (`RM-954`): hedge gap N/A transparency —
  `not_applicable` + `status_reason` / `status_reason_en` on `hedge_gap_analysis` when no hedge
  `risk_role` labels; [hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md) taxonomy;
  stress commentary plain-English N/A line; G3 closed.

- Block 3 governance Session 02 (`RM-953`): primary historical stress disclosure —
  `historical_methodology` on `stress_report.json`, `return_method` / `proxy_used` on
  `historical_results`, enhanced `stress_conclusions.data_quality_warnings`; DEC-2026-05-20-001;
  [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §9.3.

- Block 2 post-audit Session 10 (`RM-950`): [Portfolio X-Ray Baseline Snapshot](docs/audits/2026-05-20_portfolio_xray_baseline_snapshot.md)
  — artifact checklist, golden contract reference, compare template; Phase 12 (`RM-940`–`RM-950`) closed;
  post-audit ExecPlan marked Completed.

- Block 2 post-audit Session 09 (`RM-949`): golden `portfolio_xray.json` contract tests —
  `tests/fixtures/portfolio_xray_golden_v2.json`, `tests/test_portfolio_xray_contract.py`,
  `tests/portfolio_xray_golden_inputs.py`; Portfolio X-Ray wave bundle in [TESTING.md](TESTING.md).

- Block 2 post-audit Session 08 (`RM-948`): `volatility_spike` weakness row documented and implemented
  as **factor-only (Option B)** — `beta_vix` + historical `es_95`; `scenario_coverage.evidence_mode`
  and `WEAKNESS_FACTOR_ONLY_RISKS`; test `test_volatility_spike_weakness_factor_only_methodology`.

- Block 2 post-audit Session 07 (`RM-947`): Portfolio X-Ray `weight_concentration` item in
  `asset_allocation` (top-1/top-3 capital weight sums, HHI on positive weights, no look-through);
  legacy summary mirrors fields; test `test_portfolio_xray_weight_concentration_in_asset_allocation`.

- Block 2 post-audit Session 06 (`RM-946`): [portfolio_xray_layer_spec.md](docs/specs/portfolio_xray_layer_spec.md)
  — Block 2.1–2.7 layer map (code, upstream inputs, tests, Phase 12 follow-ups); indexed in
  [SPEC.md](SPEC.md) and [docs/specs/README.md](docs/specs/README.md).

- Block 2 post-audit Session 05 (`RM-945`): Portfolio X-Ray `multi_window_metrics` panel (3Y/5Y/10Y
  from snapshot metrics) and `ttr_months`/`recovered` on primary `portfolio_metrics`; loader
  `load_portfolio_windows_from_dir`; tests `test_portfolio_xray_multi_window_metrics_panel`,
  `test_portfolio_xray_ttr_in_primary_risk_metrics`, `test_load_portfolio_windows_from_dir`.

- Block 2 post-audit Session 04 (`RM-944`): Portfolio X-Ray `factor_regression_inference` items in
  `factor_exposure` (read-only HAC inference, multicollinearity, and residual diagnostics from
  `stress_report.factor_regression_5y/10y`); tests
  `test_portfolio_xray_factor_regression_inference_panel`.

- Block 2 post-audit Session 03 (`RM-943`): section-level provenance on Portfolio X-Ray sections
  `risk_diagnostics`, `factor_exposure`, `risk_budget_view`, and `weakness_map` (`method`,
  `frequency`, `window`, `n_obs`, `benchmark`); RC CSV loader returns the file actually used;
  test `test_portfolio_xray_section_provenance_metadata`.

- Block 2 post-audit Session 02 (`RM-942`): canonical `XRAY_THRESHOLDS` registry in
  [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §8 and drift
  tests in [tests/test_portfolio_xray_threshold_registry.py](tests/test_portfolio_xray_threshold_registry.py).

- Block 2 post-audit governance Session 00: [Portfolio X-Ray Methodology Map](docs/audits/2026-05-20_portfolio_xray_methodology_map.md),
  active ExecPlan [2026-05-20_portfolio_xray_post_audit_roadmap.md](docs/exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md),
  and ROADMAP Phase 12 (`RM-940`–`RM-950`) for audit-grade X-Ray transparency.

- Stress Lab Sessions 01-10 (post-audit wave): hardened `stress_scorecard_v1` / `stress_conclusions`,
  `historical_episode_paths` crisis replay CSVs, `hedge_gap_analysis`, expanded synthetic scenario
  coverage (`usd_shock`, `commodity_shock`, `banking_2023`), `synthetic_assumptions` transparency,
  portfolio-first stress resolution via `src/stress_artifacts.py`, plain-English stress narrative in
  commentary/IPS, and custom-shock simulator API (`simulate_custom_shock`); contract tests and specs
  (`stress_lab_layer_spec`, `hedge_gap_analysis_spec`, `crisis_replay_spec`); Session 10 closed the
  wave with documented regression bundle in [TESTING.md](TESTING.md).

- X-Ray Session 09 / RM-939: portfolio-first **core** vs **full** review modes on
  `run_portfolio_review.py` (`--mode core|full`, factory profiles `core_v1` / `default_v1`);
  `candidate_menu` partial-menu disclosure in `candidate_comparison.json` and decision-package
  summary; operational runbook and spec updates.

- X-Ray Session 08 / RM-938: structured X-Ray report surfaces (`format_portfolio_xray_html`,
  `format_portfolio_xray_text`, `format_portfolio_xray_commentary`) and generated-output QA scans
  for X-Ray wording in `report.txt`, `report.html`, and `commentary.txt`.

- X-Ray Session 07 / RM-937: Portfolio Archetype V2 scorecard with per-archetype
  `positive_evidence` / `negative_evidence`, `archetype_scorecard`, regime
  `conflicting_signals`, and `conflict_summary` (built after weakness map).

### Changed

- Block 4 governance Session 04 (`RM-974`): comparison rows include `construction_disclosure`
  (passthrough `baseline_weights_metadata.json`, builder `summary.json`, policy/subject excerpts,
  optional factory step); closes G6 / `KI-2026-05-20-004`; [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md) v1.3.

- Block 4 governance Session 03 (`RM-973`): unchecked freshness rebuilds instead of `skipped_existing`;
  comparison warns `candidate_freshness_unchecked_no_review_analysis_end:{candidate_id}` when review
  `analysis_end` unknown; closes G3 / `KI-2026-05-20-003`; factory + comparison specs updated.

- Block 4 governance Session 02 (`RM-972`): factory propagates builder `summary.json` `FAIL_*` into
  `candidate_factory_run.json` `reason_code` (`builder_fail_config`, `builder_infeasible_universe`, …)
  with optional `builder_status` / `builder_reason`; closes G1 / `KI-2026-05-20-001`;
  [candidate_factory_spec.md](docs/specs/candidate_factory_spec.md) reason-code table updated.

- Block 2 post-audit governance Session 01 / `RM-941`: documentation registers aligned with the
  deepening wave — `RM-932` marked Done in ROADMAP Phase 11; resolved RC/Kalman known issues removed
  from active KNOWN_ISSUES; Portfolio X-Ray regression bundle stub added to [TESTING.md](TESTING.md)
  (golden contract tests shipped in post-audit Session 09 / `RM-949`).

- Default `run_portfolio_review.py` factory scope is `core_v1` via `--mode core` (was implicit
  full `default_v1`). Use `--mode full` for the complete optimizer menu.

### Fixed

- Stress Lab Session 10: aligned stale `test_write_portfolio_commentary_creates_file` assertions with
  current `format_portfolio_xray_commentary` headings (`Portfolio X-Ray (diagnostic-only)`).

- X-Ray Session 07 / RM-937: archetype labels no longer hide inflation/rates regime
  tensions (`KI-2026-05-19-010`).

- Mitigated `KI-2026-05-19-005`: core/full review modes and `candidate_menu` disclosure (Session 09).

## 2026-05-19

### Added

- X-Ray Session 06 / RM-936: Weakness Map V2 separates `exposure_present`,
  `adverse_evidence`, `severity`, and `confidence`; adds `scenario_coverage`,
  `top_asset_loss_drivers`, `top_factor_drivers`, per-row `missing_inputs`, and
  conditional `crypto_shock` when crypto taxonomy/weights are present.

- X-Ray Session 05 / RM-935: Hidden Risk Detector V2 emits per-category
  `flagged` / `below_threshold` / `unavailable` assessments (equity beta, duration, credit, liquidity,
  raw/residual PCA, weak hedge, tail risk, stress RC, macro factor dependency, Top1 RC) plus section
  `confidence`, `evidence_count`, and flag counts in `portfolio_xray.json`.

- X-Ray Session 04 / RM-934: portfolio window metrics now include skewness/kurtosis (monthly log
  returns), downside/upside beta, `corr_base`, rolling beta/correlation summaries, and `metric_quality`
  metadata; exposed in snapshots, CSV exports, and X-Ray risk diagnostics.

### Fixed

- X-Ray Session 03 / RM-933: portfolio VaR/ES computed on daily historical returns with
  `analytics.tail_risk` disclosure (method, frequency, window, n_obs); X-Ray and report surfaces
  updated (`KI-2026-05-19-009`).
- X-Ray Session 02 / RM-932: Risk Budget View loads full `rc_vol_*` CSV evidence; factor exposure
  reads Kalman betas from `stress_report.factor_betas_kalman.latest` (`KI-2026-05-19-007`,
  `KI-2026-05-19-008`).
- X-Ray Session 01 / RM-931: report path truncates return panels to `analysis_end`; stress scenario
  analytics and scenario library honor cutoff; `inputs/monthly_returns.csv` is analysis-effective with
  optional `monthly_returns_raw.csv` and `inputs_manifest.json` (`KI-2026-05-19-006`).

### Changed

- Documented deferred operational follow-up after Phase 9: heavy full candidate refresh vs practical
  one-shot runs (`RM-920`–`RM-922`, `KI-2026-05-19-005`; ROADMAP Phase 10, ExecPlan post-closure,
  runbook and factory/review specs).

- Closed RM-911 / Phase 9 post-portfolio-first stabilization: representative review verified subject
  metadata, freshness gating, selection/decision package, regime metrics, monitoring, and PDF outputs;
  removed active issues `KI-2026-05-19-002` and `KI-2026-05-19-004`.

- RM-910: `run_portfolio_review.py` now rebuilds portfolio-first PDFs only by default
  (`rebuild_pdf_reports.py --portfolio-first`: decision package + `analysis_subject` sidecar);
  use `--legacy-full-pdf` for the full EW/RP/policy/baseline variant suite.

### Fixed

- Fixed RM-909: Decision package PDF now uses YAML front matter (`build_decision_package_pdf_md`)
  instead of a long H1 with embedded `analysis_end`, restoring `Main portfolio_decision_package.pdf`
  Pandoc/XeLaTeX builds; closed `KI-2026-05-18-001`.
- Fixed RM-908: `monitoring_diff_v1` with `no_prior_snapshot` no longer emits profile/decision
  deltas or prior snapshot paths; same-`analysis_end` re-runs stay narrative-only with warning
  `prior_same_analysis_end_ignored`.
- Fixed RM-906: Regime portfolio metrics no longer reference undefined `mar_monthly`; daily regime
  Sortino uses aligned daily risk-free by default or a daily-converted configured MAR.
- Fixed RM-905: Portfolio-first comparison now gates root `policy` artifacts as legacy optional
  references, Health Score prioritizes `analysis_subject`, and decision summaries hide the
  current-vs-policy compatibility block for portfolio-first runs.
- Fixed RM-902: Candidate Factory now reuses existing candidate snapshots only when
  `snapshot_10y.json.analysis_end` matches the review date, and Candidate Comparison marks stale
  candidate snapshots unavailable.
- Fixed RM-901: `candidate_comparison.json.analysis_setup_summary` now prefers `analysis_subject/run_metadata.json` over stale root metadata, with regression coverage for `current_portfolio` subjects.

### Added

- Added the [Portfolio X-Ray Layer Audit](docs/audits/2026-05-19_portfolio_xray_layer_audit.md),
  active [Portfolio X-Ray Diagnostics Deepening Plan](docs/exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md),
  and dedicated [Portfolio X-Ray diagnostics spec](docs/specs/portfolio_xray_diagnostics_spec.md)
  for Sessions 00-09 (`RM-930`-`RM-939`).
- Added active [Post-Portfolio-First Stabilization Plan](docs/exec_plans/2026-05-19_post_portfolio_first_stabilization_plan.md)
  and roadmap Phase 9 (`RM-900`-`RM-911`) to stabilize subject metadata, candidate freshness,
  decision reliability, methodology consistency, monitoring, and report/PDF output before UI work.
- [Post-Portfolio-First State Audit](docs/audits/2026-05-19_post_portfolio_first_state_audit.md):
  documents system state after transition closure, latest `run_portfolio_review.py` evidence, P0–P2
  stabilization backlog, and register entry in [docs/audits/README.md](docs/audits/README.md).

## 2026-05-18

### Added

- Closed the portfolio-first transition with offline E2E coverage for `current_portfolio`,
  `model_portfolio`, and `universe_baseline` subjects through comparison, decision artifacts, and
  decision-package reporting (Portfolio-first Session 09).
- Updated decision-package report language and generated-output QA for the portfolio-first story:
  summaries now name `analysis_subject` as the starting portfolio and scored rows as candidate
  alternatives, with config examples for current/model subjects (Portfolio-first Session 08).
- Isolated legacy policy workflow language: `run_portfolio_review.py` is now the documented normal
  first command, while `run_optimization.py` and `run_mvp_workflow.py` help/docs are labeled legacy
  compatibility (Portfolio-first Session 07).
- Added subject-centered comparison and decision baselines: `candidate_comparison.json` now includes `analysis_subject`, and Selection/No-Trade, Action, Monitoring, and Decision Journal prefer that baseline before legacy `current` (Portfolio-first Session 06).
- Added portfolio-first orchestration ([run_portfolio_review.py](run_portfolio_review.py), [src/portfolio_review_workflow.py](src/portfolio_review_workflow.py), [tests/test_portfolio_review_workflow.py](tests/test_portfolio_review_workflow.py)) to materialize `analysis_subject` before non-policy candidates and comparison without calling `run_optimization.py` by default (Portfolio-first Session 05).
- Added `run_report.py --materialize-analysis-subject` to write portfolio-first subject diagnostics under `{output_dir_final}/analysis_subject/` before candidate generation (Portfolio-first Session 04).
- Added explicit `analysis_subject` config/schema support and resolver export through `analysis_setup` and `input_assumptions` (Portfolio-first Session 03).
- Added canonical [portfolio review workflow spec](docs/specs/portfolio_review_workflow_spec.md) for the `analysis_subject`-first contract and linked it from top-level source-of-truth docs (Portfolio-first Session 02).
- Added active [Portfolio-First Transition Plan](docs/exec_plans/2026-05-18_portfolio_first_transition_plan.md) and roadmap Phase 8 (`RM-800`-`RM-808`) to move the main workflow from policy-first to `analysis_subject`-first while preserving the old policy engine as legacy infrastructure.

- Closed [post-audit MVP stabilization plan](docs/exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md) Session 11: Phase 7 (`RM-700`–`RM-710`) complete; broad verification (`462` pytest passes, docs verify, generated-output QA scan).
- Added file-first MVP workflow orchestration ([run_mvp_workflow.py](run_mvp_workflow.py), [src/mvp_workflow.py](src/mvp_workflow.py), [tests/test_mvp_workflow.py](tests/test_mvp_workflow.py)): thin wrapper for `input -> diagnosis -> comparison -> action`; documented in [docs/operational_runbook.md](docs/operational_runbook.md) (MVP stabilization Session 10).
- Added offline MVP pipeline smoke test ([tests/test_mvp_pipeline_offline.py](tests/test_mvp_pipeline_offline.py), [tests/mvp_offline_fixtures.py](tests/mvp_offline_fixtures.py)): synthetic snapshots, network guards, and decision-package JSON chain verification; documented in [TESTING.md](TESTING.md) (MVP stabilization Session 09).

### Changed

- Updated [README](README.md) and [ARCHITECTURE](ARCHITECTURE.md) to document supported partial utility UIs (`config_ui/`, `results_dashboard/`) vs full product workspace TBD.

### Fixed

- Removed active issue `KI-2026-05-18-002` after the default workflow was moved to
  `analysis_subject`-first and covered by offline end-to-end tests.
- Removed active issue `KI-2026-05-17-004` after partial utility UI status was synced in top-level docs (MVP stabilization Session 11).
- Removed active issue `KI-2026-05-17-020` after the offline MVP smoke test landed.

## 2026-05-17

### Added

- Added [repeat project MVP readiness audit](docs/audits/2026-05-17_repeat_project_mvp_readiness_audit.md) and active [post-audit MVP stabilization plan](docs/exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md), with roadmap/register/known-issue handoff for Sessions 01-11.
- Implemented [src/regret_analysis.py](src/regret_analysis.py): `regret_analysis_v1` JSON/TXT, stress-scenario regret vs best available, reference profiles favored/current/benchmark, Tier B CAGR slice, wired after Pareto in `write_candidate_comparison_outputs`, decision-package Regret section; [tests/test_regret_analysis.py](tests/test_regret_analysis.py) (post-audit Session 19).
- Added [regret analysis spec](docs/specs/regret_analysis_spec.md): `regret_analysis_v1` contract, stress-scenario regret vs best available, reference profiles favored/current/benchmark, pipeline placement after Pareto (post-audit Session 18); decision `DEC-2026-05-17-011`.
- Implemented [src/pareto_dominance.py](src/pareto_dominance.py): `pareto_dominance_v1` JSON/TXT, strict Pareto dominance on comparison metrics, wired after assumption sensitivity in `write_candidate_comparison_outputs`, decision-package section; optional `es_95` in comparison metrics; [tests/test_pareto_dominance.py](tests/test_pareto_dominance.py) (post-audit Session 17).
- Added [pareto dominance spec](docs/specs/pareto_dominance_spec.md): `pareto_dominance_v1` contract, strict Pareto objectives, pairwise dominance rules, pipeline placement after assumption sensitivity (post-audit Session 16); decision `DEC-2026-05-17-010`.
- Implemented [src/assumption_sensitivity.py](src/assumption_sensitivity.py): `assumption_sensitivity_v1` JSON/TXT, Tier A/B variant grid, wired after trade-off in `write_candidate_comparison_outputs`, decision-package summary section; [tests/test_assumption_sensitivity.py](tests/test_assumption_sensitivity.py) (post-audit Session 15).
- Added [assumption sensitivity spec](docs/specs/assumption_sensitivity_spec.md): `assumption_sensitivity_v1` contract, Tier A selection-weight variants, Tier B evidence ranks, stability bands, pipeline placement after trade-off (post-audit Session 14); decision `DEC-2026-05-17-009`.
- Implemented [src/tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py): `tradeoff_explanation_v1` and `model_risk_diagnostics_v1` after selection in `write_candidate_comparison_outputs`; decision package and journal integration; [tests/test_tradeoff_and_model_risk.py](tests/test_tradeoff_and_model_risk.py) (post-audit Session 13).
- Added [trade-off and model risk spec](docs/specs/tradeoff_and_model_risk_spec.md): `tradeoff_explanation_v1` and `model_risk_diagnostics_v1` contracts, warning catalog, pipeline placement after selection (post-audit Session 12); decision `DEC-2026-05-17-008`.
- Implemented candidate factory (post-audit Session 11): [run_candidate_factory.py](run_candidate_factory.py), [src/candidate_factory.py](src/candidate_factory.py), profiles and skip-existing orchestration, `candidate_factory_run.json` / `.txt`, optional `--then-compare`; [tests/test_candidate_factory.py](tests/test_candidate_factory.py).
- Added [candidate factory spec](docs/specs/candidate_factory_spec.md): V1 orchestration profiles, registry-to-script table, `candidate_factory_run_v1` contract, and planned `run_candidate_factory.py` CLI (post-audit Session 10; implementation Session 11); decision `DEC-2026-05-17-007`.
- Implemented current-vs-policy workflow (post-audit Session 09): `run_report.py --materialize-current`, sidecar resolution in [src/candidate_comparison.py](src/candidate_comparison.py), [src/current_vs_policy.py](src/current_vs_policy.py) status artifacts, reporting/selection/action gating; [tests/test_current_vs_policy_workflow.py](tests/test_current_vs_policy_workflow.py).
- Added [current vs policy workflow spec](docs/specs/current_vs_policy_workflow_spec.md): V1 combined workflow (policy on Main + `current_portfolio/` sidecar), No-Trade actionability matrix, skip reason codes, and `current_vs_policy_status_v1` contract (post-audit Session 08).
- Added [audit register](docs/audits/README.md) and [ExecPlan register](docs/exec_plans/README.md) to keep audit history, plan history, and the active plan pointer in concise documentation indexes.
- Added [post-audit stabilization and analytics ExecPlan](docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md) to guide separate future sessions for docs sync, report integration, workflow hardening, candidate factory, and new analytics.
- Added the post-session deep system audit after Sessions 01-20, covering concept alignment, docs/code drift, Post-closure triage, and Main-vs-robust optimizer boundaries.
- Implemented [src/decision_journal.py](src/decision_journal.py): generated-only `decision_journal_v1` JSON/TXT projecting selection, action, monitoring, and comparison; `journal/latest/` and `journal/history/` copies; wired after monitoring in `write_candidate_comparison_outputs`; [tests/test_decision_journal.py](tests/test_decision_journal.py).
- Added [decision journal spec](docs/specs/decision_journal_spec.md) (`decision_journal_v1`): generated-only decision record, journal latest/history layout, pipeline placement after monitoring.
- Implemented [src/monitoring.py](src/monitoring.py): `analysis_snapshot_v1` under `monitoring/latest/` and `history/`, `monitoring_diff_v1` JSON/TXT vs prior snapshot; wired in `write_candidate_comparison_outputs`; [tests/test_monitoring.py](tests/test_monitoring.py).
- Added [monitoring spec](docs/specs/monitoring_spec.md) (`analysis_snapshot_v1`, `monitoring_diff_v1`): What Changed contract, profile projection for current/policy, pipeline placement.
- Implemented [src/action_engine.py](src/action_engine.py): non-executing `action_plan.json` / `.txt` from selection and comparison (weight deltas, trades when `selected_candidate`, 10 bps transaction-cost estimate on turnover half-sum, always written after selection); wired in `write_candidate_comparison_outputs`; [tests/test_action_engine.py](tests/test_action_engine.py).
- Added [action engine spec](docs/specs/action_engine_spec.md) (`action_plan_v1`): Rebalancing Advisor contract, action statuses, transaction-cost model, pipeline placement.
- Implemented [src/selection_engine.py](src/selection_engine.py): formal non-executing `selection_decision.json` / `.txt` from comparison and score artifacts (policy default, composite fallback, No-Trade materiality, five decision statuses); wired in `write_candidate_comparison_outputs`; [tests/test_selection_engine.py](tests/test_selection_engine.py).
- Added [selection engine spec](docs/specs/selection_engine_spec.md) (`selection_decision_v1`): formal decision outcomes, composite selection from health and robustness scores, No-Trade materiality thresholds, neutral decision-support wording.
- Implemented [src/portfolio_health_score.py](src/portfolio_health_score.py): diagnostic `portfolio_health_score.json` / `.txt` from `candidate_comparison.json` (ten components, optional robustness `resilience_reference`); comparison `weight_concentration` from `snapshot_10y.final_weights_total`; [tests/test_portfolio_health_score.py](tests/test_portfolio_health_score.py).
- Added [portfolio health score spec](docs/specs/portfolio_health_score_spec.md) (`portfolio_health_score_v1`): ten weighted components, within-run ranks plus absolute mandate/liquidity checks, optional `resilience_reference` from robustness scorecard, comparison `weight_concentration` prerequisite for Session 13.
- Implemented [src/robustness_scorecard.py](src/robustness_scorecard.py): diagnostic `robustness_scorecard.json` / `.txt` from `candidate_comparison.json` (six components, within-run ranks, mandate cap, stress_report fallback).
- Extended [src/candidate_comparison.py](src/candidate_comparison.py) with per-candidate `diversification` (RC from `snapshot_10y.json`) and automatic scorecard export; [tests/test_robustness_scorecard.py](tests/test_robustness_scorecard.py).
- Added [robustness scorecard spec](docs/specs/robustness_scorecard_spec.md) (`robustness_scorecard_v1`): six weighted components, relative within-run scoring, mandate absolute checks, RC via comparison `diversification` block.
- Added [src/candidate_comparison.py](src/candidate_comparison.py) read-only builder for canonical `candidate_comparison.json` (18-candidate registry, policy/current gating, legacy subset export) and [tests/test_candidate_comparison.py](tests/test_candidate_comparison.py).
- Added [candidate comparison spec](docs/specs/candidate_comparison_spec.md) defining canonical `candidate_comparison.json` under `output_dir_final` (full candidate registry, `current` row, diagnostic-only boundary).
- Added [docs/ROADMAP.md](docs/ROADMAP.md) as the durable phased development roadmap and audit-to-session backlog.
- Added active audit-derived issues to [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for unresolved source-of-truth, config UI, rebalance, encoding, and docs-verification gaps.
- Added [scripts/verify_docs.py](scripts/verify_docs.py), [src/docs_verify.py](src/docs_verify.py), and [tests/test_docs_links.py](tests/test_docs_links.py) for repeatable Markdown link and stale-reference checks.
- Added [decision package reporting spec](docs/specs/decision_package_reporting_spec.md) and [src/decision_package_reporting.py](src/decision_package_reporting.py): compact `decision_package_summary` TXT/JSON, `report.txt` append, comparison CLI paths, optional decision-package PDF; [tests/test_decision_package_reporting.py](tests/test_decision_package_reporting.py).

### Changed

- Completed MVP stabilization Session 08 (`RM-707`): regenerated representative Main/EW/RP outputs, added generated-output QA scan/test, English EW/RP comparison labels, and FRED CSV fallback when `pandas_datareader` is unavailable.
- Completed MVP stabilization Session 06 (`RM-705`): time-to-recovery now follows the max-drawdown peak/trough path, counts monthly/trading observations by index position, and treats no-drawdown windows as recovered with `ttr = 0`.
- Completed MVP stabilization Session 07 (`RM-706`): factor multicollinearity diagnostics now emit `assessment_en`; stress commentary prefers `assessment_en` and legacy-reads `assessment_ru` from older reports only.
- Completed MVP stabilization Session 05 (`RM-704`): NaN-safe data policy docs now define when `n_months_cash_fallback` is counted after risk-weight redistribution.
- Completed MVP stabilization Session 04 (`RM-703`): monthly return-panel cache keys now include resolved asset-currency metadata so FX-adjusted cached panels invalidate after `assets.yml` currency changes.
- Completed MVP stabilization Session 03 (`RM-702`): synced risk-free and cash policy docs/tests so USD/EUR defaults are explicit and unsupported non-USD currencies require configured cash and risk-free sources.
- Completed MVP stabilization Session 02 (`RM-701`): synced `README.md`, `ARCHITECTURE.md`, and `PRODUCT.md` so implemented file-first factory, current-vs-policy, trade-off/model-risk, assumption sensitivity, Pareto, regret, and decision-package outputs are not described as target/TBD work.
- Closed post-audit stabilization plan (Session 20, `RM-623`): marked [post-audit ExecPlan](docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md) completed, updated [docs/ROADMAP.md](docs/ROADMAP.md) and [exec plan register](docs/exec_plans/README.md), synced [PRODUCT.md](PRODUCT.md) comparison targets with implemented factory/current-vs-policy/Pareto/regret file-first artifacts.
- Cross-linked current-vs-policy workflow spec from candidate comparison, input assumptions, selection, action, reporting outputs, OUTPUTS, and spec index (post-audit Session 08).
- Cleaned source/generator text defaults across optimization/report/PDF/config/docs paths so project artifacts use English and common mojibake markers are removed from source.
- Synced detailed decision-package specs so reporting, comparison, selection, action, monitoring, and journal contracts describe the implemented V1 artifact chain instead of stale future/TBD neighbors.
- Synced top-level docs after the post-session audit: `README.md`, `AGENTS.md`, `SPEC.md`, `PRODUCT.md`, and `ARCHITECTURE.md` now treat the V1 decision pipeline as implemented file-first artifacts while keeping full UI/workspace and advanced analytics as future work.
- Updated [docs/ROADMAP.md](docs/ROADMAP.md), [DECISIONS.md](DECISIONS.md), and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) with post-session next-stage priorities and unresolved stabilization issues.
- Extended [src/candidate_comparison.py](src/candidate_comparison.py) and [run_compare_variants.py](run_compare_variants.py) to export robustness scorecard and portfolio health score after each comparison run.
- Refactored [run_compare_variants.py](run_compare_variants.py) to call the shared candidate comparison builder (canonical JSON + legacy `portfolio_comparison.*`).
- Updated [DECISIONS.md](DECISIONS.md) to remove the stale empty-log wording and record the roadmap ownership decision.

### Fixed

- Closed `KI-2026-05-17-019` by emitting `assessment_en` from factor multicollinearity diagnostics and keeping `assessment_ru` as legacy-read compatibility in stress commentary only.
- Closed `KI-2026-05-17-007` after representative output regeneration and automated QA scan passed; opened `KI-2026-05-18-001` for the residual decision-package PDF Pandoc failure.
- Closed `KI-2026-05-17-018` by adding focused recovered/unrecovered/no-drawdown TTR regressions and correcting monthly/daily recovery semantics.
- Closed `KI-2026-05-17-017` by counting actual NaN-safe cash fallback months and adding focused regressions for missing-risk residual cash usage.
- Closed `KI-2026-05-17-016` by adding an asset-currency metadata fingerprint to monthly cache keys and focused regression coverage for currency-metadata invalidation.
- Closed `KI-2026-05-17-015` by aligning risk-free/cash policy wording with config resolver behavior and adding focused regressions for EUR defaults and unsupported-currency explicit configuration.
- Closed `KI-2026-05-17-014` by removing top-level implemented-as-TBD wording for the file-first V1 decision artifact chain.
- Closed `KI-2026-05-17-006` by assigning Selection Engine V1 the unique decision ID `DEC-2026-05-17-006` and updating the session handoff references.
- Closed `KI-2026-05-17-005` by removing stale top-level wording that described implemented Health Score, Selection/No-Trade, Monitoring, and Decision Journal artifacts as target/TBD.
- Project-wide documentation hygiene: fixed punctuation/math mojibake in `.cursor/` agents and rules, `docs/`, and engineering Python (`run_report.py`, `src/snapshot.py`, `results_dashboard/app.py`, `src/pdf_reports.py`, `src/config.py`); restored cp1251-mojibake logger text in `run_report.py`.
- Cleaned source-document mojibake in [production_workflow.md](docs/specs/production_workflow.md), [stress_testing_spec.md](docs/specs/stress_testing_spec.md), [metrics_specification.md](docs/specs/metrics_specification.md), and [view_after_optimization_spec.md](docs/specs/view_after_optimization_spec.md).
- Clarified [rebalance.py](src/rebalance.py) threshold docstrings: `threshold_pct` gates on max absolute per-ticker weight drift only; added focused regression tests.
- Rewrote the [stress testing spec](docs/specs/stress_testing_spec.md) stress covariance section so `taxonomy_blend_v1` is the current default and `uniform_legacy` is clearly legacy-only.
- Removed the stale editable `rc_asset_cap_pct` field from the config UI and added focused regression coverage.
- Updated the config UI to separate `analysis_mode`, user-entered `current_weights`, and read-only generated `portfolio_weights.yml` output.

## 2026-05-15

### Added

- Added Portfolio X-Ray v2 with generated `portfolio_xray.json`, common section schema, rule-based hidden-risk flags, archetype caveats, weakness map, and diagnostic-only report wiring.
- Added `analysis_setup_v1` as the resolved Input and Assumptions runtime contract and exported it in run artifacts alongside projected `input_assumptions`.
- Added Portfolio X-Ray summary helpers for report/commentary surfaces, including setup, allocation, risk-contribution, and explanatory diagnostic verdict sections.
- Added Input and Assumptions Layer V1 with `analysis_mode`, `current_weights`, an `input_assumptions` artifact summary, and the canonical [input assumptions spec](docs/specs/input_assumptions_spec.md).
- Added [GLOSSARY.md](GLOSSARY.md) as a living glossary for shared project terminology.
- Added [OUTPUTS.md](OUTPUTS.md) as the root map for generated outputs, report artifacts, output folders, formats, and generated-vs-source boundaries.
- Added [WORKFLOW.md](WORKFLOW.md) as the explicit task workflow from request to implementation, verification, docs sync, project memory, and commit.
- Added [DECISIONS.md](DECISIONS.md) as the concise living decision log for key project decisions and rationale.
- Added [CHANGELOG.md](CHANGELOG.md) as the concise living history for meaningful project changes.
- Added [KNOWN_ISSUES.md](KNOWN_ISSUES.md) as the living register for active issues, model limitations, testing gaps, and technical debt.

### Changed

- Populated [GLOSSARY.md](GLOSSARY.md) with the initial 80 shared project terms.
- Linked decision-log, changelog, and known-issues governance from the top-level documentation maps.
- Simplified top-level documentation routing and clarified source-of-truth links across root docs.

## 2026-05-14

### Added

- Added [DATA.md](DATA.md) as the living data-layer map.
- Added [TESTING.md](TESTING.md) as the project verification framework.

### Changed

- Reorganized project documentation around compact top-level maps and detailed specs under [docs/specs/](docs/specs/README.md).
- Clarified that [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) is a living product blueprint, not a binding implementation spec.
