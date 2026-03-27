---
description: Запустить полную policy-оптимизацию портфеля и показать итог
---

Запусти полную оптимизацию портфеля по текущему алгоритму проекта.

Требования:
1) Запустить:
   - python run_optimization.py

2) После выполнения прочитать и кратко показать ключевые результаты из каталога финального вывода (по умолчанию `Main portfolio/`, см. `output_dir_final` в `config.yml`): `portfolio_weights.yml`, `run_result.json`, `snapshot.json`, `ips_summary.txt`, `report.txt` (если есть).

3) В ответе обязательно вывести:
   - status из run_result.json
   - финальные веса (топ-10 по убыванию)
   - RC по блокам (target vs actual, если доступны)
   - нарушения/violations (если есть)
   - Stress status + fail reason
   - MaxDD gate (PASS/FAIL)
   - список next_actions (если есть)

4) Если оптимизация не удалась:
   - показать точную причину
   - указать, на каком этапе произошел сбой (data / feasibility / rc / maxdd / stress)
   - предложить следующий шаг.

5) Не менять вручную веса в конфиге; использовать только результаты оптимизатора.

6) **PDF (обязательно):** после успешного прогона выполнить `python rebuild_pdf_reports.py --after-main` (обновляет `run_compare_variants.py` и весь набор PDF в `pdf files/` из актуальных `Main portfolio/`, EW/RP и `pdf_md_sources/`). Если `run_optimization.py` уже отработал до конца с отчётом, PDF обычно пересобраны автоматически — всё равно при сомнении или после ручных правок артефактов повтори эту команду. Пути артефактов по умолчанию: `Main portfolio/` (или `output_dir_final` из `config.yml`), не вымышленная папка «ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ».
