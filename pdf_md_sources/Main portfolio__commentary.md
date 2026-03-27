---
title: "Main Portfolio — Commentary (policy run)"
subtitle: "Commentary"
date: "2026-03-28 00:24 Центральная Европа (зима)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Output folder:** `Main portfolio`
- **Basis:** policy portfolio commentary.
- **Commentary file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Курсор Новый Изменения/Main portfolio/commentary.txt`
- **Generated:** 2026-03-28 00:24 Центральная Европа (зима)

## Executive summary
Прогон относится к основной портфель (Main portfolio); конец выборки (analysis_end): 2026-02-28. На длинном окне (10Y в отчётном контуре) портфель показывает CAGR около 18.98%, годовую волатильность около 15.30%, максимальную просадку около -22.39%.
Risk-adjusted: Sharpe ≈ 1.076, Sortino ≈ 1.866; чувствительность к базовому бенчмарку: Beta_base ≈ 0.929.
Стресс-тест: DIAG_ATTENTION (DIAG_RC_TOP1_EQUITY_SHOCK); худший сценарий по убытку: equity_shock (RC_Top1); worst_scenario_loss_pct ≈ -31.12%.
Клиентский MaxDD-gate (portfolio_valid): PASS.


## Preamble

Source: summary.txt, stress_report.json, results_csv/portfolio_metrics_10y.csv, results_csv/rc_vol_10y.csv, report.txt


## Metric-by-Metric Interpretation

CAGR (18.98%) отражает среднегодовой темп роста по месячным простым доходностям на 10Y-окне в текущем прогоне. Волатильность (15.30%) — годовая из месячных доходностей; MaxDD (-22.39%) — по месячной equity-кривой. Sharpe (1.076) и Sortino (1.866) используют спецификацию проекта (знаменатель — vol сырой доходности для Sharpe). Beta_base (0.929) и Treynor (0.177) завязаны на базовый бенчмарк; Corr_base при наличии показывает синхронность с бенчмарком на том же окне.


## Risk Structure

Наибольшие доли RC_vol (вклад в дисперсию портфеля) на 10Y: URA 15.7%, SMH 15.1%, VOO 15.1%, COPX 15.0%, QQQ 14.8%. Стресс: status=DIAG_ATTENTION, fail_reason_code=DIAG_RC_TOP1_EQUITY_SHOCK. Провал в сценарии «equity_shock», тест «RC_Top1».


## Strengths

Мандатный MaxDD-gate PASS: реализованная просадка на полной пересекающейся истории в допуске (см. run_metadata / mandate_check).
Sharpe ≥ 1.0 (1.076) на выбранном окне — относительно сильная компенсация за риск по истории.

## Weaknesses

Стресс-диагностика: DIAG_ATTENTION — DIAG_RC_TOP1_EQUITY_SHOCK. (Не блокирует выпуск; именованный сценарий: equity_shock; тест: RC_Top1.)

## Scenario Behavior

Кратко по сценариям из stress_report.json: equity_shock: PnL≈-31.12%, pass=False; credit_shock: PnL≈-9.49%, pass=False; rates_shock: PnL≈-0.05%, pass=False; inflation_stagflation: PnL≈-12.60%, pass=False; liquidity_shock: PnL≈-20.73%, pass=False.
Худший сценарный убыток портфеля (worst_scenario_loss_pct): ≈ -31.12%.


## Final Conclusion

основной портфель (Main portfolio): профиль доходности/риска на 10Y задаётся CAGR≈18.98% и vol≈15.30% при MaxDD≈-22.39%. Стресс DIAG_ATTENTION (DIAG_RC_TOP1_EQUITY_SHOCK); клиентский gate PASS. Для сравнения вариантов используйте те же файлы в соседних папках (Equal-Weight / Risk Parity / Main portfolio) после синхронного прогона.

