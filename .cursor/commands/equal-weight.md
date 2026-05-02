---
description: Полный прогон Equal-Weight baseline, метрик, стресса и финализация (EW vs RP + PDF)
---

Сделай **полный прогон Equal-Weight** строго по правилам проекта (один вариант за запрос — не пересчитывай Main / Risk Parity без отдельной просьбы).

### 1) Запуск (единственная обязательная команда)

Из **корня репозитория** (где лежат `config.yml` и скрипты):

```bash
python run_equal_weight.py
```

Этот скрипт уже:
- строит равные веса по той же вселенной и правилам покрытия, что и policy-отчёт;
- прогоняет **полный** отчёт через `run_portfolio_report_for_weights` (метрики, стресс, CSV, JSON, `commentary.txt` / stress commentary по пайплайну);
- в конце вызывает **`try_rebuild_pdfs_after_variant`**: обновляет сравнение **EW vs RP** (`run_compare_ew_rp.py`) и пересобирает PDF в `pdf files/`.

**Не** добавляй ручных правок весов в `config.yml`.

### 2) После успеха — прочитай и кратко покажи ключевые результаты

Каталог артефактов: **`equal-weight portfolio/`** (не выдумывай другие корни).

Обязательно проверь наличие и смысл:
- `equal-weight portfolio/summary.txt`, `equal-weight portfolio/summary.json`
- `equal-weight portfolio/weights.json`, `weights.txt` (если есть)
- `equal-weight portfolio/stress_report.json`
- `equal-weight portfolio/commentary.txt`, `stress_commentary.txt` (если сгенерированы)
- `equal-weight portfolio/results_csv/` — rolling betas, матрицы и пр. по правилам стресс-факторов

В ответе пользователю выведи:
- статус baseline (`summary.json` / `summary.txt`)
- топ весов по убыванию
- ключевые метрики окна (CAGR, Vol, MaxDD, Sharpe, Sortino, Beta, Corr_base — что есть в summary)
- stress: `status`, причина сбоя/предупреждения, client-fit / portfolio_valid если есть в meta/summary
- подтверждение, что лог/вывод не показал падения `run_compare_ew_rp.py` или PDF (если были — цитируй warning)

### 3) Если прогон упал

- Покажи точную причину и этап (данные / feasibility / стресс / PDF).
- Укажи, какие файлы в `equal-weight portfolio/` всё же созданы.
- Предложи следующий шаг (например, проверка `config.yml`, кэш, pandoc/xelatex для PDF).

### 4) Опционально (только если пользователь явно просит)

- **Триплет Policy vs EW vs RP** обновляется после полного отчёта Main (`run_report` / оптимизация с отчётом), не этим скриптом. Не запускай `run_compare_variants.py` без явной просьбы обновить сравнение с Policy.
