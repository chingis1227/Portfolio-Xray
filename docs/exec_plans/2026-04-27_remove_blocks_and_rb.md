# Удаление блочной архитектуры (Growth / Duration / Inflation) и risk budgeting

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. Maintenance follows [PLANS.md](../../PLANS.md) at the repository root.

## Purpose / Big Picture

After this change, the portfolio system no longer assigns tickers to structural blocks or enforces a Growth/Duration/Inflation risk budget. The user configures a ticker list and a client profile (or explicit targets): annual target volatility, maximum drawdown, nominal return target, and optional liquidity floor. The optimizer runs a single stage that maximizes estimated expected return subject to soft penalties for vol and return, plus per-asset risk-contribution caps from the global feasibility formula. Stress testing reports scenario losses and per-asset concentration diagnostics without block role checks. You see this working by running `python run_optimization.py` then `python run_report.py` (or the EW/RP scripts): `run_result.json` has no `rc_block_targets`, `rb_deltas_pp`, or `pnl_by_block_pct`; `pytest` passes.

## Progress

- [x] (2026-04-27) ExecPlan created; implementation started.
- [x] M3–M6, M5: `config.yml`, schema/profiles, `feasibility`/`risk_contrib`/`optimization`, удалены `blocks.py` / `block_selection` / `blocks_universe.yml`; `run_optimization.py` одностадийный; `stress.py` без role/blocks; `portfolio_dynamic` глобальный redistribution.
- [x] M7: `run_report`, `run_compare_ew_rp`, `io_export` ips_summary, `snapshot`, `portfolio_commentary`, `pdf_reports` EW/RP — блочные куски убраны/загейтены; корневые `compare_*_main.py` переведены на новый API без `block_selection` / RB.
- [x] M8: тесты обновлены/удалены устаревшие; `pytest tests/ -q` — зелёный.
- [x] M2 (частично): новый `docs/portfolio_construction_policy.md`, удалены `two_stage_optimization.md` и `optimization_*_spec.md`; обновлены `data_policy_nan_young_etfs.md`, cursor rules, `config.yml.example`, `config_ui/app.py`.
- [x] M9: полный цикл Main + EW + RP (Balanced), `run_report` после Main; таблица — `_compare_post_remove_blocks/M9_post_run_2026-04-27.md`.
- [x] M10: decision point зафиксирован в M9 markdown («замена архитектуры — отдельно»); численные выводы — в таблице M9.
- [x] (2026-04-27) Стресс: синтетический `pass` только по **Portfolio PnL ≥ −MaxDD**; RC — диагностика (`rc_diagnostic_codes`, `rc_attention_codes`, `WARN_RC_SYNTHETIC_CONCENTRATION`); в JSON сценариев — `pnl_by_asset_pct`, `pnl_by_factor_pct`; исторический эпизод **dotcom** (2000-03-01 — 2002-10-31) в `HISTORICAL_EPISODES`; спека `stress_testing_spec.md` и комментарии синхронизированы.
- [x] (2026-04-27) Удалены **tail overlay** (`tail_target_weight_pct`, `_apply_tail_overlay`), режим **HEDGE** во view-after; переименование оптимизатора **`run_max_return_optimization`** (вместо `run_risk_budget_optimization`); спека `view_after_optimization_spec.md` переписана под тактический тильт.

## Surprises & Discoveries

- Оптимизатор (`run_max_return_optimization`, ранее историческое имя `run_risk_budget_optimization`) принимает список `risk_tickers`; `run_optimization` передаёт список колонок, не dict блоков.
- Тест `test_resampled_optimization_helpers` отвязан от `compare_resampled_optimization_main` (раньше были legacy импорты `block_selection` — скрипты переписаны).
- `docs/docs/stress_testing_spec.md`: в §0–1 добавлено примечание, что Role-тесты сняты с production `run_stress`; §6 остаётся как архив.
- Каталог `research/`: удалены все Python-скрипты и CSV/TXT артефакты блочных экспериментов; остался только `README.md`.

## Decision Log

- Decision: Remove `blocks_universe.yml` entirely; tickers are only validated as a non-empty list without block membership.
  Rationale: Plan specifies full removal of block mapping.
  Date: 2026-04-27

- Decision: Keep `liquidity_floor_pct` in client profiles; remove only `risk_budget` (G/D/I) from profiles.
  Rationale: Plan §1.2 — liquidity hint remains for config hints.
  Date: 2026-04-27

## Outcomes & Retrospective

- Рефакторинг закрыт: production-путь без блоков/RB; `pytest tests/ -q` зелёный; M9 задокументирован в `_compare_post_remove_blocks/M9_post_run_2026-04-27.md`.
- Папка `research/`: блочные свипы и скрипты с `block_selection` удалены; остаётся только `README.md` как заглушка под будущие ad-hoc прогоны.

## Context and Orientation

The repository root contains `config.yml` (tickers, `client_profile`, output paths), `run_optimization.py` (Main policy optimizer entry), `src/optimization.py` (numerical optimizer), `src/stress.py` (scenario PnL and diagnostics), `policy_math/feasibility.py` (RC cap formulas), `src/config.py` and `src/config_schema.py` (load and validate config). Previously `blocks_universe.yml` mapped each ticker to exactly one of Growth, Duration, Inflation, Liquidity, Tail; that file and all RB fields are removed.

## Plan of Work

See the approved implementation plan (remove blocks risk budget): simplify optimizer to single-stage `max_return`, strip stress block aggregations and role tests, rewrite policy docs, update tests and compare scripts, run full pipeline and save `_compare_post_remove_blocks/` evidence.

## Concrete Steps

Working directory: repository root.

    python -m pytest tests/ -q

After implementation, expect all non-skipped tests to pass. Run optimization and reports per `README.md` / operational runbook as needed for M9.

## Validation and Acceptance

- `pytest` completes with zero failures.
- `run_result.json` from Main contains no `rb_target_selection`, `rb_deltas_pp`, `pnl_by_block_pct`, or `rc_block_targets` as persisted RB architecture fields.
- No import of `src.blocks` or `src.block_selection` in production path (`run_optimization`, `run_report`).

## Idempotence and Recovery

Re-running `pytest` and optimization is safe. Git history preserves pre-change state.

## Artifacts and Notes

Baseline for comparison: existing `Main portfolio/`, `equal-weight portfolio/`, `risk parity portfolio/` outputs before this change (or snapshot paths noted in Progress). Post-change artifacts under `_compare_post_remove_blocks/` after M9.

## Interfaces and Dependencies

- `resolve_rc_asset_cap(n_assets: int) -> float` — global §1 cap only (no `equity_only`).
- `build_rc_cap_per_ticker` — returns `{ticker: cap}` with same scalar for every risk ticker (excluding cash proxy from cap set as today).
- Config validated without `blocks_universe.yml`.
