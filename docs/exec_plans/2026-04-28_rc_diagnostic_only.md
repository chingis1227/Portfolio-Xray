# RC только как диагностика (не constraint)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. Maintenance follows [PLANS.md](../../PLANS.md) at the repository root.

## Purpose / Big Picture

После изменений веса портфеля не оптимизируются и не постобрабатываются под per-asset RC caps; в конфиге нет `rc_asset_cap_pct`, `rc_policy_mode`, `rc_cap_penalty_lambda`, `stress_top3_rc_sum_cap_pct`. Метрика **RC_vol** по окнам и в стресс-сценариях **Top1 / Top3** остаются в отчётах и JSON как числа для анализа. `stress_report.json` больше не содержит пороговых полей `rc_asset_cap_used`, `rc1_ok`, `rc3_ok`, `rc_attention_codes`. Проверка: `pytest tests/ -q`; при прогоне Main в `stress_report.json` есть `top1_rc_pct` / `top3_rc_sum_pct` на сценариях, нет `FAIL_RC` из-за RC в `run_result.json`.

## Progress

- [x] (2026-04-28) ExecPlan создан; начата реализация по списку файлов плана «RC как диагностика».
- [x] (2026-04-28) Код: оптимизация, стресс, NaN-safe, конфиг, view-after, сравнения, снимок/экспорт — без RC-constraint.
- [x] (2026-04-28) Документация и примеры: `feasibility_constraints_spec`, `stress_testing_spec`, `portfolio_construction_policy`, runbook, README, `config.yml.example`, view-after spec, data policy, production/optimization checks, описания файлов.
- [x] (2026-04-28) Тесты: `test_portfolio_commentary`, `test_stress_historical_fields`, `test_backtest_nan_safe` и полный `pytest tests/`.

## Surprises & Discoveries

- `rebuild_pdf_reports.py` без полного конфига/весов падает на валидации — ожидаемо; актуальные `pdf_md_sources/*.md` обновятся после успешного `run_optimization.py` / `run_report.py` и повторной пересборки PDF.

## Decision Log

- Decision: Удалить `resolve_rc_asset_cap` из `policy_math/feasibility.py`; оставить только `resolve_max_weight_per_asset_cap` (лимит веса по N).
  Rationale: План — отвязать feasibility от RC; max weight — отдельная политика.
  Date: 2026-04-28

- Decision: Не менять эвристику VOO/VT/VTI в `_alpha_shift_to_target_vol` (vol-targeting при `cash_policy=prohibited`).
  Rationale: Вне объёма плана; это не RC-postprocess.
  Date: 2026-04-28

## Outcomes & Retrospective

- RC_vol и Top1/Top3 в стрессе остаются для анализа; жёсткие капы, постобработка и RC-gating в бэктесте убраны; контракт JSON и спеки согласованы.

## Context and Orientation

Корень репозитория: `run_optimization.py`, `src/optimization.py` (objective + удаление `enforce_rc_caps_postprocess`), `src/stress.py` (`run_stress`), `src/risk_contrib.py` (RC_vol по окну), `src/portfolio_dynamic.py` (NaN-safe backtest), `src/config_schema.py`, `run_report.py`, `src/view_after_optimization.py`, тесты в `tests/`, документация в `docs/`.

## Plan of Work

Убрать RC из objective и постобработки; упростить `run_stress`; убрать RC-gating в dynamic backtest; вычистить конфиг и потребителей; обновить commentary и спеки; прогнать pytest.

## Concrete Steps

Рабочая директория: корень репозитория.

    python -m pytest tests/ -q

## Validation and Acceptance

- `pytest` без падений.
- `run_stress`: `pass` сценария = только `loss_ok`; нет полей `rc1_ok`, `rc3_ok`, `rc_asset_cap_used`, `stress_top3_rc_sum_cap`, `rc_attention_codes`.
- Оптимизация не вызывает `enforce_rc_caps_postprocess`; нет статуса `FAIL_RC` из-за RC.

## Idempotence and Recovery

Повторный прогон тестов и оптимизации безопасен; состояние до изменений в git.

## Artifacts and Notes

См. прикреплённый план в `.cursor/plans/` при необходимости сверки списка файлов.

## Interfaces and Dependencies

- `run_max_return_optimization(returns_df, risk_tickers, ...)` без `rc_asset_cap_pct` и `rc_cap_penalty_lambda`.
- `run_stress(..., target_max_drawdown_pct, cash_proxy_ticker, **_)` без RC-cap аргументов.
- `portfolio_returns_nan_safe(...)` без `rc_asset_cap_pct` / `rc_cap_by_ticker` / RC fallback.
