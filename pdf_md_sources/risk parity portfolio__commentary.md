---
title: "Risk-Parity Portfolio — Commentary"
subtitle: "Commentary"
date: "2026-03-24 00:08 Центральная Европа (зима)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Variant folder:** `risk parity portfolio`
- **Basis:** post-run commentary (metrics interpreted as reported).
- **Commentary file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Cursor/risk parity portfolio/commentary.txt`
- **Generated:** 2026-03-24 00:08 Центральная Европа (зима)

## Executive summary
Прогон относится к Risk-Parity baseline; конец выборки (analysis_end): 2026-02-28. На длинном окне (10Y в отчётном контуре) портфель показывает CAGR около 8.38%, годовую волатильность около 6.59%, максимальную просадку около -12.54%.
Risk-adjusted: Sharpe ≈ 0.924, Sortino ≈ 1.531; чувствительность к базовому бенчмарку: Beta_base ≈ 0.387.
Стресс-тест: FAIL_STRESS (FAIL_LOSS_CREDIT_SHOCK); худший сценарий по убытку: credit_shock (Loss); worst_scenario_loss_pct ≈ -37.96%.
Клиентский MaxDD-gate (portfolio_valid): PASS.


## Preamble

Source: summary.txt, stress_report.json, results_csv/portfolio_metrics_10y.csv, results_csv/rc_vol_10y.csv, report.txt


## Metric-by-Metric Interpretation

CAGR (8.38%) отражает среднегодовой темп роста по месячным простым доходностям на 10Y-окне в текущем прогоне. Волатильность (6.59%) — годовая из месячных доходностей; MaxDD (-12.54%) — по месячной equity-кривой. Sharpe (0.924) и Sortino (1.531) используют спецификацию проекта (знаменатель — vol сырой доходности для Sharpe). Beta_base (0.387) и Treynor (0.157) завязаны на базовый бенчмарк; Corr_base при наличии показывает синхронность с бенчмарком на том же окне.


## Risk Structure

Наибольшие доли RC_vol (вклад в дисперсию портфеля) на 10Y: GLD 6.1%, SLV 6.0%, URA 6.0%, VWO 5.9%, COPX 5.8%. Стресс: status=FAIL_STRESS, fail_reason_code=FAIL_LOSS_CREDIT_SHOCK. Провал в сценарии «credit_shock», тест «Loss».


## Strengths

MaxDD-gate PASS: реализованная просадка в допуске относительно target_max_drawdown_pct (см. run_metadata).

## Weaknesses

Стресс не пройден (FAIL_STRESS): FAIL_LOSS_CREDIT_SHOCK. Именованный сценарий сбоя: credit_shock; тип проверки: Loss.

## Scenario Behavior

Кратко по сценариям из stress_report.json: equity_shock: PnL≈-8.71%, pass=True; credit_shock: PnL≈-37.96%, pass=False; rates_shock: PnL≈-4.09%, pass=True; inflation_stagflation: PnL≈-4.68%, pass=True; liquidity_shock: PnL≈-32.28%, pass=True.
Худший сценарный убыток портфеля (worst_scenario_loss_pct): ≈ -37.96%.


## Final Conclusion

Risk-Parity baseline: профиль доходности/риска на 10Y задаётся CAGR≈8.38% и vol≈6.59% при MaxDD≈-12.54%. Стресс FAIL_STRESS (FAIL_LOSS_CREDIT_SHOCK); клиентский gate PASS. Для сравнения вариантов используйте те же файлы в соседних папках (Equal-Weight / Risk Parity / Main portfolio) после синхронного прогона.

