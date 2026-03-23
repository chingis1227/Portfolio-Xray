---
description: Сгенерировать commentary.txt по сравнению портфелей
---

Сгенерируй comparative commentary по переданному comparison result file.

Перед началом:
1) Используй как source of truth:
   - `metrics_specification.md` (или `docs/metrics_specification.md`, если файл есть)
   - `docs/portfolio_construction_policy.md`
   - `docs/data_policy_nan_young_etfs.md`
   - `docs/stress_testing_spec.md` (если файл есть)
2) Сравнивай портфели только по метрикам, присутствующим во входном файле.
3) Не выдумывай данные, не давай buy/sell рекомендации, не добавляй неподтвержденные макро-нарративы.

Вход:
- путь к одному comparison-файлу (например, `ew_rp_comparison.txt`)

Действия:
1) Прочитай comparison-файл полностью.
2) Создай/обнови `commentary.txt` рядом с comparison-файлом.
3) Если `commentary.txt` уже содержит блоки по другим source-файлам, добавь отдельный блок с заголовком `Source: <имя_файла>`.
4) Подготовь краткий институциональный сравнительный комментарий.

Структура (строго):
- Executive Summary
- Metric-by-Metric Interpretation
- Risk Structure
- Strengths
- Weaknesses
- Scenario Behavior
- Final Conclusion

Обязательно отдельно покажи:
- где один портфель сильнее по доходности
- где другой сильнее по риску
- где лучше downside protection
- где лучше diversification
- в каких сценариях один устойчивее другого
- какие ключевые trade-offs подтверждены цифрами

Стиль:
- experienced institutional portfolio manager
- кратко и строго по цифрам
- без воды и без рекомендаций
