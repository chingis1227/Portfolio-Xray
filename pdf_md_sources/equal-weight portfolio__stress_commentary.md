---
title: "Стресс: как ведёт себя equal-weight"
date: "Итоги анализа на 10-летнем окне, по состоянию на 2026-02-28"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Ключевой вывод

По рабочему процессу проекта синтетические сценарии и исторические эпизоды в этом файле — диагностика для PM и не блокируют выпуск весов; блокирующий контур по максимальной просадке задаётся отдельно (mandate_check / IPS, полная пересекающаяся история).
Предупреждение в отчёте: WARN_ .
Худший сценарный PnL портфеля (worst_scenario_loss_pct): -22.71%; именованный сценарий: сильный обвал на рынке акций; поле failed_test: RC_Top1.


## Ключевые показатели

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{15,20\%}{Доходность (CAGR)} & \KPIone{13,00\%}{Волатильность} & \KPIone{-20,90\%}{Макс. просадка}\\[0.55em] \KPIone{0,991}{Коэф. Шарпа} & \KPIone{1,677}{Коэф. Сортино} & \KPIone{0,778}{Чувствительность к рынку}\end{tabular}\end{center}
```


## Что это значит для инвестора

- сильный обвал на рынке акций: PnL≈-22.71%, в норме по проверке=False, loss_ok=True, =True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (12.97%).
- стресс на рынке кредита: PnL≈-8.47%, в норме по проверке=False, loss_ok=True, =True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (12.97%).
- rates_shock: PnL≈-1.42%, в норме по проверке=False, loss_ok=True, =True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (11.86%).
- inflation_stagflation: PnL≈-9.29%, в норме по проверке=False, loss_ok=True, =True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (11.86%).
- liquidity_shock: PnL≈-16.29%, в норме по проверке=False, loss_ok=True, =True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (13.09%).
Коды по сценариям (уникально): сильный обвал на рынке акций, стресс на рынке кредита, , , .
Факторные беты портфеля (недельная оценка, см. спецификацию): 5Y≈{beta_cmd=0.0969, beta_credit=-0.6993, beta_eq=0.5678, beta_inf=0.1000, beta_rr=-0.7082, beta_usd=-0.8411}; 10Y≈{beta_cmd=0.0731, beta_credit=-0.0892, beta_eq=0.6216, beta_inf=0.8296, beta_rr=-1.0906, beta_usd=-0.6580}.

**Сильные стороны.**

Во всех синтетических сценариях loss_ok=true — глубина потерь в рамках порогов loss-теста.
Во всех сценариях rc3_ok=true — суммарный Top3 RC не нарушает stress_top3_rc_sum_cap.
Исторический эпизод 2020 помечен в норме по проверке=true.
Исторический эпизод 2022 помечен в норме по проверке=true.

**Риски и ограничения.**

: зафиксированы диагностические коды ( сильный обвал на рынке акций, стресс на рынке кредита, , , ); для PM имеет смысл разобрать scenario_results и historical_results.
Во всех сценариях rc1_ok=false — концентрация Top1 RC выше порога rc_asset_cap_used.
Эпизод 2008: max_dd н/д — интерпретация ограничена.

## Структура риска

rc_asset_cap_used=0.1000 (доля Top1 RC, контекст отчёта); stress_top3_rc_sum_cap=0.7000; max_dd_limit (эпизоды/контекст в отчёте)=35.00%
По сценариям Top1 RC по сценариям (см. таблицу выше): сильный обвал на рынке акций COPX=13.0%, стресс на рынке кредита COPX=13.0%, rates_shock COPX=11.9%, inflation_stagflation COPX=11.9%, liquidity_shock COPX=13.1%.
Исторические эпизоды (historical_results):
- 2008: max_dd≈н/д, в норме по проверке=None, vol_annualized_episode≈н/д, diagnostic_code=—.
- 2020: max_dd≈-10.83%, в норме по проверке=True, vol_annualized_episode≈0.3789, diagnostic_code=—.
- 2022: max_dd≈-20.94%, в норме по проверке=True, vol_annualized_episode≈0.1627, diagnostic_code=—.

## Сценарный анализ

сильный обвал на рынке акций: PnL≈-22.71%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
стресс на рынке кредита: PnL≈-8.47%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
rates_shock: PnL≈-1.42%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
inflation_stagflation: PnL≈-9.29%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
liquidity_shock: PnL≈-16.29%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.


## Итог

Equal-Weight baseline: стресс-набор ( сильный обвал на рынке акций). Синтетические потери и RC-диагностика отражают текущий состав и Σ из прогона; решения по выпуску весов сверяйте с mandate_check и run_result, а этот файл используйте как сценарную справку для PM.

