---
title: "Risk-Parity Portfolio — Commentary"
subtitle: "Commentary"
date: "2026-03-31 14:50 Центральная Европа (лето)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Variant folder:** `risk parity portfolio`
- **Basis:** post-run commentary (metrics interpreted as reported).
- **Commentary file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Курсор Новый Изменения/risk parity portfolio/commentary.txt`
- **Generated:** 2026-03-31 14:50 Центральная Европа (лето)

## Executive summary
Прогон относится к Risk-Parity baseline; конец выборки (analysis_end): 2026-02-28. На длинном окне (10Y в отчётном контуре) портфель показывает CAGR около 8.38%, годовую волатильность около 6.59%, максимальную просадку около -12.54%.
Risk-adjusted: Sharpe ≈ 0.924, Sortino ≈ 1.531; чувствительность к базовому бенчмарку: Beta_base ≈ 0.387.
Стресс-тест: PASS_WITH_WARNING; worst_scenario_loss_pct ≈ -10.76%.
Клиентский MaxDD-gate (portfolio_valid): PASS.


## Preamble

Source: summary.txt, stress_report.json, results_csv/portfolio_metrics_10y.csv, results_csv/rc_vol_10y.csv, report.txt


## Metric-by-Metric Interpretation

CAGR (8.38%) отражает среднегодовой темп роста по месячным простым доходностям на 10Y-окне в текущем прогоне. Волатильность (6.59%) — годовая из месячных доходностей; MaxDD (-12.54%) — по месячной equity-кривой. Sharpe (0.924) и Sortino (1.531) используют спецификацию проекта (знаменатель — vol сырой доходности для Sharpe). Beta_base (0.387) и Treynor (0.157) завязаны на базовый бенчмарк; Corr_base при наличии показывает синхронность с бенчмарком на том же окне.


## Risk Structure

Наибольшие доли RC_vol (вклад в дисперсию портфеля) на 10Y: GLD 6.1%, SLV 6.0%, URA 6.0%, VWO 5.9%, COPX 5.8%. Стресс: status=PASS_WITH_WARNING, fail_reason_code=—.


## Strengths

MaxDD-gate PASS: реализованная просадка в допуске относительно target_max_drawdown_pct (см. run_metadata).

## Weaknesses

Стресс не пройден (PASS_WITH_WARNING): —. Именованный сценарий сбоя: —; тип проверки: —.

## Scenario Behavior

Кратко по сценариям из stress_report.json: equity_shock: PnL≈-10.76%, pass=True; credit_shock: PnL≈-3.74%, pass=True; rates_shock: PnL≈-2.85%, pass=True; inflation_stagflation: PnL≈-4.95%, pass=True; liquidity_shock: PnL≈-7.51%, pass=True.
Худший сценарный убыток портфеля (worst_scenario_loss_pct): ≈ -10.76%.


## Final Conclusion

Risk-Parity baseline: профиль доходности/риска на 10Y задаётся CAGR≈8.38% и vol≈6.59% при MaxDD≈-12.54%. Стресс PASS_WITH_WARNING (—); клиентский gate PASS. Для сравнения вариантов используйте те же файлы в соседних папках (Equal-Weight / Risk Parity / Main portfolio) после синхронного прогона.

