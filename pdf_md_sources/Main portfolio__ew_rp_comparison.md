---
title: "Equal-Weight vs Risk-Parity — Comparison Report"
subtitle: "Analytical comparison of baseline portfolios"
date: "2026-03-23 23:38 Центральная Европа (зима)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Primary data:** `ew_rp_comparison.json` (machine-readable comparison).
- **Source file:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Cursor/Main portfolio/ew_rp_comparison.json`
- **Generated:** 2026-03-23 23:38 Центральная Европа (зима)
- **Window:** 10y (`window_months=120`), **analysis_end** = 2026-02-28.
- **Delta rule:** delta = equal_weight - risk_parity.

## Executive summary
- Период: **10y** (120 мес.), **analysis_end** = 2026-02-28.
- Дельта: **delta = equal_weight - risk_parity**.
- Доходность: EW **15.00%** vs RP **11.20%** (Δ **3.70%**).
- Риск: EW **12.50%** vs RP **9.80%**; max DD EW **-19.90%** vs RP **-18.70%**.
- Стресс: EW **FAIL_STRESS** (FAIL_ROLE_EQUITY_SHOCK); RP **FAIL_STRESS** (FAIL_ROLE_EQUITY_SHOCK).

## Core metrics (10Y window)

| Metric | Equal-Weight | Risk-Parity | Delta (EW − RP) |
| --- | ---: | ---: | ---: |
| CAGR | 15.00% | 11.20% | 3.70% |
| Vol (annual) | 12.50% | 9.80% | 2.70% |
| Max drawdown | -19.90% | -18.70% | -1.20% |
| Sharpe | 1.007 | 0.910 | 0.097 |
| Sortino | 1.722 | 1.471 | 0.251 |
| Beta (portfolio) | 0.745 | 0.602 | 0.143 |
| Treynor | 0.169 | 0.149 | 0.020 |
| Corr (base) | 0.891 | 0.915 | -0.024 |
| Downside dev. (annual) | 7.30% | 6.10% | 1.20% |
| Skewness | -0.416 | -0.516 | 0.100 |
| Kurtosis | 0.647 | 0.781 | -0.134 |
| ES 95% | -7.30% | -5.90% | -1.40% |
| ES 99% | -8.80% | -7.40% | -1.40% |
| EEE 10% | 96.069 | 74.197 | 21.872 |
| TTR (months) | — | — | — |

## Rolling Sharpe (36m)

| Statistic | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **last** | 1.798 | 1.681 | 0.117 |
| **mean** | 0.724 | 0.672 | 0.052 |
| **p10** | 0.311 | 0.190 | 0.121 |
| **p90** | 1.14 | 1.128 | 0.012 |

## Rolling Sharpe (12m)

| Statistic | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **last** | 3.29 | 3.712 | -0.422 |
| **mean** | 1.04 | 1.042 | -0.002 |
| **p10** | -0.403 | -0.383 | -0.020 |
| **p90** | 2.537 | 2.464 | 0.073 |

## Rolling vol (12m)

| Statistic | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **last** | 10.20% | 6.00% | 4.20% |
| **mean** | 11.80% | 9.30% | 2.50% |
| **p10** | 7.40% | 5.00% | 2.40% |
| **p90** | 18.20% | 15.20% | 3.00% |

## Volatility stability

| Measure | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **vol_of_vol** | 0.040 | 0.037 | 0.003 |
| **rel_vol_of_vol** | 0.339 | 0.396 | -0.057 |

## RC_vol by block

| Block | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **Duration** | 1.00% | 3.20% | -2.20% |
| **Growth** | 89.60% | 82.40% | 7.20% |
| **Inflation** | 9.30% | 14.40% | -5.10% |
| **Liquidity** | -0.00% | 0.00% | -0.00% |

## RC_vol by asset

| Ticker | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **ARMY.PA** | 0.60% | 0.10% | 0.50% |
| **BBJP** | 4.00% | 4.30% | -0.30% |
| **BIL** | -0.00% | 0.00% | -0.00% |
| **BND** | 1.00% | 3.20% | -2.20% |
| **CIBR** | 5.30% | 5.10% | 0.20% |
| **COPX** | 11.40% | 4.00% | 7.40% |
| **GLD** | 2.20% | 2.20% | 0.00% |
| **ITA** | 6.30% | 4.30% | 2.00% |
| **QQQ** | 6.00% | 8.00% | -2.00% |
| **ROBO** | 7.80% | 9.70% | -1.90% |
| **SCHD** | 4.90% | 6.60% | -1.70% |
| **SCHP** | 1.10% | 3.50% | -2.40% |
| **SLV** | 6.00% | 8.70% | -2.70% |
| **SMH** | 8.40% | 4.30% | 4.10% |
| **URA** | 9.30% | 1.60% | 7.70% |
| **VDC** | 3.40% | 5.40% | -2.00% |
| **VGK** | 5.80% | 6.90% | -1.10% |
| **VOO** | 5.50% | 9.50% | -4.00% |
| **VT** | 5.60% | 7.70% | -2.10% |
| **VWO** | 5.20% | 5.10% | 0.10% |

## RC_vol — top risk contributors (union of top-5 sets)

| Ticker | EW | RP | Delta |
| --- | ---: | ---: | ---: |
| **COPX** | 11.40% | — | — |
| **ITA** | 6.30% | — | — |
| **QQQ** | — | 8.00% | — |
| **ROBO** | 7.80% | 9.70% | -1.90% |
| **SLV** | — | 8.70% | — |
| **SMH** | 8.40% | — | — |
| **URA** | 9.30% | — | — |
| **VOO** | — | 9.50% | — |
| **VT** | — | 7.70% | — |

## Stress and validation flags
- **EW:** stress **FAIL_STRESS**, reason `FAIL_ROLE_EQUITY_SHOCK`, portfolio_valid **True**.
- **RP:** stress **FAIL_STRESS**, reason `FAIL_ROLE_EQUITY_SHOCK`, portfolio_valid **True**.

## Key takeaways
- Сравнение построено на **одинаковом универсуме тикеров** и **одном окне**; интерпретация дельт — относительная (EW vs RP).
- При **FAIL_STRESS** пояснения по сценариям см. `stress_report.json` в соответствующих папках прогонов.
