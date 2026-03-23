---
title: "Main Portfolio — Commentary (policy run)"
subtitle: "Commentary"
date: "2026-03-23 23:38 Центральная Европа (зима)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Output folder:** `Main portfolio`
- **Basis:** policy portfolio commentary.
- **Commentary file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Cursor/Main portfolio/commentary.txt`
- **Generated:** 2026-03-23 23:38 Центральная Европа (зима)

## Executive summary
Последний прогон оптимизации зафиксирован в run_result.json как FAIL_MAX_DD: итоговые веса в файл не записаны (ips_summary.txt повторяет «weights not written»), при этом отчёт report.txt по снимкам всё ещё описывает рассчитанную конструкцию с конкретными весами и метриками — это два слоя одного пайплайна: **production gate** vs **диагностический снимок**. На горизонте 10Y в report.txt портфель показывает CAGR ~18.3%, vol ~14.9%, max drawdown ~−21.1%, Sharpe ~1.06 и Sortino ~1.80 при beta ~0.89 — сильный исторический upside с ощутимой глубиной просадки. Одновременно stress_report.json фиксирует FAIL_STRESS (FAIL_ROLE_EQUITY_SHOCK), worst_scenario_loss_pct ≈ −101.64% и failed_scenario equity_shock — в связке с MAX_DD_GATE в run_result это и блокирует выпуск весов. IPS сводка указывает отклонение фактического RC по блокам от целей (Growth ниже, Inflation выше, Duration почти нулевой) и RB_BREACH по дельтам в п.п.


## Preamble

Source: report.txt (снимки 3Y/5Y/10Y), run_result.json, stress_report.json, ips_summary.txt


## Metric-by-Metric Interpretation

Мультиоконный report.txt показывает ускорение CAGR на коротком 3Y (~31.9%) при более низкой vol (~12.1%) и очень высоких Sharpe/Sortino — это отражает недавнюю выборку и не отменяет более тяжёлый 10Y max DD (~−21%). Для 5Y и 10Y метрики ближе к «умеренно-агрессивному» профилю с vol 14–15% и Sharpe около 1.06–1.06. VaR/ES в отчёте по окнам показывают, что хвостовые потери на 10Y глубже, чем на 3Y (например ES 95 ~−8.7% на 10Y против ~−4.3% на 3Y) — интерпретация: длинная история включает эпизоды, где хвост тяжелее.

RC_vol по блокам на 10Y в report.txt: Growth ~84.6%, Inflation ~15.0%, Duration ~0.3% — фактический риск смещён в growth и инфляционные прокси при почти нулевом duration-вкладе; это напрямую бьётся с целевыми долями в ips_summary (Duration 5%, Inflation 5%) и объясняет RB_BREACH. Топ RC по активам на 10Y: VOO ~23.6%, ITA ~14.6%, SLV ~14.0%, SMH ~12.7%, COPX ~11.9% — концентрация риска в ограниченном наборе имён при формально длинном списке позиций.


## Risk Structure

Структура весов в снимке (VOO ~26.3%, ITA ~13.5%, SLV ~12.3%, SMH ~9.3% и далее хвост) задаёт лидерство крупных капитализаций и тематических/commodity кусков; RC это подтверждает численно. Stress equity_shock в stress_report.json: portfolio_pnl_pct ~−24.5%, роль Growth доминирует в PnL по блокам; failed_test Role и top1_rc_asset VOO (~21.5% RC) связывают провал с ролевыми ограничениями при высокой концентрации риска на крупном ядре. credit_shock в том же файле даёт глубокий отрицательный PnL (≈−101.6%) и определяет worst_scenario_loss_pct — это отдельная ось уязвимости к кредитному сценарию в спецификации движка.

Отчёт также предупреждает о короткой inner-join выборке для Σ/RC (11 месяцев) — оценки риска в снимке могут быть шумными; это не отменяет фактов gate-статусов, но снижает уверенность в тонкой калибровке RC.


## Strengths

Сильная историческая доходность и risk-adjusted метрики на 10Y/5Y в report.txt; target_vol и max_dd в constraints_status помечены PASS на снимке. Явная декомпозиция весов, RC и сценариев stress позволяет проводить разбор без «дыр» в данных. Robustness-блок фиксирует сопоставление 10Y vs 5Y весов и RC по блокам — полезно для стабильности решения.

## Weaknesses

Production-статус FAIL_MAX_DD и пустые weights в run_result — веса нельзя считать утверждёнными для исполнения. FAIL_STRESS (equity_shock / Role) и тяжёлый credit_shock в stress_report. RB corridor FAIL и систематическое расхождение RC блоков с целями (см. ips_summary). Короткая эффективная выборка для риск-оценок в шапке report — повышает неопределённость точных уровней RC.

## Scenario Behavior

В risk-on фазах, отражённых в 3Y метриках, конструкция показывает высокую кривую доходности и Sortino. На 10Y горизонте сценарии stress показывают material equity drawdown в equity_shock и экстремальное ухудшение в credit_shock по расчёту движка — поведение не сводится к одному сценарию, но gate ломается по сочетанию MaxDD/stress. inflation_stagflation и rates_shock в stress_report дают более умеренные движения относительно credit_shock в этом прогоне.


## Final Conclusion

Снимок описывает агрессивный return-oriented портфель с сильной исторической доходностью и явной концентрацией риска в growth-ядре (VOO и сателлиты) плюс material inflation RC; duration почти не амортизирует риск в RC-терминах. Production-слой признаёт ту же конструкцию неприемлемой по совокупности стресс/MaxDD gate и не выпускает веса — ключевой trade-off для мандата: upside из отчёта достигается ценой структурного перекоса RC, провала ряда стресс-критериев и несоответствия RB-коридору, что зафиксировано в run_result.json и ips_summary.txt.

