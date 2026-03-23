---
description: Сгенерировать commentary.txt по result-файлу портфеля
---

Сгенерируй институциональный комментарий по переданному result-файлу.

Перед началом:
1) Используй как source of truth:
   - `metrics_specification.md` (или `docs/metrics_specification.md`, если файл есть)
   - `docs/portfolio_construction_policy.md`
   - `docs/data_policy_nan_young_etfs.md`
   - `docs/stress_testing_spec.md` (если файл есть)
2) Интерпретируй только метрики, реально присутствующие во входном файле.
3) Не выдумывай значения. Не добавляй buy/sell рекомендации.
4) Не добавляй макро-истории без числовой опоры.

Вход:
- путь к одному result-файлу (`report.txt`, `summary.txt`, `ips_summary.txt`, `run_result.json`, и т.д.)

Действия:
1) Прочитай входной файл полностью.
2) Создай/обнови `commentary.txt` в той же папке.
3) Если в этой папке уже есть `commentary.txt` и он относится к другому source-файлу, не удаляй существующий блок; добавь новый блок с заголовком `Source: <имя_файла>`.
4) Напиши короткий профессиональный комментарий в стиле experienced institutional portfolio manager.

Структура (строго):
- Executive Summary
- Metric-by-Metric Interpretation
- Risk Structure
- Strengths
- Weaknesses
- Scenario Behavior
- Final Conclusion

Правила интерпретации:
- Для каждой ключевой метрики:
  - 1 короткое предложение: что показывает метрика
  - 1 короткое предложение: что это означает для профиля портфеля
- Обязательно интерпретируй, если есть:
  CAGR, volatility, max drawdown, Sharpe, Sortino, beta, expected shortfall, downside deviation, skewness, kurtosis, correlation, RC_vol по блокам, RC_vol по активам.
- Если есть другие метрики, интерпретируй их в том же формате.

Стиль:
- кратко, профессионально, без воды
- только факты из цифр
- ясный разбор trade-off (return / risk / downside / concentration / diversification)
- без инвестиционных рекомендаций
