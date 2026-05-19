---
title: "Main Portfolio: Executive Commentary"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 9.90%, annualized volatility is 9.60%, maximum drawdown is -19.80%, Sharpe is 0.799, Sortino is 1.286, and market sensitivity is 0.513. Stress diagnostics show: One risk area requires attention; worst scenario loss is -22.09%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{9.90\%}{CAGR} & \KPIone{9.60\%}{Volatility} & \KPIone{-19.80\%}{Max Drawdown}\\[0.55em] \KPIone{0.799}{Sharpe} & \KPIone{1.286}{Sortino} & \KPIone{0.513}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: One risk area requires attention. Worst scenario loss: -22.09%. Flagged scenario: recession_severe; flagged test: Loss. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -16.27% | True | SCHD | 63.69% |
| credit_shock | -3.01% | True | SCHD | 58.67% |
| rates_shock | -8.26% | True | SLV | 55.31% |
| inflation_stagflation | -9.13% | True | SLV | 60.15% |
| liquidity_shock | -9.38% | True | SCHD | 60.41% |
| recession_severe | -22.09% | False | SCHD | 60.64% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
