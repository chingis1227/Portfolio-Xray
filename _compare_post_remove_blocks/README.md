# Сравнение после удаления блоков и risk budgeting

Эта папка предназначена для **артефактов сравнения** «до / после» рефакторинга (M9 плана).

## Что сюда положить

1. **Baseline (до):** копия ключевых файлов из последнего прогона со старой архитектурой (по желанию): `run_result.json`, `stress_report.json`, `summary.txt`, `portfolio_weights.yml` из `Main portfolio/`, EW и RP папок.
2. **Post (после):** те же файлы после `python run_optimization.py`, `python run_equal_weight.py`, `python run_risk_parity.py` на профиле **Balanced** и текущем `config.yml`.

## Заполненный прогон (2026-04-27)

См. **[M9_post_run_2026-04-27.md](./M9_post_run_2026-04-27.md)** — таблица после `run_optimization.py` → `run_report.py`, `run_equal_weight.py`, `run_risk_parity.py` на **Balanced**.

### Шаблон (если нужен повторный замер)

| Метрика | Main (baseline) | Main (post) | EW (post) | RP (post) |
|--------|-----------------|-------------|-----------|-----------|
| Vol 5Y/10Y | | | | |
| MaxDD | | | | |
| Sharpe | | | | |
| Top1 RC | | | | |
| Worst scenario PnL | | | | |

*Числа брать из `run_result.json` / `stress_report.json` / `snapshot_10y.json` после прогона.*

## Примечание

Полный прогон требует данных (yfinance/FRED) и времени; в среде CI/агента таблица может оставаться шаблоном — заполните локально после прогона.
