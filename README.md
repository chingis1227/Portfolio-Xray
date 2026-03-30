# Portfolio Optimization — единая точка входа

Система строит портфель по risk-budget (Growth / Duration / Inflation), применяет ProLiquidity и стресс-тесты. Веса выдаёт только оптимизатор; ручная правка весов в конфиге не допускается (исключение — протокол «View After Optimization»).

---

## Пайплайн

1. **Оптимизация**  
   ```bash
   python run_optimization.py [--no-cache] [--write-config] [--profile Growth] [--single-stage]
   ```  
   По умолчанию — **двухэтапная** RiskPortfolio-оптимизация (см. [docs/two_stage_optimization.md](docs/two_stage_optimization.md)). Флаг **`--single-stage`** — legacy одноэтапный прогон. Читает `config.yml`, при необходимости — `config/client_profiles.yml` и `blocks_universe.yml`; загружает данные; выполняет block selection (Duration/Inflation), risk-budget оптимизацию и ProLiquidity. Пишет веса в **ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/portfolio_weights.yml** и **run_result.json**. При срабатывании MaxDD gate веса не записываются, выход с ошибкой.

2. **Отчёт**  
   ```bash
   python run_report.py [--no-cache] [--clear-cache] [--backtest-mode dynamic_nan_safe]
   ```  
   Берёт веса из конфига или из **ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/portfolio_weights.yml**; считает метрики по окнам 3Y/5Y/10Y, RC_vol, стресс, отчёты. Пишет CSV в `results_csv/`, JSON и report в **ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/**.

**Порядок:** сначала `run_optimization.py`, затем `run_report.py`. Иначе отчёт будет без актуальных весов.

---

## Конфигурация

| Файл | Назначение |
|------|------------|
| **config.yml** | Основные настройки: тикеры, валюта, профиль, ликвидность, cash_policy, target_vol, target_max_drawdown_pct, окна. Веса в конфиг не вводятся — они результат оптимизации. |
| **config/client_profiles.yml** | Шаблоны риска по профилям (ultra_conservative … aggressive): rc_block_targets, target_vol_annual, target_max_drawdown_pct. При указании `client_profile` в config.yml недостающие поля подставляются из профиля. |
| **blocks_universe.yml** | Привязка тикеров к блокам: Growth, Growth_HY, Duration, Inflation, Liquidity, Tail. Каждый тикер из config.tickers должен быть ровно в одном блоке. |
| **assets.yml** | Метаданные активов (например валюта). Опционально. |

Пример полного конфига: **config.yml.example**.

---

## Документация (источники истины)

- **Политика и метрики**  
  - [Portfolio Construction Policy](docs/portfolio_construction_policy.md) — роли блоков, иерархия правил, mandate, risk budget, stress.  
  - [Two-stage optimization](docs/two_stage_optimization.md) — каноническая двухэтапная RiskPortfolio-оптимизация (по умолчанию в `run_optimization.py`).  
  - [Metrics Specification](metrics_specification.md) — формулы метрик, окна, ddof=1, RC_vol, FX.  
  - [PROJECT_RULES.md](PROJECT_RULES.md) — стандарт частоты, дат, бенчмарков.

- **Данные и бэктест**  
  - [Data policy, NaN, young ETFs](docs/data_policy_nan_young_etfs.md) — join policy, within-block redistribution, RC-gated fallback.

- **Оптимизация и ограничения**  
  - [Two-stage optimization](docs/two_stage_optimization.md) — этапы, конфиг, legacy `--single-stage`.  
  - [Optimization specs (оглавление)](docs/docs/README.md) — ссылки на спеки по блокам и ликвидности.  
  - [Feasibility constraints](docs/docs/feasibility_constraints_spec.md) — RC cap, weight caps, Growth HY/EM_debt.  
  - [Optimization run checks](docs/optimization_run_checks.md) — точки отказа, сеть, противоречия параметров.

- **Стресс и View After Optimization**  
  - [Stress testing spec](docs/docs/stress_testing_spec.md) — сценарии, Loss/Role/RC, коды FAIL.  
  - [View After Optimization](docs/docs/view_after_optimization_spec.md) — единственный разрешённый «тильт» после оптимизации.

---

## Дополнительно

- **View After Optimization:** отдельный скрипт `run_view_after_optimization.py` (см. спеку выше).  
- **Мандат MaxDD:** при заданном `target_max_drawdown_pct` блокирует запись весов только **реализованная просадка на полной пересекающейся месячной истории** портфеля (см. `run_result.json`, `mandate_check`, статус **FAIL_MANDATE**). Сценарные стресс-тесты — диагностика (**DIAG_***), не блокируют выпуск.
