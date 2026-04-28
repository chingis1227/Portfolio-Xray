# Portfolio Optimization — единая точка входа

Система строит портфель **одностадийной** оптимизацией (максимизация ожидаемой доходности при мягких целях по волатильности/доходности и ограничениях по **весу**), затем ProLiquidity и диагностический стресс. **RC_vol** в отчётах — диагностика, не жёсткий constraint. Веса выдаёт только оптимизатор; ручная правка весов в конфиге не допускается (исключение — протокол «View After Optimization»).

---

## Пайплайн

1. **Оптимизация**  
   ```bash
   python run_optimization.py [--no-cache] [--write-config]
   ```  
   Читает `config.yml` и при необходимости **`../config/client_profiles.yml`** (путь относительно корня репозитория); загружает данные; один проход оптимизатора + ProLiquidity. Пишет **`portfolio_weights.yml`** и **`run_result.json`** в **`output_dir_final`** (по умолчанию **Main portfolio**). При провале мандата MaxDD — **FAIL_MANDATE**, веса не записываются.

2. **Отчёт**  
   ```bash
   python run_report.py [--no-cache] [--clear-cache] [--backtest-mode dynamic_nan_safe]
   ```  
   Берёт веса из конфига или из **`portfolio_weights.yml`**; метрики 3Y/5Y/10Y, RC_vol, стресс; CSV в `results_csv/`, отчёты в `output_dir_final`.

**Порядок:** сначала `run_optimization.py`, затем `run_report.py`.

---

## Конфигурация

| Файл | Назначение |
|------|------------|
| **config.yml** | Тикеры, валюта, профиль, ликвидность, cash_policy, target_vol, target_max_drawdown_pct, окна, `output_dir_final`. |
| **config/client_profiles.yml** | Шаблоны профилей: vol, MaxDD, целевая доходность и др. **Блочный risk budget не используется.** |
| **assets.yml** | Метаданные активов. Опционально. |

Пример: **config.yml.example**. Файла **`blocks_universe.yml`** в текущей модели нет.

---

## Документация (источники истины)

Пути ниже — от **корня репозитория** (папка с `run_optimization.py`):

- [Portfolio Construction Policy](../docs/portfolio_construction_policy.md)  
- [Metrics Specification](../metrics_specification.md)  
- [Data policy, NaN, young ETFs](../docs/data_policy_nan_young_etfs.md)  
- [Feasibility constraints](../docs/docs/feasibility_constraints_spec.md)  
- [Optimization run checks](../docs/optimization_run_checks.md)  
- [Stress testing spec](../docs/docs/stress_testing_spec.md)  
- [Production workflow](../docs/production_workflow.md)  
- [View After Optimization](../docs/docs/view_after_optimization_spec.md)  

---

## Дополнительно

- **View After Optimization:** `run_view_after_optimization.py`.  
- **Мандат MaxDD:** только **реализованная** просадка на полной пересекающейся истории → **FAIL_MANDATE**; стресс **DIAG_*** не блокирует выпуск весов при успешном мандате.
