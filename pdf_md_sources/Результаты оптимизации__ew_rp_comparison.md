# Equal-Weight vs Risk-Parity Comparison Report

## Report Scope

- **Source:** `ew_rp_comparison.txt`
- **Calculation window:** **10y** (`window_months=120`)
- **Analysis end date:** **2026-02-28**
- **Delta rule:** **EW - RP**

## Executive Summary

- Equal-Weight (EW) shows higher return metrics than Risk-Parity (RP), with higher total and downside volatility.
- Risk-Parity (RP) demonstrates lower volatility and better tail risk values (`ES_95`, `ES_99`) in absolute terms.
- Both portfolios fail the same stress check (`FAIL_ROLE_EQUITY_SHOCK`) while remaining marked as `portfolio_valid=True`.

## Core Metrics Comparison

| Metric | EW | RP | Delta (EW - RP) |
|---|---:|---:|---:|
| CAGR | 14.95% | 11.21% | 3.70% |
| Annual Volatility | 12.50% | 9.84% | 2.70% |
| Max Drawdown | -19.93% | -18.75% | -1.20% |
| Sharpe | 1.007 | 0.910 | 0.097 |
| Sortino | 1.722 | 1.471 | 0.251 |
| Beta (Portfolio) | 0.745 | 0.602 | 0.143 |
| Treynor | 0.169 | 0.149 | 0.020 |
| Correlation to Base | 0.891 | 0.915 | -0.024 |
| Downside Deviation (Annual) | 7.30% | 6.10% | 1.20% |
| Skewness | -0.416 | -0.516 | 0.100 |
| Kurtosis | 0.647 | 0.781 | -0.134 |
| ES 95 | -7.30% | -5.90% | -1.40% |
| ES 99 | -8.80% | -7.40% | -1.40% |
| EEE 10% | 96.069 | 74.197 | 21.872 |
| Time to Recovery (months) | — | — | — |

## Rolling Metrics

### Rolling Sharpe 36m (last / mean / p10 / p90)

- **EW:** 1.798 / 0.724 / 0.311 / 1.140
- **RP:** 1.681 / 0.672 / 0.190 / 1.128
- **Delta (EW - RP):** 0.117 / 0.052 / 0.121 / 0.012

### Rolling Sharpe 12m (last / mean / p10 / p90)

- **EW:** 3.290 / 1.040 / -0.403 / 2.537
- **RP:** 3.712 / 1.042 / -0.383 / 2.464
- **Delta (EW - RP):** -0.422 / -0.002 / -0.020 / 0.073

### Rolling Volatility 12m (last / mean / p10 / p90)

- **EW:** 10.20% / 11.80% / 7.40% / 18.20%
- **RP:** 6.00% / 9.30% / 5.00% / 15.20%
- **Delta (EW - RP):** 4.20% / 2.50% / 2.40% / 3.00%

## Volatility Stability

- **vol_of_vol:** EW = 0.040 | RP = 0.037 | Delta = 0.003
- **rel_vol_of_vol:** EW = 0.339 | RP = 0.396 | Delta = -0.057

## Risk Contribution by Blocks (RC_vol)

- **Duration:** EW = 1.00% | RP = 3.20% | Delta = -2.20%
- **Growth:** EW = 89.60% | RP = 82.40% | Delta = 7.20%
- **Inflation:** EW = 9.30% | RP = 14.40% | Delta = -5.10%
- **Liquidity:** EW = 0.00% | RP = 0.00% | Delta = 0.00%

## Risk Contribution by Asset (RC_vol)

- ARMY.PA: EW = 0.60% | RP = 0.10% | Delta = 0.50%
- BBJP: EW = 4.00% | RP = 4.30% | Delta = -0.30%
- BIL: EW = -0.00% | RP = 0.00% | Delta = -0.00%
- BND: EW = 1.00% | RP = 3.20% | Delta = -2.20%
- CIBR: EW = 5.30% | RP = 5.10% | Delta = 0.20%
- COPX: EW = 11.40% | RP = 4.00% | Delta = 7.40%
- GLD: EW = 2.20% | RP = 2.20% | Delta = 0.00%
- ITA: EW = 6.30% | RP = 4.30% | Delta = 2.00%
- QQQ: EW = 6.00% | RP = 8.00% | Delta = -2.00%
- ROBO: EW = 7.80% | RP = 9.70% | Delta = -1.90%
- SCHD: EW = 4.90% | RP = 6.60% | Delta = -1.70%
- SCHP: EW = 1.10% | RP = 3.50% | Delta = -2.40%
- SLV: EW = 6.00% | RP = 8.70% | Delta = -2.70%
- SMH: EW = 8.40% | RP = 4.30% | Delta = 4.10%
- URA: EW = 9.30% | RP = 1.60% | Delta = 7.70%
- VDC: EW = 3.40% | RP = 5.40% | Delta = -2.00%
- VGK: EW = 5.80% | RP = 6.90% | Delta = -1.10%
- VOO: EW = 5.50% | RP = 9.50% | Delta = -4.00%
- VT: EW = 5.60% | RP = 7.70% | Delta = -2.10%
- VWO: EW = 5.20% | RP = 5.10% | Delta = 0.10%

## Top-5 RC_vol Assets (as reported)

### EW Top-5 by RC_vol

- COPX: EW = 11.40%
- URA: EW = 9.30%
- SMH: EW = 8.40%
- ROBO: EW = 7.80%
- ITA: EW = 6.30%

### RP Top-5 by RC_vol

- ROBO: RP = 9.70%
- VOO: RP = 9.50%
- SLV: RP = 8.70%
- QQQ: RP = 8.00%
- VT: RP = 7.70%

## Stress Status

- **EW stress:** `FAIL_STRESS (FAIL_ROLE_EQUITY_SHOCK)` | `portfolio_valid = True`
- **RP stress:** `FAIL_STRESS (FAIL_ROLE_EQUITY_SHOCK)` | `portfolio_valid = True`

## Conclusion / Key Takeaways

- EW outperforms RP on return-focused ratios (CAGR, Sharpe, Sortino, Treynor) in this 10-year window.
- RP keeps lower overall and downside volatility, and better expected shortfall values.
- Both portfolios share the same stress failure status, so comparative differences do not remove stress vulnerability in the reported scenario.
