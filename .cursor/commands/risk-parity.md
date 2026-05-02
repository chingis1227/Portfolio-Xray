---
description: Full Risk-Parity baseline run — metrics, stress, EW vs RP comparison + PDF
---

Сделай **полный прогон Risk-Parity baseline** строго по правилам проекта (один вариант за запрос — не пересчитывай Main / Equal-Weight без отдельной просьбы).

### 1) Запуск (единственная обязательная команда)

Из **корня репозитория** (где лежат `config.yml` и скрипты):

```bash
python run_risk_parity.py
```

Этот скрипт уже:
- строит risk-parity веса по той же eligible-вселенной и данным, что baseline-политика (без RC caps / policy-оверлеев — см. docstring скрипта);
- при статусе **OK** или **APPROXIMATE** прогоняет **полный** отчёт через `run_portfolio_report_for_weights` (метрики, стресс, CSV, JSON, `commentary.txt` / stress commentary по пайплайну);
- при **infeasible** baseline пишет только `summary.json` / `summary.txt` и **завершается** без полного отчёта — не ожидай полного набора метрик/stress/CSV;
- в конце вызывает **`try_rebuild_pdfs_after_variant`**: обновляет сравнение **EW vs RP** (`run_compare_ew_rp.py`) и пересобирает PDF в `pdf files/`.

**Не** добавляй ручных правок весов в `config.yml`.

### 2) После успеха — прочитай и кратко покажи ключевые результаты

Каталог артефактов: **`risk parity portfolio/`** в корне репозитория (не `ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/` и не другие корни).

Обязательно проверь наличие и смысл:
- `risk parity portfolio/summary.txt`, `risk parity portfolio/summary.json`
- `risk parity portfolio/weights.json`, `weights.txt` (если есть)
- `risk parity portfolio/stress_report.json`
- `risk parity portfolio/commentary.txt`, `stress_commentary.txt` (если сгенерированы)
- `risk parity portfolio/results_csv/` — rolling factor betas, матрицы корреляций и пр. по правилам стресс-факторов

В ответе пользователю выведи:
- статус baseline и солвера (`summary.json` / `summary.txt`: `status`, при **APPROXIMATE** — заметка из summary)
- **топ-10 весов** по убыванию
- **RC_vol по активам** — из `weights.txt`; **RC source:** solver / target parity (диагностика солвера; при fallback см. логику в `run_risk_parity.py`)
- **solver_status**, **max_rc_error** (если есть в `summary.json`)
- ключевые метрики окна: CAGR, Vol, MaxDD, Sharpe, Sortino, Beta (`beta_portfolio`), Corr_base — что есть в summary
- stress: `status` из `stress_report.json` / summary, fail/skip reason, **Client-fit (MaxDD gate)** / `portfolio_valid` из summary или meta
- подтверждение, что лог/вывод не показал падения `run_compare_ew_rp.py` или PDF (если были — цитируй warning)

### 3) Если прогон упал или baseline infeasible

- Покажи точную причину и этап (валидация конфига / данные / infeasible RP / стресс / PDF).
- Если **infeasible**: опиши `reason` из summary; укажи, что полный пайплайн не запускался.
- Укажи, какие файлы в `risk parity portfolio/` всё же созданы.
- Предложи следующий шаг (например, проверка `config.yml`, кэш, число eligible активов, pandoc/xelatex для PDF).

### 4) Опционально (только если пользователь явно просит)

- **Триплет Policy vs EW vs RP** обновляется после полного отчёта Main (`run_report` / оптимизация с отчётом), не этим скриптом. Не запускай `run_compare_variants.py` без явной просьбы обновить сравнение с Policy.
