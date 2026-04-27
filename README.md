# Portfolio Optimization — единая точка входа

Система строит портфель **одностадийной** оптимизацией (максимизация ожидаемой доходности при мягких целях по волатильности/доходности и **per-asset** ограничениях на вклад в риск), затем ProLiquidity и диагностический стресс. Веса выдаёт только оптимизатор; ручная правка весов в конфиге не допускается (исключение — протокол «View After Optimization»).

---

## Пайплайн

1. **Оптимизация**  
   ```bash
   python run_optimization.py [--no-cache] [--write-config]
   ```  
   Читает `config.yml` и при необходимости **`config/client_profiles.yml`**; подтягивает рыночные данные; считает ковариации и **один** проход оптимизатора (`run_max_return_optimization`); ProLiquidity; опционально dual-horizon (10Y + 5Y) для `robustness_report.json`. Пишет веса в **`portfolio_weights.yml`** и **`run_result.json`** в каталог **`output_dir_final`** (по умолчанию **Main portfolio**). При провале **мандата MaxDD** веса не записываются, выход с ошибкой (**FAIL_MANDATE**).

2. **Отчёт**  
   ```bash
   python run_report.py [--no-cache] [--clear-cache] [--backtest-mode dynamic_nan_safe]
   ```  
   Берёт веса из `config.yml` или из **`portfolio_weights.yml`** в `output_dir_final`; считает метрики по окнам 3Y/5Y/10Y, RC_vol, стресс, снимки. Пишет CSV в `output_dir_csv` (часто **`results_csv/`**), JSON и HTML/text отчёты в **`output_dir_final`**.

**Порядок:** сначала `run_optimization.py`, затем `run_report.py`. Иначе отчёт будет без актуальных весов.

---

## Конфигурация

| Файл | Назначение |
|------|------------|
| **config.yml** | Основные настройки: тикеры, валюта, профиль, ликвидность, cash_policy, target_vol, target_max_drawdown_pct, `rc_asset_cap_pct`, окна, `output_dir_final`. Веса в конфиг не вводятся — они результат оптимизации. |
| **config/client_profiles.yml** | Шаблоны по профилям (ultra_conservative … aggressive): целевая волатильность, MaxDD, целевая номинальная доходность и др. При `client_profile` в `config.yml` недостающие поля подставляются из профиля. |
| **assets.yml** | Метаданные активов (например валюта). Опционально. |

Пример полного конфига: **config.yml.example**. Файла **`blocks_universe.yml`** в текущей модели **нет**; параметры **`rc_block_targets`** / блочный risk budget **не используются**.

---

## Документация (источники истины)

- **Политика и метрики**  
  - [Portfolio Construction Policy](docs/portfolio_construction_policy.md) — одностадийный оптимизатор, RC по активам, mandate, стресс как диагностика.  
  - [Metrics Specification](metrics_specification.md) — формулы метрик, окна, ddof=1, RC_vol, FX.  
  - [PROJECT_RULES.md](PROJECT_RULES.md) — стандарт частоты, дат, бенчмарков.

- **Данные и бэктест**  
  - [Data policy, NaN, young ETFs](docs/data_policy_nan_young_etfs.md) — join policy, перераспределение NaN среди риск-активов, RC-gated fallback к кэшу.

- **Оптимизация и ограничения**  
  - [Optimization specs (оглавление)](docs/docs/README.md) — ProLiquidity, View After Optimization.  
  - [Feasibility constraints](docs/docs/feasibility_constraints_spec.md) — формула RC cap, лимиты весов.  
  - [Optimization run checks](docs/optimization_run_checks.md) — точки отказа, сеть, противоречия параметров.

- **Стресс и View After Optimization**  
  - [Stress testing spec](docs/docs/stress_testing_spec.md) — сценарии, Loss / RC Top1–Top3, исторические эпизоды, коды **DIAG_***.  
  - [View After Optimization](docs/docs/view_after_optimization_spec.md) — разрешённый «тильт» после оптимизации.

- **Продакшен**  
  - [Production workflow](docs/production_workflow.md) — что блокирует запись весов, статусы **APPROVED** / **OK_FALLBACK**.

---

## Дополнительно

- **View After Optimization:** отдельный скрипт `run_view_after_optimization.py` (см. спеку выше).  
- **Мандат MaxDD:** при заданном `target_max_drawdown_pct` запись весов блокирует только **реализованная просадка на полной пересекающейся месячной истории** (см. `run_result.json`, `mandate_check`, **FAIL_MANDATE**). Сценарный стресс — **диагностика** (**DIAG_***), не блокирует выпуск весов.
