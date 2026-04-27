---
title: "Стресс: как ведёт себя equal-weight"
date: "Итоги анализа на 10-летнем окне, по состоянию на 2026-03-31"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Ключевой вывод

По рабочему процессу проекта синтетические сценарии и исторические эпизоды в этом файле — диагностика для PM и не блокируют выпуск весов; блокирующий контур по максимальной просадке задаётся отдельно (mandate_check / IPS, полная пересекающаяся история).
Худший сценарный PnL портфеля (worst_scenario_loss_pct): -23.58%; именованный сценарий: сильный обвал на рынке акций; поле failed_test: Loss.


## Ключевые показатели

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{12,80\%}{Доходность (CAGR)} & \KPIone{13,10\%}{Волатильность} & \KPIone{-18,70\%}{Макс. просадка}\\[0.55em] \KPIone{0,819}{Коэф. Шарпа} & \KPIone{1,334}{Коэф. Сортино} & \KPIone{0,741}{Чувствительность к рынку}\end{tabular}\end{center}
```


## Что это значит для инвестора

- сильный обвал на рынке акций: PnL≈-23.58%, в норме по проверке=False, loss_ok=False, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (14.41%).
- стресс на рынке кредита: PnL≈-7.57%, в норме по проверке=False, loss_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (14.41%).
- rates_shock: PnL≈-1.84%, в норме по проверке=False, loss_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (15.79%).
- inflation_stagflation: PnL≈-10.18%, в норме по проверке=False, loss_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (15.79%).
- liquidity_shock: PnL≈-15.99%, в норме по проверке=False, loss_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: COPX (14.41%).
Коды по сценариям (уникально): сильный обвал на рынке акций, сильный обвал на рынке акций, стресс на рынке кредита, , , .
Факторные беты портфеля (недельная оценка, см. спецификацию): 5Y≈{beta_cmd=0.0827, beta_credit=-0.4188, beta_eq=0.5894, beta_inf=0.9621, beta_rr=-0.9192, beta_usd=-0.9247}; 10Y≈{beta_cmd=0.0819, beta_eq=0.5673, beta_inf=1.4617, beta_rr=-1.1325, beta_usd=-0.7749}.
Портфельная факторная регрессия (5Y), недельные ряды, OLS: n_obs=153, R²=0.7570, adj R²=0.7470, intercept=0.0017, se_type=classic_ols, alpha=0.05 (CI уровень 0.95).
По факторам (β, t, p, 95% CI) — классический OLS (se_type=classic_ols):
- beta_eq: β=0.5894, t=9.888, p=<1e-6, CI=[0.4716; 0.7073]
- beta_rr: β=-0.9192, t=-1.174, p=0.242310, CI=[-2.4667; 0.6282]
- beta_inf: β=0.9621, t=0.539, p=0.591050, CI=[-2.5690; 4.4933]
- beta_credit: β=-0.4188, t=-0.598, p=0.551088, CI=[-1.8042; 0.9665]
- beta_usd: β=-0.9247, t=-7.280, p=<1e-6, CI=[-1.1757; -0.6736]
- beta_cmd: β=0.0827, t=2.163, p=0.032149, CI=[0.0071; 0.1582]
HAC/Newey–West (robust) inference: se_type=hac_newey_west, kernel=bartlett, max_lags=4.
По факторам (HAC t, p, 95% CI):
- beta_eq: t_HAC=8.457, p_HAC=<1e-6, CI_HAC=[0.4517; 0.7272]
- beta_rr: t_HAC=-1.850, p_HAC=0.066267, CI_HAC=[-1.9010; 0.0625]
- beta_inf: t_HAC=0.694, p_HAC=0.489027, CI_HAC=[-1.7793; 3.7036]
- beta_credit: t_HAC=-0.591, p_HAC=0.555451, CI_HAC=[-1.8196; 0.9819]
- beta_usd: t_HAC=-6.775, p_HAC=<1e-6, CI_HAC=[-1.1944; -0.6549]
- beta_cmd: t_HAC=1.506, p_HAC=0.134266, CI_HAC=[-0.0258; 0.1912]
Автокорреляция остатков факторной OLS: Durbin–Watson=1.9778 (≈2 — мало АК первого порядка; метод: durbin_watson_breusch_godfrey_lm).
Breusch–Godfrey LM (H₀: нет АК до порядка p; LM ~ χ²(p)):
 lags=1: LM=0.0185, df=1, p=0.891793, T_aux=152, R²_aux=0.0001
 lags=2: LM=1.1219, df=2, p=0.570678, T_aux=151, R²_aux=0.0074
 lags=4: LM=4.9459, df=4, p=0.292897, T_aux=149, R²_aux=0.0332

Мультиколлинеарность факторов (те же недели, что регрессия): оценка=low; cond(R)=10.256; max VIF=2.794 (фактор credit).
Сильнейшая попарная корреляция: equity vs credit, ρ=-0.7547.
Интерпретация: Низкая: типичные VIF и cond(R); коллинеарность не доминирует, но попарные корреляции всё равно учитывать.
Все попарные ρ (|ρ| по убыванию):
 equity — credit: ρ=-0.7547
 inflation — commodity: ρ=0.4082
 inflation — credit: ρ=-0.3958
 equity — usd: ρ=-0.3004
 real_rates — usd: ρ=0.2557
 credit — commodity: ρ=-0.2538
 real_rates — inflation: ρ=0.2506
 credit — usd: ρ=0.2129
 equity — real_rates: ρ=-0.2048
 equity — inflation: ρ=0.1862
 inflation — usd: ρ=0.1530
 equity — commodity: ρ=0.1336
 real_rates — credit: ρ=0.0716
 real_rates — commodity: ρ=0.0627
 usd — commodity: ρ=-0.0375
VIF по факторам:
 commodity: 1.226
 credit: 2.794
 equity: 2.555
 inflation: 1.558
 real_rates: 1.175
 usd: 1.200
Метод: pearson_sample_corr_vif_raw_regressors; n_obs_f=153.

Портфельная факторная регрессия (10Y), недельные ряды, OLS: n_obs=520, R²=0.8581, adj R²=0.8567, intercept=0.0009, se_type=classic_ols, alpha=0.05 (CI уровень 0.95).
По факторам (β, t, p, 95% CI) — классический OLS (se_type=classic_ols):
- beta_eq: β=0.5652, t=33.813, p=<1e-6, CI=[0.5323; 0.5980]
- beta_rr: β=-1.1328, t=-3.414, p=0.000691, CI=[-1.7847; -0.4809]
- beta_inf: β=1.4682, t=2.596, p=0.009703, CI=[0.3571; 2.5794]
- beta_usd: β=-0.7627, t=-13.705, p=<1e-6, CI=[-0.8720; -0.6534]
- beta_cmd: β=0.0826, t=5.274, p=<1e-6, CI=[0.0518; 0.1134]
HAC/Newey–West (robust) inference: se_type=hac_newey_west, kernel=bartlett, max_lags=4.
По факторам (HAC t, p, 95% CI):
- beta_eq: t_HAC=25.523, p_HAC=<1e-6, CI_HAC=[0.5217; 0.6087]
- beta_rr: t_HAC=-2.747, p_HAC=0.006233, CI_HAC=[-1.9431; -0.3225]
- beta_inf: t_HAC=2.499, p_HAC=0.012775, CI_HAC=[0.3139; 2.6226]
- beta_credit: t_HAC=-11.042, p_HAC=<1e-6, CI_HAC=[-0.8984; -0.6270]
- beta_usd: t_HAC=3.825, p_HAC=0.000147, CI_HAC=[0.0402; 0.1250]
Автокорреляция остатков факторной OLS: Durbin–Watson=2.1123 (≈2 — мало АК первого порядка; метод: durbin_watson_breusch_godfrey_lm).
Breusch–Godfrey LM (H₀: нет АК до порядка p; LM ~ χ²(p)):
 lags=1: LM=1.7236, df=1, p=0.189230, T_aux=519, R²_aux=0.0033
 lags=2: LM=2.9305, df=2, p=0.231023, T_aux=518, R²_aux=0.0057
 lags=4: LM=8.4523, df=4, p=0.076346, T_aux=516, R²_aux=0.0164

Мультиколлинеарность факторов (те же недели, что регрессия): оценка=low; cond(R)=5.401; max VIF=1.458 (фактор equity).
Сильнейшая попарная корреляция: inflation vs commodity, ρ=0.4684.
Интерпретация: Низкая: типичные VIF и cond(R); коллинеарность не доминирует, но попарные корреляции всё равно учитывать.
Все попарные ρ (|ρ| по убыванию):
 inflation — commodity: ρ=0.4684
 equity — usd: ρ=-0.4645
 equity — inflation: ρ=0.3822
 equity — commodity: ρ=0.3427
 usd — commodity: ρ=-0.3405
 real_rates — usd: ρ=0.3057
 equity — real_rates: ρ=-0.2102
 inflation — usd: ρ=-0.1803
 real_rates — inflation: ρ=-0.1687
 real_rates — commodity: ρ=-0.1128
VIF по факторам:
 commodity: 1.417
 equity: 1.458
 inflation: 1.409
 real_rates: 1.125
 usd: 1.437
Метод: pearson_sample_corr_vif_raw_regressors; n_obs_f=520.

Скользящие окна (недель): 10y=520, 3y=156, 5y=260.
Сводка скользящих β (по всей доступной истории в прогоне): mean, median, p10, p90:
Окно 3y:
 beta_eq: n=889, mean=0.5097, median=0.5446, p10=0.2916, p90=0.6233
 beta_rr: n=889, mean=-0.6631, median=-0.6189, p10=-1.8780, p90=0.7600
 beta_inf: n=889, mean=1.0291, median=0.7517, p10=0.1354, p90=2.4280
 beta_usd: n=889, mean=-0.6770, median=-0.6249, p10=-1.0161, p90=-0.4647
 beta_cmd: n=889, mean=0.0973, median=0.0978, p10=0.0562, p90=0.1397

Окно 5y:
 beta_eq: n=785, mean=0.5159, median=0.5300, p10=0.3176, p90=0.6118
 beta_rr: n=785, mean=-0.5600, median=-0.7835, p10=-1.9593, p90=1.2495
 beta_inf: n=785, mean=1.1040, median=0.8553, p10=0.3409, p90=2.2531
 beta_usd: n=785, mean=-0.6716, median=-0.6423, p10=-0.9208, p90=-0.5110
 beta_cmd: n=785, mean=0.0976, median=0.0932, p10=0.0739, p90=0.1270

Окно 10y:
 beta_eq: n=525, mean=0.5201, median=0.5601, p10=0.3798, p90=0.5917
 beta_rr: n=525, mean=-0.5254, median=-0.8421, p10=-1.1483, p90=0.5733
 beta_inf: n=525, mean=0.9898, median=1.1919, p10=0.1825, p90=1.6506
 beta_usd: n=525, mean=-0.6253, median=-0.6047, p10=-0.7137, p90=-0.5599
 beta_cmd: n=525, mean=0.0967, median=0.0966, p10=0.0873, p90=0.1069

Файлы графиков скользящих β (PNG, папка прогона): 10y→rolling_factor_betas_10y.png, 3y→rolling_factor_betas_3y.png, 5y→rolling_factor_betas_5y.png
![Rolling factor betas — 3y](../equal-weight portfolio/rolling_factor_betas_3y.png)
![Rolling factor betas — 5y](../equal-weight portfolio/rolling_factor_betas_5y.png)
![Rolling factor betas — 10y](../equal-weight portfolio/rolling_factor_betas_10y.png)

**Сильные стороны.**

Во всех сценариях rc3_ok=true — суммарный Top3 RC не нарушает stress_top3_rc_sum_cap.
Исторический эпизод 2020 помечен в норме по проверке=true.
Исторический эпизод 2022 помечен в норме по проверке=true.

**Риски и ограничения.**

: зафиксированы диагностические коды ( сильный обвал на рынке акций, сильный обвал на рынке акций, стресс на рынке кредита, , , ); для PM имеет смысл разобрать scenario_results и historical_results.
Во всех сценариях rc1_ok=false — концентрация Top1 RC выше порога rc_asset_cap_used.
Эпизод 2008: max_dd н/д — интерпретация ограничена.

## Структура риска

rc_asset_cap_used=0.1000 (доля Top1 RC, контекст отчёта); stress_top3_rc_sum_cap=0.7000; max_dd_limit (эпизоды/контекст в отчёте)=20.00%
По сценариям Top1 RC по сценариям (см. таблицу выше): сильный обвал на рынке акций COPX=14.4%, стресс на рынке кредита COPX=14.4%, rates_shock COPX=15.8%, inflation_stagflation COPX=15.8%, liquidity_shock COPX=14.4%.
Исторические эпизоды (historical_results):
- 2008: pnl_real_episode≈н/д, max_dd≈н/д, в норме по проверке=None, vol_annualized_episode≈н/д, diagnostic_code=—.
- 2020: pnl_real_episode≈-8.75%, max_dd≈-11.50%, в норме по проверке=True, vol_annualized_episode≈0.3857, diagnostic_code=—.
- 2022: pnl_real_episode≈-13.95%, max_dd≈-18.65%, в норме по проверке=True, vol_annualized_episode≈0.1522, diagnostic_code=—.
OOS объяснение эпизодов через β×shock (5Y/10Y/rolling-3Y pre):
- 2008: real=н/д, model_5y=-46.51%, model_10y=-43.67%, model_roll3y=-21.73%; |err|: 5y=н/д, 10y=н/д, roll3y=н/д.
- 2020: real=-8.75%, model_5y=-12.12%, model_10y=-11.43%, model_roll3y=-10.06%; |err|: 5y=3.37%, 10y=2.68%, roll3y=1.31%.
- 2022: real=-13.95%, model_5y=-19.51%, model_10y=-18.11%, model_roll3y=-19.09%; |err|: 5y=5.56%, 10y=4.16%, roll3y=5.14%.
Средняя |ошибка| по эпизодам: 5Y=4.47%, 10Y=3.42%, rolling-3Y=3.23% (n=2).

## Сценарный анализ

сильный обвал на рынке акций: PnL≈-23.58%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
стресс на рынке кредита: PnL≈-7.57%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
rates_shock: PnL≈-1.84%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
inflation_stagflation: PnL≈-10.18%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
liquidity_shock: PnL≈-15.99%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.


## Итог

Equal-Weight baseline: стресс-набор ( сильный обвал на рынке акций). Синтетические потери и RC-диагностика отражают текущий состав и Σ из прогона; решения по выпуску весов сверяйте с mandate_check и run_result, а этот файл используйте как сценарную справку для PM.

