---
title: "Main Portfolio — Commentary (policy run)"
subtitle: "Commentary"
date: "2026-03-31 14:50 Центральная Европа (лето)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Output folder:** `Main portfolio`
- **Basis:** policy portfolio commentary.
- **Commentary file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Курсор Новый Изменения/Main portfolio/commentary.txt`
- **Generated:** 2026-03-31 14:50 Центральная Европа (лето)

## Executive summary
Прогон относится к основной портфель (Main portfolio); конец выборки (analysis_end): 2026-02-28. На длинном окне (10Y в отчётном контуре) портфель показывает CAGR около 7.78%, годовую волатильность около 7.02%, максимальную просадку около -15.69%.
Risk-adjusted: Sharpe ≈ 0.793, Sortino ≈ 1.266; чувствительность к базовому бенчмарку: Beta_base ≈ 0.396.
Стресс-тест: DIAG_PASS_WITH_WARNING; worst_scenario_loss_pct ≈ -10.22%.
Клиентский MaxDD-gate (portfolio_valid): PASS.


## Preamble

Source: summary.txt, stress_report.json, results_csv/portfolio_metrics_10y.csv, results_csv/rc_vol_10y.csv, report.txt


## Metric-by-Metric Interpretation

CAGR (7.78%) отражает среднегодовой темп роста по месячным простым доходностям на 10Y-окне в текущем прогоне. Волатильность (7.02%) — годовая из месячных доходностей; MaxDD (-15.69%) — по месячной equity-кривой. Sharpe (0.793) и Sortino (1.266) используют спецификацию проекта (знаменатель — vol сырой доходности для Sharpe). Beta_base (0.396) и Treynor (0.140) завязаны на базовый бенчмарк; Corr_base при наличии показывает синхронность с бенчмарком на том же окне.


## Risk Structure

Наибольшие доли RC_vol (вклад в дисперсию портфеля) на 10Y: BND 19.7%, VOO 7.6%, SCHP 7.1%, GLD 6.1%, SLV 5.3%. Стресс: status=DIAG_PASS_WITH_WARNING, fail_reason_code=—.


## Strengths

Диагностический стресс без критичных отметок (или только предупреждения); мандатный MaxDD-gate PASS — сочетание исторической просадки и клиентского порога не конфликтует в этом прогоне.

## Scenario Behavior

Кратко по сценариям из stress_report.json: equity_shock: PnL≈-10.22%, pass=True; credit_shock: PnL≈-3.62%, pass=True; rates_shock: PnL≈-6.17%, pass=True; inflation_stagflation: PnL≈-5.60%, pass=True; liquidity_shock: PnL≈-7.18%, pass=True.
Худший сценарный убыток портфеля (worst_scenario_loss_pct): ≈ -10.22%.


## Final Conclusion

основной портфель (Main portfolio): профиль доходности/риска на 10Y задаётся CAGR≈7.78% и vol≈7.02% при MaxDD≈-15.69%. Стресс DIAG_PASS_WITH_WARNING (—); клиентский gate PASS. Для сравнения вариантов используйте те же файлы в соседних папках (Equal-Weight / Risk Parity / Main portfolio) после синхронного прогона.

