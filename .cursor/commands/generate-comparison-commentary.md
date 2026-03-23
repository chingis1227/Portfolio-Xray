---
description: Сгенерировать commentary.txt по сравнению портфелей
---

Сгенерируй **сравнительный** комментарий в формате компактной внутренней analyst note.

Обязательный стандарт: `.cursor/rules/portfolio-commentary.mdc`.

Перед началом:
1) Source of truth: `docs/metrics_specification.md`, `docs/portfolio_construction_policy.md`, `docs/data_policy_nan_young_etfs.md`, `docs/stress_testing_spec.md` (если есть).
2) Сравнивай только по метрикам и статусам из comparison-файла (и при необходимости явно указанных в нём источников). Не выдумывай данные.
3) Не buy/sell, не неподтверждённые макро-истории.
4) Не пиши, что «деталей нет», если они есть в том же файле (RC по блокам/активам, стресс-коды, дельты и т.д.).
5) **Не добавляй** «Final note» и прочие шаблонные compliance-закрытия.

Вход:
- путь к comparison-файлу (например, `ew_rp_comparison.txt`)

Действия:
1) Прочитай comparison-файл полностью.
2) Создай/обнови `commentary.txt` рядом (часто `ew_rp_comparison.commentary.txt` или блок `Source:` в общем `commentary.txt` — по принятой в папке схеме).
3) При нескольких source-блоках в одном файле — отдельный блок с `Source: <имя_файла>`.

Структура (строго):
- Executive Summary
- Metric-by-Metric Interpretation
- Risk Structure
- Strengths
- Weaknesses
- Scenario Behavior
- Final Conclusion

Обязательно раскрой (если данные есть во входе):
- доходность (CAGR и родственные метрики);
- риск (vol, beta, downside, ES);
- max drawdown и хвосты;
- RC_vol по блокам/активам и что это значит для различия профилей;
- стресс-статусы и сценарии по каждому варианту;
- ключевые trade-offs с опорой на цифры.

Тон: институциональный, чуть более развёрнутый, чем «одна строка на метрику», но без лишней воды. Русский — грамотный и ровный.
