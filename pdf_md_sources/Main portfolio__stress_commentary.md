---
title: "Main Portfolio ? Stress Commentary"
subtitle: "Commentary"
date: "2026-03-24 14:42 Центральная Европа (зима)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Variant folder:** `Main portfolio`
- **Basis:** full stress block interpretation from stress_report.json + historical validation diagnostics.
- **Commentary file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Cursor/Main portfolio/stress_commentary.txt`
- **Generated:** 2026-03-24 14:42 Центральная Европа (зима)

## Executive summary
По Main portfolio стресс-блок имеет статус FAIL_STRESS с причиной FAIL_ROLE_EQUITY_SHOCK при худшем сценарном результате -101.64% (credit_shock). Портфель не проходит не только role-тест в equity_shock, но и loss-тест в credit и liquidity сценариях, а также системно нарушает Top1 RC cap (rc1_ok=false во всех пяти сценариях). Это указывает на структурно перегруженный риск-профиль с высокой концентрацией и недостаточным защитным контуром в критических режимах. Текущие factor-betas (особенно beta_credit) выглядят экстремально, что усиливает стресс-PnL и требует осторожной интерпретации качества факторной калибровки именно для этого прогона. Историческая валидация также слабая: 2020/2022 помечены pass=false при NaN по max_dd, а эпизод 2008 не заполнен.


## Metric-by-Metric Interpretation

Сценарные PnL показывают тяжелую уязвимость: equity -24.45%, credit -101.64%, rates -2.04%, stagflation -10.49%, liquidity -86.93%. Формально это означает прохождение только “мягких” сценариев rates/stagflation по loss, при явном breach в credit/liquidity и глубоком drawdown профиле в equity shock.

По статусам тестов: equity_shock имеет role_ok=false и rc1_ok=false; credit/liquidity имеют loss_ok=false и rc1_ok=false; rates/stagflation проходят loss/role, но также проваливают rc1. Top3 RC остается в пределах лимита (rc3_ok=true), поэтому главный концентрационный дефект сосредоточен в первом риск-драйвере, а не в общей тройке лидеров.

Факторные беты 5Y: beta_eq=0.5917, beta_rr=-1.0167, beta_inf=1.0804, beta_credit=-23.8586, beta_usd=-0.8550, beta_cmd=0.0899; 10Y: beta_eq=0.6280, beta_rr=-1.6861, beta_inf=0.7041, beta_credit=-40.7968, beta_usd=-0.6473, beta_cmd=0.1167. Масштаб beta_credit для данного прогона остается экстремальным и практически определяет разрушительный credit/liquidity стресс-результат, что повышает модельный риск интерпретации.


## Risk Structure

Stress RC демонстрирует устойчивый Top1 RC около 21.5-22.4% при cap=10%, Top3 RC около 49.6-51.3% при cap=70%. Следовательно, портфель чрезмерно концентрирован в первом источнике риска и не удовлетворяет базовому требованию к диверсификации risk contribution.

По блокам в equity_shock наблюдается классический role-fail паттерн: Growth -24.28%, Duration -0.02%, Inflation -0.14%, Tail 0.00%. В credit/liquidity шоках отрицательный вклад Growth остается доминирующим (-254.88% и -201.79%), а позитив Inflation не компенсирует потери на уровне loss-гейта.

Историческая валидация недостаточно надежна: для 2020 и 2022 max_dd = NaN, volatility_spike_ratio = null, pass=false; для 2008 данные отсутствуют. В таком виде historical layer не подтверждает устойчивость портфеля в кризисных эпизодах и должен рассматриваться как неполный контроль.


## Strengths

- Top3 RC находится ниже заданного лимита (70%) во всех сценариях.
- По rates/stagflation loss-тест формально проходит.
- Блок Inflation дает положительный вклад в credit/liquidity шоках.

## Weaknesses

- Множественные провалы: role fail (equity), loss fail (credit/liquidity), Top1 RC fail (во всех сценариях).
- Экстремальная концентрация Top1 RC (около 2x выше cap).
- Очень глубокие сценарные потери в credit и liquidity режимах.
- Низкая надежность historical validation из-за NaN/null метрик.
- Высокий модельный риск по факторной части (экстремальный beta_credit).

## Scenario Behavior

Портфель устойчиво проваливает стресс-контур не из-за одного “плохого” сценария, а из-за комбинации трех классов нарушений: роль защиты, глубина потерь и концентрация Top1 RC. В equity shock структура защиты не формирует необходимый офсет, в credit/liquidity losses выходят за лимит, а RC-кап по первому активу нарушается во всех режимах. При этом rates/stagflation выглядят менее разрушительными, что подтверждает асимметричность уязвимостей и концентрацию проблемы в risk-on/credit стрессах. Текущая конфигурация больше похожа на перегруженный ростовой профиль, чем на сбалансированную policy-конструкцию с устойчивым кризисным поведением.


## Final Conclusion

Main portfolio в текущем состоянии не готов к production-использованию по стресс-критериям: FAIL_STRESS подтверждается одновременно по нескольким независимым тестам. Самый важный bottleneck — сочетание экстремального Top1 RC и слабого defensive offset, что приводит к тяжелым провалам в credit/liquidity и role-fail в equity crash. До структурной разгрузки концентрации риска и усиления защитного контура попытки “косметических” корректировок, вероятно, не дадут устойчивого PASS-профиля. Приоритетная цель — перевести портфель из режима множественных hard-fail в режим ограниченного числа soft-warnings с контролируемой глубиной stress loss.

