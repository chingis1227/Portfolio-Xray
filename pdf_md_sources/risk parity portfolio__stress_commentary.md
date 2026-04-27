---
title: "Стресс: как ведёт себя risk parity"
date: "Итоги анализа на 10-летнем окне, по состоянию на 2026-03-31"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Ключевой вывод

По рабочему процессу проекта синтетические сценарии и исторические эпизоды в этом файле — диагностика для PM и не блокируют выпуск весов; блокирующий контур по максимальной просадке задаётся отдельно (mandate_check / IPS, полная пересекающаяся история).
Худший сценарный PnL портфеля (worst_scenario_loss_pct): -11.49%; именованный сценарий: сильный обвал на рынке акций; поле failed_test: RC_Top1.


## Ключевые показатели

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{7,70\%}{Доходность (CAGR)} & \KPIone{6,70\%}{Волатильность} & \KPIone{-11,00\%}{Макс. просадка}\\[0.55em] \KPIone{0,805}{Коэф. Шарпа} & \KPIone{1,291}{Коэф. Сортино} & \KPIone{0,381}{Чувствительность к рынку}\end{tabular}\end{center}
```


## Что это значит для инвестора

- сильный обвал на рынке акций: PnL≈-11.49%, в норме по проверке=False, loss_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: GLD (10.81%).
- стресс на рынке кредита: PnL≈-3.36%, в норме по проверке=False, loss_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: GLD (10.81%).
- rates_shock: PnL≈-2.51%, в норме по проверке=True, loss_ok=True, rc1_ok=True, rc3_ok=True; Top1 RC: BBJP (8.57%).
- inflation_stagflation: PnL≈-5.38%, в норме по проверке=True, loss_ok=True, rc1_ok=True, rc3_ok=True; Top1 RC: BBJP (8.57%).
- liquidity_shock: PnL≈-7.55%, в норме по проверке=False, loss_ok=True, rc1_ok=False, rc3_ok=True; Top1 RC: GLD (10.81%).
Коды по сценариям (уникально): сильный обвал на рынке акций, стресс на рынке кредита, .
Факторные беты портфеля (недельная оценка, см. спецификацию): 5Y≈{beta_cmd=0.0398, beta_credit=-0.1227, beta_eq=0.2872, beta_inf=0.3912, beta_rr=-1.2574, beta_usd=-0.4489}; 10Y≈{beta_cmd=0.0351, beta_eq=0.2840, beta_inf=0.4477, beta_rr=-1.4909, beta_usd=-0.3751}.
Портфельная факторная регрессия (5Y), недельные ряды, OLS: n_obs=153, R²=0.7721, adj R²=0.7627, intercept=0.0014, se_type=classic_ols, alpha=0.05 (CI уровень 0.95).
По факторам (β, t, p, 95% CI) — классический OLS (se_type=classic_ols):
- beta_eq: β=0.2872, t=10.089, p=<1e-6, CI=[0.2310; 0.3435]
- beta_rr: β=-1.2574, t=-3.363, p=0.000985, CI=[-1.9963; -0.5184]
- beta_inf: β=0.3912, t=0.459, p=0.647266, CI=[-1.2950; 2.0774]
- beta_credit: β=-0.1227, t=-0.366, p=0.714583, CI=[-0.7842; 0.5389]
- beta_usd: β=-0.4489, t=-7.400, p=<1e-6, CI=[-0.5687; -0.3290]
- beta_cmd: β=0.0398, t=2.180, p=0.030862, CI=[0.0037; 0.0759]
HAC/Newey–West (robust) inference: se_type=hac_newey_west, kernel=bartlett, max_lags=4.
По факторам (HAC t, p, 95% CI):
- beta_eq: t_HAC=8.236, p_HAC=<1e-6, CI_HAC=[0.2183; 0.3561]
- beta_rr: t_HAC=-4.424, p_HAC=0.000019, CI_HAC=[-1.8191; -0.6957]
- beta_inf: t_HAC=0.619, p_HAC=0.536892, CI_HAC=[-0.8579; 1.6402]
- beta_credit: t_HAC=-0.384, p_HAC=0.701191, CI_HAC=[-0.7532; 0.5078]
- beta_usd: t_HAC=-7.185, p_HAC=<1e-6, CI_HAC=[-0.5723; -0.3254]
- beta_cmd: t_HAC=1.504, p_HAC=0.134647, CI_HAC=[-0.0125; 0.0921]
Автокорреляция остатков факторной OLS: Durbin–Watson=2.0826 (≈2 — мало АК первого порядка; метод: durbin_watson_breusch_godfrey_lm).
Breusch–Godfrey LM (H₀: нет АК до порядка p; LM ~ χ²(p)):
 lags=1: LM=0.2891, df=1, p=0.590814, T_aux=152, R²_aux=0.0019
 lags=2: LM=1.6525, df=2, p=0.437689, T_aux=151, R²_aux=0.0109
 lags=4: LM=3.8026, df=4, p=0.433386, T_aux=149, R²_aux=0.0255

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

Портфельная факторная регрессия (10Y), недельные ряды, OLS: n_obs=520, R²=0.8789, adj R²=0.8777, intercept=0.0007, se_type=classic_ols, alpha=0.05 (CI уровень 0.95).
По факторам (β, t, p, 95% CI) — классический OLS (se_type=classic_ols):
- beta_eq: β=0.2827, t=36.481, p=<1e-6, CI=[0.2675; 0.2979]
- beta_rr: β=-1.4911, t=-9.693, p=<1e-6, CI=[-1.7934; -1.1889]
- beta_inf: β=0.4518, t=1.723, p=0.085458, CI=[-0.0633; 0.9670]
- beta_usd: β=-0.3674, t=-14.241, p=<1e-6, CI=[-0.4181; -0.3167]
- beta_cmd: β=0.0356, t=4.896, p=0.000001, CI=[0.0213; 0.0498]
HAC/Newey–West (robust) inference: se_type=hac_newey_west, kernel=bartlett, max_lags=4.
По факторам (HAC t, p, 95% CI):
- beta_eq: t_HAC=26.757, p_HAC=<1e-6, CI_HAC=[0.2619; 0.3034]
- beta_rr: t_HAC=-6.520, p_HAC=<1e-6, CI_HAC=[-1.9404; -1.0418]
- beta_inf: t_HAC=1.512, p_HAC=0.131179, CI_HAC=[-0.1353; 1.0390]
- beta_credit: t_HAC=-11.607, p_HAC=<1e-6, CI_HAC=[-0.4296; -0.3052]
- beta_usd: t_HAC=3.663, p_HAC=0.000275, CI_HAC=[0.0165; 0.0546]
Автокорреляция остатков факторной OLS: Durbin–Watson=2.1163 (≈2 — мало АК первого порядка; метод: durbin_watson_breusch_godfrey_lm).
Breusch–Godfrey LM (H₀: нет АК до порядка p; LM ~ χ²(p)):
 lags=1: LM=1.8474, df=1, p=0.174091, T_aux=519, R²_aux=0.0036
 lags=2: LM=3.8430, df=2, p=0.146391, T_aux=518, R²_aux=0.0074
 lags=4: LM=8.1560, df=4, p=0.086029, T_aux=516, R²_aux=0.0158

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
 beta_eq: n=889, mean=0.2529, median=0.2667, p10=0.1421, p90=0.3082
 beta_rr: n=889, mean=-1.1723, median=-1.2319, p10=-2.1178, p90=0.2939
 beta_inf: n=889, mean=0.1276, median=0.1159, p10=-0.6436, p90=0.8922
 beta_usd: n=889, mean=-0.3266, median=-0.3006, p10=-0.4650, p90=-0.2373
 beta_cmd: n=889, mean=0.0454, median=0.0430, p10=0.0262, p90=0.0659

Окно 5y:
 beta_eq: n=785, mean=0.2566, median=0.2718, p10=0.1535, p90=0.3043
 beta_rr: n=785, mean=-1.1689, median=-1.4162, p10=-2.1731, p90=0.3029
 beta_inf: n=785, mean=0.1456, median=0.1326, p10=-0.4594, p90=0.7044
 beta_usd: n=785, mean=-0.3220, median=-0.3129, p10=-0.4236, p90=-0.2544
 beta_cmd: n=785, mean=0.0453, median=0.0440, p10=0.0337, p90=0.0622

Окно 10y:
 beta_eq: n=525, mean=0.2594, median=0.2810, p10=0.1853, p90=0.2968
 beta_rr: n=525, mean=-1.1706, median=-1.4107, p10=-1.6883, p90=-0.2906
 beta_inf: n=525, mean=0.0863, median=0.0738, p10=-0.2711, p90=0.4489
 beta_usd: n=525, mean=-0.3027, median=-0.3013, p10=-0.3378, p90=-0.2719
 beta_cmd: n=525, mean=0.0451, median=0.0438, p10=0.0405, p90=0.0511

Файлы графиков скользящих β (PNG, папка прогона): 10y→rolling_factor_betas_10y.png, 3y→rolling_factor_betas_3y.png, 5y→rolling_factor_betas_5y.png
![Rolling factor betas — 3y](../risk parity portfolio/rolling_factor_betas_3y.png)
![Rolling factor betas — 5y](../risk parity portfolio/rolling_factor_betas_5y.png)
![Rolling factor betas — 10y](../risk parity portfolio/rolling_factor_betas_10y.png)

**Сильные стороны.**

Во всех синтетических сценариях loss_ok=true — глубина потерь в рамках порогов loss-теста.
Во всех сценариях rc3_ok=true — суммарный Top3 RC не нарушает stress_top3_rc_sum_cap.
Есть сценарии с в норме по проверке=true.
Исторический эпизод 2020 помечен в норме по проверке=true.
Исторический эпизод 2022 помечен в норме по проверке=true.

**Риски и ограничения.**

: зафиксированы диагностические коды ( сильный обвал на рынке акций, стресс на рынке кредита, ); для PM имеет смысл разобрать scenario_results и historical_results.
Эпизод 2008: max_dd н/д — интерпретация ограничена.

## Структура риска

rc_asset_cap_used=0.1000 (доля Top1 RC, контекст отчёта); stress_top3_rc_sum_cap=0.7000; max_dd_limit (эпизоды/контекст в отчёте)=20.00%
По сценариям Top1 RC по сценариям (см. таблицу выше): сильный обвал на рынке акций GLD=10.8%, стресс на рынке кредита GLD=10.8%, rates_shock BBJP=8.6%, inflation_stagflation BBJP=8.6%, liquidity_shock GLD=10.8%.
Исторические эпизоды (historical_results):
- 2008: pnl_real_episode≈н/д, max_dd≈н/д, в норме по проверке=None, vol_annualized_episode≈н/д, diagnostic_code=—.
- 2020: pnl_real_episode≈-3.64%, max_dd≈-5.50%, в норме по проверке=True, vol_annualized_episode≈0.1921, diagnostic_code=—.
- 2022: pnl_real_episode≈-7.97%, max_dd≈-10.96%, в норме по проверке=True, vol_annualized_episode≈0.0831, diagnostic_code=—.
OOS объяснение эпизодов через β×shock (5Y/10Y/rolling-3Y pre):
- 2008: real=н/д, model_5y=-21.81%, model_10y=-20.45%, model_roll3y=-12.28%; |err|: 5y=н/д, 10y=н/д, roll3y=н/д.
- 2020: real=-3.64%, model_5y=-5.62%, model_10y=-5.07%, model_roll3y=-4.29%; |err|: 5y=1.98%, 10y=1.43%, roll3y=0.65%.
- 2022: real=-7.97%, model_5y=-11.60%, model_10y=-11.44%, model_roll3y=-12.89%; |err|: 5y=3.63%, 10y=3.47%, roll3y=4.92%.
Средняя |ошибка| по эпизодам: 5Y=2.80%, 10Y=2.45%, rolling-3Y=2.78% (n=2).

## Сценарный анализ

сильный обвал на рынке акций: PnL≈-11.49%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
стресс на рынке кредита: PnL≈-3.36%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
rates_shock: PnL≈-2.51%, итог в норме по проверке=True — см. loss/role/rc в Metric-by-Metric.
inflation_stagflation: PnL≈-5.38%, итог в норме по проверке=True — см. loss/role/rc в Metric-by-Metric.
liquidity_shock: PnL≈-7.55%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.


## Итог

Risk-Parity baseline: стресс-набор ( сильный обвал на рынке акций). Синтетические потери и RC-диагностика отражают текущий состав и Σ из прогона; решения по выпуску весов сверяйте с mandate_check и run_result, а этот файл используйте как сценарную справку для PM.

