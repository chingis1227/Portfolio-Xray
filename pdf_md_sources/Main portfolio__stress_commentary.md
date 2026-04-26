---
title: "Стресс: текущий состав под давлением сценариев"
date: "Итоги анализа на 10-летнем окне, по состоянию на 2026-03-31"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Ключевой вывод

По рабочему процессу проекта синтетические сценарии и исторические эпизоды в этом файле — диагностика для PM и не блокируют выпуск весов; блокирующий контур по максимальной просадке задаётся отдельно (mandate_check / IPS, полная пересекающаяся история).
Худший сценарный PnL портфеля (worst_scenario_loss_pct): -11.42%; именованный сценарий: сильный обвал на рынке акций; поле failed_test: Role.


## Ключевые показатели

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{7,00\%}{Доходность (CAGR)} & \KPIone{7,20\%}{Волатильность} & \KPIone{-15,60\%}{Макс. просадка}\\[0.55em] \KPIone{0,676}{Коэф. Шарпа} & \KPIone{1,047}{Коэф. Сортино} & \KPIone{0,401}{Чувствительность к рынку}\end{tabular}\end{center}
```


## Что это значит для инвестора

- сильный обвал на рынке акций: PnL≈-11.42%, в норме по проверке=False, loss_ok=True, =False, rc1_ok=True, rc3_ok=True; Top1 RC: BND (12.29%).
- стресс на рынке кредита: PnL≈-3.41%, в норме по проверке=True, loss_ok=True, =True, rc1_ok=True, rc3_ok=True; Top1 RC: BND (12.29%).
- rates_shock: PnL≈-6.47%, в норме по проверке=True, loss_ok=True, =True, rc1_ok=True, rc3_ok=True; Top1 RC: BND (17.95%).
- inflation_stagflation: PnL≈-6.27%, в норме по проверке=True, loss_ok=True, =True, rc1_ok=True, rc3_ok=True; Top1 RC: BND (17.95%).
- liquidity_shock: PnL≈-7.56%, в норме по проверке=True, loss_ok=True, =True, rc1_ok=True, rc3_ok=True; Top1 RC: BND (10.16%).
Коды по сценариям (уникально): сильный обвал на рынке акций.
Факторные беты портфеля (недельная оценка, см. спецификацию): 5Y≈{beta_cmd=0.0424, beta_credit=-0.1400, beta_eq=0.2857, beta_inf=-1.6700, beta_rr=-3.2370, beta_usd=-0.3654}; 10Y≈{beta_cmd=0.0287, beta_eq=0.2900, beta_inf=-1.4985, beta_rr=-3.5101, beta_usd=-0.3317}.
Портфельная факторная регрессия (5Y), недельные ряды, OLS: n_obs=153, R²=0.8543, adj R²=0.8483, intercept=0.0013, se_type=classic_ols, alpha=0.05 (CI уровень 0.95).
По факторам (β, t, p, 95% CI) — классический OLS (se_type=classic_ols):
- beta_eq: β=0.2857, t=12.146, p=<1e-6, CI=[0.2392; 0.3322]
- beta_rr: β=-3.2370, t=-10.477, p=<1e-6, CI=[-3.8476; -2.6264]
- beta_inf: β=-1.6700, t=-2.369, p=0.019154, CI=[-3.0634; -0.2767]
- beta_credit: β=-0.1400, t=-0.506, p=0.613613, CI=[-0.6866; 0.4067]
- beta_usd: β=-0.3654, t=-7.289, p=<1e-6, CI=[-0.4644; -0.2663]
- beta_cmd: β=0.0424, t=2.811, p=0.005620, CI=[0.0126; 0.0722]
HAC/Newey–West (robust) inference: se_type=hac_newey_west, kernel=bartlett, max_lags=4.
По факторам (HAC t, p, 95% CI):
- beta_eq: t_HAC=9.890, p_HAC=<1e-6, CI_HAC=[0.2286; 0.3428]
- beta_rr: t_HAC=-12.281, p_HAC=<1e-6, CI_HAC=[-3.7579; -2.7161]
- beta_inf: t_HAC=-3.231, p_HAC=0.001526, CI_HAC=[-2.6917; -0.6484]
- beta_credit: t_HAC=-0.548, p_HAC=0.584515, CI_HAC=[-0.6447; 0.3648]
- beta_usd: t_HAC=-7.159, p_HAC=<1e-6, CI_HAC=[-0.4662; -0.2645]
- beta_cmd: t_HAC=1.990, p_HAC=0.048480, CI_HAC=[0.0003; 0.0845]
Автокорреляция остатков факторной OLS: Durbin–Watson=2.1084 (≈2 — мало АК первого порядка; метод: durbin_watson_breusch_godfrey_lm).
Breusch–Godfrey LM (H₀: нет АК до порядка p; LM ~ χ²(p)):
 lags=1: LM=0.4859, df=1, p=0.485775, T_aux=152, R²_aux=0.0032
 lags=2: LM=1.7161, df=2, p=0.423993, T_aux=151, R²_aux=0.0114
 lags=4: LM=4.2352, df=4, p=0.375112, T_aux=149, R²_aux=0.0284

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

Портфельная факторная регрессия (10Y), недельные ряды, OLS: n_obs=520, R²=0.9066, adj R²=0.9057, intercept=0.0007, se_type=classic_ols, alpha=0.05 (CI уровень 0.95).
По факторам (β, t, p, 95% CI) — классический OLS (se_type=classic_ols):
- beta_eq: β=0.2890, t=41.177, p=<1e-6, CI=[0.2752; 0.3028]
- beta_rr: β=-3.5103, t=-25.191, p=<1e-6, CI=[-3.7840; -3.2365]
- beta_inf: β=-1.4955, t=-6.297, p=<1e-6, CI=[-1.9621; -1.0289]
- beta_usd: β=-0.3262, t=-13.959, p=<1e-6, CI=[-0.3721; -0.2803]
- beta_cmd: β=0.0290, t=4.416, p=0.000012, CI=[0.0161; 0.0420]
HAC/Newey–West (robust) inference: se_type=hac_newey_west, kernel=bartlett, max_lags=4.
По факторам (HAC t, p, 95% CI):
- beta_eq: t_HAC=30.191, p_HAC=<1e-6, CI_HAC=[0.2702; 0.3078]
- beta_rr: t_HAC=-13.024, p_HAC=<1e-6, CI_HAC=[-4.0398; -2.9808]
- beta_inf: t_HAC=-3.870, p_HAC=0.000123, CI_HAC=[-2.2548; -0.7363]
- beta_credit: t_HAC=-12.122, p_HAC=<1e-6, CI_HAC=[-0.3791; -0.2733]
- beta_usd: t_HAC=3.606, p_HAC=0.000342, CI_HAC=[0.0132; 0.0449]
Автокорреляция остатков факторной OLS: Durbin–Watson=2.1172 (≈2 — мало АК первого порядка; метод: durbin_watson_breusch_godfrey_lm).
Breusch–Godfrey LM (H₀: нет АК до порядка p; LM ~ χ²(p)):
 lags=1: LM=1.8648, df=1, p=0.172069, T_aux=519, R²_aux=0.0036
 lags=2: LM=1.9286, df=2, p=0.381241, T_aux=518, R²_aux=0.0037
 lags=4: LM=6.3765, df=4, p=0.172741, T_aux=516, R²_aux=0.0124

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
 beta_eq: n=889, mean=0.2375, median=0.2487, p10=0.1356, p90=0.3047
 beta_rr: n=889, mean=-2.9411, median=-3.0171, p10=-4.4448, p90=-1.4983
 beta_inf: n=889, mean=-1.4535, median=-1.4437, p10=-2.0762, p90=-0.8832
 beta_usd: n=889, mean=-0.2827, median=-0.2573, p10=-0.4311, p90=-0.1989
 beta_cmd: n=889, mean=0.0367, median=0.0343, p10=0.0177, p90=0.0566

Окно 5y:
 beta_eq: n=785, mean=0.2420, median=0.2661, p10=0.1409, p90=0.3056
 beta_rr: n=785, mean=-2.9640, median=-3.0394, p10=-4.2814, p90=-1.5326
 beta_inf: n=785, mean=-1.4216, median=-1.3795, p10=-2.0014, p90=-1.0084
 beta_usd: n=785, mean=-0.2796, median=-0.2593, p10=-0.3891, p90=-0.2131
 beta_cmd: n=785, mean=0.0358, median=0.0374, p10=0.0223, p90=0.0512

Окно 10y:
 beta_eq: n=525, mean=0.2501, median=0.2855, p10=0.1672, p90=0.2895
 beta_rr: n=525, mean=-2.9909, median=-3.3818, p10=-3.5411, p90=-2.0245
 beta_inf: n=525, mean=-1.5180, median=-1.5209, p10=-1.6845, p90=-1.3783
 beta_usd: n=525, mean=-0.2586, median=-0.2491, p10=-0.3031, p90=-0.2222
 beta_cmd: n=525, mean=0.0362, median=0.0344, p10=0.0304, p90=0.0425

Файлы графиков скользящих β (PNG, папка прогона): 10y→rolling_factor_betas_10y.png, 3y→rolling_factor_betas_3y.png, 5y→rolling_factor_betas_5y.png
![Rolling factor betas — 3y](../Main portfolio/rolling_factor_betas_3y.png)
![Rolling factor betas — 5y](../Main portfolio/rolling_factor_betas_5y.png)
![Rolling factor betas — 10y](../Main portfolio/rolling_factor_betas_10y.png)

**Сильные стороны.**

Во всех синтетических сценариях loss_ok=true — глубина потерь в рамках порогов loss-теста.
Во всех сценариях rc3_ok=true — суммарный Top3 RC не нарушает stress_top3_rc_sum_cap.
Есть сценарии с в норме по проверке=true.
Исторический эпизод 2020 помечен в норме по проверке=true.
Исторический эпизод 2022 помечен в норме по проверке=true.

**Риски и ограничения.**

: зафиксированы диагностические коды ( сильный обвал на рынке акций); для PM имеет смысл разобрать scenario_results и historical_results.
Эпизод 2008: max_dd н/д — интерпретация ограничена.

## Структура риска

rc_asset_cap_used=0.1000 (доля Top1 RC, контекст отчёта); stress_top3_rc_sum_cap=0.7000; max_dd_limit (эпизоды/контекст в отчёте)=20.00%
По сценариям Top1 RC по сценариям (см. таблицу выше): сильный обвал на рынке акций BND=12.3%, стресс на рынке кредита BND=12.3%, rates_shock BND=17.9%, inflation_stagflation BND=17.9%, liquidity_shock BND=10.2%.
Исторические эпизоды (historical_results):
- 2008: pnl_real_episode≈н/д, max_dd≈н/д, в норме по проверке=None, vol_annualized_episode≈н/д, diagnostic_code=—.
- 2020: pnl_real_episode≈-1.83%, max_dd≈-5.16%, в норме по проверке=True, vol_annualized_episode≈0.1917, diagnostic_code=—.
- 2022: pnl_real_episode≈-13.35%, max_dd≈-15.62%, в норме по проверке=True, vol_annualized_episode≈0.0954, diagnostic_code=—.
OOS объяснение эпизодов через β×shock (5Y/10Y/rolling-3Y pre):
- 2008: real=н/д, model_5y=-16.80%, model_10y=-16.26%, model_roll3y=-9.30%; |err|: 5y=н/д, 10y=н/д, roll3y=н/д.
- 2020: real=-1.83%, model_5y=-3.63%, model_10y=-3.11%, model_roll3y=-2.36%; |err|: 5y=1.80%, 10y=1.28%, roll3y=0.53%.
- 2022: real=-13.35%, model_5y=-15.68%, model_10y=-16.38%, model_roll3y=-19.25%; |err|: 5y=2.33%, 10y=3.03%, roll3y=5.90%.
Средняя |ошибка| по эпизодам: 5Y=2.07%, 10Y=2.16%, rolling-3Y=3.21% (n=2).

## Сценарный анализ

сильный обвал на рынке акций: PnL≈-11.42%, итог в норме по проверке=False — см. loss/role/rc в Metric-by-Metric.
стресс на рынке кредита: PnL≈-3.41%, итог в норме по проверке=True — см. loss/role/rc в Metric-by-Metric.
rates_shock: PnL≈-6.47%, итог в норме по проверке=True — см. loss/role/rc в Metric-by-Metric.
inflation_stagflation: PnL≈-6.27%, итог в норме по проверке=True — см. loss/role/rc в Metric-by-Metric.
liquidity_shock: PnL≈-7.56%, итог в норме по проверке=True — см. loss/role/rc в Metric-by-Metric.


## Итог

основной портфель (Main portfolio): стресс-набор ( сильный обвал на рынке акций). Синтетические потери и RC-диагностика отражают текущий состав и Σ из прогона; решения по выпуску весов сверяйте с mandate_check и run_result, а этот файл используйте как сценарную справку для PM.

