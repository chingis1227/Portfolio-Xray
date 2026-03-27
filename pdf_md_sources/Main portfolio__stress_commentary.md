---
title: "Main Portfolio — Stress Commentary (policy run)"
subtitle: "Commentary"
date: "2026-03-28 00:24 Центральная Европа (зима)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Folder:** `Main portfolio`
- **Basis:** stress commentary (scenarios, RC, historical episodes).
- **Commentary file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Курсор Новый Изменения/Main portfolio/stress_commentary.txt`
- **Generated:** 2026-03-28 00:24 Центральная Европа (зима)

## Executive summary
Прогон: основной портфель (Main portfolio); конец выборки (analysis_end): 2026-02-28. Итоговый статус стресс-набора в stress_report: DIAG_ATTENTION. Основной код (primary / fail_reason): DIAG_RC_TOP1_EQUITY_SHOCK. Список diagnostic_codes: DIAG_RC_TOP1_EQUITY_SHOCK, DIAG_RC_TOP1_CREDIT_SHOCK, DIAG_RC_TOP1_RATES_SHOCK, DIAG_RC_TOP1_INFLATION_STAGFLATION, DIAG_RC_TOP1_LIQUIDITY_SHOCK.
По рабочему процессу проекта синтетические сценарии и исторические эпизоды в этом файле — диагностика для PM и не блокируют выпуск весов; блокирующий контур по максимальной просадке задаётся отдельно (mandate_check / IPS, полная пересекающаяся история).
Предупреждение в отчёте: WARN_ROLE_EQUITY_DEFENSIVE_WEAK.
Худший сценарный PnL портфеля (worst_scenario_loss_pct): -31.12%; именованный сценарий: equity_shock; поле failed_test: RC_Top1.


## Preamble

Source: stress_report.json (текущий прогон)


## Metric-by-Metric Interpretation

Синтетические сценарии (stress_report.scenario_results): для каждого сценария ниже — PnL портфеля, итог pass, флаги loss_ok / role_ok / rc1_ok / rc3_ok и топ-1 вклад в риск (Top1 RC), как в JSON. pass=false при нарушении любого из тестов сценария.
- equity_shock: PnL≈-31.12%, pass=False, loss_ok=True, role_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: URA (18.46%).
- credit_shock: PnL≈-9.49%, pass=False, loss_ok=True, role_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: URA (18.46%).
- rates_shock: PnL≈-0.05%, pass=False, loss_ok=True, role_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (16.02%).
- inflation_stagflation: PnL≈-12.60%, pass=False, loss_ok=True, role_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (16.02%).
- liquidity_shock: PnL≈-20.73%, pass=False, loss_ok=True, role_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: URA (18.56%).
Коды по сценариям (уникально): DIAG_RC_TOP1_EQUITY_SHOCK, DIAG_RC_TOP1_CREDIT_SHOCK, DIAG_RC_TOP1_RATES_SHOCK, DIAG_RC_TOP1_INFLATION_STAGFLATION, DIAG_RC_TOP1_LIQUIDITY_SHOCK.
Факторные беты портфеля (недельная оценка, см. спецификацию): 5Y≈{beta_cmd=0.1184, beta_credit=-0.4271, beta_eq=0.7756, beta_inf=0.6499, beta_rr=-0.0231, beta_usd=-0.7611}; 10Y≈{beta_cmd=0.0892, beta_credit=0.2900, beta_eq=0.8083, beta_inf=1.3395, beta_rr=-0.3423, beta_usd=-0.5711}.


## Risk Structure

rc_asset_cap_used=0.1000 (доля Top1 RC, контекст отчёта); stress_top3_rc_sum_cap=0.7000; max_dd_limit (эпизоды/контекст в отчёте)=35.00%
По сценариям Top1 RC по сценариям (см. таблицу выше): equity_shock URA=18.5%, credit_shock URA=18.5%, rates_shock COPX=16.0%, inflation_stagflation COPX=16.0%, liquidity_shock URA=18.6%.
Исторические эпизоды (historical_results):
- 2008: max_dd≈н/д, pass=None, vol_annualized_episode≈н/д, diagnostic_code=—.
- 2020: max_dd≈-11.59%, pass=True, vol_annualized_episode≈0.4443, diagnostic_code=—.
- 2022: max_dd≈-22.45%, pass=True, vol_annualized_episode≈0.2020, diagnostic_code=—.


## Strengths

Во всех синтетических сценариях loss_ok=true — глубина потерь в рамках порогов loss-теста.
Во всех сценариях rc3_ok=true — суммарный Top3 RC не нарушает stress_top3_rc_sum_cap.
Исторический эпизод 2020 помечен pass=true.
Исторический эпизод 2022 помечен pass=true.

## Weaknesses

DIAG_ATTENTION: зафиксированы диагностические коды (DIAG_RC_TOP1_EQUITY_SHOCK, DIAG_RC_TOP1_CREDIT_SHOCK, DIAG_RC_TOP1_RATES_SHOCK, DIAG_RC_TOP1_INFLATION_STAGFLATION, DIAG_RC_TOP1_LIQUIDITY_SHOCK); для PM имеет смысл разобрать scenario_results и historical_results.
Во всех сценариях rc1_ok=false — концентрация Top1 RC выше порога rc_asset_cap_used.
warning_code=WARN_ROLE_EQUITY_DEFENSIVE_WEAK (роль защитных блоков / прочее — см. stress_report).
Эпизод 2008: max_dd н/д — интерпретация ограничена.

## Scenario Behavior

equity_shock: PnL≈-31.12%, итог pass=False — см. loss/role/rc в Metric-by-Metric.
credit_shock: PnL≈-9.49%, итог pass=False — см. loss/role/rc в Metric-by-Metric.
rates_shock: PnL≈-0.05%, итог pass=False — см. loss/role/rc в Metric-by-Metric.
inflation_stagflation: PnL≈-12.60%, итог pass=False — см. loss/role/rc в Metric-by-Metric.
liquidity_shock: PnL≈-20.73%, итог pass=False — см. loss/role/rc в Metric-by-Metric.


## Final Conclusion

основной портфель (Main portfolio): стресс-набор DIAG_ATTENTION (DIAG_RC_TOP1_EQUITY_SHOCK). Синтетические потери и RC-диагностика отражают текущий состав и Σ из прогона; решения по выпуску весов сверяйте с mandate_check и run_result, а этот файл используйте как сценарную справку для PM.

