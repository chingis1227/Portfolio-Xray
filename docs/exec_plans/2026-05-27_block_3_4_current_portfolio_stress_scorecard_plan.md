# Block 3.4 Current Portfolio Stress Scorecard MVP

**Status: Completed** (Sessions 00–06 closed 2026-05-27). Prerequisites: Block 3.1 Scenario Library **Done**; Block 3.2 Stress Results **Done** (`stress_results_v1`); Block 3.3 Hedge Gap Analysis **Done** (`hedge_gap_analysis_v1`).

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows [PLANS.md](../../PLANS.md) from the repository root.

**Canonical specs (read order):**

- [docs/specs/stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) — Block 3 boundary and existing block keys
- [docs/specs/stress_testing_spec.md](../specs/stress_testing_spec.md) — scenario definitions and evidence fields
- [docs/specs/hedge_gap_analysis_spec.md](../specs/hedge_gap_analysis_spec.md) — Block 3.3 v1 outputs (offset coverage + main hedge gap)

## Purpose / Big Picture

After this change, a portfolio-first operator running:

    (repo root) > python run_portfolio_review.py --skip-candidates

can open:

    Main portfolio/analysis_subject/stress_report.json

and read a **single product-facing Block 3.4 object** that summarizes the current portfolio’s stress diagnosis across Blocks 3.1–3.3:

- where the portfolio loses the most (synthetic loss vs historical episode loss),
- which synthetic scenario is worst (by minimum portfolio_pnl_pct),
- which historical episode is worst (by minimum max_dd),
- which assets hurt the most and which assets helped,
- which assets create the most risk concentration (Top1/Top3 RC under stress covariance),
- which factor channels explain losses (pnl_by_factor_pct + conclusions),
- how much helped assets offset losses from hurt assets (offset coverage ratio),
- what the main hedge gap is (weakest protection area / mapped risk type),
- what data is missing or insufficient for confident interpretation.

**Product boundary (non-negotiable):** this is diagnostic-only. Block 3.4 must not reintroduce:
client mandate comparisons, max drawdown limits as pass/fail, DIAG_LOSS_* / DIAG_HIST_* language, suitability logic, or client-profile logic. Block 3.4 is a summary layer over already computed stress outputs; it is not a new stress engine.

## Progress

- [x] (2026-05-27) Session 00 — ExecPlan created and registered Active in docs/exec_plans/README.md.
- [x] (2026-05-27) Session 01 — Field audit: map required Block 3.4 fields to existing JSON evidence; record unavailable fields and reasons.
- [x] (2026-05-27) Session 02 — Implement builder module for `current_portfolio_stress_scorecard_v1` (pure adapter over Blocks 3.1–3.3) + empty fallback.
- [x] (2026-05-27) Session 03 — Wire block attachment into stress-report build path(s) (ensure it appears on portfolio-first subject runs).
- [x] (2026-05-27) Session 04 — Contract tests for Block 3.4 + regression bundle run (Block 3.1–3.3 + diagnostic mode).
- [x] (2026-05-27) Session 05 — Docs sync: specs + OUTPUTS/PRODUCT/SPEC/TESTING/CHANGELOG/DECISIONS updated for new Block 3.4 key.
- [x] (2026-05-27) Session 06 — Live validation run on current `config.yml` subject and audit notes.

## Surprises & Discoveries

- Observation: All required Block 3.4 fields (worst synthetic/historical, top loss contributors, factor drivers, helped/hurt assets, hedge gap) уже присутствуют в связке `stress_results_v1` + `hedge_gap_analysis_v1`; отдельного score-engine или новых полей не потребовалось.
  Evidence: `Main portfolio/analysis_subject/stress_report.json` envelope `worst_synthetic` / `worst_historical`, synthetic/historical rows, `hedge_gap_analysis_v1.summary.main_hedge_gap` и `by_risk_type[]`.

- Observation: Data quality предупреждения для исторических эпизодов уже собраны в `stress_conclusions.data_quality_warnings` и `data_trust_summary.user_summary_lines`.
  Evidence: `stress_report.json.stress_conclusions.data_quality_warnings` и `stress_report.json.data_trust_summary.user_summary_lines` для dotcom/2008.

- Observation: Live-run subject показывает согласованный вывод: worst synthetic = `recession_severe`, worst historical = `2022`, main hedge gap = `equity_crash_protection` с offset coverage 0.0%.
  Evidence: `Main portfolio/analysis_subject/stress_report.json.current_portfolio_stress_scorecard_v1` блок после `run_portfolio_review.py --skip-candidates`.

## Decision Log

(Record every contract or design decision made while implementing the plan.)

- Decision: Deliver Core MVP Block 3.4 as a **new top-level key** on `stress_report.json`: `current_portfolio_stress_scorecard_v1` (instead of repurposing existing `stress_scorecard_v1`).
  Rationale: Existing `stress_scorecard_v1` includes legacy mandate-mode semantics (`DIAG_*`, `pass`, `loss_ok`) and has dedicated contract tests. Block 3.4 product definition is diagnostic-only and must avoid mandate/pass-fail language. A new key avoids breaking legacy and makes the Core MVP contract explicit.
  Date/Author: 2026-05-27 / Session 00.

## Outcomes & Retrospective

- Outcome: Block 3.4 Core MVP реализован как `current_portfolio_stress_scorecard_v1` на `stress_report.json`, поверх уже существующих Blocks 3.1–3.3. Блок даёт единое диагностическое резюме: worst synthetic, worst historical, top loss/risk contributors, факторные драйверы, helped/hurt assets, offset coverage и main hedge gap.
- Outcome: Новый блок подключён во все пути сборки stress_report (портфель-first `run_report.py --materialize-analysis-subject`, legacy `run_optimization.py`, прямой `run_stress`), без изменений сценариев и без изменения контрактов Blocks 3.1–3.3.
- Outcome: Добавлены контрактные тесты `tests/test_current_portfolio_stress_scorecard_v1_contract.py`, расширен стресс-бандл в TESTING.md, обновлены specs/OUTPUTS/PRODUCT/SPEC/DECISIONS/CHANGELOG; `scripts/verify_docs.py` проходит.
- Outcome: Live прогон `python run_portfolio_review.py --skip-candidates` на текущем `config.yml` подтверждает, что subject `Main portfolio/analysis_subject/stress_report.json` содержит заполненный Block 3.4 с корректной линковкой к `stress_results_v1` и `hedge_gap_analysis_v1`.
- Lessons: Для scorecard-слоёв Core MVP достаточно adapter-подхода над уже нормализованными блоками (Blocks 3.2–3.3); важно явно разделять diagnostic-only Core MVP (`current_portfolio_stress_scorecard_v1`) и legacy scorecard (`stress_scorecard_v1`) с мандатной семантикой, чтобы не мешать продуктовые и governance-граня.

## Context and Orientation

### Where the stress report is built

The stress artifact is `stress_report.json`. For portfolio-first runs the primary file to read is:

    Main portfolio/analysis_subject/stress_report.json

`src/stress.py:run_stress` builds the raw stress evidence (`scenario_results`, `historical_results`) and attaches product layers:

- Block 3.2: `stress_results_v1` (product adapter over evidence rows)
- Block 3.3: `hedge_gap_analysis_v1` (contribution-based offset coverage and main hedge gap)

Block 3.4 will be attached on the same `stress_report` dict as an additional product-facing summary key.

### Block 3.4 required output structure (v1)

Write:

    stress_report["current_portfolio_stress_scorecard_v1"]

with the following keys:

- version
- block: "3.4"
- scenario_library snapshot
- loss_gate_mode
- worst_synthetic_scenario
- worst_historical_scenario
- portfolio_loss_summary
- historical_drawdown_summary
- top_loss_contributors
- top_risk_contributors
- factor_stress_attribution_summary
- assets_helped_hurt_summary
- offset_coverage_summary
- main_hedge_gap
- data_quality_warnings
- diagnosis_summary_en

### Data sources (linkage rules; no recompute)

Block 3.4 must be an adapter over existing outputs (do not rerun stress or invent fields):

- Block 3.1: scenario universe IDs and raw evidence rows:
  - `scenario_results[*]` (synthetic; includes `portfolio_pnl_pct`, `pnl_by_asset_pct`, `pnl_by_factor_pct`, RC top1/top3)
  - `historical_results[*]` (historical; includes `pnl_real_episode`, `max_dd`, `data_quality`, coverage fields)
- Block 3.2: `stress_results_v1` (preferred product-level access for worst-synthetic/historical and per-scenario/episode summaries)
- Block 3.3: `hedge_gap_analysis_v1` (preferred for offset coverage ratio and main hedge gap + helped/hurt lists by risk type)

### Methodology requirements (must match product definition)

- Worst synthetic: minimum `portfolio_pnl_pct` (synthetic loss).
- Worst historical: minimum `max_dd` (drawdown), not minimum `pnl_real_episode`.
- Portfolio loss:
  - Synthetic: `portfolio_pnl_pct`
  - Historical: `pnl_real_episode`
- Historical drawdown: `max_dd`
- Loss contribution: use `top3_loss_assets` and `pnl_by_asset_pct`.
- Asset risk contribution: use `top1_rc_*` and `top3_rc_*` (synthetic RC diagnostics).
- Factor stress attribution: use `pnl_by_factor_pct` and `stress_conclusions` where available.
- Offset coverage ratio + main hedge gap: use Block 3.3 `hedge_gap_analysis_v1` where available.
- Missing data must yield explicit `unavailable` / `insufficient_data` disclosures, not silent omission.

## Plan of Work

### Session 01 — Audit current artifacts and existing scorecard logic

Goal: Precisely map every required Block 3.4 field to its source in `stress_report.json` and existing product layers.

Scope:

- Inspect the subject stress report example: `Main portfolio/analysis_subject/stress_report.json`.
- Inspect current product builders:
  - `src/stress_results_block.py` (Block 3.2)
  - `src/hedge_gap_analysis_block.py` (Block 3.3)
- Inspect existing legacy scorecard and its tests:
  - `src/stress.py` (`_build_stress_scorecard_v1`)
  - `tests/test_stress_scorecard_contract.py`

Acceptance:

- We can answer, with exact paths, where each Block 3.4 output field comes from.
- Any missing/insufficient evidence is recorded in this plan with a clear “derive vs add vs unavailable” decision.
- We confirm Block 3.4 will not depend on mandate-mode-only fields.

### Session 02 — Implement Block 3.4 builder (adapter-only module)

Goal: Add a new module that builds `current_portfolio_stress_scorecard_v1` from existing evidence.

Work:

- Create `src/current_portfolio_stress_scorecard_block.py` with:
  - `build_current_portfolio_stress_scorecard_v1(stress_report: dict[str, Any]) -> dict[str, Any]`
  - `attach_current_portfolio_stress_scorecard_v1(stress_report: dict[str, Any]) -> None`
  - `empty_current_portfolio_stress_scorecard_v1(reason: str, *, loss_gate_mode: str) -> dict[str, Any]`
- Make the builder deterministic, diagnostic-only, and robust to missing sub-blocks.

Acceptance:

- The builder produces the required keys with stable shapes.
- Any missing data yields explicit `data_quality_warnings` and per-field “unavailable” disclosures (not exceptions).
- The block contains no mandate / pass-fail keys or DIAG_* wording.

### Session 03 — Wire Block 3.4 into the stress report generation path

Goal: Ensure portfolio-first runs produce Block 3.4 on subject `stress_report.json`.

Work:

- Wire `attach_current_portfolio_stress_scorecard_v1` after:
  - `attach_stress_results_v1(report)`
  - `attach_hedge_gap_analysis_v1(report)`
  in `src/stress.py:run_stress` and in any additional report enrichment/export paths that overwrite `stress_report.json`.

Acceptance:

- After a portfolio-first run, `Main portfolio/analysis_subject/stress_report.json` contains `current_portfolio_stress_scorecard_v1` with `block="3.4"`.
- The block’s `scenario_library` snapshot references the canonical scenario IDs (no drift).

### Session 04 — Tests

Goal: Add contract tests for Block 3.4 and run the relevant regression bundle.

Work:

- Add `tests/test_current_portfolio_stress_scorecard_v1_contract.py` that verifies:
  - Block exists and has required keys
  - Worst synthetic selection uses min loss (synthetic)
  - Worst historical selection uses min drawdown (max_dd)
  - Offset coverage and main hedge gap link to `hedge_gap_analysis_v1` when available
  - Forbidden mandate keys do not appear inside the block
  - Missing evidence results in explicit warnings / unavailable fields, not silent omission

Acceptance:

- New tests pass.
- Existing Block 3.1–3.3 tests remain green.

### Session 05 — Documentation sync

Goal: Make the new Block 3.4 key discoverable and correctly positioned in the product docs.

Work (minimum files to update):

- `docs/specs/stress_lab_layer_spec.md` (Block 3.4 contract; clarify legacy `stress_scorecard_v1` vs Core MVP `current_portfolio_stress_scorecard_v1`)
- `docs/specs/stress_testing_spec.md` (only if needed for the new key)
- `OUTPUTS.md` (add the new key under `stress_report.json` contract)
- `PRODUCT.md`
- `SPEC.md` (only if it enumerates Stress Lab keys)
- `TESTING.md` (add the new test to the recommended stress bundle)
- `CHANGELOG.md` (feature entry)
- `DECISIONS.md` (record the contract decision to add a new key)

Acceptance:

- Docs reflect that Block 3.4 summarizes Blocks 3.1–3.3 and is diagnostic-only.
- Docs clearly state Block 3.4 does not create new scenarios and does not use mandate pass/fail.

### Session 06 — Live validation (current config portfolio)

Goal: Prove behavior on the actual portfolio in `config.yml`.

Commands:

    (repo root) > python run_portfolio_review.py --skip-candidates

Inspect:

    Main portfolio/analysis_subject/stress_report.json

Acceptance:

- `current_portfolio_stress_scorecard_v1` exists and links to `stress_results_v1` + `hedge_gap_analysis_v1`.
- Worst synthetic scenario is correctly identified.
- Worst historical episode is correctly identified.
- Top loss contributors and top risk contributors are present.
- Factor attribution summary is present (or explicitly unavailable with reason).
- Offset coverage and main hedge gap are present when Block 3.3 provides them.
- No client mandate pass/fail language appears in the block.

## Concrete Steps

During implementation, use these commands (repo root unless stated otherwise):

    python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py
    python -m pytest tests/test_stress_scenario_coverage_contract.py
    python -m pytest tests/test_stress_results_block_contract.py
    python -m pytest tests/test_hedge_gap_analysis_v1_contract.py
    python -m pytest tests/test_stress_scorecard_contract.py
    python -m pytest tests/test_stress_diagnostic_mode.py
    python -m pytest tests/test_docs_verify.py

## Validation and Acceptance

Success is defined by:

1) A portfolio-first subject run produces a populated `current_portfolio_stress_scorecard_v1` under `analysis_subject/stress_report.json`.\n
2) The block is clearly linked to Block 3.1 scenario IDs, Block 3.2 `stress_results_v1`, and Block 3.3 `hedge_gap_analysis_v1`.\n
3) Worst synthetic and worst historical selection rules are correct.\n
4) No mandate / suitability / pass-fail semantics appear inside the Block 3.4 product key.\n
5) Missing evidence yields explicit warnings and unavailable disclosures.\n

## Idempotence and Recovery

- Re-running `python run_portfolio_review.py --skip-candidates` must be safe and should overwrite subject artifacts deterministically.
- If Block 3.4 fields are missing due to upstream missing data, the block must still exist with `data_quality_warnings` explaining the limitation.

## Artifacts and Notes

Keep short evidence excerpts (JSON snippets, test transcripts) in this section as the work proceeds.

## Interfaces and Dependencies

No new external dependencies. Implement Block 3.4 as a pure-Python adapter module within `src/`, using existing blocks and evidence dicts.

