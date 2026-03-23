---
description: Рассчитать Equal-Weight baseline и показать результаты
---

Запусти расчет Equal-Weight baseline строго по правилам проекта.

Требования:
1) Запустить скрипт:
   - python run_equal_weight.py

2) После выполнения прочитать и кратко показать ключевые результаты из файлов:
   - ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/equal-weight portfolio/summary.txt
   - ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/equal-weight portfolio/summary.json
   - ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/equal-weight portfolio/weights.txt

3) В ответе обязательно вывести:
   - статус расчета
   - топ-10 весов (по убыванию)
   - CAGR, Vol, MaxDD, Sharpe, Sortino, Beta, Corr_base (если есть)
   - Stress status + fail reason (если есть)
   - Client-fit (PASS/FAIL)

4) Если расчет не удался:
   - показать причину ошибки
   - показать, какие файлы были созданы
   - предложить следующий шаг для исправления.
