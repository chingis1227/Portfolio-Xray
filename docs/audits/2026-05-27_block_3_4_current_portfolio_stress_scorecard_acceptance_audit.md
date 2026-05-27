# 2026-05-27 — Block 3.4 Current Portfolio Stress Scorecard Acceptance Audit

Status: Accepted  
Plan: [2026-05-27_block_3_4_current_portfolio_stress_scorecard_plan.md](../exec_plans/2026-05-27_block_3_4_current_portfolio_stress_scorecard_plan.md)  
Scope: Block 3.4 Core MVP (`current_portfolio_stress_scorecard_v1` on subject `stress_report.json`)

## 1. What was implemented

- New Core MVP Block 3.4 product key on `stress_report.json`:
  - `current_portfolio_stress_scorecard_v1` (diagnostic-only current-portfolio stress scorecard).
- Implementation location:
  - Builder/attach module: `src/current_portfolio_stress_scorecard_block.py`.
  - Wiring:
    - `src/stress.py::run_stress` and `_empty_report` attach `current_portfolio_stress_scorecard_v1` after `stress_results_v1` and `hedge_gap_analysis_v1`.
    - `run_report.py` re-attaches all three blocks before `export_stress_report`.
    - `run_optimization.py` attaches the same three blocks before legacy stress export.
- Block 3.4 is a pure adapter over existing Stress Lab outputs:
  - Block 3.1 evidence: `scenario_results[]`, `historical_results[]`, `historical_episode_paths[]`.
  - Block 3.2 product layer: `stress_results_v1` (envelope + per-scenario rows).
  - Block 3.3 product layer: `hedge_gap_analysis_v1` (offset coverage + main hedge gap).

## 2. Contract and linkage checks

**Artifact inspected:** `Main portfolio/analysis_subject/stress_report.json` after:

```bash
python run_portfolio_review.py --skip-candidates
```

- `current_portfolio_stress_scorecard_v1` present at top level:
  - `version`: `current_portfolio_stress_scorecard_v1`
  - `block`: `"3.4"`
  - `loss_gate_mode`: `"diagnostic"`
- Scenario library snapshot:
  - `scenario_library.version == "scenario_library_v1"`.
  - `synthetic_ids` and `historical_ids` match canonical lists from Block 3.2 / Scenario Library.
- Worst selectors:
  - Worst synthetic scenario:
    - `current_portfolio_stress_scorecard_v1.worst_synthetic_scenario.scenario_id == "recession_severe"`.
    - Loss `-0.2203` equals `stress_results_v1.envelope.worst_synthetic.portfolio_loss_pct` and min `portfolio_pnl_pct` from `scenario_results[]`.
  - Worst historical episode:
    - `current_portfolio_stress_scorecard_v1.worst_historical_scenario.episode == "2022"`.
    - `drawdown_pct == -0.1976` equals `stress_results_v1.envelope.worst_historical.drawdown_pct` and min `max_dd` in `historical_results[]`.
- Loss vs drawdown summary:
  - `portfolio_loss_summary.synthetic` uses synthetic `portfolio_pnl_pct`.
  - `portfolio_loss_summary.historical` uses `pnl_real_episode`.
  - `historical_drawdown_summary.max_dd` uses `drawdown_pct` / `max_dd`.
- Top loss contributors:
  - Synthetic (worst synthetic):
    - Top 3 hurt assets (`QQQ`, `SLV`, `SPY`) mirror `stress_results_v1.envelope.worst_synthetic.top3_loss_assets`.
  - Historical (worst historical):
    - Top 3 hurt assets (`TLT`, `QQQ`, `BND`) mirror `stress_results_v1.envelope.worst_historical.top3_loss_assets`.
- Top risk contributors (RC, synthetic):
  - Scenario id matches worst synthetic.
  - `top1_rc_asset == "SCHD"`, `top3_rc_assets == ["SCHD", "QQQ", "SLV"]`, `top3_rc_sum_pct == 0.6063` mirror `stress_results_v1.synthetic_scenarios[recession_severe].risk_contribution`.
- Factor attribution:
  - `factor_stress_attribution_summary.scenario_id == "recession_severe"`.
  - `top_factor_drivers` mirror `stress_results_v1.envelope.worst_synthetic.top_factor_drivers`.
  - `helped_factors` mirror `stress_conclusions.helped_factors_worst_scenario`.
- Assets helped / hurt:
  - Worst synthetic:
    - `assets_helped` is `[TLT, BND, SCHP]` with PnL matching `scenario_results[recession_severe].pnl_by_asset_pct`.
    - `assets_hurt_top3` is `[QQQ, SLV, SPY]` (same as top3 loss assets for worst synthetic).
  - Hedge-gap main area:
    - `hedge_gap_main_area.risk_type == "equity_crash_protection"`, `linked_scenario_id == "equity_shock"`.
    - `assets_hurt` / `assets_helped` mirror `hedge_gap_analysis_v1.by_risk_type` row for the main hedge gap.
- Offset coverage + main hedge gap:
  - `offset_coverage_summary`:
    - `risk_type == "equity_crash_protection"`.
    - `offset_coverage_ratio == 0.0`.
    - `gross_loss_from_assets_hurt == 0.1616`, `positive_contribution_from_assets_helped == 0.0`
      (consistent with Block 3.3).
  - `main_hedge_gap`:
    - `weakest_protection_area == "equity_crash_protection"`.
    - `strongest_protection_area == "commodity_inflation_shock_protection"`.
    - `main_hedge_gap.offset_coverage_ratio == 0.0`, `portfolio_loss_pct == -0.1617`.
    - `diagnosis_summary_en` mirrors Block 3.3 summary.

## 3. Data quality and diagnostic-only boundary

- `data_quality_warnings` combine:
  - Historical methodology boundary + per-episode warnings:
    - Lines from `stress_conclusions.data_quality_warnings` and `data_trust_summary.user_summary_lines`:
      - "Historical stress: 2 of 5 episodes have incomplete or low-confidence data."
      - dotcom/2008 insufficient_data explanations.
  - Aggregated `historical_episodes_with_limited_data=2`.
- `diagnosis_summary_en` for Block 3.4:
  - States:
    - Worst synthetic scenario id and loss.
    - Worst historical episode id and max drawdown.
    - Main hedge gap risk type and offset coverage.
    - Presence of data-quality warnings.
- Diagnostic-only check:
  - Recursive scan over `current_portfolio_stress_scorecard_v1` finds **no** fields:
    - `pass`, `loss_ok`, `max_dd_limit`, `diagnostic_codes`, `primary_diagnostic_code`, `fail_reason_code`, `failed_scenario`, `failed_test`.
  - `loss_gate_mode` on the block is `"diagnostic"`; mandate semantics remain only in legacy scorecard and suite summaries, not inside Block 3.4 product key.

## 4. Tests and verification

Commands executed (repo root):

```bash
python -m pytest -q tests/test_current_portfolio_stress_scorecard_v1_contract.py \
  tests/test_stress_scenario_coverage_contract.py \
  tests/test_stress_results_block_contract.py \
  tests/test_hedge_gap_analysis_v1_contract.py \
  tests/test_stress_scorecard_contract.py \
  tests/test_stress_diagnostic_mode.py

python scripts/verify_docs.py
```

Results:

- `tests/test_current_portfolio_stress_scorecard_v1_contract.py`: PASS
  - Verifies presence/shape of Block 3.4, linkage to `stress_results_v1` and `hedge_gap_analysis_v1`, correct worst selectors, and absence of mandate keys.
- Existing Stress Lab contract tests (Blocks 3.1–3.3) and diagnostic-mode tests: PASS (total 122 tests in the bundle).
- `scripts/verify_docs.py`: `docs verification: OK`.

## 5. Conclusion

Block 3.4 Current Portfolio Stress Scorecard is **Accepted** as Core MVP:

- Contract key: `current_portfolio_stress_scorecard_v1` on `stress_report.json`.
- Block 3.4 summarizes Blocks 3.1–3.3 for the current portfolio only and remains strictly diagnostic:
  no client mandate comparison, no DIAG_* or pass/fail semantics inside the product key.
- Live portfolio-first run on root `config.yml` produces a populated Block 3.4 object for
  `Main portfolio/analysis_subject/stress_report.json` that correctly identifies worst synthetic and
  historical scenarios, main loss/risk contributors, factor drivers, helped vs hurt assets, offset
  coverage ratio, main hedge gap, and data-quality warnings.

