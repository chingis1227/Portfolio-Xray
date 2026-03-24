---
description: Прогнать выбранный вариант и вывести только stress-результат
---

Запусти stress-only прогон для выбранного варианта портфеля.

Требования:
1) Определи вариант:
   - если пользователь явно указал `equal-weight` / `risk-parity` / `main`, используй его;
   - если не указал, задай уточняющий вопрос (один из трёх вариантов).

2) Запусти:
   - python run_stress_variant.py --variant <equal-weight|risk-parity|main>
   - при явной просьбе пользователя добавить без кеша:
     - python run_stress_variant.py --variant <...> --no-cache

3) После выполнения покажи только stress-блок:
   - status
   - reason (fail_reason_code / warning_code)
   - worst_scenario_loss_pct
   - failed_scenario
   - failed_test
   - factor_betas_5y
   - factor_betas_10y
   - сценарии: scenario_id, pnl, pass, top1_rc, top3_rc_sum

4) Если прогон завершился ошибкой:
   - покажи код ошибки
   - кратко покажи хвост stdout/stderr
   - предложи следующий шаг.
