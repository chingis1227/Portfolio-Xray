---
title: "Equal-Weight Portfolio — Commentary"
subtitle: "Commentary"
date: "2026-03-31 14:49 Центральная Европа (лето)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Variant folder:** `equal-weight portfolio`
- **Basis:** post-run commentary (metrics interpreted as reported).
- **Commentary file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Курсор Новый Изменения/equal-weight portfolio/commentary.txt`
- **Generated:** 2026-03-31 14:49 Центральная Европа (лето)

## Executive summary
Прогон относится к Equal-Weight baseline; конец выборки (analysis_end): 2026-02-28. На длинном окне (10Y в отчётном контуре) портфель показывает CAGR около 15.20%, годовую волатильность около 12.98%, максимальную просадку около -20.94%.
Risk-adjusted: Sharpe ≈ 0.991, Sortino ≈ 1.677; чувствительность к базовому бенчмарку: Beta_base ≈ 0.778.
Стресс-тест: DIAG_ATTENTION (DIAG_RC_TOP1_EQUITY_SHOCK); худший сценарий по убытку: equity_shock (RC_Top1); worst_scenario_loss_pct ≈ -22.71%.
Клиентский MaxDD-gate (portfolio_valid): PASS.


## Preamble

Source: summary.txt, stress_report.json, results_csv/portfolio_metrics_10y.csv, results_csv/rc_vol_10y.csv, report.txt


## Metric-by-Metric Interpretation

CAGR (15.20%) отражает среднегодовой темп роста по месячным простым доходностям на 10Y-окне в текущем прогоне. Волатильность (12.98%) — годовая из месячных доходностей; MaxDD (-20.94%) — по месячной equity-кривой. Sharpe (0.991) и Sortino (1.677) используют спецификацию проекта (знаменатель — vol сырой доходности для Sharpe). Beta_base (0.778) и Treynor (0.165) завязаны на базовый бенчмарк; Corr_base при наличии показывает синхронность с бенчмарком на том же окне.


## Risk Structure

Наибольшие доли RC_vol (вклад в дисперсию портфеля) на 10Y: COPX 11.4%, URA 9.3%, SMH 8.4%, ROBO 7.9%, ITA 6.3%. Стресс: status=DIAG_ATTENTION, fail_reason_code=DIAG_RC_TOP1_EQUITY_SHOCK. Провал в сценарии «equity_shock», тест «RC_Top1».


## Strengths

Мандатный MaxDD-gate PASS: реализованная просадка на полной пересекающейся истории в допуске (см. run_metadata / mandate_check).

## Weaknesses

Стресс-диагностика: DIAG_ATTENTION — DIAG_RC_TOP1_EQUITY_SHOCK. (Не блокирует выпуск; именованный сценарий: equity_shock; тест: RC_Top1.)

## Scenario Behavior

Кратко по сценариям из stress_report.json: equity_shock: PnL≈-22.71%, pass=False; credit_shock: PnL≈-8.47%, pass=False; rates_shock: PnL≈-1.42%, pass=False; inflation_stagflation: PnL≈-9.29%, pass=False; liquidity_shock: PnL≈-16.29%, pass=False.
Худший сценарный убыток портфеля (worst_scenario_loss_pct): ≈ -22.71%.


## Final Conclusion

Equal-Weight baseline: профиль доходности/риска на 10Y задаётся CAGR≈15.20% и vol≈12.98% при MaxDD≈-20.94%. Стресс DIAG_ATTENTION (DIAG_RC_TOP1_EQUITY_SHOCK); клиентский gate PASS. Для сравнения вариантов используйте те же файлы в соседних папках (Equal-Weight / Risk Parity / Main portfolio) после синхронного прогона.

