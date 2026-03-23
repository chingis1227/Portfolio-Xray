---
title: "Risk-Parity Portfolio — Commentary"
subtitle: "Commentary"
date: "2026-03-23 23:38 Центральная Европа (зима)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Variant folder:** `risk parity portfolio`
- **Basis:** post-run commentary (metrics interpreted as reported).
- **Commentary file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Cursor/risk parity portfolio/commentary.txt`
- **Generated:** 2026-03-23 23:38 Центральная Европа (зима)

## Executive summary
Risk-Parity baseline на 10Y (по summary.txt и portfolio_metrics_10y.csv) даёт около 11.2% CAGR при годовой волатильности около 9.8% и max drawdown около −18.7% — то есть более низкий апсайд относительно EW, но и более сжатый масштаб колебаний. Sharpe ≈0.91 и Sortino ≈1.47 описывают умеренную компенсацию за риск; бета ≈0.60 указывает на заметно более низкую рыночную чувствительность, чем у равных весов. Стресс-статус: FAIL_STRESS с причиной FAIL_ROLE_EQUITY_SHOCK и failed_scenario = equity_shock — провал идёт по role-based критерию в сценарии equity_shock (failed_test: Role в stress_report.json), при этом лимиты по RC_top1 в этом сценарии отмечены как выполненные. Клиентский MaxDD-gate в summary отмечен как PASS.


## Preamble

Source: summary.txt, stress_report.json, results_csv/portfolio_metrics_10y.csv, results_csv/rc_vol_10y.csv


## Metric-by-Metric Interpretation

Сочетание CAGR ~11% и vol ~10% задаёт профиль ближе к «risk-balanced», чем к агрессивному growth basket: доходность уступает EW-аналогу из сравнительных отчётов, но волатильность и бета ниже, что согласуется с целью RP выровнять вклады в дисперсию. Max drawdown ~−18.7% чуть мельче, чем типичный EW на том же универсуме в последних сравнениях — это согласуется с более равномерным распределением риска по активам.

Sharpe ниже 1.0 говорит о том, что избыточная доходность относительно полной волатильности не выглядит «элитной», зато Sortino остаётся конкурентоспособным — хвостовой риск относительно сглажен. По stress_report.json в equity_shock PnL портфеля около −16.7%; топ-1 по RC в этом сценарии — ROBO (~9.1% вклада в дисперсию), топ-3 включают ROBO, VOO, QQQ с суммой top3_rc_sum_pct ~25.6%. Это конкретная структура риска, на которую опирается интерпретация role-теста.


## Risk Structure

Файл rc_vol_10y.csv в этой папке показывает наибольшие доли RC_vol у ROBO (~9.7%), VOO (~9.5%), SLV (~8.7%), QQQ (~8.0%), VT (~7.7%) — риск не равномерен по именам, несмотря на RP-цель, из-за различий в волатильностях и корреляциях. В stress сценариях credit_shock, rates_shock, inflation_stagflation и liquidity_shock в текущем stress_report.json отмечены как pass=true, а провал сосредоточен в equity_shock через role_ok=false — т.е. профиль уязвим к нарушению ролевых ограничений при шоке акций, а не ко всем типам сценариев одинаково.


## Strengths

Ниже волатильность и бета, чем у EW на сопоставимом универсуме в типичных сравнениях; более мягкий исторический max DD в summary. Большинство именованных стресс-сценариев в stress_report для этого прогона проходят по pass, кроме связки equity_shock + Role. Явные топ-RC активы и сценарные PnL позволяют говорить о структуре риска предметно, без ссылок на «нехватку данных».

## Weaknesses

FAIL_STRESS по equity_shock (Role) оставляет конструкцию вне стресс-комфорта при заданных role-критериях. CAGR и Sharpe ниже, чем у EW в сравнительных файлах — trade-off в пользу сглаживания риска ценой доходности. Если rc_vol_10y.csv содержит строки по тикерам, отсутствующим в текущем config, это сигнал пересобрать RP после синхронизации универсума (файл отражает последний прогон на диске).

## Scenario Behavior

В спокойных и умеренно позитивных режимах RP исторически реализует умеренный рост с более низкой амплитудой колебаний (vol и beta из summary). В equity_shock сценарии убыток и структура вкладов по блокам (Growth ~−16.2%, прочие блоки малы) показывают доминирование equity-риска; именно здесь role-тест не пройден. В credit_shock и liquidity_shock отчёт фиксирует положительный PnL портфеля в этом прогоне — асимметрия между сценариями заметна и полезна для внутреннего разбора.


## Final Conclusion

RP-baseline в данном прогоне выглядит как более «риск-сглаженный» вариант относительно EW: меньше волатильность и бета, глубже защита по max DD в summary, но ниже доходность и risk-adjusted метрики Sharpe. Цена этого профиля — провал стресс-гейта в equity_shock по ролевому критерию при том, что ряд других сценариев проходит. Управленчески важно различать «низкий риск по волатильности» и «приемлемость под полным стресс-набором» — здесь второе не выполнено для equity_shock/Role.

