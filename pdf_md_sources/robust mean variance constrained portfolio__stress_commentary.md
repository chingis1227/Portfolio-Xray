---
title: "Main Portfolio: Stress Analysis"
date: "Analysis results for the 10-year window as of 2026-04-30"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Executive Summary

Main Portfolio was reviewed on the latest available reporting window. CAGR is 16.00%, annualized volatility is 12.50%, maximum drawdown is -20.70%, Sharpe is 1.081, Sortino is 1.833, and market sensitivity is 0.729. Stress diagnostics show: One risk area requires attention; worst scenario loss is -42.82%.

## Key Metrics

```{=latex}
\begin{center}\begin{tabular}{@{}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{\hspace{0.45em}}>{\centering\arraybackslash}m{0.30\textwidth}@{}} \KPIone{16.00\%}{CAGR} & \KPIone{12.50\%}{Volatility} & \KPIone{-20.70\%}{Max Drawdown}\\[0.55em] \KPIone{1.081}{Sharpe} & \KPIone{1.833}{Sortino} & \KPIone{0.729}{Market Sensitivity}\end{tabular}\end{center}
```

## What This Means

The portfolio profile should be read as a trade-off between return, realized drawdown, and market sensitivity. CAGR measures compound annual growth, volatility measures annualized variability, and maximum drawdown captures the largest peak-to-trough loss in the reporting window. Sharpe and Sortino summarize risk-adjusted return, while market sensitivity indicates how strongly the portfolio moves with the broad benchmark.

## Risk Structure

Stress status: One risk area requires attention. Worst scenario loss: -42.82%. Flagged scenario: equity_shock; flagged test: Loss. These diagnostics are used to identify risk concentrations and scenario vulnerability; they do not by themselves replace the mandate checks.

## Scenario Analysis

| Scenario | PnL | Pass | Top RC Asset | Top 3 RC |
| --- | ---: | --- | --- | ---: |
| equity_shock | -29.16% | False | QQQ | 75.78% |
| credit_shock | -3.34% | True | QQQ | 75.73% |
| rates_shock | -1.50% | True | QQQ | 75.98% |
| inflation_stagflation | -11.56% | True | QQQ | 74.85% |
| liquidity_shock | -15.27% | True | QQQ | 75.38% |
| recession_severe | -42.82% | False | QQQ | 75.37% |

## Conclusion

This English PDF was generated from the current structured portfolio outputs. Use the metrics, stress status, and scenario table together: the headline return profile is only meaningful when read alongside drawdown resilience and scenario behavior.
