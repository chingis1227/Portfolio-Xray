---
title: "Main Portfolio — Commentary (policy run)"
subtitle: "Commentary"
date: "2026-03-24 00:08 Центральная Европа (зима)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Output folder:** `Main portfolio`
- **Basis:** policy portfolio commentary.
- **Commentary file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Cursor/Main portfolio/commentary.txt`
- **Generated:** 2026-03-24 00:08 Центральная Европа (зима)

## Executive summary
Прогон относится к основной портфель (Main portfolio); конец выборки (analysis_end): 2026-02-28. На длинном окне (10Y в отчётном контуре) портфель показывает CAGR около 18.30%, годовую волатильность около 14.90%, максимальную просадку около -21.10%.
Risk-adjusted: Sharpe ≈ 1.060, Sortino ≈ 1.799; чувствительность к базовому бенчмарку: Beta_base ≈ 0.892.
Стресс-тест: FAIL_STRESS (FAIL_ROLE_EQUITY_SHOCK); худший сценарий по убытку: equity_shock (Role); worst_scenario_loss_pct ≈ -101.64%.
Клиентский MaxDD-gate (portfolio_valid): PASS.


## Preamble

Source: summary.txt, stress_report.json, results_csv/portfolio_metrics_10y.csv, results_csv/rc_vol_10y.csv, report.txt


## Metric-by-Metric Interpretation

CAGR (18.30%) отражает среднегодовой темп роста по месячным простым доходностям на 10Y-окне в текущем прогоне. Волатильность (14.90%) — годовая из месячных доходностей; MaxDD (-21.10%) — по месячной equity-кривой. Sharpe (1.060) и Sortino (1.799) используют спецификацию проекта (знаменатель — vol сырой доходности для Sharpe). Beta_base (0.892) и Treynor (0.177) завязаны на базовый бенчмарк; Corr_base при наличии показывает синхронность с бенчмарком на том же окне.


## Risk Structure

Наибольшие доли RC_vol (вклад в дисперсию портфеля) на 10Y: VOO 23.6%, ITA 14.6%, SLV 14.0%, SMH 12.7%, COPX 11.9%. Стресс: status=FAIL_STRESS, fail_reason_code=FAIL_ROLE_EQUITY_SHOCK. Провал в сценарии «equity_shock», тест «Role».


## Strengths

MaxDD-gate PASS: реализованная просадка в допуске относительно target_max_drawdown_pct (см. run_metadata).
Sharpe ≥ 1.0 (1.060) на выбранном окне — относительно сильная компенсация за риск по истории.

## Weaknesses

Стресс не пройден (FAIL_STRESS): FAIL_ROLE_EQUITY_SHOCK. Именованный сценарий сбоя: equity_shock; тип проверки: Role.

## Scenario Behavior

Кратко по сценариям из stress_report.json: equity_shock: PnL≈-24.45%, pass=False; credit_shock: PnL≈-101.64%, pass=False; rates_shock: PnL≈-2.04%, pass=False; inflation_stagflation: PnL≈-10.49%, pass=False; liquidity_shock: PnL≈-86.93%, pass=False.
Худший сценарный убыток портфеля (worst_scenario_loss_pct): ≈ -101.64%.


## Final Conclusion

основной портфель (Main portfolio): профиль доходности/риска на 10Y задаётся CAGR≈18.30% и vol≈14.90% при MaxDD≈-21.10%. Стресс FAIL_STRESS (FAIL_ROLE_EQUITY_SHOCK); клиентский gate PASS. Для сравнения вариантов используйте те же файлы в соседних папках (Equal-Weight / Risk Parity / Main portfolio) после синхронного прогона.

