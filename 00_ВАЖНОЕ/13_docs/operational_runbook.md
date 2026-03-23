# Operational Runbook

Short guide for **when to run optimization**, **how to handle universe and config changes**, and **how to read run results**. See **production_workflow.md** for status and gate semantics.

---

## 1. When to re-run optimization

Re-run `python run_optimization.py` (from project root) in these cases:

| Trigger | Action |
|--------|--------|
| **Calendar** | e.g. monthly or quarterly on a fixed date (e.g. first business day of the month). |
| **Deviation** | Current or last-rebalance weights have drifted from target (e.g. max \|w_current − w_target\| > 2% or sum of \|Δw\| > 5%). Consider rebalancing and/or re-running optimization. |
| **Universe change** | Any add/remove of tickers in config and/or blocks_universe → full re-run (see §2). |
| **Profile / mandate change** | Change of client_profile or rc_block_targets, target_vol_annual, target_max_drawdown_pct → full re-run. |
| **Stress failure** | Last run had status with FAIL_STRESS in violations → review and optionally re-run after adjusting liquidity, duration, or growth share. |

---

## 2. Universe changes (add/remove tickers)

- **Adding a ticker:** Add it to `config.yml` (tickers) and to `blocks_universe.yml` in the correct block. Then run a **full** optimization. Do not try to “patch” existing weights; the new weights file will include the new ticker.
- **Removing a ticker:** Remove from config and blocks_universe, then run a **full** optimization. The new `portfolio_weights.yml` will no longer contain the removed ticker (weight 0 or omitted).

There is no partial update: every change to the investable universe requires a full re-run of `run_optimization.py`.

---

## 3. How to read run_result.json

After each run, check `output_dir_final/run_result.json` (e.g. `ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ/run_result.json`):

| Field | Meaning |
|-------|--------|
| **status** | APPROVED, CANDIDATE_RB_BREACH, OK_FALLBACK, or FAIL_* (see production_workflow.md). |
| **weights** | Target weights (empty if status is FAIL_* and weights were not written). |
| **violations** | List of { "code", "details" } (e.g. RB_BREACH, VIOL_RC_ASSET_CAP, FAIL_STRESS). |
| **next_actions** | Suggested next steps when violations or failures occur. |
| **resolved_config** | Merged config (profile + overrides) used for the run; for audit and reproducibility. |

If **status** is FAIL_DATA, FAIL_FEASIBILITY, FAIL_RC, FAIL_MAX_DD, or FAIL_STRESS (when strict_stress_gate is used) → weights were not written; follow **next_actions** and fix config/data or mandate before using the system for allocation.

If **status** is APPROVED or CANDIDATE_RB_BREACH or OK_FALLBACK → weights were written to `portfolio_weights.yml`; use them as target weights, taking into account violations (e.g. RB breach or RC breach) as per your mandate.

---

## 4. Output files

| File | Location | Purpose |
|------|----------|--------|
| **portfolio_weights.yml** | output_dir_final (e.g. ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ) | Target weights for execution; only present if weights were written. |
| **run_result.json** | output_dir_final | Status, violations, next_actions, resolved_config; always written after a run. |
| **snapshot.json** | output_dir_final | Snapshot of weights, RC, constraints, stress summary; written when weights are written. |
| **ips_summary.txt** | output_dir_final | One-page mandate summary and actions by status; written after every run. |

Report CSV and other report outputs are produced by `run_report.py` (invoked after optimization when report is enabled). If report fails, weights and run_result are still saved.

---

## 5. First run (первый деплой)

1. **Проверить config.yml:** заданы `tickers`, `client_profile`, `investor_currency`. При необходимости задать `liquidity_need_months`, `monthly_expenses`, `portfolio_value` для расчёта ликвидного пола.
2. **Запуск:** из корня проекта выполнить `python run_optimization.py` (при первой загрузке данных можно использовать `--no-cache`).
3. **Проверка результата:** открыть `output_dir_final/run_result.json` и проверить поле **status**. При APPROVED, OK_FALLBACK или CANDIDATE_RB_BREACH веса записаны в `portfolio_weights.yml` и могут использоваться как целевые.
4. **При нарушениях:** при RB_BREACH или FAIL_STRESS следовать **next_actions** в run_result.json. При включённом `strict_stress_gate: true` и FAIL_STRESS веса не записываются — скорректировать архитектуру (защитные блоки, ликвидность, долю Growth) и перезапустить.

---

## 6. Recurring run (регулярный прогон)

1. **Обновление данных:** при необходимости запускать с флагом `--no-cache` для перезагрузки цен и курсов.
2. **Календарный запуск:** выполнять `run_optimization.py` по выбранному графику (например, первый рабочий день месяца).
3. **Сравнение с предыдущим прогоном:** проверить статус и нарушения в новом run_result.json; при изменении статуса или появлении новых нарушений — просмотреть **next_actions** и при необходимости скорректировать конфиг или мандат.
4. **Ребаланс:** для получения списка сделок использовать `run_rebalance.py --current current_positions.yml --target <path_to_portfolio_weights.yml>`. При необходимости задать порог ребаланса (`--threshold`) и минимальный размер сделки (`--min-trade`). Учитывать объём торговли (turnover) при принятии решения о проведении ребаланса.
