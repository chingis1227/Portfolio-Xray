---
title: "Equal-Weight vs Risk-Parity — Comparison Report"
subtitle: "Analytical comparison of baseline portfolios"
date: "2026-03-31 00:26 Центральная Европа (лето)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Primary data:** `ew_rp_comparison.json` (machine-readable comparison).
- **Source file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Курсор Новый Изменения/Main portfolio/ew_rp_comparison.json`
- **Generated:** 2026-03-31 00:26 Центральная Европа (лето)
- **Window:** 10y (`window_months=120`), **analysis_end** = 2026-02-28.
- **Delta rule:** delta = equal_weight - risk_parity.

## Executive summary
- Период: **10y** (120 мес.), **analysis_end** = 2026-02-28.
- Дельта: **delta = equal_weight - risk_parity**.
- Доходность: EW **15.20%** vs RP **8.40%** (Δ **6.80%**).
- Риск: EW **13.00%** vs RP **6.60%**; max DD EW **-20.90%** vs RP **-12.50%**.
- Стресс: EW **DIAG_ATTENTION** (DIAG_RC_TOP1_EQUITY_SHOCK); RP **PASS_WITH_WARNING** (None).

## Core metrics (10Y window)

| Metric | Equal-Weight | Risk-Parity | Delta (EW − RP) |
| --- | ---: | ---: | ---: |
| CAGR | 15.20% | 8.40% | 6.80% |
| Vol (annual) | 13.00% | 6.60% | 6.40% |
| Max drawdown | -20.90% | -12.50% | -8.40% |
| Sharpe | 0.991 | 0.924 | 0.068 |
| Sortino | 1.677 | 1.531 | 0.146 |
| Beta (portfolio) | 0.778 | 0.387 | 0.391 |
| Treynor | 0.165 | 0.157 | 0.008 |
| Corr (base) | 0.897 | 0.879 | 0.018 |
| Downside dev. (annual) | 7.70% | 4.00% | 3.70% |
| Skewness | -0.458 | -0.411 | -0.047 |
| Kurtosis | 0.746 | 0.649 | 0.097 |
| ES 95% | -7.60% | -3.80% | -3.80% |
| ES 99% | -9.30% | -4.90% | -4.40% |
| EEE 10% | 101.025 | 51.336 | 49.689 |
| TTR (months) | — | — | — |

## Rolling Sharpe (36m)

| Statistic | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **last** | 1.827 | 1.79 | 0.037 |
| **mean** | 0.719 | 0.683 | 0.036 |
| **p10** | 0.304 | 0.181 | 0.123 |
| **p90** | 1.14 | 1.176 | -0.036 |

## Rolling Sharpe (12m)

| Statistic | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **last** | 3.557 | 3.949 | -0.392 |
| **mean** | 1.042 | 1.006 | 0.036 |
| **p10** | -0.401 | -0.478 | 0.077 |
| **p90** | 2.533 | 2.253 | 0.280 |

## Rolling vol (12m)

| Statistic | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **last** | 9.50% | 4.20% | 5.30% |
| **mean** | 12.30% | 6.20% | 6.10% |
| **p10** | 7.30% | 3.50% | 3.80% |
| **p90** | 19.20% | 10.10% | 9.10% |

## Volatility stability

| Measure | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **vol_of_vol** | 0.044 | 0.023 | 0.021 |
| **rel_vol_of_vol** | 0.356 | 0.380 | -0.024 |

## RC_vol by block

| Block | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **Duration** | 1.10% | 5.10% | -4.00% |
| **Growth** | 89.40% | 77.40% | 12.00% |
| **Inflation** | 9.60% | 17.40% | -7.80% |
| **Liquidity** | 0.00% | 0.20% | -0.20% |

## RC_vol by asset

| Ticker | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **BBJP** | 4.10% | 5.00% | -0.90% |
| **BIL** | 0.00% | 0.20% | -0.20% |
| **BND** | 1.10% | 5.10% | -4.00% |
| **CIBR** | 5.30% | 5.40% | -0.10% |
| **COPX** | 11.40% | 5.80% | 5.60% |
| **GLD** | 2.20% | 6.10% | -3.90% |
| **ITA** | 6.30% | 5.40% | 0.90% |
| **QQQ** | 6.10% | 5.50% | 0.60% |
| **ROBO** | 7.90% | 5.50% | 2.40% |
| **SCHD** | 5.00% | 5.50% | -0.50% |
| **SCHP** | 1.20% | 5.20% | -4.00% |
| **SLV** | 6.20% | 6.00% | 0.20% |
| **SMH** | 8.40% | 5.40% | 3.00% |
| **URA** | 9.30% | 6.00% | 3.30% |
| **VDC** | 3.40% | 5.70% | -2.30% |
| **VGK** | 5.90% | 5.50% | 0.40% |
| **VOO** | 5.50% | 5.40% | 0.10% |
| **VT** | 5.60% | 5.50% | 0.10% |
| **VWO** | 5.20% | 5.90% | -0.70% |

## RC_vol — top risk contributors (union of top-5 sets)

| Ticker | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **COPX** | 11.40% | 5.80% | 5.60% |
| **GLD** | — | 6.10% | — |
| **ITA** | 6.30% | — | — |
| **ROBO** | 7.90% | — | — |
| **SLV** | — | 6.00% | — |
| **SMH** | 8.40% | — | — |
| **URA** | 9.30% | 6.00% | 3.30% |
| **VWO** | — | 5.90% | — |

## Stress and validation flags
- **EW:** stress **DIAG_ATTENTION**, reason `DIAG_RC_TOP1_EQUITY_SHOCK`, portfolio_valid **True**.
- **RP:** stress **PASS_WITH_WARNING**, reason `None`, portfolio_valid **True**.

## Key takeaways
- Сравнение построено на **одинаковом универсуме тикеров** и **одном окне**; интерпретация дельт — относительная (EW vs RP).
- При **DIAG_ATTENTION** и кодах **DIAG_*** пояснения по сценариям см. `stress_report.json` (диагностика, не блокирует выпуск).
