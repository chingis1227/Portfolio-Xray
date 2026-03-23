---
description: Рассчитать Risk-Parity baseline и показать результаты
---

Запусти расчет Risk-Parity baseline строго по правилам проекта.

Требования:
1) Запустить скрипт:
   - python run_risk_parity.py

2) После выполнения прочитать и кратко показать ключевые результаты из файлов:
   - ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/risk parity portfolio/summary.txt
   - ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/risk parity portfolio/summary.json
   - ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/risk parity portfolio/weights.txt

3) В ответе обязательно вывести:
   - статус расчета
   - топ-10 весов (по убыванию)
   - RC_vol по активам брать из weights.txt (solver source)
   - отдельно указать RC source: solver (target parity)
   - CAGR, Vol, MaxDD, Sharpe, Sortino, Beta, Corr_base (если есть)
   - Stress status + fail reason (если есть)
   - Client-fit (PASS/FAIL)
   - solver_status и max_rc_error (если есть в summary)

4) Если расчет не удался:
   - показать причину ошибки
   - показать, какие файлы были созданы
   - предложить следующий шаг для исправления.
